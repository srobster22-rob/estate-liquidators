"""
Estate Liquidators — concealment, and whether it is a decision.

`DESIGN.md` 8.1 adds hiding, stashing and hand-off-then-hide as the counterplay to being
the attention target. It is the newest core verb and the only one specified purely in
prose: no durations, no search behaviour, no cost, nothing a build session could
implement without inventing values.

It also arrives with this project's characteristic risk. Three times now a menu of
options has turned out to be a step function with one dominant answer -- the appraiser
(R5-R8), the curse multiplier (R10), and the scan tail risk (R16). A fourth verb that
reads well in prose and collapses to "always do X" in play is the expected outcome, not
the surprising one. So the question this model exists to answer is not "is hiding fun",
it is:

    Does each of the four responses to being hunted -- RUN, HIDE, STASH, HAND OFF --
    have a region of the state space where it is genuinely the best play?

The state space is small and physical, which is the good news: how far you are from the
van, how close the Curator is, what you are carrying, whether a teammate is in reach,
and how much stamina you have left. All of it is legible to a player mid-panic, which is
the bar a decision has to clear to be worth having.

The speed table in `TECH-SPEC.md` A1 does most of the work. Carrying an armful you
sprint at 4.1 against its 2.9, but only for 6.0s of stamina drained 1.6x faster -- so
you get ~3.8s of running away, and after that you are at 2.6 and it is at 2.9 and it is
gaining. Every number below hangs off that.

Run: python sim/hiding.py            (stdlib only, ~20s)
"""

import json
import pathlib
import random
import statistics

TUNING = json.loads(
    (pathlib.Path(__file__).resolve().parent.parent / "tuning.json")
    .read_text(encoding="utf-8"))

# ---------------------------------------------------------------- TECH-SPEC A1
SPEED = {
    "empty_walk": 3.2, "empty_sprint": 5.6,
    "armful_walk": 2.6, "armful_sprint": 4.1,
    "two_man": 1.8, "dolly": 2.2,
}
CURATOR = {"PATROL": 2.4, "PURSUE": 2.9, "COLLECT": 3.4}
STAMINA_S = 6.0
STAMINA_RECOVER_S = 9.0            # empty -> full
ARMFUL_DRAIN = 1.6                 # carrying drains stamina 1.6x faster

# ------------------------------------------- DESIGN 8.1 / canonical in tuning.json
# R17 set these. Everything below the first three was unspecified before this round --
# the numbers a build session would otherwise have had to invent.
_C = TUNING["concealment"]
CONCEAL_ENTER_S = _C["enter_seconds"]
HIDE_BOUGHT_S = _C["hide_bought_seconds"]
STASH_QUIET_S = _C["stash_quiet_seconds"]
SEARCH_GIVEUP_S = _C["search_giveup_seconds"]
SEARCH_SPREAD_S = _C["search_spread_seconds"]
SEARCH_SPAN = _C["search_span_m"]
REACQUIRE_RADIUS = _C["reacquire_radius_m"]
HANDOFF_RANGE = _C["handoff_range_m"]
EXIT_LOUD_L = _C["exit_loudness"]
RETRIEVE_S = _C["retrieve_seconds"]
KNOCKDOWN_S = 15.0                 # fairness rule 4: retarget immunity after a hit
CORPSE_RUN_COST_S = 45.0           # a death costs the crew this much labour tonight


def stamina_seconds(carrying):
    """How long you can actually sprint, in seconds."""
    return STAMINA_S / (ARMFUL_DRAIN if carrying else 1.0)


def time_to_cover(dist, carrying, stamina_left):
    """Seconds to cover `dist` metres, sprinting while stamina lasts."""
    sprint = SPEED["armful_sprint"] if carrying else SPEED["empty_sprint"]
    walk = SPEED["armful_walk"] if carrying else SPEED["empty_walk"]
    sprint_dist = sprint * stamina_left
    if sprint_dist >= dist:
        return dist / sprint
    return stamina_left + (dist - sprint_dist) / walk


