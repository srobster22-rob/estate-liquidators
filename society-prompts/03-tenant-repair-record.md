# 03 — Tenant Repair Documenter + Letter Builder

**What it is:** A private evidence locker for a renter with a broken thing and a landlord who
doesn't answer. Photos with untouched timestamps, a tamper-evident log, and a printable
certified-mail-ready letter citing the actual habitability statute in their state. Data stays
on the phone.

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[CITY]`, `[LANGUAGES]`.

---

```text
You are building a repair-request documentation tool for renters in [STATE]. Build it now; do
not ask me clarifying questions. Where you need a decision I did not make, choose the option
that makes the resulting record harder to dispute, state your choice, and keep going.

Read SAFETY + LEGAL before writing code. It constrains both the architecture and the copy.

=== THE PERSON ===

Anthony rents a second-floor unit in [CITY]. The heat stopped working on a Thursday in
January. He texted the landlord. The landlord said "I'll send someone." Nobody came. He
texted again. Read, no reply. It is now nineteen days later, his kid has a cough, and he is
starting to think about withholding rent, or calling the city, or moving — and every one of
those paths requires proving that he asked, when he asked, and that it stayed broken.

His evidence today: a scroll of text messages he cannot easily export, and photos in his
camera roll among 4,000 others.

He is also afraid. Retaliation is the reason most renters don't escalate: a repair complaint
turning into a non-renewal. Anything this app does must account for the fact that he may
decide, rationally, not to send anything at all.

=== THE PROBLEM, WITH A NUMBER ===

Nearly every tenant remedy in every state — repair-and-deduct, rent withholding, code
enforcement, a habitability defense in eviction court — is gated on written notice to the
landlord and a reasonable time to cure. The specific number of days varies by state and by
defect severity. Anthony's nineteen days of texts may satisfy that, or may not, depending on
whether "written notice" in [STATE] includes text messages and whether he can produce them in
a form a court accepts.

Look up [STATE]'s actual notice requirement and cure period. Cite the statute section. Do not
write a number you did not read from a primary source.

=== WHAT SUCCESS LOOKS LIKE ===

Six weeks later, Anthony can produce a single PDF: every request with its date, every photo
with its capture time, the letter he sent, and the certified mail receipt number. Whether he
uses it in court, at a code enforcement office, or just to make the landlord finally answer,
the record exists and holds up.

=== BUILD THIS ===

1. ISSUES LIST (/) — The home screen. Each issue is a card: what's broken, where, days open,
   number of photos, whether notice has been sent. A big "+ Add issue" button. If empty, the
   screen shows one line: "Nothing logged yet. Add the thing that's broken." No onboarding
   carousel.

2. ADD / EDIT ISSUE — Fields:
   - What's broken (free text, with quick-pick chips: heat, hot water, plumbing leak, mold,
     pests, electrical, broken lock, smoke detector, window, appliance, other)
   - Where in the unit
   - When you first noticed (date picker, defaults today)
   - Severity (three options with plain descriptions, not numbers: "Annoying but livable" /
     "Making the place hard to live in" / "Dangerous or making someone sick")
   - Has anyone gotten sick or hurt? (yes/no + free text)
   The severity answer drives which statutory category the letter cites, so explain each
   option in one sentence of real-world terms.

3. EVIDENCE CAPTURE — Per issue, a timeline you append to. Four entry types:
   - PHOTO / VIDEO: captured in-app or picked from the roll. CRITICAL: preserve original EXIF
     including DateTimeOriginal. Store the original bytes unmodified plus a derived thumbnail.
     Never re-encode the original. Record separately: the file's EXIF timestamp, the device
     clock time at import, and a SHA-256 of the original bytes. Display all three. If EXIF is
     absent (many messaging apps strip it), say so on the item — "No camera timestamp in this
     file; imported [date]" — rather than silently showing the import date as if it were the
     capture date. That distinction is exactly what gets challenged.
   - NOTE: text + timestamp. For "called at 2pm, no answer."
   - CONTACT LOG: date, method (text/call/email/in person/letter), who, what was said, and
     whether they responded. This is the spine of the whole record.
   - DOCUMENT: PDF or image of a lease page, a bill, an inspection notice.
   Every entry is immutable once saved. Editing creates a new entry marked "correction to
   entry #N" with both visible. An evidence log you can quietly rewrite is worth nothing;
   make that property real and explain it to the user in one sentence.

4. TAMPER-EVIDENT LOG — Each entry stores: content hash, previous entry's hash, and creation
   time. Display the chain status on the export ("12 entries, chain intact"). Do not oversell
   this — it proves entries weren't altered after creation on this device; it is not a
   notarization and not a blockchain, and it does not prove the device clock was correct. Say
   exactly that in the export's methodology footnote. Overstating it is worse than omitting it.

