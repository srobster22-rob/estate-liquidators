"""Scoring: rank candidate windows by how well they stand alone.

The model is deliberately a transparent weighted sum of named features rather
than anything learned. Two reasons: there is no labelled data here, and a clip
picker that cannot say *why* it chose a moment is impossible to tune against
taste. Every score carries its own breakdown.

What the features are actually measuring is **self-containment**, not interest.
A clip fails when the viewer needs context they do not have — it opens on "and
that's why it works" with no antecedent, or stops before the point lands. That
failure is detectable from text alone. Whether the content is *interesting* is
not, and this module does not pretend otherwise.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .segment import Candidate, Segmentation

# --------------------------------------------------------------------------
# Lexicons
# --------------------------------------------------------------------------

#: Openers that promise a payoff. Matched against the first ~12 words.
HOOK_PATTERNS = [
    r"\bhere'?s (?:the|why|how|what|something)\b",
    r"\b(?:the|my|your) (?:biggest|worst|best|first|number one|most common) \w+",
    r"\b(?:the|a) (?:secret|trick|mistake|problem|reason|truth|catch|fix)\b",
    r"\b(?:nobody|no one|most people|everyone|everybody) (?:knows|tells|thinks|does|says)\b",
    r"\b(?:never|always) \w+",
    r"^(?:who|what|when|where|why|how|which)\b",
    r"\bif you(?:'| a)?re\b",
    r"\byou (?:probably |usually |always |never )?(?:think|thought|assume|believe)\b",
    r"\bstop \w+ing\b",
    r"\b(?:turns out|it turns out)\b",
    r"\b\d+\b",
]

#: First words that point at something the viewer has not seen. A clip opening
#: on one of these is broken regardless of what follows.
DANGLING_REFERENTS = {
    "it", "this", "that", "these", "those", "they", "them", "he", "she",
    "his", "her", "their", "its", "which", "who", "there",
}

#: Conversational throat-clearing. Weak openers, but not broken ones — spoken
#: English starts sentences this way constantly.
DISCOURSE_MARKERS = {
    "so", "and", "but", "or", "because", "then", "also", "plus",
    "well", "now", "okay", "ok", "right", "anyway", "yeah", "um", "uh", "like",
}

#: Phrases that mark a conclusion landing. A clip ending shortly after one of
#: these has resolved rather than merely stopped.
PAYOFF_PATTERNS = [
    r"\b(?:that'?s|this is) (?:why|how|what|the)\b",
    r"\bthe (?:point|whole point|result|upshot|takeaway) is\b",
    r"\bwhich means\b",
    r"\bso (?:that'?s|now you)\b",
    r"\bevery (?:single )?time\b",
    r"\bproblem solved\b",
]

_WORD = re.compile(r"[^\w']+")

_HOOK_RE = [re.compile(p, re.IGNORECASE) for p in HOOK_PATTERNS]
_PAYOFF_RE = [re.compile(p, re.IGNORECASE) for p in PAYOFF_PATTERNS]


# --------------------------------------------------------------------------
# Tuning
# --------------------------------------------------------------------------


@dataclass
class Weights:
    """Feature weights. Every value is a knob; none of them are measured yet."""

    hook: float = 3.0
    self_contained: float = 3.5
    closure: float = 2.5
    duration_fit: float = 1.5
    #: Raised from 1.0 at R3. Measured: on a fixture containing real dead air, a
    #: clip with a **10.5-second silence** in the middle of it ranked second and
    #: was published. At 3.0 it drops out of the top five. The feature was not
    #: weak, it was under-weighted — and the fixture that suggested otherwise
    #: simply contained no silences for it to find.
    pacing: float = 3.0
    payoff: float = 1.5

    #: Target clip length in seconds, and the half-width over which the fit
    #: score decays to zero.
    ideal_duration: float = 32.0
    duration_tolerance: float = 28.0

    #: The longest internal silence a clip may contain before it starts to lose
    #: points. A pause this long reads as a beat; much longer reads as a stall.
    max_silence: float = 1.2

    #: A gap this long after the last word counts as a full stop even when the
    #: transcript carries no punctuation.
    closing_gap: float = 0.8

    @classmethod
    def load(cls, path: str | Path) -> "Weights":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------


def _tokens(text: str) -> list[str]:
    return [t for t in _WORD.split(text.lower()) if t]


def hook_strength(text: str, *, window: int = 12) -> float:
    """How strongly the opening promises something. 0..1."""
    opening = " ".join(_tokens(text)[:window])
    if not opening:
        return 0.0
    hits = sum(1 for rx in _HOOK_RE if rx.search(opening))
    return min(1.0, hits / 2.0)


#: An opening utterance this short, followed by more, is a sentence fragment
#: left over from a list the viewer never saw — "All fine.", "Not before."
FRAGMENT_WORDS = 3


#: A lower-case opening word, in a transcript that otherwise capitalises
#: sentences, means the clip begins partway through one.
#:
#: Set to the full 1.0 rather than a partial penalty, on purpose. This feature
#: asks whether the opening stands on its own; a clip that starts halfway
#: through a sentence does not stand at all, so the answer is zero rather than
#: "somewhat". At 0.6 it was *less* than the 0.7 charged for a dangling pronoun,
#: which meant "not your starter" scored higher than "And it is not your
#: starter" — a fragment beating a whole sentence. It still only zeroes one
#: feature of six, so a strong clip can survive it.
MID_SENTENCE_PENALTY = 1.0


def self_containment(
    text: str,
    *,
    opening_words: int | None = None,
    utterance_count: int = 1,
    expect_capital: bool = False,
) -> float:
    """Whether the opening stands without prior context. 0..1.

    Discourse markers ("so", "okay", "and") carry **no penalty**, which is a
    reversal. They used to cost 0.15 each on the theory that they are weak
    openers. Measured at R3, that penalty was the single reason the scorer
    preferred a *deliberately broken* clip to a clean one 72% of the time:
    "Okay, so today I want to talk about…" was docked 0.30 while the fragment
    "the single most common reason…" — which opens mid-sentence — was docked
    nothing. The sign was backwards. A leading discourse marker is evidence that
    this *is* a sentence start, which is exactly what a clip opening needs.

    They are still skipped over when hunting for a dangling referent, so
    "And that is why it works" is caught on "that".
    """
    tokens = _tokens(text)
    if not tokens:
        return 0.0
    score = 1.0

    first_raw = next((t for t in text.split() if t), "")
    if expect_capital and first_raw[:1].islower():
        score -= MID_SENTENCE_PENALTY

    idx = 0
    while idx < len(tokens) and tokens[idx] in DISCOURSE_MARKERS:
        idx += 1
    if idx < len(tokens) and tokens[idx] in DANGLING_REFERENTS:
        score -= 0.7
    if opening_words is not None and utterance_count > 1 and opening_words <= FRAGMENT_WORDS:
        score -= 0.35
    return max(0.0, score)


def closure(candidate: Candidate, *, closing_gap: float, punctuated: bool) -> float:
    """Whether the clip ends at a stop rather than mid-thought. 0..1."""
    score = 0.0
    if punctuated and candidate.ends_on_punctuation:
        score += 0.7
    if candidate.gap_after >= closing_gap:
        score += 0.5
    elif candidate.gap_after > 0:
        score += 0.5 * (candidate.gap_after / closing_gap)
    return min(1.0, score)


def duration_fit(duration: float, *, ideal: float, tolerance: float) -> float:
    if tolerance <= 0:
        return 1.0
    return max(0.0, 1.0 - abs(duration - ideal) / tolerance)


def pacing(candidate: Candidate, *, max_silence: float, falloff: float = 2.0) -> float:
    """Penalise dead air *inside* the clip. 0..1.

    This replaced an average words-per-second measure, which had exactly zero
    variance across a talk: one speaker's mean rate barely moves, so the feature
    was a constant and could not affect any ranking. The thing a viewer actually
    notices is not the average rate but the single longest silence they have to
    sit through, so that is what is measured.
    """
    words = candidate.words
    if len(words) < 2:
        return 0.0
    worst = max((b.start - a.end) for a, b in zip(words, words[1:]))
    if worst <= max_silence:
        return 1.0
    return max(0.0, 1.0 - (worst - max_silence) / falloff)


def payoff_strength(text: str, *, tail_window: int = 25) -> float:
    tail = " ".join(_tokens(text)[-tail_window:])
    hits = sum(1 for rx in _PAYOFF_RE if rx.search(tail))
    return min(1.0, hits / 1.0)


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


@dataclass
class Scored:
    candidate: Candidate
    total: float
    features: dict[str, float] = field(default_factory=dict)

    @property
    def start(self) -> float:
        return self.candidate.start

    @property
    def end(self) -> float:
        return self.candidate.end

    @property
    def duration(self) -> float:
        return self.candidate.duration

    @property
    def text(self) -> str:
        return self.candidate.text

    def explain(self) -> str:
        parts = ", ".join(f"{k}={v:.2f}" for k, v in sorted(self.features.items()))
        return f"{self.total:.2f}  [{parts}]"


def score(candidate: Candidate, seg: Segmentation, weights: Weights | None = None) -> Scored:
    w = weights or Weights()
    text = candidate.text
    features = {
        "hook": hook_strength(text),
        "self_contained": self_containment(
            text,
            opening_words=len(candidate.utterances[0].words) if candidate.utterances else None,
            utterance_count=len(candidate.utterances),
            expect_capital=seg.capitalised,
        ),
        "closure": closure(candidate, closing_gap=w.closing_gap, punctuated=seg.punctuated),
        "duration_fit": duration_fit(
            candidate.duration, ideal=w.ideal_duration, tolerance=w.duration_tolerance
        ),
        "pacing": pacing(candidate, max_silence=w.max_silence),
        "payoff": payoff_strength(text),
    }
    total = sum(features[name] * getattr(w, name) for name in features)
    return Scored(candidate, total, features)


def rank(
    cands: list[Candidate], seg: Segmentation, weights: Weights | None = None
) -> list[Scored]:
    scored = [score(c, seg, weights) for c in cands]
    scored.sort(key=lambda s: (-s.total, s.start))
    return scored


def select(scored: list[Scored], *, count: int = 5, pad: float = 0.0) -> list[Scored]:
    """Greedily take the best non-overlapping clips, in timeline order."""
    chosen: list[Scored] = []
    for s in scored:
        if len(chosen) >= count:
            break
        if any(s.candidate.overlaps(c.candidate, pad=pad) for c in chosen):
            continue
        chosen.append(s)
    chosen.sort(key=lambda s: s.start)
    return chosen
