/**
 * The brief's 14 numbered acceptance tests, in order, plus the safety properties.
 *
 * Where a criterion cannot be checked from Node — real-device load time, axe-core, printing on
 * paper — the test is present, skipped, and names what a human has to do instead. A silently
 * missing test reads as a passing one.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import indexData from '../src/generated/index.json';
import type { DataIndex, Item, Location } from '../src/types.js';
import { parse as parseYaml } from 'yaml';
import { freshnessLine, toYaml, type VerifyRecord } from '../src/verify.js';
import { SearchIndex, normalize, editDistance } from '../src/search.js';
import { resolve, clampVerdict, isDisambiguation } from '../src/resolve.js';

const data = indexData as unknown as DataIndex;
const search = new SearchIndex(data.items, data.jurisdiction.languages);
const bySlug = new Map(data.items.map((i) => [i.slug, i]));
const root = join(import.meta.dirname, '..');

function top(query: string): Item | undefined {
  return search.search(query)[0]?.item;
}

// 1 -------------------------------------------------------------------------
describe('1. search finds the same item however people say it', () => {
  const variants = ['double A batteries', 'AA battery', 'aa batteries', 'batterys'];
  for (const v of variants) {
    it(`"${v}" reaches a battery item`, () => {
      const hit = top(v);
      expect(hit, `no hit for "${v}"`).toBeDefined();
      expect(hit!.slug).toMatch(/^battery-/);
    });
  }

  it('"batterys" (misspelled) reaches the battery disambiguation', () => {
    expect(top('batterys')?.slug).toBe('battery-generic');
  });

  it('Spanish "pilas" disambiguates, because it is the generic word', () => {
    // Written first as `toBe('battery-alkaline')` and it failed. The test was wrong, not the
    // code: "pilas" is Spanish for batteries generally, exactly like "battery" in English, so
    // resolving it straight to alkaline would be the same merge this project exists to avoid.
    expect(top('pilas')?.slug).toBe('battery-generic');
  });

  it('Spanish "pilas alcalinas" reaches the alkaline item', () => {
    expect(top('pilas alcalinas')?.slug).toBe('battery-alkaline');
  });

  it('Spanish "bateria de litio" reaches lithium-ion', () => {
    expect(top('bateria de litio')?.slug).toBe('battery-lithium-ion');
  });

  it('"flourescent" (transposed) finds the fluorescent item', () => {
    // The exact misspelling named in the brief. Levenshtein distance 2 on an 11-char word.
    expect(top('flourescent')?.slug).toBe('fluorescent-tube');
  });

  it('colloquialisms work', () => {
    expect(top('weed killer')?.slug).toBe('pesticides');
    expect(top('roundup')?.slug).toBe('pesticides');
    expect(top('swirly light bulb')?.slug).toBe('fluorescent-tube');
    expect(top('vape')?.slug).toBe('battery-lithium-ion');
    expect(top('bbq tank')?.slug).toBe('propane-cylinder');
  });
});

// 2 -------------------------------------------------------------------------
describe('2. "battery" disambiguates instead of answering', () => {
  it('resolves to the disambiguation item, not a verdict', () => {
    const hit = top('battery');
    expect(hit?.slug).toBe('battery-generic');
    expect(isDisambiguation(hit!)).toBe(true);
  });

  it('covers alkaline, lithium-ion, button cell, and lead-acid', () => {
    const kinds = bySlug.get('battery-generic')!.disambiguates!;
    expect(kinds).toEqual(
      expect.arrayContaining([
        'battery-alkaline',
        'battery-lithium-ion',
        'battery-button-cell',
        'battery-lead-acid',
      ]),
    );
  });

  it('every disambiguation target exists and is itself answerable', () => {
    for (const item of data.items.filter(isDisambiguation)) {
      for (const slug of item.disambiguates!) {
        const child = bySlug.get(slug);
        expect(child, `${item.slug} -> ${slug}`).toBeDefined();
        expect(isDisambiguation(child!)).toBe(false);
      }
    }
  });
});

// 3 -------------------------------------------------------------------------
describe("3. every item's destinations resolve to real locations", () => {
  it('no local rule points at a missing or non-accepting location', () => {
    const locs = new Map(data.locations.map((l) => [l.id, l]));
    for (const item of data.items) {
      for (const [jid, rule] of Object.entries(item.local ?? {})) {
        for (const dest of rule.destinations) {
          const loc = locs.get(dest);
          expect(loc, `${item.slug}/${jid} -> ${dest}`).toBeDefined();
          expect(loc!.acceptsSlugs).toContain(item.slug);
        }
      }
    }
  });
});

// 4 -------------------------------------------------------------------------
describe('4. every shipped location names who verified it', () => {
  it('non-demo locations have verifiedOn and verifiedBy', () => {
    for (const loc of data.locations.filter((l) => !l.isDemo)) {
      expect(loc.verifiedOn, `${loc.id} verifiedOn`).toBeTruthy();
      expect(loc.verifiedBy, `${loc.id} verifiedBy`).toBeTruthy();
    }
  });

  it('demo locations are flagged so they can never render as real', () => {
    const demo = data.locations.filter((l) => l.name.includes('NOT A REAL PLACE'));
    expect(demo.length).toBeGreaterThan(0);
    for (const l of demo) expect(l.isDemo).toBe(true);
  });

  it('a demo location is never offered as a destination', () => {
    for (const item of data.items) {
      const a = resolve(data, item);
      for (const d of a.destinations) expect(d.isDemo).not.toBe(true);
    }
  });
});

// 5 -------------------------------------------------------------------------
describe('5. staleness is visible', () => {
  it('a location with no hours never claims to be open', () => {
    // hoursLine() is the only place that renders openness, and with no hours record it
    // returns the call-first string. Asserted here against the data contract.
    for (const loc of data.locations) {
      if (!loc.hours && !loc.hoursNote) {
        expect(loc.phone, `${loc.id} has no hours, so it must at least have a phone`).toBeTruthy();
      }
    }
  });

  it('a location unverified for 180+ days says so and says to call first', () => {
    // Skipped until R12 as "needs real verified locations to exercise", which was wrong: it needs
    // a location with an old DATE, and one can be written here. The skip cost something real —
    // `isStale` shipped in R8 and was wired only into the maintainer's re-check screen, so the
    // answer screen a member of the public sees rendered "Confirmed 2023-04-01 by Dana" at any
    // age with no flag at all. Brief acceptance test 5 was unbuilt on the only path that matters.
    const today = new Date('2026-08-18T00:00:00Z');
    const at = (iso: string): Location =>
      ({ ...data.locations[0]!, verifiedOn: iso, verifiedBy: 'Dana', phone: '555-0101' });

    expect(freshnessLine(at('2026-08-11'), today).stale).toBe(false);
    // The boundary itself, from both sides.
    expect(freshnessLine(at('2026-02-20'), today).stale).toBe(false);  // 179 days
    expect(freshnessLine(at('2026-02-19'), today).stale).toBe(true);   // 180 days
    expect(freshnessLine(at('2023-04-01'), today).stale).toBe(true);

    const old = freshnessLine(at('2023-04-01'), today);
    expect(old.text).toMatch(/call before you go/i);
    expect(old.text).toMatch(/out of date/i);
    // Elapsed time, not just a date the reader has to do arithmetic on.
    expect(old.text).toMatch(/years ago/);

    const never = freshnessLine({ ...data.locations[0]!, verifiedOn: undefined }, today);
    expect(never.stale).toBe(true);
    expect(never.text).toMatch(/call before you go/i);
  });

  it('the answer screen actually uses it — not just the maintainer screen', () => {
    // A source-level check, and deliberately so. The bug it guards was not wrong logic: it was
    // correct logic wired to one screen and not the other, for four rounds. `isStale` was used
    // in the /verify view and nowhere a member of the public could see it. No behavioural test
    // can catch that while destinations do not render at all (jurisdiction.configured is false
    // until M0), so this asserts the wiring directly and says plainly that is what it is.
    const main = readFileSync(join(root, 'src', 'main.ts'), 'utf8');
    const renderPlace = main.slice(main.indexOf('function renderPlace'));
    const body = renderPlace.slice(0, renderPlace.indexOf('\nfunction '));
    expect(body).toContain('freshnessLine');
    expect(body).toContain('place-callfirst');
    // And the phone number goes in the flag, which is what the brief asks for.
    expect(body).toMatch(/place-callfirst[\s\S]*tel:/);
  });

  it('a fresh location does not nag, and still shows its date', () => {
    // The flag is worth nothing if it is on everything.
    const today = new Date('2026-08-18T00:00:00Z');
    const fresh = freshnessLine(
      { ...data.locations[0]!, verifiedOn: '2026-08-01', verifiedBy: 'Dana' }, today,
    );
    expect(fresh.stale).toBe(false);
    expect(fresh.text).not.toMatch(/call before you go/i);
    expect(fresh.text).toContain('2026-08-01');
    expect(fresh.text).toContain('Dana');
  });
});

// 6 -------------------------------------------------------------------------
describe('6. hazardous items carry prep steps', () => {
  it('every hazardous or never-curbside item explains what to do before you go', () => {
    let checked = 0;
    for (const item of data.items) {
      const u = item.universal;
      if (!u) continue;
      if (u.hazard === 'hazardous' || u.hazard === 'professional' || u.neverCurbside) {
        checked++;
        expect(u.prep.length, `${item.slug} has no prep steps`).toBeGreaterThan(0);
        expect(u.why.en.length, `${item.slug} has no why`).toBeGreaterThan(10);
      }
    }
    // Without this the test is green when the loop matches nothing — a data file that lost its
    // hazardous items, or a renamed hazard value, would read as "all items explain themselves".
    expect(checked, 'no hazardous items were checked, so this test proved nothing').toBeGreaterThan(10);
  });

  it('batteries specifically tell you to tape the terminals', () => {
    const prep = bySlug.get('battery-lithium-ion')!.universal!.prep.map((p) => p.en).join(' ');
    expect(prep.toLowerCase()).toContain('tape');
  });
});

// 7 -------------------------------------------------------------------------
describe('7. no hazardous item can be sent to a bin', () => {
  it('no shipped local rule puts a hazardous item in a cart', () => {
    for (const item of data.items) {
      for (const [jid, rule] of Object.entries(item.local ?? {})) {
        const u = item.universal;
        if (u?.neverCurbside || u?.hazard === 'hazardous' || u?.hazard === 'professional') {
          expect(
            ['recycling_cart', 'trash_cart', 'yard_waste'],
            `${item.slug}/${jid}`,
          ).not.toContain(rule.verdict);
        }
      }
    }
  });

  it('the runtime guard clamps a dangerous verdict even if the data were tampered with', () => {
    const liion = bySlug.get('battery-lithium-ion')!;
    expect(clampVerdict(liion, 'trash_cart')).toBe('hazardous_waste');
    expect(clampVerdict(liion, 'recycling_cart')).toBe('hazardous_waste');
    const asbestos = bySlug.get('asbestos-suspect')!;
    expect(clampVerdict(asbestos, 'trash_cart')).toBe('professional_only');
  });

  it('an unconfigured jurisdiction never yields a bin answer for anything', () => {
    expect(data.jurisdiction.configured).toBe(false);
    for (const item of data.items) {
      if (isDisambiguation(item)) continue;
      const a = resolve(data, item);
      expect(['recycling_cart', 'trash_cart', 'yard_waste'], item.slug).not.toContain(a.verdict);
    }
  });

  it('an unknown item is never answered "trash"', () => {
    for (const item of data.items) {
      if (item.universal) continue;
      const a = resolve(data, item);
      expect(a.verdict, item.slug).toBe('unknown');
    }
  });
});

// 8 -------------------------------------------------------------------------
describe('8. search works offline', () => {
  it('the whole index is bundled, not fetched at runtime', () => {
    const main = readFileSync(join(root, 'src', 'main.ts'), 'utf8');
    expect(main).toContain("import indexData from './generated/index.json'");
    expect(main).not.toMatch(/\bfetch\s*\(/);
  });

  it('searching needs no I/O', () => {
    // Constructed from the bundled object; if this ever needed the network the import above
    // would not be enough.
    expect(search.size).toBeGreaterThan(100);
    expect(top('propane')).toBeDefined();
  });
});

// 9 -------------------------------------------------------------------------
describe('9. zero-result logging records the query and nothing else', () => {
  it('the stored record has exactly q, lang, and day', async () => {
    const store = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
    });
    const { logZeroResult, readZeroResults } = await import('../src/telemetry.js');
    logZeroResult('sporkulator 9000', 'en');
    const rows = readZeroResults();
    expect(rows).toHaveLength(1);
    expect(Object.keys(rows[0]).sort()).toEqual(['day', 'lang', 'q']);
    expect(rows[0].day).toMatch(/^\d{4}-\d{2}-\d{2}$/); // day only, never a timestamp
  });

  it('de-duplicates within a day so typing does not log every prefix', async () => {
    const store = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
    });
    vi.resetModules();
    const { logZeroResult, readZeroResults } = await import('../src/telemetry.js');
    logZeroResult('zzz', 'en');
    logZeroResult('zzz', 'en');
    expect(readZeroResults()).toHaveLength(1);
  });

  it('no upload endpoint is configured by default', async () => {
    const { UPLOAD_ENDPOINT } = await import('../src/telemetry.js');
    expect(UPLOAD_ENDPOINT).toBeNull();
  });
});

// 10 ------------------------------------------------------------------------
describe('10. answer speed', () => {
  it('search over the full index stays well under a frame', () => {
    const queries = ['battery', 'paint', 'flourescent', 'weed killer', 'aceite', 'propane'];
    const start = performance.now();
    for (let i = 0; i < 200; i++) for (const q of queries) search.search(q);
    const perSearch = (performance.now() - start) / (200 * queries.length);
    expect(perSearch).toBeLessThan(5); // ms
  });

  it.skip('under 2s on Slow 4G with 4x CPU throttle — measure on a real device', () => {
    // scripts/check-budget.ts asserts the byte budget, which is the part a machine can check.
    // The device measurement is in VERIFY.md.
  });
});

// 11 ------------------------------------------------------------------------
describe('11. language coverage', () => {
  it('every item has an English name', () => {
    for (const item of data.items) expect(item.names.en?.length, item.slug).toBeGreaterThan(0);
  });

  it('reports Spanish coverage honestly rather than asserting completeness', () => {
    const total = data.items.length;
    const withEs = data.items.filter((i) => (i.names.es?.length ?? 0) > 0).length;
    const withEsWhy = data.items.filter((i) => i.universal?.why?.es).length;
    const withUniversal = data.items.filter((i) => i.universal).length;
    // Recorded, not enforced: full Spanish coverage needs a human translator, per VERIFY.md.
    console.log(
      `      Spanish coverage: names ${withEs}/${total}, why ${withEsWhy}/${withUniversal}`,
    );
    expect(withEs).toBeGreaterThan(total * 0.5);
  });
});

// 12 ------------------------------------------------------------------------
describe('12. accessibility', () => {
  it('no meaning is carried by colour alone: hazard is always a word too', () => {
    const main = readFileSync(join(root, 'src', 'main.ts'), 'utf8');
    expect(main).toContain('HAZARD_WORD');
    expect(main).toContain('hazard-tag');
  });

  it('touch targets and focus styles are defined', () => {
    const css = readFileSync(join(root, 'src', 'styles.css'), 'utf8');
    expect(css).toContain('min-height: 44px');
    expect(css).toContain(':focus-visible');
    expect(css).toContain('.skip');
  });

  it('axe-core, keyboard-only, and 200% zoom are covered by the browser suite', () => {
    // Not skipped: test/browser.spec.ts runs axe-core (wcag2a/2aa/21a/21aa/22aa) against all
    // five screens in real Chromium, drives the search-to-answer path with the keyboard only,
    // and asserts no horizontal overflow at 200% on a 360px viewport. Run `npx playwright test`.
    const spec = readFileSync(join(root, 'test', 'browser.spec.ts'), 'utf8');
    expect(spec).toContain('AxeBuilder');
    expect(spec).toContain('wcag22aa');
    expect(spec).toContain('keyboard alone');
    expect(spec).toContain('200% zoom');
  });
});

// 13 ------------------------------------------------------------------------
describe('13. printing', () => {
  it('a print stylesheet exists and hides the chrome', () => {
    const css = readFileSync(join(root, 'src', 'styles.css'), 'utf8');
    expect(css).toContain('@media print');
    expect(css).toContain('.no-print');
  });

  it.skip('the fridge sheet fits one page on paper — print it and look', () => {
    // See VERIFY.md.
  });
});

// 14 ------------------------------------------------------------------------
describe('14. no third-party requests', () => {
  it('no source file references an external origin at runtime', () => {
    for (const f of ['main.ts', 'search.ts', 'resolve.ts', 'telemetry.ts']) {
      const src = readFileSync(join(root, 'src', f), 'utf8');
      const runtime = src
        .split('\n')
        .filter((l) => !l.trimStart().startsWith('*') && !l.trimStart().startsWith('//'))
        .join('\n');
      expect(runtime, `${f} must not fetch`).not.toMatch(/\bfetch\s*\(/);
      expect(runtime, `${f} must not embed an external URL`).not.toMatch(
        /["'`]https?:\/\/(?!localhost)/,
      );
    }
  });

  it('the HTML loads no external stylesheet, font, or script', () => {
    const html = readFileSync(join(root, 'index.html'), 'utf8');
    expect(html).not.toMatch(/(src|href)=["']https?:\/\//);
  });

  it('the service worker refuses to handle cross-origin requests', () => {
    const sw = readFileSync(join(root, 'public', 'sw.js'), 'utf8');
    expect(sw).toContain('url.origin !== self.location.origin');
  });
});

// helpers -------------------------------------------------------------------
describe('search primitives', () => {
  it('normalize strips case, accents, and punctuation', () => {
    expect(normalize('  Aceité,  USADO! ')).toBe('aceite usado');
  });

  it('editDistance bails out past the budget', () => {
    expect(editDistance('kitten', 'sitting', 3)).toBe(3);
    expect(editDistance('abc', 'xyzxyz', 1)).toBe(2); // over budget -> max+1
    expect(editDistance('flourescent', 'fluorescent', 2)).toBe(2);
  });
});

describe('ambiguity that bit us during the build', () => {
  it('"aceite usado" surfaces both motor oil and cooking oil, not one of them', () => {
    // Spanish for "used oil" means both, and they have opposite answers. The build-time alias
    // collision check caught this; this test keeps it caught.
    const slugs = search.search('aceite usado', 8).map((h) => h.item.slug);
    expect(slugs).toContain('motor-oil');
    expect(slugs).toContain('cooking-oil');
  });
});

// --- what /verify emits is pasted into a safety data file ---------------------

/**
 * `toYaml` output is pasted by a human into `data/locations/local.yaml` — the file that decides
 * where somebody drives with a car full of hazardous waste. Its contract is that what the
 * maintainer typed is what lands in the file, and nothing was enforcing it: a value with a
 * newline escaped its comment and wrote live YAML keys.
 *
 * Parsed with the same YAML library the build uses, rather than matched as strings. A string
 * assertion here would only be checking that the emitter agrees with itself.
 */
