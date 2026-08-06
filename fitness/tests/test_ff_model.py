"""
MESO — core regression suite. Pure stdlib: `python3 -m unittest discover fitness/tests`.

These are not unit tests for their own sake. Each one pins a property that a later round
could quietly break while every number still looks plausible — which is the specific
failure mode of a simulation-driven project, because a simulation never crashes, it just
starts lying.
"""

from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))

from ff_model import (  # noqa: E402
    FFParams,
    POPULATION_PRIOR,
    RIR_FATIGUE,
    RIR_STIMULUS,
    SaturationParams,
    StalenessParams,
    block,
    lifter_population,
    session_cost,
    session_impulse,
    simulate,
    steady_state,
    weekly_schedule,
)


class TestParameterGuards(unittest.TestCase):
    def test_fatigue_must_decay_faster_than_fitness(self):
        with self.assertRaises(ValueError):
            FFParams(tau_fit=10.0, tau_fat=20.0)

    def test_fatigue_gain_must_exceed_fitness_gain(self):
        # Otherwise every session improves performance the moment it is finished, and
        # the model can never explain why anyone is ever tired.
        with self.assertRaises(ValueError):
            FFParams(k_fit=2.0, k_fat=1.0)

    def test_population_members_are_all_valid(self):
        pop = lifter_population(200)
        self.assertEqual(len(pop), 200)
        for p in pop:
            self.assertGreater(p.k_fat, p.k_fit)
            self.assertLess(p.tau_fat, p.tau_fit)

    def test_population_is_deterministic(self):
        self.assertEqual(lifter_population(30), lifter_population(30))
        self.assertNotEqual(lifter_population(30, seed=1), lifter_population(30, seed=2))


class TestImpulseResponse(unittest.TestCase):
    def test_a_single_session_hurts_before_it_helps(self):
        """The whole model in one test: cost today, benefit later."""
        trace = simulate([10.0] + [0.0] * 120)
        self.assertAlmostEqual(trace.preparedness[0], POPULATION_PRIOR.p0, places=9)
        self.assertLess(trace.preparedness[1], POPULATION_PRIOR.p0)   # next morning: worse
        self.assertGreater(trace.preparedness[30], POPULATION_PRIOR.p0)  # a month on: better
        self.assertGreater(trace.preparedness[121], POPULATION_PRIOR.p0)

    def test_the_crossover_is_where_the_algebra_says(self):
        """
        Preparedness returns to baseline when k_fit*e^(-t/tau_fit) == k_fat*e^(-t/tau_fat),
        i.e. t = ln(k_fat/k_fit) / (1/tau_fat - 1/tau_fit).
        """
        p = POPULATION_PRIOR
        expected = math.log(p.k_fat / p.k_fit) / (1 / p.tau_fat - 1 / p.tau_fit)
        trace = simulate([10.0] + [0.0] * 200)
        crossing = next(
            d for d in range(2, len(trace)) if trace.preparedness[d] >= p.p0
        )
        # The trace is discrete and shifted by one day of decay; allow two days.
        self.assertLess(abs((crossing - 1) - expected), 2.0, f"crossing {crossing}, algebra {expected:.2f}")

    def test_rest_decays_both_traces_toward_zero(self):
        trace = simulate([10.0] * 30 + [0.0] * 400)
        self.assertLess(trace.fatigue[-1], 1e-6)
        # 400 days is ~9.5 fitness time-constants, so the residue is ~1e-4 of a peak of
        # ~217 — small, but not zero. Detraining is slow; that is the point of tau_fit.
        self.assertLess(trace.fitness[-1], 0.05)
        self.assertLess(abs(trace.preparedness[-1] - POPULATION_PRIOR.p0), 0.05)

    def test_simulation_converges_to_the_closed_form(self):
        """
        Guards the closed form and the recursion against each other.

        Compared against the mean of the final week, NOT the final day. For a linear
        time-invariant system under a periodic input, the per-period mean of the state
        equals DC-gain x mean-input — which is exactly what `steady_state` computes. A
        single day's value is a phase of the within-week oscillation and does not equal
        it. Comparing against `final()` fails by ~2.6 points at 18 sets/week, and that
        is the model being right, not wrong.
        """
        for weekly in (6.0, 18.0, 30.0):
            trace = simulate(block([weekly] * 60))
            last_week = sum(trace.preparedness[-7:]) / 7.0
            closed = steady_state(weekly, POPULATION_PRIOR, sessions_per_week=3)
            self.assertLess(
                abs(last_week - closed),
                0.05,
                f"{weekly} sets/wk: sim week-mean {last_week:.3f} vs closed form {closed:.3f}",
            )

    def test_the_week_has_a_large_readiness_swing(self):
        """
        A 3-day week is lumpy: the fast fatigue trace rises and falls inside it. Pinned
        because it is the reason a plan cannot treat every day as equally ready, and any
        change to TRAINING_DAYS should force a visible decision here.
        """
        trace = simulate(block([24.0] * 40))
        week = trace.preparedness[-7:]
        swing = max(week) - min(week)
        self.assertGreater(swing, 5.0, f"swing {swing:.2f} — week has gone suspiciously flat")
        self.assertLess(swing, 40.0, f"swing {swing:.2f} — week has gone wild")

    def test_trace_length_is_days_plus_one(self):
        self.assertEqual(len(simulate([1.0] * 14)), 15)


