import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import indexData from '../src/generated/index.json';
import type { DataIndex } from '../src/types.js';
import { waitingPeriod, assessGaps, addDays, toISODate } from '../src/coverage.js';
import {
  appendEntry, verifyChain, canonical, makePhotoRecord, describeTimestamp, GENESIS, hashBytes,
} from '../src/evidence.js';

const data = indexData as unknown as DataIndex;
const root = join(import.meta.dirname, '..');

// --- the waiting period, which is the product --------------------------------

describe('the waiting period renders as a date', () => {
  it('standard purchase lands 30 days out', () => {
    const r = waitingPeriod(data.coverage, new Date('2026-03-01T00:00:00Z'));
    expect(r.days).toBe(30);
    expect(r.ruleId).toBe('standard');
    expect(r.effectiveOn).toBe('2026-03-31');
  });

  it('a mortgage purchase has no wait', () => {
    const r = waitingPeriod(data.coverage, new Date('2026-03-01T00:00:00Z'), ['mortgage']);
    expect(r.days).toBe(0);
    expect(r.effectiveOn).toBe('2026-03-01');
  });

  it('the newly-mapped exception is one day', () => {
    const r = waitingPeriod(data.coverage, new Date('2026-03-01T00:00:00Z'), ['newly-mapped']);
    expect(r.effectiveOn).toBe('2026-03-02');
  });

  it('when two exceptions apply, the shorter wait wins', () => {
    // Wrong in the other direction costs coverage. Encode the asymmetry, test the asymmetry.
    const r = waitingPeriod(data.coverage, new Date('2026-03-01T00:00:00Z'), [
      'newly-mapped',
      'mortgage',
    ]);
    expect(r.days).toBe(0);
    expect(r.ruleId).toBe('mortgage');
  });

  it('an unknown exception id is ignored rather than shortening the wait', () => {
    const r = waitingPeriod(data.coverage, new Date('2026-03-01T00:00:00Z'), ['nonsense']);
    expect(r.days).toBe(30);
  });

  it('crossing a DST transition does not shift the date', () => {
    // US DST starts 2026-03-08 and ends 2026-11-01. Calendar arithmetic in UTC must be immune.
    expect(toISODate(addDays(new Date('2026-03-01T00:00:00Z'), 30))).toBe('2026-03-31');
    expect(toISODate(addDays(new Date('2026-10-20T00:00:00Z'), 30))).toBe('2026-11-19');
  });

  it('handles a leap day', () => {
    expect(toISODate(addDays(new Date('2028-02-01T00:00:00Z'), 30))).toBe('2028-03-02');
  });

  it('carries its sources', () => {
    const r = waitingPeriod(data.coverage, new Date('2026-03-01T00:00:00Z'));
    expect(r.sources.length).toBeGreaterThan(0);
    for (const s of r.sources) expect(s.url).toMatch(/^https:/);
  });
});

// --- gaps --------------------------------------------------------------------

describe('coverage gaps', () => {
  it('"I do not know" is never treated as "I do not have it"', () => {
    const v = assessGaps(data.coverage, [{ gapId: 'flood', state: 'unknown' }]);
    const flood = v.find((x) => x.gap.id === 'flood')!;
    expect(flood.isGap).toBe(false);
    expect(flood.needsChecking).toBe(true);
  });

  it('an unanswered gap defaults to unknown, not to a gap', () => {
    const v = assessGaps(data.coverage, []);
    expect(v.every((x) => !x.isGap)).toBe(true);
    expect(v.every((x) => x.needsChecking)).toBe(true);
  });

  it('only an explicit no is a confirmed gap', () => {
    const v = assessGaps(data.coverage, [{ gapId: 'sewer-backup', state: 'no' }]);
    expect(v.find((x) => x.gap.id === 'sewer-backup')!.isGap).toBe(true);
  });

  it('every gap tells you the phrase to search your own paperwork for', () => {
    for (const v of assessGaps(data.coverage, [])) {
      expect(v.lookFor.length, v.gap.id).toBeGreaterThan(10);
    }
  });

  it('the sewer backup gap explains that flood insurance does not cover it either', () => {
    const g = data.coverage.gaps.find((x) => x.id === 'sewer-backup')!;
    expect(g.why.toLowerCase()).toContain('flood insurance');
  });

  it('renters get the contents-only sentence', () => {
    expect(data.coverage.gaps.find((g) => g.id === 'flood')!.rentersNote).toBeTruthy();
  });
});

