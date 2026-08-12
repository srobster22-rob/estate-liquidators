# Loop Log

One line per round. Newest at the bottom.

Format: `R<n> · <what was built> · <what it found>`

---

R1 · Built the 10-check estate validator (`sim/validate_estate.py`) + a clean and a
deliberately-broken sample estate. Verified: broken estate trips exactly the 7 planted faults,
clean estate passes all 10. · **Found:** LEVEL-SPEC §8's own worked example was invalid — the
study was a dead end (Curator in the doorway traps you), and V3 and V4 are in direct tension:
every second route you add to satisfy V3 creates a new *unpinched bypass* that defeats V4.
Added an authoring guard — any portal ≤2.0m must explicitly declare pinch true/false, since
silence is how safe corridors sneak in.

R2 · Built the Curator attention model (`sim/curator_attention.py`) — flicker, hand-off,
sacrifice plays, and whether the richest player is actually hunted. · **Found a real bug in
TECH-SPEC §A3:** the additive weight formula (+200/noise, +400/light) breaks design pillar 2
— an empty-handed player who is loud and lit gets hunted **100%** of the time over three
teammates carrying loot, because the constants are the same size as real item values.
Switched to multiplicative: empty-handed targeting → **0%**, flicker 5.0 → 2.7 retargets/min.
Also proved the hand-off override earns its keep: **0.0s vs 6.0s** when the pass lands inside
a commitment lock.

R3 · Built the Disturbance escalation sim (`sim/disturbance.py`). · **Found the pacing spine
was structurally broken.** As specced (slow accumulate, 1/min decay) the meter saturates in
under 60s and pins at 100 for the whole night — *every* crew, including one that never scans
and carries nothing cursed. Sweeping decay 1→22/min doesn't fix it; gross gain is ~54/min
against a 100-point scale. Also caught a live contradiction in AUDIO-SPEC §1.2: the general
`L × 0.02/s` implies walking costs 0.4/s while the table marks it `—`. Restructured to
**fast-decaying noise level + ratcheting floor**, which finally discriminates: silent crews
never get hunted, greedy crews hit COLLECT by minute 3. Baseline still runs hot (53% of night
in COLLECT vs 10–15% target) — shape right, level wrong.

R4 · Tuned the restructured Disturbance model against four crew archetypes. · **Locked at
decay 50/min**, impulse coefficient left at AUDIO-SPEC's 0.09 — the original bug was purely
the decay rate (1/min against ~54/min of gain), not the gain constants. Response surface is
sharp: impulse 0.09→0.06 swings baseline COLLECT from 53% to 3%, so this wants re-checking
whenever noise rates move. Final spread — silent 0% COLLECT, careful 0%, baseline 15% with
first PURSUE at 5.8 min, greedy 57% with first PURSUE at 2.7 min.

R5 · Built `sim/integrated.py` — haul loop coupled to the tuned Disturbance model, so the
appraiser's noise cost is derived rather than a free parameter. · **The appraiser's edge is
+31%, not +84%** — the earlier figure was inflated ~2.7× by the placeholder. D-10 survives.
Sharper finding in the Disturbance column: blind crews end at 30 and are never hunted,
scanning crews pin at 100 — appraising doesn't cost *some* safety, it relocates you to
COLLECT permanently. Two problems exposed: (a) at designed retrieval rates **always-scan
dominates**, so there is no actual decision — the selective band needs retrieval ~3× harsher;
(b) **cursed cargo is inert**, 0→8 cursed items moves earnings <$50, so the van-cost half of
the curse mechanic does nothing and needs to be 3–4× larger. Also caught myself writing the
**same myopia bug for the third time** (BLIND filling the van before deep tiers unlock, making
it a strawman) — worth a standing note: any new haul model needs a depth-reservation policy
before its baseline means anything.

