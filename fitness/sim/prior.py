"""
MESO — the starting prior, and what a covariate would have to be worth.

The question this exists to answer:

    R4 established that no control policy captures more than ~6 of the ~20 available
    preparedness points, and that 86% of the remaining loss belongs to lifters far from
    the population average during the weeks before anything can know they are unusual.
    The only lever left is to start closer to them.

THE TRAP THIS ROUND HAD TO AVOID
  The honest problem: MESO's synthetic lifters have no covariates. Sex, training age,
  bodyweight and recovery capacity do not exist in `PRIOR_SPREAD` — the parameters are
  drawn independently from uniform ranges. So any experiment that invents a covariate,
  wires it to the truth, and then reports how much it helps is measuring the wiring. It
  would produce a confident number about a relationship the experimenter created.

  So this module does not ask "does a covariate help". It asks the question that can be
  answered honestly:

      HOW GOOD WOULD A COVARIATE HAVE TO BE, IN CORRELATION TERMS, BEFORE IT IS WORTH
      COLLECTING?

  That is a property of the loss surface and the population spread, both of which are
  real properties of the model. The answer is a threshold a real covariate can later be
  measured against — and given D-17 (the optimum is flat, so precision is nearly
  worthless), the threshold is the interesting part.

THE COVARIATE MODEL
  A covariate with correlation `rho` against a lifter's true log-MRV, standardised:

      z = rho * y_std + sqrt(1 - rho^2) * e ,   e ~ N(0, 1)

  and the conditional expectation that follows from it:

      E[log MRV | z] = mu + rho * tau * z

  rho = 0 is no information (prescribe the constant); rho = 1 is an oracle. Everything
  a real questionnaire could achieve lies in between, and nothing here pretends to know
  where.

WHY THE BEST CONSTANT IS NOT THE AVERAGE LIFTER'S MRV
  R1 through R4 all used the prior lifter's MRV (30.8 sets/week) as the default
  prescription. It is not the loss-minimising constant, because the loss curve is
  asymmetric — overshooting costs far more than undershooting (D-17) — so the best
  constant sits below the population's central value. `best_constant` finds it.
"""

from __future__ import annotations

import math
import random
import statistics

from confidence import TRUE_SAT, preparedness_lost
from ff_model import FFParams, POPULATION_PRIOR, lifter_population
from fit import has_interior_optimum, mrv


def population_mrvs(
    n: int = 300, seed: int = 31337, drop_degenerate: bool = True
) -> tuple[list[FFParams], list[float]]:
    """
    A population and its MRVs, with degenerate lifters removed by default.

    R5 found this is not optional for anything that estimates population moments.
    Lifters with no interior optimum sit at `mrv()`'s search boundary rather than at a
    real value, and 5.3% of them inflate the SD of log-MRV by **56%** and drag its
    geometric mean down **19%**. Any shrinkage estimator built on those moments spreads
    its prescriptions wider than the real population does — which made a BETTER covariate
    produce WORSE prescriptions across the middle of the rho range. D-16, D-19.
    """
    pop = lifter_population(n, seed=seed)
    if drop_degenerate:
        pop = [p for p in pop if has_interior_optimum(p, TRUE_SAT)]
    return pop, [mrv(p, TRUE_SAT) for p in pop]


def best_constant(population: list[FFParams], lo: float = 2.0, hi: float = 60.0) -> float:
    """
    The single weekly volume minimising mean preparedness points lost across a
    population. Ternary search — the mean-loss curve is unimodal in volume because every
    lifter's own loss curve is.
    """
    for _ in range(200):
        a = lo + (hi - lo) / 3.0
        b = hi - (hi - lo) / 3.0
        fa = statistics.fmean([preparedness_lost(a, p) for p in population])
        fb = statistics.fmean([preparedness_lost(b, p) for p in population])
        if fa < fb:
            hi = b
        else:
            lo = a
    return (lo + hi) / 2.0


def log_mrv_moments(mrvs: list[float]) -> tuple[float, float]:
    logs = [math.log(v) for v in mrvs]
    return statistics.fmean(logs), statistics.stdev(logs)


def covariate_draws(mrvs: list[float], rho: float, seed: int = 0) -> list[float]:
    """
    Standardised covariate values with the requested correlation against log-MRV.

    Deterministic given the seed. Note what this is NOT: it is not a claim that any real
    measurement achieves any particular rho. It is the input to a sensitivity analysis.
    """
    mu, tau = log_mrv_moments(mrvs)
    rng = random.Random(seed)
    out: list[float] = []
    for v in mrvs:
        y_std = (math.log(v) - mu) / tau
        e = rng.gauss(0.0, 1.0)
        out.append(rho * y_std + math.sqrt(max(0.0, 1.0 - rho * rho)) * e)
    return out


def conditional_prescription(
    z: float, mu: float, tau: float, rho: float, asymmetry_factor: float = 1.0
) -> float:
    """
    Starting volume implied by a covariate reading.

    `asymmetry_factor` carries over the same correction that makes the unconditional best
    constant sit below the population's central value: the loss curve is steeper above
    MRV than below it, so the loss-minimising point is not the conditional mean. Applying
    the unconditional ratio is an approximation — it assumes the correction is
    scale-free, which holds while the conditional spread is a similar shape to the
    unconditional one, and stops holding as rho approaches 1.
    """
    return math.exp(mu + rho * tau * z) * asymmetry_factor


def asymmetry_correction(population: list[FFParams], mrvs: list[float]) -> float:
    """Ratio of the loss-minimising constant to the geometric mean MRV."""
    mu, _ = log_mrv_moments(mrvs)
    return best_constant(population) / math.exp(mu)


def degenerate_share(population: list[FFParams]) -> float:
    """Fraction of a population with no interior optimum. D-16 keeps this visible."""
    return sum(0 if has_interior_optimum(p, TRUE_SAT) else 1 for p in population) / len(population)
