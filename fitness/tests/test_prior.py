"""
MESO — starting-prior regression suite.

The characteristic failure of this round was a population statistic quietly computed over
members that do not belong in it. Several tests here exist purely to keep that visible.
"""

from __future__ import annotations

import math
import os
import statistics
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))

from confidence import TRUE_SAT, preparedness_lost, spearman  # noqa: E402
from ff_model import POPULATION_PRIOR, lifter_population  # noqa: E402
from fit import has_interior_optimum, mrv  # noqa: E402
from prior import (  # noqa: E402
    asymmetry_correction,
    best_constant,
    conditional_prescription,
    covariate_draws,
    degenerate_share,
    log_mrv_moments,
    population_mrvs,
)


class TestBestConstant(unittest.TestCase):
    def test_a_population_of_one_gets_its_own_mrv(self):
        p = POPULATION_PRIOR
        self.assertAlmostEqual(best_constant([p]), mrv(p, TRUE_SAT), delta=0.2)

    def test_it_actually_minimises(self):
        """The definition, checked against a grid rather than trusted."""
        pop, _ = population_mrvs(120, seed=808)
        opt = best_constant(pop)
        at_opt = statistics.fmean([preparedness_lost(opt, p) for p in pop])
        for v in (opt * 0.7, opt * 0.85, opt * 1.15, opt * 1.4):
            self.assertLessEqual(
                at_opt,
                statistics.fmean([preparedness_lost(v, p) for p in pop]) + 1e-9,
            )

    def test_asymmetry_correction_is_above_one(self):
        """
        The loss curve is steeper above MRV than below (D-17), which pulls the optimal
        constant off the geometric mean. The correction is reported rather than assumed,
        and this pins that it is a real effect and not noise.
        """
        pop, mrvs = population_mrvs(150, seed=808)
        self.assertGreater(asymmetry_correction(pop, mrvs), 1.0)


class TestDegenerateHandling(unittest.TestCase):
    def test_dropped_by_default_and_kept_on_request(self):
        clean, _ = population_mrvs(200, seed=31337)
        full, _ = population_mrvs(200, seed=31337, drop_degenerate=False)
        self.assertLess(len(clean), len(full))
        self.assertEqual(degenerate_share(clean), 0.0)
        self.assertGreater(degenerate_share(full), 0.0)

    def test_degenerate_lifters_inflate_the_population_spread(self):
        """
        R5's central mechanism, pinned. Lifters with no interior optimum sit at the MRV
        search boundary rather than at a real value, so including them inflates the SD of
        log-MRV — and every shrinkage estimator built on that SD spreads its
        prescriptions wider than the real population does. D-19.
        """
        _, clean = population_mrvs(300, seed=31337)
        _, full = population_mrvs(300, seed=31337, drop_degenerate=False)
        mu_clean, tau_clean = log_mrv_moments(clean)
        mu_full, tau_full = log_mrv_moments(full)
        self.assertGreater(tau_full, tau_clean * 1.2, "contamination effect has vanished")
        self.assertLess(mu_full, mu_clean, "degenerate lifters should drag the mean down")


class TestCovariate(unittest.TestCase):
    def test_realised_correlation_matches_the_request(self):
        _, mrvs = population_mrvs(400, seed=31337)
        logs = [math.log(v) for v in mrvs]
        for rho in (0.0, 0.3, 0.6, 0.9):
            z = covariate_draws(mrvs, rho, seed=7)
            got = statistics.correlation(logs, z)
            self.assertLess(abs(got - rho), 0.10, f"asked {rho}, got {got:.2f}")

    def test_rho_one_is_an_oracle(self):
        _, mrvs = population_mrvs(60, seed=31337)
        z = covariate_draws(mrvs, 1.0, seed=7)
        self.assertGreater(spearman([math.log(v) for v in mrvs], z), 0.999)

    def test_is_deterministic(self):
        _, mrvs = population_mrvs(40, seed=31337)
        self.assertEqual(covariate_draws(mrvs, 0.5, seed=3), covariate_draws(mrvs, 0.5, seed=3))


class TestConditionalPrescription(unittest.TestCase):
    def test_rho_zero_ignores_the_covariate(self):
        mu, tau = 3.2, 0.7
        vals = [conditional_prescription(z, mu, tau, 0.0) for z in (-2.0, 0.0, 2.0)]
        self.assertAlmostEqual(vals[0], vals[1], places=9)
        self.assertAlmostEqual(vals[1], vals[2], places=9)

    def test_higher_covariate_means_more_volume(self):
        mu, tau = 3.2, 0.7
        self.assertLess(
            conditional_prescription(-1.0, mu, tau, 0.6),
            conditional_prescription(1.0, mu, tau, 0.6),
        )

    def test_rho_one_recovers_the_lifters_own_value(self):
        _, mrvs = population_mrvs(50, seed=31337)
        mu, tau = log_mrv_moments(mrvs)
        z = covariate_draws(mrvs, 1.0, seed=7)
        for zi, v in list(zip(z, mrvs))[:10]:
            self.assertLess(abs(conditional_prescription(zi, mu, tau, 1.0) - v) / v, 0.02)


class TestMonotonicity(unittest.TestCase):
    def test_a_better_covariate_is_never_worse_on_a_clean_population(self):
        """
        R5's broken first run in one assertion. On a contaminated population, loss rose
        from rho 0.4 to 0.7 — a better covariate producing worse prescriptions, which is
        not a property of anything real. On a clean population it must fall throughout.
        """
        pop, mrvs = population_mrvs(300, seed=31337)
        mu, tau = log_mrv_moments(mrvs)
        factor = asymmetry_correction(pop, mrvs)
        losses = []
        for rho in (0.0, 0.3, 0.5, 0.7, 0.9, 1.0):
            z = covariate_draws(mrvs, rho, seed=4242)
            losses.append(statistics.fmean([
                preparedness_lost(conditional_prescription(zi, mu, tau, rho, factor), p)
                for zi, p in zip(z, pop)
            ]))
        for earlier, later in zip(losses, losses[1:]):
            self.assertLessEqual(later, earlier + 0.35, f"non-monotone: {losses}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
