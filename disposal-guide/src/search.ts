import type { Item } from './types.js';

/**
 * Search is the entire user experience here. Owen types "weed whacker", "the swirly lightbulbs",
 * or "flourescent" — an answer database he cannot reach is worth nothing.
 *
 * No dependency: a bundled fuzzy matcher costs ~12KB gzipped and this is ~1KB. The byte budget
 * in the brief is tight and this is the one place it's easy to blow.
 */

export interface SearchHit {
  item: Item;
  score: number;
  /** The alias that matched, for "showing 'sawzall' → Reciprocating saw". */
  matched: string;
}

/** Lowercase, strip accents and punctuation, collapse whitespace. */
export function normalize(s: string): string {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Levenshtein with a cutoff — returns max+1 as soon as it's certainly over budget. */
export function editDistance(a: string, b: string, max: number): number {
  if (a === b) return 0;
  if (Math.abs(a.length - b.length) > max) return max + 1;
  if (a.length === 0) return b.length;
  if (b.length === 0) return a.length;

  let prev = new Array<number>(b.length + 1);
  let curr = new Array<number>(b.length + 1);
  for (let j = 0; j <= b.length; j++) prev[j] = j;

  for (let i = 1; i <= a.length; i++) {
    curr[0] = i;
    let rowMin = curr[0];
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost);
      if (curr[j] < rowMin) rowMin = curr[j];
    }
    if (rowMin > max) return max + 1;
    const t = prev;
    prev = curr;
    curr = t;
  }
  return prev[b.length];
}

/** Tolerance scales with word length: short words get no fuzz, long ones get more. */
function fuzzBudget(len: number): number {
  if (len <= 4) return 0;
  if (len <= 7) return 1;
  return 2;
}

interface IndexedAlias {
  item: Item;
  raw: string;
  norm: string;
  tokens: string[];
}

export class SearchIndex {
  private aliases: IndexedAlias[] = [];

  constructor(items: Item[], languages: string[] = ['en']) {
    for (const item of items) {
      const seen = new Set<string>();
      for (const lang of Object.keys(item.names)) {
        // Index every language we carry, not just the active one — people search in the
        // language the word came to them in, which is often not their UI language.
        if (languages.length && !languages.includes(lang) && lang !== 'en') {
          // still index it; cost is trivial and the recall matters more
        }
        for (const raw of item.names[lang] ?? []) {
          const norm = normalize(raw);
          if (!norm || seen.has(norm)) continue;
          seen.add(norm);
          this.aliases.push({ item, raw, norm, tokens: norm.split(' ') });
        }
      }
    }
  }

  get size(): number {
    return this.aliases.length;
  }

  search(query: string, limit = 8): SearchHit[] {
    const q = normalize(query);
    if (!q) return [];
    const qTokens = q.split(' ');

    const best = new Map<string, SearchHit>();
    const offer = (item: Item, score: number, matched: string) => {
      const prev = best.get(item.slug);
      if (!prev || score > prev.score) best.set(item.slug, { item, score, matched });
    };

    for (const a of this.aliases) {
      let score = 0;

      if (a.norm === q) {
        score = 1000;
      } else if (a.norm.startsWith(q)) {
        score = 800 - (a.norm.length - q.length);
      } else if (a.norm.includes(q)) {
        score = 620 - (a.norm.length - q.length);
      } else if (qTokens.every((t) => a.tokens.some((at) => at.startsWith(t)))) {
        // "weed whack" → "weed whacker"; every query word prefixes some alias word
        score = 560;
      } else if (a.tokens.every((at) => qTokens.some((t) => t.startsWith(at)))) {
        // "old car battery" → alias "car battery"
        score = 520;
      } else {
        // Fuzzy: whole-string, then token-to-token for multi-word aliases.
        const budget = fuzzBudget(Math.max(q.length, a.norm.length));
        if (budget > 0) {
          const d = editDistance(q, a.norm, budget);
          if (d <= budget) {
            score = 400 - d * 40;
          } else {
            let tokenHits = 0;
            for (const t of qTokens) {
              const tb = fuzzBudget(t.length);
              if (tb > 0 && a.tokens.some((at) => editDistance(t, at, tb) <= tb)) tokenHits++;
            }
            if (tokenHits === qTokens.length && qTokens.length > 0) score = 340;
          }
        }
      }

      if (score > 0) offer(a.item, score, a.raw);
    }

    return [...best.values()].sort((x, y) => y.score - x.score || x.item.slug.localeCompare(y.item.slug)).slice(0, limit);
  }
}
