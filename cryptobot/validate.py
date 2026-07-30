"""
The gauntlet: eleven gates a candidate must pass, on data the optimiser never saw.

The factory's job is to produce candidates. This file's job is to kill them. That
asymmetry is the whole design — a search loop with a weak validator does not find
edges, it finds the strategies best at fooling the validator, and it finds them
faster the harder it searches.

WHAT "PROVEN PROFIT" CAN AND CANNOT MEAN

  It can mean: profitable out of sample, on data withheld from the search; robust to
  doubled costs, to an extra bar of execution latency, and to parameter nudges;
  positive across several market regimes rather than one lucky run; better than
  buying and holding the same instrument; and statistically distinguishable from the
  best of N random strategies, where N is every strategy the factory has ever tried.

  It cannot mean: it will make money. Every gate here is retrospective. Regimes
  change, edges get arbitraged, venues change fee schedules, and the sample is
  always finite. A bot that clears all eleven gates has earned a small live
  allocation and continued monitoring — that is the honest ceiling of what a
  backtest can buy.

THE GATES, and what each one kills:

   1 sanity            bots with three trades and a fluke
   2 oos_profit        bots that only worked in the training window
   3 wf_efficiency     bots whose OOS is a fraction of their IS — overfit, by
                       definition, even when OOS happens to be positive
   4 beats_benchmark   bots that made money because the coin went up
   5 drawdown          bots nobody could actually hold through
   6 cost_stress       bots living inside the fee assumption
   7 lag_robust        bots that need fills nobody can get
   8 param_robust      bots perched on a knife-edge in parameter space
   9 regime_consist    bots that caught one move and gave it back
  10 deflated_sharpe   bots that are just the max of N draws from noise
  11 mc_timing         bots whose 'edge' is exposure, not timing — measured against
                       random signals matched to their own trade frequency

Gate 10 is the one that makes the loop honest. Its bar rises with every candidate
tested out of sample, so a factory that tests ten times as many candidates must find
something correspondingly better. Without it, "keep producing bots until one is
profitable" is a machine for manufacturing false positives, and it will always
succeed.

WHICH COUNT DEFLATES THE SHARPE, AND WHY IT ISN'T ALL OF THEM

  The obvious move is to deflate by every bot the factory has ever evaluated —
  hundreds of thousands. It is also wrong, and unusably strict. Under the null that
  a bot has no edge, its out-of-sample Sharpe is centred on zero *however it was
  chosen*: picking it by maximising in-sample fitness biases the in-sample estimate,
  not the out-of-sample one. That is the entire reason for holding data back.

  What does need paying for is the number of times the held-out data is CONSULTED.
  Test 200 candidates against the validation slice and the best of them is the
  maximum of 200 draws — so gate 10 deflates by `oos_looks`, the count of distinct
  candidates that have reached this segment, with the dispersion measured from
  their own out-of-sample Sharpes.

  The in-sample trial count is still tracked and still reported. It is the honest
  measure of how hard the search dug, it drives nothing directly, and it is the
  number to look at when deciding whether the validation slice has been consulted
  so often that it needs replacing.
"""

import random

from . import backtest as bt
from . import stats
from . import strategies as st
from . import universe as uni

THRESHOLDS = {
    "min_bars": 300,
    "min_trades": 20,
    "min_trades_per_year": 4.0,
    "min_sharpe": 0.8,           # annualised, out of sample, after costs
    "max_drawdown": 0.35,
    "min_calmar": 0.5,
    "min_wf_efficiency": 0.35,   # OOS Sharpe / IS Sharpe
    "cost_stress_mult": 2.0,
    "cost_stress_keep": 0.50,    # fraction of base Sharpe retained at 2x costs
    "lag_keep": 0.50,
    "param_keep": 0.50,
    "param_step": 0.20,          # ±20% nudge per parameter
    "min_regime_frac": 0.60,     # fraction of blocks with positive return
    "regime_blocks": 6,
    "min_dsr": 0.95,
    "max_bootstrap_p": 0.05,
    "max_mc_p": 0.05,
    "mc_runs": 80,
    "bootstrap_iters": 400,
}


