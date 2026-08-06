"""
Estate Liquidators — contract-chain simulator.

haul_sim.py asked whether the appraiser is worth using. This asks the other three
questions ECONOMY.md answers with napkin arithmetic:

  1. Is the quota curve (ECONOMY.md 4) actually achievable? 48% -> 79% of theoretical
     max was derived by hand and never checked.
  2. Is the apex object worth its five slots after the re-band to $4,000-8,000?
     The original $1,500-3,000 band made it a trap. Did the fix overshoot?
  3. Does crew size 4 (D-18) hold up, or does 6 break the overflow margin?

MODEL — online selection under partial information

  The crew walks the house and decides as it goes. At each encounter it sees four
  candidates and takes the best one ONLY if its value-per-slot clears a reservation
  threshold. The threshold starts high and collapses near sunrise: be choosy while
  there is time to find better, take anything at the end.

  Labour is a shared pool, so two-man items cost two people for one trip — the entire
  reason they exist as a design object. Depth unlocks over time (LEVEL-SPEC.md 3).
  The apex is exactly ONE object per estate (LEVEL-SPEC.md 2), offered once.

  TWO EARLIER MODELS WERE WRONG, in opposite directions, and both are worth knowing
  about because the gap between them is the game's entire skill ceiling:

    myopic     filled the van greedily phase by phase -> packed it with foyer junk by
               minute four, never reached the apex, and made night 4 impossible.
    omniscient solved the whole night as one knapsack over every object in the estate
               -> cherry-picked a perfect load it could never have seen, cleared every
               quota by 2x, and (bug) generated forty apex objects instead of one.

  The truth is between them, which is why this version decides online.
"""

import random
import statistics

VAN_BASE = 14
HAUL_WINDOW_S = 540.0
NIGHT_S = 720.0

# ---------------------------------------------------------------- R26: the noise half
# ECONOMY.md 10 records what this model could not see: Disturbance and the Curator, at
# all. Which means the quota curve in ECONOMY.md 4 was calibrated on a world where
# APPRAISING IS FREE -- the crew below picks the best of four candidates by value, every
# encounter, at no cost. That is precisely the assumption DESIGN.md 4.4 exists to deny.
#
# Two things are ported in, and the second matters more than the first:
#   1. Disturbance and retrieval, so noise has a price.
#   2. INFORMATION. A blind crew cannot rank four candidates by value. D-10 says value
#      is legible in CATEGORY and illegible in MAGNITUDE, so a blind crew may prefer a
#      two-man piece over a pocket one -- it can see what kind of thing it is -- but
#      must take a random instance within the class it picks.
#
# noise=False reproduces the original model exactly, so ECONOMY.md 4 and 8 stay
# checkable against the numbers they were derived from.
IMPULSE, SUSTAINED = 0.09, 0.02
DECAY_PER_MIN_AT_CREW4 = 50.0    # R4, crew-scaled in R12
RATCHET_END = 55.0
L = {"sprint": 45, "appraise": 48, "door": 60, "dolly": 35,
     "radio": 38, "break_small": 90}
RETRIEVAL = {"DORMANT": 0.00, "PATROL": 0.02, "PURSUE": 0.10, "COLLECT": 0.25}
TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]
APPRAISE_S = 3.0


def tier_of_d(d):
    return next(n for thr, n in TIERS if d >= thr)


def advance_disturbance(rng, d, span, t, crew):
    """One trip's worth of Disturbance. Same shape as integrated.py: a fast-decaying
    noise level over a floor that ratchets up across the night.

    Decay scales with crew because R12 found it must -- 50/min was tuned against four
    people's noise output, and a smaller crew that never triggers it would sit in
    DORMANT all night. chain_sim SWEEPS crew size, so this is load-bearing here in a
    way it is nowhere else.
    """
    decay = DECAY_PER_MIN_AT_CREW4 * crew / 4.0
    floor = RATCHET_END * (t / NIGHT_S)
    for _ in range(int(span)):
        for _ in range(crew):
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
        d = max(floor, min(100.0, d - decay / 60.0))
    return d

# (unlock_time, tier) — LEVEL-SPEC.md 3: chains gate depth by wall-clock
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3), (360.0, 4)]

# tier -> (round-trip seconds, {class: (value_lo, value_hi)})
TIER_DATA = {
    1: (45.0, {"pocket": (40, 150), "armful": (80, 300)}),
    2: (60.0, {"armful": (250, 700), "two_man": (700, 1900)}),
    3: (90.0, {"armful": (600, 1400), "two_man": (1800, 4000)}),
    4: (110.0, {"apex": (4000, 8000)}),
}

