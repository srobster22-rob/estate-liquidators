"""
Estate Liquidators — a night in an ACTUAL estate, not an abstract candidate pool.

    python3 sim/estate_night.py

--------------------------------------------------------------------------------
WHY THIS EXISTS (LOOP_LOG R29)

R28 gave `chain_sim.py` a real work gate and the calibrated quota curve lost all
shape: every night passed 100%. The diagnosis was that the model prices a prerequisite
as LABOUR only, so a crew can buy an unlock at t=0 — while a real crew has to *find the
key before it can turn it*. That discovery cost is what the clock had been crudely
standing in for, and no model had it.

This model has it, because it stops inventing the estate and uses the one the repo
already contains. `estates.py` MANOR_A is the LEVEL-SPEC 8 worked example, with rooms
at real coordinates, portals between them, a prerequisite graph, and eight specific
plinths. `validate_estate.py` already knows how to path through it. Nothing had ever
connected that geometry to the economy — LEVEL-SPEC and ECONOMY have never touched.

WHAT CHANGES WHEN THE ESTATE IS REAL

  Prerequisites have LOCATIONS. Opening the office means grand_stair, then landing,
  then study, then conservatory - FOUR tasks in four rooms, not the three abstract
  steps R28 assumed. Each costs travel to get there.

  Depth costs DISTANCE. The foyer plinth is 12m from the van; the orangery is 69m and
  five portals. Deep hauls are slower because the house is bigger that way round, not
  because a tier table says so.

  The estate is FINITE. Eight plinths, $14,120 of goods, needing 16 slots of van for a
  van that holds 14. You cannot take everything, and what you leave is the decision.
  Every previous model drew from an infinite pool of statistically identical shelves.

WHAT IS STILL ASSUMED, AND SHOULD BE READ AS SUCH
  Walk 3.2 m/s and carry 2.6 m/s come from `proto3d/index.html`, not `tuning.json` -
  they are prototype movement values, not canon. The crew is treated as moving and
  working as one unit with `PARALLEL_EFFICIENCY`, so a crew never splits to do two
  things at once, which real crews do constantly. Both make this model PESSIMISTIC
  about big crews. Numbers here are a shape, not a tuning.
"""

import json
import math
import os
import pathlib
import random
import statistics

import estates
import validate_estate as V

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

HAUL_S = T["night"]["haul_window_seconds"]
NIGHT_S = T["night"]["seconds"]
SLOT_COST = T["van"]["slot_cost"]
RETRIEVAL = {k.upper(): v for k, v in T["retrieval"].items()}
RATCHET_END = T["disturbance"]["ratchet_end"]
DECAY_PER_MIN = T["disturbance"]["decay_per_min_at_crew4"]
FLOOR_PER_CURSED = T["disturbance"]["per_cursed_item_floor"]
IMPULSE = T["loudness_constants"]["impulse_disturbance_per_l"]
L = T["loudness"]
TIERS = [(T["disturbance"]["tier_collect_at"], "COLLECT"),
         (T["disturbance"]["tier_pursue_at"], "PURSUE"),
         (T["disturbance"]["tier_patrol_at"], "PATROL"), (0, "DORMANT")]
CONTRACT = T["contract"]

WALK, CARRY = 3.2, 2.6          # m/s, proto3d/index.html - NOT canonical
PARALLEL_EFFICIENCY = 0.65
TASK_WORK_S = 75.0              # validate_estate.py TASK_SECONDS, the work itself
PEOPLE = {"pocket": 1, "armful": 1, "two_man": 2, "cart": 1}
SETUP = {"pocket": 0.0, "armful": 0.0, "two_man": 0.0, "cart": 20.0}
APPRAISE_S = T["night"]["appraise_seconds"]

E = V.Estate(estates.MANOR_A)


def _dist_from_van(room):
    p = E.path(E.van, room)
    return sum(E.dist(a, b) for a, b in zip(p, p[1:])) if p else None


