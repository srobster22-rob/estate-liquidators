# ESTATE LIQUIDATORS
### Co-op horror extraction. Working title.

*Alternates: CLEANOUT · PROBATE · FINAL SALE · THE CURATOR · ESTATE SALE*

> Implementation detail for the Curator AI and the physics handoff lives in
> **`TECH-SPEC.md`**. This document is the design; that one is the build.

---

## 1. Pitch

You and 1–3 friends are a cleanout crew hired to empty a dead collector's estate before
sunrise. Every object in the house has a dollar value. The van has finite space. The quota
is in **dollars, not items**.

The collector is dead. The collection is not unattended.

**The hook:** the thing in the house is not a predator. It is a *curator*. It does not hunt
intruders — it retrieves property. Its attention follows the most valuable thing currently
leaving the house, and therefore follows **whoever is holding it**. You can get rid of the
monster by handing the vase to your friend.

---

## 2. Design pillars

| Pillar | Meaning | Test |
|---|---|---|
| **Greed is the difficulty slider** | The game never forces danger. It prices it. | Can a cowardly crew survive a night at 40% quota? Yes. Do they progress? Barely. |
| **Aggro is an object, not a state** | Danger is transferable and physical — but never free to shed. | Can a player *give* the threat away in under 2s? Yes. Can they *delete* it by dropping? **No** (§6.1). |
| **Information costs safety** | Every scan, light, and radio call is audible. | Is there any way to learn something for free? No. And is scanning ever safely skippable? Also no — see §4.4, which is the assumption this whole design rests on. |
| **The tally is the punchline** | The post-run ledger is the ritual everyone stays for. | Do players read the itemized damages out loud? Must be yes. |

If a feature doesn't serve one of these, cut it.

---

## 3. Core loop

```
LOBBY (van interior)
  ↓  pick tonight's estate, see quota, buy/repair gear
NIGHT  (12 min real time, sunrise = hard end)
  ↓  ENTER → APPRAISE → HAUL → SECURE → repeat, deeper each time
EXTRACT
  ↓  van doors close at sunrise; anything unsecured is reclaimed
LEDGER
  ↓  itemized tally: gross − breakage − curse fees − medical = net
  ↓  quota met? next estate. missed? crew is fired, run over.
```

**Run length:** 12 minutes (720s, of which ~540s is the effective haul window). Long enough for a real arc, short enough that a wipe at
minute 11 makes people immediately start another.

**Session length:** target ~50 minutes for a full contract chain (4 nights, escalating
quota). This is the "one more" unit.

---

## 4. The greed mechanic (the heart)

### 4.1 The Appraiser

A handheld device. Aim at an object, hold for **3.0 seconds** of continuous line-of-sight.

On completion it speaks the result out loud — **diegetically, from the device speaker**, at
a volume that carries roughly 15m and registers on the Disturbance meter.

It reports two things at once:

```
"VICTORIAN MOURNING DOLL.  ELEVEN HUNDRED DOLLARS.  GRADE: MALIGNANT."
```

**Value and curse are revealed by the same action.** The doll is worth $1,100 *because* it's
malignant. Knowing is not free, and knowing is loud, and knowing takes three seconds of
standing still while pointing a beeping device at something.

Unappraised items can still be hauled — you just don't know what you're carrying. Full-blind
hauling is a legitimate strategy for fast crews and it is *hilarious*.

### 4.2 Curse grades

| Grade | Value multiplier | While carried | In van |
|---|---|---|---|
| **CLEAN** | ×1.0 | nothing | nothing |
| **TAINTED** | ×2.5 | your flashlight beats like a pulse — visible to everyone, including the Curator. Continuous Disturbance gain while held. | van interior light dims one notch per tainted item; the dimmer the van, the higher the Disturbance floor |
| **MALIGNANT** | ×6.0 | gains mass fast — you are visibly slower within 20s. Attention weight ×3. **It speaks in a teammate's voice**, using real recorded audio from earlier in the run. | as above, two notches, plus the van radio starts carrying voices that aren't crew |

### The van cost is a tail risk, not a fee

**Cursed cargo carries a chance that the collection reclaims the entire van.** It rises
super-linearly with how many pieces are aboard:

```
P(ruin) = 0.015 x (cursed pieces aboard) ^ 1.8      evaluated at extraction

  1 piece   ~1.5%     a shrug
  3 pieces  ~11%      the sweet spot, and it should feel like one
  5 pieces  ~27%      a quarter of your nights end with nothing
  8 pieces  ~63%      you will not get away with this
```

