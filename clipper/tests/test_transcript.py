import unittest
from pathlib import Path

from clipper import transcript as T

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class TimestampTests(unittest.TestCase):
    def test_parses_all_three_shapes(self):
        self.assertAlmostEqual(T.parse_timestamp("00:00:02.520"), 2.520)
        self.assertAlmostEqual(T.parse_timestamp("01:02:03.456"), 3723.456)
        self.assertAlmostEqual(T.parse_timestamp("02:03,456"), 123.456)

    def test_round_trips(self):
        for seconds in (0.0, 2.52, 3723.456, 59.999):
            self.assertAlmostEqual(
                T.parse_timestamp(T.format_timestamp(seconds)), seconds, places=3
            )

    def test_srt_comma_variant(self):
        self.assertEqual(T.format_timestamp(123.456, comma=True), "00:02:03,456")


class RollingAutoCaptionTests(unittest.TestCase):
    """YouTube's auto-captions repeat previously-shown text on every cue."""

    def setUp(self):
        self.tr = T.load(FIXTURES / "rolling_auto.vtt")

    def test_carry_over_text_is_not_duplicated(self):
        self.assertEqual(
            self.tr.text,
            "so the biggest mistake people make with sourdough "
            "is they rush the bulk ferment "
            "and then they blame the starter "
            "it is almost never the starter "
            "very very very rarely",
        )

    def test_each_word_appears_once_per_utterance(self):
        self.assertEqual(self.tr.text.split().count("sourdough"), 1)
        self.assertEqual(self.tr.text.split().count("starter"), 2)

    def test_inline_timings_are_used_verbatim(self):
        by_text = {w.text: w for w in self.tr.words}
        self.assertAlmostEqual(by_text["sourdough"].start, 3.400, places=3)
        self.assertFalse(by_text["sourdough"].interpolated)

    def test_times_are_monotonic_and_non_degenerate(self):
        for a, b in zip(self.tr.words, self.tr.words[1:]):
            self.assertLessEqual(a.start, b.start)
            self.assertGreater(a.end, a.start)

    def test_duration_ends_with_the_last_word_not_the_last_cue(self):
        """A cue often outlasts the word in it; the transcript should not.

        Word ends are estimated from the speaker's inferred pace (see
        `estimate_word_ends`), so the final word ends when it stops being
        spoken rather than when its caption is retired.
        """
        self.assertLess(self.tr.duration, 16.400)
        self.assertGreater(self.tr.duration, 15.0)

    def test_reports_real_word_timings(self):
        self.assertTrue(self.tr.has_real_word_timings)


ORDINALS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"]


def rolling_body(extra: str = "") -> str:
    """A rolling caption file with no inline timings — detectable only by pattern."""
    lines = ["WEBVTT", ""]
    prev = ""
    for i, word in enumerate(ORDINALS):
        line = f"the {word} line"
        payload = f"{prev}\n{line}" if prev else line
        lines += [
            f"{T.format_timestamp(i * 2)} --> {T.format_timestamp(i * 2 + 2)}",
            payload,
            "",
        ]
        prev = line
    return "\n".join(lines) + extra


class GenuineRepetitionTests(unittest.TestCase):
    """De-duplication must not eat a phrase the speaker actually said twice."""

    def test_rolling_file_without_inline_timings_is_detected_and_collapsed(self):
        tr = T.parse(rolling_body(), fmt="vtt")
        self.assertTrue(tr.rolling)
        self.assertEqual(tr.text, " ".join(f"the {w} line" for w in ORDINALS))

    def test_repeat_after_a_pause_survives_even_in_a_rolling_file(self):
        # Same words as the last cue, but spoken 10s later — not contiguous,
        # so it is a real restatement rather than carry-over.
        extra = "\n00:00:26.000 --> 00:00:28.000\nthe eighth line\n"
        tr = T.parse(rolling_body(extra), fmt="vtt")
        self.assertTrue(tr.rolling)
        self.assertTrue(tr.text.endswith("the eighth line the eighth line"))

    def test_short_file_is_never_assumed_rolling(self):
        # Two cues is not enough evidence. Keeping a duplicate is recoverable;
        # deleting real speech is not.
        body = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\nno no no\n\n"
            "00:00:02.000 --> 00:00:04.000\nno no no\n"
        )
        tr = T.parse(body, fmt="vtt")
        self.assertFalse(tr.rolling)
        self.assertEqual(tr.text, "no no no no no no")


