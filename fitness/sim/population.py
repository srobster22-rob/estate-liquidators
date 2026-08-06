"""
MESO — population variants, and whether the project's conclusions survive them.

The question this exists to answer:

    D-16 found ~5% of synthetic lifters have no interior optimum — the model tells them
    never to train. D-19 found they are not cosmetic: they inflate the SD of log-MRV by
    56%, broke R5's estimator outright, and inflated R3's and R4's absolute figures by
    1.3-1.5x. R5 promoted "narrow or justify PRIOR_SPREAD" to the top of the ranking.

    But narrowing it is not obviously right, and picking a narrower range by hand until
    the inconvenient lifters disappear is curve-fitting the population to the result. The
    honest version of this round is bigger and cheaper: build several defensible
    populations, re-run every headline conclusion against each, and report WHICH
    CONCLUSIONS DEPEND ON THE POPULATION DEFINITION AND WHICH DO NOT.

    That is the concrete, answerable form of D-15 — the standing worry that every number
    here is calibrated on lifters the model invented.

WHERE THE DEGENERATE LIFTERS COME FROM
  A lifter is degenerate when k_fit*C(tau_fit) < k_fat*C(tau_fat): weak adaptation, strong
  fatigue, fast-decaying fitness, slow-decaying fatigue — all four unfavourable at once.
  `PRIOR_SPREAD` draws the four scales INDEPENDENTLY from uniform ranges, so it visits
  that corner at the product of four marginal probabilities. Whether real physiology
  visits it as often is exactly the open question, and independence is an assumption
  nobody in this project ever defended — it was chosen because it is easy to write.

THE FOUR VARIANTS
  BASELINE     PRIOR_SPREAD as drawn since R1. Independent uniforms.
  CLEAN        BASELINE with degenerate lifters rejected. R5's fix — post-hoc truncation,
               which is honest about the symptom and silent about the cause.
  NARROW       Ranges tightened until degeneracy is rare without rejection. The width is
               DERIVED (see `narrowing_for_target`), not chosen to look good.
  CORRELATED   Independence replaced by a positive correlation between the adaptation and
               fatigue gains — the physiologically motivated structure, on the grounds
               that a lifter who adapts strongly to a stimulus is also getting a large
               dose of it. Ranges unchanged from BASELINE; only the joint structure moves.

  No variant is claimed to be correct. The point is the spread of answers across them.
"""

from __future__ import annotations

import math
import random

from confidence import TRUE_SAT
from ff_model import FFParams, POPULATION_PRIOR, PRIOR_SPREAD
from fit import has_interior_optimum


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _build(scales: dict[str, float]) -> FFParams | None:
    k_fit = POPULATION_PRIOR.k_fit * scales["k_fit"]
    k_fat = POPULATION_PRIOR.k_fat * scales["k_fat"]
    tau_fit = POPULATION_PRIOR.tau_fit * scales["tau_fit"]
    tau_fat = POPULATION_PRIOR.tau_fat * scales["tau_fat"]
    if k_fat <= k_fit or tau_fat >= tau_fit:
        return None
    return FFParams(p0=POPULATION_PRIOR.p0, k_fit=k_fit, k_fat=k_fat,
                    tau_fit=tau_fit, tau_fat=tau_fat)


def _shrink(lo: float, hi: float, factor: float) -> tuple[float, float]:
    """Contract a range toward its midpoint by `factor` (1.0 = unchanged)."""
    mid = (lo + hi) / 2.0
    return mid - (mid - lo) * factor, mid + (hi - mid) * factor


def baseline(n: int, seed: int = 31337) -> list[FFParams]:
    rng = random.Random(seed)
    out: list[FFParams] = []
    while len(out) < n:
        p = _build({k: rng.uniform(lo, hi) for k, (lo, hi) in PRIOR_SPREAD.items()})
        if p is not None:
            out.append(p)
    return out


def clean(n: int, seed: int = 31337) -> list[FFParams]:
    rng = random.Random(seed)
    out: list[FFParams] = []
    while len(out) < n:
        p = _build({k: rng.uniform(lo, hi) for k, (lo, hi) in PRIOR_SPREAD.items()})
        if p is not None and has_interior_optimum(p, TRUE_SAT):
            out.append(p)
    return out


def narrow(n: int, seed: int = 31337, factor: float = 0.65) -> list[FFParams]:
    rng = random.Random(seed)
    ranges = {k: _shrink(lo, hi, factor) for k, (lo, hi) in PRIOR_SPREAD.items()}
    out: list[FFParams] = []
    while len(out) < n:
        p = _build({k: rng.uniform(lo, hi) for k, (lo, hi) in ranges.items()})
        if p is not None:
            out.append(p)
    return out


def correlated(n: int, seed: int = 31337, rho: float = 0.75) -> list[FFParams]:
    """
    Same marginals as BASELINE, but the two gains move together.

    Rationale, and it is a rationale rather than a measurement: `k_fit` and `k_fat` are
    both gains on the SAME training impulse. A lifter with a large adaptive response to a
    given dose is, physiologically, a lifter for whom that dose is large — and a large
    dose also fatigues. Drawing them independently permits "adapts barely, fatigues
    enormously", which is the corner the degenerate lifters live in.

    Implemented as a Gaussian copula so the marginals are exactly BASELINE's uniforms and
    ONLY the joint structure changes. That isolation matters: any difference in results
    between BASELINE and CORRELATED is attributable to dependence and to nothing else.
    """
    rng = random.Random(seed)
    out: list[FFParams] = []
    while len(out) < n:
        z1 = rng.gauss(0.0, 1.0)
        z2 = rho * z1 + math.sqrt(max(0.0, 1.0 - rho * rho)) * rng.gauss(0.0, 1.0)
        u_fit, u_fat = _normal_cdf(z1), _normal_cdf(z2)
        lo1, hi1 = PRIOR_SPREAD["k_fit"]
        lo2, hi2 = PRIOR_SPREAD["k_fat"]
        scales = {
            "k_fit": lo1 + u_fit * (hi1 - lo1),
            "k_fat": lo2 + u_fat * (hi2 - lo2),
            "tau_fit": rng.uniform(*PRIOR_SPREAD["tau_fit"]),
            "tau_fat": rng.uniform(*PRIOR_SPREAD["tau_fat"]),
        }
        p = _build(scales)
        if p is not None:
            out.append(p)
    return out


VARIANTS = {
    "BASELINE": baseline,
    "CLEAN": clean,
    "NARROW": narrow,
    "CORRELATED": correlated,
}


def degenerate_rate(builder, n: int = 400, seed: int = 909) -> float:
    pop = builder(n, seed)
    return sum(0 if has_interior_optimum(p, TRUE_SAT) else 1 for p in pop) / len(pop)


def narrowing_for_target(target: float = 0.005, n: int = 400) -> float:
    """
    Widest narrowing factor whose degenerate rate is under `target`.

    Derived rather than hand-picked, so NARROW is not a range chosen until the
    inconvenient lifters went away. Coarse by design — the point is a defensible number,
    not a precise one.
    """
    best = 0.05
    for step in range(20, 0, -1):
        factor = step / 20.0
        if degenerate_rate(lambda k, s: narrow(k, s, factor), n) <= target:
            best = factor
            break
    return best
