"""
Estate Liquidators — structural audit of the apparatus itself.

`check_drift.py` answers "do the implementations agree with tuning.json?" This file
answers the question that keeps turning out to matter more:

    **What is the checker unable to see?**

Four of the five rounds R16-R20 found apparatus that had quietly stopped describing the
current design, and every one was found by accident while doing something else:

  R16  `integrated.py` carried a cursed floor of 2.0 four rounds after the canonical
       value became 7.0 -- invisible because it lived as `cursed * 2.0` inside an
       expression, and the checker only reads NAMED constants.
  R17  `validate_estate.py` had no entry point at all. `validate()` was defined,
       `EXPECTED_FAILURES` was declared, nothing called either, so running it printed
       nothing and exited 0 -- indistinguishable from passing.
  R18  `disturbance.py` still defaulted to the pre-R4 decay of 1.0/min and a cursed
       floor of 3.0, and had no ratcheting floor at all. Running it printed the exact
       broken escalation the project had already rejected.
  R20  `chain_sim.py`'s QUOTAS list was still the ORIGINAL quota curve that ECONOMY 4
       replaced and explicitly marked as broken.

Every one is the same shape: **the checked surface is narrower than the file.** Finding
them by luck four times running is not a process, so this enumerates the gaps instead.

None of these checks can prove a model is right. They catch the specific, repeated
failure of a model that is no longer *connected* to the numbers it claims to use.

    python sim/audit.py        ->  exit 0 if the apparatus is sound

Requires nothing outside the standard library.
"""

import ast
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SIM = ROOT / "sim"
TUNING = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

# Files that are apparatus rather than models: they check things, they don't tune.
INFRASTRUCTURE = {"check_drift.py", "audit.py", "estates.py"}
DOCS = ("DESIGN.md", "ECONOMY.md", "LEVEL-SPEC.md", "TECH-SPEC.md", "AUDIO-SPEC.md",
        "README.md", "DECISIONS.md")

# Canonical values no model reads, ON PURPOSE. An allowlist with reasons beats a
# check that quietly tolerates them, because the reason is the thing that goes stale:
# when a model finally does simulate crouching, this line is what says "wire it up".
ACKNOWLEDGED = {
    "loudness.crouch_walk": "AUDIO-SPEC 1.2; no model simulates crouch movement yet",
    "loudness.voice_whisper": "voice is a player-audibility input, not simulated",
    "loudness.voice_normal": "voice is a player-audibility input, not simulated",
    "loudness.voice_raised": "voice is a player-audibility input, not simulated",
    "loudness.voice_shout": "voice is a player-audibility input, not simulated",
    "loudness.crowbar": "AUDIO-SPEC 1.2; no model simulates prying yet",
    "loudness_constants.localisation_fuzz_m":
        "TECH-SPEC A5; no model simulates where the Curator thinks you are",
    "attention.recompute_seconds":
        "TECH-SPEC A3; sims recompute every tick, which is stricter",
}

findings = []


def fail(kind, msg):
    findings.append((kind, msg))


def canonical_values():
    """Every tuned number in tuning.json, flattened, with its path."""
    out = {}

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("_"):
                    continue
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            out.setdefault(float(node), []).append(path)

    walk(TUNING, "")
    return out


CANON = canonical_values()


# ------------------------------------------------------------------ check 1
def check_reads_tuning(path, src):
    """R18's failure: a model with its own private copy of the constants.

    A model that reads tuning.json cannot carry a stale default. A model that does
    not is trusting a human to remember it exists.
    """
    if "tuning.json" in src:
        return True
    fail("DISCONNECTED",
         f"{path.name} defines its own constants and never reads tuning.json. "
         f"This is how R18's file shipped the pre-R4 decay for fifteen rounds.")
    return False


