"""Does any of this survive content the author did not write?

Through R7 every measurement in the project came from two source texts, both
instructional monologues in the same voice. `interview.srt` (two speakers,
question-and-answer, interruptions) and `rambling.srt` (unstructured, digressive,
explicitly without a conclusion) exist to break that monoculture.

They found two things immediately: the scorer generalises, and two lexicon
patterns that "never fired" were untested rather than useless.
"""

import unittest
from pathlib import Path

from clipper import score as SC
from clipper import segment as S
from clipper import transcript as T
from clipper import validate as V

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

#: Every fixture. `talk_auto.vtt` is `talk.srt` in ASR clothing, so it is not an
#: independent text — INDEPENDENT is the set that actually tests generalisation.
ALL = ("talk.srt", "pauses.srt", "talk_auto.vtt", "interview.srt", "rambling.srt")
INDEPENDENT = ("talk.srt", "pauses.srt", "interview.srt", "rambling.srt")


def load(name: str):
    tr = T.load(FIXTURES / name)
    seg = S.segment(tr)
    return tr, seg, S.candidates(seg)


class CoverageTests(unittest.TestCase):
    def test_the_fixtures_are_actually_different(self):
        """A guard on the guard: near-duplicate fixtures would prove nothing."""
        texts = {}
        for name in INDEPENDENT:
            tr, _, _ = load(name)
            texts[name] = set(SC._tokens(tr.text))
        names = list(texts)
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                overlap = len(texts[a] & texts[b]) / min(len(texts[a]), len(texts[b]))
                self.assertLess(overlap, 0.5, f"{a} and {b} share {overlap:.0%} of vocabulary")

    def test_every_fixture_yields_usable_clips(self):
        for name in ALL:
            _, seg, cands = load(name)
            chosen = SC.select(SC.rank(cands, seg), count=3)
            self.assertGreaterEqual(len(chosen), 2, name)
            for s in chosen:
                self.assertGreaterEqual(s.duration, 15.0, name)
                self.assertLessEqual(s.duration, 60.0, name)
            for a, b in zip(chosen, chosen[1:]):
                self.assertLessEqual(a.end, b.start, name)

    def test_dialogue_does_not_break_segmentation(self):
        _, seg, _ = load("interview.srt")
        self.assertTrue(seg.punctuated)
        self.assertGreater(len(seg), 20)

    def test_unstructured_speech_still_produces_something(self):
        """rambling.srt says outright that it has no conclusion."""
        _, seg, cands = load("rambling.srt")
        self.assertTrue(cands)
        self.assertTrue(SC.select(SC.rank(cands, seg), count=3))


class QualityTests(unittest.TestCase):
    """The scorer should find the quotable line, not merely a valid window."""

    def best_texts(self, name, count=3):
        _, seg, cands = load(name)
        return [s.text for s in SC.select(SC.rank(cands, seg), count=count)]

    def test_it_finds_the_hook_in_an_interview(self):
        self.assertTrue(
            any("A spreadsheet" in t for t in self.best_texts("interview.srt")),
            "expected the spreadsheet answer, the strongest moment in the piece",
        )

    def test_it_finds_the_one_quotable_line_in_a_ramble(self):
        self.assertTrue(
            any("rollback plan is fiction" in t for t in self.best_texts("rambling.srt"))
        )


class RobustnessAcrossTextsTests(unittest.TestCase):
    def test_boundary_sensitivity_is_perfect_everywhere(self):
        for name in ALL:
            _, seg, cands = load(name)
            opening, ending = V.boundary_sensitivity(cands, seg)
            self.assertEqual(opening.rate, 1.0, f"{name} openings: {opening}")
            self.assertEqual(ending.rate, 1.0, f"{name} endings: {ending}")

    def test_no_tuning_constant_is_dominant_on_any_text(self):
        for name in ALL:
            _, seg, cands = load(name)
            for influence in V.parameter_sensitivity(cands, seg):
                self.assertFalse(
                    influence.dominant,
                    f"{name}: {influence.constant} moves {influence.mean_churn:.0%}",
                )

    def test_no_feature_is_beyond_rescue_on_every_text(self):
        """The standard that deleted `payoff` at R8.

        A feature that cannot change the published selection at *any* weight, on
        *any* text, is not under-weighted — it is finished.
        """
        datasets = []
        for name in INDEPENDENT:
            _, seg, cands = load(name)
            datasets.append((name, cands, seg))
        for verdict in V.earns_its_place(datasets):
            self.assertFalse(
                verdict.beyond_rescue,
                f"{verdict.feature} is inert at every weight on all "
                f"{verdict.tested_on} texts",
            )

    def test_pacing_is_inert_only_where_its_hazard_is_absent(self):
        """Distinguishes a working safety feature from a useless one.

        `pacing` earns its keep on exactly the text that contains dead air, and
        does nothing on the ones that do not. That is correct behaviour, and the
        reason "inert on most texts" is a flag rather than a verdict.
        """
        for name in INDEPENDENT:
            _, seg, cands = load(name)
            worst = max(
                max((b.start - a.end) for a, b in zip(c.words, c.words[1:]))
                for c in cands
            )
            inert = {a.feature: a for a in V.ablation(cands, seg)}["pacing"].inert
            if worst > SC.Weights().max_silence:
                self.assertFalse(inert, f"{name} has {worst:.1f}s of silence but pacing is inert")
            else:
                self.assertTrue(inert, f"{name} has no dead air but pacing changed the output")


