import unittest
from pathlib import Path

from clipper import score as SC
from clipper import segment as S
from clipper import transcript as T
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

    def test_discourse_marker_is_only_a_nick(self):
        score = SC.self_containment("So the biggest mistake is rushing.")
        self.assertGreater(score, 0.8)
        self.assertLess(score, 1.0)

    def test_marker_then_referent_stacks(self):
        self.assertLess(SC.self_containment("And that is why it works."), 0.3)

    def test_short_opening_fragment_is_punished(self):
        whole = SC.self_containment("All fine.", opening_words=2, utterance_count=1)
        fragment = SC.self_containment("All fine.", opening_words=2, utterance_count=4)
        self.assertLess(fragment, whole)

    def test_never_goes_negative(self):
        self.assertGreaterEqual(SC.self_containment("and but so it that"), 0.0)


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


class DurationFitTests(unittest.TestCase):
    def test_peaks_at_the_ideal(self):
        self.assertEqual(SC.duration_fit(32.0, ideal=32.0, tolerance=28.0), 1.0)

    def test_decays_symmetrically(self):
        lo = SC.duration_fit(20.0, ideal=32.0, tolerance=28.0)
        hi = SC.duration_fit(44.0, ideal=32.0, tolerance=28.0)
        self.assertAlmostEqual(lo, hi)

    def test_never_negative(self):
        self.assertEqual(SC.duration_fit(500.0, ideal=32.0, tolerance=28.0), 0.0)


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
            {"hook", "self_contained", "closure", "duration_fit", "pacing", "payoff"},
        )

    def test_explain_is_readable(self):
        self.assertIn("hook=", SC.rank(self.cands, self.seg)[0].explain())


class WeightsTests(unittest.TestCase):
    def test_round_trip(self):
        import tempfile

        w = SC.Weights(hook=9.0, ideal_duration=45.0)
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
        short = SC.rank(cands, seg, SC.Weights(duration_fit=40.0, ideal_duration=16.0))
        long = SC.rank(cands, seg, SC.Weights(duration_fit=40.0, ideal_duration=58.0))
        self.assertLess(short[0].duration, long[0].duration)


if __name__ == "__main__":
    unittest.main()
