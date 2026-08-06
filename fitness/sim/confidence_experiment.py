"""
MESO — R3. Can the system tell when it does not know, and does saying so help?

Three experiments:

  1. SIGNALS    Which of the four candidate confidence signals actually tracks the error
                it is supposed to predict? Rank correlation against the realised |log MRV
                error|, so a signal is only credited for ordering lifters correctly.

  2. OUTCOME    The one that decides the round. Four prescription policies scored in
                PREPAREDNESS POINTS LOST, not percent error:

                  PRIOR    always prescribe the population prior's MRV
                  FITTED   always prescribe the fit, ungated (what R2 leaves you with)
                  HARD     prior until 24 weeks logged, then the fit (D-02's threshold)
                  SHRUNK   empirical-Bayes shrinkage toward the prior, no threshold

                Points, because R1 established them as the currency and because the
                preparedness curve is ASYMMETRIC — overshooting MRV costs far more than
                undershooting it, and every percent-error table in this project has been
                hiding that.

  3. TAIL       R2's actual complaint was never the median. Report the p90 and worst-case
                loss, since a gate that improves the median while leaving the tail intact
                has not done the job it was built for.

METHODOLOGY, per D-12
  24+ lifters, and common random numbers across arms: every policy sees the same lifters
  and the same measurement noise, so the comparisons are paired rather than four
  independent noisy estimates.
"""

from __future__ import annotations

import math
import statistics

from confidence import (
    TRUE_SAT,
    population_log_mrv_spread,
    preparedness_lost,
    prescribe,
    spearman,
)
from ff_model import lifter_population
from fit import HISTORIES, make_log, mrv

N_LIFTERS = 24
BOOTSTRAP_DRAWS = 12


def _pct(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, int(q * len(s)))]


def _run(history: str, weeks: int, n: int = N_LIFTERS):
    """One paired run: same lifters, same noise, every policy scored on all of them."""
    _, tau = population_log_mrv_spread()
    prior_mrv = mrv(__import__("ff_model").POPULATION_PRIOR, TRUE_SAT)
    prior_log = math.log(prior_mrv)

    weekly = HISTORIES[history](weeks)
    rows = []
    for i, truth in enumerate(lifter_population(n, seed=31337)):
        log = make_log(weekly, truth, TRUE_SAT, seed=7000 + i)
        c = prescribe(log, tau, prior_log, draws=BOOTSTRAP_DRAWS, seed=i)
        true_mrv = mrv(truth, TRUE_SAT)
        rows.append({
            "truth": truth,
            "true_mrv": true_mrv,
            "conf": c,
            "log_err": abs(math.log(max(c.fitted_mrv, 1e-6)) - math.log(true_mrv)),
            "loss_prior": preparedness_lost(prior_mrv, truth),
            "loss_fitted": preparedness_lost(c.fitted_mrv, truth),
            "loss_hard": preparedness_lost(
                c.fitted_mrv if weeks >= 24 else prior_mrv, truth
            ),
            "loss_shrunk": preparedness_lost(c.prescribed_mrv, truth),
        })
    return rows


def signals() -> None:
    print("\n1. SIGNALS — rank correlation with realised |log MRV error| (higher = better predictor)")
    print("  history  weeks   weeks_logged   variation   resid_rmse   bootstrap_sd")
    print("  " + "-" * 74)
    for history in ("FLAT", "WAVED", "PROBE"):
        for weeks in (12, 24):
            rows = _run(history, weeks)
            errs = [r["log_err"] for r in rows]
            cols = [
                spearman([float(r["conf"].weeks_logged) for r in rows], errs),
                spearman([r["conf"].volume_variation for r in rows], errs),
                spearman([r["conf"].residual_rmse for r in rows], errs),
                spearman([r["conf"].bootstrap_rel_sd for r in rows], errs),
            ]
            fmt = "  ".join(
                "     const" if math.isnan(c) else f"{c:10.2f}" for c in cols
            )
            print(f"  {history:<8} {weeks:5d}   {fmt}")
    print("\n  'const' = the signal does not vary within a run, so it cannot rank lifters")
    print("  inside one. weeks_logged and variation are constant per history/week cell by")
    print("  construction — they discriminate ACROSS the rows of this table, not within.")


