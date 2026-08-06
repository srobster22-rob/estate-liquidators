"""
Drift check across every implementation of the rules.

tuning.json is canonical. The same constants live in the C# core, two browser
prototypes and five Python simulations, and this asserts they all still agree.
Reads every source as TEXT rather than executing it, so it needs no toolchain
and catches the exact failure that matters: a literal edited in one file and
not the others.

    python3 sim/check_drift.py          ->  exit 0 if everything agrees

WHAT CHANGED IN R16, AND WHY IT MATTERS
---------------------------------------
The first version of this file reported "55 constants agree" and was believed.
It was measuring the constants somebody had remembered to add. Three holes:

  1. `if got is not None: check(...)` - a C# loudness value that went MISSING
     was silently skipped instead of failing. A checker with a skip path
     cannot distinguish "agrees" from "absent".
  2. proto3d/index.html - a whole fourth implementation - was never read.
  3. Constants nobody wrote a pattern for (the cursed-item floor, the levers,
     retrieval rates, slot costs) were invisible, not reported as uncovered.

And the constant that had actually drifted was in the third category: both
prototypes still used the pre-R9 cursed floor of +2/item against a canonical
+7. The checker passed the whole time.

So coverage is now explicit and total. Every (source file x canonical
constant) pair must be either ASSERTED or WAIVED with a stated reason. A pair
that is neither is a failure - "coverage hole" - which means adding a constant
to tuning.json forces a decision about every file rather than defaulting to
silence.

Run `python3 sim/mutate_drift.py` to prove the assertions can actually fail.
"""

import fnmatch
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TUNING = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ canonical

def flatten(node, prefix=""):
    """Dotted paths to every scalar in tuning.json. Keys starting `_` are prose."""
    out = {}
    for k, v in node.items():
        if k.startswith("_"):
            continue
        path = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, path + "."))
        elif isinstance(v, (int, float)):
            out[path] = float(v)
    return out


CANON = flatten(TUNING)

FILES = {
    "cs/Loudness":    "unity/Assets/Scripts/Core/Loudness.cs",
    "cs/Attention":   "unity/Assets/Scripts/Core/Attention.cs",
    "cs/Disturbance": "unity/Assets/Scripts/Core/Disturbance.cs",
    "js/proto":       "proto/index.html",
    "js/proto3d":     "proto3d/index.html",
    "py/integrated":  "sim/integrated.py",
    "py/disturbance": "sim/disturbance.py",
    "py/curse_test":  "sim/curse_test.py",
    "py/haul_sim":    "sim/haul_sim.py",
    "py/chain_sim":   "sim/chain_sim.py",
}


# ------------------------------------------------------------------ assertions
# (file key, canonical path, regex, [scope regex], [capture group])
#
# `scope` narrows the text before matching - three of the C# curse tables and
# the JS loudness table all contain the same-shaped literals, and an
# unanchored match happily reports the wrong one. R14 lost time to exactly
# that: `sprint` matched the movement SPEED table and reported 205 px/s as a
# loudness.

A = []


def assert_(file, path, pattern, scope=None, group=1):
    A.append((file, path, pattern, scope, group))


# --- C# core -----------------------------------------------------------------
LC = "loudness_constants."
assert_("cs/Loudness", LC + "hearing_radius_per_l", r"HearingRadiusPerL\s*=\s*([\d.]+)f")
assert_("cs/Loudness", LC + "impulse_disturbance_per_l",
        r"ImpulseDisturbancePerL\s*=\s*([\d.]+)f")
assert_("cs/Loudness", LC + "sustained_disturbance_per_l",
        r"SustainedDisturbancePerL\s*=\s*([\d.]+)f")
assert_("cs/Loudness", LC + "occlusion_player", r"OcclusionPlayer\s*=\s*([\d.]+)f")
assert_("cs/Loudness", LC + "occlusion_curator", r"OcclusionCurator\s*=\s*([\d.]+)f")
assert_("cs/Loudness", LC + "localisation_fuzz_m", r"LocalisationFuzzM\s*=\s*([\d.]+)f")

