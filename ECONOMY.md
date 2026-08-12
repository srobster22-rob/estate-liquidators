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

### Curses ride only on what one person can carry

**Pocket and armful items may be cursed. Two-man, cart and apex pieces never are.**

R30 put ECONOMY's weight classes into the model that drives the design — everything had been
one slot since R5 — and the jackpot appeared immediately. A malignant tier-3 two-man piece is
**$24,000 against a night-4 quota of $10,250**: one object, two people, three slots, and the
contract is met twice over. That is D-28's apex hole one tier down, and nobody had noticed it
because no model had weight classes and curses at the same time.

Left open, it does not merely inflate earnings, it deletes the loop. The optimal policy stops
having an interior optimum: refusing almost everything and waiting for a jackpot pays better
at every bar we tested, up to refusing 90% of what the crew finds. Slots used falls to **7.6
of 14** — the van stops binding, which is the single constraint this entire economy is built
on (see the box at the top of this document).

| Bar | Curses anywhere | Curses on light items only |
|---|---:|---:|
| BLIND | $8,047 | $6,424 |
| MARGIN_30 | $9,674 | $7,855 |
| **MARGIN_50** | $10,872 | **$7,874** |
| MARGIN_80 | $11,714 | $5,280 |
| MARGIN_120 | $12,053 | $5,015 |
| MARGIN_200 | **$12,424** | $5,025 |

Restrict curses to what a single player can carry and the shape comes back: the bar peaks
around the 30th–50th percentile and over-selectivity costs **36%**.

It is also the better fiction. Every curse effect in `DESIGN.md` §4.2 is intimate — it pulses
*your* flashlight, gains mass in *your* hands, speaks in *your teammate's* voice. Those belong
to a thing one person is holding. A haunted wardrobe carried by two people at either end was
never that image, and the heavy classes keep the job they are better at: logistics.

**One modelling note that generalises.** With weight classes, the marginal rule must price a
**slot**, not an item — a two-man piece worth twice an armful at three times the slots is a
worse buy, and only a per-slot comparison sees it.

### The apex is always CLEAN, and that had never been written down

Nothing in `LEVEL-SPEC.md` or this document said whether the apex object can carry a curse
grade. R28 priced the silence, on night 4 (van 19, quota $10,250):

| Apex policy | Night's earnings | Of which the apex | Vans lost |
|---|---:|---:|---:|
| skip it | $10,340 | — | 31% |
| **take it, always clean** | **$12,260** | $5,998 | 23% |
| take it, grade rolled like anything else | $13,840 | **$10,178** | 26% |

**Taking it is worth +19%**, which settles D-21 against the *current* economy rather than
against the pre-curse `chain_sim` that first established it. Reserving five slots for a single
object is correct.

**Letting it roll a grade is worth another +13%, and would ruin the game.** One object becomes
70% of a night's income, decided by a hidden coin flip at spawn. A malignant apex is worth
$24,000–48,000 against a $10,250 quota — it clears the night four times over, so nothing else
a crew does that night matters. Every decision the economy is built out of gets flattened by
one lottery ticket.

Making it *visibly* malignant does not save it either: at four times the quota it is an
auto-take, so it is not a decision, just a bigger number.

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

**Calibrated curve — recalibrated in R26**, because the previous one was fitted before curses
entered the earnings model and the economy has moved three times since. Against it, the best
policy passed night 1 only **69%** of the time and completed the chain 14%; the "you can be a
coward and survive" night was failing a third of the time. Canonical in `tuning.json`
(`progression`); reproduce with `python3 sim/integrated.py`.

| Night | Quota | Van | Careful crew passes | Greedy crew passes | Feel |
|---:|---:|---:|---:|---:|---|
| 1 | $5,750 | 14 | **87%** | 73% | you can be a coward and survive — and it is the *better* play |
| 2 | $7,250 | 15 | 61% | 70% | caution starts costing more than it saves |
| 3 | $8,750 | 17 | 34% | 67% | the sealed wing, and the first cursed piece you actually want |
| 4 | $10,250 | 19 | 10% | 64% | greed is no longer optional |
| | | | chain **2%** | chain **22%** | switch postures once and it is **26%** |

**Three things this measurement found.**

**1. The ruin lottery is a ceiling, and nobody had noticed.** A crew that takes cursed cargo
loses the entire van about a quarter of the time, so **it cannot pass more than ~74% of nights
at any quota at all** — set night 1 to a dollar and it still fails 26% of the time. The 95%
pass rate the old curve aimed at was never reachable by a greedy crew. It is reachable by a
careful one, which is what makes the arc work.

