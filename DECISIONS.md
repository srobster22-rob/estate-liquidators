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

**Simulated, five times, each time in a wider model** (`ECONOMY.md` §9–10.2). The edge decays
monotonically with van capacity until blind hauling wins outright somewhere between 24 and 32
slots, every single time — the mechanism §4.4 predicted is confirmed, and the appraiser lives
entirely on van space binding.

The *size* of the edge has been retracted four times, and the direction is worth noticing:

| | Edge | What was wrong with the previous figure |
|---|---:|---|
| R5 `haul_sim` | +84% | noise cost was a placeholder |
| R6 | +31% | losing cargo acted as a free reroll |
| R8 | +6% | — (selection-only policy space) |
| R17 | +4.4% | Disturbance floor was stale at +2 |
| R18 | +25% | the crew had never been allowed to *refuse* an item |
| **R22** | **+10%** | curses were absent, and the curses are the valuable items |

Every retraction came from finding an instrumentation or modelling error, never from a design
change. **Treat any future single figure here as provisional.** What has not moved in six
measurements is the ordering and the mechanism, and those are what the decision rests on.

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

## D-25 · Curses are judged on the margin, not counted
**Status:** FIRM (simulated, unplayed) · `DESIGN.md` §4.2, `ECONOMY.md` §10.2

There is no correct number of cursed pieces. The question is always *what does this one add* —
its value net of fee, against the ruin it raises on everything already in the van — and the
answer moves with how rich the van already is. The readout must therefore show the ruin delta
(`proto3d` does: *"van risk 5% → 11%"*), because half the arithmetic is invisible otherwise.

R11's "take two or three, then refuse" came from a model whose only lever was a count; it was
the best available answer to a question posed in counts. Given the appraiser's actual readout,
a crew that judges each piece on the margin beats every capped policy **without a cap at all**,
and capping it at three costs 7%.

This also closes something that looked like two decisions and is one. A curse is worth ×6, so
the curses *are* the valuable items: any policy reaching for value reaches for curses. A crew
refusing everything below the 70th percentile of the value band ends the night carrying 7.4
cursed pieces and losing the van 57% of the time, having never decided to take a single risk.
That is why value and grade come out of the same three seconds — separating them would let a
crew think it was making one decision while making another.

**Falsified if:** playtests show crews ignoring the ruin readout and reverting to a rule of
thumb ("never more than three"). That would mean the arithmetic is too slow for a hallway
argument, and the honest response is to make the van's interior lighting the gauge instead —
a glanceable risk state rather than a number.

---

## D-26 · Quotas are calibrated against the crew that gambles with nothing
**Status:** HELD · `ECONOMY.md` §4, `tuning.json` → `progression`

The quota curve is fitted so a **careful** crew — one that refuses every cursed item — passes
night 1 about 87% of the time and night 4 about 10%. It is not fitted to the crew that takes
what pays.

It cannot be. Cursed cargo carries a per-night chance the collection reclaims the whole van,
so a greedy crew's pass rate has a hard ceiling around **74%** — at *any* quota, including
zero. Fitting the curve to that crew would mean a night-1 quota so low the game has no floor,
and it would still fail a quarter of the time for reasons no player could act on.

Calibrating against the careful crew produces the arc the design always claimed: caution is
the *correct* play on night 1 (87% against 73%), and by night 3 it is losing two nights in
three. Switching posture once, mid-chain, beats both pure strategies. Greed is the difficulty
slider, and now the slider has a measured position on it for every night.

**Falsified if:** playtest pass rates come in far above these — most likely because real crews
are better at routing than the model's every-trip-is-average assumption, in which case the
whole curve shifts up together and keeps its shape. Refit; don't redesign. Also falsified if
crews report night 1 as a formality: the target is *survivable*, not free.

---

## D-27 · Upgrades are posture-specific, and wards buy the exponent, never the count
**Status:** HELD · `ECONOMY.md` §4.1

The shop sells along two axes that do different jobs. **Time** — the van parked closer, a
second dolly, anything that shortens a trip — is worth +7.5% to a crew that refuses cursed
cargo and +0.7% to one that doesn't. **Slots** — shelving — is the exact reverse: +22% to the
greedy crew and +5% to the careful one. They are complements, so buying one is a statement
about what kind of crew you intend to be, and the shop becomes a character sheet rather than a
list of small numbers.

