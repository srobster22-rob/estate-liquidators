"""Validation harness for the scorer.

There is no labelled data here and there is not going to be, so the question
"is the ranking good?" cannot be answered directly. These are the questions that
*can* be answered without labels, and each one has caught something real:

* **Discrimination** — does a feature vary at all? A feature pinned at its
  ceiling is a constant, and a constant cannot change a ranking. This is how
  `density` was caught in R1.
* **Redundancy** — do two features measure the same thing? Perfectly correlated
  features are one feature with two weights, which makes tuning incoherent.
* **Ablation** — if a feature is deleted, does the output change? This is the
  strongest test available: it asks about effect on the *decision*, not on the
  score, and a feature can have healthy variance while still never flipping a
  choice.
* **Boundary sensitivity** — does the scorer prefer a clean clip to a
  deliberately broken one? If not, output quality rests entirely on the
  segmenter never generating a bad window, which is a much weaker guarantee
  than it looks.
* **Parameter influence** — how much does each tuning constant move the
  published selection? A number nobody can justify, with a large influence, is
  the most dangerous thing in a scoring model: it looks like a decision and
  behaves like a coin toss. This is how `ideal_duration` was caught at R6.

Run it: ``python3 -m clipper.validate fixtures/talk.srt``
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .score import Scored, Weights, rank, score, select
from .segment import Candidate, Segmentation, Utterance, candidates, segment
from .transcript import load

FEATURES = ("hook", "self_contained", "closure", "pacing")


# --------------------------------------------------------------------------
# Discrimination
# --------------------------------------------------------------------------


@dataclass
class Discrimination:
    feature: str
    mean: float
    sd: float
    at_ceiling: float
    at_floor: float

    @property
    def dead(self) -> bool:
        """A feature that never varies cannot affect any ranking."""
        return self.sd < 1e-9


def discrimination(rows: list[Scored]) -> list[Discrimination]:
    out = []
    for name in FEATURES:
        values = [r.features[name] for r in rows]
        out.append(
            Discrimination(
                feature=name,
                mean=_mean(values),
                sd=_sd(values),
                at_ceiling=sum(1 for v in values if v >= 0.999) / len(values),
                at_floor=sum(1 for v in values if v <= 0.001) / len(values),
            )
        )
    return out


# --------------------------------------------------------------------------
# Redundancy
# --------------------------------------------------------------------------


def correlations(rows: list[Scored]) -> dict[tuple[str, str], float]:
    """Pearson r between every pair of features."""
    columns = {name: [r.features[name] for r in rows] for name in FEATURES}
    out: dict[tuple[str, str], float] = {}
    for i, a in enumerate(FEATURES):
        for b in FEATURES[i + 1 :]:
            out[(a, b)] = _pearson(columns[a], columns[b])
    return out


# --------------------------------------------------------------------------
# Ablation
# --------------------------------------------------------------------------


@dataclass
class Ablation:
    feature: str
    kept: int
    total: int

    @property
    def overlap(self) -> float:
        return self.kept / self.total if self.total else 1.0

    @property
    def inert(self) -> bool:
        """Deleting the feature changed nothing about what would be published."""
        return self.kept == self.total


def ablation(
    cands: list[Candidate], seg: Segmentation, weights: Weights | None = None, *, count: int = 5
) -> list[Ablation]:
    """Zero each feature's weight in turn and see whether the output moves."""
    weights = weights or Weights()
    baseline = {(s.start, s.end) for s in select(rank(cands, seg, weights), count=count)}
    out = []
    for name in FEATURES:
        modified = Weights(**{**_weight_dict(weights), name: 0.0})
        changed = {(s.start, s.end) for s in select(rank(cands, seg, modified), count=count)}
        out.append(Ablation(name, len(baseline & changed), len(baseline)))
    return out


def _weight_dict(weights: Weights) -> dict:
    return {f: getattr(weights, f) for f in Weights.__dataclass_fields__}


# --------------------------------------------------------------------------
# Boundary sensitivity
# --------------------------------------------------------------------------


def break_opening(candidate: Candidate, *, drop: float = 0.5) -> Candidate | None:
    """Return the same clip with its first utterance truncated mid-sentence.

    Objectively worse by construction — it opens partway through a sentence — and
    it needs no human judgement to label, which is the point.
    """
    first = candidate.utterances[0]
    cut = int(len(first.words) * drop)
    if cut < 1 or cut >= len(first.words):
        return None
    stump = Utterance(
        first.words[cut:],
        gap_after=first.gap_after,
        ends_on_punctuation=first.ends_on_punctuation,
    )
    return Candidate(candidate.start_index, candidate.end_index, [stump, *candidate.utterances[1:]])


