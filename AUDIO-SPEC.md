# ESTATE LIQUIDATORS — Audio Spec
## The loudness model, proximity voice, and the sound of the Curator

Companion to `DESIGN.md` and `TECH-SPEC.md`.

**Audio is not a department on this project. Audio is the project.** The visual budget for a
game like this is a dark house and a flashlight. Everything a player actually knows — where
their friends are, where the Curator is, whether they're about to lose $900 — arrives
through their ears. Get this system right and mediocre art will pass. Get it wrong and no
amount of art will save it.

This document also replaces the ad-hoc hearing-range table in `TECH-SPEC.md` §A5. That table
was three separate systems (Curator hearing, Disturbance gain, player audibility) with three
independent sets of magic numbers that would have drifted apart within a month. They are now
one system.

---

# PART 1 — THE LOUDNESS MODEL

## 1.1 One number, three consumers

Every noise-producing event in the game carries a single scalar: **Loudness (L)**, on a
0–100 scale. It is authored once, on the event, and three systems read from it:

```
                        ┌─────────────────────┐
                        │   EVENT: L = 90     │  a vase shatters
                        └──────────┬──────────┘
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
      Curator hearing      Disturbance gain    Player audibility
      radius = L × 0.33     Δ = L × 0.09        falloff curve
         = 29.7m               = +8.1            (see 1.4)
```

Change how loud a thing is and *all three* consequences move together, automatically and
correctly. Add a new prop and you author exactly one number for it. This is the single
highest-leverage structural decision in the audio design, and it's worth more than any
individual sound in the game.

**The constants, in one place:**

```csharp
public static class Loudness {
    public const float HEARING_RADIUS_PER_L = 0.33f;   // metres
    public const float DISTURBANCE_PER_L    = 0.09f;   // impulse events only
    public const float SUSTAINED_DIST_PER_L = 0.02f;   // per second, DESIGNATED sources only
    public const float OCCLUSION_PLAYER     = 0.60f;   // × per wall
    public const float OCCLUSION_CURATOR    = 0.85f;   // it hears through walls (§A5)
    public const float LOCALISATION_FUZZ_M  = 3.0f;    // Curator's positional error
}
```

## 1.2 The event table

| Event | **L** | Curator hears at | ΔDisturbance | Notes |
|---|---:|---:|---:|---|
| Crouch-walk | 8 | 2.6m | — | the stealth option, genuinely quiet |
| Voice — whisper | 8 | 2.6m | — | see §2.2 |
| Walk | 20 | 6.6m | — | default locomotion |
| Voice — normal | 25 | 8.3m | — | |
| Dolly on hardwood | 35 | 11.6m | 0.7/s | the cart is a rolling alarm |
| Radio transmit | 38 | 12.5m | 0.8/s | **audible at both ends** |
| Sprint | 45 | 14.9m | 0.9/s | |
| Voice — raised | 45 | 14.9m | — | |
| Appraiser ping | 48 | 15.8m | +4.3 | the information tax, made physical |
| Door slam | 60 | 19.8m | +5.4 | |
| Voice — shout | 65 | 21.5m | — | capped; see §2.2 |
| Crowbar strike | 75 | 24.8m | +6.8 | |
| Breakage — small | 90 | 29.7m | +8.1 | matches `DESIGN.md` §6.5 |
| Breakage — large | 100 | 33.0m | +9.0 | the piano. The whole house knows. |

> ⚠️ **Sustained gain applies only where the table gives a per-second value.** Walking,
> voice, and one-off impacts are marked `—` and contribute **nothing** to Disturbance, even
> though the general `L × 0.02` constant would imply 0.4/s for a walk. That contradiction was
> live in this document until simulation caught it: charging four walking players 1.6/s
> against a 1/min decay pins the meter at 100 inside sixty seconds and deletes the entire
> escalation curve. **A dash in the ΔDisturbance column is a hard zero, not an omission.**

Two things fall out of this table that are worth noticing, because they weren't designed in
directly — they emerged from putting everything on one scale:

- **Shouting is louder than a door slam.** Panicking is mechanically worse than being
  clumsy. That's correct and it's funny.
- **The appraiser is louder than sprinting.** Learning what something is worth costs more
  safety than running away with it unexamined. That's the greed mechanic expressed in
  metres, and it's the exact tension `DESIGN.md` §4.4 needs to survive.

## 1.3 Propagation

Effective loudness at a listener:

