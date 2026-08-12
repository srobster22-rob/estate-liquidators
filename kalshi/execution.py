"""
How an N-leg arbitrage is actually executed, and what a missed leg really costs.

    python -m kalshi.execution        runs the analysis, writes EXECUTION.md

THE ASSUMPTION NOBODY CHECKED

Every bracket number in this project is quoted at some number of "ticks of slippage per leg",
and K22 built its whole conclusion on that axis: one tick per leg turns 0/118 losing fires into
105/118. That models a MARKETABLE order — one that crosses and walks the book until it fills.

No sane implementation of this strategy would send one. You would send a LIMIT order at the
quoted ask, immediate-or-cancel. Then you never pay worse than the price you computed the arb
from, because that is what a limit price is for. The risk moves somewhere else entirely:

    marketable order  ->  you always fill, sometimes at a worse price   (slippage)
    IOC limit order   ->  you never fill worse, sometimes you miss      (partial fill)

For a one-leg strategy these are nearly interchangeable. For an N-leg arb they are not, and
that is the point of this module. A miss does not cost you a tick — it leaves you holding k of
N mutually exclusive brackets, which is a directional position you did not choose. K22 wrote
exactly that sentence and then moved on without pricing it, and the sentence has been load
bearing ever since.

WHAT PRICING IT SHOWS

A partial bracket is not the disaster the phrase implies, and the reason is worth stating
before the numbers. If you hold k of N brackets bought at their asks for a total of C cents,
the payout is 100c when the winner is among your k and 0 otherwise, so

    E[payout] = 100 * sum(true_p over the k legs you got)

and the legs were quoted near their true probabilities. So the expected loss on a partial fill
is roughly the SPREAD AND FEES on the legs you got — not the position. What actually determines
whether IOC beats marketable is therefore a comparison between two small numbers, not between
a small one and a catastrophe, and it has to be measured rather than argued.

`backtest.Costs(leg_fill_rate=f)` implements the IOC side: each leg fills at the quoted ask
with probability f, and a leg that misses simply never opens. Partial positions then settle
through the engine's existing logic with no special case, which is deliberate — a bespoke
settlement path for partial arbs is exactly where a favourable bug would hide.

K27 — HOW THE MISSES ARE DISTRIBUTED, WHICH IS THE PART I GOT WRONG

K26 closed by naming its own gap: "fills here are independent per leg; a fast move takes several
books at once, so real misses are correlated, and correlated misses are worse than independent
ones at the same marginal rate." The first half is a fair caveat. The second half is a guess,
it was never measured, and it is BACKWARDS.

Correlation across the legs of ONE set is not portfolio correlation. It means the set fills
entirely or not at all — so there are no partial brackets and the riskless property survives
intact. And an all-or-nothing miss is RETRYABLE: nothing was committed, so the batch can be
re-sent against the next quote, while a partial fill leaves you already in. Both effects point
the same way, and at full correlation IOC execution is indistinguishable from perfect fill.

The real hazard is a third mechanism K26 never named, and it is a change of SIGN rather than of
magnitude. ADVERSE SELECTION: the quote carrying the mispricing is the one whose maker pulls it
first, so you systematically collect the fairly-priced legs and miss the cheap one. That does
not add variance to an edge, it removes the edge. `adverse_fill=True` models it by aiming the
misses at the most underpriced unfilled legs.

Its bite is sharply non-linear in the fill rate, which is the operationally useful part — see
`adverse_sweep`.
"""

from __future__ import annotations

import json
import pathlib
import statistics

from . import arb, backtest, markets, strategies

ROOT = pathlib.Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

FAMILY = "crypto_bracket_stale"
SEEDS = (51_000_000, 53_000_000, 55_000_000, 57_000_000)   # fresh, never used for selection
N = 3000
MIN_EDGE = 8               # K24's filter, the one that made the strategy work at all
QTY = 250
Z2 = 1.96 ** 2


