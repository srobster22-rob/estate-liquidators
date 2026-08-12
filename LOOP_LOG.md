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

R22 · Wrote `ART-DIRECTION.md` §2.1 — how a room's value spread is telegraphed — because R20
left it as the one question no simulation can answer, and it gates about half the appraiser's
value. · **The finding is that the prototype's telegraph does not port, and the reason is
geometric.** `proto/index.html` signals spread with silhouette **size** variance: it measures
cleanly (R20) and it is destroyed by perspective, because a large object far away and a small
one close up subtend the same angle. The game is played standing in doorways looking across
rooms — the single viewing condition that matters is the one that breaks the cue. Worth
catching *before* the prop kit exists, which is exactly why this round was worth doing on
paper. · **The three cues that survive are all already paid for.** Repetition (a uniform room
is one silhouette six times; a curio room is six silhouette *classes*), material variety —
which reuses the one-flat-colour-per-material-class system §2 already specifies for the audio
spec's impact sounds, now earning its third payoff — and arrangement (grid and even spacing
versus individually placed objects with their own space). Lighting reinforces all three for
free: pooled display lights for curio, flat wash for uniform, which is the house telling you
what it thought of its own contents. · **It reaches back into production, and cheaply.** The
~40-object prop kit in §8 has to be **~25 unique plus 5 matched sets of 6**, because a kit of
40 unique objects cannot express a uniform room at all — the one thing that room needs is six
instances of the same thing. That is cheaper than 40 unique, which is a rare direction for a
new requirement to push. · Also constrains the comedy, and in a good way: six identical clay
pots is not a joke, so uniform rooms are the straight-man rooms and the funny objects belong
in curio rooms — which is precisely where players are mechanically rewarded for stopping to
look. Funny and correct agreed here rather than conflicting, and the standing rule says to say
so out loud either way. · **Gave it a falsification that costs nothing to run**: show a player
a one-second still of a room and ask them to call it uniform/mixed/curio, target 80%. Added it
as the fifth question in §9's doorway test, where it is the newest and so the likeliest to be
missing. · **And bounded the downside using numbers this project already owns.** R17/R18
measured the misreading case, so the cost of a failed telegraph is known rather than feared:
+8.8% for a perfect read, +5.6% for a read noisier than the entire range of rooms, +4.2% for
an estate with no spread at all. **A failed telegraph costs about two-thirds of D-23's value,
not all of it** — which is both the budget argument for spending art effort here and the
reason not to panic if the first playtest reads badly. Logged as D-24.

R23 · **Could not do the round as briefed, and the reason is worth recording:** there is no
C# toolchain in this environment and no way to get one — `dot.net` is refused by the network
policy and no compiler exists on the reachable package registries. Writing C# I cannot compile
would mean shipping an untested change to the one implementation that actually has to run, so
the port itself is deferred to a machine with `dotnet`. What R23 *did* deliver is the part
that made the port a definite job rather than a vague one. · Upgraded `check_drift.py` from
"somebody claims this value" to **per-implementation coverage**, which is the property R21's
own next-step note identified as the stronger one. Attribution needed no call-site edits:
Python evaluates a call's arguments before the call, so any tuning lookup since the last
`check()` belongs to the check about to run. The buffer is marked *consumed* rather than
cleared, so a loop that sweeps a table with `.items()` and then checks two implementations in
its body attributes the whole table to both — correct, because over the full loop both do
check it. · **The picture it produces is the useful output: C# 32/64, JS 21/64, py 39/64, and
26 values claimed by the sims that the shipping core does not have.** Not the two I already
knew about — twenty-six. The whole **retrieval table**, the entire **curse economy** (value
multipliers, attention multipliers, ledger fees), all four **van slot costs**, every
**`night`** constant, and both R19 approach constants, on top of the `room_spread` and
occlusion-floor gaps R21 named. The C# core turns out to implement the *Curator* faithfully
and almost none of the *economy*. That is a much bigger and more specific finding than "the
C# has fallen behind", and it is now a list rather than an impression. · Recorded it as
`CS_BACKLOG`, which ratchets in both directions — a value that arrives in C# fails the run
until it is struck off, and one that leaves fails immediately. Verified both directions. ·
Wrote down what "claimed" actually means, because it is narrower than it sounds: **a check
exists pinning that value in that implementation**, not that the implementation is correct.
A check whose constant is missing from the source still reports NOT FOUND, so the agreement
half catches that — the two properties are only a guarantee together, and the file now says
so rather than letting a reader assume more than it delivers.

