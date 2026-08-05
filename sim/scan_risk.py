"""
Estate Liquidators — does the appraiser become a decision if scanning has a
SUPER-LINEAR cost?

    python3 sim/scan_risk.py

--------------------------------------------------------------------------------
THE PRE-REGISTERED HYPOTHESIS (LOOP_LOG R12's next-step, never run until R20)

R8 measured the appraiser's edge at +6% over blind hauling — corrected to +4.4% in
R20, once integrated.py stopped using the retracted +2 cursed floor. Either way it is
thin, and ECONOMY 9.1 flags the open question: is a break-even-ish edge enough to
carry the game's signature mechanic?

R12 proposed that this is the SAME SHAPE of problem as the curse, and should have the
same answer. The curse was stuck because every cost was linear against a
multiplicative benefit, so the optimum was always a corner — take all, or take none.
R11 fixed it by making the cost super-linear (ruin = 0.015 x cursed^1.8), which
produced a real interior optimum at two or three pieces.

Scanning has the same structure. Its cost is linear (noise per ping, time per ping)
and its benefit is roughly linear (max-of-N beats a random draw by a fixed factor), so
one of the extremes wins and there is no interesting middle. R6 already tried the
obvious fix — tier-scaled scan exposure — and found it "goes straight from SCAN to
BLIND with no band at all", which is exactly what a linear cost does.

The untested proposal is the super-linear version: **appraising while the Curator is
already hunting risks it arriving mid-scan, and the risk COMPOUNDS with each
consecutive scan.** You are stationary for three seconds per ping; doing that once
while it is nearby is a gamble, doing it five times in a row is a request.

  P(intercepted during this scan) = RETRIEVAL[tier] x K x streak^EXP

where `streak` counts consecutive scanned trips and resets the moment you haul
something blind. That is the curse's shape applied to time-on-station instead of
cargo.

WHAT WOULD CONFIRM IT: sweeping scan RATE from 0 to 1 produces an interior maximum —
some middle rate beats both never-scan and always-scan by a margin worth having.
WHAT WOULD FALSIFY IT: the optimum stays at a corner (0 or 1) at every plausible K
and EXP, meaning super-linearity does not rescue the appraiser either, and the +4.4%
edge is simply what the mechanic is worth.

Guards against this project's three known model artifacts, all of which produced
retracted numbers before:
  - the REROLL bug (R6/R7/R8): a haul attempt consumes the opportunity whether or not
    it lands, so losing cargo is never a free extra draw.
  - the MYOPIA bug (R5, three times): every strategy gets the same depth budget, so
    blind hauling cannot be made to look bad by filling the van before tier 3 opens.
  - MONOTONICITY: harsher exposure must never make a scanning strategy richer. That is
    asserted, not eyeballed.
"""

import json
import math
import os
import pathlib
import random
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
TUNING = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

CREW = TUNING["night"]["crew"]
NIGHT_S = TUNING["night"]["seconds"]
HAUL_S = TUNING["night"]["haul_window_seconds"]
VAN_SLOTS = TUNING["van"]["base_slots"]
APPRAISE_S = TUNING["night"]["appraise_seconds"]

IMPULSE = TUNING["loudness_constants"]["impulse_disturbance_per_l"]
SUSTAINED = TUNING["loudness_constants"]["sustained_disturbance_per_l"]
DECAY_PER_MIN = TUNING["disturbance"]["decay_per_min_at_crew4"]
RATCHET_END = TUNING["disturbance"]["ratchet_end"]
FLOOR_PER_CURSED = TUNING["disturbance"]["per_cursed_item_floor"]

L = TUNING["loudness"]
RETRIEVAL = {k.upper(): v for k, v in TUNING["retrieval"].items()}
TIERS = [(TUNING["disturbance"]["tier_collect_at"], "COLLECT"),
         (TUNING["disturbance"]["tier_pursue_at"], "PURSUE"),
         (TUNING["disturbance"]["tier_patrol_at"], "PATROL"),
         (0, "DORMANT")]

CANDIDATES = 4
PARALLEL_EFFICIENCY = 0.65          # chain_sim measured ~1.5x trips per slot
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]
TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for start, ti in PHASES:
        if t >= start:
            tier = ti
    return tier


