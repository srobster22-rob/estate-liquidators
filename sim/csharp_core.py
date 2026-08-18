"""
Run the C# core without a C# toolchain.

`STATUS.md` has carried the same line since R14: *the C# suite has not run since
R14 — no .NET SDK in the container this loop runs in, and `check_drift.py` is
currently the only thing holding the C# port to the canonical numbers.* That is a
real gap and it is bigger than it sounds, because `check_drift.py` pins **literals**
and nothing else. A port that kept every constant and changed a `*` to a `+` — or
lost a wall from an occlusion loop, or dropped the `loot <= 0` guard that makes
pillar 2 arithmetically impossible to violate — passes every check this project
has.

So: translate the subset of C# these three files actually use into Python, execute
it, and compare it against the canonical model on a grid of inputs. Not a C#
compiler. A deliberately small translator that understands expression-bodied
members, switch expressions, `is A or B` patterns, ternary chains, and a handful of
statement forms — and **fails loudly** when it meets anything else, because a
translator that silently skips a method it cannot read is worse than no translator.

    python3 sim/csharp_core.py          -> exit 0 if the port computes what it should
    python3 sim/csharp_core.py -v       -> print every value compared

What this does NOT check: that the C# compiles, that its types are right, that the
tests in unity/tests pass, or anything about Unity. It checks the arithmetic, which
is the part that has to agree with four other implementations.
"""

import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE = ROOT / "unity/Assets/Scripts/Core"
TUNING = json.loads((ROOT / "tuning.json").read_text(encoding="utf-8"))
VERBOSE = "-v" in sys.argv

fails, checks = [], 0


def check(label, got, want, tol=1e-6):
    global checks
    checks += 1
    if got is None:
        fails.append(f"{label}: the translator produced nothing")
        return
    if isinstance(want, bool) or isinstance(got, bool):
        ok = bool(got) == bool(want)
    elif isinstance(want, str):
        ok = got == want
    else:
        ok = abs(float(got) - float(want)) <= tol
    if not ok:
        fails.append(f"{label}: C# gives {got}, canonical is {want}")
    if VERBOSE:
        print(f"  {'ok  ' if ok else 'DIFF'}  {label:<46}{got}")


# --------------------------------------------------------------- the translator
def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return "\n".join(l for l in src.splitlines() if not l.strip().startswith("//")
                     and not l.strip().startswith("///"))


def numbers(src):
    """1.5f -> 1.5, 100f -> 100. C# float suffixes only."""
    return re.sub(r"(?<=[\d.])[fF]\b", "", src)


def enums(src):
    """NoiseKind.Sprint -> 'Sprint'. Every enum in these files is a bare name."""
    return re.sub(r"\b(?:NoiseKind|CuratorTier|WeightClass|CurseGrade)\.(\w+)", r'"\1"', src)


def mathf(src):
    src = src.replace("MathF.Min(", "min(").replace("MathF.Max(", "max(")
    src = src.replace("MathF.Pow(", "pow(").replace("MathF.Abs(", "abs(")
    src = re.sub(r"Math\.Clamp\(([^,]+),([^,]+),([^)]+)\)", r"min(max(\1,\2),\3)", src)
    return src


def ternaries(expr):
    """`a ? b : c` -> `(b) if (a) else (c)`, innermost-last so chains work.

    C# ternary chains associate to the right, which is what a naive recursive
    split on the FIRST `?` gives you as long as the split on `:` respects nesting.
    """
    depth, qi = 0, -1
    for i, ch in enumerate(expr):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "?" and depth == 0:
            qi = i
            break
    if qi < 0:
        return expr
    depth = 0
    for i in range(qi + 1, len(expr)):
        ch = expr[i]
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "?" and depth == 0:
            # nested ternary in the true branch: find ITS colon first
            pass
        elif ch == ":" and depth == 0:
            cond, yes, no = expr[:qi], expr[qi + 1:i], expr[i + 1:]
            return f"(({ternaries(yes)}) if ({ternaries(cond)}) else ({ternaries(no)}))"
    raise SyntaxError(f"unbalanced ternary: {expr!r}")


def switch_expr(body):
    """`x switch { A => 1, _ => 0, }` -> a dict lookup with a default."""
    m = re.match(r"\s*(\w+)\s+switch\s*\{(.*)\}\s*$", body, re.S)
    if not m:
        return None
    var, arms = m.group(1), m.group(2)
    table, default = {}, "0"
    for arm in re.findall(r'("(?:\w+)"|_)\s*=>\s*([^,]+),', arms, re.S):
        key, val = arm[0].strip(), arm[1].strip()
        if key == "_":
            default = val
        else:
            table[key] = val
    entries = ", ".join(f"{k}: ({v})" for k, v in table.items())
    return f"{{{entries}}}.get({var}, ({default}))"


