# L40: the step's garbage

L39 took the audio graph out of a crowded run's memory. The same instrument
(`churn.js`, V8's sampling heap profiler with the collected objects counted)
read the JS heap's CHURN over the same ten-minute bench trial - what the step
allocates and the collector takes back - at 12.2 GB, about 350 KB a frame, and
named the sites:

```
one 585 s trial, the shipped game, before L40   (sampled at 32 KB)
   2.9 GB   botVector      the autopilot measuring every gem, hazard and event
                           again for each of its twenty headings
   2.4 GB   Math.hypot     (V8's builtin hands back a boxed number)
   1.9 GB   groundY
   1.2 GB   updateEnemies
   0.9 GB   walk
   453 MB   next           for-of iterator results
```

None of it is a leak - the heap after a trial is flat - it is a scavenge every
few dozen frames, and on a phone's smaller young generation, more often.

Two kinds of thing are in that list. Objects the source makes and drops - the
four-element array `nearestCells()` returned to every `groundY()`, the pair
`[e.x, e.z] = confine(...)` destructured per body per step, the for-of
iterators and the closure the separation pass built per body, the autopilot's
per-heading re-measurement - and boxed doubles, which is what most of
`groundY`'s, `walk`'s and `updateEnemies`' bytes turn out to be (below). This
round takes out the first kind, exactly.

## What changed

Every fix is an exact rewrite: the same arithmetic, operation for operation, in
the same order, onto scratch that is reused instead of an object that is made.

- `nearestCells()` answers in one shared array (`NC4`); the terrain build,
  which keeps the answer across further calls, takes a `.slice()`.
- `confineIn(o, x, z, pad)` writes the clamp straight onto the body; the five
  per-step sites that destructured `confine()`'s pair use it. The spawn and
  arrival sites, which run once per body, still take the pair.
- `botVector()` measures the gems, the hazards, the events and the boss's
  offset ONCE a step into scratch arrays, and the twenty headings read those;
  its lane scan and its lane loop walk their arrays by index.
- The separation pass's callback is one function (`sepAcc`) with the body it
  is measuring for in module scope, not a closure per body per step.
- `updateGems()` asks the ground under the player once a step, not once a gem.

`Math.hypot` stays: `Math.sqrt(x*x + z*z)` is not the same number in the last
place (hypot scales and compensates), and a different last place moves every
pinned run in the suite. It is the largest thing left, and a later round's.

## Nothing moved

The pinned trials reproduce to the kill on the changed build, with every sound
count the same (`trial.js`):

```
clean run                585.00 s, level 37,  19,418 kills   (unchanged)
crowd-pays-in-full       1258.70 s, level 158, 95,854 kills  (unchanged)
```

## What it bought

The same 585 s trial, whole-run churn: 12.2 GB before, 7.5 GB after (`churn.js`, the same seed, the same run to the same kill).

Six hundred steps of a settled pinned run (seed 9, t=300, `step-alloc.js`, a
16 KB sampling interval), the step's allocation by site:

```
                   before      after
nearestCells       2,340 KB       0
confine            1,522 KB       0     (confineIn 0)
botVector < next   9,606 KB       0
botVector         26,554 KB  11,416 KB
the whole step       301 KB   229 KB a step
```

And what the collector did about it over 6,000 steps from t=300, the same
run, `--trace-gc` (`scavenges.sh`):

```
                   before             after
scavenges             72              42, 44, 47   (three runs)
scavenge pauses    309 ms, max 86 ms  37-86 ms, max 6-16 ms
```

## What is left, and why it is a different round

At steady state the hot functions still allocate - `walk` 31 MB, `updateEnemies`
27 MB, `groundY` 15 MB over those 600 steps - and none of it is an object the
source makes. `tiers.js` (Chrome with `--allow-natives-syntax --trace-deopt`)
says what it is: the bodies have TEN hidden classes at once (`shapes.js`:
53 enemies, 10 maps, 42 to 60 keys - `spitTell` on the spitters, `alarm` on
the skitters, `dv*` on the fliers, sixteen keys the systems add on first use,
and the boss made another way), so the property sites in `walk` and
`updateEnemies` are megamorphic, and a megamorphic load or store of a double
goes through the generic path with a boxed number - sixteen bytes per field
per body per step. It also deoptimizes: 1,353 deopts of `rebuildGrid` in one
two-second burst of the settle (its for-of's result object, "wrong map"),
and a steady thirty-odd "wrong map" deopts per 6,000 steps in the step
functions, each of which drops the function to the baseline tier where every
double is boxed until it is optimized again. The fix is one shape per kind of
thing - every property a body will ever have, set at spawn, in one order -
which is a spawn-literal rewrite with a `=== undefined` audit behind it, and
its own gate. Not this round.

## Verification

- Section 101: the profiler around 600 settled steps, four clauses -
  `nearestCells` samples nothing, `confineIn` nothing and `confine` under
  64 KB, no iterator results under `botVector`, and the whole step under
  400 KB (a loose bound: the whole-step number is tier-dependent, the sites
  carry the claim).
- Mutants `the-cells-are-answered-fresh` (1,154 KB under nearestCells),
  `the-clamp-still-makes-a-pair` (confineIn 817 KB, confine 849 KB) and
  `the-bot-reads-the-field-through-an-iterator` (608 KB under botVector) each fail their
  own clause and no other (`section101.js`, `verify3.txt`).
- `node test.js`: 851 passed, 0 failed, in 64 min 23 s on this host (the L40 build ae6c9ddd, section 101 reading 178 KB a step inside the suite; the committed index.html and test.js differ from that build by the corrected comment only - the diff is comments).

## Files

- `trial.js`: the pinned trial on a build, with a mutant by id; the run's
  clock, level and kills and every sound's count.
- `churn.js`: whole-trial churn by allocating function (L39's instrument,
  the build taken from `REPO`).
- `step-alloc.js`: 600 settled steps under the sampling profiler, by site.
- `tiers.js`: V8's optimization status of the hot functions and, under
  `DEBUG=pw:browser`, the deopt trace; `deopts.txt` is the summary.
- `shapes.js`: the hidden-class census of the bodies (`shapes.txt`).
- `scavenges.sh`: `--trace-gc` over 6,000 settled steps on both builds.
- `section101.js`: section 101 cut out of `test.js` and run alone, with a
  mutant by id.
- `step-alloc.txt` (both builds), `tiers.txt`, `verify3.txt` (the final build: section 101
  clean and under each mutant, both pinned trials, the step, the whole-trial
  churn, the scavenges): the numbers above, as printed.

## Erratum (L48)

The per-function allocation figures in this round were taken with the engine
inlining, and V8's sampling heap profiler charges an inlined function's
allocations to the function it was inlined into. This round's three sites were
measured in fresh pages, where they were their own frames, so their before and
after numbers stand; but section 101, as this round shipped it, could not see
them in the suite's warm page and passed two of the three mutants in the full
audit. L48 (`evidence/l48-gate`) moved the site clauses into a browser that
inlines nothing. Also: in the Maglev tier the shared `nearestCells` array's
doubles are boxed (6.7-8.2 MB over 600 steps on this build), so "allocates
nothing" holds at TurboFan only.