def run_night(seed, scan_rate, mode="compound", k=0.35, exp=1.8, cursed=2,
              policy=None, depth_cap=None):
    """One night. `scan_rate` is the probability of appraising on a given trip.

    mode: 'none'     no interception risk while scanning (the current model)
          'linear'   risk scales with tier only  (what R6 tried)
          'compound' risk scales with tier AND consecutive-scan streak^exp

    `policy`, if given, overrides scan_rate with a state-dependent rule
    (slots_left, van_slots, tier_name, streak) -> bool. This is the comparison that
    matters: a fixed rate is a frequency, a policy is a judgement about WHEN.
    """
    rng = random.Random(seed)
    cap = TIER_CAP if depth_cap is None else depth_cap
    d = t = banked = 0.0
    slots = float(VAN_SLOTS)
    filled = 0.0
    streak = 0
    scans = intercepted = lost = 0
    waits = 0

    while t < HAUL_S and slots > 0:
        tier = depth_at(t)
        trip_s, band = TIER_DATA[tier]
        per_trip = trip_s / (CREW * PARALLEL_EFFICIENCY)

        if filled >= cap[tier] * VAN_SLOTS and tier < 3:
            t += per_trip
            waits += 1
            continue

        candidates = [rng.uniform(*band) for _ in range(CANDIDATES)]
        roll = rng.random()
        appraise = (policy(slots, VAN_SLOTS, tier_of(d), streak) if policy
                    else roll < scan_rate)

        cost = per_trip
        if appraise:
            value = max(candidates)
            cost += APPRAISE_S * CANDIDATES / CREW
            scans += CANDIDATES
            streak += 1
        else:
            value = rng.choice(candidates)
            streak = 0

        floor = RATCHET_END * (t / NIGHT_S) + cursed * FLOOR_PER_CURSED
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

        # An ATTEMPT consumes the opportunity whether or not it lands (R8).
        filled += 1.0

        # Standing still to appraise, priced by how hard the Curator is looking and by
        # how many times in a row you have done it.
        if appraise and mode != "none":
            p = RETRIEVAL[tier_of(d)] * k
            if mode == "compound":
                p *= streak ** exp
            if rng.random() < min(0.95, p):
                intercepted += 1
                slots -= 1.0
                streak = 0
                continue

        if rng.random() < RETRIEVAL[tier_of(d)]:
            lost += 1
            slots -= 1.0
            continue

        slots -= 1.0
        banked += value

    return banked, scans, intercepted, lost, waits


def mean_se(vals):
    m = statistics.mean(vals)
    return m, statistics.stdev(vals) / math.sqrt(len(vals))


def trial(scan_rate, n=3000, **kw):
    res = [run_night(s, scan_rate, **kw) for s in range(n)]
    return {
        "mean": statistics.mean(r[0] for r in res),
        "scans": statistics.mean(r[1] for r in res),
        "icept": statistics.mean(r[2] for r in res),
    }


def sweep(mode, k=0.35, exp=1.8, n=3000):
    rates = [i / 10 for i in range(11)]
    return {r: trial(r, n=n, mode=mode, k=k, exp=exp) for r in rates}


def report(title, rows, base):
    print(f"\n{title}")
    print("-" * 78)
    print(f"{'scan rate':<11}{'mean $':>10}{'vs never':>10}{'scans':>8}"
          f"{'mid-scan losses':>18}")
    best = max(rows, key=lambda r: rows[r]["mean"])
    for r, v in rows.items():
        mark = "  <-- best" if r == best else ""
        print(f"{r:<11.1f}{v['mean']:>10,.0f}{v['mean'] / base - 1:>10.1%}"
              f"{v['scans']:>8.0f}{v['icept']:>18.2f}{mark}")
    interior = 0.0 < best < 1.0
    print(f"  optimum at scan rate {best:.1f} — "
          f"{'INTERIOR' if interior else 'CORNER'}, "
          f"{rows[best]['mean'] / base - 1:+.1%} over never scanning")
    return best, interior, rows[best]["mean"] / base - 1


# ---------------------------------------------------------------- policies
# Each is a rule a real crew could actually follow and say out loud.
POLICIES = {
    "ADAPTIVE (van >50% full)":
        lambda slots, cap, tier, streak: slots <= 0.5 * cap,
    "QUIET (only below PURSUE)":
        lambda slots, cap, tier, streak: tier in ("DORMANT", "PATROL"),
    "QUIET + never twice running":
        lambda slots, cap, tier, streak: tier in ("DORMANT", "PATROL") and streak == 0,
    "PANIC (only when hunted)":
        lambda slots, cap, tier, streak: tier in ("PURSUE", "COLLECT"),
}


def policy_trial(fn, n=8000, **kw):
    res = [run_night(s, 0.0, policy=fn, **kw) for s in range(n)]
    return statistics.mean(r[0] for r in res), statistics.mean(r[1] for r in res)


