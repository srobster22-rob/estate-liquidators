"""
MESO — from a real log to a fittable one, and whether it can be trusted yet.

This is where six rounds of simulation meet real data. Everything the project learned
about when a fit is safe is enforced here, in one place, rather than restated by whatever
happens to call the fitter:

  D-13   below 14 weeks of varied training, prescribe the population prior and say so;
         14-18, shrink toward it; past 18, use the fit.
  D-10   an unvarying plan is an uninformative experiment — a log with no volume
         variation cannot identify the lifter no matter how long it runs, so weeks alone
         are not enough and variation is checked separately.
  D-22   report fractions, never magnitudes. No method here returns "you are losing N
         preparedness points"; that number is a property of PRIOR_SPREAD.
  D-15   every threshold below is calibrated on synthetic lifters. The readiness report
         says so, in its own output, every time.

THE POINT OF PUTTING IT HERE
  A gate that lives in a document is a gate nobody passes through. R3 measured what
  ungated fitting costs — at 8 weeks a personalised prescription is five times worse than
  ignoring the lifter entirely — so this module is the thing that stops that happening by
  construction rather than by discipline.
"""

from __future__ import annotations

import math
import os
import statistics
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))

from log import DEFAULT_FORMULA, TrainingLog  # noqa: E402

# Thresholds from D-13. Weeks of logged, varied training.
PRIOR_ONLY_BELOW = 14
FULL_TRUST_ABOVE = 18

# Minimum SD of log weekly sets for a history to count as "varied" (D-10). A normal waved
# mesocycle scores well above this; a lifter repeating the same volume scores zero.
# Calibrated against the WAVED history that scored 0.94 correlation in R2 — INFERRED in
# the sense that no real log has ever been measured against it. D-25.
VARIATION_FLOOR = 0.18


@dataclass
class FittableLog:
    """Exactly what `fit.fit()` consumes, plus provenance."""

    daily_sets: list[float]
    test_days: list[int]
    observations: list[float]
    muscle_group: str
    exercise: str
    formula: str

    def as_fit_log(self):
        from fit import Log

        return Log(
            daily_sets=self.daily_sets,
            test_days=self.test_days,
            observations=self.observations,
        )


def to_fittable(
    log: TrainingLog,
    muscle_group: str,
    exercise: str | None = None,
    formula: str = DEFAULT_FORMULA,
) -> FittableLog:
    """
    Convert a real training log into the arrays the fitter wants.

    Tests without a baseline are DROPPED rather than defaulted, because a missing baseline
    means the percentage is unanchored, and an unanchored observation is not a weak
    observation — it is a wrong one.
    """
    tests = sorted(log.tests, key=lambda t: (t.week, t.day))
    if exercise is None:
        if not tests:
            raise ValueError("no performance tests logged — nothing to fit against")
        exercise = statistics.mode([t.exercise for t in tests])

    tests = [t for t in tests if t.exercise == exercise]
    baseline = log.baseline_e1rm.get(exercise)
    if baseline is None:
        raise ValueError(
            f"no baseline e1RM recorded for '{exercise}' — "
            "log one before the observations mean anything"
        )

    test_days, observations = [], []
    for t in tests:
        test_days.append(t.week * 7 + t.day)
        observations.append(t.as_percentage(baseline, formula))

    return FittableLog(
        daily_sets=log.daily_sets(muscle_group),
        test_days=test_days,
        observations=observations,
        muscle_group=muscle_group,
        exercise=exercise,
        formula=formula,
    )


def volume_variation(weekly: list[float]) -> float:
    """SD of log weekly sets over weeks that contain training. D-10's excitation measure."""
    logs = [math.log(v) for v in weekly if v > 0]
    return statistics.stdev(logs) if len(logs) > 1 else 0.0


