"""
Re-derive the conclusions the documents quote from the sims.

`check_drift.py` holds the four implementations to the same CONSTANTS. Nothing held
the design documents to the same CONCLUSIONS - and a conclusion rots more quietly
than a constant, because it lives in prose that still reads fine.

R36 found the shape of the failure in `validate_estate.py`: a script whose output
nothing asserts is not a check. R37 found it again, in the file that answers "is the
contract chain achievable?" - `chain_sim.py` was still running the quota curve that
`ECONOMY.md` 4 replaced eleven rounds earlier, and printing a 1% night four, which is
the finding that CAUSED the replacement, as though it were still the answer.

So: every claim a document makes on a sim's authority is restated here as an
assertion, with the document and section it is quoted in. The sims are seeded per
trial, so this is reproducible rather than statistical - a failure means the model
moved, not that the dice did.

    python sim/check_claims.py           ->  exit 0 if every claim still holds
    python sim/check_claims.py -v        ->  print each claim and what it measured

Requires nothing outside the standard library. Takes about ten seconds.
"""

import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import chain_sim
import curator_attention
import curse_test
import disturbance
import haul_sim
import integrated

VERBOSE = "-v" in sys.argv
stale, claims = [], 0


def claim(where, text, ok, measured):
    """`where` is the document that quotes this conclusion."""
    global claims
    claims += 1
    if not ok:
        stale.append(f"{where}: {text}\n           measures {measured}")
    if VERBOSE:
        print(f"  {'ok  ' if ok else 'STALE'}  {where:<22}{text}\n"
              f"{'':<30}{measured}")


t0 = time.time()

# ---------------------------------------------------------------- the chain
# ECONOMY 4 tabulates a pass rate per night and calls the shape "you can be a
# coward and survive" down to "the apex is not optional". The shape is the claim:
# four nights that get harder, none of them a formality, none of them a wall.
chain_sim._build_quantiles()
rows = chain_sim.chain_trial(crew=4, n=1500)
rates = [r["pass"] for r in rows]
doc = [0.95, 0.73, 0.55, 0.40]
claim("ECONOMY 4", "the calibrated curve produces the tabulated pass rates",
      all(abs(a - b) <= 0.10 for a, b in zip(rates, doc)),
      "  ".join(f"n{i + 1} {r:.0%}" for i, r in enumerate(rates)))
claim("ECONOMY 4", "and every night is harder than the one before it",
      all(a > b for a, b in zip(rates, rates[1:])),
      "  ".join(f"{r:.0%}" for r in rates))

# The same file keeps the curve it replaced, and the reason it replaced it.
old = chain_sim.chain_trial(crew=4, n=1000, quotas=chain_sim.SUPERSEDED_QUOTAS)
claim("ECONOMY 4", "the superseded curve is three formalities and a wall",
      all(r["pass"] > 0.95 for r in old[:3]) and old[3]["pass"] < 0.05,
      "  ".join(f"{r['pass']:.0%}" for r in old))

# D-21 / ECONOMY 3: the apex must be worth its five slots on every night, or the
# thing the whole night builds toward is a trap. It was one, at $1,500-3,000.
with_apex = chain_sim.chain_trial(crew=4, n=800, allow_apex=True)
without = chain_sim.chain_trial(crew=4, n=800, allow_apex=False)
deltas = [a["mean"] / b["mean"] - 1 for a, b in zip(with_apex, without)]
claim("D-21", "the apex pays for its five slots on every night of the chain",
      all(d > 0.03 for d in deltas),
      "  ".join(f"{d:+.0%}" for d in deltas))

# D-18: four. Not six, and not three.
crews = {c: chain_sim.chain_trial(crew=c, n=600)[-1] for c in (3, 4)}
claim("D-18", "a crew of four can move the apex on the last night and three cannot",
      crews[4]["apex"] > 0.95 and crews[3]["apex"] < 0.80,
      f"crew 3 takes it {crews[3]['apex']:.0%}, crew 4 {crews[4]['apex']:.0%}")

# ECONOMY 3 / D-18: labour is a shared pool and a two-man piece costs two of it,
# which is most of why a crew of three is not simply three quarters of a crew of
# four. Without that rule three people haul nearly as much as four.
ratio = crews[3]["mean"] / crews[4]["mean"]
claim("D-18", "two-man pieces cost two haulers, so three people are worth well under four",
      ratio < 0.90, f"crew 3 earns {ratio:.0%} of crew 4")

