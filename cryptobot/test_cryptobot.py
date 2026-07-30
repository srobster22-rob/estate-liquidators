"""
Tests for the factory.

    python3 -m unittest cryptobot.test_cryptobot -v

The important ones are not the unit tests — they're the four properties that decide
whether any number this repo produces means anything:

    CAUSALITY      every strategy's signal at bar i is unchanged when the future is
                   deleted. Checked by truncating the market and comparing prefixes.
                   A lookahead bug is invisible in a backtest and fatal in live
                   trading; this test is the only thing standing between the two.

    COST REALITY   a bot that flips every bar loses exactly the fees it should, and
                   the impact term punishes size.

    NULL REJECTION the gauntlet rejects a strategy fitted to a random walk, and the
                   deflated-Sharpe hurdle rises with the trial count.

    REPRODUCIBLE   a genome round-trips through JSON and produces bit-identical
                   results.
"""

import json
import math
import random
import unittest

from . import backtest as bt
from . import bot as botmod
from . import data as dta
from . import indicators as ind
from . import stats
from . import strategies as st
from . import universe as uni
from . import validate as val


def a_market(seed=3, bars=2500, kind="spot", phi=0.0, interval="1h"):
    return dta.synth_market("t", seed=seed, bars=bars, interval=interval,
                            kind=kind, phi=phi)


class TestData(unittest.TestCase):
    def test_synth_shapes(self):
        m = a_market()
        self.assertEqual(len(m), 2500)
        for i in range(len(m)):
            self.assertGreaterEqual(m.high[i], max(m.open[i], m.close[i]) - 1e-9)
            self.assertLessEqual(m.low[i], min(m.open[i], m.close[i]) + 1e-9)
            self.assertGreater(m.low[i], 0.0)

    def test_timestamps_monotonic(self):
        m = a_market()
        self.assertTrue(all(m.ts[i] < m.ts[i + 1] for i in range(len(m) - 1)))

    def test_seed_is_deterministic(self):
        self.assertEqual(a_market(seed=11).close, a_market(seed=11).close)
        self.assertNotEqual(a_market(seed=11).close, a_market(seed=12).close)

    def test_phi_creates_the_autocorrelation_it_claims(self):
        """The null universe's whole purpose is that phi=0 means no exploitable
        structure. If that isn't true, the false-positive calibration is measuring
        nothing."""
        for phi, expect_positive in ((0.15, True), (-0.15, False)):
            m = a_market(seed=5, bars=6000, phi=phi)
            r = [x for x in ind.returns(m) if x is not None]
            ac = _autocorr(r)
            if expect_positive:
                self.assertGreater(ac, 0.05, f"phi={phi} gave ac={ac}")
            else:
                self.assertLess(ac, -0.05, f"phi={phi} gave ac={ac}")

        flat = [x for x in ind.returns(a_market(seed=5, bars=8000, phi=0.0))
                if x is not None]
        self.assertLess(abs(_autocorr(flat)), 0.05)

    def test_perp_has_funding_and_spot_does_not(self):
        self.assertTrue(any(f != 0 for f in a_market(kind="perp").funding))
        self.assertTrue(all(f == 0 for f in a_market(kind="spot").funding))

    def test_slice_does_not_share_indicator_cache(self):
        m = a_market()
        ind.sma(m, 50)
        child = m.slice(1000, 2000)
        self.assertEqual(child._memo, {})
        self.assertIsNone(ind.sma(child, 50)[0])


def _autocorr(xs, lag=1):
    n = len(xs) - lag
    mean = sum(xs) / len(xs)
    num = sum((xs[i] - mean) * (xs[i + lag] - mean) for i in range(n))
    den = sum((x - mean) ** 2 for x in xs)
    return num / den if den else 0.0


