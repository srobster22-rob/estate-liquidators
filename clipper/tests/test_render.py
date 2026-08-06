import shutil
import tempfile
import unittest
from pathlib import Path

from clipper import captions as C
from clipper import render as R
from clipper.transcript import Word

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
requires_ffmpeg = unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")


class FilterGraphTests(unittest.TestCase):
    def test_fill_crops_to_the_canvas(self):
        graph = R.build_filter("fill")
        self.assertIn("crop=1080:1920", graph)
        self.assertIn("force_original_aspect_ratio=increase", graph)
        self.assertNotIn("gblur", graph)

    def test_pad_never_crops(self):
        graph = R.build_filter("pad")
        self.assertIn("pad=1080:1920", graph)
        self.assertIn("force_original_aspect_ratio=decrease", graph)
        self.assertNotIn("crop=1080:1920,", graph.split("pad=")[0])

    def test_blur_keeps_the_whole_frame_in_the_foreground(self):
        graph = R.build_filter("blur")
        self.assertIn("split=2", graph)
        self.assertIn("gblur", graph)
        self.assertIn("overlay=(W-w)/2:(H-h)/2", graph)
        # the foreground is contained, not cropped
        self.assertIn("[fg]scale=1080:1920:force_original_aspect_ratio=decrease", graph)

    def test_every_layout_ends_on_the_output_pad(self):
        for layout in R.LAYOUTS:
            self.assertTrue(R.build_filter(layout).endswith("[vout]"), layout)

    def test_unknown_layout_is_rejected(self):
        with self.assertRaises(ValueError):
            R.build_filter("cinematic")

    def test_subtitles_are_attached_only_when_asked(self):
        self.assertIn("subtitles=", R.build_filter("fill", ass_path="/tmp/x.ass"))
        self.assertNotIn("subtitles=", R.build_filter("fill"))

    def test_custom_canvas_size(self):
        graph = R.build_filter("fill", width=720, height=1280)
        self.assertIn("crop=720:1280", graph)


class PathEscapingTests(unittest.TestCase):
    def test_colons_are_escaped(self):
        self.assertEqual(R.escape_filter_path("/a/b:c.ass"), "/a/b\\:c.ass")

    def test_apostrophes_are_recognised_as_unrepresentable(self):
        """ffmpeg cannot escape a quote inside a single-quoted filter value."""
        self.assertFalse(R.is_filter_safe("/a/it's.ass"))
        self.assertTrue(R.is_filter_safe("/a/[odd], really.ass"))

    def test_brackets_and_commas_are_safe_inside_quotes(self):
        self.assertEqual(R.escape_filter_path("/a/[x], y.ass"), "/a/[x], y.ass")


@requires_ffmpeg
class CommandTests(unittest.TestCase):
    def test_trim_is_expressed_as_start_and_duration(self):
        cmd = R.build_command("in.mp4", "out.mp4", start=10.0, end=25.5)
        self.assertEqual(cmd[cmd.index("-ss") + 1], "10.000")
        self.assertEqual(cmd[cmd.index("-t") + 1], "15.500")

    def test_seek_precedes_the_input(self):
        cmd = R.build_command("in.mp4", "out.mp4", start=1.0, end=2.0)
        self.assertLess(cmd.index("-ss"), cmd.index("-i"))

    def test_silent_source_disables_audio(self):
        cmd = R.build_command("in.mp4", "out.mp4", start=0, end=1, has_audio=False)
        self.assertIn("-an", cmd)
        self.assertNotIn("aac", cmd)

    def test_audio_source_maps_the_first_track(self):
        cmd = R.build_command("in.mp4", "out.mp4", start=0, end=1, has_audio=True)
        self.assertIn("0:a:0", cmd)

    def test_backwards_clip_is_rejected(self):
        with self.assertRaises(ValueError):
            R.build_command("in.mp4", "out.mp4", start=5.0, end=5.0)

    def test_faststart_is_set_for_streaming(self):
        cmd = R.build_command("in.mp4", "out.mp4", start=0, end=1)
        self.assertIn("+faststart", cmd)


@requires_ffmpeg
class EndToEndTests(unittest.TestCase):
    """Exercises the real encoder against an ffmpeg-synthesised source."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="clipper-test-"))
        cls.source = R.synth_source(cls.tmp / "src.mp4", duration=8, width=640, height=360, fps=15)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_probe_reads_geometry(self):
        info = R.probe(self.source)
        self.assertAlmostEqual(info.duration, 8.0, delta=0.5)
        self.assertEqual((info.width, info.height), (640, 360))
        self.assertTrue(info.has_audio)

    def test_probe_rejects_a_non_media_file(self):
        junk = self.tmp / "junk.mp4"
        junk.write_text("not a video")
        with self.assertRaises(R.RenderError):
            R.probe(junk)

    def test_render_produces_a_vertical_clip_of_the_right_length(self):
        out = R.render_clip(self.source, self.tmp / "a.mp4", start=1.0, end=4.0, layout="fill")
        info = R.probe(out)
        self.assertEqual((info.width, info.height), (1080, 1920))
        self.assertAlmostEqual(info.duration, 3.0, delta=0.35)
        self.assertTrue(info.has_audio)

    def test_every_layout_encodes(self):
        for layout in R.LAYOUTS:
            out = R.render_clip(
                self.source, self.tmp / f"{layout}.mp4", start=0.5, end=2.0, layout=layout
            )
            self.assertEqual((R.probe(out).width, R.probe(out).height), (1080, 1920))

    def test_captions_are_burned_and_the_ass_file_is_cleaned_up(self):
        words = [Word("hello", 1.0, 1.6), Word("there", 1.6, 2.4)]
        ass = C.build_ass(words, offset=1.0, duration=2.0)
        out = R.render_clip(
            self.source, self.tmp / "cap.mp4", start=1.0, end=3.0, ass=ass, layout="fill"
        )
        self.assertTrue(out.exists())
        self.assertFalse(out.with_suffix(".ass").exists())

    def test_silent_source_renders(self):
        silent = R.synth_source(self.tmp / "silent.mp4", duration=4, width=320, height=240, audio=False)
        self.assertFalse(R.probe(silent).has_audio)
        out = R.render_clip(silent, self.tmp / "s.mp4", start=0.0, end=2.0)
        self.assertFalse(R.probe(out).has_audio)

    def test_a_path_with_awkward_characters_still_burns_captions(self):
        odd = self.tmp / "it's [odd], really"
        odd.mkdir(parents=True, exist_ok=True)
        ass = C.build_ass([Word("hi", 0.2, 0.9)], duration=1.5)
        out = R.render_clip(self.source, odd / "c.mp4", start=0.0, end=1.5, ass=ass, layout="fill")
        self.assertTrue(out.exists())

    def test_failure_surfaces_ffmpeg_stderr(self):
        with self.assertRaises(R.RenderError) as ctx:
            R.render_clip(self.tmp / "nope.mp4", self.tmp / "x.mp4", start=0, end=1)
        self.assertTrue(str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
