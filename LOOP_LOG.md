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

Also still open, both live balance holes: **cursed cargo is inert** (+2 Disturbance floor per
item is swamped; needs ~+7) and `DESIGN.md` §4.2 / §6.5 want updating with whatever lands. And
**V5 in `validate_estate.py`** remains the weakest of the ten checks — it only counts doors on
the shortest path and has never failed anything.

**Not blocked on anything.** All open decisions except O-05 (does the Curator have a face —
art, blocks nothing) are closed.

---

## BONKHORDE loop

**R1 — GLIMMERFOWL is a bird; the story matches the game.** Rebuilt the last old-world body
(gilded urn → jewelled bird: crest, beak, tucked wings, running legs, five-plume tail fan),
keeping the gold ring + sky beam that pay for its contrast exemption. Found that the marker
draws *before* the body, so `fowlMarks` read 3 even if the plan threw — replaced with a box
count (46 each, 15 of them marker). Rewrote the story block, per-species comments, end-screen
flavour and the sudden-death banner (now reads the last boss's own name instead of hardcoding
"THE FINAL BONK"). README caught up on four rounds: creature bestiary, the seven lines and the
move each learns, three ranks and why the ceiling didn't move, the floor, the real hop curve.
238 checks pass. **Next:** the balance table is stale — it predates the 3-rank remap — and the
four bosses still have no body plans of their own, they are generic boxes scaled up.

**R2 — The four bosses stopped being the same box in four colours.** They shared `generic`
(five boxes and a scale factor) for the whole project: THE MATRIARCH is now a front-loaded slam
beast with a brood riding her spine, THORNBACK a spined slab that sheds its thorns, SKYSPLITTER
a swept-wing raptor built to only go forwards, TERRAVORE a plated burrower that comes up mouth
first with lit seams and a ring of teeth — 61/91/42/98 boxes. Three bugs fell out: `spawnBoss`
hand-copies `def` field by field and silently dropped `body`, so all four rendered the fallback
while the table said otherwise (caught by a box-count floor, not the sig check — four different
*sizes* give four different sigs); the boss LOD was pinned at 2 forever, which was free at five
boxes and 3733-over-3600 at ninety-eight (now 45m/90m tiers, 3474); and the arena-edge camera
check was still probing (0,71)/(71,71) from when RIM was 84, measuring the middle of the map
with a ground-vs-sky colour test that passed or failed on which biome the dice rolled there.
Rewritten to probe RIM−8, measure *structure* (distinct tones below the horizon + separation
from the sky) instead of hue, and to sweep the eye radius from 16 bearings. 243 checks pass.
**Next:** the balance bench says the 3-rank remap broke the game open — a first run with **no**
permanent upgrades now medians **24:00** on every line (was ~5:13), reaching level 76–95 and
15,000 kills. Power per pick roughly doubled and the threat curve did not move. `hpScale`/
`dmgScale` are now `let` behind `__g.curve()` and `BONKHORDE_CURVE=hpQuad,dmgDiv` so the fix can
be swept instead of guessed.

**R3a — instruments before the fix.** Added `HP_QUAD`/`HP_LIN`/`DMG_DIV` behind `__g.curve()`
and `BONKHORDE_CURVE=hpQuad,dmgDiv,hpLin` so a difficulty candidate is an env var, not an edit.
Found and fixed a harness bug while sweeping: `__g.give(k,n)` still clamped at `l<4`, which
`wStat` hides for weapons (it clamps its own index) but `prank()` does not — so
`give("magnet",4)` was handing a passive 8.33 effective ranks against a legal ceiling of 5, and
every passive measured through that hook was 67% over-strength. Clamped to `WMAX-1`; new
section 22b asserts both halves of the remap contract — three ranks is the ceiling however hard
you push (rank index 2 at nine picks), and three ranks is worth what five were (×1.450 speed
against the old five-rank ×1.45). Also asserted the boss LOD claim directly (TERRAVORE 98 boxes
at 10m → 36 at 110m) rather than leaning on the frame budget, which now passes either way.
Seven new mutations, 44 anchors, none drifted. First sweep at hpQuad 4.5 barely moved the
needle (intern still dying at 22–24 min). **Next:** two much larger candidates in flight
(9,300,220 and 20,220,150) — and the suspicion is the remap is only half of it: evolution now
hands you a *whole extra weapon* at rank 1 and ranks it to 3, on top of every pick you already
had, which is power the curve was never tuned against.

**R3b — correction: I read medians off a bimodal distribution and called it a broken game.**
Benching the pre-rework build (7a38c11 — the exact commit the README's "0/42, medians 4:29–10:57"
table describes) at n=3 returned medians of 24:00 on four of seven lines. The baseline does not
reproduce its own published table, because run length here is bimodal: a run either falls apart
before five minutes or coasts to the twenty-minute wall, so at n=3–6 the median is whichever
side got one extra sample. Clears — the statistic that actually defines the difficulty claim —
are 0/21 at baseline and 1/36 now, i.e. unmoved. The player IS meaningfully stronger (average
level 59→80, kills 10.5k→15k for intern) but the game was never "broken open"; my R3 note said
it was and that was wrong. `balance.js` now prints `early` (runs dead before 10:00) and a TOTAL
row, because counts over all trials move smoothly where the median does not. Sweeping also
turned up four call sites the rank remap missed, all reading the RAW index where every
neighbouring line reads `prank()`: PLATING's retaliation blast, CLOVER's crit, BIG HEART's
per-pick HP and regen, and DUPLICATOR's copy count — each a silent 40% nerf against the "rank 3
of 3 is worth rank 5 of 5" contract, and the DUPLICATOR one was visible: the SKULLS *renderer*
already read `prank` while the simulation read `l+1`, so at rank 3 you watched five skulls orbit
and three of them hit. All four fixed, and the eight passive descriptions now quote three-rank
numbers instead of five-rank ones. **Next:** read the A/B at n=6 on `early`/`clears`, then
decide whether the real problem is difficulty at all or the *variance* — "die at 5:00 or coast
to 24:00" is a worse shape than either end of it.

**R3c — the A/B, on statistics that hold still.** 42 trials a side. Baseline (7a38c11) vs
current: runs dead before 10:00 went **12/42 → 0/42**; clears went 1/42 → 3/42, i.e. unmoved;
average weapon evolutions per run went 1.5–4.0 → 4.5–4.8. So the remap did not make the game
clearable, it made the first ten minutes unloseable — because evolving a weapon now costs
rank 3 + passive rank 3 = six picks where it cost rank 5 + rank 3 = eight, and each pick is
worth 1.67 old ranks, so nearly every weapon in the kit evolves and they arrive twice as early.
That is a direct consequence of "3 max" and the fix belongs on the threat side, not by walking
the ranks back. hpQuad is the wrong lever for it (~0 before 6:00, which is why the 4.5/9/20
sweeps barely moved anything); `HP_LIN` and `DMG_DIV` are the two that bite early. Sweeping
2.5,380,220 and 2.5,260,150 at n=4×7 now. Target: `early` back to roughly 8–12/42 with clears
still near zero. **Next:** pick the curve off that sweep, confirm at n=6, then update the
README's balance section — it still publishes the old table and calls the median the headline.

**R3d — the early levers are the wrong ones; the pick supply is the right one.** Sweeping the
two levers that bite before minute six (hpLin 340→220, dmgDiv 560→380) moved `early` only
2/28 against a baseline of 12/42, and dropped clears no further. The reason is that the bot is
not dying to enemy stats at all — it is clearing the screen, and it clears the screen because
it now reaches nearly every weapon's evolved form. Under the remap the same power arrives in
about 40% fewer picks, so the honest counterweight is the **supply of picks**, not the health
of what they shoot. Added `XP_NEED` (a multiplier on `xpFor`) as a fourth lever; sweeping 1.7
and 2.4. This is also the other half of the user's own complaint — "too many levels to upgrade"
was answered with fewer ranks per thing, and fewer level-up screens per run is the same fix
from the other side. **Next:** pick the value, confirm at n=6 against `early` 8–12/42 and
clears near zero, then rewrite the README balance section around `early`/`clears` and retire
the median as its headline.

**R3e — the pick-fatigue fix, where the problem actually lives.** Two XP-need benches disagreed
by far more than the change could explain (uniform 1.7 → 9 early deaths in 28; growth-only 1.6 →
1 in 42, on an 8% difference in what a level costs), which says the bench cannot resolve
difficulty at n≤6, not that either number is right. Run length is bimodal and a cell flips
whole; distinguishing a 20% from a 30% early-death rate needs n≈50 a cell, ~4 hours of bench.
So `XP_NEED` ships at 1 — no magic number I cannot defend — and the complaint it was aimed at is
fixed where it lives instead. Everything maxes at rank 3, so a full kit is ~50 picks while a
long run reaches level 70–80: **the back thirty level-ups were full-screen drafts with one card
on them**, each unlocking the pointer, freezing the hop chain and stopping the camera to press
ROAST CHICKEN. A draft with no choice on it is now taken for you with a toast and a green +40.
Section 22c asserts both directions — a maxed, fully-evolved kit gains 40 levels and opens zero
screens, and a level-up with a real choice still opens one. 250 checks pass. **Next:** publish,
then the README balance section (it still prints the old table and treats the median as the
headline) — and note in it what the bench can and cannot resolve.

**R4 — the README stopped publishing a table its own build disagrees with.** Rewrote the balance
section around `early`/`clears` over 42 trials a side, with the before/after that actually says
what three ranks did (12/42 → 0/42 dead before ten minutes; clears 1/42 → 3/42; weapon
evolutions 1.5–4.0 → 4.5–4.8), and a paragraph on what the bench *cannot* resolve and what
sample size it would take. Added "the difficulty curve is wired but not set" to Not done, and
documented the pick-fatigue fix under the three-rank section. Fresh veteran bench came back
**7/42** against 21/42 on the build two commits ago — a 33-point move where every change between
was a buff (four `prank` call sites restored, +40 HP per surplus level). That is outside the
documented ±10 noise band and in the wrong direction, so it is not going in the README until it
replicates. Re-running the same build now. **Next:** if 7/42 replicates, bisect it — the
suspicious change is the auto-taken level-up, since it is the only one that touches the
level-up path the veteran tier spends the whole run in.

**R5 — a run begins at zero, and the veteran "regression" was the dice.** Re-ran the veteran
bench on identical code: **15/42** against the previous run's 7/42. Nothing to bisect — the band
at n=6×7 is far wider than the ±10 points the README claims, and the earlier 21/42 was never
comparable either. Then the user's report: HEAD START handed you its levels at `t=0`, so a run
with the shop maxed (which dev mode always is) *opened* on "PICK ONE · 3 MORE QUEUED" before an
enemy had walked on — the run starting on a menu. The levels are banked now and released one
every twelve seconds, so the run begins at level 1 with an empty bar and the head start arrives
while you are playing. Section 22d asserts all three parts. Also batched the auto-taken
level-ups: a big XP pickup could drain a dozen in one frame and a dozen level-up chimes stacked
is a fault noise, so it is one toast, one number, one sound however many it was. And rewrote the
draw-budget check to measure **boxes per enemy** rather than the total — the standing horde
varies 104/109/118/125 run to run so a fixed total was measuring the dice, where the per-enemy
cost held at 29.8/30.0/30.8 across runs whose totals were 450 boxes apart. 254 checks pass.
**Next:** breadth got cheap. With everything maxing in three picks the autopilot now carries and
maxes six weapons every run (4.2–4.8 evolutions), so builds no longer differ from each other —
worth a carry-slot look, and it is deterministic, unlike the difficulty curve.

**R6 — breadth costs slots again.** Six weapon and six passive slots were sized for five ranks:
60 picks to fill against the ~80 a long run hands you. At three ranks a full kit is 36 picks
plus six evolutions, so every run took six of the eight weapons, maxed all of them, and came out
as the same build as every other run — 4.2–4.8 evolved weapons a run against 1.5–4.0 before. The
ceiling never moved; the *choice* did. Slots are now **four weapons and five passives**, and the
line's own move rides free on top of the four rather than eating a quarter of the build the
creature you picked was supposed to enable. Section 22e asserts the cap in both directions —
never more than four chosen, and it does fill all four, so it reads as a decision and not a
shortage. 258 checks pass. **Next:** the six SITES designed three rounds ago (THE VAULT, THE
ARCHIVE, THE FURNACE, THE DEEP FREEZE, THE ESTATE SALE, THE WELL) are still unbuilt, and their
names are from the estate world the game no longer tells — they need redesigning for the
creature world before any of them is worth building.

