# MESO — Decision Log

Every non-obvious call, why it was made, and **what would prove it wrong**.

A decision with no falsification condition is a belief, and beliefs are how projects
spend eighteen months building the wrong thing. Writing the condition down in advance
also makes it socially cheap to reverse the call later: you are not admitting an error,
you are hitting a condition you set yourself.

Status values: **FIRM** (reversing it restructures the project) · **WORKING** (best
current answer, expected to move) · **OPEN** (not yet decided) · **OVERTURNED**.

---

## D-01 · The population priors are endurance numbers wearing a lifting hat — WORKING

`k_fit` 1.00, `k_fat` 1.90, `tau_fit` 42 d, `tau_fat` 9 d.

**Why:** impulse-response modelling has decades of published parameter estimates, almost
all from running, swimming and cycling. Starting from those beats starting from nothing,
provided nobody forgets where they came from.

**What it costs:** every number downstream of these — MRV, deload timing, the volume
curve — inherits an unverified transfer from endurance to resistance training.

**What would prove it wrong:** the first ten real lifters fitted in R2+. If their fitted
`tau_fat` clusters somewhere well away from 9 days, or if fits fail to converge at all,
the priors are wrong and the population spread in `PRIOR_SPREAD` is wrong with them.
This is cheap to check and should be checked the moment real logs exist.

---

## D-02 · Two traces, not three — FIRM (conclusion), **PREMISE FALSIFIED** (R2)

Busso's variable-gain and three-component variants fit historical data better.

**Why two anyway:** a better model you cannot identify is worse than a cruder one you
can.

**The original premise was wrong and R2 proved it.** D-02 was written on "four free
parameters are recoverable from ~20 sessions". They are not. At 8 weeks of logs (~24
sessions) the median MRV error is **26.4%** and the p90 is **1328%**. Usable accuracy
arrives at roughly **24 weeks** of *varied* training (8.6% median), and keeps improving
to 52 (4.5%). DESIGN.md §4.1.

**The conclusion survives and hardens.** R2 also tested the fifth parameter D-04 would
most like to free — the saturation ceiling — and it triples median error (5.9% → 18.7%
on the informative history) with a p90 of 759%. If four parameters are already at the
edge of what real logs support, three components are not a close call.

**What this changes downstream:** the confidence gate in DESIGN.md §4.1 is no longer
optional, and its threshold is now a measured quantity rather than a guess. Any feature
that assumes a trustworthy fit inside a first mesocycle is built on sand.

**Amended by R3.** The ~24-week figure here comes from percent MRV error. Scored in
preparedness points — the currency a lifter actually experiences — the collapse happens
between weeks **16 and 18** (DESIGN.md §4.2). The two metrics disagree because percent
error treats a 20% overshoot and a 20% undershoot as the same mistake and the
preparedness curve does not. D-13's thresholds supersede this number; the qualitative
claim (far more than 8 weeks) is unchanged and is what mattered.

**What would still prove the conclusion wrong:** a three-component model that reaches
0.94+ correlation on a WAVED history in under 24 weeks. Given four parameters need 24,
this would require the extra structure to be *more* identifiable than what it adds, which
is not how identifiability works. Treat any such result as a bug first.

---

## D-03 · The RIR tables are a hand-fitted shape — WORKING

Stimulus flat from RIR 0–2 then falling away; fatigue rising steeply toward failure.

**Why:** the *shape* is the consensus reading of the proximity-to-failure literature —
adaptation is roughly flat within a few reps of failure while fatigue is not. The
divergence between the two curves is what makes RIR 1–3 the right prescription.

**What it costs:** the exact numbers are drawn by hand to that shape. Any result that
turns on the second decimal of these tables is not a result.

**What would prove it wrong:** the qualitative claim survives unless the stimulus/fatigue
ratio stops being monotonic in RIR. Pinned by
`test_fatigue_rises_faster_than_stimulus_toward_failure`. If a later round needs the ratio
to be non-monotonic, that is a new decision, not a tuning tweak.

---

## D-04 · Stimulus saturates per session; fatigue stays linear — FIRM (structure), WORKING (value)

