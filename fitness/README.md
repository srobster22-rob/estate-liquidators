# MESO

**A training planner that simulates before it prescribes.**

The plan is a hypothesis. The log is the experiment. Every prescription is generated from
a per-lifter parameter set, and every logged week re-fits those parameters — so next
week's plan comes from *your* measured response, not from a population average that fits
almost nobody.

---

## Status

**Rounds 1–8 complete. The premise survived each round, at a price each time.**

**R1** set out to design a triggered-deload rule and instead found that the standard
fitness-fatigue model **cannot represent volume at all** — its steady-state preparedness
is strictly increasing in weekly sets, so it prescribes infinite training and has no
maximum recoverable volume, no minimum effective volume, and no reason to ever deload.
Every deload result that came out of it before the correction was an artefact. The fix —
saturating stimulus with linear fatigue — is one parameter, and it makes MRV a model
*output* instead of an assumption. `DESIGN.md` §3.

**R2** built the fitter and put it on trial. It works: **0.98 correlation** with truth on
an informative history, against **0.00** for the constant baselines it has to beat, and
it holds still — 3–6% week-to-week swing in prescribed volume, against a 20% failure
threshold written down in advance. But it needs **~24 weeks** of *varied* training, not
the 8 the project was designed around, and its error tail is dangerous: p90 off by 34%,
worst case by a factor of four. `DESIGN.md` §4.1.

**R3** built the confidence gate and found that R2's fitter, shipped ungated, would have
been *actively harmful*: at 8 weeks of logs a personalised prescription costs **100
preparedness points** against the population prior's 20 — five times worse than ignoring
the lifter entirely. The usable threshold is **18 weeks** of varied training. And the
principled gate (empirical-Bayes shrinkage over a bootstrap) **lost to a plain week
count**, because a bootstrap measures precision rather than accuracy and a
confidently-wrong fit sails through it. `DESIGN.md` §4.2.

**R4** built the dose-derivative controller D-07 had wanted since R1. The hypothesis held
— knowing *which way is uphill* is reliable at week 12, while knowing *where the peak is*
takes 18 — and it bought almost nothing: in closed loop the new controller **lost to R1's
broken one** (15.20 points against 14.93). The reason unified three rounds of results:
**the optimum is flat.** Being 25% off costs 1.8 points, being 100% off costs 22, so
essentially all the value is in avoiding gross error and none is in precision. It also
found that 86% of the remaining loss belongs to lifters far from the population prior,
which makes a better *prior* the next lever rather than a better controller. `DESIGN.md`
§4.3.

**R5** asked what a better starting point would be worth, without inventing a covariate
and then congratulating itself for the invention. A covariate would need to correlate
**~0.5** with a lifter's true MRV to be worth what R4's entire controller stack is worth —
and the two **substitute rather than compound**, since both are routes to the same fact.
It also found that the degenerate lifters D-16 turned up don't just inflate a headline:
they inflate the population's log-MRV spread by 56% and broke this round's estimator
outright, making a *better* covariate produce *worse* prescriptions. `DESIGN.md` §4.4.

**R6** asked which conclusions actually depend on the population definition, by
re-deriving every headline against four defensible populations. The split is clean:
**ratios are robust** (the covariate thresholds move by at most 2 points across all four),
**magnitudes are not** (the cost of not personalising ranges 5.2 to 10.0). It also exposed
a tension the project cannot resolve alone — the population that makes the estimator
well-behaved is the one that makes the product worth half as much. `DESIGN.md` §4.5.

**The simulation phase is complete (D-23).** Six rounds established what can be
established that way; the project's central quantity is a direct function of a
population-shape assumption made in R1 for convenience and never defended.

**R7 built the logger** — the thing that collects what would replace it. Building it broke
the assumption six rounds rested on: the measurement chain is **2.2x noisier** than D-09
assumed, because an e1RM is a formula applied to a measurement and the formulas disagree
by 5.8% across the working rep range. At the real noise level, 36 weeks of data is worse
than 18 at the assumed level — measurement quality, not data volume, is the binding
constraint. It is recoverable, but only under a protocol nobody had specified: **a test is
a measurement, not a stimulus**, so it is capped at 8 reps and RIR 0–1 while training
stays at RIR 1–3. That single change is worth a factor of 2.3 and costs nothing.
`DESIGN.md` §4.6.

