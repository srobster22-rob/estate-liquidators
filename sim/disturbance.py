"""
Estate Liquidators — Disturbance escalation.

DESIGN.md 6.5 defines the pacing spine of the entire game and every number in it was
invented rather than derived:

    gain        L x 0.09 impulse, L x 0.02/s sustained   (AUDIO-SPEC 1.1)
    decay       1/min, floored by cursed cargo in the van
    lights      +25 per wing lit
    levers      kill lights -15, go quiet -20, unload cargo -floor
    tiers       0-30 dormant | 30-60 patrol | 60-85 pursue | 85+ COLLECT

Nobody has checked whether a real night actually crosses those thresholds, when, or
whether the levers are strong enough to be worth using. If tier 3 arrives at minute
eleven of twelve, the escalation never happens. If tier 4 arrives at minute four, the
game is a panic from start to finish.

Run: python disturbance.py
"""

import random
import statistics

CREW = 4
NIGHT_S = 720.0
DT = 1.0

IMPULSE_PER_L = 0.09
SUSTAINED_PER_L = 0.02
DECAY_PER_MIN = 1.0
LIGHT_GAIN = 25.0

# AUDIO-SPEC 1.2
L = {"walk": 20, "sprint": 45, "appraise": 48, "door": 60, "crowbar": 75,
     "break_small": 90, "break_large": 100, "radio": 38, "dolly": 35}

TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]


def tier_of(d):
    return next(name for thr, name in TIERS if d >= thr)


def run_night(seed=0, scan_rate=0.7, use_levers=True, ghost_static=0,
              cursed_items=2, light_wings=2, decay=DECAY_PER_MIN):
    """One night. Returns (curve, first_pursue_t, first_collect_t, lever_uses)."""
    rng = random.Random(seed)
    d = 0.0
    curve = []
    first_pursue = first_collect = None
    quiet_until = -1.0
    lever_uses = 0
    lights_on = 0
    floor = cursed_items * 3.0          # cursed cargo sets the decay floor

    # Ghost Static: DESIGN.md 5.1 — every point spent adds +1 Disturbance.
    static_times = sorted(rng.uniform(180, NIGHT_S) for _ in range(ghost_static))
    si = 0

    t = 0.0
    while t < NIGHT_S:
        quiet = t < quiet_until

        # WALKING IS FREE. AUDIO-SPEC 1.2's table gives walk no Disturbance value,
        # even though the general L x 0.02/s constant would imply 0.4/s. Charging for
        # it means the meter only ever goes up: four players walking generate 1.6/s
        # against a decay of 0.017/s, which pins the meter at 100 inside a minute.
        # That inconsistency in the spec is now called out explicitly.
        hush = 0.35 if quiet else 1.0

        # Sustained sources, per player.
        for _ in range(CREW):
            if rng.random() < 0.04:                       # sprinting right now
                d += L["sprint"] * SUSTAINED_PER_L * hush

        # Sustained sources that are crew-level, not per-player — only one person is
        # pushing the dolly or keying the radio at a time.
        if rng.random() < 0.15:
            d += L["dolly"] * SUSTAINED_PER_L * hush
        if rng.random() < 0.08:
            d += L["radio"] * SUSTAINED_PER_L * hush

        # Impulses, crew-wide rates.
        if rng.random() < 0.085 * scan_rate * hush:
            d += L["appraise"] * IMPULSE_PER_L
        if rng.random() < 0.055 * hush:
            d += L["door"] * IMPULSE_PER_L
        if rng.random() < 0.006:
            d += L["break_small"] * IMPULSE_PER_L
        if rng.random() < 0.0005:
            d += L["break_large"] * IMPULSE_PER_L

        # Lighting a wing: big one-off, and it happens early.
        if lights_on < light_wings and t > 60 and rng.random() < 0.004:
            d += LIGHT_GAIN
            lights_on += 1

        while si < len(static_times) and t >= static_times[si]:
            d += 1.0
            si += 1

        d -= (decay / 60.0) * DT
        d = max(floor, min(100.0, d))

        if use_levers and not quiet:
            if d > 78 and lights_on > 0:
                d -= 15.0
                lights_on -= 1
                lever_uses += 1
            elif d > 82:
                quiet_until = t + 45.0
                d -= 20.0
                lever_uses += 1

        if first_pursue is None and d >= 60:
            first_pursue = t
        if first_collect is None and d >= 85:
            first_collect = t

        curve.append(d)
        t += DT

    return curve, first_pursue, first_collect, lever_uses


def summarise(label, **kw):
    P, C, ends, levers = [], [], [], []
    for s in range(300):
        curve, p, c, lv = run_night(seed=s, **kw)
        P.append(p if p is not None else NIGHT_S)
        C.append(c if c is not None else NIGHT_S)
        ends.append(curve[-1])
        levers.append(lv)
    pr = sum(1 for x in P if x < NIGHT_S) / len(P)
    cr = sum(1 for x in C if x < NIGHT_S) / len(C)
    print(f"{label:<34}{statistics.median(P) / 60:>7.1f}{pr:>8.0%}"
          f"{statistics.median(C) / 60:>9.1f}{cr:>8.0%}"
          f"{statistics.mean(ends):>9.0f}{statistics.mean(levers):>8.1f}")


if __name__ == "__main__":
    print("A NIGHT'S ESCALATION  (medians in minutes; 12-min night)")
    print("-" * 78)
    print(f"{'scenario':<34}{'PURSUE':>7}{'%':>8}{'COLLECT':>9}{'%':>8}"
          f"{'end D':>9}{'levers':>8}")

    summarise("baseline (scan 70%, levers on)")
    summarise("no levers", use_levers=False)
    summarise("greedy: 4 cursed, 3 wings lit", cursed_items=4, light_wings=3)
    summarise("careful: no scans, 0 cursed", scan_rate=0.0, cursed_items=0,
              light_wings=1)
    summarise("ghost spending 6 Static", ghost_static=6)
    summarise("ghost spending 18 Static", ghost_static=18)
