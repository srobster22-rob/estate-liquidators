"""
Drift check across the four implementations.

The same rules live in sim/*.py, proto/index.html, proto3d/index.html and
unity/Assets/Scripts/Core/*.cs. tuning.json is canonical; this asserts the other
four agree with it. Without this, a value gets corrected in one place and the
project starts trusting numbers that no longer describe the game.

Reads the C# and JS as TEXT rather than executing them, so it needs no toolchain and
catches the exact failure that matters: a literal edited in one file and not the others.

    python sim/check_drift.py        ->  exit 0 if everything agrees

Requires nothing outside the standard library.

--------------------------------------------------------------------------------
COVERAGE IS PART OF THE CHECK (added LOOP_LOG R16)

The first version of this file had the failure mode it existed to prevent. Two
things were wrong and both were silent:

  1. The C# loudness loop ended in `if got is not None: check(...)`. A pattern that
     matched nothing was skipped rather than failed, so `appraise` and `door` were
     never checked against the C# core at all - the enum spells them AppraisePing
     and DoorSlam, the generated regex looked for Appraise and Door, and the miss
     was swallowed. The headline count read 55 while the real C# loudness coverage
     was 12 of 14.

  2. Nothing asserted that every canonical constant is checked *somewhere*. 23 of
     the 59 values in tuning.json - the whole slot-cost table, the whole retrieval
     table, every ledger fee, all three Disturbance levers - had no guard at all,
     while being duplicated across two or three implementations.

So this file now checks itself:

  * `grab` never returns quietly. A pattern that fails to match is a FAILURE, not a
    skip. If a constant is renamed in source, that is drift and it is reported.
  * every numeric leaf in tuning.json must be checked at least once, or be named in
    UNGUARDED with a reason. A new constant that nobody wired up fails the run.
  * a stale UNGUARDED entry - one that is actually covered - also fails, so the
    exemption list cannot rot into a lie.
  * EXPECTED_CHECKS pins the headline number, so "55/55" is asserted by the program
    rather than eyeballed by whoever runs it.

--------------------------------------------------------------------------------
COVERAGE IS PER-IMPLEMENTATION (added LOOP_LOG R17)

R16's key-level audit was the wrong invariant, and the gap bit within one round.
`disturbance.per_cursed_item_floor` was checked in C# and in Python, which satisfied
"checked somewhere" and kept the run green - while BOTH browser prototypes were still
multiplying by the retracted value 2 instead of the canonical 7. proto3d/index.html
was a fourth implementation this file had never opened, while itself carrying the
comment "sim/check_drift.py asserts these stay in agreement". It did not.

So coverage is now asserted per implementation, via IMPL_KEYS: if an implementation
carries a constant, that implementation must be checked against it. DIVERGENT records
the handful of places a prototype departs from canon on purpose, with the reason.

Known limitation, stated rather than papered over: IMPL_KEYS is a hand-maintained
manifest. It fails closed when a check is deleted or a constant is renamed, which is
the regression that actually happens. It cannot detect a brand-new constant added to
an implementation and to nothing else - only reading the implementation would.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TUNING = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

# Pinned so the headline count is machine-checked. Raise it deliberately when you
# add a check; a drop means checks silently stopped running.
EXPECTED_CHECKS = 133

# Canonical constants with no implementation to check against, and why. Anything
# here that turns out to BE covered is reported as a stale exemption.
UNGUARDED = {}

# --------------------------------------------------------------------------
# PER-IMPLEMENTATION COVERAGE (added R17)
#
# R16 made this file fail-closed on *keys*: every constant in tuning.json had to be
# checked somewhere. That was not the real invariant, and the gap bit within one
# round. `disturbance.per_cursed_item_floor` was checked in C# and in Python, so the
# key-level audit was satisfied and the run was green - while BOTH browser prototypes
# were still multiplying by the retracted value 2 instead of the canonical 7. One of
# them, proto3d/index.html, this file had never even opened, despite the prototype
# carrying a comment claiming "sim/check_drift.py asserts these stay in agreement".
#
# The invariant is per-implementation: if an implementation carries a constant, that
# implementation must be checked against it. IMPL_KEYS states, for each of the four
# implementations, which canonical constants it is expected to carry. A key listed
# here but not actually checked against that implementation fails the run.
IMPL_KEYS = {
    "C#": {
        *(f"loudness.{n}" for n in ("crouch_walk", "voice_whisper", "walk",
                                    "voice_normal", "dolly", "radio", "sprint",
                                    "voice_raised", "appraise", "door", "voice_shout",
                                    "crowbar", "break_small", "break_large")),
        "loudness_constants.hearing_radius_per_l",
        "loudness_constants.impulse_disturbance_per_l",
        "loudness_constants.sustained_disturbance_per_l",
        "loudness_constants.occlusion_player", "loudness_constants.occlusion_curator",
        "loudness_constants.localisation_fuzz_m",
        "disturbance.decay_per_min_at_crew4", "disturbance.ratchet_end",
        "disturbance.per_cursed_item_floor", "disturbance.light_wing_gain",
        "disturbance.lever_kill_lights", "disturbance.lever_go_quiet",
        "disturbance.tier_patrol_at", "disturbance.tier_pursue_at",
        "disturbance.tier_collect_at",
        "attention.steal_threshold", "attention.commit_seconds",
        "attention.noise_multiplier_per_event", "attention.light_multiplier",
        "van.base_slots", "van.max_slots", "van.ruin_k", "van.ruin_exp",
        *(f"van.slot_cost.{n}" for n in ("pocket", "armful", "two_man", "cart")),
        *(f"retrieval.{n}" for n in ("dormant", "patrol", "pursue", "collect")),
        *(f"curse.{t}.{g}" for t in ("value_multiplier", "attention_multiplier",
                                     "ledger_fee")
          for g in ("clean", "tainted", "malignant")),
    },
    "JS": {   # proto/index.html
        "loudness.sprint", "loudness.appraise", "loudness.door", "loudness.break_small",
        "loudness_constants.impulse_disturbance_per_l",
        "loudness_constants.sustained_disturbance_per_l",
        "disturbance.ratchet_end", "disturbance.decay_per_min_at_crew4",
        "disturbance.per_cursed_item_floor",
        "van.base_slots", "van.ruin_k", "van.ruin_exp",
        "night.appraise_seconds",
        *(f"curse.{t}.{g}" for t in ("value_multiplier", "attention_multiplier")
          for g in ("clean", "tainted", "malignant")),
    },
    "JS3D": {  # proto3d/index.html
        "loudness.sprint", "loudness.appraise", "loudness.break_small",
        "loudness_constants.impulse_disturbance_per_l",
        "loudness_constants.sustained_disturbance_per_l",
        "disturbance.ratchet_end", "disturbance.decay_per_min_at_crew4",
        "disturbance.per_cursed_item_floor",
        "van.base_slots", "van.ruin_k", "van.ruin_exp",
        "night.appraise_seconds",
        *(f"curse.{t}.{g}" for t in ("value_multiplier", "attention_multiplier",
                                     "ledger_fee")
          for g in ("clean", "tainted", "malignant")),
    },
    "py": {
        "loudness.sprint", "loudness.appraise", "loudness.door",
        "loudness_constants.impulse_disturbance_per_l",
        "loudness_constants.sustained_disturbance_per_l",
        "disturbance.decay_per_min_at_crew4", "disturbance.ratchet_end",
        "disturbance.per_cursed_item_floor", "disturbance.tier_patrol_at",
        "disturbance.tier_pursue_at", "disturbance.tier_collect_at",
        "attention.recompute_seconds",
        "van.base_slots", "van.ruin_exp",
        "van.slot_cost.pocket", "van.slot_cost.armful", "van.slot_cost.two_man",
        "van.slot_cost.cart",
        *(f"retrieval.{n}" for n in ("dormant", "patrol", "pursue", "collect")),
        "night.crew", "night.seconds", "night.haul_window_seconds",
    },
}

# Places an implementation deliberately departs from canon, and why. These are NOT
# drift; recording them stops someone "fixing" a prototype into being wrong, and stops
# the coverage audit pretending the constant is guarded there.
DIVERGENT = {
    ("JS", "loudness.walk"):
        "proto sets L.walk=0, conflating loudness with Disturbance cost. Walking is free "
        "of Disturbance but is canonically L=20 to the Curator's ear. A loop-test "
        "simplification: proto has no Curator hearing model.",
    ("JS", "night.seconds"):
        "proto NIGHT=180 and proto3d NIGHT=210 are deliberately short loop tests; the "
        "ship value is 720. Stated in proto/index.html:50.",
    ("JS3D", "night.seconds"):
        "as above - proto3d NIGHT=210, a single-player loop test, not the 720s night.",
    ("JS", "night.crew"):
        "both prototypes are single-player (CREW=1); crew 4 is the ship value. The decay "
        "expression still reads 50/min at crew 4 and IS checked.",
    ("JS3D", "night.crew"):
        "as above - proto3d is single-player.",
}

fails, checks = [], 0
covered = set()
covered_by = {}


def _impl_of(label):
    """Which implementation a check belongs to, from its label prefix."""
    if label.startswith("C# "):
        return "C#"
    if label.startswith("JS3D "):
        return "JS3D"
    if label.startswith("JS "):
        return "JS"
    if label.startswith("py "):
        return "py"
    return "?"


def check(key, label, got, want, tol=1e-9):
    """`key` is the dotted path into tuning.json this check covers."""
    global checks
    checks += 1
    covered.add(key)
    covered_by.setdefault(_impl_of(label), set()).add(key)
    if got is None:
        fails.append(f"{label}: NOT FOUND in source (pattern matched nothing)")
        return
    if abs(float(got) - float(want)) > tol:
        fails.append(f"{label}: found {got}, canonical is {want}")


def grab(text, pattern, cast=float, flags=0, group=1):
    """Capture group of `pattern`, or None if it does not match."""
    m = re.search(pattern, text, flags)
    return cast(m.group(group)) if m else None


def switch(text, decl):
    """
    Body of an expression-bodied C# switch, e.g. decl='Value(CurseGrade g)'.
    Scoping to the declaring method matters: several of these tables share arm
    names, and an unanchored match reads a value out of the wrong one.
    """
    m = re.search(re.escape(decl) + r"\s*=>\s*\w+\s+switch\s*\{(.*?)\}\s*;",
                  text, re.S)
    return m.group(1) if m else ""


def arm(body, case):
    """Value of one switch arm. `case` may be `_` for the default arm."""
    return grab(body, rf"{re.escape(case)}\s*=>\s*([\d.]+)f?")


def leaves(node, prefix=""):
    """Every numeric leaf in tuning.json as a dotted path. `_`-keys are notes."""
    for k, v in node.items():
        if k.startswith("_"):
            continue
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from leaves(v, path)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            yield path


# --------------------------------------------------------------- C# core
cs = "\n".join((ROOT / "unity/Assets/Scripts/Core" / n).read_text(encoding="utf-8")
               for n in ("Loudness.cs", "Attention.cs", "Disturbance.cs"))

lc = TUNING["loudness_constants"]
check("loudness_constants.hearing_radius_per_l", "C# hearing_radius_per_l",
      grab(cs, r"HearingRadiusPerL\s*=\s*([\d.]+)f"), lc["hearing_radius_per_l"])
check("loudness_constants.impulse_disturbance_per_l", "C# impulse_per_l",
      grab(cs, r"ImpulseDisturbancePerL\s*=\s*([\d.]+)f"),
      lc["impulse_disturbance_per_l"])
check("loudness_constants.sustained_disturbance_per_l", "C# sustained_per_l",
      grab(cs, r"SustainedDisturbancePerL\s*=\s*([\d.]+)f"),
      lc["sustained_disturbance_per_l"])
check("loudness_constants.occlusion_player", "C# occlusion_player",
      grab(cs, r"OcclusionPlayer\s*=\s*([\d.]+)f"), lc["occlusion_player"])
check("loudness_constants.occlusion_curator", "C# occlusion_curator",
      grab(cs, r"OcclusionCurator\s*=\s*([\d.]+)f"), lc["occlusion_curator"])
check("loudness_constants.localisation_fuzz_m", "C# localisation_fuzz_m",
      grab(cs, r"LocalisationFuzzM\s*=\s*([\d.]+)f"), lc["localisation_fuzz_m"])

d = TUNING["disturbance"]
check("disturbance.decay_per_min_at_crew4", "C# decay_per_min",
      grab(cs, r"DecayPerMinAtCrew4\s*=\s*([\d.]+)f"), d["decay_per_min_at_crew4"])
check("disturbance.ratchet_end", "C# ratchet_end",
      grab(cs, r"RatchetEnd\s*=\s*([\d.]+)f"), d["ratchet_end"])
check("disturbance.per_cursed_item_floor", "C# cursed_floor",
      grab(cs, r"PerCursedItemFloor\s*=\s*([\d.]+)f"), d["per_cursed_item_floor"])
check("disturbance.tier_patrol_at", "C# tier_patrol",
      grab(cs, r"PatrolAt\s*=\s*([\d.]+)f"), d["tier_patrol_at"])
check("disturbance.tier_pursue_at", "C# tier_pursue",
      grab(cs, r"PursueAt\s*=\s*([\d.]+)f"), d["tier_pursue_at"])
check("disturbance.tier_collect_at", "C# tier_collect",
      grab(cs, r"CollectAt\s*=\s*([\d.]+)f"), d["tier_collect_at"])

# The three levers are inline literals inside one-line methods rather than named
# constants, which is exactly why they were never guarded. Match them where they are.
check("disturbance.lever_kill_lights", "C# lever_kill_lights",
      grab(cs, r"KillLights\(\)\s*=>\s*Value\s*=\s*MathF\.Max\(\s*0f\s*,\s*Value\s*-\s*([\d.]+)f"),
      d["lever_kill_lights"])
check("disturbance.lever_go_quiet", "C# lever_go_quiet",
      grab(cs, r"GoQuiet\(\)\s*=>\s*Value\s*=\s*MathF\.Max\(\s*0f\s*,\s*Value\s*-\s*([\d.]+)f"),
      d["lever_go_quiet"])
check("disturbance.light_wing_gain", "C# light_wing_gain",
      grab(cs, r"LightWing\(\)\s*=>\s*Value\s*=\s*MathF\.Min\(\s*100f\s*,\s*Value\s*\+\s*([\d.]+)f"),
      d["light_wing_gain"])

a = TUNING["attention"]
check("attention.steal_threshold", "C# steal_threshold",
      grab(cs, r"StealThreshold\s*=\s*([\d.]+)f"), a["steal_threshold"])
check("attention.commit_seconds", "C# commit_seconds",
      grab(cs, r"CommitSeconds\s*=\s*([\d.]+)f"), a["commit_seconds"])
check("attention.noise_multiplier_per_event", "C# noise_multiplier",
      grab(cs, r"NoisePerEvent\s*=\s*([\d.]+)f"), a["noise_multiplier_per_event"])
check("attention.light_multiplier", "C# light_multiplier",
      grab(cs, r"LightMultiplier\s*=\s*([\d.]+)f"), a["light_multiplier"])

v = TUNING["van"]
check("van.base_slots", "C# van_base_slots", grab(cs, r"BaseSlots\s*=\s*(\d+)"),
      v["base_slots"])
check("van.max_slots", "C# van_max_slots", grab(cs, r"MaxSlots\s*=\s*(\d+)"),
      v["max_slots"])
check("van.ruin_k", "C# ruin_k", grab(cs, r"RuinK\s*=\s*([\d.]+)f"), v["ruin_k"])
check("van.ruin_exp", "C# ruin_exp", grab(cs, r"RuinExp\s*=\s*([\d.]+)f"), v["ruin_exp"])

# Slot costs: the master capacity table, duplicated in chain_sim and never guarded.
slots_body = switch(cs, "Slots(WeightClass c)")
for name, case in (("pocket", "WeightClass.Pocket"), ("armful", "WeightClass.Armful"),
                   ("two_man", "WeightClass.TwoMan"), ("cart", "WeightClass.Cart")):
    check(f"van.slot_cost.{name}", f"C# slot_cost[{name}]", arm(slots_body, case),
          v["slot_cost"][name])

# Retrieval odds per tier: duplicated in integrated.py and curse_test.py.
retr_body = switch(cs, "RetrievalChance(CuratorTier t)")
r = TUNING["retrieval"]
check("retrieval.dormant", "C# retrieval[dormant]", arm(retr_body, "_"), r["dormant"])
for name in ("patrol", "pursue", "collect"):
    check(f"retrieval.{name}", f"C# retrieval[{name}]",
          arm(retr_body, f"CuratorTier.{name.capitalize()}"), r[name])

# The three curse tables. `clean` is the default arm in each.
for tbl, decl in (("value_multiplier", "Value(CurseGrade g)"),
                  ("attention_multiplier", "Attention(CurseGrade g)"),
                  ("ledger_fee", "Fee(CurseGrade g)")):
    body = switch(cs, decl)
    check(f"curse.{tbl}.clean", f"C# curse.{tbl}[clean]", arm(body, "_"),
          TUNING["curse"][tbl]["clean"])
    for g in ("tainted", "malignant"):
        check(f"curse.{tbl}.{g}", f"C# curse.{tbl}[{g}]",
              arm(body, f"CurseGrade.{g.capitalize()}"), TUNING["curse"][tbl][g])

# The C# enum does not spell every noise kind the way tuning.json does. Map the
# exceptions explicitly rather than generating a name and skipping the misses -
# the silent skip here is the bug this rewrite exists to remove.
CS_NOISE_NAME = {"appraise": "AppraisePing", "door": "DoorSlam"}
for name, want in TUNING["loudness"].items():
    if name.startswith("_"):
        continue
    key = CS_NOISE_NAME.get(name) or "".join(p.capitalize() for p in name.split("_"))
    check(f"loudness.{name}", f"C# L[{name}]",
          grab(cs, rf"NoiseKind\.{key}\s*=>\s*(\d+)"), want)

# --------------------------------------------------------------- JS prototype
js = (ROOT / "proto/index.html").read_text(encoding="utf-8")
check("loudness_constants.impulse_disturbance_per_l", "JS impulse_per_l",
      grab(js, r"IMPULSE\s*=\s*([\d.]+)"), lc["impulse_disturbance_per_l"])
check("loudness_constants.sustained_disturbance_per_l", "JS sustained_per_l",
      grab(js, r"SUSTAINED\s*=\s*([\d.]+)"), lc["sustained_disturbance_per_l"])
check("disturbance.ratchet_end", "JS ratchet_end",
      grab(js, r"RATCHET_END\s*=\s*([\d.]+)"), d["ratchet_end"])
check("disturbance.decay_per_min_at_crew4", "JS decay_per_min",
      grab(js, r"DECAY_PER_S\s*=\s*\(([\d.]+)"), d["decay_per_min_at_crew4"])
check("night.appraise_seconds", "JS appraise_seconds",
      grab(js, r"APPRAISE_S\s*=\s*([\d.]+)"), TUNING["night"]["appraise_seconds"])
check("van.base_slots", "JS van_slots", grab(js, r"VAN_SLOTS\s*=\s*(\d+)"),
      v["base_slots"])
check("van.ruin_k", "JS ruin_k", grab(js, r"([\d.]+)\s*\*\s*Math\.pow\(cursed"),
      v["ruin_k"])
check("van.ruin_exp", "JS ruin_exp", grab(js, r"Math\.pow\(cursed,\s*([\d.]+)\)"),
      v["ruin_exp"])

# The cursed-item floor. BOTH prototypes shipped the retracted value 2 here until R17,
# behind a key-level coverage audit that was satisfied by the C# and Python copies.
check("disturbance.per_cursed_item_floor", "JS cursed_floor",
      grab(js, r"CURSED_FLOOR\s*=\s*([\d.]+)"), d["per_cursed_item_floor"])

cm = TUNING["curse"]["value_multiplier"]
am = TUNING["curse"]["attention_multiplier"]
js_grade = grab(js, r"GRADE_MULT\s*=\s*\{([^}]*)\}", cast=str) or ""
js_att = grab(js, r"ATT_MULT\s*=\s*\{([^}]*)\}", cast=str) or ""
for g in ("clean", "tainted", "malignant"):
    check(f"curse.value_multiplier.{g}", f"JS curse_value[{g}]",
          grab(js_grade, rf"\b{g}\s*:\s*([\d.]+)"), cm[g])
    check(f"curse.attention_multiplier.{g}", f"JS curse_attention[{g}]",
          grab(js_att, rf"\b{g}\s*:\s*([\d.]+)"), am[g])

# Scope to the loudness table specifically: `sprint` also appears in the movement
# SPEED table, and an unanchored match happily reports 205 px/s as a loudness.
# `drop` is the prototypes' name for a break_small event.
JS_NOISE_NAME = {"break_small": "drop"}
js_l = re.search(r"const L\s*=\s*\{(.*?)\}", js, re.S)
js_l = js_l.group(1) if js_l else ""
for name in ("sprint", "appraise", "door", "break_small"):
    check(f"loudness.{name}", f"JS L[{name}]",
          grab(js_l, rf"\b{JS_NOISE_NAME.get(name, name)}\s*:\s*(\d+)"),
          TUNING["loudness"][name])

# --------------------------------------------------------- JS 3D prototype
# The fourth implementation. Never read by this file until R17, while carrying a
# comment asserting that it was.
js3 = (ROOT / "proto3d/index.html").read_text(encoding="utf-8")
check("loudness_constants.impulse_disturbance_per_l", "JS3D impulse_per_l",
      grab(js3, r"IMPULSE\s*=\s*([\d.]+)"), lc["impulse_disturbance_per_l"])
check("loudness_constants.sustained_disturbance_per_l", "JS3D sustained_per_l",
      grab(js3, r"SUSTAINED\s*=\s*([\d.]+)"), lc["sustained_disturbance_per_l"])
check("disturbance.ratchet_end", "JS3D ratchet_end",
      grab(js3, r"RATCHET_END\s*=\s*([\d.]+)"), d["ratchet_end"])
check("disturbance.decay_per_min_at_crew4", "JS3D decay_per_min",
      grab(js3, r"DECAY_PER_S\s*=\s*\(([\d.]+)"), d["decay_per_min_at_crew4"])
check("disturbance.per_cursed_item_floor", "JS3D cursed_floor",
      grab(js3, r"CURSED_FLOOR\s*=\s*([\d.]+)"), d["per_cursed_item_floor"])
check("van.base_slots", "JS3D van_slots", grab(js3, r"VAN_SLOTS\s*=\s*(\d+)"),
      v["base_slots"])
check("van.ruin_k", "JS3D ruin_k", grab(js3, r"RUIN_K\s*=\s*([\d.]+)"), v["ruin_k"])
check("van.ruin_exp", "JS3D ruin_exp", grab(js3, r"RUIN_EXP\s*=\s*([\d.]+)"),
      v["ruin_exp"])
check("night.appraise_seconds", "JS3D appraise_seconds",
      grab(js3, r"APPRAISE_S\s*=\s*([\d.]+)"), TUNING["night"]["appraise_seconds"])

fee = TUNING["curse"]["ledger_fee"]
js3_grade = grab(js3, r"GRADE_MULT\s*=\s*\{([^}]*)\}", cast=str) or ""
js3_att = grab(js3, r"ATT_MULT\s*=\s*\{([^}]*)\}", cast=str) or ""
js3_fee = grab(js3, r"FEE\s*=\s*\{([^}]*)\}", cast=str) or ""
for g in ("clean", "tainted", "malignant"):
    check(f"curse.value_multiplier.{g}", f"JS3D curse_value[{g}]",
          grab(js3_grade, rf"\b{g}\s*:\s*([\d.]+)"), cm[g])
    check(f"curse.attention_multiplier.{g}", f"JS3D curse_attention[{g}]",
          grab(js3_att, rf"\b{g}\s*:\s*([\d.]+)"), am[g])
    # FEE writes bare-dot floats (.08), which float() parses but \d+ would miss.
    check(f"curse.ledger_fee.{g}", f"JS3D curse_fee[{g}]",
          grab(js3_fee, rf"\b{g}\s*:\s*([\d.]*\d)"), fee[g])

js3_l = re.search(r"const L\s*=\s*\{(.*?)\}", js3, re.S)
js3_l = js3_l.group(1) if js3_l else ""
for name in ("sprint", "appraise", "break_small"):
    check(f"loudness.{name}", f"JS3D L[{name}]",
          grab(js3_l, rf"\b{JS_NOISE_NAME.get(name, name)}\s*:\s*(\d+)"),
          TUNING["loudness"][name])

# --------------------------------------------------------------- Python sims
sims = {n: (ROOT / "sim" / n).read_text(encoding="utf-8")
        for n in ("integrated.py", "disturbance.py", "curse_test.py",
                  "chain_sim.py", "curator_attention.py")}

check("loudness_constants.impulse_disturbance_per_l", "py integrated IMPULSE",
      grab(sims["integrated.py"], r"^IMPULSE\s*=\s*([\d.]+)", flags=re.M),
      lc["impulse_disturbance_per_l"])
check("loudness_constants.sustained_disturbance_per_l", "py integrated SUSTAINED",
      grab(sims["integrated.py"], r"^SUSTAINED\s*=\s*([\d.]+)", flags=re.M),
      lc["sustained_disturbance_per_l"])
check("disturbance.decay_per_min_at_crew4", "py integrated DECAY",
      grab(sims["integrated.py"], r"DECAY_PER_MIN\s*=\s*([\d.]+)"),
      d["decay_per_min_at_crew4"])
check("disturbance.ratchet_end", "py integrated RATCHET",
      grab(sims["integrated.py"], r"RATCHET_END\s*=\s*([\d.]+)"), d["ratchet_end"])
check("van.base_slots", "py integrated VAN_SLOTS",
      grab(sims["integrated.py"], r"VAN_SLOTS\s*=\s*(\d+)"), v["base_slots"])
check("loudness_constants.impulse_disturbance_per_l", "py disturbance IMPULSE",
      grab(sims["disturbance.py"], r"IMPULSE_PER_L\s*=\s*([\d.]+)"),
      lc["impulse_disturbance_per_l"])
# The cursed floor is declared in BOTH sims. integrated.py carried an inline `cursed *
# 2.0` - the value R9 retired - from before R9 until R20, unseen because the family-level
# manifest was satisfied by curse_test.py's copy. It is the model that produced the
# appraiser's headline edge, so the number was wrong too. Check every file that has one.
for f, label in (("curse_test.py", "py curse"), ("integrated.py", "py integrated")):
    check("disturbance.per_cursed_item_floor", f"{label} floor",
          grab(sims[f], r"FLOOR_PER_CURSED\s*=\s*([\d.]+)"),
          d["per_cursed_item_floor"])
check("van.ruin_exp", "py curse ruin_exp",
      grab(sims["curse_test.py"], r"RUIN_EXP\s*=\s*([\d.]+)"), v["ruin_exp"])

for name in ("sprint", "appraise", "door"):
    check(f"loudness.{name}", f"py L[{name}]",
          grab(sims["disturbance.py"], rf"[\"']{name}[\"']\s*:\s*(\d+)"),
          TUNING["loudness"][name])

# Attention recompute cadence lives only in the sim, as TICK.
check("attention.recompute_seconds", "py curator_attention TICK",
      grab(sims["curator_attention.py"], r"^TICK\s*=\s*([\d.]+)", flags=re.M),
      a["recompute_seconds"])

# Retrieval tables in the two sims that carry their own copy.
for f, label in (("integrated.py", "py integrated"), ("curse_test.py", "py curse")):
    body = grab(sims[f], r"RETRIEVAL\s*=\s*\{([^}]*)\}", cast=str)
    for name in ("dormant", "patrol", "pursue", "collect"):
        check(f"retrieval.{name}", f"{label} RETRIEVAL[{name}]",
              grab(body or "", rf"[\"']{name.upper()}[\"']\s*:\s*([\d.]+)"), r[name])

# Tier thresholds are re-declared as a TIERS ladder in three sims.
n = TUNING["night"]
for f, label in (("integrated.py", "py integrated"), ("disturbance.py", "py disturbance"),
                 ("curse_test.py", "py curse")):
    body = grab(sims[f], r"TIERS\s*=\s*\[([^\]]*)\]", cast=str) or ""
    for tier, key in (("COLLECT", "tier_collect_at"), ("PURSUE", "tier_pursue_at"),
                      ("PATROL", "tier_patrol_at")):
        check(f"disturbance.{key}", f"{label} TIERS[{tier}]",
              grab(body, rf"\(([\d.]+),\s*[\"']{tier}[\"']\)"), d[key])

# Night shape: crew size and the two clocks.
check("night.crew", "py curse CREW",
      grab(sims["curse_test.py"], r"CREW,\s*HAUL_S,\s*NIGHT_S,\s*VAN\s*=\s*(\d+)"),
      n["crew"])
check("night.haul_window_seconds", "py curse HAUL_S",
      grab(sims["curse_test.py"],
           r"CREW,\s*HAUL_S,\s*NIGHT_S,\s*VAN\s*=\s*\d+,\s*([\d.]+)"),
      n["haul_window_seconds"])
check("night.seconds", "py curse NIGHT_S",
      grab(sims["curse_test.py"],
           r"CREW,\s*HAUL_S,\s*NIGHT_S,\s*VAN\s*=\s*\d+,\s*[\d.]+,\s*([\d.]+)"),
      n["seconds"])
check("van.base_slots", "py curse VAN",
      grab(sims["curse_test.py"],
           r"CREW,\s*HAUL_S,\s*NIGHT_S,\s*VAN\s*=\s*\d+,\s*[\d.]+,\s*[\d.]+,\s*(\d+)"),
      v["base_slots"])
check("night.haul_window_seconds", "py chain HAUL_WINDOW_S",
      grab(sims["chain_sim.py"], r"^HAUL_WINDOW_S\s*=\s*([\d.]+)", flags=re.M),
      n["haul_window_seconds"])
# Scope to CLASS_DATA: TIER_DATA above it is keyed by the same class names and an
# unanchored match reports a value band ($80) as a slot cost. chain_sim also calls
# the cart class `apex`, so map the name rather than generating it.
chain_classes = grab(sims["chain_sim.py"], r"CLASS_DATA\s*=\s*\{(.*?)\n\}", cast=str,
                     flags=re.S) or ""
for name, sim_name in (("pocket", "pocket"), ("armful", "armful"),
                       ("two_man", "two_man"), ("cart", "apex")):
    check(f"van.slot_cost.{name}", f"py chain slot_cost[{name}]",
          grab(chain_classes, rf"[\"']{sim_name}[\"']:\s*\(([\d.]+)"),
          v["slot_cost"][name])

# --------------------------------------------------------------- coverage audit
canonical = set(leaves(TUNING))
missing = sorted(canonical - covered - set(UNGUARDED))
stale = sorted(set(UNGUARDED) & covered)
unknown = sorted(set(UNGUARDED) - canonical)

for k in missing:
    fails.append(f"COVERAGE {k}: canonical but checked nowhere. "
                 f"Add a check or list it in UNGUARDED with a reason.")
for k in stale:
    fails.append(f"COVERAGE {k}: listed in UNGUARDED but is checked. "
                 f"Remove the exemption.")
for k in unknown:
    fails.append(f"COVERAGE {k}: in UNGUARDED but not in tuning.json.")

# Per-implementation coverage. This is the audit that would have caught the R17 bug:
# a constant an implementation carries but nobody checks against that implementation.
for impl, keys in sorted(IMPL_KEYS.items()):
    got = covered_by.get(impl, set())
    for k in sorted(keys):
        if (impl, k) in DIVERGENT:
            fails.append(f"COVERAGE {impl}/{k}: listed in both IMPL_KEYS and "
                         f"DIVERGENT. Pick one.")
        elif k not in got:
            fails.append(f"COVERAGE {impl}/{k}: {impl} is expected to carry this "
                         f"constant but nothing checks it there.")
    for k in sorted(got - keys):
        if k in canonical:
            fails.append(f"COVERAGE {impl}/{k}: checked against {impl} but missing "
                         f"from IMPL_KEYS. Add it, so a deleted check fails the run.")
for (impl, k) in sorted(DIVERGENT):
    if k not in canonical:
        fails.append(f"COVERAGE {impl}/{k}: in DIVERGENT but not in tuning.json.")
    if k in covered_by.get(impl, set()):
        fails.append(f"COVERAGE {impl}/{k}: marked DIVERGENT but IS checked against "
                     f"{impl}. Remove the exemption.")
if checks != EXPECTED_CHECKS:
    fails.append(f"COUNT: ran {checks} checks, expected {EXPECTED_CHECKS}. "
                 f"If you added or removed one, update EXPECTED_CHECKS deliberately.")

# --------------------------------------------------------------- report
guarded = len(canonical & covered)
print(f"DRIFT CHECK  -  {checks} checks over {guarded}/{len(canonical)} "
      f"canonical constants, across {len(IMPL_KEYS)} implementations")
print("-" * 74)
if not fails:
    print("  OK   every implementation agrees with tuning.json")
    if UNGUARDED:
        print(f"  OK   {guarded} constants guarded, {len(UNGUARDED)} exempted:")
        for k, why in sorted(UNGUARDED.items()):
            print(f"         {k} - {why}")
    else:
        print("  OK   every canonical constant is guarded somewhere, none exempted")
    sys.exit(0)
for f in fails:
    print(f"  DRIFT  {f}")
print(f"\n{len(fails)} divergence(s). tuning.json is canonical - fix the implementation.")
sys.exit(1)
