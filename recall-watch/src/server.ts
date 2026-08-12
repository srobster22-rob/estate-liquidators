import { createServer as createHttpServer, type IncomingMessage, type ServerResponse } from 'node:http';
import type { Db } from './db.js';
import { rowToRecall } from './ingest.js';
import { decide } from './matchrun.js';

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
  phone: string;
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

/** The next record to decide. One at a time is the point — a list invites skimming. */
export function nextForReview(db: Db): QueueRow | undefined {
  return db.prepare(`
    SELECT m.id AS match_id, m.confidence, m.reason,
           s.phone, w.brand, w.product, w.upc, w.category, r.*
    FROM matches m
    JOIN watch_items w ON w.id = m.watch_item_id
    JOIN subscribers s ON s.id = w.subscriber_id
    JOIN recalls r ON r.id = m.recall_id
    WHERE m.confidence = 'candidate' AND m.decision IS NULL
    ORDER BY (r.severity = 'high') DESC, r.announced_on DESC, m.id
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

     <form method="post" action="/review/${row.match_id}">
       <button class="primary" name="decision" value="alert">Send the alert</button>
       <button name="decision" value="not_a_match">Not a match</button>
       <button name="decision" value="unclear">Can't tell — skip</button>
     </form>

     <p class="meta">Deciding "send" queues one text. Deciding "not a match" is a bug report about
     the matcher — those get read.</p>`,
  );
}

export function renderPublic(db: Db): string {
  const rows = db.prepare(`
    SELECT * FROM recalls WHERE severity = 'high' ORDER BY announced_on DESC LIMIT 25
  `).all() as Record<string, unknown>[];

  const cards = rows.length
    ? rows.map((r) => {
        const rec = rowToRecall(r);
        return `<div class="card high">
          <p><strong>${esc(rec.title)}</strong></p>
          <p>${esc(rec.hazard)}</p>
          <p><strong>What to do:</strong> ${esc(rec.remedy || 'See the official notice.')}</p>
          <p class="meta">${esc(rec.source.toUpperCase())} · announced ${esc(rec.announcedOn)}
            ${rec.url ? `· <a href="${esc(rec.url)}" rel="noopener">official notice</a>` : ''}</p>
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

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const c of req) chunks.push(c as Buffer);
  return Buffer.concat(chunks).toString('utf8');
}

export function createServer(db: Db, reviewer = 'coordinator') {
  return createHttpServer((req: IncomingMessage, res: ServerResponse) => {
    void (async () => {
      const url = new URL(req.url ?? '/', 'http://localhost');

      if (req.method === 'POST') {
        const m = /^\/review\/(\d+)$/.exec(url.pathname);
        if (m) {
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
        res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
        res.end(renderReview(db));
        return;
      }
      if (url.pathname === '/') {
        res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
        res.end(renderPublic(db));
        return;
      }

      res.writeHead(404, { 'content-type': 'text/plain' });
      res.end('not found');
    })().catch(() => {
      res.writeHead(500, { 'content-type': 'text/plain' });
      res.end('error');
    });
  });
}
