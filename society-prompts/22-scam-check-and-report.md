# 22 — Scam Check + Report

**What it is:** Someone is on the phone right now saying they're from the bank, or Medicare, or
the police, and they need a decision immediately. This is a two-question screen that gives the
one instruction that works — hang up and call back on a number you find yourself — plus the
first-hour recovery steps for people who already sent money.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`, `[ORG]` (senior
center, library, credit union, faith community — whoever will run the workshops; or "no partner
yet").

---

```text
You are building a scam recognition and recovery tool for [CITY], [STATE], designed primarily
for older adults and the people who help them. Build it now; do not ask me clarifying questions.
Where you need a decision I did not make, choose the option that slows the user down and gets a
trusted human involved, state your choice, and keep going.

Read THE DUAL-USE LINE and SAFETY + LEGAL before writing code.

=== THE PEOPLE ===

Eleanor, 78, [CITY]. The phone rang. The caller said he was from her bank's fraud department,
knew the last four digits of her card, and said someone in another state was making charges.
He was calm and helpful and said he needed to move her money to a "secure account" while they
investigated, and that she must not discuss it with anyone because a bank employee might be
involved.

That last instruction is the tell, and it is also why she will not ask her daughter.

The second person is Gene, 71, who already sent $4,200 in gift cards two hours ago, has just
realized, and is so ashamed that his first instinct is to tell nobody. The shame is the second
weapon; it costs more money than the first one does, because the recovery window is measured in
hours.

The third is Alma, a librarian who gets asked about this weekly and wants something to hand
people.

=== THE PROBLEM, WITH A NUMBER ===

The FTC publishes annual Consumer Sentinel data on reported fraud losses, including breakdowns
by age group and payment method, and the FBI's IC3 publishes an annual report including an
elder fraud section. Look up the current figures, cite them with their years, and note in the
UI that reported losses are a floor — most fraud is never reported, largely because of the
shame in the paragraph above.

The mechanism nearly every one of these scams shares: manufactured urgency, an instruction to
keep it secret, and a payment method that cannot be reversed — gift cards, wire transfers,
cryptocurrency, payment apps. Those three things together are the pattern to teach, because the
specific stories change every year and the pattern doesn't.

=== THE DUAL-USE LINE ===

Do not build anything that generates, sends, or simulates a scam message, call, or phishing
email — no "test your employees" simulator, no template generator, no example messages the user
can send. Educational examples in this app are static, clearly labeled, non-copyable screenshots
or transcripts of already-public reported scams, presented for recognition only.

This is not a technicality. A convincing scam-message generator is a scam-message generator
regardless of the label on it, and this project's audience makes that risk concrete. Where you
need to show what a scam looks like, describe it and show a marked-up image; never produce a
sendable artifact.

=== WHAT SUCCESS LOOKS LIKE ===

Eleanor hangs up, calls the number on the back of her card, and learns there is no fraud case.
Gene calls the gift card issuers within the hour, files with the FTC and IC3, freezes his
credit, and tells his son — and the money is sometimes, occasionally, recoverable, but the
next attempt on him is not.

=== BUILD THIS ===

1. IS THIS A SCAM? (/) — Designed to be used while the phone is still ringing. Enormous type,
   two questions, no scrolling:
   - "Are they asking for money, gift cards, or account information?"
   - "Are they saying it's urgent, or telling you not to tell anyone?"
   Any yes produces one screen, in the largest type on the page:

     STOP. HANG UP.
     Call them back on a number you find yourself —
     on your bill, your card, or their real website.
     A real bank, Medicare, or police officer will never mind you calling back.

   Then, below it: the real callback numbers for the most-impersonated organizations, so she
   does not have to find them under pressure. Verify each one: her bank's published fraud line
   if [ORG] can supply local institutions, Medicare, Social Security, the IRS, and [CITY]'s
   police non-emergency line. Make these tap-to-call.
   That callback instruction is the single most protective sentence in the whole app. It defeats
   caller ID spoofing, it defeats urgency, and it requires no expertise. Everything else is
   supporting material.