# The enum name is not the tuning key. `appraise` is AppraisePing and `door` is
# DoorSlam, and the old auto-CamelCase loop silently skipped both.
CS_NOISE = {
    "crouch_walk": "CrouchWalk", "voice_whisper": "VoiceWhisper", "walk": "Walk",
    "voice_normal": "VoiceNormal", "dolly": "Dolly", "radio": "Radio",
    "sprint": "Sprint", "voice_raised": "VoiceRaised", "appraise": "AppraisePing",
    "door": "DoorSlam", "voice_shout": "VoiceShout", "crowbar": "Crowbar",
    "break_small": "BreakSmall", "break_large": "BreakLarge",
}
for key, enum in CS_NOISE.items():
    assert_("cs/Loudness", f"loudness.{key}", rf"NoiseKind\.{enum}\s*=>\s*(\d+)")

assert_("cs/Attention", "attention.noise_multiplier_per_event",
        r"NoisePerEvent\s*=\s*([\d.]+)f")
assert_("cs/Attention", "attention.light_multiplier", r"LightMultiplier\s*=\s*([\d.]+)f")
assert_("cs/Attention", "attention.steal_threshold", r"StealThreshold\s*=\s*([\d.]+)f")
assert_("cs/Attention", "attention.commit_seconds", r"CommitSeconds\s*=\s*([\d.]+)f")

CS_VALUE = r"float Value\(CurseGrade g\).*?\};"
CS_ATT = r"float Attention\(CurseGrade g\).*?\};"
CS_FEE = r"float Fee\(CurseGrade g\).*?\};"
for scope, group_path in ((CS_VALUE, "curse.value_multiplier"),
                          (CS_ATT, "curse.attention_multiplier"),
                          (CS_FEE, "curse.ledger_fee")):
    assert_("cs/Attention", group_path + ".tainted",
            r"CurseGrade\.Tainted\s*=>\s*([\d.]+)f", scope)
    assert_("cs/Attention", group_path + ".malignant",
            r"CurseGrade\.Malignant\s*=>\s*([\d.]+)f", scope)
    assert_("cs/Attention", group_path + ".clean", r"_\s*=>\s*([\d.]+)f?", scope)

D = "disturbance."
assert_("cs/Disturbance", D + "decay_per_min_at_crew4", r"DecayPerMinAtCrew4\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", D + "ratchet_end", r"RatchetEnd\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", D + "per_cursed_item_floor", r"PerCursedItemFloor\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", D + "tier_patrol_at", r"PatrolAt\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", D + "tier_pursue_at", r"PursueAt\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", D + "tier_collect_at", r"CollectAt\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", D + "light_wing_gain", r"LightWingGain\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", D + "lever_kill_lights", r"KillLightsRelief\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", D + "lever_go_quiet", r"GoQuietRelief\s*=\s*([\d.]+)f")

CS_RETRIEVAL = r"RetrievalChance\(CuratorTier t\).*?\};"
assert_("cs/Disturbance", "retrieval.patrol", r"CuratorTier\.Patrol\s*=>\s*([\d.]+)f",
        CS_RETRIEVAL)
assert_("cs/Disturbance", "retrieval.pursue", r"CuratorTier\.Pursue\s*=>\s*([\d.]+)f",
        CS_RETRIEVAL)
assert_("cs/Disturbance", "retrieval.collect", r"CuratorTier\.Collect\s*=>\s*([\d.]+)f",
        CS_RETRIEVAL)
assert_("cs/Disturbance", "retrieval.dormant", r"_\s*=>\s*([\d.]+)f", CS_RETRIEVAL)

assert_("cs/Disturbance", "van.base_slots", r"BaseSlots\s*=\s*(\d+)")
assert_("cs/Disturbance", "van.max_slots", r"MaxSlots\s*=\s*(\d+)")
assert_("cs/Disturbance", "van.ruin_k", r"RuinK\s*=\s*([\d.]+)f")
assert_("cs/Disturbance", "van.ruin_exp", r"RuinExp\s*=\s*([\d.]+)f")
CS_SLOTS = r"float Slots\(WeightClass c\).*?\};"
for key, enum in (("pocket", "Pocket"), ("armful", "Armful"),
                  ("two_man", "TwoMan"), ("cart", "Cart")):
    assert_("cs/Disturbance", f"van.slot_cost.{key}",
            rf"WeightClass\.{enum}\s*=>\s*([\d.]+)f", CS_SLOTS)

