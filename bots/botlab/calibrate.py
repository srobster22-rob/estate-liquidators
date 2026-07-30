"""Is each market family's planted edge realistic *and* findable?

Two failure modes bracket this whole project:

  * plant too little structure and nothing can ever pass the gauntlet, so the
    loop runs forever and the honest report is "no bot found";
  * plant too much and the loop finds Sharpe-3 bots in an afternoon, which
    tells you nothing about markets and everything about the generator.

So each family is calibrated against a fixed panel of textbook strategies. The
target band: the best archetype should reach roughly **0.4-1.0 gross annual
Sharpe** — the range published single-asset anomaly research actually supports —
and costs should visibly bite. `ceiling` is the perfect-foresight bound; if a
measured number ever approaches it, the engine is cheating.
"""

from __future__ import annotations

import numpy as np

from . import engine, genome, metrics
from .markets import generate, universe


def archetype_panel(market: str, n_instances: int = 6, cost_mult: float = 1.0,
                    pool: range | None = None) -> list[dict]:
    """Every archetype on `n_instances` instances of one family."""
    spec = universe.get(market)
    idxs = list((pool or universe.SEARCH_POOL))[:n_instances]
    series = [generate.synth(spec, i) for i in idxs]
    rows = []
    for g in genome.archetypes(market):
        srs, fits, alphas, trades, costs = [], [], [], [], []
        for s in series:
            p = metrics.evaluate(engine.run(s, g, cost_mult=cost_mult))
            srs.append(p.sharpe)
            alphas.append(p.alpha_sharpe)
            fits.append(p.fitness)
            trades.append(p.n_trades)
            costs.append(p.cost_drag_ann)
        rows.append({
            "bot": g.describe(),
            "bot_id": g.bot_id,
            "sharpe_med": float(np.median(srs)),
            "alpha_sharpe_med": float(np.median(alphas)),
            "fitness_med": float(np.median(fits)),
            "pos_frac": float(np.mean(np.asarray(srs) > 0)),
            "trades_med": float(np.median(trades)),
            "cost_ann_med": float(np.median(costs)),
        })
    return rows


def calibrate_family(market: str, n_instances: int = 6) -> dict:
    spec = universe.get(market)
    gross = {r["bot_id"]: r for r in archetype_panel(market, n_instances, cost_mult=0.0)}
    net = archetype_panel(market, n_instances, cost_mult=1.0)
    # Cost bite has to be measured *per bot*, gross vs net. Comparing the
    # best-gross bot against the best-net bot instead reported beta exposure as
    # a cost effect (it made rates_daily look like it was being eaten by
    # financing when the gross number was simply a carry trade).
    for r in net:
        r["gross_alpha_sr"] = gross.get(r["bot_id"], {}).get("alpha_sharpe_med", 0.0)
        r["bite"] = r["gross_alpha_sr"] - r["alpha_sharpe_med"]
    best_net = max(net, key=lambda r: r["alpha_sharpe_med"])
    best_gross = max(gross.values(), key=lambda r: r["alpha_sharpe_med"])
    row = generate.calibration_row(spec, n_instances=min(n_instances, 6))
    return {
        "market": market,
        "vol_measured": row["vol_ann"],
        "vol_target": spec.vol_ann,
        "autocorr1": row["autocorr1"],
        "max_dd_bh": row["max_dd"],
        "ceiling_sr": spec.oracle_sharpe_ceiling(),
        "best_gross_sr": best_gross["alpha_sharpe_med"],
        "best_gross_bot": best_gross["bot"],
        "best_net_alpha_sr": best_net["alpha_sharpe_med"],
        "best_net_bot": best_net["bot"],
        "cost_bite": best_net["bite"],
        "n_archetypes_net_positive": int(sum(1 for r in net if r["alpha_sharpe_med"] > 0)),
        "n_archetypes": len(net),
    }


def calibrate_all(n_instances: int = 6, include_controls: bool = True) -> list[dict]:
    out = []
    for spec in universe.all_markets(include_controls=include_controls):
        out.append(calibrate_family(spec.name, n_instances))
    return out


