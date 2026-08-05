# 09 — Community Tool Lending Library

**What it is:** Sixty households on a block own sixty drills that run for eleven minutes a
year. This is the catalog, reservation, and reminder system that makes sharing them work —
and the reminder system is the actual product.

**Fill in before pasting:** `[NEIGHBORHOOD]`, `[CITY]`, `[TIMEZONE]`, `[LANGUAGES]`,
`[ORG]` (library, church, community center, or "no host yet").

**Read first:** established tool-library software exists — myTurn is used by many real tool
libraries, and some libraries run on Koha or a plain spreadsheet. If your local library is
already running one, help them use it rather than building this. Build this when the group is
small, informal, and would never adopt a subscription product. That's a real and common case.

---

```text
You are building a community lending library system for [NEIGHBORHOOD] in [CITY]. Build it
now; do not ask me clarifying questions. Where you need a decision I did not make, choose the
option that preserves trust between neighbors, state your choice, and keep going.

=== THE PERSON ===

Deb is 44, [NEIGHBORHOOD]. She needs a tile saw for one Saturday. Buying it is $180 for a job
she will do once. Renting is $65 plus a trip across town. Three people within four blocks own
one, and she does not know which three.

The second person is Hector, who owns the tile saw and is happy to lend it, and who has twice
lent tools that came back a month late and once did not come back at all. He is now a little
reluctant, which is the exact thing that kills these projects.

The third is whoever ends up running it — probably one volunteer with a garage — who will quit
in four months if the software makes them the collections department.

=== THE PROBLEM, WITH A NUMBER ===

Household power tools sit idle nearly all of their lives; a drill's lifetime use is famously
measured in minutes. That's the opportunity. The obstacle is not matching, it's the social
cost of asking for something back. Every failed tool library failed on returns, not on
inventory.

So the system's real job: make returns automatic and impersonal, so no neighbor ever has to
text another neighbor "hey, still got my saw?"

=== WHAT SUCCESS LOOKS LIKE ===

Deb borrows the saw Saturday and returns it Sunday because she got a friendly text Saturday
night, and Hector never had to ask. Six months later he is still lending.

=== BUILD THIS ===

1. CATALOG (/) — Browse and search. Each item: photo, name, category, condition, who holds it
   now (available / out until [date] / needs repair), a plain description of what it's for,
   any deposit, and its safety class. Filter by category and availability. Search must be
   forgiving: "sawzall" finds a reciprocating saw, "weed whacker" finds a string trimmer.
   Build a synonym list; people do not know manufacturer nomenclature.

2. ITEM DETAIL — Photos, what it's for, what it does not do, what's included (bits, blades,
   charger, case, manual), condition notes and history, loan period, deposit if any, safety
   class, and any required orientation. A "Request it" button showing the next available date.

3. REQUEST + APPROVAL — A borrower requests dates. The steward approves. Approval is one tap
   from a text or email; the steward should never need to open a dashboard to say yes. On
   approval both parties get pickup details. No calendar negotiation UI — the steward's
   judgment is faster than a scheduling algorithm at this scale.

4. CHECKOUT + RETURN — Both are one action:
   - Checkout: steward scans a QR code on the item or taps it in a list, picks the borrower,
     confirms condition, done. Optionally a photo of the item at handoff.
   - Return: same, plus condition confirm and an optional damage note. Damage creates a
     maintenance record, never an accusation. The item goes to "needs repair" and off the
     catalog until fixed.
   Every item has a printed QR label linking to its page. Cheap, and it removes all typing.

5. THE REMINDER LADDER — The heart of the project. Warm, automatic, never accusatory:
   - Due date minus 1 day: "The tile saw is due back tomorrow. Need another day? Reply MORE."
   - Due date: "Tile saw due today. Reply MORE for 2 more days if nobody's waiting."
   - +2 days: "Just a nudge about the tile saw — reply MORE or DONE."
   - +7 days: the steward is notified. Only now does a human enter the loop.
   - "MORE" auto-extends by 2 days, up to twice, only if nobody has reserved it. This single
     feature removes most late returns, because most lateness is "I forgot" or "I'm not done,"
     not bad faith.
   Every message is short, friendly, and includes the item name so it means something out of
   context.

6. WAITLIST — When an item is out, a borrower joins a waitlist and is notified the moment it
   returns and is checked in, with 24 hours to claim before it passes to the next person.

7. STEWARD VIEW — What's out and to whom, what's overdue, what needs repair, pending requests,
   and this month's activity. One screen, works on a phone.

8. DONATE AN ITEM — A neighbor offers a tool: photos, what it is, condition, whether it's a
   donation or a long-term loan (track the difference — people want their table saw back
   eventually and forgetting that is how you lose a friend). Steward approves and it enters
   the catalog.

=== DATA MODEL ===

items: id, name, aliases text[], category, description, whats_included, condition enum,
  safety_class enum(basic|caution|training_required), loan_days, deposit_cents,
  owner_type enum(library_owned|on_loan_from_member), owner_member_id|null, status enum,
  acquired_on, retired_on, qr_slug, photos[]
members: id, name, phone, email, address_line, language, joined_on, waiver_signed_on,
  trainings text[], active, notes
loans: id, item_id, member_id, checked_out_at, due_at, returned_at, extended_count,
  condition_out, condition_in, damage_note, steward_id
requests: id, item_id, member_id, requested_start, requested_end, status, decided_at,
  decided_by
waitlist: id, item_id, member_id, joined_at, notified_at, expires_at
maintenance: id, item_id, reported_at, reported_by, description, resolved_at, cost_cents
reminders: id, loan_id, kind, sent_at, response, responded_at

=== STACK ===

- Next.js 15 + TypeScript + PostgreSQL (Drizzle) or SQLite — this is a small dataset; SQLite on
  one VPS with a nightly backup is a legitimate, boring, correct choice. Pick one and say why.
- SMS via Twilio behind an `SmsProvider` interface with a console implementation. Email via
  SMTP. The reminder ladder must work on whichever channel the member chose at signup.
- Image handling: resize on upload, strip EXIF GPS from photos (a photo of a tool in someone's
  garage carries their home coordinates — strip it, and note that you did).
- QR labels: generate a printable sheet of Avery-compatible labels, client-side.
- Auth: magic link email for stewards. Members do not log in; requests and responses happen
  over text and signed links.
- Job scheduling: a durable queue for the reminder ladder, persisted, idempotent, surviving
  restarts.
- Under 150KB JS. Works on any phone.

=== HARD CONSTRAINTS ===

- Members never need an account or a password. A phone number is the identity.
- Every borrower action completable by replying to a text with one word.
- The catalog is readable without any login — this is how the project recruits.
- Timezone [TIMEZONE]; due dates are dates, not timestamps, and a due date must not shift
  across DST. Test it.
- WCAG 2.2 AA. Photos need real alt text, entered at upload and required.
- Reading level 6th grade. [LANGUAGES] for all member-facing text.
- Member addresses are stored as a single line for the steward's use only, never displayed
  publicly, never in reminder texts.
- Strip GPS metadata from every uploaded photo. Test it with a photo that has it.

=== DO NOT BUILD ===

- No payments, no membership fees, no deposits collected in-app, no Stripe. Cash or nothing;
  money in the app turns neighbors into customers and creates a tax and bookkeeping problem
  the volunteer will not survive.
- No ratings, reputation scores, or trust levels for members. A neighbor's public borrowing
  score is a way to make the block worse.
- No late fees. The reminder ladder replaces them, and fees are exactly what makes people avoid
  a library rather than return an item.
- No peer-to-peer marketplace where members lend directly to each other in v1. Central
  stewardship is what makes accountability tractable; drop it and you have a Facebook group.
- No inventory forecasting, no utilization dashboards, no analytics beyond simple counts.
- No native app. No barcode scanning hardware — a phone camera on a QR code is enough.
- No blockchain, no tokens, no time-banking currency.
- No AI anything.

=== ACCEPTANCE TESTS ===

1. Searching "sawzall" returns the reciprocating saw via its alias list.
2. Checking out an item makes it unavailable and shows the return date on the catalog.
3. The reminder ladder fires at -1d, 0d, +2d, and notifies the steward at +7d, exactly once
   each, and survives a process restart between steps.
4. Replying "MORE" extends by 2 days when no waitlist exists, and does not extend when someone
   is waiting — instead it replies explaining that someone is next in line.
5. "MORE" is honored at most twice per loan.
6. Returning an item notifies the first person on the waitlist and gives them a 24-hour claim
   window; expiry passes it to the next person.
7. Marking damage moves the item to needs_repair and removes it from the catalog until
   resolved.
8. An uploaded photo containing GPS EXIF is stored without it — verify by reading the stored
   file.
9. Member addresses never appear in any public page or any SMS.
10. Due dates do not shift when a loan spans a DST transition.
11. With TWILIO_* unset, the full loan lifecycle completes against the console provider.
12. Every item photo has non-empty alt text; upload without it is rejected.
13. An item marked on_loan_from_member displays its owner to the steward and can be returned
    to that owner, closing the record.
14. axe-core reports zero violations across catalog, item detail, and steward views.

=== MILESTONES ===

M0 — Catalog, items, checkout, return. No reminders.
  EXIT: 20 real items entered with photos, and one real loan completed end to end.

M1 — Reminder ladder with console SMS.
  EXIT: tests 3-5 pass including the restart test.

M2 — Requests, approvals, waitlist, real SMS.
  EXIT: a neighbor who is not you requests an item by text and gets it.

M3 — QR labels, donations, steward view, maintenance.
  EXIT: the steward runs a month without touching the database directly.

M4 — Three months, real neighbors.
  EXIT: report items, members, loans, and the return rate. If anything is over 30 days late,
  find out what the reminder ladder did and fix it.

=== SAFETY + LEGAL ===

- Power tools injure people. Every item carries a safety_class:
  - basic: hand tools, garden tools
  - caution: drills, sanders, pressure washers — the item page shows key safety points and
    links the manufacturer manual
  - training_required: table saws, chainsaws, tile saws, ladders over a certain height. These
    cannot be checked out to a member without the corresponding entry in members.trainings.
    Enforce it in the database, not the UI.
- A liability waiver signed at membership, tracked in members.waiver_signed_on, blocking
  checkout without it. The waiver text comes from whoever hosts the library ([ORG] or the
  group), reviewed by someone competent — not generated by you. If there is no host
  organization, note in the README that the group should look into whether a fiscal sponsor or
  an existing nonprofit will house the library, because an unincorporated group of neighbors
  lending chainsaws has real exposure.
- Never let the app instruct anyone in tool use. Link the manufacturer's manual, full stop.
- Retire unsafe items rather than lending them with a warning. Provide a one-tap "retire this
  item" and require a reason.
- Insurance: whoever hosts the collection should check whether their policy covers it. Put
  this in the README as a pre-launch item, not as advice.
- Privacy: who borrowed what is visible to the steward only. Do not build a public activity
  feed; borrowing patterns reveal home projects, finances, and absences.

=== HOW TO REPORT BACK ===

Tell me: what runs, the restart-safety test result, the EXIF-stripping verification, and the
real return rate once it's been used. If the reminder wording feels off to real members, that's
the thing worth iterating on — report what they said.
```

---

## Why it's shaped this way

**The reminder ladder is the product; the catalog is table stakes.** Every tool library that
has died, died on returns. Not because people are dishonest — because asking a neighbor for
your saw back is socially expensive, so nobody does it, so items vanish, so lenders stop
lending. Automating the ask removes the cost from the relationship entirely.

**"MORE" extends automatically** because most lateness is a half-finished project, not
bad faith. Making the honest path one letter long converts would-be overdue loans into
sanctioned ones, and the data stays true.

**No fees, no ratings, no scores.** Every one of these imports a market relationship into a
neighbor relationship, and they all produce the same outcome: people avoid the library instead
of engaging with it. A tool library runs on the assumption of goodwill, and the software's job
is to protect that assumption, not to hedge against it.

**GPS stripping from photos is a small detail with a real consequence** — a photo of a table
saw taken in a garage geotags a member's home, and the catalog is public.

**Training gates enforced in the database** because "we told them to be careful" is not a
control. A table saw is genuinely dangerous, and this is one of the few places in this
low-stakes project where a hard constraint is warranted.

**Before you build:** ask your public library. A surprising number now host tool libraries,
seed libraries, and lending collections, and they have the space, the insurance, the staff, and
the foot traffic. Building it as their thing beats building it as yours.
