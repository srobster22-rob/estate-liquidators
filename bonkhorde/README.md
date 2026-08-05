# BONKHORDE

**A 3D survivors-like in one HTML file.** Vampire Survivors' auto-attacking horde loop, played
from Megabonk's third-person camera. No engine, no build step, no dependencies — open
`index.html` in a browser and it runs.

You never attack. Every weapon fires on its own cooldown at its own targets. The only verb is
**positioning**, and every death is a positioning mistake.

![BONKHORDE](screenshot.png)

---

## Play it

```
open bonkhorde/index.html          # macOS
xdg-open bonkhorde/index.html      # Linux
```

`WASD` move · `MOUSE` orbit camera · `SPACE` jump · `ESC` pause.

Survive twenty minutes. Four bosses arrive at 5:00, 10:00, 15:00 and 19:00. Coins persist
between runs and buy permanent upgrades.

**The clock does not win the run.** THE FINAL BONK arrives at 19:00, and if it is still alive
at 20:00 the timer stops mattering — you go to **sudden death**, the horde thickens for as
long as you stall, and victory means killing it. You have four minutes.

**Bosses have moves.** Every ability keeps the same contract: a wind-up you can see, a danger
zone drawn on the ground, then the hit. A red ring says *where*, a second ring closing inward
says *when*. Dodging halves the damage a boss deals — measured, not asserted.

| | |
|---|---|
| **THE GRAVELORD** 5:00 | `slam` — a ring under your feet, then a stomp. One lesson, taught once. |
| **THE LANDLORD** 10:00 | `evict` — scatters lingering zones that eat the arena, plus slams. |
| **MR. TEETH** 15:00 | `charge` — marks a lane, pauses, then runs it at 4.4× speed. |
| **THE FINAL BONK** 19:00 | all of the above plus `spokes`, a radial burst you dodge between. |

![Sudden death](screenshot-final.png)

---

## What's in it

| | |
|---|---|
| **8 weapons** | melee arc, orbiters, homing bolts, shockwave, mortar, chain lightning, damage aura, ground hazards |
| **8 evolutions** | each weapon maxed + a specific passive at rank 3 unlocks a replacement form |
| **8 passives** | damage, speed, cooldown, pickup radius, armour, HP, +projectiles, crit |
| **5 enemy types + 4 bosses** | with a spawn director that reweights the mix over 11 phases |
| **elite variants** | from minute 6, rising to ~1 in 5 — crowned, larger, 3.2× HP, 5× XP |
| **4 boss abilities** | slam, evict, charge, spokes — telegraphed, dodgeable, worth dodging |
| **5 characters** | different starting weapon and stat profile; one unlocks by surviving 10:00 |
| **9 permanent upgrades** | bought with coins, persisted to `localStorage` |

Roughly 1,500 lines of JavaScript, no libraries.

## How it's built

**Rendering.** Hand-rolled WebGL. Everything dynamic is an axis-aligned box, and all of them
go into a single vertex buffer that is uploaded once and drawn in one call — ~2,300 boxes per
frame at peak. The alternative, one `drawElements` per object, costs more in driver overhead
than the entire simulation does. Terrain is a separate static buffer: a 60×60 heightfield with
a checkerboard tint, because a flat untextured plane gives you no sense of speed.

**Simulation.** Enemies are bucketed into a uniform spatial grid, rebuilt each frame. Every
weapon query (nearest target, everything in radius) and enemy-vs-enemy separation runs against
it. Without that, separation is O(n²) at n≈400 and the horde collapses into one stacked
super-enemy that is both invisible and unkillable.

**Audio.** A ~40-line Web Audio synth. No files.

**Cost.** The simulation is **0.4 ms/frame at 300 enemies** — a ~2,400 fps ceiling — so the
frame budget is entirely rendering. (The harness reports ~10 fps under load, but that is
SwiftShader rasterising in software; the sim number is the one that transfers to real
hardware.) Measured, not assumed: `window.__g.perf()` splits the two.

---

## Verification

The game ships with a headless harness that drives it through a `window.__g` QA hook — the
same pattern as `proto3d/` in the parent repository.

```bash
npm i playwright && npx playwright install chromium

node test.js              # 73 checks: boot, every weapon, every evolution, every
                         # enemy, elites, boss abilities, every character, a full
                         # run, the sudden-death gate, death, saves, render
node balance.js 6 both            # [trials] [first|vet|both] [char,char]
node balance.js 12 vet intern,scrap   # higher n on two characters
```

