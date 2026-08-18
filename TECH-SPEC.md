# ESTATE LIQUIDATORS — Technical Spec
## The Curator AI & the Physics Handoff

Companion to `DESIGN.md`. This is the implementation-level spec for the two systems that
carry the whole game: the thing that chases you, and the objects you drop while it does.

Everything here serves one goal — **four friends shouting at each other in a hallway.**
Where a technically superior choice would make the game less funny, this spec picks funny.
That is a deliberate engineering constraint, and it's called out where it applies.

---

# PART A — THE CURATOR

## A1. The one number relationship that defines the game

Before any AI logic, the speed table. This is the entire combat design; everything else is
decoration on top of it.

| Actor | Speed (m/s) | Notes |
|---|---|---|
| Player, empty, walking | 3.2 | |
| Player, empty, sprinting | 5.6 | stamina 6.0s, full recovery 9.0s |
| Player, **armful** carry, walking | 2.6 | |
| Player, **armful** carry, sprinting | 4.1 | stamina drains 1.6× faster |
| Player, **two-man** carry | 1.8 | no sprint |
| Player, dolly | 2.2 | no sprint, tips on turns above 1.6 m/s |
| **Curator — Patrol** | 2.4 | |
| **Curator — Pursue** | 2.9 | never sprints, never stops, never tires |
| **Curator — Inventory (T4)** | 3.4 | |

Read the table and the game falls out of it:

- **Empty-handed, you are always safe.** 5.6 > 2.9 with room to spare. Freedom is free.
- **Carrying an armful, you are on a timer.** 4.1 beats 2.9 — but only for 6 seconds of
  stamina, and then you're at 2.6 and it is at 2.9 and it is *gaining*.
- **Two-man carrying, you cannot escape. At all.** 1.8 vs 2.9. The piano is not a thing you
  flee with; it's a thing you and a friend commit to, knowing exactly what it costs.

So the decision "do I keep the vase?" is never abstract. It's a foot race the player can
feel in their thumbs, and the answer changes every four seconds. Tune these numbers before
anything else; if this table is wrong, no amount of AI polish will save the encounter.

## A2. State machine

```
                 ┌──────────┐
                 │ DORMANT  │  Disturbance < 30, deep house, stationary
                 └────┬─────┘
                      │ Disturbance ≥ 30
                 ┌────▼─────┐
            ┌────┤  PATROL  ├────┐  wanders plinth-to-plinth, verifying the collection
            │    └────┬─────┘    │
            │         │ attention target acquired
            │    ┌────▼─────┐
            │    │  FIXATE  │  2.0s pause. Turns. Looks. THIS IS THE TELL.
            │    └────┬─────┘
            │    ┌────▼─────┐
            │    │  PURSUE  │  walks the intercept route (A4)
            │    └────┬─────┘
            │         │ contact
            │    ┌────▼─────┐
            │    │ RETRIEVE │  takes the item; knocks the player down
            │    └────┬─────┘
            │    ┌────▼─────┐
            │    │  RESEAT  │  carries item back to its plinth. Ignores everyone en route.
            │    └────┬─────┘
            └─────────┘
                      
                 ┌──────────┐
                 │ COLLECT  │  Disturbance ≥ 85 — stops caring about items, comes for crew
                 └──────────┘
                 ┌──────────┐
                 │  WARDED  │  salt line — 20s, cannot cross, will path around if a route exists
                 └──────────┘
```

**FIXATE is the most important state in the machine.** Two full seconds where it stops,
turns, and looks at its target before it starts walking. It costs the AI nothing and it
gives the player the single most valuable thing in horror design: *the moment you realize.*
Never skip it, never shorten it below 1.5s, never let it trigger off-screen without audio.

**RESEAT is where the group regroups.** While the Curator walks the vase back to its plinth
it is functionally harmless and completely ignores everyone. That's a deliberate ~20-second
breather after every failed retrieval, and it's when players regroup, swear, and re-plan. A
horror game without troughs is just noise.

