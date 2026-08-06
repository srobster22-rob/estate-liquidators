"""
Drift check across the three implementations.

The same rules live in sim/*.py, proto/index.html and unity/Assets/Scripts/Core/*.cs.
tuning.json is canonical; this asserts the other three agree with it. Without this,
a value gets corrected in one place and the project starts trusting numbers that no
longer describe the game.

Reads the C# and JS as TEXT rather than executing them, so it needs no toolchain and
catches the exact failure that matters: a literal edited in one file and not the others.

    python sim/check_drift.py        ->  exit 0 if everything agrees

Requires nothing outside the standard library.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TUNING = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

fails, checks = [], 0


def check(label, got, want, tol=1e-9):
    global checks
    checks += 1
    if got is None:
        fails.append(f"{label}: NOT FOUND in source")
        return
    if abs(float(got) - float(want)) > tol:
        fails.append(f"{label}: found {got}, canonical is {want}")


def grab(text, pattern, cast=float, flags=0):
    """First capture group of `pattern`, or None."""
    m = re.search(pattern, text, flags)
    return cast(m.group(1)) if m else None


# --------------------------------------------------------------- C# core
cs = "\n".join((ROOT / "unity/Assets/Scripts/Core" / n).read_text(encoding="utf-8")
               for n in ("Loudness.cs", "Attention.cs", "Disturbance.cs"))

lc = TUNING["loudness_constants"]
check("C# hearing_radius_per_l", grab(cs, r"HearingRadiusPerL\s*=\s*([\d.]+)f"),
      lc["hearing_radius_per_l"])
check("C# impulse_per_l", grab(cs, r"ImpulseDisturbancePerL\s*=\s*([\d.]+)f"),
      lc["impulse_disturbance_per_l"])
check("C# sustained_per_l", grab(cs, r"SustainedDisturbancePerL\s*=\s*([\d.]+)f"),
      lc["sustained_disturbance_per_l"])
check("C# occlusion_player", grab(cs, r"OcclusionPlayer\s*=\s*([\d.]+)f"),
      lc["occlusion_player"])
check("C# occlusion_curator", grab(cs, r"OcclusionCurator\s*=\s*([\d.]+)f"),
      lc["occlusion_curator"])

d = TUNING["disturbance"]
check("C# decay_per_min", grab(cs, r"DecayPerMinAtCrew4\s*=\s*([\d.]+)f"),
      d["decay_per_min_at_crew4"])
check("C# ratchet_end", grab(cs, r"RatchetEnd\s*=\s*([\d.]+)f"), d["ratchet_end"])
check("C# cursed_floor", grab(cs, r"PerCursedItemFloor\s*=\s*([\d.]+)f"),
      d["per_cursed_item_floor"])
check("C# tier_pursue", grab(cs, r"PursueAt\s*=\s*([\d.]+)f"), d["tier_pursue_at"])
check("C# tier_collect", grab(cs, r"CollectAt\s*=\s*([\d.]+)f"), d["tier_collect_at"])

a = TUNING["attention"]
check("C# steal_threshold", grab(cs, r"StealThreshold\s*=\s*([\d.]+)f"),
      a["steal_threshold"])
check("C# commit_seconds", grab(cs, r"CommitSeconds\s*=\s*([\d.]+)f"), a["commit_seconds"])
check("C# noise_multiplier", grab(cs, r"NoisePerEvent\s*=\s*([\d.]+)f"),
      a["noise_multiplier_per_event"])
check("C# light_multiplier", grab(cs, r"LightMultiplier\s*=\s*([\d.]+)f"),
      a["light_multiplier"])

v = TUNING["van"]
check("C# van_base_slots", grab(cs, r"BaseSlots\s*=\s*(\d+)"), v["base_slots"])
check("C# van_max_slots", grab(cs, r"MaxSlots\s*=\s*(\d+)"), v["max_slots"])
check("C# ruin_k", grab(cs, r"RuinK\s*=\s*([\d.]+)f"), v["ruin_k"])
check("C# ruin_exp", grab(cs, r"RuinExp\s*=\s*([\d.]+)f"), v["ruin_exp"])

for name, want in TUNING["loudness"].items():
    if name.startswith("_"):
        continue
    key = "".join(p.capitalize() for p in name.split("_"))
    got = grab(cs, rf"NoiseKind\.{key}\s*=>\s*(\d+)")
    if got is not None:
        check(f"C# L[{name}]", got, want)

# --------------------------------------------------------------- JS prototype
js = (ROOT / "proto/index.html").read_text(encoding="utf-8")
check("JS impulse_per_l", grab(js, r"IMPULSE\s*=\s*([\d.]+)"),
      lc["impulse_disturbance_per_l"])
check("JS sustained_per_l", grab(js, r"SUSTAINED\s*=\s*([\d.]+)"),
      lc["sustained_disturbance_per_l"])
check("JS ratchet_end", grab(js, r"RATCHET_END\s*=\s*([\d.]+)"), d["ratchet_end"])
check("JS decay_per_min", grab(js, r"DECAY_PER_S\s*=\s*\(([\d.]+)"),
      d["decay_per_min_at_crew4"])
check("JS appraise_seconds", grab(js, r"APPRAISE_S\s*=\s*([\d.]+)"),
      TUNING["night"]["appraise_seconds"])
check("JS van_slots", grab(js, r"VAN_SLOTS\s*=\s*(\d+)"), v["base_slots"])
check("JS ruin_k", grab(js, r"([\d.]+)\s*\*\s*Math\.pow\(cursed"), v["ruin_k"])
check("JS ruin_exp", grab(js, r"Math\.pow\(cursed,\s*([\d.]+)\)"), v["ruin_exp"])

cm = TUNING["curse"]["value_multiplier"]
check("JS curse_value_tainted",
      grab(js, r"GRADE_MULT\s*=\s*\{\s*clean:1,\s*tainted:([\d.]+)"), cm["tainted"])
check("JS curse_value_malignant",
      grab(js, r"GRADE_MULT\s*=\s*\{[^}]*malignant:([\d.]+)"), cm["malignant"])
am = TUNING["curse"]["attention_multiplier"]
check("JS curse_attention_malignant",
      grab(js, r"ATT_MULT\s*=\s*\{[^}]*malignant:([\d.]+)"), am["malignant"])

# Scope to the loudness table specifically: `sprint` also appears in the movement
# SPEED table, and an unanchored match happily reports 205 px/s as a loudness.
js_l = re.search(r"const L\s*=\s*\{(.*?)\}", js, re.S)
js_l = js_l.group(1) if js_l else ""
for name in ("sprint", "appraise", "door"):
    check(f"JS L[{name}]", grab(js_l, rf"\b{name}\s*:\s*(\d+)"),
          TUNING["loudness"][name])

# --------------------------------------------------------------- Python sims
validator = (ROOT / "sim" / "validate_estate.py").read_text(encoding="utf-8")
check("py validator approach floor",
      grab(validator, r"OCCLUSION_FLOOR\s*=\s*([\d.]+)"),
      lc["approach_occlusion_floor"])
check("py validator min approach",
      grab(validator, r"MIN_APPROACH_M\s*=\s*([\d.]+)"),
      lc["approach_min_warning_m"])
check("py validator occlusion_curator",
      grab(validator, r"^OCCLUSION\s*=\s*([\d.]+)", flags=re.M),
      lc["occlusion_curator"])

rs = TUNING["room_spread"]["factor"]
for _cls, _v in rs.items():
    check(f"py validator spread[{_cls}]",
          grab(validator, rf'"{_cls}":\s*([\d.]+)'), _v)
    check(f"JS spread[{_cls}]", grab(js, rf"{_cls}:([\d.]+)"), _v)

sims = {n: (ROOT / "sim" / n).read_text(encoding="utf-8")
        for n in ("integrated.py", "disturbance.py", "curse_test.py",
                  "appraiser_risk.py", "appraiser_variance.py")}

check("py integrated IMPULSE",
      grab(sims["integrated.py"], r"^IMPULSE\s*=\s*([\d.]+)", flags=re.M),
      lc["impulse_disturbance_per_l"])
check("py integrated SUSTAINED",
      grab(sims["integrated.py"], r"^SUSTAINED\s*=\s*([\d.]+)", flags=re.M),
      lc["sustained_disturbance_per_l"])
check("py integrated DECAY", grab(sims["integrated.py"], r"DECAY_PER_MIN\s*=\s*([\d.]+)"),
      d["decay_per_min_at_crew4"])
check("py integrated RATCHET", grab(sims["integrated.py"], r"RATCHET_END\s*=\s*([\d.]+)"),
      d["ratchet_end"])
check("py integrated VAN_SLOTS", grab(sims["integrated.py"], r"VAN_SLOTS\s*=\s*(\d+)"),
      v["base_slots"])
check("py disturbance IMPULSE",
      grab(sims["disturbance.py"], r"IMPULSE_PER_L\s*=\s*([\d.]+)"),
      lc["impulse_disturbance_per_l"])
# R18: the cursed floor sat at an inert 2.0 in integrated.py and proto/index.html for
# nine rounds while tuning.json, the C# core and curse_test.py all said 7.0 -- and this
# checker could not see it, because both offenders INLINED the number instead of naming
# it. The checker's coverage is exactly the set of constants somebody bothered to name.
# Every model that computes a Disturbance floor is now checked by name.
for _f in ("integrated.py", "curse_test.py", "appraiser_risk.py",
           "appraiser_variance.py"):
    check(f"py {_f} cursed floor",
          grab(sims[_f], r"FLOOR_PER_CURSED\s*=\s*([\d.]+)"),
          d["per_cursed_item_floor"])
check("JS cursed floor", grab(js, r"PER_CURSED_FLOOR\s*=\s*([\d.]+)"),
      d["per_cursed_item_floor"])
for _f in ("appraiser_risk.py", "appraiser_variance.py"):
    check(f"py {_f} RATCHET", grab(sims[_f], r"RATCHET_END\s*=\s*([\d.]+)"),
          d["ratchet_end"])
    check(f"py {_f} DECAY", grab(sims[_f], r"DECAY_PER_MIN\s*=\s*([\d.]+)"),
          d["decay_per_min_at_crew4"])
    check(f"py {_f} VAN_SLOTS", grab(sims[_f], r"VAN_SLOTS\s*=\s*(\d+)"),
          v["base_slots"])
check("py curse ruin_exp", grab(sims["curse_test.py"], r"RUIN_EXP\s*=\s*([\d.]+)"),
      v["ruin_exp"])

for name in ("sprint", "appraise", "door"):
    check(f"py L[{name}]",
          grab(sims["disturbance.py"], rf"[\"']{name}[\"']\s*:\s*(\d+)"),
          TUNING["loudness"][name])

# --------------------------------------------------------------- report
print(f"DRIFT CHECK  -  {checks} constants across 3 implementations")
print("-" * 74)
if not fails:
    print("  OK   every implementation agrees with tuning.json")
    sys.exit(0)
for f in fails:
    print(f"  DRIFT  {f}")
print(f"\n{len(fails)} divergence(s). tuning.json is canonical - fix the implementation.")
sys.exit(1)
