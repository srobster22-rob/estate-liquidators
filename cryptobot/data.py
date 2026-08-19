"""
Market data layer for the bot factory.

Two sources, one interface:

  REAL      OHLCV pulled from a public exchange endpoint and cached as CSV. Nothing
            here needs an API key — these are the public candle endpoints. If the
            machine has no outbound access to the venue (this repo's CI sandbox
            doesn't), the fetch fails loudly rather than silently substituting
            fake data.

  SYNTHETIC A regime-switching GARCH process with fat tails, funding rates, and a
            *known* amount of exploitable structure. This exists so the factory and
            the validator can be tested end to end without network — and, more
            importantly, so the validator can be calibrated. Set every structure
            knob to zero (including regime_drift, see synth_market) and the series
            has fat tails and clustered volatility but nothing whatsoever to
            forecast, so any bot that "passes" on it is a false positive and the
            false-positive rate becomes measurable. See run.py null-test.

  A bot that looks profitable on synthetic data has proven exactly one thing: the
  harness runs. Real conclusions need real bars.

Everything is standard library. Prices are floats, timestamps are integer seconds.
"""

import collections
import csv
import itertools
import json
import math
import pathlib
import random
import time
import urllib.error
import urllib.request

CACHE_DIR = pathlib.Path(__file__).parent / "data_cache"

# Indicator cache budget, in floats, shared across EVERY market. See Market.memo.
#
# A per-market limit does not bound anything: 30 markets x 4 Market objects each
# (full plus three segments) x 160 series x 55,000 floats is hundreds of gigabytes,
# and the only reason it never blew up is that the search concentrates on a handful
# of markets. Budgeting globally, in elements rather than series, makes the ceiling
# independent of both the universe size and the history length — so a run on twelve
# years of hourly bars costs the same memory as one on five.
MEMO_MAX_ELEMENTS = 40_000_000          # ~1.3 GB of Python floats

_MEMO_ORDER = collections.OrderedDict()  # (market_id, key) -> (market, n_elements)
_MEMO_ELEMENTS = 0
_MARKET_IDS = itertools.count()


def memo_stats():
    return {"entries": len(_MEMO_ORDER), "elements": _MEMO_ELEMENTS,
            "budget": MEMO_MAX_ELEMENTS}


def _series_elements(value):
    """Length of a cached indicator, counting each list in a tuple (macd returns
    three series, the Kalman filter two)."""
    if isinstance(value, tuple):
        return sum(len(v) for v in value)
    return len(value)


SECONDS = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "12h": 43200, "1d": 86400,
}


# ---------------------------------------------------------------- market object

class Market:
    """One instrument, one timeframe, as parallel lists.

    Parallel lists rather than a list of bar objects because every indicator in
    indicators.py walks them in tight loops, and attribute lookup per bar shows up
    in the profile once the factory is evaluating thousands of bots.

    `funding` is the financing rate charged on a perp position *over that bar*,
    expressed as a fraction of notional (positive = longs pay shorts). Spot markets
    carry zeros. The backtester debits it every bar a position is open, which is
    what makes carry strategies honest instead of free money.
    """

    __slots__ = ("key", "symbol", "venue", "kind", "interval", "ts", "open",
                 "high", "low", "close", "volume", "funding", "fee_bps",
                 "spread_bps", "impact_bps", "truth", "_memo", "_mid")

    def __init__(self, key, symbol, venue, kind, interval, ts, open_, high, low,
                 close, volume, funding=None, fee_bps=5.0, spread_bps=2.0,
                 impact_bps=1.0, truth=None):
        self.key = key
        self.symbol = symbol
        self.venue = venue
        self.kind = kind                  # 'spot' | 'perp'
        self.interval = interval
        self.ts = ts
        self.open = open_
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.funding = funding if funding is not None else [0.0] * len(ts)
        self.fee_bps = fee_bps            # taker fee, one side, basis points
        self.spread_bps = spread_bps      # half-spread paid crossing, bps
        self.impact_bps = impact_bps      # extra bps per unit of notional turnover
        self.truth = truth or {}          # synthetic only: the generating params
        self._memo = {}                   # indicator cache, keyed (name, *args)
        self._mid = next(_MARKET_IDS)     # identity in the global cache

    def __len__(self):
        return len(self.ts)

    @property
    def bars_per_year(self):
        return 365.0 * 24.0 * 3600.0 / SECONDS[self.interval]

    def slice(self, start, end):
        """Half-open [start, end) view as a fresh Market. Indicator cache is NOT
        shared — a rolling mean computed on the parent would leak values from before
        `start` into the child's first bars, which is exactly the kind of leakage
        this whole file exists to prevent."""
        m = Market(self.key, self.symbol, self.venue, self.kind, self.interval,
                   self.ts[start:end], self.open[start:end], self.high[start:end],
                   self.low[start:end], self.close[start:end],
                   self.volume[start:end], self.funding[start:end],
                   self.fee_bps, self.spread_bps, self.impact_bps, self.truth)
        return m

    def memo(self, key, build):
        """Cache an indicator series. The factory evaluates thousands of bots
        against the same markets; without this, most of a run is recomputing the
        same 50-bar SMA.

        Eviction is global and measured in floats, not per-market and measured in
        series. Lookback windows are drawn from continuous ranges, so the number of
        distinct entries is unbounded, and their SIZE scales with the history — the
        two multiply. Budgeting globally in elements makes peak memory independent
        of how many markets the universe holds and how long their histories are,
        which is what makes a twelve-year run possible at all."""
        global _MEMO_ELEMENTS
        hit = self._memo.get(key)
        if hit is not None:
            _MEMO_ORDER.move_to_end((self._mid, key))
            return hit
        hit = build()
        n = _series_elements(hit)
        self._memo[key] = hit
        _MEMO_ORDER[(self._mid, key)] = (self, n)
        _MEMO_ELEMENTS += n
        while _MEMO_ELEMENTS > MEMO_MAX_ELEMENTS and len(_MEMO_ORDER) > 1:
            (_, stale_key), (owner, size) = _MEMO_ORDER.popitem(last=False)
            owner._memo.pop(stale_key, None)
            _MEMO_ELEMENTS -= size
        return hit

    def describe(self):
        span_days = (self.ts[-1] - self.ts[0]) / 86400.0 if len(self.ts) > 1 else 0
        return (f"{self.key}: {len(self)} bars of {self.interval} "
                f"({span_days:.0f}d), {self.kind}, fee {self.fee_bps}bps")


