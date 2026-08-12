"""
Ghosts (GAME-CONCEPTS.md #44) — the kill test, run.

THE BET
    Asynchronous PvP where the danger *is* the population. Nobody is online with you and
    everybody is against you.

THE STATED KILL CONDITION
    "The ghost pool converges. If everyone's run collapses onto one optimal path within a
    week, the level is static again — and you've built a hand-authored level the expensive
    way, via infrastructure."

THE STRUCTURE NOBODY MENTIONS
    This is a congestion game. Ghosts make a popular route dangerous, which pushes the next
    player off it, which empties it, which makes it safe again. That feedback might sustain
    diversity forever — or it might not, if the intrinsically fast route is worth the risk.
    The whole concept lives or dies on which.

WHAT DECIDES IT
    G1  Does path diversity survive with NEAR-DETERMINISTIC players? This is the load-
        bearing test. If diversity only exists because I injected randomness into player
        choice, the measurement is a tautology and proves nothing. Diversity has to come
        from the hazard feedback itself.

    G2  Does the hazard field keep MOVING, or settle to a fixed point? A limit cycle is
        alive — the level genuinely differs week to week. A fixed point is a static level
        with a server bill.

    G3  Where is the boundary? Sweep the pull of the fast route against the cost of a
        collision. A concept that only works at one magic ratio is a worse bet than one
        with a broad basin.

No dependencies, deterministic, runs in about three seconds.
"""

import math
import random
from collections import Counter

LANES = 12
STEPS = 20
POOL = 60          # ghosts in the pool — a rolling window of recent runs
PER_GEN = 10       # new runs per generation
GENS = 260         # ~26 "days" at 10 runs each
BURN_IN = 60       # generations discarded before measuring


def intrinsic_reward(lane, step, pull):
    """
    The level's own shape. Centre lanes are the fast line — `pull` is how much faster.
    With pull=0 the level is flat and any path is as good as any other, which would make
    diversity meaningless. With pull large, the fast line is worth any amount of risk.
    """
    centre = (LANES - 1) / 2.0
    return -pull * abs(lane - centre) / centre


def best_path(density, pull, hazard, temperature, rng):
    """
    A player's run. Dynamic programme over (lane, step) with a one-lane movement limit,
    maximising reward minus hazard. `temperature` adds imperfection: 0 is a perfect
    optimiser, which is the case that actually tests the bet.
    """
    # value[t][l] = best achievable total from (l, t) onward
    value = [[0.0] * LANES for _ in range(STEPS)]
    choice = [[0] * LANES for _ in range(STEPS)]
    for l in range(LANES):
        value[STEPS - 1][l] = intrinsic_reward(l, STEPS - 1, pull) - hazard * density[STEPS - 1][l]
    for t in range(STEPS - 2, -1, -1):
        for l in range(LANES):
            here = intrinsic_reward(l, t, pull) - hazard * density[t][l]
            best_nxt, best_val = l, -1e18
            for dl in (-1, 0, 1):
                nl = l + dl
                if 0 <= nl < LANES and value[t + 1][nl] > best_val:
                    best_val, best_nxt = value[t + 1][nl], nl
            value[t][l] = here + best_val
            choice[t][l] = best_nxt

    # Pick a start lane. At temperature 0 this is argmax; above it, softmax.
    if temperature <= 1e-9:
        start = max(range(LANES), key=lambda l: value[0][l])
    else:
        mx = max(value[0])
        w = [math.exp((value[0][l] - mx) / temperature) for l in range(LANES)]
        tot = sum(w)
        r, acc, start = rng.random() * tot, 0.0, LANES - 1
        for l in range(LANES):
            acc += w[l]
            if r <= acc:
                start = l
                break

    path, l = [], start
    for t in range(STEPS):
        path.append(l)
        l = choice[t][l]
    return path


