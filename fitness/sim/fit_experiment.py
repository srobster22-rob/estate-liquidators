"""
MESO — R2. Can the fit be found, and does it hold still?

Three experiments, in the order that matters:

  1. RECOVERY   Generate a lifter with known parameters, run a training history, sample
                noisy weekly performance tests, fit, and compare the recovered MRV to
                the true one. Reported per training history, because the hypothesis
                worth testing is that the plan you run determines whether you can learn
                anything from it.

  2. STABILITY  D-08, the project's named failure mode. Refit after each new week and
                measure how much the prescribed volume moves. A fit that swings more
                than ~20% week to week is tracking noise, and a stable template beats it
                regardless of which is theoretically better.

  3. NOISE      How much of whatever is left is measurement error rather than method.

WHAT IS MEASURED
  Error in the DECISION, not in the parameters. Two parameter sets can differ wildly and
  prescribe identical training; reporting parameter error as the headline is how a
  modelling project congratulates itself for nothing. Parameter error is printed
  alongside, for diagnosis only.
"""

from __future__ import annotations

import statistics

from fit import (
    DEFAULT_NOISE,
    HISTORIES,
    POPULATION_PRIOR_CEILING,
    fit,
    make_log,
    mrv,
)
from ff_model import SaturationParams, lifter_population

TRUE_SAT = SaturationParams(enabled=True, ceiling=POPULATION_PRIOR_CEILING)
N_LIFTERS = 12
WEEKS = 16


def _pct(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, int(q * len(s)))]


def recovery(free_ceiling: bool = False, noise: float = DEFAULT_NOISE) -> None:
    label = "5 parameters (ceiling free)" if free_ceiling else "4 parameters (ceiling fixed)"
    print(f"\n1. RECOVERY — {label}, noise sigma={noise}, {N_LIFTERS} lifters, {WEEKS} weeks")
    print("  history   median MRV err   p90 err   worst    median tau_fat err")
    print("  " + "-" * 68)

    population = lifter_population(N_LIFTERS, seed=77)
    for name, builder in HISTORIES.items():
        weekly = builder(WEEKS)
        mrv_errs: list[float] = []
        tau_errs: list[float] = []
        for i, truth in enumerate(population):
            true_mrv = mrv(truth, TRUE_SAT)
            log = make_log(weekly, truth, TRUE_SAT, noise=noise, seed=1000 + i)
            got, got_sat, _ = fit(log, free_ceiling=free_ceiling)
            mrv_errs.append(abs(mrv(got, got_sat) - true_mrv) / true_mrv * 100.0)
            tau_errs.append(abs(got.tau_fat - truth.tau_fat) / truth.tau_fat * 100.0)
        print(
            f"  {name:<9} {statistics.median(mrv_errs):11.1f}%  {_pct(mrv_errs, 0.9):8.1f}%"
            f" {max(mrv_errs):7.1f}%  {statistics.median(tau_errs):16.1f}%"
        )


def stability(free_ceiling: bool = False) -> None:
    label = "5 parameters" if free_ceiling else "4 parameters"
    print(f"\n2. STABILITY (D-08) — {label}: refit each week from week 8, "
          f"swing in prescribed volume")
    print("  history   median wk/wk swing   p90 swing   worst   verdict")
    print("  " + "-" * 66)

    population = lifter_population(6, seed=91)
    for name, builder in HISTORIES.items():
        weekly_full = builder(24)
        swings: list[float] = []
        for i, truth in enumerate(population):
            log_full = make_log(weekly_full, truth, TRUE_SAT, seed=2000 + i)
            prescriptions: list[float] = []
            for upto in range(8, 25):
                sub = make_log(weekly_full[:upto], truth, TRUE_SAT, seed=2000 + i)
                # Reuse the full log's noise draws so successive refits see a growing
                # prefix of ONE history rather than a freshly-noised one each week.
                # Without this the measured swing includes noise the lifter never saw.
                sub.observations = log_full.observations[:upto]
                got, got_sat, _ = fit(sub, free_ceiling=free_ceiling, restarts=2)
                prescriptions.append(mrv(got, got_sat))
            for a, b in zip(prescriptions, prescriptions[1:]):
                swings.append(abs(b - a) / max(a, 1e-6) * 100.0)
        med = statistics.median(swings)
        verdict = "usable" if med <= 20.0 else "TRACKING NOISE"
        print(
            f"  {name:<9} {med:16.1f}%  {_pct(swings, 0.9):9.1f}% {max(swings):7.1f}%"
            f"   {verdict}"
        )


