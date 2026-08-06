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

R16 · Took the open item the log itself named — apply R11's tail-risk lesson to the
appraiser — and built `sim/scan_risk.py` to test it. · **The hypothesis is dead, and killing it
found the real answer.** A super-linear scan cost (`p = k x consecutive^1.8 x tier_weight`,
with death and a permanently smaller crew, which slows crew-scaled decay and spirals) makes
*every* scanning policy lose to hauling blind at every k from 0.02 up, monotonically in how
much you scan. No burst length wins. **The refinement:** cost *shape* decides whether an
interior optimum can exist, but the *size of the benefit* decides whether it does. Cursed
cargo pays x6 and survives a few ruin rolls; scanning pays x1.35 and survives none. Logged as
D-23 so the next person doesn't have the same obvious idea.
· **Then found the actual gap, which was on the benefit side.** Scanning is worth
`E[max of 4] - E[random]` = **0.6 x spread x room mean** — so its payoff is a property of the
ROOM, and every model in this project has drawn all four candidates from one flat band. Eight
rounds of trying to fix the appraiser by adjusting its *cost* were all working on the wrong
half of the equation: a constant rate of return is not a decision at any price. Gave rooms a
declared `value_class` (shelf +/-10%, mixed +/-40%, curio +/-110%) and the appraiser goes from
+4.4% to **+12.2%**. · **The controls are the finding, not the headline.** Scanning a *random*
25% of rooms earns +4.6% at identical scan count and noise, so ~60% of the edge is reading the
room rather than scanning less; and scanning only *shelf* rooms earns **-1.9%**, so there is
now a wrong answer. Robust across both sweeps: curio spread 0.7->1.9 moves the edge 7%->20%,
curio share 10%->40% moves it 6%->17%, and curio-only wins in every cell. Logged as D-22, with
its cost stated — it pulls against D-10, and the reconciliation is that *the room's variance is
public and the item's value is private*.
· **Two live bugs found on the way, both in the checking apparatus rather than the game.**
(1) `integrated.py` still had the cursed Disturbance floor at **2.0** four rounds after R11
raised the canonical value to 7.0 — because it lived as `cursed * 2.0` inside an expression,
and `check_drift.py` can only see *named* constants. The drift checker had been reporting
55/55 green over a live divergence. Hoisted it, added the check (56 now), and verified the new
check actually fires by injecting 7.0->4.0 and confirming exit 1. Correcting it moved that
file's headline from +6.1% to +4.4%. **Standing rule: a tuned number that isn't a named
constant is invisible to drift checking.** (2) `sim/validate_estate.py` had **no entry point at
all** — `validate()` was defined, `EXPECTED_FAILURES` was declared, and nothing called either,
so `python sim/validate_estate.py` printed nothing and exited 0, which reads exactly like
passing. R14's "estate validator PASS" was that. Added a self-test that asserts the clean
estate passes everything and the broken estate trips *exactly* its planted faults — no more, no
fewer, so a check that over-fires is caught too.
· Added **V11** (every loot room declares a `value_class`; 15-35% curio per wing) with a
planted fault in `BROKEN_B`, and verified its three failure modes fire: missing class, unknown
class, and both ends of the share band. Suite is now 11 checks, 8 planted faults, all green.
· Swept the docs for the appraiser number, which appeared as +84% in three places long after
two corrections: `README.md`, `DESIGN.md` §4.4 and `DECISIONS.md` D-10 now carry the full
revision chain instead of a stale headline.

---

## Next step (paste the loop prompt to resume)

**1. The hiding mechanic has no numbers.** `DESIGN.md` §8.1 (added R15) is the newest core
verb and the only one specified purely in prose — no concealment durations, no detection
radius while hidden, no cost, nothing a build session could implement without inventing
values. It also interacts directly with the attention model, which is the one system this
project has already been wrong about twice. It is now the largest gap between "specified" and
"buildable", and R16's result raises its priority: the appraiser makes you stand still for
three seconds, and hiding is the counterplay to being caught doing it. Spec it to the same
depth as the attention model and simulate the stash-then-hide / hand-off-then-hide / buy-four-
seconds choice from §8.1 to check it isn't another step function.

**2. Per-crew-size pacing, still open from R12.** Solo Disturbance tops out ~57 at sunrise, so
a lone player is essentially never hunted in a 3-minute run. The `x crew/4` decay scale fixed
the *direction* of the crew-size dependency, not the *curve* — each crew size needs its own
pacing target, and nothing has swept 1/2/3/4/6 players against time-in-tier. Every sim in this
project except the prototype has only ever run four players, which is exactly how the original
bug stayed invisible.

**3. V5 is still the weakest check in the validator**, unchanged since R1: it walks only the
*shortest* path from plinth to van and counts doors, so a wing whose alternate route is
acoustically dead passes. It has never failed anything, which for a check is a symptom rather
than a reassurance — R16 found two other pieces of apparatus that were quietly not running, so
treat "never fires" as suspect by default. Make it walk every route V3 guarantees.

**Also worth doing at some point, none of it blocking:**

- **`ART-DIRECTION.md` owes V11 a treatment.** Room value class is now a *dressing contract* —
  curio rooms must read as lotteries from the doorway — and the art doc predates the idea. If
  the telegraph doesn't land visually the mechanic degrades to a coin flip (D-22's stated
  falsification condition).
- **Port the drift checker's lesson.** A tuned number that isn't a named constant is invisible
  to `check_drift.py`. Nothing has swept the three implementations for other inline literals;
  R16 found the one it was looking for, not all of them.
- **O-05** (does the Curator have a face) remains the only open decision, and still blocks
  nothing.

**Not blocked on anything.** The next genuinely new information comes from Phase 0 — two
people, a door, and spatial voice over Steam — not from another design pass.
