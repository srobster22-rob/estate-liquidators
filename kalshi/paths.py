"""
The latent price engine — one construction that generates every market family.

WHY THIS MATTERS MORE THAN ANYTHING ELSE HERE

A bot factory backtested against a badly-built simulator will always succeed, because
almost any price series that isn't a martingale contains free money. If the synthetic
prices drift, or mean-revert, or fail to match their own realized frequencies, then
every "profitable" bot the loop produces is measuring a bug in this file. The factory's
output is worth exactly as much as this construction is correct, and no more.

So the prices here are a martingale BY CONSTRUCTION, not by tuning.

    Let X be a Gaussian random walk with total variance 1 over the market's life.
    Let the event be {X_final > k}.
    Then the true conditional probability at time t is

        p_t = P(X_final > k | X_t) = Phi( (X_t - k) / sqrt(v_remaining) )

    which is a conditional expectation of a fixed random variable, so E[p_{t+1} | X_t]
    = p_t exactly, for free, with no parameter to get wrong. And because the outcome is
    drawn from the same residual variance, the series is perfectly calibrated: contracts
    quoted at 30 resolve YES 30% of the time. `selftest.py` asserts both properties
    numerically and they are the first two things it checks.

Everything a market family can differ by is then a VARIANCE SCHEDULE — the shape of how
information arrives over the contract's life — plus microstructure, which lives in
`markets.py`. That is the whole taxonomy:

    uniform      information arrives smoothly            crypto hourly, index close
    print_shock  90% of it lands in a single step         CPI, jobs report, Fed
    convergence  accelerating as the date approaches      weather, forecast-driven
    jumpy        smooth base plus discrete shocks         sports (scores), news
    slow         thin, even trickle over a long horizon   politics, long-dated

Nothing in this file contains an exploitable edge. Every edge in this project is planted
deliberately in `markets.py`'s quoting layer, where it is named, sized, and documented —
so that when the loop finds something, it can be checked against a list of what was
actually put there.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Normal CDF / inverse CDF. stdlib has erf but not ppf.
# ---------------------------------------------------------------------------

_SQRT2 = math.sqrt(2.0)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / _SQRT2))


# Acklam's rational approximation, |error| < 1.15e-9 in probability.
_A = (-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
      1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00)
_B = (-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
      6.680131188771972e01, -1.328068155288572e01)
_C = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
      -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00)
_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
      3.754408661907416e00)


def norm_ppf(p: float) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError(f"norm_ppf domain is (0,1), got {p}")
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / \
               ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / \
                ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
    q = p - 0.5
    r = q * q
    return (((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q / \
           (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1.0)


def logit(p: float) -> float:
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    return math.log(p / (1.0 - p))


def expit(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


# ---------------------------------------------------------------------------
# Variance schedules — the entire difference between market families
# ---------------------------------------------------------------------------

# Fraction of total uncertainty still unresolved at the LAST quoted step. Real markets
# don't print 0 or 100 the tick before settlement; leaving a residual is also what makes
# the final outcome a genuine draw rather than a readback of the last price.
RESIDUAL_VAR = 0.03


def variance_schedule(kind: str, steps: int, rng, **kw) -> list[float]:
    """Per-step variance increments, summing to exactly 1 - RESIDUAL_VAR."""
    if steps < 2:
        raise ValueError("need at least 2 steps")

    if kind == "uniform":
        w = [1.0] * steps

    elif kind == "print_shock":
        # Flat, then one step carries almost everything. Where the print lands is
        # unknown to the bot: it has to infer it from the price move, which is exactly
        # the situation an econ-release bot is actually in.
        share = kw.get("shock_share", 0.90)
        at = kw.get("shock_at", rng.randint(int(steps * 0.45), int(steps * 0.75)))
        w = [(1.0 - share) / (steps - 1)] * steps
        w[at] = share

    elif kind == "convergence":
        # Forecast skill improves as the event nears: weight ~ (t+1)^gamma.
        g = kw.get("gamma", 1.6)
        w = [((i + 1) / steps) ** g for i in range(steps)]

    elif kind == "jumpy":
        # Smooth base plus a handful of discrete shocks (goals, injuries, headlines).
        n_jumps = kw.get("n_jumps", max(2, steps // 12))
        base = kw.get("base_share", 0.45)
        w = [base / steps] * steps
        for _ in range(n_jumps):
            w[rng.randrange(steps)] += (1.0 - base) / n_jumps

    elif kind == "slow":
        # Long-dated: a thin even trickle, with the last stretch carrying more as the
        # resolution date finally comes into view.
        w = [1.0] * steps
        tail = max(1, steps // 5)
        for i in range(steps - tail, steps):
            w[i] *= 2.5

    else:
        raise ValueError(f"unknown variance schedule {kind!r}")

    total = sum(w)
    scale = (1.0 - RESIDUAL_VAR) / total
    return [x * scale for x in w]


# ---------------------------------------------------------------------------
# Latent path
# ---------------------------------------------------------------------------

class LatentPath:
    """A realised random walk plus the true conditional probabilities along it.

    `true_p[t]` is the honest probability an omniscient modeller would quote at step t.
    `outcome` is drawn from the residual variance left after the final quoted step, so
    it is genuinely unknown at every step — there is no lookahead available even in
    principle.
    """

    __slots__ = ("x", "v_rem", "true_p", "outcome", "k", "steps")

    def __init__(self, steps: int, schedule: list[float], k: float, rng):
        self.steps = steps
        self.k = k
        x = 0.0
        v_used = 0.0
        self.x, self.v_rem, self.true_p = [], [], []
        for t in range(steps):
            dv = schedule[t]
            x += rng.gauss(0.0, math.sqrt(dv))
            v_used += dv
            v_rem = max(1.0 - v_used, 1e-12)
            self.x.append(x)
            self.v_rem.append(v_rem)
            self.true_p.append(norm_cdf((x - k) / math.sqrt(v_rem)))
        x_final = x + rng.gauss(0.0, math.sqrt(self.v_rem[-1]))
        self.outcome = 1 if x_final > k else 0

    def bracket_probs(self, t: int, edges: list[float]) -> list[float]:
        """Probabilities for a mutually exclusive, exhaustive set of intervals.

        Sums to exactly 1.0 up to float error, which is what makes bracket-sum
        arbitrage a real thing to look for rather than an artifact.
        """
        sd = math.sqrt(self.v_rem[t])
        xt = self.x[t]
        cuts = [norm_cdf((e - xt) / sd) for e in edges]
        probs = []
        prev = 0.0
        for c in cuts:
            probs.append(c - prev)
            prev = c
        probs.append(1.0 - prev)
        return probs

    def bracket_outcome(self, edges: list[float], rng) -> int:
        x_final = self.x[-1] + rng.gauss(0.0, math.sqrt(self.v_rem[-1]))
        for i, e in enumerate(edges):
            if x_final <= e:
                return i
        return len(edges)


def strike_for_initial_prob(p0: float) -> float:
    """k such that the market opens quoting p0. Lets a family draw a realistic mix of
    coin-flips and longshots instead of every market opening at 50c."""
    return -norm_ppf(p0)