R6 · Tried three levers to open up a band where *selective* scanning is optimal — retrieval
rates, candidates-per-shelf, and tier-scaled scanning exposure. · **None of them work, and the
reason is structural.** ADAPTIVE is a linear interpolation between BLIND and SCAN, so it can
only win in the narrow crossover where scanning is *just barely* net-negative — everywhere
else one of the extremes dominates. Retrieval sweep: ADAPTIVE wins only at PURSUE≈0.30, and
BLIND takes over by 0.35. Candidates 4→2 cuts scanning's edge 31%→16% but never changes the
ordering. Tier-scaled scan exposure goes straight from SCAN to BLIND with no band at all.
· **Also found a model bug that has been corrupting every punishment sweep since haul_sim:**
losing cargo doesn't consume a van slot, so it acts as a *free reroll* — and rerolls
preferentially benefit the picky strategy. That's why harsher punishment sometimes made
scanning *better* (edge rose 31%→38% as exposure rose). Time isn't binding enough in the
model for losses to actually hurt.

R7 · Attacked the reroll artifact by making time binding — added `PARALLEL_EFFICIENCY = 0.65`
(four players don't achieve 4× throughput), calibrated so trips-to-slots matches chain_sim's
measured 1.5×. · **Did not fix it.** SCAN still rises 8,308 → 8,994 as retrieval goes 0 →
0.10; the monotonicity test still fails. **Diagnosed the actual cause:** a lost item never
increments `filled`, so the `TIER_CAP` depth budget stays unbinding and the crew simply keeps
hauling. Losses buy *extra draws against the depth cap* instead of costing anything — tightening
the clock can't fix that because the leak is in the slot accounting, not the time accounting.
One useful side-effect: with time tighter, an ADAPTIVE band did finally appear at
PURSUE 0.20 / COLLECT 0.50 (+16% over BLIND), which is the first sign R6's structural
pessimism might be beatable.

R8 · Fixed the reroll where it actually was — slot accounting, not the clock. A haul *attempt*
now consumes the opportunity whether or not it lands. · **Monotonicity test passes**, so the
model finally behaves. **And it reverses two earlier conclusions, both of which were the same
bug talking:** (1) R5's "always-scan dominates, there is no decision" is false — at the
**already-designed** retrieval rates (PURSUE 0.10 / COLLECT 0.25) **ADAPTIVE wins**, beating
both extremes, so no retuning is needed and the design was already sitting in the good band;
(2) R6's structural argument that a middle strategy can never have a wide optimum was itself
an artifact. **The appraiser's real edge is +6% over blind hauling** — down from +84% (R5,
placeholder noise) and +31% (R6, reroll bug). That number is now the thing worth arguing about.

R9 · Swept the cursed-cargo Disturbance floor to fix the inertness R5 found. · At the specced
**+2/item, carrying 6 cursed items costs 2.9%** of earnings — confirmed inert. Raising it to
+7 gives 8.9%, +10 gives 12.8%, so a real cost curve exists and **+7/item is the recommended
value**. · **But the bigger finding is that this can't be fixed from the van side at all.**
A malignant item is worth **×6** value (×4.8 after the 20% curse fee in ECONOMY §5). No
defensible Disturbance floor comes close to offsetting a 480% value bonus, so cursed cargo is
*always* correct to take — the "burden you chose" in DESIGN §4.2 is not a decision, it's free
money with atmosphere. **The multiplier is the problem, not the floor.**

R10 · Built `sim/curse_test.py` — the first model of the curse VALUE side (integrated.py only
ever modelled the count feeding the floor). Swept the malignant multiplier with fees, the +7
floor, and attention-scaled retrieval all active. · **Lowering the multiplier does not work
either.** TAKE-ALL wins at ×6, ×4, ×3, ×2.5 and ×2.0; refusing only becomes correct at ×1.5,
where the "bonus" is already a penalty. There is **no multiplier at which taking cursed cargo
is a decision** — it's a step function from always-take to never-take with no interesting
middle. Refusing *tainted* is never right at any setting. **The cause is structural: every
curse cost is linear (a flat fee, a flat floor, a small attention bump) while the benefit is
multiplicative, and multiplicative beats linear at any scale.**

