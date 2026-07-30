"""Combining proven bots — with the diversification caveat stated in the output,
not buried in a footnote.

The synthetic market families in this lab are generated **independently**. So a
portfolio of bots trading different families has structurally zero cross-family
correlation, and its combined Sharpe scales like sqrt(N). Real asset classes do
not behave that way: equities, credit, EM FX and crypto all correlate hard in a
stress event, which is precisely when the diversification is needed.

So every portfolio number here is reported twice — once under the lab's
independence assumption, and once under an assumed 0.3 cross-family correlation.
The second number is the one to plan with.
"""

from __future__ import annotations

import math

import numpy as np

from . import engine
from .genome import Genome
from .markets import generate, universe

ADVERSE_CROSS_CORR = 0.30


def _streams(g: Genome, pool, n_instances: int) -> tuple[np.ndarray, float]:
    """Concatenated residual (alpha) returns across instances, and bars/year."""
    spec = universe.get(g.market)
    idxs = list(pool)[:n_instances]
    chunks = []
    for i in idxs:
        s = generate.cached(spec, i)
        res = engine.run(s, g)
        r = res.active_ret
        m = res.active_market_ret[: r.size]
        if r.size < 8:
            continue
        vx = float(m.var(ddof=1))
        beta = float(np.cov(r, m, ddof=1)[0, 1] / vx) if vx > 1e-18 else 0.0
        chunks.append(r - beta * m)
    if not chunks:
        return np.zeros(0), spec.bars_per_year
    return np.concatenate(chunks), spec.bars_per_year


def dedupe(bots: list[Genome]) -> list[Genome]:
    """One genome per distinct strategy signature.

    Without this the portfolio double-counts: a run certified `rsi_rev(n=14)`
    twice at different gene weights (which, with one gene, normalise to the same
    signal) and the blend then claimed diversification from two legs that were
    the same bet. Risk parity across duplicated legs understates concentration
    exactly where it matters.
    """
    seen: dict[str, Genome] = {}
    for g in bots:
        seen.setdefault(g.signature(), g)
    return list(seen.values())


def build(bots: list[Genome], n_instances: int = 20, pool=None) -> dict:
    """Inverse-vol (risk-parity) blend of proven bots, on the stress pool."""
    pool = pool if pool is not None else universe.STRESS_POOL
    if not bots:
        return {"n_bots": 0}
    n_before = len(bots)
    bots = dedupe(bots)

    legs = []
    for g in bots:
        r, bpy = _streams(g, pool, n_instances)
        if r.size < 30:
            continue
        sd = float(r.std(ddof=1))
        if sd <= 1e-12:
            continue
        legs.append({
            "bot_id": g.bot_id, "market": g.market,
            "asset_class": universe.get(g.market).asset_class,
            "mu_ann": float(r.mean() * bpy),
            "sd_ann": float(sd * math.sqrt(bpy)),
            "alpha_sharpe": float(r.mean() / sd * math.sqrt(bpy)),
            "returns": r, "bpy": bpy,
        })
    if not legs:
        return {"n_bots": 0}

    n = len(legs)
    mu = np.asarray([l["mu_ann"] for l in legs])
    sd = np.asarray([l["sd_ann"] for l in legs])

    # Within-family correlation is measurable (same instances, same calendar).
    # Across families it is not — the generator made them independent.
    corr = np.eye(n)
    measured_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            if legs[i]["market"] != legs[j]["market"]:
                continue
            a, b = legs[i]["returns"], legs[j]["returns"]
            k = min(a.size, b.size)
            if k < 30 or a[:k].std() < 1e-15 or b[:k].std() < 1e-15:
                continue
            c = float(np.corrcoef(a[:k], b[:k])[0, 1])
            corr[i, j] = corr[j, i] = c
            measured_pairs += 1

    w = (1.0 / sd) / float((1.0 / sd).sum())

    def sharpe_with(rho_cross: float) -> float:
        C = corr.copy()
        for i in range(n):
            for j in range(i + 1, n):
                if legs[i]["market"] != legs[j]["market"]:
                    C[i, j] = C[j, i] = rho_cross
        cov = np.outer(sd, sd) * C
        var = float(w @ cov @ w)
        return float((w @ mu) / math.sqrt(var)) if var > 1e-18 else 0.0

    best_single = float(max(l["alpha_sharpe"] for l in legs))
    return {
        "n_bots": n,
        "n_genomes_before_dedupe": n_before,
        "legs": [{k: v for k, v in l.items() if k != "returns"} for l in legs],
        "weights": [round(float(x), 4) for x in w],
        "asset_classes": sorted({l["asset_class"] for l in legs}),
        "markets": sorted({l["market"] for l in legs}),
        "within_family_pairs_measured": measured_pairs,
        "portfolio_alpha_sharpe_lab": sharpe_with(0.0),
        "portfolio_alpha_sharpe_adverse": sharpe_with(ADVERSE_CROSS_CORR),
        "best_single_alpha_sharpe": best_single,
        "adverse_cross_corr": ADVERSE_CROSS_CORR,
    }


def format_summary(p: dict) -> str:
    if not p.get("n_bots"):
        return "no portfolio: fewer than one usable proven bot"
    single_family = len(p["markets"]) == 1
    lines = [f"{p['n_bots']} distinct strategies across {len(p['markets'])} market(s) "
             f"/ {len(p['asset_classes'])} asset class(es)"
             + (f"   [from {p['n_genomes_before_dedupe']} proven genomes]"
                if p.get("n_genomes_before_dedupe", 0) > p["n_bots"] else ""),
             f"  best single bot        alphaSR {p['best_single_alpha_sharpe']:+.2f}"]
    if single_family:
        # Both scenarios coincide, and saying so is the point: there is no
        # cross-family term to stress because there is no cross-family exposure.
        lines.append(f"  portfolio             alphaSR "
                     f"{p['portfolio_alpha_sharpe_lab']:+.2f}")
        lines.append("  NOTE: every leg trades the SAME market family, so the two "
                     "correlation scenarios")
        lines.append("        coincide and the blend buys no diversification at all — "
                     "it is one bet,")
        lines.append("        sized twice. Correlation between the legs is measured, "
                     "not assumed.")
    else:
        lines.append(f"  portfolio (lab, rho=0) alphaSR {p['portfolio_alpha_sharpe_lab']:+.2f}"
                     "   <- upper bound, independent synthetic markets")
        lines.append(f"  portfolio (rho={p['adverse_cross_corr']:.1f})    alphaSR "
                     f"{p['portfolio_alpha_sharpe_adverse']:+.2f}"
                     "   <- plan with this one")
    for leg, w in zip(p["legs"], p["weights"]):
        lines.append(f"    {w:5.1%}  {leg['bot_id']}  {leg['market']:<24} "
                     f"alphaSR {leg['alpha_sharpe']:+.2f}")
    return "\n".join(lines)
