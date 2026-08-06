import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from clipper import framing as F
from clipper import render as R

HAVE_FFMPEG = bool(shutil.which("ffmpeg"))
requires_ffmpeg = unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")

W, H = 640, 360
BOX_W, BOX_H = 80, 120


def synth(path: Path, x_expr: str, *, duration: float = 4.0, rate: int = 12) -> Path:
    """A dark frame with a light box on it, optionally animated.

    The box is composited with `overlay`, not `drawbox`. In `drawbox` the
    variable `t` is *thickness*, not time — an animated-looking expression there
    silently renders a static box, which is how a whole round of motion
    measurements once came back meaningless.
    """
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"color=c=#202020:s={W}x{H}:r={rate}:d={duration}",
            "-f", "lavfi", "-i", f"color=c=white:s={BOX_W}x{BOX_H}:d={duration}",
            "-filter_complex", f"[0][1]overlay=x='{x_expr}':y=120",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-pix_fmt", "yuv420p", str(path),
        ],
        check=True,
        capture_output=True,
    )
    return path


class ConcentrationTests(unittest.TestCase):
    def test_uniform_scores_zero(self):
        self.assertAlmostEqual(F.concentration([1.0] * 64), 0.0, places=6)

    def test_a_single_spike_scores_one(self):
        values = [0.0] * 64
        values[30] = 1.0
        self.assertAlmostEqual(F.concentration(values), 1.0, places=6)

    def test_empty_and_zero_are_safe(self):
        self.assertEqual(F.concentration([]), 0.0)
        self.assertEqual(F.concentration([0.0] * 10), 0.0)

    def test_partial_clustering_lands_between(self):
        values = [1.0] * 64
        for i in range(30, 38):
            values[i] = 6.0
        self.assertGreater(F.concentration(values), 0.1)
        self.assertLess(F.concentration(values), 0.9)


class WindowMathTests(unittest.TestCase):
    def test_sixteen_nine_to_nine_sixteen_keeps_about_a_third(self):
        self.assertEqual(F.window_columns(16 / 9, 9 / 16, width=64), 20)

    def test_a_square_source_keeps_more(self):
        self.assertGreater(F.window_columns(1.0, 9 / 16, width=64), 20)

    def test_a_source_narrower_than_the_target_keeps_everything(self):
        self.assertEqual(F.window_columns(0.4, 9 / 16, width=64), 64)

    def test_degenerate_aspect_is_safe(self):
        self.assertEqual(F.window_columns(0.0, 9 / 16, width=64), 64)


class BestWindowTests(unittest.TestCase):
    """Pure tests over hand-built energy profiles."""

    def spike_at(self, index: int, width: int = 64) -> list[float]:
        values = [0.01] * width
        for i in range(index - 2, index + 3):
            if 0 <= i < width:
                values[i] = 1.0
        return values

    def test_aims_at_a_right_hand_subject(self):
        aim = F.best_window(self.spike_at(48), 20)
        self.assertFalse(aim.fell_back)
        self.assertAlmostEqual(aim.center, 48.5 / 64, delta=0.03)

    def test_aims_at_a_left_hand_subject(self):
        aim = F.best_window(self.spike_at(12), 20)
        self.assertFalse(aim.fell_back)
        self.assertAlmostEqual(aim.center, 12.5 / 64, delta=0.03)

    def test_a_flat_profile_falls_back_to_the_centre(self):
        aim = F.best_window([1.0] * 64, 20)
        self.assertTrue(aim.fell_back)
        self.assertEqual(aim.center, 0.5)
        self.assertLess(aim.confidence, F.MIN_CONFIDENCE)

    def test_all_zero_falls_back(self):
        self.assertTrue(F.best_window([0.0] * 64, 20).fell_back)

    def test_a_subject_at_the_edge_is_not_dragged_inward(self):
        aim = F.best_window(self.spike_at(2), 20)
        self.assertLess(aim.center, 0.15)

    def test_window_wider_than_the_frame_falls_back(self):
        self.assertTrue(F.best_window([1.0] * 10, 20).fell_back)

    def test_centre_is_always_inside_the_frame(self):
        for index in (0, 5, 32, 60, 63):
            aim = F.best_window(self.spike_at(index), 20)
            self.assertGreaterEqual(aim.center, 0.0)
            self.assertLessEqual(aim.center, 1.0)


class ChooseLayoutTests(unittest.TestCase):
    def test_confident_aim_crops(self):
        self.assertEqual(F.choose_layout(F.Aim(0.8, 0.7)), "fill")

    def test_unlocatable_subject_letterboxes(self):
        self.assertEqual(F.choose_layout(F.Aim(0.5, 0.0, fell_back=True)), "blur")


