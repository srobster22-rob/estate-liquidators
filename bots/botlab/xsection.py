"""Does a cross-sectional strategy have room where a single-instrument one does not?

F29/F30 established that every strategy this lab certifies clears its narrowest
gate by under 0.07 alpha Sharpe, and that no widening of the search — more genes,
more filters, more primitives, more effort — changes that. Under a gauntlet 20%
harder, four distinct strategies become one. The open question was whether any
*structurally different* source of return would behave differently.

This measures the one candidate. The claim being tested is arithmetic, not
hopeful: a dollar-neutral basket trade cancels the common factor (so its raw
Sharpe is its alpha Sharpe, with no beta to residualise) and aggregates K roughly
independent idiosyncratic bets (so per-bet edge holds while portfolio volatility
falls by about sqrt(K)). The *same planted per-instrument edge* should therefore
support a materially larger Sharpe.

NO NEW BACKTESTER. `run_basket` is portfolio aggregation over K calls to the
existing `engine.run`, not a cross-sectional engine. Each leg is an ordinary
`Series` and the cross-sectional score is an ordinary signal primitive, so every
audited property — no lookahead, costs only ever hurt, stops can only exit,
Brownian-bridge fills — is inherited rather than reimplemented. The only thing
this file adds is the sum.

AND THE CONTROL COMES FIRST. A dollar-neutral basket has low volatility by
construction, so a small artefact divides into a large Sharpe. Every measurement
here is reported against `basket_control` — the identical factor structure with
the cross-sectional effect switched off — and a result on the live basket means
nothing without a zero on the control. That is the F6 lesson applied to a new
strategy class before the class is allowed to claim anything.
"""

from __future__ import annotations

import numpy as np

from . import engine, metrics
from .genome import Gene, Genome
from .markets import basket


def _raw_sharpe(r: np.ndarray, bpy: float) -> float:
    sd = float(r.std(ddof=1)) if r.size > 2 else 0.0
    return float(r.mean() / sd * np.sqrt(bpy)) if sd > 1e-12 else 0.0


def run_basket(legs: list, g: Genome, cost_mult: float = 1.0,
               exec_delay: int = 1) -> dict:
    """Equal-weight portfolio of the same genome applied to every leg.

    Returns the basket's own return stream plus the diagnostics that decide
    whether the result means anything: net exposure (a cross-sectional score
    should sum to roughly zero, and if it does not the "market-neutral" claim is
    false), and the per-leg Sharpe the aggregate is built from.
    """
    results = [engine.run(s, g, cost_mult=cost_mult, exec_delay=exec_delay)
               for s in legs]
    start = max(r.start for r in results)
    n = min(r.ret.size for r in results)
    if start >= n - 8:
        return {"ok": False, "reason": "no usable bars after warmup"}

    R = np.column_stack([r.ret[:n] for r in results])
    P = np.column_stack([r.pos[:n] for r in results])
    M = np.column_stack([r.market_ret[:n] for r in results])
    port = R[start:].mean(axis=1)
    mkt = M[start:].mean(axis=1)          # the equal-weight basket = the factor
    net = P[start:].mean(axis=1)          # net exposure per bar, averaged over legs
    gross = np.abs(P[start:]).mean(axis=1)
    bpy = float(results[0].bars_per_year)

    per_leg = [metrics.evaluate(r) for r in results]
    return {
        "ok": True,
        "ret": port,
        "sharpe": _raw_sharpe(port, bpy),
        "alpha_sharpe": metrics.alpha_sharpe(port, mkt, bpy),
        "net_exposure": float(np.mean(net)),
        "net_exposure_abs": float(np.mean(np.abs(net))),
        "gross_exposure": float(np.mean(gross)),
        "leg_sharpe_med": float(np.median([p.sharpe for p in per_leg])),
        "leg_alpha_med": float(np.median([p.alpha_sharpe for p in per_leg])),
        "n_trades": int(sum(p.n_trades for p in per_leg)),
        "cost_drag_ann": float(np.mean([p.cost_drag_ann for p in per_leg])),
        "n_legs": len(legs),
    }


def xs_genome(market: str, lb: int = 5, entry: float = 0.25, exit_: float = 0.05) -> Genome:
    """The textbook cross-sectional reversal rule, untuned.

    `proportional` sizing because the score is already a standardised
    cross-sectional z — position size should track how far a leg has diverged
    from its peers, which is what makes the book dollar-neutral rather than
    merely long-short.
    """
    return Genome(market=market, genes=[Gene("xs_reversal", {"lb": lb})],
                  entry_threshold=entry, exit_threshold=exit_,
                  direction="both", sizing="proportional", max_leverage=2.0,
                  rebalance_band=0.15, origin="archetype")


def measure(bspec, n_instances: int = 8, lookbacks=(3, 5, 10, 20),
            verbose: bool = True) -> dict:
    """The experiment: live basket vs its control, across a few lookbacks.

    Reports the *margin* against the replication bar, since that is the statistic
    F30 showed to be the one that predicts anything.
    """
    from . import gauntlet
    bar = gauntlet.GauntletConfig().min_repl_alpha_sr
    ctrl = basket.basket_control(bspec)
    out = {"basket": bspec.name, "rows": []}
    for lb in lookbacks:
        for spec, tag in ((bspec, "live"), (ctrl, "control")):
            srs, nets, legs_a = [], [], []
            for i in range(1, n_instances + 1):
                legs = basket.synth_basket(spec, i)
                g = xs_genome(legs[0].spec.name, lb=lb)
                r = run_basket(legs, g)
                if not r["ok"]:
                    continue
                srs.append(r["alpha_sharpe"])
                nets.append(r["net_exposure_abs"])
                legs_a.append(r["leg_alpha_med"])
            if not srs:
                continue
            med = float(np.median(srs))
            row = {"lookback": lb, "arm": tag, "alpha_sharpe_med": round(med, 4),
                   "margin": round(med - bar, 4),
                   "leg_alpha_med": round(float(np.median(legs_a)), 4),
                   "net_exposure_abs": round(float(np.median(nets)), 4),
                   "n_instances": len(srs)}
            out["rows"].append(row)
            if verbose:
                print(f"  lb={lb:<3} {tag:<8} basket alphaSR {med:+.3f} "
                      f"(margin {row['margin']:+.3f} vs the {bar:+.2f} bar), "
                      f"per-leg {row['leg_alpha_med']:+.3f}, "
                      f"|net| {row['net_exposure_abs']:.3f}", flush=True)
    return out


def format_measure(res: dict) -> str:
    head = (f"{'lookback':>9}{'arm':>10}{'basketSR':>11}{'margin':>9}"
            f"{'per-leg SR':>12}{'|net expo|':>12}")
    lines = [head, "-" * len(head)]
    for r in res["rows"]:
        lines.append(f"{r['lookback']:>9}{r['arm']:>10}{r['alpha_sharpe_med']:>11.3f}"
                     f"{r['margin']:>9.3f}{r['leg_alpha_med']:>12.3f}"
                     f"{r['net_exposure_abs']:>12.3f}")
    return "\n".join(lines)
