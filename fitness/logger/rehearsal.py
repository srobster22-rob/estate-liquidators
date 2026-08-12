"""
MESO — R8. Does the production path recover what the simulation path recovers?

The question this exists to answer:

    Seven rounds have tested the fitter against arrays built by `fit.make_log`. Nothing
    has tested it against arrays built by `logger` + `readiness.to_fittable` — the code a
    real person will actually drive. Those are different code paths and only one of them
    ships.

    The gap between them is not a formality. `make_log` writes a float impulse per day and
    a real-valued observation. The production path writes integer reps at a rounded load,
    converts through an e1RM formula, and divides by a baseline. Every one of those steps
    is a place where a real number becomes a quantised one, and R7 already found one silent
    bug living in exactly this kind of seam.

WHAT THE REHEARSAL DOES
  Drives a known synthetic lifter through 26 weeks of a realistic waved plan, writing to a
  real JSONL log on disk via the logger's own API, then reads it back, converts, fits, and
  compares the recovered MRV to the truth — against the same lifter fitted through
  `make_log` as the control.

THE QUANTISATION NOBODY HAD MODELLED
  A lifter does not produce a real-valued observation. They pick a load the gym can
  actually make (2.5 kg increments) and do an integer number of reps. At 3-5 reps an e1RM
  moves by load/30 per rep — roughly 3% of the estimate — so the observation lands on a
  grid whether anyone modelled it or not. `quantisation_sweep` measures what that costs.
"""

from __future__ import annotations

import math
import os
import statistics
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))

from log import PerformanceTest, Session, TrainingLog, WorkSet, e1rm, load as load_log
from readiness import assess, to_fittable

from ff_model import SaturationParams, lifter_population, simulate, weekly_schedule
from fit import fit as run_fit, has_interior_optimum, mrv

TRUE_SAT = SaturationParams(enabled=True, ceiling=12.0)
TRAINING_DAYS = (0, 2, 4)
BASELINE_E1RM = 140.0
PLATE = 2.5
TEST_REPS_TARGET = 4
TEST_RIR = 1.0


def waved_plan(weeks: int) -> list[float]:
    """A plan a person would actually run: ramp, deload, repeat, carrying over."""
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


def _round_to_plate(load: float, plate: float = PLATE) -> float:
    return max(plate, round(load / plate) * plate)


def observed_test(true_e1rm: float, plate: float = PLATE) -> tuple[float, int, float]:
    """
    What a lifter actually records on test day.

    They pick a load the gym can make, then do as many reps as they can while leaving
    TEST_RIR in reserve. Both choices are quantised: the load to the plate increment, the
    reps to an integer. Returns (load, reps, rir).

    This is the step the simulation never had. `make_log` hands the fitter the lifter's
    real preparedness plus Gaussian noise; a real log hands it a number derived from two
    rounded quantities.
    """
    target_load = true_e1rm / (1.0 + (TEST_REPS_TARGET + TEST_RIR) / 30.0)
    load = _round_to_plate(target_load, plate) if plate > 0 else target_load

    reps_at_failure = 30.0 * (true_e1rm / load - 1.0)
    reps = max(1, int(math.floor(reps_at_failure - TEST_RIR)))
    return load, reps, TEST_RIR


def build_real_log(
    truth,
    weeks: int,
    path: str,
    noise: float = 0.0,
    seed: int = 0,
    plate: float = PLATE,
) -> TrainingLog:
    """
    Drive the LOGGER — not `make_log` — for `weeks` weeks against a known lifter.

    Everything goes through the same API a person would use, including the on-disk round
    trip, so anything the storage layer does to the data happens here too.
    """
    import random

    rng = random.Random(seed)
    plan = waved_plan(weeks)

    log = TrainingLog()
    log.set_baseline(path, "squat", BASELINE_E1RM)

    daily: list[float] = []
    for w, weekly_target in enumerate(plan):
        per_day = weekly_target / len(TRAINING_DAYS)

        # The lifter's readiness on test morning reflects everything logged so far.
        trace = simulate(daily, truth, saturation=TRUE_SAT)
        preparedness = trace.preparedness[w * 7] if w * 7 < len(trace.preparedness) else 100.0
        true_e1rm = BASELINE_E1RM * (preparedness + rng.gauss(0.0, noise)) / 100.0

        t_load, t_reps, t_rir = observed_test(true_e1rm, plate)
        log.append_test(
            path,
            PerformanceTest(week=w, day=0, exercise="squat",
                            reps=int(t_reps), load=t_load, rir=t_rir),
        )

        for d in TRAINING_DAYS:
            n_sets = int(round(per_day))
            if n_sets:
                sets = [
                    WorkSet(muscle_group="quads", reps=8, load=100.0, rir=2.0,
                            exercise="squat")
                    for _ in range(n_sets)
                ]
                log.append_session(path, Session(week=w, day=d, sets=sets))

        daily.extend(weekly_schedule(float(int(round(per_day)) * len(TRAINING_DAYS)),
                                     TRAINING_DAYS))

    return log


