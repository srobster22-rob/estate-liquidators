import shutil
import tempfile
import unittest
from pathlib import Path

from clipper import sources


class UrlTests(unittest.TestCase):
    def test_recognises_urls(self):
        for target in ("https://youtu.be/x", "http://a.b/c", "www.youtube.com/watch?v=x"):
            self.assertTrue(sources.looks_like_url(target), target)

    def test_paths_are_not_urls(self):
        for target in ("video.mp4", "/tmp/a.mp4", "./b.mkv", "C:/x.mp4"):
            self.assertFalse(sources.looks_like_url(target), target)


class TranscriptDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="clipper-src-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def touch(self, name: str) -> Path:
        path = self.tmp / name
        path.write_text("x")
        return path

    def test_finds_a_sibling_subtitle(self):
        video = self.touch("talk.mp4")
        subs = self.touch("talk.srt")
        self.assertEqual(sources.find_transcript(video), subs)

    def test_finds_a_language_suffixed_subtitle(self):
        video = self.touch("talk.mp4")
        subs = self.touch("talk.en.vtt")
        self.assertEqual(sources.find_transcript(video), subs)

    def test_returns_none_when_there_is_nothing(self):
        self.assertIsNone(sources.find_transcript(self.touch("lonely.mp4")))

    def test_ignores_unrelated_files(self):
        video = self.touch("talk.mp4")
        self.touch("other.srt")
        self.assertIsNone(sources.find_transcript(video))

    def test_glob_metacharacters_in_the_stem_do_not_match_everything(self):
        video = self.touch("a[1].mp4")
        self.touch("b.srt")
        self.assertIsNone(sources.find_transcript(video))

    def test_glob_escape_is_single_pass(self):
        # Regression: escaping "[" to "[[]" and then escaping "]" re-processes
        # the bracket the first substitution introduced, corrupting the pattern.
        self.assertEqual(sources.glob_escape("a[1]*?"), "a[[]1][*][?]")
        self.assertNotIn("[[[", sources.glob_escape("[[["))


class LocalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="clipper-src-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_missing_video_is_an_error(self):
        with self.assertRaises(sources.IngestError):
            sources.local(self.tmp / "nope.mp4")

    def test_missing_explicit_transcript_is_an_error(self):
        video = self.tmp / "a.mp4"
        video.write_text("x")
        with self.assertRaises(sources.IngestError):
            sources.local(video, self.tmp / "nope.srt")

    def test_explicit_transcript_wins_over_a_sibling(self):
        video = self.tmp / "a.mp4"
        video.write_text("x")
        (self.tmp / "a.srt").write_text("x")
        chosen = self.tmp / "chosen.vtt"
        chosen.write_text("x")
        self.assertEqual(sources.local(video, chosen).transcript, chosen)

    def test_resolve_dispatches_to_local_for_a_path(self):
        video = self.tmp / "a.mp4"
        video.write_text("x")
        subs = self.tmp / "a.srt"
        subs.write_text("x")
        got = sources.resolve(str(video), self.tmp)
        self.assertEqual(got.video, video)
        self.assertEqual(got.transcript, subs)
        self.assertFalse(got.automatic)


class DownloadCommandTests(unittest.TestCase):
    """The command is checked; the network call it makes is not — see the module docstring."""

    def setUp(self):
        if not shutil.which("yt-dlp"):
            self.skipTest("yt-dlp not installed")
        self.tmp = Path(tempfile.mkdtemp(prefix="clipper-src-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_requests_both_manual_and_automatic_subtitles(self):
        cmd = sources.build_download_command("https://example/v", self.tmp)
        self.assertIn("--write-subs", cmd)
        self.assertIn("--write-auto-subs", cmd)

    def test_normalises_subtitles_to_vtt(self):
        cmd = sources.build_download_command("https://example/v", self.tmp)
        self.assertEqual(cmd[cmd.index("--convert-subs") + 1], "vtt")

    def test_height_cap_is_applied_to_the_format_selector(self):
        cmd = sources.build_download_command("https://example/v", self.tmp, max_height=720)
        selector = cmd[cmd.index("-f") + 1]
        self.assertIn("height<=720", selector)

    def test_playlists_are_refused(self):
        self.assertIn("--no-playlist", sources.build_download_command("https://e/v", self.tmp))

    def test_output_template_lands_in_the_workdir(self):
        cmd = sources.build_download_command("https://example/v", self.tmp)
        self.assertTrue(cmd[cmd.index("-o") + 1].startswith(str(self.tmp)))


if __name__ == "__main__":
    unittest.main()
