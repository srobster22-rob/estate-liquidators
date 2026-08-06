"""The gauntlet: seven gates between "made money in a backtest" and "proven".

A search that generates thousands of strategies will hand you a beautiful
equity curve every single time, on data with no edge in it whatsoever. So the
burden of proof sits here, and it is deliberately brutal. Each gate answers one
specific way a backtest lies:

  G1  OOS WINDOW    Did it work on bars the search never scored? (in-sample fit)
  G2  REPLICATION   Does it work on 20 *fresh instances* of its market, never
                    touched during the search? (instance-specific luck)
  G2b DURABILITY    Is the edge still there in the second half of each instance,
                    or did it fade? (crowded, published, arbitraged anomalies)
  G3  CONTROLS      Does it stay flat on a pure random walk, where profit is
                    impossible by construction? (harness bug / artifact mining)
  G4  COST STRESS   Does it survive 2x costs, 3x costs, and one extra bar of
                    execution delay? (frictionless fantasy, latency arbitrage)
  G5  PERMUTATION   Does it beat its own block-bootstrapped null at p<=0.01?
                    (return distribution masquerading as timing skill)
  G6  DEFLATED SR   Does it beat the best-by-luck Sharpe implied by the *size of
                    the entire search*? (multiple testing / p-hacking)
  G7  STRESS POOL   Does it replicate a second time, on a third disjoint pool?
                    (the gates above, re-run as a confirmation)

A bot that passes all eight is marked PROVEN — which here means precisely
"survived G1-G7 on this market model at these costs", and nothing more. See
bots/README.md for what that does and does not license.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from . import engine, metrics, stats
from .genome import Genome
from .markets import generate, universe
from .markets.series import Series

TRAIN_FRAC = 0.60           # the search only ever scores the first 60% of a series


@dataclass
class GauntletConfig:
    """Every threshold in one place, because these *are* the standard of proof.

    The Sharpe bars are set from `run.py calibrate`: the best textbook archetype
    on the best-behaved family reaches ~0.5-0.8 net alpha Sharpe, so demanding
    0.35 on replication is demanding "as good as a well-implemented classic",
    not "too good to be true".
    """

    min_oos_alpha_sr: float = 0.25
    min_repl_alpha_sr: float = 0.35
    min_repl_pos_frac: float = 0.70
    min_late_alpha_sr: float = 0.25      # G2b: edge must still be there at the end
    min_edge_retention: float = 0.50     # G2b: ... and not be a fraction of its start
    min_stress_alpha_sr: float = 0.28
    min_stress_pos_frac: float = 0.65
    max_drawdown: float = 0.35
    min_trades: int = 30
    max_control_alpha_sr: float = 0.30
    cost_stress_2x_min: float = 0.15
    cost_stress_3x_min: float = 0.0
    delay_stress_min: float = 0.10
    perm_p_max: float = 0.01
    min_dsr: float = 0.95
    family_wise_p_max: float = 0.05

    n_oos_instances: int = 8
    n_repl_instances: int = 20
    n_control_instances: int = 10
    n_stress_instances: int = 20
    n_perm_instances: int = 5
    n_perm_draws: int = 120          # >= 100 so that p <= 0.01 is attainable
    perm_block: int = 5              # keeps 5-bar structure in the null: conservative

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Stage:
    name: str
    passed: bool
    detail: str
    stats: dict = field(default_factory=dict)


@dataclass
class Verdict:
    bot_id: str
    market: str
    passed: bool
    failed_at: str | None
    stages: list[Stage]
    perf: dict = field(default_factory=dict)
    cross_market: dict = field(default_factory=dict)
    n_backtests: int = 0
    describe: str = ""

    def summary(self) -> str:
        tag = "PROVEN" if self.passed else f"failed@{self.failed_at}"
        sr = self.perf.get("repl_alpha_sr", 0.0)
        return f"{self.bot_id} {self.market:<24} {tag:<18} replSR {sr:+.2f}"

    def to_dict(self) -> dict:
        return {
            "bot_id": self.bot_id, "market": self.market, "passed": self.passed,
            "failed_at": self.failed_at, "n_backtests": self.n_backtests,
            "describe": self.describe, "perf": self.perf,
            "cross_market": self.cross_market,
            "stages": [asdict(s) for s in self.stages],
        }


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def train_slice(s: Series) -> Series:
    return s.slice(0, int(len(s) * TRAIN_FRAC), tag="|train")


def test_slice(s: Series) -> Series:
    return s.slice(int(len(s) * TRAIN_FRAC), len(s), tag="|test")


def instances(market: str, pool, n: int) -> list[Series]:
    spec = universe.get(market)
    return [generate.cached(spec, i) for i in list(pool)[:n]]


def _panel(series: list[Series], g: Genome, cost_mult: float = 1.0,
           exec_delay: int = 1) -> tuple[metrics.Perf, list[metrics.Perf]]:
    """(pooled perf, per-instance perfs)."""
    return _panel_raw(series, g, cost_mult, exec_delay)[:2]


def _panel_raw(series: list[Series], g: Genome, cost_mult: float = 1.0,
               exec_delay: int = 1):
    """(pooled perf, per-instance perfs, raw results). The durability gate needs
    the raw return series, and re-running to get them would double G2's cost."""
    results = [engine.run(s, g, cost_mult=cost_mult, exec_delay=exec_delay) for s in series]
    per = [metrics.evaluate(r) for r in results]
    return metrics.pooled_perf(results), per, results


