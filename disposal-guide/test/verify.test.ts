import { describe, it, expect } from 'vitest';
import indexData from '../src/generated/index.json';
import type { DataIndex, Location } from '../src/types.js';
import { parse } from 'yaml';
import { queue, questions, isStale, daysSince, toYaml, STALE_AFTER_DAYS } from '../src/verify.js';

const data = indexData as unknown as DataIndex;
const TODAY = new Date('2026-08-06T00:00:00Z');

function loc(over: Partial<Location>): Location {
  return { id: 'x', name: 'X', address: 'A', acceptsSlugs: [], ...over };
}

describe('staleness', () => {
  it('counts whole days', () => {
    expect(daysSince('2026-08-06', TODAY)).toBe(0);
    expect(daysSince('2026-08-05', TODAY)).toBe(1);
    expect(daysSince(undefined, TODAY)).toBeNull();
    expect(daysSince('not-a-date', TODAY)).toBeNull();
  });

  it('is due at the threshold, not after it', () => {
    const at = new Date(Date.UTC(2026, 7, 6) - STALE_AFTER_DAYS * 86_400_000)
      .toISOString().slice(0, 10);
    expect(isStale(loc({ verifiedOn: at }), TODAY)).toBe(true);
    const dayBefore = new Date(Date.UTC(2026, 7, 6) - (STALE_AFTER_DAYS - 1) * 86_400_000)
      .toISOString().slice(0, 10);
    expect(isStale(loc({ verifiedOn: dayBefore }), TODAY)).toBe(false);
  });

  it('never-verified counts as stale, not as fresh', () => {
    expect(isStale(loc({}), TODAY)).toBe(true);
  });
});

describe('the queue', () => {
  const rows = [
    loc({ id: 'fresh', verifiedOn: '2026-08-01' }),
    loc({ id: 'old', verifiedOn: '2025-01-01' }),
    loc({ id: 'never' }),
    loc({ id: 'demo', isDemo: true }),
  ];
  const idx = { ...data, locations: rows } as DataIndex;

  it('puts never-verified first, then oldest, with demo rows last', () => {
    expect(queue(idx, TODAY).map((l) => l.id)).toEqual(['never', 'old', 'fresh', 'demo']);
  });

  it('shows demo rows rather than hiding them', () => {
    // An empty list would read as "nothing to do" when the directory is still fictional.
    expect(queue(idx, TODAY).some((l) => l.isDemo)).toBe(true);
  });

  it('drops what has already been done this session', () => {
    expect(queue(idx, TODAY, new Set(['never', 'old'])).map((l) => l.id)).toEqual(['fresh', 'demo']);
  });
});

describe('the questions', () => {
  it('name the actual items that location accepts', () => {
    const target = data.locations.find((l) => l.acceptsSlugs.length > 0)!;
    const qs = questions(target, data);
    expect(qs[0]).toMatch(/still taking these from households/i);
    expect(qs[0].length).toBeGreaterThan(50);
    expect(qs.some((q) => /hours/i.test(q))).toBe(true);
    expect(qs.some((q) => /charge/i.test(q))).toBe(true);
    expect(qs.some((q) => /don't take/i.test(q))).toBe(true);
  });

  it('does not break on a location that accepts nothing', () => {
    expect(questions(loc({}), data)[0]).toContain('(nothing recorded)');
  });
});

describe('the YAML fragment', () => {
  it('fills in the date and who for a confirmation', () => {
    const y = toYaml([{ locationId: 'demo-hhw', outcome: 'confirmed', on: '2026-08-06', by: 'Dana' }], data);
    expect(y).toContain('- id: demo-hhw');
    expect(y).toContain("verifiedOn: '2026-08-06'");
    expect(y).toContain("verifiedBy: 'Dana'");
  });

  it('does NOT update the date on a no-answer', () => {
    // A location nobody can reach is a finding, not a confirmation. This is the assertion that
    // stops the re-check loop from laundering unanswered calls into fresh-looking data.
    const y = toYaml([{ locationId: 'demo-hhw', outcome: 'no_answer', on: '2026-08-06', by: 'Dana' }], data);
    expect(y).not.toMatch(/^\s*verifiedOn:/m);
    expect(y).toContain('NOT verified');
  });

  it('comments out a closure rather than deleting anything', () => {
    const y = toYaml([{ locationId: 'demo-hhw', outcome: 'closed', on: '2026-08-06', by: 'Dana' }], data);
    expect(y).toContain('# - id: demo-hhw');
    expect(y).toContain('CLOSED');
    expect(y).not.toMatch(/^- id:/m);
  });

  it('flags a change for the maintainer to transcribe', () => {
    const y = toYaml(
      [{ locationId: 'demo-hhw', outcome: 'changed', on: '2026-08-06', by: 'Dana', note: 'Closed Saturdays now' }],
      data,
    );
    expect(y).toContain('SOMETHING CHANGED');
    expect(y).toContain('Closed Saturdays now');
    expect(y).toContain("verifiedOn: '2026-08-06'");
  });

  it('escapes a quote in a name so the fragment stays valid YAML', () => {
    const y = toYaml([{ locationId: 'demo-hhw', outcome: 'confirmed', on: '2026-08-06', by: "O'Brien" }], data);
    expect(y).toContain("verifiedBy: 'O''Brien'");
  });

  it('says so when nothing has been checked', () => {
    expect(toYaml([], data)).toContain('Nothing verified yet');
  });

  it('parses as valid YAML — the fragment is meant to be pasted into a data file', () => {
    // Emitting something that looks like YAML and is not would break the build for whoever
    // pastes it, which is exactly the person doing the unglamorous work.
    const y = toYaml(
      [
        { locationId: 'demo-hhw', outcome: 'confirmed', on: '2026-08-06', by: "O'Brien" },
        { locationId: 'demo-hardware', outcome: 'changed', on: '2026-08-06', by: 'Dana', note: 'Now $5: closed Sat' },
        { locationId: 'demo-pharmacy', outcome: 'closed', on: '2026-08-06', by: 'Dana' },
        { locationId: 'demo-transfer-station', outcome: 'no_answer', on: '2026-08-06', by: 'Dana' },
      ],
      data,
    );
    const parsed = parse(y) as { id: string; verifiedOn: string; verifiedBy: string }[];
    expect(Array.isArray(parsed)).toBe(true);
    // Only the two that were actually reached produce rows; closed and no-answer stay commented.
    expect(parsed.map((r) => r.id)).toEqual(['demo-hhw', 'demo-hardware']);
    expect(parsed[0].verifiedBy).toBe("O'Brien");
    expect(parsed[0].verifiedOn).toBe('2026-08-06');
  });
});
