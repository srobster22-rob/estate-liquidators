# 32 — Security Deposit + Move-In/Move-Out Record

**What it is:** Twenty minutes with a phone on the day you get the keys, and the same twenty
minutes on the day you hand them back. Then a demand letter citing the statutory deadline your
landlord just missed.

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[CITY]`, `[LANGUAGES]`.

---

```text
You are building a security deposit documentation tool for renters in [CITY], [STATE]. Build it
now; do not ask me clarifying questions. Where you need a decision I did not make, choose the
option that produces a record a small claims judge would accept, state your choice, and keep
going.

Read SAFETY + LEGAL before writing code.

=== THE PEOPLE ===

Priya moved out of a one-bedroom in June. Her deposit was $1,450. Seven weeks later she got a
letter with three lines on it: "cleaning $400, carpet $600, painting $450." Net to her: zero. The
carpet was worn when she moved in. She has no photographs of it and no move-in inspection form,
because nobody does on the day they get the keys.

She also does not know that [STATE] gives her landlord a specific number of days to return the
deposit with an itemized statement, that the deadline has probably passed, and that in many
states missing it carries a penalty beyond the deposit itself.

The second person is Marcus, who is moving in tomorrow and has twenty minutes and no idea that
this is the most valuable twenty minutes of his tenancy.

=== THE PROBLEM ===

Security deposit disputes are among the most common landlord-tenant conflicts and among the most
winnable — because most states impose a hard deadline and an itemization requirement on the
landlord, and because normal wear and tear is not chargeable.

The evidentiary asymmetry is the whole problem. The landlord has a move-out inspection and an
invoice. The tenant has a memory of what the carpet looked like fourteen months ago.

Research and verify from [STATE]'s statutes:
- The deadline to return the deposit and/or provide an itemized statement, and what starts the
  clock
- The penalty for missing it — several states provide double or treble damages, and some require
  bad faith. Verify precisely; this is the fact that changes the negotiation.
- Whether interest on the deposit is required
- The legal definition of normal wear and tear versus damage in [STATE]
- Whether [STATE] requires a move-in or move-out inspection, a written condition statement, or
  the tenant's right to be present at the move-out walkthrough
- Any limit on the deposit amount and on non-refundable fees
- Where and how the deposit must be held, if [STATE] regulates it
- The small claims limit and the limitations period for a deposit claim

Cite each to the statute. If you cannot verify [STATE]'s deadline from a primary source, do not
compute one — route to legal aid and the state's tenant rights page.

=== WHAT SUCCESS LOOKS LIKE ===

Marcus spends twenty minutes on move-in day and has a timestamped record. Fourteen months later
Priya's situation cannot happen to him. And Priya, who found this app too late, still gets a
letter out citing the deadline the landlord missed — because the deadline claim does not depend
on her photographs.

=== BUILD THIS ===

1. WHERE ARE YOU (/) — Three doors, because the advice is completely different:
   - "I'm moving in" → the walkthrough
   - "I'm moving out" → the move-out walkthrough and the notice checklist
   - "I already moved out and there's a problem" → straight to the deadline calculator

2. THE WALKTHROUGH — Guided, room by room, designed to be done while walking. The single
   highest-value feature and it must be fast:
   - Pick the rooms you have. For each, a prompt list: floors, walls, ceiling, windows, doors,
     closets, outlets and switches, and the fixtures specific to that room (kitchen: appliances,
     counters, sink, cabinets; bathroom: tub, tile, grout, toilet, fan).
   - For each item: a photo, and a condition tap — good / worn / damaged / not working — plus an
     optional note. Nothing is required; a photo alone is worth something.
   - Prompt for the things people forget and landlords charge for: the carpet in the closet,
     behind the door, under the sink, the window screens, the blinds, the drip pans, the smoke
     detector, and a wide shot of every room from the doorway.
   - A running timer and a room counter, so it feels finite. Target: a one-bedroom in under 20
     minutes.
   - At the end: a completeness score, not as a grade but as a prompt — "you have no photos of
     the bathroom floor."
   Move-out uses the same flow, then renders **side by side with the move-in record**, item by
   item. That comparison is the artifact. It converts "it was already like that" into evidence.

3. EVIDENCE HANDLING — The same discipline as projects 03 and 27, and reuse the module if you
   have it:
   - Photo bytes hashed before anything touches them; originals stored unmodified.
   - EXIF DateTimeOriginal preserved and displayed as a capture time, distinct from import time.
     Where EXIF is absent — very common for photos that have been through a messaging app — say
     "no camera timestamp" rather than presenting the import date as when the photo was taken.
   - Entries append-only with a hash chain; corrections add an entry and both stay visible.
   - Export: a PDF packet with the side-by-side comparison and numbered exhibits, plus a ZIP of
     unmodified originals with a manifest.
   - A methodology page that states plainly what the chain does and does not prove. Do not
     oversell it.

