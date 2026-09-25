# L41: one shape per kind of thing

L40 took out the objects the step made and dropped. What was left in its
profile was boxed doubles - `walk` 31 MB, `updateEnemies` 25 MB, `groundY`
15 MB over six hundred settled steps - and `tiers.js` had one explanation
ready: the bodies had ten hidden classes at once. Every system that touches a
body added its own keys the first time it needed them - the rout its
`rout/routT/routS`, the dive its `dv*`, the headlong its `hdl*`, the spit its
`spitTell`, the draw pass its `bt/lf/lr/pH/pt2/rc2/py`, death its
`ft/fd/fhd/fx/fz` - in whatever order the run happened to reach them, so the
property sites in `walk()` and `updateEnemies()` were megamorphic, and a double
loaded or stored through the generic path is a sixteen-byte box. The tables
those functions read through a body were the same story in small: six enemy
defs with six key signatures, ten biome `mod` objects with ten.

## The audit

A shape is fixed at birth only if every key the body will ever carry is in
the spawn literal, and a key can be in the literal only if no read notices.
Two instruments, one static and one dynamic, and the static one was five
readers (one per five thousand lines) rather than one:

- `props.js`: every object pushed onto `enemies` wrapped in a Proxy for a whole
  pinned trial - per key, how many bodies had it set and from where, what
  types it held, how often it was READ while still unset and from where, and
  any `in`, `delete` or own-keys walk over a body (`props-clean.txt`,
  `props-crowd.txt`: 19,545 and 96,028 bodies; no walks, no deletes).