@dataclass
class Readiness:
    weeks_logged: int
    weeks_trained: int
    variation: float
    tests: int
    verdict: str          # "prior" | "shrink" | "fit"
    reasons: list[str]
    warnings: list[str]

    def trust_weight(self) -> float:
        """
        How far to move from the population prior toward this lifter's own fit, 0-1.

        Linear across the D-13 band. Linear rather than anything cleverer because R3
        established that the sophisticated version of exactly this decision — an
        empirical-Bayes weight from a bootstrap — lost to a plain week count (D-14), and
        because D-17 says precision near the answer is worth almost nothing anyway.
        """
        if self.verdict == "prior":
            return 0.0
        if self.verdict == "fit":
            return 1.0
        span = FULL_TRUST_ABOVE - PRIOR_ONLY_BELOW
        return max(0.0, min(1.0, (self.weeks_trained - PRIOR_ONLY_BELOW) / span))


def assess(log: TrainingLog, muscle_group: str) -> Readiness:
    """Decide what this log has earned the right to say about its owner."""
    weekly = log.weekly_sets(muscle_group)
    weeks_trained = sum(1 for v in weekly if v > 0)
    variation = volume_variation(weekly)
    tests = len([t for t in log.tests])

    reasons: list[str] = []
    warnings: list[str] = []

    problems = log.validate()
    if problems:
        warnings.extend(problems[:5])
        if len(problems) > 5:
            warnings.append(f"...and {len(problems) - 5} more validation problems")

    varied = variation >= VARIATION_FLOOR
    if not varied:
        reasons.append(
            f"volume variation {variation:.2f} is below the {VARIATION_FLOOR:.2f} floor — "
            "a plan that does not vary cannot identify you (D-10), and more weeks of the "
            "same thing will not fix it"
        )

    if tests < weeks_trained * 0.7:
        warnings.append(
            f"only {tests} performance tests across {weeks_trained} trained weeks — "
            "the fit reads the tests, not the sets"
        )

    if not varied or weeks_trained < PRIOR_ONLY_BELOW:
        verdict = "prior"
        if weeks_trained < PRIOR_ONLY_BELOW:
            reasons.append(
                f"{weeks_trained} weeks of training logged, {PRIOR_ONLY_BELOW} needed "
                "before a personalised number beats a population one (D-13)"
            )
    elif weeks_trained <= FULL_TRUST_ABOVE:
        verdict = "shrink"
        reasons.append(
            f"{weeks_trained} weeks logged — inside the {PRIOR_ONLY_BELOW}-"
            f"{FULL_TRUST_ABOVE} week band where a fit is worth something but not "
            "everything"
        )
    else:
        verdict = "fit"
        reasons.append(
            f"{weeks_trained} varied weeks logged, past the {FULL_TRUST_ABOVE}-week "
            "threshold where fitting stops being worse than not fitting"
        )

    return Readiness(
        weeks_logged=log.weeks_logged(),
        weeks_trained=weeks_trained,
        variation=variation,
        tests=tests,
        verdict=verdict,
        reasons=reasons,
        warnings=warnings,
    )


def report(log: TrainingLog, muscle_group: str) -> str:
    r = assess(log, muscle_group)
    lines = [
        f"Readiness — {muscle_group}",
        "",
        f"  weeks logged        {r.weeks_logged}",
        f"  weeks trained       {r.weeks_trained}",
        f"  volume variation    {r.variation:.2f}  (floor {VARIATION_FLOOR:.2f})",
        f"  performance tests   {r.tests}",
        f"  verdict             {r.verdict.upper()}  (trust weight {r.trust_weight():.2f})",
        "",
    ]
    for reason in r.reasons:
        lines.append(f"  · {reason}")
    if r.warnings:
        lines.append("")
        for w in r.warnings:
            lines.append(f"  ! {w}")
    lines += [
        "",
        "  Every threshold above is calibrated on synthetic lifters generated by the",
        "  model that then fits them (D-15). They are the best available and they are",
        "  not measurements. This log is part of what would replace them.",
    ]
    return "\n".join(lines)
