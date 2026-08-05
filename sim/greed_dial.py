"""
Estate Liquidators — does the greed dial have teeth?

    python3 sim/greed_dial.py

--------------------------------------------------------------------------------
WHY THIS EXISTS (LOOP_LOG R22)

DESIGN 4 calls greed the difficulty slider: "the game never forces danger, it prices
it." Milestone 4's exit criterion is that the greed dial "has teeth". R21 found that
**no model in this repo could check that**, because the two that touch it each model
half the system:

  disturbance.py   has the levers, has no earnings. Going dark and going quiet are
                   therefore free, so its idealised crew pulls a lever the instant it
                   can. The levers fire at 78 and 82, just under COLLECT's 85, which
                   makes COLLECT arithmetically unreachable rather than avoidable —
                   0% COLLECT for every archetype including greedy.
  integrated.py    has earnings, has no levers at all.

So neither could say whether greed is priced or merely decorated. This merges them:
the haul loop and its money, plus the three levers with the costs DESIGN actually
specifies for them.

THE COSTS ARE THE DESIGN'S, NOT INVENTED (DESIGN 6.5 and 9):
  light a wing   +25 Disturbance instantly, and the wing becomes "a huge visibility
                 gain, safe hauling" — modelled as faster trips in that wing.
  kill lights    -15 instantly, and "you hauled that wing lit for a reason; now you're
                 doing it blind" — you lose the speed-up you paid for.
  go quiet       -20 over 45s of "no running, no scanning, no radio, crew-wide" —
                 modelled as slower trips AND no appraising for the duration.
  unload cursed  removes that item's floor contribution, and its value with it.

THE TEST. Greed has teeth if earnings peak at an INTERIOR greed level: pushing the
dial further should eventually cost more than it pays. If earnings rise monotonically
to maximum greed, the dial is decoration and Milestone 4's criterion fails — the same
shape of finding as R10/R11, where a linear curse cost meant "take everything" was
always correct.

THE HONEST UNKNOWN. How much a lit wing is actually worth in hauling speed is a
hands-on tuning value nobody has measured — DESIGN says the joint tuning values are
"deliberately rough". So this does not assert one; it SWEEPS it and reports the
threshold at which the answer flips. That threshold is the number to take into
Milestone 4.

THE R22 DIVERGENCE, RESOLVED (R23).
This model and `scan_risk.py` disagreed about the SHAPE of the scan-rate axis: an
interior optimum at 0.2-0.3 there, monotone to 1.0 here. **Both were measuring the
depth gate, not the appraiser.**

The sims gate depth on a CLOCK (PHASES at t = 0/120/240s). A crew that fills its tier
quota early has to wait for the next tier to open, and scanning burns time, so
scanning gets credited for converting dead time into value. scan_risk has more
absorbable dead time (waits fall 2.00 -> 0.00 across the sweep) and its curve peaks
exactly where that dead time runs out. This model's trips are faster - lit wings
shorten them - so its dead time never runs out inside the range, and the curve just
rises.

Ablate the gate in `scan_risk.py` panel G and the interior peak vanishes: scanning
becomes monotonically valuable, best at 1.0, worth +25.4% instead of +3.5%. Rejected
along the way: that the curse value multiplier was amplifying scanning here
(disabling it left the peak at 1.0), and that the ruin roll was coupling to scan rate
(ruin is flat at ~11% and cursed-aboard is exactly 3.00 at every rate).

The consequence reaches past this file. Clock-gated depth is what **D-20 (FIRM)**
calls a bug - "any future timer-based gate is a bug" - and EVERY sim here still does
it, including this one. Any result whose mechanism runs through crew *time* inherits
the artifact. Building a model that gates depth on WORK, where the prerequisite
consumes crew time productively, is the outstanding job. It reversed D-23.
"""

import json
import math
import os
import pathlib
import random
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

