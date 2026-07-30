"""
Estate Liquidators — haul-loop Monte Carlo.

The question this exists to answer:

    Does using the appraiser beat ignoring it?

DESIGN.md 4.4 says the whole game rests on "yes", and DECISIONS.md D-10 says the
mechanic is dead if the answer is "no". The core of that question is arithmetic, not
taste, so it can be settled before anyone builds anything.

MODEL
  A night is a sequence of trips. On each trip a player reaches a shelf holding k
  candidate items, chooses one, and hauls it to the van. Appraising costs 3s per item
  examined and reveals that item's value.

    BLIND     take a random candidate. Zero time cost, zero information.
    SCAN_ALL  appraise all k (3k seconds), take the most valuable.
    ADAPTIVE  haul blind while the van has free slots; once it is full, start
              appraising, because from then on the only way to improve is to swap.

  The van does NOT reveal the value of unappraised cargo (see note in report). So a
  blind crew cannot optimise swaps: it can only replace at random, which in
  expectation does nothing.

DELIBERATE OMISSIONS
  No Curator, no Disturbance, no deaths, no breakage. Every one of those *raises* the
  cost of standing still to appraise, so this model is generous to the appraiser. If
  scanning loses here, it loses worse in the real game.
"""

import random
import statistics

# ---------------------------------------------------------------- parameters

HAUL_WINDOW_S = 540.0        # ECONOMY.md 2
APPRAISE_S = 3.0             # DESIGN.md 4.1
CREW = 4
VAN_SLOTS = 14               # ECONOMY.md 1
CANDIDATES_PER_SHELF = 4     # items to choose between at a given shelf

# Noise. AUDIO-SPEC 1.2: an appraiser ping is L=48, so +4.3 Disturbance; sprinting a
# trip is L=45 sustained, call it +2.0 per trip. RISK_COEF scales Disturbance into a
# per-trip chance the Curator relieves you of what you are carrying.
DISTURBANCE_PER_SCAN = 4.3
DISTURBANCE_PER_TRIP = 2.0
DISTURBANCE_DECAY_PER_TRIP = 1.0
RISK_COEF = 0.0              # 0 = the risk-free model; swept in __main__

TIERS = {
    # tier: (round-trip seconds, value band, unlock time)
    1: (45.0, (80, 300), 0.0),
    2: (60.0, (250, 700), 120.0),
    3: (90.0, (600, 1400), 240.0),
}


def available_tiers(t):
    return [k for k, (_, _, unlock) in TIERS.items() if t >= unlock]


def deepest_available(t):
    return max(available_tiers(t))


class Van:
    """Cargo hold. Knows appraised values; unappraised items are opaque."""

    def __init__(self, slots):
        self.slots = slots
        self.cargo = []   # list of (value, known)

    def full(self):
        return len(self.cargo) >= self.slots

    def add(self, value, known):
        self.cargo.append((value, known))

    def try_swap(self, value, known):
        """Replace the worst KNOWN item if the newcomer beats it.

        An unappraised newcomer has no basis for comparison, and unappraised cargo
        cannot be identified as the worst. A blind crew therefore cannot swap at all.
        """
        if not known:
            return False
        known_cargo = [(v, i) for i, (v, k) in enumerate(self.cargo) if k]
        if not known_cargo:
            return False
        worst_v, worst_i = min(known_cargo)
        if value > worst_v:
            self.cargo[worst_i] = (value, True)
            return True
        return False

    def total(self):
        return sum(v for v, _ in self.cargo)


def run_night(strategy, seed=None):
    rng = random.Random(seed)
    van = Van(VAN_SLOTS)
    scans = 0
    taken = 0
    trips = [0]         # boxed so the inner loop can increment them
    disturbance = [0.0] # shared across the crew — it is one house

    # Each crew member runs their own clock over the same shared van.
    for _ in range(CREW):
        t = 0.0
        while t < HAUL_WINDOW_S:
            tier = deepest_available(t)
            trip_s, band, _ = TIERS[tier]

            candidates = [rng.uniform(*band) for _ in range(CANDIDATES_PER_SHELF)]

            if strategy == "BLIND":
                appraise = False
            elif strategy == "SCAN_ALL":
                appraise = True
            elif strategy == "ADAPTIVE":
                # Start appraising BEFORE the van fills, not after. Appraising only
                # once full is a trap: every item already aboard is unappraised, so
                # there is nothing to compare a swap against and the crew can never
                # climb out. Threshold at 70% leaves a known floor to swap against.
                appraise = len(van.cargo) >= 0.70 * van.slots
            else:
                raise ValueError(strategy)

            cost = trip_s
            if appraise:
                cost += APPRAISE_S * CANDIDATES_PER_SHELF
                value = max(candidates)
                scans += CANDIDATES_PER_SHELF
            else:
                value = rng.choice(candidates)

            if t + cost > HAUL_WINDOW_S:
                break
            t += cost
            trips[0] += 1

            # Noise accrues, then decays a little each trip (DESIGN.md 6.5).
            disturbance[0] += DISTURBANCE_PER_TRIP
            if appraise:
                disturbance[0] += DISTURBANCE_PER_SCAN * CANDIDATES_PER_SHELF
            disturbance[0] = max(0.0, min(100.0,
                                          disturbance[0] - DISTURBANCE_DECAY_PER_TRIP))

            # Retrieval: the Curator takes what you are carrying before you reach the
            # van. The trip is spent, the item is gone.
            if rng.random() < RISK_COEF * disturbance[0] / 100.0:
                continue

            if not van.full():
                van.add(value, appraise)
                taken += 1
            else:
                if van.try_swap(value, appraise):
                    taken += 1

    return van.total(), taken, scans, trips[0]


