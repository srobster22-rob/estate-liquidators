"""
Estate Liquidators — depth gated on WORK, the way D-20 says it must be.

    python3 sim/work_gate.py

--------------------------------------------------------------------------------
WHY THIS EXISTS (LOOP_LOG R24)

Every other simulation in this repo opens depth on a **clock**: `PHASES` at t =
0/120/240s. `DECISIONS.md` D-20 is FIRM that this is a bug — "prerequisite chains gate
depth through *work* — find the key, flip the breaker, pry the boards. Never through a
timer. Falsified if: nothing. Any future timer-based gate is a bug."

R23 showed that is not a pedantic complaint. Clock gating creates **dead time**: a crew
that fills its tier quota before the next tier opens has to stand around. Scanning
burns time, so scanning got credited for converting dead time into value — which is
where `scan_risk.py`'s interior optimum at 0.2–0.3 came from, and that number is what
moved Milestone 2's kill criterion in D-23 before R23 reversed it. Any result whose
mechanism runs through crew *time* inherits the artifact.

So this model has no clock. Depth opens when the crew pays for it.

HOW IT WORKS
  The night is a budget of CREW-SECONDS, not a wall clock: HAUL_S x crew x
  PARALLEL_EFFICIENCY. Everything the crew does spends from it — hauling a trip,
  appraising, and completing a prerequisite step. Wall-clock time (which the
  Disturbance ratchet needs) is derived back out of the spend.

  A prerequisite step costs PREREQ_CREW_S. That number is not invented: it is
  `validate_estate.py`'s `TASK_SECONDS = 75.0`, "rough cost of one prerequisite step
  for a crew of 4" — a constant that has sat in this repo since R1 defined and never
  used (LOOP_LOG R18). 75 seconds of wall clock for four people is 300 crew-seconds.

  Depth follows LEVEL-SPEC 6 V2 as reconciled in R17: tier 2 needs 1 completed step,
  tier 3 needs 2, tier 4 needs 3.

  There is no waiting. A crew not hauling is doing prerequisite work, which is the
  whole point — the window that used to be dead time is now productive, and it costs
  the hauls it displaces.

THE MODEL VALIDATES ITSELF ON D-20'S OWN FINDING. D-20 exists because clock gating
made **bigger crews earn less**: "they fill the van at capacity speed while depth opens
at wall-clock speed, ending the night with a van of foyer junk. A crew of two outearned
a crew of six by 2x before this was corrected." Panel A runs both gates across crew
sizes. If the clock gate does not reproduce that inversion, and the work gate does not
remove it, this model is wrong and nothing else in it should be believed.
"""

import json
import math
import os
import pathlib
import random
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

NIGHT_S = T["night"]["seconds"]
HAUL_S = T["night"]["haul_window_seconds"]
VAN_SLOTS = T["van"]["base_slots"]
APPRAISE_S = T["night"]["appraise_seconds"]
IMPULSE = T["loudness_constants"]["impulse_disturbance_per_l"]
SUSTAINED = T["loudness_constants"]["sustained_disturbance_per_l"]
DECAY_PER_MIN = T["disturbance"]["decay_per_min_at_crew4"]
RATCHET_END = T["disturbance"]["ratchet_end"]
FLOOR_PER_CURSED = T["disturbance"]["per_cursed_item_floor"]
L = T["loudness"]
RETRIEVAL = {k.upper(): v for k, v in T["retrieval"].items()}
TIERS = [(T["disturbance"]["tier_collect_at"], "COLLECT"),
         (T["disturbance"]["tier_pursue_at"], "PURSUE"),
         (T["disturbance"]["tier_patrol_at"], "PATROL"),
         (0, "DORMANT")]

CANDIDATES = 4
PARALLEL_EFFICIENCY = 0.65
SLOT_COST = T["van"]["slot_cost"]

# (round-trip seconds, value band, weight class). The class matters: a haul is not
# one slot, it is `van.slot_cost[class]` slots - an apex is a CART at five of the
# fourteen. The first version of this file charged every haul one slot, which made
# grabbing the apex nearly free and produced nights of exactly one haul. Classes and
# carry-time multipliers follow chain_sim.py's CLASS_DATA.
TIER_DATA = {1: (45.0, (80, 300), "armful"), 2: (60.0, (250, 700), "armful"),
             3: (90.0, (600, 1400), "two_man"), 4: (110.0, (4000, 8000), "cart")}
