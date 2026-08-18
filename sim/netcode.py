"""
Estate Liquidators — does the social layer survive the network?

`STATUS.md` calls multiplayer the largest gap by far, and it is: there is one
client and three bots. But "unproven" covers two different things. The *feel* of
four people in a house needs four people. The *arithmetic* of a host-authoritative
world with owner-authoritative carry does not — it needs a clock, a delay, and an
honest account of who believes what and when. That part can be settled here, the
same way `haul_sim.py` settled the appraiser before anyone built it.

TECH-SPEC.md B1-B4 makes four promises with numbers attached. Each is a question:

  1. HAND-OFF (A3, D-25) — the aggro override retargets "instantly, every time, no
     exceptions". Instantly on the HOST, which learns about the hand-off one trip
     time after it happened. How long does the Curator keep hunting the player who
     no longer has the vase, and is that long enough to kill them for it?

  2. PICKUP RACE (B2) — "host arbitrates, first request wins, loser gets a clean
     rejection". The loser has already played the grab animation optimistically.
     How often does that rollback happen, and does it scale with latency in a way
     that makes the game feel like it is lying to you?

  3. THE PRY (B3) — a 1.5s hold that transfers ownership, "impossible to do by
     accident". Two players prying the same item, and the victim walking away
     mid-pry, both resolve on the host. Do both clients agree on who won?

  4. TWO-MAN CARRY (B4) — the follower may drift 0.4m before a soft correction.
     The follower's view of the object is one trip time old, so the drift they see
     is not the drift the anchor sees. Does the correction chase its own tail?

MODEL

  A 60Hz simulation with an explicit host and N clients. Every message carries a
  one-way delay of RTT/2 plus jitter; nothing is instantaneous and nothing is
  reordered (Steam's transport is reliable-ordered for these events). Clients act
  optimistically and roll back when the host disagrees, which is what B2 asks for.

  RTT figures are the ones that matter for a co-op game on Steam datagram relay:
  30ms same-city, 80ms same-country, 120ms the spec's own budget, 250ms a friend
  who lives somewhere else entirely and is not going to be excluded.

Run: python3 sim/netcode.py
"""

import random
import statistics

TICKRATE = 60.0
DT = 1.0 / TICKRATE

# TECH-SPEC B1: 120ms is called out as the budget a carried object must survive.
RTTS = [30.0, 80.0, 120.0, 250.0]
JITTER_FRAC = 0.25              # +-25% of the one-way delay, which is generous

# DESIGN 6.3: first contact takes the piece, second is fatal. The Curator closes
# the last few metres in about this long once it is on you.
CONTACT_S = 2.5


def one_way(rng, rtt):
    """Half the round trip, jittered. Never negative, never reordered."""
    d = rtt / 2000.0
    return max(0.0, d * (1.0 + rng.uniform(-JITTER_FRAC, JITTER_FRAC)))


# ------------------------------------------------------------------ 1. hand-off
def handoff_window(rng, rtt, curator_lock=8.0):
    """Seconds the Curator spends hunting a player who has already given it away.

    The giver presses the button at t=0. The host learns at +d, retargets on its
    next tick, and the world learns at +2d. What the giver EXPERIENCES is the
    Curator continuing toward them for the whole of that window, which is the
    thing the design promises never happens.
    """
    d = one_way(rng, rtt)
    host_learns = d
    # The host retargets on its next simulation tick, not on arrival.
    host_acts = (int(host_learns / DT) + 1) * DT
    # The giver sees the Curator turn away one more trip later, because the
    # Curator's position and state are host-simulated and replicated back.
    giver_sees = host_acts + d
    return giver_sees


def scenario_handoff(rtt, trials=20000, seed=0):
    rng = random.Random(seed)
    w = [handoff_window(rng, rtt) for _ in range(trials)]
    w.sort()
    # A hand-off made in the last moment before contact is the interesting one:
    # if the window is longer than the time the Curator needed, the giver is hit
    # for an item they no longer have.
    fatal = sum(1 for x in w if x > CONTACT_S) / trials
    return {"mean": statistics.mean(w), "p99": w[int(trials * 0.99)],
            "worse_than_contact": fatal}


# -------------------------------------------------------------- 2. pickup race
def scenario_pickup(rtt, trials=20000, seed=1, reach_window=0.35):
    """Two players reach for the same vase. How often does one get rolled back?

    `reach_window` is how close together two humans actually press the button when
    they both want the same thing - a quarter to half a second is what a race
    across a room looks like. The host takes whichever REQUEST ARRIVES first, so
    the winner is decided by the difference in press times and the difference in
    delays together.
    """
    rng = random.Random(seed)
    rollbacks = 0
    wrong_winner = 0
    for _ in range(trials):
        pa, pb = 0.0, abs(rng.gauss(0.0, reach_window))
        da, db = one_way(rng, rtt), one_way(rng, rtt)
        # Both played the grab locally the moment they pressed.
        arrive_a, arrive_b = pa + da, pb + db
        # Exactly one client is always rolled back in a contested grab, by
        # construction - counting that tells you nothing. The number a player can
        # actually object to is this one: they pressed first and still lost,
        # because their packet took longer than the other person's.
        if (arrive_a <= arrive_b) != (pa <= pb):
            wrong_winner += 1
        # And how close the race was when it went wrong, which is what decides
        # whether it reads as "they beat me" or "the game stole that from me".
        if (arrive_a <= arrive_b) != (pa <= pb) and abs(pa - pb) > 0.15:
            rollbacks += 1
    return {"first_press_lost": wrong_winner / trials,
            "not_even_close": rollbacks / trials}


