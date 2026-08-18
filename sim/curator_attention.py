"""
Estate Liquidators — Curator attention model.

TECH-SPEC.md A3 specifies aggro selection with three tuning constants that have never
been checked against the behaviour they are supposed to produce:

    steal threshold   1.25x    stop the target flickering between four players
    commitment        8.0s     make it look decisive
    hand-off override instant  the hot potato must ALWAYS work

Those pull against each other. Hysteresis exists to stop flicker; the override exists
to punch through hysteresis. If the override is too weak the hot potato feels
unreliable and players stop using it — which kills the social layer, because the whole
design rests on being able to give the monster to a friend (DESIGN.md pillar 2).

This measures four things:
    1. flicker rate, with and without hysteresis
    2. hand-off reliability and latency
    3. does the richest player actually get hunted
    4. does a sacrifice play work — can a volunteer pull the Curator off a friend
"""

import random
import statistics

TICK = 2.0              # attention recompute, seconds
STEAL = 1.25
COMMIT = 8.0
CURSE = {"clean": 1.0, "tainted": 1.5, "malignant": 3.0}


class Player:
    def __init__(self, name):
        self.name = name
        self.items = []          # list of (value, grade)
        self.noise = 0
        self.light = False

    # The shipped weight function (D-25, FIRM): noise and light MODIFY how visible
    # your loot is, and cannot conjure a target out of an empty-handed player.
    # The additive version below it is what R2 replaced, kept because the failure
    # is the argument - set this False and a loud, lit, empty-handed player becomes
    # the hunted one every single time. This file ran the superseded model as its
    # DEFAULT for thirty-five rounds after the decision was made FIRM, which is
    # the same rot R37 found in chain_sim.py: the model quietly disagreeing with
    # the document that cites it.
    MULTIPLICATIVE = True

    def weight(self):
        loot = sum(v * CURSE[g] for v, g in self.items)
        if Player.MULTIPLICATIVE:
            # Noise and light MODIFY how visible your loot is. They can never make an
            # empty-handed player a target, which is what "aggro is an object" means.
            return loot * (1.0 + 0.20 * self.noise) * (1.30 if self.light else 1.0)
        w = loot + self.noise * 200
        if self.light:
            w += 400
        return w


class Curator:
    def __init__(self, steal=STEAL, commit=COMMIT, override=True):
        self.steal, self.commit, self.override = steal, commit, override
        self.target = None
        self.locked_until = 0.0
        self.retargets = 0

    def update(self, t, players, handoff=None):
        # A hand-off is a first-class event: it punches straight through hysteresis.
        if handoff and self.override and handoff[0] is self.target:
            if self.target is not handoff[1]:
                self.target = handoff[1]
                self.retargets += 1
                self.locked_until = t + self.commit
            return

        best = max(players, key=lambda p: p.weight())
        if self.target is None:
            self.target, self.locked_until = best, t + self.commit
            return
        if t < self.locked_until:
            return
        if best is not self.target and best.weight() > self.target.weight() * self.steal:
            self.target = best
            self.retargets += 1
            self.locked_until = t + self.commit


def scenario_flicker(steal, commit, override=True, dur=300.0, seed=0):
    """Four players hauling comparable loot, with ordinary noise jitter."""
    rng = random.Random(seed)
    ps = [Player(f"P{i}") for i in range(4)]
    for p in ps:
        p.items = [(rng.uniform(400, 900), "clean")]
    cur = Curator(steal, commit, override)
    t = 0.0
    while t < dur:
        for p in ps:
            p.noise = 1 if rng.random() < 0.25 else 0
            p.light = rng.random() < 0.5
        cur.update(t, ps)
        t += TICK
    return cur.retargets / (dur / 60.0)      # retargets per minute


def scenario_handoff(override, trials=400):
    """P0 carries the prize and passes it to P1. Does aggro follow the object?"""
    ok, lat = 0, []
    for s in range(trials):
        rng = random.Random(s)
        ps = [Player(f"P{i}") for i in range(4)]
        ps[0].items = [(rng.uniform(900, 1400), "clean")]
        for p in ps[1:]:
            p.items = [(rng.uniform(200, 600), "clean")]
        cur = Curator(override=override)
        t = 0.0
        while t < 6.0:                       # settle onto P0
            cur.update(t, ps); t += TICK
        if cur.target is not ps[0]:
            continue                          # never locked on; not a hand-off test
        item = ps[0].items.pop()              # the pass
        ps[1].items.append(item)
        start = t
        handed = (ps[0], ps[1])
        for _ in range(10):
            cur.update(t, ps, handoff=handed)
            handed = None                     # the event fires once
            if cur.target is ps[1]:
                ok += 1
                lat.append(t - start)
                break
            t += TICK
    return ok / trials, (statistics.mean(lat) if lat else float("nan"))


def scenario_richest(trials=600):
    """Is the most valuable carrier the one being hunted?"""
    hit = 0
    for s in range(trials):
        rng = random.Random(s + 9000)
        ps = [Player(f"P{i}") for i in range(4)]
        for p in ps:
            p.items = [(rng.uniform(100, 1500), "clean")]
        cur = Curator()
        t = 0.0
        while t < 40.0:
            cur.update(t, ps); t += TICK
        if cur.target is max(ps, key=lambda p: p.weight()):
            hit += 1
    return hit / trials


