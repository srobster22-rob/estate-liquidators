import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { match } from './match.js';
import type { Confidence, Recall, WatchItem } from './types.js';

/**
 * Measures the matcher against hand-labelled pairs.
 *
 * The number that matters is PRECISION ON ALERTABLE (exact + strong), because those are the only
 * ones that reach a phone without a person looking. The brief's bar is ~95%: every false alarm
 * costs you the next real one.
 *
 * HONEST LIMITATION, and it is a real one: the same author wrote the matcher, the fixtures, and
 * the labels. This is a self-consistency and regression check, not an independent evaluation. A
 * genuine measurement needs real feed records and labels from somebody who did not write the
 * matching rules. See VERIFY.md.
 */

export interface Pair {
  id: string;
  recall: string;
  watch: Partial<WatchItem> & { kind: WatchItem['kind'] };
  expect: Confidence | null;
  note: string;
}

export interface EvalReport {
  total: number;
  correct: number;
  alertablePredicted: number;
  alertableCorrect: number;
  alertableExpected: number;
  alertableFound: number;
  precision: number;
  recall: number;
  /** The dangerous class: predicted alertable when it should not have been. */
  falseAlarms: { id: string; predicted: Confidence; expected: Confidence | null; note: string }[];
  /** Predicted nothing (or a candidate) when it should have alerted. */
  misses: { id: string; predicted: Confidence | null; expected: Confidence; note: string }[];
  mislabels: { id: string; predicted: Confidence | null; expected: Confidence | null; note: string }[];
}

function loadRecalls(fixtureDir: string): Map<string, Recall> {
  const map = new Map<string, Recall>();
  for (const f of readdirSync(fixtureDir).filter((f) => f.endsWith('.json'))) {
    for (const r of JSON.parse(readFileSync(join(fixtureDir, f), 'utf8')) as Recall[]) {
      map.set(r.sourceRef, r);
    }
  }
  return map;
}

const alertable = (c: Confidence | null) => c === 'exact' || c === 'strong';

export function evaluate(fixtureDir: string, pairsPath: string): EvalReport {
  const recalls = loadRecalls(fixtureDir);
  const pairs = JSON.parse(readFileSync(pairsPath, 'utf8')) as Pair[];

  const report: EvalReport = {
    total: pairs.length, correct: 0,
    alertablePredicted: 0, alertableCorrect: 0, alertableExpected: 0, alertableFound: 0,
    precision: 0, recall: 0, falseAlarms: [], misses: [], mislabels: [],
  };

  for (const p of pairs) {
    const recall = recalls.get(p.recall);
    if (!recall) throw new Error(`pair ${p.id} references unknown recall ${p.recall}`);

    const watch: WatchItem = {
      id: 0, subscriberId: 0, kind: p.watch.kind,
      brand: p.watch.brand ?? null, product: p.watch.product ?? null,
      upc: p.watch.upc ?? null, vin: p.watch.vin ?? null,
      category: p.watch.category ?? null, lot: p.watch.lot ?? null,
    };

    const got = match(recall, watch);
    const predicted = got?.confidence ?? null;

    if (predicted === p.expect) report.correct++;
    else report.mislabels.push({ id: p.id, predicted, expected: p.expect, note: p.note });

    if (alertable(p.expect)) report.alertableExpected++;
    if (alertable(predicted)) {
      report.alertablePredicted++;
      if (alertable(p.expect)) {
        report.alertableCorrect++;
        report.alertableFound++;
      } else {
        report.falseAlarms.push({ id: p.id, predicted: predicted!, expected: p.expect, note: p.note });
      }
    } else if (alertable(p.expect)) {
      report.misses.push({ id: p.id, predicted, expected: p.expect!, note: p.note });
    }
  }

  report.precision = report.alertablePredicted ? report.alertableCorrect / report.alertablePredicted : 1;
  report.recall = report.alertableExpected ? report.alertableFound / report.alertableExpected : 1;
  return report;
}

export function formatReport(r: EvalReport): string {
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`;
  const lines = [
    '',
    `Pairs:                 ${r.total}`,
    `Exact label agreement: ${r.correct}/${r.total} (${pct(r.correct / r.total)})`,
    '',
    `ALERTABLE precision:   ${pct(r.precision)}  (${r.alertableCorrect}/${r.alertablePredicted} predicted alerts were right)`,
    `ALERTABLE recall:      ${pct(r.recall)}  (${r.alertableFound}/${r.alertableExpected} real alerts were found)`,
    '',
  ];
  if (r.falseAlarms.length) {
    lines.push('FALSE ALARMS — these would have texted somebody wrongly:');
    for (const f of r.falseAlarms) lines.push(`  ${f.id}  predicted ${f.predicted}, expected ${f.expected ?? 'no match'} — ${f.note}`);
    lines.push('');
  }
  if (r.misses.length) {
    lines.push('MISSES — a real recall that would not have reached them:');
    for (const m of r.misses) lines.push(`  ${m.id}  predicted ${m.predicted ?? 'no match'}, expected ${m.expected} — ${m.note}`);
    lines.push('');
  }
  const other = r.mislabels.filter(
    (m) => !r.falseAlarms.some((f) => f.id === m.id) && !r.misses.some((x) => x.id === m.id),
  );
  if (other.length) {
    lines.push('Other disagreements (both sides non-alerting, so nobody is texted either way):');
    for (const m of other) lines.push(`  ${m.id}  predicted ${m.predicted ?? 'no match'}, expected ${m.expected ?? 'no match'} — ${m.note}`);
    lines.push('');
  }
  return lines.join('\n');
}
