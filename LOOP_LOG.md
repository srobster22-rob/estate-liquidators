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

R16 · Finally executed the appraiser brief that has been sitting in the "Next step" block
unclaimed since R11 (R12–R15 went off building instead, and never came back to it). Built
`sim/appraiser_risk.py` — scanning holds you stationary 3s, so being at PURSUE/COLLECT while
you scan risks the Curator arriving, compounding with each consecutive scanning trip — plus a
family of GATE_k policies (appraise only while Disturbance < k) to test against BLIND, SCAN
and R8's van-fill ADAPTIVE. · **The hypothesis is falsified, and the reason is worth more than
the hypothesis was.** Best-edge-over-BLIND falls monotonically as the risk rises — 6.0% at
k=0, then 5.4, 5.0, 4.3, 2.4, and by k=8 plain BLIND wins outright. There is no coefficient at
which the appraiser gets more interesting. **R11 worked because the curse's problem was the
opposite one:** cursed cargo was *always* correct to take, so a catastrophic cost created a
decision. The appraiser is *barely* correct to use, and **you cannot raise a payoff by adding
a cost.** Applying R11's lesson here was a category error — the remaining levers must widen
the benefit, not the cost. · Second finding: the interior optimum is **degenerate**. GATE_30
wins at every k>0, and 30 is exactly the DORMANT/PATROL boundary — the edge of the region
where retrieval is 0.00. A cost function with a flat zero region can't produce an interior
optimum, only a boundary rule; the answer collapses to "scan only where scanning is free."
Only at k=0 does a truly interior gate win (GATE_45). · Third: **the compounding streak is
pure loss** — sweeping the exponent 0→2 at k=4.0 moves the best edge 3.1%→1.2%, monotonically
down. It adds punishment without adding shape, so don't build it. · **One keeper.** Even at
k=0, gating on *Disturbance* (GATE_45, $6,883) beats gating on *van fill* (ADAPTIVE, $6,852),
and buries it once any risk exists ($6,822 vs $5,174 at k=1). ADAPTIVE was only ever
approximating "scan while it's quiet" — both correlate with time. The real heuristic is the
Curator's state, and it needs no HUD: DORMANT is the tier where AUDIO-SPEC §3.2 gives the
house *no sound at all*. **"Appraise while you can't hear it."**

R17 · Took R16's conclusion at its word and went at the **benefit** side. Built
`sim/appraiser_variance.py`: scanning's payoff is exactly `0.6 ×` the half-width of the room's
value spread and nothing else, so give each room its own spread and the question "is this room
worth three loud seconds?" gets asked fresh in every doorway instead of once per night. ·
**It works — the first thing in seventeen rounds to move the edge UP, +6.2% → +10.0%.** And
the experiment was built so it *couldn't* flatter itself: room spread `f` is drawn with
`E[f]=1` for every heterogeneity level, which makes both extremes arithmetically immune —
confirmed empirically, BLIND sat at $6,485 and SCAN at ~$6,470 across the entire sweep,
unmoved. Every point of the gain goes to crews that can tell rooms apart, so this is a skill
ceiling and not an economy buff. · **It has to be authored, though.** Nothing happens at
H=0.25; the selective policy doesn't take the lead until H=0.5. An estate built without
thinking about spread sits at H=0 — which is the default — so it needed a machine check, not
a guideline. Added **V11** to `validate_estate.py` (≥25% `uniform`, ≥25% `curio`, mean spread
1.00 ±0.15) plus `LEVEL-SPEC.md` §2.1 and the three room classes. Planted an eighth fault in
BROKEN_B — every room set to `mixed`, exactly what an unaware author ships — and confirmed the
suite now trips 8/8 with the clean estate still at 11/11. Also negative-tested V11's other two
guards directly: an undeclared room and a globally scan-rich estate both fail as intended. ·
**The telegraph risk turned out mild**, which was the thing most likely to kill this. Modelling
players misreading rooms: σ=0.5 still gives +8.9%, σ=1.0 (read noise as wide as the entire
range of rooms) still gives +7.8%, and it only decays to baseline at σ=2.0. A crew that reads
rooms *badly* beats one that doesn't try. Nice emergent rule: **the noisier your read, the
pickier you should be** — top-half is optimal with a perfect read, top-quarter the instant any
noise exists. · **Partly walks back D-22.** Once rooms differ, gating on the room beats gating
on the house ($7,133 vs $6,891), and doing both is worse than the room alone ($6,982) because
the quiet window is early night while good rooms arrive whenever they arrive. But the combined
rule wins the *floor* — p10 $6,147 vs $5,853, ending at Disturbance 39 vs 72 — so it survives
as the cautious line rather than a dominated one. · **Caught one of my own bugs before
trusting the number:** at max heterogeneity the tier-1 band ($80–300) stretched wide enough to
generate *negative* item values. Clamped the half-width at the mean, which fixes it while
leaving a symmetric uniform's mean exactly where it was — so the invariance the whole
experiment rests on survived the fix. Re-ran: 10.1% vs 10.2%, no material change.

