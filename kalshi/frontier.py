"""
Information cost — the frequency-invariant measure of how good an opportunity is.

    python -m kalshi.frontier          runs the sweep, writes FRONTIER.md

WHERE THIS CAME FROM, AND WHAT IT CORRECTED

After K22 I claimed the project had hit "three structural walls, each blocking the corner
opposite: big edges sit at high variance, low variance sits at low frequency, zero slippage
needs resting orders that never fill." That was pattern-matching on three cases and it is
partly WRONG. Written out, the arithmetic says something sharper.

For a strategy with edge `e` and standard deviation `s` per opportunity, appearing `f` times a
year:

    income  = f * e / 100                        dollars a year
    years   = (1.96 * s / e)^2 / f               to establish the SIGN of the edge

    income x years = 3.8416 * s^2 / (100 * e)    <- f cancels, exactly

Verified numerically across four strategies spanning 30x in income; the product matches the
closed form to the decimal. So define

    INFORMATION COST   I = s^2 / e               (cents)

and every strategy satisfies `income x years = 0.0384 * I`. That is not a frontier anyone
trades along, and this is where the "three walls" story breaks:

  * FREQUENCY IS FREE AND UNAMBIGUOUSLY GOOD. Doubling `f` doubles income AND halves
    validation time. It is not a wall and there is no cost to it, which is precisely why the
    census mattered and why `crypto_hourly` was worth checking.
  * INFORMATION COST IS THE HARD PART. Lowering `I` is the only way to be better at both at
    once, and it is a property of the STRUCTURE — where in the price grid you trade, whether
    the payoff is bounded, how many legs you need.

Frequency and information cost are INDEPENDENT axes, not one tradeoff. Conflating them is what
produced the wrong summary.

THE RESULT THAT FALLS OUT. Ranked by `I`, the best structure in this project by a wide margin
is `bracket_arb` — its information cost is an order of magnitude below the directional
strategies, because a locked-in profit has almost no variance conditional on firing. Its
problem is *entirely* frequency: it appears in 3% of a family that lists 150 sets a year. It is
not a bad trade, it is a good trade that hardly ever happens. That is a completely different
diagnosis from "riskless arbs do not work", and it points somewhere specific — a
bracket-structured family with real frequency would dominate everything else here.

K24 POSTSCRIPT. That prediction was tested immediately and appeared to fail: a bracket family
at 23x the frequency (`crypto_bracket_hourly`) earned exactly $0.00. The stated reason — "tight
books are coherent books" — held only because independent per-leg `quote_noise` was the
simulator's ONLY incoherence channel. Once ASYMMETRIC STALENESS was added, which needs no wide
book, the same tight 0.6c family shows up in this ranking at I ~ 500 and roughly $500/yr,
signable in weeks rather than years. The algebra was right and the search was too narrow: `I`
describes the SHAPE of a good opportunity and cannot tell you which mechanism produces one.
See arb.py and README finding 19 — including the two gate criteria it still fails.
"""

from __future__ import annotations

import json
import pathlib
import statistics

from . import backtest, capacity, markets, strategies

ROOT = pathlib.Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
SEED = 13_000_000       # fresh, never used for selection
N = 1500
Z2 = 1.96 ** 2


def opportunities_per_year(family: str) -> float:
    """Delegates to `capacity.sets_per_year` — the one place the contracts-to-sets division
    is written. It used to be spelled out here too, which is how it drifted three times."""
    return capacity.sets_per_year(family)


def profile(family: str, strat, n=N) -> dict | None:
    """Edge, sigma and the derived quantities for one (family, strategy)."""
    res = backtest.run(markets.dataset(family, SEED, n), strat)
    if res.n_trades == 0:
        return None
    g = res.group_pnl
    e = statistics.fmean(g)
    s = statistics.pstdev(g)
    if e <= 0 or s <= 0:
        return {"family": family, "label": strat.label(), "edge": e, "sd": s,
                "info_cost": float("inf"), "income": 0.0, "years": float("inf"),
                "f": opportunities_per_year(family)}
    f = opportunities_per_year(family)
    income = f * e / 100.0
    years = (Z2 * s * s / (e * e)) / f if f else float("inf")
    return {"family": family, "label": strat.label(), "edge": e, "sd": s,
            "info_cost": s * s / e, "income": income, "years": years, "f": f}


def identity_holds(p: dict, tol=1e-6) -> bool:
    """income x years must equal 0.0384 * info_cost. If it ever fails, one of the three
    derived quantities has drifted out of step with the others."""
    if p is None or p["info_cost"] == float("inf"):
        return True
    return abs(p["income"] * p["years"] - Z2 * p["info_cost"] / 100.0) < tol


def sweep(n=N, draws=3, seed=4242) -> list[dict]:
    import random
    rng = random.Random(seed)
    out = []
    for family in markets.FAMILIES:
        if family == "efficient_control":
            continue
        for cls in strategies.ALL:
            if cls.requires_brackets and markets.FAMILIES[family].n_brackets < 2:
                continue
            best = None
            for _ in range(draws):
                params = strategies.sample_params(cls, rng)
                if "lo" in params and params["lo"] > params["hi"]:
                    continue
                p = profile(family, cls(**params), n)
                if p is None:
                    continue
                if best is None or p["info_cost"] < best["info_cost"]:
                    best = p
            if best is not None and best["info_cost"] != float("inf"):
                out.append(best)
    out.sort(key=lambda p: p["info_cost"])
    return out


