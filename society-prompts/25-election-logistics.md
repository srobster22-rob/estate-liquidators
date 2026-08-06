# 25 — Election Logistics + Ballot Deadlines

**What it is:** Not who to vote for — whether your registration is current, what ID you need,
when your mail ballot has to be *received* rather than postmarked, and where your polling place
moved to. Deadlines with citations, sourced only from your state's own election office.

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[COUNTY]`, `[CITY]`, `[LANGUAGES]`.

---

```text
You are building an election logistics tool for voters in [COUNTY], [STATE]. Build it now; do
not ask me clarifying questions. Where you need a decision I did not make, choose the option
that keeps the tool strictly procedural and sourced to official election authorities, state your
choice, and keep going.

Read THE NEUTRALITY LINE and SAFETY + LEGAL before writing a word of copy. This is the project
in the kit where a small drift in tone destroys the whole thing.

=== THE PEOPLE ===

Renata moved apartments in March, eleven blocks, same county. She assumes her registration
followed her. It did not. She will find this out at a polling place on election day, where she
will be offered a provisional ballot and will not know whether it counts.

Darnell requested a mail ballot. He is planning to drop it in a mailbox on election day, because
that is what you do with mail. In [STATE] that may be a week too late — many states require the
ballot to be *received* by close of polls, not postmarked by it, and that distinction throws out
real ballots every cycle.

Yuki, 19, is voting for the first time. Nobody has told her that a first-time voter who
registered by mail may face an ID requirement that other voters do not.

None of them need persuading. They need four facts and a deadline.

=== THE NEUTRALITY LINE ===

This tool is about mechanics only. It never:

- names a candidate, party, measure, or campaign
- characterizes a policy, a bill, or a ballot question beyond quoting the official ballot text
- says voting is important, encourages turnout, or uses any motivational language
- links to anything other than an official election authority or a nonpartisan legal-services
  organization
- draws any conclusion about election administration, fraud, security, or any dispute

Write that list into the README as a standing constraint, and add a build-failing check that
greps the output for a blocklist of persuasive and characterizing words. The moment this reads
as advocacy it becomes something people argue with instead of something they use, and it stops
being safe for a library or a clerk's office to hand out.

=== THE PROBLEM ===

Election administration in the US is county-level and the details that decide whether a ballot
counts — registration deadlines, ID rules, mail ballot receipt deadlines, cure processes,
provisional ballot handling, polling place assignment — vary by state and change between cycles,
sometimes by court order weeks before an election.

Research and verify, from [STATE]'s Secretary of State (or equivalent) and [COUNTY]'s election
office ONLY:

- Voter registration deadline, and whether [STATE] has same-day or election-day registration
- How to check and update a registration, and what happens if you moved within the county,
  between counties, or between states
- ID requirements: at the polls, for first-time voters, for mail ballots
- Mail/absentee ballot: who may request one, request deadline, whether it must be received or
  postmarked by a date, drop box availability and hours, and the signature-cure process and its
  deadline — the cure process is under-known and it is how a rejected ballot gets fixed
- Early voting dates, hours, and locations
- Polling place lookup, and the rule for voting at the wrong precinct
- Provisional ballots: when you get one, what makes it count, and how to check whether yours did
- Voting with a disability, curbside voting, and accessible equipment rights
- Rules for voters who are unhoused, recently moved, in jail pretrial, or on probation/parole —
  eligibility after a conviction varies enormously by state and is the single most common piece
  of misinformation in this whole domain. Verify [STATE]'s rule precisely and cite the statute.
- Time off work to vote, if [STATE] provides it
- Language assistance and whether [COUNTY] is covered by federal language-access requirements

Every one of these gets a source URL from an official election authority and a verification date.
If you cannot verify one from an official source, the app does not state it — it links the
county election office and its phone number instead. Never source an election rule from a news
article, an advocacy organization, a wiki, or a model-legislation site.

=== WHAT SUCCESS LOOKS LIKE ===

Renata checks her registration three weeks out and re-registers. Darnell learns his ballot must
be received by a date, and uses a drop box. Yuki brings the right ID the first time.

=== BUILD THIS ===

1. CHECK FIRST (/) — One screen, one instruction, above everything:
   "Check that you're registered, even if you're sure. It takes 30 seconds."
   with a direct link to [STATE]'s official registration lookup and the [COUNTY] election office
   phone number. Moving is the single most common reason a registration goes stale, and people
   do not think of it as an election event.