# --- browser prototypes -------------------------------------------------------
JS_L = r"const L\s*=\s*\{.*?\}"          # the loudness table, not the SPEED table
JS_GRADE = r"const GRADE_MULT\s*=\s*\{.*?\}"
JS_ATT = r"const ATT_MULT\s*=\s*\{.*?\}"
JS_FEE = r"const FEE\s*=\s*\{.*?\}"

for js in ("js/proto", "js/proto3d"):
    assert_(js, LC + "impulse_disturbance_per_l", r"IMPULSE\s*=\s*([\d.]+)")
    assert_(js, LC + "sustained_disturbance_per_l", r"SUSTAINED\s*=\s*([\d.]+)")
    assert_(js, D + "decay_per_min_at_crew4", r"DECAY_PER_S\s*=\s*\((\d+)")
    assert_(js, D + "ratchet_end", r"RATCHET_END\s*=\s*([\d.]+)")
    assert_(js, D + "per_cursed_item_floor", r"FLOOR_PER_CURSED\s*=\s*([\d.]+)")
    assert_(js, D + "tier_collect_at", r"d\s*>=\s*(\d+)\s*\?\s*\"COLLECT\"")
    assert_(js, D + "tier_pursue_at", r"d\s*>=\s*(\d+)\s*\?\s*\"PURSUE\"")
    assert_(js, D + "tier_patrol_at", r"d\s*>=\s*(\d+)\s*\?\s*\"PATROL\"")
    assert_(js, "van.base_slots", r"VAN_SLOTS\s*=\s*(\d+)")
    assert_(js, "van.ruin_k", r"RUIN_K\s*=\s*([\d.]+)")
    assert_(js, "van.ruin_exp", r"RUIN_EXP\s*=\s*([\d.]+)")
    assert_(js, "night.appraise_seconds", r"APPRAISE_S\s*=\s*([\d.]+)")
    assert_(js, "loudness.sprint", r"sprint\s*:\s*(\d+)", JS_L)
    assert_(js, "loudness.appraise", r"appraise\s*:\s*(\d+)", JS_L)
    # `drop` is the prototypes' name for break_small: dropping furniture.
    assert_(js, "loudness.break_small", r"drop\s*:\s*(\d+)", JS_L)
    for grade in ("clean", "tainted", "malignant"):
        assert_(js, f"curse.value_multiplier.{grade}", rf"{grade}\s*:\s*([\d.]+)", JS_GRADE)
        assert_(js, f"curse.attention_multiplier.{grade}", rf"{grade}\s*:\s*([\d.]+)", JS_ATT)
        assert_(js, f"curse.ledger_fee.{grade}", rf"{grade}\s*:\s*([\d.]*\d)", JS_FEE)

assert_("js/proto", "loudness.door", r"door\s*:\s*(\d+)", JS_L)
assert_("js/proto", "loudness.walk", r"walk\s*:\s*(\d+)", JS_L)

# --- Python simulations -------------------------------------------------------
PY_L = r"^L = \{.*?\}"
PY_RETRIEVAL = r"RETRIEVAL = \{.*?\}"
PY_TIERS = r"TIERS = \[.*?\]"

assert_("py/integrated", "night.crew", r"^CREW = (\d+)")
assert_("py/integrated", "night.seconds", r"^NIGHT_S = ([\d.]+)")
assert_("py/integrated", "night.haul_window_seconds", r"^HAUL_S = ([\d.]+)")
assert_("py/integrated", "van.base_slots", r"^VAN_SLOTS = (\d+)")
assert_("py/integrated", LC + "impulse_disturbance_per_l", r"^IMPULSE = ([\d.]+)")
assert_("py/integrated", LC + "sustained_disturbance_per_l", r"^SUSTAINED = ([\d.]+)")
assert_("py/integrated", D + "decay_per_min_at_crew4", r"^DECAY_PER_MIN = ([\d.]+)")
assert_("py/integrated", D + "ratchet_end", r"^RATCHET_END = ([\d.]+)")
for key in ("sprint", "appraise", "door", "dolly", "radio", "break_small"):
    assert_("py/integrated", f"loudness.{key}", rf"\"{key}\":\s*(\d+)", PY_L)

