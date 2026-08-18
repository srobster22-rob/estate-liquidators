"""Is survival a function of the *ratio* of gross edge to cost?

F21 found that a 30% cut in gross edge took about 90% of net alpha for a
strategy sitting near its cost floor, and concluded that this leverage — not the
decay itself — is what selects the survivors. That is an anecdote from one
strategy on one family. It also implies something checkable: if costs are a
fixed subtraction and edge a proportional one, then

    net_alpha(e, c)  ~=  a*e - b*c

for an edge multiplier `e` and a cost multiplier `c`. Under that model the
*sign* of net alpha depends only on `e/c` (positive iff e/c > b/a), while its
*size* does not — net alpha scales with c along any fixed ratio. So "survival is
a ratio property" is true exactly at a zero bar and false at any positive one,
and the gauntlet's bar is +0.35.

That distinction is worth measuring rather than asserting, because it decides how
to read the decay curve: if survival were purely a ratio, halving the edge and
halving the costs would be a wash and the decay curve would be a statement about
cost levels. If it is a plane, they are separate axes and the curve means what it
says.

The grid is paired throughout — same instances, same seeds, only `e` and `c`
change — and `e` is applied through the existing decay machinery (a one-bar
halflife onto a floor of `e` is a constant edge multiplier), so nothing about the
price process differs from the rest of the lab.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace

import numpy as np

from . import engine, genome, metrics
from .markets import generate, universe

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID_STATE = os.path.join(HERE, "state", "cost_lever.json")

EDGE_MULTS = [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2]
COST_MULTS = [0.5, 1.0, 1.5, 2.0, 3.0]

# The families the search has actually certified something on, plus one cheap and
# one expensive family, so the grid spans the cost range rather than one point.
GRID_FAMILIES = ["commodity_meanrev_daily", "eq_largecap_daily",
                 "futures_trend_daily", "eq_smallcap_daily"]


def edge_variant(base: str, e: float):
    """The same family with its predictable components scaled by `e`.

    A one-bar halflife onto a floor of `e` reaches `e` within a handful of bars
    and stays there, which is a constant multiplier expressed in the machinery
    that already exists — no second code path that could disagree with the one
    the gauntlet uses.
    """
    spec = universe.get(base)
    return replace(spec, name=f"{base}~e{e:.2f}", seed_name=base,
                   edge_decay_halflife=1.0, edge_decay_floor=float(e),
                   edge_break_at=0.0, edge_break_mult=1.0,
                   notes=f"{base} with the planted edge scaled to {e:.0%}")


def grid(families: list[str] | None = None, edges: list[float] | None = None,
         costs: list[float] | None = None, n_instances: int = 8,
         verbose: bool = True) -> list[dict]:
    families = families or GRID_FAMILIES
    edges = edges or EDGE_MULTS
    costs = costs or COST_MULTS
    rows = []
    for base in families:
        arche = genome.archetypes(base)
        for e in edges:
            v = edge_variant(base, e)
            universe.register(v)
            try:
                # Re-point the archetypes at the variant. Same rules, same
                # parameters — only the market's edge scale differs.
                bots = [replace(g, market=v.name) for g in arche]
                series = [generate.cached(v, i)
                          for i in list(universe.SEARCH_POOL)[:n_instances]]
                # Gross alpha does not depend on the cost multiplier, so it is
                # measured once per bot and reused across the cost row.
                gross = {g.bot_id: float(np.median([
                    metrics.evaluate(engine.run(s, g, cost_mult=0.0)).alpha_sharpe
                    for s in series])) for g in bots}
                for c in costs:
                    best_net, best_gross, best_bot = -9.0, -9.0, ""
                    for g in bots:
                        net = float(np.median([
                            metrics.evaluate(engine.run(s, g, cost_mult=c)).alpha_sharpe
                            for s in series]))
                        if net > best_net:
                            best_net, best_gross, best_bot = net, gross[g.bot_id], g.describe()
                    rows.append({"market": base, "edge_mult": e, "cost_mult": c,
                                 "ratio": round(e / c, 4),
                                 "net_alpha_sr": round(best_net, 4),
                                 "gross_alpha_sr": round(best_gross, 4),
                                 "bot": best_bot})
                    if verbose:
                        print(f"  {base:<26} e={e:.2f} c={c:.1f} "
                              f"net {best_net:+.3f} gross {best_gross:+.3f}", flush=True)
            finally:
                universe.unregister(v.name)
    return rows


def fit_plane(rows: list[dict]) -> dict:
    """Least squares net ~ a*e + b*c + k, per market, and how much of the
    variation a pure-ratio model leaves behind."""
    out = {}
    for m in sorted({r["market"] for r in rows}):
        sub = [r for r in rows if r["market"] == m]
        y = np.array([r["net_alpha_sr"] for r in sub])
        X = np.column_stack([[r["edge_mult"] for r in sub],
                             [r["cost_mult"] for r in sub],
                             np.ones(len(sub))])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r2_plane = 1.0 - float(np.sum((y - X @ beta) ** 2) / max(np.sum((y - y.mean()) ** 2), 1e-12))
        # A pure-ratio model: net depends only on e/c.
        R = np.column_stack([[r["ratio"] for r in sub], np.ones(len(sub))])
        br, *_ = np.linalg.lstsq(R, y, rcond=None)
        r2_ratio = 1.0 - float(np.sum((y - R @ br) ** 2) / max(np.sum((y - y.mean()) ** 2), 1e-12))
        out[m] = {"a_edge": round(float(beta[0]), 4), "b_cost": round(float(beta[1]), 4),
                  "intercept": round(float(beta[2]), 4),
                  "r2_plane": round(r2_plane, 4), "r2_ratio_only": round(r2_ratio, 4),
                  "breakeven_ratio": (round(float(-beta[1] / beta[0]), 3)
                                      if abs(beta[0]) > 1e-9 else None)}
    return out


def format_grid(rows: list[dict], bar: float = 0.35) -> str:
    lines = []
    for m in sorted({r["market"] for r in rows}):
        sub = [r for r in rows if r["market"] == m]
        edges = sorted({r["edge_mult"] for r in sub}, reverse=True)
        costs = sorted({r["cost_mult"] for r in sub})
        lines.append(f"\n{m}   net alpha SR of the best archetype "
                     f"(bold = clears the +{bar:.2f} replication bar)")
        corner = "edge / cost"
        lines.append(f"{corner:<12}" + "".join(f"{c:>10.1f}x" for c in costs))
        for e in edges:
            cells = []
            for c in costs:
                r = next((x for x in sub if x["edge_mult"] == e and x["cost_mult"] == c), None)
                if r is None:
                    cells.append(f"{'-':>11}")
                else:
                    mark = "*" if r["net_alpha_sr"] >= bar else " "
                    cells.append(f"{r['net_alpha_sr']:>10.2f}{mark}")
            lines.append(f"{e:<12.2f}" + "".join(cells))
    return "\n".join(lines)


def format_fit(fit: dict) -> str:
    head = (f"{'market':<26}{'a(edge)':>9}{'b(cost)':>9}{'k':>8}"
            f"{'R2 plane':>10}{'R2 ratio':>10}{'breakeven e/c':>15}")
    lines = [head, "-" * len(head)]
    for m, f in fit.items():
        be = "-" if f["breakeven_ratio"] is None else f"{f['breakeven_ratio']:.2f}"
        lines.append(f"{m:<26}{f['a_edge']:>9.3f}{f['b_cost']:>9.3f}{f['intercept']:>8.3f}"
                     f"{f['r2_plane']:>10.3f}{f['r2_ratio_only']:>10.3f}{be:>15}")
    return "\n".join(lines)


def run(state_path: str = GRID_STATE, **kw) -> dict:
    rows = grid(**kw)
    out = {"rows": rows, "fit": fit_plane(rows)}
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


# --------------------------------------------------------------------------- #
# the cost-floor diagnostic
# --------------------------------------------------------------------------- #

COST_MULTS_FLOOR = (1.0, 0.3, 0.1)


def cost_floor(families: list[str] | None = None, mults=COST_MULTS_FLOOR,
               n_instances: int = 8, verbose: bool = True) -> list[dict]:
    """Per family: how much of the archetype panel's alpha is behind the cost floor?

    Re-prices each family at a fraction of its costs and re-measures the best
    archetype. The answer separates two situations that look identical at 1x and
    call for opposite responses:

      * **cost-limited** — alpha climbs steeply as costs fall. The edge is there
        and the frictions are eating it, so the useful question is where to trade
        it more cheaply. `eq_intraday_15m` goes +0.00 -> +0.84 across a 10x cut.
      * **edge- or panel-limited** — alpha barely moves. Cheaper execution buys
        nothing because there is nothing waiting behind the costs, for these
        rules. `fx_major_daily` sits at +0.17 at every cost level.

    Both read as "does not certify" at shipped costs, and the difference is the
    whole decision. See FINDINGS.md F36.
    """
    from dataclasses import replace as _replace

    from . import engine, gauntlet, genome, metrics
    from .markets import generate, universe
    bar = gauntlet.GauntletConfig().min_repl_alpha_sr
    families = families or [m.name for m in universe.tradeable(4)]
    rows = []
    for fam in families:
        base = universe.get(fam)
        got = {}
        for mult in mults:
            c = base.costs
            cm = _replace(c, spread_bps=c.spread_bps * mult,
                          commission_bps=c.commission_bps * mult,
                          impact_coef_bps=c.impact_coef_bps * mult,
                          funding_bps_per_bar=c.funding_bps_per_bar * mult,
                          borrow_ann=c.borrow_ann * mult)
            spec = _replace(base, name=f"{fam}~c{mult}", seed_name=fam, costs=cm)
            universe.register(spec)
            try:
                series = [generate.cached(spec, i)
                          for i in list(universe.HOLDOUT_POOL)[:n_instances]]
                got[mult] = max(
                    float(np.median([metrics.evaluate(engine.run(s, g)).alpha_sharpe
                                     for s in series]))
                    for g in genome.archetypes(spec.name))
            finally:
                universe.unregister(spec.name)
        lo, hi = mults[0], mults[-1]
        rows.append({"market": fam, "by_mult": {str(k): round(v, 3) for k, v in got.items()},
                     "released": round(got[hi] - got[lo], 3),
                     "clears_at_shipped": got[lo] >= bar,
                     "clears_when_cheap": got[hi] >= bar,
                     "verdict": ("cost-limited" if got[hi] - got[lo] >= 0.15
                                 else "edge- or panel-limited")})
        if verbose:
            r = rows[-1]
            print(f"  {fam:<26}" + "".join(f"{got[m]:>9.2f}" for m in mults)
                  + f"   released {r['released']:+.2f}  {r['verdict']}", flush=True)
    return rows


def format_cost_floor(rows: list[dict], mults=COST_MULTS_FLOOR) -> str:
    head = f"{'market':<26}" + "".join(f"{m:>9}" for m in
                                       [f"{x:.1f}x" for x in mults]) + f"{'released':>10}  verdict"
    lines = [head, "-" * len(head)]
    for r in rows:
        lines.append(f"{r['market']:<26}"
                     + "".join(f"{r['by_mult'][str(m)]:>9.2f}" for m in mults)
                     + f"{r['released']:>10.2f}  {r['verdict']}")
    n_ship = sum(1 for r in rows if r["clears_at_shipped"])
    n_cheap = sum(1 for r in rows if r["clears_when_cheap"])
    lines.append("")
    lines.append(f"families whose best archetype clears the replication bar: "
                 f"{n_ship} at shipped costs, {n_cheap} at {mults[-1]:.1f}x")
    return "\n".join(lines)