```csharp
float EffectiveL(Event e, Vector3 listener, bool isCurator) {
    float occ  = isCurator ? OCCLUSION_CURATOR : OCCLUSION_PLAYER;
    int   walls = PortalTracer.WallsBetween(e.origin, listener);   // portal graph, not raycasts
    float dist  = Vector3.Distance(e.origin, listener);

    float L = e.Loudness * Mathf.Pow(occ, walls);
    L *= Mathf.Clamp01(1f - dist / (e.Loudness * HEARING_RADIUS_PER_L));
    return L;
}
```

**Use the portal graph, not raycasts.** The estate is authored as rooms connected by
doorways; walls-between is a graph query, and an *open* door counts as zero walls while a
closed one counts as one. This means closing doors behind you is a real, physical, tactical
act with an audible consequence — one of the cheapest sources of good play in the genre, and
it costs nothing to implement once the portal graph exists for occlusion anyway.

**The Curator localises imperfectly.** It hears through walls at 0.85 per wall, but the
position it walks toward is fuzzed ±3m. It knows roughly where; never exactly. So it arrives
in the general area and then you have to not move, which is its own small hell.

## 1.4 Player audibility

Standard inverse-distance with a rolloff shaped for legibility rather than realism:

- **Full clarity** to 40% of max radius — inside this, you can localise precisely.
- **Directional but vague** from 40–80% — you know roughly where, not how far.
- **Presence only** from 80–100% — you know it happened; you do not know where.

The middle band is where the game lives. "Something broke. That way. I think." is a more
useful and more frightening piece of information than either certainty or silence.

---

# PART 2 — PROXIMITY VOICE

## 2.1 This is the most important system in the game

Four friends in a dark house is a *voice chat product* with a horror game attached. Voice
gets the best engineer, the most tuning time, and the largest share of the mix.

| Property | Value |
|---|---|
| Falloff | full clarity 0–4m, intelligible to 12m, presence to 18m |
| Occlusion | one wall = heavy lowpass (900Hz) + 0.6 gain; two walls = inaudible |
| Spatialisation | full 3D, HRTF where available |
| Latency target | < 120ms mouth-to-ear |
| Codec | Opus, 24kbps mono, VAD on |

**Doors matter for voice too.** A closed door between you and a screaming friend turns them
into a muffled thump. This is free tension and it comes automatically from §1.3's portal
graph — one system, two payoffs.

## 2.2 Your actual voice volume is a game mechanic

**Mic amplitude feeds the loudness model directly.** Whispering makes you quiet in the
fiction *and* quiet to the Curator. Screaming when the frost crawls up the vase in your
hands does exactly what screaming should do: it tells the house where you are.

```
RMS (relative to calibration)   →   L      →   Curator hears at
  below −12 dB rel.                  8          2.6m
  −12 to −4 dB rel.                 25          8.3m
  −4 to +4 dB rel.                  45         14.9m
  above +4 dB rel.                  65         21.5m   ← hard cap
```

This is the best mechanic in the audio design because it needs no teaching, no UI, and no
tutorial. Players discover in their first bad moment that panicking is punished, and they
discover it by panicking.

**Fairness engineering — this is where it gets ruined if you're careless:**

- **Lobby calibration.** Every player speaks one normal sentence in the van before their
  first night. That sets their personal 0dB reference. Everything above is *relative* — a
  cheap gaming headset and a broadcast condenser must be mechanically identical.
- **Hard cap at L=65.** A hot mic or a loud room can never be worse than shouting.
- **Floor at L=8.** A quiet mic can never be free stealth.
- **Attack 250ms / release 800ms.** Prevents a single cough from spiking your loudness, and
  keeps a sustained shout sustained.
- **Room noise gate**, calibrated at the same time, so a fan or a keyboard isn't a beacon.

**And the one place this spec breaks its own no-HUD rule.** `TECH-SPEC.md` §A7 argues hard
for diegetic-only feedback, and that argument is right *for aggro*, where the signal (a
dimming flashlight) is strong, external, and visible to everyone. It does not transfer here.
You cannot hear your own outgoing volume the way others hear it, so a purely diegetic voice
indicator would punish players for a system they physically cannot perceive.

So: a small mic-fill indicator, on by default, fading out permanently after the third
successful night. The principle underneath, worth keeping for every future feature —

> **Diegetic-only is correct when the player can perceive the signal. When the signal is
> something the player emits but cannot sense, show them.**