class GateResult:
    __slots__ = ("name", "passed", "detail")

    def __init__(self, name, passed, **detail):
        self.name = name
        self.passed = bool(passed)
        self.detail = {k: v for k, v in detail.items() if v is not None}

    def __repr__(self):
        mark = "PASS" if self.passed else "FAIL"
        bits = " ".join(f"{k}={_fmt(v)}" for k, v in self.detail.items())
        return f"  [{mark}] {self.name:<16} {bits}"


class Report:
    def __init__(self, bot, gates, oos_metrics, is_metrics, dsr, benchmark_sharpe):
        self.bot = bot
        self.gates = gates
        self.oos = oos_metrics
        self.is_ = is_metrics
        self.dsr = dsr
        self.benchmark_sharpe = benchmark_sharpe

    @property
    def passed(self):
        return all(g.passed for g in self.gates)

    @property
    def first_failure(self):
        for g in self.gates:
            if not g.passed:
                return g.name
        return None

    def to_dict(self):
        return {
            "bot": self.bot.to_dict(),
            "passed": self.passed,
            "first_failure": self.first_failure,
            "dsr": self.dsr,
            "oos": self.oos,
            "is": self.is_,
            "gates": [{"name": g.name, "passed": g.passed, **g.detail}
                      for g in self.gates],
        }

    def render(self):
        head = ("PASSED ALL GATES" if self.passed
                else f"failed at {self.first_failure}")
        lines = [f"{self.bot.describe()}", f"  -> {head}"]
        lines += [repr(g) for g in self.gates]
        return "\n".join(lines)


