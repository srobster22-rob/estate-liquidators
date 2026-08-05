"""
Kalshi fee model — the most important 30 lines in this directory.

Every strategy idea in `strategies.py` lives or dies here, so it gets its own module
with its own worked examples rather than being a helper buried in the backtester.

THE FORMULA (per order, not per contract):

    fee = ceil_to_cent( 0.07 * contracts * P * (1 - P) )        P in dollars

Two properties of that shape drive every result in this project, and neither is obvious
until you put numbers in it:

1. IT PEAKS AT 50c AND VANISHES AT THE EXTREMES.
   P*(1-P) is 0.25 at P=0.50 and 0.0475 at P=0.05. One contract at 50c costs 1.75c to
   enter; one at 5c costs 0.33c. So a round trip through the middle of the book burns
   ~3.5c of a 100c notional — 3.5% — while the same round trip at a nickel burns 0.7%.
   Any strategy that trades near even money needs to find >3.5c of edge before it has
   found anything at all. That is an enormous bar and it kills most of the obvious ideas.

2. THE CEILING IS CHARGED PER ORDER, SO SIZE IS FREE ALPHA.
   1 contract at 5c: raw fee 0.33c, rounded up to 1c -> 1.0c per contract.
   100 contracts at 5c: raw 33.25c, rounded up to 34c -> 0.34c per contract.
   The rounding penalty on a 1-lot at a nickel is 3x the actual fee. A bot that fires
   small orders is paying a tax that has nothing to do with its edge.

`breakeven_edge_cents` exists so a strategy can ask, before it trades, how much gross
edge it needs — and decline. Several strategies in this project do exactly that, and
that check is why they survive contact with the fee model.

VERIFIED against Kalshi's published schedule and independent worked examples. `selftest.py`
section 1b reproduces them: 10 contracts @ 50c = $0.18, 20 @ 50c = $0.35, per-contract
0.0175 / 0.0112 / 0.0063 at 50c / 20c / 10c, no settlement fee. The 0.07 rate, the P(1-P)
shape and the per-ORDER round-up are all confirmed.

TWO THINGS WERE WRONG BEFORE THAT CHECK, and both are fixed:
  * The MAKER formula was a guess — `0.0025 * C * P`, linear in price. The real schedule is
    `0.0175 * C * P * (1-P)`: a quarter of the taker rate with the same curve, charged only
    on designated series (default multiplier 0, so most markets pay makers nothing).
  * The S&P 500 (INX*) and Nasdaq-100 (NASDAQ100*) series are charged 0.035, HALF the
    standard rate — and that is exactly what `index_bracket_daily` models. It had been
    paying double, which understated the only riskless trade in the project by 3.3x.

ONE THING REMAINS AMBIGUOUS: sources disagree on whether the round-up is to the whole cent
or to a "centicent". Whole cent matches every published example that has a number attached,
so it is what runs; `rounding_granularity_cents` in config.json switches the other reading on
and selftest 1b prices the difference. Whole-cent is also the conservative choice — it never
charges less — so no result here is flattered by the ambiguity.
"""

from __future__ import annotations

import json
import math
import pathlib