2. YOUR DEADLINES — Enter an election date (or pick from a list you maintain), and get every
   deadline computed backward from it as a real date, each with its rule citation:
   registration, mail ballot request, mail ballot return (labelled RECEIVED BY or POSTMARKED BY
   in capitals — this is the distinction that throws out ballots), early voting window, cure
   deadline.
   Show days remaining. Offer an .ics download, because a PWA cannot be relied on to notify.
   VERIFY every deadline against the official source. Where a rule is under litigation or
   recently changed, say so and link the official page rather than printing a date.

3. WHAT DO I BRING — ID requirements, in plain words, with the exact list of acceptable
   documents quoted from the official source, and the separate rules for first-time voters and
   for mail ballots. Include what to do if you do not have any of them — most states have an
   affidavit or provisional path, and almost nobody knows it.

4. MY SITUATION — Short, plainly-written pages for the cases that generate the most wrong
   answers, each cited:
   - I moved (within county / between counties / from another state / recently, after the
     deadline)
   - I'm a student, and which address I may use
   - I have a conviction in my past — [STATE]'s actual rule, cited to statute
   - I'm unhoused and have no fixed address
   - I'm in jail but not convicted
   - I'm overseas or military (UOCAVA)
   - I need language help, or I have a disability
   - My name changed
   These are procedural questions with procedural answers. Do not editorialize about any of them.

5. WHERE — Polling place and drop box lookup, linked to the official tool rather than
   reimplemented. If [COUNTY] publishes locations as data you may display them, with the source
   and a "confirm on the official site" link, because locations move late.

6. AFTER YOU VOTE — Ballot tracking if [STATE] offers it, how to find out if a mail ballot was
   rejected, and the cure process with its deadline. A voter who learns their signature was
   rejected inside the cure window can fix it; outside it, they cannot.

7. WHO TO ASK — [COUNTY]'s election office, [STATE]'s election hotline, the federal Election
   Assistance Commission, and a nonpartisan voter-protection legal line. Every number verified
   by calling it.

=== DATA MODEL (local only) ===

elections: id, name, date, kind
rules: id, jurisdiction, topic, body, params jsonb, deadline_rule|null,
  source_url, source_authority, retrieved_on, effective_from, effective_to, status
  enum(verified|unverified|in_litigation)
saved: election_id, reminders_set, notes   -- localStorage only; no server, no account

The app stores no personal data. Not a name, not an address, not a party, not whether someone
intends to vote. See SAFETY.

=== STACK ===

- Static site: Astro or Vite + TypeScript, prerendered, offline-capable.
- Rules as dated, sourced JSON validated by Zod at build time. A rule without an official source
  URL, an authority name, and a retrieval date fails the build. Embedded test cases per rule.
- Deadline math handles the "received by" vs "postmarked by" distinction as a typed field, not a
  string, so the UI cannot render one as the other.
- No backend, no analytics, no third-party requests. Under 100KB JS.
- [LANGUAGES] from the first commit.

=== HARD CONSTRAINTS ===

- Every rule cites an official election authority, by name, with a retrieval date, displayed.
- Any rule marked unverified or in litigation renders as a link to the official page, never as a
  stated deadline.
- The receive-vs-postmark label is rendered in capitals and is covered by its own test.
- Rules older than one election cycle render a staleness banner. Election rules change between
  cycles and a stale deadline is the worst output this app can produce.
- Reading level 6th grade. [LANGUAGES] on every page.
- WCAG 2.2 AA; 18px minimum; fully printable.
- Zero personal data, zero network requests to anything, zero analytics.

=== DO NOT BUILD ===

- No candidate information, sample ballots with commentary, endorsements, voter guides, or
  issue explainers. Quote official ballot text or nothing.
- No registration submission, no ballot request submission. Link the official tool.
- No turnout encouragement, no "make your voice heard," no share buttons, no pledge features.
- No account, no email capture, no reminder emails, no phone numbers collected.
- No collection or display of any voter file data, even though much of it is public in many
  states. Do not build a lookup of individuals.
- No LLM generating any statement about election law or procedure.
- No claims about election security, integrity, fraud, or any active dispute.
- No polling place crowdsourcing, wait-time reporting, or user-submitted anything.
- No multi-state expansion until one county is correct and has survived one election.

