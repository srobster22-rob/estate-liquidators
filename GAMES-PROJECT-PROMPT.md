# The Games Project Prompt

The other prompts in this repo assume you already know which game you're making. This one is
for the step before that: **generating a large portfolio of game projects and finding out
which ones are worth a month.**

Estate Liquidators is what one concept looks like after it survives. This produces the pool
it should have been drawn from.

Everything below the line is the prompt. Notes on how to use it, and why each clause is in
there, are at the bottom.

---

## PROMPT

> Generate **40 game concepts.** I want volume, and I want the fortieth to be as considered as
> the fourth. Do not ask me to narrow the brief first — the narrowing is your job, and I'll
> tell you where you guessed wrong.
>
> ### What a concept is
>
> Not a genre and not a mood. A concept is **one mechanic that isn't in a shipped game, and
> the smallest game that could be built around it.** "Cozy roguelike about grief" is a vibe.
> "Aggro follows the most valuable object leaving the house, so you can get rid of the monster
> by handing the vase to your friend" is a concept — it tells you what the player's hands do,
> what the argument in the room is about, and what to build first.
>
> If I can't picture a player's hands, you haven't finished the idea.
>
> ### Each concept, in this shape — every field, every time
>
> - **Name** — a real one. Working titles that describe the genre ("Co-op Horror Extraction")
>   are a sign the idea hasn't found itself yet.
> - **The pitch** — one sentence, the thing you'd say at a table. If it needs two, the concept
>   is two concepts or none.
> - **The loop** — 2–3 sentences. What the player does for ninety seconds, and what makes them
>   do it again.
> - **The bet** — the single mechanical claim the whole thing rests on, stated so it could be
>   wrong. Exactly one. A concept with three bets is three concepts and will ship as none.
> - **Nearest shipped game** — named, specific, and honest about how close it is. **If you
>   can't name one, that is a red flag, not a green one** — say so explicitly and treat the
>   empty space as suspicious until you've worked out why it's empty. Most empty space is
>   empty because someone already tried it.
> - **What kills it** — the observation that would end the project. Not a risk, a *result*:
>   something you could watch happen in a playtest and know it was over. If you can't write
>   one, the concept is unfalsifiable and belongs in the graveyard.
> - **The cheapest test** — the smallest thing buildable in **one day** that would trip the
>   kill condition if it's going to trip. Grey boxes, a spreadsheet, a paper version, two
>   people and a text channel. This field is the most valuable one on the card and the one
>   you'll be most tempted to write vaguely. Don't.
> - **Scope** — team size and months to a *shippable* version, not a demo. Say which of the
>   40 a single person could actually finish.
>
> ### Coverage — I want a spread, not forty variations on your favourite
>
> Left alone, an idea generator produces one genre wearing forty hats. So:
>
> - Organise into **at least six families**, and **no more than six concepts in any one.**
> - **At most three** are co-op horror. It's the current attractor and this repo already has
>   one; I don't need six more.
> - **At least six** are shippable solo in under six months. Small and finishable is a design
>   constraint, not a consolation prize.
> - **At least six** have no combat and no health bar anywhere in them.
> - **At least six are fast** — aim, dodge, timing, combat depth. This quota exists because
>   without it the count comes back at zero, every time, and not for the reason you'd guess.
>   A list ranked by cost-to-disprove drifts away from action *structurally*: an action game's
>   bet is a claim about **feel**, and feel has no paper version, so it can never compete with
>   a systems bet that a spreadsheet settles in an evening. For these six, the one-day test
>   becomes a **playable** one — a 2D grey box, a debug overlay, a dummy — and may cost up to
>   three days. Say so on the card rather than pretending it's an evening.
> - **At least four** you think are commercially unwise but mechanically true — the ones you'd
>   normally self-censor. Mark them. An idea list with no embarrassing entries has been
>   filtered by a marketing instinct rather than a design one.
> - Vary the axes deliberately: player count (1 / 2 / 4 / async / local), session length
>   (5 minutes / 45 minutes / 100 hours), the **core verb** (aim, build, sort, route, listen,
>   negotiate, deduce, wait), and the target feeling (dread, greed, guilt, craft-pride,
>   embarrassment, tenderness, spite). Name the verb and the feeling per family.
>
> ### Banned, because they arrive by default and cost the slot
>
> Roguelike deckbuilder + anything · "Vampire Survivors but ___" · cozy farming with a dark
> secret · extraction shooter reskins · souls-like with a twist · "Papers, Please but for
> ___" as a *pitch* (as a comparable, fine) · anything whose hook is the setting rather than
> the mechanic · anything whose hook is an art style · anything that requires a live service
> to be interesting.
>
> If one of these is genuinely the right answer for a slot, use it and defend it in one line.
> The ban is on arriving there by default.
>
> ### The order of work — this matters more than anything else in this prompt
>
> **Generate → search → run → rank.** The first version of this prompt had only the first and
> last of those, and it confidently put two shipped games in its own top five. The middle two
> steps are where every finding worth having came from.
>
> **1. Generate**, to the shape and quotas above. Mark every "nothing like this exists" as the
> guess it is.
>
> **2. Search every card. Before ranking, not after.** Five minutes each. A search is the only
> instrument here that can *kill* a concept outright, so it strictly dominates every prototype
> at any price, and a ranking built on unchecked cards ranks against data you already know is
> unreliable. Three things follow:
> - **Assume taken until shown otherwise.** "I found nothing" after a real search is a finding.
>   "I can't recall anything" is not.
> - **Resolve a named suspicion with the cheapest instrument that can resolve it** — not with
>   the test your ranking criterion happens to prefer. A card labelled "probably occupied" once
>   got ranked fifth here, above the five-minute check that would have settled it.
> - **The search designs, it doesn't only filter.** It routinely hands you the mechanism. One
>   concept came back from the graveyard because a search surfaced a developer post-mortem
>   explaining why the naive version fails and what the fix is — the rejection had been right
>   about the naive build and wrong about the concept.
>
> **3. Run the cheapest test on your top few. Before ranking, not after.** You wrote a one-day
> test on every card; run some. This is not optional polish — of three concepts tested here,
> **one died outright, one only worked in 4 of 72 parameter settings, and the one that passed
> turned up a mechanic nobody had designed.** A ranking of untested concepts is a ranking of
> guesses about guesses.
>
> **And expect your test to be wrong before the concept is.** This is the most transferable
> thing in this document and the least intuitive: across three test harnesses here, **five
> separate measurements were confidently wrong before they were right** — two tautologies that
> could only ever return a pass, a parameter specified three orders of magnitude too small to
> affect anything, a sentinel value scored as a success, and a criterion that asked whether a
> number moved when it should have asked how many states it moved between. Every one produced a
> quotable, confident, false result. None was catchable by re-running anything. So: for each
> measurement, ask **what it would look like if the thing you fear were true.** If it can't look
> like that, it isn't a test.
>
> **4. Then rank**, on what survived — which will not be what you started with.
>
> ### Ranking — by cost to disprove, not by excitement
>
> Give me a **top eight, ordered**, and state the ordering criterion you used. Default to this
> one: *how cheaply can I find out I'm wrong?* An idea that can be killed in an afternoon
> outranks a more exciting one that needs three months before it tells you anything. Excitement
> is what makes people build the expensive one first.
>
> For each of the eight, say what it would cost to be wrong about it.
>
> And name the **runner-up that just missed** and why. That's the one I'll actually argue with.
>
> ### Check your rejections, not just your keeps
>
> A concept cut for a wrong reason is gone as permanently as a concept kept for a wrong reason
> is expensive — and it's the harder error to catch, because nothing downstream of a bad
> rejection ever complains.
>
> You do **not** have to search every rejection. Do this instead:
>
> - **When the same reason kills more than one concept, that reason is load-bearing — check it
>   once, properly.** A belief used three times and verified zero times is how a whole category
>   gets thrown away on a hunch. This has already happened with this prompt: one unchecked
>   assumption about LLM referees killed two concepts and set the kill condition on a third,
>   and a shipped game contradicts it.
> - **"Nobody has solved this" is a market claim and needs a search**, exactly like "nothing
>   like this exists." It is the same sentence pointed the other way. One rejection in this
>   prompt's output read "nobody has found the middle" about a design space where two games had
>   found the middle.
> - **Never invent supporting evidence.** If the reason is a hunch, write "hunch." A fabricated
>   playtest result that reaches the right verdict is worse than no reason at all, because it's
>   invisible and the habit survives.
>
> ### The graveyard — this is not optional filler
>
> A section of concepts you generated and cut, one line each: **the idea, and the specific
> reason it died.** "Already exists as X." "The bet is unfalsifiable." "The fun is in the
> premise, not the hands." "Needs 40 people online to work."
>
> The graveyard is the part I'll trust the rest of the document because of. A list with no
> visible rejections is a list that didn't reject anything.
>
> ### Standing rules
>
> - **The fortieth idea is why I asked for forty.** Front-loading five good ones and padding
>   the tail is the standard failure and I will see it immediately. If quality genuinely runs
>   out, **stop at the number where it broke and say so** — thirty-one real concepts and an
>   honest note beats forty with nine of them furniture.
> - **Distrust a concept that has no problem.** If you can't name the thing that's hard about
>   building it, you haven't thought about building it. Every card should have some friction
>   visible.
> - **Don't design the sequel.** No progression systems, no meta-currencies, no roadmaps. The
>   question on the table is whether ninety seconds of this is good.
> - **Write it as a file I can come back to**, not as chat output. One document, cards in a
>   consistent shape, scannable.
>
> ### What "done" looks like
>
> A document I can read in twenty minutes and walk out of with **one thing to prototype on
> Saturday** — named, scoped to a day, and with a written-down result that would make me drop
> it. Not a list I feel good about and never open again.

