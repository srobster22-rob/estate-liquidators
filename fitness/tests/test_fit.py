"""
MESO — fitter regression suite.

The dangerous failure here is not a crash. It is an optimiser that quietly returns its
starting point while every reported percentage still looks reasonable — which is exactly
what a stable-but-useless fit looks like from the outside. Several of these tests exist
only to make that visible.
"""

from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))

from ff_model import POPULATION_PRIOR, FFParams, SaturationParams, lifter_population  # noqa: E402
from fit import (  # noqa: E402
    HISTORIES,
    POPULATION_PRIOR_CEILING,
    fit,
    make_log,
    mrv,
    nelder_mead,
    pack,
    unpack,
)

TRUE_SAT = SaturationParams(enabled=True, ceiling=POPULATION_PRIOR_CEILING)


class TestReparameterisation(unittest.TestCase):
    def test_pack_unpack_roundtrips(self):
        for p in lifter_population(25, seed=8):
            got, _ = unpack(pack(p))
            self.assertAlmostEqual(got.k_fit, p.k_fit, places=6)
            self.assertAlmostEqual(got.k_fat, p.k_fat, places=6)
            self.assertAlmostEqual(got.tau_fit, p.tau_fit, places=5)
            self.assertAlmostEqual(got.tau_fat, p.tau_fat, places=5)

    def test_roundtrip_carries_the_ceiling(self):
        _, sat = unpack(pack(POPULATION_PRIOR, 9.5))
        self.assertAlmostEqual(sat.ceiling, 9.5, places=6)

    def test_unpack_never_produces_invalid_parameters(self):
        """
        The optimiser walks wherever it likes. Every point in R^5, including absurd ones,
        must map to parameters FFParams will accept — otherwise the loss surface has
        holes in it and Nelder-Mead falls into them.
        """
        for x in (
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [1e6, 1e6, 1e6, 1e6, 1e6],
            [-1e6, -1e6, -1e6, -1e6, -1e6],
            [50.0, -50.0, 50.0, -50.0, 3.0],
            [-30.0, 12.0, 6.9, 40.0, -8.0],
        ):
            params, sat = unpack(x)          # must not raise
            self.assertGreater(params.k_fat, params.k_fit)
            self.assertLess(params.tau_fat, params.tau_fit)
            self.assertGreater(params.tau_fat, 0.0)
            self.assertGreater(sat.ceiling, 0.0)
            self.assertTrue(math.isfinite(params.k_fit))


class TestOptimiser(unittest.TestCase):
    def test_finds_the_minimum_of_a_known_bowl(self):
        f = lambda v: (v[0] - 3.0) ** 2 + (v[1] + 1.5) ** 2 + 2.0
        x, score = nelder_mead(f, [0.0, 0.0])
        self.assertAlmostEqual(x[0], 3.0, places=3)
        self.assertAlmostEqual(x[1], -1.5, places=3)
        self.assertAlmostEqual(score, 2.0, places=5)

    def test_handles_rosenbrock(self):
        """A curved valley — if the implementation's contraction step is wrong, it stalls."""
        f = lambda v: (1 - v[0]) ** 2 + 100 * (v[1] - v[0] ** 2) ** 2
        x, score = nelder_mead(f, [-1.2, 1.0], max_iter=8000)
        self.assertLess(score, 1e-6, f"stalled at {x} scoring {score}")


class TestFitting(unittest.TestCase):
    def test_noiseless_recovery_is_essentially_exact(self):
        """
        With no measurement noise and an informative history, the fit must land on the
        truth. If this fails, the problem is the optimiser or the loss, not the data —
        which is worth knowing before interpreting any noisy result.
        """
        weekly = HISTORIES["PROBE"](16)
        for truth in lifter_population(3, seed=12):
            log = make_log(weekly, truth, TRUE_SAT, noise=0.0, seed=1)
            got, got_sat, score = fit(log)
            err = abs(mrv(got, got_sat) - mrv(truth, TRUE_SAT)) / mrv(truth, TRUE_SAT)
            self.assertLess(err, 0.02, f"MRV off by {err:.1%} with clean data")

    def test_the_fit_actually_moves_off_its_prior(self):
        """
        The null this round was built to survive: an optimiser returning its seed is
        perfectly stable and perfectly useless. Fit two lifters with very different true
        MRVs and require the prescriptions to differ in the same direction.
        """
        weekly = HISTORIES["PROBE"](24)
        pop = sorted(lifter_population(12, seed=77), key=lambda p: mrv(p, TRUE_SAT))
        low, high = pop[0], pop[-1]
        got_low, sat_low, _ = fit(make_log(weekly, low, TRUE_SAT, seed=3), restarts=2)
        got_high, sat_high, _ = fit(make_log(weekly, high, TRUE_SAT, seed=3), restarts=2)
        self.assertLess(
            mrv(got_low, sat_low),
            mrv(got_high, sat_high),
            "fitter did not distinguish a low-MRV lifter from a high-MRV one",
        )

    def test_a_flat_history_is_less_informative_than_a_varied_one(self):
        """
        R2's headline. Pinned because it is the finding that shapes the product: a plan
        that never varies produces a log you cannot learn from.
        """
        pop = lifter_population(6, seed=77)
        errs = {}
        for name in ("FLAT", "PROBE"):
            weekly = HISTORIES[name](16)
            total = 0.0
            for i, truth in enumerate(pop):
                log = make_log(weekly, truth, TRUE_SAT, seed=900 + i)
                got, got_sat, _ = fit(log, restarts=2)
                total += abs(mrv(got, got_sat) - mrv(truth, TRUE_SAT)) / mrv(truth, TRUE_SAT)
            errs[name] = total / len(pop)
        self.assertLess(
            errs["PROBE"],
            errs["FLAT"],
            f"PROBE {errs['PROBE']:.1%} vs FLAT {errs['FLAT']:.1%} — variation stopped paying",
        )


class TestMRV(unittest.TestCase):
    def test_agrees_with_the_volume_response_optimum(self):
        """Two independent golden-section searches over the same curve must agree."""
        from volume_response import optimum_weekly_sets

        sat = SaturationParams(enabled=True)
        for p in lifter_population(8, seed=3):
            self.assertAlmostEqual(mrv(p, sat), optimum_weekly_sets(p, sat)[0], places=1)

    def test_is_finite_and_positive_for_every_valid_lifter(self):
        sat = SaturationParams(enabled=True)
        for p in lifter_population(50, seed=4):
            v = mrv(p, sat)
            self.assertTrue(math.isfinite(v))
            self.assertGreater(v, 0.0)


class TestHistories(unittest.TestCase):
    def test_all_histories_produce_the_requested_length(self):
        for name, builder in HISTORIES.items():
            for weeks in (8, 16, 23):
                self.assertEqual(len(builder(weeks)), weeks, name)

    def test_flat_is_flat_and_the_others_are_not(self):
        self.assertEqual(len(set(HISTORIES["FLAT"](16))), 1)
        self.assertGreater(len(set(HISTORIES["WAVED"](16))), 3)
        self.assertGreater(len(set(HISTORIES["PROBE"](16))), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
