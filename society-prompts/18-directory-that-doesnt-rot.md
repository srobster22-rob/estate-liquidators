# 18 — The Directory That Doesn't Rot

**What it is:** Shared infrastructure for the problem every other project in this kit hits — a
list of places, hours, and phone numbers that is true today and quietly false in nine months.
A decay model, a fifteen-second re-verification loop, honest confidence display, and an open
export other tools can consume.

**Build this if** you've hit staleness in projects 01, 05, 06, 08, 12, 14, 15, 16, or 17 — or
if your community has three organizations each maintaining their own half-wrong resource list.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`, `[DOMAIN]` (what
this directory covers — food pantries, HHW sites, cooling centers, legal aid, whatever you
need), `[ORG]` (who will own it, or "no owner yet" — read the note at the end).

---

```text
You are building a verified local resource directory for [DOMAIN] in [CITY], [COUNTY], [STATE],
designed so that its data stays true. Build it now; do not ask me clarifying questions. Where
you need a decision I did not make, choose the option that makes staleness visible rather than
hidden, state your choice, and keep going.

The hard problem here is not storing records. It is that they decay silently. Everything below
is organized around that.

=== THE PEOPLE ===

Yolanda is looking for a food pantry on a Tuesday afternoon. The county's PDF lists eleven. Two
have closed. Three have different hours than listed. One moved four blocks. She calls four
numbers, reaches one person, and is told to come Thursday morning.

The second person is Dee, who maintains that PDF as roughly 4% of her job and updates it when
someone complains.

The third is every developer who has built a resource finder in this city — there have been at
least three — each of whom scraped Dee's PDF, each of whom shipped a beautiful map, and each of
whose maps was wrong within a year because nobody built the boring part.

=== THE PROBLEM, WITH A NUMBER ===

Measure it yourself, before you build anything, and this measurement is milestone zero: take any
existing published list for [DOMAIN] in [CITY], call every entry, and record how many have
wrong hours, wrong phone numbers, wrong addresses, or are closed. Report the percentage.

In most communities that number is between 20% and 50%, and it is the single most persuasive
fact you will ever have about why this project exists. It also tells you whether it does — if
the existing list is 95% accurate, help Dee instead of replacing her.

=== WHAT SUCCESS LOOKS LIKE ===

Yolanda sees five pantries, each showing when it was last confirmed and by whom. The one
confirmed yesterday is marked as such. The one nobody has reached in five months says "we
haven't been able to confirm this — call first" and shows the number. She goes to the right
place on the right day.

And in a year, that is still true, because twelve volunteers spend twenty minutes a month each.

=== THE DECAY MODEL ===

This is the core design. Facts do not have a single truth value; they have a confidence that
decreases with time, at different rates.

1. EVERY FIELD CARRIES ITS OWN VERIFICATION, not just the record. A location's address is
   stable for years; its hours change seasonally; its phone number changes when the carrier
   contract does; whether it currently has food changes weekly. Storing one `verified_on` for
   the whole record means the volatile fields inherit the stability of the address, which is
   how directories lie.
   Store per-field: value, verified_on, verified_by, verified_how (phone, in person, official
   website, partner report), and source.

2. EVERY FIELD TYPE HAS A HALF-LIFE, defined in config with a stated rationale:
   address ~24 months, phone ~12, hours ~4, eligibility rules ~6, "currently accepting new
   clients" ~1, event dates: expire at the event. These are starting values — measure your
   actual change rates after a year and revise them, and write the revision down.

3. CONFIDENCE IS DISPLAYED, NEVER HIDDEN. Three states, shown as text and not by color alone:
   - CONFIRMED — verified within its half-life
   - AGING — past its half-life, shown with the date and "call first"
   - UNCONFIRMED — never verified, or a verification attempt failed. Shown, but visibly marked.
   Never delete a stale record silently and never display it as though it were fresh. A user
   who knows a fact is four months old can act on it; one who doesn't cannot.

4. A FAILED VERIFICATION IS DATA. "Called three times, no answer" is a recorded outcome that
   lowers confidence, not a null. Track attempts. An organization nobody can reach is a finding
   Yolanda needs and Dee needs.