---

## Notes on using this

**What this replaces.** The original was, roughly: *"give me a lot of project ideas, as many
as you can, with enough detail that I could actually start one."* Everything essential was
already in there — volume, and the demand that ideas be actionable. What it was missing:

- **any defence against the tail padding out.** "As many as you can" reliably produces five
  real ideas and thirty-five variations, because nothing in the ask makes the difference
  visible.
- **any structure to the space.** Without coverage quotas you get forty entries from whatever
  genre the model is currently warm on. The families and the axis list are the fix.
- **a definition of "actionable."** "Enough detail to start" is satisfied by a paragraph of
  confident prose. "The smallest thing buildable in one day that would kill it" is not.
- **anything about how you'd know an idea was bad.** This is the same falsification discipline
  as `DECISIONS.md`, moved a stage earlier — before you've committed, rather than after.
- **a way to see what was rejected.** The graveyard is the cheapest possible credibility
  signal, and it's the section that stops the list being a highlight reel.

## Why each clause is in there

Adapt freely. These are the load-bearing ones.

**"One mechanic that isn't in a shipped game, and the smallest game around it."**
The default output of an ideation prompt is genre-plus-setting, which is not an idea — it's a
slot where an idea goes. Forcing the mechanic to be the unit of the pitch is what makes the
list buildable instead of evocative.

