import unittest
from pathlib import Path

from clipper import captions as C
from clipper import transcript as T
from clipper.transcript import Word

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def evenly(texts: list[str], step: float = 0.5, interpolated: bool = False) -> list[Word]:
    return [
        Word(t, i * step, i * step + step, interpolated) for i, t in enumerate(texts)
    ]


class FormattingTests(unittest.TestCase):
    def test_ass_time_uses_centiseconds(self):
        self.assertEqual(C.ass_time(0), "0:00:00.00")
        self.assertEqual(C.ass_time(3723.456), "1:02:03.46")
        self.assertEqual(C.ass_time(-5), "0:00:00.00")

    def test_ass_colour_is_byte_reversed(self):
        self.assertEqual(C.ass_colour("#FFD400"), "&H0000D4FF")
        self.assertEqual(C.ass_colour("#FFFFFF"), "&H00FFFFFF")
        self.assertEqual(C.ass_colour("#000000", alpha=0x80), "&H80000000")

    def test_ass_colour_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            C.ass_colour("#FFF")

    def test_escape_neutralises_markup(self):
        out = C.escape_text("a {\\b1}bold\\N line")
        self.assertNotIn("{", out)
        self.assertNotIn("}", out)
        self.assertNotIn("\\", out)


class ChunkTests(unittest.TestCase):
    def test_respects_word_limit(self):
        style = C.CaptionStyle(max_words=3, max_chars=999, max_gap=99)
        lines = C.chunk(evenly(["a"] * 10), style)
        self.assertTrue(all(len(l) <= 3 for l in lines))

    def test_respects_character_limit(self):
        style = C.CaptionStyle(max_words=99, max_chars=12, max_gap=99)
        lines = C.chunk(evenly(["abcde", "fghij", "klmno"]), style)
        self.assertGreater(len(lines), 1)

    def test_breaks_on_a_pause(self):
        words = [Word("a", 0, 0.4), Word("b", 0.5, 0.9), Word("c", 3.0, 3.4)]
        style = C.CaptionStyle(max_words=99, max_chars=999, max_gap=0.55)
        self.assertEqual([[w.text for w in l] for l in C.chunk(words, style)], [["a", "b"], ["c"]])

    def test_every_word_is_kept_exactly_once(self):
        words = evenly([f"w{i}" for i in range(40)])
        flat = [w for line in C.chunk(words, C.CaptionStyle()) for w in line]
        self.assertEqual(flat, words)

    def test_empty_input(self):
        self.assertEqual(C.chunk([], C.CaptionStyle()), [])


class BuildAssTests(unittest.TestCase):
    def test_has_the_required_sections(self):
        ass = C.build_ass(evenly(["hello", "there"]))
        for section in ("[Script Info]", "[V4+ Styles]", "[Events]"):
            self.assertIn(section, ass)
        self.assertIn("PlayResX: 1080", ass)
        self.assertIn("PlayResY: 1920", ass)

    def test_style_row_field_count_matches_the_format_row(self):
        ass = C.build_ass(evenly(["hi"]))
        fmt = next(l for l in ass.splitlines() if l.startswith("Format: Name"))
        style = next(l for l in ass.splitlines() if l.startswith("Style: "))
        self.assertEqual(
            len(fmt.split(":", 1)[1].split(",")), len(style.split(":", 1)[1].split(","))
        )

    def test_guessed_timings_disable_highlighting(self):
        """Highlighting a word whose position was interpolated lies to the eye."""
        words = evenly(["one", "two", "three", "four"], interpolated=True)
        ass = C.build_ass(words)
        self.assertEqual(C.dialogue_count(ass), 1)
        self.assertNotIn("\\c&H0000D4FF", ass)

    def test_real_timings_enable_per_word_highlighting(self):
        words = evenly(["one", "two", "three", "four"], interpolated=False)
        ass = C.build_ass(words)
        self.assertEqual(C.dialogue_count(ass), 4)
        self.assertIn("\\c", ass)

    def test_highlight_can_be_forced_off(self):
        words = evenly(["one", "two"], interpolated=False)
        ass = C.build_ass(words, C.CaptionStyle(highlight=False))
        self.assertEqual(C.dialogue_count(ass), 1)

    def test_offset_rebases_to_clip_start(self):
        words = [Word("x", 100.0, 101.0), Word("y", 101.0, 102.0)]
        ass = C.build_ass(words, offset=100.0)
        self.assertIn("0:00:00.00", ass)
        self.assertNotIn("0:01:40", ass)

    def test_duration_clamps_the_tail(self):
        words = [Word("x", 0, 1), Word("y", 1, 20)]
        ass = C.build_ass(words, duration=5.0)
        for line in ass.splitlines():
            if line.startswith("Dialogue:"):
                end = line.split(",")[2]
                self.assertLessEqual(C.ass_time(5.0), C.ass_time(6.0))
                self.assertLessEqual(end, "0:00:05.00")

    def test_no_zero_or_negative_length_events(self):
        words = [Word("a", 5.0, 5.0), Word("b", 5.0, 5.0), Word("c", 5.0, 6.0)]
        for line in C.build_ass(words).splitlines():
            if line.startswith("Dialogue:"):
                _, start, end = line.split(",")[0:3]
                self.assertLess(start, end)

    def test_highlight_events_within_a_line_do_not_overlap(self):
        words = evenly(["one", "two", "three"], interpolated=False)
        style = C.CaptionStyle(max_words=3, max_chars=999)
        events = [
            l.split(",") for l in C.build_ass(words, style).splitlines()
            if l.startswith("Dialogue:")
        ]
        for a, b in zip(events, events[1:]):
            self.assertLessEqual(a[2], b[1])

    def test_spoken_text_survives_intact(self):
        words = evenly(["Dough", "measures", "temperature."], interpolated=True)
        style = C.CaptionStyle(max_chars=99)
        self.assertIn("Dough measures temperature.", C.build_ass(words, style))

    def test_a_phrase_over_the_line_limit_is_split_not_dropped(self):
        # 27 characters against the default 26-character line.
        words = evenly(["Dough", "measures", "temperature."], interpolated=True)
        ass = C.build_ass(words)
        self.assertEqual(C.dialogue_count(ass), 2)
        self.assertIn("Dough measures", ass)
        self.assertIn("temperature.", ass)

    def test_highlighted_text_keeps_every_word_on_every_event(self):
        """Colour overrides interleave the phrase, but no word may go missing."""
        words = evenly(["Dough", "measures", "temperature."], interpolated=False)
        style = C.CaptionStyle(max_chars=99)
        events = [
            l.split(",,", 1)[1] for l in C.build_ass(words, style).splitlines()
            if l.startswith("Dialogue:")
        ]
        self.assertEqual(len(events), 3)
        for body in events:
            for token in ("Dough", "measures", "temperature."):
                self.assertIn(token, body)

    def test_real_transcript_round_trip(self):
        tr = T.load(FIXTURES / "rolling_auto.vtt")
        ass = C.build_ass(tr.words, offset=0.0, duration=tr.duration)
        self.assertGreater(C.dialogue_count(ass), len(tr.words) // 4)
        self.assertIn("sourdough", ass)

    def test_empty_words_still_produce_a_valid_file(self):
        ass = C.build_ass([])
        self.assertIn("[Events]", ass)
        self.assertEqual(C.dialogue_count(ass), 0)


if __name__ == "__main__":
    unittest.main()
