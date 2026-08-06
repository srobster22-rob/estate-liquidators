# Clip Log

One entry per build round. Newest at the bottom. Same format as `LOOP_LOG.md`:
`C<n> · <what was built> · <what it found>`.

The gates in `CLIP-SPEC.md` §5 are the definition of done. When they are all green the only
remaining changes are taste — that is the line this log exists to keep honest.

---

C1 · Built the whole pipeline: `director.js` (seeded RNG, hand-pumped rAF, caption overlay),
`shots.js` (the seven-beat performance), `render.mjs` (Playwright capture at 1080×1920),
`audio.mjs` (dependency-free synthesized bed), `encode.mjs` (H.264/AAC + the grade), and
`check.mjs` (ten gates). Added a rules-neutral `window.__d` staging hook to `proto3d`.
· **Found:** the prototype renders in the bottom ~15 % of the luma range, which is correct for
the game and unwatchable on a phone. A gamma lift turns the whole frame purple — the fix is a
curve pinned at black (`0/0 0.035/0.012 0.12/0.175 …`) that expands the low-mids only. Also
the HUD is sized for a desktop window and is illegible at 1080×1920; it is scaled 2.45× in the
clip overlay, which is presentation-only and changes no text.

C2 · First full 720-frame build. · **Found:** the take silently failed for three rounds' worth
of staging assumptions — `aimedItem()` measures its 3.2 m grab radius in **3D**, and an item on
the floor sits 1.17 m below the eye, so a spot 3.1 m away on the map is already out of reach.
Moved the approach mark to 2.0 m horizontal. Worth remembering for any authored route: map
distance is not reach distance.

C3 · Fixed the take, all ten gates went green — and the film was still bad. · **Found: green
gates are not a good clip.** A carried item is view-locked 1.15 m down the look ray, so it
covers the bottom two-thirds of a 9:16 frame no matter where you aim, and the entire payoff
beat was a full-screen blue cube with the monster invisible behind it. Added `frameAt()` to
place a world point at a chosen height in frame instead of dead centre, and capped the hero
item at tier 2 because a tier-3 box is 0.42 m half-extent and eats the whole viewport.

C4 · Tried to frame the Curator high, above the cargo. · **Found the real constraint, and it
is a finding about the game, not the clip.** The flashlight *is* the camera, so framing
something high moves it out of the beam — and while you are marked the cone tightens (0.80 →
0.88, on-axis intensity 0.60 → 0.32) on top of the range halving. A Curator 5 m in front of a
marked player renders at ~2 % luma: invisible, after a grade built specifically to rescue this
footage. **The aggro tell blinds you to the thing it is warning you about.** Written up in
CLIP-SPEC §7 with two playtest questions; it may be exactly right, but nobody chose it.

C5 · Rewrote the beat sheet around what the game actually does. Beat 5 stopped being "it cuts
you off" — a shot that cannot exist — and became `blind`: a nervous sweep of an empty room
while two captions say where it is going. The reveal moved onto the frame the light returns,
at the drop. · **Found:** this is the better clip. The rule (`A4`: it paths to the plinth, not
to you) is *proved* by the reveal rather than asserted over footage of nothing, and the beat
order now matches the emotional one. Also found the **8 s commitment lock is a hard timing
tax**: mark and drop cannot be closer than 8 s or the light stays dim through the payoff and
the clip claims something false. Mark 9.0 s, drop 17.95 s, and neither moves alone.

C6 · Pinned the Curator at the plinth after the drop, faded the game chrome off the title
card, moved the deliverable out of the ignored build directory. · **Found:** left to itself,
PATROL sends it to a random shelf the instant aggro clears, so it walked out of frame two
seconds into its own payoff. Pinning it is staging, not a rules change — but it is the third
place the clip needed the Curator held still, which suggests any future clip work wants a
proper "director track" rather than three ad-hoc pins in `update()`.

**All ten gates green as of C6.** The clip is shippable.

---

## Next step (what C7 should attack, ranked)

1. **The 4.5 s blind stretch is still the weakest thing in the clip.** It is honest and it is
   dull: a glowing box on black with two captions. Options, cheapest first — cut it to ~3 s and
   give the extra time to the reveal; add a second *near* surface for the sweep to catch (a
   doorframe 2 m away lights up even at 11.5 m range); or stage the take deeper in the house so
   the sweep has geometry in it. Do not solve it by lying about the light.
2. **Sound has never been heard on a phone speaker.** The bed is 46–55 Hz and phone speakers
   roll off below ~400 Hz. It may be effectively silent where it will actually be watched.
   Add an audible harmonic and re-listen before touching anything visual.
3. **A second clip, not a better first one.** The hand-off — the actual pitch, "you can get rid
   of the monster by handing the vase to your friend" — cannot be filmed at all until there are
   two players. That is a Phase 0 dependency (`BUILD-PROMPT.md`), and it is the clip that
   matters most.
4. **The Curator is two boxes.** Fine for a dev-facing clip, blocks anything user-facing.
   `ART-DIRECTION.md` wants a silhouette.