_CFG = json.loads((pathlib.Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
_F = _CFG["fees"]

TAKER_RATE = float(_F["taker_rate"])
MAKER_RATE = float(_F["maker_rate"])
SETTLEMENT_FEE = int(_F["settlement_fee_cents_per_contract"])
GRANULARITY = float(_F.get("rounding_granularity_cents", 1.0))
SERIES_MULTIPLIER = {k: v for k, v in _F.get("series_fee_multiplier", {}).items()
                     if not k.startswith("_")}


def _ceil_cent(cents: float) -> float:
    """Round an order's fee up to the next `GRANULARITY` cents.

    Kalshi's published worked examples all match a round-up to the WHOLE CENT, charged per
    ORDER rather than per contract: 10 contracts at 50c is a raw $0.175 and a charged $0.18;
    20 contracts at 50c is exactly $0.35. Some wording in the 2026 schedule instead says the
    round-up is to a "centicent". The whole-cent reading is used because it matches every
    example that has a number attached to it, and `rounding_granularity_cents` exists so the
    other reading can be measured rather than argued about — see selftest 1b, which prices
    the difference at a fraction of a cent per order.

    The 1e-9 guard keeps 1.75 * 4 = 7.000000000000001 from becoming 8c. Money is integer
    cents everywhere else in this project precisely so this is the only place float error
    can enter.
    """
    if GRANULARITY <= 0:
        return cents
    if GRANULARITY == 1.0:
        # The default. Return a genuine int so the "money is integer cents everywhere"
        # invariant survives — sub-cent granularity is a sensitivity experiment, not the
        # normal path, and only it is allowed to produce fractional cents.
        return int(math.ceil(cents - 1e-9))
    return math.ceil(cents / GRANULARITY - 1e-9) * GRANULARITY


def taker_fee_cents(contracts: int, price_cents: int, rate_multiplier: float = 1.0,
                    series_multiplier: float = 1.0) -> float:
    """Fee for one taker order: round_up(M * 0.07 * C * P * (1-P)).

    `series_multiplier` is Kalshi's own M. It defaults to 1, and it is 0.5 for the S&P 500
    (INX*) and Nasdaq-100 (NASDAQ100*) series, which are charged 0.035 rather than 0.07.
    That halving is real, published, and it applies to exactly the markets
    `index_bracket_daily` models — which had been paying double the true rate.

    `rate_multiplier` is separate: it is the gate's stress test (gate.stress_fee_multiplier),
    because a bot whose edge evaporates at 1.5x fees was trading a fee assumption.
    """
    if contracts <= 0:
        return 0
    p = price_cents / 100.0
    raw_dollars = TAKER_RATE * series_multiplier * rate_multiplier * contracts * p * (1.0 - p)
    return _ceil_cent(raw_dollars * 100.0)


def maker_fee_cents(contracts: int, price_cents: int, rate_multiplier: float = 1.0,
                    series_multiplier: float = 1.0) -> float:
    """Fee for one resting order that gets filled: round_up(M * 0.0175 * C * P * (1-P)).

    SAME SHAPE AS THE TAKER FEE, A QUARTER OF THE RATE. An earlier version of this had it as
    `0.0025 * C * P` — linear in price and seven times too small at the extremes — which was
    a guess, and wrong on both counts. The real schedule is 0.0175 with the same P(1-P) curve,
    charged only on designated series (default multiplier 0, so most markets pay makers
    nothing). `maker_rate` stays 0.0 by default for that reason; set it to
    `maker_rate_if_charged` to re-read the market-making results under the charged regime.
    """
    if contracts <= 0 or MAKER_RATE <= 0.0:
        return 0
    p = price_cents / 100.0
    raw_dollars = MAKER_RATE * series_multiplier * rate_multiplier * contracts * p * (1.0 - p)
    return _ceil_cent(raw_dollars * 100.0)


def settlement_fee_cents(contracts: int) -> int:
    return SETTLEMENT_FEE * max(0, contracts)


def breakeven_edge_cents(price_cents: int, contracts: int = 100) -> float:
    """Gross per-contract edge required just to cover the entry fee, in cents.

    Assumes the position is held to resolution — no exit fee. A strategy that plans to
    exit early must clear roughly twice this, which is the whole reason `theta_decay`
    (hold to settlement) beats `mean_revert` (round trip) on identical information.
    """
    if contracts <= 0:
        return float("inf")
    return taker_fee_cents(contracts, price_cents) / contracts


def round_trip_cost_cents(price_cents: int, contracts: int = 100, exit_price_cents: int | None = None) -> float:
    """Per-contract fee cost of entering AND exiting, ignoring the spread."""
    exit_price_cents = price_cents if exit_price_cents is None else exit_price_cents
    total = taker_fee_cents(contracts, price_cents) + taker_fee_cents(contracts, exit_price_cents)
    return total / contracts


def fee_table(contracts: int = 100) -> list[tuple[int, float, float]]:
    """(price, entry fee per contract, round-trip fee per contract) across the book."""
    out = []
    for p in range(2, 99, 2):
        out.append((p, breakeven_edge_cents(p, contracts), round_trip_cost_cents(p, contracts)))
    return out


if __name__ == "__main__":
    print(f"Kalshi fee model  (taker_rate={TAKER_RATE}, maker_rate={MAKER_RATE})\n")
    print("Per-contract cost, 100-lot orders:")
    print(f"  {'price':>6} {'entry':>8} {'round trip':>11}   {'edge needed to break even':<28}")
    for p, entry, rt in fee_table(100):
        if p % 10 == 0 or p in (2, 98):
            print(f"  {p:>5}c {entry:>7.2f}c {rt:>10.2f}c   hold-to-settle {entry:>5.2f}c / round trip {rt:>5.2f}c")

    print("\nThe per-order ceiling is a tax on small orders:")
    for c in (1, 5, 20, 100, 250):
        f = taker_fee_cents(c, 5)
        print(f"  {c:>4} contracts @ 5c -> fee {f:>4}c total = {f / c:>5.2f}c/contract"
              f"   (raw {TAKER_RATE * c * 0.05 * 0.95 * 100:>6.2f}c)")

    print("\nWorst place to trade is the middle:")
    for p in (5, 25, 50, 75, 95):
        print(f"  {p:>3}c: round trip costs {round_trip_cost_cents(p, 100):.2f}c/contract"
              f" = {round_trip_cost_cents(p, 100):.2f}% of notional")
