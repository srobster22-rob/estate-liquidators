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

**Base van: 14 slots.** Shelving upgrades run **14 → 15 → 17 → 19** across a four-night chain
(§4; `sim/chain_sim.py` `VAN_BY_NIGHT`), hard ceiling **20**. The ceiling is
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
| **Reclamation** | the whole van, at `P = 0.015 × cursed^1.8` rolled at extraction — all or nothing, never a per-item charge |
| **Unstrapped cargo** | reclaimed at sunrise; shows as a loss, not an absence |
| **Medical** | none. Death costs a hauler, never money (`DECISIONS.md` D-11). |

The ledger fee is real, but it is **not** what makes cursed cargo a decision. A linear fee
cannot balance a multiplicative bonus: swept with the fee and the Disturbance floor both
active, TAKE-ALL still wins at ×6, ×4, ×3, ×2.5 and ×2.0, and refusing only becomes correct at
×1.5 where the "bonus" is already a penalty (`LOOP_LOG.md` R9/R10). What actually makes it a
decision is a **tail risk on the van**: at extraction, the collection reclaims the *entire* van
with

    P(ruin) = 0.015 × (cursed pieces aboard) ^ 1.8

counting tainted and malignant alike (`DESIGN.md` §4.2; `tuning.json` van.ruin_k /
van.ruin_exp; modelled in `sim/curse_test.py`). That super-linear shape produces an interior
optimum: two or three cursed pieces is the right play, worth **+7% over refusing cursed cargo
entirely**, while taking every one loses ~40% (`LOOP_LOG.md` R11). Malignant stays at ×6 — no
value retuning was needed once the cost shape was right. The 20% fee survives because the
ledger should say out loud that you paid something for the privilege, not because it balances
anything.

## 6. Simulation results

> ### ⚠️ Superseded by LOOP_LOG R8 — read §9.1 before using any number in this section
>
> The **+84%** appraiser edge below came from `sim/haul_sim.py`, which used a *placeholder*
> for the noise cost of scanning. R5 re-measured it against the real Disturbance model at
> **+31%**, and R8 — after fixing a slot-accounting bug that let lost cargo act as a free
> reroll — measured it at **+6%**. The capacity sweep's *shape* still stands and is still the
> basis for D-19: the edge decays monotonically as the van grows and reaches zero between 24
> and 32 slots. The *levels* in this table do not. Kept as the record of how the number moved.

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
> Disturbance. Results in §9 below, and corrected again in §9.1 — **the appraiser's edge is
> +6%, not +84% and not the +31% first written here.**

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

**D-10 survives, at less than half its previous margin** *(R5's conclusion, superseded — see
§9.1)*. The +84% from §6 was inflated ~2.7× by using a placeholder for noise cost. Scanning
still pays — by +31% as measured here, by **+6%** once R8 fixed the slot-accounting reroll.

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

**The pillar works harder than designed.** Look at the Disturbance column, not the money: a
blind crew ends the night at 30 and is never hunted. A scanning crew is pinned at 100 for
most of the night. Appraising doesn't cost you *a bit* of noise — it moves you permanently
into COLLECT. "Information costs safety" turns out to be a much sharper trade than the design
claimed, which is good, and means it needs watching rather than strengthening.

### What this exposed

**1. The decision exists after all — this was R5's bug talking.** At the designed retrieval
rates (PURSUE 0.10 / COLLECT 0.25, as shipped in `tuning.json`) ADAPTIVE beats both extremes:
$6,889 against BLIND's $6,497 and SCAN's $6,481. See the table above and LOOP_LOG R8. The
earlier claim here — that SCAN dominates outright and the band only opens at ~3× harsher
retrieval — was an artifact of the slot-accounting reroll, and it is withdrawn. **Do not retune
RETRIEVAL**; the designed values already produce the right ordering. What remains open is not
whether there is a decision but whether a **+6%** edge is a big enough one to carry the
signature mechanic — a design judgement, not a simulation result.

**2. Cursed cargo was inert, and the floor alone could not fix it.** At the originally specced
**+2/item** Disturbance floor, sweeping 0 → 8 cursed items in the van moved earnings by under
$50 across every strategy — the floor was swamped by ordinary noise. It is now **+7/item**
(`tuning.json` `disturbance.per_cursed_item_floor`; LOOP_LOG R9), which costs a crew carrying
six cursed pieces ~8.9% of earnings. But R9 and R10 also showed the van cost could never be
fixed from the floor at all: every curse cost was *linear* (flat fee, flat floor) while a
malignant item's benefit is *multiplicative* at ×6 (×4.8 after the 20% fee in §5), and taking
every cursed item stayed correct down to ×2.0. R11 therefore replaced the van cost with a
super-linear tail risk — `P(ruin) = 0.015 × cursed^1.8`, evaluated at extraction
(`DESIGN.md` §4.2, `sim/curse_test.py`) — which finally produces an interior optimum: take two
or three cursed pieces, then refuse.

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
