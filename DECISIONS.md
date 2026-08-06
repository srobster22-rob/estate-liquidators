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

**Revised twice since, and the current number is +6%.** The +84% used a placeholder for how
badly noise punishes you; deriving it from the tuned Disturbance model gave +31%
(`ECONOMY.md` §9), and coupling retrieval as well gave **+6%** (`sim/integrated.py`). The
*mechanism* is unchanged and D-10 still stands — capacity is still the master lever, and the
ordering is still right. What changed is the margin, and +6% is thin enough that whether this
verb carries the game is genuinely unsettled. See D-22.

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

## D-22 · The appraiser is gated on the Curator's state, not on van fill
**Status:** FIRM (the negative half) · BET (the positive half) · `sim/appraiser_risk.py`

Two findings, one round.

**The negative half — stop trying to fix the appraiser with cost.** R11 rescued the curse by
making its cost catastrophic instead of marginal, and the obvious next move was to do the
same to scanning: hold the crew stationary for three seconds, and let the Curator arrive.
It does not work, and it cannot. Sweeping that risk moves the best available edge over blind
hauling *monotonically down* — 6.0% → 5.4 → 5.0 → 4.3 → 2.4 → 0.0, at which point not
scanning wins outright. Compounding the risk per consecutive scan makes it worse again
(3.1% → 1.2% as the exponent goes 0 → 2).

The reason the two mechanics behave oppositely is worth stating as a general rule, because
this project has now spent four rounds circling it:

> The curse was **always** correct to take, so adding cost created a decision.
> The appraiser is **barely** correct to use. **You cannot raise a payoff by adding a cost.**
> A thin edge can only be widened from the benefit side.

There is a second, sharper reason the risk lever failed. Retrieval is exactly **0.00** at
DORMANT, so the cost landscape has a flat zero region — and an optimum can't sit *inside* a
flat region, it sits flush against its edge. Every risk level tested picks the same policy:
scan only below Disturbance 30. That is a boundary rule, not a decision. **Any cost curve
with a free zone will produce a rule rather than a choice**, which is a thing to check
before designing the next one.

**The positive half — the heuristic is the Curator's state.** Gating scanning on Disturbance
beats gating it on van fill even with the risk switched off ($6,883 vs $6,852), and buries it
once any risk exists ($6,822 vs $5,174). The van-fill heuristic was only ever a proxy: both
it and quiet correlate with time. So `DESIGN.md` §4.4's advice to players is **"appraise
while you can't hear it"** — and that needs no HUD, because DORMANT is precisely the state
where `AUDIO-SPEC.md` §3.2 gives the house *no sound at all*. The tell already exists and is
already diegetic, which keeps D-14 intact.

**Knowingly accepted cost:** this makes the early night the scanning window and the late
night the hauling window, which is a slightly tidier rhythm than "four friends arguing in a
hallway" wants. It's tolerable because the floor ratchets — the window closes on you whether
or not you deserve it, so the argument becomes *when to spend the quiet*, not whether.

**Falsified if:** Milestone 2 instrumentation shows crews scanning at a roughly constant rate
across the night rather than front-loading it — that would mean players cannot actually read
the DORMANT/PATROL boundary in play, and the heuristic is only available to someone watching
a debug meter. Also falsified if the R17 variance lever widens the edge past ~+15%, since a
payoff that large would make scanning correct everywhere and dissolve the gate entirely.

> **Amended by R17 — the positive half is demoted from rule to overlay.** Once rooms differ
> (D-23), gating on the *room* beats gating on the *house*: scanning the widest-spread half
> of rooms earns $7,133 against the quiet-gate's $6,891. Combining both is *worse* than the
> room rule alone ($6,982), because the two constraints fight — the quiet window is early
> night, and the good rooms arrive whenever they arrive.
>
> It is not dominated, though, and that is the interesting part. The combined rule has a
> **much better floor**: 10th-percentile $6,147 against $5,853, ending the night at
> Disturbance 39 rather than 72. So "scan good rooms, but only while it's quiet" is the
> cautious line and "scan good rooms whenever you find them" is the greedy one, separated by
> ~$150 of expected value and a lot of variance. That is a real argument for four people to
> have in a hallway, which is the bar. The negative half of D-22 is untouched.

