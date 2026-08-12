"""
MESO — R7. Does the measurement chain inject more noise than D-09 assumes?

The question this exists to answer:

    Every week-threshold in this project (D-13's 14 and 18, D-02's data requirement,
    R3's whole gate) rests on D-09: one weekly performance test with a measurement noise
    of sigma = 2.5 points, i.e. a 2.5% CV. That figure was taken as the test-retest
    variability of an estimated 1RM and never examined.

    But an e1RM is not a measurement. It is a *formula applied to* a measurement, and the
    published formulas disagree with each other. If that disagreement alone is comparable
    to sigma, then D-09 is optimistic, and every threshold downstream is too early.

WHAT IS MEASURED
  1. Spread across Epley / Brzycki / Lombardi at the same set, over the rep range.
  2. The extra noise injected by RIR misestimation — a lifter who says "2 in reserve" and
     had 4 is not making a small error, because the reps enter the formula.
  3. What those two together do to the week-thresholds, by re-running R3's question at the
     implied sigma rather than the assumed one.

WHY IT BELONGS IN THE LOGGER
  Because this is the point where the project stops assuming its input and starts building
  the thing that produces it. The honest moment to check whether the input is as clean as
  assumed is while writing the code that generates it.
"""

from __future__ import annotations

import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))

from log import FORMULAS, e1rm  # noqa: E402

REP_RANGE = (1, 3, 5, 8, 10, 12, 15, 20)
TRUE_1RM = 100.0


def _load_for(reps: int, formula: str) -> float:
    """Load that a lifter with a 100kg true 1RM could move for `reps` under `formula`."""
    lo, hi = 1.0, 100.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if e1rm(mid, reps, 0.0, formula) > TRUE_1RM:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def formula_spread() -> float:
    """
    Disagreement between formulas at the same physical set.

    Ground truth is unknowable, so this asks the answerable version: take a load that
    Epley calls a true 100kg 1RM at n reps, and see what the others call it. The spread is
    the ambiguity a logged set carries before any biological variability is added.
    """
    print("\n1. FORMULA DISAGREEMENT — same set, three published formulas")
    print("  reps    load    epley   brzycki  lombardi    spread   as % of 1RM")
    print("  " + "-" * 68)
    spreads = []
    for reps in REP_RANGE:
        load = _load_for(reps, "epley")
        vals = {name: f(load, reps) for name, f in FORMULAS.items()}
        spread = max(vals.values()) - min(vals.values())
        spreads.append(spread)
        print(f"  {reps:4d} {load:7.1f} {vals['epley']:8.1f} {vals['brzycki']:9.1f}"
              f" {vals['lombardi']:9.1f} {spread:9.1f} {spread:12.1f}%")

    working = [s for r, s in zip(REP_RANGE, spreads) if 3 <= r <= 12]
    print(f"\n  mean spread over the 3-12 rep working range: {statistics.fmean(working):.1f}% of 1RM")
    return statistics.fmean(working)


def rir_error_cost() -> float:
    """
    What an honest RIR misestimate does to the observation.

    The convention everywhere in this project is that a set of n reps at RIR r is a set of
    (n + r) reps at failure. That presumes the lifter's RIR estimate is unbiased. It is
    well established that inexperienced lifters underestimate how many reps they have
    left — meaning the error is a BIAS, not noise, and biases do not average out over
    weeks the way sigma does.
    """
    print("\n2. RIR MISESTIMATION — reported RIR 2, actually had more")
    print("  reps   true RIR   reported e1RM   true e1RM   error")
    print("  " + "-" * 56)
    errors = []
    for reps in (5, 8, 10):
        load = _load_for(reps + 2, "epley")
        reported = e1rm(load, reps, 2.0)
        for true_rir in (3.0, 4.0, 5.0):
            actual = e1rm(load, reps, true_rir)
            err = abs(actual - reported) / actual * 100.0
            errors.append(err)
            print(f"  {reps:4d} {true_rir:10.0f} {reported:15.1f} {actual:11.1f} {err:7.1f}%")
    print(f"\n  mean error from a 1-3 RIR misestimate: {statistics.fmean(errors):.1f}%")
    return statistics.fmean(errors)


def implied_sigma(formula_pct: float, rir_pct: float) -> float:
    """
    Combine the two into an implied measurement sigma, against D-09's assumed 2.5.

    Added in quadrature, which assumes independence — defensible for formula choice
    (a fixed convention, so arguably not noise at all once chosen) against RIR error
    (genuinely per-set). The formula term is treated as a HALF-spread, since choosing one
    formula and sticking to it removes the between-formula component and leaves only the
    question of whether the chosen one is right.
    """
    f = formula_pct / 2.0
    return (f ** 2 + rir_pct ** 2) ** 0.5


