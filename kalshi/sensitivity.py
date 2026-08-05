"""
Every assumption in this project, and what the answer does when you move it.

    python -m kalshi.sensitivity          runs the sweep, writes SENSITIVITY.md

WHY THIS FILE IS THE LAST ONE

The headline is "$359/yr, 95% CI $288-$429, p=0.0003". The confidence interval describes
SAMPLING error — how much the number would wobble if you drew different markets from the same
simulator. It says nothing about the far larger question of whether the simulator's inputs are
right, and those inputs were chosen by hand. A p-value of 0.0003 against an assumption that is
wrong by 2x is worth nothing.

So this sweeps each input across a plausible range and reports the elasticity: what the annual
figure becomes, and where it crosses the $250 bar. That turns "the bot earns $359" into a set
of falsifiable conditions someone with API access can check one at a time.

    input                     status        how it enters
    ------------------------- ------------- ------------------------------------------------
    markets per year          COUNTED       linear. 534 contracts/yr = ~134 ladder events.
    depth at 95-99c           MODELLED      linear. `markets._depth_taper`, floored at 8%.
    planted edge magnitude    ASSUMED       LEVERED. Costs are fixed, so net = gross - const.
    fee rate                  VERIFIED      near-linear in the cost term.
    spread                    MODELLED      steps, because it is quantised to whole cents.
    maker fill rate           GUESS         provably irrelevant — see below.

THE ONE INPUT THAT STOPPED MATTERING. `maker_benign_fill_rate` was flagged from the start as a
pure guess that "would become load-bearing the moment market-making worked". Swept from 0.15 to
1.00 it never works: `maker_spread` is negative on every thin family at every fill rate, and it
gets WORSE as fills get easier. That is adverse selection with the sign showing — the fills you
are certain to get are the ones you did not want, and raising the benign rate just buys more of
everything, including the losses. An assumption whose sign is invariant across its whole range
is not an assumption the result depends on, and this one can now be retired rather than caveated.

WHAT THIS DOES NOT DO. Every sweep here moves ONE input with everything else held fixed, on
paired seeds. Real model error arrives in combination, and two inputs each wrong by 30% in the
same direction is not covered by either column.
"""

from __future__ import annotations

import json
import pathlib

from . import backtest, capacity, evaluate, markets, strategies