describe('the pasteable YAML cannot become something the maintainer did not type', () => {
  const locId = data.locations[0]!.id;
  const rec = (over: Partial<VerifyRecord> = {}): VerifyRecord => ({
    locationId: locId, outcome: 'confirmed', on: '2026-08-18', by: 'Dana', ...over,
  });

  it('a note containing newlines stays entirely inside its comment', () => {
    const y = toYaml([rec({ note: 'ok\n  hazard: none\n  neverCurbside: false' })], data);
    for (const line of y.split('\n')) {
      if (/hazard|neverCurbside/.test(line)) {
        expect(line.trimStart().startsWith('#'), `escaped its comment: ${line}`).toBe(true);
      }
    }
    const parsed = parseYaml(y) as Record<string, unknown>[];
    expect(parsed).toHaveLength(1);
    expect(Object.keys(parsed[0]!).sort()).toEqual(['id', 'verifiedBy', 'verifiedOn']);
  });

  it('a verifier name containing newlines stays one scalar', () => {
    const y = toYaml([rec({ by: 'Dana\n- id: fake-site\n  active: true' })], data);
    const parsed = parseYaml(y) as Record<string, unknown>[];
    // One entry, not two. The injected id must not have become a location.
    expect(parsed).toHaveLength(1);
    expect(parsed[0]!.id).toBe(locId);
    expect(parsed[0]!.verifiedBy).toBe('Dana\n- id: fake-site\n  active: true');
  });

  it('quotes, colons and YAML sigils in a name survive as text', () => {
    for (const name of ["Dana O'Brien", 'Dana: the clerk', '&anchor *ref', '{a: 1}', '- item', '*']) {
      const parsed = parseYaml(toYaml([rec({ by: name })], data)) as Record<string, unknown>[];
      expect(parsed[0]!.verifiedBy, name).toBe(name);
    }
  });

  it('a no-answer still emits nothing that could be committed as a verification', () => {
    const y = toYaml([rec({ outcome: 'no_answer', by: 'Dana\n- id: fake\n  active: true' })], data);
    expect(parseYaml(y) ?? []).toEqual([]);   // comments only
  });
});