2. WHAT KIND IS IT? — A short recognizer, one screen per family, for the common ones. Research
   the current forms from FTC and IC3 material and cite them: bank or payment-app impersonation,
   government impersonation (Social Security, Medicare, IRS, police, immigration), tech support,
   grandparent/family emergency, romance, sweepstakes and lottery, package delivery, utility
   shutoff threats, jury duty warrants, charity fraud after disasters, and investment or crypto
   schemes.
   Per family: how it opens, what they ask for, the specific tell, and the exact sentence to
   say. Also — importantly — how the legitimate version actually works: Social Security does
   send letters, Medicare does not call to sell you things, the IRS does not demand gift cards,
   the police do not settle warrants by phone. Teaching the legitimate pattern is more durable
   than teaching the fraudulent one.

3. NEVER, EVER — One short page that carries most of the protective value:
   - No legitimate organization is ever paid in gift cards. Ever. If gift cards are mentioned,
     it is a scam, with no exceptions.
   - Wire transfers, crypto, and cash-by-courier are effectively irreversible.
   - Nobody legitimate will tell you to keep it secret from your family.
   - Nobody legitimate needs remote access to your computer to give you a refund.
   - Caller ID can be faked, including a number you recognize.
   - A check that "clears" can still bounce weeks later, and the money is yours to repay.
   Each with a citable source.

4. I ALREADY SENT MONEY — Gene's screen, and the clock matters. An ordered checklist by payment
   method, verified against current FTC guidance, with phone numbers and a "do this in the next
   hour" marker on the time-critical ones:
   - Gift cards: call the issuer immediately; some can freeze remaining balances; keep the cards
     and receipts. Verify the current issuer fraud lines and list them.
   - Wire transfer: call the bank or the wire service and ask for a recall; speed is everything.
   - Payment apps: report in the app and to the bank behind it; verify what recourse actually
     exists, which is less than people assume.
   - Bank transfer or check: bank fraud department now.
   - Crypto: report to the exchange and to IC3; be honest that recovery is unlikely.
   - Credit or debit card: card issuer, and the difference in protections between the two.
   Then the universal steps: report to the FTC at ReportFraud.ftc.gov, report to IC3 at ic3.gov,
   place a free credit freeze at all three bureaus (with the current URLs and phone numbers),
   consider an identity theft report at IdentityTheft.gov if information was given, notify the
   [STATE] attorney general's consumer division, and — if the victim is an older adult — the
   [COUNTY] adult protective services number, explained as a support resource rather than a
   threat.
   And, in the same size type as everything else: "This was not your fault. These are
   professionals and they do this all day. Tell someone you trust." Verify and cite the
   recovery-scam warning too: people who report are then targeted by fake recovery services,
   and that second hit is often larger than the first.

5. FOR FAMILIES AND HELPERS — For the daughter, and for Alma at the library:
   - How to have the conversation without taking away autonomy, which is what makes people hide
     it next time
   - Setting up a trusted-contact on bank accounts, which most banks offer and almost nobody
     uses
   - Free credit freezes for someone you help
   - How to report on someone else's behalf
   - Warning signs that someone is being targeted: new secrecy about finances, unusual gift card
     purchases, a new "friend" who needs money
   - Printable workshop materials for [ORG]: a one-page handout, a wallet card with the callback
     rule and the three report numbers, and a facilitator outline for a 30-minute session, all
     in [LANGUAGES] and in large print.

6. REPORT AND REMEMBER — A local log: date, what happened, phone number or address used, what
   was said, what was sent, what was reported and when, and confirmation numbers. Prints as one
   page for a police report or a bank dispute. Local storage only.

=== DATA MODEL (local only) ===

incidents: id, occurred_at, channel enum(phone|text|email|mail|in_person|social|app),
  claimed_org, contact_identifier, story_summary, asked_for, amount_sent_cents,
  payment_method, realized_at, created_at
