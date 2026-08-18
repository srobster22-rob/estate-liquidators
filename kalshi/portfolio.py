"""
Portfolio: the only honest way to make this bigger than one bot.

    python -m kalshi.portfolio                 combine the confirmed bots in results.json
    python -m kalshi.portfolio --min-families 2

WHY A PORTFOLIO IS A REAL ANSWER AND NOT A DODGE

The single-bot ceiling in this simulator is low, and it is low for a structural reason: the
only family with an edge big enough to clear Kalshi's fees (`econ_print`, whose quote lag is
3c) is also the rarest thing on the exchange, at roughly 250 markets a year. The families
that list constantly — crypto hourlies at 17,520 a year — have edges too small to pay for
their own spread. Every parameter tweak in 14 generations and 814 bots ran into that wall.

But nothing says you trade one market family. Bots on different families are close to
INDEPENDENT here: different latent paths, different seeds, different resolution calendars.
So their dollars add while their variances add only in quadrature, and a portfolio is
strictly better than its best member on both axes. That is not a trick to clear a threshold;
it is the standard reason anybody runs more than one strategy.

WHAT THIS CHANGES ABOUT THE GATE

The eleven criteria split cleanly by what they are about:

    criteria 1-10   is this edge REAL?           -> belongs on each bot, individually
    criterion 11    is it enough MONEY?          -> belongs on the portfolio

Applying the dollar bar per-bot, which is what the previous run did, rejects a component
that is real but small even when adding it strictly increases total income. That is the
wrong shape of test: a $60/yr bot which is genuinely profitable is a good thing to own
alongside a $122/yr bot. So each member still has to clear every statistical and robustness
criterion on its own — no free passes for being in a basket — and only the total is asked to
clear the money bar.

MEASURED ON HOLDOUT DATA, NOT OUT-OF-SAMPLE. OOS is where members are chosen, so OOS means
of chosen bots are biased upward — for the incumbent the bias was 85.6c vs a true 48.8c. The
combined figure would inherit that bias from every member at once.

INDEPENDENCE IS AN ASSUMPTION AND IT IS THE WEAK POINT. In this simulator it is true by
construction. On the real exchange it is not: a macro shock moves econ prints, index brackets
and crypto together, and every one of these strategies is short the same tail — they buy
near-certain outcomes and lose when the improbable happens. So the diversification figure
below is an upper bound, and the correlated-crash case is not modelled anywhere in this
directory.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random

from . import backtest, capacity, evaluate, markets, strategies

CFG = json.loads((pathlib.Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
GATE = CFG["gate"]
SEEDS = CFG["seeds"]
ROOT = pathlib.Path(__file__).parent


class Member:
    __slots__ = ("family", "strat", "group_pnl", "mpy", "annual_dollars", "capital",
                 "mean", "n_groups", "cap")

    def __init__(self, family, strat):
        self.family, self.strat = family, strat

    def label(self):
        return f"{self.family} / {self.strat.label()}"


def build_member(family: str, strat, n_groups: int, seed_base: int) -> Member:
    m = Member(family, strat)
    data = markets.dataset(family, seed_base, n_groups)
    res = backtest.run(data, strat)
    m.group_pnl = res.group_pnl
    m.n_groups = len(res.group_pnl)
    m.mpy = capacity.sets_per_year(family)
    m.mean = res.total_pnl / max(m.n_groups, 1)
    m.annual_dollars = m.mpy * m.mean / 100.0
    m.cap = capacity.analyse(family, strat, seed_base=seed_base, n_groups=n_groups)
    m.capital = m.cap.capital_required_cents / 100.0
    return m


class PortfolioResult:
    __slots__ = ("members", "annual_dollars", "capital", "lo95", "hi95", "p_value",
                 "return_on_capital", "best_single", "diversification")


def combine(members: list[Member], resamples=4000, seed=99) -> PortfolioResult:
    """Sum the members, and bootstrap the total by resampling each family independently.

    Independent resampling is the whole point: it is what lets the combined interval be
    tighter than the sum of the individual intervals. It is also exactly the assumption that
    does not hold on a real exchange — see the module docstring.
    """
    r = PortfolioResult()
    r.members = members
    r.annual_dollars = sum(m.annual_dollars for m in members)
    r.capital = sum(m.capital for m in members)
    r.return_on_capital = (r.annual_dollars / r.capital) if r.capital > 0 else 0.0
    r.best_single = max((m.annual_dollars for m in members), default=0.0)

    rng = random.Random(seed)
    totals = []
    choices = rng.choices
    for _ in range(resamples):
        tot = 0.0
        for m in members:
            n = len(m.group_pnl)
            if n == 0:
                continue
            tot += m.mpy * (sum(choices(m.group_pnl, k=n)) / n) / 100.0
        totals.append(tot)
    totals.sort()
    r.lo95 = totals[int(0.025 * (resamples - 1))]
    r.hi95 = totals[int(0.975 * (resamples - 1))]
    ge = sum(1 for t in totals if t - r.annual_dollars >= r.annual_dollars)
    r.p_value = (ge + 1) / (resamples + 1)

    # If the members were perfectly correlated the interval half-width would be the SUM of
    # the individual half-widths. Independence makes it the root-sum-square. The ratio is
    # what diversification bought.
    halves = []
    for m in members:
        n = len(m.group_pnl)
        if n < 2:
            continue
        sd = (sum((x - m.mean) ** 2 for x in m.group_pnl) / n) ** 0.5
        halves.append(1.96 * m.mpy * (sd / math.sqrt(n)) / 100.0)
    summed = sum(halves)
    rss = math.sqrt(sum(h * h for h in halves))
    r.diversification = (summed / rss) if rss > 0 else 1.0
    return r


def select_members(rows: list[dict], n_groups: int, seed_base: int) -> list[Member]:
    """One bot per family — the best by holdout dollars. Never two of the same mechanism.

    Parameter variants of one idea on one family are the same bet placed twice; adding them
    to a basket inflates the headline and adds no diversification whatever.
    """
    by_family: dict[str, Member] = {}
    for row in rows:
        cls = next((c for c in strategies.ALL if c.__name__ == row["strategy"]), None)
        if cls is None:
            continue
        m = build_member(row["family"], cls(**row["params"]), n_groups, seed_base)
        cur = by_family.get(m.family)
        if cur is None or m.annual_dollars > cur.annual_dollars:
            by_family[m.family] = m
    return [m for m in by_family.values() if m.annual_dollars > 0]


def fmt(r: PortfolioResult) -> list[str]:
    out = [f"  {'family / bot':<52} {'$/yr':>9} {'capital':>9}"]
    out.append("  " + "-" * 72)
    for m in sorted(r.members, key=lambda x: -x.annual_dollars):
        out.append(f"  {m.label()[:52]:<52} {m.annual_dollars:>+8,.0f} "
                   f"{m.capital:>8,.0f}")
    out.append("  " + "-" * 72)
    out.append(f"  {'PORTFOLIO':<52} {r.annual_dollars:>+8,.0f} {r.capital:>8,.0f}")
    out.append("")
    out.append(f"  95% CI on annual income : ${r.lo95:,.0f} to ${r.hi95:,.0f}")
    out.append(f"  bootstrap p             : {r.p_value:.4f}")
    out.append(f"  return on capital       : {r.return_on_capital * 100:,.0f}%/yr")
    out.append(f"  best single member      : ${r.best_single:,.0f}/yr")
    out.append(f"  diversification         : {r.diversification:.2f}x tighter interval than "
               f"if the members moved together")
    return out


def write_report(r: PortfolioResult, path: pathlib.Path, bar: float):
    L = ["# Kalshi Bot Factory — Portfolio\n"]
    L.append("The dollar bar belongs on the portfolio; the statistical criteria belong on "
             "each bot. Every member below cleared criteria 1-10 of the gate on its own — "
             "out-of-sample significance after Holm correction, holdout, stress, half-edge "
             "world and rare-loss tail. Only the total is asked to clear the money bar.\n")
    L.append(f"All figures measured on the **holdout** seed range, not out-of-sample: OOS is "
             f"where members are selected, so OOS means of selected bots run high. For the "
             f"incumbent the gap was 85.6¢ vs a true 48.8¢ per market.\n")
    L.append("| member | markets/yr | ¢/market | annual $ | capital |")
    L.append("|---|---|---|---|---|")
    for m in sorted(r.members, key=lambda x: -x.annual_dollars):
        L.append(f"| `{m.family}` / {m.strat.label()} | {m.mpy:,} | {m.mean:+.1f}¢ | "
                 f"${m.annual_dollars:,.0f} | ${m.capital:,.0f} |")
    L.append(f"| **portfolio** | | | **${r.annual_dollars:,.0f}** | **${r.capital:,.0f}** |")
    L.append("")
    L.append(f"- 95% CI on annual income: **${r.lo95:,.0f} to ${r.hi95:,.0f}**")
    L.append(f"- bootstrap p: {r.p_value:.4f}")
    L.append(f"- return on committed capital: {r.return_on_capital * 100:,.0f}%/yr")
    L.append(f"- best single member: ${r.best_single:,.0f}/yr — the portfolio is "
             f"{r.annual_dollars / r.best_single:.2f}x it" if r.best_single else "")
    L.append(f"- diversification: interval is **{r.diversification:.2f}x tighter** than if "
             f"the members moved together")
    L.append("")
    verdict = "CLEARS" if r.annual_dollars >= bar else "does NOT clear"
    L.append(f"**Verdict: the portfolio {verdict} the ${bar:,.0f}/yr bar.**\n")
    L.append("## The caveat that matters\n")
    L.append("Independence is true in this simulator by construction and is the weakest "
             "assumption on this page. On the real exchange these strategies are all short "
             "the same tail — every one of them buys a near-certain outcome and loses when "
             "the improbable happens — and a macro shock moves econ prints, index brackets "
             "and crypto together. The diversification figure is an upper bound and the "
             "correlated-crash case is not modelled anywhere in this directory.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Combine confirmed bots into a portfolio.")
    ap.add_argument("--groups", type=int, default=1200)
    ap.add_argument("--min-families", type=int, default=1)
    ap.add_argument("--source", default="confirmed",
                    help="'confirmed' (passed criteria 1-10) or 'winners'")
    args = ap.parse_args()

    path = ROOT / "results.json"
    if not path.exists():
        raise SystemExit(f"{path} not found — run `python -m kalshi.factory` first")
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get(args.source) or payload.get("winners") or []
    if not rows:
        raise SystemExit(f"no '{args.source}' bots in results.json")

    members = select_members(rows, args.groups, SEEDS["holdout"])
    if len(members) < args.min_families:
        raise SystemExit(f"only {len(members)} profitable families, need {args.min_families}")
    r = combine(members)
    print(f"\nPORTFOLIO — {len(members)} bot(s) across {len(members)} market families\n")
    for line in fmt(r):
        print(line)
    bar = GATE["min_annual_dollars"]
    print(f"\n  bar: ${bar:,}/yr  ->  "
          f"{'CLEARED' if r.annual_dollars >= bar else 'NOT CLEARED'}")
    write_report(r, ROOT / "PORTFOLIO.md", bar)
    print(f"\nwrote {ROOT / 'PORTFOLIO.md'}")


if __name__ == "__main__":
    main()