R24 · With the C# port blocked on a toolchain, went looking for a question this environment
*can* answer and found a live one hiding behind a FIRM decision. **D-19 fixes van capacity at
14 with a ceiling of 20 and calls that "just under the cliff", on the strength of a 24-32 slot
figure from `haul_sim.py` — a simulation that predates `PARALLEL_EFFICIENCY` (R7), the
slot-accounting fix (R8), the derived Disturbance model (R5) and the cursed-floor correction
(R18).** All four changed how many trips a crew gets, which is the quantity the entire
capacity argument turns on, and nobody re-ran it in eleven rounds. The van also *upgrades
across a contract chain*, so this is capacity range players actually occupy, not a hypothetical.
· **Caught my own method before reporting it, which is most of what this round was.** The
first sweep produced a wildly non-monotonic edge (4.3% → 12.0% → −5.0%) against ECONOMY §6's
claim that it decays monotonically. Rather than report a reversal, diagnosed it: `TIER_CAP` is
expressed as a *fraction of the van*, so changing capacity also changes the depth-reservation
policy and the two are confounded. Turning the reservation off entirely made SCAN beat BLIND
at every capacity ≤18 — **the myopia bug for the fourth time in this project**, exactly as R5's
standing note predicts. So the sweep cannot answer "how does the edge vary with capacity", and
the file now says so instead of printing a trend nobody should read. · **What it can answer,
robustly, is where capacity stops mattering — because that is arithmetic, not a measurement.**
A crew of four fits `6.93 + 5.20 + 8.67 = 20.8` hauls into a 540-second night at the calibrated
parallel efficiency. The sim lands on exactly **21 trips** and stays there: the van is fully
used at every capacity up to 20, and at 22, 24 and 32 slots the crew stalls at 21 trips and
earns **identical money**. · **So the cliff is at 21, not 24-32, and D-19's ceiling of 20 is
right by one slot rather than by four to twelve.** The conclusion survives; the margin is a
quarter of what was believed and the *reason* is different — the cliff is not the appraiser's
edge decaying with capacity, it is the crew running out of trips. Above the ceiling capacity
does nothing whatsoever. · **The corollary is the part that will bite someone.** The capacity
ceiling is *derived*: it moves with `night.haul_window_seconds`, `night.crew` and
`PARALLEL_EFFICIENCY`. Anyone lengthening the night or improving crew throughput is silently
moving a FIRM decision they aren't editing. Added that to D-19's falsification conditions,
which previously mentioned none of the three. · **One reassurance from the same run:** on a
V11 estate the appraiser still earns **+10.1% at the full 20-slot ceiling**, so the van upgrade
path does not kill the signature verb — D-23's authored spread is what keeps it alive right up
to the trip ceiling. That is the strongest argument for D-23 yet, and it came from a round that
was not about the appraiser at all.

