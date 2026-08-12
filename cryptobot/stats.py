"""
The statistics that decide whether a backtest means anything.

This is the part of a bot factory that people skip, and skipping it is why bot
factories produce bots that lose money. If you generate ten thousand strategies and
keep the best one, its backtest Sharpe is not an estimate of its edge — it is an
estimate of the *maximum of ten thousand draws from a distribution centred on zero*,
which is around 3.9 sigma even when every single strategy is worthless.

Three defences live here:

  EXPECTED MAX SHARPE   How good the best of N worthless strategies looks. This is
                        the bar a candidate has to clear, and it rises with every
                        trial the factory burns.

  DEFLATED SHARPE       Bailey & López de Prado's probabilistic Sharpe ratio, using
                        the expected-max as the benchmark and correcting for the
                        non-normality (skew, fat tails) of strategy returns. Returns
                        the probability that the true Sharpe exceeds the benchmark.

  BOOTSTRAP / MC NULLS  Stationary block bootstrap for "is the mean return positive",
                        and a matched random-signal Monte Carlo for the sharper
                        question: "does the *timing* add anything a coin flip with
                        the same trade frequency wouldn't have got?"

References: Bailey & López de Prado (2014), "The Deflated Sharpe Ratio";
Politis & Romano (1994) for the stationary bootstrap.
"""

import math
import random

EULER = 0.5772156649015329


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p):
    """Inverse normal CDF, Acklam's rational approximation (|error| < 1.15e-9)."""
    if p <= 0.0:
        return -float("inf")
    if p >= 1.0:
        return float("inf")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def expected_max_sharpe(trials, sharpe_dispersion, bars_per_year=None):
    """Expected best Sharpe among `trials` strategies with true Sharpe zero and
    cross-sectional dispersion `sharpe_dispersion` (same units in, same units out).

        E[max] ≈ σ · [ (1-γ)·Φ⁻¹(1 - 1/N) + γ·Φ⁻¹(1 - 1/(N·e)) ]

    With 5,000 trials and a dispersion of 0.5, this is about 1.9 — meaning a 1.8
    Sharpe from a 5,000-strategy search is *below average luck*, not an edge."""
    n = max(2, int(trials))
    term = ((1 - EULER) * norm_ppf(1.0 - 1.0 / n)
            + EULER * norm_ppf(1.0 - 1.0 / (n * math.e)))
    return sharpe_dispersion * term


def probabilistic_sharpe(sharpe, benchmark, n, skew=0.0, kurt=3.0):
    """P(true Sharpe > benchmark), given an observed Sharpe over n observations.

    All three Sharpe arguments must be in the SAME period units as n. Pass per-bar
    Sharpe with n = number of bars; passing annualised Sharpe with a bar count is the
    single most common way to get a wildly overconfident number here."""
    if n < 3:
        return 0.0
    denom = 1.0 - skew * sharpe + (kurt - 1.0) / 4.0 * sharpe * sharpe
    if denom <= 1e-12:
        return 0.0
    z = (sharpe - benchmark) * math.sqrt(n - 1.0) / math.sqrt(denom)
    return norm_cdf(z)


def deflated_sharpe(metrics, trials, dispersion, bars_per_year):
    """Deflated Sharpe ratio: the probability that a strategy's true Sharpe beats
    what the best of `trials` worthless strategies would have shown.

    Returns (dsr, benchmark_annualised). Reject anything under ~0.95."""
    n = metrics["bars"]
    if n < 30:
        return 0.0, 0.0
    per_bar = metrics["sharpe"] / math.sqrt(bars_per_year)
    disp_bar = dispersion / math.sqrt(bars_per_year)
    bench = expected_max_sharpe(trials, disp_bar)
    dsr = probabilistic_sharpe(per_bar, bench, n, metrics["skew"],
                               metrics["kurtosis"])
    return dsr, bench * math.sqrt(bars_per_year)


def sharpe_needed(metrics, bench_annual, bars_per_year, confidence=0.95):
    """What annualised Sharpe this candidate would have had to post, on this much
    data, to clear the hurdle at `confidence`.

    Printed alongside a gate-10 failure because the raw verdict is uninformative on
    its own. "DSR 0.73" doesn't tell you whether the bot was close or whether the
    window was simply too short; "needed 3.2, posted 2.0, over 10 months" tells you
    the honest answer is usually MORE DATA, not a better bot."""
    n = metrics["bars"]
    if n < 30:
        return float("inf")
    ann = math.sqrt(bars_per_year)
    s_bar = metrics["sharpe"] / ann
    bench_bar = bench_annual / ann
    denom = (1.0 - metrics["skew"] * s_bar
             + (metrics["kurtosis"] - 1.0) / 4.0 * s_bar * s_bar)
    denom = max(denom, 1e-9)
    z = norm_ppf(confidence)
    needed_bar = bench_bar + z * math.sqrt(denom) / math.sqrt(n - 1.0)
    return needed_bar * ann


