# 19 — Debt Collection Response Kit

**What it is:** A collector called, or a court summons arrived. This tells you which one you're
holding, generates the validation letter or the answer to the complaint, and warns you about the
two sentences that can quietly cost you years of protection.

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[COUNTY]`, `[CITY]`, `[LANGUAGES]`.

---

```text
You are building a debt collection response tool for consumers in [STATE]. Build it now; do not
ask me clarifying questions. Where you need a decision I did not make, choose the option that
protects the user's rights and deadlines, state your choice, and keep going.

Read SAFETY + LEGAL before writing code. There is a specific trap this app exists to prevent
and it constrains the copy on every screen.

=== THE PEOPLE ===

Curtis, 47, [CITY]. Calls started six weeks ago about a credit card he thinks he had around
2016. He is not sure. The caller knew his address and the last four of his Social. Last week
the caller offered to "settle it today" for $400 if he paid over the phone right then.

The second person is Theresa, who opened an envelope containing a summons and complaint with a
court date. She read it, felt sick, put it in a drawer, and is planning to explain herself at
the hearing. Nobody has told her that not filing a written answer is how most of these end — in
a default judgment, entered without anyone hearing her side, followed by wage garnishment.

The third is Curtis's mother, who is receiving calls about a debt that belonged to her late
husband and has been told she is responsible for it.

=== THE PROBLEM, WITH A NUMBER ===

Two facts drive this entire project. Verify both from current sources and cite them:
- The large majority of consumer debt collection lawsuits end in default judgment because the
  defendant never files a written response. Look up the current research — the Pew Charitable
  Trusts and state court administrative offices have published on this — and cite it with a
  year.
- A substantial share of collection accounts are inaccurate, misidentified, already paid, or
  time-barred. Look up the CFPB's consumer complaint data on debt collection for the current
  breakdown and cite it.

Together: the person most likely to lose is the person who did nothing, and a meaningful
fraction of what they lose was never validly owed.

=== WHAT SUCCESS LOOKS LIKE ===

Theresa files a written answer before her deadline, which is a form, not a speech, and which
converts an automatic loss into a case. Curtis sends a validation letter instead of paying $400
over the phone on a debt that may be past [STATE]'s limitations period. Curtis's mother learns
she is generally not personally responsible for her husband's debts and stops taking the calls.

=== BUILD THIS ===

1. TRIAGE (/) — The first screen decides everything, because the deadlines are wildly different.
   One question with three big answers:
   - "A collector is calling or writing me" → validation track
   - "I got court papers" → lawsuit track, and immediately, above everything else, the deadline
     calculator
   - "Money is already being taken from my pay or my bank" → judgment track
   Never bury the lawsuit track. Someone holding a summons has days, and every screen they scroll
   past is a risk.

2. LAWSUIT TRACK — the highest-stakes path in the app.
   - DEADLINE FIRST. Ask the date they were served and how (in person, left with someone, mail
     — the method can change the clock). Compute the response deadline from [STATE]'s civil
     procedure rules for the court named on the papers, which may differ between small claims,
     district, and superior court. Show it as a date and a countdown, with the rule cited.
     VERIFY [STATE]'s actual deadlines from the rules of civil procedure or the court's own
     self-help materials. If you cannot verify with confidence, do NOT compute a date — show
     "your deadline is usually X to Y days; confirm it today with the court clerk at <phone>"
     and make finding the clerk trivial. A wrong deadline in this app is the single worst
     failure it can produce.
   - WHAT THE PAPERS SAY — help them read it: who is suing (the original creditor or a debt
     buyer, which matters), the amount, the court, the case number, the date served.
   - THE ANSWER — generate a written answer to the complaint: caption, case number, a numbered
     response to each allegation (admit / deny / lack sufficient information to admit or deny),
     and a section for affirmative defenses. Research and list [STATE]'s common affirmative
     defenses in collection cases — statute of limitations, lack of standing or failure to prove
     ownership of the debt, mistaken identity, improper service, payment — with a plain
     explanation of each and a clear statement that they should raise only what is true.
     Include filing mechanics: how many copies, where to file, the filing fee, how to request a
     fee waiver in [STATE], and how to serve a copy on the plaintiff's attorney. Verify all of
     it with the [COUNTY] clerk.
   - GET A LAWYER — prominently, at the top and bottom of this track: legal aid for [COUNTY],
     the [STATE] bar's lawyer referral line, and any court self-help center, all verified by
     phone. Many jurisdictions have volunteer lawyer programs specifically for collection
     dockets. Find out whether [COUNTY] does.