R11 · Implemented the curse as a tail risk in `sim/curse_test.py` — a per-night chance the
collection reclaims the **whole van**, rising as `0.015 × cursed^1.8` — and swept cap policies
(take cursed until N aboard, then refuse). · **It works. First interior optimum this project
has found.** At ruin_k 0.015 the peak is CAP_3 ($6,799) with CAP_2 close behind and CAP_4
already falling off; TAKE_ALL collapses to $3,930. So the right play is "two or three cursed
pieces, then stop" — worth **+7% over never touching them**, while unrestrained greed loses
~40%. Malignant stays at ×6; **no value retuning was needed once the cost shape was right.**
The general lesson, now twice-confirmed: when a benefit is multiplicative, only a super-linear
cost produces a decision — linear costs give step functions. `DESIGN.md` §4.2 rewritten around
it.

R12 · **Stopped analysing and built the thing.** `proto/index.html` — a playable single-player
Milestone 2 loop with the verified models wired in (multiplicative attention, noise-level
Disturbance, plinth-intercept pursuit, retrieval-then-death, dimming-light aggro tell).
Verified running in-browser end to end: grab → appraise → haul → deposit → sunrise → ledger,
with a `window.__game` hook for scripted QA. · **Building it found three bugs no simulation
would ever have caught**, because they only exist in real-time code: sustained noise applied
**per frame instead of per second** (sprinting added 54/s instead of 0.9/s and pinned the meter
to COLLECT within a few strides); a `dt` reference out of scope in the drop handler; and —
the real one — **Disturbance decay is crew-size dependent.** The 50/min from R4 was tuned
against a *four-person* crew's noise output. A solo player generates ~a quarter of that, so
50/min swamps everything they do and the meter never leaves DORMANT. Every sim in this project
only ever ran four players, so the dependency was invisible. Now scaled as `50 × crew/4`.
· Open: solo Disturbance tops out ~57 at sunrise, so the Curator rarely engages in a 3-minute
run — the pacing curve needs its own tuning per crew size, not just a scale factor.

R13 · Wrote `BUILD-PROMPT.md` (the self-contained brief for shipping this on Steam) and then
started executing it. Ported the verified rules to C# under `unity/Assets/Scripts/Core/` —
Loudness, Attention + hysteresis selector, Disturbance, Van/curse economy — deliberately free
of `UnityEngine` so they compile and test outside the editor. Built a dotnet cross-check
(`unity/tests/CoreTests`) that pins the C# against the Python simulations' numbers. · **31
checks, all passing:** appraiser ping = +4.32 Disturbance, empty-handed attention = 0,
hand-off 0.0s vs 6.0s, flicker 2.4/min against Python's 2.7, floor ratchets to 55, ruin curve
1.5% / 10.8% / 27.2% / 63%. One failure during the run was an off-by-one in the *test* (read
the loop counter one tick after the retarget), not the code — fixed the measurement rather
than the tolerance. · Run it with `dotnet run --project unity/tests/CoreTests`.

R14 · Wrote `IMPROVE-PROMPT.md`, then ran it. Picked the gap the prompt itself names as the
primary risk: the same rules now exist in **three** implementations (Python sims, JS prototype,
C# core) with every constant duplicated, and nothing preventing drift. Built `tuning.json` as
canonical plus `sim/check_drift.py`, which reads the C# and JS as *text* (no toolchain needed)
and asserts **55 constants** across all three agree. · **All 55 agree.** Then — per the
prompt's own "distrust clean results" rule — injected two fake divergences (C# decay 50→42,
JS ratchet 55→51) and confirmed the checker catches both and exits 1, then reverted and
confirmed exit 0. A checker that only ever passes is worthless. · Three of my own regexes were
wrong on first run (`sprint` matched the movement-SPEED table and reported 205 px/s as a
loudness; `^IMPULSE` failed without `re.M`; one pattern had no capture group). Fixed the
patterns rather than the tolerances. · Full regression green: drift 55/55, C# core 31/31,
estate validator PASS.

