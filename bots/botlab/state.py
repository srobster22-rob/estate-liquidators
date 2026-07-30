"""Persistent run state, so the loop is genuinely a loop.

Two things must survive a restart or the whole standard of proof collapses:

  * the **trial ledger** — every candidate ever screened, because the deflated
    Sharpe bar in G6 is a function of how many strategies the search has looked
    at. Losing the count would silently lower the bar on the next run.
  * the **hall of fame and archive** — otherwise each restart re-explores the
    same ground and re-tests bots already known to fail.

Written atomically (temp file + rename), so a kill mid-write cannot leave a
truncated ledger behind.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field

import numpy as np

from .genome import Genome, SearchSpace

STATE_VERSION = 1
MAX_TRIAL_SAMPLES = 20_000
MAX_ARCHIVE = 40_000
HALL_PER_SIGNATURE = 2       # at most 2 parameterisations of the same structure
HALL_PER_MARKET = 10         # and no single family may own the hall


@dataclass
class HallEntry:
    genome: dict
    fitness: float
    alpha_sharpe: float
    sharpe: float
    n_trades: int
    generation: int


@dataclass
class RunState:
    path: str
    generation: int = 0
    trials: int = 0
    trial_sharpes: list = field(default_factory=list)
    hall: list = field(default_factory=list)          # HallEntry dicts, best first
    proven: list = field(default_factory=list)        # {"genome":…, "verdict":…}
    gauntlet_runs: int = 0
    backtests: int = 0
    fail_counts: dict = field(default_factory=dict)
    seen: list = field(default_factory=list)          # bot_ids already screened
    space: dict = field(default_factory=dict)
    expansions: list = field(default_factory=list)
    log: list = field(default_factory=list)
    started: float = field(default_factory=time.time)
    seed: int = 20260730
    hall_size: int = 60

    # ---- lifecycle --------------------------------------------------------
    @staticmethod
    def load_or_new(path: str, space: SearchSpace, seed: int = 20260730) -> "RunState":
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            st = RunState(path=path)
            for k, v in d.items():
                if k != "path" and hasattr(st, k):
                    setattr(st, k, v)
            st._seen_set = set(st.seen)
            return st
        st = RunState(path=path, space=asdict(space), seed=seed)
        st._seen_set = set()
        return st

    def __post_init__(self) -> None:
        if not hasattr(self, "_seen_set"):
            self._seen_set = set(self.seen)

    def save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)) or ".", exist_ok=True)
        d = {k: v for k, v in asdict(self).items() if k != "path"}
        d["version"] = STATE_VERSION
        d["updated"] = time.time()
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1, default=_jsonable)
        os.replace(tmp, self.path)

    # ---- ledger -----------------------------------------------------------
    def is_new(self, bot_id: str) -> bool:
        return bot_id not in self._seen_set

    def record_trial(self, bot_id: str, alpha_sharpe: float) -> None:
        self.trials += 1
        self._seen_set.add(bot_id)
        if len(self.seen) < MAX_ARCHIVE:
            self.seen.append(bot_id)
        if len(self.trial_sharpes) < MAX_TRIAL_SAMPLES and np.isfinite(alpha_sharpe):
            self.trial_sharpes.append(round(float(alpha_sharpe), 4))

    def var_trial_sharpe(self) -> float:
        """Dispersion of screen Sharpes across the search — the input the
        deflated-Sharpe luck bar needs.

        Estimated **robustly**, from the interquartile range, and that choice is
        load-bearing rather than fussy. Deflated Sharpe wants the spread of trial
        Sharpes attributable to *chance* — how good the best of N plausible
        candidates looks for free. The raw population variance is not that. A
        random genome generator emits a long tail of structurally broken bots
        (over-levered, wrong-signed, ruined), and they dominate the second moment:
        measured over 2,340 trials, the population variance was 1.256 with a 1st
        percentile of -5.5 alpha Sharpe, while the interquartile range was 0.56.
        That inflated the luck bar to 0.776 annual Sharpe — above anything an
        honest single-asset strategy reaches — so G6 rejected every candidate
        including ones that had replicated on 20 fresh instances.

        The perverse incentive is the tell: with a population estimator, the more
        junk the generator emits, the harder it becomes to prove anything. Broken
        hypotheses are not lucky draws. IQR/1.349 is the Gaussian-consistent
        robust estimate and gives 0.175, for a luck bar of 0.29.
        """
        if len(self.trial_sharpes) < 30:
            return 0.09
        a = np.asarray(self.trial_sharpes, dtype=float)
        a = a[np.isfinite(a)]
        if a.size < 30:
            return 0.09
        iqr = float(np.subtract(*np.percentile(a, [75, 25])))
        v = (iqr / 1.349) ** 2
        return float(min(max(v, 0.02), 1.0))

    # ---- hall of fame -----------------------------------------------------
    def update_hall(self, entries: list[HallEntry]) -> None:
        """Merge new entries, then thin by structural signature.

        The cap per signature is what keeps the factory breeding from more than
        one lineage: an un-thinned hall filled up with eight copies of the same
        rule at slightly different lookbacks, and every subsequent generation
        mutated that one idea.
        """
        merged = {e["genome"]["bot_id"]: e for e in self.hall}
        for e in entries:
            d = asdict(e)
            bid = d["genome"]["bot_id"]
            if bid not in merged or d["fitness"] > merged[bid]["fitness"]:
                merged[bid] = d
        ranked = sorted(merged.values(), key=lambda e: -e["fitness"])
        kept: list[dict] = []
        per_sig: dict[str, int] = {}
        per_market: dict[str, int] = {}
        for e in ranked:
            g = Genome.from_dict(e["genome"])
            sig = g.signature()
            if per_sig.get(sig, 0) >= HALL_PER_SIGNATURE:
                continue
            if per_market.get(g.market, 0) >= HALL_PER_MARKET:
                continue
            per_sig[sig] = per_sig.get(sig, 0) + 1
            per_market[g.market] = per_market.get(g.market, 0) + 1
            kept.append(e)
            if len(kept) >= self.hall_size:
                break
        self.hall = kept

    def hall_genomes(self) -> list[Genome]:
        return [Genome.from_dict(e["genome"]) for e in self.hall]

    def note_failure(self, stage: str | None) -> None:
        key = stage or "unknown"
        self.fail_counts[key] = self.fail_counts.get(key, 0) + 1

    def proven_ids(self) -> set:
        return {p["genome"]["bot_id"] for p in self.proven}

    def proven_signatures(self) -> dict[str, list[str]]:
        """Distinct strategies -> the bot_ids that implement them."""
        out: dict[str, list[str]] = {}
        for p in self.proven:
            sig = Genome.from_dict(p["genome"]).signature()
            out.setdefault(sig, []).append(p["genome"]["bot_id"])
        return out

    def n_distinct_proven(self) -> int:
        """How many *distinct strategies* are proven, not how many genomes.

        The loop's target counts this. A first run "reached 3" with four proven
        bots that were two strategies each certified twice: `rsi_rev(n=14)` at
        gene weight 1.00 and at 1.82 — and with a single gene the weight
        normalises out, so those were the identical signal with a different entry
        threshold. Counting genomes would let the loop declare victory on
        cosmetic variation, and would let the portfolio claim diversification
        across legs that are the same bet.
        """
        return len(self.proven_signatures())

    def add_proven(self, genome: Genome, verdict_dict: dict) -> bool:
        if genome.bot_id in self.proven_ids():
            return False
        self.proven.append({"genome": genome.to_dict(), "verdict": verdict_dict,
                            "found_generation": self.generation,
                            "signature": genome.signature()})
        return True

    def elapsed(self) -> float:
        return time.time() - self.started


def _jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, set):
        return sorted(o)
    return str(o)
