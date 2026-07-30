"""The bot factory: where each generation's candidates come from.

The mix matters more than any single ingredient:

  random       keeps the search from collapsing into one corner of the space
  mutants      exploits whatever the hall of fame already knows
  crossover    recombines two partial answers
  transplants  takes a rule that works on one market and tries it on another —
               the cheapest source of genuine generalisation
  archetypes   seeds human priors, and re-seeds when expansion unlocks a family

Every generation allocates candidates across *all* unlocked market families
rather than chasing whichever family looked best last round. Without that, the
search piles onto the easiest market within two generations and the answer to
"try all different types of markets" quietly becomes "try one".
"""

from __future__ import annotations

import numpy as np

from . import genome as gm
from .genome import Genome, SearchSpace
from .state import RunState

MIX = {"random": 0.22, "mutant": 0.40, "crossover": 0.20, "transplant": 0.08, "archetype": 0.10}


def propose(state: RunState, space: SearchSpace, rng: np.random.Generator,
            seeded_markets: set[str] | None = None) -> list[Genome]:
    """One generation's candidate list, deduplicated against everything the run
    has already screened."""
    n = int(space.population)
    hall = state.hall_genomes()
    fits = np.asarray([e["fitness"] for e in state.hall], dtype=float) if state.hall else np.zeros(0)
    markets = list(space.markets)
    seeded = seeded_markets if seeded_markets is not None else set()

    out: list[Genome] = []
    seen: set[str] = set()

    def add(g: Genome) -> None:
        if g.bot_id in seen or not state.is_new(g.bot_id):
            return
        seen.add(g.bot_id)
        out.append(g)

    # Archetypes for any family not yet seeded (generation 0, or newly unlocked).
    for mkt in markets:
        if mkt in seeded:
            continue
        for g in gm.archetypes(mkt):
            g.generation = state.generation
            add(g)

    if hall:
        w = np.clip(fits - fits.min() + 0.05, 1e-6, None)
        w = w / w.sum()
    else:
        w = None

    # Round-robin over markets so coverage does not collapse onto one family.
    guard = 0
    while len(out) < n and guard < n * 40:
        guard += 1
        mkt = markets[len(out) % len(markets)] if markets else None
        kind = _pick_kind(rng, bool(hall))
        if kind == "random":
            add(gm.random_genome(space, rng, market=mkt, generation=state.generation))
        elif kind == "mutant" and hall:
            parent = hall[int(rng.choice(len(hall), p=w))]
            add(gm.mutate(parent, space, rng, generation=state.generation))
        elif kind == "crossover" and len(hall) >= 2:
            i, j = rng.choice(len(hall), size=2, replace=False, p=w)
            add(gm.crossover(hall[int(i)], hall[int(j)], space, rng, generation=state.generation))
        elif kind == "transplant" and hall:
            parent = hall[int(rng.choice(len(hall), p=w))]
            child = gm.mutate(parent, space, rng, generation=state.generation, n_ops=1)
            child.market = mkt or child.market
            child.origin = "transplant"
            gm._repair(child, space)
            add(child)
        else:
            add(gm.random_genome(space, rng, market=mkt, generation=state.generation))

    return out[:n]


def _pick_kind(rng: np.random.Generator, have_hall: bool) -> str:
    if not have_hall:
        return "random"
    keys = [k for k in MIX if k != "archetype"]
    p = np.asarray([MIX[k] for k in keys], dtype=float)
    p = p / p.sum()
    return str(rng.choice(keys, p=p))


SIMPLE_GENES = 2                # "simple" = at most 2 genes and 1 filter
SIMPLE_RESERVE = 0.5            # half the gauntlet slots are reserved for them


def _is_simple(g: Genome) -> bool:
    return len(g.genes) <= SIMPLE_GENES and len(g.filters) <= 1


def finalists(scored: list[tuple[Genome, object]], k: int, per_market: int = 3) -> list[Genome]:
    """Pick who gets the expensive gauntlet.

    Two caps, both there because unconstrained ranking picks badly:

    * **per market** — one family that happens to score well would otherwise take
      every slot, and the run would prove one thing about one market instead of
      testing the catalogue.
    * **a reserve for simple bots** — complex genomes win the screen almost every
      time (more parameters, more room to fit the training instances) and then
      die at G1. Half the slots go to candidates with at most two genes, which is
      where every bot that has actually passed the gauntlet has come from.

    Archetypes do not compete here at all — `loop.py` tests every one of them
    exactly once, in a separate priors pass, for the reasons given there.
    """
    ranked = sorted(scored, key=lambda t: -getattr(t[1], "fitness", 0.0))
    n_simple = int(k * SIMPLE_RESERVE)
    chosen: list[Genome] = []
    counts: dict[str, int] = {}
    sigs: set[str] = set()

    def take(pool, limit: int) -> None:
        for g, perf in pool:
            if len(chosen) >= limit:
                return
            if getattr(perf, "fitness", 0.0) <= 0.0:
                continue
            if g.bot_id in {c.bot_id for c in chosen}:
                continue
            if counts.get(g.market, 0) >= per_market:
                continue
            if g.signature() in sigs:       # no two finalists of the same structure
                continue
            sigs.add(g.signature())
            counts[g.market] = counts.get(g.market, 0) + 1
            chosen.append(g)

    take([t for t in ranked if _is_simple(t[0])], n_simple)
    take(ranked, k)
    return chosen
