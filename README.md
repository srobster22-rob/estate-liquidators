# ESTATE LIQUIDATORS

**Co-op horror extraction for 4 players.** You're a cleanout crew emptying a dead collector's
estate before sunrise. Every object has a dollar value, the van has finite space, and the
quota is in dollars, not items.

The thing in the house isn't a predator — it's a **curator**. It doesn't hunt intruders, it
retrieves property. Its attention follows the most valuable thing currently leaving the
house, which means it follows *whoever is holding it*.

You can get rid of the monster by handing the vase to your friend.

---

## Status

**Design foundation, plus working code.** Eight Python simulations, a C# rules core pinned by
31 passing checks (`unity/tests/CoreTests`), a fail-closed drift checker holding all three
implementations to `tuning.json`, and two browser prototypes of the loop — which are loop
tests, not the product. The design documents themselves are deliberately unfinished — they're
built to be extended, argued with, and revised as playtests come back. Nothing here is
precious except the things marked FIRM in the decision log, and even those state their own
falsification conditions.

## The documents

| Doc | What it is | Read it when |
|---|---|---|
| **[DESIGN.md](DESIGN.md)** | The game. Loop, economy, monster, estate, progression, scope. | Start here. |
| **[TECH-SPEC.md](TECH-SPEC.md)** | Curator AI and the networked physics handoff, to implementation detail. | Building either. |
| **[AUDIO-SPEC.md](AUDIO-SPEC.md)** | The loudness model, proximity voice, the Curator's sound, mix, accessibility. | Before Milestone 0 — audio gates the earliest test. |
| **[ART-DIRECTION.md](ART-DIRECTION.md)** | The look: straight-faced house, ridiculous crew. Flat-shaded low-poly, light as the whole budget. | Before any asset work. |
| **[LEVEL-SPEC.md](LEVEL-SPEC.md)** | Estate module contract, prerequisite chains, pinch points, and the 10-check validation suite. | Authoring any wing. |
| **[ECONOMY.md](ECONOMY.md)** | Van capacity, slot costs, value bands, quota curve, and the simulation results behind them. | Tuning anything with a number in it. |
| **[sim/haul_sim.py](sim/haul_sim.py)** | Monte Carlo of the haul loop. Runs in seconds, no dependencies. | Before changing van capacity or appraiser cost. |
| **[sim/chain_sim.py](sim/chain_sim.py)** | Full-night sim with weight classes, crew labour, and depth gating. | Before changing the quota curve, crew size, or the apex. |
| **[sim/integrated.py](sim/integrated.py)** | Haul loop coupled to the tuned Disturbance model, so scan noise is derived rather than assumed. | Before changing scan noise or the appraiser's payoff. |
| **[sim/curator_attention.py](sim/curator_attention.py)** | Attention weighting, flicker, hand-off override, sacrifice plays. | Before touching aggro selection. |
| **[sim/disturbance.py](sim/disturbance.py)** | Disturbance escalation across six scenarios — baseline, levers off, greedy, careful, and two poltergeist Static budgets. | Before changing decay, gain, or tier thresholds. |
| **[sim/curse_test.py](sim/curse_test.py)** | The curse value side and the tail-risk ruin curve. | Before changing curse multipliers or ruin_k. |
| **[sim/work_gate.py](sim/work_gate.py)** | The only model that gates depth on **work** rather than a clock, as D-20 requires. Reproduces D-20's crew-size inversion under the clock gate and removes it under the work gate. Added R24. | Before trusting any result whose mechanism runs through crew time. |
| **[sim/greed_dial.py](sim/greed_dial.py)** | The first model with BOTH the levers and the money, so pulling a lever costs throughput. Answers whether greed is priced. Added R22. | Before touching Disturbance levers, lights, or the curse. |
| **[sim/scan_risk.py](sim/scan_risk.py)** | Sweeps scan *rate* and tests whether a super-linear scan cost helps. It does not — see D-22. Also where the optimal ~0.2–0.3 rate that recalibrated the Phase 2 gate comes from. | Before touching the appraiser. |
| **[sim/validate_estate.py](sim/validate_estate.py)** + **[sim/estates.py](sim/estates.py)** | The ten-check estate validator, plus a clean sample wing and a deliberately-broken one. | Before a wing enters the pool. |
| **[sim/check_estates.py](sim/check_estates.py)** | Mutation test: one targeted fault per check, asserting all ten can actually *fail*. Added R18, when V7 turned out to be undetectable and the validator had no entry point at all. | After touching any check. |
| **[sim/check_drift.py](sim/check_drift.py)** | Fail-closed drift checker: 133 checks over 59/59 constants in `tuning.json`, across all four implementations (Python, both JS prototypes, C#). | After changing any constant, anywhere. |
| **[STACK.md](STACK.md)** | Verified package status, licensing, and the one dependency risk. | Before Milestone 0. |
| **[DECISIONS.md](DECISIONS.md)** | Every non-obvious call, why, and what would disprove it. | Before re-opening any settled argument. |
| **[LOOP_LOG.md](LOOP_LOG.md)** | Sixteen rounds of build-and-find, newest at the bottom. **Where the log and a spec disagree, the log is newer.** | Before trusting any number in any spec. |
| **[BUILD-PROMPT.md](BUILD-PROMPT.md)** | The self-contained brief for shipping this on Steam: phases, exit criteria, non-negotiables. | Starting a build session. |
| **[TRANSFER.md](TRANSFER.md)** | The move to the Mac, what to run first, and why the shipping build comes off the PC. | Setting up a machine. |
| **[tuning.json](tuning.json)** | Canonical constants. Every implementation is checked against it by `sim/check_drift.py`. | Before changing any number anywhere. |
| **[proto/index.html](proto/index.html)** · **[proto3d/index.html](proto3d/index.html)** | Two browser prototypes: the original loop test, and the first-person one built after the direction correction in `LOOP_LOG.md` R15. Loop tests, not the product. | Before writing anything. |
| **[unity/Assets/Scripts/Core/](unity/Assets/Scripts/Core/)** | The verified rules in C#, `UnityEngine`-free. 41 assertions in `unity/tests/CoreTests`. | Porting or changing a rule. |
| **[sim/check_core.py](sim/check_core.py)** | Mutation test for the C# core: reverts each rule and requires a guard to notice. Added R19, when eight rules — including multiplicative attention — turned out to be unguarded. Needs the .NET SDK. | After changing any rule. |
| **[IMPROVE-PROMPT.md](IMPROVE-PROMPT.md)** | The prompt for a hardening pass over existing work. | Between build phases. |
| **[ITERATION-PROMPT.md](ITERATION-PROMPT.md)** | The older design-iteration prompt. Superseded for build work by BUILD-PROMPT.md. | Design passes only. |

**Reading order for someone new:** `DESIGN.md` §1–6 → `DECISIONS.md` (skim the FIRM entries)
→ `LOOP_LOG.md` (newer than every spec; where the log and a doc disagree, the log wins) →
`BUILD-PROMPT.md` if you're building, or whichever spec covers what you're writing.

## The five ideas everything else hangs off

1. **The monster is an anti-thief.** Aggro follows loot, not people — so danger is a physical
   object you can hand to someone else. (`DESIGN.md` §6)
2. **Greed is the difficulty slider.** The game never forces danger, it prices it. Every
   scary moment is one the crew chose, out loud, together. (`DESIGN.md` §4)
3. **Information costs safety.** Appraising tells you an item's value *and* its curse, takes
   three stationary seconds, and is louder than sprinting. (`DESIGN.md` §4.4)
4. **Aggro is visible to everyone.** Frost crawls up the item and the marked player's
   flashlight dims to 60%. "If your light is dimming, it's coming for you."
   (`TECH-SPEC.md` §A7)
5. **One number, three systems.** Every noise event has a single Loudness value driving
   Curator hearing, Disturbance gain, and player audibility. (`AUDIO-SPEC.md` §1)

## What's solid and what isn't

**Solid enough to build on:** the loop and economy; the Curator's state machine and attention
model; the physics ownership protocol; the loudness model; the decision log.

**Specified and tested in simulation:** the economy and the core rules, by eight Python models,
a 31-assertion C# cross-check of the ported core, and a fail-closed drift checker over 59/59
canonical constants — which between them overturned most of what this project first believed.
The four that mattered earliest:

- The appraiser beats blind hauling by **+4.4%** at 14 van slots — but that is the *clock-gated*
  figure, and R25 re-measured it on `sim/work_gate.py`: **selective scanning is worth +1.8%,
  always-scanning +13.9%**, and ADAPTIVE stops being the best strategy. (`LOOP_LOG.md` R8/R20/R25 / `ECONOMY.md`
  §9.1 — the +84% first reported was placeholder-noise, and the +31% that replaced it a
  slot-accounting reroll bug) — and dies entirely between
  24 and 32 slots. Van capacity is the master constant.
- Scan *duration* barely matters. **Noise has to carry the whole cost of appraising**;
  making the scan slower will not create tension.
- The quota curve is calibrated and now *verified* — 94% / 73% / 56% / 42% pass across the four
  nights (R27; `chain_sim.py` had been running the retracted curve until then).
- The original quota curve had **no shape**: nights 1–3 passed 100% of the time and night 4
  passed 1%. Recalibrated against simulated earnings.
- Depth must unlock on **work, not wall-clock**, or bigger crews earn *less* — a bug that
  would have been near-impossible to diagnose from playtest reports.

**Deliberately rough:** joint tuning values (guesses — a week of hands-on iteration decides
the game's feel); and all art *production* — the lighting and fog pass, the ~8-material class
kit, the ~40-object prop kit. The direction is settled in `ART-DIRECTION.md`; none of it is
built, and none of its values are tuned.

**Recently answered:** dead-player downtime — the genre's standing unsolved problem. The dead
join the collection: free movement, permanent sight of the Curator, curse-sight, and a small
budget of poltergeist verbs whose every use raises Disturbance. The dead player should be the
*loudest* person in voice chat, not the quietest. Unproven in play. (`DESIGN.md` §5.1)

## The next three things

1. **Two people, a door, spatial voice.** A fifteen-minute test that tells you whether the
   foundation of this game feels right. Nothing else buildable this early is worth as much.
   (`AUDIO-SPEC.md` §8)
2. **Vendor the Dissonance↔FishNet bridge**, then hold it to the two-day rule. If voice isn't
   working end-to-end in two days, switch to Mirror and don't relitigate it. (`STACK.md`)
3. **Milestone 2, with instrumentation.** Hauling junk to a van with friends, no monster.
   Two kill criteria, both written down in advance: is it already funny, and do players
   actually use the appraiser? (`DESIGN.md` §11)

~~Verify the stack~~ — done, see [STACK.md](STACK.md). FishNet, Dissonance, and FMOD all
check out; the bridge between the first two does not, hence item 2.

## The honest scope

Milestones 0–6 is 9–18 months for a small team. **Milestones 0–2 — the part that tells you
whether the game is worth making — is 2–4 months, and that's the only thing worth committing
to right now.**
