# 34 — Funeral Price Shopping

**What it is:** Federal law entitles you to an itemized price list, to buy only what you want, and
to supply your own casket without a surcharge. Almost nobody exercises any of it, at a moment when
prices vary by thousands of dollars across town.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`.

---

```text
You are building a funeral price comparison and rights tool for [CITY], [STATE]. Build it now; do
not ask me clarifying questions. Where you need a decision I did not make, choose the option that
reduces pressure on the person making the decision, state your choice, and keep going.

Read TONE and SAFETY + LEGAL before writing copy. Cross-reference project 24, which covers
everything else that happens after a death; this one is only about the money.

=== THE PEOPLE ===

Ines is 63. Her mother died on Thursday. On Friday she sat in an office and was shown a book of
caskets, starting at the third page. She agreed to a package because agreeing was easier than
asking questions in front of her brother, and because she did not know that packages are optional,
that the same services three miles away cost substantially less, or that she was entitled to a
printed price list she could take home.

The second person is Walter, 78, who is doing this in advance, on a Tuesday, with a notebook —
which is the entire difference and is the behaviour this app exists to make possible.

=== THE PROBLEM ===

The FTC's Funeral Rule gives consumers specific rights. Research and verify the current rule text
from the FTC directly before writing a word — do not paraphrase from memory or from a funeral
industry site. The rights to verify include, at minimum:

- The right to receive a **General Price List (GPL)**, itemized, to keep, when you inquire in
  person about arrangements.
- The right to get **price information over the telephone**.
- The right to **buy only the goods and services you want**, rather than a package, with limited
  exceptions.
- The right to **supply a casket or urn purchased elsewhere**, with the provider prohibited from
  charging a handling fee for it.
- Disclosure requirements about embalming — verify what the rule says about when it is and is not
  required, because the belief that it is always required is widespread and expensive.

Also verify: what [STATE] adds on top of the federal rule, whether [STATE] requires a casket for
cremation, what "direct cremation" and "immediate burial" mean as defined categories, and who
enforces the rule and how to complain.

Prices for identical services vary substantially between providers in the same city. That
variation is the opportunity, and the GPL is the instrument that makes it visible.

=== TONE ===

Same constraints as project 24 and they matter as much here.

- Plain and warm. No euphemism ("passed on," "at rest") and no clinical distance ("the decedent").
- Never urgent. Nothing on this screen is time-critical in the way the person fears it is —
  including, in most cases, embalming. Slowing the decision down is the intervention.
- No motivational language, no progress gamification, no celebration of any kind.
- Everything resumable and printable. This gets done in fifteen-minute pieces.
- Never imply that spending less means caring less. That belief is the mechanism the whole
  industry's upsell runs on, and the app must not reinforce it even accidentally. Ban a word list
  in CI: "dignified," "deserve," "final gift," "peace of mind," "honor them with."

=== WHAT SUCCESS LOOKS LIKE ===

Ines makes three phone calls before she goes anywhere, has three itemized lists in front of her,
and buys what she chose. Or she goes anyway and takes the price list home and sleeps on it.

=== BUILD THIS ===

1. START (/) — Two doors: "Someone has died" and "I'm planning ahead."
   The first opens with one screen, no navigation, before anything else:
   - You do not have to decide today. In most cases nothing has to be arranged in the first
     hours. Verify this and state it accurately.
   - You are entitled to an itemized price list you can keep.
   - You can buy only what you want.
   - You can bring a casket you bought somewhere else, and they cannot charge you extra for it.
   Then a "call before you go" button. That screen is the product; everything after it is
   support.

2. THE PHONE SCRIPT — Printable, in [LANGUAGES]. What to ask, in order, with space to write:
   the price of direct cremation; the price of immediate burial; the basic services fee, which is
   non-declinable and is the number that most distinguishes providers; transfer of remains;
   embalming, and whether it is required for what you want; a viewing or ceremony if you want one;
   the casket range from the lowest available price, not the one you are shown first; and whether
   they will email or hand over the GPL.
   Include the sentence that does the work: "Can you email me your general price list?" Verify
   what the rule requires over the phone versus in person and state it accurately.

3. THE COMPARISON — A simple table across up to four providers, one row per line item, with a
   total that updates as items are checked or unchecked. Printable.
   The point is not the total; it is seeing that the same non-declinable basic services fee is
   $1,395 at one place and $3,200 at another, which is invisible until the numbers sit next to
   each other.
   Include a column for the low-cost options that people are not shown: direct cremation and
   immediate burial as defined categories.

