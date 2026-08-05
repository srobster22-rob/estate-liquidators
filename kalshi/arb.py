"""
Bracket arbitrage — the opposite corner of the signal-to-noise tradeoff, and why it loses.

    python -m kalshi.arb          runs the analysis, writes ARB.md

WHY THIS WAS WORTH ANALYSING

K21 established that variance dominates edge: signal-to-noise is `edge / (100*sqrt(q(1-q)))`,
and the denominator moves far more across the price grid than any mispricing does. The logical
end of that argument is a structure with NO denominator at all. Bracket arbitrage is exactly
that. Buy all N mutually exclusive brackets for a total under 100c and exactly one pays 100c,
so the profit is locked at trade time:

    * per-set variance is ZERO. It cannot lose.
    * validation needs NO settled outcomes. One snapshot of the book proves the opportunity
      exists — you do not wait years for prints to land, which is the wall every directional
      strategy here ran into.

That is the best possible position on the axis K21 identified, so it deserved a real look
rather than the passing mention it had been getting.

WHAT KILLS IT, IN ONE LINE

    An N-leg arbitrage pays N x slippage to capture ONE margin.

The margin is the gap below 100 and it is captured once. Slippage is paid on every leg. So the
break-even per-leg slippage is `margin / N`, and on this simulator's index brackets the median
margin is **1c across 5 legs** — a break-even of **0.2 ticks**. The tick is 1c. The minimum
possible adverse move is therefore five times what the trade can afford, and one tick on each
leg turns 100% of opportunities into 1%.

So the riskless trade is riskless only if you fill all N legs at the quoted ask simultaneously.
Miss that and you are not holding an arbitrage, you are holding a directional position you
never chose. The leg count is leverage on execution risk and it points the wrong way — which is
the general reason multi-leg arbitrage is harder than the arithmetic suggests, and it is not
specific to Kalshi.

THE ONLY VERSION THAT COULD WORK is resting orders on every leg, since a maker fill happens at
your price with no slippage by definition. That trades slippage risk for FILL risk — you get
some legs and not others — and `maker_spread` already established that resting orders in this
simulator are negative at every fill rate from 0.15 to 1.0. Both doors are shut, for reasons
that are structural rather than parameter-dependent.
"""

from __future__ import annotations

import json
import pathlib
import statistics

from . import backtest, capacity, markets, strategies

ROOT = pathlib.Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

FAMILY = "index_bracket_daily"
SEED = 13_000_000          # fresh, never used for selection
N = 4000


def sets_per_year(family=FAMILY) -> float:
    """Bracket SETS, not contracts. The census counts contracts; a set is N of them, and the
    backtester measures per set. Confusing the two overstates income by exactly N — the same
    units bug K18 caught on the econ ladders."""
    fam = markets.FAMILIES[family]
    legs = max(fam.n_brackets, fam.n_rungs, 1)
    return capacity.MARKETS_PER_YEAR.get(family, 0) / legs


def margins(family=FAMILY, n=N) -> list[int]:
    """Every moment the asks summed below 100, and by how much."""
    out = []
    for g in markets.dataset(family, SEED, n):
        for t in range(g.steps):
            total = sum(leg.ask[t] for leg in g.legs)
            if total < 100:
                out.append(100 - total)
    out.sort()
    return out


def profile(family=FAMILY, n=N) -> dict:
    data = markets.dataset(family, SEED, n)
    st = strategies.bracket_arb(min_edge=0, qty=250)
    res = backtest.run(data, st)
    g = res.group_pnl
    fired = [x for x in g if x != 0]
    mean = statistics.fmean(g)
    sd = statistics.pstdev(g)
    spy = sets_per_year(family)
    return {
        "n_sets": len(g), "n_fired": len(fired),
        "fire_rate": len(fired) / len(g) if g else 0.0,
        "mean_when_fired": statistics.fmean(fired) if fired else 0.0,
        "losing_fires": sum(1 for x in fired if x < 0),
        "mean_per_set": mean, "sd_per_set": sd,
        "snr": mean / sd if sd else 0.0,
        "n_to_sign": (1.96 * sd / mean) ** 2 if mean > 0 else float("inf"),
        "sets_per_year": spy,
        "annual_dollars": spy * mean / 100.0,
        "contracts_per_fill": res.n_contracts / max(res.n_trades, 1),
    }


def slippage_sweep(family=FAMILY, n=N, ticks=(0, 1, 2)) -> list[tuple]:
    data = markets.dataset(family, SEED, n)
    st = strategies.bracket_arb(min_edge=0, qty=250)
    spy = sets_per_year(family)
    out = []
    for extra in ticks:
        res = backtest.run(data, st, backtest.Costs(extra_spread=extra))
        g = res.group_pnl
        fired = [x for x in g if x != 0]
        m = statistics.fmean(g)
        out.append((extra, m, spy * m / 100.0,
                    sum(1 for x in fired if x < 0), len(fired)))
    return out


def leg_leverage(margin_list: list[int], leg_counts=(2, 3, 5, 8)) -> list[tuple]:
    """Share of opportunities surviving one tick of slippage per leg, by leg count.

    Uses the SAME measured margin distribution for every leg count, which is the honest way
    to isolate the leg-count effect: it answers "if a margin of this size were spread over N
    legs, how often would it survive", not "what do 8-leg markets look like".
    """
    out = []
    for n_legs in leg_counts:
        cost = n_legs  # 1 tick each
        surv = sum(1 for m in margin_list if m > cost)
        out.append((n_legs, cost, surv / len(margin_list) if margin_list else 0.0))
    return out