**Why it had to be restructured this way.** The original design charged a flat ledger fee and
a flat Disturbance floor per cursed item. Simulated (`sim/curse_test.py`), that can never
work — and not at any tuning. Every cost was *linear* while the value bonus is
*multiplicative*, so taking every cursed item was correct at ×6, ×4, ×3, ×2.5 and ×2.0.
Refusing only became right at ×1.5, where the "bonus" is already a penalty. It was a step
function from always-take to never-take with no interesting middle at all.

Ruin probability fixes it because it's the one cost that can grow faster than the benefit.
With it, there is finally an **interior optimum** — the best play is to take *two or three*
cursed pieces and then start refusing, worth about +7% over never touching them, while
taking every cursed item you see is catastrophic (it loses roughly 40% against playing it
safe). That's a real decision with a real greed curve, and it's better fiction than a
handling fee: the collection doesn't fine you, it takes everything back at once.

**Every curse cost must be felt within ~30 seconds of pickup and be obviously caused by the
thing in your hands.** This is a hard rule, added after the first design review killed the
original effects — "your flashlight drains 3× faster" is invisible across a 12-minute run,
and "seeds a hostile object into the next estate" happens so far from the decision that no
player will ever connect the two. A cost nobody can attribute is not a cost; it's noise.

Curse effects are **carry costs and van costs**, never instant death. The item is a burden
you chose. That's the whole feeling.

The van's interior lighting is the readout for total cursed cargo — a physical, glanceable
gauge rather than a UI number, so the crew can *see* what their greed has done to the ride
home.

### 4.3 Object taxonomy

Every object has: **Value**, **Weight class**, **Fragility**, **Curse grade**, **Silhouette**.

| Weight class | Carry | Notes |
|---|---|---|
| **Pocket** | one hand, run freely | coins, jewelry, letters. Low value, high density. |
| **Armful** | two hands, no ladder, no door-open | vases, clocks, taxidermy. The bread and butter. |
| **Two-man** | requires 2 players in sync | armoires, safes, pianos, **corpses** |
| **Cart-only** | must be loaded on the dolly | the big money |

**Fragility** (0–3) determines break threshold on impact velocity. A broken item is worth
$0 and makes a *lot* of noise. Fragile items are disproportionately valuable — the physics
does the comedy.

### 4.4 Why anyone scans at all — the load-bearing assumption

**The single most likely way this design fails is that good players stop using the
appraiser.** It costs 3 stationary seconds and a noise spike per item. A crew that grabs and
runs will out-haul a crew that scans, unless scanning answers a question they genuinely
have. So the whole game rests on making that question unavoidable:

**Requirement A — van space must be the binding constraint.** You must be forced to leave
behind more than half of what you could physically carry out. If the van fits everything,
selection doesn't matter, and if selection doesn't matter, nobody scans. Van capacity is
therefore not a comfort setting — it is the mechanism that makes the signature verb exist.
Upgrade shelving expands it only slightly, and never past the point where choosing stops
hurting.

**Requirement B — value must be legible in category, illegible in magnitude.** Players
should instantly recognize *a vase*, and have no idea whether it's the $80 vase or the $900
vase. If appearance correlates with price, players learn value by silhouette within about
five hours of play and never scan again. This fights readability and makes the world feel
slightly arbitrary — that's a real, accepted cost, not an oversight.

**The gate:** at Milestone 2, instrument it. Track *what percentage of extracted items were
appraised first*, per playtester, per hour of experience. If that number is still falling at
hour five and lands under **~30%**, the appraiser is dead as a core mechanic and needs to be
replaced rather than tuned. Decide this with data before building the Curator on top of it.

> **This number is the designer's, not a simulation's — and R23 established that nothing here
> can derive it.** R20 briefly lowered it to ~15%, because `sim/scan_risk.py` put the
> earnings-optimal rate at 0.2–0.3 and a gate set at the optimum cannot tell "players ignore the
> appraiser" from "players use it well". R23 then found that optimum is an **artifact of
> clock-gated depth**: a crew that fills its tier quota early has to *wait*, and scanning burns
> time, so scanning was being credited for converting dead time into value. Ablate the gate and
> the peak vanishes — scanning becomes monotonically valuable, best at 1.0, worth +25.4%
> (`scan_risk.py` panel G). The change is reversed and the threshold is back to ~30%.
>
> The deeper problem is that the dead time should not exist: **D-20 (FIRM) forbids timer-based
> depth gates**, and every sim here still uses one. Two further caveats for the playtest: the
> sims model scan-or-not *per trip* while the gate counts *per extracted item*, and no model
> prices the prerequisite work that ought to fill that window. Re-derive from telemetry.

**Simulated ahead of the gate** (`ECONOMY.md` §9.1). Scanning beats blind hauling by only +4.4% at 14
van slots, and the edge decays to nothing between 24 and 32 slots — Requirement A is
confirmed as the load-bearing one. But the sim also overturned part of §4.1's framing:

