"""
Indicators, all O(n), all causal.

CAUSAL means: the value at index i uses bars 0..i and nothing after. Every function
here returns a list the same length as its input, with None in the warm-up region
where the window isn't full. The backtester refuses to take a position on a bar
whose signal is None, which is what keeps a 200-bar moving average from silently
trading the first 200 bars with a partial window.

Rolling max/min use a monotonic deque and rolling mean/std use prefix sums, so
adding a strategy with a 500-bar lookback costs the same as a 5-bar one. The factory
evaluates tens of thousands of bots against the same few markets; results are cached
on the Market via market.memo().
"""

import math
from collections import deque


def _memo(market, name, series_id, *args):
    return (name, series_id) + args


def returns(market):
    """Log returns, r[i] = ln(close[i]/close[i-1]); r[0] is None."""
    def build():
        c = market.close
        out = [None]
        for i in range(1, len(c)):
            out.append(math.log(c[i] / c[i - 1]))
        return out
    return market.memo(("ret",), build)


def simple_returns(market):
    def build():
        c = market.close
        out = [None]
        for i in range(1, len(c)):
            out.append(c[i] / c[i - 1] - 1.0)
        return out
    return market.memo(("sret",), build)


def sma(market, window, source="close"):
    def build():
        x = getattr(market, source)
        out = [None] * len(x)
        run = 0.0
        for i, val in enumerate(x):
            run += val
            if i >= window:
                run -= x[i - window]
            if i >= window - 1:
                out[i] = run / window
        return out
    return market.memo(("sma", window, source), build)


def ema(market, window, source="close"):
    def build():
        x = getattr(market, source)
        k = 2.0 / (window + 1.0)
        out = [None] * len(x)
        if len(x) < window:
            return out
        seed = sum(x[:window]) / window
        out[window - 1] = seed
        prev = seed
        for i in range(window, len(x)):
            prev = x[i] * k + prev * (1 - k)
            out[i] = prev
        return out
    return market.memo(("ema", window, source), build)


def rolling_std(market, window, source="close"):
    """Sample standard deviation over `window` bars, prefix-sum based. Variance is
    clamped at zero: catastrophic cancellation on a flat series can otherwise
    produce a tiny negative number and a domain error in sqrt."""
    def build():
        x = getattr(market, source)
        x = [0.0 if v is None else v for v in x]
        out = [None] * len(x)
        s = s2 = 0.0
        for i, val in enumerate(x):
            s += val
            s2 += val * val
            if i >= window:
                old = x[i - window]
                s -= old
                s2 -= old * old
            if i >= window - 1:
                mean = s / window
                var = max(0.0, s2 / window - mean * mean) * window / (window - 1.0)
                out[i] = math.sqrt(var)
        return out
    return market.memo(("std", window, source), build)


def realized_vol(market, window):
    """Stdev of log returns over `window` bars, annualised. This is the risk input
    for position sizing, so it must never see the future: vol[i] is computed from
    returns up to and including bar i, and the position it sizes earns bar i+1."""
    def build():
        r = returns(market)
        n = len(r)
        out = [None] * n
        s = s2 = 0.0
        count = 0
        buf = deque()
        scale = math.sqrt(market.bars_per_year)
        for i in range(n):
            val = r[i]
            if val is not None:
                buf.append(val)
                s += val
                s2 += val * val
                count += 1
                if count > window:
                    old = buf.popleft()
                    s -= old
                    s2 -= old * old
                    count -= 1
            if count >= window:
                mean = s / count
                var = max(0.0, s2 / count - mean * mean) * count / (count - 1.0)
                out[i] = math.sqrt(var) * scale
        return out
    return market.memo(("rvol", window), build)


def rolling_max(market, window, source="high"):
    def build():
        return _extreme(getattr(market, source), window, True)
    return market.memo(("rmax", window, source), build)


def rolling_min(market, window, source="low"):
    def build():
        return _extreme(getattr(market, source), window, False)
    return market.memo(("rmin", window, source), build)


def _extreme(x, window, want_max):
    out = [None] * len(x)
    dq = deque()                      # indices, values monotonic
    for i, val in enumerate(x):
        while dq and ((x[dq[-1]] <= val) if want_max else (x[dq[-1]] >= val)):
            dq.pop()
        dq.append(i)
        if dq[0] <= i - window:
            dq.popleft()
        if i >= window - 1:
            out[i] = x[dq[0]]
    return out


