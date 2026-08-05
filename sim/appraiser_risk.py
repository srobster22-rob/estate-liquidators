"""
Estate Liquidators — R16: the appraiser as a TAIL RISK.

(This executes the brief that LOOP_LOG's "Next step" block has been holding since R11.
Rounds R12-R15 went somewhere more useful — the prototype, the C# core, the drift
checker, art direction — and left this question open. It is still open, so here it is.)

R8 measured the appraiser's edge at +6% and R9 asked whether that is enough to carry
the game's signature mechanic. R10/R11 answered the same shape of question for curses:
a LINEAR cost can never balance a MULTIPLICATIVE benefit, so the cost has to be
super-linear or catastrophic before an interior optimum exists. Making the curse a ruin
roll produced exactly that.

The appraiser has the identical structure. Scanning's cost in integrated.py is linear
(3s of time + 17 Disturbance per trip) and its benefit is max-of-4 instead of
choose-1 — so ADAPTIVE is a linear interpolation between BLIND and SCAN and can only
win in the narrow crossover band. That is R6's structural finding restated.

This file gives scanning a cost with the shape R11 proved is necessary:

  Appraising holds you STATIONARY for three seconds. If the Curator is already at
  PURSUE or COLLECT, that is when it arrives. The risk compounds with each
  CONSECUTIVE scanning trip — the crew that keeps stopping teaches it where to look.

Two things follow that a linear cost cannot produce:

  1. The cost is STATE-DEPENDENT. Scanning at DORMANT is free (retrieval 0.00);
     scanning at COLLECT is ruinous. So the best policy is not "scan more" or "scan
     less" — it is "scan WHEN", which is a different point in policy space, not a
     blend of the two extremes.
  2. The cost is SELF-INFLICTED. Scanning is what raises Disturbance in the first
     place, so a crew that scans freely walks itself into the tier where scanning is
     punished. That feedback is what bends the curve.

The test: sweep the risk coefficient and ask whether a GATE policy — scan only while
Disturbance is below k — beats both extremes across a broad band. If an interior gate
wins only in a sliver, the appraiser has the same structural problem R6 found and the
+6% concern stands. If it wins broadly, the mechanic answers itself.

--------------------------------------------------------------------------------------
WHAT IT FOUND — the hypothesis is falsified, and the reason generalises.

1. THE TAIL RISK NEVER HELPS. Best-policy edge over BLIND falls monotonically as the
   risk coefficient rises: 6.0% (k=0) -> 5.4 -> 5.0 -> 4.3 -> 2.4 -> 0.0 (k=8, BLIND
   wins outright). There is no k at which the appraiser gets MORE interesting.

   The reason R11 worked and R12 does not is that the two mechanics had opposite
   problems. The curse was ALWAYS CORRECT to take — benefit too large — so adding a
   catastrophic cost created a decision. The appraiser is BARELY correct to use —
   benefit too small — and no cost you add to a thin edge makes it thicker.
   You cannot raise a payoff by adding a cost. The brief was structurally confused; the
   remaining levers must widen the BENEFIT (see appraiser_variance.py).

2. THE "INTERIOR" OPTIMUM IS DEGENERATE. GATE_30 wins at every k > 0, and 30 is exactly
   the DORMANT/PATROL boundary — the edge of the region where RETRIEVAL is 0.00. The
   optimum does not sit inside the risk landscape, it sits flush against the flat zero
   part of it. A cost function with a zero region cannot produce an interior optimum;
   it produces a boundary rule. Only at k=0 does a genuinely interior gate win
   (GATE_45, 6,883) — i.e. the moment you switch the risk on, the answer collapses to
   "scan only when it is free."

3. THE COMPOUNDING STREAK IS PURE LOSS. Sweeping the exponent 0 -> 2 at fixed k=4.0
   moves the best edge 3.1% -> 1.2%, monotonically down. Compounding adds punishment
   without adding shape, so the "teaches it where to look" half of the brief buys
   nothing and should not be built.

4. THE ONE KEEPER — GATE BEATS ADAPTIVE ON ITS OWN TERMS. Even at k=0, gating on
   Disturbance (GATE_45: 6,883) edges out the van-fill heuristic (ADAPTIVE: 6,852) and
   beats it decisively once any risk exists (k=1: 6,822 vs 5,174). ADAPTIVE was
   accidentally approximating "scan while it's quiet" via van fill, because both
   correlate with time. The real heuristic is the Curator's state, and that is
   legible without a HUD: DORMANT is the tier where AUDIO-SPEC 3.2 gives the house
   NO SOUND AT ALL. "Appraise while you can't hear it" is a rule a crew can say out
   loud in a hallway, which is the bar this project sets.

Run: python appraiser_risk.py
"""

