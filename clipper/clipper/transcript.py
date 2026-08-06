"""Transcript parsing.

Turns a subtitle file into a flat, word-timed stream. Everything downstream —
segmentation, scoring, caption rendering — consumes `Transcript.words` and never
touches the file format again.

Two formats are supported:

* **WebVTT**, including YouTube's auto-caption dialect, which carries per-word
  timings inline (``<00:00:01.234><c> word</c>``) and repeats previously-shown
  text on every cue to produce the rolling two-line effect.
* **SRT**, which has no word timings at all.

Where word timings are absent they are *interpolated* across the cue, weighted by
word length. That is a guess, and `Word.interpolated` says so, because a caption
renderer that highlights the wrong word is worse than one that highlights none.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Word:
    """One spoken word with a start and end time in seconds."""

    text: str
    start: float
    end: float
    interpolated: bool = False
    """True when the timing was guessed from the cue rather than read from it."""

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class Cue:
    """A raw subtitle cue, kept for debugging and for round-tripping."""

    start: float
    end: float
    text: str


@dataclass
class Transcript:
    words: list[Word]
    cues: list[Cue]
    source: str = ""
    rolling: bool = False
    """True when the file was detected as a rolling auto-caption dialect and de-duplicated."""

    @property
    def duration(self) -> float:
        return self.words[-1].end if self.words else 0.0

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def has_real_word_timings(self) -> bool:
        """False when every word's timing was interpolated from cue bounds."""
        return any(not w.interpolated for w in self.words)

    def slice(self, start: float, end: float) -> list[Word]:
        """Words whose midpoint falls inside [start, end)."""
        return [w for w in self.words if start <= (w.start + w.end) / 2 < end]


# --------------------------------------------------------------------------
# Time parsing
# --------------------------------------------------------------------------

_TS = r"(?:\d+:)?\d{1,2}:\d{2}[.,]\d{1,3}"
_CUE_TIMING = re.compile(rf"^\s*({_TS})\s*-->\s*({_TS})\s*(.*)$")
_INLINE_TS = re.compile(rf"<({_TS})>")
_TAG = re.compile(r"</?[cvibu](?:[.\s][^>]*)?>|</?ruby>|</?rt>|</?lang[^>]*>")
_WS = re.compile(r"\s+")


def parse_timestamp(raw: str) -> float:
    """``01:02:03.456`` / ``02:03,456`` -> seconds. Hours are optional."""
    raw = raw.strip().replace(",", ".")
    parts = raw.split(":")
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, (m, s) = "0", parts
    else:
        raise ValueError(f"unparsable timestamp: {raw!r}")
    return int(h) * 3600 + int(m) * 60 + float(s)


def format_timestamp(seconds: float, *, comma: bool = False) -> str:
    """Seconds -> ``HH:MM:SS.mmm`` (or ``,mmm`` for SRT)."""
    seconds = max(0.0, seconds)
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


# --------------------------------------------------------------------------
# Cue block parsing
# --------------------------------------------------------------------------


def _blocks(body: str) -> list[list[str]]:
    """Split a subtitle file into blank-line-separated blocks of non-empty lines."""
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    out: list[list[str]] = []
    current: list[str] = []
    for line in body.split("\n"):
        if line.strip():
            current.append(line)
        elif current:
            out.append(current)
            current = []
    if current:
        out.append(current)
    return out


def _strip_tags(text: str) -> str:
    return _WS.sub(" ", _TAG.sub("", text)).strip()


