# 27 — Flood Risk, Basement Water, and the Insurance Clock

**What it is:** Two things most people find out too late — that ordinary home insurance doesn't
cover flood, and that buying flood insurance generally starts a waiting period before it takes
effect. Plus a damage log that survives an insurance dispute.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`.

---

```text
You are building a flood risk and water damage tool for households in [CITY], [COUNTY], [STATE].
Build it now; do not ask me clarifying questions. Where you need a decision I did not make,
choose the option that gets someone protected before the water arrives, state your choice, and
keep going.

Read SAFETY + LEGAL before writing code. One section of this app is a life-safety warning and
must not be softened.

=== THE PEOPLE ===

Ruth has lived in her house eleven years. It has never flooded. Her insurance agent mentioned
flood coverage once and she declined it, because she is not in a flood zone and because she
believed her homeowners policy covered water. It does not — standard homeowners and renters
policies generally exclude flood, and a large share of flood claims come from properties outside
the mapped high-risk areas.

She will discover both facts in the same week, and by then it will be too late to buy a policy,
because flood insurance generally does not take effect the day you buy it.

Marcus rents a garden apartment. Three inches of water came up through the floor drain last
spring. His landlord's policy covers the building; nothing covered Marcus's things. He does not
know that renters flood coverage exists and is inexpensive.

Deb is standing in four inches of water right now, and what she needs is a photograph sequence
and a phone number, not an explainer.

=== THE PROBLEM ===

Three under-known facts, and getting them in front of people early is most of this project:

1. Standard homeowners and renters insurance generally does not cover flood. Flood coverage is
   separate — through the National Flood Insurance Program or a private carrier.
2. A new flood policy generally does not take effect immediately. Verify the current waiting
   period and its exceptions from FEMA/NFIP directly; there is one, it is measured in weeks, and
   it means the decision has to be made on a dry day.
3. Water that backs up through a drain or sewer is typically **not** covered by flood insurance
   either. It usually needs a separate sewer/water backup endorsement on the homeowners policy.
   This is the single most common uncovered basement loss and almost nobody knows the
   distinction.

Verify all three from FEMA, the NFIP, and your state insurance department before writing a word.
Cite them, date them, and never paraphrase an insurance term from memory.

=== WHAT SUCCESS LOOKS LIKE ===

Ruth learns in March that she is not covered, learns what it costs, and either buys a policy or
declines it knowing what she declined. Marcus adds a renters flood policy for the price of a
takeout order. Deb photographs everything before she touches it.

=== BUILD THIS ===

Three modes, because the same household needs completely different things depending on when they
arrive. Build them in this order.

1. AM I COVERED? (/) — The default screen, aimed at a dry day.
   Four questions: do you own or rent; do you have homeowners or renters insurance; does your
   policy include flood (most people do not know — tell them the exact phrase to search for on
   their declarations page); does it include sewer/water backup (again, the phrase to look for).
   Then a plain result: what is and is not covered, what the gaps are, what each costs roughly,
   and — prominently — the waiting period, framed as a deadline rather than a footnote:
   "If you buy today, coverage generally starts around <date>. Buying during a forecast does not
   work."
   Include: renters can buy contents-only flood coverage; landlords' policies do not cover a
   tenant's belongings; and coverage is available to properties outside high-risk zones, often
   at lower cost.

2. WHAT'S MY RISK? — Flood zone lookup by address.
   FEMA publishes the National Flood Hazard Layer and a map service center; research what is
   available programmatically, verify it, and use it. Explain the zone in plain words, and then
   explain what the zone does and does not mean:
   - A high-risk zone (an SFHA) generally triggers a mandatory purchase requirement for a
     federally backed mortgage. Verify this.
   - A moderate or low-risk zone is not "no risk." A substantial share of claims come from
     outside high-risk areas — verify the current figure and cite it.
   - Maps are drawn on a schedule and can be years old; they may not reflect new upstream
     development, and they generally do not model heavy-rain street flooding or sewer surcharge
     at all. Say this plainly. It is the most important caveat on the page.
   If you cannot access the map data reliably, link FEMA's own lookup rather than approximating,
   and say so.