`test.js` covers each of the 8 weapons and all 8 evolutions individually, spawns every enemy
type and boss, plays a complete run to the 20:00 victory, verifies the player can actually
die, and checks that `localStorage` survives a reload. **73 passing.**

### Balance is measured, not guessed

`balance.js` runs an autopilot to death, many times over, and reports where runs actually end.
Tuning a survivors-like by feel is how you ship something unwinnable in week one, so the
difficulty curve here is a measurement. Current state, 6 trials per cell:

```
                     median    worst     best   lvl  kills  evos  clears
FIRST RUN   intern    05:15    04:01    06:11    13    720   0.0     0/6
  (no perm  scrap     05:03    04:15    05:15    12    645   0.0     0/6
  upgrades) spark     04:47    03:52    05:03    11    590   0.0     0/6
            ox        05:19    04:09    05:21    12    694   0.0     0/6
            ghoul     05:49    04:10    10:40    17   1242   0.2     0/6

VETERAN     intern    15:07    05:27    21:15    35   4564   1.7     2/6
  (all      scrap     06:07    05:15    10:08    17   1116   0.5     0/6
  upgrades  spark     20:56    06:28    22:08    42   5979   2.0     2/6
  bought)   ox        21:11    05:54    24:00    46   7145   2.5     2/6
            ghoul     07:47    06:23    16:18    23   2111   0.3     0/6
```

Which is the shape the genre wants. First-run deaths cluster hard at **4–6 minutes** (11 of 12
in the histogram) and never once clear, though a lucky run occasionally reaches the final boss
at 21:17 — so the ceiling is visible without being available. A maxed shop makes twenty minutes
*reachable* and clears **6 of 30**; the medians above are mostly runs that got to sudden death
and lost there, which is the fight being the fight.

**Read the total, not the rows.** At n=6 against a bimodal outcome the per-character cells are
mostly noise, and this project has now proved that the hard way — see the last finding below.

Note the veteran medians read past 20:00 because sudden death runs the clock on. Survival time
is no longer the same thing as winning.

That harness has overturned sixteen things this build believed:

- **Skitters moved at 6.2 against a player speed of 6.3.** You could not outrun the horde,
  which deletes the only verb the genre has. Kiting has to be possible or the game is just
  attrition with extra steps.
- **The first autopilot was wrong, and it looked right.** It maximised distance from the
  crowd, survived a plausible-looking 2:50 — and killed 13 things in 90 seconds against 200
  spawns, because weapons only reach 4–8m and it never let anything close. A bot that runs
  away measures nothing. It now orbits at knife-edge range.
- **Gems accumulated without bound.** Long-range weapons kill outside pickup radius, so a
  20-minute run finished holding **15,006** uncollected gems, every one of them iterated and
  drawn every frame. Capping the count and *merging* the most distant gem into each new one
  bounds the cost and leaves the XP economy untouched. Levelling past minute 15 went from
  frozen at 46 to reaching 60.
- **The terrain never rendered once.** Triangle winding was clockwise seen from above, so
  `CULL_FACE` discarded the entire map and what looked like dark ground was the background
  clear colour. Three rounds of "the lighting is too dark" were chasing a geometry bug.
- **Skitters were 52–74% of the horde against a nominal weight of ~15%.** A skitter roll
  spawned a pack of eight but charged the director for one, so every mix weight in the phase
  table was a fiction. Packs now cost what they deliver.
- **Nothing ever despawned.** Enemies you had comfortably outrun kept following forever, so
  the alive-count tracked *cumulative spawns* rather than spawn rate, and minute six was a
  wall no build could pass.
- **The horde could not reach you.** Separation force summed over every neighbour with no
  cap, so past ~400 enemies it beat pursuit outright and the crowd settled into an
  equilibrium ring at **9–11m** — nothing within 8m of the player, ever, for the entire back
  half of a run. Standing still got *safer* the bigger the horde grew, which is precisely
  backwards. Clamping separation below the slowest enemy's speed brought contact back to
  3–8m.
- **The clock handed you the win.** THE FINAL BONK spawned at 19:00 and 20:00 ended the run
  regardless, so the game's climax could be skipped by running away for sixty seconds.
- **Enemy damage never scaled.** HP scaled all game and contact damage did not, so late
  enemies were tanky and harmless — a maxed veteran could stand in the horde at minute 18.
- **Cooldown reduction compounded past everything else.** Character × shop × METRONOME took
  THE SPARK to 0.446, a 2.24× fire rate multiplying an already multiplicative damage stack.
  Floored at 0.58.