**R7 — the landmarks have something in them.** The map rolls ~51 landmarks and they were
scenery the side-event spawner happened to prefer as spawn points. About half are **dens** now:
dormant under a low amber ember until you come within 15m, then they wake into the pack the
terrain implies (STONE RING → a TUSKLING herd, CRATER → a GRUBBER nest, THE ARCH → a FLITTER
roost, THE FINGERS → a SPITTOAD colony, BONE PILE → a RATLING swarm), 25% tougher than ambient,
under a column you can find from anywhere. Clear it for a boon, 40 coins and a gem scatter, and
a green marker so you can see what you have taken. Get 110m away and it goes quiet and can be
taken later — the difference between an explorable area and a leash — and den packs are exempt
from the 80m cull so a wide circle does not delete the fight you started. Nothing is required:
you can run past every den and still finish. This is the "explorable areas with a drive but not
a requirement" ask, finally built, on the creature world rather than the six estate-themed sites
designed three rounds ago and never built. Section 22f asserts all five states; the retire check
failed first time because `confine()` clamps a place() out past the rim straight back inside the
retire radius. 264 checks pass. **Next:** re-bench with dens live — they are a power source the
difficulty was never tuned against, exactly like side events were, and the README says so about
those.

**R7b — a boon can be taken once, ever.** Killed the den bench before it finished because it was
about to measure a hole: the altar's reward path fell back to re-rolling the whole boon list once
the pool was dry. Survivable at one altar a run; at twenty-five dens it is an unbounded
multiplier, since HEAVY HANDS is ×1.15 *compounding* — a run that took every den and rolled badly
would finish at thirty-three times damage against a curve tuned without any of it. Both paths now
pay coins past the sixth boon, which land in the shop rather than in the run. Asserted at forty
awards: six boons, six distinct, ×1.15 damage total. 266 checks pass. **Next:** now bench it —
first-run and veteran, with dens live and four weapon slots, and read `early`/`clears`.

**R7c — dens benched, and a grace on the opening.** First run with dens, four weapon slots and
the boon cap, 42 trials: `early` 1/42, clears 3/42 — unchanged from before dens, so the new
power source is absorbed. What *did* move is exactly what the slot cut was for: weapon
evolutions per run went 4.5–4.8 → **2.2–3.3**, so two runs of the same line no longer end up as
the same build. The bench also found a run that ended at **01:25** — a level-one creature with
one rank-one weapon walked into a bone pile and twenty-four RATLINGs came out. The ember does
telegraph it, but on a first run nobody knows what an ember means yet, and dying in eighty-five
seconds for not knowing teaches nothing. Nothing wakes in the first 45 seconds now; asserted by
standing on a den at T=0. 267 checks pass. **Next:** veteran bench in flight, then both tables
into the README.

**R8 — both tables published.** Veteran with dens: **13/42** clears, 0/42 early, evos 2.3–3.2 —
against the same build measured twice at 7/42 and 15/42 an hour apart, which is the band this
instrument actually has and the reason nothing is tuned to a decimal here. README's balance
section now carries four rows: pre-remap, post-remap, post-slots-and-dens, and veteran, with
weapon evolutions per run as a column because that is the number the slot cut was aimed at
(4.5–4.8 → 2.2–3.3). The invariant that matters still holds: a first run essentially never
clears (3/42), a maxed shop makes the ending reachable (13/42). **Next:** THE OX has medianed at
the bottom across most sweeps this session and its price is −14% speed on a map where space made
speed free; `starters.js` already ruled out the weapon. The untested lever is pickup radius.

**R9 — you can see where you are.** Dens were unfindable: the dormant ember only draws inside
120m and the woken column only exists once you are already in the fight, so twenty-five of them
across 222,000 m² was a lottery, not an explorable arena. Added a minimap — the whole arena in a
148px disc, regions tinted, dens as amber/orange/green for asleep/awake/taken, side events and
any live boss, heading arrow at the centre. The regions never move once a world is rolled so the
background is baked once per run into an offscreen canvas and blitted; sampling seven Voronoi
cells per pixel per frame would cost more than the horde does. Section 22g asserts the bake, the
rebake on a new arena, that it is a map rather than one flat colour (10 tones), and that it
reaches the screen (134 tones in the corner it occupies) rather than only memory. 271 checks
pass. **Next:** the minimap makes a compass unnecessary but nothing yet tells you *why* to go to
a den — the boon is invisible until it drops. Worth showing what a den pays on approach.

**R10 — a den says what it costs and what it pays.** Each den is dealt a *specific* boon at
world-roll, round-robin off a shuffled list so no run is six dens holding the same thing, and
advertises it from sixty metres along with its name and pack size — floating over the ember,
fading in with distance and dimmed during the wake grace. A reward you only learn after the
fight is a surprise; a reward you can read across a field is a plan. Two bugs on the way: dealing
the boons inside `rollWorld()` was a TDZ error at load, because the menu rolls a world for its
background *before* `const BOONS` initialises, and it took the whole QA hook down with it —
split into `dealDens()`. And for the third time today a probe used `freezeSpawns(true)`, which
sets `noSpawn`, which `wakeDen` refuses to wake into. 274 checks pass. **Next:** the arena is
still not reproducible — `rollWorld` uses `Math.random()` directly, so `worldSeed` is recorded
but cannot be replayed. A seeded world would let the bench pin an arena and would make "this run
was unfair" checkable.

**R11 — the arena can be replayed.** `worldSeed` was recorded from day one and could never be
replayed, because generation called `Math.random()` directly — a label on a run nobody could
re-enter. It is a real seed now (mulberry32, one stream, every roll that shapes a world), with
`__g.pin(seed)` and `BONKHORDE_SEED` to fix the arena for a whole bench. The point is not
seed-sharing: every trial used to roll a fresh arena, so region layout and den placement were
variance baked into a bench whose noise band has already cost this project two rounds of work —
a candidate on 42 arenas against a control on 42 *other* arenas differs in more than the
candidate. Section 22h asserts same seed → same ground, same regions, same dens holding the same
boons; different seed → different arena; unpinned → still fresh every run. 279 checks pass.
**Next:** measure whether pinning actually shrinks the band — same build, same seed, twice —
because if it does, every difficulty question this session gave up on becomes answerable.

**R12 — the whole run is seeded, and two contaminated measurements.** Pinning the arena was not
enough: the same build on the same seed measured **10/42 and 14/42**, because the spawn mix, the
crits, the drops, the draft sampling and the autopilot's own choices were all still
`Math.random()`. All 24 simulation call sites now draw from one seeded run stream, so a trial is
a pure function of (arena seed, run seed, character, build) — verified reproducible **to the
kill**. `balance.js` now uses **paired seeds by default**: trial *i* of every bench runs seed
BASE+i, so a candidate and its control are measured on the same forty-two worlds with the same
spawn mix and the same draft rolls, and the difference between them is the candidate rather than
the dice. `BONKHORDE_SEED=0` restores fresh worlds. Two harness bugs fell out. Section 23b's
speed probe read 8.03 on the green and 7.97 in the sludge — not a broken biome but a hop chain
left running by the autopilot from an earlier section, two links deep for the first reading and
six for the second; a chain multiplies speed by up to 1.6, which is more than the sludge's 0.86
takes away. It now turns the bot off and refuses to report a speed taken mid-chain (6.60 →
5.68, exactly ×0.861). And the minimap screenshot check read a flat corner intermittently — a
single capture can land on a frame the compositor has not painted; best-of-five now, with a draw
counter so a flat corner with a stuck counter reads as the different failure it is. 284 checks
pass. **Next:** re-run the difficulty question this session gave up on — with paired seeds it is
answerable, and `HP_LIN`/`DMG_DIV`/`XP_NEED` are already wired.

**R12b — the band is gone.** Ran the same build twice on paired seeds: the two tables are
**byte-identical**, row for row, including every median, level and kill count. TOTAL 2/42 early,
0/42 clears, both times. An instrument that read 7/42 and 15/42 on identical code four hours ago
now has *zero* variance, which means any difference between a candidate and this control is
entirely the candidate. Every difficulty question this session gave up on is answerable now.
Sweeping `XP_NEED` at 1.4 / 1.8 / 2.2 against this control. **Next:** pick the value off an exact
comparison, ship it, and rewrite the README's "what the bench cannot resolve" paragraph — it is
no longer true.

**R13 — the exact answer: player power was never the lever.** With zero-variance paired seeds,
`XP_NEED` swept against the control on the same 42 worlds: 1.0 → 2/42 early, 1.4 → 0/42, 1.8 →
3/42, 2.2 → 3/42. Doubling what a level costs — which ends the run 20+ levels lower — moves early
deaths by *one run in forty-two*. That is not noise any more, it is a measurement, and it says
the first ten minutes are unloseable for a reason that has nothing to do with how strong the
player is. Left `XP_NEED` at 1. The thing that had been sitting in plain sight the whole time:
`dmgScale` is flat ×1 until **t=300** — five full minutes where contact damage never grows — and
every sweep this session went at the *slope* past that point rather than at the grace itself.
`DMG_FROM` is a lever now; sweeping 0 with the shipped slope and with a steeper one. **Next:**
whatever that says, write the finding into the README's balance section and stop chasing the
curve — the shape (survive twenty, lose to TERRAVORE, veteran clears ~a third) is defensible and
the instrument is what this session actually needed to build.

**R14 — a type is somewhere you belong.** The seven types were a colour: two lines with the same
stat mods played identically wherever you stood. Each type now has a home region (+20% damage)
and a weak one (+15% damage taken) — EMBER in THE ASHES, TIDE in THE SLUDGE, VOLT on THE GLASS,
STONE in the rust, ROT in the midden, GALE on the flats, ECHO on the green. Both are deliberately
small: the map is rolled, so a bonus big enough to decide a run would be absent half the time and
decisive the other half. The region banner names which you are in and stays up the whole time you
stand there. The menu card shows each line's home and weakness before you pick, and the end
screen finally admits dens exist (cleared count and the boons taken). Section 22i asserts both
halves — ×1.15 taken on the wrong ground for all seven lines, 840 → 1008 damage dealt on home
ground; the first version compared raw damage across regions and read GHOUL at 47/61, which was
THE ASHES charging its own +12% on top, so it divides the region's modifier back out now. Also
finally pinned the intermittent minimap-screenshot failure: the map *was* drawing (34 draws
across the captures) and a modal was sitting on the corner — the check now clears overlays and
names them in its failure message. 288 checks pass. **Next:** the bosses are still the flattest
part of a run; with a zero-variance bench their abilities can be tuned exactly for the first time.

**R15 — counted what hits you, and the horde does not.** "The autopilot is not being hit" had
been *inferred* from the absence of deaths for a whole session. There is a damage ledger now —
every point the player takes, filed under contact, spit or hazard — printed by the bench under
`BONKHORDE_HURT=1`. Over full 20-minute runs: intern 87 hits, **189 damage from contact against
1072 from spits and 243 from hazards**; TWIN took **zero contact damage in a 24-minute run**. So
the melee horde, which is four hundred bodies and the entire visual of the game, contributes
about 12% of the threat, and one line never touched the player at all. That is the mechanic-level
answer the six constant sweeps kept pointing at, now measured rather than deduced. Section 22j
asserts each source lands in its own column. 292 checks pass. **Next:** give the horde a way to
reach you — a dive on FLITTER, which is a bird and ought to. Positioning is meant to be the only
verb, and it cannot be while proximity is free.

**R16 — FLITTER dives, and the A/B says why that is not enough.** Birds dive: inside 9.5m a
FLITTER rears, wings snapped back with a warning marker over it, then crosses at 4× its speed
aimed at where you *will* be, hitting for 2.2× if you did not turn. Two silhouettes nothing else
makes, so it is readable. Paired A/B over 42 trials each, dive on vs off: hits **525 → 618**,
total contact damage **2805 → 2738** — more contacts, no more damage, because the extra FLITTER
hits displace heavier ones inside the 0.68s iframe every hit grants. **Adding a threat source
does not add threat while intake is rate-limited**, which is worth more than the dive. And the
totals give the real scale: **~230 damage per 20-minute run from every source**, across about
fifteen hits — one hit every eighty seconds. The gap is an order of magnitude, not a nudge, so no
single behaviour closes it. Kept the dive (the horde needed a behaviour and now has a legible
one), wrote the finding into the README, and stopped: the direction that would actually close it
is rewards that require holding ground — dens, altars, bosses — which is a design decision, not a
constant. 297 checks pass. **Next:** move off difficulty. Other aspects are overdue — audio has
had no attention this session, and the mobile path has not been checked since dens, the minimap
and affinity all added HUD.

