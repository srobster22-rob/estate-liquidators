"""What a market *is*, in the two ways that matter: what structure it has to
exploit, and what it charges you to try.

Structure parameters are expressed as *fractions of total per-bar volatility*
rather than as raw coefficients, because that makes the ceiling explicit. If
the persistent trend component is 6% of one-bar volatility, then a forecaster
with perfect knowledge of that component earns an annual Sharpe of
0.06 * sqrt(bars_per_year) and not one basis point more. Every number in
`universe.py` is chosen so that ceiling sits where the published literature
puts the real thing, and `calibrate` prints the ceiling next to what canonical
bots actually achieve.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CostModel:
    """Everything that stands between a signal and a bank balance."""

    spread_bps: float = 2.0          # full quoted spread; you cross half of it
    commission_bps: float = 0.5      # per side, on notional
    impact_coef_bps: float = 12.0    # bps at 100% of ADV participation
    adv_notional: float = 5e8        # $ average daily volume of the venue
    borrow_ann: float = 0.005        # short borrow fee, annualised
    financing_ann: float = 0.045     # cost of leverage above 1x, annualised
    funding_bps_per_bar: float = 0.0 # perpetual-swap funding (crypto), signed cost of longs
    min_ticket_bps: float = 0.0      # fixed cost floor per trade, in bps of equity

    def trade_cost_bps(self, notional: float, gross_size_bps_of_adv: float) -> float:
        """Round-trip-agnostic cost of a single trade, in bps of the traded
        notional: half spread + commission + square-root impact."""
        impact = self.impact_coef_bps * math.sqrt(max(gross_size_bps_of_adv, 0.0) / 1e4)
        return 0.5 * self.spread_bps + self.commission_bps + impact


@dataclass(frozen=True)
class MarketSpec:
    """A market *family*. Combined with a seed it yields an instance.

    The family/instance split is what makes replication possible: the search
    only ever sees instances drawn from the training seed pool, and the
    gauntlet re-tests survivors on instances from a disjoint holdout pool. No
    real-data backtest can do that, which is exactly why the synthetic side of
    this lab exists.
    """

    name: str
    asset_class: str
    bars_per_year: float
    n_bars: int = 3000

    # --- price process ------------------------------------------------------
    drift_ann: float = 0.0           # risk premium, annualised
    vol_ann: float = 0.16            # target annualised volatility
    carry_ann: float = 0.0           # roll / funding yield earned by a long
    trend_frac: float = 0.0          # persistent trend component, as a fraction of per-bar vol
    trend_rho: float = 0.97          # AR(1) persistence of that component
    rev_kappa: float = 0.0           # pull back toward the anchor, per bar
    rev_halflife: float = 10.0       # anchor EMA halflife, bars
    garch_alpha: float = 0.08        # vol clustering: shock loading
    garch_beta: float = 0.88         # vol clustering: persistence
    regime_switch_prob: float = 0.0  # per-bar probability of flipping calm/stress
    regime_vol_mult: float = 2.0     # stress-state vol multiplier
    regime_drift_mult: float = -1.0  # stress-state drift multiplier
    jump_prob: float = 0.0           # per-bar jump probability
    jump_mean: float = 0.0           # jump mean, in per-bar sigmas
    jump_scale: float = 0.0          # jump std, in per-bar sigmas
    tail_df: float = 6.0             # Student-t df of innovations (inf-ish above 30)
    # A GARCH(1,1) has finite unconditional kurtosis only when
    # alpha^2*E[eps^4] + 2*alpha*beta + beta^2 < 1, and E[eps^4] is INFINITE for a
    # Student-t with df <= 4. Six families here sit below that line, so their
    # variance process is ill-defined in its fourth moment and can transiently
    # explode: one 12,000-bar small-cap instance produced a single-bar log return
    # of 3.9 (a 4,900% day) and sample kurtosis of 1,263. The returns are meant to
    # be fat-tailed; the *variance feedback* is not meant to be explosive. So the
    # shock entering the variance update is winsorized and the conditional
    # volatility is capped, while the return itself still gets the full untruncated
    # innovation and any jump. Fat tails in prices, finite moments in the recursion.
    garch_clip: float = 4.0          # winsorise the standardised shock feeding sigma^2
    vol_cap_mult: float = 8.0        # conditional vol ceiling, multiples of long-run
    # Even with a tamed variance process, a Student-t innovation at df 3.6 will
    # occasionally draw 40+ sigma, which on a 45%-vol name is an 1,100% day. Real
    # venues do not permit that: equities have limit-up/limit-down bands and
    # market-wide circuit breakers, futures have daily limits, and even crypto
    # exchanges halt or auto-deleverage. So the single-bar move is capped. At 12
    # sigma the tail stays far fatter than Gaussian (which never reaches 12 sigma)
    # while the worst daily move on a 45%-vol instrument becomes ~34% rather than
    # ~1,100%.
    max_bar_move_sigma: float = 12.0

    # --- edge decay: the assumption everything else rested on -----------------
    # Every family above is stationary — the same trend and reversion parameters
    # at the last bar as at the first. Real anomalies do not behave that way: they
    # get crowded, arbitraged and published, and the ones that survive usually
    # shrink. With 47.6 simulated years per instance that assumption had become
    # the binding limitation on anything this lab could claim.
    #
    # `edge_decay_halflife` (bars) decays the *predictable* components — trend,
    # reversion, calendar — toward `edge_decay_floor` as a fraction of their
    # original size. Drift, volatility, GARCH and jumps are untouched, so the
    # instrument still looks like the same instrument; only the edge fades.
    # `edge_break_at` instead applies an abrupt multiplier at a point in the
    # series, for the case where an anomaly stops working on a date rather than
    # fading — a rule change, a publication, a new venue.
    edge_decay_halflife: float = 0.0   # 0 = stationary
    edge_decay_floor: float = 0.0      # surviving fraction of the original edge
    edge_break_at: float = 0.0         # fraction of the series, 0 = no break
    edge_break_mult: float = 1.0       # edge multiplier after the break
    seasonal_amp: float = 0.0        # amplitude of the calendar effect, fraction of per-bar vol
    seasonal_period: int = 5         # bars per cycle (5 = weekday, 26 = 15-min US session)
    seasonal_shape: str = "sin"      # "sin" | "u"  (u = intraday U-shaped vol + open reversal)
    gap_frac: float = 0.30           # fraction of the bar move that arrives at the open
    range_mult: float = 1.0          # intrabar diffusion / close-to-close diffusion

    # --- tradeability ------------------------------------------------------
    costs: CostModel = field(default_factory=CostModel)
    allow_short: bool = True
    max_leverage: float = 2.0

    # --- calibration -------------------------------------------------------
    # Locked constant, not a free parameter. Regime, seasonal and jump variance
    # are corrected analytically in generate._noise_scale, but the fat-tailed
    # near-integrated GARCH families still miss their target volatility by up to
    # 20% because the sampling distribution of realised vol is badly skewed.
    # Refresh with `python bots/run.py calibrate --refresh-vol-fix` and paste the
    # printed values back into universe.py — measured on a reserved probe pool
    # so it never tunes against the search, holdout or stress instances.
    vol_fix: float = 1.0

    # --- bookkeeping -------------------------------------------------------
    tier: int = 1                    # search-space expansion tier that unlocks it
    control: bool = False            # True => must NOT be beatable (negative control)
    notes: str = ""

    @property
    def sigma_bar(self) -> float:
        return self.vol_ann / math.sqrt(self.bars_per_year)

    def edge_profile(self, n: int):
        """Per-bar multiplier on the predictable components, in [0, 1]."""
        import numpy as _np
        prof = _np.ones(int(n))
        if self.edge_decay_halflife > 0.0:
            t = _np.arange(int(n))
            decayed = 0.5 ** (t / float(self.edge_decay_halflife))
            prof = self.edge_decay_floor + (1.0 - self.edge_decay_floor) * decayed
        if 0.0 < self.edge_break_at < 1.0:
            cut = int(self.edge_break_at * int(n))
            prof = prof.copy()
            prof[cut:] *= float(self.edge_break_mult)
        return prof

    @property
    def is_stationary(self) -> bool:
        return self.edge_decay_halflife <= 0.0 and not (0.0 < self.edge_break_at < 1.0)

    def oracle_sharpe_ceiling(self) -> float:
        """Annual Sharpe of a forecaster with perfect knowledge of the
        predictable components. Nothing found in this market may exceed it, and
        anything close to it is a bug, not a discovery."""
        # Trend: contributes trend_frac of one-bar sigma, fully predictable one
        # bar ahead up to the innovation, hence the rho factor.
        trend = self.trend_frac * self.trend_rho
        # Reversion: the pull is kappa * dislocation; stationary dislocation std
        # is roughly sigma * sqrt(halflife / ln2 / 2) for an EMA anchor.
        disloc_sigmas = math.sqrt(max(self.rev_halflife, 1.0) / (2.0 * math.log(2.0)))
        rev = self.rev_kappa * disloc_sigmas
        seas = self.seasonal_amp / math.sqrt(2.0)
        carry = abs(self.carry_ann) / max(self.vol_ann, 1e-9) / math.sqrt(self.bars_per_year)
        edge = math.sqrt(trend ** 2 + rev ** 2 + seas ** 2 + carry ** 2)
        if not self.is_stationary:
            # A decaying family's ceiling is its *average* edge, not its opening
            # one — quoting the opening value would overstate what is on the table
            # for the whole series by a factor of several.
            import numpy as _np
            edge *= float(_np.mean(self.edge_profile(self.n_bars)))
        return edge * math.sqrt(self.bars_per_year)

    def summary(self) -> str:
        return (f"{self.name:<24} {self.asset_class:<10} vol={self.vol_ann:5.0%} "
                f"trend={self.trend_frac:4.2f} rev={self.rev_kappa:4.2f} "
                f"carry={self.carry_ann:+5.1%} spr={self.costs.spread_bps:5.1f}bp "
                f"ceiling_SR={self.oracle_sharpe_ceiling():4.2f}"
                + ("  [CONTROL]" if self.control else "")
                + ("" if self.is_stationary else "  [DECAYING]"))
