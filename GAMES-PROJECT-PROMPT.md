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
> ### Then rank them — by cost to disprove, not by excitement
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
> - **Search before you rank, not after.** You are working from memory of the games market and
>   that memory has a cutoff, so every "nothing like this exists" is a guess. Mark the guesses —
>   and then **check all of them against a store before the ranking section, not after it.**
>   Five minutes per card. This is not a nicety: a search is the only instrument here that can
>   *kill* a concept outright, so it strictly dominates every prototype, and a ranking built on
>   unchecked cards will confidently put a shipped game in its top five. That has already
>   happened once with this prompt — the card was even labelled "probably occupied" and got
>   ranked above the thing that would have settled it. **Resolve a named suspicion with the
>   cheapest instrument that can resolve it, before ranking, not with the test the ranking
>   prefers.**
> - **Assume taken until shown otherwise.** Write the cards with a pessimistic prior. "I found
>   nothing" after a real search is a finding; "I can't recall anything" is not.
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

**"Search before you rank, not after."**
Started as `ITERATION-PROMPT.md`'s separate-verified-from-inferred clause, then earned a
stronger form the hard way. Flagging a claim as unverified is *not enough*: when all 46 cards
from the first run were finally searched, **seven were games that already existed — and three
of those seven were cards the document had itself labelled "probably occupied" and then ranked
highly.** The suspicion was recorded and changed nothing, because the ranking criterion (cost
to disprove) only sees tests the document proposes, and a store search isn't one of them. It
should be.

A search can kill a concept outright in five minutes, which no prototype can do at any price.
Two of the seven kills sat in the top eight, and one of them — a salvage game — had its
recommended *weekend prototype* already on Steam, shipped five months earlier. Putting the
search after the ranking buys nothing and ranks against data you know is unreliable.

The corollary is the pessimistic prior. A 15% kill rate across the whole set and 25% inside
the most-considered section says the correlation runs the wrong way from comfort: **the more
thought a concept received, the likelier it was to already exist**, because attention and
market obviousness are the same signal.

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

`GAME-CONCEPTS.md` is this prompt, run once, then corrected twice and fully verified. **39 live
concepts** out of 46 written, nine families, a ranked top eight, and a graveyard of thirty-two.

Every correction is recorded there rather than tidied away, because they're worth more than
the list:

1. **The action quota** above. Family 9 was added when the self-audit caught that forty
   concepts had no twitch in any of them — and the interesting part was that the cause was the
   scoring function, not taste.
2. **The verification clause** above. All 46 cards were then searched. **Seven were games that
   already exist**, three of them on cards already flagged as probably-occupied and ranked
   highly anyway, two of them inside the top eight. Ninety minutes of searching outperformed
   every prototype the document proposed.

**And one thing the prompt got wrong that is still unfixed.** Family 9 now sits at four
against a floor of six. Two replacement concepts were generated and searched *before* being
written up; both died. Action is dense enough that this prompt may not be able to satisfy its
own action quota — which is better information than three padded cards, and is why the breach
is documented rather than papered over. If you hit the same wall, do the same thing.

That's the loop this prompt is for: run it, find where the output is thin or wrong, **fix the
prompt**, re-run only the affected part, and write down the breaches you can't fix. Every
clause above exists because the output embarrassed the previous version of this file.