3. VALIDATION TRACK — for Curtis.
   - Explain the validation right plainly: under federal law a collector must send certain
     information about the debt, and a written dispute sent within a defined window triggers
     obligations before collection continues. VERIFY the current requirements and timelines
     under the FDCPA and the CFPB's Regulation F, including what the validation notice must
     contain and what happens on a timely dispute, and quote them accurately with citations.
     The rules were substantially updated by Regulation F; do not describe pre-2021 practice
     as current.
   - Generate a validation and dispute letter: identify the account, dispute it, request
     verification, request the name of the original creditor, and — separately — a written
     instruction about how and whether the collector may contact them. Explain what each
     paragraph does.
   - Send it certified mail with return receipt, keep the receipt, and log it. Provide the
     tracking-number field and the reminder.
   - LOG EVERY CONTACT: date, time, number, who they said they were, what they said, whether
     they were told to stop. This log is what turns harassment into an FDCPA claim, and it is
     the same immutable, hash-chained pattern as project 03.

4. THE TWO TRAPS — a screen every user sees before generating any letter, because these are the
   mistakes that cost the most and are the easiest to make:
   - MAKING A PAYMENT OR ACKNOWLEDGING THE DEBT CAN RESTART THE LIMITATIONS CLOCK in many
     states. A $20 "good faith" payment on a debt that was almost time-barred can revive years
     of exposure. VERIFY exactly how [STATE] treats partial payment, written acknowledgment,
     and new promises to pay, cite the authority, and warn accordingly. If [STATE]'s rule is
     unsettled, say so and tell them to talk to a lawyer before paying anything.
   - NEVER GIVE A COLLECTOR BANK ACCOUNT OR DEBIT CARD NUMBERS OVER THE PHONE, and never agree
     to anything on a first call. If a payment is right, it can be made in writing, later,
     with terms confirmed in writing first.
   Also cover: time-barred debt is generally still collectable by asking, just not by suing —
   verify how [STATE] and federal rules treat suits and threats to sue on time-barred debt.

