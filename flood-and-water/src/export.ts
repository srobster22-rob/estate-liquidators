import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';
import { makeZip } from './zip.js';
import {
  METHODOLOGY, verifyChain, describeTimestamp,
  type ChainEntry, type ChainCheck, type PhotoRecord,
} from './evidence.js';

/**
 * The claim packet.
 *
 * A hash-chained log on somebody's phone is not evidence until it is something they can hand to
 * an adjuster. This is that artifact, and it is deliberately plain: a cover page, the entries in
 * order with their times and hashes, and the methodology statement — which is printed with every
 * export precisely because it says what the record does NOT prove.
 *
 * The chain-check result is printed whether it passes or fails. A packet that quietly omitted a
 * broken chain would be worse than no packet.
 */

const MARGIN = 50;
const LINE = 14;

interface Ctx {
  doc: PDFDocument;
  page: import('pdf-lib').PDFPage;
  y: number;
  font: import('pdf-lib').PDFFont;
  bold: import('pdf-lib').PDFFont;
}

function newPage(ctx: Ctx): void {
  ctx.page = ctx.doc.addPage([612, 792]);
  ctx.y = 792 - MARGIN;
}

function write(ctx: Ctx, text: string, opts: { bold?: boolean; size?: number; gap?: number } = {}): void {
  const size = opts.size ?? 10;
  const font = opts.bold ? ctx.bold : ctx.font;
  const maxWidth = 612 - MARGIN * 2;

  for (const paragraph of text.split('\n')) {
    const words = paragraph.split(' ');
    let line = '';
    const flush = () => {
      if (ctx.y < MARGIN + LINE) newPage(ctx);
      ctx.page.drawText(line, { x: MARGIN, y: ctx.y, size, font, color: rgb(0, 0, 0) });
      ctx.y -= LINE;
      line = '';
    };
    for (const w of words) {
      const next = line ? `${line} ${w}` : w;
      if (font.widthOfTextAtSize(next, size) > maxWidth) flush();
      line = line ? `${line} ${w}` : w;
    }
    flush();
  }
  ctx.y -= opts.gap ?? 4;
}

