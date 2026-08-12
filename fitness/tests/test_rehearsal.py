"""
MESO — end-to-end rehearsal regression suite.

These are the only tests in the project that exercise the code a real person will drive,
all the way from a logged set to a prescribed volume. Everything else tests a component.

The failure this suite exists to prevent: the production path silently diverging from the
simulation path, so that seven rounds of thresholds stop applying to the thing that ships
without anything going red.
"""

from __future__ import annotations

import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "logger"))

from ff_model import POPULATION_PRIOR, SaturationParams, lifter_population  # noqa: E402
from fit import fit as run_fit, has_interior_optimum, mrv  # noqa: E402
from log import load as load_log  # noqa: E402
from readiness import fit_is_usable, prescribe, to_fittable  # noqa: E402
from rehearsal import (  # noqa: E402
    BASELINE_E1RM,
    TRUE_SAT,
    build_real_log,
    observed_test,
    waved_plan,
)


class TestObservedTest(unittest.TestCase):
    def test_recovers_the_true_e1rm_when_nothing_is_rounded(self):
        """With no plate grid the construction is exact — a control for everything else."""
        from log import e1rm

        load, reps, rir = observed_test(140.0, plate=0.0)
        self.assertLess(abs(e1rm(load, reps, rir) - 140.0) / 140.0, 0.01)

    def test_obeys_the_d26_protocol(self):
        """A test the logger would reject is a test the rehearsal must not generate."""
        from log import TEST_MAX_REPS, TEST_MAX_RIR

        for true_e1rm in (80.0, 120.0, 140.0, 200.0):
            _, reps, rir = observed_test(true_e1rm)
            self.assertLessEqual(reps, TEST_MAX_REPS)
            self.assertLessEqual(rir, TEST_MAX_RIR)
            self.assertGreaterEqual(reps, 1)

    def test_load_lands_on_the_plate_grid(self):
        for plate in (1.0, 2.5, 5.0):
            load, _, _ = observed_test(137.0, plate=plate)
            self.assertAlmostEqual(load / plate, round(load / plate), places=9)

    def test_a_stronger_lifter_gets_a_heavier_load(self):
        self.assertLess(observed_test(100.0)[0], observed_test(180.0)[0])


class TestWavedPlan(unittest.TestCase):
    def test_length_and_variation(self):
        for weeks in (8, 26, 52):
            plan = waved_plan(weeks)
            self.assertEqual(len(plan), weeks)
            self.assertGreater(len(set(plan)), 3, "plan is too flat to identify anyone")

    def test_contains_deloads(self):
        plan = waved_plan(26)
        self.assertTrue(any(b < a * 0.6 for a, b in zip(plan, plan[1:])))


class TestEndToEnd(unittest.TestCase):
    def test_a_logged_lifter_survives_the_round_trip_to_a_fit(self):
        truth = next(p for p in lifter_population(8, seed=31337)
                     if has_interior_optimum(p, TRUE_SAT))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            build_real_log(truth, 26, path, noise=2.5, seed=1)

            back = load_log(path)
            self.assertEqual(back.weeks_logged(), 26)
            self.assertEqual(len(back.tests), 26)
            self.assertEqual(back.baseline_e1rm["squat"], BASELINE_E1RM)

            f = to_fittable(back, "quads")
            self.assertEqual(len(f.observations), 26)
            self.assertEqual(len(f.daily_sets), 26 * 7)

            params, sat, _ = run_fit(f.as_fit_log(), restarts=2)
            self.assertGreater(params.k_fat, params.k_fit)

    def test_the_written_log_has_no_validation_problems(self):
        """The rehearsal must not generate data the logger itself considers malformed."""
        truth = next(p for p in lifter_population(8, seed=31337)
                     if has_interior_optimum(p, TRUE_SAT))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            build_real_log(truth, 12, path, noise=2.5, seed=2)
            self.assertEqual(load_log(path).validate(), [])

    def test_observations_track_the_lifters_actual_trajectory(self):
        """
        Weakest possible signal check: with zero noise, a 26-week plan must produce
        observations that move. A pipeline returning a flat line would fit nothing and
        fail nothing.
        """
        truth = next(p for p in lifter_population(8, seed=31337)
                     if has_interior_optimum(p, TRUE_SAT))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            build_real_log(truth, 26, path, noise=0.0, seed=3)
            obs = to_fittable(load_log(path), "quads").observations
            self.assertGreater(max(obs) - min(obs), 2.0)