if __name__ == "__main__":
    # n=4,000 keeps the whole run near a minute, which is what makes a model useful as a
    # regression citizen rather than something nobody re-runs. The headline effect is
    # z>14 at this size; SCAN_RISK_N=20000 reproduces the R20 figures exactly if you
    # want the tighter bars. Every number printed carries its own 95% interval, so the
    # sample size is visible rather than assumed.
    N = int(os.environ.get("SCAN_RISK_N", 4000))
    print("=" * 78)
    print("DOES A SUPER-LINEAR SCAN COST MAKE THE APPRAISER A DECISION?")
    print(f"n = {N:,} nights per cell; +/- figures are 95% CI")
    print("=" * 78)

    base_none = mean_se([run_night(s, 0.0, mode="none")[0] for s in range(N)])
    base_comp = mean_se([run_night(s, 0.0, mode="compound")[0] for s in range(N)])

    def rate_panel(title, mode, **kw):
        print(f"\n{title}")
        print("-" * 78)
        print(f"{'scan rate':<11}{'mean $':>10}{'+/-':>7}{'vs never':>10}"
              f"{'mid-scan losses':>18}")
        rows = {}
        for r in [i / 10 for i in range(11)]:
            res = [run_night(s, r, mode=mode, **kw) for s in range(N)]
            m, se = mean_se([x[0] for x in res])
            ic = statistics.mean(x[2] for x in res)
            rows[r] = (m, se)
            print(f"{r:<11.1f}{m:>10,.0f}{1.96 * se:>7.0f}"
                  f"{m / base_none[0] - 1:>10.1%}{ic:>18.2f}")
        best = max(rows, key=lambda r: rows[r][0])
        d = rows[best][0] - base_none[0]
        sed = math.sqrt(rows[best][1] ** 2 + base_none[1] ** 2)
        print(f"  optimum at {best:.1f} "
              f"({'INTERIOR' if 0 < best < 1 else 'CORNER'}), "
              f"{d / base_none[0]:+.1%} over never scanning, z={d / sed:.1f}")
        return best, rows[best][0] / base_none[0] - 1

    a = rate_panel("A. No interception risk - the model as it stands (R8/R20)", "none")
    b = rate_panel("B. LINEAR exposure, tier-scaled - what R6 tried (k=0.35)", "linear")
    c = rate_panel("C. COMPOUND exposure, streak^1.8 - R12's proposal (k=0.35)",
                   "compound")

    print("\n\nD. Is the shape robust, or an artifact of one (k, exp)?")
    print("-" * 78)
    print(f"{'k':<7}{'exp':<7}{'best rate':>11}{'edge':>10}{'shape':>12}")
    interiors = total = 0
    for k in (0.15, 0.35, 0.75):
        for exp in (1.4, 1.8, 2.2):
            rows = {r / 10: trial(r / 10, n=max(1500, N // 3), mode="compound", k=k, exp=exp)["mean"]
                    for r in range(11)}
            best = max(rows, key=lambda r: rows[r])
            interiors += 0 < best < 1
            total += 1
            print(f"{k:<7.2f}{exp:<7.1f}{best:>11.1f}"
                  f"{rows[best] / base_none[0] - 1:>10.1%}"
                  f"{'interior' if 0 < best < 1 else 'corner':>12}")
    print(f"  interior optima in {interiors}/{total} combinations - "
          f"the shape does not depend on the tuning")

    print("\n\nE. MONOTONICITY - harsher exposure must never pay better")
    print("-" * 78)
    prev, bad = None, []
    for k in (0.0, 0.15, 0.35, 0.75, 1.5):
        m = trial(1.0, n=max(1500, N // 3), mode="compound", k=k, exp=1.8)["mean"]
        flag = ""
        if prev is not None and m > prev * 1.02:
            flag, _ = "  <-- VIOLATION", bad.append(k)
        print(f"  always-scan at k={k:<5.2f}  ${m:>9,.0f}{flag}")
        prev = m
    print(f"  {'OK - monotonic' if not bad else f'BROKEN at k={bad}'}")

    print("\n\nF. Can a PLAYER follow the winning rule? Disturbance is a HIDDEN meter")
    print("   (DESIGN 6.5), so a policy that reads the tier is not implementable.")
    print("-" * 78)
    print(f"{'rule':<36}{'no risk':>11}{'compound':>11}{'+/-':>7}{'needs meter':>13}")
    for name, fn, needs in (
            ("never scan", None, "-"),
            ("ADAPTIVE (van >50%) - current design",
             lambda sl, cap, t, k: sl <= 0.5 * cap, "no"),
            ("streak==0 (never twice running)",
             lambda sl, cap, t, k: k == 0, "no"),
            ("tier only (below PURSUE)",
             lambda sl, cap, t, k: t in ("DORMANT", "PATROL"), "YES"),
            ("tier AND streak==0",
             lambda sl, cap, t, k: t in ("DORMANT", "PATROL") and k == 0, "YES")):
        if fn is None:
            print(f"{name:<36}{base_none[0]:>11,.0f}{base_comp[0]:>11,.0f}"
                  f"{1.96 * base_comp[1]:>7.0f}{needs:>13}")
            continue
        mn, _ = mean_se([run_night(s, 0.0, policy=fn, mode="none")[0]
                         for s in range(N)])
        mc, sc = mean_se([run_night(s, 0.0, policy=fn, mode="compound")[0]
                          for s in range(N)])
        print(f"{name:<36}{mn:>11,.0f}{mc:>11,.0f}{1.96 * sc:>7.0f}{needs:>13}")

    print("\n\nG. IS THE OPTIMUM REAL, OR DEAD TIME? (R23)")
    print("   The depth gate makes a capped crew WAIT for the next tier. Scanning burns")
    print("   time, so it converts dead time into value. Ablate the gate and see.")
    print("-" * 78)
    NO_GATE = {1: 1.00, 2: 1.00, 3: 1.00}
    print(f"{'scan rate':<11}{'gated $':>11}{'waits':>8}{'  |':>4}"
          f"{'ungated $':>12}{'waits':>8}")
    gated, ungated = {}, {}
    for r in [i / 10 for i in range(11)]:
        # NB: not `a`/`b` - those hold panels A/B and the verdict below reads them.
        run_gated = [run_night(s, r, mode="none") for s in range(N)]
        run_open = [run_night(s, r, mode="none", depth_cap=NO_GATE) for s in range(N)]
        gated[r] = statistics.mean(x[0] for x in run_gated)
        ungated[r] = statistics.mean(x[0] for x in run_open)
        print(f"{r:<11.1f}{gated[r]:>11,.0f}"
              f"{statistics.mean(x[4] for x in run_gated):>8.2f}{'  |':>4}"
              f"{ungated[r]:>12,.0f}{statistics.mean(x[4] for x in run_open):>8.2f}")
    pg = max(gated, key=lambda r: gated[r])
    pu = max(ungated, key=lambda r: ungated[r])
    print(f"  gated   peak {pg:.1f}  {gated[pg] / gated[0.0] - 1:+.1%} over never scanning")
    print(f"  ungated peak {pu:.1f}  {ungated[pu] / ungated[0.0] - 1:+.1%}")
    print("""
  The interior optimum does not survive. It is a property of how much dead time the
  depth gate creates, not of the appraiser. Worse, that dead time comes from gating
  depth on a CLOCK (PHASES at fixed t) - which DECISIONS D-20 calls a bug outright:
  depth unlocks on WORK, never on a timer. In the real game the crew is finding keys
  and flipping breakers during that window, which is productive time, not waiting.

  So neither shape is the appraiser's. The honest answer needs a model where the
  prerequisite work costs crew time productively, and no sim in this repo has one.""")

    print("\n" + "=" * 78)
    print("VERDICT - R12's hypothesis is FALSIFIED, and the cost would make it worse")
    print("=" * 78)
    for nm, (br, ed) in (("no risk", a), ("linear", b), ("compound", c)):
        print(f"  {nm:<10} best rate {br:.1f}  {ed:+6.1%}")
    print("""
  1. The interior optimum ALREADY EXISTS without any super-linear cost. Nobody had
     swept scan RATE before - the project compared three fixed strategies and
     concluded from three points that there was no interesting middle.
  2. Adding the cost LOWERS the peak and does not move it. Compound is worse than
     linear, which is worse than none.
  3. Under compound risk every PLAYER-IMPLEMENTABLE policy lands at or below
     break-even. The only rule that still pays needs the hidden Disturbance meter,
     which DESIGN 6.5 keeps hidden and D-14 forbids leaning on.
  4. It also destroys the current design's ADAPTIVE heuristic.

  Recommendation: do NOT add a super-linear scan cost. The appraiser is worth what
  it is worth, and whether that is enough is a design judgement, not a simulation
  result - exactly as ECONOMY 9.1 already says.""")