R15 · Direction correction from the owner: first-person, REPO/Lethal-adjacent **hiding**,
shipping as a real Steam download rather than anything web, and "good and funny graphics —
easy to look at." Two genuine gaps that surfaced: **there was no art direction document at
all**, and **the design had no hiding mechanic**, which is core genre DNA it was missing.
· Wrote `ART-DIRECTION.md`. Central call: **a straight-faced house and a ridiculous crew** —
in both reference games the environment is grim and the *players* are the comedy, and if the
level were cartoonish too there'd be nothing to be funny against. Flat-shaded low-poly, no
PBR, no PS1-crust (Lethal owns that), light and fog as the entire art budget, crew colours as
a legibility system rather than decoration. · Added `DESIGN.md` §8.1 concealment, derived from
the existing attention model rather than bolted on: **you can hide, but your loot can't.**
Carrying the prize into a wardrobe doesn't work because the item keeps radiating, so the
choice becomes stash-then-hide, hand-off-then-hide, or buy four seconds. Hiding only becomes
the *primary* verb at COLLECT, where the Curator switches to hunting crew — so the genre's
signature panic is earned late rather than constant.

R16 · Took the open item the log itself named — apply R11's tail-risk lesson to the
appraiser — and built `sim/scan_risk.py` to test it. · **The hypothesis is dead, and killing it
found the real answer.** A super-linear scan cost (`p = k x consecutive^1.8 x tier_weight`,
with death and a permanently smaller crew, which slows crew-scaled decay and spirals) makes
*every* scanning policy lose to hauling blind at every k from 0.02 up, monotonically in how
much you scan. No burst length wins. **The refinement:** cost *shape* decides whether an
interior optimum can exist, but the *size of the benefit* decides whether it does. Cursed
cargo pays x6 and survives a few ruin rolls; scanning pays x1.35 and survives none. Logged as
D-23 so the next person doesn't have the same obvious idea.
· **Then found the actual gap, which was on the benefit side.** Scanning is worth
`E[max of 4] - E[random]` = **0.6 x spread x room mean** — so its payoff is a property of the
ROOM, and every model in this project has drawn all four candidates from one flat band. Eight
rounds of trying to fix the appraiser by adjusting its *cost* were all working on the wrong
half of the equation: a constant rate of return is not a decision at any price. Gave rooms a
declared `value_class` (shelf +/-10%, mixed +/-40%, curio +/-110%) and the appraiser goes from
+4.4% to **+12.2%**. · **The controls are the finding, not the headline.** Scanning a *random*
25% of rooms earns +4.6% at identical scan count and noise, so ~60% of the edge is reading the
room rather than scanning less; and scanning only *shelf* rooms earns **-1.9%**, so there is
now a wrong answer. Robust across both sweeps: curio spread 0.7->1.9 moves the edge 7%->20%,
curio share 10%->40% moves it 6%->17%, and curio-only wins in every cell. Logged as D-22, with
its cost stated — it pulls against D-10, and the reconciliation is that *the room's variance is
public and the item's value is private*.
· **Two live bugs found on the way, both in the checking apparatus rather than the game.**
(1) `integrated.py` still had the cursed Disturbance floor at **2.0** four rounds after R11
raised the canonical value to 7.0 — because it lived as `cursed * 2.0` inside an expression,
and `check_drift.py` can only see *named* constants. The drift checker had been reporting
55/55 green over a live divergence. Hoisted it, added the check (56 now), and verified the new
check actually fires by injecting 7.0->4.0 and confirming exit 1. Correcting it moved that
file's headline from +6.1% to +4.4%. **Standing rule: a tuned number that isn't a named
constant is invisible to drift checking.** (2) `sim/validate_estate.py` had **no entry point at
all** — `validate()` was defined, `EXPECTED_FAILURES` was declared, and nothing called either,
so `python sim/validate_estate.py` printed nothing and exited 0, which reads exactly like
passing. R14's "estate validator PASS" was that. Added a self-test that asserts the clean
estate passes everything and the broken estate trips *exactly* its planted faults — no more, no
fewer, so a check that over-fires is caught too.
· Added **V11** (every loot room declares a `value_class`; 15-35% curio per wing) with a
planted fault in `BROKEN_B`, and verified its three failure modes fire: missing class, unknown
class, and both ends of the share band. Suite is now 11 checks, 8 planted faults, all green.
· Swept the docs for the appraiser number, which appeared as +84% in three places long after
two corrections: `README.md`, `DESIGN.md` §4.4 and `DECISIONS.md` D-10 now carry the full
revision chain instead of a stale headline.

