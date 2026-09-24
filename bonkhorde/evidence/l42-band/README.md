# L42: the band

L35's frame at 12:00 read as "a band on the horizon behind a wall of damage
numbers, not bodies pressing in", and its `next:` carried the question twice:
does the crowd stand at twenty metres because of what the kit is allowed to
reach? Measured before anything was typed, on the L41 build.

## The instrument

`band.js`: the pinned god-bot run (seed 9) brought to 7:00, 12:00 and 17:00 by
the bot, then a twenty-second window in one of two arms from the same state -
the bot keeps KITING, or the player STANDS (bot off, no input). Every step:
the live bodies' distances (nearest, p10/p50/p90, the share of body-time
within 3, 8 and 20 m), bodies at contact (`d <= rad + .75`), every body that
vanished and at what distance (the 80 m cull separated), and the game's own
measured kill radius `killR`. A frame at the end of each window
(`band-<arm>-<t>.png`). `band2.js` is the same split by enemy kind, with the
damage ledger (`hurtBy()`) over the window. `crowd-count.js` reads the crowd
director's own counters at four times.

## What it read

```
seed 9, 20 s windows          alive   nearest   body distance p10/p50/p90   <=8 m  <=20 m   at contact   died   death p50 (p90)   killR
 7:00  kiting                  87.7    4.8 m       9.7 / 17.5 / 31.0 m        5%     60%        0.10       167     5.7 (18.1) m     7.4
 7:00  standing                91.7    4.4 m      10.0 / 15.5 / 29.5 m        6%     68%        0.00       163     4.0 ( 6.6) m     4.3
12:00  kiting                 121.3    3.7 m      10.9 / 24.5 / 42.7 m        5%     35%        0.17       262     6.4 (20.7) m     7.8
12:00  standing               119.7    4.3 m       9.2 / 19.6 / 33.4 m        7%     52%        0.04       265     4.3 ( 7.9) m     4.2
17:00  kiting                 238.0    1.7 m       9.6 / 20.9 / 35.6 m        7%     47%        0.86       406     7.3 (23.0) m    15.0
17:00  standing               247.1    1.5 m       9.5 / 18.7 / 32.4 m        7%     55%        1.38       399     4.5 ( 8.7) m     4.4
```

By kind, standing at 12:00 (`band2.txt` has all four windows):

```
kind       alive   distance p10/p50/p90   <=20 m   died in 20 s   death p50 / p90
skitter     62.1    7.7 / 19.6 / 31.2 m     52%        211           4.3 /  7.7 m
spitter     28.3   14.1 / 18.8 / 34.2 m     61%          1          23.0 / 23.0 m
brute       16.1    9.2 / 25.2 / 46.0 m     38%         10           4.0 /  6.5 m
runner      12.2    9.4 / 19.6 / 31.3 m     51%         43           4.0 /  8.1 m
```

The ledger over the same windows: at 12:00 the kiting bot took 106 contact
and 78 spit; the standing player took 0 contact and 294 spit. At 17:00,
268 contact / 134 spit / 52 hazard kiting against 54 / 493 / 0 standing.

## What it means

- **The walkers press in.** They die at a median of 4 to 7 m - 4.0 to 4.5 m
  when the player stands - which is the kit's real kill radius (`killR` 4.2 to
  4.4 standing; the 7 to 15 the bot reads is its own movement). At 17:00 a
  standing player has 1.4 brutes at contact on average and the nearest body
  1.5 m away. Nothing stops at twenty metres and stays there.
- **What stands at twenty metres is two things, neither of them the kit's
  reach.** The walkers in transit: a body spawns on the ring just past the
  screen's edge (30 to 38 m), walks in at 2 to 5 m/s and dies within a second
  of arriving, so nearly all of its life is spent between 10 and 30 m and the
  living population's median sits near 20 m by construction. And the
  spitters, who hold at their 22 m range by design (p50 16 to 19 m, six in ten
  inside 20 m, one death in twenty seconds).
- **The bench's kiting bot takes MORE contact than a player who stands still**
  (106 against 0 at 12:00, 268 against 54 at 17:00), because it runs through
  bodies, and about half the spit, because it moves. A human sits between the
  two arms.
- So L35's reading was the numbers wall (taken down in L37) in front of a
  transit population, and there is nothing to type: the design does what it
  says - the field is always full of bodies coming, and they die at your
  feet. The frames: `band-stand-0720.png` has brutes at the player's flank
  and corpses underfoot; `band-kite-0720.png` the same field with the bot on
  the move.

## A side reading, for later

`crowd-count.js`: the crowd director sent 9 bodies by 5:00, 317 by 12:00 and
no more by 17:00, and was HELD (the field already at or over its wanted
count) 41,952 times; the standing count exceeds L35's want table at every
sample (61 against 45 at 5:00, 120 against 75 at 12:00, 238 against 105 at
17:00). On this seed the ambient director alone keeps the field, and the
crowd is a floor it never falls to. Whether that is true across seeds and
characters, and whether the ambient rate moved since L35, is a question for
a balance round, not this one.

## Files

- `band.js`, `band.txt`; `band2.js`, `band2.txt`; `crowd-count.js`.
- `band-kite-*.png`, `band-stand-*.png`: the six frames.
