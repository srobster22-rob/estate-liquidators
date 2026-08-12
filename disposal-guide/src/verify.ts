import type { DataIndex, Location } from './types.js';

/**
 * The re-verification loop.
 *
 * The schema already refuses to ship a location without `verifiedOn` and `verifiedBy`. Nothing
 * kept them true. Hours change seasonally, facilities close, and a directory that silently rots
 * is worse than none — somebody drives to a locked gate on a Saturday with a bag of paint.
 *
 * The brief's target is fifteen seconds per call, so this is one location at a time with the
 * number as a tap-to-call link, the questions already written out, and three buttons. No
 * navigation, no forms to fill unless something changed.
 *
 * There is no server, so the outcome is recorded locally and exported as a YAML fragment the
 * maintainer pastes into `data/locations/local.yaml` and commits. That keeps the data in git
 * where it can be reviewed, which is where it belongs.
 */

export type Outcome = 'confirmed' | 'changed' | 'closed' | 'no_answer';

export interface VerifyRecord {
  locationId: string;
  outcome: Outcome;
  on: string;
  by: string;
  /** Free text when something changed — the maintainer transcribes it into the YAML. */
  note?: string;
}

const KEY = 'dg.verifications';

/** Days after which a location's hours should be re-checked. From the brief: 180. */
export const STALE_AFTER_DAYS = 180;

export function daysSince(iso: string | undefined, today: Date): number | null {
  if (!iso) return null;
  const then = Date.parse(`${iso}T00:00:00Z`);
  if (Number.isNaN(then)) return null;
  const now = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  return Math.floor((now - then) / 86_400_000);
}

export function isStale(loc: Location, today: Date): boolean {
  const d = daysSince(loc.verifiedOn, today);
  return d === null || d >= STALE_AFTER_DAYS;
}

/**
 * Oldest first, never-verified before everything, demo rows last.
 *
 * Demo rows sort last rather than being hidden: a maintainer looking at this screen should see
 * that the directory is still fictional, not an empty list that reads like "nothing to do".
 */
export function queue(index: DataIndex, today: Date, done: Set<string> = new Set()): Location[] {
  return [...index.locations]
    .filter((l) => !done.has(l.id))
    .sort((a, b) => {
      if (Boolean(a.isDemo) !== Boolean(b.isDemo)) return a.isDemo ? 1 : -1;
      const da = daysSince(a.verifiedOn, today);
      const db = daysSince(b.verifiedOn, today);
      if (da === null && db === null) return a.id.localeCompare(b.id);
      if (da === null) return -1;
      if (db === null) return 1;
      return db - da;
    });
}

/** The questions, in the order that gets them answered in under a minute of somebody's time. */
export function questions(loc: Location, index: DataIndex): string[] {
  const items = loc.acceptsSlugs
    .map((s) => index.items.find((i) => i.slug === s))
    .filter(Boolean)
    .slice(0, 6)
    .map((i) => i!.names.en[0])
    .join(', ');
  return [
    `Are you still taking these from households: ${items || '(nothing recorded)'}?`,
    'What are your hours right now, including any seasonal change?',
    'Do you charge for any of it? How much?',
    'Do I need to prove I live in the county? What counts?',
    'Any limit on how much someone can bring?',
    "Anything people often bring that you don't take?",
  ];
}

export function readVerifications(): VerifyRecord[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]') as VerifyRecord[];
  } catch {
    return [];
  }
}

/** Returns false when the device refused the write, so the caller can say so. */
export function recordVerification(rec: VerifyRecord): boolean {
  try {
    localStorage.setItem(KEY, JSON.stringify([...readVerifications(), rec]));
    return true;
  } catch {
    return false;
  }
}

function yamlString(s: string): string {
  return `'${s.replace(/'/g, "''")}'`;
}

/**
 * A YAML fragment to paste into `data/locations/local.yaml`.
 *
 * Deliberately not a full file: the maintainer merges it, so a bad call cannot silently wipe a
 * directory. Closures are emitted commented out with the reason, because deleting a row is a
 * decision a person should make with their eyes open.
 */
export function toYaml(records: VerifyRecord[], index: DataIndex): string {
  if (!records.length) return '# Nothing verified yet.\n';
  const byId = new Map(index.locations.map((l) => [l.id, l]));
  const lines = [
    '# Paste into data/locations/local.yaml, then run: npm run data',
    '# Only verifiedOn/verifiedBy are filled in here — transcribe any changes yourself.',
    '',
  ];
  for (const r of records) {
    const loc = byId.get(r.locationId);
    lines.push(`# ${loc?.name ?? r.locationId} — ${r.outcome} on ${r.on}`);
    if (r.note) lines.push(`#   note: ${r.note}`);
    if (r.outcome === 'closed') {
      lines.push(`#   CLOSED. Remove this location, or set active: false.`);
      lines.push(`# - id: ${r.locationId}`);
      lines.push(`#   active: false`);
    } else if (r.outcome === 'no_answer') {
      lines.push(`#   No answer — NOT verified. Try again; do not update the date.`);
    } else {
      lines.push(`- id: ${r.locationId}`);
      lines.push(`  verifiedOn: ${yamlString(r.on)}`);
      lines.push(`  verifiedBy: ${yamlString(r.by)}`);
      if (r.outcome === 'changed') {
        lines.push(`  # SOMETHING CHANGED — update the fields below before committing:`);
        lines.push(`  #   ${r.note ?? '(no note recorded)'}`);
      }
    }
    lines.push('');
  }
  return lines.join('\n');
}