def null_sharpe_dispersion(years, sharpe=0.0):
    """Standard error of an annualised Sharpe estimate under the null of no edge.

        SE(S_hat) ~= sqrt((1 + S^2/2) / T)      T in years

    THIS is the sigma the expected-max correction needs, and getting it from the
    observed spread of the candidates instead was a real bug. Gate 10 asks: if these
    N strategies all had zero edge, how good would the luckiest look? That question
    is about SAMPLING NOISE in a Sharpe estimate, which depends only on the length
    of the window.

    The observed spread of promoted candidates is a different quantity entirely. Those
    are the survivors of an in-sample search, a mixed population of genuinely good and
    genuinely awful bots, and their spread is dominated by real quality differences
    rather than noise. On a 3.1-year validation slice the true null dispersion is
    0.56; the observed spread was 2.9, which pushed the hurdle to 6.5 and demanded an
    observed Sharpe of 7.4 before gate 10 would call anything real. Nothing in the
    universe could clear that, and the only bots that ever passed were the ones lucky
    enough to arrive in the first few looks, while the correction was still small.

    So the gate was not strict. It was miscalibrated in a way that made it strict
    later and lax early, which is worse than either.
    """
    return math.sqrt((1.0 + 0.5 * sharpe * sharpe) / max(1e-9, years))


def sharpe_dispersion(sharpes):
    """Cross-sectional stdev of the trial Sharpes. This is the σ the deflation needs,
    and it must come from the search's *own* population — borrowing a textbook 0.5
    understates the correction for a search that explores wildly different families."""
    vals = [s for s in sharpes if s is not None and math.isfinite(s)]
    if len(vals) < 3:
        return 0.5
    m = sum(vals) / len(vals)
    var = sum((s - m) ** 2 for s in vals) / (len(vals) - 1)
    return max(0.05, math.sqrt(var))


# ------------------------------------------------------------------ bootstrap

def stationary_bootstrap(series, rng, mean_block=20):
    """One resample preserving short-range dependence: geometric block lengths with
    wraparound. An IID bootstrap on autocorrelated strategy returns understates the
    variance and hands out significance for free."""
    n = len(series)
    p = 1.0 / mean_block
    out = []
    i = rng.randrange(n)
    while len(out) < n:
        out.append(series[i])
        if rng.random() < p:
            i = rng.randrange(n)
        else:
            i = (i + 1) % n
    return out


def bootstrap_pvalue(net, iterations=500, mean_block=20, seed=0):
    """P(mean return <= 0) under a stationary bootstrap of the realised returns,
    recentred to a zero-mean null. Small p means the positive mean is unlikely to be
    sampling noise — it says nothing about whether it was mined."""
    n = len(net)
    if n < 30:
        return 1.0
    rng = random.Random(seed)
    observed = sum(net) / n
    if observed <= 0:
        return 1.0
    centred = [x - observed for x in net]
    hits = 0
    for _ in range(iterations):
        sample = stationary_bootstrap(centred, rng, mean_block)
        if sum(sample) / n >= observed:
            hits += 1
    return (hits + 1.0) / (iterations + 1.0)


def matched_random_signals(position, count, rng):
    """Generate random position paths matched to a candidate's own trading profile.

    Matched on: the fraction of bars spent long, short and flat, and the probability
    of changing state per bar. So the null bot trades as often as the real one, is
    exposed as much as the real one, and pays the same fees — it just has no idea
    when. If the candidate can't beat that, its 'edge' is exposure, not timing."""
    n = len(position)
    states = [(1 if p > 0 else (-1 if p < 0 else 0)) for p in position]
    mags = {1: [], -1: []}
    for p, s in zip(position, states):
        if s:
            mags[s].append(abs(p))
    switches = sum(1 for i in range(1, n) if states[i] != states[i - 1])
    p_switch = switches / max(1, n - 1)
    counts = {s: states.count(s) for s in (-1, 0, 1)}
    total = sum(counts.values()) or 1
    weights = [counts[-1] / total, counts[0] / total, counts[1] / total]
    mean_mag = {s: (sum(v) / len(v) if v else 1.0) for s, v in mags.items()}

    out = []
    for _ in range(count):
        path = [0.0] * n
        state = rng.choices([-1, 0, 1], weights=weights)[0]
        for i in range(n):
            if rng.random() < p_switch:
                state = rng.choices([-1, 0, 1], weights=weights)[0]
            path[i] = 0.0 if state == 0 else state * mean_mag[state]
        out.append(path)
    return out


def mc_pvalue(candidate_sharpe, null_sharpes):
    """Fraction of null runs that matched or beat the candidate, with the standard
    +1 correction so a p-value can never be reported as exactly zero."""
    if not null_sharpes:
        return 1.0
    beat = sum(1 for s in null_sharpes if s >= candidate_sharpe)
    return (beat + 1.0) / (len(null_sharpes) + 1.0)


def benjamini_hochberg(pvalues, fdr=0.05):
    """Largest p-value that survives BH control of the false discovery rate at
    `fdr`. Used when several candidates are put forward at once."""
    if not pvalues:
        return 0.0
    ordered = sorted(pvalues)
    m = len(ordered)
    threshold = 0.0
    for k, p in enumerate(ordered, start=1):
        if p <= fdr * k / m:
            threshold = p
    return threshold
