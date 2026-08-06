"""Rendering: cut a clip out of the source and reframe it for vertical video.

This is the only module that shells out to ffmpeg. It is split so the command is
*built* by a pure function and *run* by a thin wrapper, which means the filter
graph — the part that actually goes wrong — is testable without encoding
anything.

Three reframing layouts:

* ``blur``  — the whole frame, letterboxed onto a blurred copy of itself. Never
  removes anything from the picture.
* ``fill``  — crop to 9:16, aimed at `aim` rather than assumed centred. Looks
  best on a talking head; it is also the only layout that discards picture.
* ``pad``   — black bars.

`fill` used to be dangerous because the crop was always centred and nothing
could tell whether the subject was. `framing.aim()` answers that, so the CLI's
default is now `auto`: crop when the subject was located confidently, letterbox
when it was not.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .captions import CANVAS_H, CANVAS_W

LAYOUTS = ("blur", "fill", "pad")


class RenderError(RuntimeError):
    """ffmpeg or ffprobe failed, with its stderr attached."""


@dataclass(frozen=True)
class MediaInfo:
    duration: float
    width: int
    height: int
    has_audio: bool

    @property
    def aspect(self) -> float:
        return self.width / self.height if self.height else 0.0


def _require(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise RenderError(
            f"{tool} not found on PATH. Install ffmpeg (which provides both "
            f"ffmpeg and ffprobe) and try again."
        )
    return path


def probe(source: str | Path) -> MediaInfo:
    """Read duration and frame geometry from a media file."""
    cmd = [
        _require("ffprobe"), "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(source),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RenderError(f"ffprobe failed on {source}:\n{result.stderr.strip()}")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise RenderError(f"{source} has no video stream")
    duration = float(data.get("format", {}).get("duration") or video.get("duration") or 0.0)
    return MediaInfo(
        duration=duration,
        width=int(video.get("width", 0)),
        height=int(video.get("height", 0)),
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
    )


def escape_filter_path(path: str | Path) -> str:
    """Escape a path for use inside a *single-quoted* ffmpeg filter argument.

    Only ``\\`` and ``:`` are handled, and that is deliberate: inside single
    quotes ffmpeg treats a backslash as a literal character, so an apostrophe in
    the path cannot be escaped at all — it silently truncates or mangles the
    name. Rather than fight two levels of unescaping, `render_clip` writes the
    subtitle file to a temporary directory it controls, so an awkward path never
    reaches this function in the first place.

    The output path has no such problem: it is passed as its own argv element
    and never goes near the filter parser.
    """
    text = str(path).replace("\\", "/")
    return text.replace(":", "\\:")


def is_filter_safe(path: str | Path) -> bool:
    """Whether a path can survive ffmpeg's filter-argument quoting intact."""
    return "'" not in str(path)


def crop_expression(center: float, width: int, height: int) -> str:
    """A crop filter aimed at `center`, a fraction of the frame's width.

    The offset is an expression over ``in_w``/``out_w`` rather than a pixel
    count, so it stays correct whatever width the scaler rounds the intermediate
    frame to. `clip()` keeps the window inside the picture when the subject sits
    near an edge.
    """
    center = min(1.0, max(0.0, center))
    return (
        f"crop={width}:{height}:"
        f"x='clip(in_w*{center:.4f}-out_w/2,0,in_w-out_w)':"
        f"y='(in_h-out_h)/2'"
    )


def build_filter(
    layout: str,
    *,
    ass_path: str | Path | None = None,
    width: int = CANVAS_W,
    height: int = CANVAS_H,
    blur_sigma: float = 26.0,
    aim: float = 0.5,
) -> str:
    """Build the filter graph that reframes the source and burns captions.

    `aim` is where the subject is, as a fraction of frame width. It only affects
    `fill`, which is the only layout that discards picture.
    """
    if layout not in LAYOUTS:
        raise ValueError(f"unknown layout {layout!r}; expected one of {LAYOUTS}")

    cover = f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos"
    contain = f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=lanczos"
    crop = f"crop={width}:{height}"

    if layout == "fill":
        graph = [f"[0:v]{cover},{crop_expression(aim, width, height)},setsar=1[v]"]
    elif layout == "pad":
        graph = [
            f"[0:v]{contain},pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[v]"
        ]
    else:  # blur
        graph = [
            "[0:v]split=2[bg][fg]",
            f"[bg]{cover},{crop},gblur=sigma={blur_sigma:g},eq=brightness=-0.10[bgb]",
            f"[fg]{contain}[fgs]",
            "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1[v]",
        ]

    if ass_path is not None:
        graph.append(f"[v]subtitles=filename='{escape_filter_path(ass_path)}'[vout]")
    else:
        graph.append("[v]null[vout]")
    return ";".join(graph)


