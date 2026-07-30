# The Improvement Prompt

The build brief (`BUILD-PROMPT.md`) says what to make. This says how to keep it honest while
making it. Paste it to run an improvement loop.

---

## PROMPT

> Improve **Estate Liquidators** in `~/dev/estate-liquidators`. Read `README.md`,
> `DECISIONS.md`, and `LOOP_LOG.md` first; where the log contradicts a doc, the log is newer.
>
> ### The specific risk this loop exists to fight
>
> The same rules are now implemented **four times** — Python simulations (`sim/`), two
> JavaScript prototypes (`proto/index.html` and `proto3d/index.html`), and the C# core
> (`unity/Assets/Scripts/Core/`). Every disturbance, curse and van constant is duplicated
> across all four. Until R17 the guard covered only three: `sim/check_drift.py` read
> `proto/index.html` alone, so `proto3d/` re-declared the canonical constants outside the
> checker entirely — and behind that gap **both** prototypes had drifted to `+2` per cursed
> item where `tuning.json` says `7.0`, the value R9 retired as inert. R17 fixed both copies
> and now checks all four implementations, asserting coverage *per implementation* rather
> than merely somewhere. Assume the next such gap exists and has not been found yet.
> This is a drift machine: a value gets corrected in one place, the other three quietly
> disagree, and the project starts trusting numbers that no longer describe the game. This
> project has already retracted four "verified" figures that turned out to be instrumentation
> artifacts — most recently the drift checker's own "55/55 constants agree" headline (R16:
> real C# loudness coverage was 12 of 14, and 23 of the 59 canonical constants had no guard
> at all) — so treat divergence as the primary defect class.
>
> ### Each round
>
> 1. **Pick the highest-value gap yourself** — the thing whose absence most endangers the
>    build. State why it beat the runner-up. Don't ask.
> 2. **Build it**, to implementation depth: real numbers, real code, no placeholders.
> 3. **Verify it by running it.** A claim without an execution behind it doesn't count. If
>    something can't be run here, say so plainly rather than implying it was checked.
> 4. **Reconcile.** Anything the new work contradicts elsewhere gets fixed in the same round,
>    so there is exactly one source of truth per fact.
> 5. **Log one line** to `LOOP_LOG.md`: what you built, what it found.
>
> ### Standing rules
>
> - **Optimise for four friends laughing in a hallway.** Where good engineering and funny
>   conflict, pick funny and say what it costs.
> - **Distrust clean results.** The last seven rounds turned up four bugs in the *instrumentation*
>   rather than the design. A test that passes first time and a sweep that comes back 100% both
>   deserve a second look before they're believed.
> - **Never loosen a failing assertion to make it pass.** Find out whether the code or the test
>   is wrong, and fix that.
> - **Prefer deleting duplication to adding features.** One rule in one place beats the same
>   rule in four — `sim/`, `proto/`, `proto3d/`, and `unity/Assets/Scripts/Core/`. `proto3d/` is
>   not read by `sim/check_drift.py` at all, so its copy drifts unobserved.
> - Flag inference vs verification explicitly — package status, licensing, API behaviour.
> - **Commit as you go, but only within this project folder.** The project is now its own git repo with its own remote — it moved off the Windows PC to the Mac (see `TRANSFER.md`). The old rule about never committing to the shared parent repo at `C:\Users\srobs` described that machine and no longer applies.
>
> ### What "done" looks like for a round
>
> Something that runs, a number that's checked, a contradiction removed, and one line in the
> log. Not a document describing what could be built.

---

## Why these clauses

**"Divergence is the primary defect class"** — the project's biggest asset is that its numbers
are trustworthy. Four implementations, one of them unguarded, is exactly how that stops being
true.

**"Distrust clean results"** — empirically earned. The ADAPTIVE-equals-BLIND row, the 100%
scenarios, and the monotonicity violation were all too-clean outputs that turned out to be
bugs.

**"Never loosen a failing assertion"** — the reflex that would have hidden the off-by-one in
R13's hand-off test, and with it the ability to detect a real regression later.

**"Prefer deleting duplication"** — the codebase is now large enough that its failure mode has
shifted from *missing* to *inconsistent*.
