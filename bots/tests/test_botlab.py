#!/usr/bin/env python3
"""Falsification suite. Run: `python bots/run.py selftest`

These are not unit tests in the "does the function return 4" sense. Each one
tries to break a claim the lab makes, because a backtesting harness that is
subtly wrong is worse than no harness — it produces confident, fundable
nonsense. The load-bearing ones:

  no-lookahead      scramble the future, assert the past does not move
  buy-and-hold      a constant-long bot must reproduce the price exactly
  planted edge      the right primitive must find the structure that is there
  control market    the same primitive must find nothing where nothing exists
  ceiling           nothing may beat perfect foresight
  random bots       a batch of random genomes must not pass the gauntlet

No pytest: stdlib only, matching the sims in the repo root.
"""

from __future__ import annotations

import math
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np

from bots.botlab import (engine, gauntlet, genome, metrics, portfolio, signals,
                         state, stats)
from bots.botlab.genome import Gene, Genome, SearchSpace
from bots.botlab.markets import generate, loader, universe

_RESULTS: list[tuple[str, bool, str]] = []


def test(fn):
    _RESULTS.append((fn.__name__, None, ""))
    return fn


def _series(market="eq_index_daily", idx=1):
    return generate.cached(universe.get(market), idx)


# --------------------------------------------------------------------------- #
# rolling primitives
# --------------------------------------------------------------------------- #

def test_rolling_helpers_match_naive():
    x = np.random.default_rng(0).normal(100, 5, 300).cumsum() / 10 + 100
    for n in (2, 5, 37):
        assert np.allclose(signals.sma(x, n)[n - 1:],
                           [x[i - n + 1:i + 1].mean() for i in range(n - 1, x.size)]), "sma"
        assert np.allclose(signals.rstd(x, n)[n - 1:],
                           [x[i - n + 1:i + 1].std(ddof=1) for i in range(n - 1, x.size)]), "rstd"
        assert np.allclose(signals.rmax(x, n)[n - 1:],
                           [x[i - n + 1:i + 1].max() for i in range(n - 1, x.size)]), "rmax"
        assert np.allclose(signals.rmin(x, n)[n - 1:],
                           [x[i - n + 1:i + 1].min() for i in range(n - 1, x.size)]), "rmin"
        assert np.all(np.isnan(signals.sma(x, n)[:n - 1])), "sma warmup must be NaN"
    pw = signals.pct_in_window(x, 10)
    for i in (50, 120, 299):
        assert abs(pw[i] - float((x[i - 9:i + 1] < x[i]).mean())) < 1e-12, "pct_in_window"


def test_no_lookahead_in_signals():
    """Scramble every bar from k onward. Nothing at or before k-1 may move."""
    s = _series()
    k = 1500
    rng = np.random.default_rng(4)
    tail = np.exp(rng.normal(0, 0.05, len(s) - k)).cumprod()
    s2 = generate.Series(
        name="scrambled", spec=s.spec, seed=None,
        open=np.concatenate([s.open[:k], s.open[k:] * tail]),
        high=np.concatenate([s.high[:k], s.high[k:] * tail]),
        low=np.concatenate([s.low[:k], s.low[k:] * tail]),
        close=np.concatenate([s.close[:k], s.close[k:] * tail]),
        volume=np.concatenate([s.volume[:k], s.volume[k:] * 1.7]),
    )
    bad = []
    for name, d in signals.SIGNALS.items():
        p = genome._sample_params(d.params, np.random.default_rng(11))
        a = np.nan_to_num(d.fn(s, p))[:k]
        b = np.nan_to_num(d.fn(s2, p))[:k]
        if not np.allclose(a, b, atol=1e-9):
            bad.append(f"signal:{name}(first diff at {int(np.argmax(np.abs(a - b) > 1e-9))})")
    for name, d in signals.FILTERS.items():
        p = genome._sample_params(d.params, np.random.default_rng(12))
        a = np.nan_to_num(d.fn(s, p))[:k]
        b = np.nan_to_num(d.fn(s2, p))[:k]
        if not np.allclose(a, b, atol=1e-9):
            bad.append(f"filter:{name}")
    assert not bad, "lookahead detected in " + ", ".join(bad)


def test_no_lookahead_in_engine():
    s = _series("eq_largecap_daily", 3)
    k = 1400
    rng = np.random.default_rng(5)
    tail = np.exp(rng.normal(0, 0.06, len(s) - k)).cumprod()
    s2 = generate.Series(
        name="scrambled", spec=s.spec, seed=None,
        open=np.concatenate([s.open[:k], s.open[k:] * tail]),
        high=np.concatenate([s.high[:k], s.high[k:] * tail]),
        low=np.concatenate([s.low[:k], s.low[k:] * tail]),
        close=np.concatenate([s.close[:k], s.close[k:] * tail]),
        volume=np.concatenate([s.volume[:k], s.volume[k:]]),
    )
    rng = np.random.default_rng(6)
    space = SearchSpace(tier=3, max_genes=4, max_filters=2)
    for _ in range(12):
        g = genome.random_genome(space, rng, market="eq_largecap_daily")
        r1, r2 = engine.run(s, g), engine.run(s2, g)
        assert np.allclose(r1.pos[:k], r2.pos[:k], atol=1e-10), \
            f"engine lookahead in positions: {g.describe()}"
        assert np.allclose(r1.equity[:k], r2.equity[:k], atol=1e-10), \
            f"engine lookahead in equity: {g.describe()}"


# --------------------------------------------------------------------------- #
# engine semantics
# --------------------------------------------------------------------------- #

def test_buy_and_hold_reproduces_the_price():
    s = _series("eq_index_daily", 2)
    g = [x for x in genome.archetypes("eq_index_daily") if x.genes[0].name == "long_bias"][0]
    r = engine.run(s, g, cost_mult=0.0)
    expected = s.close[-1] / s.open[r.start]
    assert abs(r.equity[-1] / expected - 1.0) < 2e-3, \
        f"constant-long equity {r.equity[-1]:.4f} != price ratio {expected:.4f}"
    assert r.n_trades == 1, f"constant-long should trade once, traded {r.n_trades}"
    assert abs(r.exposure - 1.0) < 1e-6, f"exposure {r.exposure} should be exactly 1"