## 2.3 The radio

Radio is a *broadcast*, and broadcasts are loud at both ends (L=38, ~12.5m). Speaking into
your radio makes noise where you are, and your voice comes out of every other crew member's
radio, making noise where *they* are. Calling for help endangers the person you're calling.

That's the whole design. It needs no further mechanics.

- Radio voice gets deliberate degradation: bandpass 300–3400Hz, light bitcrush, squelch tail.
  Ugly on purpose, so radio and proximity voice are never confused for one another.
- **Radio ignores occlusion and distance.** It is the only channel that does.

## 2.4 The dead

Dead players speak through the van's radio (`DESIGN.md` §5) — which means the dead are
audible in the world, at L=38, wherever a living crew member is standing.

The dead can help. The dead can also get you killed by shouting advice at the wrong moment.
Nothing else needs to be built for this; it is entirely a consequence of §2.3 and it is one
of the better emergent jokes in the design.

## 2.5 Accessibility alternatives

The voice-volume mechanic cannot be the *only* way to control your loudness.

- **Volume keybind** — a three-state toggle (whisper / normal / shout) that overrides mic
  amplitude, for players who can't reliably modulate voice or who play in shared spaces.
  Mechanically identical, no disadvantage, no stigma. Available to everyone, not gated
  behind an accessibility menu.
- **Text-to-crew** — typed messages emit at L=25 from your position, with a synthesized
  voice. Same cost as speaking normally.
- Neither option is weaker than using your voice. If either turns out to be *stronger* in
  playtest, nerf the mechanic, not the accessibility path.

---

# PART 3 — THE CURATOR'S SOUND

## 3.1 The approach layer — implementing the fairness contract

`TECH-SPEC.md` §A6 rule 2 promises the Curator is **always audible for ≥8m before contact**.
That promise is kept here, or it isn't kept at all.

```
BUS: Curator_Approach
  - occlusion floor 0.45  (never fully blocked, by any geometry, ever)
  - never ducked by any other bus, including breakage and voice
  - never virtualised, regardless of voice budget pressure
  - drives: dragging cloth, floorboard groan, the sound of something heavy set down
```

This bus is a contract, not a sound design choice. It must be impossible for a level, a mix
state, or a performance spike to break it. Write an automated test: spawn the Curator at 8m
through every wall configuration in the estate library and assert the bus output exceeds the
audibility floor. Run it in CI on every level change.

> **Half of that test exists** as V5 in `sim/validate_estate.py` (R19), and building it
> surfaced something this section implies but never says outright: **with the 0.45 floor
> applied, no wall configuration can break the bus.** 60 × 0.45 = 27 against an audibility
> floor of 25, and that is the *worst* case at any wall count. So the audio half of the
> contract is satisfied by construction and the CI test above can only ever catch a
> regression in the floor itself — which is worth having, but is not the risk.
>
> The risk is geometric. **You cannot be audible for 8m before contact if the floorplan
> does not contain 8m of approach**, and that is a thing a level author breaks by accident
> every time they tuck a valuable object into a small side room. V5 now enforces it. The
> remaining half of the test — asserting the *engine* honours the 0.45 floor rather than
> trusting the constant — still wants writing, in the FMOD project rather than here.

## 3.2 Its vocabulary

The Curator never roars, never screams, never stings. It is a caretaker doing a job it finds
tedious, and it is *annoyed with you*. All of its audio is domestic:

| State | Sound |
|---|---|
| DORMANT | nothing. The house is empty. |
| PATROL | slow footsteps on hardwood; the click of a display case being closed; a cloth being folded |
| **FIXATE** | **everything stops.** Its own audio cuts to silence for 2.0s. The room tone drops a third. This is the tell. |
| PURSUE | footsteps only. Same tempo as PATROL. It is not in a hurry. That's the point. |
| RETRIEVE | one sharp intake of breath, and the sound of an object being taken from a hand |
| RESEAT | footsteps, and the small satisfied sound of an object placed correctly on felt |
| COLLECT (T4) | the footsteps are faster and the domestic sounds stop entirely |