def measure(costs, family=FAMILY, n=N, seeds=SEEDS) -> dict:
    """One execution mode, measured across independent seeds WITH a standard error.

    The standard error is not decoration. The first version of this module ran one seed and
    reported that income RISES as fills get worse — 25.4c/set at perfect fill against 28.3c
    at an 80% fill rate — which read as a discovery and was entirely noise: the strategy
    fires ~80 times in 3,000 sets, so the mean's SE is 1.5-3.3c and every row was within
    about one of every other. Reporting a monotone story off that would have been the exact
    error K5 and K8 exist to prevent, one round after congratulating myself for catching it.
    """
    means, sds, worsts, losing, total = [], [], [], 0, 0
    fires = 0
    for seed in seeds:
        res = backtest.run(markets.dataset(family, seed, n), costs=costs,
                           strat=strategies.bracket_arb(min_edge=MIN_EDGE, qty=QTY))
        g = res.group_pnl
        means.append(statistics.fmean(g))
        sds.append(statistics.pstdev(g))
        worsts.append(min(g))
        losing += sum(1 for x in g if x < 0)
        fires += sum(1 for x in g if x != 0)
        total += len(g)
    spy = arb.sets_per_year(family)
    e = statistics.fmean(means)
    s = statistics.fmean(sds)
    se = statistics.pstdev(means) / (len(means) ** 0.5) if len(means) > 1 else float("nan")
    return {
        "label": costs.label, "per_set": e, "se": se, "sd": s,
        "annual": spy * e / 100.0,
        "info_cost": s * s / e if e > 0 else float("inf"),
        "fires": fires, "losing": losing, "n": total,
        "worst": min(worsts),
    }


def modes() -> list[dict]:
    """The comparison the module exists for, on one basis."""
    return [measure(c) for c in (
        backtest.Costs(label="perfect fill (unachievable)"),
        backtest.Costs(extra_spread=1, label="marketable, +1 tick/leg"),
        backtest.Costs(extra_spread=2, label="marketable, +2 ticks/leg"),
        backtest.Costs(leg_fill_rate=0.95, label="IOC limit, 95% per leg"),
        backtest.Costs(leg_fill_rate=0.80, label="IOC limit, 80% per leg"),
        backtest.Costs(leg_fill_rate=0.60, label="IOC limit, 60% per leg"),
    )]


def flat_in_fill_rate(rows: list[dict]) -> bool:
    """Is the IOC mean actually falling with the fill rate, or is that noise?

    Returns True when every IOC row sits within 2 SE of the best one — i.e. when the honest
    answer is "the expected value is flat and the story is entirely in the variance".
    """
    ioc = [r for r in rows if "IOC" in r["label"]]
    if len(ioc) < 2:
        return False
    top = max(r["per_set"] for r in ioc)
    return all(r["per_set"] + 2 * r["se"] >= top for r in ioc)


def miss_regimes(rate=0.80) -> list[dict]:
    """The three-way comparison K26's caveat needed and did not run.

    Same marginal per-leg fill rate throughout; only the JOINT distribution of misses moves.
    """
    return [
        measure(backtest.Costs(label="perfect fill (unachievable)")),
        measure(backtest.Costs(leg_fill_rate=rate,
                               label=f"IOC {rate:.0%}, independent misses")),
        measure(backtest.Costs(leg_fill_rate=rate, fill_correlation=0.5,
                               label=f"IOC {rate:.0%}, half correlated")),
        measure(backtest.Costs(leg_fill_rate=rate, fill_correlation=1.0,
                               label=f"IOC {rate:.0%}, fully correlated")),
        measure(backtest.Costs(leg_fill_rate=rate, adverse_fill=True,
                               label=f"IOC {rate:.0%}, ADVERSE")),
    ]


def realised_fill_rate(rate=0.80, family=FAMILY, n=4000) -> list[tuple]:
    """Legs actually filled, as a share of the perfect-fill run, per regime.

    Full correlation lands ABOVE its nominal rate and that is not a leak — it is the second
    reason correlation helps. When the whole batch misses, nothing is committed, so the
    strategy re-fires against the next quote and often gets in. A PARTIAL fill cannot be
    retried: the position guard has already been tripped by the legs that did fill.
    """
    st = strategies.bracket_arb(min_edge=MIN_EDGE, qty=QTY)
    data = markets.dataset(family, SEEDS[0], n)
    base = backtest.run(data, st, backtest.Costs()).n_trades
    out = []
    for label, c in (("independent", backtest.Costs(leg_fill_rate=rate)),
                     ("adverse", backtest.Costs(leg_fill_rate=rate, adverse_fill=True)),
                     ("fully correlated",
                      backtest.Costs(leg_fill_rate=rate, fill_correlation=1.0))):
        got = backtest.run(data, st, c).n_trades
        out.append((label, got / base if base else 0.0))
    return out


