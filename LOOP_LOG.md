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

R16 · Audited the thing that audits everything else. Rebuilt `sim/check_drift.py` around
assert-or-waive coverage (every source file × every canonical constant must be one or the
other), added `sim/mutate_drift.py`, `tools/proto_smoke.mjs`, a `__main__` for the estate
validator, and `check.py` as the single entry point. · **R14's "all 55 constants agree" was
a coverage illusion, and it was hiding a live divergence.** The checker had three holes: a
`if got is not None` skip that made a *missing* C# constant indistinguishable from a correct
one; `proto3d/index.html` — an entire fourth implementation — never read at all; and no
report of constants nobody had written a pattern for. **The cursed-item Disturbance floor was
in that third category: R9 raised it from an inert +2 to +7, and both browser prototypes were
still applying `*2` two rounds later while the checker printed OK.** Assertions went 55 → 177
and the run now names every gap. · Then tested the tester: `mutate_drift.py` corrupts each of
the 177 literals in turn and requires the checker to exit 1 *and name that constant* —
**177/177 killed.** Distrusting that, I blinded one constant's comparison on purpose and
confirmed the harness reports exactly the four expected survivors. · The prototypes are now
driven headlessly in real Chromium, which catches what text-matching structurally cannot: a
constant that is correct and **unused**. It found `proto`'s loudness table declaring
`walk:0` against a canonical 20 — dead, contradictory, and invisible to every check in the
project. · Also found `validate_estate.py` had no entry point at all, so R14's "estate
validator PASS" was not produced by the command its own docstring documents. It has a two-way
self-test now: clean estate 10/10, broken estate trips exactly its 7 planted faults.
· **Unverified this round:** the C# core suite. `dotnet` cannot be installed in this
environment (the package proxy refuses), so the three named lever constants I added to
`Disturbance.cs` are checked by drift and by eye, not by a compiler. Run
`dotnet run --project unity/tests/CoreTests` on the Mac before trusting them.

R17 · Built `sim/audit_waivers.py`, which checks the *claims* R16's waivers make: if a file
has a line that talks about a constant it claims not to implement, and there's a number on
that line, the waiver is suspect. · **D-22 predicted its own failure mode — "a lazy round can
wave a genuine divergence through by writing a waiver instead of a fix" — and the audit found
three of them, all one round old, all mine.** (1) `integrated.py` hardcoded `cursed * 2.0`,
so every appraiser number published since R8 used the floor R9 replaced. (2) `disturbance.py`
used `cursed_items * 3.0` — **a third value for a constant that is 7 everywhere else.**
(3) `disturbance.py` implements both levers at exactly the canonical −15/−20, which I had
waived as "levers not modelled". · **Then the bigger one, which the audit only led to:
`disturbance.py` never had the ratcheting floor at all**, and its `__main__` defaulted to the
disproven 1/min decay — so DESIGN §6.5's headline pacing table, the thing the whole escalation
design rests on, **could not be reproduced from anything in the repository**, and the module's
own output contradicted it. Its claim that "the floor guarantees the night escalates anyway"
was true of the spec and absent from the simulation. Fixed, re-measured, and the table is now
regenerable by running one file. **With the ratchet in, 85% of *silent* nights are hunted at
least once** (was 27%) — the design's stated intent, finally modelled. · **And the finding
that matters for play: the levers, unrationed, delete COLLECT entirely.** Pull-on-sight is 5
uses a night and **0%** of the night in the Curator's top tier; the emergency valve removes
the pressure it exists to relieve. Swept the cooldown — 60s → 6%, **120s → 14%**, 300s → 26%,
never → 30% — and locked 120s as D-23. · Appraiser edge falls **+6% → +4.4%** with the
canonical floor (ordering unchanged, ADAPTIVE still wins at designed rates), the fourth value
this number has had, every retraction an instrumentation bug rather than a design change.
Cursed cargo is no longer inert in the integrated model either: 0→8 aboard now costs a blind
crew **12%** of earnings, and at 8 aboard always-scanning overtakes selective scanning.
· Suite: drift 184/184, mutation 184/184 killed, waiver audit clean, validator PASS, both
prototypes PASS in Chromium. C# still unrun (no `dotnet` here).

