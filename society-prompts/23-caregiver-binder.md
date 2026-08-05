# 23 — The Caregiver's Binder

**What it is:** One page a paramedic can read in ninety seconds, one page a hospital gets at
admission, and one page the sister who flew in can run the week from. Everything a family
caregiver knows and nobody has written down.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`.

---

```text
You are building a care information organizer for family caregivers in [CITY], [STATE]. Build it
now; do not ask me clarifying questions. Where you need a decision I did not make, choose the
option that gets accurate information into a clinician's hands faster, state your choice, and
keep going.

Read SAFETY + LEGAL before writing code. This app holds medical information and must never
become medical software.

=== THE PEOPLE ===

Rosalind, 58, cares for her mother Junie, 84, who has heart failure, early dementia, diabetes,
and eleven prescriptions from four prescribers. Rosalind knows all of it. None of it is written
down.

At 2am Junie falls. The paramedics ask what she takes and Rosalind, who has not slept, recites
nine of the eleven. At the hospital she is asked the same questions six times by six people. The
cardiologist's name is in her phone under "Dr. K." Nobody asks whether Junie has an advance
directive until day three, and the answer is that there is one, in a drawer, at home.

The second person is Rosalind's brother Paul, who flies in for a week twice a year and cannot
do anything useful without three days of briefing.

The third is the paramedic, who has ninety seconds and wants one page.

=== THE PROBLEM ===

Care information lives in one person's head. That is fine until the moment it isn't: an
emergency, a hospitalization, a respite stay, a caregiver getting sick. Transitions between
settings are a well-documented site of medication errors and lost information; look up current
research on care transitions and medication reconciliation, cite it with a year, and do not
display an unsourced figure.

The second problem is that the caregiver is also a person who will eventually need to hand this
off, and who currently cannot take a day off without a two-hour phone briefing.

=== WHAT SUCCESS LOOKS LIKE ===

At 2am, Rosalind hands the paramedic a printed page taped inside the kitchen cabinet. At
admission she hands the nurse a second page. Paul arrives in July and reads the same binder and
knows that Junie sundowns after 4pm, that she will refuse the shower for a stranger but not for
someone who offers her the blue towel first, and where the advance directive is.

=== BUILD THIS ===

Seven outputs, each printable, each fitting a specific moment. Build the printouts first and let
the data entry follow from what they need — the reverse produces a database nobody prints.

1. THE EMERGENCY PAGE — One page, high contrast, big type. Designed for a refrigerator, a
   cabinet door, and a go-bag. Contains only what someone needs in ninety seconds:
   name, DOB, photo, allergies (drug and other), current diagnoses in plain terms, current
   medications with dose and frequency, implanted devices, baseline mental status ("oriented to
   person only; this is her normal"), communication needs (hard of hearing on the left, speaks
   Tagalog when tired), the emergency contact and the healthcare decision-maker with phone
   numbers, the primary physician, the preferred hospital, whether an advance directive or
   POLST exists and exactly where it is, and code status if documented — recorded as "a signed
   [document type] exists, dated [date], located [where]," never as a claim the app makes.
   Baseline mental status is the field clinicians most want and least often get: knowing that
   confusion is her normal, or that it isn't, changes the entire workup.

2. THE HOSPITAL PAGE — Handed over at admission. Everything on the emergency page plus:
   full medication list with prescriber and pharmacy for each, over-the-counter and supplements
   (routinely missed and routinely interacting), recent hospitalizations and procedures with
   dates, all specialists with contact information, insurance identifiers, the pharmacy, care
   preferences and routines that affect a hospital stay (sleeps with the light on, needs
   glasses to hear — people lip-read more than they say), mobility and transfer needs, diet and
   swallowing precautions, and the names of who to call for decisions.