R25 · Ran the provenance audit R24 called for: trace every economic claim to the model that
produced it, and mark what is stale. · **The good news first — §2's binding arithmetic checks
out.** Its hand-waved "20-24 items actually extracted" and R24's analytic 20.8-trip ceiling
are the same number, because `PAR_EFF = 0.65` was calibrated against it in R7. Two independent
routes to the same figure is the strongest the project has on it. · **The live finding is in
§4.** The quota curve upgrades the van **14 → 19** across the contract chain, and R24's ceiling
is 20.8 trips — so the margin the appraiser lives on falls from **49% on night 1 to 9% on
night 4**. Measured it properly rather than assuming the worst: the van still binds on all four
nights and the edge stays healthy (8.8% / 16.3% / 13.8% / 11.7%), so **the upgrade path stays
inside R24's cliff — but only just.** A fifth night, a +2 slot buff, or a longer night removes
the constraint the signature verb depends on. §4's own standing recommendation (growth from
richer estates, not from squeezing a flat ceiling) now has a number behind it. · **And a
comparison nobody should have been making.** `chain_sim` reports a blind crew earning $9,373
on night 1; the appraiser family reports ~$6,400 at the same capacity, and shows **+56%**
growth across the chain where chain_sim shows **+30%**. Both are right about their own model:
**the entire appraiser family — `integrated.py` and both `appraiser_*.py` — has no apex object
in it at all.** The apex is one cart-class prize worth $4,000-8,000 for five slots, so it lifts
the level *and*, being a large fixed-size prize, damps the proportional value of every extra
slot. So the quota curve resting on chain_sim is correct and must not be "corrected" toward the
appraiser numbers — a mistake that was one plausible reading away, since nothing said so. ·
**Wrote `ECONOMY.md` §10 — a provenance table: which model produced which claim, which round,
and what each one cannot see.** Marked `haul_sim.py` superseded, noted that `chain_sim` cannot
price noise at all, and put the apex omission in the docstring of all three appraiser sims so
it is visible where the numbers are generated rather than only where they are quoted. Added it
to the README's document table under "**before quoting any number**". · The rule the table
exists to enforce: **quote a number with its model, or don't quote it.** R24's discovery took
eleven rounds purely because nothing linked a claim to the code behind it.

R26 · Closed the last big modelling gap `ECONOMY.md` §10 exposed: **`chain_sim.py` had no
Disturbance and no Curator at all, which means the quota curve was calibrated in a world where
appraising is free** — the one assumption `DESIGN.md` §4.4 exists to deny. Ported in the tuned
Disturbance model (crew-scaled per R12, which matters here as nowhere else because this is the
model that *sweeps crew size*), retrieval with R8's slot accounting, and a real cost for
information: three stationary seconds and a ping per candidate examined. `noise=False`
reproduces the original numbers exactly, so §4 and §8 stay checkable against what produced
them. · Also fixed a latent bug found on the way in: **`chain_sim` could not be imported at
all** — `_build_quantiles()` was only called under `__main__`, so `quantile()` raised
`KeyError` for any other module. A model nobody can import is a model nobody checks, and this
is the one the quota curve rests on. · **The result: the quota curve is 10-14 points harder
than designed once scanning is not free.** Pass rates fall 94→86, 73→62, 56→43, 41→30 across
the four nights. Re-calibrated to restore the intended feel: **$6,750 / $8,500 / $10,250 /
$12,000**, roughly $500-750 off each night. The shape and the design intent per night are
untouched — this is paying a cost the model previously ignored, not a rebalance. · **And then
the round tried to answer the bigger question and failed honestly, which is the part worth
reading.** With the apex finally in the same model as the noise, "what is the appraiser
actually worth" looked answerable — and the appraiser family has only ever modelled the
within-shelf half of the mechanic, not the across-the-night reservation price `chain_sim` runs
on, so a much larger number seemed likely. **First attempt gave the blind crew no depth
reservation at all and it packed the van with foyer junk — the myopia bug, fifth occurrence,
caught before reporting.** Fixed by letting it judge on class-and-tier averages, which D-10
says are legitimately legible. **That inverted the result: blind then beat scanning by 36%.**
Diagnosed rather than published: the class average is *noiseless*, so the threshold becomes a
perfect class filter and earnings jump $7,676 → $12,371 across a single step of the pickiness
parameter. A knife-edge is not a strategy, and a crew that never misjudges is the same strawman
pointing the other way. · **So the appraiser's value in an apex-bearing model is NOT
established, and is deliberately quoted nowhere.** The fix is one line of modelling — give the
blind estimate a per-item error — but it is a design decision about how wrong a crew can be,
not a parameter to guess, and R27 should do it deliberately. Two rounds (R6, R7) were once
spent on exactly this class of artifact; that is the going rate for getting it wrong instead.