5. LETTER BUILDER — The payoff. Generates a formal notice letter from the issue record:
   - Tenant name, unit address, landlord name and address (entered once, stored locally)
   - Date, and a subject line naming the defect
   - A dated chronology auto-built from the contact log and evidence timeline
   - The specific [STATE] statute section for habitability / warranty of habitability /
     landlord duty to repair, quoted accurately with its citation
   - A clear request: repair within [the statutory cure period for [STATE]] days
   - A statement that the tenant is preserving all remedies
   - Signature block
   Three delivery paths shown side by side with honest tradeoffs: certified mail with return
   receipt (strongest, costs about $9, takes days), email (fast, weaker proof), hand delivery
   with a witness. Include a field for the certified mail tracking number so it goes in the
   record, and a reminder set for the cure-period deadline.
   The letter must be editable before export. Never send anything — this app has no outbound
   channel. It produces a document the tenant sends themselves.

6. EXPORT — One button, "Build evidence packet," producing a PDF:
   - Cover page: address, tenant, landlord, issue summary, date range, entry count
   - Chronological timeline, one row per entry, with hashes
   - Full-page photos with their three timestamps and hash beneath each
   - Copies of any letters generated
   - A methodology page explaining precisely what the timestamps and hashes do and do not
     prove
   Also export raw: a ZIP with original unmodified files and a JSON manifest. A lawyer will
   want the originals, not your PDF.

7. WHAT HAPPENS NEXT — A reference page, [STATE]-specific, plainly written, covering: code
   enforcement / housing inspection for [CITY] with the actual phone number, what repair-and-
   deduct means in [STATE] and its preconditions, what rent withholding requires (in many
   states, escrow — get this right or omit it), legal aid organizations serving [CITY] with
   contact info, and a prominent section on retaliation protections in [STATE]: what counts,
   what the presumption period is, what to do if it happens. Every claim on this page carries
   its statute citation. Anything you cannot verify does not appear.

=== DATA MODEL (all local) ===

issues: id, title, category, location, first_noticed, severity, health_impact, created_at,
  notice_sent_at, resolved_at
entries: id, issue_id, type, body, created_at, device_time, content_hash, prev_hash, seq
media: id, entry_id, original_blob_ref, mime, byte_size, sha256, exif_datetime_original|null,
  exif_present bool, import_time, thumb_ref
contacts: id, issue_id, occurred_at, method, party, summary, response_received bool
letters: id, issue_id, generated_at, body_md, sent_via, sent_at, tracking_number
profile: tenant_name, unit_address, landlord_name, landlord_address, lease_start, rent_amount

=== STACK ===

- Local-first web app: React + TypeScript + Vite, installable PWA, offline-capable via a
  service worker.
- Storage: IndexedDB for records, original media blobs in IndexedDB too (do not upload).
  Use Dexie or idb — pick one and pin it.
- PDF: pdf-lib or jsPDF, generated entirely client-side.
- Hashing: Web Crypto SubtleCrypto SHA-256. No dependency.
- EXIF: exifr or piexifjs. Verify the library reads DateTimeOriginal from real phone photos
  before committing to it — test with an actual photo from an actual phone, both iOS and
  Android if you can.
- NO BACKEND. No account. No sync. If the user wants a backup they export the ZIP. Say this
  on the first screen: "Everything stays on this device. We cannot see any of it. If you
  clear your browser data, it's gone — export a backup."
- The backup warning must also appear as a persistent banner once there are more than 5
  entries and no export has ever been made. This is the app's most likely real-world failure.

=== HARD CONSTRAINTS ===

- Works fully offline after first load. Anthony's issue may literally be that the utilities
  are off.
- Photo import must handle a 12MP HEIC from an iPhone without freezing the UI. Do thumbnail
  generation in a worker. Test with a 5MB file.
- Total local storage usage displayed on a settings screen, with a per-issue breakdown, and a
  warning when approaching quota. Silent quota failure that loses evidence is unacceptable —
  handle QuotaExceededError explicitly and tell the user what to delete.
- WCAG 2.2 AA. One-handed operation: primary actions in the bottom third of the screen.
  Anthony is often holding a phone in one hand and pointing at a leak with the other.
- Reading level 6th grade for all UI. The letter itself is formal — that's intentional and
  is the one exception; explain to the user why the letter sounds different from the app.
- [LANGUAGES] from the first commit.
- No analytics, no crash reporting, no remote fonts, no network requests at all after the
  service worker caches the app. Write a test that asserts zero fetches to third-party
  origins during a full user journey.

=== DO NOT BUILD ===

- No cloud sync, no accounts, no "share with your lawyer" server feature. Export a file.
- No sending of any letter or email from the app. It generates; the tenant sends. An app that
  transmits on a tenant's behalf creates questions about who gave notice.
- No landlord-facing features, no landlord portal, no two-sided anything.
- No AI-generated legal argument. Templates with verified statute citations only.
- No public database of bad landlords, no reviews, no map of complaints. That is a different
  project with defamation exposure and it will get this one shut down.
- No blockchain, no external timestamping service, no notarization claims.
- No rent payment tracking, no lease management, no maintenance-request-to-landlord
  integration.

