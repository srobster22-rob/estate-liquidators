"""
The engine: sizing, costs, funding, stops, and the metrics everything else judges on.

Timing convention, stated once and obeyed everywhere:

    signal[i]  is decided at the close of bar i, from bars 0..i
    position   is established at the close of bar i, paying costs
    it earns   the return from close[i] to close[i+1]

So the last bar's signal never trades and the first bar's return is never earned.
`lag` shifts execution further into the future (lag=1 means the decision made at
close[i] is only filled at close[i+1]); the validator runs every candidate at lag=0
and lag=1 and throws away anything that only works at zero latency, because a bot
that needs instant fills is a bot that needs an execution stack it doesn't have.

COSTS are charged on turnover, three ways:

    fee     taker fee, one side, in bps of traded notional
    spread  half-spread crossed, in bps
    impact  quadratic in turnover — doubling size costs four times as much slippage

The quadratic term is what stops the optimiser from discovering that a bot flipping
its whole book every bar is free money. It is a crude model of a real constraint,
and it is deliberately set pessimistic rather than realistic.

FUNDING is charged every bar a perp position is open: a long pays the rate, a short
receives it. That single line is why carry strategies in this repo are not free money.

RUIN is absolute. If equity hits zero the run is over and every downstream metric
reports the wipeout rather than the strategy's average behaviour.
"""

import math
from collections import deque

from . import indicators as ind


class Result:
    """Everything the validator needs, and nothing it has to recompute."""

    __slots__ = ("net", "equity", "position", "market_key", "bars_per_year",
                 "metrics", "ruined")

    def __init__(self, net, equity, position, market_key, bars_per_year, ruined):
        self.net = net                    # per-bar net return, length n-1
        self.equity = equity              # equity curve, length n
        self.position = position          # realised exposure per bar
        self.market_key = market_key
        self.bars_per_year = bars_per_year
        self.ruined = ruined
        self.metrics = compute_metrics(net, equity, position, bars_per_year, ruined)

    def __getitem__(self, k):
        return self.metrics[k]


DEFAULT_RISK = {
    "vol_target": 0.40,      # annualised vol the sizer aims at
    "vol_win": 72,           # bars of trailing vol used to size
    "max_leverage": 2.0,
    "stop_atr": 0.0,         # 0 disables; otherwise stop distance in ATR multiples
    "stop_atr_win": 24,
}


def hedged_returns(market, hedge, beta=1.0):
    """Per-bar return of a long-market / short-hedge pair.

        r(t) = r_market(t) - beta * r_hedge(t)

    Without this, a "pairs" bot is not a pairs bot. The engine computes the P&L of
    the market it is handed, so a spread strategy run single-leg is really a
    directional bet on one leg that happens to be timed by the spread — and, because
    the cost model already bills both legs, it pays for a hedge it never held. That
    was the bug that made every cointegrated market in the universe look untradeable
    while the spread sitting in it was worth 200bps a round trip."""
    rm = ind.simple_returns(market)
    rh = ind.simple_returns(hedge)
    n = min(len(rm), len(rh))
    out = [None] * n
    for i in range(1, n):
        if rm[i] is None or rh[i] is None:
            continue
        out[i] = rm[i] - beta * rh[i]
    return out


def _trailing_vol(returns, window, bars_per_year):
    """Annualised trailing stdev of an arbitrary return series, causal, O(n).

    Pairs need their own sizing input: the spread's volatility is a fraction of
    either leg's, so sizing a spread trade off one leg's vol produces a position
    small enough that the edge disappears under fees."""
    n = len(returns)
    out = [None] * n
    scale = math.sqrt(bars_per_year)
    buf = deque()
    s = s2 = 0.0
    for i in range(n):
        v = returns[i]
        if v is not None:
            buf.append(v)
            s += v
            s2 += v * v
            if len(buf) > window:
                old = buf.popleft()
                s -= old
                s2 -= old * old
        if len(buf) >= window:
            m = s / len(buf)
            var = max(0.0, s2 / len(buf) - m * m) * len(buf) / (len(buf) - 1.0)
            out[i] = math.sqrt(var) * scale
    return out


