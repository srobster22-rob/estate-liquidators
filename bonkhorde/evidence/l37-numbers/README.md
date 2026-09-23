# L37: the wall of numbers

L35 put a standing crowd of 75-130 bodies in front of the kit. Its frames showed
the cost straight away: at 12:00 the crowd read as a band on the horizon behind
a solid bar of gold damage numbers. This round measured the bar first and then
took it apart.

## What the bar was made of (numprobe.js, the pre-L37 build)

L35's protocol: seed-9 god bot as THE INTERN, crowd on, two seconds of sim
sampled at each station, then one frame read off the real overlay canvas.

```
                         3:00    7:00   12:00   17:00
numbers pushed / s          5      62     146     215
  of them crits           50%     77%    100%    100%
numbers alive (mean)      2.7    31.8    73.7   124.9
on screen                   3      49     115     122
  >35% under another      67%     88%     99%    100%
bodies under a number      8%     16%     55%     80%
crowd OFF, pushed / s       4      12      15      24
```

Two causes, and they compound:

- **Crits jumped the cap.** `if(nums.length < 30 || crit)` let every crit
  through, and a late kit crits on most hits (55% at 3:00, 78% at 17:00 on
  this save). Once crits alone held the pool above 30, no white number was
  ever pushed again: 100% of pushes were crits from 12:00 on.
- **An area weapon rolls once.** `damageArea` calls `dmgOut` once and hands the
  same roll to every body it reaches. One crit pulse through the crowd is fifty
  identical gold numbers on fifty neighbouring bodies in the same frame, at
  full size at any depth. That is the "3189 3189 3189" band in L35's frames.

With the crowd off the same kit pushes 12-24 a second; the wall is the crowd
multiplied by the bypass.

## The fix

- **One cap for every number.** `NUM_CAP` (48) holds whatever a crit says. A
  crit that finds the pool full takes the place of the oldest white number that
  is not on screen and is not the player's own, or no place at all (`numRoom`).
- **Placed once, where nothing is.** `numPlace` decides, the first frame a number
  is drawn, whether it goes on screen: only where its box touches no box already
  there (`NUM_GAP` px). A number on screen keeps its place for its whole rise.
  A newcomer that lands on one is turned away and leaves the pool, unless it
  outranks everything it lands on. The ranks are the player's own numbers (the
  chain payout and a level's heal, both made by `numMe`), then crits, then
  white hits. Two of the player's own numbers on one frame stack instead
  (`numStack`), and the climb is kept for the rest of the rise.
- **Re-checked every frame.** Numbers rise at their own speeds and the camera
  moves, so two placed apart can slide onto each other. Where the ink of two
  numbers on screen meets, the higher rank keeps its place, then the older, and
  the other goes. A number behind the eye or wholly off the canvas leaves the
  pool rather than hold one of its 48 places.
- **Sized by depth.** A number within `NUM_NEAR` (12 m) of the eye draws at full
  size. Past that it shrinks with distance, never below `NUM_FAR_K` (0.6). The
  crowd stands 20-38 m out, and at one size for every depth its numbers were
  wider than the gaps between its bodies.
- **Off the run stream.** A number's jitter came from the seeded run stream,
  three draws per number. How many numbers a frame made therefore moved every
  pinned run after the first hit. It rolls on the cosmetic stream now. Pinned
  runs shift once with this round, and never again for a change to the numbers.

Three QA knobs make the same-build A/B possible: `numSort`, `numDepth` (both
ship on) and `numJump` (ships off). With all three flipped the page draws the
pre-L37 numbers over the identical sim, because the numbers no longer touch it.

## The same frame, both ways (stage-on.png / stage-off.png)

numGate's own staging (stageshot2.js), seeded like the gate's first pulse
so the picture reproduces: one crit pulse through 117 bodies standing 18-34 m
ahead of the chase camera, both arms on the same seed.

```
                        pre-L37 numbers    L37
numbers in the pool           117           48
numbers drawn                 117           14
overlapping pairs             837            0
bodies under a number     76 of 117     28 of 117
screen under numbers      24,576 px     5,160 px
```

The suite reads the same staging off three seeded pulses at its own
1280x760: 14 drawn with 0 overlapping pairs against 117 with 2,348; 84 of 351
bodies under a number against 218; 16,092 px of screen against 77,080.

## In play (numprobe3.js)

L35's protocol (seed 9, the god bot as THE INTERN, crowd on), measured over
120 painted frames at each station with the camera easing to the heading as
a player's would. "old" is this build with the three knobs flipped back: the
pre-L37 numbers over the identical run. The rows that describe the run (level,
crit chance, bodies on screen) are equal in both arms at every station.

