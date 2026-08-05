"""
The market universe, and how it is cut into train / validation / vault.

MARKET TYPES. The brief was "try all different types of markets", and the types that
matter are not the ticker names — they're the behaviours: slow majors, high-beta
alts, funding-bearing perps, fast timeframes where costs dominate, slow timeframes
where sample size dominates. The synthetic universe spans those deliberately, and
*most of its markets have nothing to find*, because that is the honest prior for a
liquid market. A universe where everything is exploitable would train the factory to
expect a signal in every instrument, which is the habit that loses money.

One of the markets that DOES have structure — smallcap_alt_1h — sits behind 30bps of
round-trip cost that eats the edge completely. The correct verdict there is "real
pattern, don't trade it", and it is in the universe specifically because that verdict
is the one a factory with an optimistic fee model will get wrong.

THE THREE-WAY SPLIT is the spine of the whole project:

    TRAIN       [~50%]  The optimiser lives here. It may look at this as many
                        times as it likes.
    VALIDATION  [~25%]  The gauntlet runs here. Every look is counted, because
                        every look is a trial and the deflated Sharpe pays for it.
    VAULT       [~25%]  Touched only by a candidate that has already passed
                        everything else, at most a handful of times per project,
                        with each use logged permanently to state/vault_log.json.

Between segments sits an EMBARGO of dropped bars. The reason is not what it first
looks like: a strategy cannot literally read across the boundary, because each
segment is sliced into its own Market and every indicator restarts its warm-up there
(returning None, on which the backtester refuses to trade). The real problem is
information OVERLAP. A trend with a 500-bar half-life that begins in training is
still running at the start of validation, so the two windows are not independent
draws and the "out-of-sample" test is partly a re-run of the in-sample one. The
embargo therefore has to cover the data's own persistence — the longest trend
half-life and spread half-life in the universe — which is what 1000 bars is sized
against, not the longest lookback.

That has a cost worth stating: at 1000 bars of embargo and a 25% vault, a market
needs ~8,400 bars to be splittable at all. For daily bars that is twenty-three
years, which nothing in crypto has, so the daily market in this universe is skipped
with a message rather than quietly validated on a sample too short to mean anything.

The vault burn counter exists because out-of-sample data is a consumable. Test
against it twenty times and it is training data with extra steps; the counter makes
that visible instead of letting it happen quietly.
"""

import math

from . import data as dta

EMBARGO_BARS = 1000         # see the note on overlap below


class Segments:
    __slots__ = ("train", "validation", "vault", "full")

    def __init__(self, full, train, validation, vault):
        self.full = full
        self.train = train
        self.validation = validation
        self.vault = vault


def split(market, train_frac=0.50, val_frac=0.25, embargo=EMBARGO_BARS):
    """Chronological three-way split with embargo gaps. Chronological because a
    random split lets the optimiser interpolate across time, which no live bot can
    do."""
    n = len(market)
    need = 3 * embargo + 300
    if n < need:
        raise ValueError(f"{market.key}: {n} bars is too few to split with a "
                         f"{embargo}-bar embargo (need {need})")
    t_end = int(n * train_frac)
    v_start = t_end + embargo
    v_end = v_start + int(n * val_frac)
    k_start = v_end + embargo
    if k_start >= n - 100:
        raise ValueError(f"{market.key}: vault segment would be under 100 bars")
    return Segments(market,
                    market.slice(0, t_end),
                    market.slice(v_start, v_end),
                    market.slice(k_start, n))


# ------------------------------------------------------------ synthetic build