class Encounter:
    """One moment of being the attention target, with a decision to make.

    Distances are along the route, not straight lines -- the Curator paths to the
    item's home plinth rather than to you (A4), so it converges on your route rather
    than trailing you. `curator_lead` is how far it is from the point where those
    routes meet: negative means it gets there first.
    """

    def __init__(self, rng, d_van, curator_lead, value, tier, mate_dist, stamina,
                 route_len=None):
        self.rng = rng
        self.d_van = d_van
        # Total plinth->van route. Anything already carried is behind you.
        self.route_len = route_len if route_len is not None else d_van
        self.curator_lead = curator_lead
        self.value = value
        self.tier = tier
        self.mate_dist = mate_dist
        self.stamina = stamina
        self.speed = CURATOR[tier]

    # -- the four verbs ----------------------------------------------------
    def run(self, carrying=True, extra_delay=0.0):
        """Keep hold of it and race. Returns (value kept, seconds lost, died)."""
        t_me = time_to_cover(self.d_van, carrying, self.stamina) + extra_delay
        t_it = self.curator_lead / self.speed
        if t_me < t_it:
            return self.value, t_me, False
        # Caught. First contact of a night is a retrieval, not a death (A6 rule 3).
        return 0.0, t_me + RETRIEVE_S + KNOCKDOWN_S, False

    def hide_holding(self):
        """Get in the wardrobe with the prize.

        Below COLLECT the prize keeps broadcasting, so this is a delaying action and
        what it buys is stamina -- the only resource in the fiction that regenerates.
        At COLLECT the rules invert: the Curator has dropped item logic entirely and
        is targeting the nearest player (A3, A8), so the thing in your arms is no
        longer what it is following, and concealment works exactly as the genre
        expects. This is why 8.1 says hiding becomes the primary verb at COLLECT --
        it is not a difficulty ramp, it is a different targeting rule.
        """
        if not self._spot_in_reach():
            return self.run()

        if self.tier == "COLLECT":
            # Not a valid target while concealed, and it isn't tracking the item.
            wait = SEARCH_GIVEUP_S + self.rng.uniform(0, SEARCH_SPREAD_S)
            self.stamina = stamina_seconds(True)
            return self.value, wait + CONCEAL_ENTER_S, False

        hidden = min(HIDE_BOUGHT_S, self._time_until_opened())
        regained = (hidden / STAMINA_RECOVER_S) * STAMINA_S
        self.stamina = min(stamina_seconds(True), self.stamina + regained)
        if hidden < self._time_until_opened():
            return self.run(extra_delay=CONCEAL_ENTER_S + hidden)
        # It opened the wardrobe. It takes the item; you are alive and cornered.
        return 0.0, CONCEAL_ENTER_S + hidden + RETRIEVE_S + KNOCKDOWN_S, False

    def stash_then_hide(self):
        """Put it in the wardrobe, get in a different one. You vanish; it doesn't.

        The safety of a stash is POSITIONAL, and that is the whole mechanic. A
        stashed item stops radiating, so the Curator has nothing to follow -- but by
        A4 it was never pathing to you in the first place, it was pathing to the
        plinth the item came from. It will walk past everywhere you have carried
        that item. So a stash near the plinth is on its route and gets found; a stash
        near the van is behind it and is safe.

        Which makes "stash it" cost the thing you were trying to buy: to stash
        somewhere safe you must first carry it most of the way home, and by then
        running was already an option.
        """
        if not self._spot_in_reach():
            return self.run()

        if self.tier == "COLLECT":
            # It isn't following items at all, so stashing solves a problem you do
            # not have -- and you still have to survive the walk back to the van.
            return self.run(carrying=False)

        # How far this item has already travelled from its plinth.
        carried = max(0.0, self.route_len - self.d_van)
        p_found = max(0.0, 1.0 - carried / SEARCH_SPAN)
        wait = SEARCH_GIVEUP_S + self.rng.uniform(0, SEARCH_SPREAD_S)
        if wait > STASH_QUIET_S or self.rng.random() < p_found:
            # Found on its way to the plinth. Reseated. You are alive and you know
            # exactly where it went, which is worth something but not tonight.
            return 0.0, wait, False
        self.stamina = stamina_seconds(True)
        return self.value, wait + CONCEAL_ENTER_S, False

    def hand_off_then_hide(self, mate_d_van, mate_stamina):
        """The hot potato at knifepoint. Retarget is instant (D-verified, 0.0s)."""
        if self.mate_dist > HANDOFF_RANGE:
            return None
        # Your teammate is now the target, from wherever they are standing, with
        # their stamina -- and critically the Curator must re-converge on THEIR route.
        mate = Encounter(self.rng, mate_d_van, self.curator_lead + self.mate_dist,
                         self.value, self.tier, 99.0, mate_stamina)
        kept, t, died = mate.run()
        # You are free and empty-handed, which A1 says is always safe.
        return kept, t, died

    # -- helpers -----------------------------------------------------------
    def _spot_in_reach(self):
        """Estates author several per module; not every corner has one."""
        return self.rng.random() < CONCEAL_DENSITY

    def _time_until_opened(self):
        """It walks to the wardrobe the item is broadcasting from and opens it."""
        return self.curator_lead / self.speed + HIDE_BOUGHT_S


