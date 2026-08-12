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

#: Silence inserted *between* words inside a sentence, and *after* a sentence
#: ends. Real ASR emits word-level timings with exactly this two-population
#: structure, and it is the only sentence signal that survives into an
#: unpunctuated transcript.
#:
#: The first version of this generator inherited the source SRT's cue-level
#: interpolation instead, which put a gap of *exactly zero* between every word
#: inside a cue. That fixture could not contain the thing it was built to
#: measure: segmentation had nothing but cue boundaries to cut on, produced
#: utterances three times coarser than the punctuated original, and made
#: `payoff` unreachable on every candidate.
WORD_GAP = 0.04
SENTENCE_GAP = 0.42

_STRIP = re.compile(r"[^\w' ]+")


def flatten(word: Word) -> str:
    """ASR output: lower-case, no punctuation, no capitals — not even on names."""
    return _STRIP.sub("", word.text).lower()


def respace(words: list[Word], source_text: list[str]) -> list[Word]:
    """Re-time words with realistic inter-word and sentence-boundary silence.

    Anchored to the original span so the transcript stays aligned with the video:
    speech time is shared out by word length, and the gaps are carved from the
    same budget rather than added on top.
    """
    if not words:
        return []
    start, end = words[0].start, words[-1].end
    span = max(0.01, end - start)

    ends_sentence = [bool(t) and t[-1] in ".!?" for t in source_text]
    gaps = [
        (SENTENCE_GAP if ends_sentence[i] else WORD_GAP)
        for i in range(len(words) - 1)
    ]
    speech_weights = [max(1, len(w.text)) for w in words]

    gap_total = sum(gaps)
    speech_total = max(0.01, span - gap_total)
    if speech_total < span * 0.35:  # pathologically tight; shrink the gaps
        scale = (span * 0.65) / max(gap_total, 1e-6)
        gaps = [g * scale for g in gaps]
        speech_total = span - sum(gaps)

    unit = speech_total / sum(speech_weights)
    out: list[Word] = []
    cursor = start
    for i, word in enumerate(words):
        duration = speech_weights[i] * unit
        out.append(Word(word.text, cursor, cursor + duration, False))
        cursor += duration + (gaps[i] if i < len(gaps) else 0.0)
    return out


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
    timed = respace(transcript.words, [w.text for w in transcript.words])
    destination.write_text(build(timed), encoding="utf-8")
    gaps = [b.start - a.end for a, b in zip(timed, timed[1:])]
    big = sum(1 for g in gaps if g > (WORD_GAP + SENTENCE_GAP) / 2)
    print(
        f"{source} -> {destination}: {len(timed)} words, "
        f"{big} sentence-sized gaps of {len(gaps)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