- **The difficulty curve was invisible.** Making the endgame ×14.5 HP left minute 18 looking
  identical to minute 8 while nothing died — which reads as *your weapons got worse*, not
  *these are tougher*, and a player who cannot see the difficulty cannot adapt to it. Elites
  give the curve a face. They are deliberately close to difficulty-neutral (clears went 10/30
  → 9/30); the change was legibility, and the measurement confirms it did not smuggle in a
  balance shift.
- **The slam was impossible to dodge, by seven centimetres.** A 7.0m radius against a 1.05s
  wind-up: a player at full speed running straight out covers **6.93m**. Not a mechanic — a
  damage tax wearing a telegraph, and one you would only ever experience as *unfair* rather
  than diagnose. Arithmetic caught it in one line. Now 5.6m / 1.15s, leaving ~2m of margin
  (and ~0.9m for THE OX, who is slower and tankier in exchange).
- **Every boss cast the same ability.** `spawnBoss` assembled its `def` field by field and
  never copied `ai`, so `BOSS_KIT[undefined]` fell through to slam-only — for all four bosses,
  silently, while the feature looked like it worked.
- **`freezeSpawns` did not freeze bosses.** It stopped the horde but not the director, so a
  test that skipped to 15:00 quietly had three bosses on the field and attributed a blend of
  their kits to one of them.
- **The elite HP check measured species mix.** Comparing median HP of elites against normals
  compares a population whose elite half is mostly skitters (8 base HP) with a normal half
  that is mostly spitters (34). It reported "elite 283 vs normal 331" while elites were in
  fact 3.24× tougher. Normalise the variable you are *not* asking about.
- **The clears metric silently broke.** It counted `t >= 1199`, which was synonymous with
  victory right up until sudden death let losing runs reach 22:00 — and then reported them as
  wins. The instrument has to be re-checked every time the thing it measures changes shape.

Eleven of the sixteen were found by measurement rather than by playing, which is the argument
for having the harness. Three came from actually looking at a screenshot, which is the
argument against trusting the harness alone. And **four were the harness lying about itself** —
the two broken autopilots, the clears metric, the elite probe, plus `freezeSpawns` not
freezing what it claimed. Every time the shape of the thing being measured changed, the
instrument needed re-checking, and every single time it did not get re-checked until it
produced a number too strange to ignore.

**And then I tuned against noise anyway.** One n=6 row showed THE SCRAPPER collapsing to 0/6
clears, so I softened boss damage in response — and the re-measure had THE GHOUL fall from 5/6
to 0/6, which a damage *cut* cannot cause. It was variance, in a table whose own caption says
"read the total, not the rows". A higher-n run settled it: at n=12 THE SCRAPPER is genuinely
weak (0 clears in 24 veteran runs, p≈0.001) but THE GHOUL's swing was nothing. Writing down
the caveat does not protect you from it.

**The autopilot itself was wrong twice before it was useful**, and both times it looked fine:
v1 maximised distance and scored a plausible 2:50 while killing almost nothing; v2 summed
repulsion vectors, which cancel to zero when you are ringed, so it stood perfectly still in
the middle of the horde and died. v3 samples 20 headings and commits to the best one. A
measuring instrument that produces confident numbers is not the same as a correct one — and
the same trap caught the clears metric later, for the same reason.

---

## Not done

- **Nobody has played this with hands.** Every number above is the autopilot's opinion, and it
  is a plausible player rather than a good one — a human reads incoming waves and plans routes
  across the whole arena, which it cannot. Expect the real curve to sit longer than the table
  says, and expect the veteran tier to look too easy once someone competent tries it.
- **THE SCRAPPER cannot close a run.** Zero clears in 24 veteran runs, against 3/12 for THE
  INTERN — but with near-identical medians (10:08 vs 10:16) and a best of 20:54. So it reaches
  the finale and cannot kill it: a damage problem, not a survival one. It starts with CALTROPS,
  whose single-target output against a boss is poor, and it levels slower for it (1.1 evolutions
  vs 1.8). Measured and left alone deliberately — fixing it means reworking CALTROPS' single-
  target profile, which is its own round.
- No mobile/touch input. Pointer lock and WASD only.
- Weapon variety is broad but shallow — 8 weapons with one evolution each. The genre expects
  more, and the data tables are the easy part to extend.
- No run modifiers, no stage variety, no unlock tree beyond one character.