# ---------------------------------------------------------------- csv cache i/o

def cache_path(venue, symbol, interval, kind="spot"):
    """Cache filename. `kind` is part of it because BTCUSDT spot and BTCUSDT perp
    are different instruments with the same symbol: without it the perp fetch found
    the spot file already on disk, loaded it, and produced a "perp" with no funding
    at all — silently turning every carry strategy into a no-op."""
    CACHE_DIR.mkdir(exist_ok=True)
    safe = symbol.replace("/", "-")
    suffix = "" if kind == "spot" else f"_{kind}"
    return CACHE_DIR / f"{venue}_{safe}_{interval}{suffix}.csv"


def write_csv(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "open", "high", "low", "close", "volume", "funding"])
        w.writerows(rows)


def read_csv_market(path, key=None, kind="spot", interval=None, **kw):
    """Load a cached or hand-supplied CSV. Columns: ts,open,high,low,close,volume
    and optionally funding. `ts` is seconds since epoch (milliseconds are detected
    and converted). Rows must be ascending in time; duplicates and gaps are the
    caller's problem, but non-monotonic timestamps raise."""
    ts, o, h, l, c, v, f = [], [], [], [], [], [], []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            t = int(float(row["ts"]))
            if t > 10_000_000_000:        # milliseconds
                t //= 1000
            ts.append(t)
            o.append(float(row["open"]))
            h.append(float(row["high"]))
            l.append(float(row["low"]))
            c.append(float(row["close"]))
            v.append(float(row.get("volume") or 0.0))
            f.append(float(row.get("funding") or 0.0))
    if len(ts) < 2:
        raise ValueError(f"{path}: need at least 2 bars, got {len(ts)}")
    for i in range(1, len(ts)):
        if ts[i] <= ts[i - 1]:
            raise ValueError(f"{path}: timestamps not strictly increasing at row {i}")
    if interval is None:
        interval = _infer_interval(ts)
    name = pathlib.Path(path).stem
    parts = name.split("_")
    venue = parts[0] if len(parts) > 2 else "csv"
    symbol = parts[1] if len(parts) > 2 else name
    return Market(key or name, symbol, venue, kind, interval,
                  ts, o, h, l, c, v, f, **kw)


def _infer_interval(ts):
    gap = min(ts[i + 1] - ts[i] for i in range(min(len(ts) - 1, 200)))
    for name, sec in SECONDS.items():
        if sec == gap:
            return name
    raise ValueError(f"unrecognised bar spacing: {gap}s")


