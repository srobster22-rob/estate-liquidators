# 13 — Wage Theft Record + Claim Builder

**What it is:** A worker logs their real hours on their phone as they work them, compares that
record to what the paycheck actually paid, and ends up with a documented claim — the hours, the
math, the difference, and the completed state wage claim form.

**Fill in before pasting:** `[STATE]`, `[STATE_ABBR]`, `[CITY]`, `[LANGUAGES]` (for most places
in the US this should include Spanish; research what else [CITY] needs).

---

```text
You are building a wage and hour documentation tool for workers in [STATE]. Build it now; do
not ask me clarifying questions. Where you need a decision I did not make, choose the option
that produces a record a labor agency would accept, state your choice, and keep going.

Read SAFETY + LEGAL before writing code. Retaliation risk shapes the architecture.

=== THE PERSON ===

Beatriz works at a restaurant in [CITY]. She clocks in at 3:30 and is told to start setting up
at 3:15. She stays past clock-out to finish cleaning, twenty minutes most nights. Some weeks
she works 46 hours and the check shows 40 at straight time. When she asked, the manager said
the system rounds and it evens out.

She has no records. The employer has the timeclock. She has a phone, a stack of paper stubs in
a drawer, and a memory of most weeks being like this for about eight months.

The second person is Danny, classified as an independent contractor, paid a flat day rate,
working twelve-hour days on someone else's schedule with someone else's tools. Nobody has ever
said the word overtime to him.

Both are afraid of losing the job. That fear is not irrational and the app must not pretend
it is.

=== THE PROBLEM, WITH A NUMBER ===

Wage theft — unpaid overtime, off-the-clock work, illegal deductions, tip violations,
misclassification, minimum wage violations — is measured in billions annually and concentrates
in low-wage industries. Look up a current figure from a named study with a year before
displaying one; do not display an unsourced number.

The operational problem is evidentiary. The employer holds the time records. A worker with no
contemporaneous record of their own is arguing memory against paperwork. A worker who logged
their hours daily, on their own device, from the first week, is in a completely different
position.

Research and cite the actual rule in [STATE] and under federal law about what happens when an
employer's records are inadequate or missing — there is well-established law on the employee's
burden in that situation, and it is favorable. Verify it from a primary source and state it
accurately in the app, because it is the single fact that makes daily logging worth doing.

=== WHAT SUCCESS LOOKS LIKE ===

Beatriz opens the app twice a day for four weeks. At the end she has: 28 days of logged
shifts, photos of four pay stubs, a computed difference of $612.40 with the arithmetic shown
line by line, and a filled-out [STATE] wage claim form. Whether she files it, shows it to a
lawyer, or shows it to her manager, the record exists.

=== BUILD THIS ===

1. LOG A SHIFT — The daily loop, and it must take under 20 seconds or she will stop.
   - A big "Start work" / "Stop work" button on the home screen. One tap each.
   - Time is editable after the fact — she will forget and log it at home that night. Editing
     creates a corrected entry, not a silent overwrite (see the immutability rule below).
   - Per shift: start, end, unpaid break start/end (multiple), what she did, where, and
     "off-the-clock work" as an explicit flag with a note. That flag is the whole product for
     Beatriz's situation: work performed before clock-in or after clock-out.
   - Quick entry for a whole past week, because the first thing a new user wants to do is
     reconstruct the last month. Make reconstruction possible and label those entries as
     reconstructed rather than contemporaneous. That distinction matters to an investigator and
     the app should be honest about it.
   - Optional: attach a photo of the schedule, the timeclock screen, a text from a manager
     telling her to come in early. Preserve EXIF DateTimeOriginal; see the evidence rules.

2. LOG A PAYCHECK — Photo of the stub plus the numbers typed in: pay period start and end,
   hours paid at regular rate, hours paid at overtime rate, rate(s), gross, each deduction
   itemized, tips reported, net. Typing them is fine; do not build OCR in v1.

3. THE COMPARISON — The screen that turns logs into a claim. Per pay period:
   - Hours you logged vs hours you were paid, side by side, with the difference in bold
   - Overtime hours you logged (over the applicable threshold) vs overtime hours paid
   - Effective hourly rate: gross divided by hours actually worked, compared against the
     applicable minimum wage — this catches the flat-rate and salaried-misclassification cases
     that hour-counting alone misses
   - Each deduction, with a note on which categories of deduction [STATE] restricts
   - The computed difference, with every step of the arithmetic shown and printable
   Never a single number without its derivation. An unexplained "$612.40" is unusable in a
   claim; "46 hours logged, 40 paid, 6 hours × $19.50 overtime rate = $117.00 this period" is
   evidence.

4. THE RULES ENGINE — as dated, sourced JSON in /rules/[STATE_ABBR]/, never as code:
   - Federal and [STATE] minimum wage, and [CITY]'s if it has its own — many cities do, and
     the highest applicable one governs
   - Overtime threshold and multiplier for [STATE]. Most states follow the federal 40-hour
     week; a few also require daily overtime. Verify [STATE] specifically.
   - Meal and rest break requirements for [STATE], including whether breaks are paid and what
     the penalty is for a missed break — some states pay a premium hour
   - Tip rules: whether [STATE] permits a tip credit, tip pooling limits, and the rule against
     managers sharing in tips
   - Deduction restrictions: uniforms, walkouts, register shortages, tools
   - Statutes of limitations, federal and state, with the exact periods
   - Which agency takes a claim in [STATE], its form number, its filing deadline, and whether
     filing with the state affects federal rights
   Every rule file carries effectiveFrom, a source URL, a retrieval date, and its own test
   cases. Verify every number from a primary source — the state labor department and the US
   DOL — and ship no rule you could not verify. Minimum wages change on January 1 in many
   states and on July 1 in some cities; the stale-data banner is mandatory.

5. THE CLAIM PACKET — Export a PDF:
   - Cover summary: employer, dates, total claimed, categories of violation
   - The full shift log as a table
   - The pay period comparison with all arithmetic
   - Photos of stubs and evidence with their timestamps
   - A methodology page stating exactly how each number was computed and which rule version
     was applied
   Plus: [STATE]'s actual wage claim form, pre-filled where the app has the data, as a separate
   file. Research the current form, verify the version, and if you cannot obtain or fill it
   reliably, link it and pre-fill a companion sheet instead of generating a form that might be
   the wrong version.

6. KNOW WHAT YOU'RE OWED — A short reference page, plain language, [STATE]-specific, each claim
   cited: what counts as compensable work time (donning gear, opening duties, travel between
   sites, required training, waiting time), what misclassification means and the tests used for
   it, what happens to a claim if you quit or are fired, the fact that immigration status does
   not determine coverage under wage and hour law — verify this and state it precisely and with
   citation, because it is the reason many workers never file — and the retaliation protections
   in [STATE] with their deadlines.

=== DATA MODEL (local only) ===

employers: id, name, address, manager_name, ein_if_known, pay_frequency, stated_rate,
  classification enum(employee|contractor|unsure), start_date, end_date
shifts: id, employer_id, date, start_time, end_time, breaks jsonb, off_clock_minutes,
  off_clock_note, work_description, location, entry_mode enum(live|same_day|reconstructed),
  created_at, seq, content_hash, prev_hash
paychecks: id, employer_id, period_start, period_end, pay_date, regular_hours_paid,
  overtime_hours_paid, regular_rate, overtime_rate, gross, deductions jsonb, tips, net,
  stub_photo_ref
evidence: id, shift_id|paycheck_id|employer_id, kind, blob_ref, sha256,
  exif_datetime_original|null, exif_present bool, import_time, note
computations: id, employer_id, period_start, period_end, rule_version, inputs jsonb,
  steps jsonb, amount_owed_cents, computed_at

Shift entries follow the same immutability and hash-chain rules as project 03: an edit creates
a correction entry with both visible, and each entry stores the prior entry's hash. The value of
a contemporaneous log is that it is contemporaneous; an editable-in-place log is worth much
less, and the app should be able to demonstrate the difference.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB, offline-capable, installable.
- NO BACKEND. No account. No sync. Export is the backup, and the app nags for one once there
  are more than five shifts and no export has ever been made.
- Hashing via Web Crypto. EXIF via a library you verify against real phone photos.
- PDF via pdf-lib, client-side.
- Rules validated by Zod at build time; a malformed or unsourced rule fails the build.
- Under 200KB JS gzipped.

=== HARD CONSTRAINTS ===

- Logging a shift start or end must take one tap from the home screen, with the app cold.
- Works fully offline. Restaurant basements and job sites have no signal.
- All money computed in integer cents. Never floating point. Test the rounding rule you choose
  and document it — an off-by-a-penny in a claim is an argument you do not want to have.
- Time zone: store local wall-clock time with an explicit zone; a shift that crosses midnight
  or a DST boundary must compute correct duration. Test both directions.
- WCAG 2.2 AA. One-handed, large targets, works with wet or gloved hands — this is used in a
  kitchen, on a site, in a car.
- Reading level 6th grade. [LANGUAGES] from the first commit, professionally reviewed.
- No network requests to anything, ever, after the app caches. Assert it in a test.
- Discreet by design: a PIN or biometric lock option, an unremarkable app name and icon, and a
  fast way to close it. See SAFETY.

=== DO NOT BUILD ===

- No cloud account, no sync, no "share with an advocate" server feature. Export a file.
- No employer-facing anything. No sending, no notifying, no submitting to any agency on the
  worker's behalf.
- No GPS tracking or geofenced auto clock-in. It is surveillance, it drains the battery, and a
  location log of a worker's day is a liability to them, not an asset.
- No public database of employers, no reviews, no "worst employers" list. Defamation exposure,
  and it turns a private evidence tool into a target.
- No LLM in the computation path. Every dollar traces to a cited rule and shown arithmetic.
- No legal argument generation. Facts, math, and citations.
- No union organizing features in v1 — a different project with different legal considerations
  and different security requirements.
- No integration with any payroll or timeclock system.

=== ACCEPTANCE TESTS ===

1. Start and stop a shift with two taps from a cold app launch.
2. A shift crossing midnight computes the correct duration; so does one crossing a DST boundary
   in both directions.
3. All monetary math is in integer cents; a property test over random hour/rate combinations
   shows no floating-point drift.
4. Overtime computes correctly at the [STATE] threshold, including a week with a paid holiday
   and a week with unpaid breaks deducted.
5. The effective-rate check flags a flat-rate week that falls below the applicable minimum wage.
6. The highest of federal, state, and city minimum wage is the one applied — test with three
   different values.
7. Editing a saved shift creates a correction entry; the original remains with its hash intact.
8. Tampering with a stored entry causes the chain check to report a break at that entry.
9. Every rule file has a source URL, retrieval date, and passing embedded tests; one missing
   any of these fails the build.
10. A rule past its effectiveTo renders the stale banner and logs a startup warning.
11. Reconstructed entries are labeled distinctly from contemporaneous ones in the app and in
    the exported packet.
12. The exported packet shows every arithmetic step for every period.
13. Zero network requests during a complete journey, verified by an intercepting test.
14. A photo with EXIF capture time shows that time; one without shows "no camera timestamp."
15. All strings present in every language in [LANGUAGES].

=== MILESTONES ===

M0 — Shift logging, offline, one tap.
  EXIT: log your own shifts for a week. If you skipped days, the interaction is too slow —
  fix that before anything else.

M1 — Paycheck entry + the comparison + the rules engine for [STATE].
  EXIT: hand-verify six pay periods against the state and federal rules. Show your work.

M2 — The claim packet + the [STATE] form.
  EXIT: a worker center organizer, legal aid employment attorney, or state labor agency
  intake worker reviews a generated packet and tells you whether they could act on it. Do not
  skip this gate. It will change the packet substantially.

M3 — Second language, evidence attachments, hash chain.
  EXIT: a native speaker reviews the translation. Not a machine.

M4 — Three real workers, one month.
  EXIT: report how many logged consistently and where the drop-off happened. Consistency is
  the only metric; a beautiful app used for four days produces no claim.

=== SAFETY + LEGAL ===

- Not legal advice. On the home screen and every generated document: "This tool helps you keep
  records and do the math. It is not a lawyer. Free help in [CITY]: <worker center / legal aid,
  phone>." Research and name a real organization.
- RETALIATION IS THE CENTRAL RISK. Firing, cutting hours, and threats are illegal responses to
  a wage complaint under federal and most state law, and they still happen. Before any screen
  that encourages filing, show one screen explaining the protections in [STATE] with citations,
  their limits, and their deadlines — and make clear that the decision to file is the worker's
  alone. Never nudge toward filing. A worker who logs for six months and files after leaving
  the job is using this tool correctly.
- IMMIGRATION STATUS: verify and state accurately that federal and state wage and hour
  protections generally apply regardless of immigration status, cite the source, and link to an
  immigration legal aid organization. This is the fear that keeps the most people from filing.
  If you cannot verify the current state of this from a primary source, write only "Talk to a
  worker center or an employment lawyer about your specific situation" and link them — do not
  guess.
- DEVICE SECURITY IS WORKER SAFETY. The threat model includes an employer or a supervisor
  looking at the phone. PIN lock, no notifications that reveal content on the lock screen, no
  distinctive icon, quick exit. No server means nothing to subpoena from you.
- Statutes of limitations are hard deadlines and every day of delay can cost a day of claim.
  Display the applicable deadline prominently with its source, computed from the earliest
  logged shift, and update it as time passes. Cite where the period comes from and say plainly
  that only a lawyer or the agency can tell them how it applies to their case.
- Never tell a user their claim is strong or weak, or estimate what they will recover. Show
  the hours, the rule, and the arithmetic.

=== HOW TO REPORT BACK ===

Tell me: every wage rule you verified with its source URL and date; what [STATE]'s claim form
is and whether you could fill it reliably; the results of the DST, midnight, and integer-cents
tests; what the M2 reviewer said; and everything you could not verify.
```

---

## Why it's shaped this way

**Twenty seconds a day is the whole design constraint.** Everything else is downstream. A
worker who logs consistently for a month has a claim; one who logs for four days has an
anecdote. Every feature that adds friction to the daily loop costs more than it adds.

**Contemporaneous versus reconstructed is labeled honestly** because the distinction matters to
an investigator and pretending otherwise damages the record. Reconstruction is still worth
doing — most people arrive after months of the problem — but it should be marked as what it is.

**The effective-rate check catches what hour-counting misses.** Danny's flat day rate looks fine
until you divide gross by hours actually worked and compare it against minimum wage. That single
computation covers the misclassification and salaried-abuse cases that a pure timesheet app
never sees.

**No GPS auto-clock-in**, which is the first feature anyone proposes. A minute-by-minute
location history of a worker's day is a liability to that worker, sitting on a device an
employer may demand to see.

**Integer cents and a documented rounding rule** because this arithmetic ends up in an agency
filing, and a penny of drift is a credibility argument you don't want to have on top of the
real one.

**Before you build:** find the worker center or legal aid employment unit in [CITY] and ask what
a claim packet needs to contain. They process these; they will tell you exactly what's missing
from yours.
