export interface SourceRef {
  org: string;
  title: string;
  url: string;
  retrieved: string;
  method: 'fetched' | 'search_index' | 'phone' | 'in_person';
}

export interface WaitingPeriodException {
  id: string;
  days: number;
  question: string;
  detail: string;
}

export interface WaitingPeriodRule {
  days: number;
  exceptions: WaitingPeriodException[];
  sources: SourceRef[];
}

export interface WaitingPeriodResult {
  days: number;
  ruleId: string;
  detail: string;
  /** ISO date. The whole point: a date, never a duration. */
  effectiveOn: string;
  purchasedOn: string;
  sources: SourceRef[];
}

export interface Gap {
  id: string;
  name: string;
  what: string;
  coveredByHomeowners: boolean;
  why: string;
  rentersNote?: string;
  sources: SourceRef[];
}

export type GapState = 'yes' | 'no' | 'unknown';
export interface GapAnswer { gapId: string; state: GapState }

export interface GapVerdict {
  gap: Gap;
  state: GapState;
  isGap: boolean;
  needsChecking: boolean;
  lookFor: string;
  sources: SourceRef[];
}

export interface CoverageData {
  waitingPeriod: WaitingPeriodRule;
  gaps: Gap[];
  declarationsHints: { gapId: string; lookFor: string }[];
}

export interface SafetyPoint { text: string; sources: SourceRef[] }

export interface SafetyData {
  emergency: { headline: string; points: SafetyPoint[] };
  mold: { window_hours: number; text: string; sources: SourceRef[] };
  prepare: {
    id: string; title: string; detail: string; cost: string; sources: SourceRef[];
  }[];
}

export interface LocalData {
  id: string;
  city: string;
  county: string;
  state: string;
  languages: string[];
  configured: boolean;
  resources: {
    id: string; name: string; kind: string; phone?: string; url?: string; note?: string;
    verifiedOn: string; verifiedBy: string;
  }[];
}

export interface DataIndex {
  coverage: CoverageData;
  safety: SafetyData;
  local: LocalData;
  builtAt: string;
}
