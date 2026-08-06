# CLIP-SPEC — the vertical clip

The one-shot vertical clip that has to make a stranger understand the hook in under three
seconds and want to see the game. It is rendered, not filmed: `clip/render.mjs` drives the
real `proto3d` prototype through a scripted performance in headless Chromium and captures
every frame, so the footage is *actual gameplay running the actual verified rules* —
not a mockup, and not a hand-edited screen recording that rots the moment the sim changes.

Regenerate with `node clip/build.mjs`. Everything below is the contract that build checks
itself against.

---

## 1. Format

| Property | Value | Why |
|---|---|---|
| Resolution | **1080 × 1920** | 9:16, the only aspect that fills a phone. |
| Frame rate | **30 fps** | Matches the capture pump exactly; 60 doubles render time for nothing at this motion speed. |
| Duration | **24.0 s** (720 frames) | Long enough for setup → reveal → payoff, short enough to loop before a scroll. |
| Video | H.264 High, yuv420p, CRF 19, `+faststart` | yuv420p is not optional — 444 plays back green on half of mobile. |
| Audio | AAC-LC 128 kbps, 44.1 kHz stereo | Sound-on platform. Silence reads as a broken upload. |
| Target size | ≤ 12 MB | Well inside every upload limit, uploads over a phone tether. |

**Safe areas.** The right 140 px and the bottom 420 px belong to the platform's own UI
(action rail, handle, caption). Nothing that must be read may enter them. The top 180 px
is eaten by some clients' status overlay. All clip text lives inside
**x ∈ [64, 900], y ∈ [200, 1480]** and `check.mjs` enforces it.

**Loop.** The last frame holds the title card and the first frame is near-black, so an
auto-replay reads as a cut rather than a jump. This is deliberate — the clip is not
seamless-looping and should not pretend to be.

---

## 2. What the clip is arguing

One idea, stated once, then *shown* being true:

> **The monster doesn't hunt you. It hunts what you're holding. So put it down.**

That is the whole pitch. Not the quota, not the van, not the four-player comedy — those are
what the *second* clip is for. A viewer who scrolls past at 3 s should still have received
"horror game where the monster follows the loot", because the first two captions carry it
alone even with the sound off.

**What we deliberately do not show:** other players (the prototype is single-player, and a
fake co-op shot would be the exact "pretend a guess is a measurement" failure this project
keeps flagging), the appraiser, the economy screen, and the sunrise fail-state. Every one of
them is a better fit for its own clip than as a crowded second idea in this one.

---

## 3. Beat sheet

Times are seconds from frame 0. `beat` names match `clip/shots.js` so a timing change lands
in exactly one place.

| # | Beat | t | What's on screen | Caption |
|---|---|---|---|---|
| 1 | `hook` | 0.0–3.0 | Dark landing. The Curator crosses the deep doorway, small, unremarked; the camera pans off it onto a piece on the floor. | **"the monster in this house isn't hunting you"** |
| 2 | `bait` | 3.0–6.0 | Camera settles on the piece. Prompt reads `UNAPPRAISED`, then at 4.95 s the value resolves to `$678 TAINTED`. | **"it's hunting whatever you're picking up"** |
| 3 | `take` | 6.0–9.0 | Grab at 6.35 s. HUD flips to `CARRYING $678 TAINTED`. Camera straightens toward the way home. | — (let the HUD talk) |
| 4 | `mark` | 9.0–13.0 | Disturbance jumps to COLLECT. Flashlight range drops 19 m → 11.5 m and the cone narrows, the held piece goes frost-blue, `IT IS COMING FOR YOU`. | **"your light dims when it's you"** |
| 5 | `blind` | 13.0–17.5 | It is walking to the plinth the whole time and **you cannot see it** — a dimmed light does not reach that far. A nervous sweep between the dark doorway and the near corner; the only thing that comes back is a wall at ~2.5 m. | **"and now you can't see it coming"** → **"it's walking to the shelf you took it from"** |
| 6 | `drop` | 17.5–21.0 | Drop at 17.95 s. Aggro clears in one frame, the light snaps back to full range — and it is standing on the plinth, between you and the door. | **"so put it down —"** → **"or hand it to your friend"** |
| 7 | `card` | 21.0–24.0 | HUD fades out, title card over the piece on the floor. | **ESTATE LIQUIDATORS** / *co-op horror extraction* |

**The load-bearing beat is 6, and beat 5 is what buys it.** Beat 5 was originally written as
"it cuts you off" with the Curator visibly closing down the hall — that shot does not exist,
because being marked halves your light's reach *and* tightens its cone, so the thing coming
for you is invisible at 5 m (see §7). The rewrite is better and truer: you go blind, the
captions tell you where it is going, and the reveal lands on the frame the light returns.

**Timing is not free here.** Aggro holds an 8 s commitment lock (`TECH-SPEC` §A3), so the drop
cannot come less than 8 s after the mark or the light would stay dim through the payoff and
the clip would be claiming something the sim doesn't do. Mark at 9.0 s, drop at 17.95 s.
Move one, move the other.

**Caption timing.** Each caption fades in over 8 frames, holds, and fades out over 8. Two
captions never overlap. Beat 6's two lines are one caption with a hard swap at 19.4 s so the
punchline lands on its own.

---

## 4. Sound

No recorded assets exist yet, so the bed is synthesized in `encode.mjs` from ffmpeg
primitives. It is a placeholder with a defined replacement path, not a soundtrack.