def run_heterogeneous(pull=1.0, hazard=3.0, spread=0.6, gens=GENS, seed=11):
    """
    The same level, but players are not identical. Each draws their own risk tolerance
    (how much a collision costs them) and their own skill (how hard they chase the fast
    line). Still perfect optimisers — no injected path noise — they simply want different
    things, which is the one thing that is unambiguously true of real players.

    This exists because the homogeneous version collapses: ten identical optimisers compute
    one identical DP and contribute ONE path per generation, so a 60-ghost pool holds five
    or six distinct paths and settles into a short limit cycle. That result says nothing
    about a real population; it says the model had one player in it.
    """
    rng = random.Random(seed)
    pool = [[i % LANES] * STEPS for i in range(POOL)]
    ent_series, distinct_series, states = [], [], []
    for _ in range(gens):
        density = [[0.0] * LANES for _ in range(STEPS)]
        for p in pool:
            for t, l in enumerate(p):
                density[t][l] += 1.0 / len(pool)
        new = []
        for _ in range(PER_GEN):
            h = hazard * (1.0 + spread * (rng.random() * 2 - 1))
            pl = pull * (1.0 + spread * (rng.random() * 2 - 1))
            new.append(best_path(density, pl, h, 0.0, rng))
        pool.extend(new)
        pool = pool[-POOL:]

        ent = 0.0
        for t in range(STEPS):
            counts = Counter(p[t] for p in pool)
            n = len(pool)
            ent += -sum((c / n) * math.log(c / n) for c in counts.values() if c) / math.log(LANES)
        ent_series.append(ent / STEPS)
        distinct_series.append(len({tuple(p) for p in pool}))
        states.append(tuple(tuple(r) for r in density))
    return ent_series, distinct_series, states


def cycle_period(states, tail_from=120, max_p=40):
    """Smallest p for which the hazard field repeats exactly over the whole tail."""
    tail = states[tail_from:]
    if len(tail) < 2 * max_p:
        return None
    for p in range(1, max_p + 1):
        if all(tail[i] == tail[i + p] for i in range(len(tail) - p)):
            return p
    return None


def run(pull=1.0, hazard=3.0, temperature=0.0, gens=GENS, seed=7):
    """
    Play `gens` generations. Each generation, PER_GEN players best-respond to the current
    ghost pool, then join it; the oldest runs fall out of the window.

    Returns (entropy_series, turnover_series, lane_usage_by_gen).
    """
    rng = random.Random(seed)
    pool = []
    # Seed the pool with spread-out runs so generation 1 isn't responding to an empty level.
    for i in range(POOL):
        lane = i % LANES
        pool.append([lane] * STEPS)

    ent_series, turn_series, usage_series = [], [], []
    prev_density = None
    for _ in range(gens):
        density = [[0.0] * LANES for _ in range(STEPS)]
        for p in pool:
            for t, l in enumerate(p):
                density[t][l] += 1.0 / len(pool)

        new = [best_path(density, pull, hazard, temperature, rng) for _ in range(PER_GEN)]
        pool.extend(new)
        pool = pool[-POOL:]

        # Diversity: mean normalised entropy of lane occupancy across the level.
        ent = 0.0
        for t in range(STEPS):
            counts = Counter(p[t] for p in pool)
            n = len(pool)
            h = -sum((c / n) * math.log(c / n) for c in counts.values() if c)
            ent += h / math.log(LANES)
        ent_series.append(ent / STEPS)

        # Turnover: how much the hazard field moved since last generation.
        if prev_density is not None:
            diff = sum(abs(density[t][l] - prev_density[t][l])
                       for t in range(STEPS) for l in range(LANES))
            turn_series.append(diff / STEPS)
        prev_density = density
        usage_series.append(Counter(p[t] for p in pool for t in range(STEPS)))

    return ent_series, turn_series, usage_series


def summarise(series, burn=BURN_IN):
    tail = series[burn:]
    return sum(tail) / len(tail), min(tail), max(tail)


def bar(v, width=34):
    return "#" * max(0, int(round(v * width)))