def outcome() -> None:
    print("\n2. OUTCOME — mean preparedness points lost (lower = better). Paired, 24 lifters.")
    print("  history  weeks    PRIOR   FITTED     HARD   SHRUNK   shrunk vs fitted")
    print("  " + "-" * 74)
    for history in ("FLAT", "WAVED", "PROBE"):
        for weeks in (8, 12, 24, 52):
            rows = _run(history, weeks)
            means = {
                k: statistics.fmean([r[f"loss_{k}"] for r in rows])
                for k in ("prior", "fitted", "hard", "shrunk")
            }
            delta = means["shrunk"] - means["fitted"]
            print(
                f"  {history:<8} {weeks:5d} {means['prior']:8.2f} {means['fitted']:8.2f}"
                f" {means['hard']:8.2f} {means['shrunk']:8.2f}   {delta:+8.2f}"
            )


def tail() -> None:
    print("\n3. TAIL — p90 and worst-case preparedness points lost")
    print("  history  weeks   FITTED p90   FITTED worst   SHRUNK p90   SHRUNK worst")
    print("  " + "-" * 72)
    for history in ("WAVED", "PROBE"):
        for weeks in (12, 24):
            rows = _run(history, weeks)
            f = [r["loss_fitted"] for r in rows]
            s = [r["loss_shrunk"] for r in rows]
            print(
                f"  {history:<8} {weeks:5d} {_pct(f, 0.9):12.2f} {max(f):14.2f}"
                f" {_pct(s, 0.9):12.2f} {max(s):14.2f}"
            )


def weights() -> None:
    print("\n4. WHAT THE GATE ACTUALLY DOES — mean shrinkage weight w (1 = trust the fit)")
    print("  history   8wk    12wk    24wk    52wk")
    print("  " + "-" * 42)
    for history in ("FLAT", "WAVED", "PROBE"):
        ws = []
        for weeks in (8, 12, 24, 52):
            rows = _run(history, weeks)
            ws.append(statistics.fmean([r["conf"].weight for r in rows]))
        print(f"  {history:<8} " + " ".join(f"{w:6.2f}" for w in ws))


def cliff() -> None:
    """
    Resolve the 12 -> 24 week transition.

    Experiment 2 samples weeks at 8, 12, 24, 52 and shows mean loss falling from 44.4 to
    0.53 between the middle two. A threshold rule needs to know whether that is a cliff
    or a slope, and two sample points cannot tell you. If the gate is going to hard-code
    a number, the number has to come from the shape rather than from the sampling grid.
    """
    print("\n5. THE CLIFF — WAVED history, week by week (mean / p90 points lost)")
    print("  weeks   PRIOR    FITTED mean   FITTED p90   SHRUNK mean   SHRUNK p90   mean w")
    print("  " + "-" * 80)
    for weeks in (8, 10, 12, 14, 16, 18, 20, 22, 24, 28):
        rows = _run("WAVED", weeks)
        f = [r["loss_fitted"] for r in rows]
        s = [r["loss_shrunk"] for r in rows]
        w = statistics.fmean([r["conf"].weight for r in rows])
        print(
            f"  {weeks:5d} {statistics.fmean([r['loss_prior'] for r in rows]):7.2f}"
            f" {statistics.fmean(f):13.2f} {_pct(f, 0.9):12.2f}"
            f" {statistics.fmean(s):13.2f} {_pct(s, 0.9):12.2f} {w:8.2f}"
        )


def main() -> None:
    _, tau = population_log_mrv_spread()
    print("MESO R3 — the confidence gate")
    print(f"  population SD of log(MRV), tau = {tau:.3f}  (not a tunable; a property of the prior)")
    signals()
    outcome()
    tail()
    weights()


if __name__ == "__main__":
    main()
