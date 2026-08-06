/**
 * Text normalization for matching.
 *
 * Its own module with its own tests, because every false positive and every miss in this project
 * traces back to here. A brand written "Ben's Best, Inc." on a recall notice and "bens best" by a
 * subscriber has to compare equal; "Ben's Best" and "Ben's Better" must not.
 */

/** Corporate suffixes carry no matching signal and appear inconsistently on recall notices. */
const SUFFIXES = [
  'inc', 'incorporated', 'llc', 'l l c', 'ltd', 'limited', 'corp', 'corporation', 'co',
  'company', 'holdings', 'group', 'brands', 'foods', 'food', 'usa', 'us', 'international',
  'intl', 'gmbh', 'sa', 'nv', 'plc', 'lp', 'llp',
];

/** Unit spellings vary between a package label and an enforcement report. */
const UNITS: [RegExp, string][] = [
  [/\bounces?\b/g, 'oz'],
  [/\bfluid ounces?\b/g, 'floz'],
  [/\bfl oz\b/g, 'floz'],
  [/\bpounds?\b/g, 'lb'],
  [/\blbs\b/g, 'lb'],
  [/\bgrams?\b/g, 'g'],
  [/\bkilograms?\b/g, 'kg'],
  [/\bmilliliters?\b/g, 'ml'],
  [/\bliters?\b/g, 'l'],
  [/\bcounts?\b/g, 'ct'],
  [/\bpacks?\b/g, 'pk'],
  [/\bpieces?\b/g, 'pc'],
];

/** Lowercase, strip accents and punctuation, collapse whitespace. */
export function basic(s: string): string {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/&/g, ' and ')
    // Apostrophes are DELETED, not turned into spaces, so "Ben's Best" becomes "bens best"
    // rather than "ben s best". A subscriber who types "bens best" has to reach the same
    // string. Found by the labelled-pair evaluation, which scored it as a missed alert.
    .replace(/['‘’ʼ]/g, '')
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Full normalization for brand and product comparison. */
export function normalize(s: string): string {
  let out = basic(s);
  for (const [re, to] of UNITS) out = out.replace(re, to);
  // Numbers glued to units: "12oz" -> "12 oz"
  out = out.replace(/(\d)([a-z])/g, '$1 $2').replace(/([a-z])(\d)/g, '$1 $2');
  return out.replace(/\s+/g, ' ').trim();
}

/** Brand comparison additionally drops corporate suffixes and possessives. */
export function normalizeBrand(s: string): string {
  const words = normalize(s).split(' ').filter(Boolean);
  while (words.length > 1 && SUFFIXES.includes(words[words.length - 1]!)) words.pop();
  return words.join(' ');
}

/**
 * UPCs appear as 12-digit UPC-A, 13-digit EAN, and 8-digit UPC-E, with and without dashes, and
 * sometimes with a leading zero dropped by a spreadsheet. Compare on the 13-digit form so all
 * three land in the same place.
 */
export function normalizeUpc(raw: string): string | null {
  const digits = raw.replace(/\D/g, '');
  if (digits.length < 8 || digits.length > 14) return null;
  return digits.padStart(13, '0').slice(-13);
}

export function tokens(s: string): string[] {
  return normalize(s).split(' ').filter(Boolean);
}

const UNIT_TOKENS = new Set(['oz', 'floz', 'lb', 'g', 'kg', 'ml', 'l', 'ct', 'pk', 'pc']);

/**
 * Tokens that carry product identity: no bare numbers, no units.
 *
 * A recall notice says "Frozen Cut Green Beans 12 oz"; a subscriber types "frozen cut green
 * beans". Comparing the raw token sets punishes the notice for being specific about packaging,
 * which is exactly backwards.
 */
export function contentTokens(s: string): string[] {
  return tokens(s).filter((t) => !UNIT_TOKENS.has(t) && !/^\d+$/.test(t));
}

/**
 * Containment, not Jaccard.
 *
 * Returns how much of the SHORTER description is covered by the longer one, plus the size of the
 * overlap. Jaccard scored "salsa verde" against "Salsa Verde 16 fluid ounces" at 0.5 and dropped
 * a real alert to a candidate; containment scores it 1.0. The overlap count is returned so the
 * caller can refuse to call a single shared word a strong match.
 */
export function productScore(a: string, b: string): { score: number; shared: number } {
  const A = new Set(contentTokens(a));
  const B = new Set(contentTokens(b));
  if (!A.size || !B.size) return { score: 0, shared: 0 };
  let shared = 0;
  for (const t of A) if (B.has(t)) shared++;
  return { score: shared / Math.min(A.size, B.size), shared };
}

/** Jaccard overlap on token sets. Cheap, order-insensitive, and good enough for product names. */
export function tokenOverlap(a: string, b: string): number {
  const A = new Set(tokens(a));
  const B = new Set(tokens(b));
  if (!A.size || !B.size) return 0;
  let shared = 0;
  for (const t of A) if (B.has(t)) shared++;
  return shared / (A.size + B.size - shared);
}

/**
 * Lot codes on a notice are free text: "Lot 4271, 4272", "best by 05/12/2026", "EST. 21247".
 * Extract comparable tokens rather than trying to parse a grammar that does not exist.
 */
export function lotTokens(codeInfo: string): string[] {
  return (codeInfo.match(/[A-Z0-9][A-Z0-9/-]{2,}/gi) ?? [])
    .map((t) => t.replace(/[^A-Z0-9]/gi, '').toUpperCase())
    .filter((t) => t.length >= 3);
}

/** True when the subscriber's recorded lot appears among the notice's codes. */
export function lotMatches(recallCodeInfo: string, subscriberLot: string | null): boolean {
  if (!subscriberLot) return false;
  const want = subscriberLot.replace(/[^A-Z0-9]/gi, '').toUpperCase();
  if (want.length < 3) return false;
  return lotTokens(recallCodeInfo).some((t) => t === want || t.includes(want) || want.includes(t));
}
