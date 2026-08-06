"""Segmentation: word stream -> utterances -> candidate clip windows.

A clip that starts mid-sentence reads as a mistake no matter how good the
content is, so every candidate window is required to begin and end on an
utterance boundary. The interesting question is what counts as a boundary when
the transcript has no punctuation at all — which is the normal case, because
auto-captions never emit any.

Two boundary signals, in priority order:

1. **Punctuation**, when the transcript has it.
2. **Silence**, always. A gap between words is the speaker breathing, and it is
   the only sentence signal an auto-caption transcript carries.

`Segmentation.punctuated` records which regime was used, because it changes how
much the downstream scorer should trust a "clean ending".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .transcript import Transcript, Word

#: A gap at least this long is treated as a sentence boundary.
DEFAULT_GAP = 0.65

#: Hard cap on utterance length, so an unpunctuated monologue with no pauses
#: still produces boundaries to cut on.
DEFAULT_MAX_WORDS = 45

#: Below this fraction of sentence-final punctuation, the transcript is treated
#: as unpunctuated and gaps carry the whole load.
PUNCTUATION_FLOOR = 0.02

#: Fraction of utterances that must begin with a capital before capitalisation
#: is treated as a meaningful signal. Set high: the value of a lower-case
#: opening word is that it proves a mid-sentence cut, and that inference is only
#: sound if capitals are otherwise reliable.
CAPITAL_FLOOR = 0.80

_SENTENCE_END = re.compile(r"[.!?…]+[\"')\]]*$")

#: Trailing dots that are not sentence ends. Deliberately short — a false
#: negative here merely fails to split, which the gap rule usually catches anyway.
_ABBREVIATIONS = {
    "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.",
    "vs.", "etc.", "e.g.", "i.e.", "approx.", "fig.", "no.",
}


def _is_sentence_end(word: Word) -> bool:
    text = word.text.strip()
    if text.lower() in _ABBREVIATIONS:
        return False
    if re.fullmatch(r"(?:[A-Za-z]\.){2,}", text):
        return False  # U.S.A., a.m. — initialisms, not sentence ends
    return bool(_SENTENCE_END.search(text))


@dataclass(frozen=True)
class Utterance:
    """A run of words bounded by punctuation, silence, or the length cap."""

    words: list[Word]
    gap_after: float = 0.0
    ends_on_punctuation: bool = False

    @property
    def start(self) -> float:
        return self.words[0].start

    @property
    def end(self) -> float:
        return self.words[-1].end

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)


@dataclass
class Segmentation:
    utterances: list[Utterance]
    punctuated: bool
    capitalised: bool = False
    """True when utterances reliably start with a capital letter.

    Auto-captions are entirely lower-case, so this is the signal that tells the
    scorer whether a lower-case opening word means anything.
    """

    def __len__(self) -> int:
        return len(self.utterances)


@dataclass(frozen=True)
class Candidate:
    """A proposed clip: a contiguous run of whole utterances."""

    start_index: int
    end_index: int  # exclusive
    utterances: list[Utterance] = field(repr=False, default_factory=list)

    @property
    def start(self) -> float:
        return self.utterances[0].start

    @property
    def end(self) -> float:
        return self.utterances[-1].end

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def words(self) -> list[Word]:
        return [w for u in self.utterances for w in u.words]

    @property
    def text(self) -> str:
        return " ".join(u.text for u in self.utterances)

    @property
    def gap_after(self) -> float:
        return self.utterances[-1].gap_after

    @property
    def ends_on_punctuation(self) -> bool:
        return self.utterances[-1].ends_on_punctuation

    def overlaps(self, other: "Candidate", *, pad: float = 0.0) -> bool:
        return self.start - pad < other.end and other.start - pad < self.end


def punctuation_ratio(words: list[Word]) -> float:
    if not words:
        return 0.0
    return sum(1 for w in words if _is_sentence_end(w)) / len(words)


def segment(
    transcript: Transcript,
    *,
    gap: float = DEFAULT_GAP,
    max_words: int = DEFAULT_MAX_WORDS,
) -> Segmentation:
    """Group a transcript's words into utterances."""
    words = transcript.words
    punctuated = punctuation_ratio(words) >= PUNCTUATION_FLOOR

    utterances: list[Utterance] = []
    current: list[Word] = []
    for i, word in enumerate(words):
        current.append(word)
        next_word = words[i + 1] if i + 1 < len(words) else None
        gap_after = (next_word.start - word.end) if next_word else 0.0

        by_punctuation = punctuated and _is_sentence_end(word)
        by_silence = next_word is not None and gap_after >= gap
        by_length = len(current) >= max_words
        if next_word is None or by_punctuation or by_silence or by_length:
            utterances.append(
                Utterance(current, gap_after=gap_after, ends_on_punctuation=by_punctuation)
            )
            current = []

    starts = [u.words[0].text[:1] for u in utterances if u.words and u.words[0].text]
    alpha = [c for c in starts if c.isalpha()]
    capitalised = bool(alpha) and sum(1 for c in alpha if c.isupper()) / len(alpha) >= CAPITAL_FLOOR
    return Segmentation(utterances, punctuated, capitalised)


def candidates(
    seg: Segmentation,
    *,
    min_duration: float = 15.0,
    max_duration: float = 60.0,
    max_per_start: int | None = None,
) -> list[Candidate]:
    """Every run of whole utterances whose duration lands in the target band.

    All valid lengths are emitted per starting point so the scorer, not the
    segmenter, decides where a clip should end.

    `max_per_start` exists for pathological inputs only, and it is *not* a
    default. Capping here truncates the window list from the short end, which
    silently biases every clip below the target length — the scorer never sees
    the candidates nearest the ideal duration and cannot recover them.
    """
    out: list[Candidate] = []
    utts = seg.utterances
    for i in range(len(utts)):
        emitted = 0
        for j in range(i + 1, len(utts) + 1):
            window = utts[i:j]
            duration = window[-1].end - window[0].start
            if duration > max_duration:
                break
            if duration >= min_duration:
                out.append(Candidate(i, j, window))
                emitted += 1
                if max_per_start is not None and emitted >= max_per_start:
                    break
    return out
