"""
A bot: the thing the factory breeds.

A bot is a genome, not a program — market + strategy + parameters + risk settings,
all of it serialisable to JSON so a survivor can be reproduced exactly, next month,
on data it has never seen. Reproducibility is not a nicety here: a candidate that
cannot be re-run bit-for-bit cannot be validated, and a bot that cannot be validated
is a story about a backtest.

The genome has four parts:

    market      which instrument and timeframe it trades
    strategy    which entry/exit logic, from the zoo
    params      that strategy's knobs
    risk        vol target, leverage cap, stop distance — shared by every strategy,
                so two ideas are always compared on the same risk budget

Plus an optional `children` list, which makes the bot an equal-weight ensemble of
sub-strategies. Ensembles are unlocked only when the search stalls, because a
two-strategy ensemble has roughly twice the parameters and therefore roughly twice
the capacity to memorise noise — and the deflated Sharpe charges for that capacity
whether or not it was used.
"""

import hashlib
import json

from . import backtest as bt
from . import strategies as st


RISK_SPACE = {
    "vol_target": st.FloatP(0.10, 0.80),
    "vol_win": st.IntP(24, 400, log=True),
    "max_leverage": st.FloatP(0.5, 3.0),
    "stop_atr": st.ChoiceP([0.0, 1.5, 2.5, 4.0, 6.0]),
    "stop_atr_win": st.IntP(10, 100, log=True),
}


class Bot:
    __slots__ = ("market_key", "strategy_name", "params", "risk", "partner_key",
                 "children", "born_gen", "notes", "_sig_cache")

    def __init__(self, market_key, strategy_name, params, risk,
                 partner_key=None, children=None, born_gen=0, notes=None):
        self.market_key = market_key
        self.strategy_name = strategy_name
        self.params = params
        self.risk = risk
        self.partner_key = partner_key
        self.children = children or []
        self.born_gen = born_gen
        self.notes = notes or {}
        self._sig_cache = {}

    # ------------------------------------------------------------- identity

    def fingerprint(self):
        """Stable hash of everything that affects behaviour. Two bots with the same
        fingerprint are the same trial, and the factory's trial counter — which sets
        the deflated-Sharpe bar — must not double-count them."""
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha1(payload.encode()).hexdigest()[:16]

    def to_dict(self):
        return {
            "market": self.market_key,
            "strategy": self.strategy_name,
            "params": self.params,
            "risk": self.risk,
            "partner": self.partner_key,
            "children": self.children,
        }

    @classmethod
    def from_dict(cls, d, born_gen=0):
        return cls(d["market"], d["strategy"], d["params"], d["risk"],
                   d.get("partner"), d.get("children"), born_gen)

    def describe(self):
        bits = [f"{self.strategy_name} on {self.market_key}"]
        if self.children:
            bits.append("+".join(c["strategy"] for c in self.children))
        if self.partner_key:
            bits.append(f"vs {self.partner_key}")
        bits.append("risk=" + ",".join(
            f"{k}={_fmt(v)}" for k, v in sorted(self.risk.items())))
        bits.append("params=" + ",".join(
            f"{k}={_fmt(v)}" for k, v in sorted(self.params.items())))
        return " | ".join(bits)

    # -------------------------------------------------------------- signals

    def signal(self, market, partner=None):
        # Keyed by identity AND shape, not id() alone: CPython reuses addresses
        # after a garbage collection, and a bot that got handed a recycled id would
        # silently trade one market's signal on another's prices.
        ck = (id(market), market.key, len(market), market.ts[0])
        cached = self._sig_cache.get(ck)
        if cached is not None:
            return cached
        if self.children:
            sig = _ensemble_signal(self.children, market, partner)
        else:
            strat = st.REGISTRY[self.strategy_name]
            sig = strat.signal(market, self.params, partner)
        self._sig_cache[ck] = sig
        return sig

    def run(self, market, partner=None, lag=0, cost_mult=1.0):
        """A bot with a partner is a two-leg trade: it earns the spread, not the
        market, and it pays fees on both sides."""
        paired = self.partner_key is not None and partner is not None
        return bt.run(market, self.signal(market, partner), risk=self.risk,
                      lag=lag, cost_mult=cost_mult,
                      partner_turnover=1.0 if paired else 0.0,
                      hedge=partner if paired else None)


def _ensemble_signal(children, market, partner):
    """Equal-weight average of the children's exposures, with a bar counting as
    ready only when every child is ready. Averaging rather than voting because a
    partial agreement should produce a partial position — a bot that is half
    convinced should be half sized."""
    parts = []
    for child in children:
        strat = st.REGISTRY[child["strategy"]]
        parts.append(strat.signal(market, child["params"], partner))
    n = len(market.close)
    out = [None] * n
    for i in range(n):
        vals = [p[i] for p in parts]
        if any(v is None for v in vals):
            continue
        out[i] = sum(vals) / len(vals)
    return out


# -------------------------------------------------------------------- fitness

