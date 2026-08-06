"""
Estate Liquidators — R17: widen the appraiser's PAYOFF, since R16 killed the cost side.

R16 established that no cost you bolt onto scanning can make it more attractive — the
best available edge over blind hauling falls monotonically as you punish scanning
harder. A thin edge can only be widened from the benefit side. This is the benefit-side
lever `DESIGN.md` §4.4 has wanted since R9: make scanning **situational**.

THE IDEA. Scanning's payoff is `E[max of 4] − E[1 of 4]`, and for a uniform band of
half-width h that is exactly `0.6h`. So the payoff is proportional to the SPREAD of the
room you are standing in, and nothing else. A curio cabinet of wildly unlike objects —
a snuffbox, a ship model, a bad painting — is worth three loud seconds. A shelf of forty
identical books is not, because you already know what the best one is worth.

WHY THIS IS A DIFFERENT AXIS. Every previous lever (R6 retrieval, R8 candidates, R16
tail risk) moved a single global number, so the best policy stayed a global one: scan,
or don't. Spread varies ROOM TO ROOM, so the question gets asked fresh in every room and
the answer legitimately differs. That is a decision in the sense this project means it —
four people in a doorway, disagreeing.

THE HONEST-EXPERIMENT PART. Room heterogeneity is controlled by H: each room's
half-width is `f × w` with `f` uniform on `[1−H, 1+H]`. Because `E[f] = 1` for every H:

    E[BLIND value] = m                     — independent of H
    E[SCAN value]  = m + 0.6·w·E[f] = m + 0.6w   — independent of H

**H cannot help either extreme. It is arithmetically incapable of it.** So any edge that
appears as H rises belongs entirely to the policy that can tell rooms apart, and this
sweep cannot be accused of simply handing the appraiser more money. That is the property
R5's myopia bug and R6's strawman were both missing.

VAR_q = appraise the top q fraction of rooms by spread. VARGATE_q = that, AND only while
the house is quiet (R16's keeper). SIGMA is how badly the crew misjudges a room from its
look — the whole mechanic depends on spread being telegraphed, so it gets pressure-tested
rather than assumed.

--------------------------------------------------------------------------------------
WHAT IT FOUND — it works, and it is the first thing in this project to move the edge UP.

1. +6.2% -> +10.0% as H goes 0 -> 1.0. Every previous lever (R6, R8, R16) moved the best
   available edge down or sideways. The control held exactly as designed: BLIND sat at
   $6,485 and SCAN at ~$6,470 across the ENTIRE sweep, unmoved. So the gain is not extra
   money in the estate — it is money that only a crew reading rooms can reach.

2. IT NEEDS A LOT OF HETEROGENEITY, WHICH MEANS IT MUST BE AUTHORED. At H=0.25 nothing
   happens at all (the flat quiet-gate still wins); the selective policy does not take
   the lead until H=0.5, and the payoff climbs roughly linearly after that. An estate
   authored without thinking about spread sits at H=0, so this cannot be left to
   judgement -- hence LEVEL-SPEC 2.1's three room classes and V11's ratio check.

3. THE TELEGRAPH DEGRADES GRACEFULLY, which was the real risk. Misreading rooms costs
   surprisingly little: sigma 0 -> +10.0%, 0.5 -> +8.9%, 1.0 -> +7.8% (still well ahead
   of the +6.2% baseline), collapsing to baseline only at sigma=2.0. A crew that reads
   rooms BADLY still beats a crew that doesn't read them. Skill ceiling without a skill
   floor.

4. NOISE MAKES YOU PICKIER. VAR_0.5 (scan the top half of rooms) is optimal with a
   perfect read; the moment any read noise exists, VAR_0.25 takes over. "When you're not
   sure, only stop for the obviously weird rooms."

5. THE ROOM BEATS THE HOUSE, but the house is still the safe line. Pairing R16's
   quiet-gate with the room rule LOSES mean ($6,982 vs $7,133) because the two fight --
   the quiet window is early night and good rooms arrive whenever they arrive. But it
   wins the FLOOR decisively: p10 $6,147 vs $5,853, ending at Disturbance 39 vs 72. Two
   defensible strategies about $150 apart with very different variance is a better
   outcome than one dominant one. See D-22's amendment.

Run: python appraiser_variance.py
"""

