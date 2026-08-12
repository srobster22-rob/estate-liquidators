"""
Sample estates for the validator.

MANOR_A is the worked example from LEVEL-SPEC.md 8 (East Conservatory), built to pass.
BROKEN_B is the same estate with seven deliberate faults, one per check, used to prove
the validator actually detects things rather than just printing PASS ten times.
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
    d["id"] = "broken_b  (seven deliberate faults)"

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

# What BROKEN_B is built to trip. The test asserts exactly this set.
EXPECTED_FAILURES = {"V2", "V3", "V4", "V6", "V8", "V9", "V10"}


# ---------------------------------------------------------------- single faults
#
# R20. BROKEN_B plants seven faults at once, which proves seven checks can fire
# and says nothing at all about the other three. V1, V5 and V7 had never failed
# anything in this repository - and V5 turned out to be measuring the wrong pair
# of rooms entirely, which is exactly what "has never failed" is evidence of.
#
# One estate per check, each carrying a single deliberate fault. A fault often
# trips neighbouring checks too (an unreachable room is unreachable for the
# Curator as well), so the test asserts the TARGET check fires, not that it
# fires alone.


def _fault(name, mutate):
    d = copy.deepcopy(MANOR_A)
    d["id"] = f"fault_{name.lower()}  ({name} only)"
    mutate(d)
    return d


def _v1(d):
    """A room nothing connects to. The classic copy-paste-a-wing mistake."""
    d["rooms"]["ice_house"] = {"pos": (90, 30), "tier": 1}


def _v2(d):
    """Tier 3 that opens immediately - depth without the work that gates it."""
    d["prereqs"]["orangery"] = []


def _v3(d):
    """A wing on one corridor: lose that portal and the crew is sealed in."""
    d["rooms"]["cold_store"] = {"pos": (26, -22), "tier": 1}
    d["portals"].append({"a": "service_hall", "b": "cold_store", "width": 2.4,
                         "door": True, "pinch": True})


def _v4(d):
    """A wide, unpinched bypass straight to the deep wing - V3's usual side-effect."""
    d["portals"].append({"a": "foyer", "b": "conservatory", "width": 3.2,
                         "door": True, "pinch": False})


def _v5(d):
    """
    Loot buried six closed doors from where the Curator starts. The approach bus
    arrives at 22 against a floor of 25, so the first warning you get is the
    thing itself. Tier 0 throughout so this trips V5 and nothing else.
    """
    chain = [("scullery", (14, -26)), ("coal_store", (10, -36)),
             ("boot_room", (6, -46))]
    prev = "service_hall"
    for room, pos in chain:
        d["rooms"][room] = {"pos": pos, "tier": 0}
        d["portals"].append({"a": prev, "b": room, "width": 3.0, "door": True})
        prev = room
    # No shortcut back to the foyer: a second route would shorten the Curator's
    # approach to four doors, which is audible, and the fault would evaporate.
    # Tier 0 keeps V3 out of it - the fairness contract is about wings, and a
    # scullery chain is not one.
    d["plinths"].append({"room": "boot_room", "cls": "armful", "tier": 0,
                         "value": 200})


def _v6(d):
    """An opening that is neither door nor declared archway."""
    d["portals"].append({"a": "service_hall", "b": "study", "width": 2.0,
                         "pinch": False})


def _v7(d):
    """The Curator spawns somewhere it cannot leave."""
    d["rooms"]["gate_lodge"] = {"pos": (-20, 0), "tier": 0}
    d["curator_spawn"] = "gate_lodge"


def _v8(d):
    """A tier-1 plinth priced like tier 3."""
    d["plinths"].append({"room": "study", "cls": "armful", "tier": 1,
                         "value": 2400})


def _v9(d):
    """Free money parked next to the van."""
    d["rooms"]["cloakroom"] = {"pos": (14, 2), "tier": 1}
    d["portals"].append({"a": "foyer", "b": "cloakroom", "width": 2.0,
                         "door": True, "pinch": False})
    d["portals"].append({"a": "grand_stair", "b": "cloakroom", "width": 2.2,
                         "door": True, "pinch": True})
    d["plinths"].append({"room": "cloakroom", "cls": "armful", "tier": 1,
                         "value": 280})


def _v10(d):
    """The piano check: an apex behind doorways it cannot physically pass."""
    for p in d["portals"]:
        if "office" in (p["a"], p["b"]):
            p["width"] = 1.9


