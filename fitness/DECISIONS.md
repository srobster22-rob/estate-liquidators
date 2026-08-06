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

## D-07 · A trigger built on "am I getting worse" will always be late — FIRM

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