CONCEAL_DENSITY = 0.55             # chance a hiding place is within reach when needed

POLICIES = ("RUN", "HIDE", "STASH", "HANDOFF")


def play(seed, policy, d_van, tier, value, mate_dist, route_len=80.0):
    rng = random.Random(seed)
    stam = stamina_seconds(True) * rng.uniform(0.3, 1.0)
    lead = rng.uniform(6.0, 26.0)
    e = Encounter(rng, d_van, lead, value, tier, mate_dist, stam,
                  route_len=max(route_len, d_van))

    if policy == "RUN":
        kept, t, died = e.run()
    elif policy == "HIDE":
        kept, t, died = e.hide_holding()
    elif policy == "STASH":
        kept, t, died = e.stash_then_hide()
    else:
        r = e.hand_off_then_hide(rng.uniform(0.6, 1.4) * d_van,
                                 stamina_seconds(True) * rng.uniform(0.5, 1.0))
        if r is None:
            return None
        kept, t, died = r

    # Seconds are money: time not hauling is loot not taken. Calibrated against
    # ECONOMY 2 -- a tier-2 armful round trip is ~60s for ~$475 of expected value.
    return kept - t * (475.0 / 60.0) - (CORPSE_RUN_COST_S * 8.0 if died else 0.0)


def trial(policy, n=1500, **kw):
    out = [play(s, policy, **kw) for s in range(n)]
    out = [o for o in out if o is not None]
    return statistics.mean(out) if out else None


def sweep(title, rows, fmt, **fixed):
    print(f"\n{title}")
    print("-" * 78)
    print(f"{'':<14}{'RUN':>11}{'HIDE':>11}{'STASH':>11}{'HANDOFF':>11}{'best':>10}")
    winners = set()
    for label, kw in rows:
        vals = {}
        for p in POLICIES:
            vals[p] = trial(p, **{**fixed, **kw})
        live = {p: v for p, v in vals.items() if v is not None}
        best = max(live, key=lambda p: live[p])
        winners.add(best)
        cells = "".join(f"{live[p]:>11,.0f}" if p in live else f"{'n/a':>11}"
                        for p in POLICIES)
        print(f"{fmt(label):<14}{cells}{best:>10}")
    return winners


def stash_success(n=3000, d_van=35.0, route_len=80.0):
    """Of the times you CAN stash, how often does it save the item?

    Conditional on a hiding place being in reach -- otherwise this measures wardrobe
    density rather than the mechanic, and 56% of encounters looks like a gamble when
    the gamble is actually a certainty gated on furniture. 100% here is the D-03
    failure: a free reset of the whole threat system, wearing a different hat.
    """
    keeps = tries = 0
    for seed in range(n):
        rng = random.Random(seed)
        e = Encounter(rng, d_van, rng.uniform(6.0, 26.0), 900.0, "PURSUE", 99.0,
                      stamina_seconds(True), route_len=route_len)
        if not e._spot_in_reach():
            continue                      # no wardrobe, no decision to measure
        tries += 1
        carried = max(0.0, e.route_len - e.d_van)
        p_found = max(0.0, 1.0 - carried / SEARCH_SPAN)
        wait = SEARCH_GIVEUP_S + rng.uniform(0, SEARCH_SPREAD_S)
        if not (wait > STASH_QUIET_S or rng.random() < p_found):
            keeps += 1
    return keeps / tries if tries else 0.0