def scenario_sacrifice(trials=500):
    """P0 is hunted while hauling the prize. P2 grabs a malignant item to pull it off.

    This is the heroic moment the design exists to produce (TECH-SPEC A3). If the
    numbers don't allow it, the moment never happens.
    """
    saved = 0
    for s in range(trials):
        rng = random.Random(s + 4242)
        ps = [Player(f"P{i}") for i in range(4)]
        ps[0].items = [(rng.uniform(1000, 1500), "clean")]
        for p in ps[1:]:
            p.items = []
        cur = Curator()
        t = 0.0
        while t < 12.0:
            cur.update(t, ps); t += TICK
        if cur.target is not ps[0]:
            continue
        # The volunteer picks up something malignant: value x3.
        ps[2].items = [(rng.uniform(700, 1100), "malignant")]
        for _ in range(8):
            t += TICK
            cur.update(t, ps)
            if cur.target is ps[2]:
                saved += 1
                break
    return saved / trials


def scenario_partial_handoff(override, trials=500):
    """The case that actually matters: pass ONE item while still holding others.

    The clean hand-off (give away everything) beats any threshold trivially. The real
    risk is a thin margin colliding with the 8s commitment lock, leaving the Curator
    walking at the wrong player while the right one gets away — or worse, while the
    wrong one is cornered.
    """
    ok, lat = 0, []
    for s in range(trials):
        rng = random.Random(s + 555)
        ps = [Player(f"P{i}") for i in range(4)]
        prize = rng.uniform(800, 1200)
        ps[0].items = [(prize, "clean"), (rng.uniform(400, 700), "clean")]
        ps[1].items = [(rng.uniform(300, 600), "clean")]
        for p in ps[2:]:
            p.items = [(rng.uniform(100, 400), "clean")]
        cur = Curator(override=override)
        t = 0.0
        while t < 10.0:
            cur.update(t, ps); t += TICK
        if cur.target is not ps[0]:
            continue
        ps[0].items.remove((prize, "clean"))
        ps[1].items.append((prize, "clean"))
        start, handed = t, (ps[0], ps[1])
        for _ in range(8):
            cur.update(t, ps, handoff=handed)
            handed = None
            if cur.target is ps[1]:
                ok += 1
                lat.append(t - start)
                break
            t += TICK
    return ok / trials, (statistics.mean(lat) if lat else float("nan"))


def scenario_sacrifice_latency(trials=500):
    """How LONG does a rescue take? A rescue that lands after 8s is not a rescue."""
    lat = []
    for s in range(trials):
        rng = random.Random(s + 4242)
        ps = [Player(f"P{i}") for i in range(4)]
        ps[0].items = [(rng.uniform(1000, 1500), "clean")]
        cur = Curator()
        t = 0.0
        while t < 12.0:
            cur.update(t, ps); t += TICK
        if cur.target is not ps[0]:
            continue
        ps[2].items = [(rng.uniform(700, 1100), "malignant")]
        start = t
        for _ in range(8):
            t += TICK
            cur.update(t, ps)
            if cur.target is ps[2]:
                lat.append(t - start)
                break
    return statistics.mean(lat), max(lat)


def scenario_lootless_target(trials=800):
    """Can a player carrying NOTHING become the target? Pillar 2 says never."""
    bad = 0
    for s in range(trials):
        rng = random.Random(s + 77)
        ps = [Player(f"P{i}") for i in range(4)]
        ps[0].items = []                       # empty-handed, but noisy and lit
        ps[0].noise, ps[0].light = 1, True
        for p in ps[1:]:
            p.items = [(rng.uniform(150, 500), "clean")]
        cur = Curator()
        t = 0.0
        while t < 30.0:
            cur.update(t, ps); t += TICK
        if cur.target is ps[0]:
            bad += 1
    return bad / trials


if __name__ == "__main__":
    print("1. FLICKER — target changes per minute (4 players, comparable loot)")
    print("-" * 74)
    print(f"{'steal':>7}{'commit':>8}{'retargets/min':>16}   verdict")
    for steal, commit in ((1.00, 0.0), (1.00, 8.0), (1.25, 0.0), (1.25, 8.0),
                          (1.50, 8.0), (2.00, 12.0)):
        r = statistics.mean(scenario_flicker(steal, commit, seed=s)
                            for s in range(40))
        note = ("SPEC" if (steal, commit) == (1.25, 8.0) else
                "no hysteresis" if (steal, commit) == (1.00, 0.0) else "")
        print(f"{steal:>7.2f}{commit:>8.1f}{r:>16.1f}   {note}")

    print("\n\n2. HAND-OFF — does the hot potato work?")
    print("-" * 74)
    for override in (True, False):
        rate, lat = scenario_handoff(override)
        print(f"  override={str(override):<6} success {rate:>6.1%}   "
              f"mean latency {lat:.1f}s")

    print("\n\n3. IS THE RICHEST PLAYER HUNTED?")
    print("-" * 74)
    print(f"  correct target {scenario_richest():.1%} of the time")

    print("\n\n3b. CAN AN EMPTY-HANDED PLAYER BE HUNTED?  (D-06 / D-25: never)")
    print("-" * 74)
    for mult, label in ((True, "shipped, multiplicative over items"),
                        (False, "superseded, additive per player")):
        Player.MULTIPLICATIVE = mult
        print(f"  {label:<38}{scenario_lootless_target():>6.0%} of the time")
    Player.MULTIPLICATIVE = True

    print("\n\n4. SACRIFICE PLAY — can a volunteer pull the Curator off a friend?")
    print("-" * 74)
    print(f"  rescue succeeds {scenario_sacrifice():.1%} of the time")
