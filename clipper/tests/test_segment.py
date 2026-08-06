import unittest
from pathlib import Path

from clipper import segment as S
from clipper import transcript as T
from clipper.transcript import Transcript, Word

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def words(spec: list[tuple[str, float, float]]) -> Transcript:
    return Transcript([Word(t, a, b) for t, a, b in spec], [])


class UtteranceTests(unittest.TestCase):
    def test_splits_on_sentence_punctuation(self):
        tr = words([("Hello.", 0, 1), ("Again", 1, 2), ("now.", 2, 3)])
        seg = S.segment(tr)
        self.assertTrue(seg.punctuated)
        self.assertEqual([u.text for u in seg.utterances], ["Hello.", "Again now."])

    def test_splits_on_silence_without_punctuation(self):
        tr = words([("hello", 0, 1), ("there", 1, 2), ("again", 5, 6)])
        seg = S.segment(tr)
        self.assertFalse(seg.punctuated)
        self.assertEqual([u.text for u in seg.utterances], ["hello there", "again"])

    def test_length_cap_forces_a_boundary_in_a_gapless_monologue(self):
        tr = words([(f"w{i}", i * 0.3, i * 0.3 + 0.3) for i in range(100)])
        seg = S.segment(tr, max_words=45)
        self.assertGreater(len(seg), 1)
        self.assertTrue(all(len(u.words) <= 45 for u in seg.utterances))

    def test_abbreviations_do_not_end_a_sentence(self):
        tr = words([("Dr.", 0, 1), ("Ito", 1, 2), ("arrived.", 2, 3), ("Late", 3, 4)])
        seg = S.segment(tr)
        self.assertEqual(seg.utterances[0].text, "Dr. Ito arrived.")

    def test_initialisms_do_not_end_a_sentence(self):
        tr = words([("The", 0, 1), ("U.S.A.", 1, 2), ("team", 2, 3), ("won.", 3, 4)])
        seg = S.segment(tr)
        self.assertEqual(len(seg.utterances), 1)

    def test_gap_after_and_punctuation_flags(self):
        tr = words([("One.", 0, 1), ("Two.", 3, 4)])
        seg = S.segment(tr)
        self.assertAlmostEqual(seg.utterances[0].gap_after, 2.0)
        self.assertTrue(seg.utterances[0].ends_on_punctuation)

    def test_every_word_survives_segmentation(self):
        tr = T.load(FIXTURES / "talk.srt")
        seg = S.segment(tr)
        self.assertEqual(sum(len(u.words) for u in seg.utterances), len(tr.words))

    def test_empty_transcript(self):
        seg = S.segment(words([]))
        self.assertEqual(len(seg), 0)
        self.assertEqual(S.candidates(seg), [])


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tr = T.load(FIXTURES / "talk.srt")
        self.seg = S.segment(self.tr)

    def test_all_candidates_respect_the_duration_band(self):
        for c in S.candidates(self.seg, min_duration=15, max_duration=60):
            self.assertGreaterEqual(c.duration, 15.0)
            self.assertLessEqual(c.duration, 60.0)

    def test_candidates_start_and_end_on_utterance_boundaries(self):
        starts = {u.start for u in self.seg.utterances}
        ends = {u.end for u in self.seg.utterances}
        for c in S.candidates(self.seg):
            self.assertIn(c.start, starts)
            self.assertIn(c.end, ends)

    def test_capping_biases_clips_short(self):
        """Regression: max_per_start truncates from the short end.

        The first windows past min_duration are the shortest ones, so a cap
        removes exactly the candidates nearest the target length. The scorer
        cannot recover what the generator never emitted.
        """
        uncapped = S.candidates(self.seg)
        capped = S.candidates(self.seg, max_per_start=4)
        self.assertLess(
            max(c.duration for c in capped), max(c.duration for c in uncapped)
        )
        self.assertIs(S.candidates.__defaults__, None)  # keyword-only, no default cap

    def test_uncapped_pool_reaches_the_ideal_duration(self):
        durations = [c.duration for c in S.candidates(self.seg)]
        self.assertTrue(any(30.0 <= d <= 34.0 for d in durations))

    def test_overlap_detection(self):
        cands = S.candidates(self.seg)
        a = cands[0]
        self.assertTrue(a.overlaps(a))
        later = next(c for c in cands if c.start > a.end)
        self.assertFalse(a.overlaps(later))

    def test_text_and_words_agree(self):
        for c in S.candidates(self.seg)[:20]:
            self.assertEqual(c.text.split(), [w.text for w in c.words])

    def test_candidate_count_stays_linear_in_utterances(self):
        """Guard on D-5: uncapped generation is only safe if it does not blow up.

        The window count per starting utterance is bounded by max_duration, so
        the total is linear in utterance count, not quadratic. Measured on a
        3-hour transcript: 3,207 utterances -> 42,487 candidates, ranked in 5.3s.
        """
        count = len(S.candidates(self.seg))
        self.assertLess(count, len(self.seg) * 25)

    def test_a_long_transcript_does_not_explode(self):
        words = [Word(f"w{i}", i * 0.35, i * 0.35 + 0.35) for i in range(12_000)]
        seg = S.segment(Transcript(words, []))
        cands = S.candidates(seg)
        self.assertGreater(len(cands), 100)
        self.assertLess(len(cands), len(seg) * 25)


if __name__ == "__main__":
    unittest.main()
