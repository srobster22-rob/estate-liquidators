/**
 * The two-layer verdict model — the central design decision of this project.
 *
 * UNIVERSAL layer: facts that are true regardless of where you live. "Lithium batteries start
 *   fires when crushed in a truck." "Never put loose needles in any bin." These come from
 *   federal agencies, they are citable, and they are safe to ship.
 *
 * LOCAL layer: which of YOUR bins, which facility, what hours. These are municipal, they change,
 *   and they are only true after somebody phones and confirms them.
 *
 * The layers are separate types on purpose. An item with universal guidance and no local
 * configuration renders an honest partial answer — the hazard, the why, the prep, and "we don't
 * know your town's rule yet, here's who to ask." It NEVER guesses which bin.
 *
 * This is what makes the app safe to ship before the phone calls are made, and it is why
 * `LocalRule` is nullable everywhere it appears.
 */

/** How badly a wrong answer hurts. Drives the safe-default in resolveVerdict(). */
export type Hazard =
  | 'none' // paper, cardboard
  | 'caution' // sharp, heavy, messy — not dangerous in a truck
  | 'hazardous' // fire, toxicity, pressure — never guess a bin for these
  | 'professional'; // asbestos, mercury spills — the app's only job is routing to a pro

/** What the app tells you to do. */
export type Verdict =
  | 'recycling_cart'
  | 'trash_cart'
  | 'yard_waste'
  | 'special_dropoff'
  | 'retail_takeback'
  | 'hazardous_waste'
  | 'not_in_any_bin' // universal negative: we know it's not curbside, we don't know where it goes
  | 'professional_only'
  | 'unknown'; // no universal rule AND no local config — say so, don't guess

export interface SourceRef {
  /** Publishing body, e.g. "US EPA". */
  org: string;
  /** Page or document title as published. */
  title: string;
  url: string;
  /** ISO date this was checked. Displayed to the user. */
  retrieved: string;
  /**
   * How it was checked. `search_index` means the content was confirmed through a web search
   * index but the page itself was not fetched — weaker than `fetched`, and shown as such.
   */
  method: 'fetched' | 'search_index' | 'phone' | 'in_person';
}

/** Locale-keyed display strings. `en` is required; others optional. */
export interface I18nText {
  en: string;
  [lang: string]: string;
}

/** Facts true everywhere. Shippable before any phone call. */
export interface UniversalGuidance {
  hazard: Hazard;
  /**
   * True when federal/authoritative guidance says this must not go in household trash or
   * recycling anywhere. Hard-blocks a local rule from claiming otherwise — see resolveVerdict().
   */
  neverCurbside: boolean;
  /** One plain sentence. The mechanism, not the rule — "starts fires in the truck". */
  why: I18nText;
  /** Concrete prep steps: tape the terminals, keep it in the original container. */
  prep: I18nText[];
  /** Nationally-available options that don't depend on the local hauler. */
  nationalOptions?: I18nText[];
  sources: SourceRef[];
}

/** The municipal answer. Only exists after somebody confirmed it by phone. */
export interface LocalRule {
  verdict: Verdict;
  /** Location ids this item can go to. */
  destinations: string[];
  notes?: I18nText;
  quantityLimit?: I18nText;
  verifiedOn: string;
  /** A person's name or role. "the county HHW line, 2026-08-05" — not "the website". */
  verifiedBy: string;
}

export interface Item {
  slug: string;
  /** Display names and every colloquialism people actually type, per language. */
  names: Record<string, string[]>;
  category: string;
  /**
   * When set, searching this item returns a disambiguation screen rather than an answer.
   * "battery" must never resolve to a single verdict — alkaline and lithium-ion differ, and
   * one of them starts fires.
   */
  disambiguates?: string[];
  universal?: UniversalGuidance;
  /** Keyed by jurisdiction id. Absent = not configured here. */
  local?: Record<string, LocalRule>;
}

export interface OpeningHours {
  /** 0 = Sunday. Missing day = closed. */
  [weekday: number]: { open: string; close: string }[];
}

export interface Location {
  id: string;
  name: string;
  address: string;
  phone?: string;
  url?: string;
  hours?: OpeningHours;
  hoursNote?: I18nText;
  acceptsSlugs: string[];
  residencyRequired?: boolean;
  proofRequired?: I18nText;
  feesNote?: I18nText;
  verifiedOn?: string;
  verifiedBy?: string;
  /** Demo rows are fictional and must never render as a real destination. */
  isDemo?: boolean;
}

export interface Jurisdiction {
  id: string;
  city: string;
  county: string;
  state: string;
  hauler: string;
  timezone: string;
  languages: string[];
  /**
   * False until a human has done the M0 phone calls. Drives the "not set up for your area"
   * banner and suppresses every local verdict.
   */
  configured: boolean;
}

export interface DataIndex {
  jurisdiction: Jurisdiction;
  items: Item[];
  locations: Location[];
  builtAt: string;
}

/** What the UI actually renders for one item. */
export interface ResolvedAnswer {
  item: Item;
  verdict: Verdict;
  /** True when the verdict came from a confirmed local rule rather than a universal fallback. */
  isLocal: boolean;
  hazard: Hazard;
  why?: I18nText;
  prep: I18nText[];
  nationalOptions: I18nText[];
  destinations: Location[];
  verifiedOn?: string;
  verifiedBy?: string;
  /** Set when we are deliberately declining to answer. Rendered prominently. */
  caveat?: 'not_configured' | 'demo_data' | 'no_data';
  sources: SourceRef[];
}
