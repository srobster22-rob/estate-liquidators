"""
MESO — confidence gate regression suite.

The failure mode here is a gate that reports low confidence and then prescribes the same
number anyway, or one whose shrinkage weight is really a hand-tuned threshold wearing a
Bayesian costume. Several of these tests exist to keep both honest.
"""

from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))

from confidence import (  # noqa: E402
    TRUE_SAT,
    population_log_mrv_spread,
    preparedness_lost,
    prescribe,
    spearman,
    volume_variation,
)
from ff_model import POPULATION_PRIOR, lifter_population  # noqa: E402
from fit import HISTORIES, make_log, mrv  # noqa: E402


class TestPopulationSpread(unittest.TestCase):
    def test_tau_is_a_plausible_log_spread(self):
        mean, tau = population_log_mrv_spread(120, seed=9)
        self.assertGreater(tau, 0.3, "prior too tight — shrinkage would swallow every fit")
        self.assertLess(tau, 2.0, "prior too loose — shrinkage would never engage")
        self.assertTrue(math.isfinite(mean))

    def test_tau_is_deterministic(self):
        self.assertEqual(population_log_mrv_spread(80, seed=3), population_log_mrv_spread(80, seed=3))


class TestVolumeVariation(unittest.TestCase):
    def test_flat_history_scores_zero(self):
        p = lifter_population(1, seed=2)[0]
        log = make_log(HISTORIES["FLAT"](12), p, TRUE_SAT, noise=0.0, seed=1)
        self.assertAlmostEqual(volume_variation(log), 0.0, places=9)

    def test_varied_histories_score_above_flat(self):
        p = lifter_population(1, seed=2)[0]
        flat = volume_variation(make_log(HISTORIES["FLAT"](12), p, TRUE_SAT, seed=1))
        waved = volume_variation(make_log(HISTORIES["WAVED"](12), p, TRUE_SAT, seed=1))
        probe = volume_variation(make_log(HISTORIES["PROBE"](12), p, TRUE_SAT, seed=1))
        self.assertGreater(waved, flat)
        self.assertGreater(probe, flat)

    def test_survives_a_week_with_no_training(self):
        """A week off is a real thing lifters do; log(0) must not reach the gate."""
        p = lifter_population(1, seed=2)[0]
        log = make_log([18.0, 0.0, 18.0, 22.0, 0.0, 14.0], p, TRUE_SAT, seed=1)
        v = volume_variation(log)
        self.assertTrue(math.isfinite(v))
        self.assertGreaterEqual(v, 0.0)


class TestPreparednessLost(unittest.TestCase):
    def test_prescribing_the_truth_costs_nothing(self):
        for p in lifter_population(8, seed=6):
            self.assertLess(abs(preparedness_lost(mrv(p, TRUE_SAT), p)), 1e-3)

    def test_loss_is_never_negative(self):
        for p in lifter_population(8, seed=6):
            for sets in (2.0, 12.0, 25.0, 60.0, 120.0):
                self.assertGreaterEqual(preparedness_lost(sets, p), -1e-6)

    def test_overshooting_costs_more_than_undershooting(self):
        """
        The asymmetry every percent-error table in this project has been hiding: MRV is
        the peak of a curve that falls away steeply on the high side and gently on the
        low side, so equal proportional errors are not equally bad.
        """
        p = POPULATION_PRIOR
        best = mrv(p, TRUE_SAT)
        self.assertGreater(
            preparedness_lost(best * 1.6, p),
            preparedness_lost(best / 1.6, p),
            "overshoot is no longer the expensive direction — check the saturation form",
        )


class TestGate(unittest.TestCase):
    def test_weight_is_bounded_and_the_prescription_lies_between(self):
        _, tau = population_log_mrv_spread(80, seed=9)
        prior_log = math.log(mrv(POPULATION_PRIOR, TRUE_SAT))
        for i, truth in enumerate(lifter_population(4, seed=44)):
            log = make_log(HISTORIES["WAVED"](16), truth, TRUE_SAT, seed=50 + i)
            c = prescribe(log, tau, prior_log, draws=6, seed=i)
            self.assertGreaterEqual(c.weight, 0.0)
            self.assertLessEqual(c.weight, 1.0)
            lo, hi = sorted((c.fitted_mrv, math.exp(prior_log)))
            self.assertGreaterEqual(c.prescribed_mrv, lo - 1e-6)
            self.assertLessEqual(c.prescribed_mrv, hi + 1e-6)

    def test_a_flat_history_is_trusted_less_than_a_varied_one(self):
        """
        The gate's whole reason to exist: it must be able to tell an uninformative log
        from an informative one, without being told which is which.
        """
        _, tau = population_log_mrv_spread(80, seed=9)
        prior_log = math.log(mrv(POPULATION_PRIOR, TRUE_SAT))
        pop = lifter_population(5, seed=44)
        weights = {}
        for name in ("FLAT", "PROBE"):
            total = 0.0
            for i, truth in enumerate(pop):
                log = make_log(HISTORIES[name](16), truth, TRUE_SAT, seed=60 + i)
                total += prescribe(log, tau, prior_log, draws=8, seed=i).weight
            weights[name] = total / len(pop)
        self.assertLess(
            weights["FLAT"],
            weights["PROBE"],
            f"FLAT {weights['FLAT']:.2f} vs PROBE {weights['PROBE']:.2f} — "
            "gate cannot see the difference between an informative log and a flat one",
        )


class TestSpearman(unittest.TestCase):
    def test_perfect_monotone_relationships(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertAlmostEqual(spearman(xs, [1.0, 4.0, 9.0, 16.0, 25.0]), 1.0, places=6)
        self.assertAlmostEqual(spearman(xs, [5.0, 4.0, 3.0, 2.0, 1.0]), -1.0, places=6)

    def test_ignores_non_finite_pairs(self):
        xs = [1.0, 2.0, float("inf"), 4.0, 5.0]
        ys = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertAlmostEqual(spearman(xs, ys), 1.0, places=6)

    def test_returns_nan_when_there_is_nothing_to_rank(self):
        self.assertTrue(math.isnan(spearman([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
