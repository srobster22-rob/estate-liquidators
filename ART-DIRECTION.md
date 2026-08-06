# ESTATE LIQUIDATORS — Art Direction

The brief: *good and funny. It doesn't have to be the best, but it has to be easy to look at
and enjoyable.* First person, for immersion.

That is a achievable brief, and this document is about spending the budget where it shows.

---

## 1. The core decision: a straight-faced house, a ridiculous crew

This is the single most important call in the document, and it's lifted from what actually
makes the reference games work.

**In R.E.P.O. and Lethal Company the environment is not funny.** The facilities are grim,
dark, and oppressive. The comedy comes from *the players* — goofy proportions, flailing
physics, four idiots in a serious place. If the level had been cartoonish too, there'd be no
tension to puncture, and nothing to be funny *against*.

So:

| | Treatment |
|---|---|
| **The estate** | Played completely straight. Dark, heavy, over-furnished, genuinely unpleasant. No wacky props, no joke paintings, no comic sans on the ledger. |
| **The crew** | Absurd. Squat bodies, oversized heads, stubby arms, a walk cycle with too much bounce. Boiler suits and rubber gloves in colours that were never meant for a haunted house. |
| **The Curator** | Straight, and the straightest thing in the game. It is never funny. It is the reason the funny stops. |

The joke is the mismatch — four cartoon removal men in a real haunted house. That contrast is
free comedy *and* free horror, and it costs nothing to produce because the expensive-looking
half (the house) is made of darkness.

## 2. Rendering: flat-shaded low-poly, not photoreal, not PS1-nostalgia

**No PBR. No photorealism. No normal maps.** Those are where small teams die, and they'd
fight the visual clarity a game about spotting objects in the dark needs.

**Also not deliberate PS1 crust.** Lethal Company owns that look, and copying it reads as
derivative rather than distinctive.

The target is **flat-shaded low-poly with clean silhouettes** — think a well-lit stop-motion
set that someone turned the lights off in:

- **Untextured or near-untextured.** One flat colour per material, occasionally a subtle
  gradient. Colour identifies material class (wood, porcelain, brass, cloth, taxidermy), which
  the audio spec already needs for impact sounds. One system, two payoffs.
- **Baked vertex AO** in the corners and under furniture. This is what stops flat shading
  looking cheap, and it's nearly free at runtime.
- **Chunky, readable geometry.** Nothing under ~200 tris that doesn't need it. A vase should
  read as a vase in silhouette at 8 metres in a flashlight beam, because that is the actual
  gameplay question.
- **Hard edges, no bevels.** Faster to model, and it suits the shadow-heavy lighting.

**Why this is the right cost/benefit:** flat colour and low poly is the one style where "made
by a small team" and "deliberate aesthetic choice" are indistinguishable to the player.

## 2.1 Reading a room: how value spread is telegraphed

`LEVEL-SPEC.md` §2.1 and `DECISIONS.md` D-23 make every room declare a **spread** —
`uniform`, `mixed` or `curio` — describing how much its objects differ from each other in
value. That declaration is worth **about half the appraiser's entire value** (`ECONOMY.md`
§9: a flat estate is worth +4.2% over blind hauling, a mixed one +8.8%), and it is worth
exactly nothing unless the player can *see* which kind of room they walked into.

**The requirement, stated as a test:** standing in the doorway, in the dark, with a
flashlight, a player must be able to tell in about a second whether this room rewards
stopping — **without learning what any single object is worth.** That second clause is D-10
and it is not negotiable: you may read the room, never the item.

### The prototype's telegraph does not port, and it is worth knowing why

`proto/index.html` signals spread with **silhouette size variance** — in a curio room the
shapes are wildly different sizes, in a uniform room they are identical. It works there and
it measures cleanly (R20). **It will not work in first person.** Top-down, a bigger shape is
unambiguously a bigger object. In perspective, a large object far away and a small object
close up subtend the same angle, so size variance is destroyed by exactly the thing the game
is made of: standing in a doorway looking across a room. **Any cue that survives here has to
be perspective-invariant.**

Three do, and all three are already paid for by decisions made for other reasons:

| Cue | `uniform` | `curio` | Why it survives |
|---|---|---|---|
| **Repetition** | the *same* silhouette repeated — six identical clay pots, a shelf of matched book spines | every object a different silhouette class: tall-thin, squat-round, flat, irregular | "these are all the same thing" reads at any distance and through fog. It is the strongest of the three. |
| **Material variety** | one material class, repeated | brass beside porcelain beside taxidermy | §2 already gives each material class one flat colour, for the audio spec's impact sounds. Colour survives distance and fog far better than size. One system, three payoffs now. |
| **Arrangement** | grid, row, or stack — storage. Even spacing. | individually placed, each with its own space, its own pedestal or doily | Regular spacing reads as rhythm and is perspective-invariant in the same way repetition is. |

**Lighting carries it too**, at no extra cost (§3). A `curio` room wants small pooled lights —
a display lamp, a glass case — so objects read as individually considered. A `uniform` room
wants a single flat wash, or nothing at all. The house is telling you what it thought of its
own contents, which is better fiction than a signal and does the same job.

### What this costs production

**The ~40-object prop kit in §8 must be authored partly in matched sets.** A kit of forty
*unique* objects cannot express `uniform` at all — the one thing a uniform room needs is six
to eight instances of the same silhouette. Budget the kit as roughly **25 unique objects plus
5 matched sets of 6**, rather than 40 unique. This is cheaper than 40 unique, which is a
pleasant thing to be able to say about a requirement.

