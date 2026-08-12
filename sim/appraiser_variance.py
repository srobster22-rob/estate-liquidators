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

(Figures are R18's re-run, after it found that this file and integrated.py were both
using an inert cursed-cargo floor of 2.0 against tuning.json's canonical 7.0. The
correction lowers every absolute number by about 1.7 points — the headline is +4.2% ->
+8.8%, not the +6% -> +10% first reported — and it changed one conclusion outright,
flagged in 5 below.)

1. +4.2% -> +8.8% as H goes 0 -> 1.0: the edge roughly DOUBLES. Every previous lever
   (R6, R8, R16) moved the best available edge down or sideways. The control held
   exactly as designed: BLIND sat at ~$6,430 and SCAN at ~$6,400 across the ENTIRE
   sweep, unmoved. So the gain is not extra money in the estate — it is money only a
   crew that reads rooms can reach.

2. IT NEEDS A LOT OF HETEROGENEITY, WHICH MEANS IT MUST BE AUTHORED. At H=0.25 the
   selective policies barely edge ahead; they do not take a clear lead until H=0.5, and
   the payoff climbs roughly linearly after that. An estate authored without thinking
   about spread sits at H=0, so this cannot be left to judgement -- hence LEVEL-SPEC
   2.1's three room classes and V11's ratio check.

3. THE TELEGRAPH DEGRADES GRACEFULLY, which was the real risk. Misreading rooms costs
   surprisingly little: sigma 0 -> +8.8%, 0.5 -> +7.8%, 1.0 -> +6.5%, and even sigma=2.0
   (a read noisier than the entire range of rooms) still returns +5.6% — above the
   spread-blind baseline. A crew that reads rooms BADLY still beats a crew that doesn't
   read them at all. Skill ceiling without a skill floor.

4. NOISE MAKES YOU PICKIER, AND SO DOES THE GATE. With a perfect read the top-half rules
   win; with any read noise the top-QUARTER rules take over. Same in the gate sweep: the
   pickier you are about rooms, the later into the night you can afford to keep scanning
   (GATE alone peaks at 45, VARGATE_0.5 at 60, VARGATE_0.25 at 75). "When you're not
   sure, only stop for the obviously weird rooms."

5. THE ROOM AND THE HOUSE ARE WORTH EXACTLY THE SAME — R18 OVERTURNED R17 HERE.
   R17 reported that gating on the room beat gating on both, with the combined rule
   surviving only as a safer, lower-variance line. That was an artifact of the wrong
   cursed floor AND of pinning the gate at 30. With the floor corrected and the gate at
   its proper threshold of 60 — the PATROL/PURSUE boundary, where retrieval jumps
   0.02 -> 0.10, the only large discontinuity in the cost of being seen — the two are
   statistically identical: over 8,000 paired nights, VARGATE_0.5 minus VAR_0.25 is
   +$0 +/- 12 (t = 0.0).

   That is a better outcome than either one winning. "Scan the top quarter of rooms
   whenever you find them" and "scan the top half, but only while it's still tidying"
   are worth the same money and feel completely different — and the second is
   perceivable without a HUD, because AUDIO-SPEC 3.2 has the Curator stop making
   domestic sounds the moment it switches from tidying to hunting.

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
FLOOR_PER_CURSED = 7.0

L = {"sprint": 45, "appraise": 48, "door": 60, "dolly": 35,
     "radio": 38, "break_small": 90}

CANDIDATES = 4
PARALLEL_EFFICIENCY = 0.65

RETRIEVAL = {"DORMANT": 0.00, "PATROL": 0.02, "PURSUE": 0.10, "COLLECT": 0.25}
TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]
# Tiers 1-3 ONLY: there is no apex object in this model. chain_sim.py has it, and it
# is one cart-class prize worth $4,000-8,000 for five slots (D-21). Consequence, spelled
# out in ECONOMY.md 10: earnings here are ~$3,000 below chain_sim's and NOT comparable
# with a quota, and growth from van upgrades is overstated, because a fixed-size prize
# damps the proportional value of every extra slot.
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]
TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}

# R18 moved this from 30 to 60. With the cursed floor corrected to its canonical 7.0 the
# night simply runs hotter, so a gate at the DORMANT boundary closes almost immediately
# and the crew barely scans at all. 60 is the PATROL/PURSUE boundary -- the point where
# retrieval jumps 0.02 -> 0.10, a 5x step, and the only large discontinuity in the cost
# of being seen. "Scan while it is merely tidying; stop when it starts hunting."
# Threshold sensitivity is printed by sweep_gate() below; the spread-BLIND gate peaks
# slightly lower, at 45.
QUIET = 60.0


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


def wants_scan(policy, d, slots, f_hat, H, cap=VAN_SLOTS):
    if policy == "BLIND":
        return False
    if policy == "SCAN":
        return True
    if policy == "GATE":                       # R16's winner, spread-blind
        return d < QUIET
    if policy == "ADAPTIVE":                   # R8's van-fill heuristic
        return slots <= 0.5 * cap
    if policy.startswith("VARGATE_"):
        return d < QUIET and f_hat >= spread_threshold(float(policy[8:]), H)
    if policy.startswith("VAR_"):
        return f_hat >= spread_threshold(float(policy[4:]), H)
    raise ValueError(policy)


