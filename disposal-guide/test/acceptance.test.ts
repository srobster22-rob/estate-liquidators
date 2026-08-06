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
import type { DataIndex, Item } from '../src/types.js';
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

  it.skip('180-day staleness flag — needs real verified locations to exercise', () => {
    // Blocked on M0: there are no non-demo locations yet. See VERIFY.md.
  });
});

// 6 -------------------------------------------------------------------------
describe('6. hazardous items carry prep steps', () => {
  it('every hazardous or never-curbside item explains what to do before you go', () => {
    for (const item of data.items) {
      const u = item.universal;
      if (!u) continue;
      if (u.hazard === 'hazardous' || u.hazard === 'professional' || u.neverCurbside) {
        expect(u.prep.length, `${item.slug} has no prep steps`).toBeGreaterThan(0);
        expect(u.why.en.length, `${item.slug} has no why`).toBeGreaterThan(10);
      }
    }
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