R18 · Took R11's lesson to the appraiser as planned — modelled being caught mid-scan as a
super-linear cost, `k x n^1.8 x tier alertness`, and added scan-depth and scan-threshold
policies to `integrated.py`. · **The tail risk works but it was answering the wrong question.
The appraiser's edge was never +4.4% — that was the ceiling of a policy space missing a
verb.** Every model since R5 asked "do you scan?" and only ever let the crew choose between
items it had already decided to take. Give it the move the mechanic actually implies —
**appraise, refuse, walk away with the slot unspent** — and the edge is **+20 to +25%**.
· **And it produces the interior optimum this project has been hunting since R5**, without
any new system: the decision is *where you set the bar*. Refusing below the 70th percentile
is best in a quiet house, the 50th once scanning is dangerous, and the 85th is **−16%** —
because the binding constraint switches. Up to the median the van fills every night and
refusing junk is nearly free; past it the clock takes over, and SKIP_85 ends **99% of nights
out of time with 8.6 of 14 slots empty.** Too picky loses more than never choosing at all,
which is a trade players can feel at the table. · Sanity checks that R6–R8 kept failing now
pass: BLIND is flat across the whole risk sweep, every scanning policy declines monotonically,
and the diagnostic that proves it — slots used, trips taken, share of nights that run out of
time — is printed with every run so the next round cannot mistake a free reroll for a finding.
· The tail-risk cost survives as a *regulator of the bar* rather than the thing that creates
the decision. · **The generalisable lesson, and the reason four rounds were spent retuning:
when a mechanic looks marginal, check whether the model gives the player every verb the
mechanic implies before touching a single number.** D-24. `DESIGN.md` §4.4, `ECONOMY.md`
§10.1 and the README's headline rewritten around it.

R19 · Built R18's finding into the game rather than leaving it in a spreadsheet.
`proto3d/index.html` gets **[Q] leave it** as a first-class verb: refused items are chalked
and dimmed so a room can be swept once instead of re-argued, the appraisal readout now says
where the item sits in its tier's value band (*"$136 CLEAN (tier 0: $40-150, this is 87%)"*),
and the ledger closes with **appraised / left behind** and a refusal percentage — the
Milestone 2 metric D-24 asks for. · **The band readout is the part that actually matters.**
D-24's decision is "where do you set the bar", and a bare dollar value gives the player
nothing to set it against; without the band the optimal policy is invisible from inside the
game, which is how a +25% mechanic goes uncollected. · Extended `tools/proto_smoke.mjs` to
drive the whole flow in real Chromium — aim, appraise, refuse, refuse again — and assert the
counters, the chalk mark, the band string and the ledger line. **14 assertions, all passing.**
· **Two bugs, both in the test, both worth the note:** the harness carried `KeyW` over from
the previous block, and appraising requires standing still, so it silently measured nothing
and reported zero — a failure that looks like an empty result rather than an error. And aiming
at an item from one metre away misses the 0.86 aim cone entirely, because the item sits at
knee height and the camera is at 1.62m. Fixed the measurement, not the tolerance. · The 2D
prototype is deliberately left alone: `proto3d` is the direction (R15), and duplicating the
verb into a legacy toy is the kind of duplication R16 exists to fight.

R20 · Went after the check that had never failed anything — V5, flagged as the weakest of
the ten since R1 — and gave every check an estate built to break it. · **V5 was measuring the
wrong pair of rooms.** It counted doors between the plinth and the *van*, but the approach bus
is the Curator coming at you, not you walking home; the geometry that matters is
spawn-to-plinth. It now walks the Curator's actual route and fails when loot is buried far
enough behind closed doors that the first warning a player gets is the thing itself.
· **The deeper problem was the evidence, not the check.** BROKEN_B plants seven faults at
once, so it proves seven checks can fire and says nothing about the other three — and V1, V5
and V7 had never failed anything in this repository. `estates.FAULTS` now carries **one estate
per check, one fault each**, and the validator asserts all ten fire on demand, reporting which
neighbouring checks each fault also trips (an unreachable room is unreachable for the Curator
too — one fault, several consequences, worth seeing). · Verified by reinstating the old
plinth-to-van path: the suite immediately reports *"V5 did not fire on an estate built to
break it"*, which is what the last nineteen rounds could not have told anyone. · The V5 fault
estate is itself instructive to build: the first version linked each scullery back to the
foyer to keep V3 happy, which shortened the Curator's approach to four doors and made the
fault evaporate. **A planted fault you cannot see fire is indistinguishable from no fault at
all**, which is the same failure this round exists to fix, one level up.

