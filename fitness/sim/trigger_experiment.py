"""
MESO — R4. Is "which way is uphill" an easier question than "where is the peak"?

The hypothesis this round exists to test:

    R3 established the fitter cannot be trusted to locate MRV for 18 weeks. But locating
    an argmax is a strictly harder estimation problem than getting the sign of a slope
    right. If the sign is reliable early, a hill-climbing controller converges on the
    lifter's own MRV long before anyone could estimate it — filling exactly the gap R3
    opened, during which R3's rule currently prescribes a population average.

FOUR EXPERIMENTS

  1. SIGN vs ARGMAX   The hypothesis, measured directly. Sign accuracy of the estimated
                      marginal return against weeks logged, next to MRV error over the
                      same data. If they converge together, the round is over and the
                      answer is no.

  2. CLOSED LOOP      Mean preparedness points lost over a 24-week block, controllers
                      running against the same lifters with the same noise (D-12).
                      Includes R1's level trigger as the baseline a new mechanism has to
                      beat, and an oracle that knows the truth as the floor.

  3. CONVERGENCE      Weeks until the prescription settles within 15% of true MRV.

  4. BREAKING IT      Step size, starting point, and dither. A controller that only works
                      from a lucky start with a tuned step is a tuned constant.
"""

from __future__ import annotations

import math
import statistics

from confidence import TRUE_SAT, preparedness_lost
from ff_model import POPULATION_PRIOR, lifter_population
from fit import HISTORIES, make_log, mrv
from trigger import (
    HillClimb,
    LevelTrigger,
    marginal_return,
    normalised_marginal_return,
    points_lost_over_block,
    run_closed_loop,
    weeks_to_converge,
)

N_LIFTERS = 24
BLOCK_WEEKS = 24
PRIOR_MRV = mrv(POPULATION_PRIOR, TRUE_SAT)


def _pct(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, int(q * len(s)))]


def sign_vs_argmax() -> None:
    print("\n1. SIGN vs ARGMAX — is the direction easier than the location?")
    print("  Fitted on a WAVED history. 'sign ok' = estimated marginal return has the")
    print("  correct sign at a volume 40% below / 50% above the lifter's true MRV.")
    print()
    print("  weeks   sign ok (below MRV)   sign ok (above MRV)   median MRV error")
    print("  " + "-" * 72)
    population = lifter_population(N_LIFTERS, seed=31337)
    from fit import fit

    for weeks in (4, 6, 8, 10, 12, 16, 18, 24):
        weekly = HISTORIES["WAVED"](weeks)
        ok_below = ok_above = 0
        errs: list[float] = []
        for i, truth in enumerate(population):
            true_mrv = mrv(truth, TRUE_SAT)
            log = make_log(weekly, truth, TRUE_SAT, seed=8000 + i)
            got, got_sat, _ = fit(log, restarts=2)
            errs.append(abs(mrv(got, got_sat) - true_mrv) / true_mrv * 100.0)
            for factor, bucket in ((0.60, "below"), (1.50, "above")):
                v = true_mrv * factor
                est = marginal_return(v, got, got_sat)
                true_slope = marginal_return(v, truth, TRUE_SAT)
                if est * true_slope > 0:
                    if bucket == "below":
                        ok_below += 1
                    else:
                        ok_above += 1
        n = len(population)
        print(
            f"  {weeks:5d}   {ok_below / n * 100:17.0f}%   {ok_above / n * 100:17.0f}%"
            f"   {statistics.median(errs):15.1f}%"
        )


def closed_loop() -> None:
    print(f"\n2. CLOSED LOOP — mean preparedness points lost over {BLOCK_WEEKS} weeks")
    print("  (paired: same lifters, same noise. lower is better; ORACLE is the floor)")
    print()
    print("  policy                 mean     p90    worst")
    print("  " + "-" * 46)
    population = lifter_population(N_LIFTERS, seed=31337)

    results: dict[str, list[float]] = {k: [] for k in (
        "ORACLE", "PRIOR-FIXED", "GATED (R3)", "LEVEL-TRIGGER (R1)",
        "HILL-CLIMB", "HILL-CLIMB+dither",
    )}

    for i, truth in enumerate(population):
        true_mrv = mrv(truth, TRUE_SAT)
        results["ORACLE"].append(preparedness_lost(true_mrv, truth))
        results["PRIOR-FIXED"].append(preparedness_lost(PRIOR_MRV, truth))

        # R3's rule: prior until week 18, then the fit. Scored over the same block.
        weekly = HISTORIES["WAVED"](BLOCK_WEEKS)
        log = make_log(weekly, truth, TRUE_SAT, seed=9000 + i)
        from fit import fit as _fit
        got, got_sat, _ = _fit(log, restarts=2)
        gated = [PRIOR_MRV] * 18 + [mrv(got, got_sat)] * (BLOCK_WEEKS - 18)
        results["GATED (R3)"].append(points_lost_over_block(gated, truth))

        pres, _ = run_closed_loop(truth, BLOCK_WEEKS, LevelTrigger(PRIOR_MRV), seed=9000 + i)
        results["LEVEL-TRIGGER (R1)"].append(points_lost_over_block(pres, truth))

        pres, _ = run_closed_loop(truth, BLOCK_WEEKS, HillClimb(PRIOR_MRV), seed=9000 + i)
        results["HILL-CLIMB"].append(points_lost_over_block(pres, truth))

        pres, _ = run_closed_loop(
            truth, BLOCK_WEEKS, HillClimb(PRIOR_MRV, dither=0.18), seed=9000 + i
        )
        results["HILL-CLIMB+dither"].append(points_lost_over_block(pres, truth))

    for name, vals in results.items():
        print(f"  {name:<20} {statistics.fmean(vals):7.2f} {_pct(vals, 0.9):7.2f}"
              f" {max(vals):8.2f}")


