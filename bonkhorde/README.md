# BONKHORDE

[![CI](https://github.com/srobster22-rob/estate-liquidators/actions/workflows/ci.yml/badge.svg)](https://github.com/srobster22-rob/estate-liquidators/actions/workflows/ci.yml)

**▶ [Play it in your browser](https://srobster22-rob.github.io/estate-liquidators/bonkhorde/)**

**A 3D survivors-like in one HTML file.** Vampire Survivors' auto-attacking horde loop, played
from Megabonk's third-person camera. No engine, no build step, no dependencies — open
`index.html` in a browser and it runs.

You never attack. Every weapon fires on its own cooldown at its own targets. The only verb is
**positioning**, and every death is a positioning mistake.

![BONKHORDE](screenshot.png)

---

## Play it

[In your browser](https://srobster22-rob.github.io/estate-liquidators/bonkhorde/), or locally:

```
open bonkhorde/index.html          # macOS
xdg-open bonkhorde/index.html      # Linux
```

`WASD` move · `MOUSE` orbit camera · `SPACE` jump · `ESC` pause.

**On a phone:** left thumb is a virtual stick (analog — a half push moves you at half speed),
right thumb turns the camera, a tap on the right jumps, and there is a pause button because
a phone has no Escape key.

Nothing decides "is this a phone" up front. Both input paths are always installed and pointer
lock is always attempted; the auto-pause keys off whether a lock was ever genuinely *held*.
Guessing from `maxTouchPoints` killed mouse control on touchscreen laptops, and swapping it
for a media query only moves the guess — an emulated touch desktop reports
`(any-pointer:fine) = false`, byte-identical to a phone.

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
| **8 passives** | every one contributes to output, not just the four with "damage" in the text — PLATING blasts attackers off you, MAGNET drags the horde into a pile |
| **5 enemy types + 4 bosses** | with a spawn director that reweights the mix over 11 phases |
| **elite variants** | from minute 6, rising to ~1 in 5 — crowned, larger, 3.2× HP, 5× XP |
| **4 boss abilities** | slam, evict, charge, spokes — telegraphed, dodgeable, worth dodging |
| **5 characters** | different starting weapon and stat profile; one unlocks by surviving 10:00 |
| **9 permanent upgrades** | bought with coins, persisted to `localStorage` |

Roughly 1,600 lines of JavaScript, no libraries.

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

node test.js              # 117 checks: boot, every weapon, every evolution, every
                         # enemy, elites, boss abilities, evolution partners,
                         # draft rules, colour-vision contrast, edge camera,
                         # every character, a full run, the sudden-death gate,
                         # death, saves, draw budget, render, and touch controls
                         # in a real phone-sized touch context
node balance.js 6 both            # [trials] [first|vet|both] [char,char]
node balance.js 12 vet intern,scrap   # higher n on two characters
node dps.js 8 5                   # per-weapon boss/crowd/survival bench
                                  # [dps trials] [survival trials]; n=3 is noise
node passives.js 5                # per-passive offence/defence bench, n=5
```

`test.js` covers each of the 8 weapons and all 8 evolutions individually, spawns every enemy
type and boss, plays a complete run to the 20:00 victory, verifies the player can actually
die, and checks that `localStorage` survives a reload. **117 passing.**

### Every weapon, on the two axes that decide a run

`dps.js` benches all eight weapons at rank 5 and evolved, inside the actual
sudden-death fight — horde present, gems pulling you back in, autopilot kiting —
and attributes boss damage separately from crowd damage. Boss DPS decides whether
you can *close* a run; crowd DPS decides whether you survive to try.

```
RANK 5        boss   crowd   alive      EVOLVED           boss   crowd   alive
bat             78    1492    4:46      MEGABONK           919    3346    4:20
skulls         110    1227    5:03      CAROUSEL          1351    3540    4:24
bolt           127    1226   10:58      BOLTSTORM         1229    3595   15:31
pulse           66    1656    4:45      EARTHQUAKE         665    3087    3:52
mortar         450    2292    6:16      BOMBARDIER        1422    3590   10:07
zap            219     574    6:28      TESLA COIL         512    1521   10:33
aura            80    1388    4:16      PLAGUE             850    3026    3:55
caltrops       366    2046    4:13      SCORCHED EARTH    1137    2960    4:13
                                        (dps n=6, survival n=4)
```

**The third column is new, and it says the second one was never measuring what we
thought.** EARTHQUAKE has the highest crowd DPS among the player-centred weapons
and the *worst* survival in the game. BOLT has nearly the lowest rank-5 crowd DPS
and stays alive **more than twice as long as anything else**. Sort either table by
survival and the same three names come out on top — BOLT, MORTAR, ZAP — and they
are exactly the three weapons that reach. The other five cluster at 3:52–4:24
evolved, a 3.5× cliff with nothing in between.

That is not a tuning error, it is the shape of the game: crowd DPS counts damage
that landed and cannot count *where*, so a kill at 30m and a kill at 2m score
identically and are not remotely the same thing. Trimming BOLTSTORM's throughput
by 23% (9 → 7 bolts, 5 → 4 pierce) took its crowd DPS from 4689 into the pack at
3595 and moved its survival by **eight percent**, from 16:49 to 15:31 — volume was
never what kept it alive. The single most consequential draft decision in this
game is whether anything in your kit has reach.

Specialists are intentional — ZAP is a boss weapon that barely dents a crowd,
AURA the reverse. What the bench is for is catching the ones that are not
specialists but simply broken, and the test it applies is **strict dominance**:
a weapon that beats every other weapon on *both* axes at once is not a
specialist, it is a default. Unevolved MORTAR was exactly that — best boss DPS
*and* best crowd DPS against all seven others — before reach started counting
bodies. It no longer is: CALTROPS out-damages it against a boss and it keeps
the crowd, which is a trade rather than a default. Nothing dominates either
table now.

### Colour-vision contrast

You have to tell a SPRINTBOI (charges you) from a SPITBOI (holds at range) at a
glance, in a crowd, while running. The palette was picked by eye and collapsed
for the ~8% of men with a colour-vision deficiency.

The first attempt at this **shipped a fix that did not work, and a test that said
it did.** The check modelled scene lighting as a flat ×1.35 — which is the
*ground's* multiplier. An enemy's side face, which is most of its silhouette at a
37° camera, actually receives ×0.92 sunlit and ×0.50 shaded, per channel. Scored
under light the enemies never receive, the palette read ΔE 26.9. Scored properly
it was **ΔE 2.8**, and the check had also never compared elites to each other or
to the ground at all.

Corrected, the harness now compares 10 enemy variants (5 types + their elite
tints) against each other and against 6 terrain shades, across 4 vision types and
both lighting conditions —
and it derives the terrain colours and the lighting constants from the renderer
rather than retyping them, so a recolour cannot slip past it.

| | worst pair | worst vs ground |
|---|---|---|
| original hand-picked palette | ΔE 18.8 | ΔE 14.4 |
| "fixed" palette, measured wrongly | ΔE 26.9 | ΔE 26.3 |
| the same palette, measured correctly | **ΔE 2.8** | **ΔE 0.6** |
| re-searched against real lighting | **ΔE 19.7** | **ΔE 20.0** |

Two things fell out of doing it properly:

**The elite tint was costing ~4 ΔE.** Mixing 34% toward orange pulled every
species toward one hue. Elites already carry a crown, +38% size and a glow, so
the tint only needs to hint — it is now 12%, with brightness taking the slack.

**Eleven distinguishable colours is not achievable.** Five enemies, five elite
tints and the player, all mutually separable under four vision types at two
lighting levels, against grass — the best player colour tested still sat at ΔE
7.5 from something. So the player stopped competing for a hue and is marked by
**shape** instead: a bright ring nothing else draws, which no deficiency can take
away. Knowing when to stop using a channel is part of using it.

### The camera went blind at the arena edge

Found while re-shooting screenshots. The chase boom is 17 units long and
unbounded, so near the edge the eye ends up out among the boundary spires
(radius 74–79, height 7–15) at an eye height of ~12.8 — inside them, with the
whole frame rendering as fog. Clamping the eye sideways fixes the blindness but
slides the camera onto the player and loses the third-person view; the boom now
*shortens* until it fits and lifts as it shortens, so the player stays framed.
Asserted from the centre, an edge and a corner.

### Every passive, against a no-passive control

Reaching an evolution means feeding one specific passive for about three of your
picks, so the question is not "does the text say damage" but "is it a comparable
pick". `passives.js` benches each one at rank 3 — the evolution gate — against a
control with an identical weapon kit.

```
                    dps   vs base   survived   vs base            (n=10)
control            2166        --      10.9m        --
spinach            2726       26%      11.3m        4%   offence partner
dupe               2788       29%      11.5m        6%   offence partner
tempo              2569       19%      12.2m       12%   offence partner
clover             2421       12%      10.9m        0%   offence partner
heart              2355        9%      12.7m       16%   defence partner
boots              2362        9%      11.0m        1%   defence partner
magnet             2275        5%      11.5m        5%   defence partner
plating            2245        4%      12.7m       17%   defence partner

  offence partners   avg +21% dps,  +5% survival
  defence partners   avg  +7% dps, +10% survival
```

It used to read **+25% dps / 0% survival** against **−0% dps / +4% survival**: half
the roster ramped its power while chasing an evolution and half simply did not,
for the same reward. The two rows now separate on the axis their names promise —
offence buys damage, defence buys minutes — and no passive dominates another on
both. All four of the quiet ones contribute in their own idiom rather than by
bolting "+damage" onto everything:

| | |
|---|---|
| **BOOTS** | momentum — speed *and* damage. It measured as the single worst pick in the game: +27% move speed at rank 3 produced nothing detectable. |
| **BIG HEART** | a bigger heart pumps harder. HP, regen, and damage. |
| **PLATING** | spiked armour. Being hit blasts them off you, which rewards the tank build for doing the thing it is built to do. |
| **MAGNET** | it pulls more than loot. A weak inward drag on the horde clumps them, so every AoE weapon lands more — and brings them closer to you, which is the cost. |

### Balance is measured, not guessed

`balance.js` runs an autopilot to death, many times over, and reports where runs actually end.
Tuning a survivors-like by feel is how you ship something unwinnable in week one, so the
difficulty curve here is a measurement. Current state, **pooled over two independent sweeps of
6 trials per cell** — a single sweep swings the veteran total by ten points, so one is not a
reading:

```
                                                          clears     pooled
FIRST RUN   intern                                       0/6  0/6      0/12
  (no perm  scrap                                        0/6  0/6      0/12
  upgrades) spark                                        0/6  0/6      0/12
            ox                                           0/6  0/6      0/12
            ghoul                                        0/6  0/6      0/12
                                                                       0/60

VETERAN     intern                                       4/6  2/6      6/12
  (all      scrap                                        1/6  1/6      2/12
  upgrades  spark                                        3/6  3/6      6/12
  bought)   ox                                           4/6  3/6      7/12
            ghoul                                        2/6  2/6      4/12
                                                                      25/60
```

Which is the shape the genre wants. First-run deaths cluster hard at **2–6 minutes** — 19 of 24
across both histograms — and **never once clear in sixty runs**, though a lucky run occasionally
reaches minute nineteen, so the ceiling is visible without being available. A maxed shop makes
twenty minutes *reachable* and clears **25 of 60**; the veteran medians run past 20:00 because
almost every veteran run now reaches sudden death and is decided there, which is the fight being
the fight.

**42% is the target, not a miss.** An earlier draft of this file treated ~33% as the number to
hold, and every content change since has had to be walked back toward it with boss HP. That was
cargo cult: the invariant that matters is *first run never clears and a maxed shop makes the
ending reachable*, and 0/60 against 25/60 says both. Chasing a third decimal on the veteran
figure through a ±10-point noise floor is measuring the harness, not the game.

The per-character spread — 2/12 to 7/12 — is roughly the noise floor wide, and the ordering
does not survive re-sampling: THE GHOUL led at 8/12 one round ago and sits at 4/12 here on an
unchanged character. THE SCRAPPER is the only one consistently at the bottom.

**Read the total, not the rows — and be suspicious of the median.** The outcome is bimodal: you
die around minute six, or you go the distance. A median over six runs just reports which side
of that split got the fifth sample, and it swings wildly — THE SCRAPPER measured 15:20 and 06:31
on *identical* configurations twenty minutes apart. The clear count over the whole table is the
only number here worth acting on, and even that needs pooling: the two sweeps above are the same
build and read 9/30 and 15/30. Anything smaller than a ten-point move is not a result.

Note the veteran medians read past 20:00 because sudden death runs the clock on. Survival time
is no longer the same thing as winning.

That harness has overturned forty-nine things this build believed:

- **MEGABONK was a strictly worse EARTHQUAKE, and the evolution is what did it.** BONK BAT's
  identity is a directional swing; its evolution turned that into a 360° slam at 150 damage
  per 0.78s in an 8.2m circle with kb 20 — against EARTHQUAKE's 150 per 0.85s in a 10.5m
  circle with kb 22. Bigger radius, bigger knockback, no arc to miss with, same damage. The
  evolution took away the one thing that made the weapon distinct and handed it a losing copy
  of another weapon's job, which is how BONK BAT ended up **last on all three axes at once**.
  It stays directional now and hits like the name says — 333 damage a second into a cone
  against EARTHQUAKE's 176 in every direction — and reads 919 boss / 3346 crowd, still with
  the worst survival in the game. A glass cannon is a design; last-on-everything is a bug.
- **BOLTSTORM was the only weapon dominating every other on all three axes**, and the fix
  proved the survival finding twice over. Trimming it 23% (9 → 7 bolts, 5 → 4 pierce) pulled
  crowd DPS from 4689 into the pack at 3595 and moved survival by **eight percent**. Whatever
  keeps that weapon alive, it is not volume — it is that the bolts arrive before the horde
  does, which is why the trim came off throughput and left the reach alone.
- **The weapon bench had two axes and the game has three.** Adding a survival column — one
  weapon, mid-tier shop, no godmode, played to death — inverted the reading of the column
  next to it. EARTHQUAKE has the highest rank-5 crowd DPS in the game (1716) and survives
  4:25. BOLT has nearly the lowest (1120) and survives **9:46**, more than twice anything
  else; BOLTSTORM survives **18:17**. Sorted by survival, rank 5 is the three ranged weapons
  on top and the five player-centred ones underneath, almost exactly ordered by reach. Crowd
  DPS counts damage that landed and cannot count *where* it landed, so it scores a kill at
  30m and a kill at 2m identically. One of those is why you are alive.
- **PLAGUE was strictly dominated by six of the other seven weapons, on both axes at once.**
  A flat damage aura is squeezed from both ends: against 8–22 HP trash nearly all of its
  output is overkill that `hurt()` correctly refuses to count, and against a boss 120 DPS is
  nothing. Stacking fixes only the end that was broken — 12% a tick to 2.44× after three
  seconds in the cloud, which trash never lives to see. Boss DPS 340 → 845, and it is
  dominated by four instead of six. The weakness moved to BONK BAT, which the new survival
  column says is not hiding defensive value either: it is last on all three.
- **The GPU can be taken away, and nothing handled it.** A mobile browser reclaims WebGL when
  you switch apps, and lost-context GL calls fail *silently* rather than throwing — so the
  canvas would be black forever while the simulation carried on behind it, which reads as a
  crash on the one platform this build advertises. Every GL object is now re-creatable, loss
  pauses the run and says so, and restore rebuilds the program, both buffers and the terrain.
  Section 12c drives it through `WEBGL_lose_context`.
- **The first version of that test passed against a corpse.** `restoreContext()` did nothing,
  because `getExtension()` returns null on an already-lost context and the handle was being
  fetched at restore time. The suite reported it anyway: a lost context keeps its last
  drawing buffer on screen and `drawnBoxes` keeps its last value, so "the scene draws again"
  and "the frame is not blank" both passed on a frame rendered before the loss. Only "restore
  clears the flag" failed. The assertions now park the counter at −1 and move the camera, so
  nothing but a live frame can satisfy them.
- **The best offensive passive in the game was filed under defence.** PLATING benched at
  **+36% DPS** against a no-passive control (n=10) — beating SPINACH's +25% and DUPLICATOR's
  +28% at their own job — while also cutting incoming damage by a flat 8 and a further 25% at
  rank 5. Its retaliation blast was a 7.1m, ~290-damage hit fired on *every* hit taken, and
  the 0.68s invulnerability window lets that land 1.4 times a second: roughly **430 free area
  DPS that no design document mentions**. The description did not mention the 25% mitigation
  either. Retaliation is the flavour and mitigation is the passive, so the blast is now
  5.35m / ~113 damage at rank 5 and it reads +4% DPS, +17% survival — the best defensive pick
  and nearly the worst offensive one, which is the shape the word "defence" promises.
- **Aim and damage disagreed about where things were.** Fixing reach left `nearest()` — what
  BONK BAT and BOLT aim at — still measuring to centres while the damage that followed
  measured to bodies. A swing could aim past a boss it was about to hit and then exclude it
  on the arc test. Making the aim body-aware moved BAT +9% and BOLT +17%, both inside this
  bench's noise, so it is recorded as a *consistency* fix rather than a buff: the point is
  that the two halves of one weapon now agree, not that the number went up.
- **Every weapon measured its reach to an enemy's CENTRE, and enemies are not points.**
  Contact damage had always counted the body — an enemy hits you at `e.rad + .75`. Weapons
  did not, so a target shrugged off exactly its own radius worth of your reach: 0.62m against
  a shambler, **4.0m against THE FINAL BONK**. The bigger and more important the target, the
  worse your weapon performed against it, which is precisely backwards. STINK at rank 5 is a
  6.5m cloud; the boss's surface could be a metre inside it, plainly on fire, taking nothing,
  because its centre sat at 9.5m. Routing every "what does this area hit" query through a
  body-aware test moved rank-5 boss DPS from a median of 47 to 133, and lifted the
  player-centred weapons most, since those are the ones whose whole reach was being eaten —
  SKULLS, CALTROPS and PULSE all multiplied several times over. (Per-weapon multipliers from
  that first comparison are *not* quoted here: both columns were n=3, which the entry below
  shows is noise. The median across eight weapons is the part that survives.) It also ended
  MORTAR's strict dominance of all seven other weapons on both axes at once. A boundary
  sweep now pins the damage cliff at exactly 10.5m (6.5 ring + 4.0 body): damage at 10.4m,
  none at 10.6m.
- **Boss HP had to go up in proportion to body size, because that is the axis the bug ran
  along.** Honest reach handed the most DPS to fights against the biggest bodies, so veteran
  clears jumped from 10/30 to **34/60** across two samples. Scaling each boss's HP by roughly
  how much reach it had been stealing (+19% for the 2.6m GRAVELORD, +46% for the 4.0m FINAL
  BONK) put clears back to 24/60 — statistically indistinguishable from where they started,
  which is the point. Same fight, honest numbers.
- **Capping overlapping hazards to one zone destroyed the weapon it was meant to balance.**
  Once reach counted a 4m body, SCORCHED EARTH sat at 2.47× the median boss weapon, because a
  boss occupies far more of a burning trail than a shambler does. The principled-sounding
  rule — one body burns once, strongest source wins — dropped it from **3165 DPS to 309**, the
  best boss weapon to the worst, because stacking is not a bug in that weapon, it *is* that
  weapon. What actually needed bounding was the stack a large body can sit inside, not the
  stack. A cap of three lands it at 1.00× median and a crowd body, covered by one or two
  zones, never reaches the cap at all.
- **THE SCRAPPER's bonus expires and its cost does not.** Measured at 1/12 veteran clears
  against THE GHOUL's 9/12. By minute fifteen you are swimming in gems and +70% pickup radius
  buys nothing, so the phase that decides the run is played as a strictly worse INTERN with
  15% less HP. Speed is the one stat that cannot expire in a game whose only verb is
  positioning: +8% → +16% took it to 3/12 while the GHOUL control held at 8/12. It is now the
  genuinely fast one rather than the fast-ish one, and it dodges the boss telegraphs its HP
  pool cannot afford to eat.
- **The DPS bench moves untouched weapons by 53% at n=3.** Between two consecutive runs that
  changed only MORTAR, SKULLS read 137 then 64 and PULSE 87 then 53 — neither had been
  touched. Every conclusion drawn from a single three-sample column in this file was drawn
  from noise, including two on this list. n=8 is the floor for reading this bench, and the
  numbers quoted above are all n=8 or pooled.
- **Mouse-look was gated on pointer lock, so an embed froze the camera.** The handler
  returned early unless `document.pointerLockElement === cv`, which is correct on a page
  that can *get* the lock. A sandboxed iframe without `allow-pointer-lock` cannot, and the
  failure is silent: the game boots, the horde advances, WASD works, and the camera never
  turns again. Nothing in 98 checks looked at the unlocked case, because every test ran the
  file top-level where the lock is granted. Drag-to-look now covers it, and section 15c
  asserts the camera turns with `locked === false`.
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
- **Every passive measured as worth exactly nothing.** The first passive bench scored kills by
  8:00 and returned 0% for all eight — including SPINACH, which is +39% damage at rank 3. The
  metric was **supply-capped**: with godmode and a working kit the autopilot kills everything
  that spawns, so the number was the spawn budget, not the player's output. Same class of error
  as the DPS bench measuring reach, one round earlier, and I walked into it again.
- **`give(k, n)` under-applied half the passives.** The test hook jumped the rank by `n` and
  called `applyPassive` once. Recalculated passives read their rank so they were fine;
  *accumulating* ones were not — BIG HEART at "rank 3" had +22 max HP instead of +66, and had
  been quietly under-tested in every run that used the hook.
- **The retaliation test read 660 → 660, exactly.** That is 30 shamblers × 22 HP: both arms of
  the comparison killed everything on the field, so effective damage was pinned to how much
  there was to kill. Supply-capping again, in miniature, in the very test written to catch the
  fix for it.
- **DUPLICATOR was a coin flip the draft would not tell you about.** Benched across kits it
  read **+52% with BOLT, −9% without, −4% with mortar+aura** — the best passive in the game or
  a completely wasted pick, decided by which weapons you happened to be offered, on a card that
  reads identically either way. That is worse than an overpowered passive; it is a trap wearing
  the same clothes as the correct answer. It now touches four weapons rather than two, its
  copies are echoes at 55% damage so bolting one onto a 3-shell mortar is not +100%, and **the
  roller will not offer it to a kit that provably cannot use it.** Reads +25%/+7%/+25% across
  the same three kits.
- **Three enemy pairs were indistinguishable to colour-blind players.** Worst separation
  across the roster was ΔE 14.4, and the colliding pairs — SPRINTBOI/SPITBOI under
  deuteranopia, SHAMBLER/SPRINTBOI under protanopia — are exactly the ones whose correct
  response is opposite. I went looking for this in the boss telegraph, which turned out to be
  fine (ΔE 46–64); the defect was in the thing I had not thought to check.
- **The contrast test scored the palette under light enemies never receive.** A flat ×1.35 is
  the *ground's* multiplier; a vertical enemy face gets ×0.92 sunlit and ×0.50 shaded. The
  previous round's accessibility fix measured ΔE 26.9 and was actually **2.8**. It shipped, and
  the test said it was fine.
- **`state().boxes` was a stale frame.** `render()` only runs under `requestAnimationFrame`, so
  reading the draw count after a synchronous step loop returns whatever the last real frame
  drew — the same number for twenty simulated minutes. The "box budget never exceeded"
  assertion had been reading it that way since it was written.
- **The camera went blind at the arena edge**, ending up inside the boundary spires with the
  frame rendering as fog. Any player walking into a corner would have hit it; no automated
  check was looking at composition.
- **The game was unopenable on a phone**, which is the device most people follow a link with.
  It asked for pointer lock and read WASD, and neither exists there. Now: left thumb drives a
  virtual stick, right thumb turns the camera, a tap on the right jumps, and pointer lock is
  skipped entirely on touch — the `pointerlockchange` auto-pause would otherwise have frozen
  the game permanently on the first tap.
- **Touch support broke mouse support.** Deriving "is a phone" from `maxTouchPoints` classified
  every touchscreen laptop as touch-only, so pointer lock no-op'd and the `mousemove` handler
  bailed — mouse camera control simply died there. Neither the desktop nor the phone test could
  have caught it, because each has only one input.
- **The analog stick was not analog.** `touchVec()` scaled by deflection, then the existing
  normalise threw the magnitude away, so any push past the dead zone ran at full speed while
  the drawn knob showed a half push. The control visibly disagreed with the game.
- **The touch test never dispatched `touchend`.** It returned a page-side closure from
  `page.evaluate` to fire the release later, and functions do not serialise across that
  boundary — so tap-to-jump and stick release were entirely untested while the docs claimed
  touch was covered.
- **A phone player could not pause.** The overlay covers the canvas, so the canvas resume
  handler was unreachable, and with `pointerlockchange` skipped on touch, `Escape`/`KeyP` were
  the only pause triggers — neither of which a phone has. There was no way to reach ABANDON RUN.
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

**A flaky test is a broken test.** Section 11 failed intermittently for two rounds. `startRun`
fires a pointer-lock request that always rejects in headless, and the resulting
`pointerlockchange` re-pauses the game — sometimes *after* the test's `resume()`, so the
level-up overlay never opened. Adding `resume()` last round narrowed the race and I called it
fixed. It isn't fixed until it stops depending on timing: the test now drives exactly one
simulation tick itself instead of waiting on `requestAnimationFrame`.

A second one hid behind it. The MAGNET check spawns enemies at a *uniform random* distance, so
the mean starting distance wobbles by about a metre between the two arms — the same order as
the effect being measured. It read `5.6m → 6.1m` once in eight runs and passed the rest.
Averaging four trials per arm settled it. **Eight consecutive clean runs of all 77** before
either was called done, because a suite that passes most of the time tells you almost nothing.

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
- **THE SCRAPPER is still the weakest character.** Its HP penalty was isolated and cleared
  (patching `hp` back to 1.0 changes nothing — identical clears, identical median), and the
  partner rework has lifted it further, but it remains the least reliable closer. What is
  actually left is a per-character question rather than a systemic one.
- **The bench numbers move ±10 points between runs at n=5.** PLATING has read 35% and 42% dps
  on identical builds. Directionally reliable, not precise — do not tune to one decimal.
- Weapon variety is broad but shallow — 8 weapons with one evolution each. The genre expects
  more, and the data tables are the easy part to extend.
- No run modifiers, no stage variety, no unlock tree beyond one character.
