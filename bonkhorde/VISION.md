# BONKHORDE - the vision

The standing brief. One section per answer from the vision interview, dated.
The loop (LOOP_LOG.md) takes its direction from here.

## 2026-09-08 - Q1: when BONKHORDE is at its best, what is the player doing?

**Answer: any of them - the options should depend on the playstyle.**

Asked to choose between outrunning the horde, building an absurd machine, raising
a creature and exploring the world, the answer was that it is not a choice. All
four are real ways to play and the game should meet the player where they are:
what BONKHORDE *offers* should depend on how the player is actually playing.

What that means concretely, in this build:

- The draft is the game's main offer, and it deals from one pool by weight,
  ignoring what the player has been doing for the last two minutes. A player
  who never stops moving and one who stands and fights get the same hand.
- So "the options depend on the playstyle" is, first, a draft that reads the
  run and weights the hand toward the way it is being played - without tunnelling
  it, because a build that can never surprise you is not a build.
- Later rounds can extend the same idea to the rest of the offer: which events
  the world puts in reach, what the shop leads with, which creature the menu
  suggests.

Not: a difficulty rubber band, and not a game that decides for the player. The
player's own play is the input; the offer is the output; the choice stays theirs.

## 2026-09-08 - Q2 (unprompted): what is missing

**Answer, in the user's words, condensed:** the direction is better, but the
upgrades and level-ups have to be MEANINGFUL. A companion. Upgrades that change
the overall flow of the character - switching the fire creature to water mid-run,
mutations, "more important stuff we can take along the way" - the kind of pickup
that gets a player going, in the register the popular roguelikes use. The map
design is bland and has no story; walking around is blocky and the floor reads as
plain lines and dots. The mobs are weak and there is no real boss to work toward:
the end monster has to be strong and it has to be the thing every run is going
for. More story and design, less number-tuning. And the fire line is the
favourite - "I'm playing as two" - a creature that duplicates itself.

**The standing order this sets, in priority:**

1. **Level-ups that change the run, not the numbers.** Mutations, a companion,
   an element switch mid-run. A pick you remember, several times a run.
2. **The map has to be a place with a story.** Ground, silhouette, landmarks and
   region identity - not a blocky floor with dots on it.
3. **The horde and the final boss.** The mobs need teeth and variety; the end
   monster has to be the strong thing the whole run is aimed at.
4. **Per-creature playtesting.** Each line looked at and played on its own.

Read together with Q1: the offer should depend on the playstyle AND the offer
itself has to be worth depending on.

## 2026-09-08 - Q3: which of Q2's "meaningful level-ups" to push hardest

Asked which of the three things Q2 named that now exist in some form - BROOD (a
hatchling that fights beside you), TIDEBORN (fire to water mid-run, coat and all),
SECOND HEAD (a literal second head on the animal) - the next round should push.

**Answer: playing as two, PROPERLY.** SECOND HEAD is currently cosmetic plus a
+55% copy on every weapon. It should be a real second creature: its own body
beside you, taking its own line, so a run can end as two different animals.

That is the direct reading of Q2's "I'm playing as two" - not a second head on
one animal, and not a pet that follows. Two creatures, both yours, both growing.

## 2026-09-08 - Q4: what is still most wrong with the map

Asked what is still worst about the map now that region monuments and horizon
labels have shipped against Q2's "the map design sucks".

**Answer: drive it and tell me.** Do not guess and do not take the last three
rounds' word for it - take a real run, film the map from the play camera at
several points, and report what actually reads badly.

**The standing order this sets:** the map's next round is opened by EVIDENCE,
not by a lead. Measure first, then decide what to build.

### Q4, answered by driving it (evidence: bonkhorde/evidence/l8-map)

One bot-driven run, pinned seed 9, filmed from the play camera at 0:30, 3:00,
7:00, 12:00 and 17:00, with the frame's own box census beside each shot. What
actually reads badly, in the order the frames show it:

1. **The sky is a flat colour field.** At night it is one unbroken purple over
   the top 40% of the frame - no gradient, no stars, no moon, nothing. By day it
   is one unbroken grey-blue. It is the single largest area on screen and it is
   the emptiest thing in the game.
