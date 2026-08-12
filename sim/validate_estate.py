"""
Estate Liquidators — estate validator.

Implements the ten checks LEVEL-SPEC.md 6 specifies. A wing that fails any of them
does not enter the pool.

The point of this file is that every promise the other documents make about SPACE is
a promise a level designer under deadline will break by accident:

  - the Curator intercepts at pinch points     -> a wing with none has no Curator
  - the fairness contract guarantees a 2nd route -> a single-corridor wing breaks it
  - depth gates pacing                          -> an early-opening deep wing inverts it
  - a piano must physically fit through a door  -> or four people waste three minutes

None of those survive contact with a deadline unless a machine checks them.

Run: python validate_estate.py
"""

from collections import deque
from itertools import combinations
import math

# Minimum clear width to move each class through a doorway.
CLASS_WIDTH = {"pocket": 0.7, "armful": 0.9, "two_man": 1.6, "cart": 2.2}
CLASS_SLOTS = {"pocket": 0.5, "armful": 1.0, "two_man": 3.0, "cart": 5.0}

# ECONOMY.md 3
VALUE_BANDS = {
    0: (40, 300), 1: (80, 300), 2: (250, 1900), 3: (600, 4000), 4: (4000, 8000),
}

TASK_SECONDS = 75.0     # rough cost of one prerequisite step for a crew of 4
APPROACH_L = 60.0       # AUDIO-SPEC 3.1 approach bus at source
AUDIBILITY_FLOOR = 25.0
OCCLUSION = 0.85        # per wall, Curator


class Estate:
    def __init__(self, d):
        self.id = d["id"]
        self.rooms = d["rooms"]
        self.portals = d["portals"]
        self.plinths = d["plinths"]
        self.prereqs = d.get("prereqs", {})
        self.curator_spawn = d["curator_spawn"]
        self.van = next(r for r, v in self.rooms.items() if v.get("van"))

        # The CORE is the room the fairness contract measures redundancy to -
        # the hub every wing must reach by two routes. It was resolved as
        # `core_link` with a default of "foyer", which is fine for MANOR_A and
        # silently wrong for every estate that does not happen to contain a room
        # of that name: V3 then reports every wing "sealed off by losing" an
        # arbitrary portal, which sends the author rebuilding topology that was
        # never the problem. R29 found this by authoring a second estate.
        self.core = self.rooms[self.van].get("core_link")
        if self.core is None:
            self.core = "foyer" if "foyer" in self.rooms else None

    def adj(self, min_width=0.0):
        g = {r: [] for r in self.rooms}
        for p in self.portals:
            if p["width"] >= min_width:
                g[p["a"]].append(p["b"])
                g[p["b"]].append(p["a"])
        return g

    def path(self, src, dst, min_width=0.0, banned=()):
        """BFS shortest path by room count; returns list of rooms or None."""
        g = self.adj(min_width)
        seen, q = {src}, deque([[src]])
        while q:
            p = q.popleft()
            if p[-1] == dst:
                return p
            for n in g[p[-1]]:
                edge = frozenset((p[-1], n))
                if n not in seen and edge not in banned:
                    seen.add(n)
                    q.append(p + [n])
        return None

    def portal_between(self, a, b):
        for p in self.portals:
            if {p["a"], p["b"]} == {a, b}:
                return p
        return None

    def pinches_on(self, path):
        n = 0
        for a, b in zip(path, path[1:]):
            p = self.portal_between(a, b)
            if p and p.get("pinch"):
                n += 1
        return n

    def dist(self, a, b):
        pa, pb = self.rooms[a]["pos"], self.rooms[b]["pos"]
        return math.dist(pa, pb)

    def chain_len(self, room, _seen=None):
        """How many prerequisite steps before `room` opens."""
        _seen = _seen or set()
        if room in _seen:
            return 0
        _seen.add(room)
        reqs = self.prereqs.get(room, [])
        if not reqs:
            return 0
        return 1 + max(self.chain_len(r["room"], _seen) for r in reqs)


# ------------------------------------------------------------------ the checks

def V1_reachable(e):
    g = self_reach = e.adj()
    seen, q = {e.van}, deque([e.van])
    while q:
        for n in g[q.popleft()]:
            if n not in seen:
                seen.add(n)
                q.append(n)
    missing = set(e.rooms) - seen
    return not missing, f"unreachable rooms: {sorted(missing)}" if missing else ""


def V2_depth_pacing(e):
    bad = []
    for room, meta in e.rooms.items():
        tier = meta.get("tier", 0)
        if tier < 2:
            continue
        need = {2: 1, 3: 2, 4: 3}[tier]
        got = e.chain_len(room)
        if got < need:
            bad.append(f"{room} (tier {tier}) opens after {got} steps, needs {need}")
        for r in e.prereqs.get(room, []):
            src_tier = e.rooms[r["room"]].get("tier", 0)
            if src_tier >= tier:
                bad.append(f"{room} prereq sits at tier {src_tier}, not shallower")
    return not bad, "; ".join(bad)


