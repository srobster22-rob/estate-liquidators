"""The decay-rate curve.

Every headline this lab has ever produced was conditional on one number nobody
measured: how fast a planted edge fades. The catalogue's default — a halflife of
half the series toward a 35% floor — was chosen as *the mildest setting that
still certifies anything*, which is an honest reason to pick a parameter and a
terrible reason to trust a result derived from it. "Four strategies survive"
means nothing without "...at a 24-year halflife, and none at six years".

So: report a curve, not a count.

WHAT IS HELD FIXED. A curve is only readable if one thing varies. Running a
fresh search at each rate would vary three things at once — the decay, the
candidates the search happened to find, and the multiple-testing burden those
candidates carry — and the resulting differences would be uninterpretable. So
the sweep evaluates a **fixed, pre-registered panel** at every rung:

  * every archetype of every baseline family (the textbook priors, written down
    before any data was seen and never tuned), and
  * every distinct strategy the search has actually certified, deduplicated by
    structural signature.

The same genomes, the same gates, the same multiplicity denominator, the same
seeds. The only difference between two rungs is how fast the edge fades.

WHAT THIS IS NOT. It is not a claim about what a search *would* find at each
rate — a search pointed at a fast-decaying catalogue might discover a different
kind of bot better suited to it, and this panel cannot see that. It is the
narrower and cleaner claim: **these strategies, under this standard of proof,
survive down to here and no further.**

The rungs vary halflife with the floor pinned at 35%, so the axis is rate and
not depth, plus two off-axis points that matter more than any interpolation: a
deeper floor at a fast rate, and an abrupt break. Halflives are quoted as a
fraction of the series so daily, hourly and 15-minute families stay comparable;
at 12,000 daily bars, 1.0x is ~47.6 simulated years and 0.125x is ~6.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import replace

import numpy as np

from . import gauntlet, genome, metrics, engine
from .genome import Genome
from .markets import generate, universe

# --------------------------------------------------------------------------- #
# the rungs
# --------------------------------------------------------------------------- #

# (label, halflife as a fraction of n_bars, floor, break_at, break_mult)
#   halflife_frac <= 0  =>  stationary
RUNGS: list[tuple[str, float, float, float, float]] = [
    ("stationary", 0.0, 0.0, 0.0, 1.0),
    ("hl=1.00x", 1.000, 0.35, 0.0, 1.0),
    ("hl=0.50x", 0.500, 0.35, 0.0, 1.0),      # the catalogue default
    ("hl=0.25x", 0.250, 0.35, 0.0, 1.0),
    ("hl=0.125x", 0.125, 0.35, 0.0, 1.0),
    ("hl=0.125x/f10", 0.125, 0.10, 0.0, 1.0),  # fast *and* deep: the crowding case
    ("break@45%", 0.0, 0.0, 0.45, 0.15),       # publication, rule change, new venue
    # Diagnostic, not a point on the rate axis. Every gradual rung confounds two
    # things — how much edge there was *in total* and how much was left *at the
    # end* — because both fall together. A break placed at 85% separates them:
    # 87% of the edge is still there on average, and 15% of it at the close. If
    # certification tracks the average, this rung should behave like `hl=1.00x`;
    # if it tracks the terminal value, it should behave like `break@45%`.
    ("break@85%", 0.0, 0.0, 0.85, 0.15),
]

DEFAULT_RUNG = "hl=0.50x"

# The families the sweep varies. The two harsher twins already in the catalogue
# (`futures_trend_decay_daily`, `eq_largecap_break_daily`) are excluded: they are
# fixed points on this very axis, and re-decaying them would double-apply it.
BASE_FAMILIES = [
    "eq_index_daily", "eq_largecap_daily", "eq_smallcap_daily",
    "fx_major_daily", "fx_em_daily", "crypto_major_hourly", "crypto_alt_hourly",
    "futures_trend_daily", "commodity_meanrev_daily", "rates_daily",
    "eq_intraday_15m",
]

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOLFIX_CACHE = os.path.join(HERE, "state", "sweep_volfix.json")
SWEEP_STATE = os.path.join(HERE, "state", "decay_sweep.json")

# Multiplicity inputs, held constant across every rung so G6 is the same gate at
# every rate. `var_trial_sharpe` is the robust estimate from the 12,400-trial
# headline run rather than something re-fit here, because re-fitting it per rung
# would make the luck bar move with the decay too.
VAR_TRIAL_SHARPE = 0.1227


def variant_name(base: str, rung: str) -> str:
    return f"{base}~{rung}"


def base_of(name: str) -> str:
    return name.split("~", 1)[0]


def strategy_signature(g: Genome) -> str:
    """`Genome.signature()` with the rung stripped, so the same rule on
    `commodity_meanrev_daily~hl=0.25x` and on `~stationary` counts once."""
    sig = g.signature()
    market, rest = sig.split("|", 1)
    return f"{base_of(market)}|{rest}"


# --------------------------------------------------------------------------- #
# building the variant catalogue
# --------------------------------------------------------------------------- #

def _load_volfix() -> dict:
    if os.path.exists(VOLFIX_CACHE):
        with open(VOLFIX_CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _save_volfix(d: dict) -> None:
    os.makedirs(os.path.dirname(VOLFIX_CACHE), exist_ok=True)
    with open(VOLFIX_CACHE, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)


def build_variants(rung: str) -> list:
    """The baseline catalogue re-specified at one decay rate, **paired**.

    `seed_name` is pinned to the base family, so instance 7 of
    `commodity_meanrev_daily~hl=0.125x` is drawn from exactly the same
    innovation, jump and regime stream as instance 7 of `~stationary`. Without
    that, every rung would be a fresh set of random 47-year histories and the
    curve would be reporting instance luck alongside the decay — with 11
    families and ~50 instances each that noise is comparable to the effect.
    Paired, the comparison is one market that fades at different speeds.

    `vol_fix` is inherited from the base family for the same reason: see
    `volfix_drift()`, which measures the systematic effect of decay on realised
    volatility (it is smaller than the probe noise in the constant itself, so
    re-measuring per rung would inject more variation than it removes).
    """
    label, hl_frac, floor, brk_at, brk_mult = _rung(rung)
    out = []
    for base in BASE_FAMILIES:
        spec = universe.get(base)
        hl = hl_frac * spec.n_bars if hl_frac > 0 else 0.0
        out.append(replace(spec, name=variant_name(base, label), seed_name=base,
                           edge_decay_halflife=hl, edge_decay_floor=floor,
                           edge_break_at=brk_at, edge_break_mult=brk_mult,
                           notes=f"{base} at decay rung {label}"))
    return out


class use_catalogue:
    """Context manager that *replaces* the tradeable catalogue with one rung.

    The panel sweep answers "do these strategies survive a faster fade". It
    cannot answer the other half — "could a search find something *else* that
    does" — because the panel is fixed by construction. Swapping the catalogue
    lets the ordinary loop run against a decay rate, with its own ledger, its own
    multiplicity burden and the same gates.

    The base families *and the two harsher twins* are unregistered rather than
    left alongside, so `universe.tradeable()` returns exactly the rung and no
    candidate can wander onto a family fading at some other rate — which would
    make "what a search finds at rung X" quietly untrue. Controls are untouched:
    they have no edge to decay, and G3 needs them.
    """

    #: fixed points on this same axis; they belong to no rung
    OFF_LADDER = ("futures_trend_decay_daily", "eq_largecap_break_daily")

    def __init__(self, rung: str):
        self.rung = rung
        self.variants: list = []
        self._saved: list = []

    def __enter__(self) -> list:
        # Snapshot the list itself, not just the names: `register` appends, so
        # restoring family by family would silently reorder the catalogue, and
        # catalogue order drives which market the factory proposes for first.
        self._saved = universe.all_markets()
        self.variants = build_variants(self.rung)
        for base in list(BASE_FAMILIES) + list(self.OFF_LADDER):
            universe.unregister(base)
        for v in self.variants:
            universe.register(v)
        return self.variants

    def __exit__(self, *exc) -> None:
        for v in self.variants:
            universe.unregister(v.name)
        universe.reset(self._saved)
        return None


def volfix_drift(n_probe: int = 48, cache_path: str = VOLFIX_CACHE) -> dict:
    """Does fading the edge move realised volatility?

    It should, a little: the trend component carries `trend_frac^2` of the
    variance budget and `_noise_scale` subtracts that whether or not it decays,
    so a decayed family lands slightly *under* its volatility target. The
    question is whether the shortfall is big enough to matter next to the ~2%
    sampling noise in `vol_fix` itself.

    Measured paired — the probe instances share their seeds across rungs — so
    the sampling noise largely cancels and what is left is the systematic part.
    """
    cache = _load_volfix()
    out: dict[str, dict] = {}
    for label, *_ in RUNGS:
        for v in build_variants(label):
            key = v.name
            if key not in cache:
                cache[key] = generate.measure_vol_fix(v, n_probe=n_probe)
        _save_volfix(cache)
    for label, *_ in RUNGS:
        rows = {}
        for v in build_variants(label):
            base = universe.get(base_of(v.name))
            rows[base.name] = cache[v.name] / base.vol_fix - 1.0
        out[label] = {
            "mean_drift": float(np.mean(list(rows.values()))),
            "max_abs_drift": float(np.max(np.abs(list(rows.values())))),
            "by_market": {k: round(x, 4) for k, x in rows.items()},
        }
    _save_volfix(cache)
    return out


def _rung(label: str):
    for r in RUNGS:
        if r[0] == label:
            return r
    raise KeyError(f"unknown rung '{label}'; known: {[r[0] for r in RUNGS]}")


def mean_edge(spec) -> float:
    return float(np.mean(spec.edge_profile(spec.n_bars)))


def final_edge(spec) -> float:
    return float(spec.edge_profile(spec.n_bars)[-1])


# --------------------------------------------------------------------------- #
# the fixed panel
# --------------------------------------------------------------------------- #

def build_panel(variants: list, proven: list[dict] | None = None,
                per_signature: int = 3) -> list[Genome]:
    """Archetypes for every variant family, plus the search's certified bots
    re-pointed at their own family's variant.

    The proven bots are deduplicated by signature because the ledger holds up to
    13 parameter-clones of one rule, and gauntleting all of them at seven rungs
    would spend most of the budget re-proving the same strategy.
    """
    by_base = {base_of(v.name): v for v in variants}
    out: list[Genome] = []
    for v in variants:
        out.extend(genome.archetypes(v.name))
    seen: dict[str, int] = {}
    for p in (proven or []):
        g = Genome.from_dict(p["genome"])
        v = by_base.get(g.market)
        if v is None:
            continue
        sig = g.signature()
        if seen.get(sig, 0) >= per_signature:
            continue
        seen[sig] = seen.get(sig, 0) + 1
        # `bot_id` hashes the market, so a re-pointed bot gets a new id at every
        # rung. Carry the ledger id in `origin` so a row is still traceable back
        # to the run that certified it.
        out.append(replace(g, market=v.name, origin=f"proven:{g.bot_id}"))
    return out


# --------------------------------------------------------------------------- #
# the sweep
# --------------------------------------------------------------------------- #

def run_rung(rung: str, proven: list[dict] | None = None,
             cfg: gauntlet.GauntletConfig | None = None,
             seed: int = 7717, verbose: bool = True,
             per_signature: int = 3) -> dict:
    """Gauntlet the whole panel at one decay rate."""
    cfg = cfg or gauntlet.GauntletConfig()
    variants = build_variants(rung)
    for v in variants:
        universe.register(v)
    try:
        panel = build_panel(variants, proven, per_signature=per_signature)
        n_panel = len(panel)
        rng = np.random.default_rng(seed)
        rows, certified = [], []
        t0 = time.time()
        for i, g in enumerate(panel):
            v = gauntlet.run_gauntlet(
                g, cfg, n_trials=n_panel, var_trial_sharpe=VAR_TRIAL_SHARPE,
                rng=rng, cross_market=False, n_confirm_tests=n_panel)
            row = {
                "bot_id": g.bot_id, "market": base_of(g.market),
                "origin": g.origin, "describe": g.describe(),
                "signature": strategy_signature(g),
                "passed": v.passed, "failed_at": v.failed_at,
                "repl_alpha_sr": round(v.perf.get("repl_alpha_sr", 0.0), 3),
                "late_alpha_sr": round(v.perf.get("late_alpha_sr", 0.0), 3),
                "early_alpha_sr": round(v.perf.get("early_alpha_sr", 0.0), 3),
                "stress_alpha_sr": round(v.perf.get("stress_alpha_sr", 0.0), 3),
                "headroom": int(v.perf.get("burden_headroom", 0)),
                "perm_p": v.perf.get("perm_p"),
            }
            rows.append(row)
            if v.passed:
                certified.append(row)
                if verbose:
                    print(f"    CERTIFIED {g.bot_id} {base_of(g.market)}  "
                          f"replSR {row['repl_alpha_sr']:+.2f} late {row['late_alpha_sr']:+.2f} "
                          f"headroom {row['headroom']:,}", flush=True)
            if verbose and (i + 1) % 25 == 0:
                print(f"    ...{i + 1}/{n_panel} ({time.time() - t0:.0f}s)", flush=True)
        sigs = sorted({r["signature"] for r in certified})
        fails: dict[str, int] = {}
        for r in rows:
            k = r["failed_at"] or "PASSED"
            fails[k] = fails.get(k, 0) + 1
        return {
            "rung": rung,
            "n_panel": n_panel,
            "n_certified": len(certified),
            "n_distinct": len(sigs),
            "signatures": sigs,
            "markets": sorted({r["market"] for r in certified}),
            "mean_edge": round(float(np.mean([mean_edge(v) for v in variants])), 4),
            "final_edge": round(float(np.mean([final_edge(v) for v in variants])), 4),
            "fail_counts": fails,
            "seconds": round(time.time() - t0, 1),
            "rows": rows,
        }
    finally:
        for v in variants:
            universe.unregister(v.name)


def achievable(rung: str, n_instances: int = 6) -> list[dict]:
    """The mechanism, measured separately from the gates: what the best
    archetype makes gross and net on each family at this rate.

    Gross alpha should fall roughly in proportion to the mean edge profile.
    Net alpha should fall *faster*, because costs do not decay — and the gap
    between those two curves is the entire reason certification collapses well
    before the edge does.
    """
    variants = build_variants(rung)
    for v in variants:
        universe.register(v)
    try:
        out = []
        for v in variants:
            series = [generate.cached(v, i) for i in list(universe.SEARCH_POOL)[:n_instances]]
            best_gross, best_net = -9.0, -9.0
            for g in genome.archetypes(v.name):
                gr = float(np.median([metrics.evaluate(engine.run(s, g, cost_mult=0.0)).alpha_sharpe
                                      for s in series]))
                nt = float(np.median([metrics.evaluate(engine.run(s, g)).alpha_sharpe
                                      for s in series]))
                best_gross = max(best_gross, gr)
                best_net = max(best_net, nt)
            out.append({
                "market": base_of(v.name), "rung": rung,
                "mean_edge": round(mean_edge(v), 4),
                "ceiling_sr": round(v.oracle_sharpe_ceiling(), 3),
                "best_gross_alpha_sr": round(best_gross, 3),
                "best_net_alpha_sr": round(best_net, 3),
                "bite": round(best_gross - best_net, 3),
            })
        return out
    finally:
        for v in variants:
            universe.unregister(v.name)


def run_sweep(rungs: list[str] | None = None, proven: list[dict] | None = None,
              state_path: str = SWEEP_STATE, resume: bool = True,
              verbose: bool = True, with_achievable: bool = True,
              per_signature: int = 3) -> dict:
    rungs = rungs or [r[0] for r in RUNGS]
    out: dict = {"rungs": {}, "achievable": {}, "version": 1}
    if resume and os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as fh:
            out = json.load(fh)
        out.setdefault("rungs", {})
        out.setdefault("achievable", {})
    for label in rungs:
        if label in out["rungs"]:
            if verbose:
                r = out["rungs"][label]
                print(f"[{label}] cached: {r['n_distinct']} distinct, "
                      f"{r['n_certified']} genomes", flush=True)
            continue
        if verbose:
            print(f"[{label}] gauntleting the panel...", flush=True)
        out["rungs"][label] = run_rung(label, proven, verbose=verbose,
                                       per_signature=per_signature)
        if with_achievable and label not in out["achievable"]:
            out["achievable"][label] = achievable(label)
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
        r = out["rungs"][label]
        if verbose:
            print(f"[{label}] {r['n_distinct']} distinct / {r['n_certified']} genomes "
                  f"of {r['n_panel']} tested, mean edge {r['mean_edge']:.2f}, "
                  f"{r['seconds']:.0f}s", flush=True)
    for label in rungs:
        if with_achievable and label not in out["achievable"]:
            out["achievable"][label] = achievable(label)
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #

def _years(frac: float) -> str:
    if frac <= 0:
        return "  --"
    return f"{frac * 12000 / 252.0:>4.0f}"


def _distinct(rows) -> int:
    return len({r["signature"] for r in rows if r["passed"]})


def format_curve(sweep: dict) -> str:
    """The headline curve.

    `arch` and `disc` are reported separately on purpose. The archetypes are a
    neutral panel — fixed textbook rules, never tuned, identical at every rung —
    so their column is the honest curve. The discovered bots were found by a
    search run against the `hl=0.50x` catalogue, so their column is fitted to
    that rung and *must* be expected to peak there; pooling the two would let
    that fit masquerade as a property of the decay rate.
    """
    order = [r[0] for r in RUNGS if r[0] in sweep.get("rungs", {})]
    head = (f"{'rung':<16}{'hl_yr':>6}{'edge':>6}{'end':>6}"
            f"{'arch':>6}{'disc':>6}{'distinct':>9}{'genomes':>8}"
            f"{'medSR':>7}{'medLate':>8}{'medHead':>12}  markets")
    lines = [head, "-" * len(head)]
    for label in order:
        r = sweep["rungs"][label]
        hl_frac = _rung(label)[1]
        cert = [c for c in r["rows"] if c["passed"]]
        arch = _distinct([c for c in r["rows"] if not c["origin"].startswith("proven")])
        disc = _distinct([c for c in r["rows"] if c["origin"].startswith("proven")])
        med_sr = np.median([c["repl_alpha_sr"] for c in cert]) if cert else float("nan")
        med_lt = np.median([c["late_alpha_sr"] for c in cert]) if cert else float("nan")
        med_hd = np.median([c["headroom"] for c in cert]) if cert else 0
        mk = ", ".join(r["markets"]) or "-"
        lines.append(
            f"{label:<16}{_years(hl_frac):>6}{r['mean_edge']:>6.2f}{r['final_edge']:>6.2f}"
            f"{arch:>6}{disc:>6}{r['n_distinct']:>9}{r['n_certified']:>8}"
            f"{med_sr:>7.2f}{med_lt:>8.2f}{int(med_hd):>12,}  {mk}")
    lines.append("")
    lines.append("arch = distinct strategies certified from the untuned archetype panel;")
    lines.append("disc = ditto from the bots the search certified at hl=0.50x (fitted to that rung).")
    return "\n".join(lines)


def format_achievable(sweep: dict) -> str:
    ach = sweep.get("achievable", {})
    order = [r[0] for r in RUNGS if r[0] in ach]
    if not order:
        return ""
    markets = sorted({row["market"] for label in order for row in ach[label]})
    head = f"{'market':<26}" + "".join(f"{lab.replace('hl=', ''):>15}" for lab in order)
    lines = ["gross alpha SR / net alpha SR of the best archetype, by rung",
             head, "-" * len(head)]
    for m in markets:
        cells = []
        for lab in order:
            row = next((r for r in ach[lab] if r["market"] == m), None)
            cells.append("             -" if row is None
                         else f"{row['best_gross_alpha_sr']:>7.2f}/{row['best_net_alpha_sr']:<7.2f}")
        lines.append(f"{m:<26}" + "".join(f"{c:>15}" for c in cells))
    # catalogue aggregates
    for key, lbl in (("best_gross_alpha_sr", "catalogue mean gross"),
                     ("best_net_alpha_sr", "catalogue mean net"),
                     ("mean_edge", "mean edge profile")):
        cells = [f"{np.mean([r[key] for r in ach[lab]]):>7.2f}       " for lab in order]
        lines.append(f"{lbl:<26}" + "".join(f"{c:>15}" for c in cells))
    return "\n".join(lines)


def survival_table(sweep: dict) -> str:
    """Per strategy, the fastest rung it still certifies at. This is the curve
    the headline actually needs: not how many survive, but which ones and how
    far down."""
    order = [r[0] for r in RUNGS if r[0] in sweep.get("rungs", {})]
    sigs: dict[str, dict] = {}
    for label in order:
        for row in sweep["rungs"][label]["rows"]:
            if row["passed"]:
                sigs.setdefault(row["signature"], {})[label] = row
    if not sigs:
        return "no strategy certified at any rung."
    head = f"{'strategy':<62}" + "".join(f"{lab.replace('hl=', '')[:9]:>10}" for lab in order)
    lines = [head, "-" * len(head)]
    for sig in sorted(sigs, key=lambda s: -len(sigs[s])):
        cells = []
        for lab in order:
            r = sigs[sig].get(lab)
            cells.append("    .     " if r is None else f"{r['repl_alpha_sr']:>9.2f} ")
        lines.append(f"{sig[:62]:<62}" + "".join(cells))
    return "\n".join(lines)