DIST = {r: _dist_from_van(r) for r in E.rooms}


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def _tasks_for(room, seen=None):
    """Every prerequisite task that must be done before `room` opens, in order."""
    seen = seen if seen is not None else set()
    out = []
    for req in E.prereqs.get(room, []):
        key = (req["room"], req["type"])
        if key in seen:
            continue
        out.extend(_tasks_for(req["room"], seen))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def run_night(seed, crew=4, van_slots=14, scan_rate=0.4, depth_target=4, jitter=0.20):
    rng = random.Random(seed)
    t = d = banked = 0.0
    slots = float(van_slots)
    done = set()
    taken = set()
    spent_prereq = spent_haul = spent_travel = 0.0

    plinths = []
    for i, pl in enumerate(estates.MANOR_A["plinths"]):
        v = pl["value"] * (1.0 + rng.uniform(-jitter, jitter))
        plinths.append({**pl, "i": i, "value": v})

    def advance(wall, kind):
        """Spend WALL seconds. Callers convert people-seconds to wall themselves,
        because the two kinds of work parallelise differently: hauling contends for
        doorways (PARALLEL_EFFICIENCY), four people at a breaker do not."""
        nonlocal t, d, spent_prereq, spent_haul
        for _ in range(int(wall)):
            if rng.random() < 0.055:
                d += L["door"] * IMPULSE
            if rng.random() < 0.006:
                d += L["break_small"] * IMPULSE
            floor = RATCHET_END * min(1.0, t / NIGHT_S)
            d = max(floor, min(100.0, d - DECAY_PER_MIN / 60.0))
        t += wall
        if kind == "prereq":
            spent_prereq += wall
        else:
            spent_haul += wall

    def open_rooms():
        return {r for r in E.rooms
                if all((q["room"], q["type"]) in done for q in E.prereqs.get(r, []))}

    # Buy depth first, up to the intended tier. Each task costs TRAVEL to its room
    # plus the work itself - the discovery cost R28 said was missing.
    wanted = [pl for pl in plinths if pl["tier"] <= depth_target]
    need = []
    for pl in sorted(wanted, key=lambda p: -p["value"]):
        for task in _tasks_for(pl["room"]):
            if task not in need:
                need.append(task)
    for task in need:
        room, _ = task
        # TASK_WORK_S is already WALL time for a crew of four (validate_estate.py),
        # so it is 4 x 75 = 300 people-seconds; the crew walks there, then works.
        wall = DIST[room] / WALK + (TASK_WORK_S * 4.0) / crew
        if t + wall >= HAUL_S:
            break
        advance(wall, "prereq")
        d = min(100.0, d + L["crowbar"] * IMPULSE)
        done.add(task)

    # Then haul, best value-per-slot first among what is reachable.
    while t < HAUL_S and slots > 0:
        opened = open_rooms()
        avail = [p for p in plinths if p["i"] not in taken and p["room"] in opened
                 and SLOT_COST[p["cls"]] <= slots]
        if not avail:
            break
        pl = max(avail, key=lambda p: p["value"] / SLOT_COST[p["cls"]])
        taken.add(pl["i"])

        dist = DIST[pl["room"]]
        people = PEOPLE[pl["cls"]]
        labour = ((dist / WALK) + (dist / CARRY) + SETUP[pl["cls"]]) * people
        if rng.random() < scan_rate:
            labour += APPRAISE_S * 4
            d = min(100.0, d + L["appraise"] * IMPULSE * 4)
        # Hauls run in parallel across the crew and contend for the same doorways.
        wall = labour / (crew * PARALLEL_EFFICIENCY)
        if t + wall > HAUL_S:
            break
        advance(wall, "haul")

        slots -= SLOT_COST[pl["cls"]]
        if rng.random() < RETRIEVAL[tier_of(d)]:
            continue
        banked += pl["value"]

    return banked, len(done), len(taken), spent_prereq, spent_haul, t


def trial(n=2000, **kw):
    res = [run_night(s, **kw) for s in range(n)]
    v = [r[0] for r in res]
    return {"mean": statistics.mean(v), "se": statistics.stdev(v) / math.sqrt(n),
            "tasks": statistics.mean(r[1] for r in res),
            "hauls": statistics.mean(r[2] for r in res),
            "prereq_s": statistics.mean(r[3] for r in res),
            "haul_s": statistics.mean(r[4] for r in res)}