R17 · Built `sim/hiding.py` and specified `DESIGN.md` §8.1 to implementation depth — it was
the newest core verb and the only one written purely in prose, with no durations, no search
behaviour and no cost. · **Found the free-reset exploit before it was ever built.** §8.1's own
numbers make stash-then-hide a *certainty*: the item goes quiet for 20s, the Curator gives up
in 12-18s, so stashing saves the loot **100% of the time you can reach a wardrobe**. That is
D-03's free-aggro-reset exploit re-entered through a different door — D-03 makes aggro persist
to the object precisely so dropping isn't a free reset, and stashing is dropping plus hiding
the object. **The fix is not a shorter timer** (at 8s stashing is never correct and the verb
dies); it is making the *search* ragged, `Random.Range(8f, 24f)` re-rolled each time, so the
two durations overlap instead of one always winning. Save rate 75%. `check_drift.py` now
asserts the invariant — search window must straddle the stash timer at both ends — so this
can't be reopened by a tidy-up. Logged as D-24.
· **Stash safety is positional, and that was the missing half.** The Curator paths to the
item's home plinth, not to you (A4), so it walks past everywhere you carried that item: a
stash within 40m of the plinth is on its route and gets found. Which means stashing somewhere
genuinely safe requires having already carried the thing most of the way home — the verb costs
exactly what you were trying to buy. Derived from an existing rule rather than invented.
· **All four verbs survived the dominance test on the first try**, which nothing else in this
project has. Run wins under ~15m (you sprint 4.1 vs 2.9 for 3.8s of stamina ≈ 15m of lead);
hand-off wins whenever anyone is within 2.5m; stash wins the long middle; hide wins at COLLECT.
· Two of those regions were **my modelling errors first, and fixing them is the finding**: I
had hide-while-holding dominated everywhere until I modelled the COLLECT targeting switch, and
stash winning everywhere until I modelled its positional cost. The first is the better one —
at Disturbance ≥85 the Curator drops item logic and targets the nearest player (A3), so the
worst verb everywhere else becomes the best one, and the genre's signature panic falls out of
a rule that was already written rather than being bolted on. Logged as D-25.
· Wrote `TECH-SPEC.md` §A9 (the SEARCH state, the attention-exclusion, stash suppression,
reacquire), `LEVEL-SPEC.md` §2.2 (hiding places as a balance parameter dressed as furniture)
and **V12** — ≥2 per wing, every plinth within 12m, none in a sole-exit room. Planted a V12
fault in `BROKEN_B` that passes the count check and fails on *coverage*, since the obvious
fault (no hiding places at all) tests nothing a level designer would actually ship. Suite is
12 checks, 9 planted faults, green.
· **Consistency sweep caught a live contradiction:** `DESIGN.md` §9 still carried the original
quota curve ($2,000 → $4,500 → $8,000 → $15,000) that `ECONOMY.md` §4 had already replaced and
measured at a **1% pass rate on night 4**. Two documents, one canonical, and the wrong one was
the one people read first. §9 now points at ECONOMY §4 and keeps the dead curve visible as a
correction rather than silently deleting it.