# ------------------------------------------------------------------- data audit
#
# Everything in this project was developed against the synthetic generator, which
# emits a perfect grid: every bar present, every OHLC consistent, every return
# drawn from a distribution with finite everything. Real candles are not like that,
# and the ways they differ are precisely the ways a backtest turns into fiction.
#
# The four that matter, in order of how much damage they do:
#
#   GAPS          An exchange outage removes bars. The bar that follows the hole
#                 carries a two-day price move in a one-hour slot. Nothing in the
#                 engine knows that: the vol estimator reads it as a regime change,
#                 the impact model prices it as a normal fill, and a momentum bot
#                 books the whole move as a win it could never have traded — the
#                 venue was down. Outages cluster on crash days, so this is not a
#                 rare inconvenience, it is a bias pointed in one direction.
#
#   STALE RUNS    A halted or illiquid symbol prints the same close for hours. A
#                 reversion bot sees zero deviation and no vol, sizes up, and earns
#                 a flat line for free. Then the halt lifts and the gap-return above
#                 lands on top of the oversized position.
#
#   BAD OHLC      close outside [low, high], high < low, zero or negative prices.
#                 Any of these means the feed is broken somewhere, and a stop or a
#                 range indicator reading that bar produces a number with no meaning.
#
#   BAD TICKS     A single-bar 60% move that reverses next bar is a data error, not
#                 a flash crash, and it is indistinguishable from one after the fact.
#                 Both are real hazards for a vol-targeted sizer.
#
# audit_market() finds all four and reports them. It deliberately does NOT repair
# anything by default. Interpolating a gap invents a price path that never traded;
# dropping a stale run rewrites history to be more tradeable than it was. Both make
# the backtest better-looking and less true, which is the exact failure mode this
# codebase spends most of its lines defending against. The caller gets the numbers
# and makes the call.


def contiguous_runs(market):
    """Index ranges over which bars are spaced exactly one interval apart.

    Returns [(start, end), ...] half-open, longest first."""
    step = SECONDS[market.interval]
    ts = market.ts
    runs, start = [], 0
    for i in range(1, len(ts)):
        if ts[i] - ts[i - 1] != step:
            runs.append((start, i))
            start = i
    runs.append((start, len(ts)))
    runs.sort(key=lambda r: r[1] - r[0], reverse=True)
    return runs


def trim_to_contiguous(market, min_bars=500):
    """The longest gap-free stretch, as a fresh Market.

    Use when a gap sits near one end of the history — the usual case for a symbol
    that was listed part-way through the window, or one whose feed broke once. If
    the holes are scattered through the middle this throws away most of the data
    and you are better off keeping the gaps and knowing they are there, which is
    why this is never applied automatically."""
    runs = contiguous_runs(market)
    start, end = runs[0]
    if end - start < min_bars:
        raise ValueError(
            f"{market.key}: longest gap-free run is {end - start} bars, "
            f"under the {min_bars} required")
    return market.slice(start, end)


def audit_market(market, extreme_return=0.35, stale_run=12):
    """Data-quality findings for one market. Pure inspection, no mutation.

    `extreme_return` is a per-bar log move flagged as suspicious (0.35 ~= 42% up or
    30% down in a single bar). `stale_run` is how many identical closes in a row
    count as a stall."""
    n = len(market)
    step = SECONDS[market.interval]
    ts, c, h, l, o, v = (market.ts, market.close, market.high, market.low,
                         market.open, market.volume)

    gaps, missing = [], 0
    for i in range(1, n):
        delta = ts[i] - ts[i - 1]
        if delta != step:
            skipped = delta // step - 1 if delta > step else -1
            gaps.append({"index": i, "at": ts[i - 1], "seconds": delta,
                         "bars_missing": skipped})
            if skipped > 0:
                missing += skipped

    bad_ohlc = [i for i in range(n)
                if not (l[i] <= min(o[i], c[i]) and h[i] >= max(o[i], c[i])
                        and h[i] >= l[i])]
    nonpositive = [i for i in range(n) if c[i] <= 0.0 or o[i] <= 0.0]

    stalls, run_len, longest_stall = 0, 1, 1
    for i in range(1, n):
        if c[i] == c[i - 1]:
            run_len += 1
        else:
            if run_len >= stale_run:
                stalls += 1
            longest_stall = max(longest_stall, run_len)
            run_len = 1
    if run_len >= stale_run:
        stalls += 1
    longest_stall = max(longest_stall, run_len)

    extremes, worst = [], 0.0
    gap_indices = {g["index"] for g in gaps}
    for i in range(1, n):
        if c[i] <= 0.0 or c[i - 1] <= 0.0:
            continue
        r = math.log(c[i] / c[i - 1])
        worst = max(worst, abs(r))
        if abs(r) > extreme_return:
            extremes.append({"index": i, "log_return": r,
                             "spans_gap": i in gap_indices})

    runs = contiguous_runs(market)
    span = ts[-1] - ts[0] if n > 1 else 0
    expected = span // step + 1 if step else n

    return {
        "key": market.key,
        "interval": market.interval,
        "kind": market.kind,
        "bars": n,
        "span_days": span / 86400.0,
        "expected_bars": expected,
        "coverage": n / expected if expected else 1.0,
        "gaps": gaps,
        "bars_missing": missing,
        "longest_contiguous": runs[0][1] - runs[0][0],
        "bad_ohlc": bad_ohlc,
        "nonpositive": nonpositive,
        "stalls": stalls,
        "longest_stall": longest_stall,
        "zero_volume": sum(1 for x in v if x == 0.0),
        "extremes": extremes,
        "extremes_spanning_gaps": sum(1 for e in extremes if e["spans_gap"]),
        "worst_bar_return": worst,
        "funding_bars": sum(1 for x in market.funding if x != 0.0),
    }