---

## D-23 · Rooms declare a value *spread*, and the estate must mix them
**Status:** HELD · `LEVEL-SPEC.md` §2.1, V11 · `sim/appraiser_variance.py`

Every room declares `uniform` (0.3× the band's half-width), `mixed` (1.0×) or `curio` (1.7×),
and V11 rejects any estate that isn't at least a quarter of each with a mean of 1.00 ±0.15.

**Why it's the right lever, when four others weren't.** Scanning's payoff is `0.6 ×` the
room's spread and nothing else, so spread is not *a* lever on the appraiser — it is the only
one on the benefit side. D-22 established that cost levers can only shave the edge down from
+6%; this is the first thing in seventeen rounds to move it **up**, to +10%.

**Why it isn't just handing the appraiser money.** `E[value]` of a room is its band midpoint
regardless of spread, and mean spread is pinned at 1.00, so a V11-compliant estate pays out
exactly what a flat one does to a crew that never scans *and* to a crew that always scans.
Both extremes were measured flat across the whole heterogeneity sweep ($6,485 and ~$6,470,
unmoved). **The entire +4 points goes to crews that tell rooms apart.** That is a skill
ceiling rather than an economy buff, and the distinction is the reason this decision is worth
its authoring cost.

**Knowingly accepted cost: this is real work for level authors**, and it constrains art —
a `curio` room has to *look* miscellaneous and a `uniform` room has to *look* repetitive, or
the information isn't there to act on. Paying it because the alternative is the appraiser
being a formality, and because the requirement is one line per room and machine-checked.

**The reassuring result** is that it degrades gracefully. Modelling players misreading rooms
(σ = noise on their read, in units of the full heterogeneity range): σ=0 gives +10.0%, σ=0.5
gives +8.9%, and even σ=1.0 — a read as noisy as the entire spread of rooms — still gives
+7.8%, beating a crew that doesn't try. It only collapses to the +6% baseline at σ=2.0. So
the mechanic rewards good reads without punishing bad ones, and a new player is never worse
off for guessing.

One emergent nuance worth keeping: **the noisier your read, the pickier you should be.**
With a perfect read, scanning the top half of rooms is best; with any read noise at all, the
top *quarter* wins. "When you're not sure, only stop for the obviously weird rooms" is
correct play and also good advice, which is a pleasant thing to be able to say.

**Falsified if:** Milestone 2 shows players scanning `uniform` and `curio` rooms at
indistinguishable rates — that means the art isn't telegraphing spread and the whole
mechanism is invisible, which is an art fix, not a tuning one. Also falsified if authors
find the three classes so coarse that estates feel samey, in which case make spread a
continuous per-room float and keep V11's distributional check unchanged.

---

# Open decisions

| # | Question | Blocks | Notes |
|---|---|---|---|
| ~~O-01~~ | ~~Crew size 4 or 6?~~ | — | **Closed → D-18.** Four. |
| ~~O-02~~ | ~~Dead-player downtime~~ | — | **Closed → D-17.** The dead join the collection. |
| ~~O-03~~ | ~~Van capacity numbers~~ | — | **Closed → `ECONOMY.md` §1.** 14 slots, ceiling 20. |
| ~~O-04~~ | ~~Estate module authoring template~~ | — | **Closed → `LEVEL-SPEC.md`.** Module contract + 11-check validation suite. |
| **O-05** | Does the Curator have a face? | art | recommend never fully seen — silhouette and hands only. Not blocking anything yet. |
| ~~O-06~~ | ~~Contract chain and quota curve~~ | — | **Closed → `ECONOMY.md` §4.** 4 nights, 48%→79% of theoretical max. |

Only O-05 remains open, and it blocks nothing. Every decision that gated build work has been
made — which means the next real information comes from a playtest, not another design pass.
