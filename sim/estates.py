"""
Sample estates for the validator.

MANOR_A is the worked example from LEVEL-SPEC.md 8 (East Conservatory), built to pass.
BROKEN_B is the same estate with ten deliberate faults, one per check, used to prove
the validator actually detects things rather than just printing PASS ten times.
"""

import copy

MANOR_A = {
    "id": "manor_a  (LEVEL-SPEC 8 worked example)",
    "curator_spawn": "orangery",
    "rooms": {
        "driveway":     {"pos": (0, 0),    "tier": 0, "van": True},
        "foyer":        {"pos": (12, 0),   "tier": 0, "value_class": "shelf"},
        "grand_stair":  {"pos": (24, 0),   "tier": 1, "value_class": "shelf"},
        "service_hall": {"pos": (20, -14), "tier": 1, "value_class": "shelf"},
        "study":        {"pos": (34, 8),   "tier": 1, "value_class": "curio"},
        "landing":      {"pos": (36, 0),   "tier": 2, "value_class": "mixed"},
        "conservatory": {"pos": (52, 4),   "tier": 3, "value_class": "mixed"},
        "potting_room": {"pos": (60, 10),  "tier": 3, "value_class": "shelf"},
        "orangery":     {"pos": (68, 6),   "tier": 3, "value_class": "curio"},
        "office":       {"pos": (58, -4),  "tier": 4, "value_class": "mixed"},
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
    "hiding_places": [
        {"id": "h1", "room": "foyer"},
        {"id": "h2", "room": "landing"},
        {"id": "h3", "room": "conservatory"},
        {"id": "h4", "room": "orangery"},
    ],
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
    d["id"] = "broken_b  (ten deliberate faults)"

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

    # V5 — an ambush room. Slide the potting room in until it is 5.8m from the
    # conservatory, so the Curator can cross between them in under the 8m of approach
    # the fairness contract promises. Nothing about the topology changes and every
    # other check still passes on it, which is the point: this is a fault you cannot
    # see in a portal graph, only in the distances.
    d["rooms"]["potting_room"]["pos"] = (57, 7)

    # V11 — a flat house. Every room evenly priced, so scanning has a fixed rate of
    # return everywhere and the appraiser is a habit rather than a decision. This is
    # the fault that looks like nothing wrong: every room individually is fine.
    for room in ("study", "orangery"):
        d["rooms"][room]["value_class"] = "shelf"

    # V12 — pull the orangery's wardrobe. Three hiding places is still above the
    # minimum, so the count check passes and the COVERAGE check is what catches it:
    # the orangery's two-man piece is now 16m from the nearest concealment, which
    # means the deepest room in the wing has no answer to being hunted.
    d["hiding_places"] = [h for h in d["hiding_places"] if h["id"] != "h4"]

    # V9 — free money parked next to the van.
    d["rooms"]["cloakroom"] = {"pos": (14, 2), "tier": 1, "value_class": "mixed"}
    d["portals"].append({"a": "foyer", "b": "cloakroom", "width": 2.0, "door": True})
    d["plinths"].append({"room": "cloakroom", "cls": "armful", "tier": 1,
                         "value": 280})
    return d


BROKEN_B = _broken()

# What BROKEN_B is built to trip. The test asserts exactly this set.
EXPECTED_FAILURES = {"V2", "V3", "V4", "V5", "V6", "V8", "V9", "V10", "V11",
                     "V12"}
