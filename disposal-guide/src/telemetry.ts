/**
 * The zero-results log is the project's roadmap: every search that finds nothing is a synonym
 * somebody needs. It is also the only thing this app records, and it records the query string
 * and nothing else.
 *
 * No IP (there is no server by default), no session id, no timestamp finer than the day, no
 * ordering that would let queries be stitched back into one person's visit. Someone searching
 * "needles" or "medication" is telling you something about their household; the log must not be
 * able to give them away.
 */

const KEY = 'dg.zeroresults';
const MAX = 500;

interface ZeroResult {
  q: string;
  lang: string;
  /** Day only. Deliberately coarse. */
  day: string;
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function logZeroResult(query: string, lang: string): void {
  const q = query.trim().toLowerCase();
  if (!q || q.length > 80) return;
  try {
    const existing: ZeroResult[] = JSON.parse(localStorage.getItem(KEY) ?? '[]');
    // De-duplicate within the day so a slow typist doesn't record "b", "ba", "bat", "batt".
    if (existing.some((r) => r.q === q && r.day === today())) return;
    existing.push({ q, lang, day: today() });
    localStorage.setItem(KEY, JSON.stringify(existing.slice(-MAX)));
  } catch {
    /* storage full or blocked — never break search over telemetry */
  }
}

export function readZeroResults(): ZeroResult[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]');
  } catch {
    return [];
  }
}

/**
 * Optional upload target. Unset by default, which is why the app makes zero network requests
 * out of the box. If you set it, point it at your own host — never a third party — and have it
 * store the query string and nothing the request itself reveals.
 */
export const UPLOAD_ENDPOINT: string | null = null;