def noise_sensitivity() -> None:
    print("\n3. NOISE SENSITIVITY — median MRV error vs test-retest noise (PROBE history)")
    print("  sigma   median MRV err   p90 err")
    print("  " + "-" * 40)
    population = lifter_population(8, seed=55)
    weekly = HISTORIES["PROBE"](WEEKS)
    for noise in (0.0, 1.0, 2.5, 5.0):
        errs: list[float] = []
        for i, truth in enumerate(population):
            true_mrv = mrv(truth, TRUE_SAT)
            log = make_log(weekly, truth, TRUE_SAT, noise=noise, seed=3000 + i)
            got, got_sat, _ = fit(log)
            errs.append(abs(mrv(got, got_sat) - true_mrv) / true_mrv * 100.0)
        print(f"  {noise:5.1f}   {statistics.median(errs):12.1f}%  {_pct(errs, 0.9):8.1f}%")


def null_hypothesis(n: int = 24) -> None:
    """
    The test this round exists to survive.

    A fit that never moves off its starting point is perfectly stable and perfectly
    useless, and experiment 2's low swing numbers are exactly what that would look like.
    So compare the fitter against the two constants it has to beat to justify existing:

      PRIOR    always prescribe the population prior's MRV (30.8 sets/wk)
      MEDIAN   always prescribe the population median MRV  (~25 sets/wk)

    Also report the correlation between true and fitted MRV. A fitter returning its
    prior scores near zero there no matter how good its error percentiles look.
    """
    from ff_model import POPULATION_PRIOR

    print(f"\n4. NULL HYPOTHESIS — is the fitter beating a constant? ({n} lifters)")
    population = lifter_population(n, seed=31337)
    true_mrvs = [mrv(p, TRUE_SAT) for p in population]
    prior_mrv = mrv(POPULATION_PRIOR, TRUE_SAT)
    median_mrv = statistics.median(true_mrvs)

    print("  history   method    median err   p90 err    corr(true, fitted)")
    print("  " + "-" * 62)
    for name in ("FLAT", "WAVED", "PROBE"):
        weekly = HISTORIES[name](WEEKS)
        fitted: list[float] = []
        for i, truth in enumerate(population):
            log = make_log(weekly, truth, TRUE_SAT, seed=4000 + i)
            got, got_sat, _ = fit(log)
            fitted.append(mrv(got, got_sat))

        errs = [abs(f - t) / t * 100.0 for f, t in zip(fitted, true_mrvs)]
        try:
            corr = statistics.correlation(true_mrvs, fitted)
        except statistics.StatisticsError:
            corr = float("nan")
        print(f"  {name:<9} FITTED   {statistics.median(errs):10.1f}%"
              f" {_pct(errs, 0.9):8.1f}%    {corr:16.2f}")

    for label, const in (("PRIOR", prior_mrv), ("MEDIAN", median_mrv)):
        errs = [abs(const - t) / t * 100.0 for t in true_mrvs]
        print(f"  {'—':<9} {label:<8} {statistics.median(errs):10.1f}%"
              f" {_pct(errs, 0.9):8.1f}%    {0.0:16.2f}")


def data_volume() -> None:
    """Does more logged history help, or has the fit already converged to its ceiling?"""
    print("\n5. DATA VOLUME — median MRV error vs weeks logged (PROBE, 16 lifters)")
    print("  weeks   median err   p90 err")
    print("  " + "-" * 36)
    population = lifter_population(16, seed=606)
    for weeks in (8, 16, 24, 52):
        weekly = HISTORIES["PROBE"](weeks)
        errs: list[float] = []
        for i, truth in enumerate(population):
            true_mrv = mrv(truth, TRUE_SAT)
            log = make_log(weekly, truth, TRUE_SAT, seed=5000 + i)
            got, got_sat, _ = fit(log, restarts=2)
            errs.append(abs(mrv(got, got_sat) - true_mrv) / true_mrv * 100.0)
        print(f"  {weeks:5d}   {statistics.median(errs):9.1f}%  {_pct(errs, 0.9):8.1f}%")


def main() -> None:
    print("MESO R2 — can the per-lifter fit be found, and does it hold still?")
    recovery(free_ceiling=False)
    recovery(free_ceiling=True)
    stability(free_ceiling=False)
    noise_sensitivity()
    null_hypothesis()
    data_volume()


if __name__ == "__main__":
    main()
