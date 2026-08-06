import type { RecallSource } from './index.js';
import type { Recall } from '../types.js';

/**
 * openFDA food/drug enforcement adapter.
 *
 * ⚠️ NEVER RUN. This was written from openFDA's published field documentation
 * (recall_number, product_description, reason_for_recall, classification, code_info,
 * recalling_firm, report_date) but this build environment cannot reach api.fda.gov, so not one
 * line of it has executed against the real API. Field presence, pagination behaviour, rate
 * limits, and date formats are all assumptions.
 *
 * It refuses to run unless RECALL_WATCH_ALLOW_UNVERIFIED=1 is set, so nobody wires it into a
 * cron job believing it has been tested. Verify it, delete the guard, and record what you found
 * — VERIFY.md item 1.
 */
export class OpenFdaSource implements RecallSource {
  readonly name: string;

  constructor(
    private readonly endpoint: 'food' | 'drug' = 'food',
    private readonly limit = 100,
  ) {
    this.name = `fda-${endpoint}`;
  }

  async fetchSince(sinceISODate: string): Promise<Recall[]> {
    if (process.env.RECALL_WATCH_ALLOW_UNVERIFIED !== '1') {
      throw new Error(
        'OpenFdaSource has never been run against the real API — see the comment at the top of ' +
          'this file and VERIFY.md item 1. Set RECALL_WATCH_ALLOW_UNVERIFIED=1 to try it anyway, ' +
          'and compare what comes back against the fixtures before trusting a single match.',
      );
    }
    const from = sinceISODate.replace(/-/g, '');
    const to = '99991231';
    const url =
      `https://api.fda.gov/${this.endpoint}/enforcement.json` +
      `?search=report_date:[${from}+TO+${to}]&limit=${this.limit}`;

    const res = await fetch(url, { headers: { accept: 'application/json' } });
    if (!res.ok) throw new Error(`openFDA ${this.endpoint}: HTTP ${res.status}`);
    const body = (await res.json()) as { results?: Record<string, string>[] };
    return (body.results ?? []).map((r) => this.toRecall(r));
  }

  private toRecall(r: Record<string, string>): Recall {
    const desc = r.product_description ?? '';
    return {
      source: 'fda',
      sourceRef: r.recall_number ?? r.event_id ?? desc.slice(0, 64),
      title: desc.slice(0, 200),
      brands: r.recalling_firm ? [r.recalling_firm] : [],
      products: desc ? [desc] : [],
      // openFDA does not expose a structured UPC field; UPCs appear inside free text when they
      // appear at all. Extracting them from prose is a separate job — do not fake it here.
      upcs: [],
      codeInfo: r.code_info ?? '',
      hazard: r.reason_for_recall ?? '',
      severity: r.classification === 'Class I' ? 'high'
        : r.classification === 'Class II' ? 'medium'
        : r.classification === 'Class III' ? 'low' : 'unknown',
      remedy: '',
      announcedOn: (r.report_date ?? '').replace(/^(\d{4})(\d{2})(\d{2})$/, '$1-$2-$3'),
      url: '',
      raw: r,
    };
  }
}