R18 · Took R12's open question — does `x crew/4` actually give comparable pacing at 1-4
players, or only fix the direction? — and rebuilt `sim/disturbance.py` around crew size to
answer it. · **Found the file had been shipping the pre-R4 numbers for fifteen rounds.** Its
default decay was still **1.0/min** and its cursed floor still 3.0, four rounds after both were
corrected elsewhere, so running it printed the exact broken escalation R3 diagnosed and R4
fixed — every crew in PURSUE at minute 1 and COLLECT at minute 3, including one that never
scans — with nothing to indicate it was stale. It also had no ratcheting floor at all, which
`integrated.py` has had since R5: two models of the same system, structurally different. Now
reads `tuning.json` like everything else. **This is the third stale-apparatus find in three
rounds** (R16: an inline literal invisible to the drift checker; R17: a validator with no entry
point), which is starting to look like the project's real failure mode rather than three
accidents.
· **The answer to R12: two effects, not one, and R12 named the wrong one.** The crew dependency
is mostly in the noise SOURCES — four people open four times as many doors, and the early models
charged crew-wide impulse rates that didn't scale. Fix that and most of the problem is gone
before decay is touched. What remains is that the floor, the dolly and the radio don't scale
with headcount at all, so they're a much larger share of one player's budget than of four's —
which means strictly linear decay **over**-corrects and leaves a solo crew hunted *harder* than
a full one, 28% of the night at COLLECT against 17%. Exponent **0.8** flattens it to
18/15/15/18% across 1-4 players. Logged as D-27; the prototype's `DECAY_PER_S` updated to match
and the drift checker now pins the exponent and asserts it stays sub-linear.
· **The bigger find, and it wasn't what I went looking for: the levers delete the top tier.**
Unlimited kill-lights/go-quiet means a baseline crew spends **0%** of the night at COLLECT,
against **40%** with the levers removed — five free pulls a night and the meter never stays
above 85. A 150s cooldown puts it back to 17%, matching R4's 15% target. · That is the **third
instance of one pattern**: a free, repeatable reset of the threat state. D-03 closed it for
dropping an item, D-24 (last round) for stashing one, D-26 now for the meter itself. Named as a
pattern in D-26 rather than fixed a fourth time in isolation. · It matters most here because
COLLECT is where the Curator switches from retrieving items to collecting people, which is
exactly where R17's concealment work becomes the primary verb — **an unreachable COLLECT makes
the entire hiding system unreachable content.** Two rounds of work that only pay off above 85.
· **Flagged rather than hidden: 150s is a placeholder for a cost the model can't see.** A
lever's real price is time — creeping for 45s, or hauling blind — and `disturbance.py` has no
haul loop, so it charges neither. D-26 states its own falsification: model the time cost in
`integrated.py` and if the target falls out without a cooldown, delete the cooldown.
· One coincidence worth recording. The floor tops out at `55 + 7 x cursed`, so 4 cursed items
reach 83 — two points under COLLECT — and **5 reach 90 and pin you there for the rest of the
night**. `ECONOMY.md` §5 independently puts the curse ruin optimum at 2-3 aboard with 5+ losing
~40%. The greed that ruins your van is the same greed that pins the monster on you, from three
constants tuned in three separate rounds with no knowledge of each other. Documented, not
formalised.
· Corrected `DESIGN.md` §6.5's headline table: its first-PURSUE times were measured on a model
with no ratcheting floor and are 5.8 min against a real 3.1. The COLLECT shares survive.