> **The three seconds are decoration. The noise is the cost.**

Scan duration between 1s and 9s per item makes almost no difference to the outcome, because
van space binds long before the clock does. So the appraiser must never be balanced by making
it *slower* — only by sharpening what the noise does to you. Tune toward the band where
scanning *selectively* beats both scanning everything and scanning nothing; that's the only
setting with a skill ceiling in it.

---

## 5. Death, and why your friend is inventory

When a player dies, their body remains. **It is an appraisable object.**

```
"CREW MEMBER: DAVE.  EIGHT HUNDRED DOLLARS.  GRADE: TAINTED."
```

- **Weight class:** Two-man. Someone has to help.
- **Value:** the number the Appraiser reads out is **never paid to you.** It's what Dave is
  worth *to the collection* — which is precisely why the Curator wants him. Carrying a
  corpse adds its value to your attention weight exactly like any other item. Your friend's
  body makes you a target.
- **Recover him:** haul Dave to the van and he's back next night, free.
- **Leave him:** costs you nothing tonight, and you run tomorrow's higher quota one hauler
  short. That's the entire trade — no cash, no fees, no invented currency.
- **The dilemma:** Dave and the armoire are both two-man. There is one dolly and eight
  minutes left. Discuss.

*(The earlier draft had the corpse both paying out on extraction and paying out if
abandoned, which was incoherent. The version above is the fix: the only currency is van
space now versus crew capacity tomorrow.)*

This single mechanic generates more table talk than any monster we could design. It's also
free content — the corpse system reuses the entire item pipeline.

Dead players talk to the living over the van radio, which is *audible in the world* on the
crew's radios — so the dead can help, and the dead can get you killed.

## 5.1 Death is a role change, not a spectator seat

**The problem this solves.** Die at minute three of a twelve-minute night and the genre
standard is that you watch for nine. Lethal Company ships this way; so does everything
else here. It's survivable, and "the genre tolerates it" has never been a design.

**The fiction does the work.** The Curator collects you. You're part of the collection now —
in the house, of the house, and no longer able to leave it. That's not a consolation prize
bolted onto death; it's the thing this monster has wanted the whole time.

### What you get

After a 10-second **collection** beat — deliberately slow, so death keeps its weight — the
dead player gains:

**Free movement through the estate.** No collision, no light needed, fast. You are the
crew's overwatch, and you already have a radio (§2.3 of `AUDIO-SPEC.md`). This alone is
worth more than spectating, because you can see the whole board.

**Permanent sight of the Curator.** You always know where it is and what state it's in. This
is what makes radio chatter matter — *"it's in the east hall, it's fixated, it's coming for
whoever has the clock."* The dead player has the single most valuable information in the
game and the only way to deliver it is out loud, over a channel that makes noise.

**Curse-sight.** You can see the curse grade of any item within 5m — clean, tainted,
malignant — without an appraiser and without a sound. **Not the dollar value.** That split
is deliberate: the dead help you *not die*, they don't help you *get rich*. Value remains the
appraiser's exclusive job, so §4.4's core economic loop is untouched.

### Static — the intervention budget

You accumulate **Static**, capped at 6, regenerating 1 per 20 seconds. Spend it to touch the
world:

| Verb | Cost | Effect |
|---|---|---|
| **Flicker** a light | 1 | signal, or briefly reveal a room |
| **Knock** | 1 | a noise at your location, L=25 — *pulls the Curator toward you and away from them* |
| **Slam** a door | 2 | block a route, break a line of sight, make everyone scream |
| **Nudge** an object | 3 | push something small. Yes, you can knock a vase off a shelf. Yes, it breaks. |
| **Hold** a door shut | 5 | ~4 seconds. The heroic one. |

**Every point of Static spent adds +1 Disturbance.** This is the whole balance in one line.
The dead can genuinely save the living — a well-timed Knock pulls the Curator off a friend
carrying a piano — but *the dead are the haunting*. Help too much and the house gets angrier
for everyone. It's self-limiting, it's thematically exact, and it needs no other rule.

### Why this doesn't make dying desirable

The win condition is dollars, and **a ghost cannot carry anything.** Hauling capacity is the
binding constraint on quota, so a dead crew member contributes exactly $0 toward the only
thing that matters. Their body is now a two-man object someone has to argue about. Death
always costs the crew more than the ghost gives back — that margin is what keeps this honest,
and it's the first thing to check in playtest.

### Why this doesn't enable griefing

