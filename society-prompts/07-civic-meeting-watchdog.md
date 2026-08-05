# 07 — Civic Meeting Watchdog

**What it is:** Your city council posts a 214-page agenda packet four days before the meeting.
This reads it, turns it into a two-minute email, tells you which items touch your street, and
tells you when public comment closes — while you can still say something.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[TIMEZONE]`, `[LANGUAGES]`,
`[AGENDA_URL]` (the page where your city posts agendas — find it before you paste).

---

```text
You are building a civic meeting monitoring and plain-language digest tool for [CITY],
[COUNTY], [STATE]. Build it now; do not ask me clarifying questions. Where you need a decision
I did not make, choose the option that keeps every published claim traceable to a source
document, state your choice, and keep going.

Read the ACCURACY DOCTRINE section before writing any code. It is the architecture.

=== THE PERSON ===

Nadia, 41, [CITY]. She found out about the rezoning at the end of her block from a neighbor,
eleven days after the council approved it. The agenda had been public. It was item 14.c,
titled "Ordinance 2024-118 — Amendment to Title 17 Zoning Map, Parcel 44-201-003." Nothing in
that string told her it was her street, and nothing told her that written comment closed at
noon the day before.

She is not going to attend meetings. She is going to read one email a week if it is short and
if it is about her.

The second user is Marcus, who writes a neighborhood newsletter and would happily include a
civic section if producing it took ten minutes instead of three hours.

=== THE PROBLEM, WITH A NUMBER ===

The information is public and functionally inaccessible: posted as a PDF packet, often within
the statutory minimum notice period, in language that requires knowing the code section to
decode, with the comment deadline stated nowhere obvious. Look up [STATE]'s open meetings law
and find the actual minimum notice period and the public comment requirements — cite the
statute. That number is the window this tool is fighting for.

=== WHAT SUCCESS LOOKS LIKE ===

Nadia gets an email on Friday: "Three things Tuesday. One is a zoning change one block from
you. Written comment closes Monday noon — here's the email address and here's what the
proposal actually says." She sends four sentences. She is on the record. That's the whole
product.

=== BUILD THIS ===

1. INGEST — Get the agendas. Research [AGENDA_URL] and identify the platform first, because it
   determines everything downstream. Common ones in US local government:
   - Legistar (Granicus) — exposes a documented web API; if [CITY] uses it, use the API, not
     scraping. Verify the current API before building.
   - Granicus / CivicClerk / CivicPlus / PrimeGov / BoardDocs / Municode Meetings — varying
     degrees of structure; some have feeds, most need HTML parsing.
   - A plain page of PDF links — the fallback, and very common.
   Build an adapter interface with one implementation for [CITY]'s platform and a generic
   PDF-links implementation as a fallback. Do not build adapters for platforms [CITY] does not
   use. Record in the README exactly what [CITY] uses and how you determined it.
   Scrape politely: identify yourself in the User-Agent with a contact URL, respect
   robots.txt, no more than one request every few seconds, cache everything by URL and ETag,
   and never re-fetch an unchanged document. This is public data being read at human speed.

2. PARSE — For each meeting, extract: body (Council / Planning Commission / School Board /
   Zoning Board), date, time, location, whether remote participation is offered, the agenda
   items in order with their numbers and titles, links to attachments per item, and — this is
   the one that matters — every deadline mentioned anywhere in the packet for written comment,
   registration to speak, or protest filing. Deadlines are usually in body text, not metadata.
   Search for them explicitly with patterns and verify by hand on ten real packets.
   Extract full text from attached PDFs (pdf.js or pdftotext). Store the text with page and
   character offsets so every later claim can point at an exact location.

3. GEOCODE THE ITEMS — The feature that turns a list into "your street."
   - Extract addresses and parcel identifiers from item titles and body text.
   - Resolve addresses via Nominatim, cached permanently, rate-limited to 1/sec with a
     descriptive User-Agent per their policy.
   - Resolve parcel numbers via [COUNTY]'s parcel/GIS service if one exists — most counties
     publish an ArcGIS REST endpoint or an open data portal. Research this; it is the single
     highest-value integration in the project, because zoning items are identified by parcel,
     not address.
   - When an item has a location, users within a radius get told. When it doesn't, it goes in
     the general digest.
   - Never guess a location. An item whose address you could not confidently resolve is
     unlocated, not approximately located.

