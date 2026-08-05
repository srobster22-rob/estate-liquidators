"""
The gate. This file is the adversary, and it is the only reason the factory is worth
running at all.

Producing bots is easy — `factory.py` can make thousands. Producing a bot that LOOKS
profitable is easier still: search 4,734 hypotheses against noise and roughly 240 will
clear p<0.05 on their own, every one of them worthless. So the interesting engineering is
not the search, it is the disqualification, and it has to be built to reject the author's
own favourite result.

WHAT "PROVEN PROFIT" IS DEFINED TO MEAN HERE (all of it, not some of it):

  1. Out-of-sample data, disjoint by seed from anything used to pick the bot. Selection
     happens on in-sample ONLY — including the mutation that produced the bot. The moment
     a survivor is bred from its OOS score, OOS stops being out of sample and the number
     becomes decoration.
  2. At least `min_trades_oos` trades. An edge measured over 40 trades is not measured.
  3. Positive mean PnL per market offered, counting the markets it declined as zeros.
     Per-trade means flatter a selective bot; per-offered does not.
  4. A bootstrap 95% lower bound above zero, resampling GROUPS — because the five legs of
     a bracket arb are one bet, not five, and a naive per-trade bootstrap would claim five
     times the evidence that exists.
  5. A FAMILY-WISE adjusted p-value under 0.05 (Holm), where the family is EVERY
     out-of-sample test the loop has ever run, cumulatively, across all generations. This
     is the line most strategy searches quietly omit, and it is the one that does the most
     work.

     FWER, NOT FDR, AND THE DISTINCTION IS THE WHOLE POINT. The obvious choice here is
     Benjamini-Hochberg, and it is the wrong one. BH controls the false discovery RATE:
     given 500 tests all at p=0.04, BH declares all 500 discoveries, because under a global
     null you would expect 25, not 500. That reasoning is sound and it is useless here —
     the factory does not fund a portfolio of 500 bots, it picks ONE and puts money behind
     it, so a single false discovery is not 1/500th of a problem, it is the entire problem.
     Holm controls the probability of ANY false discovery, which is the question actually
     being asked. `selftest.py` check 10 pins both behaviours down with worked examples;
     BH is still computed and reported alongside, because the gap between the two numbers
     is a useful read on how hard the search has been pushed.
  6. A third dataset — holdout — confirming the sign. Touched once, at the very end.
  7. Survival of a stress test: fees 1.5x, spread one tick wider, maker fills halved. An
     edge that dies here was an edge in the assumptions, not the market.
  8. An annualised return on locked capital above the floor. Kalshi collateral is locked
     until settlement, so a 3c edge on a 90-day contract is a worse business than a 0.3c
     edge on an hourly one, and ranking by PnL per trade hides that completely.
  9. Profitability in a HALF-EDGE WORLD. Criterion 7 makes execution worse — higher fees,
     wider spreads, fewer maker fills — which tests whether a bot was fitting the cost
     assumptions. It does not test the assumption that matters most: that the inefficiency
     is as big as `markets.py` claims. Those magnitudes are estimates. So the bot is re-run
     against markets whose planted edges are halved and whose spreads, depth and fees are
     untouched, and it has to still make money against the fainter signal. This is the
     closest available proxy for "the real world is less exploitable than I guessed", which
     is the most likely way any of this fails outside the simulator.
 10. Profitability under a pessimistic RARE-LOSS RATE. Criteria 1-8 were the whole gate
     until the first three bots passed it, and all three turned out to win 99.3% of the
     time and hand back most of the position on the other 0.7% — seven observed losses in
     1200 markets. Nothing above notices that the entire risk of the strategy rests on
     seven data points. This criterion applies the Wilson upper bound on the loss rate to
     the losses actually seen and asks whether the edge survives; the fewer losses
     observed, the wider that bound and the harsher the test. No arbitrary minimum-loss
     threshold needed, and no "picking up pennies in front of a steamroller" strategy gets
     certified on the strength of a quiet sample.

 11. At least `min_annual_dollars` PER YEAR. Criteria 1-10 all measure edge per market, and
     a bot can ace every one of them and still be a $214/yr business — which is exactly what
     the first winner turned out to be, because `econ_print` lists ~250 markets a year and
     the book holds ~55 contracts where the edge lives. Annual dollars is markets/yr x edge
     per market, so this criterion is the only one that can see the difference between a big
     edge somewhere rare and a small edge somewhere constant. It is also the only criterion
     that depends on an estimate nobody has verified (`capacity.markets_per_year`), and it
     scales linearly with it.
Criteria 9, 10 and 11 all exist because the gate was PASSED. Every time this thing clears its
own bar, the first question is what the bar failed to ask — and criterion 11 came from the
bluntest version of that question: fine, it works, so how much money is it?

The bootstrap is used for the p-value as well as the interval, deliberately. Per-group
PnL is violently skewed — most groups lose a little and a few win 100c — and a t-test on
that shape is not to be trusted at the third decimal place. The centred bootstrap makes
no distributional claim.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import statistics

from . import backtest

_CFG = json.loads((pathlib.Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
GATE = _CFG["gate"]


# The gate, named. One entry per check emitted by `gate()`, in order, so the count in the
# report cannot drift out of step with the code the way it did when it was inferred from
# config keys.
GATE_CRITERIA = (
    "trades_oos", "oos_mean_positive", "bootstrap_lo95_positive", "fwer_adjusted_p",
    "holdout_trades", "holdout_mean_positive", "stress_mean_positive",
    "annualized_return", "tail_risk", "half_edge", "annual_dollars",
)


class Stats:
    __slots__ = ("n_groups", "n_trades", "n_contracts", "total", "mean", "sd", "t",
                 "p_one_sided", "lo95", "hi95", "annualized", "win_rate", "max_dd",
                 "fees_paid", "gross", "mean_per_trade", "fee_share",
                 "n_losses", "loss_rate", "wilson_loss_hi", "tail_mean", "worst_loss",
                 "annual_dollars", "markets_per_year")

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}


def wilson_upper(x: int, n: int, z: float = 1.96) -> float:
    """Upper bound of the Wilson score interval for a proportion.

    Used on the LOSS RATE, and the choice of Wilson over the normal approximation is the
    whole point: at 7 losses in 1024 trades the normal interval is meaningless, and Wilson
    stays sane all the way down to zero events.
    """
    if n <= 0:
        return 1.0
    ph = x / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (ph + z2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(max(ph * (1.0 - ph) / n + z2 / (4 * n * n), 0.0))
    return min(1.0, centre + half)


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def summarize(res: backtest.Result, resamples: int | None = None, seed: int = 12345,
              markets_per_year: int = 0) -> Stats:
    s = Stats()
    # Edge per market is a fact about the strategy; dollars per year is a fact about the
    # BUSINESS, and they rank candidates completely differently. econ_print pays 85c a market
    # and lists ~250 of them; crypto_hourly lists 17,520. A tenth of the edge in the second is
    # seven times the money. Ranking by t-statistic — which is scale-free — cannot see that
    # difference at all, which is why the first winner this loop produced was a $214/yr bot.
    s.markets_per_year = markets_per_year
    g = res.group_pnl
    s.n_groups = len(g)
    s.n_trades = res.n_trades
    s.n_contracts = res.n_contracts
    s.total = res.total_pnl
    s.mean = _mean(g)
    s.sd = statistics.pstdev(g) if len(g) > 1 else 0.0
    s.gross = res.gross_pnl
    s.fees_paid = res.fees_paid
    s.fee_share = (res.fees_paid / abs(res.gross_pnl)) if res.gross_pnl else 0.0
    s.mean_per_trade = _mean(res.trade_pnl)
    s.win_rate = (sum(1 for x in res.trade_pnl if x > 0) / len(res.trade_pnl)) if res.trade_pnl else 0.0
    s.annualized = res.annualized_return
    s.annual_dollars = markets_per_year * s.mean / 100.0

    # --- RARE-EVENT TAIL --------------------------------------------------------------
    # Added because the first three bots to pass this gate all won ~99.3% of the time and
    # lost most of the position when they lost. On 1200 markets that is SEVEN observed
    # losses, and every other criterion in this file treats seven observations of the only
    # thing that can hurt you as sufficient evidence. It is not.
    #
    # So: take the Wilson 97.5% upper bound on the loss rate, apply it to the average loss
    # actually seen (or to the largest position ever opened, if the strategy was lucky
    # enough never to lose), and ask whether the strategy is still profitable. The fewer
    # losses observed, the wider the Wilson bound and the harsher this gets — which is the
    # correct direction, and it needs no arbitrary "minimum number of losses" threshold.
    # Computed per TRADE, and for a multi-leg strategy that is pessimistic rather than
    # wrong: `bracket_arb` books four guaranteed-losing legs for every winning one, so it
    # reads as an 80% loss rate even though the arb as a whole cannot lose. Pessimistic is
    # the safe direction for a gate — it can refuse a good bot, it cannot certify a bad one —
    # and the other eight criteria use per-group PnL, which accounts for multi-leg trades
    # correctly.
    losses = [x for x in res.trade_pnl if x < 0]
    wins = [x for x in res.trade_pnl if x >= 0]
    s.n_losses = len(losses)
    s.worst_loss = min(losses) if losses else -res.max_position_cost
    s.loss_rate = (len(losses) / len(res.trade_pnl)) if res.trade_pnl else 0.0
    s.wilson_loss_hi = wilson_upper(len(losses), len(res.trade_pnl)) if res.trade_pnl else 1.0
    if res.trade_pnl:
        mean_win = _mean(wins) if wins else 0.0
        mean_loss = _mean(losses) if losses else float(-res.max_position_cost)
        ph = s.wilson_loss_hi
        # Per-trade expectancy if losses really arrive at the top of their interval, then
        # rescaled to the per-market-offered basis the rest of the gate uses.
        per_trade = (1.0 - ph) * mean_win + ph * mean_loss
        s.tail_mean = per_trade * len(res.trade_pnl) / max(s.n_groups, 1)
    else:
        s.tail_mean = 0.0

    # Max drawdown over the group sequence. Groups are independent draws, not a calendar,
    # so this is a rough shape-of-the-path number rather than a real historical drawdown.
    peak = cum = 0
    dd = 0
    for x in g:
        cum += x
        peak = max(peak, cum)
        dd = min(dd, cum - peak)
    s.max_dd = dd

    if s.sd > 0 and s.n_groups > 1:
        se = s.sd / math.sqrt(s.n_groups)
        s.t = s.mean / se
    else:
        s.t = 0.0

    n_re = GATE["bootstrap_resamples"] if resamples is None else resamples
    if n_re and s.n_groups >= 20:
        s.lo95, s.hi95, s.p_one_sided = _bootstrap(g, n_re, seed, s.mean)
    else:
        s.lo95 = s.hi95 = 0.0
        s.p_one_sided = 1.0
    return s


def _bootstrap(data, n_re, seed, observed_mean):
    """Percentile CI, plus a centred-bootstrap one-sided p-value for H0: mean <= 0.

    The null is built by subtracting the observed mean from the data, so the resampled
    means describe a world with no edge and the same shape and variance as the real one.
    p is the share of that world at least as profitable as what was observed.
    """
    rng = random.Random(seed)
    n = len(data)
    means = []
    choices = rng.choices
    for _ in range(n_re):
        means.append(sum(choices(data, k=n)) / n)
    means.sort()
    lo = means[int(0.025 * (n_re - 1))]
    hi = means[int(0.975 * (n_re - 1))]

    shift = observed_mean
    ge = 0
    for m in means:
        if m - shift >= observed_mean:
            ge += 1
    p = (ge + 1) / (n_re + 1)
    return lo, hi, p


def benjamini_hochberg(pvals: list[float], alpha: float = 0.05) -> list[float]:
    """BH-adjusted p-values, order preserved. Controls the false discovery RATE.

    Reported for context, not gated on — see the module docstring for why FDR is the wrong
    error rate when the output is one funded bot rather than a portfolio of findings.
    """
    m = len(pvals)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        val = min(prev, pvals[i] * m / (rank + 1))
        adj[i] = val
        prev = val
    return adj


def holm(pvals: list[float], alpha: float = 0.05) -> list[float]:
    """Holm-adjusted p-values, order preserved. Controls the FAMILY-WISE error rate.

    Step-down: the k-th smallest p is multiplied by (m - k + 1), then made monotone. This
    is what the gate binds on. It is strictly more conservative than BH and uniformly more
    powerful than Bonferroni, which makes it the cheapest available way to be honest.
    """
    m = len(pvals)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank in range(m):
        i = order[rank]
        running = max(running, min(1.0, pvals[i] * (m - rank)))
        adj[i] = running
    return adj


class Verdict:
    __slots__ = ("passed", "reasons", "checks")

    def __init__(self):
        self.passed = False
        self.reasons: list[str] = []
        self.checks: list[tuple[str, bool, str]] = []

    def check(self, label, ok, detail):
        self.checks.append((label, bool(ok), detail))
        if not ok:
            self.reasons.append(f"{label}: {detail}")
        return ok

    def finish(self):
        self.passed = all(ok for _, ok, _ in self.checks) and bool(self.checks)
        return self


def gate(oos: Stats, holdout: Stats | None, stress: Stats | None,
         fwer_adjusted_p: float | None, n_hypotheses: int,
         bh_adjusted_p: float | None = None, half_edge: Stats | None = None) -> Verdict:
    """Every line must pass. Loosening any of them is how a bot factory lies to itself."""
    v = Verdict()
    v.check("trades_oos", oos.n_trades >= GATE["min_trades_oos"],
            f"{oos.n_trades} trades, need {GATE['min_trades_oos']}")
    v.check("oos_mean_positive", oos.mean > 0,
            f"mean {oos.mean:+.3f}c per market offered")
    v.check("bootstrap_lo95_positive", oos.lo95 > 0,
            f"95% CI [{oos.lo95:+.3f}, {oos.hi95:+.3f}]c")
    if fwer_adjusted_p is None:
        v.check("fwer_adjusted_p", False, "not computed")
    else:
        bh_note = f", BH would say {bh_adjusted_p:.4f}" if bh_adjusted_p is not None else ""
        v.check("fwer_adjusted_p", fwer_adjusted_p < GATE["max_bh_adjusted_p"],
                f"Holm-adjusted p={fwer_adjusted_p:.4f} over {n_hypotheses} OOS tests "
                f"(raw p={oos.p_one_sided:.4f}{bh_note})")
    if holdout is None:
        v.check("holdout", False, "not run")
    else:
        v.check("holdout_trades", holdout.n_trades >= GATE["min_trades_holdout"],
                f"{holdout.n_trades} trades, need {GATE['min_trades_holdout']}")
        v.check("holdout_mean_positive", holdout.mean > 0,
                f"mean {holdout.mean:+.3f}c per market offered")
    if stress is None:
        v.check("stress", False, "not run")
    else:
        v.check("stress_mean_positive", stress.mean > 0,
                f"mean {stress.mean:+.3f}c at {GATE['stress_fee_multiplier']}x fees, "
                f"+{GATE['stress_extra_spread_ticks']} tick spread")
    v.check("annualized_return", oos.annualized >= GATE["min_annualized_return_on_locked_capital"],
            f"{oos.annualized * 100:.2f}%/yr on locked capital, floor "
            f"{GATE['min_annualized_return_on_locked_capital'] * 100:.0f}%")
    if half_edge is None:
        v.check("half_edge", False, "not run")
    else:
        v.check("half_edge", half_edge.mean > 0,
                f"mean {half_edge.mean:+.2f}c/market in a world where the planted "
                f"inefficiency is {GATE['half_edge_factor']:g}x what markets.py assumes")
    v.check("annual_dollars", oos.annual_dollars >= GATE["min_annual_dollars"],
            f"${oos.annual_dollars:,.0f}/yr on ~{oos.markets_per_year:,} markets/yr, "
            f"bar is ${GATE['min_annual_dollars']:,}")
    v.check("tail_risk", oos.tail_mean > 0,
            f"{oos.n_losses} losses in {oos.n_trades} trades (rate {oos.loss_rate * 100:.2f}%, "
            f"Wilson upper {oos.wilson_loss_hi * 100:.2f}%, worst {oos.worst_loss:+,.0f}c) "
            f"-> tail-adjusted mean {oos.tail_mean:+.2f}c/market")
    return v.finish()


def stress_costs() -> backtest.Costs:
    return backtest.Costs(
        fee_mult=GATE["stress_fee_multiplier"],
        extra_spread=GATE["stress_extra_spread_ticks"],
        fill_mult=GATE["stress_maker_fill_multiplier"],
        label="stress",
    )


def fmt_stats(s: Stats) -> str:
    return (f"n={s.n_groups:<5} trades={s.n_trades:<6} mean={s.mean:+7.3f}c "
            f"CI[{s.lo95:+7.3f},{s.hi95:+7.3f}] t={s.t:+6.2f} p={s.p_one_sided:.4f} "
            f"ann={s.annualized * 100:+7.2f}%/yr")