def V3_two_routes(e):
    """Two edge-disjoint routes from each wing back to the CORE.

    Not to the van. The front door is a designed singularity — every route leaves the
    house through it, and demanding redundancy there fails every estate ever built.
    The fairness contract (TECH-SPEC A6 rule 5) is about the Curator not sealing you
    inside a wing, so portals flagged `entrance` are exempt.
    """
    if e.core is None:
        return False, ("the van room declares no `core_link` and there is no room "
                       "named `foyer` - name the hub every wing must reach twice "
                       "(LEVEL-SPEC 5)")
    core = e.core
    bad = []
    for room in e.rooms:
        if room in (e.van, core) or not e.rooms[room].get("tier"):
            continue
        for p in e.portals:
            if p.get("entrance"):
                continue
            banned = {frozenset((p["a"], p["b"]))}
            if e.path(room, core, banned=banned) is None:
                bad.append(f"{room} sealed off by losing {p['a']}<->{p['b']}")
                break
    return not bad, "; ".join(bad)


def _all_paths(e, src, dst, limit=4000):
    """Every simple path, so we can find the route a player would use to DODGE pinches."""
    g, out, stack = e.adj(), [], [[src]]
    while stack and len(out) < limit:
        p = stack.pop()
        if p[-1] == dst:
            out.append(p)
            continue
        for n in g[p[-1]]:
            if n not in p:
                stack.append(p + [n])
    return out


def V4_pinch_points(e):
    """LEVEL-SPEC 4: EVERY route from a tier-3/4 plinth crosses >=2 pinch nodes.

    Checking only the shortest path is not enough — players will happily take a longer
    route precisely to avoid the dangerous one, so the check is the MINIMUM pinch count
    across all simple paths.
    """
    bad = []

    # Authoring guard. LEVEL-SPEC 4 defines a pinch as <=2.0m effective width. Any
    # portal that narrow must SAY whether it is one — silence is how unpinched
    # bypasses appear. Adding a second route (V3) repeatedly created new safe
    # corridors that quietly defeated the pinch design; this is the guard against it.
    for p in e.portals:
        if p["width"] <= 2.0 and "pinch" not in p and not p.get("entrance"):
            bad.append(f"{p['a']}<->{p['b']} is {p['width']}m wide "
                       f"but does not declare pinch true/false")

    for pl in e.plinths:
        if pl["tier"] < 3:
            continue
        paths = _all_paths(e, pl["room"], e.van)
        if not paths:
            bad.append(f"{pl['room']} has no route to the van")
            continue
        worst = min(e.pinches_on(p) for p in paths)
        if worst < 2:
            bad.append(f"{pl['room']} has a route crossing only {worst} pinch nodes")
    return not bad, "; ".join(sorted(set(bad)))


def V5_audibility(e):
    """
    AUDIO-SPEC 3.1: the Curator's approach must be audible where the loot is.

    R20 rewrote this. It measured doors between the plinth and the VAN, which is
    the wrong pair of rooms entirely - the approach bus is the Curator coming at
    you, so the geometry that matters is spawn-to-plinth. Measuring the wrong
    path is why this check had never failed anything, including the estate built
    to fail seven checks.

    The Curator paths to the plinth (TECH-SPEC A4, the one AI cheat), so its
    actual approach is the shortest route from where it is. If that route is
    buried behind enough closed doors, the player at the plinth gets no warning,
    which is an ambush the fairness contract does not allow.
    """
    bad = []
    for pl in e.plinths:
        path = e.path(e.curator_spawn, pl["room"])
        if path is None:
            continue                      # V7's problem, not this one
        walls = sum(1 for a, b in zip(path, path[1:])
                    if (e.portal_between(a, b) or {}).get("door"))
        heard = APPROACH_L * OCCLUSION ** walls
        if heard < AUDIBILITY_FLOOR:
            bad.append(f"{pl['room']}: {walls} doors from the Curator's spawn, "
                       f"approach heard at {heard:.0f} against a floor of "
                       f"{AUDIBILITY_FLOOR:.0f}")
    return not bad, "; ".join(sorted(set(bad)))


def V6_portal_graph(e):
    bad = []
    for p in e.portals:
        for side in ("a", "b"):
            if p[side] not in e.rooms:
                bad.append(f"portal references missing room {p[side]}")
        if not p.get("door") and not p.get("archway"):
            bad.append(f"{p['a']}<->{p['b']} is neither door nor declared archway")
    for r in e.rooms:
        if not any(r in (p["a"], p["b"]) for p in e.portals):
            bad.append(f"{r} has no portals")
    return not bad, "; ".join(bad)


def V7_curator_navmesh(e):
    g = e.adj()
    seen, q = {e.curator_spawn}, deque([e.curator_spawn])
    while q:
        for n in g[q.popleft()]:
            if n not in seen:
                seen.add(n)
                q.append(n)
    bad = [pl["room"] for pl in e.plinths if pl["room"] not in seen]
    return not bad, f"Curator cannot reach plinths in {sorted(set(bad))}" if bad else ""