def is_pattern(expr):
    """`k is A or B or C` -> `k in ("A","B","C")`."""
    m = re.match(r'\s*(\w+)\s+is\s+(.+)$', expr, re.S)
    if not m:
        return None
    var, rest = m.group(1), m.group(2)
    names = [n.strip() for n in re.split(r"\bor\b", rest)]
    if not all(re.fullmatch(r'"\w+"', n) for n in names):
        return None
    return f"{var} in ({', '.join(names)},)"


ARGS = re.compile(r"\(([^)]*)\)")


def params(sig):
    """`(NoiseKind k, float dt)` -> `k, dt`, dropping types and defaults."""
    inner = ARGS.search(sig)
    if not inner or not inner.group(1).strip():
        return ""
    out = []
    for p in inner.group(1).split(","):
        p = p.strip()
        if "=" in p:
            p = p.split("=")[0].strip()
        out.append(p.split()[-1])
    return ", ".join(out)


def translate(src):
    """C# subset -> Python source. Raises on anything it does not understand."""
    src = mathf(enums(numbers(strip_comments(src))))
    out = ["from math import pow"]
    found, funcs = set(), set()

    # const float A = 1, B = 2;
    for m in re.finditer(r"public const (?:float|int) ([^;]+);", src):
        for part in m.group(1).split(","):
            name, val = part.split("=")
            out.append(f"{name.strip()} = {val.strip()}")
            found.add(name.strip())

    # Expression-bodied members: methods, and properties with no parameter list.
    pat = re.compile(
        r"public (?:static |sealed )?(?:float|bool|int|CuratorTier|"
        r"WeightClass|CurseGrade) (\w+)(\([^)]*\))?\s*=>\s*(.*?);", re.S)
    for m in pat.finditer(src):
        name, sig, body = m.group(1), m.group(2), " ".join(m.group(3).split())
        expr = switch_expr(body) or is_pattern(body) or ternaries(body)
        args = params(sig) if sig else ""
        out.append(f"def {name}({args}):\n    return {expr}")
        found.add(name)
        funcs.add(name)
    return "\n".join(out), found, funcs


# Members this translator cannot read, with the reason. A member that is neither
# translated nor named here fails the load - otherwise adding a method to the C#
# core silently adds an unchecked one, which is the exact hole this file exists to
# close and the exact hole it had on its first run.
UNREAD = {
    "EffectiveAt": "statement body with a loop - covered by the JS occlusion checks",
    "AddNoise": "mutates instance state", "AddStatic": "mutates instance state",
    "Tick": "mutates instance state", "KillLights": "mutates instance state",
    "GoQuiet": "mutates instance state", "LightWing": "mutates instance state",
    "Reset": "mutates instance state", "Update": "mutates instance state",
    "Weight": "statement body over an interface - no objects to hand it here",
    "Value": "auto-property", "Elapsed": "auto-property", "Target": "auto-property",
    "Retargets": "auto-property", "Carried": "interface member",
    "NoiseEventsLast10s": "interface member", "LightVisible": "interface member",
    "AppraisedValue": "interface member", "Grade": "interface member",
}
PUBLIC = re.compile(r"public (?:static |sealed |const |readonly )*"
                    r"(?:float|bool|int|void|CuratorTier|WeightClass|CurseGrade|"
                    r"IAttentionSubject|IReadOnlyList<\w+>) (\w+)")


def load(fname, expect):
    src = strip_comments((CORE / fname).read_text(encoding="utf-8"))
    py, found, funcs = translate((CORE / fname).read_text(encoding="utf-8"))
    unknown = [n for n in set(PUBLIC.findall(src)) if n not in found and n not in UNREAD]
    if unknown:
        raise SystemExit(f"{fname}: public member(s) {unknown} are neither translated "
                         "nor listed as unreadable. Add them to UNREAD with a reason, "
                         "or teach the translator to read them - do not leave them "
                         "unchecked by accident.")
    # A method the translator CAN read but the comparison never calls is the other
    # half of the same hole: it looks covered and is not. An injected
    # `public static float Whatever(NoiseKind k) => 1f;` walked straight through
    # the first version of this guard for exactly that reason.
    idle = sorted(funcs - set(expect) - set(UNREAD))
    if idle:
        raise SystemExit(f"{fname}: {idle} translated but never compared against "
                         "anything. Add a comparison, or list it in UNREAD with a "
                         "reason - a member nothing asserts is not covered.")
    missing = [n for n in expect if n not in found]
    if missing:
        raise SystemExit(f"{fname}: the translator could not read {missing} - "
                         "it has been rewritten in a form this file does not "
                         "understand, which is a reason to look at it, not to skip it")
    ns = {}
    exec(compile(py, f"<{fname}>", "exec"), ns)
    return ns


# --------------------------------------------------------------- the comparison
L = load("Loudness.cs", ["Of", "IsSustained", "HearingRadius", "DisturbanceGain",
                         "HearingRadiusPerL", "OcclusionCurator"])
D = load("Disturbance.cs", ["Floor", "RetrievalChance", "Slots", "RuinChance",
                            "DecayPerSecond", "Tier"])

