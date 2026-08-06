"""
Provenance (GAME-CONCEPTS.md #16) — the kill test, run.

THE BET
    A generative model of *how objects get made* produces forgeries with real internal
    inconsistencies, so the tells are learnable but never memorisable.

THE STATED KILL CONDITION
    "Generated flaws come out either trivially visible or invisible, with nothing in
    between. That's the standard failure of procedural puzzles and it shows itself inside
    the first fifty generated items."

WHAT THIS MEASURES
    The card proposes 50 text dossiers and a friend, measuring accuracy at item 5 against
    item 50. That needs a human. What does *not* need a human is the thing underneath it:
    whether a learnable middle band exists at all. If every forgery is either flawless or
    obvious, no amount of playtesting rescues it, and the concept dies here for free.

    Three measurements, in increasing order of how much they can hurt:

    M1  Cue distribution. How many detectable inconsistencies does a forgery carry?
        Bimodal at 0 and many = dead. A populated middle = a game.

    M2  The learning curve. A detector who knows R of the period rules — accuracy as R
        climbs 0..all. Smooth and rising = tells are learnable. A step function = you
        either know the trick or you don't, which is memorisation, not skill.

    M3  Precision on genuine objects. A detector who flags real pieces is not playing a
        deduction game, they are playing a coin flip with extra steps.

    No dependencies, deterministic, runs in about a second.
"""

import random
from collections import Counter

# --- The world model -------------------------------------------------------------------
#
# Seven attributes. Each period admits some values and not others. This is the "how objects
# get made" model the bet rests on: the constraints are what make a forgery detectable, and
# they overlap between neighbouring periods, which is what stops detection being trivial.

PERIODS = ["Queen Anne", "Georgian", "Regency", "Victorian", "Edwardian"]

# attribute -> period -> set of plausible values
RULES = {
    "primary_wood":   {"Queen Anne": {"walnut", "maple"},
                       "Georgian":   {"mahogany", "walnut"},
                       "Regency":    {"mahogany", "rosewood"},
                       "Victorian":  {"mahogany", "oak", "rosewood"},
                       "Edwardian":  {"oak", "satinwood", "mahogany"}},

    "secondary_wood": {"Queen Anne": {"pine", "oak"},
                       "Georgian":   {"pine", "oak"},
                       "Regency":    {"pine", "deal"},
                       "Victorian":  {"deal", "pine"},
                       "Edwardian":  {"deal", "plywood"}},

    "joinery":        {"Queen Anne": {"hand_dovetail_coarse"},
                       "Georgian":   {"hand_dovetail_coarse", "hand_dovetail_fine"},
                       "Regency":    {"hand_dovetail_fine"},
                       "Victorian":  {"hand_dovetail_fine", "machine_dovetail"},
                       "Edwardian":  {"machine_dovetail"}},

    "finish":         {"Queen Anne": {"oil_wax"},
                       "Georgian":   {"oil_wax", "shellac"},
                       "Regency":    {"shellac", "french_polish"},
                       "Victorian":  {"french_polish", "varnish"},
                       "Edwardian":  {"varnish", "spirit_lacquer"}},

    "hardware":       {"Queen Anne": {"handmade_brass", "iron_pin"},
                       "Georgian":   {"handmade_brass", "cast_brass"},
                       "Regency":    {"cast_brass"},
                       "Victorian":  {"cast_brass", "machine_screw"},
                       "Edwardian":  {"machine_screw", "pressed_steel"}},

    "saw_marks":      {"Queen Anne": {"pit_saw"},
                       "Georgian":   {"pit_saw", "frame_saw"},
                       "Regency":    {"frame_saw"},
                       "Victorian":  {"circular_saw", "frame_saw"},
                       "Edwardian":  {"circular_saw", "band_saw"}},

    "wear_pattern":   {"Queen Anne": {"deep_uneven"},
                       "Georgian":   {"deep_uneven", "moderate"},
                       "Regency":    {"moderate"},
                       "Victorian":  {"moderate", "light"},
                       "Edwardian":  {"light", "minimal"}},
}

ATTRS = list(RULES)

# Every value that exists anywhere, per attribute — the forger's palette.
ALL_VALUES = {a: sorted({v for p in PERIODS for v in RULES[a][p]}) for a in ATTRS}