def V8_value_bands(e):
    bad = []
    for pl in e.plinths:
        lo, hi = VALUE_BANDS[pl["tier"]]
        if not lo <= pl["value"] <= hi:
            bad.append(f"{pl['room']} ${pl['value']:,} outside tier-{pl['tier']} band")
    return not bad, "; ".join(bad)


def V9_no_free_money(e):
    """No *valuable* plinth adjacent to the van.

    Tier 0 is exempt by design: ECONOMY.md 3 wants cheap foyer loot right by the door
    as the tutorial nobody notices. The rule is about free money, not about proximity.
    """
    bad = [f"tier-{pl['tier']} plinth in {pl['room']} is "
           f"{e.dist(pl['room'], e.van):.0f}m from the van"
           for pl in e.plinths
           if pl["tier"] >= 1 and e.dist(pl["room"], e.van) < 15.0]
    return not bad, "; ".join(sorted(set(bad)))


def V10_it_fits(e):
    """The piano check. Does a route exist wide enough to actually carry it out?"""
    bad = []
    for pl in e.plinths:
        w = CLASS_WIDTH[pl["cls"]]
        if e.path(pl["room"], e.van, min_width=w) is None:
            bad.append(f"{pl['cls']} in {pl['room']} cannot fit any route to the van "
                       f"(needs {w}m clear)")
    return not bad, "; ".join(bad)


CHECKS = [
    ("V1  reachability", V1_reachable),
    ("V2  depth pacing", V2_depth_pacing),
    ("V3  second route", V3_two_routes),
    ("V4  pinch points", V4_pinch_points),
    ("V5  audibility", V5_audibility),
    ("V6  portal graph", V6_portal_graph),
    ("V7  curator navmesh", V7_curator_navmesh),
    ("V8  value bands", V8_value_bands),
    ("V9  no free money", V9_no_free_money),
    ("V10 it fits", V10_it_fits),
]


def self_test(verbose=True):
    """
    Both directions. A validator that only ever passes clean estates proves
    nothing - BROKEN_B carries one planted fault per check, and the test
    asserts the exact set, not merely "something failed".
    """
    import estates

    problems = []
    for name in ("MANOR_A", "COACH_HOUSE_C"):
        clean = validate(getattr(estates, name), verbose)
        if clean:
            problems.append(f"{name} should pass all ten checks, failed {sorted(clean)}")

    broken = set(validate(estates.BROKEN_B, verbose))
    missed = estates.EXPECTED_FAILURES - broken
    spurious = broken - estates.EXPECTED_FAILURES
    if missed:
        problems.append(f"BROKEN_B has planted faults the checks did not catch: "
                        f"{sorted(missed)}")
    if spurious:
        problems.append(f"BROKEN_B failed checks nothing was planted for: "
                        f"{sorted(spurious)}")

    # R20: one estate per check, each with a single planted fault. Without this,
    # "the validator passes" only ever meant seven of the ten checks had been
    # shown to fire - and the three that hadn't included V5, which was measuring
    # doors between the plinth and the VAN when the thing it is about is the
    # Curator's approach. A check that has never failed is not a check.
    if verbose:
        print(f"\n{'=' * 78}\nCAN EVERY CHECK ACTUALLY FAIL?\n{'=' * 78}")
    for check, estate in estates.FAULTS.items():
        failed = set(validate(estate, verbose=False))
        if check.split("-")[0] not in failed:
            problems.append(f"{check} did not fire on an estate built to break it "
                            f"(fired: {sorted(failed) or 'nothing'})")
        elif verbose:
            others = sorted(failed - {check.split("-")[0]},
                            key=lambda c: int(c[1:]))
            print(f"  {check:<4} fires"
                  + (f"   (also trips {', '.join(others)} - one fault, several "
                     f"consequences)" if others else ""))

    if verbose:
        print()
        for p in problems:
            print(f"  FAIL  {p}")
        if not problems:
            print(f"  OK   both clean estates pass 10/10, the broken estate trips "
                  f"exactly {len(estates.EXPECTED_FAILURES)} planted faults, and "
                  f"all {len(estates.FAULTS)} fault estates fire the check they "
                  f"were built for")
    return problems


def validate(d, verbose=True):
    e = Estate(d)
    failed = []
    if verbose:
        print(f"\n{'=' * 78}\nESTATE: {e.id}\n{'=' * 78}")
    for name, fn in CHECKS:
        ok, msg = fn(e)
        if not ok:
            failed.append(name.split()[0])
        if verbose:
            print(f"  {'PASS' if ok else 'FAIL'}  {name:<22}{msg}")
    if verbose:
        verdict = "ENTERS POOL" if not failed else f"REJECTED ({', '.join(failed)})"
        print(f"  -> {verdict}")
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(1 if self_test() else 0)
