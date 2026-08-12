import { describe, it, expect } from 'vitest';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { makeZip, crc32 } from '../src/zip.js';

/**
 * Verified against `unzip` and Python's `zipfile` — two implementations that know nothing about
 * this writer. Checking an archive writer with its own reader proves only that it is
 * self-consistent, which is the limitation recall-watch's eval harness had to document about
 * itself. Here an independent tool is available, so use it.
 */

function tmp(): string {
  return mkdtempSync(join(tmpdir(), 'zip-test-'));
}

function writeZip(entries: { name: string; bytes: Uint8Array }[]): string {
  const dir = tmp();
  const path = join(dir, 'out.zip');
  writeFileSync(path, makeZip(entries));
  return path;
}

const enc = (s: string) => new TextEncoder().encode(s);
const sha = (b: Uint8Array) => createHash('sha256').update(b).digest('hex');

describe('crc32', () => {
  it('matches the standard check value for "123456789"', () => {
    // If this is wrong, every archive is subtly corrupt and only a stricter tool would notice.
    expect(crc32(enc('123456789')).toString(16)).toBe('cbf43926');
  });

  it('is zero for empty input', () => {
    expect(crc32(new Uint8Array(0))).toBe(0);
  });
});

describe('the archive is valid to tools that did not write it', () => {
  it('passes `unzip -t`', () => {
    const path = writeZip([
      { name: 'manifest.json', bytes: enc('{"entries":1}') },
      { name: 'photos/one.bin', bytes: new Uint8Array([0, 1, 2, 255, 254, 0, 0, 7]) },
    ]);
    const out = execFileSync('unzip', ['-t', path], { encoding: 'utf8' });
    expect(out).toContain('No errors detected');
  });

  it('Python zipfile reads it and agrees on every byte', () => {
    const payloads = [
      { name: 'manifest.json', bytes: enc('{"hello":"world"}') },
      { name: 'photos/a.bin', bytes: new Uint8Array(Array.from({ length: 5000 }, (_, i) => i % 256)) },
      { name: 'photos/b.bin', bytes: new Uint8Array(0) },
      { name: 'photos/unicode-ñ.txt', bytes: enc('agua — 3 pulgadas') },
    ];
    const path = writeZip(payloads);

    const script = [
      'import json, zipfile, hashlib',
      `z = zipfile.ZipFile(${JSON.stringify(path)})`,
      'out = {"bad": z.testzip(), "names": z.namelist(), "hashes": {}}',
      'for n in z.namelist(): out["hashes"][n] = hashlib.sha256(z.read(n)).hexdigest()',
      'print(json.dumps(out))',
    ].join('\n');
    const result = JSON.parse(execFileSync('python3', ['-c', script], { encoding: 'utf8' }));

    expect(result.bad).toBeNull();
    expect(result.names).toEqual(payloads.map((p) => p.name));
    for (const p of payloads) {
      expect(result.hashes[p.name], `${p.name} round-trips byte-identically`).toBe(sha(p.bytes));
    }
  });

  it('extracted bytes are identical to the input, which is the whole point', () => {
    // Every byte value, so nothing is mangled by an encoding assumption somewhere.
    const bytes = new Uint8Array(256);
    for (let i = 0; i < 256; i++) bytes[i] = i;
    const path = writeZip([{ name: 'photos/all-bytes.bin', bytes }]);
    const dir = tmp();
    execFileSync('unzip', ['-q', path, '-d', dir]);
    expect(sha(new Uint8Array(readFileSync(join(dir, 'photos/all-bytes.bin'))))).toBe(sha(bytes));
  });

  it('an archive with no entries is structurally valid, not corrupt', () => {
    // `unzip` exits non-zero here with "zipfile is empty" — a warning about content, not a
    // structural complaint. Python parses the same bytes as a valid empty archive. Asserted
    // both ways because the first version of this test read the non-zero exit as a failure.
    const path = writeZip([]);
    let unzipSaid = '';
    try {
      execFileSync('unzip', ['-l', path], { encoding: 'utf8' });
    } catch (err) {
      const e = err as { stdout?: string; stderr?: string };
      unzipSaid = `${e.stdout ?? ''}${e.stderr ?? ''}`;
    }
    expect(unzipSaid).toContain('zipfile is empty');

    const script = [
      'import json, zipfile',
      `z = zipfile.ZipFile(${JSON.stringify(path)})`,
      'print(json.dumps({"names": z.namelist(), "bad": z.testzip()}))',
    ].join('\n');
    const parsed = JSON.parse(execFileSync('python3', ['-c', script], { encoding: 'utf8' }));
    expect(parsed.names).toEqual([]);
    expect(parsed.bad).toBeNull();
  });

  it('handles a file large enough to cross a buffer boundary', () => {
    const bytes = new Uint8Array(300_000);
    for (let i = 0; i < bytes.length; i++) bytes[i] = (i * 31) % 256;
    const path = writeZip([{ name: 'photos/big.bin', bytes }]);
    const dir = tmp();
    execFileSync('unzip', ['-q', path, '-d', dir]);
    expect(sha(new Uint8Array(readFileSync(join(dir, 'photos/big.bin'))))).toBe(sha(bytes));
  });
});