class TestIndicators(unittest.TestCase):
    def setUp(self):
        self.m = a_market(seed=17, bars=800)

    def test_sma_matches_naive(self):
        got = ind.sma(self.m, 30)
        for i in (29, 100, 500, 799):
            want = sum(self.m.close[i - 29:i + 1]) / 30
            self.assertAlmostEqual(got[i], want, places=9)
        self.assertIsNone(got[28])

    def test_rolling_std_matches_naive(self):
        got = ind.rolling_std(self.m, 40)
        i = 400
        window = self.m.close[i - 39:i + 1]
        mean = sum(window) / 40
        want = math.sqrt(sum((x - mean) ** 2 for x in window) / 39)
        self.assertAlmostEqual(got[i], want, places=6)

    def test_rolling_max_min_match_naive(self):
        hi = ind.rolling_max(self.m, 25, "high")
        lo = ind.rolling_min(self.m, 25, "low")
        for i in (24, 199, 799):
            self.assertAlmostEqual(hi[i], max(self.m.high[i - 24:i + 1]))
            self.assertAlmostEqual(lo[i], min(self.m.low[i - 24:i + 1]))

    def test_rsi_bounds(self):
        vals = [v for v in ind.rsi(self.m, 14) if v is not None]
        self.assertTrue(all(0.0 <= v <= 100.0 for v in vals))
        self.assertGreater(len(vals), 700)

    def test_indicators_are_causal(self):
        """Every indicator, truncated at k, must agree with the full-history version
        on bars 0..k-1."""
        k = 600
        short = self.m.slice(0, k)
        builders = [
            lambda mk: ind.sma(mk, 30), lambda mk: ind.ema(mk, 30),
            lambda mk: ind.rsi(mk, 14), lambda mk: ind.atr(mk, 20),
            lambda mk: ind.zscore(mk, 40), lambda mk: ind.roc(mk, 12),
            lambda mk: ind.rolling_max(mk, 25, "high"),
            lambda mk: ind.realized_vol(mk, 50),
            lambda mk: ind.percent_rank(mk, 60),
        ]
        for build in builders:
            full, trunc = build(self.m), build(short)
            for i in range(k):
                self.assertEqual(_r(full[i]), _r(trunc[i]),
                                 f"non-causal at bar {i}")


def _r(v):
    return None if v is None else round(v, 10)


class TestStrategiesAreCausal(unittest.TestCase):
    """The single most important test in the repo.

    For every strategy, with several random parameter draws, the signal computed on
    the first k bars must equal the first k signals computed on the whole series. If
    it doesn't, that strategy is reading the future and its backtest is fiction."""

    def test_every_strategy_every_kind(self):
        rng = random.Random(4)
        k = 900
        for kind in ("spot", "perp"):
            market = a_market(seed=23, bars=1400, kind=kind, phi=0.05)
            partner = a_market(seed=24, bars=1400, kind=kind)
            short = market.slice(0, k)
            pshort = partner.slice(0, k)
            for strat in st.REGISTRY.values():
                if kind not in strat.kinds:
                    continue
                for _ in range(4):
                    params = strat.sample(rng)
                    full = strat.signal(market, params, partner)
                    trunc = strat.signal(short, params, pshort)
                    for i in range(k):
                        self.assertEqual(
                            _r(full[i]), _r(trunc[i]),
                            f"{strat.name} looks ahead at bar {i} with {params}")

    def test_signals_are_bounded(self):
        rng = random.Random(9)
        market = a_market(seed=31, bars=900, kind="perp")
        partner = a_market(seed=32, bars=900, kind="perp")
        for strat in st.REGISTRY.values():
            for _ in range(5):
                sig = strat.signal(market, strat.sample(rng), partner)
                for v in sig:
                    if v is not None:
                        self.assertLessEqual(abs(v), 1.0 + 1e-12, strat.name)

    def test_long_only_never_shorts(self):
        rng = random.Random(12)
        market = a_market(seed=41, bars=900)
        for strat in st.REGISTRY.values():
            if "long_only" not in strat.space:
                continue
            if True not in strat.space["long_only"].options:
                continue
            params = dict(strat.sample(rng), long_only=True)
            for v in strat.signal(market, params):
                if v is not None:
                    self.assertGreaterEqual(v, 0.0, strat.name)


