# 20 — Utility Shutoff Prevention + Bill Help

**What it is:** A shutoff notice arrived. This finds out whether [STATE] protections apply today,
what a medical certificate does and how to get one this week, what assistance exists, and what
sentence to say when you call the utility — which is not the sentence most people say.

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[COUNTY]`, `[CITY]`, `[LANGUAGES]`,
`[UTILITIES]` (the electric, gas, and water providers serving [CITY] — name them before pasting).

---

```text
You are building a utility shutoff prevention tool for households in [CITY], [STATE]. Build it
now; do not ask me clarifying questions. Where you need a decision I did not make, choose the
option that keeps the power on today, state your choice, and keep going.

Read SAFETY + LEGAL first. This is a life-safety issue for some users and the design has to
reflect that.

=== THE PEOPLE ===

Yolanda, [CITY]. Shutoff notice for the electric bill: $842 past due, disconnection in ten days.
Her son uses a nebulizer. She has $180. She has not called the utility because she does not have
$842 and assumes the call ends with them asking for $842.

That assumption is the problem. What she does not know: [STATE] may restrict disconnection right
now depending on the season and the temperature; a doctor's certificate about her son can delay
it; there is almost certainly a payment agreement that does not require the full balance; and
there is likely an assistance program with money in it that she has never heard of.

The second person is Ray, a renter whose landlord pays the utilities and has stopped, which is a
different problem with a different answer.

The third is a caseworker at a community action agency who does this eleven times a day and
knows every program, and whose knowledge exists in her head and nowhere written down for [CITY].

=== THE PROBLEM, WITH A NUMBER ===

Energy burden — the share of household income spent on energy — runs several times higher for
low-income households than for others; the Department of Energy publishes a Low-Income Energy
Affordability Data tool with figures by geography. Look up the number for [COUNTY] and cite it.

The operational gap: protections and assistance exist and are unevenly known. Utilities are
generally required to offer payment arrangements. Many states restrict disconnection during
defined cold or hot periods. Medical certification provisions exist in most states. LIHEAP
exists everywhere. Each has rules, deadlines, and paperwork, and none of it is written down in
one place for a person holding a notice.

=== WHAT SUCCESS LOOKS LIKE ===

Yolanda calls the utility and asks for a deferred payment agreement and a medical certificate
hold, faxes her son's doctor a one-page form the same day, applies for LIHEAP with the documents
already gathered, and the power stays on.

=== BUILD THIS ===

1. TRIAGE (/) — Three questions, one screen:
   - Which utility, and is this electric, gas, water, or a landlord-paid situation?
   - Do you have a shutoff notice? If yes, the disconnection date from the notice.
   - Is anyone in the home dependent on electricity for medical equipment, seriously ill,
     elderly, a young child, or disabled?
   That third question routes to the fastest protection available and it must come early.
   Then produce the ACTION PLAN: an ordered list of things to do, each with today's date
   context, a phone number, and an estimated time. Ordered by what stops the disconnection
   soonest, not by what solves the balance.

2. AM I PROTECTED RIGHT NOW? — Research and encode [STATE]'s disconnection rules as dated,
   sourced JSON. What to verify from the [STATE] public utilities commission's rules and the
   utility's own tariff:
   - Seasonal moratoria: dates, and whether they are calendar-based or temperature-triggered.
     Some states forbid disconnection when the forecast is below or above a threshold — if so,
     wire in the NWS forecast (see project 06) and tell the user whether today qualifies.
   - Medical certification: who can certify, what form, how long it holds, how many times it
     can be renewed, and what it does and does not excuse. This is frequently the fastest
     protection available and it is chronically underused.
   - Protections for households with infants, elderly, or disabled members.
   - Notice requirements: how much notice the utility must give, in what form, and what must be
     on it. If the notice the user received does not meet the requirements, that is worth
     knowing.
   - Whether a pending assistance application or a filed complaint stays disconnection.
   - Reconnection: the fee, the timeline, and whether the utility must reconnect within a set
     time after payment or certification.
   Every rule cited to the PUC rule number or the tariff section, with a retrieval date. Where
   the utility's own tariff is stricter or looser than the state minimum, use the tariff and say
   so. If you cannot verify a rule, say "call the utility and the PUC consumer line" and give
   both numbers rather than guessing.

3. THE CALL SCRIPT — Printable, and the single highest-value screen. What to ask for, in order,
   in the words that work:
   - "I want to set up a deferred payment agreement." (Not "I can't pay." The first is a
     request for a thing that exists; the second invites a no.)
   - "What is the smallest down payment that will stop the disconnection?"
   - "I want to apply for a medical certificate. What do you need from the doctor and where do
     I send it?"
   - "Please note on the account that I have applied for LIHEAP."
   - "Can you put me on budget billing?" and "Do you have an arrearage forgiveness or
     percentage-of-income plan?"
   - Write down: date, time, the representative's name and ID, the confirmation number, and
     exactly what they agreed to. Then send an email or letter confirming it in writing the
     same day — the app generates that letter.
   Include what to do if the answer is no: ask for a supervisor, then file with the [STATE] PUC
   consumer division, which in many states stays disconnection while a complaint is pending —
   verify this for [STATE], because if true it is the most powerful item in the whole app.

