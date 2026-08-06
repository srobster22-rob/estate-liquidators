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

## D-22 · A constant is either asserted or waived, never merely unwatched
**Status:** FIRM · `sim/check_drift.py`, `sim/mutate_drift.py`, `check.py`

The drift checker must account for every (source file × canonical constant) pair. Either a
regex asserts it, or a waiver states in words why that file doesn't embody it. A pair that is
neither fails the run as a **coverage hole**, so adding anything to `tuning.json` forces a
decision about all ten files rather than defaulting to silence.

R14 built the checker, reported "55 constants agree", and injected two fake divergences to
prove it worked. Both true, and both beside the point. The constant that was actually wrong —
the cursed-item Disturbance floor, raised from an inert +2 to +7 in R9 — had no pattern
watching it, so it stayed at +2 in **both** browser prototypes for two rounds while the
checker printed OK. The checker wasn't broken; its coverage was invisible. Silence read
exactly like agreement.

Two rules follow. **Coverage is a defect surface, not a nice-to-have** — an unwatched
constant is indistinguishable from a correct one, so the accounting has to be total and the
gaps have to be named out loud. And **every assertion must be shown to be able to fail**:
`mutate_drift.py` corrupts each literal in turn and requires the checker to exit non-zero and
name that constant. A hand-picked sample of two does not scale to 177.

The cost is real: waivers are prose, prose rots, and a lazy future round can wave a genuine
divergence through by writing a waiver instead of a fix. That trade is deliberate — a wrong
waiver is at least *visible in a diff*, which is more than an absent pattern ever was.

**Falsified if:** waivers start outnumbering assertions in a file that genuinely implements
the rules, or a round is caught writing a waiver to silence a real divergence. Either means
the mechanism has become paperwork and should be replaced by generating the constants into
each implementation instead of checking them after the fact.

---

## D-23 · Relief is rationed — the levers get a 120-second cooldown
**Status:** FIRM (simulated, unplayed) · `DESIGN.md` §6.5, `tuning.json`

Kill the lights and go quiet each drop Disturbance by a fixed amount. Neither may be used
more than once every **120 seconds**.

Without a cooldown, a crew that pulls a lever whenever the meter crosses 78 pulls five a
night and spends **0% of the night in COLLECT** — the Curator's top tier stops existing. The
valve removes exactly the pressure it was installed to relieve, and it does so under the most
obvious possible player policy, so this is not an exotic failure. Measured across cooldowns
for a baseline crew: none → 0% COLLECT, 60s → 6%, **120s → 14%**, 300s → 26%, never → 30%.
120s is the setting that reproduces the 15% the design was aiming at.

The fiction is open — a breaker somebody has to walk to, a recharge, a per-night budget of
three. The rationing is not. Any relief that can be applied on sight flattens the escalation
curve to its first three tiers.

**Falsified if:** playtests show crews hoarding the lever instead of using it — if the
cooldown makes it too precious to pull, it is doing the opposite job and wants to become a
budget (spend when you like, run out) rather than a timer.

---

## D-24 · The appraiser is a rejection tool, and "leave it" is a first-class verb
**Status:** FIRM (simulated, unplayed) · `DESIGN.md` §4.4, `ECONOMY.md` §10

Appraising exists so a crew can *refuse* an item, not so it can rank four of them. The
interface must make walking away from an appraised object as deliberate and visible as
picking it up.

Every model of this mechanic from R5 to R17 asked "do you scan?" and let the crew choose only
between things it was already going to take. In that policy space the appraiser is worth
**+4.4%**, which is thin enough that R9 through R17 all listed "is this enough to carry a
signature mechanic?" as an open question, and the candidate fixes were value-variance per
room, harsher retrieval, or tighter van capacity — three new systems.

None were needed. Adding one verb the mechanic already implies — decline the item, keep the
slot, spend the trip — takes the edge to **+20–25%**, and creates the interior optimum this
project has been hunting for thirteen rounds: the decision is **where you set the bar**, and
its answer moves with danger (70th percentile in a quiet house, 50th when scanning is risky,
and the 85th is a −16% disaster because the clock replaces the van as the binding
constraint). The trade is legible at the table — *too picky loses the night, too greedy
fills the van with junk* — which is worth more than any tuning value in the file.

The lesson generalises past this mechanic: **when a mechanic looks marginal, check whether
the model has given the player every verb the mechanic implies before tuning anything.** Four
rounds of retuning were spent on a policy space that was missing a move.

**Falsified if:** playtests show refusal rates near zero. That would mean players read the
appraiser as a comparison tool — a UI failure rather than a balance one, fixed by making
"leave it" an explicit action, not by touching the numbers.

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
