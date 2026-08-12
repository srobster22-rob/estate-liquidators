/**
 * A minimal ZIP writer, STORE only (no compression).
 *
 * WHY NOT A LIBRARY. The point of this export is that the photo bytes come out byte-identical
 * to what went in, so an adjuster or a lawyer can re-hash them against the manifest. Photos are
 * already compressed, so deflate would buy nothing and only add a transform between the stored
 * bytes and the delivered ones. STORE means the file in the archive *is* the file.
 *
 * It is ~120 lines and has no dependency, which matters for a page held to a byte budget.
 *
 * Verified against `unzip` and Python's `zipfile` rather than against itself — see
 * test/zip.test.ts. A self-checking archive writer proves nothing.
 */

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[i] = c >>> 0;
  }
  return t;
})();

export function crc32(bytes: Uint8Array): number {
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]!) & 0xff]! ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

/** MS-DOS date/time, which is what the format stores. Seconds have 2-second resolution. */
function dosDateTime(d: Date): { time: number; date: number } {
  const time = (d.getHours() << 11) | (d.getMinutes() << 5) | (Math.floor(d.getSeconds() / 2) & 0x1f);
  const date = (((d.getFullYear() - 1980) & 0x7f) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
  return { time, date };
}

export interface ZipEntry {
  /** Forward-slash separated path inside the archive. */
  name: string;
  bytes: Uint8Array;
  modified?: Date;
}

class Writer {
  private parts: Uint8Array[] = [];
  length = 0;

  push(b: Uint8Array): void {
    this.parts.push(b);
    this.length += b.length;
  }

  concat(): Uint8Array {
    const out = new Uint8Array(this.length);
    let at = 0;
    for (const p of this.parts) {
      out.set(p, at);
      at += p.length;
    }
    return out;
  }
}

function header(size: number, fill: (v: DataView) => void): Uint8Array {
  const buf = new Uint8Array(size);
  fill(new DataView(buf.buffer));
  return buf;
}

export function makeZip(entries: ZipEntry[]): Uint8Array {
  const out = new Writer();
  const central: { name: Uint8Array; crc: number; size: number; offset: number; time: number; date: number }[] = [];
  const encoder = new TextEncoder();

  for (const e of entries) {
    const name = encoder.encode(e.name);
    const crc = crc32(e.bytes);
    const { time, date } = dosDateTime(e.modified ?? new Date(2026, 0, 1));
    const offset = out.length;

    out.push(
      header(30, (v) => {
        v.setUint32(0, 0x04034b50, true); // local file header
        v.setUint16(4, 20, true); // version needed
        v.setUint16(6, 0x0800, true); // flags: UTF-8 filename
        v.setUint16(8, 0, true); // method: store
        v.setUint16(10, time, true);
        v.setUint16(12, date, true);
        v.setUint32(14, crc, true);
        v.setUint32(18, e.bytes.length, true); // compressed size == uncompressed
        v.setUint32(22, e.bytes.length, true);
        v.setUint16(26, name.length, true);
        v.setUint16(28, 0, true); // extra length
      }),
    );
    out.push(name);
    out.push(e.bytes);

    central.push({ name, crc, size: e.bytes.length, offset, time, date });
  }

  const cdStart = out.length;
  for (const c of central) {
    out.push(
      header(46, (v) => {
        v.setUint32(0, 0x02014b50, true); // central directory header
        v.setUint16(4, 20, true); // version made by
        v.setUint16(6, 20, true); // version needed
        v.setUint16(8, 0x0800, true);
        v.setUint16(10, 0, true); // store
        v.setUint16(12, c.time, true);
        v.setUint16(14, c.date, true);
        v.setUint32(16, c.crc, true);
        v.setUint32(20, c.size, true);
        v.setUint32(24, c.size, true);
        v.setUint16(28, c.name.length, true);
        v.setUint16(30, 0, true); // extra
        v.setUint16(32, 0, true); // comment
        v.setUint16(34, 0, true); // disk number
        v.setUint16(36, 0, true); // internal attrs
        v.setUint32(38, 0, true); // external attrs
        v.setUint32(42, c.offset, true);
      }),
    );
    out.push(c.name);
  }
  const cdSize = out.length - cdStart;

  out.push(
    header(22, (v) => {
      v.setUint32(0, 0x06054b50, true); // end of central directory
      v.setUint16(4, 0, true);
      v.setUint16(6, 0, true);
      v.setUint16(8, central.length, true);
      v.setUint16(10, central.length, true);
      v.setUint32(12, cdSize, true);
      v.setUint32(16, cdStart, true);
      v.setUint16(20, 0, true); // comment length
    }),
  );

  return out.concat();
}