It is written sample by sample in `clip/audio.mjs` rather than as an ffmpeg filter graph,
because the payoff at 18.0 s is a *hole* in the sound and holes need sample accuracy.

| Layer | Source | Behaviour |
|---|---|---|
| Room tone | Brown noise, two-pole lowpass | Constant, quiet. The house. |
| Drone | 55 Hz + 82.5 Hz (a fifth), detuned 0.13 Hz between channels | Constant, slow 0.07 Hz swell. |
| Heart | 46 Hz, two thumps per 1.05 s | In from 9.0 s (the mark), out by 19.0 s. |
| Riser | Phase-integrated sweep 150 → 620 Hz | 12.4 s → 15.6 s, arriving as it reaches the plinth. |
| Drop | Everything ducked to 10 % for 260 ms at 17.95 s, back over 340 ms | The relief beat. Silence is the payoff, not a stinger. |

Levels are set by construction — there is no `loudnorm` in the bundled ffmpeg build, so nothing
here is measured, only headroomed to 0.89 peak. The gate asserts only that a stereo AAC track
of the right length exists. **Unverified:** whether these levels survive TikTok's own
normalisation, and whether a 46–55 Hz bed survives a phone speaker at all — it may need a
harmonic an octave up to be audible off-headphones.

---

## 5. Done gates

`node clip/check.mjs` must print `PASS` on all of these. This is the definition of
"the clip is completed" — the loop stops adding beats when these are green and the only
remaining changes are taste.

| Gate | Assertion |
|---|---|
| G1 container | mp4, H.264, yuv420p, ≥ 1 audio stream |
| G2 geometry | exactly 1080 × 1920, 30 fps |
| G3 duration | 24.0 s ± 0.2 s, video and audio within 0.15 s of each other |
| G4 size | ≤ 12 MB |
| G5 not black | no frame of the *graded* video is > 97 % dark pixels, outside the opening fade (frames 0–11) and the last 6 |
| G6 not frozen | no two consecutive frames are identical between the opening fade and the title card (21.0 s) |
| G7 hook | a caption is ≥ 50 % opaque by frame 12 (0.4 s) and the first caption holds ≥ 45 frames |
| G8 safe area | every caption and card bounding box is inside x ∈ [64, 900], y ∈ [200, 1480] |
| G9 rules-true | the sim state trace shows: `marked` is true only while holding; the Curator's pursuit goal is one fixed point, the item's home, and it reaches it (< 1.6 m); `marked` goes false within 1.5 s of the drop |
| G10 no drift | `python3 sim/check_drift.py` still passes — the clip harness never edits a tuning constant |

G5 and G6 read the encoded video back at 24 × 42 greyscale, so they judge what a viewer sees
after the grade, not what the capture pass intended.

G9 is the one that matters. It is why the clip is rendered from the prototype instead of
animated: if a future tuning change breaks the claim the clip is making, the clip fails to
build rather than quietly becoming a lie.

---

## 6. What is deliberately rough

- **One camera.** No cuts, no second angle, no speed ramps. A cut would need a second capture
  pass and a concat, and the single unbroken take is a stronger claim of "this is the game
  running" anyway. Revisit when there is more than one estate worth showing.
- **Placeholder audio.** See §4. Replace whole-file when AUDIO-SPEC's real assets exist.
- **The Curator is two boxes.** ART-DIRECTION calls for a silhouette; this is the prototype's
  stand-in and it reads as "unfinished game" to a viewer. Accepted for a dev-facing clip;
  blocks anything user-facing on a store page.
- **No captions burned for accessibility** beyond the on-screen copy — no spoken word to
  caption yet.
- **The grade is one static curve.** No per-beat looks, no keyframes. It is set for the
  darkest beat, which means the lit beats run slightly flatter than they could.

---

## 7. What building this found out about the game

Not clip notes — findings about Estate Liquidators, recorded here because the clip is the
first thing that ever tried to *look* at the game rather than measure it.

**The aggro tell blinds you to the thing it is warning you about.** `TECH-SPEC` §A7 dims a
marked player's flashlight to 60 %. In the prototype that is range 19 m → 11.5 m *and* cone
0.80 → 0.88, and the cone term is the one that bites: on-axis intensity drops from 0.60 to
0.32, so a Curator at 5 m in front of you renders at roughly 2 % luma — invisible even after
a grade built to rescue this exact footage. The full 6.9 s of its approach happens off-screen.

That may be exactly right — "you know it's coming and you can't see it" is a real horror
beat, and it makes the hand-off the only information you have. But it is not what §A7 says it
is doing, and nobody has decided it on purpose. **Two things worth a playtest:** whether
players ever *see* the Curator arrive at all in a normal night, and whether the 60 % should be
range-only, leaving the cone alone, so the tell dims your world without erasing the threat.

**The commitment lock is a five-second tax on any clip.** 8 s between mark and release means
the shortest honest "marked → put it down → free" arc is 8 s, which is a third of a TikTok.
Fine for the game, worth knowing for every future clip.

**A carried item owns a third of a vertical frame.** `proto3d` hangs the held item 1.15 m down
the look ray; at tier 2 (0.34 m half-extent) that is ±16.5° of a frame only 41° wide, and it is
view-locked, so it cannot be framed around — it is in the middle of every shot you take while
carrying. On a 16:9 monitor this is unremarkable; at 9:16 it is most of the picture. Nothing to
fix in the game — first-person carry looks like this — but it means **any composition for a
vertical clip has to treat the bottom-centre third as unavailable**, and it interacts badly
with the dimmed cone above: the region you can light and the region you can see barely overlap.
