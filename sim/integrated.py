"""
Estate Liquidators — integrated night.

haul_sim.py found the appraiser's tuning target by sweeping a free "loss coefficient"
that stood in for how badly noise punishes you, and landed on 0.50-0.75. That was a
placeholder for a system that did not exist yet.

It exists now. R3/R4 rebuilt Disturbance as a fast-decaying noise level plus a
ratcheting floor, tuned to decay 50/min. So the punishment is no longer a free
parameter — it can be DERIVED. Appraising costs L=48 x 0.09 = +4.32 Disturbance, that
Disturbance drives the Curator's tier, and the tier drives how often it takes your
cargo off you.

The question: with real numbers instead of a stand-in, does scanning still pay?

Run: python integrated.py
"""

import random
import statistics

CREW = 4
NIGHT_S = 720.0
HAUL_S = 540.0
VAN_SLOTS = 14

IMPULSE = 0.09
SUSTAINED = 0.02
DECAY_PER_MIN = 50.0        # R4
RATCHET_END = 55.0          # floor climbs 0 -> 55 across the night
FLOOR_PER_CURSED = 7.0      # R9. Was an inline 2.0 here until R20 - see below.

L = {"sprint": 45, "appraise": 48, "door": 60, "dolly": 35,
     "radio": 38, "break_small": 90}

# Per-trip chance the Curator relieves you of what you are carrying, by tier.
CANDIDATES = 4
SCAN_EXPOSURE = 0.0   # extra risk while stationary and scanning

# Four players do not achieve 4x throughput: they collide in doorways, wait on each
# other, and re-walk ground. Without this the model has 2.6x more trips than van slots,
# which leaves so much slack that losing cargo is a FREE REROLL -- and rerolls help the
# picky strategy, so harsher punishment made scanning better. chain_sim.py measured a
# real crew at 20-24 extractions against 14 slots (~1.5x), so calibrate to that.
PARALLEL_EFFICIENCY = 0.65

RETRIEVAL = {"DORMANT": 0.00, "PATROL": 0.02, "PURSUE": 0.10, "COLLECT": 0.25}

TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for start, ti in PHASES:
        if t >= start:
            tier = ti
    return tier


def run_night(seed, strategy, cursed=2, retrieval_scale=1.0):
    """One night with Disturbance and the haul loop fully coupled."""
    rng = random.Random(seed)
    d = 0.0
    t = 0.0
    slots = float(VAN_SLOTS)
    banked = 0.0
    scans = 0
    lost = 0

    # Depth budget. A crew that has run this estate type once knows the cellar beats
    # the foyer, and that knowledge has NOTHING to do with the appraiser — so every
    # strategy gets it. Without this, BLIND fills the van by t~200s, before tier 3 even
    # unlocks at 240s, and loses to SCAN purely because scanning wastes enough time to
    # accidentally wait for the good wings. That is a strawman, not a finding.
    # (Third time this exact myopia bug has appeared in this project. See LOOP_LOG R5.)
    TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}
    filled = 0.0

    while t < HAUL_S and slots > 0:
        tier = depth_at(t)
        trip_s, band = TIER_DATA[tier]
        per_trip = trip_s / (CREW * PARALLEL_EFFICIENCY)

        # Hold slots back for depth we know is coming.
        if filled >= TIER_CAP[tier] * VAN_SLOTS and tier < 3:
            t += per_trip          # scout / stage instead of hauling junk
            continue

        candidates = [rng.uniform(*band) for _ in range(CANDIDATES)]
        appraise = strategy == "SCAN" or (
            strategy == "ADAPTIVE" and slots <= 0.5 * VAN_SLOTS)

        cost = per_trip
        if appraise:
            value = max(candidates)
            cost += 3.0 * CANDIDATES / CREW
            scans += CANDIDATES
        else:
            value = rng.choice(candidates)

        # --- Disturbance over the span of this trip -------------------------
        span = cost
        floor = RATCHET_END * (t / NIGHT_S) + cursed * FLOOR_PER_CURSED
        for _ in range(int(span)):
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

        # The appraiser's real cost: one loud ping per item examined.
        if appraise:
            d = min(100.0, d + CANDIDATES * L["appraise"] * IMPULSE)

        t += cost
        if t > HAUL_S:
            break

        # A haul ATTEMPT consumes the opportunity whether or not it lands. Counting
        # only successes let a retrieval act as a free reroll against the depth budget,
        # which is why harsher punishment used to make the picky strategy richer.
        filled += 1.0

        # Standing still to appraise is its own exposure, priced by current tier.
        if appraise and rng.random() < RETRIEVAL[tier_of(d)] * SCAN_EXPOSURE:
            lost += 1
            slots -= 1.0
            continue

        # --- did it take the cargo? -----------------------------------------
        if rng.random() < RETRIEVAL[tier_of(d)] * retrieval_scale:
            lost += 1
            slots -= 1.0
            continue

        slots -= 1.0
        banked += value

    return banked, scans, lost, d


def trial(strategy, n=2500, **kw):
    res = [run_night(s, strategy, **kw) for s in range(n)]
    return {
        "mean": statistics.mean(r[0] for r in res),
        "scans": statistics.mean(r[1] for r in res),
        "lost": statistics.mean(r[2] for r in res),
        "endD": statistics.mean(r[3] for r in res),
    }


if __name__ == "__main__":
    print("APPRAISER vs BLIND — noise cost now DERIVED, not a free parameter")
    print("-" * 78)
    print(f"{'strategy':<12}{'mean $':>10}{'scans':>8}{'lost':>7}{'end D':>8}"
          f"{'vs BLIND':>11}")
    base = trial("BLIND")
    for s in ("BLIND", "ADAPTIVE", "SCAN"):
        r = trial(s)
        print(f"{s:<12}{r['mean']:>10,.0f}{r['scans']:>8.0f}{r['lost']:>7.1f}"
              f"{r['endD']:>8.0f}{r['mean'] / base['mean'] - 1:>11.1%}")

    print("\n\nHOW HARSH DOES RETRIEVAL HAVE TO GET BEFORE SCANNING STOPS PAYING?")
    print("-" * 78)
    print(f"{'scale':<8}{'BLIND':>11}{'ADAPTIVE':>11}{'SCAN':>11}{'best':>11}"
          f"{'edge':>9}")
    for scale in (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
        rows = {s: trial(s, n=1200, retrieval_scale=scale)
                for s in ("BLIND", "ADAPTIVE", "SCAN")}
        best = max(rows, key=lambda k: rows[k]["mean"])
        edge = rows[best]["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{scale:<8.1f}{rows['BLIND']['mean']:>11,.0f}"
              f"{rows['ADAPTIVE']['mean']:>11,.0f}{rows['SCAN']['mean']:>11,.0f}"
              f"{best:>11}{edge:>9.1%}")

    print("\n\nGREED: does hauling cursed cargo change the calculus?")
    print("-" * 78)
    print(f"{'cursed':<9}{'BLIND':>11}{'ADAPTIVE':>11}{'SCAN':>11}{'best':>11}")
    for c in (0, 2, 5, 8):
        rows = {s: trial(s, n=1200, cursed=c)
                for s in ("BLIND", "ADAPTIVE", "SCAN")}
        best = max(rows, key=lambda k: rows[k]["mean"])
        print(f"{c:<9}{rows['BLIND']['mean']:>11,.0f}"
              f"{rows['ADAPTIVE']['mean']:>11,.0f}{rows['SCAN']['mean']:>11,.0f}"
              f"{best:>11}")
