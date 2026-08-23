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
