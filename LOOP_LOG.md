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

R16 · Audited the drift checker itself — the guard against this project's stated primary defect
class — and rebuilt it to be fail-closed. · **Found the guard had the failure mode it exists to
prevent, twice.** (1) The C# loudness loop ended in `if got is not None: check(...)`, so a
pattern matching nothing was *skipped rather than failed*: `appraise` and `door` were never
checked against the C# core at all, because the enum spells them `AppraisePing`/`DoorSlam` and
the generated regex looked for `Appraise`/`Door`. Real C# loudness coverage was 12 of 14 while
the headline read 55. (2) Nothing asserted that every canonical constant is checked *somewhere*
— **23 of the 59 values in `tuning.json` had no guard at all**: the entire slot-cost table, the
entire retrieval table, all three ledger fees, all three Disturbance levers (inline literals in
one-line methods, which is why they were missed), `localisation_fuzz_m`, `tier_patrol_at`,
`recompute_seconds`, and the night's crew/clock shape — several of them duplicated across two or
three implementations. Nothing had actually drifted yet; the values were all correct. The defect
was that nothing would have noticed if they had. · Rewrote `check_drift.py`: unmatched patterns
now FAIL instead of skipping, every `tuning.json` leaf must be checked or explicitly exempted
with a reason, stale exemptions fail too, and `EXPECTED_CHECKS` pins the headline number so it
is asserted rather than eyeballed. **55 checks → 106, covering 59/59 canonical constants.**
· Verified with 19 single-constant perturbations (each caught, each naming the right constant)
plus 5 coverage-audit probes. **The first negative-control harness was itself buggy** — it
grepped for `DRIFT`, which matches the `DRIFT CHECK` header, so all 14 rows reported CAUGHT
regardless; 14/14 clean was the tell. Re-ran against exit code. That is the fourth instrumentation
bug in seven rounds, and the second found only because a clean result looked too clean.
· Also fixed a stale comment in `chain_sim.py` that read as if wall-clock depth gating were the
live rule, contradicting D-20 — the clock path is the un-scaled baseline that reproduces D-20's
failure, not the default.

R17 · Audited every document against verified ground truth — counts, canonical numbers, paths,
and each spec against what the code actually does — then reconciled the repo to one source of
truth per fact. 68 candidate findings, each independently re-checked by a skeptic prompted to
refute; **58 confirmed, 10 refuted.** · **The headline is not a document at all.** The audit
found `proto3d/index.html` is a **fourth implementation** that `check_drift.py` had never
opened — while the prototype carried the comment *"Mirrors tuning.json. sim/check_drift.py
asserts these stay in agreement."* It did not. Behind that gap, **both** browser prototypes
were still multiplying the cursed-item Disturbance floor by the retracted **+2** instead of the
canonical **7.0** — the value R9 retired as inert. R16's coverage audit passed anyway, because
it asserted keys were checked *somewhere* and the C# and Python copies satisfied it. **That was
the wrong invariant, and it took one round to bite.** Coverage is now asserted *per
implementation* (`IMPL_KEYS`), with deliberate prototype divergences recorded and reasoned
(`DIVERGENT`) rather than silently tolerated. Fixed both prototypes; **106 checks → 132, across
4 implementations.** Verified with 13 perturbations of the newly-guarded constants plus 3
coverage-machinery probes, each failing with the right message. · **Documents:** 57 edits across
11 files. The ones that would have cost real time: `DESIGN.md` called the night *fourteen
minutes* against a canonical 720s, contradicted three times by its own text; `README.md` said
**"No code yet"** over 2,108 lines of Python, a 31-assertion C# suite and two prototypes, and
its index omitted 4 of 14 docs including `LOOP_LOG.md` — the file two other entry points declare
outranks every spec; `LEVEL-SPEC.md`'s **V2** specified wall-clock depth gating, which D-20
(FIRM) calls a bug outright, and **V3/V8/V9** described checks that would reject the validator's
own passing sample; `ECONOMY.md` §6 asserted the twice-retracted **+84%** appraiser edge with no
supersession banner, and §9.1 still told the next session to retune RETRIEVAL, which R8 forbids;
`STACK.md` cited a `TECH-SPEC.md` §10.1 that does not exist; `DECISIONS.md` printed FMOD-on-Unity-6
as **verified** when `STACK.md` records it as inferred. Three prompt docs still pointed at
`C:\Users\srobs` and warned against committing — advice that inverts on the Mac, where the
project is its own repo. · **What the refutations were worth:** they killed a proposed rewrite of
LEVEL-SPEC V5/V7 on the grounds that §6 is a *contract* deliberately ahead of the Python tool —
the right target was `validate_estate.py`'s own docstring claiming it "implements the ten
checks", which it does not. That is now honest about V2, V5 and V7.