def break_ending(candidate: Candidate, *, drop: float = 0.5) -> Candidate | None:
    """Return the same clip cut off partway through its final sentence."""
    last = candidate.utterances[-1]
    keep = int(len(last.words) * drop)
    if keep < 1 or keep >= len(last.words):
        return None
    stump = Utterance(last.words[:keep], gap_after=0.0, ends_on_punctuation=False)
    return Candidate(candidate.start_index, candidate.end_index, [*candidate.utterances[:-1], stump])


@dataclass
class Sensitivity:
    kind: str
    tested: int
    preferred_clean: int
    tied: int = 0

    @property
    def preferred_broken(self) -> int:
        return self.tested - self.preferred_clean - self.tied

    @property
    def rate(self) -> float:
        """Share of *decided* comparisons the clean clip wins.

        Ties are excluded rather than counted as losses. Scoring a tie as a
        failure made four features read 0% when they were simply neutral to the
        break, which is a different — and much less alarming — fact.
        """
        decided = self.tested - self.tied
        return self.preferred_clean / decided if decided else 1.0


def boundary_sensitivity(
    cands: list[Candidate], seg: Segmentation, weights: Weights | None = None, *, limit: int = 120
) -> list[Sensitivity]:
    """How often the scorer prefers a clean clip to a deliberately broken one."""
    weights = weights or Weights()
    out = []
    for kind, breaker in (("truncated opening", break_opening), ("truncated ending", break_ending)):
        tested = preferred = tied = 0
        for candidate in cands[:limit]:
            broken = breaker(candidate)
            if broken is None:
                continue
            tested += 1
            clean_score = score(candidate, seg, weights).total
            broken_score = score(broken, seg, weights).total
            if abs(clean_score - broken_score) < 1e-9:
                tied += 1
            elif clean_score > broken_score:
                preferred += 1
        out.append(Sensitivity(kind, tested, preferred, tied))
    return out


# --------------------------------------------------------------------------
# Parameter sensitivity
# --------------------------------------------------------------------------

#: Plausible ranges for every tuning constant that shapes the score.
#:
#: Clip length appears nowhere here because it is no longer scored at all — the
#: band is the user's stated constraint, enforced by `segment.candidates()`, and
#: R6 removed the feature that pretended to have a preference inside it.
SWEEPS: dict[str, list[float]] = {
    "hook": [1.0, 2.0, 3.0, 4.5, 6.0],
    "self_contained": [1.5, 2.5, 3.5, 5.0, 7.0],
    "closure": [1.0, 1.75, 2.5, 3.5, 5.0],
    "pacing": [1.0, 2.0, 3.0, 4.5, 6.0],
    "max_silence": [0.6, 0.9, 1.2, 1.8, 2.5],
    "closing_gap": [0.4, 0.6, 0.8, 1.2, 1.6],
}


@dataclass
class Influence:
    """How much one tuning constant controls what actually gets published."""

    constant: str
    mean_churn: float
    worst_churn: float

    @property
    def dominant(self) -> bool:
        return self.mean_churn > 0.35


def parameter_sensitivity(
    cands: list[Candidate],
    seg: Segmentation,
    weights: Weights | None = None,
    *,
    count: int = 5,
    sweeps: dict[str, list[float]] | None = None,
) -> list[Influence]:
    """Sweep each constant and measure how much the published selection moves.

    Ablation asks whether a *feature* earns its place. This asks the sharper
    question about the numbers themselves: if I cannot justify this value, how
    much damage does that do? A constant with no evidence behind it and a large
    influence is the most dangerous thing in a scoring model, because it looks
    like a decision and behaves like a coin toss.

    Measured at R6, `ideal_duration` scored 43% mean churn against under 10% for
    everything else — an unjustified number was choosing the output. It was
    replaced by a band-relative plateau, which is why it is not in `SWEEPS`.
    """
    weights = weights or Weights()
    sweeps = sweeps or SWEEPS
    baseline = {(s.start, s.end) for s in select(rank(cands, seg, weights), count=count)}
    out: list[Influence] = []
    for name, values in sweeps.items():
        churns = []
        for value in values:
            modified = Weights(**{**_weight_dict(weights), name: value})
            chosen = {
                (s.start, s.end) for s in select(rank(cands, seg, modified), count=count)
            }
            churns.append(1.0 - len(baseline & chosen) / max(1, len(baseline)))
        out.append(Influence(name, _mean(churns), max(churns)))
    out.sort(key=lambda i: -i.mean_churn)
    return out


# --------------------------------------------------------------------------
# Boundary agreement against a reference
# --------------------------------------------------------------------------

#: How far an inferred boundary may sit from a true one and still count.
BOUNDARY_TOLERANCE = 0.5


