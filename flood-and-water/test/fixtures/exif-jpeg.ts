/**
 * A real JPEG carrying a real EXIF block, built byte by byte.
 *
 * It exists because of a gap found in R10: every photo test in this project used a file with no
 * EXIF, and asserted that the camera timestamp came back null. So the single distinction the
 * evidence layer calls load-bearing — a camera timestamp is not an import timestamp — was only
 * ever tested in the case where there is no camera timestamp. The happy path was never run.
 *
 * That is not a hypothetical worry. The EXIF read sits inside a try/catch whose comment says a
 * failure means "no EXIF", so anything that throws — including the module not exposing `parse`
 * where the code expects it — degrades silently into "No camera timestamp in this file" on every
 * photo. A wrong answer, delivered confidently, in the one place this app has to be right.
 *
 * Generated rather than committed as a binary so the contents are reviewable: the GPS IFD here
 * is what lets the metadata-disclosure test prove it is reading a genuine coordinate block.
 */

function u16(v: number): Uint8Array {
  return new Uint8Array([(v >> 8) & 0xff, v & 0xff]);
}
function u32(v: number): Uint8Array {
  return new Uint8Array([(v >>> 24) & 0xff, (v >>> 16) & 0xff, (v >>> 8) & 0xff, v & 0xff]);
}
function concat(parts: Uint8Array[]): Uint8Array {
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let at = 0;
  for (const p of parts) { out.set(p, at); at += p.length; }
  return out;
}
function ascii(s: string): Uint8Array {
  return new TextEncoder().encode(s);
}
function entry(tag: number, type: number, count: number, value: number | Uint8Array): Uint8Array {
  return concat([u16(tag), u16(type), u32(count), typeof value === 'number' ? u32(value) : value]);
}

export interface ExifJpegOptions {
  /** EXIF DateTimeOriginal, in EXIF's own "YYYY:MM:DD HH:MM:SS" form. */
  takenAt?: string;
  /** Include a GPS IFD with a real latitude. */
  withGps?: boolean;
}

export function makeExifJpeg(opts: ExifJpegOptions = {}): Uint8Array {
  const takenAt = opts.takenAt ?? '2026:03:02 10:15:00';
  const withGps = opts.withGps ?? true;

  const dt = ascii(`${takenAt}\0`);
  const ifd0Count = withGps ? 2 : 1;
  const exifIfdOffset = 8 + 2 + ifd0Count * 12 + 4;
  const exifDataOffset = exifIfdOffset + 2 + 1 * 12 + 4;
  const gpsIfdOffset = exifDataOffset + dt.length;
  const gpsDataOffset = gpsIfdOffset + 2 + 3 * 12 + 4;

  const ifd0 = [entry(0x8769, 4, 1, exifIfdOffset)];
  if (withGps) ifd0.push(entry(0x8825, 4, 1, gpsIfdOffset));

  const parts: Uint8Array[] = [
    ascii('MM'), u16(42), u32(8),                       // big-endian TIFF header, IFD0 at 8
    u16(ifd0.length), ...ifd0, u32(0),                  // IFD0
    u16(1), entry(0x9003, 2, dt.length, exifDataOffset), u32(0), dt,  // Exif IFD: DateTimeOriginal
  ];

  if (withGps) {
    parts.push(
      u16(3),
      entry(0x0001, 2, 2, concat([ascii('N\0'), new Uint8Array(2)])),  // GPSLatitudeRef
      entry(0x0002, 5, 3, gpsDataOffset),                              // GPSLatitude
      entry(0x0003, 2, 2, concat([ascii('W\0'), new Uint8Array(2)])),  // GPSLongitudeRef
      u32(0),
      u32(29), u32(1), u32(58), u32(1), u32(30), u32(1),               // 29° 58' 30"
    );
  }

  const app1 = concat([ascii('Exif\0\0'), concat(parts)]);
  return concat([
    new Uint8Array([0xff, 0xd8]),                        // SOI
    new Uint8Array([0xff, 0xe1]), u16(app1.length + 2), app1,
    new Uint8Array([0xff, 0xdb]), u16(67), new Uint8Array([0]), new Uint8Array(64).fill(16),
    new Uint8Array([0xff, 0xd9]),                        // EOI
  ]);
}