actions: id, incident_id, kind, done_at, org_contacted, confirmation_number, outcome
contacts_directory: id, org_name, purpose, phone, url, verified_on, verified_by
content: slug, family, body, sources jsonb, verified_on

No server. A record of having been scammed is not something to hold on someone's behalf.

=== STACK ===

- Static-first PWA: Astro or Vite + React, offline after first load, installable, IndexedDB for
  the incident log.
- The "Is this a scam?" screen must render offline, from a cold start, in under 1.5 seconds,
  with no network. It is used under pressure.
- Every phone number is a tel: link. Every report site is a plain link with the full URL shown
  as text as well, so it can be typed or read aloud over the phone.
- PDF generation client-side for handouts, the wallet card, and the incident report.
- No analytics, no third-party requests, no fonts from a CDN.
- Under 80KB JS.

=== HARD CONSTRAINTS ===

- Designed for a 78-year-old under stress: 22px minimum body text, 30px+ for the primary
  instruction, maximum contrast, no thin weights, no gray-on-gray, no animation, no timeouts,
  no modals that can trap focus.
- The callback instruction is reachable in one tap from a cold launch. Test it.
- Every phone number and URL in the app is verified by calling or visiting, with a verified_on
  date, and re-verified twice a year. A wrong fraud-report number in this app sends a
  frightened person to a dead end, and there are people who register numbers hoping for exactly
  that traffic.
- Reading level 5th grade on the emergency screens, 6th elsewhere.
- [LANGUAGES] on every screen and every printable.
- WCAG 2.2 AA, and beyond it: full screen-reader operability, and everything usable at 200%
  zoom without horizontal scrolling.
- Works fully offline.

=== DO NOT BUILD ===

- No scam message, email, call, or text generator. No phishing simulator. No "send yourself a
  test." See THE DUAL-USE LINE.
- No call blocking, call screening, or telephony integration. That is a different product with
  carrier dependencies, and a false sense of coverage is dangerous.
- No AI that judges whether a specific message is a scam. It will be wrong in both directions,
  and a false "this looks legitimate" is a catastrophic output. The recognizer is a fixed
  checklist the user answers.
- No account, no login, no cloud sync, no sharing of incident records.
- No "report a scammer" public database, no scam number lookup community wiki. Those are
  gameable and they turn into harassment lists.
- No recovery services, no referrals to any company offering to recover funds for a fee, no
  affiliate links, no advertising. Recovery-fee operations are themselves the most common
  second-strike scam; the app must name that and must never be a route to it.
- No credit monitoring product referrals. Freezes are free; say so and link the bureaus
  directly.
- No collection of the user's phone number, email, or name anywhere.

=== ACCEPTANCE TESTS ===

1. From a cold start with the network disabled, the callback instruction is reachable in one tap
   and renders in under 1.5 seconds.
2. Answering yes to either triage question shows the STOP/HANG UP/CALL BACK screen with no other
   content above it.
3. Every phone number and URL in the app has a verified_on date; any older than 180 days renders
   a staleness flag in the admin view.
4. No code path generates, composes, or sends any message on the user's behalf — verified by a
   grep and dependency check that fails the build if a mail/SMS client is present.
5. The "I already sent money" checklist orders steps by time-criticality per payment method and
   marks the one-hour items.
6. Every claim on the NEVER page has a citation with a retrieval date.
7. The recovery-scam warning appears on the reporting screen.
8. Body text renders at 22px minimum by default; primary instruction at 30px or larger;
   contrast measured at 7:1 or better on the emergency screens.
9. The app functions fully offline including PDF generation.
10. Zero third-party network requests on any screen.
11. All content and printables render in every language in [LANGUAGES].
12. The incident log stores no name, phone number, or email of the user.
13. axe-core clean; the emergency screen is fully operable by screen reader and at 200% zoom.
14. The wallet card prints at credit-card size and is legible.

=== MILESTONES ===

