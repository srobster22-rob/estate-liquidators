# ESTATE LIQUIDATORS — Economy Model

Closes open decisions **O-03** (van capacity) and **O-06** (quota curve).

**Everything here is a starting model, not a measurement.** These numbers exist so Milestone
2 has something specific to falsify — a wrong number you can test beats a vague number you
can't. Expect most of them to move.

The one thing that must *not* move is the constraint this is all built to produce:

> **A crew must be able to haul more than the van can hold.** If van space doesn't bind,
> selection doesn't matter; if selection doesn't matter, nobody appraises; if nobody
> appraises, the game's signature mechanic is dead (`DESIGN.md` §4.4, `DECISIONS.md` D-10).

Every number below is reverse-engineered from that sentence.

---

## 1. Van capacity: 14 slots

| Weight class | Slots | Rationale |
|---|---:|---|
| Pocket | 0.5 | filler that tops off a van, never a strategy |
| Armful | 1 | the unit of account |
| Two-man | 3 | |
| Cart | 5 | a third of the van for one object |

**Base van: 14 slots.** Shelving upgrades: +2 per tier, hard ceiling **20**. The ceiling is
not a balance knob, it's a design guarantee — capacity may never grow to the point where
choosing stops hurting.

## 2. Does it actually bind? (the arithmetic)

A 12-minute night is 720s. Roughly 90s of that is approach and first entry, and the last 90s
is the run home, leaving a **~540s effective haul window** per player.

| Depth | Round trip (grab + carry + return) | Trips per player |
|---|---:|---:|
| Tier 1 (ground floor) | ~45s | ~12 |
| Tier 2 (upper / cellar) | ~60s | ~9 |
| Tier 3 (sealed wing) | ~90s | ~6 |

Four players working tier 2 cleanly: **~36 armful trips.** Discount hard for reality —
appraisal time, deaths, Curator interruptions, the piano argument, someone going the wrong
way — and call it **20–24 items actually extracted** on a good night.

**Van holds 14 slots. A functioning crew can move 20–24 items. The constraint binds by a
margin of roughly 40%.** That margin is the appraiser's entire reason to exist, and it's the
first number to re-measure the moment real playtest data arrives.

## 3. Value bands, priced per slot

Depth must pay *per slot*, or the optimal play is to farm the foyer forever.

| Tier | Class | Value | **Per slot** |
|---:|---|---|---:|
| 0–1 | pocket | $40 – 150 | $80 – 300 |
| 0–1 | armful | $80 – 300 | $80 – 300 |
| 2 | armful | $250 – 700 | $250 – 700 |
| 2 | two-man | $700 – 1,900 | $233 – 633 |
| 3 | armful | $600 – 1,400 | $600 – 1,400 |
| 3 | two-man | $1,800 – 4,000 | $600 – 1,333 |
| **4** | **apex (cart)** | **$4,000 – 8,000** | **$800 – 1,600** |

### The apex bug this arithmetic caught

`LEVEL-SPEC.md` originally banded the apex object at **$1,500–3,000**. At 5 slots that's
$300–600 per slot — *worse than a tier-2 armful*. The single most dangerous object in the
house, the one the whole night is supposed to build toward, was mathematically a trap. Any
player who did this arithmetic once would have correctly ignored it forever, and the estate's
authored centrepiece would have become a joke.

Re-banded to **$4,000–8,000**. `LEVEL-SPEC.md` §2 is updated to match.

Note that two-man items are deliberately *slightly* worse per slot than armfuls of the same
tier. They're big single grabs that solve a logistics problem — one trip instead of three —
and they cost two people and a pinch-point crossing to move. They should never also be the
efficient choice.

## 4. Quota curve

A contract chain is 4 nights. Van capacity rises with upgrades; accessible depth rises with
crew skill.

> ⚠️ **The original curve here was wrong and has been replaced.** It was napkin arithmetic
> that assumed earnings scale with the quota. They don't — see §8. Nights 1–3 passed 100% of
> the time and night 4 passed **1%**: three formalities followed by a wall. Kept visible
> rather than quietly deleted, because the failure mode is instructive.
>
> | Night | Old quota | Simulated pass rate |
> |---:|---:|---:|
> | 1 | $2,000 | 100% |
> | 2 | $4,500 | 100% |
> | 3 | $8,000 | 100% |
> | 4 | $15,000 | **1%** |