def path_comparison(n_lifters: int = 12, weeks: int = 26) -> None:
    """
    The round's central experiment: production path against simulation path, same lifters.

    If the production path recovers materially worse, the difference is in the code that
    ships and seven rounds of thresholds do not apply to it.
    """
    from fit import HISTORIES, make_log

    print(f"\n1. PATH COMPARISON — {weeks} weeks, {n_lifters} lifters")
    print("  Production = logger -> disk -> to_fittable -> fit")
    print("  Simulation = fit.make_log -> fit   (what every round so far measured)")
    print()
    print("  lifter   true MRV   production   sim path   prod err   sim err")
    print("  " + "-" * 66)

    pop = [p for p in lifter_population(n_lifters * 2, seed=31337)
           if has_interior_optimum(p, TRUE_SAT)][:n_lifters]

    prod_errs, sim_errs = [], []
    with tempfile.TemporaryDirectory() as d:
        for i, truth in enumerate(pop):
            true_mrv = mrv(truth, TRUE_SAT)

            path = os.path.join(d, f"lifter{i}.jsonl")
            build_real_log(truth, weeks, path, noise=2.5, seed=700 + i)
            f = to_fittable(load_log(path), "quads")
            got, got_sat, _ = run_fit(f.as_fit_log(), restarts=2)
            prod = mrv(got, got_sat)

            sim_log = make_log(HISTORIES["WAVED"](weeks), truth, TRUE_SAT,
                               noise=2.5, seed=700 + i)
            got2, got_sat2, _ = run_fit(sim_log, restarts=2)
            sim = mrv(got2, got_sat2)

            pe = abs(prod - true_mrv) / true_mrv * 100.0
            se = abs(sim - true_mrv) / true_mrv * 100.0
            prod_errs.append(pe)
            sim_errs.append(se)
            print(f"  {i:6d} {true_mrv:10.1f} {prod:12.1f} {sim:10.1f}"
                  f" {pe:10.1f}% {se:8.1f}%")

    print()
    print(f"  median error   production {statistics.median(prod_errs):6.1f}%"
          f"   simulation {statistics.median(sim_errs):6.1f}%")


def quantisation_sweep(n_lifters: int = 12, weeks: int = 26) -> None:
    """
    What does the real world's rounding cost?

    NOTE ON AN EARLIER VERSION OF THIS EXPERIMENT, kept because the mistake is instructive:
    it tried to separate "integer reps" from "continuous reps" as a factor. That is not
    separable, because `PerformanceTest.reps` is an int — reps ARE integers, in the schema
    because they are integers in reality, and the flag was silently truncated by the record
    constructor. The rows differed in label only.

    So the honest factor is plate granularity, swept below. The rep grid is measured
    separately in `observation_grid` as a property rather than as a condition, since there
    is no version of the world without it.
    """
    print(f"\n2. QUANTISATION — what gym plates cost ({n_lifters} lifters, ZERO noise)")
    print("  plate increment                  median MRV error   p90")
    print("  " + "-" * 58)

    pop = [p for p in lifter_population(n_lifters * 2, seed=31337)
           if has_interior_optimum(p, TRUE_SAT)][:n_lifters]

    with tempfile.TemporaryDirectory() as d:
        for label, plate in (("none (unreachable ideal)", 0.0),
                             ("1.0 kg (micro plates)", 1.0),
                             ("2.5 kg (typical gym)", 2.5),
                             ("5.0 kg (bare minimum)", 5.0)):
            errs = []
            for i, truth in enumerate(pop):
                true_mrv = mrv(truth, TRUE_SAT)
                path = os.path.join(d, f"p{plate}_{i}.jsonl")
                build_real_log(truth, weeks, path, noise=0.0, seed=700 + i, plate=plate)
                f = to_fittable(load_log(path), "quads")
                got, got_sat, _ = run_fit(f.as_fit_log(), restarts=2)
                errs.append(abs(mrv(got, got_sat) - true_mrv) / true_mrv * 100.0)
            errs.sort()
            print(f"  {label:<33} {statistics.median(errs):12.1f}%"
                  f" {errs[int(0.9 * len(errs))]:8.1f}%")

    print("\n  Noise is ZERO throughout. Everything above is the plate rack alone.")


def observation_grid() -> None:
    """The grid a real observation lands on, which no round before this one modelled."""
    print("\n3. THE OBSERVATION GRID — spacing of achievable e1RM values")
    print("  reps   load    e1RM    next rep    step    step as %")
    print("  " + "-" * 56)
    for reps in (2, 3, 4, 5, 8):
        load = _round_to_plate(140.0 / (1.0 + (reps + 1) / 30.0))
        here = e1rm(load, reps, 1.0)
        nxt = e1rm(load, reps + 1, 1.0)
        step = nxt - here
        print(f"  {reps:4d} {load:7.1f} {here:7.1f} {nxt:10.1f} {step:7.2f}"
              f" {step / here * 100:10.1f}%")
    print("\n  A rep is an atom. The observation cannot land between these values, so the")
    print("  quantisation error is uniform over one step: SD = step / sqrt(12).")


def readiness_at_the_end(weeks: int = 26) -> None:
    print(f"\n4. WHAT THE GATE SAYS after {weeks} weeks of a realistic plan")
    truth = [p for p in lifter_population(4, seed=31337)
             if has_interior_optimum(p, TRUE_SAT)][0]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "meso.jsonl")
        build_real_log(truth, weeks, path, noise=2.5, seed=1)
        r = assess(load_log(path), "quads")
        print(f"  verdict {r.verdict.upper()}, trust {r.trust_weight():.2f}, "
              f"variation {r.variation:.2f}, tests {r.tests}")
        for reason in r.reasons:
            print(f"  · {reason}")
        for w in r.warnings:
            print(f"  ! {w}")


def main() -> None:
    print("MESO R8 — does the production path recover what the simulation path recovers?")
    observation_grid()
    path_comparison()
    quantisation_sweep()
    readiness_at_the_end()


if __name__ == "__main__":
    main()
