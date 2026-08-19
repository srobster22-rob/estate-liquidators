"""Retracted numbers must not be quoted as if they were still true.

The root README claimed the appraiser beat blind hauling by +84% in its
"what's solid" list, four paragraphs after the same file said that figure had
been retracted twice and now reads +6%. Both statements were written honestly,
months apart; nothing in the repository was watching for the contradiction.

check_drift.py already guards constants across three implementations. This
guards *claims* across the prose: a number the log has retracted may still
appear - the retraction history is the most useful thing in this project - but
only somewhere that says it was retracted.

    python3 sim/check_claims.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# id, the values the log has retracted, the value that replaced them, and the
# files whose prose must not present a retracted value as current.
CLAIMS = [
    {
        "id": "appraiser-edge",
        "retracted": ["+84%", "+31%"],
        "current": "+6%",
        "guard": ["README.md"],
    },
]

# A retracted value is fine in a sentence that frames it as history.
MARKERS = ("retract", "down from", "not the", "not +", "→", "->", "inflated",
           "first reported", "earlier figure", "was wrong", "second")

# Prose is checked a paragraph at a time: close enough to catch "+84%" sitting
# in a bullet of its own, loose enough not to trip on a proper retraction.
def paragraphs(text):
    start = 0
    for m in re.finditer(r"\n\s*\n", text):
        yield start, text[start:m.start()]
        start = m.end()
    yield start, text[start:]


def main():
    problems = []
    for claim in CLAIMS:
        for name in claim["guard"]:
            path = ROOT / name
            text = path.read_text(encoding="utf-8")
            if claim["current"] not in text:
                problems.append(
                    f"{name}: current value {claim['current']} for "
                    f"{claim['id']} appears nowhere")
            for value in claim["retracted"]:
                for offset, para in paragraphs(text):
                    if value not in para:
                        continue
                    if any(mark in para.lower() for mark in MARKERS):
                        continue
                    line = text.count("\n", 0, offset + para.index(value)) + 1
                    problems.append(
                        f"{name}:{line}: quotes retracted {value} for "
                        f"{claim['id']} with nothing marking it as retracted "
                        f"(current: {claim['current']})")

    print("=" * 74)
    print("CLAIM CHECK  -  retracted numbers must not be stated as current")
    print("-" * 74)
    if problems:
        for p in problems:
            print("  FAIL  " + p)
        print(f"\n  {len(problems)} problem(s)")
        return 1
    total = sum(len(c["retracted"]) * len(c["guard"]) for c in CLAIMS)
    print(f"  OK   {len(CLAIMS)} claim(s), {total} retracted value(s), "
          f"every mention framed as history")
    return 0


if __name__ == "__main__":
    sys.exit(main())