R18 · Built `sim/check_estates.py` — a mutation test that breaks a known-good wing one fault at
a time and requires every check in `validate_estate.py` to actually fire. Picked because R17
reconciled LEVEL-SPEC's V2/V3/V8/V9 rows *to match the implementation*, which makes the
implementation the contract; if a check is vacuous, R17 canonised a bug. · **The validator had
no entry point.** Its docstring said `Run: python validate_estate.py`; the file defines
`validate()` and never calls it, so running it printed nothing and exited 0. Nothing in the repo
imported `estates.py` or called `validate()`. So `EXPECTED_FAILURES` — the seven planted faults
R1 records as verified — **was asserted by nothing**, and that verification has not run since R1.
· **And R17's own regression line was partly vacuous.** "All nine sims exit 0" counted this
file's silence as a pass. Exit codes are not evidence when a script has no entry point; the
sweep now also reports output-line counts. Fourth instrumentation bug in eight rounds, and the
first one I shipped myself. · **V7 could not fail.** It BFS'd from `curator_spawn` at zero width
over the same graph V1 walks, so in a connected estate it was strictly implied by V1 — no mutant
could trip it. Implemented the half LEVEL-SPEC actually specifies ("*and* carry an item back to
it"): the Curator must path to each plinth at the item's class width. It now detects on its own,
and it immediately caught something real — `BROKEN_B`'s V10 fault also breaks V7, because a
doorway too narrow for four players to carry a piano out is too narrow for the Curator to carry
it back. Verified that coupling by restoring the two office widths: V7 and V10 clear together.
`EXPECTED_FAILURES` updated 7 → 8, which tightens the fixture rather than loosening it.
· **V5 does not check what its name says.** It compounds occlusion 0.85 per door with no lower
bound, failing a plinth at 6+ doors (60 × 0.85⁶ = 22.6 < 25). But `AUDIO-SPEC.md` §3.1 specifies
the Curator_Approach bus with an **occlusion floor of 0.45 — "never fully blocked, by any
geometry, ever"**. Apply it and the bus bottoms out at 27, above the 25 floor at every wall
count: **geometry can never breach the audibility contract.** V5's failures model attenuation
the spec forbids. Left the threshold alone — "plinth buried six doors deep" is a real wing smell
and deleting it would trade a mislabelled check for no check — but the docstring now carries the
measured table and says plainly that the contract needs the *runtime* test §3.1 asks for.
· Result: **10/10 checks proven able to fail**, up from 7 planted and 0 asserted. V1, V5 and V7
had never been shown to fail at all.

R19 · Built `sim/check_core.py` — a mutation test that reverts each rule in the C# core one at a
time and asks whether anything notices. Every mutation runs past **both** guards, CoreTests and
`check_drift`, because a constant reversion should be caught by the drift checker while a
*logic* reversion can only be caught by behaviour. Picked because the core is what Phases 3–4
build on, and 31 passing assertions say the core agrees with the sims on the cases they cover —
not that they would notice a rule being reverted, which is the exact failure BUILD-PROMPT's
non-negotiables list exists to prevent. · **8 of 29 reversions survived both guards.** The worst
was **A2: attention noise made additive on a carrying player** — BUILD-PROMPT's *first*
non-negotiable, the R2 bug that let an empty-handed player be hunted 100% of the time. It
survived because every attention assertion used a player with **zero noise events**, so the
multiplicative shape was never exercised; only the empty-handed guard was, and that still held.
The other seven: `EffectiveAt` had no assertion at all (swapping the player/Curator occlusion
coefficients, or deleting the range clamp so distant sources go *negative*, were both
invisible); a hand-off from a non-target could steal the Curator off the person holding the
prize; the ratchet could climb past sunrise; Disturbance could exceed 100; `AddStatic` — the
dead player's whole Static budget, DESIGN 5.1 — was never called by any test; and ruin
probability could exceed certainty. Added 10 assertions, **31 → 41**, and all 29 reversions are
now caught. · **One filed gap was my own error, not the code's.** E4 (`cursedAboard <= 0` →
`< 0`) looked unguarded; checking it showed `MathF.Pow(0, 1.8) == 0`, so the early return is
redundant and the mutant is *equivalent* — identical output at 0,1,2,3,5,8,20. Reclassified
rather than "fixed" with a test that would have asserted nothing. Two equivalent mutants are now
asserted to survive, so if either is ever caught the analysis gets revisited. · **The finding
worth carrying forward is what the harness cannot reach.** Mapping the eight non-negotiables to
guards: four are pinned here, one lives in the estate validator, and **three cannot be guarded
by anything in this repository** — aggro persisting to the object, carried items staying
non-kinematic, and zero friendly-fire damage. All three are Unity behaviour, there is no Unity
project yet, and they are the likeliest to be quietly lost during Phases 1 and 3. That map is
now asserted in `check_core.py`, so a rule cannot lose its guard silently.