Every hostile use of Static is self-punishing. Knock the vase off the shelf and you've cost
the crew money and raised Disturbance and burned your own budget. Slam a door in a friend's
face and the Curator now knows where you both are. There's no need for a rule against
griefing when the resource economy makes it stupid.

> **The design goal, stated plainly:** the dead player should be the loudest person in the
> voice chat, not the quietest. Spectating makes people go silent and check their phone.
> This gives them a job, information nobody else has, and six points of agency — and the
> job is *talking*.

---

## 6. The Curator

One entity. Not a slasher. A caretaker with a grievance.

### 6.1 Attention

The Curator maintains an **Attention target**, recalculated every 2s:

```
attention_weight(player) =
      value_of_carried_items
    × curse_multiplier          (malignant ×3, tainted ×1.5)
    × (1 + 0.20 × noise_events_last_10s)
    × 1.30 if flashlight on and in line of sight
```

Highest weight is the target. **It walks toward that player.** Not sprinting — walking, and
it does not stop, and it does not need to breathe.

**Attention persists to the object, not the person.** This is the most important rule in the
combat design. When the Curator locks onto a carried item, it commits to *that item's last
known position*. Drop the vase and the Curator keeps coming — to the vase. It picks it up,
carries it back to its plinth, and re-seats it.

Without this rule the entire threat system has a two-second, zero-cost off switch: set the
item down gently, walk away, come back in forty seconds. A crew of decent players finds that
exploit in one evening. With it, dropping saves your life and costs you the loot, the hand-
off stays meaningful, and the monster's behavior finally matches what it actually wants.

**Consequences, all emergent:**
- Handing the vase to a teammate transfers the threat. Legally.
- Dropping the vase saves you and forfeits the item — the Curator collects it, not you.
- The richest player is the most hunted player, which means the best hauler needs an escort,
  which means the group naturally forms roles without a class system.
- A player can *volunteer* to take the malignant item and lead the Curator away. This is the
  heroic moment the game exists to produce.

### 6.2 Movement — it arrives where you're going

The Curator walks. It never sprints. On its own that makes it harmless: you can outwalk a
walker forever, and the moment players reach a ballroom, a landing, or the lawn, they know
it and the tension dies. Every slow pursuer that actually works has one distance-closing
cheat.

Ours: **it does not path to the player, it paths to the plinth the item came from.** It's
going to put the vase back. Since you're carrying the vase away from that plinth and toward
the van, it routes to intercept your return trip rather than trailing your back. It is
frequently already in the doorway you were about to use.

One cheat, no more. It never teleports, never opens a door you locked, never moves off-
camera in a way that contradicts what you last saw. The behavior reads as intelligent while
remaining fully explicable after the fact, which is the only way players accept losing to it.

Corridors, stairs, and doorways are therefore the real combat arenas. Level modules must be
authored so that **every route from a high-value wing back to the van passes through at
least two pinch points.** Open rooms are rest; the pinch points are the game.

### 6.3 Retrieval

If the Curator reaches its target it does not kill immediately. **It takes the item back.**
First contact = item is reclaimed and returned to its plinth, player is knocked down and
stunned 4s. Second contact within the same night = death.

This is critical: the first encounter is a *loss*, not a *wipe*. Players learn the monster
without the run ending, and losing $1,100 of appraised loot to a thing that just walks up
and takes it is more upsetting than dying.

### 6.4 The van is not safe

The Curator will enter the van. Items in the van that are **not strapped down** can be
reclaimed. So there's a second job nobody wants: cargo securing. Strapping takes 2s per
item and someone has to stay back and do it.

Watching the monster climb into your van and calmly remove the piano is the trailer shot.

### 6.5 Disturbance

A hidden 0–100 meter rising from: appraiser pings, breakage, lights switched on, running,
radio use, doors slammed.

**Gain values are not authored here.** Every noise event carries one Loudness value `L`
(`AUDIO-SPEC.md` §1.2) and Disturbance gain is derived from it — `L × 0.09` for impulses,
`L × 0.02` per second for continuous sources. One number per event, read by three systems.
Lights are the exception, being silent: switching on a wing is a flat +25.

| Range | Behavior |
|---|---|
| 0–30 | Curator is stationary in the deep house. Ambient dread only. |
| 30–60 | Patrols. Retrieval only. |
| 60–85 | Actively pursues Attention target across the whole map. Doors start locking. |
| 85–100 | **Inventory.** It stops caring about items and starts collecting *crew*. |

**Players must be able to push it back down.** A meter that only rises is a timer wearing a
meter's costume, and players feel the difference immediately — it reads as the game ignoring
them. Three levers, all of which cost something they want:

