"""
The strategy zoo. Twelve families, four of which are expected to lose.

The losers are not padding. A factory that only tests ideas its author believes in has no
way to tell "my strategy works" from "my backtester is broken", so this file deliberately
contains:

  buy_longshot   the exact opposite of `hold_favorite`. If the planted longshot bias is
                 real and the engine's sign conventions are right, these two must come
                 out roughly mirrored. If they are both positive, the fee or payout
                 accounting is wrong and every other number here is void.
  jump_fade      the opposite of `jump_follow`, same reasoning for the underreaction edge.
  pair_arb       buy YES and NO for less than 100. Cannot exist on a single Kalshi book,
                 because a YES bid at 40 IS a NO ask at 60, so yes_ask + no_ask =
                 100 + spread >= 100 identically. Implemented so the count of
                 opportunities found can be reported as zero rather than assumed.
  random_control random entries at a fixed rate. Its only job is to fail the gate. If it
                 ever passes, the gate is broken and nothing else in this directory means
                 anything.

ONE NON-OBVIOUS THING, worth stating because it collapses two families into one:

  "Back the favourite" and "fade the longshot" are THE SAME TRADE. In a binary market,
  buying NO at 92c and buying the 92c favourite are the same position — Kalshi has one
  book and NO at 92 is YES at 8. So `hold_favorite` covers both descriptions, and the
  interesting question about it is not direction but capital: it ties up 92c to win ~2c.
  `late_favorite` exists to attack exactly that, by taking the same edge later in the
  contract's life so the collateral is locked for a fraction of the time.

Strategies see a `GroupView` (public book, current step and earlier — see backtest.py)
and the engine's position list. They cannot see `true_p` or `outcome`; those identifiers
do not appear in this file and `selftest.py` greps to keep it that way.
"""

from __future__ import annotations

import random
import statistics

from .backtest import Intent, close, maker, taker


class Strategy:
    """Base: a name, a parameter dict, and `decide`."""

    requires_brackets = False
    targets = ""

    def __init__(self, **params):
        self.params = params
        for k, v in params.items():
            setattr(self, k, v)

    @property
    def name(self):
        return type(self).__name__

    def label(self):
        ps = ",".join(f"{k}={v}" for k, v in sorted(self.params.items()))
        return f"{self.name}({ps})"

    def decide(self, gv, pos) -> list[Intent]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# EDGE 1 — longshot compression
# ---------------------------------------------------------------------------

class hold_favorite(Strategy):
    """Buy whichever side is expensive, hold to settlement.

    The cheapest possible way to harvest a pricing bias: one order, no exit, so the only
    cost is one entry fee plus half the spread. Holding to settlement instead of round
    tripping roughly halves the fee bill, and at 90c the fee is 0.63c/contract against a
    round-trip 1.26c — which is the difference between this working and not.
    """

    targets = "EDGE 1 (longshot compression)"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            if pos[v.leg] is not None or v.frac() < self.enter_frac:
                continue
            if v.ask() >= self.thresh:
                out.append(taker(v.leg, "yes", self.qty))
            elif v.no_ask() >= self.thresh:
                out.append(taker(v.leg, "no", self.qty))
        return out


class buy_longshot(Strategy):
    """Buy whichever side is cheap, hold to settlement. SIGN CONTROL — should lose.

    Under compression the cheap side is the overpriced one, so this should mirror
    `hold_favorite`. Its value is entirely diagnostic.
    """

    targets = "EDGE 1 sign control — expected to LOSE"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            if pos[v.leg] is not None or v.frac() < self.enter_frac:
                continue
            if v.ask() <= self.max_price:
                out.append(taker(v.leg, "yes", self.qty))
            elif v.no_ask() <= self.max_price:
                out.append(taker(v.leg, "no", self.qty))
        return out


