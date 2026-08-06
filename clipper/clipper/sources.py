"""Ingest: get a video file and a transcript from a URL or a local path.

This is the one module that cannot be tested where it was written — the sandbox
this was built in has no route to YouTube, so **every yt-dlp invocation below is
inferred from its documented interface rather than observed working**. Treat the
flag choices as a starting point that needs one real run to confirm.

Everything the module returns is a plain `Ingest` of local paths, so the rest of
the pipeline neither knows nor cares whether a download happened.
"""

from __future__ import annotations

import glob
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"}
SUBTITLE_SUFFIXES = {".vtt", ".srt"}


class IngestError(RuntimeError):
    pass


@dataclass(frozen=True)
class Ingest:
    video: Path
    transcript: Path | None
    #: True when the transcript came from automatic speech recognition, which
    #: means no punctuation and occasional invented words.
    automatic: bool = False


def looks_like_url(target: str) -> bool:
    return target.startswith(("http://", "https://", "www."))


def find_transcript(video: Path) -> Path | None:
    """Look for a subtitle file sitting next to a video, by stem match."""
    directory = video.parent
    candidates = [
        p
        for p in directory.glob(f"{glob_escape(video.stem)}*")
        if p.suffix.lower() in SUBTITLE_SUFFIXES
    ]
    if not candidates:
        return None
    # Prefer a manual track over an automatic one; yt-dlp does not distinguish
    # them by filename, so this only reflects format preference.
    candidates.sort(key=lambda p: (p.suffix.lower() != ".srt", len(p.name)))
    return candidates[0]


def glob_escape(text: str) -> str:
    """Escape glob metacharacters in a filename stem.

    Delegated to the standard library rather than hand-rolled: replacing ``[``
    with ``[[]`` and then escaping ``]`` re-processes the bracket the first
    substitution just introduced, which corrupts the pattern. `glob.escape`
    does it in one pass and leaves a lone ``]`` alone, which is already literal.
    """
    return glob.escape(text)


def local(target: str | Path, transcript: str | Path | None = None) -> Ingest:
    """Use a video already on disk."""
    video = Path(target)
    if not video.exists():
        raise IngestError(f"no such file: {video}")
    if transcript is not None:
        subs = Path(transcript)
        if not subs.exists():
            raise IngestError(f"no such transcript: {subs}")
    else:
        subs = find_transcript(video)
    return Ingest(video, subs, automatic=False)


def build_download_command(
    url: str,
    workdir: Path,
    *,
    max_height: int = 1080,
    languages: str = "en.*",
) -> list[str]:
    """Assemble the yt-dlp argv. Pure — runs nothing.

    UNVERIFIED: the format selector and subtitle flags below match yt-dlp's
    documentation but have not been executed against a live URL from here.
    """
    if not shutil.which("yt-dlp"):
        raise IngestError("yt-dlp not found on PATH. pip install yt-dlp")
    return [
        "yt-dlp",
        "--no-playlist",
        "--restrict-filenames",
        "-f", f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b",
        "--merge-output-format", "mp4",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", languages,
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        "-o", str(workdir / "%(id)s.%(ext)s"),
        "--print", "after_move:filepath",
        url,
    ]


def download(url: str, workdir: str | Path, *, timeout: float = 3600.0, **kwargs) -> Ingest:
    """Download a video and whatever subtitles it has.

    UNVERIFIED end to end — see the module docstring.
    """
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    cmd = build_download_command(url, workdir, **kwargs)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise IngestError(
            f"yt-dlp failed for {url}:\n{(result.stderr or result.stdout).strip()}"
        )

    printed = [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]
    video = next((p for p in printed if p.suffix.lower() in VIDEO_SUFFIXES and p.exists()), None)
    if video is None:
        found = [p for p in workdir.iterdir() if p.suffix.lower() in VIDEO_SUFFIXES]
        if not found:
            raise IngestError(f"yt-dlp reported success but produced no video in {workdir}")
        video = found[0]

    subs = find_transcript(video)
    # yt-dlp names automatic tracks the same way as manual ones, so the only
    # honest signal available here is that we asked for both.
    return Ingest(video, subs, automatic=subs is not None)


def resolve(target: str, workdir: str | Path, transcript: str | None = None) -> Ingest:
    """Take a URL or a path and return local files either way."""
    if looks_like_url(target):
        if transcript is not None:
            got = download(target, workdir)
            return Ingest(got.video, Path(transcript), automatic=False)
        return download(target, workdir)
    return local(target, transcript)