| Lever | Effect | Cost |
|---|---|---|
| **Kill the lights** at the breaker | −15 instantly | you hauled that wing lit for a reason; now you're doing it blind |
| **Go quiet** — no running, no scanning, no radio, crew-wide for 45s | −20 over the period | 45 seconds of a 12-minute night, spent standing still |
| **Unload cursed cargo** into the yard | removes that item's Disturbance floor contribution | it's out of the van, so it isn't strapped, so it can be reclaimed |

### Disturbance is a noise *level*, not an accumulator

Simulated (`sim/disturbance.py`), the original model — slow accumulation, 1/min decay —
**does not work at any decay rate.** Gross gain from ordinary play is ~54/min against a
100-point scale, so the meter saturates in the first minute and stays pinned for the rest of
the night. Sweeping decay from 1 to 22/min barely moves it: PURSUE still arrives before
minute two. There is no escalation curve, only a wall.

The structure has to be:

```
Disturbance = fast-decaying NOISE LEVEL  +  slowly ratcheting FLOOR
              decay 50/min                    0 -> 55 across the night,
              (drains in ~2 min of quiet)     plus 7 per cursed item in the van

impulse gain  L x 0.09     unchanged from AUDIO-SPEC 1.1
sustained     L x 0.02/s   designated continuous sources only (never walking)
```

**Only the decay changed — 1/min to 50/min.** The gain coefficients are exactly as the audio
spec derived them; the original error was treating a meter fed ~54 points per minute as
though it could be drained one point at a time.

**The noise level is what the crew controls moment to moment.** Go quiet and it genuinely
drains inside a minute and a half, which is what makes the levers below worth pulling. **The
floor is what guarantees the night escalates anyway** — the house gets angrier as you strip
it, regardless of how careful you are.

With that structure, behaviour finally matters:

Tuned at decay 50/min against a four-person crew and locked there — the shipping rule scales it
as `50 × crew/4` (`tuning.json` `disturbance.decay_per_min_at_crew4`, LOOP_LOG R12, which also
notes a scale factor alone does not fix solo pacing). Rows below are play archetypes, not crew
sizes. Percentages are share of a 12-minute night spent in each
tier, over 400 simulated nights per archetype:

| Crew | DORMANT | PATROL | PURSUE | COLLECT | First PURSUE |
|---|---:|---:|---:|---:|---:|
| Silent running | 53% | 46% | 0% | **0%** | 11.7 min (27% of nights) |
| Careful, no scans | 52% | 48% | 1% | **0%** | 11.4 min (52%) |
| **Baseline** | 24% | 36% | 25% | **15%** | **5.8 min** (100%) |
| Greedy — 5 cursed, loud | 11% | 16% | 16% | **57%** | 2.7 min (100%) |

> ### ⚠️ This table does not reproduce under the current constants — R21
>
> Re-run against canonical `tuning.json` (decay 50, cursed floor **7**), the same
> archetypes give **0% COLLECT for every crew, greedy included** — and with the levers
> disabled, 35% baseline / 66% greedy. The table matches neither. Three causes, and they
> need untangling before any of these numbers is quoted again:
>
> 1. **It predates R9.** The table was measured with the cursed floor at 3.0; R9 raised it
>    to 7.0 and nobody re-ran the tuning.
> 2. **The file that produced it stopped being runnable as recorded.** `sim/disturbance.py`
>    shipped `DECAY_PER_MIN = 1.0` — the value R3 proved unsurvivable and R4 replaced — as
>    the default its printed run used, from R4 until R21. Anyone who ran it saw the *broken*
>    curve, not this one.
> 3. **The levers are a ceiling, not a lever.** They fire at 78 (kill lights) and 82 (go
>    quiet), just under COLLECT's 85, and the sim's crew pulls them the instant it can. That
>    makes COLLECT arithmetically unreachable rather than merely avoidable. The model prices
>    the levers' *benefit* and not their *cost* — it has no earnings, so going dark and going
>    quiet are free — so it cannot say whether that ceiling is real or an artifact of a
>    perfect-play policy. `integrated.py`, which does model earnings, has no levers at all.
>    **Neither model can currently answer whether the greed dial has teeth.**
>
> What survives unchanged: a careful crew is never hunted (0% COLLECT, first PURSUE in 1–4%
> of nights), and a greedy crew reaches PURSUE inside 90 seconds versus 3.5 for baseline. The
> *ordering* holds. The COLLECT shares do not.
>
> **R22 answered the question this banner opened.** `sim/greed_dial.py` is the first model with
> both the levers and the money, so going dark and going quiet cost throughput. With the levers
> priced, **COLLECT is reachable again — 80% of the night at maximum greed** — and earnings peak
> at an *interior* greed level. **The dial has teeth.** But the decomposition matters more than
> the verdict: holding two axes fixed and moving one,
>
> | axis | earnings span | peak |
> |---|---:|---|
> | **cursed cargo aboard** | **85%** | interior, at two pieces |
> | scan rate | 7% | at maximum — no teeth |
> | wings lit | 8% | at zero — no teeth |
>
> **The curse's tail risk is carrying the entire greed pillar on its own.** Scanning and lighting
> are close to free at every setting the model can reach. If §4's claim that "the game prices
> danger" is to hold across all three, lights and scanning need a cost with the shape R11 gave
> the curse — or the pillar rests on one mechanic.