def _cue_words(payload: str, start: float, end: float) -> list[Word]:
    """Extract words from one cue payload, using inline timings where present.

    The payload is split on inline timestamps. Everything before the first
    timestamp belongs to `start`; each subsequent chunk begins at the timestamp
    that introduced it. Within a chunk (usually one word, but not guaranteed)
    time is divided evenly.
    """
    pieces = _INLINE_TS.split(payload)
    # split() with one capture group yields [text, ts, text, ts, text, ...]
    chunks: list[tuple[float, str, bool]] = []
    chunks.append((start, pieces[0], not _INLINE_TS.search(payload)))
    for i in range(1, len(pieces), 2):
        ts = parse_timestamp(pieces[i])
        chunks.append((ts, pieces[i + 1] if i + 1 < len(pieces) else "", False))

    words: list[Word] = []
    for idx, (chunk_start, raw, guessed) in enumerate(chunks):
        tokens = _strip_tags(raw).split()
        if not tokens:
            continue
        chunk_end = chunks[idx + 1][0] if idx + 1 < len(chunks) else end
        if chunk_end <= chunk_start:
            chunk_end = chunk_start
        words.extend(_spread(tokens, chunk_start, chunk_end, guessed or len(tokens) > 1))
    return words


def _spread(tokens: list[str], start: float, end: float, interpolated: bool) -> list[Word]:
    """Lay `tokens` across [start, end], giving longer words proportionally more time."""
    if not tokens:
        return []
    if len(tokens) == 1:
        return [Word(tokens[0], start, end, interpolated)]
    weights = [max(1, len(t)) for t in tokens]
    total = sum(weights)
    span = max(0.0, end - start)
    out: list[Word] = []
    cursor = start
    for token, weight in zip(tokens, weights):
        width = span * weight / total
        out.append(Word(token, cursor, cursor + width, interpolated))
        cursor += width
    return out


# --------------------------------------------------------------------------
# Rolling-caption de-duplication
# --------------------------------------------------------------------------

_NORM = re.compile(r"[^\w']+", re.UNICODE)


def _key(word: Word) -> str:
    return _NORM.sub("", word.text.lower())


def _overlap(tail: list[str], head: list[str]) -> int:
    """Longest k where the last k of `tail` equal the first k of `head`."""
    for k in range(min(len(tail), len(head)), 0, -1):
        if tail[-k:] == head[:k] and any(tail[-k:]):
            return k
    return 0


def _drop_repeat_prefix(emitted: list[Word], incoming: list[Word]) -> list[Word]:
    """Drop the leading words of `incoming` that merely restate the tail of `emitted`.

    Only called once the file has been identified as a rolling dialect (see
    `looks_rolling`) and only for cues that are *contiguous* with the previous
    one. Both conditions matter: a phrase the speaker genuinely repeats after a
    pause keeps its own timing gap, so it fails the contiguity test and survives.
    """
    if not emitted or not incoming:
        return incoming
    k = _overlap([_key(w) for w in emitted], [_key(w) for w in incoming])
    return incoming[k:] if k else incoming


#: Cues closer together than this are treated as one continuous scroll.
CONTIGUITY = 0.5

#: Fraction of adjacent cue pairs that must overlap before a file without inline
#: timings is called a rolling dialect. Auto-captions carry text forward on
#: essentially every pair, so the bar is set near-total rather than at a majority.
ROLLING_THRESHOLD = 0.70

#: Minimum adjacent-cue pairs before the fallback heuristic is trusted at all.
#: On a four-cue file a single incidental overlap is 33% of the sample, which is
#: noise, not a pattern.
MIN_ROLLING_PAIRS = 6


def looks_rolling(body: str, cues: list[Cue]) -> bool:
    """Decide whether a subtitle file uses the rolling carry-over convention.

    Inline word timings are conclusive — only the auto-caption generator emits
    them. Otherwise fall back to measuring how often consecutive cues share a
    two-or-more-word boundary overlap, which is normal in auto-captions and rare
    in hand-authored ones.

    Getting this wrong in the permissive direction deletes real dialogue, so the
    fallback deliberately requires a *pattern* across the file rather than
    reacting to any single suspicious pair.
    """
    if _INLINE_TS.search(body):
        return True
    if len(cues) < 2:
        return False
    tokens = [[_NORM.sub("", t.lower()) for t in c.text.split()] for c in cues]
    pairs = list(zip(tokens, tokens[1:]))
    if len(pairs) < MIN_ROLLING_PAIRS:
        return False
    hits = sum(1 for a, b in pairs if _overlap(a, b) >= 2)
    return hits / len(pairs) >= ROLLING_THRESHOLD


