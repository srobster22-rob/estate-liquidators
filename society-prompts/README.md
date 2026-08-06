# Everyday Projects That Help Society — A Prompt Kit

Thirty copy-and-paste prompts for building small, real software that helps actual people in
an actual place. Each one is a complete brief: a named user with a named problem, an exact
stack, named data sources, hard constraints, a scope fence, numbered acceptance tests, and
milestones with exit criteria.

**These are not idea lists.** "Build an app to fight food waste" is a wish. The prompts here
tell a coding agent what screens exist, what the database looks like, which API to call, what
it must refuse to do, and how you'll know it worked. Paste one into Claude Code (or any coding
agent) and it can start writing files in the first minute without asking you twenty questions.

---

## Building them

**[`launch/`](launch/README.md) turns any of these into one paste.** Fill in `launch/LOCALE.md`
once (your city, county, state, timezone, languages), run `launch/build-pack.sh`, and you get 30
self-contained files in `launch/ready/` — each one the brief plus repo setup, a working
agreement, deliverables, and stop conditions. Open a new chat, paste one file, done. One project
per chat.

The pack is pre-generated with placeholders intact, so it works before you fill anything in.

---

## How to use this

1. **Pick a project below.** Prefer the one where you personally know someone affected — a
   parent on WIC, a landlord problem, a grandmother who got scammed. Proximity to the problem
   is worth more than a better idea.
2. **Open the file, copy everything inside the fenced block.** That block is the whole prompt.
   Nothing outside it needs to be pasted.
3. **Replace every `[BRACKETED]` value** before you send it. There are usually 3–8 per prompt:
   your city, your state, your county, the org you're building for. The prompt works with
   placeholders left in, but it works far better with them filled.
4. **Paste it into a coding agent** in an empty directory, or a fresh Git repo.
5. **When the build stalls or gets sloppy,** paste `HARDENING-PROMPT.md`. It's a separate pass
   that assumes the thing exists and tries to break it.
6. **Before you show it to a real user,** run the checklist in `LAUNCH-CHECKLIST.md`. Several
   of these projects touch benefits, medical bills, or housing, where a confidently wrong
   answer does damage. That file is about not doing damage.

---

## The thirty

**New here? Start with [16](16-disposal-guide.md).** Lowest stakes, real users on day one, and
it drills the two habits every other project depends on: verify local facts by phone, and design
for the data going stale.