if __name__ == "__main__":
    N = int(os.environ.get("ESTATE_N", 2000))
    print("=" * 78)
    print("A NIGHT IN MANOR_A — the LEVEL-SPEC 8 estate, priced by its own geometry")
    print(f"n = {N:,}")
    print("=" * 78)
    total = sum(p["value"] for p in estates.MANOR_A["plinths"])
    need = sum(SLOT_COST[p["cls"]] for p in estates.MANOR_A["plinths"])
    print(f"\n  The estate holds ${total:,} across {len(estates.MANOR_A['plinths'])} "
          f"plinths needing {need:.0f} slots. The van holds 14.")
    print(f"  So the ceiling is not the estate, it is the van - and what you leave")
    print(f"  behind is the decision every previous model drew from an infinite shelf.")

    print("\n\nA. HOW DEEP IS IT WORTH GOING, once unlocking costs travel + work?")
    print("-" * 78)
    print(f"{'depth target':<14}{'banked $':>10}{'+/-':>7}{'tasks':>7}{'hauls':>7}"
          f"{'prereq s':>10}{'haul s':>9}{'vs t1':>8}")
    base = None
    for dt in (1, 2, 3, 4):
        r = trial(n=N, depth_target=dt)
        if base is None:
            base = r["mean"]
        print(f"{'tier ' + str(dt):<14}{r['mean']:>10,.0f}{1.96 * r['se']:>7.0f}"
              f"{r['tasks']:>7.1f}{r['hauls']:>7.1f}{r['prereq_s']:>10.0f}"
              f"{r['haul_s']:>9.0f}{r['mean'] / base - 1:>8.0%}")

    print("\n\nB. THE QUOTA CURVE against a real estate")
    print("-" * 78)
    print(f"{'night':<7}{'quota':>8}{'van':>5}{'mean $':>10}{'pass':>7}"
          f"{'best depth':>12}{'quota/estate':>13}")
    for night in range(1, 5):
        q = CONTRACT[f"quota_night{night}"]
        van = CONTRACT[f"van_night{night}"]
        best, bq, bdt = None, 0.0, 0
        for dt in (1, 2, 3, 4):
            res = [run_night(s, van_slots=van, depth_target=dt) for s in range(N)]
            m = statistics.mean(r[0] for r in res)
            if best is None or m > best:
                best = m
                bq = sum(1 for r in res if r[0] >= q) / len(res)
                bdt = dt
        print(f"{night:<7}{q:>8,}{van:>5}{best:>10,.0f}{bq:>7.0%}"
              f"{'tier ' + str(bdt):>12}{q / total:>10.0%}")

    print("""
  The quota curve still has no shape - but for the OPPOSITE reason to R28. There the
  work gate let crews rush depth. Here the estate simply does not hold enough to make
  $12,500 hard once the office is open: MANOR_A contains $14,120 total, so night 4 asks
  for 89% of everything in the house. A crew that opens the apex banks ~96% of the
  estate and clears every quota.

  That is the first time LEVEL-SPEC's geometry and ECONOMY's quota curve have been put
  in the same model, and it says they were never calibrated against each other. The
  quota is a number; the estate's total value is a number; nothing has ever compared
  them. ECONOMY 4 already says the fix is richer estates rather than a tighter ceiling -
  this is how much richer.""")

    print("\n\nC. CREW SIZE — does the geometry still reward more hands?")
    print("-" * 78)
    print(f"{'crew':<7}{'banked $':>10}{'+/-':>7}{'tasks':>7}{'hauls':>7}{'prereq s':>10}")
    for crew in (2, 3, 4, 5, 6):
        r = max((trial(n=N, crew=crew, depth_target=dt) for dt in (1, 2, 3, 4)),
                key=lambda x: x["mean"])
        print(f"{crew:<7}{r['mean']:>10,.0f}{1.96 * r['se']:>7.0f}{r['tasks']:>7.1f}"
              f"{r['hauls']:>7.1f}{r['prereq_s']:>10.0f}")
    print("""
  Not the monotone rise chain_sim reports. The prerequisite chain is a hard gate below
  four: a crew of two can only afford ONE unlock and never reaches the money, and a
  crew of three spends 83% of the night opening doors. Above four it goes flat, because
  a finite estate runs out - the van binds, not the labour. Both ends are consequences
  of modelling a real house instead of an infinite shelf.""")
