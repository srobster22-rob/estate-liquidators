# 02 — Benefits Eligibility Screener

**What it is:** Eight questions, no account, no SSN, and a plain-language list of the programs
you might qualify for in your state — each one citing the exact rule and its date, with a link
to the real application. Screening, not determination. It never says "you qualify."

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[COUNTY]`, `[LANGUAGES]` (e.g.
"English and Spanish"), `[ORG]` (the org whose caseworkers will use it, or "no partner yet").

---

```text
You are building a public benefits eligibility SCREENER for residents of [STATE]. Build it
now; do not ask me clarifying questions. Where you need a decision I did not make, choose the
option that reduces the chance of telling someone the wrong thing, state your choice, keep
going.

Read the SAFETY section before you write any code. It constrains the architecture.

=== THE PERSON ===

Renée is 34, in [COUNTY], [STATE]. Her hours got cut from 38 to 22 last month. She has two
kids, 4 and 9. She has never applied for anything. She half-thinks she doesn't qualify, and
she half-thinks applying will cause a problem she doesn't understand. She is on her phone, at
night, and she will close the tab the moment it asks for a Social Security number.

Her second worry, which is the real one: she has heard that using benefits can hurt an
immigration case. This is a live fear in mixed-status households and it stops people from
applying for programs their US-citizen children are entitled to.

=== THE PROBLEM, WITH A NUMBER ===

Participation gaps are the target. A meaningful share of eligible households do not receive
SNAP, and take-up is lowest among working households and older adults — the two groups most
likely to assume they earn too much. Look up the current published participation-rate figures
from USDA FNS before quoting any number in the UI, cite the year, and if you cannot verify a
figure, do not display one at all.

=== WHAT SUCCESS LOOKS LIKE ===

In under three minutes, without giving a name, an email, or an SSN, Renée gets a short list
like: "Based on what you entered, you may qualify for SNAP, WIC, and free school meals.
Here's what each is, here's what to bring, here's where to apply in [COUNTY]." And she leaves
knowing that her kids' school meals do not depend on her immigration status.

=== BUILD THIS ===

1. START (/) — One screen, no marketing. A single sentence: "Answer 8 questions. No name, no
   Social Security number, nothing saved to our servers." Big "Start" button. Language
   switcher in the header for [LANGUAGES].

2. THE QUESTIONS — One question per screen, back button always available, progress shown as
   "3 of 8." Never more than 8 required questions. In this order:
   Q1. How many people live in your household and share meals? (number stepper, 1-12+)
   Q2. How many are under 18? Under 5? Age 60 or older? (three steppers)
   Q3. Is anyone pregnant, or is there a baby under 6 months? (yes/no/prefer not to say)
   Q4. Roughly how much money comes into the household before taxes? (amount + a
       per-week/per-2-weeks/per-month/per-year selector — people know their paycheck, not
       their annual gross. Do the arithmetic for them.)
   Q5. Does anyone have a disability, or receive SSI or SSDI? (yes/no/not sure)
   Q6. Do you pay rent or a mortgage, and roughly how much per month? (amount, "skip" allowed)
   Q7. Do you pay for heat or cooling separately from rent? (yes/no/not sure)
   Q8. What's your ZIP code? (used only to pick the right county office; never transmitted
       with anything else)
   Every question has an "I'm not sure" option that does not dead-end. Every question has one
   line explaining why it's asked.