def audit_verdict(report, min_coverage=0.98):
    """Reduce an audit to (ok, [reasons]). `ok` False means the numbers a backtest
    on this market produces should not be believed until the reason is understood."""
    bad = []
    if report["bad_ohlc"]:
        bad.append(f"{len(report['bad_ohlc'])} bars with impossible OHLC")
    if report["nonpositive"]:
        bad.append(f"{len(report['nonpositive'])} bars at or below zero price")
    if report["coverage"] < min_coverage:
        bad.append(f"only {report['coverage']:.1%} of the calendar has bars "
                   f"({report['bars_missing']} missing across "
                   f"{len(report['gaps'])} gaps)")
    if report["extremes_spanning_gaps"]:
        bad.append(f"{report['extremes_spanning_gaps']} large moves land on the "
                   f"bar right after a gap — untradeable, the venue was down")
    if report["longest_stall"] >= 48:
        bad.append(f"price frozen for {report['longest_stall']} consecutive bars")
    return (not bad), bad


def format_audit(report, min_coverage=0.98):
    """One market's audit as a short block of text."""
    ok, reasons = audit_verdict(report, min_coverage)
    lines = [f"{report['key']}  ({report['kind']}, {report['interval']})",
             f"    bars {report['bars']} of {report['expected_bars']} expected"
             f"   coverage {report['coverage']:.2%}"
             f"   span {report['span_days']:.0f}d",
             f"    gaps {len(report['gaps'])}"
             f"   missing bars {report['bars_missing']}"
             f"   longest clean run {report['longest_contiguous']}",
             f"    stalls {report['stalls']} (longest {report['longest_stall']} "
             f"bars)   zero-volume bars {report['zero_volume']}",
             f"    worst 1-bar move {report['worst_bar_return']:+.1%} log"
             f"   outliers {len(report['extremes'])}"
             f" ({report['extremes_spanning_gaps']} of them post-gap)"]
    if report["funding_bars"]:
        lines.append(f"    funding charged on {report['funding_bars']} bars")
    lines.append("    VERDICT: usable" if ok else "    VERDICT: SUSPECT")
    for r in reasons:
        lines.append(f"      - {r}")
    return "\n".join(lines)


def audit_universe(markets, min_coverage=0.98):
    """Audit a whole universe. Returns (reports, [keys that failed])."""
    reports = {k: audit_market(m) for k, m in markets.items()}
    suspect = [k for k, r in reports.items()
               if not audit_verdict(r, min_coverage)[0]]
    return reports, suspect


# ---------------------------------------------------------------- real fetchers

def _get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "cryptobot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def fetch_binance(symbol="BTCUSDT", interval="1h", bars=5000, kind="spot"):
    """Public klines endpoint, paged backwards 1000 at a time.

    Perp mode also pulls the funding history and prorates each 8h funding payment
    across the bars it covers, so a 1h perp backtest is charged 1/8 of the rate per
    bar rather than a lump every eighth bar. Funding is the difference between a
    carry strategy that works and one that only appears to."""
    base = ("https://fapi.binance.com/fapi/v1" if kind == "perp"
            else "https://api.binance.com/api/v3")
    step = SECONDS[interval] * 1000
    end = int(time.time() * 1000)
    rows = []
    while len(rows) < bars:
        want = min(1000, bars - len(rows))
        url = (f"{base}/klines?symbol={symbol}&interval={interval}"
               f"&limit={want}&endTime={end}")
        chunk = _get_json(url)
        if not chunk:
            break
        rows = chunk + rows
        end = chunk[0][0] - step
        if len(chunk) < want:
            break
        time.sleep(0.25)                  # be a good citizen

    bars_out = [[int(r[0]) // 1000, float(r[1]), float(r[2]), float(r[3]),
                 float(r[4]), float(r[5]), 0.0] for r in rows]

    if kind == "perp" and bars_out:
        _apply_binance_funding(symbol, bars_out, SECONDS[interval])
    return bars_out