class TestBacktest(unittest.TestCase):
    def test_buy_hold_tracks_the_market(self):
        m = a_market(seed=51, bars=2000)
        res = bt.buy_hold(m)
        warm = bt.DEFAULT_RISK["vol_win"]
        want = m.close[-1] / m.close[warm] - 1.0
        self.assertLess(abs(res["total_return"] - want), 0.03)

    def test_fees_are_actually_charged(self):
        """A signal that flips every bar on a zero-drift market must lose roughly
        turnover x fee. If costs were free the optimiser would find that out long
        before we did."""
        m = a_market(seed=61, bars=1200, phi=0.0)
        m.fee_bps, m.spread_bps, m.impact_bps = 10.0, 0.0, 0.0
        flip = [1.0 if i % 2 == 0 else -1.0 for i in range(len(m))]
        risk = dict(bt.DEFAULT_RISK, vol_target=0.4, max_leverage=1.0)
        res = bt.run(m, flip, risk=risk)
        # Only bars 0..n-2 ever trade — the last signal has no return to earn — and
        # the first entry is charged from flat, so the turnover the engine bills is
        # |pos[0]| plus the changes across the traded range.
        traded = res.position[:len(m) - 1]
        turnover = abs(traded[0]) + sum(abs(traded[i] - traded[i - 1])
                                        for i in range(1, len(traded)))
        expected_cost = turnover * 10.0 / 1e4
        self.assertGreater(expected_cost, 0.5)
        free = bt.run(m, flip, risk=risk, cost_mult=0.0)
        drag = sum(free.net) - sum(res.net)
        self.assertAlmostEqual(drag, expected_cost, places=4)

    def test_cost_multiplier_scales_costs(self):
        m = a_market(seed=62, bars=900)
        sig = st.REGISTRY["ema_cross"].signal(
            m, {"fast": 10, "slow": 50, "deadband": 0.0, "long_only": False})
        one = bt.run(m, sig)
        two = bt.run(m, sig, cost_mult=2.0)
        self.assertLess(sum(two.net), sum(one.net))

    def test_funding_is_charged_to_longs(self):
        m = a_market(seed=63, bars=900, kind="perp")
        m.funding = [0.0005] * len(m)          # a hefty, constant rate
        long_sig = [1.0] * len(m)
        risk = dict(bt.DEFAULT_RISK, vol_target=0.4, max_leverage=1.0)
        with_f = bt.run(m, long_sig, risk=risk)
        m2 = a_market(seed=63, bars=900, kind="spot")
        without = bt.run(m2, long_sig, risk=risk)
        self.assertLess(sum(with_f.net), sum(without.net))

    def test_lag_shifts_execution(self):
        m = a_market(seed=64, bars=900, phi=0.2)
        sig = st.REGISTRY["ts_momentum"].signal(
            m, {"lookback": 10, "threshold": 0.0, "long_only": False})
        base = bt.run(m, sig)
        lagged = bt.run(m, sig, lag=1)
        self.assertNotAlmostEqual(base["sharpe"], lagged["sharpe"], places=6)

    def test_ruin_is_terminal(self):
        # A quiet random walk (so the sizer levers up) and then a bar that goes to
        # essentially zero — a delisting, a depeg, a bridge hack.
        rng = random.Random(65)
        px, closes = 100.0, []
        for _ in range(400):
            px *= math.exp(rng.gauss(0, 0.004))
            closes.append(px)
        closes += [px * 1e-6] * 200
        m = a_market(seed=65, bars=600)
        m.close = closes
        m.open = list(closes)
        m.high = [c * 1.001 for c in closes]
        m.low = [c * 0.999 for c in closes]
        m._memo = {}
        res = bt.run(m, [1.0] * len(m),
                     risk=dict(bt.DEFAULT_RISK, max_leverage=3.0))
        self.assertTrue(res.ruined)
        self.assertEqual(res.equity[-1], 0.0)
        self.assertEqual(res["cagr"], -1.0)

    def test_metrics_sanity(self):
        m = a_market(seed=66, bars=1500)
        res = bt.buy_hold(m)
        met = res.metrics
        self.assertAlmostEqual(res.equity[-1] - 1.0, met["total_return"], places=9)
        self.assertGreaterEqual(met["max_dd"], 0.0)
        self.assertLessEqual(met["max_dd"], 1.0)
        self.assertGreaterEqual(met["hit_rate"], 0.0)
        self.assertLessEqual(met["hit_rate"], 1.0)

    def test_vol_targeting_stabilises_risk(self):
        """Two markets with very different vol, sized to the same target, should end
        up with similar realised vol. That is the point of the sizer."""
        quiet = dta.synth_market("q", seed=71, bars=3000, phi=0.0)
        loud = dta.synth_market("l", seed=72, bars=3000, phi=0.0)
        loud.close = [c for c in loud.close]
        risk = dict(bt.DEFAULT_RISK, vol_target=0.30, max_leverage=10.0)
        a = bt.run(quiet, [1.0] * len(quiet), risk=risk)
        b = bt.run(loud, [1.0] * len(loud), risk=risk)
        self.assertLess(abs(a["ann_vol"] - b["ann_vol"]), 0.25)