**And it constrains the "ridiculous" half of §1 slightly.** A room of six identical clay pots
is not funny. Uniform rooms are the straight-man rooms; put the jokes in the curio rooms,
where they are also mechanically rewarded. That is a better distribution than scattering them
evenly, and it means the funniest objects in the house are the ones players are being paid to
stop and look at.

### If the telegraph fails

**It degrades rather than collapsing, and the size of the loss is known.** R17/R18 modelled
players misreading rooms: a perfect read is worth +8.8% over blind hauling, and a read *noisier
than the entire range of rooms* still returns +5.6% — above what any spread-blind strategy
manages. So a bad telegraph costs roughly **two-thirds of D-23's value**, not all of it.

That is the budget argument for spending real art effort here, and also the reason not to
panic: if the first playtest shows players can't classify rooms, the mechanic is worse but
alive, and the fix is art, not design.

## 3. Light is the whole art budget

The house is 90% black. What you can see, you can see because someone chose to light it.

- **Flashlights are the primary light source**, and they are the game's aggro tell
  (`TECH-SPEC.md` §A7): the marked player's light dims to 60% and shifts cold. That has to be
  the most legible visual event in the game.
- **Baked lighting only for the few lit spaces** — a moonlit conservatory, a lamp somebody
  left on. Everything else is dynamic flashlight.
- **Heavy distance fog**, tuned so you can never see the far end of a long room. Fog is a
  performance budget and a horror device at the same time.
- **Restrained colour temperature.** Warm flashlight against cold moonlight. When a light goes
  cold, it means something.

## 4. Palette

Deliberately narrow, so that *value* (light and dark) does the work rather than hue:

| Role | Where |
|---|---|
| **Ink black** | the house's default state, the fog, the Curator |
| **Bone / dust** | plaster, dust sheets, the few lit surfaces |
| **Brass** | the appraiser, the van, valuable fittings — the colour of money |
| **Verdigris** | patina, the conservatory, anything old and outdoors |
| **Rust** | curse and damage. The only saturated colour in the game, used sparingly. |
| **Crew colours** | four unmistakable boiler suits, and they are the only cheerful thing on screen |

**The crew colours are a gameplay system, not decoration.** In a dark house at 12 metres, the
one thing you must always be able to identify instantly is *which of your friends that is*.

## 5. The Curator's design

Never fully seen. This is a budget decision and a design decision at once.

- **Silhouette and hands only.** Tall, narrow, domestic. Reads as staff, not monster.
- **No face, ever.** No reveal, no cutscene. Players will invent something worse than we can
  model, for free.
- **It moves like a person doing a job it finds tedious.** Never a monster run. The horror is
  that it isn't hurrying, because it doesn't need to.
- Movement, not geometry, carries the character — which means the animation budget matters far
  more than the model budget.

## 6. First person, and what that costs

First person for immersion, per the brief. Two consequences worth planning for:

- **You still need visible bodies.** Look down and see your own boots and gloved hands; look
  across the room and see your friends' full ridiculous bodies. First person without a body
  loses the comedy that §1 is built on. Budget for full character models regardless.
- **Carried objects sit in view and must not block it.** Held items render slightly low and
  offset so they occlude as little as possible — but they *must* still visibly clatter into
  doorframes, because that collision is the product (`TECH-SPEC.md` §B0).

## 7. UI

Almost none. `TECH-SPEC.md` §A7 commits to diegetic feedback, and that decision holds here:
aggro is a dimming flashlight and frost on the item, not an icon.

- **In-world where possible.** The appraiser has a physical readout. The van has a physical
  slot count.
- **The ledger is the one screen that gets typographic care**, because reading the itemised
  damages aloud is a designed ritual (`DESIGN.md` pillar 4). Set it like an auction catalogue.
- One typeface, one weight, generous letter-spacing. Nothing else.

## 8. Production order

Cheapest thing that makes the game look intentional, first:

1. **Lighting and fog.** Before any asset work. A grey-box room with good fog and a flashlight
   already looks like this game.
2. **Crew characters.** They're the identity, they're on screen constantly, and they carry the
   tone.
3. **A material-class kit** — one flat material per class, ~8 total. Every prop is built from
   these.
4. **A prop kit of ~40 objects** recombined across estates — as **~25 unique plus 5 matched
   sets of 6**, not 40 unique (§2.1). Silhouette variety matters far more than count, and it
   is now load-bearing rather than advice: it is the signal a player reads a room's value
   spread from.
5. **The Curator.** Last, and least. It's a silhouette in the dark.

## 9. What "easy to look at" means concretely

A test to apply to every scene:

> Stand in a doorway with a flashlight. Can you tell, in under a second: where the exits are,
> which shapes are takeable, which of those you've already appraised, which of the four
> figures in the room are your friends, and **whether this room is worth stopping in**?

The last one is §2.1's requirement and the newest, so it is the one most likely to be missing.
Test it directly rather than by feel: **show a player a still frame of a room for one second
and ask them to call it `uniform`, `mixed` or `curio`.** Target 80% correct. Anything at or
below chance means the room is not telegraphing and half the appraiser's value is unreachable
(`DECISIONS.md` D-24).

If any of those takes longer than a second, the scene is too busy or too dark — regardless of
how good it looks in a screenshot.