## A3. Attention

Recalculated every **2.0s** on the host only.

```csharp
float AttentionWeight(Player p) {
    float loot = 0f;

    foreach (var item in p.CarriedItems)
        loot += item.AppraisedValue * CurseMultiplier(item.Grade);  // clean 1.0, tainted 1.5, malignant 3.0

    // A corpse is an item. Carrying your friend makes you a target. This is intended.
    foreach (var body in p.CarriedCorpses)
        loot += body.CollectionValue;

    // Noise and light MODIFY how visible your loot is. They are multipliers, never
    // addends — see the note below, this is load-bearing.
    float mult = 1f + 0.20f * p.NoiseEventsLast10s;
    if (p.FlashlightOn && HasLineOfSight(p)) mult *= 1.30f;

    return loot * mult;
}
```

> ### Why multiplicative — this was a real bug
>
> The original formula added noise (+200/event) and light (+400) to the loot value.
> Simulated (`sim/curator_attention.py`), that **breaks design pillar 2 outright**: an
> empty-handed player who is noisy and has their flashlight on is hunted **100% of the
> time**, in preference to three teammates actually carrying loot. Aggro stops being an
> object you can hand over and becomes a state you're stuck in.
>
> The additive constants were simply the same order of magnitude as real item values
> ($150–1400), so they swamped them. Multiplying instead makes the pillar arithmetically
> impossible to violate — carry nothing and your weight is zero, no matter how much noise
> you make. Empty-handed targeting drops to **0%**, and flicker nearly halves as a bonus
> (5.0 → 2.7 retargets/min).
>
> Being loud still matters enormously — it just makes *the loot you're carrying* more
> attractive rather than making you attractive by itself.

**Unappraised items** count at the *category median* for their type, not their true value —
so the Curator's interest is a soft hint about what you're holding, without being an oracle.
Players who never scan still get information, just noisier and later. Nice secondary payoff:
"why is it coming for Jenna? …Jenna, what did you pick up?"

### Hysteresis, or: why the target doesn't flicker

Raw highest-weight targeting produces a monster that pirouettes between four players every
two seconds and reads as broken. Three rules fix it:

| Rule | Value | Why |
|---|---|---|
| **Steal threshold** | new target must exceed current by **1.25×** | small fluctuations don't re-target |
| **Minimum commitment** | **8.0s** locked on a target | it looks *decisive*, which reads as intelligent |
| **Hand-off override** | an explicit item hand-off re-targets **instantly**, ignoring both rules above | the hot potato must always work, every time, no exceptions |

That last row is a gameplay rule wearing an AI rule's clothes. Passing the vase is the
game's best moment; it is never allowed to feel unreliable or delayed. Hand-off is a
first-class event, not a side effect of the weight calculation.

> **R20 note — the override is free if you target objects, not players.** The pseudo-code
> above computes a weight *per player*, which is why a hand-off has to be special-cased: the
> target player changes. `proto3d` instead targets the **item** (which D-06 requires anyway,
> since aggro must persist to the object) and derives who to chase from whoever is currently
> holding it. Under that structure a hand-off does not change what the Curator wants at all —
> only who has it — so the hot potato is instant **by construction**, and the override row
> becomes a no-op rather than a rule that has to be remembered. Measured in the prototype:
> the mark moves the same frame, inside an active commitment lock, with no exemption code.
>
> The steal threshold and commitment lock still do real work, because a *different* item
> becoming more attractive is a genuine retarget. Keep those two.

**Measured, and it is load-bearing.** When a hand-off lands *inside* an active commitment
lock — which is common, because hand-offs tend to follow the retarget that scared you into
passing — the override delivers aggro in **0.0s**. Without it, **6.0s**. Six seconds of the
Curator walking at the wrong player while the vase strolls away in someone else's hands is
long enough that players would conclude the mechanic doesn't work and stop using it.

### When nobody is carrying anything

