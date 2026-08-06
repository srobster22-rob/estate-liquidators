export type SourceName = 'fda' | 'fsis' | 'cpsc' | 'nhtsa';

/** Severity, normalized across feeds. `high` is the only class that earns a text message. */
export type Severity = 'high' | 'medium' | 'low' | 'unknown';

export interface Recall {
  source: SourceName;
  /** The feed's own identifier. Together with `source` this is the idempotency key. */
  sourceRef: string;
  title: string;
  brands: string[];
  products: string[];
  upcs: string[];
  codeInfo: string;
  hazard: string;
  severity: Severity;
  remedy: string;
  announcedOn: string;
  url: string;
  raw: unknown;
}

export type WatchKind = 'product' | 'upc' | 'vin' | 'category';

export interface WatchItem {
  id: number;
  subscriberId: number;
  kind: WatchKind;
  brand: string | null;
  product: string | null;
  upc: string | null;
  vin: string | null;
  category: string | null;
  lot: string | null;
}

export type Confidence = 'exact' | 'strong' | 'candidate';

export interface MatchResult {
  confidence: Confidence;
  /** Why it matched, field by field. A match that cannot explain itself is a bug. */
  reason: { rule: string; fields: string[]; detail: string };
}
