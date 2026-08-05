# 16 — "What Do I Do With This?" Disposal Guide

**What it is:** Type "old laptop battery" and get one screen: no, not the recycling bin; yes,
that hardware store two miles away takes them; here are the hours. Hyper-local, verified by
phone, and correct for *your* collection service — which the national websites never are.

**Start here if this is your first project in this kit.** Lowest stakes, shortest path to real
use, and it teaches the two skills every other project needs: verifying local information by
phone, and building a directory that stays true.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`, `[HAULER]` (the
company or department that collects trash and recycling at your address — check your bill).

---

```text
You are building a local disposal and recycling lookup tool for [CITY], [COUNTY], [STATE].
Build it now; do not ask me clarifying questions. Where you need a decision I did not make,
choose the option that avoids telling someone to put something dangerous in a truck, state your
choice, and keep going.

=== THE PERSON ===

Owen is cleaning out a garage in [CITY] on a Saturday. On the floor: a bag of dead AA batteries,
two laptop batteries that are slightly swollen, a half-can of deck stain, a CRT television, an
old smoke detector, a bag of expired prescriptions including two controlled substances, four
propane canisters, a mattress, and a broken microwave.

He looks up "how to recycle batteries," gets a national site that tells him about a program that
doesn't operate here, gives up, and puts most of it in the trash. The lithium batteries go in
the recycling cart, where they will get crushed in the truck.

The second person is a driver for [HAULER], who has been on a truck that caught fire.

=== THE PROBLEM, WITH A NUMBER ===

Two real, documented problems this addresses:
- Lithium-ion batteries in trash and recycling streams cause fires in collection trucks and
  sorting facilities. Waste industry associations track these; look up a current figure with a
  year and source before displaying one.
- Recycling contamination — wishful recycling of things that aren't accepted — raises processing
  costs and sends whole loads to landfill. Ask [HAULER] for their local contamination rate; they
  usually know it and it is usually startling.

Both are information problems. The rules are genuinely local, they change, and the national
sites are generic by necessity.

=== WHAT SUCCESS LOOKS LIKE ===

Owen types each item, gets a specific answer with an address and hours for the six things that
need one, and takes one Saturday trip. The batteries do not go in the cart.

=== BUILD THIS ===

1. SEARCH (/) — One box. Type anything. The search must be extremely forgiving, because this
   is the entire user experience:
   - Synonyms and colloquialisms: "weed killer," "bug spray," "roundup" → pesticides. "TV,"
     "telly," "flatscreen," "tube TV" → electronics, with different answers for CRT vs LCD.
     "AA," "double A," "batteries," "car battery," "laptop battery," "vape" → four different
     answers.
   - Misspellings: fuzzy matching, tuned so "flourescent" finds fluorescent.
   - Brand names: "Sawzall," "Ziploc," "Styrofoam" (which is a brand for extruded polystyrene
     and the thing people mean is usually expanded polystyrene foam — handle it).
   - [LANGUAGES]: search must work in every supported language.
   Build the synonym list as data, and add to it every time a search returns nothing. Log
   zero-result searches (the query text only, nothing else) — that log is your roadmap.

2. THE ANSWER — One screen, no scrolling required for the core answer:
   - A verdict in plain words at the top: "Not in your bins" / "Recycling cart" / "Trash cart" /
     "Special drop-off" / "Take it back to a store" / "Hazardous waste only"
   - One sentence of why, when the why prevents a repeat mistake — especially for the dangerous
     ones. "Lithium batteries start fires when they're crushed in a truck" is worth more than
     any rule.
   - Where to take it: the nearest two or three locations with address, hours, cost, quantity
     limits, and whether they take it from residents versus businesses only
   - Any prep required: tape battery terminals, drain the oil, remove the door from the fridge,
     keep it in the original container
   - Last verified date, visible
   - "This is wrong / they were closed" button — one tap, goes to your review queue

3. THE ITEM DATABASE — YAML files in the repo, one per item or item family:
   slug, display names and aliases per language, category, verdict, why, prep steps,
   destinations (references to locations), quantity limits, hazard notes, source, verified_on.
   Start with the ~120 items people actually search for, not an exhaustive taxonomy. The list
   Owen is standing in front of is a good start; add: paint (latex vs oil — different answers),
   motor oil and filters, antifreeze, propane cylinders (1 lb vs 20 lb — different answers),
   fluorescent tubes and CFLs (mercury), smoke detectors (some contain a radioactive source),
   sharps and needles, medications (controlled vs not), thermometers, tires, appliances with
   refrigerant, e-waste, mattresses, textiles, cooking oil, pizza boxes, plastic bags and film,
   shredded paper, glass (accepted in some programs and not others), aerosol cans, ammunition
   and flares (police, not waste), and asbestos-suspect materials (professional only, never
   DIY guidance).

