# 31 — Free Tax Prep + Refund Protection

**What it is:** Millions of people pay a few hundred dollars to have a simple return prepared,
and some pay again to get their own refund a week early. This finds the free option they qualify
for, and names the fees before they're charged.

**Fill in before pasting:** `[CITY]`, `[COUNTY]`, `[STATE]`, `[LANGUAGES]`, `[ORG]` (the library,
community org, or VITA site you're building with).

---

```text
You are building a free tax preparation navigator for [CITY], [COUNTY], [STATE]. Build it now; do
not ask me clarifying questions. Where you need a decision I did not make, choose the option that
keeps more of the refund with the household, state your choice, and keep going.

Read SAFETY + LEGAL before writing code. There is a line here about giving tax advice, and a
harder line about what this tool must never become a funnel to.

=== THE PEOPLE ===

Lourdes cleans offices. Her return is a W-2, a standard deduction, and the credits she qualifies
for because she has two kids. Last February she paid $280 at a storefront preparer and another
$40 for a card to get the money "fast." She did not know that free preparation exists, that the
people who do it are IRS-certified volunteers, or that her refund would have arrived at nearly
the same time.

The second person is Amos, 71, whose only income is Social Security and a small pension. He may
not need to file at all, and he has paid someone to file for six years running.

The third is a volunteer coordinator at [ORG] who runs a VITA site with more capacity than
appointments in February and a line out the door in April, because nobody knows they exist until
the last two weeks.

=== THE PROBLEM ===

Three things to research and verify from IRS sources before writing anything:

1. **The IRS Volunteer Income Tax Assistance (VITA) and Tax Counseling for the Elderly (TCE)
   programs** provide free preparation by IRS-certified volunteers, with income and complexity
   limits. Verify the current income threshold, what is in and out of scope, and how the site
   locator works.
2. **IRS Free File and any current IRS-run filing option.** These have changed repeatedly —
   verify what exists for the current filing season, what the income limits are, and which
   options are genuinely free versus free-to-start. Do not describe last season's landscape.
3. **The Earned Income Tax Credit and the Child Tax Credit** are large, refundable, and
   under-claimed. The IRS publishes participation estimates; look up the current figure with its
   year and cite it. A meaningful share of eligible households never claim the EITC, often
   because they were not required to file at all.

Also verify: the fees attached to refund advances, refund transfers, and preparer-issued cards,
and the disclosure rules that apply to them. This is where the money leaks.

=== WHAT SUCCESS LOOKS LIKE ===

Lourdes books a free appointment in early February, arrives with the right documents, keeps the
$320, and finds out she qualified for a credit she had not claimed. Amos finds out he does not
need to file.

=== BUILD THIS ===

1. WHICH FREE OPTION IS YOURS (/) — A short screener, at most seven questions, no account, no
   personal identifiers:
   household size; roughly what came in last year and from where (job, self-employment or gig
   work, Social Security, unemployment, retirement); anyone under 17; anyone in college; anyone
   65+ or with a disability; whether they own a home or a rental property; whether they have
   income from more than one state.
   Then route to the option that fits: a VITA or TCE site, IRS Free File, an IRS-run option if
   one exists this season, or — honestly — "your situation is out of scope for the free programs
   and here is what a paid preparer should cost and how to choose one."
   That last outcome is important. VITA has real scope limits (rental income, complex
   self-employment, certain investment situations), and sending someone to an appointment they
   will be turned away from wastes a morning they took off work.

2. DO YOU EVEN NEED TO FILE? — Amos's screen. Verify the current filing thresholds by age and
   status and state them with citations. Then the crucial second half: **people below the filing
   threshold often should file anyway**, because refundable credits and withheld tax are only
   returned if you file. Explain that plainly. This is the single most under-known thing in the
   domain.

3. WHAT TO BRING — A printable checklist, generated from the screener answers, in [LANGUAGES]:
   photo ID for the taxpayer and spouse; Social Security cards or ITIN letters for everyone on
   the return; all W-2s and 1099s; last year's return if they have it; bank routing and account
   numbers for direct deposit; childcare provider name, address, and tax ID; and health coverage
   forms.
   Note the rules that surprise people: both spouses generally must be present to sign a joint
   return at a VITA site, and originals of certain documents are required. Verify these.

4. THE FEE PAGE — The part that keeps the money. Plainly, with citations:
   - What a refund advance actually is, and what it costs.
   - What a "refund transfer" is — the arrangement where preparation fees are deducted from the
     refund — and what that service charges. Many people who think they paid nothing up front
     paid the most.
   - Preparer-issued prepaid cards and their fee schedules.
   - That direct deposit into the household's own account is free, and roughly how long the IRS
     says refunds take. Verify the current guidance.
   - How to check a paid preparer's credentials, and that a preparer must sign the return and
     include their PTIN. A preparer who will not sign is a serious warning sign.
   Never name a company. Describe the products.

5. THE SITE DIRECTORY — VITA and TCE sites in [COUNTY], phone-verified: address, season dates,
   hours, whether appointments or walk-ins, languages spoken, wheelchair accessibility, whether
   they do drop-off or virtual, and what they cannot handle. Each with `verified_on` and
   `verified_by`.
   The IRS publishes a site locator; use it as a starting list, then call every site, because
   season dates and appointment policies change annually and the locator lags.

6. CREDITS WORTH ASKING ABOUT — Not a calculator. A short, cited list of the refundable and
   state credits people miss, each with a one-line "you may qualify if" and an instruction to
   ask the preparer: EITC, the Child Tax Credit and the additional child tax credit, the child
   and dependent care credit, education credits, the saver's credit, and any [STATE] EITC or
   property tax circuit breaker. Research [STATE]'s own credits — several states have generous
   ones nobody claims.

7. AFTER FILING — How to check refund status through the IRS's own tool, what to do if a refund
   is smaller than expected or offset, what an IRS letter means and that most are routine, and
   the Taxpayer Advocate Service and the Low Income Taxpayer Clinic serving [COUNTY]. Verify both
   and include phone numbers. Also: what tax-related identity theft looks like and what to do.

=== DATA MODEL (local only) ===

answers: session only, in memory. Cleared when the tab closes.
sites: id, name, program enum(vita|tce|other), address, phone, season_start, season_end, hours,
  appointment_required, languages, accessible, virtual_available, out_of_scope_note,
  verified_on, verified_by
rules: id, topic, body, params jsonb, tax_year, source_url, retrieved_on, status
  enum(verified|unverified)
content: slug, body, sources jsonb, verified_on

No user data touches a server. Ever. See SAFETY.

=== STACK ===

- Static site, screener evaluated client-side. A server-side record of who asked about their
  income is not a thing to create.
- Rules and sites as dated, sourced JSON validated by Zod at build time; no source URL and
  retrieval date, no build. Every rule carries its `tax_year`.
- No backend, no analytics, no third-party requests. Under 120KB JS.
- [LANGUAGES] from the first commit. Spanish at minimum for most of the US; check ACS data for
  [COUNTY].

=== HARD CONSTRAINTS ===

- Every threshold, limit, and dollar figure carries its tax year and source, displayed inline.
  Tax figures change every single year; a stale threshold is the default failure of this whole
  category. Rules from a prior tax year render a loud banner.
- NEVER ask for or store: name, SSN or ITIN, date of birth, address, employer, or exact income.
  The screener works on ranges and yes/no answers.
- Reading level 6th grade, checked in CI. No tax jargon in the question flow — "money that came
  in," not "gross income."
- WCAG 2.2 AA; 18px minimum; everything printable; works on an old phone.
- Zero third-party requests. Someone answering questions about their income should be able to
  watch nothing leave.

=== DO NOT BUILD ===

- No tax calculator, no refund estimator, no eligibility determination for any credit. A number
  on the screen becomes an expectation, and a wrong one sends someone to an appointment angry or
  keeps them home.
- No return preparation, no form filling, no e-filing, no IRS integration.
- No LLM answering tax questions. Rules as data, cited, traceable.
- No referrals to paid preparers, no affiliate links, no lead generation, no advertising, no
  sponsored placement. **This is the hardest line in the project.** The commercial tax
  preparation industry pays well for exactly this traffic, and monetizing Lourdes at this moment
  is the whole harm the project exists to prevent.
- No refund advance products, no partnerships with any financial product.
- No account, no email capture, no "we'll remind you next January."
- No document upload of any kind.
- No naming or rating of specific preparation companies. Describe products and fees.

=== ACCEPTANCE TESTS ===

1. Completing the screener sends no network request containing any answer.
2. Every rule carries a `tax_year` and a source URL with a retrieval date; one missing either
   fails the build.
3. A rule from a prior tax year renders the stale banner and logs a startup warning.
4. A household with rental income is routed away from VITA with the out-of-scope explanation,
   not to an appointment.
5. A below-threshold household is told they may not need to file AND that filing anyway may get
   them money.
6. No SSN, ITIN, name, DOB, address, or exact-income field exists anywhere in the codebase —
   grep test.
7. The what-to-bring checklist reflects the screener answers and prints on one page.
8. The fee page names no company — grep against a list of major preparation brands.
9. Every site has `verified_on` and `verified_by`; one past 300 days (a full season) renders
   "call to confirm this season's dates."
10. Reading level at or below grade 8 for every user-facing string.
11. All content renders in every language in [LANGUAGES].
12. Zero third-party network requests during a full journey.
13. axe-core clean; full flow completable with keyboard only; readable at 200% zoom.
14. No output contains a dollar estimate of anyone's refund — grep for currency patterns in
    generated result strings.

=== MILESTONES ===

M0 — The rules research for the current tax year, before any code.
  EXIT: filing thresholds, VITA/TCE income limits and scope, current free filing options, and
  [STATE]'s own credits — each with an IRS or state revenue source and a retrieval date.

M1 — The screener and the routing, including the out-of-scope path.
  EXIT: a VITA site coordinator reads the routing logic and confirms it sends them the right
  people and turns away the wrong ones. Do not skip this gate — their scope rules are specific
  and a bad referral costs a household a work day.

M2 — What to bring, the fee page, the site directory.
  EXIT: every site called and this season's dates confirmed.

M3 — Credits list, after-filing, second language.
  EXIT: a native speaker reviews the translation; the coordinator reviews the credits list.

M4 — One filing season.
  EXIT: ask [ORG] whether appointments filled earlier in the season. That is the metric — VITA
  capacity is wasted in February and rationed in April.

=== SAFETY + LEGAL ===

- Not tax advice, not a tax preparer. On every screen, with the [COUNTY] VITA site and the Low
  Income Taxpayer Clinic, both verified by phone.
- Every figure is dated by tax year. This is the fastest-rotting content in the entire kit — the
  numbers change annually and a screener serving last year's thresholds is confidently wrong for
  twelve months. `MAINTENANCE.md` must name the month.
- Never estimate a refund or determine credit eligibility. Route to a preparer, always.
- Never ask for identifying information. Someone screening for tax help may be undocumented, may
  file with an ITIN, and may have concrete reasons to avoid creating a record. Build so there is
  no record to create, and say so.
- On ITIN filers and mixed-status households: state accurately that people file with ITINs and
  that some credits have specific identification requirements. Verify the current rules, cite
  them, and route to a Low Income Taxpayer Clinic rather than advising.
- Do not become a lead source. No referrals, no affiliates, no ads, no sponsorship. If a funder
  asks for a partnership with a preparation company, the answer is no.
- Do not display any participation or fee statistic you have not sourced with a year.

=== HOW TO REPORT BACK ===

Tell me: the tax year every rule applies to and its IRS source; what the current free filing
landscape actually is this season; VITA scope limits as the coordinator described them; which
[STATE] credits exist; which sites you confirmed by phone; and everything you could not verify.
```

---

## Why it's shaped this way

**The fee page is where the money is.** A free preparation appointment saves a couple hundred
dollars; understanding that a "refund transfer" is a loan against your own money, with a fee,
often saves more. Most people who believe they paid nothing up front paid the most, and nobody
explains the product to them.

**No refund estimator, despite it being the obvious feature.** A number on the screen becomes an
expectation, and an expectation that misses sends someone into an appointment angry at a
volunteer or keeps them home entirely.

**The out-of-scope path is a feature.** VITA cannot handle rental income and complex
self-employment, and sending someone to an appointment they'll be turned away from costs them a
day off work. Routing honestly — including to "here's what a paid preparer should cost" — is
worth more than maximizing referrals.

**No identifying information, at all.** The screener works on ranges and yes/no answers. The
intended user includes ITIN filers and mixed-status households with concrete reasons to avoid
creating a record, and the only credible way to promise that is to have no server.

**Dated by tax year, enforced.** This is the fastest-rotting content in the kit. Every figure
changes each January, and a screener quietly serving last year's thresholds is confidently wrong
for a full season.

**Before you build:** call the VITA coordinator at your library or community org and ask two
things — what their scope limits are, and when their appointments actually fill. The answers
shape both the routing and the whole point of the project.