3. RESULTS — Programs sorted into three groups, with the group label visible:
   "Likely eligible" / "Might be eligible — worth applying" / "Probably not eligible now."
   Never a fourth category and never a percentage or score.
   Each program card shows, in this exact order:
     - The program's plain name and one sentence of what it actually gives you ("SNAP puts
       money on a card for groceries")
     - Why this result: the specific rule that decided it, in plain language, with the number
       ("Your household of 3 is under the $X monthly gross income limit for SNAP in [STATE]")
     - The rule's source, its publication date, and a link to the official page
     - What to bring to apply (documents list)
     - Where to apply: the [COUNTY] office address, phone, hours, and the online application
       URL for [STATE]
     - "This is a guess based on what you typed. Only [STATE agency] can decide."
   At minimum cover: SNAP, WIC, Medicaid/CHIP, LIHEAP, free and reduced-price school meals,
   Lifeline (phone/internet discount), EITC and the Child Tax Credit, SSI, Head Start, and
   [STATE]'s own cash assistance / TANF program. Research which additional [STATE]-specific
   programs exist — utility discounts, property tax circuit breakers, state EITC — and include
   the ones you can verify.

4. THE IMMIGRATION QUESTION — a dedicated, linked, plainly-written page reachable from every
   results page: "Will using these hurt my immigration case?" Explain, accurately and with
   citations to current USCIS public charge guidance: which programs are and are not
   considered, that benefits received by a household member (including US-citizen children)
   are treated differently from benefits received by the applicant, and that this is a
   complicated area where free legal help exists. Link to the current USCIS public charge
   page and to the [STATE] immigration legal aid directory. VERIFY the current guidance before
   writing a word of this; it has changed materially more than once. If you cannot verify it
   from a primary source, write only: "Rules about this changed recently. Talk to a free
   immigration lawyer before deciding — here's how to find one," and link the directory.
   Getting this page wrong is worse than not having it.

5. TAKE IT WITH YOU — A "Print or save" button producing a clean one-page printable summary,
   and a "Copy as text" button. No email capture. No "we'll send you a reminder." If [ORG] is
   a partner, add "Show this to a caseworker at [ORG]" with their address.

=== ARCHITECTURE: RULES AS DATA, NOT CODE ===

This is the most important structural decision in the project. Do not encode eligibility in
TypeScript conditionals.

Every program is a JSON file in /rules/[STATE_ABBR]/, versioned in git:

  {
    "program": "snap",
    "displayName": "SNAP (food assistance)",
    "jurisdiction": "[STATE_ABBR]",
    "effectiveFrom": "YYYY-MM-DD",
    "effectiveTo": "YYYY-MM-DD",
    "source": { "url": "...", "title": "...", "retrieved": "YYYY-MM-DD" },
    "tests": [ { "when": {...}, "expect": "likely" }, ... ],
    "criteria": [ ... declarative conditions over the 8 answers ... ],
    "explanation": { "likely": "...", "maybe": "...", "unlikely": "..." }
  }

Rules:
- Federal Poverty Guidelines are published annually by HHS and change every January. Store
  them as their own dated dataset, not inline in each program. Multiple programs reference
  them at different percentages.
- Every rule file MUST carry effectiveFrom, a source URL, and a retrieved date. A rule
  without a verified source does not ship — omit the program entirely instead.
- If today's date is past a rule's effectiveTo, the app shows that program with a visible
  "These numbers are from [year] and may be out of date" banner, and logs a loud warning at
  startup. It must never silently serve stale limits.
- Each rule file carries its own test cases in the "tests" array, and the test runner
  executes them. Adding a program means adding its tests.
- Write /rules/README.md explaining to a future maintainer exactly how to update for the new
  year: which pages to check, in what order, in which month.

VERIFY EVERY NUMBER BEFORE YOU WRITE IT. Fetch the current figures from primary sources —
HHS for the poverty guidelines, USDA FNS for SNAP, your state agency for state programs. Do
not write any income limit, benefit amount, or asset limit from memory. If you cannot reach a
source, put the program in the rules directory with "status": "unverified" and exclude it
from the UI, and tell me which ones those were.

=== DATA MODEL ===

There is no user database. Answers live in React state and sessionStorage, and are gone when
the tab closes. Say that on the first screen and make it true.