=== ACCEPTANCE TESTS ===

1. Every rule has an official source URL, an authority name, and a retrieval date; one missing
   any fails the build.
2. A rule with status unverified or in_litigation renders a link, never a computed date.
3. Deadlines compute correctly backward from an election date, verified by hand against the
   official calendar for at least three elections.
4. The mail ballot return rule renders RECEIVED BY or POSTMARKED BY in capitals and matches the
   typed field; a mismatch fails the test.
5. Rules past one election cycle render the staleness banner.
6. The blocklist grep finds no persuasive or characterizing language in any built output.
7. No candidate, party, or measure name appears anywhere in the codebase or content.
8. No personal data is written to storage during a full journey — asserted, not inspected.
9. Zero network requests to any origin during a full journey.
10. The .ics export lands the deadlines on the correct dates in a calendar app.
11. All content renders in every language in [LANGUAGES].
12. axe-core clean; the whole flow completes with keyboard only; readable at 200% zoom.
13. Every page prints legibly.
14. The conviction-eligibility page cites a [STATE] statute and no other kind of source.

=== MILESTONES ===

M0 — The rules research, written up before any code.
  EXIT: a document with every rule above, its official source URL, the authority, and the
  retrieval date. Confirm at least five of them by calling the [COUNTY] election office.

M1 — Deadlines + what to bring.
  EXIT: hand-verify three elections' worth of deadline math against the official calendar.

M2 — The situation pages.
  EXIT: an election official, a county clerk, or a nonpartisan voter-protection attorney reads
  every page. Do not skip this gate — the conviction-eligibility page in particular is where
  wrong information is most common and most consequential.

M3 — Second language, print, tracking, cure.
  EXIT: a native speaker reviews the translation.

M4 — One election.
  EXIT: run it through a real election cycle and report what changed under you mid-cycle. It
  will be something.

=== SAFETY + LEGAL ===

- Not legal advice. On every page, with [COUNTY]'s election office and a nonpartisan voter
  protection line, both verified by phone.
- Never state an election rule you could not verify from an official election authority. This is
  the one domain in this kit where a plausible-sounding wrong answer is also the exact shape of
  misinformation, and being confidently wrong here does harm beyond the individual reader.
- Do not present the tool as official. A persistent line: "Independent volunteer project. Not
  [COUNTY] or [STATE] government. Always confirm at <official URL>."
- Correct errors visibly, with a public corrections log. Never silently edit a rule page.
- Conviction-related eligibility is the most misreported rule in American elections and the fear
  of getting it wrong keeps eligible people from voting. Get it exactly right, cite the statute,
  and route to a legal-services organization for anything specific.
- Store nothing about the user. A record of who looked up voting rules is a record that should
  not exist, and the only way to promise that is to have no server.
- Introduce yourself to the [COUNTY] election office before launch. They are usually glad
  someone is explaining the mechanics accurately and will correct your pages.

=== HOW TO REPORT BACK ===

Tell me: every rule you verified, its official source and authority and date; which you could
not verify and therefore did not state; what the [COUNTY] office confirmed by phone; the
deadline math results; and what the M2 reviewer corrected. Flag anything currently in
litigation.
```

---

## Why it's shaped this way

**"Check your registration" is the whole first screen** because moving is the most common way a
registration goes stale and nobody thinks of a move as an election event. It's thirty seconds
of work weeks before it matters, and it prevents the provisional-ballot scenario entirely.

**Received-by versus postmarked-by is a typed field, not a string.** It is the single distinction
that invalidates the most ballots, it varies by state, and rendering one as the other is a bug
that costs somebody their vote. Making it a type means the UI cannot get it wrong.

**Official sources only, enforced.** Election rules are the one domain in this kit where a
confidently wrong answer is indistinguishable in shape from misinformation. Sourcing from
advocacy groups or news coverage — even accurate ones — makes the tool arguable. The Secretary
of State's own page is not arguable.

**The neutrality blocklist exists because tone drifts.** Every draft of civic content slides
toward encouragement, and encouragement makes this a partisan artifact in the eyes of half its
potential audience — including the county clerk whose cooperation makes it accurate.

**Conviction eligibility gets its own gate** because it is the most misreported rule in American
elections, and the direction of the error keeps eligible people home.

**Before you build:** call the [COUNTY] election office and ask what people get wrong most. The
answer is usually a deadline, and usually not the one you'd guess.