class TestStats(unittest.TestCase):
    def test_norm_ppf_roundtrip(self):
        for p in (0.01, 0.1, 0.5, 0.9, 0.975, 0.999):
            self.assertAlmostEqual(stats.norm_cdf(stats.norm_ppf(p)), p, places=6)

    def test_expected_max_sharpe_grows_with_trials(self):
        a = stats.expected_max_sharpe(10, 0.5)
        b = stats.expected_max_sharpe(1000, 0.5)
        c = stats.expected_max_sharpe(100000, 0.5)
        self.assertLess(a, b)
        self.assertLess(b, c)
        self.assertGreater(b, 1.0)

    def test_expected_max_matches_simulation(self):
        """Sanity-check the closed form against brute force: draw N Sharpes from a
        zero-mean normal, take the max, average over many replications."""
        rng = random.Random(2)
        n, reps = 200, 400
        sigma = 0.5
        sim = sum(max(rng.gauss(0, sigma) for _ in range(n))
                  for _ in range(reps)) / reps
        closed = stats.expected_max_sharpe(n, sigma)
        self.assertLess(abs(sim - closed), 0.15, f"{sim} vs {closed}")

    def test_deflated_sharpe_falls_as_trials_rise(self):
        met = {"bars": 4000, "sharpe": 1.6, "skew": 0.0, "kurtosis": 3.0}
        few, _ = stats.deflated_sharpe(met, 5, 0.5, 8760)
        many, _ = stats.deflated_sharpe(met, 200000, 0.5, 8760)
        self.assertGreater(few, many)
        self.assertLess(many, 0.95)

    def test_bootstrap_rejects_noise_and_accepts_signal(self):
        rng = random.Random(3)
        noise = [rng.gauss(0, 0.01) for _ in range(2000)]
        self.assertGreater(stats.bootstrap_pvalue(noise, 200, seed=1), 0.05)
        edge = [rng.gauss(0.0015, 0.01) for _ in range(2000)]
        self.assertLess(stats.bootstrap_pvalue(edge, 200, seed=1), 0.05)

    def test_matched_random_signals_match_the_profile(self):
        rng = random.Random(4)
        pos = [0.0] * 100 + [1.0] * 300 + [0.0] * 100 + [-1.0] * 200
        paths = stats.matched_random_signals(pos, 40, rng)
        want_active = sum(1 for p in pos if p != 0) / len(pos)
        got = sum(sum(1 for v in path if v != 0) / len(path)
                  for path in paths) / len(paths)
        self.assertLess(abs(got - want_active), 0.15)


