"""The bot genome: what a candidate *is*, and how the factory breeds it.

A genome is a complete, serialisable trading rule — signals, how they combine,
the regime filters, position sizing, and the exits. It contains no fitted
weights beyond its own parameters, which is deliberate: the whole object is the
hypothesis, so a walk-forward test can hold it fixed and there is nothing to
silently refit on the test window.

`SearchSpace` is the other half of the story. It is what "expand until the goal
is reached" acts on — each expansion level unlocks more primitives, more market
families, more genes per bot, and wider parameter ranges.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, replace

import numpy as np

from . import signals
from .markets import universe

COMBINERS = ("weighted", "vote", "unanimous")
DIRECTIONS = ("both", "long", "short")
SIZINGS = ("fixed", "voltarget", "proportional")


# --------------------------------------------------------------------------- #
# search space
# --------------------------------------------------------------------------- #

@dataclass
class SearchSpace:
    """The reachable set of bots. Widened by the loop when progress stalls."""

    level: int = 1
    tier: int = 1                       # signal/filter/market tier unlocked
    max_genes: int = 2
    max_filters: int = 1
    allow_stops: bool = True
    allow_shorts: bool = True
    markets: tuple[str, ...] = ()
    population: int = 160
    finalists: int = 12
    per_market: int = 3                 # finalist slots any one family may take

    def __post_init__(self) -> None:
        if not self.markets:
            self.markets = tuple(m.name for m in universe.tradeable(self.tier))

    def signal_pool(self) -> list[str]:
        return signals.signal_names(self.tier)

    def filter_pool(self) -> list[str]:
        return signals.filter_names(self.tier)

    def expanded(self) -> "SearchSpace":
        """Next level. Order matters: cheap widenings first, exotica last.

        Past level 6 the *structural* dials are all at their ceiling — tier 3,
        five genes, three filters, every market unlocked — and an earlier version
        of this method then became a silent no-op, so "expand until the goal is
        reached" degenerated into resampling the same space forever. Beyond that
        point expansion buys search *effort* instead: a bigger population, more
        gauntlet slots, and a higher per-market cap so a family with a promising
        near-miss can have several variants tested in one generation.

        Spending more effort is self-penalising rather than a loosening of the
        standard: every extra candidate raises G6's luck bar, so a bot found by a
        longer search has to be correspondingly better to survive it.
        """
        lvl = self.level + 1
        tier = min(3, 1 + lvl // 2)
        return SearchSpace(
            level=lvl,
            tier=tier,
            max_genes=min(5, 2 + lvl // 2),
            max_filters=min(3, 1 + lvl // 3),
            allow_stops=True,
            allow_shorts=True,
            markets=tuple(m.name for m in universe.tradeable(tier)),
            population=min(1600, int(self.population * 1.5)),
            finalists=min(60, self.finalists + 4),
            per_market=min(6, self.per_market + (1 if lvl > 5 else 0)),
        )

    def describe(self) -> str:
        return (f"L{self.level}: tier={self.tier} genes<={self.max_genes} "
                f"filters<={self.max_filters} pop={self.population} "
                f"finalists={self.finalists} per_mkt={self.per_market} "
                f"markets={len(self.markets)}")


# --------------------------------------------------------------------------- #
# parameter sampling
# --------------------------------------------------------------------------- #

def sample_param(spec, rng: np.random.Generator, resolved: dict):
    kind = spec[0]
    if kind == "log":
        lo, hi = float(spec[1]), float(spec[2])
        return int(round(math.exp(rng.uniform(math.log(lo), math.log(hi)))))
    if kind == "int":
        return int(rng.integers(int(spec[1]), int(spec[2]) + 1))
    if kind == "float":
        return float(rng.uniform(float(spec[1]), float(spec[2])))
    if kind == "choice":
        return spec[1][int(rng.integers(0, len(spec[1])))]
    if kind == "bits":
        width = int(resolved.get(spec[1], 5))
        while True:
            bits = int(rng.integers(1, (1 << width) - 1))
            if 0 < bin(bits).count("1") < width:
                return bits
    raise ValueError(f"unknown param kind {kind}")


def mutate_param(spec, value, rng: np.random.Generator, resolved: dict, scale: float = 1.0):
    kind = spec[0]
    if kind == "log":
        lo, hi = float(spec[1]), float(spec[2])
        v = float(value) * math.exp(rng.normal(0.0, 0.35 * scale))
        return int(min(max(round(v), lo), hi))
    if kind == "int":
        lo, hi = int(spec[1]), int(spec[2])
        step = max(1, int(round(abs(rng.normal(0.0, 1.5 * scale)))))
        v = int(value) + step * (1 if rng.random() < 0.5 else -1)
        return int(min(max(v, lo), hi))
    if kind == "float":
        lo, hi = float(spec[1]), float(spec[2])
        v = float(value) + rng.normal(0.0, 0.2 * scale) * (hi - lo)
        return float(min(max(v, lo), hi))
    if kind == "choice":
        return spec[1][int(rng.integers(0, len(spec[1])))]
    if kind == "bits":
        width = int(resolved.get(spec[1], 5))
        bits = int(value)
        for _ in range(max(1, int(rng.integers(1, 3)))):
            bits ^= 1 << int(rng.integers(0, width))
        bits &= (1 << width) - 1
        if bits == 0 or bin(bits).count("1") == width:
            bits = 1 << int(rng.integers(0, width))
        return bits
    raise ValueError(f"unknown param kind {kind}")


def _sample_params(param_specs: dict, rng: np.random.Generator) -> dict:
    out: dict = {}
    # Two passes so a "bits" width can reference an already-sampled parameter.
    for name, spec in param_specs.items():
        if spec[0] != "bits":
            out[name] = sample_param(spec, rng, out)
    for name, spec in param_specs.items():
        if spec[0] == "bits":
            out[name] = sample_param(spec, rng, out)
    return out


# --------------------------------------------------------------------------- #
# genome
# --------------------------------------------------------------------------- #

@dataclass
class Gene:
    name: str
    params: dict = field(default_factory=dict)
    weight: float = 1.0
    mode: int = 1                      # +1 as written, -1 inverted

    def key(self) -> tuple:
        return (self.name, tuple(sorted(self.params.items())), self.mode)


@dataclass
class FilterGene:
    name: str
    params: dict = field(default_factory=dict)


@dataclass
class Genome:
    market: str
    genes: list[Gene]
    filters: list[FilterGene] = field(default_factory=list)
    combine: str = "weighted"
    entry_threshold: float = 0.25
    exit_threshold: float = 0.10
    direction: str = "both"
    sizing: str = "voltarget"
    base_size: float = 1.0
    target_vol: float = 0.15
    max_leverage: float = 2.0
    rebalance_band: float = 0.15
    atr_n: int = 20
    stop_atr: float | None = None
    take_atr: float | None = None
    trail_atr: float | None = None
    max_hold: int | None = None
    min_hold: int = 1
    dd_halt: float | None = None
    dd_resume: int = 20

    # lineage (excluded from the identity hash)
    generation: int = 0
    origin: str = "random"
    parents: tuple[str, ...] = ()

    # ---- identity ---------------------------------------------------------
    def strategy_dict(self) -> dict:
        d = {
            "market": self.market,
            "genes": [{"name": g.name, "params": _canon(g.params),
                       "weight": round(float(g.weight), 4), "mode": int(g.mode)}
                      for g in sorted(self.genes, key=lambda g: (g.name, str(g.params)))],
            "filters": [{"name": f.name, "params": _canon(f.params)}
                        for f in sorted(self.filters, key=lambda f: (f.name, str(f.params)))],
            "combine": self.combine,
            "entry_threshold": round(self.entry_threshold, 4),
            "exit_threshold": round(self.exit_threshold, 4),
            "direction": self.direction,
            "sizing": self.sizing,
            "base_size": round(self.base_size, 4),
            "target_vol": round(self.target_vol, 4),
            "max_leverage": round(self.max_leverage, 4),
            "rebalance_band": round(self.rebalance_band, 4),
            "atr_n": int(self.atr_n),
            "stop_atr": _r(self.stop_atr), "take_atr": _r(self.take_atr),
            "trail_atr": _r(self.trail_atr),
            "max_hold": self.max_hold, "min_hold": int(self.min_hold),
            "dd_halt": _r(self.dd_halt), "dd_resume": int(self.dd_resume),
        }
        return d

    @property
    def bot_id(self) -> str:
        blob = json.dumps(self.strategy_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(blob.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        d = self.strategy_dict()
        d.update({"bot_id": self.bot_id, "generation": self.generation,
                  "origin": self.origin, "parents": list(self.parents)})
        return d

    @staticmethod
    def from_dict(d: dict) -> "Genome":
        return Genome(
            market=d["market"],
            genes=[Gene(g["name"], dict(g["params"]), float(g.get("weight", 1.0)),
                        int(g.get("mode", 1))) for g in d["genes"]],
            filters=[FilterGene(f["name"], dict(f["params"])) for f in d.get("filters", [])],
            combine=d.get("combine", "weighted"),
            entry_threshold=float(d.get("entry_threshold", 0.25)),
            exit_threshold=float(d.get("exit_threshold", 0.1)),
            direction=d.get("direction", "both"),
            sizing=d.get("sizing", "voltarget"),
            base_size=float(d.get("base_size", 1.0)),
            target_vol=float(d.get("target_vol", 0.15)),
            max_leverage=float(d.get("max_leverage", 2.0)),
            rebalance_band=float(d.get("rebalance_band", 0.15)),
            atr_n=int(d.get("atr_n", 20)),
            stop_atr=d.get("stop_atr"), take_atr=d.get("take_atr"),
            trail_atr=d.get("trail_atr"),
            max_hold=d.get("max_hold"), min_hold=int(d.get("min_hold", 1)),
            dd_halt=d.get("dd_halt"), dd_resume=int(d.get("dd_resume", 20)),
            generation=int(d.get("generation", 0)), origin=d.get("origin", "random"),
            parents=tuple(d.get("parents", ())),
        )

    def signature(self) -> str:
        """Structural identity, ignoring parameter values.

        Used to keep the hall of fame diverse. Without it the hall fills with
        near-clones — one run produced eight entries that were the same rule with
        `lb=34` versus `lb=38` — and the factory then breeds exclusively from that
        one lineage.
        """
        genes = ",".join(sorted(f"{'-' if g.mode < 0 else ''}{g.name}" for g in self.genes))
        filts = ",".join(sorted(f.name for f in self.filters))
        return f"{self.market}|{genes}|{filts}|{self.combine}|{self.direction}|{self.sizing}"

    def n_params(self) -> int:
        return sum(len(g.params) for g in self.genes) + sum(len(f.params) for f in self.filters)

    def warmup(self) -> int:
        w = [signals.SIGNALS[g.name].warmup(g.params) for g in self.genes]
        w += [signals.FILTERS[f.name].warmup(f.params) for f in self.filters]
        w.append(int(self.atr_n) + 2)
        return int(max(w)) + 2

    def _ordered_genes(self) -> list["Gene"]:
        """Same canonical order the identity hash uses, so a genome and its
        round-tripped twin describe themselves identically."""
        return sorted(self.genes, key=lambda g: (g.name, str(g.params)))

    def describe(self) -> str:
        parts = []
        for g in self._ordered_genes():
            ps = ",".join(f"{k}={_fmt(v)}" for k, v in sorted(g.params.items()))
            sign = "" if g.mode > 0 else "-"
            parts.append(f"{sign}{g.name}({ps})x{g.weight:.2f}")
        s = " + ".join(parts) if self.combine == "weighted" else f" {self.combine} ".join(parts)
        flt = "".join(f" | {f.name}({','.join(f'{k}={_fmt(v)}' for k, v in sorted(f.params.items()))})"
                      for f in sorted(self.filters, key=lambda f: (f.name, str(f.params))))
        exits = []
        if self.stop_atr:
            exits.append(f"stop {self.stop_atr:.1f}atr")
        if self.take_atr:
            exits.append(f"tp {self.take_atr:.1f}atr")
        if self.trail_atr:
            exits.append(f"trail {self.trail_atr:.1f}atr")
        if self.max_hold:
            exits.append(f"hold<={self.max_hold}")
        if self.dd_halt:
            exits.append(f"halt@{self.dd_halt:.0%}dd")
        ex = ("  [" + ", ".join(exits) + "]") if exits else ""
        return (f"{s}{flt} -> thr {self.entry_threshold:.2f}/{self.exit_threshold:.2f} "
                f"{self.direction} {self.sizing}"
                f"{'' if self.sizing != 'voltarget' else f'@{self.target_vol:.0%}v'} "
                f"lev<={self.max_leverage:.1f}{ex}")


def _r(x):
    return None if x is None else round(float(x), 3)


def _fmt(v):
    return f"{v:.2f}" if isinstance(v, float) else str(v)


def _canon(params: dict) -> dict:
    out = {}
    for k, v in sorted(params.items()):
        out[k] = round(float(v), 4) if isinstance(v, float) else v
    return out


# --------------------------------------------------------------------------- #
# construction
# --------------------------------------------------------------------------- #

def random_genome(space: SearchSpace, rng: np.random.Generator,
                  market: str | None = None, generation: int = 0) -> Genome:
    mkt_name = market or space.markets[int(rng.integers(0, len(space.markets)))]
    spec = universe.get(mkt_name) if mkt_name in universe.BY_NAME else None

    pool = space.signal_pool()
    n_genes = 1 + int(rng.integers(0, space.max_genes))
    genes: list[Gene] = []
    used: set[str] = set()
    for _ in range(n_genes):
        name = pool[int(rng.integers(0, len(pool)))]
        if name in used and rng.random() < 0.7:
            continue
        used.add(name)
        genes.append(Gene(name, _sample_params(signals.SIGNALS[name].params, rng),
                          float(np.round(rng.uniform(0.4, 1.6), 3)),
                          1 if rng.random() < 0.72 else -1))
    if not genes:
        name = pool[int(rng.integers(0, len(pool)))]
        genes.append(Gene(name, _sample_params(signals.SIGNALS[name].params, rng)))

    filters: list[FilterGene] = []
    fpool = space.filter_pool()
    n_filt = int(rng.integers(0, space.max_filters + 1))
    for _ in range(n_filt):
        if not fpool:
            break
        name = fpool[int(rng.integers(0, len(fpool)))]
        if any(f.name == name for f in filters):
            continue
        filters.append(FilterGene(name, _sample_params(signals.FILTERS[name].params, rng)))

    max_lev = float(spec.max_leverage) if spec else 2.0
    allow_short = bool(spec.allow_short) if spec else True
    direction = "both" if (allow_short and space.allow_shorts) else "long"
    if rng.random() < 0.3:
        direction = "long" if rng.random() < 0.7 or not allow_short else "short"

    entry = float(np.round(rng.uniform(0.02, 0.6), 3))
    g = Genome(
        market=mkt_name,
        genes=genes,
        filters=filters,
        combine=COMBINERS[int(rng.integers(0, len(COMBINERS)))] if len(genes) > 1 else "weighted",
        entry_threshold=entry,
        exit_threshold=float(np.round(entry * rng.uniform(0.1, 0.9), 3)),
        direction=direction,
        sizing=SIZINGS[int(rng.integers(0, len(SIZINGS)))],
        base_size=float(np.round(rng.uniform(0.3, min(max_lev, 3.0)), 3)),
        target_vol=float(np.round(rng.uniform(0.05, 0.30), 3)),
        max_leverage=float(np.round(rng.uniform(0.5, max_lev), 3)),
        rebalance_band=float(np.round(rng.uniform(0.05, 0.6), 3)),
        atr_n=int(rng.integers(10, 40)),
        stop_atr=(float(np.round(rng.uniform(0.8, 6.0), 2))
                  if space.allow_stops and rng.random() < 0.45 else None),
        take_atr=(float(np.round(rng.uniform(1.0, 10.0), 2))
                  if space.allow_stops and rng.random() < 0.25 else None),
        trail_atr=(float(np.round(rng.uniform(1.0, 8.0), 2))
                   if space.allow_stops and rng.random() < 0.25 else None),
        max_hold=(int(rng.integers(2, 200)) if rng.random() < 0.3 else None),
        min_hold=int(rng.integers(1, 6)),
        dd_halt=(float(np.round(rng.uniform(0.1, 0.5), 3)) if rng.random() < 0.2 else None),
        dd_resume=int(rng.integers(5, 80)),
        generation=generation,
        origin="random",
    )
    return g


def mutate(parent: Genome, space: SearchSpace, rng: np.random.Generator,
           generation: int = 0, n_ops: int | None = None) -> Genome:
    child = replace(parent,
                    genes=[Gene(g.name, dict(g.params), g.weight, g.mode) for g in parent.genes],
                    filters=[FilterGene(f.name, dict(f.params)) for f in parent.filters],
                    generation=generation, origin="mutant", parents=(parent.bot_id,))
    ops = n_ops if n_ops is not None else 1 + int(rng.integers(0, 3))
    for _ in range(ops):
        _mutate_once(child, space, rng)
    _repair(child, space)
    return child


def _mutate_once(g: Genome, space: SearchSpace, rng: np.random.Generator) -> None:
    r = rng.random()
    pool = space.signal_pool()
    if r < 0.34 and g.genes:                                   # tweak a gene parameter
        gene = g.genes[int(rng.integers(0, len(g.genes)))]
        specs = signals.SIGNALS[gene.name].params
        if specs:
            key = list(specs)[int(rng.integers(0, len(specs)))]
            gene.params[key] = mutate_param(specs[key], gene.params.get(key), rng, gene.params)
            for k2, sp2 in specs.items():                       # keep bit-widths legal
                if sp2[0] == "bits" and k2 != key:
                    width = int(gene.params.get(sp2[1], 5))
                    gene.params[k2] = int(gene.params[k2]) & ((1 << width) - 1) or 1
        else:
            gene.mode *= -1
    elif r < 0.44 and g.genes:                                  # reweight / invert
        gene = g.genes[int(rng.integers(0, len(g.genes)))]
        if rng.random() < 0.5:
            gene.weight = float(min(max(gene.weight * math.exp(rng.normal(0, 0.4)), 0.1), 3.0))
        else:
            gene.mode *= -1
    elif r < 0.56:                                              # add / drop / swap a gene
        if len(g.genes) < space.max_genes and rng.random() < 0.6:
            name = pool[int(rng.integers(0, len(pool)))]
            g.genes.append(Gene(name, _sample_params(signals.SIGNALS[name].params, rng),
                                float(np.round(rng.uniform(0.4, 1.4), 3)),
                                1 if rng.random() < 0.7 else -1))
        elif len(g.genes) > 1:
            g.genes.pop(int(rng.integers(0, len(g.genes))))
        else:
            name = pool[int(rng.integers(0, len(pool)))]
            g.genes[0] = Gene(name, _sample_params(signals.SIGNALS[name].params, rng))
    elif r < 0.66:                                              # filters
        fpool = space.filter_pool()
        if g.filters and rng.random() < 0.45:
            if rng.random() < 0.5:
                g.filters.pop(int(rng.integers(0, len(g.filters))))
            else:
                f = g.filters[int(rng.integers(0, len(g.filters)))]
                specs = signals.FILTERS[f.name].params
                if specs:
                    key = list(specs)[int(rng.integers(0, len(specs)))]
                    f.params[key] = mutate_param(specs[key], f.params.get(key), rng, f.params)
        elif len(g.filters) < space.max_filters and fpool:
            name = fpool[int(rng.integers(0, len(fpool)))]
            if not any(f.name == name for f in g.filters):
                g.filters.append(FilterGene(name, _sample_params(signals.FILTERS[name].params, rng)))
    elif r < 0.76:                                              # thresholds / combine
        if rng.random() < 0.5:
            g.entry_threshold = float(min(max(g.entry_threshold + rng.normal(0, 0.08), 0.0), 0.9))
            g.exit_threshold = float(min(g.exit_threshold, g.entry_threshold * 0.95))
        else:
            g.combine = COMBINERS[int(rng.integers(0, len(COMBINERS)))]
    elif r < 0.88:                                              # sizing / risk
        pick = int(rng.integers(0, 4))
        if pick == 0:
            g.sizing = SIZINGS[int(rng.integers(0, len(SIZINGS)))]
        elif pick == 1:
            g.target_vol = float(min(max(g.target_vol * math.exp(rng.normal(0, 0.3)), 0.02), 0.6))
        elif pick == 2:
            g.max_leverage = float(min(max(g.max_leverage * math.exp(rng.normal(0, 0.3)), 0.2), 10.0))
        else:
            g.rebalance_band = float(min(max(g.rebalance_band + rng.normal(0, 0.1), 0.02), 0.9))
    else:                                                       # exits / direction / market
        pick = int(rng.integers(0, 5))
        if pick == 0:
            g.stop_atr = None if g.stop_atr and rng.random() < 0.4 else \
                float(np.round(min(max((g.stop_atr or 3.0) * math.exp(rng.normal(0, 0.35)), 0.4), 12.0), 2))
        elif pick == 1:
            g.take_atr = None if g.take_atr and rng.random() < 0.5 else \
                float(np.round(min(max((g.take_atr or 4.0) * math.exp(rng.normal(0, 0.35)), 0.5), 20.0), 2))
        elif pick == 2:
            g.trail_atr = None if g.trail_atr and rng.random() < 0.5 else \
                float(np.round(min(max((g.trail_atr or 3.0) * math.exp(rng.normal(0, 0.35)), 0.5), 15.0), 2))
        elif pick == 3:
            g.max_hold = None if g.max_hold and rng.random() < 0.4 else \
                int(min(max(int((g.max_hold or 40) * math.exp(rng.normal(0, 0.5))), 2), 500))
        else:
            g.direction = DIRECTIONS[int(rng.integers(0, len(DIRECTIONS)))]


def crossover(a: Genome, b: Genome, space: SearchSpace, rng: np.random.Generator,
              generation: int = 0) -> Genome:
    """Genes from both parents, everything else inherited field-by-field.

    Cross-market pairings are allowed: the child takes one parent's market, so a
    rule that worked on FX gets tried on crypto. That is where most of the
    cross-market generalisation in the hall of fame comes from.
    """
    pool = [Gene(g.name, dict(g.params), g.weight, g.mode) for g in (a.genes + b.genes)]
    rng.shuffle(pool)
    keep: list[Gene] = []
    seen: set[tuple] = set()
    for gene in pool:
        if len(keep) >= space.max_genes:
            break
        if gene.key() in seen:
            continue
        seen.add(gene.key())
        keep.append(gene)
    src = a if rng.random() < 0.5 else b
    child = replace(
        src,
        genes=keep or [Gene(a.genes[0].name, dict(a.genes[0].params))],
        filters=[FilterGene(f.name, dict(f.params))
                 for f in (a.filters if rng.random() < 0.5 else b.filters)][: space.max_filters],
        market=(a if rng.random() < 0.5 else b).market,
        combine=(a if rng.random() < 0.5 else b).combine,
        entry_threshold=(a if rng.random() < 0.5 else b).entry_threshold,
        exit_threshold=(a if rng.random() < 0.5 else b).exit_threshold,
        sizing=(a if rng.random() < 0.5 else b).sizing,
        target_vol=(a if rng.random() < 0.5 else b).target_vol,
        max_leverage=(a if rng.random() < 0.5 else b).max_leverage,
        stop_atr=(a if rng.random() < 0.5 else b).stop_atr,
        take_atr=(a if rng.random() < 0.5 else b).take_atr,
        trail_atr=(a if rng.random() < 0.5 else b).trail_atr,
        generation=generation, origin="crossover", parents=(a.bot_id, b.bot_id),
    )
    _repair(child, space)
    return child


def _repair(g: Genome, space: SearchSpace) -> None:
    """Keep a genome inside the market's own constraints and the search space."""
    if g.market not in space.markets and space.markets:
        g.market = space.markets[0] if g.market not in universe.BY_NAME else g.market
    spec = universe.BY_NAME.get(g.market)
    if spec is not None:
        g.max_leverage = float(min(g.max_leverage, spec.max_leverage))
        if not spec.allow_short and g.direction != "long":
            g.direction = "long"
    if not space.allow_shorts and g.direction != "long":
        g.direction = "long"
    g.genes = [ge for ge in g.genes if ge.name in signals.SIGNALS][: max(1, space.max_genes)]
    if not g.genes:
        g.genes = [Gene("momentum", {"lb": 20})]
    g.filters = [f for f in g.filters if f.name in signals.FILTERS][: space.max_filters]
    g.entry_threshold = float(min(max(g.entry_threshold, 0.0), 0.9))
    g.exit_threshold = float(min(max(g.exit_threshold, 0.0), g.entry_threshold * 0.99))
    g.min_hold = int(min(max(g.min_hold, 1), 100))
    if len(g.genes) == 1 and g.combine != "weighted":
        g.combine = "weighted"


