"""
Estate Liquidators — is the appraiser a decision, or just a chore?

The standing question since R8: scanning beats blind hauling by only +6%, which is
thin enough that players may rationally skip the game's signature mechanic — the
exact failure DESIGN 4.4 exists to prevent.

R10/R11 established the shape of the problem, twice: **a linear cost cannot balance
a multiplicative benefit.** It produces a step function — always-take or never-take —
with no interesting middle. The curse only became a decision when its cost became a
super-linear tail risk, and that produced this project's first interior optimum.

The appraiser has the same shape. Its benefit is multiplicative (pick the best of N
candidates instead of a random one) and every cost it currently carries is linear
(3 seconds, one +4.32 Disturbance ping, per item). So try the same fix:

    **appraising is three seconds standing still, and the Curator can arrive
    during them — with the risk compounding across consecutive scans.**

The model sweeps two things the earlier sims never separated:

  1. how many of a shelf's candidates you scan before committing (0..4), and
  2. whether the right answer CHANGES WITH THE TIER — which is what would make
     scanning situational rather than a global always/never.

Honest caveat, stated up front: the benefit of scanning n candidates is concave
(diminishing returns on max-of-n) and interception risk is convex in n, so *an*
interior optimum is arithmetic, not a discovery. The findings worth having are
where it sits under the game's real numbers, whether it moves across tiers, and
by how much a tier-aware policy beats the best fixed one. A tier-invariant
optimum is not a decision — it is a number to hard-code and forget.

Constants are imported from integrated.py so this cannot drift from the tuned
night model. Run: python sim/appraise_test.py
"""

import random
import statistics
import sys

from integrated import (CANDIDATES, CREW, DECAY_PER_MIN, FLOOR_PER_CURSED, HAUL_S,
                        IMPULSE, L, NIGHT_S, PARALLEL_EFFICIENCY, RATCHET_END,
                        RETRIEVAL, SUSTAINED, TIER_DATA, VAN_SLOTS, depth_at, tier_of)

# Per-scan interception: you are stationary for APPRAISE_S, and the risk of the
# Curator arriving compounds across a run of consecutive scans at the same shelf.
#
#     p(intercepted | n scans) = min(0.95, RETRIEVAL[tier] * K * n ** EXP)
#
# Scaling by RETRIEVAL[tier] falls out of the design rather than being invented:
# at DORMANT the Curator is not hunting, so standing still costs nothing but time.
INTERCEPT_K = 0.60
INTERCEPT_EXP = 1.8

TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}
APPRAISE_S = 3.0

TIER_NAMES = ("DORMANT", "PATROL", "PURSUE", "COLLECT")


def intercept_p(tier_name, n, k=INTERCEPT_K, exp=INTERCEPT_EXP):
    if n <= 0:
        return 0.0
    return min(0.95, RETRIEVAL[tier_name] * k * n ** exp)


def scans_for(policy, tier_name, depth):
    """How many candidates this policy scans, given tier and estate depth."""
    if callable(policy):
        return policy(tier_name, depth)
    if isinstance(policy, dict):
        return policy[tier_name]
    return policy


def trip_world(seed, i):
    """Everything random about trip i, drawn independently of what came before.

    Policies take different numbers of trips and spend different amounts of time
    in them, so a single per-night stream desynchronises between policies and the
    comparison drowns in Monte Carlo noise - the first version of this sweep
    reported that scanning MORE was better at K=0.15 than at K=0.00, which is
    impossible. Seeding per trip index makes every policy face the same estate.
    """
    rng = random.Random(seed * 1000003 + i)
    return ([rng.uniform(0, 1) for _ in range(CANDIDATES)],
            [[rng.random() for _ in range(4 + CREW)] for _ in range(45)])


