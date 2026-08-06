# Decision Log

Every non-obvious choice, why it was made, and **what would prove it wrong**.

The falsification column is the point. A decision without a stated way to disprove it is a
belief, and beliefs are what turn into eighteen months of building the wrong game. When a
playtest trips one of these conditions, reopen the decision — don't defend it.

Status: `FIRM` (rebuild costs weeks) · `HELD` (reasoned, reversible) · `BET` (deliberate
gamble, expect to revisit) · `OPEN` (not yet decided)

---

## D-01 · Unity over Godot and Unreal
**Status:** HELD · `DESIGN.md` §10

Every shipped game in this genre is Unity. That's not taste, it's ecosystem: the netcode and
proximity-voice problems this project will hit have known solutions, worked examples, and
off-the-shelf assets there. Godot costs an estimated 4–6 extra weeks hand-rolling positional
voice and Steamworks. Unreal is heavier iteration for a look it doesn't help with.

**Verified 2026-07-29** (`STACK.md`): FishNet, Dissonance, and FMOD are all actively
maintained with current Unity 6 support and workable licensing. The falsification condition
below was *checked* rather than left hanging — which is the entire point of writing these
down.

**Falsified if:** the team's existing fluency is strongly Godot. Fluency beats ecosystem for
a small team, and that's the only remaining argument against this.

---

## D-02 · The monster retrieves; it does not hunt
**Status:** FIRM · `DESIGN.md` §6

The Curator is a caretaker restoring the collection, not a predator eating intruders. This
is the game's whole identity — it makes aggro follow *loot* rather than people, which is
what produces the hot potato, the sacrifice play, and the argument in the hallway.

**Falsified if:** playtesters consistently describe it as "the monster" rather than by what
it does. If the caretaker framing doesn't land in the fiction, the mechanics lose their
justification and it becomes an ordinary chase game with extra steps.

---

## D-03 · Attention persists to the object, not the person
**Status:** FIRM · `DESIGN.md` §6.1

Drop the vase and it still comes — for the vase. Without this, dropping is a free two-second
aggro reset and the entire threat system has an off switch that decent players find in one
evening.

**Falsified if:** playtesters stop picking up valuables at all because commitment feels
total. The fix would be a partial release (aggro decays over ~15s after a drop), not
reverting.

---

## D-04 · Exactly one AI cheat: it paths to the plinth
**Status:** FIRM · `TECH-SPEC.md` §A4

A walking monster in open space is harmless, so it needs one distance-closer. It routes to
where the item *belongs* rather than to the player, so it intercepts the return trip. It
never teleports, never opens locked doors, never contradicts what a player last saw.

**Falsified if:** players describe deaths as unfair or inexplicable. The test is whether a
death is fully explicable in hindsight — "terrifying" is the goal, "bullshit" is the failure.

---

## D-05 · Carried items stay non-kinematic
**Status:** BET · `TECH-SPEC.md` §B0

The safe implementation — kinematic, parented to a hand socket — never jitters and deletes
the game. The clock catching the doorframe *is* the product. Joint-attached, fully
simulated, jitter accepted.

**This is the most expensive bet in the project.** Deliberately taking on the hardest netcode
problem in exchange for the comedy.

**Falsified if:** after a genuine tuning effort (budget one full week on joint values), the
jitter is still bad enough that players fight the *game* instead of the *doorframe*. Fallback
is a hybrid: simulated while moving, kinematic snap when stationary.

---

## D-06 · Owner-authoritative carry; clients fully trusted
**Status:** HELD · `TECH-SPEC.md` §B1

No server validation of positions, break events, or values. Threat model is genuinely none —
this is played with friends over Steam. The tradeoff buys responsiveness, which is the only
thing that matters. Cheating gets handled socially, which is cheaper and more effective than
anything we could write.

**Falsified if:** the game ever ships public matchmaking with strangers. Then this inverts
completely, and it's a rewrite, not a patch. Decide before adding any lobby browser.

