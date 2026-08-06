# 36 — Pet Retention + Veterinary Access

**What it is:** Most people who surrender a pet don't want to. They're moving and can't find a
place that allows dogs, or the vet quoted $900. This finds the pet food bank, the low-cost clinic,
and the pet-friendly housing before the surrender appointment.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`, `[ORG]` (the shelter,
humane society, or rescue you're building with — this one really wants one).

---

```text
You are building a pet retention support tool for [CITY], [COUNTY], [STATE]. Build it now; do not
ask me clarifying questions. Where you need a decision I did not make, choose the option that
keeps the animal in the home, state your choice, and keep going.

Read TONE and SAFETY + LEGAL before writing copy.

=== THE PEOPLE ===

Curtis is 68 and has a twelve-year-old dog named Bo. Bo needs a dental extraction and the quote
was $1,100. Curtis's income is Social Security. He has an appointment at the shelter on Thursday
to surrender Bo, and he has not told anyone why.

Nobody at that shelter wants Bo. A twelve-year-old dog with dental disease is hard to place, the
kennel is full, and the surrender is a worse outcome for everyone including the shelter's budget.
What Curtis needs is a payment plan, a low-cost dental clinic two towns over, or a grant he has
never heard of — and the shelter intake form does not ask.

The second person is Nadia, who is leaving a violent partner and will not go to the shelter that
has a bed because it cannot take her cat. That is a documented and common reason people stay.

The third is a shelter intake coordinator who has ten minutes and a waiting room.

=== TONE ===

- **Never imply that surrendering is a failure.** Some people genuinely cannot keep an animal and
  the right outcome is a good rehoming, done with support. Copy that shames drives people to
  abandon animals rather than surrender them, which is worse for everyone.
- **Never moralize about cost.** "If you can't afford a pet you shouldn't have one" is the belief
  Curtis is already carrying, and it is why he hasn't asked anybody.
- Plain, warm, brief. Ban a word list in CI: "irresponsible," "just get rid of," "dumped,"
  "gave up on."

=== THE PROBLEM ===

Research and verify current figures before displaying any: national and [STATE] shelter intake and
outcome data — Shelter Animals Count and ASPCA publish relevant material. Cite anything with a
year.

The reasons people surrender are consistently practical rather than attitudinal: housing that
does not allow the animal or charges pet rent, veterinary cost, a landlord's breed or weight
restriction, a move, a health crisis in the household, and a lack of temporary boarding during a
hospitalization or a domestic violence escape. Nearly all of them are addressable with information
and small amounts of money, and almost none of them are addressed at the moment of intake.

=== WHAT SUCCESS LOOKS LIKE ===

Curtis cancels Thursday. Bo gets the extraction at a clinic that charges $280 with a payment plan,
paid partly by a grant the shelter helped him apply for. Nadia goes to the shelter that has a bed
because a foster network is holding her cat for six weeks.

=== BUILD THIS ===

1. WHAT'S HAPPENING (/) — One screen, no judgment, six options. Each routes to a different set of
   resources and each is phrased as a circumstance, not a failing:
   - "I can't afford the vet"
   - "I'm moving and can't find a place that takes pets"
   - "My landlord says the pet has to go"
   - "I can't afford food or supplies right now"
   - "I need someone to hold my pet for a while"
   - "Something else, or I've decided to rehome"
   No account, nothing stored on a server, no name.

2. VET COST — Curtis's path and the biggest one. A verified [COUNTY] directory plus the tactics
   nobody tells people:
   - Low-cost and nonprofit veterinary clinics, and whether they have income eligibility.
   - Veterinary school teaching hospitals within driving distance, which are often substantially
     cheaper and are not on anyone's radar.
   - Spay/neuter and vaccination clinics, including mobile ones and their schedules.
   - Financial assistance: national grant programs, breed- and condition-specific funds,
     [STATE] and [COUNTY] funds, and whether [ORG] has one. Verify current status and whether
     applications are open — several well-known funds are frequently closed.
   - Veterinary payment plans and third-party credit, presented with an honest warning about
     deferred-interest terms rather than as a recommendation.
   - The conversation to have with the vet: ask for an itemized estimate, ask what is urgent
     versus what can wait, ask whether there is a less expensive approach that is still
     appropriate, and ask directly whether they offer a payment plan or a discount. Print it as a
     script, like project 20 does — that script is most of the value here.
   - Pet insurance, noted honestly: useful before a problem, useless for a condition the animal
     already has.

