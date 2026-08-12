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
| **Lever charge** | **1** | salt, a spare fuse. Bought between nights, spent in a panic. |

> **The charge row is the price of safety, and it is deliberately paid in cargo** (`DESIGN.md`
> §6.5.1, `DECISIONS.md` D-28). Priced in *time* instead, the Disturbance levers are dominated
> — a crew that does the arithmetic never pulls one, because throughput and cargo are the same
> currency and retrieval only takes a fraction of what you carry. In slots there's an interior
> optimum: one charge is +2.6%, two break even, six is −22%.

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
| **4** | **apex (cart)** | **$6,000 – 11,000** | **$1,200 – 2,200** |

### The apex bug this arithmetic caught

`LEVEL-SPEC.md` originally banded the apex object at **$1,500–3,000**. At 5 slots that's
$300–600 per slot — *worse than a tier-2 armful*. The single most dangerous object in the
house, the one the whole night is supposed to build toward, was mathematically a trap. Any
player who did this arithmetic once would have correctly ignored it forever, and the estate's
authored centrepiece would have become a joke.

Re-banded to **$4,000–8,000**… and then again to **$6,000–11,000** in R20, because the first
re-band was measured on a model that ended the night when the van filled. Once the crew keeps
working and *upgrades* — which is what really happens — the apex has to beat not the five items
it displaces but **everything those five slots would have become by sunrise**. Measured: five
marginal slots are worth ~$3,418 (~$684/slot), and the apex also costs a large labour block, so
at $4,000–8,000 it came out at **−3.8%** — a trap again, for the second time. At $6,000–11,000
it is **+9.1%**: worth taking, and cheap enough to skip on a bad night. `LEVEL-SPEC.md` §2
matches.

> **Three settings of one band, each overturned by a model correction rather than by taste.**
> That is the cost of tuning against simulations, and it is still cheaper than finding out in
> a playtest. What has never moved is the *rule*: the apex must clear five slots' marginal
> value plus its labour, or it is a decoration players correctly ignore.

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

**Calibrated curve.** A crew earns **$18,067 / $18,676 / $19,880 / $21,208** across the four
nights — only **+17% growth**, because van capacity rises just 14→19 and the estates are
equally rich every night. The quota has to live inside that range or the chain has no shape,
and the narrowness of the range is exactly why the quota steps are small.

| Night | Quota | Van | Sim mean | Pass rate | Feel |
|---:|---:|---:|---:|---:|---|
| 1 | **$15,250** | 14 | $18,067 | 96% | you can be a coward and survive |
| 2 | **$17,500** | 15 | $18,676 | 73% | tier 2 is now mandatory |
| 3 | **$19,500** | 17 | $19,880 | 59% | someone has to go into a sealed wing |
| 4 | **$21,750** | 19 | $21,208 | 38% | above the mean. The apex is not optional. |

> **Recalibrated in R20, and the previous curve ($7,500 / $9,000 / $10,750 / $12,500) is dead.**
> It was measured on a model that **ended the night when the van filled**. Real crews don't
> leave — the van binds by ~40%, so the back half of a night is spent swapping a better thing
> for a worse one, which is worth about **+42%**. Under the old quotas every night passed 100%:
> the exact shapelessness this section was written to fix, reintroduced by a modelling
> assumption nobody had questioned.
>
> **Recalibrated once more in R21**, because R20 set the quota curve *before* re-banding the
> apex and left it stale against its own final configuration by the end of the round. Caught
> within minutes by `chain_sim.py` now printing measured pass rates beside their calibration
> targets — the fix for a class of error this project keeps making, which is not getting a
> number wrong but failing to notice when a later change invalidates an earlier one.

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

> **Settled in R16, and the answer was that the question was wrong — see §10.** The +6% was
> also slightly overstated: this model carried a stale cursed-Disturbance floor of 2.0 after
> R11 raised the canonical value to 7.0, which puts the corrected figure at **+4.4%**. With
> room value classes in place the appraiser earns **+12.2%**.

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

## 10. The appraiser, settled — the payoff is a room property (R16)

`sim/scan_risk.py`. §9 left the project with a genuine open question: is a **+6%** edge
enough to carry the game's signature verb, or will good players rationally skip it? Two
hypotheses were tested. The first is dead and the second answers the question.