**R8 drove the whole thing end to end** — the first test of the path a real person
actually walks, from a logged set to a prescribed volume. The shipping path recovers what
the simulation path recovers (**10.6% against 10.8%** median MRV error), so eight rounds of
thresholds transfer. But it found a live safety gap no component test could see: **1 fit in
12 collapses to the model's "never train" corner**, silently, for lifters whose true MRV is
60 sets/week. Now caught. It also found that quantisation alone — plates and integer reps —
costs 3–9% error at zero measurement noise, a third of which is a **fixable bias** that one
constant removes. `DESIGN.md` §4.7.

**What comes next is twenty lifters and six months.** The collector exists, the path is
proven, and the last gap between a log and a safe prescription is closed. That dataset
settles eight open decisions at once — and no simulation settles any of them.

Not built yet: the volume budget, the autoregulation controller, the logger.

## The documents

| Doc | What it is | Read it when |
|---|---|---|
| **[DESIGN.md](DESIGN.md)** | The model, the hole R1 found in it, the fix, and what deloads are actually worth. | Start here. §3 is the load-bearing section. |
| **[DECISIONS.md](DECISIONS.md)** | Every non-obvious call, why, and what would prove it wrong. | Before re-opening a settled argument. |
| **[LOOP_LOG.md](LOOP_LOG.md)** | One entry per round: what was built, what it found. Ends with the ranked next targets. | Resuming work. |
| **[ITERATION-PROMPT.md](ITERATION-PROMPT.md)** | The reusable prompt for continuing this. | Next session. |
| **[sim/ff_model.py](sim/ff_model.py)** | The two-trace impulse-response core. No policy lives here. | Before touching any number. |
| **[sim/volume_response.py](sim/volume_response.py)** | Does the model have an interior optimum in volume? (R1: no. Then: yes.) | Before changing the saturation ceiling. |
| **[sim/deload_sweep.py](sim/deload_sweep.py)** | Five deload policies over a 20-week block, three model variants. | Before arguing about deload cadence. |
| **[sim/fit.py](sim/fit.py)** | The per-lifter fitter: reparameterised least squares, multi-start Nelder-Mead, pure stdlib. | Before touching the fit or the MRV search. |
| **[sim/fit_experiment.py](sim/fit_experiment.py)** | Does the fit work, hold still, and beat a constant? Five experiments. | Before believing any claim about personalisation. |
| **[sim/confidence.py](sim/confidence.py)** | The gate: four candidate signals, bootstrap, and empirical-Bayes shrinkage. | Before trusting any prescription. |
| **[sim/confidence_experiment.py](sim/confidence_experiment.py)** | Which signal works, does the gate help, and where is the threshold? | Before changing when the app trusts a fit. |
| **[sim/trigger.py](sim/trigger.py)** | Marginal-return estimation and the closed-loop controllers, including R1's broken one. | Before changing how volume is steered. |
| **[sim/trigger_experiment.py](sim/trigger_experiment.py)** | Is direction easier than location, and does it pay? | Before proposing a smarter controller. |
| **[sim/prior.py](sim/prior.py)** | The starting prior, the covariate sensitivity model, and clean population moments. | Before adding a signup question. |
| **[sim/prior_experiment.py](sim/prior_experiment.py)** | What a covariate would have to be worth, and whether it compounds with control. | Before assuming personalisation data pays. |
| **[sim/population.py](sim/population.py)** | Four defensible population variants, including a copula that isolates dependence. | Before trusting any absolute number. |
| **[sim/population_experiment.py](sim/population_experiment.py)** | Which conclusions survive the population definition and which don't. | Before quoting a figure outside this repo. |
| **[logger/](logger/)** | The thing that collects real data: append-only log, readiness gate, CLI. | Before logging a single set. |
| **[logger/formula_check.py](logger/formula_check.py)** | Is the measurement chain as clean as D-09 assumes? (No — and here is the protocol that fixes it.) | Before designing a test protocol. |
| **[logger/rehearsal.py](logger/rehearsal.py)** | The whole path, end to end, against a lifter whose truth is known. | Before trusting that the shipping code does what the simulation measured. |
| **[tests/](tests/)** | 135 tests pinning the properties a later round could quietly break. | Every round, before and after. |

