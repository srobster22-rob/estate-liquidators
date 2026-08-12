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

> **R32 — Finding 3's *direction* survives; its *shape* does not, and the shape was the
> argument.** Re-run against the current model (noise, curses, rooms), earnings still rise
> monotonically with crew — but crew 6 earns **2.05×** crew 4 rather than +12%. The cause is
> not noise or curses: it is that **`chain_sim` divides labour by crew linearly**, so six
> people do exactly 1.5× the work of four. Sweeping the parallelism exponent moves the same
> comparison from 2.05× (`crew`) to 1.52× (`crew^0.85`) to 1.17× (`crew^0.75`).
>
> So the number is unknown, and everything downstream of it is a guess about an unmeasured
> exponent. `PARALLEL_EFFICIENCY = 0.65` does not help — it is a *level* correction
> (`crew × 0.65`), still linear in crew, and the appraiser sims never sweep crew size so it
> never mattered there. **The project has no sublinear parallelism model anywhere.**
>
> **R33 built the parallelism model and then found it was not the cause.** `tuning.json` now
> carries `labour.parallel_exponent` (default 0.75, **unmeasured**) and `chain_sim` uses
> `effort(crew) = 4 × (crew/4)^a`, anchored so nothing about the four-player results moves.
> R32's exponent sweep had conflated *level* with *scaling* — it changed crew 4's throughput
> as well as the ratio — and with the level anchored the whole plausible range of exponents
> moves crew 6 ÷ crew 4 only from **1.43× (a = 0.30) to 2.03× (a = 1.00)**. No parallelism
> assumption recovers +12%.
>
> **Isolated properly, one variable at a time, with every policy switch held fixed:**
>
> | | crew 4 | crew 6 | ratio |
> |---|---:|---:|---:|
> | no noise, no curses | $10,986 | $15,867 | **1.44×** |
> | + noise | $10,458 | $15,882 | 1.52× |
> | + curses | $11,351 | $21,608 | **1.90×** |
> | + curses, crew never appraises | $11,502 | $19,553 | 1.70× |
>
> **The base advantage is 1.44× before noise or curses exist at all**, noise contributes
> almost nothing (+0.08), and the **curse tail is the single largest amplifier** (+0.38). The
> mechanism is simple and probably real rather than artefactual: with a reservation-price
> policy, extra search time converts directly into higher value *per slot*, and the van caps
> quantity but not quality — so headcount buys quality without limit, and a heavy-tailed value
> distribution (×2.5, ×6) pays for selectivity twice over.
>
> **So the gap between §8's +12% and today's 1.44× is the decision rule, not information,
> noise, curses or parallelism.** §8 ran the old value-threshold rule on a per-slot metric;
> R27 replaced both for reasons unrelated to crew size. The current model is the better one
> and it says the economy prefers six people by a lot.
>
> This is the third settled conclusion found resting on a model that changed underneath it
> (after D-19 in R24 and the appraiser denominator in R27). **Measure the exponent in the
> first playtest that has six people in it** — it will not rescue crew 4, but it is the only
> number here that is currently a pure guess.

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

### R27 — the denominator, and why the two model families never actually disagreed

**The appraiser's edge has been quoted against the wrong denominator for nine rounds.**

`appraiser_variance.py` reports **+8.8%**, and that is correct — *for the loot a crew actually
chooses between*. `chain_sim.py` contains the apex, and the apex is **62% of a night's take**
($6,000 of $9,700), is taken on 100% of nights (D-21), and **cannot be improved by appraising
anything**: it is one authored object whose price everybody already knows.

So the same benefit, expressed against a night's total:

```
  +8.8% of the $3,700 selectable portion  =  +$326
  +$326 against a $9,700 night            =  +3.4%
  minus three stationary seconds per shelf =  roughly zero
```

Measured directly, with the decision rule held fixed and *only* the information varying, the
appraiser's value-revealing function is worth **−0.4% / −1.2% / −3.2% / −3.0%** across the four
nights of the chain. **The two models never disagreed. They were answering different questions,
and the docs were quoting the one that flatters the mechanic against a quota measured in the
other.**

**This matters because the quota is a night total.** An appraiser worth +8.8% of selectable
loot contributes ~3% toward clearing quota, not ~9%.

**Three things this does *not* say.** (1) It is not a verdict on the appraiser, which reveals
**curse grade as well as value** — and `chain_sim` has no curses in it at all, so the half R11
valued at +7% is entirely outside this measurement. (2) It is not an argument to cut the apex;
D-21 is settled and the apex earns its place on drama and on economics both. (3) It is
sensitive to the apex band — shrink the apex and the denominator effect shrinks with it.

