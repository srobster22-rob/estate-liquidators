"""Framing: work out *where* to crop, instead of assuming the centre.

Cropping 16:9 to 9:16 keeps about 32% of the frame's width. Taking that from the
middle is a coin flip — if the speaker sits left of centre, the centre crop
removes their head and nothing downstream can tell. That is the whole reason
`render`'s default layout is the letterboxed one.

This module removes the guess. It decodes a handful of *very* small greyscale
frames and scores each column of the picture by two things:

* **Motion** — how much that column changes between frames. A person talking is
  the only thing moving in most of these videos.
* **Detail** — horizontal gradient energy. Faces and hands carry detail; walls,
  skies and bokeh backgrounds do not.

No model, no dependencies, and — importantly — a ground truth you can synthesise:
put a moving box on the right of the frame and the aim must come back right.

**What it does not do:** track. One aim is computed per clip and held for its
whole duration. A speaker who walks across the room mid-clip will still be lost.
Panning is the obvious next round; a static but *correct* aim is already the
difference between a usable clip and a beheaded one.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

from .render import RenderError, _require

#: Analysis resolution. Small on purpose — the subject's position is a
#: low-frequency property, and 64x36 makes pure-Python analysis instant.
GRID_W = 64
GRID_H = 36

#: Frames sampled per second of clip.
SAMPLE_FPS = 3.0

#: Below this, the picture has no dominant region and the centre is as good a
#: guess as any. Reported rather than hidden.
#:
#: Measured, not guessed. Across synthesised fixtures the two populations are
#: cleanly separated: subjects that stay inside a crop window score 0.556–0.689,
#: while a subject walking across the frame scores 0.128 and aims somewhere
#: meaningless. 0.35 sits in the middle of that gap. Re-measure if the analysis
#: grid, the sample rate, or the signal weights change — all three move it.
MIN_CONFIDENCE = 0.35

#: Motion is the stronger signal for talking heads; detail keeps it honest when
#: the speaker holds still.
MOTION_WEIGHT = 0.65
DETAIL_WEIGHT = 0.35


@dataclass
class Aim:
    """Where the subject is, and how sure we are."""

    #: Horizontal centre of the subject as a fraction of frame width, 0..1.
    center: float
    #: 0..1. How much better the chosen window is than an average one.
    confidence: float
    #: Per-column energy, kept for debugging and for tests.
    energy: list[float] = field(default_factory=list, repr=False)
    #: True when the aim fell back to the centre for lack of signal.
    fell_back: bool = False


def sample_luma(
    source,
    *,
    start: float,
    duration: float,
    fps: float = SAMPLE_FPS,
    width: int = GRID_W,
    height: int = GRID_H,
) -> list[bytes]:
    """Decode a clip to a list of tiny greyscale frames."""
    cmd = [
        _require("ffmpeg"), "-hide_banner", "-loglevel", "error",
        "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(source),
        "-vf", f"fps={fps:g},scale={width}:{height}:flags=area,format=gray",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RenderError(
            f"frame sampling failed for {source}:\n{result.stderr.decode(errors='replace').strip()}"
        )
    size = width * height
    data = result.stdout
    return [data[i : i + size] for i in range(0, len(data) - size + 1, size)]


def column_energy(
    frames: list[bytes],
    *,
    width: int = GRID_W,
    height: int = GRID_H,
    motion_weight: float = MOTION_WEIGHT,
    detail_weight: float = DETAIL_WEIGHT,
) -> list[float]:
    """Score each column of the picture by motion and detail.

    The two measures are normalised independently before being combined, so the
    weights mean what they say regardless of the absolute scale of either.
    """
    if not frames:
        return [0.0] * width

    motion = [0.0] * width
    detail = [0.0] * width
    previous: bytes | None = None
    for frame in frames:
        if len(frame) < width * height:
            continue
        for r in range(height):
            row = r * width
            for c in range(1, width):
                detail[c] += abs(frame[row + c] - frame[row + c - 1])
            if previous is not None:
                for c in range(width):
                    motion[c] += abs(frame[row + c] - previous[row + c])
        previous = frame

    # Column 0 has no left neighbour; give it its neighbour's detail rather than
    # a structural zero, which would otherwise bias every aim rightwards.
    if width > 1:
        detail[0] = detail[1]

    # Each signal is normalised to unit mass so their *shapes* are comparable,
    # then scaled by how concentrated that shape is. Without the second step a
    # motion field made entirely of compression noise still carries its full
    # weight: unit-mass normalisation discards exactly the thing that decides
    # whether the signal means anything. Measured on a static shot, that noise
    # was outvoting a perfectly clean detail peak.
    motion_reliability = concentration(motion)
    detail_reliability = concentration(detail)
    return [
        motion_weight * motion_reliability * m + detail_weight * detail_reliability * d
        for m, d in zip(_normalise(motion), _normalise(detail))
    ]


def _normalise(values: list[float]) -> list[float]:
    total = sum(values)
    if total <= 0:
        return [0.0] * len(values)
    return [v / total for v in values]


def concentration(values: list[float], quantile: float = 0.25) -> float:
    """How clustered a distribution is, 0 (uniform) to 1 (a single spike).

    Measured as the share of total mass held by the heaviest `quantile` of
    columns, rescaled so that the uniform expectation maps to zero. Noise is
    close to uniform and scores near zero; a subject occupying a quarter of the
    frame scores high.
    """
    if not values:
        return 0.0
    total = sum(values)
    if total <= 0:
        return 0.0
    k = max(1, round(len(values) * quantile))
    share = sum(sorted(values, reverse=True)[:k]) / total
    baseline = k / len(values)
    return max(0.0, min(1.0, (share - baseline) / (1.0 - baseline)))


def window_columns(source_aspect: float, target_aspect: float, width: int = GRID_W) -> int:
    """How many analysis columns the crop window covers."""
    if source_aspect <= 0:
        return width
    fraction = min(1.0, target_aspect / source_aspect)
    return max(1, min(width, round(fraction * width)))


def best_window(
    energy: list[float], window: int, *, min_confidence: float = MIN_CONFIDENCE
) -> Aim:
    """Slide a crop-width window across the energy profile and take the best spot.

    Confidence is how far the best window beats the *average* window. A flat
    profile — an evenly-lit static shot, or noise — scores near zero and the aim
    falls back to the centre rather than latching onto a meaningless maximum.
    """
    width = len(energy)
    if width == 0 or window >= width:
        return Aim(0.5, 0.0, energy, fell_back=True)

    sums: list[float] = []
    running = sum(energy[:window])
    sums.append(running)
    for i in range(window, width):
        running += energy[i] - energy[i - window]
        sums.append(running)

    best = max(sums)
    mean = sum(sums) / len(sums)
    confidence = 0.0 if best <= 0 else max(0.0, (best - mean) / best)

    if confidence < min_confidence:
        return Aim(0.5, confidence, energy, fell_back=True)

    # Centroid of the tied maxima, so a plateau aims at its middle rather than
    # snapping to whichever edge the scan reached first.
    top = [i for i, s in enumerate(sums) if s >= best - 1e-12]
    start = int(round(sum(top) / len(top)))

    # Then the energy-weighted centroid *inside* that window, rather than the
    # window's midpoint. Two biases go away with it: a half-column offset, and
    # — the larger one — the fact that near a frame edge the plateau of tied
    # windows is truncated by clamping, which drags the midpoint inward.
    segment = energy[start : start + window]
    mass = sum(segment)
    if mass <= 0:
        center = (start + window / 2) / width
    else:
        center = sum(e * (start + i + 0.5) for i, e in enumerate(segment)) / mass / width
    return Aim(min(1.0, max(0.0, center)), confidence, energy)


def aim(
    source,
    *,
    start: float,
    duration: float,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
    **kwargs,
) -> Aim:
    """Find the subject's horizontal centre for one clip."""
    if source_height <= 0 or target_height <= 0:
        return Aim(0.5, 0.0, [], fell_back=True)
    frames = sample_luma(source, start=start, duration=duration, **kwargs)
    energy = column_energy(frames)
    window = window_columns(source_width / source_height, target_width / target_height)
    return best_window(energy, window)


def choose_layout(aimed: Aim, *, confident: str = "fill", unsure: str = "blur") -> str:
    """Pick a reframing layout from how well the subject could be located.

    This is the point of the whole module. Centre-cropping is the better-looking
    option *when you know where to crop*; letterboxing is the safe one when you
    do not. Confidence answers exactly that question, so the choice stops being
    a global preference and becomes a per-clip fact.
    """
    return unsure if aimed.fell_back else confident