4. THE DIGEST — Per meeting, a page and an email containing, per item:
   - The official item number and title, verbatim, linked to the source document and page
   - A plain-language "what this is" of at most two sentences
   - "Who this affects," when determinable
   - Every deadline, with the date and time in [TIMEZONE] and how to submit
   - A "read the original" link that opens the exact PDF page
   Items are sorted by likely public interest, not agenda order: land use, taxes and fees,
   police and public safety, budget, contracts over a threshold, then everything else. State
   the sort order on the page so it isn't a hidden editorial judgment.

5. ALERTS — Sign up with an email or a phone number, plus either a street address or a list of
   keywords, or both. Send:
   - A weekly digest of upcoming meetings
   - An immediate alert when a new agenda contains an item within 1/4 mile of the saved
     address, or matching a keyword
   - A deadline reminder 24 hours before written comment closes on an item they were alerted
     to. This is the highest-value message in the system.
   Never more than one email per day. Every message links to sources and has one-click
   unsubscribe.

6. AFTER THE MEETING — Once minutes or video are posted, attach them to the meeting and update
   each item with the recorded outcome, taken verbatim from the minutes ("Passed 5-2",
   "Continued to 11/12"). If you transcribe video, use a local Whisper model, store the
   transcript with timestamps, and link every quote to its timestamp. Never state an outcome
   that is not in the official minutes; a transcript is evidence of what was said, not a
   record of what was decided.

7. ARCHIVE — Every document you fetch is stored with its URL, fetch time, and SHA-256, and
   served from your copy. Local government sites reorganize constantly and links rot within a
   year. The archive is quietly one of the most valuable things this project produces.

=== ACCURACY DOCTRINE ===

This project publishes claims about government actions. Being wrong here damages real people
and destroys the tool's credibility permanently. Four rules, and they are architectural:

1. EVERY published sentence traces to a source. Each summary field stores
   {source_document_id, page, char_start, char_end} for the text it derives from. If a claim
   cannot cite a span, it does not publish. Enforce this in the type system — make the
   summary object impossible to construct without a citation.
2. AN LLM MAY DRAFT; IT MAY NOT PUBLISH. Using a model to turn "Ordinance 2024-118 — Amendment
   to Title 17 Zoning Map, Parcel 44-201-003" into "This would let the lot at 400 Elm build
   apartments instead of only houses" is exactly the right use of one. But:
   - It receives only the extracted text of that item, never the whole packet, and never
     external context.
   - It is prompted to output only what the text supports, to quote the operative language
     verbatim in a separate field, and to return "unclear" rather than infer. Give it an
     explicit refusal path.
   - Every generated summary is stored with status=draft and is NOT sent or published until a
     human approves it in a review queue. Build the review queue in M1, not later.
   - A reviewer sees the draft, the verbatim quote, and the source page side by side, and can
     approve, edit, or reject in one keystroke.
   - Generated text is visibly labeled in the UI and email: "Plain-language summary, reviewed
     by a person. Read the original."
3. VERBATIM ALWAYS AVAILABLE. Every item shows the official title exactly as written, and
   links to the source page. The plain-language version is an addition, never a replacement.
4. NEVER CHARACTERIZE MOTIVE OR PREDICT OUTCOME. No "council is expected to approve," no
   "critics say," no "controversial." Describe what the document says and what the deadline
   is. The moment this tool sounds like it has an opinion, it becomes something people argue
   with instead of something they use.

=== DATA MODEL ===

bodies: id, name, jurisdiction, meeting_schedule, contact_email, comment_instructions
meetings: id, body_id, starts_at, location, remote_url, agenda_url, status, fetched_at
documents: id, meeting_id, kind, url, sha256, fetched_at, local_path, page_count, text
items: id, meeting_id, ordinal, item_number, official_title, doc_id, page_start, page_end,
  category, latitude, longitude, location_confidence, parcel_id
