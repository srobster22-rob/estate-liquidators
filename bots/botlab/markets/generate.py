"""Synthetic market generator.

One family + one seed = one instance, reproducibly. The generator plants
*named, bounded* structure — a persistent trend state, an anchor-reversion
pull, vol clustering, regimes, jumps, fat tails, a calendar effect, carry — so
that when a bot makes money we can say which phenomenon it ate, and check
whether the amount it ate is physically possible (`oracle_sharpe_ceiling`).

Limits, stated up front so nobody over-reads a result:
  * Intrabar paths are synthesised from a range model, so stop-loss fills are
    approximations, not observed ticks.
  * Structure is stationary within an instance apart from the regime switch.
    Real markets decay their edges; that is what `markets/loader.py` is for.
  * Instances are independent. Cross-sectional and cross-asset effects
    (pairs, lead-lag, factor crowding) are out of scope for this generator.
"""

from __future__ import annotations

import math
import zlib

import numpy as np

from .series import Series
from .spec import MarketSpec


def instance_seed(spec_name: str, index: int) -> int:
    """Stable across processes and runs (Python's str hash is salted)."""
    return (zlib.crc32(spec_name.encode()) ^ (int(index) * 2654435761)) & 0x7FFFFFFF


def _innovations(rng: np.random.Generator, n: int, df: float) -> np.ndarray:
    if df >= 30.0:
        return rng.standard_normal(n)
    t = rng.standard_t(df, n)
    return t / math.sqrt(df / (df - 2.0))


def _seasonal(spec: MarketSpec, n: int) -> tuple[np.ndarray, np.ndarray]:
    """(drift_component_in_sigmas, vol_multiplier) per bar."""
    if spec.seasonal_amp <= 0.0:
        return np.zeros(n), np.ones(n)
    p = max(int(spec.seasonal_period), 2)
    phase = 2.0 * math.pi * (np.arange(n) % p) / p
    if spec.seasonal_shape == "u":
        # Intraday: U-shaped volatility, plus an open-drift / close-drift tilt.
        vol_mult = 1.0 + 0.55 * np.cos(phase)          # high at session edges
        drift = spec.seasonal_amp * np.sin(phase)
        return drift, vol_mult
    return spec.seasonal_amp * np.sin(phase), np.ones(n)


STRESS_EXIT_RATIO = 8.0     # stress state is 8x more likely to end than to start


def _noise_scale(spec: MarketSpec, seas_vol: np.ndarray) -> float:
    """Rescale the innovation so realised volatility actually equals `vol_ann`.

    Regimes, seasonal vol and jumps all add variance on top of the innovation,
    so without this the parameter `vol_ann` is a lie: the first version of this
    generator asked for 16% and delivered 22%. Everything downstream sizes
    positions off realised vol, so the error was not fatal — but a market
    parameter that does not mean what it says is a trap for the next person.
    """
    stress_frac = 0.0
    if spec.regime_switch_prob > 0.0:
        stress_frac = 1.0 / (1.0 + STRESS_EXIT_RATIO)
    regime_m2 = (1.0 - stress_frac) + stress_frac * spec.regime_vol_mult ** 2
    seas_m2 = float(np.mean(seas_vol ** 2)) if seas_vol.size else 1.0
    e_vm2 = regime_m2 * seas_m2

    jump_var = spec.jump_prob * (spec.jump_mean ** 2 + spec.jump_scale ** 2)
    seas_drift_var = 0.5 * spec.seasonal_amp ** 2
    budget = 1.0 - spec.trend_frac ** 2 - jump_var - seas_drift_var
    return math.sqrt(max(budget, 0.05) / max(e_vm2, 1e-9))


PROBE_BASE = 999_000       # instance indices reserved for volatility calibration


def measure_vol_fix(spec: MarketSpec, n_probe: int = 24, iterations: int = 3) -> float:
    """Compute the `vol_fix` constant for a family. Offline only.

    `_noise_scale` corrects the variance added by regimes, seasonal vol and
    jumps analytically. What it cannot correct is the fat-tailed,
    near-integrated GARCH families (alpha+beta ~ 0.98 with Student-t df 4, where
    the fourth moment barely exists): the unconditional variance is right, but
    the sampling distribution of realised vol is so skewed that a typical
    realisation misses by up to 20%. Asking for 55% delivered 43%.

    Measured by iteration because jump size is specified in units of the
    *nominal* sigma and therefore does not move when the innovation is rescaled,
    so a single pass overshoots on the jumpy families.

    The log-return path is homogeneous of degree one in the innovation scale, so
    applying this factor is exactly equivalent to having chosen a different sigma
    — a reparameterisation, not a distortion. Instance-level vol dispersion is
    untouched, which is why the test asserts the *median* across instances.
    """
    fix = 1.0
    for _ in range(max(1, iterations)):
        vols = [synth(spec, PROBE_BASE + k, _noise_mult=fix, _apply_fix=False).realised_vol_ann()
                for k in range(n_probe)]
        vols = [v for v in vols if v > 0]
        if not vols:
            break
        fix *= float(np.clip(spec.vol_ann / float(np.median(vols)), 0.5, 2.0))
    return round(float(np.clip(fix, 0.4, 2.5)), 4)


