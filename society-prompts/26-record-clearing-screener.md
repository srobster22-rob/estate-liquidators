# 26 — Record Clearing Screener

**What it is:** A screener that tells someone whether their old conviction might be eligible for
expungement, sealing, or set-aside in their state — what the waiting period is, what it costs,
and which legal aid clinic files it. It never says "you qualify," and it never asks for a name.

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[COUNTY]`, `[CITY]`, `[LANGUAGES]`.

---

```text
You are building a criminal record clearing eligibility SCREENER for [STATE]. Build it now; do
not ask me clarifying questions. Where you need a decision I did not make, choose the option
least likely to give someone false hope or false despair, state your choice, and keep going.

Read SAFETY + LEGAL before writing any code. It constrains the architecture and the copy, and
it contains one rule that overrides everything else in this brief.

=== THE PEOPLE ===

Terrence is 41. Nine years ago he pleaded guilty to a felony drug possession charge, did his
time, finished probation in 2019, and has had nothing since. He has been turned down for four
apartments and two jobs. He has heard the word "expungement" and assumes it costs thousands of
dollars and is for other people.

He is right that it costs something and wrong about almost everything else. Many states have
substantially expanded record clearing in the last decade, several have automatic or "clean
slate" clearing for some offenses, and there are free legal clinics that do nothing but this.

The second person is Alicia, whose record is a dismissed charge that never resulted in a
conviction — which in most states is the easiest thing there is to clear, and which is sitting
on background checks costing her jobs because nobody told her she could.

The third is a legal aid attorney who runs a monthly clinic, has capacity for twelve people, and
currently spends the first half of every appointment on people who are not eligible.

=== THE PROBLEM ===

A large share of American adults have a criminal record, and the collateral consequences —
housing, employment, licensing, education — persist for decades after any sentence ends. Look up
current figures from a named source with a year before displaying any number; if you cannot
verify one, display none.

Record clearing law is entirely state law, it is intricate, and it changed substantially in many
states over the last ten years. Terrence's belief that it isn't for him is a screening problem,
not a legal one — and a screener that gets him into that clinic with the right paperwork is the
whole product.

=== THE RULE THAT OVERRIDES EVERYTHING ===

**This tool routes people to a lawyer. It does not replace one.**

Record clearing involves reading a criminal history transcript, identifying the precise offense
of conviction and its statutory subsection, applying waiting periods that run from events that
are themselves ambiguous, and filing a petition in the sentencing court. People get this wrong
in both directions constantly — including lawyers who do not practice in the area.

So the output of this screener is never an answer. It is a sorted, honest "worth asking about"
with the specific questions to bring, and the name and phone number of the free clinic that
handles it in [COUNTY]. Research that clinic and verify it by phone before you write a line of
code. If there is no clinic in [COUNTY], find the nearest one and the [STATE] bar's pro bono
program, and say plainly in the app that this is a gap.

If you cannot verify [STATE]'s record clearing statutes from primary sources, **do not ship a
screener at all.** Ship the questions-to-ask page, the document-gathering checklist, and the
clinic directory. Those three things carry most of the value and none of the risk.

=== WHAT SUCCESS LOOKS LIKE ===

Terrence answers eight questions without giving his name, learns that his conviction type has a
waiting period he passed four years ago, walks into the clinic with his court disposition
already printed, and the attorney spends the appointment on his case instead of on triage.

=== BUILD THIS ===

1. START (/) — One screen, no marketing, and one sentence that does real work:
   "This asks about the kind of case, not about you. No name, no date of birth, nothing saved."
   Then, immediately below, the most under-known fact in the domain, stated plainly and cited:
   in most states a charge that was dismissed, dropped, or ended in acquittal can be cleared far
   more easily than a conviction, and many people do not know a non-conviction shows up on
   background checks at all. Verify [STATE]'s rule and lead with it.

2. THE QUESTIONS — At most 8, one per screen, back button always, "I'm not sure" on every one
   and never a dead end:
   Q1. Was there a conviction, or was the case dismissed, dropped, acquitted, or diverted?
   Q2. Adult or juvenile case?
   Q3. Roughly what kind of offense? (plain-language categories that map to [STATE]'s statutory
       classes — research these; do not use the raw class letters, and do not ask the user to
       identify a statute subsection)
   Q4. Roughly what year was the case closed?
   Q5. Did you finish everything the court ordered — time, probation, classes, fees?
   Q6. Are any fines or restitution still owed? (In several states this is a bar, and in several
       it is not; verify, and if [STATE] bars on unpaid fines, say so and route to any
       waiver process.)
   Q7. Anything since? Any new case, anywhere?
   Q8. Which county was the case in?
   Never ask for a name, date of birth, case number, or the specific statute.