def trial(strategy, n=4000):
    results = [run_night(strategy, seed=i) for i in range(n)]
    totals = [r[0] for r in results]
    return {
        "strategy": strategy,
        "mean": statistics.mean(totals),
        "median": statistics.median(totals),
        "p10": sorted(totals)[n // 10],
        "p90": sorted(totals)[9 * n // 10],
        "items": statistics.mean(r[1] for r in results),
        "scans": statistics.mean(r[2] for r in results),
        "trips": statistics.mean(r[3] for r in results),
    }


def report(rows, title):
    print(f"\n{title}")
    print("-" * 78)
    print(f"{'strategy':<10}{'mean $':>10}{'median':>10}{'p10':>10}"
          f"{'p90':>10}{'trips':>9}{'taken':>9}{'scans':>9}")
    for r in rows:
        print(f"{r['strategy']:<10}{r['mean']:>10,.0f}{r['median']:>10,.0f}"
              f"{r['p10']:>10,.0f}{r['p90']:>10,.0f}{r['trips']:>9.1f}"
              f"{r['items']:>9.1f}{r['scans']:>9.1f}")
    best = max(rows, key=lambda r: r["mean"])
    blind = next(r for r in rows if r["strategy"] == "BLIND")
    print(f"\n  best: {best['strategy']}  "
          f"({best['mean'] / blind['mean'] - 1:+.1%} vs BLIND)")


if __name__ == "__main__":
    strategies = ["BLIND", "SCAN_ALL", "ADAPTIVE"]

    report([trial(s) for s in strategies],
           f"BASELINE — van {VAN_SLOTS} slots, {CREW} crew, {HAUL_WINDOW_S:.0f}s")

    # Does the appraiser's value depend on the van binding? Sweep capacity.
    print("\n\nVAN CAPACITY SWEEP — mean $ by strategy")
    print("-" * 78)
    print(f"{'slots':<8}{'BLIND':>12}{'SCAN_ALL':>12}{'ADAPTIVE':>12}"
          f"{'best':>12}{'edge':>10}")
    for slots in (6, 10, 14, 18, 24, 32, 48):
        VAN_SLOTS = slots
        rows = {s: trial(s, n=1500) for s in strategies}
        best = max(rows.values(), key=lambda r: r["mean"])
        edge = best["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{slots:<8}{rows['BLIND']['mean']:>12,.0f}"
              f"{rows['SCAN_ALL']['mean']:>12,.0f}"
              f"{rows['ADAPTIVE']['mean']:>12,.0f}"
              f"{best['strategy']:>12}{edge:>10.1%}")

    # How expensive can appraisal get before it stops being worth it?
    # NOTE: this sweep comes out flat and non-monotonic. That is quantisation, not
    # signal — trip counts are integers and the tier-3 unlock at 240s sits inside the
    # step. The real conclusion is that at 14 slots TIME is not the binding constraint,
    # so the 3s scan is nearly free. See RISK sweep below for the cost that does bite.
    print("\n\nAPPRAISAL TIME-COST SWEEP — van 14 slots (expect flat; see note)")
    print("-" * 78)
    print(f"{'sec/item':<10}{'BLIND':>12}{'SCAN_ALL':>12}{'ADAPTIVE':>12}"
          f"{'best':>12}{'edge':>10}")
    VAN_SLOTS = 14
    for cost in (1.0, 2.0, 3.0, 4.0, 6.0, 9.0):
        APPRAISE_S = cost
        rows = {s: trial(s, n=1500) for s in strategies}
        best = max(rows.values(), key=lambda r: r["mean"])
        edge = best["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{cost:<10.1f}{rows['BLIND']['mean']:>12,.0f}"
              f"{rows['SCAN_ALL']['mean']:>12,.0f}"
              f"{rows['ADAPTIVE']['mean']:>12,.0f}"
              f"{best['strategy']:>12}{edge:>10.1%}")

    # THE REAL QUESTION.
    #
    # If time isn't what makes appraising expensive, noise must be. Every scan is
    # L=48 -> +4.3 Disturbance (AUDIO-SPEC 1.2), and Disturbance is what gets your
    # cargo taken off you. How punishing does that have to be before scanning stops
    # paying? That number is the appraiser's actual tuning knob.
    APPRAISE_S = 3.0
    print("\n\nNOISE-RISK SWEEP — van 14 slots, scan = +4.3 Disturbance")
    print("-" * 78)
    print(f"{'loss coef':<12}{'BLIND':>12}{'SCAN_ALL':>12}{'ADAPTIVE':>12}"
          f"{'best':>12}{'edge':>10}")
    for coef in (0.0, 0.10, 0.25, 0.50, 0.75, 1.00, 1.50, 2.50):
        RISK_COEF = coef
        rows = {s: trial(s, n=1500) for s in strategies}
        best = max(rows.values(), key=lambda r: r["mean"])
        edge = best["mean"] / rows["BLIND"]["mean"] - 1
        print(f"{coef:<12.2f}{rows['BLIND']['mean']:>12,.0f}"
              f"{rows['SCAN_ALL']['mean']:>12,.0f}"
              f"{rows['ADAPTIVE']['mean']:>12,.0f}"
              f"{best['strategy']:>12}{edge:>10.1%}")