`stimulus = ceiling * (1 - exp(-sets/ceiling))`, `ceiling = 12` set-equivalents/session.

**Why:** R1 proved the linear model has no interior optimum in volume — its steady-state
preparedness is strictly increasing in weekly sets, so it prescribes infinite training
and cannot represent MRV, MEV, or any reason to deload (DESIGN.md §3.2). A model that
cannot say "too much" cannot be the basis of a training planner. Saturating the benefit
while leaving the cost linear is the cheapest correction that produces an interior
optimum: one parameter, derivative 1 at the origin, low-volume behaviour unchanged.

**Structure is FIRM** because the alternative repair was tested and failed: discounting
adaptation under chronic fatigue (`StalenessParams`) moves the answer by +2.7 points at a
plausible onset, and only bites when set so aggressively that it lowers everyone's curve
instead of bending anyone's. Null result kept in the code, disabled.

**Value is WORKING.** `ceiling = 12` puts the prior lifter's MRV at 30.8 sets/week/muscle
group, above commonly-cited tables of ~20–25.

**What would prove the value wrong:** fitted `ceiling` from real logs landing outside
roughly 6–20. Below 6 and the model forbids productive sessions people demonstrably run;
above 20 and saturation stops binding in any realistic session and D-04 has bought
nothing. Also suspect if the discrepancy with published tables turns out to be a
set-counting convention difference rather than a parameter error — that is a
bookkeeping bug wearing a physiology costume.

---

## D-05 · The model has no honest opinion on training frequency — OPEN

Saturation is applied **per session**, so the model mechanically prefers spreading the
same weekly volume across more sessions, without representing warm-up time, travel,
or adherence.

**Why it is open, not decided:** the preference is real inside the model and meaningless
outside it. Reading a frequency recommendation out of the current code would be reading
an artefact of where the saturation was attached.

**What resolves it:** either attach a per-session fixed cost (making frequency a genuine
trade-off), or declare frequency a user constraint the planner accepts rather than
optimises. The second is probably right and is certainly cheaper. Do not ship a
frequency recommendation until one of them is chosen.

---

## D-06 · Deload cadence is not worth optimising — FIRM

**Why:** R1's corrected sweep put FIXED-3, FIXED-5, FIXED-7 and TRIGGERED within **0.8
preparedness points** of each other, while the gap between deloading at all and never
deloading was **~13 points**, and the gap between a fitted and an unfitted lifter is
**~36 points** (DESIGN.md §4). Effort spent on cadence is effort spent on the third
decimal of the third-largest term.

**What it costs:** MESO will ship a boring, defensible deload rule and put the
engineering into fitting instead.

**What would prove it wrong:** any policy beating the field by more than ~3 points at
equal total volume. Note the equal-volume clause — the current comparison is confounded,
since the winning policies did 45–70% of the losing one's work, and a like-for-like
volume-matched sweep is the honest version of this test. Until that exists, D-06 rests
on a comparison that is suggestive rather than clean.

---

## D-07 · A trigger built on "am I getting worse" will always be late — **RESOLVED, and the fix was not worth it** (R4)

R1's triggered policy fired spuriously in week 3 on a startup transient, then never fired
again while volume ramped 46% past MRV.

**Why it happens:** the fitness trace integrates over `tau_fit` (~42 d), so preparedness
keeps *rising* for weeks after the marginal set has stopped paying. Performance decline
is a lagging indicator of overreaching with lag on the order of `tau_fit`. This is
structural, not a threshold that needs tuning.

**What follows:** a working trigger must watch the **derivative of response with respect
to dose** — the last volume increment bought less than the one before — not the level of
the output. That is R2's target.

**What would prove it wrong:** a level-based trigger that detects overshoot within two
weeks of it starting, across the synthetic population, without firing on the startup
transient. If one exists, it is doing something the lag argument says is impossible and
is worth understanding.

**R4 built the replacement, and the mechanism argument held perfectly while being worth
almost nothing.** Sign of the marginal return is correct 96% of the time at week 12,
when the MRV estimate is still 22% wrong — direction genuinely is an easier question than
location. But in closed loop over 24 weeks the dose-derivative controller scored **15.20**
mean points lost against the broken level trigger's **14.93**, with a worst case more
than twice as bad (117.6 vs 52.4). Gating it on R3's threshold recovers a narrow lead
(14.23, best of anything tested), but the entire field spans 14.2–15.5 against an oracle
at 0.

