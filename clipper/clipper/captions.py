"""Caption generation: word-timed transcript -> burned-in ASS subtitles.

Short-form captions are not the same object as accessibility subtitles. They
carry three or four words at a time, sit above the platform's UI furniture, and
highlight the word currently being spoken. That last part is why this module
needs word timings and why `Word.interpolated` matters: highlighting a *guessed*
word position is actively worse than highlighting nothing, because the eye
tracks the highlight and notices when it lies.

ASS rather than SRT because SRT cannot express per-word colour, and because
libass gives deterministic layout — the same file renders identically wherever
ffmpeg runs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .transcript import Word

#: Vertical video canvas. Captions are laid out against this and libass scales
#: to the real frame, so the numbers below are resolution-independent.
CANVAS_W = 1080
CANVAS_H = 1920


def ass_time(seconds: float) -> str:
    """Seconds -> ``H:MM:SS.cc``. ASS uses centiseconds, not milliseconds."""
    seconds = max(0.0, seconds)
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6_000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def ass_colour(rgb: str, alpha: int = 0) -> str:
    """``#RRGGBB`` -> ``&HAABBGGRR``. ASS stores colour byte-reversed."""
    value = rgb.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"expected #RRGGBB, got {rgb!r}")
    r, g, b = value[0:2], value[2:4], value[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def escape_text(text: str) -> str:
    """Neutralise ASS markup characters in spoken text."""
    return (
        text.replace("\\", "∖")
        .replace("{", "(")
        .replace("}", ")")
        .replace("\n", " ")
    )


@dataclass
class CaptionStyle:
    font: str = "DejaVu Sans"
    size: int = 78
    bold: bool = True

    text_colour: str = "#FFFFFF"
    highlight_colour: str = "#FFD400"
    outline_colour: str = "#000000"
    outline: float = 6.0
    shadow: float = 1.5

    #: Distance from the bottom of the frame. Short-form players park their own
    #: UI over roughly the bottom 15%, so captions sit well clear of it.
    margin_v: int = 420
    margin_h: int = 90

    #: Lines are short on purpose — a phone reads three words at a glance.
    max_words: int = 4
    max_chars: int = 26

    #: A pause longer than this always breaks the line, so a caption never spans
    #: a silence the viewer can hear.
    max_gap: float = 0.55

    #: Highlight the spoken word. Disabled automatically when timings are guesses.
    highlight: bool = True


def chunk(words: list[Word], style: CaptionStyle) -> list[list[Word]]:
    """Group words into caption lines."""
    lines: list[list[Word]] = []
    current: list[Word] = []
    for word in words:
        gap = word.start - current[-1].end if current else 0.0
        too_many = len(current) >= style.max_words
        too_wide = current and sum(len(w.text) + 1 for w in current) + len(word.text) > style.max_chars
        if current and (too_many or too_wide or gap >= style.max_gap):
            lines.append(current)
            current = []
        current.append(word)
    if current:
        lines.append(current)
    return lines


def _style_block(style: CaptionStyle) -> str:
    fields = [
        "Clip",
        style.font,
        str(style.size),
        ass_colour(style.text_colour),
        ass_colour(style.highlight_colour),
        ass_colour(style.outline_colour),
        ass_colour("#000000", alpha=0x80),
        "-1" if style.bold else "0",
        "0", "0", "0",          # italic, underline, strikeout
        "100", "100", "0", "0",  # scale x/y, spacing, angle
        "1",                     # border style: outline + shadow
        f"{style.outline:g}",
        f"{style.shadow:g}",
        "2",                     # alignment: bottom centre
        str(style.margin_h),
        str(style.margin_h),
        str(style.margin_v),
        "1",                     # encoding
    ]
    return "Style: " + ",".join(fields)


HEADER_FORMAT = (
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
    "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
    "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
    "MarginR, MarginV, Encoding"
)
EVENT_FORMAT = (
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
)


def build_ass(
    words: list[Word],
    style: CaptionStyle | None = None,
    *,
    offset: float = 0.0,
    duration: float | None = None,
) -> str:
    """Render word-timed captions as an ASS subtitle file.

    `offset` is subtracted from every timestamp, so pass the clip's start time
    when the captions will be burned onto an already-trimmed clip.
    """
    style = style or CaptionStyle()
    highlight = style.highlight and any(not w.interpolated for w in words)

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {CANVAS_W}",
        f"PlayResY: {CANVAS_H}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709",
        "",
        "[V4+ Styles]",
        HEADER_FORMAT,
        _style_block(style),
        "",
        "[Events]",
        EVENT_FORMAT,
    ]

    active = ass_colour(style.highlight_colour)
    normal = ass_colour(style.text_colour)

    for group in chunk(words, style):
        line_start = max(0.0, group[0].start - offset)
        line_end = group[-1].end - offset
        if duration is not None:
            line_end = min(line_end, duration)
        if line_end <= line_start:
            continue

        if not highlight:
            body = escape_text(" ".join(w.text for w in group))
            lines.append(
                f"Dialogue: 0,{ass_time(line_start)},{ass_time(line_end)},Clip,,0,0,0,,{body}"
            )
            continue

        # One event per word, so the spoken word can be coloured differently.
        for i, word in enumerate(group):
            seg_start = max(line_start, word.start - offset)
            seg_end = (group[i + 1].start - offset) if i + 1 < len(group) else line_end
            seg_end = min(seg_end, line_end)
            if seg_end <= seg_start:
                continue
            parts = []
            for j, w in enumerate(group):
                token = escape_text(w.text)
                parts.append(f"{{\\c{active}}}{token}{{\\c{normal}}}" if j == i else token)
            body = " ".join(parts)
            lines.append(
                f"Dialogue: 0,{ass_time(seg_start)},{ass_time(seg_end)},Clip,,0,0,0,,{body}"
            )

    return "\n".join(lines) + "\n"


_DIALOGUE = re.compile(r"^Dialogue: ")


def dialogue_count(ass: str) -> int:
    return sum(1 for line in ass.splitlines() if _DIALOGUE.match(line))
