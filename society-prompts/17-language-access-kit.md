# 17 — Language Access Kit

**What it is:** A tool that helps someone with limited English get a qualified interpreter at a
hospital, clinic, or school — by naming the right, producing the request, logging what happened
when it was refused, and filing the complaint. It deliberately does **not** translate anything
important, and that refusal is the point.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]` (the languages your
area actually needs — research this from Census ACS language data for [COUNTY], don't guess).

---

```text
You are building a language access tool for people with limited English proficiency in [CITY],
[STATE], and for the advocates and staff who work with them. Build it now; do not ask me
clarifying questions. Where you need a decision I did not make, choose the option that gets a
qualified human interpreter into the room, state your choice, and keep going.

Read THE CENTRAL REFUSAL before writing any code. It inverts the obvious design.

=== THE PEOPLE ===

Mrs. Thao is 63, speaks Hmong, and is in an emergency department in [CITY] at 11pm. The nurse
is kind and is using a translation app on a phone. Mrs. Thao is being asked to consent to a
procedure. She nods, because that is what you do when someone is kind and you do not understand.
Her son, 19, is being asked to interpret for her, which he does, badly, because nobody has
taught him the words and because he is her son and this is a conversation about her body.

The second person is Marta, whose daughter's school has scheduled a special education meeting
and has sent every notice home in English. Marta has asked twice for someone who speaks Spanish
and been told they will "try to find someone."

The third is Jaya, a community health worker who accompanies people to appointments and has
watched this happen forty times and does not know that what she is watching is, in most of
these settings, a violation of a federal civil rights obligation.

=== THE PROBLEM ===

Federal law obligates many institutions to provide meaningful language access. The relevant
authorities to research and verify — do not write about any of them from memory:
- Title VI of the Civil Rights Act of 1964 and the executive order and agency guidance
  implementing it for limited English proficient individuals, which apply to recipients of
  federal financial assistance
- Section 1557 of the Affordable Care Act and its implementing regulation, covering health
  programs and activities
- Department of Education and Department of Justice guidance regarding communication with
  parents in a language they understand
- Any [STATE] statute or regulation on interpreters in health care, courts, or schools — several
  states have their own and they are sometimes stronger

For each: verify the current text and status from a primary source, quote it accurately, cite
it, and record the date you checked. Rules and enforcement guidance in this area have been
revised more than once. If you cannot verify one, omit it rather than describing it loosely.

The gap is not that the obligations don't exist. It is that the person in the room doesn't know
they exist, doesn't know the words to invoke them, and has no record afterward.

=== THE CENTRAL REFUSAL ===

The obvious product here is a translation app. Do not build one, and be explicit in the UI about
why.

Machine translation of medical consent, a diagnosis, a legal instruction, or an IEP is not
language access. It is a liability shifted onto the patient, and the failure mode is silent:
nobody in the room knows the translation was wrong. Professional interpreting in these settings
requires terminology, ethics, and accuracy standards that a phone app does not meet, and in many
of these settings a qualified interpreter is an obligation the institution owes — not a
convenience the patient should have to substitute for.

So: this app translates only its own interface and its own fixed, professionally-reviewed
phrases — the ones whose entire content is "I need an interpreter." It never translates
user-entered text, never translates clinical or legal content, and never positions itself as a
substitute for an interpreter. Put that statement in the app, in plain language, in every
language you support.

The one exception: pointing people to the institution's own interpreter line, and to telephonic
interpreter services the institution already contracts with, is exactly right. Getting a
qualified human on speakerphone in ninety seconds is the goal.

=== BUILD THIS ===

