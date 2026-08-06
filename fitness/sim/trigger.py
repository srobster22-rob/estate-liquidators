"""
MESO — the dose-derivative trigger, and the controller built on it.

The question this exists to answer:

    D-07, open since R1: every trigger this project has tried reads "am I getting worse",
    which is a lagging indicator with lag on the order of tau_fit (~42 days). R1's fired
    spuriously in week 3 and then missed a 46% overshoot of MRV entirely. A working
    trigger has to watch the derivative of response with respect to DOSE, not the level
    of the output.

    And the reason it is worth a round now rather than at any earlier point: R3
    established the fitter cannot be trusted for 18 weeks. But finding WHERE a peak is
    (an argmax) is a strictly harder estimation problem than finding WHICH WAY IS UPHILL
    (a sign). If the sign is reliable early, a hill-climbing controller fills exactly the
    gap R3 opened — and the lifter converges on their own MRV without anyone ever having
    estimated it.

WHY A CONTROLLER AND NOT A TRIGGER
  "Trigger" was always the wrong noun. A trigger fires once and inserts a deload. What
  the problem actually wants is a closed loop: prescribe, observe, re-estimate the local
  slope, step. The deload falls out of it — stepping down IS the deload — which is also
  consistent with D-06, where cadence turned out to be worth under a point and only
  overshooting MRV mattered.

THE CLOSED LOOP MATTERS
  The controller changes the plan, the plan changes the log, and the log changes the fit.
  That feedback is not a complication to be simulated away: hill climbing *creates volume
  variation as a side effect*, and D-10 says variation is the excitation that makes a
  lifter identifiable at all. A controller that moves is a controller that learns faster
  than one that sits still, which is a property no open-loop analysis can see.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ff_model import FFParams, POPULATION_PRIOR, SaturationParams, steady_state
from fit import Log, POPULATION_PRIOR_CEILING, fit, mrv, weekly_schedule

SESSIONS_PER_WEEK = 3
TRAINING_DAYS = (0, 2, 4)
TRUE_SAT = SaturationParams(enabled=True, ceiling=POPULATION_PRIOR_CEILING)


# ---------------------------------------------------------------------------
# The derivative itself
# ---------------------------------------------------------------------------


def marginal_return(
    weekly_sets: float,
    params: FFParams,
    sat: SaturationParams,
    sessions: int = SESSIONS_PER_WEEK,
    h: float = 0.25,
) -> float:
    """
    d(steady-state preparedness) / d(weekly sets), evaluated at `weekly_sets`.

    Central difference. This is the quantity D-07 says a trigger must watch: what the
    NEXT set is worth, not whether the last month felt bad. It is positive below MRV,
    zero at it, and negative above — and crucially its SIGN is a much weaker thing to ask
    of the data than the location of the zero crossing.
    """
    lo = max(0.25, weekly_sets - h)
    hi = weekly_sets + h
    return (
        steady_state(hi, params, sessions, sat) - steady_state(lo, params, sessions, sat)
    ) / (hi - lo)


def normalised_marginal_return(
    weekly_sets: float,
    params: FFParams,
    sat: SaturationParams,
    sessions: int = SESSIONS_PER_WEEK,
) -> float:
    """
    Marginal return per set, expressed as a fraction of what the FIRST set is worth.

    Raw slope units are arbitrary and vary by lifter, so a threshold on the raw value
    would be a threshold on lifter identity. Normalising against the slope near zero
    volume makes "the last set is buying less than 10% of what the first one did" a
    statement that means the same thing for everybody.
    """
    reference = marginal_return(1.0, params, sat, sessions)
    if reference <= 1e-9:
        return 0.0
    return marginal_return(weekly_sets, params, sat, sessions) / reference


# ---------------------------------------------------------------------------
# Controllers
# ---------------------------------------------------------------------------


@dataclass
class ControllerState:
    volume: float
    weeks: list[float] = field(default_factory=list)
    slopes: list[float] = field(default_factory=list)
    prescribed: list[float] = field(default_factory=list)


class HillClimb:
    """
    Step volume in whichever direction the estimated marginal return points.

    Never estimates MRV. Only ever asks which way is uphill, which is the whole point:
    R3 showed the argmax needs 18 weeks of data and this needs only a sign.

    `dither` adds a deliberate alternating wobble to the prescription. It exists because
    of D-10 — a plan that does not vary produces a log that cannot identify the lifter —
    and because a hill climber that has converged stops varying by construction, which
    would slowly blind the very fit it depends on. The cost is real and is measured.
    """

    def __init__(
        self,
        start_volume: float,
        step_frac: float = 0.12,
        dither: float = 0.0,
        min_volume: float = 4.0,
        max_volume: float = 60.0,
        deadband: float = 0.05,
    ):
        self.state = ControllerState(volume=start_volume)
        self.step_frac = step_frac
        self.dither = dither
        self.min_volume = min_volume
        self.max_volume = max_volume
        self.deadband = deadband

    def prescribe(self, week: int) -> float:
        v = self.state.volume
        if self.dither > 0.0:
            v *= (1.0 + self.dither) if week % 2 == 0 else (1.0 - self.dither)
        return max(self.min_volume, min(self.max_volume, v))

    def update(self, params: FFParams, sat: SaturationParams) -> None:
        slope = normalised_marginal_return(self.state.volume, params, sat)
        self.state.slopes.append(slope)
        if slope > self.deadband:
            self.state.volume *= 1.0 + self.step_frac
        elif slope < -self.deadband:
            self.state.volume *= 1.0 - self.step_frac
        self.state.volume = max(self.min_volume, min(self.max_volume, self.state.volume))


class LevelTrigger:
    """
    R1's trigger, kept as the baseline to beat: ramp until preparedness is below where it
    was 7 days ago, then cut.

    It is here because a new mechanism that cannot beat the broken one it replaces has
    not earned its place, and because D-07's falsification condition is stated in terms
    of it.
    """

    def __init__(self, start_volume: float, step_frac: float = 0.12,
                 deload_frac: float = 0.45, min_volume: float = 4.0,
                 max_volume: float = 60.0):
        self.state = ControllerState(volume=start_volume)
        self.step_frac = step_frac
        self.deload_frac = deload_frac
        self.min_volume = min_volume
        self.max_volume = max_volume
        self.weeks_since_cut = 0

    def prescribe(self, week: int) -> float:
        return max(self.min_volume, min(self.max_volume, self.state.volume))

    def update_from_observations(self, observations: list[float]) -> None:
        self.weeks_since_cut += 1
        if len(observations) >= 2 and observations[-1] < observations[-2] and self.weeks_since_cut >= 2:
            self.state.volume *= self.deload_frac
            self.weeks_since_cut = 0
        else:
            self.state.volume *= 1.0 + self.step_frac
        self.state.volume = max(self.min_volume, min(self.max_volume, self.state.volume))


# ---------------------------------------------------------------------------
# Closed-loop simulation
# ---------------------------------------------------------------------------


def run_closed_loop(
    truth: FFParams,
    weeks: int,
    controller,
    noise: float = 2.5,
    seed: int = 0,
    refit_every: int = 2,
    use_fit: bool = True,
):
    """
    Week by week: prescribe, train, test, refit, update.

    The fit only ever sees data that existed at the time of the decision — no controller
    here is allowed to peek at the future or at the truth. `refit_every` exists because
    refitting is the expensive step and a controller that acts on a two-week-old fit is
    also more realistic than one that re-derives everything every Monday.
    """
    import random

    from ff_model import simulate

    rng = random.Random(seed)
    daily: list[float] = []
    test_days: list[int] = []
    observations: list[float] = []
    prescribed: list[float] = []

    params, sat = POPULATION_PRIOR, TRUE_SAT

    for w in range(weeks):
        v = controller.prescribe(w)
        prescribed.append(v)
        # Record the controller's CENTRE separately from what it prescribed. A dithered
        # controller deliberately oscillates around its centre, so scoring convergence on
        # the prescription marks any dither wider than the tolerance as "never converges"
        # by construction — which is a property of the metric, not the controller.
        controller.state.weeks.append(controller.state.volume)
        daily.extend(weekly_schedule(v, TRAINING_DAYS))

        trace = simulate(daily, truth, saturation=TRUE_SAT)
        day = w * 7
        test_days.append(day)
        observations.append(trace.preparedness[day] + rng.gauss(0.0, noise))

        if isinstance(controller, LevelTrigger):
            controller.update_from_observations(observations)
            continue

        if use_fit and w >= 3 and (w % refit_every == 0):
            log = Log(daily_sets=daily, test_days=test_days, observations=observations)
            params, sat, _ = fit(log, restarts=2)
        if use_fit:
            controller.update(params, sat)

    controller.state.prescribed = prescribed
    return prescribed, observations


def points_lost_over_block(prescribed: list[float], truth: FFParams) -> float:
    """
    Mean steady-state preparedness given up across the block.

    Averaged over weeks rather than taken at the end, because a controller that spends
    ten weeks badly wrong and then converges has cost the lifter those ten weeks, and an
    endpoint metric would hand it a free pass.
    """
    best = steady_state(mrv(truth, TRUE_SAT), truth, SESSIONS_PER_WEEK, TRUE_SAT)
    losses = [
        best - steady_state(v, truth, SESSIONS_PER_WEEK, TRUE_SAT) for v in prescribed
    ]
    return sum(losses) / len(losses)


def weeks_to_converge(prescribed: list[float], truth: FFParams, tol: float = 0.15) -> int | None:
    """First week after which the prescription stays within `tol` of true MRV."""
    target = mrv(truth, TRUE_SAT)
    for i in range(len(prescribed)):
        if all(abs(v - target) / target <= tol for v in prescribed[i:]):
            return i
    return None