```
same run, old numbers / L37        3:00         7:00        12:00        17:00
bodies on screen                   17.2         43.0         27.5         65.4
numbers drawn (mean)          3.6 / 3.4  12.8 / 13.4  10.2 /  6.8  27.8 / 11.2
  most at once                  9 / 8      23 / 25      21 / 15      54 / 19
  illegible (>35% covered)     6% / 0%     54% / 0%     37% / 0%     75% / 0%
screen under a number       0.46 / 0.20  1.47 / 0.84  1.32 / 0.72  2.48 / 0.98 %
bodies under a number        3.3 / 0.0    8.1 / 3.9   24.4 / 6.3   43.3 / 14.3 %
```

The number jitter is cosmetic and unseeded, so these move a little between
takes: across three takes, bodies under a number at 17:00 read 43-47% with
the old numbers and 8.4-14.3% with L37. Illegible read 0% in every L37 frame
of every take.

The pre-L37 build on its own run (a different run from the same seed - see
"Off the run stream"): 1.3, 21.4, 61.5 and 83.1 numbers drawn, 0, 61, 88 and
94% of them illegible, 0, 19, 48 and 70% of the bodies under one.

The frames are one fixed frame of each window (frame 60 of 120), the same
frame in each arm. `l37-t1020.png` and `wall-t1020.png` are the same moment
at 17:00: a band of overlapping 1530s across the crowd, and 12 numbers apart
with the bodies showing between them. `base-t1020.png` is the pre-L37 build's
own 17:00 frame: 130 numbers drawn, 122 illegible. `l37-t0420.png` and
`wall-t0420.png` (7:00) show a second failure of the old cap. The old numbers
drew ONE number on that frame, because the pool sat at its cap of 30 with
numbers that were off the screen, and every hit in view was turned away. L37
drops a number that leaves the screen, and drew nine.

## Verification

- `numGate()` (suite section 97), ten clauses: the pool cap against a crit
  pulse; no two drawn numbers sharing ink, on the pulse's frame and through the
  rest of the rise; the crowd showing through, in bodies and in pixels, against
  the pre-L37 numbers on the same staging; depth, in the font and box actually
  drawn; rank, stacking and the climb; incumbency, and a staged drift where the
  re-check must fire; a lone hit drawn; zero run-stream draws for a number; a
  crit at a full pool, and what it may and may not evict; a number off the
  canvas or behind the eye leaving the pool. Every placed number is checked
  against what the frame actually painted: its text, spot and size. Every "it
  works" clause has a null that shows the staging reproduces the fault without
  the fix.
- **The gate is deterministic.** Its first version read one unseeded pulse, and
  a number's jitter (`crnd`) decides which 15 of the 117 numbers get placed,
  and so which bodies they stand over. Forty clean runs put the bodies-under
  ratio anywhere from .19 to .49, and a forty-first at .57, against a bound of
  .5. That clause would have failed a clean build now and then. The gate now
  seeds `Math.random` for its own length (and hands it back), and reads the
  crowd clause off the sum of three pulses. The same seed gives the same pulse,
  field for field. Over forty different seed bases the summed ratio runs .30 to
  .43, and the pixel ratio .20 to .25 against its bound of .33.
- Seventeen mutants, each written to fail the gate by name. All seventeen fail
  `numGate` on its own (gatemut.js), each by the clause it was written for.
  Their full-suite verdicts follow in `LOOP_LOG.md`.
- `node test.js`: 846 passed, 0 failed. The first run on L37 read 844 and 2.
  Neither failure was the numbers: two checks read one moment of a pinned
  seeded run, and L37 moves every pinned run once. Section 96's frame share
  now reads its two seeds pooled (twelve paired seeds: .412 on L37 against
  .408 before, paired difference +.004, standard error .024). Section 100's
  outcrop paint now reads a full turn of the camera. Both are in
  `LOOP_LOG.md`, and their replicas are `s96pass.js` and `s100turn.js`.
- `node analyze.js`: 0 of 55 broken. `node mutate.js --anchors`: 318 present.

## Files

- `numprobe.js`: the baseline table above, run on the pre-L37 build (a paused
  frame a station, read off the real overlay canvas).
- `numprobe3.js`: the in-play table (`ARM=l37`, `wall` or `base`) and its frames.
- `stageshot2.js`: the staging pictures and their table, seeded like the gate.
- `gaterun.js`, `gatemut.js`, `gatedist.js`: numGate on a build, each L37
  mutant against the gate on its own, and the gate's spread over forty seed
  bases.
- `s96pass.js`, `s100turn.js`: section 96's and section 100's measurements
  lifted out of the suite (the frame census by pass, and the outcrop paint
  over a full turn of the camera).
- `l37.json`, `wall.json`, `base.json`, `stage.json`: the numbers behind the
  tables.
