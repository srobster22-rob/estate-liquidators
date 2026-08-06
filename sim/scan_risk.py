"""
Estate Liquidators — the appraiser as a tail risk.

R11 established the project's most-used lesson twice over: **when a benefit is
multiplicative, only a super-linear cost produces a decision.** A linear cost gives a
step function — always-take or never-take, with nothing interesting in between.

The appraiser has exactly that shape and nobody noticed. Scanning four candidates and
keeping the best is `E[max of 4]` instead of `E[uniform]` — roughly a **x1.35 multiplier
on every item you haul**, and it does not decay. Against it, every cost this project has
ever priced on scanning is *linear*: +4.32 Disturbance per ping (integrated.py), three
stationary seconds, a flat per-trip retrieval chance. So R5-R8's result was structurally
inevitable: SCAN dominates at designed values, ADAPTIVE only wins in the narrow crossover
band where scanning is *just barely* net-negative, and the whole thing lands on a thin
+6% edge that the owner correctly refused to sign off on.

This model replaces the linear scan cost with the shape that worked for curses:

    p(interrupted mid-scan) = INTERRUPT_K x streak^INTERRUPT_EXP x tier_weight

where `streak` is the number of **consecutive** scanning trips. The fiction is the whole
argument: one ping is a noise, two pings from the same room is a direction, three is a
fix. And the cost of an interrupt is not a fee either — the Curator takes the item, and
if it is already hunting it takes the player, who joins the collection for the rest of
the night. A dead crewmate does not just remove a quarter of the labour: **Disturbance
decay is crew-scaled** (R12, `50 x crew/4`), so the survivors' meter now falls slower,
which raises the tier, which raises the next interrupt roll. The spiral is derived from
two already-verified rules rather than invented for this model.

The question this answers: is there a policy between "never scan" and "always scan" that
beats both? If yes, the +6% question dissolves the same way the curse question did — the
answer was never the multiplier, it was the shape of the cost.

Run: python sim/scan_risk.py            (stdlib only, ~15s)
"""

import json
import pathlib
import random
import statistics

TUNING = json.loads(
    (pathlib.Path(__file__).resolve().parent.parent / "tuning.json")
    .read_text(encoding="utf-8"))

_N = TUNING["night"]
_D = TUNING["disturbance"]
_L = TUNING["loudness"]
_LC = TUNING["loudness_constants"]

CREW = _N["crew"]
NIGHT_S = float(_N["seconds"])
HAUL_S = float(_N["haul_window_seconds"])
APPRAISE_S = _N["appraise_seconds"]
VAN_SLOTS = TUNING["van"]["base_slots"]

IMPULSE = _LC["impulse_disturbance_per_l"]
SUSTAINED = _LC["sustained_disturbance_per_l"]
DECAY_AT_CREW4 = _D["decay_per_min_at_crew4"]
RATCHET_END = _D["ratchet_end"]
CURSED_FLOOR = _D["per_cursed_item_floor"]

RETRIEVAL = {"DORMANT": TUNING["retrieval"]["dormant"],
             "PATROL": TUNING["retrieval"]["patrol"],
             "PURSUE": TUNING["retrieval"]["pursue"],
             "COLLECT": TUNING["retrieval"]["collect"]}
TIERS = [(_D["tier_collect_at"], "COLLECT"), (_D["tier_pursue_at"], "PURSUE"),
         (_D["tier_patrol_at"], "PATROL"), (0.0, "DORMANT")]

CANDIDATES = 4
PARALLEL_EFFICIENCY = 0.65                      # R7
TIER_DATA = {1: (45.0, (80, 300)), 2: (60.0, (250, 700)), 3: (90.0, (600, 1400))}
PHASES = [(0.0, 1), (120.0, 2), (240.0, 3)]
TIER_CAP = {1: 0.40, 2: 0.75, 3: 1.00}          # depth reservation, R5

# --------------------------------------------------------- hypothesis 2: rooms
# Every model in this project has drawn all four candidates from one flat band, which
# hard-codes the appraiser's payoff as a single global constant. Real rooms are not
# flat: a shelf of identical encyclopaedias has almost no spread, a curio cabinet is
# a lottery. Scanning's benefit is E[max of 4] - E[random], which for a uniform spread
# of +/-s is exactly 0.6 x s x mean -- so the payoff is PROPORTIONAL to how varied the
# room is, and a flat band prices it at one number everywhere.
#
# If the room's spread is telegraphed by its dressing (D-10 already says value is
# legible in category), then "which rooms are worth scanning" is a real, readable,
# repeatable decision instead of a habit.
_RC = TUNING["appraiser"]["room_classes"]
ROOMS = [(k.upper(), _RC[k]["spread"], _RC[k]["share"])
         for k in ("shelf", "mixed", "curio")]  # books | furnished room | the lottery
