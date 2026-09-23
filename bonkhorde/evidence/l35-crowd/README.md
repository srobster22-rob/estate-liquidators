# L35: the crowd (bodies arriving faster than the kit clears them)

L33 measured the field under play: 8 to 20 bodies alive at any moment, because
a levelled kit kills everything inside about 25 m in about a second. L34 showed
that body HP does not change that. This round adds the third option L34 named.
The director now keeps a standing crowd topped up at a rate the kit cannot
clear, and the table's own sends are left as they were.

## What the crowd is

- **A floor, not a rate.** `CROWD_AT` sets how many ordinary bodies should be
  alive at a given time: 20 at 2:00, 45 at 4:30, 75 at 8:00, 105 at 13:00 and
  135 at 18:20, interpolated between those points. Whenever the field is under
  that count, the director adds bodies at up to `CROWD_RATE` (200/s, banked
  for 0.25 s) from the usual spawn ring, 30 to 38 m out.
- **Walkers only** (`CROWD_WALK`). The first version drew from the phase mix,
  spitters included. Six spitters standing in a ring of eighty make a firing
  line, and early deaths went from 1/36 to 7/36. With walkers only, early
  deaths are back at 1/36.
- **Paid for once.** At most `CROWD_SHARE` (10%) of the table's sends are
  matched with crowd bodies that carry XP. Every other crowd body is free and
  pays no gem, coins or heal. The level at 10:00 stays at 48 to 49 (control
  47 to 48), so the extra bodies do not buy a stronger kit.
- **Off while a boss is up, and off before 2:00.** The boss fights and the
  opening are unchanged.

## The field (crowd_sweep.js: verbRun, levels on, pinned seed 9, minutes 6-16)

```
arm  char    lvl(10:00)  mean alive  peak  hurt/min  death m med/p90   kills
off  intern   73(48)        8.3       27     34.3     23.1/33.7        9,525
off  scrap    71(47)       12.8       38     59.3     20.9/32.3        9,334
off  spark    73(48)       19.5       53    105.2     18.9/27.8        8,756
off  ox       74(47)       18.8       41     10.7     21.8/30.1        9,163
on   intern   74(48)       87.1      125     38.5     23.2/30.4       83,554
on   scrap    76(48)       73.7      120     44.7     24.7/32.2      105,478
on   spark    73(49)       84.7      120     52.9     15.4/26.5       28,013
on   ox       75(48)       91.6      129     70.4     17.0/22.3       30,738
```

The standing crowd rose ten- to fourfold at the same level. Bodies still die a
median of 15 to 25 m out. What changed is that about ninety of them are
standing there at any moment, where before there were ten to twenty.

## The frames (frames.js: god bot, intern, pinned seed 9, crowd on vs off)

```
          alive / on screen       frame boxes      horde boxes (share)
t        off        on           off     on        off        on
0:30     14/14      14/14        1069    1057      81 (8%)    66 (6%)
3:00     25/25      33/33        1259    1391      55 (4%)    31 (2%)
7:00      3/3       67/60        2558    3921       6 (0%)   586 (15%)
12:00    10/10     105/105       2036    3632      13 (1%)   265 (7%)
17:00    14/14     114/109       2182    4694      74 (3%)  1158 (25%)
```

`on-*.png` and `off-*.png` are those ten frames. By eye:

- At 7:00, the crowd-on frame has a pack of small animals massed on the left.
  The crowd-off frame has three animals.
- At 17:00, the crowd-on frame is full.
- At 12:00, the crowd-on frame shows the crowd as a band on the horizon behind
  a wall of damage numbers, not as bodies pressing in. The census says 105 are
  on screen. The frame reads as a fight at the edge of the screen.

That is the honest reading of what the design does. The kit still kills a
body about 20 m out. The crowd makes sure there are always more coming.

Most of the extra frame cost is corpses and pops (about 770 and 460 to 610
boxes), not the living horde. The sim stays under 0.7 ms per step even with
other jobs competing for the CPU.

## Survival (balance.js: autopilot to death, paired seeds 20260821+)

```
FIRST TIER, 36 runs a side        dead <10:00   clears   hits  contact  spit  hazard
shipped (no crowd)                    1/36       29/36    716    3302   2722   4035
crowd v1 (phase mix, spitters)        7/36       21/36
crowd, walkers only (this build)      1/36       25/36    793    4945   2093   3048
```

Early deaths are unchanged. Four clears in thirty-six are lost. Contact damage
rose by half, and it is now the largest of the three damage sources; before
the crowd, hazards were.

```
VETERAN, 36 runs a side           dead <10:00   clears   hits  contact  spit  hazard
shipped (no crowd)                    0/36       36/36    652    2316   2113   4204
crowd, walkers only (this build)      0/36       30/36   1237    7531   3460   4072
```

At veteran the crowd costs six clears: one each for intern, scrap, spark and
surge, and two for ghoul. Contact damage triples. Spit rises by 60%, though the
crowd sends no spitters.

Note on the method. The no-crowd veteran bench runs every character in one
browser page. It was OOM-killed twice at about 7 GB during THE OX while other
browser jobs shared the container's 14.3 GB. It was rerun split: intern,
scrap and spark reproduced their first rows exactly, ox ran alone (peak
renderer about 2.3 GB, 4/4), and the other five ran together.

## Verification

- `crowdGate()` (suite section 97) stages a late kit that clears the table: bat, aura,
  zap and mortar evolved, 2.8 reach, 400 damage. It runs 6 s with the crowd on and off.
  - With the crowd on, the field must hold at least 80% of the target. With it off, the
    field must fall below half. With it on, kills must also exceed the target.
  - The crowd sends nothing ranged, and the gate checks that the phase mix it draws from
    does contain a ranged kind.
  - No crowd in the opening, none while a boss is up, never past `MAXE`.
  - Paid bodies stay at or under 10% of the table. An unpaid kill pays no gem, coins or
    heal; a paid control does pay.
- `node test.js` on this build: 841 passed, 0 failed. `node analyze.js`: 0 of 55
  broken. `node mutate.js --anchors`: all 294 anchors present.
- Four new mutants, each written for the suite to catch: `crowd-never-fills`,
  `crowd-pays-in-full`, `crowd-sends-a-firing-line` and `crowd-fights-the-boss`.
  Each one fails the gate by name when the gate is run on its own. The
  full-suite `mutate.js` verdicts for these four, plus four existing mutants
  this round touched (two re-anchored, two whose section 96 it rewrote), were
  still running at the commit that added this file. The L35 line in
  `LOOP_LOG.md` records them.
- Section 96 still measures the DIRECTOR. It now also checks that the table is
  what sends the bodies it counts: crowd sends are at most 6% (early) and 8%
  (late) of the table's.
