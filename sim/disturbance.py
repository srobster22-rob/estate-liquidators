"""
Estate Liquidators — Disturbance escalation, and what crew size does to it.

DESIGN.md 6.5 defines the pacing spine of the entire game. This file has been through
three rounds and is now on its fourth question.

  R3 found the spine was structurally broken: as originally specced (slow accumulate,
     1/min decay) the meter saturates in under 60s and pins at 100 for the whole night
     for EVERY crew, including one that never scans and carries nothing. Restructured
     to a fast-decaying noise level plus a ratcheting floor.
  R4 tuned the restructured model and locked decay at 50/min.
  R12 found, from the prototype rather than from here, that decay is CREW-DEPENDENT --
     the 50/min was calibrated against four players, and a solo player generates roughly
     a quarter of that, so 50/min swamps everything they do and the meter never leaves
     DORMANT. Scaled as 50 x crew/4.

  R18 (this round) asks the question R12 left open: does `x crew/4` actually produce
     comparable pacing at 1, 2, 3 and 4 players, or does it only fix the direction?

**This file shipped the pre-R4 numbers until R18.** Its default decay was still 1.0/min
and its cursed floor still 3.0, four rounds after both were corrected elsewhere, so
running it printed the broken escalation the project had already rejected -- every crew
in PURSUE at minute 1 and COLLECT at minute 3 -- with nothing to say it was stale. It now
reads tuning.json like everything else.

Run: python sim/disturbance.py
"""

import json
import pathlib
import random
import statistics

TUNING = json.loads(
    (pathlib.Path(__file__).resolve().parent.parent / "tuning.json")
    .read_text(encoding="utf-8"))

_D = TUNING["disturbance"]
_LC = TUNING["loudness_constants"]
L = {k: v for k, v in TUNING["loudness"].items() if not k.startswith("_")}

NIGHT_S = float(TUNING["night"]["seconds"])
DT = 1.0

IMPULSE_PER_L = _LC["impulse_disturbance_per_l"]
SUSTAINED_PER_L = _LC["sustained_disturbance_per_l"]
DECAY_AT_CREW4 = _D["decay_per_min_at_crew4"]
RATCHET_END = _D["ratchet_end"]
CURSED_FLOOR = _D["per_cursed_item_floor"]
LIGHT_GAIN = _D["light_wing_gain"]
LEVER_LIGHTS = _D["lever_kill_lights"]
LEVER_QUIET = _D["lever_go_quiet"]
LEVER_COOLDOWN_S = _D["lever_cooldown_seconds"]

TIERS = [(_D["tier_collect_at"], "COLLECT"), (_D["tier_pursue_at"], "PURSUE"),
         (_D["tier_patrol_at"], "PATROL"), (0.0, "DORMANT")]

# How decay scales with crew. R12 set this to 1.0 (strictly linear in crew/4).
# R18 swept it and 1.0 is right -- but for a reason R12 did not state. See the bottom.
DECAY_CREW_EXP = _D.get("decay_crew_exponent", 1.0)


def tier_of(d):
    return next(name for thr, name in TIERS if d >= thr)


def decay_for(crew):
    return DECAY_AT_CREW4 * (crew / 4.0) ** DECAY_CREW_EXP