R20 · **Stopped hardening instrumentation and answered the open design question.** Built
`sim/scan_risk.py` to run R12's pre-registered hypothesis — that the appraiser's thin edge could
be rescued the way R11 rescued the curse, by making scanning's cost *super-linear* so appraising
repeatedly while hunted compounds the risk of being caught mid-scan. It had sat in the
next-step block for **eight rounds** while R13–R19 did the port, the drift checker, the doc
reconciliation and three mutation harnesses. · **Found a live drift bug first.**
`integrated.py` computed the cursed floor as an inline `cursed * 2.0` — the value R9 retired as
inert — and `check_drift` could not see it: mutating it to 99.0 left the run green, because the
family-level manifest was satisfied by `curse_test.py`'s copy. That is the residual hole R19
documented, and it was already there. It matters because **integrated.py is the model that
produced the appraiser's headline number**: the edge is **+4.4%, not +6%.** Third live bug from
this one constant (R17 caught it in both prototypes). Fixed, guarded per-file, negative-controlled.
· **The hypothesis is falsified, three ways, at n=20,000.** (1) **The interior optimum already
exists without any added cost** — sweeping scan *rate* 0→1 peaks at **0.2–0.3, worth +3.5%**
(z=33). Nobody had ever swept the rate; the project compared three fixed strategies and
concluded from three points that there was no interesting middle. (2) Adding the cost *lowers*
the peak (+3.5% → +2.9% linear → +2.4% compound) and does not move it — robust across nine
(k, exp) combinations. (3) The one that kills it: under the compound cost every
**player-implementable** policy lands at or below break-even. The only rule that still pays is
"scan below PURSUE *and* never twice running", and neither half works alone (streak-only −0.4%,
tier-only −0.3%, both +3.8%) — so it needs the Disturbance meter, which `DESIGN.md` §6.5 keeps
**hidden** and D-14 forbids leaning on. It also collapses the current design's ADAPTIVE
heuristic from +4.4% to **−16.9%**. Logged as **D-22: no super-linear scan cost.** · **And the
sweep found a worse problem than the one it was sent to solve.** Milestone 2's kill criterion
was "scan rate under **~30%** at hour five means the appraiser is dead". The measured *optimal*
rate is **0.2–0.3**. The gate was set at the optimum, so a crew playing correctly fails it — it
cannot distinguish *ignoring* the appraiser from *using it well*, and it is a **stop-and-rework**
gate with everything expensive behind it. Lowered to **~15%** across `DESIGN.md` §4.4/§11 and
`BUILD-PROMPT.md` Phase 2, with the per-trip-vs-per-item caveat recorded. Logged as **D-23.**
· Three attempts have now failed to turn "is +4.4% enough?" into a simulation result. It is a
design judgement, and the next real information comes from a playtest.

