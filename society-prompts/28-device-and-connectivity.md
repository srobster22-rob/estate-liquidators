# 28 — Device Lending + Connectivity Navigator

**What it is:** A library or community org lends laptops and hotspots. This is the lending
system, plus the part that matters more — a navigator that finds the household a permanent,
affordable connection instead of a device that goes home to no internet.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`, `[ORG]` (the library,
school district, or community organization running it).

---

```text
You are building a device lending and connectivity navigation tool for [ORG] in [CITY], [STATE].
Build it now; do not ask me clarifying questions. Where you need a decision I did not make,
choose the option that leaves the household connected after the loan ends, state your choice,
and keep going.

=== THE PEOPLE ===

Rosalie is 67 and needs to upload documents to a benefits portal, do a telehealth visit, and
video call a grandchild. She has a phone with a cracked screen and a data plan she runs out of
by the 20th of the month. She has never owned a computer.

Her problem is not one device for two weeks. It is that she has no home connection, does not
know that a low-cost internet offer exists for households on benefits she already receives, and
would not be able to complete a telehealth visit on a phone anyway.

The second person is Devon, 15, whose school issued a laptop and whose home has no broadband, so
he does his homework in a fast food parking lot. The device was never the constraint.

The third is Mia, who staffs the desk at [ORG], hands out six hotspots, and spends most of her
time on returns, chargers, and explaining the same three things to every borrower.

=== THE PROBLEM ===

A device without a connection is furniture, and a two-week hotspot loan does not fix a household
that cannot afford a monthly bill. Look up current household broadband adoption figures for
[COUNTY] — the FCC and the Census Bureau's American Community Survey both publish relevant data
— and cite them with a year. If you cannot verify a figure, display none.

The design consequence: this is a lending tool with a navigator bolted to the front, and the
navigator is the more valuable half.

=== WHAT SUCCESS LOOKS LIKE ===

Rosalie borrows a laptop, and before she leaves the desk Mia has checked her against every
low-cost internet program she might qualify for and signed her up for a digital skills session.
Ninety days later she has her own connection and the laptop is back in circulation.

=== BUILD THIS ===

Build part 1 first. It is the higher-value half and it works even if the lending system never
ships.

1. THE CONNECTIVITY NAVIGATOR — A short, non-invasive screener plus a verified directory.
   Ask at most six questions, none of them requiring documents: household size, roughly what
   comes in monthly, whether anyone receives specific benefit programs (list them as plain
   names), whether there are school-age children, whether anyone is a veteran or 65+, and the
   ZIP code.
   Then show every program the household might qualify for, each with what it provides, who
   qualifies, how to apply, what to bring, roughly how long it takes, and a verified_on date:
   - **Lifeline** — the federal telephone/broadband discount program. Verify the current benefit
     amount, eligibility rules, and application process from the administering authority, and
     note that eligibility often flows automatically from programs like SNAP and Medicaid.
   - **Carrier and ISP low-income offers** — most large providers run one, they are inconsistently
     advertised, and they generally require an application through the provider rather than
     through a government program. Research the ones actually available at [CITY] addresses.
   - **[STATE] programs**, if any — several states run their own broadband affordability or
     device programs. Research and verify.
   - **School district hotspot or connectivity programs** for households with students.
   - **Municipal or community wireless**, where it exists.
   - **Free public access**: [ORG]'s own wifi and computer hours, other library branches, and
     anywhere with hours that extend past 5pm — which is the constraint for anyone who works.
   IMPORTANT: federal broadband subsidy programs have changed substantially in recent years and
   at least one major one ended. **Verify the current status of every program before listing it**,
   and never list a program you could not confirm is currently accepting applications. A
   directory entry for a dead program sends someone through an application that goes nowhere and
   costs them their trust in the whole list.

2. WHAT DO YOU ACTUALLY NEED — A two-minute plain-language guide that prevents the most common
   mismatch: a phone is fine for messaging and most benefit portals; a tablet or laptop is
   effectively required for a video appointment where you must also read a document, for job
   applications with attachments, and for schoolwork; a hotspot serves one or two devices lightly
   and will not carry a household's streaming. Say what each option cannot do. Managing
   expectations at the desk is most of Mia's job.

3. INVENTORY + LENDING — The system for [ORG]:
   - Items: laptops, tablets, hotspots, chargers, cases, adapters, cameras, and the accessories
     that go missing. Each with an asset tag, condition, and what is in the kit — an itemized kit
     list is what makes returns checkable.
   - Loans: borrower, out date, due date, condition out and in, kit completeness.
   - Hotspots additionally track: carrier, line identifier, data plan, and the current billing
     cycle's usage if [ORG] can get it. A hotspot that has hit its cap is a brick, and a borrower
     who does not know that thinks the device is broken.
   - Reservations and a waitlist, notified when an item comes back and checked in.
   - Renewals: allow at least one self-service extension by text if nobody is waiting. Same
     reasoning as project 09 — most lateness is "I still need it," and making the honest path one
     word long converts overdue loans into sanctioned ones.