Falls through in order: **last dropped high-value item** → walk to it → RESEAT it → PATROL.
It never idle-hunts below Disturbance 85. If the crew is being careful and quiet, the house
is *quiet*, and that contrast is what makes the loud parts land.

At Disturbance ≥ 85 (COLLECT) it drops item logic entirely and targets the nearest player,
full stop.

## A4. Navigation — the intercept

Standard NavMesh A*, with one twist that makes it feel like it's thinking.

**It does not path to the player. It paths to the plinth the item came from.** It's going to
put the vase back where it belongs. Since you're carrying the vase *away* from that plinth
and toward the van, its route and your route converge naturally — it shows up in the doorway
ahead of you rather than trailing behind your shoulder.

```csharp
Vector3 GoalFor(CuratorState s) => s switch {
    PURSUE  => TargetItem.HomePlinth.Position,   // NOT the player
    RESEAT  => CarriedItem.HomePlinth.Position,
    COLLECT => NearestPlayer.Position,           // T4 only
    PATROL  => NextUnverifiedPlinth.Position,
    _       => transform.position
};
```

**Pinch-point bias.** Levels author explicit `PinchNode` markers on doorways, stair
landings, and corridor junctions. When multiple routes to the plinth are within 15% of equal
cost, the Curator prefers the one crossing the most pinch nodes that currently sit between
the target player and the van. Cheap to compute, and it produces the "how did it get *there*"
moment over and over.

**One cheat, and only one.** It never teleports. It never opens a door a player locked. It
never moves in a way that contradicts what a player last saw. Everything it does must be
fully explicable in hindsight — that's the difference between players saying "that was
terrifying" and "that was bullshit."

## A5. Senses

**Sight:** 18m, 100° cone, properly occluded. Darkness does **not** reduce it — it isn't
using eyes.

**Hearing:** ➜ **superseded by `AUDIO-SPEC.md` §1.** Hearing ranges are no longer authored
here. Every noise event carries a single Loudness value `L`, and the Curator's hearing radius
is derived as `L × 0.33` metres, with per-wall attenuation of 0.85 through the portal graph.

The earlier version of this section hardcoded seven hearing ranges while `DESIGN.md` §6.5
separately hardcoded Disturbance gains for the same events — two tables, two sets of magic
numbers, guaranteed to drift apart within a month of content work. There is now exactly one
number per event and three systems reading from it. **Do not re-add ranges to this document.**

Hearing remains omnidirectional and wall-penetrating, and the resulting investigation point
is fuzzed ±3m. It knows roughly where; it doesn't know exactly. So it arrives in the general
area and then you have to not move, which is its own small hell.

## A6. The fairness contract

Every rule here is non-negotiable. A single violation in a playtest costs you more goodwill
than five good scares earn.

1. **Never spawns or transitions to PURSUE within 12m of a player who cannot see it.**
2. **Always audible for ≥ 8m before contact** — a dedicated floorboard/dragging layer that
   is never occluded to zero. You always get to hear it coming.
3. **First contact of a night never kills.** It takes the item. (`DESIGN.md` §6.3)
4. **15s of retarget immunity** after a knockdown, so a downed player is never chain-hit.
5. **Never blocks the only route to the van for more than 20s.** Every estate must author a
   secondary route out of every wing; verify with an automated pathfinding check at build
   time, not by eye.
6. **After RESEAT completes, 10s minimum in PATROL** before it may re-fixate on anyone.

## A7. The readability contract — how the group knows who's marked

**This is the section that makes the game fun with friends.** Everything above is worthless
if the other three players can't tell who's being hunted. The hot potato requires *shared*
knowledge — if only the target knows, nobody hands anything over, nobody makes a sacrifice
play, and the entire social layer of the game silently fails to exist.

**No HUD. No outline. No marker. Diegetic only.** When a player becomes the attention
target:

| Signal | Detail | Who perceives it |
|---|---|---|
| **The item frosts** | condensation then visible frost crawls across the carried object over ~3s | anyone with line of sight to the item |
| **Their flashlight dims to 60%** | smooth falloff over 2s, warm→cold color shift | **everyone**, at any range, through doorways — a dimming cone is visible far past where you can see the person |
| **A low hum** | 8m radius, emitted by the item, not the player | teammates nearby, and it's how you know before you turn around |
| **Their breath fogs** | third-person only — you can see it on *them*, not on yourself | teammates |

Which collapses to one sentence, and this sentence is the actual design deliverable:

> **"If your light is dimming, it's coming for you."**

That's a rule a player learns in one night, teaches a new friend in four seconds, and shouts
across a hallway forever. The dimming flashlight is doing quadruple duty — it's the aggro
indicator, it's a *mechanical* penalty (you can see less exactly when you need to see more),
it's visible to teammates from a distance and through door gaps, and it's the reason people
scream each other's names. Build this before you build the AI. It is more important than
the AI.

**Corollary — the hand-off must be readable too.** When aggro transfers, the frost visibly
crawls off one item onto the receiving player's hands, and their light dims as yours comes
back up. Both players get unmistakable confirmation. If the transfer is ambiguous, players
stop trusting it, and if they stop trusting it they stop doing it.

## A8. Escalation

| Disturbance | State | Speed | Behavior |
|---|---|---|---|
| 0–30 | DORMANT | — | stationary, deep house. Distant sounds only. |
| 30–60 | PATROL | 2.4 | plinth-to-plinth. Retrieval only. |
| 60–85 | PURSUE | 2.9 | active intercept across the whole map. Interior doors begin locking. |
| 85–100 | COLLECT | 3.4 | ignores items. Comes for people. Fairness contract rules 1–5 still apply. |

Rule 6 of the fairness contract is suspended at T4 — at that point the crew has chosen this,
repeatedly, out loud, and everyone at the table knows it.

---

# PART B — THE PHYSICS HANDOFF

## B0. The engineering constraint, stated up front

**Carried items stay fully simulated and keep colliding with the world.**

The correct, safe, professional implementation is to make a carried object kinematic and
parent it to a hand socket. It never jitters, never clips, never fights the netcode. Do not
do this. It deletes the game.

Eighty percent of the laughs in this genre come from a grandfather clock catching a
doorframe, from a vase clipping your friend's head as you turn around, from a chest of
drawers that will not fit through the hall no matter what angle you try. That requires the
carried object to be a real rigidbody having a real bad time. The jitter is worth it. **Pick
funny.**

Implementation: **owner-simulated non-kinematic rigidbody + ConfigurableJoint to a carry
anchor** in front of the player. Spring-damped, with breakable force limits so a hard enough
snag rips it out of your hands.

```
Joint tuning (starting values — expect to spend a full week here):
  spring         600      lower = floppier = funnier, up to a point
  damper          40
  maxForce      1400      exceed it and the item is torn from your grip
  angularSpring  120      items rotate lazily; heavy ones swing
  breakForce    2200      doorframe snag rips it loose
```

## B1. Ownership model

Host-authoritative world, **owner-authoritative carry.**

| Object state | Simulated by | Why |
|---|---|---|
| Resting in the world | host | one authority, no drift |
| Being carried | **carrying client** | responsiveness — 120ms of input lag on a carried object is unplayable |
| Thrown / in flight | **thrower**, until it sleeps | the thrower sees a truthful arc; that's who cares |
| Asleep after landing | host (ownership reverts) | back to a single authority |
| In the van | host | the van is the ledger; it must be authoritative |

**Threat model: none.** This is a co-op game played with friends over Steam. Clients are
trusted completely. No server validation of break events, values, or positions — that
tradeoff buys responsiveness, which is the only thing that matters here. If someone cheats,
their friends will deal with it socially, which is both cheaper and more effective than
anything we could write.

## B2. Pickup protocol

Race condition to design around: two players grab the same vase on the same frame. Host
arbitrates, first request wins, loser gets a clean rejection and a small "missed" animation
so it never looks like a bug.

