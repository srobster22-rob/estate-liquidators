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

Between segments sits an EMBARGO of dropped bars. A strategy with a 400-bar lookback
whose validation window starts one bar after training ends is still, in effect,
reading the training data — the embargo has to be at least as long as the longest
lookback any strategy uses.

The vault burn counter exists because out-of-sample data is a consumable. Test
against it twenty times and it is training data with extra steps; the counter makes
that visible instead of letting it happen quietly.
"""

import math

from . import data as dta

EMBARGO_BARS = 500          # ≥ the longest lookback in strategies.py


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
    # Five markets carry added structure, nine carry none, and the magnitudes were
    # not guessed — they were calibrated by probing each market with plain, unfitted
    # bots and adjusting until a hand-written momentum, fade or carry rule reached
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
]

STRUCTURED = {s["key"] for s in SYNTH_SPEC
              if s.get("trend_strength") or s.get("revert_kappa")
              or s.get("funding_beta")}

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
    """Fourteen markets across five behaviours and four timeframes.

    Five carry deliberately added structure (`STRUCTURED` names them); the other
    nine are efficient apart from the regime cycle every market here has. A factory
    that finds "edges" spread evenly across all fourteen is overfitting; one that
    concentrates on the five is working. That audit is the whole reason to keep a
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
