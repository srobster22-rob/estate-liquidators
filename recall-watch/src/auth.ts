import { createHmac, timingSafeEqual, randomBytes } from 'node:crypto';

/**
 * Access control for the review queue.
 *
 * Written in R10 after running the hardening prompt's Pass 2 and Pass 4 against a live server.
 * Both passes found the same hole from opposite directions, and the finding was worse than
 * expected. Anonymous, with no credential of any kind:
 *
 *   POST /review/1  decision=alert        -> 303. A stranger queues a text to a real phone.
 *   POST /review/N  decision=not_a_match  -> 303, for N = 1..8, and the queue was empty.
 *
 * The toll-fraud direction is the obvious one. The second is the one that actually hurts: a
 * passer-by can mark a superpotent-infant-acetaminophen recall "not a match" and the coordinator
 * then sees "Nothing to review" -- which the empty-state text truthfully calls the normal state.
 * The alert is gone and nothing anywhere says so. This project's whole design is built around
 * never failing silently, and its one write endpoint failed silently to anyone on the network.
 *
 * There are no user accounts here and inventing them would be worse than the disease. The
 * proportionate control for a volunteer project with a handful of coordinators is one shared
 * secret, so that is what this is -- with the sharp edges filed off:
 *
 *   - Unset token means /review REFUSES TO SERVE. Not "open in development", not a default
 *     password. The same rule as `jurisdiction.configured` in the disposal guide: an
 *     unconfigured deployment is useless rather than dangerous.
 *   - The token never appears in a URL. Pass 2.3 is explicit about why: URLs reach access logs,
 *     Referer headers, and shared browser history. It is posted once to a sign-in form.
 *   - The cookie holds an expiring HMAC, not the token, so a stolen cookie jar does not hand
 *     over the secret itself and every session eventually dies.
 *   - Comparisons are constant-time.
 */

export const TOKEN_ENV = 'RECALL_WATCH_REVIEW_TOKEN';
export const COOKIE_NAME = 'rw_review';
export const SESSION_TTL_MS = 12 * 60 * 60 * 1000;

/**
 * A short shared secret is not a control, it is a speed bump, and one that reads as security is
 * worse than none. Sixteen characters is not a strong opinion about entropy; it is a floor low
 * enough that nobody is tempted to work around it and high enough to stop `review`.
 */
export const TOKEN_MIN_LENGTH = 16;

export interface TokenState {
  configured: boolean;
  token?: string;
  /** Set when a token is present but unusable. Shown to the operator, never to the public. */
  problem?: string;
}

export function readToken(env: Record<string, string | undefined>): TokenState {
  const raw = env[TOKEN_ENV];
  if (!raw) return { configured: false };
  if (raw.length < TOKEN_MIN_LENGTH) {
    return {
      configured: false,
      problem: `${TOKEN_ENV} is set but only ${raw.length} characters. It needs at least ` +
        `${TOKEN_MIN_LENGTH}. Generate one with: node -e "console.log(require('crypto').randomBytes(24).toString('base64url'))"`,
    };
  }
  return { configured: true, token: raw };
}

/** Suggests a token for the operator to copy. Never used as a default. */
export function suggestToken(): string {
  return randomBytes(24).toString('base64url');
}

function safeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a, 'utf8');
  const bb = Buffer.from(b, 'utf8');
  // timingSafeEqual throws on length mismatch, which would itself leak length. Compare a
  // fixed-width digest of each instead so every comparison does the same work.
  const ah = createHmac('sha256', 'len-guard').update(ab).digest();
  const bh = createHmac('sha256', 'len-guard').update(bb).digest();
  return timingSafeEqual(ah, bh);
}

export function checkToken(supplied: string, state: TokenState): boolean {
  if (!state.configured || !state.token) return false;
  return safeEqual(supplied, state.token);
}

// ------------------------------------------------------------------ session cookie

function sign(token: string, expiresAt: number): string {
  return createHmac('sha256', token).update(`review-session-v1|${expiresAt}`).digest('hex');
}

export function mintSession(token: string, now = Date.now()): string {
  const expiresAt = now + SESSION_TTL_MS;
  return `${expiresAt}.${sign(token, expiresAt)}`;
}

export function verifySession(value: string | undefined, state: TokenState, now = Date.now()): boolean {
  if (!value || !state.configured || !state.token) return false;
  const dot = value.indexOf('.');
  if (dot <= 0) return false;
  const expiresAt = Number(value.slice(0, dot));
  if (!Number.isFinite(expiresAt) || expiresAt <= now) return false;
  return safeEqual(value.slice(dot + 1), sign(state.token, expiresAt));
}

export function parseCookies(header: string | undefined): Record<string, string> {
  const out: Record<string, string> = {};
  for (const part of (header ?? '').split(';')) {
    const eq = part.indexOf('=');
    if (eq <= 0) continue;
    out[part.slice(0, eq).trim()] = decodeURIComponent(part.slice(eq + 1).trim());
  }
  return out;
}

export function sessionCookie(value: string, secure: boolean): string {
  // HttpOnly: no script on the page needs it, and this page has no script at all.
  // SameSite=Strict: a cross-site form post must not carry it. This is the CSRF control -- with
  //   no cookie the POST is simply unauthenticated -- and the Origin check below backs it up.
  // Path=/review: the public page never receives it.
  return [
    `${COOKIE_NAME}=${encodeURIComponent(value)}`,
    'Path=/review',
    'HttpOnly',
    'SameSite=Strict',
    `Max-Age=${Math.floor(SESSION_TTL_MS / 1000)}`,
    ...(secure ? ['Secure'] : []),
  ].join('; ');
}

/**
 * Belt and braces against CSRF, because SameSite handling still varies between browsers and
 * this endpoint sends text messages to people.
 *
 * A request with no Origin and no Referer is allowed: that is curl and the test suite, and
 * blocking it would buy nothing (an attacker forging a request from a browser cannot strip
 * Origin, and one not using a browser has no victim cookie to ride on).
 */
export function originAllowed(headers: { origin?: string; referer?: string; host?: string }): boolean {
  const stated = headers.origin ?? headers.referer;
  if (!stated) return true;
  if (!headers.host) return false;
  try {
    return new URL(stated).host === headers.host;
  } catch {
    return false;
  }
}

// ------------------------------------------------------------------ rate limiting

/**
 * A fixed-window counter, per key, in memory.
 *
 * Deliberately not a distributed limiter: one process serves this and pretending otherwise
 * would be architecture theatre. What it stops is the thing Pass 4.7 asks about -- one client
 * firing a hundred requests at the decision endpoint -- and it stops it without any dependency
 * a volunteer has to run.
 */
export class RateLimiter {
  private hits = new Map<string, { count: number; resetAt: number }>();
  constructor(private readonly limit: number, private readonly windowMs: number) {}

  /** True when the request may proceed. */
  take(key: string, now = Date.now()): boolean {
    const entry = this.hits.get(key);
    if (!entry || now >= entry.resetAt) {
      this.hits.set(key, { count: 1, resetAt: now + this.windowMs });
      return true;
    }
    entry.count++;
    return entry.count <= this.limit;
  }

  retryAfterSeconds(key: string, now = Date.now()): number {
    const entry = this.hits.get(key);
    return entry ? Math.max(1, Math.ceil((entry.resetAt - now) / 1000)) : 1;
  }
}
