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

THREE PROPERTIES, EACH ADDED AFTER THE PREVIOUS ONE PROVED TOO WEAK:

  1. AGREEMENT (R14). Every constant present in more than one place holds the same
     value. Reported "55 constants agree" for four rounds while two implementations
     disagreed about the cursed-cargo floor, because both wrote it inline and named
     constants are all this can see (R18).
  2. COVERAGE (R21). Every numeric leaf in tuning.json is claimed by somebody, with
     UNIMPLEMENTED listing the deliberate gaps. Stays green while the SHIPPING C# core
     lacks a whole subsystem, as long as a Python sim has it.
  3. PER-IMPLEMENTATION COVERAGE (R23). What each of the three actually pins, and what
     the C# core still has to catch up on (CS_BACKLOG).

WHAT "CLAIMED" MEANS, precisely: a check exists pinning that value in that
implementation. It does NOT mean the implementation behaves correctly -- but a check
whose constant is missing from the source reports NOT FOUND, so property 1 catches the
difference. The pair is the guarantee; neither half is one alone.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
_RAW = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

fails, checks = [], 0

# --------------------------------------------------------------- coverage
# R21: the inverse of a drift check. Drift only compares constants that exist on BOTH
# sides, so a value NO implementation has is invisible to it -- R18's lesson one level
# up. Rather than edit seventy call sites to declare their key, wrap the tuning dicts
# and record every lookup: `want` is always a dict access, so reading it IS the claim.
CLAIMED = set()

# R23: per-IMPLEMENTATION coverage. The global check above only asks whether SOMEBODY
# claims a value, which is the weaker property -- it stays green while the shipping C#
# core silently lacks a whole subsystem the sims have moved past.
#
# Attribution needs no call-site edits either. Python evaluates a call's arguments
# before the call, so any tuning lookups since the last check() belong to the check
# about to run. The buffer is marked consumed rather than cleared, so a loop that sweeps
# a table with .items() and then checks two implementations in its body attributes the
# whole table to both -- which is correct, because over the full loop both do check it.
BY_IMPL = {"C#": set(), "JS": set(), "py": set()}
_PENDING = {"paths": set(), "consumed": False}


def _impl_of(label):
    for name in BY_IMPL:
        if label.startswith(name):
            return name
    return None


class Tracked(dict):
    def __init__(self, d, path=()):
        super().__init__(d)
        self._path = path

    def __getitem__(self, k):
        return self._wrap(k, dict.__getitem__(self, k))

    def _wrap(self, k, v):
        p = self._path + (k,)
        if isinstance(v, dict):
            return Tracked(v, p)
        if not k.startswith("_"):        # prose keys are not tuning values
            CLAIMED.add(".".join(p))
            if _PENDING["consumed"]:
                _PENDING["paths"] = set()
                _PENDING["consumed"] = False
            _PENDING["paths"].add(".".join(p))
        return v

    # Iterating a table IS claiming its values -- several checks sweep a whole dict
    # rather than naming each key. Without these, a swept table reads as unclaimed and
    # the coverage report lies in the direction that matters.
    def items(self):
        return [(k, self._wrap(k, v)) for k, v in dict.items(self)]

    def values(self):
        return [self._wrap(k, v) for k, v in dict.items(self)]


def _leaves(d, path=()):
    """Every numeric leaf. Keys starting with _ are prose, not tuning."""
    for k, v in d.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict):
            yield from _leaves(v, path + (k,))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            yield ".".join(path + (k,))


TUNING = Tracked(_RAW)
ALL_LEAVES = set(_leaves(_RAW))

