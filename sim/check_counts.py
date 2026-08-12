"""
Do the documented check counts match what the suites report?

README.md and STATUS.md both quote "N checks" and "N constants". Those numbers
drifted three times in fifteen rounds - written by hand, from memory, while the
suite they describe was still growing. For a project whose main asset is that its
numbers are trustworthy, a wrong number in the first paragraph of the README is
not a footnote.

    python3 sim/check_counts.py          -> exit 0 if the docs agree with reality

Runs check_drift.py directly and reads proto3d/qa.mjs's own count only if the
harness has been run (--qa N passes the number in, so this needs no browser).
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def documented(pattern):
    out = {}
    for name in ("README.md", "STATUS.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for m in re.finditer(pattern, text):
            out.setdefault(name, []).append(int(m.group(1)))
    return out


def main():
    fails = []

    drift = subprocess.run([sys.executable, str(ROOT / "sim/check_drift.py")],
                           capture_output=True, text=True)
    m = re.search(r"DRIFT CHECK\s+-\s+(\d+) constants", drift.stdout)
    if not m:
        print("could not read a constant count from check_drift.py")
        return 2
    real_drift = int(m.group(1))

    qa = None
    if "--qa" in sys.argv:
        qa = int(sys.argv[sys.argv.index("--qa") + 1])

    for name, nums in documented(r"check_drift\.py\s+#\s+(\d+) constants").items():
        for n in nums:
            if n != real_drift:
                fails.append(f"{name} says {n} constants, check_drift.py reports {real_drift}")

    if qa is not None:
        for pat in (r"qa\.mjs\s+#\s+(\d+) checks", r"\*\* (\d+) headless checks"):
            for name, nums in documented(pat).items():
                for n in nums:
                    if n != qa:
                        fails.append(f"{name} says {n} checks, the harness reports {qa}")

    print(f"COUNT CHECK  -  drift {real_drift}" + (f", qa {qa}" if qa else ""))
    print("-" * 74)
    if not fails:
        print("  OK   the documented numbers are the real ones")
        return 0
    for f in fails:
        print(f"  STALE  {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
