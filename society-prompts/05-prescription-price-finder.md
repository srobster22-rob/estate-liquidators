# 05 — Prescription Price + Assistance Finder

**What it is:** Type a drug name. Get the generic equivalent, what pharmacies actually pay for
it (public federal data), every patient assistance program that covers it, and a printed
script for the two conversations that lower the price: the one with the pharmacist and the one
with the prescriber.

**Fill in before pasting:** `[STATE]`, `[CITY]`, `[LANGUAGES]`.

---

```text
You are building a prescription cost tool for people in [STATE] who are uninsured,
underinsured, or in a deductible. Build it now; do not ask me clarifying questions. Where you
need a decision I did not make, choose the option that keeps clinical judgment with the
prescriber, state your choice, and keep going.

Read SAFETY + LEGAL first. It draws a line this app must not cross, and the line shapes the
whole product.

=== THE PERSON ===

Ray, 61, [CITY]. Type 2 diabetes, high blood pressure, and a statin. He retired early, is not
yet 65, and bought a marketplace plan with a $7,000 deductible, which means he pays cash for
everything. Last month the pharmacy told him $312 for a 30-day fill of one drug. He said
"never mind" and walked out, and he has been taking it every other day since to stretch what
he has left.

He did not tell his doctor he stopped. That is the normal thing to do and it is the thing
this app exists to interrupt.

=== THE PROBLEM, WITH A NUMBER ===

Cost-related nonadherence — skipping doses, splitting pills, not filling — is measured
regularly by CDC/NCHS and KFF. Look up a current figure with its year and source before
displaying one. Do not display an unsourced statistic.

The mechanism to attack: the cash price at the counter is often wildly disconnected from what
the drug costs the pharmacy, from what the same drug costs three miles away, and from what a
therapeutically equivalent drug costs. Ray has no way to see any of that, so he has no way to
ask for it.

=== WHAT SUCCESS LOOKS LIKE ===

Ray walks into an appointment with one printed page: "These three drugs cost me $412/month.
Here are the generic and therapeutic alternatives. Here are two assistance programs I appear
to qualify for. Can we talk about this?" And he tells the doctor he's been skipping doses.

=== BUILD THIS ===

1. ADD YOUR MEDICATIONS (/) — A search box. Type "Januvia" or "sitagliptin" or a partial name.
   Autocomplete against RxNorm. For each drug the user adds, capture: strength, form,
   quantity per fill, days supply, and what they currently pay cash. No login, stored locally.

2. THE GENERIC QUESTION — For each drug, resolve via RxNorm whether a generic equivalent
   exists and name it. This is the single highest-value lookup in the app.
   - Use the RxNav / RxNorm APIs from the National Library of Medicine to normalize the name
     to an RxCUI and to find related concepts (branded vs clinical drug forms).
   - Present it plainly: "Januvia is the brand name. The active ingredient is sitagliptin.
     [Generic available / No generic available yet.]"
   - Where no generic exists, say so and move to therapeutic alternatives (part 4).
   VERIFY the RxNav endpoints and their current rate limits and terms of use before building
   on them. Cache aggressively by RxCUI; do not hammer a free public NLM service.

3. WHAT IT ACTUALLY COSTS — Show the NADAC value: the National Average Drug Acquisition Cost,
   published by CMS/Medicaid as a public dataset of what retail pharmacies actually pay to
   acquire drugs, updated regularly and downloadable from data.medicaid.gov.
   Present it precisely and without spin:
   "Pharmacies pay about $X per [unit] for this. A 30-day supply costs them about $Y. That's
   not what you'll be charged — pharmacies add dispensing fees and markup — but it tells you
   what's possible to ask about."
   - Join on NDC. Handle the NDC format problem explicitly: NDCs appear in 10-digit and
     11-digit forms with different segment paddings, and getting this wrong silently produces
     no matches or wrong matches. Write and test a normalizer both directions.
   - Ship the NADAC data as a versioned static file fetched by a script in /scripts, recording
     the file's publication date. Display that date next to every price.
   - If a drug has no NADAC entry (common for brand-only drugs), say "No public acquisition
     cost is published for this drug" — never estimate.

4. ALTERNATIVES TO ASK ABOUT — For each drug, show other drugs in the same class, sourced
   from a citable classification (RxClass from NLM exposes ATC and other class relationships;
   verify what it returns before relying on it). Frame every single one as a question for the
   prescriber, never a suggestion:
   "Other drugs in this class include A, B, C. Some are much cheaper. Only your prescriber
   can say whether any of them is right for you — here's how to ask."
   Never rank them, never recommend one, never say "switch to." The app surfaces the
   existence of options; the clinician decides.

5. ASSISTANCE PROGRAMS — A researched, cited directory, filtered to the user's drugs:
   - Manufacturer patient assistance programs for the specific brand drugs entered. Each
     entry: program name, who qualifies (income as a % of federal poverty level, insurance
     status), what it provides, application URL, and the date you verified it.
   - Manufacturer copay cards, with the standard caveat that most exclude people with
     government insurance.
   - Federally Qualified Health Centers and 340B pharmacies in [CITY] — FQHC locations are
     published by HRSA. Explain in one plain sentence what these are and why the price may be
     dramatically lower.
   - [STATE]'s pharmaceutical assistance program, if one exists. Research this; many states
     have one and almost nobody knows about it.
   - Community health center sliding-scale pharmacies in [CITY].
   Every entry cites a source URL and a verification date, and the directory lives in a JSON
   file with a documented refresh procedure. An out-of-date assistance directory sends
   someone on a wasted trip, so a stale entry must render a visible "last checked" date.

6. THE TWO SCRIPTS — Printable, personalized with the user's actual drugs and prices.
   a. AT THE PHARMACY: ask for the cash price without insurance (sometimes lower than the
      insured price); ask whether a 90-day supply lowers the per-month cost; ask whether they
      price-match; ask if a different strength with the same daily dose costs less and whether
      the prescriber would need to authorize it; ask about their discount program.
   b. WITH THE PRESCRIBER: the sentence that matters most, printed at the top in large type —
      "I have not been taking this as prescribed because of the cost." Then: is there a
      generic or a cheaper drug in the same class; can this be a 90-day prescription; is there
      a sample or a patient assistance program; is any drug on this list one I could stop.
   Both scripts end with blank lines for writing down the answers.

7. TOTAL PICTURE — A simple monthly total across all drugs, with a "what changed" line if
   they update prices later. No charts, no trends, no gamification.

=== DATA MODEL (local only) ===

medications: id, user_label, rxcui, name, is_brand, generic_rxcui|null, strength, form,
  qty_per_fill, days_supply, current_cash_price, pharmacy_name, added_at
nadac_cache: ndc11, rxcui, description, unit_cost, effective_date, pricing_unit
programs: id, drug_rxcuis[], name, sponsor, type, eligibility_text, income_threshold_fpl,
  excludes_govt_insurance bool, url, phone, verified_on
Everything in IndexedDB. No server. Ray's medication list is a health record.

=== STACK ===

- React + TypeScript + Vite, PWA, offline-capable, IndexedDB.
- NADAC and the assistance directory ship as static compressed JSON, built by
  /scripts/fetch-reference-data.ts, which records source URL, publication date, and fetch
  date for each file and fails loudly if a source 404s.
- RxNorm/RxNav calls go directly from the browser to NLM if CORS permits; verify this first.
  If CORS blocks it, build a thin stateless proxy that forwards the query and logs NOTHING —
  no query text, no IP, no timestamps. Document that guarantee in the code and the README.
- Fuzzy search over a bundled drug-name index (Fuse.js or a trie you write). Typing must work
  offline for the common case; live RxNav lookups enhance it.
- Under 200KB JS gzipped, plus lazily-loaded data files.

=== HARD CONSTRAINTS ===

- No account. No server-side medication list. Ever. A list of someone's prescriptions is a
  list of their diagnoses.
- The app must work fully offline with bundled NADAC data and a bundled name index. Ray may be
  standing in a pharmacy with no signal.
- Every price displayed shows its source and its date, inline, not in a tooltip.
- WCAG 2.2 AA. Body text 18px minimum default. Users skew older; do not use gray-on-gray.
  Every drug name must be selectable text so it can be copied, and rendered in a font where
  0/O and 1/l are distinguishable — drug name confusion is a real safety issue.
- Reading level 6th grade for app copy. Drug names are what they are.
- [LANGUAGES] from the first commit.
- No third-party requests except NLM's API. No fonts, no analytics, no error reporting.

=== DO NOT BUILD ===

- No dosing information, no interaction checker, no side-effect lists, no "is this safe with"
  anything. That is clinical software with a completely different risk profile and regulatory
  posture. Out of scope, and say so in the app.
- No recommendation of any specific drug, ever, including implicitly through sort order.
  Alternatives are listed alphabetically, not by price. Sorting a therapeutic class by price
  is a de facto clinical recommendation.
- No pill-splitting, dose-stretching, or "take every other day to save money" advice under any
  framing. Some formulations are dangerous to split. The app's response to "I can't afford
  this" is always "tell your prescriber," never a workaround.
- No coupon aggregation, no affiliate links, no discount-card partnerships, no referral fees.
  Those business models are why existing tools are untrustworthy. If you find yourself adding
  a "Get this coupon" button that pays you, stop.
- No pharmacy price scraping. Retail cash prices are not published in any reliable public API,
  and scraping them yields stale numbers that get someone's hopes up. Show NADAC as the anchor
  and teach them to ask.
- No LLM in the drug identification or pricing path. RxNorm resolution and NADAC lookups are
  deterministic joins. A hallucinated generic equivalent is a patient safety event.
- No prescription refill tracking, no reminders, no adherence scoring.

=== ACCEPTANCE TESTS ===

1. Searching "Januvia" resolves to the correct RxCUI and identifies sitagliptin as the
   ingredient.
2. A drug with a known generic reports it; a brand-only drug reports "no generic available"
   rather than guessing.
3. NDC normalization round-trips correctly for all three 10-digit segment configurations
   (4-4-2, 5-3-2, 5-4-1) into 11-digit form. Test each explicitly with real examples.
4. A drug with no NADAC entry renders "no public acquisition cost published" and no number.
5. Every displayed price renders its source name and effective date.
6. The app functions fully offline: search, view, generate scripts, print.
7. Zero network requests to any origin other than NLM's API during a full journey.
8. No generated output contains a recommendation verb ("switch to", "you should take",
   "better than", "instead take"). Enforce with a grep test that fails the build.
9. Therapeutic alternatives render in alphabetical order regardless of price.
10. Every assistance program entry has a verified_on date, and entries older than 180 days
    render a visible staleness warning.
11. The prescriber script's first line is the cost-nonadherence sentence, in large type.
12. axe-core reports zero violations; the full flow completes with keyboard only.
13. The reference-data build script fails loudly when a source URL 404s rather than shipping
    the previous file silently.

=== MILESTONES ===

M0 — Search, RxNorm resolution, generic identification. One screen.
  EXIT: enter five real drugs from a real medicine cabinet; every generic relationship is
  correct when checked by hand against the label.

M1 — NADAC integration with correct NDC handling.
  EXIT: acceptance test 3 passes and five drugs show acquisition costs that match the raw
  dataset when you look them up manually.

M2 — The two scripts, printable.
  EXIT: a pharmacist reads the pharmacy script and says the questions are ones they can
  actually answer. Do not skip this gate; it will change the wording substantially.

M3 — Assistance directory for [STATE] and [CITY].
  EXIT: you personally call three of the listed programs and confirm they exist, take
  applications, and have the stated income thresholds. Delete any you cannot confirm.

M4 — One real person.
  EXIT: someone takes the printed page to an actual appointment and tells you what happened.

=== SAFETY + LEGAL ===

- Not medical advice, and this one is not boilerplate — it's the design constraint. The app
  identifies chemical equivalence and surfaces the existence of alternatives and programs. It
  never evaluates whether a drug is appropriate. Every alternatives view carries: "Only your
  prescriber can decide if any of these is right for you."
- Never, under any phrasing, suggest changing a dose, skipping, splitting, or stopping a
  medication. Include an explicit check in code review for this, and a grep test.
- Generic substitution is not universally interchangeable — narrow therapeutic index drugs and
  certain formulations are the known exceptions. Add a line to every generic finding: "Ask
  your pharmacist whether the generic works the same for you. For a few medicines it matters."
- The prescription list never leaves the device, and the README must state the threat model:
  this list reveals HIV status, psychiatric diagnoses, pregnancy, addiction treatment, and
  gender-affirming care. A server holding it is a harm waiting to happen.
- If you must proxy NLM calls, log nothing. Not the query, not the IP, not the time. Write
  that as an explicit test if you can, and as a prominent comment if you cannot.
- Do not display any statistic you have not sourced to a named publication with a year.

=== HOW TO REPORT BACK ===

Tell me: which NLM endpoints you verified and their terms; the NADAC file publication date;
which assistance programs you confirmed by phone versus by webpage; the NDC normalization test
results; and every place you had to guess. If RxNav's CORS policy forced a proxy, tell me
exactly what it does and does not log.
```

---

## Why it's shaped this way

**NADAC is the honest anchor.** There is no public API for retail cash prices, and scraping
one produces confidently wrong numbers. What *is* public is what pharmacies actually pay to
acquire drugs — a federal dataset. It doesn't tell Ray what he'll be charged, but it tells him
whether $312 is in a different universe from the drug's cost, which is exactly the information
that makes a conversation at the counter possible.

**The alternatives list is alphabetical on purpose.** Sorting a therapeutic class by price is
a clinical recommendation wearing a UI affordance. The app's entire ethical position is that it
surfaces facts and hands the decision to a clinician; sort order is where that position would
quietly leak.

**The prescriber script's first line is the product.** "I have not been taking this because of
the cost" is a sentence patients don't say and clinicians can't act on until they hear. Most of
the value here is getting that sentence into the room; the data work is what earns the printout
the trip.

**No coupon affiliate revenue, stated flatly,** because it's the obvious business model and it
is precisely what makes every existing tool in this space impossible to trust.

**Before you build:** ask a pharmacist what they wish patients asked them. They will give you
the script for free, and it will be better than yours.