## The five ideas everything hangs off

1. **Fit the lifter, don't apply the template.** The population spread in maximum
   recoverable volume is **5.8x** from p10 to p90 (R1 said 8.9x; R4 found that figure
   included lifters the model says should never train — D-16). No template survives that.
2. **Volume is spent, not scheduled.** Weekly sets are a budget against diminishing
   returns, not a number copied off a spreadsheet.
3. **Autoregulation is a control loop, not a vibe.** An explicit gain — a number that can
   be wrong, and therefore improved.
4. **The mesocycle is a search, not a ritual.** The ramp exists to find your MRV — and
   its variation is also the excitation signal that makes you identifiable at all. Train
   the same amount every week and the fit barely knows who you are (0.45 correlation,
   against 0.94 for a normal waved block).
5. **Every recommendation states its confidence.** Below 18 weeks of varied logged
   training the app says "population prior, not your data" out loud, every time — because
   R3 measured what happens otherwise, and it is five times worse than not personalising
   at all.

## The one number that reorganised the project

Prescribing the population-median volume to everyone costs the median lifter **7.4**
preparedness points, the p90 lifter **35.9**, and the worst-fit lifter **61.7**.

The entire gap between the best and worst deload policy is **~14**. Between deload
*cadences*, under **1**. Between the best and worst *controller*, under **1.3**.

Not knowing which lifter you are costs several times more than every programming decision
this project set out to optimise — and R4 sharpened it further: **86% of the remaining
loss belongs to the lifters furthest from the population average**, during the weeks
before anything can tell they are unusual.

## Running it

Pure Python 3.11 standard library. No dependencies, by design — every simulation here
should still run in five years.

```bash
cd fitness/sim
python3 ff_model.py          # smoke test
python3 volume_response.py   # dose-response, and the MRV spread
python3 deload_sweep.py      # policy comparison across three model variants
python3 fit_experiment.py    # recovery, stability, noise, null hypothesis, data volume

python3 confidence_experiment.py  # signals, outcome in points, the tail, the threshold
python3 trigger_experiment.py     # sign vs argmax, closed loop, convergence, robustness
python3 prior_experiment.py       # the free win, the rho sweep, compounding
python3 population_experiment.py  # every headline, re-derived four ways

cd ../logger
python3 formula_check.py          # what the measurement chain actually injects
python3 -m logger.cli status LOG --muscle quads   # (from fitness/) what a log has earned

python3 rehearsal.py              # production path vs simulation path

cd .. && python3 -m unittest discover tests   # 135 tests
```

## What is solid and what isn't

**Solid:** the model's structure and its two enforced constraints; the proof that the
linear form has no interior optimum; the population-spread argument for fitting; that the
fit is findable, stable, and beats its null; that the gate beats ungated fitting and a
week count beats a bootstrap; the test suite.

**Specified but unverified:** every parameter value. All five priors are literature-typical
figures from *endurance* research, and the saturation ceiling is a guess whose value the
entire volume prescription turns on. `DECISIONS.md` flags each one with what would replace
it.

**Calibrated, not validated:** every threshold — 18 weeks, the shrinkage weight, the
population spread — comes from synthetic lifters drawn from the model's own prior and
simulated by the model that then fits them. The *relative* results survive that; the
specific numbers want real logs before anyone quotes them to a person. `DECISIONS.md`
D-15.

**Not started:** the dose-derivative trigger, the volume budget across muscle groups, the
autoregulation controller, the logger.