class band_fade(Strategy):
    """Buy the expensive side only when the cheap side quotes inside [lo, hi].

    The overfitting canary. Nothing about a price band is a hypothesis — searching over
    (lo, hi) is fitting, and the grid in `PARAM_GRID` is a 30-hypothesis search dressed up
    as one strategy. It is included so the multiplicity correction in `evaluate.py` has
    something real to bite on: this family will produce the best in-sample numbers in
    almost every generation and should mostly fail out-of-sample.
    """

    targets = "EDGE 1, narrowed by search — overfitting canary"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            if pos[v.leg] is not None or v.frac() < self.enter_frac:
                continue
            a = v.ask()
            if self.lo <= a <= self.hi:
                out.append(taker(v.leg, "no", self.qty))
            elif self.lo <= v.no_ask() <= self.hi:
                out.append(taker(v.leg, "yes", self.qty))
        return out


class late_favorite(Strategy):
    """`hold_favorite`, entered late — same edge, a fraction of the capital-hours.

    On `politics_long` the same 3c edge is worth ~4 turns a year at enter_frac=0 and ~40
    at enter_frac=0.9. Whether the edge survives being taken late is the question: by then
    the price has usually moved past the entry threshold.
    """

    targets = "EDGE 1, capital-efficient variant"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            if pos[v.leg] is not None or v.frac() < self.enter_frac:
                continue
            if v.ask() >= self.thresh:
                out.append(taker(v.leg, "yes", self.qty))
            elif v.no_ask() >= self.thresh:
                out.append(taker(v.leg, "no", self.qty))
        return out


# ---------------------------------------------------------------------------
# EDGE 2 — underreaction
# ---------------------------------------------------------------------------

class jump_follow(Strategy):
    """After a one-step move of at least `jump_ticks`, trade with it for `hold_steps`.

    Aimed straight at the capped lag in markets.py. The lag is capped at 1-3c depending
    on family, and a round trip at mid-book costs 3.5c, so this is a strategy that has to
    find its edge at the extremes of the book or not at all.
    """

    targets = "EDGE 2 (underreaction)"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            p = pos[v.leg]
            if p is not None:
                if v.t - p.opened_t >= self.hold_steps:
                    out.append(close(v.leg))
                continue
            if v.t < 1 or v.steps_left() < 1:
                continue
            d = v.mid() - v.mid(-1)
            if d >= self.jump_ticks:
                out.append(taker(v.leg, "yes", self.qty))
            elif d <= -self.jump_ticks:
                out.append(taker(v.leg, "no", self.qty))
        return out


class jump_fade(Strategy):
    """Trade against a one-step move. SIGN CONTROL for EDGE 2 — should lose."""

    targets = "EDGE 2 sign control — expected to LOSE"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            p = pos[v.leg]
            if p is not None:
                if v.t - p.opened_t >= self.hold_steps:
                    out.append(close(v.leg))
                continue
            if v.t < 1 or v.steps_left() < 1:
                continue
            d = v.mid() - v.mid(-1)
            if d >= self.jump_ticks:
                out.append(taker(v.leg, "no", self.qty))
            elif d <= -self.jump_ticks:
                out.append(taker(v.leg, "yes", self.qty))
        return out


class momentum(Strategy):
    """Trend over `look_k` steps rather than a single jump. Exits after `hold_steps`."""

    targets = "EDGE 2, smoothed"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            p = pos[v.leg]
            if p is not None:
                if v.t - p.opened_t >= self.hold_steps:
                    out.append(close(v.leg))
                continue
            if v.t < self.look_k or v.steps_left() < 1:
                continue
            d = v.mid() - v.mid(-self.look_k)
            if d >= self.move_ticks:
                out.append(taker(v.leg, "yes", self.qty))
            elif d <= -self.move_ticks:
                out.append(taker(v.leg, "no", self.qty))
        return out


class mean_revert(Strategy):
    """Buy the side that has moved away from its own moving average.

    Included knowing it should fail: the underlying is a martingale by construction, so
    there is no mean reversion in the true probability, and the quote noise it is really
    trading against is one to two cents against a 3.5c round trip. If this shows up
    profitable, suspect the harness before believing it.
    """

    targets = "nothing planted — expected to LOSE to fees"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            p = pos[v.leg]
            if p is not None:
                if v.t - p.opened_t >= self.hold_steps:
                    out.append(close(v.leg))
                continue
            if v.t < self.ma_k or v.steps_left() < 1:
                continue
            ma = statistics.fmean(v.hist_mid(self.ma_k))
            m = v.mid()
            if m <= ma - self.dev_ticks:
                out.append(taker(v.leg, "yes", self.qty))
            elif m >= ma + self.dev_ticks:
                out.append(taker(v.leg, "no", self.qty))
        return out


