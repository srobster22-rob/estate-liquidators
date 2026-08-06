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

**Design foundation, plus a playable prototype and a tested rules core.** No Unity project
yet. There is a single-player browser prototype of the loop (`proto/index.html`), the verified
rules ported to engine-free C# (`unity/Assets/Scripts/Core/`) with a 31-assertion cross-check
against the Python models, and three green test gates — see `TRANSFER.md`.

These documents are deliberately unfinished — built to be extended, argued with, and revised
as playtests come back. Nothing here is precious except the things marked FIRM in the decision
log, and even those state their own falsification conditions.

## The documents

| Doc | What it is | Read it when |
|---|---|---|
| **[DESIGN.md](DESIGN.md)** | The game. Loop, economy, monster, estate, progression, scope. | Start here. |
| **[TECH-SPEC.md](TECH-SPEC.md)** | Curator AI and the networked physics handoff, to implementation detail. | Building either. |
| **[AUDIO-SPEC.md](AUDIO-SPEC.md)** | The loudness model, proximity voice, the Curator's sound, mix, accessibility. | Before Milestone 0 — audio gates the earliest test. |
| **[ART-DIRECTION.md](ART-DIRECTION.md)** | The look: straight-faced house, ridiculous crew. Flat-shaded low-poly, light as the whole budget. | Before any asset work. |
| **[LEVEL-SPEC.md](LEVEL-SPEC.md)** | Estate module contract, prerequisite chains, pinch points, and the 12-check validation suite. | Authoring any wing. |
| **[ECONOMY.md](ECONOMY.md)** | Van capacity, slot costs, value bands, quota curve, and the simulation results behind them. | Tuning anything with a number in it. |
| **[sim/haul_sim.py](sim/haul_sim.py)** | Monte Carlo of the haul loop. Runs in seconds, no dependencies. | Before changing van capacity or appraiser cost. |
| **[sim/chain_sim.py](sim/chain_sim.py)** | Full-night sim with weight classes, crew labour, and depth gating. | Before changing the quota curve, crew size, or the apex. |
| **[sim/scan_risk.py](sim/scan_risk.py)** | The appraiser: why a tail risk kills it and room variance saves it. | Before touching anything about scanning. |
| **[sim/hiding.py](sim/hiding.py)** | Concealment: whether run / hide / stash / hand off are four decisions or one. | Before touching §8.1 or the search state. |
| **[sim/validate_estate.py](sim/validate_estate.py)** | The 12-check estate validator, with a self-test. `python sim/validate_estate.py` | Authoring or reviewing any wing. |
| **[STACK.md](STACK.md)** | Verified package status, licensing, and the one dependency risk. | Before Milestone 0. |
| **[DECISIONS.md](DECISIONS.md)** | Every non-obvious call, why, and what would disprove it. | Before re-opening any settled argument. |
| **[ITERATION-PROMPT.md](ITERATION-PROMPT.md)** | The reusable prompt for continuing this work. | Next session. |

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

**Specified and partly tested:** the economy and the encounter, by ten simulations that between
them overturned seven things this project believed.

- The appraiser's edge dies entirely between 24 and 32 van slots. **Van capacity is the master
  constant.** The edge itself has been revised four times as the model got honest (+84% →
  +31% → +6% → +4.4%); it reaches **+12.2%** once rooms vary in how varied they are.
- **Scanning's payoff is a property of the room, not a constant** — it's `0.6 × spread ×
  mean`, so a house of evenly-priced rooms makes the signature verb a habit. Scanning only
  high-variance rooms earns +12.2%; scanning a random 25% of rooms earns +4.6%; scanning the
  *wrong* rooms earns −1.9%. The gap between those is the skill.
- Scan *duration* barely matters. **Noise has to carry the whole cost of appraising**;
  making the scan slower will not create tension.
- The original quota curve had **no shape**: nights 1–3 passed 100% of the time and night 4
  passed 1%. Recalibrated against simulated earnings.
- Depth must unlock on **work, not wall-clock**, or bigger crews earn *less* — a bug that
  would have been near-impossible to diagnose from playtest reports.
- **Stashing loot to break a chase was a free reset of the entire threat system** — a
  guaranteed save, because the 20s quiet timer always outlasted the Curator's search. Fixed by
  making the *search* ragged (8–24s, re-rolled) rather than the timer shorter; 75% save rate,
  and all four responses to being hunted now have a region where they're correct.

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