def bars_from_log_returns(spec: MarketSpec, lr_arr: np.ndarray, sig_arr: np.ndarray,
                          rng: np.random.Generator) -> tuple:
    """(open, high, low, close, volume) from a log-return path and its vol path.

    Factored out of `synth` so that anything else generating a price path — the
    correlated baskets in `markets/basket.py` — uses the *same* bar model rather
    than a second one that could quietly disagree. The Brownian-bridge intrabar
    extremes below are the single most safety-critical piece of the generator
    (F6), and there must be exactly one copy of them.
    """
    n = lr_arr.size
    close = 100.0 * np.exp(np.cumsum(lr_arr))
    prev_close = np.empty(n)
    prev_close[0] = 100.0
    prev_close[1:] = close[:-1]

    # THE OVERNIGHT GAP IS A SEPARATE DRAW, NOT A SLICE OF THE SAME NUMBER.
    #
    # This used to be `gap = gap_frac * lr`, which makes the open a deterministic
    # function of the bar's own close-to-close return — correlation exactly 1. A
    # strategy that transacts at the open therefore observes the gap and knows the
    # rest of the bar precisely, because they are the same random variable split
    # in two. Real bars do not work that way: overnight news and the intraday
    # session are different events.
    #
    # What that bought: a 12-leg dollar-neutral cross-sectional book earned +0.147
    # gross alpha Sharpe on a basket with *no* effect planted, scaling linearly
    # with `gap_frac` and vanishing at zero (FINDINGS.md F31). Single instruments
    # were unaffected, which is why the existing controls never caught it.
    #
    # The fix keeps `gap_frac` meaning what it says — the share of the bar's
    # variance that happens overnight — while making the two components
    # *uncorrelated*. Writing u for the gap and d = lr - u for the intraday move,
    #
    #     u = f*lr + sqrt(f*(1-f)) * sigma * xi,     xi ~ N(0,1) independent
    #
    # gives var(u) = f*var(lr), var(d) = (1-f)*var(lr) and cov(u, d) = 0 exactly,
    # so the variance split is unchanged and the deterministic link is gone.
    # corr(u, lr) falls from 1 to sqrt(f), which is the whole point: seeing the
    # gap still tells you something about the bar, just no longer everything.
    #
    # `close` is untouched — it is built from `lr_arr` above — so every planted
    # structure, every vol_fix constant and every realised-vol target survives
    # this change. Only the open and, through it, the intrabar extremes move.
    f = float(np.clip(spec.gap_frac, 0.0, 1.0))
    if f <= 0.0:
        gap = np.zeros(n)
    elif f >= 1.0:
        gap = lr_arr.copy()
    else:
        xi = rng.standard_normal(n)
        gap = f * lr_arr + math.sqrt(f * (1.0 - f)) * sig_arr * xi
    open_ = prev_close * np.exp(gap)

    # Intrabar extremes as the running max/min of a BROWNIAN BRIDGE from the open
    # to the close. This is not cosmetic. The first version drew the high and low
    # as independent excursions above max(o,c) and below min(o,c), unconditional on
    # the bar's own return — which destroys the martingale property of the path and
    # therefore breaks optional stopping. The engine reads "high >= take level" as
    # "the limit filled at the take level", so a take-profit with no stop harvested
    # favourable excursions the price never actually traversed. Bots exploiting it
    # earned +0.31 to +0.35 alpha Sharpe on a pure iid random walk, and were caught
    # only by the G3 negative-control market.
    #
    # For a bridge 0 -> delta over one bar with log-vol s, P(max >= m) =
    # exp(-2m(m-delta)/s^2) for m >= max(0, delta), which inverts in closed form.
    # Sampling the max and min independently is an approximation (they are
    # negatively dependent), but every draw satisfies max >= max(0, delta) and
    # min <= min(0, delta) by construction, so the OHLC stays consistent — and the
    # conditioning on delta, which is the part that matters, is now correct.
    delta = np.log(close / open_)
    s_intra = np.maximum(sig_arr * spec.range_mult, 1e-12)
    var_intra = s_intra * s_intra
    u_hi = np.clip(rng.random(n), 1e-12, 1.0 - 1e-12)
    u_lo = np.clip(rng.random(n), 1e-12, 1.0 - 1e-12)
    m_up = 0.5 * (delta + np.sqrt(delta * delta - 2.0 * var_intra * np.log(u_hi)))
    m_dn = 0.5 * (delta - np.sqrt(delta * delta - 2.0 * var_intra * np.log(u_lo)))
    high = np.maximum(open_ * np.exp(m_up), np.maximum(open_, close))
    low = np.minimum(open_ * np.exp(m_dn), np.minimum(open_, close))

    base_units = spec.costs.adv_notional / close
    vol_noise = np.exp(0.45 * rng.standard_normal(n)
                       + 0.8 * np.abs(lr_arr) / max(spec.sigma_bar, 1e-12) * 0.25)
    volume = base_units * vol_noise

    return open_, high, low, close, volume


