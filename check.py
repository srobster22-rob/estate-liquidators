"""
One command for the whole regression suite.

    python3 check.py            # everything available on this machine
    python3 check.py --fast     # skip the mutation test (the slow one, ~11s)

Before R16 the suite was four commands in three documents, one of which
(`python validate_estate.py`) did not exist - the file had no entry point, so
the round that reported "estate validator PASS" cannot have run it that way.
Anything that needs a toolchain this machine lacks is reported as SKIPPED with
the reason, never quietly omitted: a suite that hides what it did not run is
how "all green" stops meaning anything.
"""

import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
FAST = "--fast" in sys.argv


def run(name, cmd, cwd=ROOT, env=None):
    e = dict(os.environ, **(env or {}))
    r = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True)
    return name, r.returncode == 0, (r.stdout + r.stderr).strip()


def find_chrome():
    """Preinstalled Chromium, whatever build number this machine happens to have."""
    base = pathlib.Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    if not base.is_dir():
        return None
    for d in sorted(base.glob("chromium-*")):
        exe = d / "chrome-linux" / "chrome"
        if exe.exists():
            return str(exe)
    return None


results, skipped = [], []

results.append(run("drift check", [sys.executable, "sim/check_drift.py"]))

if FAST:
    skipped.append(("mutation test", "--fast"))
else:
    results.append(run("mutation test", [sys.executable, "sim/mutate_drift.py"]))

results.append(run("estate validator", [sys.executable, "validate_estate.py"],
                   cwd=ROOT / "sim"))

if shutil.which("dotnet"):
    results.append(run("C# core suite",
                       ["dotnet", "run", "--project", "unity/tests/CoreTests"]))
else:
    skipped.append(("C# core suite", "no dotnet on PATH - install the .NET 9 SDK"))

if (ROOT / "node_modules/playwright").exists():
    chrome = find_chrome()
    results.append(run("prototype smoke test", ["node", "tools/proto_smoke.mjs"],
                       env={"PW_CHROME": chrome} if chrome else None))
else:
    skipped.append(("prototype smoke test", "playwright not installed - `npm i playwright`"))

print("=" * 78)
print("ESTATE LIQUIDATORS - regression suite")
print("=" * 78)
for name, ok, _ in results:
    print(f"  {'PASS' if ok else 'FAIL':<5} {name}")
for name, why in skipped:
    print(f"  SKIP  {name}  ({why})")

failed = [r for r in results if not r[1]]
for name, _, out in failed:
    print(f"\n{'-' * 78}\n{name}\n{'-' * 78}\n{out}")

print()
if failed:
    print(f"{len(failed)} of {len(results)} checks failed.")
elif skipped:
    print(f"{len(results)} checks passed; {len(skipped)} could not run here.")
else:
    print(f"All {len(results)} checks passed.")
sys.exit(1 if failed else 0)
