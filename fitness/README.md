# MESO

**A training planner that simulates before it prescribes.**

The plan is a hypothesis. The log is the experiment. Every prescription is generated from
a per-lifter parameter set, and every logged week re-fits those parameters — so next
week's plan comes from *your* measured response, not from a population average that fits
almost nobody.

---

## Status

**Round 1 complete. Model built, tested, and already overturned once.**

R1 set out to design a triggered-deload rule and instead found that the standard
fitness-fatigue model **cannot represent volume at all** — its steady-state preparedness
is strictly increasing in weekly sets, so it prescribes infinite training and has no
maximum recoverable volume, no minimum effective volume, and no reason to ever deload.
Every deload result that came out of it before the correction was an artefact.

The correction — saturating stimulus with linear fatigue — is one parameter, and it makes
MRV a model *output* instead of an assumption. Details in `DESIGN.md` §3.

Not built yet: the fitter, the volume budget, the autoregulation controller, the logger.

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
| **[tests/](tests/)** | 24 tests pinning the properties a later round could quietly break. | Every round, before and after. |

## The five ideas everything hangs off

1. **Fit the lifter, don't apply the template.** The population spread in maximum
   recoverable volume is **8.9x** from p10 to p90. No template survives that.
2. **Volume is spent, not scheduled.** Weekly sets are a budget against diminishing
   returns, not a number copied off a spreadsheet.
3. **Autoregulation is a control loop, not a vibe.** An explicit gain — a number that can
   be wrong, and therefore improved.
4. **The mesocycle is a search, not a ritual.** The ramp exists to find your MRV; the
   deload is what overshooting costs.
5. **Every recommendation states its confidence.** Below the identifiability threshold
   the app says "population prior, not your data" out loud, every time.

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

cd .. && python3 -m unittest discover tests   # 24 tests
```

## What is solid and what isn't

**Solid:** the model's structure and its two enforced constraints; the proof that the
linear form has no interior optimum; the population-spread argument for fitting; the test
suite.

**Specified but unverified:** every parameter value. All five priors are literature-typical
figures from *endurance* research, and the saturation ceiling is a guess whose value the
entire volume prescription turns on. `DECISIONS.md` flags each one with what would replace
it.

**Not started:** fitting, and therefore the whole premise.