def synth(spec: MarketSpec, index: int, n_bars: int | None = None,
          _noise_mult: float = 1.0, _apply_fix: bool = True) -> Series:
    """Generate instance `index` of market family `spec`."""
    n = int(n_bars or spec.n_bars)
    seed = instance_seed(spec.seed_name or spec.name, index)
    rng = np.random.default_rng(seed)

    sigma_bar = spec.sigma_bar
    eps = _innovations(rng, n, spec.tail_df)
    w_trend = rng.standard_normal(n)
    u_switch = rng.random(n)
    u_jump = rng.random(n)
    z_jump = rng.standard_normal(n)
    seas_drift, seas_vol = _seasonal(spec, n)

    noise_k = _noise_scale(spec, seas_vol) * float(_noise_mult)
    if _apply_fix:
        noise_k *= float(spec.vol_fix)
    sigma_noise = sigma_bar * noise_k

    a, b = float(spec.garch_alpha), float(spec.garch_beta)
    if a + b >= 0.995:                      # keep the vol process stationary
        b = 0.995 - a
    omega = sigma_noise * sigma_noise * (1.0 - a - b)
    lam = 1.0 - 0.5 ** (1.0 / max(spec.rev_halflife, 1.0))
    rho = float(spec.trend_rho)
    s_tr = float(spec.trend_frac) * sigma_bar
    tr_shock = math.sqrt(max(1.0 - rho * rho, 1e-9)) * s_tr
    mu_bar = (spec.drift_ann + spec.carry_ann) / spec.bars_per_year

    logp = 0.0
    anchor = 0.0
    trend = s_tr * w_trend[0]
    sigma2 = sigma_noise * sigma_noise
    state = 0

    log_close = np.empty(n)
    lr_arr = np.empty(n)
    sig_arr = np.empty(n)

    p_enter = spec.regime_switch_prob
    p_exit = min(1.0, spec.regime_switch_prob * STRESS_EXIT_RATIO)
    clip_eps = float(spec.garch_clip)
    sigma2_cap = (float(spec.vol_cap_mult) * sigma_noise) ** 2
    move_cap = float(spec.max_bar_move_sigma) * sigma_bar
    edge = spec.edge_profile(n)

    for t in range(n):
        if p_enter > 0.0 and u_switch[t] < (p_exit if state else p_enter):
            state ^= 1
        vol_mult = (spec.regime_vol_mult if state else 1.0) * seas_vol[t]
        drift_mult = (spec.regime_drift_mult if state else 1.0)

        sigma_t = math.sqrt(sigma2) * vol_mult
        trend = rho * trend + tr_shock * w_trend[t]
        disloc = logp - anchor                       # strictly prior-bar information
        rev = -spec.rev_kappa * disloc
        jump = 0.0
        if spec.jump_prob > 0.0 and u_jump[t] < spec.jump_prob:
            jump = sigma_bar * (spec.jump_mean + spec.jump_scale * z_jump[t])

        shock = sigma_t * eps[t]
        # `edge[t]` scales only the predictable part. Drift, volatility, GARCH and
        # jumps are untouched, so a decaying family still looks like the same
        # instrument — it just stops being forecastable.
        lr = (mu_bar * drift_mult
              + edge[t] * (trend + rev + seas_drift[t] * sigma_bar)
              + shock + jump)
        if lr > move_cap:                       # limit-up / circuit breaker
            lr = move_cap
        elif lr < -move_cap:
            lr = -move_cap

        # GARCH update uses the *unscaled* shock so the regime multiplier does not
        # compound into the long-run variance, and a *winsorised* one so the
        # recursion has a finite fourth moment even where tail_df <= 4 (see
        # MarketSpec.garch_clip). The return above already used the full innovation,
        # so prices keep their fat tails; only the variance feedback is tamed.
        eps_var = eps[t]
        if eps_var > clip_eps:
            eps_var = clip_eps
        elif eps_var < -clip_eps:
            eps_var = -clip_eps
        base_shock = math.sqrt(sigma2) * eps_var
        sigma2 = omega + a * base_shock * base_shock + b * sigma2
        if sigma2 > sigma2_cap:
            sigma2 = sigma2_cap

        logp += lr
        anchor += lam * (logp - anchor)
        log_close[t] = logp
        lr_arr[t] = lr
        sig_arr[t] = sigma_t

    open_, high, low, close, volume = bars_from_log_returns(
        spec, lr_arr, sig_arr, rng)

    return Series(
        name=f"{spec.name}#{index}",
        open=open_, high=high, low=low, close=close, volume=volume,
        spec=spec, seed=seed,
        meta={"index": index, "generator": "synth-v1"},
    )