3. BEFORE IT HAPPENS — A prioritized, costed checklist, each item cited where it makes a
   safety or insurance claim:
   - Buy the coverage (the deadline again)
   - Sewer backup endorsement, and what a backwater valve is and roughly what it costs
   - Sump pump, and a battery or water-powered backup — the failure mode is a pump that stops
     when the power does, which is exactly when it is needed
   - Move the irreplaceable things off the basement floor; a documents-and-photos go-box
   - Grading, downspouts, window wells, and where water actually enters most homes
   - Photograph and inventory your belongings now, room by room, while they are dry. This takes
     twenty minutes and is what an adjuster will ask for.
   - Know where your water main and electrical panel are, and how to shut them off

4. IT'S HAPPENING NOW — A short, calm, high-contrast screen. Life safety first, in the largest
   type on the page, quoted from an authoritative source with a citation:
   - Never walk or drive through floodwater. Quote the National Weather Service guidance
     verbatim; a small depth of moving water moves a car, and this is how most flood deaths
     happen.
   - Do not touch electrical equipment while standing in water. Do not enter a flooded basement
     with submerged outlets or a submerged panel.
   - Floodwater may contain sewage, chemicals, and hazards you cannot see.
   - If it is rising, leave. Things are replaceable.
   Then, only after that: shut-off instructions, what to photograph, and who to call.

5. THE DAMAGE LOG — What Deb needs, and the part that pays for itself in a dispute.
   - Photograph everything before moving or cleaning anything, including a wide shot of each
     room, water lines on walls, and serial numbers. Preserve EXIF capture times; store the
     original bytes unmodified with a SHA-256; display capture time, import time, and whether
     EXIF was present — the same evidence discipline as project 03, for the same reason.
   - A room-by-room item list: what it was, roughly what it cost, roughly when bought, whether
     it can be dried or is a loss.
   - A contact log for every call with the insurer, the adjuster, and any contractor: date,
     time, name, what was said, claim number.
   - Receipts for anything spent — pumps, fans, a hotel, a plumber. Additional living expenses
     are frequently reimbursable and frequently unclaimed for lack of receipts.
   - Export as a PDF claim packet plus a ZIP of unmodified originals with a manifest.
   Include a caution: mitigation matters. Most policies require reasonable steps to prevent
   further damage, and mold begins quickly in wet materials. Verify current EPA/CDC guidance on
   drying timelines and mold and cite it. Do not tell anyone to gut their house before an
   adjuster sees it — tell them to document, mitigate, and ask their insurer what they require.

6. AFTER — What comes next, verified for [STATE]:
   - The claim process and how long an insurer has to respond under [STATE] law
   - What to do when a claim is denied or underpaid: the appeal path, [STATE]'s insurance
     department complaint process, and what a public adjuster is (and that they take a
     percentage)
   - FEMA individual assistance: only available after a federal disaster declaration, generally
     capped, and not a substitute for insurance. Verify and state this precisely — the belief
     that "FEMA will cover it" is a major reason people decline flood insurance.
   - Contractor fraud after a disaster: never pay in full up front, verify licensing with
     [STATE], be wary of door-to-door offers. Cross-reference project 22.
   - Mold remediation, and when it is a professional job

7. LOCAL — [CITY] and [COUNTY] specifics, phone-verified: sandbag distribution sites and when
   they open, the storm drain complaint line, any municipal sewer backup reimbursement or
   backwater valve subsidy program (several cities run these and they are badly publicized),
   elevation certificate access, and the floodplain manager's phone number.

=== DATA MODEL (local only) ===

profile: tenure enum(own|rent), has_policy bool, has_flood bool, has_backup_endorsement bool,
  policy_notes, zone_looked_up, zone_result, zone_checked_on
