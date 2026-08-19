# ESTATE LIQUIDATORS

[![CI](https://github.com/srobster22-rob/estate-liquidators/actions/workflows/ci.yml/badge.svg)](https://github.com/srobster22-rob/estate-liquidators/actions/workflows/ci.yml)

**▶ [Play the prototypes in your browser](https://srobster22-rob.github.io/estate-liquidators/)** — no install, no build step.

**Co-op horror extraction for 4 players.** You're a cleanout crew emptying a dead collector's
estate before sunrise. Every object has a dollar value, the van has finite space, and the
quota is in dollars, not items.

The thing in the house isn't a predator — it's a **curator**. It doesn't hunt intruders, it
retrieves property. Its attention follows the most valuable thing currently leaving the
house, which means it follows *whoever is holding it*.

You can get rid of the monster by handing the vase to your friend.

---

## Status

**Design foundation, plus the parts that could be proved without an engine.** Eight Python
simulations, a C# core pinned against their numbers, and two playable browser prototypes —
but no Unity project yet, and none of the netcode that the product actually rests on.

These documents are deliberately unfinished — they're built to be extended, argued with, and
revised as playtests come back. Nothing here is precious except the things marked FIRM in the
decision log, and even those state their own falsification conditions.

Two simulations between them overturned four things this project believed, and the headline
number was retracted twice: the appraiser's edge over blind hauling went **+84% → +31% → +6%**
as each measurement found a bug in the one before it. That history is in `LOOP_LOG.md`, and it
is the most useful thing here.

**There is also a second, unrelated game in this repository** — see `bonkhorde/`.

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
| **[bonkhorde/](bonkhorde/)** | A different game entirely: a 3D survivors-like in one HTML file, with its own measurement harness. | It stands alone. |

**Reading order for someone new:** `DESIGN.md` §1–6 → `DECISIONS.md` (skim the FIRM entries)
→ whichever spec covers what you're building.

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

- **`proto3d` was drawing the entire house at about 13% grey.** Which reads as "atmospheric
  night game" until you measure it: centre-of-frame luminance across four headings came back
  **4, 34, 34 and 78 out of 255**. It was not broken, it was lit to almost nothing — a black
  rectangle in a browser tab in daylight, and I nearly published it that way. Two causes. The
  spotlight's `smoothstep(uCone, uCone + .28, …)` had an upper bound of **1.08**, and a cosine
  cannot exceed 1, so the middle of the beam topped out at 80% of full and never reached it.
  And the whole scene was multiplied by 1.5 over base colours around 0.23. Raising the
  multiplier alone traded one failure for its opposite — 2.4× lifted the mid-ground and blew
  near walls out to a flat yellow disc with no detail in it. A Reinhard rolloff
  (`lin / (lin + 0.55)`) fixes both ends: a lit interior now reads 31/255 where it read 4, and
  a wall at arm's length reads 131 instead of clipping.
- **The two prototypes had no tests at all.** They are the only playable evidence this half of
  the repository has, and nothing checked they still booted. `proto-tests.js` asks the three
  questions a prototype fails silently: does it boot, does its loop advance state, and can you
  steer it. `proto3d` failed the third — its mouse-look was gated on holding pointer lock, the
  identical bug found in BONKHORDE, so in any embed it booted, the Curator walked, WASD worked
  and the camera never turned again. Verified by reverting the fix: 16/17 with the old code,
  17/17 with the new. Both prototypes now run in CI, at 20 checks.

  And the suite I wrote to catch that shipped without the one check that would have caught the
  *lighting*: it asserted "draws to a live WebGL context", which is not the same claim as "you
  can see the house". Then the clipping assertion I added passed at **3.7/255** — because the
  probe walked the player out of the building and measured the void. Both fixed; both are the
  same mistake this file keeps recording, which is that an assertion is only worth what it
  would have failed on.
- The appraiser's edge over blind hauling is **+6%**, not the +84% first reported. That first
  figure used a placeholder for scan noise; the second, +31%, survived a reroll bug. Both are
  in `LOOP_LOG.md` with the measurement that killed them. A 6% edge is small enough that
  whether the appraiser earns its slot in the design is still an open question, and it is the
  one worth arguing about.
- Van capacity is the master constant: the appraiser's advantage dies entirely between 24 and
  32 slots, whatever its size at 14.
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