# ------------------------------------------------------------------ check 2
def check_has_entry_point(path, src):
    """R17's failure: a suite that runs nothing and exits 0."""
    if "__main__" in src:
        return True
    fail("NO ENTRY POINT",
         f"{path.name} has no `if __name__ == '__main__'` block, so running it "
         f"prints nothing and exits 0 -- indistinguishable from passing.")
    return False


# ------------------------------------------------------------------ check 3
# WATCHLIST — concepts whose value has actually drifted, or would hurt if it did.
#
# The first two cuts of this check tried to be universal: flag every literal equal to
# a canonical value (176 findings, almost all coincidence -- `8` is a loudness value,
# `0.5` is a slot cost), then only "distinctive" ones (60 findings, still mostly
# coincidence: a 0.08 probability rate matching a 0.08 ledger fee).
#
# Both were the wrong shape, and the reason is worth writing down: **numeric equality
# is weak evidence.** Worse, it could never have caught R16 -- that bug was `cursed *
# 2.0` against a canonical 7.0, so the literal did NOT match and no equality test
# would fire.
#
# What identifies a drifted copy is CONTEXT: a line that talks about a concept and
# carries a number that is not that concept's canonical value. That catches R16
# exactly. It needs a curated list of concepts rather than all 63 values, which is a
# deliberate trade -- narrower, but every finding is worth reading.
WATCH = [
    ("cursed floor", r"cursed", ["disturbance", "per_cursed_item_floor"]),
    ("decay", r"decay|DECAY", ["disturbance", "decay_per_min_at_crew4"]),
    ("ratchet", r"ratchet|RATCHET", ["disturbance", "ratchet_end"]),
    ("van slots", r"VAN_SLOTS|van_slots", ["van", "base_slots"]),
    ("collect tier", r"tier_collect|COLLECT_AT|collect_at", ["disturbance",
                                                            "tier_collect_at"]),
    ("steal threshold", r"steal|STEAL", ["attention", "steal_threshold"]),
    ("ruin exponent", r"ruin_exp|RUIN_EXP", ["van", "ruin_exp"]),
]


def canon_at(keys):
    node = TUNING
    for k in keys:
        node = node[k]
    return float(node)


def check_concept_drift(path, src):
    """A line that discusses a tuned concept and carries a different number.

    This is R16's exact signature and the one shape no equality check can see.
    """
    for label, pattern, keys in WATCH:
        want = canon_at(keys)
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#") or '"""' in line:
                continue
            # Display code mentions everything and tunes nothing.
            if "print(" in line or ":>" in line or ":<" in line:
                continue

            num = r"(\d+\.?\d*)"
            # The shapes a tuned copy actually takes. Co-location is not enough --
            # `d = max(floor, min(100.0, d - DECAY/60))` mentions decay and carries
            # 100.0, and that is the meter cap, not a stale decay rate.
            #
            # Multiplication is only suspicious against a LOWERCASE term. `cursed *
            # 2.0` is R16's bug -- a runtime count times a tuned rate. `0.5 *
            # VAN_SLOTS` is a coefficient on a named constant, which is checkable and
            # fine, and flagging it taught me the difference.
            low = "|".join(a for a in pattern.split("|") if a.islower() or "_" in a)
            hits = []
            if low:
                hits += re.findall(rf"(?<![A-Z_])(?:{low})\s*\*\s*{num}", line)
            hits += re.findall(rf"(?:{pattern})\w*\s*=\s*{num}\s*(?:#|$)", line)
            vals = [float(h) for h in hits if float(h) not in (0.0, 1.0)]
            if not vals or want in vals:
                continue
            fail("CONCEPT DRIFT",
                 f"{path.name}:{i} multiplies or assigns {label} with {vals} rather "
                 f"than the canonical {want}. R16\'s bug was exactly this shape.")