def adverse_sweep(rates=(0.95, 0.90, 0.80), seeds=None, n=N) -> list[dict]:
    """Where adverse selection actually bites, with a t-statistic on every row.

    Ten seeds rather than four, because the four-seed version put the 90% row at t=-1.5 and
    that is not enough to claim a cliff. The claim being made — harmless at 95%, fatal by 80%
    — is a claim about WHERE the transition is, so the rows either side of it have to be
    separated by more than their own noise.
    """
    seeds = seeds or tuple(51_000_000 + 2_000_000 * i for i in range(10))
    st = strategies.bracket_arb(min_edge=MIN_EDGE, qty=QTY)
    out = []
    for r in rates:
        arm = []
        for adv in (False, True):
            ms = [statistics.fmean(backtest.run(
                markets.dataset(FAMILY, s, n), st,
                backtest.Costs(leg_fill_rate=r, adverse_fill=adv)).group_pnl) for s in seeds]
            arm.append((statistics.fmean(ms), statistics.pstdev(ms) / len(ms) ** 0.5))
        d = arm[1][0] - arm[0][0]
        se = (arm[0][1] ** 2 + arm[1][1] ** 2) ** 0.5
        out.append({"rate": r, "indep": arm[0][0], "indep_se": arm[0][1],
                    "adverse": arm[1][0], "adverse_se": arm[1][1],
                    "delta": d, "t": d / se if se else 0.0})
    return out


def partial_anatomy(rows: list[dict]) -> dict:
    """What a partial fill costs, decomposed against what it does to the risk."""
    full = next(r for r in rows if "perfect" in r["label"])
    worst = max((r for r in rows if "IOC" in r["label"]), key=lambda r: r["sd"])
    return {
        "full": full, "worst": worst,
        "sd_ratio": worst["sd"] / full["sd"] if full["sd"] else float("nan"),
        "income_ratio": worst["per_set"] / full["per_set"] if full["per_set"] else float("nan"),
    }