4. YOUR RIGHTS — One page, each right quoted from the FTC rule or its consumer guidance, cited,
   with a retrieval date, in plain words and in [LANGUAGES]. Plus:
   - What to do if a provider will not give you a price list, and how to complain to the FTC and
     to [STATE]'s funeral regulatory board. Verify both and include phone numbers.
   - The embalming reality, stated carefully and cited: verify when it is and is not required and
     what the disclosure obligation is.
   - Whether [STATE] requires a casket for cremation, and what an alternative container is.

5. THE CHEAPER PATHS — Presented without judgment, each verified for [STATE]:
   - Direct cremation and immediate burial, and what each includes and excludes.
   - Whether [STATE] permits home funerals or family-directed disposition, and what is required.
   - Whole-body donation programs, which are usually free and which have acceptance criteria that
     must be arranged in advance.
   - Veterans burial benefits and national cemetery eligibility.
   - [COUNTY]'s indigent burial or cremation assistance, which exists in most counties, is almost
     never publicised, and has an application process worth knowing before you need it. Call and
     verify.
   - Any [STATE] crime victim compensation fund that covers funeral costs.
   - Memorial societies and nonprofit funeral consumer alliances, if any serve [COUNTY].

6. IF YOU ALREADY SIGNED — What a statement of goods and services selected is, what to check it
   against, what to do about charges you did not agree to, and how to complain. Never assert that
   a charge was improper; show the rule and the document and let them ask.

7. PLANNING AHEAD — For Walter. What to write down, where to keep it, and the honest warning
   about prepaid funeral contracts: verify [STATE]'s rules on how prepaid funds must be held,
   what happens if the provider closes or is sold, whether the contract is transferable, and what
   is refundable. This is a genuinely risky product and the app should say so plainly with
   citations rather than either recommending or condemning it.

=== DATA MODEL (local only) ===

cases: id, mode enum(now|planning), created_at
providers: id, case_id, name, phone, address, gpl_received_on, gpl_method, notes
line_items: id, provider_id, slug, label, price_cents, is_non_declinable bool, note
selections: case_id, slug, selected bool
rights: slug, body, citation, source_url, retrieved_on
resources: id, name, kind, phone, url, eligibility, verified_on, verified_by

Local-first. No account, no server.

=== STACK ===

- Local-first PWA: React + TypeScript + Vite, IndexedDB, offline, installable.
- Rights and resources as dated, sourced JSON, Zod-validated at build time; no source URL and
  retrieval date, no build.
- Money in integer cents.
- PDF via pdf-lib for the phone script and the comparison.
- No backend, no analytics, no third-party requests. Under 120KB JS.
- [LANGUAGES] from the first commit.

=== HARD CONSTRAINTS ===

- The four rights appear before any other content on the "someone has died" path and cannot be
  skipped by deep link.
- Every right is quoted with a citation and a retrieval date, displayed.
- Money in integer cents; totals recompute from selections and never round in the app's favour.
- The banned-word list fails the build.
- Everything printable; the phone script prints on one page with writing space.
- Reading level 6th grade. [LANGUAGES] everywhere.
- WCAG 2.2 AA; 18px minimum; works offline; no timeouts anywhere.

=== DO NOT BUILD ===

- No funeral home directory with ratings, reviews, or rankings. Defamation exposure, and it
  invites exactly the commercial relationships this project must not have.
- No referrals, no affiliate links, no lead generation, no sponsored placement, no advertising.
  Funeral leads are among the most valuable in local advertising and this is the one moment a
  household is least able to evaluate what it is being sold.
- No casket or merchandise sales, no partnerships with third-party retailers.
- No prepaid funeral products or insurance of any kind.
- No price database aggregated across users or scraped from providers in v1 — GPLs change,
  scraping invites a fight, and stale prices in this domain send someone somewhere on wrong
  information. The comparison holds what the user was quoted.
- No LLM generating any statement about the rule or about costs.
- No account, no cloud, no sharing platform.
- No estimate of what a funeral "should" cost.

=== ACCEPTANCE TESTS ===

1. The four rights render before any other content on the bereaved path and cannot be bypassed by
   deep link.
