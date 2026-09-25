# L48: the gate that could not see inlined code

The audit's full-suite verdicts on the L40 mutants came back wrong for the
gate that owns them:

```
elsewhere the-cells-are-answered-fresh  expected 101  1 of 848, first in 22 - 101 did NOT
SURVIVED  the-clamp-still-makes-a-pair  expected 101  the suite passed a broken game
```

L40 had judged its three mutants with `section101.js` - section 101 cut out
of the suite and run in a fresh page - and every one failed its own clause
there. In the suite itself, the gate was blind to two of them.

## Why

- **Not escape analysis.** The first guess was that TurboFan, a hundred
  sections warm, inlines `nearestCells` into `groundY` and its escape
  analysis removes the returned array. `warmcold.js` took section 101's
  measurement in a fresh page and in a page warmed by a whole run to 15:00:
  the fresh-array mutant read 2,067 KB cold and 2,084 KB warm, the clean
  build 0 and 17 (`warmcold.txt`).
- **The profiler's attribution.** The whole quick suite run on the mutant
  with every line kept (`mutsuite.txt`) read section 101 as `nearestCells
  0.0 KB, confineIn 0.0 KB, confine 0.0 KB` - while `groundY` came out 1.7 MB
  heavier than on the clean build. V8's sampling heap profiler charges an
  allocation to the physical stack frame it happens in, and a function
  TurboFan has inlined has no frame of its own: in the suite's page,
  `nearestCells` lives inside `groundY` and `confine` inside its callers, and
  their bytes are charged there. Section 101's L40 comment said "inlined
  frames are attributed to their own function". They are not.
- **The fix is a browser that does not inline.** `flags.js` found the V8
  flags this Chrome accepts; `flagged.txt` took the measurement with
  `--no-turbo-inlining --no-maglev-inlining` (TurboFan kept, every function
  its own frame) and with `--max-opt=2 --no-maglev-inlining` (Maglev only):

```
no inlining, cold / warm           nearestCells     confineIn + confine   iterator results
clean                                  0 / 0          144 / 32               0 / 0
the-cells-are-answered-fresh       5,690 / 6,475      0 / 0                  0 / 0
the-clamp-still-makes-a-pair           0 / 0      1,714 / 2,946              0 / 0
the-bot-reads-the-field...             0 / 0         80 / 0                672 / 688
```

  Maglev-only is no control: it boxes the shared array's doubles, and the
  CLEAN `nearestCells` reads 6.7-8.2 MB there.

## What changed

- **Section 101** reads its three sites in a second browser launched with
  `--no-turbo-inlining --no-maglev-inlining`, on the same settled seed-9 field,
  so a site's bytes are its own cold or warm; and `nearestCells` gets an
  exact clause that no tier can hide - two calls return the same array. The
  whole-step bound and the shape clause stay in the suite's own page.
- **Section 22's GLIMMERFOWL count** was the other half of the first verdict,
  and it was a flake, not the mutant. It subtracted the whole frame's box
  count before three birds from the count after them, with the birds dropped
  at random inside eight metres: the camera was still settling onto the
  placed player between the two frames, and a bird behind the camera counted
  nothing. Run alone on an unchanged build it read anywhere from 31 to 61 boxes
  a bird over six tries, against a bound of 26 (`fowl.txt` has three of them
  and three under the mutant, 30 to 49); in the audit it failed a build whose only change was how
  `nearestCells` hands back its answer. It now counts the horde pass - which
  holds nothing but the birds - with the three birds in a row six to seven
  metres ahead of the player at camera yaw 0: 45, 42 and 45 clean, 17 under
  `fowl-marker-only`.
- **mutate.js** prints the child's first failing lines under every verdict
  row, so an "elsewhere" can be told apart from a flake without running the
  suite again - the first verdict here could not be, because the child's
  output was gone.

## Corrections to L40 and L41

- L40's per-function numbers were taken with inlining on. Its three sites were
  measured in fresh pages, where they happened to be their own frames, so the
  before/after numbers for them stand; the gate that was meant to keep them
  there could not see them in the suite.
- In the Maglev tier the shared `nearestCells` array still allocates: its
  doubles are boxed, 6.7-8.2 MB over 600 steps. L40's "allocates nothing"
  holds at TurboFan, where the step spends most of its time.
- L41 put 12-15 MB of boxed doubles over 600 steps on `groundY` and read them
  as `groundY`'s own. With nothing inlined, `groundY` itself allocates 0.7-0.9
  MB; the rest belonged to the functions inlined into it (the relief noise,
  the shore cap, the water depth). The same caution applies to L41's `walk`
  and `updateEnemies` figures. L41's conclusion - as played, the step
  allocates what it allocated before the shapes - is a whole-step number and
  stands.

## Verification

- `verify-l48.txt`: section 22 alone, three clean runs and `fowl-marker-only`;
  section 101 alone, two clean runs and each of its five mutants - every
  mutant fails its own clause and no other.
- `suite.txt`: `node test.js` 852 passed, 0 failed in 61 min on exactly the committed
  files (7bb9aed); section 22 read 45.0 boxes a bird, section 101's site clauses read 0.0 /
  144 + 16 / 0.0 KB in the no-inlining browser.
- `audit.txt`: the four mutants L48 changes, judged through the full quick suite with the
  new mutate.js - all CAUGHT by their own section, the failing line under each row:
  the-cells-are-answered-fresh (same array twice: false, 6,699 KB), the-clamp-still-makes-a-pair
  (1,378 KB under confine), the-bot-reads-the-field-through-an-iterator (720 KB of iterator
  results), fowl-marker-only (17 boxes a bird). Before L48 the first three read elsewhere,
  SURVIVED and SURVIVED (`chain3-verdicts.txt`).

## Files

- `warmcold.js` / `.txt`, `flags.js`, `flagged.txt`: the attribution
  experiments.
- `mutsuite.txt`: the full quick suite on the nearestCells mutant, before the
  fix.
- `fowl.js` / `.txt`: section 22's bird count alone, before the fix.
- `section.js`: any one section of `test.js` run alone, with a mutant by id.
- `verify-l48.txt`, `suite.txt`, `audit.txt`.