CREW = T["night"]["crew"]
NIGHT_S = T["night"]["seconds"]
HAUL_S = T["night"]["haul_window_seconds"]
VAN_SLOTS = T["van"]["base_slots"]
APPRAISE_S = T["night"]["appraise_seconds"]

IMPULSE = T["loudness_constants"]["impulse_disturbance_per_l"]
SUSTAINED = T["loudness_constants"]["sustained_disturbance_per_l"]
DECAY_PER_MIN = T["disturbance"]["decay_per_min_at_crew4"]
RATCHET_END = T["disturbance"]["ratchet_end"]
FLOOR_PER_CURSED = T["disturbance"]["per_cursed_item_floor"]
LIGHT_GAIN = T["disturbance"]["light_wing_gain"]
KILL_LIGHTS = T["disturbance"]["lever_kill_lights"]
GO_QUIET = T["disturbance"]["lever_go_quiet"]

L = T["loudness"]
RETRIEVAL = {k.upper(): v for k, v in T["retrieval"].items()}
TIERS = [(T["disturbance"]["tier_collect_at"], "COLLECT"),
         (T["disturbance"]["tier_pursue_at"], "PURSUE"),
         (T["disturbance"]["tier_patrol_at"], "PATROL"),
         (0, "DORMANT")]
VALUE_MULT = T["curse"]["value_multiplier"]
LEDGER_FEE = T["curse"]["ledger_fee"]
RUIN_K, RUIN_EXP = T["van"]["ruin_k"], T["van"]["ruin_exp"]

CANDIDATES = 4
PARALLEL_EFFICIENCY = 0.65
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]
TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}
WINGS = 3

QUIET_SLOWDOWN = 1.35      # no running, crew-wide
QUIET_S = 45.0

# How often a crew that has DECIDED to take cursed cargo actually takes a piece when
# one is offered. The first version of this file used 0.35, which was invented rather
# than derived, and it broke the experiment: cursed-aboard saturated at ~4.3 no matter
# how greedy the profile said it was, and 4.3 sits INSIDE the profitable region, so the
# dial could never reach its own teeth. The model reported "greed has no teeth" purely
# because it could not be greedy. At 1.0 it reproduces R11 exactly - peak at two pieces
# (+8.5% against R11's +7%), take-eight loses 32%, take-ten loses 86%. R22.
TAKE_RATE = 1.0


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for start, ti in PHASES:
        if t >= start:
            tier = ti
    return tier


