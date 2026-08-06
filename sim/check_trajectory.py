"""
Does the running game behave like the model, or only agree with it on paper?

check_drift.py proves the constants match. check_docs.py proves the tables match.
Neither would have caught R12's bug, which was the most expensive one this
project has had: sustained noise applied per FRAME instead of per SECOND, making
sprinting sixty times too loud. Every constant involved was correct. The defect
was in how they were used, and only running the thing finds that.

So: drive the real prototype through a scripted night (`tools/trace_dist.mjs`),
re-derive the same run here from tuning.json alone, and compare the Disturbance
meter second by second.

    python3 sim/check_trajectory.py

Needs node and playwright. Says so and exits 0 if they are missing, because a
check that cannot run is not a failure - it is an absence, and check.py reports
absences separately.
"""

import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))

TOL = 0.02          # points of Disturbance
NIGHT = 210.0       # proto3d's short QA night
CREW = 1            # the prototype is solo (LOOP_LOG R12)


def reference(dt, n_samples):
    """The same night, derived from canon. Mirrors DESIGN 6.5, nothing else."""
    lc, dst = T["loudness_constants"], T["disturbance"]
    decay_per_s = dst["decay_per_min_at_crew4"] * (CREW / 4.0) / 60.0
    sprint_gain = T["loudness"]["sprint"] * lc["sustained_disturbance_per_l"]
    drop_gain = T["loudness"]["break_small"] * lc["impulse_disturbance_per_l"]

    d, t, out = 0.0, 0.0, []

    def tick(sprinting):
        nonlocal d, t
        t += dt
        if sprinting:
            d = min(100.0, d + sprint_gain * dt)
        floor = dst["ratchet_end"] * (t / NIGHT)       # nothing cursed aboard
        d = max(floor, min(100.0, d - decay_per_s * dt))

    for i in range(300):                     # sprinting
        tick(True)
        if i % 60 == 59:
            out.append((t, d))
    for i in range(300):                     # still
        tick(False)
        if i % 60 == 59:
            out.append((t, d))
    for _ in range(3):                       # impulses
        d = min(100.0, d + drop_gain)
        for i in range(120):
            tick(False)
            if i % 60 == 59:
                out.append((t, d))
    return out[:n_samples]


def main():
    if not (ROOT / "node_modules/playwright").exists():
        print("TRAJECTORY CHECK  -  SKIPPED (playwright not installed)")
        return 0

    env = dict(os.environ)
    if "PW_CHROME" not in env:
        for d in sorted((pathlib.Path(
                env.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))).glob("chromium-*")):
            exe = d / "chrome-linux" / "chrome"
            if exe.exists():
                env["PW_CHROME"] = str(exe)
                break

    r = subprocess.run(["node", "tools/trace_dist.mjs"], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("TRAJECTORY CHECK  -  the prototype could not be driven")
        print(r.stdout + r.stderr)
        return 1

    trace = json.loads(r.stdout)
    got = trace["samples"]
    want = reference(trace["dt"], len(got))

    fails = []
    for (t_g, d_g), (t_w, d_w) in zip(got, want):
        if abs(t_g - t_w) > 1e-6 or abs(d_g - d_w) > TOL:
            fails.append(f"t={t_g:6.2f}s  prototype {d_g:8.4f}   canon {d_w:8.4f}   "
                         f"delta {d_g - d_w:+.4f}")

    print(f"TRAJECTORY CHECK  -  {len(got)} samples of a scripted night, "
          f"prototype vs canon")
    print("-" * 74)
    if not fails:
        peak = max(d for _, d in got)
        print(f"  OK   the running game tracks the model within {TOL} "
              f"(peak {peak:.2f})")
        return 0
    for f in fails[:12]:
        print(f"  DIVERGES  {f}")
    if len(fails) > 12:
        print(f"  ... and {len(fails) - 12} more")
    print("\nThe constants agree and the behaviour does not, which is R12's bug "
          "class - look at how they are applied, not at what they are.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
