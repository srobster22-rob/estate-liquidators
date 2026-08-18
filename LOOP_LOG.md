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

R20 · Put a **crew** in the house — three AI haulers — and with them, for the first time, the
pillar the entire game is built on: *you can get rid of the monster by handing the vase to
your friend.* With one actor in the build, A3's selector had nothing to select between, so
"the richest carrier is hunted", the 1.25× steal threshold, the 8s commitment and the noise
multiplier were all unexercised code. Ten new checks cover them, and every one fails when its
rule is neutered. · **The finding: with aggro bound to the object, A3's hand-off override is
unnecessary.** The spec computes weight *per player*, so passing the vase changes the target
and needs a special case to beat the commitment lock — R2 measured 0.0s with it and 6.0s
without. Target the **item** instead (which D-06 requires anyway) and derive the chased body
from `heldBy` each frame: handing it over doesn't change what it wants, only who has it. The
mark moves the same frame, inside an active lock, with no exemption code. Same trick as the
multiplicative weight — make the rule arithmetically impossible to violate rather than
reliably special-cased. Logged as D-25; `TECH-SPEC.md` §A3 now says so, and says to keep the
other two hysteresis rules, which do real work. · **Four defects the crew exposed, all in code
written in the last two rounds:** (1) R19's `c.fix` was a single anonymous "last thing I
heard" — with four actors, a crewmate's footsteps two rooms away handed the Curator a fresh
fix on a player sitting silently in a wardrobe. Fixes are now about somebody. (2) The aggro
tell **lied**: the HUD went on announcing IT IS COMING FOR YOU while it walked at RUSS,
because "it has a target" and "it is coming for me" were the same statement with one actor.
(3) `curator().goalValue` reported the idle *wander* destination as if it were a hunt target,
which sent me chasing a phantom retarget for twenty minutes. (4) The torches were saturated
white by the player's own flashlight, so the dimming that IS the tell was invisible — added an
emissive path to the shader and checked it by screenshot. · Six existing checks had to be
restated rather than fixed, and the distinction matters: "empty-handed is never targeted" is
now *while three crewmates carry loot and it is actively hunting*, which is a stronger claim;
"concealment works at COLLECT" is now *it hunts someone else*, not *nobody*; and "dropping
does not reset aggro" split into **the mark leaves you** and **the hunt continues on the
object**, which is the actual content of D-06. · Regression: QA 70/70, drift 89/89.

R21 · Built the thing R18 priced. D-24 found the appraiser is a **breadth** decision — how
many of a shelf's four do I scan before committing, worth +14% with an interior optimum at two
— and said in as many words that the payoff dies if players read scanning as a mode they
switch on for a room. The build had no shelves: items were scattered individually on floors,
so there was no candidate set to be selective about and the decision the sim priced was
literally unreachable. Loot now comes on **sideboards of four**, appraising is per candidate,
and the prompt reads `SHELF 2/4 scanned, best so far $840` — the state D-24 says has to be
legible. Six new checks. · **Two failures on the first run, and the interesting one was not a
bug at all:** the per-second-noise regression check started failing across timesteps, and the
cause was the crew depositing *cursed* items at slightly different rates under different `dt`
— each one raising the Disturbance floor by 7 and swamping the 0.9/s the check is about.
Which is the R18 cursed-floor fix working end to end in a live game, arriving as a test
failure. Added a bounded noise trail (`__g.noiseLog`) to diagnose it, because "one number,
three systems" means a wrong Disturbance number has three possible authors and nothing was
recording which. · The other was mine again: two checks still compared items by **dollar
value** when the selector weights by value × curse multiplier, so a $332 malignant outweighs a
$612 clean. Fixed by comparing like with like rather than by loosening the assertion. · **And
the harness could crash instead of failing.** Injecting a two-piece shelf threw at check 30
and reported nothing about the other 46 — a silent hole in every injection test run so far,
since a crash and a pass are both "no FAIL lines". `checks()` is now wrapped, a throw is
recorded as a failing check, and the summary always prints. · Regression: QA 76/76, drift
89/89, estate validator PASS.

R22 · **Put something in the house that nobody can lift alone.** Weight classes (DESIGN §5,
ECONOMY §1) with the van priced in *slots* rather than items — an armful costs 1 of 14, an
armoire costs 3 — and the B4 anchor/follower carry: you take one end, shout at a crewmate, and
they get dragged along behind you at 0.62 speed. Newly possible only because R20 put a crew in
the build; before that "two-man" was a class with nobody to be the second man. Seven new
checks, all injection-tested. · **The V10 check passed on its first run, which is how I knew it
was worthless.** `LEVEL-SPEC`'s tenth check — does the piano physically fit through every
route — cannot fail if the piano has no collision footprint, and carried items had none: an
object nothing collides with fits everywhere. Gave a carried two-man piece its real 1.1m width
and re-ran. · **It immediately failed on two doorways, and the cause was level authoring, not
physics.** The procedural sideboard placement had parked the `land` shelf directly in the mouth
of the conservatory corridor, so the armoire could not leave the room at all — furniture in the
route, which is precisely the fault V10 exists to catch and precisely the sort nobody finds by
eye. Placement now picks from candidate wall positions and rejects any within 2.4m of a doorway
rect or 1.6m of a wardrobe. `BUILD-PROMPT.md` says to automate V10 *before the first wing
ships, not after the first bug report*; this is the first wing, and it shipped with the bug in
it. · One test-fairness call worth stating: the check walks the armoire in along the corridor
**axis**, centred, the way a player lining up a wardrobe would. Whether you can shoulder it
through at an angle is a different and much harder question than whether the geometry admits
the object, and conflating them would make the check fail for reasons that are not the estate's
fault. · Regression: QA 83/83, drift 89/89, estate validator PASS.

