"""
Estate Liquidators — contract-chain simulator.

haul_sim.py asked whether the appraiser is worth using. This asks the other three
questions ECONOMY.md answers with napkin arithmetic:

  1. Is the quota curve (ECONOMY.md 4) actually achievable? 48% -> 79% of theoretical
     max was derived by hand and never checked.
  2. Is the apex object worth its five slots after the re-band to $6,000-11,000?
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

import json as _json
import pathlib as _pathlib

# R21: was a private copy of every tuned constant. See sim/audit.py for why that is
# the project's most repeated failure -- there is nothing to notice when a canonical
# value moves, which is how this very file carried a stale cursed floor for four
# rounds (R16).
TUNING = _json.loads(
    (_pathlib.Path(__file__).resolve().parent.parent / "tuning.json")
    .read_text(encoding="utf-8"))
_D, _V, _C, _N = (TUNING["disturbance"], TUNING["van"], TUNING["curse"],
                  TUNING["night"])
_A, _R, _P = TUNING["attention"], TUNING["retrieval"], TUNING["progression"]

VAN_BASE = 14
HAUL_WINDOW_S = 540.0

# (unlock_time, tier) — LEVEL-SPEC.md 3: chains gate depth by wall-clock
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3), (360.0, 4)]

# tier -> (round-trip seconds, {class: (value_lo, value_hi)})
TIER_DATA = {
    1: (45.0, {"pocket": (40, 150), "armful": (80, 300)}),
    2: (60.0, {"armful": (250, 700), "two_man": (700, 1900)}),
    3: (90.0, {"armful": (600, 1400), "two_man": (1800, 4000)}),
    4: (110.0, {"apex": tuple(_P["apex_band"])}),   # re-banded R20, see below
}

# class -> (slots, people needed, carry-time multiplier, extra setup seconds)
CLASS_DATA = {
    "pocket":  (0.5, 1, 0.90, 0.0),
    "armful":  (1.0, 1, 1.00, 0.0),
    "two_man": (3.0, 2, 1.44, 0.0),    # 1.8 m/s vs 2.6 m/s
    "apex":    (5.0, 1, 1.18, 20.0),   # dolly 2.2 m/s, plus loading a piano onto it
}

# R20. This list was still the ORIGINAL curve that ECONOMY 4 replaced and marked as
# broken -- so this file printed pass rates against a quota curve the project had
# already thrown away. Recalibrated against the corrected model (swap phase in) to
# reproduce the intended 95/73/55/40% shape.
QUOTAS = list(_P["quota_by_night"])
VAN_BY_NIGHT = list(_P["van_by_night"])   # shelving upgrades, ceiling 20
# The pass rates the quota curve was calibrated to reproduce (R20). Printed
# alongside the measured ones so a drifted curve is visible in the output
# rather than only in a diff -- R20 found this file reporting against a quota
# list two rounds dead, and nothing in its output said so.
TARGET_PASS = list(_P["target_pass_rate"])


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
              reserve_apex=True, labour_gated=True):
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
    held = []                   # what is aboard, so a full van can still upgrade
    took = {}
    t = 0.0
    labour_pool = crew          # people available in parallel
    apex_offered = False

    while t < HAUL_WINDOW_S:
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
                held.append({"cls": "apex", "value": value, "slots": slots})
                took["apex"] = 1
                t += labour / labour_pool
            continue

        eff_tier = min(tier, 3)
        pool = generate_candidates(rng, eff_tier, CANDIDATES)
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
            q = 0.0 if ratio <= 1.0 else min(0.90, 1.0 - 1.0 / ratio)
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

        if best["slots"] <= effective_slots and best["value"] / best["slots"] >= thresh:
            t += best["labour"] / labour_pool
            slots_left -= best["slots"]
            cargo_value += best["value"]
            held.append({"cls": best["cls"], "value": best["value"],
                         "slots": best["slots"]})
            took[best["cls"]] = took.get(best["cls"], 0) + 1
        elif slots_left < best["slots"]:
            # R20: a full van does not end the night. The crew keeps working and
            # UPGRADES -- carry a better thing out, leave a worse thing behind.
            # ECONOMY 2 sizes a crew at 20-24 extractions against 14 slots, so most of
            # what a good night does after the halfway mark is swapping, and stopping
            # at slots_left == 0 simply deletes it.
            t += best["labour"] / labour_pool
            gain = _try_upgrade(held, best, slots_left)
            if gain > 0:
                cargo_value += gain
                slots_left = van_slots - sum(h["slots"] for h in held)
                took[best["cls"]] = took.get(best["cls"], 0) + 1
        else:
            t += trip_cost   # searched, took nothing

    return cargo_value, took


def _try_upgrade(held, cand, slots_left):
    """Drop the worst-per-slot cargo until `cand` fits. Returns the value gained.

    Only swaps if it is actually an upgrade -- a crew does not throw a $900 vase out
    of the van to make room for a $200 clock, however much they like the clock.
    """
    if not held:
        return 0.0
    worst_first = sorted(held, key=lambda h: h["value"] / h["slots"])
    freed, dropped, value_lost = slots_left, [], 0.0
    for h in worst_first:
        if freed >= cand["slots"]:
            break
        freed += h["slots"]
        dropped.append(h)
        value_lost += h["value"]
    if freed < cand["slots"] or value_lost >= cand["value"]:
        return 0.0
    for h in dropped:
        held.remove(h)
    held.append({"cls": cand["cls"], "value": cand["value"],
                 "slots": cand["slots"]})
    return cand["value"] - value_lost


def chain_trial(crew=4, n=3000, allow_apex=True, picky=True, reserve_apex=True,
                labour_gated=True, quotas=None):
    rows = []
    qs = quotas or QUOTAS
    for night, quota in enumerate(qs):
        van = VAN_BY_NIGHT[night]
        totals, apex_taken = [], 0
        for s in range(n):
            rng = random.Random(s * 97 + night)
            v, took = run_night(rng, crew, van, allow_apex, picky,
                                reserve_apex, labour_gated)
            totals.append(v)
            apex_taken += took.get("apex", 0) > 0
        passed = sum(1 for t in totals if t >= quota) / n
        rows.append({
            "night": night + 1,
            "quota": quota,
            "van": van,
            "target": TARGET_PASS[night] if night < len(TARGET_PASS) else None,
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
          f"{'quota/mean':>12}{'pass':>8}{'target':>8}{'apex':>8}")
    drifted = []
    for r in rows:
        tgt = r.get("target")
        print(f"{r['night']:<7}{r['quota']:>9,}{r['van']:>6}{r['mean']:>11,.0f}"
              f"{r['p10']:>11,.0f}{r['quota'] / r['mean']:>12.0%}"
              f"{r['pass']:>8.0%}"
              f"{(f'{tgt:.0%}' if tgt is not None else '-'):>8}{r['apex']:>8.0%}")
        if tgt is not None and abs(r["pass"] - tgt) > 0.10:
            drifted.append(r["night"])
    if drifted:
        print(f"  ** night(s) {drifted} are >10 points off their calibration target."
              f" The quota curve or the model has moved.")


if __name__ == "__main__":
    _build_quantiles()
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
