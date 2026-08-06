"""The market catalogue — "all different types of markets".

Thirteen tradeable families across seven asset classes, plus two negative
controls. **Every tradeable family's edge decays.** Real anomalies get crowded,
published and arbitraged, and the ones that survive shrink; a catalogue whose
structure is identical at bar 12,000 and bar 1 flatters every strategy tested on
it.

The default is a halflife of half the series with a 35% floor — the edge halves
once across ~24 simulated years and keeps about a third of itself. That split is
deliberate: only the *predictable* components fade (trend, reversion, calendar),
while `drift_ann` and `carry_ann` do not, because a risk premium is compensation
for bearing risk rather than a mispricing waiting to be arbitraged away.

The rate is the mildest setting that still tests anything. Measured against the
archetype panel, decay costs about a third of the achievable alpha Sharpe
(catalogue mean +0.36 -> +0.24); at a quarter-series halflife it costs about half
(+0.19), which puts nearly every family under the certification bar and leaves the
lab measuring nothing. So this is a modelling choice made to keep the catalogue
discriminating, not an estimate of how fast real anomalies die — published
post-publication decay is far more abrupt, and that case is `eq_largecap_break_daily`.

Two families remain deliberately harsher than the default, as the fast-crowding
and structural-break cases. Every
number is a claim about the real world, so each family carries the claim it is
making in `notes`. Where a claim is wrong, the fix is to change it here and
re-run `python bots/run.py calibrate` — nothing downstream hard-codes a market.

Seed pools are disjoint on purpose:
  SEARCH   — the only instances the search loop is ever allowed to see
  HOLDOUT  — replication instances, first touched inside the gauntlet
  STRESS   — third pool, used for the final confirmation of proven bots
"""

from __future__ import annotations

from .spec import CostModel, MarketSpec

SEARCH_POOL = range(1, 400)
HOLDOUT_POOL = range(100_000, 100_400)
STRESS_POOL = range(200_000, 200_400)

DAY = 252.0
HOUR_24_7 = 365.0 * 24.0
BAR_15M = 252.0 * 26.0

