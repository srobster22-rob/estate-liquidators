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

**Rounds 1–5 complete.** The core model exists and is tested (77 tests,
`fitness/tests/`). Each round has overturned something the previous one established: R1
found the model could not represent volume at all (§3), R2 found the fitter needs three
times more data than the project was designed around (§4.1), R3 found the fitter is
*harmful* if used before that threshold and that a crude gate beats a principled one
(§4.2), and R4 found that the flatness of the objective explains why crude keeps winning
— and corrected R1's headline number by a third (§4.3, D-16).

The premise survives. Per-lifter fitting works, correlates 0.98 with truth on an
informative history, and holds still — 3–6% week-to-week swing, inside the 20% threshold
D-08 set in advance.

What R4 and R5 together establish about where effort should go: control and starting
information **substitute for each other** rather than compounding, and neither closes more
than about 40% of the gap to an oracle. A covariate would need to correlate ~0.5 with true
MRV to be worth what the whole controller stack is worth (§4.4).

**The simulation-only phase is close to finished.** Five rounds have taken achievable loss
from ~15 points (prescribe a constant) to ~10, against an oracle at 0, and every remaining
number is calibrated on lifters the model invented (D-15). What the project needs next is
real logged data, not another round of this.

Not built yet: the volume budget across muscle groups, the autoregulation controller, the
logger. Ranked in `LOOP_LOG.md`.

---

## 2. The five ideas everything else hangs off

1. **Fit the lifter, don't apply the template.** Two-trace impulse-response with four
   free parameters, fit per lifter from their own logs. The population spread in the
   one number that matters most — maximum recoverable volume — is **5.8x from p10 to
   p90** (§4; R1 reported 8.9x, corrected in R4 — see D-16). No template survives that. R2 confirmed the fit is findable (correlation
   0.98) and stable (3–6% week-to-week), at a cost: it needs ~24 weeks of *varied*
   training before it can be trusted (§4.1).

2. **Volume is spent, not scheduled.** Weekly sets are a budget allocated across muscle
   groups against diminishing returns, not a number copied off a spreadsheet.

3. **Autoregulation is a control loop, not a vibe.** RIR feedback drives load through a
   proportional controller with an explicit, tuned gain — a number that can be wrong and
   therefore a number that can be improved.

4. **The mesocycle is a search, not a ritual.** The ramp exists to *find* your MRV; the
   deload is what it costs to overshoot it. R2 gave this a second job: the variation is
   also the **excitation signal** that makes you identifiable at all. A lifter who trains
   the same amount every week produces a log that barely identifies them — correlation
   0.45 against 0.94 for a normal waved mesocycle (§4.1). An unvarying plan is an
   uninformative experiment.

5. **Every recommendation states its confidence.** Below the identifiability threshold
   the app says "population prior, not your data" out loud, in the UI, every time. R2
   made this a release requirement rather than a nicety: the median fit is good and the
   p90 fit is off by 34–148%, so a confident number is unsafe for a tenth of users
   (§4.1).

**And one principle R4 added, which is really a rule about where not to spend effort:**
**the optimum is flat, so precision is nearly worthless and avoiding gross error is
nearly everything.** Being 25% off a lifter's MRV costs 1.8 preparedness points; being
100% off costs 22. Any proposal that only sharpens an already-reasonable answer is
declined by default (§4.3).

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
| p10 | 8.9 |
| median | 26.4 |
| p90 | 51.3 |
| **p90/p10** | **5.76x** |

**These numbers were corrected in R4.** R1 reported 5.8 / 25.4 / 51.3 and a spread of
**8.86x**, which included 4.5% of the synthetic population who have no interior optimum
at all — lifters the model tells never to train, for whom `mrv()` was silently returning
the lower bound of its own search interval. Excluding them gives the figures above. The
argument is unchanged and the number was inflated by a third. D-16.

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

## 4.1 Can the fit actually be found? (R2)

Four parameters (`k_fit`, `k_fat`, `tau_fit`, `tau_fat`), fitted by least squares against
one weekly performance test, corrupted by 2.5 points of measurement noise. `p0` is fixed
at 100 by construction: measurements are a percentage of a baseline test, so the baseline
is a definition, not an unknown. Constraints are enforced by reparameterisation, so the
optimiser never walks into an invalid region. `sim/fit.py`.

**Yes, and it beats its null decisively.** Across 24 lifters on a 16-week history:

| History | Median MRV error | p90 | Correlation with truth |
|---|---|---|---|
| FLAT — 18 sets/wk, every week | 38.5% | 317.9% | **0.45** |
| WAVED — normal ramp-and-deload mesocycle | 17.7% | 77.8% | **0.94** |
| PROBE — deliberately varied volume | 16.0% | 34.3% | **0.98** |
| *always prescribe the population prior* | 58.9% | 779.0% | 0.00 |
| *always prescribe the population median* | 59.9% | 508.1% | 0.00 |

The two constant baselines are the honest null: a fitter that quietly returns its
starting point would be perfectly stable and perfectly useless, and would score exactly
like them. It doesn't.

**Stability — D-08, the named failure mode — did not occur.** Refitting after each new
week from week 8 to week 24 moves the prescribed volume by a median of **3.4% (PROBE)**
to **5.7% (WAVED)**, against the 20% threshold written down in advance. Combined with
the 0.98 correlation, that is real stability rather than a stuck optimiser.

### The plan you run decides what you can learn from it

Look at the FLAT row. A lifter who trains the same amount every week produces a log that
**barely identifies them at all** — correlation 0.45, median error 38.5%. Not because
they trained badly, but because a constant input excites two exponential traces in
lockstep, and nothing in the response separates them.

This gives idea 4 a second job. The mesocycle's variation was justified in §5 as a search
for MRV. It is *also* the excitation signal that makes the lifter identifiable. **A
comfortable, unvarying plan is an uninformative experiment**, and a planner that
prescribes one is sabotaging its own next prescription.

Unresolved and important: PROBE is a good excitation signal and an unpleasant training
plan (alternating 8 and 36 sets). WAVED gets 0.94 for free out of a plan people would
actually run. **The remaining gap between 0.94 and 0.98 is probably not worth any
training-quality cost at all** — which suggests the right design is a normal mesocycle
with a deliberate variation floor, not a plan optimised for identifiability. Not settled.
D-11.

### It needs far more data than this project assumed

| Weeks logged | Median MRV error | p90 |
|---|---|---|
| 8 | 26.4% | **1328.6%** |
| 16 | 20.0% | 148.4% |
| 24 | 8.6% | 94.5% |
| 52 | 4.5% | 36.4% |

D-02 chose two traces over three specifically because "four parameters are recoverable
from ~20 sessions". **That premise is false.** At 8 weeks the median lifter gets a 26%
error and the p90 lifter gets a prescription off by more than a factor of thirteen. The
fit is not trustworthy until roughly **24 weeks** of varied training.

D-02's *conclusion* survives, and is strengthened: freeing the saturation ceiling as a
fifth parameter triples the median error (5.9% → 18.7% on PROBE) and blows the p90 out to
759%. Four is already more than the data comfortably supports. Five is fantasy.

### The tail is the safety problem, not the median

Every row above has a median that reads fine and a p90 that does not. Even the best
configuration at 16 weeks leaves a tenth of lifters with a 34% error, and the worst-case
lifter in an earlier run was off by ~400%.

**A planner that is excellent for most people and four times wrong for some must not
present a confident number to anyone.** This turns idea 5 from a nice-to-have into a
release requirement: below the data threshold, the app says "population prior, not your
data" and prescribes conservatively. What the confidence gate is actually keyed on —
weeks logged, volume variation in those weeks, residual scale, or a bootstrap over the
fit — is R3's job.

### Methodological caveat, stated plainly

Median MRV error for the same configuration came out as 5.9%, 14.1%, 16.0% and 20.0%
across four experiments that differed only in which synthetic lifters they drew.
**Small-population medians in this project swing by a factor of three.** The 24-lifter
numbers are quoted as canonical above; anything from a run of 6–12 lifters is
directional at best. Larger populations, or common random numbers across arms, before any
number here is treated as measured. D-12.

---

## 4.2 The confidence gate (R3)

R2 left a fitter that is excellent for most lifters and dangerous for some. §4.1 said
nothing should present a confident number until something can tell which case it is in.
This is that something — and it did not work the way it was supposed to.

Everything below is scored in **preparedness points lost** against prescribing the
lifter's true optimum, not percent error. Points because R1 established them as the
currency, and because the preparedness curve is **asymmetric** — overshooting MRV costs
far more than undershooting it, which every percent-error table in this project had been
hiding. `sim/confidence.py`, `sim/confidence_experiment.py`.