| # | Project | Who it's for | Hard part |
|---|---|---|---|
| [01](01-food-rescue-dispatch.md) | **Surplus food rescue dispatch** | Bakery with 40 unsold loaves at 8pm; shelter that could use them at 8:30 | Perishable windows — a match 90 minutes late is worthless |
| [02](02-benefits-screener.md) | **Benefits eligibility screener** | Someone who just lost hours and doesn't know SNAP exists | Being useful without being wrong; rules change yearly |
| [03](03-tenant-repair-record.md) | **Tenant repair documenter + letter builder** | Renter with a broken heater and a landlord who ignores texts | Evidence that survives contest: timestamps, unedited photos |
| [04](04-medical-bill-auditor.md) | **Medical bill error checker + appeal builder** | Anyone holding a $4,800 bill with "MISC SUPPLIES 1 EA" on it | Parsing garbage PDFs; flagging errors without practicing law |
| [05](05-prescription-price-finder.md) | **Prescription price + assistance finder** | Uninsured diabetic choosing between insulin and rent | Real acquisition-cost data, generic substitution, patient-assistance programs |
| [06](06-heat-risk-cooling-map.md) | **Heat risk + cooling center finder** | Elderly resident on the 3rd floor, no A/C, 104°F outside | Heat index ≠ temperature; the people at risk have the worst phones |
| [07](07-civic-meeting-watchdog.md) | **Civic meeting watchdog** | Resident who found out about the rezoning after it passed | Turning a 200-page agenda packet into "this affects your street" |
| [08](08-ride-coordination.md) | **Volunteer ride coordination** | Dialysis patient who misses treatment when a ride falls through | No-show handling; the failure mode is a person alone at a curb |
| [09](09-lending-library.md) | **Community tool lending library** | Neighborhood where 60 households own 60 unused drills | Overdue items and trust, not inventory |
| [10](10-accessibility-mapping.md) | **Sidewalk + entrance accessibility survey** | Wheelchair user planning a route through an unmapped downtown | Survey rigor — bad data is worse than none when a curb ramp is the question |
| [11](11-air-quality-network.md) | **Neighborhood air quality sensor network** | Block downwind of a highway with no regulatory monitor | Calibration; a cheap sensor reads 2× high in humidity |
| [12](12-outage-checkin-board.md) | **Outage / disaster check-in board** | Ice storm, no power, 5% battery, one bar of signal | Works offline, over SMS, on a 2014 Android |
| [13](13-wage-theft-record.md) | **Wage theft record + claim builder** | Cook told to set up 15 minutes before clock-in, every night, for 8 months | Twenty seconds a day, or she stops logging |
| [14](14-court-date-reminders.md) | **Court date reminders + logistics** | Man whose court paper is in a bag somewhere, date "sometime in March" | Reminding without scraping dockets or outing anyone |
| [15](15-lead-water-lookup.md) | **Lead service line + water lookup** | Parent of a two-year-old in a 1948 house | "Unknown" is the most common answer — how it reads decides everything |
| [16](16-disposal-guide.md) | **"What do I do with this?" disposal guide** | Anyone cleaning a garage with two swollen laptop batteries in it | The rules are municipal; only phone calls make them true |
| [17](17-language-access-kit.md) | **Language access kit** | Woman being asked to consent to a procedure through her 19-year-old son | Refusing to build the translation feature everyone asks for |
| [18](18-directory-that-doesnt-rot.md) | **The directory that doesn't rot** | Every other project here, nine months after launch | Per-field decay, and 15 seconds per verification |
| [19](19-debt-collection-kit.md) | **Debt collection response kit** | Woman who put the court summons in a drawer, planning to explain at the hearing | The answer deadline — most of these are lost by default |
| [20](20-utility-shutoff-help.md) | **Utility shutoff prevention** | Mother with a $842 notice, $180, and a son on a nebulizer | Knowing the sentence that gets a payment plan instead of a no |
| [21](21-iep-meeting-prep.md) | **Special education meeting prep** | Parent who asked about testing at pickup in October; it's February | Timelines nobody told her were running |
| [22](22-scam-check-and-report.md) | **Scam check + report** | 78-year-old on the phone with "the bank's fraud department" right now | One sentence, in type she can read, in one tap |
| [23](23-caregiver-binder.md) | **The caregiver's binder** | Daughter reciting nine of eleven medications to a paramedic at 2am | Fits on one page or it doesn't get read |
| [24](24-after-a-death.md) | **After a death: the first weeks** | Widow asked for a death certificate four times in two days, holding two | Tone, and the debt sentence collectors count on |
| [25](25-election-logistics.md) | **Election logistics + deadlines** | Voter who moved eleven blocks and assumed registration followed | Received-by vs postmarked-by, and staying strictly procedural |
| [26](26-record-clearing-screener.md) | **Record clearing screener** | Man turned down for four apartments over a nine-year-old charge | Routing to the clinic without pretending to be the lawyer |
| [27](27-flood-and-water.md) | **Flood risk + the insurance clock** | Homeowner who thinks her policy covers water. It doesn't. | A waiting period means the decision happens on a dry day |
| [28](28-device-and-connectivity.md) | **Device lending + connectivity** | Teen doing homework in a parking lot; the laptop was never the constraint | The navigator matters more than the lending system |
| [29](29-naloxone-access.md) | **Naloxone access + overdose response** | Mother who's meant to get naloxone for a year and hasn't | Good Samaritan law belongs on the emergency screen, stated exactly |
| [30](30-small-claims-helper.md) | **Small claims + consumer complaints** | Roofer took $4,200 and left a tarp | A judgment is not money, and the tool has to say so first |

Also in this directory:

- **[00-MASTER-FRAME.md](00-MASTER-FRAME.md)** — the reusable skeleton behind all twelve, plus
  a generator prompt for turning *your* problem into a brief this specific.
- **[HARDENING-PROMPT.md](HARDENING-PROMPT.md)** — the second pass. Paste after v1 works.
- **[LAUNCH-CHECKLIST.md](LAUNCH-CHECKLIST.md)** — what to verify before a real person relies
  on it. Includes the legal and safety lines these projects must not cross.

