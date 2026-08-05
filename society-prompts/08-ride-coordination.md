# 08 — Volunteer Ride Coordination

**What it is:** Scheduling for volunteer drivers taking neighbors to medical appointments. The
hard part isn't the calendar — it's that a failed ride means a person sitting alone outside a
dialysis clinic at 6pm, and the system must make that structurally almost impossible.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[TIMEZONE]`, `[LANGUAGES]`,
`[ORG]` (the organization running the program — this project genuinely needs one; if you don't
have one, read the note at the bottom before pasting).

---

```text
You are building a volunteer medical-appointment ride coordination system for [ORG] in
[CITY], [COUNTY], [STATE]. Build it now; do not ask me clarifying questions. Where you need a
decision I did not make, choose the option that makes a stranded rider less likely, state your
choice, and keep going.

Read SAFETY + LEGAL before writing code. This project has real liability structure and the
architecture has to respect it.

=== THE PERSON ===

Willa is 71, [CITY], and gets dialysis Monday, Wednesday, Friday. Treatment runs about four
hours; she is exhausted and unsteady afterward. She does not drive. Her daughter takes her
when she can, which is about half the time. The rest is a patchwork: a neighbor, a paratransit
service she has to book three days ahead that arrives inside a two-hour window, and once, a
$46 rideshare she could not afford.

When a ride falls through, she does not skip the appointment. She goes anyway, somehow, or she
misses treatment — and missing dialysis puts people in the hospital.

The second person is Tom, 68, retired, who would drive twice a week and has said so, and who
has never been asked in a way that fit his schedule.

The third is Priya, the volunteer coordinator at [ORG], who currently runs this on a
spreadsheet and a personal cell phone and is the single point of failure for the whole program.

=== THE PROBLEM, WITH A NUMBER ===

Missed medical appointments due to transportation are a well-documented access barrier,
concentrated in older adults, people with disabilities, and low-income households; look up the
current figures and cite them with a year rather than displaying an unsourced statistic.

The operational problem is narrower: a volunteer program has more capacity than it can
schedule, because matching is manual, confirmations are unreliable, and one dropped ride burns
the rider's trust for months.

=== BEFORE YOU BUILD THE SCHEDULER: THE FEATURE THAT MATTERS MOST ===

Build this first. It is one screen and it may help more people than the rest of the system.

Many riders are entitled to transportation they don't know exists:
- Medicaid covers non-emergency medical transportation (NEMT) as a benefit in every state,
  administered differently in each. Most eligible people have never heard of it.
- Medicare Advantage plans frequently include a transportation benefit.
- Dialysis centers, cancer centers, and large hospital systems often have their own transport
  or contracts.
- Area Agencies on Aging, and many faith and civic organizations, run existing programs.
- Paratransit under the ADA is available to people whose disability prevents fixed-route
  transit use, within 3/4 mile of a bus route.

Build /other-options: a researched, cited, [STATE]- and [COUNTY]-specific page listing each
one with who qualifies, the phone number to call, what to ask for, and the date you verified
it. Show it to every new rider during intake, before offering a volunteer ride. Sending a
rider to a benefit they're already entitled to is a better outcome than scheduling a volunteer,
and it frees the volunteer for someone with no other option. Verify every phone number by
calling it.

=== BUILD THIS ===

1. RIDER INTAKE — Done by phone with a coordinator, not self-service. Priya fills the form
   while talking. Fields: name, phone, address, preferred language, mobility needs (walks
   independently / uses a cane or walker / uses a wheelchair — folding or not / needs help to
   the door / needs someone to stay during the appointment), whether they can be left at the
   curb, oxygen or equipment, cognitive considerations, emergency contact, and any other
   transportation they're eligible for from /other-options.
   Mobility is not a checkbox. A driver arriving in a two-door sedan for a non-folding
   wheelchair is a failed ride, so store it as structured fields and use it in matching.

2. RIDE REQUEST — Recurring rides are the primary case, not the exception. Willa's dialysis is
   M/W/F for the next six months. Build recurrence first:
   - Appointment address, arrival time, expected duration or "call when done"
   - Recurrence rule with an end date, plus per-instance exceptions (holidays, a changed week)
   - Return trip is a separate leg with its own driver assignment — this is essential, because
     the return is where rides fail. The rider is tired, the clinic runs late, and the driver
     who dropped them off is gone.
   - "Wait during appointment" vs "come back" vs "different driver returns"

