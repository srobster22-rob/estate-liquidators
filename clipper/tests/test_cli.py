import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from clipper import cli
from clipper import score as SC
from clipper import transcript as T

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class SlugifyTests(unittest.TestCase):
    def test_lowercases_and_hyphenates(self):
        self.assertEqual(cli.slugify("Here's the Thing!"), "here-s-the-thing")

    def test_collapses_runs_and_trims(self):
        self.assertEqual(cli.slugify("  a --- b  "), "a-b")

    def test_truncates(self):
        self.assertLessEqual(len(cli.slugify("word " * 50)), 48)

    def test_never_returns_empty(self):
        self.assertEqual(cli.slugify("!!!"), "clip")


class PickTests(unittest.TestCase):
    def setUp(self):
        self.tr = T.load(FIXTURES / "talk.srt")

    def test_returns_the_requested_number(self):
        picks, _ = cli.pick(
            self.tr, count=3, min_duration=15, max_duration=60, weights=None
        )
        self.assertEqual(len(picks), 3)

    def test_respects_the_duration_band(self):
        picks, _ = cli.pick(
            self.tr, count=5, min_duration=20, max_duration=30, weights=None
        )
        for p in picks:
            self.assertGreaterEqual(p.duration, 20.0)
            self.assertLessEqual(p.duration, 30.0)

    def test_impossible_band_yields_nothing(self):
        picks, _ = cli.pick(
            self.tr, count=5, min_duration=500, max_duration=600, weights=None
        )
        self.assertEqual(picks, [])

    def test_custom_weights_are_applied(self):
        """A weights file must be able to change what gets published."""
        default, _ = cli.pick(
            self.tr, count=1, min_duration=15, max_duration=60, weights=None
        )
        hook_only, _ = cli.pick(
            self.tr, count=1, min_duration=15, max_duration=60,
            weights=SC.Weights(hook=50.0, self_contained=0.0, closure=0.0,
                               pacing=0.0, payoff=0.0),
        )
        self.assertNotEqual(
            (default[0].start, default[0].end), (hook_only[0].start, hook_only[0].end)
        )

    def test_the_band_is_a_hard_constraint_not_a_preference(self):
        """R6 removed duration scoring; the band alone controls clip length."""
        picks, _ = cli.pick(self.tr, count=3, min_duration=40, max_duration=60, weights=None)
        for p in picks:
            self.assertGreaterEqual(p.duration, 40.0)
            self.assertLessEqual(p.duration, 60.0)


class MainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="clipper-cli-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.video = self.tmp / "lesson.mp4"
        self.video.write_text("not really a video, but --dry-run never opens it")
        shutil.copy(FIXTURES / "talk.srt", self.tmp / "lesson.srt")

    def run_cli(self, *argv) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_dry_run_succeeds_and_finds_the_sibling_transcript(self):
        code, out, _ = self.run_cli(str(self.video), "--dry-run", "-n", "3")
        self.assertEqual(code, 0)
        self.assertIn("573 words", out)
        self.assertEqual(out.count("→"), 3)

    def test_dry_run_reports_the_feature_breakdown(self):
        _, out, _ = self.run_cli(str(self.video), "--dry-run", "-n", "1")
        for feature in ("hook", "self_contained", "closure", "pacing"):
            self.assertIn(feature, out)

    def test_interpolated_timings_are_announced(self):
        _, out, _ = self.run_cli(str(self.video), "--dry-run", "-n", "1")
        self.assertIn("interpolated", out)

    def test_json_manifest_is_valid_and_complete(self):
        code, out, _ = self.run_cli(str(self.video), "--dry-run", "--json", "-n", "2")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(len(data["clips"]), 2)
        clip = data["clips"][0]
        self.assertLess(clip["start"], clip["end"])
        self.assertAlmostEqual(clip["duration"], clip["end"] - clip["start"], places=2)
        self.assertIn("hook", clip["features"])
        self.assertIsNone(clip["file"])

    def test_clips_do_not_overlap(self):
        _, out, _ = self.run_cli(str(self.video), "--dry-run", "--json", "-n", "5")
        clips = json.loads(out)["clips"]
        for a, b in zip(clips, clips[1:]):
            self.assertLessEqual(a["end"], b["start"])

    def test_missing_video_is_reported(self):
        code, _, err = self.run_cli(str(self.tmp / "absent.mp4"), "--dry-run")
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)

    def test_missing_transcript_is_reported(self):
        lonely = self.tmp / "lonely.mp4"
        lonely.write_text("x")
        code, _, err = self.run_cli(str(lonely), "--dry-run")
        self.assertEqual(code, 2)
        self.assertIn("no transcript", err)

    def test_impossible_duration_band_is_reported(self):
        code, _, err = self.run_cli(
            str(self.video), "--dry-run", "--min-duration", "500", "--max-duration", "600"
        )
        self.assertEqual(code, 1)
        self.assertIn("no candidate clip", err)

    def test_empty_transcript_is_reported(self):
        empty = self.tmp / "empty.mp4"
        empty.write_text("x")
        (self.tmp / "empty.vtt").write_text("WEBVTT\n\n")
        code, _, err = self.run_cli(str(empty), "--dry-run")
        self.assertEqual(code, 2)
        self.assertIn("zero words", err)

    def test_explicit_transcript_flag(self):
        lonely = self.tmp / "lonely.mp4"
        lonely.write_text("x")
        code, out, _ = self.run_cli(
            str(lonely), "--transcript", str(self.tmp / "lesson.srt"), "--dry-run", "-n", "1"
        )
        self.assertEqual(code, 0)
        self.assertIn("573 words", out)


class ParserTests(unittest.TestCase):
    def test_defaults(self):
        args = cli.build_parser().parse_args(["v.mp4"])
        self.assertEqual((args.count, args.layout, args.out), (5, "auto", "clips"))
        self.assertEqual((args.min_duration, args.max_duration), (15.0, 60.0))

    def test_layout_is_constrained(self):
        with self.assertRaises(SystemExit):
            cli.build_parser().parse_args(["v.mp4", "--layout", "cinematic"])


if __name__ == "__main__":
    unittest.main()