R18 · Went after the first of the two standing balance holes — cursed cargo being inert — and
it turned out to be a **drift-checker blind spot, not a tuning question**. `tuning.json`, the
C# core and `curse_test.py` have all said the Disturbance floor is **7.0 per cursed item**
since R9. `sim/integrated.py` and `proto/index.html` were both still on the inert **2.0**, and
`check_drift.py` — the tool built in R14 specifically to prevent this — could not see either,
because **both offenders inlined the number instead of naming it.** The checker's coverage is
exactly the set of constants somebody bothered to give a name to, which is a much weaker
guarantee than "55 constants agree" sounds like. Fixed all four call sites, added named
constants, and extended the checker to **65 constants** covering every model that computes a
Disturbance floor. Re-verified it still fails when it should: injected `integrated.py` 7→2 and
the JS 7→3, confirmed both are caught and the run exits 1, reverted, exit 0. · **Then re-ran
the two rounds that had been standing on the wrong number, which is the real content of this
entry.** Everything shifts down ~1.5 points and one conclusion inverts. **R16 survives
cleanly:** the tail-risk edge still falls monotonically (5.3 → 4.5 → 3.3 → 1.8 → 1.1 → 0.0),
compounding still only ever hurts, and "you cannot raise a payoff by adding a cost" is
untouched. **R17's headline survives but shrinks:** +6%→+10% was really **+4.2%→+8.8%**. The
edge still roughly doubles and the control still holds exactly (BLIND ~$6,430 and SCAN ~$6,400
flat across the entire heterogeneity sweep), so the finding stands — it was just standing a
point and a half too high. · **R17's one genuinely wrong conclusion, now overturned.** R17
claimed the room rule beats the quiet gate and that combining them costs money. That was an
artifact of the bad constant *and* of pinning the gate at Disturbance 30. With the floor
corrected the night runs hotter, so a gate at the DORMANT boundary shuts almost immediately —
the right threshold is **60, the PATROL/PURSUE boundary**, where retrieval jumps 0.02→0.10 and
which is the only large discontinuity in the cost of being seen. There, over 8,000 paired
nights, the two rules are **exactly tied: +$0 ± 12, t = 0.0**. Two strategies with identical
expected value and completely different variance is a better result than either winning, and
the gated one is *more* legible than the old rule, not less — AUDIO-SPEC §3.2 already has the
Curator drop its domestic sounds when it stops tidying and starts hunting. **"Appraise while
it's still tidying."** · Corrected the numbers in `D-10`, `D-22`, `D-23`, `README`, `DESIGN`
§4.4, `ECONOMY` §9 and `LEVEL-SPEC` §2.1 rather than leaving two rounds of confident wrong
figures in the docs.

