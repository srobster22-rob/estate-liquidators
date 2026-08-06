"""
MESO — dose-derivative controller regression suite.

Two failure modes worth guarding. First, a controller that looks like it is responding to
data while actually just drifting in a fixed direction. Second — the one that bit this
round — a metric that scores a controller on something it cannot satisfy by construction.
"""

from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))

from confidence import TRUE_SAT  # noqa: E402
from ff_model import POPULATION_PRIOR, lifter_population  # noqa: E402
from fit import has_interior_optimum, mrv  # noqa: E402
from trigger import (  # noqa: E402
    HillClimb,
    LevelTrigger,
    marginal_return,
    normalised_marginal_return,
    points_lost_over_block,
    run_closed_loop,
    weeks_to_converge,
)


class TestMarginalReturn(unittest.TestCase):
    def test_sign_flips_at_mrv(self):
        """The definition of MRV, restated as a property of the derivative."""
        for p in lifter_population(12, seed=17):
            if not has_interior_optimum(p, TRUE_SAT):
                continue
            peak = mrv(p, TRUE_SAT)
            self.assertGreater(marginal_return(peak * 0.5, p, TRUE_SAT), 0.0)
            self.assertLess(marginal_return(peak * 1.5, p, TRUE_SAT), 0.0)

    def test_is_near_zero_at_the_peak(self):
        for p in lifter_population(8, seed=17):
            if not has_interior_optimum(p, TRUE_SAT):
                continue
            peak = mrv(p, TRUE_SAT)
            reference = marginal_return(1.0, p, TRUE_SAT)
            self.assertLess(abs(marginal_return(peak, p, TRUE_SAT)) / reference, 0.02)

    def test_boundary_lifters_are_detected_rather_than_prescribed_to(self):
        """
        ~4.5% of the synthetic population has no interior optimum — the model tells them
        never to train, and mrv() returns the search boundary. They were silently inside
        every population from R1 to R3, inflating the reported spread. D-16.
        """
        pop = lifter_population(200, seed=20260805)
        degenerate = [p for p in pop if not has_interior_optimum(p, TRUE_SAT)]
        self.assertGreater(len(degenerate), 0, "detector found none — is it still working?")
        self.assertLess(len(degenerate) / len(pop), 0.10)
        for p in degenerate:
            self.assertLess(marginal_return(1.0, p, TRUE_SAT), 0.0)

    def test_normalised_starts_near_one_and_decreases(self):
        p = POPULATION_PRIOR
        peak = mrv(p, TRUE_SAT)
        vals = [normalised_marginal_return(v, p, TRUE_SAT)
                for v in (1.0, peak * 0.5, peak, peak * 1.5)]
        self.assertAlmostEqual(vals[0], 1.0, places=6)
        self.assertEqual(vals, sorted(vals, reverse=True))


class TestHillClimb(unittest.TestCase):
    def test_steps_toward_the_peak_from_both_sides(self):
        """Given the TRUE parameters, the controller must be right by construction."""
        p = POPULATION_PRIOR
        peak = mrv(p, TRUE_SAT)

        low = HillClimb(peak * 0.5)
        low.update(p, TRUE_SAT)
        self.assertGreater(low.state.volume, peak * 0.5)

        high = HillClimb(peak * 1.5)
        high.update(p, TRUE_SAT)
        self.assertLess(high.state.volume, peak * 1.5)

    def test_holds_still_inside_the_deadband(self):
        p = POPULATION_PRIOR
        c = HillClimb(mrv(p, TRUE_SAT))
        before = c.state.volume
        c.update(p, TRUE_SAT)
        self.assertAlmostEqual(c.state.volume, before, places=9)

    def test_respects_its_bounds(self):
        p = POPULATION_PRIOR
        c = HillClimb(5.0, step_frac=0.9, min_volume=4.0, max_volume=60.0)
        for _ in range(60):
            c.update(p, TRUE_SAT)
            self.assertGreaterEqual(c.state.volume, 4.0)
            self.assertLessEqual(c.state.volume, 60.0)

    def test_dither_oscillates_around_the_centre(self):
        c = HillClimb(20.0, dither=0.15)
        a, b = c.prescribe(0), c.prescribe(1)
        self.assertGreater(a, 20.0)
        self.assertLess(b, 20.0)
        self.assertAlmostEqual((a + b) / 2.0, 20.0, places=6)


