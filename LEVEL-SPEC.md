# ESTATE LIQUIDATORS — Level Spec
## The estate module contract, and the checks that enforce it

Closes open decision **O-04**. Companion to `DESIGN.md` §7.

Every rule in the other documents makes a promise about the *space*. The Curator intercepts
you at pinch points — a level with no pinch points has no Curator. The fairness contract
guarantees a second route out — a level with one corridor breaks it. Depth gates pacing — a
level where the deep wing opens immediately inverts the whole escalation curve.

**None of those promises survive contact with a level designer under deadline unless a
machine checks them.** So this document is really two things: a template for authoring a
wing, and a validation suite that fails the build when a wing lies.

---

## 1. Anatomy

```
ESTATE = CORE  +  3–5 WINGS drawn from the pool

CORE (authored once per estate, never procedural)
  ├── Driveway + VAN          the extraction point, the ledger, the only safety
  ├── Foyer                   depth 0. Cheap loot. Always open.
  ├── Grand stair             the primary pinch point of the whole house
  └── Service corridor        the secondary route. Exists so rule V3 can pass.

WING (authored module, procedurally selected)
  ├── 3–5 rooms
  ├── 1 depth tier (1–4)
  ├── ≥1 entry portal, ≥2 total portals   ← V3
  ├── prerequisite chain                   ← V2
  └── plinth set matching its value band
```

The Core is hand-built and constant; wings shuffle. That gives every night the same
comprehensible spine — you always know where the van is — with genuinely different interiors
hanging off it. Players learn a *language*, not a map.

## 2. The module contract

Every wing ships a declaration alongside its geometry. This is the file the validator reads:

```yaml
id: east_conservatory
depth_tier: 3                    # 1–4; drives value band and prereq depth

rooms:                           # value_class drives the appraiser's payoff — see §2.1
  - { id: r1, value_class: curio }
  - { id: r2, value_class: mixed }
  - { id: r3, value_class: mixed }
  - { id: r4, value_class: shelf }

portals:                         # doorways into the wing
  - { to: core.grand_stair, type: door,           locked: true  }
  - { to: core.service_hall, type: boarded,       locked: false }   # V3 needs this

prerequisites:                   # what must happen before this wing opens
  - key: conservatory_key        # spawns in a depth-1 or depth-2 wing
  - power: cellar_breaker        # optional; gates lights, not access

pinch_nodes:                     # authored, not inferred
  - stair_landing
  - conservatory_door

hiding_places:                   # wardrobes, crates, under-stairs — see 2.2, V12
  - { id: h1, room: r1 }
  - { id: h2, room: r3 }

plinths:
  - { id: p1, class: armful,  band: high,   fragility: 3 }
  - { id: p2, class: armful,  band: mid,    fragility: 1 }
  - { id: p3, class: two_man, band: high,   fragility: 0 }
  - { id: p4, class: pocket,  band: low,    fragility: 0 }
  - { id: p5, class: cart,    band: apex,   fragility: 2 }

curator_spawn: false             # exactly one wing per estate may be true
```

### Value bands by depth tier

| Tier | Where | Band range | Feel |
|---|---:|---|---|
| 0 | Foyer (Core) | $40 – 150 | the tutorial you never notice |
| 1 | Ground floor | $80 – 300 | safe money, never enough |
| 2 | Upper floor / cellar | $250 – 700 | the working middle |
| 3 | Sealed wings | $600 – 1400 | where crews start dying |
| 4 | The apex room, one per estate | $4,000 – 8,000 | one object. Cart class. Everybody knows about it. |

> **Re-banded from $1,500–3,000 by `ECONOMY.md` §3.** At 5 slots the original band priced the
> apex at $300–600 per slot — worse than a tier-2 armful. The most dangerous object in the
> house was mathematically a trap, and any player who did the arithmetic once would have
> correctly ignored it forever. Full slot-value table in `ECONOMY.md` §3.

**One apex object per estate, and it must be visible early.** Players should walk past
something they cannot yet take, in the first ninety seconds, and spend the rest of the night
arguing about it. That single authored moment does more for a run's shape than any system.

> **This is not just drama — it's load-bearing economics** (`ECONOMY.md` §8, `DECISIONS.md`
> D-21). A crew only holds five van slots back for the apex if it knows the apex exists.
> Simulated without that foreknowledge, the van is full by the time it unlocks and the apex
> is taken **0–7% of the time**. With it, 100%. An unseen centrepiece is a centrepiece nobody
> ever takes.

### 2.1 Room value classes — the appraiser's content lever

`DESIGN.md` §4.4 Requirement C: **the appraiser's payoff is a property of the room, not a
global constant.** Scanning is worth `0.6 × spread × room mean`, so a wing built entirely
from evenly-priced rooms makes the game's signature verb a habit with a fixed rate of return.
This is the lever that fixes it, and it lives here in level authoring — not in tuning.