deadlines: id, item_id|meeting_id, kind, due_at, instructions, source_doc_id, source_page
summaries: id, item_id, draft_text, verbatim_quote, source_span jsonb, model, generated_at,
  status(draft|approved|rejected), reviewed_by, reviewed_at, edited_text
outcomes: id, item_id, result_text, source_doc_id, source_page, recorded_at
subscribers: id, email|phone, address, lat, lng, radius_m, keywords text[], language,
  verified bool, created_at, last_sent_at
sends: id, subscriber_id, kind, sent_at, item_ids[]

=== STACK ===

- Node/TypeScript. A worker process for ingest on a schedule, a small web app for the reader.
- PostgreSQL. Full-text search on document text via Postgres tsvector — do not add
  Elasticsearch.
- pdf.js or poppler's pdftotext for extraction, with a layout-preserving mode.
- Whisper (whisper.cpp or faster-whisper) locally for transcription. Do not send meeting audio
  to a third-party API; it is public, but the cost and rate limits will kill the project and
  local is fast enough for a weekly meeting.
- Email: a plain SMTP provider, plaintext-first messages with a minimal HTML alternative. Many
  recipients are on old email clients. Test the plaintext version — that's the one that must
  be complete.
- LLM for drafting only, behind an interface with a null implementation so the entire pipeline
  runs and is testable with no model access. The app must be fully functional — ingest, parse,
  geocode, alert — with the summarizer disabled.
- Deployment: one small VPS. This handles a city.

=== HARD CONSTRAINTS ===

- Politeness: robots.txt respected, identifying User-Agent with a contact URL, conditional
  requests, aggressive caching, and no re-fetch of unchanged documents. If [CITY]'s site blocks
  you, contact the clerk and ask — they will often just give you access, and that relationship
  is worth more than a workaround.
- Ingest must be idempotent and resumable. A crash mid-meeting leaves no partial state.
- Every published claim carries its source link. Enforced by type, tested.
- Emails are readable as plaintext with all information present.
- WCAG 2.2 AA on the web reader. Reading level 8th grade for summaries — this is one place
  where 6th grade is not achievable without losing legal precision, and precision wins; say so
  in the README.
- [LANGUAGES]. Machine-translate only with a visible label and a link to the original.
- Time zone [TIMEZONE] everywhere, tested against a UTC server.
- No paywall, no ads, no account required to read anything.

=== DO NOT BUILD ===

- No comment submission on behalf of users. Give them the email address and the deadline; the
  words must be theirs. An automated comment pipeline gets public comment discounted for
  everyone.
- No voting records, scorecards, or "how your councilmember votes" ratings in v1. That is an
  advocacy product and it will change how the clerk's office treats you.
- No opinion, endorsement, or campaign content. Ever.
- No AI-generated "impact analysis," "what this means for you" speculation, or predictions.
- No social auto-posting in v1.
- No multi-city expansion until one city works completely. The temptation to generalize the
  scraper before finishing one city is the standard way these projects die.
- No user accounts beyond an email or phone plus preferences.
- No live meeting streaming or chat.

=== ACCEPTANCE TESTS ===

1. Ingest of a real [CITY] agenda produces the correct number of items with correct item
   numbers, verified by hand against the PDF.
2. Re-running ingest on unchanged documents makes zero new fetches and creates zero new rows.
3. Every summary row has a non-empty source_span; constructing one without a span is a
   compile error.
4. No summary with status=draft is ever included in an email or a public page.
5. The full pipeline runs end to end with the LLM interface set to null, producing digests
   containing official titles, deadlines, and links but no plain-language text.
6. An item whose address fails to geocode has null coordinates and appears in the general
   digest, never in a proximity alert.
7. A subscriber 200m from a geocoded item is alerted; one 2km away is not.
8. Deadline extraction finds the written-comment deadline in 10 real packets you check by
   hand; report the true hit rate rather than claiming success.
