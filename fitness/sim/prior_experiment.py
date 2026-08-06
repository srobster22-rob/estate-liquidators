"""
MESO — R5. How good would a covariate have to be before it is worth collecting?

R4 left exactly one lever: start closer to the lifter. This round measures what that is
worth as a function of how informative the starting information is, WITHOUT inventing a
covariate and then congratulating itself for the invention (see the note in prior.py).

FOUR EXPERIMENTS

  1. THE FREE WIN     The best constant prescription against the one this project has
                      used since R1. No data, no covariates, no fitting — just the
                      observation that an asymmetric loss curve is not minimised at the
                      middle of the distribution.

  2. RHO SWEEP        Points lost against covariate quality. The headline: the correlation
                      a real questionnaire would need to hit before it beats simply
                      prescribing the best constant to everyone.

  3. COMPOUNDING      Does a better start ADD to what the R4 controller already captures,
                      or do they overlap? A covariate that only re-finds what 18 weeks of
                      logging would have found anyway is worth much less than its
                      standalone number suggests.

  4. BREAKING IT      Is the answer an artefact of the degenerate lifters D-16 found? Re-run
                      excluding them. If the covariate's value collapses, its apparent
                      benefit was mostly the ability to identify people the model says
                      should not train.
"""

from __future__ import annotations

import math
import statistics

from confidence import TRUE_SAT, preparedness_lost
from ff_model import POPULATION_PRIOR, lifter_population
from fit import has_interior_optimum, mrv
from prior import (
    asymmetry_correction,
    best_constant,
    conditional_prescription,
    covariate_draws,
    degenerate_share,
    log_mrv_moments,
    population_mrvs,
)
from trigger import HillClimb, points_lost_over_block, run_closed_loop

N_BIG = 300
N_LOOP = 24
BLOCK_WEEKS = 24
DEFAULT_RX = mrv(POPULATION_PRIOR, TRUE_SAT)
RHOS = (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0)


def _pct(v: list[float], q: float) -> float:
    s = sorted(v)
    return s[min(len(s) - 1, int(q * len(s)))]


def _summary(losses: list[float]) -> tuple[float, float, float]:
    return statistics.fmean(losses), _pct(losses, 0.9), max(losses)


class Gated(HillClimb):
    """R4's best controller: hold the start until the slope sign is trustworthy."""

    def __init__(self, start: float, hold_until: int = 12, **kw):
        super().__init__(start, **kw)
        self.hold_until = hold_until
        self.week = 0

    def prescribe(self, week: int) -> float:
        self.week = week
        return super().prescribe(week)

    def update(self, params, sat) -> None:
        if self.week < self.hold_until:
            return
        super().update(params, sat)


def free_win() -> None:
    pop, mrvs = population_mrvs(N_BIG)
    opt = best_constant(pop)
    print("\n1. THE FREE WIN — the best constant is not the average lifter's MRV")
    print(f"  population: {len(pop)} lifters, {degenerate_share(pop) * 100:.1f}% degenerate (D-16)")
    print(f"  median MRV                     {statistics.median(mrvs):6.1f} sets/wk")
    print(f"  geometric mean MRV             {math.exp(log_mrv_moments(mrvs)[0]):6.1f}")
    print(f"  default since R1               {DEFAULT_RX:6.1f}")
    print(f"  loss-minimising constant       {opt:6.1f}")
    print()
    print("  prescription        mean     p90    worst")
    print("  " + "-" * 44)
    for name, v in (("default (R1–R4)", DEFAULT_RX), ("optimal constant", opt)):
        m, p, w = _summary([preparedness_lost(v, p) for p in pop])
        print(f"  {name:<18} {m:7.2f} {p:7.2f} {w:8.2f}")
    print()
    print(f"  asymmetry correction (optimal / geometric mean) = {asymmetry_correction(pop, mrvs):.3f}")


def rho_sweep(include_degenerate: bool = False) -> None:
    """
    `include_degenerate=True` reproduces R5's broken first run, kept deliberately: it is
    the clearest demonstration that D-16's boundary lifters break population moments, and
    a null result nobody should have to rediscover.
    """
    pop, mrvs = population_mrvs(N_BIG, drop_degenerate=not include_degenerate)

    mu, tau = log_mrv_moments(mrvs)
    factor = asymmetry_correction(pop, mrvs)
    const = best_constant(pop)
    const_mean = statistics.fmean([preparedness_lost(const, p) for p in pop])

    label = ("CONTAMINATED by degenerate lifters — see D-19"
             if include_degenerate else "degenerate lifters excluded")
    print(f"\n2. RHO SWEEP — value of a covariate, {label} ({len(pop)} lifters)")
    print(f"  baseline: best constant {const:.1f} sets/wk, mean loss {const_mean:.2f}")
    print()
    print("   rho    mean     p90    worst   vs constant   % of oracle gap closed")
    print("  " + "-" * 68)
    for rho in RHOS:
        z = covariate_draws(mrvs, rho, seed=4242)
        losses = [
            preparedness_lost(conditional_prescription(zi, mu, tau, rho, factor), p)
            for zi, p in zip(z, pop)
        ]
        m, p90, worst = _summary(losses)
        closed = (const_mean - m) / const_mean * 100.0
        print(f"  {rho:4.2f} {m:7.2f} {p90:7.2f} {worst:8.2f} {m - const_mean:+12.2f}"
              f" {closed:20.0f}%")


def compounding() -> None:
    """Does a better start add to what the controller already finds, or overlap with it?"""
    pop_big, mrvs_big = population_mrvs(N_BIG)   # clean moments — D-19
    mu, tau = log_mrv_moments(mrvs_big)
    factor = asymmetry_correction(pop_big, mrvs_big)
    const = best_constant(pop_big)

    pop = [p for p in lifter_population(N_LOOP, seed=31337)
           if has_interior_optimum(p, TRUE_SAT)]
    mrvs = [mrv(p, TRUE_SAT) for p in pop]

    print(f"\n3. COMPOUNDING — covariate start + R4's controller, {BLOCK_WEEKS}-week block")
    print(f"  ({N_LOOP} lifters, paired. 'start only' holds the starting volume all block.)")
    print()
    print("   rho    start only   + controller   controller's extra")
    print("  " + "-" * 58)
    for rho in (0.0, 0.3, 0.5, 0.7, 0.9):
        z = covariate_draws(mrvs, rho, seed=4242)
        starts = [
            const if rho == 0.0 else conditional_prescription(zi, mu, tau, rho, factor)
            for zi in z
        ]
        static = [preparedness_lost(s, p) for s, p in zip(starts, pop)]
        looped = []
        for i, (s, truth) in enumerate(zip(starts, pop)):
            pres, _ = run_closed_loop(
                truth, BLOCK_WEEKS, Gated(s, 12, dither=0.10), seed=9000 + i
            )
            looped.append(points_lost_over_block(pres, truth))
        a, b = statistics.fmean(static), statistics.fmean(looped)
        print(f"  {rho:4.2f} {a:12.2f} {b:14.2f} {a - b:+19.2f}")


def main() -> None:
    print("MESO R5 — the starting prior, and what a covariate would have to be worth")
    free_win()
    rho_sweep()
    rho_sweep(include_degenerate=True)
    compounding()


if __name__ == "__main__":
    main()