def build_command(
    source: str | Path,
    destination: str | Path,
    *,
    start: float,
    end: float,
    layout: str = "blur",
    ass_path: str | Path | None = None,
    width: int = CANVAS_W,
    height: int = CANVAS_H,
    has_audio: bool = True,
    crf: int = 20,
    preset: str = "veryfast",
    audio_bitrate: str = "160k",
    fps: float | None = None,
    overwrite: bool = True,
    aim: float = 0.5,
) -> list[str]:
    """Assemble the ffmpeg argv for one clip. Pure — runs nothing."""
    if end <= start:
        raise ValueError(f"clip end ({end}) must be after start ({start})")

    cmd = [_require("ffmpeg"), "-hide_banner", "-loglevel", "error"]
    cmd += ["-y"] if overwrite else ["-n"]
    # -ss before -i seeks fast; ffmpeg still decodes to the exact frame when
    # re-encoding, so this is accurate as well as quick.
    cmd += ["-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(source)]

    cmd += [
        "-filter_complex",
        build_filter(layout, ass_path=ass_path, width=width, height=height, aim=aim),
    ]
    cmd += ["-map", "[vout]"]
    if has_audio:
        cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", audio_bitrate, "-ac", "2"]
    else:
        cmd += ["-an"]

    cmd += [
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
    ]
    if fps:
        cmd += ["-r", f"{fps:g}"]
    cmd += ["-movflags", "+faststart", str(destination)]
    return cmd


def run(cmd: list[str], *, timeout: float = 900.0) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RenderError(
            "ffmpeg failed:\n"
            + " ".join(cmd)
            + "\n---\n"
            + (result.stderr.strip() or "(no stderr)")
        )


def render_clip(
    source: str | Path,
    destination: str | Path,
    *,
    start: float,
    end: float,
    ass: str | None = None,
    layout: str = "blur",
    info: MediaInfo | None = None,
    **kwargs,
) -> Path:
    """Cut one clip, reframe it, and burn `ass` captions onto it if given."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    info = info or probe(source)

    workdir: str | None = None
    ass_path: Path | None = None
    if ass:
        # Deliberately *not* beside the destination: the destination may contain
        # an apostrophe, which ffmpeg's filter parser cannot represent.
        workdir = tempfile.mkdtemp(prefix="clipper-")
        ass_path = Path(workdir) / "captions.ass"
        ass_path.write_text(ass, encoding="utf-8")
        if not is_filter_safe(ass_path):
            raise RenderError(
                f"temporary directory {workdir!r} contains an apostrophe, which "
                f"ffmpeg cannot escape in a filter argument. Set TMPDIR to a "
                f"path without one."
            )
    try:
        cmd = build_command(
            source, destination,
            start=start, end=end,
            layout=layout, ass_path=ass_path,
            has_audio=info.has_audio,
            **kwargs,
        )
        run(cmd)
    finally:
        if workdir is not None:
            shutil.rmtree(workdir, ignore_errors=True)
    return destination


def synth_source(
    destination: str | Path,
    *,
    duration: float = 30.0,
    width: int = 1280,
    height: int = 720,
    fps: int = 25,
    audio: bool = True,
) -> Path:
    """Generate a test video with ffmpeg's own sources.

    The whole pipeline downstream of the download is exercisable without a
    network or a real video file, which is what makes the render layer testable
    in CI at all.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        _require("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"testsrc2=size={width}x{height}:rate={fps}:duration={duration}",
    ]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}"]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "64k", "-shortest"]
    cmd += [str(destination)]
    run(cmd)
    return destination
