"""
The execution engine. Its whole job is to be pessimistic in the right places.

A backtester that is wrong is worse than no backtester, because it produces a number
with a decimal point in it. Four things are the usual way that happens, and each one is
handled here structurally rather than by being careful:

1. LOOKAHEAD. Strategies are handed a `View`, not an `Episode`. The View exposes bid,
   ask, depth and spread at offsets <= 0 from the current step, and asserts on anything
   later. It has no reference to `true_p` and no reference to `outcome` — not a private
   one, not a hidden one. A strategy cannot peek because there is nothing to peek at.
   `selftest.py` additionally greps `strategies.py` for `true_p` and `outcome`, which is
   the same trick `sim/check_drift.py` uses on the C# and JS.

2. PAYING THE MID. Every taker buy pays the ask and every taker sell receives the bid.
   On a 1c-tick book with 2-4c spreads this is most of the cost, and a backtester that
   fills at the mid will report a profitable bot for every strategy in this file.

3. INFINITE LIQUIDITY. Orders are capped at the depth quoted at the touch. A bot that
   wants 500 contracts in a 30-contract book gets 30. This is what makes `awards_thin`
   score badly despite having the largest gross edge on the exchange, and that ranking
   flip only appears if depth is enforced.

4. FREE MAKER FILLS. A resting order fills when price moves THROUGH it — which is to say
   it fills precisely when it was wrong. Benign fills from uninformed flow happen at
   `microstructure.maker_benign_fill_rate`, which is a guess, and every market-making
   result in this project is downstream of that guess. It is flagged in the log, in the
   config, and in the report.

WHAT IS DELIBERATELY NOT MODELLED, because pretending otherwise would be worse:
  * Market impact beyond depth-at-touch. Taking 800 of an 800-contract book would move
    the next quote in reality; here it does not.
  * A shared bankroll across simultaneous markets. Each group is independently
    capitalised to `capital.max_position_cents_per_market`. So there is no compounding
    and no path to ruin in these numbers — the engine measures whether an edge exists,
    not what a portfolio of it would do. Sizing is a separate problem and this project
    does not solve it.
  * Queue position. A resting order is either at the touch or it is not.
  * Rejected orders, outages, settlement disputes, and the exchange's position limits.
"""

from __future__ import annotations

import json
import pathlib
import random
from collections import namedtuple

from . import fees
from .markets import Group