**What it does say** is that `DESIGN.md` §4.4's load-bearing assumption deserves re-reading:
most of the selection value in this economy is available from **category alone**, for free,
and the appraiser's value half is buying a thin slice on top of that. The mechanic's real
defence is the curse grade, not the price.

### R28 — the appraiser decays across the upgrade path, and goes negative by night 3

R27 argued the mechanic's real defence must be the **curse grade** rather than the price, since
R11 valued the curse decision at +7% and a blind crew cannot even express it — "take two or
three and then refuse" requires knowing which ones they are. R28 put curses into `chain_sim`,
so for the first time the apex, the classes, the noise **and** the curse are in one model.

**It is not the rescue R27 expected.** Measured with the scanning crew free to choose its own
cursed cap, and both crews on the same decision rule:

| Night | Van | Best SCAN | BLIND | Edge | Scan end-Disturbance | Cargo lost |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 14 | $12,456 | $11,360 | **+9.6%** | 98 | 0.3 |
| 2 | 15 | $12,171 | $11,417 | **+6.6%** | 99 | 0.4 |
| 3 | 17 | $11,322 | $11,529 | **−1.8%** | 99 | 0.8 |
| 4 | 19 | $10,718 | $11,730 | **−8.6%** | 100 | 1.5 |

**The appraiser is strongly worth using on night 1 and actively harmful by night 3.** The
mechanic does not merely fail to grow with the crew — it inverts, exactly as they progress.
This is `DESIGN.md` §4.4's nightmare arriving from a direction nobody was watching: not
players tiring of the appraiser, but players being *correct* to abandon it.

**The mechanism is noise, and the duration test proves it.** Cutting appraise time from 3.0s
to 1.0s changes nothing (edges stay ≈ +9 / +5 / +1 / −9). What moves is Disturbance: a
scanning crew sits pinned at **98–100 — COLLECT — all night**, while a blind crew sits at
**46–57 — PATROL**. A bigger van means more shelves, more pings, more of the night in the state
where the Curator takes your cargo: retrieval losses climb 0.3 → 1.5 items across the chain
while the blind crew loses 0.1.

> **This independently re-confirms D-10's second bullet from a model that shares none of
> `haul_sim`'s bugs.** "Scan duration is not the cost; noise has to carry the whole cost" was
> a superseded-source claim (§10) and it has now survived re-derivation. It is one of the few
> things in this document that has.

**And it compounds, which is the part worth designing around.** A scanning crew seeks value;
cursed items *are* the value (×2.5 and ×6); every cursed piece aboard lifts the Disturbance
floor another 7 points (R9/R18). So the appraiser's own success makes the rest of its night
more dangerous — scan → find the good thing → the good thing is cursed → the floor rises →
more retrieval → scan again to compensate. A blind crew never enters that loop because it
never chases the multiplier.

**Three candidate fixes, none yet tested.** (1) **Selective scanning** — R17 established that
scanning *some* rooms is the good policy, and `chain_sim` has no rooms, so it can only express
"appraise every shelf" or "appraise none". That binary is the same framing R6 and R16 both
found hides the interesting middle, and it is the most likely resolution. (2) **An appraiser
upgrade path** — the crew upgrades the van across a chain; if the tool does not get quieter,
the mechanic decays by construction. (3) **Don't grow the van**, which D-19 already half-argues
on other grounds (R24).

### R29 — selective scanning rescues the appraiser, and the optimum tightens as you upgrade

Every model in this project had been partial in a way that mattered, and §10 above records
which. `appraiser_variance` had **rooms and spread** but no apex, no classes, no curses.
`chain_sim` had **the apex, classes, curses and noise** but no rooms — so it could only ever
ask *"appraise every shelf, or none"*, which is the exact binary framing R6, R16 and R28 each
independently found hides the answer. R29 merged them.

| Night | Van | BLIND | Scan **all** rooms | vs | Scan **selectively** | vs | Which rooms |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 14 | $11,381 | $12,232 | +7.5% | **$12,334** | **+8.4%** | curio + mixed |
| 2 | 15 | $11,444 | $12,040 | +5.2% | **$12,333** | **+7.8%** | curio + mixed |
| 3 | 17 | $11,578 | $11,454 | **−1.1%** | **$11,904** | **+2.8%** | curio only |
| 4 | 19 | $11,534 | $10,744 | **−6.8%** | **$11,882** | **+3.0%** | curio only |

**Two results, and the second one is the better game.**

**1. The R28 inversion was an artifact of the all-or-nothing policy, not a property of the
appraiser.** Scanning everything still decays and still goes negative by night 4 — that column
reproduces R28 in a model that now has rooms in it. Scanning *selectively* stays positive on
every night of the chain. The mechanic was never broken; the only policy the model could
express was.