def run_night(seed, policy, cursed=2, k=INTERCEPT_K, exp=INTERCEPT_EXP):
    rng = random.Random(seed * 7919 + 13)
    d, t = 0.0, 0.0
    slots = float(VAN_SLOTS)
    banked = 0.0
    scans = lost_scan = lost_haul = 0
    filled = 0.0

    trip = 0
    while t < HAUL_S and slots > 0:
        depth = depth_at(t)
        trip_s, band = TIER_DATA[depth]
        per_trip = trip_s / (CREW * PARALLEL_EFFICIENCY)

        if filled >= TIER_CAP[depth] * VAN_SLOTS and depth < 3:
            t += per_trip
            continue

        unit, events = trip_world(seed, trip)
        trip += 1
        tier_name = tier_of(d)
        n = scans_for(policy, tier_name, depth)
        lo, hi = band
        candidates = [lo + u * (hi - lo) for u in unit]

        # Scan n of them, then take the best you know about. Scanning none means
        # taking an unknown piece, which is the blind strategy.
        if n > 0:
            value = max(candidates[:n])
            cost = per_trip + APPRAISE_S * n / CREW
            scans += n
        else:
            value = candidates[int(unit[0] * CANDIDATES) % CANDIDATES]
            cost = per_trip

        # --- Disturbance across the trip (same event rates as integrated.py) ---
        floor = RATCHET_END * (t / NIGHT_S) + cursed * FLOOR_PER_CURSED
        for sec in range(min(int(cost), len(events))):
            e = events[sec]
            for c in range(CREW):
                if e[c] < 0.04:
                    d += L["sprint"] * SUSTAINED
            if e[CREW] < 0.15:
                d += L["dolly"] * SUSTAINED
            if e[CREW + 1] < 0.08:
                d += L["radio"] * SUSTAINED
            if e[CREW + 2] < 0.055:
                d += L["door"] * IMPULSE
            if e[CREW + 3] < 0.006:
                d += L["break_small"] * IMPULSE
            d = max(floor, min(100.0, d - DECAY_PER_MIN / 60.0))

        if n > 0:
            d = min(100.0, d + n * L["appraise"] * IMPULSE)

        t += cost
        if t > HAUL_S:
            break
        filled += 1.0

        # Both rolls are drawn every trip, used or not, so the risk stream stays
        # aligned across policies - a policy that scans less must not thereby get
        # a different retrieval roll on the same trip.
        roll_scan, roll_haul = rng.random(), rng.random()
        if roll_scan < intercept_p(tier_name, n, k, exp):
            lost_scan += 1
            slots -= 1.0
            continue

        if roll_haul < RETRIEVAL[tier_of(d)]:
            lost_haul += 1
            slots -= 1.0
            continue

        slots -= 1.0
        banked += value

    return banked, scans, lost_scan, lost_haul, d


def trial(policy, n=2500, **kw):
    res = [run_night(s, policy, **kw) for s in range(n)]
    return {
        "mean": statistics.mean(r[0] for r in res),
        "scans": statistics.mean(r[1] for r in res),
        "caught": statistics.mean(r[2] for r in res),
        "lost": statistics.mean(r[3] for r in res),
        "endD": statistics.mean(r[4] for r in res),
    }


def best_fixed(k, n=1200):
    rows = {i: trial(i, n=n, k=k) for i in range(CANDIDATES + 1)}
    best = max(rows, key=lambda i: rows[i]["mean"])
    return best, rows


def best_per_tier(k, n=1200):
    """Optimal scan count at each tier, holding the others at the best fixed value."""
    base, _ = best_fixed(k, n=n)
    policy = {t: base for t in TIER_NAMES}
    for tier in TIER_NAMES:
        scores = {}
        for i in range(CANDIDATES + 1):
            trial_policy = dict(policy)
            trial_policy[tier] = i
            scores[i] = trial(trial_policy, n=n, k=k)["mean"]
        policy[tier] = max(scores, key=lambda i: scores[i])
    return policy


def by_scan_count(k, n=2000, **kw):
    return {i: trial(i, n=n, k=k, **kw) for i in range(CANDIDATES + 1)}


def conditional_best(k, key, values, n=1500):
    """Best scan count for each tier (or depth), holding the rest at best fixed.

    `key` is "tier" or "depth". Returns {value: (best_n, gain_over_fixed)}.
    """
    rows = by_scan_count(k, n=n)
    fixed = max(rows, key=lambda i: rows[i]["mean"])
    out = {}
    for v in values:
        scores = {}
        for i in range(CANDIDATES + 1):
            def policy(tier_name, depth, _v=v, _i=i, _f=fixed):
                here = tier_name if key == "tier" else depth
                return _i if here == _v else _f
            scores[i] = trial(policy, n=n, k=k)["mean"]
        best = max(scores, key=lambda i: scores[i])
        out[v] = (best, scores[best] / rows[fixed]["mean"] - 1)
    return fixed, rows[fixed]["mean"], out


