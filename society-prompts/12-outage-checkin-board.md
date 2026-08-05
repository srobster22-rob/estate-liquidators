# 12 — Outage / Disaster Check-In Board

**What it is:** The ice storm took the power out four days ago. This is a 15KB page and a text
number where neighbors say "I'm OK," say what they need, say what they have, and find out which
building has heat — on a dying phone with one bar.

**Fill in before pasting:** `[NEIGHBORHOOD]`, `[CITY]`, `[COUNTY]`, `[STATE]`, `[TIMEZONE]`,
`[LANGUAGES]`, `[ORG]` (neighborhood association, CERT team, congregation, or "no host yet").

---

```text
You are building a neighborhood check-in and mutual aid board for [NEIGHBORHOOD] in [CITY],
for use during power outages, storms, heat events, and similar disruptions. Build it now; do
not ask me clarifying questions. Where you need a decision I did not make, choose the option
that works on the worst phone with the worst connection and the least battery, state your
choice, and keep going.

Read SAFETY + LEGAL before writing code. This project has one boundary it must never cross and
one privacy tension that shapes the entire data model.

=== THE PEOPLE ===

Day four of an ice storm. Power is out across [NEIGHBORHOOD].

Ruth is 79, alone, has a landline that is dead and a cell phone at 12%. She is cold. She has
not spoken to anyone in two days. She is not going to install anything.

Marcus has a generator, a working truck, and no idea who needs either.

Priya coordinates for [ORG] and is trying to figure out who has not been heard from — which is
the single question that matters in an outage, because the person who has not checked in is
the person to go knock on.

The cell network is congested. Data is slow and intermittent. SMS still gets through, because
it usually does when data doesn't. Everyone's battery is the binding constraint.

=== THE PROBLEM, WITH A NUMBER ===

In sustained outages and extreme weather, the deaths are overwhelmingly among people who are
old, alone, medically dependent on power, or without transportation — and they are usually
found late. The operational failure is not a lack of willing neighbors. It is that nobody has
a list of who to check on and no way to know who has already been checked.

Look up [STATE]'s or [COUNTY]'s after-action reports from the last major outage or storm and
cite what they found; the specifics will sharpen this project more than any general statistic.

=== WHAT SUCCESS LOOKS LIKE ===

By hour 30, Priya has a list of eleven households not heard from, three of them flagged at
signup as medically vulnerable. Volunteers knock on all eleven. Ruth's is the fourth door.

=== THE PRIVACY TENSION — DECIDE THIS BEFORE YOU DESIGN ===

A public board saying "79-year-old woman alone at 412 Elm, no power, needs help" is a map for
burglary and worse, published at the moment a neighborhood is least able to respond. This is
not hypothetical; it is a documented pattern after disasters.

The resolution, and it is not negotiable in this design:

- PUBLIC, with no login: which locations are open (warming/cooling/charging/water), general
  status of the neighborhood, how to check in, how to volunteer, and offers of help that
  people explicitly chose to publish (see below).
- VOLUNTEER-VISIBLE ONLY, behind a coordinator-issued link: individual check-in statuses,
  needs, addresses, and the not-heard-from list.
- NEVER PUBLIC: any combination of address and vulnerability. Not on a map, not in an API
  response, not in a page the search engines can reach.
- Offers ("I have a generator," "I can drive") are public only if the offerer opts in, and
  even then default to block-level location, not an address, with contact through the
  coordinator.

Build this as an authorization boundary in the data layer, not as a UI decision. Write a test
that hits every public endpoint and asserts no address, phone number, or vulnerability flag
appears in any response.

=== BUILD THIS ===

1. THE PAGE (/) — Static HTML. Total transfer under 20KB including CSS. No JavaScript required
   for anything essential. Structure, in source order:
   - One line of current status for [NEIGHBORHOOD], with a timestamp in [TIMEZONE]
   - "Text OK to [number] to check in" — in large type, at the top, because that is the action
   - Open locations right now: name, address, what they have (heat / cooling / power to charge
     / water / restrooms / wifi), hours, whether pets are allowed
   - Emergency numbers: 911 first, then the utility's outage line, then [ORG], then 211
   - "I need help" and "I can help" links
   - Last updated, prominently
   It must render usefully with CSS entirely disabled. Write the HTML so the source order is
   the priority order.

2. SMS — The primary interface, because data may be unusable and SMS is cheap in battery and
   bandwidth. Support single-word commands, case-insensitive, forgiving of punctuation:
   - OK — check in as safe. Reply: "Got it. You're marked safe as of 3:42pm."
   - HELP — start a needs conversation: one question at a time, at most three questions, then
     "A volunteer will contact you. If this is an emergency, call 911."
   - OPEN — text back the two nearest open locations with addresses
   - HAVE — register an offer (generator, truck, chainsaw, spare room, water)
   - STATUS — the one-line neighborhood status
   - STOP — unsubscribe
   Every reply is under 300 characters. Every reply that could involve a life-safety situation
   ends with "If this is an emergency, call 911." Design for a person with 8% battery: fewest
   possible round trips.

3. SIGN UP BEFORE THE STORM — /signup, the feature that makes everything else work, and the
   one that must be promoted when nothing is happening. Fields: name, address, phone,
   languages, how many people in the household, whether anyone is medically dependent on
   electricity (oxygen concentrator, CPAP, refrigerated medication, powered mobility device),
   whether anyone has limited mobility, pets and livestock, a secondary contact, and whether
   they're willing to be checked on in person.
   The medical-dependency flag is the highest-value field in the entire system and it is also
   the most sensitive. It is visible to coordinators only, encrypted at rest, and it is why
   there is no public map.
   Also: many utilities maintain a medical baseline or critical-care customer registry. Tell
   people about it and link it — it may get their power restored sooner and it is not a
   substitute for this list, nor is this a substitute for it.

4. COORDINATOR VIEW — Priya's screen, behind a magic link. Three sections, in this order:
   - NOT HEARD FROM — everyone registered who has not checked in during the current event,
     sorted by vulnerability flags first, then by time since last contact. This is the whole
     product. Each row: name, address, phone, flags, secondary contact, and one tap to mark
     "assigned to <volunteer>" or "checked — OK" or "checked — needs follow-up."
   - OPEN NEEDS — requests, with status and assignment.
   - OFFERS — who has what.
   Works on a phone, offline-tolerant, and printable — because the coordinator's own power may
   be out and paper works at 0%.

5. EVENT MODE — A coordinator declares an event, which starts a check-in cycle: everyone
   registered gets one text asking them to reply OK, resent once after 6 hours to
   non-responders. Cycles have a defined window and clear open/close, so "not heard from" means
   something precise. Outside an event, the board shows a calm page with the signup link and
   the preparedness info.

6. PRINTED FALLBACK — Generate two printables:
   - A door hanger: "Checking on neighbors. Are you OK? Text OK to [number], or call [number].
     If you need help and can't reach anyone, put this card in your front window." Two-sided,
     [LANGUAGES], with a large ARE YOU OK / I NEED HELP card the resident can display.
   - A coordinator roster: every registered household with address, phone, and flags, sorted
     by street, printed on paper, in a binder, updated monthly.
   Paper is the only thing with 100% uptime. Say so in the README and make the printables good.

=== DATA MODEL ===

households: id, name, address, lat, lng, phone, alt_phone, languages text[], household_size,
  power_dependent_medical bool, medical_notes_encrypted, mobility_limited bool, pets text,
  secondary_contact_name, secondary_contact_phone, willing_in_person_check bool,
  registered_at, verified_at, active
events: id, name, kind, declared_at, closed_at, declared_by
checkins: id, event_id, household_id, status enum(ok|needs_help|no_response|checked_in_person),
  reported_at, channel, reported_by
needs: id, event_id, household_id, category, description, urgency, status, assigned_to,
  created_at, resolved_at
offers: id, household_id, category, description, public_ok bool, available_from,
  available_until, active
locations: id, name, address, lat, lng, capabilities text[], hours_text, pets_ok bool,
  phone, verified_on, verified_by, open_now bool
volunteers: id, name, phone, has_vehicle, capabilities text[], active, background_note
assignments: id, need_id|household_id, volunteer_id, assigned_at, completed_at, outcome
messages: id, household_id, direction, body, channel, sent_at, delivered

Encrypt medical_notes and treat power_dependent_medical as the most protected field in the
schema. Document the key management in the README, honestly, including its weaknesses.

=== STACK ===

- Static HTML for the public page, generated by a small build step, served from a host with
  very high availability plus a mirror on a second provider. The public page must survive your
  server being down — if the coordinator app is offline, the static page with locations and
  phone numbers still serves. Set a short cache TTL and long stale-while-revalidate so a cached
  copy remains useful during an outage.
- Backend: Node/TypeScript + PostgreSQL, one small VPS, hosted OUTSIDE the affected region.
  Do not host the disaster tool for [CITY] in a datacenter in [CITY].
- SMS: Twilio, behind an `SmsProvider` interface with a console implementation. Test what
  happens under carrier congestion and queue with retries and idempotency keys.
- Service worker on the public page caching locations and numbers, so a phone that loaded it
  once has it during the outage. This is a genuine offline requirement, not a nicety.
- Coordinator app: server-rendered, minimal JS, works on a phone, prints cleanly.
- No dependency on any service inside the affected area. No dependence on data connectivity for
  the critical path.

=== HARD CONSTRAINTS ===

- Public page under 20KB total transfer, no JS required, renders with CSS disabled. Measure
  and report the real byte count.
- Every SMS reply under 300 characters, no more than one round trip per user action where
  possible. Battery is the scarcest resource in the neighborhood.
- The system must be usable by a coordinator with no power, from a printed roster, and the
  printed roster must be current — build the print export as a first-class feature, not an
  afterthought.
- No public endpoint returns an address, phone number, medical flag, or precise coordinate.
  Tested.
- [LANGUAGES] on the page, in every SMS, and on the printables.
- WCAG 2.2 AA. 20px minimum body text on the public page; assume cold hands and poor light.
- All times in [TIMEZONE] with explicit "as of" stamps everywhere.
- Data retention: check-in and needs data purged 90 days after an event closes; the household
  registry persists until someone asks to be removed, with an annual re-consent prompt.

=== DO NOT BUILD ===

- No 911 replacement, no emergency dispatch, no medical triage, no "how urgent is this"
  scoring. See SAFETY.
- No public map of individuals. No public list of who needs help. No API that exposes either.
- No real-time chat, forums, or comment threads. They fill with rumor in an emergency, they
  need moderation nobody has capacity for during an actual disaster, and they consume battery.
- No damage reports, insurance documentation, or photo uploads in v1.
- No integration with utility outage APIs in v1 — they fail or rate-limit precisely during
  large outages, which is when you need them. Link the utility's page instead.
- No native app, no push notifications. SMS.
- No account passwords for residents. Phone number identity, coordinator magic links.
- No AI anything. Under congestion, every dependency is a failure mode.
- No donation collection, no fundraising, no payments.

=== ACCEPTANCE TESTS ===

1. Public page total transfer under 20KB; renders correctly with JavaScript disabled and with
   CSS disabled.
2. No public endpoint or page returns an address, phone number, medical flag, or precise
   coordinate — assert against every public route, including any JSON.
3. Texting "ok", "OK.", " Ok " all check in successfully and return a confirmation under 300
   characters.
4. Texting "HELP" collects at most three answers and every reply includes the 911 line.
5. Declaring an event texts every active household exactly once, and re-texts only
   non-responders after 6 hours.
6. The not-heard-from list sorts households with medical dependency flags first.
7. The coordinator roster prints legibly, sorted by street, on standard paper.
8. With the backend fully down, the cached public page still displays open locations and phone
   numbers.
9. SMS sends are idempotent under retry — a duplicate delivery attempt does not send twice.
10. All resident-facing messages render in the household's chosen language.
11. Medical notes are encrypted at rest — verify by inspecting the raw database.
12. Purging an event removes check-ins and needs while preserving the household registry.
13. axe-core clean on public and coordinator views.
14. With TWILIO_* unset, a full event cycle runs against the console provider.

=== MILESTONES ===

M0 — Public static page + open locations, hand-maintained.
  EXIT: it loads on a phone at one bar in under 2 seconds, and is legible outdoors in winter
  light with gloves on. Test that literally.

M1 — Signup + SMS check-in + coordinator not-heard-from list.
  EXIT: 10 real households registered and a test event run end to end with real texts.

M2 — Needs, offers, assignment, printables.
  EXIT: [ORG] runs a tabletop drill using only the printed roster, with the laptop closed.

M3 — Event mode, second-language support, mirrored hosting.
  EXIT: the public page still serves with the primary backend deliberately switched off.

M4 — A real event, or a full drill.
  EXIT: report registered households, check-in rate, not-heard-from count, and how long it
  took to physically reach everyone on that list. That last number is the project's real
  scoreboard.

=== SAFETY + LEGAL ===

- THE BOUNDARY: this is not an emergency service. It never dispatches, never triages, never
  advises on medical urgency, and never delays a 911 call. Every needs interaction — SMS and
  web — leads with "If this is an emergency, call 911." Put it in code as a required element of
  those message templates, and write a test asserting it is present.
- Do not create the impression that checking in summons help. Copy must be exact: "This tells
  your neighbors you're OK. It does not call anyone for you."
- Volunteer safety: two-person door knocks, daylight where possible, no entering homes, and a
  documented procedure for what to do when there's no answer or something looks wrong — which
  is to call [ORG]'s coordinator and, if there is reason to think someone is in danger, call
  for a welfare check. Put that procedure in the volunteer materials and in the app.
- The registry is a list of vulnerable people with addresses. Treat it accordingly: encryption
  at rest, access limited and logged, no public exposure, no export feature for
  non-coordinators, no analytics, no third-party services touching it. Document who has access
  and how that's revoked.
- Get explicit consent at signup for what's stored, who sees it, and how it's used, in plain
  language, in [LANGUAGES]. Offer removal at any time, honored immediately.
- Coordinate with [CITY]'s emergency management office and with [COUNTY]'s CERT program before
  an actual event. An unaffiliated volunteer system operating during a declared emergency can
  create real friction with official response; being known in advance prevents that and often
  gets you their location list.
- Check whether [STATE] has volunteer liability protections and whether [ORG] carries
  appropriate coverage. Note it in the README as a launch item, not as advice.
- Rumor control: because there is no chat, the page carries only verified information. State
  on the page who verifies it and when it was last checked.

=== HOW TO REPORT BACK ===

Tell me: the measured byte weight of the public page; the results of the public-endpoint
privacy test; what happened in the tabletop drill; the SMS round-trip count per action; and
everything you could not verify. If [CITY] emergency management said something that changes the
design, lead with that.
```