# ------------------------------------------------------------------ check 5
def check_docs_quote_canon():
    """Docs that quote a superseded number.

    R20 found `chain_sim.py` printing pass rates against a quota curve two rounds
    dead. Prose rots the same way and is read far more often than code.
    """
    watched = {
        "quota curve": ([str(q) for q in TUNING["progression"]["quota_by_night"]],
                        ["7,500", "9,000", "10,750", "12,500"]),
        "apex band": ([f"{TUNING['progression']['apex_band'][0]:,}"],
                      ["4,000 – 8,000", "4,000–8,000"]),
    }
    for doc in ("DESIGN.md", "ECONOMY.md", "LEVEL-SPEC.md", "README.md"):
        text = (ROOT / doc).read_text(encoding="utf-8")
        for label, (_current, superseded) in watched.items():
            for dead in superseded:
                # Word boundaries matter: without them "9,000" matches inside the
                # CURRENT "$19,000" and the check reports its own new numbers as
                # stale. Found by reading the first run's output rather than
                # trusting it, which is the habit this whole file exists to enforce.
                for m in re.finditer(r"(?<![\d,])" + re.escape(dead) + r"(?![\d,])",
                                     text):
                    line = text[:m.start()].count("\n") + 1
                    context = text[max(0, m.start() - 700):m.start()].lower()
                    # A superseded number is fine when it is explicitly labelled as
                    # history. This project keeps dead numbers on purpose.
                    if any(w in context for w in
                           ("supersed", "replaced", "old ", "originally", "dead",
                            "was ", "re-band", "recalibrat", "revised", "previous")):
                        continue
                    fail("STALE PROSE",
                         f"{doc}:{line} quotes {dead} ({label}) with no nearby marker "
                         f"saying it is superseded.")


# ------------------------------------------------------------------ check 6
def check_orphan_canon(all_src):
    """Canonical values nothing reads.

    Either the value is dead and should be removed, or a model that should be using
    it is quietly using something else.
    """
    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("_"):
                    continue
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, (int, float, list)) and path:
            leaf = path.split(".")[-1]
            if leaf in all_src:
                return
            # A value the SPECS use but no model reads is fine -- plenty of tuning is
            # prose-only until something needs to simulate it. A value nothing
            # anywhere mentions is either dead or being shadowed by a private copy.
            in_docs = any(leaf in (ROOT / d).read_text(encoding="utf-8")
                          or leaf.replace("_", " ") in
                          (ROOT / d).read_text(encoding="utf-8").lower()
                          for d in DOCS)
            if path in ACKNOWLEDGED or in_docs:
                return
            if True:
                fail("ORPHAN",
                     f"tuning.json `{path}` is read by no model and mentioned in no "
                     f"spec. Dead value, or a model using its own copy?")

    walk(TUNING, "")


def main():
    sims = sorted(p for p in SIM.glob("*.py"))
    sources = {p: p.read_text(encoding="utf-8") for p in sims}

    for path, src in sources.items():
        if path.name in INFRASTRUCTURE:
            continue
        check_reads_tuning(path, src)
        check_has_entry_point(path, src)
        check_concept_drift(path, src)

    check_docs_quote_canon()

    everything = "\n".join(sources.values())
    everything += (ROOT / "proto/index.html").read_text(encoding="utf-8")
    for cs in (ROOT / "unity/Assets/Scripts/Core").glob("*.cs"):
        everything += cs.read_text(encoding="utf-8")
    check_orphan_canon(everything)

    print(f"APPARATUS AUDIT  -  {len(sims)} models, {len(CANON)} canonical values")
    print("-" * 74)
    if not findings:
        print("  OK   every model reads canonical tuning, runs, and reports")
        return 0

    by_kind = {}
    for kind, msg in findings:
        by_kind.setdefault(kind, []).append(msg)
    for kind in sorted(by_kind):
        print(f"\n  {kind}  ({len(by_kind[kind])})")
        for msg in by_kind[kind]:
            print(f"    - {msg}")
    print(f"\n{len(findings)} finding(s). None of these prove a model is WRONG -- they")
    print("mark places where a model is no longer connected to the numbers it claims.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