checklist: id, slug, status, completed_on, cost_note
events: id, started_on, description, water_depth_note, source enum(surface|sewer|groundwater|
  unknown|not_sure)
damage_items: id, event_id, room, description, purchase_year, purchase_cost_cents, condition,
  photo_refs
photos: id, event_id, blob_ref, sha256, exif_datetime_original|null, exif_present bool,
  import_time, room, note
calls: id, event_id, occurred_at, party, person, claim_number, summary, seq, content_hash,
  prev_hash
receipts: id, event_id, vendor, amount_cents, dated_on, category, blob_ref

Local-first. A record of someone's flood loss and their insurance dispute is theirs.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB, offline-capable, installable. Offline is
  not optional here — the power is out during the event this app exists for.
- Facts and checklists as dated, sourced JSON, Zod-validated at build time; no source URL and
  retrieval date, no build.
- Flood zone lookup: FEMA's published services, verified before use, with the answer cached
  locally and stamped with the date checked. If unavailable, link FEMA's lookup and say so
  rather than estimating.
- EXIF via a library verified against real phone photos; hashing via Web Crypto; PDF via pdf-lib.
- No backend, no account, no analytics, no third-party requests except the FEMA lookup.
- Under 200KB JS.

=== HARD CONSTRAINTS ===

- The "it's happening now" screen renders offline, from a cold start, in under 2 seconds, with
  life-safety guidance above everything else and no scrolling required to see it.
- Every insurance claim in the app carries a citation and a retrieval date. Never paraphrase a
  policy term.
- The waiting period is rendered as a computed date, not a duration, wherever a purchase decision
  is being discussed.
- Photos: originals stored byte-identical, EXIF capture time distinguished from import time, and
  "no camera timestamp" shown honestly when EXIF is absent.
- WCAG 2.2 AA; 18px minimum; the emergency screen at 22px+ with 7:1 contrast; readable at 200%.
- Reading level 6th grade. [LANGUAGES] on every screen.
- Storage quota handled explicitly — a flood photo set is large, and silent QuotaExceededError
  losing someone's claim evidence is unacceptable. Show usage, warn early, handle the error.

=== DO NOT BUILD ===

- No insurance quotes, no agent referrals, no affiliate links, no lead generation to carriers or
  public adjusters. This household is a marketing target at its worst moment.
- No claim estimate, no damage valuation, no "you should be owed $X." Document; do not appraise.
- No advice on whether to file a claim. Filing has consequences for premiums and renewals that
  vary by carrier and state; say that it is a real consideration and route to the state
  insurance department's consumer line.
- No structural, electrical, or mold-remediation instructions beyond citing official guidance and
  saying when it is a professional job.
- No flood forecasting or river-stage prediction. Link the National Weather Service.
- No account, no cloud sync, no sharing platform. Export a file.
- No LLM anywhere in the insurance or safety content.
- No property-level public map of flood claims or losses.

=== ACCEPTANCE TESTS ===

1. The emergency screen renders offline from a cold start in under 2 seconds with the
   never-drive-through-water guidance above the fold at the specified type size and contrast.
2. Every insurance statement in the content has a citation with a retrieval date.
3. The waiting period renders as a date computed from today, and a test asserts it is never
   rendered as a bare duration on the purchase screens.
4. A photo with EXIF DateTimeOriginal shows that capture time distinctly from its import time; a
   stripped photo shows "no camera timestamp."
5. Stored originals are byte-identical to the source — asserted by hash.
6. The call log is immutable; edits create corrections and the hash chain detects tampering.
7. The exported ZIP's originals re-hash to the manifest values.
8. QuotaExceededError produces a specific, actionable message naming what to delete.
9. The app functions fully offline including photo import and PDF export.
10. A failed or unavailable flood zone lookup renders "check FEMA's map" and never an estimated
    zone.