ROOM_SCAN_SET = {"BLIND": set(),
                 "SCAN_ALL": {"SHELF", "MIXED", "CURIO"},
                 "CURIO_ONLY": {"CURIO"},
                 "CURIO_MIXED": {"CURIO", "MIXED"},
                 # Controls. RANDOM_25 scans the same FRACTION of rooms as CURIO_ONLY
                 # but ignores which ones -- if it wins too, the finding is only
                 # "scan less often" and the room telegraph adds nothing to the game.
                 # SHELF_ONLY is the same fraction spent on the wrong rooms.
                 "RANDOM_25": None,
                 "SHELF_ONLY": {"SHELF"}}


def draw_room(rng):
    r = rng.random()
    acc = 0.0
    for name, spread, w in ROOMS:
        acc += w
        if r <= acc:
            return name, spread
    return ROOMS[-1][0], ROOMS[-1][1]

# ---------------------------------------------------------------- the new cost
# Interrupt risk while stationary and scanning. Super-linear in CONSECUTIVE scans.
INTERRUPT_K = 0.030
INTERRUPT_EXP = 1.8                             # same exponent as the curse ruin curve
INTERRUPT_TIER_W = {"DORMANT": 0.0, "PATROL": 0.30, "PURSUE": 1.00, "COLLECT": 2.00}
# If it arrives while it is already hunting, it does not stop at the vase.
DEATH_ON_INTERRUPT = {"DORMANT": 0.00, "PATROL": 0.00, "PURSUE": 0.15, "COLLECT": 0.40}
INTERRUPT_FLOOR_BUMP = 4.0                      # a scene that loud does not un-happen


def tier_of(d):
    return next(n for thr, n in TIERS if d >= thr)


def depth_at(t):
    tier = 1
    for start, ti in PHASES:
        if t >= start:
            tier = ti
    return tier


def wants_scan(policy, streak, tier_name, slots):
    if policy == "BLIND":
        return False
    if policy == "SCAN_ALL":
        return True
    if policy == "QUIET":                       # read the room, ignore the streak
        return tier_name in ("DORMANT", "PATROL")
    if policy.startswith("BURST_"):             # k consecutive, then one quiet trip
        return streak < int(policy.split("_")[1])
    if policy == "ADAPTIVE":                    # integrated.py's policy, for comparison
        return slots <= 0.5 * VAN_SLOTS
    raise ValueError(policy)


def run_night(seed, policy, cursed=2, interrupt_k=INTERRUPT_K, rooms=False):
    rng = random.Random(seed)
    d, t, filled = 0.0, 0.0, 0.0
    slots = float(VAN_SLOTS)
    banked = 0.0
    crew = CREW
    streak = 0
    scans = interrupts = deaths = lost = 0

    while t < HAUL_S and slots > 0 and crew > 0:
        depth = depth_at(t)
        trip_s, band = TIER_DATA[depth]
        per_trip = trip_s / (crew * PARALLEL_EFFICIENCY)

        if filled >= TIER_CAP[depth] * VAN_SLOTS and depth < 3:
            t += per_trip
            continue

        tname = tier_of(d)
        if rooms:
            room, spread = draw_room(rng)
            mean = rng.uniform(*band)
            # A worthless thing is worth ~nothing, not a negative amount; floor at 5%
            # of the room mean so wide spreads stay a lottery rather than a debt.
            candidates = [max(0.05 * mean, mean * rng.uniform(1 - spread, 1 + spread))
                          for _ in range(CANDIDATES)]
            wanted = ROOM_SCAN_SET[policy]
            appraise = (rng.random() < 0.25) if wanted is None else (room in wanted)
        else:
            appraise = wants_scan(policy, streak, tname, slots)
            candidates = [rng.uniform(*band) for _ in range(CANDIDATES)]

        cost = per_trip
        if appraise:
            value = max(candidates)
            cost += APPRAISE_S * CANDIDATES / crew
            scans += CANDIDATES
            streak += 1
        else:
            value = rng.choice(candidates)
            streak = 0

        # --- Disturbance across the trip, decay scaled by SURVIVING crew (R12) ---
        floor = RATCHET_END * (t / NIGHT_S) + cursed * CURSED_FLOOR
        decay_s = DECAY_AT_CREW4 * (crew / 4.0) / 60.0
        for _ in range(int(cost)):
            for _ in range(crew):
                if rng.random() < 0.04:
                    d += _L["sprint"] * SUSTAINED
            if rng.random() < 0.15:
                d += _L["dolly"] * SUSTAINED
            if rng.random() < 0.08:
                d += _L["radio"] * SUSTAINED
            if rng.random() < 0.055:
                d += _L["door"] * IMPULSE
            if rng.random() < 0.006:
                d += _L["break_small"] * IMPULSE
            d = max(floor, min(100.0, d - decay_s))

        if appraise:
            d = min(100.0, d + CANDIDATES * _L["appraise"] * IMPULSE)

        t += cost
        if t > HAUL_S:
            break
        filled += 1.0                           # an ATTEMPT spends the opportunity (R8)

        # --- the tail risk -------------------------------------------------
        if appraise:
            tn = tier_of(d)
            p = interrupt_k * (streak ** INTERRUPT_EXP) * INTERRUPT_TIER_W[tn]
            if rng.random() < min(1.0, p):
                interrupts += 1
                lost += 1
                slots -= 1.0
                d = min(100.0, d + INTERRUPT_FLOOR_BUMP)
                streak = 0
                if rng.random() < DEATH_ON_INTERRUPT[tn]:
                    deaths += 1
                    crew -= 1                   # joins the collection; decay slows
                continue

        if rng.random() < RETRIEVAL[tier_of(d)]:
            lost += 1
            slots -= 1.0
            continue

        slots -= 1.0
        banked += value

    return banked, scans, lost, interrupts, deaths, d