def test_never_trading_bot_is_flat():
    """`carry` on a market with no carry is identically zero, so this bot cannot
    fire. (An earlier version of this test used a 0.99 momentum threshold and
    failed — correctly: tanh does reach 0.99 on a big enough move.)"""
    s = _series()
    assert universe.get("eq_index_daily").carry_ann == 0.0
    g = Genome(market="eq_index_daily", genes=[Gene("carry", {})],
               entry_threshold=0.05, exit_threshold=0.01, sizing="fixed", base_size=1.0)
    r = engine.run(s, g)
    assert r.n_trades == 0, f"a zero signal traded {r.n_trades} times"
    assert abs(r.equity[-1] - 1.0) < 1e-12, "a bot that never trades must not move equity"
    assert metrics.evaluate(r).sharpe == 0.0
    assert metrics.evaluate(r).fitness <= 0.0, "a flat bot must not score positive fitness"

    # ... and the same must hold at a zero entry threshold, where `abs(0) >= 0` is
    # true and copysign(m, 0.0) is positive. Mutation can reach threshold 0.0, so
    # without an explicit non-zero-signal guard a bot with no opinion opens a long.
    g0 = Genome(market="eq_index_daily", genes=[Gene("carry", {})],
                entry_threshold=0.0, exit_threshold=0.0, sizing="fixed", base_size=1.0)
    r0 = engine.run(s, g0)
    assert r0.n_trades == 0, f"zero signal at zero threshold opened {r0.n_trades} trades"
    assert r0.exposure == 0.0, f"zero signal produced exposure {r0.exposure}"


def test_costs_only_ever_hurt():
    s = _series("eq_smallcap_daily", 4)
    g = Genome(market="eq_smallcap_daily", genes=[Gene("zrev", {"lb": 4})],
               entry_threshold=0.1, exit_threshold=0.02, sizing="fixed", base_size=1.0,
               rebalance_band=0.1, max_leverage=1.5)
    eqs = [engine.run(s, g, cost_mult=c).equity[-1] for c in (0.0, 1.0, 2.0, 4.0)]
    assert all(eqs[i] >= eqs[i + 1] - 1e-12 for i in range(len(eqs) - 1)), \
        f"equity must fall as costs rise, got {eqs}"
    assert eqs[0] > eqs[-1], "4x costs must cost something on an active bot"


def test_vol_targeting_lands_near_target():
    s = _series("eq_largecap_daily", 7)
    g = Genome(market="eq_largecap_daily", genes=[Gene("long_bias", {})],
               entry_threshold=0.0, exit_threshold=0.0, direction="long",
               sizing="voltarget", target_vol=0.15, max_leverage=4.0, rebalance_band=0.05)
    p = metrics.evaluate(engine.run(s, g, cost_mult=0.0))
    assert 0.10 <= p.vol_ann <= 0.22, f"asked for 15% vol, realised {p.vol_ann:.1%}"


def test_stops_can_only_exit():
    """A stop must never create exposure, only remove it."""
    s = _series("eq_index_daily", 9)
    base = Genome(market="eq_index_daily", genes=[Gene("ma_cross", {"fast": 10, "slow": 50})],
                  entry_threshold=0.1, exit_threshold=0.02, sizing="fixed", base_size=1.0)
    import dataclasses
    stopped = dataclasses.replace(base, stop_atr=1.0)
    r0, r1 = engine.run(s, base, cost_mult=0.0), engine.run(s, stopped, cost_mult=0.0)
    assert r1.time_in_market <= r0.time_in_market + 1e-9, \
        f"stop increased time in market: {r1.time_in_market:.3f} > {r0.time_in_market:.3f}"
    assert r1.stop_exits > 0, "a 1-ATR stop should have fired at least once"


# --------------------------------------------------------------------------- #
# markets
# --------------------------------------------------------------------------- #

def test_every_family_hits_its_vol_target():
    """`vol_ann` is a claim about the family, so it is tested on the median of
    several instances. Individual draws vary a lot in the fat-tailed families
    (crypto_alt spans 98%-159% around a 110% target) and that dispersion is a
    feature: real volatility is not a constant either."""
    bad = []
    for spec in universe.all_markets():
        vols = [generate.cached(spec, i).realised_vol_ann() for i in range(3, 11)]
        med = float(np.median(vols))
        if not (0.85 * spec.vol_ann <= med <= 1.15 * spec.vol_ann):
            bad.append(f"{spec.name}: asked {spec.vol_ann:.1%}, median {med:.1%}")
        if not all(0.4 * spec.vol_ann <= v <= 2.5 * spec.vol_ann for v in vols):
            bad.append(f"{spec.name}: instance vol out of sane range {min(vols):.1%}-{max(vols):.1%}")
    assert not bad, "; ".join(bad)


def test_ohlc_is_internally_consistent():
    for spec in universe.all_markets():
        s = generate.cached(spec, 5)
        assert np.all(s.high >= s.close - 1e-9) and np.all(s.high >= s.open - 1e-9), f"{spec.name} high"
        assert np.all(s.low <= s.close + 1e-9) and np.all(s.low <= s.open + 1e-9), f"{spec.name} low"
        assert np.all(s.close > 0) and np.all(s.low > 0), f"{spec.name} positive prices"


def test_controls_really_are_structureless():
    for spec in universe.controls():
        row = generate.calibration_row(spec, n_instances=6)
        assert abs(row["autocorr1"]) < 0.04, f"{spec.name} autocorr {row['autocorr1']:.3f}"
        assert abs(row["vol_ratio_20bar"] - 1.0) < 0.12, \
            f"{spec.name} 20-bar vol ratio {row['vol_ratio_20bar']:.3f} implies trend/reversion"
        assert spec.oracle_sharpe_ceiling() == 0.0


def test_planted_edge_is_findable_and_absent_in_controls():
    """The same trend bot: profitable where trend was planted, flat where it wasn't."""
    g_trend = Genome(market="futures_trend_daily",
                     genes=[Gene("ma_cross", {"fast": 20, "slow": 100})],
                     entry_threshold=0.1, exit_threshold=0.02, sizing="voltarget",
                     target_vol=0.15, max_leverage=2.0)
    real = [metrics.evaluate(engine.run(generate.cached(universe.get("futures_trend_daily"), i),
                                       g_trend, cost_mult=0.0)).sharpe for i in range(1, 9)]
    ctrl = [metrics.evaluate(engine.run(generate.cached(universe.get("control_martingale_daily"), i),
                                        g_trend, cost_mult=0.0)).sharpe for i in range(1, 9)]
    assert float(np.median(real)) > 0.25, f"planted trend not recovered: median SR {np.median(real):.2f}"
    assert abs(float(np.median(ctrl))) < 0.40, \
        f"trend bot found a trend in a random walk: median SR {np.median(ctrl):.2f}"
    assert float(np.median(real)) > float(np.median(ctrl)), "no discrimination between real and control"


def test_nothing_beats_perfect_foresight():
    bad = []
    for name in ("eq_index_daily", "futures_trend_daily", "commodity_meanrev_daily",
                 "fx_major_daily"):
        spec = universe.get(name)
        ceiling = spec.oracle_sharpe_ceiling()
        for g in genome.archetypes(name):
            srs = [metrics.evaluate(engine.run(generate.cached(spec, i), g, cost_mult=0.0)).sharpe
                   for i in range(1, 6)]
            if float(np.median(srs)) > ceiling * 1.25:
                bad.append(f"{name}: {g.describe()[:40]} SR {np.median(srs):.2f} > ceiling {ceiling:.2f}")
    assert not bad, "physically impossible performance: " + "; ".join(bad)


