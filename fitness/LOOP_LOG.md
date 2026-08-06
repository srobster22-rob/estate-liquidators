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

R3 · Built the confidence gate (`sim/confidence.py`) and the experiment that decides
whether it earns its place (`sim/confidence_experiment.py`), plus 13 tests. Target taken
from R2's ranking without deviation. Everything scored in **preparedness points lost**
rather than percent error — R1 named points as the currency, and the preparedness curve
is asymmetric, so every percent-error table in this project had been quietly treating a
20% overshoot and a 20% undershoot as the same mistake.

· **R2's fitter, shipped ungated, would have been actively harmful.** At 8 weeks of logs
an ungated personalised prescription costs **100.4 points** against the population
prior's **19.97** — five times worse than ignoring the lifter entirely — with a p90 of
**248**. That is the population most likely to install a training app, getting worse
advice than a printed template, for their first two mesocycles.

· **Found the threshold is not where R2 put it.** Sampling only 12 and 24 weeks made the
transition look like a cliff between them; resolving it week by week puts the collapse
between **16 and 18 weeks** — mean loss 19.4 at week 14, 10.3 at 16, **0.88 at 18**, a
factor of twelve across two weeks. Break-even with the prior arrives at 14. This is
earlier than the ~24 weeks R2 inferred from percent MRV error, and the disagreement is
the point: the two metrics rank the same fits differently, and points is the one a lifter
experiences. D-02 amended, D-13 supersedes its number.

· **The principled gate lost to the crude one, and the reason generalises.** The
empirical-Bayes shrinkage — no tunable thresholds, weight `tau^2/(tau^2 + s^2)` from a
residual bootstrap — beats ungated fitting everywhere and costs nothing after the
threshold, but it **loses to a plain week count**: 30.2 points against 19.97 at 8 weeks,
22.0 against 19.97 at 12. **A bootstrap measures precision, not accuracy.** Resampling
residuals around a badly-wrong fit tells you how reproducible that wrong answer is, not
how wrong it is, so a confidently-wrong fit sails through. The weights table shows it
happening: mean trust at 8 weeks is 0.50 for a normal mesocycle and 0.68 for a varied
one, extended to fits off by 100 points. Self-reported uncertainty under-shrinks exactly
the lifters who most need shrinking. D-14.

· Of the four candidate signals, `residual_rmse` is **useless** — rank correlation with
realised error runs −0.23 to +0.21 and the sign is not stable. The gate that ships is
keyed on weeks of logged varied history: the cheapest signal available, knowable before
the lifter trains, and it beat a twelve-draw bootstrap.

· **Caught a fabricated result before it printed.** The Spearman implementation broke
ties by index, which invents an ordering out of nothing — so `weeks_logged`, constant
within a run, would have come back with a real-looking correlation instead of the
undefined it actually is. Caught by the round's own test suite while the experiment that
would have published the fabricated numbers was still running. Fixed with average ranks
and re-run from scratch.

· Logged D-15 against the round's own foundation: every threshold here is calibrated on
synthetic lifters drawn from the model's own prior and simulated by the model that then
fits them. The *relative* results (fitter beats null, gate beats ungated, crude beats
sophisticated) survive misspecification; the specific week counts do not, and expect real
data to push them later rather than earlier.

---

## Next round (paste `ITERATION-PROMPT.md` to resume)

**R4: fix the trigger properly (D-07).** Promoted after two rounds as runner-up, and now
it is both the oldest open item and the cheapest it will ever be. R1 established that any
trigger reading "am I getting worse" is a lagging indicator with lag on the order of
`tau_fit` — it fired spuriously in week 3 and then missed a 46% overshoot of MRV entirely.
A working trigger has to watch the **derivative of response with respect to dose**: the
last volume increment bought less than the one before. R2 and R3 built exactly the
machinery that needs — a fitted response curve is an estimate of its slope, and the gate
already says when that estimate can be trusted. Score it the way R3 scored everything, in
preparedness points against a policy that just sits at the fitted MRV, and be ready for
the answer to be "sitting at the fitted MRV is fine and the trigger buys nothing", which
would be consistent with D-06 and worth knowing.

**Runner-up: the volume-matched deload sweep (D-06).** Third on the last two rankings and
still unstarted, which is itself a signal — it keeps losing to things that turned out to
matter more. D-06 rests on a comparison where the winning policies did 45–70% of the work
of the losing one. Re-run holding total sets constant, with D-12's methodology (24+
lifters, common random numbers). Cheap, and it either hardens a FIRM decision or reveals
it was wrong for an embarrassing reason.

**Third: profile likelihood instead of a bootstrap (D-13's falsification condition).**
D-14 argues a resampling method *cannot* beat a week count because it never sees the
truth, but a curvature-based interval might, because a flat loss surface is observable
without knowing the answer. This is the named way to prove D-13 wrong, it is one
experiment, and the machinery is already there.

**Fourth, cheap: the deep-deload excitation test (D-11).** Does deepening the deload in a
normal mesocycle close the 0.94 → 0.98 identifiability gap, and — now more interesting —
does it move R3's 18-week threshold earlier? Every week shaved off that threshold is a
week of real users getting their own prescription instead of the prior.

**Also still open:** D-05 (frequency preference is an artefact of attaching saturation per
session), and the D-04 ceiling-vs-published-MRV discrepancy, which may just be a
set-counting convention. Both cheap, neither blocking.

**Blocked on nothing — but note D-15.** Every threshold this project has produced is
calibrated on lifters the model invented. The relative comparisons hold; the numbers want
real logs before anyone quotes them to a person.
