import type { Db } from './db.js';
import type { SmsProvider } from './sms.js';
import { rowToRecall } from './ingest.js';
import type { Recall } from './types.js';

/**
 * Delivery: durable, idempotent, exactly-once, restart-safe.
 *
 * Two separate guarantees, both enforced by the database rather than by careful code:
 *
 *  1. ONE MESSAGE PER PERSON PER RECALL — UNIQUE (subscriber_id, recall_id). Two matches on the
 *     same recall (a UPC watch and a product watch for the same jar) produce one text.
 *  2. EXACTLY ONCE UNDER FAILURE — a row is claimed before it is sent, and only an unclaimed or
 *     stale-claimed row can be picked up. A worker killed mid-send leaves a claim that expires;
 *     the replacement worker retries it, and `delivered` stops it being sent twice.
 *
 * Both matter more than they look. A pipeline that loses messages on deploy fails silently at the
 * exact moment it is needed; one that double-sends teaches people to ignore it, which is worse.
 */

const CLAIM_TTL_MS = 5 * 60 * 1000;

/**
 * After this many failed attempts a message is dead-lettered and an operator is told.
 *
 * The version before this one left a permanently failing message in the table with `last_error`
 * set and nobody informed — so a bad phone number, a suspended account, or a carrier block meant
 * somebody silently stopped receiving recall alerts while the dashboard showed nothing wrong.
 * For a safety notification service, failing quietly is the worst available behaviour.
 */
const MAX_ATTEMPTS = 5;

export interface OperatorAlert {
  kind: 'delivery_dead_letter';
  notificationId: number;
  subscriberId: number;
  recallId: number;
  attempts: number;
  lastError: string;
}

/** Where dead letters go. Wire this to whatever a human actually reads. */
export type OperatorSink = (alert: OperatorAlert) => void | Promise<void>;

export const consoleOperatorSink: OperatorSink = (a) => {
  console.error(
    `[OPERATOR] notification ${a.notificationId} for subscriber ${a.subscriberId} gave up after ` +
      `${a.attempts} attempts: ${a.lastError}. Somebody is not receiving recall alerts.`,
  );
};

/** Only high-severity recalls earn a text. Everything else belongs in a digest, or nowhere. */
export function earnsSms(severity: Recall['severity']): boolean {
  return severity === 'high';
}

export function composeMessage(r: Recall): string {
  // Under 300 characters, plain, and it says what to do. The hazard text is not softened.
  const what = r.products[0] ?? r.title;
  const brand = r.brands[0] ? `${r.brands[0]} ` : '';
  const body = `RECALL: ${brand}${what}. ${r.hazard} What to do: ${r.remedy} ${r.url} Reply STOP to end.`;
  return body.length <= 300 ? body : `${body.slice(0, 296)}...`;
}

/** Turn decided matches into queued notifications. Safe to run repeatedly. */
export function enqueue(db: Db, now = new Date().toISOString()): number {
  const rows = db.prepare(`
    SELECT m.id AS match_id, m.confidence, m.decision, w.subscriber_id, r.*
    FROM matches m
    JOIN watch_items w ON w.id = m.watch_item_id
    JOIN recalls r ON r.id = m.recall_id
    JOIN subscribers s ON s.id = w.subscriber_id
    WHERE s.active = 1
      AND (m.decision = 'alert' OR (m.decision IS NULL AND m.confidence IN ('exact','strong')))
  `).all() as Record<string, unknown>[];

  const insert = db.prepare(`
    INSERT INTO notifications (subscriber_id, recall_id, body, idempotency_key, created_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT (subscriber_id, recall_id) DO NOTHING
  `);

  let queued = 0;
  for (const row of rows) {
    const recall = rowToRecall(row);
    if (!earnsSms(recall.severity)) continue;
    const subscriberId = Number(row.subscriber_id);
    const key = `sms:${subscriberId}:${recall.id}`;
    const res = insert.run(subscriberId, recall.id, composeMessage(recall), key, now);
    if (res.changes > 0) queued++;
  }
  return queued;
}