R21 · Closed the drift class structurally — a **declared-constant audit** that scans every
Python sim for module-level constants whose name maps to a canonical concept and requires the
value to match `tuning.json`, with no manifest entry needed. This is the "read the
implementation" check R17's docstring said only reading could do, and R19 documented as the
residual hole. · **The same defect has now been found four times, and the fourth is the worst.**
R17 caught it in both browser prototypes; R20 caught it in `integrated.py`, in the model that
produced the appraiser's headline number. R21 caught **`sim/disturbance.py` shipping
`DECAY_PER_MIN = 1.0`** — the value R3 *proved unsurvivable* and R4 replaced with 50 — as the
default its printed run actually used, plus a cursed floor of 3.0 against canon's 7.0. So from
R4 until now, anyone running the file that defines the pacing spine saw **"PURSUE at 1.0 min in
100% of nights, COLLECT in 99%, even for a crew that never scans"**: the exact broken behaviour
R4 fixed, presented as current output. Fixed both, kept the 1/min case as an explicitly-named
historical scenario so R3's finding stays reproducible, and negative-controlled all six. **133 →
157 checks.** · **Fixing it invalidated the pacing spine's headline evidence.** `DESIGN.md` §6.5's
archetype table — the table under the line "that's the curve the design has been claiming all
along, now actually produced" — does not reproduce. Under canonical constants every archetype
including greedy sits at **0% COLLECT**; with levers disabled, 35% baseline and 66% greedy. The
table says 15% and 57% and matches neither. Three causes, separated by measurement: (1) it
predates R9's floor change 3.0 → 7.0 and was never re-run; (2) the file that produced it has not
been runnable-as-recorded since R4, per the bug above; (3) **the levers are a ceiling, not a
lever** — they fire at 78 and 82, just under COLLECT's 85, and the modelled crew pulls them the
instant it can, which makes COLLECT arithmetically unreachable rather than avoidable. · **The
honest limit:** `disturbance.py` prices the levers' benefit but not their cost — it has no
earnings model, so going dark and going quiet are free — while `integrated.py`, which does model
earnings, has no levers at all. **Neither model can currently say whether the greed dial has
teeth**, which is Milestone 4's whole exit criterion. Marked the table superseded with the
measured alternatives rather than quietly rewriting the design's central claim on the strength of
a model I had just shown to be incomplete. What survives: the *ordering* (careful never hunted,
greedy at PURSUE inside 90s vs baseline's 3.5 min). The COLLECT shares do not.

R22 · Built `sim/greed_dial.py` — the first model with **both the levers and the money**, so
going dark and going quiet cost throughput. R21 ended by showing no model in the repo could
answer Milestone 4's exit criterion: `disturbance.py` has the levers and no earnings (so pulling
one is free), `integrated.py` has earnings and no levers. Costs taken from DESIGN 6.5/9 rather
than invented — a lit wing is "a huge visibility gain, safe hauling" for +25, killing lights
takes that speed-up back, going quiet is 45s of no running and no scanning. · **First verdict was
wrong, and cross-checking against R11 caught it.** The model said greed has *no* teeth — earnings
rising monotonically to maximum greed at every parameter. That is the shape that has been an
artifact three times here, so I checked it against R11's independently-derived curse curve and
they disagreed. Cause: I had invented a 35% opportunistic take-rate for cursed cargo, which
capped cursed-aboard at **4.3 no matter how greedy the profile claimed to be** — and 4.3 sits
*inside* the profitable region, so the dial could never reach its own teeth. **The model reported
no teeth because it could not be greedy.** At a realistic take rate it reproduces R11 almost
exactly: peak at two pieces **+8.5%** (R11: +7%), take-eight **−32%**, take-ten **−86%** (R11:
take-all loses ~40%). Two independent code paths, same answer — which is the strongest evidence
either has had. · **Corrected verdict: the dial has teeth.** With levers priced, COLLECT is
reachable again — **80% of the night at maximum greed**, against R21's 0% when levers were free —
and earnings peak at an interior greed level. · **The decomposition is worth more than the
verdict.** Holding two axes at baseline and moving the third: **cursed cargo spans 85% of
earnings with an interior peak at two pieces; scan rate spans 7% and peaks at maximum; wings lit
spans 8% and peaks at zero.** So **the curse's tail risk is carrying the entire greed pillar by
itself** — lights and scanning are close to free at every setting reachable here. DESIGN §4 claims
the game prices danger; on two of its three axes it currently does not. · **One divergence found
and left open rather than guessed at.** This model and R20's `scan_risk.py` disagree on the
*shape* of the scan-rate axis — interior peak at 0.2–0.3 (z=33) there, flat with a shallow peak
at 1.0 here. Same order of magnitude, and both agree scanning is not where greed gets priced, but
one shape is wrong. Tested and **rejected** the obvious explanation (that this model applies the
curse value multiplier after max-selection): disabling it leaves the peak at 1.0. Recorded in the
file with the remaining candidates. Do not quote either shape as settled.