4. THE DEPOSIT RECORD — Amount paid, date, method, what the lease says about it, any
   non-refundable fees, the address, the landlord's name and address for service, and the date
   keys were returned. That last date usually starts the clock.

5. THE DEADLINE — Computed from [STATE]'s rule and the date the tenancy ended or the keys were
   returned, whichever the statute specifies. Shown as a date with a countdown and its citation.
   When the deadline passes with nothing received, say so plainly and explain what [STATE]
   provides for that — including any multiplier — with the statute cited.
   Where the rule cannot be verified, show "confirm with legal aid" and the phone number rather
   than a computed date.

6. THE LETTERS — Generated, editable, printable:
   a. **Move-in condition statement** to send the landlord within the first days, with the
      photos referenced. Sending it, and keeping proof, is what makes it hard to dispute later.
   b. **Forwarding address notice** at move-out — in many states the landlord's obligation is
      tied to having one, and failing to provide it is how tenants lose otherwise good claims.
      Verify [STATE]'s rule.
   c. **Demand letter** when the deposit is late or the deductions are disputed: the amount, the
      statutory deadline and citation, the itemization received or not received, the specific
      items disputed with reference to the move-in record, the amount demanded, and a deadline
      to respond.
   All sent by the tenant, certified mail with return receipt, tracking number recorded.
   Cross-reference project 30 if they go to small claims.

7. WEAR AND TEAR — A plainly-written, cited page on what [STATE] treats as normal wear and tear
   versus damage, with concrete examples: worn carpet in a traffic path, nail holes, faded paint,
   minor scuffs. This is the substance of most disputes and it is almost never explained to
   tenants. Where [STATE] has no clear standard, say so and give the general principle with a
   citation to a court decision or the state's own tenant guide.

=== DATA MODEL (local only) ===

tenancies: id, address, unit, landlord_name, landlord_address, lease_start, lease_end,
  deposit_cents, deposit_paid_on, nonrefundable_fees_cents, keys_returned_on,
  forwarding_address_sent_on
inspections: id, tenancy_id, kind enum(move_in|move_out), started_at, completed_at
items: id, inspection_id, room, feature, condition enum(good|worn|damaged|not_working), note
photos: id, item_id, blob_ref, sha256, exif_datetime_original|null, exif_present bool,
  import_time
entries: id, tenancy_id, seq, created_at, body jsonb, content_hash, prev_hash, corrects_seq|null
letters: id, tenancy_id, kind, body_md, generated_at, sent_on, method, tracking_number
deductions: id, tenancy_id, description, amount_cents, disputed bool, dispute_reason
deadlines: id, tenancy_id, kind, due_on, rule_cite, source_url, satisfied_on

Local-first. The threat model includes a landlord with a key to the tenant's home; offer a PIN
lock and keep the app's name and icon unremarkable.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB for records and original blobs, offline,
  installable.
- Rules as dated, sourced JSON in /rules/[STATE_ABBR]/, Zod-validated at build time, with
  embedded test cases. No source URL and retrieval date, no build.
- Money in integer cents.
- Photo pipeline: hash originals, read EXIF with a library verified against real phone photos,
  thumbnail generation in a worker so a 12MP HEIC does not freeze the walkthrough.
- PDF via pdf-lib. Web Crypto for hashing.
- Storage quota surfaced and QuotaExceededError handled explicitly — a full walkthrough is a lot
  of photos, and silently losing evidence is unacceptable.
- No backend, no account, no analytics, no third-party requests.

=== HARD CONSTRAINTS ===

- The walkthrough must be usable one-handed while walking, with the camera opening in one tap
  from any item.
- A one-bedroom move-in walkthrough completes in under 20 minutes. Time it and report the real
  number.
- Photo capture times and import times are never conflated.
- Every legal statement cites a [STATE] statute with a retrieval date, displayed.
- Deadlines are computed or routed to legal aid — never estimated.
- Works fully offline. Moving day frequently has no wifi and bad cell service in a stairwell.
- Reading level 6th grade for app copy; letters are formal and the app says why.
- [LANGUAGES] from the first commit.
- WCAG 2.2 AA; touch targets 44px; readable at 200% zoom.

=== DO NOT BUILD ===

- No cloud sync, no account, no "share with your landlord" server feature. Export a file.
- No sending anything to the landlord from the app. The tenant sends; the app prepares.
- No landlord-facing product, no two-sided anything.
- No public database of landlords or properties, no reviews, no ratings. Defamation exposure, and
  it converts a private evidence tool into a target.
- No AI assessment of whether damage is normal wear and tear. That is the contested question and
  a generated opinion is worse than useless in front of a judge.
