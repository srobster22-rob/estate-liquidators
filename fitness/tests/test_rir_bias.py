"""
MESO — RIR reporting bias regression suite.

R9's finding is a negative one with a condition attached: a constant RIR bias cancels,
*provided* the baseline was measured the same way. These tests pin the condition, because
the failure mode is silent — a declared baseline produces a log that looks completely
normal and fits nearly twice as badly.
"""

from __future__ import annotations

import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "logger"))

from log import PerformanceTest, TrainingLog, e1rm  # noqa: E402
from rir_bias import (  # noqa: E402
    BiasModel,
    estimate_constant_offset,
    fatigue_fraction,
    observed_reps_and_load,
)


class TestBiasModel(unittest.TestCase):
    def test_no_bias_reports_the_truth(self):
        b = BiasModel()
        self.assertEqual(b.reported(2.0, 10, 0.5), 2.0)
        self.assertTrue(b.is_constant_only())

    def test_a_positive_offset_under_reports_reps_in_reserve(self):
        """Positive means the lifter says fewer reps left than they had."""
        self.assertLess(BiasModel(constant=1.0).reported(2.0, 0, 0.0), 2.0)

    def test_drift_grows_with_weeks_and_state_with_fatigue(self):
        drift = BiasModel(drift=0.1)
        self.assertGreater(drift.reported(3.0, 0, 0.0), drift.reported(3.0, 10, 0.0))
        state = BiasModel(state=1.0)
        self.assertGreater(state.reported(3.0, 0, 0.0), state.reported(3.0, 0, 1.0))
        self.assertFalse(drift.is_constant_only())
        self.assertFalse(state.is_constant_only())

    def test_reported_rir_cannot_go_below_zero(self):
        """
        The clamp that R9's first run mistook for a harmless result. It is real — a lifter
        cannot claim fewer than zero reps in reserve — and it means a large enough bias
        saturates into a CONSTANT, which then cancels. D-26's RIR cap is doing protective
        work nobody designed it for.
        """
        b = BiasModel(constant=5.0, drift=1.0, state=3.0)
        for week in (0, 5, 25):
            for ff in (0.0, 0.5, 1.0):
                self.assertEqual(b.reported(1.0, week, ff), 0.0)


class TestFatigueFraction(unittest.TestCase):
    def test_bounded_and_monotone_against_the_trace(self):
        from ff_model import block, simulate

        trace = simulate(block([20.0] * 8))
        for day in (0, 10, 30, len(trace.fatigue) - 1):
            self.assertGreaterEqual(fatigue_fraction(trace, day), 0.0)
            self.assertLessEqual(fatigue_fraction(trace, day), 1.0)

    def test_day_zero_is_unfatigued(self):
        from ff_model import block, simulate

        self.assertEqual(fatigue_fraction(simulate(block([20.0] * 4)), 0), 0.0)

    def test_a_day_past_the_end_does_not_crash(self):
        from ff_model import block, simulate

        trace = simulate(block([20.0] * 2))
        self.assertLessEqual(fatigue_fraction(trace, 10_000), 1.0)


class TestObservedRepsAndLoad(unittest.TestCase):
    def test_the_label_is_wrong_but_the_physics_is_not(self):
        """
        The mechanism: the lifter performs to their TRUE rir and mislabels it. Load and
        reps must therefore depend on the truth, not on what gets written down.
        """
        a = observed_reps_and_load(140.0, reported_rir=0.0, true_rir=1.0)
        b = observed_reps_and_load(140.0, reported_rir=1.0, true_rir=1.0)
        self.assertEqual(a, b)

    def test_load_lands_on_the_plate_grid(self):
        load, _ = observed_reps_and_load(137.0, 1.0, 1.0, plate=2.5)
        self.assertAlmostEqual(load / 2.5, round(load / 2.5), places=9)


class TestEstimator(unittest.TestCase):
    def test_recovers_a_known_offset(self):
        training = [e1rm(120.0, r, 1.0) for r in (3, 4, 5, 6)]
        tests = [e1rm(120.0, r, 2.0) for r in (3, 4, 5, 6)]
        expected = sum(math.log(t / s) for s, t in zip(training, tests)) / 4
        self.assertAlmostEqual(estimate_constant_offset(training, tests), expected, places=9)

    def test_identical_inputs_imply_no_offset(self):
        v = [140.0, 142.0, 138.0]
        self.assertAlmostEqual(estimate_constant_offset(v, v), 0.0, places=12)

    def test_empty_and_invalid_inputs_return_zero_rather_than_raising(self):
        self.assertEqual(estimate_constant_offset([], []), 0.0)
        self.assertEqual(estimate_constant_offset([0.0], [140.0]), 0.0)


class TestBaselineProvenance(unittest.TestCase):
    """D-30: the condition under which a constant bias cancels."""

    def test_a_measured_baseline_is_marked_as_such(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            log = TrainingLog()
            log.set_baseline_from_test(
                path, PerformanceTest(0, 0, "squat", 4, 120.0, 1.0))
            self.assertEqual(log.baseline_source["squat"], "test")

    def test_a_declared_baseline_is_flagged_by_validate(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            log = TrainingLog()
            log.set_baseline(path, "squat", 140.0)
            log.append_test(path, PerformanceTest(1, 0, "squat", 4, 120.0, 1.0))
            problems = log.validate()
            self.assertTrue(any("declared rather than measured" in p for p in problems))

    def test_a_measured_baseline_passes_validate(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            log = TrainingLog()
            log.set_baseline_from_test(
                path, PerformanceTest(0, 0, "squat", 4, 120.0, 1.0))
            log.append_test(path, PerformanceTest(1, 0, "squat", 4, 122.5, 1.0))
            self.assertEqual(log.validate(), [])

    def test_provenance_survives_the_disk_round_trip(self):
        from log import load

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            log = TrainingLog()
            log.set_baseline_from_test(
                path, PerformanceTest(0, 0, "squat", 4, 120.0, 1.0))
            self.assertEqual(load(path).baseline_source["squat"], "test")

    def test_an_old_log_without_provenance_reads_as_declared(self):
        """Backward compatibility: records written before R9 have no source field."""
        from log import load

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('{"type": "baseline", "exercise": "squat", "value": 140.0}\n')
            back = load(path)
            self.assertEqual(back.baseline_e1rm["squat"], 140.0)
            self.assertEqual(back.baseline_source["squat"], "declared")


if __name__ == "__main__":
    unittest.main(verbosity=2)