### Ungated fitting is worse than not personalising at all, and it is not close

Mean points lost, 24 lifters, paired (same lifters, same noise, every policy):

| History | Weeks | PRIOR | FITTED | HARD | SHRUNK |
|---|---|---|---|---|---|
| WAVED | 8 | 19.97 | **100.37** | 19.97 | 30.22 |
| WAVED | 12 | 19.97 | **44.40** | 19.97 | 22.03 |
| WAVED | 24 | 19.97 | 0.53 | 0.53 | 0.51 |
| WAVED | 52 | 19.97 | 0.14 | 0.14 | 0.14 |
| PROBE | 8 | 19.97 | 42.25 | 19.97 | 25.86 |
| PROBE | 24 | 19.97 | 0.17 | 0.17 | 0.17 |

At 8 weeks, an ungated personalised prescription costs **five times more** than ignoring
the lifter entirely and prescribing the population prior. The p90 lifter loses **248
points**. R2's fitter, shipped as-is, would have been actively harmful to everyone in
their first two mesocycles — which is exactly the population most likely to install
something like this.

### Where the threshold actually is

Sampling only 12 and 24 weeks made this look like a cliff between them. It is a cliff,
but not there:

| Weeks (WAVED) | 8 | 10 | 12 | 14 | 16 | **18** | 20 | 22 | 24 | 28 |
|---|---|---|---|---|---|---|---|---|---|---|
| FITTED mean loss | 100.4 | 45.2 | 44.4 | 19.4 | 10.3 | **0.88** | 1.18 | 1.48 | 0.53 | 0.27 |
| FITTED p90 loss | 248.5 | 195.1 | 174.6 | 17.4 | 15.8 | **1.17** | 2.95 | 3.23 | 1.31 | 0.62 |

**The transition is between weeks 16 and 18**, and it is abrupt — a factor of twelve in
the mean and thirteen in the p90 across two weeks. Fitting reaches break-even with the
prior at **14 weeks** and is essentially free from **18**.

This is earlier than the ~24 weeks R2 inferred from percent MRV error, and the
disagreement is instructive: percent error treats a 20% overshoot and a 20% undershoot
as the same mistake, and they are not. **The two metrics disagree about when the fit
becomes usable, and points is the one a lifter experiences.** The 20–22 week bump back up
to 1.18 and 1.48 is sampling noise at n=24, per D-12; do not read a dip into it.

### The principled gate loses to the crude one

Four candidate signals were tested. Only two are real:

| Signal | Verdict |
|---|---|
| `weeks_logged` | **Wins.** Free, knowable before the lifter trains, and the table above is its calibration curve. |
| `volume_variation` | Real but coarse; sets how *fast* the threshold arrives (D-10), not whether. |
| `residual_rmse` | **Useless.** Rank correlation with realised error runs −0.23 to +0.21 — the sign is not even stable. |
| `bootstrap_rel_sd` | Weakly useful (0.25–0.67 on informative histories, −0.12 on a flat one) and not enough. |

The empirical-Bayes shrinkage built on the bootstrap — no tunable thresholds, weight
`w = tau²/(tau² + s²)` — beats ungated fitting everywhere before the cliff and costs
nothing after. It still **loses to the crude rule.** At 8 weeks: HARD 19.97, SHRUNK
30.22. At 12: HARD 19.97, SHRUNK 22.03.

**Why, and this is the finding worth keeping: a bootstrap measures precision, not
accuracy.** Resampling residuals around a badly-wrong fit tells you how *reproducible*
that wrong answer is, not how wrong it is. A confidently-wrong fit has a small bootstrap
spread and sails through the gate. The weights table shows it happening — mean `w` at 8
weeks is **0.50** for WAVED and **0.68** for PROBE, meaning the gate extends half to
two-thirds of its trust to fits that are off by 100 points. Self-reported uncertainty
systematically under-shrinks exactly the lifters who most need shrinking.

### The rule that ships

```
weeks of logged, varied training     prescription
  < 14                               population prior, labelled as such
  14 – 18                            shrunk toward the prior (SHRUNK beats PRIOR here:
                                     13.2 vs 20.0 at week 14)
  > 18                               the fit, with the residual caveat below
```

The gate is keyed on **history**, not on the model's opinion of itself. That is the
cheapest signal available, it is knowable in advance, and it beat a twelve-draw bootstrap.