def test_bootstrap_null_keeps_the_distribution_and_kills_the_structure():
    """The null must preserve the return distribution and destroy the serial
    structure. Measured on the **first third** of the series: every tradeable
    family now decays, so the full-series variance ratio is diluted by a late
    stretch with little structure left in it, and the test loses its power to
    detect what it is asserting."""
    full = generate.cached(universe.get("futures_trend_daily"), 2)
    s = full.slice(0, len(full) // 3)
    rng = np.random.default_rng(3)
    lr = s.log_returns()[1:]
    acs_real, acs_null, sds = [], [], []
    for _ in range(6):
        nl = generate.bootstrap_like(s, rng, block=5)
        nlr = nl.log_returns()[1:]
        sds.append(float(nlr.std(ddof=1)))
        k = 40                      # far beyond the 5-bar block
        agg_r = lr[: (lr.size // k) * k].reshape(-1, k).sum(axis=1)
        agg_n = nlr[: (nlr.size // k) * k].reshape(-1, k).sum(axis=1)
        acs_real.append(float(agg_r.std(ddof=1) / (lr.std(ddof=1) * math.sqrt(k))))
        acs_null.append(float(agg_n.std(ddof=1) / (nlr.std(ddof=1) * math.sqrt(k))))
    assert abs(float(np.mean(sds)) / float(lr.std(ddof=1)) - 1.0) < 0.08, \
        "null changed the return distribution"
    assert float(np.mean(acs_real)) > 1.02, \
        f"the probe window has no trend to destroy (variance ratio {np.mean(acs_real):.2f})"
    assert float(np.mean(acs_null)) < float(np.mean(acs_real)), \
        f"null kept the trend: variance ratio {np.mean(acs_null):.2f} vs real {np.mean(acs_real):.2f}"


# --------------------------------------------------------------------------- #
# genome
# --------------------------------------------------------------------------- #

def test_genome_roundtrip_is_exact():
    rng = np.random.default_rng(21)
    space = SearchSpace(tier=3, max_genes=5, max_filters=3)
    s = _series()
    for _ in range(25):
        g = genome.random_genome(space, rng)
        g2 = Genome.from_dict(g.to_dict())
        assert g2.bot_id == g.bot_id, "bot_id changed across serialisation"
        assert g2.describe() == g.describe(), "describe changed across serialisation"
        if g.market == "eq_index_daily":
            assert np.allclose(engine.run(s, g).equity, engine.run(s, g2).equity), \
                "backtest changed across serialisation"


def test_inert_genes_are_dropped():
    """A `carry` gene on a market with no carry emits a constant zero: it cannot
    affect behaviour, but it does change the genome's hash. Left in, `+carry` and
    `-carry` variants of the same rule count as different strategies — the hall of
    fame once held eight behaviourally identical bots that differed only in the
    sign of an inert gene."""
    space = SearchSpace(tier=4, max_genes=4, max_filters=2)
    assert universe.get("eq_intraday_15m").carry_ann == 0.0
    assert universe.get("fx_major_daily").carry_ann != 0.0

    a = Genome(market="eq_intraday_15m",
               genes=[Gene("bollinger", {"n": 32, "k": 2.57}), Gene("carry", {}, 1.0, +1)])
    b = Genome(market="eq_intraday_15m",
               genes=[Gene("bollinger", {"n": 32, "k": 2.57}), Gene("carry", {}, 1.0, -1)])
    genome._repair(a, space)
    genome._repair(b, space)
    assert len(a.genes) == 1 and a.genes[0].name == "bollinger", "inert carry survived"
    assert a.bot_id == b.bot_id, "sign of an inert gene still changes identity"
    assert a.signature() == b.signature()

    # ... but carry is real where the market pays it, and must be kept.
    c = Genome(market="fx_major_daily",
               genes=[Gene("ma_cross", {"fast": 20, "slow": 100}), Gene("carry", {})])
    genome._repair(c, space)
    assert any(x.name == "carry" for x in c.genes), "dropped a live carry gene"

    # A genome that is nothing but an inert gene must still be a valid genome.
    d = Genome(market="eq_intraday_15m", genes=[Gene("carry", {})])
    genome._repair(d, space)
    assert len(d.genes) == 1 and d.genes[0].name != "carry"


def test_bot_id_is_stable_and_ignores_lineage():
    import dataclasses
    rng = np.random.default_rng(22)
    g = genome.random_genome(SearchSpace(tier=3), rng)
    assert g.bot_id == Genome.from_dict(g.to_dict()).bot_id
    moved = dataclasses.replace(g, generation=99, origin="mutant", parents=("abc",))
    assert moved.bot_id == g.bot_id, "lineage metadata must not change identity"


def test_mutation_and_crossover_stay_legal():
    rng = np.random.default_rng(23)
    space = SearchSpace(tier=3, max_genes=4, max_filters=2)
    pop = [genome.random_genome(space, rng) for _ in range(20)]
    s = _series()
    for i in range(300):
        a = pop[int(rng.integers(0, len(pop)))]
        b = pop[int(rng.integers(0, len(pop)))]
        child = genome.mutate(a, space, rng) if i % 2 else genome.crossover(a, b, space, rng)
        assert 1 <= len(child.genes) <= space.max_genes, f"gene count {len(child.genes)}"
        assert len(child.filters) <= space.max_filters
        assert all(g.name in signals.SIGNALS for g in child.genes)
        assert all(f.name in signals.FILTERS for f in child.filters)
        assert child.exit_threshold <= child.entry_threshold + 1e-9
        spec = universe.BY_NAME[child.market]
        assert child.max_leverage <= spec.max_leverage + 1e-9, "leverage above the market's cap"
        if not spec.allow_short:
            assert child.direction == "long"
        if child.market == "eq_index_daily":
            engine.run(s, child)        # must not raise
        pop[int(rng.integers(0, len(pop)))] = child


def test_every_signal_and_filter_runs_on_every_family():
    rng = np.random.default_rng(24)
    for spec in universe.all_markets():
        s = generate.cached(spec, 1)
        for name, d in signals.SIGNALS.items():
            v = np.asarray(d.fn(s, genome._sample_params(d.params, rng)), dtype=float)
            assert v.size == len(s), f"{name} on {spec.name}: wrong length"
            fin = v[~np.isnan(v)]
            assert fin.size == 0 or np.all(np.isfinite(fin)), f"{name} on {spec.name}: inf"
            assert fin.size == 0 or np.abs(fin).max() <= 2.0, \
                f"{name} on {spec.name}: score {np.abs(fin).max():.2f} outside [-2,2]"
        for name, d in signals.FILTERS.items():
            v = np.asarray(d.fn(s, genome._sample_params(d.params, rng)), dtype=float)
            assert v.size == len(s), f"filter {name} on {spec.name}: wrong length"


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #

def test_normal_helpers():
    for x in (-3.0, -0.5, 0.0, 0.7, 2.5):
        assert abs(stats.norm_ppf(stats.norm_cdf(x)) - x) < 1e-6, f"ppf(cdf({x})) failed"
    assert 0.0 <= stats.psr(np.random.default_rng(1).normal(0, 0.01, 500), 252.0) <= 1.0


def test_luck_bar_rises_with_the_size_of_the_search():
    bars = [stats.expected_max_sharpe(n, 0.09) for n in (10, 100, 1000, 10000)]
    assert all(bars[i] < bars[i + 1] for i in range(len(bars) - 1)), \
        f"luck bar must rise with trial count, got {bars}"
    assert bars[0] > 0.0


def test_deflated_sharpe_rejects_a_lucky_null():
    rng = np.random.default_rng(2)
    bpy = 252.0
    # A pure-noise return stream, cherry-picked as the best of 2000 trials.
    best = max((rng.normal(0, 0.01, 3000) for _ in range(60)), key=lambda r: stats.sharpe(r, bpy))
    dsr, sr0 = stats.deflated_sharpe(best, bpy, 2000, 0.09)
    assert dsr < 0.95, f"deflated Sharpe accepted noise (DSR {dsr:.3f} vs bar {sr0:.2f})"


def test_alpha_sharpe_does_not_reward_pure_beta():
    """A levered buy-and-hold bot on a drifting market must not look skilful."""
    s = _series("control_efficient_daily", 4)
    g = Genome(market="control_efficient_daily", genes=[Gene("long_bias", {})],
               entry_threshold=0.0, exit_threshold=0.0, direction="long",
               sizing="fixed", base_size=1.5, max_leverage=2.0)
    p = metrics.evaluate(engine.run(s, g, cost_mult=0.0))
    assert p.sharpe > 0.10, "sanity: levered long on a drifting market should show raw Sharpe"
    assert abs(p.alpha_sharpe) < 0.15, \
        f"alpha_sharpe {p.alpha_sharpe:+.2f} credited pure beta as skill"


# --------------------------------------------------------------------------- #
# gauntlet
# --------------------------------------------------------------------------- #

def test_every_tradeable_family_decays():
    """Decay is the default now, not an exhibit. A catalogue whose structure is
    identical at the last bar and the first flatters every strategy tested on it,
    so any tradeable family that forgot to decay is a bug."""
    stationary = [m.name for m in universe.tradeable(4) if m.is_stationary]
    assert not stationary, f"tradeable families with no edge decay: {stationary}"
    for m in universe.tradeable(4):
        prof = m.edge_profile(m.n_bars)
        assert prof[-1] < prof[0], f"{m.name}: edge profile does not fall"
        assert 0.2 <= float(np.mean(prof)) <= 0.95, \
            f"{m.name}: mean edge {np.mean(prof):.2f} is degenerate"
    # The controls have no edge to decay and must stay the simplest possible object.
    for m in universe.controls():
        assert m.is_stationary, f"{m.name}: a control should not decay"


def test_aggressive_decay_families_are_harsher_than_the_default():
    """The two named twins must be meaningfully worse than the catalogue default,
    or they are just two more markets."""
    for default, harsh in [("futures_trend_daily", "futures_trend_decay_daily"),
                           ("eq_largecap_daily", "eq_largecap_break_daily")]:
        d, h = universe.get(default), universe.get(harsh)
        md, mh = float(np.mean(d.edge_profile(d.n_bars))), float(np.mean(h.edge_profile(h.n_bars)))
        assert mh < md - 0.10, f"{harsh} mean edge {mh:.2f} not below {default} {md:.2f}"
        assert h.oracle_sharpe_ceiling() < d.oracle_sharpe_ceiling(), \
            f"{harsh} ceiling not below {default}"


def test_decay_actually_reaches_the_backtest():
    """A parameter that never changes a return is decoration. The same bot on a
    constructed stationary twin must retain materially more of its alpha."""
    import dataclasses
    from bots.botlab.markets import generate as _gen
    base = universe.get("futures_trend_daily")
    probe = dataclasses.replace(base, name="stationary_probe", edge_decay_halflife=0.0,
                                edge_decay_floor=0.0)
    universe.register(probe)
    try:
        ret = {}
        for name in ("stationary_probe", "futures_trend_daily"):
            spec = universe.get(name)
            g = Genome(market=name, genes=[Gene("ma_cross", {"fast": 20, "slow": 100})],
                       entry_threshold=0.1, exit_threshold=0.02, sizing="voltarget",
                       target_vol=0.15, max_leverage=2.0)
            e, l = [], []
            for i in range(1, 9):
                s_ = _gen.synth(spec, i)
                h = len(s_) // 2
                e.append(metrics.evaluate(engine.run(s_.slice(0, h), g, cost_mult=0.0)).alpha_sharpe)
                l.append(metrics.evaluate(engine.run(s_.slice(h, len(s_)), g, cost_mult=0.0)).alpha_sharpe)
            me, ml = float(np.median(e)), float(np.median(l))
            ret[name] = ml / me if abs(me) > 0.05 else 1.0
        assert ret["stationary_probe"] > 0.7, \
            f"stationary probe should hold its edge, retained {ret['stationary_probe']:.2f}"
        assert ret["futures_trend_daily"] < ret["stationary_probe"] - 0.3, \
            f"default decay retained {ret['futures_trend_daily']:.2f} vs stationary " \
            f"{ret['stationary_probe']:.2f} — decay is not reaching the backtest"
    finally:
        universe.unregister("stationary_probe")


def test_paired_variants_share_their_random_stream():
    """The decay curve compares one family against itself at several fade rates,
    and that comparison is only readable if the two runs are the *same market*
    with a different edge — same innovations, same jumps, same regime flips.

    Instance seeds derive from the family name, so a renamed variant silently
    draws a fresh 47-year history: with 11 families x ~50 instances that
    resampling noise is comparable in size to the decay effect being measured,
    and the curve would be reporting both. `seed_name` pins the stream. The sharp
    version of the check: a renamed-but-otherwise-identical variant must be
    byte-identical to its base when paired, and must differ when not.
    """
    import dataclasses
    from bots.botlab.markets import generate as _gen
    base = universe.get("commodity_meanrev_daily")
    paired = dataclasses.replace(base, name="paired_probe", seed_name=base.name)
    unpaired = dataclasses.replace(base, name="unpaired_probe")
    b, p, u = (_gen.synth(base, 7), _gen.synth(paired, 7), _gen.synth(unpaired, 7))
    assert np.array_equal(b.close, p.close), \
        "seed_name did not reproduce the base family's instance exactly"
    assert not np.array_equal(b.close, u.close), \
        "an unpaired rename produced the identical series — seeds are not name-derived"

    # ... and with the edge faded, the paired instance is still the same market:
    # the shocks line up bar for bar, only the predictable part shrinks.
    faded = dataclasses.replace(base, name="faded_probe", seed_name=base.name,
                                edge_decay_halflife=base.n_bars * 0.125,
                                edge_decay_floor=0.10)
    f = _gen.synth(faded, 7)
    rb, rf = np.diff(np.log(b.close)), np.diff(np.log(f.close))
    ru = np.diff(np.log(u.close))
    assert np.corrcoef(rb, rf)[0, 1] > 0.95, \
        f"paired faded instance decorrelated from its base ({np.corrcoef(rb, rf)[0, 1]:.2f})"
    assert abs(np.corrcoef(rb, ru)[0, 1]) < 0.10, \
        "an unpaired instance should be independent of the base"


def test_decay_sweep_rungs_are_a_monotone_ladder():
    """The curve's x-axis has to be an axis. Each halflife rung must plant
    strictly less total edge than the one above it, and every rung must be the
    same instrument — paired to its base family — or the sweep is comparing
    markets rather than rates."""
    from bots.botlab import decaysweep as ds
    hl_rungs = [r[0] for r in ds.RUNGS if r[2] == 0.35 or r[1] <= 0.0][:5]
    means = []
    for label in hl_rungs:
        vs = ds.build_variants(label)
        assert {v.seed_name for v in vs} == set(ds.BASE_FAMILIES), \
            f"{label}: variants are not seed-paired to their base families"
        means.append(float(np.mean([ds.mean_edge(v) for v in vs])))
    assert all(a > b for a, b in zip(means, means[1:])), \
        f"rungs are not monotone in mean planted edge: {means}"
    assert means[0] == 1.0, "the stationary rung should plant its full edge"
    # The off-axis rungs are the ones that matter most, so they must be off-axis:
    # deeper than the fastest halflife, and abrupt rather than gradual.
    deep = float(np.mean([ds.mean_edge(v) for v in ds.build_variants("hl=0.125x/f10")]))
    brk = ds.build_variants("break@45%")
    assert deep < means[-1], "the deep-floor rung is not harsher than the fast one"
    assert all(float(v.edge_profile(v.n_bars)[-1]) < 0.2 for v in brk), \
        "the break rung should leave almost nothing at the end"


def test_durability_gate_can_fire():
    """G2b is currently unexercised — on the two decaying families G1 rejects
    everything first, because G1's window is already the last 40% of the series.
    That makes it worth proving the gate is live code rather than decoration: on a
    family with a *mild* decay, which G1's threshold would wave through, the
    durability statistic must still register the fade."""
    import dataclasses
    from bots.botlab.markets import generate as _gen
    mild = dataclasses.replace(universe.get("futures_trend_daily"),
                               name="mild_decay_probe", edge_decay_halflife=5000.0,
                               edge_decay_floor=0.0, tier=1)
    universe.register(mild)
    try:
        g = Genome(market="mild_decay_probe",
                   genes=[Gene("ma_cross", {"fast": 20, "slow": 100})],
                   entry_threshold=0.1, exit_threshold=0.02, sizing="voltarget",
                   target_vol=0.15, max_leverage=2.0)
        res = [engine.run(_gen.cached(mild, i), g) for i in range(1, 13)]
        early, late, final = gauntlet._early_late_alpha(res)
        retention = (late / early) if early > 0.10 else 1.0
        assert retention < gauntlet.GauntletConfig().min_edge_retention, \
            f"durability statistic did not register a 5,000-bar halflife: " \
            f"early {early:+.2f} late {late:+.2f} retention {retention:.2f}"
        assert final <= late + 1e-9, \
            f"final quarter ({final:+.2f}) should not read stronger than the " \
            f"late half ({late:+.2f}) on a monotonically fading edge"
    finally:
        universe.unregister("mild_decay_probe")


def test_basket_peers_slice_with_their_series():
    """A basket leg carries its peers' closes in `meta`, indexed by bar. If
    `Series.slice` sliced the leg but not the peers, bar 0 of a test window would
    read peer prices from bar 0 of the *full* series — lookahead of exactly the
    train-window length, on every gate that slices. G1's window is the last 40%,
    so the gauntlet slices constantly.
    """
    from bots.botlab.markets import basket
    b = basket.BasketSpec(name="slice_probe", leg=universe.get("eq_largecap_daily"),
                          n_legs=6, n_bars=600)
    legs = basket.synth_basket(b, 1)
    lo, hi = 200, 500
    cut = legs[0].slice(lo, hi)
    peers = cut.meta[basket.PEERS_KEY]
    assert peers.shape[0] == len(cut), \
        f"peers not sliced: {peers.shape[0]} rows for a {len(cut)}-bar slice"
    assert np.array_equal(peers, legs[0].meta[basket.PEERS_KEY][lo:hi]), \
        "peers sliced to the wrong window"
    # ... and this leg's own column must still be its own closes.
    assert np.array_equal(peers[:, cut.meta["peer_col"]], cut.close), \
        "the leg's peer column no longer matches its own price"


def test_no_lookahead_in_cross_sectional_signals():
    """The scramble test, run on a basket leg with its peers attached.

    The tier-5 primitives are the only ones that read data outside their own
    series, so the standard lookahead test — which builds a bare `Series` with no
    peers — cannot see them at all: they return zeros and pass trivially. This
    scrambles the future of *every leg*, peers included, and requires the past not
    to move.
    """
    from bots.botlab.markets import basket
    b = basket.BasketSpec(name="scramble_probe", leg=universe.get("eq_largecap_daily"),
                          n_legs=8, n_bars=1200)
    legs = basket.synth_basket(b, 3)
    k = 700
    rng = np.random.default_rng(17)
    scrambled = []
    for leg in legs:
        tail = np.exp(rng.normal(0, 0.05, len(leg) - k)).cumprod()
        scrambled.append(generate.Series(
            name=leg.name + "|scr", spec=leg.spec, seed=None,
            open=np.concatenate([leg.open[:k], leg.open[k:] * tail]),
            high=np.concatenate([leg.high[:k], leg.high[k:] * tail]),
            low=np.concatenate([leg.low[:k], leg.low[k:] * tail]),
            close=np.concatenate([leg.close[:k], leg.close[k:] * tail]),
            volume=np.concatenate([leg.volume[:k], leg.volume[k:]]),
            meta=dict(leg.meta)))
    basket.attach_peers(scrambled)
    bad = []
    for name, d in signals.SIGNALS.items():
        if d.tier != 5:
            continue
        p = genome._sample_params(d.params, np.random.default_rng(21))
        a = np.nan_to_num(d.fn(legs[0], p))[:k]
        c = np.nan_to_num(d.fn(scrambled[0], p))[:k]
        assert np.any(a != 0.0), f"{name} returned all zeros — the test proves nothing"
        if not np.allclose(a, c, atol=1e-9):
            bad.append(f"{name} (first diff at {int(np.argmax(np.abs(a - c) > 1e-9))})")
    assert not bad, "lookahead in cross-sectional signals: " + ", ".join(bad)


def test_cross_sectional_signals_are_inert_without_peers():
    """On an ordinary single-instrument series they must return zeros rather than
    raise — the same convention `carry` uses on a market with no carry, so a
    cross-sectional genome that wanders onto a normal family is harmless."""
    s = _series("eq_largecap_daily", 2)
    for name, d in signals.SIGNALS.items():
        if d.tier != 5:
            continue
        out = d.fn(s, genome._sample_params(d.params, np.random.default_rng(5)))
        assert out.shape == s.close.shape, f"{name} returned the wrong shape"
        assert np.all(out == 0.0), f"{name} produced a signal with no peers present"


def test_the_basket_control_artefact_is_the_open_gap():
    """Pins F31's diagnosis so it cannot quietly change under a repair.

    A cross-sectional reversal bot earns positive gross alpha on a basket with no
    cross-sectional effect planted, and the cause is the bar model: the engine
    fills at the open, `open[t] = close[t-1]*exp(gap_frac*lr[t])` embeds part of
    the bar's own move, and a high-turnover long-short book therefore transacts at
    prices displaced the way its own signal points.

    Two things must stay true. With the gap the artefact is present — if it ever
    vanishes on its own, something else changed and the diagnosis is stale. Without
    the gap it is gone — which is what identifies the cause, and what any fix has
    to preserve while *keeping* a realistic gap.
    """
    import dataclasses
    from bots.botlab import xsection
    from bots.botlab.markets import basket
    # The two arms share `seed_name`, so they are the *same* basket with and
    # without the gap rather than two random ones — the F23 pairing lesson. The
    # unpaired version of this test measured +0.048 against a +0.147 population
    # value and would have failed for lack of power, which is a much worse
    # failure than a wrong threshold because it looks like a real result.
    leg = universe.get("eq_largecap_daily")
    out = {}
    for gf in (0.35, 0.0):
        spec = basket.basket_control(basket.BasketSpec(
            name=f"gap_probe_{gf}", leg=dataclasses.replace(leg, gap_frac=gf),
            n_legs=12, n_bars=6000, beta_disp=0.0, seed_name="gap_probe"))
        srs = []
        for i in range(1, 11):
            legs = basket.synth_basket(spec, i)
            r = xsection.run_basket(legs, xsection.xs_genome(legs[0].spec.name, lb=5),
                                    cost_mult=0.0)
            if r["ok"]:
                srs.append(r["alpha_sharpe"])
        out[gf] = float(np.mean(srs))
    assert out[0.35] - out[0.0] > 0.05, \
        f"removing the open gap did not remove the artefact (gap {out[0.35]:+.3f} vs " \
        f"no gap {out[0.0]:+.3f}) — either F31's diagnosis is wrong, or the artefact " \
        f"has changed and the quarantine needs re-deriving rather than lifting"
    assert out[0.0] < 0.06, \
        f"the no-gap arm still shows {out[0.0]:+.3f}; the gap is not the whole cause"


def test_cross_sectional_primitives_are_quarantined_from_the_search():
    """The basket control does not pass (F31): a cross-sectional reversal bot
    earns +0.11 to +0.26 gross alpha Sharpe on a basket with *no* cross-sectional
    effect planted, and four candidate causes have been ruled out without finding
    it. Until that is resolved the class must not be searchable — a strategy type
    whose negative control fails will certify artefacts, which is the F6 story
    exactly.

    The quarantine is structural rather than a flag: the primitives are tier 5
    and `SearchSpace.expanded()` caps the tier at 4, so no expansion can reach
    them. This test holds that cap in place, because raising it looks like an
    innocuous widening and would silently unquarantine them.
    """
    space = SearchSpace()
    for _ in range(15):
        space = space.expanded()
    assert space.tier <= 4, f"expansion reached tier {space.tier}; tier 5 is quarantined"
    reachable = [n for n in space.signal_pool() if signals.SIGNALS[n].tier >= 5]
    assert not reachable, f"cross-sectional primitives reachable by the search: {reachable}"
    # ... and they must still exist, or the quarantine is just deletion.
    assert any(d.tier == 5 for d in signals.SIGNALS.values()), \
        "the cross-sectional primitives have gone missing"


def test_a_rejected_argument_does_not_destroy_the_ledger():
    """`loop` rotates the ledger to `.prev` before starting a fresh run. It used
    to do that *before* validating its arguments, so `--bar-scale 0.9` — an
    argument the lab refuses on principle — still destroyed the previous run's
    backup on its way out. The ledger carries the trial counts G6's luck bar is
    built from, so losing one to a typo is not a cosmetic failure.
    """
    import tempfile
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from bots import run as runner
    with tempfile.TemporaryDirectory() as d:
        # Both files rotate together, and the *log* is the one that was actually
        # lost when this fired for real — the first version of this test only
        # covered the ledger and would have passed while the log was destroyed.
        led, log = os.path.join(d, "ledger.json"), os.path.join(d, "loop_log.md")
        for path, body in ((led, '{"sentinel": true}'), (log, "sentinel log\n")):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
        rc = runner.main(["--state", led, "loop", "--bar-scale", "0.9",
                          "--target", "1", "--log", log])
        assert rc != 0, "a bar-lowering argument should be refused"
        for path, what in ((led, "ledger"), (log, "loop log")):
            assert os.path.exists(path), f"the {what} was destroyed by a rejected argument"
            with open(path, encoding="utf-8") as fh:
                assert "sentinel" in fh.read(), f"the {what} was overwritten"
            assert not os.path.exists(path + ".prev"), f"the {what} was rotated anyway"

    # ... and the guard itself must actually be a guard in both directions.
    class A:
        min_repl_sharpe = None
        bar_scale = 1.5
    assert runner._build_config(A()) is not None, "raising the bars was refused"
    A.bar_scale = 0.999
    assert runner._build_config(A()) is None, "a bar-lowering scale was accepted"
    A.bar_scale = None
    A.min_repl_sharpe = 0.10
    assert runner._build_config(A()) is None, "a bar-lowering replication floor was accepted"


def test_default_rung_reproduces_the_shipped_catalogue():
    """The `hl=0.50x` rung is meant to *be* the shipped catalogue, restated. If it
    is not, every comparison the curve makes is against a straw catalogue and the
    row labelled "shipped" is a different market from the one that ships."""
    from bots.botlab import decaysweep as ds
    from bots.botlab.markets import generate as _gen
    for v in ds.build_variants("hl=0.50x"):
        base = universe.get(ds.base_of(v.name))
        assert v.edge_decay_halflife == base.edge_decay_halflife, \
            f"{base.name}: rung halflife {v.edge_decay_halflife} != shipped {base.edge_decay_halflife}"
        assert v.edge_decay_floor == base.edge_decay_floor
        assert v.vol_fix == base.vol_fix
        assert np.array_equal(_gen.synth(v, 3).close, _gen.synth(base, 3).close), \
            f"{base.name}: the default rung is not the same instrument"


def test_catalogue_swap_is_total_and_reversible():
    """`loop --catalogue` has to replace the tradeable catalogue *completely*.

    A candidate that wanders onto a family fading at some other rate would make
    "what a search finds at rung X" quietly untrue, and the two off-ladder twins
    (`futures_trend_decay_daily`, `eq_largecap_break_daily`) are exactly that —
    fixed points on the same axis. Controls must survive the swap, because G3
    needs them. And the catalogue must come back in its original order, since
    order decides which family the factory proposes for first.
    """
    from bots.botlab import decaysweep as ds
    before = [m.name for m in universe.all_markets()]
    with ds.use_catalogue("hl=0.125x"):
        tradeable = [m.name for m in universe.tradeable(4)]
        assert tradeable, "the swap left no tradeable families"
        assert all(n.endswith("~hl=0.125x") for n in tradeable), \
            f"families at some other decay rate survived the swap: {tradeable}"
        assert [m.name for m in universe.controls()] == \
            [m.name for m in ds._BASE_CONTROLS], "the swap disturbed the controls"
    assert [m.name for m in universe.all_markets()] == before, \
        "the catalogue was not restored exactly (order included)"


def test_final_standard_recheck_can_only_take_bots_away():
    """The closing-standard recheck exists to be conservative. A bigger search
    must never certify *more* than a smaller one, or the luck bar is not a bar."""
    import types
    from bots.botlab.markets import generate as _gen
    spec = universe.get("commodity_meanrev_daily")
    g = Genome(market=spec.name, genes=[Gene("rsi_rev", {"n": 14}, mode=-1)],
               entry_threshold=0.2, exit_threshold=0.05, sizing="proportional",
               target_vol=0.15, max_leverage=2.0)
    repl = [_gen.cached(spec, i) for i in list(universe.HOLDOUT_POOL)[:20]]
    z = 4.0
    perf = {"perm_z": z, "n_confirm_tests": 10, "var_trial_sharpe": 0.12}
    counts = []
    for burden in (1, 100, 10_000, 10_000_000):
        st = types.SimpleNamespace(
            gauntlet_runs=burden, proven=[{"genome": g.to_dict(), "verdict": {"perf": perf}}],
            var_trial_sharpe=lambda: 0.12)
        rows = gauntlet.recheck_at_final_standard(st)
        counts.append(sum(1 for r in rows if r["passed"]))
    assert counts == sorted(counts, reverse=True), \
        f"recheck is not monotone in search size: {counts}"
    assert counts[-1] == 0, "a ten-million-test burden should certify nothing here"


def test_durability_gate_sees_a_death_near_the_end():
    """The late *half* cannot resolve an edge that dies in the last 15% of the
    series: 70% of that window is still live, so the median reads healthy. This
    is not hypothetical — it certified four strategies on a catalogue broken at
    the 85% mark, the same four it certifies with no break at all.

    So the gate asks the same question again over the final quarter. This test
    holds that fix in place: on a probe whose edge is cut by 85% at 85% of the
    way through, the late-half statistic must stay comfortable while the
    final-quarter statistic must not.
    """
    import dataclasses
    from bots.botlab.markets import generate as _gen
    late_break = dataclasses.replace(universe.get("commodity_meanrev_daily"),
                                     name="late_break_probe", seed_name="commodity_meanrev_daily",
                                     edge_decay_halflife=0.0, edge_decay_floor=0.0,
                                     edge_break_at=0.85, edge_break_mult=0.15, tier=1)
    universe.register(late_break)
    try:
        # Pick the probe bot by its *early-half* alpha, a window that ends 35
        # percentage points before the break. Selecting on it therefore cannot
        # touch the late-versus-final comparison the test is about, while still
        # guaranteeing a bot with a real edge — the comparison is meaningless on
        # one that loses money in every window.
        series = [_gen.cached(late_break, i) for i in range(1, 17)]
        best, best_early = None, -9.0
        for cand in genome.archetypes("late_break_probe"):
            res = [engine.run(s, cand) for s in series]
            e = gauntlet._window_alpha(res, 0.0, 0.5)
            if e > best_early:
                best, best_early, best_res = cand, e, res
        assert best_early > 0.2, f"no archetype has an edge to lose ({best_early:+.2f})"
        early, late, final = gauntlet._early_late_alpha(best_res)
        assert late > final, \
            f"a break at 85% should hurt the final quarter more than the late " \
            f"half, got late {late:+.2f} final {final:+.2f}"
        assert late - final > 0.15, \
            f"the two windows barely differ (late {late:+.2f}, final {final:+.2f}) " \
            f"— the final-quarter leg adds nothing over the late half"
    finally:
        universe.unregister("late_break_probe")


def test_gauntlet_refuses_control_markets():
    g = Genome(market="control_martingale_daily", genes=[Gene("momentum", {"lb": 40})])
    v = gauntlet.run_gauntlet(g, gauntlet.GauntletConfig(), n_trials=10, cross_market=False)
    assert not v.passed and v.failed_at == "G0-market"


def test_gauntlet_rejects_random_bots():
    """The headline control. Random genomes must not become 'proven' bots."""
    rng = np.random.default_rng(31)
    space = SearchSpace(tier=3, max_genes=3, max_filters=2)
    cfg = gauntlet.GauntletConfig(n_perm_draws=30, n_repl_instances=12, n_stress_instances=12)
    passed = []
    for _ in range(25):
        g = genome.random_genome(space, rng)
        v = gauntlet.run_gauntlet(g, cfg, n_trials=5000, var_trial_sharpe=0.09,
                                  rng=rng, cross_market=False)
        if v.passed:
            passed.append(v)
    assert not passed, f"{len(passed)} random bots passed the gauntlet: " \
                       f"{[v.bot_id for v in passed]}"


def test_end_to_end_false_positive_rate_is_zero():
    """The headline calibration, in miniature: point the whole search at a market
    with no exploitable structure and require that it certifies nothing.

    The full-size version (`python bots/run.py fpr`) searches 2,000 candidates and
    gauntlets the best 22 of them; 0 passed, 20 died at G1. This is the evidence
    that justifies the thresholds in GauntletConfig — every gate can be argued
    about in the abstract, but this measures what they actually do."""
    from bots.botlab import calibrate
    cfg = gauntlet.GauntletConfig(n_perm_draws=30, n_repl_instances=12,
                                  n_stress_instances=12)
    r = calibrate.control_search_fpr(n_candidates=1200, n_finalists=8, seed=909,
                                     cfg=cfg, verbose=False)
    assert r["n_passed"] == 0, \
        f"the ladder certified {r['n_passed']} bots on a pure random walk: {r['passed_ids']}"
    # Zero finalists is a *stronger* result than zero passes, not a broken test:
    # it means the screen alone found nothing on a structureless market worth the
    # cost of a gauntlet. At this sample size it happens, so it is not asserted.
    assert r["best_screen_fitness"] < 0.35, \
        f"screen fitness {r['best_screen_fitness']:+.2f} on a random walk is too high; " \
        "the screen is finding structure that does not exist"


def test_gauntlet_stages_run_in_order_and_stop_at_the_first_failure():
    rng = np.random.default_rng(32)
    g = genome.random_genome(SearchSpace(), rng, market="eq_index_daily")
    v = gauntlet.run_gauntlet(g, gauntlet.GauntletConfig(n_perm_draws=20), n_trials=100,
                              rng=rng, cross_market=False)
    names = [s.name for s in v.stages]
    assert names == sorted(names), f"stages out of order: {names}"
    if not v.passed:
        assert all(s.passed for s in v.stages[:-1]) and not v.stages[-1].passed
        assert v.failed_at == v.stages[-1].name


def test_screen_only_sees_the_training_window():
    s = _series()
    tr, te = gauntlet.train_slice(s), gauntlet.test_slice(s)
    assert len(tr) + len(te) == len(s)
    assert abs(len(tr) / len(s) - gauntlet.TRAIN_FRAC) < 0.01
    assert tr.close[-1] != te.close[0], "train and test must not overlap"
    assert np.allclose(te.close, s.close[len(tr):]), "test slice misaligned"


# --------------------------------------------------------------------------- #
# plumbing
# --------------------------------------------------------------------------- #

def test_luck_bar_is_robust_to_junk_candidates():
    """A random genome generator emits structurally broken bots. They must not be
    allowed to set the deflated-Sharpe luck bar: with a population-variance
    estimator, the more junk a generator emits the harder it becomes to prove
    anything, which is exactly backwards. Measured on a real run, the population
    variance was 1.256 against an IQR-based 0.175, and the resulting luck bar of
    0.78 annual Sharpe rejected bots that had replicated on 20 fresh instances."""
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        st = state.RunState.load_or_new(os.path.join(d, "s.json"), SearchSpace())
        rng = np.random.default_rng(77)
        plausible = rng.normal(0.0, 0.30, 400)          # candidates that could be real
        for i, v in enumerate(plausible):
            st.record_trial(f"ok{i}", float(v))
        clean = st.var_trial_sharpe()
        for i in range(40):                              # broken bots: -3 to -8 Sharpe
            st.record_trial(f"junk{i}", float(rng.uniform(-8.0, -3.0)))
        polluted = st.var_trial_sharpe()
        assert abs(polluted / clean - 1.0) < 0.45, \
            f"junk moved the luck bar input from {clean:.3f} to {polluted:.3f}"
        assert 0.02 <= polluted <= 1.0


def test_state_survives_a_round_trip():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "s.json")
        st = state.RunState.load_or_new(path, SearchSpace())
        rng = np.random.default_rng(41)
        g = genome.random_genome(SearchSpace(), rng)
        st.record_trial(g.bot_id, 0.4)
        st.record_trial("deadbeef", -0.2)
        st.update_hall([state.HallEntry(genome=g.to_dict(), fitness=0.5, alpha_sharpe=0.4,
                                       sharpe=0.5, n_trades=100, generation=1)])
        st.add_proven(g, {"passed": True, "stages": []})
        st.generation = 3
        st.save()
        st2 = state.RunState.load_or_new(path, SearchSpace())
        assert st2.trials == 2 and st2.generation == 3
        assert not st2.is_new(g.bot_id), "the ledger must remember what it screened"
        assert st2.is_new("nothing-like-this")
        assert len(st2.proven) == 1 and len(st2.hall) == 1
        assert st2.hall_genomes()[0].bot_id == g.bot_id
        assert not st2.add_proven(g, {}), "the same bot must not be proven twice"


def test_real_csv_loader():
    s = _series("eq_largecap_daily", 11)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "TEST.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("Date,Open,High,Low,Close,Volume\n")
            day = 0
            for i in range(600):
                day += 1
                y, m = 2015 + day // 365, (day % 12) + 1
                fh.write(f"{y}-{m:02d}-{(day % 28) + 1:02d},{s.open[i]:.4f},{s.high[i]:.4f},"
                         f"{s.low[i]:.4f},{s.close[i]:.4f},{int(s.volume[i])}\n")
        got = loader.load_csv(path, template="eq_largecap_daily")
        assert len(got) == 600, f"loaded {len(got)} rows"
        assert np.allclose(got.close, s.close[:600], atol=1e-3)
        assert np.all(got.high >= got.close) and np.all(got.low <= got.close)
        assert got.spec.oracle_sharpe_ceiling() == 0.0, \
            "real data must not claim a known edge ceiling"
        assert got.spec.costs.spread_bps == universe.get("eq_largecap_daily").costs.spread_bps
        g = genome.archetypes("eq_largecap_daily")[1]
        assert engine.run(got, g).equity[-1] > 0.0


def test_bars_per_year_inference():
    from datetime import datetime, timedelta
    base = datetime(2020, 1, 1)
    for step, expect in ((timedelta(days=1), (252.0, 365.0)), (timedelta(hours=1), (8760.0,)),
                         (timedelta(days=7), (52.0,)), (timedelta(minutes=15), (35040.0,))):
        dates = [base + step * i for i in range(400)]
        got = loader.infer_bars_per_year(dates)
        assert any(abs(got - e) < 1.0 for e in expect), \
            f"step {step}: inferred {got}, expected one of {expect}"


def test_portfolio_reports_the_adverse_case_as_worse():
    g1 = Genome(market="futures_trend_daily", genes=[Gene("ma_cross", {"fast": 20, "slow": 100})],
                entry_threshold=0.1, exit_threshold=0.02)
    g2 = Genome(market="commodity_meanrev_daily", genes=[Gene("rsi_rev", {"n": 14})],
                entry_threshold=0.4, exit_threshold=0.05, max_hold=15)
    p = portfolio.build([g1, g2], n_instances=6)
    assert p["n_bots"] == 2
    assert p["portfolio_alpha_sharpe_adverse"] <= p["portfolio_alpha_sharpe_lab"] + 1e-9, \
        "correlated portfolio cannot beat the independent one"
    assert abs(sum(p["weights"]) - 1.0) < 1e-6


def test_factory_covers_every_unlocked_market():
    with tempfile.TemporaryDirectory() as d:
        from bots.botlab import factory
        space = SearchSpace(level=1, population=120)
        st = state.RunState.load_or_new(os.path.join(d, "s.json"), space)
        pop = factory.propose(st, space, np.random.default_rng(51))
        covered = {g.market for g in pop}
        assert covered == set(space.markets), \
            f"factory skipped {set(space.markets) - covered}"
        assert len({g.bot_id for g in pop}) == len(pop), "factory produced duplicates"


def test_expansion_only_widens():
    space = SearchSpace(level=1)
    for _ in range(6):
        nxt = space.expanded()
        assert nxt.level > space.level
        assert nxt.tier >= space.tier
        assert nxt.max_genes >= space.max_genes
        assert nxt.population >= space.population
        assert set(space.markets) <= set(nxt.markets), "expansion removed a market"
        space = nxt


# --------------------------------------------------------------------------- #

def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failures = []
    for fn in tests:
        name = fn.__name__
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as exc:
            failures.append((name, str(exc)))
            print(f"  FAIL {name}\n         {exc}")
        except Exception:                                   # noqa: BLE001
            failures.append((name, traceback.format_exc()))
            print(f"  ERR  {name}\n{traceback.format_exc()}")
    print(f"\n{len(tests) - len(failures)}/{len(tests)} passed")
    if failures:
        print("\nfailed:")
        for n, _ in failures:
            print(f"  - {n}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