**2. The optimal risk posture inverts across the chain**, and that is the shape the design
wanted without ever having stated it. On night 1 caution beats greed (87% against 73%),
because the quota is low enough that gambling only adds a way to lose. By night 3 caution is
losing two nights in three. A crew that plays safe once and then commits completes the chain
**26%** of the time, beating both pure strategies — the arc is a decision, not a difficulty
ramp.

**3. Shelving upgrades are worthless to a careful crew.** Their earnings move $7,594 → $7,969
across vans 14→19 — **+5%** — because refusing roughly a third of what they find makes them
time-bound rather than slot-bound, so the extra shelves stay empty. The upgrade that is
supposed to be the progression reward only pays the crew already gambling. Worth fixing before
Phase 4 ships a shop: the careful path needs a reward denominated in *time* or *routes*, not
in slots.

## 4.1 The upgrade path — what each posture is allowed to buy

R26 found shelving is worthless to a careful crew (+5% across vans 14→19). R27 asked what
would not be. Each row is 1,200 nights per posture, `python3 sim/integrated.py`:

| Upgrade | Careful | Greedy | Cursed aboard | Vans lost |
|---|---:|---:|---:|---:|
| none (van 14) | $7,597 | $8,354 | 4.8 | 27% |
| shelves → van 16 | +4% | +8% | | |
| shelves → van 19 | +5% | **+22%** | | |
| **van parked closer** (−12% trip time) | **+7.5%** | +0.7% | | |
| appraiser mk2 (1.5s scans) | +0.6% | +3% | | |
| muffled appraiser (L48 → 30) | +1.5% | +0.5% | | |
| warded crate — 1 piece exempt | +0% | +10% | 4.9 | 19% |
| warded crate — 2 pieces exempt | +0% | +16% | 5.0 | 14% |
| gentler curve — ruin exp 1.8 → 1.5 | +0% | +14% | **5.3** | 18% |

**Time is the careful crew's only upgrade, and shelves are the greedy crew's.** They are near
perfect complements: −12% trip time is worth +7.5% to a crew that refuses curses and nothing
at all (+0.7%) to one that doesn't; the van-19 shelving is the exact reverse. That gives the
shop two axes that *mean* something — buying one tells the crew what kind of crew to be, which
is a better shop than "+2 slots, again".

**And a rule for anything that touches the curse curve.** A ward that *exempts pieces* makes
the crew safer: two free pieces cut vans lost from 27% to 14% and the crew still carries five.
A ward that *gentles the exponent* makes the crew **braver** for the same money — 5.3 cursed
pieces aboard, still losing 18% of its vans, for +14%. Same price, opposite feeling. Buy the
exponent down, never buy pieces out: an upgrade should move the greed slider, not remove it.
Exemption also re-flattens the cost curve R10/R11 spent two rounds proving has to be
super-linear.

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

Re-measured in R17 with the canonical +7 cursed floor — this table was previously computed
with a hardcoded +2 that had been stale since R9. Reproduce with `python3 sim/integrated.py`.

| PURSUE / COLLECT | BLIND | ADAPTIVE | SCAN | Best |
|---|---:|---:|---:|---|
| 0.00 / 0.00 | $6,523 | $7,776 | $8,302 | SCAN |
| 0.05 / 0.12 | $6,484 | $7,269 | $7,356 | SCAN |
| **0.10 / 0.25** ← as designed | **$6,434** | **$6,717** | $6,409 | **ADAPTIVE** |
| 0.20 / 0.50 | $6,342 | $5,684 | $4,556 | BLIND |
| 0.30 / 0.70 | $6,264 | $4,601 | $2,714 | BLIND |

**Two prior conclusions were wrong, both caused by the same bug:**

- §9 claimed *always-scan dominates and there is no decision to make*. False. At the
  **already-designed** retrieval rates, **selective scanning is the optimal policy** — ADAPTIVE
  beats both extremes. No retuning of RETRIEVAL is needed.
- LOOP_LOG R6 argued no middle strategy could ever have a wide optimum, since ADAPTIVE is a
  linear interpolation between two extremes. That pessimism was itself an artifact. The band
  exists, and the design already sits in it.