3. HOUSING — Nadia's path and the hardest one:
   - How to search for pet-friendly rentals in [CITY], what pet rent and pet deposits typically
     run, and whether [STATE] regulates them.
   - **Assistance animals.** Verify and state accurately: under the federal Fair Housing Act,
     assistance animals — including emotional support animals — are not pets, are exempt from pet
     restrictions and pet fees, and require a reasonable accommodation request rather than
     certification. There is a large industry selling worthless "registration certificates" and
     the app must say plainly that no registry is required or recognized. Cite HUD guidance and
     explain what documentation a housing provider may actually request. This is the single most
     misunderstood thing in this domain and getting it right is worth real housing outcomes.
   - Breed and weight restrictions, and whether [STATE] or [CITY] limits them.
   - A pet resume: vaccination records, a landlord reference, training, and a photo, assembled
     into one printable page. It works more often than people expect.
   - Temporary boarding while housing is arranged.

4. TEMPORARY CARE — The one that keeps people safe:
   - Foster networks that hold animals during hospitalization, treatment, incarceration, or
     housing transition.
   - **Domestic violence-specific programs.** Verify which shelters in [COUNTY] accept animals on
     site and which partner with a foster network, and get this right, because it is a documented
     reason people delay leaving. Handle it carefully: cross-reference safety planning resources
     and do not publish anything that maps where a person or an animal has gone.
   - Emergency boarding after a fire, flood, or eviction.
   - What to do about a pet if the owner dies or is hospitalized — cross-reference projects 23
     and 24, and note that a card in a wallet saying who to call is the practical version.

5. FOOD AND SUPPLIES — Pet food banks, and which human food pantries also distribute pet food,
   which is common and almost never advertised. Include hours, eligibility, and whether they carry
   prescription diets. Verify each by phone.

6. IF REHOMING IS THE RIGHT ANSWER — Without judgment, and this section must exist:
   - How to rehome directly and safely: screening questions, an adoption fee as a filter, a
     written agreement, and the warning signs of someone acquiring animals for the wrong reasons.
   - Breed-specific and senior-specific rescues, which take animals shelters struggle to place.
   - How [ORG]'s surrender process works, what it costs, what happens to the animal, and — stated
     honestly — what their live-outcome rate is if they publish it.
   - What "owner-requested euthanasia" means and when a vet will and will not do it. This is a
     real, difficult conversation and pretending it does not exist helps nobody.

7. FOR [ORG] — An intake-diversion view: the coordinator picks the reason and gets the printable
   resource sheet for that reason in the person's language, plus a log of what was offered and
   what happened. Ten minutes of the waiting room turned into a handout. If [ORG] tracks
   diversions, this is where the number comes from.

=== DATA MODEL ===

resources: id, category, name, address, phone, url, hours jsonb, eligibility, cost_note,
  species text[], appointment_required bool, languages text[], currently_accepting bool,
  verified_on, verified_by, notes
content: slug, category, body, sources jsonb, verified_on
diversions: id, reason, offered_resource_ids[], outcome enum(kept|surrendered|rehomed|unknown),
  recorded_at, recorded_by     -- [ORG] only, no owner or animal identifiers

The public tool stores nothing about the user. The diversion log records circumstances and
outcomes, never a name, an address, or an animal's identity.

=== STACK ===

- Static site + client-side directory for the public tool; a small authenticated view for [ORG].
- Resources as dated, sourced JSON, Zod-validated at build time; `verified_on`, `verified_by`, and
  `currently_accepting` required or the build fails. Reuse the verification pattern from project
  18 — this directory rots faster than most, because grant funds open and close.
- Everything printable. The printed sheet is the deliverable in the waiting room.
- No analytics, no third-party requests. Under 120KB JS.
- [LANGUAGES] from the first commit.

=== HARD CONSTRAINTS ===

- Every resource has `verified_on`, `verified_by`, and `currently_accepting`; past 120 days it
  renders "call to confirm," and a closed fund renders as closed rather than being hidden.
- The assistance animal content is quoted from HUD guidance with a citation and a retrieval date.
- The banned-word list fails the build.
- Every path prints on one page per category.
- Reading level 6th grade. [LANGUAGES] on every screen and printable.
- WCAG 2.2 AA; 18px minimum; works on an old phone.
- No user data on any server.

=== DO NOT BUILD ===

- No veterinary advice, no symptom checker, no triage, no "is this an emergency." Route to a vet
  or an emergency clinic with phone numbers.
- No medication or dosing information.
- No adoption listings, no rehoming marketplace, no classified ads. Those exist, they attract
  people acquiring animals for bad reasons, and moderating them is a full-time job.
- No emotional support animal letters, certificates, registrations, or referrals to services
  selling them. Explain the actual accommodation process instead; the registry industry is
  predatory and part of why housing providers are sceptical of legitimate requests.
- No pet insurance sales, affiliate links, or referrals to veterinary credit products. Describe
  them honestly and let people decide.
- No public map of where animals or their owners are, especially for the domestic violence path.
- No LLM in the content path.
- No breed-based judgments beyond reporting what a landlord or ordinance actually restricts.
- No account, no email capture.

=== ACCEPTANCE TESTS ===