class CropExpressionTests(unittest.TestCase):
    def test_offset_is_expressed_over_input_width(self):
        expr = R.crop_expression(0.8, 1080, 1920)
        self.assertIn("in_w*0.8000", expr)
        self.assertIn("clip(", expr)

    def test_window_is_kept_inside_the_frame(self):
        self.assertIn("0,in_w-out_w", R.crop_expression(0.99, 1080, 1920))

    def test_out_of_range_aims_are_clamped(self):
        self.assertIn("in_w*1.0000", R.crop_expression(5.0, 1080, 1920))
        self.assertIn("in_w*0.0000", R.crop_expression(-5.0, 1080, 1920))

    def test_only_fill_uses_the_aim(self):
        for layout in ("blur", "pad"):
            self.assertNotIn("in_w*0.8000", R.build_filter(layout, aim=0.8))
        self.assertIn("in_w*0.8000", R.build_filter("fill", aim=0.8))


@requires_ffmpeg
class AimEndToEndTests(unittest.TestCase):
    """Ground truth is known because the fixture is synthesised."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="clipper-aim-"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def aim_for(self, name: str, x_expr: str) -> F.Aim:
        src = synth(self.tmp / f"{name}.mp4", x_expr)
        return F.aim(
            src, start=0, duration=4,
            source_width=W, source_height=H,
            target_width=1080, target_height=1920,
        )

    def test_static_subject_on_the_right(self):
        truth = (460 + BOX_W / 2) / W
        aim = self.aim_for("right", "460")
        self.assertFalse(aim.fell_back)
        self.assertAlmostEqual(aim.center, truth, delta=0.04)

    def test_static_subject_on_the_left(self):
        truth = (90 + BOX_W / 2) / W
        aim = self.aim_for("left", "90")
        self.assertFalse(aim.fell_back)
        self.assertAlmostEqual(aim.center, truth, delta=0.04)

    def test_gently_swaying_subject_is_still_located(self):
        truth = (440 + 20 + BOX_W / 2) / W
        aim = self.aim_for("sway", "440+10*t")
        self.assertFalse(aim.fell_back)
        self.assertAlmostEqual(aim.center, truth, delta=0.05)

    def test_subject_crossing_the_frame_falls_back(self):
        """A static aim cannot follow a walk, and says so instead of guessing."""
        aim = self.aim_for("walk", "20+130*t")
        self.assertTrue(aim.fell_back)
        self.assertEqual(aim.center, 0.5)

    def test_confidence_separates_aimable_from_unaimable(self):
        """The threshold sits in a measured gap, not next to either population."""
        aimable = self.aim_for("still", "460").confidence
        unaimable = self.aim_for("crossing", "20+130*t").confidence
        self.assertGreater(aimable, F.MIN_CONFIDENCE * 1.4)
        self.assertLess(unaimable, F.MIN_CONFIDENCE * 0.7)

    def test_a_slow_drift_is_still_aimable(self):
        aim = self.aim_for("drift", "300+30*t")
        self.assertFalse(aim.fell_back)

    def test_empty_frame_falls_back(self):
        src = self.tmp / "flat.mp4"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
             "-i", f"color=c=gray:s={W}x{H}:r=12:d=4", "-c:v", "libx264",
             "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p", str(src)],
            check=True, capture_output=True,
        )
        aim = F.aim(src, start=0, duration=4, source_width=W, source_height=H,
                    target_width=1080, target_height=1920)
        self.assertTrue(aim.fell_back)

    def test_motion_noise_alone_does_not_move_the_aim(self):
        """A static shot's compression noise must not outvote the real signal.

        Unit-mass normalising each signal made a pure-noise motion field carry
        its full weight; the reliability factor is what stops that.
        """
        src = synth(self.tmp / "static_noise.mp4", "460")
        frames = F.sample_luma(src, start=0, duration=4)
        motion = F.column_energy(frames, motion_weight=1.0, detail_weight=0.0)
        detail = F.column_energy(frames, motion_weight=0.0, detail_weight=1.0)
        self.assertLess(F.concentration(motion), 0.2)
        self.assertGreater(F.concentration(detail), 0.8)

    def test_sampling_returns_frames_of_the_expected_size(self):
        src = synth(self.tmp / "size.mp4", "300")
        frames = F.sample_luma(src, start=0, duration=4)
        self.assertTrue(frames)
        self.assertTrue(all(len(f) == F.GRID_W * F.GRID_H for f in frames))

    def test_sampling_a_missing_file_raises(self):
        with self.assertRaises(R.RenderError):
            F.sample_luma(self.tmp / "nope.mp4", start=0, duration=1)

    def test_aimed_render_keeps_an_offcentre_subject_in_frame(self):
        """The end of the argument: a centred crop loses this subject entirely."""
        src = synth(self.tmp / "offcentre.mp4", "530", duration=3)
        aim = F.aim(src, start=0, duration=3, source_width=W, source_height=H,
                    target_width=1080, target_height=1920)
        out = R.render_clip(src, self.tmp / "aimed.mp4", start=0, end=2,
                            layout="fill", aim=aim.center)
        # The subject is bright; a frame that kept it has a much higher maximum.
        kept = F.sample_luma(out, start=0, duration=2)
        centred_out = R.render_clip(src, self.tmp / "centred.mp4", start=0, end=2,
                                    layout="fill", aim=0.5)
        lost = F.sample_luma(centred_out, start=0, duration=2)
        self.assertGreater(max(kept[0]), max(lost[0]) + 40)


if __name__ == "__main__":
    unittest.main()