R23 · **Pointed the level contract at the level.** `validate_estate.py` has verified a worked
example in a document since R1 and had never once been run against the wing anyone actually
plays. Added an estate exporter (`node proto3d/dump-estate.mjs`) and a `--estate` mode to the
validator. · **The wing failed three of the ten checks**, and every failure was real: **V2** —
no depth pacing whatsoever, every room open from the first second, so a player could walk
straight to the tier-3 conservatory and take the best thing in the house before the Curator
had moved; **V3** — the entire estate hung off `foyer↔hall`, so one Curator standing in one
doorway sealed five rooms, which A6 rule 5 forbids by name; **V8** — the prototype had
invented its own value bands, tier 0 priced at the *pocket* numbers and a made-up ×2.6
two-man multiplier. · Fixes, in the estate rather than in the checks: a **service hall**
giving a second route to the interior, a **study↔land** link so the deep wings survive losing
`hall↔land`, prerequisite gating where **clearing a wing's sideboard opens the next wing**
(D-20: work, never a clock — and gates bind the crew, never the Curator, or V7's navmesh
requirement becomes a safe room), and ECONOMY §3's per-class bands replacing the invented
ones. Estate now **enters the pool**, 10/10. · **One failure was the checker's fault and I
fixed the checker:** V8 rejected nine correctly-banded pieces for being *cursed*. A malignant
tier-3 vase is six times its band by design (D-11) — a check that calls that a fault rejects
every estate with cursed loot in it. V8 now divides the grade multiplier out and additionally
checks the per-class band, which the coarse per-tier band could never do. · **And the same
level fault appeared twice more, which is the finding worth keeping:** R22's V10 check caught
a sideboard parked in the conservatory doorway; this round it caught a wardrobe in the mouth
of the study↔land corridor, placed there by a *fallback* that picked the room centre-line when
no candidate cleared — a fallback that chooses the worst available spot is worse than placing
nothing. Furniture placement is now one shared rule (clear of every doorway rect by 1.9–2.4m),
candidates span all four walls, and a room that ends up with nowhere to hide reports a fault
rather than shrugging. · Regression: QA 86/86, drift 111/111, both sample estates and the
prototype's own estate PASS.

R24 · **Estates are generated now, and gated before anyone sees one.** LEVEL-SPEC has
described a module contract since R1 and the project has had exactly one hand-authored wing
the entire time, which means the contract has never had to hold anything up and every
playtest is the same house. Rooms now sit on a lattice — each inset from its cell by a
per-axis margin, so neighbours always *face* each other across a corridor by construction —
and the build loop rejects estates until one passes, with `?seed=` for handing a specific
house back to whoever found something in it. 120 seeds, all pass; the Python validator agrees
on a 12-estate batch, which is how the JS gate (a subset) is held honest against the ten-check
authority. · **Four defects, three of them mine and one a rule nobody had written down.** The
first generator grew a free-form tree and was rejected 64% of the time, almost always on V3 —
a tree has no second route anywhere, and a leaf room can never satisfy "survives losing any
one door". Leaves are now repaired by adding the 2×2 block that closes a cycle. · **The rule
nobody had written down: a prerequisite chain has to be SATISFIABLE.** V2 checks how many
steps deep a wing sits; nothing checked that you can *reach* the room whose sideboard opens
it. A generated house locked itself shut — clear the hall to open the foyer, with the hall
only reachable through the foyer — and the crew stood in the driveway for three minutes with
$500 and nowhere to go. Added a progressive-reachability pass to the gate; then found my own
implementation of it re-expanded only from the driveway each round and declared every estate
sealed, which took the pass rate to zero and was the loudest possible way to be told. ·
**And the finding worth the round on its own:** the crew's navigation was "walk at whichever
door of this room is nearest the destination", which survived a seven-room chain and jammed
three haulers against locked doors in generated houses. They banked $381 across a whole night,
in SEEK, with reachable loot on the other side of the estate, and **every rule-level check
still passed** — 89 of them. Replaced with a real route over the room graph that only counts
doors the walker may use: nights now bank $2.0k–3.9k instead of $0.4k–4.2k with a stall in the
middle. The new check runs five seeds to completion and asserts the crew actually work. ·
Two more: the Curator's spawn was the room literally named "cons", which most generated
estates do not have; and room names were assigned in lattice order, producing a tier-2 "foyer"
and a tier-0 "attic". · Regression: QA 90/90, drift 111/111, 12 generated estates + both
samples PASS.

R25 · Built the **contract chain** — four nights, an escalating quota, a van that grows
14→19, a different generated house each night, and a chain that ends the moment you miss.
ECONOMY §4's curve has been tuned since an early round and never played. 12 new checks. ·
**And I reproduced ECONOMY §4's own recorded mistake before catching it.** Its original quota
curve was "napkin arithmetic that assumed earnings scale with the quota"; my first pass scaled
the ship quotas by night length, which assumes earnings scale with the *clock*. They don't — a
210s night does not fill a 14-slot van — and the scaled night-two quota landed **above the
mean take**, passing 40% where the sim wanted 73%. Replaced with quotas **measured** in this
build: 36 headless nights per rung, quota set at the take that produces the intended pass
rate. The ship curve stays canonical in `tuning.json`; the measured one describes this build
and is labelled as such. · **The zero tail, and a correction to my own finding.** 14–19% of
nights were banking **nothing**, which caps night one's achievable pass rate at ~81% however
low the quota goes. Every one of them was the **ruin roll** — the crew were hauling cursed
cargo with no policy at all. I gave them R11's cap and D-24's scanning rule (appraise while
it is quiet, take blind once it is hunting), measured 18% → 5%, and wrote it up as R11's
optimum reproduced in play. **Then a paired sweep on identical houses said otherwise:**
uncapped they average 2.73 cursed pieces and capped 2.70, because a 210s night simply does not
contain enough cursed cargo for a cap of three to bind. The 18%→5% was two different seed
sets, which is exactly the mistake the common-random-numbers work in R18 existed to prevent,
made again three rounds later in a different file. What the paired sweep *does* show, cleanly:
**refusing cursed cargo outright costs ~43%** ($1,623 against $2,848), which is R10's
structural point arriving as a live measurement. · The cap did surface one real bug: it counted
cursed pieces **in the van** only, so two crew could each carry one under a cap of one and both
deposit. Counting pieces in transit as well brought a cap of 1 from 1.25 aboard to 1.0 — and
moved earnings enough to invalidate the quota curve I had just measured, which had to be
measured again. · Also: a leaked QA `freezeCrew` flag from the selector checks silently zeroed
every night's take and read as "the quota is too hard" for twenty minutes. · Regression: QA
102/102, drift 120/120.