4. THE REMINDER LADDER — Warm, automatic, never accusatory. Due minus 3 days, due date, plus 3
   days, then staff notification at plus 10. "MORE" extends if no one is waiting. Every message
   names the item, because "your loan is due" means nothing out of context.
   For hotspots, add a message when the data cycle resets, and one when usage crosses a threshold
   if that data is available — the most common support call is a hotspot that stopped working at
   the end of the month.

5. SETUP HELP — What goes in the box and what happens after:
   - A printed one-page start card in [LANGUAGES]: how to turn it on, how to connect, how to get
     help, and when it is due. Large type.
   - Basic-safety content, plainly written and cited: how to spot a phishing message, why
     software updates matter, what a public network can and cannot see. Cross-reference project
     22 rather than duplicating it.
   - Digital skills sessions at [ORG], if they exist, with times — and if they do not, say so,
     because that absence is a finding worth [ORG] knowing.

6. STAFF VIEW — Mia's screen. Out, overdue, due today, reserved, needs repair, and the return
   checklist with the kit contents. Works on a phone at a desk. Printable daily list, because the
   desk sometimes has no computer free.

7. WIPE + REISSUE — A documented, enforced process: every returned device is reset before it
   goes out again, and the system records who did it and when. A borrower's benefits portal
   session or saved passwords reaching the next borrower is the worst thing this project can do,
   and it happens through ordinary busyness rather than malice.

=== DATA MODEL ===

items: id, asset_tag, kind enum(laptop|tablet|hotspot|accessory), model, kit_contents text[],
  condition, status, acquired_on, retired_on, notes
hotspots: item_id, carrier, line_ref, plan_gb, cycle_start_day, last_known_usage_gb,
  usage_checked_on
borrowers: id, name, phone, email, language, household_notes, agreement_signed_on, active
loans: id, item_id, borrower_id, out_at, due_at, returned_at, extended_count, condition_out,
  condition_in, kit_complete bool, staff_out, staff_in
wipes: id, item_id, loan_id, wiped_at, wiped_by, method
reservations: id, item_id_or_kind, borrower_id, created_at, notified_at, expires_at
programs: id, name, provider, kind, covers, eligibility, how_to_apply, documents_needed,
  typical_days, url, phone, currently_accepting bool, verified_on, verified_by
sessions: id, title, starts_at, location, language, capacity

Borrower records live behind staff authentication. Library borrowing records are sensitive and in
many states specifically protected — see SAFETY.

=== STACK ===

- Next.js + TypeScript + PostgreSQL (or SQLite; this is a small dataset — pick one and say why).
- SMS via Twilio behind an `SmsProvider` interface with a console implementation, so the whole
  system demos with no credentials.
- Durable job queue for the reminder ladder: persisted, idempotent, surviving restarts.
- The navigator is a static, client-side screener over dated JSON program data — no answers leave
  the device, same reasoning as project 02.
- Staff auth by email magic link. Borrowers never log in; everything they do is a signed link
  from a text.
- [LANGUAGES] from the first commit.

=== HARD CONSTRAINTS ===

- The navigator works with no account and sends no answer to a server. Assert it.
- Every program entry carries currently_accepting and verified_on; entries older than 120 days
  render "call to confirm." Broadband program status changes fast.
- Every borrower action completable by replying to a text with one word.
- Wipes are enforced: an item cannot be checked out again until a wipe record exists for the
  previous loan. Enforce in the database, not the UI, and test it.
- WCAG 2.2 AA, 18px minimum. This user base includes people using a computer for the first time,
  so the staff-facing print card matters as much as the screen.
- Reading level 6th grade. [LANGUAGES] on every borrower-facing message and printable.
- No analytics, no third-party fonts, no CDN scripts.

=== DO NOT BUILD ===

- No device management agents, remote monitoring, keyloggers, location tracking, or remote
  screenshot capability on lent devices. Ever. Surveillance of a borrower is worse than the loss
  of a laptop, and a library that does it deserves to lose its patrons' trust.
- No remote-lock or kill switch in v1. It sounds prudent, it changes the relationship, and it
  fails in the direction of bricking a device someone needs.