def gauntlet(bot, segments, partner_segments=None, oos_looks=1, dispersion=0.6,
             thresholds=None, seed=0, segment="validation", stop_early=True,
             trials=None):
    """Run every gate against `segment` (default: the validation slice).

    `oos_looks` must be the number of distinct candidates that have been tested
    against this segment, INCLUDING this one. Under-reporting it is the easiest way
    to slip a bad bot past gate 10, and nothing about the output will look wrong
    when you do. `trials` is the in-sample search count, carried through for
    reporting only."""
    th = dict(THRESHOLDS, **(thresholds or {}))
    train = segments.train
    oos = getattr(segments, segment)
    p_train = partner_segments.train if partner_segments else None
    p_oos = getattr(partner_segments, segment) if partner_segments else None

    base = bot.run(oos, p_oos)
    ins = bot.run(train, p_train)
    m, mi = base.metrics, ins.metrics
    gates = []

    def add(gate):
        gates.append(gate)
        return not (stop_early and not gate.passed)

    # 1 ------------------------------------------------------------- sanity
    ok = (not m["ruined"] and m["bars"] >= th["min_bars"]
          and m["trades"] >= th["min_trades"]
          and m["trades_per_year"] >= th["min_trades_per_year"])
    if not add(GateResult("sanity", ok, bars=m["bars"], trades=m["trades"],
                          trades_yr=m["trades_per_year"], ruined=m["ruined"])):
        return _finish(bot, gates, m, mi, 0.0, 0.0)

    # 2 --------------------------------------------------------- oos profit
    ok = m["sharpe"] >= th["min_sharpe"] and m["total_return"] > 0
    if not add(GateResult("oos_profit", ok, sharpe=m["sharpe"],
                          ret=m["total_return"], cagr=m["cagr"])):
        return _finish(bot, gates, m, mi, 0.0, 0.0)

    # 3 ------------------------------------------------------ wf efficiency
    eff = (m["sharpe"] / mi["sharpe"]) if mi["sharpe"] > 1e-6 else 0.0
    ok = eff >= th["min_wf_efficiency"]
    if not add(GateResult("wf_efficiency", ok, is_sharpe=mi["sharpe"],
                          oos_sharpe=m["sharpe"], efficiency=eff)):
        return _finish(bot, gates, m, mi, 0.0, 0.0)

    # 4 ------------------------------------------------------- vs benchmark
    bh = bt.buy_hold(oos)
    ok = m["sharpe"] > bh["sharpe"] and m["total_return"] > 0
    if not add(GateResult("beats_benchmark", ok, bot=m["sharpe"],
                          buy_hold=bh["sharpe"], bh_ret=bh["total_return"])):
        return _finish(bot, gates, m, mi, 0.0, bh["sharpe"])

    # 5 ----------------------------------------------------------- drawdown
    ok = m["max_dd"] <= th["max_drawdown"] and m["calmar"] >= th["min_calmar"]
    if not add(GateResult("drawdown", ok, max_dd=m["max_dd"],
                          calmar=m["calmar"])):
        return _finish(bot, gates, m, mi, 0.0, bh["sharpe"])

    # 6 -------------------------------------------------------- cost stress
    stressed = bot.run(oos, p_oos, cost_mult=th["cost_stress_mult"])
    triple = bot.run(oos, p_oos, cost_mult=th["cost_stress_mult"] * 1.5)
    keep = (stressed["sharpe"] / m["sharpe"]) if m["sharpe"] > 0 else 0.0
    ok = (stressed["sharpe"] > 0 and keep >= th["cost_stress_keep"]
          and triple["total_return"] > 0)
    if not add(GateResult("cost_stress", ok, sharpe_2x=stressed["sharpe"],
                          retained=keep, ret_3x=triple["total_return"])):
        return _finish(bot, gates, m, mi, 0.0, bh["sharpe"])

    # 7 --------------------------------------------------------- lag robust
    lagged = bot.run(oos, p_oos, lag=1)
    keep = (lagged["sharpe"] / m["sharpe"]) if m["sharpe"] > 0 else 0.0
    ok = lagged["sharpe"] > 0 and keep >= th["lag_keep"]
    if not add(GateResult("lag_robust", ok, sharpe_lag1=lagged["sharpe"],
                          retained=keep)):
        return _finish(bot, gates, m, mi, 0.0, bh["sharpe"])

    # 8 ------------------------------------------------------- param robust
    neigh = _neighbour_sharpes(bot, oos, p_oos, th["param_step"])
    med = _median(neigh) if neigh else 0.0
    keep = (med / m["sharpe"]) if m["sharpe"] > 0 else 0.0
    worst = min(neigh) if neigh else 0.0
    ok = bool(neigh) and keep >= th["param_keep"] and worst > -0.5
    if not add(GateResult("param_robust", ok, neighbours=len(neigh),
                          median=med, retained=keep, worst=worst)):
        return _finish(bot, gates, m, mi, 0.0, bh["sharpe"])

    # 9 ---------------------------------------------------- regime coherence
    blocks = uni.regime_blocks(oos, th["regime_blocks"])
    pos, labels = 0, []
    for b in blocks:
        seg_ret = _segment_return(base, b["start"], b["end"])
        labels.append(f"{b['label']}:{seg_ret*100:+.1f}%")
        if seg_ret > 0:
            pos += 1
    frac = pos / len(blocks) if blocks else 0.0
    ok = frac >= th["min_regime_frac"]
    if not add(GateResult("regime_consist", ok, positive=f"{pos}/{len(blocks)}",
                          detail=",".join(labels))):
        return _finish(bot, gates, m, mi, 0.0, bh["sharpe"])

    # 10 -------------------------------------------------- deflated sharpe
    dsr, bench = stats.deflated_sharpe(m, oos_looks, dispersion, oos.bars_per_year)
    need = stats.sharpe_needed(m, bench, oos.bars_per_year, th["min_dsr"])
    ok = dsr >= th["min_dsr"]
    if not add(GateResult("deflated_sharpe", ok, dsr=dsr, oos_looks=oos_looks,
                          search_trials=trials, hurdle_sharpe=bench,
                          observed=m["sharpe"], needed=need,
                          oos_years=round(m["years"], 2))):
        return _finish(bot, gates, m, mi, dsr, bh["sharpe"])

    # 11 ------------------------------------------- bootstrap + timing null
    p_boot = stats.bootstrap_pvalue(base.net, th["bootstrap_iters"], seed=seed)
    rng = random.Random(seed + 1)
    raw = [0.0 if v is None else v for v in bot.signal(oos, p_oos)]
    nulls = stats.matched_random_signals(raw, th["mc_runs"], rng)
    null_sharpes = []
    for path in nulls:
        r = bt.run(oos, path, risk=bot.risk,
                   partner_turnover=1.0 if bot.partner_key else 0.0)
        null_sharpes.append(r["sharpe"])
    p_mc = stats.mc_pvalue(m["sharpe"], null_sharpes)
    ok = p_boot <= th["max_bootstrap_p"] and p_mc <= th["max_mc_p"]
    add(GateResult("mc_timing", ok, p_bootstrap=p_boot, p_random_signal=p_mc,
                   null_best=max(null_sharpes) if null_sharpes else 0.0))

    return _finish(bot, gates, m, mi, dsr, bh["sharpe"])


