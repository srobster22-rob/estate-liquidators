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
CANDIDATES = 4

# R33: how crew throughput scales with headcount. Every model in this project previously
# assumed perfect parallelism -- N people do N times the work -- and R32 showed that is
# what produced "+12% from four to six" (it is really +105% under that assumption, and
# +17% at 0.75). The form is anchored at crew 4 so nothing about the four-player results
# moves; only the SCALING changes, which is the part that was never modelled.
#
#     effort(crew) = 4 * (crew/4) ** PARALLEL_EXPONENT
#
# The exponent is UNMEASURED and is the project's biggest open number. See tuning.json.
PARALLEL_EXPONENT = 0.75


def crew_effort(crew):
    return 4.0 * (crew / 4.0) ** PARALLEL_EXPONENT

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


def advance_disturbance(rng, d, span, t, crew, cursed=0):
    """One trip's worth of Disturbance. Same shape as integrated.py: a fast-decaying
    noise level over a floor that ratchets up across the night.

    Decay scales with crew because R12 found it must -- 50/min was tuned against four
    people's noise output, and a smaller crew that never triggers it would sit in
    DORMANT all night. chain_sim SWEEPS crew size, so this is load-bearing here in a
    way it is nowhere else.
    """
    decay = DECAY_PER_MIN_AT_CREW4 * crew / 4.0
    floor = RATCHET_END * (t / NIGHT_S) + cursed * PER_CURSED_FLOOR
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

# (unlock_time, tier) — the ORIGINAL wall-clock schedule, kept as the default so every
# published result stays reproducible.
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3), (360.0, 4)]

# R37: D-20 for real. LEVEL-SPEC.md 3 gates depth on completed PREREQUISITE STEPS -- find
# the key, flip the breaker, pry the boards -- at 1 / 2 / 3 steps for tiers 2 / 3 / 4.
# A step costs labour from the same pool the hauling draws on, so depth is bought with
# time the crew could have spent carrying things, which is the trade the design intends
# and the clock schedule silently gave away for free (R36).
#
# TASK_SECONDS matches sim/validate_estate.py, where it is documented as "rough cost of
# one prerequisite step FOR A CREW OF 4" -- i.e. 75 seconds of wall clock at four people,
# which is 300 labour-seconds. Dividing 75 by the labour pool instead made a step cost 19
# seconds, a crew bought the whole house in under a minute, and the design's shallow-then-
# deep arc vanished entirely.
TASK_SECONDS = 75.0
TASK_LABOUR = TASK_SECONDS * 4.0
PREREQ_STEPS = {2: 1, 3: 2, 4: 3}

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


# ------------------------------------------------------------------ R28: the curse
# R27 established that the appraiser's VALUE half is worth roughly nothing against a
# night's total, and that its real defence must be the other half -- the grade. That
# had never been measured in a model containing the apex, the classes and the noise,
# because this model had no curses in it at all.
#
# The asymmetry is the whole point, and it is sharper than the value one: a blind crew
# does not merely choose worse, it CANNOT EXECUTE THE POLICY. R11 found the optimum is
# "take two or three cursed pieces, then refuse" -- and refusing requires knowing which
# ones they are. A blind crew takes the base rate and rides whatever ruin roll it gets.
GRADE_P = [("clean", 0.70), ("tainted", 0.22), ("malignant", 0.08)]
VALUE_MULT = {"clean": 1.0, "tainted": 2.5, "malignant": 6.0}
ATTENTION_MULT = {"clean": 1.0, "tainted": 1.5, "malignant": 3.0}
LEDGER_FEE = {"clean": 0.0, "tainted": 0.08, "malignant": 0.20}
PER_CURSED_FLOOR = 7.0          # R9/R18
RUIN_K, RUIN_EXP = 0.015, 1.8   # R11


def _grade(rng):
    r, acc = rng.random(), 0.0
    for g, prob in GRADE_P:
        acc += prob
        if r < acc:
            return g
    return "clean"