> **R30 — a gap this vocabulary does not cover: approaching a tier boundary.** Measured in the
> prototype, the ratcheting floor *masks* accumulated noise — while a crew's noise sits under
> the floor, scanning moves the meter not at all, and then it moves fast. A crew that appraises
> 20 objects reads Disturbance 57; one that appraises 29 reads 92. The table above gives each
> **state** a sound, but nothing distinguishes "comfortably inside PATROL" from "one more room
> and it hunts you", so players get no warning before the cliff.
>
> **This wants a within-state gradient**, and PATROL is the state that needs it: the domestic
> sounds (the case closing, the cloth folding) getting *closer together* as Disturbance climbs
> toward 60, so the house audibly runs out of patience before anything changes. It stays
> diegetic, costs no UI, and reuses sounds that already exist — but it is a real addition to
> the model, not a mix note, and it should be specced before Milestone 2 rather than
> discovered in a playtest.

**Silence is its scariest sound.** FIXATE cutting to nothing does more work than any
designed roar, because the player's own audio system has just told them something is about
to happen and they don't know what. Never fill that gap.

## 3.3 It is never scored

No music cue fires when it appears. No stinger on FIXATE, no swell on PURSUE. The moment
players learn the soundtrack tells them they're in danger, they stop listening to the house
and start listening to the score — and the house is the whole game.

Music exists in exactly three places: the van (lobby), the sunrise timer's last 90 seconds,
and the ledger screen. Nowhere else, ever.

---

# PART 4 — ITEM AUDIO

## 4.1 The marked hum

When a player becomes the attention target (`TECH-SPEC.md` §A7), the carried item emits a
low hum: **8m radius, L=0** — it is audible to humans but does *not* feed the loudness model
and does not attract the Curator. It's a readout, not an event.

Sub-bass fundamental around 55Hz with a slow 0.7Hz amplitude wobble. It should be felt more
than heard, and it should be immediately obvious which *object* it's coming from, because
the whole hot-potato mechanic depends on players knowing which thing is the problem.

## 4.2 Malignant mimicry

A malignant item speaks in a teammate's voice (`DESIGN.md` §4.2), using real audio from
earlier in the run.

**Implementation:** the host keeps a 90-second ring buffer per player, segmented into 1–2s
chunks at VAD boundaries. A malignant item plays a chunk through its own spatial emitter,
pitched down 8% with light formant shift, at intervals of 40–90 seconds.

Selection rules, which are what make it land:

- Prefer chunks from a player who is **currently far away** — hearing Dave from a room Dave
  is not in.
- Never a chunk recorded in the last 20 seconds; the uncanniness needs distance.
- Prefer emotionally flat chunks over screams. "yeah, I got it" in an empty hallway is worse
  than a scream, by a wide margin.

**Comfort and consent.** This records and replays people's real voices. It needs a lobby
toggle, host-side, default on, clearly labelled — and when off, malignant items substitute
pre-recorded VO instead of losing the mechanic. The ring buffer is memory-only, never
written to disk, and is destroyed at run end. Say this plainly in the options menu; players
will ask, and the honest answer is a good one.

## 4.3 Everything else

- **Every object gets a material class** (glass, porcelain, wood, metal, cloth, taxidermy)
  driving impact, scrape, and settle sounds. Six classes cover the entire game.
- **Impact velocity drives everything** — pitch, layer count, and the L value from §1.2.
  Setting a vase down gently is genuinely quiet; the same vase at 4 m/s is L=90 and the
  house knows.
- **Scrape loops** on dragged furniture. Dragging is the loud, cheap alternative to carrying
  properly, and it should sound like a mistake you're making on purpose.

---

# PART 5 — MIX

## 5.1 Bus priority

Ducking, highest priority first. When something has to give, it gives from the bottom.

```
1. Curator_Approach     never ducked, never virtualised     (§3.1 contract)
2. Voice_Proximity      ducks everything below it
3. Voice_Radio
4. Item_Marked_Hum      the aggro readout
5. Player_Foley
6. World_Impacts
7. Room_Tone
8. Music                three places only (§3.3)
```

## 5.2 Dynamic range and the troughs

The mix's job is to make quiet *mean* something.

| Moment | Target LUFS | Why |
|---|---|---|
| DORMANT house | −34 | genuinely, uncomfortably quiet |
| Normal hauling | −26 | |
| PURSUE | −20 | |
| Breakage / COLLECT | −14 | |