---

## Ground rules baked into every prompt

Every prompt here carries the same seven constraints, because they're the difference between
a demo and something a person can actually use.

1. **It runs on the first `npm install && npm run dev`, with seed data, no API keys.** A
   project that needs three credentials before it shows you anything dies in the first hour.
   Every prompt requires a working offline demo mode with realistic fixtures.

2. **It works on a bad phone on a bad connection.** Target a 2018 Android on 3G. First
   contentful paint under 2 seconds on Slow 4G throttling, JS bundle under 150KB gzipped,
   fully usable at 200% zoom. The people most helped by these projects have the worst devices;
   building for a MacBook on fiber excludes exactly the intended user.

3. **Accessible by default, not as a later ticket.** WCAG 2.2 AA: keyboard-reachable
   everything, visible focus rings, 4.5:1 text contrast, real form labels, no
   information conveyed by color alone. Tested with axe-core in CI, not by eyeballing it.

4. **Plain language, ~6th grade reading level.** No "eligibility determination," no "submit
   remediation request." The prompts specify this and require it to be checked, because
   bureaucratic English is itself an access barrier.

5. **Collect the minimum, keep it local when you can.** No analytics, no third-party fonts,
   no CDN scripts, no session recording. Where a project touches income, health, immigration
   status, or address, the default is client-side storage with explicit export — the server
   should not become a subpoena target for people already at risk.

6. **Say what it doesn't know.** Every project that estimates something must show its
   confidence, cite the rule or dataset it used, print the date of that source, and link the
   official page. "You may qualify" with a source link beats a confident wrong number.

7. **Never invent a data source.** Each prompt instructs the agent to verify each endpoint
   exists and returns what's expected *before* building on it, and to say so plainly if one is
   dead. APIs get deprecated; a hallucinated endpoint that returns plausible fake numbers is
   the worst outcome in this entire kit.

---

## Choosing well

A short honest filter, since thirty options invites drift:

- **Is there a specific person you can show it to this month?** If not, pick a different one.
  These are not products; they're tools for a place you know.
- **Does an org already do this locally?** Then build the thing they're doing in a spreadsheet
  at 11pm. Call them first. Most of these projects are better as "the food bank's dispatch
  tool" than as "a food rescue platform."
- **What happens when it's wrong?** #09 wrong means someone waits a week for a drill; #16
  wrong means a wasted Saturday trip. #02, #04, and #14 wrong means someone doesn't apply for
  food assistance they qualify for, pays a bill they didn't owe, or misses a court date. **#19
  and #20 have the sharpest edges in the kit** — a wrong court answer deadline or a wrong
  shutoff protection is a judgment entered or a power cut. Build a low-stakes one first if this
  is your first project of this kind.
- **Will you maintain it for a year?** Data sources move. Rules change every January. A dead
  benefits screener showing 2026 numbers in 2029 is actively harmful. If the answer is no,
  pick #01, #09, #12, or #16 — the ones that fail safe.

**One is already built.** [#16 is implemented](../disposal-guide/) as a reference: two-layer
verdicts, build-time safety validation, 19.5KB gzipped, axe clean. Read its `STATUS.md` and
`VERIFY.md` to see what an honest "done" looks like — including the milestones an agent cannot
finish.

**A few are different in kind.** #18 is infrastructure rather than a product: build it when a
directory you already run has started rotting, or when three organizations in your city each
maintain their own half-wrong list. #08 genuinely wants a partner organization before the first
ride, because the screening, insurance, and waiver structure needs an entity with liability
coverage — the brief says so and means it. And #21 exists partly to route people to their
state's federally-funded Parent Training and Information Center, which is free, expert, and
almost unknown; if the app does nothing but hand a parent that phone number, it has worked.

**Several have a hard external gate you can't skip.** #19, #21, #22, #24, #26, #29, and #30
each require someone who does the work — a legal aid attorney, a PTI advocate, a bank fraud
specialist, a probate clerk, a harm reduction program — to read the output before a real person
sees it. Those milestones are written
as blockers because in each case a confidently wrong sentence costs someone a judgment, a
year of services, or money they didn't owe.

The best version of any of these is boring, narrow, and used by eleven people in one
neighborhood. Aim there.