# ---------------------------------------------------------------------------
# EDGE 3 — incoherence across a mutually exclusive set
# ---------------------------------------------------------------------------

class bracket_arb(Strategy):
    """Buy every bracket when their asks sum to less than 100 minus fees.

    The only riskless trade in this project. Exactly one bracket pays 100, so buying all
    N for a total outlay under 100 is a locked profit, fully collateralised, no model risk
    and no exit. The whole question is whether the fee on N legs eats the discount, which
    is why the fee is computed per leg here before committing rather than assumed away.
    """

    requires_brackets = True
    targets = "EDGE 3 (bracket incoherence) — riskless"

    def decide(self, gv, pos):
        if any(p is not None for p in pos):
            return []
        if gv.n_legs < 2:
            return []
        asks = [v.ask() for v in gv.legs]
        total = sum(asks)
        if total >= 100 - self.min_edge:
            return []
        qty = min([self.qty] + [v.depth() for v in gv.legs])
        if qty <= 0:
            return []
        from . import fees as _f
        fee = sum(_f.taker_fee_cents(qty, a) for a in asks)
        if (100 - total) * qty <= fee + self.min_edge * qty:
            return []
        return [taker(v.leg, "yes", qty) for v in gv.legs]


class pair_arb(Strategy):
    """Buy YES and NO on the same market for under 100. STRUCTURAL CONTROL.

    Impossible on one book by identity: no_ask = 100 - yes_bid, so
    yes_ask + no_ask = 100 + (yes_ask - yes_bid) >= 100. This exists to report zero
    opportunities out of every market examined, which is a more useful statement than
    leaving the folklore unchallenged. The engine only holds one position per leg, so on
    a bracket family it takes the YES side and the count is what matters.
    """

    targets = "nothing — structurally impossible, reported as zero"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            if pos[v.leg] is not None:
                continue
            if v.ask() + v.no_ask() < 100 - self.min_edge:
                out.append(taker(v.leg, "yes", self.qty))
        return out


# ---------------------------------------------------------------------------
# EDGE 4 — spread capture
# ---------------------------------------------------------------------------

class maker_spread(Strategy):
    """Rest an order inside a wide spread, take profit `exit_ticks` later.

    TWO CAVEATS THAT MATTER MORE THAN THE RESULT:
    (a) every number this produces is downstream of `maker_benign_fill_rate` in
        config.json, which is a guess, not a measurement;
    (b) the engine holds one position per leg, so this quotes ONE side at a time — it
        leans to the cheaper side to keep collateral and fees down. A real two-sided
        maker earns the full spread per round trip instead of half, so treat this as a
        lower bound on the family rather than a fair test of it.
    """

    targets = "EDGE 4 (spread capture) — assumption-dependent"

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            p = pos[v.leg]
            if p is not None:
                gain = (v.bid() - p.cost / p.qty) if p.side == "yes" else ((100 - v.ask()) - p.cost / p.qty)
                if gain >= self.exit_ticks or v.steps_left() <= 1:
                    out.append(close(v.leg))
                continue
            if v.spread() < self.min_spread or v.steps_left() < 2:
                continue
            if v.mid() <= 50:
                out.append(maker(v.leg, "yes", self.qty, v.bid() + 1))
            else:
                out.append(maker(v.leg, "no", self.qty, v.no_bid() + 1))
        return out


# ---------------------------------------------------------------------------
# The null
# ---------------------------------------------------------------------------

class random_control(Strategy):
    """Random entries, held to settlement. MUST FAIL THE GATE.

    Carries its own RNG seeded once, so its state persists across groups within a run.
    That is deliberate: it makes the control's results reproducible without making its
    individual trades predictable from the market it is trading.
    """

    targets = "nothing — must fail the gate or the gate is broken"

    def __init__(self, **params):
        super().__init__(**params)
        self._rng = random.Random(0xC0FFEE)

    def decide(self, gv, pos):
        out = []
        for v in gv.legs:
            if pos[v.leg] is not None:
                continue
            if self._rng.random() < self.rate:
                side = "yes" if self._rng.random() < 0.5 else "no"
                out.append(taker(v.leg, side, self.qty))
        return out