- No estimate of what a claim is worth and no prediction of outcome.
- No rent payment, lease management, or landlord communication features.
- No automated image analysis of condition.

=== ACCEPTANCE TESTS ===

1. A photo with EXIF DateTimeOriginal shows that capture time distinctly from import time; a
   stripped photo shows "no camera timestamp" and never presents import time as capture time.
2. Stored originals are byte-identical to the source — asserted by hash.
3. Entries are append-only; a correction preserves the original and its hash; tampering is
   detected and located.
4. The exported ZIP's originals re-hash to the manifest values.
5. The deadline computes correctly from [STATE]'s rule and the correct trigger date, verified by
   hand for three scenarios including one crossing a month boundary.
6. With the deadline rule absent, the app renders the legal aid fallback and never a computed
   date.
7. Every rule has a statute citation, source URL, and retrieval date; one missing any fails the
   build, and embedded rule tests pass.
8. The move-out view renders each item beside its move-in counterpart, and items with no move-in
   record are marked as such rather than shown as absent damage.
9. All money is integer cents; a property test shows no floating-point drift.
10. A 12MP photo import keeps the UI responsive — no frame over 100ms.
11. QuotaExceededError produces a specific, actionable message.
12. The app functions fully offline including PDF export.
13. Zero third-party network requests during a full journey.
14. All strings and letters render in every language in [LANGUAGES]; axe-core clean.

=== MILESTONES ===

M0 — [STATE] rules research, before any code.
  EXIT: deadline, trigger, penalty multiplier, wear-and-tear standard, inspection rights, and the
  forwarding-address rule — each with a statute citation and a retrieval date.

M1 — The walkthrough and the evidence layer.
  EXIT: do a real one-bedroom walkthrough yourself and report the actual time. If it is over 20
  minutes, cut prompts until it isn't — an unfinished walkthrough is worth much less than a fast
  incomplete one.

M2 — Deadline calculator and the three letters.
  EXIT: a legal aid attorney or tenant organizer in [STATE] reads the demand letter and the
  wear-and-tear page. Do not skip this gate.

M3 — Side-by-side comparison, export packet, second language.
  EXIT: the PDF prints legibly and a stranger can follow the comparison without explanation.

M4 — Three real tenancies.
  EXIT: report how many completed a move-in walkthrough, and of those, how many disputes arose
  and how they resolved. The move-in completion rate is the number that matters.

=== SAFETY + LEGAL ===

- Not legal advice. On every screen and every generated document, with legal aid for [CITY] and
  any tenant union or organizing group, verified by phone.
- Retaliation is real. Before any letter is sent, show the same kind of screen as project 03:
  what [STATE]'s retaliation protections are, their limits, and that the decision to send is the
  tenant's. Never push toward escalation, and never imply that a tenant who decides not to send
  has done something wrong.
- Never assert that a deduction is improper. The app shows the move-in record, the deduction, and
  [STATE]'s standard, and lets the tenant draw the conclusion in their own letter.
- Never state that a deadline has been violated. State the rule, the date, and what was received.
- Deposit rules vary enormously and some cities add their own on top of the state's. Check for
  [CITY] ordinances and note in the README whether you did.
- Device security is safety: PIN lock available, unremarkable name and icon, nothing on a server.
- Do not build anything that publishes a landlord's name.

=== HOW TO REPORT BACK ===

Tell me: [STATE]'s deadline, trigger, and penalty with statute citations and retrieval dates;
whether [CITY] adds its own rules; the real walkthrough time; the EXIF results against real phone
photos; what the M2 reviewer changed; and everything you could not verify.
```

---

## Why it's shaped this way

**Twenty minutes on move-in day is the entire product.** Everything downstream — the comparison,
the demand letter, the small claims exhibit — depends on a record that only exists if somebody
made it on a day when nothing was wrong yet. So the walkthrough is optimized ruthlessly for
completion speed, with a timer and a room counter, and the brief says to cut prompts rather than
let it run long.

**The deadline claim doesn't depend on the photos**, which is why Priya — who found the app too
late — still gets something. Most states impose a hard return deadline with an itemization
requirement, and several attach a multiplier for missing it. That claim stands on the calendar
alone, and it's the one that changes the negotiation.

**The side-by-side comparison is the artifact.** A folder of move-in photos is raw material; the
same closet carpet in June and in the following August, next to each other with their capture
times, is an argument.

**"Items with no move-in record are marked as such."** The tempting bug is to render a missing
move-in photo as an absence of damage. It isn't — it's an absence of evidence, and conflating
them would hand the other side an easy answer.

**No AI wear-and-tear assessment.** That's the contested question in nearly every one of these
disputes, and a generated opinion is worse than useless in front of a judge.

**Before you build:** find your state's deposit statute and read the deadline and the penalty
yourself. If there's a multiplier for a late return, that one sentence is the most valuable thing
in the app.