def run_night(seed, greed, lit_speedup=0.80, use_levers=True,
              axis_override=None, n_unused=None):
    """`greed` is 0..4. It moves scan rate, cursed appetite and wings lit together —
    the dial the crew argues about, not three independent knobs.

    `axis_override=(name, value)` pins one axis while the other two stay at `greed`,
    which is how panel D attributes the teeth to a mechanism rather than to the ladder.
    """
    rng = random.Random(seed)
    scan_rate = [0.0, 0.2, 0.4, 0.7, 1.0][greed]
    # The ladder must span PAST the optimum or the sweep cannot find a peak. R11 puts
    # the cursed optimum at two to three pieces, so 'reckless' has to be well beyond it.
    cursed_want = [0, 1, 3, 6, 10][greed]
    wings_want = [0, 1, 2, 3, 3][greed]
    if axis_override:
        name, val = axis_override
        if name == "scan":
            scan_rate = val
        elif name == "cursed":
            cursed_want = val
        elif name == "wings":
            wings_want = val

    d = t = gross = 0.0
    slots = float(VAN_SLOTS)
    filled = 0.0
    cursed_aboard = 0
    wings_lit = 0
    quiet_until = -1.0
    levers = 0
    tier_time = {"DORMANT": 0.0, "PATROL": 0.0, "PURSUE": 0.0, "COLLECT": 0.0}

    while t < HAUL_S and slots > 0:
        tier = depth_at(t)
        trip_s, band = TIER_DATA[tier]
        quiet = t < quiet_until

        # Light a wing: +25 now, faster hauling after. A group argument, per DESIGN 9.
        if wings_lit < wings_want and not quiet and t > 30:
            d = min(100.0, d + LIGHT_GAIN)
            wings_lit += 1

        # A lit wing is "a huge visibility gain, safe hauling". Killing the lights
        # takes that back - that is the whole cost of the lever.
        lit_frac = wings_lit / WINGS
        speed = (1.0 - lit_frac) + lit_frac * lit_speedup
        if quiet:
            speed *= QUIET_SLOWDOWN
        per_trip = trip_s * speed / (CREW * PARALLEL_EFFICIENCY)

        if filled >= TIER_CAP[tier] * VAN_SLOTS and tier < 3:
            t += per_trip
            continue

        candidates = [rng.uniform(*band) for _ in range(CANDIDATES)]
        appraise = (not quiet) and rng.random() < scan_rate     # no scanning while quiet

        cost = per_trip
        if appraise:
            value = max(candidates)
            cost += APPRAISE_S * CANDIDATES / CREW
        else:
            value = rng.choice(candidates)

        take_cursed = cursed_aboard < cursed_want and rng.random() < TAKE_RATE
        grade = "malignant" if take_cursed and rng.random() < 0.35 else (
            "tainted" if take_cursed else "clean")
        value *= VALUE_MULT[grade]

        floor = RATCHET_END * (t / NIGHT_S) + cursed_aboard * FLOOR_PER_CURSED
        hush = 0.35 if quiet else 1.0
        for _ in range(int(cost)):
            for _ in range(CREW):
                if rng.random() < 0.04 * hush:
                    d += L["sprint"] * SUSTAINED
            if rng.random() < 0.15 * hush:
                d += L["dolly"] * SUSTAINED
            if rng.random() < 0.08 * hush:
                d += L["radio"] * SUSTAINED
            if rng.random() < 0.055 * hush:
                d += L["door"] * IMPULSE
            if rng.random() < 0.006:
                d += L["break_small"] * IMPULSE
            d = max(floor, min(100.0, d - DECAY_PER_MIN / 60.0))
            tier_time[tier_of(d)] += 1.0

        if appraise:
            d = min(100.0, d + CANDIDATES * L["appraise"] * IMPULSE)

        # Levers, now with the price DESIGN attaches to them.
        if use_levers and not quiet:
            if d > 78 and wings_lit > 0:
                d = max(floor, d - KILL_LIGHTS)
                wings_lit -= 1          # back to hauling blind
                levers += 1
            elif d > 82:
                quiet_until = t + QUIET_S
                d = max(floor, d - GO_QUIET)
                levers += 1

        t += cost
        if t > HAUL_S:
            break
        filled += 1.0

        if rng.random() < RETRIEVAL[tier_of(d)]:
            slots -= 1.0
            continue

        slots -= 1.0
        gross += value * (1.0 - LEDGER_FEE[grade])
        if grade != "clean":
            cursed_aboard += 1

    # Extraction: the collection reclaims the whole van, super-linearly (R11).
    ruined = cursed_aboard > 0 and rng.random() < min(
        0.95, RUIN_K * cursed_aboard ** RUIN_EXP)
    banked = 0.0 if ruined else gross

    total = sum(tier_time.values()) or 1.0
    return banked, {k: v / total for k, v in tier_time.items()}, levers, ruined


def trial(greed, n=3000, **kw):
    res = [run_night(s, greed, **kw) for s in range(n)]
    vals = [r[0] for r in res]
    m = statistics.mean(vals)
    return {
        "mean": m,
        "se": statistics.stdev(vals) / math.sqrt(n),
        "collect": statistics.mean(r[1]["COLLECT"] for r in res),
        "pursue": statistics.mean(r[1]["PURSUE"] for r in res),
        "levers": statistics.mean(r[2] for r in res),
        "ruin": statistics.mean(r[3] for r in res),
    }