MIN_TRADES_PER_YEAR = 4.0


def fitness(result, min_trades=20, turnover_penalty=0.0015, dd_limit=0.40,
            folds=4, consistency_weight=0.6, market_returns=None):
    """The in-sample objective the genetic search maximises.

    Deliberately NOT raw Sharpe. Selecting on raw in-sample Sharpe is how the first
    version of this factory produced a population with in-sample Sharpe 5.6 and
    out-of-sample Sharpe -1.4: the maximum of thousands of noisy estimates is a
    measure of luck, and the genetic search compounds it generation after
    generation. Four things are penalised instead:

      * bots that trade twice and got lucky      → min-trade floor
      * bots that churn                          → turnover penalty, a cheap
                                                   stand-in for the full cost
                                                   stress test in the gauntlet
      * bots that ride one enormous drawdown     → penalty above `dd_limit`
      * bots that made it all in one burst       → CONSISTENCY penalty
      * bots that are just long a market that rose → ALPHA floor

    The consistency term is nearly free: split the realised return series into
    `folds` contiguous blocks, measure the Sharpe of each, and charge for their
    dispersion and for the worst one. A bot with a real edge earns steadily; a bot
    fitted to noise earns everything in one window.

    The alpha floor exists because the search and the gauntlet were pulling in
    opposite directions. Raw Sharpe rewards riding a trend with size; gates 4 and 11
    then kill exactly that bot for failing to beat buy-and-hold, or for losing to
    random signals with its own exposure profile. So `market_returns` (when supplied)
    buys a second number: the Sharpe of the bot's returns after regressing out its
    market exposure. The score is the WORSE of the two, because the gates are a
    conjunction — a bot has to be good on both counts, so the search may as well
    optimise for that from the start.

    Ruin is -100, not -1: a wiped-out bot must never breed just because its
    pre-death Sharpe looked interesting."""
    m = result.metrics
    if m["ruined"]:
        return -100.0
    if m["trades"] < min_trades or m["trades_per_year"] < MIN_TRADES_PER_YEAR:
        return -10.0 + m["trades"] * 0.01

    score = m["sharpe"]
    if market_returns is not None:
        score = min(score, alpha_sharpe(result, market_returns))
    score -= turnover_penalty * m["turnover_per_year"]
    score -= 2.0 * max(0.0, m["max_dd"] - dd_limit)
    if m["exposure"] < 0.02:
        score -= 5.0

    fold_sharpes = fold_sharpe(result, folds)
    if len(fold_sharpes) >= 2:
        mean = sum(fold_sharpes) / len(fold_sharpes)
        sd = (sum((s - mean) ** 2 for s in fold_sharpes)
              / (len(fold_sharpes) - 1)) ** 0.5
        score -= consistency_weight * sd
        score -= 1.0 * max(0.0, -min(fold_sharpes))
    return score


def alpha_sharpe(result, market_returns):
    """Annualised Sharpe of the bot's returns after removing its market exposure.

        beta     = cov(bot, market) / var(market)
        residual = bot - beta * market

    A bot that is simply long a rising market has a large raw Sharpe and an alpha
    Sharpe near zero. A market-timing bot keeps most of its Sharpe here. This is
    the cheap in-sample proxy for what gate 11 tests properly with matched random
    signals — cheap enough to run on every bot in every generation."""
    net = result.net
    n = min(len(net), len(market_returns) - 1)
    if n < 30:
        return 0.0
    mkt = [market_returns[i + 1] or 0.0 for i in range(n)]
    bot_r = net[:n]
    mb = sum(mkt) / n
    bb = sum(bot_r) / n
    var = sum((x - mb) ** 2 for x in mkt) / n
    if var <= 1e-18:
        return result.metrics["sharpe"]
    cov = sum((bot_r[i] - bb) * (mkt[i] - mb) for i in range(n)) / n
    beta = cov / var
    resid = [bot_r[i] - beta * mkt[i] for i in range(n)]
    mean = sum(resid) / n
    rvar = sum((x - mean) ** 2 for x in resid) / (n - 1)
    sd = rvar ** 0.5
    if sd <= 1e-12:
        return 0.0
    return (mean / sd) * (result.bars_per_year ** 0.5)


def fold_sharpe(result, folds=4):
    """Annualised Sharpe of each contiguous block of the realised return series.

    Computed from the returns the backtest already produced, so it costs one pass
    over a list rather than `folds` extra backtests."""
    n = len(result.net)
    if n < folds * 30:
        return []
    ann = result.bars_per_year ** 0.5
    out = []
    for k in range(folds):
        lo, hi = int(n * k / folds), int(n * (k + 1) / folds)
        chunk = result.net[lo:hi]
        if len(chunk) < 30:
            continue
        mean = sum(chunk) / len(chunk)
        var = sum((x - mean) ** 2 for x in chunk) / (len(chunk) - 1)
        sd = var ** 0.5
        out.append((mean / sd) * ann if sd > 1e-12 else 0.0)
    return out


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)
