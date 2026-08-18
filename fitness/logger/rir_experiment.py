"""
MESO — R9 experiments. Which RIR reporting errors reach the answer?

  1. DOES A CONSTANT BIAS EVEN MATTER?   Observations are a ratio to a baseline measured
                                          the same way, so a uniform scaling should cancel.
                                          Established before building anything on top.

  2. WHAT SURVIVES THE RATIO              Drift (judgement improves with experience) and
                                          state-dependence (judgement degrades with
                                          fatigue), swept separately.

  3. ESTIMABILITY                         Can the offset be recovered from what the logger
                                          already records?

  4. WHAT IT COSTS TO IGNORE              The whole point: is this worth a field, a
                                          protocol change, or nothing at all?
"""

from __future__ import annotations

import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))

from log import PerformanceTest, Session, TrainingLog, WorkSet, e1rm
from readiness import to_fittable
from rir_bias import BiasModel, estimate_constant_offset, fatigue_fraction, observed_reps_and_load

from ff_model import SaturationParams, lifter_population, simulate, weekly_schedule
from fit import fit as run_fit, has_interior_optimum, mrv

TRUE_SAT = SaturationParams(enabled=True, ceiling=12.0)
TRAINING_DAYS = (0, 2, 4)
BASELINE_E1RM = 140.0
TRUE_TEST_RIR = 1.0
WEEKS = 26
N_LIFTERS = 16


def waved(weeks: int) -> list[float]:
    out: list[float] = []
    start = 12.0
    while len(out) < weeks:
        for i in range(5):
            out.append(min(36.0, start + i * 3.0))
            if len(out) == weeks:
                return out
        out.append(round(out[-1] * 0.45))
        start = min(24.0, start + 1.0)
    return out[:weeks]


def build_log(truth, bias: BiasModel, weeks: int = WEEKS, seed: int = 0,
              noise: float = 2.5, biased_baseline: bool = True) -> TrainingLog:
    """
    Drive the logger with a lifter whose RIR reporting is systematically wrong.

    `biased_baseline` is the parameter this round turned out to be about. A real lifter
    establishes their reference e1RM the same way they take every weekly test — same
    protocol, same body, same RIR judgement — so their bias is baked into the denominator
    as well as the numerator. Setting this False models a baseline that came from somewhere
    else: a previous program, a coach's number, a true tested single.
    """
    import random
    import tempfile

    rng = random.Random(seed)
    plan = waved(weeks)
    path = os.path.join(tempfile.mkdtemp(), "meso.jsonl")

    log = TrainingLog()
    if biased_baseline:
        # What this lifter would RECORD as their baseline, under their own bias, rested.
        rir0 = bias.reported(TRUE_TEST_RIR, 0, 0.0)
        b_load, b_reps = observed_reps_and_load(BASELINE_E1RM, rir0, TRUE_TEST_RIR)
        recorded_baseline = e1rm(b_load, b_reps, rir0)
    else:
        recorded_baseline = BASELINE_E1RM
    log.set_baseline(path, "squat", recorded_baseline)

    daily: list[float] = []
    for w, weekly_target in enumerate(plan):
        per_day = int(round(weekly_target / len(TRAINING_DAYS)))
        trace = simulate(daily, truth, saturation=TRUE_SAT)
        day = w * 7
        prep = trace.preparedness[day] if day < len(trace.preparedness) else 100.0
        true_e1rm = BASELINE_E1RM * (prep + rng.gauss(0.0, noise)) / 100.0

        ff = fatigue_fraction(trace, day)
        reported_rir = bias.reported(TRUE_TEST_RIR, w, ff)
        load, reps = observed_reps_and_load(true_e1rm, reported_rir, TRUE_TEST_RIR)

        log.append_test(path, PerformanceTest(
            week=w, day=0, exercise="squat", reps=reps, load=load, rir=reported_rir))

        for d in TRAINING_DAYS:
            if per_day:
                log.append_session(path, Session(w, d, [
                    WorkSet("quads", 8, 100.0, 2.0, "squat") for _ in range(per_day)
                ]))
        daily.extend(weekly_schedule(float(per_day * len(TRAINING_DAYS)), TRAINING_DAYS))

    return log


def _median_err(bias: BiasModel, n: int = N_LIFTERS, biased_baseline: bool = True) -> float:
    pop = [p for p in lifter_population(n * 2, seed=31337)
           if has_interior_optimum(p, TRUE_SAT)][:n]
    errs = []
    for i, truth in enumerate(pop):
        log = build_log(truth, bias, seed=900 + i, biased_baseline=biased_baseline)
        f = to_fittable(log, "quads")
        got, got_sat, _ = run_fit(f.as_fit_log(), restarts=2)
        errs.append(abs(mrv(got, got_sat) - mrv(truth, TRUE_SAT)) / mrv(truth, TRUE_SAT) * 100.0)
    return statistics.median(errs)