SYNTH_SPEC = [
    # The magnitudes here were not guessed — they were calibrated by probing each
    # market with plain, unfitted bots and adjusting until a hand-written momentum,
    # fade, carry or spread rule reached
    # roughly 1.0-2.5 Sharpe on the structured ones and nothing on the rest. Strong
    # enough that a working factory finds them; weak enough that a broken one
    # doesn't stumble into them. test_structured_markets_carry_a_reachable_edge
    # keeps that calibration honest as the generator changes.
    dict(key="major_spot_1h", interval="1h", kind="spot", price=30000.0,
         fee=5.0, spread=1.0),
    dict(key="major_spot_4h", interval="4h", kind="spot", price=30000.0,
         fee=5.0, spread=1.0),
    dict(key="major_spot_1d", interval="1d", kind="spot", price=30000.0,
         fee=5.0, spread=1.0),
    dict(key="major_perp_1h", interval="1h", kind="perp", price=30000.0,
         fee=4.0, spread=1.0),
    dict(key="largecap_alt_1h", interval="1h", kind="spot", price=1800.0,
         fee=7.0, spread=2.0, trend_strength=0.090, trend_halflife=250),
    dict(key="largecap_alt_4h", interval="4h", kind="spot", price=1800.0,
         fee=7.0, spread=2.0, trend_strength=0.100, trend_halflife=120),
    dict(key="midcap_alt_1h", interval="1h", kind="spot", price=12.0,
         fee=10.0, spread=5.0, revert_kappa=0.011, revert_span=150),
    # High-cost venue with genuine reversion that the costs eat. The correct
    # verdict here is "no trade", and a factory that reports an edge on it has
    # under-modelled fees.
    dict(key="smallcap_alt_1h", interval="1h", kind="spot", price=0.4,
         fee=15.0, spread=15.0, revert_kappa=0.012, revert_span=100),
    dict(key="smallcap_alt_15m", interval="15m", kind="spot", price=0.4,
         fee=15.0, spread=20.0),
    dict(key="alt_perp_1h", interval="1h", kind="perp", price=12.0,
         fee=6.0, spread=3.0, funding_beta=0.13),
    dict(key="alt_perp_4h", interval="4h", kind="perp", price=12.0,
         fee=6.0, spread=3.0, trend_strength=0.100, trend_halflife=90),
    dict(key="quiet_pair_1h", interval="1h", kind="spot", price=100.0,
         fee=6.0, spread=2.0),
    dict(key="decoy_a_1h", interval="1h", kind="spot", price=500.0,
         fee=6.0, spread=2.0),
    dict(key="decoy_b_1h", interval="1h", kind="spot", price=500.0,
         fee=6.0, spread=2.0),

    # --- second wave -------------------------------------------------------
    # Added to give the factory more than two independent edges to find. Each of
    # these is generated from its own seed, so its structure is statistically
    # independent of every other market's — which is the point. Two bots on the
    # same market tend to correlate above 0.8 no matter how different their logic
    # looks, so extra *edges* require extra *markets*, not extra strategies.
    #
    # Trend at three different half-lives, because a trend a bot can catch at a
    # 60-bar half-life is a different trade from one at 500.
    dict(key="trend_fast_1h", interval="1h", kind="spot", price=45.0,
         fee=7.0, spread=2.0, trend_strength=0.105, trend_halflife=60),
    dict(key="trend_slow_1h", interval="1h", kind="spot", price=220.0,
         fee=6.0, spread=2.0, trend_strength=0.055, trend_halflife=500),
    dict(key="trend_mid_4h", interval="4h", kind="spot", price=8.0,
         fee=8.0, spread=3.0, trend_strength=0.095, trend_halflife=110),
    # Reversion, fast and slow.
    dict(key="revert_fast_1h", interval="1h", kind="spot", price=3.2,
         fee=8.0, spread=3.0, revert_kappa=0.022, revert_span=60),
    dict(key="revert_slow_1h", interval="1h", kind="spot", price=64.0,
         fee=7.0, spread=2.0, revert_kappa=0.008, revert_span=300),
    dict(key="revert_mid_4h", interval="4h", kind="spot", price=140.0,
         fee=7.0, spread=2.0, revert_kappa=0.030, revert_span=90),
    # A second, stronger carry market on a different seed.
    dict(key="carry_perp_1h", interval="1h", kind="perp", price=6.5,
         fee=6.0, spread=2.0, funding_beta=0.16),
    # Mixed: trend AND reversion at different horizons, which is the closest this
    # generator gets to how a real market actually misbehaves.
    dict(key="mixed_alt_1h", interval="1h", kind="spot", price=27.0,
         fee=7.0, spread=2.0, trend_strength=0.070, trend_halflife=400,
         revert_kappa=0.018, revert_span=48),
    # More decoys, to keep the universe mostly efficient. Without these, adding
    # structured markets would quietly shift the prior from "most markets have
    # nothing" to "most markets pay", which is the habit that loses money.
    dict(key="decoy_c_1h", interval="1h", kind="spot", price=75.0,
         fee=6.0, spread=2.0),
    dict(key="decoy_d_1h", interval="1h", kind="spot", price=9.0,
         fee=8.0, spread=3.0),
    dict(key="decoy_e_4h", interval="4h", kind="spot", price=1200.0,
         fee=6.0, spread=2.0),
    dict(key="decoy_f_1h", interval="1h", kind="perp", price=310.0,
         fee=5.0, spread=2.0),
]

# Factor baskets: several names sharing a common factor plus idiosyncratic returns.
# The factor is just another random walk, so betting on it is betting on direction;
# what is forecastable is the idiosyncratic drift, which is the cross-sectional
# momentum premise and the only structure `xs_momentum` can trade across a real
# cross-section. A basket with idio_trend=0 is a decoy: correlated, plausible, and
# offering a ranking strategy nothing at all.
BASKET_SPEC = []


