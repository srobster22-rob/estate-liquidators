"""
MESO — population variant regression suite.

The claim these guard is unusual for this project: not that a number is right, but that
four populations differ in exactly the way they are documented to differ. R6's whole
argument is a comparison ACROSS them, so a variant that quietly stopped being what its
docstring says would invalidate the round without failing anything.
"""

from __future__ import annotations

import math
import os
import statistics
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))

from confidence import TRUE_SAT  # noqa: E402
from fit import has_interior_optimum, mrv  # noqa: E402
from population import (  # noqa: E402
    VARIANTS,
    baseline,
    clean,
    correlated,
    degenerate_rate,
    narrow,
    narrowing_for_target,
)


def _deg(pop) -> float:
    return sum(0 if has_interior_optimum(p, TRUE_SAT) else 1 for p in pop) / len(pop)


class TestAllVariants(unittest.TestCase):
    def test_each_produces_exactly_what_was_asked_for(self):
        """Rejection sampling must not quietly return short."""
        for name, build in VARIANTS.items():
            self.assertEqual(len(build(50)), 50, name)

    def test_each_produces_only_valid_lifters(self):
        for name, build in VARIANTS.items():
            for p in build(60):
                self.assertGreater(p.k_fat, p.k_fit, name)
                self.assertLess(p.tau_fat, p.tau_fit, name)

    def test_each_is_deterministic(self):
        for name, build in VARIANTS.items():
            self.assertEqual(build(30, seed=11), build(30, seed=11), name)


class TestDegeneracy(unittest.TestCase):
    def test_clean_contains_none_by_construction(self):
        self.assertEqual(_deg(clean(200)), 0.0)

    def test_baseline_contains_some(self):
        rate = _deg(baseline(400))
        self.assertGreater(rate, 0.01)
        self.assertLess(rate, 0.15)

    def test_correlating_the_gains_reduces_but_does_not_eliminate_it(self):
        """
        R6's finding that the degeneracy is not purely a gains problem. Correlating k_fit
        with k_fat roughly halves the rate; the remainder comes from the tau ratio, which
        this variant leaves independent.
        """
        b, c = _deg(baseline(400)), _deg(correlated(400))
        self.assertLess(c, b, "correlation should reduce the unfavourable corner")
        self.assertGreater(c, 0.0, "correlation alone should not eliminate it")

    def test_narrow_hits_its_derived_target(self):
        factor = narrowing_for_target(target=0.005, n=300)
        self.assertGreater(factor, 0.2, "narrowing collapsed to nothing")
        self.assertLessEqual(factor, 1.0)
        self.assertLessEqual(degenerate_rate(lambda k, s: narrow(k, s, factor), 300), 0.02)


class TestCopulaIsolatesDependence(unittest.TestCase):
    """
    The load-bearing claim of the CORRELATED variant: same marginals as BASELINE, only
    the joint structure differs. Without it, any BASELINE-vs-CORRELATED difference could
    be a marginal effect in disguise and R6's comparison would mean nothing.
    """

    def test_marginals_are_preserved(self):
        b, c = baseline(2500, seed=5), correlated(2500, seed=5)
        for attr in ("k_fit", "k_fat"):
            mb = statistics.fmean([getattr(p, attr) for p in b])
            mc = statistics.fmean([getattr(p, attr) for p in c])
            sb = statistics.stdev([getattr(p, attr) for p in b])
            sc = statistics.stdev([getattr(p, attr) for p in c])
            self.assertLess(abs(mb - mc) / mb, 0.03, f"{attr} mean moved")
            self.assertLess(abs(sb - sc) / sb, 0.06, f"{attr} sd moved")

    def test_the_correlation_is_the_thing_that_changes(self):
        b, c = baseline(2500, seed=5), correlated(2500, seed=5)
        corr_b = statistics.correlation([p.k_fit for p in b], [p.k_fat for p in b])
        corr_c = statistics.correlation([p.k_fit for p in c], [p.k_fat for p in c])
        self.assertLess(abs(corr_b), 0.15, "baseline gains should be near-independent")
        self.assertGreater(corr_c, 0.5, "correlated variant lost its dependence")


class TestSpread(unittest.TestCase):
    def test_narrow_is_narrower_and_baseline_is_widest(self):
        def spread(pop) -> float:
            v = sorted(mrv(p, TRUE_SAT) for p in pop)
            return v[int(0.9 * len(v))] / max(v[int(0.1 * len(v))], 1e-9)

        s_narrow = spread(narrow(300))
        s_base = spread(baseline(300))
        self.assertLess(s_narrow, s_base)
        self.assertGreater(s_narrow, 1.5, "narrowing removed the variation entirely")

    def test_log_mrv_is_finite_everywhere(self):
        for name, build in VARIANTS.items():
            for p in build(80):
                self.assertTrue(math.isfinite(math.log(mrv(p, TRUE_SAT))), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