4. THE LOCATION DATABASE — Every drop-off site with: name, address, coordinates, phone, hours
   including seasonal and event-only schedules, what it accepts (referencing item slugs),
   residency restrictions, proof-of-residency requirements, fees, quantity limits, and
   verified_on with verified_by.
   Sources to research and verify: [COUNTY]'s household hazardous waste facility and its
   collection events, [CITY]'s public works or solid waste department, [HAULER]'s accepted
   materials list, retailer take-back programs (many hardware and electronics chains take
   batteries, bulbs, and e-waste — verify each store, not the corporate policy page, because
   individual stores vary), pharmacy medication drop boxes and the DEA's collection site
   locator, [STATE] product stewardship programs (several states run paint, mattress,
   pharmaceutical, or electronics stewardship programs — find out whether [STATE] does), and
   any scrap yards or reuse organizations that take specific materials.
   EVERY LOCATION IS VERIFIED BY PHONE BEFORE IT SHIPS. Not from a website. This is the actual
   work of the project and it is what makes it better than the alternatives.

5. RE-VERIFICATION — A /verify page listing locations by staleness, showing the phone number,
   the questions to ask, and three buttons: confirmed / changed / closed. Fifteen seconds per
   call. Locations unverified for 180 days show a "call first" flag on the public site with the
   phone number. Hours change, facilities close, and a directory that silently rots is worse
   than none because it sends people on Saturday trips to locked gates.

6. COLLECTION SCHEDULE — If [CITY] or [HAULER] publishes a pickup calendar, add address-based
   lookup: which day, which weeks for recycling, yard waste season dates, holiday shifts, and
   bulky-item pickup rules and how to book one. Verify whether a machine-readable source exists;
   if it's a PDF, transcribe it and note the transcription date.

7. PRINT + SHARE — A one-page printable "what goes where" for the fridge in [LANGUAGES], and a
   printable HHW-event flyer. Also a plain /list page of every location, printable, which is
   what a community center will actually put on a bulletin board.

=== DATA MODEL ===

items: slug, names jsonb (per language, with aliases), category, verdict, why, prep_steps[],
  hazard_level, quantity_limit_note, destination_location_ids[], source_url, verified_on
locations: id, name, address, lat, lng, phone, hours jsonb, seasonal_notes, accepts_slugs[],
  residency_required bool, proof_required, fees_note, quantity_limits, url, verified_on,
  verified_by, active
events: id, name, location_id, starts_at, ends_at, accepts_slugs[], registration_url, notes
zero_results: query_text, searched_at, language   -- query text only, nothing else
reports: id, item_slug|location_id, message, created_at, resolved_at

=== STACK ===

- Astro or Next.js static export. This is a search over a few hundred records — it should be a
  static site with a client-side index, no backend, no database.
- Search: a bundled index with fuzzy matching (Fuse.js or a small trie you write). Must work
  offline after first load; Owen may be in a garage with bad signal.
- The zero-results log and the report button need one tiny endpoint. That is the only server
  component. Log the query string and nothing else — no IP, no session, no timestamp finer
  than the day.
- Under 100KB JS plus the index. Total page weight under 200KB.
- Deploy on any static host. This should cost nothing to run and survive you not touching it.

=== HARD CONSTRAINTS ===

- Answer visible within 2 seconds of typing, offline, on an old phone. Measure it.
- Every answer shows its verified_on date.
- No answer without a destination that has been phone-verified.
- Hazardous items must never be given a "just throw it away" answer unless that is genuinely
  [CITY]'s rule and you have confirmed it with the county or the hauler. When in doubt the
  answer is "take it to hazardous waste," which is never wrong.
- [LANGUAGES] including in search matching, not just display.
- WCAG 2.2 AA, works at 200% zoom, keyboard-only search and navigation.
- Reading level 6th grade.
- No third-party requests at runtime.

=== DO NOT BUILD ===

- No account, no login, no saved lists, no gamification, no "you diverted 4.2 lbs" tracker.
- No photo recognition of items in v1. It is the fun feature, it will consume the whole
  schedule, it will misidentify a lithium battery as a AA, and typing works.
- No national database. Being correct for [CITY] beats being vague everywhere, and the
  generic-national-site failure is precisely the gap this fills.
- No marketplace, no junk removal referrals, no affiliate links to disposal services.
- No LLM answering disposal questions. A hallucinated "yes, that's fine in the recycling" about
  a propane cylinder is a genuinely dangerous output. Curated data only.
- No user-submitted items or locations published without verification.
- No guidance on asbestos, lead paint removal, mercury spill cleanup, ammunition, explosives,
  or medical waste beyond "here is who to call." Those are professional-response items and the
  app's entire job for them is routing.