assert_("py/disturbance", "night.crew", r"^CREW = (\d+)")
assert_("py/disturbance", "night.seconds", r"^NIGHT_S = ([\d.]+)")
assert_("py/disturbance", LC + "impulse_disturbance_per_l", r"^IMPULSE_PER_L = ([\d.]+)")
assert_("py/disturbance", LC + "sustained_disturbance_per_l", r"^SUSTAINED_PER_L = ([\d.]+)")
assert_("py/disturbance", D + "light_wing_gain", r"^LIGHT_GAIN = ([\d.]+)")
for key in ("walk", "sprint", "appraise", "door", "crowbar", "break_small",
            "break_large", "radio", "dolly"):
    assert_("py/disturbance", f"loudness.{key}", rf"\"{key}\":\s*(\d+)", PY_L)

assert_("py/curse_test", "night.crew", r"CREW, HAUL_S, NIGHT_S, VAN = (\d+)")
assert_("py/curse_test", "night.haul_window_seconds",
        r"CREW, HAUL_S, NIGHT_S, VAN = \d+, ([\d.]+)")
assert_("py/curse_test", "night.seconds",
        r"CREW, HAUL_S, NIGHT_S, VAN = \d+, [\d.]+, ([\d.]+)")
assert_("py/curse_test", "van.base_slots",
        r"CREW, HAUL_S, NIGHT_S, VAN = \d+, [\d.]+, [\d.]+, (\d+)")
assert_("py/curse_test", D + "decay_per_min_at_crew4", r"^DECAY, IMPULSE, SUSTAINED = ([\d.]+)")
assert_("py/curse_test", LC + "impulse_disturbance_per_l",
        r"^DECAY, IMPULSE, SUSTAINED = [\d.]+, ([\d.]+)")
assert_("py/curse_test", LC + "sustained_disturbance_per_l",
        r"^DECAY, IMPULSE, SUSTAINED = [\d.]+, [\d.]+, ([\d.]+)")
assert_("py/curse_test", D + "ratchet_end", r"^RATCHET_END = ([\d.]+)")
assert_("py/curse_test", D + "per_cursed_item_floor", r"^FLOOR_PER_CURSED = ([\d.]+)")
assert_("py/curse_test", "van.ruin_exp", r"^RUIN_EXP = ([\d.]+)")
assert_("py/curse_test", "curse.value_multiplier.clean", r"\"clean\":\s*([\d.]+)",
        r"mult = \{.*?\}")
assert_("py/curse_test", "curse.value_multiplier.tainted", r"\"tainted\":\s*([\d.]+)",
        r"mult = \{.*?\}")
for grade in ("clean", "tainted", "malignant"):
    assert_("py/curse_test", f"curse.ledger_fee.{grade}", rf"\"{grade}\":\s*([\d.]+)",
            r"^FEE = \{.*?\}")
    assert_("py/curse_test", f"curse.attention_multiplier.{grade}",
            rf"\"{grade}\":\s*([\d.]+)", r"^ATTENTION = \{.*?\}")

for f in ("py/integrated", "py/curse_test"):
    for key, name in (("dormant", "DORMANT"), ("patrol", "PATROL"),
                      ("pursue", "PURSUE"), ("collect", "COLLECT")):
        assert_(f, f"retrieval.{key}", rf"\"{name}\":\s*([\d.]+)", PY_RETRIEVAL)

for f in ("py/integrated", "py/curse_test", "py/disturbance"):
    assert_(f, D + "tier_collect_at", r"\((\d+), \"COLLECT\"\)", PY_TIERS)
    assert_(f, D + "tier_pursue_at", r"\((\d+), \"PURSUE\"\)", PY_TIERS)
    assert_(f, D + "tier_patrol_at", r"\((\d+), \"PATROL\"\)", PY_TIERS)

assert_("py/haul_sim", "night.haul_window_seconds", r"^HAUL_WINDOW_S = ([\d.]+)")
assert_("py/haul_sim", "night.appraise_seconds", r"^APPRAISE_S = ([\d.]+)")
assert_("py/haul_sim", "night.crew", r"^CREW = (\d+)")
assert_("py/haul_sim", "van.base_slots", r"^VAN_SLOTS = (\d+)")

