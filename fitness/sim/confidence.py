"""
MESO — the confidence gate.

The question this exists to answer:

    R2's fitter is excellent for the median lifter and off by 34-1328% at the p90. The
    same machinery that helps most people would badly mislead some. Before any of this
    can be shown to a person: can the system tell, WITHOUT knowing the truth, which case
    it is in - and prescribe accordingly?

TWO JOBS, AND THE SECOND IS THE REAL ONE
  Detecting low confidence is only half of it. Detecting it and then still prescribing
  the same number is worthless. So this module also does the prescribing: it shrinks the
  fitted MRV toward the population prior in proportion to how badly identified the
  lifter is, and the experiment scores it in preparedness points lost rather than in
  percent error, because points are what a lifter actually experiences.

THE FOUR CANDIDATE SIGNALS, cheapest first
  weeks_logged        blunt, free, and D-02 now gives it a number (~24 weeks).
  volume_variation    SD of log weekly sets. D-10 says excitation is the binding
                      constraint, and unlike the others this is knowable BEFORE the
                      lifter trains - which makes it the only one that can be designed
                      for rather than merely observed.
  residual_rmse       scale of the fit's own residuals. Free, since the fit computes it.
  bootstrap_rel_sd    residual-resampling bootstrap over the fitted MRV. The principled
                      answer, ~10x the cost of the fit, and the only one that measures
                      uncertainty in the DECISION rather than a proxy for it.

THE SHRINKAGE RULE
  Empirical Bayes in log space, because MRV is a scale quantity and an additive shrink
  would push low-MRV lifters negative:

      log(prescribed) = w * log(fitted) + (1 - w) * log(prior)
      w = tau^2 / (tau^2 + s^2)

  `s` is the bootstrap SD of log(MRV) for this lifter; `tau` is the population SD of
  log(MRV), which is a known property of the prior rather than a tuning knob. When the
  fit is sharp relative to the population spread, w -> 1 and the lifter's own data wins.
  When it is mush, w -> 0 and they get the prior. Nothing to tune, which is the point:
  a gate with a hand-set threshold is a gate that was fitted to the test set.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass

from ff_model import FFParams, POPULATION_PRIOR, SaturationParams, simulate, steady_state
from fit import Log, POPULATION_PRIOR_CEILING, fit, mrv

SESSIONS_PER_WEEK = 3
TRUE_SAT = SaturationParams(enabled=True, ceiling=POPULATION_PRIOR_CEILING)


# ---------------------------------------------------------------------------
# Population spread of log MRV — the `tau` in the shrinkage rule
# ---------------------------------------------------------------------------


def population_log_mrv_spread(n: int = 300, seed: int = 202) -> tuple[float, float]:
    """
    (mean, SD) of log(MRV) across the prior population.

    This is not a free parameter. It is a property of `PRIOR_SPREAD` in ff_model, and if
    that changes this changes with it — which is correct, because the amount you should
    shrink toward a prior depends on how tight the prior is.
    """
    from ff_model import lifter_population

    logs = [math.log(mrv(p, TRUE_SAT)) for p in lifter_population(n, seed=seed)]
    return statistics.fmean(logs), statistics.stdev(logs)


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


@dataclass
class Confidence:
    weeks_logged: int
    volume_variation: float
    residual_rmse: float
    bootstrap_rel_sd: float
    fitted_mrv: float
    prescribed_mrv: float
    weight: float


def volume_variation(log: Log) -> float:
    """
    SD of log weekly sets — how much excitation the history actually contains.

    Log scale so that 10->20 sets counts the same as 20->40, which is the scale the
    saturating stimulus responds on. Weeks with zero sets are dropped rather than
    log(0)'d; a week off is a real thing a lifter does and should not crash the gate.
    """
    weekly: list[float] = []
    for start in range(0, len(log.daily_sets) - 6, 7):
        total = sum(log.daily_sets[start:start + 7])
        if total > 0:
            weekly.append(math.log(total))
    return statistics.stdev(weekly) if len(weekly) > 1 else 0.0


def residual_rmse(log: Log, params: FFParams, sat: SaturationParams) -> float:
    trace = simulate(log.daily_sets, params, saturation=sat)
    errs = [
        trace.preparedness[d] - y
        for d, y in zip(log.test_days, log.observations)
        if d < len(trace.preparedness)
    ]
    if not errs:
        return float("inf")
    return math.sqrt(sum(e * e for e in errs) / len(errs))


def bootstrap_log_mrv_sd(
    log: Log,
    params: FFParams,
    sat: SaturationParams,
    draws: int = 12,
    seed: int = 0,
) -> float:
    """
    Residual-resampling bootstrap over the fitted MRV, in log space.

    Resample the fit's own residuals with replacement, add them back to its predictions,
    refit, and look at how far the DECISION moves. This measures uncertainty in the thing
    being prescribed rather than in the parameters, which matters because the parameters
    are known to be poorly identified individually while still pinning MRV reasonably
    well (R2).
    """
    trace = simulate(log.daily_sets, params, saturation=sat)
    preds = [trace.preparedness[d] for d in log.test_days if d < len(trace.preparedness)]
    resid = [y - p for y, p in zip(log.observations, preds)]
    if len(resid) < 3:
        return float("inf")

    rng = random.Random(seed)
    logs: list[float] = []
    for _ in range(draws):
        synthetic = [p + rng.choice(resid) for p in preds]
        boot = Log(
            daily_sets=log.daily_sets,
            test_days=log.test_days[:len(synthetic)],
            observations=synthetic,
        )
        got, got_sat, _ = fit(boot, restarts=1)
        logs.append(math.log(max(mrv(got, got_sat), 1e-6)))

    return statistics.stdev(logs) if len(logs) > 1 else float("inf")


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


def prescribe(
    log: Log,
    tau: float,
    prior_log_mrv: float,
    draws: int = 12,
    seed: int = 0,
) -> Confidence:
    """Fit, measure how much to trust the fit, and shrink the prescription accordingly."""
    params, sat, _ = fit(log)
    fitted = mrv(params, sat)

    s = bootstrap_log_mrv_sd(log, params, sat, draws=draws, seed=seed)
    if not math.isfinite(s):
        w = 0.0
    else:
        w = tau * tau / (tau * tau + s * s)

    log_prescribed = w * math.log(max(fitted, 1e-6)) + (1.0 - w) * prior_log_mrv

    return Confidence(
        weeks_logged=len(log.test_days),
        volume_variation=volume_variation(log),
        residual_rmse=residual_rmse(log, params, sat),
        bootstrap_rel_sd=s,
        fitted_mrv=fitted,
        prescribed_mrv=math.exp(log_prescribed),
        weight=w,
    )


# ---------------------------------------------------------------------------
# Scoring, in the only currency that matters
# ---------------------------------------------------------------------------


def preparedness_lost(prescribed_sets: float, truth: FFParams) -> float:
    """
    Points of steady-state preparedness given up by prescribing `prescribed_sets`
    instead of this lifter's actual optimum.

    R1 established points as the project's currency: percent error in MRV is not
    something anyone experiences, and the curve is asymmetric — overshooting MRV costs
    far more than undershooting it, which a percentage hides completely.
    """
    best = steady_state(mrv(truth, TRUE_SAT), truth, SESSIONS_PER_WEEK, TRUE_SAT)
    got = steady_state(prescribed_sets, truth, SESSIONS_PER_WEEK, TRUE_SAT)
    return best - got


def spearman(xs: list[float], ys: list[float]) -> float:
    """
    Rank correlation. Used because these relationships are monotone, not linear.

    Ties get AVERAGE ranks, which is not a detail. Breaking ties by index instead
    fabricates an ordering out of nothing, so a constant signal — `weeks_logged` inside a
    single run, for instance — comes back with a real-looking correlation rather than the
    undefined it actually is. Caught by the round's own test suite while the experiment
    that would have printed the fabricated numbers was still running.
    """
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        out = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            shared = (i + j) / 2.0
            for k in range(i, j + 1):
                out[order[k]] = shared
            i = j + 1
        return out

    finite = [(x, y) for x, y in zip(xs, ys) if math.isfinite(x) and math.isfinite(y)]
    if len(finite) < 3:
        return float("nan")
    fx, fy = [a for a, _ in finite], [b for _, b in finite]
    try:
        return statistics.correlation(ranks(fx), ranks(fy))
    except statistics.StatisticsError:
        return float("nan")