# Cointegrated pairs: two legs sharing a price plus a stationary spread. Neither
# leg is predictable alone; the gap between them is. This is the only structure in
# the universe that a single-market strategy cannot touch, so a pairs bot found here
# is genuinely uncorrelated with every directional bot — which is what "more bots"
# has to mean if it is to mean anything.
PAIR_SPEC = [
    dict(key_a="coint_a1", key_b="coint_b1", interval="1h", kind="spot",
         price=52.0, fee=6.0, spread=2.0, spread_sd=0.028, spread_halflife=100),
    dict(key_a="coint_a2", key_b="coint_b2", interval="1h", kind="spot",
         price=410.0, fee=6.0, spread=2.0, spread_sd=0.024, spread_halflife=110),
]

STRUCTURED = {s["key"] for s in SYNTH_SPEC
              if s.get("trend_strength") or s.get("revert_kappa")
              or s.get("funding_beta")}
# Both legs of a cointegrated pair carry structure — in the spread, not in either
# leg's own direction.
STRUCTURED |= {p["key_a"] for p in PAIR_SPEC} | {p["key_b"] for p in PAIR_SPEC}
# A basket leg carries structure only when the basket has idiosyncratic drift; a
# flat basket is correlated noise and belongs with the decoys.
STRUCTURED |= {k for b in BASKET_SPEC if b.get("idio_trend")
               for k in b["keys"]}

# Structured AND worth trading after costs. The difference between the two sets is
# smallcap_alt_1h, whose 30bps round trip eats a genuine reversion edge.
REACHABLE = STRUCTURED - {"smallcap_alt_1h"}

# Bars per timeframe. Every market gets years of history, because the statistics
# downstream are useless without it. The validation slice is a quarter of whatever
# you supply, and gate 10 needs the observed Sharpe to clear its hurdle by roughly
# 1.645 standard errors — where the standard error of a Sharpe estimate is
# sqrt((1 + S^2/2) / years). Over three months that error is about 2.0, larger than
# any edge worth trading, so a short history makes the gate unpassable no matter how
# good the bot is. These lengths put every market at 5+ years.
#
# The daily market is the instructive one: a 500-bar embargo plus a 25% vault means
# it needs ~4,400 daily bars — twelve years — to be splittable at all. Supply less
# and run.py skips it with a message. That is not a bug to route around; it is what
# "validate a daily-bar strategy" actually costs.
BARS_BY_INTERVAL = {"15m": 30000, "1h": 45000, "4h": 16000, "1d": 4600}


def synthetic_universe(seed=7, bars=45000, subset=None):
    """Twenty-eight markets across six behaviours and four timeframes.

    Sixteen carry deliberately added structure (`STRUCTURED` names them); the other
    twelve are efficient apart from the regime cycle every market here has. Each
    structured market is generated from its own seed, so its edge is statistically
    independent of the rest — which is what makes several *uncorrelated* winners
    possible at all. Two bots on one market correlate above 0.8 however different
    their logic looks, so more edges needs more markets, not more strategies. A factory
    that finds "edges" spread evenly across all twenty-eight is overfitting; one
    that concentrates on the sixteen is working. That audit is the whole reason to keep a
    synthetic path — real markets never tell you which of them had an edge.

    `bars` is the reference length for a 1h market; the other timeframes scale from
    BARS_BY_INTERVAL so every market spans a comparable number of years."""
    out = {}
    scale = bars / BARS_BY_INTERVAL["1h"]
    for i, spec in enumerate(SYNTH_SPEC):
        if subset and spec["key"] not in subset:
            continue
        n = max(2000, int(BARS_BY_INTERVAL[spec["interval"]] * scale))
        out[spec["key"]] = dta.synth_market(
            spec["key"], seed=seed * 1000 + i, bars=n,
            interval=spec["interval"], kind=spec["kind"],
            start_price=spec["price"], fee_bps=spec["fee"],
            spread_bps=spec["spread"], impact_bps=max(1.0, spec["spread"]),
            funding_beta=spec.get("funding_beta", 0.0),
            trend_strength=spec.get("trend_strength", 0.0),
            trend_halflife=spec.get("trend_halflife", 200),
            revert_kappa=spec.get("revert_kappa", 0.0),
            revert_span=spec.get("revert_span", 200))

    for j, spec in enumerate(PAIR_SPEC):
        if subset and spec["key_a"] not in subset and spec["key_b"] not in subset:
            continue
        n = max(2000, int(BARS_BY_INTERVAL[spec["interval"]] * scale))
        a, b = dta.cointegrated_pair(
            spec["key_a"], spec["key_b"], seed=seed * 1000 + 500 + j,
            spread_sd=spec["spread_sd"], spread_halflife=spec["spread_halflife"],
            bars=n, interval=spec["interval"], kind=spec["kind"],
            start_price=spec["price"], fee_bps=spec["fee"],
            spread_bps=spec["spread"], impact_bps=max(1.0, spec["spread"]))
        out[spec["key_a"]] = a
        out[spec["key_b"]] = b

    for j, spec in enumerate(BASKET_SPEC):
        if subset and not any(k in subset for k in spec["keys"]):
            continue
        n = max(2000, int(BARS_BY_INTERVAL[spec["interval"]] * scale))
        legs = dta.factor_basket(
            spec["keys"], seed=seed * 1000 + 700 + j,
            factor_vol_share=spec.get("factor_vol_share", 0.6),
            idio_trend=spec.get("idio_trend", 0.0),
            idio_halflife=spec.get("idio_halflife", 200),
            bars=n, interval=spec["interval"], kind=spec["kind"],
            start_price=spec["price"], fee_bps=spec["fee"],
            spread_bps=spec["spread"], impact_bps=max(1.0, spec["spread"]))
        for leg in legs:
            out[leg.key] = leg
    return out


