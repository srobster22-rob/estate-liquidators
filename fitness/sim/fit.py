"""
MESO — the per-lifter fitter.

The question this exists to answer:

    R1 established that not knowing which lifter you are costs 2-4x more than every
    programming decision combined (DESIGN.md 4). So: can you actually find out, from the
    kind of data a real person produces?

    And the sharper version, D-08: even if the parameters are recoverable, are they
    STABLE? If re-fitting after each new week swings the prescribed volume by more than
    ~20%, the fit is tracking noise, and a stable template beats a jittery
    personalisation regardless of which is theoretically better. That is the single most
    likely way this project fails, so it gets measured before anything is built on top.

WHAT IS FITTED
  Four free parameters (D-02): k_fit, k_fat, tau_fit, tau_fat. p0 is fixed at 100 by
  construction - measurements are expressed as a percentage of a baseline test, so the
  baseline is a definition rather than an unknown. Optionally a fifth, the saturation
  ceiling, which D-04 flags as the parameter the whole volume prescription turns on.

  Constraints are enforced by reparameterisation rather than penalties, so the optimiser
  never has to be told about them:

    k_fit   = exp(a)
    k_fat   = k_fit * (1 + exp(b))        guarantees k_fat > k_fit
    tau_fit = exp(c)
    tau_fat = tau_fit * sigmoid(d)        guarantees 0 < tau_fat < tau_fit
    ceiling = exp(e)

WHAT IS MEASURED
  Not parameter error. Parameter error is the wrong metric and using it is how modelling
  projects fool themselves: two parameter sets can differ wildly and prescribe the same
  training. What matters is the error in the DECISION - the recovered MRV - so that is
  the headline number, with parameter error reported alongside for diagnosis.

MEASUREMENT MODEL
  One performance test per week (a top set taken to a known RIR, converted to an
  estimated 1RM, expressed as a percentage of baseline), corrupted by Gaussian noise.
  Default sigma = 2.5 points, i.e. a 2.5% coefficient of variation, which is the rough
  test-retest variability of an estimated 1RM. INFERRED, D-09.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from ff_model import (
    FFParams,
    POPULATION_PRIOR,
    SaturationParams,
    lifter_population,
    simulate,
    weekly_schedule,
)

TRAINING_DAYS = (0, 2, 4)
TEST_DAY = 0                # performance test on the first training day of each week
DEFAULT_NOISE = 2.5         # points of preparedness, ~2.5% CV on an e1RM


# ---------------------------------------------------------------------------
# Reparameterisation
# ---------------------------------------------------------------------------


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def unpack(x: list[float]) -> tuple[FFParams, SaturationParams]:
    """Unconstrained vector -> valid parameters. Never raises."""
    k_fit = math.exp(max(-20.0, min(5.0, x[0])))
    k_fat = k_fit * (1.0 + math.exp(max(-20.0, min(5.0, x[1]))))
    tau_fit = math.exp(max(-2.0, min(7.0, x[2])))
    tau_fat = tau_fit * _sigmoid(x[3])
    tau_fat = max(1e-3, min(tau_fat, tau_fit * (1.0 - 1e-9)))
    ceiling = math.exp(max(-2.0, min(7.0, x[4]))) if len(x) > 4 else POPULATION_PRIOR_CEILING
    return (
        FFParams(p0=100.0, k_fit=k_fit, k_fat=k_fat, tau_fit=tau_fit, tau_fat=tau_fat),
        SaturationParams(enabled=True, ceiling=ceiling),
    )


POPULATION_PRIOR_CEILING = 12.0


def pack(params: FFParams, ceiling: float | None = None) -> list[float]:
    """Valid parameters -> unconstrained vector. Inverse of `unpack`."""
    a = math.log(params.k_fit)
    b = math.log(params.k_fat / params.k_fit - 1.0)
    c = math.log(params.tau_fit)
    ratio = params.tau_fat / params.tau_fit
    d = math.log(ratio / (1.0 - ratio))
    x = [a, b, c, d]
    if ceiling is not None:
        x.append(math.log(ceiling))
    return x


# ---------------------------------------------------------------------------
# Nelder-Mead, pure stdlib
# ---------------------------------------------------------------------------


def nelder_mead(
    f,
    x0: list[float],
    step: float = 0.35,
    max_iter: int = 4000,
    tol: float = 1e-9,
) -> tuple[list[float], float]:
    n = len(x0)
    simplex = [list(x0)]
    for i in range(n):
        p = list(x0)
        p[i] += step
        simplex.append(p)
    scores = [f(p) for p in simplex]

    for _ in range(max_iter):
        order = sorted(range(n + 1), key=lambda i: scores[i])
        simplex = [simplex[i] for i in order]
        scores = [scores[i] for i in order]
        if abs(scores[-1] - scores[0]) <= tol * (abs(scores[0]) + abs(scores[-1]) + 1e-12):
            break

        centroid = [sum(p[i] for p in simplex[:-1]) / n for i in range(n)]

        def combine(t: float) -> list[float]:
            return [centroid[i] + t * (simplex[-1][i] - centroid[i]) for i in range(n)]

        xr = combine(-1.0)
        fr = f(xr)
        if fr < scores[0]:
            xe = combine(-2.0)
            fe = f(xe)
            simplex[-1], scores[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < scores[-2]:
            simplex[-1], scores[-1] = xr, fr
        else:
            xc = combine(0.5)
            fc = f(xc)
            if fc < scores[-1]:
                simplex[-1], scores[-1] = xc, fc
            else:
                best = simplex[0]
                for i in range(1, n + 1):
                    simplex[i] = [best[j] + 0.5 * (simplex[i][j] - best[j]) for j in range(n)]
                    scores[i] = f(simplex[i])

    best = min(range(n + 1), key=lambda i: scores[i])
    return simplex[best], scores[best]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class Log:
    """What a lifter's history looks like to the fitter."""

    daily_sets: list[float]
    test_days: list[int]
    observations: list[float]