class TestUniverse(unittest.TestCase):
    def test_split_is_ordered_and_embargoed(self):
        m = a_market(seed=81, bars=9000)
        seg = uni.split(m)
        self.assertLess(seg.train.ts[-1], seg.validation.ts[0])
        self.assertLess(seg.validation.ts[-1], seg.vault.ts[0])
        gap = seg.validation.ts[0] - seg.train.ts[-1]
        self.assertGreaterEqual(gap, uni.EMBARGO_BARS * 3600 * 0.9)

    def test_split_refuses_short_history(self):
        with self.assertRaises(ValueError):
            uni.split(a_market(seed=82, bars=800))

    def test_synthetic_universe_is_mostly_edgeless(self):
        specs = uni.SYNTH_SPEC
        edgeless = len(specs) - len(uni.STRUCTURED)
        self.assertGreaterEqual(edgeless / len(specs), 0.5,
                                "the universe should be mostly efficient markets")

    def test_null_universe_has_no_directional_structure(self):
        """The strict null must have zero drift in every regime, or the
        false-positive count measures nothing. Checked at the generator level and
        confirmed by the realised drift of the series."""
        for m in uni.null_universe(bars=6000, count=3).values():
            self.assertEqual(m.truth["regime_drift"], 0.0)
            self.assertEqual(m.truth["phi"], 0.0)
            self.assertEqual(m.truth["trend_strength"], 0.0)
            self.assertEqual(m.truth["revert_kappa"], 0.0)
            rets = [x for x in ind.returns(m) if x is not None]
            mean = sum(rets) / len(rets)
            sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / len(rets))
            t_stat = mean / (sd / math.sqrt(len(rets)))
            self.assertLess(abs(t_stat), 4.0, "null market has a drift")

    def test_structured_markets_carry_a_reachable_edge(self):
        """The other half of the calibration: on the five structured markets, a
        plain unfitted bot with no parameter search should clear costs. If it can't,
        the universe's 'edge' is unreachable and a factory that finds nothing there
        is being told the truth by a rigged test."""
        mkts = uni.synthetic_universe(bars=30000)
        probes = (
            ("ts_momentum", {"lookback": 200, "threshold": 0.0, "long_only": False}),
            ("ts_momentum", {"lookback": 400, "threshold": 0.0, "long_only": False}),
            ("bollinger_fade", {"window": 96, "entry_z": 1.5, "exit_z": 0.0,
                                "long_only": False}),
            ("carry_funding", {"avg_win": 24, "enter": 0.2, "long_only": False}),
        )
        reachable = 0
        for key in uni.REACHABLE:
            m = mkts[key]
            best = -9.0
            for name, params in probes:
                strat = st.REGISTRY[name]
                if m.kind not in strat.kinds:
                    continue
                res = bt.run(m, strat.signal(m, params),
                             risk=dict(bt.DEFAULT_RISK, vol_target=0.35,
                                       max_leverage=2.0))
                best = max(best, res["sharpe"])
            if best > 0.8:
                reachable += 1
        self.assertGreaterEqual(reachable, 3,
                                "fewer than 3 of the reachable markets are "
                                "reachable by an unfitted probe")

    def test_the_high_cost_market_is_correctly_unreachable(self):
        """smallcap_alt_1h has a real reversion edge behind 30bps of round-trip
        cost. A probe that finds it profitable means the cost model has gone soft,
        and every other result in the repo gets more optimistic with it."""
        m = uni.synthetic_universe(bars=30000)["smallcap_alt_1h"]
        best = -9.0
        for w in (48, 96, 200, 400):
            res = bt.run(m, st.REGISTRY["bollinger_fade"].signal(
                m, {"window": w, "entry_z": 1.5, "exit_z": 0.0,
                    "long_only": False}),
                risk=dict(bt.DEFAULT_RISK, vol_target=0.35, max_leverage=2.0))
            best = max(best, res["sharpe"])
        self.assertLess(best, 0.8, "costs should have eaten this edge")

    def test_regime_blocks_partition_the_segment(self):
        m = a_market(seed=83, bars=3000)
        blocks = uni.regime_blocks(m, 6)
        self.assertEqual(len(blocks), 6)
        self.assertEqual(blocks[0]["start"], 0)
        for a, b in zip(blocks, blocks[1:]):
            self.assertEqual(a["end"], b["start"])


