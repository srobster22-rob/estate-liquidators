# MESO — Loop Log

One entry per round. Newest at the bottom.

Format: `R<n> · <what was built> · <what it found>`

---

R1 · Built the fitness-fatigue core (`sim/ff_model.py`), a deload policy sweep
(`sim/deload_sweep.py`), a volume dose-response experiment (`sim/volume_response.py`),
and a 24-test regression suite (`tests/test_ff_model.py`). Target chosen because
everything else in the project — deload timing, volume budgets, autoregulation gain — is
a query against one dynamical model, and building any of them on an unverified model
means building all of them twice. Runner-up was the logger, rejected because a logger
whose data feeds a wrong model is a wrong logger.

· **Found the model was structurally incapable of the thing the project needs it for.**
The standard two-component impulse-response model has **no interior optimum in volume**.
Its steady-state preparedness is `p0 + daily_work * (k_fit*C_fit - k_fat*C_fat)`, and
that bracket is a *constant* — +24.43 for the prior lifter. Preparedness is linear and
strictly increasing in weekly sets, forever, so the model prescribes infinite training
and cannot represent MRV, MEV, or any reason to deload. Not a tuning problem: the
bracket is either positive (train infinitely) or negative (never train), and 7 of 200
synthetic lifters drawn from the prior spread landed on the *negative* side. The deload
sweep's initial result — never deloading beats every schedule by 9–17 points — was
therefore not a fact about training; it was the model saying "more is better" in the
only voice it has.

· Tried the obvious repair first and it failed: discounting adaptation under chronic
fatigue (`StalenessParams`) is worth **+2.7 points** at a plausible onset, and only bites
when set so low that everyone is permanently discounted, collapsing absolute
preparedness from 139 to 87 across the board. It lowers the curve instead of bending it.
Kept in the code, disabled, as a cheap-to-re-run null result.

· The repair that works is **saturating stimulus with linear fatigue** — one parameter,
derivative 1 at the origin, so low-volume behaviour is untouched. The curve turns over,
and MRV becomes a model *output*: **30.8 sets/week/muscle group** for the prior lifter.
That is above commonly-cited tables (~20–25), which is either a wrong `ceiling` or a
set-counting convention mismatch. Unresolved, D-04.

· **The finding that should reorganise the project:** population MRV spread is **8.86x**
from p10 (5.8 sets/wk) to p90 (51.3). Prescribing the population median costs the median
lifter 7.4 preparedness points, the p90 lifter 35.9, and the worst-fit lifter 61.7. For
scale, the entire gap between the best and worst deload policy is ~14 points, and the
gap between deload *cadences* is under 1. **The cost of not knowing which lifter you are
is 2–4x larger than the cost of every programming decision this round set out to
optimise.** Per-lifter fitting is the dominant term; everything else is rounding error.

· Under the corrected model deloading finally pays — +12.9 to +13.7 points, while doing
**45–70% of the total work** of the never-deload policy. But FIXED-3, FIXED-5, FIXED-7
and TRIGGERED land within **0.8 points** of each other across a 163-set spread in total
volume. The value is entirely in not chronically overshooting MRV and not at all in the
cadence, which kills the round's original premise ("make deloads triggered rather than
calendared"). Logged as D-06, with the honest caveat that the comparison is confounded
by unequal total volume.

· **The trigger built for the round is broken in both directions, and the reason is
structural.** It fires spuriously in week 3 on the startup transient, then never fires
again while volume ramps to 45 sets/week — 46% past MRV — because the fitness trace
integrates over ~42 days and keeps preparedness *rising* long after the marginal set has
stopped paying. Any trigger reading "am I getting worse" is a lagging indicator with lag
on the order of `tau_fit`. D-07.

· Two bugs caught by the round's own test suite rather than by a later round: the
population sampler constructed `FFParams` before validating them, so it raised instead of
rejecting; and the closed-form `steady_state` was being compared against a single day's
simulated value when it is a **weekly mean** — a 3-day training week swings readiness
~10 points inside the week, so the 2.6-point mismatch was the model being right. Fixed
the comparison, not the tolerance, and pinned the swing with its own test.

R2 · Built the per-lifter fitter (`sim/fit.py` — reparameterised four-parameter least
squares, multi-start Nelder-Mead, all pure stdlib) and the experiment suite that decides
whether it deserves to exist (`sim/fit_experiment.py`), plus 12 more tests. Target taken
from R1's ranking without deviation: fitting is the dominant term (~36 preparedness
points against ~13 for deloading), and D-08 named its instability as the most likely way
the project dies, so it had to be measured before anything was built on top of it.