3. THE MEDICATION LIST — Its own page because it is asked for constantly and separately:
   drug name (generic and brand), dose, route, frequency, what it's for in plain words,
   prescriber, pharmacy, start date, and a notes field. Plus a "changed recently" section — the
   last 30 days of changes — which is the thing reconciliation misses.
   Include a "bring the bottles anyway" reminder, because a list plus bottles beats either.

4. THE WEEK — For Paul. The daily routine hour by hour, what happens when, what she can do
   herself and what she cannot, what makes a day go badly, what to do when it does, meal and
   fluid preferences, what is in which cupboard, the aide's schedule and phone number, and the
   dog.
   For dementia in particular, a structured "what works" section: approaches that succeed,
   approaches that reliably fail, words to use and avoid, and the specific triggers. This is
   the knowledge that takes a year to accumulate and vanishes if the caregiver is hospitalized.

5. THE DOCUMENT MAP — Not the documents; where they are. Advance directive, POLST or MOLST,
   healthcare power of attorney, financial power of attorney, will, deed, insurance policies,
   Social Security and Medicare information, bank accounts, safe deposit box and where the key
   is, tax records, and the attorney's or financial advisor's contact.
   For each: whether it exists, its date, and its physical or digital location. Optionally a
   scan attached — stored locally, never uploaded.
   VERIFY and explain, for [STATE], what an advance directive and a POLST/MOLST are, how they
   differ, who can complete them, whether witnessing or notarization is required, and where to
   register them if [STATE] has a registry. Cite it. Then route to the free resources — many
   states publish their own statutory forms at no cost, and hospital social workers and Area
   Agencies on Aging help people complete them.

6. THE APPOINTMENT SHEET — Printable before each visit: the three questions to ask, what's
   changed since last time, current medications, and space to write the answers. Plus, after,
   a place to record what was decided. Most of a visit's value is lost between the exam room and
   the car.

7. CAREGIVER SUPPORT — A short, verified [COUNTY] resource page, because the person filling out
   this app is at real risk themselves: the Area Agency on Aging and the caregiver support
   program it administers, respite options, the [STATE] family caregiver support program if one
   exists, adult day services, disease-specific organizations' local chapters and helplines,
   and support groups with times and places. Every entry phone-verified with a verified_on date.
   Also, plainly: caregiver burnout is a health problem, here is who to call, and taking a break
   is care, not abandonment.

=== DATA MODEL (local only) ===

people: id, role enum(care_recipient|caregiver|contact), name, preferred_name, dob, photo_ref,
  languages, phone, relationship, is_decision_maker bool, notes
conditions: id, person_id, name_plain, name_clinical, diagnosed_on, notes, active
medications: id, person_id, generic_name, brand_name, dose, route, frequency, purpose_plain,
  prescriber_id, pharmacy_id, started_on, stopped_on, is_otc bool, notes
med_changes: id, medication_id, changed_on, change_type, old_value, new_value, who_changed
allergies: id, person_id, substance, reaction, severity
providers: id, person_id, name, specialty, org, phone, fax, portal_url, last_seen_on
facilities: id, person_id, kind, name, phone, address, notes
events: id, person_id, kind enum(hospitalization|er|procedure|fall|infection), started_on,
  ended_on, facility, summary
routines: id, person_id, time_of_day, activity, detail, what_works, what_fails
documents_map: id, person_id, kind, exists bool, dated_on, location_text, scan_ref|null,
  notes
insurance: id, person_id, kind, plan_name, member_id_encrypted, group_number, phone
appointments: id, person_id, provider_id, scheduled_at, questions, outcome_notes
resources: id, name, category, phone, address, hours, eligibility, verified_on, verified_by

Everything local. Member IDs encrypted at rest. This is a complete medical and financial profile
of a vulnerable adult; it is exactly the dataset that should never sit on someone else's server.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB, offline, installable.
- Printing is a first-class feature, not an afterthought. Real print stylesheets, tested on
  paper, with page breaks that fall in sensible places. The emergency page must print correctly
  from a phone to a home printer, and must also render legibly as a screenshot sent by text —
  test both.