=== ACCEPTANCE TESTS ===

1. Searching "double A batteries," "AA battery," "batterys," and the [LANGUAGES] equivalents
   all reach the same item.
2. "Battery" returns a disambiguation covering alkaline, lithium-ion, car, and button cells —
   they have different answers and merging them is dangerous.
3. Every item's destinations resolve to existing, active locations.
4. Every shipped location has verified_on set and verified_by naming a person.
5. A location unverified for 180+ days renders the "call first" flag with its phone number.
6. Every hazardous item's answer includes prep steps where prep matters (taping terminals,
   original container, sealed bag).
7. No item classified hazardous has a trash or recycling-cart verdict.
8. Search works with the network disabled after first load.
9. Zero-result searches are logged with the query only — verified by inspecting the stored
   record for absence of any other field.
10. Answer renders in under 2 seconds on Slow 4G with 4x CPU throttle — report the number.
11. All item names and answers exist in every language in [LANGUAGES].
12. axe-core clean; search fully operable by keyboard.
13. The printable fridge sheet fits one page and the /list page prints legibly.
14. No runtime request to any third-party origin.

=== MILESTONES ===

M0 — 30 items, 10 locations, all phone-verified.
  EXIT: you have personally called all 10 locations and confirmed hours, what they accept, and
  whether they take residential drop-offs. Write down how many websites were wrong. That number
  is the project's justification.

M1 — Search that actually finds things.
  EXIT: hand 10 people a list of 8 items and watch them search. Every zero-result is a synonym
  you add. Repeat until the miss rate is near zero.

M2 — 120 items, full location set, re-verification workflow.
  EXIT: someone who is not you re-verifies 10 locations using /verify in under 5 minutes total.

M3 — Second language, printables, collection schedule.
  EXIT: a native speaker reviews the translations; the fridge sheet goes on an actual fridge.

M4 — Real use.
  EXIT: report the zero-result rate from real searches and the top 10 misses. Fix them. Then
  report again — that loop is the whole maintenance model.

=== SAFETY + LEGAL ===

- Never tell anyone to put a lithium battery, a pressurized cylinder, a flare, ammunition, or a
  container of unknown chemicals in any bin. When you are not certain, the answer is the
  hazardous waste facility with its phone number.
- Swollen, damaged, or hot lithium batteries are a fire hazard in the home too. Include the
  current recommended handling guidance from a citable source (fire service or EPA), quoted,
  not paraphrased.
- Controlled substances have their own disposal path. Point to the DEA collection site locator
  and pharmacy drop boxes, and note that some medications have specific FDA disposal guidance
  that differs — verify and cite rather than generalizing.
- Sharps: needles have specific container and disposal requirements that vary by state. Verify
  [STATE]'s and cite it. Never suggest loose disposal.
- Do not instruct anyone in any removal, cleanup, or abatement procedure for asbestos, lead
  paint, or mercury. Route to professionals with phone numbers.
- Do not present the site as official [CITY] or [HAULER] guidance unless they have agreed. A
  line on every page: "Independent volunteer project. Rules can change — call to confirm."
- Every claim traces to a named source: the county, the hauler, the retailer, the state program,
  or a phone call with a date and the name of who you spoke to.

=== HOW TO REPORT BACK ===

Tell me: how many locations you phone-verified and how many of their websites were wrong; the
zero-result rate after M1; the measured answer time; which [STATE] stewardship programs exist;
and everything you could not verify.
```

---

## Why it's shaped this way

**Phone verification is the product.** Everything else is a static site with a search box. The
reason national disposal sites are unsatisfying isn't bad software — it's that the rules are
municipal and change, and nobody calls. Counting how many websites were wrong during M0 is both
the justification and the most interesting thing you'll learn.

**Search forgiveness is the entire user experience.** People type "weed killer," "the swirly
lightbulbs," and "that spray can stuff." An answer database nobody can reach is worthless, so
the synonym list is a living artifact fed by the zero-results log — which is why that log
exists and why it stores nothing but the query.

**Disambiguating "battery" is a safety feature, not a UX nicety.** Alkaline, lithium-ion, car,
and button cells have four different answers and one of them starts fires. Merging them into a
single friendly result is the most likely way this app hurts someone.

**No image recognition in v1** even though it's the obvious demo. It will eat the schedule, and
a model that confidently misidentifies a swollen lithium pouch as a AA is worse than a text box.

**Why this is the recommended starter:** it has real users on day one, the failure mode is a
wasted trip rather than a lost benefit or a missed court date, and it forces you to practice
the two habits the higher-stakes projects depend on — verify locally by phone, and design for
the data going stale.

**Before you build:** call [HAULER] and ask for their contamination rate and their top five
problem items. You'll get your first ten entries and a number worth putting on the front page.
