import type { Db } from './db.js';
import type { RecallSource } from './sources/index.js';
import type { Recall } from './types.js';

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
}

export async function ingest(
  db: Db,
  source: RecallSource,
  since: string,
  now = new Date().toISOString(),
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

  db.prepare(
    'UPDATE ingest_runs SET finished_at = ?, fetched = ?, created = ?, unchanged = ? WHERE id = ?',
  ).run(now, result.fetched, result.created, result.unchanged, runId);

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
