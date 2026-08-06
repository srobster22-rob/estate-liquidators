# clip/ — the vertical clip, built from the game

`clip/estate-liquidators.mp4` is 24 seconds of 1080×1920 that came out of `proto3d`, not out
of an editor. A headless browser plays a scripted take against the real prototype and every
frame is captured; the rules deciding what the Curator does during that take are the same
rules `sim/` measures and `unity/tests` asserts.

That is the point of doing it this way. A screen recording rots the moment the sim changes and
nobody notices. This one **fails to build** — see gate G9 — if the game stops behaving the way
the captions claim.

```bash
node clip/build.mjs            # capture -> encode -> gate    (~4 min)
node clip/build.mjs --frames 90    # first 3 s only, for framing work
node clip/build.mjs --skip-render  # re-grade / re-gate the frames you already have
```

## The pieces

| File | What it is |
|---|---|
| `CLIP-SPEC.md` | The contract: format, beat sheet, sound, the ten gates, and what the build found out about the game. **Read this first.** |
| `director.js` | Injected before the prototype's own script. Seeded RNG, a virtual clock, the caption overlay, and the camera helpers. |
| `shots.js` | The performance — the only file that decides what the clip *shows*. |
| `render.mjs` | Playwright capture pass → `clip/build/frames/*.png` + `trace.json`. |
| `audio.mjs` | The synthesized bed, written sample by sample. No dependencies. |
| `encode.mjs` | Frames + bed → H.264/AAC mp4. Also holds the grade. |
| `check.mjs` | The ten gates. Exit code 1 if any fails. |
| `build.mjs` | All of the above, in order. |

## How the capture is deterministic

Three tricks, all in `director.js`:

1. **`Math.random` is seeded** (`?seed=…`, default 20260806), so the estate rolls the same
   items every build.
2. **`requestAnimationFrame` is trapped and pumped by hand.** The sim advances exactly
   1/30 s per captured frame regardless of how slow the headless renderer is, so a machine
   that renders at 4 fps produces the identical film to one that renders at 60.
3. **`preserveDrawingBuffer` is forced on**, or WebGL screenshots come back blank.

Staging goes through `window.__d` in `proto3d/index.html` — an additive, rules-neutral hook
that moves the camera, the props and the Disturbance meter. It cannot change a tuning
constant, and G10 re-runs `sim/check_drift.py` to prove nothing did.

## Requirements

- **Node ≥ 18** and **Playwright** (`npm i -g playwright`, then `npx playwright install chromium`).
- **ffmpeg with libx264 and aac.** Found in this order: `$FFMPEG`, then `ffmpeg` on `PATH`,
  then whatever `pip install imageio-ffmpeg` provides. Playwright's own bundled ffmpeg is
  deliberately *not* used — it is built without libx264.

`clip/build/` (frames, `bed.wav`, `trace.json`) is gitignored and regenerable. The finished
mp4 is committed so a fresh clone can watch it without a four-minute render.

## Changing it

Timings live in **two** places on purpose: `CLIP-SPEC.md` §3 is the argument, `shots.js` is the
implementation. Change both or they drift — same rule this project applies to `tuning.json`.

Before touching the beat sheet, read CLIP-SPEC §3's note on the 8-second commitment lock and
§7 on the flashlight. Both of them ate a round.
