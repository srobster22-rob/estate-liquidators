"""
Estate Liquidators — is taking cursed cargo ever a real decision?

R9 found the van-side cost can't balance a x6 malignant multiplier: no defensible
Disturbance floor offsets a 480% value bonus, so cursed items are always correct to
take. DESIGN 4.2 calls a cursed item "a burden you chose"; arithmetically it is free
money with atmosphere.

integrated.py never modelled the VALUE side of curses at all, only the count feeding
the floor — which is why this needed its own file.

The test: sweep the malignant multiplier and ask whether REFUSING cursed cargo is ever
the better play. If refusal never wins at any plausible multiplier, the grade is not a
choice and DESIGN 4.2 needs rewriting rather than retuning.
"""

import random
import statistics

CREW, HAUL_S, NIGHT_S, VAN = 4, 540.0, 720.0, 14
DECAY, IMPULSE, SUSTAINED = 50.0, 0.09, 0.02
RATCHET_END = 55.0
FLOOR_PER_CURSED = 7.0                    # R9 recommendation, up from 2.0

# R11 - the curse as a TAIL RISK. R10 proved a linear cost can never balance a
# multiplicative benefit, so the cost has to be catastrophic instead of marginal: the
# collection reclaims the WHOLE van, with probability rising super-linearly in how many
# cursed pieces are aboard. One is a shrug; five should be a real chance of nothing.
RUIN_K = 0.0
RUIN_EXP = 1.8

GRADE_P = [("clean", 0.70), ("tainted", 0.22), ("malignant", 0.08)]
FEE = {"clean": 0.0, "tainted": 0.08, "malignant": 0.20}
ATTENTION = {"clean": 1.0, "tainted": 1.5, "malignant": 3.0}
RETRIEVAL = {"DORMANT": 0.0, "PATROL": 0.02, "PURSUE": 0.10, "COLLECT": 0.25}
TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]
PAR_EFF = 0.65


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for s, ti in PHASES:
        if t >= s:
            tier = ti
    return tier


def grade(rng):
    r = rng.random()
    acc = 0.0
    for g, p in GRADE_P:
        acc += p
        if r < acc:
            return g
    return "clean"


def cap_of(policy):
    """CAP_n = take cursed while fewer than n are aboard. The interior policies."""
    if policy.startswith("CAP_"):
        return int(policy[4:])
    return {"TAKE_ALL": 99, "REFUSE_MALIGNANT": 99, "REFUSE_ALL_CURSED": 0}[policy]


def run(seed, policy, mal_mult):
    rng = random.Random(seed)
    mult = {"clean": 1.0, "tainted": 2.5, "malignant": mal_mult}
    d, t, slots, gross, fees, cursed_aboard = 0.0, 0.0, float(VAN), 0.0, 0.0, 0
    TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}
    filled = 0.0

    while t < HAUL_S and slots > 0:
        tier = depth_at(t)
        trip_s, band = TIER_DATA[tier]
        per_trip = trip_s / (CREW * PAR_EFF)
        if filled >= TIER_CAP[tier] * VAN and tier < 3:
            t += per_trip
            continue

        cands = []
        for _ in range(4):
            g = grade(rng)
            cands.append((rng.uniform(*band) * mult[g], g))

        if policy.startswith("CAP_"):
            pool = ([c for c in cands if c[1] == "clean"] or cands)                 if cursed_aboard >= cap_of(policy) else cands
        elif policy == "REFUSE_MALIGNANT":
            pool = [c for c in cands if c[1] != "malignant"] or cands
        elif policy == "REFUSE_ALL_CURSED":
            pool = [c for c in cands if c[1] == "clean"] or cands
        else:
            pool = cands
        value, g = max(pool)

        cost = per_trip + 3.0 * 4 / CREW      # every strategy appraises (needs grade)
        floor = RATCHET_END * (t / NIGHT_S) + cursed_aboard * FLOOR_PER_CURSED
        for _ in range(int(cost)):
            for _ in range(CREW):
                if rng.random() < 0.04:
                    d += 45 * SUSTAINED
            if rng.random() < 0.15:
                d += 35 * SUSTAINED
            if rng.random() < 0.055:
                d += 60 * IMPULSE
            d = max(floor, min(100.0, d - DECAY / 60.0))
        d = min(100.0, d + 4 * 48 * IMPULSE)

        t += cost
        if t > HAUL_S:
            break
        filled += 1.0

        # Carrying a cursed item makes you a bigger target on the way home.
        risk = RETRIEVAL[tier_of(d)] * (1.0 + 0.25 * (ATTENTION[g] - 1.0))
        slots -= 1.0
        if rng.random() < risk:
            continue

        gross += value
        fees += value * FEE[g]
        if g != "clean":
            cursed_aboard += 1

    net = gross - fees
    if RUIN_K > 0 and cursed_aboard > 0:
        p_ruin = min(0.95, RUIN_K * cursed_aboard ** RUIN_EXP)
        if rng.random() < p_ruin:
            return 0.0        # the collection takes the van back
    return net


def trial(policy, mal_mult, n=2000):
    return statistics.mean(run(s, policy, mal_mult) for s in range(n))


def sweep_ruin():
    global RUIN_K
    print("\n\nR11 - CURSE AS TAIL RISK  (malignant x6 kept; does an interior cap win?)")
    print("-" * 78)
    pols = ["CAP_0", "CAP_1", "CAP_2", "CAP_3", "CAP_4", "TAKE_ALL"]
    print(f"{'ruin k':<9}" + "".join(f"{p:>10}" for p in pols) + f"{'best':>10}")
    for k in (0.0, 0.004, 0.008, 0.015, 0.025, 0.040):
        RUIN_K = k
        rows = {p: trial(p, 6.0, n=2500) for p in pols}
        best = max(rows, key=lambda x: rows[x])
        print(f"{k:<9.3f}" + "".join(f"{rows[p]:>10,.0f}" for p in pols)
              + f"{best:>10}")
    RUIN_K = 0.0


if __name__ == "__main__":
    print(f"CURSE MULTIPLIER SWEEP   (floor {FLOOR_PER_CURSED:.0f}/item, net of fees)")
    print("-" * 78)
    print(f"{'malignant':<11}{'TAKE ALL':>11}{'refuse mal':>13}"
          f"{'refuse all':>13}{'best':>18}")
    for m in (6.0, 4.0, 3.0, 2.5, 2.0, 1.5):
        rows = {p: trial(p, m) for p in
                ("TAKE_ALL", "REFUSE_MALIGNANT", "REFUSE_ALL_CURSED")}
        best = max(rows, key=lambda k: rows[k])
        print(f"x{m:<10.1f}{rows['TAKE_ALL']:>11,.0f}"
              f"{rows['REFUSE_MALIGNANT']:>13,.0f}"
              f"{rows['REFUSE_ALL_CURSED']:>13,.0f}{best:>18}")
    sweep_ruin()
