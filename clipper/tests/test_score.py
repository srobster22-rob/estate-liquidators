import unittest
from pathlib import Path

from clipper import score as SC
from clipper import segment as S
from clipper import transcript as T
from clipper import validate as V
from clipper.transcript import Transcript, Word

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def candidate_from(spec: list[tuple[str, float, float]], **kw) -> S.Candidate:
    tr = Transcript([Word(t, a, b) for t, a, b in spec], [])
    seg = S.segment(tr, **kw)
    return S.Candidate(0, len(seg), seg.utterances), seg


class HookTests(unittest.TestCase):
    def test_recognises_promise_openers(self):
        for text in (
            "Here's the thing nobody tells you about proofing",
            "The biggest mistake people make is rushing",
            "Why does this keep happening to your loaf",
            "Stop kneading the dough so hard",
        ):
            self.assertGreater(SC.hook_strength(text), 0.0, text)

    def test_flat_narration_scores_zero(self):
        self.assertEqual(SC.hook_strength("and we carried on to the next room"), 0.0)

    def test_only_the_opening_counts(self):
        buried = "and we carried on for a while " * 3 + "here's the secret"
        self.assertEqual(SC.hook_strength(buried), 0.0)


class SelfContainmentTests(unittest.TestCase):
    def test_clean_opener_is_perfect(self):
        self.assertEqual(SC.self_containment("Dough measures temperature."), 1.0)

    def test_dangling_referent_is_punished_hard(self):
        self.assertLess(SC.self_containment("It is almost never the starter."), 0.4)

    def test_discourse_marker_is_not_penalised(self):
        """Reversed at R3. A leading "so" is evidence of a sentence *start*.

        Penalising it was the reason the scorer preferred a deliberately broken
        clip to a clean one 72% of the time.
        """
        self.assertEqual(SC.self_containment("So the biggest mistake is rushing."), 1.0)
        self.assertEqual(SC.self_containment("Okay, so today I want to talk about it."), 1.0)

    def test_marker_is_skipped_so_the_referent_behind_it_is_still_caught(self):
        self.assertAlmostEqual(SC.self_containment("And that is why it works."), 0.3)

    def test_mid_sentence_start_scores_zero_when_capitals_are_meaningful(self):
        self.assertEqual(
            SC.self_containment("not your starter, it is your schedule.", expect_capital=True),
            0.0,
        )

    def test_mid_sentence_penalty_beats_the_dangling_referent_penalty(self):
        """A fragment must never outscore a whole sentence, however weak."""
        fragment = SC.self_containment("not your starter.", expect_capital=True)
        whole_but_dangling = SC.self_containment("And it is not your starter.", expect_capital=True)
        self.assertLess(fragment, whole_but_dangling)

    def test_lower_case_start_is_ignored_when_captions_have_no_capitals(self):
        # Auto-captions are entirely lower-case; the signal means nothing there.
        self.assertEqual(
            SC.self_containment("dough measures temperature", expect_capital=False), 1.0
        )

    def test_short_opening_fragment_is_punished(self):
        whole = SC.self_containment("All fine.", opening_words=2, utterance_count=1)
        fragment = SC.self_containment("All fine.", opening_words=2, utterance_count=4)
        self.assertLess(fragment, whole)

    def test_never_goes_negative(self):
        self.assertGreaterEqual(SC.self_containment("and but so it that"), 0.0)

    def test_stacked_penalties_stay_distinguishable_from_disqualification(self):
        """Regression: subtracting made both of these clamp to exactly 0.0.

        Once two clips read as an identical zero, an irrelevant 0.011 difference
        in duration_fit decided between them — and picked the broken one.
        """
        bad = SC.self_containment(
            "That distinction matters.", opening_words=3, utterance_count=4, expect_capital=True
        )
        disqualified = SC.self_containment(
            "distinction matters.", opening_words=2, utterance_count=4, expect_capital=True
        )
        self.assertGreater(bad, 0.0)
        self.assertEqual(disqualified, 0.0)
        self.assertGreater(bad, disqualified)

    def test_penalties_compose_multiplicatively(self):
        self.assertAlmostEqual(
            SC.self_containment("That thing.", opening_words=2, utterance_count=3),
            (1 - SC.DANGLING_PENALTY) * (1 - SC.FRAGMENT_PENALTY),
        )