R23 · Resolved R22's divergence — `scan_risk.py` finding an interior scan-rate optimum at 0.2–0.3
while `greed_dial.py` found the axis monotone to 1.0. Method was ablation rather than argument:
enumerate what differs, test each, keep going until something flips the shape. · **Both models
were measuring the depth gate, not the appraiser.** The tell was `waits` — the sims gate depth on
a **clock** (`PHASES` at t = 0/120/240s), so a crew that fills its tier quota early has to stand
around until the next tier opens. Scanning burns time, so it converts dead time into value and
gets credited for it. `scan_risk` has more absorbable dead time (waits fall 2.00 → 0.00 across the
sweep) and **its curve peaks exactly where that dead time runs out**; `greed_dial`'s trips are
faster because lit wings shorten them, so its dead time never runs out inside the range and the
curve just rises. **Ablate the gate and the interior peak vanishes: scanning is monotonically
valuable, best at rate 1.0, worth +25.4% instead of +3.5%.** Reproducible as panel G. · Two
hypotheses tested and rejected before that one landed: the curse value multiplier amplifying
scanning here (disabling it left the peak at 1.0), and the ruin roll coupling to scan rate (ruin
flat at ~11%, cursed-aboard exactly 3.00 at every rate). Both were plausible and both were wrong,
which is why the round took ablation rather than a good story. · **This reverses my own D-23.**
R20 lowered Milestone 2's kill criterion from ~30% to ~15% precisely because 0.2–0.3 looked like
the optimum, and a gate set at the optimum cannot tell "players ignore the appraiser" from
"players use it well". That optimum measured `PHASES` and `TIER_CAP`. Gate restored to **~30%**,
the designer's original number — and recorded as *not* simulation-backed, because after R23
nothing here can derive it. D-22's conclusion is unaffected and in fact strengthened: scanning
already pays well when the measurement is clean, so adding a super-linear cost is less justified,
not more. · **The finding reaches past both files.** Clock-gated depth is what **D-20 (FIRM)**
calls a bug outright — "any future timer-based gate is a bug" — and **every simulation in this
repo still does it**, including `chain_sim.py`, which has a `labour_gated` flag precisely because
R21 knew this mattered. Any result whose mechanism runs through crew *time* inherits the artifact.
The outstanding job is a model where the prerequisite work consumes crew time productively; that
is what would let the appraiser's real shape be measured, and it is the thing I would build next.

R24 · Built `sim/work_gate.py` — the outstanding job from R23, and the first model in this repo
that gates depth on **work** rather than a clock, as **D-20 (FIRM)** has required since R8. The
night is a budget of *crew-seconds*; hauling, appraising and prerequisite steps all spend from it,
and wall-clock time is derived back out. A prerequisite step costs `validate_estate.py`'s
`TASK_SECONDS = 75.0` × 4 = 300 crew-seconds — **a constant that had sat in the repo since R1,
defined and never used**, which R18 flagged. Depth follows LEVEL-SPEC V2 as reconciled in R17: 1
step for tier 2, 2 for tier 3, 3 for tier 4. There is no waiting; a crew not hauling is prying
boards. · **The model validates itself on D-20's own reported failure.** D-20 exists because clock
gating made bigger crews earn *less* — "a crew of two outearned a crew of six by 2×". Run both
gates over the same code: the **clock gate reproduces the inversion** (crew 2 out-earns crew 6)
and the **work gate removes it** (earnings rise monotonically 2→6). If it had failed that, nothing
else in the file would have been worth reading. · **It confirms R23 far more cleanly than R23
could.** R23 had to ablate across two files; this runs one model and changes only the gate:
**work-gated, the scan-rate optimum is a CORNER at 1.0, +14.4%, z=34.5. Clock-gated, the same code
gives an INTERIOR optimum at 0.4, +5.2%.** The interior optimum is manufactured by the gate. That
is now demonstrated within a single model, which closes the question D-23 was reversed on.
· **Three bugs of my own, all caught by reading the intermediate columns rather than the
headline.** (1) Tier 4 was an unlimited value band, so reaching the apex early printed money and a
crew of three out-earned everyone by 3× — D-21 says the apex is a single centrepiece, so it is now
capped at one. (2) Every haul cost one slot regardless of weight class, making the apex nearly
free; `van.slot_cost` is canonical and a cart is **five of fourteen** slots. (3) Panel A forced one
depth policy on every crew size, which measured the policy rather than the gate — it now takes the
best target per crew. Each showed up as an absurd intermediate (`hauls = 1.0`, crew 3 earning 3×
its neighbours), not as a wrong-looking conclusion. · Panel C carries an explicit caveat rather
than a finding: it assigns one weight class per tier while `estates.py` gives tier 3 a mix, so the
tier-3 dip is most likely that simplification. Not quoted as an economy result. · **Eleven sims
still gate on a timer.** This one does not, and D-20 now records that any result of theirs running
through crew *time* carries the artifact.