_CFG = json.loads((pathlib.Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
_CAP = _CFG["capital"]
_MICRO = _CFG["microstructure"]

MAX_POS_CENTS = int(_CAP["max_position_cents_per_market"])
MAX_ORDER = int(_CAP["max_contracts_per_order"])
BENIGN_FILL = float(_MICRO["maker_benign_fill_rate"])
HOURS_PER_YEAR = 24 * 365

# leg: index into the group. action: "open" | "close". side: "yes" | "no".
# otype: "taker" | "maker". limit: required for maker, ignored for taker.
Intent = namedtuple("Intent", "leg action side qty otype limit")


def taker(leg, side, qty):
    return Intent(leg, "open", side, qty, "taker", None)


def close(leg, qty=None):
    return Intent(leg, "close", None, qty, "taker", None)


def maker(leg, side, qty, limit):
    return Intent(leg, "open", side, qty, "maker", limit)


class Costs:
    """Execution assumptions. The gate re-runs every candidate through a harsher set of
    these; a bot whose edge does not survive that was fitting the assumptions."""

    __slots__ = ("fee_mult", "extra_spread", "fill_mult", "label")

    def __init__(self, fee_mult=1.0, extra_spread=0, fill_mult=1.0, label="base"):
        self.fee_mult = fee_mult
        self.extra_spread = extra_spread
        self.fill_mult = fill_mult
        self.label = label


BASE_COSTS = Costs()


class View:
    """What a strategy is allowed to know about one market: the public book, up to now.

    `_t` advances as the engine steps. Any request for data at a step the engine has not
    reached raises. That assert is the no-lookahead guarantee.
    """

    __slots__ = ("_bid", "_ask", "_depth", "_t", "n", "leg", "family")

    def __init__(self, ep, leg):
        self._bid, self._ask, self._depth = ep.bid, ep.ask, ep.depth
        self.n = ep.n
        self.leg = leg
        self.family = ep.family.name
        self._t = 0

    def _idx(self, dt):
        if dt > 0:
            raise AssertionError("lookahead: strategies may only read dt <= 0")
        i = self._t + dt
        if i < 0:
            i = 0
        return i

    def bid(self, dt=0):
        return self._bid[self._idx(dt)]

    def ask(self, dt=0):
        return self._ask[self._idx(dt)]

    def depth(self, dt=0):
        return self._depth[self._idx(dt)]

    def mid(self, dt=0):
        i = self._idx(dt)
        return (self._bid[i] + self._ask[i]) / 2.0

    def spread(self, dt=0):
        i = self._idx(dt)
        return self._ask[i] - self._bid[i]

    def no_ask(self, dt=0):
        """One book: a YES bid at 40 IS a NO ask at 60."""
        return 100 - self._bid[self._idx(dt)]

    def no_bid(self, dt=0):
        return 100 - self._ask[self._idx(dt)]

    @property
    def t(self):
        return self._t

    def frac(self):
        """Fraction of the contract's life elapsed. Expiry is public information."""
        return self._t / max(self.n - 1, 1)

    def steps_left(self):
        return self.n - 1 - self._t

    def hist_mid(self, k):
        """Last k mids, oldest first. Shorter than k early in the market's life."""
        lo = max(0, self._t - k + 1)
        return [(self._bid[i] + self._ask[i]) / 2.0 for i in range(lo, self._t + 1)]


class GroupView:
    __slots__ = ("legs", "family", "n_legs")

    def __init__(self, group: Group):
        self.legs = [View(ep, i) for i, ep in enumerate(group.legs)]
        self.family = group.family.name
        self.n_legs = len(self.legs)

    def _advance(self, t):
        for v in self.legs:
            v._t = t


class Position:
    __slots__ = ("side", "qty", "cost", "opened_t")

    def __init__(self, side, qty, cost, opened_t):
        self.side, self.qty, self.cost, self.opened_t = side, qty, cost, opened_t


class Result:
    """What one backtest produced.

    `group_pnl` is the statistical unit and it has one entry PER GROUP OFFERED, including
    zeros for groups the bot declined to trade. That choice matters: a per-trade mean
    rewards a bot for being selective in hindsight, while per-group-offered is an unbiased
    estimate of what the strategy earns per market it is shown. Trades inside a group are
    correlated (a bracket arb takes five legs at once), so the group is also the only
    correct resampling unit for the bootstrap in `evaluate.py`.
    """

    __slots__ = ("group_pnl", "n_trades", "n_contracts", "capital_cent_hours",
                 "gross_pnl", "fees_paid", "life_hours", "n_groups", "trade_pnl",
                 "max_position_cost", "cost_sum", "hold_hours_sum", "n_closed")

    def __init__(self):
        self.group_pnl: list[int] = []
        self.trade_pnl: list[int] = []
        self.n_trades = 0
        self.n_contracts = 0
        self.capital_cent_hours = 0.0
        self.gross_pnl = 0
        self.fees_paid = 0
        self.life_hours = 0.0
        self.n_groups = 0
        # Largest single position ever opened, in cents. This is the most a hold-to-
        # settlement trade can lose, and it is what the tail check in evaluate.py falls back
        # to when a strategy's losses are so rare that none were observed.
        self.max_position_cost = 0
        # Accumulated so capacity.py can report mean position cost and mean holding time
        # directly instead of inferring them from capital-hours, which needed an assumption
        # about the cost/duration split and got both slightly wrong in opposite directions.
        self.cost_sum = 0
        self.hold_hours_sum = 0.0
        self.n_closed = 0

    @property
    def total_pnl(self):
        return sum(self.group_pnl)

    @property
    def annualized_return(self):
        """Return on capital actually locked up, per year. An IDEALISED UPPER BOUND.

        The reason a 3c edge on a 90-day political market loses to a 0.3c edge on an hourly
        crypto market: collateral on Kalshi is locked until settlement, so the edge per turn
        has to be multiplied by how often the capital comes back.

        READ THIS BEFORE QUOTING THE NUMBER. It is simple, not compounded, and it assumes
        capital is redeployed the instant a position settles into another market with the
        same edge. Neither assumption holds — there is a finite supply of qualifying markets
        at any moment, and the figures it produces on short-dated families run into the
        thousands of percent, which is arithmetic, not a forecast. It earns its place as a
        FLOOR: a strategy that cannot clear 5% on this generous a basis definitely cannot
        pay for the collateral it ties up. It is not evidence for the upside.
        """
        if self.capital_cent_hours <= 0:
            return 0.0
        return self.total_pnl / (self.capital_cent_hours / HOURS_PER_YEAR)


def _cap_qty(want, depth, cost_per, already_cents):
    qty = min(int(want), int(depth), MAX_ORDER)
    if qty <= 0 or cost_per <= 0:
        return 0
    room = MAX_POS_CENTS - already_cents
    if room <= 0:
        return 0
    return max(0, min(qty, room // cost_per))


def run_group(group: Group, strat, costs: Costs = BASE_COSTS, rng=None) -> tuple[int, int, int, float, int, int]:
    """Backtest one market (or bracket set).

    Returns (group_pnl, n_trades, n_contracts, capital_cent_hours, gross, fees_paid,
    per_trade_pnl, max_position_cost, cost_sum, hold_hours_sum, n_closed). The caller
    aggregates.
    """
    rng = rng or random.Random(group.gid * 1000003)
    gv = GroupView(group)
    n_steps = group.steps
    step_h = group.family.step_hours
    legs = group.legs

    pos: list[Position | None] = [None] * len(legs)
    resting: list[Intent] = []
    pnl = 0
    gross = 0
    fee_total = 0
    n_trades = 0
    n_contracts = 0
    cap_hours = 0.0
    max_cost = 0
    cost_sum = 0
    hold_sum = 0.0
    n_closed = 0
    trade_log = []

    for t in range(n_steps):
        gv._advance(t)

        # --- 1. resting orders posted last step, resolved against this step's book ----
        for order in resting:
            i = order.leg
            if pos[i] is not None:
                continue
            ep = legs[i]
            bid_t, ask_t = ep.bid[t], ep.ask[t]
            mid_t = (bid_t + ask_t) / 2.0
            q = order.limit
            if order.side == "yes":
                crossed = ask_t <= q                       # price fell through our bid
                near = mid_t <= q + 1
            else:
                no_ask_t = 100 - bid_t
                crossed = no_ask_t <= q
                near = (100 - mid_t) <= q + 1
            filled = crossed or (near and rng.random() < BENIGN_FILL * costs.fill_mult)
            if not filled:
                continue
            price = q
            qty = _cap_qty(order.qty, ep.depth[t], price, 0)
            if qty <= 0:
                continue
            f = fees.maker_fee_cents(qty, price, costs.fee_mult)
            cost = qty * price + f
            pos[i] = Position(order.side, qty, cost, t)
            max_cost = max(max_cost, cost)
            fee_total += f
            n_trades += 1
            n_contracts += qty
        resting = []

        # --- 2. the strategy decides, seeing only the public book up to t -------------
        intents = strat.decide(gv, pos)

        # --- 3. execute ---------------------------------------------------------------
        for it in intents:
            i = it.leg
            ep = legs[i]
            bid_t, ask_t = ep.bid[t], ep.ask[t]

            if it.action == "close":
                p = pos[i]
                if p is None:
                    continue
                qty = p.qty if it.qty is None else min(it.qty, p.qty)
                if qty <= 0:
                    continue
                if p.side == "yes":
                    px = max(1, bid_t - costs.extra_spread)
                else:
                    px = max(1, (100 - ask_t) - costs.extra_spread)
                fillable = min(qty, ep.depth[t])
                if fillable <= 0:
                    continue
                f = fees.taker_fee_cents(fillable, px, costs.fee_mult)
                proceeds = fillable * px - f
                basis = p.cost * fillable // p.qty
                realized = proceeds - basis
                pnl += realized
                gross += fillable * px - basis
                fee_total += f
                held_h = (t - p.opened_t) * step_h
                cap_hours += basis * held_h
                cost_sum += basis
                hold_sum += held_h
                n_closed += 1
                n_trades += 1
                n_contracts += fillable
                trade_log.append(realized)
                if fillable >= p.qty:
                    pos[i] = None
                else:
                    p.cost -= basis
                    p.qty -= fillable
                continue

            if it.otype == "maker":
                if pos[i] is None and it.limit is not None and 1 <= it.limit <= 99:
                    resting.append(it)
                continue

            if pos[i] is not None:
                continue
            if it.side == "yes":
                px = min(99, ask_t + costs.extra_spread)
            else:
                px = min(99, (100 - bid_t) + costs.extra_spread)
            qty = _cap_qty(it.qty, ep.depth[t], px, 0)
            if qty <= 0:
                continue
            f = fees.taker_fee_cents(qty, px, costs.fee_mult)
            pos[i] = Position(it.side, qty, qty * px + f, t)
            max_cost = max(max_cost, qty * px + f)
            fee_total += f
            n_trades += 1
            n_contracts += qty

    # --- 4. anything still open settles. No exit fee — this is the cheapest exit -----
    last_t = n_steps - 1
    for i, p in enumerate(pos):
        if p is None:
            continue
        ep = legs[i]
        win = ep.outcome if p.side == "yes" else (1 - ep.outcome)
        payout = 100 * p.qty * win
        settle_f = fees.settlement_fee_cents(p.qty)
        realized = payout - p.cost - settle_f
        pnl += realized
        gross += payout - p.cost
        fee_total += settle_f
        held_h = max((last_t - p.opened_t) * step_h, step_h)
        cap_hours += p.cost * held_h
        cost_sum += p.cost
        hold_sum += held_h
        n_closed += 1
        trade_log.append(realized)

    return (pnl, n_trades, n_contracts, cap_hours, gross, fee_total, trade_log, max_cost,
            cost_sum, hold_sum, n_closed)


def run(groups: list[Group], strat, costs: Costs = BASE_COSTS) -> Result:
    res = Result()
    res.n_groups = len(groups)
    for g in groups:
        pnl, nt, nc, ch, gr, ft, tl, mc, cs, hs, ncl = run_group(g, strat, costs)
        res.group_pnl.append(pnl)
        res.trade_pnl.extend(tl)
        res.n_trades += nt
        res.n_contracts += nc
        res.capital_cent_hours += ch
        res.gross_pnl += gr
        res.fees_paid += ft
        res.life_hours += g.family.life_hours
        res.max_position_cost = max(res.max_position_cost, mc)
        res.cost_sum += cs
        res.hold_hours_sum += hs
        res.n_closed += ncl
    return res