class TestNoInteriorOptimumWithoutSaturation(unittest.TestCase):
    """
    R1's central finding, pinned so a later round cannot silently un-find it.

    If this test ever fails, the linear model has acquired an optimum it should not
    have, which means something else changed shape — go read LOOP_LOG R1 before
    "fixing" it.
    """

    def test_linear_steady_state_is_strictly_increasing_in_volume(self):
        prev = -math.inf
        for sets in range(2, 200, 2):
            cur = steady_state(float(sets), POPULATION_PRIOR, 3)
            self.assertGreater(cur, prev)
            prev = cur

    def test_linear_bracket_is_constant(self):
        p = POPULATION_PRIOR
        a = steady_state(10.0, p, 3) - p.p0
        b = steady_state(20.0, p, 3) - p.p0
        self.assertAlmostEqual(b / a, 2.0, places=6)


class TestSaturation(unittest.TestCase):
    def test_saturating_model_turns_over(self):
        sat = SaturationParams(enabled=True)
        curve = [steady_state(float(s), POPULATION_PRIOR, 3, sat) for s in range(2, 120, 2)]
        peak = max(range(len(curve)), key=lambda i: curve[i])
        self.assertGreater(peak, 0, "optimum sits at the low boundary — no MEV region")
        self.assertLess(peak, len(curve) - 1, "optimum sits at the high boundary — still no MRV")

    def test_saturation_is_a_no_op_at_low_volume(self):
        """Derivative at zero is 1 by construction, so tiny doses must be unaffected."""
        sat = SaturationParams(enabled=True)
        lin = steady_state(0.3, POPULATION_PRIOR, 3)
        s = steady_state(0.3, POPULATION_PRIOR, 3, sat)
        self.assertLess(abs(lin - s), 0.05)

    def test_saturation_never_increases_the_deposit(self):
        sat = SaturationParams(enabled=True)
        for sets in (1.0, 5.0, 12.0, 40.0):
            self.assertLessEqual(
                steady_state(sets, POPULATION_PRIOR, 3, sat),
                steady_state(sets, POPULATION_PRIOR, 3) + 1e-9,
            )


class TestStaleness(unittest.TestCase):
    def test_disabled_by_default(self):
        trace = simulate(block([20.0] * 8))
        self.assertTrue(all(f == 1.0 for f in trace.adaptation_factor))

    def test_factor_stays_within_bounds(self):
        stale = StalenessParams(enabled=True)
        trace = simulate(block([40.0] * 12), staleness=stale)
        for f in trace.adaptation_factor:
            self.assertGreaterEqual(f, stale.floor - 1e-9)
            self.assertLessEqual(f, 1.0 + 1e-9)

    def test_staleness_can_only_lower_preparedness(self):
        weeks = block([30.0] * 12)
        self.assertLessEqual(
            simulate(weeks, staleness=StalenessParams(enabled=True)).final(),
            simulate(weeks).final() + 1e-9,
        )


class TestSetAccounting(unittest.TestCase):
    def test_rir_tables_are_anchored_at_two(self):
        self.assertEqual(RIR_STIMULUS[2], 1.00)
        self.assertEqual(RIR_FATIGUE[2], 1.00)

    def test_fatigue_rises_faster_than_stimulus_toward_failure(self):
        """The arithmetic reason DESIGN.md prescribes RIR 1-3 rather than RIR 0."""
        ratio_at_0 = RIR_STIMULUS[0] / RIR_FATIGUE[0]
        ratio_at_2 = RIR_STIMULUS[2] / RIR_FATIGUE[2]
        self.assertLess(ratio_at_0, ratio_at_2)

    def test_both_tables_are_monotonic(self):
        vals_s = [RIR_STIMULUS[r] for r in sorted(RIR_STIMULUS)]
        vals_f = [RIR_FATIGUE[r] for r in sorted(RIR_FATIGUE)]
        self.assertEqual(vals_s, sorted(vals_s, reverse=True))
        self.assertEqual(vals_f, sorted(vals_f, reverse=True))

    def test_session_helpers_agree_at_the_anchor(self):
        self.assertAlmostEqual(session_impulse(6, 2), session_cost(6, 2))
        self.assertAlmostEqual(session_impulse(6, 2), 6.0)

    def test_weekly_schedule_conserves_volume(self):
        for days in ((0, 2, 4), (0, 1, 3, 5), (0,)):
            self.assertAlmostEqual(sum(weekly_schedule(21.0, days)), 21.0)
            self.assertEqual(len(weekly_schedule(21.0, days)), 7)

    def test_block_length_and_volume(self):
        series = block([10.0, 20.0, 5.0])
        self.assertEqual(len(series), 21)
        self.assertAlmostEqual(sum(series), 35.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