```
CLIENT                          HOST                          OTHER CLIENTS
  │ RequestPickup(itemId) ───────►│
  │                               │ owner == null?
  │                               │  ├─ no  → DenyPickup ──────►│
  │                               │  └─ yes → assign ownership
  │◄──── GrantPickup(itemId) ─────│──── ItemPickedUp(id,player) ►│
  │ attach joint                  │                              │ attach visual joint
  │ begin local simulation        │ stop simulating              │ interpolate from owner
```

Target: **< 1 frame of perceived delay for the grabbing client** — play the grab animation
optimistically on request and roll back on denial. Denial is rare and a 100ms visual hitch
on a rare event beats input lag on every pickup.

## B3. Drop, throw, and the pry

- **Drop** — release joint, apply owner's current velocity, retain ownership until the body
  sleeps (~2s), then revert to host. *Aggro consequence in `DESIGN.md` §6.1: the Curator
  still comes for the item.*
- **Throw** — impulse along camera forward, scaled inversely by mass. Everything in the game
  is throwable, including corpses. Especially corpses.
- **Pry** (`DESIGN.md` §13 open question) — take an item from a teammate's hands. **1.5s
  hold**, with a loud, obvious tug-of-war animation both players can see. Resolves as an
  ownership transfer with the hand-off aggro override from §A3.
  - Deliberately slow and visible so it is *unmistakably an act of aggression*. It should be
    possible, hilarious, and impossible to do by accident.
  - **No cooldown.** Let them fight over the vase in a doorway while the Curator walks up
    behind them. That's the game.
  - **Modelled, R38.** The pry resolves on the host, and the victim's escape is judged one trip
    time late, so a victim who walks out of range in the last moments sees themselves escape on
    their own screen and lose the item anyway: **3.6% of pries at 120ms, 7.3% at 250ms**
    (`sim/netcode.py`). That is not a bug in the pry, it is where the authority is — but the
    1.5s hold is long enough to fix it cheaply: judge the escape against the victim's own
    reported position at the moment the pry completes, and let the victim's client win ties.
    They are the one who will notice.

## B4. Two-man carry — the hardest problem in the project

Two clients cannot both own one rigidbody. Ownership models are single-owner by design, and
a piano authoritatively simulated by two machines across residential connections will fight
itself, jitter, duplicate, and eventually achieve orbit.

**Anchor / follower, and don't be precious about it:**

```
ANCHOR  (owns the rigidbody)
  - full ConfigurableJoint, exactly as single-carry
  - their movement drives the object
  - mass penalty applied to their locomotion

FOLLOWER (owns nothing)
  - a second spring targets the object's far end toward their carry anchor
  - applies force, never position
  - their input influences rotation and lift, not translation
  - may drift up to 0.4m from "correct" before a soft correction eases in
  - if the anchor disconnects → follower is promoted to anchor within 1 frame
```

It is **not physically honest**, and players will never know. Two people carrying a couch in
real life are also not in agreement about where the couch is. What it must do is survive
120ms of latency and look like two people carrying a piano, badly, which is what it looks
like anyway.

> **Modelled, R38 — the 0.4m is already spent.** `sim/netcode.py` measures how far behind the
> follower's view of the far end actually is, and at the spec's own 120ms budget it is **0.27m
> mean and 0.38m at p95** against a 0.4m tolerance. Walking in a straight line costs 0.13m; the
> rest is the *pivot*, because the far end of a two-man object sweeps at ω·r and 1.4m of lever
> arm turns a lazy turn into two metres a second of far-end travel. At 250ms, 87% of pivots
> exceed the tolerance outright.
>
> So the tolerance as written is not a slop budget with latency inside it — it *is* the latency,
> and the physics gets whatever is left, which at 120ms is nothing. Two consequences for the
> implementation: **scale the tolerance with measured RTT** rather than fixing it at 0.4m, and
> **do not let the correction fire on a pivot** — the one moment it will always trigger is the
> doorway turn, which is exactly where a soft correction fighting the network will look worst.
> The comedy needs the couch to be wrong; it does not need it to snap.