def run_night(seed=0, crew=4, scan_rate=0.7, use_levers=True, ghost_static=0,
              cursed_items=2, light_wings=2, decay=None):
    """One night. Returns (curve, first_pursue_t, first_collect_t, lever_uses)."""
    rng = random.Random(seed)
    decay = decay_for(crew) if decay is None else decay
    d = 0.0
    curve = []
    first_pursue = first_collect = None
    quiet_until = -1.0
    lever_uses = 0
    lights_on = 0
    last_lever = -1e9

    static_times = sorted(rng.uniform(180, NIGHT_S) for _ in range(ghost_static))
    si = 0

    t = 0.0
    while t < NIGHT_S:
        quiet = t < quiet_until
        hush = 0.35 if quiet else 1.0

        # The ratcheting floor. Climbs across the night and is raised by cursed cargo
        # in the van. Neither part scales with crew -- one cursed vase is as loud in
        # a solo van as in a four-player one, and that asymmetry is the whole finding
        # at the bottom of this file.
        floor = RATCHET_END * (t / NIGHT_S) + cursed_items * CURSED_FLOOR

        # WALKING IS FREE. AUDIO-SPEC 1.2's table gives walk no Disturbance value,
        # even though the general L x 0.02/s constant would imply 0.4/s. Charging for
        # it means the meter only ever goes up.

        # --- sources that scale with crew: more people, more of everything ---
        for _ in range(crew):
            if rng.random() < 0.04:                       # sprinting right now
                d += L["sprint"] * SUSTAINED_PER_L * hush
            if rng.random() < 0.085 / 4 * scan_rate * hush:
                d += L["appraise"] * IMPULSE_PER_L
            if rng.random() < 0.055 / 4 * hush:
                d += L["door"] * IMPULSE_PER_L
            if rng.random() < 0.006 / 4:
                d += L["break_small"] * IMPULSE_PER_L
            if rng.random() < 0.0005 / 4:
                d += L["break_large"] * IMPULSE_PER_L

        # --- sources that do NOT scale: one dolly, one radio channel, one house ---
        # A solo player still pushes the dolly and still keys the radio.
        if rng.random() < 0.15:
            d += L["dolly"] * SUSTAINED_PER_L * hush
        if rng.random() < 0.08:
            d += L["radio"] * SUSTAINED_PER_L * hush
        if lights_on < light_wings and t > 60 and rng.random() < 0.004:
            d += LIGHT_GAIN
            lights_on += 1

        while si < len(static_times) and t >= static_times[si]:
            d += 1.0
            si += 1

        d -= (decay / 60.0) * DT
        d = max(floor, min(100.0, d))

        # The cooldown is R18's correction. Without it the levers are free and
        # unlimited, and a crew simply spends one every time the meter approaches
        # COLLECT -- which deletes the top tier of the game outright (0% of the
        # baseline night at COLLECT with levers, 40% without).
        if (use_levers and not quiet
                and t - last_lever >= LEVER_COOLDOWN_S):
            if d > 78 and lights_on > 0:
                d -= LEVER_LIGHTS
                lights_on -= 1
                lever_uses += 1
                last_lever = t
            elif d > 82:
                quiet_until = t + 45.0
                d -= LEVER_QUIET
                lever_uses += 1
                last_lever = t

        if first_pursue is None and d >= _D["tier_pursue_at"]:
            first_pursue = t
        if first_collect is None and d >= _D["tier_collect_at"]:
            first_collect = t

        curve.append(d)
        t += DT

    return curve, first_pursue, first_collect, lever_uses


def stats(n=300, **kw):
    P, C, ends, levers, collect_share, pursue_share = [], [], [], [], [], []
    for s in range(n):
        curve, p, c, lv = run_night(seed=s, **kw)
        P.append(p if p is not None else NIGHT_S)
        C.append(c if c is not None else NIGHT_S)
        ends.append(curve[-1])
        levers.append(lv)
        collect_share.append(sum(1 for x in curve if x >= _D["tier_collect_at"])
                             / len(curve))
        pursue_share.append(sum(1 for x in curve if x >= _D["tier_pursue_at"])
                            / len(curve))
    return {
        "pursue_min": statistics.median(P) / 60,
        "pursue_rate": sum(1 for x in P if x < NIGHT_S) / len(P),
        "collect_min": statistics.median(C) / 60,
        "collect_rate": sum(1 for x in C if x < NIGHT_S) / len(C),
        "end": statistics.mean(ends),
        "levers": statistics.mean(levers),
        "in_collect": statistics.mean(collect_share),
        "in_pursue": statistics.mean(pursue_share),
    }


def row(label, **kw):
    r = stats(**kw)
    print(f"{label:<30}{r['pursue_min']:>7.1f}{r['pursue_rate']:>7.0%}"
          f"{r['collect_min']:>9.1f}{r['collect_rate']:>7.0%}"
          f"{r['in_pursue']:>10.0%}{r['in_collect']:>10.0%}{r['end']:>7.0f}")
    return r