R21 · Ported D-23's rationed relief out of the simulation and into the things that will
become the game. `proto3d` gets **[G] go quiet** — 20 points off the meter, a 45-second
crew-wide hush that scales noise to 0.35, and a 120-second lockout with the countdown on the
HUD so the ration is *visible* rather than a mysterious refusal. The C# core enforces the
cooldown itself: `KillLights()` and `GoQuiet()` return `bool` and refuse while locked, because
a rule that lives in a call site is a rule that gets lost. · Promoted the hush duration and
multiplier to `tuning.json` — they had been bare literals inside `sim/disturbance.py`, which
is the same shape of gap R16 found in the prototypes, caught this time before it could drift.
Drift coverage now runs to 192 assertions across ten files, all mutation-killed. · The smoke
test drives the lever in Chromium: the drop is canonical, the second pull is refused, and the
hush expires on schedule. · **Unverified, and it is the second round in a row saying so:** the
C# additions — the cooldown gate, `Quiet`, `Hush`, and eight new assertions in the test suite
— have not been near a compiler, because `dotnet` cannot be installed in this environment. The
first thing to run on a machine that has it is `python3 check.py`; the C# line must read PASS,
not SKIP.

R22 · Merged the curse economy into `integrated.py`, so for the first time one model holds
both the appraiser and the curses. R11 measured the curse decision with the appraiser absent;
R18 measured the appraiser with the cursed count nailed to a constant. · **They were never
independent, and the coupling runs the wrong way.** A curse pays ×6, so *the curses are the
valuable items* — any policy reaching for value reaches for curses without meaning to. R18's
champion, refuse-below-the-70th-percentile, ends the night carrying **7.4 cursed pieces and
losing the entire van 57% of the time**, an outcome it never chose. Its +25% was measured in a
curse-free world; in this model it earns less than hauling blind. · **The fix is a better
rule, not a lower number: judge each piece on the margin** — value net of fee, discounted by
the ruin it raises, minus the ruin it adds to everything already aboard. MARGIN_30 beats every
capped policy **with no cap at all**, and capping it at three costs 7%. So R11's "take two or
three then refuse" is superseded: it was the best answer to a question posed in counts, and
the appraiser lets you stop counting. **Appraiser edge: +10%**, the fifth value this number
has had and the fourth time widening the model has lowered it. · Verified the merge by
reproducing every pre-R22 figure exactly with curses switched off, and reconciled the two
models rather than picking a winner — R11's TAKE_ALL collapse was real, and this shows why: a
max-of-N policy is a curse magnet, so its "take everything" arm was already a greedy selector.
· Built the missing half of the readout into `proto3d`: a cursed item now shows *"van risk 5%
→ 11%"*, because the marginal judgement is unplayable when only one side of it is visible.
Four new smoke-test assertions pin it to the canonical ruin curve.

R23 · Audited the checker's own **inventory**, then extended the same idea outward to the
specifications. · **The drift checker read ten files perfectly and was blind to the eleventh.**
`sim/curator_attention.py` carries the steal threshold, the commitment lock and the curse
attention table; `sim/validate_estate.py` carries the slot costs and the Curator's occlusion —
and neither had ever been read by the thing whose job is to read them. Both happened to agree,
which is luck, not a system. Files are now enumerated by glob and every one must be checked or
excluded **with a reason**, so the eleventh file cannot arrive silently. 206 assertions over
twelve files, all mutation-killed; verified by dropping a scratch file into `sim/` and
watching the run fail. · Then the layer nobody was guarding at all: **the specs**. Built
`sim/check_docs.py`, which re-derives 51 numbers a human reads before typing them somewhere —
including AUDIO-SPEC §1.2's *derived* columns, where the hearing radius and Disturbance delta
for every event were computed by hand from L and the constants in §1.1. **A hand-computed
column is a copy of a calculation, and it drifts exactly like a copy of a constant.** It also
enforces the rule that bit this project in R3: a dash in the ΔDisturbance column is a hard
zero, so a sustained source is not allowed to claim one. · All 51 agree — the docs are
currently honest. Confirmed the checker can say otherwise by planting five different classes
of error (a wrong L, a wrong derived radius, a dash on a sustained source, a wrong slot cost,
a wrong ruin percentage) and watching it name all five.

