"""
Mutation test for the C# core.

    python3 sim/check_core.py     ->  exit 0 if every mutation is caught
                                      exit 1 if a rule is unguarded
                                      exit 2 if the .NET SDK is missing

Needs the .NET SDK, unlike sim/check_drift.py which reads the C# as text. If dotnet
is absent this exits **2**, not 0 — a skipped test must never be mistakable for a
passing one. R18 found the estate validator had been silently exiting 0 while doing
nothing, and R17's regression sweep counted that as green.

--------------------------------------------------------------------------------
WHY THIS EXISTS (LOOP_LOG R19)

`unity/tests/CoreTests` has 31 assertions and they all pass. That says the core
agrees with the simulations on the cases the assertions cover. It does not say the
assertions would notice if a rule were reverted — and reverting a rule is the exact
failure BUILD-PROMPT's non-negotiables list exists to prevent, since each of those
eight was wrong in an earlier draft and corrected by evidence.

So this breaks the core on purpose, one rule at a time, and asks whether anything
notices. Each mutation is run past BOTH guards:

    CoreTests      the 31 behavioural assertions
    check_drift    the 132-check constant guard

A mutation nothing catches is a rule this project believes is pinned and is not.
Constant mutations are expected to be caught by check_drift rather than CoreTests;
that is fine and is reported as such. What matters is the LOGIC mutations, which
check_drift cannot see by construction — it reads literals, not behaviour.

EQUIVALENT MUTANTS. Some mutations do not change behaviour at all, so surviving is
correct and says nothing about test quality. They are marked `equivalent=True`, with
the reason, and are asserted to survive — if one is ever caught, either the analysis
is wrong or the code changed underneath it.
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE = "unity/Assets/Scripts/Core"

# (id, rule, file, old, new, equivalent, note)
MUTATIONS = [
    # ---------------------------------------------------------- LOUDNESS
    ("L1", "walking is free of Disturbance (R3)", f"{CORE}/Loudness.cs",
     "k is NoiseKind.Sprint or NoiseKind.Dolly or NoiseKind.Radio",
     "k is NoiseKind.Sprint or NoiseKind.Dolly or NoiseKind.Radio or NoiseKind.Walk",
     False, "the exact R3 bug: charging for walking pins the meter inside a minute"),
    ("L2", "impulse vs sustained are not interchangeable", f"{CORE}/Loudness.cs",
     "? Of(k) * SustainedDisturbancePerL * dt\n                : Of(k) * ImpulseDisturbancePerL",
     "? Of(k) * ImpulseDisturbancePerL\n                : Of(k) * SustainedDisturbancePerL * dt",
     False, "swap the two branches"),
    ("L3", "hearing radius uses the radius coefficient", f"{CORE}/Loudness.cs",
     "public static float HearingRadius(NoiseKind k) => Of(k) * HearingRadiusPerL;",
     "public static float HearingRadius(NoiseKind k) => Of(k) * OcclusionCurator;",
     False, "wrong coefficient, same shape"),
    ("L4", "the Curator's ear occludes less than a player's", f"{CORE}/Loudness.cs",
     "float occ = curator ? OcclusionCurator : OcclusionPlayer;",
     "float occ = curator ? OcclusionPlayer : OcclusionCurator;",
     False, "EffectiveAt: swap the two occlusion coefficients"),
    ("L5", "sound does not carry past its radius", f"{CORE}/Loudness.cs",
     "return falloff <= 0f ? 0f : l * falloff;",
     "return l * falloff;",
     False, "EffectiveAt: drop the clamp, so distant sources go NEGATIVE"),
    ("L6", "authored loudness table", f"{CORE}/Loudness.cs",
     "NoiseKind.Walk => 20,", "NoiseKind.Walk => 25,",
     False, "a constant - check_drift's job, not CoreTests'"),

    # ---------------------------------------------------------- ATTENTION
    ("A1", "attention is MULTIPLICATIVE, never additive (pillar 2)",
     f"{CORE}/Attention.cs",
     "            if (loot <= 0f) return 0f;   // pillar 2, enforced by arithmetic\n\n"
     "            float mult = 1f + NoisePerEvent * p.NoiseEventsLast10s;\n"
     "            if (p.LightVisible) mult *= LightMultiplier;\n"
     "            return loot * mult;",
     "            float mult = 1f;\n"
     "            if (p.LightVisible) mult *= LightMultiplier;\n"
     "            return loot * mult + NoisePerEvent * p.NoiseEventsLast10s * 500f;",
     False, "the ORIGINAL additive bug from R2, with the zero-guard removed too"),
    ("A2", "additive noise on a CARRYING player", f"{CORE}/Attention.cs",
     "            float mult = 1f + NoisePerEvent * p.NoiseEventsLast10s;\n"
     "            if (p.LightVisible) mult *= LightMultiplier;\n"
     "            return loot * mult;",
     "            float mult = 1f;\n"
     "            if (p.LightVisible) mult *= LightMultiplier;\n"
     "            return loot * mult + NoisePerEvent * p.NoiseEventsLast10s * 500f;",
     False, "additive noise, but the pillar-2 zero-guard left intact"),
    ("A3", "the zero-guard is redundant given multiplicativity",
     f"{CORE}/Attention.cs",
     "            if (loot <= 0f) return 0f;   // pillar 2, enforced by arithmetic\n",
     "",
     True, "loot==0 makes the product 0 anyway; belt-and-braces, no behaviour change"),
    ("A4", "light is a conditional multiplier", f"{CORE}/Attention.cs",
     "if (p.LightVisible) mult *= LightMultiplier;",
     "mult *= LightMultiplier;",
     False, "apply the light bonus unconditionally"),
    ("A5", "curse scales attention", f"{CORE}/Attention.cs",
     "CurseGrade.Malignant => 3.0f,", "CurseGrade.Malignant => 2.0f,",
     False, "attention multiplier constant"),
    ("A6", "tainted scales attention 1.5x", f"{CORE}/Attention.cs",
     "CurseGrade.Tainted => 1.5f,", "CurseGrade.Tainted => 2.0f,",
     False, "constant CoreTests never exercises"),

    # ---------------------------------------------------------- SELECTOR
    ("S1", "hand-off punches through hysteresis", f"{CORE}/Attention.cs",
     "if (handoffTo != null && ReferenceEquals(handoffFrom, Target))",
     "if (false)",
     False, "remove the override entirely - measured 0.0s vs 6.0s"),
    ("S2", "a hand-off only counts FROM the current target", f"{CORE}/Attention.cs",
     "if (handoffTo != null && ReferenceEquals(handoffFrom, Target))",
     "if (handoffTo != null)",
     False, "any hand-off retargets, even from a player nobody was hunting"),
    ("S3", "the commitment lock exists", f"{CORE}/Attention.cs",
     "public const float CommitSeconds = 8.0f;",
     "public const float CommitSeconds = 0.0f;",
     False, "no lock at all"),
    ("S4", "stealing needs a clear margin, not a tie", f"{CORE}/Attention.cs",
     "public const float StealThreshold = 1.25f;",
     "public const float StealThreshold = 1.0f;",
     False, "the flicker the hysteresis exists to prevent"),
    ("S5", "the lock is respected", f"{CORE}/Attention.cs",
     "if (now < _lockedUntil) return;", "if (false) return;",
     False, "ignore the lock while keeping the constant"),

    # ---------------------------------------------------------- DISTURBANCE
    ("D1", "decay scales with crew size (R12)", f"{CORE}/Disturbance.cs",
     "DecayPerMinAtCrew4 * (_crew / 4f) / 60f", "DecayPerMinAtCrew4 / 60f",
     False, "the R12 bug: 50/min swamps a solo player"),
    ("D2", "the floor is per cursed ITEM", f"{CORE}/Disturbance.cs",
     "+ cursedInVan * PerCursedItemFloor", "+ PerCursedItemFloor",
     False, "flat, not per item"),
    ("D3", "the floor is a floor", f"{CORE}/Disturbance.cs",
     "Value = MathF.Max(Floor(cursedInVan),\n                    MathF.Min(100f, Value - DecayPerSecond * dt));",
     "Value = MathF.Min(100f, Value - DecayPerSecond * dt);",
     False, "decay straight through the ratchet"),
    ("D4", "the ratchet is clamped to the night", f"{CORE}/Disturbance.cs",
     "RatchetEnd * Math.Clamp(Elapsed / _nightSeconds, 0f, 1f)",
     "RatchetEnd * (Elapsed / _nightSeconds)",
     False, "floor keeps climbing past sunrise"),
    ("D5", "Disturbance is capped at 100", f"{CORE}/Disturbance.cs",
     "public void AddNoise(NoiseKind k, float dt) =>\n            Value = MathF.Min(100f, Value + Loudness.DisturbanceGain(k, dt));",
     "public void AddNoise(NoiseKind k, float dt) =>\n            Value = Value + Loudness.DisturbanceGain(k, dt);",
     False, "uncapped meter"),
    ("D6", "ghost Static costs 1 Disturbance per point", f"{CORE}/Disturbance.cs",
     "Value = MathF.Min(100f, Value + points);",
     "Value = MathF.Min(100f, Value + points * 3);",
     False, "DESIGN 5.1 - the dead player's budget"),
    ("D7", "tier thresholds", f"{CORE}/Disturbance.cs",
     "public const float PatrolAt = 30f, PursueAt = 60f, CollectAt = 85f;",
     "public const float PatrolAt = 30f, PursueAt = 75f, CollectAt = 85f;",
     False, "constant"),
    ("D8", "retrieval odds per tier", f"{CORE}/Disturbance.cs",
     "CuratorTier.Pursue => 0.10f,", "CuratorTier.Pursue => 0.20f,",
     False, "constant CoreTests never exercises"),

    # ---------------------------------------------------------- ECONOMY
    ("E1", "curse cost is a TAIL RISK, not a fee (R11)", f"{CORE}/Disturbance.cs",
     ": MathF.Min(0.95f, RuinK * MathF.Pow(cursedAboard, RuinExp));",
     ": MathF.Min(0.95f, RuinK * cursedAboard);",
     False, "linear ruin - the shape R10/R11 proved cannot work"),
    ("E2", "ruin probability is capped below certainty", f"{CORE}/Disturbance.cs",
     ": MathF.Min(0.95f, RuinK * MathF.Pow(cursedAboard, RuinExp));",
     ": RuinK * MathF.Pow(cursedAboard, RuinExp);",
     False, "uncapped - exceeds 1.0 at 22+ cursed items"),
    ("E3", "slot costs", f"{CORE}/Disturbance.cs",
     "WeightClass.Pocket => 0.5f,", "WeightClass.Pocket => 1.0f,",
     False, "constant CoreTests never exercises"),
    ("E4", "the empty-van early return is redundant", f"{CORE}/Disturbance.cs",
     "cursedAboard <= 0 ? 0f", "cursedAboard < 0 ? 0f",
     True, "MathF.Pow(0, 1.8) == 0, so RuinChance(0) is 0 either way - verified "
           "identical at 0,1,2,3,5,8,20. First filed as a gap in R19 and reclassified "
           "after checking; the guard only matters for negative input, which is not a "
           "reachable state"),
]


# BUILD-PROMPT's eight non-negotiables, mapped to the mutations that guard them.
# Each was wrong in an earlier draft and corrected by evidence, so each is exactly the
# kind of rule an implementer reverts by accident. A rule with no guarding mutation
# must say WHY here; an empty list with no reason fails the run.
#
# The point of this table is the second half of it. Three of the eight cannot be
# guarded by anything in this repository, because they are Unity behaviour and there
# is no Unity project yet. Those three are the ones most likely to be quietly lost
# during Phase 1 and 3 — and knowing that is worth more than pretending the core
# covers them.
NON_NEGOTIABLES = {
    "attention weighting is multiplicative, never additive": (["A1", "A2"], None),
    "hand-off re-targets instantly, bypassing hysteresis": (["S1", "S2"], None),
    "Disturbance is fast decay + ratcheting floor, crew-scaled": (["D1", "D3", "D4"], None),
    "cursed cargo is a tail risk, not a fee": (["E1", "E2"], None),
    "depth unlocks on work, never on a timer": ([], "guarded outside the core, by "
        "V2 in sim/check_estates.py — the estate validator owns depth gating"),
    "aggro persists to the object, not the person": ([], "NOT GUARDED ANYWHERE. The "
        "core models attention over what a player is carrying; it has no drop event, "
        "so 'the item keeps its aggro after you let go' has nothing to assert against. "
        "Becomes testable at Phase 1, with the networked pickup/carry/drop."),
    "carried items stay non-kinematic": ([], "NOT GUARDED ANYWHERE. Unity physics "
        "behaviour; there is no Unity project yet. Phase 1."),
    "full friendly-fire physics, zero friendly-fire damage": ([], "NOT GUARDED "
        "ANYWHERE. Unity collision behaviour. Phase 1."),
}


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)


def main():
    if shutil.which("dotnet") is None:
        print("SKIPPED - no .NET SDK on PATH. This test cannot run here.")
        print("Exiting 2 so a sweep cannot mistake a skip for a pass.")
        return 2

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="core-mut-"))
    base = tmp / "base"
    shutil.copytree(ROOT, base, ignore=shutil.ignore_patterns(
        ".git", "bin", "obj", "__pycache__", "Library"))

    # One shadow csproj so the target framework is whatever this SDK supports,
    # without editing the repo's own net9.0 project.
    tfm = run(["dotnet", "--version"], base).stdout.strip().split(".")[0]
    proj = base / "proj"
    proj.mkdir()
    (proj / "M.csproj").write_text(f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType><TargetFramework>net{tfm}.0</TargetFramework>
    <Nullable>disable</Nullable><AssemblyName>M</AssemblyName>
    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>
  </PropertyGroup>
  <ItemGroup>
    <Compile Include="../unity/tests/CoreTests/Program.cs" />
    <Compile Include="../unity/Assets/Scripts/Core/*.cs" />
  </ItemGroup>
</Project>""")

    def core_tests():
        r = run(["dotnet", "run", "--project", str(proj / "M.csproj")], base)
        return r.returncode == 0, r

    def drift():
        return run([sys.executable, "sim/check_drift.py"], base).returncode == 0

    print("C# CORE - MUTATION TEST")
    print("=" * 78)
    print("\nCONTROL   unmutated core must pass both guards ... ", end="", flush=True)
    ok_t, r = core_tests()
    ok_d = drift()
    if not (ok_t and ok_d):
        print(f"NO (CoreTests={ok_t}, check_drift={ok_d})")
        print(r.stdout[-2000:])
        shutil.rmtree(tmp, ignore_errors=True)
        return 1
    print("yes")

    originals = {f: (base / f).read_text() for f in {m[2] for m in MUTATIONS}}
    fails, rows = [], []

    print(f"\nMUTANTS   {len(MUTATIONS)} reversions; each must be caught by something")
    print("-" * 78)
    print(f"  {'id':<4}{'core':<6}{'drift':<7}{'verdict':<12}rule")
    print("-" * 78)

    for mid, rule, f, old, new, equivalent, note in MUTATIONS:
        src = originals[f]
        if src.count(old) != 1:
            fails.append(f"{mid}: anchor matches {src.count(old)}x in {f} - "
                         f"mutation could not be applied, so the rule is UNTESTED")
            print(f"  {mid:<4}{'--':<6}{'--':<7}{'ANCHOR?':<12}{rule}")
            continue
        (base / f).write_text(src.replace(old, new, 1))
        caught_t = not core_tests()[0]
        caught_d = not drift()
        (base / f).write_text(src)

        caught = caught_t or caught_d
        if equivalent:
            verdict = "equivalent" if not caught else "UNEXPECTED"
            if caught:
                fails.append(f"{mid}: marked equivalent but WAS caught - the analysis "
                             f"is wrong or the code changed. ({note})")
        else:
            verdict = "caught" if caught else "SURVIVED"
            if not caught:
                fails.append(f"{mid}: nothing caught it - {rule}. Mutation: {note}")
        rows.append((mid, caught_t, caught_d, verdict, rule, note, equivalent))
        print(f"  {mid:<4}{'yes' if caught_t else 'no':<6}"
              f"{'yes' if caught_d else 'no':<7}{verdict:<12}{rule}")

    shutil.rmtree(tmp, ignore_errors=True)

    logic_only = [r for r in rows if r[3] == "caught" and r[1] and not r[2]]
    drift_only = [r for r in rows if r[3] == "caught" and r[2] and not r[1]]
    print("-" * 78)
    print(f"  caught by CoreTests only : {len(logic_only):>2}   (behaviour, the part "
          f"check_drift cannot see)")
    print(f"  caught by check_drift only: {len(drift_only):>2}   (constants CoreTests "
          f"never exercises)")
    print(f"  equivalent (must survive) : "
          f"{sum(1 for r in rows if r[6]):>2}")

    # Tie the result back to BUILD-PROMPT's list of rules that must never be reverted.
    caught_ids = {r[0] for r in rows if r[3] == "caught"}
    known_ids = {m[0] for m in MUTATIONS}
    print(f"\nNON-NEGOTIABLES   BUILD-PROMPT's eight, and what actually guards them")
    print("-" * 78)
    unguarded = 0
    for rule, (ids, why) in NON_NEGOTIABLES.items():
        for i in ids:
            if i not in known_ids:
                fails.append(f"non-negotiable '{rule}' cites mutation {i}, "
                             f"which does not exist")
            elif i not in caught_ids:
                fails.append(f"non-negotiable '{rule}' is guarded by {i}, "
                             f"which nothing catches")
        if ids:
            print(f"  guarded   {rule}  [{', '.join(ids)}]")
        elif why:
            unguarded += 1
            print(f"  {'ELSEWHERE' if 'guarded outside' in why else 'UNGUARDED'} "
                  f"{rule}")
            print(f"              {why}")
        else:
            fails.append(f"non-negotiable '{rule}' has no guard and no reason given")
    print("-" * 78)
    print(f"  {sum(1 for v in NON_NEGOTIABLES.values() if v[0])}/8 guarded by this "
          f"harness, {unguarded} elsewhere or not yet guardable")

    print()
    if not fails:
        print("  OK   every reversion is caught by CoreTests, check_drift, or both")
        return 0
    for x in fails:
        print(f"  GAP  {x}")
    print(f"\n{len(fails)} unguarded rule(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
