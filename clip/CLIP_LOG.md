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

C7 · Attacked the blind stretch, the weakest 4.5 s in the clip (it beat the audio work because
it is 19 % of the runtime and sits immediately before the payoff — a viewer who leaves, leaves
here). Doubled the dolly rate for parallax, re-aimed the sweep from 6–8 m surfaces to the near
corner, and staged a second piece for the beam to catch. · **Found the off-axis band is mostly
theory.** Reasoning said: the cargo owns the middle ±16.5°, the dimmed cone reaches 28°, so
put things in the 16.5–28° ring where they clear the cargo and are still lit. Tried it — aimed
the sweep *past* the dressing piece — and it came back emptier than before, because that ring
is open floor at grazing incidence. Reverted. **The only thing a marked player reliably sees is
a wall inside ~3 m**, and that is what the near-corner aim brings back. The dressing piece
never appears: centre it and the cargo hides it, offset it and the cone barely lights it.
· Net: the beat is better (parallax, a wall sweeping through frame, the cargo rotating rather
than sitting) and still the weakest thing in the clip. Two rounds of framing have now hit the
same wall from opposite directions, which says the constraint is structural, not compositional.

C8 · Went after C7's root cause — shrink the view-locked cargo by staging a tier-1 hero — and
**the hypothesis was already false when it was written.** Probed the actual staged item across
all three tier caps: `heroTier<=1` and `heroTier<=2` both select the same piece, `$678 tainted,
tier 1`. The clip has been carrying the smallest item in the game since C3. **Correction to
C4 and C7: the cargo is ±12.7°, not ±16.5°** — that figure was inferred from a tier-2 size the
clip never used, and it has been propagated through two rounds of reasoning. Fixed in
CLIP-SPEC §7. There is no smaller size class, so this lever does not exist.

· **What did work was recovering the framing height C5 gave away.** The dimmed cone's falloff
is not linear, and nobody had measured it: on-axis intensity is 0.394, and off-axis it holds
97 % at `up` 0.10, **87 % at 0.22**, and only 73 % at C4's 0.32. C4 lost the shot at 0.32 and
C5 over-corrected all the way to 0.10–0.12 — paying away 260 px of usable frame to buy 8 % of
light. Moved beats 4 and 5 to 0.22, which clears the cargo's top edge (y 1009) and puts the
near wall visibly in the upper frame for the first time. The blind beat now has architecture
sweeping through it rather than a box on black. · Standing lesson, twice earned now: **measure
the falloff before framing to it.** Both bad framing decisions in this project came from
treating a smoothstep as if it were a cliff.

C9 · Went after the sound — the only remaining item verifiable without a person listening.
Built a phone-speaker model (48 dB/oct below 500 Hz, top at 8 kHz) and **validated the
instrument against tones before trusting it**: unity at 1 kHz, −12 dB at 500 Hz, −58 dB at
200 Hz. First attempt at measuring used a 12 dB/oct filter, which leaked the 55 Hz drone in at
−49 dBFS and drowned the very thing being measured — the instrument was reading itself.
· **Found a real bug that had been shipping since C1.** The bed measured **−61.7 dBFS** through
the phone model: inaudible on the device the clip exists for. Chasing why, the room-tone layer
turned out to be at gain 26 — **+10 dBFS RMS, peaking at 11.9** — so `toWav`'s peak normaliser
was scaling the *entire mix* down by 22.5 dB on every build. The drone, heart, riser and drop
were all 22 dB below where they were written. The bed was, in effect, brown noise. One
unmeasured constant, silently rewriting every other level for eight rounds.
· Fixed the gain structure (room tone to −32 dBFS, master trim to unity, and the normaliser
demoted from level control to a 0.98 clip guard that should never fire), then added the
partials and transients a phone can actually reproduce: drone partials at 220–880 Hz, an air
layer above 1.1 kHz, a 700–1400 Hz knock on each heartbeat, and the riser moved from 150→620
to 210→1150 Hz. **Phone-band went −61.7 → −30.5 dBFS, a 31 dB improvement**, peak −1.5 dBFS.
· Added **gate G11**, which measures the encoded audio through the phone model. · Standing
lesson: **a gate that only asserts existence is not a gate.** "A non-silent stereo AAC track of
the right length" passed happily on a bed 31 dB below audible. Every gate should be able to
fail on plausible work.

