"""Word-end estimation and adaptive segmentation.

Both exist because a WebVTT inline timing says only where a word *starts*. Taking
the obvious reading — each word lasts until the next one begins — asserts that
the speaker never pauses, which erases the only sentence signal an unpunctuated
transcript has.
"""

import unittest
from pathlib import Path

from clipper import segment as S
from clipper import transcript as T
from clipper.transcript import Transcript, Word

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def inline_vtt(pairs: list[tuple[str, float]], end: float) -> str:
    """A cue whose words carry inline start timings, as YouTube emits them."""
    head, *rest = pairs
    payload = head[0] + "".join(
        f"<{T.format_timestamp(t)}><c> {w}</c>" for w, t in rest
    )
    return (
        "WEBVTT\nKind: captions\n\n"
        f"{T.format_timestamp(head[1])} --> {T.format_timestamp(end)}\n{payload}\n"
    )


class WordEndEstimationTests(unittest.TestCase):
    def test_silence_between_words_survives_parsing(self):
        """Regression: stretching each word to the next start zeroes every gap."""
        body = inline_vtt(
            [("one", 0.0), ("two", 0.5), ("three", 3.0), ("four", 3.5)], 4.0
        )
        words = T.parse(body, fmt="vtt").words
        gaps = [b.start - a.end for a, b in zip(words, words[1:])]
        self.assertGreater(max(gaps), 1.0, f"expected a visible pause, got {gaps}")

    def test_a_word_never_outlasts_the_next_one_starting(self):
        body = inline_vtt([("a", 0.0), ("b", 0.2), ("c", 0.4), ("d", 0.6)], 1.0)
        words = T.parse(body, fmt="vtt").words
        for a, b in zip(words, words[1:]):
            self.assertLessEqual(a.end, b.start + 1e-9)

    def test_every_word_has_positive_duration(self):
        tr = T.load(FIXTURES / "talk_auto.vtt")
        for w in tr.words:
            self.assertGreater(w.end, w.start)

    def test_a_single_word_is_left_alone(self):
        words = [Word("solo", 1.0, 2.0)]
        self.assertEqual(T.estimate_word_ends(words), words)

    def test_the_inferred_rate_is_bounded(self):
        # Absurdly sparse timings must not imply an absurd word length.
        body = inline_vtt([("a", 0.0), ("b", 600.0), ("c", 1200.0)], 1800.0)
        words = T.parse(body, fmt="vtt").words
        self.assertLess(words[0].duration, 60.0)

    def test_srt_is_untouched_by_estimation(self):
        """SRT has no inline timings, so `_spread` already owns the whole cue."""
        tr = T.load(FIXTURES / "plain.srt")
        gaps = [b.start - a.end for a, b in zip(tr.words, tr.words[1:])]
        self.assertLessEqual(max(g for g in gaps if g < 0.5), 0.5)


class AdaptiveGapTests(unittest.TestCase):
    def bimodal(self, short=0.03, long=0.5, n=10) -> list[Word]:
        words, t = [], 0.0
        for i in range(n * 4):
            words.append(Word(f"w{i}", t, t + 0.25))
            t += 0.25 + (long if i % 4 == 3 else short)
        return words

    def test_it_finds_the_split_between_the_two_populations(self):
        threshold = S.adaptive_gap(self.bimodal())
        self.assertIsNotNone(threshold)
        self.assertGreater(threshold, 0.03)
        self.assertLess(threshold, 0.5)

    def test_too_few_gaps_returns_nothing(self):
        self.assertIsNone(S.adaptive_gap([Word("a", 0, 1), Word("b", 2, 3)]))

    def test_floating_point_dust_is_not_a_pause(self):
        """Contiguous timings differ by ~1e-16; Otsu will split on that if let."""
        words = [Word(f"w{i}", i * 0.35, i * 0.35 + 0.35) for i in range(500)]
        self.assertIsNone(S.adaptive_gap(words))

    def test_a_transcript_with_no_real_pauses_falls_back(self):
        words = [Word(f"w{i}", i * 0.3, i * 0.3 + 0.29) for i in range(200)]
        threshold = S.adaptive_gap(words)
        self.assertTrue(threshold is None or threshold >= S.MIN_GAP_THRESHOLD)

    def test_real_fixtures_all_produce_a_usable_threshold(self):
        for name in ("talk.srt", "talk_auto.vtt", "pauses.srt"):
            seg = S.segment(T.load(FIXTURES / name))
            self.assertGreaterEqual(seg.gap_threshold, S.MIN_GAP_THRESHOLD, name)
            self.assertLess(seg.gap_threshold, 5.0, name)


class AdaptiveSegmentationTests(unittest.TestCase):
    def test_the_threshold_is_reported_and_sits_between_the_populations(self):
        seg = S.segment(T.load(FIXTURES / "talk_auto.vtt"))
        # Intra-phrase gaps are ~0.02s, sentence pauses ~0.44s. The exact value
        # is an implementation detail; landing between them is the contract.
        self.assertGreater(seg.gap_threshold, 0.05)
        self.assertLess(seg.gap_threshold, 0.44)

    def test_an_explicit_gap_overrides_the_adaptive_one(self):
        tr = T.load(FIXTURES / "talk_auto.vtt")
        self.assertEqual(S.segment(tr, gap=2.0).gap_threshold, 2.0)
        self.assertLess(len(S.segment(tr, gap=2.0)), len(S.segment(tr)))

    def test_auto_captions_segment_comparably_to_their_punctuated_twin(self):
        """The paired fixture is the same content; granularity should be similar.

        Before R7 the auto side produced 20 utterances against 62 — a third of
        the boundaries, on the input path this tool exists for.
        """
        clean = len(S.segment(T.load(FIXTURES / "talk.srt")))
        auto = len(S.segment(T.load(FIXTURES / "talk_auto.vtt")))
        self.assertGreater(auto, clean * 0.8)
        self.assertLess(auto, clean * 3.0)

    def test_punctuated_segmentation_is_unaffected(self):
        """Punctuation dominates where it exists; adaptivity must not disturb it."""
        self.assertEqual(len(S.segment(T.load(FIXTURES / "talk.srt"))), 62)
        self.assertEqual(len(S.segment(T.load(FIXTURES / "pauses.srt"))), 24)

    def test_a_gapless_transcript_uses_the_fallback(self):
        words = [Word(f"w{i}", i * 0.35, i * 0.35 + 0.35) for i in range(12_000)]
        seg = S.segment(Transcript(words, []))
        self.assertEqual(seg.gap_threshold, S.DEFAULT_GAP)
        self.assertLess(len(seg), 400)


if __name__ == "__main__":
    unittest.main()
