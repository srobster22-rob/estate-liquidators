"""
MESO — R6. Which of this project's conclusions depend on the population definition?

Every number in five rounds rests on `PRIOR_SPREAD`: four scale factors drawn
INDEPENDENTLY from uniform ranges, chosen in R1 because it was easy to write and never
defended since. D-15 has flagged the risk from the start. R5 showed it biting — a 5%
contamination silently broke an estimator and inflated two rounds of figures.

So rather than narrow the population until the awkward lifters vanish, this round
re-derives every headline conclusion under four defensible populations and reports the
spread. A conclusion that holds across all four is a conclusion about training. One that
moves is a conclusion about `PRIOR_SPREAD`.

WHAT IS RE-DERIVED
  1. Degeneracy rate and MRV spread — the descriptive facts D-16 and D-19 turn on.
  2. The cost of not personalising — R1's founding argument.
  3. The rho threshold — R5's answer, and the one most likely to move, since a tighter
     population makes any covariate worth less.
  4. The controller's value — R4's result, and whether control still substitutes for
     starting information (D-21) regardless of population.

WHAT WOULD MAKE THIS ROUND A FAILURE
  Finding that everything moves. That would mean five rounds of conclusions are
  properties of an arbitrary choice made in R1, and the correct response would be to stop
  simulating and go get data.
"""

from __future__ import annotations

import math
import statistics

from confidence import TRUE_SAT, preparedness_lost
from fit import has_interior_optimum, mrv
from population import VARIANTS, narrowing_for_target
from prior import (
    asymmetry_correction,
    best_constant,
    conditional_prescription,
    covariate_draws,
    log_mrv_moments,
)
from trigger import points_lost_over_block, run_closed_loop
from prior_experiment import Gated

N_BIG = 300
N_LOOP = 20
BLOCK_WEEKS = 24


def _pct(v: list[float], q: float) -> float:
    s = sorted(v)
    return s[min(len(s) - 1, int(q * len(s)))]


def descriptive() -> None:
    print("\n1. DESCRIPTIVE — what each population actually contains")
    print("  variant       degenerate   p10 MRV   median   p90 MRV   spread   SD log-MRV")
    print("  " + "-" * 78)
    for name, build in VARIANTS.items():
        pop = build(N_BIG)
        mrvs = sorted(mrv(p, TRUE_SAT) for p in pop)
        deg = sum(0 if has_interior_optimum(p, TRUE_SAT) else 1 for p in pop) / len(pop)
        clean_mrvs = [mrv(p, TRUE_SAT) for p in pop if has_interior_optimum(p, TRUE_SAT)]
        _, tau = log_mrv_moments(clean_mrvs)
        p10, p90 = _pct(mrvs, 0.10), _pct(mrvs, 0.90)
        print(f"  {name:<12} {deg * 100:9.1f}% {p10:9.1f} {statistics.median(mrvs):8.1f}"
              f" {p90:9.1f} {p90 / max(p10, 1e-9):8.2f}x {tau:11.3f}")


def cost_of_not_personalising() -> None:
    print("\n2. R1'S FOUNDING ARGUMENT — points lost by prescribing one number to everyone")
    print("  variant       best constant   mean loss   p90 loss   worst")
    print("  " + "-" * 62)
    for name, build in VARIANTS.items():
        pop = [p for p in build(N_BIG) if has_interior_optimum(p, TRUE_SAT)]
        const = best_constant(pop)
        losses = [preparedness_lost(const, p) for p in pop]
        print(f"  {name:<12} {const:13.1f} {statistics.fmean(losses):11.2f}"
              f" {_pct(losses, 0.9):10.2f} {max(losses):8.2f}")


def rho_threshold() -> None:
    print("\n3. R5'S ANSWER — % of the oracle gap a covariate closes, by population")
    print("  variant       rho 0.3   rho 0.5   rho 0.7   rho 0.9")
    print("  " + "-" * 54)
    for name, build in VARIANTS.items():
        pop = [p for p in build(N_BIG) if has_interior_optimum(p, TRUE_SAT)]
        mrvs = [mrv(p, TRUE_SAT) for p in pop]
        mu, tau = log_mrv_moments(mrvs)
        factor = asymmetry_correction(pop, mrvs)
        const = best_constant(pop)
        base = statistics.fmean([preparedness_lost(const, p) for p in pop])
        cells = []
        for rho in (0.3, 0.5, 0.7, 0.9):
            z = covariate_draws(mrvs, rho, seed=4242)
            m = statistics.fmean([
                preparedness_lost(conditional_prescription(zi, mu, tau, rho, factor), p)
                for zi, p in zip(z, pop)
            ])
            cells.append((base - m) / base * 100.0)
        print(f"  {name:<12}" + "".join(f"{c:9.0f}%" for c in cells))


def controller_value() -> None:
    print(f"\n4. R4'S RESULT — controller value, and does it still substitute? ({N_LOOP} lifters)")
    print("  variant       constant only   + controller   controller adds   at rho 0.7")
    print("  " + "-" * 74)
    for name, build in VARIANTS.items():
        big = [p for p in build(N_BIG) if has_interior_optimum(p, TRUE_SAT)]
        big_mrvs = [mrv(p, TRUE_SAT) for p in big]
        mu, tau = log_mrv_moments(big_mrvs)
        factor = asymmetry_correction(big, big_mrvs)
        const = best_constant(big)

        pop = [p for p in build(N_LOOP, seed=777) if has_interior_optimum(p, TRUE_SAT)]
        mrvs = [mrv(p, TRUE_SAT) for p in pop]

        static = statistics.fmean([preparedness_lost(const, p) for p in pop])
        looped = statistics.fmean([
            points_lost_over_block(
                run_closed_loop(t, BLOCK_WEEKS, Gated(const, 12, dither=0.10), seed=9000 + i)[0],
                t,
            )
            for i, t in enumerate(pop)
        ])

        z = covariate_draws(mrvs, 0.7, seed=4242)
        starts = [conditional_prescription(zi, mu, tau, 0.7, factor) for zi in z]
        cov_static = statistics.fmean([preparedness_lost(s, p) for s, p in zip(starts, pop)])
        cov_looped = statistics.fmean([
            points_lost_over_block(
                run_closed_loop(t, BLOCK_WEEKS, Gated(s, 12, dither=0.10), seed=9000 + i)[0],
                t,
            )
            for i, (s, t) in enumerate(zip(starts, pop))
        ])

        print(f"  {name:<12} {static:13.2f} {looped:14.2f} {static - looped:16.2f}"
              f" {cov_static - cov_looped:12.2f}")


def main() -> None:
    print("MESO R6 — which conclusions depend on the population definition?")
    print(f"  NARROW's derived narrowing factor: {narrowing_for_target():.2f}")
    descriptive()
    cost_of_not_personalising()
    rho_threshold()
    controller_value()


if __name__ == "__main__":
    main()