# --------------------------------------------------------------------------- #
# archetypes: known strategies, seeded so the search starts from human priors
# --------------------------------------------------------------------------- #

def archetypes(market: str) -> list[Genome]:
    """Textbook strategies for a market. These are *seeds*, not answers — they
    go through exactly the same gauntlet as random genomes, and most of them
    fail it."""
    spec = universe.BY_NAME.get(market)
    lev = float(spec.max_leverage) if spec else 2.0
    short_ok = bool(spec.allow_short) if spec else True
    base = dict(market=market, filters=[], combine="weighted", direction="both" if short_ok else "long",
                sizing="voltarget", target_vol=0.15, max_leverage=min(2.0, lev),
                rebalance_band=0.2, atr_n=20, origin="archetype")
    out = [
        Genome(genes=[Gene("long_bias", {})], entry_threshold=0.0, exit_threshold=0.0,
               **{**base, "direction": "long", "sizing": "fixed", "base_size": 1.0}),
        Genome(genes=[Gene("ma_cross", {"fast": 20, "slow": 100})],
               entry_threshold=0.1, exit_threshold=0.02, **base),
        Genome(genes=[Gene("ma_cross", {"fast": 50, "slow": 200})],
               entry_threshold=0.05, exit_threshold=0.01, **base),
        Genome(genes=[Gene("momentum", {"lb": 60})], entry_threshold=0.15, exit_threshold=0.05, **base),
        Genome(genes=[Gene("momentum", {"lb": 250})], entry_threshold=0.1, exit_threshold=0.02, **base),
        Genome(genes=[Gene("breakout", {"n": 55})], entry_threshold=0.9, exit_threshold=0.2,
               **{**base, "trail_atr": 3.0}),
        Genome(genes=[Gene("zrev", {"lb": 5})], entry_threshold=0.3, exit_threshold=0.05,
               **{**base, "max_hold": 10}),
        Genome(genes=[Gene("rsi_rev", {"n": 14})], entry_threshold=0.4, exit_threshold=0.05,
               **{**base, "max_hold": 15}),
        Genome(genes=[Gene("bollinger", {"n": 20, "k": 2.0})], entry_threshold=0.5,
               exit_threshold=0.1, **{**base, "max_hold": 20}),
        Genome(genes=[Gene("momentum", {"lb": 120}), Gene("zrev", {"lb": 5}, 0.6)],
               entry_threshold=0.2, exit_threshold=0.05, **base),
    ]
    if spec is not None and abs(spec.carry_ann) > 1e-6:
        out.append(Genome(genes=[Gene("carry", {})], entry_threshold=0.0, exit_threshold=0.0,
                          **{**base, "sizing": "fixed", "base_size": 1.0}))
        out.append(Genome(genes=[Gene("carry", {}), Gene("ma_cross", {"fast": 20, "slow": 100})],
                          entry_threshold=0.2, exit_threshold=0.05, **base))
    for g in out:
        _repair(g, SearchSpace(tier=3, max_genes=5, max_filters=3))
    return out