3. RESULTS — Three buckets, never a percentage, never the word "eligible":
   "Worth asking about now" / "May be worth asking about later — here's roughly when" /
   "Probably not under [STATE]'s current rules — but rules change, and here's who to ask anyway."
   Each result shows:
   - Which rule produced it, in plain language, with the specific number ("[STATE] requires X
     years after the case closes for this kind of offense")
   - The statute citation, its retrieval date, and a link to the primary source
   - What the process is actually called in [STATE] — expungement, sealing, set-aside, vacatur,
     certificate of relief — because the words differ and using the wrong one at a clerk's
     window wastes a trip
   - Whether [STATE] has automatic or "clean slate" clearing that might already have applied
     without anyone telling him. Verify this; several states now do, and it is life-changing
     news that nobody delivers.
   - What it costs: filing fees, whether a fee waiver exists and how to request it
   - Roughly how long it takes
   - The clinic, with address, phone, hours, and what to bring
   Every result ends with: "Only a lawyer who reads your actual record can tell you. This is a
   guess from eight questions."

4. GET YOUR RECORD — The step that makes the clinic appointment productive, and the thing nobody
   explains. Research and verify for [STATE]: how to obtain your own criminal history from the
   state repository, the cost, the ID needed, the turnaround; how to get the court disposition
   from the clerk in the county of conviction; and the difference between the two, because they
   are different documents and the clinic needs both. Generate a printable request checklist.

5. WHAT IT DOES AND DOESN'T FIX — Plainly, cited. Clearing a record does not always mean it
   disappears from everything: verify how [STATE] treats law enforcement access, immigration
   consequences, firearms rights, professional licensing, and background checks run by private
   companies that may hold stale data. Overpromising here is cruel — someone budgets a year and
   a filing fee for an outcome that was never on offer.
   Include, prominently: even after clearing, private background check companies sometimes keep
   reporting old records, and there is a federal process for disputing inaccurate reports. Link
   it.

6. WHILE YOU WAIT — Things that help before or without clearing, each verified: [STATE]'s
   ban-the-box or fair-chance hiring law if it has one, certificates of rehabilitation or relief
   if [STATE] issues them, housing protections, and the fair-chance obligations of employers who
   run background checks. This section matters because most people arrive years before they are
   eligible and the honest answer is otherwise "come back in three years."

=== ARCHITECTURE: RULES AS DATA ===

Same as project 02, and for the same reason. Every rule is a dated, sourced JSON file in
/rules/[STATE_ABBR]/ with effectiveFrom, a primary-source URL, a retrieval date, embedded test
cases, and a status of verified | unverified. Unverified rules do not reach the UI at all — the
program is omitted and listed in the report.

Record clearing statutes change often and several states have amended them repeatedly. A rule
past its effectiveTo renders a stale banner and logs a startup warning. Write /rules/README.md
telling a future maintainer exactly which pages to check and when.

=== DATA MODEL ===

There is no user database. Answers live in memory and sessionStorage and are gone when the tab
closes. Say so on the first screen and make it architecturally true.

Permitted server-side persistence: an aggregate counter of (date, bucket) with no other field.
If you cannot build it without being able to reconstruct an individual, do not build it.

=== STACK ===

- Static export, rules evaluated client-side. This is a privacy decision: a server-side record
  of who asked about clearing a felony is a dataset that should not exist.
- TypeScript, Zod-validated rules at build time.
- No database for user data. No analytics, no third-party fonts, no error reporting SaaS.
- Under 150KB JS. [LANGUAGES] from the first commit.

=== HARD CONSTRAINTS ===

- NEVER ask for or store: name, date of birth, SSN, case number, address, or the specific
  statute of conviction. The screener works without all of them.
- The words "you qualify," "you are eligible," and "approved" never appear. Build-failing grep.
- Every displayed rule carries its citation and retrieval date.
- Bias toward "worth asking about." The two errors are not symmetric: a wasted clinic
  appointment costs an hour; a wrongly discouraged person loses years of housing and work.
  Encode the asymmetry and write it in a code comment.
- Reading level 6th grade, checked in CI. No statutory jargon in the question flow.
- [LANGUAGES], professionally reviewed.
- WCAG 2.2 AA. Full keyboard operation. Works on an old phone.
- Zero third-party requests. Someone worried about a record should be able to open dev tools and
  watch nothing leave.

=== DO NOT BUILD ===

- No petition generation, no court forms, no filing. This is where errors become expensive and
  where the unauthorized-practice-of-law line is. The clinic files.
- No LLM in the eligibility path, ever. A generated eligibility answer cannot be audited by the
  attorney at the M2 gate, and that review is this project's only real quality control.
- No background check, record lookup, or integration with any court or state records system.
  Do not build a tool that searches for people's records — that is the harm, not the fix.
- No percentage, score, or confidence number. Three buckets.
- No account, no email capture, no "we'll remind you when you're eligible."
- No referral fees, no paid attorney marketplace, no partnerships with record-clearing services
  that charge for what a free clinic does. That industry targets this exact user.
- No advice about immigration consequences beyond "this can affect immigration status in ways
  that are complicated — talk to an immigration lawyer before filing," with a link. Verify and
  state that warning; a clearing that helps in state court can hurt in immigration court.

=== ACCEPTANCE TESTS ===

1. Completing all 8 questions sends no network request containing any answer.
2. Every rule validates; one missing a source URL, authority, or retrieval date fails the build.
3. Every rule's embedded test cases pass.
4. A rule with status unverified never reaches the UI.
5. A rule past effectiveTo renders the stale banner and logs a warning.
6. The forbidden-phrase grep ("you qualify", "you are eligible", "approved", "guaranteed") finds
   nothing in the built output.
7. Answering "I'm not sure" to every optional question still produces results, and moves affected
   items toward "worth asking about" rather than excluding them.
8. Identical inputs produce identical results; the rule that decided each is named on screen.
9. No name, DOB, case number, or address field exists anywhere in the codebase — grep test.
10. The non-conviction path is reachable from the first screen in one tap.
11. Every result includes the clinic's verified phone number.
12. All strings render in every language in [LANGUAGES]; a missing key fails the build.
13. Reading level at or below grade 8 for every user-facing string.
14. axe-core clean; full flow completable by keyboard; no third-party requests.

=== MILESTONES ===

M0 — Find the clinic and verify it by phone. Before any code.
  EXIT: you have spoken to whoever runs record clearing clinics in [COUNTY], confirmed how
  someone gets an appointment and what to bring, and asked them the question that shapes this
  entire project: what do people arrive believing that is wrong?

M1 — The document-gathering checklist and the questions-to-ask page.
  EXIT: the clinic says they would hand this to someone. This ships even if the screener never
  does.

M2 — The rules engine and the screener, [STATE] rules verified from primary sources.
  EXIT: a legal aid attorney who does this work reviews every rule, every result string, and
  every citation. **This gate is the project.** Without it, do not ship the screener — ship M1
  and stop, and say so.

M3 — What it does and doesn't fix, while-you-wait, second language.
  EXIT: a native speaker reviews the translation; the attorney reviews the limitations page.

M4 — Ten real people through the clinic.
  EXIT: ask the clinic whether triage got faster and whether anyone arrived with wrong
  expectations because of you. That second question is the one that matters.

=== SAFETY + LEGAL ===

- Not legal advice, not a lawyer, not an eligibility determination. On every screen, with the
  clinic's name and number.
- The unauthorized practice of law is a real line and it varies by state. Providing legal
  information and generating no filings keeps you on the right side of it; check [STATE]'s rule
  and note what you found in the README.
- The asymmetry rule again, because it is the ethical core: wrongly discouraging Terrence costs
  him years. Wrongly encouraging him costs him an appointment. When a rule is ambiguous or your
  data is uncertain, resolve toward "ask someone."
- Never state or imply that clearing makes a record vanish everywhere. Verify [STATE]'s actual
  effect and state its limits.
- Immigration: flag it, route it, never advise on it.
- Store nothing. The threat model includes a person who does not want a record of having asked.
- Do not build or link anything that searches for other people's records.
- Do not display any statistic you have not sourced with a year.

=== HOW TO REPORT BACK ===

Lead with M0: who runs the clinic, what they told you people get wrong. Then: every [STATE]
statute you verified with its URL and date; every rule you could not verify and therefore did
not ship; whether [STATE] has automatic clearing; what the attorney changed at M2; and whether
you concluded the screener should ship at all.
```

---

## Why it's shaped this way

**M1 ships without the screener, deliberately.** The document checklist and the
questions-to-ask page carry most of the value — an appointment where the attorney reads the
actual disposition instead of spending forty minutes on triage — and they carry none of the risk
of an eligibility engine built on statutes you couldn't verify. If M2's attorney review can't
happen, the honest move is to ship M1 and stop, and the brief says so out loud.

**The first screen leads with non-convictions** because it's the biggest, cheapest win in the
domain and almost nobody knows it. A dismissed charge still shows on background checks, and in
most states it's the easiest thing there is to clear.

**"Get your record" is the unglamorous middle of the project and probably its highest leverage.**
The state repository history and the court disposition are two different documents, the clinic
needs both, and nobody explains that anywhere.

**The error asymmetry is stated twice and encoded once.** A wrongly discouraged Terrence doesn't
come back in a year to re-check — he concludes it isn't for him, permanently. That's the failure
this design bends away from.

**No petition generation.** It's the feature that looks like the finish line and it's where the
unauthorized-practice line and the expensive mistakes both live. The clinic files; you get people
to the clinic ready.

**Before you build:** find the clinic first and ask what people arrive believing. That single
question will restructure your question flow.