def threshold_impact(sigma: float) -> None:
    """Re-run R2's data-volume question at the implied sigma rather than the assumed one."""
    from ff_model import SaturationParams
    from fit import HISTORIES, fit, make_log, mrv, has_interior_optimum
    from ff_model import lifter_population

    sat = SaturationParams(enabled=True, ceiling=12.0)
    pop = [p for p in lifter_population(16, seed=606) if has_interior_optimum(p, sat)]

    print(f"\n3. THRESHOLD IMPACT — median MRV error vs weeks, at sigma {sigma:.1f} "
          f"(D-09 assumed 2.5)")
    print("  weeks   sigma 2.5 (assumed)   sigma %.1f (implied)" % sigma)
    print("  " + "-" * 52)
    for weeks in (12, 18, 24, 36):
        row = []
        for s in (2.5, sigma):
            errs = []
            for i, truth in enumerate(pop):
                true_mrv = mrv(truth, sat)
                log = make_log(HISTORIES["WAVED"](weeks), truth, sat, noise=s, seed=5000 + i)
                got, got_sat, _ = fit(log, restarts=2)
                errs.append(abs(mrv(got, got_sat) - true_mrv) / true_mrv * 100.0)
            row.append(statistics.median(errs))
        print(f"  {weeks:5d} {row[0]:20.1f}% {row[1]:21.1f}%")


def protocol_recovery() -> float:
    """
    The constructive half: a test protocol that buys most of the noise back.

    Both noise sources are functions of how the test set is taken, and both shrink in the
    same direction — few reps, close to failure:

      · formula disagreement explodes with reps (2.8% at 8, 11.3% at 12, 46.1% at 20),
        because the formulas are fitted to different data and only agree near 1RM.
      · RIR error enters through (reps + RIR), so a test taken at RIR 0-1 has almost no
        room to be misestimated.

    This means the TEST should be taken differently from the TRAINING, which the project
    had been quietly conflating. Training wants RIR 1-3 because that is where the
    stimulus-to-fatigue ratio is best (DESIGN.md 6). A test wants RIR 0-1 and low reps
    because it is a measurement, not a stimulus, and its only job is to be precise.
    """
    print("\n4. PROTOCOL RECOVERY — the test taken differently from the training")
    print("  protocol                     formula spread   RIR error   implied sigma")
    print("  " + "-" * 72)

    rows = [
        ("as logged today (3-12 reps, RIR 2)", (3, 5, 8, 10, 12), (3.0, 4.0, 5.0), 2.0),
        ("cap at 8 reps, RIR 2",              (3, 5, 8),          (3.0, 4.0),      2.0),
        ("cap at 8 reps, RIR 0-1",            (3, 5, 8),          (1.0, 2.0),      1.0),
        ("cap at 5 reps, RIR 0-1",            (3, 5),             (1.0, 2.0),      1.0),
    ]

    best = None
    for label, reps_set, true_rirs, reported_rir in rows:
        spreads = []
        for reps in reps_set:
            load = _load_for(reps, "epley")
            vals = [f(load, reps) for f in FORMULAS.values()]
            spreads.append(max(vals) - min(vals))
        f_pct = statistics.fmean(spreads)

        errors = []
        for reps in reps_set:
            load = _load_for(reps + reported_rir, "epley")
            reported = e1rm(load, reps, reported_rir)
            for true_rir in true_rirs:
                actual = e1rm(load, reps, true_rir)
                errors.append(abs(actual - reported) / actual * 100.0)
        r_pct = statistics.fmean(errors)

        sigma = implied_sigma(f_pct, r_pct)
        best = sigma if best is None else min(best, sigma)
        print(f"  {label:<32} {f_pct:9.1f}% {r_pct:11.1f}% {sigma:13.1f}")

    naive = implied_sigma(5.8, 4.8)
    print(f"\n  D-09 assumed 2.5, and it is achievable — but only under a protocol nobody")
    print(f"  had specified. Naive logging gives sigma {naive:.1f}; capping the test at 8 reps")
    print(f"  and RIR 0-1 gives {best:.1f}, a factor of {naive / best:.1f}, bought entirely by how the")
    print("  test set is taken rather than by any modelling.")
    return best


def main() -> None:
    print("MESO R7 — is the measurement chain as clean as D-09 assumes?")
    f = formula_spread()
    r = rir_error_cost()
    sigma = implied_sigma(f, r)
    print(f"\n  implied measurement sigma: {sigma:.1f} points "
          f"against D-09's assumed 2.5")
    threshold_impact(sigma)
    best = protocol_recovery()
    print()
    threshold_impact(best)


if __name__ == "__main__":
    main()