That's the curve the design has been claiming all along, now actually produced: a careful
crew can play an entire night without ever being hunted, a baseline crew gets its first
serious pursuit around the halfway mark and spends the last stretch genuinely in danger, and
a greedy crew is being collected before minute three.

Under the old model **every** crew was pinned at maximum inside sixty seconds — including one
that never scanned a single item. There was no curve at all, and no amount of decay tuning
could produce one.

---

## 7. The estate

**Structure:** a hand-authored floorplan skeleton (foyer, halls, stair) with **procedurally
selected wings**. Each wing is an authored 3–5 room module, chosen from a pool per night.
This is the Lethal Company approach and it's correct: authored spaces read better than fully
procedural ones, and the pool gives replayability.

**Depth = value.** Foyer items are $40–150. The sealed east wing is $900+.

**Gating is the pacing system, not set dressing.** Value rises with depth while danger rises
with time, so the naive optimum is to sprint to the deepest wing at T=0 while Disturbance is
zero and work outward — players solving the escalation curve by running it backwards, and
never touching the shallow rooms at all. The fix is that **deep wings cannot be opened until
shallow work is done**: the east wing key is in the study, the cellar breaker feeds the
annex lights, the boarded stair needs the crowbar that's in the garage. You physically
cannot be deep at minute one.

Sequencing this correctly is a level-design responsibility on every single estate module,
and it is the thing most likely to be got wrong quietly. When authoring a new wing, state
its prerequisite chain explicitly and verify the deepest room is unreachable before roughly
minute four.

**Light:** the house has no power at start. A player can restore a wing at the breaker box —
which lights it (huge visibility gain, safe hauling) and adds **+25 Disturbance instantly**.
Turning on the lights is always a group argument.

**Sunrise:** at T-minus 90s the sky begins to grey and the van starts its engine. At T-0 the
doors close. Anyone outside is left. Anything unstrapped is reclaimed.

---

## 8. Player toolkit

| Item | Function | Cost of use |
|---|---|---|
| **Flashlight** | primary light, always available | battery; +Attention when visible |
| **Appraiser** | value + curse grade | 3s stationary, loud |
| **Radio** | talk to crew across map + to the dead | broadcasts audibly in-world at both ends |
| **Dolly** | moves cart-class items | slow, loud on hardwood, tips over |
| **Straps** | secures van cargo | 2s per item, someone has to stay behind |
| **Crowbar** | opens boarded doors, breaks display cases | extremely loud |
| **Salt line** *(unlock)* | Curator won't cross for 20s | single use, consumed |

Deliberately no weapons. There is no fighting the Curator, ever. Every tool is a
**logistics** tool, and the horror is a logistics problem.

## 8.1 Concealment — you can hide, but your loot can't

The genre's defining verb, and it has to inherit this game's logic rather than being bolted
on. The Curator's attention follows **loot**, not people (§6.1), so plain "get in a locker"
would simply not work — the vase in your arms is still broadcasting.

That constraint turns out to be the mechanic.

**Hiding places** are furniture, not markers: wardrobes, under beds, inside crates, behind
dust sheets, the space under a stair. Every estate module authors several. Entering one takes
~1s and is silent; leaving is instant and loud.

**While concealed, you are not a valid attention target — but anything you're carrying still
is.** So the choice, every single time:

| | What happens |
|---|---|
| **Hide holding the prize** | The item keeps radiating. The Curator walks to the wardrobe and opens it. You have bought about four seconds. |
| **Stash the item, then hide** | You're invisible. The Curator goes to the *item*, reseats it, and you've lost it — but you're alive and you know exactly where it went. |
| **Hand it off, then hide** | Someone else is now the target. This is the hot potato, played at knifepoint. |

**Stashing** is the third verb this adds: place an item *inside* concealment furniture and it
stops radiating for **20 seconds**. Long enough to break a chase, short enough that it's a
delay and not a solution. A crew learns to seed the route home with stashed loot and run it in
relays — which is a genuinely good strategy that nobody designed, and exactly the kind of play
this structure should produce.