---

## D-07 · Two-man carry is anchor + follower, and physically dishonest
**Status:** HELD · `TECH-SPEC.md` §B4

Two clients cannot both own a rigidbody. One player owns it; the second applies force and
may drift 0.4m from correct. Two people carrying a couch in real life also disagree about
where the couch is.

**Falsified if:** the drift is visible enough to break the illusion at 120ms latency. Test
this at real latency, not on LAN — LAN will lie to you and say it's fine.

---

## D-08 · Aggro is shown diegetically — frost and a dimming flashlight
**Status:** FIRM · `TECH-SPEC.md` §A7

No HUD, no outline, no marker. The whole social layer requires that *everyone* can see who's
marked, which is why the dimming flashlight does the heavy lifting: visible at range, through
door gaps, and it doubles as a mechanical penalty.

Collapses to one sentence: **"if your light is dimming, it's coming for you."**

**Falsified if:** playtesters can't reliably identify the marked player within ~3 seconds.
Fix by strengthening the signal, not by adding UI.

---

## D-09 · Full friendly-fire physics, zero friendly-fire damage
**Status:** FIRM · `TECH-SPEC.md` §B6

Flatten your friend with an armoire; it does nothing. The only cost lands on the shared
ledger. Chaos without consequence is comedy; chaos with consequence is griefing. "You owe the
crew four hundred dollars" is a better punishment than a health bar and a funnier one.

**Falsified if:** nothing plausible. This is settled genre wisdom.

---

## D-10 · Value is legible in category, illegible in magnitude
**Status:** BET · `DESIGN.md` §4.4

You can tell it's a vase; you cannot tell it's the $900 vase. If appearance predicts price,
players learn value by silhouette in about five hours and never scan again — and the
appraiser is the game's signature verb.

**Knowingly accepted cost:** the world feels slightly arbitrary.

**Simulated 2026-07-29** (`ECONOMY.md` §6, `sim/haul_sim.py`): the edge decays monotonically
with capacity until blind hauling wins outright somewhere between 24 and 32 slots. The
mechanism §4.4 predicted is confirmed — the appraiser lives entirely on van space binding.

> **The size of the edge has been revised four times and the early figures are dead.** +84%
> (placeholder noise cost) → +31% (noise derived, R5) → +6% (slot-accounting reroll fixed,
> R8) → **+4.4%** (cursed floor corrected to canonical 7.0, R16) → **+12.2%** with room value
> classes in place (D-22). Quote the last one; the +84% in older prose is superseded
> everywhere it appears.

Two things the sim changed:
- **Scan *duration* is not the cost.** 1s and 9s per item produce the same outcome; there's
  too much slack time at 14 slots. Noise has to carry the whole cost — do not try to make
  appraising expensive by making it slower.
- **The tuning target is a noise-to-consequence level where *selective* scanning wins.**
  That band is the only place a skill ceiling exists.

This is not proof. The model omits the Curator, the hot potato, curses, deaths, and human
imperfection, and it was rigged generously toward the appraiser. It survived anyway.

**Falsified if:** the Milestone 2 instrumentation shows scan rate under ~30% at hour five
anyway (the mechanic is dead regardless), *or* if playtesters report the world feeling
random rather than mysterious. These are different failures with different fixes.

---

## D-11 · The corpse carries no currency
**Status:** HELD · `DESIGN.md` §5

The appraised value of a dead crewmate is never paid out — it's what they're worth to the
collection, which is why carrying a body makes you a target. Recovering them costs van space;
abandoning them costs a hauler on tomorrow's higher quota. That's the entire trade.

**Falsified if:** crews abandon bodies every single time without discussion. The argument is
the feature; if there's no argument, the costs are mispriced.

---

## D-12 · One Loudness value per event, read by three systems
**Status:** FIRM · `AUDIO-SPEC.md` §1