R26 · Made the fix `ECONOMY.md` §4 names but could never build: **later contracts are richer
houses, not the same house against a higher bar.** Estates now scale with the contract night —
5–7 rooms on night one, 8–10 by night four, tier 4 unlocked from night three — and the gate
*requires* a tier-4 wing on late nights, so "richer" is a mechanism rather than a comment.
With it comes the **apex**: one per late estate, five of the van's nineteen slots, two people
to move, and the thing D-21 says the whole night should build toward. · **It doesn't lift the
crew's baseline, and that is the interesting part.** Earnings across the chain stayed flat
($2.4k–2.8k) even with houses half again as large, because every piece of the added richness
is in objects **bots cannot move** — the apex and the two-man pieces both need a second pair
of hands. Richer estates raise the ceiling available to a crew that *coordinates*, not the
floor available to one that doesn't, which is exactly what ECONOMY §4 wants those nights to
be ("someone has to go into a sealed wing", "the apex is not optional") and not at all what I
expected to measure. The last two quotas are set **above** bot throughput on purpose: night
four passes 33% on crew work alone and 92% if the apex comes home. · **The apex needed the
same correction the quota did.** At ECONOMY's literal $4,000–8,000 it was worth $6,221 against
a $2,900 quota — one object paying for two nights. What transfers across a change of night
length is the **ratio**, not the dollars: the ship band is 32–64% of the final quota, so that
is what `tuning.json` now carries and what the prototype derives from. Same class of error as
R25's scaled quotas, caught one round earlier this time. · Also made the apex **never cursed**:
a ×6 multiplier on the centrepiece would dwarf every other decision in the night, and D-21
wants a goal rather than a lottery ticket. · **And the suite was quietly non-deterministic the whole time.** `newContract()` seeded its
estate from `Date.now()`, so every check after it drew from the harness's seeded RNG at a
different offset — which is why a statistical check failed about one run in three and passed
on retry. Fixed at the source rather than by widening the threshold: a contract can be handed
a seed, and QA always hands it one. Three consecutive clean runs. · Regression: QA 108/108,
drift 124/124.

R27 · **The corpse economy** (DESIGN §5). Until now a collected crewmate was a subtraction:
they vanished and the ledger printed a name. Now they leave a **body** — a two-man object that
reuses the entire item pipeline, exactly as the design says it should. The number on it is
what he is worth *to the collection*, which is why the Curator wants him and why **carrying
your friend makes you a target**; it is never paid to you. Haul him to the van and he is back
tomorrow, free. Leave him and you run tomorrow's higher quota one hauler short. That is the
whole trade — no cash, no fees, no invented currency, and it cost almost nothing to build
because two-man carry, attention weighting, van slots and the ledger were all already there.
7 new checks. · **The bug it found is the one DESIGN §5 says it already fixed once.** The
HUD's quota bar summed everything in the van, so a recovered body read as **$2,056 toward the
quota** — the earlier draft's incoherence ("the corpse both paying out on extraction and
paying out if abandoned") reappearing through the back door of a running total. Bodies are
now excluded from banked, gross and fees; the only thing recovering one changes is who turns
up tomorrow. · One statistical check had to be loosened rather than fixed: "the last night is
not passable on crew throughput alone" was asserting a rate to ten points off twelve runs and
failed on its own noise. It now makes the coarse claim the sample supports and says `n=12` in
the message. · Regression: QA 114/114, drift 124/124, three consecutive clean runs. · Post-round sweep found `STATUS.md` — written one round earlier —
already contradicting itself: a row saying player death ends the night, directly under the row
saying it doesn't, and three check counts quoted from memory that were all wrong. Wrote
`sim/check_counts.py`, which asserts the numbers in the README and STATUS are the numbers the
suites actually report, and injection-tested it. Documented counts have drifted three times in
fifteen rounds; for a project whose main asset is trustworthy numbers, a wrong one in the
first paragraph of the README is not a footnote.

R28 · **Things break now.** Fragility 0–3 (DESIGN §5), a break chance that scales with
fragility *and* with how fast you were moving when you let go, a broken piece worth $0 and
gone, heard at L90–100, and a value premium so delicate pieces are worth more to begin with —
"the physics does the comedy". Put a vase down standing still and it survives every time; let
go of the same vase at a sprint and it breaks three times in four. Crew panic-drops run the
same rule, which is where most of the breakage in a real night will come from: they let go at
a run, by definition, every time the Curator gets within six metres. 7 new checks. · The one
worth stating: **impact, not altitude.** Height would have needed a physics system this
prototype does not have; speed at release is already in the movement code and produces the
same decision — carry the good stuff slowly, and think twice before sprinting home with it. ·
Caught myself writing a check that could never fail — an `ok(..., true, "")` placeholder left
in while the real measurement went below it. That is precisely the thing R14 wrote a rule
about ("a checker that only ever passes is worthless"), and it survived in the file for about
four minutes. Deleted. · Regression: QA 121/121, drift 129/129.