**2. The optimal selectivity tightens as the crew upgrades — and that is a skill curve, not a
balance problem.** Two room classes are worth stopping for on nights 1–2; by night 3 only the
curio rooms are. It falls straight out of R28's mechanism: a bigger van means more shelves,
scanning pins Disturbance at COLLECT, so as capacity grows the crew must spend its noise
budget more carefully. **The right play changes as you progress**, which is what a mechanic
with a ceiling is supposed to do, and it is the first thing in this economy that gets
*harder to play well* rather than merely harder.

> Figures at n = 2,500–3,000 per cell, each policy at its own best pickiness and cursed cap.
> `python sim/chain_sim.py` runs the same comparison at n=900, which reproduces the ordering
> and the sign of every cell. The spread mix and factors are V11's (`LEVEL-SPEC.md` §2.1),
> mean exactly 1.0, so a room-bearing estate holds no more money than a flat one — only a
> decision.

**This closes the thread R9 opened.** The question "is the appraiser's edge enough to carry the
game's signature mechanic" has been asked for twenty rounds against four different models and
three different denominators. The answer: **yes, at +3% to +8% depending on the night, but
only for a crew that chooses which rooms to stop in** — and every model that reported otherwise
was one that could not express choosing.

### R34 — the estate is infinite in every model, and its size is an unspecified balance constant

Every model in this project draws candidates from an **infinite shelf**: each encounter
generates four fresh objects forever, so a crew that searches twice as fast simply sees twice
as much house and nothing ever runs out. That is why headcount scaled without limit (R33).

A real estate does not work that way. `LEVEL-SPEC.md` §1 is CORE + 3–5 WINGS at ~5 plinths
each, so an estate holds roughly **25–30 takeable objects**; `proto/index.html` ships 29. But
**that number is never stated as a constraint, has no rationale attached, and is in no
document as a tuning value** — and it turns out to control two of the project's open questions
at once, in opposite directions:

| Objects | Estate ÷ van | Appraiser edge | Crew 6 ÷ crew 4 |
|---:|---:|---:|---:|
| 20 | 1.1 | **+15.0%** | **1.07×** |
| 28 (as specced) | 1.5 | +13.2% | 1.18× |
| 40 | 2.1 | +5.9% | 1.54× |
| 60 | 3.2 | −6.2% | 1.68× |
| 80 | 4.2 | **−11.0%** | **1.90×** |

**A tight estate makes crew size nearly irrelevant and the appraiser strongly worth using; a
loose one does the reverse.** At the specced ~28 objects both sit in a good place — crew 6
only 1.18× crew 4, appraiser +13.2% — which is a much better answer to R33's crew problem than
any of the fixes that were on the table.

> **Do not act on the appraiser column yet.** Its direction **contradicts §4.4's Requirement
> A**, which says van space must bind and the crew must leave behind more than half of what
> they could carry — this says the appraiser does *better* when the estate is tight. That may
> be real (with a small estate, the order you take things in matters more than the set you
> take) or it may be an artifact. **It is one model, one round old, and R34 already found one
> bug in it** — an early `break` when tiers 1–3 were picked clean, which dropped the apex take
> rate to 1% at some estate sizes and 100% at others and made blind earnings non-monotone in
> estate size. That anomaly is what caught it. Verify the appraiser column against an
> independent route before touching §4.4.

**What is safe to act on now:** put the object count in `LEVEL-SPEC.md` as an explicit
authored constant with its rationale, because right now it is an accident of how many plinths
an author happens to place, and it is doing more balance work than several constants that have
their own decision entries.

### What R26 did *not* establish

`chain_sim` can now charge for scanning, so the obvious next question is what the appraiser
is worth **in a model that has the apex in it** — the appraiser family says +8.8%, and it
only ever modelled the within-shelf half of the mechanic, not the across-the-night
reservation price that `chain_sim`'s threshold policy runs on.

**R27 resolved this, and the knife-edge turned out not to be about estimate error at all.**
The two crews were using *different decision rules* — the blind one filtering on class, the
scanning one on value — and the gap between the rules was being read as the appraiser's worth.
It was not. **"Refuse pockets" is worth +45%, and it is a class-level policy that no threshold
on value-per-slot can express**, because pocket and armful per-slot distributions almost
entirely overlap. (A pocket costs half a slot and a *whole trip*; when trips bind, per-slot
ranking systematically overvalues small objects — hence `metric="per_trip"`.) Hold the rule
fixed with `rule="class"` and the comparison becomes clean; see the denominator section above.

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