assert_("py/chain_sim", "van.base_slots", r"^VAN_BASE = (\d+)")
assert_("py/chain_sim", "night.haul_window_seconds", r"^HAUL_WINDOW_S = ([\d.]+)")
PY_CLASS = r"CLASS_DATA = \{.*?\n\}"
for key, name in (("pocket", "pocket"), ("armful", "armful"),
                  ("two_man", "two_man"), ("cart", "apex")):
    assert_("py/chain_sim", f"van.slot_cost.{key}", rf"\"{name}\":\s*\(([\d.]+),", PY_CLASS)


# ------------------------------------------------------------------ waivers
# (file glob, path glob, reason). A waiver is a claim that the file does not
# embody the constant, or embodies a deliberately different value. Both are
# fine; being silent about it is not.

WAIVERS = [
    ("cs/Loudness", "attention.*", "audio module - no attention model"),
    ("cs/Loudness", "disturbance.*", "gain is computed here, thresholds live in Disturbance.cs"),
    ("cs/Loudness", "curse.*", "audio module"),
    ("cs/Loudness", "van.*", "audio module"),
    ("cs/Loudness", "retrieval.*", "audio module"),
    ("cs/Loudness", "night.*", "audio module"),

    ("cs/Attention", "loudness.*", "attention counts noise EVENTS, not their loudness"),
    ("cs/Attention", "loudness_constants.*", "as above"),
    ("cs/Attention", "disturbance.*", "separate system"),
    ("cs/Attention", "van.*", "separate system"),
    ("cs/Attention", "retrieval.*", "separate system"),
    ("cs/Attention", "night.*", "no clock in the attention model"),
    ("cs/Attention", "attention.recompute_seconds",
     "the caller drives Update(); the selector has no internal tick"),

    ("cs/Disturbance", "loudness.*", "delegates to Loudness.DisturbanceGain"),
    ("cs/Disturbance", "loudness_constants.*", "delegates to Loudness"),
    ("cs/Disturbance", "attention.*", "separate system"),
    ("cs/Disturbance", "curse.*", "grades live in Attention.cs; only the COUNT matters here"),
    ("cs/Disturbance", "night.*", "night length is a constructor argument, not a constant"),

    ("js/*", "loudness.crouch_walk", "prototype has no crouch"),
    ("js/*", "loudness.voice_*", "prototypes are single-player, no voice chat"),
    ("js/*", "loudness.crowbar", "no forced entry in the prototype"),
    ("js/*", "loudness.break_large", "nothing large enough to break yet"),
    ("js/*", "loudness.dolly", "no dolly in the prototype"),
    ("js/*", "loudness.radio", "no radio in the prototype"),
    ("js/*", "loudness_constants.hearing_radius_per_l",
     "Curator hears by room adjacency, not radius - prototype simplification"),
    ("js/*", "loudness_constants.occlusion_*", "no portal-graph audio in the prototype"),
    ("js/*", "loudness_constants.localisation_fuzz_m", "no localisation in the prototype"),
    ("js/*", "attention.*",
     "single player - there is nobody to retarget between, so hysteresis is untestable here"),
    ("js/*", "retrieval.*",
     "contact-based retrieval: the Curator reaching you takes the item outright, no roll"),
    ("js/*", "van.slot_cost.*", "prototype counts items, not weight classes"),
    ("js/*", "van.max_slots", "no shelving upgrades - single night"),
    ("js/*", "disturbance.lever_*", "levers are Phase 4; not in the prototype"),
    ("js/*", "disturbance.light_wing_gain", "no breaker/lighting system in the prototype"),
    ("js/*", "night.crew", "CREW = 1 deliberately: this is the solo prototype (R12)"),
    ("js/*", "night.seconds",
     "short test runs (180s / 210s) on purpose - a 12-minute night is unusable for QA"),
    ("js/*", "night.haul_window_seconds", "no separate haul window; the whole run is the window"),
    ("js/proto3d", "loudness.door", "no door-slam event in the 3D build yet"),
    ("js/proto3d", "loudness.walk", "walking never raises Disturbance, so the table omits it"),

    ("py/integrated", "loudness.crouch_walk", "not modelled - no crouch in the haul loop"),
    ("py/integrated", "loudness.voice_*", "voice is not modelled in the haul loop"),
    ("py/integrated", "loudness.walk", "walking is free (AUDIO-SPEC 1.2 dash = hard zero)"),
    ("py/integrated", "loudness.crowbar", "not modelled"),
    ("py/integrated", "loudness.break_large", "not modelled"),
    ("py/integrated", "loudness_constants.hearing_radius_per_l", "no geometry in this model"),
    ("py/integrated", "loudness_constants.occlusion_*", "no geometry in this model"),
    ("py/integrated", "loudness_constants.localisation_fuzz_m", "no geometry in this model"),
    ("py/integrated", "attention.*", "attention is modelled in curator_attention.py"),
    ("py/integrated", "curse.*", "curse VALUE is modelled in curse_test.py"),
    ("py/integrated", "van.max_slots", "single night; upgrades are chain_sim's job"),
    ("py/integrated", "van.slot_cost.*", "uniform items; weight classes are chain_sim's job"),
    ("py/integrated", "van.ruin_*", "tail risk is modelled in curse_test.py"),
    ("py/integrated", "disturbance.per_cursed_item_floor",
     "floor-per-cursed is swept in curse_test.py, which is where R9 measured it"),
    ("py/integrated", "disturbance.lever_*", "levers not modelled"),
    ("py/integrated", "disturbance.light_wing_gain", "lighting not modelled"),
    ("py/integrated", "night.appraise_seconds",
     "R5 found scan DURATION barely matters; this model prices the scan by its noise"),

    ("py/disturbance", "disturbance.decay_per_min_at_crew4",
     "DECAY_PER_MIN = 1.0 is the pre-R4 value this module exists to disprove; it sweeps 1->22"),
    ("py/disturbance", "disturbance.ratchet_end", "sweeps its own floor shape"),
    ("py/disturbance", "disturbance.per_cursed_item_floor", "cursed cargo not modelled here"),
    ("py/disturbance", "disturbance.lever_*", "levers not modelled"),
    ("py/disturbance", "attention.*", "not an attention model"),
    ("py/disturbance", "curse.*", "not a curse model"),
    ("py/disturbance", "van.*", "no van in this model"),
    ("py/disturbance", "retrieval.*", "no retrieval in this model"),
    ("py/disturbance", "night.haul_window_seconds", "models the whole night, not the haul window"),
    ("py/disturbance", "night.appraise_seconds", "scan noise is an impulse; duration is irrelevant"),
    ("py/disturbance", "loudness.crouch_walk", "not in the archetype noise profiles"),
    ("py/disturbance", "loudness.voice_*", "voice not modelled"),
    ("py/disturbance", "loudness_constants.hearing_radius_per_l",
     "no geometry - noise is a rate, not a position"),
    ("py/disturbance", "loudness_constants.occlusion_*", "no geometry"),
    ("py/disturbance", "loudness_constants.localisation_fuzz_m", "no geometry"),

    ("py/curse_test", "loudness.*", "noise enters as archetype rates, not per-event"),
    ("py/curse_test", "loudness_constants.hearing_radius_per_l", "no geometry"),
    ("py/curse_test", "loudness_constants.occlusion_*", "no geometry"),
    ("py/curse_test", "loudness_constants.localisation_fuzz_m", "no geometry"),
    ("py/curse_test", "attention.*", "attention enters as a grade multiplier only"),
    ("py/curse_test", "curse.value_multiplier.malignant",
     "the swept variable - R10 ran x6 down to x1.5 and none of them produced a decision"),
    ("py/curse_test", "van.ruin_k",
     "RUIN_K = 0.0 is the sweep's off position; R11 passes 0.015 in explicitly"),
    ("py/curse_test", "van.max_slots", "single night"),
    ("py/curse_test", "van.slot_cost.*", "uniform items"),
    ("py/curse_test", "disturbance.lever_*", "levers not modelled"),
    ("py/curse_test", "disturbance.light_wing_gain", "lighting not modelled"),
    ("py/curse_test", "night.appraise_seconds", "scan cost enters as noise, not seconds"),

    ("py/haul_sim", "loudness*", "superseded: this model prices scanning with the R5 "
     "placeholder DISTURBANCE_PER_SCAN, which integrated.py replaced with derived noise"),
    ("py/haul_sim", "disturbance.*", "as above - placeholder disturbance model, kept for history"),
    ("py/haul_sim", "attention.*", "no attention model"),
    ("py/haul_sim", "curse.*", "no curses in the first haul model"),
    ("py/haul_sim", "retrieval.*", "risk enters as RISK_COEF, swept in __main__"),
    ("py/haul_sim", "van.max_slots", "single night"),
    ("py/haul_sim", "van.slot_cost.*", "uniform items"),
    ("py/haul_sim", "van.ruin_*", "tail risk postdates this model"),
    ("py/haul_sim", "night.seconds", "models the haul window only"),

    ("py/chain_sim", "loudness*", "chain_sim is about labour and depth, not noise"),
    ("py/chain_sim", "disturbance.*", "no disturbance model"),
    ("py/chain_sim", "attention.*", "no attention model"),
    ("py/chain_sim", "curse.*", "no curses"),
    ("py/chain_sim", "retrieval.*", "no retrieval"),
    ("py/chain_sim", "van.ruin_*", "no curses"),
    ("py/chain_sim", "van.max_slots",
     "VAN_BY_NIGHT ends at 19 against a ceiling of 20 - headroom is deliberate"),
    ("py/chain_sim", "night.seconds", "models the haul window only"),
    ("py/chain_sim", "night.crew", "crew size is the swept variable"),
    ("py/chain_sim", "night.appraise_seconds", "appraising is not modelled here"),
]