**The reason is D-17, and it retires this line of work.** Effort on control mechanism is
effort on the flat part of the objective.

---

## D-08 · The project's own falsification test — **PASSED** (R2)

MESO's claim is that a fitted plan beats a good template. The whole thing rests on it.

**The condition, written down in advance:** if re-fitting after each new week swings
prescribed volume by more than ~20%, the fit is tracking noise and a stable template
beats a jittery personalisation regardless of which is theoretically better.

**Measured, R2:** refitting weekly from week 8 to week 24 moves the prescribed volume by
a median of **3.4%** (PROBE), **5.7%** (WAVED), **4.3%** (FLAT). Comfortably inside the
threshold.

**And the test that makes that number mean something.** A fit that never leaves its
starting point would also score ~0% swing, so stability alone proves nothing. Against
two constant baselines — always prescribe the population prior, always prescribe the
population median — the fitter scores **0.98 correlation with truth** and 16% median
error where the constants score **0.00** and ~59%. It is genuinely learning the lifter,
and it is holding still while it does. Both halves were required.

**Residual worry, unresolved:** the p90 and worst-case swings are 28% and 96% (PROBE),
so a minority of lifters do see prescriptions jump. Combined with the fat error tail in
D-10, this is the same population — poorly-identified lifters — showing up twice. The
confidence gate has to catch them, and that is R3.

---

## D-09 · One weekly performance test, sigma 2.5 points — WORKING

The fitter is fed one measurement per week: a top set to a known RIR, converted to an
estimated 1RM, expressed as a percentage of a baseline test, plus Gaussian noise with
sigma = 2.5 (i.e. a 2.5% coefficient of variation).

**Why:** it is roughly the test-retest variability of an estimated 1RM, and one test per
week is the most a real lifter will reliably produce without the measurement becoming
training in its own right.

**What it costs:** noise dominates the result. Median MRV error runs 0.0% at sigma 0,
6.1% at sigma 1, 14.1% at 2.5 and 23.8% at 5. **Fit quality is roughly linear in
measurement noise**, which means better estimation is worth as much as any modelling
improvement this project could make.

**What would prove it wrong:** real logged e1RM series with a test-retest CV outside
1–4%. Above 4% the fit needs multiple measurements per week or a smoothed estimate, and
the 24-week data threshold gets worse. INFERRED — no measurement, literature-typical.

---

## D-10 · An unvarying plan is an uninformative experiment — FIRM

A lifter who trains the same volume every week produces a log that barely identifies
them: correlation **0.45** and 38.5% median MRV error, against **0.94** for a normal
waved mesocycle and **0.98** for a deliberately varied one.

**Why it happens:** a constant input drives both exponential traces in lockstep. Nothing
in the response separates a fast-fatiguing lifter from a slow-adapting one, so the loss
surface is nearly flat along the direction that matters.

**What follows:** variation in the plan is not only a search for MRV (idea 4) — it is the
excitation signal. A planner that prescribes a comfortable, unvarying block is degrading
its own next prescription, and should be prevented from doing so by a variation floor
rather than trusted not to.

**What would prove it wrong:** a fit reaching 0.9+ correlation on a genuinely flat
history. That would mean the identifiability is coming from somewhere other than the
input variation, and the whole excitation argument is wrong.

---

## D-11 · Don't optimise the plan for identifiability — WORKING

PROBE (alternating 8 and 36 sets) scores 0.98. WAVED — a normal ramp-and-deload
mesocycle people would actually run — scores 0.94, for free.

**The call:** take the 0.94. The remaining gap is small, and buying it costs a training
plan nobody wants to follow. Prescribe a normal mesocycle with a *variation floor*, not a
plan designed to excite the model.

**What it costs:** a slightly worse fit for everyone, forever.