1. THE CARD (/) — The highest-value screen and the one to build first. Pick a language, get a
   full-screen card, high contrast, huge type, showing in that language and in English:
   "I speak [language]. I need an interpreter. Please call your interpreter service. I have the
   right to an interpreter at no cost to me."
   - Works offline, immediately, with no typing. One tap from the home screen.
   - A language picker that a person who cannot read English can use: language names shown in
     their own script and endonym, not English exonyms — "Español," not "Spanish"; "ພາສາລາວ,"
     not "Lao." Include an audio button that says the phrase aloud in the language, recorded by
     a human speaker, not synthesized.
   - Printable as a wallet card, two-sided, in the browser, no login.
   - Base the language list on Census ACS language data for [COUNTY] so it reflects who is
     actually here — and include the languages the national lists omit.
   The federal government publishes language identification cards; look at those for reference
   and cite them, but build yours for one-tap use on a phone at 11pm.

2. KNOW THE RIGHT — Per setting (hospital and clinic, school, court, government office, social
   services), a plain-language page in every supported language, professionally translated, no
   machine translation, covering:
   - What the institution is obligated to provide, quoted from the verified authority with a
     citation
   - That a qualified interpreter is generally provided at no cost to the patient or parent
   - That family members, and especially children, should not be used as interpreters — verify
     and quote the actual guidance on this, which is specific and strong, particularly regarding
     minor children
   - The difference between a qualified interpreter, a bilingual staff member, and a phone app,
     in one paragraph a person can use in a conversation
   - Exactly what to say to invoke it, as a scripted sentence in both languages
   - Who to ask for when the front desk says no: the patient advocate, the charge nurse, the
     school district's language access or Title VI coordinator, the agency's civil rights
     contact
   Every claim carries its citation and a verification date. Where the law is uncertain or
   varies, say so rather than overstating — a person who invokes a right that doesn't apply
   loses credibility in a room where they have little.

3. THE REQUEST — Generate a written request, in English and the person's language, for an
   interpreter at a specific upcoming appointment or meeting: date, place, language, and the
   citation. Written requests matter: they create a record, they route past the front desk, and
   for school meetings they often work when a verbal ask hasn't.
   For schools, also generate a request for translated copies of the specific documents at
   issue, naming them.

4. THE LOG — When it goes wrong, a record. Per incident: date, place, department, who was
   asked, what was said, what happened instead (no interpreter, a family member used, a child
   used, a phone app used, a bilingual staff member with no qualification), what the consequence
   was, and an optional photo of any document handed over. Local storage on the device, same
   immutability and export rules as project 03.
   This log is what turns "this keeps happening" into a complaint that goes somewhere.

5. THE COMPLAINT — Research and verify the current complaint pathways and deadlines:
   - HHS Office for Civil Rights for health care settings
   - Department of Education Office for Civil Rights for schools
   - DOJ Civil Rights Division where applicable
   - [STATE]'s civil rights or human rights agency
   - The institution's own grievance process, which is usually a required first or parallel step
   For each: what it covers, the filing deadline, whether it can be filed in a language other
   than English, and the actual form or portal. Generate a draft complaint from the incident log
   with the facts, dates, and citation filled in — the person edits and files it themselves.
   VERIFY every deadline and pathway. A missed complaint deadline caused by a wrong number here
   is the worst outcome this project can produce. Where you cannot verify, say "check the
   current deadline at <official link>" rather than printing one.

6. FOR STAFF AND ADVOCATES — A separate section for Jaya and for clinic and school staff who
   want to do this right:
   - How to access the institution's telephonic interpreter service, with the [CITY]-specific
     numbers where you can verify them
   - A one-page "how to work with an interpreter" guide: speak to the patient not the
     interpreter, short segments, no idioms, allow time
   - Signage in every supported language, printable, for a front desk
   - A "we could not find an interpreter" escalation checklist
   This is often the fastest path to change — most front-desk staff are not refusing, they do
   not know the contract exists or how to dial it.

7. LOCAL DIRECTORY — Verified by phone: which hospitals and clinics in [CITY] have on-site
   interpreters for which languages and at what hours, which have only telephonic, the school
   district's language access contact, the court interpreter coordinator for [COUNTY], and the
   community organizations serving each language group. Every entry with a verified_on date and
   a re-verification workflow (see project 18).

=== DATA MODEL (local for personal data) ===

languages: code, endonym, english_name, script, rtl bool, audio_ref, card_text,
  translation_reviewed_by, reviewed_on