import random
import statistics

CREW = 4
NIGHT_S = 720.0
HAUL_S = 540.0
VAN_SLOTS = 14

IMPULSE = 0.09
SUSTAINED = 0.02
DECAY_PER_MIN = 50.0        # R4
RATCHET_END = 55.0

L = {"sprint": 45, "appraise": 48, "door": 60, "dolly": 35,
     "radio": 38, "break_small": 90}

CANDIDATES = 4
PARALLEL_EFFICIENCY = 0.65

RETRIEVAL = {"DORMANT": 0.00, "PATROL": 0.02, "PURSUE": 0.10, "COLLECT": 0.25}
TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]
TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}

# --- the R16 addition ------------------------------------------------------------
# p(caught mid-scan) = SCAN_RISK x RETRIEVAL[tier] x streak^SCAN_EXP
# streak = consecutive trips on which this crew stopped to appraise.
SCAN_RISK = 0.0            # swept below; 0.0 reproduces integrated.py exactly
SCAN_EXP = 1.0             # 0.0 = no compounding, 1.0 = linear in streak
P_CAUGHT_CAP = 0.60
INTERRUPT_D = 25.0         # it found you standing still: aggro spike
FLEE_S = 12.0              # and you drop everything and run


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for start, ti in PHASES:
        if t >= start:
            tier = ti
    return tier


def wants_scan(policy, d, slots):
    """Every policy in one place, so the comparison is apples to apples."""
    if policy == "BLIND":
        return False
    if policy == "SCAN":
        return True
    if policy == "ADAPTIVE":                 # integrated.py's van-fill heuristic
        return slots <= 0.5 * VAN_SLOTS
    if policy.startswith("GATE_"):           # scan only while it is not looking
        return d < float(policy[5:])
    raise ValueError(policy)


def run_night(seed, policy, cursed=2, retrieval_scale=1.0,
              scan_risk=None, scan_exp=None):
    risk_k = SCAN_RISK if scan_risk is None else scan_risk
    risk_e = SCAN_EXP if scan_exp is None else scan_exp

    rng = random.Random(seed)
    d, t, slots, banked, filled = 0.0, 0.0, float(VAN_SLOTS), 0.0, 0.0
    scans, lost, caught, scan_trips, trips = 0, 0, 0, 0, 0
    streak = 0

    while t < HAUL_S and slots > 0:
        tier = depth_at(t)
        trip_s, band = TIER_DATA[tier]
        per_trip = trip_s / (CREW * PARALLEL_EFFICIENCY)

        # Depth budget — every strategy gets it. See integrated.py / LOOP_LOG R5.
        if filled >= TIER_CAP[tier] * VAN_SLOTS and tier < 3:
            t += per_trip
            continue

        candidates = [rng.uniform(*band) for _ in range(CANDIDATES)]
        appraise = wants_scan(policy, d, slots)

        cost = per_trip
        if appraise:
            value = max(candidates)
            cost += 3.0 * CANDIDATES / CREW
            scans += CANDIDATES
            streak += 1
        else:
            value = rng.choice(candidates)
            streak = 0

        # --- Disturbance across the trip ------------------------------------
        floor = RATCHET_END * (t / NIGHT_S) + cursed * 2.0
        for _ in range(int(cost)):
            for _ in range(CREW):
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

        if appraise:
            d = min(100.0, d + CANDIDATES * L["appraise"] * IMPULSE)

        t += cost
        if t > HAUL_S:
            break
        filled += 1.0
        trips += 1
        if appraise:
            scan_trips += 1

        # --- R16: caught standing still -------------------------------------
        # Priced off the tier the crew is IN while stationary, and compounding in
        # how many trips in a row they have stopped.
        if appraise and risk_k > 0.0:
            p = risk_k * RETRIEVAL[tier_of(d)] * (streak ** risk_e)
            if rng.random() < min(P_CAUGHT_CAP, p):
                caught += 1
                lost += 1
                slots -= 1.0
                d = min(100.0, d + INTERRUPT_D)
                t += FLEE_S
                streak = 0
                continue

        if rng.random() < RETRIEVAL[tier_of(d)] * retrieval_scale:
            lost += 1
            slots -= 1.0
            continue

        slots -= 1.0
        banked += value

    scan_share = scan_trips / trips if trips else 0.0
    return banked, scans, lost, d, caught, scan_share