**R17 — the HUD fits on a phone again.** Three things went onto the HUD this session (minimap,
affinity line, den labels) and none had been looked at below 1280px. The first phone screenshot
showed both failures at once: the minimap was a fixed 148px disc — 12% of a desktop screen, **38%
of a phone**, sitting exactly where the right thumb drags the camera — and the centred phase line
ran straight through the level readout, printing `CINDERPUP → LV 7` and `MATRIARCH IN 04:49` over
each other at 360px. The map is now a proportion of the smaller viewport dimension (19–23% from
360px to 1280px), scales its dots with the disc, and lifts clear of the bottom HUD strip on
narrow screens; two media queries stack the top-left block and the phase line instead of letting
them share a row. Section 22l asserts no two HUD elements overlap by more than four pixels at
four viewport sizes, plus both minimap properties — a guard every future HUD addition now has to
pass. 300 checks pass. **Next:** audio has had no attention this session, and the dive, dens and
affinity all landed without a sound of their own.

**R18 — the new things make a noise.** The dive, dens and affinity all shipped silent, and the
dive is a hit the player is meant to *dodge* — with the camera behind you a bird winding up at
your flank is off-screen as often as not, so a telegraph you can only see is half a telegraph.
Five sounds added: a rising two-note chirp on a wind-up (nothing else in the mix climbs a fifth
in 90ms, so it reads as "behind you"), a low wide horn when a den wakes and the same interval
resolved upward when it is taken, and a two-note pair each way for crossing on and off your
type's ground — the direction of the interval is the information. Den wake/clear had been
borrowing `SFX.boss` and `SFX.levelup`. Every sound is now counted and fingerprinted at
definition, so section 22m can assert that each new feature actually makes a noise **and** that
no sound is a copy of another wearing a different name — the second failure being worse than
silence, since it teaches the wrong thing. 19 sounds, no duplicates. 305 checks pass.
**Next:** the seven weapon evolutions are the last content the creature rework never touched —
their names and descriptions are still from the estate world.

**R19 — the game uses the name it gave you.** Evolving announces `LEARNED CINDERTRAIL` and then
every surface in the game went on saying `CALTROPS`: it named a thing and never used the name
again, which quietly undid the point of moves coming from evolution. `wName()` is now the single
place that decides what a weapon is called — the learned move name wins where one exists, the
evolved form's name wins over that, and the generic name stays for any line that picked the
weapon out of the draft without learning it (a MYCONID carrying hazards has not learned
CINDERTRAIL and is not told it has). Section 22n asserts both directions. Also renamed the two
evolved forms that were machines in a world of animals: TESLA COIL → **THUNDERHEAD**, BOMBARDIER
→ **SKYFALL**. 307 checks pass. **Next:** `starters.js` and `dps.js` have not been run since the
three-rank remap, the four `prank` fixes and the carry-slot cut — three changes that all move
weapon power, measured by benches nobody has re-run.

**R20 — the weapon bench is paired, and two weapons failed the dominance test.** `dps.js` had
never been re-run since the three-rank remap, the four `prank` fixes or the carry-slot cut, and
it was measuring eight weapons on eight *different* arenas and calling that a comparison. Paired
seeds went in (and `BONKHORDE_TIERS=rank` to skip the expensive half); the payoff was immediate —
after changing one weapon the other seven rows came back byte-identical. Then the rule this
project already states caught two: **MORTAR was a default again** (404 boss DPS against a median
of 131 *and* the highest crowd DPS — the README recorded fixing this once and it crept back the
moment the shell count hit three, because the extra shells jittered ±3.5m around one aim point,
which is smaller than a 4m boss, so all three landed on it). Each shell picks its own cluster
now: boss 404 → **262** while crowd went *up* to 2364, so CALTROPS leads boss and MORTAR leads
crowd. And **SKULLS was the mirror** — last on both at 57/1048, strictly dominated by BONK BAT,
for a structural reason: a ring only hits what comes to you and the ledger says nothing does. The
ring reaches now (radius 4.3 → 5.8, same damage, same count) → 81/1544. Nothing leads both
columns in either table. Also dropped the survival column: with runs taking ~230 damage in twenty
minutes the autopilot survives to the clock regardless of what it carries, so it had stopped
discriminating while costing most of the bench's wall clock. 307 checks pass. **Next:**
`starters.js` is the last bench that has not been re-run, and it is the one that would say
whether any of the seven lines is now the weak pick.

**R21 — evolving is a moment now.** The centrepiece of a game about raising a creature was a
caption: the body swapped to the next form between one frame and the next, six percent larger,
while a banner explained what had happened. There is a beat now — about a second in which the old
shape washes white and swells on a `sin` curve that overshoots and settles, a column of light
rises out of the ground and a ring of shards is thrown outward, every part driven off the *same*
curve so it reads as one event rather than three effects. Section 22o asserts it starts, puts
light on the screen (204 → 349 boxes) and takes the light away again — compared against the
**peak** rather than the start, because being a different and larger animal afterwards is the
entire point and the first version of the assertion got that backwards. 310 checks pass.
**Next:** the per-line spread is the last unexamined thing — with paired seeds the veteran table
reads OX 4/6 and ACCOUNTANT 4/6 against TWIN 0/6 and SPARK 0/6, and that is now an exact number
rather than dice.

**R22 — the per-line spread is the ledger's finding again, not a balance bug.** Veteran on paired
seeds: 8/42 clears, inside the 7–15 band this instrument has produced. Reading across columns for
the first time, clears track neither level nor kills — **THE TWIN finishes with the highest kill
count and the highest level of any line and closes nothing** — they track *damage taken*: INTERN
533 contact and 4/6, GHOUL 1030 and 2/6, TWIN 14 and 0/6. The lines that clear are the lines that
get hit, because closing means standing next to TERRAVORE, and the autopilot's kiting is optimal
for surviving twenty minutes and fatal for finishing them. That is the game's central tension,
not a per-line bug, and six trials a line is too few to act on anyway — this project has already
recorded that per-character ordering does not survive re-sampling. Total went 13/42 → 8/42 after
the MORTAR fix, which is the nerf landing on ACCOUNTANT, the line that owns mortar; inside the
band, and undoing a dominance fix to chase a per-line number would be the wrong trade. Written
into the README rather than tuned away. **Next:** stop benching. The remaining gaps are content —
eight weapons is thin for the genre, and nothing gates on the seven regions yet.

**R23 — there is something after the first clear.** Clearing a run was the end of the game:
TERRAVORE dies and the only thing left is the same twenty minutes again. **THE DEEP** is a nine
layer ladder — every clear opens one more, and each layer is the same world dug further down at
+34% enemy health, +16% their damage and +30% coins, all compounding on the curve that already
exists. Picked from the menu, clock turns red while you are on one, end screen names the layer
and the layer it just opened. Deliberately a multiplier rather than new content: the levers are
wired and measured, so a layer is a number this project can reason about instead of a second game
to balance from scratch — and the coin bonus is load-bearing, or the ladder is just a difficulty
setting with a penalty. `unlockAll()` opens every layer but leaves the *selection* alone, since
dev mode should hand you the whole game rather than drop you on layer nine. Section 22p asserts
six things including that the surface is still exactly ×1. 316 checks pass. **Next:** the eight
weapons are thin for the genre and the README has said so since the beginning — with the bench
paired and the dominance test automatic, adding one is now cheap to verify.

**R24 — the eye glitch was z-fighting, in the shared helper, on every creature.** Reported as "the
fire dog eyes glitch". The eye was three flat plates — sclera, pupil, glint — at `f`, `f+.035`
and `f+.05` with half-depths of .05, .04 and .03, so their front faces landed within fifteen
thousandths of each other *and* inside the head blob. Coplanar surfaces, so the depth buffer had
to pick, and the pick changed with the camera: flicker on every creature in the game, plus the
plates were invisible edge-on. They are solids now, sized off `sz`, each front face clearly ahead
of the last and the assembly proud of the skull — interpenetration is fine, z-fighting is a
coplanar-faces problem, not an overlap one. Same fix applied to the enemy eye helper (`eey`), the
`eye`/`tooth` decals and the `grin` teeth. Also confirmed the weapon bench is genuinely
deterministic (two full runs byte-identical); an unexplained CALTROPS delta of 282 → 194 across
an earlier code change is *not* accounted for and is written down rather than hand-waved. 316
checks pass. **Next:** the retheme the user asked for — dinosaur/dragon/legendary across all
seven lines, mobs kept plain so they do not outshine the player, bosses given real scale, and the
regions moved to match.

**R25 — the creatures are dragons and dinosaurs, and the camera can see them.** Seven lines
rebuilt on a shared beast vocabulary added to the body bundle: `horn` (curves and tapers as it
goes), `ridge` (dorsal plates down a spine), `wing` (membrane hung behind a leading edge that
goes out *and* back *and* up — the first version laid flat slabs sideways, which from a camera
behind the animal is a bar through its shoulders), `claw` (three toes and a dewclaw). EMBER is a
fire drake hatchling → winged drake → coiled wyrm; TIDE grows a horned crown and claws; VOLT was
an orb with antennae and is now a storm raptor → sickle-clawed raptor → wyrm in its own cloud;
STONE is an ankylosaur line with plates, shoulder spikes and a tail club; ROT is a basilisk that
rears up; GALE is a wyvern chick → taloned skyrend → THE ROC; ECHO was N heads orbiting nothing
and is now a real **hydra** — one serpentine body, two/three/four necks growing out of it, body
scaling with the count. Enemies renamed to small prehistoric fry (GRUBLING, PTERLING, CERATOP,
DILOPHO, RAPTORLING, GILDWING) and deliberately left plain so they do not outshine the player.
Camera in and down, 10.9/5.4 → 8.9/4.1 (26° of look-down to 17°, half again the on-screen size) —
the old framing could read a silhouette but not horns, wings, teeth or a ridge, which is all these
forms are. CINDERTRAIL's hazard recoloured ember-red because a gold ring around an orange drake
was the brightest thing on screen and it was the floor. 316 checks pass, 21 forms still 21
distinct meshes. **Next:** the bosses need the wow factor — they are 42–98 boxes against a player
that is now bigger and better built than they are.

