# The Iteration Prompt

Paste this to continue MESO. Written to be reusable across sessions, and to survive the
fact that a fresh session remembers none of the conversation that produced the work.

---

## The prompt

> Continue the MESO training-planner work in `fitness/`.
> Read `README.md`, then `LOOP_LOG.md`'s last entry and its "Next round" section, then
> `DECISIONS.md`. They are the map, the state, and the settled arguments.
>
> **Each time I run this, do a full self-directed pass:**
>
> 1. **Pick the target yourself.** Take the top-ranked item from the last round's "Next
>    round" section unless something has changed that makes it wrong — and if you deviate,
>    say why it beat what was ranked above it. Don't ask me what to work on.
> 2. **Build it, don't describe it.** A simulation that runs, or a spec with real numbers
>    and pseudo-code in it. A spec I can't build from is a blog post.
> 3. **Try to break your own result before you report it.** Every round so far has found
>    its most important thing by attacking its own output — R1's headline finding came
>    from asking why a result looked too clean. Run the null hypothesis. Check whether the
>    finding is a property of training or a property of the model.
> 4. **Then sweep for consistency.** Reconcile anything the new work contradicts elsewhere,
>    and collapse duplicated facts so there is exactly one source of truth per number. Say
>    what you reconciled.
> 5. **Log it.** `DECISIONS.md` gets the non-obvious calls with their falsification
>    conditions, and moves any decision the new work invalidates. `LOOP_LOG.md` gets one
>    entry: what was built, what it found, and a re-ranked "Next round".
> 6. **Keep the tests green and add to them.** Anything a later round could quietly break
>    while the numbers still look plausible gets pinned by a test. That is the specific
>    failure mode here: a simulation never crashes, it just starts lying.
> 7. **Report back:** what you improved, what you deliberately left rough and why, and the
>    two or three things to attack next, ranked.
>
> **Standing constraints:**
>
> - **Separate what you verified from what you inferred.** Every parameter in this project
>   is currently a guess wearing a citation's clothes. Say so, every time, and never let a
>   number pass from "assumed" to "known" just because it has been sitting in a table for
>   three rounds.
> - **Prefer the finding that costs you the round.** A result that invalidates the work you
>   just did is worth more than one that confirms it. R1's deload sweep was rendered
>   meaningless by R1's own volume analysis, and that was the round's value.
> - **Size the term before optimising it.** The project's biggest mistake so far was
>   spending a round on deload cadence, worth 0.8 preparedness points, while the fitting
>   term worth ~36 sat untouched. Ask what a finding is worth against the other terms
>   before you spend a round on it.
> - **No dependencies.** Pure Python standard library. Everything here should still run in
>   five years.
> - **Leave seams. Don't gold-plate.** Don't over-specify what one week of real logged data
>   would answer.
> - **Don't ask permission to proceed.** Do the work, then tell me what you did.
>
> Work only in `fitness/`. Commit to the working branch when the round is done.

---

## Why each clause is in there

**"Take the top-ranked item unless something changed."**
Pure self-direction drifts toward whatever is most pleasant to write. Ranking targets at
the *end* of a round — when you know the most — and consuming that ranking at the *start*
of the next puts the decision where the information is.

**"Try to break your own result before you report it."**
The single highest-value clause. R1 produced a clean, confident deload comparison, then
asked why never-deloading won so uniformly, and discovered the model could not represent
volume at all. Without that step the round would have shipped a table of numbers that
were all artefacts.

**"Check whether the finding is a property of training or a property of the model."**
The specific version of the above for this project. Simulation output always looks like a
fact about the world.

**"Size the term before optimising it."**
Added after R1 spent most of a round on a term worth under one point. Costless to ask,
and it is the difference between a project that converges and one that polishes.

**"Separate what you verified from what you inferred."**
Every number in MESO is currently inferred. The danger is not that they are wrong, it is
that repetition launders them into facts. `DECISIONS.md` exists to resist that and needs
active maintenance to keep working.

**"What would prove it wrong."**
A decision without a falsification condition is a belief. It also makes reversal socially
cheap later — you are not admitting error, you are hitting a condition you wrote down in
advance.

---

## On "keep looping"

Two readings: "iterate deeply each time I ask" and "run this on a timer". This prompt is
written for the first, and works for both — under `/loop` it fires on a schedule and each
firing is one full pass, picking its target from the previous round's ranking. Each
firing costs a model invocation, which is the thing to be aware of if the rounds start
outrunning the ideas.
