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
node dps.js 4                     # per-weapon boss/crowd DPS bench, n=4
```

`test.js` covers each of the 8 weapons and all 8 evolutions individually, spawns every enemy
type and boss, plays a complete run to the 20:00 victory, verifies the player can actually
die, and checks that `localStorage` survives a reload. **73 passing.**

### Every weapon, on the two axes that decide a run

`dps.js` benches all eight weapons at rank 5 and evolved, inside the actual
sudden-death fight — horde present, gems pulling you back in, autopilot kiting —
and attributes boss damage separately from crowd damage. Boss DPS decides whether
you can *close* a run; crowd DPS decides whether you survive to try.

```
RANK 5          boss dps   crowd dps        EVOLVED        boss dps   crowd dps
bat                   11        1194        MEGABONK            297        2402
skulls                21        1371        CAROUSEL            306        2342
bolt                  33        1170        BOLTSTORM           686        4358
pulse                 38        1507        EARTHQUAKE          490        2923
mortar               127        2120        BOMBARDIER          555        2863
zap                  161         488        TESLA COIL          537        1261
aura                  22        1160        PLAGUE              223        2150
caltrops              93        1796        SCORCHED EARTH     1099        2996
```

Specialists are intentional — ZAP is a boss weapon that barely dents a crowd,
SKULLS the reverse. What the bench is for is catching the ones that are not
specialists but simply broken.

### Balance is measured, not guessed

`balance.js` runs an autopilot to death, many times over, and reports where runs actually end.
Tuning a survivors-like by feel is how you ship something unwinnable in week one, so the
difficulty curve here is a measurement. Current state, 6 trials per cell:

```
                     median    worst     best   lvl  kills  evos  clears
FIRST RUN   intern    04:24    03:48    04:36    11    504   0.0     0/6
  (no perm  scrap     04:05    03:59    16:16    16   1325   0.3     0/6
  upgrades) spark     05:03    03:31    05:23    11    598   0.0     0/6
            ox        05:11    04:02    05:23    12    696   0.0     0/6
            ghoul     04:31    04:02    09:14    13    771   0.0     0/6

VETERAN     intern    05:35    05:14    12:23    18   1250   0.3     0/6
  (all      scrap     21:20    05:11    22:09    44   6464   3.0     1/6
  upgrades  spark     21:22    11:18    22:40    54   8275   3.3     3/6
  bought)   ox        13:35    07:50    21:48    36   4705   1.5     1/6
            ghoul     20:41    05:39    21:50    44   6346   2.7     3/6
```

Which is the shape the genre wants. First-run deaths cluster hard at **4–6 minutes** (11 of 12
in the histogram) and never once clear, though a lucky run occasionally reaches the final boss
at 21:17 — so the ceiling is visible without being available. A maxed shop makes twenty minutes
*reachable* and clears **8 of 30**; the medians above are mostly runs that got to sudden death
and lost there, which is the fight being the fight.

**Read the total, not the rows — and be suspicious of the median.** The outcome is bimodal: you
die around minute six, or you go the distance. A median over six runs just reports which side
of that split got the fifth sample, and it swings wildly — THE SCRAPPER measured 15:20 and 06:31
on *identical* configurations twenty minutes apart. The clear count over the whole table is the
only number here worth acting on.

Note the veteran medians read past 20:00 because sudden death runs the clock on. Survival time
is no longer the same thing as winning.

That harness has overturned nineteen things this build believed:

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
- **CALTROPS was fine, and the round meant to fix it was built on a guess.** The previous
  round's write-up asserted its "single-target output against a boss is poor" — asserted, never
  measured. The bench says it is the **best evolved boss weapon in the game** (1099 dps) and
  second-best at rank 5. The plausible-sounding diagnosis had been sitting in the README as a
  fact for a whole round.
- **ZAP could not participate in a boss fight.** Chain lightning arced to the *nearest* body,
  which in a horde is always trash, so it landed **1 boss dps** against a median of 55 — not a
  weak weapon, a weapon that never showed up. Making the first link seek threat (boss > elite >
  nearest) took it to 161.
- **The DPS bench was wrong on first build, and confidently.** v1 measured a lone boss with the
  autopilot on and reported exactly 0.0 for skulls, pulse and caltrops. That was not DPS, it was
  *reach*: with one enemy and no gems on the floor the bot has no reason to go near it, so it
  fled and every player-centred weapon whiffed forever.
- **The clears metric silently broke.** It counted `t >= 1199`, which was synonymous with
  victory right up until sudden death let losing runs reach 22:00 — and then reported them as
  wins. The instrument has to be re-checked every time the thing it measures changes shape.

Fourteen of the nineteen were found by measurement rather than by playing, which is the
argument for having the harness. Three came from actually looking at a screenshot, which is the
argument against trusting the harness alone. And **five were the harness lying about itself** —
the two broken autopilots, the clears metric, the elite probe, `freezeSpawns` not freezing what
it claimed, and the DPS bench measuring reach instead of damage. Every time the shape of the
thing being measured changed, the instrument needed re-checking, and every single time it did
not get re-checked until it produced a number too strange to ignore.

**The DPS table is not the run.** Trimming MORTAR by 23% looked obviously right — it was 4.5×
the median boss DPS *and* the best crowd DPS, dominating both axes. It dropped veteran clears
from 6/30 to **1/20** and cut the median run almost in half. A per-weapon bench tells you what a
weapon does; it cannot tell you how much of the game is standing on it. Settled at −12%, and
only the run data could say so.

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
- **Half the evolution partners buy no damage.** Committing to an evolution means feeding a
  specific passive, and four of the eight — `plating`, `magnet`, `heart`, `boots` — give armour,
  pickup radius, HP and move speed respectively. The other four give damage, crit, projectiles
  and cooldown. So half the roster ramps its power while chasing an evolution and half does not,
  against the same reward. Measured and documented; re-pairing or giving the four a small
  offensive rider is its own round.
- **THE SCRAPPER is still the weakest character**, though much less so than reported last round
  (median 10:08 → 15:20, evolutions 1.1 → 1.6 after the weapon work). Its HP penalty was
  *isolated and cleared* — patching `hp` back to 1.0 changes nothing at all (1/10 clears either
  way, identical median), so the deficit is not survivability. It starts with CALTROPS, whose
  evolution partner is BOOTS, which is one of the four that buys no damage.
- No mobile/touch input. Pointer lock and WASD only.
- Weapon variety is broad but shallow — 8 weapons with one evolution each. The genre expects
  more, and the data tables are the easy part to extend.
- No run modifiers, no stage variety, no unlock tree beyond one character.