def trial(policy, n=2000, **kw):
    res = [run_night(s, policy, **kw) for s in range(n)]
    return {"mean": statistics.mean(r[0] for r in res),
            "scans": statistics.mean(r[1] for r in res),
            "lost": statistics.mean(r[2] for r in res),
            "intr": statistics.mean(r[3] for r in res),
            "deaths": statistics.mean(r[4] for r in res),
            "endD": statistics.mean(r[5] for r in res)}


POLICIES = ("BLIND", "BURST_1", "BURST_2", "BURST_3", "BURST_5", "QUIET",
            "ADAPTIVE", "SCAN_ALL")


def table(title, rows, base_key="BLIND"):
    print(f"\n{title}")
    print("-" * 78)
    print(f"{'policy':<11}{'mean $':>10}{'scans':>7}{'lost':>7}{'intr':>7}"
          f"{'deaths':>8}{'end D':>7}{'vs BLIND':>11}")
    base = rows[base_key]["mean"]
    for p in POLICIES:
        r = rows[p]
        print(f"{p:<11}{r['mean']:>10,.0f}{r['scans']:>7.0f}{r['lost']:>7.1f}"
              f"{r['intr']:>7.2f}{r['deaths']:>8.2f}{r['endD']:>7.0f}"
              f"{r['mean'] / base - 1:>11.1%}")
    best = max(POLICIES, key=lambda p: rows[p]["mean"])
    print(f"  best: {best}  ({rows[best]['mean'] / base - 1:+.1%} over BLIND)")
    return best