3. DRIVER PROFILES — name, phone, vehicle (make, doors, trunk, whether a folding wheelchair
   fits, whether they can assist a rider physically), service area, recurring availability by
   weekday and time block, blackout dates, languages, background check status and expiry,
   insurance verification status and expiry, orientation completion date.
   A driver whose background check or insurance verification has expired CANNOT be assigned.
   Enforce it in the database, not the UI. Write the test.

4. MATCHING + OFFERS — Never auto-assign. Offer.
   - Rank eligible drivers by: availability match, vehicle compatibility with mobility needs,
     proximity to the rider, prior rides with this rider (continuity matters enormously to
     older riders — the same face is a feature), and load balancing so nobody burns out.
   - Send offers by text with the details minus the rider's exact address: date, time, general
     area, duration, mobility needs. Full details on acceptance.
   - Offer to 3 drivers at once for a ride more than 72 hours out; sequentially, 10 minutes
     apart, for anything sooner.
   - First acceptance wins, enforced by a unique constraint on the assignment.
   - For recurring rides, offer the whole series and let a driver take all of it or specific
     dates. A driver who commits to Mondays for three months is worth more than twelve
     one-off matches.

5. THE CONFIRMATION LADDER — This is the core safety system. Build it carefully; it's what
   prevents a stranded rider.
   - T-48h: driver gets "You have a ride Wednesday 8:15am. Reply C to confirm or X to cancel."
   - T-24h: unconfirmed drivers get a second text. Still unconfirmed at T-20h, the ride goes
     to the coordinator's URGENT list and re-offers to backups automatically.
   - T-12h: rider gets a reminder with the driver's name and vehicle.
   - T-2h: driver gets the address and phone. Rider gets "Tom is picking you up at 8:15 in a
     blue Camry."
   - T-0: driver taps "picked up" — one tap, from the text link, no login.
   - The return leg gets its own ladder, with a check at appointment end time + 30 minutes:
     if the return driver hasn't marked "picked up," the coordinator is alerted immediately by
     phone call, not email. A rider waiting is an emergency, not a notification.
   - Any cancellation at any stage instantly re-offers and alerts the coordinator.

6. COORDINATOR DASHBOARD — Priya's screen. Today's rides with status, unconfirmed rides sorted
   by urgency, unfilled requests, and a big red section for anything currently at risk.
   Everything doable in two clicks: reassign, call the rider, call the driver, cancel with a
   reason. She is on the phone while using this; do not make her navigate.

7. FALLBACK — Every ride record carries the rider's backup plan, captured at intake: a family
   member's number, the paratransit booking number, or, explicitly, "none." Rides with no
   backup are flagged in matching and get offered earlier and wider. When a ride truly cannot
   be filled, the coordinator gets the rider's fallback options on screen with phone numbers,
   and calls them — the system's last act is to make the human call easy, not to send an
   automated apology.

=== DATA MODEL ===

riders: id, name, phone, address, lat, lng, language, mobility jsonb, needs_door_to_door bool,
  can_be_left_at_curb bool, equipment text[], emergency_contact_name, emergency_contact_phone,
  backup_plan, other_benefits_checked bool, active, created_at, notes
drivers: id, name, phone, email, vehicle jsonb, service_area_radius_m, home_lat, home_lng,
  can_assist_physically bool, wheelchair_capacity enum, languages text[],
  background_check_status, background_check_expires, insurance_verified_on,
  insurance_expires, orientation_completed_on, active, max_rides_per_week
availability: id, driver_id, weekday, start_time, end_time
blackouts: id, driver_id, start_date, end_date, reason
ride_series: id, rider_id, rrule, start_date, end_date, destination, arrival_time, notes
rides: id, series_id|null, rider_id, leg enum(outbound|return), scheduled_pickup_at,
  pickup_address, dropoff_address, status enum(unfilled|offered|assigned|confirmed|
  en_route|picked_up|completed|canceled|failed), created_at
assignments: id, ride_id UNIQUE, driver_id, offered_at, accepted_at, confirmed_at,
  picked_up_at, completed_at, canceled_at, cancel_reason