@dataclass
class Agreement:
    """How well one segmentation reproduces another's boundaries."""

    matched: int
    inferred: int
    reference: int

    @property
    def precision(self) -> float:
        """Share of inferred boundaries that are real. Low means over-segmenting."""
        return self.matched / self.inferred if self.inferred else 0.0

    @property
    def recall(self) -> float:
        """Share of real boundaries found. Low means under-segmenting."""
        return self.matched / self.reference if self.reference else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


def boundary_agreement(
    inferred: Segmentation,
    reference: Segmentation,
    *,
    tolerance: float = BOUNDARY_TOLERANCE,
) -> Agreement:
    """Score a segmentation against a trusted one covering the same speech.

    This is the project's only *ground truth*. It exists because `talk_auto.vtt`
    is `talk.srt` re-rendered as ASR — same words, same timings — so the
    punctuated twin's sentence boundaries are the answer key for what the
    unpunctuated one had to infer from silence alone.

    Measured at R9: **42% precision, 68% recall.** The auto path finds two thirds
    of the real boundaries and invents an equal number of false ones, which is
    the concrete cost of having no punctuation, and the direct cause of clips
    that open mid-sentence there.

    Deliberately *not* used to tune the gap threshold. The reference is
    synthetic, so optimising against it would fit the generator rather than
    speech — the mistake R2 and R7 each paid a round for.
    """
    truth = [u.start for u in reference.utterances]
    if not truth:
        return Agreement(0, len(inferred.utterances), 0)
    matched = sum(
        1
        for u in inferred.utterances
        if min(abs(u.start - t) for t in truth) <= tolerance
    )
    return Agreement(matched, len(inferred.utterances), len(truth))


# --------------------------------------------------------------------------
# Weight rescue
# --------------------------------------------------------------------------

#: Multipliers applied to a feature's default weight when asking whether *any*
#: weighting would let it matter.
RESCUE_FACTORS = (0.0, 0.25, 2.0, 4.0, 8.0)


@dataclass
class Rescue:
    feature: str
    changed_at: list[float]

    @property
    def irredeemable(self) -> bool:
        """No weighting whatsoever changes what gets published."""
        return not self.changed_at


def weight_rescue(
    cands: list[Candidate],
    seg: Segmentation,
    weights: Weights | None = None,
    *,
    count: int = 5,
    factors: tuple[float, ...] = RESCUE_FACTORS,
) -> list[Rescue]:
    """Ask whether a feature could matter *at any weight*, not just its current one.

    Ablation at the default weight conflates two very different diagnoses, and
    telling them apart decides whether a feature is fixable or finished:

    * **Under-weighted.** `pacing` was inert at R3 and turned out to be worth
      keeping — at 3.0 it removed a clip containing a 10.5-second silence that
      had been ranking second. Turning the knob rescued it.
    * **Irredeemable.** `payoff` fired on up to 105 candidates per text and still
      changed nothing at *eight times* its default weight, on every text tried.
      The clips it favoured were already winning or already losing on other
      features. No knob could rescue it, so R8 deleted it.

    A feature can also be legitimately inert because its hazard is absent — the
    long silence `pacing` guards against exists in only one fixture. That is a
    safety feature working, not a weak one, which is why this is reported per
    text rather than pooled.
    """
    weights = weights or Weights()
    current = _weight_dict(weights)
    baseline = {(s.start, s.end) for s in select(rank(cands, seg, weights), count=count)}
    out: list[Rescue] = []
    for name in FEATURES:
        changed = []
        for factor in factors:
            trial = Weights(**{**current, name: current[name] * factor})
            chosen = {(s.start, s.end) for s in select(rank(cands, seg, trial), count=count)}
            if chosen != baseline:
                changed.append(current[name] * factor)
        out.append(Rescue(name, changed))
    return out


# --------------------------------------------------------------------------
# Generalisation across texts
# --------------------------------------------------------------------------


@dataclass
class Verdict:
    """Whether a feature earns its place across *independent* content."""

    feature: str
    inert_on: list[str]
    tested_on: int
    irredeemable_on: list[str] = field(default_factory=list)

    @property
    def carries_its_weight(self) -> bool:
        return len(self.inert_on) * 2 <= self.tested_on

    @property
    def beyond_rescue(self) -> bool:
        """No weight helps it on any text tried. This is the deletion standard."""
        return bool(self.tested_on) and len(self.irredeemable_on) == self.tested_on


