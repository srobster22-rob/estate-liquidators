"""
Drift check across the four implementations.

The same rules live in sim/*.py, proto/index.html, proto3d/index.html and
unity/Assets/Scripts/Core/*.cs. tuning.json is canonical; this asserts the other
three agree with it. Without this,
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

cm = TUNING["curse"]["value_multiplier"]
am = TUNING["curse"]["attention_multiplier"]

# Both prototypes are checked. proto3d was unchecked until R16 and had already
# drifted - it still carried the pre-R9 cursed floor of 2 while tuning.json,
# curse_test.py and the C# core had all moved to 7.
for tag, rel, l_names in (("JS2d", "proto/index.html", ("sprint", "appraise", "door")),
                          ("JS3d", "proto3d/index.html", ("sprint", "appraise", "door"))):
    js = (ROOT / rel).read_text(encoding="utf-8")
    check(f"{tag} impulse_per_l", grab(js, r"IMPULSE\s*=\s*([\d.]+)"),
          lc["impulse_disturbance_per_l"])
    check(f"{tag} sustained_per_l", grab(js, r"SUSTAINED\s*=\s*([\d.]+)"),
          lc["sustained_disturbance_per_l"])
    check(f"{tag} ratchet_end", grab(js, r"RATCHET_END\s*=\s*([\d.]+)"), d["ratchet_end"])
    check(f"{tag} decay_per_min", grab(js, r"DECAY_PER_S\s*=\s*\(([\d.]+)"),
          d["decay_per_min_at_crew4"])
    check(f"{tag} cursed_floor", grab(js, r"PER_CURSED_FLOOR\s*=\s*([\d.]+)"),
          d["per_cursed_item_floor"])
    check(f"{tag} appraise_seconds", grab(js, r"APPRAISE_S\s*=\s*([\d.]+)"),
          TUNING["night"]["appraise_seconds"])
    # proto3d derives its van from the contract curve; proto has a literal.
    check(f"{tag} van_slots", grab(js, r"VAN_SLOTS\s*=\s*(\d+)")
          or grab(js, r"CONTRACT_VAN=\[(\d+)"), v["base_slots"])
    # Written inline in proto, as named constants in proto3d - accept either.
    check(f"{tag} ruin_k", grab(js, r"RUIN_K\s*=\s*([\d.]+)")
          or grab(js, r"([\d.]+)\s*\*\s*Math\.pow\(cursed"), v["ruin_k"])
    check(f"{tag} ruin_exp", grab(js, r"RUIN_EXP\s*=\s*([\d.]+)")
          or grab(js, r"Math\.pow\(cursed,\s*([\d.]+)\)"), v["ruin_exp"])
    check(f"{tag} curse_value_tainted",
          grab(js, r"GRADE_MULT\s*=\s*\{\s*clean:\s*1,\s*tainted:\s*([\d.]+)"), cm["tainted"])
    check(f"{tag} curse_value_malignant",
          grab(js, r"GRADE_MULT\s*=\s*\{[^}]*malignant:\s*([\d.]+)"), cm["malignant"])
    check(f"{tag} curse_attention_malignant",
          grab(js, r"ATT_MULT\s*=\s*\{[^}]*malignant:\s*([\d.]+)"), am["malignant"])

    # Scope to the loudness table specifically: `sprint` also appears in the movement
    # SPEED table, and an unanchored match happily reports 205 px/s as a loudness.
    js_l = re.search(r"const L\s*=\s*\{(.*?)\}", js, re.S)
    js_l = js_l.group(1) if js_l else ""
    for name in l_names:
        check(f"{tag} L[{name}]", grab(js_l, rf"\b{name}\s*:\s*(\d+)"),
              TUNING["loudness"][name])
    # The prototypes call it `drop`; the spec's table calls it break_small.
    check(f"{tag} L[drop=break_small]", grab(js_l, r"\bdrop\s*:\s*(\d+)"),
          TUNING["loudness"]["break_small"])

# Concealment exists only in the first-person build so far (DESIGN 8.1).
cn = TUNING["concealment"]
js3 = (ROOT / "proto3d/index.html").read_text(encoding="utf-8")
check("JS3d hide_enter_s", grab(js3, r"HIDE_ENTER_S\s*=\s*([\d.]+)"), cn["enter_seconds"])
check("JS3d hide_open_s", grab(js3, r"HIDE_OPEN_S\s*=\s*([\d.]+)"), cn["open_seconds"])
check("JS3d stash_s", grab(js3, r"STASH_S\s*=\s*([\d.]+)"), cn["stash_seconds"])

check("JS3d steal_threshold", grab(js3, r"STEAL_THRESHOLD\s*=\s*([\d.]+)"),
      a["steal_threshold"])
check("JS3d commit_seconds", grab(js3, r"COMMIT_S\s*=\s*([\d.]+)"), a["commit_seconds"])
check("JS3d recompute_seconds", grab(js3, r"RECOMPUTE_S\s*=\s*([\d.]+)"),
      a["recompute_seconds"])
check("JS3d noise_multiplier", grab(js3, r"NOISE_MULT_PER_EVENT\s*=\s*([\d.]+)"),
      a["noise_multiplier_per_event"])
check("JS3d light_multiplier", grab(js3, r"LIGHT_MULT\s*=\s*([\d.]+)"),
      a["light_multiplier"])

# --------------------------------------------------------------- Python sims
sims = {n: (ROOT / "sim" / n).read_text(encoding="utf-8")
        for n in ("integrated.py", "disturbance.py", "curse_test.py",
                  "appraise_test.py", "validate_estate.py")}

w = TUNING["weight"]
vb = w["value_bands"]

# The per-class value bands live in three places now: ECONOMY 3 (prose), the
# validator's CLASS_BANDS, and the prototype's BAND table. R23 found the
# prototype had invented its own - tier 0 banded at the POCKET numbers and a
# made-up x2.6 two-man multiplier - which the level contract rejected on sight.
for key, tier, cls in (("t2_armful", 2, "armful"), ("t2_two_man", 2, "two_man"),
                       ("t3_armful", 3, "armful"), ("t3_two_man", 3, "two_man"),
                       ("t4_cart", 4, "cart")):
    m = re.search(rf'\({tier}, "{cls}"\): \((\d+), (\d+)\)', sims["validate_estate.py"])
    check(f"py CLASS_BANDS[{tier},{cls}] lo", m.group(1) if m else None, vb[key][0])
    check(f"py CLASS_BANDS[{tier},{cls}] hi", m.group(2) if m else None, vb[key][1])

for key, tier, cls in (("t2_armful", 2, "armful"), ("t2_two_man", 2, "two_man"),
                       ("t3_armful", 3, "armful"), ("t3_two_man", 3, "two_man")):
    m = re.search(rf"{tier}:\{{[^}}]*{cls}:\[(\d+),(\d+)\]", js3)
    check(f"JS3d BAND[{tier}].{cls} lo", m.group(1) if m else None, vb[key][0])
    check(f"JS3d BAND[{tier}].{cls} hi", m.group(2) if m else None, vb[key][1])

check("JS3d slot_two_man", grab(js3, r"SLOTS=\{[^}]*two_man:\s*([\d.]+)"),
      w["slots"]["two_man"])
check("JS3d slot_cart", grab(js3, r"SLOTS=\{[^}]*cart:\s*([\d.]+)"), w["slots"]["cart"])
check("JS3d two_man_speed", grab(js3, r"TWO_MAN_SPEED=([\d.]+)"), w["two_man_speed_mult"])
check("JS3d follower_drift", grab(js3, r"FOLLOWER_DRIFT_M=([\d.]+)"), w["follower_drift_m"])

# NOTE: do not name a loop variable `v` here - it is the van tuning dict below,
# and shadowing it made this file crash rather than report a divergence.
fr = TUNING["fragility"]
mb = re.search(r"BREAK_AT_SPEED=\[([\d.,]+)\]", js3)
for i, chance in enumerate(fr["break_chance_at_full_speed"]):
    check(f"JS3d break_chance[{i}]", mb.group(1).split(",")[i] if mb else None, chance)
check("JS3d frag_premium", grab(js3, r"FRAG_PREMIUM=([\d.]+)"),
      fr["value_premium_per_grade"])

ct = TUNING["contract"]
mq = re.search(r"CONTRACT_QUOTA=\[([\d,]+)\]", js3)
mv = re.search(r"CONTRACT_VAN=\[([\d,]+)\]", js3)
for i, quota in enumerate(ct["quota"]):
    check(f"JS3d contract_quota[{i}]",
          mq.group(1).split(",")[i] if mq else None, quota)
for i, slots in enumerate(ct["van_slots"]):
    check(f"JS3d contract_van[{i}]",
          mv.group(1).split(",")[i] if mv else None, slots)
check("JS3d ship_night", grab(js3, r"SHIP_NIGHT=(\d+)"), ct["ship_night_seconds"])
ma = re.search(r"APEX_SHARE=\[([\d.,]+)\]", js3)
for i, share in enumerate(ct["apex_share_of_final_quota"]):
    check(f"JS3d apex_share[{i}]", ma.group(1).split(",")[i] if ma else None, share)
mh = re.search(r"CONTRACT_QUOTA_HERE=\[([\d,]+)\]", js3)
for i, quota in enumerate(ct["quota_measured_210s"]):
    check(f"JS3d measured_quota[{i}]",
          mh.group(1).split(",")[i] if mh else None, quota)

dd = TUNING["dead"]
check("JS3d collection_seconds", grab(js3, r"COLLECT_S=([\d.]+)"), dd["collection_seconds"])
check("JS3d static_cap", grab(js3, r"STATIC_CAP=(\d+)"), dd["static_cap"])
check("JS3d static_regen", grab(js3, r"STATIC_REGEN_S=([\d.]+)"), dd["static_regen_seconds"])
check("JS3d curse_sight_m", grab(js3, r"CURSE_SIGHT_M=([\d.]+)"), dd["curse_sight_m"])
check("JS3d knock_loudness", grab(js3, r"KNOCK_L=(\d+)"), dd["knock_loudness"])
check("JS3d cost_knock", grab(js3, r"COST_KNOCK=(\d+)"), dd["cost_knock"])
check("JS3d cost_nudge", grab(js3, r"COST_NUDGE=(\d+)"), dd["cost_nudge"])

sn = TUNING["senses"]
check("JS3d hear_per_l", grab(js3, r"HEAR_PER_L\s*=\s*([\d.]+)"),
      lc["hearing_radius_per_l"])
check("JS3d occlusion_curator", grab(js3, r"OCCLUSION_CURATOR\s*=\s*([\d.]+)"),
      lc["occlusion_curator"])
check("JS3d localisation_fuzz", grab(js3, r"FUZZ_M\s*=\s*([\d.]+)"),
      lc["localisation_fuzz_m"])
# Anchored: CURSE_SIGHT_M contains SIGHT_M, and an unanchored match reported the
# dead's 5m curse-sight as the Curator's 18m eyesight. Same class of bug as R14's
# `sprint` matching the movement table.
check("JS3d sight_range", grab(js3, r"(?<![A-Z_])SIGHT_M\s*=\s*([\d.]+)"),
      sn["sight_range_m"])
check("JS3d sight_cone", grab(js3, r"SIGHT_COS=Math\.cos\((\d+)"),
      sn["sight_cone_deg"] / 2)
check("JS3d fix_stale", grab(js3, r"FIX_STALE_S\s*=\s*([\d.]+)"),
      sn["fix_stale_seconds"])

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
check("py curse floor", grab(sims["curse_test.py"], r"FLOOR_PER_CURSED\s*=\s*([\d.]+)"),
      d["per_cursed_item_floor"])
# integrated.py had the cursed floor inline as 2.0 until R18 - the pre-R9 value,
# unreadable to this checker because it was a bare literal rather than a constant.
check("py integrated curse floor",
      grab(sims["integrated.py"], r"FLOOR_PER_CURSED\s*=\s*([\d.]+)"),
      d["per_cursed_item_floor"])
check("py integrated appraise_s",
      grab(sims["appraise_test.py"], r"APPRAISE_S\s*=\s*([\d.]+)"),
      TUNING["night"]["appraise_seconds"])
check("py curse ruin_exp", grab(sims["curse_test.py"], r"RUIN_EXP\s*=\s*([\d.]+)"),
      v["ruin_exp"])

for name in ("sprint", "appraise", "door"):
    check(f"py L[{name}]",
          grab(sims["disturbance.py"], rf"[\"']{name}[\"']\s*:\s*(\d+)"),
          TUNING["loudness"][name])

# --------------------------------------------------------------- report
print(f"DRIFT CHECK  -  {checks} constants across 4 implementations")
print("-" * 74)
if not fails:
    print("  OK   every implementation agrees with tuning.json")
    sys.exit(0)
for f in fails:
    print(f"  DRIFT  {f}")
print(f"\n{len(fails)} divergence(s). tuning.json is canonical - fix the implementation.")
sys.exit(1)