R19 · Ran D-26's own falsification test — price the Disturbance levers properly in a model
with a haul loop (`sim/levers.py`) and see whether the 15%-at-COLLECT target falls out without
a cooldown. · **It failed, and worse than either branch of the test anticipated: a crew that
pays for its levers pulls ZERO of them.** Not "fewer" — none. Pulling them reflexively costs
about **$975 a night, nearly 10% of earnings**, to buy a 26%→3% reduction in time at COLLECT.
So R18's cooldown wasn't rate-limiting a self-limiting choice; it was rate-limiting a choice
nobody would ever make. D-26 superseded, with the half that survives (free levers do delete
the climax) kept explicitly.
· **The cause is structural, and it generalises.** A lever priced in *throughput* asks you to
pay in the same currency as the thing you're protecting, and retrieval only ever takes a
fraction of what you carry: benefit `(0.25-0.10) x $1000 x 1.3 trips = $193` against cost
`$1000 x 0.45 x 1.3 = $579`. **Paying loot to protect loot cannot come out ahead at any
tuning.** Third time this project has found that the *shape* of a price decides whether a
decision exists independent of its size (after R10's linear-vs-multiplicative and R16's
benefit-must-survive-the-first-draws). The new clause: **a cost denominated in the same
currency as the benefit is not a decision, it's arithmetic with a known answer.**
· **Fix: levers become consumables priced in van slots** — salt and spare fuses, bought
between nights (DESIGN §9 already sells salt), free at the moment of panic, finite because you
chose how many to bring. Different currency, and the master constant of the economy (D-19). It
produces an interior optimum immediately: **1 charge +2.6%, 2 break-even, 3 -4.8%, 6 -22%**,
with COLLECT time falling 26% → 8%. Carry one, argue about the second, never carry three —
same shape as the curse cap. And it needs no rate limit, because a thing you carry limits
itself. Logged as D-28; the 150s cooldown is retired rather than tuned.
· Also worth saying plainly: **both previous positions on this were wrong in opposite
directions.** The original design had free levers (climax deleted); R18 priced them in time
(levers deleted). The design had never actually put a price on them, and both obvious prices
break something.
· **One modelling bug found, and it was distorting everything.** The first cut of this file
ended the night when the van filled — so every crew was done by minute six with the meter
still in PATROL, and every policy scored 0% at COLLECT. But a full van does *not* end the
night: the van binds by ~40% (ECONOMY §2), so the back half is spent **swapping**, hauling a
better thing out and leaving a worse thing behind. That's the appraiser's whole reason to
exist, and it means the crew is still in the house making noise long after the van is
nominally full. Adding the swap phase moved baseline from 0% to 26% at COLLECT. Any future
haul model needs the swap phase before its Disturbance numbers mean anything — the same class
of standing note as R5's depth-reservation warning.

R20 · Retro-fitted R19's swap phase to `integrated.py`, `scan_risk.py` and `chain_sim.py` —
all three still ended the night at `slots > 0` — and re-measured everything downstream. · **One
modelling assumption was wrong in three files and it moved three published numbers.** A full
van does not end the night: the van binds by ~40% (ECONOMY §2), so the back half is spent
upgrading, and stopping there deletes it. Worth **+42%** in `chain_sim`.
· **The appraiser headline falls +12.2% → +8.8%, and the finding gets stronger rather than
weaker.** Scanning broadly used to be mildly positive (curio+mixed +5.9%, scan-everything
+2.4%); it is now clearly negative (−3.3%, −6.8%). And the skill share — curio-only against a
random-25% control at identical scan count and noise — rises from 60% to **72%** of the edge.
Selectivity used to be the best of several profitable options; it is now the only profitable
one. That is the sharpest version of "information costs safety" this design has produced.
· **The quota curve is dead and recalibrated.** Every night passed 100% under
$7,500/$9,000/$10,750/$12,500 — the exact shapelessness ECONOMY §4 was written to fix,
reintroduced by a modelling assumption nobody had questioned. New curve
**$13,250/$15,250/$17,250/$19,000**, verified to reproduce the intended 95/73/54/42%.
· **The apex is a trap again, for the second time, and needed a third band.** Five indivisible
slots now compete against everything those slots would have been *upgraded into* by sunrise —
five marginal slots are worth ~$3,418 (~$684 each) and the apex also costs a large labour
block. At $4,000–8,000 it measured **−3.8%**. Re-banded to **$6,000–11,000** (+9.1%): worth
taking, cheap enough to skip on a bad night. D-21's *drama* half was never in question.
· **Two more stale constants found on the way, both in `chain_sim.py`.** Its `QUOTAS` list was
still the ORIGINAL curve that ECONOMY §4 replaced and explicitly marked broken — so the file
had been printing pass rates against a quota curve the project threw away rounds ago. And its
pre-swap earnings ($11,024) don't reproduce ECONOMY §4's recorded $9,373 either, so that
figure was already stale before this round touched anything. Both quota curve and apex band
are now canonical in `tuning.json` with drift checks.
· **Checked the swap phase against ECONOMY §2 before believing any of it**, because a +42%
earnings revision is exactly the kind of result that should be distrusted. It produces 14.9
take-or-upgrade events against 14 slots (1.07×), *below* §2's stated 20–24 extractions
(1.43–1.71×) — so the model is if anything conservative, not generous. The +60% figure I first
saw was two effects stacked: the swap phase (+42%) and a pre-existing 18% discrepancy in the
recorded baseline.
· **Fourth stale-apparatus find in five rounds.** R16 an inline literal invisible to the drift
checker, R17 a validator with no entry point, R18 a sim shipping pre-R4 defaults, R20 a sim
carrying a superseded quota list. The pattern is now unmistakable and it is always the same
shape: **the checked surface is narrower than the file.** Every fix so far has been to widen
what `check_drift.py` can see — inline literals hoisted, whole-file "does it read tuning.json"
assertions, and now list-valued constants.

