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

export type Choice = 'alert' | 'not_a_match' | 'unclear';

export type DecideResult =
  | 'recorded'
  | 'deferred'
  /** Already decided. The earlier decision stands; this call changed nothing. */
  | 'already_decided'
  | 'no_such_match';

/**
 * Record a human's decision about one candidate.
 *
 * Two behaviours here are deliberate and were both bugs before R10.
 *
 * 1. A DECIDED RECORD IS FINAL unless `overwrite` is passed. The previous version issued a bare
 *    UPDATE, so any repeat POST -- a double-click, a retried request, or someone walking
 *    /review/1, /review/2, ... -- silently replaced a coordinator's "alert" with whatever
 *    arrived last. A decision that can be overwritten without a trace is not a decision.
 *
 * 2. "unclear" DEFERS, IT DOES NOT DISMISS. The button says "Can't tell -- skip", and skip has
 *    to mean skip. Writing decision='unclear' dropped the record out of `nextForReview` (which
 *    filters on `decision IS NULL`) permanently, so the honest answer -- I don't know, let
 *    someone else look -- was the one answer that buried a recall with nobody informed. It now
 *    stays in the queue, moves to the back, and counts how many people have passed on it.
 *
 * There is deliberately no UI for `overwrite` yet; see VERIFY.md. Correcting a mistaken decision
 * should be a considered act with a record of who changed what, not a fourth button.
 */
export function decide(
  db: Db, matchId: number, decision: Choice, by: string,
  now = new Date().toISOString(),
  opts: { overwrite?: boolean } = {},
): DecideResult {
  const row = db.prepare('SELECT decision FROM matches WHERE id = ?').get(matchId) as
    | { decision: string | null }
    | undefined;
  if (!row) return 'no_such_match';
  if (row.decision !== null && !opts.overwrite) return 'already_decided';

  if (decision === 'unclear') {
    db.prepare(
      'UPDATE matches SET deferred_at = ?, defer_count = defer_count + 1 WHERE id = ?',
    ).run(now, matchId);
    return 'deferred';
  }

  db.prepare('UPDATE matches SET decision = ?, decided_at = ?, decided_by = ? WHERE id = ?')
    .run(decision, now, by, matchId);
  return 'recorded';
}