=== ACCEPTANCE TESTS ===

1. A photo imported with EXIF DateTimeOriginal displays that exact capture time, distinct
   from its import time.
2. A photo with EXIF stripped displays "No camera timestamp" and does not present the import
   time as a capture time.
3. The stored original bytes are byte-identical to the source file — assert by hash.
4. Editing a saved entry creates a correction entry; the original remains visible and its
   hash unchanged.
5. Altering a stored entry's body directly in IndexedDB causes the chain check to report a
   break, identifying the entry.
6. The exported PDF contains every entry, every photo, and every hash present in the record.
7. The exported ZIP's originals re-hash to the values recorded in the manifest.
8. The app functions with the network fully disabled, including photo import, letter
   generation, and PDF export.
9. Zero network requests to any third-party origin during a complete journey.
10. Importing a 5MB HEIC keeps the main thread responsive (no frame longer than 100ms).
11. QuotaExceededError surfaces a specific, actionable message rather than a silent failure.
12. The generated letter includes the [STATE] statute citation and the correct cure-period
    number from the rules file.
13. Every statute reference in the app resolves to a source URL recorded with a retrieval
    date.
14. All UI strings present in every language in [LANGUAGES].

=== MILESTONES ===

M0 — Issues + evidence timeline + photo import with correct EXIF handling.
  EXIT: import 10 photos from a real phone — some from the camera, some forwarded through a
  messaging app — and every timestamp displayed is correct or correctly marked as missing.

M1 — Hash chain + immutable entries + tamper detection test.
  EXIT: acceptance tests 3, 4, and 5 pass.

M2 — Letter builder with verified [STATE] statute text and cure period.
  EXIT: a legal aid attorney or tenant organizer in [STATE] reads a generated letter and says
  it would not embarrass the tenant. Do not skip this gate. If you cannot get a lawyer to
  read it, ship the app without the letter builder rather than shipping an unreviewed one.

M3 — Export packet + "what happens next" reference page.
  EXIT: the PDF prints legibly on paper and a stranger can follow the chronology without you
  explaining it.

M4 — One real tenant, one real issue.
  EXIT: someone with an actual broken heater uses it for two weeks and the record survives a
  phone restart, an app update, and a browser storage cleanup warning.

=== SAFETY + LEGAL ===

- This is not legal advice and must say so, on the home screen and on every generated
  document: "This tool helps you keep records. It is not legal advice and not a lawyer.
  Free legal help in [CITY]: <organization, phone>."
- Statute citations must be verified against primary sources — the state code, not a summary
  site — with the retrieval date stored and displayed. If you cannot verify [STATE]'s
  habitability statute from a primary source, do not generate a letter citing one. Say so and
  ship the letter builder with a generic notice template instead.
- Retaliation warning: before the tenant sends anything, show one screen explaining, with
  citations, what retaliation protections exist in [STATE] and what their limits are, and
  making clear that the decision to send is theirs. Do not push the user toward escalation.
  Some tenants correctly decide the risk is not worth it, and the app must not shame that.
- Do not advise rent withholding. In most states, withholding without following an exact
  procedure — often escrow — is grounds for eviction. Describe what [STATE] law requires,
  cite it, and direct them to legal aid before they act. Write this constraint in the code
  comments where the "what happens next" content lives.
- Privacy is a safety property here, not a preference. The threat model includes a landlord
  with access to the tenant's home. Add a settings option for a PIN/biometric lock on app
  open, and make the app's icon and name unremarkable.
- Never transmit the address, the landlord's name, or any photo anywhere. There is no server.

=== HOW TO REPORT BACK ===

Tell me: the [STATE] statute sections you verified and their URLs and retrieval dates, which
EXIF library you tested and against what real files, the storage-quota behavior you observed,
and anything you could not verify. If you had to guess at a legal requirement, say which one
and mark it in the code.
```

---

## Why it's shaped this way

**The EXIF distinction is the whole evidentiary value.** Photos forwarded through messaging
apps usually have their metadata stripped, so a naive implementation shows the import date and
implicitly presents it as the capture date. That's the single detail most likely to be attacked
and the one most tools get wrong. Showing three timestamps with honest labels is less impressive
and much more useful.

**"Do not oversell the hash chain"** is in there because an agent will reach for
tamper-proof language it can't support. What the chain actually proves is narrow: entries
weren't altered after creation on this device. Claiming more in a document that ends up in
front of a judge damages the tenant.

**The retaliation screen exists to slow the app down at the right moment.** Every other design
instinct pushes toward "send the letter." For a tenant on a month-to-month lease in a tight
market, sending may be the wrong call, and a tool that only knows one direction is giving
advice it isn't qualified to give.

**No public landlord database, stated flatly.** It's the feature every version of this idea
drifts toward, it carries real defamation exposure, and it converts a private evidence tool
into a target.

**Before you build:** contact the legal aid organization serving your city and ask if they'd
review the letter template. Many will. That single review is worth more than everything else in
this brief.