4. MEDICAL CERTIFICATE — Generate [STATE]'s form or, if the utility has its own, link and
   pre-fill what you can: patient, address, account number, condition category, equipment, and
   the fields the prescriber completes. Add a cover note the user can hand or fax to the
   clinic, explaining what is needed and by when. Include: what to say when calling the doctor's
   office, which is usually a nurse line and not the doctor, and that this is a routine request
   they handle regularly.

5. MONEY — A verified [CITY]/[COUNTY] assistance directory, each entry with what it covers, who
   qualifies, what to bring, how long it takes, whether funds are currently available, and a
   verified_on date. Research and include:
   - LIHEAP for [STATE]: the administering agency, application method, income limits for the
     current program year, crisis or emergency component and its faster timeline, and the
     application window. Verify the current year's figures; they change annually.
   - The Weatherization Assistance Program and any state-level equivalent.
   - Utility hardship funds — most utilities have one, often administered by a nonprofit,
     usually underspent, and frequently unmentioned by the call center.
   - [STATE] percentage-of-income payment plans or arrearage forgiveness, if they exist.
   - Water bill assistance, which is patchier than energy assistance; verify what exists in
     [CITY] and say plainly if the answer is little.
   - Local community action agency, faith-based emergency funds, and 211.
   Ranked by how fast money actually arrives, with an honest estimate, because Yolanda has ten
   days.

6. RENTERS — A separate track for Ray. Verify [STATE]'s rules on landlord-paid utilities: what
   happens when a landlord fails to pay, whether tenants may pay directly and deduct, whether
   the utility must give tenants notice before disconnecting a landlord-billed account, and what
   remedies exist. This is a real and frequently mishandled situation. Cross-reference project
   03 for documenting it.

7. NEXT WINTER — Once the emergency passes, the boring things that prevent the next one: budget
   billing, weatherization, appliance replacement programs, LIHEAP application timing for next
   season with a reminder, and a link to the utility's usage data so they can see what's driving
   the bill.

=== DATA MODEL (local only) ===

households: id, utility_ids[], account_numbers, service_address, household_size, income_band,
  medical_needs jsonb, has_notice bool, disconnect_date, balance_cents
rules: jurisdiction, utility_id|null, kind enum(moratorium|medical_cert|notice|payment_plan|
  reconnect|complaint_stay), body, params jsonb, source_url, source_citation, retrieved_on,
  effective_from, effective_to
programs: id, name, administrator, covers, eligibility, income_limit_note, documents_needed,
  typical_days_to_funds, apply_url, phone, funds_status, verified_on, verified_by
calls: id, household_id, occurred_at, utility, rep_name, rep_id, confirmation_number,
  what_was_agreed, follow_up_sent_on
applications: id, household_id, program_id, submitted_on, status, decision_on, amount_cents

Local storage only. This record says a household is behind on utilities and who in it is sick.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB, offline, printable.
- Rules and programs as versioned JSON with Zod validation at build time; no source URL and
  retrieval date, no build.
- Optional NWS forecast fetch for temperature-triggered moratoria — same api.weather.gov
  approach as project 06, with a cached fallback and never a blank value.
- PDF via pdf-lib for the call script, confirmation letter, and medical certificate cover note.
- No account, no backend for household data. A tiny static host.
- Under 150KB JS.

=== HARD CONSTRAINTS ===

- The action plan is ordered by what stops the disconnection soonest. Test that the medical
  certificate path outranks the assistance application path when a medical need is present.
- Days remaining until the disconnection date shown prominently on every screen once a notice
  date is entered.
- Every rule and every program figure carries a citation and a retrieval date, displayed.
- LIHEAP income limits and program windows change annually — the stale banner is mandatory and
  MAINTENANCE.md names the month.
- Reading level 6th grade. [LANGUAGES] from the first commit, including the call script and the
  medical certificate cover note.
- WCAG 2.2 AA; 18px minimum; printable everything.
- Works offline. The power may already be off and the phone may be the only device.
- No third-party requests except NWS.

=== DO NOT BUILD ===

- No account, no cloud, no sharing.
- No payment processing, no donation collection, no "we'll pay your bill" fund.
- No utility account integration, no screen-scraping of utility portals, no storing of utility
  login credentials. Ever.
- No referrals to solar sales, energy brokers, third-party retail energy suppliers, or bill
  negotiation services. In deregulated states, third-party supplier pitches target exactly this
  household and frequently make bills worse. If [STATE] is deregulated, add a warning page
  about supplier switching instead — verify [STATE]'s status and what the PUC says about it.
- No LLM interpreting a user's bill or advising on their eligibility. Rules as data.
- No energy usage analytics, no smart home, no thermostat integration.
- No credit or lending features of any kind, and no referral to payday or utility-bill loan
  products.

=== ACCEPTANCE TESTS ===

1. Entering a disconnection date renders a days-remaining countdown on every subsequent screen.
2. A household with a medical need gets the medical certificate step ranked above assistance
   applications in the action plan.
