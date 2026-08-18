"""
MESO — R9. Which RIR reporting errors actually matter, and can they be estimated?

The question this exists to answer:

    D-24 flagged that the project treats a set of n reps at RIR r as (n + r) reps at
    failure, which presumes the lifter's RIR estimate is unbiased. R7 measured the size of
    a misestimate — 4.8% on an observation — and D-28 showed that a bias of that order
    matters far more than noise of the same size, because it does not average out.

    R8's ranking put this first on the grounds that a per-lifter offset must be estimable
    from data the logger records, and data not collected in month one cannot be recovered
    in month six. So: what does the estimator need, and does it work?

THE THING TO CHECK BEFORE BUILDING ANY OF IT
  Observations are not e1RM values. They are e1RM expressed as a PERCENTAGE OF A BASELINE
  measured the same way (DESIGN.md 4.1 — this is what makes p0 = 100 a definition rather
  than a fifth free parameter).

  So a bias that scales every e1RM by the same factor scales the numerator and the
  denominator alike, and cancels. Before building an estimator for a quantity, it is worth
  establishing whether the quantity reaches the answer at all.

WHAT SURVIVES THE RATIO
  Only a bias that VARIES. Two candidates, and the second is the dangerous one:

    drift      the lifter's RIR judgement improves with experience — a slow trend
    state      the lifter misjudges RIR worse when fatigued — correlated with exactly
               the thing being measured, which is the worst possible structure

  `BiasModel` represents both, and the experiment measures what each costs.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))


@dataclass(frozen=True)
class BiasModel:
    """
    How a lifter's reported RIR differs from the truth.

        reported_rir = true_rir - constant - drift * week - state * fatigue_fraction

    Signs are chosen so a POSITIVE parameter means the lifter UNDER-reports reps in
    reserve — says "2 left" when they had more — which is the direction the literature
    describes for inexperienced lifters and the direction that inflates an e1RM.

    `state` is expressed against a fatigue fraction in [0, 1], so its units are "reps of
    RIR misjudgement at maximum fatigue".
    """

    constant: float = 0.0
    drift: float = 0.0          # reps per week
    state: float = 0.0          # reps at full fatigue

    def reported(self, true_rir: float, week: int, fatigue_fraction: float) -> float:
        offset = self.constant + self.drift * week + self.state * fatigue_fraction
        return max(0.0, true_rir - offset)

    def is_constant_only(self) -> bool:
        return self.drift == 0.0 and self.state == 0.0


def fatigue_fraction(trace, day: int) -> float:
    """
    How fatigued this lifter is on a given day, scaled 0-1 against their own worst.

    Uses the fatigue trace rather than preparedness because the claim under test is about
    RIR judgement under fatigue, not about performance.
    """
    if not trace.fatigue:
        return 0.0
    worst = max(trace.fatigue) or 1.0
    d = min(day, len(trace.fatigue) - 1)
    return trace.fatigue[d] / worst


def observed_reps_and_load(
    true_e1rm: float,
    reported_rir: float,
    true_rir: float,
    plate: float = 2.5,
    target_reps: int = 4,
) -> tuple[float, int]:
    """
    What gets written down when the lifter's RIR judgement is wrong.

    The lifter genuinely performs to `true_rir` — their body does what it does — but
    RECORDS `reported_rir`. The load and rep count are real; only the RIR label is wrong.
    That is the whole mechanism, and it matters that the error enters through the label
    rather than through the physiology.
    """
    target_load = true_e1rm / (1.0 + (target_reps + true_rir) / 30.0)
    load = max(plate, round(target_load / plate) * plate) if plate > 0 else target_load
    reps_at_failure = 30.0 * (true_e1rm / load - 1.0)
    reps = max(1, int(math.floor(reps_at_failure - true_rir)))
    return load, reps


def estimate_constant_offset(
    training_e1rms: list[float], test_e1rms: list[float]
) -> float:
    """
    Reconcile e1RM implied by claimed-RIR training sets against e1RM from near-failure
    tests, in log space. The mean discrepancy is the lifter's RIR offset expressed as a
    proportion.

    This is the estimator D-24 asked for, and it needs nothing the logger does not already
    record — `WorkSet` carries load, reps and rir. What it DOES need is for training sets
    to be logged truthfully on the tested lift, which the schema permits and nothing
    currently enforces or uses. That is the finding for the logger, not a new field.
    """
    pairs = [
        math.log(t / s)
        for s, t in zip(training_e1rms, test_e1rms)
        if s > 0 and t > 0
    ]
    if not pairs:
        return 0.0
    return sum(pairs) / len(pairs)