**At COLLECT (Disturbance ≥ 85) hiding becomes the primary verb.** The Curator has stopped
caring about items and is collecting crew (§6.5), so concealment now works properly — and the
game turns, for the last minutes of a bad night, into the hiding game the genre trades on.
That escalation is earned rather than constant, which is what keeps it frightening.

**The fairness rules extend.** It never opens a hiding place it did not have a reason to
approach; there is always audio warning before it does; and being found while concealed is a
retrieval, not an instant death, on first contact (§6.3).

---

## 9. Progression

Keep it thin. Meta-progression in this genre exists to give a session a shape, not to be an
RPG.

- **Contract chain:** 4 nights, quota escalating $7,500 → $9,000 → $10,750 → $12,500
  (calibrated in `ECONOMY.md` §4, which closes O-06; the earlier $2,000 → $15,000 curve
  simulated as three formalities followed by a 1%-pass wall). Miss
  one, the chain ends, you start a new chain. This is the run structure.
- **Between nights:** spend net profit on gear (better battery, second dolly, van shelving
  for +cargo slots, salt) and repairs. Money does not carry across chains.
- **Persistent unlocks:** cosmetics and *estates* only. New estate types (the hospital
  annex, the storage facility, the ship) unlock permanently as content, never as power.

---

## 10. Multiplayer & voice — the actual project

Be honest about where the work is: **netcode and proximity voice are 60% of this build.**
The monster and the mansion are the easy parts.

### 10.1 Recommended stack — Unity

Every game in this genre is Unity (Phasmophobia, Lethal Company, Content Warning, R.E.P.O.).
That isn't coincidence — it's where the co-op horror asset ecosystem lives, and it's the
fastest path from prototype to a Steam build friends can actually join.

| Layer | Choice | Why |
|---|---|---|
| Engine | **Unity 6, URP** | genre precedent, iteration speed, the look is achievable |
| Netcode | **FishNet** (free) — **Mirror** is the pre-agreed fallback if the voice bridge fails the two-day test at Milestone 0 | FishNet's prediction/ownership model suits physics handoff better; NGO is ruled out (`STACK.md`, D-16) — its physics story is the weakest of the three and physics is the whole game |
| Transport | **Steam P2P relay** (Steamworks.NET / Facepunch) | zero server cost, friends join from the Steam overlay, no port forwarding |
| Voice | **Dissonance Voice Chat** (paid asset) | positional voice done right; do not build this yourself |
| Audio | **FMOD Studio** + occlusion volumes | the entire horror budget is audio; Unity's built-in audio won't do the §5.2 dynamic mix without a lot of custom work (`AUDIO-SPEC.md` §7.1, verified in `STACK.md`) |

> ✅ **Verified 2026-07-29 — see `STACK.md`.** FishNet is actively developed (4.7.2R, April
> 2026) with explicit Unity 6 support and recent Unity 6-specific fixes. Dissonance is
> actively maintained (April 2026). FMOD's free indie tier covers this project comfortably.
>
> ⚠️ **One caveat, planned for rather than ignored:** Dissonance ships no *official* FishNet
> integration — the bridge is a community project and the prominent copy is a backup fork.
> Mitigation is to **vendor it** into this repo at Milestone 0 instead of depending on
> upstream, with Mirror as the pre-agreed fallback if it isn't working end-to-end in two
> days. Full reasoning in `STACK.md`.

**Authority model:** host-authoritative. Only the host simulates rigidbodies; clients get
transform sync with client-side interpolation. When a client picks up an item, ownership
transfers to that client for responsive carry, then reverts on drop. This is the single
riskiest system in the game — prototype it *first*, in isolation, before any content.

**Two-man carry is the hardest technical problem in this project.** Harder than the Curator,
harder than the procedural estate, harder than anything else on the list. Two clients cannot
both own one rigidbody; ownership models are single-owner by design, and a piano held by two
players across a residential connection will fight itself, jitter, duplicate, or launch into
orbit.

Plan for the cheap fake from day one rather than discovering the need for it in month four:
**one player is the authoritative anchor** (they own the rigidbody and their movement drives
it), **the second is a constraint** applying force and a carry pose. The follower can desync
by a modest margin without the object breaking, and swaps to anchor if the first player
disconnects. It doesn't have to be physically honest. It has to survive 120ms of latency and
look like two people carrying a piano.

This is exactly why two-man carry sits in Milestone 1 and not later.

**Physics budget:** cap at ~60 simultaneously-awake rigidbodies. Items sleep aggressively
when untouched and far from players. Nothing about this game requires more.

### 10.2 If you'd rather use Godot 4

Entirely viable and I'd support it — cleaner to work in, open source, C# available. Costs:
proximity voice is largely DIY (no Dissonance equivalent), Steamworks needs GodotSteam, and
physics-heavy networked interaction has fewer worked examples to crib from. Add ~4–6 weeks
for infrastructure you'd otherwise buy.