The second half is a rule about anything that softens the curse. A ward that **exempts
pieces** from the ruin roll makes a crew *safer* — two free pieces halve the vans lost, from
27% to 14%. A ward that **gentles the exponent** (1.8 → 1.5) is worth the same money and makes
the crew *braver*: it carries more cursed cargo, 5.3 pieces against 5.0, and still loses 18% of
its vans. Same price, opposite feeling, and only one of them is the game this project is
trying to make. Exemption also flattens the cost curve that R10 and R11 spent two rounds
proving has to be super-linear or the decision collapses into a step function.

**Falsified if:** the two axes turn out not to be complements in play — most likely because
real crews route better than the model's every-trip-is-average assumption, which would make
time cheaper than measured and shelving relatively more valuable to everyone. Re-measure trip
variance from Milestone 2 telemetry before pricing the shop.

---

## D-28 · The apex object is never cursed
**Status:** FIRM · `ECONOMY.md` §3, `LEVEL-SPEC.md` §2

The estate's centrepiece always has curse grade CLEAN. Its danger is logistics — five van
slots, a dolly, two people, every pinch point in the house — never a value multiplier.

No document had ever said either way, and the silence was worth a third of a night. Rolling
the apex's grade like any other item is worth +13% on top of taking it, and makes that one
object **70% of a night's income**: a malignant apex is $24,000–48,000 against a night-4 quota
of $10,250, so it clears the quota four times over and nothing else the crew does that night
counts. Twenty-seven rounds of work went into making ordinary cargo a decision; one lottery
ticket at spawn flattens all of it.

Making the grade *visible* at spawn does not rescue it. At four times the quota it is an
auto-take — a bigger number, not a choice.

The apex is worth **+19%** clean, which is a healthy reward for reserving five slots and is
the first time D-21's economics have been confirmed against the curse economy rather than
against the pre-curse `chain_sim`.

**Falsified if:** playtests find the apex ignored anyway — that would mean the five-slot
reservation is too expensive in practice, and the fix is the slot cost or the unlock timing,
never the grade.

---

## D-29 · Curses ride only on what one person can carry
**Status:** FIRM · `ECONOMY.md` §3, `DESIGN.md` §4.3

Pocket and armful items may be cursed. Two-man, cart and apex pieces never are — their danger
is logistics, never a value multiplier. This is D-28 generalised: R28 closed the hole for the
apex, and R30 found the same hole one tier down the moment weight classes entered the model.

A malignant tier-3 two-man piece is **$24,000 against a night-4 quota of $10,250**. Left open,
the economy stops having an interior optimum at all: refusing almost everything and waiting
for a jackpot pays better at every bar tested, and slots used falls to 7.6 of 14 — **the van
stops binding**, which is the one constraint the entire economy is built on. Restricting
curses to single-carry items restores the peak at the 30th–50th percentile and makes
over-selectivity cost 36%.

The fiction agrees, which is how it should have been caught earlier. Every curse effect in
`DESIGN.md` §4.2 is intimate: it pulses *your* flashlight, gains mass in *your* hands, speaks
in *your teammate's* voice. None of that is an image of two people carrying a wardrobe.

**Falsified if:** playtests show crews ignoring two-man pieces entirely once they cannot be
cursed. That would mean the per-slot pricing in §3 is too thin to justify a two-person job,
and the fix is the band, not the grade.

---

## D-30 · A class shut out of the curse lottery carries a printed premium
**Status:** HELD · `ECONOMY.md` §3

A curse-eligible item is worth **×1.73** its printed band in expectation — 0.70×1 + 0.22×2.5
+ 0.08×6, straight off the grade table. D-28 and D-29 shut two-man pieces, the cart and the
apex out of that lottery, which silently repriced all three. Their bands now carry the
difference: **×2.1 for two-man** (the lottery, plus the labour of two people and a slower
carry) and **×1.73 for the apex** (one person, a dolly).

Without it they are dominated, and not marginally: on the corrected model a crew that
**refused every two-man piece earned +26%**, and the apex — once its competitors kept the
lottery — cost 27% to take. Every heavy item in the house was a trap, created by two decisions
that had nothing to say about value.

**The rule generalises past these classes:** any time an item is excluded from a multiplier
everything else can roll, its printed value has to absorb the expectation, or the exclusion is
a stealth nerf. Per-slot parity has to be measured *in expectation*, after the lottery and the
labour — the pre-curse "two-man is deliberately slightly worse per slot" line was comparing
printed numbers against expected ones without noticing.

**Falsified if:** a future change to the grade distribution or the multipliers moves ×1.73.
The premium is a function of the grade table, not a constant — recompute it whenever
`curse.value_multiplier` or the grade probabilities change.

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