interface Claim { id: number; phone: string; body: string; idempotency_key: string }

/** Atomically claim a batch. A stale claim (from a killed worker) becomes claimable again. */
export function claimBatch(db: Db, limit = 20, now = Date.now()): Claim[] {
  const cutoff = new Date(now - CLAIM_TTL_MS).toISOString();
  const nowIso = new Date(now).toISOString();
  db.exec('BEGIN IMMEDIATE');
  try {
    const rows = db.prepare(`
      SELECT n.id, s.phone, n.body, n.idempotency_key
      FROM notifications n JOIN subscribers s ON s.id = n.subscriber_id
      WHERE n.delivered = 0 AND n.dead_lettered_at IS NULL
        AND (n.claimed_at IS NULL OR n.claimed_at < ?)
      ORDER BY n.id LIMIT ?
    `).all(cutoff, limit) as unknown as Claim[];
    const mark = db.prepare('UPDATE notifications SET claimed_at = ?, attempts = attempts + 1 WHERE id = ?');
    for (const r of rows) mark.run(nowIso, r.id);
    db.exec('COMMIT');
    return rows;
  } catch (err) {
    db.exec('ROLLBACK');
    throw err;
  }
}

export async function deliverBatch(
  db: Db,
  provider: SmsProvider,
  limit = 20,
  now = Date.now(),
  onOperatorAlert: OperatorSink = consoleOperatorSink,
): Promise<{ attempted: number; delivered: number; failed: number; deadLettered: number }> {
  const batch = claimBatch(db, limit, now);
  let delivered = 0;
  let failed = 0;
  let deadLettered = 0;

  const ok = db.prepare('UPDATE notifications SET delivered = 1, sent_at = ?, last_error = NULL WHERE id = ?');
  const bad = db.prepare('UPDATE notifications SET claimed_at = NULL, last_error = ? WHERE id = ?');

  for (const row of batch) {
    const res = await provider.send({
      to: row.phone, body: row.body, idempotencyKey: row.idempotency_key,
    });
    if (res.delivered) {
      ok.run(new Date(now).toISOString(), row.id);
      delivered++;
    } else {
      bad.run(res.error ?? 'unknown', row.id);
      failed++;

      const state = db.prepare(
        'SELECT attempts, subscriber_id, recall_id FROM notifications WHERE id = ?',
      ).get(row.id) as { attempts: number; subscriber_id: number; recall_id: number };

      if (Number(state.attempts) >= MAX_ATTEMPTS) {
        // Stop retrying and tell a person. `dead_lettered_at` keeps it out of future batches
        // without marking it delivered, because it was not delivered and the record must not
        // claim otherwise.
        db.prepare('UPDATE notifications SET dead_lettered_at = ? WHERE id = ?')
          .run(new Date(now).toISOString(), row.id);
        deadLettered++;
        await onOperatorAlert({
          kind: 'delivery_dead_letter',
          notificationId: row.id,
          subscriberId: Number(state.subscriber_id),
          recallId: Number(state.recall_id),
          attempts: Number(state.attempts),
          lastError: res.error ?? 'unknown',
        });
      }
    }
  }
  return { attempted: batch.length, delivered, failed, deadLettered };
}

export function unsubscribe(db: Db, phone: string, now = new Date().toISOString()): number {
  const sub = db.prepare('SELECT id FROM subscribers WHERE phone = ?').get(phone) as { id: number } | undefined;
  if (!sub) return 0;
  db.prepare('UPDATE subscribers SET active = 0 WHERE id = ?').run(sub.id);
  // Queued-but-unsent messages must die with the subscription, not arrive after STOP.
  const res = db.prepare(
    "UPDATE notifications SET delivered = 1, sent_at = ?, last_error = 'cancelled by STOP' " +
    'WHERE subscriber_id = ? AND delivered = 0',
  ).run(now, sub.id);
  return Number(res.changes);
}
