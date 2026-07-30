# The Iteration Prompt

Paste this to continue the work. It's written to be reusable across sessions, and to survive
the fact that a fresh session won't remember any of this conversation.

---

## The prompt

> Continue the Estate Liquidators design work in `C:\Users\srobs\estate-liquidators`.
> Read `README.md` and `DECISIONS.md` first — they're the map and the settled arguments.
>
> **Each time I run this, do a full self-directed pass:**
>
> 1. **Pick the target yourself.** Choose the highest-value gap — the thing whose absence
>    most endangers the build. Don't ask me what to work on; tell me what you picked and why
>    it beat the runner-up.
> 2. **Spec it to implementation depth.** Concrete numbers, tables, pseudo-code, tuning
>    values. A spec I can't build from is a blog post.
> 3. **Then sweep for consistency.** Reconcile anything the new work contradicts elsewhere,
>    and collapse duplicated facts so there's exactly one source of truth per number. Say
>    what you reconciled.
> 4. **Log the non-obvious calls** in `DECISIONS.md`: the decision, the reasoning, and *what
>    would prove it wrong*. Move any decision the new work invalidates.
> 5. **Report back:** what you improved, what you deliberately left rough and why, and the
>    two or three things you'd attack next, ranked.
>
> **Standing constraints:**
>
> - **Optimise for four friends laughing in a hallway.** Where good engineering and funny
>   conflict, pick funny — and say out loud that you're doing it, and what it costs.
> - **This is a foundation, not a product.** Leave seams. Don't gold-plate, don't
>   over-specify things a playtest will answer in an hour, and never pretend a guess is a
>   measurement.
> - **Separate what you verified from what you inferred.** Asset availability, licensing,
>   API behaviour, version support — flag these explicitly as unverified whenever you lean
>   on them.
> - **Pressure-test your own work before you hand it over.** Ask how four experienced
>   players would break it in one evening, and fix what you find rather than shipping it for
>   me to catch.
> - **Don't ask permission to proceed.** Do the work, then tell me what you did.
>
> Work only in that folder. Never commit — this repo is shared across sessions.

---

## Why each clause is in there

Adapt freely, but these are the load-bearing ones:

**"Pick the target yourself... tell me why it beat the runner-up."**
Self-direction without accountability drifts toward whatever's easiest to write. Forcing a
stated runner-up makes the prioritisation visible and arguable.

**"A spec I can't build from is a blog post."**
The failure mode for design docs is confident prose with no numbers in it. Demanding tuning
values and pseudo-code makes vagueness obvious.

**"Then sweep for consistency."**
This is the clause that keeps a growing doc set from rotting. Every pass adds facts that
contradict older ones — the audio spec's loudness model silently invalidated two tables in
two other documents. Without an explicit sweep step, those just sit there and drift.

**"What would prove it wrong."**
The single highest-value habit in the whole prompt. A decision with no falsification
condition is a belief, and beliefs are how projects spend eighteen months building the wrong
thing. It also makes it socially easy to reverse a call later — you're not admitting error,
you're hitting a condition you wrote down in advance.

**"Where good engineering and funny conflict, pick funny — and say what it costs."**
The default pull is toward the safe technical choice. Kinematic carried items never jitter
and would delete the game. The second half of the clause matters as much as the first: the
cost gets stated, not hidden.

**"Leave seams. Don't gold-plate."**
Prevents the model from polishing the parts it finds pleasant instead of building the parts
that are missing. Also stops it from over-specifying things one playtest would answer in an
hour.

**"Separate what you verified from what you inferred."**
Package maintenance status, licensing tiers, and version support all change, and a model's
knowledge has a cutoff. Anything downstream of an unflagged guess inherits the risk silently.

**"Pressure-test your own work before you hand it over."**
The first pressure test in this project killed a free-aggro-reset exploit, a self-
contradicting corpse economy, and a signature mechanic that good players would have skipped
entirely. Making that a standing instruction moves it earlier — the model catches its own
holes instead of you catching them a week later.

---

## What this replaces

The original was: *"do the audio spec next, improve that volume too, keep improving based on
your judgment — not a final product, a solid foundation we can build off. keep looping."*

Everything essential was already in there. What it was missing: a way to pick targets, a
definition of "done" per pass, anything about keeping the documents consistent with each
other, and any mechanism for remembering *why* a decision was made once the conversation
that produced it is gone.

**One note on "keep looping."** It reads two ways — "iterate deeply each time I ask" or "run
this on a timer." This version is written for the first. If you ever want the second, that's
the `/loop` command and it costs a model invocation every time it fires, which is the thing
you've objected to before.