M0 — The one screen: triage, STOP/CALL BACK, verified callback numbers.
  EXIT: hand a phone to three people over 70 and ask them to imagine the call. They should reach
  the instruction without help and be able to read it at arm's length. If they can't, nothing
  else matters.

M1 — Scam families + the NEVER page, all cited.
  EXIT: someone who works fraud at a bank or credit union, or a [STATE] AG consumer protection
  staffer, reviews every page for accuracy and currency. Scam patterns shift yearly.

M2 — "I already sent money" with verified numbers.
  EXIT: you have called every number in the recovery checklist and confirmed it reaches the right
  place. Every one.

M3 — Family/helper section, workshop materials, second language.
  EXIT: [ORG] runs one 30-minute session using your handout and tells you what fell flat.

M4 — Six months.
  EXIT: re-verify every number and every scam family. Report what changed. This app rots faster
  than anything else in the kit and a stale version is a liability.

=== SAFETY + LEGAL ===

- Never tell a user that a specific message or caller IS legitimate. The app's answer is always
  the callback: verify independently. A false reassurance is the worst output this app can
  produce, and it is why there is no AI judging messages.
- Shame is the mechanism that compounds losses. Every screen that touches "I already sent money"
  must open with the non-blaming line, and no copy anywhere may imply carelessness — not
  "don't fall for," not "avoid being fooled," not "smart consumers know." Grep for those.
- Verify every number by calling it. Fraud-report numbers, credit bureau freeze lines, and
  gift-card issuer lines are all impersonated by scammers who purchase similar numbers and buy
  search ads. Your app's numbers must be right and must be re-checked.
- Warn about recovery scams explicitly, with a citation. Someone who has just reported a loss is
  a marked target for a second approach promising to get the money back.
- Adult protective services: present it as help available, never as a threat or a report on
  someone. Fear of losing independence is a primary reason older adults hide victimization, and
  framing matters enormously here.
- Do not encourage confrontation, engagement, "scam-baiting," or stringing along a caller. Hang
  up. Engagement marks a number as live and invites escalation.
- This is not legal or financial advice. Name [STATE]'s AG consumer division and legal aid for
  [COUNTY], verified.
- Do not display a loss statistic without its year and source, and state that reported figures
  understate the real total.

=== HOW TO REPORT BACK ===

Tell me: every phone number and URL you verified and how; which scam families you sourced from
current FTC or IC3 material and their dates; the results of the three older-adult usability
tests; the measured type sizes and contrast on the emergency screen; and everything you could
not verify. Confirm explicitly that no code path in the app can compose or send a message.
```

---

## Why it's shaped this way

**The whole app is one sentence: hang up and call back on a number you find yourself.** It
defeats caller ID spoofing, manufactured urgency, and the secrecy instruction all at once, and
it requires no ability to detect a sophisticated impersonation. Everything else — the scam
families, the recovery steps, the workshop kit — is supporting material for getting that
sentence in front of someone at the right moment, in type they can read without their glasses.

**No AI judging whether a message is a scam.** It's the obvious feature and it's the one that
could hurt someone: a false "this looks legitimate" is a catastrophic output, and the model has
no way to know that the caller knew the last four digits of her card. A fixed checklist that
always ends in "verify independently" cannot make that mistake.

**No message generator of any kind, enforced by a build check.** A tool that produces convincing
scam messages is a tool that produces convincing scam messages, and the training-simulator
framing doesn't change what the artifact is.

**The shame handling is a functional requirement, not a kindness.** Gene's two-hour delay is
where most of the recoverable money goes, and it's caused by embarrassment. Copy that implies
carelessness — "don't fall for," "smart consumers" — makes the next victim hide longer, so it's
banned by a grep test.

**Every number verified by phone, twice a year.** Scammers buy numbers and search ads adjacent to
fraud-recovery terms specifically to catch people at this moment. A stale number in this app
routes a frightened person to the second scam.

**Before you build:** ask your local credit union or bank whether they have a fraud specialist
who'd review the content and speak at [ORG]'s workshop. They usually do, they're good at it, and
they know which scams are hitting your town this month.