def constant_bias() -> None:
    """
    Does a constant bias reach the answer, and does it depend on where the baseline
    came from?

    NOTE ON THE OFFSET RANGE. D-26 caps the test at RIR 0-1, and a lifter cannot claim
    fewer reps in reserve than zero. So an offset above the test RIR saturates: 1.0, 2.0
    and 3.0 all produce reported RIR 0 and byte-identical logs. That clamp is not an
    artefact of the experiment — it is a real and previously unnoticed property of the
    protocol, and it is reported rather than swept around.
    """
    print("\n1. DOES A CONSTANT BIAS REACH THE ANSWER?")
    print("  Observations are e1RM as a percentage of a baseline. If the baseline was")
    print("  measured by the same lifter under the same protocol, a constant bias scales")
    print("  numerator and denominator alike and should cancel.")
    print()
    print("  offset (reps)   baseline measured same way   baseline from elsewhere")
    print("  " + "-" * 68)
    for c in (0.0, 0.25, 0.5, 0.75, 1.0):
        same = _median_err(BiasModel(constant=c), biased_baseline=True)
        other = _median_err(BiasModel(constant=c), biased_baseline=False)
        print(f"  {c:13.2f}   {same:26.1f}%   {other:22.1f}%")
    print()
    print("  Offsets above 1.0 are omitted: the test is taken at RIR 1 (D-26) and reported")
    print("  RIR cannot go below zero, so they saturate to identical logs.")


def varying_bias() -> None:
    print("\n2. WHAT SURVIVES THE RATIO — bias that changes over the block")
    print("  drift is judgement improving with experience; state is judgement degrading")
    print("  with fatigue, which correlates with the very signal being measured.")
    print()
    print("  model                              median MRV error")
    print("  " + "-" * 54)
    print(f"  {'no bias':<34} {_median_err(BiasModel()):14.1f}%")
    for d in (0.02, 0.05, 0.10):
        label = f"drift {d:.2f} reps/week (={d * WEEKS:.1f} over block)"
        print(f"  {label:<34} {_median_err(BiasModel(drift=d)):14.1f}%")
    for st in (0.5, 1.0, 2.0):
        label = f"state {st:.1f} reps at full fatigue"
        print(f"  {label:<34} {_median_err(BiasModel(state=st)):14.1f}%")


def estimability() -> None:
    """Can the offset be recovered from what the logger already records?"""
    print("\n3. ESTIMABILITY — recovering a constant offset from logged sets vs tests")
    print("  true offset (reps)   implied e1RM ratio   estimated   error")
    print("  " + "-" * 62)
    for c in (0.0, 1.0, 2.0):
        training, tests = [], []
        for reps in (3, 4, 5, 6):
            load = 120.0
            # What the lifter claims (biased) against what a near-failure test shows.
            claimed = e1rm(load, reps, max(0.0, 2.0 - c))
            actual = e1rm(load, reps, 2.0)
            training.append(claimed)
            tests.append(actual)
        implied = statistics.fmean([math.log(t / s) for s, t in zip(training, tests)])
        est = estimate_constant_offset(training, tests)
        print(f"  {c:18.1f}   {math.exp(implied):18.4f}   {est:9.4f}   {abs(est - implied):6.4f}")


def cost_of_ignoring() -> None:
    """
    What ignoring RIR bias actually costs, given a same-protocol baseline.

    THE SATURATION TRAP, which this experiment fell into on its first run. A combined
    model with constant 1.5 scores +0.2 points — apparently harmless — but only because
    reported RIR is clamped at zero, so drift and state have nothing left to move and the
    whole thing collapses to a constant. Constants cancel (experiment 1), so the number
    was real and the interpretation would have been nonsense.

    That clamp is a genuine property of D-26's protocol rather than a modelling artefact,
    and it cuts in the project's favour: a bias large enough to saturate BECOMES a
    constant, and constants cancel. Only bias that stays inside 0 < reported RIR < 1 can
    vary, and that bounds how much of it can reach the answer at all. The row below is
    chosen to sit inside that unsaturated band, which is where the honest worst case lives.
    """
    print("\n4. WHAT IT COSTS TO IGNORE — with a same-protocol baseline")
    base = _median_err(BiasModel())
    saturating = _median_err(BiasModel(constant=1.5, drift=0.05, state=1.5))
    honest = _median_err(BiasModel(constant=0.2, drift=0.03, state=0.4))
    print(f"  no bias at all                          {base:6.1f}%")
    print(f"  worst case inside the unsaturated band  {honest:6.1f}%   "
          f"({honest - base:+.1f} pts)")
    print(f"  a saturating bias (const 1.5)           {saturating:6.1f}%   "
          f"({saturating - base:+.1f} pts)")
    print()
    print("  The saturating row is LOW because clamping turns it into a constant, and")
    print("  constants cancel. That is D-26's cap protecting the answer, not bias being")
    print("  harmless.")


def main() -> None:
    print("MESO R9 — which RIR reporting errors actually reach the answer?")
    constant_bias()
    varying_bias()
    estimability()
    cost_of_ignoring()


if __name__ == "__main__":
    main()