**Calibrated curve.** A crew earns $9,373 / $9,919 / $10,997 / $12,152 across the four nights
— only **+30% growth**, because van capacity rises just 14→19 and the estates are equally
rich every night. The quota has to live inside that range or the chain has no shape.

| Night | Quota | Van | Sim mean | Pass rate | Feel |
|---:|---:|---:|---:|---:|---|
| 1 | $7,500 | 14 | $9,373 | ~95% | you can be a coward and survive |
| 2 | $9,000 | 15 | $9,919 | ~73% | tier 2 is now mandatory |
| 3 | $10,750 | 17 | $10,997 | ~55% | someone has to go into a sealed wing |
| 4 | $12,500 | 19 | $12,152 | ~40% | above the mean. The apex is not optional. |

> **R26 — this curve was calibrated in a model where appraising is free, and it is
> 10–14 points harder than intended once it isn't.** `chain_sim.py` had no Disturbance and
> no Curator (§10), so its crew read every candidate's value at no cost — the one assumption
> `DESIGN.md` §4.4 exists to deny. With the tuned Disturbance model and retrieval ported in,
> and three stationary seconds plus a ping charged per item examined, the same crew earns less
> and passes less often:
>
> | Night | Quota | Free information | With the appraiser paid for |
> |---:|---:|---:|---:|
> | 1 | $7,500 | $9,356 · 94% | $9,059 · **86%** |
> | 2 | $9,000 | $9,930 · 73% | $9,493 · **62%** |
> | 3 | $10,750 | $11,002 · 56% | $10,429 · **43%** |
> | 4 | $12,500 | $12,141 · 41% | $11,556 · **30%** |
>
> **Re-calibrated curve, restoring the intended feel: $6,750 / $8,500 / $10,250 / $12,000.**
> Roughly $500–750 off each night. The shape and the design intent behind each night are
> unchanged — this is paying for a cost the model previously ignored, not a rebalance.
>
> Run `python sim/chain_sim.py` for the current numbers.

**The better fix, and the one to make before ship:** growth should come from the *estates*,
not from squeezing the crew against a flat ceiling. Later contracts should be richer houses
with higher value bands, so earnings genuinely climb and the quota can climb with them. The
curve above is correct for the game as currently specified; a richer-estates progression
would let it breathe.

Miss a quota and the chain ends. Money doesn't carry across chains (`DESIGN.md` §9).

## 5. Deductions

The ledger is the punchline (`DESIGN.md` pillar 4), so deductions must be legible, itemised,
and read aloud well:

| Line | Amount |
|---|---|
| **Breakage** | full appraised value, listed by item and by *who was holding it* |
| **Curse fee** | 8% of a tainted item's value, 20% of a malignant one — the estate's cut for handling it |
| **Unstrapped cargo** | reclaimed at sunrise; shows as a loss, not an absence |
| **Medical** | none. Death costs a hauler, never money (`DECISIONS.md` D-11). |

Curse fees are the mechanism that stops malignant items being a pure no-brainer at ×6 value.
After a 20% fee a malignant item is still ×4.8 — worth taking, but the number on the ledger
now reflects that you paid something for the privilege, out loud, in front of everyone.

## 6. Simulation results

`sim/haul_sim.py` is a Monte Carlo of the haul loop, built to kill D-10 early if it deserved
killing. Three strategies compete over a night: **BLIND** (grab, never scan), **SCAN_ALL**
(appraise every candidate, always take the best), and **ADAPTIVE** (haul blind until the van
is 70% full, then start scanning because from there the only gains are swaps).

### Result 1 — the appraiser survives, and van capacity is why

At the chosen 14 slots, SCAN_ALL earns **+84%** over BLIND. That's not close. But the
interesting part is the sweep:

| Van slots | BLIND | SCAN_ALL | ADAPTIVE | Best | Appraiser's edge |
|---:|---:|---:|---:|---|---:|
| 6 | $2,526 | $7,749 | $2,895 | SCAN_ALL | **+207%** |
| 10 | $4,897 | $11,200 | $7,537 | SCAN_ALL | +129% |
| **14** | **$7,037** | **$12,911** | $10,112 | SCAN_ALL | **+84%** |
| 18 | $9,407 | $14,018 | $12,422 | SCAN_ALL | +49% |
| 24 | $13,522 | $15,397 | $16,006 | ADAPTIVE | +18% |
| 32 | $18,052 | $15,397 | $17,627 | **BLIND** | **0%** |
| 48 | $18,052 | $15,397 | $18,052 | BLIND | 0% |