def _early_late_alpha(results) -> tuple[float, float]:
    """Median alpha Sharpe over the first and second half of each run.

    Computed by splitting the *return series already produced by G2*, not by
    re-running on sliced data: one continuous run with no warmup discontinuity at
    the midpoint, and no extra backtests.
    """
    early, late = [], []
    for res in results:
        r = res.active_ret
        m = res.active_market_ret[: r.size]
        k = r.size // 2
        if k < 32:
            continue
        early.append(metrics.alpha_sharpe(r[:k], m[:k], res.bars_per_year))
        late.append(metrics.alpha_sharpe(r[k:], m[k:], res.bars_per_year))
    if not early:
        return 0.0, 0.0
    return float(np.median(early)), float(np.median(late))


SCREEN_QUANTILE = 0.40          # score on the bad instances, not the average one
COMPLEXITY_PENALTY = 0.04       # per gene/filter beyond the first
SCREEN_INSTANCES = 24           # see the second calibration in FINDINGS.md F8


def screen(g: Genome, config: GauntletConfig, n_instances: int = SCREEN_INSTANCES) -> metrics.Perf:
    """The cheap pre-filter the loop uses on every candidate: train window only,
    search pool only. Nothing here is evidence — it only decides who gets tested.

    The statistic is deliberately *not* pooled performance. Ranking 640
    candidates a generation by their pooled screen fitness selects whichever bot
    got the luckiest instance: in the first run of this loop, screen fitness
    climbed 0.45 -> 1.19 over 17 generations while 76% of finalists died at G1 and
    nothing was ever proven. Meanwhile a textbook RSI-reversion bot that *does*
    pass all seven gates never made the finalist list, because its honest 0.5
    could not outbid the overfit 1.2s.

    So the score is a lower quantile of per-instance fitness — what the bot
    achieves on its *worst* instances — minus a complexity charge. Both are priors
    on what generalises, applied at selection time where priors belong, rather
    than being smuggled into the gates where the standard of proof lives.

    Instance count, not the choice of quantile, turned out to be what binds. The
    screen runs on 1800-bar train slices, where a single instance's Sharpe is very
    noisy, so a low quantile over few instances measures noise. Measured against
    holdout replication (FINDINGS.md F8, second table): at 8 instances precision
    among the top 18 is 17-22% and a bot known to pass all seven gates ranks
    24th-48th and never makes the cut. At 24 instances with q=0.40 precision is
    44% and that bot ranks 2nd — against a base rate of 1.8%.
    """
    series = [train_slice(s) for s in instances(g.market, universe.SEARCH_POOL, n_instances)]
    pooled, per = _panel(series, g)
    if not per:
        return pooled
    fits = np.asarray([p.fitness for p in per], dtype=float)
    srs = np.asarray([p.alpha_sharpe for p in per], dtype=float)
    complexity = COMPLEXITY_PENALTY * (max(len(g.genes) - 1, 0) + len(g.filters))
    pooled.fitness = float(np.quantile(fits, SCREEN_QUANTILE)) - complexity
    pooled.alpha_sharpe = float(np.median(srs))
    return pooled