# ...but only just, and it is worth writing down which way. Halving the labour cost
# of a two-man piece - one hauler instead of two - moves the chain by about two
# points, because what binds a night is TRIPS, not people. ECONOMY 3 justifies the
# two-man band partly on that labour cost; the model can barely see it, and an
# injection that removes the rule entirely does not disturb any claim above.
_saved = chain_sim.CLASS_DATA["two_man"]
chain_sim.CLASS_DATA["two_man"] = (_saved[0], 1, _saved[2], _saved[3])
cheap = chain_sim.chain_trial(crew=3, n=600)[-1]["mean"]
chain_sim.CLASS_DATA["two_man"] = _saved
claim("ECONOMY 3", "labour is not what binds a night - trips are",
      abs(cheap / crews[3]["mean"] - 1) < 0.05,
      f"free labour on two-man pieces is worth {cheap / crews[3]['mean'] - 1:+.1%} to a crew of three")

# ---------------------------------------------------------------- the appraiser
# D-10: the appraiser is dead if ignoring it is correct. haul_sim swept a free loss
# coefficient standing in for noise punishment and landed on 0.50-0.75 as the band
# where the decision is live - ADAPTIVE, neither of the two extremes.
for coef in (0.50, 0.75):
    haul_sim.RISK_COEF = coef
    means = {s: haul_sim.trial(s, n=1500)["mean"]
             for s in ("BLIND", "SCAN_ALL", "ADAPTIVE")}
    best = max(means, key=means.get)
    claim("D-10", f"at loss coefficient {coef} the live answer is ADAPTIVE",
          best == "ADAPTIVE",
          "  ".join(f"{k} {v:,.0f}" for k, v in means.items()))
haul_sim.RISK_COEF = 0.0

# R8 / integrated.py: with the real Disturbance model instead of the stand-in, the
# edge is small and positive, and scanning everything is NOT the play.
means = {s: integrated.trial(s, n=1200)["mean"] for s in ("BLIND", "ADAPTIVE", "SCAN")}
edge = means["ADAPTIVE"] / means["BLIND"] - 1
claim("DESIGN 4.4", "with real noise the appraiser still pays, but only just",
      0.005 < edge < 0.15 and means["ADAPTIVE"] > means["SCAN"],
      f"ADAPTIVE {edge:+.1%} over BLIND, SCAN {means['SCAN'] / means['BLIND'] - 1:+.1%}")

# ---------------------------------------------------------------- curses
# R9: a linear van-side cost cannot balance a x6 multiplier. That finding is what
# D-11's ruin tail exists to answer, so it has to still be true without the tail.
curse_test.RUIN_K = 0.0
takeall = curse_test.trial("TAKE_ALL", 6.0, n=1200)
refuse = curse_test.trial("REFUSE_MALIGNANT", 6.0, n=1200)
claim("D-11", "without a ruin tail, taking every cursed piece is simply correct",
      takeall > refuse * 1.10, f"TAKE_ALL {takeall:,.0f} vs REFUSE {refuse:,.0f}")

# R11 / D-11: with the shipped ruin coefficient the best policy is an INTERIOR cap.
# Not zero (the curse would be inert), not unlimited (it would be free money).
curse_test.RUIN_K = 0.015
caps = {c: curse_test.trial(f"CAP_{c}", 6.0, n=1200) for c in (0, 1, 2, 3, 4)}
caps["TAKE_ALL"] = curse_test.trial("TAKE_ALL", 6.0, n=1200)
best = max(caps, key=caps.get)
claim("D-11", "at the shipped ruin coefficient the best policy is an interior cap",
      best not in (0, "TAKE_ALL"),
      f"best {best}  " + "  ".join(f"{k}:{v:,.0f}" for k, v in caps.items()))
# R11 quotes the position of that optimum, not just its existence: "take two or
# three cursed pieces, then stop". Where it sits is what the fees and the ruin
# exponent are for - drop the fees and it slides outward.
claim("D-11", "and the optimum sits where R11 put it - two or three, then stop",
      best in (2, 3), f"best cap {best}")

# R9's finding, restated as a property of the shipped numbers rather than a story
# about them: a LINEAR van-side cost cannot move a multiplicative decision. Zeroing
# the curse fees entirely leaves the optimum exactly where it was; zeroing the ruin
# tail moves it straight to "take everything". That is the whole argument for
# D-11's tail risk, and it is checkable in four lines.
_fees = dict(curse_test.FEE)
curse_test.FEE = {k: 0.0 for k in _fees}
nofee = max((c for c in (0, 1, 2, 3, 4)),
            key=lambda c: curse_test.trial(f"CAP_{c}", 6.0, n=1200))