R19 · Rewrote **V5**, which had been the validator's weakest check since R1 and had never
failed anything in eighteen rounds. · **Two reasons, and the second one is the interesting
one.** (1) It measured the wrong pair — doors between each plinth and the *van*, occlusion
along a path nobody is listening across. The player stands at the plinth; the Curator arrives
from wherever it is. (2) **It modelled an occlusion the spec explicitly forbids.** V5 used
`0.85 ** walls` decaying without bound, but AUDIO-SPEC §3.1 puts a hard floor of **0.45** on
the approach bus — "never fully blocked, by any geometry, ever" — which the validator had
simply never implemented. Apply the floor and the bus clamps at **27 against an audibility
floor of 25 at any wall count**, so the audio half of the fairness contract *cannot be broken
by a level at all*. The check wasn't merely weak, it **had no failing condition by
construction**, which is why eighteen rounds of estates sailed through it. · **The half a
level author can actually break is geometric**, and it follows from TECH-SPEC §A6 rule 2 in
one line: **you cannot be audible for 8m before contact if the floorplan does not contain 8m
of approach.** At PURSUE speed the Curator crosses a 3m gap in about a second and the warning
is over before it begins. V5 now requires every room holding a plinth to sit ≥8m from every
room connecting to it, which in practice bans the tucked-away closet with something valuable
in it — a tempting thing to author and exactly the kind of default V11 taught us to check
for. · MANOR_A passes, but only just: its tightest approach is study↔landing at **8.25m**, so
8.0 is a live threshold rather than a formality. Planted a ninth fault in BROKEN_B (potting
room pulled to 2.8m from the conservatory) and moved the V9 cloakroom out to 11.7m so the two
faults stop overlapping — **9/9 planted faults now trip exactly one check each**, clean estate
still 11/11. · Put both new constants under canonical control per R18's lesson —
`approach_occlusion_floor` 0.45 and `approach_min_warning_m` 8.0 into `tuning.json`, wired
into `check_drift.py` (now **68 constants**), and confirmed the new checks fail when the
value is perturbed. · Fed the finding back into `AUDIO-SPEC.md` §3.1, which asked for this
test in the first place: half of it now exists, and the half that remains is asserting the
*engine* honours the 0.45 floor rather than trusting the constant — an FMOD-side test, not a
validator one.

R20 · Took `room_spread` out of the documents and into the **prototype**, where the design
work had got two rounds ahead of the build. `proto/index.html` now draws each room's items
from `min(f x half-width, mean)` per LEVEL-SPEC §2.1, with the estate authored to V11's mix
(2 uniform, 2 curio, 2 mixed across its six tier-1..3 rooms, mean exactly 1.00). · **Built
the telegraph, which is the part no simulation could answer.** R17 measured that the mechanic
survives players misreading rooms; it said nothing about whether a room can *communicate*
"miscellaneous" at a glance. In the prototype it does it with **silhouette variety** — item
size variance and the number of distinct shapes both scale with the room's spread class
(uniform → 1 shape, mixed → 2, curio → 3). Crucially the silhouette is drawn from a
distribution **independent of the item's own value**, which is what keeps D-10 intact: you may
read the room, never the item. · **Verified by driving the real page in headless Chromium**
(`qa.mjs`, playwright) rather than by reading the diff. Same tier, different class:
SERVICE HALL (uniform) has a value SD of **16** against STUDY's (curio) **89** — a 5.6× ratio
against the 5.67× that 0.3:1.7 predicts. Deep rooms the same: POTTING ROOM 59 vs
CONSERVATORY 336. Shape counts land exactly on 1.00 for both uniform rooms and ~2.5 of 3 for
the curio ones. A full night runs to sunrise with no console or page errors. · **Caught a
confounded statistic in my own test before believing it.** The first D-10 pass computed
correlation between silhouette and true value across *all* items and got **r = 0.46**, which
looks like a serious leak. It isn't — silhouette base and value both scale with depth tier,
so pooling across tiers measures the tier, not the leak. Recomputed **within** each room, the
correlations are `+0.019, +0.007, −0.009, −0.030, −0.067, −0.023, +0.013`; one re-run moved
the −0.067 to +0.006, so even the largest is noise. D-10 holds, but only because the question
was asked at the right altitude. · D-23's "no extra money" claim also verified in the running
game: mean pre-curse value per tier is **96 / 191 / 476 / 995** against band midpoints of
95 / 190 / 475 / 1000. · Put `SPREAD_F` under canonical control per R18 (`tuning.json`
`room_spread.factor`, checked in both the validator and the JS — **74 constants** now), and
confirmed the new checks fail when perturbed.

