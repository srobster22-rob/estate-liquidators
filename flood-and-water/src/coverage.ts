import type { CoverageData, Gap, WaitingPeriodResult, GapAnswer, GapVerdict } from './types.js';

/**
 * The waiting period, as a date.
 *
 * This is the whole product. "There is a 30-day waiting period" reads as trivia; "if you buy
 * today, you are covered starting <date>" reads as a deadline, and the purchase decision has to
 * be made on a dry day. Everything else in this app exists to get someone to this sentence
 * before the water does.
 */

/** Calendar-day arithmetic in UTC, so a DST transition can never shift the result by a day. */
export function addDays(from: Date, days: number): Date {
  const d = new Date(Date.UTC(from.getUTCFullYear(), from.getUTCMonth(), from.getUTCDate()));
  d.setUTCDate(d.getUTCDate() + days);
  return d;
}

export function toISODate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/**
 * Returns the effective date and which rule produced it.
 *
 * `applicableExceptionIds` are the exceptions the user said apply to them. The shortest wait
 * wins — a household can be inside more than one exception, and giving them the longer one
 * would be wrong in the direction that costs coverage.
 */
export function waitingPeriod(
  data: CoverageData,
  purchaseDate: Date,
  applicableExceptionIds: string[] = [],
): WaitingPeriodResult {
  const wp = data.waitingPeriod;
  let days = wp.days;
  let ruleId = 'standard';
  let detail = `New flood policies generally take effect ${wp.days} days after purchase.`;

  for (const ex of wp.exceptions) {
    if (!applicableExceptionIds.includes(ex.id)) continue;
    if (ex.days < days) {
      days = ex.days;
      ruleId = ex.id;
      detail = ex.detail;
    }
  }

  return {
    days,
    ruleId,
    detail,
    effectiveOn: toISODate(addDays(purchaseDate, days)),
    purchasedOn: toISODate(purchaseDate),
    sources: wp.sources,
  };
}

/**
 * What the household is and is not covered for.
 *
 * "unknown" is a first-class verdict and the most common honest one — most people genuinely do
 * not know what is on their declarations page, and guessing on their behalf would be the same
 * mistake this whole kit is written against. An unknown renders the phrase to search their own
 * paperwork for.
 */
export function assessGaps(data: CoverageData, answers: GapAnswer[]): GapVerdict[] {
  const byId = new Map(answers.map((a) => [a.gapId, a.state]));
  const hints = new Map(data.declarationsHints.map((h) => [h.gapId, h.lookFor]));

  return data.gaps.map((gap: Gap): GapVerdict => {
    const state = byId.get(gap.id) ?? 'unknown';
    return {
      gap,
      state,
      // Only "no" is a confirmed gap. "unknown" is a thing to go check, and the difference
      // matters: telling someone they have a gap they may not have costs your credibility, and
      // telling them they are fine when they never checked costs them a house.
      isGap: state === 'no',
      needsChecking: state === 'unknown',
      lookFor: hints.get(gap.id) ?? '',
      sources: gap.sources,
    };
  });
}

/** Renters get a different sentence for the flood gap, and it is the one that lands. */
export function rentersNote(data: CoverageData): string | undefined {
  return data.gaps.find((g) => g.id === 'flood')?.rentersNote;
}
