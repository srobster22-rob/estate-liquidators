"""
The strategy zoo.

A strategy is a pure function from (market, params) to a list of *target exposures*
in [-1, +1], one per bar, with None wherever the strategy isn't ready. It does not
size, it does not stop out, it does not pay fees — risk.py sizes it and backtest.py
charges it. Keeping those separate means a mean-reversion idea and a trend idea are
compared on the same risk budget instead of one of them secretly running 3x levered.

THE CONTRACT, which the test suite enforces mechanically:

    signal[i] may depend on bars 0..i and on nothing else.

The backtester applies signal[i] to the return from bar i to bar i+1, so a strategy
that peeks at bar i+1 will look spectacular and be worthless. test_cryptobot.py
verifies causality by truncating each market at a random index and checking that
every prefix signal is bit-identical to the full-history one.

Families are deliberately spread across market behaviours — trend, reversion,
breakout, carry, cross-sectional — because the factory's whole premise is that
different market types need different strategies, and a zoo of eight trend followers
would just be one strategy with eight parameterisations.
"""

import math

from . import indicators as ind


# ------------------------------------------------------------------ param space

class FloatP:
    def __init__(self, lo, hi, log=False):
        self.lo, self.hi, self.log = lo, hi, log

    def sample(self, rng):
        if self.log:
            return math.exp(rng.uniform(math.log(self.lo), math.log(self.hi)))
        return rng.uniform(self.lo, self.hi)

    def mutate(self, rng, value, scale=0.25):
        span = (math.log(self.hi) - math.log(self.lo)) if self.log else (self.hi - self.lo)
        if self.log:
            v = math.exp(math.log(value) + rng.gauss(0, span * scale))
        else:
            v = value + rng.gauss(0, span * scale)
        return min(self.hi, max(self.lo, v))

    def perturb(self, value, frac):
        """Deterministic nudge, used by the robustness check in validate.py."""
        return min(self.hi, max(self.lo, value * (1.0 + frac)))


class IntP(FloatP):
    def sample(self, rng):
        return int(round(super().sample(rng)))

    def mutate(self, rng, value, scale=0.25):
        return int(round(super().mutate(rng, float(value), scale)))

    def perturb(self, value, frac):
        v = int(round(value * (1.0 + frac)))
        if v == value:
            v = value + (1 if frac > 0 else -1)
        return int(min(self.hi, max(self.lo, v)))


class ChoiceP:
    def __init__(self, options):
        self.options = list(options)

    def sample(self, rng):
        return rng.choice(self.options)

    def mutate(self, rng, value, scale=0.25):
        return rng.choice(self.options)

    def perturb(self, value, frac):
        return value          # categorical: nothing to nudge


class Strategy:
    def __init__(self, name, family, space, fn, kinds=("spot", "perp"),
                 needs_partner=False, tier=0):
        self.name = name
        self.family = family
        self.space = space
        self.fn = fn
        self.kinds = kinds
        self.needs_partner = needs_partner
        self.tier = tier          # 0 = available from generation 0, 1+ = unlocked
                                  # by the factory when the search stagnates

    def signal(self, market, params, partner=None):
        return self.fn(market, params, partner) if self.needs_partner \
            else self.fn(market, params)

    def sample(self, rng):
        return {k: spec.sample(rng) for k, spec in self.space.items()}


REGISTRY = {}


def register(strategy):
    REGISTRY[strategy.name] = strategy
    return strategy


def _dir(long_only, raw):
    """Clamp a raw exposure to [-1,1], and to [0,1] if the bot is long-only.

    Long-only is not a formality. Perp shorts pay borrow through funding and are the
    first thing to blow up in a squeeze; a factory that only ever finds short-biased
    bots has usually found a data artifact."""
    v = max(-1.0, min(1.0, raw))
    return max(0.0, v) if long_only else v


# ------------------------------------------------------------------- trend

def _ema_cross(market, p):
    fast = ind.ema(market, p["fast"])
    slow = ind.ema(market, p["slow"])
    out = [None] * len(market.close)
    for i in range(len(out)):
        if fast[i] is None or slow[i] is None or slow[i] == 0:
            continue
        gap = (fast[i] - slow[i]) / slow[i]
        if abs(gap) < p["deadband"]:
            out[i] = 0.0
        else:
            out[i] = _dir(p["long_only"], 1.0 if gap > 0 else -1.0)
    return out


register(Strategy("ema_cross", "trend", {
    "fast": IntP(3, 60, log=True),
    "slow": IntP(20, 400, log=True),
    "deadband": FloatP(0.0, 0.02),
    "long_only": ChoiceP([True, False]),
}, _ema_cross))