CARRY_MULT = {"pocket": 0.90, "armful": 1.00, "two_man": 1.44, "cart": 1.18}

# The apex is ONE object, not a band you can farm. D-21: "the apex object must be
# visible before it is reachable" - it is the estate's centrepiece, singular. The first
# version of this file let tier 4 be hauled repeatedly, which turned reaching the apex
# early into money-printing and made a crew of three out-earn every other size by 3x
# under the clock gate. That was an artifact of mine, not a finding about gating.
APEX_ITEMS = 1

# validate_estate.py TASK_SECONDS: 75s of wall clock for a crew of four.
PREREQ_CREW_S = 75.0 * 4
STEPS_FOR_TIER = {1: 0, 2: 1, 3: 2, 4: 3}

# Clock gate, kept only so panel A can show what it does wrong.
CLOCK_PHASES = [(0.0, 1), (120.0, 2), (240.0, 3), (360.0, 4)]
CLOCK_CAP = {1: 0.40, 2: 0.75, 3: 1.00, 4: 1.00}


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def run_night(seed, crew=4, scan_rate=0.4, depth_target=3, cursed=2,
              gate="work", labour_scaled=True, strategy=None, van_slots=None,
              scan_cost="none", k=0.35, exp=1.8, policy=None):
    """One night.

    gate='work'  : depth opens when the crew completes prerequisite steps.
    gate='clock' : depth opens at fixed wall-clock times, as every other sim does.
                   `labour_scaled` divides those times by crew/4 - the half-fix
                   chain_sim.py applies. Both are here so panel A can compare.
    """
    rng = random.Random(seed)
    cap = VAN_SLOTS if van_slots is None else van_slots
    budget = HAUL_S * crew * PARALLEL_EFFICIENCY
    spent = 0.0
    slots = float(cap)
    d = banked = 0.0
    steps = 0
    hauls = 0
    apex_taken = 0
    streak = 0
    intercepted = 0
    scanned = 0
    prereq_spend = 0.0

    def wall():
        return spent / (crew * PARALLEL_EFFICIENCY)

    def depth():
        if gate == "work":
            return max(ti for ti, need in STEPS_FOR_TIER.items() if steps >= need)
        scale = (4.0 / crew) if labour_scaled else 1.0
        tier = 1
        for start, ti in CLOCK_PHASES:
            if wall() >= start * scale:
                tier = ti
        return tier

    def noise_over(span, floor):
        nonlocal d
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
            d = max(floor, min(100.0, d - DECAY_PER_MIN / 60.0))

    while spent < budget and slots > 0:
        floor = RATCHET_END * min(1.0, wall() / NIGHT_S) + cursed * FLOOR_PER_CURSED
        tier = depth()

        # Invest in depth, or haul? Under the work gate this is the only place time
        # can go that is not hauling - and it is productive, not waiting.
        want_deeper = gate == "work" and tier < depth_target and steps < 3
        if want_deeper and spent + PREREQ_CREW_S <= budget:
            # Prying boards and flipping breakers is crowbar-loud.
            noise_over(PREREQ_CREW_S / (crew * PARALLEL_EFFICIENCY), floor)
            d = min(100.0, d + L["crowbar"] * IMPULSE)
            spent += PREREQ_CREW_S
            steps += 1
            continue

        # Under the clock gate the crew has nothing to do but wait for the tier it
        # is holding slots for. That wait is the artifact R23 found.
        if gate == "clock" and hauls >= CLOCK_CAP[tier] * cap and tier < 4:
            step = TIER_DATA[tier][0] / (crew * PARALLEL_EFFICIENCY)
            noise_over(step, floor)
            spent += step * crew * PARALLEL_EFFICIENCY
            continue

        if tier == 4 and apex_taken >= APEX_ITEMS:
            tier = 3                      # the centrepiece is already in the van
        trip_s, band, cls = TIER_DATA[tier]
        slot_cost = SLOT_COST[cls]
        if slot_cost > slots:
            if tier == 1:
                break                     # cannot fit anything else
            tier = 1                      # take something small instead
            trip_s, band, cls = TIER_DATA[1]
            slot_cost = SLOT_COST[cls]
        cand = [rng.uniform(*band) for _ in range(CANDIDATES)]
        # The three strategies the appraiser's edge has always been quoted against.
        # ADAPTIVE is integrated.py's rule: haul blind until the van is half full,
        # then scan, because from there the only gains are swaps.
        if policy is not None:
            appraise = policy(slots, cap, tier_of(d), streak)
        elif strategy == "BLIND":
            appraise = False
        elif strategy == "SCAN":
            appraise = True
        elif strategy == "ADAPTIVE":
            appraise = slots <= 0.5 * cap
        else:
            appraise = rng.random() < scan_rate
        streak = streak + 1 if appraise else 0
        if appraise:
            scanned += 1
        cost_crew = trip_s * CARRY_MULT[cls]     # crew-seconds for this trip
        value = max(cand) if appraise else rng.choice(cand)
        if appraise:
            cost_crew += APPRAISE_S * CANDIDATES

        noise_over(cost_crew / (crew * PARALLEL_EFFICIENCY), floor)
        if appraise:
            d = min(100.0, d + CANDIDATES * L["appraise"] * IMPULSE)

        spent += cost_crew
        if spent > budget:
            break
        hauls += 1
        if tier == 4:
            apex_taken += 1

        # Standing still to appraise, priced by how hard the Curator is looking and by
        # how many times in a row you have done it. D-22 rejected this shape on
        # CLOCK-GATED evidence; R26 re-tests it here.
        if appraise and scan_cost == "compound":
            if rng.random() < min(0.95, RETRIEVAL[tier_of(d)] * k * streak ** exp):
                slots -= slot_cost
                intercepted += 1
                streak = 0
                continue

        # The attempt consumes the slots whether or not it lands (R8's reroll fix).
        slots -= slot_cost
        if rng.random() < RETRIEVAL[tier_of(d)]:
            continue
        banked += value

    return banked, steps, hauls, wall(), intercepted, scanned


