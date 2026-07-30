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
4. **A prop kit of ~40 objects** recombined across estates. Silhouette variety matters far
   more than count.
5. **The Curator.** Last, and least. It's a silhouette in the dark.

## 9. What "easy to look at" means concretely

A test to apply to every scene:

> Stand in a doorway with a flashlight. Can you tell, in under a second: where the exits are,
> which shapes are takeable, which of those you've already appraised, and which of the four
> figures in the room are your friends?

If any of those takes longer than a second, the scene is too busy or too dark — regardless of
how good it looks in a screenshot.