**What would prove it wrong:** a variation schedule that closes most of the 0.94→0.98 gap
while staying inside what a normal mesocycle already does — e.g. deeper deloads, which
cost little and add excitation. Worth one experiment. It would move this from WORKING to
FIRM in either direction.

---

## D-12 · Small-population medians in this project are not measurements — WORKING

The same fitter configuration produced median MRV errors of 5.9%, 14.1%, 16.0% and 20.0%
across four R2 experiments that differed only in which synthetic lifters they drew.

**Why it matters:** those are the numbers every decision in this project is made from,
and a 3x swing from sampling alone is larger than most of the effects being compared.

**The rule from here:** headline numbers come from populations of 24+, and any figure
from a run of 6–12 lifters is labelled directional. Where two arms are being compared,
use common random numbers — the same lifters and the same noise draws in both — so the
comparison is paired rather than two independent noisy estimates.

**What would prove it wrong:** nothing; this is a methodology fix, not a claim. It is
logged because R2 nearly quoted the 5.9% figure as a headline, and that number was
sampling luck.

---

## D-13 · The confidence gate is keyed on history, not on the fit's opinion of itself — FIRM

Below 14 weeks of logged varied training, prescribe the population prior and label it as
such. From 14 to 18, shrink toward it. Past 18, use the fit.

**Why:** R3 tested four signals and the cheapest one won. `weeks_logged` is free,
knowable *before* the lifter trains, and outperforms a twelve-draw bootstrap. Ungated
fitting at 8 weeks costs 100.4 preparedness points against the prior's 19.97 — five times
worse than not personalising at all, with a p90 of 248. The threshold is where the loss
curve collapses: 19.4 points at week 14, 10.3 at 16, **0.88 at 18**.

**What it costs:** every new user gets a population prescription for three to four
months, in a product whose entire pitch is personalisation. That is the honest price of
the fitter not working yet, and hiding it would mean shipping harm to exactly the people
most likely to install this.

**What would prove it wrong:** a signal that beats `weeks_logged` at ordering lifters by
realised loss — profile likelihood over MRV rather than a residual bootstrap is the
obvious candidate, since it would measure curvature of the loss surface rather than
reproducibility of a point estimate. Also wrong if real-lifter data puts the collapse
anywhere but 14–18 weeks (see D-15).

---

## D-14 · A bootstrap measures precision, not accuracy — FIRM

The empirical-Bayes shrinkage in `confidence.py` is principled, has no tunable
thresholds, and **loses to a crude week-count rule**: 30.22 points against 19.97 at 8
weeks, 22.03 against 19.97 at 12.

**Why it fails:** resampling residuals around a badly-wrong fit measures how
*reproducible* that wrong answer is, not how wrong it is. A confidently-wrong fit has a
small bootstrap spread. R3's weights table shows the consequence directly — mean
shrinkage weight at 8 weeks is 0.50 (WAVED) and 0.68 (PROBE), so the gate extends most of
its trust to fits that are off by 100 points. Self-reported uncertainty under-shrinks
exactly the lifters who most need shrinking.