**But the margin is small: +4.4% over blind hauling** — the fourth value this number has had,
after +84% (placeholder noise cost), +31% (slot-accounting bug) and +6% (stale cursed floor).
Each retraction came from finding an instrumentation error, never from a design change, and
each one moved in the same direction. That is the number to argue about now. A ~4% edge means
the appraiser is close to break-even — defensible for a risk/reward mechanic where the
*interesting* state is a genuine toss-up, but thin enough that players may rationally skip it.
Whether it is enough to carry a signature mechanic is a design judgement, not a simulation
result, and it should be settled deliberately rather than by default.

## 10.1 R18 — the policy space was missing a verb

Everything above asks "do you scan?" and lets the crew pick only between items it was already
going to take. Give it the move the mechanic actually implies — **appraise, refuse, walk away
with the slot unspent** — and the numbers change character. `SKIP_p` refuses anything below
the p-th percentile of the tier band; the trip is spent either way, so this is a real cost and
not the free reroll that corrupted R6–R7.

| Policy | mean $ | scans | slots used | trips | out of time | vs BLIND |
|---|---:|---:|---:|---:|---:|---:|
| BLIND | $6,434 | 0 | 14.0 | 14.0 | 0% | — |
| CAP_2 — scan two, take better | $6,742 | 28 | 14.0 | 14.0 | 0% | +4.8% |
| ADAPTIVE | $6,717 | 28 | 14.0 | 14.0 | 0% | +4.4% |
| SCAN everything | $6,409 | 56 | 14.0 | 14.0 | 0% | −0.4% |
| THRESH_50 — stop at good enough | $7,159 | 26 | 14.0 | 14.0 | 0% | +11.3% |
| SKIP_50 — refuse below median | $7,707 | 28 | 14.0 | 14.9 | 0% | **+19.8%** |
| **SKIP_70** | **$8,025** | 45 | 13.1 | 17.3 | 45% | **+24.7%** |
| SKIP_85 — too picky | $5,427 | 61 | 8.6 | 18.0 | 99% | **−15.6%** |

**The binding constraint switches**, which is what makes the optimum interior. Up to the 50th
percentile the van fills every night and refusing junk is nearly free. Past it the clock takes
over: SKIP_85 ends 99% of nights out of time with 8.6 of 14 slots still empty. Being too
choosy costs more than never choosing at all.

**And a tail-risk scan cost regulates the bar rather than the verb.** Modelling "caught
mid-scan", compounding as `k × n^1.8 × tier alertness`, leaves BLIND flat and lowers every
scanning policy monotonically — the sanity check R6–R8 kept failing. What it changes is
*where* the optimum sits: the 70th percentile is right in a quiet house, the 50th once
scanning is genuinely dangerous. So the tail risk is worth having, but it is not what creates
the decision; the refusal verb is.

## 10.2 R22 — the two decisions were never independent

R11 measured the curse decision with the appraiser absent. R18 measured the appraiser with the
cursed count held constant. In one model:

| Policy | cap | mean $ | cursed aboard | van lost | slots used |
|---|---:|---:|---:|---:|---:|
| BLIND | none | $7,701 | 4.1 | 21% | 14.0 |
| BLIND | 5 | $7,810 | 3.8 | 18% | 14.0 |
| SKIP_50 — refuse below median | 5 | $7,687 | 4.8 | 24% | 13.8 |
| SKIP_70 — refuse below 70th | none | $5,423 | **7.4** | **57%** | 14.0 |
| SCAN — always take the best | 5 | $4,960 | 5.0 | 27% | 12.1 |
| MARGIN_20 | none | $8,510 | 4.4 | 22% | 13.9 |
| **MARGIN_30** | **none** | **$8,563** | 4.8 | 25% | 13.7 |
| MARGIN_40 | none | $8,364 | 5.0 | 29% | 13.2 |
| MARGIN_30 | 3 | $7,983 | 2.9 | 11% | 13.6 |

**Sticker-price greed is curse greed.** A curse is worth ×6, so the curses *are* the valuable
items; a crew that raises its value bar raises its cursed intake without deciding to. SKIP_70
ends the night with 7.4 cursed pieces and loses the whole van 57% of the time — an outcome it
never chose.

**Judging on the margin replaces the cap.** MARGIN_p asks what an item *adds* — value net of
fee, discounted by the ruin it raises, minus the ruin it adds to everything already aboard —
and beats every capped policy without a cap. Capping it at three costs 7%. One rule instead of
two, and the rule is a judgement rather than a count.