def make_genuine(period, rng, honest_anomalies=False):
    """
    A real object: every attribute drawn from what that period actually admits.

    With `honest_anomalies`, the object also carries the inconsistencies real antiques
    carry — a repair, a replaced part, a transitional example made at a period boundary.
    These are period-violating and *entirely genuine*.

    This is the correction that makes M3 mean anything. v1 drew genuines from the same
    rules the detector checked against, so "does a detector flag a genuine?" was
    arithmetically zero and could never fail. It also modelled the wrong world: honest
    anomalies are the reason authentication is hard, and they are what force the game's
    real decision — not "is anything inconsistent?" but "how much inconsistency is too
    much?" A design where one violation means forgery is a lookup table, not a game.
    """
    obj = {a: rng.choice(sorted(RULES[a][period])) for a in ATTRS}
    if not honest_anomalies:
        return obj
    r = rng.random()
    if r < 0.55:
        return obj                       # untouched, as it left the workshop
    n = 1 if r < 0.88 else 2             # a repair, or a long life with two
    idx = PERIODS.index(period)
    for a in rng.sample(ATTRS, n):
        later = [PERIODS[i] for i in range(idx + 1, len(PERIODS))]
        cands = sorted({v for p in later for v in RULES[a][p]} - RULES[a][period])
        if cands:
            obj[a] = rng.choice(cands)   # replaced with something from a later period
    return obj


def make_forgery(period, rng, skill):
    """
    A forgery of `period`, by a forger of the given skill.

    The forger gets most things right and errs on a few. Errors are *plausible* — a value
    from a neighbouring period, not a random one — which is what stops this being a
    spot-the-anachronism quiz. `skill` sets how many attributes they get wrong.

    NOTE (v2): skill 0 is permitted, and produces a forgery indistinguishable from a
    genuine object. v1 forced at least one error, which made "invisible forgery" a
    measurement that could not come back non-zero — an instrumentation artifact that
    flattered the design. A perfect forgery is the interesting case, not an edge case.
    """
    obj = make_genuine(period, rng)
    if skill <= 0:
        return obj
    wrong_attrs = rng.sample(ATTRS, min(skill, len(ATTRS)))
    idx = PERIODS.index(period)
    for a in wrong_attrs:
        # Prefer a value from an adjacent period: the believable mistake.
        neighbours = [PERIODS[i] for i in (idx - 1, idx + 1) if 0 <= i < len(PERIODS)]
        candidates = sorted({v for n in neighbours for v in RULES[a][n]} - RULES[a][period])
        if not candidates:
            candidates = sorted(set(ALL_VALUES[a]) - RULES[a][period])
        if candidates:
            obj[a] = rng.choice(candidates)
    return obj


def visible_cues(obj, period, known_attrs):
    """How many inconsistencies a detector who knows `known_attrs` can actually see."""
    return sum(1 for a in known_attrs if obj[a] not in RULES[a][period])


def draw_skill(rng):
    """
    Forger errors: a master-forger tail that includes genuinely perfect fakes, a fat
    middle, and a crude tail. v1 had no zero, which was the artifact.
    """
    r = rng.random()
    if r < 0.08:
        return 0              # perfect forgery — undetectable, by construction
    if r < 0.20:
        return 1              # one slip
    if r < 0.82:
        return rng.randint(2, 3)
    return rng.randint(4, 6)  # crude


# --- M1: cue distribution --------------------------------------------------------------

def m1_cue_distribution(n=4000, seed=1):
    rng = random.Random(seed)
    counts = Counter()
    for _ in range(n):
        p = rng.choice(PERIODS)
        f = make_forgery(p, rng, draw_skill(rng))
        counts[visible_cues(f, p, ATTRS)] += 1
    return counts, n


# --- M2: the learning curve ------------------------------------------------------------

def m2_learning_curve(n=6000, seed=2):
    """
    A detector who knows R of the 7 rules, judging a 50/50 mix. Genuines now carry honest
    anomalies, so the detector must pick a *threshold*: flag as forgery at >= T cues. We
    give them the best threshold available at that knowledge level — the ceiling a perfect
    player could reach knowing R rules.
    """
    rng = random.Random(seed)
    rows = []
    for R in range(len(ATTRS) + 1):
        sample = []
        for _ in range(n):
            p = rng.choice(PERIODS)
            known = rng.sample(ATTRS, R)
            is_fake = rng.random() < 0.5
            obj = (make_forgery(p, rng, draw_skill(rng)) if is_fake
                   else make_genuine(p, rng, honest_anomalies=True))
            sample.append((visible_cues(obj, p, known), is_fake))
        best_acc, best_T = 0.0, 1
        for T in range(1, len(ATTRS) + 1):
            acc = sum(1 for c, f in sample if (c >= T) == f) / n
            if acc > best_acc:
                best_acc, best_T = acc, T
        rows.append((R, best_acc, best_T))
    return rows


# --- M3: can ANY threshold separate a repaired genuine from a good forgery? -------------