class TestFitSafety(unittest.TestCase):
    """
    R8's headline finding, pinned. One fit in twelve collapses to a parameter set with no
    interior optimum — the model's "never train" corner — for lifters whose true MRV is as
    high as 60 sets/week. Nothing in the pipeline checked it before this round.
    """

    def test_a_healthy_fit_is_usable(self):
        ok, why = fit_is_usable(POPULATION_PRIOR, TRUE_SAT)
        self.assertTrue(ok)
        self.assertEqual(why, "")

    def test_a_degenerate_fit_is_refused(self):
        degenerate = next(p for p in lifter_population(400, seed=20260805)
                          if not has_interior_optimum(p, TRUE_SAT))
        ok, why = fit_is_usable(degenerate, TRUE_SAT)
        self.assertFalse(ok)
        self.assertIn("prior", why)

    def test_an_absurd_volume_is_refused(self):
        from ff_model import FFParams

        # Very high adaptation gain and a long fitness constant push MRV past anything a
        # person trains; the guard must catch that as well as the degenerate corner.
        silly = FFParams(k_fit=4.0, k_fat=4.1, tau_fit=200.0, tau_fat=1.0)
        volume = mrv(silly, TRUE_SAT)
        ok, _ = fit_is_usable(silly, TRUE_SAT)
        self.assertEqual(ok, 2.0 <= volume <= 80.0)


class TestPrescribe(unittest.TestCase):
    def test_a_short_log_returns_the_prior_and_says_so(self):
        truth = next(p for p in lifter_population(8, seed=31337)
                     if has_interior_optimum(p, TRUE_SAT))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            build_real_log(truth, 6, path, noise=2.5, seed=4)
            volume, source, notes = prescribe(load_log(path), "quads", 26.9)
            self.assertEqual(source, "prior")
            self.assertAlmostEqual(volume, 26.9, places=9)
            self.assertTrue(notes)

    def test_a_long_log_returns_a_fit_labelled_as_one(self):
        truth = next(p for p in lifter_population(8, seed=31337)
                     if has_interior_optimum(p, TRUE_SAT))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            build_real_log(truth, 26, path, noise=2.5, seed=5)
            volume, source, _ = prescribe(load_log(path), "quads", 26.9)
            self.assertEqual(source, "fit")
            self.assertGreater(volume, 0.0)
            self.assertNotAlmostEqual(volume, 26.9, places=3)

    def test_the_source_is_never_silently_a_prior_presented_as_a_fit(self):
        """
        DESIGN idea 5 in code. A caller must be able to tell a personalised number from a
        population one without inspecting the value, because the two are indistinguishable
        by inspection and presenting one as the other is the failure that idea exists to
        prevent.
        """
        truth = next(p for p in lifter_population(8, seed=31337)
                     if has_interior_optimum(p, TRUE_SAT))
        with tempfile.TemporaryDirectory() as d:
            for weeks, expected in ((6, "prior"), (26, "fit")):
                path = os.path.join(d, f"m{weeks}.jsonl")
                build_real_log(truth, weeks, path, noise=2.5, seed=6)
                _, source, _ = prescribe(load_log(path), "quads", 26.9)
                self.assertEqual(source, expected)

    def test_a_flat_log_never_returns_a_fit(self):
        """D-10 enforced through the prescription entry point, not just the report."""
        from log import PerformanceTest, Session, TrainingLog, WorkSet

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "flat.jsonl")
            log = TrainingLog()
            log.set_baseline(path, "squat", BASELINE_E1RM)
            for w in range(40):
                for day in (0, 2, 4):
                    log.append_session(path, Session(w, day, [
                        WorkSet("quads", 8, 100.0, 2.0) for _ in range(5)
                    ]))
                log.append_test(path, PerformanceTest(w, 0, "squat", 4, 120.0, 1.0))
            volume, source, _ = prescribe(load_log(path), "quads", 26.9)
            self.assertEqual(source, "prior")
            self.assertAlmostEqual(volume, 26.9, places=9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