R29 · Consistency sweep, which the iteration prompt asks for every round and which had gone
five rounds without one. Wrote **`STATUS.md`**: spec against build, one row per system, with
a second table for what is specified and *not* built and a third for what the checks cannot
tell you. The project had no single place saying where it actually was — the loop log says
what each round did, the design documents say what the game is, and nobody reading either
could answer "so what runs?". · Rewrote the log's own next-step list, stale since R23, and
corrected the README's counts (121 checks, 129 constants — it still said 90 and 111). ·
Nothing was found broken, which after five rounds of changes is worth one line rather than
five. Full regression green: QA 121/121, drift 129/129, both sample estates and twelve
generated ones PASS.

R30 · **The dead join the collection** (DESIGN §5.1) — the design's answer to the genre's
standing problem, and until now the prototype shipped the failure it names: die and the night
ended. Now a second contact starts a ten-second **collection beat**, and what comes out the
other side is a role. Free movement through walls, permanent sight of the Curator (drawn
lit, and coloured by whether it is hunting), **curse-sight at 5m — grade, never value**, and
**Static**: six points, one back every twenty seconds, and *every point spent adds +1
Disturbance*, which is the entire balance in one line. Knock (1) makes an L25 noise that pulls
it toward you and away from them; Nudge (3) shoves a piece off a shelf, and yes it breaks.
Flicker, Slam and Hold need a lights system and door entities that do not exist and are
listed as missing rather than faked. 16 new checks. · **Three bugs, and one number that was
lying about a different system entirely.** The drift checker's `SIGHT_M` pattern matched the
new `CURSE_SIGHT_M`, so it cheerfully reported the dead's 5m curse-sight as the Curator's 18m
eyesight — the same substring class of bug R14 caught with `sprint`, in the same file, four
regexes later. Nudge charged three Static and did nothing when its one random direction
pointed at a wall. And a knock from forty metres appeared to be heard, because the check
compared the *age* of a fix that never expires rather than whether it had moved. · **One check
had to be rewritten to say something true rather than something flattering.** "The apex turns
around the nights that fell short" is false as stated: it rescues about a third of them,
because the player is doing nothing at all in these runs and a failed night is short by about
one apex. What is defensible — and what is now asserted — is that the apex is the right *size*
to be the thing that decides the night. · Regression: QA 135/135, drift 138/138, three
consecutive clean runs.

R31 · **Lights, and the lever against them** (DESIGN §6.5). The house starts dark. Light a
wing and you can work without leaning on a flashlight that dims to 60% exactly when you need
it most — at a flat **+25 Disturbance**, and **silently**, which is the one exception in this
game to "every gain comes from a Loudness value". The breaker is at the van, so reaching it
means leaving whatever you were doing: **−15 instantly**, and every wing goes out at once.
Six new checks, all injection-tested, including that lighting a wing produces *no* entry in
the noise log. · Shader now takes up to eight lit-room boxes and lifts ambient inside them —
flat house light, no falloff, no shadows, which is what flat-shaded low-poly wants anyway. ·
This is also the first time `LIGHT_MULT` has had anything to be about. It has sat in the
attention model since R20 at ×1.3, and while it did vary with line of sight, "lit" was
hard-coded true for every actor in the house. · One check needed a different statistic rather
than a different threshold: "the apex is the right size to decide the last night" was
measuring the median shortfall of *all* failed nights, and the median was a full quota —
because a ruined night loses the whole van and no single object was ever going to cover that.
Ruin nights are excluded now, with the reason written next to the line. · Regression: QA
141/141, drift 140/140, counts check green.

R32 · The other two **Disturbance levers**, which closes DESIGN §6.5's set. **Go quiet** —
no running, no scanning, crew-wide, −20 over the window — and **unload cursed cargo into the
yard**, which takes that cargo's floor contribution away and, because it is out of the van and
therefore not strapped, leaves it lying in the driveway radiating where the Curator can come
and take it back. Both are real trades rather than free buttons: the first costs the only
thing this game has less of than money, and the second converts a Disturbance floor into a
theft risk. 8 new checks. · Go quiet's **duration** is scaled to this build's night the same
way the quota and the apex band were: 45 seconds is 6% of a twelve-minute night and would be
a fifth of this one. The −20 is not scaled, because it is a meter reading rather than a
proportion. Third time this distinction has come up and the first time it went in without a
wrong version first. · **Two checker bugs, both mine, both old friends.** One asserted on the
Disturbance *meter* where the rule is about the *floor* — the meter decays toward the floor
rather than snapping to it, so the check was measuring the decay rate. The other took item
indices from one snapshot of the list and used them after depositing, which slides every index
by one: it banked a clean piece it never chose and then reported that unloading did not work.
That is the R20 index-shift bug exactly, in a different fixture, twelve rounds later. ·
**And a third checker bug, found by running the suite six times instead of once:**
the fragility-premium check took a per-grade mean off eight seeds to measure an 18%-per-grade
effect against a band spanning 80-300, and failed one run in six on its own variance. Pooled
across 24 seeds and across pairs of grades. Worth a standing note: every statistical check in
this suite wants running several times before it is believed, and I have now been caught by
that three times. · Regression: QA 149/149, drift 142/142, counts green, four consecutive clean runs.

