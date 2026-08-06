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
import pathlib
import sys
import math

# Minimum clear width to move each class through a doorway.
CLASS_WIDTH = {"pocket": 0.7, "armful": 0.9, "two_man": 1.6, "cart": 2.2}
CLASS_SLOTS = {"pocket": 0.5, "armful": 1.0, "two_man": 3.0, "cart": 5.0}

# ECONOMY.md 3
VALUE_BANDS = {
    0: (40, 300), 1: (80, 300), 2: (250, 1900), 3: (600, 4000), 4: (4000, 8000),
}

# ECONOMY.md 3, per class. The coarse per-tier band above spans both classes and
# therefore cannot catch a two-man piece priced like an armful, which is the exact
# error the apex re-band was about: two-man must be slightly WORSE per slot, never
# better, or the logistics object is also the efficient one.
CLASS_BANDS = {
    (0, "pocket"): (40, 150), (1, "pocket"): (40, 150),
    (0, "armful"): (80, 300), (1, "armful"): (80, 300),
    (2, "armful"): (250, 700), (2, "two_man"): (700, 1900),
    (3, "armful"): (600, 1400), (3, "two_man"): (1800, 4000),
    (4, "cart"): (4000, 8000),
}

# DESIGN.md 4.2 / D-11. A curse grade multiplies the piece's value; a malignant
# tier-1 vase is legitimately worth six times its band and is not a banding fault.
GRADE_MULT = {"clean": 1.0, "tainted": 2.5, "malignant": 6.0}

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
    core = e.rooms[e.van].get("core_link", "foyer")
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
    """AUDIO-SPEC 3.1: the Curator must stay audible through the wing's geometry."""
    bad = []
    for pl in e.plinths:
        path = e.path(pl["room"], e.van)
        if path is None:
            continue
        walls = sum(1 for a, b in zip(path, path[1:])
                    if (e.portal_between(a, b) or {}).get("door"))
        if APPROACH_L * OCCLUSION ** walls < AUDIBILITY_FLOOR:
            bad.append(f"{pl['room']}: {walls} doors to van, approach bus inaudible")
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
    """Banding is checked on the piece BEFORE its curse multiplier.

    The first run of this check against the prototype rejected it on nine plinths,
    all of which were correctly banded pieces that happened to be cursed - a
    malignant tier-3 vase is six times its band by design (D-11), and a check that
    calls that a fault would reject every estate with cursed loot in it. The
    multiplier is divided out, and the per-class band is checked as well, which the
    coarse per-tier band cannot do.
    """
    bad = []
    for pl in e.plinths:
        base = pl["value"] / GRADE_MULT.get(pl.get("grade", "clean"), 1.0)
        lo, hi = VALUE_BANDS[pl["tier"]]
        if not lo <= base <= hi:
            bad.append(f"{pl['room']} ${base:,.0f} outside tier-{pl['tier']} band")
            continue
        cb = CLASS_BANDS.get((pl["tier"], pl["cls"]))
        if cb and not cb[0] <= base <= cb[1]:
            bad.append(f"{pl['room']} ${base:,.0f} outside tier-{pl['tier']} "
                       f"{pl['cls']} band {cb[0]}-{cb[1]}")
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


# --------------------------------------------------------------------------- CLI
# Until R18 this module had no entry point at all: `python sim/validate_estate.py`
# ran zero checks and exited 0, and several rounds recorded "estate validator PASS"
# on the strength of it. A regression command that cannot fail is worse than none,
# because it is the one nobody re-reads.
def main():
    from estates import MANOR_A, BROKEN_B, EXPECTED_FAILURES

    verbose = "-q" not in sys.argv
    problems = []

    # A single estate from a file - the prototype dumps itself in this schema via
    # `node proto3d/dump-estate.mjs`. An estate that fails here does not enter the
    # pool, whether it came from a document or from the thing people are playing.
    if "--estate" in sys.argv:
        import json
        path = sys.argv[sys.argv.index("--estate") + 1]
        d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        failed = validate(d, True)
        print(f"\n{'-' * 74}")
        if failed:
            print(f"  REJECTED  {d['id']}  failed {', '.join(sorted(failed))}")
            return 1
        print(f"  OK   {d['id']} enters the pool")
        return 0

    clean = validate(MANOR_A, verbose)
    if clean:
        problems.append(f"MANOR_A should enter the pool, failed {sorted(clean)}")

    broken = set(validate(BROKEN_B, verbose))
    if broken != EXPECTED_FAILURES:
        missed = sorted(EXPECTED_FAILURES - broken)
        spurious = sorted(broken - EXPECTED_FAILURES)
        if missed:
            problems.append(f"planted faults NOT caught: {missed}")
        if spurious:
            problems.append(f"unplanted faults reported: {spurious}")

    print(f"\nESTATE VALIDATOR  -  {len(CHECKS)} checks x 2 estates")
    print("-" * 74)
    if not problems:
        print("  OK   clean estate enters the pool, broken estate trips exactly "
              f"its {len(EXPECTED_FAILURES)} planted faults")
        return 0
    for p in problems:
        print(f"  FAIL  {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
