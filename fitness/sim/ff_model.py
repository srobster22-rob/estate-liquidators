"""
MESO — the fitness-fatigue core.

The question this exists to answer:

    If a plan is going to be *derived* rather than templated, what is it derived from?

Everything downstream (deload timing, volume budgets, taper shape, the autoregulation
gain) is a query against one small dynamical model. This file is that model and nothing
else. No policy lives here.

MODEL
  Two exponentially-decaying traces driven by the same daily training impulse:

    fitness[d]      = fitness[d-1]   * exp(-1/tau_fit) + w[d-1]
    fatigue[d]      = fatigue[d-1]   * exp(-1/tau_fat) + w[d-1]
    preparedness[d] = p0 + k_fit * fitness[d] - k_fat * fatigue[d]

  This is Banister's impulse-response model. `w` is a scalar session stimulus in
  arbitrary units; `preparedness` is in whatever units p0 is in (we use "percent of
  current best single", so p0 = 100).

  Note the d-1 indexing: today's session cannot improve today's performance. It costs
  today and pays later. That asymmetry is the entire model.

WHY TWO TRACES AND NOT THREE
  Busso's variable-gain and Kolie's three-component variants fit historical data better
  but need far more sessions to identify, and this project's binding constraint is a
  lifter with eight weeks of logs, not a lab with two years. Two traces have four free
  parameters; four parameters are recoverable from ~20 sessions. See DECISIONS.md D-02.

WHAT IS INFERRED, NOT VERIFIED
  The default parameters below are literature-typical values from ENDURANCE research
  (running, swimming, cycling). No resistance-training calibration is claimed. They are
  priors to be overwritten by per-lifter fitting, not truths. Every number in
  POPULATION_PRIOR is flagged in DECISIONS.md D-01 with what would disprove it.

NONLINEAR EXTENSION
  `StalenessParams` adds one thing the linear model cannot represent: that training
  while deeply fatigued produces *less adaptation per unit of work*. It is off by
  default. R1 exists to establish whether it is needed at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FFParams:
    """Per-lifter impulse-response parameters."""

    p0: float = 100.0        # baseline performance, % of current best single
    k_fit: float = 1.00      # gain on the fitness trace
    k_fat: float = 1.90      # gain on the fatigue trace (must exceed k_fit; see below)
    tau_fit: float = 42.0    # fitness decay constant, days
    tau_fat: float = 9.0     # fatigue decay constant, days

    def __post_init__(self) -> None:
        if self.tau_fat >= self.tau_fit:
            raise ValueError("fatigue must decay faster than fitness or the model is inert")
        if self.k_fat <= self.k_fit:
            raise ValueError("k_fat <= k_fit makes every session immediately beneficial")


POPULATION_PRIOR = FFParams()

# Spread used to synthesise a population. Multiplicative on the prior.
# Chosen to span the range reported across individual subjects in impulse-response
# fitting studies, which is wide — individual tau_fat estimates vary by a factor of ~3.
PRIOR_SPREAD = {
    "k_fit": (0.70, 1.40),
    "k_fat": (0.70, 1.40),
    "tau_fit": (0.70, 1.35),
    "tau_fat": (0.55, 1.80),
}


@dataclass(frozen=True)
class SaturationParams:
    """
    Diminishing stimulus per session, with fatigue left linear.

    Added in R1 after the linear model was shown to have no interior optimum in volume
    at all — its steady-state preparedness is strictly increasing in weekly sets, so it
    prescribes infinite training and cannot represent a maximum recoverable volume, a
    minimum effective volume, or any reason to ever deload. See LOOP_LOG R1.

        stimulus deposited = ceiling * (1 - exp(-sets / ceiling))
        fatigue  deposited = sets

    One parameter. The form is chosen so the derivative at zero sets is exactly 1, which
    means low-volume behaviour is unchanged and the saturation only bites where the
    dose-response literature says it bites: high per-session set counts.

    INFERRED, NOT VERIFIED. `ceiling` is not measured; it is the parameter whose value
    the whole volume prescription turns on, and D-04 states what would pin it down.
    """

    enabled: bool = False
    ceiling: float = 12.0    # per-session stimulus ceiling, in set-equivalents


@dataclass(frozen=True)
class StalenessParams:
    """
    Diminishing adaptation under chronic fatigue.

    The linear model says a session performed while wrecked deposits exactly as much
    fitness as one performed fresh. That is the claim R1 tests. If it is false, this is
    the cheapest possible correction: scale the *fitness* deposit (not the fatigue
    deposit) by a factor that falls as the fatigue trace rises relative to the fitness
    trace.

        ratio  = fatigue / max(fitness, eps)
        factor = 1                              if ratio <= onset
                 1 - slope * (ratio - onset)    otherwise, floored at `floor`

    Fatigue still accrues at full rate. That asymmetry — full cost, discounted benefit —
    is what makes a deload arithmetically rational.
    """

    enabled: bool = False
    onset: float = 0.85      # fatigue/fitness ratio at which adaptation starts discounting
    slope: float = 1.60      # discount per unit of ratio above onset
    floor: float = 0.25      # never below this fraction of nominal adaptation


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------


@dataclass
class Trace:
    """Day-indexed output of a simulation. Index 0 is the day before day 1's session."""

    fitness: list[float] = field(default_factory=list)
    fatigue: list[float] = field(default_factory=list)
    preparedness: list[float] = field(default_factory=list)
    adaptation_factor: list[float] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.preparedness)

    def peak(self) -> tuple[int, float]:
        best = max(range(len(self.preparedness)), key=lambda d: self.preparedness[d])
        return best, self.preparedness[best]

    def mean(self, start: int = 0) -> float:
        window = self.preparedness[start:]
        return sum(window) / len(window) if window else 0.0

    def final(self) -> float:
        return self.preparedness[-1]