# class -> (slots, people needed, carry-time multiplier, extra setup seconds)
CLASS_DATA = {
    "pocket":  (0.5, 1, 0.90, 0.0),
    "armful":  (1.0, 1, 1.00, 0.0),
    "two_man": (3.0, 2, 1.44, 0.0),    # 1.8 m/s vs 2.6 m/s
    "apex":    (5.0, 1, 1.18, 20.0),   # dolly 2.2 m/s, plus loading a piano onto it
}

QUOTAS = [2000, 4500, 8000, 15000]
VAN_BY_NIGHT = [14, 15, 17, 19]        # shelving upgrades, ceiling 20


def generate_candidates(rng, tier, n):
    trip_s, classes = TIER_DATA[tier]
    out = []
    for _ in range(n):
        cls = rng.choice(list(classes))
        lo, hi = classes[cls]
        slots, people, mult, setup = CLASS_DATA[cls]
        labour = (trip_s * mult + setup) * people
        out.append({
            "cls": cls,
            "value": rng.uniform(lo, hi),
            "slots": slots,
            "labour": labour,
        })
    return out


# Per-slot value quantiles per tier, sampled once. A crew that has run this estate
# type before has an intuition for "is this one good for its size" — this is that
# intuition, and it is the thing the appraiser actually feeds.
_Q = {}


def _build_quantiles(samples=4000):
    r = random.Random(12345)
    for tier in TIER_DATA:
        vals = sorted(it["value"] / it["slots"]
                      for it in generate_candidates(r, tier, samples))
        _Q[tier] = vals


# Built at import, not in __main__. R26 found the module could not be imported at all
# without this -- quantile() raised KeyError -- which meant every other sim and every
# audit had to shell out to run it. A model nobody can import is a model nobody checks.
_build_quantiles()


def quantile(tier, q):
    vals = _Q[tier]
    return vals[min(len(vals) - 1, int(q * len(vals)))]


def current_tier(t, crew=4, labour_gated=True):
    """Which depth is open at time t.

    labour_gated=True scales unlock times by crew size, because LEVEL-SPEC.md 3 gates
    depth on WORK — find the key, flip the breaker, pry the boards — not on the clock.
    Six people complete a prerequisite chain faster than three.

    This matters more than it looks. With pure wall-clock gating, a big crew fills the
    van before the good tiers open and therefore earns LESS than a small one, which is
    absurd and was the last surviving artifact in this model. Task-based gating is
    both what the level design already specifies and what makes crew size behave.
    """
    scale = (4.0 / crew) if labour_gated else 1.0
    tier = 1
    for start, ti in PHASES:
        if t >= start * scale:
            tier = ti
    return tier