| `value_class` | Spread about the room mean | Target share | Dress it as |
|---|---:|---:|---|
| `shelf` | ±10% | 30% | matched sets. Encyclopaedias, tinned goods, a run of identical chairs, a filing room. |
| `mixed` | ±40% | 45% | an ordinary furnished room — the default. |
| `curio` | ±110% | 25% | junk and treasure on the same shelf. Cabinets of oddments, a hoarder's sideboard, the estate sale table. |

**The class must be readable from the doorway, before anyone spends three seconds and a noise
spike.** A curio room that doesn't *look* like a lottery converts a decision into a coin flip,
which is worse than not having the mechanic — it costs the noise and returns the average.
This is a dressing contract, and it is the one art requirement in this document that is
load-bearing rather than aesthetic (`ART-DIRECTION.md` owes it a treatment).

Note this pulls in the opposite direction to §4.4 Requirement B, which insists an *individual*
item's value is illegible. Both hold: **the room's variance is public, the item's value is
private.** You can see that the cabinet is a lottery; you cannot see which drawer won. If
that reads as contradictory in play — if testers say the room already tells them what to take
— Requirement C is the one to weaken, because B is what keeps the appraiser alive at all.

Enforced by **V11**. Below ~10% curio the mechanic stops paying (+6.2% and falling); above
~40% everything is worth scanning and the reading stops mattering. Both ends collapse back
into a habit, which is the failure §4.4 exists to prevent.

### 2.2 Hiding places — a balance parameter dressed as furniture

`DESIGN.md` §8.1 gives the crew four responses to being hunted, and three of them require a
wardrobe, a crate, a dust sheet or the space under a stair to be *within reach at the moment
of panic*. So concealment density is not set dressing that a level artist adds at the end —
it decides how often the mechanic exists at all.

`sim/hiding.py` models availability at **55%**, meaning nearly half of all encounters offer
no concealment option whatsoever (45%). That is deliberate: a house where you can always hide has no
chase in it, and a house where you can never hide has no §8.1. But it only holds if wings are
authored to it.

| Rule | Value |
|---|---|
| Minimum per wing | **2** hiding places |
| Coverage | every plinth within **12m** of one, along a walkable route |
| Never | in the same room as the wing's only exit portal — that turns a pinch point into a safe room |
| Placement intent | *on* the plinth→van route, not tucked in dead ends. A hiding place you have to detour to is one nobody uses under pressure. |

Enforced by **V12**. Note the tension with `TECH-SPEC.md` §A9: a stash is safe only if it is
more than 40m from the item's home plinth, so a wing whose hiding places all sit next to its
plinths satisfies V12 and still makes stashing useless. That is a judgement the validator
cannot make for you — V12 checks that the option exists, not that it's worth taking.

## 3. Prerequisite chains — the pacing mechanism

`DESIGN.md` §7 makes gating the pacing system rather than set dressing. Concretely:

> **A wing's prerequisites must live at a strictly shallower depth tier — and they must be
> gated by WORK, never by a timer** (`DECISIONS.md` D-20).

The conservatory key is in a tier-1 or tier-2 room. Never in another tier-3 wing, never in
the conservatory itself. This makes the intended shallow→deep progression physically
enforced instead of merely encouraged, and it's why the naive "sprint to the money at T=0"
strategy cannot be executed.

**Chain length by tier** — minimum number of prerequisite steps:

| Tier | Min chain | Typical time-to-open |
|---:|---:|---|
| 1 | 0 | immediate |
| 2 | 1 | ~2 min |
| 3 | 2 | ~4 min |
| 4 (apex) | 3 | ~6–7 min |

The times in that table are what a **four-person** crew should achieve, not a countdown. A
six-person crew completes the same chains faster and should reach depth sooner; a two-person
crew may never reach tier 4 at all, and that's correct. Implementing these as clock timers
instead of task chains silently punishes larger crews — see D-20, which is the single least
obvious finding in the whole design.

The apex object opening around minute six or seven is the design intent: it becomes available
*exactly* when Disturbance is climbing and the sunrise timer is real. The decision to go for
it is never made from a position of comfort.

## 4. Pinch points

Pinch nodes are **authored markers**, not inferred from geometry. Inference will find you a
"pinch point" in the middle of a ballroom and the Curator will do something stupid there.

A valid pinch node is a doorway, stair landing, or corridor junction where:

- effective width ≤ 2.0m (a two-man carry cannot pass someone standing there)
- there is no line of sight through it from more than 8m
- it lies on a plausible route between a plinth and the van

**Every route from a tier-3 or tier-4 plinth back to the van must cross at least two pinch
nodes** (V4). This is the level's half of `TECH-SPEC.md` §A4 — the Curator's plinth-intercept
pathing is only frightening if the geometry gives it somewhere to intercept you.

## 5. Routes, doors, and sound