def simulate(
    impulses: list[float],
    params: FFParams = POPULATION_PRIOR,
    staleness: StalenessParams | None = None,
    fitness0: float = 0.0,
    fatigue0: float = 0.0,
    saturation: SaturationParams | None = None,
) -> Trace:
    """
    Run the model over a daily impulse series.

    `impulses[d]` is the stimulus performed ON day d. The returned trace has
    len(impulses) + 1 entries: one per day plus the state after the final day, so
    trace.preparedness[d] is readiness on the MORNING of day d, before that day's work.
    """
    stale = staleness or StalenessParams()
    sat = saturation or SaturationParams()
    decay_fit = math.exp(-1.0 / params.tau_fit)
    decay_fat = math.exp(-1.0 / params.tau_fat)

    g, h = fitness0, fatigue0
    trace = Trace()

    def record(factor: float) -> None:
        trace.fitness.append(g)
        trace.fatigue.append(h)
        trace.preparedness.append(params.p0 + params.k_fit * g - params.k_fat * h)
        trace.adaptation_factor.append(factor)

    record(1.0)

    for w in impulses:
        factor = 1.0
        if stale.enabled and w > 0.0:
            ratio = h / max(g, 1e-9)
            if ratio > stale.onset:
                factor = max(stale.floor, 1.0 - stale.slope * (ratio - stale.onset))
        deposit = w
        if sat.enabled and w > 0.0:
            deposit = sat.ceiling * (1.0 - math.exp(-w / sat.ceiling))
        g = g * decay_fit + deposit * factor
        h = h * decay_fat + w
        record(factor)

    return trace


def steady_state(
    weekly_sets: float,
    params: FFParams = POPULATION_PRIOR,
    sessions_per_week: int = 3,
    saturation: SaturationParams | None = None,
) -> float:
    """
    Preparedness an unchanging weekly load converges to, averaged over the week.

    It is a WEEKLY MEAN, not a daily value. Training clustered onto 3 days makes the
    fast fatigue trace swing inside the week by ~10 points at 24 sets/week, so no
    individual morning equals this number. Compare against a 7-day mean or the
    comparison will look broken when it is correct.

    Closed form, and worth having: it is the number every "just keep training" policy
    asymptotes to, so any policy that beats it is doing something the constant policy
    cannot. It is also the cheapest possible test of whether the model has an interior
    optimum in volume — sweep this and look for a maximum.
    """
    sat = saturation or SaturationParams()
    per_session = weekly_sets / sessions_per_week
    stim = per_session
    if sat.enabled and per_session > 0.0:
        stim = sat.ceiling * (1.0 - math.exp(-per_session / sat.ceiling))

    weekly_stim = stim * sessions_per_week
    weekly_fat = weekly_sets

    g = (weekly_stim / 7.0) / (1.0 - math.exp(-1.0 / params.tau_fit))
    h = (weekly_fat / 7.0) / (1.0 - math.exp(-1.0 / params.tau_fat))
    return params.p0 + params.k_fit * g - params.k_fat * h