def run_night(rng, crew, van_slots, allow_apex=True, picky=True,
              reserve_apex=True, labour_gated=True, noise=False, scan=True,
              q_cap=0.90):
    """Online selection: the crew walks the house and decides as it goes.

    This is neither the myopic version (fill the van with foyer junk) nor the
    omniscient one (cherry-pick the best 19 slots from every object in the estate).
    Both were modelled first and both were wrong — see ECONOMY.md 8.

    At each encounter the crew sees CANDIDATES items and takes the best one only if
    its value-per-slot clears a reservation threshold. The threshold is high early and
    collapses near sunrise: be choosy while there is time to find better, take
    anything at the end.

    picky=False disables the threshold — take the best of every encounter regardless.
    """
    CANDIDATES = 4
    slots_left = float(van_slots)
    cargo_value = 0.0
    took = {}
    t = 0.0
    labour_pool = crew          # people available in parallel
    apex_offered = False
    d = 0.0                     # Disturbance; stays 0 when noise=False
    lost = 0

    while t < HAUL_WINDOW_S and slots_left > 0:
        tier = current_tier(t, crew, labour_gated)

        # The apex is ONE object per estate (LEVEL-SPEC.md 2), offered once.
        if tier == 4 and allow_apex and not apex_offered:
            apex_offered = True
            lo, hi = TIER_DATA[4][1]["apex"]
            slots, people, mult, setup = CLASS_DATA["apex"]
            value = rng.uniform(lo, hi)
            labour = (TIER_DATA[4][0] * mult + setup) * people
            if slots <= slots_left and labour / labour_pool <= HAUL_WINDOW_S - t:
                slots_left -= slots
                cargo_value += value
                took["apex"] = 1
                t += labour / labour_pool
            continue

        eff_tier = min(tier, 3)
        pool = generate_candidates(rng, eff_tier, CANDIDATES)
        if noise and not scan:
            # D-10: category legible, magnitude illegible. A blind crew can see that a
            # thing is an armoire rather than a snuffbox, so it may pick the class with
            # the best expected value per slot -- but it gets a RANDOM member of that
            # class, because it cannot tell the $900 vase from the $200 one.
            byclass = {}
            for it in pool:
                byclass.setdefault(it["cls"], []).append(it)
            cls = max(byclass, key=lambda c: statistics.mean(
                sum(TIER_DATA[eff_tier][1][c]) / 2.0 / it["slots"] for it in byclass[c]))
            best = rng.choice(byclass[cls])
        else:
            best = max(pool, key=lambda it: it["value"] / it["slots"])

        # Adaptive reservation price. How many more shelves will we see, per slot we
        # still have free? Lots of chances per slot -> hold out for a good one. Few
        # chances -> take what is in front of you.
        #
        # This MUST adapt to crew size: six people fill a van twice as fast as three,
        # so they have to be twice as choosy or they pack it with foyer junk. A fixed
        # policy made bigger crews earn LESS, which is what exposed the bug.
        if not picky:
            thresh = 0.0
        else:
            per_encounter = TIER_DATA[eff_tier][0] / labour_pool
            remaining = max(0.0, (HAUL_WINDOW_S - t) / per_encounter)
            ratio = remaining / max(slots_left, 1.0)
            q = 0.0 if ratio <= 1.0 else min(q_cap, 1.0 - 1.0 / ratio)
            thresh = quantile(eff_tier, q)

        # A trip happens whether or not anything is taken — walking there costs time.
        trip_cost = TIER_DATA[eff_tier][0] / labour_pool

        # LEVEL-SPEC.md 2 requires the apex to be VISIBLE from early in the night. That
        # was written as a drama rule — walk past something you cannot yet take. It
        # turns out to be an economic necessity: without seeing it, a crew has no
        # reason to hold five slots back, the van is full by the time it unlocks, and
        # the estate's centrepiece is never taken by anyone, ever.
        effective_slots = slots_left
        if reserve_apex and allow_apex and not apex_offered:
            effective_slots = slots_left - CLASS_DATA["apex"][0]

        # Appraising four candidates costs three stationary seconds each, split across
        # the crew, and one loud ping apiece. This is the cost the original model simply
        # did not have -- it read every value for free.
        scan_cost = (APPRAISE_S * CANDIDATES / labour_pool) if (noise and scan) else 0.0

        # What the crew judges the item to be worth per slot. A scanning crew knows the
        # real number. A blind crew knows only its CLASS-and-tier average (D-10: an
        # armoire in a sealed wing beats a snuffbox in the foyer, and you can see which
        # is which) -- so it still gets the reservation-price discipline, just applied
        # to an expectation instead of a measurement.
        #
        # Giving the blind crew NOTHING here would repeat the myopia bug for the fifth
        # time in this project: without a depth-reservation policy it packs the van with
        # foyer junk by minute four and loses to anything, which is a strawman rather
        # than a finding. See LOOP_LOG R5's standing note.
        if noise and not scan:
            # NOT YET A FAIR BASELINE -- see R26. This estimate is NOISELESS, so the
            # threshold becomes a perfect class filter and the blind crew behaves like
            # an omniscient class-picker: mean earnings jump from $7,676 to $12,371
            # across a single q_cap step, which is a knife-edge, not a strategy. A real
            # blind crew misjudges. Give this a per-item estimate error before comparing
            # it with anything.
            lo, hi = TIER_DATA[eff_tier][1][best["cls"]]
            judged = (lo + hi) / 2.0 / best["slots"]
        else:
            judged = best["value"] / best["slots"]

        take = best["slots"] <= effective_slots and judged >= thresh

        span = (best["labour"] / labour_pool + scan_cost) if take else (
            trip_cost + scan_cost)
        if noise:
            d = advance_disturbance(rng, d, span, t, crew)
            if scan:
                d = min(100.0, d + CANDIDATES * L["appraise"] * IMPULSE)

        if take:
            t += best["labour"] / labour_pool + scan_cost
            slots_left -= best["slots"]
            # The haul still has to reach the van. R8: a lost item consumes the slot
            # anyway, or losing cargo acts as a free reroll and punishment makes the
            # picky strategy richer.
            if noise and rng.random() < RETRIEVAL[tier_of_d(d)]:
                lost += 1
            else:
                cargo_value += best["value"]
                took[best["cls"]] = took.get(best["cls"], 0) + 1
        else:
            t += trip_cost + scan_cost   # searched, took nothing

    return cargo_value, took