R21 · Built the **inverse** of the drift check. Drift only compares constants that exist on
*both* sides, so a canonical value that **no implementation has** is invisible to it — R18's
lesson one level up. Rather than edit seventy call sites to declare which key each one covers,
wrapped the tuning dicts so every lookup records itself: `want` is always a dict access, so
*reading a value is the claim*. Then assert every numeric leaf in `tuning.json` is claimed by
somebody, with an explicit `UNIMPLEMENTED` allowlist so the existing backlog is visible and
anything **new** and unclaimed fails the run. Verified by adding a fake `brand_new_knob` to
`tuning.json` and confirming it fails immediately. · **The first honest number was 27 of 64
claimed** — nearly two-thirds of the canonical tuning was being checked against nothing. ·
**Then the tracker turned out to have the same blind spot it was built to find.** Several
checks sweep a whole table with `.items()` rather than naming each key, and `.items()` bypasses
`__getitem__` — so 15 values that *were* checked read as unclaimed. Recording on `items()` and
`values()` too moved it to 41/64. A coverage tool that under-reports coverage is the one
direction that matters, and it was wrong that way for its first hour of life. · Wrote the
checks that were merely missing and took it to **58/64 claimed, 111 constants** (from 74). The
big absences were the **whole retrieval table** — the four numbers that drive every haul result
in the project, checked nowhere — plus night length, crew size, van slot costs, six of the
nine loudness values, and the curse multiplier and fee tables. · **Caught R14's regex bug for
the third time in this project.** The slot-cost pattern matched `CLASS_WIDTH` two lines above
`CLASS_SLOTS` and reported a doorway clearance in metres as a van slot cost (0.7 against a
canonical 0.5). Anchored the pattern on the table name. Standing rule for anything that
scrapes source as text: **name the table you mean**, because the first plausible match is
usually the wrong one. · Deliberately did **not** check `NIGHT` or `CREW` against
`proto/index.html`: it ships 180s and crew 1 because it is a three-minute single-player
harness, and R12 established the decay is crew-dependent. Those are intended divergences, and
the checker now says so in a comment rather than being quietly weakened. · **Six real gaps
remain**, each annotated with why: the three light levers (specced in DESIGN §6.5, built
nowhere), the attention recompute interval, the PATROL threshold (every implementation keys
its tier table by name rather than by value), and localisation fuzz (FMOD-side; nothing here
models where a sound *seems* to come from).

---

## Next step (paste the loop prompt to resume)

*This block went stale once before — it sat on an R11-era plan while R12–R15 built something
else entirely. Rewrite it every round, even when the round changes nothing.*

**R22: the telegraph is the one open question a simulation cannot close, and it now gates
D-23.** R20 proved silhouette variety works as a spread signal in a 2D top-down prototype,
where an item is a shape on a floor seen from above. `ART-DIRECTION.md` commits to flat-shaded
low-poly in **first person**, where the player sees a room, not a plan view, and "this cabinet
holds unlike things" has to read from a doorway, at a glance, in the dark, with a flashlight.
That is an art problem with a real chance of not working. Write the `ART-DIRECTION.md` section
on how a `uniform` room and a `curio` room differ visually — repetition and rhythm versus
silhouette variety, and what the lighting has to do to support it — before any asset work
starts. Cheap now, expensive once a kitbash exists.

**Then R23: close the C#-side gaps R21 made visible.** `unity/tests/CoreTests` still pins 31
checks against a model the Python and JS have both moved past: nothing there knows about
`room_spread`, and `Loudness.cs` has no `approach_occlusion_floor` despite `tuning.json`
carrying one since R19. Those are claimed by *some* implementation so the coverage check is
green, which is exactly the weaker guarantee it can give — per-implementation coverage would
be the stronger property, and is probably the right next upgrade to `check_drift.py`.

**Four standing rules, each earned by getting it wrong first.**
*A checker only checks what somebody named* (R18) — it reported "55 constants agree" for four
rounds while two implementations disagreed about a number that moved the headline result.
*A check earns its place by failing the default an unaware author produces* (R19) — V5 passed
everything for eighteen rounds because it had no failing condition at all.
*Ask a statistic at the right altitude* (R20) — the D-10 leak test read r = 0.46 pooled across
tiers and ~0.00 within rooms, and only the second was answering the question.
*Name the table you mean* (R14, R21) — a text-scraping pattern matched `CLASS_WIDTH` instead
of `CLASS_SLOTS` and reported a doorway width as a slot cost; third occurrence of that exact
bug. Before trusting any green run, ask what it cannot see.

**The appraiser thread is closed. Keep it closed.** Five rounds (R6, R8, R16, R17, R18)
circled the same number, and the resolution was structural rather than numerical: cost levers
can only shave the edge down (D-22), the benefit side had exactly one lever on it (D-23), and
one of those rounds was measuring a typo. At **+8.8%** with a real skill ceiling, a graceful
failure mode under misreading, and two equal-value strategies of different shape, the mechanic
is defensible. **Do not reopen it with another tuning sweep.** The next real information comes
from Milestone 2 instrumentation measuring what fraction of items players actually scan at
hour five — the falsification condition D-10 has carried since the beginning.

**Not blocked on anything.** All open decisions except O-05 (does the Curator have a face —
art, blocks nothing) are closed.