=== BUILD THIS ===

1. PUBLIC DIRECTORY (/) — Search and browse for [DOMAIN]. Each entry shows: name, address,
   phone, hours, what they provide, who is eligible, languages spoken, accessibility, whether
   an appointment is needed, cost, and — prominently, not in a footnote — the confidence state
   and the last-confirmed date for the fields that matter.
   Filters that reflect real constraints: open now, open today, no appointment needed, no ID
   required, no residency requirement, wheelchair accessible, language spoken. These are the
   things that decide whether a trip is wasted.
   Fast, static-ish, works on an old phone, printable.

2. THE VERIFICATION QUEUE — The heart of the project. /verify shows the single most valuable
   thing to check right now, sorted by (confidence decay × how often the field is used in
   search results). One record at a time, with:
   - The organization's name and phone number as a tap-to-call link
   - A script: exactly what to ask, in order, in under 60 seconds of someone's time
   - The current stored values, each with a one-tap "still correct" button
   - A field to type a corrected value
   - Outcome buttons: confirmed / corrected / no answer / disconnected / permanently closed
   - "Next" — which immediately serves the next record
   Target: 15 seconds per record for a confirmation, 60 for a correction. Time it and report the
   real number. If a volunteer can do ten in five minutes, you will get volunteers.
   Also support in-person verification with a note, and partner-reported updates.

3. THE VOLUNTEER LOOP — No accounts for the public; verifiers get a magic link. A monthly email:
   "12 records need a call. It'll take 20 minutes. Here's your link." Show each verifier what
   they've confirmed and what it's worth ("your calls kept 41 records current last quarter").
   Recognition is the entire compensation and it works, but only if the task is genuinely small.
   Never assign more than 15 records at once.

4. CHANGE HISTORY — Every field change is appended, never overwritten: old value, new value,
   who, when, how, and the outcome that produced it. Two reasons. First, when an organization
   says "we never changed our hours," you can show them when and from whom you got the old
   value. Second, after a year the history tells you your real half-lives, which is how the
   decay model stops being a guess.

5. REPORT A PROBLEM — On every public entry, one tap: "This was wrong." Free text plus what
   happened (closed, wrong hours, no answer, turned away, different requirements). Goes to the
   top of the verification queue with the report attached. A user report is the highest-signal
   input the system gets — someone stood at the door.

6. EXPORT + IMPORT — Open data, both directions:
   - Publish the whole directory as JSON and CSV, openly licensed, with per-field verification
     metadata included. Other tools in this kit should be able to consume it.
   - Use the Open Referral Human Services Data Specification (HSDS) as your interchange format
     if it fits [DOMAIN]. Research its current version and structure before committing — it is
     the established standard for exactly this, several 211s and civic data efforts use it, and
     adopting it means your data can flow into and out of systems you did not build. If it does
     not fit [DOMAIN], say why in the README and define a documented schema instead.
   - Import from an existing list — Dee's spreadsheet, the county PDF — as UNCONFIRMED records
     that enter the verification queue. Imported data is never displayed as confirmed. This is
     the single most important import rule; violating it reintroduces the problem you are
     solving.

7. ADMIN — Add and edit organizations, merge duplicates (there will be many, with slightly
   different names and the same phone), deactivate closed ones, manage verifiers, and see the
   dashboard that matters: percentage of records currently confirmed, aging, and unconfirmed,
   plotted over time. That chart is how you know the project is alive.

=== DATA MODEL ===

organizations: id, name, akas text[], parent_org_id|null, website, description, active,
  closed_on, created_at
locations: id, org_id, name, address, unit, lat, lng, accessibility jsonb, transit_notes
services: id, org_id, location_id, name, description, category, eligibility, cost,
  appointment_required, id_required, residency_required, languages text[], intake_notes
facts: id, subject_type, subject_id, field, value jsonb, verified_on, verified_by,
  verified_how enum(phone|in_person|official_web|partner|user_report|imported),
  source_note, superseded_by|null, created_at
  -- every displayed value is a fact row; corrections supersede rather than overwrite