That's a 20 LUFS working range, which is enormous, and it's the point. The design's troughs
(`TECH-SPEC.md` §A2's RESEAT breather) are only breathers if the mix drops with them: when
the Curator turns to carry the vase home, **the house exhales** — room tone returns, low-end
rumble releases over ~4s. Players will feel the safety before they consciously understand
they're safe.

Never compress the game into a consistent loudness. The whole point is that the quiet parts
are quiet enough to hear a floorboard three rooms away.

---

# PART 6 — ACCESSIBILITY

Sound is the primary information channel, which means a player with hearing loss is playing
a different and much harder game. Options, all default-off except captions:

- **Captions for diegetic audio**, with a direction arrow and a distance band. Not a
  transcript — an information channel: `↖ floorboard · near`.
- **Visual sound indicator** — a subtle screen-edge bloom at the bearing of significant
  events, intensity by effective L. Deliberately excluded from the default experience
  (`TECH-SPEC.md` §A7 argues for diegetic-only), and equally deliberately available.
- **Mono downmix** for single-sided hearing, with the front/back ambiguity resolved by the
  caption arrows.
- **Voice keybind** (§2.5) as a first-class alternative to mic amplitude.
- **Curator approach boost** — a separate slider for the §3.1 bus only, so the fairness
  contract can be turned up without turning the whole game up.

## 6.1 The comfort options

Horror needs an exit, and the presence of an exit makes people braver:

- **Mimicry toggle** (§4.2) — real-voice replay off, VO substitute on.
- **Reduce sudden loudness** — caps the peak-to-average ratio without flattening the mix.
- **Heartbeat/breathing intensity** — the player's own panic audio, which some find
  immersive and some find genuinely distressing.

---

# PART 7 — TECHNICAL

## 7.1 Middleware

**Recommendation: FMOD Studio.** Mature Unity integration, the free tier covers a small
project comfortably, and its bus/snapshot model maps almost one-to-one onto §5. Wwise is
equally capable and heavier to learn. Unity's built-in audio will not do the dynamic mix in
§5.2 without a lot of custom work.

> ✅ **Verified 2026-07-29 — see `STACK.md`.** FMOD's indie tier is free under $500K project
> budget and $200K/yr gross revenue, with no revenue share. That covers this project with
> room to spare. FMOD-on-Unity-6 specifically wasn't directly confirmed — very likely fine
> given FMOD's first-tier Unity support, but check their compatibility docs rather than
> trusting this sentence.

**Voice chat integration is the integration risk.** The voice solution and the audio
middleware must share a spatialiser, or crew voices will sit in a different acoustic space
than the world and the illusion collapses.

**Downgraded, not cleared.** Third-party walkthroughs exist covering exactly this three-way
combination — FMOD + Dissonance + FishNet — for dynamic voice manipulation, so the
combination is known to work and this is no longer an unknown-unknown. It is still worth an
afternoon in a throwaway scene before it's in the critical path: precedent existing is not
the same as it working on your Unity version, on your machine, today.

## 7.2 Budgets

| Resource | Budget |
|---|---|
| Real voices | 48 |
| Virtual voices | 192 |
| Voice-chat streams | 4 (crew) + 1 (radio bus) |
| Portal-graph occlusion queries | 30/frame, amortised over 4 frames |
| Ring buffer (mimicry) | 4 × 90s Opus ≈ 1.1MB total |

Occlusion is the only real cost, and it's why §1.3 uses a portal graph rather than raycasts:
one graph query beats a dozen raycasts, and it produces *better* answers because an open
door is genuinely different from a hole in a wall.

---

# PART 8 — BUILD ORDER

| # | Build | Validates |
|---|---|---|
| **D1** | Proximity voice, spatialised, 2 clients | the actual product |
| **D2** | Portal graph + occlusion, for voice only | doors matter — testable with two people and a door |
| **D3** | Loudness model + event table, no Curator | one number, three consumers |
| **D4** | Mic amplitude → L, calibration, cap/floor | §2.2 — the best mechanic in the spec |
| **D5** | Curator_Approach bus + CI audibility test | the fairness contract is real |
| **D6** | Material classes, impact velocity → L | the world gets loud correctly |
| **D7** | Dynamic mix, snapshots, the exhale | §5.2 |
| **D8** | Marked hum, mimicry + toggle | §4 |
| **D9** | Captions, visual indicator, comfort options | §6 |

**D1 and D2 come before everything else in the entire project** — before the Curator, before
the physics tuning, arguably before Milestone 1 in `DESIGN.md` §11. Two people, a door, and
spatial voice is a fifteen-minute test that tells you whether the foundation of this game
feels right. Nothing else you can build that early is worth as much.