# Canonical values that deliberately live nowhere yet. Every entry is a real gap and
# should be shrinking; anything unclaimed and NOT listed here fails the run, so a
# constant can never be added to tuning.json and quietly forgotten again.
UNIMPLEMENTED = {
    # Every entry is a real gap with a reason, and the list should only ever shrink.
    # R21 took it from 23 to 6 by writing the checks that were merely missing; these
    # six are values no implementation has yet, which is a backlog, not an oversight.
    "attention.recompute_seconds",          # C# retargets every tick; the 2s interval
                                            # is a perf budget nothing enforces yet
    "disturbance.light_wing_gain",          # DESIGN 6.5 light levers: specced,
    "disturbance.lever_kill_lights",        # not built in any of the three
    "disturbance.lever_go_quiet",
    "disturbance.tier_patrol_at",           # every impl hardcodes the 30 boundary in a
                                            # TIERS table keyed by name, not by value
    "loudness_constants.localisation_fuzz_m",   # audio-side; belongs in FMOD, and
                                            # nothing here models where a sound SEEMS
                                            # to come from
}



def check(label, got, want, tol=1e-9):
    global checks
    checks += 1
    impl = _impl_of(label)
    if impl:
        BY_IMPL[impl] |= _PENDING["paths"]
    _PENDING["consumed"] = True
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

check("py chain parallel_exponent",
      grab(sims_chain := (ROOT / "sim" / "chain_sim.py").read_text(encoding="utf-8"),
           r"PARALLEL_EXPONENT\s*=\s*([\d.]+)"),
      TUNING["labour"]["parallel_exponent"])

ca = TUNING["curator_audio"]
check("JS patrol tell @30", grab(js, r"PATROL_TELL_AT_30\s*=\s*([\d.]+)"),
      ca["patrol_tell_interval_at_30_s"])
check("JS patrol tell @60", grab(js, r"PATROL_TELL_AT_60\s*=\s*([\d.]+)"),
      ca["patrol_tell_interval_at_60_s"])

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

# R21 closed these off the coverage backlog. disturbance.py carries the fullest L
# table of the three implementations, so it is the one worth pinning key by key.
for name in ("walk", "sprint", "appraise", "door", "crowbar",
             "break_small", "break_large", "radio", "dolly"):
    check(f"py L[{name}]",
          grab(sims["disturbance.py"], rf"[\"']{name}[\"']\s*:\s*(\d+)"),
          TUNING["loudness"][name])

# The retrieval table drives every haul result in the project and was checked nowhere.
r = TUNING["retrieval"]
for _f in ("integrated.py", "appraiser_risk.py", "appraiser_variance.py"):
    for tier in ("DORMANT", "PATROL", "PURSUE", "COLLECT"):
        check(f"py {_f} retrieval[{tier}]",
              grab(sims[_f], rf'"{tier}":\s*([\d.]+)'), r[tier.lower()])

n = TUNING["night"]
check("py night seconds", grab(sims["integrated.py"], r"NIGHT_S\s*=\s*([\d.]+)"),
      n["seconds"])
check("py haul window", grab(sims["integrated.py"], r"HAUL_S\s*=\s*([\d.]+)"),
      n["haul_window_seconds"])
check("py crew", grab(sims["integrated.py"], r"^CREW\s*=\s*(\d+)", flags=re.M),
      n["crew"])
# NOT checked against proto/index.html on purpose: it ships NIGHT=180 and CREW=1
# because it is a three-minute single-player harness, and R12 found the Disturbance
# decay is crew-dependent. Those two are deliberate divergences, not drift.

# Anchored on CLASS_SLOTS by name. Unanchored, this matched CLASS_WIDTH two lines
# above and cheerfully reported a doorway clearance in metres as a van slot cost --
# the same failure R14 hit when `sprint` matched the movement-SPEED table. Third time
# in this project: a text-scraping check must name the table it means.
for cls, want in TUNING["van"]["slot_cost"].items():
    check(f"py validator slot_cost[{cls}]",
          grab(validator, rf'CLASS_SLOTS = \{{[^}}]*?"{cls}":\s*([\d.]+)'), want)

# Curse tables: the JS prototype and curse_test.py each carry a copy.
for cls, want in TUNING["curse"]["value_multiplier"].items():
    check(f"JS GRADE_MULT[{cls}]",
          grab(js, rf"GRADE_MULT = \{{[^}}]*?{cls}:([\d.]+)"), want)
