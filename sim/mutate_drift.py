"""
Mutation test for the drift checker. Answers one question: can each of its
assertions actually fail?

R14 hand-injected two fake divergences and concluded the checker worked. That
proved two of fifty-five patterns could fire. R16 found the rest of the answer
the hard way - the cursed-item floor had been wrong in both prototypes since
R9, and no pattern was watching it. A checker that only ever passes is
worthless, and "I tested two of them" does not scale to 177.

So: for every assertion, copy the tree, corrupt exactly that literal, run
check_drift.py, and require it to exit non-zero AND name that specific
constant. A mutant that survives is a hole in the checker.

    python3 sim/mutate_drift.py           ->  exit 0 if every mutant is killed
    python3 sim/mutate_drift.py -v        ->  print each mutation

Costs one subprocess per assertion; a full run is a few seconds.
"""

import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_checker():
    spec = importlib.util.spec_from_file_location("check_drift", ROOT / "sim/check_drift.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CD = load_checker()


def locate(text, pattern, scope, group):
    """Absolute (start, end) of the captured literal, or None."""
    offset = 0
    if scope is not None:
        m = re.search(scope, text, re.S | re.M)
        if m is None:
            return None
        offset, text = m.start(), m.group(0)
    m = re.search(pattern, text, re.M | re.S)
    if m is None or m.group(group) is None:
        return None
    return offset + m.start(group), offset + m.end(group)


def perturb(literal):
    """A different number that is still a valid literal in the same syntax."""
    value = float(literal)
    if "." in literal:
        # ".08" -> "1.08" keeps the leading-dot form matchable.
        return f"{value + 1:g}" if not literal.startswith(".") else f"1{literal}"
    return str(int(literal) + 1)


def run(tree):
    r = subprocess.run([sys.executable, str(tree / "sim/check_drift.py")],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main(verbose=False):
    with tempfile.TemporaryDirectory() as tmp:
        tree = pathlib.Path(tmp) / "repo"
        shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", "bin", "obj", "Library"))

        # Control. If the clean copy does not pass, nothing below means anything.
        code, out = run(tree)
        if code != 0:
            print("CONTROL FAILED - the unmutated copy does not pass:")
            print(out)
            return 1

        survivors, unlocatable, killed = [], [], 0
        for file_key, path, pattern, scope, group in CD.A:
            label = f"{file_key}:{path}"
            target = tree / CD.FILES[file_key]
            original = target.read_text(encoding="utf-8")
            span = locate(original, pattern, scope, group)
            if span is None:
                unlocatable.append(label)
                continue
            a, b = span
            mutant = original[:a] + perturb(original[a:b]) + original[b:]
            target.write_text(mutant, encoding="utf-8")
            try:
                code, out = run(tree)
                if code != 0 and label in out:
                    killed += 1
                    if verbose:
                        print(f"  killed  {label}  ({original[a:b]} -> {mutant[a:b]})")
                else:
                    survivors.append(
                        f"{label}  (exit {code}, "
                        f"{'named' if label in out else 'NOT NAMED'} in output)")
            finally:
                target.write_text(original, encoding="utf-8")

    total = len(CD.A)
    print(f"MUTATION TEST  -  {killed}/{total} assertions provably able to fail")
    print("-" * 78)
    if not survivors and not unlocatable:
        print("  OK   every assertion in check_drift.py detects a corrupted literal")
        return 0
    for s in survivors:
        print(f"  SURVIVED  {s}")
    for u in unlocatable:
        print(f"  UNLOCATABLE  {u}  - pattern matched during the check but not here")
    print("\nA surviving mutant is a constant the drift checker is not really guarding.")
    return 1


if __name__ == "__main__":
    sys.exit(main(verbose="-v" in sys.argv))