3. A temperature-triggered moratorium correctly reflects today's NWS forecast, and renders
   "could not check today's forecast — call the utility" when the fetch fails, never a default.
4. Every rule has a source citation and retrieval date; one missing either fails the build.
5. A rule or program past its effective window renders the stale banner.
6. The call script prints on one page and includes the fields for rep name, ID, and confirmation
   number.
7. The confirmation letter generator produces a letter naming the agreed terms the user entered.
8. Programs are ordered by typical_days_to_funds, and one with funds_status = exhausted renders
   as such rather than being silently hidden.
9. The renter track appears when the user indicates landlord-paid utilities and does not appear
   otherwise.
10. All strings, the call script, and the medical cover note render in every language in
    [LANGUAGES].
11. The app functions fully offline including PDF generation.
12. No third-party network requests other than NWS.
13. axe-core clean; countdown announced by a screen reader.
14. No utility credential field exists anywhere in the codebase — grep test.

=== MILESTONES ===

M0 — [STATE] rules research, written up before any code.
  EXIT: a document listing every disconnection protection in [STATE] with its PUC rule citation
  and retrieval date, plus the differences in each of [UTILITIES]' own tariffs. Confirm at least
  two of them by calling the PUC consumer line.

M1 — Triage + action plan + the call script.
  EXIT: a community action agency caseworker reads the call script and the action plan and
  tells you what's wrong with them. They do this eleven times a day; their edits are the
  product.

M2 — Assistance directory, phone-verified.
  EXIT: you have called every program and confirmed eligibility, documents, timeline, and
  whether funds are currently available.

M3 — Medical certificate flow, renter track, second language.
  EXIT: one real medical certificate is submitted successfully by a real household.

M4 — Ten real households.
  EXIT: report how many avoided disconnection and which step did it. If the medical certificate
  or the payment agreement did most of the work, move them further up.

=== SAFETY + LEGAL ===

- This can be a life-safety situation. Loss of electricity to medical equipment, or of heat in
  winter, kills people. If the user indicates powered medical equipment and imminent
  disconnection, show — above everything — the utility's medical emergency line, the [STATE] PUC
  emergency consumer line, and 911 if someone is in immediate danger. Verify those numbers by
  calling them.
- Never advise anyone to use an unsafe heating or cooling substitute. Do not mention generators,
  ovens, charcoal, or unvented heaters except in a clearly-labeled warning that quotes CDC or
  fire service guidance on carbon monoxide, with citation. This warning belongs in the app
  because people in this situation do these things and die of it.
- Not legal advice. If a disconnection appears to violate [STATE] rules, the app says "this may
  not be allowed — call the PUC consumer line at <number> today" and names legal aid for
  [COUNTY]. It does not conclude that a violation occurred.
- Every income limit, program window, and rule is dated. LIHEAP figures change every program
  year and a stale limit can cause someone to not apply when they qualify. Bias the copy toward
  "apply anyway, they decide."
- Never store or request utility account credentials, Social Security numbers, or full birth
  dates. Account numbers only, locally.
- If [STATE] has retail energy choice, warn about supplier switching offers made to households
  in arrears, and cite the PUC's own consumer guidance.
- Coordinate with the community action agency that administers LIHEAP for [COUNTY] before
  launch. They know which programs currently have money, which is the most volatile and most
  important field in your entire directory.

=== HOW TO REPORT BACK ===

Lead with the M0 rules document: every protection, its citation, its retrieval date, and where
[UTILITIES]' tariffs differ from the state minimum. Then: which programs you confirmed by phone
and their current funds status; what the caseworker changed in the call script; whether a
pending PUC complaint stays disconnection in [STATE]; and everything you could not verify.
```

---

## Why it's shaped this way

**The call script is the product.** Yolanda's actual barrier is a belief that the call ends with
"we need $842." It doesn't — utilities generally must offer payment arrangements, and the
difference between "I can't pay" and "I want to set up a deferred payment agreement" is the
difference between a no and a process. That's a printed page, not software, and it's the highest
leverage thing here.

**Medical certification is ranked above everything else** when it applies, because it is usually
the fastest available protection, it works in days rather than weeks, and it is chronically
underused — most people have never heard of it and many call center reps don't volunteer it.

**Programs are ranked by how fast money arrives, and "funds exhausted" is displayed rather than
hidden.** Assistance directories that list a program with no money left send someone on a
week-long detour they don't have. That field is also the most volatile thing in the directory,
which is why project 18 exists.

**The carbon monoxide warning is in the app on purpose.** People facing disconnection use ovens
and unvented heaters and generators indoors, and they die of it every winter. Quoting fire
service guidance is not scope creep; it's the predictable consequence of the situation the app
is already in.

**No third-party supplier referrals, no bill loans.** In deregulated states, households in
arrears are a marketing target and the pitches usually make the bill worse.

**Before you build:** spend an hour with a LIHEAP intake worker at the community action agency.
They will hand you the entire program directory, tell you which funds are actually available
this month, and correct your call script.