The only server-side persistence permitted:
  rule_files (in git, not a database)
  aggregate_counts: date, program, bucket(likely|maybe|unlikely), count
  — incremented with NO other field, no IP, no session id, no timestamp finer than the day.
  This exists so [ORG] can say "1,200 screenings this month." If you cannot build it without
  being able to reconstruct an individual, do not build it.

=== STACK ===

- Astro or Next.js static export — the whole screener should be static files plus a tiny
  counting endpoint. Rules evaluate client-side. This is a privacy decision: if the answers
  never leave the device, there is nothing to subpoena, leak, or misuse.
- TypeScript. Zod for validating rule files at build time — a malformed rule fails the build.
- No database for user data. SQLite for aggregate_counts only.
- i18n: build for [LANGUAGES] from the first commit. Retrofitting translation is what kills
  bilingual delivery. Use a plain JSON message catalog. Get the Spanish (or other) copy
  professionally reviewed before launch and note in the README that machine translation of
  benefits terminology is not acceptable — the words for "household," "gross income," and
  "qualify" carry legal meaning.
- Under 150KB JS gzipped. It must work on a 5-year-old Android over 3G.

=== HARD CONSTRAINTS ===

- NEVER ask for: name, SSN or any part of it, date of birth, exact address, email, phone,
  immigration status, or citizenship. The screener works without all of them. If a program's
  eligibility genuinely depends on immigration status, describe the rule in the results text
  instead of asking the user to disclose it.
- Reading level 6th grade, measured. Run every user-facing string through a Flesch-Kincaid
  check in CI and fail on anything above grade 8. Prohibited words in UI copy: "eligibility
  determination," "verification," "household composition," "remuneration," "attestation."
- WCAG 2.2 AA, verified by axe-core in CI. Also: the whole flow must be completable with
  keyboard only, and the question screens must work at 200% zoom on a 360px viewport.
- No third-party requests of any kind at runtime. No Google Fonts, no analytics, no error
  reporting SaaS, no map embeds. Someone worried about immigration consequences should be
  able to open dev tools and see that nothing left their device.
- Back button must work and preserve answers. People re-read questions.
- Every dollar figure displayed must be accompanied by its "as of" year.

=== DO NOT BUILD ===

- No accounts, no saved progress across sessions, no email results.
- No document upload, no application submission, no integration with any state system. This
  screens; it does not apply. Applying involves identity verification you must not touch.
- No chatbot, no LLM in the eligibility path. Ever. A generated eligibility answer is an
  unverifiable answer. Rules are data, evaluation is deterministic, results are traceable to
  a cited rule. If you want an LLM anywhere, the only acceptable place is a build-time tool
  that drafts plain-language explanations for a human to review, and it must not run at
  request time.
- No "chance you qualify: 87%." Three buckets, never a score.
- No referral partnerships, no lead generation, no advertising, no monetization of any kind.
  Do not add a "sponsored" anything. This is the failure mode that has destroyed the trust of
  every commercial benefits site.
- No county-by-county customization beyond the office address lookup in v1.

=== ACCEPTANCE TESTS ===

1. Completing all 8 questions never sends a network request containing any answer.
   (Assert this with an intercepting test, not by inspection.)
2. Every rule file validates against the Zod schema; a rule missing `source.url` or
   `effectiveFrom` fails the build.
3. Every rule file's embedded test cases pass.
4. A rule whose effectiveTo is in the past renders the stale-data banner and logs a warning.
5. Household of 3, $2,400/month gross, [STATE]: results are reproducible, and each program's
   explanation names the specific number that decided it.
6. Income entered as "$600 per week" produces the same result as "$2,600 per month" —
   test the frequency conversion explicitly, including the 52/12 weeks-per-month factor, and
   document which convention you used.
7. Choosing "I'm not sure" on every optional question still produces results, with affected
   programs placed in "Might be eligible" rather than excluded.
8. The full flow is completable with keyboard only; axe-core reports zero violations on
   every screen.
