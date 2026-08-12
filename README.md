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

**Design foundation plus a playable single-player prototype, under test.** The documents are
deliberately unfinished — built to be extended, argued with, and revised as playtests come
back. Nothing here is precious except the things marked FIRM in the decision log, and even
those state their own falsification conditions.

What runs, and how to check it:

```bash
node proto3d/qa.mjs               # 159 checks driving the real build in headless Chromium
node proto3d/qa.mjs -r 5           # run it five times; anything flaky is reported as flaky
python3 sim/check_drift.py        # 147 constants agree across four implementations
python3 sim/check_counts.py --qa 159   # the numbers in these docs are the real ones
python3 sim/validate_estate.py    # 10 checks x 2 sample estates
node proto3d/dump-estate.mjs --seeds 12 --out /tmp/e && \
  python3 sim/validate_estate.py --estate /tmp/e/*.json   # generated estates vs the contract
dotnet run --project unity/tests/CoreTests   # 31 assertions pinning C# to the sims
```

**[STATUS.md](STATUS.md) is the honest inventory** — what the prototype implements, what it
doesn't, and what the checks cannot tell you.

Open `proto3d/index.html` in a browser to play it; the estate is generated per
run and `?seed=12345` reproduces a specific house. The Unity build does not exist yet; the
prototypes are where the rules are being proved.

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
| **[STATUS.md](STATUS.md)** | Spec against build: what exists, what doesn't, what the checks can't tell you. | First, if you want to know where this actually is. |
| **[proto3d/index.html](proto3d/index.html)** | Playable first-person prototype: a generated house, a crew, an apex, four nights. Raw WebGL, no dependencies. | Before arguing about feel. |
| **[proto3d/qa.mjs](proto3d/qa.mjs)** | Headless QA driving that build in Chromium. Every rule this project calls FIRM has a check here. | After changing any rule. |
| **[BUILD-PROMPT.md](BUILD-PROMPT.md)** | Self-contained brief for shipping this on Steam: phases, exit criteria, non-negotiables. | Starting a build session. |
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

**Specified and partly tested:** the economy, by two simulations that between them overturned
four things this project believed.

- The appraiser beats blind hauling by **+14%**, and the right number of candidates to scan
  is **two of four** — better than scanning none *and* better than scanning all. The earlier
  +84%, +31% and +6% figures each priced a different, cruder axis (`ECONOMY.md` §11).
- Scan *duration* barely matters. **Noise has to carry the whole cost of appraising**;
  making the scan slower will not create tension.
- The original quota curve had **no shape**: nights 1–3 passed 100% of the time and night 4
  passed 1%. Recalibrated against simulated earnings.
- Depth must unlock on **work, not wall-clock**, or bigger crews earn *less* — a bug that
  would have been near-impossible to diagnose from playtest reports.

**Deliberately rough:** joint tuning values (guesses — a week of hands-on iteration decides
the game's feel); material and prop dressing; lighting standards; anything about art. In the
prototype specifically: the crew are haul bots rather than players, there is one hand-authored
wing, and nothing has weight — no dolly, no two-man carry, no piano.

**Recently answered:** dead-player downtime — the genre's standing unsolved problem. The dead
join the collection: free movement, permanent sight of the Curator, curse-sight, and a small
budget of poltergeist verbs whose every use raises Disturbance. The dead player should be the
*loudest* person in voice chat, not the quietest. Unproven in play. (`DESIGN.md` §5.1)

## The next three things

1. **Open `proto3d/index.html` and play it for twenty minutes.** Everything claimed below
   R16 in the loop log is a simulation result or a headless assertion. Seventy checks say
   the rules behave; nothing says the game is fun, and no amount of further iteration can
   substitute for the first honest opinion.
2. **Two people, a door, spatial voice.** A fifteen-minute test that tells you whether the
   foundation of this game feels right. Nothing else buildable this early is worth as much.
   (`AUDIO-SPEC.md` §8). The prototype now has audio, but it is single-player and
   synthesised — it proves the loudness model drives a mix, not that proximity voice works.
3. **Milestone 2, with instrumentation.** Hauling junk to a van with friends, no monster.
   Two kill criteria, both written down in advance: is it already funny, and do players
   actually use the appraiser? (`DESIGN.md` §11)

~~Verify the stack~~ — done, see [STACK.md](STACK.md). FishNet, Dissonance, and FMOD all
check out; the bridge between the first two does not, hence item 2.

## The honest scope

Milestones 0–6 is 9–18 months for a small team. **Milestones 0–2 — the part that tells you
whether the game is worth making — is 2–4 months, and that's the only thing worth committing
to right now.**
