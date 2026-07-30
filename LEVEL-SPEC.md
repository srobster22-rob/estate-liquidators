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

Every wing ships a declaration alongside its geometry. The sketch below is authoring shorthand — there is no YAML loader in the repo and the validator does not read it. What `sim/validate_estate.py` actually consumes is a whole-estate Python dict, of which `sim/estates.py` MANOR_A is the reference instance: `rooms` as name → {pos, tier, van}, `portals` as a flat list of {a, b, width, door|archway, pinch, entrance} (pinch is a per-portal flag, not a separate `pinch_nodes` list), `plinths` as {room, cls, tier, value}, `prereqs` as room → [{room, type}], and `curator_spawn` as a room name.

```yaml
id: east_conservatory
depth_tier: 3                    # 1–4; drives value band and prereq depth
rooms: 4

portals:                         # doorways into the wing
  - { to: core.grand_stair, type: door,           locked: true  }
  - { to: core.service_hall, type: boarded,       locked: false }   # V3 needs this

prerequisites:                   # what must happen before this wing opens
  - key: conservatory_key        # spawns in a depth-1 or depth-2 wing
  - power: cellar_breaker        # optional; gates lights, not access

pinch_nodes:                     # authored, not inferred
  - stair_landing
  - conservatory_door

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

**Narrow is not the same as pinched, and silence is not an answer.** Every portal ≤ 2.0m wide —
the width in the first bullet — must carry an explicit `pinch: true` or `pinch: false`.
Omitting the flag does not default to false; it is a **V4 failure** and the wing is rejected.
This guard exists because V3 and V4 pull against each other: every second route added to
satisfy V3 (§5) tended to be another narrow corridor that nobody remembered to classify, and an
unclassified corridor is precisely the unpinched bypass that defeats this section
(`LOOP_LOG.md` R1). The wing entrance is exempt.

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
| **V2** | Every tier-2/3/4 room opens only after ≥1 / ≥2 / ≥3 completed prerequisite steps, and every prerequisite sits at a strictly shallower tier | `DECISIONS.md` D-20 — work, never wall-clock |
| **V3** | ≥2 edge-disjoint routes from every wing room back to the **Core** — no single non-`entrance` portal may seal a wing off. Not to the van: the front door is a designed singularity, so portals flagged `entrance` are exempt | fairness contract #5 |
| **V4** | Every tier-3/4 plinth→van route crosses ≥2 pinch nodes, **and every non-entrance portal ≤2.0m wide declares `pinch` explicitly** | `TECH-SPEC.md` §A4 |
| **V5** | Curator audibility ≥8m through every wall configuration in the wing | `AUDIO-SPEC.md` §3.1 — **the contract test** |
| **V6** | Portal graph closed: no unreachable room, no orphan portal, every doorway has a door | audio occlusion |
| **V7** | NavMesh connectivity: Curator can reach every plinth *and* carry an item back to it | RESEAT can't dead-end |
| **V8** | Every plinth's value sits inside its own depth tier's band | `ECONOMY.md` §3 economy sanity |
| **V9** | No **tier-1-or-deeper** plinth within 15m of the van (tier 0 exempt — cheap loot by the door is deliberate, and per-slot pricing already makes foyer-farming a losing play: `ECONOMY.md` §3) | no free money |
| **V10** | **Every two-man and cart-class plinth has a route to the van wide enough to carry it** | see below |

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
   ruin someone's night. Then flag every *other* portal ≤2.0m wide `pinch: false` — the
   validator will not let you leave it unsaid.
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