def main():
    print("HOW MANY OF A SHELF'S FOUR CANDIDATES SHOULD YOU SCAN?")
    print("Every earlier sim tested only the corners - BLIND (0) against SCAN (4).")
    print("R8's ADAPTIVE interpolated in TIME (scan once the van is half full), not")
    print("in breadth, so the middle of this axis had never been measured at all.")
    print("-" * 78)
    print(f"{'K':<7}" + "".join(f"{('n=' + str(i)):>10}" for i in range(CANDIDATES + 1))
          + f"{'peak':>7}{'vs blind':>10}{'vs scan-all':>13}")
    for k in (0.00, 0.15, 0.30, 0.60, 1.20):
        rows = by_scan_count(k)
        peak = max(rows, key=lambda i: rows[i]["mean"])
        print(f"{k:<7.2f}" + "".join(f"{rows[i]['mean']:>10,.0f}"
                                    for i in range(CANDIDATES + 1))
              + f"{peak:>7}"
              + f"{rows[peak]['mean'] / rows[0]['mean'] - 1:>10.1%}"
              + f"{rows[peak]['mean'] / rows[CANDIDATES]['mean'] - 1:>13.1%}")

    K = 0.30
    print(f"\n\nIS IT SITUATIONAL?  (K={K})")
    print("A policy worth playing has to CHANGE with the situation. If the best")
    print("answer is the same everywhere it is a constant, not a decision.")
    print("-" * 78)
    for key, values, label in (("tier", TIER_NAMES, "Disturbance tier"),
                               ("depth", (1, 2, 3), "estate depth")):
        fixed, fixed_mean, out = conditional_best(K, key, values)
        print(f"\n  by {label}  (best fixed policy = scan {fixed}, ${fixed_mean:,.0f})")
        for v, (best, gain) in out.items():
            flag = "" if best == fixed else "   <- differs"
            print(f"    {str(v):<10} best n = {best}   {gain:+.1%} vs fixed{flag}")

    print("\n\nTHE POLICY THAT FALLS OUT OF IT, PRICED AGAINST THE BEST CONSTANT")
    print("  scan 2 while it is quiet and the room is worth it, 0 once it is hunting")
    print("-" * 78)
    print(f"{'K':<7}{'blind':>10}{'scan-all':>10}{'best fixed':>12}{'combined':>10}"
          f"{'vs fixed':>10}{'vs blind':>10}")

    def combined(tier_name, depth):
        if tier_name in ("PURSUE", "COLLECT"):
            return 0
        return 2 if depth >= 2 else 1

    for k in (0.00, 0.15, 0.30, 0.60, 1.20):
        rows = by_scan_count(k)
        fixed = max(rows, key=lambda i: rows[i]["mean"])
        c = trial(combined, n=2000, k=k)["mean"]
        print(f"{k:<7.2f}{rows[0]['mean']:>10,.0f}{rows[CANDIDATES]['mean']:>10,.0f}"
              f"{rows[fixed]['mean']:>12,.0f}{c:>10,.0f}"
              f"{c / rows[fixed]['mean'] - 1:>10.1%}{c / rows[0]['mean'] - 1:>10.1%}")

    print("\n\nWHAT IT COSTS TO BE CAUGHT MID-SCAN")
    print("-" * 78)
    print(f"{'tier':<10}" + "".join(f"{('n=' + str(i)):>9}" for i in range(CANDIDATES + 1)))
    bad = []
    for tier in TIER_NAMES:
        ps = [intercept_p(tier, i, K) for i in range(CANDIDATES + 1)]
        if any(b < a for a, b in zip(ps, ps[1:])):
            bad.append(tier)
        print(f"  {tier:<8}" + "".join(f"{p:>9.3f}" for p in ps))
    if bad:
        print(f"  FAIL  risk not monotone in scan count for {bad}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
