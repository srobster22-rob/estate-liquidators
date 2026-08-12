import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from clipper import score as SC
from clipper import segment as S
from clipper import transcript as T
from clipper import validate as V

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def load(name: str):
    tr = T.load(FIXTURES / name)
    seg = S.segment(tr)
    return tr, seg, S.candidates(seg)


class StatisticsTests(unittest.TestCase):
    def test_pearson_extremes(self):
        a = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(V._pearson(a, a), 1.0)
        self.assertAlmostEqual(V._pearson(a, [4.0, 3.0, 2.0, 1.0]), -1.0)

    def test_pearson_of_a_constant_is_zero(self):
        self.assertEqual(V._pearson([1.0, 2.0, 3.0], [5.0, 5.0, 5.0]), 0.0)

    def test_pearson_of_mismatched_lengths_is_zero(self):
        self.assertEqual(V._pearson([1.0, 2.0], [1.0]), 0.0)

    def test_mean_and_sd(self):
        self.assertAlmostEqual(V._mean([2.0, 4.0]), 3.0)
        self.assertAlmostEqual(V._sd([2.0, 4.0]), 1.0)
        self.assertEqual(V._sd([]), 0.0)


class DiscriminationTests(unittest.TestCase):
    def test_a_constant_feature_is_flagged_dead(self):
        _, seg, cands = load("talk.srt")
        rows = [SC.score(c, seg) for c in cands]
        by_name = {d.feature: d for d in V.discrimination(rows)}
        # talk.srt contains no silence over 0.8s, so pacing cannot vary on it.
        self.assertTrue(by_name["pacing"].dead)
        self.assertFalse(by_name["self_contained"].dead)

    def test_pacing_comes_alive_on_content_with_real_dead_air(self):
        """R1 left this open: pacing was untested against actual silence."""
        _, seg, cands = load("pauses.srt")
        rows = [SC.score(c, seg) for c in cands]
        by_name = {d.feature: d for d in V.discrimination(rows)}
        self.assertFalse(by_name["pacing"].dead)
        self.assertGreater(by_name["pacing"].sd, 0.3)

    def test_every_feature_is_reported(self):
        _, seg, cands = load("talk.srt")
        rows = [SC.score(c, seg) for c in cands]
        self.assertEqual({d.feature for d in V.discrimination(rows)}, set(V.FEATURES))