---

## Next step (paste the loop prompt to resume)

~~**1. The hiding mechanic has no numbers.**~~ **Done, R17.** Specified, simulated, and it
found a free-reset exploit in §8.1's own numbers on the way.

~~**Per-crew-size pacing, open from R12.**~~ **Done, R18.** Exponent 0.8, and the dependency
was in the noise sources rather than the decay.

~~**Price the Disturbance levers properly.**~~ **Done, R19.** The test failed, D-26 is
superseded, and levers are now consumables priced in van slots.

~~**Retro-fit the swap phase to the other haul models.**~~ **Done, R20.** It moved three
published numbers. `haul_sim.py` is the one file left untouched — it is the oldest model and
its results are already superseded by `integrated.py` and `scan_risk.py`, so it was left alone
deliberately rather than overlooked.

**1. Audit every remaining sim for the same class of staleness, mechanically.** Four of the
last five rounds found apparatus that was quietly not describing the current design, and each
was found by accident while doing something else. That is luck, not process. The specific
lesson from all four: **the checked surface is narrower than the file.** `check_drift.py` now
covers scalars, list constants, and "does this file read tuning.json at all" — the next step is
to invert it and enumerate what it *cannot* see, then decide deliberately which of those gaps
matter. A structural check ("does every sim import tuning.json?") would have caught three of
the four immediately.

**2. V5 is still the weakest check in the validator**, unchanged since R1: it walks only the
*shortest* path from plinth to van and counts doors, so a wing whose alternate route is
acoustically dead passes. It has never failed anything, which for a check is a symptom rather
than a reassurance — R16 found two other pieces of apparatus that were quietly not running, so
treat "never fires" as suspect by default. Make it walk every route V3 guarantees.

**Also worth doing at some point, none of it blocking:**

- **`ART-DIRECTION.md` owes V11 a treatment.** Room value class is now a *dressing contract* —
  curio rooms must read as lotteries from the doorway — and the art doc predates the idea. If
  the telegraph doesn't land visually the mechanic degrades to a coin flip (D-22's stated
  falsification condition).
- **Port the drift checker's lesson.** A tuned number that isn't a named constant is invisible
  to `check_drift.py`. Nothing has swept the three implementations for other inline literals;
  R16 found the one it was looking for, not all of them.
- **O-05** (does the Curator have a face) remains the only open decision, and still blocks
  nothing.

**Not blocked on anything.** The next genuinely new information comes from Phase 0 — two
people, a door, and spatial voice over Steam — not from another design pass.