- `sweep.txt`: the file read end to end for every write of a property on a
  body and every read that would distinguish an absent key - 507 writes over
  99 keys, and fourteen distinguishing reads: the four hash-roll caches
  (`_rr/_dr/_sr/_hr === undefined`), `_s` (seeded from the RNG on first use),
  `ft` (three death-pose guards), `fgap` (the first-draw flag), `rest`, `hd`
  (the boss's first `walk()`), `skyT`, `born`, and `denRef === null`.
- `tables.js`: the key signatures of the enemy defs, the boss defs, the biomes
  and their sub-objects (`tables-before.txt`).

## What changed

Every key, from birth, in one order - and the value chosen so that no read
can tell:

- **NaN** for a number the body writes later. To every read in this file an
  absent number and NaN are the same thing: `> 0` false, `<= 0` false, `|| 0`
  zero, `!x` true, a sum NaN. NaN keeps the field a double, which is the
  point; `0` would not have been exact (`e.dv <= 0` is true of 0 and false of
  an absent key, and the first step of a flier's life turns on it).
- **undefined** where a read tests for it (`ft`, `fgap`, `rest`, the boss's
  `skyT` and `hd`), where laziness IS the semantics (`_s` draws from the RNG
  the first time it is asked, and drawing it at spawn would move every pinned
  run), where a test gate reads it (`dvX/dvZ`), and for every key this kind of
  body never writes (a boss never routs by alarm; a body never has phases).
- **null** for `hdl`, `bt` and `calfOf`, whose reads are truthiness and one
  `=== e`.
- The four hash rolls are pure functions of the eid, so they are computed
  where the eid is: `eid` is taken before the literal (nothing between reads
  `EID`) and `_rr/_dr/_sr/_hr` are set from it; the boss's, of eid 0, are 0,
  as `Math.imul(undefined|0, k)` always made them.
- The boss literal carries the same key set in its own order, so it is its
  own map and its `hd` sentinel does not make every body's `hd` a tagged
  field.
- The enemy defs, the boss defs and the biome `mod`s carry their optional
  keys as `undefined`, in one order each; every read of those keys is a
  truthiness test or `|| 1`, and nothing walks their keys
  (`Object.keys(ENEMIES)` walks the table, not a def).
- `groundY()` reads `nearestCells()`' answer by index instead of destructuring
  it: in every tier but the top one the destructuring is the iterator protocol,
  a result object and a boxed number per element per call.

## Nothing moved

Both pinned trials reproduce to the kill after every one of those edits, with
every sound count the same (`trial.js` from L40):

```
clean run                585.00 s, level 37,  19,418 kills
crowd-pays-in-full       1258.70 s, level 158, 95,854 kills
```

## What it bought, and what it did not

The shapes: 53 bodies at t=300 with 10 maps and 42 to 60 keys before; 2 maps
(the field's and the boss's) with 105 keys each after, corpses included
(`shapes.js`). The tables: 1 signature each.

Six hundred settled steps run flat out (`step-alloc.js`), the L40 build
against this one:

```
                      L40 build      L41 build
walk                   31.2 MB      18-24 MB
updateEnemies          24.7 MB      23-24 MB
groundY                14.9 MB      12.4 MB
the whole step          229 KB       201-225 KB a step
```

That is not the order of magnitude the megamorphism predicted, and the reason
is the more important finding of the round. `tiers2.js` runs the same settled field at sixty steps a second of WALL time
- the page's own loop cut, so the JIT gets the time it gets in play - and
reads V8's own optimization status of each hot function every quarter second:

```
as played, 20 s from t=305         L40 build                      L41 build
the step allocates                 223 KB a step                  220 KB a step
walk                               TF 74%, Maglev 24%   48 KB     Maglev 68%, TF 27%   49 KB
updateEnemies                      Maglev 51%, TF 42%   43 KB     Maglev 74%, TF 21%   40 KB
groundY                            TF 100%              32 KB     TF 100%              27 KB
step                               Maglev 87%                     Baseline 63%, Maglev 37%
deopts in the window                8                             15 (11 "wrong map")
```

As played, the shapes bought nothing measurable: the step allocates what it
allocated. What boxes the doubles is not the shape of the body but the TIER
the function is running in - `walk` and `updateEnemies` spend most of their
time in Maglev, which boxes a double at every call boundary and many stores,
and re-enter TurboFan only to be thrown out of it by the next deopt (the
window opens five seconds after the first boss, whose map is new to every
site) - and, for `groundY`, which is TurboFanned throughout and still
allocates 27-32 KB a step, the boxing of arguments at calls TurboFan did not
inline (`BASE_Y`, `RELIEF` sit in Maglev). None of that is a shape, and none
of it is a leak; at 220 KB a step the collector runs a one-to-two-millisecond
scavenge about once a second of play. This is where the allocation thread
stops: two rounds took out everything the source itself made and dropped
(12.2 GB a run to 7.5), and what is left is the engine's, at a cost that does
not reach the frame.

## Verification

- Section 101, one new clause: every body on the settled field - live and
  dead, the boss included - has ONE key signature among the field's bodies
  and one key set overall (10 signatures before). The boxed-double bytes are
  printed beside it and not asserted: a 15% swing between runs of the same
  build is the tier state, and the tier state is not this round's claim.
- Mutants `a-body-still-grows-its-shape` (spitTell leaves the literal: the
  spitters' first tell makes a second class) and `the-boss-keeps-its-old-shape`
  (the boss loses the keys it never writes) each fail the shape clause and
  nothing else; L40's three mutants still fail theirs (`verify3.txt`).
- `node test.js`: 852 passed, 0 failed, in 66 min 05 s on this host, on exactly the committed files (build b0654d66 = commit 4301b29); section 101 read 189 KB a step inside the suite, one signature across 82 bodies.

## Files

- `props.js`, `props-clean.txt`, `props-crowd.txt`: the dynamic audit.
- `sweep.txt`: the static audit, with the readers' notes.
- `tables.js`, `tables-before.txt`: the tables' signatures before.
- `pacedalloc.js`: the step's allocation with the steps paced at sixty a
  second (superseded by `tiers2.js`, which also cuts the page's own loop -
  `__g.step()` un-pauses it, so the first paced numbers counted two drivers).
- `tiers2.js`, `tiers2-*.txt`: tier residency of the hot functions as played,
  the deopts over the same window, and the step's allocation in that regime.
- `verify*.txt`: the trials, the census and the allocation after each edit.

## Erratum (L48)

The function-by-function figures here were taken with the engine inlining, and
V8's sampling heap profiler charges an inlined function's allocations to the
function it was inlined into. With nothing inlined (L48, `evidence/l48-gate`),
`groundY` itself allocates 0.7-0.9 MB over the 600 steps, not 12-15 MB: the rest
was the relief noise, the shore cap and the water depth inlined into it. The
same caution applies to the `walk` and `updateEnemies` figures and to the
explanation of `groundY`'s bytes above. The whole-step numbers, and the
conclusion that the shapes did not change what the step allocates as played,
stand.