def write_report(path: pathlib.Path, prof, marg, sweep, lev):
    q = lambda f: marg[int(f * (len(marg) - 1))] if marg else 0
    L = ["# Kalshi Bot Factory — Bracket Arbitrage\n"]
    L.append("The one structure in this project with **zero variance**: buy all N mutually "
             "exclusive brackets for under 100¢, exactly one pays 100¢, profit locked at trade "
             "time. K21 showed variance dominates edge, so a zero-variance trade is the best "
             "possible position on that axis and deserved a proper look.\n")
    L.append("It loses anyway, for a structural reason.\n")

    L.append("## What it is worth\n")
    L.append("| | |")
    L.append("|---|---|")
    L.append(f"| fires in | **{prof['fire_rate'] * 100:.1f}%** of bracket sets "
             f"({prof['n_fired']} of {prof['n_sets']:,}) |")
    L.append(f"| when it fires | {prof['mean_when_fired']:+,.0f}¢ |")
    L.append(f"| losing fires | **{prof['losing_fires']}** — riskless means this is zero |")
    L.append(f"| per set offered | {prof['mean_per_set']:+.2f}¢ |")
    L.append(f"| observations to sign the edge | {prof['n_to_sign']:,.0f} sets "
             f"= **{prof['n_to_sign'] / prof['sets_per_year']:.1f} years** |")
    L.append(f"| **annual income** | **${prof['annual_dollars']:,.0f}/yr** |")
    L.append("")
    L.append(f"Only {prof['sets_per_year']:.0f} bracket sets a year exist, so even a perfect "
             f"capture is a rounding error. That alone would end it — but the reason it fails "
             f"is more interesting and more general.\n")

    L.append("## The margin is 1¢ and it is shared across 5 legs\n")
    L.append("| percentile | margin (100 − Σ asks) |")
    L.append("|---|---|")
    for f, lbl in ((0.5, "median"), (0.75, "75th"), (0.9, "90th"), (0.99, "99th")):
        L.append(f"| {lbl} | {q(f)}¢ |")
    L.append(f"| max | {marg[-1] if marg else 0}¢ |")
    L.append("")
    L.append("## One tick of slippage destroys it\n")
    L.append("| slippage per leg | ¢/set | annual | fires that now LOSE |")
    L.append("|---|---|---|---|")
    for extra, m, ann, lose, fired in sweep:
        L.append(f"| +{extra} tick | {m:+.2f}¢ | ${ann:+,.0f} | **{lose}/{fired}** |")
    L.append("")
    L.append("## Why: an N-leg arb pays N × slippage to capture ONE margin\n")
    L.append("| legs | cost of 1 tick each | opportunities still profitable |")
    L.append("|---|---|---|")
    for n_legs, cost, surv in lev:
        L.append(f"| {n_legs} | {cost}¢ | {surv * 100:.0f}% |")
    L.append("")
    L.append("Break-even per-leg slippage is `margin / N`. At a median margin of "
             f"{q(0.5)}¢ over 5 legs that is **{q(0.5) / 5:.1f} ticks** — and **the tick is "
             "1¢**. The minimum possible adverse move is five times what the trade can "
             "afford. This is not a tuning problem; it is the price grid against the "
             "structure.\n")
    L.append("## Both doors are shut\n")
    L.append("The only version that survives slippage is **resting** orders on every leg, "
             "because a maker fill happens at your price by definition. That swaps slippage "
             "risk for fill risk — you get some legs and not others, leaving a directional "
             "position you never chose — and `maker_spread` already showed resting orders are "
             "negative here at **every** fill rate from 0.15 to 1.00.\n")
    L.append("So the zero-variance trade and the zero-slippage trade are each blocked by the "
             "other's risk. The general lesson outlives Kalshi: **leg count is leverage on "
             "execution risk, and it points the wrong way.**\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    prof = profile()
    marg = margins()
    sweep = slippage_sweep()
    lev = leg_leverage(marg)

    print(f"BRACKET ARBITRAGE — {FAMILY}, fresh seeds\n")
    print(f"  fires in {prof['fire_rate'] * 100:.1f}% of sets, "
          f"{prof['losing_fires']} losing fires (riskless => 0)")
    print(f"  {prof['mean_per_set']:+.2f}c per set, sigma {prof['sd_per_set']:.1f}c, "
          f"SNR {prof['snr']:.4f}")
    print(f"  ${prof['annual_dollars']:,.0f}/yr on {prof['sets_per_year']:.0f} sets/yr")
    print(f"  sign the edge in {prof['n_to_sign'] / prof['sets_per_year']:.1f} years\n")
    print(f"  margin when it fires: median {marg[int(0.5 * len(marg))]}c, "
          f"max {marg[-1]}c, across {markets.FAMILIES[FAMILY].n_brackets} legs\n")
    for extra, m, ann, lose, fired in sweep:
        print(f"  +{extra} tick/leg: {m:+.2f}c/set  ${ann:+,.0f}/yr  {lose}/{fired} fires lose")
    print()
    for n_legs, cost, surv in lev:
        print(f"  {n_legs} legs: 1 tick each costs {cost}c -> {surv * 100:.0f}% survive")

    write_report(ROOT / "ARB.md", prof, marg, sweep, lev)
    print(f"\nwrote {ROOT / 'ARB.md'}")


if __name__ == "__main__":
    main()