def _apply_binance_funding(symbol, bars_out, bar_sec):
    """Attach realised funding to the bar in which each payment SETTLES.

    Not spread backwards over the preceding eight hours, which is what this did
    first and which is a lookahead: Binance's rate for the period ending at t is the
    clamped TWAP of the premium index over (t-8h, t], so it is not known until t.
    Writing it onto the eight bars before t handed `carry_funding` — which reads
    this very column as its signal — seven bars of advance knowledge of a payment it
    was about to collect. It would have cleared every gate, because the edge really
    is in the data as constructed, and earned nothing live.

    Charging the whole payment on its settlement bar is also simply more accurate:
    funding is a discrete cash flow paid by whoever holds the position at t, not a
    continuous accrual. A daily bar therefore collects all three of its payments,
    where the old prorated version gave it one."""
    start_ms = bars_out[0][0] * 1000
    end_ms = bars_out[-1][0] * 1000
    payments = []
    cursor = start_ms
    while cursor < end_ms:
        url = ("https://fapi.binance.com/fapi/v1/fundingRate"
               f"?symbol={symbol}&startTime={cursor}&limit=1000")
        chunk = _get_json(url)
        if not chunk:
            break
        payments += [(int(p["fundingTime"]) // 1000, float(p["fundingRate"]))
                     for p in chunk]
        nxt = int(chunk[-1]["fundingTime"]) + 1
        if nxt <= cursor:
            break
        cursor = nxt
        time.sleep(0.25)
    if not payments:
        return
    # Bucket each payment onto the bar whose interval contains its settlement time,
    # summing when several settle inside one bar (a daily bar holds three).
    per_bar = {}
    for t, rate in payments:
        bucket = t - (t % bar_sec)
        per_bar[bucket] = per_bar.get(bucket, 0.0) + rate
    for row in bars_out:
        row[6] = per_bar.get(row[0] - (row[0] % bar_sec), 0.0)


def fetch_coinbase(symbol="BTC-USD", interval="1h", bars=5000, kind="spot"):
    """Coinbase Exchange candles. Granularity is restricted to a fixed set and each
    request returns at most 300 candles, so this pages backwards in 300s."""
    gran = SECONDS[interval]
    if gran not in (60, 300, 900, 3600, 21600, 86400):
        raise ValueError(f"coinbase does not serve {interval} candles")
    out = []
    end = int(time.time())
    while len(out) < bars:
        start = end - gran * 300
        url = (f"https://api.exchange.coinbase.com/products/{symbol}/candles"
               f"?granularity={gran}&start={start}&end={end}")
        chunk = _get_json(url)
        if not chunk:
            break
        # [ time, low, high, open, close, volume ], newest first
        chunk.sort(key=lambda r: r[0])
        out = [[int(r[0]), float(r[3]), float(r[2]), float(r[1]),
                float(r[4]), float(r[5]), 0.0] for r in chunk] + out
        end = start
        time.sleep(0.3)
    return out[-bars:]


def fetch_kraken(symbol="XBTUSD", interval="1h", bars=720, kind="spot"):
    """Kraken OHLC. Serves at most 720 bars per pair — fine for a sanity check,
    too short for walk-forward validation on anything but daily bars."""
    minutes = SECONDS[interval] // 60
    url = f"https://api.kraken.com/0/public/OHLC?pair={symbol}&interval={minutes}"
    payload = _get_json(url)
    if payload.get("error"):
        raise RuntimeError(f"kraken: {payload['error']}")
    series = next(v for k, v in payload["result"].items() if k != "last")
    return [[int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]),
             float(r[6]), 0.0] for r in series][-bars:]


FETCHERS = {"binance": fetch_binance, "coinbase": fetch_coinbase,
            "kraken": fetch_kraken}


def fetch_market(venue, symbol, interval="1h", bars=5000, kind="spot",
                 refresh=False, **market_kw):
    """Fetch-or-load. Returns a Market; raises with the underlying network error if
    there is no cache and the venue is unreachable. It will never quietly hand back
    synthetic data in place of real data — that substitution is how people end up
    trading a backtest of a random number generator."""
    path = cache_path(venue, symbol, interval, kind)
    if path.exists() and not refresh:
        return read_csv_market(path, key=f"{venue}:{symbol}:{interval}:{kind}",
                               kind=kind, interval=interval, **market_kw)
    try:
        rows = FETCHERS[venue](symbol=symbol, interval=interval, bars=bars, kind=kind)
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(
            f"cannot reach {venue} ({exc}); no cache at {path}. Run the fetch on a "
            f"machine with outbound access and commit/copy the CSV, or use "
            f"--markets synthetic for a harness test."
        ) from exc
    if not rows:
        raise RuntimeError(f"{venue} returned no candles for {symbol} {interval}")
    write_csv(path, rows)
    return read_csv_market(path, key=f"{venue}:{symbol}:{interval}:{kind}",
                           kind=kind, interval=interval, **market_kw)


# ------------------------------------------------------------------- synthetic