**Unreal:** great physics and lighting, wrong tool here. Heavier iteration for a small team,
and the genre's grubby low-fi look is not what UE5 buys you.

---

## 11. Vertical slice — build order

Each milestone must be **playable and testable** before the next starts. Do not build
content ahead of systems.

| # | Milestone | Proves |
|---|---|---|
| **0** | 2 players in a grey box over Steam, spatial proximity voice, **and one door that occludes it** | the entire technical risk of the project — and per `AUDIO-SPEC.md` §8, the door is not optional. Two people, a door, and spatial voice is a 15-minute test that tells you whether this game's foundation feels right. |
| **1** | Pick up / drop / throw a networked rigidbody; two-man carry | physics authority handoff — the hard part |
| **2** | One room, 10 items, appraiser, van, quota, sunrise timer, ledger screen, **+ scan-rate instrumentation** | *the loop is fun without a monster*, and the appraiser survives contact with players ← the real gate |
| **3** | The Curator: attention weighting, retrieval, hot-potato handoff | the core hook actually reads at the table |
| **4** | Disturbance escalation, lights/breaker, curse grades | the greed dial has teeth |
| **5** | Corpse-as-inventory, death, van radio spectating | the argument mechanic |
| **6** | 5 wing modules, contract chain, gear shop | it's a game |

**Milestone 2 is the honest checkpoint**, and it carries two independent kill criteria:

1. If hauling objects to a van with your friends isn't already funny with no monster in the
   building, the monster will not save it. Test with real friends and real voice chat.
2. If the scan rate from §4.4 collapses under **~30%** by hour five, the appraiser is not a core
   mechanic and no amount of tuning will make it one. (R20 lowered this to ~15% on a measured
   optimum; R23 found that optimum was an artifact of clock-gated depth and reversed it. See
   D-23 — no scan-rate threshold in this repo is simulation-backed.)

Either failure means stopping and reworking, not proceeding to Milestone 3. Write both
numbers down before the playtest, not after.

**Scope, stated honestly:** Milestones 0–6 is a 9–18 month build for a small team, and
longer if netcode is new to you. The earlier draft of this plan implied something much
lighter. Milestones 0–2 alone — the part that tells you whether the game is worth making —
is realistically 2–4 months, and that is the correct thing to commit to right now. Do not
schedule content work past Milestone 2 until Milestone 2 has passed both gates.

---

## 12. Known unsolved problems

Recorded rather than hidden. These have no good answer yet.

**Dead-player downtime — answered in §5.1, unproven in play.** The dead become part of the
collection: free movement, permanent sight of the Curator, curse-sight without an appraiser,
and six points of Static to touch the world with. It should turn the deadest ten minutes in
the genre into the loudest seat in the voice chat.

It is still a **bet**, and it carries two failure modes worth watching for specifically:
*(a)* dying becomes preferable to living, which kills the game outright and means cutting the
whole thing back to spectating; *(b)* the ghost's information trivialises the Curator, so
crews with a dead friend are safer than crews without one. Watch for the second in
playtest — the fix would be tightening curse-sight range or adding latency to Curator
sight, not removing the role.

**Genre timing.** This space is crowded, and the breakouts in it had a large streamer-luck
component on top of being good. Not a design flaw, but it should inform how much is spent
before Milestone 2 answers whether the loop actually works.

**The readability tax from §4.4 Requirement B.** Deliberately decoupling appearance from
value keeps the appraiser alive, and makes the world feel a little arbitrary. That's a real
cost being knowingly paid, and it may turn out to be worse in play than it looks on paper.

---

## 13. Open questions

- ~~**Crew size:** 4 max, or up to 6?~~ **Closed → D-18: four.** On voice legibility alone — past four simultaneous speakers proximity chat stops being intelligible. The chain sim (`ECONOMY.md` §8) mildly prefers six (+12%, $12,131 → $13,586), so four is a conversation decision, not an economic one, and that +12% is not a reason to revisit it.
- **Friendly fire on carried items:** can you *take* an item out of a teammate's hands, or
  only receive a voluntary hand-off? Forced-take is funnier and meaner. Probably gate it
  behind a slow 1.5s pry so it's a visible act of aggression.
- **Does the Curator have a face?** Recommend: never fully seen. Silhouette, hands, the
  sound of it setting an item back down.
- **Permadeath on chain failure?** Currently no — crew resets, money resets, nothing else.
- **Do players see each other's appraisals in a shared ledger UI, or must they say the
  number out loud?** Strongly prefer the latter. Force the talking.