R27 · Went after the question R26 left open — what the appraiser is worth in a model that
contains the apex — and **the answer turned out to be that the question had been asked against
the wrong denominator for nine rounds.** · Getting there took three wrong turns, all diagnosed
rather than published. First: the blind crew's knife-edge (R26) is **not** an estimate-error
problem at all. Second: it is not the trip/slot metric either, though that is a real bug —
a pocket costs half a slot and a *whole trip*, so when trips bind (R24) per-slot ranking
systematically overvalues small objects, and `metric="per_trip"` fixes it. Third and actual
cause: **the two crews were using different decision rules.** The blind one filtered on class,
the scanning one on value, and the gap between the *rules* was being read as the value of
*information*. **"Refuse pockets" is worth +45%, and it is a class-level policy that no
threshold on value-per-slot can express**, because pocket and armful per-slot distributions
almost entirely overlap. · Held the rule fixed (`rule="class"`, both crews filter on class,
only the within-class choice differs) and the comparison finally isolates information:
**−0.4% / −1.2% / −3.2% / −3.0%** across the four nights. The appraiser's value-revealing
function does not pay for its own three seconds. · **And then the two model families
reconciled exactly, which is what makes this trustworthy rather than alarming.**
`appraiser_variance` reports +8.8% and is right — *for the loot a crew chooses between*. The
apex is **62% of a night's take** ($6,000 of $9,700), taken 100% of the time (D-21), and
cannot be improved by appraising anything. So: 8.8% of the $3,700 selectable portion = $326;
$326 against a $9,700 night = **+3.4%**; minus the scan cost ≈ zero. **The models never
disagreed — the docs were quoting the flattering denominator against a quota measured in the
other one.** · **What this does and does not mean.** It does not condemn the appraiser: it
reveals **curse grade as well as value**, `chain_sim` has no curses at all, and R11 measured
the curse decision at +7% — impossible without the grade. So **the mechanic's real defence is
the curse, not the price**, and `DESIGN.md` §4.4 is written as though it were the other way
round. That changes what Milestone 2 should instrument: not "do players scan" but "do players
scan *when the grade matters*". · All three new switches (`metric`, `rule`, `depth_cap`) are
opt-in, and I checked: an earlier version of the class rule silently moved the free-info
baseline from $9,373 to $13,536, which would have invalidated ECONOMY §4 and §8 without saying
so. Gated it and confirmed `noise=False` reproduces 9,376 / 9,921 / 10,994 / 12,141 exactly.

R28 · Put curses into `chain_sim` — so for the first time the apex, the classes, the noise
**and** the curse are in one model — and measured the half R27 said had to be the appraiser's
real defence. **It is not the rescue R27 expected. The appraiser's edge inverts across the
contract chain: +9.6% on night 1, +6.6%, −1.8%, and −8.6% by night 4.** The mechanic doesn't
merely fail to keep up with the crew; it becomes actively harmful exactly as they progress.
That is `DESIGN.md` §4.4's nightmare arriving from a direction nobody was watching — not
players tiring of the appraiser, but players being **correct** to abandon it. · **First
explanation I wrote was wrong and I caught it by testing it.** I'd blamed the three seconds
scaling with van size. Cutting appraise time 3.0s → 1.0s changes essentially nothing
(+9/+5/+1/−9). **The cost is the noise**: a scanning crew sits pinned at Disturbance **98–100,
COLLECT, all night**, while a blind crew sits at **46–57, PATROL**. A bigger van means more
shelves, more pings, more of the night in the state where the Curator takes your cargo —
retrieval losses climb **0.3 → 1.5 items** across the chain against the blind crew's 0.1.
· **That independently re-confirms D-10's second bullet from a model sharing none of
`haul_sim`'s bugs.** "Scan duration is not the cost, noise carries the whole cost" was a
superseded-source claim per §10, and it has now survived re-derivation — one of very few
things in `ECONOMY.md` that has. · **And the mechanism compounds, which is the part worth
designing around.** A scanning crew seeks value; cursed items *are* the value (×2.5, ×6);
every cursed piece aboard lifts the Disturbance floor another 7 (R9/R18). So the appraiser's
own success makes the rest of its night more dangerous: scan → find the good thing → the good
thing is cursed → floor rises → more retrieval. A blind crew never enters that loop because it
never chases the multiplier. · Also worth recording: **R11's CAP_3 does not survive contact
with the apex.** Sweeping the cursed cap, take-all wins on nights 1–2 and nothing beats blind
by night 4 — because a ruin roll now destroys the apex too, and because the blind crew gets
the value multipliers for free by accident while being unable to over-collect them
deliberately. · **The honest limit on all of this, and it is a big one:** `chain_sim` has no
rooms, so it can only express "appraise every shelf" or "appraise none". R17 established the
good policy is *selective*, and this is the same binary framing R6 and R16 both found hides
the interesting middle. **The finding is real but the model cannot see the fix.** Logged three
candidates in `ECONOMY.md` §10 — selective scanning, an appraiser upgrade path to match the
van's, or not growing the van — and flagged in D-10 that this must not be reopened as a tuning
question. · Baseline discipline held: `curses=False` still reproduces 9,376 / 9,921 / 10,994 /
12,141.