def _ts_momentum(market, p):
    r = ind.roc(market, p["lookback"])
    out = [None] * len(market.close)
    for i in range(len(out)):
        if r[i] is None:
            continue
        if abs(r[i]) < p["threshold"]:
            out[i] = 0.0
        else:
            out[i] = _dir(p["long_only"], 1.0 if r[i] > 0 else -1.0)
    return out


register(Strategy("ts_momentum", "trend", {
    "lookback": IntP(6, 500, log=True),
    "threshold": FloatP(0.0, 0.10),
    "long_only": ChoiceP([True, False]),
}, _ts_momentum))


def _macd_trend(market, p):
    fast, slow = p["fast"], max(p["fast"] + 2, p["slow"])
    _, _, hist = ind.macd(market, fast, slow, p["signal"])
    out = [None] * len(market.close)
    for i in range(len(out)):
        if hist[i] is None:
            continue
        out[i] = _dir(p["long_only"], 1.0 if hist[i] > 0 else -1.0)
    return out


register(Strategy("macd_trend", "trend", {
    "fast": IntP(5, 40),
    "slow": IntP(15, 200, log=True),
    "signal": IntP(3, 30),
    "long_only": ChoiceP([True, False]),
}, _macd_trend))


# ---------------------------------------------------------------- breakout

def _donchian(market, p):
    """Channel breakout with a separate, shorter exit channel — the Turtle shape.
    Stateful, so it is written as an explicit forward loop; state at bar i depends
    only on bars <= i."""
    entry_hi = ind.rolling_max(market, p["entry"], "high")
    entry_lo = ind.rolling_min(market, p["entry"], "low")
    exit_hi = ind.rolling_max(market, p["exit"], "high")
    exit_lo = ind.rolling_min(market, p["exit"], "low")
    c = market.close
    out = [None] * len(c)
    pos = 0.0
    warm = max(p["entry"], p["exit"])
    for i in range(len(c)):
        if i < warm or entry_hi[i] is None or exit_lo[i] is None:
            continue
        # Compare against the channel as of the PREVIOUS bar; using this bar's own
        # high in its own breakout test is the classic self-fulfilling bug.
        if entry_hi[i - 1] is not None and c[i] >= entry_hi[i - 1]:
            pos = 1.0
        elif entry_lo[i - 1] is not None and c[i] <= entry_lo[i - 1] and not p["long_only"]:
            pos = -1.0
        elif pos > 0 and exit_lo[i - 1] is not None and c[i] <= exit_lo[i - 1]:
            pos = 0.0
        elif pos < 0 and exit_hi[i - 1] is not None and c[i] >= exit_hi[i - 1]:
            pos = 0.0
        out[i] = _dir(p["long_only"], pos)
    return out


register(Strategy("donchian", "breakout", {
    "entry": IntP(10, 300, log=True),
    "exit": IntP(5, 120, log=True),
    "long_only": ChoiceP([True, False]),
}, _donchian))


def _vol_breakout(market, p):
    """Enter on a bar that moves more than k * ATR, hold for `hold` bars. Fast, and
    therefore the family most likely to be destroyed by the cost stress test — which
    is the point of having a cost stress test."""
    a = ind.atr(market, p["atr_win"])
    r = ind.simple_returns(market)
    c = market.close
    out = [None] * len(c)
    pos, left = 0.0, 0
    for i in range(len(c)):
        if a[i] is None or r[i] is None:
            continue
        if left > 0:
            left -= 1
            if left == 0:
                pos = 0.0
        if abs(r[i]) > p["k"] * a[i]:
            pos = 1.0 if r[i] > 0 else -1.0
            if p["fade"]:
                pos = -pos
            left = p["hold"]
        out[i] = _dir(p["long_only"], pos)
    return out


register(Strategy("vol_breakout", "breakout", {
    "atr_win": IntP(5, 100, log=True),
    "k": FloatP(0.5, 5.0),
    "hold": IntP(1, 48, log=True),
    "fade": ChoiceP([True, False]),
    "long_only": ChoiceP([True, False]),
}, _vol_breakout))


# --------------------------------------------------------------- reversion

def _bollinger_fade(market, p):
    z = ind.zscore(market, p["window"])
    out = [None] * len(market.close)
    pos = 0.0
    for i in range(len(out)):
        if z[i] is None:
            continue
        if pos == 0.0:
            if z[i] <= -p["entry_z"]:
                pos = 1.0
            elif z[i] >= p["entry_z"] and not p["long_only"]:
                pos = -1.0
        elif pos > 0 and z[i] >= -p["exit_z"]:
            pos = 0.0
        elif pos < 0 and z[i] <= p["exit_z"]:
            pos = 0.0
        out[i] = _dir(p["long_only"], pos)
    return out


