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

R4 · Built the dose-derivative controller D-07 had been asking for since R1
(`sim/trigger.py`, `sim/trigger_experiment.py`) plus 16 tests. Target taken from R3's
ranking without deviation. The framing that made it worth a round: R3 established the fit
cannot locate MRV for 18 weeks, but locating an argmax is a strictly harder problem than
getting a slope's sign right — so if the sign is reliable early, a hill-climbing
controller fills exactly the gap R3 opened.

· **The hypothesis was right and it bought almost nothing.** Sign of the marginal return
is correct **96%** of the time at week 12, when the MRV estimate is still 22% wrong —
direction genuinely is the easier question. But in closed loop over 24 weeks the new
controller scored **15.20** mean points lost against R1's **broken** level trigger's
**14.93**, with a worst case more than twice as bad (117.6 vs 52.4). Gating it on R3's
threshold takes the lead at **14.23**, the best number anything has scored — and the
entire field, from the broken trigger to the gated controller, spans **14.2 to 15.5**
against an oracle at 0. **Roughly 14 of the 20 available points are captured by no
control policy at all.** D-07 resolved and the line of work retired.

· **Found the explanation for three rounds of results at once.** The objective is flat
near its peak: being 25% off a lifter's true MRV costs **1.78** points, being 100% off
costs **22.36** — a ratio of about **12:1**. Essentially all the available value is in
avoiding gross error and almost none is in precision. That is why deload cadence was
worth under a point (D-06), why a plain week count beat empirical-Bayes shrinkage over a
bootstrap (R3), and why a broken trigger beat a correct controller (R4). Three
sophisticated methods beaten by crude ones, one cause. Promoted to D-17 as a prospective
rule — *anything that only improves accuracy near the peak is not worth a round* — so the
project stops rediscovering it.

· **Located the missing points, and they are not a control problem.** Rank correlation
between a lifter's distance from the population prior and the points they lose is
**0.89**. The half of the population farthest from the prior carries **86% of all loss**
(mean 25.3 against 4.0 for the near half). No controller can help them until something
knows they are unusual, which makes a **better starting prior** the next lever rather than
a better controller. That is R5.

· **Corrected R1's headline number, which had been wrong for four rounds.** A test written
for an unrelated reason asserted the marginal return is positive below MRV, and it failed:
4.5% of the synthetic population has no interior optimum at all — lifters the model tells
never to train — for whom `mrv()` was silently returning the lower bound of its own search
interval. They were inside every population since R1, inflating the reported MRV spread
from a true **5.76x** to the **8.86x** quoted in the README, in DESIGN idea 1, and in three
commit messages. The argument survives (5.8x still defeats any template); the number was
inflated by a third. `has_interior_optimum()` makes the case detectable, pinned by a test.
D-16.

· **The one clearly positive result:** a ±10% dither in prescribed volume is free and cuts
the tail by 30% — p90 loss 33.62 against 48.37, mean slightly better, convergence
marginally faster. This is D-10's excitation argument paying off in closed loop: a
converged controller stops varying and slowly blinds the fit it depends on, and the wobble
prevents that at a cost D-17 makes negligible. D-18.

· Caught and fixed a self-inflicted measurement artefact: convergence was scored on the
controller's dithered prescription rather than its centre, so any dither wider than the
15% tolerance read as "never converges" by construction — the dithered controller was
reported at 25% convergence and is actually at 92%, marginally *faster* than undithered.
Both behaviours are now pinned by tests so the distinction cannot be quietly lost again.

R5 · Built the starting prior and the covariate sensitivity analysis (`sim/prior.py`,
`sim/prior_experiment.py`) plus 12 tests. Target taken from R4's ranking without
deviation, including its warning: MESO's synthetic lifters have no covariates, so an
experiment that invents one and wires it to the truth measures its own wiring. The round
asked the answerable question instead — **how good would a covariate have to be before it
is worth collecting?**