---

## Next step (paste the loop prompt to resume)

*This block went stale once before — it sat on an R11-era plan while R12–R15 built something
else entirely. Rewrite it every round, even when the round changes nothing.*

**R29 is the round the last four have been converging on: merge rooms into `chain_sim`.**
Every model in this project is now partial in a way that matters, and the partials disagree
for understood reasons (`ECONOMY.md` §10). `appraiser_variance` has **rooms and spread** and no
apex, no classes, no curses. `chain_sim` has **the apex, classes, curses and noise** and no
rooms — so it can only ask "appraise everything or nothing", which R6, R16 and now R28 have all
shown is the framing that hides the answer. **R17 already established the good policy is
selective, and no model containing the apex can express it.** Port `room_spread` into
`chain_sim`: give each encounter a room class, let the crew scan only high-spread rooms, and
re-run R28's chain. That is the round that either rescues the appraiser or kills it honestly,
and it is the last big modelling gap.

**R30, and only after R29 says which: rewrite `DESIGN.md` §4.4.** It is written as though the
*price* were the point, R27 showed the value half is worth ~0 against a night's total, and R28
showed the grade half inverts across the chain. Whatever §4.4 becomes, `DESIGN.md` §11's kill
criterion has to move with it — "do players use the appraiser" is the wrong instrument if the
correct answer changes by night. Measure **scan rate by night**, and expect it to fall.

**R31 (needs `dotnet`): port the economy into the C# core.** 26 values in `CS_BACKLOG`.
*This environment cannot do it* — no toolchain, `dot.net` refused by the network policy.

**Standing rules, each earned by getting it wrong first.**
*A checker only checks what somebody named* (R18). *A check earns its place by failing the
default an unaware author produces* (R19). *Ask a statistic at the right altitude* (R20).
*Name the table you mean* (R14, R21). *A model verified in one projection is not verified in
the one you ship* (R22). *Every guarantee has been weaker than it sounded* (R23). *A
conclusion is only as current as the model underneath it* (R24) — enforced by §10's rule,
**quote a number with its model, or don't quote it**. *Every strategy needs the knowledge that
has nothing to do with the thing being tested* (R5, R6, R24, R26 twice — six occurrences, both
directions). *When two strategies differ in more than one way, you are not measuring the
difference you named* (R26, R27). *Check the denominator* (R27) — +8.8% and +3.4% were one
measurement all along.

**And the newest, from R28: test your explanation, not just your result.** The decay was real;
the first mechanism I wrote for it — scan time scaling with van size — was wrong, and one
sweep of `APPRAISE_S` falsified it. A correct finding with a wrong cause attached is worse
than no finding, because the cause is what people design against.

**Not blocked on anything except the C# port, which is blocked on a toolchain rather than a
decision.** All open decisions except O-05 (does the Curator have a face — art, blocks
nothing) are closed.