### Hypothesis 1 — make scanning a tail risk. Dead.

§5 fixed cursed cargo by replacing a linear cost with a super-linear one. The appraiser looked
like the same problem, so it got the same treatment: `p(the Curator arrives mid-scan) = k ×
consecutive_scans^1.8 × tier_weight`, with death — and a permanently smaller crew, which slows
Disturbance decay because decay is crew-scaled — if it arrives while hunting.

| k | BLIND | burst 1 | burst 2 | burst 3 | scan all | best |
|---:|---:|---:|---:|---:|---:|---|
| 0.00 | 6,454 | 6,533 | 6,331 | 6,296 | 6,433 | (within noise) |
| 0.02 | 6,454 | 6,442 | 6,044 | 5,782 | 4,882 | BLIND |
| 0.05 | 6,454 | 6,296 | 5,535 | 4,693 | 4,144 | BLIND |
| 0.12 | 6,454 | 5,962 | 3,927 | 3,243 | 3,057 | BLIND |
| 0.20 | 6,454 | 5,473 | 2,825 | 2,556 | 2,448 | BLIND |

No burst length wins at any coefficient. **The lesson this project has leaned on twice needs a
qualifier:** cost *shape* decides whether an interior optimum can exist; the *size of the
benefit* decides whether it does. Cursed cargo pays ×6 and so survives a few ruin rolls;
scanning pays ×1.35 and survives none. Logged as D-23.

### Hypothesis 2 — the payoff varies by room. This is the answer.

Scanning four candidates and keeping the best is worth `E[max of 4] − E[random]` =
**0.6 × spread × room mean**. Every model in this project drew all four from one flat band,
which prices the appraiser as a single global constant — a fixed rate of return, which is not
a decision at any price. Give rooms a declared value class instead (`LEVEL-SPEC.md` §2.1):

| Policy | Mean $ | Scans | End Disturbance | vs blind |
|---|---:|---:|---:|---:|
| Blind haul | 10,625 | 0 | 59 | — |
| Scan a **random** 25% of rooms | 10,865 | 20 | 70 | +2.3% |
| Scan **shelf** rooms only | 10,136 | 24 | 73 | **−4.6%** |
| Scan **curio** rooms only | **11,557** | 20 | 69 | **+8.8%** |
| Scan curio + mixed | 10,275 | 53 | 93 | **−3.3%** |
| Scan everything | 9,899 | 76 | 100 | **−6.8%** |

> **Re-measured in R20 with the swap phase in** (the figures above). The first cut of this
> table read +12.2% / +5.9% / +2.4% for the last three rows, measured on nights that ended
> when the van filled. **The ordering survives and the conclusion gets sharper:** scanning
> curio rooms is still clearly best, the skill gap over random-25% is now ~72% of the total
> edge rather than 60%, and — the real change — **scanning more broadly is now actively
> harmful.** Curio+mixed and scan-everything have gone from mildly positive to −3.3% and
> −6.8%. Selectivity is no longer just the best play, it is the only profitable one.

Three things in that table matter more than the headline:

1. **Random-25% vs curio-only is the skill component.** Same scan count, same noise, same
   losses — +4.6% against +12.2%. About 60% of the edge is *reading the room*, and the rest is
   simply scanning less. Both are new; only the first is interesting.
2. **Shelf-only is negative.** Reading the room wrong is worse than never scanning. The
   decision now has a wrong answer, which is what makes it a decision.
3. **Scan-everything nearly gives it all back** (+2.4%), because it pins Disturbance at 100.
   "Information costs safety" is doing exactly the work §9 said it was.

**Sensitivity.** The result is not perched on the tuning. Curio spread 0.7 → 1.9 moves the
edge 7.0% → 20.3% and curio-only wins throughout; curio share 10% → 40% moves it 6.2% → 16.7%
and curio-only wins throughout. The mechanic degrades gracefully in both directions and never
inverts. What it cannot survive is a house with *no* variance — which is why V11 exists.

**Van capacity remains the master constant.** Nothing here changes §6: this widens the
appraiser's payoff, it does not replace the scarcity that makes selection matter at all.