def _finish(bot, gates, oos_m, is_m, dsr, bh_sharpe):
    return Report(bot, gates, oos_m, is_m, dsr, bh_sharpe)


def _neighbour_sharpes(bot, market, partner, step):
    """Nudge each parameter up and down and re-measure. A real edge is a plateau: a
    20% change in a lookback should move the Sharpe, not delete it. A peak that
    collapses under a nudge is a peak the optimiser found in the noise."""
    from .bot import Bot
    out = []
    if bot.children:
        # Nudge each child's knobs in turn. An ensemble whose robustness was only
        # ever checked on its risk settings would sail through this gate with two
        # knife-edge children inside it.
        for idx, child in enumerate(bot.children):
            space = st.REGISTRY[child["strategy"]].space
            for key, spec in space.items():
                for frac in (step, -step):
                    moved = spec.perturb(child["params"][key], frac)
                    if moved == child["params"][key]:
                        continue
                    kids = [dict(c, params=dict(c["params"]))
                            for c in bot.children]
                    kids[idx]["params"][key] = moved
                    twin = Bot(bot.market_key, bot.strategy_name, bot.params,
                               bot.risk, bot.partner_key, kids)
                    out.append(twin.run(market, partner)["sharpe"])
    else:
        space = st.REGISTRY[bot.strategy_name].space
        for key, spec in space.items():
            for frac in (step, -step):
                moved = spec.perturb(bot.params[key], frac)
                if moved == bot.params[key]:
                    continue
                params = dict(bot.params, **{key: moved})
                twin = Bot(bot.market_key, bot.strategy_name, params, bot.risk,
                           bot.partner_key, bot.children)
                out.append(twin.run(market, partner)["sharpe"])
    for key in ("vol_win", "max_leverage"):
        spec = _risk_spec(key)
        for frac in (step, -step):
            moved = spec.perturb(bot.risk[key], frac)
            if moved == bot.risk[key]:
                continue
            twin = Bot(bot.market_key, bot.strategy_name, bot.params,
                       dict(bot.risk, **{key: moved}), bot.partner_key,
                       bot.children)
            out.append(twin.run(market, partner)["sharpe"])
    return out


def _risk_spec(key):
    from .bot import RISK_SPACE
    return RISK_SPACE[key]


def _segment_return(result, start, end):
    """Compound the bot's own net returns over a slice of the segment. Uses the
    realised return series rather than re-running, so block returns always add up to
    the reported total."""
    lo = max(0, start)
    hi = min(len(result.net), end)
    acc = 1.0
    for i in range(lo, hi):
        acc *= (1.0 + result.net[i])
    return acc - 1.0


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.3f}" if abs(v) < 1000 else f"{v:.3g}"
    return str(v)