**The appraiser's edge is +10% here**, down from R18's +25%, because that was measured in a
curse-free world. The bar also moves: about the **20–30th percentile** of the band on marginal
value, not the 50–70th on sticker value. Every widening of this model has lowered the
appraiser's headline number and strengthened the reason to have one — it is the only way to
run the marginal rule at all.

## 10.3 R25 — the same claims, measured in the game instead of in Python

`tools/play_night.mjs` drives `proto3d` itself — real loop, real clock, real Curator, real
three-second scans — under each policy, 30 seeded nights each. The bot walks the room graph
through doorway centres at the game's own speeds; it does not solve collision, so it cannot
catch a movement bug, but everything downstream of movement is the real implementation.

| Policy | net $ | items | cursed | nights ruined | appraised | refused |
|---|---:|---:|---:|---:|---:|---:|
| BLIND | $3,317 | 14.0 | 4.3 | 27% | 0 | 0 |
| VALUE_70 — sticker price | $5,223 | 11.0 | **6.5** | **53%** | 23.1 | 11.7 |
| MARGIN_30 | $5,622 | 12.6 | 4.8 | 37% | 21.7 | 8.8 |
| **MARGIN_50** | **$6,638** | 10.2 | 4.9 | 27% | 25.0 | 14.6 |

**R22's failure mode reproduces in the implementation.** VALUE_70 — the policy that judges by
sticker price — accumulates the most cursed cargo of any policy and **loses the van on more
than half its nights**, exactly as the Python model predicted and for the same reason: the
curses are the valuable items. Judging on the margin carries the same amount of cursed cargo
as hauling blind while banking twice as much.

**What does not transfer, and why.** The prototype is one player, a 210-second night and seven
rooms; `integrated.py` is four players, 720 seconds and a depth-gated estate. In the prototype
the van is easy to fill, so blind hauling has no scarcity to exploit and does far worse than in
the model. The *orderings* are what carry: margin beats sticker price, sticker price is a curse
magnet, and appraising pays. Do not port a dollar figure from this table into a spec.

**Sample size is 30 nights per policy** and ruin is a coin flip with p≈0.3, so the ruin column
carries roughly ±8 points. It is enough to separate 53% from 27%; it is not enough to separate
27% from 37%.

**Cursed cargo is no longer inert, and it changes the ordering.** With the +7 floor, sweeping
0 → 8 cursed items costs a blind crew 12% of earnings ($6,503 → $5,744) against the 2.9% R9
measured at +2 — and at 8 aboard, always-scanning overtakes selective scanning, because a van
full of curses keeps the Curator high enough that picking the best item on every shelf starts
to pay for its own noise. Greed and information are coupled: the greedier the van, the more
the appraiser is worth.

**The pillar works harder than designed.** Look at the Disturbance column, not the money: a
blind crew ends the night at 30 and is never hunted. A scanning crew is pinned at 100 for
most of the night. Appraising doesn't cost you *a bit* of noise — it moves you permanently
into COLLECT. "Information costs safety" turns out to be a much sharper trade than the design
claimed, which is good, and means it needs watching rather than strengthening.

### Two problems this exposed

**1. There is currently no decision to make.** *(Overturned — R8. Left in place because the
retraction is the useful part.)* At the designed retrieval rates SCAN appeared to dominate
outright. That was the free-reroll bug in slot accounting, not the design: once a haul
*attempt* consumed the opportunity whether or not it landed, ADAPTIVE won at the
already-designed rates. See the table above. **Do not tune RETRIEVAL on the strength of this
paragraph.**

**2. Cursed cargo is inert.** *(Fixed — R9/R11. Kept because the diagnosis was right and
the prescribed cure was wrong.)* Sweeping 0 → 8 cursed items in the van moved earnings by
under $50 across every strategy: the then-current **+2** Disturbance floor per cursed item
was swamped by ordinary noise, so the van-cost half of the curse mechanic did nothing.

R9 raised the floor to **+7** (6 cursed items now cost 8.9% of earnings) — but also showed
that no floor can fix this, because a malignant item is worth ×6 and no linear cost balances
a multiplicative benefit. The floor is a texture; the actual cost is the **tail risk** in
§5. Canonical value lives in `tuning.json` (`disturbance.per_cursed_item_floor`), and both
browser prototypes were still shipping +2 as late as R16 because nothing was checking it.

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