**Two routes minimum, always** (V3). The fairness contract promises the Curator can never
block the only way out for more than 20 seconds. That promise is kept in geometry or not at
all. The Core's service corridor exists purely so that wings with a single grand entrance can
still satisfy this.

**The second route should be worse.** Narrower, darker, longer, or requiring a crowbar. It's
an escape valve, not an equal option — otherwise players just always take the safe one and
the pinch points never do their job.

**Doors are load-bearing for audio.** `AUDIO-SPEC.md` §1.3 counts walls through the portal
graph, and an open door is zero walls while a closed one is one. Every doorway must therefore
be a real portal with a real door object. A decorative archway is a permanent hole in the
sound design — use them deliberately and sparingly, in places where you *want* sound to carry.

## 6. Validation suite

Run in CI on every level change. **A wing that fails any check does not enter the pool.**

| # | Check | Enforces |
|---|---|---|
| **V1** | Every room reachable from the foyer given a complete prerequisite chain | basic sanity |
| **V2** | Deepest room unreachable before T+4min, apex before T+6min, via simulated traversal at 2.6 m/s carry speed | `DESIGN.md` §7 pacing |
| **V3** | ≥2 topologically distinct routes from every wing to the van | fairness contract #5 |
| **V4** | Every tier-3/4 plinth→van route crosses ≥2 pinch nodes | `TECH-SPEC.md` §A4 |
| **V5** | Curator audibility ≥8m through every wall configuration in the wing | `AUDIO-SPEC.md` §3.1 — **the contract test** |
| **V6** | Portal graph closed: no unreachable room, no orphan portal, every doorway has a door | audio occlusion |
| **V7** | NavMesh connectivity: Curator can reach every plinth *and* carry an item back to it | RESEAT can't dead-end |
| **V8** | Total wing value within ±15% of its depth band | economy sanity |
| **V9** | No plinth within 15m of the van | no free money |
| **V10** | **Every two-man and cart-class plinth has a route to the van wide enough to carry it** | see below |
| **V11** | Every room declares a `value_class`, and 15–35% of the wing's rooms are `curio` | §2.1 — the appraiser has a payoff worth reading the room for |
| **V12** | ≥2 hiding places per wing, every plinth within 12m of one, none in a sole-exit room | §2.2 — three of §8.1's four verbs need furniture in reach |

**V10 deserves its own paragraph.** A piano that physically cannot leave the room it spawned
in is a rage-quit bug — four people spending three real minutes discovering that a doorway is
2cm too narrow, with a monster closing in. It will happen, it will happen repeatedly, and it
is invisible in the editor. The check walks the item's bounding box along every route with
the two-man carry pose applied. Automate it before the first wing ships, not after the first
bug report.

## 7. Authoring workflow

1. **Block out rooms and portals.** Every doorway gets a door.
2. **Declare depth tier**, and derive the prerequisite chain length from §3.
3. **Place prerequisites in shallower wings** — never within your own tier or deeper.
4. **Mark pinch nodes by hand.** Walk the plinth→van routes and ask where you'd stand to
   ruin someone's night.
5. **Place plinths** to the value band, mixing weight classes. Every wing wants at least one
   two-man object — that's where the arguments come from.
6. **Author the second route**, and make it worse.
7. **Run the validator.** Fix what it says. It is not negotiable and it is not a linter.
8. **Playtest for the walk-past moment** — is there something in this wing you see before you
   can take it?

## 8. Worked example — East Conservatory (tier 3)

> Entered from the grand stair through a locked door; the key is in the tier-1 study. A
> boarded servants' passage connects it to the service hall — the crowbar route, narrow,
> dark, and it makes noise to open.
>
> Four rooms: the conservatory proper (glass, moonlight, the one lit space in the wing), a
> potting room, a collapsed orangery, and a small locked office.
>
> **The bait:** a taxidermy peacock under glass, tier-3 band, fragility 3, sitting on a
> pedestal directly in the sightline as you enter. It is worth $1,200 and it will not survive
> being dropped down the grand stair, and everyone will find that out together.
>
> **Pinch nodes:** the stair landing outside the entry door, and the potting-room doorway —
> the only two-man-passable route out of the orangery, and the one the Curator arrives
> through when it comes to reseat the peacock.
>
> **Second route:** the servants' passage. Narrow enough that the cart-class item cannot use
> it, so the apex loot must go back through the pinch points. That constraint is the wing's
> entire personality.

---

## 9. What this doesn't cover yet

Deliberately unbuilt, in rough priority order:

- **Estate archetypes beyond the manor.** The hospital annex, storage facility, and ship
  from `DESIGN.md` §9 need their own Core layouts. The wing contract should transfer intact;
  that's the point of writing it as a contract.
- **Lighting authoring standards.** Breaker coverage per wing, moonlight rules, which rooms
  are never lit.
- **Curator spawn placement heuristics** beyond one flag per estate.
- **Prop dressing density budgets** — the line between "furnished" and "60 awake rigidbodies"
  (`TECH-SPEC.md` §B5).