schedules: id, service_id, weekday, opens, closes, effective_from, effective_to, notes
verification_attempts: id, subject_type, subject_id, attempted_at, verifier_id, outcome
  enum(confirmed|corrected|no_answer|disconnected|closed|refused), duration_seconds, note
verifiers: id, name, email, active, records_verified, last_active_at
reports: id, subject_type, subject_id, kind, body, reporter_contact|null, created_at,
  resolved_at, resolution
field_config: field, half_life_days, rationale, updated_on

The `facts` table with supersession rather than in-place updates is what makes history, decay,
and honest confidence possible. Do not flatten it into columns on `services` for convenience —
that shortcut is exactly how every previous version of this project failed.

=== STACK ===

- Next.js 15 + TypeScript + PostgreSQL (Drizzle). One small VPS. This is a small dataset with a
  long life; choose boring.
- Public pages server-rendered and cached, under 100KB, no JS required for search and browse.
- Verification queue: mobile-first, one-handed, tap-to-call, works on a phone while the
  verifier is on hold.
- Email via SMTP for the volunteer loop. No push, no app.
- Full-text search in Postgres. No search service.
- Nightly backup, off-box, and a restore you have actually performed.
- Export generated on a schedule as static files.

=== HARD CONSTRAINTS ===

- No record is ever displayed without its confidence state and last-confirmed date.
- Imported data enters as UNCONFIRMED. Always. Enforce it in the import code path and test it.
- Corrections never overwrite; they supersede. Full history retained.
- A verification takes under 15 seconds for a confirmation. Measure and report.
- Public pages work with JavaScript disabled and on an old phone; under 100KB.
- WCAG 2.2 AA. Confidence conveyed by text, never by color alone.
- Reading level 6th grade for public copy. [LANGUAGES] for the public directory.
- Time zone handling for hours must be correct across DST; "open now" is the most-used filter
  and it must not be wrong twice a year.
- Open export, openly licensed, always available, no login.

=== DO NOT BUILD ===

- No scraping as a substitute for verification. Scraping is fine for finding candidate records;
  they enter as UNCONFIRMED and get a phone call. A scraper that overwrites verified data with
  website content is a machine for reintroducing rot.
- No AI-generated descriptions of services, eligibility, or hours. Every value came from a
  person who confirmed it, and the provenance is the product.
- No user accounts for the public. No login to read anything.
- No reviews, ratings, or comments on organizations. A one-star review of a food pantry helps
  nobody and will end your relationships with the providers whose cooperation you need.
- No referral tracking, no lead generation, no "connect me" button that emails the org on the
  user's behalf in v1.
- No case management, no client records, no storing of anything about the people who search.
  Search queries are not logged with identifiers.
- No multi-city expansion until one [DOMAIN] in one city is above 90% confirmed and has stayed
  there for six months. This is the discipline the previous three attempts lacked.
- No mobile app.

=== ACCEPTANCE TESTS ===

1. Imported records are UNCONFIRMED and are visibly marked as such — tested through the actual
   import path, not by inserting rows.
2. A correction creates a new fact row and supersedes the old one; the old value remains
   queryable with its verifier and date.
3. Confidence state computes correctly from field-specific half-lives — test each field type at
   one day before and one day after its threshold.
4. A record past its half-life renders "call first" with the phone number, in text, not by
   color alone.
5. Three failed verification attempts lower confidence and surface the record as unconfirmed
   rather than leaving it stale-but-confirmed.
6. "Open now" is correct across a DST transition in both directions with a UTC server.
7. A confirmation through the verification UI completes in under 15 seconds of interaction —
   measured with a real run, reported honestly.
8. Merging two duplicate organizations preserves the full fact history of both.
9. A user problem report moves the record to the top of the queue with the report visible to
   the verifier.
10. The public export validates against the declared schema (HSDS or your documented one) and
    includes per-field verification metadata.
11. Public pages render with JavaScript disabled, under 100KB.
12. axe-core clean; the confidence state is announced by a screen reader.
13. The admin dashboard's confirmed/aging/unconfirmed percentages match a hand count on a
    seeded dataset.
14. No search query is stored with any identifier.

=== MILESTONES ===

