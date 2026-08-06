# MESO — Design

**A training planner that simulates before it prescribes.**

The plan is a hypothesis. The log is the experiment. Every prescription MESO makes is
generated from a per-lifter parameter set, and every week of logged training re-fits
those parameters, so next week's prescription is derived from *your* measured response
rather than a population average that fits almost nobody.

This document is written to be built from. Where a number is a guess it says so, and
`DECISIONS.md` states what would prove it wrong.

---

## 1. Status

**Round 1 complete.** The core model exists, is tested (24 tests, `fitness/tests/`), and
has already overturned its own founding assumption once — see §3, which is the most
important section in this document.

Not built yet: parameter fitting, the volume budget across muscle groups, the
autoregulation controller, the logger. Ranked in `LOOP_LOG.md`.

---

## 2. The five ideas everything else hangs off

1. **Fit the lifter, don't apply the template.** Two-trace impulse-response with four
   free parameters, fit per lifter from their own logs. The population spread in the
   one number that matters most — maximum recoverable volume — is **8.9x from p10 to
   p90** (§4). No template survives that.

2. **Volume is spent, not scheduled.** Weekly sets are a budget allocated across muscle
   groups against diminishing returns, not a number copied off a spreadsheet.

3. **Autoregulation is a control loop, not a vibe.** RIR feedback drives load through a
   proportional controller with an explicit, tuned gain — a number that can be wrong and
   therefore a number that can be improved.

4. **The mesocycle is a search, not a ritual.** The ramp exists to *find* your MRV; the
   deload is what it costs to overshoot it. This replaces R1's original framing (see §3
   and §5) and is the single most consequential change of the round.

5. **Every recommendation states its confidence.** Below the identifiability threshold
   the app says "population prior, not your data" out loud, in the UI, every time.

---

## 3. The model, and the hole R1 found in it

### 3.1 What the model is

Two exponentially-decaying traces driven by one daily stimulus (`sim/ff_model.py`):

```
fitness[d]      = fitness[d-1] * exp(-1/tau_fit) + stimulus[d-1]
fatigue[d]      = fatigue[d-1] * exp(-1/tau_fat) + sets[d-1]
preparedness[d] = p0 + k_fit * fitness[d] - k_fat * fatigue[d]
```

Today's session cannot improve today's performance. It costs today and pays later. That
asymmetry is the entire model.

| Parameter | Prior | Meaning | Status |
|---|---|---|---|
| `p0` | 100 | baseline, % of current best single | definition |
| `k_fit` | 1.00 | gain on the fitness trace | **inferred** |
| `k_fat` | 1.90 | gain on the fatigue trace | **inferred** |
| `tau_fit` | 42 d | fitness decay constant | **inferred** |
| `tau_fat` | 9 d | fatigue decay constant | **inferred** |

Every one of those is a literature-typical value from **endurance** research. No
resistance-training calibration is claimed. They are priors to be overwritten, and D-01
states what would replace them.

Two structural constraints are enforced in code, not by convention: `tau_fat < tau_fit`
and `k_fat > k_fit`. Violate the first and the model is inert; violate the second and
every session improves performance the instant it ends, which no lifter has ever
experienced.

### 3.2 The hole

**The model as standardly specified has no interior optimum in volume.** At steady state
the two traces converge to `daily * C` where `C = 1/(1 - exp(-1/tau))`, so:

```
preparedness = p0 + daily_work * (k_fit*C_fit - k_fat*C_fat)
             = p0 + daily_work * (42.50 - 18.07)
             = p0 + daily_work * 24.43
```

That bracket is a **constant**, and it is **positive**. Preparedness is linear and
strictly increasing in weekly volume, forever. The model prescribes infinite training.

This is not a tuning problem. The bracket is either positive (train infinitely) or
negative (never train at all) — and in a 200-lifter synthetic population drawn from the
prior spread, **7 lifters land on the negative side**, i.e. the model tells them to never
train. There is no parameter choice that makes it turn over, because the slow trace
integrates over 42 days while the fast one integrates over 9, and both are linear in the
dose.

**Consequence: MRV, MEV, and every deload rationale derived from this model are derived
from nothing.** R1's deload sweep dutifully found that never deloading beats every
deload schedule by 9–17 preparedness points, which was never a fact about training. It
was the model saying "more is better" in the only voice it has.

### 3.3 The fix that works, and the one that doesn't

**Doesn't work — staleness.** Discounting adaptation when the fatigue trace runs high
relative to fitness (`StalenessParams`) is the obvious repair and it fails. Set at a
plausible onset (fatigue/fitness = 0.85) it moves the best policy by **+2.7 points**,
inside noise. To make it bite you have to set the onset so low that *everyone* is
permanently discounted, at which point absolute preparedness collapses from 139 to 87
across the board. It lowers the whole curve instead of bending it. Kept in the codebase,
disabled by default, because it is a useful null result and cheap to re-test.

**Works — saturating stimulus with linear fatigue.** One parameter:

```
stimulus deposited = ceiling * (1 - exp(-sets_this_session / ceiling))
fatigue  deposited = sets_this_session
```

Each set past the first few deposits less adaptation than the one before while
depositing the same fatigue. The form is chosen so the derivative at zero sets is
exactly 1 — low-volume behaviour is untouched, and the saturation only bites where the
dose-response literature says it bites. `ceiling` = 12 set-equivalents per session,
**inferred, D-04**.

This makes the bracket volume-dependent, and the curve turns over:

| Weekly sets | Linear model | Saturating model |
|---|---|---|
| 8 | 127.9 | 122.9 |
| 16 | 155.9 | 137.1 |
| 24 | 183.8 | 144.4 |
| **32** | 211.7 | **146.1 ← optimum** |
| 40 | 239.6 | 143.4 |
| 60 | 309.4 | 122.4 |
| 120 | 518.9 | 1.1 |

**MRV now exists as a model output rather than an assumption.** Prior lifter: **30.8
hard sets per week per muscle group** at 3 sessions/week.

That figure is higher than commonly-cited MRV tables (~20–25). Two readings: either
`ceiling` is too generous, or "hard sets" here are being counted more loosely than those
tables count them. Not resolved. D-04.

---

## 4. Why the plan must be fitted, not templated

Under the corrected model, across 200 synthetic lifters:

| | Weekly sets at optimum |
|---|---|
| p10 | 5.8 |
| median | 25.4 |
| p90 | 51.3 |
| **p90/p10** | **8.86x** |

Prescribing the population median (25 sets/week) to everyone costs:

- the median lifter — **7.4** preparedness points
- the p90 lifter — **35.9**
- the worst-fit lifter — **61.7**

For scale, the entire gap between the best and worst deload policy is ~14 points. **The
cost of not knowing which lifter you are is two to four times larger than the cost of
picking the wrong deload schedule.** Per-lifter fitting is not a nice-to-have feature
sitting alongside good programming; it is the dominant term, and everything else in this
project is rounding error next to it.

That is the finding the whole product should be organised around.

---

## 5. Deloads: what R1 actually established

Under the corrected (saturating) model, over a 20-week block, 40 lifters:

| Policy | Mean prep | Final | Total sets | vs never deloading |
|---|---|---|---|---|
| NONE | 98.8 | 112.8 | 618 | — |
| FIXED-3 | 111.7 | 134.7 | 276 | **+12.9** |
| FIXED-5 | 112.5 | 134.3 | 312 | **+13.7** |
| FIXED-7 | 112.5 | 134.2 | 347 | **+13.7** |
| TRIGGERED | 112.5 | 136.6 | 439 | **+13.6** |

Two things fall out, and the second is the interesting one.

**Deloading beats not deloading by ~13 points.** Note the volume column: the winning
policies did **45–70% of the work** of the losing one. This is not "rest is good", it is
"a ramp that never resets eventually spends every set on fatigue and none on adaptation".

**Which deload schedule you use is worth less than 1 point.** FIXED-3, FIXED-5, FIXED-7
and TRIGGERED land within 0.8 of each other while differing by up to 163 total sets.
**The value is entirely in not chronically overshooting MRV, and not at all in the
cadence.** That kills the premise this round set out to serve — "make deloads triggered
rather than calendared" is optimising a term worth ~0.8 points while the term worth ~36
points (§4) sits untouched.

**The trigger built for this round is broken in both directions, and that is worth
keeping.** Rule: deload when modelled preparedness is below where it was 7 days ago.

- It fires **spuriously in week 3**, on the startup transient, before any real
  accumulation has happened.
- It then **never fires again**, letting volume ramp to 45 sets/week — 46% above the
  prior lifter's MRV — because the slow fitness trace keeps preparedness *rising* for
  many weeks after volume has passed the point where it stops paying.

A performance decline is a lagging indicator of overreaching, with lag on the order of
`tau_fit`. **Any trigger built on "am I getting worse" will always be late.** A trigger
has to be built on the derivative of the response to the *dose* — noticing that the last
increment of volume bought less than the one before — not on the level of the output.
That is R2.

---

## 6. Set accounting

Volume is counted in **hard sets per muscle group per week**. Sets are weighted by
proximity to failure, anchored at RIR 2 = 1.00 because that is the reference
prescription everything else here is written against:

| RIR | Stimulus | Fatigue | Ratio |
|---|---|---|---|
| 0 | 1.05 | 1.55 | 0.68 |
| 1 | 1.02 | 1.22 | 0.84 |
| 2 | 1.00 | 1.00 | 1.00 |
| 3 | 0.93 | 0.84 | 1.11 |
| 4 | 0.82 | 0.70 | 1.17 |
| 5 | 0.67 | 0.57 | 1.18 |

Fatigue rises faster than stimulus as you approach failure. That divergence — not
tradition — is the argument for prescribing RIR 1–3 rather than RIR 0, and it is pinned
by a test so a later round cannot flatten it by accident.

The shape is the consensus reading of the proximity-to-failure literature. **The exact
numbers are a hand-fitted curve, not data.** D-03.

---

## 7. What a week looks like in the model

Training on 3 days makes readiness lumpy: at 24 sets/week the within-week swing in
preparedness is ~10 points, so no two mornings are equally ready. `steady_state()`
returns the weekly **mean**, and comparing it to any single day's value will look broken
when it is correct. This bit R1's own test suite before it bit anyone else.

Open, and unaddressed: whether frequency should be a decision variable rather than a
fixed 3 days. The model currently has no opinion, because saturation is per-session — so
it will mechanically prefer spreading the same weekly volume over more sessions, without
any of the real costs of doing so (warm-up time, travel, adherence). Anyone reading a
frequency recommendation out of the current model would be reading an artefact. D-05.

---

## 8. Scope

**In:** the model, per-lifter fitting, weekly volume allocation, load prescription with
RIR feedback, a logger good enough to produce fittable data.

**Out, deliberately:** nutrition, cardio, exercise selection as an optimisation problem,
anything social, anything with a subscription attached.

**Out, regretfully:** injury hazard. It is a real reason to deload and it is invisible to
a performance model. Where deloads are recommended for safety rather than performance,
this project should say "safety" rather than draw a curve it does not have.