register(Strategy("bollinger_fade", "reversion", {
    "window": IntP(10, 300, log=True),
    "entry_z": FloatP(0.8, 4.0),
    "exit_z": FloatP(-0.5, 1.5),
    "long_only": ChoiceP([True, False]),
}, _bollinger_fade))


def _rsi_reversion(market, p):
    v = ind.rsi(market, p["window"])
    out = [None] * len(market.close)
    pos = 0.0
    lo, hi = p["low"], max(p["low"] + 5.0, p["high"])
    for i in range(len(out)):
        if v[i] is None:
            continue
        if v[i] < lo:
            pos = 1.0
        elif v[i] > hi:
            pos = -1.0 if not p["long_only"] else 0.0
        elif 45.0 <= v[i] <= 55.0 and p["exit_mid"]:
            pos = 0.0
        out[i] = _dir(p["long_only"], pos)
    return out


register(Strategy("rsi_reversion", "reversion", {
    "window": IntP(4, 60, log=True),
    "low": FloatP(10.0, 45.0),
    "high": FloatP(55.0, 90.0),
    "exit_mid": ChoiceP([True, False]),
    "long_only": ChoiceP([True, False]),
}, _rsi_reversion))


def _range_position(market, p):
    """Scale into the bottom of an N-bar range and out at the top. Continuous rather
    than binary, so it holds a small position most of the time — cheap in turnover,
    which matters more than it looks once fees are real."""
    pr = ind.percent_rank(market, p["window"])
    out = [None] * len(market.close)
    for i in range(len(out)):
        if pr[i] is None:
            continue
        raw = (0.5 - pr[i]) * 2.0 * p["gain"]
        out[i] = _dir(p["long_only"], raw)
    return out


register(Strategy("range_position", "reversion", {
    "window": IntP(20, 500, log=True),
    "gain": FloatP(0.5, 3.0),
    "long_only": ChoiceP([True, False]),
}, _range_position))


def _grid(market, p):
    """Grid trading: exposure proportional to distance below a slow anchor, in
    discrete steps. Makes money in chop, dies in trends — the factory should only
    ever select it on a market where the trend filter says chop."""
    anchor = ind.sma(market, p["anchor"])
    a = ind.atr(market, p["atr_win"])
    c = market.close
    out = [None] * len(c)
    for i in range(len(c)):
        if anchor[i] is None or a[i] is None or a[i] <= 0:
            continue
        dist = (anchor[i] - c[i]) / (a[i] * c[i])
        step = max(1, int(min(abs(dist) / p["step_atr"], p["levels"])))
        raw = math.copysign(step / p["levels"], dist)
        out[i] = _dir(p["long_only"], raw)
    return out


register(Strategy("grid", "reversion", {
    "anchor": IntP(20, 400, log=True),
    "atr_win": IntP(5, 100, log=True),
    "step_atr": FloatP(0.3, 3.0),
    "levels": IntP(2, 8),
    "long_only": ChoiceP([True, False]),
}, _grid))


# ------------------------------------------------------------------- carry

def _carry_funding(market, p):
    """Harvest perpetual funding: when longs are paying a lot, be short and collect;
    when funding is deeply negative, be long. The position pays or earns funding
    every bar in the backtester, so this only survives if the collected rate beats
    the price risk of holding the wrong side — which is the actual question."""
    avg = ind.rolling_mean_of(market.funding, p["avg_win"])
    out = [None] * len(market.close)
    thresh = p["enter"] * 1e-4
    for i in range(len(out)):
        if avg[i] is None:
            continue
        if avg[i] > thresh:
            out[i] = _dir(p["long_only"], -1.0)
        elif avg[i] < -thresh:
            out[i] = _dir(p["long_only"], 1.0)
        else:
            out[i] = 0.0
    return out


register(Strategy("carry_funding", "carry", {
    "avg_win": IntP(4, 200, log=True),
    "enter": FloatP(0.05, 3.0),        # in bps per bar
    "long_only": ChoiceP([False]),
}, _carry_funding, kinds=("perp",)))


# ---------------------------------------------------------- cross-sectional

def _spread_reversion(market, p, partner):
    """Trade this market against a partner: when the log price ratio stretches, bet
    on it snapping back. Two legs means two lots of fees, and the backtester charges
    the partner leg's costs through `partner_turnover`."""
    n = min(len(market.close), len(partner.close))
    win = p["window"]
    spread = [None] * n
    for i in range(n):
        spread[i] = math.log(market.close[i] / partner.close[i])
    out = [None] * n
    run = run2 = 0.0
    pos = 0.0
    for i in range(n):
        run += spread[i]
        run2 += spread[i] ** 2
        if i >= win:
            old = spread[i - win]
            run -= old
            run2 -= old ** 2
        if i < win - 1:
            continue
        mean = run / win
        var = max(0.0, run2 / win - mean * mean) * win / (win - 1.0)
        sd = math.sqrt(var)
        if sd <= 0:
            out[i] = 0.0
            continue
        z = (spread[i] - mean) / sd
        if pos == 0.0:
            if z >= p["entry_z"]:
                pos = -1.0
            elif z <= -p["entry_z"]:
                pos = 1.0
        elif (pos > 0 and z >= -p["exit_z"]) or (pos < 0 and z <= p["exit_z"]):
            pos = 0.0
        out[i] = pos
    return out