# --------------------------------------------------------------------------- #
# the ladder
# --------------------------------------------------------------------------- #

def run_gauntlet(g: Genome, config: GauntletConfig | None = None,
                 n_trials: int = 1, var_trial_sharpe: float = 0.25,
                 rng: np.random.Generator | None = None,
                 cross_market: bool = True, n_confirm_tests: int | None = None) -> Verdict:
    """Run the ladder.

    `n_trials` is every candidate the search has ever screened.
    `n_confirm_tests` is how many candidates have ever been tested against the
    *confirmation* pools (i.e. how many gauntlets have run) — and that, not
    `n_trials`, is the right multiple-testing denominator for G6. See the G6
    comment for why.
    """
    cfg = config or GauntletConfig()
    rng = rng or np.random.default_rng(12345)
    stages: list[Stage] = []
    perf: dict = {}
    n_bt = 0

    spec = universe.BY_NAME.get(g.market)
    if spec is None or spec.control:
        stages.append(Stage("G0-market", False, f"{g.market} is not a tradeable family"))
        return Verdict(g.bot_id, g.market, False, "G0-market", stages, describe=g.describe())

    def fail(name: str) -> Verdict:
        return Verdict(g.bot_id, g.market, False, name, stages, perf=perf,
                       n_backtests=n_bt, describe=g.describe())

    # ---- G1: out-of-sample window on the search instances -------------------
    oos = [test_slice(s) for s in instances(g.market, universe.SEARCH_POOL, cfg.n_oos_instances)]
    pooled, per = _panel(oos, g)
    n_bt += len(oos)
    pos = float(np.mean([p.alpha_sharpe > 0 for p in per])) if per else 0.0
    ok = (pooled.alpha_sharpe >= cfg.min_oos_alpha_sr and pooled.n_trades >= cfg.min_trades
          and not pooled.ruined and pos >= 0.5)
    perf.update(oos_alpha_sr=pooled.alpha_sharpe, oos_sr=pooled.sharpe,
                oos_trades=pooled.n_trades, oos_pos_frac=pos)
    stages.append(Stage("G1-oos", ok,
                        f"alphaSR {pooled.alpha_sharpe:+.2f} (need {cfg.min_oos_alpha_sr:+.2f}), "
                        f"{pooled.n_trades} trades, {pos:.0%} instances positive",
                        pooled.to_dict()))
    if not ok:
        return fail("G1-oos")

    # ---- G2: replication on untouched instances -----------------------------
    repl = instances(g.market, universe.HOLDOUT_POOL, cfg.n_repl_instances)
    pooled, per, repl_raw = _panel_raw(repl, g)
    n_bt += len(repl)
    srs = np.array([p.alpha_sharpe for p in per])
    med = float(np.median(srs))
    pos = float(np.mean(srs > 0))
    ruins = int(sum(1 for p in per if p.ruined))
    # Drawdown is a *per-instance* property. The pooled curve chains 20 lifetimes
    # of compounding end to end, so its drawdown is an artefact of the ordering:
    # it read -99% for strategies whose every individual run drew down 25%.
    dds = np.array([p.max_dd for p in per])
    dd_med = float(np.median(dds))
    dd_worst = float(dds.min())
    ok = (med >= cfg.min_repl_alpha_sr and pos >= cfg.min_repl_pos_frac
          and -dd_med <= cfg.max_drawdown and -dd_worst <= cfg.max_drawdown * 1.6
          and ruins == 0 and pooled.alpha_sharpe >= cfg.min_repl_alpha_sr * 0.8)
    perf.update(repl_alpha_sr=med, repl_pooled_alpha_sr=pooled.alpha_sharpe,
                repl_sr=pooled.sharpe, repl_pos_frac=pos, repl_max_dd=dd_med,
                repl_max_dd_worst=dd_worst, repl_cagr=pooled.cagr,
                repl_trades=pooled.n_trades, repl_ruins=ruins,
                repl_sr_iqr=float(np.subtract(*np.percentile(srs, [75, 25]))))
    stages.append(Stage("G2-replication", ok,
                        f"median alphaSR {med:+.2f} (need {cfg.min_repl_alpha_sr:+.2f}), "
                        f"{pos:.0%} of {len(repl)} instances positive "
                        f"(need {cfg.min_repl_pos_frac:.0%}), median DD {dd_med:.1%} "
                        f"/ worst {dd_worst:.1%} (allowed {-cfg.max_drawdown:.0%}"
                        f"/{-cfg.max_drawdown * 1.6:.0%}), {ruins} wipeouts",
                        pooled.to_dict()))
    if not ok:
        return fail("G2-replication")

    # ---- G2b: durability — does the edge still exist late in the series? -----
    # Every synthetic family was stationary until this gate existed, which made
    # "passed the gauntlet" conditional on an assumption real markets violate:
    # anomalies get crowded, published and arbitraged, and the survivors shrink.
    # The catalogue now contains two families whose edge fades (a trend that
    # halves every 3,000 bars, and a large-cap anomaly that loses 85% of itself on
    # a date), and this gate is what notices.
    #
    # Thresholds measured, not assumed. Across ten bots that had already been
    # certified on stationary families, second-half alpha Sharpe ran +0.38 to
    # +0.66 and retention 0.85 to 1.40 (median 0.98). On the decaying twins the
    # same style of bot retains 0.31 and 0.02. A floor of +0.25 late and 0.50
    # retention sits comfortably between them.
    #
    # Costs nothing: it splits the return series G2 already produced.
    early_a, late_a = _early_late_alpha(repl_raw)
    retention = (late_a / early_a) if early_a > 0.10 else 1.0
    ok = late_a >= cfg.min_late_alpha_sr and retention >= cfg.min_edge_retention
    perf.update(early_alpha_sr=early_a, late_alpha_sr=late_a, edge_retention=retention)
    stages.append(Stage("G2b-durability", ok,
                        f"late-half alphaSR {late_a:+.2f} (need {cfg.min_late_alpha_sr:+.2f}), "
                        f"retained {retention:.0%} of the early half {early_a:+.2f} "
                        f"(need {cfg.min_edge_retention:.0%})"))
    if not ok:
        return fail("G2b-durability")

    # ---- G3: negative controls ----------------------------------------------
    worst_ctrl, ctrl_detail = 0.0, []
    for cspec in universe.controls():
        cser = [generate.cached(cspec, i) for i in list(universe.HOLDOUT_POOL)[:cfg.n_control_instances]]
        cp, _ = _panel(cser, g)
        n_bt += len(cser)
        worst_ctrl = max(worst_ctrl, abs(cp.alpha_sharpe))
        ctrl_detail.append(f"{cspec.name}={cp.alpha_sharpe:+.2f}")
    ok = worst_ctrl <= cfg.max_control_alpha_sr
    perf.update(control_worst_alpha_sr=worst_ctrl)
    stages.append(Stage("G3-controls", ok,
                        f"worst |alphaSR| {worst_ctrl:.2f} (allowed {cfg.max_control_alpha_sr:.2f}) "
                        f"[{', '.join(ctrl_detail)}]"))
    if not ok:
        return fail("G3-controls")

    # ---- G4: cost and latency stress ----------------------------------------
    sub = repl[: max(8, cfg.n_repl_instances // 2)]
    p2, _ = _panel(sub, g, cost_mult=2.0)
    p3, _ = _panel(sub, g, cost_mult=3.0)
    pd_, _ = _panel(sub, g, exec_delay=2)
    n_bt += 3 * len(sub)
    ok = (p2.alpha_sharpe >= cfg.cost_stress_2x_min and p3.alpha_sharpe >= cfg.cost_stress_3x_min
          and pd_.alpha_sharpe >= cfg.delay_stress_min)
    perf.update(cost2x_alpha_sr=p2.alpha_sharpe, cost3x_alpha_sr=p3.alpha_sharpe,
                delay2_alpha_sr=pd_.alpha_sharpe)
    stages.append(Stage("G4-stress", ok,
                        f"2x costs {p2.alpha_sharpe:+.2f} (need {cfg.cost_stress_2x_min:+.2f}), "
                        f"3x {p3.alpha_sharpe:+.2f} (need {cfg.cost_stress_3x_min:+.2f}), "
                        f"+1 bar delay {pd_.alpha_sharpe:+.2f} (need {cfg.delay_stress_min:+.2f})"))
    if not ok:
        return fail("G4-stress")

    # ---- G5: block-bootstrap permutation null -------------------------------
    perm_base = repl[: cfg.n_perm_instances]
    real, _ = _panel(perm_base, g)
    n_bt += len(perm_base)
    null_srs = []
    for _ in range(cfg.n_perm_draws):
        nulls = [generate.bootstrap_like(s, rng, cfg.perm_block) for s in perm_base]
        np_, _ = _panel(nulls, g)
        n_bt += len(nulls)
        null_srs.append(np_.alpha_sharpe)
    null_arr = np.asarray(null_srs, dtype=float)
    null_mean = float(null_arr.mean())
    null_sd = float(null_arr.std(ddof=1)) if null_arr.size > 2 else 0.0
    # Empirical p, floored by the number of draws: with N draws the smallest
    # attainable p is 1/(N+1), so demanding p<=0.01 needs N>=100. The first
    # version of this file asked for 0.01 from 40 draws, which no strategy on
    # earth could have satisfied.
    p_value = float((np.sum(null_arr >= real.alpha_sharpe) + 1) / (null_arr.size + 1))
    z_null = ((real.alpha_sharpe - null_mean) / null_sd) if null_sd > 1e-9 else 0.0
    ok = p_value <= cfg.perm_p_max
    perf.update(perm_p=p_value, perm_real_alpha_sr=real.alpha_sharpe,
                perm_null_mean=null_mean, perm_null_sd=null_sd, perm_z=z_null,
                perm_null_p99=float(np.quantile(null_arr, 0.99)), perm_draws=int(null_arr.size))
    stages.append(Stage("G5-permutation", ok,
                        f"real {real.alpha_sharpe:+.2f} vs null {null_mean:+.2f}"
                        f"+-{null_sd:.2f} (p99 {np.quantile(null_arr, 0.99):+.2f}) -> "
                        f"z={z_null:.1f}, p={p_value:.4f} of {null_arr.size} draws "
                        f"(need <={cfg.perm_p_max})"))
    if not ok:
        return fail("G5-permutation")

    # ---- G6: correct for the size of the search -----------------------------
    # Two independent multiple-testing controls, both required.
    #
    # (a) Deflated Sharpe. The subtlety that matters: the evidence being judged
    #     is a *median over n independent instances*, not a single backtest, so
    #     the luck-implied bar must be built from the sampling variance of that
    #     median (var/n, x1.57 for a median rather than a mean) — not from the
    #     variance of one 12-year Sharpe. Using the latter sets a bar of ~0.8
    #     Sharpe that no honest single-asset strategy clears, and rejects
    #     everything including strategies whose edge is real.
    # (b) Bonferroni on the permutation z-score.
    #
    # WHICH DENOMINATOR. The deflated-Sharpe literature counts *every* trial,
    # because in real-data backtesting there is one history and all trials are
    # scored against it. That does not hold here: selection happens on the SEARCH
    # pool, while this evidence comes from the HOLDOUT and STRESS pools, which are
    # independent draws no screened-out candidate ever touched. The exposure on
    # confirmation data is therefore the number of candidates *tested against it*
    # — the gauntlet count — not the number screened. Using the screen count
    # instead demanded z >= 4.25 and killed 9 bots that had already replicated on
    # 20 fresh instances and beaten their permutation null at p <= 0.01, which is
    # double-counting, not rigour.
    #
    # Both figures are recorded; the gate uses the confirmation count and the
    # stricter all-trials number is reported alongside. The end-to-end
    # false-positive rate of the ladder under this choice is measured directly by
    # `calibrate.control_search_fpr()`, which runs the whole search against a
    # structureless market.
    #
    # Known limitation: the Bonferroni leg extrapolates the permutation null's
    # Gaussian tail well past what 120 draws can resolve. It is a sanity bound,
    # not a measured p-value; the weight is carried by the conjunction of G2, G5
    # and G7.
    n_confirm = int(n_confirm_tests if n_confirm_tests is not None else n_trials)
    n_confirm = max(n_confirm, 1)
    repl_results = [engine.run(s, g) for s in repl]
    n_bt += len(repl)
    r_pooled, _, bpy = metrics.pool(repl_results)
    var_median = var_trial_sharpe * 1.57 / max(len(repl), 1)
    dsr, sr0 = stats.deflated_sharpe(r_pooled, bpy, n_confirm, var_median)
    p_fw = min(1.0, (1.0 - stats.norm_cdf(z_null)) * n_confirm)
    p_fw_all = min(1.0, (1.0 - stats.norm_cdf(z_null)) * max(n_trials, 1))
    dsr_all, sr0_all = stats.deflated_sharpe(r_pooled, bpy, max(n_trials, 1), var_median)
    ok = dsr >= cfg.min_dsr and p_fw <= cfg.family_wise_p_max
    headroom = _burden_headroom(r_pooled, bpy, z_null, var_median, cfg)
    perf.update(burden_headroom=headroom,
                dsr=dsr, dsr_threshold_sr=sr0, n_trials=n_trials,
                n_confirm_tests=n_confirm, var_trial_sharpe=var_trial_sharpe,
                family_wise_p=p_fw, family_wise_p_all_trials=p_fw_all,
                dsr_all_trials=dsr_all, dsr_threshold_sr_all_trials=sr0_all)
    stages.append(Stage("G6-multiplicity", ok,
                        f"DSR {dsr:.3f} (need {cfg.min_dsr:.2f}) vs luck bar SR {sr0:.2f} "
                        f"after {n_confirm} confirmation tests (would still pass up to "
                        f"{'>=' if headroom >= HEADROOM_CAP else ''}{headroom:,}); "
                        f"Bonferroni p {p_fw:.2e} "
                        f"(need <={cfg.family_wise_p_max}) | stricter all-trials view "
                        f"({n_trials} screened): DSR {dsr_all:.3f} vs SR {sr0_all:.2f}, "
                        f"p {p_fw_all:.2e}"))
    if not ok:
        return fail("G6-multiplicity")

    # ---- G7: second replication, third pool ---------------------------------
    stress = instances(g.market, universe.STRESS_POOL, cfg.n_stress_instances)
    pooled, per = _panel(stress, g)
    n_bt += len(stress)
    srs = np.array([p.alpha_sharpe for p in per])
    med, pos = float(np.median(srs)), float(np.mean(srs > 0))
    dd_med = float(np.median([p.max_dd for p in per]))
    ok = (med >= cfg.min_stress_alpha_sr and pos >= cfg.min_stress_pos_frac
          and not pooled.ruined and -dd_med <= cfg.max_drawdown * 1.2)
    perf.update(stress_alpha_sr=med, stress_pos_frac=pos, stress_sr=pooled.sharpe,
                stress_cagr=pooled.cagr, stress_max_dd=dd_med,
                stress_vol=pooled.vol_ann, stress_calmar=pooled.calmar,
                stress_turnover=pooled.turnover_ann, stress_cost_drag=pooled.cost_drag_ann,
                stress_exposure=pooled.exposure, stress_psr=pooled.psr)
    stages.append(Stage("G7-stress-pool", ok,
                        f"median alphaSR {med:+.2f} (need {cfg.min_stress_alpha_sr:+.2f}), "
                        f"{pos:.0%} positive (need {cfg.min_stress_pos_frac:.0%}), "
                        f"CAGR {pooled.cagr:+.1%}, median DD {dd_med:.1%}"))
    if not ok:
        return fail("G7-stress-pool")

    # ---- badge (not a gate): does the rule travel? --------------------------
    xm: dict = {}
    if cross_market:
        for other in universe.tradeable(3):
            if other.name == g.market:
                continue
            oser = [generate.cached(other, i) for i in list(universe.HOLDOUT_POOL)[:6]]
            op, _ = _panel(oser, g)
            n_bt += len(oser)
            xm[other.name] = round(op.alpha_sharpe, 3)

    return Verdict(g.bot_id, g.market, True, None, stages, perf=perf, cross_market=xm,
                   n_backtests=n_bt, describe=g.describe())


HEADROOM_CAP = 1 << 30      # search sizes beyond this are not a meaningful distinction


def _burden_headroom(r_pooled: np.ndarray, bpy: float, z_null: float,
                     var_median: float, cfg: GauntletConfig) -> int:
    """The largest search this bot's evidence could have come out of and still
    certify: the maximum number of confirmation tests at which it clears both
    legs of G6.

    This is the number that says how much of a certification is the bot and how
    much is the search having been small. Both criteria fall monotonically as the
    test count rises, so a binary search finds the crossing exactly, and it costs
    nothing — the replication returns and the permutation z are already in hand.

    Measured because it mattered: doubling the bars per instance let a run certify
    six strategies from 960 candidates, but re-testing them against the burden of
    the previous 92,000-candidate run showed only three would have survived it.
    Both facts are true and only reporting the first would be misleading.
    """
    if r_pooled.size < 8:
        return 0

    def passes(n: int) -> bool:
        dsr, _ = stats.deflated_sharpe(r_pooled, bpy, max(n, 1), var_median)
        p_fw = min(1.0, (1.0 - stats.norm_cdf(z_null)) * max(n, 1))
        return dsr >= cfg.min_dsr and p_fw <= cfg.family_wise_p_max

    if not passes(1):
        return 0
    lo, hi = 1, HEADROOM_CAP
    if passes(hi):
        return hi                            # saturated; report as ">= cap"
    while lo < hi - 1:                       # invariant: passes(lo), not passes(hi)
        mid = (lo + hi) // 2
        if passes(mid):
            lo = mid
        else:
            hi = mid
    return lo


def quick_report(v: Verdict) -> str:
    lines = [f"{'PROVEN' if v.passed else 'REJECTED'}  {v.bot_id}  {v.market}",
             f"  {v.describe}"]
    for s in v.stages:
        lines.append(f"  [{'PASS' if s.passed else 'FAIL'}] {s.name:<16} {s.detail}")
    if v.cross_market:
        best = sorted(v.cross_market.items(), key=lambda kv: -kv[1])[:4]
        lines.append("  travels to: " + ", ".join(f"{k} {x:+.2f}" for k, x in best))
    lines.append(f"  ({v.n_backtests} backtests)")
    return "\n".join(lines)