def earns_its_place(
    datasets: list[tuple[str, list[Candidate], Segmentation]],
    weights: Weights | None = None,
    *,
    count: int = 5,
) -> list[Verdict]:
    """Ask of each feature: on how many different texts does deleting it matter?

    Single-fixture ablation answers a narrower question than it appears to. A
    feature can look essential because one document happens to suit it — and
    every conclusion in this project rests on a handful of fixtures, most of them
    written by the same hand. Measured at R8, `payoff` changed the published
    selection on exactly one underlying text and was inert on the other three.

    The reverse error is just as real and cost a round to notice: a lexicon
    pattern that fires on no fixture is *untested*, not useless. Two of them
    revived the moment genuinely different prose was added. So this measures
    effect on the output, never coverage of a word list.
    """
    seen: dict[str, list[str]] = {name: [] for name in FEATURES}
    stuck: dict[str, list[str]] = {name: [] for name in FEATURES}
    for label, cands, seg in datasets:
        for result in ablation(cands, seg, weights, count=count):
            if result.inert:
                seen[result.feature].append(label)
        for result in weight_rescue(cands, seg, weights, count=count):
            if result.irredeemable:
                stuck[result.feature].append(label)
    return [
        Verdict(name, sorted(seen[name]), len(datasets), sorted(stuck[name]))
        for name in FEATURES
    ]


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sd(values: list[float]) -> float:
    if not values:
        return 0.0
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / len(values))


def _pearson(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    ma, mb = _mean(a), _mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else 0.0


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def report(path: str | Path, weights: Weights | None = None, *, count: int = 5) -> int:
    tr = load(path)
    seg = segment(tr)
    cands = candidates(seg)
    if not cands:
        print(f"{path}: no candidates to validate")
        return 1
    rows = [score(c, seg, weights) for c in cands]

    print(f"{path}: {len(tr.words)} words, {len(seg)} utterances, {len(cands)} candidates")
    print(f"punctuated={seg.punctuated} rolling={tr.rolling}\n")

    print("DISCRIMINATION  (sd=0 means the feature is a constant and cannot rank anything)")
    for d in discrimination(rows):
        flag = "  <-- DEAD" if d.dead else ""
        print(
            f"  {d.feature:15s} mean={d.mean:.3f} sd={d.sd:.3f} "
            f"ceiling={d.at_ceiling:5.0%} floor={d.at_floor:5.0%}{flag}"
        )

    print("\nREDUNDANCY  (|r| > 0.9 means two features are one feature with two weights)")
    strong = [(pair, r) for pair, r in correlations(rows).items() if abs(r) > 0.6]
    if not strong:
        print("  no pair above |r| = 0.6")
    for (a, b), r in sorted(strong, key=lambda kv: -abs(kv[1])):
        flag = "  <-- DUPLICATE" if abs(r) > 0.9 else ""
        print(f"  {a:15s} ~ {b:15s} r={r:+.3f}{flag}")

    print(f"\nABLATION  (top-{count} overlap when the feature's weight is zeroed)")
    for a in ablation(cands, seg, weights, count=count):
        flag = "  <-- INERT, changes nothing" if a.inert else ""
        print(f"  {a.feature:15s} keeps {a.kept}/{a.total} of the selection{flag}")

    print(f"\nPARAMETER INFLUENCE  (how much each constant moves the published top-{count})")
    for i in parameter_sensitivity(cands, seg, weights, count=count):
        flag = "  <-- DOMINANT, and it had better be justified" if i.dominant else ""
        print(f"  {i.constant:18s} mean churn {i.mean_churn:5.0%}  worst {i.worst_churn:5.0%}{flag}")

    print("\nBOUNDARY SENSITIVITY  (clean clip should beat a deliberately broken one)")
    for s in boundary_sensitivity(cands, seg, weights):
        flag = "  <-- BLIND" if s.rate < 0.6 else ""
        print(
            f"  {s.kind:20s} clean {s.preferred_clean:3d} / broken {s.preferred_broken:3d}"
            f" / tied {s.tied:3d}  -> {s.rate:.0%} of decided{flag}"
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python3 -m clipper.validate TRANSCRIPT [TRANSCRIPT ...]", file=sys.stderr)
        return 2
    worst = 0
    datasets = []
    for path in args:
        worst = max(worst, report(path))
        print()
        transcript = load(path)
        seg = segment(transcript)
        cands = candidates(seg)
        if cands:
            datasets.append((Path(path).name, cands, seg))

    if len(datasets) > 1:
        print(f"EARNS ITS PLACE  (deleting the feature changes nothing, per text)")
        for verdict in earns_its_place(datasets):
            where = ", ".join(verdict.inert_on) or "-"
            if verdict.beyond_rescue:
                flag = "  <-- NO WEIGHT HELPS, ON ANY TEXT: DELETE IT"
            elif not verdict.carries_its_weight:
                flag = "  <-- inert on most texts (check whether its hazard is absent)"
            else:
                flag = ""
            print(
                f"  {verdict.feature:15s} inert on {len(verdict.inert_on)}/"
                f"{verdict.tested_on}: {where}{flag}"
            )
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