# ------------------------------------------------------------------ R29: rooms
# The gap every model in this project has been partial around. `appraiser_variance`
# has rooms and spread but no apex, no classes and no curses; `chain_sim` has all of
# those and no rooms -- so it could only ever ask "appraise every shelf or none",
# which is exactly the binary framing R6, R16 and R28 each found hides the answer.
#
# R17 established that scanning's payoff is 0.6 x the room's value spread and nothing
# else, and that the good policy is therefore SELECTIVE. R28 then found the appraiser
# inverts across the contract chain because scanning pins Disturbance at COLLECT. Those
# two findings point at the same fix and neither model could test it: scan only the
# rooms worth scanning, and pay the noise only there.
#
# Mix and factors are LEVEL-SPEC 2.1 / V11, mean exactly 1.0 by construction, so a
# room-bearing estate holds no more money than a flat one -- only a decision.
SPREAD_F = {"uniform": 0.3, "mixed": 1.0, "curio": 1.7}
SPREAD_MIX = [("uniform", 0.25), ("mixed", 0.50), ("curio", 0.25)]


# ------------------------------------------------------------------ R34: a finite estate
# Every model in this project has drawn candidates from an INFINITE shelf: each encounter
# generates four fresh objects forever, so a crew that searches twice as fast simply sees
# twice as much house. That is why headcount scaled without limit (R33) -- extra search
# time buys higher value per slot, and nothing ever runs out.
#
# A real estate does not work that way. LEVEL-SPEC 1 is CORE + 3-5 WINGS at ~5 plinths
# each, so an estate holds roughly 25-30 takeable objects; proto/index.html ships 29. Once
# the crew has walked past a shelf, it is walked past.
ESTATE_OBJECTS = 28
TIER_SHARE = {1: 0.40, 2: 0.30, 3: 0.30}


def build_estate(rng, curses, rooms, n=None):
    """One estate's worth of objects, drawn once and then consumed.

    `n` defaults to the module global rather than binding it at definition time -- a
    default argument is evaluated once at import, so `n=ESTATE_OBJECTS` silently ignored
    every sweep of that constant and printed seven identical rows.
    """
    if n is None:
        n = ESTATE_OBJECTS
    pools = {}
    for tier, share in TIER_SHARE.items():
        room = draw_room(rng) if rooms else None
        count = max(CANDIDATES, int(round(n * share)))
        pools[tier] = generate_candidates(rng, tier, count, curses, room)
        if rooms:                       # re-roll the room per shelf, not per tier
            for i in range(0, len(pools[tier]), CANDIDATES):
                r2 = draw_room(rng)
                for it in pools[tier][i:i + CANDIDATES]:
                    it["room"] = r2
    return pools


def draw_room(rng):
    r, acc = rng.random(), 0.0
    for name, prob in SPREAD_MIX:
        acc += prob
        if r < acc:
            return name
    return "mixed"


def generate_candidates(rng, tier, n, curses=False, spread=None):
    trip_s, classes = TIER_DATA[tier]
    f = SPREAD_F[spread] if spread else None
    out = []
    for _ in range(n):
        cls = rng.choice(list(classes))
        lo, hi = classes[cls]
        slots, people, mult, setup = CLASS_DATA[cls]
        labour = (trip_s * mult + setup) * people
        g = _grade(rng) if curses else "clean"
        if f is None:
            base = rng.uniform(lo, hi)
        else:
            m, w = (lo + hi) / 2.0, (hi - lo) / 2.0
            h = min(f * w, m)          # clamp: no object is ever worth less than zero
            base = rng.uniform(m - h, m + h)
        out.append({
            "cls": cls,
            "value": base * VALUE_MULT[g],
            "slots": slots,
            "labour": labour,
            "grade": g,
        })
    return out


# R27: a trip is a budget too, and per-slot ranking ignores it. A pocket item costs
# half a slot but a WHOLE TRIP, and R24 established the crew runs out of trips at ~21
# against 14 slots -- so small objects are systematically overvalued by value/slots.
# Charging each candidate a fixed slot-equivalent for the trip it consumes fixes the
# ranking and stays precomputable, which the obvious state-dependent version does not.
#   14 slots / 21 trips = 0.667 slots per trip
TRIP_SLOT_EQUIV = 14.0 / 21.0


def cost_of(item, metric="per_slot"):
    if metric == "per_trip":
        return item["slots"] + TRIP_SLOT_EQUIV
    return item["slots"]


# Per-slot value quantiles per tier, sampled once. A crew that has run this estate
# type before has an intuition for "is this one good for its size" — this is that
# intuition, and it is the thing the appraiser actually feeds.
_Q = {}


def _build_quantiles(samples=4000):
    r = random.Random(12345)
    for metric in ("per_slot", "per_trip"):
        for tier in TIER_DATA:
            vals = sorted(it["value"] / cost_of(it, metric)
                          for it in generate_candidates(r, tier, samples))
            _Q[(metric, tier)] = vals