class TestScoring(unittest.TestCase):
    def test_prescribing_true_mrv_costs_nothing(self):
        for p in lifter_population(8, seed=21):
            peak = mrv(p, TRUE_SAT)
            self.assertLess(points_lost_over_block([peak] * 10, p), 1e-3)

    def test_loss_averages_over_the_block_not_the_endpoint(self):
        """
        A controller that is badly wrong for half the block and perfect afterwards has
        cost the lifter those weeks. Pinned because an endpoint metric would hand it a
        free pass, and this project has already been burned once by a metric that
        flattered the thing it measured.
        """
        p = POPULATION_PRIOR
        peak = mrv(p, TRUE_SAT)
        mixed = [peak * 2.5] * 5 + [peak] * 5
        self.assertGreater(points_lost_over_block(mixed, p), 1.0)
        self.assertLess(points_lost_over_block(mixed, p), points_lost_over_block([peak * 2.5] * 10, p))

    def test_convergence_requires_staying_converged(self):
        p = POPULATION_PRIOR
        peak = mrv(p, TRUE_SAT)
        self.assertEqual(weeks_to_converge([peak] * 6, p), 0)
        self.assertIsNone(weeks_to_converge([peak] * 5 + [peak * 3], p))
        self.assertEqual(weeks_to_converge([peak * 3] + [peak] * 5, p), 1)

    def test_dither_wider_than_tolerance_is_a_metric_artefact(self):
        """
        The bug this round shipped and then caught: scoring a dithered controller on its
        prescription rather than its centre marks it as never converging no matter how
        well it tracks the peak. Both behaviours are pinned so the distinction cannot be
        quietly lost.
        """
        p = POPULATION_PRIOR
        peak = mrv(p, TRUE_SAT)
        dithered = [peak * 1.18 if i % 2 == 0 else peak * 0.82 for i in range(10)]
        self.assertIsNone(weeks_to_converge(dithered, p, tol=0.15))
        self.assertEqual(weeks_to_converge([peak] * 10, p, tol=0.15), 0)


class TestClosedLoop(unittest.TestCase):
    def test_is_deterministic_given_a_seed(self):
        truth = lifter_population(1, seed=5)[0]
        a, _ = run_closed_loop(truth, 12, HillClimb(30.0), seed=1)
        b, _ = run_closed_loop(truth, 12, HillClimb(30.0), seed=1)
        self.assertEqual(a, b)

    def test_records_centre_and_prescription_separately(self):
        truth = lifter_population(1, seed=5)[0]
        c = HillClimb(30.0, dither=0.15)
        pres, _ = run_closed_loop(truth, 8, c, seed=1)
        self.assertEqual(len(pres), 8)
        self.assertEqual(len(c.state.weeks), 8)
        self.assertNotEqual(pres[0], c.state.weeks[0])

    def test_beats_a_deliberately_bad_fixed_prescription(self):
        """
        The weakest possible sanity check, and it should be easy: a controller that reads
        its own data must beat one parked at four times the population MRV.
        """
        losses_c, losses_fixed = [], []
        for i, truth in enumerate(lifter_population(6, seed=31337)):
            pres, _ = run_closed_loop(truth, 24, HillClimb(30.8, dither=0.10), seed=9000 + i)
            losses_c.append(points_lost_over_block(pres, truth))
            losses_fixed.append(points_lost_over_block([120.0] * 24, truth))
        self.assertLess(sum(losses_c), sum(losses_fixed))

    def test_level_trigger_still_runs(self):
        """R1's broken trigger is the baseline D-07 is stated against — keep it alive."""
        truth = lifter_population(1, seed=5)[0]
        pres, obs = run_closed_loop(truth, 12, LevelTrigger(30.0), seed=1)
        self.assertEqual(len(pres), 12)
        self.assertTrue(all(math.isfinite(v) for v in pres))


if __name__ == "__main__":
    unittest.main(verbosity=2)
