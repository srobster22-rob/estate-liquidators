# 30 — Small Claims + Consumer Complaint Helper

**What it is:** The contractor took $4,000 and left. This writes the demand letter that resolves
most of these without a filing, and if that fails, walks the small claims process — including the
part nobody mentions, which is that winning and collecting are different problems.

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[COUNTY]`, `[CITY]`, `[LANGUAGES]`.

---

```text
You are building a small claims and consumer complaint tool for [COUNTY], [STATE]. Build it now;
do not ask me clarifying questions. Where you need a decision I did not make, choose the option
that resolves the dispute without a court filing, state your choice, and keep going.

Read SAFETY + LEGAL before writing code. It contains the honesty requirement that shapes the
whole product.

=== THE PEOPLE ===

Gloria paid a contractor $4,200 up front to replace a roof. He tore off half of it, did not come
back, and stopped answering. That was five weeks ago and there is a tarp up there.

Bram bought a used transmission install for $1,900. It failed in three weeks. The shop says the
warranty does not cover labor, which is not what he was told and not what the invoice says.

Neither of them has a lawyer, and a lawyer would cost more than the claim. Both assume the choice
is "sue" or "eat it," and both are wrong: a specific written demand with a deadline resolves a
large share of disputes like these before anyone files anything, and neither of them knows how to
write one.

=== THE PROBLEM ===

Three things people do not know, and each one changes the outcome:

1. **A written demand letter works surprisingly often**, and in some states it is a prerequisite
   before filing. It converts a vague dispute into a documented one with a deadline, and it
   creates the record a court will want later. Verify whether [STATE] requires one.
2. **Small claims is designed for people without lawyers.** Filing fees are modest, the limits
   are meaningful — research and verify [STATE]'s current limit, which changes — and in many
   states lawyers are restricted or barred in small claims court entirely.
3. **A judgment is not money.** This is the fact that nobody says out loud. Winning gets you a
   piece of paper; collecting it is a separate process with its own steps, and against a
   defendant with no reachable assets it may not happen at all. Any tool that walks someone to a
   filing without telling them this is setting them up.

Verify [STATE]'s current small claims limit, filing fee, service rules, deadlines, and collection
procedures from the [STATE] courts' own self-help materials and the [COUNTY] clerk. Not from a
legal-marketing site.

=== WHAT SUCCESS LOOKS LIKE ===

Gloria sends a demand letter by certified mail with a 14-day deadline and a specific number, and
the contractor's insurer calls her. That is the most common good ending and it never involves a
courthouse.

=== BUILD THIS ===

1. WHAT HAPPENED (/) — Structured intake, because the facts are the case:
   - Who (business or individual, and their legal name and address — see part 3, this is where
     claims fail)
   - What was agreed, how, and when: verbal, written, text messages, an estimate, an invoice
   - What was paid, when, how
   - What went wrong and when
   - What you want: money back, the work finished, a repair, a replacement
   - What you have already done to resolve it
   The amount claimed and a timeline are assembled from this. Keep it to one screen per topic and
   let people come back — this takes people days, not minutes.

2. EVIDENCE — Same discipline as project 03, and for the same reason: this ends up in front of a
   judge. Photos with EXIF capture time preserved and displayed distinctly from import time,
   originals stored byte-identical with a SHA-256, and an honest "no camera timestamp" when the
   metadata is absent. Contracts, estimates, invoices, receipts, texts, emails. A contact log:
   date, time, who, what was said, what was promised.
   Everything local. Export as a PDF exhibit packet with a numbered index, plus a ZIP of
   unmodified originals with a manifest — a judge will want it organized and a lawyer will want
   the originals.

3. THE DEMAND LETTER — The highest-value output in the app. Generated, editable, printable:
   - Your name and address, theirs, the date
   - What was agreed, in dates and dollars, from the intake
   - What went wrong, factually, without adjectives
   - Exactly what you want and by when — a specific amount and a specific deadline, usually 10 to
     14 days
   - A plain statement that you will pursue available remedies if you do not hear back, without
     threats and without legal conclusions you are not entitled to draw
   - Where to send payment or a response
   Delivery: certified mail with return receipt, and keep the receipt. The tracking number goes
   in the record and the deadline creates a reminder.
   Include the two sentences that cause the most damage and should not appear: do not admit
   fault, and do not threaten anything you are not going to do — including criminal charges,
   which in some states is itself a problem. Say so.

4. BEFORE YOU SUE — A decision screen, and the honest one:
   - Is the amount within [STATE]'s small claims limit? If it is over, what the options are
     (waive the excess, or a different court).
   - Are you inside the statute of limitations? Verify [STATE]'s periods by claim type (contract,
     written vs oral, property damage, consumer statutes) and cite them. Show a computed deadline
     with the rule, and where uncertain, route to the clerk.
   - **Can you actually collect?** Walk this honestly: does the defendant have a job, a bank
     account, a business, property? Are they insured or bonded — contractors in many states must
     be, and a claim against a contractor's bond or license is often faster and more collectable
     than a judgment. Verify [STATE]'s contractor licensing and bond claim process. Is the
     business still operating, or dissolved?
   - Alternatives that may be faster: a credit card chargeback if it was paid by card and is
     within the window, a licensing board complaint, the [STATE] attorney general, the CFPB for
     financial products, or a manufacturer warranty claim.
   The app should be willing to say: based on what you have told us, filing may not get you paid,
   and here is what might.