curse_test.FEE = _fees
curse_test.RUIN_K = 0.0
notail = {c: curse_test.trial(f"CAP_{c}", 6.0, n=1200) for c in (0, 1, 2, 3, 4)}
notail["TAKE_ALL"] = curse_test.trial("TAKE_ALL", 6.0, n=1200)
claim("D-11", "the fees cannot move that optimum and the ruin tail is the only thing that can",
      nofee == best and max(notail, key=notail.get) == "TAKE_ALL",
      f"best cap {nofee} with no fees at all, {max(notail, key=notail.get)} with no ruin tail")

# ---------------------------------------------------------------- the night
# DESIGN 6.5 is the pacing spine: escalation has to ARRIVE, and the levers have to
# be worth pulling. A night that reaches COLLECT in minute one is a panic; one that
# reaches it in minute eleven of twelve never escalated at all.
def night_medians(**kw):
    """Median minute at which a night first crosses PURSUE and COLLECT, the median
    Disturbance it ends on, and the fraction of the night spent at COLLECT."""
    P, C, ends, above = [], [], [], 0.0
    for s in range(200):
        curve, p, c, _ = disturbance.run_night(seed=s, **kw)
        P.append((p if p is not None else disturbance.NIGHT_S) / 60.0)
        C.append((c if c is not None else disturbance.NIGHT_S) / 60.0)
        ends.append(curve[-1])
        above += sum(1 for x in curve if x >= 85) / len(curve)
    P.sort(); C.sort(); ends.sort()
    return P[len(P) // 2], C[len(C) // 2], ends[len(ends) // 2], above / 200

pursue, collect, end_d, at_collect = night_medians()
claim("DESIGN 6.5", "a normal night reaches PURSUE early and COLLECT in the middle",
      pursue < 2.5 and 2.0 < collect < 6.0,
      f"PURSUE at {pursue:.1f} min, COLLECT at {collect:.1f} min, ends at {end_d:.0f}")

# DESIGN 6.5 prices lighting a wing at +25 and calls it silent but expensive. The
# price is paid in time spent at COLLECT, not in when COLLECT first arrives.
#
# Only the FIRST lit wing is measurable here, and that is a finding rather than a
# tolerance: the lever policy turns a wing back off as soon as Disturbance passes
# 78, so a second one is never simultaneously lit, and with the levers off the
# night saturates at the 100 ceiling where nothing extra can register. Beyond one
# wing this model has nothing to say, and neither does this check.
_, _, _, dark = night_medians(light_wings=0)
_, _, _, lit = night_medians(light_wings=1)
claim("DESIGN 6.5", "lighting a wing is silent and expensive - it buys time at COLLECT",
      lit > dark * 1.25,
      f"{lit:.1%} of the night at COLLECT with a wing lit, {dark:.1%} with none")

_, nolev_collect, nolev_end, _ = night_medians(use_levers=False)
claim("DESIGN 6.5", "and the levers are worth pulling - without them it arrives sooner",
      nolev_collect < collect - 0.5 and nolev_end > end_d,
      f"COLLECT at {nolev_collect:.1f} min and ends at {nolev_end:.0f} with no levers, "
      f"{collect:.1f} min and {end_d:.0f} with them")

# ---------------------------------------------------------------- attention
# TECH-SPEC A3's three constants pull against each other. The claims are: hysteresis
# stops the flicker, the override makes the hot potato instant, and the richest
# carrier is the one being hunted.
none = curator_attention.scenario_flicker(1.0, 0.0)
spec = curator_attention.scenario_flicker(1.25, 8.0)
claim("TECH-SPEC A3", "the spec's hysteresis removes most of the target flicker",
      spec < none * 0.45, f"{none:.1f} switches unhysteresised, {spec:.1f} with the spec")

on, lat_on = curator_attention.scenario_handoff(True, trials=400)
off, lat_off = curator_attention.scenario_handoff(False, trials=400)
claim("D-25", "the hot potato always works, and is instant only with the override",
      on > 0.99 and lat_on < 0.1 and lat_off > lat_on,
      f"override {on:.0%} at {lat_on:.1f}s, without {off:.0%} at {lat_off:.1f}s")

rich = curator_attention.scenario_richest(trials=600)
claim("TECH-SPEC A3", "the richest carrier is the one being hunted",
      rich > 0.95, f"correct target {rich:.0%} of the time")

# ---------------------------------------------------------------- report
print(f"CLAIM CHECK  -  {claims} documented conclusions re-derived "
      f"({time.time() - t0:.0f}s)")
print("-" * 74)
if not stale:
    print("  OK   every conclusion the documents quote is still what the model produces")
    sys.exit(0)
for f in stale:
    print(f"  STALE  {f}")
print(f"\n{len(stale)} claim(s) the sims no longer support. Fix the document or the model -"
      f"\nand if the model moved on purpose, the document is the thing that is wrong.")
sys.exit(1)
