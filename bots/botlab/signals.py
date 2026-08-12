"""Signal primitives — the alphabet the bot factory writes with.

Every primitive is a pure function of a `Series` and its parameters, returns a
score array roughly in [-1, +1] where positive means "be long", and is
**strictly trailing**: the value at bar t uses only bars <= t. Warmup bars are
NaN and the engine refuses to trade them. `tests/test_botlab.py` enforces the
no-lookahead property mechanically by scrambling the future and checking that
past scores do not move — do not add a primitive without that test passing.

Parameter specs drive random sampling *and* mutation, so adding a primitive
here is all it takes to widen the search space:

    ("log", lo, hi)   integer lookback, sampled log-uniformly
    ("int", lo, hi)   integer, uniform
    ("float", lo, hi) float, uniform
    ("choice", [..])  categorical
    ("bits", "period") bitmask whose width is the value of another parameter
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np

from .markets.series import Series

EPS = 1e-12


# --------------------------------------------------------------------------- #
# rolling primitives
# --------------------------------------------------------------------------- #

def _win(x: np.ndarray, n: int) -> np.ndarray:
    """Trailing windows: row t holds x[t-n+1 .. t]. Rows < n-1 are absent, so
    callers left-pad with NaN."""
    return np.lib.stride_tricks.sliding_window_view(x, n)


def sma(x: np.ndarray, n: int) -> np.ndarray:
    n = max(int(n), 1)
    out = np.full(x.size, np.nan)
    if x.size < n:
        return out
    cs = np.concatenate(([0.0], np.cumsum(x)))
    out[n - 1:] = (cs[n:] - cs[:-n]) / n
    return out


def ema(x: np.ndarray, span: int) -> np.ndarray:
    span = max(int(span), 1)
    alpha = 2.0 / (span + 1.0)
    out = np.empty(x.size)
    acc = x[0]
    for i in range(x.size):
        acc += alpha * (x[i] - acc)
        out[i] = acc
    out[: span - 1] = np.nan
    return out


def rstd(x: np.ndarray, n: int) -> np.ndarray:
    n = max(int(n), 2)
    out = np.full(x.size, np.nan)
    if x.size < n:
        return out
    out[n - 1:] = _win(x, n).std(axis=1, ddof=1)
    return out


def rmax(x: np.ndarray, n: int) -> np.ndarray:
    n = max(int(n), 1)
    out = np.full(x.size, np.nan)
    if x.size < n:
        return out
    out[n - 1:] = _win(x, n).max(axis=1)
    return out


def rmin(x: np.ndarray, n: int) -> np.ndarray:
    n = max(int(n), 1)
    out = np.full(x.size, np.nan)
    if x.size < n:
        return out
    out[n - 1:] = _win(x, n).min(axis=1)
    return out


def shift(x: np.ndarray, k: int = 1) -> np.ndarray:
    out = np.full(x.size, np.nan)
    if k <= 0:
        return x.copy()
    if k < x.size:
        out[k:] = x[:-k]
    return out


def log_returns(s: Series) -> np.ndarray:
    lr = np.zeros(s.close.size)
    lr[1:] = np.log(s.close[1:] / s.close[:-1])
    return lr


def true_range(s: Series) -> np.ndarray:
    pc = shift(s.close, 1)
    pc[0] = s.close[0]
    return np.maximum.reduce([s.high - s.low, np.abs(s.high - pc), np.abs(s.low - pc)])


def atr(s: Series, n: int) -> np.ndarray:
    return sma(true_range(s), n)


def rsi(x: np.ndarray, n: int) -> np.ndarray:
    n = max(int(n), 2)
    d = np.zeros(x.size)
    d[1:] = np.diff(x)
    gain = sma(np.maximum(d, 0.0), n)
    loss = sma(np.maximum(-d, 0.0), n)
    rs = gain / (loss + EPS)
    return 100.0 - 100.0 / (1.0 + rs)


def zscore(x: np.ndarray, n: int) -> np.ndarray:
    return (x - sma(x, n)) / (rstd(x, n) + EPS)


def pct_in_window(x: np.ndarray, n: int) -> np.ndarray:
    """Fraction of the trailing n-window that x[t] exceeds, in [0,1]."""
    n = max(int(n), 2)
    out = np.full(x.size, np.nan)
    if x.size < n:
        return out
    w = _win(x, n)
    out[n - 1:] = (w < x[n - 1:, None]).mean(axis=1)
    return out


def bar_phase(n: int, period: int) -> np.ndarray:
    return np.arange(n) % max(int(period), 2)


def _tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(np.nan_to_num(x, nan=np.nan, posinf=6.0, neginf=-6.0))


def _bar_vol(s: Series, n: int) -> np.ndarray:
    return rstd(log_returns(s), max(int(n), 5))


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class SignalDef:
    name: str
    tier: int
    params: dict
    fn: Callable[[Series, dict], np.ndarray]
    warmup: Callable[[dict], int]
    family: str = "other"


SIGNALS: dict[str, SignalDef] = {}


def _register(name: str, tier: int, params: dict, warmup, family: str = "other"):
    def deco(fn):
        SIGNALS[name] = SignalDef(name, tier, params, fn, warmup, family)
        return fn
    return deco


# ---- tier 1: the workhorses ------------------------------------------------

@_register("ma_cross", 1, {"fast": ("log", 2, 60), "slow": ("log", 10, 250)},
           lambda p: int(p["slow"]) + 5, "trend")
def _ma_cross(s: Series, p: dict) -> np.ndarray:
    fast, slow = int(p["fast"]), int(p["slow"])
    if fast >= slow:
        fast, slow = max(2, slow // 3), slow
    d = ema(s.close, fast) - ema(s.close, slow)
    return _tanh(d / (rstd(s.close, slow) + EPS))


@_register("momentum", 1, {"lb": ("log", 3, 250)}, lambda p: int(p["lb"]) + 25, "trend")
def _momentum(s: Series, p: dict) -> np.ndarray:
    lb = int(p["lb"])
    c = s.close
    past = shift(c, lb)
    r = np.log(c / past)
    scale = _bar_vol(s, max(lb, 25)) * np.sqrt(lb)
    return _tanh(r / (scale + EPS))


@_register("zrev", 1, {"lb": ("log", 3, 60)}, lambda p: int(p["lb"]) + 5, "reversion")
def _zrev(s: Series, p: dict) -> np.ndarray:
    return -_tanh(zscore(s.close, int(p["lb"])))


@_register("breakout", 1, {"n": ("log", 5, 120)}, lambda p: int(p["n"]) + 5, "trend")
def _breakout(s: Series, p: dict) -> np.ndarray:
    n = int(p["n"])
    hi = shift(rmax(s.high, n), 1)
    lo = shift(rmin(s.low, n), 1)
    mid = 0.5 * (hi + lo)
    span = np.maximum(hi - lo, EPS)
    return np.clip(2.0 * (s.close - mid) / span, -1.5, 1.5)


@_register("rsi_rev", 1, {"n": ("log", 3, 40)}, lambda p: int(p["n"]) + 5, "reversion")
def _rsi_rev(s: Series, p: dict) -> np.ndarray:
    return (50.0 - rsi(s.close, int(p["n"]))) / 50.0


@_register("bollinger", 1, {"n": ("log", 8, 120), "k": ("float", 1.0, 3.0)},
           lambda p: int(p["n"]) + 5, "reversion")
def _bollinger(s: Series, p: dict) -> np.ndarray:
    z = zscore(s.close, int(p["n"]))
    return np.clip(-z / float(p["k"]), -1.5, 1.5)


@_register("long_bias", 1, {}, lambda p: 2, "beta")
def _long_bias(s: Series, p: dict) -> np.ndarray:
    """Constant long. Present so buy-and-hold competes in the same ledger as
    everything else — and gets judged by the same alpha gate."""
    return np.ones(s.close.size)


@_register("carry", 1, {}, lambda p: 2, "carry")
def _carry(s: Series, p: dict) -> np.ndarray:
    """Sign of the market's roll/funding yield. Static by construction: a carry
    trade is a position, not a forecast."""
    c = float(getattr(s.spec, "carry_ann", 0.0))
    if abs(c) < 1e-9:
        return np.zeros(s.close.size)
    return np.full(s.close.size, 1.0 if c > 0 else -1.0)


# ---- tier 2: shape and timing ---------------------------------------------

@_register("macd", 2, {"fast": ("log", 3, 30), "slow": ("log", 10, 120), "sig": ("log", 3, 40)},
           lambda p: int(p["slow"]) + int(p["sig"]) + 5, "trend")
def _macd(s: Series, p: dict) -> np.ndarray:
    fast, slow = int(p["fast"]), int(p["slow"])
    if fast >= slow:
        fast = max(2, slow // 3)
    line = ema(s.close, fast) - ema(s.close, slow)
    hist = line - ema(np.nan_to_num(line), int(p["sig"]))
    return _tanh(hist / (rstd(s.close, slow) * 0.4 + EPS))


@_register("stoch", 2, {"n": ("log", 5, 80)}, lambda p: int(p["n"]) + 5, "reversion")
def _stoch(s: Series, p: dict) -> np.ndarray:
    n = int(p["n"])
    hi, lo = rmax(s.high, n), rmin(s.low, n)
    return np.clip(2.0 * (s.close - lo) / (hi - lo + EPS) - 1.0, -1.0, 1.0)


@_register("accel", 2, {"n": ("log", 3, 60)}, lambda p: 3 * int(p["n"]) + 25, "trend")
def _accel(s: Series, p: dict) -> np.ndarray:
    n = int(p["n"])
    c = s.close
    r1 = np.log(c / shift(c, n))
    r2 = np.log(shift(c, n) / shift(c, 2 * n))
    scale = _bar_vol(s, max(2 * n, 25)) * np.sqrt(n)
    return _tanh((r1 - r2) / (scale + EPS))


@_register("vol_thrust", 2, {"ns": ("log", 3, 30), "nl": ("log", 20, 250)},
           lambda p: int(p["nl"]) + 5, "vol")
def _vol_thrust(s: Series, p: dict) -> np.ndarray:
    ns, nl = int(p["ns"]), int(p["nl"])
    if ns >= nl:
        ns = max(3, nl // 4)
    vs, vl = _bar_vol(s, ns), _bar_vol(s, nl)
    mom = _tanh(np.log(s.close / shift(s.close, ns)) / (vl * np.sqrt(ns) + EPS))
    return mom * np.clip(vs / (vl + EPS), 0.0, 2.0)


@_register("seasonal", 2, {"period": ("choice", [5, 7, 21, 26, 24]), "bits": ("bits", "period")},
           lambda p: 5, "calendar")
def _seasonal(s: Series, p: dict) -> np.ndarray:
    period = int(p["period"])
    bits = int(p["bits"])
    phase = bar_phase(s.close.size, period)
    on = np.array([(bits >> k) & 1 for k in range(period)], dtype=float) * 2.0 - 1.0
    return on[phase]


@_register("gap_rev", 2, {"n": ("log", 10, 120)}, lambda p: int(p["n"]) + 5, "reversion")
def _gap_rev(s: Series, p: dict) -> np.ndarray:
    pc = shift(s.close, 1)
    gap = np.zeros(s.close.size)
    gap[1:] = np.log(s.open[1:] / pc[1:])
    return -_tanh(gap / (rstd(gap, int(p["n"])) + EPS))


@_register("dd_dip", 2, {"n": ("log", 10, 250), "depth": ("float", 0.5, 4.0)},
           lambda p: int(p["n"]) + 25, "reversion")
def _dd_dip(s: Series, p: dict) -> np.ndarray:
    n = int(p["n"])
    peak = rmax(s.close, n)
    a = atr(s, 20)
    dd = (peak - s.close) / (a + EPS)
    return np.clip((dd - float(p["depth"])) / 2.0, -1.0, 1.0)


# ---- tier 3: adaptive and exotic ------------------------------------------

@_register("slope", 3, {"n": ("log", 5, 150)}, lambda p: int(p["n"]) + 25, "trend")
def _slope(s: Series, p: dict) -> np.ndarray:
    n = max(int(p["n"]), 3)
    y = np.log(s.close)
    out = np.full(y.size, np.nan)
    if y.size < n:
        return out
    t = np.arange(n) - (n - 1) / 2.0
    denom = float((t * t).sum())
    out[n - 1:] = (_win(y, n) * t).sum(axis=1) / denom
    return _tanh(out / (_bar_vol(s, max(n, 25)) + EPS))


@_register("autocorr_adapt", 3, {"nac": ("log", 30, 250), "nm": ("log", 3, 60)},
           lambda p: int(p["nac"]) + int(p["nm"]) + 25, "adaptive")
def _autocorr_adapt(s: Series, p: dict) -> np.ndarray:
    """Trade momentum while returns autocorrelate positively, reversion while
    they do not. The one primitive that changes its own mind."""
    nac, nm = int(p["nac"]), int(p["nm"])
    lr = log_returns(s)
    prev = shift(lr, 1)
    prod = lr * prev
    ac = sma(np.nan_to_num(prod), nac) / (rstd(lr, nac) ** 2 + EPS)
    mom = _tanh(np.log(s.close / shift(s.close, nm)) / (_bar_vol(s, max(nm, 25)) * np.sqrt(nm) + EPS))
    return mom * np.clip(ac * 8.0, -1.0, 1.0)


@_register("compress_break", 3, {"ns": ("log", 3, 30), "nl": ("log", 20, 250)},
           lambda p: int(p["nl"]) + 25, "vol")
def _compress_break(s: Series, p: dict) -> np.ndarray:
    ns, nl = int(p["ns"]), int(p["nl"])
    if ns >= nl:
        ns = max(3, nl // 4)
    ratio = _bar_vol(s, ns) / (_bar_vol(s, nl) + EPS)
    squeeze = np.clip(1.4 - ratio, 0.0, 1.0)
    mom = _tanh(np.log(s.close / shift(s.close, ns)) / (_bar_vol(s, nl) * np.sqrt(ns) + EPS))
    return mom * squeeze


@_register("volume_thrust", 3, {"n": ("log", 10, 120)}, lambda p: int(p["n"]) + 25, "volume")
def _volume_thrust(s: Series, p: dict) -> np.ndarray:
    n = int(p["n"])
    if not np.any(s.volume > 0):
        return np.zeros(s.close.size)
    vz = s.volume / (sma(s.volume, n) + EPS)
    mom = _tanh(np.log(s.close / shift(s.close, 3)) / (_bar_vol(s, 25) * np.sqrt(3) + EPS))
    return mom * np.clip(vz - 0.5, 0.0, 2.0) * 0.7


@_register("skew_rev", 3, {"n": ("log", 20, 150)}, lambda p: int(p["n"]) + 5, "reversion")
def _skew_rev(s: Series, p: dict) -> np.ndarray:
    n = max(int(p["n"]), 20)
    lr = log_returns(s)
    out = np.full(lr.size, np.nan)
    if lr.size < n:
        return out
    w = _win(lr, n)
    mu = w.mean(axis=1, keepdims=True)
    sd = w.std(axis=1, ddof=1, keepdims=True) + EPS
    out[n - 1:] = (((w - mu) / sd) ** 3).mean(axis=1)
    return -_tanh(out * 1.5)


@_register("range_pos_multi", 3, {"n1": ("log", 5, 40), "n2": ("log", 40, 250)},
           lambda p: int(p["n2"]) + 5, "trend")
def _range_pos_multi(s: Series, p: dict) -> np.ndarray:
    n1, n2 = int(p["n1"]), int(p["n2"])
    a = pct_in_window(s.close, max(n1, 3)) * 2.0 - 1.0
    b = pct_in_window(s.close, max(n2, 10)) * 2.0 - 1.0
    return 0.5 * (a + b)


# --------------------------------------------------------------------------- #
# filters: gates (0/1 on exposure) and direction masks
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class FilterDef:
    name: str
    tier: int
    kind: str                      # "gate" | "dir"
    params: dict
    fn: Callable[[Series, dict], np.ndarray]
    warmup: Callable[[dict], int]


FILTERS: dict[str, FilterDef] = {}


def _register_filter(name: str, tier: int, kind: str, params: dict, warmup):
    def deco(fn):
        FILTERS[name] = FilterDef(name, tier, kind, params, fn, warmup)
        return fn
    return deco


@_register_filter("trend_regime", 1, "dir", {"n": ("log", 20, 250)}, lambda p: int(p["n"]) + 5)
def _trend_regime(s: Series, p: dict) -> np.ndarray:
    """Allowed side: only long above the long average, only short below it."""
    d = s.close - sma(s.close, int(p["n"]))
    return np.where(np.isnan(d), 0.0, np.sign(d))


@_register_filter("vol_band", 1, "gate", {"n": ("log", 10, 60), "lo": ("float", 0.0, 0.5),
                                          "hi": ("float", 0.5, 1.0)}, lambda p: 260)
def _vol_band(s: Series, p: dict) -> np.ndarray:
    v = _bar_vol(s, int(p["n"]))
    r = pct_in_window(np.nan_to_num(v), 250)
    lo, hi = float(p["lo"]), float(p["hi"])
    if lo > hi:
        lo, hi = hi, lo
    return ((r >= lo) & (r <= hi)).astype(float)


@_register_filter("session", 2, "gate", {"period": ("choice", [5, 7, 21, 26, 24]),
                                         "bits": ("bits", "period")}, lambda p: 2)
def _session(s: Series, p: dict) -> np.ndarray:
    period, bits = int(p["period"]), int(p["bits"])
    phase = bar_phase(s.close.size, period)
    on = np.array([(bits >> k) & 1 for k in range(period)], dtype=float)
    return on[phase]


@_register_filter("trend_strength", 2, "gate", {"nf": ("log", 5, 40), "ns": ("log", 40, 250),
                                                "thr": ("float", 0.0, 1.5)},
                  lambda p: int(p["ns"]) + 25)
def _trend_strength(s: Series, p: dict) -> np.ndarray:
    nf, ns = int(p["nf"]), int(p["ns"])
    spread = np.abs(sma(s.close, nf) - sma(s.close, ns)) / (atr(s, 20) + EPS)
    return (spread >= float(p["thr"])).astype(float)


@_register_filter("near_high", 3, "gate", {"n": ("log", 20, 250), "x": ("float", 0.5, 8.0)},
                  lambda p: int(p["n"]) + 25)
def _near_high(s: Series, p: dict) -> np.ndarray:
    peak = rmax(s.close, int(p["n"]))
    return ((peak - s.close) / (atr(s, 20) + EPS) <= float(p["x"])).astype(float)


def signal_names(tier: int = 3) -> list[str]:
    return [n for n, d in SIGNALS.items() if d.tier <= tier]


def filter_names(tier: int = 3) -> list[str]:
    return [n for n, d in FILTERS.items() if d.tier <= tier]


# ---- tier 4: added when the level 1-3 ladder was exhausted ------------------
#
# The catalogue contains structure the original 21 primitives could not reach
# efficiently. These three target it directly. They are a widening of the
# hypothesis space, not a weakening of any gate: every one still has to survive
# the same seven-gate ladder, and each extra candidate they generate raises G6's
# luck bar for everything that follows.

@_register("seasonal_profile", 4, {"period": ("choice", [5, 7, 21, 24, 26]),
                                   "cycles": ("log", 4, 40)},
           lambda p: int(p["period"]) * (int(p["cycles"]) + 1) + 5, "calendar")
def _seasonal_profile(s: Series, p: dict) -> np.ndarray:
    """Trailing mean return of the current calendar phase.

    The existing `seasonal` primitive encodes the active phases as a bitmask, so
    finding a 21-bar commodity calendar effect means drawing the right pattern
    out of 2^21. This one *estimates* the profile instead: for each phase, the
    mean return of its last `cycles` occurrences, all strictly earlier bars. The
    planted effects in `commodity_meanrev_daily` (21-bar sine) and
    `eq_intraday_15m` (26-bar session shape) are reachable this way.
    """
    period = max(int(p["period"]), 2)
    k = max(int(p["cycles"]), 2)
    lr = log_returns(s)
    n = lr.size
    out = np.full(n, np.nan)
    for ph in range(period):
        idx = np.arange(ph, n, period)
        if idx.size <= k:
            continue
        vals = lr[idx]
        cs = np.concatenate(([0.0], np.cumsum(vals)))
        m = np.full(idx.size, np.nan)
        # m[j] averages vals[j-k : j] — occurrences strictly before bar idx[j].
        m[k:] = (cs[k:idx.size] - cs[0:idx.size - k]) / k
        out[idx] = m
    scale = _bar_vol(s, 60) / math.sqrt(max(k, 1))
    return _tanh(out / (scale + EPS))


@_register("efficiency_ratio", 4, {"n": ("log", 8, 150)}, lambda p: int(p["n"]) + 5, "trend")
def _efficiency_ratio(s: Series, p: dict) -> np.ndarray:
    """Kaufman efficiency ratio, signed: |net move| / |path travelled|, times the
    direction of the net move. Trades trend only when the trend is *clean*, which
    is a different question from whether a moving average has crossed."""
    n = max(int(p["n"]), 3)
    c = s.close
    net = c - shift(c, n)
    step = np.zeros(c.size)
    step[1:] = np.abs(np.diff(c))
    path = sma(step, n) * n
    er = np.abs(net) / (path + EPS)
    return np.clip(er, 0.0, 1.0) * np.sign(np.nan_to_num(net))


@_register("adaptive_horizon", 4, {"ns": ("log", 3, 30), "nl": ("log", 40, 250),
                                   "lb": ("log", 40, 250)},
           lambda p: int(p["nl"]) + int(p["lb"]) + 25, "adaptive")
def _adaptive_horizon(s: Series, p: dict) -> np.ndarray:
    """Momentum at whichever of two horizons has actually been paying recently.

    Scores each horizon by the trailing sum of (signal at t-1) x (return at t) —
    realised, strictly past predictive value — and emits the winner. Chooses its
    own timescale rather than having one picked for it by the search.
    """
    ns, nl = max(int(p["ns"]), 2), max(int(p["nl"]), 10)
    lb = max(int(p["lb"]), 20)
    lr = log_returns(s)
    vol = _bar_vol(s, max(nl, 25))
    mom_s = _tanh(np.log(s.close / shift(s.close, ns)) / (vol * np.sqrt(ns) + EPS))
    mom_l = _tanh(np.log(s.close / shift(s.close, nl)) / (vol * np.sqrt(nl) + EPS))
    pay_s = sma(np.nan_to_num(shift(mom_s, 1) * lr), lb)
    pay_l = sma(np.nan_to_num(shift(mom_l, 1) * lr), lb)
    pick_short = pay_s > pay_l
    return np.where(pick_short, np.nan_to_num(mom_s), np.nan_to_num(mom_l))


# ---- tier 5: cross-sectional ------------------------------------------------
#
# These are the only primitives that read anything other than their own series.
# A basket leg carries the whole basket's closes in `meta["peer_close"]` (see
# `markets/basket.py`), so a cross-sectional score is an ordinary signal and a
# basket strategy is K ordinary single-leg backtests. That is deliberate: it
# means the audited engine, fill model and cost model are reused unchanged
# rather than a second cross-sectional backtester existing to disagree with them.
#
# On a series with no peers they return zeros, so a cross-sectional genome on a
# single-instrument family is inert rather than an error — the same convention
# `carry` uses on a market with no carry.

def _peer_log_returns(s: Series):
    """(peer log-return matrix, this leg's column) or (None, -1)."""
    mat = s.meta.get("peer_close")
    if mat is None or getattr(mat, "ndim", 0) != 2 or mat.shape[0] != s.close.size:
        return None, -1
    lp = np.log(mat)
    out = np.zeros_like(lp)
    out[1:] = lp[1:] - lp[:-1]
    return out, int(s.meta.get("peer_col", 0))


@_register("xs_reversal", 5, {"lb": ("log", 2, 40)},
           lambda p: int(p["lb"]) + 5, "cross_sectional")
def _xs_reversal(s: Series, p: dict) -> np.ndarray:
    """Minus this leg's trailing return *relative to its peers*, standardised.

    The most robustly documented cross-sectional effect there is: the leg that
    has lagged the basket over the last `lb` bars tends to catch up. Because the
    score is cross-sectionally demeaned, the same rule applied to every leg sums
    to roughly zero net exposure — the basket trade is dollar-neutral without any
    machinery imposing it, which is also why its raw Sharpe *is* its alpha
    Sharpe: there is no common factor left to residualise away.

    Strictly trailing: the window ends at t, and the engine acts on t+1.
    """
    r, col = _peer_log_returns(s)
    if r is None:
        return np.zeros(s.close.size)
    lb = max(int(p["lb"]), 2)
    cum = np.cumsum(r, axis=0)
    trail = np.full_like(cum, np.nan)
    trail[lb:] = cum[lb:] - cum[:-lb]
    rel = trail - np.nanmean(trail, axis=1, keepdims=True)
    sd = np.nanstd(rel, axis=1, keepdims=True)
    z = np.divide(rel, sd, out=np.zeros_like(rel), where=sd > EPS)
    return _tanh(-z[:, col])


@_register("xs_momentum", 5, {"lb": ("log", 20, 250), "skip": ("log", 1, 25)},
           lambda p: int(p["lb"]) + int(p["skip"]) + 5, "cross_sectional")
def _xs_momentum(s: Series, p: dict) -> np.ndarray:
    """This leg's trailing return relative to its peers, skipping the last
    `skip` bars — the standard construction, because the most recent window
    carries the reversal `xs_reversal` trades and including it fights itself."""
    r, col = _peer_log_returns(s)
    if r is None:
        return np.zeros(s.close.size)
    lb, sk = max(int(p["lb"]), 2), max(int(p["skip"]), 1)
    cum = np.cumsum(r, axis=0)
    trail = np.full_like(cum, np.nan)
    if lb + sk < cum.shape[0]:
        trail[lb + sk:] = cum[sk:-lb] - cum[: -(lb + sk)]
    rel = trail - np.nanmean(trail, axis=1, keepdims=True)
    sd = np.nanstd(rel, axis=1, keepdims=True)
    z = np.divide(rel, sd, out=np.zeros_like(rel), where=sd > EPS)
    return _tanh(z[:, col])
