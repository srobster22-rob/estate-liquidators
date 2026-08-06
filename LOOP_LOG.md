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

---

## Next step (paste the loop prompt to resume)

*(This section described R11 and R12 as pending for four rounds after they shipped. Rewritten
in R16 to say what is actually open. If you finish an item, delete it here — a stale plan is
worse than no plan, because it gets read as current.)*

**1 — Apply R11's lesson to the appraiser. Still the highest-value modelling gap**, and R17
made it sharper: the edge is now **+4.4%**, and cursed cargo turns out to *raise* the value of
scanning (at 8 cursed aboard, always-scan overtakes selective). That coupling is the seam to
pull on. The +6%
edge from R8 is a *linear* trade (scan cost vs scan benefit), which is exactly the structure
that produced flat, uninteresting curves for the curse until R11 made the cost catastrophic
instead of marginal. Try a tail-risk cost for scanning: appraising while already at
PURSUE/COLLECT risks the Curator arriving mid-scan (you are stationary for three seconds),
compounding per consecutive scan. If that produces an interior optimum the way it did for
curses — "scan two or three times a trip, then stop" — the appraiser question answers itself
and the whole +6% worry dissolves. Model it in `integrated.py`; do **not** tune RETRIEVAL,
which R8 showed is already sitting in the right band.

**2 — The one that genuinely needs the owner's call, deferred since R9.** Is a **+4.4%** edge
enough to carry the game's signature mechanic? Break-even-ish is defensible for a risk/reward
system — the interesting state is a real toss-up — but it is thin enough that players may
rationally skip the appraiser, the exact failure `DESIGN.md` §4.4 exists to prevent. Three
options: accept it and lean into the toss-up; make scanning *situational* (value-variance per
room — pays at a curio cabinet, wasted on a shelf of identical books, with the room's dressing
telegraphing which); or widen van scarcity, since capacity is the master lever on this edge.
If item 1 lands, this may not need answering at all.

**3 — V5 in `validate_estate.py` is the weakest of the ten checks.** It counts doors on the
*shortest* path only and has never failed anything, including the estate built to fail seven
checks. Either strengthen it to the worst-case path (as V4 already does) or delete it — a
check that cannot fail is worse than no check, because it reads as coverage. R16 makes this
cheap to test: the validator now has a self-test that asserts the *exact* failure set.

**4 — Port the lever cooldown (D-23) into the implementations.** It exists in `tuning.json`
and `sim/disturbance.py` only; the C# core exposes `KillLights()`/`GoQuiet()` with no gate,
and both prototypes have no levers at all. Currently waived in the drift checker with reasons.

**5 — Unverified, and it needs a machine with `dotnet`.** The C# core suite has not been run
since R13. R16 added three named lever constants to `Disturbance.cs` that no compiler has
seen. First thing on the Mac: `python3 check.py` and confirm the C# line says PASS, not SKIP.

**Not blocked on anything.** All open decisions except O-05 (does the Curator have a face —
art, blocks nothing) are closed. The next real information comes from Phase 0, not from
another modelling round.