# --------------------------------------------------------------------------
# Format parsers
# --------------------------------------------------------------------------


def parse_vtt(body: str, *, source: str = "", rolling: bool | None = None) -> Transcript:
    """Parse WebVTT. `rolling` overrides auto-detection of the carry-over dialect."""
    raw: list[tuple[float, float, str]] = []
    cues: list[Cue] = []
    for block in _blocks(body):
        timing_idx = next((i for i, ln in enumerate(block) if _CUE_TIMING.match(ln)), None)
        if timing_idx is None:
            continue  # WEBVTT header, NOTE block, STYLE block, or a stray cue id
        match = _CUE_TIMING.match(block[timing_idx])
        assert match is not None
        start, end = parse_timestamp(match.group(1)), parse_timestamp(match.group(2))
        payload = "\n".join(block[timing_idx + 1 :])
        if not payload.strip():
            continue
        raw.append((start, end, payload))
        cues.append(Cue(start, end, _strip_tags(payload)))

    is_rolling = looks_rolling(body, cues) if rolling is None else rolling

    words: list[Word] = []
    prev_end: float | None = None
    for start, end, payload in raw:
        fresh = _cue_words(payload, start, end)
        contiguous = prev_end is not None and start - prev_end <= CONTIGUITY
        if is_rolling and contiguous:
            fresh = _drop_repeat_prefix(words, fresh)
        words.extend(fresh)
        prev_end = end
    return Transcript(_monotonic(words), cues, source, is_rolling)


def parse_srt(body: str, *, source: str = "") -> Transcript:
    words: list[Word] = []
    cues: list[Cue] = []
    for block in _blocks(body):
        timing_idx = next((i for i, ln in enumerate(block) if _CUE_TIMING.match(ln)), None)
        if timing_idx is None:
            continue
        match = _CUE_TIMING.match(block[timing_idx])
        assert match is not None
        start, end = parse_timestamp(match.group(1)), parse_timestamp(match.group(2))
        payload = _strip_tags("\n".join(block[timing_idx + 1 :]))
        if not payload:
            continue
        cues.append(Cue(start, end, payload))
        words.extend(_spread(payload.split(), start, end, interpolated=True))
    return Transcript(_monotonic(words), cues, source)


def _monotonic(words: list[Word]) -> list[Word]:
    """Clamp out-of-order or zero-length timings so downstream code can trust them."""
    out: list[Word] = []
    cursor = 0.0
    for w in words:
        start = max(w.start, cursor)
        end = max(w.end, start + 0.01)
        out.append(Word(w.text, start, end, w.interpolated))
        cursor = start
    return out


def parse(text: str, *, fmt: str | None = None, source: str = "") -> Transcript:
    """Parse a subtitle body, sniffing the format when `fmt` is not given."""
    if fmt is None:
        head = text.lstrip()[:64].upper()
        fmt = "vtt" if head.startswith("WEBVTT") or "-->" in head and "." in head else "srt"
        if "-->" in text and "," in text.split("-->", 1)[1][:16]:
            fmt = "srt"
    if fmt == "vtt":
        return parse_vtt(text, source=source)
    if fmt == "srt":
        return parse_srt(text, source=source)
    raise ValueError(f"unknown subtitle format: {fmt!r}")


def load(path: str | Path) -> Transcript:
    """Parse a subtitle file, choosing the parser by extension."""
    path = Path(path)
    body = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower().lstrip(".")
    fmt = {"vtt": "vtt", "srt": "srt"}.get(suffix)
    return parse(body, fmt=fmt, source=str(path))
