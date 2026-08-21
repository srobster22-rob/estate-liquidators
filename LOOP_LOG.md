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