def trial(policy, n=2500, **kw):
    res = [run_night(s, policy, **kw) for s in range(n)]
    return {
        "mean": statistics.mean(r[0] for r in res),
        "scans": statistics.mean(r[1] for r in res),
        "lost": statistics.mean(r[2] for r in res),
        "endD": statistics.mean(r[3] for r in res),
        "caught": statistics.mean(r[4] for r in res),
        "share": statistics.mean(r[5] for r in res),
    }


GATES = ["GATE_30", "GATE_45", "GATE_60", "GATE_75", "GATE_85"]
ALL_POLICIES = ["BLIND"] + GATES + ["ADAPTIVE", "SCAN"]


def sweep_risk():
    print("\n\nDOES A TAIL RISK CREATE AN INTERIOR OPTIMUM?")
    print("(mean $ by policy; GATE_k = appraise only while Disturbance < k)")
    print("-" * 100)
    print(f"{'risk k':<8}" + "".join(f"{p:>10}" for p in ALL_POLICIES)
          + f"{'best':>10}{'edge':>8}")
    for k in (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
        rows = {p: trial(p, n=1500, scan_risk=k) for p in ALL_POLICIES}
        best = max(rows, key=lambda x: rows[x]["mean"])
        edge = rows[best]["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{k:<8.1f}"
              + "".join(f"{rows[p]['mean']:>10,.0f}" for p in ALL_POLICIES)
              + f"{best:>10}{edge:>8.1%}")


def sweep_exponent():
    print("\n\nHOW MUCH OF THE EFFECT IS THE COMPOUNDING STREAK?")
    print("(risk k=4.0 held; exp 0 = flat per-scan risk, 2 = quadratic in streak)")
    print("-" * 100)
    print(f"{'exp':<8}" + "".join(f"{p:>10}" for p in ALL_POLICIES)
          + f"{'best':>10}{'edge':>8}")
    for e in (0.0, 0.5, 1.0, 1.5, 2.0):
        rows = {p: trial(p, n=1500, scan_risk=4.0, scan_exp=e)
                for p in ALL_POLICIES}
        best = max(rows, key=lambda x: rows[x]["mean"])
        edge = rows[best]["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{e:<8.1f}"
              + "".join(f"{rows[p]['mean']:>10,.0f}" for p in ALL_POLICIES)
              + f"{best:>10}{edge:>8.1%}")


def detail(k=4.0):
    print(f"\n\nWHAT THE WINNING POLICY ACTUALLY DOES   (risk k={k}, exp 1.0)")
    print("-" * 100)
    print(f"{'policy':<10}{'mean $':>10}{'p10':>9}{'p90':>9}{'scan %':>9}"
          f"{'caught':>9}{'lost':>8}{'end D':>8}{'vs BLIND':>10}")
    base = None
    for p in ALL_POLICIES:
        res = [run_night(s, p, scan_risk=k) for s in range(2500)]
        vals = sorted(r[0] for r in res)
        m = statistics.mean(vals)
        if base is None:
            base = m
        r = trial(p, n=2500, scan_risk=k)
        print(f"{p:<10}{m:>10,.0f}{vals[len(vals)//10]:>9,.0f}"
              f"{vals[9*len(vals)//10]:>9,.0f}{r['share']:>9.0%}"
              f"{r['caught']:>9.2f}{r['lost']:>8.1f}{r['endD']:>8.0f}"
              f"{m / base - 1:>10.1%}")


if __name__ == "__main__":
    print("R16 — THE APPRAISER AS A TAIL RISK")
    print("=" * 100)
    sweep_risk()
    sweep_exponent()
    detail()