R33 · Two things: **flake detection in the harness**, and the **salt line**. · `qa.mjs -r N`
runs the whole suite N times in one browser and reports any label that failed *sometimes* as
FLAKY rather than letting a good run bury it. Three statistical checks have been caught failing
one run in six on their own variance, in three consecutive rounds; a check that passes four
times and fails once is a failing check with a publicity problem. Proved by injecting a probe
that fails 40% of the time and watching it come back FLAKY 2/3. · The salt line is DESIGN §8's
one defensive tool: one charge, twenty seconds, laid in a doorway, consumed. · **And it does
not do what the spec says it does.** "The Curator won't cross for 20s" implies denial; V3
requires every wing to survive losing any one portal, so a house that passes the level
contract *always* has a way round, and salting a doorway costs it a detour instead. The same
V3/V4 tension R1 found in the very first round, arriving from the other direction. Written into
`STATUS.md` as a known limit rather than papered over. · **The checks for it were wrong three
times and each was a different flavour of wrong.** First they asserted the Curator never
reached me — passed with the rule deleted, because it went round. Then they measured how long
it took with and without salt — that difference was hearing fuzz, not salt. Then they asserted
"never entered the salted corridor" with a disjunction that short-circuited and a movement test
that a *stationary* Curator would pass. What finally works is deterministic and small: the
router returns a different door once salt is down, and the body moves without ending up on your
side of the line. · Regression: QA 154/154, drift 144/144, and `-r 3` clean.

R34 · **The dolly**, which removes the last stand-in from the weight system. Cart-class
pieces — which since R26 means the apex — can no longer be picked up *at all*: they go on the
dolly or they stay where they are. It is slow (×0.55), it is **L35 while it rolls** at 0.7/s,
which makes it the loudest thing you can do on purpose, and it **tips** if you sprint with it,
dropping the load and breaking it if it is fragile. That last one is the design's own promise
("slow, loud on hardwood, tips over") and it is where the apex stops being a heavy pickup and
becomes a logistics problem with a comedy failure mode attached. 6 new checks. · This also
retires the note R26 left behind: cart class was being carried by two people at a crawl,
flagged in the code as a stand-in for a tool that did not exist. · Three fixture faults, all
mine, all instructive: I sampled the Curator's fix *after* the run and read null, because it
had already walked to the noise and cleared it — the fix has to be sampled during. I set
`player.speed` directly to test tipping, and the movement code overwrites it from actual
displacement on the same frame, so the shove never happened; sprinting with the dolly is what
does it, which is the real mechanic anyway. And an apex check from R26 asserted two people and
five slots — correct then, wrong now, and it failed the moment the rule changed, which is what
it is for. · Regression: QA 159/159, drift 147/147.

