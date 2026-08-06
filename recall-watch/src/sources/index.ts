import type { Recall } from '../types.js';

/**
 * One implementation per feed, plus a fixture implementation that replays recorded responses.
 *
 * The fixture path is not a testing convenience. It is what lets the entire pipeline — ingest,
 * match, notify — run and be verified with no network and no credentials, which is the only way
 * the matching logic can be trusted by someone who cannot reach the feeds.
 */
export interface RecallSource {
  readonly name: string;
  fetchSince(sinceISODate: string): Promise<Recall[]>;
}
