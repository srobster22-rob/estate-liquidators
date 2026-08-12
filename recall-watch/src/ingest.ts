import type { Db } from './db.js';
import type { RecallSource } from './sources/index.js';
import type { Recall } from './types.js';
import { consoleOperatorSink, type OperatorSink } from './operator.js';

/**
 * Idempotent ingest.
 *
 * The unique constraint on (source, source_ref) is the whole strategy. A poller that runs twice —
 * because of a retry, an overlapping cron, or a restart — must produce no new rows and no new
 * matches. `INSERT ... ON CONFLICT DO NOTHING` makes that a database property rather than a race
 * we hope not to lose.
 *
 * Existing rows are deliberately NOT updated. A recall notice can be revised, and silently
 * rewriting one that people were already notified about would change the record under them. A
 * revision should arrive as its own row with its own source_ref, or be handled explicitly by a
 * person. That decision is worth revisiting with real feed data — see VERIFY.md.
 */
export interface IngestResult {
  source: string;
  fetched: number;
  created: number;
  unchanged: number;
  /**
   * Set when this run returned nothing from a source that has produced records before.
   *
   * A run like that used to be indistinguishable from a quiet week: `error` null, counts zero,
   * dashboard green. It is the failure mode most likely to hurt somebody in production, because
   * every watch list then matches nothing and the system reports perfect health while doing it.
   */
  emptyFeedAlert?: boolean;
}

export async function ingest(
  db: Db,
  source: RecallSource,
  since: string,
  now = new Date().toISOString(),
  onOperatorAlert: OperatorSink = consoleOperatorSink,
): Promise<IngestResult> {
  const runIns = db.prepare(
    'INSERT INTO ingest_runs (source, started_at) VALUES (?, ?)',
  );
  const runId = Number(runIns.run(source.name, now).lastInsertRowid);

  let recalls: Recall[] = [];
  try {
    recalls = await source.fetchSince(since);
  } catch (err) {
    db.prepare('UPDATE ingest_runs SET finished_at = ?, error = ? WHERE id = ?')
      .run(now, String(err), runId);
    throw err;
  }

  const insert = db.prepare(`
    INSERT INTO recalls (source, source_ref, title, brands, products, upcs, code_info, hazard,
                         severity, remedy, announced_on, url, raw, first_seen_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (source, source_ref) DO NOTHING
  `);

  let created = 0;
  for (const r of recalls) {
    const res = insert.run(
      r.source, r.sourceRef, r.title,
      JSON.stringify(r.brands), JSON.stringify(r.products), JSON.stringify(r.upcs),
      r.codeInfo, r.hazard, r.severity, r.remedy, r.announcedOn, r.url,
      JSON.stringify(r.raw ?? {}), now,
    );
    if (res.changes > 0) created++;
  }

  const result: IngestResult = {
    source: source.name,
    fetched: recalls.length,
    created,
    unchanged: recalls.length - created,
  };

  // Checked before this run's own counts are written, so the comparison is against history and
  // not against itself.
  const best = db.prepare(
    'SELECT COALESCE(MAX(fetched), 0) b FROM ingest_runs WHERE source = ? AND id != ? AND error IS NULL',
  ).get(source.name, runId) as { b: number };
  const previousBest = Number(best.b);

  db.prepare(
    'UPDATE ingest_runs SET finished_at = ?, fetched = ?, created = ?, unchanged = ? WHERE id = ?',
  ).run(now, result.fetched, result.created, result.unchanged, runId);

  if (result.fetched === 0 && previousBest > 0) {
    result.emptyFeedAlert = true;
    db.prepare('UPDATE ingest_runs SET error = ? WHERE id = ?').run(
      `empty feed: returned 0 records; this source has returned as many as ${previousBest}`,
      runId,
    );
    await onOperatorAlert({ kind: 'empty_feed', source: source.name, previousBest, runId });
  }

  return result;
}

export function rowToRecall(row: Record<string, unknown>): Recall & { id: number } {
  return {
    id: Number(row.id),
    source: row.source as Recall['source'],
    sourceRef: String(row.source_ref),
    title: String(row.title),
    brands: JSON.parse(String(row.brands)),
    products: JSON.parse(String(row.products)),
    upcs: JSON.parse(String(row.upcs)),
    codeInfo: String(row.code_info ?? ''),
    hazard: String(row.hazard ?? ''),
    severity: row.severity as Recall['severity'],
    remedy: String(row.remedy ?? ''),
    announcedOn: String(row.announced_on),
    url: String(row.url ?? ''),
    raw: JSON.parse(String(row.raw ?? '{}')),
  };
}