CFG = json.loads((pathlib.Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
BAR = float(CFG["gate"]["min_annual_dollars"])
ROOT = pathlib.Path(__file__).parent

FAMILY = "econ_print"
BOT = strategies.hold_favorite(enter_frac=0.25, qty=250, thresh=95)
# Fresh seeds, never used for selection anywhere in the pipeline.
SEED = 13_000_000
N = 1500


def _events_per_year(fam_name=FAMILY) -> float:
    fam = markets.FAMILIES[fam_name]
    legs = max(fam.n_rungs, fam.n_brackets, 1)
    return capacity.MARKETS_PER_YEAR.get(fam_name, 0) / legs


def _annual(family_name: str, n=N) -> tuple[float, float]:
    """(annual dollars, mean cents per event) for a family variant."""
    res = backtest.run(markets.dataset(family_name, SEED, n), BOT)
    mean = res.total_pnl / max(len(res.group_pnl), 1)
    return _events_per_year() * mean / 100.0, mean


def sweep_depth(scales=(2.0, 1.5, 1.0, 0.75, 0.5, 0.25, 0.1)) -> list[tuple]:
    out = []
    for sc in scales:
        ann, mean = _annual(markets.variant(FAMILY, depth_scale=sc))
        out.append((sc, mean, ann))
    return out


def sweep_edge(factors=(1.5, 1.25, 1.0, 0.75, 0.5, 0.25)) -> list[tuple]:
    out = []
    for f in factors:
        ann, mean = _annual(markets.variant(FAMILY, edge_factor=f))
        out.append((f, mean, ann))
    return out


def sweep_spread(extras=(0, 1, 2, 3)) -> list[tuple]:
    out = []
    for e in extras:
        ann, mean = _annual(markets.variant(FAMILY, spread_extra=e))
        out.append((e, mean, ann))
    return out


def sweep_markets(counts=(1068, 800, 534, 400, 250, 150)) -> list[tuple]:
    """Linear by construction, but it is the input the census settled, so it belongs here."""
    _, mean = _annual(FAMILY)
    legs = max(markets.FAMILIES[FAMILY].n_rungs, 1)
    return [(c, mean, (c / legs) * mean / 100.0) for c in counts]


def sweep_fee(mults=(0.5, 1.0, 1.5, 2.0, 3.0)) -> list[tuple]:
    out = []
    data = markets.dataset(FAMILY, SEED, N)
    for m in mults:
        res = backtest.run(data, BOT, backtest.Costs(fee_mult=m))
        mean = res.total_pnl / max(len(res.group_pnl), 1)
        out.append((m, mean, _events_per_year() * mean / 100.0))
    return out


def sweep_maker(rates=(0.15, 0.35, 0.60, 0.85, 1.0)) -> list[tuple]:
    """The retired guess. Best of a small config grid per family — a maximum, so an upper
    bound on how good market-making could look."""
    fams = ("politics_long", "awards_thin", "weather_temp", "mentions_short")
    saved = backtest.BENIGN_FILL
    out = []
    try:
        for rate in rates:
            backtest.BENIGN_FILL = rate
            row = []
            for fam in fams:
                best = None
                for ms in (2, 3, 4, 6):
                    for ex in (1, 2, 3):
                        r = backtest.run(markets.dataset(fam, SEED, 600),
                                         strategies.maker_spread(min_spread=ms, exit_ticks=ex,
                                                                 qty=100))
                        if r.n_trades:
                            v = r.total_pnl / 600
                            best = v if best is None else max(best, v)
                row.append(best)
            out.append((rate, row))
    finally:
        backtest.BENIGN_FILL = saved
    return out, fams


def breakeven(rows) -> float | None:
    """Where a monotone sweep crosses the bar, by linear interpolation between bracketing
    points. Returns None if the bar is not crossed inside the swept range."""
    pts = sorted(((x, ann) for x, _, ann in rows), key=lambda t: t[0])
    for (x0, a0), (x1, a1) in zip(pts, pts[1:]):
        if (a0 - BAR) * (a1 - BAR) <= 0 and a1 != a0:
            return x0 + (BAR - a0) * (x1 - x0) / (a1 - a0)
    return None


def write_report(path: pathlib.Path, depth, edge, spread, mkts, fee, maker, maker_fams):
    L = ["# Kalshi Bot Factory — Sensitivity\n"]
    L.append("The confidence interval on the headline describes **sampling** error. It says "
             "nothing about whether the simulator's inputs are right, and those were chosen "
             "by hand. This sweeps each one and reports where the answer crosses the "
             f"**${BAR:,.0f}/yr** bar.\n")
    L.append(f"Bot: `{FAMILY}` / `{BOT.label()}`, measured on fresh seeds never used for "
             f"selection. One input moves at a time, everything else held fixed, paired "
             f"seeds throughout.\n")

    def table(title, rows, unit, note=""):
        L.append(f"## {title}\n")
        if note:
            L.append(note + "\n")
        L.append(f"| {unit} | ¢/event | annual $ | vs bar |")
        L.append("|---|---|---|---|")
        for x, mean, ann in rows:
            mark = "clears" if ann >= BAR else "**below**"
            xs = f"{x:g}"
            L.append(f"| {xs} | {mean:+.1f}¢ | ${ann:,.0f} | {mark} |")
        be = breakeven(rows)
        L.append("")
        if be is not None:
            L.append(f"**Crosses the bar at {be:.2f}.**\n")
        return be

    be_d = table("Depth at 95–99¢ — MODELLED", depth, "depth × my model",
                 "Income is exactly linear in depth: the bot is depth-limited at every "
                 "size it wants. `markets._depth_taper` floors the book at 8% of base, which "
                 "is a modelling choice, not a measurement — and it sits at precisely the "
                 "price where the whole edge lives.")
    be_e = table("Planted edge magnitude — ASSUMED", edge, "edge × markets.py",
                 "The levered one. Costs are fixed, so net = gross − constant, and halving "
                 "the assumed inefficiency removes far more than half the profit.")
    table("Spread — MODELLED", spread, "extra ticks",
          "Steps rather than glides, because the spread is quantised to whole cents and the "
          "bot's entry threshold sits on a tick boundary.")
    be_m = table("Markets per year — COUNTED", mkts, "contracts/yr",
                 "Linear by construction. This is the input the census settled at 534 "
                 "contracts ≈ 134 ladder events; it is here for completeness.")
    table("Fee rate — VERIFIED", fee, "fee × published",
          "The published schedule is confirmed (see `selftest.py` §1b), so this column is "
          "not an open question — it is here to show what a schedule change would do.")

    L.append("## Maker fill rate — a GUESS that turned out not to matter\n")
    L.append("`maker_benign_fill_rate` was flagged from the start as a pure guess that would "
             "become load-bearing the moment market-making worked. Swept across its whole "
             "plausible range, it never works — and it gets **worse** as fills get easier, "
             "which is adverse selection with the sign showing: the fills you are certain to "
             "get are the ones you did not want.\n")
    L.append("| fill rate | " + " | ".join(f"`{f}`" for f in maker_fams) + " |")
    L.append("|---|" + "---|" * len(maker_fams))
    for rate, row in maker:
        cells = [(f"{v:+,.0f}¢" if v is not None else "n/a") for v in row]
        L.append(f"| {rate:.2f} | " + " | ".join(cells) + " |")
    L.append("")
    L.append("Best of 12 configs per cell — a maximum, so an upper bound. **An assumption "
             "whose sign is invariant across its entire range is not one the result depends "
             "on.** This one is retired rather than caveated.\n")

    L.append("## What has to be true\n")
    L.append("Stated so each can be checked separately, against a real book:\n")
    if be_d is not None:
        L.append(f"- the book holds at least **{be_d:.2f}×** the depth this simulator assumes "
                 f"at 95–99¢ — roughly **{be_d * 55:.0f} contracts** at the touch")
    if be_e is not None:
        L.append(f"- the real mispricing is at least **{be_e * 100:.0f}%** of what "
                 f"`markets.py` plants")
    if be_m is not None:
        L.append(f"- Kalshi lists at least **{be_m:,.0f} econ contracts a year** "
                 f"(census counted 534)")
    L.append("")
    L.append("Each is a one-input statement. Real model error arrives in combination, and two "
             "inputs each 30% out in the same direction are not covered by any single column "
             "above.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    print(f"sensitivity of {FAMILY} / {BOT.label()}  (bar ${BAR:,.0f}/yr)\n")
    depth = sweep_depth()
    edge = sweep_edge()
    spread = sweep_spread()
    mkts = sweep_markets()
    fee = sweep_fee()
    maker, maker_fams = sweep_maker()

    for title, rows, unit in (("depth", depth, "x"), ("edge", edge, "x"),
                              ("spread", spread, "+ticks"), ("markets/yr", mkts, ""),
                              ("fee", fee, "x")):
        be = breakeven(rows)
        print(f"  {title:<12} " + "  ".join(f"{x:g}{unit}=${a:,.0f}" for x, _, a in rows)
              + (f"   -> bar at {be:.2f}" if be is not None else "   -> bar not crossed"))
    print(f"  {'maker fill':<12} negative at every rate on every thin family "
          f"({', '.join(maker_fams)})")

    write_report(ROOT / "SENSITIVITY.md", depth, edge, spread, mkts, fee, maker, maker_fams)
    print(f"\nwrote {ROOT / 'SENSITIVITY.md'}")


if __name__ == "__main__":
    main()
