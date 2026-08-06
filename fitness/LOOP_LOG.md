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

---

## Next round (paste `ITERATION-PROMPT.md` to resume)

**R2: build the per-lifter fitter and measure whether it is stable — before building
anything on top of it.** This is the dominant term (§4 of DESIGN.md: ~36 points against
~13 for deloading and ~0.8 for cadence), and D-08 names the way the whole project most
plausibly dies: if re-fitting after each new week swings prescribed volume by more than
~20%, the fit is tracking noise, and a stable template beats a jittery personalisation no
matter which is theoretically better. Measure that first. Four parameters, ~20 sessions,
Nelder-Mead in pure stdlib; feed it synthetic logs from known parameters plus realistic
measurement noise and check parameter recovery *and* week-to-week stability. If recovery
fails, D-02 says the answer is fewer parameters and stronger priors, not a better
optimiser.

**Runner-up, and it is close: fix the trigger properly.** D-07 says a working trigger has
to watch the derivative of response with respect to dose, not the level of the output.
That is a genuinely different mechanism — estimate the marginal return on the last
volume increment and back off when it goes flat — and it is the same shape of problem as
the fitter, so doing the fitter first probably hands it to you.

**Third: the volume-matched deload sweep.** D-06 currently rests on a comparison where
the winning policies did 45–70% of the work of the losing one. Re-run holding total sets
constant. If cadence still doesn't matter, D-06 hardens; if it does, D-06 was wrong for
an embarrassing reason.

**Also open and cheap:** D-05 (the model's frequency preference is an artefact of
attaching saturation per session — decide whether frequency is optimised or accepted as a
constraint, and don't ship a recommendation until it is), and the `ceiling`-vs-published-
MRV discrepancy in D-04, which may just be a set-counting convention.

**Not blocked on anything.**