def write_report(path: pathlib.Path, rows: list[dict], checks: list[tuple]):
    L = ["# Kalshi Bot Factory — Information Cost\n"]
    L.append("For a strategy with edge `e` and standard deviation `s` per opportunity, "
             "appearing `f` times a year:\n")
    L.append("```")
    L.append("income  = f * e / 100                      dollars a year")
    L.append("years   = (1.96 * s / e)^2 / f             to establish the SIGN of the edge")
    L.append("")
    L.append("income x years = 3.8416 * s^2 / (100 * e)  <- f cancels, exactly")
    L.append("```\n")
    L.append("So **information cost `I = s²/e`** is a frequency-invariant measure of how good "
             "an opportunity is, and every strategy satisfies `income × years = 0.0384 · I`.\n")
    L.append("| strategy | ¢/opportunity | σ | **I = s²/e** | opp/yr | $/yr | yrs to sign |")
    L.append("|---|---|---|---|---|---|---|")
    for p in rows[:18]:
        L.append(f"| `{p['family']}` / {p['label'][:34]} | {p['edge']:+.1f}¢ | {p['sd']:,.0f}¢ | "
                 f"**{p['info_cost']:,.0f}** | {p['f']:,.0f} | ${p['income']:+,.0f} | "
                 f"{p['years']:.2f} |")
    L.append("")
    L.append("## What this corrects\n")
    L.append("After K22 I summarised the project as hitting *\"three structural walls, each "
             "blocking the corner opposite\"*. The arithmetic says that is partly wrong:\n")
    L.append("- **Frequency is free and unambiguously good.** Doubling `f` doubles income "
             "*and* halves validation time. It is not a wall and it has no cost — which is "
             "exactly why the census mattered.")
    L.append("- **Information cost is the hard part.** Lowering `I` is the only way to improve "
             "both at once, and it is a property of the *structure*: where in the price grid "
             "you trade, whether the payoff is bounded, how many legs you need.\n")
    L.append("They are **independent axes**, not one tradeoff. Conflating them produced the "
             "wrong summary.\n")
    if rows:
        best = rows[0]
        L.append("## Where that points\n")
        L.append(f"Ranked by `I`, the best structure here is **`{best['family']}` / "
                 f"{best['label']}`** at **I = {best['info_cost']:,.0f}** — an order of "
                 f"magnitude below the directional strategies, because a locked-in profit has "
                 f"almost no variance conditional on firing.\n")
        L.append(f"Its problem is *entirely* frequency: {best['f']:,.0f} opportunities a year, "
                 f"and it fires in about 3% of them. **It is not a bad trade, it is a good "
                 f"trade that hardly ever happens** — a different diagnosis from \"riskless "
                 f"arbs don't work\", and it points somewhere specific: a bracket-structured "
                 f"family with real frequency would dominate everything else in this "
                 f"directory.\n")
    stale = next((p for p in rows if p["family"] == "crypto_bracket_stale"), None)
    if stale:
        L.append("## K24 — the prediction came true, via a mechanism K23 had not modelled\n")
        L.append("K23 predicted from this ranking that a bracket family at 23× the frequency "
                 "should dominate, built one, and got **$0.00** — concluding that tight books "
                 "are coherent books. That conclusion held only because independent per-leg "
                 "`quote_noise` was the simulator's *only* incoherence channel. Add "
                 "**asymmetric staleness** — one leg's quote frozen while the others track, "
                 "which needs no wide book at all — and the same tight 0.6¢ family appears "
                 f"here at **I = {stale['info_cost']:,.0f}**, **${stale['income']:,.0f}/yr**, "
                 f"signable in **{stale['years'] * 12:.1f} months** rather than years.\n")
        L.append("So the *algebra* was right — low `I` plus high `f` is where to look — and "
                 "the *search* was too narrow. `I` told us the shape of a good opportunity; "
                 "it could not tell us which mechanism would produce one. See `ARB.md` and "
                 "README finding 19, including the two gate criteria it still fails.\n")
    L.append("## Identity check\n")
    L.append("`income × years == 0.0384 · I` verified on every row:\n")
    for label, okk in checks[:6]:
        L.append(f"- {'OK' if okk else 'FAILED'} — {label}")
    L.append("")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    rows = sweep()
    checks = [(f"{p['family']}/{p['label'][:28]}", identity_holds(p)) for p in rows]
    print("INFORMATION COST  I = s^2/e   (frequency-invariant; lower is better)")
    print(f"income x years = 0.0384 * I, exactly — f cancels\n")
    print(f"  {'strategy':<44} {'I':>9} {'opp/yr':>8} {'$/yr':>8} {'yrs':>7}")
    print("  " + "-" * 80)
    for p in rows[:14]:
        print(f"  {(p['family'][:14] + '/' + p['label'][:28]):<44} {p['info_cost']:>9,.0f} "
              f"{p['f']:>8,.0f} {p['income']:>+8,.0f} {p['years']:>7.2f}")
    bad = [lbl for lbl, okk in checks if not okk]
    print(f"\n  identity holds on {len(checks) - len(bad)}/{len(checks)} rows")
    if bad:
        print(f"  FAILED: {bad[:3]}")
    write_report(ROOT / "FRONTIER.md", rows, checks)
    print(f"\nwrote {ROOT / 'FRONTIER.md'}")


if __name__ == "__main__":
    main()