The edge decays monotonically as the van grows, and **somewhere between 24 and 32 slots the
appraiser dies outright** — scanning becomes a waste of time you could have spent hauling.
This is exactly the mechanism `DESIGN.md` §4.4 predicted, now with a number on it.

> **Superseded in R24 — do not quote the 24–32 figure.** It comes from `haul_sim.py`, which
> predates `PARALLEL_EFFICIENCY` (R7), the slot-accounting fix (R8), the derived Disturbance
> model (R5) and the cursed-floor correction (R18) — all four of which changed how many trips
> a crew gets, which is what the capacity argument turns on. Re-run against the corrected
> model (`sim/appraiser_variance.py::sweep_capacity`), the cliff is at **21 trips**, and it is
> arithmetic rather than a measurement: `6.93 + 5.20 + 8.67 = 20.8` hauls fit in a
> 540-second night. Below that the van binds and the appraiser earns +8–13% on a V11 estate;
> at 22 slots and above the crew stalls at 21 trips and earns identical money at 24 and 32.
> **The lever above 21 slots is the clock, not the van.** See D-19.

**This sharpens D-19.** The 20-slot ceiling was chosen by instinct; it turns out to sit just
below where the mechanic starts collapsing. Shelving upgrades must never approach it. If
anyone ever proposes a capacity buff, this table is the answer.

### Result 2 — time is not what makes appraisal expensive

