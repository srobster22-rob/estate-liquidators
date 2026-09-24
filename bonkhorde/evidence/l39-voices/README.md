# L39: the sound of a crowd

The audit's `crowd-pays-in-full` run (a mutant: every crowd body pays XP) came
back `killed (timeout, 60 min)` with the suite stopped after section 22h's
five arena checks. The kernel's log said what it was: a `chrome` renderer
killed for memory at 13.6 GB resident, twenty-two minutes in. 22h's last step
plays six whole games back to back inside one `runOut()` each - a synchronous
twenty-minute simulation per trial with no frame between them - and under this
mutant one game is level 158 and 95,854 kills.

## What held the memory

Not the game's arrays: every pool is capped and the census after a trial finds
nothing large. Not V8's heap: 27 MB used. `accounting.js` (V8's own
`Runtime.getHeapUsage`) after one trial read 641 MB of ArrayBuffer backing
stores and 162 MB of embedder objects, and `who-allocates.js` - the typed-array
constructors, `getImageData`, `createBuffer` and `readPixels` wrapped in the
page and every allocation attributed to its stack - named the owner:

```
one trial, crowd paying in full, before the fix
   604.4 MB   12,832 calls   AudioContext.createBuffer < noiseBurst < boom
    13.2 MB    1,568 calls   AudioContext.createBuffer < noiseBurst < hop
     6.0 MB      256 calls   AudioContext.createBuffer < noiseBurst < hurt
     3.8 MB       32 calls   AudioContext.createBuffer < noiseBurst < boss
     3.2 MB      192 calls   AudioContext.createBuffer < noiseBurst < gore
     1.3 MB      320 calls   AudioContext.createBuffer < noiseBurst < whiff
```

`noiseBurst` built a fresh `AudioBuffer` for every burst - a 0.28 s boom is
12,348 samples, each one a `Math.random()` call, 49 KB - and the counts for one
such run (`sounds.js`, the page's own `sfxCount`):

```
                  crowd paying in full        the shipped game
pop                    96,119                    4,170
gem                    42,278                    2,976
boom                   12,607                    3,018
bonk                    6,796                    2,240
hop                     1,575                      726
```

Every `pop`, `gem` and `bonk` is an oscillator and a gain node; every boom a
buffer source, a filter and a gain. A node lives until its sound ends, and a
synchronous run never reaches the moment it would be collected: 2.6 GB of
renderer after one trial, 4.7 after the second, 5.6 after the third
(`trials-rss.js`), and the audit's child, which had already run twenty-two
sections, went past the machine on the fifth or sixth. Forcing a full GC every
3,000 steps changed nothing, which is how the audio graph (outside V8) was
told apart from the heap.

The shipped game does the same thing at a fifth of the rate: seventy-six pops
a second on a paid crowd, fifteen on the real one, every one of them a buffer
or two nodes allocated on the main thread.

## The fix

- **One second of noise, made once.** `noiseBurst` plays a slice of a shared
  buffer from a random offset, with the fade the fill used to carry (`1 - i/n`)
  moved onto its gain. The same sound; no buffer and no 12,348 random numbers
  per burst.
- **A voice limit.** No frequent sound starts twice inside `SFX_GAP` (0.04 s of
  sim time): two pops forty milliseconds apart are one pop. The long, rare
  one-shots - a level, an evolution, a boss, death, the win, the dens, the
  affinity notes, a pearl - always play (`SFX_ALWAYS`). Every call is still
  counted in `sfxCount`, which is what the suite reads to ask whether a thing
  made a noise; what actually started is counted beside it in `sfxPlayed`.

## After the fix, the same trial

The run is byte-for-byte the same run (1258.70 s, level 158, 95,854 kills):

```
                                    before          after
typed-array / buffer allocations    15,274, 633 MB  11, 9.6 MB
renderer RSS after the trial        2,610 MB        629 MB
ArrayBuffer backing stores          641 MB          17 MB
embedder (Blink) objects            162 MB          33 MB
RSS after a second trial            4,711 MB        652 MB
wall time of the trial              91-99 s         70-72 s
```

What the limit does to the mix, over the same two runs (`sounds.js`: asked is
`sfxCount`, unchanged by the fix; played is `sfxPlayed`):

```
              crowd paying in full           the shipped game
              asked      played              asked     played
pop           96,119      9,380              4,170     1,736
gem           42,278     11,513              2,976     1,977
boom          12,607      2,753              3,018     1,006
bonk           6,796      6,486              2,240     2,240
hop            1,575      1,575                726       726
whiff            495        495                181       181
```

A bonk, a hop and a whiff never arrive faster than the gap, so they play as
they did; the pops, chimes and booms that arrived in the same frame - a pulse
through a crowd, a magnet pulling a pile of gems - play once for the frame.

## Verification

- `voiceGate()` (section 97), five clauses with two nulls: a frequent sound
  asked for a hundred times in one frame starts once, once more after the gap,
  not again inside it (null: with the gap at 0, all hundred start); every call
  is counted; an always-play sound plays three of three; two noise bursts make
  one `AudioBuffer` and the second plays the first's (null: with the shared
  buffer forgotten between them, two); a new run's first sound plays although
  its clock is below the last start. Clean in 30 ms.
- Mutants `the-noise-is-made-fresh` and `every-pop-plays` fail the gate by name
  (`voicegate.js`).
- `node test.js` on this host: 847 passed, 0 failed (846 and the voice gate) in 66 min 35 s; `node mutate.js --anchors`: 320 present. The whole suite's sound-count checks ("THE NEW THINGS MAKE A NOISE", the whiff clicks, the dens, the pearl, the upwelling) pass unchanged, because the count is taken before the limit.

## Files

- `who-allocates.js`: the constructors and buffer makers wrapped, bytes per
  allocating stack over one trial.
- `accounting.js`: V8 heap, embedder and backing stores after each trial, and
  after a forced collection.
- `trials-rss.js`: six trials in the suite's order with the renderer's RSS
  sampled from outside.
- `churn.js`: V8's sampling heap profiler over a trial, every allocation
  including the collected ones (the JS-heap churn: 37 GB a trial, led by the
  autopilot's `botVector`, `Math.hypot` and `groundY` - a later round's).
- `sounds.js`: `sfxCount` and `sfxPlayed` over a trial.
- `voicegate.js`: the gate on a build, with a mutant applied by id.