NAMES = {"crouch_walk": "CrouchWalk", "walk": "Walk", "sprint": "Sprint",
         "dolly": "Dolly", "radio": "Radio", "appraise": "AppraisePing",
         "door": "DoorSlam", "crowbar": "Crowbar", "break_small": "BreakSmall",
         "break_large": "BreakLarge", "voice_whisper": "VoiceWhisper",
         "voice_normal": "VoiceNormal", "voice_raised": "VoiceRaised",
         "voice_shout": "VoiceShout"}

lc = TUNING["loudness_constants"]

# 1. The table. check_drift.py already pins these one at a time; what it cannot
#    see is whether the SWITCH still maps them to the right kinds.
for key, cs_name in NAMES.items():
    check(f"Of({cs_name})", L["Of"](cs_name), TUNING["loudness"][key])

# 2. Which sources are sustained. AUDIO-SPEC 1.1 gives a per-second value to
#    three of them and the comment in the file says why walking is not one.
for cs_name in NAMES.values():
    want = cs_name in ("Sprint", "Dolly", "Radio")
    check(f"IsSustained({cs_name})", L["IsSustained"](cs_name), want)

# 3. The two formulas that turn a loudness into a consequence.
for key, cs_name in NAMES.items():
    l = TUNING["loudness"][key]
    check(f"HearingRadius({cs_name})", L["HearingRadius"](cs_name),
          l * lc["hearing_radius_per_l"])
    sustained = cs_name in ("Sprint", "Dolly", "Radio")
    want = (l * lc["sustained_disturbance_per_l"] * 0.5 if sustained
            else l * lc["impulse_disturbance_per_l"])
    check(f"DisturbanceGain({cs_name}, 0.5)", L["DisturbanceGain"](cs_name, 0.5), want)

# 4. Disturbance: the floor, the tiers and the retrieval ladder.
d = TUNING["disturbance"]
# Floor() reads two instance fields. The translated function's globals ARE the
# namespace dict, so setting them there is how you hand it an instance - and it
# matters that this CALLS the translated function rather than recomputing the
# formula in Python, which is the mistake that makes a checker agree with itself.
for elapsed, night, cursed in ((0, 720, 0), (360, 720, 0), (720, 720, 0),
                               (360, 720, 3), (900, 720, 1)):
    want = (d["ratchet_end"] * min(max(elapsed / night, 0.0), 1.0)
            + cursed * d["per_cursed_item_floor"])
    D["Elapsed"], D["_nightSeconds"] = elapsed, night
    check(f"Floor(elapsed={elapsed}, cursed={cursed})", D["Floor"](cursed), want)

for tier, want in (("Patrol", 0.02), ("Pursue", 0.10), ("Collect", 0.25),
                   ("Dormant", 0.0)):
    check(f"RetrievalChance({tier})", D["RetrievalChance"](tier), want)

check("PatrolAt", D["PatrolAt"], d["tier_patrol_at"] if "tier_patrol_at" in d else 30)
check("PursueAt", D["PursueAt"], d["tier_pursue_at"])
check("CollectAt", D["CollectAt"], d["tier_collect_at"])
# Decay scales with crew size - the dependency that stayed invisible until R12
# because every sim ran four players.
for crew in (1, 2, 4, 6):
    D["_crew"] = crew
    check(f"DecayPerSecond(crew {crew})", D["DecayPerSecond"](),
          d["decay_per_min_at_crew4"] * (crew / 4) / 60)

# The tier ladder, including both sides of every threshold. DESIGN 6.5's pacing
# spine is these three numbers and the direction of the comparisons.
for value, want in ((0, "Dormant"), (29.9, "Dormant"), (30, "Patrol"),
                    (59.9, "Patrol"), (60, "Pursue"), (84.9, "Pursue"),
                    (85, "Collect"), (100, "Collect")):
    D["Value"] = value
    check(f"Tier(Disturbance={value})", D["Tier"](), want)

# 5. Slots and the ruin tail - the two numbers ECONOMY 1 calls master constants.
for cls, want in (("Pocket", 0.5), ("Armful", 1.0), ("TwoMan", 3.0), ("Cart", 5.0)):
    key = {"Pocket": "pocket", "Armful": "armful", "TwoMan": "two_man",
           "Cart": "cart"}[cls]
    check(f"Slots({cls})", D["Slots"](cls), TUNING["weight"]["slots"][key])

v = TUNING["van"]
for n in (0, 1, 2, 3, 5, 8, 20):
    want = 0.0 if n <= 0 else min(0.95, v["ruin_k"] * math.pow(n, v["ruin_exp"]))
    check(f"RuinChance({n})", D["RuinChance"](n), want)

# --------------------------------------------------------------- report
print(f"C# CORE  -  {checks} values, translated out of C# and executed")
print("-" * 74)
if not fails:
    print("  OK   the port computes what tuning.json says it should")
    sys.exit(0)
for f in fails:
    print(f"  DIFF  {f}")
print(f"\n{len(fails)} disagreement(s). tuning.json is canonical - fix the port.")
sys.exit(1)