HEAD = (f"{'scenario':<30}{'PURSUE':>7}{'%':>7}{'COLLECT':>9}{'%':>7}"
        f"{'%night>=P':>10}{'%night>=C':>10}{'end D':>7}")

if __name__ == "__main__":
    print("A NIGHT'S ESCALATION  (medians in minutes; 12-min night)")
    print("-" * 87)
    print(HEAD)
    row("baseline (scan 70%, levers)")
    row("no levers", use_levers=False)
    row("greedy: 4 cursed, 3 lit", cursed_items=4, light_wings=3)
    row("careful: no scans, 0 cursed", scan_rate=0.0, cursed_items=0, light_wings=1)
    row("ghost spending 18 Static", ghost_static=18)

    print("\n\nCREW SIZE — the question R12 left open")
    print("-" * 87)
    print(f"decay = {DECAY_AT_CREW4} x (crew/4)^{DECAY_CREW_EXP}")
    print(HEAD)
    for c in (1, 2, 3, 4):
        row(f"crew {c}  (decay {decay_for(c):.0f}/min)", crew=c)

    print("\n  Near-identical across 1-4 players, which is the answer to R12's open")
    print("  question. The crew dependency was never in the DECAY -- it was in whether")
    print("  the noise SOURCES scale per-player. Once doors, scans and breakage scale")
    print("  with headcount, linear decay scaling is already correct and the exponent")
    print("  sweep below is flat. Solo runs a little hotter (29% vs 18% at COLLECT)")
    print("  because the floor and the dolly/radio sources do not scale at all.")
    print("\n  NOTE: R4 recorded baseline first-PURSUE at 5.8 min. That was measured on")
    print("  a model with NO ratcheting floor, which is a different system; with the")
    print("  floor in, it is 3.1 min. Carry the COLLECT share forward as the target,")
    print("  not the PURSUE time.")

    print("\n\nWHERE THE FLOOR TOPS OUT — the fifth cursed item")
    print("-" * 87)
    print("The floor is ratchet_end + cursed x per_cursed_floor, and it does not decay.")
    print("Three constants tuned in separate rounds decide whether a crew can be PINNED")
    print("at COLLECT rather than merely visiting it:")
    for n in range(0, 7):
        fl = RATCHET_END + n * CURSED_FLOOR
        mark = "  <- pinned at COLLECT for the rest of the night" if fl >= _D["tier_collect_at"] else ""
        print(f"    {n} cursed aboard: floor tops at {fl:5.1f}{mark}")
    print(f"  COLLECT is {_D['tier_collect_at']:.0f}. The crossing sits between 4 and 5 cursed items,")
    print("  and ECONOMY 5 independently puts the curse ruin optimum at 2-3 aboard with")
    print("  5+ losing ~40%. The greed that ruins your van is the same greed that pins")
    print("  the monster on you. Neither number was tuned with the other in view.")

    print("\n\nSWEEP: how should decay scale with crew?")
    print("-" * 87)
    print("exp 1.0 is R12's linear scaling. LOWER exponent = MORE decay for small crews,")
    print("because (crew/4)^exp rises toward 1 as exp falls. Flattest column wins.")
    print(f"{'exponent':<10}" + "".join(f"{'crew ' + str(c):>18}" for c in (1, 2, 3, 4)))
    print(f"{'':<10}" + "".join(f"{'PURSUE  %@COLLECT':>18}" for _ in range(4)))
    base = DECAY_CREW_EXP
    for exp in (0.0, 0.4, 0.6, 0.8, 1.0):
        DECAY_CREW_EXP = exp
        cells = ""
        for c in (1, 2, 3, 4):
            r = stats(n=150, crew=c)
            cells += f"{r['pursue_min']:>10.1f}{r['in_collect']:>8.0%}"
        print(f"{exp:<10.1f}{cells}")
    DECAY_CREW_EXP = base
