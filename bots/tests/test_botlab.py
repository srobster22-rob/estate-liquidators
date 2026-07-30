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
    s = generate.cached(universe.get("futures_trend_daily"), 2)
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