5. FILING — [COUNTY]-specific and verified with the clerk:
   - Which court and where, with address and hours
   - The correct form, its current version, and where to get it
   - The filing fee and how to request a waiver
   - **Naming the defendant correctly.** This is the most common fatal error: suing a trade name
     instead of the legal entity, or an employee instead of the business. Explain how to find the
     registered legal name and agent for service through [STATE]'s business entity search, and
     how to name an individual, a sole proprietor, and an LLC differently.
   - **Service of process** — the second most common fatal error. What [STATE] allows, what it
     costs, who may serve, and the deadline. Getting this wrong loses the case before it starts.
   - What happens at the hearing, how long it takes, what to bring, how to present in order
   - What if they do not show, and what if you do not

6. COLLECTING — Its own section, given the weight it deserves. Verify for [STATE]: how to record
   or abstract a judgment, wage garnishment and its limits, bank levy, property liens, the
   debtor's examination, what income and property are exempt from collection, and how long a
   judgment lasts and whether it can be renewed. Also state plainly that some judgments are never
   collected, and that this is not a failure of the person who filed.

7. COMPLAIN INSTEAD, OR AS WELL — Verified paths that cost nothing: [STATE] attorney general
   consumer protection, [STATE]'s contractor licensing board, the CFPB for financial products,
   the FTC, and the [STATE] insurance department where relevant. What each can and cannot do —
   most cannot get your money back, and saying so prevents a wasted month of waiting.

=== DATA MODEL (local only) ===

matters: id, kind, other_party_name, other_party_legal_name, other_party_address,
  agreed_on, agreement_form, amount_paid_cents, amount_claimed_cents, what_happened,
  desired_outcome, created_at
timeline: id, matter_id, occurred_on, description, seq, content_hash, prev_hash
evidence: id, matter_id, kind, blob_ref, sha256, exif_datetime_original|null, exif_present bool,
  import_time, label, exhibit_number
contacts: id, matter_id, occurred_at, party, person, channel, summary, promised
letters: id, matter_id, kind, body_md, generated_at, sent_on, method, tracking_number,
  response_by, response_received_on
deadlines: id, matter_id, kind, due_on, rule_cite, source_url, satisfied_on
filings: id, matter_id, court, case_number, filed_on, fee_cents, served_on, service_method,
  hearing_at, outcome, judgment_amount_cents, collected_cents

Local-first, no server, no account. A record of someone's dispute, their finances, and their
evidence is theirs.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB, offline, installable.
- Rules as dated, sourced JSON in /rules/[STATE_ABBR]/: small claims limit, filing fee, statutes
  of limitations by claim type, service methods, collection procedures, exemptions. Zod-validated
  at build time; no source URL and retrieval date, no build. Embedded test cases per rule.
- Money in integer cents. Never floating point.
- Web Crypto for the evidence hash chain; pdf-lib for the demand letter and exhibit packet.
- No backend, no analytics, no third-party requests. Under 200KB JS.
- [LANGUAGES] from the first commit, with a note that court filings in [STATE] generally must be
  in English and how to request an interpreter — cross-reference project 17.

=== HARD CONSTRAINTS ===

- Every legal rule cites a primary source with a retrieval date, displayed.
- Statute of limitations renders as a computed date with its rule, or as "confirm with the clerk"
  when unverifiable. Never a guess.
- The collection reality check appears before the filing section can be reached, not after.
- Evidence entries immutable; corrections visible; hash chain verifiable.
- Reading level 6th grade for app copy; the letter and filings are formal and the app says why.
- WCAG 2.2 AA; 18px minimum; everything printable; works offline.
- Zero third-party network requests. Assert it.

=== DO NOT BUILD ===

- No legal advice about the merits: never "you have a strong case," never "you will probably
  win," never an assessment of liability.
- No filing on anyone's behalf, no e-filing integration, no service of process arrangement.
- No LLM generating legal argument or evaluating a dispute. The letter is a template filled from
  the user's own structured facts.
- No attorney marketplace, no referral fees, no litigation funding, no debt-buying, no
  partnerships with collection agencies.
- No public database of businesses, contractors, or defendants. No reviews. This is where a
  dispute tool becomes a defamation problem.
- No credit reporting of any judgment.
- No settlement negotiation on the user's behalf, and no automated follow-up messages to the
  other party. The user sends; the app prepares.
- No advice on recording phone calls — consent law varies by state and getting it wrong is a
  crime in some of them. If you mention it at all, say only "recording laws vary; check [STATE]'s
  before you record anyone."