5. IS THIS EVEN MINE? — Short paths for the common misdirections:
   - Identity theft or mistaken identity: how to dispute, the FTC identity theft process, a
     police report, and the credit bureau dispute route.
   - Debt of a deceased relative: verify and state accurately that surviving family members are
     generally not personally responsible for a decedent's debts from their own funds, with the
     usual exceptions (joint accounts, co-signers, community property rules in some states,
     being the estate's representative). Cite the FTC's guidance and check [STATE]'s community
     property status. Cross-reference project 24.
   - Debt already paid or discharged in bankruptcy.

6. WHAT THEY CAN AND CAN'T TAKE — for the judgment track and for anyone frightened by threats.
   Research and verify for [STATE]: wage garnishment limits, which income sources are exempt,
   the federal rule protecting directly deposited federal benefits in bank accounts, homestead
   and personal property exemptions, and how to claim an exemption in [STATE] — including the
   form and the deadline, which is often short. Social Security, SSI, and VA benefits have
   specific protections; verify the current rules and state them precisely, because people
   living on exempt income are routinely frightened into paying from funds that could not have
   been taken.

7. COMPLAIN — the CFPB complaint process, the [STATE] attorney general's consumer division, and
   the [STATE] agency that licenses collection agencies, each with its current link and what it
   is good for. Generate a draft complaint from the contact log.

=== DATA MODEL (local only) ===

matters: id, kind enum(collection|lawsuit|judgment), creditor_original, collector_name,
  collector_address, collector_phone, amount_claimed_cents, account_last4, first_contact_on,
  last_activity_on, believed_last_payment_on, disputed_on, notes
lawsuits: id, matter_id, court_name, case_number, plaintiff, served_on, service_method,
  response_deadline, deadline_source, filed_answer_on, hearing_at
contacts: id, matter_id, occurred_at, direction, channel, party, summary, seq, content_hash,
  prev_hash
letters: id, matter_id, kind, body_md, generated_at, sent_on, method, tracking_number,
  green_card_returned_on
evidence: id, matter_id, kind, blob_ref, sha256, exif_datetime_original|null, note

Everything in IndexedDB. No server, no account. A record of someone's debts is a record of their
worst year.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB, offline, installable.
- Rules as dated, sourced JSON in /rules/[STATE_ABBR]/: limitations periods by debt type,
  response deadlines by court type, exemption amounts, restart-on-payment treatment, filing
  fees and waiver process. Zod-validated at build time; a rule without a source URL and
  retrieval date fails the build. Embedded test cases per rule.
- PDF via pdf-lib, client-side, formatted to look like a court filing where it is one.
- Web Crypto for the contact-log hash chain.
- No backend, no analytics, no third-party requests. Assert it.

=== HARD CONSTRAINTS ===

- The lawsuit deadline is the most prominent element on any screen where a lawsuit exists.
  Countdown in days, the date, and the rule citation.
- Never compute a deadline you cannot source. Fall back to the clerk's phone number.
- Every legal statement carries a citation and a verification date, displayed.
- Reading level 6th grade for app copy; generated letters and court filings are formal, and the
  app says why in one line.
- [LANGUAGES] from the first commit. Note prominently that court filings in [STATE] generally
  must be in English and explain how to request an interpreter for the hearing —
  cross-reference project 17.
- WCAG 2.2 AA; 18px minimum; works on an old phone.
- Zero network requests to third parties, ever.
- Nothing leaves the device. Say it on the first screen and make it architecturally true.

=== DO NOT BUILD ===

- No debt settlement, no negotiation service, no referral to debt relief companies, no
  affiliate links, no lead generation. That industry preys on exactly this user and a funnel
  into it would be the worst thing this app could do.
- No credit repair claims or credit score features.
- No payment processing of any kind.
- No LLM generating legal argument, defenses, or advice about a specific case. Templates,
  verified rules, and cited explanations only. The answer form is filled from the user's own
  admissions and denials — the app never decides for them what to deny.
- No prediction of case outcome, no "your defense is strong."
- No public database of collectors, no reviews, no complaint board.
- No account, no cloud sync, no sharing feature.
- No advice on bankruptcy beyond "this may be worth asking a bankruptcy attorney about, here is
  how to find a free consultation in [COUNTY]."

=== ACCEPTANCE TESTS ===

1. Selecting "I got court papers" surfaces the deadline calculator before any other content.
2. With an unverifiable deadline rule, the app renders the clerk fallback and never a computed
   date — test by removing the rule file.
3. Deadline computation is correct for each service method in the [STATE] rules, including
   weekend and holiday roll-forward if [STATE]'s rules require it. Test each boundary.
4. Every rule file has a source URL, retrieval date, and passing embedded tests; a missing
   source fails the build.
5. A rule past its effectiveTo renders the stale banner.
6. The two-traps screen appears before any letter is generated, and cannot be skipped by deep
   link.
7. The generated answer includes a numbered response to every numbered allegation the user
   entered.
8. Contact log entries are immutable; edits create corrections and the hash chain detects
   tampering.
9. Zero third-party network requests during a complete journey.
10. Every legal statement in the UI has a citation with a verification date.
11. All strings present in every language in [LANGUAGES].
12. The exempt-income section renders [STATE]'s verified exemptions, and shows "verify with
    legal aid" for any exemption whose rule you could not source.
13. axe-core clean; deadline countdown is announced by a screen reader.
14. The printed answer matches the [COUNTY] court's formatting requirements you verified.

=== MILESTONES ===

M0 — Triage + the lawsuit deadline calculator with verified [STATE] rules.
  EXIT: hand-verify the deadline for three court types and three service methods against the
  rules of civil procedure, and confirm one of them with a [COUNTY] clerk by phone.

M1 — The answer generator + filing mechanics.
  EXIT: a legal aid attorney or a court self-help center staffer reviews a generated answer and
  says it would be accepted. Do not skip this gate. Formatting requirements are local and a
  rejected filing on a deadline is a catastrophe.

M2 — Validation track, letters, contact log.
  EXIT: acceptance tests 6-8 pass and an attorney reviews the validation letter.

M3 — Exemptions, judgment track, complaints, second language.
  EXIT: every exemption figure traces to a verified source.

M4 — Five real users.
  EXIT: report how many filed an answer before their deadline. That is the only number that
  matters.

=== SAFETY + LEGAL ===

- Not legal advice, not a lawyer, stated on every screen and in every generated document, with
  legal aid for [COUNTY] and the [STATE] bar referral line named and verified.
- The deadline is a hard cliff and the app's most dangerous output. Never guess it. When
  uncertain, route to the clerk. Put a comment in the code at that branch explaining why the
  conservative path is mandatory.
- Never advise anyone to make a payment, offer a settlement, or acknowledge a debt without
  warning about the limitations-restart risk in [STATE] first.
- Never tell a user a debt is time-barred. Show them [STATE]'s limitations period, the debt
  type, and the date they said the last activity was, and tell them that whether it applies is
  a question for a lawyer — the accrual date is frequently disputed and getting it wrong in
  either direction is costly.
- Do not encourage ignoring a collector, and do not encourage confrontation. The app's position
  is: respond in writing, keep records, meet deadlines, get a lawyer.
- The contact log may contain harassment, threats, and abusive language. Store it locally,
  never transmit it, and offer a PIN lock — a household member may also be a creditor's contact
  point.
- Debts of the deceased: be precise and cautious. Collectors do contact grieving relatives who
  owe nothing. State the general rule, name the exceptions, and route to legal aid.
- Do not display any statistic you have not sourced with a year.

=== HOW TO REPORT BACK ===

Lead with the deadline rules: what you verified from [STATE]'s rules of civil procedure, which
court types, which service methods, and what the [COUNTY] clerk confirmed. Then: the limitations
periods by debt type with sources; how [STATE] treats partial payment; the exemption figures;
what the M1 reviewer said; and everything you could not verify.
```

---

## Why it's shaped this way

**The deadline is the product.** Most collection lawsuits are lost by default, which means the
decisive event happens before anyone argues about whether the debt is owed. A tool that helps
someone understand their rights but lets the answer deadline pass has failed completely. Hence
the countdown at the top of every screen and the rule that an unverifiable deadline routes to
the clerk rather than getting estimated.

**The limitations-restart warning appears before any letter is generated** because it's the trap
people walk into while trying to do the right thing. A small good-faith payment on an old debt
can revive years of exposure in many states, and the person making it thinks they're being
responsible.

**"Never tell a user their debt is time-barred."** The app shows the state's period, the debt
type, and the date the user gave — and stops. Accrual dates are contested constantly, and a
confident "this expired" that turns out wrong is worse than the uncertainty.

**No settlement, no negotiation, no referrals, stated flatly.** The debt relief industry targets
precisely this user at precisely this moment, and a funnel into it would monetize the worst week
of someone's year.

**Before you build:** call the [COUNTY] clerk and ask what a pro se answer has to look like to
be accepted, and ask whether the court has a self-help center or a volunteer lawyer program on
the collection docket. Many do, almost nobody knows, and it's a better outcome than anything
your software produces.