· **D-08 passed, and passed the harder second test.** Refitting after each new week from
week 8 to 24 moves the prescribed volume by a median of **3.4–5.7%**, against the 20%
threshold set in advance. But stability alone proves nothing — an optimiser that never
leaves its seed scores 0% swing and is useless — so the round was re-run against the two
constants it has to beat. Always-prescribe-the-prior and always-prescribe-the-median
score **0.00 correlation** with truth and ~59% median error. The fitter scores **0.98
correlation** and 16%. It is genuinely learning the lifter, and holding still while it
does. The premise survives.

· **Found the round's own founding document was wrong.** D-02 chose two traces over three
on the grounds that "four parameters are recoverable from ~20 sessions". They are not. At
8 weeks of logs the median MRV error is **26.4%** and the p90 is **1328%** — a
prescription off by more than a factor of thirteen. Usable accuracy arrives at roughly
**24 weeks** of varied training (8.6%), still improving at 52 (4.5%). The premise is
falsified; the conclusion hardens, because freeing a fifth parameter (D-04's saturation
ceiling) triples median error and blows the p90 to 759%. Four is already at the edge of
what real logs support.

· **The plan you run decides what you can learn from it.** A lifter training the same
volume every week is nearly unidentifiable — correlation **0.45**, 38.5% median error —
because a constant input drives both exponential traces in lockstep and nothing in the
response separates them. A normal waved mesocycle gets **0.94**; a deliberately varied
probe gets **0.98**. This gives the mesocycle a second job it did not have in R1: the
variation is the excitation signal, not just a search for MRV. Logged as D-10, with D-11
taking the 0.94 and declining to optimise training plans for identifiability — the last
0.04 is not worth a plan nobody will follow.

· **The tail is the safety problem, not the median.** Every configuration has a median
that reads fine and a p90 that does not — 34% at best, 148% at 16 weeks, 1328% at 8. A
planner that is excellent for most people and four times wrong for some must not show a
confident number to anyone. That promotes DESIGN idea 5 from a nicety to a release
requirement, and makes the confidence gate R3's target.

· **Caught itself nearly quoting sampling luck as a finding.** The same configuration
produced median errors of 5.9%, 14.1%, 16.0% and 20.0% across four experiments differing
only in which synthetic lifters they drew — a **3x swing from sampling alone**, larger
than most effects being compared. The 5.9% figure was almost the headline. Canonical
numbers are now 24-lifter runs, and paired comparisons want common random numbers. D-12.

· Also fixed a real methodological bug mid-round: the stability experiment initially
re-drew measurement noise on every refit, so it was measuring "how much does the fit move
when the past changes" rather than "when a week is added". Successive refits now see a
growing prefix of one history.

---

## Next round (paste `ITERATION-PROMPT.md` to resume)

**R3: build the confidence gate, because the fit is now known to be unsafe for a tenth
of users.** This is the only thing standing between R2's working fitter and something a
person could act on. Every configuration measured has a median that reads fine and a p90
that does not — 34% error at best, 148% at 16 weeks, 1328% at 8 — and the same lifters
show up twice, once in the error tail and once in the stability tail (28% p90 swing). The
gate has to identify *which* lifters those are, from data available at prescription time,
without knowing the truth. Candidates, in order of how cheap they are to test: weeks
logged (a blunt rule, and D-02 now gives it a number); volume variation actually present
in the log (D-10 says this is the binding constraint, and it is measurable directly);
residual scale from the fit; and a bootstrap or profile-likelihood interval over the
fitted MRV, which is the principled answer and the expensive one. Measure each against
the actual error, and prescribe conservatively — toward the population prior — in
proportion to the uncertainty. Ship no confident number the data does not support.

**Runner-up: fix the trigger properly (D-07), still unbuilt.** A working trigger has to
watch the derivative of response with respect to dose, not the level of the output. It
was runner-up last round too and stays here because R2's fitter is exactly the machinery
it needs — an estimate of the response curve is an estimate of its slope. Cheap now,
expensive before. If R3's gate lands early, this is the natural second half of the round.

**Third: the volume-matched deload sweep (D-06).** Unchanged from R1's ranking and
unstarted. D-06 rests on a comparison where the winning policies did 45-70% of the work
of the losing one. Re-run holding total sets constant, now with D-12's methodology —
24+ lifters, common random numbers across arms.

**Fourth, and newly cheap: the deep-deload excitation test (D-11).** Does deepening the
deload in a normal WAVED mesocycle close most of the 0.94 -> 0.98 identifiability gap?
One experiment, reuses everything R2 built, and it would settle D-11 in either direction.

**Also still open:** D-05 (the model's frequency preference is an artefact of attaching
saturation per session — decide whether frequency is optimised or accepted as a
constraint), and the D-04 ceiling-vs-published-MRV discrepancy, which may just be a
set-counting convention. Both are cheap and neither blocks anything.

**Not blocked on anything.**
