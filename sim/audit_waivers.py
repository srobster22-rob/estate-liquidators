"""
Audit the drift checker's waivers.

D-22 named its own failure mode in advance: "a lazy future round can wave a
genuine divergence through by writing a waiver instead of a fix." That round
was R17, the waiver was written in R16, and it was this one:

    ("py/integrated", "disturbance.per_cursed_item_floor",
     "floor-per-cursed is swept in curse_test.py")

integrated.py does not sweep it. It hardcodes `cursed * 2.0` - the pre-R9
value - in the middle of the Disturbance floor calculation, which means every
appraiser number the project has published since R8 was computed with a stale
constant. The waiver was wrong one round after being written, by the same
author who wrote the decision warning about it.

A waiver is a claim: "this file does not embody this constant." This checks
that claim the only way text allows - if a file has a line that talks about
the constant (matching two or more words from its name) AND has a number on
it, the claim is suspect. That is a heuristic and it will produce false
positives; every one of them is answered by adding the pair to ACKNOWLEDGED
with a reason, which is the same discipline as the waivers themselves, one
level up.

    python3 sim/audit_waivers.py      ->  exit 0 if no unexplained suspects
"""

import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_checker():
    spec = importlib.util.spec_from_file_location("check_drift", ROOT / "sim/check_drift.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CD = load_checker()

# Words that carry no signal about which constant a line is talking about.
STOP = {"per", "at", "of", "in", "the", "and", "item", "items", "end", "max",
        "base", "value", "multiplier", "seconds", "min", "k", "exp"}

# (file, path, reason) - suspects a human has looked at and cleared.
ACKNOWLEDGED = [
    ("py/haul_sim", "disturbance.per_cursed_item_floor",
     "DISTURBANCE_PER_SCAN/TRIP are the R5 placeholder model, not the cursed floor"),
    ("py/chain_sim", "van.slot_cost.cart",
     "CLASS_DATA's apex row IS asserted; the comment line mentioning cart trips this"),
    ("py/haul_sim", "loudness_constants.sustained_disturbance_per_l",
     "prose only - line 44 explains the R5 placeholder DISTURBANCE_PER_TRIP that "
     "integrated.py replaced with derived noise; haul_sim implements no per-L gain"),
]


def tokens(path):
    """
    Words from the LEAF of the path only. Including the group name made every
    `van.*` constant match any line mentioning a van and a slot, which buried
    the three real findings under fifteen restatements of `VAN_SLOTS = 14`.
    The cost is that single-word leaves (pocket, malignant, crowbar) fall below
    the two-token bar and are never audited - deliberate, and better than a
    list nobody reads.
    """
    words = re.split(r"[._]", path.rsplit(".", 1)[-1])
    return {w for w in words if len(w) > 2 and w not in STOP}


def asserted_lines(text, file_key):
    """
    Line numbers an assertion already lands on. `const VAN_SLOTS = 14` mentions
    a van and a slot, so it looks like every van.* constant at once - but it is
    already pinned by van.base_slots, and a line that is being checked is not
    an unwatched one.
    """
    lines = set()
    for f, path, pattern, scope, group in CD.A:
        if f != file_key:
            continue
        body, offset = text, 0
        if scope is not None:
            m = re.search(scope, text, re.S | re.M)
            if m is None:
                continue
            body, offset = m.group(0), m.start()
        m = re.search(pattern, body, re.M | re.S)
        if m is None:
            continue
        lines.add(text.count("\n", 0, offset + m.start()) + 1)
    return lines


def main():
    suspects = []
    ack = {(f, p) for f, p, _ in ACKNOWLEDGED}

    for file_key, rel in CD.FILES.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        lines = text.splitlines()
        covered = asserted_lines(text, file_key)
        asserted = {p for f, p, *_ in CD.A if f == file_key}
        for path in CD.CANON:
            if path in asserted or (file_key, path) in ack:
                continue
            if CD.waiver_for(file_key, path) is None:
                continue                      # a coverage hole; check_drift's problem
            want = tokens(path)
            if len(want) < 2:
                continue                      # too weak a signal to act on
            for i, line in enumerate(lines, 1):
                if i in covered:
                    continue
                low = line.lower()
                # Whole words only. Substring matching reported "against" as a
                # mention of light_wing_GAIN.
                if sum(1 for w in want if re.search(rf"\b{w}\b", low)) < 2:
                    continue
                if not re.search(r"\d", line):
                    continue
                suspects.append((file_key, path, i, line.strip()[:96]))
                break

    print(f"WAIVER AUDIT  -  {len(CD.WAIVERS)} waiver rules, "
          f"{len(ACKNOWLEDGED)} previously cleared")
    print("-" * 78)
    if not suspects:
        print("  OK   no waived constant looks like it is actually implemented")
        return 0
    for file_key, path, line_no, line in suspects:
        print(f"  SUSPECT  {file_key}:{path}")
        print(f"           {CD.FILES[file_key]}:{line_no}  {line}")
    print(f"\n{len(suspects)} waiver(s) look false. Either assert the constant "
          f"(and fix the file) or add it to ACKNOWLEDGED with a reason.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
