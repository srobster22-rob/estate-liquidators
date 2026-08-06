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
].join('\n');