// --- sourcing ----------------------------------------------------------------

describe('every claim is cited', () => {
  it('every life-safety point has at least one source with a retrieval date', () => {
    for (const p of data.safety.emergency.points) {
      expect(p.sources.length, p.text).toBeGreaterThan(0);
      for (const s of p.sources) expect(s.retrieved).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it('every coverage gap has at least one source', () => {
    for (const g of data.coverage.gaps) expect(g.sources.length, g.id).toBeGreaterThan(0);
  });

  it('the mold guidance is cited and states its own limits', () => {
    expect(data.safety.mold.sources.length).toBeGreaterThan(0);
    expect(data.safety.mold.text.toLowerCase()).toContain('not a guarantee');
  });

  it('sources currently confirmed only via search index are labelled as such', () => {
    // Honest reporting, not a pass/fail: this is what VERIFY.md §1.1 is for.
    const all = [
      ...data.coverage.waitingPeriod.sources,
      ...data.coverage.gaps.flatMap((g) => g.sources),
      ...data.safety.emergency.points.flatMap((p) => p.sources),
    ];
    const unfetched = all.filter((s) => s.method === 'search_index').length;
    console.log(`      ${unfetched}/${all.length} source references are search_index, not fetched`);
    expect(all.every((s) => Boolean(s.method))).toBe(true);
  });
});

// --- the evidence chain ------------------------------------------------------

describe('the evidence log', () => {
  const at = (n: number) => `2026-04-0${n}T12:00:00Z`;

  it('builds a verifiable chain', async () => {
    let chain: Awaited<ReturnType<typeof appendEntry>>[] = [];
    for (let i = 1; i <= 4; i++) {
      chain = [...chain, await appendEntry(chain, { note: `entry ${i}` }, at(i))];
    }
    expect(chain[0].prevHash).toBe(GENESIS);
    expect(await verifyChain(chain)).toEqual({ intact: true });
  });

  it('detects a body that was altered after the fact', async () => {
    let chain: Awaited<ReturnType<typeof appendEntry>>[] = [];
    for (let i = 1; i <= 3; i++) {
      chain = [...chain, await appendEntry(chain, { note: `entry ${i}` }, at(i))];
    }
    (chain[1].body as { note: string }).note = 'tampered';
    const check = await verifyChain(chain);
    expect(check.intact).toBe(false);
    expect(check.brokenAt).toBe(2);
    expect(check.reason).toBe('content altered');
  });

  it('detects a deleted entry', async () => {
    let chain: Awaited<ReturnType<typeof appendEntry>>[] = [];
    for (let i = 1; i <= 3; i++) {
      chain = [...chain, await appendEntry(chain, { note: `entry ${i}` }, at(i))];
    }
    const without = [chain[0], chain[2]];
    expect((await verifyChain(without)).intact).toBe(false);
  });

  it('a correction adds an entry and leaves the original intact', async () => {
    let chain: Awaited<ReturnType<typeof appendEntry>>[] = [];
    chain = [...chain, await appendEntry(chain, { note: 'water was 2 inches' }, at(1))];
    const originalHash = chain[0].contentHash;
    chain = [...chain, await appendEntry(chain, { note: 'water was 4 inches' }, at(2), 1)];
    expect(chain).toHaveLength(2);
    expect(chain[0].contentHash).toBe(originalHash);
    expect(chain[1].correctsSeq).toBe(1);
    expect((await verifyChain(chain)).intact).toBe(true);
  });

  it('canonical form is stable across key order', () => {
    expect(canonical({ b: 1, a: [2, { d: 4, c: 3 }] })).toBe(canonical({ a: [2, { c: 3, d: 4 }] , b: 1 }));
  });

  it('hashes original bytes, and a single changed byte changes the hash', async () => {
    const a = new Uint8Array([1, 2, 3, 4]);
    const b = new Uint8Array([1, 2, 3, 5]);
    expect(await hashBytes(a)).toHaveLength(64);
    expect(await hashBytes(a)).not.toBe(await hashBytes(b));
  });
});

// --- photo timestamps --------------------------------------------------------

describe('photo timestamps are honest', () => {
  it('a camera timestamp is shown as a capture time, distinct from import', () => {
    const p = makePhotoRecord({
      sha256: 'x'.repeat(64), byteSize: 100, mime: 'image/jpeg',
      exifDateTimeOriginal: '2026-04-02 07:31:00', importedAt: '2026-04-05',
    });
    expect(p.kind).toBe('camera');
    expect(describeTimestamp(p)).toContain('2026-04-02 07:31:00');
    expect(describeTimestamp(p)).toContain('Added to this record 2026-04-05');
  });

  it('a stripped photo says so and never presents import time as capture time', () => {
    // The failure mode this whole module exists for: photos forwarded through messaging apps
    // lose their metadata, and a naive tool shows the import date as if it were the capture date.
    const p = makePhotoRecord({
      sha256: 'y'.repeat(64), byteSize: 100, mime: 'image/jpeg',
      exifDateTimeOriginal: null, importedAt: '2026-04-05',
    });
    expect(p.exifPresent).toBe(false);
    expect(p.kind).toBe('import-only');
    const text = describeTimestamp(p);
    expect(text).toContain('No camera timestamp');
    expect(text).not.toMatch(/\bTaken\b/);
  });
});

// --- honesty about what is proven -------------------------------------------

describe('the methodology statement understates rather than oversells', () => {
  it('says what the chain does not prove', async () => {
    const { METHODOLOGY } = await import('../src/evidence.js');
    expect(METHODOLOGY).toContain('does not show');
    expect(METHODOLOGY).toContain('device clock');
    expect(METHODOLOGY).toContain('not a notarization');
  });

  it('never oversells what the record is', () => {
    // First written as "the word 'blockchain' must not appear", which failed on the sentence
    // "it is not a blockchain" — the test was wrong. What matters is the claim, not the word.
    const overselling = [
      'tamper-proof', 'tamperproof', 'tamper proof', 'legally binding', 'court-admissible',
      'court admissible', 'notarized', 'guarantees', 'proves that the events',
    ];
    for (const f of ['evidence.ts', 'coverage.ts', 'main.ts', 'store.ts']) {
      const src = readFileSync(join(root, 'src', f), 'utf8').toLowerCase();
      for (const phrase of overselling) expect(src, `${f} contains "${phrase}"`).not.toContain(phrase);
    }
  });

  it('mentions blockchain and notarization only to deny them', () => {
    const src = readFileSync(join(root, 'src', 'evidence.ts'), 'utf8').toLowerCase();
    for (const word of ['blockchain', 'notarization']) {
      const idx = src.indexOf(word);
      if (idx === -1) continue;
      expect(src.slice(Math.max(0, idx - 30), idx), word).toMatch(/\bnot\b/);
    }
  });
});

// --- local gating ------------------------------------------------------------

describe('local claims are gated', () => {
  it('ships unconfigured with no resources', () => {
    expect(data.local.configured).toBe(false);
    expect(data.local.resources).toHaveLength(0);
  });

  it('every local resource, if any existed, would carry who verified it and when', () => {
    for (const r of data.local.resources) {
      expect(r.verifiedOn).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(r.verifiedBy.length).toBeGreaterThan(0);
    }
  });
});

// --- no third parties --------------------------------------------------------

describe('nothing leaves the device', () => {
  it('no source file fetches or embeds an external origin', () => {
    for (const f of ['main.ts', 'coverage.ts', 'evidence.ts']) {
      const src = readFileSync(join(root, 'src', f), 'utf8');
      const runtime = src.split('\n')
        .filter((l) => !l.trimStart().startsWith('*') && !l.trimStart().startsWith('//'))
        .join('\n');
      expect(runtime, f).not.toMatch(/\bfetch\s*\(/);
      expect(runtime, f).not.toMatch(/["'`]https?:\/\/(?!localhost)/);
    }
  });

  it('the HTML loads no external stylesheet, font, or script', () => {
    expect(readFileSync(join(root, 'index.html'), 'utf8')).not.toMatch(/(src|href)=["']https?:\/\//);
  });
});

// --- typed entries -----------------------------------------------------------

describe('money is integer cents, never a float', () => {
  it('parses the shapes people actually type', async () => {
    const { parseMoneyToCents } = await import('../src/evidence.js');
    expect(parseMoneyToCents('1234.56')).toBe(123456);
    expect(parseMoneyToCents('$1,234.56')).toBe(123456);
    expect(parseMoneyToCents(' 89 ')).toBe(8900);
    expect(parseMoneyToCents('0.05')).toBe(5);
    expect(parseMoneyToCents('.5')).toBe(50);
    expect(parseMoneyToCents('-12.34')).toBe(-1234);
  });

  it('refuses what it cannot read rather than guessing', async () => {
    const { parseMoneyToCents } = await import('../src/evidence.js');
    for (const bad of ['', 'abc', '12.345', '1.2.3', '$', '12,3.456']) {
      expect(parseMoneyToCents(bad), bad).toBeNull();
    }
  });

  it('survives amounts that would drift as floats', async () => {
    const { parseMoneyToCents, formatCents } = await import('../src/evidence.js');
    // 0.1 + 0.2 territory: summing these as floats gives 1470.0000000000002.
    const parts = ['0.10', '0.20', '1469.70'].map((s) => parseMoneyToCents(s)!);
    expect(parts.reduce((a, b) => a + b, 0)).toBe(147000);
    expect(formatCents(147000)).toBe('$1,470.00');
  });

  it('formats cents back without rounding error', async () => {
    const { formatCents } = await import('../src/evidence.js');
    expect(formatCents(5)).toBe('$0.05');
    expect(formatCents(100)).toBe('$1.00');
    expect(formatCents(123456789)).toBe('$1,234,567.89');
    expect(formatCents(-1234)).toBe('-$12.34');
  });
});

describe('receipts total, damage does not', () => {
  it('sums receipts only', async () => {
    const { appendEntry, receiptsTotalCents, countByKind } = await import('../src/evidence.js');
    let chain: Awaited<ReturnType<typeof appendEntry>>[] = [];
    const at = (n: number) => `2026-04-0${n}T12:00:00Z`;
    chain = [...chain, await appendEntry(chain, { note: 'water in the basement' }, at(1))];
    chain = [...chain, await appendEntry(chain, {
      kind: 'receipt', vendor: 'Hardware store', amountCents: 8999, category: 'drying',
      datedOn: '2026-04-01',
    }, at(2))];
    chain = [...chain, await appendEntry(chain, {
      kind: 'receipt', vendor: 'Motel', amountCents: 21000, category: 'lodging',
      datedOn: '2026-04-02',
    }, at(3))];
    chain = [...chain, await appendEntry(chain, {
      kind: 'damage', room: 'Basement', description: 'Sofa', purchaseCostCents: 90000,
      purchaseYear: 2019, condition: 'ruined',
    }, at(4))];

    // The damage item's $900 must NOT appear in the total — this app does not appraise.
    expect(receiptsTotalCents(chain)).toBe(29999);
    expect(countByKind(chain)).toEqual({ note: 1, damage: 1, call: 0, receipt: 2 });
  });

  it('typed entries ride the same chain and verify like any other', async () => {
    const { appendEntry, verifyChain } = await import('../src/evidence.js');
    let chain: Awaited<ReturnType<typeof appendEntry>>[] = [];
    chain = [...chain, await appendEntry(chain, {
      kind: 'call', party: 'Insurer', person: 'Rita', claimNumber: 'CL-99',
      summary: 'Adjuster booked for Thursday', promised: 'Callback with a time',
    }, '2026-04-05T09:00:00Z')];
    chain = [...chain, await appendEntry(chain, {
      kind: 'receipt', vendor: 'Fan rental', amountCents: 4500, category: 'drying',
      datedOn: '2026-04-05',
    }, '2026-04-05T10:00:00Z')];
    expect(await verifyChain(chain)).toEqual({ intact: true });

    (chain[0].body as { summary: string }).summary = 'never said that';
    const check = await verifyChain(chain);
    expect(check.intact).toBe(false);
    expect(check.brokenAt).toBe(1);
  });
});