R25 · Re-measured the appraiser's edge on `work_gate.py`, using the comparison the number has
always meant — ADAPTIVE vs BLIND, with the depth policy optimised per strategy so the panel
measures the appraiser and not the policy. · **Two things flip, and the second is the finding.**
Clock-gated: BLIND 4,469 / ADAPTIVE 4,825 / SCAN 4,333 — ADAPTIVE edge **+8.0%**, and ADAPTIVE is
the best strategy, which is R8's headline. Work-gated: BLIND 7,802 / ADAPTIVE 7,944 / SCAN 8,886 —
ADAPTIVE edge collapses to **+1.8%**, and **SCAN becomes the best strategy at +13.9% over blind**.
So the appraiser is worth *more* than the project thought, and the **selectivity is worth almost
nothing**. R8's "selective scanning beats both extremes, so the design already sits in the good
band" is a clock-gate result. That inverts the open question: it was "is +4.4% enough to carry the
mechanic"; it is now "the mechanic pays fine, but there is no judgement in it" — which is the
opposite of what `DESIGN.md` §4.4 asks of it. · **Then checked the other half of the same claim,
and found the artifact at its worst.** README and D-19 say the edge "dies entirely between 24 and
32 slots", which is `haul_sim.py` — also clock-gated. The clock-gated capacity sweep is not
monotone: at 24 slots ADAPTIVE out-earns BLIND by **+69.9%**, against +9.4% at 18 and +5.2% at 32.
Investigated rather than reported: at 24 slots ADAPTIVE earns 70% more on **fewer hauls (16 vs
18)** — because scanning burns time, and under a clock gate burning time **buys depth**. ADAPTIVE
stalls long enough to unlock the tier-4 apex (4,000–8,000) that BLIND never reaches; at 32 slots
BLIND reaches it too and the gap collapses. That is R23's artifact with the apex behind it, and it
is a much larger distortion than the waiting one. · **Work-gated, the edge does not decay with
capacity at all** — small and flat, ±3% from 6 to 32 slots. Above ~18 slots the work-gated figure
stops moving entirely, because at deep play **time binds before the van does**, so extra capacity
buys nothing. That is a different mechanism from D-19's "the appraiser lives on van space
binding". **D-19's 20-slot ceiling survives** — it sits below where anything changes under either
gate — **but the 24–32 number should not be quoted as its justification.** Recorded in D-19, D-22,
`ECONOMY.md` §9.1, `DESIGN.md` §4.4 and the README.

