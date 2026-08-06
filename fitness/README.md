# MESO

**A training planner that simulates before it prescribes.**

The plan is a hypothesis. The log is the experiment. Every prescription is generated from
a per-lifter parameter set, and every logged week re-fits those parameters — so next
week's plan comes from *your* measured response, not from a population average that fits
almost nobody.

---

## Status

**Rounds 1–3 complete. The premise survived each round, at a price each time.**

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

Not built yet: the dose-derivative trigger, the volume budget, the autoregulation
controller, the logger.

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
| **[tests/](tests/)** | 49 tests pinning the properties a later round could quietly break. | Every round, before and after. |

## The five ideas everything hangs off

1. **Fit the lifter, don't apply the template.** The population spread in maximum
   recoverable volume is **8.9x** from p10 to p90. No template survives that.
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
*cadences*, under **1**.

Not knowing which lifter you are costs 2–4x more than every programming decision this
project set out to optimise. That is why the fitter is R2 and everything else waits.

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

cd .. && python3 -m unittest discover tests   # 49 tests
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
