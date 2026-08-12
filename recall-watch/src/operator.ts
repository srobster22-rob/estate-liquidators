/**
 * Things a human has to be told about.
 *
 * This system's whole promise is that it speaks up when it matters, and its two worst failure
 * modes are both silent: a message that never arrives, and a feed that quietly stops producing
 * recalls. Neither shows up as an error. Both look exactly like a quiet week.
 *
 * So every condition that means "somebody is not being protected right now" goes through this
 * one channel, and the sink is an interface rather than a `console.error` so that a deployment
 * can wire it to something a person actually reads.
 */

export interface DeliveryDeadLetter {
  kind: 'delivery_dead_letter';
  notificationId: number;
  subscriberId: number;
  recallId: number;
  attempts: number;
  lastError: string;
}

/**
 * A feed that has always produced recalls produced none.
 *
 * Found in R11 while answering the hardening prompt's closing question — how does this hurt
 * somebody — and it was the honest answer for recall-watch. `ingest` recorded a zero-row fetch as
 * `fetched: 0, created: 0, error: null`: a successful run. An upstream schema change, a renamed
 * field, an endpoint that starts returning an empty array instead of a 500 — any of these give a
 * permanently green pipeline in which every watch list matches nothing and every dashboard reads
 * healthy. Pass 1 says it plainly: a zero displayed as data is worse than an error.
 *
 * The trigger is deliberately not a threshold. "Zero, from a source that has produced rows
 * before" needs no tuning and cannot be wrong about what it saw. A gentler rule — this week is
 * well below the usual — needs a number nobody here can source, and inventing one would put it
 * straight onto list B of the inventory.
 */
export interface EmptyFeed {
  kind: 'empty_feed';
  source: string;
  /** The largest number of records this source has ever returned in one run. */
  previousBest: number;
  runId: number;
}

export type OperatorAlert = DeliveryDeadLetter | EmptyFeed;

/** Where alerts go. Wire this to whatever a human actually reads. */
export type OperatorSink = (alert: OperatorAlert) => void | Promise<void>;

export function describeAlert(a: OperatorAlert): string {
  switch (a.kind) {
    case 'delivery_dead_letter':
      return `notification ${a.notificationId} for subscriber ${a.subscriberId} gave up after ` +
        `${a.attempts} attempts: ${a.lastError}. Somebody is not receiving recall alerts.`;
    case 'empty_feed':
      return `${a.source} returned no records (run ${a.runId}). It has returned as many as ` +
        `${a.previousBest} before, so this is a change in the feed, not a quiet week. Until it ` +
        'is fixed nobody is being matched against this source.';
  }
}

export const consoleOperatorSink: OperatorSink = (a) => {
  console.error(`[OPERATOR] ${describeAlert(a)}`);
};
