"""
Sample estates for the validator.

MANOR_A is the worked example from LEVEL-SPEC.md 8 (East Conservatory), built to pass.
BROKEN_B is the same estate with eight deliberate faults, one per check, used to prove
the validator actually detects things rather than just printing PASS eleven times.
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
        "study":        {"pos": (34, 8),   "tier": 1, "spread": "curio"},
        "landing":      {"pos": (36, 0),   "tier": 2, "spread": "uniform"},
        "conservatory": {"pos": (52, 4),   "tier": 3, "spread": "curio"},
        "potting_room": {"pos": (60, 10),  "tier": 3, "spread": "uniform"},
        "orangery":     {"pos": (68, 6),   "tier": 3, "spread": "mixed"},
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
    d["id"] = "broken_b  (eight deliberate faults)"

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

    # V11 — every room the same shade of interesting. This is the DEFAULT an author
    # produces when nothing asks them for a mix, which is exactly why it is planted:
    # the estate reads fine and quietly deletes the appraiser's decision.
    for r in ("study", "landing", "conservatory", "potting_room", "orangery"):
        d["rooms"][r]["spread"] = "mixed"

    # V9 — free money parked next to the van.
    d["rooms"]["cloakroom"] = {"pos": (14, 2), "tier": 1}
    d["portals"].append({"a": "foyer", "b": "cloakroom", "width": 2.0, "door": True})
    d["rooms"]["cloakroom"]["spread"] = "mixed"
    d["plinths"].append({"room": "cloakroom", "cls": "armful", "tier": 1,
                         "value": 280})
    return d


BROKEN_B = _broken()

# What BROKEN_B is built to trip. The test asserts exactly this set.
EXPECTED_FAILURES = {"V2", "V3", "V4", "V6", "V8", "V9", "V10", "V11"}