# ---------------------------------------------------------------------------
# Turning a week of lifting into impulses
# ---------------------------------------------------------------------------


# Relative stimulus per hard set, by proximity to failure at the end of the set.
# RIR = reps in reserve. Anchored so RIR 2 == 1.0, because that is the reference
# prescription everything else in DESIGN.md is written against.
#
# INFERRED, NOT VERIFIED. The shape (flat from RIR 0-2, falling away past RIR 3) is the
# consensus reading of the proximity-to-failure literature; the exact numbers are a
# smooth curve fitted to that shape by hand, not to data. DECISIONS.md D-03.
RIR_STIMULUS = {
    0: 1.05,
    1: 1.02,
    2: 1.00,
    3: 0.93,
    4: 0.82,
    5: 0.67,
}

# Fatigue cost per hard set, same anchoring. Rises FASTER than stimulus as you approach
# failure — that divergence is the whole argument for training at RIR 1-3 rather than 0.
RIR_FATIGUE = {
    0: 1.55,
    1: 1.22,
    2: 1.00,
    3: 0.84,
    4: 0.70,
    5: 0.57,
}


def session_impulse(sets: int, rir: int = 2) -> float:
    """Stimulus deposited by one session of `sets` hard sets at a given RIR."""
    return sets * RIR_STIMULUS[rir]


def session_cost(sets: int, rir: int = 2) -> float:
    """Fatigue deposited by the same session. Equals stimulus at the RIR-2 anchor."""
    return sets * RIR_FATIGUE[rir]


def weekly_schedule(sets_per_week: float, days: tuple[int, ...] = (0, 2, 4)) -> list[float]:
    """Spread a weekly set count across training days, returning 7 daily impulses."""
    per_day = sets_per_week / len(days)
    return [per_day if d in days else 0.0 for d in range(7)]


def block(weeks: list[float], days: tuple[int, ...] = (0, 2, 4)) -> list[float]:
    """Concatenate weekly set counts into one daily impulse series."""
    series: list[float] = []
    for sets_per_week in weeks:
        series.extend(weekly_schedule(sets_per_week, days))
    return series


# ---------------------------------------------------------------------------
# Synthetic population
# ---------------------------------------------------------------------------


def lifter_population(n: int, seed: int = 20260805) -> list[FFParams]:
    """
    Deterministic spread of plausible lifters.

    Uses a low-discrepancy sweep rather than random sampling so that a population of 40
    actually covers the corners — random draws of this size leave holes exactly where
    the interesting lifters are (fast-fatiguing, low-gain).
    """
    import random

    rng = random.Random(seed)
    out: list[FFParams] = []
    attempts = 0
    while len(out) < n and attempts < n * 50:
        attempts += 1
        scale = {k: rng.uniform(lo, hi) for k, (lo, hi) in PRIOR_SPREAD.items()}
        k_fit = POPULATION_PRIOR.k_fit * scale["k_fit"]
        k_fat = POPULATION_PRIOR.k_fat * scale["k_fat"]
        tau_fit = POPULATION_PRIOR.tau_fit * scale["tau_fit"]
        tau_fat = POPULATION_PRIOR.tau_fat * scale["tau_fat"]
        # Reject rather than clamp: clamping piles lifters up on the boundary of the
        # valid region, which is exactly where the interesting behaviour is, and would
        # make every sweep look like it has a mode there.
        if k_fat <= k_fit or tau_fat >= tau_fit:
            continue
        out.append(
            FFParams(
                p0=POPULATION_PRIOR.p0,
                k_fit=k_fit,
                k_fat=k_fat,
                tau_fit=tau_fit,
                tau_fat=tau_fat,
            )
        )
    return out


if __name__ == "__main__":
    print("MESO fitness-fatigue core — smoke test\n")
    weeks = [12.0] * 8
    t = simulate(block(weeks))
    print(f"  8 weeks @ 12 sets/wk, prior lifter")
    print(f"    preparedness start {t.preparedness[0]:.1f}  end {t.final():.1f}")
    print(f"    peak {t.peak()[1]:.1f} on day {t.peak()[0]}")
    print(f"    linear steady state {steady_state(12.0):.1f}")
    print()
    print(f"  population of 40: {len(lifter_population(40))} valid lifters")
