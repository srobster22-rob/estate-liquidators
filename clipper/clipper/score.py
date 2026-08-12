"""Scoring: rank candidate windows by how well they stand alone.

The model is deliberately a transparent weighted sum of named features rather
than anything learned. Two reasons: there is no labelled data here, and a clip
picker that cannot say *why* it chose a moment is impossible to tune against
taste. Every score carries its own breakdown.

Clip *length* is deliberately not scored. The band is a hard constraint the user
sets, and inside it no length is known to be better than another — see D-8, where
an unjustified 32-second target turned out to control the published selection
more strongly than any other constant in the project.

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

_WORD = re.compile(r"[^\w']+")

_HOOK_RE = [re.compile(p, re.IGNORECASE) for p in HOOK_PATTERNS]


# --------------------------------------------------------------------------
# Tuning
# --------------------------------------------------------------------------


@dataclass
class Weights:
    """Feature weights. Every value is a knob; none of them are measured yet."""

    hook: float = 3.0
    self_contained: float = 3.5
    closure: float = 2.5
    #: Raised from 1.0 at R3. Measured: on a fixture containing real dead air, a
    #: clip with a **10.5-second silence** in the middle of it ranked second and
    #: was published. At 3.0 it drops out of the top five. The feature was not
    #: weak, it was under-weighted — and the fixture that suggested otherwise
    #: simply contained no silences for it to find.
    pacing: float = 3.0

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
FRAGMENT_PENALTY = 0.35

#: A pronoun with no antecedent on screen. The viewer cannot resolve it.
DANGLING_PENALTY = 0.7


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


#: Silence that must precede an opening before it reads as a sentence start,
#: used only when capitalisation is unavailable. Real utterance boundaries in an
#: unpunctuated transcript are gap-defined and so sit at or above
#: `segment.DEFAULT_GAP` (0.65s); a cut made mid-utterance has no gap at all.
#: 0.35 separates those two populations with room on both sides.
OPENING_GAP = 0.35


def opens_mid_sentence(
    text: str, *, expect_capital: bool, gap_before: float | None = None
) -> bool:
    """Whether the clip starts partway through a sentence.

    Two signals, and the order matters:

    1. **Capitalisation**, when the transcript has it. Precise and unambiguous.
    2. **Silence before the opening**, otherwise. This is the auto-caption
       fallback, and it is *only* a fallback — on a punctuated transcript two
       sentences inside one cue are contiguous, so `gap_before` is legitimately
       0.0 at a perfectly clean boundary. Using gaps there would reject good
       openings wholesale.

    Without the fallback the whole mid-sentence defence was unavailable on
    YouTube auto-captions, which is the input this tool actually exists for.
    """
    if expect_capital:
        first = next((t for t in text.split() if t), "")
        return first[:1].islower()
    if gap_before is not None:
        return gap_before < OPENING_GAP
    return False


def self_containment(
    text: str,
    *,
    opening_words: int | None = None,
    utterance_count: int = 1,
    expect_capital: bool = False,
    gap_before: float | None = None,
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

    Penalties **multiply** rather than subtract. Subtracting let two differently
    broken openings both clamp to exactly 0.0 — "That distinction matters." loses
    0.7 for the pronoun and 0.35 for being a fragment, which is -0.05 before the
    floor — and once two clips read as an identical zero, an irrelevant 0.011
    difference in `duration_fit` decides between them. Multiplying keeps the
    ordering: heavily penalised openings stay distinguishable from disqualified
    ones, and nothing has to cross zero to get there.
    """
    tokens = _tokens(text)
    if not tokens:
        return 0.0
    score = 1.0

    if opens_mid_sentence(text, expect_capital=expect_capital, gap_before=gap_before):
        score *= 1.0 - MID_SENTENCE_PENALTY

    idx = 0
    while idx < len(tokens) and tokens[idx] in DISCOURSE_MARKERS:
        idx += 1
    if idx < len(tokens) and tokens[idx] in DANGLING_REFERENTS:
        score *= 1.0 - DANGLING_PENALTY
    if opening_words is not None and utterance_count > 1 and opening_words <= FRAGMENT_WORDS:
        score *= 1.0 - FRAGMENT_PENALTY
    return max(0.0, score)


#: How much a sentence-final mark is worth on its own. Not 1.0: punctuation can
#: be a comma-spliced full stop, and the gap is independent corroboration.
PUNCTUATION_EVIDENCE = 0.7


def closure(candidate: Candidate, *, closing_gap: float, punctuated: bool) -> float:
    """Whether the clip ends at a stop rather than mid-thought. 0..1.

    Two independent pieces of evidence — a sentence-final mark, and silence after
    the last word — combined as a soft OR, so either alone is suggestive and both
    together are strong.

    The silence term is **smooth and unbounded** rather than a threshold test,
    which is a correction. The previous version scored a flat 0.5 once the gap
    passed `closing_gap` and interpolated below it, putting a kink in the
    function exactly at the parameter's value. Measured at R6 on auto-captions,
    where the gap is the *only* ending signal: `closing_gap` sat at 0.80 against
    a candidate-gap median of 0.80, so it split the distribution through its own
    mode and any nudge reclassified a third of all candidates at once — 48% churn
    in the published selection, the most influential constant in the project once
    `duration_fit` was gone. A threshold belongs in a gap between populations,
    not inside one.

    It also fixes a structural handicap: the old form could never exceed 0.5 on
    an unpunctuated transcript, halving the range of the one feature carrying all
    the ending evidence there.
    """
    gap = max(0.0, candidate.gap_after)
    gap_evidence = gap / (gap + closing_gap) if closing_gap > 0 else 0.0
    mark_evidence = PUNCTUATION_EVIDENCE if (punctuated and candidate.ends_on_punctuation) else 0.0
    return 1.0 - (1.0 - mark_evidence) * (1.0 - gap_evidence)


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
    # A promise you joined halfway through was never made to you. Gating the
    # hook on a clean opening removed the last systematic way a truncated clip
    # could outscore the whole one it was cut from: truncation drags a hook
    # phrase into the scored window, which was worth more than the penalty for
    # the broken opening it created.
    mid_sentence = opens_mid_sentence(
        text, expect_capital=seg.capitalised, gap_before=candidate.gap_before
    )
    features = {
        "hook": 0.0 if mid_sentence else hook_strength(text),
        "self_contained": self_containment(
            text,
            opening_words=len(candidate.utterances[0].words) if candidate.utterances else None,
            utterance_count=len(candidate.utterances),
            expect_capital=seg.capitalised,
            gap_before=candidate.gap_before,
        ),
        "closure": closure(candidate, closing_gap=w.closing_gap, punctuated=seg.punctuated),
        "pacing": pacing(candidate, max_silence=w.max_silence),
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