def control_search_fpr(n_candidates: int = 2000, n_finalists: int = 30,
                       seed: int = 424242, cfg=None, verbose: bool = True) -> dict:
    """End-to-end false-positive rate: run the *whole search* against a market
    with no exploitable structure, and count how many bots the ladder certifies.

    This is the single most important number in the lab, and the only honest way
    to justify a threshold choice. Every gate can be argued about in the abstract;
    this measures what the gates actually do when a determined search is pointed
    at a pure random walk with realistic costs. The correct answer is zero.

    A tradeable clone of `control_martingale_daily` is registered so G0 cannot
    reject the candidates on a technicality and the rest of the ladder has to earn
    the rejection. G3 still runs against the real control families, but those are
    independent instance draws, so it does not shortcut the test.
    """
    from dataclasses import replace as _replace

    from . import factory, gauntlet
    from .genome import SearchSpace, random_genome

    cfg = cfg or gauntlet.GauntletConfig()
    probe = _replace(universe.get("control_martingale_daily"),
                     name="fpr_probe_martingale", control=False, tier=1,
                     notes="tradeable clone of the martingale control, for FPR calibration only")
    universe.register(probe)
    try:
        space = SearchSpace(level=3, tier=3, max_genes=3, max_filters=2,
                            markets=("fpr_probe_martingale",))
        rng = np.random.default_rng(seed)
        pop = [random_genome(space, rng, market="fpr_probe_martingale")
               for _ in range(n_candidates)]
        perfs = [gauntlet.screen(g, cfg, 8) for g in pop]
        picks = factory.finalists(list(zip(pop, perfs)), n_finalists,
                                  per_market=n_finalists)
        if verbose:
            best = max((p.fitness for p in perfs), default=0.0)
            print(f"  screened {len(pop)} bots on a structureless market; "
                  f"best screen fitness {best:+.2f}; {len(picks)} finalists", flush=True)
        reached: dict[str, int] = {}
        passed = []
        for g in picks:
            v = gauntlet.run_gauntlet(g, cfg, n_trials=n_candidates,
                                      var_trial_sharpe=0.09, rng=rng,
                                      cross_market=False, n_confirm_tests=len(picks))
            key = v.failed_at or "PASSED"
            reached[key] = reached.get(key, 0) + 1
            if v.passed:
                passed.append(v)
            if verbose:
                print(f"    {v.bot_id} {key}", flush=True)
        return {
            "n_candidates": n_candidates,
            "n_finalists": len(picks),
            "n_passed": len(passed),
            "fpr": len(passed) / max(len(picks), 1),
            "stopped_at": reached,
            "passed_ids": [v.bot_id for v in passed],
            "best_screen_fitness": float(max((p.fitness for p in perfs), default=0.0)),
        }
    finally:
        universe.unregister("fpr_probe_martingale")


def refresh_vol_fix(n_probe: int = 24) -> list[tuple[str, float]]:
    """Recompute the locked `vol_fix` constants. Prints values to paste into
    `universe.py`; deliberately does not rewrite the file, so the constants stay
    reviewable in a diff."""
    return [(spec.name, generate.measure_vol_fix(spec, n_probe=n_probe))
            for spec in universe.all_markets()]


def format_table(rows: list[dict]) -> str:
    head = (f"{'market':<26}{'vol':>7}{'ac1':>7}{'ceil':>7}"
            f"{'gross':>7}{'net_a':>7}{'bite':>7}{'net+':>6}")
    lines = [head, "-" * len(head)]
    for r in rows:
        lines.append(
            f"{r['market']:<26}{r['vol_measured']:>6.1%}{r['autocorr1']:>7.3f}"
            f"{r['ceiling_sr']:>7.2f}{r['best_gross_sr']:>7.2f}"
            f"{r['best_net_alpha_sr']:>7.2f}{r['cost_bite']:>7.2f}"
            f"{r['n_archetypes_net_positive']:>3d}/{r['n_archetypes']:<3d}")
    return "\n".join(lines)