2. **The ground is a plane.** The two-tone value noise the terrain builder is so
   careful about is nearly invisible at play distance: what reads is faint
   rectangular patches on a flat sand or flat ice. That IS the "blocky" and
   "plain" complaint - not the box shapes, the *absence* of anything between
   them.
3. **The middle distance is empty.** Monuments drew 0 to 9 of 14 across the five
   frames and were often not in shot at all. Between the animal and the horizon
   there is usually nothing but ground.
4. **The player's own trail is the loudest thing on screen.** Across the run the
   frame's geometry went: hazard zones 40.3%, the player 14.6%, pets 8.3%, the
   twin 7.3%, scenery 6.1% - and THE HORDE 3.8%. The game is about four hundred
   bodies and they are a twenty-fifth of what is drawn. At 17:00 there were 18
   enemies on screen and they are genuinely hard to find under the caltrops.
5. **The pickups are pale chips on a pale floor.** Visible in the 3:00 sand
   frame: the white and lilac gems sit on sand at almost the same value. This is
   Q2's "my floor is just covering the plus lines or dots", still true.
6. **The horizon is a grey sawtooth band.** The backdrop ridge reads as a
   low-contrast city skyline all the way round - the exact thing an earlier
   round's comment worried about and thought it had fixed.

**What this says the next map round is.** Not more landmarks: the map already
has monuments, dens, lakes and regions, and they are only 15-20% of the frame.
The two biggest areas on screen - the sky and the ground - carry no information
at all, and the one thing that should dominate (the horde) carries 3.8%.

## Q5 — which map failing to build first (2026-09-08)

Asked, with the driven evidence in hand, which of the six failings the next map
round should be.

**Answer: make the horde the loudest thing.** The frame's own census says the
player's hazard trail is 40.3% of the geometry and the four hundred bodies the
game is about are 3.8%. At 17:00 there were eighteen enemies on screen and they
were genuinely hard to find under the fire. Cut what the player's own weapons
paint, and make the crowd read as the crowd.

**What this settles for the map rounds after it:** the map's problem is a
BUDGET problem before it is a content problem. The instrument is the per-pass
box census (`__g.boxCensus().passes`), and a map round is judged by where the
frame's geometry went, not by how much of it there is.

### Q5 re-measured, at the end of L14: the sky is 2.6% of the frame

L14 built the sky, and the first thing it had to do was find out how much of a
frame the sky actually is. The answer was not the one Q4's prose implies, and it
is worth writing down because it reorders the six failings.

Derived from the boom maths, the play camera looked like it framed elevation
-51 to +7.5 degrees. Measured off a real driven frame it pitches **27.9 degrees
down** and frames **-57.2 to +1.3** on desktop, **-63.6 to +6.9** on a phone. So
sky - anything above the horizon - is **2.6% of a desktop frame** and **11.8% of
a phone one**.

Q4's "one unbroken purple over the top 40% of the frame" is therefore not the
sky. Measured as the longest run of rows whose luminance holds within 0.012,
across three hours and six columns of a real frame, the flattest thing on screen
is **the ground: 47-56% of the frame**, rows from the middle down, elevation -24
to -57 degrees, constant for four hundred rows. That is failing #2, "the ground
is a plane", and it is an order of magnitude larger than failing #1.

Two more things the same frames show, neither of them the sky:

- **The ground does not take the hour.** At midnight the sky reads 0.115 of
  luminance and the ground reads 0.44 - a daylight-green field under a night
  sky. The hemisphere term uses skyAt()'s `gnd`, which is 0.33-0.36 at every
  hour of the arc while `fog` travels from 0.63 to 0.09.
- **The fully-fogged band is thin.** Fog closes at 84-145 m, which from an eye
  6 m up is elevation -2.4 degrees: only about 6% of the frame is saturated fog.
  Aerial perspective is not what is flattening the picture.

**What this settles for the map round after L14:** the ground, and its light,
before anything else above the horizon. Q5's instrument still stands - a map
round is judged by where the frame's geometry went - but this adds a second one:
the frame's own luminance profile by elevation, which is what found this.