for cls, want in TUNING["curse"]["attention_multiplier"].items():
    check(f"JS ATT_MULT[{cls}]",
          grab(js, rf"ATT_MULT\s*= \{{[^}}]*?{cls}:([\d.]+)"), want)
    check(f"py curse ATTENTION[{cls}]",
          grab(sims["curse_test.py"], rf'ATTENTION = \{{[^}}]*?"{cls}":\s*([\d.]+)'),
          want)
for cls, want in TUNING["curse"]["ledger_fee"].items():
    check(f"py curse FEE[{cls}]",
          grab(sims["curse_test.py"], rf'FEE = \{{[^}}]*?"{cls}":\s*([\d.]+)'), want)

# --------------------------------------------------------------- coverage report
# The C# core under unity/ is the SHIPPING implementation. Every canonical value the
# sims or the prototype rely on has to reach it eventually, so anything claimed by
# somebody but not by C# is a real port backlog rather than a stylistic gap. Listed
# explicitly so it can only shrink: a value that leaves C#'s reach fails the run, and
# one that arrives has to be struck off.
CS_BACKLOG = {
    # R31 added these two and the ratchet below caught them the same minute, which is
    # the check working exactly as designed: a value cannot enter tuning.json and quietly
    # skip the shipping implementation.
    "labour.parallel_exponent",          # R33, and the C# has no labour model yet
    "curator_audio.patrol_tell_interval_at_30_s",
    "curator_audio.patrol_tell_interval_at_60_s",
    "curse.attention_multiplier.clean",
    "curse.attention_multiplier.malignant",
    "curse.attention_multiplier.tainted",
    "curse.ledger_fee.clean",
    "curse.ledger_fee.malignant",
    "curse.ledger_fee.tainted",
    "curse.value_multiplier.clean",
    "curse.value_multiplier.malignant",
    "curse.value_multiplier.tainted",
    "loudness_constants.approach_min_warning_m",
    "loudness_constants.approach_occlusion_floor",
    "night.appraise_seconds",
    "night.crew",
    "night.haul_window_seconds",
    "night.seconds",
    "retrieval.collect",
    "retrieval.dormant",
    "retrieval.patrol",
    "retrieval.pursue",
    "room_spread.factor.curio",
    "room_spread.factor.mixed",
    "room_spread.factor.uniform",
    "van.slot_cost.armful",
    "van.slot_cost.cart",
    "van.slot_cost.pocket",
    "van.slot_cost.two_man",
}

claimed = CLAIMED & ALL_LEAVES
unclaimed = ALL_LEAVES - CLAIMED
cs_missing = claimed - BY_IMPL["C#"]
cs_new = sorted(cs_missing - CS_BACKLOG)
cs_done = sorted(CS_BACKLOG - cs_missing)
new_gaps = sorted(unclaimed - UNIMPLEMENTED)
stale = sorted(UNIMPLEMENTED & CLAIMED)

# --------------------------------------------------------------- report
print(f"DRIFT CHECK  -  {checks} constants across 3 implementations")
print(f"COVERAGE     -  {len(claimed)}/{len(ALL_LEAVES)} canonical values are claimed by "
      f"at least one implementation, {len(unclaimed)} known gaps")
print("             -  by implementation: "
      + ",  ".join(f"{k} {len(v & ALL_LEAVES)}/{len(ALL_LEAVES)}"
                   for k, v in BY_IMPL.items())
      + f"  ({len(cs_missing)} awaiting the C# port)")
print("-" * 74)
for k in new_gaps:
    fails.append(f"{k}: in tuning.json, checked against NO implementation")
for k in cs_new:
    fails.append(f"{k}: claimed by the sims but NOT by the shipping C# core")
for k in cs_done:
    fails.append(f"{k}: listed in CS_BACKLOG but C# now claims it - remove it")
for k in stale:
    fails.append(f"{k}: listed as unimplemented but IS now checked - "
                 f"remove it from UNIMPLEMENTED")
if not fails:
    print("  OK   every implementation agrees with tuning.json")
    print(f"  OK   no unclaimed canonical values outside the known-gap list")
    sys.exit(0)
for f in fails:
    print(f"  DRIFT  {f}")
print(f"\n{len(fails)} divergence(s). tuning.json is canonical - fix the implementation.")
sys.exit(1)