if __name__ == "__main__":
    print("=" * 78)
    print("GHOSTS (#44) — kill test")
    print(f"  {LANES} lanes x {STEPS} steps · pool of {POOL} ghosts · {GENS} generations")
    print("=" * 78)

    print("\nG1  Does diversity survive PERFECT optimisers?")
    print("    Players at temperature 0 — no injected randomness at all. If diversity")
    print("    holds here, the hazard feedback is doing the work. If it only holds when")
    print("    players are sloppy, the measurement was a tautology.\n")
    ent, turn, usage = run(temperature=0.0)
    mean_e, min_e, max_e = summarise(ent)
    print(f"      generation   1: entropy {ent[0]:.3f}  {bar(ent[0])}")
    for g in (10, 40, 100, 180, GENS - 1):
        print(f"      generation {g:3d}: entropy {ent[g]:.3f}  {bar(ent[g])}")
    print(f"\n      settled mean entropy (after burn-in): {mean_e:.3f}")
    print(f"      range: {min_e:.3f} .. {max_e:.3f}")
    print(f"      lanes in use at the end: {len(usage[-1])}/{LANES}")

    print("\n" + "-" * 78)
    print("\nG2  How many DISTINCT states does the level actually have?")
    print("    v1 asked only whether the hazard field moved, and passed on turnover > 0.")
    print("    That was the wrong question: a field can move forever around a tiny loop.")
    print("    A player who has seen every state has seen the whole game.\n")
    mean_t, _, _ = summarise(turn)
    _, distinct_hom, states_hom = run_heterogeneous(spread=0.0, gens=200, seed=7)
    period_hom = cycle_period(states_hom)
    print(f"      mean turnover per generation: {mean_t:.4f}  (non-zero — v1 passed on this)")
    print(f"      distinct paths in a {POOL}-ghost pool: {distinct_hom[-1]}")
    print(f"      limit-cycle period: {period_hom} generations")
    print(f"\n      => the level is a {period_hom}-state automaton. Play it {period_hom + 1}")
    print("         times and you have seen everything it can do.")

    print("\n" + "-" * 78)
    print("\nG2b IDENTICAL players were the problem. What if they merely differ?")
    print("    Same perfect optimisers, no path noise — they just want different things:")
    print("    their own risk tolerance and their own appetite for the fast line. That is")
    print("    the one thing unambiguously true of a real population.\n")
    for spread in (0.0, 0.2, 0.4, 0.6, 0.8):
        e, d, st = run_heterogeneous(spread=spread, gens=200)
        m, _, _ = summarise(e, burn=60)
        p = cycle_period(st)
        print(f"      spread {spread:.1f}:  entropy {m:.3f}   distinct paths {d[-1]:3d}/{POOL}"
              f"   cycle period {p if p else '>40 (none found)'}")
    e_het, d_het, st_het = run_heterogeneous(spread=0.6, gens=200)
    mean_het, _, _ = summarise(e_het, burn=60)
    period_het = cycle_period(st_het)
    distinct_het = d_het[-1]

    print("\n" + "-" * 78)
    print("\nG3  Where is the boundary? Fast-line pull vs collision cost.")
    print("    Kill condition: diversity only survives at one magic ratio.\n")
    print("      pull \\ hazard      0.5     1.0     2.0     4.0     8.0")
    hazards = [0.5, 1.0, 2.0, 4.0, 8.0]
    viable = 0
    total = 0
    for pull in (0.25, 0.5, 1.0, 2.0, 4.0):
        cells = []
        for h in hazards:
            e, _, _ = run(pull=pull, hazard=h, temperature=0.0, gens=140)
            m, _, _ = summarise(e, burn=40)
            cells.append(m)
            total += 1
            if m > 0.35:
                viable += 1
        print(f"      pull {pull:<5.2f}     " + "  ".join(f"{c:.3f}" for c in cells))
    print(f"\n      cells with entropy > 0.35: {viable}/{total}")

    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    g1 = mean_e > 0.35
    g2 = period_hom is None or period_hom > 20        # identical players
    g2b = (period_het is None or period_het > 20) and distinct_het > 20
    g3 = viable / total > 0.4
    for name, ok, why in [
        ("G1 diversity survives optimisers", g1, f"settled entropy {mean_e:.3f}"),
        ("G2 level has many states", g2,
         f"period {period_hom}, {distinct_hom[-1]} distinct paths — identical players"),
        ("G2b heterogeneity rescues it", g2b,
         f"period {period_het if period_het else '>40'}, {distinct_het} distinct paths"),
        ("G3 broad viable basin", g3, f"{viable}/{total} of the parameter grid"),
    ]:
        print(f"  [{'PASS' if ok else 'FAIL'}]  {name:34s}  {why}")
    print()
    if g2:
        print("  The stated kill condition is NOT met.")
    elif g2b:
        print("  The kill condition IS met for identical players — the pool collapses to a")
        print("  short loop and the level becomes a small automaton. It is NOT met once")
        print("  players merely differ from each other.")
        print()
        print("  That relocates the bet. The card claims the hazard feedback keeps the")
        print("  level alive; it does not. What keeps it alive is that the population is")
        print("  varied. So the design question is not 'do ghosts create pressure' but")
        print("  'is my player base heterogeneous enough, and what happens to a level")
        print("  once the good players converge?' Segment the ghost pool by skill, or")
        print("  the top of the ladder gets a seven-state game.")
    else:
        print("  The kill condition IS met and heterogeneity does not rescue it. Stop.")
    print()
    print("  What this does NOT show: whether dodging a stranger's ghost feels different")
    print("  from dodging a designed bullet pattern, which is the actual product question")
    print("  and needs fifty real runs from ten real people.")