# ------------------------------------------------------------------- 3. the pry
PRY_S = 1.5


def scenario_pry(rtt, trials=20000, seed=2):
    """Both clients hold for 1.5s. Do they agree on who won, and does the victim
    escaping mid-pry resolve the same way on both machines?

    The pry starts on the host when the request arrives and completes 1.5s later by
    the HOST's clock. The prying client sees their own progress bar fill from the
    moment they pressed. Those two clocks differ by exactly one trip time, so a
    victim who walks out of range in the last trip-time of the pry is a
    disagreement: their client says they escaped, the host says they did not.
    """
    rng = random.Random(seed)
    disagreements = 0
    for _ in range(trials):
        d = one_way(rng, rtt)
        # The victim decides to walk at a uniformly random point in the pry.
        escape_at = rng.uniform(0.0, PRY_S + 2 * d)
        host_completes = d + PRY_S
        victim_thinks_escaped = escape_at < host_completes
        host_sees_escape = escape_at + d < host_completes
        if victim_thinks_escaped != host_sees_escape:
            disagreements += 1
    return {"disagree": disagreements / trials, "window_s": None}


# ------------------------------------------------------- 4. two-man carry drift
DRIFT_TOLERANCE_M = 0.4         # TECH-SPEC B4
WALK_MS = 2.6                   # anchor's walking speed


def scenario_twoman(rtt, trials=4000, seed=3, turn_rate=0.9):
    """How far behind is the follower's view of the far end?

    The follower renders the object from state that is one trip time old, so while
    the anchor is moving, the follower is aiming their spring at where the object
    WAS. The question B4 leaves open is whether the 0.4m tolerance is spent on
    physics slop or eaten entirely by latency before the physics gets any of it.
    """
    rng = random.Random(seed)
    over = 0
    worst = []
    for _ in range(trials):
        d = one_way(rng, rtt)
        # Anchor moving, and turning: the far end of a two-man object sweeps much
        # faster than the anchor walks when the anchor pivots in a doorway.
        speed = rng.uniform(0.6, 1.0) * WALK_MS
        turning = rng.random() < turn_rate
        # Far end is ~1.4m from the anchor; a pivot sweeps it at omega * r.
        sweep = rng.uniform(1.2, 2.6) * 1.4 if turning else 0.0
        lag = (speed + sweep) * d
        worst.append(lag)
        over += lag > DRIFT_TOLERANCE_M
    worst.sort()
    return {"mean_lag_m": statistics.mean(worst), "p95_lag_m": worst[int(trials * 0.95)],
            "over_tolerance": over / trials}


def main():
    print("HAND-OFF — how long the Curator keeps hunting the player who gave it away")
    print("-" * 78)
    print(f"{'RTT':>6}{'mean':>10}{'p99':>10}{'> contact (2.5s)':>20}   verdict")
    for rtt in RTTS:
        r = scenario_handoff(rtt)
        v = "fine" if r["p99"] < 0.5 else ("noticeable" if r["p99"] < 1.0 else "BROKEN")
        print(f"{rtt:>5.0f}ms{r['mean']:>9.3f}s{r['p99']:>9.3f}s"
              f"{r['worse_than_contact']:>19.2%}   {v}")

    print("\n\nPICKUP RACE — two players grab the same vase (B2)")
    print("-" * 78)
    print("One client is always rolled back; the question is whether it is the right one.")
    print(f"{'RTT':>6}{'first press lost':>20}{'lost by >150ms':>17}   verdict")
    for rtt in RTTS:
        r = scenario_pickup(rtt)
        v = "fine" if r["first_press_lost"] < 0.10 else \
            ("noticeable" if r["first_press_lost"] < 0.25 else "feels like a lie")
        print(f"{rtt:>5.0f}ms{r['first_press_lost']:>19.1%}{r['not_even_close']:>16.2%}   {v}")

    print("\n\nTHE PRY — do both machines agree on who won? (B3, 1.5s hold)")
    print("-" * 78)
    print(f"{'RTT':>6}{'disagreements':>16}   verdict")
    for rtt in RTTS:
        r = scenario_pry(rtt)
        v = "fine" if r["disagree"] < 0.05 else \
            ("noticeable" if r["disagree"] < 0.15 else "the victim will call it a bug")
        print(f"{rtt:>5.0f}ms{r['disagree']:>15.1%}   {v}")

    print("\n\nTWO-MAN CARRY — how much of the 0.4m tolerance is spent on latency? (B4)")
    print("-" * 78)
    print("Straight-line walking is cheap; it is the pivot in a doorway that spends it.")
    print(f"{'RTT':>6}{'straight':>11}{'mean lag':>11}{'p95 lag':>10}{'over 0.4m':>12}   verdict")
    for rtt in RTTS:
        r = scenario_twoman(rtt)
        straight = scenario_twoman(rtt, turn_rate=0.0)["mean_lag_m"]
        v = "fits" if r["p95_lag_m"] < DRIFT_TOLERANCE_M else \
            ("tight" if r["mean_lag_m"] < DRIFT_TOLERANCE_M else "tolerance is latency, not slop")
        print(f"{rtt:>5.0f}ms{straight:>10.2f}m{r['mean_lag_m']:>10.2f}m"
              f"{r['p95_lag_m']:>9.2f}m{r['over_tolerance']:>11.0%}   {v}")


if __name__ == "__main__":
    main()