R26 · Re-tested **D-22** on `work_gate.py`. R25 left the appraiser paying well (+13.9%) but
containing **no judgement** — always-scan simply wins — which is the opposite of what `DESIGN.md`
§4.4 asks of it. D-22 (FIRM) had rejected the one mechanism that might supply that judgement, a
super-linear scan cost, and **every measurement behind that rejection was clock-gated.**
· **All three of D-22's grounds fail under work gating, and it is reversed.** (1) "The interior
optimum already exists without any cost" — it does not; without a cost the peak is a **corner at
1.0**. That optimum was the gate, exactly as R23 found. (2) "Adding the cost lowers the peak and
does not move it" — it **moves** it: 1.0 → 0.8 → 0.6 → 0.4 as the cost strengthens, producing a
real interior optimum. (3) The one that mattered most: "every player-implementable policy lands at
or below break-even; the only rule that still pays needs the hidden Disturbance meter". Work-gated
the **best** policy is meter-free — **"never scan twice in a row", +10.1%** over never scanning,
beating always-scan (+5.7%) *and* the meter-based rule (+8.9%). · **Checked for robustness before
reversing a FIRM decision**, since deciding on one parameter point is the mistake D-22 itself made:
swept k ∈ {0.15, 0.35, 0.75} × exp ∈ {1.4, 1.8, 2.2}, and the streak rule beats always-scan in
**9 of 9**. The interior optimum appears wherever the cost is strong enough to bite (k ≥ 0.35); at
k = 0.15 the peak stays at the corner, which is the mechanism behaving correctly rather than noise.
· The rule this produces is one a crew can say out loud without reading anything hidden — *don't
scan twice in a row* — which is the same shape R11 gave the curse, and the second time a
super-linear cost has turned a corner solution into a decision in this design. What remains the
designer's call is whether to ship a mechanic at all; the simulation no longer argues against it.
· Housekeeping: a worker restart mid-round left panels G and H duplicated in the file. Removed.

R27 · Went looking for other published numbers sourced from clock-gated models, and found a
larger problem first: **`chain_sim.py` was running the retracted quota curve.** `ECONOMY.md` §4
carries a warning box about the original curve — "nights 1–3 passed 100% of the time and night 4
passed **1%**: three formalities followed by a wall" — and lists it as
**$2,000 / $4,500 / $8,000 / $15,000**. That is exactly what `chain_sim.py:63` still held, from
the recalibration until now. The model that produced the fix never adopted it, and had been
printing the broken pass rates (0% / 0% / 1% / 7% / 20% across crew sizes) as current output.
**Fifth instance of a retracted constant surviving in one implementation** — after R17's two
prototypes, R20's `integrated.py`, and R21's `disturbance.py`. · **R21's declared-constant audit
could not see it, and that gap is the real lesson.** `QUOTAS` is a *list*, and the audit only
scans `NAME = <scalar>`. So the guard built specifically to end this class had a shape it could
not inspect. Made the contract chain canonical — `tuning.json` now carries `contract.*` with the
quota curve and van ladder — and added element-wise checks. **157 → 166 checks, 59 → 68
constants.** Negative-controlled by reverting the curve: caught, per night, by name. · **The fix
validates itself against the document.** Pointed at the calibrated curve, `chain_sim` reproduces
ECONOMY §4's recorded pass rates almost exactly — **94% / 73% / 56% / 42%** against the recorded
~95% / ~73% / ~55% / ~40% — and night 4 at crew 4 lands on **41%**, which is the "40% overflow
margin" D-18 was written around. The document had been right the whole time; the model was stale.
That is the reverse of the usual finding here, and worth saying plainly. · Also fixed a hardcoded
`$15,000` in the crew-size panel header, which had gone on printing the retracted quota even
after the curve was corrected — the label is now derived from `QUOTAS`. · Crew-size *means* are
unchanged ($5,108 / $10,131 / $12,131 / $12,820 / $13,586 for crews 2–6), so D-18's reasoning and
ECONOMY §8 stand; only the pass rates were wrong, and they were wrong in the direction that made
the chain look unwinnable.

