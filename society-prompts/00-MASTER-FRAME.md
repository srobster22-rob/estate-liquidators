# The Master Frame

Two things in this file:

1. **The skeleton** — the twelve sections every prompt in this kit uses, and why each exists.
   Read this if you want to write your own briefs.
2. **The generator prompt** — paste it, describe your problem in one messy sentence, and get
   back a brief as specific as the twelve.

---

## 1. The skeleton

Every prompt here has these sections in this order. The order matters: an agent reads
top-to-bottom and starts forming a plan by section 3, so the person and the problem have to
come before the tech.

| Section | What it does | The failure it prevents |
|---|---|---|
| **THE PERSON** | One named individual, their situation, their device, what they're doing at the moment they open this | Software built for an abstract "user" that fits no one |
| **THE PROBLEM, WITH A NUMBER** | The gap quantified — minutes, dollars, percent | "Improve outcomes" — unfalsifiable, so undirectable |
| **WHAT SUCCESS LOOKS LIKE** | One sentence describing a real changed outcome | Shipping features instead of results |
| **BUILD THIS** | Numbered screens and flows, each with its fields and states | The agent inventing a different app than you wanted |
| **DATA MODEL** | Tables and key fields, explicitly | Three incompatible schemas across a codebase |
| **STACK** | Exact, pinned, decided | Twenty minutes of framework comparison in your reply |
| **DATA SOURCES** | Named APIs/datasets + *verify before building* | Hallucinated endpoints returning plausible fake data |
| **HARD CONSTRAINTS** | Perf, a11y, privacy, reading level, offline | The demo that only works on the developer's laptop |
| **DO NOT BUILD** | The scope fence, itemized | Auth systems, admin panels, and an AI chatbot nobody asked for |
| **ACCEPTANCE TESTS** | Numbered, each mechanically checkable | "Done" meaning "the happy path ran once" |
| **MILESTONES** | Phases with an exit criterion each | A half-finished everything |
| **SAFETY + LEGAL** | What it must never claim, store, or do | Real harm, in the projects that touch money, health, or housing |

Two rules that carry most of the weight:

**Every constraint states its consequence.** Not "make it accessible" but "keyboard-only,
because the intended user has tremor and cannot use a trackpad." An agent that knows *why*
makes the right call at the hundred decision points you didn't write down.

**The scope fence is as important as the feature list.** Left unfenced, agents build login
systems. None of these projects need one on day one, and several are actively safer without.

---

## 2. The generator prompt

Copy everything inside the block. Replace the two bracketed lines at the top. Send it.

```text
You are going to turn a rough problem into a build brief specific enough that a coding
agent can start writing files immediately, without asking clarifying questions.

MY ROUGH PROBLEM: [Describe it in one to three sentences. Be concrete about the place and
the people. Example: "In my county, people released from jail lose their Medicaid coverage
and nobody tells them how to turn it back on, so they show up in the ER instead of a clinic."]

WHAT I KNOW ABOUT IT: [Anything real you know — who you've talked to, what org handles this
now, what tool they use today, how many people it affects, what they've told you is broken.
If you know nothing yet, write "nothing yet" and I'll tell you what to go find out.]

=== YOUR TASK ===

First, before writing anything, do this research and report it back in under 300 words:

1. Find who already works on this problem in this place. Name specific organizations,
   agencies, or mutual aid groups. If you cannot find any, say so — that is itself a
   finding, and usually means I should go look harder before building.
2. Find whether a tool for this already exists. If it does, the answer is probably "help
   them, don't rebuild it." Say that plainly if it's true. I would rather hear that than
   get a brief for something redundant.
3. Identify the data that would make this work — datasets, APIs, public records. For each,
   verify it currently exists and is reachable: fetch it, or find current documentation with
   a date. Report which ones you confirmed and which you could not. Never list a source you
   did not check. If an API you expected is deprecated, say so.
4. Name the single hardest thing about this problem. Not the hardest to code — the hardest
   to get right for the person affected. (For a food rescue tool it's perishability windows,
   not the database. For a benefits screener it's being useful without being wrong.)

Then write the brief, using exactly these twelve headings:

THE PERSON — One named individual. Their situation, their phone, their connection, the
literal moment they'd open this thing. Not a demographic. A person with a Tuesday.

THE PROBLEM, WITH A NUMBER — Quantify the gap. Minutes lost, dollars wasted, percent who
don't get the thing they qualify for. If no number exists, state the closest proxy you found
and label it as an estimate with its source.

WHAT SUCCESS LOOKS LIKE — One sentence, describing a changed real-world outcome, not a
shipped feature.

BUILD THIS — Numbered screens or flows. For each: what's on it, what the user does, what
happens next, and the empty/loading/error states. Enough that two developers reading it
would build the same app.

DATA MODEL — Every table, every field, every type, every relationship. Mark which fields
hold sensitive data and what the retention rule is for each.

STACK — Pick and commit. Exact packages, exact versions where it matters. Prefer boring,
widely-documented, deployable free or near-free. Justify anything unusual in one line.

DATA SOURCES — Each named, with its URL, its auth requirement, its rate limit, its update
cadence, its license, and whether you verified it. Include the fallback if it disappears.

HARD CONSTRAINTS — Performance budget with numbers. Accessibility to WCAG 2.2 AA. Reading
level. Privacy: what is collected, where it lives, how long, who can subpoena it. Offline
behavior. Each constraint states the consequence of violating it.

DO NOT BUILD — Itemized. Everything a coding agent would reflexively add that would waste
the first week. Be specific and slightly ruthless.

ACCEPTANCE TESTS — At least 10, numbered, each mechanically checkable. Include at least
three failure-path tests (bad input, dead API, offline) and at least one test that the thing
refuses to do something it shouldn't.

MILESTONES — 3 to 5 phases. Each has an exit criterion that is observable, and each
criterion involves a real person or real data, not a unit test. Order them so the riskiest
assumption gets tested first, not last.

SAFETY + LEGAL — What this must never claim to be. What it must never store. What
disclaimers must appear and where. Which professional line it must not cross (legal advice,
medical advice, benefits determination). What happens when it's wrong, and how the design
limits that damage.

=== RULES FOR WRITING THE BRIEF ===

- Address it to the coding agent as "you." It gets pasted directly.
- No placeholders except values only I can supply (my city, my org). Mark those [LIKE THIS]
  and list them at the very end under "FILL THESE IN BEFORE PASTING."
- Every number must be real or explicitly labeled an assumption. Never invent a statistic.
- Never invent an API endpoint, dataset, or package. If you did not verify it, say
  "UNVERIFIED — check before building" next to it.
- Scope it to something one person can build a usable v1 of in 20 to 40 hours. If the
  problem is bigger than that, carve off the sharpest useful piece and say what you cut.
- If the honest answer is "don't build software for this, the bottleneck is elsewhere," say
  that instead of writing a brief. That answer is worth more than a brief I'd abandon.
```

### Notes on the generator

**The research step comes before the brief on purpose.** The most common failure in
civic-tech is building a thing that duplicates what a local org already runs, or that solves
a problem whose real bottleneck is funding or staffing. Forcing the agent to look first — and
explicitly licensing it to say "don't build this" — catches that in ten minutes instead of
after a month.

**"Never invent a statistic" and "UNVERIFIED — check before building" carry more weight than
they look like they do.** A brief full of confident fabricated numbers and dead endpoints is
worse than no brief, because it burns your trust in the parts that *were* real.

**The 20-to-40-hour fence is what makes it finishable.** Ambition is not the scarce resource
here. The scarce resource is a v1 that a real person actually uses, which is what makes the
next 40 hours worth spending.
