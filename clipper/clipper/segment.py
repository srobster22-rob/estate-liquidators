"""Segmentation: word stream -> utterances -> candidate clip windows.

A clip that starts mid-sentence reads as a mistake no matter how good the
content is, so every candidate window is required to begin and end on an
utterance boundary. The interesting question is what counts as a boundary when
the transcript has no punctuation at all — which is the normal case, because
auto-captions never emit any.

Two boundary signals, in priority order:

1. **Punctuation**, when the transcript has it.
2. **Silence**, always. A gap between words is the speaker breathing, and it is
   the only sentence signal an auto-caption transcript carries. How long a gap
   has to be is *derived per transcript* rather than fixed — see `adaptive_gap`.

`Segmentation.punctuated` records which regime was used, because it changes how
much the downstream scorer should trust a "clean ending".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .transcript import Transcript, Word

#: Fallback sentence-boundary gap, used only when a transcript's own gap
#: distribution is too degenerate to split (see `adaptive_gap`).
#:
#: It is a fallback rather than the rule because no single number fits every
#: speaker. Measured at R7 on auto-captions, 0.65 caught **14 of 572** gaps —
#: that transcript's sentence pauses sit around 0.44 — which starved the
#: segmenter of boundaries and produced utterances three times coarser than the
#: same content with punctuation.
DEFAULT_GAP = 0.65

#: Histogram resolution for the adaptive split. 256 is plenty for a value range
#: measured in seconds.
GAP_BINS = 256

#: Gaps below this are numerical dust, not silence. Contiguous word timings
#: differ by ~1e-16 through floating-point accumulation alone, and without this
#: filter Otsu happily splits on that noise — a gapless synthetic transcript
#: produced 2,412 utterances instead of 267.
GAP_EPSILON = 1e-3

#: The shortest threshold worth believing. Below this the transcript has no real
#: pauses to find, so the adaptive split is meaningless and the fallback is
#: honest.
MIN_GAP_THRESHOLD = 0.08

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
_TOKEN = re.compile(r"[^\w']+")

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
    gap_before: float = 0.0
    """Silence preceding this utterance.

    The only sentence-start signal an auto-caption transcript carries. Where a
    transcript has capitals, they are the better evidence; where it does not,
    this is all there is.
    """

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

    gap_threshold: float = DEFAULT_GAP
    """The silence threshold actually used — adaptive unless explicitly overridden."""

    frequency: dict[str, int] = field(default_factory=dict)
    """How often each token appears in this transcript.

    Used to tell content words from function words *without a stopword list*:
    the words a document leans on hardest are its own background. Deriving that
    from the text rather than hardcoding it is the same move as `adaptive_gap`,
    and for the same reason — one fixed list cannot fit every speaker or subject.
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
    def gap_before(self) -> float:
        return self.utterances[0].gap_before

    @property
    def ends_on_punctuation(self) -> bool:
        return self.utterances[-1].ends_on_punctuation

    def overlaps(self, other: "Candidate", *, pad: float = 0.0) -> bool:
        return self.start - pad < other.end and other.start - pad < self.end


def adaptive_gap(words: list[Word], *, bins: int = GAP_BINS) -> float | None:
    """Find this speaker's own sentence-pause threshold, by Otsu's method.

    Inter-word silence is bimodal: the short gaps between words inside a phrase,
    and the longer breath at the end of a thought. Otsu picks the split that
    maximises the separation between those two populations, which means the
    threshold comes from the transcript rather than from a constant nobody can
    justify for every speaker.

    Returns None when the distribution cannot be split — too few gaps, or no
    variation in them — in which case the caller falls back to `DEFAULT_GAP`.
    """
    values = [
        g for g in (b.start - a.end for a, b in zip(words, words[1:])) if g > GAP_EPSILON
    ]
    if len(values) < 8:
        return None
    low, high = min(values), max(values)
    if high <= low:
        return None

    histogram = [0] * bins
    for value in values:
        histogram[min(bins - 1, int((value - low) / (high - low) * bins))] += 1

    total = len(values)
    weighted_total = sum(i * histogram[i] for i in range(bins))
    variances: list[float] = [-1.0] * bins
    below = 0
    weighted_below = 0.0
    for i in range(bins):
        below += histogram[i]
        if below == 0:
            continue
        above = total - below
        if above == 0:
            break
        weighted_below += i * histogram[i]
        mean_below = weighted_below / below
        mean_above = (weighted_total - weighted_below) / above
        variances[i] = below * above * (mean_below - mean_above) ** 2

    best_variance = max(variances)
    if best_variance <= 0:
        return None
    # Two well-separated populations make every bin between them equally good,
    # so the maximum is a plateau rather than a point. Taking the first bin puts
    # the threshold hard against the *lower* cluster — for gaps of 0.03 and 0.50
    # it returned 0.031. The midpoint of the plateau is the split that actually
    # sits between the two groups.
    top = [i for i, v in enumerate(variances) if v >= best_variance - 1e-12]
    best_bin = (top[0] + top[-1]) / 2.0

    threshold = low + (best_bin + 0.5) * (high - low) / bins
    return threshold if threshold >= MIN_GAP_THRESHOLD else None


def punctuation_ratio(words: list[Word]) -> float:
    if not words:
        return 0.0
    return sum(1 for w in words if _is_sentence_end(w)) / len(words)


def segment(
    transcript: Transcript,
    *,
    gap: float | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
) -> Segmentation:
    """Group a transcript's words into utterances.

    `gap` defaults to a threshold derived from this transcript's own silence
    distribution rather than a fixed constant.
    """
    words = transcript.words
    punctuated = punctuation_ratio(words) >= PUNCTUATION_FLOOR
    if gap is None:
        gap = adaptive_gap(words)
        if gap is None:
            gap = DEFAULT_GAP

    utterances: list[Utterance] = []
    current: list[Word] = []
    pending_gap = 0.0
    for i, word in enumerate(words):
        current.append(word)
        next_word = words[i + 1] if i + 1 < len(words) else None
        gap_after = (next_word.start - word.end) if next_word else 0.0

        by_punctuation = punctuated and _is_sentence_end(word)
        by_silence = next_word is not None and gap_after >= gap
        by_length = len(current) >= max_words
        if next_word is None or by_punctuation or by_silence or by_length:
            utterances.append(
                Utterance(
                    current,
                    gap_after=gap_after,
                    ends_on_punctuation=by_punctuation,
                    gap_before=pending_gap,
                )
            )
            current = []
            pending_gap = gap_after

    frequency: dict[str, int] = {}
    for word in words:
        token = _TOKEN.sub("", word.text.lower())
        if token:
            frequency[token] = frequency.get(token, 0) + 1

    starts = [u.words[0].text[:1] for u in utterances if u.words and u.words[0].text]
    alpha = [c for c in starts if c.isalpha()]
    capitalised = bool(alpha) and sum(1 for c in alpha if c.isupper()) / len(alpha) >= CAPITAL_FLOOR
    return Segmentation(utterances, punctuated, capitalised, gap, frequency)


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