# ---------------------------------------------------------------------------
# Search space
# ---------------------------------------------------------------------------

# Order size is a searched parameter, not a constant, because the fee ceiling is charged
# per ORDER: a 1-lot at 5c pays 1c of fee on 0.33c of real fee, a 3x tax that has nothing
# to do with edge. If size matters as much as fees.py predicts, the loop will find it
# without being told.
QTY = [25, 100, 250]

PARAM_GRID: dict[type, dict[str, list]] = {
    hold_favorite:   {"thresh": [65, 75, 85, 90, 95], "enter_frac": [0.0, 0.25, 0.5], "qty": QTY},
    buy_longshot:    {"max_price": [5, 10, 20, 35], "enter_frac": [0.0, 0.25], "qty": QTY},
    band_fade:       {"lo": [2, 5, 10, 20, 30], "hi": [8, 15, 25, 40], "enter_frac": [0.0, 0.3], "qty": QTY},
    late_favorite:   {"thresh": [75, 85, 92], "enter_frac": [0.6, 0.8, 0.9], "qty": QTY},
    jump_follow:     {"jump_ticks": [2, 3, 5, 8], "hold_steps": [1, 3, 6, 12], "qty": QTY},
    jump_fade:       {"jump_ticks": [2, 3, 5, 8], "hold_steps": [1, 3, 6], "qty": QTY},
    momentum:        {"look_k": [3, 6, 12], "move_ticks": [3, 5, 8], "hold_steps": [3, 6, 12], "qty": QTY},
    mean_revert:     {"ma_k": [5, 10, 20], "dev_ticks": [2, 3, 5, 8], "hold_steps": [3, 6, 12], "qty": QTY},
    bracket_arb:     {"min_edge": [0, 1, 2], "qty": QTY},
    pair_arb:        {"min_edge": [0, 1], "qty": [100]},
    maker_spread:    {"min_spread": [2, 3, 4, 6], "exit_ticks": [1, 2, 3], "qty": [25, 100]},
    random_control:  {"rate": [0.05, 0.2], "qty": [100]},
}

ALL = list(PARAM_GRID.keys())
CONTROLS = [buy_longshot, jump_fade, pair_arb, random_control, mean_revert]


def grid_size(cls) -> int:
    n = 1
    for vs in PARAM_GRID[cls].values():
        n *= len(vs)
    return n


def sample_params(cls, rng) -> dict:
    return {k: rng.choice(v) for k, v in PARAM_GRID[cls].items()}


def all_params(cls):
    keys = list(PARAM_GRID[cls].keys())

    def rec(i, acc):
        if i == len(keys):
            yield dict(acc)
            return
        for v in PARAM_GRID[cls][keys[i]]:
            acc[keys[i]] = v
            yield from rec(i + 1, acc)
    yield from rec(0, {})


def mutate(cls, params, rng) -> dict:
    """Nudge one parameter to an adjacent value in its grid. Local search around a
    survivor, rather than a fresh random draw — the point of later generations is to
    refine something that already looked plausible, not to re-roll the dice."""
    out = dict(params)
    grid = PARAM_GRID[cls]
    k = rng.choice(list(grid.keys()))
    vals = grid[k]
    try:
        i = vals.index(out[k])
    except ValueError:
        i = rng.randrange(len(vals))
    j = max(0, min(len(vals) - 1, i + rng.choice([-1, 1])))
    out[k] = vals[j]
    return out


if __name__ == "__main__":
    print(f"{len(ALL)} strategies, {len(CONTROLS)} of them controls expected to lose\n")
    print(f"{'strategy':<16} {'grid':>6} {'brackets':>9}  targets")
    print("-" * 86)
    total = 0
    for c in ALL:
        total += grid_size(c)
        print(f"{c.__name__:<16} {grid_size(c):>6} {str(c.requires_brackets):>9}  {c.targets}")
    print("-" * 86)
    print(f"{'TOTAL':<16} {total:>6} parameter points, x 9 families = {total * 9} distinct hypotheses available")