content: slug, setting, language_code, body, citations jsonb, verified_on, translator,
  review_status
incidents: id, occurred_at, place, department, language_needed, what_was_requested,
  what_happened, who_interpreted enum(none|family_adult|minor_child|staff_bilingual|
  machine_app|qualified_interpreter), consequence_note, evidence_refs, created_at, seq,
  content_hash, prev_hash
requests: id, appointment_at, place, language_code, generated_at, delivered_how, response
complaint_paths: id, agency, covers, deadline_days, deadline_source_url, filing_url,
  languages_accepted, verified_on
providers: id, name, type, address, phone, interpreter_capability jsonb, hours, verified_on,
  verified_by

Incidents and requests are stored on the device only, in IndexedDB. An immigration-adjacent
threat model applies: a server-side database of who asked for a Hmong interpreter at which
hospital is not a thing that should exist.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB, offline-capable, installable.
- The card must work offline, from a cold start, with no network, in under two seconds. Cache
  every language's card and audio on install.
- Full internationalization from the first commit, including right-to-left layout support.
  Test with an actual RTL language, not a mirrored English string.
- Fonts: system fonts wherever possible; where a script needs a webfont, self-host it and
  subset it. Never a CDN. Verify every supported script actually renders on an old Android —
  missing glyph boxes are a complete failure for the user who most needs this.
- Audio: real recordings, compressed, bundled. No TTS.
- PDF generation client-side for cards, requests, complaints, and signage.
- No backend for personal data. A tiny static host is enough.

=== HARD CONSTRAINTS ===

- NEVER machine-translate user-entered text, clinical content, legal content, or any document.
  Enforce this by having no translation API in the codebase at all — the absence is the control.
- Every translated string in the app was produced or reviewed by a qualified human translator,
  and the reviewer and date are recorded per language. A language without a completed human
  review ships marked as "translation pending review" or does not ship.
- The card works offline, one tap, under 2 seconds, from a cold start.
- Every legal claim carries a citation and a verification date, displayed.
- WCAG 2.2 AA. The card is the accessibility showcase: maximum contrast, largest practical type,
  audio, and no reliance on reading English anywhere in the path to it.
- Personal data never leaves the device. No analytics, no third-party requests, ever.
- RTL languages render correctly in layout, not just text direction.

=== DO NOT BUILD ===

- No translation feature of any kind. Not for messages, not for documents, not "just for
  convenience." See THE CENTRAL REFUSAL.
- No interpreter marketplace, no booking, no payments, no referral fees to interpreting
  agencies.
- No AI interpreting, speech-to-speech, or real-time conversation mode. Whatever the current
  quality, the failure mode in a consent conversation is invisible and unrecoverable.
- No account, no login, no cloud sync of incidents.
- No naming and shaming: no public database of institutions that refused. Individual complaints
  through official channels, not a public list.
- No legal advice about the merits of anyone's complaint.
- No immigration status questions anywhere, for any reason.
- No storing of medical information beyond what the user types into an incident note.

=== ACCEPTANCE TESTS ===

1. The card renders offline, from a cold start, in under 2 seconds, in every supported language.
2. Every supported script renders correctly on an old Android profile — no missing-glyph boxes.
   Verify per language and report which you tested.
3. RTL languages lay out correctly, including mixed English and RTL content in the same card.
4. Audio plays offline for every language.
5. No translation API, SDK, or endpoint exists anywhere in the codebase — verified by a
   dependency and grep check that fails the build.
6. Every language record has translation_reviewed_by and reviewed_on populated, or is marked
   pending and excluded from the main picker.
7. Every legal claim in content has at least one citation with a verification date.
8. Incident entries are immutable; edits create corrections with an intact hash chain.
9. Zero network requests to any third-party origin during a full journey.
10. The generated complaint draft includes the incident facts, dates, and the correct agency
    with its current filing link.
11. The printable card fits a wallet-card format and prints legibly two-sided.
12. axe-core clean; the entire path from launch to card is completable without reading English.
13. The language picker shows endonyms in their own script.