class TestBot(unittest.TestCase):
    def make(self):
        return botmod.Bot("t", "ema_cross",
                          {"fast": 12, "slow": 60, "deadband": 0.001,
                           "long_only": False},
                          dict(bt.DEFAULT_RISK))

    def test_genome_roundtrips(self):
        b = self.make()
        clone = botmod.Bot.from_dict(json.loads(json.dumps(b.to_dict())))
        self.assertEqual(b.fingerprint(), clone.fingerprint())
        m = a_market(seed=91, bars=1500)
        self.assertEqual(b.run(m)["sharpe"], clone.run(m)["sharpe"])

    def test_fingerprint_is_sensitive(self):
        b = self.make()
        other = botmod.Bot("t", "ema_cross", dict(b.params, fast=13), b.risk)
        self.assertNotEqual(b.fingerprint(), other.fingerprint())

    def test_fitness_punishes_ruin_and_inactivity(self):
        m = a_market(seed=92, bars=1500)
        live = self.make().run(m)
        self.assertLess(botmod.fitness(live, min_trades=10_000), -5.0)

    def test_alpha_sharpe_strips_market_exposure(self):
        """A bot that is simply long the market must score near zero on alpha, and a
        bot with genuine timing must keep most of its Sharpe. This is the in-sample
        proxy that keeps the search pointed where the gauntlet is looking."""
        m = a_market(seed=94, bars=4000, phi=0.0)
        mkt = ind.simple_returns(m)
        risk = dict(bt.DEFAULT_RISK, vol_target=0.35, max_leverage=1.0)

        always_long = bt.run(m, [1.0] * len(m), risk=risk)
        self.assertLess(abs(botmod.alpha_sharpe(always_long, mkt)), 0.4)

        # A cheating bot that knows tomorrow: all timing, and its market beta is
        # incidental. Used ONLY here, to prove alpha_sharpe can see timing at all.
        # position[i] earns the return from bar i to i+1, so the oracle at bar i
        # is the sign of mkt[i+1]. Off-by-one here and the "cheat" becomes plain
        # momentum, which on a random walk just pays fees.
        oracle = [1.0 if mkt[i + 1] > 0 else -1.0
                  for i in range(len(m) - 1)] + [0.0]
        cheat = bt.run(m, oracle, risk=risk)
        self.assertGreater(botmod.alpha_sharpe(cheat, mkt), 3.0)

    def test_fitness_takes_the_worse_of_raw_and_alpha(self):
        m = a_market(seed=95, bars=4000, phi=0.0)
        mkt = ind.simple_returns(m)
        res = bt.run(m, [1.0] * len(m),
                     risk=dict(bt.DEFAULT_RISK, vol_target=0.35,
                               max_leverage=1.0))
        raw = botmod.fitness(res, min_trades=0)
        with_alpha = botmod.fitness(res, min_trades=0, market_returns=mkt)
        self.assertLessEqual(with_alpha, raw + 1e-9)

    def test_ensemble_averages_children(self):
        m = a_market(seed=93, bars=1200)
        kids = [{"strategy": "ema_cross",
                 "params": {"fast": 10, "slow": 50, "deadband": 0.0,
                            "long_only": True}},
                {"strategy": "ts_momentum",
                 "params": {"lookback": 20, "threshold": 0.0, "long_only": True}}]
        ens = botmod.Bot("t", "ensemble", {}, dict(bt.DEFAULT_RISK),
                         children=kids)
        sig = ens.signal(m)
        a = st.REGISTRY["ema_cross"].signal(m, kids[0]["params"])
        b = st.REGISTRY["ts_momentum"].signal(m, kids[1]["params"])
        for i in range(len(sig)):
            if sig[i] is not None:
                self.assertAlmostEqual(sig[i], (a[i] + b[i]) / 2)