**What follows:** keep the shrinkage — it is strictly better than ungated fitting
everywhere and free after the threshold, and it is what makes the 14–18 week band usable
(13.2 points against the prior's 20.0 at week 14). But it is a refinement inside the
gate, never the gate itself.

**What would prove it wrong:** any self-reported uncertainty measure that beats
`weeks_logged`. The mechanism argument says a resampling method cannot, because it never
sees the truth; a curvature-based interval might, because a flat loss surface is
observable without it.

---

## D-15 · Every threshold in R3 is calibrated on the model's own children — WORKING

The 14/18-week thresholds, the shrinkage weight, and the population `tau` are all
calibrated on synthetic lifters drawn from `PRIOR_SPREAD` and simulated by the same model
that then fits them.

**Why it is stated rather than fixed:** there is no honest way to fix it without real
data, and pretending otherwise would launder a self-consistency check into a validation.
The one genuine protection available — checking that the fitter beats its null, that the
gate beats ungated fitting, and that the crude signal beats the sophisticated one — are
all *relative* comparisons, which survive model misspecification better than any absolute
threshold does.

**What would prove it wrong:** real logged data where the loss curve collapses anywhere
but 14–18 weeks. Expect it to be worse, not better: real lifters carry sources of
variation the model has no term for, and every one of them pushes the threshold later.

**What this blocks:** shipping a specific week count to a user as though it were
measured. It is calibrated, on simulated people.

---

## D-16 · Part of the population has no MRV, and it inflated R1's headline — WORKING

`mrv()` searches for the volume maximising steady-state preparedness over [0.5, 200]
sets/week. For lifters whose linear bracket is negative — the ones R1 found the model
tells never to train — there is no interior optimum, and the search silently returned its
own lower bound as though it were a prescription.

**Scale of it:** 9 of 200 synthetic lifters (**4.5%**), plus a wider tail of 18 (**9%**)
whose "MRV" lands below 5 sets/week, which is not a plausible number for anyone who
trains.

**What it corrupted:** R1's headline population spread, the number that reorganised the
whole project. Reported as **8.86x** (p10 5.8, p90 51.3); excluding degenerate lifters it
is **5.76x** (p10 8.9, p90 51.3). Inflated by a third. The conclusion is unaffected — a
5.8x spread still defeats any template — but the figure was quoted in the README, in
DESIGN idea 1, and in three commit messages, and it was wrong in all of them.

**Caught by:** a test asserting the derivative is positive below MRV, written in R4 for
an unrelated reason. It had been true and unnoticed since R1.

**The fix applied:** `has_interior_optimum()` makes the case detectable instead of
silent, and it is pinned by a test. The population is *not* narrowed, because doing so
would invalidate every number in four rounds for a 4.5% effect — but every spread figure
now gets reported both ways.

**What would prove it wrong / what is still open:** whether `PRIOR_SPREAD` should be
narrowed at the low end at all. It currently generates people the model says cannot
train, which is either an honest representation of non-responders or a modelling artefact
of drawing k and tau independently. Nobody has checked which, and D-01's real-lifter test
would settle it.

---

## D-17 · The optimum is flat, so precision is worth ~1/12th of avoiding gross error — FIRM

Points lost by prescribing a multiple of a lifter's true MRV: **0.32** at ×0.9, **1.78**
at ×1.25, **6.52** at ×1.5, **22.36** at ×2.0.

**Why this is a decision and not just a measurement:** it is the single explanation for
every "crude beats principled" result the project has produced, and it should be used
prospectively rather than rediscovered every round.

- D-06 — deload cadence worth under 1 point, overshooting MRV worth 13.
- R3 — a plain week count beat empirical-Bayes shrinkage over a residual bootstrap.
- R4 — a broken level trigger beat a correct dose-derivative controller.

Three rounds, three sophisticated methods beaten by crude ones, one cause.

**The rule that follows:** *anything that only improves accuracy near the peak is not
worth a round.* The burden is on any proposal to show it prevents gross error — being
2x wrong, or being wrong for months — rather than refining an answer that is already
within 25%.

**What would prove it wrong:** a term in the objective that is *not* flat near its
optimum. Injury hazard is the obvious candidate and is explicitly out of scope
(DESIGN.md §8) — if it were ever brought in, its curve near MRV would need checking
before D-17 could be applied to it.

---

## D-18 · A small dither in prescribed volume is free and cuts the tail — WORKING

±10% alternating wobble around the controller's centre. Mean loss 16.21 against 16.76
without it, p90 loss **33.62 against 48.37**, convergence marginally faster (median 16
weeks vs 17.5).

**Why it works:** a controller that has converged stops varying, and D-10 says an
unvarying plan is an uninformative experiment — so a converged controller slowly blinds
the fit it depends on. The dither keeps the excitation alive at a cost the flat objective
(D-17) makes negligible.

**Why ±10% and not more:** larger dithers keep the tail benefit but start costing the
mean (17.94 at ±30%). The benefit is in *having* excitation, not in having a lot of it.

**What would prove it wrong:** real lifters finding a weekly ±10% swing annoying enough
to hurt adherence, which no simulation here can see. Also suspect if the tail improvement
turns out to be driven by the dither accidentally slowing the controller near the
boundary rather than by better identification — worth one experiment to separate.