class HookGatingTests(unittest.TestCase):
    """A promise you joined halfway through was never made to you."""

    def test_mid_sentence_opening_earns_no_hook_credit(self):
        tr = T.load(FIXTURES / "talk.srt")
        seg = S.segment(tr)
        cands = S.candidates(seg)
        candidate = next(c for c in cands if SC.hook_strength(c.text) > 0)
        broken = V.break_opening(candidate)
        self.assertIsNotNone(broken)
        self.assertTrue(SC.opens_mid_sentence(broken.text, expect_capital=seg.capitalised))
        self.assertEqual(SC.score(broken, seg).features["hook"], 0.0)

    def test_clean_opening_keeps_its_hook(self):
        tr = T.load(FIXTURES / "talk.srt")
        seg = S.segment(tr)
        cands = S.candidates(seg)
        best = SC.rank(cands, seg)[0]
        self.assertFalse(SC.opens_mid_sentence(best.text, expect_capital=seg.capitalised))

    def test_detection_needs_capitals_to_mean_something(self):
        self.assertTrue(SC.opens_mid_sentence("not your starter", expect_capital=True))
        self.assertFalse(SC.opens_mid_sentence("not your starter", expect_capital=False))
        self.assertFalse(SC.opens_mid_sentence("Not your starter", expect_capital=True))


class PacingTests(unittest.TestCase):
    """Dead air inside a clip, which the old average-rate feature could not see."""

    def test_continuous_speech_is_perfect(self):
        cand, _ = candidate_from([(f"w{i}", i * 0.4, i * 0.4 + 0.4) for i in range(30)])
        self.assertEqual(SC.pacing(cand, max_silence=1.2), 1.0)

    def test_a_long_silence_costs_points(self):
        spec = [(f"a{i}", i * 0.4, i * 0.4 + 0.4) for i in range(10)]
        spec += [(f"b{i}", 8.0 + i * 0.4, 8.0 + i * 0.4 + 0.4) for i in range(10)]
        cand, _ = candidate_from(spec, gap=10.0)  # keep it one utterance
        self.assertLess(SC.pacing(cand, max_silence=1.2), 0.5)

    def test_same_word_count_and_duration_still_differ(self):
        """The measure must be the worst gap, not the average rate."""
        even = [(f"w{i}", i * 1.0, i * 1.0 + 0.4) for i in range(10)]
        clumped = [(f"w{i}", i * 0.4, i * 0.4 + 0.4) for i in range(9)] + [("w9", 9.0, 9.4)]
        a, _ = candidate_from(even, gap=10.0)
        b, _ = candidate_from(clumped, gap=10.0)
        self.assertAlmostEqual(a.duration, b.duration, places=1)
        self.assertEqual(len(a.words), len(b.words))
        self.assertNotEqual(SC.pacing(a, max_silence=1.2), SC.pacing(b, max_silence=1.2))


