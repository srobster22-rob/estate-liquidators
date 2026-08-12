"""
Do the documents still say what the code says?

`check_drift.py` guards the implementations. Nothing guarded the *specifications*
- and the specs are where a human reads a number before typing it somewhere.
Worse, the spec tables carry DERIVED columns: AUDIO-SPEC 1.2 prints a hearing
radius and a Disturbance delta for every event, both computed by hand from L and
the constants in 1.1. A hand-computed column is a copy of a calculation, and a
copy of a calculation drifts exactly like a copy of a constant.

This re-derives them and compares:

  AUDIO-SPEC 1.2   L, "Curator hears at" = L x 0.33, dDisturbance = L x 0.09
                   (impulse) or L x 0.02 (the three sustained sources)
  ECONOMY 1        slot cost per weight class
  DESIGN 4.2       the ruin curve's quoted percentages

    python3 sim/check_docs.py       ->  exit 0 if the prose agrees with tuning.json
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

fails, checks = [], 0


def check(label, got, want, tol):
    global checks
    checks += 1
    if got is None:
        fails.append(f"{label}: not found in the document")
    elif abs(got - want) > tol:
        fails.append(f"{label}: document says {got:g}, canon gives {want:g}")


def rows(text, heading):
    """The markdown table under `heading`, as lists of stripped cells."""
    body = text.split(heading, 1)[1] if heading in text else ""
    out = []
    for line in body.splitlines():
        if not line.startswith("|"):
            if out:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and not set("".join(cells)) <= set("-: "):
            out.append(cells)
    return out


def number(cell):
    """
    First number in a cell. Strips the thousands comma and the dollar sign -
    without that, "$5,750" parses as 5 and the checker reports a disagreement
    that is entirely its own. R14 lost time to three regexes like this one; the
    rule is the same as it was then: fix the pattern, never the document.
    """
    m = re.search(r"(\d+(?:\.\d+)?)", cell.replace("**", "").replace(",", "")
                                            .replace("$", ""))
    return float(m.group(1)) if m else None


# ------------------------------------------------------- AUDIO-SPEC 1.2
audio = (ROOT / "AUDIO-SPEC.md").read_text(encoding="utf-8")
LC = T["loudness_constants"]
SUSTAINED = set(LC["_sustained_sources"])

# Table label -> tuning key. The document writes for humans ("Breakage - small"),
# tuning.json writes for machines. This mapping is the only place they meet.
EVENTS = {
    "Crouch-walk": "crouch_walk", "Voice — whisper": "voice_whisper",
    "Walk": "walk", "Voice — normal": "voice_normal", "Dolly on hardwood": "dolly",
    "Radio transmit": "radio", "Sprint": "sprint", "Voice — raised": "voice_raised",
    "Appraiser ping": "appraise", "Door slam": "door", "Voice — shout": "voice_shout",
    "Crowbar strike": "crowbar", "Breakage — small": "break_small",
    "Breakage — large": "break_large",
}

seen = set()
for row in rows(audio, "## 1.2 The event table"):
    label = row[0].replace("**", "").strip()
    key = EVENTS.get(label)
    if key is None:
        continue
    seen.add(key)
    L = T["loudness"][key]
    check(f"AUDIO 1.2 [{label}] L", number(row[1]), L, 1e-9)
    check(f"AUDIO 1.2 [{label}] hearing radius", number(row[2]),
          L * LC["hearing_radius_per_l"], 0.06)
    delta = row[3].strip()
    if delta in ("—", "-", ""):
        # A dash is a hard zero, and only non-sustained events may claim one.
        if key in SUSTAINED:
            fails.append(f"AUDIO 1.2 [{label}]: marked '—' but {key} is a "
                         f"sustained source, which must show a per-second gain")
        checks += 1
    elif key in SUSTAINED:
        check(f"AUDIO 1.2 [{label}] sustained gain", number(delta),
              L * LC["sustained_disturbance_per_l"], 0.06)
    else:
        check(f"AUDIO 1.2 [{label}] impulse gain", number(delta),
              L * LC["impulse_disturbance_per_l"], 0.06)

missing = set(EVENTS.values()) - seen
if missing:
    fails.append(f"AUDIO 1.2: the table has lost rows for {sorted(missing)}")

# ------------------------------------------------------- ECONOMY 1
econ = (ROOT / "ECONOMY.md").read_text(encoding="utf-8")
SLOTS = {"Pocket": "pocket", "Armful": "armful", "Two-man": "two_man", "Cart": "cart"}
for row in rows(econ, "## 1. Van capacity"):
    key = SLOTS.get(row[0].replace("**", "").strip())
    if key:
        check(f"ECONOMY 1 [{row[0]}] slot cost", number(row[1]),
              T["van"]["slot_cost"][key], 1e-9)

check("ECONOMY 1 base van", number(econ.split("**Base van:")[1][:12]),
      T["van"]["base_slots"], 1e-9)

# ------------------------------------------------------- ECONOMY 4
# The quota curve lived in ECONOMY's prose, in chain_sim, and in a calibration
# nobody had re-run - three places, three values (R26).
prog = T["progression"]
night_rows = [r for r in rows(econ, "## 4. Quota curve")
              if r[0].strip().isdigit()]
for r in night_rows:
    n = int(r[0]) - 1
    if n < len(prog["quotas"]):
        check(f"ECONOMY 4 night {n + 1} quota", number(r[1]), prog["quotas"][n], 1e-9)
        check(f"ECONOMY 4 night {n + 1} van", number(r[2]), prog["van_by_night"][n], 1e-9)
if len(night_rows) != len(prog["quotas"]):
    fails.append(f"ECONOMY 4: table has {len(night_rows)} nights, "
                 f"tuning.json has {len(prog['quotas'])}")

# ------------------------------------------------------- DESIGN 4.2
design = (ROOT / "DESIGN.md").read_text(encoding="utf-8")
block = design.split("P(ruin)", 1)[1][:400] if "P(ruin)" in design else ""
for line in block.splitlines():
    m = re.match(r"\s*(\d+) pieces?\s+~?([\d.]+)%", line)
    if not m:
        continue
    n = int(m.group(1))
    want = min(0.95, T["van"]["ruin_k"] * n ** T["van"]["ruin_exp"]) * 100
    check(f"DESIGN 4.2 ruin at {n} cursed", float(m.group(2)), want, 0.6)

# ------------------------------------------------------- report
print(f"DOC CHECK  -  {checks} numbers re-derived from tuning.json")
print("-" * 74)
if not fails:
    print("  OK   the specifications agree with canon, derived columns included")
    sys.exit(0)
for f in fails:
    print(f"  FAIL  {f}")
print(f"\n{len(fails)} disagreement(s). The documents are what humans read before "
      f"they type a number - fix them.")
sys.exit(1)
