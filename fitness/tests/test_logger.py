"""
MESO — logger regression suite.

This is the first code in the project that touches a real person's data, so the failure
modes are different from the simulation's. The one that matters most: a log that silently
loses or reorders history would corrupt a fit without failing anything, because the fitter
cannot tell a short history from a truthful one.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sim"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "logger"))

from log import (  # noqa: E402
    FORMULAS,
    PerformanceTest,
    Session,
    TEST_MAX_REPS,
    TEST_MAX_RIR,
    TrainingLog,
    WorkSet,
    e1rm,
    load,
)
from readiness import (  # noqa: E402
    FULL_TRUST_ABOVE,
    PRIOR_ONLY_BELOW,
    VARIATION_FLOOR,
    assess,
    report,
    to_fittable,
    volume_variation,
)


def _sets(n: int, muscle: str = "quads", rir: float = 2.0) -> list[WorkSet]:
    return [WorkSet(muscle_group=muscle, reps=8, load=100.0, rir=rir) for _ in range(n)]


def _build(weekly: list[float], tests: bool = True) -> TrainingLog:
    log = TrainingLog(baseline_e1rm={"squat": 140.0})
    for w, count in enumerate(weekly):
        per_day = int(count) // 3
        for d in (0, 2, 4):
            if per_day:
                log.sessions.append(Session(week=w, day=d, sets=_sets(per_day)))
        if tests:
            log.tests.append(
                PerformanceTest(week=w, day=0, exercise="squat", reps=3, load=120.0, rir=1.0)
            )
    return log


class TestE1RM(unittest.TestCase):
    def test_all_formulas_agree_at_one_rep(self):
        """At a true single there is nothing to estimate, so they must coincide."""
        vals = [f(100.0, 1.0) for f in FORMULAS.values()]
        self.assertLess(max(vals) - min(vals), 4.0)

    def test_more_reps_means_a_higher_estimate(self):
        for name in FORMULAS:
            self.assertLess(e1rm(100.0, 5, 0, name), e1rm(100.0, 10, 0, name), name)

    def test_rir_is_treated_as_extra_reps(self):
        self.assertAlmostEqual(e1rm(100.0, 5, 2.0), e1rm(100.0, 7, 0.0), places=9)

    def test_brzycki_does_not_explode_or_go_negative(self):
        """It is undefined at 37 reps; clamped rather than confidently absurd."""
        for reps in (30, 36, 37, 40, 100):
            v = e1rm(100.0, reps, 0.0, "brzycki")
            self.assertGreater(v, 0.0)
            self.assertLess(v, 1e5)

    def test_rejects_impossible_sets(self):
        for bad in ((0.0, 5, 0.0), (100.0, 0, 0.0), (100.0, 5, -1.0)):
            with self.assertRaises(ValueError):
                e1rm(*bad)


class TestValidation(unittest.TestCase):
    def test_a_good_set_has_no_problems(self):
        self.assertEqual(WorkSet("quads", 8, 100.0, 2.0).validate(), [])

    def test_bad_sets_are_caught(self):
        self.assertTrue(WorkSet("", 8, 100.0).validate())
        self.assertTrue(WorkSet("quads", 0, 100.0).validate())
        self.assertTrue(WorkSet("quads", 8, -5.0).validate())
        self.assertTrue(WorkSet("quads", 8, 100.0, 99.0).validate())

    def test_the_test_protocol_is_enforced(self):
        """D-26: a test is a measurement, not a stimulus."""
        ok = PerformanceTest(0, 0, "squat", TEST_MAX_REPS, 100.0, TEST_MAX_RIR)
        self.assertEqual(ok.validate(), [])
        self.assertTrue(PerformanceTest(0, 0, "squat", TEST_MAX_REPS + 4, 100.0, 0.0).validate())
        self.assertTrue(PerformanceTest(0, 0, "squat", 5, 100.0, TEST_MAX_RIR + 2).validate())

    def test_duplicate_sessions_are_reported(self):
        log = TrainingLog()
        log.sessions = [Session(1, 0, _sets(3)), Session(1, 0, _sets(3))]
        self.assertTrue(any("duplicate" in p for p in log.validate()))

    def test_a_test_without_a_baseline_is_reported(self):
        log = TrainingLog()
        log.tests = [PerformanceTest(0, 0, "squat", 3, 120.0, 1.0)]
        self.assertTrue(any("baseline" in p for p in log.validate()))


class TestPersistence(unittest.TestCase):
    def test_roundtrips_through_disk(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            log = TrainingLog()
            log.set_baseline(path, "squat", 140.0)
            log.append_session(path, Session(0, 0, _sets(4)))
            log.append_test(path, PerformanceTest(0, 0, "squat", 3, 120.0, 1.0))

            back = load(path)
            self.assertEqual(back.baseline_e1rm["squat"], 140.0)
            self.assertEqual(len(back.sessions), 1)
            self.assertEqual(len(back.sessions[0].sets), 4)
            self.assertEqual(len(back.tests), 1)
            self.assertEqual(back.tests[0].load, 120.0)

    def test_missing_file_is_an_empty_log_not_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load(os.path.join(d, "nope.jsonl")).weeks_logged(), 0)

    def test_unknown_record_types_are_ignored_not_fatal(self):
        """Forward compatibility: a newer writer must not break an older reader."""
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            log = TrainingLog()
            log.append_session(path, Session(0, 0, _sets(2)))
            with open(path, "a", encoding="utf-8") as fh:
                fh.write('{"type": "sleep_score", "week": 0, "value": 7}\n')
            self.assertEqual(len(load(path).sessions), 1)

    def test_malformed_lines_raise_rather_than_vanish(self):
        """A line that cannot be parsed is data loss; skipping it silently would hide it."""
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{not json\n")
            with self.assertRaises(ValueError):
                load(path)

    def test_blank_lines_are_tolerated(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "meso.jsonl")
            log = TrainingLog()
            log.append_session(path, Session(0, 0, _sets(2)))
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\n\n")
            self.assertEqual(len(load(path).sessions), 1)


class TestAggregation(unittest.TestCase):
    def test_weekly_sets_counts_and_zero_fills(self):
        log = TrainingLog()
        log.sessions = [Session(0, 0, _sets(3)), Session(2, 0, _sets(5))]
        self.assertEqual(log.weekly_sets("quads"), [3.0, 0.0, 5.0])

    def test_daily_sets_are_rir_weighted(self):
        """A set at RIR 5 must not count the same as one at RIR 1 (DESIGN.md 6)."""
        hard = TrainingLog()
        hard.sessions = [Session(0, 0, _sets(4, rir=1.0))]
        easy = TrainingLog()
        easy.sessions = [Session(0, 0, _sets(4, rir=5.0))]
        self.assertGreater(sum(hard.daily_sets("quads")), sum(easy.daily_sets("quads")))

    def test_daily_sets_lands_on_the_right_days(self):
        log = TrainingLog()
        log.sessions = [Session(1, 2, _sets(3))]
        daily = log.daily_sets("quads")
        self.assertEqual(len(daily), 14)
        self.assertGreater(daily[9], 0.0)
        self.assertEqual(sum(daily[:9]) + sum(daily[10:]), 0.0)

    def test_muscle_groups_are_kept_separate(self):
        log = TrainingLog()
        log.sessions = [Session(0, 0, _sets(3, "quads") + _sets(2, "chest"))]
        self.assertEqual(log.weekly_sets("quads"), [3.0])
        self.assertEqual(log.weekly_sets("chest"), [2.0])
        self.assertEqual(log.muscle_groups(), ["chest", "quads"])


class TestFittableConversion(unittest.TestCase):
    def test_produces_arrays_the_fitter_accepts(self):
        from fit import fit as run_fit

        log = _build([12, 15, 18, 21, 24, 9] * 4)
        f = to_fittable(log, "quads")
        self.assertEqual(len(f.observations), len(f.test_days))
        self.assertEqual(len(f.daily_sets), log.weeks_logged() * 7)
        params, sat, score = run_fit(f.as_fit_log(), restarts=1)
        self.assertGreater(params.k_fat, params.k_fit)

    def test_a_missing_baseline_is_refused_not_defaulted(self):
        log = _build([12, 15, 18])
        log.baseline_e1rm.clear()
        with self.assertRaises(ValueError):
            to_fittable(log, "quads")

    def test_no_tests_at_all_is_refused(self):
        log = _build([12, 15, 18], tests=False)
        with self.assertRaises(ValueError):
            to_fittable(log, "quads")

    def test_observations_are_percentages_of_baseline(self):
        log = _build([12, 15, 18])
        f = to_fittable(log, "quads")
        expected = log.tests[0].estimated_1rm() / 140.0 * 100.0
        self.assertAlmostEqual(f.observations[0], expected, places=6)


class TestReadiness(unittest.TestCase):
    def test_a_short_log_gets_the_prior(self):
        r = assess(_build([12, 15, 18, 21]), "quads")
        self.assertEqual(r.verdict, "prior")
        self.assertEqual(r.trust_weight(), 0.0)

    def test_a_long_varied_log_gets_the_fit(self):
        r = assess(_build([12, 15, 18, 21, 24, 9] * 4), "quads")
        self.assertEqual(r.verdict, "fit")
        self.assertEqual(r.trust_weight(), 1.0)

    def test_a_flat_log_never_gets_the_fit_however_long(self):
        """
        D-10, enforced rather than documented. A lifter repeating the same volume for two
        years is still unidentifiable, and weeks alone must not unlock a personalised
        number.
        """
        r = assess(_build([18] * 40), "quads")
        self.assertEqual(r.verdict, "prior")
        self.assertLess(r.variation, VARIATION_FLOOR)
        self.assertTrue(any("vary" in reason for reason in r.reasons))

    def test_the_shrink_band_ramps_between_the_thresholds(self):
        weights = []
        for weeks in (PRIOR_ONLY_BELOW, PRIOR_ONLY_BELOW + 2, FULL_TRUST_ABOVE):
            pattern = ([12, 15, 18, 21, 24, 9] * 10)[:weeks]
            weights.append(assess(_build(pattern), "quads").trust_weight())
        self.assertEqual(weights, sorted(weights))
        self.assertLessEqual(weights[0], 0.01)
        self.assertGreaterEqual(weights[-1], 0.99)

    def test_variation_ignores_untrained_weeks(self):
        """A week off is a real thing; it must not read as variation or crash on log(0)."""
        self.assertEqual(volume_variation([18.0, 0.0, 18.0, 18.0]), 0.0)
        self.assertGreater(volume_variation([12.0, 0.0, 24.0]), 0.0)

    def test_report_states_its_own_calibration_limits(self):
        """D-15 in the product surface, not just in a document nobody reads."""
        text = report(_build([12, 15, 18, 21, 24, 9] * 4), "quads")
        self.assertIn("synthetic", text)
        self.assertIn("D-15", text)


class TestCLI(unittest.TestCase):
    """The CLI prints; tests capture it so a green run stays readable."""

    def test_logs_and_reports_end_to_end(self):
        from cli import main

        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            path = os.path.join(d, "meso.jsonl")
            # Measured baseline, the D-30 route the CLI now prefers.
            self.assertEqual(main(["baseline", path, "--exercise", "squat",
                                   "--reps", "4", "--load", "120", "--rir", "1"]), 0)
            self.assertEqual(main(["set", path, "--week", "0", "--day", "0",
                                   "--muscle", "quads", "--reps", "8", "--load", "100"]), 0)
            self.assertEqual(main(["test", path, "--week", "0", "--exercise", "squat",
                                   "--reps", "3", "--load", "120", "--rir", "1"]), 0)
            self.assertEqual(main(["status", path, "--muscle", "quads"]), 0)

            back = load(path)
            self.assertEqual(len(back.sessions), 1)
            self.assertEqual(len(back.tests), 1)

    def test_a_declared_baseline_warns_but_still_records(self):
        """D-30 is advice at the CLI, not a refusal — a log is a record of what happened."""
        from cli import main

        with tempfile.TemporaryDirectory() as d, \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            path = os.path.join(d, "meso.jsonl")
            self.assertEqual(
                main(["baseline", path, "--exercise", "squat", "--value", "140"]), 0)
            self.assertIn("D-30", err.getvalue())
            self.assertEqual(load(path).baseline_source["squat"], "declared")

    def test_adding_a_second_set_to_the_same_day_keeps_both(self):
        from cli import main

        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            path = os.path.join(d, "meso.jsonl")
            for _ in range(3):
                main(["set", path, "--week", "0", "--day", "0", "--muscle", "quads",
                      "--reps", "8", "--load", "100"])
            back = load(path)
            self.assertEqual(back.weekly_sets("quads"), [3.0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