**Which end is which matters for comedy:** the follower — walking backwards, unable to see,
shouting "left, LEFT, MY left" — is the funnier job. Make sure both ends are worth being.
The follower gets the better view of what's behind the anchor, which is where the Curator
usually is.

## B5. Sync, budget, and edge cases

**Transform sync:** 20Hz for awake bodies, position + rotation + velocity, cubic
interpolation on receivers with a 100ms buffer. Sleeping bodies sync on state change only.

**Budget:** hard cap **60 simultaneously awake rigidbodies.** Items sleep aggressively when
untouched and beyond 25m from any player. Nothing in this design needs more; if you're
exceeding it, an estate is overfurnished.

**Fragility:** break threshold on impact velocity, evaluated by the owner, broadcast as an
event. Tuned to a specific comedic target — **a flight of stairs is survivable, a balcony is
not.** Players must be able to gamble on the stairs. That gamble is a load-bearing part of
the fun.

| Edge case | Handling |
|---|---|
| Owner disconnects mid-carry | host claims ownership, item drops at last known position with zero velocity |
| Item clipped into geometry | owner-side depenetration; if unresolved for 3s, teleport to nearest NavMesh point |
| Two grabs, same frame | §B2 host arbitration |
| Item carried into the van | ownership → host on trigger enter; van cargo is host-simulated always |
| Curator RETRIEVE on carried item | forced ownership transfer to host, joint broken, frost VFX released |
| Player disconnects mid two-man carry | follower promoted to anchor, 1 frame |

## B6. Friendly fire — the chaos rules

The rule that makes this genre work, stated explicitly so nobody "fixes" it later:

> **Full friendly-fire physics. Zero friendly-fire damage.**

- You can knock your friend flat with a swung armoire. It does no damage.
- You can throw a vase at their head. It does no damage — and it might break, which costs
  the *crew*, which is a far better punishment than a health bar.
- You can shove someone off a landing. They ragdoll 1.5s, stand up, and are fine.
- You cannot kill a teammate. Not by accident, not on purpose. The Curator does that.

Chaos without consequence is comedy; chaos with consequence is griefing. The van's ledger is
the *only* place friendly fire has a cost, and it's a shared cost, which turns every incident
into a group grievance instead of a personal one. "You owe the crew four hundred dollars" is
funnier and more social than any damage number.

---

# PART C — BUILD ORDER

Neither system is built in one pass. Order matters, and each row is independently testable.

| # | Build | Validates | Blocks |
|---|---|---|---|
| **C1** | Single-item pickup/carry/drop, one client, no net | joint tuning, the "feel" | everything |
| **C2** | Same over network, 2 clients, ownership transfer | §B1–B2 — **the core technical risk** | all physics |
| **C3** | Throw, pry, friendly-fire physics | §B3, §B6 — *is it funny yet?* | — |
| **C4** | Two-man carry, anchor/follower | §B4 — the hard one | corpses, big loot |
| **C5** | Readability contract: frost, dimming light, hum | §A7 — **build before the AI** | hot potato |
| **C6** | Attention + hysteresis + hand-off override, no navigation | §A3 — aggro reads correctly while it's standing still | pursuit |
| **C7** | State machine + intercept pathing + FIXATE | §A2, §A4 | — |
| **C8** | Senses, fairness contract, escalation tiers | §A5, §A6, §A8 | ship |

**C5 before C6/C7 is not a typo.** Build the aggro *display* before the aggro *logic*. A
target indicator with a dumb monster is testable and immediately fun; a brilliant monster
nobody can read is a week of debugging why playtesters look bored while being hunted.

**The checkpoint is C3.** Four people, a room full of junk, a van, no monster, full physics
chaos. If that isn't already making people laugh, the Curator will not rescue it — and you
will have learned it three weeks in, for the price of three weeks.