def run_night(seed, policy, H=0.0, sigma=0.0, cursed=2, van=None, estate=None):
    """`estate` = total objects in the house (R35). None keeps the historical infinite
    shelf, where every trip draws four fresh candidates forever.

    R34 found that constraint controls both the crew-size gap and the appraiser's edge in
    chain_sim, and that the appraiser half CONTRADICTS DESIGN 4.4's Requirement A -- it
    said the appraiser does BETTER when the estate is tight, where 4.4 says van scarcity
    is what makes anyone scan. That claim came from a model one round old with two bugs
    already found in it, so it needed an independent route. This is that route: different
    code, no classes, no apex, no curses.
    """
    cap = VAN_SLOTS if van is None else van
    left = estate
    rng = random.Random(seed)
    d, t, slots, banked, filled = 0.0, 0.0, float(cap), 0.0, 0.0
    trips, scan_trips, lost = 0, 0, 0

    while t < HAUL_S and slots > 0:
        tier = depth_at(t)
        trip_s, band = TIER_DATA[tier]
        per_trip = trip_s / (CREW * PARALLEL_EFFICIENCY)

        if filled >= TIER_CAP[tier] * cap and tier < 3:
            t += per_trip
            continue

        if left is not None:
            if left <= 0:
                break                     # the house is picked clean
            left -= CANDIDATES

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

        appraise = wants_scan(policy, d, slots, f_hat, H, cap)

        cost = per_trip
        if appraise:
            value = max(candidates)
            cost += 3.0 * CANDIDATES / CREW
        else:
            value = rng.choice(candidates)

        floor = RATCHET_END * (t / NIGHT_S) + cursed * FLOOR_PER_CURSED
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

    return (banked, (scan_trips / trips if trips else 0.0), lost, d,
            trips, cap - slots)


def trial(policy, n=2500, **kw):
    res = [run_night(s, policy, **kw) for s in range(n)]
    return {
        "mean": statistics.mean(r[0] for r in res),
        "share": statistics.mean(r[1] for r in res),
        "lost": statistics.mean(r[2] for r in res),
        "endD": statistics.mean(r[3] for r in res),
        "trips": statistics.mean(r[4] for r in res),
        "used": statistics.mean(r[5] for r in res),
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


def sweep_gate(H=1.0):
    print(f"\n\nWHERE SHOULD THE QUIET GATE SIT?   (H = {H})")
    print("(30 = DORMANT/PATROL, 60 = PATROL/PURSUE, 85 = PURSUE/COLLECT)")
    print("-" * 108)
    cols = ["GATE", "VARGATE_0.5", "VARGATE_0.25"]
    print(f"{'gate':<8}" + "".join(f"{c:>14}" for c in cols))
    global QUIET
    keep = QUIET
    for g in (30.0, 45.0, 60.0, 75.0, 85.0):
        QUIET = g
        rows = {c: trial(c, n=2000, H=H)["mean"] for c in cols}
        print(f"{g:<8.0f}" + "".join(f"{rows[c]:>14,.0f}" for c in cols))
    QUIET = keep


def sweep_capacity():
    """R24: where does van capacity STOP being the binding constraint?

    D-19 is FIRM, fixes the ceiling at 20 slots, and calls that "just under the cliff"
    on the strength of ECONOMY 6's finding that the appraiser dies between 24 and 32
    slots. That number comes from haul_sim.py, which predates PARALLEL_EFFICIENCY (R7),
    the slot-accounting fix (R8), the derived Disturbance model (R5) and the cursed-floor
    correction (R18). Every one of those changed how many trips a crew gets, which is the
    quantity the whole capacity argument turns on. Nobody re-ran it.

    WHAT THIS SWEEP CAN AND CANNOT ANSWER. It answers *where capacity stops mattering*,
    robustly, because that is set by the trip ceiling and the trip ceiling is analytic:

        0-120s  tier 1 @ 45/(4 x 0.65) = 17.31s  ->  6.93 trips
        120-240 tier 2 @ 60/2.6        = 23.08s  ->  5.20
        240-540 tier 3 @ 90/2.6        = 34.62s  ->  8.67
                                                    -----
                                                    20.8 trips in a 540s night

    It does NOT answer how the edge *varies* with capacity below that point. TIER_CAP is
    expressed as a fraction of the van, so changing capacity also changes the depth
    reservation policy, and the two are confounded. The edge column below is bumpy for
    that reason and should not be read as a trend -- only the VAN/CLOCK transition is
    load-bearing here.
    """
    print("\n\nWHERE DOES CAPACITY STOP BINDING?   (D-19 ships 14, ceiling 20)")
    print("(edge is on a V11 estate. Read the binding column, not the edge trend --")
    print(" the depth-reservation policy scales with the van, so the two are confounded.)")
    print("-" * 108)
    print(f"{'slots':<7}{'BLIND $':>10}{'best $':>11}{'edge':>8}{'trips':>9}"
          f"{'slots used':>12}   {'binding':<8}{'winner':<14}")
    pols = ["ADAPTIVE", "GATE", "SCAN", "VAR_0.5", "VAR_0.25",
            "VARGATE_0.5", "VARGATE_0.25"]
    for cap in (10, 12, 14, 16, 18, 20, 22, 24, 32):
        base = trial("BLIND", n=1500, H=1.0, van=cap)
        rows = {p: trial(p, n=1500, H=1.0, van=cap) for p in pols}
        name = max(rows, key=lambda k: rows[k]["mean"])
        bind = "VAN" if base["used"] > cap - 0.75 else "CLOCK"
        print(f"{cap:<7}{base['mean']:>10,.0f}{rows[name]['mean']:>11,.0f}"
              f"{rows[name]['mean'] / base['mean'] - 1:>8.1%}{base['trips']:>9.1f}"
              f"{base['used']:>12.1f}   {bind:<8}{name:<14}")


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
    sweep_gate()
    sweep_capacity()
    detail()
