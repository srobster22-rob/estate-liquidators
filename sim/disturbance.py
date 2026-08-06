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

# THE DECAY. R4 tuned this to 50/min and DESIGN 6.5 says "tuned and locked" - but
# this module kept 1.0 as its default, so running it printed the DISPROVEN model,
# and the table the design quotes could not be reproduced from anything committed.
# 50/min is canonical (crew of four; scale by crew/4). SPEC_DECAY is the original
# invented value, kept because the sweep in __main__ is the evidence it was wrong.
DECAY_PER_MIN = 50.0
SPEC_DECAY = 1.0
LIGHT_GAIN = 25.0
KILL_LIGHTS = 15.0
GO_QUIET = 20.0

# THE FLOOR. R17 found this module never had the ratchet at all - its floor was
# `cursed_items * 3.0`, a third value for a constant that is 7 everywhere else,
# and no time term. So the archetype table DESIGN 6.5 presents as the result of
# the restructure was produced by a model missing the restructure's second half,
# and its claim that "the floor guarantees the night escalates anyway" was true
# of the specification and false of the simulation behind the numbers.
RATCHET_END = 55.0
FLOOR_PER_CURSED = 7.0

# THE LEVERS' COOLDOWN. R17 measured what happens without one: a crew that pulls
# a lever every time it crosses 78 does so 5-8 times a night and NEVER SEES
# COLLECT - the escalation's top tier stops existing. An unlimited valve deletes
# the pressure it exists to relieve. At 120s the baseline crew spends 15% of the
# night in COLLECT, which is what DESIGN 6.5 was aiming at all along.
LEVER_COOLDOWN_S = 120.0

# AUDIO-SPEC 1.2
L = {"walk": 20, "sprint": 45, "appraise": 48, "door": 60, "crowbar": 75,
     "break_small": 90, "break_large": 100, "radio": 38, "dolly": 35}

TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]


def tier_of(d):
    return next(name for thr, name in TIERS if d >= thr)


def run_night(seed=0, scan_rate=0.7, use_levers=True, ghost_static=0,
              cursed_items=2, light_wings=2, decay=DECAY_PER_MIN,
              lever_cooldown=LEVER_COOLDOWN_S):
    """One night. Returns (curve, first_pursue_t, first_collect_t, lever_uses)."""
    rng = random.Random(seed)
    d = 0.0
    curve = []
    first_pursue = first_collect = None
    quiet_until = -1.0
    next_lever = 0.0
    lever_uses = 0
    lights_on = 0

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

        # Fast-decaying noise LEVEL over a ratcheting FLOOR (DESIGN 6.5).
        floor = RATCHET_END * (t / NIGHT_S) + cursed_items * FLOOR_PER_CURSED
        d -= (decay / 60.0) * DT
        d = max(floor, min(100.0, d))

        if use_levers and not quiet and t >= next_lever:
            if d > 78 and lights_on > 0:
                d -= KILL_LIGHTS
                lights_on -= 1
                lever_uses += 1
                next_lever = t + lever_cooldown
            elif d > 82:
                quiet_until = t + 45.0
                d -= GO_QUIET
                lever_uses += 1
                next_lever = t + lever_cooldown

        if first_pursue is None and d >= 60:
            first_pursue = t
        if first_collect is None and d >= 85:
            first_collect = t

        curve.append(d)
        t += DT

    return curve, first_pursue, first_collect, lever_uses


def summarise(label, nights=400, **kw):
    """Tier shares and first-contact times. This IS the table in DESIGN 6.5."""
    P, ends, levers = [], [], []
    share = {"DORMANT": 0, "PATROL": 0, "PURSUE": 0, "COLLECT": 0}
    samples = 0
    for s in range(nights):
        curve, p, c, lv = run_night(seed=s, **kw)
        P.append(p if p is not None else NIGHT_S)
        ends.append(curve[-1])
        levers.append(lv)
        for d in curve:
            share[tier_of(d)] += 1
            samples += 1
    pr = sum(1 for x in P if x < NIGHT_S) / len(P)
    hunted = [x for x in P if x < NIGHT_S]
    first = statistics.median(hunted) / 60 if hunted else float("nan")
    row = {k: v / samples for k, v in share.items()}
    print(f"{label:<30}{row['DORMANT']:>9.0%}{row['PATROL']:>8.0%}"
          f"{row['PURSUE']:>8.0%}{row['COLLECT']:>9.0%}"
          f"{first:>10.1f}{pr:>7.0%}{statistics.mean(levers):>8.1f}")
    return row


if __name__ == "__main__":
    print("A NIGHT'S ESCALATION  -  share of a 12-minute night per tier, 400 nights")
    print(f"decay {DECAY_PER_MIN:.0f}/min at a crew of {CREW}; floor ratchets "
          f"0 -> {RATCHET_END:.0f} plus {FLOOR_PER_CURSED:.0f}/cursed item; "
          f"levers on a {LEVER_COOLDOWN_S:.0f}s cooldown")
    print("-" * 78)
    print(f"{'crew':<30}{'DORMANT':>9}{'PATROL':>8}{'PURSUE':>8}{'COLLECT':>9}"
          f"{'1st PUR':>10}{'%':>7}{'levers':>8}")

    summarise("silent running", scan_rate=0.0, cursed_items=0, light_wings=0)
    summarise("careful, no scans", scan_rate=0.0, cursed_items=0, light_wings=1)
    summarise("baseline (scan 70%)")
    summarise("greedy: 4 cursed, 3 lit", cursed_items=4, light_wings=3)
    summarise("baseline, no levers", use_levers=False)
    summarise("ghost spending 6 Static", ghost_static=6)
    summarise("ghost spending 18 Static", ghost_static=18)

    print("\n\nWHY THE LEVERS NEED A COOLDOWN  -  R17")
    print("Unlimited, the emergency valve gets pulled five times a night and COLLECT never")
    print("happens at all. The top tier exists only if relief is rationed.")
    print("-" * 78)
    print(f"{'baseline, cooldown':<30}{'DORMANT':>9}{'PATROL':>8}{'PURSUE':>8}"
          f"{'COLLECT':>9}{'1st PUR':>10}{'%':>7}{'levers':>8}")
    for cd in (0.0, 60.0, LEVER_COOLDOWN_S, 180.0, 300.0):
        summarise(f"every {cd:.0f}s at most", nights=300, lever_cooldown=cd)

    print("\n\nWHY THE DECAY MOVED  -  R3's finding, now reproducible from this file")
    print("The spec's 1/min is not slow, it is inert: gross gain is ~54/min against a")
    print("100-point scale, so every crew saturates and the meter stops discriminating.")
    print("-" * 78)
    print(f"{'decay/min':<30}{'DORMANT':>9}{'PATROL':>8}{'PURSUE':>8}{'COLLECT':>9}"
          f"{'1st PUR':>10}{'%':>7}{'levers':>8}")
    for dk in (SPEC_DECAY, 5.0, 12.0, 22.0, 35.0, DECAY_PER_MIN, 70.0):
        summarise(f"careful crew @ {dk:.0f}", nights=200, decay=dk,
                  scan_rate=0.0, cursed_items=0, light_wings=1)