- No content filtering beyond whatever the network already does.
- No credit checks, deposits, or fees.
- No public list of borrowers, overdue items, or usage.
- No ISP affiliate links, referral fees, or sales partnerships.
- No LLM in the eligibility path of the navigator. Rules as data, results traceable.
- No collection of browsing history, installed apps, or anything about how the device was used.

=== ACCEPTANCE TESTS ===

1. The navigator sends no network request containing any answer.
2. Every program entry has verified_on, a phone number, and currently_accepting; one missing any
   fails the build.
3. A program with currently_accepting false renders as closed rather than being silently hidden.
4. An item without a wipe record for its previous loan cannot be checked out — verified by
   attempting a direct database insert.
5. The reminder ladder fires at -3d, due, +3d and notifies staff at +10d, exactly once each, and
   survives a process restart mid-ladder.
6. "MORE" extends when no reservation exists and declines with an explanation when one does.
7. Returning an item notifies the first person on the waitlist, with a claim window.
8. Kit completeness is recorded on return and a missing accessory creates a follow-up, not an
   accusation.
9. Borrower records are unreachable without staff authentication — asserted against the API.
10. All borrower-facing messages and printables render in every language in [LANGUAGES].
11. With TWILIO_* unset the full loan lifecycle completes against the console provider.
12. Due dates do not shift across a DST transition.
13. axe-core clean on navigator, staff view, and printables.
14. No code path collects location, browsing, or usage data from a lent device — grep and
    dependency review.

=== MILESTONES ===

M0 — The connectivity navigator, programs phone-verified.
  EXIT: you have called every program and confirmed it exists, is accepting applications, and
  has the stated eligibility. Delete any you cannot confirm. This ships alone and is worth more
  than the lending system.

M1 — Inventory, loans, staff view, printable start card.
  EXIT: Mia runs one real week off it instead of the spreadsheet.

M2 — Reminder ladder and reservations, console SMS.
  EXIT: tests 4-8 pass including the restart test.

M3 — Real SMS, hotspot usage, second language.
  EXIT: a borrower receives a data-cycle message in their language.

M4 — Thirty loans.
  EXIT: report return rate, kit-completeness rate, and — the number that matters — how many
  households ended up with their own connection.

=== SAFETY + LEGAL ===

- Library borrowing records are confidential under many state statutes and under library
  professional ethics. Find [STATE]'s provision, cite it in the README, and design to it:
  minimum retention, no public exposure, access limited and logged, and purge borrower history
  after a defined period rather than keeping it forever.
- The wipe process is a privacy control for the *previous* borrower. Someone logged into a
  benefits portal, a bank, or a health record on a lent laptop. Enforce it in the database and
  audit it.
- No surveillance of lent devices, stated plainly to borrowers in the loan agreement: "We cannot
  see what you do on this device." Make that true, then say it.
- Never require a Social Security number, immigration status, or proof of income to borrow.
  Whatever [ORG] requires as identification should be the minimum that works, and the app should
  not add fields beyond it.
- Program status is volatile. A federal broadband subsidy program ended recently and directories
  across the country still list it. Verify currently_accepting on every entry, re-verify
  quarterly, and put that in MAINTENANCE.md.
- Do not display any adoption or affordability statistic you have not sourced with a year.

=== HOW TO REPORT BACK ===

Tell me: which programs you confirmed by phone and which are currently accepting; what [STATE]'s
library-records confidentiality statute says; the wipe-enforcement test result; the restart test;
and everything you could not verify. If a widely-listed program turned out to be dead, lead with
that.
```

---

## Why it's shaped this way

**The navigator ships before the lending system and is worth more.** A two-week hotspot loan
does not fix a household that cannot afford a monthly bill, and the single highest-value moment
is the one where Mia checks Rosalie against Lifeline and the ISP low-income offers while she is
standing at the desk. Devices circulate; a connection persists.

**"Verify currently_accepting" is not boilerplate.** Federal broadband subsidy programs have
changed materially in recent years and at least one large one ended, yet directories all over
the country still list it. Sending someone through a dead application costs them a morning and
costs the list its credibility.

**No device surveillance, stated flatly.** Remote monitoring is the first "responsible" feature
anyone proposes for lent hardware. For a library it is a betrayal of the institution's central
promise, and the thing it protects — a laptop — is worth less than the trust it spends.

**Wipes enforced at the database layer** because the failure is ordinary busyness, not malice,
and the consequence is one borrower's benefits-portal session reaching the next.

**Telling people what each device cannot do** prevents the most common bad outcome: someone
borrows a hotspot expecting it to carry a household, or tries a telehealth visit on a phone
while also needing to read a document.

**Before you build:** ask [ORG] what the desk spends its time on. It will be chargers, hotspot
data caps, and the same three questions — and those are your first three features.