**"If I can't picture a player's hands."**
The single fastest test for whether a concept is real. It kills mood pieces on contact and
costs nothing to apply.

**"Exactly one bet."**
Concepts die of ambition, not of ignorance. Three unproven mechanics multiply their failure
probabilities and no playtest can tell you which one is the problem.

**"If you can't name a nearest shipped game, that is a red flag."**
The instinct is to treat empty market space as opportunity. Empty space is usually a grave.
Making the model name the closest thing forces it to reason about *why* the gap is there,
and it turns the "nobody's done this" reflex into a checkable claim.

**"What kills it — not a risk, a result."**
Straight from this project's decision log, and the highest-value habit in any of these
prompts. A concept with no falsification condition can absorb unlimited months, because
there's never a day on which it's disproven.

**"The cheapest test, in one day."**
This is the clause the whole prompt exists to deliver. The point of forty ideas is not forty
games — it's finding the two you can find out about on a Saturday. Note that it is also the
field most likely to come back vague, because writing it honestly requires actually thinking
about the build. Push back on any card where it's a sentence of intent rather than a thing
with a shape.

**The coverage quotas, and the "at most three co-op horror" cap.**
Idea generation collapses toward whatever's salient. Quotas are a blunt instrument and they
work. The "commercially unwise but mechanically true" quota is doing something specific: a
model's market instinct filters early and silently, and some of what it removes is the good
part.

**"At least six are fast."**
Added after the first run of this prompt returned forty concepts with no twitch in any of
them. Worth understanding *why*, because the same distortion applies elsewhere: it isn't
taste, it's the scoring function. Ranking by cost-to-disprove rewards bets a spreadsheet can
settle, and an action game's bet is "this feels good," which no spreadsheet settles. So the
cheap-test clause — the best clause in this prompt — quietly suppresses an entire category.
The quota patches the symptom. Assume it's also suppressing everything else whose quality
lives in execution rather than structure: animation, comedy timing, horror pacing. Add quotas
for those too if you care about them, and don't mistake the patch for the prompt having
changed its mind.

**"Rank by cost to disprove, not by excitement."**
Excitement ranking is why people build the expensive idea first and learn nothing for three
months. This inverts it: the best idea in a portfolio is the one that answers a question
soonest.

**"Stop at the number where it broke."**
Gives the model a way to be honest that isn't failure, which is the only way you get honesty
out of a quantity target. Without it, the instruction "give me 40" is an instruction to
produce 40 things regardless of whether 40 exist.

**"Generate → search → run → rank."**
Began as `ITERATION-PROMPT.md`'s separate-verified-from-inferred clause and earned each later
step the hard way. Flagging a claim as unverified is *not enough*: when all 46 cards from the
first run were finally searched, **seven were games that already existed — three of them on
cards this document had itself labelled "probably occupied" and then ranked highly.** The
suspicion was recorded and changed nothing, because the ranking criterion only sees tests the
document proposes, and a store search wasn't one of them. One kill — a salvage game — had its
recommended *weekend prototype* already on Steam, shipped five months earlier.