=== ACCEPTANCE TESTS ===

1. Every rule file has a primary source URL and retrieval date; one missing either fails the
   build, and every rule's embedded tests pass.
2. A rule past its effective window renders the stale banner.
3. Statute of limitations computes correctly for each claim type, verified by hand against
   [STATE]'s statutes, including a case that spans a leap day.
4. With a limitations rule absent, the app renders the clerk fallback and never a computed date.
5. All monetary math is integer cents; a property test over random amounts shows no drift.
6. A claim above [STATE]'s small claims limit surfaces the over-limit guidance rather than the
   filing flow.
7. The collection reality check is reachable before filing and cannot be bypassed by deep link.
8. The demand letter contains the amount, the deadline, and no threat language — grep test
   against a blocklist including "criminal charges", "prosecute", "fraud".
9. No output contains a merits assessment — grep for "strong case", "you will win", "they are
   liable".
10. Evidence entries are immutable; tampering is detected by the hash chain; exported ZIP
    originals re-hash to the manifest.
11. Photos show EXIF capture time distinctly from import time, and "no camera timestamp" when
    absent.
12. The exhibit packet numbers exhibits consecutively and includes an index.
13. Zero third-party network requests during a full journey.
14. All strings render in every language in [LANGUAGES]; axe-core clean; works offline.

=== MILESTONES ===

M0 — [STATE] and [COUNTY] rules research, before any code.
  EXIT: a document with the small claims limit, filing fee, fee waiver process, service methods,
  statutes of limitations by claim type, and collection procedures — each with a primary source
  and a retrieval date. Confirm the limit, the fee, and the service rules with the [COUNTY] clerk
  by phone.

M1 — Intake, timeline, evidence, and the demand letter.
  EXIT: a legal aid attorney or a court self-help center staffer reads a generated demand letter
  and says they would send it. Do not skip this gate.

M2 — Before-you-sue, including the collection reality check.
  EXIT: the same reviewer confirms the collection section is honest and complete for [STATE].

M3 — Filing guidance, exhibit packet, second language.
  EXIT: every [COUNTY] detail confirmed with the clerk; the exhibit packet prints legibly and a
  stranger can follow it.

M4 — Five real disputes.
  EXIT: report how many resolved at the demand letter stage, how many filed, how many won, and
  how many actually collected. That last number is the one nobody publishes.

=== SAFETY + LEGAL ===

- Not legal advice, not a lawyer. Every screen and every generated document, with legal aid for
  [COUNTY] and any court self-help center, both verified by phone.
- **The honesty requirement:** this app must tell people when filing is unlikely to get them
  paid. A tool that walks someone through a filing fee, a service fee, two days off work, and a
  hearing, and never mentions that the defendant has no reachable assets, has taken something
  from them. The collection reality check is not a disclaimer; it is a feature, and it comes
  before the filing flow.
- Never assess the merits. Facts, deadlines, procedure, and citations only.
- Never generate a threat. Threatening criminal prosecution to gain advantage in a civil dispute
  is improper and in some states unlawful; the blocklist test exists for that reason.
- Deadlines are hard. Display them with sources; where unverifiable, route to the clerk. A missed
  limitations period ends the claim permanently.
- Naming and service are where pro se claims die. Give both their own screens and verify both
  with the clerk.
- Evidence stays on the device. A dispute is adversarial, and the other side is sometimes a
  neighbor, a landlord, or an employer.
- Do not build anything that publishes a defendant's name.

=== HOW TO REPORT BACK ===

Lead with the M0 document: limit, fee, waiver, service rules, limitations periods, collection
procedures, each with its source and what the clerk confirmed. Then: what the M1 and M2 reviewers
changed; the integer-cents and limitations test results; and everything you could not verify.
```

---

## Why it's shaped this way

**The demand letter is the product; the courthouse is the fallback.** A specific written demand
with a number and a deadline resolves a large share of these disputes, costs about ten dollars in
certified mail, and is a thing most people simply do not know how to write. Everything downstream
exists for the cases where it fails.

**"A judgment is not money" gets its own section and gates the filing flow.** This is the fact
the whole category omits. Walking someone through a filing fee, service costs, and two days off
work without mentioning that the defendant may be uncollectable is a real harm, and the honest
version of this tool is sometimes the one that says "don't file, claim against his bond instead."

**Naming the defendant and service of process each get their own screen** because they are where
pro se claims actually die — suing a trade name instead of the LLC, or serving improperly — and
both failures happen before anyone hears the merits.

**No merits assessment, enforced by grep.** "You have a strong case" is the sentence an eager
tool wants to produce and it is both outside what software can know and the thing that sets
someone up for a bad afternoon.

**No public database of contractors or defendants,** which is the feature this idea always drifts
toward and which converts a private preparation tool into a defamation target.

**Before you build:** call the [COUNTY] clerk and ask what gets claims dismissed. The answer will
be naming and service, in that order, and it will reshape your priorities.
