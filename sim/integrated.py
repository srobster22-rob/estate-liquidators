"""
Estate Liquidators — integrated night.

haul_sim.py found the appraiser's tuning target by sweeping a free "loss coefficient"
that stood in for how badly noise punishes you, and landed on 0.50-0.75. That was a
placeholder for a system that did not exist yet.

It exists now. R3/R4 rebuilt Disturbance as a fast-decaying noise level plus a
ratcheting floor, tuned to decay 50/min. So the punishment is no longer a free
parameter — it can be DERIVED. Appraising costs L=48 x 0.09 = +4.32 Disturbance, that
Disturbance drives the Curator's tier, and the tier drives how often it takes your
cargo off you.

The question: with real numbers instead of a stand-in, does scanning still pay?

Run: python integrated.py
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
RATCHET_END = 55.0          # floor climbs 0 -> 55 across the night
FLOOR_PER_CURSED = 7.0      # R9. Was hardcoded at 2.0 here until R17 - see LOOP_LOG

L = {"sprint": 45, "appraise": 48, "door": 60, "dolly": 35,
     "radio": 38, "break_small": 90}

# Per-trip chance the Curator relieves you of what you are carrying, by tier.
CANDIDATES = 4
SCAN_EXPOSURE = 0.0   # extra risk while stationary and scanning - LINEAR, and R6 showed
                      # a linear scan cost cannot open a band where selective wins wide

# R18 - the appraiser as a TAIL RISK, the shape R11 found for curses.
#
# Appraising holds you still for three seconds with your light on. The nth
# consecutive scan at one shelf is not as safe as the first: the Curator has had
# 3(n-1) more seconds of a stationary, loud, lit target in one place. Model that
# as a super-linear interception chance, scaled by how alert the house already is.
# A LINEAR cost gives a step function (R6, R10); only a super-linear one can
# produce an interior optimum, which is the whole lesson of R11.
SCAN_RISK_K = 0.0     # 0 = off, restoring the pre-R18 model exactly
SCAN_RISK_EXP = 1.8   # same exponent as the curse ruin curve, until measured otherwise

# Four players do not achieve 4x throughput: they collide in doorways, wait on each
# other, and re-walk ground. Without this the model has 2.6x more trips than van slots,
# which leaves so much slack that losing cargo is a FREE REROLL -- and rerolls help the
# picky strategy, so harsher punishment made scanning better. chain_sim.py measured a
# real crew at 20-24 extractions against 14 slots (~1.5x), so calibrate to that.
PARALLEL_EFFICIENCY = 0.65

RETRIEVAL = {"DORMANT": 0.00, "PATROL": 0.02, "PURSUE": 0.10, "COLLECT": 0.25}

# R22 - curses, in the same model as the appraiser for the first time.
#
# R11 measured the cursed-cargo decision (take two or three, then refuse) with
# perfect information about grades. R18 measured the appraiser's decision with
# the cursed count held at a constant. Neither could see the coupling, and the
# coupling is the interesting part: the grade IS the appraiser's readout, so the
# curse policy is only executable by a crew that scans.
GRADE_P = [("clean", 0.70), ("tainted", 0.22), ("malignant", 0.08)]
GRADE_MULT = {"clean": 1.0, "tainted": 2.5, "malignant": 6.0}
FEE = {"clean": 0.0, "tainted": 0.08, "malignant": 0.20}
ATT_MULT = {"clean": 1.0, "tainted": 1.5, "malignant": 3.0}
RUIN_K = 0.015
RUIN_EXP = 1.8

# DESIGN 4.2: a tainted item pulses your flashlight, a malignant one gains mass -
# so a blind crew finds out what it is holding shortly after picking it up, and
# can put it down again at the cost of the trip. Whether that tell exists is a
# DESIGN choice with a measurable price, so it is a parameter, not an assumption.
CARRY_TELL = True


def draw_grade(rng):
    r = rng.random()
    acc = 0.0
    for grade, p in GRADE_P:
        acc += p
        if r < acc:
            return grade
    return "clean"

TIERS = [(85, "COLLECT"), (60, "PURSUE"), (30, "PATROL"), (0, "DORMANT")]
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for start, ti in PHASES:
        if t >= start:
            tier = ti
    return tier


def scan_cap_of(strategy, slots, slots_total=VAN_SLOTS):
    """How many of the CANDIDATES items this policy examines at one shelf."""
    if strategy == "BLIND":
        return 0
    if strategy == "SCAN":
        return CANDIDATES
    if strategy == "ADAPTIVE":
        return CANDIDATES if slots <= 0.5 * slots_total else 0
    if strategy.startswith("CAP_"):     # scan at most N, then commit
        return int(strategy[4:])
    if strategy.startswith(("THRESH_", "SKIP_", "MARGIN_")):
        return CANDIDATES
    raise ValueError(strategy)


def run_night(seed, strategy, cursed=2, retrieval_scale=1.0, scan_risk_k=SCAN_RISK_K,
              curse_cap=None, carry_tell=CARRY_TELL, van_slots=VAN_SLOTS):
    """
    One night with Disturbance and the haul loop fully coupled.

    `curse_cap` is how many cursed pieces the crew will accept before refusing
    them (None = take whatever turns up, the pre-R22 behaviour). `cursed` is the
    old fixed-count knob and is only used when curse_cap is None, so every
    number this file printed before R22 still reproduces.
    """
    rng = random.Random(seed)
    d = 0.0
    t = 0.0
    slots = float(van_slots)
    banked = 0.0
    scans = 0
    lost = 0
    modelling_curses = curse_cap is not None
    cursed_aboard = 0
    gross = 0.0
    fees = 0.0

    # Depth budget. A crew that has run this estate type once knows the cellar beats
    # the foyer, and that knowledge has NOTHING to do with the appraiser — so every
    # strategy gets it. Without this, BLIND fills the van by t~200s, before tier 3 even
    # unlocks at 240s, and loses to SCAN purely because scanning wastes enough time to
    # accidentally wait for the good wings. That is a strawman, not a finding.
    # (Third time this exact myopia bug has appeared in this project. See LOOP_LOG R5.)
    TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}
    filled = 0.0

    while t < HAUL_S and slots > 0:
        tier = depth_at(t)
        trip_s, band = TIER_DATA[tier]
        per_trip = trip_s / (CREW * PARALLEL_EFFICIENCY)

        # Hold slots back for depth we know is coming.
        if filled >= TIER_CAP[tier] * van_slots and tier < 3:
            t += per_trip          # scout / stage instead of hauling junk
            continue

        candidates = [rng.uniform(*band) for _ in range(CANDIDATES)]
        grades = [draw_grade(rng) if modelling_curses else "clean"
                  for _ in range(CANDIDATES)]
        # A curse is worth taking: x6 before fees. The value the crew sees is the
        # marked-up one, so a cursed piece clears any bar a clean one would.
        if modelling_curses:
            candidates = [v * GRADE_MULT[g] for v, g in zip(candidates, grades)]
        cap = scan_cap_of(strategy, slots, van_slots)
        appraise = cap > 0

        cost = per_trip
        declined = False
        if strategy.startswith("MARGIN_"):
            # The policy a crew with an appraiser can actually run: judge an item
            # by what it ADDS, not by its sticker price. A cursed piece is worth
            # x6 AND raises the chance the collection takes the whole van, so its
            # marginal value falls as the van fills with curses. That arithmetic
            # is the reason the readout gives you value and grade in one breath.
            lo, hi = band
            bar = lo + (hi - lo) * int(strategy.split("_")[1]) / 100.0
            looked = 0
            value = None
            for c, g in zip(candidates, grades):
                looked += 1
                n = cursed_aboard + (0 if g == "clean" else 1)
                r_now = min(0.95, RUIN_K * cursed_aboard ** RUIN_EXP) if cursed_aboard else 0.0
                r_next = min(0.95, RUIN_K * n ** RUIN_EXP) if n else 0.0
                margin = c * (1 - FEE[g]) * (1 - r_next) - gross * (r_next - r_now)
                if margin >= bar:
                    value = c
                    break
            if value is None:
                declined = True
                value = max(candidates)
            cap = looked
            cost += 3.0 * looked / CREW
            scans += looked
        elif strategy.startswith(("THRESH_", "SKIP_")):
            # The appraiser as a REJECTION tool, which is what it is in the game:
            # it tells you a value, and the scarce resource is van slots, not shelf
            # choice. Keep looking until something clears the bar, then commit.
            lo, hi = band
            pct = int(strategy.split("_")[1])
            bar = lo + (hi - lo) * pct / 100.0
            looked = 0
            value = None
            for c in candidates:
                looked += 1
                if c >= bar:
                    value = c
                    break
            if value is None:
                # SKIP_p walks away with the slot unspent. The trip is gone either
                # way - time passes and the depth budget is consumed - so this is a
                # real cost, not the free reroll that corrupted R6 and R7.
                if strategy.startswith("SKIP_"):
                    declined = True
                value = max(candidates)     # THRESH_p commits to the best seen
            cap = looked
            cost += 3.0 * looked / CREW
            scans += looked
        elif appraise:
            # You examine `cap` of them and take the best one you looked at.
            value = max(candidates[:cap])
            cost += 3.0 * cap / CREW
            scans += cap
        else:
            value = rng.choice(candidates)

        # --- Disturbance over the span of this trip -------------------------
        span = cost
        floor = RATCHET_END * (t / NIGHT_S) + (
            cursed_aboard if modelling_curses else cursed) * FLOOR_PER_CURSED
        for _ in range(int(span)):
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

        # The appraiser's real cost: one loud ping per item examined.
        if appraise:
            d = min(100.0, d + cap * L["appraise"] * IMPULSE)

        # Caught mid-scan. Compounds with each consecutive scan at the shelf, and
        # only bites in proportion to how alert the house already is - scanning in
        # a DORMANT house is free, which is the point.
        caught = False
        if appraise and scan_risk_k > 0.0:
            alert = RETRIEVAL[tier_of(d)]
            for n in range(1, cap + 1):
                if rng.random() < scan_risk_k * (n ** SCAN_RISK_EXP) * alert:
                    caught = True
                    break

        t += cost
        if t > HAUL_S:
            break

        # A haul ATTEMPT consumes the opportunity whether or not it lands. Counting
        # only successes let a retrieval act as a free reroll against the depth budget,
        # which is why harsher punishment used to make the picky strategy richer.
        filled += 1.0

        if declined:
            continue

        if caught:
            lost += 1
            slots -= 1.0
            continue

        # Standing still to appraise is its own exposure, priced by current tier.
        if appraise and rng.random() < RETRIEVAL[tier_of(d)] * SCAN_EXPOSURE:
            lost += 1
            slots -= 1.0
            continue

        # --- did it take the cargo? -----------------------------------------
        if rng.random() < RETRIEVAL[tier_of(d)] * retrieval_scale:
            lost += 1
            slots -= 1.0
            continue

        if modelling_curses:
            picked = candidates.index(value)
            grade = grades[picked]
            over_cap = grade != "clean" and cursed_aboard >= curse_cap

            # Refusing a curse requires KNOWING it is one. The appraiser reads the
            # grade out; a blind crew only learns from the carry tell, and only
            # after it has spent the trip picking the thing up.
            if over_cap and (appraise or carry_tell):
                slots += 0.0        # the slot survives; the trip does not
                continue

            if grade != "clean":
                cursed_aboard += 1
            gross += value
            fees += value * FEE[grade]
            # Aggro scales with what you are carrying (TECH-SPEC A3), so a cursed
            # piece is more likely to be taken off you on the way out.
            if rng.random() < RETRIEVAL[tier_of(d)] * (ATT_MULT[grade] - 1.0) * 0.5:
                lost += 1
                slots -= 1.0
                gross -= value
                fees -= value * FEE[grade]
                if grade != "clean":
                    cursed_aboard -= 1
                continue

        slots -= 1.0
        banked += value

    if modelling_curses:
        ruined = cursed_aboard > 0 and rng.random() < min(
            0.95, RUIN_K * cursed_aboard ** RUIN_EXP)
        banked = 0.0 if ruined else gross - fees

    return (banked, scans, lost, d, van_slots - slots, filled, t,
            cursed_aboard, 1.0 if (modelling_curses and banked == 0.0) else 0.0)


def trial(strategy, n=2500, **kw):
    res = [run_night(s, strategy, **kw) for s in range(n)]
    return {
        "mean": statistics.mean(r[0] for r in res),
        "scans": statistics.mean(r[1] for r in res),
        "lost": statistics.mean(r[2] for r in res),
        "endD": statistics.mean(r[3] for r in res),
        # Is the van or the clock binding? A policy that can decline items is only
        # honestly priced if trips are scarce - otherwise walking away is the free
        # reroll that corrupted every punishment sweep from R6 to R8.
        "used": statistics.mean(r[4] for r in res),
        "trips": statistics.mean(r[5] for r in res),
        "ranout": sum(1 for r in res if r[6] >= HAUL_S) / len(res),
        # R22: how much of the van is cursed, and how often the collection takes
        # it all back. A policy that seeks value is seeking curses, because the
        # curses ARE the valuable items.
        "cursed": statistics.mean(r[7] for r in res),
        "ruined": statistics.mean(r[8] for r in res),
    }


if __name__ == "__main__":
    print("APPRAISER vs BLIND — noise cost DERIVED, not a free parameter")
    print("-" * 78)
    print(f"{'strategy':<12}{'mean $':>10}{'scans':>8}{'lost':>7}{'end D':>8}"
          f"{'vs BLIND':>11}")
    base = trial("BLIND")
    for s in ("BLIND", "ADAPTIVE", "SCAN"):
        r = trial(s)
        print(f"{s:<12}{r['mean']:>10,.0f}{r['scans']:>8.0f}{r['lost']:>7.1f}"
              f"{r['endD']:>8.0f}{r['mean'] / base['mean'] - 1:>11.1%}")

    print("\n\nR18 — THE POLICY SPACE WAS TOO SMALL")
    print("Every earlier round asked 'do you scan?'. The appraiser's actual job is to let")
    print("you REFUSE things: it reads a value, and the scarce resource is van slots.")
    print("CAP_n scans n items and commits. THRESH_p keeps looking until something clears")
    print("the p-th percentile of the tier band. SKIP_p does the same but WALKS AWAY when")
    print("nothing does — spending the trip, keeping the slot.")
    print("-" * 78)
    print(f"{'policy':<12}{'mean $':>10}{'scans':>8}{'lost':>7}{'slots':>8}"
          f"{'trips':>8}{'no time':>9}{'vs BLIND':>11}")
    for s in ("BLIND", "CAP_1", "CAP_2", "CAP_3", "SCAN", "ADAPTIVE",
              "THRESH_50", "SKIP_50", "SKIP_70", "SKIP_85"):
        r = trial(s)
        print(f"{s:<12}{r['mean']:>10,.0f}{r['scans']:>8.1f}{r['lost']:>7.1f}"
              f"{r['used']:>8.1f}{r['trips']:>8.1f}{r['ranout']:>9.0%}"
              f"{r['mean'] / base['mean'] - 1:>11.1%}")
    print("\nThe van binds until you get picky; then the clock does. SKIP_85 ends 99% of")
    print("nights out of time with 8.6 of 14 slots empty, which is why being too choosy")
    print("costs more than never choosing at all.")

    print("\n\nDOES A TAIL-RISK SCAN COST CREATE THE DECISION?  (R11's lesson, applied)")
    print("Caught mid-scan, compounding as k x n^%.1f x tier alertness." % SCAN_RISK_EXP)
    print("-" * 78)
    pols = ("BLIND", "CAP_2", "SCAN", "ADAPTIVE", "THRESH_50", "SKIP_50", "SKIP_70")
    print(f"{'risk k':<9}" + "".join(f"{p:>11}" for p in pols) + f"{'best':>11}")
    for k in (0.0, 0.02, 0.05, 0.10, 0.20):
        row = {p: trial(p, n=1500, scan_risk_k=k)["mean"] for p in pols}
        best = max(row, key=row.get)
        print(f"{k:<9.2f}" + "".join(f"{row[p]:>11,.0f}" for p in pols) + f"{best:>11}")
    print("\nBLIND is flat across the sweep and every scanning policy falls monotonically,")
    print("which is the sanity check R6-R8 kept failing. The optimum BAR moves with danger:")
    print("70th percentile in a quiet house, 50th once scanning is genuinely risky.")

    print("\n\nHOW HARSH DOES RETRIEVAL HAVE TO GET BEFORE SCANNING STOPS PAYING?")
    print("-" * 78)
    print(f"{'scale':<8}{'BLIND':>11}{'ADAPTIVE':>11}{'SCAN':>11}{'SKIP_50':>11}"
          f"{'best':>11}{'edge':>9}")
    for scale in (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
        rows = {s: trial(s, n=1200, retrieval_scale=scale)
                for s in ("BLIND", "ADAPTIVE", "SCAN", "SKIP_50")}
        best = max(rows, key=lambda k: rows[k]["mean"])
        edge = rows[best]["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{scale:<8.1f}{rows['BLIND']['mean']:>11,.0f}"
              f"{rows['ADAPTIVE']['mean']:>11,.0f}{rows['SCAN']['mean']:>11,.0f}"
              f"{rows['SKIP_50']['mean']:>11,.0f}{best:>11}{edge:>9.1%}")

    print("\n\nR22 — CURSES AND THE APPRAISER, IN ONE MODEL AT LAST")
    print("R11 measured the curse decision with grades known and the appraiser absent.")
    print("R18 measured the appraiser with the cursed count held constant. Neither could")
    print("see the coupling: a curse is worth x6, so THE CURSES ARE THE VALUABLE ITEMS,")
    print("and any policy that reaches for value is reaching for curses.")
    print("-" * 78)
    print(f"{'policy':<14}{'cap':>5}{'mean $':>10}{'cursed':>9}{'ruined':>9}"
          f"{'slots':>8}{'scans':>7}")
    for pol, cap in (("BLIND", 99), ("BLIND", 5), ("SKIP_50", 5), ("SKIP_70", 99),
                     ("SCAN", 5), ("MARGIN_20", 99), ("MARGIN_30", 99),
                     ("MARGIN_40", 99), ("MARGIN_30", 3)):
        r = trial(pol, n=1500, curse_cap=cap)
        print(f"{pol:<14}{cap:>5}{r['mean']:>10,.0f}{r['cursed']:>9.1f}"
              f"{r['ruined']:>9.0%}{r['used']:>8.1f}{r['scans']:>7.1f}")
    print("\nSticker-price greed is curse greed: SKIP_70 uncapped ends the night with 7.4")
    print("cursed pieces and loses the van 57% of the time. MARGIN_p judges each item by")
    print("what it ADDS - value net of fees and of the ruin it raises - and needs no cap at")
    print("all. Capping it makes it worse. One rule instead of two.")

    print("\n\nR26 — THE CONTRACT CHAIN, AGAINST THE CURRENT ECONOMY")
    print("ECONOMY 4's curve was calibrated before curses were in the earnings model.")
    print("Pass rate per night for a crew that REFUSES every curse, and one that takes")
    print("what pays. Quotas and van sizes from tuning.json.")
    print("-" * 78)
    import json as _json
    _prog = _json.loads((__import__("pathlib").Path(__file__).resolve().parent.parent
                         / "tuning.json").read_text())["progression"]
    QUOTAS, VANS = _prog["quotas"], _prog["van_by_night"]
    print(f"{'crew':<24}" + "".join(f"  night {i + 1}" for i in range(4)) + "    chain")
    for label, cap in (("careful (no curses)", 0), ("greedy (takes what pays)", 99)):
        rates = []
        for q, v in zip(QUOTAS, VANS):
            res = [run_night(s, "MARGIN_30", curse_cap=cap, van_slots=v)[0]
                   for s in range(1200)]
            rates.append(sum(1 for r in res if r >= q) / len(res))
        chain = 1.0
        for r in rates:
            chain *= r
        print(f"{label:<24}" + "".join(f"{r:>9.0%}" for r in rates) + f"{chain:>9.0%}")
    print("\nThe ruin lottery is a CEILING: a crew taking curses cannot pass more than")
    print("~74% of nights at any quota, because that is how often the van survives. The")
    print("intended 95% night-1 pass rate is reachable only by a crew that gambles with")
    print("nothing - which is the arc, and it is now the arc on purpose.")

    print("\n\nGREED: does hauling cursed cargo change the calculus?")
    print("-" * 78)
    print(f"{'cursed':<9}{'BLIND':>11}{'ADAPTIVE':>11}{'SCAN':>11}{'SKIP_50':>11}{'best':>11}")
    for c in (0, 2, 5, 8):
        rows = {s: trial(s, n=1200, cursed=c)
                for s in ("BLIND", "ADAPTIVE", "SCAN", "SKIP_50")}
        best = max(rows, key=lambda k: rows[k]["mean"])
        print(f"{c:<9}{rows['BLIND']['mean']:>11,.0f}"
              f"{rows['ADAPTIVE']['mean']:>11,.0f}{rows['SCAN']['mean']:>11,.0f}"
              f"{rows['SKIP_50']['mean']:>11,.0f}{best:>11}")
