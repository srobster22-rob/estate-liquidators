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

## D-02 · Two traces, not three — FIRM

Busso's variable-gain and three-component variants fit historical data better.

**Why two anyway:** the binding constraint is a lifter with eight weeks of logs, not a
lab with two years of data. Four free parameters are recoverable from ~20 sessions;
seven are not. A better model you cannot identify is worse than a cruder one you can.

**What would prove it wrong:** if R2's fitting shows four parameters are *already*
unidentifiable from realistic logs, the answer is fewer parameters and stronger priors,
not more. Either way, three components stay out.

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

## D-08 · The project's own falsification test — WORKING

MESO's claim is that a fitted plan beats a good template. The whole thing rests on it.

**What would prove it wrong:** fitted parameters that are unstable week to week — if
re-fitting after each new week swings prescribed volume by more than ~20%, the "fit"
is tracking noise, and a stable template beats a jittery personalisation regardless of
which one is theoretically better. **This is the single most likely way this project
fails**, and R2 should measure it before building anything on top of the fitter.