class DialectDetectionTests(unittest.TestCase):
    """De-duplication must not run at all on hand-authored captions."""

    def test_professional_captions_keep_an_incidental_overlap(self):
        # "the starter" legitimately ends one cue and opens the next. Only one
        # pair in the file overlaps, so the file is not a rolling dialect.
        body = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\nIt is almost never the starter.\n\n"
            "00:00:02.000 --> 00:00:04.000\nThe starter is fine.\n\n"
            "00:00:04.000 --> 00:00:06.000\nYour schedule is the problem.\n\n"
            "00:00:06.000 --> 00:00:08.000\nGive it another two hours.\n"
        )
        tr = T.parse(body, fmt="vtt")
        self.assertFalse(tr.rolling)
        self.assertIn("the starter. The starter is fine.", tr.text)

    def test_inline_timings_alone_prove_the_dialect(self):
        body = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\nhello<00:00:01.000><c> there</c>\n"
        )
        self.assertTrue(T.parse(body, fmt="vtt").rolling)

    def test_detection_can_be_overridden(self):
        body = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\nno no no\n\n"
            "00:00:02.000 --> 00:00:04.000\nno no no\nreally\n"
        )
        self.assertEqual(T.parse_vtt(body, rolling=False).text, "no no no no no no really")
        self.assertEqual(T.parse_vtt(body, rolling=True).text, "no no no really")

    def test_de_duplication_never_consumes_a_whole_cue(self):
        """The structural guard that replaced the contiguity test at R5.

        Real rolling captions always add words — carry-over exists to scroll the
        previous line under a new one. A cue that is *entirely* a repeat is
        therefore not carry-over, whatever the timing, so it is kept.
        """
        body = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\nno no no\n\n"
            "00:00:02.000 --> 00:00:04.000\nno no no\n"
        )
        self.assertEqual(T.parse_vtt(body, rolling=True).text, "no no no no no no")

    def test_carry_over_survives_a_pause(self):
        """Regression for R5: carry-over is a property of the format, not timing.

        Gating de-duplication on cue contiguity duplicated a whole line at every
        pause longer than the threshold — 8.5% of a normal talk.
        """
        body = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\nthe first line\n\n"
            "00:00:02.000 --> 00:00:04.000\nthe first line\nthe second line\n\n"
            "00:00:12.000 --> 00:00:14.000\nthe second line\nthe third line\n"
        )
        self.assertEqual(
            T.parse_vtt(body, rolling=True).text,
            "the first line the second line the third line",
        )

    def test_rolling_flag_is_set_on_the_fixture(self):
        self.assertTrue(T.load(FIXTURES / "rolling_auto.vtt").rolling)


class SrtTests(unittest.TestCase):
    def setUp(self):
        self.tr = T.load(FIXTURES / "plain.srt")

    def test_text(self):
        self.assertTrue(self.tr.text.startswith("The trick nobody tells you"))
        self.assertTrue(self.tr.text.endswith("when it has doubled."))

    def test_word_timings_are_flagged_as_guesses(self):
        self.assertFalse(self.tr.has_real_word_timings)
        self.assertTrue(all(w.interpolated for w in self.tr.words))

    def test_interpolation_stays_inside_cue_bounds(self):
        first_cue = [w for w in self.tr.words if w.end <= 4.001]
        self.assertGreaterEqual(min(w.start for w in first_cue), 1.0)

    def test_longer_words_get_more_time(self):
        words = {w.text: w for w in self.tr.words}
        self.assertGreater(words["proofing."].duration, words["you"].duration)


class SliceTests(unittest.TestCase):
    def test_slice_selects_by_midpoint(self):
        tr = T.load(FIXTURES / "rolling_auto.vtt")
        window = tr.slice(5.0, 8.0)
        self.assertTrue(window)
        for w in window:
            midpoint = (w.start + w.end) / 2
            self.assertGreaterEqual(midpoint, 5.0)
            self.assertLess(midpoint, 8.0)


class RobustnessTests(unittest.TestCase):
    def test_empty_input(self):
        tr = T.parse("WEBVTT\n\n", fmt="vtt")
        self.assertEqual(tr.words, [])
        self.assertEqual(tr.duration, 0.0)

    def test_note_and_style_blocks_are_skipped(self):
        body = (
            "WEBVTT\n\n"
            "NOTE this is a comment\nwith a second line\n\n"
            "STYLE\n::cue { color: peachpuff }\n\n"
            "1\n00:00:00.000 --> 00:00:01.000\nhello\n"
        )
        self.assertEqual(T.parse(body, fmt="vtt").text, "hello")

    def test_cue_identifiers_are_not_treated_as_text(self):
        body = "WEBVTT\n\nintro-cue\n00:00:00.000 --> 00:00:01.000\nhello\n"
        self.assertEqual(T.parse(body, fmt="vtt").text, "hello")

    def test_crlf_line_endings(self):
        body = "WEBVTT\r\n\r\n00:00:00.000 --> 00:00:01.000\r\nhello there\r\n"
        self.assertEqual(T.parse(body, fmt="vtt").text, "hello there")

    def test_zero_length_cue_does_not_crash(self):
        body = "WEBVTT\n\n00:00:05.000 --> 00:00:05.000\nblip\n"
        tr = T.parse(body, fmt="vtt")
        self.assertEqual(tr.text, "blip")
        self.assertGreater(tr.words[0].end, tr.words[0].start)

    def test_format_sniffing(self):
        srt = "1\n00:00:01,000 --> 00:00:02,000\nhi\n"
        self.assertEqual(T.parse(srt).text, "hi")
        vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nhi\n"
        self.assertEqual(T.parse(vtt).text, "hi")


if __name__ == "__main__":
    unittest.main()