class CorrelationTests(unittest.TestCase):
    def test_every_pair_is_covered_once(self):
        _, seg, cands = load("talk.srt")
        rows = [SC.score(c, seg) for c in cands]
        pairs = V.correlations(rows)
        n = len(V.FEATURES)
        self.assertEqual(len(pairs), n * (n - 1) // 2)

    def test_no_two_features_are_duplicates(self):
        """|r| > 0.9 would mean one feature carrying two weights."""
        for fixture in ("talk.srt", "pauses.srt"):
            _, seg, cands = load(fixture)
            rows = [SC.score(c, seg) for c in cands]
            for (a, b), r in V.correlations(rows).items():
                self.assertLess(abs(r), 0.9, f"{a} ~ {b} in {fixture}")


class AblationTests(unittest.TestCase):
    def test_pacing_is_inert_where_there_is_no_dead_air(self):
        _, seg, cands = load("talk.srt")
        by_name = {a.feature: a for a in V.ablation(cands, seg)}
        self.assertTrue(by_name["pacing"].inert)

    def test_pacing_changes_the_selection_where_there_is(self):
        _, seg, cands = load("pauses.srt")
        by_name = {a.feature: a for a in V.ablation(cands, seg)}
        self.assertFalse(by_name["pacing"].inert)

    def test_hook_always_matters(self):
        for fixture in ("talk.srt", "pauses.srt"):
            _, seg, cands = load(fixture)
            by_name = {a.feature: a for a in V.ablation(cands, seg)}
            self.assertFalse(by_name["hook"].inert, fixture)

    def test_overlap_is_a_fraction(self):
        _, seg, cands = load("talk.srt")
        for a in V.ablation(cands, seg):
            self.assertGreaterEqual(a.overlap, 0.0)
            self.assertLessEqual(a.overlap, 1.0)


class BreakageTests(unittest.TestCase):
    def setUp(self):
        _, self.seg, self.cands = load("talk.srt")

    def test_break_opening_shortens_the_first_utterance(self):
        candidate = next(c for c in self.cands if len(c.utterances[0].words) > 4)
        broken = V.break_opening(candidate)
        self.assertIsNotNone(broken)
        self.assertLess(len(broken.utterances[0].words), len(candidate.utterances[0].words))
        self.assertGreater(broken.start, candidate.start)

    def test_break_ending_shortens_the_last_utterance(self):
        candidate = next(c for c in self.cands if len(c.utterances[-1].words) > 4)
        broken = V.break_ending(candidate)
        self.assertIsNotNone(broken)
        self.assertLess(broken.end, candidate.end)
        self.assertFalse(broken.ends_on_punctuation)

    def test_a_one_word_utterance_cannot_be_broken(self):
        one = S.Utterance([self.cands[0].words[0]])
        self.assertIsNone(V.break_opening(S.Candidate(0, 1, [one])))
        self.assertIsNone(V.break_ending(S.Candidate(0, 1, [one])))


class SensitivityTests(unittest.TestCase):
    def test_ties_are_excluded_rather_than_counted_as_losses(self):
        s = V.Sensitivity("x", tested=10, preferred_clean=5, tied=5)
        self.assertEqual(s.rate, 1.0)
        self.assertEqual(s.preferred_broken, 0)

    def test_all_tied_reports_full_rate(self):
        self.assertEqual(V.Sensitivity("x", tested=4, preferred_clean=0, tied=4).rate, 1.0)

    def test_the_scorer_always_prefers_a_clean_opening(self):
        """Regression for R3's worst finding: this was 28%, i.e. backwards.

        R4 took it to 100% by gating the hook on a clean opening and composing
        the self-containment penalties multiplicatively.
        """
        for fixture in ("talk.srt", "pauses.srt"):
            _, seg, cands = load(fixture)
            opening = V.boundary_sensitivity(cands, seg)[0]
            self.assertEqual(opening.rate, 1.0, f"{fixture}: {opening}")

    def test_the_scorer_always_prefers_a_clean_ending(self):
        for fixture in ("talk.srt", "pauses.srt"):
            _, seg, cands = load(fixture)
            ending = V.boundary_sensitivity(cands, seg)[1]
            self.assertEqual(ending.rate, 1.0, fixture)

    def test_a_ten_second_silence_stays_out_of_the_published_clips(self):
        """Measured at R3: at the old pacing weight it ranked second."""
        _, seg, cands = load("pauses.srt")
        chosen = SC.select(SC.rank(cands, seg), count=5)
        for s in chosen:
            words = s.candidate.words
            worst = max((b.start - a.end) for a, b in zip(words, words[1:]))
            self.assertLess(worst, 3.0, f"published clip contains {worst:.1f}s of silence")


class ParameterInfluenceTests(unittest.TestCase):
    """No tuning constant may quietly control the output — see D-8 and D-22."""

    def test_no_constant_is_dominant_on_any_fixture(self):
        for fixture in ("talk.srt", "pauses.srt", "talk_auto.vtt"):
            _, seg, cands = load(fixture)
            for influence in V.parameter_sensitivity(cands, seg):
                self.assertFalse(
                    influence.dominant,
                    f"{fixture}: {influence.constant} moves {influence.mean_churn:.0%}",
                )

    def test_every_swept_constant_exists_on_weights(self):
        fields = set(SC.Weights.__dataclass_fields__)
        self.assertTrue(set(V.SWEEPS).issubset(fields), set(V.SWEEPS) - fields)

    def test_clip_length_is_no_longer_scored_at_all(self):
        """R6: the band is a hard constraint, not a preference."""
        self.assertNotIn("duration_fit", V.FEATURES)
        self.assertNotIn("duration_fit", SC.Weights.__dataclass_fields__)

    def test_influence_is_sorted_worst_first(self):
        _, seg, cands = load("talk.srt")
        churns = [i.mean_churn for i in V.parameter_sensitivity(cands, seg)]
        self.assertEqual(churns, sorted(churns, reverse=True))


class ReportTests(unittest.TestCase):
    def test_report_runs_and_mentions_each_section(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = V.report(FIXTURES / "talk.srt")
        self.assertEqual(code, 0)
        text = out.getvalue()
        for heading in ("DISCRIMINATION", "REDUNDANCY", "ABLATION",
                        "PARAMETER INFLUENCE", "BOUNDARY SENSITIVITY"):
            self.assertIn(heading, text)

    def test_main_requires_an_argument(self):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()):
            import contextlib

            with contextlib.redirect_stderr(err):
                self.assertEqual(V.main([]), 2)
        self.assertIn("usage", err.getvalue())

    def test_main_accepts_several_transcripts(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                V.main([str(FIXTURES / "talk.srt"), str(FIXTURES / "pauses.srt")]), 0
            )


class CapitalisationTests(unittest.TestCase):
    def test_a_normal_transcript_is_detected_as_capitalised(self):
        _, seg, _ = load("talk.srt")
        self.assertTrue(seg.capitalised)

    def test_auto_captions_are_not(self):
        tr = T.load(FIXTURES / "rolling_auto.vtt")
        self.assertFalse(S.segment(tr).capitalised)


if __name__ == "__main__":
    unittest.main()