- PDF via pdf-lib for the shareable versions.
- Export: a full encrypted backup file the caregiver can store or hand to a sibling, plus plain
  PDFs. The encrypted export needs a password the user sets, with an honest warning that a lost
  password means a lost file.
- No backend, no account, no sync, no cloud. Say so on the first screen.
- [LANGUAGES] from the first commit.

=== HARD CONSTRAINTS ===

- The emergency page prints on one page. Enforce it: if the content overflows, the app tells the
  user which fields to shorten rather than silently spilling to page two. A two-page emergency
  page is a one-page emergency page with the second half unread.
- Every printed page carries the person's name, the print date, and "verify with the patient or
  caregiver" — a printed list is a starting point for reconciliation, not a source of truth, and
  saying so is what keeps clinicians willing to use it.
- Medication entry must be fast and forgiving: free text with autocomplete over a bundled name
  list, never a required lookup that blocks entry. If someone can only remember "the little
  white one for her heart," that goes in.
- Works fully offline. The 2am use is offline by definition.
- WCAG 2.2 AA. Default 18px; the emergency page's print output at 12pt minimum with the critical
  fields larger.
- Reading level 6th grade for app copy.
- No third-party network requests, ever. Assert it in a test.
- A PIN or biometric lock, on by default, with a documented tradeoff: it protects the data and
  it must never prevent access in an emergency — which is why the emergency page also lives on
  paper on the refrigerator. Say that explicitly in the app.

=== DO NOT BUILD ===

- No dosing calculations, no drug interaction checking, no allergy cross-reference, no clinical
  alerts of any kind. That is clinical decision support with a completely different regulatory
  posture, and a missed interaction warning is worse than no warning at all because it implies
  coverage.
- No medication reminders or adherence tracking in v1. It is a different product, it generates
  constant notifications, and it is not what the 2am moment needs.
- No symptom checker, no triage, no "should we go to the ER."
- No LLM summarizing a medical history or generating clinical language. Structured fields, the
  caregiver's own words.
- No patient portal integration, no EHR connection, no HL7/FHIR in v1, no credential storage.
- No cloud sync, no family sharing account, no server. Sharing is an exported file the caregiver
  hands over deliberately.
- No care marketplace, no referrals to paid home care agencies, no lead generation, no
  advertising, no insurance sales. This user is a heavy marketing target.
- No advance directive form generation. Point to [STATE]'s official free form and to the people
  who help complete it; a defective directive is worse than none.

=== ACCEPTANCE TESTS ===

1. The emergency page prints on exactly one page; overflow triggers a specific warning naming
   the fields to shorten.
2. Every printed page includes the person's name, the print date, and the verify-with-caregiver
   line.
3. A medication entered as free text with no match saves successfully and appears on all lists.
4. The medication list shows a "changed in the last 30 days" section computed from med_changes.
5. The app functions fully offline, including printing and PDF export.
6. Zero third-party network requests during a complete journey.
7. Insurance member IDs are encrypted at rest — verified by reading raw storage.
8. The encrypted export restores completely on a different device with the correct password and
   fails cleanly with a clear message on a wrong one.
9. No code path performs any interaction, dosing, or allergy check — verified by grep and
   dependency review.
10. The emergency page is legible as a phone screenshot at typical messaging compression.
11. All strings and all printed pages render in every language in [LANGUAGES].
12. PIN lock is on by default and the app explains the paper-backup tradeoff at setup.
13. axe-core clean; full entry flow completable with keyboard only.
14. Every resource entry has a verified_on date; older than 180 days renders "call first."

=== MILESTONES ===

M0 — The emergency page: data entry and one-page print.
  EXIT: fill it out for a real person and show it to a paramedic, an ER nurse, or a hospitalist.
  Ask what's missing and what they'd cut. Do this before building anything else; their answer
  determines the field list for the entire app.

