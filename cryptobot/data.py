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

import csv
import json
import math
import pathlib
import random
import time
import urllib.error
import urllib.request

CACHE_DIR = pathlib.Path(__file__).parent / "data_cache"

# Max cached indicator series per market. See Market.memo.
MEMO_LIMIT = 400

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
                 "spread_bps", "impact_bps", "truth", "_memo")

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
        """Cache an indicator series on the market. The factory evaluates thousands
        of bots against the same handful of markets; without this, 90% of a run is
        recomputing the same 50-bar SMA.

        The cap is not decoration. Lookback windows are sampled from continuous
        ranges, so an unbounded cache grows to (distinct windows x indicator types)
        entries — a few thousand series of tens of thousands of floats each, which
        is gigabytes on a long run. When it fills, the oldest half goes; insertion
        order makes that the least recently *created*, which for this access pattern
        is close enough to least recently used."""
        hit = self._memo.get(key)
        if hit is None:
            if len(self._memo) >= MEMO_LIMIT:
                for stale in list(self._memo)[:MEMO_LIMIT // 2]:
                    del self._memo[stale]
            hit = build()
            self._memo[key] = hit
        return hit

    def describe(self):
        span_days = (self.ts[-1] - self.ts[0]) / 86400.0 if len(self.ts) > 1 else 0
        return (f"{self.key}: {len(self)} bars of {self.interval} "
                f"({span_days:.0f}d), {self.kind}, fee {self.fee_bps}bps")


# ---------------------------------------------------------------- csv cache i/o

def cache_path(venue, symbol, interval):
    CACHE_DIR.mkdir(exist_ok=True)
    safe = symbol.replace("/", "-")
    return CACHE_DIR / f"{venue}_{safe}_{interval}.csv"


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
    # Prorate each 8h payment across the bars in its window.
    per_bar = {}
    for t, rate in payments:
        window = 8 * 3600
        n = max(1, window // bar_sec)
        for k in range(n):
            per_bar[t - k * bar_sec] = rate / n
    for row in bars_out:
        row[6] = per_bar.get(row[0] - row[0] % bar_sec, 0.0)


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
    path = cache_path(venue, symbol, interval)
    if path.exists() and not refresh:
        return read_csv_market(path, key=f"{venue}:{symbol}:{interval}",
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
    return read_csv_market(path, key=f"{venue}:{symbol}:{interval}",
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
        r = (REGIMES[regime][0] * regime_drift * dt + mu + pull
             + phi * prev_r + sigma * eps)
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


def _student_t(rng, df):
    """Student-t via the normal/chi-square ratio. Variance is df/(df-2); callers
    normalise. Fat tails matter here: a Gaussian synthetic market makes every
    drawdown estimate optimistic, and drawdown is what actually stops a bot."""
    z = rng.gauss(0.0, 1.0)
    chi = sum(rng.gauss(0.0, 1.0) ** 2 for _ in range(df))
    return z / math.sqrt(chi / df)
