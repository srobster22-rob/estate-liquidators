"""
Estate Liquidators — what the Disturbance levers actually cost.

R18 found that unlimited levers delete the top tier of the game: a baseline crew spends
0% of the night at COLLECT with kill-lights and go-quiet available, against 40% without.
It patched that with a 150s cooldown and said plainly that the cooldown was a placeholder
for a cost the model could not see:

    A lever's real price is TIME. Going quiet means creeping for 45 seconds. Killing the
    lights means hauling in the dark for the rest of the night. `sim/disturbance.py` has
    no haul loop in it, so it charges neither -- which means its crews pulled levers as a
    reflex, for free, and of course the meter never stayed high.

D-26 wrote its own falsification condition: model the time cost properly, and if the
15%-at-COLLECT target falls out with no cooldown at all, delete the cooldown rather than
tuning it. An artificial limit on a choice that was already self-limiting is worse than no
limit, because it stops players ever discovering the real trade.

This file runs that test. The question is not "how strong should the levers be" -- it is
**whether a crew that pays for its levers rations them on its own.**

Run: python sim/levers.py            (stdlib only, ~30s)
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

CREW = TUNING["night"]["crew"]
NIGHT_S = float(TUNING["night"]["seconds"])
HAUL_S = float(TUNING["night"]["haul_window_seconds"])
VAN_SLOTS = TUNING["van"]["base_slots"]

IMPULSE = _LC["impulse_disturbance_per_l"]
SUSTAINED = _LC["sustained_disturbance_per_l"]
DECAY_AT_CREW4 = _D["decay_per_min_at_crew4"]
DECAY_CREW_EXP = _D["decay_crew_exponent"]
RATCHET_END = _D["ratchet_end"]
CURSED_FLOOR = _D["per_cursed_item_floor"]
LIGHT_GAIN = _D["light_wing_gain"]
LEVER_LIGHTS = _D["lever_kill_lights"]
LEVER_QUIET = _D["lever_go_quiet"]
LEVER_COOLDOWN_S = _D["lever_cooldown_seconds"]

RETRIEVAL = {"DORMANT": TUNING["retrieval"]["dormant"],
             "PATROL": TUNING["retrieval"]["patrol"],
             "PURSUE": TUNING["retrieval"]["pursue"],
             "COLLECT": TUNING["retrieval"]["collect"]}
TIERS = [(_D["tier_collect_at"], "COLLECT"), (_D["tier_pursue_at"], "PURSUE"),
         (_D["tier_patrol_at"], "PATROL"), (0.0, "DORMANT")]

PARALLEL_EFFICIENCY = 0.65
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]
TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}

# --------------------------------------------------------------- the real prices
# These are the numbers R18 could not charge. All three are estimates, and they are
# the whole result, so they get swept at the bottom rather than asserted.
QUIET_S = 45.0             # DESIGN 6.5: go quiet for 45 seconds
QUIET_THROUGHPUT = 0.55    # creeping. You are not hauling a chest of drawers at speed.
QUIET_NOISE = 0.35         # and you are much quieter, which is the point
DARK_THROUGHPUT = 0.85     # hauling a lit wing blind for the rest of the night
DARK_BREAKAGE = 2.0        # x multiplier on breaking something in the dark
LIT_THROUGHPUT = 1.15      # what the lights bought you in the first place
BREAK_BASE = 0.04          # per-trip chance of dropping something, lights on


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for start, ti in PHASES:
        if t >= start:
            tier = ti
    return tier


def decay_per_s(crew):
    return DECAY_AT_CREW4 * (crew / 4.0) ** DECAY_CREW_EXP / 60.0


def run_night(seed, policy, cursed=2, cooldown=0.0, light_wings=2,
              scan_rate=0.7, charges=0):
    """One night with levers that cost what they actually cost."""
    rng = random.Random(seed)
    d = t = filled = 0.0
    # CHARGES model the third option: a lever you BOUGHT, carried as cargo. It costs
    # van capacity before the night starts and costs nothing at the moment you pull
    # it. DESIGN 9 already sells salt as gear, so the fiction is in place.
    slots = float(VAN_SLOTS) - charges
    held = []                 # what is actually in the van, so we can swap up
    banked = 0.0
    lights_on = 0
    lights_killed = 0
    quiet_until = -1.0
    last_lever = -1e9
    lever_uses = 0
    at_collect_s = 0.0
    lost = 0

    while t < HAUL_S:
        depth = depth_at(t)
        trip_s, band = TIER_DATA[depth]

        quiet = t < quiet_until
        throughput = 1.0
        if quiet and policy != "CHARGE":
            throughput *= QUIET_THROUGHPUT
        throughput *= LIT_THROUGHPUT ** lights_on
        throughput *= DARK_THROUGHPUT ** lights_killed
        per_trip = trip_s / (CREW * PARALLEL_EFFICIENCY * throughput)

        if filled >= TIER_CAP[depth] * VAN_SLOTS and depth < 3:
            t += per_trip
            continue

        value = rng.uniform(*band)
        # A full van does NOT end the night, and assuming it did was why an earlier
        # cut of this file had every crew finished by minute six with the meter still
        # in PATROL. The van binds by ~40% (ECONOMY 2), so the back half of a night is
        # spent SWAPPING -- hauling a better thing out and leaving a worse thing
        # behind. That is the appraiser's whole reason to exist, and it means the crew
        # is still in the house making noise long after the van is nominally full.
        swapping = slots <= 0
        hush = QUIET_NOISE if quiet else 1.0
        if swapping and (not held or value <= min(held)):
            # Not worth carrying out. You still walked the wing to find that out.
            t += per_trip * 0.6
            continue

        # --- the trip, second by second ---------------------------------
        for _ in range(int(per_trip)):
            floor = RATCHET_END * (t / NIGHT_S) + cursed * CURSED_FLOOR
            for _ in range(CREW):
                if rng.random() < 0.04:
                    d += L["sprint"] * SUSTAINED * hush
                if rng.random() < 0.055 / 4 * hush:
                    d += L["door"] * IMPULSE
                if rng.random() < 0.085 / 4 * scan_rate * hush:
                    d += L["appraise"] * IMPULSE
                if rng.random() < 0.006 / 4:
                    d += L["break_small"] * IMPULSE
            if rng.random() < 0.15:
                d += L["dolly"] * SUSTAINED * hush
            if rng.random() < 0.08:
                d += L["radio"] * SUSTAINED * hush
            # Turning lights ON: a big one-off cost for lasting throughput.
            if (lights_on + lights_killed) < light_wings and t > 60 \
                    and rng.random() < 0.004:
                d += LIGHT_GAIN
                lights_on += 1
            d = max(floor, min(100.0, d - decay_per_s(CREW)))
            if d >= _D["tier_collect_at"]:
                at_collect_s += 1.0
            t += 1.0

        # --- lever decision ---------------------------------------------
        if policy == "CHARGE":
            # Free to use, finite to own. Pull it when it does something -- there is
            # no throughput cost to weigh, only "will I want it more later".
            if charges > 0 and tier_of(d) == "COLLECT":
                charges -= 1
                quiet_until = t + QUIET_S
                d -= LEVER_QUIET
                lever_uses += 1
        elif policy != "NONE" and not quiet and t - last_lever >= cooldown:
            if pull_lever(policy, d, lights_on, depth, band, per_trip):
                if d > 78 and lights_on > 0:
                    d -= LEVER_LIGHTS
                    lights_on -= 1
                    lights_killed += 1
                    lever_uses += 1
                    last_lever = t
                elif d > 70:
                    quiet_until = t + QUIET_S
                    d -= LEVER_QUIET
                    lever_uses += 1
                    last_lever = t

        filled += 1.0
        broke = rng.random() < BREAK_BASE * (DARK_BREAKAGE ** lights_killed)
        taken = rng.random() < RETRIEVAL[tier_of(d)]
        if broke or taken:
            lost += 1
            if not swapping:
                slots -= 1.0                   # the slot is spent either way (R8)
            continue

        if swapping:
            worst = min(held)
            held.remove(worst)
            held.append(value)
            banked += value - worst
        else:
            slots -= 1.0
            held.append(value)
            banked += value

    return banked, at_collect_s / max(t, 1.0), lever_uses, lost


def pull_lever(policy, d, lights_on, depth, band, per_trip):
    """Should the crew spend a lever right now?"""
    if policy == "REFLEX":
        # R18's assumption, and what a free lever produces: pull whenever you can.
        return d > 78 or (d > 70 and lights_on == 0)

    if policy == "ECONOMIC":
        # Pull only when the retrieval you avoid is worth more than the hauling you
        # give up. This is the calculation a good crew makes out loud in a hallway.
        tname = tier_of(d)
        drop = LEVER_LIGHTS if lights_on > 0 else LEVER_QUIET
        after = tier_of(max(0.0, d - drop))
        saved_rate = RETRIEVAL[tname] - RETRIEVAL[after]
        if saved_rate <= 0:
            return False
        item_value = sum(band) / 2
        # Trips inside the window the lever protects.
        trips = QUIET_S / max(per_trip, 1.0)
        benefit = saved_rate * item_value * max(trips, 1.0)
        if lights_on > 0:
            # Killing lights is permanent: cost the whole remaining night.
            cost = item_value * (1 - DARK_THROUGHPUT) * 6
        else:
            cost = item_value * (1 - QUIET_THROUGHPUT) * max(trips, 1.0)
        return benefit > cost

    raise ValueError(policy)


def trial(policy, n=800, **kw):
    res = [run_night(s, policy, **kw) for s in range(n)]
    return {"mean": statistics.mean(r[0] for r in res),
            "collect": statistics.mean(r[1] for r in res),
            "levers": statistics.mean(r[2] for r in res),
            "lost": statistics.mean(r[3] for r in res)}


def table(title, rows):
    print(f"\n{title}")
    print("-" * 78)
    print(f"{'policy':<26}{'mean $':>10}{'%night@COLLECT':>16}{'levers':>9}"
          f"{'lost':>7}")
    for label, kw in rows:
        r = trial(**kw)
        print(f"{label:<26}{r['mean']:>10,.0f}{r['collect']:>16.0%}"
              f"{r['levers']:>9.1f}{r['lost']:>7.1f}")
    return None


if __name__ == "__main__":
    print("WHAT DO THE LEVERS COST? — D-26's falsification test")
    print("=" * 78)
    print("R18 charged levers nothing and they deleted the top tier (0% at COLLECT).")
    print("It patched that with a 150s cooldown and called the cooldown a placeholder.")
    print("Here levers cost throughput: go quiet = 45s at 0.55x, kill lights = 0.85x")
    print("for the rest of the night plus double breakage.")

    table("DOES A CREW THAT PAYS FOR ITS LEVERS RATION THEM?", [
        ("no levers at all", dict(policy="NONE")),
        ("REFLEX, no cooldown", dict(policy="REFLEX", cooldown=0.0)),
        ("REFLEX, 150s cooldown", dict(policy="REFLEX",
                                       cooldown=LEVER_COOLDOWN_S)),
        ("ECONOMIC, no cooldown", dict(policy="ECONOMIC", cooldown=0.0)),
        ("ECONOMIC, 150s cooldown", dict(policy="ECONOMIC",
                                         cooldown=LEVER_COOLDOWN_S)),
    ])
    print("\n  Target from R4 / D-26: baseline sits around 15% of the night at COLLECT.")
    print("  If ECONOMIC-no-cooldown already lands there, the cooldown is an artificial")
    print("  limit on a choice that was self-limiting, and D-26 says delete it.")

    table("GREED — does the answer hold when the floor is higher?", [
        ("ECONOMIC, 0 cursed", dict(policy="ECONOMIC", cursed=0)),
        ("ECONOMIC, 2 cursed", dict(policy="ECONOMIC", cursed=2)),
        ("ECONOMIC, 4 cursed", dict(policy="ECONOMIC", cursed=4)),
        ("ECONOMIC, 5 cursed", dict(policy="ECONOMIC", cursed=5)),
        ("REFLEX,   5 cursed", dict(policy="REFLEX", cursed=5)),
    ])

    print("\n\nSENSITIVITY — the three prices are estimates, so sweep them")
    print("-" * 78)
    print(f"{'quiet throughput':<20}{'%@COLLECT':>12}{'levers':>9}{'mean $':>11}")
    base_q = QUIET_THROUGHPUT
    for q in (0.35, 0.45, 0.55, 0.70, 0.90):
        QUIET_THROUGHPUT = q
        r = trial("ECONOMIC", n=500)
        print(f"{q:<20.2f}{r['collect']:>12.0%}{r['levers']:>9.1f}{r['mean']:>11,.0f}")
    QUIET_THROUGHPUT = base_q

    print(f"\n{'dark throughput':<20}{'%@COLLECT':>12}{'levers':>9}{'mean $':>11}")
    base_d = DARK_THROUGHPUT
    for dk in (0.70, 0.80, 0.85, 0.92, 1.00):
        DARK_THROUGHPUT = dk
        r = trial("ECONOMIC", n=500)
        print(f"{dk:<20.2f}{r['collect']:>12.0%}{r['levers']:>9.1f}{r['mean']:>11,.0f}")
    DARK_THROUGHPUT = base_d

    print("\n\nTHE THIRD OPTION — pay in VAN SLOTS instead of throughput")
    print("=" * 78)
    print("A lever you bought and carried: costs cargo capacity before the night, costs")
    print("nothing at the moment you pull it. Different currency, so the trade is not")
    print("automatically unfavourable. DESIGN 9 already sells salt as gear.")
    print("-" * 78)
    print(f"{'charges carried':<20}{'mean $':>11}{'%@COLLECT':>12}{'used':>8}"
          f"{'vs 0 charges':>14}")
    zero = trial("CHARGE", n=900, charges=0)["mean"]
    for c in (0, 1, 2, 3, 4, 6):
        r = trial("CHARGE", n=900, charges=c)
        print(f"{c:<20}{r['mean']:>11,.0f}{r['collect']:>12.0%}{r['levers']:>8.1f}"
              f"{r['mean'] / zero - 1:>14.1%}")
    print("\n  An interior optimum here means the lever is a real decision made in the")
    print("  lobby -- greed against safety, which is the trade the whole game runs on.")
    print("  A monotone column means it is still the wrong price, just in new units.")
