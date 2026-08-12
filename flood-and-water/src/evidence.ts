/**
 * The evidence layer: an append-only, hash-chained log and honest photo timestamps.
 *
 * This is the pattern projects 03, 13, 19, 22, 27 and 30 in the kit all specify and none had
 * implemented. It is deliberately narrow about what it proves.
 *
 * WHAT THE CHAIN PROVES: entries were not altered after they were created on this device.
 * WHAT IT DOES NOT PROVE: that the device clock was correct, that the events described happened,
 * or anything at all to a third party who does not trust the device. It is not a notarization
 * and it is not a blockchain. Overstating it in a document that ends up in front of an adjuster
 * or a judge damages the person relying on it, which is why `METHODOLOGY` below is exported and
 * required to be printed with any export.
 */

export interface ChainEntry {
  seq: number;
  createdAt: string;
  body: unknown;
  /** SHA-256 of `${seq}|${createdAt}|${canonical(body)}|${prevHash}` */
  contentHash: string;
  prevHash: string;
  /** Set when this entry corrects an earlier one. Both remain visible; nothing is overwritten. */
  correctsSeq?: number;
}

export const GENESIS = '0'.repeat(64);

/** Stable stringify — key order must not change a hash. */
export function canonical(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value) ?? 'null';
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${canonical(obj[k])}`).join(',')}}`;
}