REGIMES = {
    # name          drift/yr  vol/yr  mean duration (bars)
    "bull_trend":   (1.40,    0.65,   400),
    "bear_trend":   (-0.90,   0.85,   300),
    "chop":         (0.05,    0.45,   600),
    "high_vol":     (0.00,    1.40,   150),
    "crash":        (-3.00,   2.20,    40),
    "quiet_drift":  (0.25,    0.28,   700),
}

REGIME_NAMES = list(REGIMES)


def synth_market(key, seed, bars=8000, interval="1h", kind="spot", phi=0.0,
                 start_price=30000.0, fee_bps=5.0, spread_bps=2.0,
                 impact_bps=1.0, funding_beta=0.0, trend_strength=0.0,
                 trend_halflife=200, revert_kappa=0.0, revert_span=200,
                 regime_drift=1.0):
    """Regime-switching GARCH(1,1) with Student-t(5) shocks and three optional,
    independently switchable sources of exploitable structure.

        mu_t    = rho*mu_{t-1} + innovation           hidden persistent drift
        d_t     = log P_t - anchor_t                  deviation from a slow anchor
        r_t     = mu_regime*dt + mu_t - kappa*d_t + phi*r_{t-1} + sigma_t*eps_t
        sigma_t = GARCH(1,1) around the regime's unconditional vol

    WHICH KNOB MATTERS, AND WHY IT ISN'T phi

      `phi` is one-bar autocorrelation. It looks like an edge and isn't: on hourly
      bars a phi of 0.05 is worth about 3bps of expected move per bar against 9bps
      of round-trip cost, and it decays to nothing by the third bar. A market whose
      only structure is phi is a market where the honest answer is "don't trade it",
      which is why the first version of this file produced a universe nothing could
      pass. That was the generator being wrong, not the validator being harsh.

      `trend_strength` is the realistic one: a hidden drift state with a half-life
      of `trend_halflife` bars, so the predictable component persists long enough to
      be worth paying a spread for. It is expressed as the ratio of the drift's
      standard deviation to the bar's own volatility — 0.04 means an oracle who knew
      mu_t exactly would run at roughly 4 annualised Sharpe, and a real estimator
      with real costs lands somewhere near 1 to 2.

      `revert_kappa` pulls price back toward an EMA anchor, which is what makes a
      fader work. Same idea in the opposite direction.

      All three default to zero. Most of the universe leaves them there.

    `regime_drift` scales the bull/bear regime drifts. It is 1.0 by default because
    real markets do cycle, but note what that means: a regime that drifts up for 400
    bars IS a persistent, exploitable trend. So a market with all three knobs at zero
    is efficient *apart from the regime cycle*, not featureless. The strict null used
    for false-positive calibration sets regime_drift=0, leaving only volatility
    clustering — vol that clusters without drift offers no directional edge at all,
    which is precisely the property the calibration needs.

    `funding_beta` makes the perp funding rate respond to trailing returns, which is
    how the real thing behaves (crowded longs pay). Nonzero gives a carry bot
    something genuine to harvest; the cost of holding is charged regardless.
    """
    rng = random.Random(seed)
    dt = SECONDS[interval] / (365.0 * 24.0 * 3600.0)
    sqdt = math.sqrt(dt)

    regime = rng.choice(REGIME_NAMES)
    left = REGIMES[regime][2]
    # GARCH state, expressed per-bar
    a, b = 0.08, 0.90                          # ARCH + GARCH coefficients
    base_var = (REGIMES[regime][1] * sqdt) ** 2
    var = base_var
    prev_r = 0.0

    ts0 = int(time.mktime((2019, 1, 1, 0, 0, 0, 0, 1, 0)))
    step = SECONDS[interval]
    price = start_price
    ts, o, h, l, c, v, fnd = [], [], [], [], [], [], []
    labels = []
    recent = []

    # Hidden drift state and slow anchor. Both are properties of the generating
    # process only — a bot sees prices and nothing else, so it has to estimate them.
    rho = 0.5 ** (1.0 / max(1, trend_halflife))
    mu = 0.0
    anchor_log = math.log(price)
    anchor_lam = 2.0 / (revert_span + 1.0)

    for i in range(bars):
        if left <= 0:
            regime = rng.choice(REGIME_NAMES)
            left = max(20, int(rng.expovariate(1.0 / REGIMES[regime][2])))
        left -= 1
        vol = REGIMES[regime][1]
        base_var = (vol * sqdt) ** 2
        w = base_var * (1.0 - a - b)
        var = w + a * (prev_r ** 2) + b * var
        sigma = math.sqrt(max(var, 1e-12))

        eps = _student_t(rng, 5) / math.sqrt(5.0 / 3.0)   # unit variance
        if trend_strength:
            # Stationary sd of mu is trend_strength * sigma, by construction.
            innov = trend_strength * sigma * math.sqrt(1.0 - rho * rho)
            mu = rho * mu + rng.gauss(0.0, innov)
        pull = -revert_kappa * (math.log(price) - anchor_log) if revert_kappa else 0.0
        # Ito correction. These are LOG returns, but P&L is earned in simple
        # returns, and E[exp(r) - 1] = exp(sigma^2/2) - 1 > 0 even when E[r] = 0.
        # Without the -sigma^2/2 term a "zero drift" market pays a permanently long
        # bot a premium of sigma^2/2 a year — at 65% vol that is 21% — so the strict
        # null used to calibrate the false-positive rate was not null in the space
        # where the measurement happens. Subtracting it makes the intended drift the
        # ARITHMETIC drift, so regime_drift=0 means exactly zero expected P&L.
        r = (REGIMES[regime][0] * regime_drift * dt - 0.5 * sigma * sigma
             + mu + pull + phi * prev_r + sigma * eps)
        r = max(-0.35, min(0.35, r))          # no single-bar -100%
        prev_r = r

        op = price
        price = price * math.exp(r)
        anchor_log += anchor_lam * (math.log(price) - anchor_log)
        # Intrabar range: a fraction of the bar's own vol on each side.
        up = abs(rng.gauss(0, 1)) * sigma * 0.7
        dn = abs(rng.gauss(0, 1)) * sigma * 0.7
        hi = max(op, price) * math.exp(up)
        lo = min(op, price) * math.exp(-dn)

        recent.append(r)
        if len(recent) > 48:
            recent.pop(0)
        if kind == "perp":
            # Base 0.01% per 8h, prorated per bar, plus a crowding term.
            base = 0.0001 * (step / (8 * 3600.0))
            crowd = funding_beta * (sum(recent) / len(recent))
            rate = base + crowd + rng.gauss(0, base * 0.5)
        else:
            rate = 0.0

        ts.append(ts0 + i * step)
        o.append(op)
        h.append(hi)
        l.append(lo)
        c.append(price)
        v.append(abs(rng.gauss(1000, 300)) * (1 + abs(r) * 40))
        fnd.append(rate)
        labels.append(regime)

    return Market(key, key, "synthetic", kind, interval, ts, o, h, l, c, v, fnd,
                  fee_bps, spread_bps, impact_bps,
                  truth={"phi": phi, "seed": seed, "funding_beta": funding_beta,
                         "trend_strength": trend_strength,
                         "trend_halflife": trend_halflife,
                         "revert_kappa": revert_kappa,
                         "regime_drift": regime_drift, "regimes": labels})


