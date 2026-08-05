"""
The market census — replacing the one estimate the dollar figure actually rests on.

    python -m kalshi.census          shows the count and what it does to the answer

WHY THIS FILE EXISTS

Annual income is strictly linear in markets-per-year, and until now that number was a guess:
250 for `econ_print`, written down as "~70 releases x a few strikes" and flagged as unverified
in three places. `capacity.py` reported that the winning bot clears the $250/yr bar **if and
only if** the family lists >= 469 markets a year. So the entire result reduced to a counting
question, and this file is the count.

HOW IT WAS COUNTED, AND WHY NOT FROM THE API

Kalshi's API returns 403 to every request from this environment — the container's proxy blocks
the host, and the fetch tooling is blocked by Kalshi's own bot protection, including on
kalshi.com itself. So the census is assembled from published sources rather than from
`GET /markets`, and the headline figure comes from an academic dataset:

    "Information Efficiency Across Macroeconomic Prediction Markets: Evidence from Kalshi"
    -> 2,668 SETTLED CONTRACTS across EIGHT economic series, July 2021 - June 2026.

    July 2021 through June 2026 inclusive is 60 months, exactly 5.0 years.
    2,668 / 5.0 = 534 contracts per year.

That is a COUNT of settled contracts, which is precisely the quantity `markets_per_year` is
meant to be, and it is 2.1x the guess it replaces.

THREE REASONS IT IS A LOWER BOUND

  1. Eight series, not all of them. Kalshi's economics category is wider than the eight the
     paper groups (Fed/rates, inflation, labour).
  2. The window includes Kalshi's small years. A 2021-2026 average understates the 2026
     run-rate on an exchange whose volume grew by orders of magnitude over the window.
  3. Settled contracts only. Anything still open at the cutoff is not in the 2,668.

THE CATCH, AND IT IS A REAL ONE: CONTRACTS ARE NOT INDEPENDENT BETS

A Kalshi CPI market is a LADDER — nested rungs ("above 0.2%", "above 0.3%", ...) that all
settle from one printed number. Six rungs is one bet resolved six ways, not six bets. So the
census produces two different numbers and they are used for two different things:

    contracts/year  ~534   each rung has its own book and its own depth, so INCOME scales
                           with this. It is the right multiplier for dollars.
    events/year     ~124   the number of independent resolutions. RISK and EVIDENCE scale
                           with this. It is the right denominator for a confidence interval.

Reconciling the two is also a check on the count: 534 / 124 = 4.3 rungs per event, which is
consistent with the ladder sizes visible in published examples (a Core CPI ladder priced
across six thresholds). Two independently-sourced numbers landing on a plausible third is
weak evidence, but it is evidence.

WHAT IT DOES TO THE ANSWER: at the replicated edge of +53.3c per market, 534 contracts a year
is $285, against a $250 bar and a $214 headline that was never real. The bar is cleared on
income — and the same census says the risk behind it is concentrated in ~124 independent
events a year, not 534.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).parent

# --- the counted figure ------------------------------------------------------------
SETTLED_CONTRACTS = 2668
WINDOW_MONTHS = 60          # July 2021 through June 2026 inclusive
WINDOW_YEARS = WINDOW_MONTHS / 12.0
SERIES_COUNTED = 8
COUNTED_CONTRACTS_PER_YEAR = SETTLED_CONTRACTS / WINDOW_YEARS

SOURCE = ('"Information Efficiency Across Macroeconomic Prediction Markets: Evidence from '
          'Kalshi" — 2,668 settled contracts, 8 series, July 2021-June 2026')

# --- the release calendar, used to split contracts into independent events ---------
# Cadences are from the published release schedules of the underlying statistics, which are
# fixed and public. Series existence is confirmed by Kalshi tickers seen in search results
# (KXCPI, KXPAYROLLS, KXFED, KXJOBLESSCLAIMS, KXU3MAX). The mapping of "eight series" to
# exactly these eight is INFERRED, not stated by the paper.
SERIES = [
    # (label, ticker or None, events per year, evidence strength)
    ("Initial jobless claims", "KXJOBLESSCLAIMS", 52, "ticker confirmed; weekly DOL release"),
    ("CPI headline", "KXCPI", 12, "ticker confirmed; monthly BLS release"),
    ("Core CPI", None, 12, "ladder example published; monthly"),
    ("Nonfarm payrolls", "KXPAYROLLS", 12, "ticker confirmed; monthly BLS release"),
    ("Unemployment rate", "KXU3MAX", 12, "ticker confirmed; monthly BLS release"),
    ("Fed / FOMC rate decision", "KXFED", 8, "ticker confirmed; 8 scheduled meetings a year"),
    ("PCE inflation", None, 12, "series named in coverage; monthly BEA release"),
    ("GDP", None, 4, "series named in coverage; quarterly BEA release"),
]

EVENTS_PER_YEAR = sum(e for _, _, e, _ in SERIES)
RUNGS_PER_EVENT = COUNTED_CONTRACTS_PER_YEAR / EVENTS_PER_YEAR


def summary() -> dict:
    return {
        "source": SOURCE,
        "settled_contracts": SETTLED_CONTRACTS,
        "window_years": WINDOW_YEARS,
        "contracts_per_year": COUNTED_CONTRACTS_PER_YEAR,
        "events_per_year": EVENTS_PER_YEAR,
        "rungs_per_event": RUNGS_PER_EVENT,
        "series_counted": SERIES_COUNTED,
        "prior_estimate": 250,
    }


def report() -> list[str]:
    L = []
    L.append(f"THE COUNT (replacing a guess of 250/yr)")
    L.append(f"  source : {SOURCE}")
    L.append(f"  {SETTLED_CONTRACTS:,} settled contracts / {WINDOW_YEARS:.1f} years "
             f"= {COUNTED_CONTRACTS_PER_YEAR:.0f} contracts per year")
    L.append(f"  that is {COUNTED_CONTRACTS_PER_YEAR / 250:.1f}x the estimate it replaces, "
             f"and it is a LOWER bound (8 series only; window includes Kalshi's small years)")
    L.append("")
    L.append("THE RELEASE CALENDAR — independent resolutions, not contracts")
    L.append(f"  {'series':<28} {'ticker':<20} {'events/yr':>9}  evidence")
    L.append("  " + "-" * 92)
    for label, ticker, ev, note in SERIES:
        L.append(f"  {label:<28} {(ticker or '—'):<20} {ev:>9}  {note}")
    L.append("  " + "-" * 92)
    L.append(f"  {'TOTAL':<28} {'':<20} {EVENTS_PER_YEAR:>9}  independent events per year")
    L.append("")
    L.append(f"  {COUNTED_CONTRACTS_PER_YEAR:.0f} contracts / {EVENTS_PER_YEAR} events "
             f"= {RUNGS_PER_EVENT:.1f} rungs per event")
    L.append(f"  Consistent with published ladder examples (~6 thresholds on a Core CPI "
             f"ladder). Two independently-sourced numbers landing on a plausible third.")
    L.append("")
    L.append("THE TWO NUMBERS DO DIFFERENT JOBS")
    L.append(f"  income scales with CONTRACTS ({COUNTED_CONTRACTS_PER_YEAR:.0f}/yr) — each "
             f"rung has its own book and its own depth")
    L.append(f"  risk and evidence scale with EVENTS ({EVENTS_PER_YEAR}/yr) — nested rungs "
             f"settle from one printed number, so six rungs is one bet resolved six ways")
    return L


def write_report(path: pathlib.Path, edge_cents: float | None = None,
                 bar: float | None = None):
    L = ["# Kalshi Bot Factory — Market Census\n"]
    L.append("The one estimate the whole dollar figure rested on, replaced with a count.\n")
    L.append(f"> **{COUNTED_CONTRACTS_PER_YEAR:.0f} economics contracts per year**, from "
             f"{SETTLED_CONTRACTS:,} settled contracts across {SERIES_COUNTED} series over "
             f"{WINDOW_YEARS:.1f} years.\n>\n> Source: {SOURCE}\n")
    L.append("Counted from published sources rather than from `GET /markets`: Kalshi's API "
             "returns 403 to every request from this environment, and so does kalshi.com "
             "itself. That makes this a *sourced count* rather than a *measurement*, and the "
             "distinction is worth keeping — the honest next step is still to run the census "
             "against the live API from a machine with egress.\n")
    L.append("## The release calendar\n")
    L.append("| series | ticker | events/yr | evidence |")
    L.append("|---|---|---|---|")
    for label, ticker, ev, note in SERIES:
        L.append(f"| {label} | `{ticker}` | {ev} | {note} |" if ticker
                 else f"| {label} | — | {ev} | {note} |")
    L.append(f"| **total** | | **{EVENTS_PER_YEAR}** | independent resolutions per year |")
    L.append("")
    L.append(f"{COUNTED_CONTRACTS_PER_YEAR:.0f} contracts ÷ {EVENTS_PER_YEAR} events = "
             f"**{RUNGS_PER_EVENT:.1f} rungs per event**, consistent with the ~6-threshold "
             f"ladders visible in published Core CPI examples. Two independently sourced "
             f"numbers landing on a plausible third is weak evidence, but it is evidence.\n")
    L.append("## Contracts are not independent bets\n")
    L.append("A Kalshi CPI market is a **ladder**: nested rungs (\"above 0.2%\", \"above "
             "0.3%\", …) that all settle from one printed number. Six rungs is one bet "
             "resolved six ways. So the census yields two numbers doing two different jobs:\n")
    L.append(f"- **income** scales with contracts (~{COUNTED_CONTRACTS_PER_YEAR:.0f}/yr) — "
             f"each rung has its own book and its own depth")
    L.append(f"- **risk and evidence** scale with events (~{EVENTS_PER_YEAR}/yr) — this is "
             f"the honest denominator for a confidence interval\n")
    if edge_cents is not None and bar is not None:
        annual = COUNTED_CONTRACTS_PER_YEAR * edge_cents / 100.0
        old = 250 * edge_cents / 100.0
        L.append("## What it does to the answer\n")
        L.append(f"| | markets/yr | annual income |")
        L.append(f"|---|---|---|")
        L.append(f"| previous estimate | 250 | ${old:,.0f} |")
        L.append(f"| **counted** | **{COUNTED_CONTRACTS_PER_YEAR:.0f}** | "
                 f"**${annual:,.0f}** |")
        L.append("")
        verdict = "clears" if annual >= bar else "does not clear"
        L.append(f"At the replicated edge of {edge_cents:+.1f}¢ per market, the count "
                 f"**{verdict}** the ${bar:,.0f}/yr bar.\n")
        L.append("The income went up because the count went up, not because the bot got "
                 "better. The edge per market is unchanged and so is everything the gate "
                 "said about it.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    for line in report():
        print(line)

    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    bar = cfg["gate"]["min_annual_dollars"]
    print()
    print("EFFECT ON THE INCUMBENT (edge measured on holdout, +53.3c/market)")
    for n, label in ((250, "old estimate"), (COUNTED_CONTRACTS_PER_YEAR, "counted")):
        print(f"  {label:<14} {n:>6.0f} markets/yr -> ${n * 0.533:>7,.0f}/yr"
              f"   {'CLEARS' if n * 0.533 >= bar else 'below'} the ${bar:,} bar")
    write_report(ROOT / "CENSUS.md", edge_cents=53.3, bar=bar)
    print(f"\nwrote {ROOT / 'CENSUS.md'}")