# ------------------------------------------------------------------ engine

def read(file_key):
    return (ROOT / FILES[file_key]).read_text(encoding="utf-8")


def find(text, pattern, scope=None, group=1):
    """Value of `group` in `pattern`, searched inside `scope` if given."""
    if scope is not None:
        m = re.search(scope, text, re.S | re.M)
        if m is None:
            return None, "scope not found"
        text = m.group(0)
    m = re.search(pattern, text, re.M | re.S)
    if m is None:
        return None, "pattern not found"
    try:
        return float(m.group(group)), None
    except (IndexError, ValueError):
        return None, "capture group did not parse as a number"


def waiver_for(file_key, path):
    for f_glob, p_glob, reason in WAIVERS:
        if fnmatch.fnmatch(file_key, f_glob) and fnmatch.fnmatch(path, p_glob):
            return reason
    return None


def main(verbose=True):
    fails, asserted, waived = [], {}, {}
    texts = {k: read(k) for k in FILES}

    for file_key, path, pattern, scope, group in A:
        asserted.setdefault(file_key, set()).add(path)
        if path not in CANON:
            fails.append(f"{file_key}:{path}  asserts a path that is not in tuning.json")
            continue
        got, why = find(texts[file_key], pattern, scope, group)
        if got is None:
            fails.append(f"{file_key}:{path}  NOT FOUND in source ({why})")
        elif abs(got - CANON[path]) > 1e-9:
            fails.append(f"{file_key}:{path}  found {got:g}, canonical is {CANON[path]:g}")

    # Coverage: every (file, constant) pair is asserted or waived, never neither.
    for file_key in FILES:
        for path in CANON:
            if path in asserted.get(file_key, ()):
                continue
            reason = waiver_for(file_key, path)
            if reason is None:
                fails.append(f"{file_key}:{path}  COVERAGE HOLE - not asserted, not waived")
            else:
                waived.setdefault(file_key, {})[path] = reason

    if verbose:
        print(f"DRIFT CHECK  -  {len(A)} assertions over {len(CANON)} canonical "
              f"constants x {len(FILES)} files")
        print("-" * 78)
        for file_key in FILES:
            n_a, n_w = len(asserted.get(file_key, ())), len(waived.get(file_key, {}))
            print(f"  {file_key:<16} {n_a:>3} asserted   {n_w:>3} waived   "
                  f"{len(CANON) - n_a - n_w:>3} unaccounted")
        print("-" * 78)
        if not fails:
            print("  OK   every implementation agrees with tuning.json, "
                  "and every gap is declared")
        for f in fails:
            print(f"  FAIL  {f}")
        if fails:
            print(f"\n{len(fails)} problem(s). tuning.json is canonical - "
                  f"fix the implementation, not the checker.")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
