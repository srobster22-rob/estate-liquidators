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

R16 · Built `proto3d/qa.mjs` — headless QA that loads the real first-person build in
Chromium and drives it through `window.__g` (28 checks: pillar-2 targeting, retrieval-then-
death, the appraise ping, van accounting, both night endings, the ratcheting floor, estate
containment). Extended `check_drift.py` to cover **proto3d, which was never checked** —
72 constants across four implementations now. · **Found four real defects, three of them
in the shipping artifact:** (1) both prototypes still carried the **pre-R9 cursed floor of
2** while tuning.json, `curse_test.py` and the C# core had moved to 7 — the exact drift the
checker exists to catch, sitting in the one file the checker didn't read; (2) **doorways
were a 5.2m box centred on the midpoint of two room centres**, and the rooms never touch,
so the "doorway" was floating in the void — you could walk out of the conservatory into
nothing. Replaced with corridor rectangles derived from the facing walls and the rooms'
overlap interval, plus a boot-time fault list for any doorway narrower than its door;
(3) `land`↔`pot` overlapped by **0.5m against a 2.2m door** — a link that could never
hold a real doorway. Moved `pot` to z=7; (4) the game's `requestAnimationFrame` loop kept
advancing time between scripted checks, so results depended on how long an `evaluate` took
— added a QA pause. · **And the checker itself was wrong twice.** Its first containment test
asked the game's own `solid()` whether the player was somewhere legal, which cannot fail —
a too-permissive doorway test simply declares its own leak to be floor. Rebuilt with an
oracle recomputed from room boxes and the link list; the original doorway model now trips it
immediately. Its first appraise assertion read 3.60 against an expected 4.32 and the code was
right — 0.72 of decay had accrued across the 3.5s window. Fixed the measurement, not the
tolerance. · Injection-tested per R14's rule: additive attention, per-frame sustained noise,
fatal-first-contact, the old doorway box and a cursed-floor divergence are each caught, and
all five revert clean. Full regression: QA 28/28, drift 72/72, estate validator PASS.

R17 · Built **concealment** — the verb the owner asked for in R15 and the one genre-defining
mechanic the design had specced (§8.1) and never played. Hiding furniture in every room, a 1s
silent entry, a loud exit, a clamped view from inside, stashing an item into furniture for 20s
of quiet, and the Curator opening a wardrobe over four seconds when the prize is still
radiating from inside it. 18 new QA checks, all injection-tested. · **Found the prototype was
violating a FIRM rule.** The Curator's target was `player.holding` — aggro bound to the
*person*, so putting the piece down cleared the hunt outright. That is the free aggro reset
D-06 and `BUILD-PROMPT.md`'s non-negotiables name by name, sitting in the build since R12.
Rewrote targeting around `radiance(item)`: an item radiates once it has left its plinth, goes
quiet while stashed, and goes quiet again when reseated — so dropping now buys you nothing,
which is the whole point of the rule. · Two more: **at COLLECT the Curator never switched to
hunting crew** (§6.5 was unimplemented, so the tier did nothing but move faster), and the
first pass at concealment **cut the light so hard that hiding was blind** — you couldn't watch
it approach, which turns the genre's best mechanic into a wait. Raised ambient while
concealed; verified by screenshot, not by reading the code. · The COLLECT change also broke an
R16 check that asserted an empty-handed player is *never* targeted. It was right at PURSUE and
wrong at COLLECT — the check was over-broad, not the code. Split into two checks that state
the tier difference explicitly, which is now the only place that distinction is written down
as an executable rule. · Logged D-22 (concealment is a hard stop at COLLECT, with the
economic counter written down in advance) and D-23 (the three Loudness values §8.1 never
specified, all flagged as guesses). Regression: QA 46/46, drift 76/76, estate validator PASS.