**Residual caveat, unresolved:** this rule is calibrated on synthetic lifters generated
by the same model that fits them. Real lifters are not drawn from `PRIOR_SPREAD`, and
every threshold above inherits that. D-15.

---

## 4.3 The dose-derivative controller, and why the peak being flat explains everything (R4)

D-07 has been open since R1: every trigger this project tried read "am I getting worse",
which lags by ~`tau_fit`. R4 built the replacement — a controller that watches the
**marginal return on the next set** and steps volume in whichever direction it points,
never estimating MRV at all. `sim/trigger.py`.

**The hypothesis was right.** Getting a slope's sign right is a strictly easier problem
than locating an argmax, and the data says so:

| Weeks | Sign correct below MRV | Sign correct above | Median MRV error |
|---|---|---|---|
| 8 | 71% | 58% | 66.6% |
| 12 | **96%** | 88% | 21.9% |
| 16 | 100% | 88% | 17.5% |
| 18 | 100% | 96% | 6.3% |

At week 12 the direction is known 96% of the time while the location is still 22% wrong.

**And it bought almost nothing.** Mean preparedness points lost over a 24-week block, 24
lifters, paired:

| Policy | Mean | p90 | Worst |
|---|---|---|---|
| ORACLE (knows the truth) | 0.00 | 0.00 | 0.00 |
| PRIOR-FIXED | 19.97 | 49.94 | 94.33 |
| GATED (R3's rule) | 15.12 | 37.46 | 70.74 |
| **LEVEL-TRIGGER (R1's broken one)** | **14.93** | 38.83 | 52.36 |
| HILL-CLIMB | 15.20 | 48.37 | 117.64 |
| HILL-CLIMB + gate@12 | **14.23** | 33.12 | 82.22 |
| HILL-CLIMB + gate@8 + dither | 15.35 | **25.31** | 94.57 |

The new mechanism **loses to the broken one it was built to replace** (15.20 vs 14.93),
and its worst case is more than twice as bad. Gating it on R3's threshold recovers the
lead — 14.23, the best mean anything has scored — but look at the spread: every policy
that reads data at all lands between **14.2 and 15.5**, while the oracle is at 0. Roughly
**14 of the 20 available points are not captured by any control policy**, and the
difference between the best and worst controller is under 1.3.

### Why: the peak is flat, and that explains three rounds at once

Points lost by prescribing a given multiple of a lifter's true MRV:

| Off by | ×0.75 | ×0.9 | ×1.0 | ×1.1 | ×1.25 | ×1.5 | ×2.0 |
|---|---|---|---|---|---|---|---|
| Points lost (pop. mean) | 2.11 | 0.32 | 0.00 | 0.30 | 1.78 | 6.52 | **22.36** |

**Being 25% wrong costs 1.8 points. Being 100% wrong costs 22.** The ratio is roughly
**12:1** — essentially all of the available value is in avoiding gross error, and almost
none of it is in precision.

This is the single explanation for every "crude beats principled" result in the project:

- **D-06** — deload cadence worth under 1 point while overshooting MRV cost 13.
- **R3** — a plain week count beat empirical-Bayes shrinkage over a bootstrap.
- **R4** — a broken level trigger beat a correct dose-derivative controller.

None of these were surprises about training. They are the same fact about the objective,
observed three times: **a quadratically flat optimum pays nothing for precision.** The
corollary is a rule for future rounds — *anything that only improves accuracy near the
peak is not worth a round*, and the burden is on any proposal to show it prevents gross
error rather than refining a good answer.

### Where the missing 14 points actually are

Rank correlation between a lifter's distance from the population prior and the points
they lose under the best controller: **0.89**. Splitting the population in half by that
distance:

- 12 lifters closest to the prior: mean loss **3.99**
- 12 lifters farthest: mean loss **25.26**
- Share of all loss from the far half: **86%**

The remaining loss is not a control problem and no controller will fix it. It is
concentrated in the minority whose true MRV is far from where everyone starts, during the
weeks before anything can know they are unusual. **The lever is a better starting point —
a prior stratified on something observable before the first session — not a better
controller.** That is R5.

### The one clearly positive result

A small deliberate wobble in prescribed volume is **free and cuts the tail by 30%**: p90
loss drops from 48.4 to 33.6 at a dither of ±10%, with mean loss slightly *better* (16.21
vs 16.76) and convergence marginally faster (median 16 weeks vs 17.5). This is D-10's
excitation argument paying off in closed loop — a controller that has converged stops
varying, which slowly blinds the fit it depends on, and the wobble prevents that at no
cost. Step size is not knife-edge either (16.8–19.5 points across 0.05–0.30), so nothing
here rests on a tuned constant.

---

## 4.4 The starting prior, and what a covariate would have to be worth (R5)

R4 left one lever: start closer to the lifter. R5 measured what that is worth — and had
to avoid an obvious trap to do it. MESO's synthetic lifters **have no covariates**; sex,
training age and bodyweight do not exist in `PRIOR_SPREAD`. Any experiment that invents
one, wires it to the truth, and reports how much it helps is measuring its own wiring.

So the question asked is the one that can be answered honestly: **how good would a
covariate have to be, in correlation terms, before it is worth collecting?** That is a
property of the loss surface and the population spread, both real properties of the
model, and it yields a threshold a real questionnaire can later be measured against.
`sim/prior.py`, `sim/prior_experiment.py`.

### The answer

Covariate correlated `rho` with true log-MRV; prescription is the conditional
expectation. 284 lifters, degenerate cases excluded (see below):

| rho | Mean points lost | p90 | % of the gap to an oracle closed |
|---|---|---|---|
| 0.0 (best constant) | 10.04 | 25.70 | — |
| 0.3 | 8.89 | 22.50 | 12% |
| **0.5** | **7.67** | 20.04 | **24%** |
| 0.7 | 6.18 | 17.18 | 38% |
| 0.9 | 3.56 | 9.47 | 65% |
| 1.0 (oracle) | 0.99 | 1.94 | 90% |

**A covariate needs rho ≈ 0.5 to be worth roughly what R4's entire controller stack is
worth**, and rho ≈ 0.3 to be worth about half of it. Below rho ≈ 0.2 it is not worth the
question on the signup form.

Whether any real measurement clears 0.5 against a lifter's true MRV is **not something
this project can answer and nothing here should be read as claiming it does**. As a
rough calibration: single self-report items in exercise science rarely exceed 0.3–0.4
against objective outcomes, so a composite would probably be needed — **inferred
judgement, not measured, D-20.**

### Covariates and control substitute for each other, they do not compound

| rho | Start only | + R4's controller | What the controller adds |
|---|---|---|---|
| 0.0 | 14.45 | 10.11 | **+4.34** |
| 0.3 | 11.20 | 7.75 | +3.45 |
| 0.5 | 8.74 | 6.08 | +2.67 |
| 0.7 | 6.70 | 4.81 | +1.89 |
| 0.9 | 4.97 | 3.50 | **+1.48** |

The controller's marginal value **falls by two-thirds** as the covariate improves. They
are two routes to the same information — one asks at signup, the other learns over 18
weeks — and buying both pays for one and a bit. That is worth knowing before anyone
budgets for both.

### The "free win" this round opened with was itself an artefact

The first result was that the default prescription used since R1 (30.8 sets/week, the
average lifter's MRV) was not the loss-minimising constant, which looked like 26.9 and a
free 0.65 points. **On a clean population that evaporates**: the optimum is 28.8 and the
gain is 0.16 points. The apparent win was the degenerate lifters below dragging the
optimum down. Retracted in the same round that produced it.

### Degenerate lifters do not just inflate a headline, they break the estimator

D-16 found that ~5% of the synthetic population has no interior optimum, and `mrv()` was
returning its search boundary for them. R5 found what that costs downstream: those
lifters inflate the **SD of log-MRV by 56%** and drag its geometric mean down **19%**.

Any shrinkage estimator built on those moments spreads its prescriptions wider than the
real population does — so in R5's first run, **a better covariate produced worse
prescriptions** across the whole middle of the range (loss rising from 12.55 at rho 0 to
14.98 at rho 0.7, then falling again). Non-monotone, and not a property of anything real.
`population_mrvs` now excludes them by default; the contaminated sweep is kept in the
experiment as a demonstration. D-19.

**This also inflates R3's and R4's absolute figures.** Their 24-lifter population
contained 8% degenerate lifters, which inflates PRIOR-FIXED's loss from 15.15 to 19.97
(1.3x) and the best controller's from 10.29 to 15.14 (1.5x). **Every ordering those
rounds concluded from is preserved** — which is exactly the argument D-15 made for
trusting relative results over absolute ones — but the magnitudes quoted in §4.2 and §4.3
are 30–50% too high.

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