def null_universe(seed=99, bars=45000, count=8):
    """The strict null: markets with NO directional predictability of any kind.

    regime_drift=0 leaves the regime machinery switching volatility but not drift,
    so these series have fat tails and clustered vol — everything that makes a
    backtest look alive — and nothing whatsoever to forecast. Any bot that "passes"
    here is a false positive, by construction. run.py null-test counts them, and
    that count is the only evidence that a pass on real data means anything."""
    out = {}
    for i in range(count):
        key = f"null_{i}"
        out[key] = dta.synth_market(key, seed=seed * 1000 + i, bars=bars,
                                    interval="1h", kind="spot", phi=0.0,
                                    start_price=100.0 * (i + 1), fee_bps=6.0,
                                    spread_bps=2.0, impact_bps=2.0,
                                    regime_drift=0.0)
    return out


REAL_SPEC = [
    ("binance", "BTCUSDT", "1h", "spot"),
    ("binance", "ETHUSDT", "1h", "spot"),
    ("binance", "SOLUSDT", "1h", "spot"),
    ("binance", "BTCUSDT", "4h", "spot"),
    ("binance", "ETHUSDT", "4h", "spot"),
    ("binance", "BTCUSDT", "1d", "spot"),
    ("binance", "BTCUSDT", "1h", "perp"),
    ("binance", "ETHUSDT", "1h", "perp"),
    ("coinbase", "BTC-USD", "1h", "spot"),
    ("coinbase", "ETH-USD", "1h", "spot"),
]


def real_universe(spec=None, bars=8000, refresh=False):
    """Fetch (or load from cache) the real market universe. Raises on the first
    unreachable venue rather than falling back to synthetic — see data.py."""
    out = {}
    for venue, symbol, interval, kind in (spec or REAL_SPEC):
        key = f"{venue}:{symbol}:{interval}:{kind}"
        m = dta.fetch_market(venue, symbol, interval=interval, bars=bars,
                             kind=kind, refresh=refresh)
        m.key = key
        out[key] = m
    return out


def csv_universe(directory):
    """Load every CSV in a directory as a market. The escape hatch for anyone with
    their own data: name files `venue_SYMBOL_interval.csv` and drop them in."""
    import pathlib
    out = {}
    for path in sorted(pathlib.Path(directory).glob("*.csv")):
        m = dta.read_csv_market(path)
        out[m.key] = m
    return out


# ------------------------------------------------------------------- regimes

def regime_blocks(market, blocks=6):
    """Cut a segment into contiguous blocks and label each one, so the validator can
    ask 'does this work in more than one kind of market' instead of 'did this catch
    one enormous move'. Labels are descriptive only — the pass/fail test is on the
    per-block returns."""
    n = len(market)
    if n < blocks * 20:
        blocks = max(1, n // 20)
    edges = [int(n * k / blocks) for k in range(blocks + 1)]
    out = []
    for k in range(blocks):
        s, e = edges[k], edges[k + 1]
        if e - s < 5:
            continue
        c = market.close
        total = c[e - 1] / c[s] - 1.0
        rets = [math.log(c[i] / c[i - 1]) for i in range(s + 1, e)]
        mean = sum(rets) / len(rets) if rets else 0.0
        var = (sum((r - mean) ** 2 for r in rets) / len(rets)) if rets else 0.0
        vol = math.sqrt(var * market.bars_per_year)
        if abs(total) < 0.08:
            label = "chop"
        elif total > 0:
            label = "uptrend"
        else:
            label = "downtrend"
        if vol > 1.1:
            label += "_highvol"
        out.append({"start": s, "end": e, "label": label,
                    "market_return": total, "vol": vol})
    return out