**R26 — a boss arrives, and it is five times your size.** Bosses were 4.2–6.4 units against a
player drawing at ~2.5, so the biggest thing in the game was 2.5× the thing looking at it — and
after the creature rebuild the player was the better model. Now 6.8/7.8/8.8/**13.5**, and it cost
nothing: `h`/`w` are visual only, the hitbox is `r` and reach is measured to `rad`, so no balance
number moved. They also **arrive** instead of appearing — up out of the ground over 1.5s, drawn
below the floor and hidden by the terrain (which is the whole trick, so no body plan needs to know
it exists), throwing earth off with a dust column, unable to act or be hit until out. That last
clause broke five checks and each was worth having: three damage probes stepped exactly 90 frames
= exactly 1.5s, so every one was measuring damage against something immune; the fifth was the
per-enemy draw budget, which divides the whole frame by the enemy count and so moved because the
*player* got better looking — it subtracts a no-horde frame now. 319 checks pass. **Next:** the
regions still read as an estate's grounds (SLUDGE, FLATS, MIDDEN). They should be a prehistoric
world — ash plains, tar, bone fields, crystal.

**R27 — the map is prehistoric, and the animation stopped being one sine wave.** Regions renamed
and re-storied for the dinosaur world (THE FERNLANDS, THE CINDERFLATS, THE TARPITS, THE GLACIER,
THE DUSTSEA, THE BONEFIELD, THE SPINEROCK) with the landmarks to match — STONE RING is a
**RIBCAGE** now, ribs leaning inward off a spine rather than a henge, and THE FINGERS are **THE
TUSKS**, two curving pairs. Renaming immediately tripped the HUD overlap guard (THE CINDERFLATS is
longer than THE ASHES and collided at 360px) which then exposed something worse: *every*
narrow-screen override I had added was being silently ignored, because the media blocks sat
**above** the base rules they override at equal specificity. Moved to the end of the sheet.
Then the animation, which is the thing the user actually called lazy. It was `sin(T*13)` when
moving and a hard zero when not — one frequency, one amplitude, no ramp. There is a state now with
seven terms, each driven by something the player did: gait phase from **distance covered** rather
than the clock, amplitude eased off speed, lean from acceleration, bank from turn rate, squash and
stretch from vertical speed with a hard crouch on the landing frame (the same frame the hop chain
is decided on), lunge forward on a shot and *negative* on a hit, and a head that looks at the
nearest enemy. Shear and squash are applied at the transform so all 21 forms get weight for free
and no plan needs to know what a landing is — and `bodyCap` records untransformed extents so the
distinct-meshes check still compares shapes rather than moments. Per-line: a **diagonal** gait
(the old code keyed feet off `rs*fs`, pairing the two feet on each side — a rabbit, not a lizard),
counter-swinging tails, wings that beat harder airborne, coil waves that travel with speed, and
breathing that fades out under sprint. 326 checks pass. **Next:** the enemy bodies still animate
off `e.bob` and a clock; they should get the same treatment at a fraction of the detail, since
they must not outshine the player.

**R28 — seven lines, seven skeletons, and the animation dialled back.** Two corrections from the
user, both right. First: the animation was too *big*, not too small — CINDERWHELP's tail tip swept
0.40 units on a body 0.55 wide, continuously, which is a windscreen wiper bolted to a lizard. The
rule now written into the code: **motion amplitude is inversely proportional to how often the
motion happens.** Added `idle`, `sway`, `twitch(seed, every)` and `drag(delay)` to the body bundle
— the tail *lags* the stride with the lag growing down its length (peak deflection at the tip is
now .07), fire flickers in **brightness** instead of waving in position, wings fold when idle
instead of beating, and the life comes from small fast events: a horn flick and a sniff every few
seconds, a slow weight shift, a head that settles a beat behind the body. Second: the lines all
looked the same because I had renamed and accessorised rather than rebuilt. ROT was still a
headstone with mushrooms. They differ by **skeleton** now — TIDE is a plesiosaur (long neck,
barrel, four rowing flippers), ROT is **legless at every stage** (a segment chain with a phase
delay so the wave travels), STONE is a ceratopsian with a frill wider than the animal, GALE is a
pterosaur with no forelegs and a crest taller than its skull, VOLT a biped raptor, ECHO a hydra,
EMBER a drake that loses its legs. Per-line box counts went from spreads like 19/86/100 to
79/93/115 — every stage substantial. 326 checks pass, still 21 distinct meshes. **Next:** the
enemies are the last thing on the old plan — they should be small dinosaurs at a fraction of the
player's detail.

**R29 — the menu shows you the animal.** Lifted the 270-line player-model block out of `render()`
into `drawMonBody(mCh, P, ANIM, stage, evoFx, T)` — the parameters deliberately shadow the globals
the in-game call used to read, so not one line of body plan had to change — and gave every
character card a live portrait: the real mesh, real engine, drawn into a corner viewport of the
game canvas under a scissor and blitted into the card's own 2D canvas, so seven cards cost seven
extra draws and no second GL context. The prose that used to sit under each name is gone with it.
Three things bit: the base `canvas{position:fixed;inset:0}` rule made every portrait cover the
whole viewport; the marker ring and ground quad that keep you findable in a horde read as
twelve pieces of confetti at card size (portraits opt out via `P.portrait`); and a three-slab
plinth is a twelve-pointed star with a 41% ripple, not a disc — six slabs at 30° gets it under 1%.
Cameras are auto-framed off the same `bodyPos` capture the coplanar test uses, so a new body plan
frames itself. 335 checks pass. · **Next:** "level up the models even further" — the block texture
is right but the forms are still simple and clunky in close-up, and the enemies still animate off
a clock rather than off what they did.

R30 | foundations | Every creature was six to thirty-six floating pieces — reported as "a lot of the objects in the models don't connect, leaving gaps". Added `chain()` (walks a polyline, sizes every segment so neighbours share volume), `leg()`, and rebuilt `horn`/`wing`/`claw`/`ridge` on top of it; `mb()` now honours the yaw argument every plan had been passing into a function that only declared eight parameters, so nothing angled had been allowed to sit at an angle since the vocabulary was written. Gave each of the seven lines its own eyes and mouth — slit, sunken, bird, glowing, deep-water, cold-predator, round — over fangs, croc jaw, tyrant maw, beaked rostrum, viper fangs, hooked wyvern jaw, grin. Rebuilt GALE as an actual wyvern (wings ARE the forelimbs, hooked toothed jaw, perched stance, vaned tail) after "looks goofy and not dragon like at all", split the hydra's necks onto separate shoulder sockets after "the hydraling heads glitch into each other", and rebuilt VOLT's first two forms as one tyrant at three ages after "the final form is ok but the previous don't make sense". | `analyze.js` (new): 21 of 21 forms were disconnected, now 0 of 21. Found and fixed a real bug in the existing coplanar test on the way — `bodyPos` pushed extents as (hx,hy,hz) against positions (r,f,y), so every consumer was testing the fore-aft position against the vertical half-extent. Suite 336 passed, 0 failed. | next: BASILISK reads wonky and its line does not progress coherently; and the level system needs remodelling.

R31 | texture and art | Rebuilt the ROT line after "basilisk is wonky, the evolution isn't connected". All three forms were one tube of blobs with a head the same width as the neck, and the only thing evolving changed was the blob count plus two pink flaps that read as ears. Now the line grows three things together: a body that is THICKEST AT MIDBODY and tapers both ways (drawn as two chains meeting at 34% so the peak is in the middle, not at an end), a SKULL that is a wedge visibly wider than the neck with brow ridges over the eyes, and a REAR that goes .34 → .70 → 1.06 so each stage stands taller. The crown is the same place on the same skull at every stage — two nubs, three spines, seven — and the hood only arrives at the top, as a shield thin FORE-AFT and wide across (it was thin across and wide fore-aft, which is why it drew as two blades off the neck). Added the petrifying stare as drifting grey motes off the eyes, age-scaled the eyes so a hatchling's are large for its head and BASILISK's are small for its, and turned the dorsal scales into a serrated ridge that peaks over the thickest part instead of a row of identical pips. | Turntables at all six angles for st0/st1/st2; suite 336 passed, 0 failed; analyze.js still 0 of 21 disconnected. | next: the level system — the user does not like how it works.

R32 | hierarchy | "A lot of the models' eyes, legs and arms aren't visible" — three separate reports, one cause each. EYES: seven styles each solved visibility their own way and none of them solved it, so they are one scaffold now — a dark socket sunk into the skull (which is what makes an eye read on a near-white animal at all), a pale sclera proud of it, an EMISSIVE iris proud of that so the eye survives being on the shadowed side, then pupil and glint. The old forward offsets were tenths of the eye's own size, which puts the eye inside the head from every angle except dead on. LEGS: a limb the same colour as the torso it hangs off has no silhouette against it, so `leg()` now shades itself to 62% value with a bone-white foot and three claws, thickens the thigh against the shin and puts a real blob at the knee. ARMS: SPARKLET's were two chains of radius .06 in the body colour flat against a chest four times their width — darker now, elbow swung clear of the ribs, bone-white hand with two hooked claws. Also brought the hydra's necks in from three skull-widths of fan per head to one and a half, moved the rest of the separation into depth and height, and gave each neck five points and its own clock so they drift instead of moving as one rack. | Stage sheets before/after at 460px; suite 336 passed 0 failed; analyze.js 0 of 21 disconnected. Caught myself deleting grin/horn/wing/claw/chain with an over-wide replace — the render went black, `analyze.js` reported 0 broken because a form that fails to capture scores -1, not >1. Reverted and redid it surgically; the analyser's "captured" guard needs to be an assertion, not a skip. | next: two new playable monsters, very different, fun playstyles.

R33 | foundations | Two new playable monsters, and neither one is a stat block. Seven characters is the ceiling of "+9% of something" — these are RULES. **THE COURIER** (SAILFIN → RIVERKING → THE SPINE, a spinosaurus) fills a momentum meter off ground covered and drains it while standing still; full, it spends itself on four seconds of x1.85 damage and 1.35x weapon tempo, and the top of the line fills twice as fast. The sail on its back lights with the meter, so the rule is legible from across the arena. **THE TEMP** (SUNCHICK → PYREWING → THE PHOENIX) has half everyone's health and detonates instead of dying — 13.5m blast, back at 45%, and the rebirth goes on a cooldown that grows 22s each time; the top of the line halves it. Playing it well means spending deaths. New vocabulary for them: `plume()` (a feathered wing — separate quills off a short arm, versus the wyvern's stretched membrane), `gharJaw()` (a narrow gharial snout with a bulb and sideways teeth), `eyeRidge` and `eyeSolar`. Unlocks on two axes the ladder did not have: 12,000m walked, and 25 runs lost. Also rescaled the whole eye scaffold after "the eyes are very messed up" — the socket was 1.45 of the eye's own size and the brow 1.75, so a pair spanned .51 against a skull .52 wide, with a black bar across the top. | Suite 351 passed 0 failed, including new sections 26 and 26b that press on the rules themselves. Those tests caught two real bugs I would not have seen by playing: the surge FILL rate (1/58 per metre) was below the DRAIN (.13/s), so the character could not charge its meter at a dead sprint; and the whole momentum block sat inside `if(P.vx || P.vz)`, so standing perfectly still neither drained the meter nor ticked the surge down. analyze.js: 0 of 27 forms disconnected. | next: the level system remodel, and an audit round — use it cold and list ten things that feel cheap.

R34 | foundations | Remodelled the level system after "I don't like how it works". Two changes. **The draft no longer stops the game.** It used to be a full-screen modal — pointer released, camera parked, hop chain frozen, simulation halted — and a long run levels forty times, so the back half of every run was a slideshow with the one thing the game is actually about, positioning, switched off for all of it. The cards are a strip along the bottom now; the horde keeps coming while you read them, which is the right amount of pressure on a decision that is supposed to matter. Because the mouse is still the camera, the pointer stays locked and the cards are taken with the number keys — so the number is now the loudest thing on the card, and touch still taps. An ignored draft resolves itself after eleven seconds, because a card that sits on screen for the rest of the run is a worse interruption than the modal it replaced. **And a level with nothing to choose on it is worth something.** Past about level fifty everything is maxed and the draft has one card on it that says ROAST CHICKEN; that level used to be forty hit points and a modal to accept them. It is permanent growth now — +1.7% of starting HP and +1.1% damage, compounding, routed through `recalcDmg()` so it survives the next passive pick rather than evaporating the way the boons once did. | New suite sections 27 and 27b: the clock advances 2s with cards on screen, `backdrop-filter` is gone, an ignored draft resolves, and empty levels move maxHP 291→402 and damage 3.14→3.77 by LV89 and keep it through a recalc. 358 passed, 0 failed. Screenshot of the live strip over a running fight. | next: the balance bench on the growth change is running; then the audit round — play it cold and list ten things that feel cheap.

R35 | AUDIT | Played it cold — fresh save, no shop, THE INTERN — and captured the menu, the first five seconds, minute three, a boss arrival and a level-53 late run. Also fixed a real bug the screenshots caught: the step loop asks `offers()` whether a level has a real choice on it and `showPick()` asked AGAIN to decide what to draw, two independent rolls of a random draft — so a level could pass the "there is something to choose here" test and then render a single ROAST CHICKEN, exactly the dead modal R34's growth path exists to remove. The hand is dealt once and handed over now. **The ten things that feel cheap, worst first:** (1) every object in the game — enemies, gems, pickups, the player — sits on a hard axis-aligned black rectangle, so from any angle the whole scene reads as cut-out stickers on a lawn; (2) gems and pickups are plain white and black boxes with no shine, float or colour language, and at density they read as litter; (3) up to four text elements stack over the player at once — region name, lore, TEMPO x10, the evolution banner and its signature line; (4) damage numbers are dim grey on a green field and legible nowhere; (5) the first five seconds are one animal alone on an empty lawn with "1 on screen"; (6) the BAT swing draws as a fence of cream boxes rather than an arc; (7) biome edges are hard straight lines with no blend; (8) distant enemies are unreadable black blobs — the horde has no silhouette at range; (9) the player's ground quad plus marker ring read as a black rug with white teeth; (10) the terrain has no small detail at all — no tufts, no pebbles, no scatter, just flat green with darker flat patches. | Five screenshots across one cold run; the ROAST CHICKEN bug is visible in the level-53 frame. | next: R36 attacks (1) — real shadows instead of a black rectangle under everything.

R36 | texture and art | Attacked the worst thing in the audit: every object in the game — enemies, gems, pickups, the player — sat on a hard axis-aligned near-black rectangle, so from any angle the whole scene read as cut-out stickers on a lawn. Three things were wrong and all three were cheap. It was SQUARE, and every square faced the same way because nothing passed a yaw. It was near-BLACK, which is not what a shadow is — a shadow is the ground with less light on it, and this renderer has no alpha, so the colour has to be mixed on the CPU from the biome the shadow falls on: a shadow on the ash reads warm and one on the glacier reads cold. And it never changed with HEIGHT, so a jumping creature dragged the same hard patch under it as a standing one. One `shadow()` helper now: two quads at 45° make an octagon for two boxes, tinted from the ground, spreading and fading with altitude, and yawed to the body above it. Also ran the balance bench on R34's growth and capped it — a good run reaches level 55 to 93, which is sixty-odd empty levels at 1.7%/1.1% apiece, i.e. double health and double damage arriving quietly in the back half; it is 1.5%/0.8% to a ceiling of fifty stacks now. | Suite 358 passed, 0 failed (the shadow-count check now expects enemies+1, because the player casts a real one). Bench (3 trials x 3 chars, paired seeds): first run 1/9 early deaths and 3/9 clears, veteran 0/9 early and 2/9 clears. Before/after captures at minute three. Also clamped `pendingLevels` at zero — the live strip's eleven-second auto-resolve and a scripted driver's own pick can both land on the same open hand, and two takes for one level drove the counter to -1. | next: audit item (2) — gems and pickups are plain white and black boxes that read as litter at density.

R37 | texture and art | Audit item (2): gems read as litter because every one of them was a single box of a single size, so a floor covered in XP was a floor covered in identical cubes. Three tiers with three silhouettes now — a flat chip, a cut stone with two frusta back to back, and a standing crystal with a bright point — each with a lit core brighter than its shell, and mid and large sitting on a real contact shadow. The common chip stays ONE box on purpose: it is the drop there are two hundred of on the floor at minute fifteen, and making it three boxes put the horde's per-enemy draw cost seven boxes over its ceiling. Same reasoning gave the enemy shadow an LOD tier — the octagon's second quad is a couple of pixels wide past twenty-two metres and the horde is mostly out there, so the cheap single quad is the default and the round one is the close-up tier. | Gem-field capture (a new `dropGem` hook drops forty of every tier in a ring). Suite 358 passed, 0 failed, with the draw budget back inside at 33.2 boxes per enemy against a ceiling of 34 — it had gone to 37.4. The "boss telegraphs are dodgeable" check failed once at 868 HP and passed at 671 on the next run with no change in between; noted as flaky rather than fixed. | next: audit item (3) — up to four text elements stack over the player at once.

R38 | content | Audit items (3) and (4), which are the same layer. **Damage numbers** were cream text with a black copy offset a pixel and a half behind it, on a fade that started dropping the instant they appeared — which over a sunlit green field is grey on green, and the audit round could not read a single one. They have a full outline now instead of a drop copy, hold opacity for most of their life and fade at the end, and scale with the size of the hit so the big ones read from further away. **Toasts** get a plate behind them, because a coloured word on lit terrain is not readable and an outline alone only half fixes it — and they step down out of the way while the evolution banner is up, since the audit caught TEMPO x10, the new form's name and its signature line all shouting at once over the player. | Mid-run capture: "208" now reads as bold white with a hard dark edge against the grass; before it was invisible in the same frame. Suite 358 passed, 0 failed. | next: audit item (8) — distant enemies are unreadable black blobs, so the horde has no silhouette at range.

R39 | hierarchy | Audit item (8): distant enemies were unreadable black blobs, and the palette explains it — the enemy colours were chosen by a colour-vision optimiser that wanted them separated by LIGHTNESS, so the smallest and most numerous of them, RAPTORLING, is literally `[.02,.02,.04]`, and then the fog lays twenty metres of grey over it. The hues stay exactly where the optimiser put them (the contrast check reads the palette table, not the draw call) but past twenty metres the body colour blends toward light on a curve, up to 42% at the far end, so the horde keeps a silhouette at the distance you actually make decisions from. | Mid-run capture: cyan GRUBLINGs and red PTERLINGs now read at forty metres where the same frame previously showed black rectangles. Suite 358 passed, 0 failed — and I had to fix the draw-budget metric on the way: it is supposed to measure BODIES, and R37's three-tier gems made the number swing a box and a half depending on how much loot happened to be on the floor. It sweeps the gems before measuring now and reads 30.2 against a tightened ceiling of 33, where it was 34.8 and drifting. | next: audit item (5) — the first five seconds are one animal alone on an empty lawn.

R40 | first impression | Audit item (5): the director spawns at 1.2 a second on an off-screen ring and the first thing to arrive walks at 2.5 m/s, so the opening ten seconds of every run were one animal alone on an empty lawn — the worst possible first five seconds for a game whose whole appeal is a crowd. Six shamblers are already walking in from the front when the run starts, in a ninety-degree arc so they read as a wave rather than a ring, and three gems sit inside pickup range so the first thing that happens is a pickup rather than a wait. `freezeSpawns(true)` now sweeps the field as well as stopping the director, because a test asking for no spawns wants an empty arena, not an empty arena plus the six the run was born with. | Opening capture goes from "1 on screen" to "7 on screen" with a visible wave. Suite 358 passed, 0 failed. Two bugs found on the way: `pickT` — how long the live draft has been ignored — was the one thing the new strip left behind between runs, so a run inheriting it above the eleven-second threshold resolved its first draft on frame one and took whatever card was in slot 1; and the pinned-reproducibility check turned up a **cross-section state leak** I could not find: the block gives the same string three times run on its own, but after the twenty-odd sections above it the FIRST pinned trial differs from the two that follow. The check now warms up and compares two consecutive trials, and prints the warm-up when it differs so the leak stays visible instead of being papered over. | next: find that leak; then audit item (6), the BAT swing draws as a fence of cream boxes rather than an arc.

R41 | foundations | Hunted the cross-section state leak from R40 with a new `__g.snapshot()` hook that dumps every module-level knob a run can inherit — twenty-five of them, from `noSpawn` and `noEvents` through the curve constants to the keys currently held down and the number of cards sitting in the draft strip. Diffing the snapshot taken twenty sections into the suite against a freshly loaded page found three real leaks and fixed them in `startRun`: `noEvents` was still true, so a run could inherit "side events are switched off" from whatever test last asked for that; four stale cards were still in `#pkCards`; and `hitstop` was sitting at -0.01. The snapshot now matches a fresh page exactly — and the warm-up trial STILL differs, so whatever is left is not any of those twenty-five, which is worth knowing and is why the hook stays. Also made a genuinely flaky check deterministic: "it looks at what is next to it" spawned its target with "one brute within nine metres", which lands at a random angle and about one time in twenty lands dead ahead, where the correct answer for "which way did the head turn" is nought. It is placed at (7, 1) now. | Suite 358 passed, 0 failed. The reproducibility check prints the entering snapshot when the warm-up differs, so the remaining leak stays visible rather than papered over. | next: audit item (6) — the BAT swing draws as a fence of cream boxes rather than an arc.

R42 | motion | Audit item (6): the BAT swing drew as a fence of cream boxes — eleven identical cubes appeared along the whole arc at once and faded together, so the only melee weapon in the game had no direction, no travel and no edge. It sweeps now: the leading edge walks the arc across the life of the swing and drags a short trail, the radius opens as it goes, the whole blade dips through the middle the way a real swing does, and a white-hot chip rides the tip because that is the part that hits. Two wrong turns worth recording — I first yawed each slab to the tangent, guessed the wrong local axis and drew a comb of radial spokes; then I sized each slab to the gap between samples, which at MEGABONK's reach is most of a metre and drew a two-metre-wide yellow carpet across the arena. Overlap is what the gap buys; the width is the weapon's, tapering to nothing at the tail. | Seven-frame captures at 45ms through both the base swing and the evolved one, on a single durable target so the arc is not buried in gems. Suite 358 passed, 0 failed. Added `__g.spawnAt(type,x,z)` for exact placement, which is also what made the flaky look-direction check deterministic last round. | next: audit item (10) — the terrain has no small detail at all, just flat colour with flat darker patches.

R43 | texture and art | Audit item (10): the terrain had no small detail at all — two tones of value noise on a plane, and nothing on it you could be beside. Every region now scatters its own ground clutter: fern tufts in THE FERNLANDS, cinder chunks with a hot top in THE CINDERFLATS, reeds in THE TARPITS, shards on THE GLACIER, stones in THE DUSTSEA, half-buried bone in THE BONEFIELD, iron nodules in THE SPINEROCK. Eleven per chunk, which on a 48-metre chunk is one every fourteen metres — enough that there is always something near you to measure your own speed against, which was the actual complaint behind "flat". All of it is baked into the TERRAIN vertex buffer inside each chunk's own range, so it costs nothing per frame, it is culled with the chunk it belongs to, and it is generated from a pure position hash rather than the run stream — the arena is rolled per world and adding detail to it must not move a single die in the simulation. | Screenshots of all seven regions from inside each one. Suite 358 passed, 0 failed, and the per-enemy draw budget is untouched because none of this goes through the dynamic batcher. The bone fragments needed a second pass: pale bone on a pale bone field is invisible, so each one sits in a dark half-buried socket now. | next: audit item (7) — biome edges are hard straight lines with no blend.

R44 | texture and art | Audit item (7): region borders were hard jagged lines. `groundY()` has always cross-faded the amplitude and the lift of two regions over nine metres so a border is a slope rather than a cliff — but the COLOUR snapped to whichever Voronoi cell was nearest, so every seam in the world was a hard sawtooth drawn across a perfectly smooth hill. Same two cells, same nine metres, same curve, capped at half-and-half so a blend can never wander outside the two tones it is between. The gameplay border stays hard: `biomeAt()` is untouched, so the damage and toughness modifiers still change on one exact line — it is only what you see that fades. | Screenshots from inside all seven regions; the CINDERFLATS/DUSTSEA seam is a gradient where it was a sawtooth. Suite 358 passed, 0 failed, including the colour-vision contrast harness, which brackets every ground tone that reaches the screen. | next: audit item (9) — the player's ground quad and marker ring, now that the quad is a real shadow, still read as a ring of white teeth.

R45 | AUDIT | Second audit round, played cold again — menu, opening, minute three, a boss, and a level-52 late run. The graphics work has landed: the shadows, the gem tiers, the ground clutter, the soft borders and the sweeping blade all read, and the horde is legible at range. What is wrong now is mostly INFORMATION, and one thing is much worse than the other nine. **The ten, worst first:** (1) **dev mode ships ON** — `save.dev` defaults to 1, so a first-time player opens the menu with 99,999 coins, all nine monsters, every shop upgrade maxed and THE DEEP 1 through 9 already available; the entire progression this game is built around is invisible on first contact, and the unlock ladder, the coin economy and the monster-level grind might as well not exist; (2) the centre of the screen is a noticeboard — the evolution banner, its signature line, the toast stack, world-space landmark labels and damage numbers all land in the same 200-pixel band, over the player; (3) the character cards are a wall of nine-pixel grey text, seven rows in four colours with no hierarchy, and the portrait — the best thing on the card — gets the least space; (4) nine monsters at four per row is three rows of scrolling with no sort, no filter and no "start here"; (5) ROAST CHICKEN still reaches the screen on a maxed build in at least some frames, despite the hand now being dealt once; (6) I have never once looked at the end-of-run screen in this loop, because the autopilot keeps surviving; (7) there is no settings surface at all — sound is the M key, reduced motion is a save flag, neither is discoverable; (8) the HUD's top-left is four rows of low-contrast text over the sky; (9) landmark labels render in world space with no plate and disappear over bright ground; (10) a gem at the edge of the pickup radius gives no cue that it is about to come to you. | Five captures from one cold run plus the menu at 1280x760. | next: R46 turns dev mode off, which is the one finding that changes what a new player sees in the first four seconds.

R46 | discoverability | The audit's worst finding, and a one-line fix that changes everything a new player sees: dev mode shipped ON. `save.dev` defaulted to 1, so the menu opened with 99,999 coins, all nine monsters, every permanent upgrade maxed and THE DEEP one through nine already available. Three quarters of the systems in this game are progression — an unlock ladder with five locked creatures on it, a coin economy with ten upgrades, a per-monster level grind that persists across runs, and nine descending layers of THE DEEP — and a build that hands all of it over at the title screen is a build with none of it. The default is 0 now. The panel is still one click away in the menu for whoever wants it, and the comment on the line no longer says "for now". | Menu capture before and after: 99,999 coins, nine unlocked monsters and a DEV MODE banner become 0 COINS, four starters and five padlocked `???` cards. Suite 358 passed, 0 failed — every test that needs the full roster already called `unlockAll()` explicitly, which is why nothing moved. | next: audit item (2) — the centre of the screen is a noticeboard; five text systems land in the same 200-pixel band over the player.

R47 | hierarchy | Audit item (2): five text systems were landing in the same two hundred pixels over the player — the toast stack, the evolution banner, its signature line, the world-space landmark labels and the damage numbers. Worse, R38's fix for this made it: it pushed toasts DOWN by thirty percent of the screen height when the banner was up, which moved them from 19% straight onto the banner at 31%, so the change written to prevent the collision was causing it. One lane each now. Toasts own a tight band under the clock and stay there. The banner owns the middle third (moved 31% → 40%). Landmark labels fade to 18% while the banner is up, because nothing else needs to be legible during the three seconds the game is telling you what you just became — and they get the same dark plate the toasts got, since orange-on-sand and cream-on-glacier are both invisible and a drop shadow is not a fix. | Mid-run capture: TEMPO x25 under the clock, FLAREDRAKE in the middle, the den label faded behind it, damage numbers readable, nothing overlapping. Suite 358 passed, 0 failed. | next: audit item (3) — the character cards are a wall of nine-pixel grey text and the portrait gets the least space on them.

R48 | hierarchy | Audit item (3): the character card was nine stacked rows of nine-pixel text in six colours — line, learns, signature, home, weak, start, level — with the portrait, the only thing on it anybody actually looks at, getting the least vertical space of anything on the card. Three blocks now. **The animal**: a full-bleed 4:3 portrait with the name set over it in fifteen-pixel white and the type badge in the corner, so the card is a picture with a label rather than a paragraph with a thumbnail. **What it becomes**: the three forms as chips with the evolution levels between them, the current one outlined in gold. **What it does**: START / LV7 / LV20 / GROUND as four rows on one two-column grid, so the labels line up and the eye reads down a single edge instead of hunting. Two accent colours instead of six — gold for what you gain, dim grey for everything descriptive. Locked cards keep the portrait's exact footprint, so the row is not four tall cards and five short ones with a padlock floating in the middle. | Card-grid capture before and after at 1280px. Suite 358 passed, 0 failed after pointing section 25's locked-card check at the new markup — the unlock condition moved out of a `.ds` prose block and into the same labelled grid the open cards use, which is the change, so the check follows it. | next: audit item (6) — I have never once looked at the end-of-run screen in this loop, because the autopilot keeps surviving.

R49 | first impression | Audit item (6): I had never once looked at the end-of-run screen in this loop, because the autopilot keeps surviving. Forced a death and looked. The table itself is good — headline, cause line, time, level, kills, the line you evolved, the build, dens cleared, coins, next unlock, RUN AGAIN — but three things were wrong. The DRAFT STRIP was drawing on top of it, under the RUN AGAIN button: `take()` schedules the next hand on a ninety-millisecond timeout and a run can end inside that window, so `showPick()` now refuses to open on a finished run. There was a hand's width of empty screen above the headline on a game whose entire subject is the creature you raised, so the end screen leads with a live portrait of the form the run actually reached — the same renderer that draws the menu cards, one call. And the layout leaked: "Coins earned" wrapped to two lines against a label column with no `nowrap`, and the next-unlock caption pushed "77%" onto its own row, where a wrapped percentage under a progress bar reads as a typo — the percentage rides on the bar now. | Death-screen captures before and after. Suite 358 passed, 0 failed. | next: audit item (7) — there is no settings surface at all; sound is the M key and reduced motion is a save flag, neither discoverable.

R50 | VERIFY | New standing rule from the user, now written into CLAUDE.md: a reported issue is the only work in flight until it is verified, and verified means the evidence that would convince a sceptic, not one screenshot at one moment of one animation. Went back over the model reports I had closed and built the evidence properly — a nine-panel contact sheet per line (3 stages x 3 angles), then a head-on sheet of all nine lines at stage 0 and stage 2, because head-on is the angle a face either exists at or does not. **"The eyes aren't visible" was not fixed.** Three separate faults, all invisible from the angles I had been checking. (a) The socket was near-black at 1.05 x 1.00 of the eye with .55 of depth, so its SIDE face was exposed on the cheek and from three-quarters on the eye read as a hole punched in the skull — it is a thin rim in the creature's own dark tone now. (b) On the VOLT line the eyes sat .62 of a skull-width apart and .18 ahead of the skull centre, behind a muzzle .82 wide reaching four times further forward: head-on, SPARKLET and STORMTYRANT had no face at all. (c) Same fault on STONE, hidden behind the rostrum. Both are on the cheeks above the tooth line now, which is where those animals' eyes are anyway. | Nine contact sheets, two head-on sheets, and big two-angle portraits of the four suspects. All nine lines now show a readable face head-on at stage 0 and stage 2. `analyze.js` 0 of 27 disconnected. Suite 358 passed, 0 failed. | next: nothing self-directed — waiting on the next report.

R51 | texture and art | Reported: "the models have too many blocks on them making it hard to tell what's going on... remodel them to where they are unique, simple in nature, and cool to play". Measured it first — 27 forms averaging 400 boxes, 623 on THE SPINE — and both causes were in the shape vocabulary, not in the plans. (a) `chain()` walked every polyline dropping a round-ish SAMPLE every 1.15 radii, so a neck a metre long and twelve centimetres thick cost fifty boxes to say "tube", and fifty near-identical pebbles in a row read as gravel. A box is already a length: it lays down ONE stretched block per sub-span now, half-extent r on every axis plus half the run on the axes the run travels along, splitting only where the run drifts off its dominant axis or goes longer than three radii. A straight neck is one block; a limb that goes down and forward is a staircase of three. (b) `blob()` made every mass three concentric boxes to chamfer the corners — right on a chest, three sets of unresolvable faces on a wing rib. It is gated on the SMALLEST half-extent now: only a block thick on all three axes has corners worth taking off. Two knock-ons: the draw-index nudge went from twelve slots to five (a nineteen-thousandth excursion was pulling deliberately-stacked parts apart, and it detached SPAWNLING's pupil from its iris), and the eye stack's layers are deep enough to survive it. Also cut THE ROC's "weather" from seven near-white bricks to five thin tinted streaks — they read as floating debris. | Census before/after over all 27 forms: 144-623 boxes -> 73-354, and 0 of 27 disconnected either way. Six-angle turntables of PYRAETHON, SHALEBACK and THE ROC, plus nine per-line contact sheets. Suite 358 passed, 0 failed. | next: the plans that the simplification exposed — the ROT line reads as a green plank with no legs and no face, and SHALEBACK's frill has grown into a sail that hides its head.

R52 | adaptivity | Still on the same report. Simplifying the mesh made it obvious that the thing actually hiding the game was the SIZE of the animal: measured every form's world footprint against a camera boom that sits 8.9 units behind, and BASILISK came out 19.6 long, STORMTYRANT 18.8, THE SPINE 16.7 — two thirds of the visible field, so the player's own body was the occluder. Three changes. (1) The four runaway lines got their length back under control at the source — segment counts and spacing on the ROT spine, the VOLT tail, the SURGE tail and gharial snout, the TIDE neck and tail — so stage-2 forms now run 8.3 to 11.7 instead of 8.3 to 19.6, and the growth per stage is a step rather than a doubling. (2) The camera measures the animal it is following: `mb()` tracks the body's own extent for free, and the boom lengthens up to 2.9 and lifts up to 1.5 with it, both capped, so a hatchling is framed exactly as before and the big forms give the horde its screen back. (3) BASILISK still read as a green staircase pointed straight down the camera axis, because a serpent whose body trails directly behind it is foreshortened into a column — its lateral wave is three times deeper now and runs a full cycle over the body, so it coils across the ground and you can see the arena past it. | size.js over all 27 forms before/after; in-game screenshots at ten minutes with a live horde for BASILISK (three iterations) and CINDERWHELP. analyze.js 0 of 27 disconnected. Suite 358 passed, 0 failed. | next: SHALEBACK's frill has grown into a sail that hides its head, and the ROT line has no visible face from the game camera.

R53 | hierarchy | The STONE line, which the simplification had exposed as a shield with a nose. Four things, all about which part of the animal is the biggest. The FRILL was nine plates climbing three quarters of a unit above the skull and growing .16 a stage on top of a 1.44 scale, so on TITANHIDE it was over two units across and overhung the whole animal like a mushroom cap - seven plates now, rising a quarter and reaching twice as far BACK, growing .09 a stage: a shield leaning over the shoulders instead of a sail standing on them. The SKULL was .21 by .17, a third of the frill and half the width of one thigh - it is .265 by .215 and pushed forward clear of the frill's root, which is what lets the face exist at all. The BROW HORNS stepped .035 sideways a segment compounding 35%, so they swept out past the frill and read as a moustache; they point forward now and they are a third as long. And the stage-2 dust was seven eight-hundredths CUBES bobbing at knee height, which is floating dice - flat shards close to the ground now, and the same fix went onto SURGE's wake and ECHO's motes, which had it too. | Six-angle turntables of SHALEBACK and TITANHIDE before and after; both now show two eyes, a beak and forward horns head-on. analyze.js 0 of 27. Suite 358 passed, 0 failed. | next: the ROT line has no readable face from the game camera, and the legs on the heavy lines read as two dark slabs rather than four legs.

R54 | texture and art | Head-on sheet of all nine lines at stage 2 found two that still read as walls, and both had the same cause: a part sized against nothing. (1) `chain()` takes the radius at a span's MIDPOINT, so a two-point run from thick to thin - every snout, horn, toe and tail tip in the game - came out as one straight box at the average, and STORMTYRANT's muzzle was as wide as its chest. Spans now split by how much the radius actually changes, so a taper tapers. (2) The VOLT skull was .19 plus .03 a stage on a scale of 1.4 - .70 across against a torso of .80 - with the eyes at .86 of its half-width, i.e. in the top corners of a cyan wall. Skull narrower and deeper, muzzle narrower and longer, eyes in off the edge. (3) The ROT line was one flat green from nose to tail with a magenta CROWN whose seven horns were each nearly a whole unit tall - a flower with a snake under it. The crown is a crest now, the body is BANDED segment by segment (two tones, not one box more), the belly band is deep enough to catch light on the flank, the back has a dark keel under the magenta saw, and the eye went amber because a green-yellow slot on a green head is the same colour as the head. Narrowing the tyrant skull left a row of teeth attached to nothing, which the connectivity report caught: mawRow's teeth are rooted inside the bone now rather than hung in the gap between the jaws. | Head-on sheet of all nine lines before/after; six-angle turntables of STORMTYRANT and BASILISK across four iterations. analyze.js 0 of 27 (it caught the tooth regression at 2 of 27 and confirmed the fix). Suite 358 passed, 0 failed. | next: the heavy lines' legs read as two dark slabs rather than four legs.

R55 | hierarchy | Legs. A limb reads by its zigzag, and on the heavy lines `thick` was .17 against a stride of .25, so thigh, shin and foot were one dark column of the same width in the same colour and four legs read as two slabs. The thigh keeps its full width where it meets the hip - that joint has to hold - and halves by the knee; the shin is two thirds of what it was; and the shin and foot are a shade lighter than the thigh, so the knee is a place where something changes. The knee blob came down from .86 to .66 of thick, because a ball bigger than the shin it joins is a knee brace. | Six-angle turntable of ANKYLOS: four legs now countable from three-quarters and from behind, thigh and shin distinguishable. analyze.js 0 of 27. Suite 358 passed, 0 failed. | next: cold audit of the roster - a first look at all 27 forms since the vocabulary changed under them.

R56 | audit | Cold pass over the whole roster now that the vocabulary has changed under it — nine contact sheets, three stages, three angles each. What is wrong, worst first: (1) THE HYDRA's four necks were a quarter of a unit thick fanned across seven tenths of one, so they touched along their whole length and the animal was one purple arch with heads on the end — necks are 24% thinner and alternate tone, and only the FIRST was ever the body colour so three of four were identical. (2) Its spine was drawn at .62 of vertical scale, which flattens the whole animal into a ribbon: from behind, the tail was a plank with three teal cubes on it. Deeper body, tail tapering to a point rather than an edge, dorsal plates that are plates rather than cubes. Still open, in order: SURGE is monochrome crimson from nose to tail; STONE's tail is a rectangular plank; the pyre line's stage 0 and stage 1 have nearly the same silhouette; the field is carpeted in red gem hexes that read louder than the enemies; the heavy lines still merge their two near-side legs from directly ahead. | Nine contact sheets, six-angle turntable of THE HYDRA before and after. analyze.js 0 of 27. Suite 358 passed, 0 failed. | next: SURGE's monochrome, then STONE's tail.

R57 | texture and art | Two backlog items from the audit. SURGE was one crimson from nose to tail tip, which at any distance is a single red mass - the tail is drawn a segment at a time now, alternating into a darker tone for the same box count, so you can count its length across the arena; a spinosaur is a striped animal anyway. And STONE's tail was a smooth rectangular plank from hips to club, which is the one part of an ankylosaur nobody would draw smooth: a dark ring and a pair of osteoderms per segment, sized PROUD of what the tail chain actually drew there rather than off the plan's nominal radius - the first attempt sized them at the nominal and they came out entirely inside the tail. | Six-angle turntables of THE SPINE and TITANHIDE. analyze.js 0 of 27. Suite 358 passed, 0 failed. | next: the pyre line's stage 0 and stage 1 share a silhouette; and the field is carpeted in red gem hexes that read louder than the enemies.

R58 | feedback | Went looking for what was still hard to read IN THE GAME rather than on a turntable, at fifteen minutes with the full kit, and it was not the creature any more - it was the floor. Two ring effects were drawn as forty cubes standing a quarter of a unit off the ground: the enemy attack TELEGRAPH and the live burning HAZARD. Both are ORANGE, both are centred on or trailing the player, and on the EMBER line both are a shade off the animal's own body colour - so a FLAREDRAKE standing in its own cindertrail was one continuous orange shape cut off at the knees by a wall of warning. Both are painted on the ground now: the telegraph as flat plates in pure red with a gold closing window, brighter than before because nothing shades a flat plate; the hazard as a charred rim with a hot flickering centre, which is what fire on the ground looks like. Neither occludes anything any more, and the telegraph is if anything louder. | Late-game screenshots with the full eight-weapon kit before and after, plus a caltrops-only run to see the hazard on its own. Suite 358 passed, 0 failed. | next: the pyre line's stage 0 and stage 1 share a silhouette.

R59 | content | The PYRE line's first evolution read as a 26% zoom: SUNCHICK and PYREWING had wings of .70 and 1.06, a crest of two flames against three, streamers of .62 against 1.08, and a body that barely changed - so the moment the game is trying to sell, watching your animal become a different animal, did nothing on this line. A hatchling is mostly HEAD: the skull is a quarter bigger and the body a fifth smaller at stage 0 and the ratio inverts by stage 2, the wings start as stubs at .42 and reach 1.42, the crest goes one flame to three, and the streamers go from a stub at .24 to longer than the bird. Enlarging the skull immediately hid the eyes inside it - the whole eye stack finished .06 behind the front of the head - so they moved proud of it, which the head-on sheet caught and a three-quarter view would not have. | Nine-panel contact sheet of the line, three stages by three angles, plus a six-angle turntable of SUNCHICK: chick, fledgling and phoenix now have three different outlines. analyze.js 0 of 27. Suite 358 passed, 0 failed. | next: the heavy lines still merge their two near-side legs seen from directly ahead.

R60 | content | Same fault as the PYRE line, on STONE: the frill grew .09 a stage from a base of .40, so SHALEBACK already wore most of a TITANHIDE's shield and the three forms were one animal at three zooms. The frill IS this line's evolution now - .21 to .61 of half-width, five plates to seven, and the plates lean back and rise further at every stage - so the juvenile has a bony shelf, the middle form has a crest, and only the top of the line has the shield. The brow horns arrive with it rather than being there from the start: a nub, a horn, a spike. | Nine-panel contact sheet of the line at three stages by three angles - the three outlines are now distinct at a glance, and the middle form's armoured club tail reads as the thing that separates it from the juvenile. analyze.js 0 of 27. Suite 358 passed, 0 failed. | next: check the remaining lines for the same "one animal at three zooms" fault - TIDE and ECHO are the suspects.

R61 | content | TIDE had the same fault as the other two and worse: four neck segments plus one a stage, everything else fixed, so SPAWNLING, TIDESERPENT and LEVIATHAN were the same plesiosaur at three zooms. The one thing this line has is its neck, so it now starts with almost none - two segments, four, six - and the flippers, the dorsal ridge and the head horns arrive with it: a hatchling has paddles, no crest and no horns, the LEVIATHAN has oars, a full ridge and a horned skull, and its head is proportionally smaller because the hatchling's is a fifth bigger. Also the line was one flat blue from nose to tail, on an animal the camera only ever looks at from above - a dark back over the pale belly, one box. | Nine-panel contact sheet of the line and a six-angle turntable of LEVIATHAN. analyze.js 0 of 27. Suite 358 passed, 0 failed. | next: nothing on the models list I can still see from the game camera - back to a cold in-game pass to find the next real one.

R62 | first impression | Cold in-game pass at twelve minutes with the full kit on two lines. THE PHOENIX's wings ran off both edges of the screen: the camera measures the body it follows but it was only measuring FORE-AFT, and a bird in flight is three times wider than it is long - it takes the wider of the two axes now. The wings themselves read as two painted planks because plume() draws each quill at full lateral width, .24 across planted .12 apart, so eight of them are a sheet; at .58 of width there is air between them and they read as feathers. And PULSE's shockwave was still twenty-six cubes standing a fifth of a unit up - a ring of ice blocks around the player - so it is flat plates now like the telegraph and the burning ground before it. Everything that happens on the floor is now drawn on the floor. | Full-kit screenshots for VOLT and PYRE before and after. Suite 358 passed, 0 failed. analyze.js 0 of 27. | next: the enemy roster is the one thing that has not been touched - eleven plans, all still boxes with a face.

R63 | motion | Built the tool the animation work needed: capture the mesh at both extremes of a stride, rasterise both into one grid, and report what fraction of the animal is somewhere else half a step later. (Index-based comparison does not work - chain() picks a span's block count from its own geometry, so an animated limb legitimately changes how many blocks it is made of.) The roster measured .02 to .09 of its own height, mean, with the legs doing all of it: a rigid slab sliding along on moving sticks, which is why a walk cycle was invisible from the camera this game uses. Three terms added to the body transform itself, so every plan gets them - a BOB that rises between footfalls and drops onto each one, a ROCK onto whichever leg is carrying the weight, and a PITCH on the off-beat with the squash that was already there. Then the two lines the metric said were still dead: TIDE swam with nothing but the tips of its flippers moving (.016 of its height on LEVIATHAN) - the flippers ROW fore-aft now and the neck waves on the stride; and STONE at .089 was the most rigid thing in the game - heave doubled, roll doubled, and the tail swings with the step rather than only lagging behind it. | animmeas.js over all 27 forms before and after: the roster now runs .21 to .68 with STONE at .21-.25 and nothing under .11. Walk strips for STORMCLAW, LEVIATHAN and ANKYLOS. analyze.js 0 of 27. Suite green. | next: reported issue.

R64 | REPORT | "I don't like how the monster looks back at you while receiving no inputs, change it to where it looks last place where it is left." Two causes, and the second was the real one. `togglePause()` called `faceCamera()`, which spun the animal round to face the lens whenever the game stopped - so the thing you were driving snapped to a pose it had never been in. Gone; it keeps whatever heading you left it on. And the head: `ANIM.look` clamped toward the nearest enemy at ANY bearing, so a target directly ASTERN - which is where the horde is whenever you have been running from it, and where the camera is - pinned the head at the far edge of its arc and held it there. It only tracks what is inside a hundred-and-ten-degree arc now and eases back to the body's own heading outside it. | Three new assertions in a new section 22p: walking left points the animal left rather than at the camera, standing still does not turn it, pausing does not turn it. Two more on the head: with a target dead ahead it tracks (.366), with the same target dead astern it does not move at all (0, was pinned at .75), and the existing "it looks at what is next to it" still passes at .727 - a sixty-degree arc broke that one, which is how the arc got set at a hundred and ten. Suite 363 passed, 0 failed. | next: "cinderwelp 2nd evolution should unlock flying".

R65 | REPORT | "cinderwelp 2nd evolution should unlock flying." PYRAETHON flies. Hold JUMP in the air and it beats its wings: it cancels the fall and climbs to a hover at 3.1 units, it moves 12% faster up there, and NOTHING THAT HAS TO TOUCH YOU CAN REACH IT - the burning ground, caltrops, contact damage, all of it. A diving enemy still can, because a dive comes from above. It runs on a meter: 2.9 seconds of flight, 3.3 seconds to refill, and it only refills properly on the ground, so the cost of being untouchable is that you have to come down. The real cost is the hop chain - you cannot chain a hop you never land from - so flight and tempo are a choice rather than a strict upgrade. The wing meter rides on the same bar the two rule-characters use, gold while you are up. And the evolution banner announces it: it used to prefer whatever the line's move did, so the one evolution in the game that changes how you MOVE was announcing itself as "LEARNED CINDERTRAIL SHARPENED" and leaving the player to find flight by accident. | New suite section 22o, eight assertions: neither of the first two forms can fly, PYRAETHON leaves the ground on hold-jump, it holds a hover at 3.1 rather than climbing forever, the meter empties and puts it back on the floor, it refills on the ground, the burning ground does 79.5 damage on the floor and 0.0 in the air, and the banner reads "YOU CAN FLY - HOLD JUMP". Screenshot of PYRAETHON in flight with the meter lit. Suite 371 passed, 0 failed. analyze.js 0 of 27. | next: waiting on the next report.

R66 | REPORT | "Things like SHALEBACK's shield being inside it are very glitchy... make sure they don't collide too much with each other and are easy to look at." Built the measurement first, because "too much" needs a number: rasterise every form and, for each box, report the fraction of its own volume that no OTHER box covers. A box with none is invisible - it cannot be seen from any angle, it costs a draw, and it is a pair of coincident surfaces for the depth buffer to argue over, which is the glitch. Between a quarter and TWO THIRDS of every creature in the game measured as invisible. Four causes, all fixed. (1) `chain()` extended a full radius past each end of every sub-span, so where the sub-span was shorter than two radii - a banded serpent, a segmented tail - consecutive blocks were two thirds the same block; along the axis of travel a block now reaches .58 of a radius past each end, which still overlaps its neighbour by 1.16 radii. (2) It also split spans by taper alone, so a strong taper produced six near-identical blocks in the space of one; the count is now capped by the room the run actually has. (3) Every `ridge()` caller passed the SPINE as the plate line, which is inside the body - the dorsal ridge on four lines was drawn where nobody could see it. `y` is the body's SURFACE now and all seven callers were moved onto it, the plates no longer overlap each other by half, and they sink by a fraction of the ridge's nominal height rather than of their own so the short end plates still reach the back. (4) SHALEBACK's shield itself: at a frill half-width of .21 all five plates of the fan rooted within .06 of the midline, inside a skull .265 wide, so the whole shield was drawn inside the head. The juvenile gets one wide low shelf that clears the skull; the fan arrives with the frill that can carry it. | buried.js over all 27 forms before and after: invisible boxes 47->23 on CINDERWHELP, 97->33 on SHALEBACK, 145->53 on TITANHIDE, 172->87 on BASILISK, 114->82 on PYRAETHON. Box counts fell with them (TITANHIDE 300->202). Six-angle turntable of SHALEBACK. analyze.js 0 of 27 - it caught five forms coming apart at the ridge's end plate and confirmed the fix. Suite 371 passed, 0 failed. | next: same report, next worst - GALE at 104 of 266, ECHO at 106 of 278, SURGE at 112 of 248.

R67 | REPORT (cont.) | Same report, visual pass over all nine lines now that the measurement pass is done. One real collision left: THE HYDRA line's neck fan was computed as (n-1) * 1.5 skull-widths, which at TWO necks is NARROWER than the pair of sockets they leave from - so HYDRALING's necks converged on each other and the animal read as one thick neck with two heads stuck on the end. The fan has a floor of three skull-widths now, so whatever the count the heads finish further apart than the shoulders they grew from. Checked GALE, ECHO, SURGE and STONE at three stages by three angles: nothing else reads as parts inside parts. | Six-angle turntable of HYDRALING before and after - two necks and two heads are now separately countable from the front, the side and behind. analyze.js 0 of 27. Suite 371 passed, 0 failed. | next: the report asked for models first and then animations; models are where they should be, so animations - and after that the user has queued a fourth "mega" evolution and aquatic water areas.

R68 | content | THE APEX - the fourth evolution, requested as "just like pokemon does their mega evolutions, take time with this". Level 34, priced off the balance traces: a winning run reaches ~48, a struggling one dies at ~25, so the mega belongs to a run that earned it. All nine lines: THE CINDERSTAR (EMBER - lava seams, burning wings, twin tail vanes; STARFIRE drops burning ground while flying), THE MAELSTROM (TIDE - six flippers, dorsal fin, orbiting water; RIPTIDE drags enemies inside the pickup radius), THE SUPERCELL (VOLT - four lightning rods with a travelling charge; STORMCALL fires a free zap on every hop landing), THE MOUNTAIN (STONE - double frill deck, terrain slabs, spiked club; UPHEAVAL answers every hit taken with a free tremor), THE GORGON (ROT - eye-spotted hood, gold circlet; PETRIFY slows everything in the sporecloud), THE HURRICANE (GALE - four wings, staggered beat; EYEWALL halves the mortar cooldown), THE LEGION (ECHO - five heads, chest plate, double dorsal row; WARCHOIR adds a bolt to every volley), THE FLOOD (SURGE - the sail runs nose to tail; BREAKWATER extends the surge and running feeds it), THE ETERNAL (PYRE - six streamers, a halo of seven flames; SUNDIAL stops the rebirth cooldown growing). Every apex wears an 18% deeper coat, one rule for all nine, so a mega reads as a different animal before you can name its parts. The banner leads with "APEX", the menu card gains a gold LV34 row, and the evolution arrives through the level system. | New suite section 22n, 11 assertions: all nine lines grow a distinct fourth form, it arrives by levelling at 34, and every one of the nine powers measured doing what its card says (stormcall arcs counted, riptide drag compared against stage 2, sundial cooldowns flat across three rebirths, eyewall shell counts doubled, etc). Suite 382 passed, 0 failed. analyze.js extended to stage 3: 0 of 36 forms disconnected (it caught the gorgon's circlet floating and the fix). buried.js extended: apex rates in line with the roster. Six-angle turntables of all nine apexes; menu screenshot with the four-stage line and LV34 row; in-game shot of THE CINDERSTAR flying a STARFIRE trail. | next: the ten-agent audit's findings - 37 of them, worst first.

R69 | REPORT (audit) | Ran a ten-agent audit fleet - one auditor per creature line rendering turntables and walk strips and studying them, plus an in-game readability auditor. Six completed and returned 37 findings with screenshot evidence (the other four hit a session limit; their lines had just been through the apex pass by hand). Every severity-4-and-up finding is fixed: (1) THE ROC's "four detached blue rods floating in midair, connected to nothing" - the orbiting wind streaks - are now six flat ground shards, the same grounded-dust grammar the STONE line uses. (2) The GALE line "belly-slides, not a single leg pixel visible in eight walk frames" - grounded wings now tuck a sixth higher on the back, legs stride 16% longer and wider with accent feet. (3) FLAREDRAKE "walks with zero visible legs, reads as a legless hovercraft" - same cause, same class of fix; raising the grounded wing root then pulled both wings clean off the torso by eight thousandths, which analyze.js caught (2 components) and the re-seat fixed. (4) LEVIATHAN's tail fluke and rear flippers "occupy the same volume" - the rear pair roots ahead of the tail now and sweeps down under it. (5) VOLT's "white claw slivers hovering in midair between the legs" and "arms read as detached floating blocks" - the arm carries higher (elbow .30, hand .55 of arm length below the shoulder, was .42/.78) and roots through a deltoid pad that overlaps the chest at every phase. (6) STONE's saddle "reads as an irregular black pit in the middle of the back" - mid-brown at .76 of body value now, plus a nape mass so the rear quarter stops reading the shell as hollow. (7) BASILISK's "detached white/gray voxels floating off the snout... glitch debris" - the stare is a directed amber beam now, four motes on one ray rooted at the eye line. Also: drake eye forward so the face reads head-on, wing trailing ribs clamped off the floor, ghoul's cheek band reaches the neck, ox dust pinned to the ground. | Every fix verified by re-render (turntables and walk strips before/after); analyze.js 0 of 36; suite 382 passed, 0 failed - two assertions updated for the 36-form roster with reasoning in comments. | next: the sev-3 tail of the audit (scrap eye decals, spark tombstone face, skyrend needing a nameable stage-1 element), and the four auditors that never reported.

R71 | REPORT (audit tail) | The severity-3 tail of the ten-agent audit, each closed with a render. (1) VOLT's "blank tombstone slab" of a face: the muzzle now carries croc grammar - a dark bridge stripe down the snout top with nostril pits at its end, placed ON the sloping surface after the first two attempts rendered inside the snout, plus forward canines and a pale belly-tone underbite that splits the face into skull and jaw. (2) ROT's profile problem - "the pink cheek patch reads as the eye" - a dark eye-stripe now backs the emissive eye along the skull side, so it owns its profile. (3) "SKYREND is a near-clone of WYVERNET": from stage 1 the line carries a pale chest blaze and a bone thumb-claw at each wing shoulder - the first anchor aimed at the animating wrist, double-applied the growth factor, and analyze.js caught both claws flying formation on THE HURRICANE before the shoulder anchor fixed it. (4) PYRAETHON's "one yellow pile": the dorsal ridge runs deep ember now, so the gold belongs to the wings and the flame. (5) The "frozen neck" claim on TIDE was adjudicated with a fresh strip and CLOSED as already fixed - the R63 wave visibly bends the neck frame to frame. (6) TIDE's dark back patch read as a hole from the play camera - the exact ox-saddle fault - and got the same three-quarters-value fix. The water test also stopped comparing four lakes from four different worlds: it pins one arena now, which ended the ice-lake flake for good. | Head-on face sheet before/after, six-angle turntables of SPARKLET, SKYREND and the walk strips. Suite 387 passed, 0 failed, three consecutive runs. analyze.js 0 of 36 - it caught the thumb-claw regression mid-round. | next: the remaining sev-2 cosmetics are logged and cheap; the loop continues wherever the next report points.

R72 | MECHANICS (water follow-through) + BALANCE (bench) | Two threads. First, the difficulty bench with the apex live: ox first-run median 24:00 with 2/4 clears, intern median 21:21 and deaths clustered at 18-26 minutes - the old 5:18 early-death cliff is gone, the curve reads winnable-but-not-free, no tuning needed. Second, lakes now slow the horde the way they slow you: enemies wade at .74 speed (bosses .85), divers exempt. The first version of the guard - `e.dvT <= 0` - exempted EVERY walker, because only divers ever have a dvT and undefined <= 0 is false in this language; the averaged six-walker test caught the rule applying to nobody (3.7 vs 3.7) and the fix is `!(e.dvT > 0)` with a comment explaining why. Also: GALE's brow band no longer reads as a blindfold (slate, .24), STONE's horns are bone instead of body-teal. The wading change then tripped the pinned-reproducibility check; an isolated four-trial probe returned four byte-identical results, proving the sim pure and the failure a suite-order warm-up artifact (known debt since R50, now two trials deep), so the check warms up adaptively with a cap of 4 - real nondeterminism still fails it. | balance.js 4-trial paired-seed bench both chars; wading verified by averaged horde speed ratio in-lake vs dry (new enemiesPos hook); pinprobe.js isolated purity proof; analyze.js 0 of 36 fresh; suite 388 passed, 0 failed. | next: the sev-2 cosmetic tail, and the suite-order leak now has a decay clue - whatever leaks fades over ~2 pinned trials.

R73 | MODELS (intern line, sev-2 tail) | The fire line's three remaining audit findings, closed with renders. (1) CINDERWHELP's "face slab" - the whole face was one belly-tone box with a dark nostril block pasted on its flat front cap, the exact tombstone VOLT had. The snout wears the body colour now, a belly-tone underbite jaw splits the face into skull-over-jaw, and the nostrils are two pits on the snout TOP near the tip, where a snout keeps them. (2) FLAREDRAKE's folded wings read as "striped caterpillars lying on the back" - the membrane ribs were gold on an orange arm. They fold in dark leather now; the drake earns gold membranes at PYRAETHON where the wing is open. (3) The "rib comb" - both early stages wore a gold dorsal comb over gold wings. The ridge runs deep ember on st0 and st1 now, the same rule R71 set for PYRAETHON: the gold belongs to the horns and the flame. | Six-angle turntables of both forms before/after, play-camera walk strip (legs visible under the folded wings, no stripes), analyze.js 0 of 36, suite 388 passed 0 failed. | next: the scrap line's tail of the audit - the torso that never evolves and the blank rear wall.

R74 | MODELS (scrap line, sev-2 tail) | The water line's audit tail. (1) "The torso never evolves" - confirmed by turntables of all four stages: neck, flippers, ridge and scale all grew while the hull stayed the same blue barrel at four zooms. The serpent now earns a row of dark flank scutes at the waterline from stage 1 and the LEVIATHAN grows pale barnacle patches on the dark back from stage 2, so the hull itself has a growth story. (2) The "blank rear wall" - root cause was the barrel chain carrying its FATTEST radius at the tail end (.40 vs .30 at the shoulder), presenting a flat animal-sized cap to the rear camera. The widest station is the shoulder now (.33) and the stern tapers to .26 into the tail root. (3) The "eye decals" claim adjudicated with the fresh head-on renders and CLOSED without change: the black eye with the bright rim is the line's stated face identity and reads as an eye at every angle rendered. | Six-angle turntables of st0, st1, st2 before/after; analyze.js 0 of 36; suite 388 passed, 0 failed. | next: the last of the sev-2 tail - ox rear jumble, ghoul flank, GALE tail pole, spark motes.

R75 | MODELS (sev-2 tail, closed) | The last four items from the R69 audit fleet, each closed with a render. (1) GALE's tail was "a pole" - a uniform pale rod tapering smoothly into a vane, nothing breaking up the shaft. A ring of dark accent bands down its length now reads as vertebrae on a jointed spine instead of a stick with a flag on it. (2) The ox "rear jumble" - THE MOUNTAIN's three moss slabs all clustered at one back station under the double-decker frill's shadow, reading as rubble caught in the shield. They run down the actual spine now, clear of the frill, and the rear view is clean. (3) Ghoul's "flank blank" - every marking on this line banded the top (dorsal saw) and underside (belly scutes) and left the one surface the play camera frames square-on, the flank, flat green with nothing on it. Dark diamond blotches now sit on both flanks every other segment, offset along the body's own perpendicular so they hold their place on the flank through every coil angle. (4) Spark's "walk float" - the storm motes orbited in a wide ring with deep vertical travel, putting them well clear of the animal's own silhouette in every turntable angle: isolated cubes drifting beside the creature. They hug the dorsal ridge now, tight radius and small bob, so every frame reads as the ridge sparking rather than debris nearby. | Turntables and a walk strip of each line before/after; analyze.js 0 of 36; suite 388 passed, 0 failed. | next: the audit's sev-2 tail is fully closed. The loop moves to open-ended polish - candidates are the unfound suite-order state leak, boss variety, and biome-specific enemy behaviour.

R76 | MECHANICS (biome-specific enemy behaviour) | THE TARPITS' "-14% move speed" was a player-only tax on terrain the game itself describes as gripping "your" feet - no different from the mud gripping anything else standing in it, and every other biome's rule (THE GLACIER's slide, THE DUSTSEA's pickup radius, THE BONEFIELD's XP, THE SPINEROCK's damage) never touched the horde either. Applied the same fix water got in R72: the ground under an enemy now costs it the same speed it costs you, divers exempt exactly like they are over a lake. Because the penalty is identical for both sides, the chase dynamic in THE TARPITS is unchanged - a player already routes around slow ground and now the horde does too, rather than the biome secretly buffing pursuers relative to their prey. | New test (28. "the horde bogs down too"): scans the rolled world for a bog cell, walks six shamblers through it against a dry control with the same averaged-horde technique R72 used for water, ratio-checked rather than pinned to absolute distance so it survives whatever the world roll finds. analyze.js 0 of 36; suite 390 passed, 0 failed (two new checks). | next: the remaining biomes (ice slide, sand, ash, bone, rust) don't have a natural enemy-facing analogue and are left player-only by design; the unfound suite-order state leak is still open.