# Built at import, not in __main__. R26 found the module could not be imported at all
# without this -- quantile() raised KeyError -- which meant every other sim and every
# audit had to shell out to run it. A model nobody can import is a model nobody checks.
_build_quantiles()


def quantile(tier, q, metric="per_slot"):
    vals = _Q[(metric, tier)]
    return vals[min(len(vals) - 1, int(q * len(vals)))]


def current_tier(t, crew=4, labour_gated=True):
    """Which depth is open at time t.

    labour_gated=True scales unlock times by crew size, because LEVEL-SPEC.md 3 gates
    depth on WORK — find the key, flip the breaker, pry the boards — not on the clock.
    Six people complete a prerequisite chain faster than three.

    **R36: this does NOT actually implement D-20, and the gap is load-bearing.** The
    unlock is a function of `t` alone, scaled by crew — it never checks that any
    prerequisite work was done. So a crew that refuses every object and idles still gets
    depth handed to it on schedule. That is wall-clock gating with a crew multiplier, and
    D-20 / LEVEL-SPEC 3 both require gating on completed tasks. Any policy that trades
    shallow loot for depth is over-rewarded here, which is exactly what `global_bar`
    exposed.

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


def tier_from_work(steps_done):
    """R37: depth as a function of prerequisite steps COMPLETED, per D-20.

    The property the clock version could not have: a crew that does no work never gets
    deeper. Asserted in `_assert_work_gating()` below, because a gate nobody tests is a
    gate that quietly turns back into a clock.
    """
    tier = 1
    for ti, need in sorted(PREREQ_STEPS.items()):
        if steps_done >= need:
            tier = ti
    return tier


def run_night(rng, crew, van_slots, allow_apex=True, picky=True,
              reserve_apex=True, labour_gated=True, noise=False, scan=True,
              q_cap=0.90, depth_cap=False, metric="per_slot",
              rule="value", curses=False, cursed_cap=3, rooms=False,
              scan_rooms=("uniform", "mixed", "curio"), finite_estate=False,
              global_bar=False, work_gated=False):
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
    slots_left = float(van_slots)
    cargo_value = 0.0
    took = {}
    t = 0.0
    labour_pool = crew_effort(crew)   # R33: sublinear, anchored at crew 4
    apex_offered = False
    estate = build_estate(rng, curses, rooms) if finite_estate else None
    steps_done = 0
    d = 0.0                     # Disturbance; stays 0 when noise=False
    lost = 0
    cursed_aboard = 0
    fees = 0.0

    while t < HAUL_WINDOW_S and slots_left > 0:
        tier = tier_from_work(steps_done) if work_gated else current_tier(
            t, crew, labour_gated)

        # R37: buy the next depth with labour. The crew works a prerequisite step when it
        # no longer wants what is in front of it -- the current tier is picked clean, or
        # its depth budget here is spent. That is the trade D-20 describes and the clock
        # schedule gave away: every step is time not spent carrying.
        if work_gated and tier < 4:
            # When to stop looting here and go open the next door. This uses the same
            # 40% / 75% depth schedule as `depth_cap`, but it is a DIFFERENT decision --
            # depth_cap governs whether to refuse loot, this governs whether to spend
            # labour on a prerequisite -- so it must not be conditioned on that flag.
            # It was, at first, and a crew with depth_cap off never did any prerequisite
            # work at all and spent the whole night in the foyer earning $2,500.
            spent_here = van_slots - slots_left
            budget = {1: 0.40, 2: 0.75, 3: 1.00}[min(tier, 3)]
            want_deeper = (
                (estate is not None and not estate.get(min(tier, 3)))
                or spent_here >= budget * van_slots
                # Holding five slots for an apex you have not unlocked yet is a deadlock:
                # the reserve stops you filling the van, so the depth budget never trips,
                # so you never buy the door, so the reserve is never spent. Go and open
                # it. Without this the crew reached tier 3 and stopped, and never earned
                # the apex at all -- which is ~$6,000 of a ~$12,000 night.
                or (reserve_apex and allow_apex and not apex_offered))
            if want_deeper:
                t += TASK_LABOUR / labour_pool
                steps_done += 1
                continue

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

        # R27: an EXPLICIT depth reservation, held separately from the value threshold.
        # chain_sim's reservation price conflates two different decisions -- "is this a
        # good one for its size" and "should I be spending slots at this depth at all"
        # -- and the blind crew was accidentally getting the second one right, because
        # its class average sits below the tier-1 threshold so it skips the shallow
        # tiers wholesale. The scanning crew, seeing that some individual foyer objects
        # clear the bar, took them and filled slots it should have saved. That is not
        # information being harmful; it is a policy that never separated the two.
        # Sixth occurrence of LOOP_LOG R5's standing note, and the first time it has
        # appeared as a confound between two strategies rather than in one of them.
        if depth_cap:
            spent = van_slots - slots_left
            if eff_tier < 3 and spent >= {1: 0.40, 2: 0.75}[eff_tier] * van_slots:
                t += TIER_DATA[eff_tier][0] / labour_pool
                continue

        if estate is not None:
            # A shelf you have walked past is walked past. When a tier is picked clean
            # the crew moves on; when the whole estate is, the night is over even if
            # there is time and van left -- which is the thing an infinite shelf could
            # never model, and the reason headcount used to scale without limit.
            avail = estate[eff_tier]
            if not avail:
                # Picked clean at this depth. Do NOT end the night just because tiers
                # 1-3 are empty -- the apex is a tier-4 object of its own and may still
                # be waiting. Ending early here dropped the apex take rate to 1% at some
                # estate sizes and 100% at others, which is what made blind earnings
                # non-monotone in estate size and nearly produced a confident wrong
                # design recommendation.
                if all(not v for v in estate.values()) and (apex_offered or not allow_apex):
                    break
                t += TIER_DATA[eff_tier][0] / labour_pool
                continue
            pool = avail[:CANDIDATES]
            del avail[:CANDIDATES]
            room = pool[0].get("room") if rooms else None
        else:
            room = draw_room(rng) if rooms else None
            pool = generate_candidates(rng, eff_tier, CANDIDATES, curses, room)

        # R29: the appraiser becomes a per-room decision. `scan` is now "can this crew
        # appraise at all"; `scan_rooms` is which rooms it judges worth the noise.
        here = scan and (room is None or room in scan_rooms)
        if noise and not here:
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
            best = max(pool, key=lambda it: it["value"] / cost_of(it, metric))

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
            # R36: the reservation bar is TIER-RELATIVE, which means a crew never
            # refuses an object for being shallow -- only for being poor *for its
            # depth*. Standing in the foyer it compares foyer objects against foyer
            # quantiles and takes them, and the depth cap (40% of the van at tier 1) is
            # the only thing restraining it. That is the myopia family again, seventh
            # occurrence, and the first time it has been in the THRESHOLD rather than in
            # a missing cap.
            #
            # global_bar=True judges every object against the deepest tier's bar. It
            # makes blind earnings monotone in estate size, which fixes R35's anomaly --
            # but see the caution in R36: it also earns 1.7x and clears every quota,
            # which is NOT a clean result, because this model does not implement D-20.
            thresh = quantile(3 if global_bar else eff_tier, q, metric)

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
        scan_cost = (APPRAISE_S * CANDIDATES / labour_pool) if (noise and here) else 0.0

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
        # R27: `rule` selects WHICH DECISION RULE the crew uses, and it turned out to
        # matter far more than the information does.
        #
        #   "value" -- the original: rank candidates by value per unit cost, accept if
        #             above the reservation price. Reproduces ECONOMY 4 and 8 exactly.
        #   "class" -- filter on the CLASS's expected value per unit cost first, then
        #             choose within the survivors.
        #
        # The isolation experiment needs "class", because under "value" the two crews
        # were not differing in information at all -- the blind crew was filtering on
        # class and the scanning crew on value, i.e. two different rules, and the gap
        # between them was being read as the appraiser's worth. It was not. "Refuse
        # pockets" is worth +45% and is a class-level policy that NO threshold on
        # value-per-slot can express, because pocket and armful per-slot distributions
        # almost entirely overlap.
        if rule == "class":
            allowed = [it for it in pool
                       if sum(TIER_DATA[eff_tier][1][it["cls"]]) / 2.0
                       / cost_of(it, metric) >= thresh]
            if not allowed:
                span = trip_cost + (APPRAISE_S * CANDIDATES / labour_pool
                                    if (noise and here) else 0.0)
                if noise:
                    d = advance_disturbance(rng, d, span, t, crew, cursed_aboard)
                t += span
                continue
            if noise and not here:
                best = rng.choice(allowed)
            else:
                # R11's optimum is "take two or three cursed pieces, then refuse", and
                # refusing requires knowing which ones they are. Only a scanning crew
                # can even express this policy -- which is the appraiser's other half.
                pick = allowed
                if curses and cursed_aboard >= cursed_cap:
                    pick = [it for it in allowed if it["grade"] == "clean"] or allowed
                best = max(pick, key=lambda it: it["value"] / cost_of(it, metric))
            take = best["slots"] <= effective_slots
        else:
            if noise and not here:
                lo, hi = TIER_DATA[eff_tier][1][best["cls"]]
                judged = (lo + hi) / 2.0 / cost_of(best, metric)
            else:
                judged = best["value"] / cost_of(best, metric)
            take = best["slots"] <= effective_slots and judged >= thresh

        span = (best["labour"] / labour_pool + scan_cost) if take else (
            trip_cost + scan_cost)
        if noise:
            d = advance_disturbance(rng, d, span, t, crew, cursed_aboard)
            if here:
                d = min(100.0, d + CANDIDATES * L["appraise"] * IMPULSE)

        if take:
            t += best["labour"] / labour_pool + scan_cost
            slots_left -= best["slots"]
            # The haul still has to reach the van. R8: a lost item consumes the slot
            # anyway, or losing cargo acts as a free reroll and punishment makes the
            # picky strategy richer.
            risk = RETRIEVAL[tier_of_d(d)] * (
                1.0 + 0.25 * (ATTENTION_MULT[best["grade"]] - 1.0))
            if noise and rng.random() < risk:
                lost += 1
            else:
                cargo_value += best["value"]
                fees += best["value"] * LEDGER_FEE[best["grade"]]
                if best["grade"] != "clean":
                    cursed_aboard += 1
                took[best["cls"]] = took.get(best["cls"], 0) + 1
        else:
            t += trip_cost + scan_cost   # searched, took nothing

    # The collection reclaims the whole van (D-23 / DESIGN 4.2), super-linear in how
    # many cursed pieces are aboard. This is the cost a blind crew cannot manage.
    net = cargo_value - fees
    if curses and cursed_aboard > 0:
        if rng.random() < min(0.95, RUIN_K * cursed_aboard ** RUIN_EXP):
            net = 0.0
    took["cursed"] = cursed_aboard
    took["lost"] = lost
    took["endD"] = round(d)
    return net, took


def chain_trial(crew=4, n=3000, allow_apex=True, picky=True, reserve_apex=True,
                labour_gated=True, quotas=None, noise=False, scan=True, **kw):
    rows = []
    qs = quotas or QUOTAS
    for night, quota in enumerate(qs):
        van = VAN_BY_NIGHT[night]
        totals, apex_taken = [], 0
        for s in range(n):
            rng = random.Random(s * 97 + night)
            v, took = run_night(rng, crew, van, allow_apex, picky,
                                reserve_apex, labour_gated, noise, scan, **kw)
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


def _assert_work_gating(n=400):
    """R37: the property D-20 asserts and the clock schedule could never have.

    A crew that never takes anything and never works a prerequisite must never get
    deeper than tier 1. Under the wall-clock gate it reaches tier 4 by simply existing,
    which is how the model spent thirty rounds over-rewarding every policy that traded
    shallow loot for depth (R36).
    """
    print("\n\nR37 — DOES DEPTH COST ANYTHING?")
    print("-" * 78)
    for label, kw in (("wall-clock gate (default)", {}),
                      ("work gate (D-20)", dict(work_gated=True))):
        deepest = 0
        for s in range(n):
            rng = random.Random(s * 97)
            # A crew that refuses everything: no hauling, and with depth_cap off it
            # never triggers a prerequisite step either. Pure idling.
            t, steps = 0.0, 0
            while t < HAUL_WINDOW_S:
                tier = (tier_from_work(steps) if kw.get("work_gated")
                        else current_tier(t, 4, True))
                deepest = max(deepest, tier)
                t += TIER_DATA[min(tier, 3)][0] / 4.0
        print(f"  {label:<28} an idle crew reaches tier {deepest}")
    print("\n  D-20 says depth is bought with work. Only the second row honours that.")


def show_rooms(n=1200):
    """R29: the round every partial model had been converging on.

    R17 found scanning's payoff is 0.6 x the room's value spread and that the good
    policy is therefore SELECTIVE -- but its model had no apex, no classes and no
    curses. R28 found the appraiser INVERTS across the contract chain (+9.6% on night 1,
    -8.6% by night 4) because scanning pins Disturbance at COLLECT -- but its model had
    no rooms, so it could only ask "appraise every shelf or none".

    Both findings point at the same fix, and neither model could test it. This one can.
    """
    print("\n\nR29 — SELECTIVE SCANNING, WITH THE APEX AND THE CURSE IN THE MODEL")
    print("-" * 78)
    print(f"{'night':<7}{'van':>5}{'BLIND $':>11}{'scan ALL':>11}{'vs':>8}"
          f"{'SELECTIVE':>12}{'vs':>8}   which rooms")

    def best(rooms_, night, van):
        out = 0.0
        for q in (0.45, 0.75, 0.90):
            for cap in (3, 99):
                m = statistics.mean(
                    run_night(random.Random(s * 97 + night), 4, van, noise=True,
                              scan=bool(rooms_), q_cap=q, depth_cap=True,
                              metric="per_trip", rule="class", curses=True,
                              cursed_cap=cap, rooms=True, scan_rooms=rooms_)[0]
                    for s in range(n))
                out = max(out, m)
        return out

    for night, van in ((1, 14), (2, 15), (3, 17), (4, 19)):
        bl = best((), night, van)
        al = best(("uniform", "mixed", "curio"), night, van)
        sel = {"curio": best(("curio",), night, van),
               "curio+mixed": best(("curio", "mixed"), night, van)}
        k = max(sel, key=lambda x: sel[x])
        print(f"{night:<7}{van:>5}{bl:>11,.0f}{al:>11,.0f}{al / bl - 1:>8.1%}"
              f"{sel[k]:>12,.0f}{sel[k] / bl - 1:>8.1%}   {k}")
    print("\nScanning EVERYTHING decays across the chain and goes negative -- that is R28.")
    print("Scanning SELECTIVELY stays positive on every night. The all-or-nothing framing")
    print("was the problem, not the appraiser. And the optimum TIGHTENS as the van grows:")
    print("two room classes are worth stopping for early, one by night 4.")


def show_curse(n=2500):
    """R28: the appraiser measured on the half R27 said was its real defence.

    R27 found the VALUE half worth roughly nothing against a night's total, and argued
    the mechanic must be earning its place on the GRADE instead -- R11 valued the curse
    decision at +7%, and it is a decision a blind crew cannot even express, because
    "take two or three and then refuse" requires knowing which ones they are.

    Measured here for the first time in a model that has the apex, the classes, the
    noise AND the curse together. The answer is not the rescue R27 expected.
    """
    print("\n\nR28 — THE APPRAISER ACROSS THE CONTRACT CHAIN, WITH CURSES")
    print("-" * 78)
    print(f"{'night':<7}{'van':>5}{'best SCAN $':>14}{'BLIND $':>11}{'edge':>9}"
          f"{'scan endD':>11}{'lost':>7}")
    for night, van in ((1, 14), (2, 15), (3, 17), (4, 19)):
        def best(scan, **kw):
            out = 0.0
            for q in (0.45, 0.75, 0.90):
                m = statistics.mean(
                    run_night(random.Random(s * 97 + night), 4, van, noise=True,
                              scan=scan, q_cap=q, depth_cap=True, metric="per_trip",
                              rule="class", curses=True, **kw)[0]
                    for s in range(n))
                out = max(out, m)
            return out
        sc = max(best(True, cursed_cap=c) for c in (0, 2, 3, 4, 99))
        bl = best(False)
        diag = [run_night(random.Random(s * 97 + night), 4, van, noise=True, scan=True,
                          q_cap=0.75, depth_cap=True, metric="per_trip", rule="class",
                          curses=True, cursed_cap=99)[1] for s in range(600)]
        print(f"{night:<7}{van:>5}{sc:>14,.0f}{bl:>11,.0f}{sc / bl - 1:>9.1%}"
              f"{statistics.mean(x['endD'] for x in diag):>11.0f}"
              f"{statistics.mean(x['lost'] for x in diag):>7.1f}")
    print("\nThe edge DECAYS across the upgrade path and goes negative by night 3.")
    print("Not because of the three seconds -- cutting appraise time to 1.0s changes")
    print("nothing. It is the NOISE. Scanning pins Disturbance at ~100 (COLLECT) while a")
    print("blind crew sits at 46-57 (PATROL), and a bigger van means more shelves, more")
    print("pings, more of the night spent where the Curator takes your cargo: retrieval")
    print("losses go 0.3 -> 1.5 items across the chain while the blind crew loses 0.1.")
    print("Worse, it compounds: a scanning crew seeks value, cursed items ARE the value,")
    print("and every cursed piece aboard lifts the Disturbance floor another 7 points.")


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
    show_curse(n=1200)
    show_rooms(n=900)
    _assert_work_gating()