def write_report(path: pathlib.Path, rows: list[dict], anat: dict, flat: bool,
                 regimes=None, sweep=None, realised=None) -> None:
    L = ["# Kalshi Bot Factory — Execution\n"]
    L.append("Every bracket number in this project is quoted at some number of **ticks of "
             "slippage per leg**, and K22's conclusion rests on that axis. That models a "
             "*marketable* order — one that crosses and walks the book.\n")
    L.append("No sane implementation would send one. You would send a **limit order at the "
             "quoted ask**, immediate-or-cancel, and then you never pay worse than the price "
             "you computed the arb from. The risk moves somewhere else:\n")
    L.append("| order type | you always | you sometimes |")
    L.append("|---|---|---|")
    L.append("| marketable | fill | pay worse — **slippage** |")
    L.append("| IOC limit | pay your price | **miss** — partial fill |")
    L.append("")
    L.append("For a one-leg strategy these are nearly interchangeable. For an N-leg arb they "
             "are not: a miss does not cost a tick, it leaves you holding *k* of *N* mutually "
             "exclusive brackets. K22 wrote that sentence and moved on without pricing it.\n")

    L.append("## Every mode on one basis\n")
    L.append(f"Four independent seeds, {N:,} sets each. `I = s²/e` is K23's "
             "frequency-invariant information cost — lower is better.\n")
    L.append("| execution | ¢/set | SE | σ | **I = s²/e** | losing sets | worst set |")
    L.append("|---|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['label']} | {r['per_set']:+.2f}¢ | ±{r['se']:.2f} | {r['sd']:,.0f}¢ | "
                 f"**{r['info_cost']:,.0f}** | {r['losing']}/{r['n']:,} | "
                 f"{r['worst']:+,.0f}¢ |")
    L.append("")

    L.append("## The result, and the one I nearly reported instead\n")
    L.append("The first version of this ran **one seed** and found income *rising* as fills "
             "got worse — +25.4¢/set at perfect fill against +28.3¢ at an 80% fill rate. That "
             "read as a discovery. It was noise: the strategy fires ~80 times in 3,000 sets, "
             "so the mean carries an SE of 1.5–3.3¢ and every row sat within about one of "
             "every other. Reporting the trend would have been exactly the error findings 5 "
             "and 8 exist to catch, one round after congratulating myself for catching it.\n")
    if flat:
        L.append("Measured across four seeds, **the expected value is flat in the fill rate** "
                 "— every IOC row is within 2 SE of the best. The entire story is in the "
                 "second moment.\n")
    L.append(f"- **σ rises {anat['sd_ratio']:.1f}×** across the IOC range while income holds "
             f"at {anat['income_ratio'] * 100:.0f}% of perfect fill.")
    L.append(f"- **Losing sets go from 0 to {anat['worst']['losing']}**, worst case "
             f"{anat['worst']['worst']:+,.0f}¢ on a single set.")
    L.append(f"- **Information cost rises from {anat['full']['info_cost']:,.0f} to "
             f"{anat['worst']['info_cost']:,.0f}** — an order of magnitude.\n")

    L.append("### Why the mean survives\n")
    L.append("A set only fires when it is underpriced by at least the filter, and a set that "
             "is collectively underpriced is on average made of individually underpriced "
             "legs. So a partial fill is a **positive-EV directional position**, not a loss. "
             "K22's phrase — *\"you are holding a directional position you never chose\"* — "
             "is right about the mechanism and wrong about the consequence. The money is "
             "fine. What you lose is *the reason you wanted the trade*.\n")

    L.append("## Which is what settles it\n")
    mk1 = next(r for r in rows if "+1 tick" in r["label"])
    ioc95 = next(r for r in rows if "95%" in r["label"])
    L.append("| | income | I = s²/e | riskless? |")
    L.append("|---|---|---|---|")
    L.append(f"| marketable, +1 tick | {mk1['per_set']:+.2f}¢ | **{mk1['info_cost']:,.0f}** | "
             f"**yes** — {mk1['losing']}/{mk1['n']:,} losing |")
    L.append(f"| IOC limit, 95% | {ioc95['per_set']:+.2f}¢ | {ioc95['info_cost']:,.0f} | "
             f"no — {ioc95['losing']}/{ioc95['n']:,} losing |")
    L.append("")
    L.append("**Marketable execution has the lowest information cost of any mode measured, "
             "including perfect fill.** Slippage shrinks the mean and the spread by almost "
             "the same proportion, and `I` is linear in a proportional shrink — so you buy a "
             "better risk profile at a fair price. IOC keeps the money and throws the risk "
             "profile away.\n")
    L.append("So finding 17 modelled the right execution mode for the wrong reason, and the "
             "conclusion sharpens rather than reverses: **at a 95% per-leg fill rate this is "
             "no longer an arbitrage at all.** Its information cost is worse than `snr_band`, "
             "the plain directional strategy it was supposed to beat. A riskless trade you "
             "cannot execute risklessly is a directional trade with extra steps.\n")

    if regimes and sweep and realised:
        L.append("## K27 — how the misses are distributed, which is the part I got wrong\n")
        L.append("K26 closed by naming its own gap: *\"real misses are correlated, and "
                 "correlated misses are worse than independent ones at the same marginal "
                 "rate.\"* The caveat was fair; the direction was a guess, and it is "
                 "**backwards**.\n")
        L.append("Correlation across the legs of *one set* is not portfolio correlation. It "
                 "means the set fills **entirely or not at all** — no partial brackets, so "
                 "the riskless property survives. Same marginal fill rate in every row below; "
                 "only the joint distribution moves.\n")
        L.append("| regime | ¢/set | SE | σ | **I = s²/e** | losing sets | worst set |")
        L.append("|---|---|---|---|---|---|---|")
        for r in regimes:
            ic = "—" if r["info_cost"] == float("inf") else f"{r['info_cost']:,.0f}"
            L.append(f"| {r['label']} | {r['per_set']:+.2f}¢ | ±{r['se']:.2f} | "
                     f"{r['sd']:,.0f}¢ | **{ic}** | {r['losing']}/{r['n']:,} | "
                     f"{r['worst']:+,.0f}¢ |")
        L.append("")
        L.append("**At full correlation IOC is indistinguishable from perfect fill** — same "
                 "σ, same zero losing sets, same information cost. And there is a second "
                 "reason correlation helps that shows up in the realised fill rate:\n")
        L.append("| regime | legs filled, vs perfect fill |")
        L.append("|---|---|")
        for label, share in realised:
            L.append(f"| {label} | {share:.1%} |")
        L.append("")
        L.append("Full correlation lands *above* its nominal rate. That is not a leak — **an "
                 "all-or-nothing miss is retryable.** Nothing was committed, so the batch "
                 "re-fires against the next quote. A partial fill cannot be retried: the "
                 "legs that did fill have already tripped the position guard.\n")

        L.append("### The hazard is a third mechanism, and it changes the sign\n")
        L.append("**Adverse selection.** The quote carrying the mispricing is the one whose "
                 "maker pulls it first, so you systematically collect the fairly-priced legs "
                 "and miss the cheap one. That does not add variance to an edge — it removes "
                 "the edge. Ten seeds × 3,000 sets:\n")
        L.append("| per-leg fill | independent | adverse | delta | t |")
        L.append("|---|---|---|---|---|")
        for r in sweep:
            L.append(f"| {r['rate']:.0%} | {r['indep']:+.2f} ±{r['indep_se']:.2f}¢ | "
                     f"{r['adverse']:+.2f} ±{r['adverse_se']:.2f}¢ | {r['delta']:+.2f}¢ | "
                     f"**{r['t']:+.1f}** |")
        L.append("")
        L.append("**Sharply non-linear, and that is the operationally useful part.** At a 95% "
                 "per-leg fill rate adverse selection is undetectable (t = "
                 f"{sweep[0]['t']:+.1f}). By 80% it takes the strategy **negative**. The "
                 "transition sits between 95% and 90%, which turns the whole question into "
                 "one number an operator can measure from their own fill logs — the same move "
                 "`COHERENCE.md` makes for the staleness rate.\n")

    L.append("## What this does not settle\n")
    L.append("- Adverse selection is modelled as **perfectly informed**: misses land on the "
             "most underpriced legs, always. Reality sits somewhere between that and random, "
             "and nothing here locates it.")
    L.append("- The gate's **stress** criterion still applies 2 ticks *and* 1.5× fees. Two "
             "ticks is a marketable-order assumption an IOC limit does not face, so the "
             "right stress for this strategy is a fill-rate stress — but inventing one now, "
             "after seeing which way it falls, is how a gate gets quietly loosened. It is "
             "left alone.")
    L.append("- `crypto_bracket_stale` remains a simulated family whose staleness rate was "
             "invented. `COHERENCE.md` is the branch that would settle it from real books.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    spy = arb.sets_per_year(FAMILY)
    print(f"EXECUTION — {FAMILY}, bracket_arb(min_edge={MIN_EDGE}), {spy:,.0f} sets/yr")
    print(f"{len(SEEDS)} seeds x {N:,} sets. I = s^2/e, K23's information cost.\n")
    rows = modes()
    print(f"  {'execution':<30} {'c/set':>9} {'SE':>6} {'sd':>7} {'I':>9} "
          f"{'losing':>11} {'worst':>10}")
    print("  " + "-" * 88)
    for r in rows:
        print(f"  {r['label']:<30} {r['per_set']:>+9.2f} {r['se']:>6.2f} {r['sd']:>7,.0f} "
              f"{r['info_cost']:>9,.0f} {r['losing']:>5}/{r['n']:<5,} {r['worst']:>+10,.0f}")

    flat = flat_in_fill_rate(rows)
    anat = partial_anatomy(rows)
    print(f"\n  expected value is {'FLAT' if flat else 'NOT flat'} in the fill rate "
          f"(every IOC row within 2 SE of the best)")
    print(f"  sigma rises {anat['sd_ratio']:.1f}x while income holds at "
          f"{anat['income_ratio'] * 100:.0f}% of perfect fill")
    print(f"  losing sets 0 -> {anat['worst']['losing']}, info cost "
          f"{anat['full']['info_cost']:,.0f} -> {anat['worst']['info_cost']:,.0f}")

    mk1 = next(r for r in rows if "+1 tick" in r["label"])
    i95 = next(r for r in rows if "95%" in r["label"])
    print(f"\n  marketable +1 tick has the LOWEST I of any mode ({mk1['info_cost']:,.0f}), "
          f"including perfect fill")
    print(f"  at a 95% per-leg fill rate this is no longer an arbitrage: I="
          f"{i95['info_cost']:,.0f}, worse than snr_band's ~1,300-3,000")

    print("\n  K27 — HOW THE MISSES ARE DISTRIBUTED (same marginal rate, different joint)")
    regimes = miss_regimes()
    for r in regimes:
        ic = "  neg" if r["info_cost"] == float("inf") else f"{r['info_cost']:>7,.0f}"
        print(f"    {r['label']:<34} {r['per_set']:>+8.2f} sd {r['sd']:>4,.0f} I={ic} "
              f"{r['losing']:>4}/{r['n']:<6,} losing")

    realised = realised_fill_rate()
    print("\n  realised legs filled vs perfect fill (an all-or-nothing miss is RETRYABLE):")
    for label, share in realised:
        print(f"    {label:<20} {share:.1%}")

    sweep = adverse_sweep()
    print("\n  where adverse selection bites (10 seeds):")
    print(f"    {'fill':>5} {'independent':>16} {'adverse':>16} {'delta':>9} {'t':>6}")
    for r in sweep:
        print(f"    {r['rate']:>5.0%} {r['indep']:>+11.2f}+-{r['indep_se']:<4.2f} "
              f"{r['adverse']:>+11.2f}+-{r['adverse_se']:<4.2f} {r['delta']:>+9.2f} "
              f"{r['t']:>6.1f}")

    write_report(ROOT / "EXECUTION.md", rows, anat, flat, regimes, sweep, realised)
    print(f"\nwrote {ROOT / 'EXECUTION.md'}")


if __name__ == "__main__":
    main()