offers: id, ride_id, driver_id, sent_at, responded_at, response
incidents: id, ride_id, kind, description, occurred_at, reported_by, resolved_at
mileage: id, assignment_id, miles, recorded_at

=== STACK ===

- Next.js 15 + TypeScript + PostgreSQL (Drizzle). One VPS.
- SMS: Twilio behind an `SmsProvider` interface with a console implementation; the whole system
  demoable with no credentials.
- Voice call for coordinator escalation: Twilio voice, or a documented manual fallback. A text
  is not sufficient for "a rider is waiting and nobody came."
- Scheduling: a durable job queue (pg-boss or equivalent) — the confirmation ladder is a set of
  scheduled jobs and it must survive a restart. Every ladder step is a persisted job with an
  idempotency key. A ladder that silently stops after a deploy is the failure mode that
  strands someone.
- Auth: coordinator and admin only, email magic link. Drivers and riders never log in —
  everything they do is a signed link from a text.
- Timezone [TIMEZONE] everywhere; test with a UTC server and across a DST boundary. A ride at
  8:15am the morning clocks change must be right.

=== HARD CONSTRAINTS ===

- Drivers and riders complete every action by replying to a text with one letter or tapping one
  link. No app, no login, no password.
- Coordinator dashboard must be usable on a phone; Priya is not at a desk.
- Every scheduled job is idempotent and persisted. Test by killing the process mid-ladder and
  restarting.
- DST correctness, tested explicitly in both directions.
- WCAG 2.2 AA on all surfaces. Rider-facing text at 18px minimum.
- [LANGUAGES] for every rider- and driver-facing message.
- Rider addresses, phone numbers, and mobility/health notes are sensitive. Encrypt at rest,
  restrict to authenticated coordinators, log every access to a rider record with who and when,
  and never include the rider's address in an offer message before acceptance.
- Data retention: ride records 3 years for insurance and reporting; then purge personal fields
  and keep aggregate counts.

=== DO NOT BUILD ===

- No rider self-service signup in v1. Intake is a conversation, because mobility needs captured
  wrong strand people, and the coordinator's judgment is a safety control.
- No payments, tips, fare splitting, or driver compensation processing. Volunteer drivers who
  receive compensation raise insurance and employment-classification questions this project
  must not create. Mileage is recorded for reimbursement reporting only, outside the app.
- No live GPS tracking of drivers. It is surveillance of volunteers, it will lose you drivers,
  and it does not prevent the failure you care about — the confirmation ladder does.
- No ratings or reviews of drivers or riders. Problems go to the coordinator as incidents.
- No public ride marketplace, no open driver signup without screening.
- No medical information beyond mobility and equipment needs. Do not record diagnoses. "Needs
  a wheelchair-accessible vehicle" is operational; "has congestive heart failure" is not yours.
- No emergency dispatch, no 911 integration, no medical transport. This is not an ambulance
  and the intake must screen out anyone who needs one.
- No AI matching. Six ranked criteria in SQL, reviewed by a human.

=== ACCEPTANCE TESTS ===

1. A driver with an expired background check cannot be assigned — enforced at the database
   layer, verified by attempting a direct insert.
2. A rider requiring a non-folding wheelchair is never offered to a driver whose vehicle cannot
   carry one.
3. Two drivers accepting the same offer simultaneously result in exactly one assignment.
4. A recurring M/W/F series for 12 weeks generates the correct ride instances including both
   legs, with the correct local time across a DST transition.
5. An unconfirmed ride at T-20h appears on the coordinator's URGENT list and triggers re-offers.
6. A return leg unmarked 30 minutes after expected appointment end triggers a coordinator
   phone-call escalation, not just a text.
7. Killing the worker process mid-ladder and restarting delivers all remaining steps exactly
   once.
8. An offer message contains no rider address, name, or phone; the acceptance message does.
9. A cancellation at any stage re-offers immediately and notifies the coordinator.
10. Every read of a rider record writes an access log row.
11. All rider- and driver-facing messages render in the recipient's language.
12. With TWILIO_* unset, the entire flow completes against the console provider.
13. Riders with backup_plan = "none" are ranked ahead of others in offer urgency.
14. /other-options renders for [STATE] with every phone number and a verified_on date.

=== MILESTONES ===