Sweeping the scan duration from 1s to 9s per item barely moves the outcome. At 14 slots the
binding constraint is van space, not the clock, so there's enough slack that a longer scan
costs almost nothing. (The sweep is also non-monotonic — that's integer trip counts
interacting with the tier-3 unlock, not signal. Don't read the steps.)

**This has a direct design consequence.** `DESIGN.md` §4.1 frames the appraiser's cost as
"3 stationary seconds *and* a noise spike". The seconds are decoration. If appraising needs
to feel expensive, **lengthening the scan will not do it** — the noise has to carry the
entire weight.

### Result 3 — the tuning target

So the real knob is how badly noise punishes you. Modelling each scan as +4.3 Disturbance
(`AUDIO-SPEC.md` §1.2) and Disturbance as a per-trip chance of losing what you're carrying:

| Loss coefficient | BLIND | SCAN_ALL | ADAPTIVE | Best |
|---:|---:|---:|---:|---|
| 0.00 | $7,035 | $12,937 | $10,129 | SCAN_ALL |
| 0.25 | $7,160 | $10,693 | $9,807 | SCAN_ALL |
| **0.50** | $7,255 | $8,026 | **$9,141** | **ADAPTIVE** |
| **0.75** | $7,323 | $4,528 | **$7,947** | **ADAPTIVE** |
| 1.00 | $7,351 | $779 | $5,895 | BLIND |
| 2.50 | $7,204 | $166 | $4,881 | BLIND |

**Target the 0.50–0.75 band.** That's the only region where ADAPTIVE wins — where the right
play is to scan *selectively*, judging when information is worth the noise. Below it,
scan-everything dominates and there's no decision to make. Above it, the appraiser is dead
and everyone grabs blind.

A game with a skill ceiling lives in that band. Tune Disturbance-to-consequence until real
players land in it.

> ### Superseded — the loss coefficient was a placeholder
>
> That whole sweep used a free parameter standing in for a Disturbance system that didn't
> exist yet. It exists now (§6.5 of `DESIGN.md`, tuned in LOOP_LOG R4), so the punishment can
> be derived instead of guessed. `sim/integrated.py` couples the haul loop to real
> Disturbance. Results in §9 below — **the appraiser's edge is +31%, not +84%.**

### What the model does not include

Stated plainly, because these all matter: no Curator as an actual agent, no hot potato, no
curse grades, no two-man or cart items, no breakage, no deaths, no ghost, and no
communication between players. SCAN_ALL is also a *perfect* optimiser, which no human is —
so the real-world edge is smaller than +84%.

The risk-free version of this model is deliberately generous to the appraiser: it charges
time for scanning and nothing else. That made it a fair kill test. The mechanic survived a
test rigged in its favour, which is weaker than proof and much better than nothing.

## 8. Chain simulation — three more findings

`sim/chain_sim.py` models a full night with real weight classes, shared crew labour, and
depth that unlocks as prerequisite chains complete. It exists to check the three things §3
and §4 asserted from arithmetic alone.

### Finding 1 — the quota curve had no shape

Covered in §4. Earnings grow +30% across a chain while the old quota grew 650%. Three free
nights and one impossible one.

### Finding 2 — the apex works, but only because it's visible early

After the re-band to $4,000–8,000 the apex is worth taking: **+21% on night 1, +6% on night
4**, and a crew takes it 100% of the time. The re-band was correct and did not overshoot.

**But it only works if the crew holds five slots back for it** — and they'll only do that if
they know it's there. When the sim didn't reserve, the van was full by the time the apex
unlocked and it was taken **0–7% of the time**, contributing nothing.

`LEVEL-SPEC.md` §2 already requires the apex to be visible in the first ninety seconds. That
was written as a *drama* rule: walk past something you can't yet take, and argue about it all
night. It turns out to be an **economic load-bearing rule** — without it the estate's
centrepiece is never taken by anyone, ever. The dramatic requirement and the economic
requirement are the same requirement, which is a good sign the design is coherent.

### Finding 3 — depth must be gated by work, not by the clock

This one was hiding behind a model bug that took three rewrites to see.

Gating depth on wall-clock time makes **bigger crews earn less**: six people fill the van
twice as fast as three, so they hit capacity while only the cheap tiers are open, and end the
night with a van full of foyer junk. Crew 2 outearned crew 6 by 2×, which is absurd.

Gating depth on *labour* — find the key, flip the breaker, pry the boards, all of which go
faster with more hands — inverts it back to sane. Earnings then rise monotonically with crew
size: $5,108 / $10,131 / $12,131 / $12,820 / $13,586 for crews of 2–6.

`LEVEL-SPEC.md` §3 already specifies task-based prerequisites. This finding says that isn't
a flavour choice — **clock-based gating would silently punish larger crews**, and the bug
would have been extremely hard to diagnose from playtest reports.

### What this cost D-18

Crew size 4 was justified in the decision log on economics: a 40% overflow margin. The sim
says the economy mildly *prefers more people* (+12% from 4 to 6, with diminishing returns).
The honest position is that **the case for four is voice legibility, not money** — and D-18
has been corrected to say so.

### The three models it took to get here

Recorded because the wrong ones were each convincingly wrong:

| Model | What it did | Why it was wrong |
|---|---|---|
| **Myopic** | filled the van greedily, phase by phase | packed foyer junk by minute four, never reached the apex, made night 4 impossible |
| **Omniscient** | solved the whole night as one knapsack | cherry-picked a load it could never have seen, cleared every quota by 2×, and generated forty apex objects instead of one |
| **Online (current)** | decides shelf by shelf against an adaptive reservation price | — |

The first two disagreed by a factor of four on the same question. Any single one of them,
taken on its own, would have produced confident and completely wrong tuning.

## 9. Integrated night — the appraiser re-measured against real noise

`sim/integrated.py` couples the haul loop to the tuned Disturbance model, so appraising
costs its actual `L=48 × 0.09 = +4.32` per ping, that drives the Curator's tier, and the tier
drives how often your cargo gets taken.

| Strategy | Mean | Scans | Items lost | End Disturbance | vs BLIND |
|---|---:|---:|---:|---:|---:|
| BLIND | $6,511 | 0 | 0.0 | **30** (PATROL) | — |
| ADAPTIVE | $7,783 | 33 | 1.3 | 99 | +19.5% |
| SCAN | $8,513 | 69 | 3.3 | **100** (COLLECT) | **+30.8%** |

> ### ⚠️ Superseded again by LOOP_LOG R8 — read §9.1 before using these numbers
>
> The table above still contained a slot-accounting bug: a retrieval didn't consume a van
> slot, so losing cargo acted as a **free reroll**, and rerolls preferentially help the picky
> strategy. Harsher punishment made scanning *richer*, which is nonsense. Corrected figures
> in §9.1.

**D-10 survives, at less than half its previous margin.** The +84% from §6 was inflated ~2.7×
by using a placeholder for noise cost. Scanning still pays — by +31%.

## 9.1 Corrected — and it reverses two earlier conclusions

With attempts (not successes) counted against the depth budget, the model finally passes its
own sanity check: harsher retrieval now monotonically lowers **every** strategy's earnings.

| PURSUE / COLLECT | BLIND | ADAPTIVE | SCAN | Best |
|---|---:|---:|---:|---|
| 0.00 / 0.00 | $6,520 | $7,777 | $8,308 | SCAN |
| 0.05 / 0.12 | $6,511 | $7,369 | $7,442 | SCAN |
| **0.10 / 0.25** ← as designed | **$6,497** | **$6,889** | $6,481 | **ADAPTIVE** |
| 0.20 / 0.50 | $6,470 | $6,015 | $4,697 | BLIND |
| 0.30 / 0.70 | $6,440 | $5,231 | $3,271 | BLIND |

**Two prior conclusions were wrong, both caused by the same bug:**

- §9 claimed *always-scan dominates and there is no decision to make*. False. At the
  **already-designed** retrieval rates, **selective scanning is the optimal policy** — ADAPTIVE
  beats both extremes. No retuning of RETRIEVAL is needed.
- LOOP_LOG R6 argued no middle strategy could ever have a wide optimum, since ADAPTIVE is a
  linear interpolation between two extremes. That pessimism was itself an artifact. The band
  exists, and the design already sits in it.

**But the margin is small: +6% over blind hauling**, down from the +84% first reported and the
+31% second. That is the number to argue about now. A ~6% edge means the appraiser is close to
break-even — defensible for a risk/reward mechanic where the *interesting* state is a genuine
toss-up, but thin enough that players may rationally skip it. Whether 6% is enough to carry a
signature mechanic is a design judgement, not a simulation result, and it should be settled
deliberately rather than by default.

> **Settled in R16–R18, and the answer was to change the estate rather than the number.**
> R16 tried to widen the margin by making scanning riskier and proved it cannot be done —
> the best available edge falls monotonically the harder you punish scanning, because you
> cannot raise a payoff by adding a cost (`DECISIONS.md` D-22). R17 went at the benefit side
> instead: scanning's payoff is `0.6 ×` the value *spread* of the room you're in, so making
> spread differ room to room turns one global answer into a per-room question. That takes the
> edge to **+8.8%**, and — because mean spread is pinned at 1.0 — without adding a dollar to
> the estate. See `LEVEL-SPEC.md` §2.1, V11, and D-23.
>
> R18 then corrected the baseline itself: the +6% above was computed with a cursed-cargo
> Disturbance floor of 2.0, an inert value this file's own §5 had already replaced with 7.0.
> **A flat estate is worth +4.2%, a V11 estate +8.8%**, and the lever is `room_spread`,
> not retrieval.

**The pillar works harder than designed.** Look at the Disturbance column, not the money: a
blind crew ends the night at 30 and is never hunted. A scanning crew is pinned at 100 for
most of the night. Appraising doesn't cost you *a bit* of noise — it moves you permanently
into COLLECT. "Information costs safety" turns out to be a much sharper trade than the design
claimed, which is good, and means it needs watching rather than strengthening.

### Two problems this exposed

**1. There is currently no decision to make.** At the designed retrieval rates, SCAN
dominates outright — always-scan is simply correct. The band where *selective* scanning wins
only appears when retrieval is ~3× harsher than specced (PURSUE 0.10 → 0.30 per trip). Either
raise retrieval toward that, or reduce candidates-per-shelf so max-of-N is a smaller prize.
Until one of those happens the appraiser is a mandatory chore rather than a judgement call.

**2. Cursed cargo is inert.** Sweeping 0 → 8 cursed items in the van moves earnings by under
$50 across every strategy. The +2 Disturbance floor per cursed item is swamped by ordinary
noise, so the entire van-cost half of the curse mechanic (`DESIGN.md` §4.2) currently does
nothing. It needs to be roughly 3–4× larger to be felt.

## 7. What would falsify this model

- **Crews clear night 1 without appraising anything.** The margin in §2 is wrong; cut van
  capacity before touching anything else.
- **Crews routinely fill the van and still miss quota.** Bands are too low, or trip times are
  optimistic. Check trip times first — they're the softest number here.
- **Nobody ever takes the apex.** Either the re-band in §3 is still too low, or the pinch-
  point risk is priced worse than it plays.
- **Everybody always takes the apex.** It's a trap in the other direction: the cart is
  supposed to be a genuine gamble, not a checklist item.
- **Pocket items dominate.** Their per-slot value has crept up to parity; drop their band, not
  their slot cost.

---

## 10. Which model said what — provenance, and what each one cannot see

**R24 found a FIRM decision (D-19, the master balance constant) resting on a figure from the
one simulation that four subsequent rounds of bug-fixes had invalidated.** It took eleven
rounds to notice, because nothing linked a claim to the code that produced it. This table
exists so that never costs eleven rounds again.

**The rule: quote a number with its model, or don't quote it.**

| Model | Round | Produces | Cannot see |
|---|---|---|---|
| `haul_sim.py` | R0 | *(superseded)* the +84% edge, §6's capacity sweep, the "24–32 slot cliff" | parallel efficiency (R7), slot accounting (R8), derived Disturbance (R5), the corrected cursed floor (R18) |
| `chain_sim.py` | R0, R26 | §4 quota curve, §8, D-21 apex, **the 20–24 extraction measurement that calibrated `PAR_EFF`**, and since R26 the quota curve with scanning paid for | *(R26 ported in Disturbance and retrieval; `noise=False` still reproduces the original exactly.)* A fair BLIND baseline — see the note below |
| `curator_attention.py` | R2 | attention model, hand-off, D-03 | the economy |
| `disturbance.py` | R3–R4 | the meter, decay 50/min, the ratcheting floor | the haul loop |
| `integrated.py` | R5, R8 | the appraiser's edge against *derived* noise | the apex; tier 4 does not exist in it |
| `curse_test.py` | R10–R11 | the curse value side, the ruin curve, D-23's predecessor | the apex |
| `appraiser_risk.py` | R16 | D-22 — cost levers cannot widen a thin edge | the apex |
| `appraiser_variance.py` | R17–R18, R24 | D-23 spread, the +8.8% edge, the 21-trip ceiling | the apex |
| `validate_estate.py` | R1, R19, R17 | the eleven geometry checks | anything about value over time |
| `check_drift.py` | R14, R18, R21, R23 | constant agreement, coverage, the C# backlog | whether the code is *correct* — only whether it agrees |

### The one that will mislead you

**The whole appraiser family — `integrated.py` and both `appraiser_*.py` — models tiers 1–3
and has no apex object in it at all.** `chain_sim.py` does, and the apex is one cart-class
prize worth $4,000–8,000 for five slots (D-21). That single omission has two consequences,
and both are easy to trip over:

1. **The absolute earnings are not comparable.** At 14 slots the appraiser family reports a
   blind crew earning **~$6,400**; `chain_sim` reports **$9,373** for night 1. Both are right
   about their own model. Only the second may be compared with a quota.
2. **Growth from van upgrades is overstated by the appraiser family.** Across the chain's
   14→19 slots it shows **+56%**, where `chain_sim` shows **+30%** — because the apex is a
   large *fixed-size* prize that does not scale with capacity, so it damps the proportional
   benefit of every extra slot. **The quota curve in §4 is calibrated on `chain_sim`, and
   that is the correct choice**; do not "correct" it toward the appraiser family's numbers.

### What R26 did *not* establish

`chain_sim` can now charge for scanning, so the obvious next question is what the appraiser
is worth **in a model that has the apex in it** — the appraiser family says +8.8%, and it
only ever modelled the within-shelf half of the mechanic, not the across-the-night
reservation price that `chain_sim`'s threshold policy runs on.

**That number is not yet trustworthy and is deliberately not quoted anywhere.** A blind crew
needs an estimate of value-per-slot to apply any reservation price at all, and the natural
one — the class-and-tier average, which D-10 says is legitimately legible — is *noiseless*.
That turns the threshold into a perfect class filter: mean earnings jump from $7,676 to
$12,371 across a single step of the pickiness parameter. A knife-edge is not a strategy, and
a blind crew that never misjudges is a strawman in the opposite direction from the one R5
warned about. **Give the blind estimate a per-item error before comparing anything to it.**

### The chain against the trip ceiling (R24/R25)

The van still binds on every night of the contract chain, but the margin closes steadily —
and by night 4 it is thin enough that any change to night length, crew size or parallel
efficiency would eliminate it:

| Night | Van | Margin over the 20.8-trip ceiling | Appraiser edge (V11 estate) | Binding |
|---:|---:|---:|---:|---|
| 1 | 14 | 49% | +8.8% | van |
| 2 | 15 | 39% | +16.3% | van |
| 3 | 17 | 22% | +13.8% | van |
| 4 | 19 | **9%** | +11.7% | van |

**The upgrade path stays inside the cliff, but only just.** §4's own recommendation — that
growth should come from richer estates rather than from squeezing the crew against a flat
ceiling — is the fix, and this table is the number that makes the case: a fifth night, or a
+2 slot buff, or a longer night, and the constraint the appraiser lives on is gone.
