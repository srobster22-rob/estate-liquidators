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

**Measured in the build, R46** (`proto3d/play.mjs --ablate`): a competent policy that never
appraises loses **$620 ± 508 per night** against the same policy on the *same houses*, and its
pass rate falls 76% → 61%. Of the five verbs ablated, the appraiser is the only one whose cost
clears its own noise band — narrowly, at 2.4 standard errors across five comparisons — — which is D-10's claim, measured for the first time in the thing
you can actually play rather than in a model of it.

> The unpaired version of that same table said the opposite. Run across separate seed sets it
> reported that appraising *costs* 5% at eight nights a cell and *pays* 7% at twenty-four; the
> houses differ by more than the verb does, and R11 had already learned this once. Paired on
> identical estates, the answer stops moving.

**Simulated 2026-07-29** (`ECONOMY.md` §6, `sim/haul_sim.py`): scanning beats blind hauling
by **+84%** at 14 van slots, and the edge decays monotonically with capacity until blind
hauling wins outright somewhere between 24 and 32 slots. The mechanism §4.4 predicted is
confirmed — the appraiser lives entirely on van space binding.

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

## D-22 · At COLLECT, concealment is a full stop, not a delay
**Status:** SOFT · `DESIGN.md` §6.5 and §8.1, implemented `proto3d/index.html`

Two rules meet at COLLECT and the interaction had never been written down. §6.5 says the
Curator stops curating objects and starts collecting crew; §8.1 says a concealed player is
not a valid attention target. Composed literally, that means a player who is hidden and
empty-handed at COLLECT is *completely* safe — the Curator has no target at all and returns
to patrol. It does not search, listen at the door, or wait you out.

Implemented literally, on purpose. The alternative — a search behaviour — is the standard
genre answer and it is where hiding games go to die: once the monster can find you in the
box, the box is a countdown and the player is a spectator. Making concealment a hard stop
keeps the cost on the *approach*: getting to the wardrobe is the dangerous part, and your
loot is still lying out there radiating while you sit in it.

The price is that the last minutes of a bad night have a safety switch in them.

**Falsified if:** playtests show crews reaching COLLECT and simply parking in furniture
until sunrise. The fix then is not a search behaviour but an economic one — time spent
concealed earns nothing, so the counter is a quota the crew cannot meet from inside a
wardrobe. If that doesn't bite either, give the Curator a slow sweep of hiding places *it
has already seen a player near*, which keeps the fairness rule intact.

---

## D-23 · Stashing is silent; leaving concealment costs a door
**Status:** SOFT · `DESIGN.md` §8.1, `tuning.json` concealment block

§8.1 fixes the durations (≈1s to enter, 20s of stash quiet, ~4s to be opened) but says
nothing about what any of it costs in Loudness. Three calls, all guesses, all flagged:

- **Entering is silent.** It already costs the scarcest resource in the game — a second of
  standing still while something walks toward you.
- **Leaving costs L60**, the door value from the loudness table. "Leaving is instant and
  loud" is the spec's own wording, and a wardrobe door is the obvious referent.
- **Stashing is silent.** Placing a vase inside furniture is a careful act; the noisy verb
  is *dropping*, which is already L90. If stashing were loud it would collapse into
  dropping, and the two want to stay distinct decisions.

**Falsified if:** stash-relay play (seed the route home, run it in relays) turns out to be
strictly better than carrying, with no counterplay. Then stashing needs a cost — most likely
a small impulse on placement, since the 20s timer is already load-bearing.

---

## D-24 · Appraising is a breadth decision priced by a tail risk
**Status:** FIRM (model) / SOFT (values) · `ECONOMY.md` §11, `sim/appraise_test.py`

The project spent four rounds asking whether the appraiser's +6% edge was enough to carry the
game's signature verb. The question was wrong. Every sim that produced that number compared
**blind** against **scan everything**, and R8's ADAPTIVE interpolated in *time*, not in
*breadth*. Nobody had ever measured the actual decision a player makes at a shelf: **how many
of these four do I scan before I commit?**

Measured, the appraiser is worth **+14%** over blind hauling, and the optimum is **interior at
two** — better than scanning nothing *and* better than scanning everything — with no new
mechanic required. Time and noise alone are enough to make over-scanning wrong.