· **The answer: rho ~ 0.5.** A covariate correlated 0.5 with true log-MRV closes **24%**
of the gap between a constant prescription and an oracle, which is roughly what R4's
entire controller stack is worth. rho 0.3 buys 12%, rho 0.7 buys 38%, rho 0.9 buys 65%.
Below ~0.2 it is not worth a question on the signup form. Whether any real measurement
clears 0.5 is explicitly outside what this project can answer, and D-20 says so.

· **Control and starting information substitute rather than compound.** The controller
adds **4.34** points on top of a constant start, **2.67** on top of rho 0.5, and **1.48**
on top of rho 0.9 — its marginal value falls by two-thirds as the start improves. They
are two routes to the same fact: one asks at signup, the other learns it over 18 weeks.
Buying both pays for one and a bit, which is worth knowing before anyone budgets for
both. D-21.

· **Retracted the round's own opening result.** The first finding was that the default
prescription used since R1 (30.8 sets/wk, the average lifter's MRV) is not the
loss-minimising constant — 26.9 was better by 0.65 points, a free win needing no data at
all. On a clean population that evaporates: the optimum is 28.8 and the gain is **0.16**.
The apparent win was entirely the degenerate lifters dragging the optimum down. Found and
retracted inside the same round.

· **D-16 turned out to be structural, not cosmetic.** R4 logged it as an inflated headline
number. R5 found what it costs downstream: the ~5% of lifters with no interior optimum
inflate the SD of log-MRV by **56%** and drag the geometric mean down **19%**, so every
shrinkage estimator built on those moments spreads its prescriptions wider than the real
population does. R5's first covariate sweep was consequently **non-monotone — a better
covariate producing worse prescriptions** from rho 0.4 to 0.7. Not a property of anything
real. `population_mrvs` now excludes them by default and the contaminated sweep is kept as
a demonstration. D-19.

· **And it reaches back two rounds.** R3 and R4's 24-lifter population contained 8%
degenerate lifters, inflating PRIOR-FIXED's loss from a true 15.15 to the reported 19.97
(1.3x) and the best controller's from 10.29 to 15.14 (1.5x). **Every ordering those rounds
concluded from is preserved** — the concrete vindication of D-15's claim that relative
results survive misspecification while absolute ones do not — but the magnitudes quoted in
DESIGN §4.2 and §4.3 are 30–50% too high, and are now annotated as such rather than
silently recomputed.

R6 · Built four defensible population variants and re-derived every headline against each
(`sim/population.py`, `sim/population_experiment.py`) plus 11 tests. Target taken from
R5's ranking, but deliberately widened: R5 asked for "narrow or justify `PRIOR_SPREAD`",
and narrowing a population until the inconvenient lifters vanish is curve-fitting the
population to the answer. The answerable version is **which conclusions depend on the
population definition and which do not** — the concrete form of D-15, which has been a
standing worry since R3 and never a measurement.

· **The split is clean, and it is the finding.** Across BASELINE (independent uniforms,
as drawn since R1), CLEAN (degenerates rejected), NARROW (ranges tightened by a *derived*
factor of 0.70), and CORRELATED (same marginals, gains correlated via a Gaussian copula):
**ratios barely move** — the covariate thresholds land at 22–24% for rho 0.5 and 63–67%
for rho 0.9 across all four, and every comparison in every round keeps its direction.
**Magnitudes move by 2–3x** — the cost of not personalising ranges **5.23 to 10.04**
points, the controller's added value **1.10 to 3.08**. D-15 predicted exactly this; R6
turns it into D-22: *quote ratios, never magnitudes.*

· **R5's answer is the most robust thing this project has produced**, and now it is clear
why: it is expressed as a fraction of an available gap, so numerator and denominator both
scale with the population's spread. D-21's substitution result is equally stable — the
controller adds less when the start is better, in all four variants without exception.

· **Settled D-16 as far as simulation can, by declining to narrow.** Correlating the two
gains is the physiologically motivated repair — both are gains on the *same* impulse, and
independence permits "adapts barely, fatigues enormously", which is where the degenerate
lifters live. It halves the rate (5.3% → 3.0%) and does not remove it; the remainder comes
from the tau ratio. Narrowing does remove it — **and halves the project's central quantity
while doing so.** So the population is left alone: choosing the version that makes the
estimator well-behaved would also be choosing the version that makes the product look
worth half as much, and there is no evidence to prefer either.

· **The tension that ends the simulation phase.** You cannot have both. If lifters vary as
much as BASELINE says, ~5% of them should never train at all, which is not a claim about
people anyone should believe. If they are as similar as NARROW says, personalisation is
worth roughly half what five rounds have assumed. CORRELATED sits between and is the most
defensible on physiological grounds — where "defensible" means argued for, not measured.
**The project's central quantity is a direct function of a population-shape assumption
made in R1 for convenience and never defended since.** D-23.

· Verified the round's own load-bearing claim rather than asserting it: the CORRELATED
variant must change *only* the joint structure, or any BASELINE-vs-CORRELATED difference
could be a marginal effect in disguise. Measured — means and SDs within 3%, correlation
0.05 → 0.73. Pinned by tests.

R7 · Built the logger (`logger/log.py`, `logger/readiness.py`, `logger/cli.py`) plus 31
tests. First engineering rather than analysis in the project, and taken straight from
D-23's ranking. Append-only JSONL, four CLI verbs, no dependencies; per week it needs hard
sets per muscle group with an RIR for each, and one performance test. Six rounds of
simulation narrowed the requirement to exactly that.

· **The gate now lives in code rather than in a document.** `readiness.assess` enforces
D-13's thresholds, D-10's variation floor and D-15's disclosure — the readiness report
states in its own output that every threshold it applies is calibrated on synthetic
lifters. One consequence worth stating plainly: **a lifter who trains the same volume
every week never unlocks a personalised number, however long they log.** That is D-10
enforced rather than described, and it will read as a bug to anyone who has not read
DESIGN §4.1.

· **Building the measurement chain broke the assumption six rounds rested on.** Every
week-threshold in this project sits on D-09: one weekly test at sigma 2.5. But an e1RM is
not a measurement, it is a *formula applied to* one — and the published formulas disagree
by **5.8%** across the 3–12 rep range (2.8% at 8 reps, 11.3% at 12, **46.1% at 20**). RIR
misestimation adds **4.8%**, and that one is a *bias* rather than noise, so it does not
average out over weeks. Implied sigma: **5.6 against the assumed 2.5.** At that level
median MRV error at 18 weeks is 20.2% rather than 11.1%, and **36 weeks at the implied
noise is still worse than 18 at the assumed noise** — measurement quality, not data
volume, is the binding constraint. That is R2's noise-sensitivity finding arriving from a
completely different direction.

· **The constructive half, and the distinction the project had been missing.** Both noise
sources shrink in the same direction: few reps, close to failure. Capping the test at 8
reps and RIR 0–1 brings implied sigma to **2.4** — D-09's assumption is achievable, but
only under a protocol nobody had specified, and the naive thing to do is test the way you
train, which is exactly wrong. **A test is a measurement, not a stimulus.** Training wants
RIR 1–3 for the stimulus-to-fatigue ratio; a test wants precision. Using one protocol for
both optimises neither. Caps are enforced in `PerformanceTest.validate()`. D-26 — and it
costs nothing but how one set per week is taken.

· Caught a real storage bug with its own test, and fixed the semantics rather than the
symptom: the CLI's read-modify-append wrote whole session records, and the reader summed
every record it saw, so logging three sets one at a time produced a week with five.
Sessions are now keyed on (week, day) with last-write-wins, which is what makes
append-only storage compatible with editing a day at all. Pinned.

R8 · Built the end-to-end rehearsal (`logger/rehearsal.py`) plus 16 tests — the first code
in the project that exercises the path a real person drives, from a logged set to a
prescribed volume. Target taken from R7's ranking without deviation. Seven rounds had
tested the fitter against arrays built by `fit.make_log`; nothing had tested it against
arrays built by the logger, and only one of those ships.

· **The paths agree, which is the licence the round was after.** Median MRV error over 26
weeks: **10.6% production against 10.8% simulation.** Seven rounds of thresholds transfer
to the shipping path.

· **But the rehearsal found a live safety gap no component test could see.** **One fit in
twelve collapses to a parameter set with no interior optimum** — the model's "never train"
corner — for lifters whose *true* MRV is as high as 60 sets/week. The fit does not fail,
does not warn, and `mrv()` returns the lower bound of its own search interval. Every gate
before this asked whether the *lifter* had earned a personalised number; none asked whether
the number the *fitter* produced was a number at all. `fit_is_usable()` now checks, and
`prescribe()` is the single entry point that produces a volume, returning an explicit
source so a caller cannot present a population average as a personalised result. D-27.

· **Quantisation is not a rounding detail.** At **zero** measurement noise, plate rounding
and integer reps alone cost **3–9% median MRV error** (p90 ~20%). No round before this had
modelled it.

· **And one third of that is a fixable bias.** Under D-26's protocol a lifter does as many
reps as they can while leaving the stated RIR, then records an integer — someone who could
manage 4.7 writes 4. The truncation is one-sided, so it is a **bias, not noise: −1.4% on
every observation**, and a bias does not average out the way sigma does. The lost fraction
is uniform on [0,1), so adding back half a rep takes the bias to **+0.02%** and cuts
observation RMS by **~40%**. One constant. Protocol-dependent, so it is a flag rather than
a constant — the alternative protocol truncates in RIR and would double-count it. D-28.

· **Fixed a broken experiment of its own before reporting it.** The first quantisation
sweep tried to separate "integer reps" from "continuous reps" as a factor. That is not
separable — `PerformanceTest.reps` is an int because reps are integers in reality — and the
flag was silently truncated by the record constructor, so two rows of the table differed in
label only. Rewritten to sweep the factor that is real.

· **Left one finding explicitly unexplained.** Coarser plates fit *better* (3.4% at 5 kg
against 9.4% at 1 kg) and the ordering strengthens at n=28, so it is not sampling noise —
but observation-level accuracy is near-identical across plate sizes, so it is not explained
by measurement precision either. The plausible mechanism was not tested. Logged as D-29
OPEN rather than explained badly.

---

## Next round

**The pre-data work is now done.** R7 built the collector, R8 proved the shipping path
recovers what the simulation path recovers and closed the last safety gap between a log and
a prescription. There is no remaining item that changes what gets built.

**What the project needs is twenty lifters and six months.** Unchanged since R6, now fully
unblocked. That dataset settles D-01 (do endurance priors transfer), D-04 (the saturation
ceiling), D-09 (real measurement noise), D-16 (does anyone occupy the degenerate corner),
D-20 (does any real covariate reach rho 0.5), D-24 (is RIR reporting biased), D-25 (the
variation floor) and D-28 (is the truncation model right) — eight open decisions, one
dataset. No simulation settles any of them.

Ranked, for as long as rounds continue without data:

**R9: the RIR bias correction (D-24), specified now rather than later.** R7 measured that a
systematic RIR misestimate shifts an observation 4.8% and does not average out; D-28 just
showed how much a bias of that size matters. A per-lifter offset is estimable from the
relationship between logged RIR-2 sets and tested maxes — but only if the logger records
what the estimate needs. **Data not collected in month one cannot be recovered in month
six**, which makes this the last thing that is cheap now and expensive later.

**Runner-up: re-derive D-25's variation floor.** 0.18 is the weakest number in the logger,
calibrated against a synthetic history and never a real one. It decides whether a real user
ever gets a personalised number, so it is the threshold most likely to be wrong in a way
someone actually feels.

**Third: D-29's plate mystery.** Cheap, and the honest way to close an OPEN decision — run
the modelled re-targeting protocol against a fixed-load protocol and see whether the effect
survives.

**Fourth: D-06, the volume-matched deload sweep.** Now unstarted through seven rankings.
Worth one round purely to close it rather than carry it forever.

**Everything else in simulation** remains worth less than the uncertainty in the population
definition (D-22, D-23).