def _v3_no_core(d):
    """
    The contract's hidden required field. Without `core_link` the fairness check
    silently measured redundancy to a room called "foyer" - which only MANOR_A
    has - and reported every wing sealed off by an arbitrary portal.
    """
    _v3(d)
    d["rooms"]["driveway"].pop("core_link", None)


FAULTS = {
    "V1": _fault("V1", _v1), "V2": _fault("V2", _v2), "V3": _fault("V3", _v3),
    "V4": _fault("V4", _v4), "V5": _fault("V5", _v5), "V6": _fault("V6", _v6),
    "V7": _fault("V7", _v7), "V8": _fault("V8", _v8), "V9": _fault("V9", _v9),
    "V10": _fault("V10", _v10),
    # Same check, a second way to break it - and the one an author actually hits.
    "V3-no-core": _fault("V3-no-core", _v3_no_core),
}


# ---------------------------------------------------------------- a second estate
#
# R29. MANOR_A is the contract's own worked example, and R1 found even that one
# invalid on its first pass. One estate that passes is not evidence the contract
# is AUTHORABLE - it is evidence one estate was fixed until it passed. So this is
# a second wing, drawn to a different shape (a service spine with a courtyard
# loop rather than a stair-and-landing hub), authored from LEVEL-SPEC's rules
# rather than by copying MANOR_A's topology, and run against the ten checks to
# see what the contract does to somebody following it.

COACH_HOUSE_C = {
    "id": "coach_house_c  (R29, authored from the contract)",
    "curator_spawn": "clock_tower",
    "rooms": {
        "yard":        {"pos": (0, 0),    "tier": 0, "van": True,
                        "core_link": "boot_room"},
        "boot_room":   {"pos": (12, 0),   "tier": 0},
        "kitchen":     {"pos": (24, 6),   "tier": 1},
        "scullery":    {"pos": (24, -8),  "tier": 1},
        "back_stair":  {"pos": (34, -1),  "tier": 1},
        "gallery":     {"pos": (46, 2),   "tier": 2},
        "nursery":     {"pos": (58, 9),   "tier": 3},
        "workshop":    {"pos": (58, -7),  "tier": 3},
        "clock_tower": {"pos": (70, 1),   "tier": 4},
    },
    "portals": [
        {"a": "yard", "b": "boot_room", "width": 3.2, "door": True, "entrance": True},
        {"a": "boot_room", "b": "kitchen", "width": 2.4, "door": True, "pinch": True},
        {"a": "boot_room", "b": "scullery", "width": 2.2, "door": True, "pinch": True},
        {"a": "kitchen", "b": "back_stair", "width": 2.6, "door": True},
        {"a": "scullery", "b": "back_stair", "width": 2.3, "door": True, "pinch": True},
        {"a": "back_stair", "b": "gallery", "width": 2.4, "door": True, "pinch": True},
        {"a": "scullery", "b": "gallery", "width": 2.3, "door": True, "pinch": True},
        {"a": "gallery", "b": "nursery", "width": 2.3, "door": True, "pinch": True},
        {"a": "gallery", "b": "workshop", "width": 2.3, "door": True, "pinch": True},
        {"a": "nursery", "b": "workshop", "width": 2.3, "door": True, "pinch": True},
        {"a": "nursery", "b": "clock_tower", "width": 2.4, "door": True, "pinch": True},
        {"a": "workshop", "b": "clock_tower", "width": 2.4, "door": True, "pinch": True},
    ],
    "prereqs": {
        "gallery":     [{"room": "kitchen", "type": "key"}],
        "nursery":     [{"room": "gallery", "type": "clear"}],
        "workshop":    [{"room": "gallery", "type": "clear"}],
        "clock_tower": [{"room": "nursery", "type": "key"}],
    },
    "plinths": [
        {"room": "boot_room", "cls": "armful", "tier": 0, "value": 130},
        {"room": "kitchen", "cls": "armful", "tier": 1, "value": 220},
        {"room": "scullery", "cls": "pocket", "tier": 1, "value": 95},
        {"room": "gallery", "cls": "armful", "tier": 2, "value": 520},
        {"room": "gallery", "cls": "two_man", "tier": 2, "value": 1500},
        {"room": "nursery", "cls": "armful", "tier": 3, "value": 1100},
        {"room": "workshop", "cls": "two_man", "tier": 3, "value": 3000},
        {"room": "clock_tower", "cls": "cart", "tier": 4, "value": 6000},
    ],
}
