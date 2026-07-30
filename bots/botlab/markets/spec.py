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
        return edge * math.sqrt(self.bars_per_year)

    def summary(self) -> str:
        return (f"{self.name:<24} {self.asset_class:<10} vol={self.vol_ann:5.0%} "
                f"trend={self.trend_frac:4.2f} rev={self.rev_kappa:4.2f} "
                f"carry={self.carry_ann:+5.1%} spr={self.costs.spread_bps:5.1f}bp "
                f"ceiling_SR={self.oracle_sharpe_ceiling():4.2f}"
                + ("  [CONTROL]" if self.control else ""))
