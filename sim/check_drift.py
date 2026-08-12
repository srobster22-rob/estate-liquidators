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
#
# R21: every model now READS tuning.json instead of declaring its own copy, so the
# per-literal checks that used to live here are gone -- there is no literal left to
# check. That is a strictly stronger guarantee than this file could offer: a value
# cannot drift if there is only one of it.
#
# The structural half of that guarantee lives in sim/audit.py, which fails if any
# model stops reading tuning.json, loses its entry point, or multiplies a runtime
# term by a tuned constant the way R16's bug did. Run both.
sims = {p_.name: p_.read_text(encoding="utf-8") for p_ in (ROOT / "sim").glob("*.py")}
for name in ("integrated.py", "disturbance.py", "curse_test.py", "chain_sim.py",
             "haul_sim.py", "curator_attention.py", "scan_risk.py", "hiding.py",
             "levers.py"):
    check(f"py {name} reads tuning.json",
          1.0 if "tuning.json" in sims.get(name, "") else 0.0, 1.0)

# Concealment (R17). hiding.py reads tuning.json at runtime so it cannot drift; these
# pin the two values that also appear as literals in the specs' pseudo-code, and the
# ordering invariant that the whole mechanic rests on.
c = TUNING["concealment"]
check("py hiding uses tuning", 1.0 if "TUNING[\"concealment\"]" in
      (ROOT / "sim/hiding.py").read_text(encoding="utf-8") else 0.0, 1.0)
_search_max = c["search_giveup_seconds"] + c["search_spread_seconds"]
# THE invariant: the search window must straddle the stash timer. If its maximum is
# below stash_quiet, stashing saves the item 100% of the time and D-03's free-reset
# exploit is back. If its minimum is above, stashing never works and the verb is dead.
check("concealment search straddles stash (low)",
      1.0 if c["search_giveup_seconds"] < c["stash_quiet_seconds"] else 0.0, 1.0)
check("concealment search straddles stash (high)",
      1.0 if _search_max > c["stash_quiet_seconds"] else 0.0, 1.0)

# R19: levers are consumables priced in slots, not a rate-limited free action. The
# cooldown constant is retired but kept so disturbance.py still reproduces R18; assert
# the charge model exists so nobody quietly reinstates the cooldown as the real answer.
check("lever charges are priced in slots",
      1.0 if d.get("lever_charge_slot_cost", 0) > 0 else 0.0, 1.0)
check("recommended charges is an interior optimum, not a max",
      1.0 if 0 < d.get("lever_charges_recommended", 0) <= 2 else 0.0, 1.0)

# R20: the quota curve and apex band are canonical now, because both had drifted --
# chain_sim.py was still printing pass rates against the ORIGINAL quota list that
# ECONOMY 4 replaced and marked broken.
pg = TUNING["progression"]
cs_py = (ROOT / "sim/chain_sim.py").read_text(encoding="utf-8")
# R21: these were literal-matching checks until chain_sim started reading the values.
# Now assert it reads them, and that the curve is internally coherent -- a quota list
# and a van list of different lengths is a crash waiting for night five.
check("py chain reads quota curve",
      1.0 if 'quota_by_night' in cs_py and 'apex_band' in cs_py else 0.0, 1.0)
check("progression lists are same length",
      1.0 if len(pg["quota_by_night"]) == len(pg["van_by_night"])
      == len(pg["target_pass_rate"]) else 0.0, 1.0)
# Quotas must rise. A flat or falling step is a chain with no shape, which is the
# exact failure ECONOMY 4 exists to prevent and which has now happened twice.
check("quota curve rises monotonically",
      1.0 if all(b > a_ for a_, b in zip(pg["quota_by_night"],
                                         pg["quota_by_night"][1:])) else 0.0, 1.0)

# The crew exponent must match between the model and the prototype -- it is the one
# tuned number that lives as an expression rather than a table entry.
check("JS decay_crew_exp", grab(js, r"DECAY_CREW_EXP\s*=\s*([\d.]+)"),
      d["decay_crew_exponent"])
# Sub-linear, or a solo crew is hunted far harder than a full one (R18).
check("decay exponent is sub-linear",
      1.0 if 0.0 < d["decay_crew_exponent"] < 1.0 else 0.0, 1.0)

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