def cointegrated_pair(key_a, key_b, seed, spread_sd=0.020, spread_halflife=300,
                      beta=1.0, **kw):
    """Two markets that share a price and differ by a stationary spread.

        log P_b(t) = beta * log P_a(t) + s_t
        s_t        = rho * s_{t-1} + noise,   rho from `spread_halflife`

    Neither leg is predictable on its own — market A is whatever synth_market was
    asked for, and B inherits A's drift, regimes and vol. What IS predictable is the
    gap between them, which is exactly the structure a pairs trade needs and the one
    kind this generator could not previously produce. `spread_reversion` shipped in
    the strategy zoo from the start with nothing in the universe it could trade;
    this is that market.

    `spread_sd` is the standard deviation of the log spread. It has to clear costs
    by a wide margin to be tradeable: a two-sigma round trip earns about
    2 * spread_sd, and pays fees on FOUR legs (in and out, both sides), so at 8bps a
    leg the cost is ~32bps and a 2% spread sd leaves plenty. Set it near the cost and
    the correct answer becomes "don't trade it", which is a fine thing to test but
    not what this market is for.

    Returns (market_a, market_b), sharing timestamps exactly so the pair is legal
    under evolve.Factory._build_pairs.
    """
    a = synth_market(key_a, seed=seed, **kw)
    rng = random.Random(seed + 7717)
    rho = 0.5 ** (1.0 / max(1, spread_halflife))
    innov = spread_sd * math.sqrt(1.0 - rho * rho)

    n = len(a)
    s = 0.0
    log_b, spreads = [], []
    for i in range(n):
        s = rho * s + rng.gauss(0.0, innov)
        spreads.append(s)
        log_b.append(beta * math.log(a.close[i]) + s)

    close = [math.exp(x) for x in log_b]
    o, h, l = [], [], []
    for i, c in enumerate(close):
        prev = close[i - 1] if i else c
        # Intrabar range scaled to this bar's own move, same shape as synth_market.
        move = abs(math.log(c / prev)) if prev > 0 else 0.0
        up = abs(rng.gauss(0, 1)) * (move + 1e-4) * 0.7
        dn = abs(rng.gauss(0, 1)) * (move + 1e-4) * 0.7
        o.append(prev)
        h.append(max(prev, c) * math.exp(up))
        l.append(min(prev, c) * math.exp(-dn))

    b = Market(key_b, key_b, "synthetic", a.kind, a.interval, list(a.ts), o, h, l,
               close, list(a.volume), list(a.funding), a.fee_bps, a.spread_bps,
               a.impact_bps,
               truth=dict(a.truth, cointegrated_with=key_a, spread_sd=spread_sd,
                          spread_halflife=spread_halflife, beta=beta))
    a.truth = dict(a.truth, cointegrated_with=key_b, spread_sd=spread_sd,
                   spread_halflife=spread_halflife, beta=beta)
    return a, b