9. Every user-facing string scores at or below grade 8 Flesch-Kincaid.
10. All UI strings exist in every language in [LANGUAGES]; a missing key fails the build.
11. The printable summary renders on one page and contains every program's source link.
12. The aggregate counter increments without storing anything that could identify a session.
13. With JavaScript throttled to 3G and CPU 4x slowdown, the first question is interactive in
    under 3 seconds.
14. No request to any domain other than the app's own origin, on any screen.

=== MILESTONES ===

M0 — Rules infrastructure. Schema, validator, FPG dataset, one program (SNAP) with verified
  numbers and passing embedded tests.
  EXIT: `npm test` proves the SNAP rule against 6 hand-computed household scenarios.

M1 — The 8 questions and results UI, one language, three programs.
  EXIT: you complete it on your own phone in under 3 minutes and every displayed number
  traces to a source link you can click.

M2 — Full program set + [STATE] specifics + the immigration page.
  EXIT: a caseworker at [ORG] — or any person who does this work for a living — reads every
  results string and finds nothing wrong. This gate is non-negotiable. Do not skip it because
  it's the slow one.

M3 — Second language, print output, county office directory.
  EXIT: a native speaker reviews the translation, not a machine.

M4 — Five real people, watched, not asked.
  EXIT: five people use it while you sit quietly and take notes. Count how many close the
  tab, and where. Fix that question.

=== SAFETY + LEGAL ===

- The words "you qualify," "you are eligible," and "approved" must never appear. Use "you may
  qualify" and "worth applying." Write a test that greps the built output for the forbidden
  phrases and fails the build.
- A persistent, non-dismissible footer on every screen: "This tool only makes a guess. It is
  not an application and not legal advice. Only [STATE agency] can decide if you qualify."
- Every results page shows the date the rules were last verified.
- Wrong in the "you might qualify" direction costs someone a wasted trip. Wrong in the "you
  don't qualify" direction costs someone a year of food assistance. When a rule is ambiguous
  or your data is uncertain, resolve toward "might be eligible — worth applying," and say in
  the explanation that you weren't sure. State this bias explicitly in the code comments so
  the next maintainer preserves it.
- If [ORG] exists, their name and phone appear on every results page as the human backstop.
  If not, link the 211 service for [STATE] and the legal aid organization for [COUNTY].
- Do not build a "share your results" feature. Screenshots of someone's income situation
  circulating is a harm you would be creating.

=== HOW TO REPORT BACK ===

Tell me: which programs you verified against primary sources and which you could not; the
retrieved dates; the measured reading-level scores; the FCP number; and every place where you
had to guess at a rule. The list of things you could not verify is the most important part of
your report — lead with it.
```

---

## Why it's shaped this way

**Rules as dated, sourced, self-testing JSON is the whole architecture.** Income limits change
every January when HHS publishes new poverty guidelines. A screener with eligibility logic
buried in `if` statements becomes silently wrong every year and nobody notices, because it
keeps returning confident answers. Dated rule files with a stale-data banner fail loudly.

**No LLM in the eligibility path, stated twice, on purpose.** This is the request an agent will
push back on. The reason is traceability: when Renée asks "why did it say that," the answer has
to be a specific rule with a specific citation. A generated answer cannot be audited by the
caseworker at M2, and that review is the only real quality gate this project has.

**Client-side-only evaluation is a threat-model decision, not a performance one.** The intended
user includes people in mixed-status households who have concrete reasons to fear a database of
who asked about benefits. "Open dev tools and watch — nothing leaves your phone" is a claim you
can only make if it's architecturally true.

**Bias toward "worth applying" is asymmetric on purpose.** The two error directions cost
wildly different amounts. Encode the asymmetry deliberately rather than letting it land wherever
the code happens to put it.

**Before you build:** ask a benefits caseworker or legal aid paralegal for 45 minutes. They
will tell you the three questions people actually get wrong, and it will not be the three you
expected.
