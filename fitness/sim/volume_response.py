"""
MESO — R1b. Does the model have a maximum recoverable volume, or does it prescribe
infinity?

The question this exists to answer:

    R1's deload sweep found that no deload policy ever beats never deloading. Before
    concluding anything about deloads, check the obvious suspect: a model in which more
    work is monotonically better cannot produce an MRV, cannot produce an MEV, and
    cannot produce a reason to ever back off. If that is what we have, the deload result
    is an artefact of the model and not a finding about training.

THE ARITHMETIC
  At steady state under a constant weekly load, the two traces converge to

    fitness -> daily_stimulus * C_fit ,  C_fit = 1 / (1 - exp(-1/tau_fit)) ~ 42.5
    fatigue -> daily_fatigue  * C_fat ,  C_fat = 1 / (1 - exp(-1/tau_fat)) ~  9.5

  so steady-state preparedness is

    p0 + daily * (k_fit * C_fit - k_fat * C_fat)

  With the prior parameters that bracket is 42.5 - 18.1 = +24.4 per unit of daily work.
  It is a CONSTANT, and it is positive. Preparedness is therefore linear and increasing
  in volume with no maximum anywhere. The slow trace always wins, because it integrates
  over 42 days while the fast one integrates over 9.

  This is not a tuning problem. No choice of k_fit, k_fat, tau_fit, tau_fat produces an
  interior optimum: the bracket is either positive (train infinitely) or negative (never
  train). A linear cost cannot balance a linear benefit into a decision.

THE CORRECTION UNDER TEST
  Saturating stimulus, linear fatigue (`SaturationParams`). Each set past the first few
  in a session deposits less adaptation than the one before, while depositing the same
  fatigue. That makes the bracket volume-dependent and therefore capable of turning
  over.

WHAT THIS SCRIPT PRINTS
  1. Steady-state preparedness against weekly sets, linear vs saturating.
  2. The derived optimum ("modelled MRV") per lifter, and its spread across a population.
  3. Whether the spread is wide enough that a fixed prescription is a bad idea — which
     is the argument for making the program probe for the lifter's own value.
"""

from __future__ import annotations

from ff_model import (
    FFParams,
    POPULATION_PRIOR,
    SaturationParams,
    lifter_population,
    steady_state,
)

SESSIONS_PER_WEEK = 3
SWEEP = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 60, 80, 120]


def optimum_weekly_sets(
    params: FFParams,
    sat: SaturationParams,
    lo: float = 0.5,
    hi: float = 200.0,
    tol: float = 0.01,
) -> tuple[float, float]:
    """Golden-section search for the volume that maximises steady-state preparedness."""
    invphi = 0.6180339887498949
    a, b = lo, hi
    c = b - invphi * (b - a)
    d = a + invphi * (b - a)
    fc = steady_state(c, params, SESSIONS_PER_WEEK, sat)
    fd = steady_state(d, params, SESSIONS_PER_WEEK, sat)
    while b - a > tol:
        if fc > fd:
            b, d, fd = d, c, fc
            c = b - invphi * (b - a)
            fc = steady_state(c, params, SESSIONS_PER_WEEK, sat)
        else:
            a, c, fc = c, d, fd
            d = a + invphi * (b - a)
            fd = steady_state(d, params, SESSIONS_PER_WEEK, sat)
    best = (a + b) / 2.0
    return best, steady_state(best, params, SESSIONS_PER_WEEK, sat)


def dose_response_table() -> None:
    linear = SaturationParams()
    sat = SaturationParams(enabled=True)
    print("Steady-state preparedness vs weekly hard sets (prior lifter, 3 sessions/wk)")
    print("  sets/wk    linear   saturating")
    print("  " + "-" * 34)
    for s in SWEEP:
        print(
            f"  {s:7d}  {steady_state(float(s), POPULATION_PRIOR, SESSIONS_PER_WEEK, linear):8.1f}"
            f"   {steady_state(float(s), POPULATION_PRIOR, SESSIONS_PER_WEEK, sat):10.1f}"
        )


def bracket_report() -> None:
    p = POPULATION_PRIOR
    import math

    c_fit = 1.0 / (1.0 - math.exp(-1.0 / p.tau_fit))
    c_fat = 1.0 / (1.0 - math.exp(-1.0 / p.tau_fat))
    print("\nThe linear bracket (prior lifter)")
    print(f"  C_fit = {c_fit:6.2f}   k_fit * C_fit = {p.k_fit * c_fit:6.2f}")
    print(f"  C_fat = {c_fat:6.2f}   k_fat * C_fat = {p.k_fat * c_fat:6.2f}")
    print(f"  net per unit of daily work = {p.k_fit * c_fit - p.k_fat * c_fat:+6.2f}"
          "   (constant, so no optimum exists)")

    negative = 0
    for lifter in lifter_population(200):
        c1 = 1.0 / (1.0 - math.exp(-1.0 / lifter.tau_fit))
        c2 = 1.0 / (1.0 - math.exp(-1.0 / lifter.tau_fat))
        if lifter.k_fit * c1 - lifter.k_fat * c2 < 0:
            negative += 1
    print(f"  lifters in a 200-population whose bracket is NEGATIVE "
          f"(model says never train): {negative}")


def mrv_spread() -> None:
    sat = SaturationParams(enabled=True)
    population = lifter_population(200)
    optima = sorted(optimum_weekly_sets(p, sat)[0] for p in population)
    n = len(optima)

    def pct(q: float) -> float:
        return optima[min(n - 1, int(q * n))]

    print("\nModelled MRV under saturating stimulus (weekly hard sets per muscle group)")
    print(f"  prior lifter          {optimum_weekly_sets(POPULATION_PRIOR, sat)[0]:6.1f}")
    print(f"  population p10        {pct(0.10):6.1f}")
    print(f"  population median     {pct(0.50):6.1f}")
    print(f"  population p90        {pct(0.90):6.1f}")
    print(f"  ratio p90/p10         {pct(0.90) / pct(0.10):6.2f}x")

    # What does a fixed prescription cost the people it does not fit?
    fixed = pct(0.50)
    losses = []
    for p in population:
        best_sets, best_prep = optimum_weekly_sets(p, sat)
        at_fixed = steady_state(fixed, p, SESSIONS_PER_WEEK, sat)
        losses.append(best_prep - at_fixed)
    losses.sort()
    print(f"\n  Cost of prescribing the population median ({fixed:.0f} sets/wk) to everyone:")
    print(f"    median lifter loses  {losses[n // 2]:5.2f} preparedness points")
    print(f"    p90 lifter loses     {losses[int(0.90 * n)]:5.2f}")
    print(f"    worst lifter loses   {losses[-1]:5.2f}")


def main() -> None:
    print("MESO R1b — does the model have an interior optimum in volume?\n")
    dose_response_table()
    bracket_report()
    mrv_spread()


if __name__ == "__main__":
    main()