def trial(n=3000, **kw):
    res = [run_night(s, **kw) for s in range(n)]
    v = [r[0] for r in res]
    return {"mean": statistics.mean(v),
            "se": statistics.stdev(v) / math.sqrt(n),
            "steps": statistics.mean(r[1] for r in res),
            "hauls": statistics.mean(r[2] for r in res),
            "icept": statistics.mean(r[4] for r in res),
            "scanned": statistics.mean(r[5] for r in res)}


if __name__ == "__main__":
    # 1,200 keeps the full panel set inside a couple of minutes so this stays a usable
    # regression citizen; R28 found the default blew a 10-minute sweep budget.
    # WORK_GATE_N=8000 reproduces the figures quoted in D-22 and LOOP_LOG R26.
    N = int(os.environ.get("WORK_GATE_N", 1200))
    print("=" * 78)
    print("DEPTH GATED ON WORK, NOT THE CLOCK  (D-20)")
    print(f"n = {N:,} nights per cell")
    print("=" * 78)

    print("\nA. THE MODEL'S OWN VALIDATION - D-20 says clock gating makes bigger")
    print("   crews earn LESS. If that does not reproduce, this model is wrong.")
    print("-" * 78)
    print(f"{'crew':<7}{'clock, unscaled':>17}{'clock, /crew':>15}{'WORK-GATED':>14}"
          f"{'steps':>8}{'hauls':>8}")
    rows = {}
    for crew in (2, 3, 4, 5, 6):
        a = trial(n=N, crew=crew, gate="clock", labour_scaled=False)
        b = trial(n=N, crew=crew, gate="clock", labour_scaled=True)
        # Best depth policy for THIS crew. A crew of two cannot afford the unlocks a
        # crew of six can, and forcing one policy on all sizes would measure the policy
        # rather than the gate.
        c = max((trial(n=N, crew=crew, gate="work", depth_target=dt)
                 for dt in (1, 2, 3, 4)), key=lambda r: r["mean"])
        rows[crew] = (a, b, c)
        print(f"{crew:<7}{a['mean']:>17,.0f}{b['mean']:>15,.0f}{c['mean']:>14,.0f}"
              f"{c['steps']:>8.2f}{c['hauls']:>8.1f}")
    inv_raw = rows[2][0]["mean"] > rows[6][0]["mean"]
    inv_work = rows[2][2]["mean"] > rows[6][2]["mean"]
    print(f"  unscaled clock gate: crew 2 outearns crew 6? {'YES' if inv_raw else 'no'}"
          f"   <- D-20's reported failure")
    print(f"  work gate:           crew 2 outearns crew 6? {'YES' if inv_work else 'no'}"
          f"   <- should be 'no'")

    print("\n\nB. THE SCAN-RATE AXIS WITH NO DEAD TIME (R23's prediction)")
    print("   Clock-gated, the peak sat at 0.2-0.3 because scanning absorbed waiting.")
    print("-" * 78)
    print(f"{'scan rate':<11}{'work-gated $':>14}{'+/-':>7}{'vs never':>10}"
          f"{'clock-gated $':>15}{'vs never':>10}")
    w, c = {}, {}
    for r in [i / 10 for i in range(11)]:
        rw = trial(n=N, scan_rate=r, gate="work")
        rc = trial(n=N, scan_rate=r, gate="clock")
        w[r], c[r] = rw, rc
        print(f"{r:<11.1f}{rw['mean']:>14,.0f}{1.96 * rw['se']:>7.0f}"
              f"{rw['mean'] / w[0.0]['mean'] - 1:>10.1%}"
              f"{rc['mean']:>15,.0f}{rc['mean'] / c[0.0]['mean'] - 1:>10.1%}")
    pw = max(w, key=lambda r: w[r]["mean"])
    pc = max(c, key=lambda r: c[r]["mean"])
    dz = (w[pw]["mean"] - w[0.0]["mean"]) / math.sqrt(w[pw]["se"] ** 2
                                                      + w[0.0]["se"] ** 2)
    print(f"  work-gated  peak {pw:.1f}  "
          f"{w[pw]['mean'] / w[0.0]['mean'] - 1:+.1%}  z={dz:.1f}  "
          f"({'INTERIOR' if 0 < pw < 1 else 'CORNER'})")
    print(f"  clock-gated peak {pc:.1f}  "
          f"{c[pc]['mean'] / c[0.0]['mean'] - 1:+.1%}  "
          f"({'INTERIOR' if 0 < pc < 1 else 'CORNER'})")

    print("\n\nE. THE APPRAISER'S EDGE, RE-MEASURED  (the +4.4% figure)")
    print("   ADAPTIVE vs BLIND, the comparison that number has always meant.")
    print("   Depth policy optimised per strategy so this measures the appraiser.")
    print("-" * 78)
    print(f"{'gate':<14}{'BLIND':>10}{'ADAPTIVE':>10}{'SCAN':>10}{'best':>10}"
          f"{'ADAPTIVE edge':>15}")
    for g in ("clock", "work"):
        r = {}
        for st in ("BLIND", "ADAPTIVE", "SCAN"):
            r[st] = max((trial(n=N, strategy=st, gate=g, depth_target=dt)["mean"]
                         for dt in (1, 2, 3, 4)), key=lambda m: m)
        best = max(r, key=lambda k: r[k])
        print(f"{g:<14}{r['BLIND']:>10,.0f}{r['ADAPTIVE']:>10,.0f}{r['SCAN']:>10,.0f}"
              f"{best:>10}{r['ADAPTIVE'] / r['BLIND'] - 1:>15.1%}")
    print("   clock-gated is the regime every earlier measurement of this number used.")

    print("\n\nF. DOES THE EDGE STILL DIE BETWEEN 24 AND 32 SLOTS?  (D-19)")
    print("   That claim - and the van ceiling of 20 - comes from haul_sim.py, which")
    print("   gates depth on unlock TIME. Re-run it under both gates.")
    print("   READ THE CLOCK COLUMN AS CONTAMINATED, NOT AS DATA. Scanning burns time,")
    print("   and under a clock gate burning time BUYS DEPTH. At 24 slots ADAPTIVE")
    print("   earns +70% on FEWER hauls (16 vs 18) because it stalls long enough to")
    print("   unlock the tier-4 apex that BLIND never reaches; at 32 BLIND reaches it")
    print("   too and the gap collapses to +5%. That is the R23 artifact with the apex")
    print("   behind it, and it is why the clock row is not monotone. R25.")
    print("-" * 78)
    print(f"{'van slots':<11}{'clock: BLIND':>14}{'ADAPTIVE':>10}{'edge':>8}"
          f"{'   |':>4}{'work: BLIND':>13}{'ADAPTIVE':>10}{'edge':>8}")
    for vs in (6, 10, 14, 18, 24, 32):
        out = []
        for g in ("clock", "work"):
            b = max(trial(n=max(1200, N // 2), strategy="BLIND", gate=g,
                          van_slots=vs, depth_target=dt)["mean"] for dt in (1, 2, 3, 4))
            a = max(trial(n=max(1200, N // 2), strategy="ADAPTIVE", gate=g,
                          van_slots=vs, depth_target=dt)["mean"] for dt in (1, 2, 3, 4))
            out.append((b, a))
        (cb, ca), (wb, wa) = out
        print(f"{vs:<11}{cb:>14,.0f}{ca:>10,.0f}{ca / cb - 1:>8.1%}{'   |':>4}"
              f"{wb:>13,.0f}{wa:>10,.0f}{wa / wb - 1:>8.1%}")
    print("   Work-gated, the edge does not decay with capacity - it is small and flat.")
    print("   Above ~18 slots the work-gated BLIND figure stops moving entirely: at deep")
    print("   play TIME binds before the van does, so extra capacity buys nothing. That")
    print("   is a different mechanism from D-19's 'the appraiser lives on van space")
    print("   binding', and it means the 24-32 crossover is not reproduced here.")

    print("\n\nG. RE-TEST OF D-22: does a SUPER-LINEAR scan cost work once the gate")
    print("   is honest? D-22 rejected it on clock-gated evidence, and R25 showed the")
    print("   clock gate inverts which strategy wins. Cost = RETRIEVAL x k x streak^1.8.")
    print("-" * 78)
    print(f"{'scan rate':<11}{'no cost $':>11}{'+/-':>7}{'compound $':>13}{'+/-':>7}"
          f"{'mid-scan losses':>17}")
    free, cost = {}, {}
    for r in [i / 10 for i in range(11)]:
        a = trial(n=N, scan_rate=r, gate="work", depth_target=4)
        b = trial(n=N, scan_rate=r, gate="work", depth_target=4,
                  scan_cost="compound")
        free[r], cost[r] = a, b
        print(f"{r:<11.1f}{a['mean']:>11,.0f}{1.96 * a['se']:>7.0f}"
              f"{b['mean']:>13,.0f}{1.96 * b['se']:>7.0f}{b['icept']:>17.2f}")
    pf = max(free, key=lambda r: free[r]["mean"])
    pc = max(cost, key=lambda r: cost[r]["mean"])
    print(f"  no cost   peak {pf:.1f}  "
          f"{free[pf]['mean'] / free[0.0]['mean'] - 1:+.1%}  "
          f"({'INTERIOR' if 0 < pf < 1 else 'CORNER'})")
    print(f"  compound  peak {pc:.1f}  "
          f"{cost[pc]['mean'] / cost[0.0]['mean'] - 1:+.1%}  "
          f"({'INTERIOR' if 0 < pc < 1 else 'CORNER'})")

    print("\n\nH. IS THE RESULTING RULE ONE A PLAYER CAN ACTUALLY FOLLOW?")
    print("   D-14 forbids leaning on signals the player cannot perceive, and DESIGN")
    print("   6.5 keeps Disturbance hidden. So: streak-based rules only - a crew always")
    print("   knows how many times in a row it just scanned.")
    print("-" * 78)
    POLICIES = [
        ("never scan", lambda sl, cp, t, k: False, "-"),
        ("always scan", lambda sl, cp, t, k: True, "no"),
        ("never twice running", lambda sl, cp, t, k: k == 0, "no"),
        ("at most twice running", lambda sl, cp, t, k: k < 2, "no"),
        ("at most three running", lambda sl, cp, t, k: k < 3, "no"),
        ("ADAPTIVE (van half full)", lambda sl, cp, t, k: sl <= 0.5 * cp, "no"),
        ("only below PURSUE", lambda sl, cp, t, k: t in ("DORMANT", "PATROL"), "YES"),
    ]
    print(f"{'rule':<27}{'no cost $':>11}{'compound $':>13}{'+/-':>7}"
          f"{'scans':>7}{'needs meter':>13}")
    base_c = None
    rows = {}
    for name, fn, meter in POLICIES:
        a = trial(n=N, gate="work", depth_target=4, policy=fn)
        b = trial(n=N, gate="work", depth_target=4, policy=fn, scan_cost="compound")
        if base_c is None:
            base_c = b["mean"]
        rows[name] = b
        print(f"{name:<27}{a['mean']:>11,.0f}{b['mean']:>13,.0f}"
              f"{1.96 * b['se']:>7.0f}{b['scanned']:>7.1f}{meter:>13}")
    best = max(rows, key=lambda k: rows[k]["mean"])
    playable = max((k for k in rows if k != "only below PURSUE"),
                   key=lambda k: rows[k]["mean"])
    print(f"  best overall: '{best}'   "
          f"{rows[best]['mean'] / base_c - 1:+.1%} over never scanning")
    print(f"  best PLAYER-FOLLOWABLE: '{playable}'   "
          f"{rows[playable]['mean'] / base_c - 1:+.1%}")

    print("\n\nI. IS THE REVERSAL ROBUST, OR ONE LUCKY (k, exp)?")
    print("   Reversing a FIRM decision on a single parameter point would be exactly")
    print("   the mistake D-22 itself made. Sweep both.")
    print("-" * 78)
    print(f"{'k':<7}{'exp':<6}{'rate peak':>11}{'shape':>10}"
          f"{'always':>9}{'streak':>9}{'winner':>18}")
    streak_wins = total = 0
    for kk in (0.15, 0.35, 0.75):
        for ee in (1.4, 1.8, 2.2):
            rows = {r / 10: trial(n=max(1500, N // 3), scan_rate=r / 10, gate="work",
                                  depth_target=4, scan_cost="compound",
                                  k=kk, exp=ee)["mean"] for r in range(11)}
            pk = max(rows, key=lambda r: rows[r])
            al = trial(n=max(1500, N // 3), gate="work", depth_target=4,
                       scan_cost="compound", k=kk, exp=ee,
                       policy=lambda sl, cap, ti, st: True)["mean"]
            sk = trial(n=max(1500, N // 3), gate="work", depth_target=4,
                       scan_cost="compound", k=kk, exp=ee,
                       policy=lambda sl, cap, ti, st: st == 0)["mean"]
            win = "streak" if sk > al else "always"
            streak_wins += win == "streak"
            total += 1
            print(f"{kk:<7.2f}{ee:<6.1f}{pk:>11.1f}"
                  f"{'interior' if 0 < pk < 1 else 'corner':>10}"
                  f"{al:>9,.0f}{sk:>9,.0f}{win:>18}")
    print(f"  the streak rule beats always-scan in {streak_wins}/{total} combinations")

    print("\n\nC. HOW MUCH DEPTH IS WORTH BUYING? Each step costs "
          f"{PREREQ_CREW_S:.0f} crew-seconds")
    print("   CAVEAT: this panel assigns ONE weight class per tier, while estates.py")
    print("   gives tier 3 a mix (two armfuls and a two-man). The tier-3 dip below is")
    print("   most likely that simplification, not an economy finding. Do not quote it.")
    print(f"   of a {HAUL_S * 4 * PARALLEL_EFFICIENCY:.0f} crew-second night at crew 4.")
    print("-" * 78)
    print(f"{'depth target':<14}{'banked $':>11}{'+/-':>7}{'steps':>8}{'hauls':>8}"
          f"{'vs tier 1':>11}")
    base = None
    for dt in (1, 2, 3, 4):
        r = trial(n=N, depth_target=dt, gate="work")
        if base is None:
            base = r["mean"]
        print(f"{'tier ' + str(dt):<14}{r['mean']:>11,.0f}{1.96 * r['se']:>7.0f}"
              f"{r['steps']:>8.2f}{r['hauls']:>8.1f}{r['mean'] / base - 1:>11.1%}")