M0 — /other-options, verified by phone.
  EXIT: you have personally called every number on it and confirmed the program exists and
  what it requires. This is real work and it is the highest-value hour in the project.

M1 — Intake, ride requests, manual assignment, coordinator dashboard.
  EXIT: Priya runs one real week off the dashboard instead of the spreadsheet.

M2 — Offers and the confirmation ladder, console SMS.
  EXIT: acceptance tests 1-9 pass, including the process-kill test.

M3 — Real SMS + recurrence + escalation.
  EXIT: one real recurring rider completes two weeks with zero missed rides, and you can show
  the ladder's message log for each.

M4 — Six drivers, five riders, one month.
  EXIT: report the number of rides requested, filled, confirmed, and failed. The failure count
  is the number that matters; if it isn't zero, find out why each one happened.

=== SAFETY + LEGAL ===

This section is not boilerplate. Volunteer driver programs carry real exposure and [ORG] must
have these in place before the first ride. Build the software to require them.

- DRIVER SCREENING: motor vehicle record check, a criminal background check appropriate to
  working with vulnerable adults under [STATE] law, proof of a valid license, and proof of
  personal auto insurance at or above [ORG]'s required limits. Store status and expiry; block
  assignment on expiry. Research whether [STATE] has volunteer driver protections or
  requirements and record what you find in the README.
- INSURANCE: in a volunteer driver arrangement, the driver's personal auto policy is generally
  primary, and the sponsoring organization typically carries non-owned auto liability coverage
  on top. [ORG] must confirm its coverage with its insurer before the first ride. Put this in
  the README as a launch blocker, and do not treat this brief as insurance advice — [ORG]'s
  insurer decides.
- LIABILITY WAIVERS: riders and drivers sign [ORG]'s forms during intake and orientation.
  Track completion; block assignment without it. The forms come from [ORG]'s counsel, not
  from you.
- SCOPE: this is not medical transport. Intake must screen for anyone requiring stretcher
  transport, medical monitoring, or emergency care, and route them to the appropriate service.
  Put that screening question in the intake form, in bold, with the numbers to call.
- MANDATORY REPORTING: drivers may be the only person who sees a rider's living conditions
  weekly. [STATE] likely has elder abuse and vulnerable adult reporting requirements. Include
  guidance in driver orientation materials and an incident-reporting path in the app that
  routes to the coordinator immediately, not to a queue.
- DRIVER SAFETY TOO: drivers must be able to report an unsafe situation and decline future
  rides with a specific rider without explaining themselves publicly. Build that path.
- PRIVACY: a rider's address plus a dialysis schedule is a vulnerability profile. Access
  logging, encryption at rest, no address in pre-acceptance messages, no public data, no
  analytics.
- Never display any statistic you have not sourced with a year.

=== HOW TO REPORT BACK ===

Tell me: what you verified about [STATE]'s volunteer driver rules and screening requirements;
which numbers on /other-options you confirmed by phone; the results of the process-kill and
DST tests; and everything you could not verify. Flag anything that should block launch until
[ORG] confirms it with their insurer.
```

---

## Why it's shaped this way

**`/other-options` comes before the scheduler** because the highest-value outcome is often that
the rider was already entitled to covered transportation and nobody ever told them. Medicaid
NEMT exists in every state and awareness is poor. A volunteer program that routes people to
benefits they already have serves more riders and preserves volunteer capacity for those with
no alternative.

**The return leg is a separate ride with its own confirmation ladder** because that's where the
failure happens. Outbound is easy — the rider is rested, the time is known. The return is
uncertain, the rider is depleted, and a system that treats a round trip as one unit will
regularly leave someone at a curb.

**Durable, idempotent scheduled jobs** are load-bearing, not an implementation detail. The
confirmation ladder *is* the safety system, and an in-memory timer that dies on deploy fails
silently and strands someone. The process-kill test is the one to actually run.

**No GPS tracking, no ratings.** Both feel like obvious features. Both drive away the volunteers
this depends on, and neither prevents the failure mode. Confirmations do.

**On needing a partner org:** unlike the others in this kit, this one genuinely should not be
run solo. The screening, insurance, and waiver structure requires an organization with
liability coverage. If you don't have one, the right move is to take `/other-options` and the
confirmation ladder design to an Area Agency on Aging, a senior center, or a faith
congregation already doing this on paper — and build it for them.