_MARKETS: list[MarketSpec] = [
    MarketSpec(
        name="eq_index_daily", asset_class="equity", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.07, vol_ann=0.16, trend_frac=0.090, trend_rho=0.97,
        rev_kappa=0.010, rev_halflife=10.0,
        garch_alpha=0.09, garch_beta=0.87, regime_switch_prob=0.006,
        regime_vol_mult=2.2, regime_drift_mult=-1.5,
        jump_prob=0.0015, jump_mean=-2.0, jump_scale=2.5, tail_df=5.0,
        gap_frac=0.30, range_mult=1.0,
        costs=CostModel(spread_bps=1.5, commission_bps=0.3, impact_coef_bps=8.0,
                        adv_notional=5e9, borrow_ann=0.004, financing_ann=0.05),
        edge_decay_halflife=6000.0, edge_decay_floor=0.35,
        vol_fix=1.056,
        allow_short=True, max_leverage=2.0, tier=1,
        notes="Index futures/ETF. Equity risk premium, modest 12m momentum, vol clustering, crash-skewed jumps.",
    ),
    MarketSpec(
        name="eq_largecap_daily", asset_class="equity", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.08, vol_ann=0.28, trend_frac=0.040, trend_rho=0.975,
        rev_kappa=0.030, rev_halflife=6.0,
        garch_alpha=0.08, garch_beta=0.88, regime_switch_prob=0.005,
        jump_prob=0.003, jump_mean=-1.0, jump_scale=3.5, tail_df=4.5,
        gap_frac=0.35,
        costs=CostModel(spread_bps=3.0, commission_bps=0.5, impact_coef_bps=15.0,
                        adv_notional=4e8, borrow_ann=0.006, financing_ann=0.055),
        edge_decay_halflife=6000.0, edge_decay_floor=0.35,
        vol_fix=1.0736,
        tier=1,
        notes="Single large-cap. Both effects live here: 12m momentum plus 1-week reversal.",
    ),
    MarketSpec(
        name="eq_smallcap_daily", asset_class="equity", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.06, vol_ann=0.45, trend_frac=0.070, trend_rho=0.97,
        rev_kappa=0.050, rev_halflife=5.0,
        garch_alpha=0.10, garch_beta=0.85, regime_switch_prob=0.006,
        jump_prob=0.005, jump_mean=-1.5, jump_scale=4.0, tail_df=3.6,
        gap_frac=0.40, range_mult=1.0,
        costs=CostModel(spread_bps=28.0, commission_bps=1.0, impact_coef_bps=70.0,
                        adv_notional=6e6, borrow_ann=0.045, financing_ann=0.07),
        edge_decay_halflife=6000.0, edge_decay_floor=0.35,
        vol_fix=1.1457,
        max_leverage=1.5, tier=2,
        notes="Illiquid small-cap: the strongest planted edges in the catalogue, behind the widest costs. The trap market.",
    ),
    MarketSpec(
        name="fx_major_daily", asset_class="fx", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.0, vol_ann=0.08, carry_ann=0.012,
        trend_frac=0.110, trend_rho=0.985, rev_kappa=0.010, rev_halflife=12.0,
        garch_alpha=0.06, garch_beta=0.91, tail_df=6.0, gap_frac=0.05,
        costs=CostModel(spread_bps=0.8, commission_bps=0.15, impact_coef_bps=5.0,
                        adv_notional=2e10, borrow_ann=0.0, financing_ann=0.03),
        edge_decay_halflife=6000.0, edge_decay_floor=0.35,
        vol_fix=1.0296,
        max_leverage=6.0, tier=1,
        notes="G10 pair. No risk premium at all — every dollar has to come from trend or carry.",
    ),
    MarketSpec(
        name="fx_em_daily", asset_class="fx", bars_per_year=DAY, n_bars=12000,
        drift_ann=-0.015, vol_ann=0.14, carry_ann=0.055,
        trend_frac=0.080, trend_rho=0.985, rev_kappa=0.012, rev_halflife=15.0,
        garch_alpha=0.09, garch_beta=0.88, regime_switch_prob=0.004,
        regime_vol_mult=2.6, regime_drift_mult=-3.0,
        jump_prob=0.002, jump_mean=-4.0, jump_scale=4.0, tail_df=3.5, gap_frac=0.10,
        costs=CostModel(spread_bps=6.0, commission_bps=0.5, impact_coef_bps=25.0,
                        adv_notional=8e8, borrow_ann=0.0, financing_ann=0.06),
        edge_decay_halflife=6000.0, edge_decay_floor=0.35,
        vol_fix=1.2149,
        max_leverage=3.0, tier=2,
        notes="EM carry: paid to hold, occasionally devalued. Tests whether the gauntlet respects tail risk.",
    ),
    MarketSpec(
        name="crypto_major_hourly", asset_class="crypto", bars_per_year=HOUR_24_7, n_bars=36000,
        drift_ann=0.35, vol_ann=0.55,
        trend_frac=0.018, trend_rho=0.995, rev_kappa=0.005, rev_halflife=24.0,
        garch_alpha=0.12, garch_beta=0.86, regime_switch_prob=0.0015,
        regime_vol_mult=2.0, regime_drift_mult=-2.0,
        jump_prob=0.0008, jump_mean=-1.5, jump_scale=4.0, tail_df=4.0,
        gap_frac=0.02, range_mult=1.0,
        costs=CostModel(spread_bps=4.0, commission_bps=3.0, impact_coef_bps=30.0,
                        adv_notional=3e8, borrow_ann=0.02, financing_ann=0.09,
                        funding_bps_per_bar=0.12),
        edge_decay_halflife=18000.0, edge_decay_floor=0.35,
        vol_fix=1.268,
        max_leverage=3.0, tier=1,
        notes="BTC/ETH perp, hourly. Strong slow trend, funding charged to longs every bar.",
    ),
    MarketSpec(
        name="crypto_alt_hourly", asset_class="crypto", bars_per_year=HOUR_24_7, n_bars=36000,
        drift_ann=0.0, vol_ann=1.10,
        trend_frac=0.016, trend_rho=0.99, rev_kappa=0.008, rev_halflife=12.0,
        garch_alpha=0.14, garch_beta=0.83, regime_switch_prob=0.003,
        jump_prob=0.0015, jump_mean=-1.0, jump_scale=6.0, tail_df=3.2,
        gap_frac=0.02, range_mult=1.0,
        costs=CostModel(spread_bps=25.0, commission_bps=5.0, impact_coef_bps=140.0,
                        adv_notional=1.5e7, borrow_ann=0.05, financing_ann=0.14,
                        funding_bps_per_bar=0.30),
        edge_decay_halflife=18000.0, edge_decay_floor=0.35,
        vol_fix=1.3903,
        max_leverage=2.0, tier=3,
        notes="Alt perp. Violent reversal edge, funding and spread built to eat it.",
    ),
    MarketSpec(
        name="futures_trend_daily", asset_class="futures", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.01, vol_ann=0.14, carry_ann=0.020,
        trend_frac=0.085, trend_rho=0.99, rev_kappa=0.0,
        garch_alpha=0.07, garch_beta=0.90, tail_df=6.0, gap_frac=0.15,
        costs=CostModel(spread_bps=1.5, commission_bps=0.3, impact_coef_bps=7.0,
                        adv_notional=3e9, borrow_ann=0.0, financing_ann=0.04),
        edge_decay_halflife=6000.0, edge_decay_floor=0.35,
        vol_fix=1.0322,
        max_leverage=5.0, tier=1,
        notes="Classic managed-futures substrate: long persistent trends, positive roll, cheap access.",
    ),
    MarketSpec(
        name="commodity_meanrev_daily", asset_class="commodity", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.0, vol_ann=0.35, carry_ann=-0.03,
        trend_frac=0.020, trend_rho=0.95, rev_kappa=0.030, rev_halflife=8.0,
        seasonal_amp=0.030, seasonal_period=21, seasonal_shape="sin",
        garch_alpha=0.11, garch_beta=0.84,
        jump_prob=0.004, jump_mean=1.2, jump_scale=4.5, tail_df=3.8, gap_frac=0.20,
        costs=CostModel(spread_bps=5.0, commission_bps=0.6, impact_coef_bps=30.0,
                        adv_notional=4e8, borrow_ann=0.0, financing_ann=0.05),
        edge_decay_halflife=6000.0, edge_decay_floor=0.35,
        vol_fix=1.1244,
        max_leverage=3.0, tier=2,
        notes="Storage-economy commodity: hard reversion, calendar effect, upside spikes, negative roll.",
    ),
    MarketSpec(
        name="rates_daily", asset_class="rates", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.015, vol_ann=0.055, carry_ann=0.018,
        trend_frac=0.070, trend_rho=0.99, rev_kappa=0.008, rev_halflife=20.0,
        garch_alpha=0.06, garch_beta=0.92, tail_df=6.0, gap_frac=0.10,
        costs=CostModel(spread_bps=0.5, commission_bps=0.1, impact_coef_bps=4.0,
                        adv_notional=1e10, borrow_ann=0.0, financing_ann=0.012),
        edge_decay_halflife=6000.0, edge_decay_floor=0.35,
        vol_fix=1.0459,
        max_leverage=8.0, tier=2,
        notes="Bond future. Tiny vol, so the whole game is leverage discipline and financing cost.",
    ),
    MarketSpec(
        name="eq_intraday_15m", asset_class="equity", bars_per_year=BAR_15M, n_bars=31200,
        drift_ann=0.05, vol_ann=0.22,
        trend_frac=0.010, trend_rho=0.93, rev_kappa=0.012, rev_halflife=8.0,
        seasonal_amp=0.015, seasonal_period=26, seasonal_shape="u",
        garch_alpha=0.10, garch_beta=0.86, tail_df=4.0, gap_frac=0.10, range_mult=1.0,
        costs=CostModel(spread_bps=3.0, commission_bps=0.5, impact_coef_bps=20.0,
                        adv_notional=2e9, borrow_ann=0.005, financing_ann=0.055),
        edge_decay_halflife=15600.0, edge_decay_floor=0.35,
        vol_fix=1.1224,
        max_leverage=4.0, tier=2,
        notes="Intraday 15-minute bars: U-shaped session vol, open/close drift tilt, costs paid 26x more often.",
    ),
    # ---------------- non-stationary twins ---------------------------------
    # Deliberate near-clones of the two families that certify most readily, so
    # the *same* bot can be run on both and the only thing that differs is
    # whether its edge survives. A stationary result and a decaying result are
    # otherwise incomparable, and comparing them is the entire point.
    MarketSpec(
        name="futures_trend_decay_daily", asset_class="futures", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.01, vol_ann=0.14, carry_ann=0.020,
        trend_frac=0.085, trend_rho=0.99, rev_kappa=0.0,
        garch_alpha=0.07, garch_beta=0.90, tail_df=6.0, gap_frac=0.15,
        edge_decay_halflife=3000.0, edge_decay_floor=0.10,
        costs=CostModel(spread_bps=1.5, commission_bps=0.3, impact_coef_bps=7.0,
                        adv_notional=3e9, borrow_ann=0.0, financing_ann=0.04),
        vol_fix=1.0328,
        max_leverage=5.0, tier=1,
        notes="The fast-crowding case: trend halves every 3,000 bars (~12y) toward a 10% floor, against the catalogue default of 6,000 bars and a 35% floor. Same instrument, forecastability mostly gone.",
    ),
    MarketSpec(
        name="eq_largecap_break_daily", asset_class="equity", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.08, vol_ann=0.28, trend_frac=0.040, trend_rho=0.975,
        rev_kappa=0.030, rev_halflife=6.0,
        garch_alpha=0.08, garch_beta=0.88, regime_switch_prob=0.005,
        jump_prob=0.003, jump_mean=-1.0, jump_scale=3.5, tail_df=4.5,
        gap_frac=0.35,
        edge_break_at=0.45, edge_break_mult=0.15,
        costs=CostModel(spread_bps=3.0, commission_bps=0.5, impact_coef_bps=15.0,
                        adv_notional=4e8, borrow_ann=0.006, financing_ann=0.055),
        vol_fix=1.0699,
        tier=1,
        notes="The structural-break case: 85% of the edge vanishes on a date 45% of the way in, rather than fading. Publication, a rule change, a new venue. Closest family to the published post-publication decay literature.",
    ),
    # ---------------- negative controls -----------------------------------
    MarketSpec(
        name="control_efficient_daily", asset_class="control", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.06, vol_ann=0.20, trend_frac=0.0, rev_kappa=0.0,
        garch_alpha=0.07, garch_beta=0.90, tail_df=5.0, gap_frac=0.30,
        costs=CostModel(spread_bps=2.0, commission_bps=0.4, impact_coef_bps=10.0,
                        adv_notional=2e9, borrow_ann=0.005, financing_ann=0.05),
        vol_fix=1.0594,
        tier=1, control=True,
        notes="Drift + vol clustering, zero directional structure. Timing skill here is impossible; beating buy-and-hold is the tell.",
    ),
    MarketSpec(
        name="control_martingale_daily", asset_class="control", bars_per_year=DAY, n_bars=12000,
        drift_ann=0.0, vol_ann=0.20, trend_frac=0.0, rev_kappa=0.0,
        garch_alpha=0.0, garch_beta=0.0, tail_df=30.0, gap_frac=0.30,
        costs=CostModel(spread_bps=2.0, commission_bps=0.4, impact_coef_bps=10.0,
                        adv_notional=2e9, borrow_ann=0.005, financing_ann=0.05),
        vol_fix=1.0022,
        tier=1, control=True,
        notes="Pure iid Gaussian random walk, no drift. Any strategy that shows profit here after costs proves the harness is broken.",
    ),
]

