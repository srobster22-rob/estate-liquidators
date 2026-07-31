"""
Mutation test for the estate validator.

    python3 sim/check_estates.py     ->  exit 0 if every check can actually fail

--------------------------------------------------------------------------------
WHY THIS EXISTS (LOOP_LOG R18)

`validate_estate.py` had no entry point. Its docstring said "Run: python
validate_estate.py"; running it produced zero output and exited 0, because the file
defines `validate()` and never calls it. Nothing in the repo imported `estates.py`
or called `validate()`. So `EXPECTED_FAILURES` - the seven planted faults R1 says it
verified - was asserted by nothing, and R17's regression line "all nine sims exit 0"
counted this file's silence as a pass.

Worse, BROKEN_B only ever planted faults for **seven** of the ten checks. V1, V5 and
V7 had never been shown to fail at all. A check that has never failed is not a check;
it is a line of code that prints PASS.

So this file proves each check can fail, by mutating a known-good estate one fault at
a time and asserting the intended check fires. A check that cannot be tripped is
reported as a failure of THIS file, not quietly skipped.

The rule it enforces: every check in CHECKS must have a mutant that trips it.
"""

import copy
import sys

from estates import MANOR_A, BROKEN_B, EXPECTED_FAILURES
from validate_estate import CHECKS, CLASS_WIDTH, validate

fails = []


# ---------------------------------------------------------------- mutations
# Each returns a copy of MANOR_A with exactly one fault, aimed at one check.

def m_v1(d):
    """Two rooms wired to each other and to nothing else."""
    d["rooms"]["shed"] = {"pos": (-20, -20), "tier": 0}
    d["rooms"]["yard"] = {"pos": (-26, -20), "tier": 0}
    d["portals"].append({"a": "shed", "b": "yard", "width": 2.5, "door": True})
    return d


def m_v2(d):
    """A tier-3 room that opens with no prerequisite work at all."""
    d["prereqs"]["orangery"] = []
    return d


def m_v3(d):
    """Remove the service-hall alternative, leaving a single corridor in."""
    d["portals"] = [p for p in d["portals"]
                    if {p["a"], p["b"]} != {"service_hall", "landing"}]
    return d


def m_v4(d):
    """Strip the pinch off the conservatory approach, opening a safe bypass."""
    for p in d["portals"]:
        if {p["a"], p["b"]} == {"landing", "conservatory"}:
            p["pinch"] = False
    return d


def m_v5(d):
    """A plinth six doors deep, so the approach bus attenuates below the floor."""
    d["rooms"]["cellar"] = {"pos": (78, 8), "tier": 0}
    d["portals"].append({"a": "orangery", "b": "cellar", "width": 2.5, "door": True})
    d["plinths"].append({"room": "cellar", "cls": "armful", "tier": 0, "value": 120})
    return d


def m_v6(d):
    """An opening that is neither a door nor a declared archway."""
    d["portals"].append({"a": "service_hall", "b": "study", "width": 2.5})
    return d


def m_v7(d):
    """Curator spawns behind a gap too narrow to carry the cart-class item through.

    Everything stays connected at zero width, so V1 still passes - which is the whole
    point. Before R18's fix, V7 BFS'd at width 0 and could only fail when V1 already
    had, making it strictly redundant.
    """
    d["rooms"]["attic"] = {"pos": (36, 12), "tier": 0}
    d["portals"].append({"a": "landing", "b": "attic", "width": 1.0, "door": True,
                         "pinch": False})
    d["curator_spawn"] = "attic"
    return d


def m_v8(d):
    """A tier-1 plinth priced like tier 3."""
    d["plinths"].append({"room": "study", "cls": "armful", "tier": 1, "value": 2400})
    return d


def m_v9(d):
    """Free money parked next to the van."""
    d["rooms"]["cloakroom"] = {"pos": (14, 2), "tier": 1}
    d["portals"].append({"a": "foyer", "b": "cloakroom", "width": 2.5, "door": True})
    d["plinths"].append({"room": "cloakroom", "cls": "armful", "tier": 1,
                         "value": 280})
    return d


def m_v10(d):
    """Narrow every cart-wide route out of the office. The piano check."""
    for p in d["portals"]:
        if {p["a"], p["b"]} in ({"conservatory", "office"}, {"landing", "office"}):
            p["width"] = 1.1
    return d


MUTANTS = [
    ("V1", m_v1, "orphan room pair"),
    ("V2", m_v2, "tier-3 room with no prerequisites"),
    ("V3", m_v3, "single corridor into the wing"),
    ("V4", m_v4, "unpinched bypass to a tier-3 plinth"),
    ("V5", m_v5, "plinth six doors from the van"),
    ("V6", m_v6, "portal that is neither door nor archway"),
    ("V7", m_v7, "Curator cannot carry the cart back to its plinth"),
    ("V8", m_v8, "tier-1 plinth priced like tier 3"),
    ("V9", m_v9, "tier-1 plinth beside the van"),
    ("V10", m_v10, "cart cannot fit any route out"),
]


def run(mut):
    d = mut(copy.deepcopy(MANOR_A))
    d["id"] = "mutant"
    return set(validate(d, verbose=False))


# ---------------------------------------------------------------- the suite
print("ESTATE VALIDATOR - MUTATION TEST")
print("=" * 78)

# Control. If the known-good estate does not pass, nothing below means anything.
clean = set(validate(MANOR_A, verbose=False))
print(f"\nCONTROL   MANOR_A passes all {len(CHECKS)} checks ... ", end="")
if clean:
    print(f"NO - fails {sorted(clean)}")
    fails.append(f"MANOR_A should pass every check but fails {sorted(clean)}")
else:
    print("yes")

# The fixture nobody was asserting.
broken = set(validate(BROKEN_B, verbose=False))
print(f"FIXTURE   BROKEN_B trips exactly its planted faults ... ", end="")
if broken == EXPECTED_FAILURES:
    print("yes")
else:
    print("NO")
    if EXPECTED_FAILURES - broken:
        fails.append(f"BROKEN_B plants {sorted(EXPECTED_FAILURES - broken)} "
                     f"but they do not fire")
    if broken - EXPECTED_FAILURES:
        fails.append(f"BROKEN_B trips {sorted(broken - EXPECTED_FAILURES)} "
                     f"which it does not claim to plant")

# One mutant per check.
print(f"\nMUTANTS   one targeted fault each; the named check must fire")
print("-" * 78)
tripped = set()
for target, mut, desc in MUTANTS:
    got = run(mut)
    hit = target in got
    collateral = sorted(got - {target})
    if hit:
        tripped.add(target)
    note = f"also {collateral}" if collateral else "isolated"
    print(f"  {'TRIP' if hit else '****'}  {target:<4} {desc:<46}{note}")
    if not hit:
        fails.append(f"{target}: mutant '{desc}' did not trip it "
                     f"(fired: {sorted(got) or 'nothing'}). The check cannot fail.")

# Every check must be reachable by some mutant.
names = {n.split()[0] for n, _ in CHECKS}
never = sorted(names - tripped, key=lambda s: int(s[1:]))
print("-" * 78)
print(f"  {len(tripped)}/{len(names)} checks proven able to fail")

for n in never:
    fails.append(f"{n} is in CHECKS but no mutant trips it - it cannot detect anything.")

print()
if not fails:
    print("  OK   every check in validate_estate.py can actually fail")
    sys.exit(0)
for f in fails:
    print(f"  FAIL  {f}")
print(f"\n{len(fails)} problem(s).")
sys.exit(1)