async function sha256Hex(input: string | Uint8Array): Promise<string> {
  const bytes = typeof input === 'string' ? new TextEncoder().encode(input) : input;
  const digest = await crypto.subtle.digest('SHA-256', bytes as BufferSource);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function hashBytes(bytes: Uint8Array): Promise<string> {
  return sha256Hex(bytes);
}

export async function appendEntry(
  chain: ChainEntry[],
  body: unknown,
  createdAt: string,
  correctsSeq?: number,
): Promise<ChainEntry> {
  const prev = chain[chain.length - 1];
  const seq = (prev?.seq ?? 0) + 1;
  const prevHash = prev?.contentHash ?? GENESIS;
  const contentHash = await sha256Hex(`${seq}|${createdAt}|${canonical(body)}|${prevHash}`);
  return { seq, createdAt, body, contentHash, prevHash, ...(correctsSeq ? { correctsSeq } : {}) };
}

export interface ChainCheck {
  intact: boolean;
  /** seq of the first entry that fails, if any. */
  brokenAt?: number;
  reason?: string;
}

export async function verifyChain(chain: ChainEntry[]): Promise<ChainCheck> {
  let prevHash = GENESIS;
  for (const [i, e] of chain.entries()) {
    if (e.seq !== i + 1) return { intact: false, brokenAt: e.seq, reason: 'sequence out of order' };
    if (e.prevHash !== prevHash) return { intact: false, brokenAt: e.seq, reason: 'previous hash mismatch' };
    const expected = await sha256Hex(`${e.seq}|${e.createdAt}|${canonical(e.body)}|${e.prevHash}`);
    if (expected !== e.contentHash) return { intact: false, brokenAt: e.seq, reason: 'content altered' };
    prevHash = e.contentHash;
  }
  return { intact: true };
}

// --------------------------------------------------------------------------- photo timestamps

export type TimestampKind = 'camera' | 'import-only';

/**
 * What ELSE the original file is carrying.
 *
 * Found by running the hardening prompt's Pass 2.6 — "check what an exported file contains that
 * the screen didn't". This app reads exactly one EXIF tag, DateTimeOriginal, and shows a date.
 * The originals archive then hands over the whole unmodified file, and a phone photo routinely
 * carries the GPS coordinates it was taken at, the device's serial number, and sometimes an
 * owner name — none of which appears anywhere on screen.
 *
 * Stripping it is the wrong fix and was rejected: the unmodified bytes ARE the evidence, editing
 * them changes the SHA-256 that the whole chain is built on, and a stripped photo is worth less
 * to the person than an intact one. What was actually missing is that nobody was told. So the
 * app now looks for these tags at import, records only whether each is PRESENT, and warns before
 * the archive leaves the device.
 *
 * Note what is deliberately NOT stored: no coordinates, no serial, no name. A flag saying a file
 * knows where it was taken is not itself a location, and this record is the last place that
 * should acquire one.
 */
export interface EmbeddedMetadata {
  location: boolean;
  deviceSerial: boolean;
  owner: boolean;
}

export interface PhotoRecord {
  /** SHA-256 of the ORIGINAL bytes, unmodified. Never of a re-encoded or resized copy. */
  sha256: string;
  byteSize: number;
  mime: string;
  /** From EXIF DateTimeOriginal. Null when the file carries none. */
  exifDateTimeOriginal: string | null;
  exifPresent: boolean;
  /** When this device read the file. Always known, never a substitute for the above. */
  importedAt: string;
  kind: TimestampKind;
  /** Absent on entries recorded before this was checked — which is not the same as "none". */
  embedded?: EmbeddedMetadata;
}

export function embeddedLabels(m: EmbeddedMetadata | undefined): string[] {
  if (!m) return [];
  return [
    m.location && 'the place it was taken',
    m.deviceSerial && 'the camera or phone serial number',
    m.owner && 'the owner name set on the camera',
  ].filter((s): s is string => Boolean(s));
}

/** How many photos in the chain carry each kind of hidden detail. */
export function embeddedSummary(chain: ChainEntry[]): { photos: number; withAny: number; labels: string[] } {
  const labels = new Set<string>();
  let photos = 0;
  let withAny = 0;
  for (const e of chain) {
    const photo = (e.body as { photo?: PhotoRecord }).photo;
    if (!photo) continue;
    photos++;
    const found = embeddedLabels(photo.embedded);
    if (found.length) {
      withAny++;
      for (const l of found) labels.add(l);
    }
  }
  return { photos, withAny, labels: [...labels] };
}

/**
 * The distinction that carries the entire evidentiary value.
 *
 * Photos forwarded through messaging apps usually have their metadata stripped. A naive
 * implementation shows the import date and implicitly presents it as when the photo was taken —
 * which is the single detail most likely to be challenged and the one most tools get wrong.
 *
 * So: when EXIF is absent we say so, in those words, and we never fall back to the import time
 * as if it were a capture time.
 */
export function describeTimestamp(p: PhotoRecord): string {
  return p.exifPresent && p.exifDateTimeOriginal
    ? `Taken ${p.exifDateTimeOriginal} (from the camera). Added to this record ${p.importedAt}.`
    : `No camera timestamp in this file. Added to this record ${p.importedAt}.`;
}

export function makePhotoRecord(args: {
  sha256: string;
  byteSize: number;
  mime: string;
  exifDateTimeOriginal: string | null;
  importedAt: string;
  embedded?: EmbeddedMetadata;
}): PhotoRecord {
  const exifPresent = Boolean(args.exifDateTimeOriginal);
  return {
    ...args,
    exifPresent,
    kind: exifPresent ? 'camera' : 'import-only',
  };
}

/** Printed with every export. Understating what this proves is the point. */
export const METHODOLOGY = [
  'How this record was kept',
  '',
  'Entries in this log are append-only. Editing an entry does not replace it — it adds a',
  'correction, and both remain visible with their original times.',
  '',
  'Each entry stores a SHA-256 hash of its own contents together with the hash of the entry',
  'before it. If any entry were altered after it was created, the chain would no longer match',
  'and the check would report where.',
  '',
  'What this shows: entries were not changed after they were written on this device.',
  '',
  'What it does not show: that the device clock was correct, that the events described here',
  'happened as described, or anything verifiable by someone who does not trust this device.',
  'It is not a notarization.',
  '',
  'Photograph times come from the camera metadata (EXIF DateTimeOriginal) when the file has it.',
  'Many photos sent through messaging apps have that metadata removed. Where it is missing this',
  'record says so and shows only when the file was added, which is not the same thing.',
  '',
  'Photographs are included exactly as the camera wrote them, with nothing removed. That is what',
  'makes them worth anything as evidence, and it also means a file may carry details that do not',
  'appear anywhere in this document — commonly the place it was taken and the device serial',
  'number. Anyone sending this record on should know that.',
].join('\n');

// --------------------------------------------------------------------------- typed entries

/**
 * What an entry can be.
 *
 * All four ride the same append-only hash chain — a receipt is evidence in exactly the way a
 * photo is, and splitting them into separate stores would mean two things to keep honest instead
 * of one. The discriminator lets the PDF and the manifest group them without the chain caring.
 */
export type EntryKind = 'note' | 'damage' | 'call' | 'receipt';

export interface DamageItemBody {
  kind: 'damage';
  room: string;
  description: string;
  /** What it cost when it was bought, in integer cents. NOT an estimate of what it is owed. */
  purchaseCostCents: number | null;
  purchaseYear: number | null;
  condition: 'ruined' | 'damaged' | 'maybe-dryable' | 'unknown';
  note?: string;
}

export interface CallBody {
  kind: 'call';
  party: string;
  person: string;
  claimNumber?: string;
  summary: string;
  promised?: string;
}

export interface ReceiptBody {
  kind: 'receipt';
  vendor: string;
  amountCents: number;
  category: 'drying' | 'repair' | 'lodging' | 'meals' | 'other';
  datedOn: string;
  note?: string;
}

export interface NoteBody {
  kind?: 'note';
  note: string;
  photo?: PhotoRecord;
}

export type EntryBody = NoteBody | DamageItemBody | CallBody | ReceiptBody;

export function entryKind(body: unknown): EntryKind {
  const k = (body as { kind?: string })?.kind;
  return k === 'damage' || k === 'call' || k === 'receipt' ? k : 'note';
}

/**
 * "$1,234.56" -> 123456. Returns null on anything it cannot read confidently.
 *
 * Parsed to integer cents rather than a float, because this number ends up in a document an
 * adjuster reads and a cent of drift is an argument nobody needs. Rounds the cents rather than
 * truncating, and refuses more than two decimal places rather than silently discarding digits.
 */
export function parseMoneyToCents(input: string): number | null {
  const cleaned = input.trim().replace(/[$\s,]/g, '');
  if (!cleaned) return null;
  if (!/^-?\d*(\.\d{1,2})?$/.test(cleaned)) return null;
  const negative = cleaned.startsWith('-');
  const [whole = '0', frac = ''] = cleaned.replace('-', '').split('.');
  if (whole === '' && frac === '') return null;
  const cents = Number(whole || '0') * 100 + Number(frac.padEnd(2, '0') || '0');
  if (!Number.isSafeInteger(cents)) return null;
  return negative ? -cents : cents;
}

/** Integer cents in, formatted dollars out. Money never touches a float here. */
export function formatCents(cents: number): string {
  const sign = cents < 0 ? '-' : '';
  const abs = Math.abs(cents);
  return `${sign}$${Math.floor(abs / 100).toLocaleString('en-US')}.${String(abs % 100).padStart(2, '0')}`;
}

/**
 * Sums receipts only.
 *
 * Deliberately NOT a sum of damage items. The brief bans claim estimates and damage valuation,
 * and for good reason: a number on the screen becomes an expectation, and this app has no
 * business appraising anything. Receipts are different — they are money the household actually
 * spent, with paper to show for it, and additional living expenses go unclaimed constantly for
 * exactly the lack of that total.
 */
export function receiptsTotalCents(chain: ChainEntry[]): number {
  return chain.reduce((sum, e) => {
    const b = e.body as ReceiptBody;
    return entryKind(b) === 'receipt' ? sum + (b.amountCents || 0) : sum;
  }, 0);
}

export function countByKind(chain: ChainEntry[]): Record<EntryKind, number> {
  const out: Record<EntryKind, number> = { note: 0, damage: 0, call: 0, receipt: 0 };
  for (const e of chain) out[entryKind(e.body)]++;
  return out;
}