if __name__ == "__main__":
    print("THE APPRAISER AS A TAIL RISK — is there an interior optimum?")
    print("=" * 78)
    print(f"interrupt p = {INTERRUPT_K} x streak^{INTERRUPT_EXP} x tier_weight,"
          f"  death on interrupt at PURSUE/COLLECT")

    rows = {p: trial(p) for p in POLICIES}
    table("DESIGNED VALUES", rows)

    print("\n\nCONTROL: interrupt_k = 0 reproduces the old LINEAR world")
    print("(if BURST/QUIET still win here, the finding is an artifact of the policies,")
    print(" not of the cost shape — this is the check that would falsify the result)")
    rows0 = {p: trial(p, n=1200, interrupt_k=0.0) for p in POLICIES}
    table("interrupt_k = 0.000", rows0)

    print("\n\nSWEEP: where does the optimum move as the tail gets fatter?")
    print("-" * 78)
    print(f"{'k':<8}{'BLIND':>10}{'BURST_1':>10}{'BURST_2':>10}{'BURST_3':>10}"
          f"{'SCAN_ALL':>10}{'best':>10}{'edge':>8}")
    for k in (0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.20):
        rk = {p: trial(p, n=900, interrupt_k=k) for p in POLICIES}
        best = max(POLICIES, key=lambda p: rk[p]["mean"])
        edge = rk[best]["mean"] / rk["BLIND"]["mean"] - 1
        print(f"{k:<8.3f}{rk['BLIND']['mean']:>10,.0f}{rk['BURST_1']['mean']:>10,.0f}"
              f"{rk['BURST_2']['mean']:>10,.0f}{rk['BURST_3']['mean']:>10,.0f}"
              f"{rk['SCAN_ALL']['mean']:>10,.0f}{best:>10}{edge:>8.1%}")

    print("\n\nGREED INTERACTION: cursed cargo raises the floor, which raises the tier,")
    print("which raises every interrupt roll. Does the right scan policy change?")
    print("-" * 78)
    print(f"{'cursed':<8}{'BLIND':>10}{'BURST_1':>10}{'BURST_2':>10}{'BURST_3':>10}"
          f"{'SCAN_ALL':>10}{'best':>10}")
    for c in (0, 2, 3, 5):
        rc = {p: trial(p, n=900, cursed=c) for p in POLICIES}
        best = max(POLICIES, key=lambda p: rc[p]["mean"])
        print(f"{c:<8}{rc['BLIND']['mean']:>10,.0f}{rc['BURST_1']['mean']:>10,.0f}"
              f"{rc['BURST_2']['mean']:>10,.0f}{rc['BURST_3']['mean']:>10,.0f}"
              f"{rc['SCAN_ALL']['mean']:>10,.0f}{best:>10}")

    # ================================================================= rooms
    print("\n\n" + "=" * 78)
    print("HYPOTHESIS 2 — the payoff is not a constant, it is a property of the ROOM")
    print("=" * 78)
    print("No tail risk here (hypothesis 1 is dead). Same linear noise cost as")
    print("integrated.py. The only change: candidate spread varies by room class, and")
    print("the class is visible before you decide to scan.")
    print("-" * 78)
    rp = ("BLIND", "RANDOM_25", "SHELF_ONLY", "CURIO_ONLY", "CURIO_MIXED", "SCAN_ALL")
    print(f"{'policy':<13}{'mean $':>10}{'scans':>7}{'lost':>7}{'end D':>8}"
          f"{'vs BLIND':>11}")
    rr = {p: trial(p, n=2500, interrupt_k=0.0, rooms=True) for p in rp}
    for p in rp:
        r = rr[p]
        print(f"{p:<13}{r['mean']:>10,.0f}{r['scans']:>7.0f}{r['lost']:>7.1f}"
              f"{r['endD']:>8.0f}{r['mean'] / rr['BLIND']['mean'] - 1:>11.1%}")
    best = max(rp, key=lambda p: rr[p]["mean"])
    print(f"  best: {best}  ({rr[best]['mean'] / rr['BLIND']['mean'] - 1:+.1%} "
          f"over BLIND)")

    print("\nSENSITIVITY: how wide does the curio spread have to be to carry it?")
    print("(SHELF and MIXED held at 0.10 / 0.40; only the lottery room moves)")
    print("-" * 78)
    print(f"{'curio s':<10}{'BLIND':>11}{'CURIO_ONLY':>12}{'CURIO_MIXED':>13}"
          f"{'SCAN_ALL':>11}{'best':>13}{'edge':>8}")
    saved = ROOMS[2]
    for s in (0.4, 0.7, 1.1, 1.5, 1.9):
        ROOMS[2] = ("CURIO", s, saved[2])
        rs = {p: trial(p, n=1200, interrupt_k=0.0, rooms=True) for p in rp}
        b = max(rp, key=lambda p: rs[p]["mean"])
        print(f"{s:<10.2f}{rs['BLIND']['mean']:>11,.0f}"
              f"{rs['CURIO_ONLY']['mean']:>12,.0f}{rs['CURIO_MIXED']['mean']:>13,.0f}"
              f"{rs['SCAN_ALL']['mean']:>11,.0f}{b:>13}"
              f"{rs[b]['mean'] / rs['BLIND']['mean'] - 1:>8.1%}")
    ROOMS[2] = saved

    print("\nMIX SENSITIVITY: how rare can the lottery room be before scanning dies?")
    print("-" * 78)
    print(f"{'curio %':<10}{'BLIND':>11}{'CURIO_ONLY':>12}{'CURIO_MIXED':>13}"
          f"{'SCAN_ALL':>11}{'best':>13}{'edge':>8}")
    base_rooms = list(ROOMS)
    for w in (0.10, 0.15, 0.25, 0.40):
        ROOMS[0] = ("SHELF", 0.10, 0.30 + (0.25 - w) / 2)
        ROOMS[1] = ("MIXED", 0.40, 0.45 + (0.25 - w) / 2)
        ROOMS[2] = ("CURIO", 1.10, w)
        rs = {p: trial(p, n=1200, interrupt_k=0.0, rooms=True) for p in rp}
        b = max(rp, key=lambda p: rs[p]["mean"])
        print(f"{w:<10.0%}{rs['BLIND']['mean']:>11,.0f}"
              f"{rs['CURIO_ONLY']['mean']:>12,.0f}{rs['CURIO_MIXED']['mean']:>13,.0f}"
              f"{rs['SCAN_ALL']['mean']:>11,.0f}{b:>13}"
              f"{rs[b]['mean'] / rs['BLIND']['mean'] - 1:>8.1%}")
    ROOMS[:] = base_rooms