import random
import statistics

CREW = 4
NIGHT_S = 720.0
HAUL_S = 540.0
VAN_SLOTS = 14

IMPULSE = 0.09
SUSTAINED = 0.02
DECAY_PER_MIN = 50.0
RATCHET_END = 55.0

L = {"sprint": 45, "appraise": 48, "door": 60, "dolly": 35,
     "radio": 38, "break_small": 90}

CANDIDATES = 4
PARALLEL_EFFICIENCY = 0.65

RETRIEVAL = {"DORMANT": 0.00, "PATROL": 0.02, "PURSUE": 0.10, "COLLECT": 0.25}
TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]
TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}

QUIET = 30.0        # R16: the DORMANT/PATROL boundary, and the only free place to scan


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for start, ti in PHASES:
        if t >= start:
            tier = ti
    return tier


def spread_threshold(q, H):
    """The f above which a crew scanning the top q fraction of rooms will stop."""
    return 1.0 + H * (1.0 - 2.0 * q)


def wants_scan(policy, d, slots, f_hat, H):
    if policy == "BLIND":
        return False
    if policy == "SCAN":
        return True
    if policy == "GATE":                       # R16's winner, spread-blind
        return d < QUIET
    if policy == "ADAPTIVE":                   # R8's van-fill heuristic
        return slots <= 0.5 * VAN_SLOTS
    if policy.startswith("VARGATE_"):
        return d < QUIET and f_hat >= spread_threshold(float(policy[8:]), H)
    if policy.startswith("VAR_"):
        return f_hat >= spread_threshold(float(policy[4:]), H)
    raise ValueError(policy)


def run_night(seed, policy, H=0.0, sigma=0.0, cursed=2):
    rng = random.Random(seed)
    d, t, slots, banked, filled = 0.0, 0.0, float(VAN_SLOTS), 0.0, 0.0
    trips, scan_trips, lost = 0, 0, 0

    while t < HAUL_S and slots > 0:
        tier = depth_at(t)
        trip_s, band = TIER_DATA[tier]
        per_trip = trip_s / (CREW * PARALLEL_EFFICIENCY)

        if filled >= TIER_CAP[tier] * VAN_SLOTS and tier < 3:
            t += per_trip
            continue

        # This room's spread. E[f] = 1 for every H, so the mean value of the room is
        # untouched -- only how much scanning is WORTH here changes.
        lo, hi = band
        m, w = (lo + hi) / 2.0, (hi - lo) / 2.0
        f = rng.uniform(1.0 - H, 1.0 + H)
        # Clamp the half-width at the mean so no object is ever worth less than nothing.
        # Tier 1 is the only band where this bites (w/m = 0.58, so it engages above
        # f = 1.73) and clamping a SYMMETRIC uniform leaves its mean at m exactly, so
        # the H-invariance of BLIND survives untouched. It slightly shrinks the payoff
        # in the very widest rooms, which makes this sweep conservative, not generous.
        h = min(f * w, m)
        candidates = [rng.uniform(m - h, m + h) for _ in range(CANDIDATES)]

        # What the crew THINKS the spread is, from the look of the room.
        f_hat = f if sigma <= 0.0 else f + rng.gauss(0.0, sigma * max(H, 1e-9))

        appraise = wants_scan(policy, d, slots, f_hat, H)

        cost = per_trip
        if appraise:
            value = max(candidates)
            cost += 3.0 * CANDIDATES / CREW
        else:
            value = rng.choice(candidates)

        floor = RATCHET_END * (t / NIGHT_S) + cursed * 2.0
        for _ in range(int(cost)):
            for _ in range(CREW):
                if rng.random() < 0.04:
                    d += L["sprint"] * SUSTAINED
            if rng.random() < 0.15:
                d += L["dolly"] * SUSTAINED
            if rng.random() < 0.08:
                d += L["radio"] * SUSTAINED
            if rng.random() < 0.055:
                d += L["door"] * IMPULSE
            if rng.random() < 0.006:
                d += L["break_small"] * IMPULSE
            d = max(floor, min(100.0, d - DECAY_PER_MIN / 60.0))

        if appraise:
            d = min(100.0, d + CANDIDATES * L["appraise"] * IMPULSE)

        t += cost
        if t > HAUL_S:
            break
        filled += 1.0
        trips += 1
        if appraise:
            scan_trips += 1

        if rng.random() < RETRIEVAL[tier_of(d)]:
            lost += 1
            slots -= 1.0
            continue

        slots -= 1.0
        banked += value

    return banked, (scan_trips / trips if trips else 0.0), lost, d