R24 · Every check in this repo compares **numbers** — constants in files, figures in tables.
None compared **behaviour**, and behaviour is where this project's most expensive bug lived:
R12's sustained noise applied per frame instead of per second, sixty times too loud, with
every constant involved correct. A drift check would have passed it forever. · Built
`tools/trace_dist.mjs`, which drives the real prototype through a scripted night — real input
handler, real frame rate — and `sim/check_trajectory.py`, which re-derives the same run from
`tuning.json` alone and compares the meter second by second. **The running game tracks the
model within 0.02 points.** · Then put R12's bug back on purpose. The checker reports the
prototype at **53.8 against a canonical 0.69 after one second, and pinned at 100 by the
second** — which is precisely the description R12 wrote by hand after losing an evening to it.
**That class of bug is now a one-second check.** · Worth stating plainly what this does not
do: it drives the Disturbance integrator, not the game. A bot that plays a night — walks,
appraises, refuses, hauls — and reproduces R22's policy ordering in the actual implementation
is the obvious next step, and it needs navigation the QA hook does not yet provide.

---

## Next step (paste the loop prompt to resume)

*(This section described R11 and R12 as pending for four rounds after they shipped. Rewritten
in R16 to say what is actually open. If you finish an item, delete it here — a stale plan is
worse than no plan, because it gets read as current.)*

~~**1 — Apply R11's lesson to the appraiser.**~~ **Done, R18** — and the answer was not the
tail risk, it was the missing verb. Edge is +20–25%, the optimum bar is interior, and D-24
records both the call and the reason four earlier rounds missed it.

~~**2 — Is a thin edge enough to carry the signature mechanic?**~~ **Dissolved, R18.** It was
thin because the model was, and the fix cost nothing to implement. What replaces it is a
**build** requirement, not a modelling one: **"leave it" has to be a visible verb in the
prototype**, and Milestone 2 has to instrument *refusal rate* alongside scan rate. If players
appraise and then take everything anyway, the +25% is sitting on the table.

~~**3 — V5 is the weakest of the ten checks.**~~ **Done, R20.** It was measuring
plinth-to-van when the check is about the Curator's approach. All ten checks now have an
estate built to break them and are asserted to fire on demand.

~~**4 — Port the lever cooldown (D-23) into the implementations.**~~ **Done, R21** — enforced
inside the C# model, playable as [G] in proto3d, with the hush constants promoted to
`tuning.json`. The 2D prototype still has no levers, deliberately.

**5 — Unverified, and growing. This needs a machine with `dotnet`.** The C# core suite has
not run since R13. Since then R16 added three lever constants, R21 added the cooldown gate,
`Quiet`/`Hush`, and eight assertions — none of it compiled, because the package proxy in this
environment refuses the .NET installer. **This is now the largest unverified surface in the
project.** First thing on the Mac: `python3 check.py`, and the C# line must read PASS.

**6 — Teach the QA hook to navigate.** R24 proved the prototype's Disturbance integrator
matches canon second by second; the natural next check is a bot that plays a whole night under
a named policy and reproduces R22's ordering (MARGIN beats BLIND beats SCAN) in the real
implementation rather than in Python. That needs room-to-room pathing through the door graph,
which is maybe eighty lines and would make every future economy claim testable in the thing
people will actually play.

**7 — The next real information is a playtest, not another round.** Phases 0–2 are unchanged
and unstarted: two people, a door, spatial voice. Everything the simulations can settle at
this fidelity has been settled twice over; what is left is whether four friends in a hallway
find it funny.

**Not blocked on anything.** All open decisions except O-05 (does the Curator have a face —
art, blocks nothing) are closed. The next real information comes from Phase 0, not from
another modelling round.
