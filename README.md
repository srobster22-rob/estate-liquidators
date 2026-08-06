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

**Design foundation. No code yet.** These documents are deliberately unfinished — they're
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
| **[STACK.md](STACK.md)** | Verified package status, licensing, and the one dependency risk. | Before Milestone 0. |
| **[DECISIONS.md](DECISIONS.md)** | Every non-obvious call, why, and what would disprove it. | Before re-opening any settled argument. |
| **[ITERATION-PROMPT.md](ITERATION-PROMPT.md)** | The reusable prompt for continuing this work. | Next session. |

**Reading order for someone new:** `DESIGN.md` §1–6 → `DECISIONS.md` (skim the FIRM entries)
→ whichever spec covers what you're building.

## Before this game — the portfolio

Everything above assumes the concept is already chosen. These two are for the step before
that, and they're independent of Estate Liquidators — take them anywhere.

| Doc | What it is |
|---|---|
| **[GAMES-PROJECT-PROMPT.md](GAMES-PROJECT-PROMPT.md)** | Generate 40 game concepts, each with a falsifiable bet and a one-day test that could kill it. Coverage quotas, a banned list, ranking by cost-to-disprove, and a mandatory graveyard. |
| **[GAME-CONCEPTS.md](GAME-CONCEPTS.md)** | That prompt, run once, then corrected and verified over five passes. 40 live concepts in 9 families, a ranked top eight, 31 rejections with reasons. **All 47 cards checked against the market — 7 were games that already exist**, 2 of them in the top eight. The judgement-based rejections were audited too: no verdict reversed, six reasons wrong, one load-bearing on a live card, and one concept recovered. |

`concepts-sim/provenance.py` is the first kill test from that document actually **run** —
deterministic, no dependencies, ~1s. It does not meet its kill condition, and it found an
emergent mechanic nobody designed in: the optimal "is this a forgery?" threshold *rises* with
expertise, because expertise means recognising the honest repairs a novice reads as fakes.

Estate Liquidators is roughly the bar those concepts were written against — *aggro follows the
most valuable object leaving the house* is what "one mechanical bet, stated so it could be
wrong" looks like once it survives. Note that **Removals** (`GAME-CONCEPTS.md` #6) costs
nothing to evaluate: Phase 1 of this project is already running its kill test.

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

**Specified and partly tested:** the economy, by two simulations that between them overturned
four things this project believed.

- The appraiser beats blind hauling by **+84%** at 14 van slots — and dies entirely between
  24 and 32 slots. Van capacity is the master constant.
- Scan *duration* barely matters. **Noise has to carry the whole cost of appraising**;
  making the scan slower will not create tension.
- The original quota curve had **no shape**: nights 1–3 passed 100% of the time and night 4
  passed 1%. Recalibrated against simulated earnings.
- Depth must unlock on **work, not wall-clock**, or bigger crews earn *less* — a bug that
  would have been near-impossible to diagnose from playtest reports.

**Deliberately rough:** joint tuning values (guesses — a week of hands-on iteration decides
the game's feel); material and prop dressing; lighting standards; anything about art.

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