def trial(policy, n=2500, **kw):
    res = [run_night(s, policy, **kw) for s in range(n)]
    return {
        "mean": statistics.mean(r[0] for r in res),
        "share": statistics.mean(r[1] for r in res),
        "lost": statistics.mean(r[2] for r in res),
        "endD": statistics.mean(r[3] for r in res),
    }


POLICIES = ["BLIND", "ADAPTIVE", "GATE", "SCAN",
            "VAR_0.5", "VAR_0.25", "VARGATE_0.5", "VARGATE_0.25"]


def sweep_H():
    print("\n\nDOES ROOM-TO-ROOM VARIANCE WIDEN THE EDGE?")
    print("(H = heterogeneity. E[BLIND] and E[SCAN] are H-invariant by construction.)")
    print("-" * 108)
    print(f"{'H':<6}" + "".join(f"{p:>12}" for p in POLICIES) + f"{'best':>13}{'edge':>8}")
    for H in (0.0, 0.25, 0.5, 0.75, 1.0):
        rows = {p: trial(p, n=2000, H=H) for p in POLICIES}
        best = max(rows, key=lambda x: rows[x]["mean"])
        edge = rows[best]["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{H:<6.2f}" + "".join(f"{rows[p]['mean']:>12,.0f}" for p in POLICIES)
              + f"{best:>13}{edge:>8.1%}")


def sweep_sigma():
    print("\n\nWHAT IF THE CREW MISREADS THE ROOM?   (H = 1.0 held)")
    print("(sigma = how noisy their read of the spread is, in units of H)")
    print("-" * 108)
    print(f"{'sigma':<7}" + "".join(f"{p:>12}" for p in POLICIES) + f"{'best':>13}{'edge':>8}")
    for s in (0.0, 0.25, 0.5, 1.0, 2.0):
        rows = {p: trial(p, n=2000, H=1.0, sigma=s) for p in POLICIES}
        best = max(rows, key=lambda x: rows[x]["mean"])
        edge = rows[best]["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{s:<7.2f}" + "".join(f"{rows[p]['mean']:>12,.0f}" for p in POLICIES)
              + f"{best:>13}{edge:>8.1%}")


def detail(H=1.0):
    print(f"\n\nWHAT THE POLICIES ACTUALLY DO   (H = {H}, perfect read)")
    print("-" * 108)
    print(f"{'policy':<14}{'mean $':>10}{'p10':>9}{'p90':>9}{'scan %':>9}"
          f"{'lost':>7}{'end D':>8}{'vs BLIND':>10}")
    base = None
    for p in POLICIES:
        res = [run_night(s, p, H=H) for s in range(2500)]
        vals = sorted(r[0] for r in res)
        mean = statistics.mean(vals)
        if base is None:
            base = mean
        r = trial(p, n=2500, H=H)
        print(f"{p:<14}{mean:>10,.0f}{vals[len(vals)//10]:>9,.0f}"
              f"{vals[9*len(vals)//10]:>9,.0f}{r['share']:>9.0%}{r['lost']:>7.1f}"
              f"{r['endD']:>8.0f}{mean / base - 1:>10.1%}")


if __name__ == "__main__":
    print("R17 — WIDENING THE APPRAISER'S PAYOFF WITH PER-ROOM VALUE VARIANCE")
    print("=" * 108)
    sweep_H()
    sweep_sigma()
    detail()
