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

const FIXTURES = join(import.meta.dirname, '..', 'fixtures');
const PAIRS = join(import.meta.dirname, '..', 'data', 'labelled-pairs.json');
const NOW = '2026-03-25T09:00:00.000Z';

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