register(Strategy("spread_reversion", "cross_sectional", {
    # The window has to be several times the spread's own half-life or the rolling
    # mean chases the deviation instead of measuring it: at a 150-bar window against
    # a 120-bar half-life a 2-sigma excursion reads as noise, and the edge vanishes
    # before costs. Hence a range that reaches 1000.
    "window": IntP(60, 1000, log=True),
    "entry_z": FloatP(1.0, 4.0),
    "exit_z": FloatP(-0.5, 1.0),
}, _spread_reversion, needs_partner=True, tier=1))


# ---------------------------------------------------------- regime-conditioned

def _filtered_reversion(market, p):
    """Fade extremes, but only when the slow trend is flat. This is the composite the
    factory tends to converge on once it has been beaten up by the regime-consistency
    gate: a pure fader makes money for two years and gives it all back in one trend."""
    z = ind.zscore(market, p["window"])
    slope_src = ind.ema(market, p["trend_win"])
    a = ind.atr(market, p["trend_win"])
    out = [None] * len(market.close)
    pos = 0.0
    for i in range(len(out)):
        if z[i] is None or a[i] is None or i < p["trend_win"] + 1:
            continue
        prev = slope_src[i - p["trend_win"]]
        if prev is None or slope_src[i] is None or prev == 0:
            continue
        trend = (slope_src[i] - prev) / prev
        trending = abs(trend) > p["trend_gate"]
        if trending:
            pos = 0.0
            if p["ride"]:
                pos = _dir(p["long_only"], 1.0 if trend > 0 else -1.0)
        else:
            if pos == 0.0:
                if z[i] <= -p["entry_z"]:
                    pos = 1.0
                elif z[i] >= p["entry_z"]:
                    pos = -1.0
            elif (pos > 0 and z[i] >= 0) or (pos < 0 and z[i] <= 0):
                pos = 0.0
        out[i] = _dir(p["long_only"], pos)
    return out


register(Strategy("filtered_reversion", "hybrid", {
    "window": IntP(10, 200, log=True),
    "entry_z": FloatP(0.8, 3.5),
    "trend_win": IntP(20, 400, log=True),
    "trend_gate": FloatP(0.005, 0.15, log=True),
    "ride": ChoiceP([True, False]),
    "long_only": ChoiceP([True, False]),
}, _filtered_reversion, tier=1))


def _vol_regime_switch(market, p):
    """Trend-follow when realised vol is high, fade when it's low (or the reverse,
    if the search prefers it). One knob, two personalities."""
    rv = ind.realized_vol(market, p["vol_win"])
    rv_med = ind.rolling_mean_of(rv, p["vol_ref"])
    z = ind.zscore(market, p["rev_win"])
    mom = ind.roc(market, p["mom_win"])
    out = [None] * len(market.close)
    for i in range(len(out)):
        if rv[i] is None or rv_med[i] is None or z[i] is None or mom[i] is None:
            continue
        hot = rv[i] > rv_med[i] * p["ratio"]
        if hot != p["invert"]:
            out[i] = _dir(p["long_only"], 1.0 if mom[i] > 0 else -1.0)
        else:
            out[i] = _dir(p["long_only"], max(-1.0, min(1.0, -z[i] / p["entry_z"])))
    return out


register(Strategy("vol_regime_switch", "hybrid", {
    "vol_win": IntP(10, 200, log=True),
    "vol_ref": IntP(50, 600, log=True),
    "rev_win": IntP(10, 200, log=True),
    "mom_win": IntP(6, 300, log=True),
    "ratio": FloatP(0.6, 1.8),
    "entry_z": FloatP(1.0, 3.0),
    "invert": ChoiceP([True, False]),
    "long_only": ChoiceP([True, False]),
}, _vol_regime_switch, tier=2))


# --------------------------------------------------------------- benchmark

def _buy_hold(market, p):
    return [1.0] * len(market.close)


BUY_HOLD = Strategy("buy_hold", "benchmark", {}, _buy_hold)
register(BUY_HOLD)


def available(tier, kind):
    """Strategies unlocked at or below `tier` that can trade this instrument kind."""
    return [s for s in REGISTRY.values()
            if s.tier <= tier and kind in s.kinds and s.family != "benchmark"]
