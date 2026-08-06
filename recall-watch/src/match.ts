import { lotMatches, normalizeBrand, normalizeUpc, productScore, tokens } from './normalize.js';
import type { Confidence, MatchResult, Recall, WatchItem } from './types.js';

/**
 * The matcher.
 *
 * Three outcomes and only three:
 *
 *   exact     — a UPC in the notice matches a watched UPC. Alert without human review.
 *   strong    — brand and product both match, and the lot codes either agree or the notice
 *               specifies none. Alert without human review.
 *   candidate — brand alone, a fuzzy product, or a category watch. NEVER alerted directly;
 *               goes to a human.
 *   (null)    — no match, which is the common case and the correct one most of the time.
 *
 * The design bias is toward precision, deliberately. Under-alerting misses a recall; over-alerting
 * trains someone to ignore the channel, which misses every future recall. An ignored channel
 * protects nobody, so ambiguity resolves to `candidate` and a person decides.
 *
 * Do not "improve" this by promoting candidates automatically. If the review queue is too slow,
 * make review faster — do not lower the bar.
 */

const PRODUCT_STRONG = 0.8; // containment required to call a product name a match
const PRODUCT_WEAK = 0.34; // below this, the products are simply different things
const MIN_SHARED = 2; // one shared word is a coincidence, not a product match

function brandsMatch(recall: Recall, watch: WatchItem): string | null {
  if (!watch.brand) return null;
  const want = normalizeBrand(watch.brand);
  if (!want) return null;
  for (const b of recall.brands) {
    const got = normalizeBrand(b);
    if (!got) continue;
    if (got === want) return b;
    // A recall brand of "Ben's Best Foods" should match a watched brand of "Ben's Best", but
    // "Ben" must not match "Ben's Best" — require a whole-token prefix, not a substring.
    const gotT = got.split(' ');
    const wantT = want.split(' ');
    // A whole-token prefix match is safe when the shorter side is either multi-word
    // ("Green Valley" -> "Green Valley Farms") or a single distinctive word
    // ("Harborline" -> "Harborline Beverages Co."). It is NOT safe for a short single token:
    // "Green" must never match "Green Valley Farms". Threshold found by the labelled pairs.
    const distinctive = (t: string[]) => t.length >= 2 || (t[0]?.length ?? 0) >= 6;
    if (distinctive(wantT) && gotT.slice(0, wantT.length).join(' ') === want) return b;
    if (distinctive(gotT) && wantT.slice(0, gotT.length).join(' ') === got) return b;
  }
  return null;
}

function bestProductOverlap(
  recall: Recall, product: string,
): { score: number; shared: number; against: string } {
  let best = { score: 0, shared: 0, against: '' };
  for (const p of [...recall.products, recall.title]) {
    const { score, shared } = productScore(p, product);
    if (score > best.score) best = { score, shared, against: p };
  }
  return best;
}

export function match(recall: Recall, watch: WatchItem): MatchResult | null {
  // --- UPC: the strongest key a household can give us -------------------------------------
  if (watch.upc) {
    const want = normalizeUpc(watch.upc);
    if (want) {
      for (const u of recall.upcs) {
        if (normalizeUpc(u) === want) {
          return {
            confidence: 'exact',
            reason: { rule: 'upc', fields: ['upc'], detail: `UPC ${u} listed in the notice` },
          };
        }
      }
      // A watched UPC that does not appear in a notice that lists UPCs is a real negative.
      // Fall through only if the notice lists none, in which case brand/product may still match.
      if (recall.upcs.length > 0 && !watch.brand && !watch.product) return null;
    }
  }

  // --- VIN: exact only, no fuzz -----------------------------------------------------------
  if (watch.kind === 'vin' && watch.vin) {
    const want = watch.vin.trim().toUpperCase();
    const found = recall.raw && typeof recall.raw === 'object' && 'vins' in recall.raw
      ? (recall.raw as { vins?: string[] }).vins ?? []
      : [];
    if (found.map((v) => v.toUpperCase()).includes(want)) {
      return { confidence: 'exact', reason: { rule: 'vin', fields: ['vin'], detail: `VIN ${want}` } };
    }
    return null;
  }

  // --- category: always a candidate, never an alert ----------------------------------------
  if (watch.kind === 'category' && watch.category) {
    const cat = tokens(watch.category);
    const hay = tokens([recall.title, ...recall.products, recall.hazard].join(' '));
    const hit = cat.length > 0 && cat.every((t) => hay.includes(t));
    if (!hit) return null;
    return {
      confidence: 'candidate',
      reason: {
        rule: 'category',
        fields: ['category'],
        detail: `category "${watch.category}" appears in the notice; a person must confirm`,
      },
    };
  }

  // --- brand + product ---------------------------------------------------------------------
  const brandHit = brandsMatch(recall, watch);
  if (!brandHit) return null;

  if (!watch.product) {
    return {
      confidence: 'candidate',
      reason: {
        rule: 'brand-only',
        fields: ['brand'],
        detail: `brand "${brandHit}" matches but no product was recorded; a person must confirm`,
      },
    };
  }

  const { score, shared, against } = bestProductOverlap(recall, watch.product);
  if (score < PRODUCT_WEAK) return null;

  if (score < PRODUCT_STRONG || shared < MIN_SHARED) {
    return {
      confidence: 'candidate',
      reason: {
        rule: 'brand-and-fuzzy-product',
        fields: ['brand', 'product'],
        detail: `brand "${brandHit}"; product overlap ${score.toFixed(2)} against "${against}"`,
      },
    };
  }

  // Lot codes: when the notice names specific codes and the subscriber recorded one that is not
  // among them, this is a different production run and not their problem.
  if (recall.codeInfo && watch.lot) {
    if (!lotMatches(recall.codeInfo, watch.lot)) {
      return {
        confidence: 'candidate',
        reason: {
          rule: 'lot-mismatch',
          fields: ['brand', 'product', 'lot'],
          detail: `brand and product match but lot "${watch.lot}" is not among the recalled codes`,
        },
      };
    }
    return {
      confidence: 'strong',
      reason: {
        rule: 'brand-product-lot',
        fields: ['brand', 'product', 'lot'],
        detail: `brand "${brandHit}", product overlap ${score.toFixed(2)}, lot "${watch.lot}" listed`,
      },
    };
  }

  return {
    confidence: 'strong',
    reason: {
      rule: 'brand-product',
      fields: ['brand', 'product'],
      detail: `brand "${brandHit}", product overlap ${score.toFixed(2)} against "${against}"`,
    },
  };
}

/** Only these get a message without a human deciding. */
export function isAlertable(c: Confidence): boolean {
  return c === 'exact' || c === 'strong';
}