R28 · Put a real work gate into `chain_sim.py` — the model that owns the quota curve — rather
than growing `work_gate.py` into a second economy model. `chain_sim` already had the rich economy
(per-class candidate pools, an adaptive reservation price, a shared labour pool); what it lacked
was the gate. A prerequisite step is now 300 people-seconds drawn from that same pool, so it costs
the hauls it displaces and six people open a wing faster than three — D-20's mechanism rather than
a scale factor bolted onto a clock. · **The calibrated quota curve does not survive it. Every night
passes 100%** — precisely the shape `ECONOMY.md` §4's own warning box calls a failed curve.
Work-gated night 4 earns **$21,613 against a $12,500 quota**, versus $12,124 clock-gated.
· **Checked the mechanism rather than trusting the number**, because 100% across the board is the
exact shape of the failure the curve was built to fix. It is not a bug: the composition shows
clock-gated crews carry apex + 8 armfuls + 5 pockets, work-gated crews carry apex + 4 armfuls +
3 two-man and **no pocket junk at all**. Rushing all three unlocks costs 225s of a 540s night and
buys a van of tier-3 goods worth roughly four times as much per slot. **The clock was *forcing*
240 seconds of shallow hauling, and the quota curve was fitted to that forcing.** The transition is
sharp — at 600 people-seconds per step instead of 300, night-4 pass falls 100% → 8%.
· **Deliberately did not recalibrate the quotas on this.** The model prices the prerequisite as
*labour only*, so a crew can buy an unlock at t=0 — but a real crew has to **find the key before it
can turn it**, and that discovery cost is what the clock was crudely standing in for. Pricing
labour without discovery is the same error R21 found in the Disturbance levers, which were priced
on benefit and not cost. Doubling the quotas on a model with a known missing cost would repeat the
mistake this loop has now corrected four times. · Recorded as a ⚠️ flag in `ECONOMY.md` §4 and in
D-20: the curve is valid for the clock-gated world it was measured in, and **re-deriving it needs
a prerequisite that costs search as well as labour** — which is now the clearest single gap in the
simulation set.

---

## Next step (paste the loop prompt to resume)

**R12: apply R11's lesson to the appraiser — it is the same shape of problem.** The +6% edge
from R8 is a *linear* trade (scan cost vs scan benefit), which is exactly the structure that
gave flat, uninteresting curves for the curse. Try giving scanning a super-linear or tail-risk
cost — e.g. appraising while already at PURSUE/COLLECT risks the Curator arriving mid-scan
(you are stationary for 3s), with the risk compounding per consecutive scan. If that produces
an interior optimum the way it did for curses, the appraiser question answers itself and the
+6% concern dissolves.

~~R11: make the curse a TAIL RISK instead of a marginal cost.~~ **Done.** That's the only shape that
can work, and it follows directly from R10 — a linear cost can never balance a multiplicative
benefit, so the cost has to be super-linear or catastrophic. Candidate: cursed cargo carries a
chance of losing the **entire van**, scaling super-linearly with how many you're carrying (one
malignant item is a shrug, four is a real chance the night ends with nothing). That converts
"linear cost vs multiplicative benefit" into a gamble with a ruin probability, which is a
genuine decision and also much better fiction — the collection reclaiming everything at once.
Model it in `curse_test.py` as a per-night ruin roll and find the curve where 1–2 cursed items
is clearly worth it and 5+ clearly isn't. Then rewrite `DESIGN.md` §4.2 around it, because the
current "burden you chose" framing describes a burden that arithmetically isn't one.

**And the one that genuinely needs your call, deferred from R9.** Is a **+6%** edge
edge enough to carry the game's signature mechanic? Break-even-ish is arguably correct for a
risk/reward system (the interesting state is a real toss-up), but it's thin enough that players
may rationally skip the appraiser entirely, which is the exact failure `DESIGN.md` §4.4 was
written to prevent. Three options worth weighing: accept it and lean into the toss-up; widen
the payoff by making scanning *situational* (value-variance per room — pays at a curio cabinet,
wasted on a shelf of identical books, with the room's look telegraphing which); or widen van
scarcity, since §6 showed capacity is the master lever on this edge. **Do not tune RETRIEVAL** —
R8 showed the designed values already produce the right ordering.

~~Also still open, both live balance holes: **cursed cargo is inert** (+2 Disturbance floor per
item is swamped; needs ~+7) and `DESIGN.md` §4.2 / §6.5 want updating with whatever lands.~~
**Closed.** The floor shipped at +7 and the van cost became R11's super-linear tail risk; R17
reconciled `DESIGN.md` §4.2 and `ECONOMY.md` §5/§9.1 to match, and fixed the `+2` still live in
both browser prototypes. Still open: **V5 in `validate_estate.py`** remains the weakest of the
ten checks — it only counts doors on the shortest path and has never failed anything. R17 adds
**V2 and V7** to that list (see the file's own docstring).

**Not blocked on anything.** All open decisions except O-05 (does the Curator have a face —
art, blocks nothing) are closed.
