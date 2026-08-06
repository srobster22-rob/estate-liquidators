"""Generate a YouTube-style auto-caption VTT from a clean SRT.

Produces a *paired* fixture: same words, same timings, but rendered the way ASR
actually delivers them — lower-case, unpunctuated, with per-word inline timings
and each cue carrying the previous line forward so the block scrolls.

Pairing is the point. Any difference the scorer shows between `talk.srt` and
`talk_auto.vtt` is caused by the caption regime alone, because nothing else
differs. That isolates how much of the scorer depends on punctuation and
capitals, which real YouTube input does not have.

    python3 fixtures/make_auto.py fixtures/talk.srt fixtures/talk_auto.vtt
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clipper.transcript import Word, format_timestamp, load  # noqa: E402

#: Words per rolling caption line, roughly what YouTube emits.
LINE_WORDS = 7

_STRIP = re.compile(r"[^\w' ]+")


def flatten(word: Word) -> str:
    """ASR output: lower-case, no punctuation, no capitals — not even on names."""
    return _STRIP.sub("", word.text).lower()


def build(words: list[Word]) -> str:
    lines = ["WEBVTT", "Kind: captions", "Language: en", ""]
    rows: list[list[Word]] = [
        words[i : i + LINE_WORDS] for i in range(0, len(words), LINE_WORDS)
    ]

    previous: list[Word] | None = None
    for row in rows:
        if not row:
            continue
        start, end = row[0].start, row[-1].end
        payload_lines = []
        if previous is not None:
            # Carry-over line: plain text, no inline timings. This is the part a
            # naive parser duplicates into the transcript.
            payload_lines.append(" ".join(flatten(w) for w in previous))

        # New line: first word plain, every later word preceded by its timestamp.
        parts = [flatten(row[0])]
        for word in row[1:]:
            parts.append(f"<{format_timestamp(word.start)}><c> {flatten(word)}</c>")
        payload_lines.append("".join(parts))

        lines.append(
            f"{format_timestamp(start)} --> {format_timestamp(end)} align:start position:0%"
        )
        lines.extend(payload_lines)
        lines.append("")
        previous = row
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    source, destination = Path(argv[0]), Path(argv[1])
    transcript = load(source)
    destination.write_text(build(transcript.words), encoding="utf-8")
    print(f"{source} -> {destination}: {len(transcript.words)} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