def size_positions(market, signal, risk, vol_series=None):
    """Turn target exposures into leverage, scaled so that a quiet market and a wild
    one carry the same risk budget.

        leverage = signal * vol_target / trailing_realised_vol   (capped)

    Trailing vol at bar i uses returns up to bar i, so the sizing of the position
    that earns bar i+1 knows nothing about bar i+1. Without vol targeting the
    optimiser reliably 'discovers' that leverage is alpha.

    `vol_series` overrides the market's own volatility, which pairs trades need:
    their risk is the spread's, not either leg's."""
    rv = vol_series if vol_series is not None else ind.realized_vol(
        market, risk["vol_win"])
    cap = risk["max_leverage"]
    out = [0.0] * len(signal)
    for i, s in enumerate(signal):
        if s is None:
            continue
        v = rv[i]
        if v is None or v <= 1e-9:
            continue
        lev = s * (risk["vol_target"] / v)
        out[i] = max(-cap, min(cap, lev))
    return out


def run(market, signal, risk=None, lag=0, cost_mult=1.0, partner_turnover=0.0,
        hedge=None, hedge_beta=1.0):
    """Backtest one signal on one market. Returns a Result.

    `cost_mult` scales every cost — the validator reruns survivors at 2x and 3x to
    see whether the edge is real or is living inside the fee assumption.
    `partner_turnover` bills the second leg of a pairs trade.

    `hedge` makes it an actual pairs trade: the position earns the market's return
    MINUS `hedge_beta` times the hedge's, is sized off the spread's volatility
    rather than either leg's, and pays fees on both legs. Stops are disabled in this
    mode — a stop is a price level, and a spread does not have one."""
    risk = dict(DEFAULT_RISK, **(risk or {}))
    n = len(market.close)
    if n < 10:
        raise ValueError("need at least 10 bars")

    if hedge is not None:
        n = min(n, len(hedge.close))
        spread_ret = hedged_returns(market, hedge, hedge_beta)
        vol_series = _trailing_vol(spread_ret, risk["vol_win"],
                                   market.bars_per_year)
        sret = spread_ret
        risk = dict(risk, stop_atr=0.0)
    else:
        vol_series = None
        sret = ind.simple_returns(market)

    sized = size_positions(market, signal, risk, vol_series)[:n]
    if lag:
        sized = [0.0] * lag + sized[:-lag] if lag < n else [0.0] * n
    a = ind.atr(market, risk["stop_atr_win"]) if risk["stop_atr"] else None
    fee = market.fee_bps + market.spread_bps
    impact = market.impact_bps
    leg_mult = 1.0 + partner_turnover

    equity = [1.0]
    net = []
    realised = [0.0] * n
    pos_prev = 0.0
    entry_px = None
    blocked_dir = 0          # after a stop, ignore same-side signals until it flips
    ruined = False

    for i in range(n - 1):
        tgt = sized[i]
        if blocked_dir:
            if tgt == 0.0 or (tgt > 0) != (blocked_dir > 0):
                blocked_dir = 0
            else:
                tgt = 0.0

        turnover = abs(tgt - pos_prev)
        cost = (turnover * fee / 1e4 + impact * turnover * turnover / 1e4) \
            * cost_mult * leg_mult

        if tgt != 0.0 and (pos_prev == 0.0 or (tgt > 0) != (pos_prev > 0)):
            entry_px = market.close[i]

        r = sret[i + 1]
        stopped = False
        if risk["stop_atr"] and tgt != 0.0 and entry_px and a and a[i] is not None:
            dist = risk["stop_atr"] * a[i]
            if tgt > 0:
                stop_px = entry_px * (1.0 - dist)
                if market.low[i + 1] <= stop_px:
                    # A gap through the stop fills at the open, not at the stop.
                    fill = min(stop_px, market.open[i + 1])
                    r = fill / market.close[i] - 1.0
                    stopped = True
            else:
                stop_px = entry_px * (1.0 + dist)
                if market.high[i + 1] >= stop_px:
                    fill = max(stop_px, market.open[i + 1])
                    r = fill / market.close[i] - 1.0
                    stopped = True

        funding_cost = tgt * market.funding[i + 1] if market.kind == "perp" else 0.0
        if hedge is not None and hedge.kind == "perp":
            # Short the hedge, so its funding flows the other way.
            funding_cost -= tgt * hedge_beta * hedge.funding[i + 1]
        bar = tgt * r - cost - funding_cost

        if stopped:
            bar -= abs(tgt) * fee / 1e4 * cost_mult * leg_mult   # exit fill
            blocked_dir = 1 if tgt > 0 else -1

        eq = equity[-1] * (1.0 + bar)
        if eq <= 1e-9:
            ruined = True
            net.append(-1.0)
            equity.append(0.0)
            realised[i] = tgt
            for _ in range(i + 1, n - 1):
                net.append(0.0)
                equity.append(0.0)
            break

        net.append(bar)
        equity.append(eq)
        realised[i] = tgt
        pos_prev = 0.0 if stopped else tgt

    return Result(net, equity, realised, market.key, market.bars_per_year, ruined)