R35 · **Made it playable by a person**, which is item one on this log's own next-step list
and has been for six rounds. Sixteen verbs had accumulated behind a start screen that listed
eight — the salt line, the breaker, go quiet, the dolly, the ghost's Static verbs and the
whole contract chain were all undiscoverable unless you read the source. One control list,
rendered on the start screen and behind <kbd>H</kbd> in game, grouped by what you are doing
rather than by keyboard order, with what each verb *costs* on the same line ("light this wing
— silent, +25 disturbance"). · The check that matters here reads the key handler out of the
page source and asserts **every bound key appears on the list**, so the next verb cannot ship
undocumented. Injection-tested by deleting one row. · Two layout passes, both driven by a
screenshot rather than by hope: the first list ran off the bottom of a 720p laptop with CLICK
TO BEGIN below the fold, which for a prototype whose entire purpose is one honest playtest is
worse than not writing it. Two columns and tighter leading now fit the whole thing on screen.
· Regression: QA 161/161, drift 147/147.

R36 · **Doors, and the last three Static verbs** — which retires the whole "specified, not
built" row for `DESIGN` §5.1. A door is now a thing rather than a hole: open until something
shuts it, and walking into a shut one costs **1.4 seconds and a door's worth of noise**. That
single number is what makes the ghost's remaining verbs worth their price — **Slam** (2) buys
the Curator a delay, **Hold** (5) stops it dead for four seconds without the opening timer
even starting, and **Flicker** (1) is how the dead say "in here" without a radio. Slam and
Hold cost 7 between them against a cap of 6, so you cannot do both to one door on one budget;
that is `DESIGN` §5.1's arithmetic and it is now asserted in two places, as behaviour in
`qa.mjs` and as a constraint on the constants in `check_drift.py`. · Eight injections, all
caught by the check they were aimed at. · **The door-timing check took three attempts and
found a bug on the way.** It first measured the time for the Curator to reach the player and
read *no difference at all*, because both runs spent the same two and a half seconds in
FIXATE and 1.4s vanished into the noise of a longer walk — so it measures the crossing of the
doorway itself. Then it started the Curator 1m from the door, which is *inside* the doorway
rect, so the door spent its FIXATE seconds quietly opening and only half the delay survived.
Then, with both fixed, it read the shut door as **faster** than the open one: `reset()` treats
doors as estate furniture and was never clearing them, so a door slammed on night two was
still shut on night three. Fixed, and asserted. · The pair is measured on one pinned random
stream, restored afterwards, because hearing is fuzzed ±3m and that moves an approach further
than the effect being measured.

R36b · **The level validator had been rejecting every house the generator makes.** The command
`README.md` tells you to run — dump estates, hand them to the Python authority — returned
**12 of 12 REJECTED**, and had done for as long as the batch mode has existed, because nothing
asserted its output. Three faults, all the checker's: V8 divided the *curse* multiplier back
out of a price but not the **fragility premium**, which is just as designed (`DESIGN` §5, +18%
per grade) and is why a delicate piece is worth more; there was **no tier-4 band** for ordinary
loot, so the sideboard next to the apex was judged against the apex's own $4,000–8,000; and the
apex was judged in **ship dollars** when this build bands it as a share of a 210-second night's
quota. All three fixed, all three injection-tested, and the export now carries the `frag` grade
and the night's quota so the authority can apply the rules it owns — D-26 writes down the
general rule, which is that a band check has to be handed its multipliers rather than asked to
infer them, and that a validator whose output nothing asserts is a script and not a check. 24 of 24 estates across all
four nights now enter the pool. · The way in was a console error that appeared in about one QA
run in four: `page.on("console")` delivers asynchronously, so "no page errors" was racing the
errors it exists to catch. Recorded in-page instead, it is observed the moment it is asked for.
· What it was hiding: the gate sweep only ever swept **night one**, and the gate asks for more
on a late contract — a tier-3 wing always, an apex wing from night three. Night three failed
**5% of seeds outright** and played them with their faults printed to a console nobody reads.
The house is grown to fit the tier it has to hold, the retry loop asks for a *bigger* house
every twenty failures rather than rerolling the same one, and the sweep now covers all four
nights: 0 bad in 1,600 seed-nights, worst case 60 attempts against a cap of 120. · One
injection here did *not* fail the suite and that was the informative one: taking the extra
rooms away again left the gate still holding — the retry escalation covers for it — so the
claim was rewritten from "it holds" to "it holds with margin", worst case under 80 attempts
where the injected build needs 92. · Regression:
QA 171/171, drift 166/166, the validator over 24 generated estates across all
four nights plus its own two samples, and `-r 3` clean.

R37 · **The same failure again, in the six files nobody was asserting.** R36 ended on a rule —
*a script whose output nothing asserts is not a check* — so the first thing this round did was
ask which other scripts that describes. Six: `chain_sim`, `haul_sim`, `integrated`,
`curse_test`, `disturbance`, `curator_attention`, between them the authority for most of the
numbers in `DESIGN`, `ECONOMY` and `DECISIONS`, and not one assertion among them. · The one
that had rotted was the worst possible one. `chain_sim.py` — the file that answers *is the
contract chain achievable?* — was still running the quota curve `ECONOMY` §4 **replaced eleven
rounds ago**, and printing a **1% night four**: the finding that caused the replacement,
presented as if it were still the answer. Anyone who ran it would have concluded the chain is
unwinnable. Pointed at the calibrated curve it reproduces the documented table almost exactly —
94 / 73 / 56 / 42 against a published 95 / 73 / 55 / 40 — and the superseded curve is kept and
still printed, because `ECONOMY` §4 records the failure on purpose. · `sim/check_claims.py`
now restates **20 conclusions** as assertions, each tagged with the document that quotes it.
The sims are seeded per trial, so it is reproducible rather than statistical: a failure means
the model moved, not that the dice did. Ten seconds to run, and wired into `check_counts.py`
so the number in the README cannot drift either. · **Ten injections, seven caught — and the
three misses were the round's real content.** Halving the labour cost of a two-man piece moves
the chain by 2%, because what binds a night is *trips*, not people; ECONOMY §3 justifies the
two-man band partly on a cost the model can barely see. Zeroing the curse fees outright leaves
the optimum cap exactly where it was, which is R9's finding restated — a *linear* van-side
cost cannot move a *multiplicative* decision, and that is the entire argument for D-11's ruin
tail. Both are now claims in their own right, so the checker states what the models cannot see
rather than leaving it as a blind spot. The third miss, a three-minute apex load, corresponds
to no claim any document makes, and I did not invent one to cover it. · One more inert lever
found on the way: in `disturbance.py` only the **first** lit wing is measurable. The lever
policy switches a wing back off as soon as Disturbance passes 78, and with the levers off the
night saturates at the 100 ceiling where nothing extra can register. The claim is scoped to
what the model can actually see, and says so. · Regression: claims 20/20, drift 166/166, QA
171/171.

R38 · **Put the largest gap on a clock.** `STATUS.md` has called multiplayer the biggest risk
in the project for twenty rounds, and it is — but "unproven" was covering two different things.
The *feel* of four people in a house needs four people. The *arithmetic* of a host-authoritative
world with owner-authoritative carry needs a clock, a delay, and an honest account of who
believes what and when, and that is a thing this container can settle — the same way
`haul_sim.py` settled the appraiser before anyone built it. `sim/netcode.py` puts all four of
`TECH-SPEC` B1–B4's promises on a 60Hz loop with one-way delay and jitter, at 30 / 80 / 120 /
250ms.

Three of the four survive, and one does not:

- **The hot potato holds.** The override retargets instantly on the *host*, which learns about
  the hand-off one trip later, so the giver keeps the Curator for 0.13s at the spec's own
  budget and 0.26s at 250ms — against the 2.5s the Curator needs to reach you. The design's
  most load-bearing promise is not close to breaking.
- **The pickup race only flips in a photo finish.** A press gap over 150ms is never overturned
  at any latency modelled, because human reach times dwarf the jitter differential. Optimistic
  grab plus rollback is safe.
- **The pry disagrees with the victim's own screen** 3.6% of the time at 120ms and 7.3% at
  250ms: they walk out of range, watch themselves escape, and lose the item anyway. Not a bug
  in the pry — that is where the authority is — but the 1.5s hold is long enough to fix cheaply,
  and B3 now says how.
- **The two-man drift tolerance is already spent.** B4 allows the follower 0.4m of drift before
  a soft correction. At 120ms the follower's view of the far end is **0.38m behind at p95**.
  Straight-line walking costs 0.13m of that; the rest is the *pivot*, because 1.4m of lever arm
  turns a lazy doorway turn into two metres a second of far-end travel. At 250ms, 87% of pivots
  are over the line. So 0.4m is not a slop budget with latency inside it — it *is* the latency,
  and the physics gets nothing. B4 now says to scale it with measured RTT and to not let the
  correction fire on a pivot, which is the one moment it is guaranteed to trigger and the worst
  possible moment for the couch to snap.

· And the same rot R37 found, one more time: `curator_attention.py` still had the **additive**
weight function as its default — the one R2 replaced and D-25 made FIRM against — so anyone
running it saw the pre-R2 model. Under it, a loud, lit, **empty-handed** player is hunted 100%
of the time; under the shipped one, never. Both are now printed side by side, and the claim
reads the module's default rather than setting it, because a check that sets the flag it is
testing passes just as happily with the wrong model shipped. That is exactly how this survived
thirty-five rounds. · 15 injections, 12 caught; the three that are not are R37's documented
blind spots and stayed that way on purpose. · Regression: claims 25/25, drift 166/166, QA
171/171.

R39 · **The crowbar, and the second kind of lock.** `DESIGN` §6.4 says it in one line — "the
boarded stair needs the crowbar that's in the garage. You physically cannot be deep at minute
one" — and the house has never had one. Now every doorway into the deepest wing is boarded.
**Every** doorway, not one: `LEVEL-SPEC` V3 guarantees no single portal can seal anything,
which is exactly why the salt line buys a detour rather than a wall, so boarding one door
would have gated precisely nothing. Boarding a whole wing is the same shape of lock the
prerequisite chain already uses, and it is the shape the design describes. · The crowbar
spawns shallow, never behind its own boards, and takes **both hands** — you fetch it or you
haul, never both, so the trip to get it is a trip nobody is earning on. Prying reuses the
door-opening shape (walk into it and it takes time), costs three seconds, and is **L75**, the
loudest thing in the toolkit, at a doorway as deep in the house as the house goes. The crew
never touch it; the Curator ignores boards entirely, because it is the house and not a guest.
· **What it buys, measured rather than asserted:** with the wing shut the crew still make
quota on all four nights — 3,817 against 1,550 on night one, 4,830 against 3,300 on night four
— so the boards are not a wall across the contract. What is behind them is the **apex**, from
night three, worth 32–64% of the final quota on its own. The crowbar is how the last third of
a contract gets paid, not a gate on the first, and `DESIGN` §6.4 now says so. · **Nine injections, nine caught — but only after two rounds in which three of them
walked straight through, and those three were more useful than the checks.** "Boards do
not lock anything" walked through untouched twice: the deepest wing is shut by its
prerequisite chain *as well*, and its neighbours are deep rooms with chains of their own, so
nothing could tell wood from prerequisites. It takes emptying every sideboard in the house
first — then `locked()` must be exactly the boarded doors and nothing else. "Only one door is
boarded" also survived, because `reset()` had its own copy of the boarding loop and quietly
repaired the injected estate every night; one place decides now. And "you can hold a crowbar
and a vase at once" survived because the fixture called `grab()` while aimed at nothing, which
is a check that cannot fail. · **A latent suite-wide bug fell out of it:** `gates(true)` is a
global QA switch and `reset()` does not clear it, so every check after a block that turned it
on had been running with the prerequisite chain disabled. `fresh()` clears it now. Nothing
was passing only because of it — all 183 still pass — but the crowbar checks reported that
boards could not be pried, and the reason was that nothing was stopping the player at all. ·
Regression: QA 183/183, drift 168/168, claims 25/25.

R40 · **What actually stops a night, and a wrong finding caught before it was published.**
The round started with an alarm: nights measured at 24 runs came back **88 / 100 / 83 / 29**
percent — a chain with no shape in the middle and a wall at the end, which would have meant
the build's quotas had drifted out of calibration since R25. At 40 runs the same measurement
reads **88 / 82 / 72 / 53**, a clean monotone curve. The distributions are wide enough that
twenty-four nights cannot tell a formality from a coin flip, which is the same lesson three
statistical checks already carry and which I still nearly published as a defect in the quota
curve. Nothing was wrong with the quotas. · What *is* wrong is one layer down, and the wide
distributions were the clue: the four nights' takes are nearly identical — median net 3,438 /
3,499 / 3,204 / 3,579 — so **none of the escalation comes from the house**. Measuring what
binds says why. At dawn, over 96 nights, the van still has **4 to 7.5 free slots** and **88–95%
of the house's value is still on its shelves**. Time binds this build. Not capacity, not what
is in the house — and it binds *harder* on the later nights, where the van is bigger and the
house is larger. · So two of `ECONOMY`'s escalation levers are decoration in the thing you can
actually play: the 14→19 van curve, which §1 calls the master scarcity lever, and "richer
estates later in the chain". Neither can matter to a crew that never fills the van and never
reaches most of the rooms. The entire escalation is the quota number going up — which is
structurally the same failure §4 already records for the superseded curve, arriving by a
different route. · This is a property of a 210-second night against a design calibrated for
720, not a fault in the design, and the honest response is to say so rather than to re-tune
the build around it: the prototype **cannot** be used to tune capacity, and `chain_sim.py`'s
720s model is the only place that question can be asked. Both facts are now checks rather than
paragraphs — `qa.mjs` asserts that the van still has slots at dawn and that most of the house
is untouched, so if the night ever gets long enough for capacity to bite, the check that says
it does not will be the thing that fails. · Regression: QA 185/185, drift 168/168, claims
25/25.

R41 · **What a curse costs you to carry** — the last content gap `DESIGN` §4.2 specified and
nothing implemented. Grades moved price, attention and the ruin roll; none of them did
anything to the hands holding the piece. Now: **TAINTED** forces your torch on and beats it,
and adds Disturbance while held. **MALIGNANT** gains mass over twenty seconds to ×0.62 speed,
and every eight seconds it speaks in a living crewmate's voice — which to the Curator is an
L25 noise exactly where you are standing. All of it ends the *frame* the piece leaves your
hands, because §4.2's hard rule is that a cost nobody can attribute is not a cost. · **The
tainted gain is 1.0/s and that number is an argument, not a preference.** The first
implementation used 0.25/s and the check reported Disturbance *falling* by six points across
the thirty seconds it was supposed to be rising: a crew of four decays at 50/min, which is
0.83/s, so anything under that makes the number drop more slowly instead of climbing. A cost
that only slows a decline is not one anybody can feel, which is exactly what the rule
forbids. · **Giving TAINTED a torch cost meant giving the torch a switch first.** Every
actor's light was hard-wired on, so "your flashlight beats like a pulse — visible to everyone"
would have been a drawback that changed nothing at all. Dark is a verb now: a lighter mark to
the Curator's eye, because A3's light multiplier stops applying, and nearly blind to work in.
A cursed piece is the thing that takes the choice away. · **Nine injections, and the first
round caught six.** All three misses were the checks' fault and each was a different way of
testing nothing. "A tainted piece leaves your torch alone" survived because the fixture never
turned the torch off before picking the piece up, so there was nothing to turn back on. "The
mass does nothing to your legs" survived because the check read the *variable* that is
supposed to cause the slowdown instead of metres walked. And "a clean piece is cursed too"
survived because nothing asserted what a clean piece costs — the baseline was missing, so
there was nothing for the other two to be a cost *against*. · Three fixture faults on the way,
all of them old friends: an index taken before `reset()` and used after it, a player standing
in the van where anything in your hands is banked on the next frame, and thirty seconds of
walking in a straight line that carried the piece out of the room and into the van mid-
measurement. · Regression: QA 192/192, drift 173/173, claims 25/25.

R42 · **The voice ladder** — four loudness values that had sat in `tuning.json` unused for
forty rounds, because the prototype had nothing to say. `AUDIO-SPEC` §2.2 is the best mechanic
in the audio design and the one that most obviously needs two clients, but only *half* of it
does: falloff, occlusion filtering and the codec need a second mouth, and the **ladder** — how
loud you are, and therefore who hears you — is arithmetic this build can carry. Whisper 8,
raised 45, shout 65, on exactly the hearing model everything else uses: `L × 0.33` metres,
`× 0.85` per wall. · What that exposed is a consequence nobody had written down. Rooms sit on
a 13-metre lattice, so a **raised voice fills the room you are in and stops at the doorway**
(14.9m) and only a **shout** is heard next door (21.5m, 18m through a wall). That makes the
ladder a decision instead of three words for the same thing: asking for the other end of an
armoire from across the house means telling the Curator exactly where you both are. ·
`grabDrop` has carried the comment "you take one end and shout at somebody to take the other"
since R26 with **no shout in the game** and a `wantHelp` flag that nothing ever read. Calling
now brings whoever heard you, and the first one to reach you takes the far end. · **Eight
injections, all caught** — but four fixture faults first, each one a different way of testing
nothing: crew parked in the driveway four rooms out of earshot; crew who picked something up
during the fixture's own five seconds of stepping, because `unparkCrew` emptied everything
except their hands and `speak()` skips a crew member who is carrying; a `carry()` that goes
null the moment an armoire held by one person is put down, thrown from inside a loop
condition; and crew who could hear the shout perfectly well but could not legally *route* to
a two-man piece, because two-man pieces live at tier 2 and deeper and the prerequisite chain
was still shut. That last one is not a bug: calling for help from a locked wing correctly gets
you nobody. · One real tuning fault fell out of the same check: the crew gave up after six
seconds, which is exactly how long it takes to cross a room, so they turned back one step
before arriving. Twelve seconds, and the number is now in `tuning.json` with the room width
written next to it. · Regression: QA 198/198, drift 177/177, claims 25/25.

---

## Next step (paste the loop prompt to resume)

`STATUS.md` is the current spec-against-build inventory. Ranked by what most endangers the
build:

**1. Nobody has played it.** 121 headless checks say the rules behave; none of them says the
game is fun, and `DESIGN` §11's Phase 2 gate — four friends find hauling junk to a van funny,
*without* a monster — is the only thing that can. Twenty minutes with `proto3d/index.html`
open is worth more than another round of this. Every round since R16 has been building the
thing that makes that twenty minutes informative.

**2. The whole social layer is unproven and unbuildable here.** The hot potato, proximity
voice, the physics handoff at real latency: one player and three haul bots cannot test any of
it, and the bots make the *shape* of the loop measurable without saying anything about whether
four people shouting at each other is funny. This is Phase 0/1 and it needs two machines.

**3. The tools are missing.** Dolly, radio, crowbar, salt line, breakers, and the two
Disturbance levers are all specced and absent (`STATUS.md`). The dolly is the one with
mechanical consequences — cart-class pieces are currently carried by two at a crawl, which is
a stand-in, not the design.

**4. Death is still an ending.** `DESIGN` §5.1 answers the genre's standing problem — the dead
join the collection, with sight of the Curator and a budget of poltergeist verbs — and player
death currently just ends the night. Crew death now leaves a body worth recovering (R27), which
is half of it.

**Standing:** the C# core suite (`unity/tests/CoreTests`, 31 assertions) has not run since R14
— no .NET SDK in the container this loop runs in — so `check_drift.py` is the only thing
holding the C# port to the canonical numbers. Run it on a machine that has `dotnet`.

---

## Superseded next-steps, kept for the reasoning


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