def make_log(
    weekly_sets: list[float],
    params: FFParams,
    sat: SaturationParams,
    noise: float = DEFAULT_NOISE,
    seed: int = 0,
) -> Log:
    daily: list[float] = []
    for s in weekly_sets:
        daily.extend(weekly_schedule(s, TRAINING_DAYS))
    truth = simulate(daily, params, saturation=sat)
    rng = random.Random(seed)
    test_days = [w * 7 + TEST_DAY for w in range(len(weekly_sets))]
    obs = [truth.preparedness[d] + rng.gauss(0.0, noise) for d in test_days]
    return Log(daily_sets=daily, test_days=test_days, observations=obs)


def fit(log: Log, free_ceiling: bool = False, restarts: int = 4) -> tuple[FFParams, SaturationParams, float]:
    """Least-squares fit. Multi-start, because Nelder-Mead on 4-5 dims has local minima."""

    def loss(x: list[float]) -> float:
        params, sat = unpack(x)
        try:
            trace = simulate(log.daily_sets, params, saturation=sat)
        except ValueError:
            return 1e18
        err = 0.0
        for d, y in zip(log.test_days, log.observations):
            if d < len(trace.preparedness):
                err += (trace.preparedness[d] - y) ** 2
        return err

    seeds = [pack(POPULATION_PRIOR, POPULATION_PRIOR_CEILING if free_ceiling else None)]
    rng = random.Random(4242)
    for _ in range(restarts - 1):
        base = list(seeds[0])
        seeds.append([v + rng.gauss(0.0, 0.6) for v in base])

    best_x, best_score = None, math.inf
    for s in seeds:
        x, score = nelder_mead(loss, s)
        if score < best_score:
            best_x, best_score = x, score

    params, sat = unpack(best_x)
    return params, sat, best_score


# ---------------------------------------------------------------------------
# The decision the fit is for
# ---------------------------------------------------------------------------


MRV_SEARCH_LO = 0.5
MRV_SEARCH_HI = 200.0


def has_interior_optimum(params: FFParams, sat: SaturationParams, sessions: int = 3) -> bool:
    """
    Does this lifter have a real MRV, or does `mrv()` return a search boundary?

    R1 established that a lifter whose linear bracket `k_fit*C_fit - k_fat*C_fat` is
    negative is told by the model never to train at all. Saturation does not rescue them:
    it only bends the curve down further. For those lifters `mrv()` returns
    MRV_SEARCH_LO, which is a property of the search interval and not a prescription.

    Added in R4 after a test noticed the derivative had the wrong sign at half of one
    lifter's "MRV". Those lifters had been silently inside every population since R1,
    inflating the reported population spread — see DECISIONS.md D-16.
    """
    return mrv(params, sat, sessions) > MRV_SEARCH_LO * 2.0


def mrv(params: FFParams, sat: SaturationParams, sessions: int = 3) -> float:
    """
    Weekly sets maximising steady-state preparedness. The only output that matters.

    Returns MRV_SEARCH_LO for lifters with no interior optimum — check
    `has_interior_optimum` before treating the result as a prescription.
    """
    from ff_model import steady_state

    invphi = 0.6180339887498949
    a, b = MRV_SEARCH_LO, MRV_SEARCH_HI
    c, d = b - invphi * (b - a), a + invphi * (b - a)
    fc = steady_state(c, params, sessions, sat)
    fd = steady_state(d, params, sessions, sat)
    while b - a > 0.01:
        if fc > fd:
            b, d, fd = d, c, fc
            c = b - invphi * (b - a)
            fc = steady_state(c, params, sessions, sat)
        else:
            a, c, fc = c, d, fd
            d = a + invphi * (b - a)
            fd = steady_state(d, params, sessions, sat)
    return (a + b) / 2.0


# ---------------------------------------------------------------------------
# Training histories, which turn out to be the whole story
# ---------------------------------------------------------------------------


def history_flat(weeks: int = 16) -> list[float]:
    """What most people actually do: the same thing every week."""
    return [18.0] * weeks


def history_waved(weeks: int = 16) -> list[float]:
    """A normal mesocycle: ramp, deload, repeat."""
    out: list[float] = []
    while len(out) < weeks:
        for s in (12.0, 15.0, 18.0, 21.0, 24.0):
            out.append(s)
            if len(out) == weeks:
                return out
        out.append(9.0)
    return out[:weeks]


def history_probe(weeks: int = 16) -> list[float]:
    """
    Deliberately informative: alternating blocks of low and high volume, chosen to move
    the two traces against each other rather than in step.
    """
    out: list[float] = []
    pattern = [8.0, 8.0, 30.0, 30.0, 14.0, 36.0, 10.0, 26.0]
    while len(out) < weeks:
        out.extend(pattern)
    return out[:weeks]


HISTORIES = {
    "FLAT": history_flat,
    "WAVED": history_waved,
    "PROBE": history_probe,
}
