"""
Capacity: turning a percentage into dollars per year.

    python -m kalshi.capacity                 analyse the winners in results.json
    python -m kalshi.capacity --all           analyse every bot that reached out-of-sample
    python -m kalshi.capacity --bot 'econ_print/hold_favorite(thresh=95,qty=250)'

WHY THIS FILE EXISTS

`RESULTS.md` reports the winning bot at **+4552% per year on locked capital**, and that
figure is arithmetically correct and close to meaningless. It is a *simple return on capital
while capital happens to be deployed*, and it says nothing about the two questions that
decide whether a strategy is worth building:

    1. How many markets like this does the exchange actually list per year?
    2. How much size does the book hold at the price where the edge lives?

A strategy earning 85c per market on a family that prints 250 markets a year, filling ~40
contracts at a time because the book is thin there, is a **$200/year business**. The 4552%
is real; it describes capital that sits idle 93% of the time. Both statements are true and
only one of them is useful.

WHAT THIS COMPUTES

  markets/yr        an ESTIMATE from config.json, not a measurement (see caveats below)
  annual P&L        markets/yr x mean cents per market offered
  mean concurrent   how many positions are open at once on average, from Little's law:
                    arrival rate x mean holding time
  capital required  peak concurrent positions (Poisson, mean + 3 sigma) x cost each.
                    This is the capital you have to COMMIT, not the average you use.
  return on capital annual P&L / capital required. The honest ROI, and it is much smaller
                    than the headline because the denominator includes the idle time.
  utilisation       fraction of the year the capital is actually working

THE CAVEATS, all of which bite:

  * `markets_per_year` is an estimate from general knowledge of what Kalshi lists. It was
    not scraped and not verified. It scales the dollar figure linearly, so a 2x error here
    is a 2x error in the headline.
  * Fill sizes come from the simulator's depth model, including the taper at extreme prices
    which is itself a modelling choice (`markets._depth_taper`).
  * No competition. If an edge this simple existed at this size, the capacity is what other
    people would be taking too, and the first thing that happens to a thin structural edge
    is that somebody else's bot is already resting there.
  * Everything is gross of infrastructure, data, taxes, and the cost of your own time.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib

from . import backtest, evaluate, markets, strategies

CFG = json.loads((pathlib.Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
CAP = CFG["capacity"]
GATE_MIN_DOLLARS = CFG["gate"]["min_annual_dollars"]
SEEDS = CFG["seeds"]
MARKETS_PER_YEAR = CAP["markets_per_year"]
PEAK_SIGMA = float(CAP["peak_sigma"])
HOURS_PER_YEAR = 24 * 365
ROOT = pathlib.Path(__file__).parent


class Capacity:
    __slots__ = ("family", "label", "markets_per_year", "traded_fraction", "mean_per_market",
                 "annual_pnl_cents", "mean_cost_per_position", "mean_hold_hours",
                 "mean_concurrent", "peak_concurrent", "capital_required_cents",
                 "return_on_capital", "utilization", "mean_contracts", "annual_contracts",
                 "breakeven_markets_per_year")

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}


def analyse(family: str, strat, seed_base=None, n_groups=1200) -> Capacity:
    """Run the bot, then ask what a year of it looks like in dollars.

    DEFAULTS TO THE HOLDOUT SET, NOT OUT-OF-SAMPLE, AND THAT IS A BUG FIX. The first version
    of this file used the OOS seeds, and OOS is where winners are *chosen* — a bot only
    becomes a winner if its OOS numbers clear the gate, so the OOS mean of a winner is the
    maximum of a selected set and is biased upward. It reported the best bot at 85.6c per
    market and therefore $214/yr. Its holdout figure was 53.3c and a fourth, never-touched
    seed range gives 48.8c: the honest number is about $122/yr, and the headline was 75% too
    high. Capacity is exactly the number people quote, so it has to come from data that had
    no hand in picking the bot.
    """
    seed_base = SEEDS["holdout"] if seed_base is None else seed_base
    data = markets.dataset(family, seed_base, n_groups)
    res = backtest.run(data, strat)
    fam = markets.FAMILIES[family]

    c = Capacity()
    c.family = family
    c.label = strat.label()
    c.markets_per_year = MARKETS_PER_YEAR.get(family, 0)
    c.mean_per_market = res.total_pnl / max(res.n_groups, 1)
    c.annual_pnl_cents = c.markets_per_year * c.mean_per_market

    # A "position" here is one trade. Cost basis and holding time come straight from the
    # engine's capital accounting rather than being assumed.
    c.mean_contracts = res.n_contracts / max(res.n_trades, 1)
    c.annual_contracts = c.mean_contracts * (res.n_trades / max(res.n_groups, 1)) * c.markets_per_year
    c.traded_fraction = min(1.0, res.n_trades / max(res.n_groups, 1))

    # Measured by the engine, not inferred. An earlier version split capital-cent-hours into
    # cost x duration using the largest position ever opened as the scale, which overstated
    # cost and understated holding time — the product is invariant so the mean capital came
    # out right, but the Poisson peak buffer scales as sqrt(cost) and came out too large.
    if res.n_closed > 0:
        c.mean_cost_per_position = res.cost_sum / res.n_closed
        c.mean_hold_hours = min(fam.life_hours, res.hold_hours_sum / res.n_closed)
    else:
        c.mean_hold_hours = 0.0
        c.mean_cost_per_position = 0.0

    # Little's law: mean number in system = arrival rate x time in system.
    trades_per_year = (res.n_trades / max(res.n_groups, 1)) * c.markets_per_year
    c.mean_concurrent = trades_per_year * c.mean_hold_hours / HOURS_PER_YEAR
    # Poisson tail — you must fund the busy days, not the average day.
    c.peak_concurrent = c.mean_concurrent + PEAK_SIGMA * math.sqrt(max(c.mean_concurrent, 0.0))
    c.capital_required_cents = c.peak_concurrent * c.mean_cost_per_position
    c.return_on_capital = (c.annual_pnl_cents / c.capital_required_cents
                           if c.capital_required_cents > 0 else 0.0)
    c.utilization = (c.mean_concurrent / c.peak_concurrent) if c.peak_concurrent > 0 else 0.0
    # How many markets a year the family would have to list for this bot to clear the bar.
    # Annual income is LINEAR in markets/yr, and markets/yr is the one input in this project
    # that is a pure estimate, so this number is where the whole dollar figure actually
    # rests. Quoting it turns "the bot earns $X" into the falsifiable "the bot earns the bar
    # if and only if the exchange lists N of these", which somebody can go and count.
    bar = float(GATE_MIN_DOLLARS)
    c.breakeven_markets_per_year = (bar / (c.mean_per_market / 100.0)
                                    if c.mean_per_market > 0 else float("inf"))
    return c


def fmt(c: Capacity) -> list[str]:
    d = 100.0
    return [
        f"  markets listed per year (ESTIMATE) : {c.markets_per_year:,}",
        f"  bot trades in                      : {c.traded_fraction * 100:.0f}% of them",
        f"  mean fill size                     : {c.mean_contracts:.0f} contracts "
        f"(depth-limited)",
        f"  edge per market offered            : {c.mean_per_market:+.2f}c",
        f"  ANNUAL P&L                         : ${c.annual_pnl_cents / d:,.0f}",
        f"  mean position cost                 : ${c.mean_cost_per_position / d:,.2f} "
        f"held {c.mean_hold_hours:.1f}h",
        f"  positions open at once             : {c.mean_concurrent:.2f} mean, "
        f"{c.peak_concurrent:.2f} peak",
        f"  CAPITAL YOU MUST COMMIT            : ${c.capital_required_cents / d:,.0f}",
        f"  return on committed capital        : {c.return_on_capital * 100:,.0f}%/yr",
        f"  capital utilisation                : {c.utilization * 100:.0f}% "
        f"(the rest of the time it is idle)",
        f"  clears ${GATE_MIN_DOLLARS:,}/yr iff the family lists : "
        f"{c.breakeven_markets_per_year:,.0f} markets/yr "
        f"(estimated {c.markets_per_year:,})",
    ]


def parse_spec(spec: str):
    family, _, botspec = spec.partition("/")
    family = family.strip()
    if family not in markets.FAMILIES:
        raise SystemExit(f"unknown family {family!r}. Known: {', '.join(markets.FAMILIES)}")
    name, _, rest = botspec.strip().partition("(")
    cls = next((c for c in strategies.ALL if c.__name__ == name.strip()), None)
    if cls is None:
        raise SystemExit(f"unknown strategy {name!r}")
    params = {}
    for part in rest.rstrip(")").split(","):
        if not part.strip():
            continue
        k, _, v = part.partition("=")
        try:
            params[k.strip()] = int(v)
        except ValueError:
            params[k.strip()] = float(v)
    return family, cls(**params)


def from_results(path: pathlib.Path, which="winners"):
    if not path.exists():
        raise SystemExit(f"{path} not found — run `python -m kalshi.factory` first")
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get(which) or []
    if not rows:
        raise SystemExit(f"no {which} in {path}")
    out = []
    for r in rows:
        cls = next((c for c in strategies.ALL if c.__name__ == r["strategy"]), None)
        if cls is None:
            continue
        out.append((r["family"], cls(**r["params"])))
    return out


def write_report(results: list[Capacity], path: pathlib.Path):
    L = ["# Kalshi Bot Factory — Capacity\n"]
    L.append("What the winning bots are worth **in dollars per year**, which is a different "
             "question from what `RESULTS.md` reports and a more useful one.\n")
    L.append("> `markets_per_year` in `config.json` is an **estimate** from general knowledge "
             "of what Kalshi lists. It was not scraped and not verified, and it scales every "
             "dollar figure on this page linearly. Fill sizes come from the simulator's depth "
             "model. No competition is modelled — a thin structural edge is exactly the kind "
             "somebody else's bot is already resting on.\n")
    L.append("| bot | markets/yr | fill | edge/market | **annual P&L** | capital to commit | return on it | utilisation |")
    L.append("|---|---|---|---|---|---|---|---|")
    for c in sorted(results, key=lambda x: -x.annual_pnl_cents):
        L.append(f"| `{c.family}` / {c.label} | {c.markets_per_year:,} | "
                 f"{c.mean_contracts:.0f} | {c.mean_per_market:+.1f}c | "
                 f"**${c.annual_pnl_cents / 100:,.0f}** | ${c.capital_required_cents / 100:,.0f} | "
                 f"{c.return_on_capital * 100:,.0f}%/yr | {c.utilization * 100:.0f}% |")
    L.append("")
    if results:
        best = max(results, key=lambda x: x.annual_pnl_cents)
        L.append("## What this changes\n")
        L.append(f"The best bot in `RESULTS.md` reports a headline return in the thousands of "
                 f"percent. Its actual output is **${best.annual_pnl_cents / 100:,.0f} a "
                 f"year** on **${best.capital_required_cents / 100:,.0f}** of committed "
                 f"capital, because `{best.family}` lists roughly "
                 f"{best.markets_per_year:,} markets a year and the book holds about "
                 f"{best.mean_contracts:.0f} contracts at the price where the edge lives.\n")
        L.append(f"The percentage is not wrong — it is a return on capital measured only over "
                 f"the {best.utilization * 100:.0f}% of the year that capital is deployed. "
                 f"Both numbers describe the same bot. Only one of them tells you whether to "
                 f"build it.\n")
        L.append("The two ways this gets better are both about the denominator, not the edge: "
                 "find the same inefficiency in a family that lists more markets, or find it "
                 "at a price where the book is deeper. Neither is a tuning problem.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Turn a percentage return into dollars per year.")
    ap.add_argument("--bot", help="'family/strategy(params)' to analyse one bot")
    ap.add_argument("--all", action="store_true", help="every bot that reached out-of-sample")
    ap.add_argument("--groups", type=int, default=1200)
    ap.add_argument("--no-report", action="store_true")
    args = ap.parse_args()

    if args.bot:
        specs = [parse_spec(args.bot)]
    else:
        specs = from_results(ROOT / "results.json",
                             "candidates" if args.all else "winners")

    out = []
    for family, strat in specs:
        c = analyse(family, strat, n_groups=args.groups)
        out.append(c)
        print(f"\n{family} / {strat.label()}")
        for line in fmt(c):
            print(line)

    if out and not args.no_report and not args.bot:
        write_report(out, ROOT / "CAPACITY.md")
        print(f"\nwrote {ROOT / 'CAPACITY.md'}")


if __name__ == "__main__":
    main()