# ------------------------------------------------------------------- metrics

def compute_metrics(net, equity, position, bars_per_year, ruined=False):
    n = len(net)
    if n < 2:
        return _empty_metrics()

    mean = sum(net) / n
    var = sum((x - mean) ** 2 for x in net) / (n - 1)
    sd = math.sqrt(var)
    downside = [x for x in net if x < 0]
    dvar = sum(x * x for x in downside) / n if downside else 0.0
    dsd = math.sqrt(dvar)

    ann = math.sqrt(bars_per_year)
    sharpe = (mean / sd) * ann if sd > 1e-12 else 0.0
    sortino = (mean / dsd) * ann if dsd > 1e-12 else 0.0

    years = n / bars_per_year
    final = equity[-1]
    cagr = (final ** (1.0 / years) - 1.0) if final > 0 and years > 0 else -1.0

    peak, max_dd, dd_len, cur_len = equity[0], 0.0, 0, 0
    for e in equity:
        if e > peak:
            peak = e
            cur_len = 0
        else:
            cur_len += 1
            dd_len = max(dd_len, cur_len)
        if peak > 0:
            max_dd = max(max_dd, 1.0 - e / peak)

    gains = sum(x for x in net if x > 0)
    losses = -sum(x for x in net if x < 0)
    pf = gains / losses if losses > 1e-12 else (float("inf") if gains > 0 else 0.0)

    active = [i for i in range(n) if position[i] != 0.0]
    hits = sum(1 for i in active if net[i] > 0)
    trades = 0
    for i in range(1, len(position)):
        a, b = position[i - 1], position[i]
        if (a == 0.0) != (b == 0.0) or (a * b < 0):
            trades += 1
    turnover = sum(abs(position[i] - position[i - 1])
                   for i in range(1, len(position)))

    # Third and fourth moments: the deflated Sharpe ratio needs them, and a strategy
    # that is short volatility shows up here long before it shows up in the equity.
    skew = kurt = 0.0
    if sd > 1e-12:
        skew = sum((x - mean) ** 3 for x in net) / (n * sd ** 3)
        kurt = sum((x - mean) ** 4 for x in net) / (n * sd ** 4)

    return {
        "bars": n,
        "years": years,
        "total_return": final - 1.0,
        "cagr": cagr,
        "ann_vol": sd * ann,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_dd": max_dd,
        "dd_bars": dd_len,
        "calmar": (cagr / max_dd) if max_dd > 1e-6 else 0.0,
        "profit_factor": pf,
        "hit_rate": hits / len(active) if active else 0.0,
        "exposure": len(active) / n,
        "trades": trades,
        "trades_per_year": trades / years if years > 0 else 0.0,
        "turnover_per_year": turnover / years if years > 0 else 0.0,
        "skew": skew,
        "kurtosis": kurt,
        "ruined": ruined,
    }


def _empty_metrics():
    return {"bars": 0, "years": 0.0, "total_return": -1.0, "cagr": -1.0,
            "ann_vol": 0.0, "sharpe": 0.0, "sortino": 0.0, "max_dd": 1.0,
            "dd_bars": 0, "calmar": 0.0, "profit_factor": 0.0, "hit_rate": 0.0,
            "exposure": 0.0, "trades": 0, "trades_per_year": 0.0,
            "turnover_per_year": 0.0, "skew": 0.0, "kurtosis": 0.0,
            "ruined": True}


def buy_hold(market):
    """Benchmark. Every result in this repo is quoted against it, because 'made
    money' is not an achievement in a market that tripled — beating the coin you
    were trading is."""
    from .strategies import BUY_HOLD
    return run(market, BUY_HOLD.signal(market, {}),
               risk=dict(DEFAULT_RISK, vol_target=1e9, max_leverage=1.0))