def convergence() -> None:
    print("\n3. CONVERGENCE — weeks until the prescription settles within 15% of true MRV")
    print("  controller             converged   median wk   p90 wk")
    print("  " + "-" * 54)
    population = lifter_population(N_LIFTERS, seed=31337)
    for name, make in (
        ("HILL-CLIMB", lambda: HillClimb(PRIOR_MRV)),
        ("HILL-CLIMB+dither", lambda: HillClimb(PRIOR_MRV, dither=0.18)),
        ("LEVEL-TRIGGER (R1)", lambda: LevelTrigger(PRIOR_MRV)),
    ):
        weeks_list: list[int] = []
        for i, truth in enumerate(population):
            c = make()
            run_closed_loop(truth, 40, c, seed=9000 + i)
            # Scored on the controller's centre, not its dithered prescription — see the
            # note in run_closed_loop. Otherwise any dither wider than `tol` reads as
            # "never converged" no matter how well the controller tracked the peak.
            w = weeks_to_converge(c.state.weeks, truth)
            if w is not None:
                weeks_list.append(w)
        share = len(weeks_list) / len(population) * 100
        med = statistics.median(weeks_list) if weeks_list else float("nan")
        p90 = _pct([float(w) for w in weeks_list], 0.9) if weeks_list else float("nan")
        print(f"  {name:<20} {share:9.0f}% {med:11.1f} {p90:8.1f}")


def breaking_it() -> None:
    print("\n4. BREAKING IT — does the controller depend on a lucky start or a tuned step?")
    population = lifter_population(16, seed=31337)

    print("\n  step size (start = prior MRV, no dither)")
    print("    step    mean points lost    p90")
    print("    " + "-" * 40)
    for step in (0.05, 0.08, 0.12, 0.20, 0.30):
        vals = []
        for i, truth in enumerate(population):
            pres, _ = run_closed_loop(
                truth, BLOCK_WEEKS, HillClimb(PRIOR_MRV, step_frac=step), seed=9000 + i
            )
            vals.append(points_lost_over_block(pres, truth))
        print(f"    {step:4.2f}   {statistics.fmean(vals):15.2f} {_pct(vals, 0.9):8.2f}")

    print("\n  starting volume (step 0.12, no dither)")
    print("    start    mean points lost    p90")
    print("    " + "-" * 41)
    for start in (6.0, 12.0, PRIOR_MRV, 45.0):
        vals = []
        for i, truth in enumerate(population):
            pres, _ = run_closed_loop(
                truth, BLOCK_WEEKS, HillClimb(start), seed=9000 + i
            )
            vals.append(points_lost_over_block(pres, truth))
        print(f"    {start:5.1f}   {statistics.fmean(vals):15.2f} {_pct(vals, 0.9):8.2f}")

    print("\n  dither (step 0.12, start = prior MRV)")
    print("    dither   mean points lost    p90")
    print("    " + "-" * 41)
    for d in (0.0, 0.10, 0.18, 0.30):
        vals = []
        for i, truth in enumerate(population):
            pres, _ = run_closed_loop(
                truth, BLOCK_WEEKS, HillClimb(PRIOR_MRV, dither=d), seed=9000 + i
            )
            vals.append(points_lost_over_block(pres, truth))
        print(f"    {d:5.2f}   {statistics.fmean(vals):15.2f} {_pct(vals, 0.9):8.2f}")


def main() -> None:
    print("MESO R4 — the dose-derivative controller (D-07)")
    print(f"  prior MRV = {PRIOR_MRV:.1f} sets/wk, the volume every controller starts from")
    sign_vs_argmax()
    closed_loop()
    convergence()
    breaking_it()


if __name__ == "__main__":
    main()