R18 · Built `sim/appraise_test.py` and closed the question the log has carried since R8: is a
+6% edge enough to carry the game's signature verb? · **The question was wrong.** Every sim
that produced that number compared *blind* against *scan everything*, and R8's ADAPTIVE
interpolated in **time** (scan once the van is half full), never in **breadth**. The actual
decision a player makes at a shelf — how many of these four do I scan before I commit? — had
never been measured. Measured: the appraiser is worth **+14% over blind**, and the optimum is
**interior at two**, beating both scanning nothing and scanning everything, with no new
mechanic in the model at all. · Then applied R11's shape anyway — appraising as a tail risk,
`p_caught = RETRIEVAL[tier] × K × n^1.8`, since three seconds standing still is three seconds
it can arrive. It doesn't rescue the mechanic (nothing needed rescuing) but it makes the right
answer **situational**: scan while it is quiet, stop once it is hunting, scan wider in the deep
wings. That policy is worth a further **+6.2% over the best single constant** at K=0.30, which
is the recommended value — it is where the most of the mechanic's value sits in the decision
rather than in a number a player memorises once. · **The first version of the sweep was
garbage and said so out loud:** it reported that scanning more paid better at K=0.15 than at
K=0.00, which is impossible. Cause: policies take different numbers of trips and spend
different time in them, so a single per-night RNG stream desynchronises and the comparison
drowns in Monte Carlo noise. Rebuilt with per-trip common random numbers — every policy now
faces the same estate, and both risk rolls are drawn every trip whether used or not — after
which the ordering is monotone in K everywhere. · Also: `integrated.py` still had the **pre-R9
cursed floor of 2.0** inline as a bare literal, which is why the drift checker had never seen
it. Promoted to a named constant, corrected to 7.0, and added to the checker (78 constants
now). · And `sim/validate_estate.py` **had no entry point at all** — running it executed zero
checks and exited 0, so "estate validator PASS" in R14, R16 and R17 was a claim about nothing.
Added a real CLI that validates both sample estates and asserts the broken one trips exactly
its seven planted faults; injection-tested by neutering V9, which it catches. · Wrote
`ECONOMY.md` §11 and D-24, and marked §10's +6% superseded rather than deleting it.

R19 · Gave the Curator senses and the game a soundtrack — `TECH-SPEC.md` §A5 and the
fairness rule that depends on it. Hearing radius `L × 0.33` attenuated 0.85 per wall over the
portal graph, the resulting investigation point fuzzed ±3m, sight at 18m through a 100° cone
that walls block and darkness doesn't, and a last-known-position fix that goes stale after 6s.
Audio is synthesised outright — no assets: a filtered-noise drag layer mixed by distance and
occlusion, the marked item's 8m hum, and impulse pings whose carry is the same Loudness number
that drives everything else. 14 new checks. · **The first cut applied the senses to everything
and immediately broke §8.1.** A player hidden in a wardrobe holding the prize became
unfindable, because the Curator had no fix on them — which deletes "you can hide, but your
loot can't", the sentence the whole concealment design hangs off. The resolution is that the
two problems are different: **an item radiates its own position** (carried, dropped or
stashed in furniture), so retrieval never needed senses; **crew do not**, so hunting people at
COLLECT is where hearing and sight decide everything. Being quiet now works on the second and
does nothing for the first, which is exactly the split the design wanted and had never stated.
· **Two of the four injection tests didn't fire, and both were the checker's fault.** The A6.2
floor ("never occluded to zero within 8m") could be deleted without any test noticing, because
with seven rooms nothing is ever both four walls away and eight metres close — the rule is
defensive against content that doesn't exist yet. Refactored the mix into a pure
`dragAt(distance, walls, opening)` and swept it over combinations the estate can't currently
produce. And sight had no test for *walls* at all, only for wardrobes. Both now fail when
neutered. · One honest limit, stated rather than papered over: headless Chromium has no audio
device and its context clock never advances, so `gain.value` stays at zero however correct the
mix is. The harness asserts the **mixing rule**, not audible output. Nobody has heard this yet.
· Regression: QA 60/60, drift 84/84, estate validator 10×2 PASS.

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
