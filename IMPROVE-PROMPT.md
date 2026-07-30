# The Improvement Prompt

The build brief (`BUILD-PROMPT.md`) says what to make. This says how to keep it honest while
making it. Paste it to run an improvement loop.

---

## PROMPT

> Improve **Estate Liquidators** in `C:\Users\srobs\estate-liquidators`. Read `README.md`,
> `DECISIONS.md`, and `LOOP_LOG.md` first; where the log contradicts a doc, the log is newer.
>
> ### The specific risk this loop exists to fight
>
> The same rules are now implemented **three times** — Python simulations (`sim/`), a
> JavaScript prototype (`proto/`), and the C# core (`unity/Assets/Scripts/Core/`). Every
> tuning constant appears in all three. That is a drift machine: a value gets corrected in one
> place, the other two quietly disagree, and the project starts trusting numbers that no
> longer describe the game. This project has already retracted three "verified" figures that
> turned out to be instrumentation artifacts, so treat divergence as the primary defect class.
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
> - **Distrust clean results.** Three of the last six rounds found bugs in the *instrumentation*
>   rather than the design. A test that passes first time and a sweep that comes back 100% both
>   deserve a second look before they're believed.
> - **Never loosen a failing assertion to make it pass.** Find out whether the code or the test
>   is wrong, and fix that.
> - **Prefer deleting duplication to adding features.** One rule in one place beats the same
>   rule in three.
> - Flag inference vs verification explicitly — package status, licensing, API behaviour.
> - **Never commit to the repo at `C:\Users\srobs`**; it's shared across sessions.
>
> ### What "done" looks like for a round
>
> Something that runs, a number that's checked, a contradiction removed, and one line in the
> log. Not a document describing what could be built.

---

## Why these clauses

**"Divergence is the primary defect class"** — the project's biggest asset is that its numbers
are trustworthy. Three implementations is exactly how that stops being true.

**"Distrust clean results"** — empirically earned. The ADAPTIVE-equals-BLIND row, the 100%
scenarios, and the monotonicity violation were all too-clean outputs that turned out to be
bugs.

**"Never loosen a failing assertion"** — the reflex that would have hidden the off-by-one in
R13's hand-off test, and with it the ability to detect a real regression later.

**"Prefer deleting duplication"** — the codebase is now large enough that its failure mode has
shifted from *missing* to *inconsistent*.