export async function buildPacket(chain: ChainEntry[], now: string): Promise<Uint8Array> {
  const doc = await PDFDocument.create();
  const font = await doc.embedFont(StandardFonts.Helvetica);
  const bold = await doc.embedFont(StandardFonts.HelveticaBold);
  const ctx: Ctx = { doc, page: doc.addPage([612, 792]), y: 792 - MARGIN, font, bold };

  const check = await verifyChain(chain);
  const first = chain[0]?.createdAt?.slice(0, 10) ?? '—';
  const last = chain[chain.length - 1]?.createdAt?.slice(0, 10) ?? '—';

  write(ctx, 'Water damage record', { bold: true, size: 18, gap: 10 });
  write(ctx, `Exported ${now}`, { size: 10 });
  write(ctx, `${chain.length} ${chain.length === 1 ? 'entry' : 'entries'}, ${first} to ${last}`, { size: 10 });
  write(
    ctx,
    check.intact
      ? 'Chain check: intact. No entry was altered after it was written.'
      : `Chain check: BROKEN at entry #${check.brokenAt} (${check.reason}).`,
    { bold: true, size: 10, gap: 14 },
  );
  write(
    ctx,
    'Kept by the household using a local record-keeping tool. Not prepared by an insurer, an ' +
      'adjuster, or a contractor. See the methodology page at the end for exactly what this ' +
      'record does and does not establish.',
    { size: 9, gap: 16 },
  );

  write(ctx, 'Entries', { bold: true, size: 13, gap: 8 });
  if (!chain.length) write(ctx, 'No entries.', { size: 10 });

  for (const e of chain) {
    const b = e.body as Record<string, unknown>;
    const photo = b.photo as PhotoRecord | undefined;
    write(
      ctx,
      `#${e.seq}${e.correctsSeq ? ` (correction to #${e.correctsSeq})` : ''} — recorded ${e.createdAt}`,
      { bold: true, size: 10, gap: 2 },
    );
    if (b.note) write(ctx, String(b.note), { size: 10, gap: 2 });
    if (photo) {
      write(ctx, describeTimestamp(photo), { size: 9, gap: 2 });
      write(ctx, `Photo SHA-256: ${photo.sha256}`, { size: 8, gap: 2 });
      write(ctx, `${photo.byteSize} bytes, ${photo.mime}`, { size: 8, gap: 2 });
    }
    write(ctx, `Entry hash: ${e.contentHash}`, { size: 8, gap: 10 });
  }

  newPage(ctx);
  write(ctx, METHODOLOGY, { size: 10 });

  return doc.save();
}

export function downloadBlob(bytes: Uint8Array, filename: string): void {
  const blob = new Blob([bytes as unknown as BlobPart], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// --------------------------------------------------------------------------- originals

/**
 * The originals archive.
 *
 * The PDF is for reading; this is for verifying. An adjuster or a lawyer gets the photo files
 * exactly as they came off the camera, plus a manifest they can re-hash them against. If the
 * bytes had been resized, re-encoded, or stripped of metadata on the way out, the SHA-256 in the
 * record would prove nothing about the file in their hands.
 */
export interface ManifestEntry {
  seq: number;
  file: string;
  sha256: string;
  byteSize: number;
  mime: string;
  cameraTimestamp: string | null;
  addedToRecord: string;
  note: string;
}

const EXT: Record<string, string> = {
  'image/jpeg': 'jpg', 'image/png': 'png', 'image/heic': 'heic',
  'image/heif': 'heif', 'image/webp': 'webp',
};

export async function buildOriginalsZip(
  chain: ChainEntry[],
  getBytes: (sha256: string) => Promise<Uint8Array | undefined>,
  chainCheck: ChainCheck,
  exportedOn: string,
): Promise<{ zip: Uint8Array; missing: string[] }> {
  const files: { name: string; bytes: Uint8Array }[] = [];
  const entries: ManifestEntry[] = [];
  const missing: string[] = [];

  for (const e of chain) {
    const body = e.body as Record<string, unknown>;
    const photo = body.photo as PhotoRecord | undefined;
    if (!photo) continue;

    const bytes = await getBytes(photo.sha256);
    if (!bytes) {
      // Recorded but no longer on the device. Say so in the manifest rather than omitting it —
      // a gap the reader can see beats a gap they cannot.
      missing.push(photo.sha256);
      continue;
    }

    const name = `photos/${String(e.seq).padStart(3, '0')}-${photo.sha256.slice(0, 12)}.${EXT[photo.mime] ?? 'bin'}`;
    files.push({ name, bytes });
    entries.push({
      seq: e.seq,
      file: name,
      sha256: photo.sha256,
      byteSize: photo.byteSize,
      mime: photo.mime,
      cameraTimestamp: photo.exifPresent ? photo.exifDateTimeOriginal : null,
      addedToRecord: photo.importedAt,
      note: String(body.note ?? ''),
    });
  }

  const manifest = {
    exportedOn,
    entryCount: chain.length,
    photoCount: entries.length,
    chainIntact: chainCheck.intact,
    chainBrokenAt: chainCheck.brokenAt ?? null,
    missingFromDevice: missing,
    howToVerify:
      'Each file below is the original, unmodified. Re-compute its SHA-256 and compare it to ' +
      'the value here. On macOS or Linux: shasum -a 256 <file>',
    cameraTimestampNote:
      'cameraTimestamp is null when the file carried no EXIF DateTimeOriginal — common for ' +
      'photos sent through a messaging app. It is NOT the same as addedToRecord, and a null ' +
      'here does not mean the photo was taken on the date it was added.',
    photos: entries,
  };

  files.unshift({
    name: 'manifest.json',
    bytes: new TextEncoder().encode(JSON.stringify(manifest, null, 2)),
  });
  files.push({ name: 'METHODOLOGY.txt', bytes: new TextEncoder().encode(METHODOLOGY) });

  return { zip: makeZip(files), missing };
}

export function downloadZip(bytes: Uint8Array, filename: string): void {
  const blob = new Blob([bytes as unknown as BlobPart], { type: 'application/zip' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