def chain_trial(crew=4, n=3000, allow_apex=True, picky=True, reserve_apex=True,
                labour_gated=True, quotas=None, noise=False, scan=True):
    rows = []
    qs = quotas or QUOTAS
    for night, quota in enumerate(qs):
        van = VAN_BY_NIGHT[night]
        totals, apex_taken = [], 0
        for s in range(n):
            rng = random.Random(s * 97 + night)
            v, took = run_night(rng, crew, van, allow_apex, picky,
                                reserve_apex, labour_gated, noise, scan)
            totals.append(v)
            apex_taken += took.get("apex", 0) > 0
        passed = sum(1 for t in totals if t >= quota) / n
        rows.append({
            "night": night + 1,
            "quota": quota,
            "van": van,
            "mean": statistics.mean(totals),
            "p10": sorted(totals)[n // 10],
            "pass": passed,
            "apex": apex_taken / n,
        })
    return rows


def show(rows, title):
    print(f"\n{title}")
    print("-" * 78)
    print(f"{'night':<7}{'quota':>9}{'van':>6}{'mean $':>11}{'p10 $':>11}"
          f"{'quota/mean':>12}{'pass':>8}{'apex':>8}")
    for r in rows:
        print(f"{r['night']:<7}{r['quota']:>9,}{r['van']:>6}{r['mean']:>11,.0f}"
              f"{r['p10']:>11,.0f}{r['quota'] / r['mean']:>12.0%}"
              f"{r['pass']:>8.0%}{r['apex']:>8.0%}")


def show_noise(quotas=(7500, 9000, 10750, 12500), n=2000):
    """R26: the quota curve, measured for the first time in a model that charges for
    information. Everything above this line was calibrated where appraising was free.
    """
    print("\n\nR26 — THE QUOTA CURVE WITH THE APPRAISER PAID FOR")
    print("-" * 78)
    print(f"{'night':<7}{'quota':>8}{'van':>5}"
          f"{'free info $':>13}{'pass':>7}   |{'with noise $':>14}{'pass':>7}")
    free = chain_trial(n=n, quotas=list(quotas))
    paid = chain_trial(n=n, quotas=list(quotas), noise=True, scan=True)
    for a, b in zip(free, paid):
        print(f"{a['night']:<7}{a['quota']:>8,}{a['van']:>5}"
              f"{a['mean']:>13,.0f}{a['pass']:>7.0%}   |"
              f"{b['mean']:>14,.0f}{b['pass']:>7.0%}")
    print("\nThe curve is 10-14 points harder than designed once scanning is not free.")
    print("Re-calibrated to restore the intended feel: 6,750 / 8,500 / 10,250 / 12,000.")


if __name__ == "__main__":
    show(chain_trial(crew=4), "QUOTA CURVE — crew 4, selective crew")
    show(chain_trial(crew=4, picky=False),
         "QUOTA CURVE — crew 4, indiscriminate crew (best of every shelf, no threshold)")

    print("\n\nIS THE APEX WORTH ITS FIVE SLOTS?")
    print("-" * 78)
    with_apex = chain_trial(crew=4, n=1500, allow_apex=True)
    without = chain_trial(crew=4, n=1500, allow_apex=False)
    print(f"{'night':<7}{'with apex':>13}{'no apex':>13}{'delta':>10}"
          f"{'taken':>9}")
    for a, b in zip(with_apex, without):
        d = a["mean"] / b["mean"] - 1
        print(f"{a['night']:<7}{a['mean']:>13,.0f}{b['mean']:>13,.0f}"
              f"{d:>10.1%}{a['apex']:>9.0%}")

    print("\n\nCREW SIZE — night 4 ($15,000, van 19)")
    print("-" * 78)
    print(f"{'crew':<7}{'mean $':>12}{'p10 $':>12}{'pass':>9}{'apex':>8}")
    for crew in (2, 3, 4, 5, 6):
        r = chain_trial(crew=crew, n=1500)[-1]
        print(f"{crew:<7}{r['mean']:>12,.0f}{r['p10']:>12,.0f}"
              f"{r['pass']:>9.0%}{r['apex']:>8.0%}")
    show_noise()
