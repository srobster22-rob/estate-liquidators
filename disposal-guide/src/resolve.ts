import type {
  DataIndex,
  Hazard,
  Item,
  Location,
  ResolvedAnswer,
  Verdict,
} from './types.js';

/** Verdicts that put the thing in a truck. Never allowed for neverCurbside items. */
const CURBSIDE: ReadonlySet<Verdict> = new Set<Verdict>(['recycling_cart', 'trash_cart', 'yard_waste']);

/**
 * The safe answer when we don't know. Never "trash" — a wrong "trash" for a propane cylinder
 * or a lithium pouch is the failure this whole project exists to prevent, and "take it to
 * hazardous waste" is never dangerous, only inconvenient.
 */
function safeFallback(hazard: Hazard): Verdict {
  switch (hazard) {
    case 'professional':
      return 'professional_only';
    case 'hazardous':
      return 'hazardous_waste';
    case 'caution':
    case 'none':
    default:
      return 'unknown';
  }
}

/**
 * Runtime guard mirroring the build-time validation in scripts/build-index.ts.
 *
 * A local rule may not send a neverCurbside or hazardous item to a household bin. The build
 * refuses to emit such data at all; this is the second line, so a hand-edited index or a future
 * refactor cannot produce a dangerous answer.
 */
export function clampVerdict(item: Item, proposed: Verdict): Verdict {
  const u = item.universal;
  if (!u) return proposed;
  if (!CURBSIDE.has(proposed)) return proposed;
  if (u.neverCurbside) return safeFallback(u.hazard);
  if (u.hazard === 'hazardous' || u.hazard === 'professional') return safeFallback(u.hazard);
  return proposed;
}

export function isDisambiguation(item: Item): boolean {
  return Array.isArray(item.disambiguates) && item.disambiguates.length > 0;
}

export function resolve(index: DataIndex, item: Item, opts: { allowDemo?: boolean } = {}): ResolvedAnswer {
  const { jurisdiction, locations } = index;
  const u = item.universal;
  const hazard: Hazard = u?.hazard ?? 'none';

  const localRule = jurisdiction.configured ? item.local?.[jurisdiction.id] : undefined;

  const byId = new Map(locations.map((l) => [l.id, l]));
  const wanted = localRule?.destinations ?? [];
  let destinations: Location[] = wanted
    .map((id) => byId.get(id))
    .filter((l): l is Location => Boolean(l))
    // A location only counts as a destination if its own record says it takes this item.
    .filter((l) => l.acceptsSlugs.includes(item.slug));

  const demoDropped = destinations.some((l) => l.isDemo);
  if (!opts.allowDemo) destinations = destinations.filter((l) => !l.isDemo);

  const base: Omit<ResolvedAnswer, 'verdict' | 'isLocal' | 'caveat'> = {
    item,
    hazard,
    why: u?.why,
    prep: u?.prep ?? [],
    nationalOptions: u?.nationalOptions ?? [],
    destinations,
    verifiedOn: localRule?.verifiedOn,
    verifiedBy: localRule?.verifiedBy,
    sources: u?.sources ?? [],
  };

  if (!localRule) {
    // No confirmed local rule. Say what we do know — which for a hazardous item is a great
    // deal — and be explicit that the bin question is unanswered rather than answered "trash".
    const verdict: Verdict = u?.neverCurbside ? safeFallback(hazard) : safeFallback(hazard);
    return {
      ...base,
      verdict: u ? verdict : 'unknown',
      isLocal: false,
      caveat: jurisdiction.configured ? 'no_data' : 'not_configured',
    };
  }

  return {
    ...base,
    verdict: clampVerdict(item, localRule.verdict),
    isLocal: true,
    caveat: demoDropped && destinations.length === 0 ? 'demo_data' : undefined,
  };
}

/** Human-facing verdict text. Deliberately plain; no jargon, no color-only meaning. */
export const VERDICT_LABEL: Record<Verdict, string> = {
  recycling_cart: 'Recycling cart',
  trash_cart: 'Trash cart',
  yard_waste: 'Yard waste',
  special_dropoff: 'Special drop-off',
  retail_takeback: 'Take it back to a store',
  hazardous_waste: 'Hazardous waste only',
  not_in_any_bin: 'Not in any of your bins',
  professional_only: 'Call a professional',
  unknown: "We don't know your town's rule for this",
};

/** One line under the verdict. Never softens an unknown into an implied "it's fine". */
export const VERDICT_SUBTEXT: Record<Verdict, string> = {
  recycling_cart: 'Goes in your recycling.',
  trash_cart: 'Goes in your regular trash.',
  yard_waste: 'Goes in your yard waste collection.',
  special_dropoff: 'Has to be dropped off somewhere specific.',
  retail_takeback: 'A store near you takes these back.',
  hazardous_waste: 'This has to go to household hazardous waste. Do not put it in a bin.',
  not_in_any_bin: 'Do not put this in the trash or the recycling. It is not safe in a truck.',
  professional_only: 'Do not handle this yourself. This one needs someone trained.',
  unknown: 'Nobody has confirmed the rule here yet. Call before you guess.',
};

export const HAZARD_ORDER: Record<Hazard, number> = {
  none: 0,
  caution: 1,
  hazardous: 2,
  professional: 3,
};