class ClosureTests(unittest.TestCase):
    """Smooth evidence, not a threshold test — see D-22."""

    def cand(self, gap, ends_on_punctuation=False):
        w = [Word("a", 0.0, 1.0), Word("b.", 1.0, 2.0)]
        return S.Candidate(0, 1, [S.Utterance(w, gap_after=gap,
                                              ends_on_punctuation=ends_on_punctuation)])

    def test_no_evidence_scores_zero(self):
        self.assertEqual(SC.closure(self.cand(0.0), closing_gap=0.8, punctuated=False), 0.0)

    def test_silence_alone_can_exceed_a_half(self):
        """The old form capped unpunctuated closure at 0.5, halving its range."""
        self.assertGreater(SC.closure(self.cand(1.2), closing_gap=0.8, punctuated=False), 0.5)

    def test_it_is_strictly_increasing_in_the_gap(self):
        vals = [SC.closure(self.cand(g), closing_gap=0.8, punctuated=False)
                for g in (0.0, 0.2, 0.5, 0.8, 1.1, 2.0, 5.0)]
        self.assertEqual(vals, sorted(vals))
        self.assertEqual(len(set(vals)), len(vals))

    def test_there_is_no_kink_at_the_parameter(self):
        """A threshold put a discontinuity in the slope exactly at closing_gap.

        Measured at R6: that kink sat on the median of the real gap distribution,
        so nudging the parameter reclassified a third of all candidates at once.
        """
        step = 0.01

        def slope(g):
            a = SC.closure(self.cand(g), closing_gap=0.8, punctuated=False)
            b = SC.closure(self.cand(g + step), closing_gap=0.8, punctuated=False)
            return (b - a) / step

        # A smooth function still curves, so linearity is the wrong assertion.
        # What must not happen is the curvature *spiking at the parameter*.
        at_parameter = abs(slope(0.81) - slope(0.79))
        elsewhere = abs(slope(0.41) - slope(0.39))
        self.assertLess(at_parameter, elsewhere * 3.0)

    def test_punctuation_and_silence_combine_as_a_soft_or(self):
        gap_only = SC.closure(self.cand(0.8), closing_gap=0.8, punctuated=False)
        mark_only = SC.closure(self.cand(0.0, True), closing_gap=0.8, punctuated=True)
        both = SC.closure(self.cand(0.8, True), closing_gap=0.8, punctuated=True)
        self.assertGreater(both, gap_only)
        self.assertGreater(both, mark_only)
        self.assertLessEqual(both, 1.0)

    def test_punctuation_is_ignored_when_the_transcript_has_none(self):
        self.assertEqual(
            SC.closure(self.cand(0.5, True), closing_gap=0.8, punctuated=False),
            SC.closure(self.cand(0.5, False), closing_gap=0.8, punctuated=False),
        )

    def test_stays_within_bounds(self):
        for gap in (0.0, 0.5, 5.0, 500.0):
            for punct in (False, True):
                v = SC.closure(self.cand(gap, punct), closing_gap=0.8, punctuated=punct)
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.tr = T.load(FIXTURES / "talk.srt")
        self.seg = S.segment(self.tr)
        self.cands = S.candidates(self.seg)

    def test_ranking_is_descending(self):
        ranked = SC.rank(self.cands, self.seg)
        self.assertEqual([s.total for s in ranked], sorted((s.total for s in ranked), reverse=True))

    def test_selection_is_non_overlapping_and_ordered(self):
        chosen = SC.select(SC.rank(self.cands, self.seg), count=5)
        self.assertLessEqual(len(chosen), 5)
        for a, b in zip(chosen, chosen[1:]):
            self.assertLessEqual(a.end, b.start)

    def test_selection_honours_padding(self):
        chosen = SC.select(SC.rank(self.cands, self.seg), count=5, pad=2.0)
        for a, b in zip(chosen, chosen[1:]):
            self.assertGreaterEqual(b.start - a.end, 0.0)

    def test_the_best_moment_in_the_fixture_is_chosen(self):
        """The temperature-not-time line is the actual thesis of the talk."""
        chosen = SC.select(SC.rank(self.cands, self.seg), count=5)
        self.assertTrue(any("Dough measures temperature" in s.text for s in chosen))

    def test_every_feature_is_reported(self):
        s = SC.rank(self.cands, self.seg)[0]
        self.assertEqual(
            set(s.features),
            {"hook", "self_contained", "closure", "pacing"},
        )

    def test_explain_is_readable(self):
        self.assertIn("hook=", SC.rank(self.cands, self.seg)[0].explain())


class WeightsTests(unittest.TestCase):
    def test_round_trip(self):
        import tempfile

        w = SC.Weights(hook=9.0, pacing=4.5)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            path = fh.name
        w.save(path)
        self.assertEqual(SC.Weights.load(path), w)

    def test_unknown_keys_are_ignored(self):
        import json
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"hook": 2.0, "not_a_weight": 1}, fh)
            path = fh.name
        self.assertEqual(SC.Weights.load(path).hook, 2.0)

    def test_weights_actually_change_the_ranking(self):
        tr = T.load(FIXTURES / "talk.srt")
        seg = S.segment(tr)
        cands = S.candidates(seg)
        only = lambda name: SC.Weights(
            **{f: (50.0 if f == name else 0.0)
               for f in ("hook", "self_contained", "closure", "pacing")}
        )
        a = [(s.start, s.end) for s in SC.rank(cands, seg, only("hook"))[:10]]
        b = [(s.start, s.end) for s in SC.rank(cands, seg, only("closure"))[:10]]
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