Curator hearing, Disturbance gain, and player audibility all derive from a single authored
number. The previous design had three tables with independent magic numbers, guaranteed to
drift apart within a month of content work.

**Falsified if:** a system needs to break the ratio — e.g. something loud that shouldn't
raise Disturbance. Handle with an explicit per-event multiplier, never by re-introducing a
second table.

---

## D-13 · Mic amplitude is a game mechanic
**Status:** BET · `AUDIO-SPEC.md` §2.2

How loudly you actually speak feeds the loudness model. Panicking is mechanically punished,
and it teaches itself with no UI and no tutorial.

**Requires** lobby calibration, a hard cap, a floor, and a keybind alternative — without all
four it's a hardware lottery instead of a mechanic.

**Falsified if:** calibration can't make a cheap headset and a good microphone behave
identically, or if players self-mute rather than whisper. Self-muting would mean the
mechanic is suppressing the voice chat the whole game is built on — fatal, revert immediately.

---

## D-14 · Diegetic-only, except where the player can't perceive the signal
**Status:** FIRM · `AUDIO-SPEC.md` §2.2

Aggro is diegetic (D-08) because the signal is external and visible. Voice volume gets a
small indicator because you *cannot hear your own outgoing level*, and punishing players for
a system they can't sense is just bad design.

> Diegetic-only is correct when the player can perceive the signal. When the signal is
> something the player emits but cannot sense, show them.

**Falsified if:** nothing. This is the rule that keeps D-08 from becoming dogma.

---

## D-15 · The Curator is never scored
**Status:** HELD · `AUDIO-SPEC.md` §3.3

No stinger, no swell, no music cue on any state. The moment players learn the soundtrack
warns them, they stop listening to the house — and the house is the game. Music exists in
three places: the van, the last 90 seconds of the timer, and the ledger.

**Falsified if:** playtesters miss the Curator's approach so often it reads as unfair. The
fix is the §3.1 approach bus, not music.

---

## D-16 · Vendor the Dissonance↔FishNet bridge
**Status:** HELD · `STACK.md`

Dissonance has official integrations for Mirror, Netcode for GameObjects, and Photon Fusion
— but not FishNet. The FishNet bridge is community-maintained and the prominent copy is a
backup fork, which is the fingerprint of a project whose author has moved on.

Fork it into this repository at Milestone 0 rather than depending on upstream. It's a thin
transport shim moving opaque byte arrays; an unmaintained dependency you control is source
code, an unmaintained dependency you fetch is a liability.

**Pre-agreed contingency, recorded now so it isn't relitigated under pressure:** if the
bridge isn't working end-to-end within **two days** at Milestone 0, switch to Mirror. Losing
FishNet's prediction model is a real cost and it is smaller than losing two weeks to a
transport shim. Not NGO — its physics story is the weakest of the three and physics is the
whole game.

**Falsified if:** the bridge turns out to need real ongoing work rather than occasional
patching. That would mean it isn't the thin shim this decision assumes, and the Mirror
contingency should fire immediately rather than at the two-day mark.

---

## D-17 · Death is a role change, not a spectator seat
**Status:** BET · `DESIGN.md` §5.1

The only genuinely unsolved problem in the design (O-02) gets an actual answer rather than
genre-standard resignation: a dead player becomes **the Curator's inventory**, gaining a
small set of world-manipulation verbs on a shared budget, plus information the living can't
see. See `DESIGN.md` §5.1 for the full mechanic.