The corollary is the pessimistic prior. A 15% kill rate overall and 25% inside the most-
considered section says the correlation runs the wrong way from comfort: **the more thought a
concept received, the likelier it was to already exist**, because attention and market
obviousness are the same signal.

Running the tests was added last and immediately justified itself: of the first three run, one
concept died outright, one survived in only 4 of 72 parameter settings, and the one that passed
produced a mechanic nobody had designed. **A search finds what exists; only running finds what
doesn't work.** The `EMPTY` cards — where a search returns nothing — are precisely the ones a
search cannot help with, and they are also the most tempting.

**"Expect your test to be wrong before the concept is."**
The least intuitive clause here, and the one I'd keep if I could keep only one. Five separate
measurements across three test harnesses were confidently wrong before they were right, and
every one produced a quotable false result that re-running would never have caught. They came
in three flavours worth naming, because they need different defences: **tautologies** (a check
whose construction guaranteed a pass), **units** (a parameter three orders of magnitude too
small to influence anything, which made a whole sweep meaningless), and — hardest — **a wrong
question**, where the code was correct and the criterion asked whether a number moved when it
should have asked how many states it moved between. The defence is the same in all three
cases: for each measurement, state what it would look like if the thing you fear were true.

**"Don't design the sequel."**
Progression systems are the most pleasant thing to write and the least informative. They also
disguise a weak loop — if the ninety seconds isn't good, no meta-layer saves it, and adding
one hides the problem for a year.

**"Check your rejections, not just your keeps."**
Added last, and it's the clause I'd have expected least. Auditing the 25 rejections from this
prompt's first run reversed **no verdicts** but found **six wrong reasons** — including one
belief about LLM referees that had killed two concepts *and* was setting the kill condition on
a live one, and one flat factual error ("nobody has found the middle" about a design space
with two games in it). One rejection cited a playtest pattern that was simply invented.

The asymmetry is what earns it a clause. A bad keep costs a month and announces itself. **A bad
rejection costs the idea and never says a word** — no test fails, no reviewer objects, the
concept is just gone. And the correction had teeth: the falsified referee prediction promoted
a live concept from runner-up to third.

The cheap version of the fix is the one to keep: audit a reason only when it has killed more
than one concept. That caught the one that mattered here and cost six searches.

## Where to weaken it

**If you want fewer, better:** drop to 15 and add "each card gets a full page, including the
first hour of the player's experience beat by beat." The quotas matter less at 15 because
you're no longer fighting the padding failure — you're fighting shallowness instead, which is
a different prompt.

**If you want it for something other than games:** the shape transfers to any portfolio-of-
projects question. Swap "one mechanic that isn't in a shipped game" for "one claim that isn't
in a shipped product," keep the nearest-comparable clause and the one-day test verbatim, and
keep the graveyard. Those three are what make it work; the rest is genre dressing.

**What not to cut:** the kill condition, the one-day test, and the graveyard. Remove any of
those and this becomes a list of forty things you will feel good about and never open again,
which is the exact artefact it was written to avoid.

---

## The output

`GAME-CONCEPTS.md` is this prompt, run once and then corrected over twelve rounds. **39 live
concepts** out of 47 written, nine families, a ranked top eight, a graveyard of thirty-three,
and three kill tests actually executed in `concepts-sim/`.

Every clause above exists because the output embarrassed the previous version of this file:

1. **The action quota** — added when the self-audit caught that forty concepts had no twitch
   in any of them. The interesting part was the *cause*: the scoring function, not taste.
   Ranking by cost-to-disprove structurally suppresses bets about feel.
2. **Search before ranking** — added after all 46 cards were searched and **seven were games
   that already exist**, two of them inside the top eight.
3. **Check your rejections** — added after auditing the graveyard found six wrong reasons and
   one belief that had killed two concepts while setting the kill condition on a third.
4. **Run the tests, and distrust them** — added after three were run: one concept died, one
   survived in 4 of 72 settings, and five of the harnesses' own measurements were wrong first.

**Two things the prompt still can't fix, both stated rather than papered over.** The action
quota is breached — Family 9 sits at three against a floor of six, and both replacement
concepts were searched before being written and died. Action is dense enough that this prompt
may not be able to satisfy its own quota. And the two highest-value items left in the output
need a human: a twenty-person negotiation test and fifty text dossiers read by a friend. No
amount of looping reaches either.

That's the loop this prompt is for: run it, find where the output is thin or wrong, **fix the
prompt**, re-run only the affected part, and write down the breaches you can't fix.