_CACHE: dict[tuple, Series] = {}
_CACHE_ORDER: list[tuple] = []
_CACHE_MAX = 600


def cached(spec: MarketSpec, index: int, n_bars: int | None = None) -> Series:
    """Instances are deterministic, so generating one twice is pure waste; the
    gauntlet re-reads the same holdout instances for every candidate."""
    key = (spec.name, int(index), int(n_bars or spec.n_bars))
    hit = _CACHE.get(key)
    if hit is not None:
        return hit
    s = synth(spec, index, n_bars)
    _CACHE[key] = s
    _CACHE_ORDER.append(key)
    if len(_CACHE_ORDER) > _CACHE_MAX:
        _CACHE.pop(_CACHE_ORDER.pop(0), None)
    return s


def bootstrap_like(series: Series, rng: np.random.Generator, block: int = 5) -> Series:
    """A null-hypothesis twin of `series`.

    Bars are resampled in circular blocks, each bar keeping its own shape
    (open/high/low offsets from its close) and its return magnitude. What
    survives: the return distribution, the fat tails, the drift, the intrabar
    geometry, the cost model. What is destroyed: serial dependence beyond
    `block` bars — i.e. exactly the trend and reversion structure a timing bot
    claims to exploit.

    A bot that scores as well on these as on the real thing has not found an
    edge; it has found the return distribution.
    """
    from .. import stats as _stats                      # local: avoid import cycle

    n = len(series)
    c = series.close
    lr = np.zeros(n)
    lr[1:] = np.log(c[1:] / c[:-1])
    a = np.log(series.open / c)
    b = np.log(np.maximum(series.high, c) / c)
    d = np.log(np.minimum(series.low, c) / c)

    idx = _stats.block_bootstrap_indices(n, block, rng)
    lr_new = lr[idx]
    lr_new[0] = 0.0
    close = float(c[0]) * np.exp(np.cumsum(lr_new))
    open_ = close * np.exp(a[idx])
    high = np.maximum.reduce([close * np.exp(b[idx]), open_, close])
    low = np.minimum.reduce([close * np.exp(d[idx]), open_, close])
    volume = series.volume[idx]

    return Series(name=f"{series.name}~null", open=open_, high=high, low=low,
                  close=close, volume=volume, spec=series.spec, seed=None,
                  meta={**series.meta, "null": True, "block": int(block)})


def calibration_row(spec: MarketSpec, n_instances: int = 8) -> dict:
    """Measured properties of a family — the reality check on its parameters."""
    vols, ac1, hurst_ish, dd = [], [], [], []
    for i in range(n_instances):
        s = synth(spec, 5_000 + i)
        lr = s.log_returns()[1:]
        vols.append(float(lr.std(ddof=1) * math.sqrt(spec.bars_per_year)))
        if lr.size > 30 and lr.std() > 0:
            ac1.append(float(np.corrcoef(lr[:-1], lr[1:])[0, 1]))
            k = 20
            agg = lr[: (lr.size // k) * k].reshape(-1, k).sum(axis=1)
            if agg.size > 5 and agg.std() > 0:
                hurst_ish.append(float(agg.std(ddof=1) / (lr.std(ddof=1) * math.sqrt(k))))
        eq = s.close / s.close[0]
        dd.append(float((eq / np.maximum.accumulate(eq) - 1.0).min()))
    return {
        "market": spec.name,
        # Median, not mean: crypto_alt_hourly has tail_df 3.2 and jump_scale 6, so
        # one outlier instance dragged the reported volatility to 148% against a
        # 110% target while the median sat at 107%. A mean is the wrong summary
        # for a deliberately fat-tailed family.
        "vol_ann": float(np.median(vols)),
        "target_vol": spec.vol_ann,
        "autocorr1": float(np.mean(ac1)) if ac1 else 0.0,
        "vol_ratio_20bar": float(np.mean(hurst_ish)) if hurst_ish else 1.0,
        "max_dd": float(np.mean(dd)),
        "ceiling_sr": spec.oracle_sharpe_ceiling(),
    }