BY_NAME: dict[str, MarketSpec] = {m.name: m for m in _MARKETS}


def register(spec: MarketSpec) -> None:
    """Add a family at runtime. Used by the false-positive-rate calibration,
    which needs a *tradeable* clone of a control market so the ladder cannot
    reject it at G0 and must actually work for its answer."""
    BY_NAME[spec.name] = spec
    if spec not in _MARKETS:
        _MARKETS.append(spec)


def unregister(name: str) -> None:
    spec = BY_NAME.pop(name, None)
    if spec is not None and spec in _MARKETS:
        _MARKETS.remove(spec)


def all_markets(include_controls: bool = True) -> list[MarketSpec]:
    return [m for m in _MARKETS if include_controls or not m.control]


def tradeable(tier: int = 3) -> list[MarketSpec]:
    """Non-control families unlocked at the given expansion tier."""
    return [m for m in _MARKETS if not m.control and m.tier <= tier]


def controls() -> list[MarketSpec]:
    return [m for m in _MARKETS if m.control]


def get(name: str) -> MarketSpec:
    if name not in BY_NAME:
        raise KeyError(f"unknown market '{name}'; known: {sorted(BY_NAME)}")
    return BY_NAME[name]


def asset_classes(tier: int = 3) -> list[str]:
    return sorted({m.asset_class for m in tradeable(tier)})