11. Zero third-party network requests other than the FEMA lookup, asserted.
12. All strings render in every language in [LANGUAGES].
13. axe-core clean; emergency screen operable by screen reader; no horizontal overflow at 200%.
14. The sewer-backup distinction appears on the coverage result whenever the user indicates no
    backup endorsement.

=== MILESTONES ===

M0 — The three facts, verified and written up before any code: the flood exclusion, the waiting
  period and its exceptions, and the sewer backup distinction.
  EXIT: each cited to FEMA, the NFIP, or [STATE]'s insurance department, with URLs and dates.
  Confirm the waiting period by calling the state insurance department's consumer line.

M1 — "Am I covered?" and the before-it-happens checklist.
  EXIT: an insurance agent or a state insurance department consumer specialist reads every
  coverage statement and finds nothing wrong. Do not skip this gate.

M2 — The emergency screen and the damage log with evidence handling.
  EXIT: import 10 real phone photos, some forwarded through messaging apps, and every timestamp
  is correct or correctly marked missing.

M3 — Flood zone lookup, local page, second language.
  EXIT: every [CITY] and [COUNTY] item phone-verified, including whether a backwater valve
  subsidy exists.

M4 — One household, one season.
  EXIT: somebody either buys coverage or declines it knowing what they declined. Report which.

=== SAFETY + LEGAL ===

- Not insurance advice, not legal advice, not a coverage determination. On every screen, with
  [STATE]'s insurance department consumer line, verified by phone.
- The life-safety guidance is quoted, not paraphrased, from the National Weather Service and
  CDC, with citations. Never soften it, never bury it, never put anything above it on the
  emergency screen. Most flood deaths involve vehicles in moving water.
- Never tell anyone their loss is or is not covered. The app explains what policy types generally
  cover and tells them the phrases to look for on their own declarations page.
- Never estimate a claim value or advise on whether to file.
- Do not tell anyone to enter a flooded basement. Submerged outlets and panels are an
  electrocution risk and the app should say so every time it mentions a basement during an event.
- The waiting period must never be presented in a way that implies coverage is available during
  an approaching storm. Frame it as a decision for a dry day.
- Mold and contaminated water are health issues; cite CDC/EPA and say when it is a professional
  job rather than describing a procedure.
- Photos and the damage log stay on the device. An insurance dispute is adversarial and the
  household's evidence should not sit on a third party's server.

=== HOW TO REPORT BACK ===

Lead with the three facts: the exact waiting period and its exceptions, the flood exclusion
language, and the sewer backup distinction — each with its source and date, and what the state
insurance department told you by phone. Then: whether FEMA's zone data was usable; the EXIF test
results; the measured emergency-screen load; and everything you could not verify.
```

---

## Why it's shaped this way

**The waiting period is the hero fact and it's rendered as a date.** "Thirty days" reads as
trivia; "if you buy today, coverage starts around [date]" reads as a deadline. The entire
purchase decision has to happen on a dry day, and the framing is what makes that land.

**The sewer backup distinction is the most useful thing in the app.** Water coming up the floor
drain is the most common basement loss, flood insurance typically doesn't cover it, and the fix
is a cheap endorsement almost nobody has been told about. Two policies, two different gaps, and
most people believe they have neither problem.

**"Not in a flood zone" is treated as a risk factor, not reassurance.** A large share of claims
come from outside mapped high-risk areas, and the maps don't model heavy-rain street flooding or
sewer surcharge at all. The zone lookup exists mostly to deliver that caveat.

**Life safety sits above everything on the emergency screen** because most flood deaths involve
vehicles in moving water, and because someone opening that screen is not in a state to read past
a paragraph of context.

**Photograph before you touch anything** is the whole damage log. Adjusters ask for
before-mitigation documentation, homeowners start bailing immediately, and the twenty minutes of
inventory on a dry day is what makes the claim work months later.

**Before you build:** call your state insurance department's consumer line and ask them to state
the waiting period and the backup-endorsement distinction. They answer this all day and they will
correct your wording.