M1 — Medications, providers, hospital page, appointment sheet.
  EXIT: a caregiver uses the hospital page at a real admission and reports whether anyone read
  it.

M2 — The week, routines, what-works, document map.
  EXIT: someone who does not know the care recipient runs a day from the binder without calling
  the primary caregiver.

M3 — Export, encryption, second language, caregiver resources.
  EXIT: every [COUNTY] resource phone-verified; a sibling restores the export on their own
  device.

M4 — Three real caregivers, three months.
  EXIT: report what they actually printed and kept current, and what they abandoned. Cut what
  they abandoned.

=== SAFETY + LEGAL ===

- Not medical advice, not a medical record, not a substitute for the clinical record. On every
  screen and every printout: "Information provided by the family caregiver. Please verify."
- Never perform or imply any clinical check. The app organizes what the family knows; it does
  not evaluate it. Write this in the code comments where the medication model lives, because it
  is the boundary an eager contributor will cross first.
- Advance directives and POLST are legal documents with [STATE]-specific execution requirements.
  The app records that one exists and where; it never generates one, never interprets one, and
  never displays code status as a directive. Route to [STATE]'s official form and to the free
  help — hospital social workers, the Area Agency on Aging, and in many places a hospital
  chaplain or palliative care team.
- Decision-making authority is a legal question. The app records who the family says the
  healthcare decision-maker is and whether a document exists. It never asserts that someone has
  authority.
- Privacy: this dataset would be devastating in the wrong hands and it describes a person who
  may not be able to consent. Local only, encrypted export, PIN by default, no analytics, no
  crash reporting, and a plainly-worded explanation of all of it. Also give the care recipient a
  voice where possible — if Junie can express preferences about what is shared, record them.
- Elder abuse: caregiving relationships are sometimes not safe. Include the [COUNTY] adult
  protective services number and the national elder abuse hotline on the caregiver support page,
  framed as help, and make sure nothing in the app requires the care recipient's data to pass
  through a third party who might be the problem.
- Caregiver health is a safety issue for both people. The burnout resources are not decoration;
  put them where a tired person will see them.
- Do not display any statistic you have not sourced with a year.

=== HOW TO REPORT BACK ===

Lead with what the paramedic or ER nurse told you in M0 — what they wanted, what they'd cut, and
what they said nobody ever brings. Then: the print tests on real paper and as a screenshot; the
[COUNTY] resources you phone-verified; the encrypted export round-trip result; and confirmation
that no clinical checking exists anywhere in the codebase.
```

---

## Why it's shaped this way

**Build the printouts first.** The temptation is to model the data beautifully and add printing
later, which produces a database nobody prints. The seven outputs are the product; the schema is
whatever those pages need. The one-page constraint on the emergency page is enforced in code for
the same reason — a two-page emergency page is a one-page one with the back unread.

**Baseline mental status is the field clinicians ask about and families never think to write.**
Knowing that confusion is Junie's normal — or that it emphatically is not — changes the entire
workup at 2am. It costs one text field and it's the most clinically valuable thing in the app.

**No interaction checking, no dosing, no alerts, enforced by a grep test.** It's the first
feature anyone proposes and it converts an organizer into clinical decision support, with a
different regulatory posture and a worse failure mode: a missed warning is more dangerous than
no warning, because it implies coverage that isn't there.

**The document map records locations, not documents.** "A signed advance directive dated
March 2024 is in the fireproof box in the hall closet" is what the hospital needs on day one,
and it takes five minutes to record instead of a scanning project that never happens.

**The "what works" section is the knowledge that vanishes.** A year of learning that Junie will
accept a shower if offered the blue towel first is invisible, unwritten, and lost entirely the
week Rosalind is hospitalized. Structuring it is most of what makes Paul useful in July.

**Before you build:** show a draft emergency page to an ER nurse or a paramedic and ask what
they'd cut. They'll cut half of it, and the half they keep is your v1.
