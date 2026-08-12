"""
Regression guard for concepts-sim/ — the equivalent of sim/check_drift.py.

WHY THIS EXISTS
    Every figure quoted on a card in GAME-CONCEPTS.md comes out of one of these files. Two
    rounds in, four separate measurements had been confidently wrong before they were right:
    two tautological checks in provenance.py, and in commons.py a cost parameter three orders
    of magnitude too small to matter, a sentinel that scored "greed loses money" as a
    cooperative surplus, and a headline that compared two negative payoffs.

    All four were caught by reading output sceptically. None would have been caught by
    running the file again. So the risk now is the other direction: an edit that silently
    moves a published number while the script still runs clean and still looks plausible.

    This asserts the numbers the documents actually quote. If a card says 85.5%, this fails
    when it stops being 85.5%. Fix the card or fix the model — but do it deliberately.

    Run: python3 concepts-sim/check_numbers.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import provenance as P            # noqa: E402
import commons as C               # noqa: E402

CHECKS = []


def check(label, got, want, tol, where):
    ok = abs(got - want) <= tol
    CHECKS.append((ok, label, got, want, where))
    return ok


# --- provenance.py — quoted on GAME-CONCEPTS.md #16 -------------------------------------

counts, n = P.m1_cue_distribution()
invisible = counts.get(0, 0) / n
middle = sum(counts[c] for c in counts if 1 <= c <= 3) / n
check("undetectable forgeries", invisible, 0.078, 0.005, "#16 card, README")
check("forgeries in 1-3 cue band", middle, 0.745, 0.010, "#16 card")

rows = P.m2_learning_curve()
climb = rows[-1][1] - rows[0][1]
gains = [rows[i][1] - rows[i - 1][1] for i in range(1, len(rows))]
check("largest jump / total climb", max(gains) / climb, 0.43, 0.03, "#16 card (marginal pass)")

gen, fake, best_acc, best_T, n3 = P.m3_separation()
overlap = sum(min(gen.get(c, 0), fake.get(c, 0)) for c in set(gen) | set(fake)) / n3
check("full-knowledge accuracy ceiling", best_acc, 0.855, 0.010, "#16 card, README, top eight")
check("genuine/forgery overlap", overlap, 0.290, 0.010, "#16 card")
check("best threshold (cues)", best_T, 2, 0, "#16 card — 'expertise raises your bar'")

# The emergent finding the card leans on: the optimal threshold RISES with knowledge.
# If this stops being true, the card's headline claim is gone even if every number above
# still matches.
thresholds = [T for _, _, T in rows]
CHECKS.append((thresholds[1] < thresholds[-1], "threshold rises with expertise",
               thresholds[1], thresholds[-1], "#16 card — the emergent mechanic"))


# --- commons.py — quoted on GAME-CONCEPTS.md #21 ----------------------------------------

d1 = C.d1_dominance()
check("distinct best responses", len({e for _, e, _, _ in d1}), 4, 0, "#21 card")

d2 = C.d2_surplus()
d2.pop("_social_optimum")
surplus = d2["everyone restrained"][1] / d2["everyone greedy"][1]
check("restraint vs greed", surplus, 1.24, 0.03, "#21 card")

d3 = C.d3_betrayal()
payable = [(k, a) for _, k, a, _ in d3 if a > 0]
check("worst sucker payoff", min(k / a for k, a in payable), 0.41, 0.02, "#21 card")

grid, hits = C.d4_sweep()
check("viable parameter points", len(hits), 4, 0, "#21 card, top eight")
check("sweep size", len(grid), 72, 0, "#21 card")

# Every viable point must have low catchability — that IS the design finding.
CHECKS.append((all(q <= 0.30 for _, q, _, _ in hits), "all viable points low-catchability",
               max((q for _, q, _, _ in hits), default=0), 0.30,
               "#21 card — 'boats must be inefficient'"))


# --- ghosts.py — quoted on GAME-CONCEPTS.md #44 (tombstone) and graveyard entry 33 -------

import ghosts as G                # noqa: E402

_, dist_hom, states_hom = G.run_heterogeneous(spread=0.0, gens=200, seed=7)
check("Ghosts: distinct paths, identical players", dist_hom[-1], 5, 0, "#44 tombstone")
check("Ghosts: limit-cycle period", G.cycle_period(states_hom), 7, 0,
      "#44 tombstone, graveyard 33")

_, dist_het, states_het = G.run_heterogeneous(spread=0.6, gens=200)
check("Ghosts: distinct paths, heterogeneous", dist_het[-1], 7, 0, "#44 tombstone")
CHECKS.append((G.cycle_period(states_het) is None,
               "Ghosts: heterogeneity breaks the cycle", "no cycle", "no cycle",
               "#44 tombstone"))

# The load-bearing claim: variety does NOT scale with level width. If this ever starts
# scaling, the "structural, not a resolution artifact" sentence on the tombstone is wrong
# and the concept deserves reopening.
_saved_lanes = G.LANES
widths = {}
for _w in (8, 48):
    G.LANES = _w
    widths[_w] = G.run_heterogeneous(spread=0.6, gens=180)[1][-1]
G.LANES = _saved_lanes
CHECKS.append((abs(widths[8] - widths[48]) <= 2,
               "Ghosts: variety flat across level width", widths[8], widths[48],
               "#44 tombstone — 'structural, not resolution'"))


if __name__ == "__main__":
    width = max(len(c[1]) for c in CHECKS)
    failed = 0
    print("=" * 78)
    print("concepts-sim regression guard")
    print("=" * 78)
    for ok, label, got, want, where in CHECKS:
        g = f"{got:.3f}" if isinstance(got, float) else str(got)
        w = f"{want:.3f}" if isinstance(want, float) else str(want)
        print(f"  [{'ok' if ok else 'FAIL'}]  {label:<{width}}  {g:>7} vs {w:>7}   {where}")
        failed += not ok
    print("-" * 78)
    print(f"  {len(CHECKS) - failed}/{len(CHECKS)} published figures still hold")
    if failed:
        print("\n  A number quoted in GAME-CONCEPTS.md no longer comes out of the model.")
        print("  Fix the card or fix the model — but don't let them drift apart.")
    sys.exit(1 if failed else 0)
