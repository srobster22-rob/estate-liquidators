"""
Sample estates for the validator.

MANOR_A is the worked example from LEVEL-SPEC.md 8 (East Conservatory), built to pass.
BROKEN_B is the same estate with seven deliberate faults, used to prove the validator
detects things rather than just printing PASS ten times. It trips EIGHT checks: V7
fires as a consequence of the V10 fault, not as a planted one (see EXPECTED_FAILURES).

Seven faults for ten checks was never full coverage, and nothing asserted even that
until R18 — see sim/check_estates.py, which mutates this estate one fault at a time
and requires every check to be provably able to fail.
"""

import copy

MANOR_A = {
    "id": "manor_a  (LEVEL-SPEC 8 worked example)",
    "curator_spawn": "orangery",
    "rooms": {
        "driveway":     {"pos": (0, 0),    "tier": 0, "van": True},
        "foyer":        {"pos": (12, 0),   "tier": 0},
        "grand_stair":  {"pos": (24, 0),   "tier": 1},
        "service_hall": {"pos": (20, -14), "tier": 1},
        "study":        {"pos": (34, 8),   "tier": 1},
        "landing":      {"pos": (36, 0),   "tier": 2},
        "conservatory": {"pos": (52, 4),   "tier": 3},
        "potting_room": {"pos": (60, 10),  "tier": 3},
        "orangery":     {"pos": (68, 6),   "tier": 3},
        "office":       {"pos": (58, -4),  "tier": 4},
    },
    "portals": [
        {"a": "driveway", "b": "foyer", "width": 3.0, "door": True,
         "entrance": True},
        {"a": "foyer", "b": "grand_stair", "width": 2.6, "door": True},
        {"a": "foyer", "b": "service_hall", "width": 2.4, "door": True,
         "pinch": True},
        {"a": "grand_stair", "b": "study", "width": 1.8, "door": True,
         "pinch": True},
        {"a": "study", "b": "landing", "width": 1.7, "door": True,
         "pinch": True},
        {"a": "grand_stair", "b": "landing", "width": 2.4, "door": True,
         "pinch": True},
        {"a": "service_hall", "b": "landing", "width": 2.3, "door": True,
         "pinch": True},
        {"a": "landing", "b": "conservatory", "width": 2.3, "door": True,
         "pinch": True},
        {"a": "conservatory", "b": "potting_room", "width": 2.3, "door": True,
         "pinch": True},
        {"a": "potting_room", "b": "orangery", "width": 2.4, "door": True,
         "pinch": True},
        {"a": "conservatory", "b": "orangery", "width": 2.4, "door": True,
         "pinch": True},
        {"a": "conservatory", "b": "office", "width": 2.3, "door": True,
         "pinch": True},
        {"a": "landing", "b": "office", "width": 2.3, "door": True,
         "pinch": True},
    ],
    "prereqs": {
        "landing":      [{"room": "grand_stair", "type": "clear"}],
        "conservatory": [{"room": "study", "type": "key"},
                         {"room": "landing", "type": "clear"}],
        "potting_room": [{"room": "landing", "type": "clear"},
                         {"room": "study", "type": "key"}],
        "orangery":     [{"room": "study", "type": "key"},
                         {"room": "landing", "type": "clear"}],
        "office":       [{"room": "conservatory", "type": "key"}],
    },
    "plinths": [
        {"room": "foyer", "cls": "armful", "tier": 0, "value": 120},
        {"room": "study", "cls": "armful", "tier": 1, "value": 260},
        {"room": "landing", "cls": "armful", "tier": 2, "value": 540},
        {"room": "landing", "cls": "two_man", "tier": 2, "value": 1500},
        {"room": "conservatory", "cls": "armful", "tier": 3, "value": 1200},
        {"room": "potting_room", "cls": "armful", "tier": 3, "value": 900},
        {"room": "orangery", "cls": "two_man", "tier": 3, "value": 3200},
        {"room": "office", "cls": "cart", "tier": 4, "value": 6400},
    ],
}


def _broken():
    d = copy.deepcopy(MANOR_A)
    d["id"] = "broken_b  (seven planted faults; trips eight checks)"

    # V10 — the piano check. Narrow the ONLY cart-wide route out of the office.
    for p in d["portals"]:
        if {p["a"], p["b"]} == {"conservatory", "office"}:
            p["width"] = 1.1
        if {p["a"], p["b"]} == {"landing", "office"}:
            p["width"] = 1.1

    # V3 — remove the service-hall alternative, leaving one route in.
    d["portals"] = [p for p in d["portals"]
                    if {p["a"], p["b"]} != {"service_hall", "landing"}]

    # V4 — strip pinch flags from the conservatory approach.
    for p in d["portals"]:
        if {p["a"], p["b"]} == {"landing", "conservatory"}:
            p["pinch"] = False

    # V2 — let the tier-3 orangery open with no prerequisites at all.
    d["prereqs"]["orangery"] = []

    # V6 — an undeclared opening with no door.
    d["portals"].append({"a": "service_hall", "b": "study", "width": 2.0})

    # V8 — a tier-1 plinth priced like tier 3.
    d["plinths"].append({"room": "study", "cls": "armful", "tier": 1, "value": 2400})

    # V9 — free money parked next to the van.
    d["rooms"]["cloakroom"] = {"pos": (14, 2), "tier": 1}
    d["portals"].append({"a": "foyer", "b": "cloakroom", "width": 2.0, "door": True})
    d["plinths"].append({"room": "cloakroom", "cls": "armful", "tier": 1,
                         "value": 280})
    return d


BROKEN_B = _broken()

# What BROKEN_B is built to trip. sim/check_estates.py asserts exactly this set —
# and until R18 nothing did, because validate_estate.py had no entry point and nobody
# imported this module.
#
# V7 is here as a CONSEQUENCE, not a planted fault. The V10 narrowing above takes the
# office down to 1.1m, and a route too narrow for four players to carry a piano out is
# also too narrow for the Curator to carry it back — so R18's strengthened V7 fires on
# the same geometry. Verified by restoring the two office portal widths: V7 and V10
# both clear together. The coupling is real and worth keeping visible.
EXPECTED_FAILURES = {"V2", "V3", "V4", "V6", "V7", "V8", "V9", "V10"}