2. Every right has a citation with a retrieval date; one missing either fails the build.
3. The banned-word grep finds nothing in built output.
4. Totals are integer cents and recompute correctly as items are selected and deselected; a
   property test shows no drift.
5. Non-declinable items are marked as such and cannot be deselected out of a total silently —
   deselecting one shows why it cannot be removed.
6. The phone script prints on one page with space to write, in every language in [LANGUAGES].
7. The comparison prints legibly with four providers.
8. Every resource has `verified_on` and `verified_by`; one past 365 days renders "call to
   confirm."
9. No provider name is shipped in the data — the directory is empty by design and populated by
   the user.
10. The app functions fully offline including PDF export.
11. Zero third-party network requests.
12. No output contains a recommended or expected cost figure — grep test.
13. All content renders in every language in [LANGUAGES].
14. axe-core clean; readable at 200% zoom; no timeouts.

=== MILESTONES ===

M0 — The Funeral Rule, verified from the FTC directly, plus [STATE]'s additions.
  EXIT: every right quoted with its citation and retrieval date, and [STATE]'s board and the
  county's indigent assistance process confirmed by phone.

M1 — The four-rights screen and the phone script.
  EXIT: call three funeral homes yourself using your own script and ask for a GPL. Report what
  happened — whether they gave it, over what channel, and how the conversation went. That
  experience will rewrite your script.

M2 — The comparison and the rights page.
  EXIT: a funeral consumer advocacy organization, a state board staffer, or a hospice social
  worker reviews every rights statement. Do not skip this gate.

M3 — Cheaper paths, planning ahead, second language.
  EXIT: [COUNTY]'s indigent burial process confirmed by phone and written down — almost nobody
  has this in writing anywhere.

M4 — Three real users.
  EXIT: report how many called before visiting, and the spread between the highest and lowest
  basic services fee they were quoted in your city. Publish that spread.

=== SAFETY + LEGAL ===

- Not legal or financial advice. Every screen names [STATE]'s funeral board and the FTC complaint
  process, both verified.
- Quote the rule; never paraphrase a legal right. The wording is precise and the exceptions
  matter.
- Never assert that a provider violated the rule. Show the right, the citation, and what the
  person was told, and give them the complaint route.
- Do not shame any choice. Some families want a full traditional funeral and that is a legitimate
  decision made with good information; the project's goal is that it was chosen rather than
  defaulted into.
- Be careful and accurate about embalming and about whether a casket is required for cremation.
  Both are widely misunderstood in the direction that costs money, and both have real exceptions.
- Prepaid contracts: present the risks and [STATE]'s protections with citations. Do not
  recommend or condemn.
- Timing: verify and state accurately how much time a family actually has before decisions must
  be made. The perception of urgency is the pressure this app exists to relieve.
- Do not display any average-cost statistic you have not sourced with a year and a methodology.

=== HOW TO REPORT BACK ===

Lead with M1: what happened when you called three funeral homes and asked for a price list. Then:
the Funeral Rule rights with citations and retrieval dates; [STATE]'s additions; [COUNTY]'s
indigent burial process; the price spread you found; and everything you could not verify.
```

---

## Why it's shaped this way

**The first screen is four sentences and a phone button.** By the time someone is sitting in an
office looking at a casket book, the decision is largely made — the leverage is entirely in the
hour before, and most of it is knowing that the hour exists.

**The non-declinable basic services fee is the comparison that matters.** It's charged by
everyone, it varies enormously across a single city, and it is invisible until two price lists sit
next to each other. Everything else on the list is optional; that one isn't, which makes it the
cleanest apples-to-apples number available.

**M1 is calling three funeral homes yourself.** You will find out whether they hand over a GPL,
what they say when you ask by phone, and how the conversation feels — and it will rewrite the
script more than any amount of reading the rule.

**The banned word list is the tone control.** "Dignified," "deserve," "final gift" — that
vocabulary is the upsell, and a consumer tool that borrows it undermines itself.

**No directory, no ratings, no referrals.** Funeral leads are among the most valuable in local
advertising, and this is the single moment a household is least able to evaluate what it's being
sold. The comparison holds only what the user was quoted.

**Before you build:** call your county and ask what happens when a family cannot pay. Almost every
county has an indigent burial or cremation process, almost none publish it clearly, and having it
written down is worth the whole project to somebody.
