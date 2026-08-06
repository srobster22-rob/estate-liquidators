"""The auto-caption regime — the input this tool actually exists for.

`talk.srt` and `talk_auto.vtt` are a **paired** fixture: identical words and
timings, rendered as clean subtitles and as YouTube-style ASR output. Any
difference the pipeline shows between them is caused by the caption regime and
nothing else, which is what makes the comparison worth anything.
"""

import re
import unittest
from pathlib import Path

from clipper import score as SC
from clipper import segment as S
from clipper import transcript as T
from clipper import validate as V

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
_PUNCT = re.compile(r"[^\w' ]+")


def load(name: str):
    tr = T.load(FIXTURES / name)
    seg = S.segment(tr)
    return tr, seg, S.candidates(seg)


class PairedFixtureTests(unittest.TestCase):
    """The two fixtures must carry exactly the same words."""

    def setUp(self):
        self.clean, self.clean_seg, _ = load("talk.srt")
        self.auto, self.auto_seg, _ = load("talk_auto.vtt")

    def test_no_words_are_gained_or_lost(self):
        """Regression for R5: rolling carry-over duplicated a line at every pause.

        De-duplication was gated on cue contiguity, but carry-over is a property
        of the caption format, not of the timing. Every gap over 0.5s leaked a
        whole line through — 573 words became 622.
        """
        expected = [_PUNCT.sub("", w.text).lower() for w in self.clean.words]
        actual = [w.text for w in self.auto.words]
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(actual, expected)

    def test_the_regimes_are_detected_correctly(self):
        self.assertTrue(self.clean_seg.punctuated)
        self.assertTrue(self.clean_seg.capitalised)
        self.assertFalse(self.auto_seg.punctuated)
        self.assertFalse(self.auto_seg.capitalised)
        self.assertTrue(self.auto.rolling)

    def test_auto_captions_carry_real_word_timings(self):
        """The inline <c> timings survive de-duplication, so highlighting works."""
        self.assertTrue(self.auto.has_real_word_timings)
        self.assertFalse(self.clean.has_real_word_timings)

    def test_both_regimes_span_the_same_time(self):
        self.assertAlmostEqual(self.auto.duration, self.clean.duration, delta=0.5)


class GapBeforeTests(unittest.TestCase):
    def test_utterances_record_the_silence_that_precedes_them(self):
        _, seg, _ = load("talk_auto.vtt")
        self.assertEqual(seg.utterances[0].gap_before, 0.0)
        for previous, current in zip(seg.utterances, seg.utterances[1:]):
            self.assertAlmostEqual(current.gap_before, previous.gap_after, places=6)

    def test_a_candidate_exposes_its_own_opening_gap(self):
        _, seg, cands = load("talk_auto.vtt")
        for c in cands[:20]:
            self.assertEqual(c.gap_before, c.utterances[0].gap_before)


class MidSentenceDetectionTests(unittest.TestCase):
    def test_capitals_take_priority_when_available(self):
        self.assertTrue(
            SC.opens_mid_sentence("lower start", expect_capital=True, gap_before=5.0)
        )
        self.assertFalse(
            SC.opens_mid_sentence("Upper start", expect_capital=True, gap_before=0.0)
        )

    def test_silence_is_the_fallback_when_capitals_are_absent(self):
        self.assertTrue(
            SC.opens_mid_sentence("no capitals here", expect_capital=False, gap_before=0.0)
        )
        self.assertFalse(
            SC.opens_mid_sentence("no capitals here", expect_capital=False, gap_before=0.9)
        )

    def test_no_signal_at_all_means_no_accusation(self):
        self.assertFalse(SC.opens_mid_sentence("anything", expect_capital=False))

    def test_punctuated_transcripts_do_not_use_the_gap_signal(self):
        """Two sentences inside one cue are contiguous — gap 0.0 at a clean break.

        Using gaps on a punctuated transcript would reject good openings wholesale.
        """
        _, seg, cands = load("talk.srt")
        zero_gap = [c for c in cands if c.gap_before == 0.0]
        self.assertTrue(zero_gap, "expected some within-cue sentence boundaries")
        clean = [
            c for c in zero_gap
            if not SC.opens_mid_sentence(c.text, expect_capital=seg.capitalised,
                                         gap_before=c.gap_before)
        ]
        self.assertTrue(clean, "capitalised transcripts must ignore gap_before")


class PayoffGatingTests(unittest.TestCase):
    """A conclusion you were cut away from never landed."""

    def test_truncating_an_ending_cannot_raise_the_payoff_score(self):
        for fixture in ("talk.srt", "talk_auto.vtt", "pauses.srt"):
            _, seg, cands = load(fixture)
            for c in cands[:60]:
                broken = V.break_ending(c)
                if broken is None:
                    continue
                self.assertLessEqual(
                    SC.score(broken, seg).features["payoff"],
                    SC.score(c, seg).features["payoff"],
                    f"{fixture}: truncation raised payoff",
                )

    def test_a_clip_cut_mid_sentence_is_detected(self):
        _, seg, cands = load("talk.srt")
        candidate = cands[0]
        broken = V.break_ending(candidate)
        self.assertTrue(SC.ends_mid_sentence(broken, punctuated=seg.punctuated))


class RegimeComparisonTests(unittest.TestCase):
    """What the auto-caption regime costs, stated as a number rather than a worry."""

    def sensitivity(self, fixture):
        _, seg, cands = load(fixture)
        opening, ending = V.boundary_sensitivity(cands, seg)
        return opening.rate, ending.rate

    def test_punctuated_transcripts_are_perfect(self):
        for fixture in ("talk.srt", "pauses.srt"):
            self.assertEqual(self.sensitivity(fixture), (1.0, 1.0), fixture)

    def test_auto_captions_are_worse_but_not_broken(self):
        """Floors, not targets. If these rise, tighten them; if they fall, something
        regressed the one input path that matters most."""
        opening, ending = self.sensitivity("talk_auto.vtt")
        self.assertGreater(opening, 0.70)
        self.assertGreater(ending, 0.75)

    def test_the_auto_regime_still_produces_usable_clips(self):
        _, seg, cands = load("talk_auto.vtt")
        chosen = SC.select(SC.rank(cands, seg), count=3)
        self.assertEqual(len(chosen), 3)
        for s in chosen:
            self.assertGreaterEqual(s.duration, 15.0)
            self.assertLessEqual(s.duration, 60.0)
        for a, b in zip(chosen, chosen[1:]):
            self.assertLessEqual(a.end, b.start)


if __name__ == "__main__":
    unittest.main()