9. A subscriber receives at most one email per day regardless of how many items match.
10. Unsubscribe works from a single click with no login and is honored immediately.
11. Every document in the archive re-hashes to its stored SHA-256.
12. Plaintext email contains every piece of information the HTML version does.
13. All datetimes render in [TIMEZONE] with a server in UTC.
14. robots.txt disallow rules are honored — test with a fixture that disallows the agenda path.
15. No published string contains characterization words from a blocklist ("controversial",
    "expected to", "critics", "supporters say"). Fails the build.

=== MILESTONES ===

M0 — Ingest + parse one body's agendas, no summaries, no alerts.
  EXIT: the last 8 real meetings parse with correct items and correct deadlines, checked by
  hand. Report the deadline extraction accuracy honestly.

M1 — Digest page + human review queue + LLM drafting.
  EXIT: you review and approve one real meeting's summaries in under 15 minutes, and a
  neighbor who knows nothing about local government reads the page and correctly tells you
  what one item would do.

M2 — Geocoding + proximity alerts.
  EXIT: an item on your own street triggers an alert to you, and an item across town does not.

M3 — Email digest + deadline reminders.
  EXIT: someone who is not you subscribes, receives a digest, and submits a public comment
  because of it. This is the only exit criterion that matters in the whole project.

M4 — Outcomes from minutes + the archive.
  EXIT: a link that has rotted on the city's site still resolves from your archive.

=== SAFETY + LEGAL ===

- Meeting agendas, packets, and minutes are public records. Republishing them with attribution
  is ordinary. Keep the archive faithful — never alter a source document — and always link to
  the official original.
- Do not present the tool as official. A persistent line: "This is an independent volunteer
  project. It is not [CITY] government. Always check the official agenda at [AGENDA_URL]."
- Correct errors visibly. When a summary is wrong, publish the correction on the item page
  rather than silently editing, and keep a public /corrections log. Credibility here is the
  entire asset and it is built by how you handle being wrong.
- Personal information appears in agenda packets — variance applications carry home addresses,
  some items name individuals. Do not extract, index, or alert on individual names. Redact
  nothing from archived originals, but never build a person-search feature over them.
- Introduce yourself to the city clerk before launch. Explain what you're building. Clerks are
  usually glad someone is reading and will tell you when the posting schedule changes.
- Check [STATE]'s open meetings law for any notice or publication requirements relevant to
  republication, and cite what you find in the README.

=== HOW TO REPORT BACK ===

Tell me: which platform [CITY] uses and how you confirmed it; the real deadline-extraction hit
rate on hand-checked packets; the geocoding success rate; how long a human review of one
meeting actually takes; and everything you could not verify. If the LLM produced a summary
that a reviewer had to reject, show me it — that failure is more informative than ten
successes.
```

---

## Why it's shaped this way

**Human review before publish is what separates this from a hallucination machine pointed at
local government.** The LLM's job here — turning "Amendment to Title 17 Zoning Map, Parcel
44-201-003" into "apartments instead of houses at 400 Elm" — is genuinely the right use of the
technology. But a wrong summary of a government action, sent by email to 400 neighbors, is a
harm you can't take back. The review queue costs fifteen minutes a week and is the whole reason
this can be trusted.

**"Runs fully with the summarizer disabled"** guarantees the pipeline never becomes dependent
on model access, and makes the whole thing testable. Titles, deadlines, and links alone already
beat the status quo.

**Deadline extraction is the actual product.** Everything else is context. Knowing a rezoning
exists after comment closed is trivia; knowing it exists on Friday when comment closes Monday
is participation. Test that extraction by hand on ten packets and report the true rate.

**Parcel-number geocoding via the county GIS** is what makes proximity alerts work for land use
items, which are the ones people care most about — and zoning items are identified by parcel,
not address. It's the least glamorous integration and the highest-value one.

**No scorecards, no opinions, blocklisted characterization words.** The moment this reads as
advocacy, the clerk's office treats you as an adversary and half the audience discounts it. Dry
is a feature.

**Before you build:** email your city clerk and ask how agendas are posted and whether there's
a machine-readable feed. Roughly half the time, there is one nobody advertises.