class GroundTruthTests(unittest.TestCase):
    """The paired fixture is the only answer key this project has."""

    def setUp(self):
        self.clean = S.segment(T.load(FIXTURES / "talk.srt"))
        self.auto = S.segment(T.load(FIXTURES / "talk_auto.vtt"))

    def test_the_measure_is_exact_against_itself(self):
        perfect = V.boundary_agreement(self.clean, self.clean)
        self.assertEqual((perfect.precision, perfect.recall), (1.0, 1.0))

    def test_the_auto_path_finds_most_real_boundaries(self):
        """Recall floor. Under-segmentation was R7's failure — 20 utterances
        against 62 — and this is what stops it coming back quietly."""
        self.assertGreater(V.boundary_agreement(self.auto, self.clean).recall, 0.55)

    def test_the_auto_path_over_segments_and_we_know_by_how_much(self):
        """Measured at R9: 42% precision. Recorded rather than tuned away — the
        reference is synthetic, so optimising against it would fit the generator
        rather than speech."""
        agreement = V.boundary_agreement(self.auto, self.clean)
        self.assertGreater(agreement.precision, 0.30)
        self.assertLess(agreement.precision, 0.90)

    def test_both_regimes_choose_the_same_moments(self):
        """Same content, two caption formats: the picks should largely agree.

        Measured at R9: 5 of 5 clean picks have an overlapping auto counterpart,
        81% mean temporal overlap.
        """
        def picks(seg):
            return SC.select(SC.rank(S.candidates(seg), seg), count=5)

        clean, auto = picks(self.clean), picks(self.auto)
        overlaps = []
        for c in clean:
            best = max(
                (max(0.0, min(c.end, a.end) - max(c.start, a.start)) / c.duration
                 for a in auto),
                default=0.0,
            )
            overlaps.append(best)
        self.assertGreaterEqual(sum(1 for o in overlaps if o > 0.5), 4)
        self.assertGreater(sum(overlaps) / len(overlaps), 0.6)


class LexiconEvidenceTests(unittest.TestCase):
    """A pattern that fires on no fixture is untested, not useless."""

    def firing_counts(self, names):
        counts = [0] * len(SC.HOOK_PATTERNS)
        for name in names:
            _, seg, cands = load(name)
            for c in cands:
                opening = " ".join(SC._tokens(c.text)[:12])
                for i, rx in enumerate(SC._HOOK_RE):
                    if rx.search(opening):
                        counts[i] += 1
        return counts

    def test_adding_independent_texts_revives_dormant_patterns(self):
        """Measured at R8: two hook patterns fired only once new prose was added.

        This is the argument against pruning a lexicon on thin evidence — the
        same reasoning that would have deleted them was wrong.
        """
        narrow = self.firing_counts(("talk.srt", "pauses.srt", "talk_auto.vtt"))
        wide = self.firing_counts(ALL)
        revived = [i for i, (n, w) in enumerate(zip(narrow, wide)) if n == 0 and w > 0]
        self.assertTrue(revived, "expected some pattern to be untested rather than useless")

    def test_the_numeral_pattern_needs_digits_to_exist(self):
        """It fired on nothing until a fixture used digits instead of words."""
        digits = SC.HOOK_PATTERNS.index(r"\b\d+\b")
        self.assertGreater(self.firing_counts(("rambling.srt",))[digits], 0)


if __name__ == "__main__":
    unittest.main()