M0 — Measure the rot.
  EXIT: call every entry on the existing published list for [DOMAIN] in [CITY] and report the
  error rate by category. This is the project's justification and its baseline. If the existing
  list is accurate, stop and say so — that is a successful outcome of this milestone.

M1 — Data model + import + public directory, everything unconfirmed.
  EXIT: the existing list is imported, visibly unconfirmed, and browsable.

M2 — The verification queue.
  EXIT: you verify 25 records yourself and report the real median time per record. If it is over
  30 seconds for a confirmation, fix the UI before recruiting anyone.

M3 — Volunteer loop + change history + problem reports.
  EXIT: three volunteers who are not you each verify 10 records in a month without you helping
  them.

M4 — Export + one consumer.
  EXIT: another tool — one of the other projects in this kit, or Dee's own list — consumes your
  export. And report the confirmed percentage; if it is above 90% and holding after three
  months, this worked.

=== SAFETY + LEGAL ===

- Do not publish anything about an organization that the organization has not confirmed or that
  is not already public. When a verifier learns something off the record ("we're closing in
  June"), it is a note for the queue, not a public field.
- Be a good phone citizen. Verifiers are calling small organizations with two staff. Sixty
  seconds, at a good time of day, with a script that respects them, and never during their
  service hours if you can avoid it. A directory project that annoys providers loses the
  cooperation it runs on. Put this in the verifier onboarding.
- Never publish which organizations "failed" verification as a judgment. "We could not reach
  this number" is a fact about your attempt, phrased as such.
- Search queries reveal need — someone searching for domestic violence shelters, immigration
  legal help, or HIV services. Log nothing that could identify a searcher. No analytics, no IP
  logging beyond what the web server needs for a short window, no third-party scripts.
- If [DOMAIN] includes services where a wrong entry has safety consequences — shelters, crisis
  services, legal deadlines — raise the verification cadence for those records and mark them as
  requiring confirmation before display. Say which categories those are in the README.
- Accessibility and language fields must be verified specifically, not assumed. "Wheelchair
  accessible" reported by a receptionist who has not measured a door is the same unreliable
  claim project 10 exists to fix; record who said it and how.
- Coordinate with the existing 211 or information-and-referral service in [COUNTY]. They have
  been doing this for decades, they may have data-sharing arrangements, and duplicating them
  badly serves nobody. Ask before building whether they want a feed from you or want to give
  you one.

=== HOW TO REPORT BACK ===

Lead with the M0 number: what fraction of the existing list was wrong, broken down by field.
Then: the real median verification time; the confirmed/aging/unconfirmed percentages; whether
HSDS fit [DOMAIN]; how the volunteers did without you; and everything you could not verify.
```

---

## Why it's shaped this way

**Per-field verification instead of per-record** is the one idea that makes this different from
every directory that came before. An address is stable, hours are not, and "currently accepting
clients" changes weekly. A single `last_updated` on the record lets the volatile facts hide
behind the stable ones — which is the precise mechanism by which accurate-looking directories
become wrong.

**Fifteen seconds per confirmation is a hard design target because volunteer time is the
scarce resource.** At fifteen seconds, twelve people doing twenty minutes a month keeps a few
hundred records current forever. At two minutes, nobody does it twice and the project dies the
ordinary way.

**Imported data enters unconfirmed, always.** Every previous attempt in your city imported the
county PDF and displayed it as fact — which is how three separate maps all inherited the same
30% error rate and shipped it with better typography.

**M0 is calling every entry on the existing list before writing code.** It gives you the number
that justifies the work, the baseline you'll be measured against, and occasionally the answer
that the list is fine and you should go help Dee instead. That last outcome is a success, not
a wasted week.

**Confidence displayed, never hidden,** because a user who knows a fact is four months old can
compensate — she calls first. A user shown a stale fact as current cannot. Honest uncertainty
beats false precision every time, and it is also the only sustainable position, because you
will never get to 100%.

**On ownership:** this is the project in the kit most likely to outlive its builder and most
likely to die when they lose interest. It wants an owner with institutional continuity — a
library, a 211, a united-way-type organization, a community foundation. Build it, run it for six
months to prove the loop works, and then find it a home.