def m3_separation(n=8000, seed=3):
    """
    The real kill test. Full knowledge of all seven rules. Genuines carry honest
    anomalies; forgeries carry forger errors. If the two cue-count distributions overlap
    badly, no threshold separates them, and the game is a coin flip wearing a monocle.

    Returns the two distributions and the best accuracy any threshold can achieve.
    """
    rng = random.Random(seed)
    gen, fake = Counter(), Counter()
    for _ in range(n):
        p = rng.choice(PERIODS)
        gen[visible_cues(make_genuine(p, rng, honest_anomalies=True), p, ATTRS)] += 1
        fake[visible_cues(make_forgery(p, rng, draw_skill(rng)), p, ATTRS)] += 1
    best_acc, best_T = 0.0, 1
    for T in range(1, len(ATTRS) + 2):
        tn = sum(v for c, v in gen.items() if c < T)
        tp = sum(v for c, v in fake.items() if c >= T)
        acc = (tn + tp) / (2 * n)
        if acc > best_acc:
            best_acc, best_T = acc, T
    return gen, fake, best_acc, best_T, n


def bar(frac, width=40):
    return "#" * int(round(frac * width))


if __name__ == "__main__":
    print("=" * 74)
    print("PROVENANCE (#16) — kill test")
    print("=" * 74)

    print("\nM1  How many detectable inconsistencies does a forgery carry?")
    print("    Kill condition: bimodal at 0 and many, with an empty middle.\n")
    counts, n = m1_cue_distribution()
    for cues in sorted(counts):
        frac = counts[cues] / n
        print(f"      {cues} cue(s): {frac:6.1%}  {bar(frac)}")
    middle = sum(counts[c] for c in counts if 1 <= c <= 3) / n
    invisible = counts.get(0, 0) / n
    print(f"\n      invisible (0 cues):        {invisible:6.1%}")
    print(f"      learnable middle (1-3):    {middle:6.1%}")
    print(f"      obvious (4+):              {sum(counts[c] for c in counts if c >= 4)/n:6.1%}")

    print("\n" + "-" * 74)
    print("\nM2  Best achievable accuracy vs. how many of the 7 rules you know.")
    print("    Genuines carry honest anomalies, so the detector must pick a threshold.")
    print("    Kill condition: flat (knowledge doesn't pay) or a step (one trick is all).\n")
    print("      rules known   ceiling   best threshold")
    rows = m2_learning_curve()
    for R, acc, T in rows:
        print(f"           {R}         {acc:6.1%}      >= {T} cue(s)   {bar(acc, 24)}")
    gains = [rows[i][1] - rows[i - 1][1] for i in range(1, len(rows))]
    climb = rows[-1][1] - rows[0][1]
    print(f"\n      per-rule gain: min {min(gains):+.1%}  max {max(gains):+.1%}")
    print(f"      largest single jump as share of total climb: {max(gains)/climb:.0%}")

    print("\n" + "-" * 74)
    print("\nM3  THE REAL TEST. Full knowledge. Can any threshold separate a repaired")
    print("    genuine from a competent forgery?")
    print("    Kill condition: the distributions overlap so badly that the ceiling is")
    print("    near chance. That would make the game a coin flip wearing a monocle.\n")
    gen, fake, best_acc, best_T, n3 = m3_separation()
    print("      cues   genuine (w/ repairs)   forgery")
    for c in range(0, max(max(gen), max(fake)) + 1):
        g, f = gen.get(c, 0) / n3, fake.get(c, 0) / n3
        print(f"       {c}      {g:6.1%} {bar(g, 18):18s}   {f:6.1%} {bar(f, 18)}")
    print(f"\n      best threshold: flag at >= {best_T} cues")
    print(f"      ceiling accuracy at that threshold: {best_acc:.1%}")
    overlap = sum(min(gen.get(c, 0), fake.get(c, 0)) for c in set(gen) | set(fake)) / n3
    print(f"      distribution overlap: {overlap:.1%} of mass is ambiguous")

    print("\n" + "=" * 74)
    print("VERDICT")
    print("=" * 74)
    passed_m1 = middle >= 0.40 and invisible <= 0.25
    passed_m2 = max(gains) / climb < 0.45
    passed_m3 = best_acc >= 0.70
    for name, ok, why in [
        ("M1 populated middle band", passed_m1,
         f"{middle:.0%} at 1-3 cues, {invisible:.0%} undetectable"),
        ("M2 knowledge pays smoothly", passed_m2,
         f"largest jump is {max(gains)/climb:.0%} of the climb"),
        ("M3 genuine vs forgery separable", passed_m3,
         f"ceiling {best_acc:.0%}, {overlap:.0%} ambiguous"),
    ]:
        print(f"  [{'PASS' if ok else 'FAIL'}]  {name:32s}  {why}")
    print()
    print("  The stated kill condition is NOT met." if (passed_m1 and passed_m2 and passed_m3)
          else "  The stated kill condition IS met. Stop.")
    print()
    print("  What this does NOT show: whether a human finds it fun, whether the dossier")
    print("  prose communicates the cues, or whether accuracy climbs for a real player")
    print("  rather than for a detector handed the rules. Those still need the friend and")
    print("  the fifty dossiers. This only establishes that a learnable signal exists to")
    print("  be communicated — which is the part that had to be true first.")