=== MILESTONES ===

M0 — The card, three languages, offline, with human-recorded audio.
  EXIT: hand a phone to a speaker of each language and watch them get to their own card without
  help and without reading English. If they can't, the picker is wrong.

M1 — Know-the-right pages for health care and schools, verified and professionally translated.
  EXIT: a civil rights attorney, legal aid advocate, or an agency's language access coordinator
  reviews every legal claim and citation. Do not skip this gate — an overstated right handed to
  someone in an emergency department costs them credibility at the worst moment.

M2 — Request generator, incident log, staff section.
  EXIT: a community health worker uses it at a real appointment and tells you what was missing.

M3 — Complaint pathways with verified deadlines + local provider directory.
  EXIT: you have called each agency and each institution to confirm the process and the numbers.

M4 — Full language set for [COUNTY].
  EXIT: report which languages ACS data says [COUNTY] needs, which you shipped with human
  review, and which are pending. The gap between those lists is the project's roadmap.

=== SAFETY + LEGAL ===

- Not legal advice. On every page: "This explains rights and helps you ask. It is not legal
  advice. Free help in [CITY]: <legal aid organization, phone>." Name a real one, verified.
- Never overstate an obligation. The authorities differ by setting, by funding source, and by
  state, and a person who invokes something that does not apply is worse off than one who asks
  plainly. Where scope is uncertain, say "this generally applies to..." and cite, or say you
  are not sure.
- Never suggest a minor child interpret, and make the guidance against it prominent and quoted
  from a citable source.
- Do not ask about, record, or infer immigration status anywhere. Add a visible line: "This app
  never asks about immigration status." Fear of disclosure is a primary reason people accept a
  bad interpretation instead of insisting on a good one.
- The incident log stays on the device. It contains health information, institution names, and
  a pattern of a person's medical visits. There is no server; say so and make it true.
- Machine translation of the app's own fixed phrases is not acceptable either — the phrase "I
  need an interpreter" carries specific meaning, and a bad rendering of it in a waiting room is
  exactly the failure this project exists to prevent. Human review, recorded, per language.
- Complaint deadlines are hard. Display them with their source and date, and tell people to
  confirm at the official link.
- Work with the community organizations serving each language group before launch. They know
  which hospitals actually answer the interpreter line, which school offices are cooperative,
  and what wording people will and will not use. They should also be your translation reviewers,
  and they should be paid for that work.

=== HOW TO REPORT BACK ===

Tell me: which legal authorities you verified, from which primary sources, on what date; which
languages have completed human translation review and by whom; which scripts you confirmed
render on an old Android; the complaint deadlines you verified by phone; and everything you
could not verify. Lead with any legal claim you were unsure about.
```

---

## Why it's shaped this way

**The refusal to translate is the product.** Every instinct — and every agent's first draft —
pushes toward a translation feature, because it looks like the obvious solution and it demos
well. In a consent conversation it is not a solution; it is a way for a hospital to discharge
an obligation onto a patient, with a failure mode nobody in the room can detect. Having no
translation API anywhere in the codebase, enforced by a build check, is how that principle
survives the third sprint.

**The card is the whole first milestone** because it is what helps at 11pm. Everything else —
the rights pages, the complaint pathways — matters over weeks. The card matters in the ninety
seconds when someone is being handed a consent form.

**Endonyms in native script, with human audio,** because a language picker labeled in English
is unusable by exactly the person it exists for. This sounds like polish and is actually the
difference between a working tool and a demo.

**No public list of institutions that refused.** It's satisfying and it converts a tool that
front-desk staff can be shown into one they'll be defensive about. Most language access failures
are ignorance of an existing contract, not refusal — the staff section fixes more of them than
a shame list would.

**Pay your translators.** The community organizations that will review your translations are
doing skilled professional work, and asking for it free from the groups this project claims to
serve is the wrong way to start.

**Before you build:** pull ACS language data for [COUNTY] and find out which languages are
actually spoken there. It is reliably not the list you'd have guessed, and the languages that
surprise you are the ones with no existing materials.