LABELS = ["0 timid", "1 careful", "2 baseline", "3 greedy", "4 reckless"]

if __name__ == "__main__":
    N = int(os.environ.get("GREED_N", 3000))
    print("=" * 78)
    print("DOES THE GREED DIAL HAVE TEETH?")
    print("levers priced as DESIGN 6.5/9 specifies; n =", f"{N:,}")
    print("=" * 78)

    def panel(title, **kw):
        print(f"\n{title}")
        print("-" * 78)
        print(f"{'greed':<12}{'banked $':>10}{'+/-':>7}{'PURSUE':>8}{'COLLECT':>9}"
              f"{'levers':>8}{'ruin':>7}")
        rows = {}
        for g in range(5):
            r = trial(g, n=N, **kw)
            rows[g] = r
            print(f"{LABELS[g]:<12}{r['mean']:>10,.0f}{1.96 * r['se']:>7.0f}"
                  f"{r['pursue']:>8.0%}{r['collect']:>9.0%}"
                  f"{r['levers']:>8.1f}{r['ruin']:>7.1%}")
        best = max(rows, key=lambda g: rows[g]["mean"])
        interior = 0 < best < 4
        print(f"  peak at '{LABELS[best]}' - "
              f"{'INTERIOR: the dial has teeth' if interior else 'CORNER: no teeth'}")
        return best, rows

    best_lev, rows_lev = panel("A. Levers available, priced (the shipping design)")
    best_no, _ = panel("B. Levers unavailable - what the danger looks like unmitigated",
                       use_levers=False)

    print("\n\nC. How good must a lit wing be before lighting up stops being free?")
    print("   lit_speedup 1.00 = lights do nothing; 0.60 = 40% faster hauling")
    print("-" * 78)
    print(f"{'lit_speedup':<13}{'peak greed':>12}{'peak $':>10}{'COLLECT@peak':>14}"
          f"{'shape':>11}")
    flip = None
    for sp in (1.00, 0.95, 0.90, 0.85, 0.80, 0.70, 0.60):
        rows = {g: trial(g, n=max(1200, N // 2), lit_speedup=sp) for g in range(5)}
        best = max(rows, key=lambda g: rows[g]["mean"])
        shape = "interior" if 0 < best < 4 else "corner"
        if shape == "corner" and flip is None and best == 4:
            flip = sp
        print(f"{sp:<13.2f}{LABELS[best]:>12}{rows[best]['mean']:>10,.0f}"
              f"{rows[best]['collect']:>14.0%}{shape:>11}")

    print("\n\nD. WHICH axis actually prices greed? Hold two at baseline, move one.")
    print("-" * 78)
    AXES = {
        "scan rate":   ("scan", [0.0, 0.2, 0.4, 0.7, 1.0]),
        "cursed aboard": ("cursed", [0, 1, 3, 6, 10]),
        "wings lit":   ("wings", [0, 1, 2, 3, 3]),
    }
    for label, (axis, ladder) in AXES.items():
        means = []
        for i in range(5):
            res = [run_night(s, 2, axis_override=(axis, ladder[i]), n_unused=None)
                   for s in range(max(1500, N // 2))]
            means.append(statistics.mean(r[0] for r in res))
        peak = means.index(max(means))
        span = (max(means) - min(means)) / max(means)
        print(f"  {label:<16}" + "".join(f"{m:>9,.0f}" for m in means)
              + f"   peak {peak}  span {span:>5.0%}")
    print("  The axis with the widest span is the one doing the pricing.")

    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    print(f"  With levers priced, earnings peak at '{LABELS[best_lev]}'.")
    print(f"  With levers removed, they peak at '{LABELS[best_no]}'.")
    print(f"  COLLECT is reachable: {rows_lev[4]['collect']:.0%} of the night at "
          f"maximum greed, against R21's 0% when levers were free.")