def atr(market, window):
    """Average true range, Wilder smoothing, returned as a fraction of close so it
    is comparable across a $0.30 alt and a $60,000 BTC."""
    def build():
        h, l, c = market.high, market.low, market.close
        n = len(c)
        out = [None] * n
        if n < window + 1:
            return out
        trs = [None]
        for i in range(1, n):
            trs.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
        seed = sum(trs[1:window + 1]) / window
        out[window] = seed / c[window]
        prev = seed
        for i in range(window + 1, n):
            prev = (prev * (window - 1) + trs[i]) / window
            out[i] = prev / c[i]
        return out
    return market.memo(("atr", window), build)


def rsi(market, window):
    """Wilder's RSI in 0..100."""
    def build():
        c = market.close
        n = len(c)
        out = [None] * n
        if n < window + 1:
            return out
        gains = losses = 0.0
        for i in range(1, window + 1):
            d = c[i] - c[i - 1]
            gains += max(d, 0.0)
            losses += max(-d, 0.0)
        ag, al = gains / window, losses / window
        out[window] = 100.0 - 100.0 / (1.0 + ag / al) if al > 0 else 100.0
        for i in range(window + 1, n):
            d = c[i] - c[i - 1]
            ag = (ag * (window - 1) + max(d, 0.0)) / window
            al = (al * (window - 1) + max(-d, 0.0)) / window
            out[i] = 100.0 - 100.0 / (1.0 + ag / al) if al > 0 else 100.0
        return out
    return market.memo(("rsi", window), build)


def zscore(market, window):
    """(close - SMA) / rolling stdev. The workhorse for every mean-reversion idea."""
    def build():
        c = market.close
        m = sma(market, window)
        s = rolling_std(market, window)
        out = [None] * len(c)
        for i in range(len(c)):
            if m[i] is None or s[i] is None or s[i] <= 0:
                continue
            out[i] = (c[i] - m[i]) / s[i]
        return out
    return market.memo(("z", window), build)


def roc(market, window):
    """Rate of change over `window` bars: close[i]/close[i-window] - 1."""
    def build():
        c = market.close
        out = [None] * len(c)
        for i in range(window, len(c)):
            out[i] = c[i] / c[i - window] - 1.0
        return out
    return market.memo(("roc", window), build)


def macd(market, fast, slow, signal):
    """Returns (line, signal_line, histogram)."""
    def build():
        ef, es = ema(market, fast), ema(market, slow)
        n = len(market.close)
        line = [None] * n
        for i in range(n):
            if ef[i] is not None and es[i] is not None:
                line[i] = ef[i] - es[i]
        # EMA of the line, computed inline because it has its own warm-up.
        sig = [None] * n
        k = 2.0 / (signal + 1.0)
        vals = [(i, v) for i, v in enumerate(line) if v is not None]
        if len(vals) >= signal:
            seed_idx = vals[signal - 1][0]
            prev = sum(v for _, v in vals[:signal]) / signal
            sig[seed_idx] = prev
            for i, v in vals[signal:]:
                prev = v * k + prev * (1 - k)
                sig[i] = prev
        hist = [None] * n
        for i in range(n):
            if line[i] is not None and sig[i] is not None:
                hist[i] = line[i] - sig[i]
        return line, sig, hist
    return market.memo(("macd", fast, slow, signal), build)


def percent_rank(market, window):
    """Where the current close sits in its own `window`-bar range, 0..1. Cheap
    regime proxy: near 1 in an uptrend, near 0.5 in chop."""
    def build():
        hi = rolling_max(market, window, "close")
        lo = rolling_min(market, window, "close")
        c = market.close
        out = [None] * len(c)
        for i in range(len(c)):
            if hi[i] is None or lo[i] is None or hi[i] <= lo[i]:
                continue
            out[i] = (c[i] - lo[i]) / (hi[i] - lo[i])
        return out
    return market.memo(("prank", window), build)


def rolling_mean_of(series, window):
    """Rolling mean of an arbitrary list-with-Nones (funding rates, mostly)."""
    out = [None] * len(series)
    buf = deque()
    run = 0.0
    for i, v in enumerate(series):
        if v is None:
            continue
        buf.append(v)
        run += v
        if len(buf) > window:
            run -= buf.popleft()
        if len(buf) == window:
            out[i] = run / window
    return out