1. Every resource has `verified_on`, `verified_by`, and `currently_accepting`; one missing any
   fails the build.
2. A resource with `currently_accepting: false` renders as closed with its phone number, never
   hidden.
3. A resource past 120 days renders "call to confirm."
4. The banned-word grep finds nothing in built output.
5. The assistance-animal content includes a HUD citation with a retrieval date and states that no
   registration or certification is required.
6. No content path offers, links, or mentions buying an ESA letter or registration — grep test.
7. Each of the six reasons produces a distinct printable sheet that fits one page.
8. The rehoming section is reachable from the first screen without passing through a retention
   pitch.
9. The public tool writes nothing to any server — asserted.
10. Diversion records contain no owner or animal identifier — schema assertion.
11. All content and printables render in every language in [LANGUAGES].
12. Zero third-party network requests.
13. axe-core clean; readable at 200% zoom.
14. Every phone number is a `tel:` link and appears as text as well, so it can be read aloud.

=== MILESTONES ===

M0 — The [COUNTY] directory, phone-verified.
  EXIT: you have called every clinic, fund, food bank, and foster network and confirmed cost,
  eligibility, hours, and whether they are currently accepting. Report how many of the grant funds
  turned out to be closed — it will be more than you expect, and a directory listing a closed fund
  sends someone through an application that goes nowhere.

M1 — The six paths and the printable sheets.
  EXIT: [ORG]'s intake coordinator uses the sheets in the waiting room for a week and tells you
  what was missing.

M2 — Assistance animal content and the housing path.
  EXIT: a fair housing organization or legal aid housing attorney reviews the assistance animal
  section. Do not skip this gate — it is the highest-value and most-misstated content in the
  project.

M3 — Domestic violence path, second language.
  EXIT: a domestic violence advocacy organization reviews that path, including what it does not
  publish.

M4 — One quarter with [ORG].
  EXIT: report diversions by reason and outcome. If vet cost dominates, that tells [ORG] where to
  put its next grant dollar, and that finding may be worth more than the software.

=== SAFETY + LEGAL ===

- Not veterinary advice. Every screen names an emergency veterinary clinic with a phone number,
  verified.
- The assistance animal content must be accurate and cited to HUD. Overstating the right sets
  someone up for a denied accommodation and a lost home; understating it costs them housing they
  were entitled to. Get it reviewed.
- Never suggest misrepresenting an animal as an assistance animal. Beyond being wrong, it is the
  practice that has made legitimate accommodation requests harder for people who need them.
- The domestic violence path is safety-critical. Do not publish which shelters house animals on
  site if the local advocacy organization says that is unsafe to publish; route through their
  hotline instead. Take their direction over this brief.
- Do not shame any outcome, including surrender and including euthanasia. People arrive at this
  tool already carrying it.
- Grant funds open and close constantly. `currently_accepting` is the most volatile field in the
  directory and a stale one wastes a desperate person's week.
- The diversion log records circumstances, never identities. A record of who could not afford
  their dog's dental work is not a record to keep.
- Do not display any shelter statistic you have not sourced with a year.

=== HOW TO REPORT BACK ===

Tell me: how many resources you confirmed by phone and how many funds were closed; what the fair
housing reviewer changed in the assistance animal section; what the domestic violence organization
said should not be published; what [ORG]'s coordinator found missing from the sheets; and
everything you could not verify.
```

---

## Why it's shaped this way

**The intake desk is the intervention point and nobody is working it.** By the time Curtis has a
Thursday appointment, the decision looks settled to him and to the shelter — but the reason is a
$1,100 quote, and there is a clinic two towns over that charges $280. Ten minutes and a printed
sheet in the waiting room is the whole mechanism.

**Assistance animals are the highest-value and most-misstated content in the project.** Under the
Fair Housing Act they aren't pets, aren't subject to pet fees or breed restrictions, and don't
require any registry — yet an entire industry sells certificates that do nothing, and that
industry is part of why housing providers now treat legitimate requests with suspicion. Getting
this section right, cited to HUD and reviewed by a fair housing organization, changes housing
outcomes.

**The rehoming section is reachable from the first screen** without passing through a retention
pitch. Some people genuinely cannot keep an animal, and a tool that makes them scroll past
persuasion to reach honest help is a tool they close.

**The domestic violence path takes its direction from the local advocacy organization, not from
this brief.** Pets are a documented reason people delay leaving, which makes this genuinely
important — and publishing which shelters house animals on site may be exactly the wrong move in a
given town. Their call, not yours.

**`currently_accepting` is the field that rots fastest.** The well-known veterinary assistance
funds are frequently closed, and a directory that lists a closed fund costs a desperate person a
week.

**Before you build:** ask [ORG] for their intake reasons from the last quarter. The distribution
will tell you which of the six paths to build first, and it is usually vet cost.
