"""The loop: keep producing bots, keep testing them, widen the search when it
stalls, stop when the target number of proven bots is reached.

Per generation:

  1. propose   — factory builds candidates across every unlocked market family
  2. screen    — train window only, search pool only, 24 instances
  3. finalists — top scorers, capped per market
  4. gauntlet  — the seven gates; every candidate screened counts in the ledger
  5. expand    — on stagnation, unlock a wider search space and re-seed

The expansion policy is the answer to "expand until the goal is reached". It is
deliberately not "search harder": raising the population alone would just buy
more lottery tickets, and G6 makes lottery tickets *more* expensive by raising
the luck bar with every trial. So expansion adds new *kinds* of bot — more
signal primitives, more genes per bot, more market families — which is the only
way to move the frontier rather than resample it.

There is no guarantee of success, by design. If the loop hits its generation
budget with nothing proven, that is a finding about the markets in the
catalogue, and `report.py` writes it up as one instead of lowering the bar.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict

import numpy as np

from . import factory, gauntlet, metrics, report
from .genome import Genome, SearchSpace
from .state import HallEntry, RunState

DEFAULT_STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "state", "run_state.json")


def _screen_batch(genomes: list[Genome], cfg: gauntlet.GauntletConfig,
                  n_instances: int, jobs: int) -> list[metrics.Perf]:
    if jobs <= 1:
        return [gauntlet.screen(g, cfg, n_instances) for g in genomes]
    from concurrent.futures import ProcessPoolExecutor
    payload = [(g.to_dict(), asdict(cfg), n_instances) for g in genomes]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(_screen_one, payload, chunksize=8))


def _screen_one(args) -> metrics.Perf:
    """Worker entry point. Must stay module-level and picklable."""
    gd, cfgd, n_inst = args
    g = Genome.from_dict(gd)
    cfg = gauntlet.GauntletConfig(**cfgd)
    return gauntlet.screen(g, cfg, n_inst)


def run_loop(target_proven: int = 3, max_generations: int = 40,
             state_path: str = DEFAULT_STATE, cfg: gauntlet.GauntletConfig | None = None,
             space: SearchSpace | None = None, seed: int = 20260730,
             patience: int = 3, jobs: int = 1, screen_instances: int = gauntlet.SCREEN_INSTANCES,
             time_budget_s: float | None = None, verbose: bool = True,
             report_path: str | None = None, log_path: str | None = None) -> RunState:
    cfg = cfg or gauntlet.GauntletConfig()
    space = space or SearchSpace()
    st = RunState.load_or_new(state_path, space, seed=seed)
    space = SearchSpace(**st.space) if st.space else space
    rng = np.random.default_rng(st.seed + st.generation * 7919)
    t0 = time.time()

    seeded_markets: set[str] = set()
    for e in st.hall:
        seeded_markets.add(e["genome"]["market"])
    since_last_find = 0

    def say(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    say(f"loop start: {st.n_distinct_proven()}/{target_proven} distinct proven, generation {st.generation}, "
        f"{st.trials} trials on the ledger, space {space.describe()}")

    while st.n_distinct_proven() < target_proven and st.generation < max_generations:
        if time_budget_s is not None and time.time() - t0 > time_budget_s:
            say(f"time budget {time_budget_s:.0f}s reached at generation {st.generation}")
            break

        st.generation += 1
        gen = st.generation
        rng = np.random.default_rng(st.seed + gen * 7919)

        candidates = factory.propose(st, space, rng, seeded_markets=seeded_markets)
        seeded_markets |= set(space.markets)
        if not candidates:
            say(f"G{gen}: search space exhausted at level {space.level}; expanding")
            space = space.expanded()
            st.space = asdict(space)
            st.expansions.append({"generation": gen, "level": space.level,
                                  "reason": "no novel candidates"})
            seeded_markets = set()
            continue

        t_screen = time.time()
        perfs = _screen_batch(candidates, cfg, screen_instances, jobs)
        for g, p in zip(candidates, perfs):
            st.record_trial(g.bot_id, p.alpha_sharpe)
        screen_s = time.time() - t_screen

        scored = list(zip(candidates, perfs))
        st.update_hall([HallEntry(genome=g.to_dict(), fitness=p.fitness,
                                  alpha_sharpe=p.alpha_sharpe, sharpe=p.sharpe,
                                  n_trades=p.n_trades, generation=gen)
                        for g, p in scored if p.fitness > 0])

        # PRIORS PASS. The archetypes are a fixed set of ~12 textbook rules per
        # market, written down before any data was seen and never tuned. Every one
        # of them gets a full gauntlet exactly once, rather than competing for
        # finalist slots against fitted mutants that beat them on the screen and
        # then die at G1. Two reasons this is not favouritism:
        #
        #   * They are priors, not search output. A human evaluating a new market
        #     tests the classics first, and 130 fixed hypotheses is a different
        #     kind of exposure from thousands of fitted ones.
        #   * They are the ones that survive. The single bot known to clear all
        #     seven gates is an *untuned* RSI-reversion archetype; with a reserve
        #     of 3 slots it was still outbid by other markets' archetypes and
        #     never tested.
        #
        # It is also what makes "try all different types of markets with different
        # strategies" literally true: every family x every classic, once.
        # Every verdict records `origin`, so a reader can always tell a seeded
        # prior from a search discovery.
        priors = [g for g, p in scored if g.origin == "archetype" and p.fitness > 0.0]
        searched = factory.finalists(scored, space.finalists, per_market=3)
        prior_ids = {g.bot_id for g in priors}
        picks = priors + [g for g in searched if g.bot_id not in prior_ids]
        best_screen = max((p.fitness for p in perfs), default=0.0)

        found_this_gen = []
        for g in picks:
            v = gauntlet.run_gauntlet(g, cfg, n_trials=max(st.trials, 1),
                                      var_trial_sharpe=st.var_trial_sharpe(),
                                      rng=rng, cross_market=True,
                                      n_confirm_tests=st.gauntlet_runs + 1)
            st.gauntlet_runs += 1
            st.backtests += v.n_backtests
            if v.passed:
                if st.add_proven(g, v.to_dict()):
                    found_this_gen.append(v)
                    say(f"  PROVEN  {v.bot_id}  {g.market}\n    {g.describe()}")
            else:
                st.note_failure(v.failed_at)

        since_last_find = 0 if found_this_gen else since_last_find + 1
        rec = {
            "generation": gen, "level": space.level, "tier": space.tier,
            "candidates": len(candidates), "trials_total": st.trials,
            "gauntlets": len(picks), "priors_tested": len(priors),
            "proven_new": len(found_this_gen),
            "proven_total": len(st.proven), "proven_distinct": st.n_distinct_proven(),
            "best_screen_fitness": round(best_screen, 3),
            "screen_seconds": round(screen_s, 1),
            "markets": sorted({g.market for g in candidates}),
        }
        st.log.append(rec)
        say(f"G{gen} L{space.level}: {len(candidates)} candidates "
            f"({screen_s:.1f}s screen), {len(picks)} gauntlets"
            + (f" ({len(priors)} priors)" if priors else "") + ", "
            f"best screen fit {best_screen:+.2f}, "
            f"proven {st.n_distinct_proven()}/{target_proven} distinct"
            + (f" ({len(st.proven)} genomes)" if len(st.proven) > st.n_distinct_proven() else "")
            + (f", stagnant {since_last_find}" if since_last_find else ""))

        if log_path:
            report.append_loop_log(log_path, rec, found_this_gen, space, st)
        st.save()

        if st.n_distinct_proven() >= target_proven:
            break

        if since_last_find >= patience:
            old = space.describe()
            space = space.expanded()
            st.space = asdict(space)
            st.expansions.append({"generation": gen, "level": space.level,
                                  "from": old, "to": space.describe(),
                                  "reason": f"{since_last_find} generations without a pass"})
            seeded_markets = set()          # re-seed archetypes on newly unlocked families
            since_last_find = 0
            say(f"  EXPAND -> {space.describe()}")

    st.save()
    say(f"loop end: {st.n_distinct_proven()} distinct strategies proven "
        f"({len(st.proven)} genomes), {st.trials} trials, "
        f"{st.gauntlet_runs} gauntlets, {st.backtests} backtests, "
        f"{st.elapsed():.0f}s elapsed")

    if report_path:
        report.write_report(report_path, st, cfg)
        say(f"report written to {report_path}")
    return st


def rejection_funnel(st: RunState) -> list[tuple[str, int]]:
    order = ["G0-market", "G1-oos", "G2-replication", "G3-controls", "G4-stress",
             "G5-permutation", "G6-multiplicity", "G7-stress-pool", "unknown"]
    return [(k, st.fail_counts.get(k, 0)) for k in order if st.fail_counts.get(k, 0)]
