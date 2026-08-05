# 15 — Lead Service Line + Water Quality Lookup

**What it is:** Type your address. Find out which utility serves you, whether the pipe from the
main to your house is lead or "unknown," what the utility's own testing found, and what to
actually do about it — including the filter certification that matters and the one that doesn't.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`, `[UTILITY]` (the
water system serving [CITY] — find its name and PWSID before you paste).

---

```text
You are building a drinking water lookup tool for residents of [CITY], [STATE], served by
[UTILITY]. Build it now; do not ask me clarifying questions. Where you need a decision I did
not make, choose the option that avoids alarming people about a risk you have not verified,
state your choice, and keep going.

Read SAFETY + LEGAL first. This project can frighten people, and the design has to earn the
right to do that.

=== THE PERSON ===

Priscilla rents a house built in 1948 in [CITY]. She has a two-year-old. She read something
about lead pipes and now she is not sure whether to let him drink the water, and the water
department's website has a PDF called "2024 Consumer Confidence Report" that is 14 pages of
tables.

What she needs to know, in order: is my pipe lead, is my water tested, what do I do today, and
what do I do about it permanently. What she gets instead is either a table of detection limits
or a headline about a different city.

The second person is her landlord, who is not going to replace a service line because a tenant
asked, but might if handed a specific document about a specific address.

=== THE PROBLEM, WITH A NUMBER ===

There is no safe level of lead exposure for children — verify and cite the current CDC and EPA
language for this precisely, because it is the sentence that justifies the whole project and it
must be quoted accurately.

Federal drinking water rules required community water systems to compile service line material
inventories and make them publicly accessible, with a compliance deadline in October 2024, and
subsequent rules address replacement. VERIFY the current status of these requirements before
writing a word about them — this area has been revised and litigated, and stating a superseded
rule as current is the single most likely way this app misleads someone. If you cannot verify
the current rule, describe only what [UTILITY]'s published inventory says and link it.

The practical gap: those inventories exist now, and almost nobody knows they can look up their
own address in one. A large share of entries are classified "unknown," which is itself
actionable information and is usually presented as though it were reassuring.

=== WHAT SUCCESS LOOKS LIKE ===

Priscilla learns her service line is listed as "unknown," learns how to check it herself in ten
minutes with a coin and a magnet, learns that running the tap before drinking helps and why,
buys a filter certified for lead reduction rather than one that isn't, and sends her landlord a
one-page letter with the utility's own record attached.

=== BUILD THIS ===

1. LOOK UP MY ADDRESS (/) — One field. Type an address, get an answer page. No account.
   The answer page, in this order:
   - Which water system serves this address, and its PWSID
   - Service line material on record: LEAD / GALVANIZED REQUIRING REPLACEMENT / NON-LEAD /
     UNKNOWN / NOT IN THE INVENTORY — using the utility's own categories, quoted, with a link
     to the inventory record and the date it was published
   - Plain-language meaning of that category in two sentences
   - What to do today, specific to the category
   - Whether the building is likely old enough for lead solder or brass fixtures regardless of
     the service line — because a non-lead service line does not mean no lead in the house
   - The utility's most recent lead testing results and what they mean
   - Any current violations for this system
   "UNKNOWN" must be presented as what it is: not yet determined, worth finding out, not
   "probably fine." Most inventories are full of unknowns and the wording here decides whether
   this tool helps or lulls.

2. THE DATA — Research and verify each source before building. Do not assume any of these
   exist in the form you expect:
   - [UTILITY]'s service line inventory. Format varies wildly: some publish an interactive
     map, some a spreadsheet, some a PDF, some an address-lookup page. Find [UTILITY]'s,
     document what it is, and import it. If it is only a lookup page you cannot bulk-download,
     do NOT scrape it — link users to it directly and build the rest of the app around it.
   - EPA's Safe Drinking Water Information System and the ECHO / SDWIS public data for
     violations and system information, joined by PWSID.
   - [UTILITY]'s Consumer Confidence Report, published annually — parse or transcribe the lead
     and copper results, the 90th percentile value, and the sample count, and cite the report
     and its year.
   - Address-to-water-system mapping. This is harder than it sounds; systems have service area
     boundaries that are not always published. If [CITY] has one utility, hardcode it and say
     so. If it has several, find the boundary data or ask users to confirm from their bill.
   Every fact displayed carries its source, the source's publication date, and a link.

3. FIND OUT YOURSELF — For unknown lines, an illustrated guide to the coin-and-magnet test on
   the pipe where it enters the building: scratch it, look at the color, try a magnet, compare
   against photos of lead, galvanized steel, copper, and plastic. Include a "how to send this
   to your utility" step, because many utilities are actively collecting resident-submitted
   material identifications to fill in their inventories, and a resident who identifies their
   own line has done real work for the public record.
   Be careful and clear: this is identification, not disturbance. Do not instruct anyone to
   cut, scrape aggressively at, or disturb a pipe.

4. WHAT TO DO NOW — Verified, cited, plainly written, ordered by effectiveness:
   - Filters: the certification that matters is the standard specifically covering lead
     reduction. Look up the current NSF/ANSI standard designations and certification marks for
     lead reduction, name them exactly, and tell people to look for that specific mark on the
     package — not "filters lead" in marketing copy. Include price range and where to buy.
     Include the fact that filters must be replaced on schedule to keep working. This is the
     most actionable item in the app; get the standard number right.
   - Flushing: run the tap before drinking after water has sat. Verify current guidance for how
     long and cite it. Explain why it works and when it does not.
   - Cold water only for drinking, cooking, and formula, and why hot water is worse.
   - Testing your own tap: how to get a test, what a certified lab costs in [STATE], whether
     [UTILITY] offers free testing, and how to read the result.
   - Blood lead testing for young children: how to ask, and note that some children are
     eligible for it through Medicaid — verify the current requirements and cite them.
   - Formula: verify and state current guidance about mixing formula with tap water where lead
     is a concern.

5. WHAT TO DO PERMANENTLY —
   - [UTILITY]'s replacement program: is there one, what does it cost the homeowner, what is
     the timeline, how do you get on the list, and is there financial assistance. Call and
     verify; do not rely on the website.
   - A letter generator for renters to landlords: the address, the inventory record with its
     link, a request for information about the plumbing, and a request for replacement or
     filters. Note the applicable habitability or lead disclosure obligations in [STATE] if you
     can verify them, and cite them; otherwise write a plain request. Reference project 03 for
     the record-keeping approach if the landlord does not respond.
   - The federal lead disclosure requirements for pre-1978 housing at sale and lease — verify
     the current rule and what it does and does not require, and state it precisely. This is
     frequently misdescribed.

6. BEYOND LEAD — A secondary section covering what else [UTILITY]'s reports show: disinfection
   byproducts, nitrate, PFAS. Federal drinking water standards for certain PFAS compounds were
   established recently and their compliance timelines and status should be VERIFIED before you
   describe them. Show what [UTILITY] reported, against the current standard, with dates and
   links, and no interpretation beyond over/under.

7. PRIVATE WELLS — If any part of [COUNTY] is on well water, one honest page: private wells are
   generally not covered by federal drinking water regulations, nobody is testing them for you,
   and here is [COUNTY]'s health department guidance, the recommended testing schedule, and
   what a test costs. Verify all of it. This audience is invisible in every water-quality tool
   and it is a five-hour addition.

=== DATA MODEL ===

systems: pwsid, name, county, population_served, source_type, contact_phone, ccr_url,
  inventory_url, last_synced
service_lines: id, pwsid, address_normalized, lat, lng, utility_side_material,
  customer_side_material, category, source_record_id, inventory_published_on
violations: id, pwsid, contaminant, kind, began_on, resolved_on, description, source
ccr_results: id, pwsid, year, analyte, value, unit, standard_value, sample_count,
  ninetieth_percentile, source_url
resident_reports: id, address_normalized, material_reported, photo_ref, reported_at,
  forwarded_to_utility_at
content: id, slug, body_md, sources jsonb, verified_on

Address normalization is the hard part and will decide whether lookups work. Use a consistent
normalizer, store the raw input alongside it, and when a lookup misses, say "we could not find
this address in the inventory" and link the utility's own lookup — never say "no lead found."
Those are completely different statements and conflating them is the worst bug this app can
have. Write a test for it.

=== STACK ===

- Static-first: Astro or Next.js static export with the inventory as a prebuilt searchable
  index. The whole lookup can be client-side over a compressed index for a single city.
- Data build script in /scripts that fetches each source, records URL and retrieval date, fails
  loudly on a 404, and writes versioned files. This script is the maintenance surface; document
  it in MAINTENANCE.md with the month each source updates.
- PostgreSQL only if you need resident reports; otherwise no database at all.
- No third-party requests at runtime. No analytics.
- Under 150KB JS plus the lazily-loaded index.

=== HARD CONSTRAINTS ===

- Every displayed value carries its source, publication date, and link, inline.
- "Not found in the inventory" is never rendered as "no lead." Distinct copy, distinct styling,
  tested.
- Reading level 6th grade. This subject generates fear; clear beats clinical, and precise beats
  both. No jargon in the answer page — "90th percentile" appears only in the detail section
  with an explanation.
- [LANGUAGES] from the first commit.
- WCAG 2.2 AA; the answer page must be usable at 200% zoom and must not convey the category by
  color alone.
- The answer page must render in under 1.5s on Slow 4G. Measure it.
- Any content page not re-verified in 12 months displays its age.

=== DO NOT BUILD ===

- No health risk assessment, no "your child's exposure level," no calculator estimating blood
  lead. That is clinical territory requiring individual testing.
- No filter product recommendations by brand, no affiliate links, no shopping integration. Name
  the certification standard; let people buy anything that carries it.
- No lead testing kit sales, no lab partnerships that pay you.
- No property-level public map of lead lines beyond what the utility already publishes — do
  not build a searchable "lead houses" layer that affects property values and rentals in ways
  you have not thought through. Show a result to the person who typed their own address.
- No scraping of a utility lookup page that is not published as bulk data. Link it.
- No LLM interpreting water quality results.
- No comparison rankings between water systems or cities.
- No alarm language, no color-coded threat levels beyond the utility's own categories.

=== ACCEPTANCE TESTS ===

1. An address present in the inventory returns the utility's own category, quoted, with a
   source link and publication date.
2. An address absent from the inventory returns "not found in the inventory" with distinct copy
   and styling — never "no lead" — verified by a test that greps the rendered output.
3. Address normalization matches a real address entered five different ways (abbreviations,
   apartment forms, casing, punctuation, missing ZIP).
4. Every displayed number has a source URL and a publication date.
5. The build script fails when a source URL 404s rather than silently shipping stale data.
6. Content pages past 12 months render an age notice.
7. The filter guidance names the specific certification standard for lead reduction and does
   not name a brand.
8. The answer page renders under 1.5s on Slow 4G — report the measured number.
9. axe-core clean; category is conveyed by text, not color alone.
10. All strings present in every language in [LANGUAGES].
11. No runtime requests to any third-party origin.
12. The letter generator produces a one-page PDF including the inventory record link.
13. Violations for the correct PWSID are shown, and a system with none shows "no current
    violations reported as of <date>" rather than an empty section.

=== MILESTONES ===

M0 — Data acquisition, honestly assessed.
  EXIT: a written report of what [UTILITY] actually publishes, in what format, how complete it
  is, what fraction is "unknown," and whether it is bulk-downloadable. If it is not, say so —
  that finding reshapes the project and is worth knowing on day one rather than day twelve.

M1 — Address lookup returning the utility's category with citations.
  EXIT: ten real addresses, including your own, return correct results checked by hand against
  the utility's own lookup.

M2 — What to do now + what to do permanently, verified.
  EXIT: someone at [UTILITY] or [COUNTY]'s health department reviews the guidance pages and
  confirms nothing is wrong. Call them; most will do this.

M3 — Self-identification guide, letter generator, second language.
  EXIT: a person with an unknown line follows the coin-and-magnet guide and successfully
  identifies their pipe.

M4 — Wells page + PFAS + violations.
  EXIT: report how many addresses in [CITY] are "unknown" in the inventory. That single number
  is the most useful thing this project produces and nobody has published it locally.

=== SAFETY + LEGAL ===

- This is not medical advice, not a water test, and not a determination of safety for any
  address. Say so on the answer page. Only a test of the water at that tap tells you what is in
  that water.
- Quote health language from CDC and EPA verbatim with citation. Do not paraphrase health
  claims about lead — the wording is careful for good reasons and paraphrase drifts.
- Do not tell anyone their water is safe. The app reports records and what they mean; the
  absence of a record is not evidence of safety, and the app must never blur that.
- Do not tell anyone to stop drinking their water either, unless quoting an official advisory
  in effect for that system. Unfounded alarm has real costs — bottled water expense, and
  reduced tap water consumption persisting long after the actual problem is resolved.
- Be extremely careful with rule status. Federal lead rules have been revised and litigated;
  describing a proposed, superseded, or stayed requirement as current is the most likely way
  this app misleads. Cite the specific rule, its status, and the date you checked.
- Renters: the letter generator is a request, not a demand, and the app should note that
  retaliation concerns are real and point to the tenant resources in [CITY]. Cross-reference
  project 03.
- Do not build anything that lets someone search which houses have lead lines. Utilities
  publish inventories for residents to check their own addresses; a searchable public map of
  affected properties affects renters and sellers in ways that are not yours to impose.
- Talk to [UTILITY] before launch. Many have community engagement staff who will correct your
  page, give you the inventory in a usable format, and tell you about assistance programs the
  website doesn't mention.

=== HOW TO REPORT BACK ===

Lead with the M0 finding: what [UTILITY] publishes, in what format, how complete. Then: every
rule whose current status you verified and how; the certification standard number for lead
filters and where you read it; the unknown-line percentage; the measured page load; and
everything you could not verify.
```

---

## Why it's shaped this way

**"Unknown" is the most common answer and the whole design hinges on how it reads.** Service line
inventories are full of unknowns, and a UI that renders unknown in soft gray next to a checkmark
tells people they're fine. Unknown means nobody has looked — which is actionable, and which is
why the self-identification guide exists.

**"Not found in the inventory" ≠ "no lead," enforced by a test,** because address matching fails
constantly and the failure mode of a sloppy lookup is telling a parent their water is fine when
nobody ever checked.

**Naming the filter certification standard instead of a brand** is the single most useful
sentence in the app. Consumer filters vary enormously in what they actually remove, package
marketing is unreliable, and the certification mark is the one durable signal — worth getting
exactly right and worth refusing to monetize.

**Verify the rule status, repeatedly stated,** because federal lead rules have moved recently
and confidently describing a superseded requirement is how a well-meaning tool ends up wrong in
a way nobody catches.

**The unknown-line percentage for [CITY]** is a genuine local finding. It usually isn't published
anywhere accessible, it's computable from the inventory in an afternoon, and it's the number a
reporter or a council member can use.

**Before you build:** find [UTILITY]'s inventory and look at it. Everything about the project's
scope follows from what format it's in.