---

## Why it's shaped this way

**"Who have we not heard from" is the entire product.** Everything else — needs, offers,
locations — is useful. But in a sustained outage, the deaths are people found late, and the only
way to find them early is a list of everyone and a record of who has been contacted. That's a
database of names and a check-in log, which is unglamorous and lifesaving.

**The privacy boundary is architectural because the failure is severe and well-documented.** A
public board listing vulnerable people at specific addresses during a disaster is a targeting
list. Splitting public information from volunteer-visible information at the data layer — and
testing every public endpoint for leakage — is the only way that holds under time pressure.

**SMS-first, 20KB, no JavaScript** are not aesthetic preferences. Congested cell networks
degrade data before they degrade SMS, and every kilobyte and round trip is battery in a
neighborhood where nobody can charge. Design for 8%.

**Signup happens before the storm, which means the real work is promotion during calm weather.**
The software is a weekend; getting 200 households registered is the project. Build the door
hanger and the printed roster well, because they're the tools for that part.

**Paper as a first-class output** because it is the only thing with 100% uptime. The coordinator
whose own power is out works from a binder, and if the binder is stale the system fails at
exactly the moment it exists for.

**Before you build:** call [CITY]'s emergency management office and [COUNTY]'s CERT program.
Tell them what you're building. They will often hand you the verified shelter list, tell you
what went wrong last time, and — most valuably — know you exist when it happens.