The tail risk (R11's shape, applied again: `p_caught = RETRIEVAL[tier] × 0.30 × n^1.8`) does
not rescue the mechanic, because the mechanic did not need rescuing. What it buys is that the
right answer **changes with the situation** — scan while it is quiet, stop the moment it is
hunting, scan wider in the wings worth scanning — which is worth a further +6% over playing
the best constant, and is the difference between a decision and a number to memorise.

**The design consequence:** the appraiser should be usable *per candidate*, not per shelf, and
the UI must make "I have scanned two of these four" a legible state. If scanning is presented
as a mode you switch on for a room, the interesting axis is unreachable and the +6% question
comes back exactly as it was.

**Falsified if:** Milestone 2 instrumentation shows scan *breadth* clustering at 0 or 4 —
players treating it as on/off despite the payoff shape. That would mean the cost is not
legible in the moment, and the fix is the frost/tell treatment (make the risk visible while
you stand there), not a change to the numbers.

---

## D-25 · Target objects, not players — then the hot potato needs no special case
**Status:** FIRM · `TECH-SPEC.md` §A3, `proto3d/index.html`, verified `proto3d/qa.mjs`

A3's weight function is written per player, so its third hysteresis rule — "an explicit hand-
off re-targets instantly, ignoring the other two" — exists to stop the game's best moment
being swallowed by an eight-second commitment lock. R2 measured the cost of omitting it:
0.0s with the override, 6.0s without.

Implementing attention over **items** instead makes that rule unnecessary. D-06 already
requires aggro to persist to the object rather than the person; if the Curator's target *is*
the object and the chased body is derived from `item.heldBy` each frame, then handing the vase
over does not change what it wants. The mark moves the same frame, inside an active lock,
with no exemption code anywhere.

This is the better structure for the same reason the multiplicative weight was: it makes the
rule **arithmetically impossible to violate** rather than reliably special-cased. A special
case can be forgotten during a refactor; a derivation cannot.

Keep the other two hysteresis rules. A *different* item becoming more attractive is a real
retarget, and both the 1.25× steal threshold and the 8s commitment still earn their place —
the prototype's checks fail immediately when either is neutered.

**Falsified if:** a case appears where the Curator must target a person independently of what
they carry — the COLLECT-tier crew hunt is exactly that, and it is handled as a separate mode
rather than by folding people into the item weighting. If a second such case appears, the
two-mode structure is the thing to re-examine, not this decision.

## D-26 · A price is a band times its multipliers, and a checker has to divide out every one
**Status:** FIRM · `ECONOMY.md` §3, `sim/validate_estate.py` V8, verified `proto3d/qa.mjs`

An item's price is its tier-and-class band multiplied by the curse grade (§4.2, ×2.5 / ×6)
and by the fragility premium (`DESIGN` §5, +18% per grade, so a fragility-3 piece is 1.54× its
band). Both multipliers are deliberate and both are *invisible in the number*: a $462 tier-0
armful is either three times its band or a delicate piece at the top of it, and nothing in the
price says which.

V8 divided out the curse and not the fragility, and so rejected **12 of 12** generated estates
for being correct. It had done so for as long as the batch mode existed, because nothing
asserted the output of the command the README tells you to run.

The rule this fixes in general: **a band check must be handed the factors, not asked to infer
them.** The estate export now carries the fragility grade alongside the curse grade, and the
apex carries the night's quota it is a share of, because the apex is banded by ratio (D-21) and
this build's night is 210 seconds rather than 720 — judged in ship dollars it fails too.

The corollary is about checks, not prices: a validator whose output nothing asserts is not a
check, it is a script. `qa.mjs` now asserts that the export still carries all three, which is
the part a refactor can silently take away.

**Falsified if:** a third multiplier appears that genuinely cannot be exported — at which point
the band check has to move to where the multipliers are, rather than the factors moving to it.

---

# Open decisions

| # | Question | Blocks | Notes |
|---|---|---|---|
| ~~O-01~~ | ~~Crew size 4 or 6?~~ | — | **Closed → D-18.** Four. |
| ~~O-02~~ | ~~Dead-player downtime~~ | — | **Closed → D-17.** The dead join the collection. |
| ~~O-03~~ | ~~Van capacity numbers~~ | — | **Closed → `ECONOMY.md` §1.** 14 slots, ceiling 20. |
| ~~O-04~~ | ~~Estate module authoring template~~ | — | **Closed → `LEVEL-SPEC.md`.** Module contract + 10-check validation suite. |
| **O-05** | Does the Curator have a face? | art | recommend never fully seen — silhouette and hands only. Not blocking anything yet. |
| ~~O-06~~ | ~~Contract chain and quota curve~~ | — | **Closed → `ECONOMY.md` §4.** 4 nights, 48%→79% of theoretical max. |

Only O-05 remains open, and it blocks nothing. Every decision that gated build work has been
made — which means the next real information comes from a playtest, not another design pass.
