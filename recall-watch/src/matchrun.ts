import type { Db } from './db.js';
import { rowToRecall } from './ingest.js';
import { match } from './match.js';
import type { WatchItem } from './types.js';

/**
 * Runs the matcher over every (recall, watch item) pair that has not been evaluated yet.
 *
 * Idempotent by UNIQUE (recall_id, watch_item_id): re-running produces no new matches and does
 * not disturb a decision a human already made.
 */
export function runMatching(db: Db, now = new Date().toISOString()): { evaluated: number; created: number } {
  const recalls = (db.prepare('SELECT * FROM recalls').all() as Record<string, unknown>[]).map(rowToRecall);
  const watches = (db.prepare('SELECT * FROM watch_items').all() as Record<string, unknown>[]).map(
    (w): WatchItem => ({
      id: Number(w.id),
      subscriberId: Number(w.subscriber_id),
      kind: w.kind as WatchItem['kind'],
      brand: (w.brand as string) ?? null,
      product: (w.product as string) ?? null,
      upc: (w.upc as string) ?? null,
      vin: (w.vin as string) ?? null,
      category: (w.category as string) ?? null,
      lot: (w.lot as string) ?? null,
    }),
  );

  const insert = db.prepare(`
    INSERT INTO matches (recall_id, watch_item_id, confidence, reason, created_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT (recall_id, watch_item_id) DO NOTHING
  `);

  let evaluated = 0;
  let created = 0;
  for (const r of recalls) {
    for (const w of watches) {
      evaluated++;
      const m = match(r, w);
      if (!m) continue;
      const res = insert.run(r.id, w.id, m.confidence, JSON.stringify(m.reason), now);
      if (res.changes > 0) created++;
    }
  }
  return { evaluated, created };
}

export function decide(
  db: Db, matchId: number, decision: 'alert' | 'not_a_match' | 'unclear', by: string,
  now = new Date().toISOString(),
): void {
  db.prepare('UPDATE matches SET decision = ?, decided_at = ?, decided_by = ? WHERE id = ?')
    .run(decision, now, by, matchId);
}