C10 · Read `ART-DIRECTION.md` properly before starting, which is what C4, C7 and C8 should have
done. §6: *"Carried objects sit in view and must not block it. Held items render slightly low
and offset so they occlude as little as possible."* **The fix for the constraint that ate three
rounds was already specified, and the prototype had simply never implemented it** — items hung
dead centre, 1.15 m down the look ray. · Implemented the specced pose in `proto3d`: 1.05 m
forward, 0.24 m screen-right, 0.55 m below the eye. Pose only — nothing reads those coordinates
until the item is dropped, and drift is still 55/55. The centre of the frame came back, and
beats 3–6 were re-centred onto the beam axis (`up` 0.22 → 0.08) where the light is 97 % rather
than 87 %. First build where the room is visible while you are carrying.
· **Two findings.** First, the sign convention: the natural-looking `right` vector puts the
cargo on screen-*left*, where the captions live — the view basis is `[-dz, 0, dx]`, and the
prototype's strafe vector is the opposite of it, which is worth a look on its own. Second, and
bigger: **G6 was wrong, not the footage.** With the cargo out of centre the mark beat went
nearly black, and at 24 × 42 greyscale a dark shot's genuine camera motion falls below
quantisation — the gate reported freezes on moving footage. Raised the freeze test to 96 × 170
(a truly dropped frame is identical at any resolution) and gave the beat a real subject: one
slow pass across the near east wall at ~4 m, close enough to actually light. · Same lesson as
C9, third time: **validate the instrument before believing what it says about the work.**

C11 · Rebuilt the Curator to `ART-DIRECTION.md` §5 — "tall, narrow, domestic, reads as staff,
not monster, no face ever". It was a 2 m column with a cube on top, which reads as placeholder
art in the one shot the whole clip is built around. Now seven boxes at the same cost: long coat
to the hip, narrower torso, a shoulder bar, two long hanging arms, a neck and a small pale
head, 2.29 m total. **The small head is the trick** — it is what makes the figure read tall;
the previous version's cube head was 0.20 m and made it read stocky. Visual only, no rules, no
constants, drift 55/55. · **Found:** the renderer has no rotation — `M4.trs` is translate and
scale only — so the Curator is necessarily axis-aligned and never turns to face you. Invisible
with two symmetric boxes; the moment it has arms it is a real constraint, and it is the first
thing that will need fixing if it ever gets an animation. A figure that walks at you without
ever turning is uncanny in a way that is currently free and later will not be.

C12 · Added the rotation the renderer never had. `M4.trsY` (yaw + scale), an optional yaw on
`drawBox`, a `yaw` on the Curator that turns toward its heading at 6/s in `walkTo`, and — the
part worth having — **it turns to face you during FIXATE**, the two seconds it is doing nothing
but noticing you. Held items now inherit the carrier's yaw too. Visual only, drift 55/55.
· **Found:** held items had been world-axis-aligned all along, so the box appeared to *rotate
in your hands* every time you turned. Invisible in a 16:9 screenshot, obvious in 24 seconds of
continuous motion, and it reads as a physics glitch rather than a stylisation. Fixed by the
same yaw. · **Also worth recording: normals came through rotation for free.** No inverse-
transpose was needed, because every box normal is a coordinate axis, so a non-uniform scale
changes its length but not its direction and the shader already normalises. That is only true
while the geometry is boxes — the first non-box mesh will need a real normal matrix.
· FIXATE facing is the first thing in the prototype that communicates intent through movement
rather than through the HUD, which is what `ART-DIRECTION.md` §5 asked for all along.

C13 · Gave the Curator a gait, per `ART-DIRECTION.md` §5's "moves like a person doing a job it
finds tedious". Six lines: 0.75 m stride, 25 mm of vertical rise on the torso and above, 10 cm
of counter-swung arms. · **The one decision worth recording is that the phase is driven by
distance travelled, not by elapsed time.** A time-driven bob keeps walking on the spot whenever
the character stops, which is the classic tell of fake animation — and this Curator stops
constantly (FIXATE, arriving at a plinth, the clip's own staging pins). On distance it stands
genuinely still, then starts moving again mid-stride. · Deliberately under-animated: §5 says
never a monster run, and the horror is that it isn't hurrying.

---

## Next step (what C14 should attack, ranked)

1. **Someone has to listen to it.** G11 proves the bed is audible; it cannot prove it is good,
   and the mix has never been heard by a human. The knock and hiss levels in particular were
   set to hit a number, which is exactly how you get a bed that measures well and sounds like
   a modem. **This needs the owner, not another round.**
2. **A second clip, not a better first one.** The hand-off — the actual pitch, "you can get rid
   of the monster by handing the vase to your friend" — cannot be filmed until there are two
   players. Phase 0 dependency (`BUILD-PROMPT.md`), and it is the clip that matters most.
3. **Nothing else in the prototype can be improved from a clip.** C10-C13 walked the whole
   visual chain the clip touches — carry pose, silhouette, facing, gait — and it is now ahead of
   what a 24-second take can show. Further prototype work should be driven by playtests, not by
   framing.
4. **The blind beat is done being optimised.** C7 and C8 both improved it and both hit the same
   structural wall. Anything further needs a shot where the player is *not* carrying, which
   contradicts the beat. Leave it until item 2 makes a second clip possible.