class TestGauntlet(unittest.TestCase):
    """The gauntlet has one job: reject things. These tests check that it does."""

    def test_rejects_a_strategy_mined_on_a_random_walk(self):
        market = dta.synth_market("rw", seed=101, bars=9000, phi=0.0)
        seg = uni.split(market)
        rng = random.Random(7)
        best, best_fit = None, -1e9
        strat = st.REGISTRY["ema_cross"]
        for _ in range(120):                       # mine hard on the train slice
            params = strat.sample(rng)
            cand = botmod.Bot("rw", "ema_cross", params, dict(bt.DEFAULT_RISK))
            fit = botmod.fitness(cand.run(seg.train))
            if fit > best_fit:
                best, best_fit = cand, fit
        report = val.gauntlet(best, seg, oos_looks=20, dispersion=0.6, seed=1)
        self.assertFalse(report.passed,
                         f"gauntlet passed a bot mined on noise: {report.render()}")

    def test_rejects_a_bot_that_only_beats_buy_and_hold_by_being_long(self):
        market = dta.synth_market("bull", seed=102, bars=9000, phi=0.0)
        seg = uni.split(market)
        always_long = botmod.Bot("bull", "ts_momentum",
                                 {"lookback": 10, "threshold": 0.0,
                                  "long_only": True},
                                 dict(bt.DEFAULT_RISK))
        report = val.gauntlet(always_long, seg, oos_looks=10, dispersion=0.6, seed=2)
        self.assertFalse(report.passed)

    def test_trial_count_can_flip_a_verdict(self):
        """The same bot, same data, more trials burned: the deflated-Sharpe gate has
        to get stricter. This is the property that makes 'loop until profitable'
        legitimate rather than circular."""
        met = {"bars": 3000, "sharpe": 1.9, "skew": 0.0, "kurtosis": 3.0}
        low, hurdle_low = stats.deflated_sharpe(met, 20, 0.6, 8760)
        high, hurdle_high = stats.deflated_sharpe(met, 500000, 0.6, 8760)
        self.assertGreater(low, high)
        self.assertGreater(hurdle_high, hurdle_low)

    def test_gates_run_in_order_and_short_circuit(self):
        market = dta.synth_market("x", seed=103, bars=9000, phi=0.0)
        seg = uni.split(market)
        dud = botmod.Bot("x", "ema_cross",
                         {"fast": 300, "slow": 400, "deadband": 0.5,
                          "long_only": True}, dict(bt.DEFAULT_RISK))
        report = val.gauntlet(dud, seg, oos_looks=5, dispersion=0.6, seed=3)
        self.assertFalse(report.passed)
        self.assertEqual(report.gates[0].name, "sanity")
        self.assertEqual(report.first_failure, report.gates[-1].name)

    def test_a_genuinely_predictable_market_can_pass_the_early_gates(self):
        """A market with a huge, obvious edge should get a matching bot past the
        performance gates. If nothing can EVER pass, the gauntlet isn't strict —
        it's broken, which is just as useless."""
        market = dta.synth_market("easy", seed=104, bars=9000, phi=0.30,
                                  fee_bps=1.0, spread_bps=0.5, impact_bps=0.5)
        seg = uni.split(market)
        cand = botmod.Bot("easy", "ts_momentum",
                          {"lookback": 3, "threshold": 0.0, "long_only": False},
                          dict(bt.DEFAULT_RISK, vol_target=0.3, max_leverage=2.0))
        report = val.gauntlet(cand, seg, oos_looks=5, dispersion=0.6, seed=4)
        names = [g.name for g in report.gates if g.passed]
        self.assertIn("oos_profit", names, report.render())
        self.assertIn("beats_benchmark", names, report.render())


if __name__ == "__main__":
    unittest.main()
