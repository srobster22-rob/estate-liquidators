# L36b: the audit's clock is the host's

The L36/L37 mutant chain's first two full-suite verdicts came back `ERROR` after
exactly 3300 s each, both stopped at section 97's header. Two different
mutants in the bonk path, one shape of failure, and the audit's wording was
"the suite did not finish" - the wording for a crash. This round found out
what it was. Nothing hung, and neither mutant was at fault.

## What was measured

The container had restarted twice in the night. Section 12 of the suite times
a heavy frame; `fpsprobe.js` repeats that measurement on the same build:

```
                                     yesterday (two runs)     today (three takes)
heavy frame, ~365 enemies, ~3,040 boxes   9.8 / 10.4 fps        4.8 / 3.9 / 4.3 fps
```

Software GL (ANGLE over SwiftShader, `glprobe.js`) renders 2.3x slower on this
host than it did the day before. JavaScript speed is unchanged (numGate runs in
0.6-1.9 s today, 0.7-1.4 s yesterday). The frame's content is identical: the
silhouette set, the far-read percentages and every reach the bezel gates
derive match yesterday's passing run to the digit.

The suite's clock, clean, on this host (`suite-sections.txt`, one timestamp a
section):

```
                              yesterday      today
sections 1-96                  ~12 min       20 min
section 97 (the gates)         ~25 min       41 min 45 s
whole suite                    37 min        64 min 07 s    846 passed, 0 failed
mutate.js's timeout                          55 min
```

Section 97 is three bezel gates (silhouetteGate, rimDayGate, farReadGate):
hundreds of chipReadFar reads, each four renders and three readbacks of a
1280x760 frame. `bezelprobe.js`: one region-hour of rimDayGate's derivation is
48 reads (16 radii x 3 stations, the sweep running to 72 m where the shipped
table says 72) at 1.8-2.2 s each, on the L37 build and the pre-L37 build alike.
Forty-four region-hours.

## What it was not

- Not a loop. `hang.js` walks section 97 gate by gate under the mutant, each
  gate in its own evaluate with a timeout, and pauses the page over CDP when
  one runs over. Without the bezel gates every gate returns in 228 s;
  whipGate fails by name ("IT LASHES A BOSS") in 0.3 s. With them, the pause
  landed inside `rimDayGate -> bezelDerive -> chipReadFar -> render` after
  25 minutes: rendering, not looping.
- Not the game. Same reaches, same set, same percentages as the passing run.
- Not memory or throttling: no cgroup quota, no throttled periods, no OOM,
  steal under 1%.

## What changed in the instrument

- `mutate.js`: the timeout is `BONKHORDE_MUTANT_MIN` (default 55) and a chain
  sets it from a clean run measured on the machine it is about to use. A
  timed-out child is reported as `killed (timeout, N min)`: Playwright catches
  the SIGTERM the timeout sends and exits with a status of its own, which is
  why the rows read as crashes.
- `BONKHORDE_QUICK=1`: each child skips the three bezel gates (the suite's
  `BONKHORDE_SKIP_BEZEL`, which prints `SKIP` for them and the silhouette
  budget check and counts neither), every row says `[quick]` and carries the
  child's own check count (842 against 846), and the three mutants that target
  those gates are marked `bezel:true` and NOT JUDGED in quick mode rather than
  reported SURVIVED by an instrument that never looked.
- First quick verdict on this host: `whiptail-lashes-a-boss` CAUGHT, 3 of 842
  assertions, first in section 16 and 97 also, in 1543 s.

## Files

- `fpsprobe.js`: section 12's measurement as a probe.
- `glprobe.js`: the renderer string, the frame's pixels, one chip read.
- `bezelprobe.js`: reads and seconds per region-hour of the reach derivation.
- `hang.js`: section 97 gate by gate under a mutant, with the CDP pause.
- `suite-sections.txt`: the clean run's section timestamps on this host.