def factor_basket(keys, seed, factor_vol_share=0.6, idio_trend=0.0,
                  idio_halflife=200, **kw):
    """A basket of markets sharing one common factor plus idiosyncratic moves.

        r_i(t) = beta_i * f(t) + e_i(t)

    where f is a market-wide factor and e_i is that instrument's own return, which
    may carry its own hidden drift. This is the structure real crypto actually has —
    everything moves with BTC, and the interesting question is which names are
    strong *relative to the pack* — and it is the only structure in this generator
    that `xs_momentum` can trade properly. Cointegrated pairs give it two names to
    rank; a basket gives it a cross-section.

    Note what is and is not exploitable here. The factor itself is a random walk
    with regime drift like any other market, so betting on it is just betting on
    direction. What IS forecastable is the idiosyncratic component when
    `idio_trend` is nonzero: names whose own drift is persistent stay strong
    relative to the basket, which is exactly the cross-sectional momentum premise.
    With idio_trend=0 the basket is a decoy — correlated, plausible-looking, and
    offering nothing to a ranking strategy.

    Returns markets in the order of `keys`, sharing timestamps exactly.
    """
    n_names = len(keys)
    factor = synth_market(f"{keys[0]}__factor", seed=seed, **kw)
    f_ret = [0.0] + [math.log(factor.close[i] / factor.close[i - 1])
                     for i in range(1, len(factor))]
    n = len(factor)
    dt_years = SECONDS[factor.interval] / (365.0 * 24.0 * 3600.0)
    sqdt = math.sqrt(dt_years)
    rho = 0.5 ** (1.0 / max(1, idio_halflife))

    out = []
    for j, key in enumerate(keys):
        rng = random.Random(seed * 131 + j * 977)
        beta = 0.7 + 0.6 * (j / max(1, n_names - 1))     # 0.7 .. 1.3
        # Idiosyncratic vol scaled so the factor explains `factor_vol_share` of
        # variance on average.
        f_var = sum(x * x for x in f_ret) / max(1, n - 1)
        idio_sd = math.sqrt(max(1e-18, f_var * (1.0 - factor_vol_share)
                                / max(1e-9, factor_vol_share)))
        mu = 0.0
        price = kw.get("start_price", 100.0) * (0.5 + j)
        ts, o, h, l, c, v = [], [], [], [], [], []
        for i in range(n):
            if idio_trend:
                innov = idio_trend * idio_sd * math.sqrt(1.0 - rho * rho)
                mu = rho * mu + rng.gauss(0.0, innov)
            e = mu + rng.gauss(0.0, idio_sd)
            r = beta * f_ret[i] + e - 0.5 * (beta * beta * f_var + idio_sd ** 2)
            r = max(-0.35, min(0.35, r))
            op = price
            price = price * math.exp(r)
            up = abs(rng.gauss(0, 1)) * (abs(r) + 1e-4) * 0.7
            dn = abs(rng.gauss(0, 1)) * (abs(r) + 1e-4) * 0.7
            ts.append(factor.ts[i])
            o.append(op)
            h.append(max(op, price) * math.exp(up))
            l.append(min(op, price) * math.exp(-dn))
            c.append(price)
            v.append(factor.volume[i] * (0.5 + rng.random()))
        out.append(Market(key, key, "synthetic", factor.kind, factor.interval,
                          list(ts), o, h, l, c, v, list(factor.funding),
                          factor.fee_bps, factor.spread_bps, factor.impact_bps,
                          truth=dict(factor.truth, basket=keys, beta=beta,
                                     idio_trend=idio_trend,
                                     factor_vol_share=factor_vol_share)))
    return out


def _student_t(rng, df):
    """Student-t via the normal/chi-square ratio. Variance is df/(df-2); callers
    normalise. Fat tails matter here: a Gaussian synthetic market makes every
    drawdown estimate optimistic, and drawdown is what actually stops a bot."""
    z = rng.gauss(0.0, 1.0)
    chi = sum(rng.gauss(0.0, 1.0) ** 2 for _ in range(df))
    return z / math.sqrt(chi / df)