if __name__ == "__main__":
    print("CONCEALMENT — is DESIGN 8.1 four verbs or one verb and three decorations?")
    print("=" * 78)
    print(f"conceal density {CONCEAL_DENSITY}, hide buys {HIDE_BOUGHT_S}s, "
          f"stash quiet {STASH_QUIET_S}s, search {SEARCH_GIVEUP_S}"
          f"-{SEARCH_GIVEUP_S + SEARCH_SPREAD_S}s")

    won = set()
    won |= sweep(
        "DISTANCE TO VAN, teammate in reach (PURSUE, $900 armful, 80m route)",
        [(d, {"d_van": float(d)}) for d in (10, 20, 35, 50, 70, 95)],
        lambda d: f"{d}m to van",
        tier="PURSUE", value=900.0, mate_dist=2.0)

    won |= sweep(
        "DISTANCE TO VAN, nobody in reach — the common case",
        [(d, {"d_van": float(d)}) for d in (10, 20, 35, 50, 70, 95)],
        lambda d: f"{d}m to van",
        tier="PURSUE", value=900.0, mate_dist=12.0)

    won |= sweep(
        "ITEM VALUE (35m to van, PURSUE, nobody in reach)",
        [(v, {"value": float(v)}) for v in (150, 400, 900, 1400, 3200)],
        lambda v: f"${v} item",
        d_van=35.0, tier="PURSUE", mate_dist=12.0)

    won |= sweep(
        "DISTURBANCE TIER ($900 armful, 35m to van, nobody in reach)",
        [(t, {"tier": t}) for t in ("PATROL", "PURSUE", "COLLECT")],
        lambda t: t,
        d_van=35.0, value=900.0, mate_dist=12.0)

    won |= sweep(
        "HOW FAR HAVE YOU ALREADY CARRIED IT? (35m to van, PURSUE, no mate)",
        [(r, {"route_len": float(r)}) for r in (40, 55, 70, 90, 120)],
        lambda r: f"{r - 35:.0f}m carried",
        d_van=35.0, tier="PURSUE", value=900.0, mate_dist=12.0)

    print("\n" + "=" * 78)
    print(f"VERDICT: {len(won)}/4 verbs win somewhere -> {sorted(won)}")
    dead = [p for p in POLICIES if p not in won]
    print(f"         dominated everywhere (decoration): {dead or 'none'}")
    print(f"\n  stash save rate at the designed values: {stash_success():.0%}")
    print("  100% would mean stashing is a FREE reset of the whole threat system,")
    print("  which is the exploit D-03 exists to prevent, re-entered by another door.")

    print("\n\nPARAMETER SWEEP — the numbers 8.1 leaves unspecified")
    print("-" * 78)
    print("Target: all four verbs alive, and a stash save rate that is not a formality.")
    print(f"{'stash quiet':<13}{'search':<14}{'verbs':<8}{'stash saves':<13}{'dead'}")
    base = (STASH_QUIET_S, SEARCH_GIVEUP_S, SEARCH_SPREAD_S)
    for st in (8.0, 12.0, 16.0, 20.0):
        for gv, spread in ((8.0, 6.0), (8.0, 16.0), (12.0, 6.0), (12.0, 16.0)):
            STASH_QUIET_S, SEARCH_GIVEUP_S, SEARCH_SPREAD_S = st, gv, spread
            w = set()
            for tier in ("PURSUE", "COLLECT"):
                for md in (2.0, 12.0):
                    for d in (10, 35, 70, 95):
                        vals = {pol: trial(pol, n=400, d_van=float(d), tier=tier,
                                           value=900.0, mate_dist=md)
                                for pol in POLICIES}
                        live = {k: v for k, v in vals.items() if v is not None}
                        w.add(max(live, key=lambda k: live[k]))
            dead = [pol for pol in POLICIES if pol not in w]
            print(f"{st:<13.0f}{f'{gv:.0f}-{gv + spread:.0f}s':<14}{len(w):<8}"
                  f"{stash_success(n=1500):<13.0%}{dead or 'none'}")
    STASH_QUIET_S, SEARCH_GIVEUP_S, SEARCH_SPREAD_S = base
