"""Statistics that the gauntlet needs and scipy would otherwise provide.

Deliberately dependency-light: numpy only. Everything here is a gate in the
validation ladder, so each function states what it assumes.
"""

from __future__ import annotations

import math

import numpy as np

EULER_MASCHERONI = 0.5772156649015329


def norm_cdf(x: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation).

    Absolute error < 1.15e-9 over the open interval, which is far tighter than
    anything the gauntlet's thresholds are sensitive to.
    """
    if p <= 0.0:
        return -math.inf
    if p >= 1.0:
        return math.inf

    a = (-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00)
    b = (-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00)

    p_low, p_high = 0.02425, 1.0 - 0.02425
    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    return x


def moments(r: np.ndarray) -> tuple[float, float, float, float]:
    """(mean, std, skew, kurtosis) — std is the sample (ddof=1) estimate,
    kurtosis is *raw* (3.0 for a normal), matching the PSR literature."""
    n = r.size
    if n < 3:
        return 0.0, 0.0, 0.0, 3.0
    mu = float(r.mean())
    sd = float(r.std(ddof=1))
    if sd <= 0.0 or not math.isfinite(sd):
        return mu, 0.0, 0.0, 3.0
    z = (r - mu) / sd
    skew = float((z ** 3).mean())
    kurt = float((z ** 4).mean())
    return mu, sd, skew, kurt


def sharpe(r: np.ndarray, bars_per_year: float) -> float:
    """Annualised Sharpe of a per-bar simple-return series, rf=0."""
    if r.size < 3:
        return 0.0
    sd = float(r.std(ddof=1))
    if sd <= 1e-12 or not math.isfinite(sd):
        return 0.0
    return float(r.mean()) / sd * math.sqrt(bars_per_year)


def psr(r: np.ndarray, bars_per_year: float, sr_benchmark: float = 0.0) -> float:
    """Probabilistic Sharpe Ratio: P(true SR > benchmark) given the observed
    sample, adjusted for non-normality (Bailey & Lopez de Prado 2012).

    Non-normality matters here because leveraged, stop-loss strategies are
    left-skewed and fat-tailed, which inflates a naive Sharpe t-stat.
    """
    n = r.size
    if n < 8:
        return 0.0
    sr_hat = sharpe(r, bars_per_year)
    _, _, skew, kurt = moments(r)
    # Convert to per-bar Sharpe for the standard-error formula.
    sr_bar = sr_hat / math.sqrt(bars_per_year)
    sr_b_bar = sr_benchmark / math.sqrt(bars_per_year)
    denom = 1.0 - skew * sr_bar + 0.25 * (kurt - 1.0) * sr_bar * sr_bar
    if denom <= 1e-12:
        return 0.0
    z = (sr_bar - sr_b_bar) * math.sqrt(n - 1) / math.sqrt(denom)
    return norm_cdf(z)


def expected_max_sharpe(n_trials: int, var_trial_sharpe: float) -> float:
    """Expected maximum annualised Sharpe attainable by chance across
    `n_trials` independent trials whose Sharpes have variance
    `var_trial_sharpe` (Bailey & Lopez de Prado, deflated Sharpe).

    This is the number that makes a search honest: run 5,000 strategies and the
    best one looks good *for free*. This says how good "for free" is.
    """
    n = max(int(n_trials), 2)
    v = max(float(var_trial_sharpe), 1e-12)
    g = EULER_MASCHERONI
    term = (1.0 - g) * norm_ppf(1.0 - 1.0 / n) + g * norm_ppf(1.0 - 1.0 / (n * math.e))
    return math.sqrt(v) * term


def deflated_sharpe(r: np.ndarray, bars_per_year: float, n_trials: int,
                    var_trial_sharpe: float) -> tuple[float, float]:
    """(DSR, sr_threshold) — the probability the strategy's true Sharpe beats
    the best-by-luck benchmark implied by the size of the search."""
    sr0 = expected_max_sharpe(n_trials, var_trial_sharpe)
    return psr(r, bars_per_year, sr_benchmark=sr0), sr0


def t_stat(r: np.ndarray) -> float:
    """t-statistic of the mean return against zero (iid assumption)."""
    if r.size < 3:
        return 0.0
    sd = float(r.std(ddof=1))
    if sd <= 1e-12:
        return 0.0
    return float(r.mean()) / (sd / math.sqrt(r.size))


def alpha_beta(r: np.ndarray, mkt: np.ndarray) -> tuple[float, float, float]:
    """OLS of strategy returns on market returns.

    Returns (alpha_per_bar, beta, alpha_t_stat). Guards against a
    long-only bot passing the gauntlet on borrowed market beta.
    """
    n = min(r.size, mkt.size)
    if n < 8:
        return 0.0, 0.0, 0.0
    y = r[:n].astype(float)
    x = mkt[:n].astype(float)
    vx = float(x.var(ddof=1))
    if vx <= 1e-18:
        return float(y.mean()), 0.0, t_stat(y)
    beta = float(np.cov(y, x, ddof=1)[0, 1] / vx)
    alpha = float(y.mean() - beta * x.mean())
    resid = y - beta * x
    sd = float(resid.std(ddof=1))
    if sd <= 1e-15:
        return alpha, beta, 0.0
    return alpha, beta, alpha / (sd / math.sqrt(n))


def block_bootstrap_indices(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Circular moving-block bootstrap index vector.

    Preserves the marginal distribution and *within-block* dependence while
    destroying dependence across blocks. Used to build the null hypothesis
    "this market has no exploitable structure at the horizons this bot trades".
    """
    block = max(1, min(int(block), n))
    n_blocks = int(math.ceil(n / block))
    starts = rng.integers(0, n, size=n_blocks)
    idx = (starts[:, None] + np.arange(block)[None, :]) % n
    return idx.reshape(-1)[:n]


def pct_rank(value: float, sample: np.ndarray) -> float:
    """Fraction of `sample` strictly below `value` (0..1)."""
    if sample.size == 0:
        return 0.0
    return float(np.mean(sample < value))
