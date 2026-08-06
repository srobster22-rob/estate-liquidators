"""Performance measurement, including the two numbers that decide everything:
`alpha_sharpe` and `fitness`.

`sharpe` alone would let a long-only bot on a market with a 7% risk premium
look skilful for holding beta. So every gate in the gauntlet uses
`alpha_sharpe` — the Sharpe of the residual after regressing the bot's returns
on the underlying's — and `fitness`, which is the *smaller* of the two. A bot
that only has beta scores near zero. A bot with real timing skill scores the
same either way.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np

from . import stats
from .engine import BacktestResult


@dataclass
class Perf:
    n_bars: int = 0
    years: float = 0.0
    total_return: float = 0.0
    cagr: float = 0.0
    vol_ann: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    max_dd: float = 0.0
    calmar: float = 0.0
    hit_rate: float = 0.0
    profit_factor: float = 0.0
    worst_bar: float = 0.0
    tail_ratio: float = 0.0
    n_trades: int = 0
    turnover_ann: float = 0.0
    cost_drag_ann: float = 0.0
    exposure: float = 0.0
    time_in_market: float = 0.0
    t_stat: float = 0.0
    psr: float = 0.0
    alpha_ann: float = 0.0
    beta: float = 0.0
    alpha_t: float = 0.0
    alpha_sharpe: float = 0.0
    bench_sharpe: float = 0.0
    bench_cagr: float = 0.0
    fitness: float = 0.0
    ruined: bool = False
    stop_exits: int = 0
    halted_frac: float = 0.0

    def to_dict(self) -> dict:
        return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in asdict(self).items()}

    def line(self) -> str:
        return (f"SR {self.sharpe:6.2f} aSR {self.alpha_sharpe:6.2f} "
                f"CAGR {self.cagr:8.2%} DD {self.max_dd:7.2%} "
                f"trades {self.n_trades:5d} exp {self.exposure:4.2f} "
                f"cost {self.cost_drag_ann:6.2%}/y fit {self.fitness:6.2f}")


def alpha_sharpe(r: np.ndarray, m: np.ndarray, bpy: float) -> float:
    """Annualised Sharpe of the residual after regressing out the market.

    Shared by `evaluate` and by the durability gate, which needs the same number
    computed on half a return series. The residual-vol floor is the one from
    `evaluate`: without it a near-beta bot's alpha Sharpe explodes on rounding
    noise.
    """
    n = min(r.size, m.size)
    if n < 16:
        return 0.0
    r, m = r[:n], m[:n]
    _, beta, _ = stats.alpha_beta(r, m)
    resid = r - beta * m
    sd = max(float(resid.std(ddof=1)), 0.25 * float(r.std(ddof=1)), 1e-12)
    return float((r.mean() - beta * m.mean()) / sd * math.sqrt(bpy))


def _max_dd(equity: np.ndarray) -> float:
    if equity.size < 2:
        return 0.0
    peak = np.maximum.accumulate(np.maximum(equity, 1e-12))
    return float((equity / peak - 1.0).min())


def evaluate(res: BacktestResult) -> Perf:
    r = res.active_ret
    m = res.active_market_ret
    n = int(r.size)
    bpy = res.bars_per_year
    if n < 8:
        return Perf(n_bars=n, ruined=res.ruined)

    years = n / bpy
    eq = res.equity[res.start:]
    total = float(eq[-1] / max(eq[0], 1e-12) - 1.0)
    cagr = float((1.0 + total) ** (1.0 / max(years, 1e-9)) - 1.0) if total > -1.0 else -1.0
    vol = float(r.std(ddof=1) * math.sqrt(bpy))
    sr = stats.sharpe(r, bpy)

    downside = r[r < 0.0]
    dsd = float(downside.std(ddof=1)) if downside.size > 2 else 0.0
    sortino = float(r.mean() / dsd * math.sqrt(bpy)) if dsd > 1e-12 else 0.0
    mdd = _max_dd(eq)
    calmar = float(cagr / abs(mdd)) if mdd < -1e-9 else 0.0

    traded = r[res.pos[res.start:] != 0.0]
    hit = float((traded > 0).mean()) if traded.size else 0.0
    gains = float(r[r > 0].sum())
    losses = float(-r[r < 0].sum())
    pf = gains / losses if losses > 1e-12 else (gains / 1e-12 if gains > 0 else 0.0)
    q95, q05 = float(np.quantile(r, 0.95)), float(np.quantile(r, 0.05))
    tail = abs(q95 / q05) if abs(q05) > 1e-12 else 0.0

    alpha_bar, beta, alpha_t = stats.alpha_beta(r, m)
    resid = r - beta * m[: r.size]
    # Floor the residual vol at a quarter of the strategy's own vol. Without it,
    # a bot that is essentially buy-and-hold has a near-zero residual and its
    # alpha Sharpe explodes to +/- infinity on rounding noise — the first
    # version of this file scored levered buy-and-hold as skill for that reason.
    rsd = max(float(resid.std(ddof=1)), 0.25 * float(r.std(ddof=1)), 1e-12)
    alpha_sr = float(alpha_bar / rsd * math.sqrt(bpy))
    bench_sr = stats.sharpe(m, bpy)
    bench_cagr = float((np.prod(1.0 + m)) ** (1.0 / max(years, 1e-9)) - 1.0) if m.size else 0.0

    # Fitness: the conservative view. Take the weaker of raw and alpha Sharpe,
    # discount for a thin trade count (a 4-trade backtest is a rumour), and
    # charge hard for deep drawdowns and for blowing up.
    conf = min(1.0, math.sqrt(max(res.n_trades, 0) / 40.0)) if res.n_trades < 40 else 1.0
    base = min(sr, alpha_sr)
    fit = base * conf - 2.0 * max(0.0, -mdd - 0.40) - (5.0 if res.ruined else 0.0)

    return Perf(
        n_bars=n, years=years, total_return=total, cagr=cagr, vol_ann=vol,
        sharpe=sr, sortino=sortino, max_dd=mdd, calmar=calmar, hit_rate=hit,
        profit_factor=pf, worst_bar=float(r.min()), tail_ratio=tail,
        n_trades=res.n_trades, turnover_ann=res.n_trades / max(years, 1e-9),
        cost_drag_ann=(res.cost_paid + res.financing_paid) / max(years, 1e-9),
        exposure=res.exposure, time_in_market=res.time_in_market,
        t_stat=stats.t_stat(r), psr=stats.psr(r, bpy),
        alpha_ann=float(alpha_bar * bpy), beta=beta, alpha_t=alpha_t, alpha_sharpe=alpha_sr,
        bench_sharpe=bench_sr, bench_cagr=bench_cagr, fitness=fit,
        ruined=res.ruined, stop_exits=res.stop_exits, halted_frac=res.halted_frac,
    )


def pool(results: list[BacktestResult]) -> tuple[np.ndarray, np.ndarray, float]:
    """Concatenate active returns across runs for a single pooled estimate."""
    rs = [res.active_ret for res in results if res.active_ret.size > 8]
    ms = [res.active_market_ret[: res.active_ret.size] for res in results if res.active_ret.size > 8]
    if not rs:
        return np.zeros(0), np.zeros(0), 252.0
    bpy = float(np.mean([res.bars_per_year for res in results]))
    return np.concatenate(rs), np.concatenate(ms), bpy


def pooled_perf(results: list[BacktestResult]) -> Perf:
    """Perf of the pooled return stream. Used where many short runs must be
    judged together (walk-forward folds, replication instances)."""
    r, m, bpy = pool(results)
    if r.size < 8:
        return Perf()
    equity = np.concatenate(([1.0], np.cumprod(1.0 + r)))
    fake = BacktestResult(
        equity=equity, ret=np.concatenate(([0.0], r)), pos=np.ones(r.size + 1),
        market_ret=np.concatenate(([0.0], m)), bars_per_year=bpy, start=1,
        n_trades=sum(res.n_trades for res in results),
        cost_paid=sum(res.cost_paid for res in results),
        financing_paid=sum(res.financing_paid for res in results),
        exposure=float(np.mean([res.exposure for res in results])),
        time_in_market=float(np.mean([res.time_in_market for res in results])),
        halted_frac=float(np.mean([res.halted_frac for res in results])),
        stop_exits=sum(res.stop_exits for res in results),
        ruined=any(res.ruined for res in results),
        market=results[0].market,
    )
    return evaluate(fake)