**Falsified if:** dead players use their verbs to grief rather than help (the budget is
shared with the crew's own resources specifically to make griefing self-punishing), or if
the added complexity means players *want* to die. If dying is ever preferable to living, cut
the whole thing and go back to spectating.

---

## D-18 · Crew size is four
**Status:** HELD · `ECONOMY.md` §2

**Corrected 2026-07-29.** This decision originally claimed an economic justification. The
chain simulation (`ECONOMY.md` §8) does not support it: with correctly labour-gated depth,
earnings rise monotonically with crew size — $12,131 at four, $13,586 at six. The economy
mildly *prefers* more people, with diminishing returns.

So the honest justification is the one that survives: **voice legibility.** Past four
simultaneous speakers, proximity chat stops being intelligible, and this game is a voice chat
product with a horror game attached (`AUDIO-SPEC.md` §2.1). Four is a design choice about
conversation, not about money, and it should be defended on those terms.

**Falsified if:** playtest shows four players can't cover an estate's prerequisite chains in
the time available — that would mean the level, not the crew, is mis-sized. The +12% that six
players earn is not a reason to revisit this.

---

## D-19 · Van capacity is the master balance constant
**Status:** FIRM · `ECONOMY.md` §1

14 slots, ceiling 20, and the ceiling is a design guarantee rather than a tuning knob.
Capacity may never grow to where choosing stops hurting. Every other economy number —
value bands, quota curve, trip times — is reverse-engineered from the requirement that a crew
can haul more than the van holds.

**Sharpened by simulation** (`ECONOMY.md` §6): the appraiser's edge collapses to zero
somewhere between **24 and 32 slots**. The 20-slot ceiling was picked by instinct and turns
out to sit just under the cliff. It is now a measured boundary, not a guess — when someone
proposes a capacity buff, that table is the answer.

**Falsified if:** crews clear night 1 without appraising anything. Cut capacity before
touching any other number.

---

## D-20 · Depth unlocks on labour, never on wall-clock
**Status:** FIRM · `ECONOMY.md` §8, `LEVEL-SPEC.md` §3

Prerequisite chains gate depth through *work* — find the key, flip the breaker, pry the
boards. Never through a timer.

`LEVEL-SPEC.md` already specified task-based prerequisites, but as a pacing device rather
than a constraint. The chain sim shows it is load-bearing: **clock-based gating makes bigger
crews earn less**, because they fill the van at capacity speed while depth opens at wall-clock
speed, ending the night with a van of foyer junk. A crew of two outearned a crew of six by
2× before this was corrected.

The failure would have been near-impossible to diagnose from playtest reports — "six-player
lobbies feel bad" is not a bug report anyone can act on.

**Falsified if:** nothing. Any future timer-based gate is a bug.

---

## D-21 · The apex object must be visible before it is reachable
**Status:** FIRM · `ECONOMY.md` §8, `LEVEL-SPEC.md` §2

`LEVEL-SPEC.md` requires the estate's centrepiece to be seen in the first ninety seconds and
opened only at minute six or seven. That was written as drama — walk past something you can't
have, argue about it all night.

The sim shows it's also the only thing that makes the apex *economically reachable*. Crews
reserve five van slots for it only if they know it's there; when they don't, the van is full
by the time it unlocks and the apex is taken 0–7% of the time. With foreknowledge it's taken
100% of the time and is worth +21% on night 1.

Drama requirement and economic requirement turn out to be the same requirement.

**Falsified if:** crews reserve slots for it and then routinely fail to reach it anyway —
that would mean the unlock timing, not the visibility, is wrong.

---

## D-22 · The appraiser's payoff is a property of the room, not a constant

**Decision:** every room declares a `value_class` — `shelf` (±10% spread), `mixed` (±40%),
`curio` (±110%) — dressed so the class is readable from the doorway. Wings ship 15–35% curio
rooms, enforced by validator check **V11**. Scanning's payoff is `0.6 × spread × room mean`,
so this makes it vary by a factor of eleven across the house instead of being one number.

**Why.** For eight rounds the appraiser's edge sat at a thin, arguably-skippable few percent,
and every attempt to widen it worked on the *cost* side — harsher retrieval, fewer candidates,
tier-scaled exposure, and finally (R16) a super-linear tail risk. All of them failed, and R6
concluded from that that no middle strategy could ever have a wide optimum. That was the wrong
diagnosis. Every one of those models drew all four candidates from a single flat band, which
hard-codes the benefit as a global constant — and a constant rate of return is not a decision
no matter what you charge for it. The fix was on the benefit side, and it is content, not
tuning.

**Measured** (`sim/scan_risk.py`, 2500 nights per policy): scanning only curio rooms earns
**+12.2%** over blind hauling, against +2.4% for scanning everything. The controls are what
make it a mechanic rather than a discount — scanning a *random* 25% of rooms earns +4.6% at
identical scan count and noise, so **roughly 60% of the edge is the read, not the frugality**;
and scanning only shelf rooms earns **−1.9%**, so reading the room wrong is worse than never
scanning at all. A decision with no wrong answer is a formality.

**Cost, stated plainly.** This pulls against D-10, which insists value is illegible in
magnitude. The reconciliation is that **the room's variance is public and the item's value is
private** — you can see the cabinet is a lottery, you cannot see which drawer won. That is a
real tension, not a resolved one, and it is now a standing dressing constraint on every wing
the project ever authors. It also makes level authoring harder in a way no level designer will
thank us for: a wing can now be *economically* wrong while being spatially perfect.

**Falsified if:** Milestone 2 instrumentation shows scan rate is roughly the same in curio and
shelf rooms — that means the telegraph isn't reading and the decision is a coin flip, which is
worse than not having it. Also falsified if testers report the room dressing tells them what to
take *without* scanning, which would mean D-10 has been broken to buy this; in that conflict
D-10 wins, because it is what keeps the appraiser alive at all.

---

## D-23 · Scanning is not a tail risk, and shape is not the whole lesson

**Decision:** do not attach ruin-style risk to appraising. The super-linear cost that fixed
cursed cargo (D-19's sibling, `DESIGN.md` §4.2) does not transfer to the appraiser, and this is
logged as a decision precisely because it is the obvious next idea.

**Why.** Modelled in `sim/scan_risk.py`: `p(interrupted) = k × consecutive_scans^1.8 ×
tier_weight`, with death and a permanently smaller crew — which slows Disturbance decay,
because decay is crew-scaled (R12) — if the Curator arrives while hunting. Every scanning
policy loses to hauling blind at every k from 0.02 up, monotonically in how much you scan.
There is no burst length that wins. Scan-everything falls to −29%.

**The refinement worth keeping.** This project has twice concluded "a multiplicative benefit
needs a super-linear cost." That is necessary and not sufficient:

> Cost **shape** decides whether an interior optimum *can* exist. The **size of the benefit**
> decides whether it *does*. Cursed cargo pays ×6, so the first two pieces are clearly worth a
> ruin roll and the fifth clearly isn't — that gap is the decision. Scanning pays ×1.35, and
> there is no number of draws at which ×1.35 survives a tail risk. The curve has no interior
> peak; it declines from the first scan.

So the appraiser needed its *benefit widened* (D-22), not its cost sharpened — the opposite
prescription to the curse, derived from the same principle.

**Falsified if:** the candidate count per shelf rises far enough that scanning's multiplier
approaches the curse's — at ×3 or better, a tail risk becomes worth re-testing. It is ×1.35 at
4 candidates and this is not close.

---

## D-24 · A stash is safe by position, and the search window is deliberately ragged

**Status:** HELD · `DESIGN.md` §8.1, `TECH-SPEC.md` §A9

**Decision:** stashing an item suppresses its attention radiation for 20s, but whether that
saves it depends on **where** you stashed it — within ~40m of the item's home plinth it is on
the Curator's route (§A4) and gets found. And the Curator's search-before-giving-up is
`Random.Range(8f, 24f)`, **re-rolled every time**, never a constant.

**Why the randomness is load-bearing.** With any fixed give-up time, the 20s stash timer
either always outlasts the search or never does — and at every plausible fixed value it always
does. Modelled (`sim/hiding.py`), that makes stashing save the item **100% of the time you can
reach a wardrobe**: a free, certain reset of the entire threat system, available on demand.

That is D-03's exploit wearing a different hat. D-03 exists so that dropping an item isn't a
free two-second aggro reset; stashing is dropping plus hiding the object, and it walked
straight back through the door D-03 was built to close. **The fix is not a shorter timer** —
short timers kill the verb outright (at 8s it saves 0% and stashing is never correct). The fix
is making the *search* ragged, so the two durations overlap instead of one always dominating.
At 8–24s the save rate is 75%.

**Consequence for the build:** a future refactor will want to make that search deterministic
for testability. Seed it; do not fix it. `check_drift.py` asserts the invariant directly — the
search window must straddle the stash timer at both ends — so the exploit cannot be reopened
by an innocent-looking tuning change.

**Falsified if:** playtesters stash reflexively rather than as a decision, which would mean 75%
still reads as "usually works". The fix would be widening the span, not shortening the timer.

---

## D-25 · Concealment is an attention exclusion, and COLLECT inverts which verb is right

**Status:** HELD · `DESIGN.md` §8.1, `TECH-SPEC.md` §A9

**Decision:** a concealed player is skipped by the attention loop; their carried items are
not. Three lines of §A9, and every consequence in §8.1 follows from them.

**Measured** (`sim/hiding.py`, across distance-to-van, item value, Disturbance tier, and
whether a teammate is in reach): **all four responses have a region where they are the best
play** — run under ~15m, hand off whenever someone is within 2.5m, stash in the long middle,
hide at COLLECT. That matters because this project's characteristic failure is a menu that
collapses to one dominant answer; it happened to the appraiser (three attempts), the curse
multiplier (two), and the scan tail risk (dead on arrival). Concealment is the first
multi-option system here that survived the test on the first try, and only because each verb
is answering a different question.

**The part worth keeping.** Hiding-while-holding is the worst verb everywhere except COLLECT,
where it becomes the best — and that inversion is not a difficulty ramp or a special case. At
Disturbance ≥ 85 the Curator drops item logic and targets the nearest player (§A3), so the
thing in your arms stops being what it's following. **The genre's signature panic falls out of
a targeting rule that was already written**, rather than being bolted on for the last act.

**Cost, stated plainly.** The whole system is gated on furniture. At the modelled 55%
availability, 45% of encounters offer no concealment at all and collapse back to "run for it".
That makes hiding-place placement a balance parameter dressed as set dressing, and it is now a
level-authoring constraint with a validator check (V12) rather than an art decision.

**Falsified if:** playtesters describe concealment as "the thing you do when you're about to
die" rather than as a choice between four options — that would mean the regions are real in the
model and invisible in play, and the fix is signposting (can you tell how far the van is? can
you tell where your teammates are?) rather than retuning.

---

# Open decisions

| # | Question | Blocks | Notes |
|---|---|---|---|
| ~~O-01~~ | ~~Crew size 4 or 6?~~ | — | **Closed → D-18.** Four. |
| ~~O-02~~ | ~~Dead-player downtime~~ | — | **Closed → D-17.** The dead join the collection. |
| ~~O-03~~ | ~~Van capacity numbers~~ | — | **Closed → `ECONOMY.md` §1.** 14 slots, ceiling 20. |
| ~~O-04~~ | ~~Estate module authoring template~~ | — | **Closed → `LEVEL-SPEC.md`.** Module contract + 12-check validation suite. |
| **O-05** | Does the Curator have a face? | art | recommend never fully seen — silhouette and hands only. Not blocking anything yet. |
| ~~O-06~~ | ~~Contract chain and quota curve~~ | — | **Closed → `ECONOMY.md` §4.** 4 nights, 48%→79% of theoretical max. |

Only O-05 remains open, and it blocks nothing (25 decisions logged as of R17). Every decision that gated build work has been
made — which means the next real information comes from a playtest, not another design pass.
