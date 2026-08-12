# The honest inventory

Pass 6 of [`society-prompts/HARDENING-PROMPT.md`](society-prompts/HARDENING-PROMPT.md), run in R11
against `disposal-guide`, `flood-and-water`, and `recall-watch`.

The prompt calls this "the most valuable and the most likely to be skipped", and it was skipped
for ten rounds. Lists E and F ask an agent to enumerate its own quiet substitutions and its own
green-but-empty tests, which are invisible to everyone except the agent that wrote them. Both of
R10's worst findings were that shape and were stumbled into rather than looked for.

Nothing here is softened. Items fixed during R11 are marked **[fixed]**; everything unmarked is
a live limitation and belongs in the projects' `VERIFY.md` files, which it now is.

---

## A. Claims made to a user that were never verified against a primary source

**Every sourced claim in all three projects is at one remove.** Every entry in every
`sources.yaml` is recorded `method: search_index`, not `fetched`. The build environment blocks
direct egress to `epa.gov`, `fda.gov`, `fema.gov`, `nrc.gov`, `weather.gov`, and `api.fda.gov`;
a search index confirmed each page says what is claimed, but nobody opened one. Search summaries
go stale, sometimes describe an archived snapshot as if it were current, and never reveal a
page's last-updated date. This is Tier 1, item 1 in every `VERIFY.md` and it is the single
largest outstanding risk in the repository.

Specifically unverified beyond that:

| Project | Claim | Why it matters |
| --- | --- | --- |
| disposal-guide | Smoke detector disposal | The sources genuinely conflict. NRC material allows household disposal of residential ionization detectors; many county programs require HHW or manufacturer return. The app says "rules differ, ask your county", which is honest and unhelpful. |
| disposal-guide | 5 `why` strings on non-hazardous items | Bags tangling sorting machinery, shredding shortening fibres, mixed glass melt points, textile fibre value, oil congealing in sewers. All widely repeated, none cited. The build prints them as warnings on every run. |
| disposal-guide | 1 lb propane camping canisters | Handling varies by facility and the current answer is generic. This is the cylinder people actually have a bag of. |
| flood-and-water | 5 `prepare` steps | Inventory, lift-the-irreplaceable, sump backup, know-your-shutoffs, gutters and grading. Sensible, uncited; the build warns on each. |
| recall-watch | Severity mapping | The rule deciding which recalls earn a text is a string comparison in the openFDA adapter, not an encoded classification scheme from FDA and FSIS. |

**[fixed]** The four NFIP waiting-period exceptions inherited two general FEMA citations from
their parent block, so nothing said which page backed which rule. They now cite individually, the
build refuses to emit an uncited one, and the post-wildfire exception was re-verified against
FEMA's dedicated page — its conditions were right, and the "privately owned property" condition
was missing and has been added.

## B. Numbers in the codebase with no cited origin

The distinction that matters here is between a number that is a **fact about the world** and one
that is an **engineering choice**. An uncited fact is a bug. An uncited choice is fine as long as
it is honestly labelled as a choice, and dangerous when it is dressed up as a finding.

**Facts about the world.** All are cited: NFIP's 30-day waiting period and its four exceptions
(`data/coverage.yaml`, now per-exception), every hazard claim in `disposal-guide`, every safety
point in `flood-and-water`.

**Engineering choices, uncited by nature — with the honest reason for each:**

| Constant | Value | Where it came from |
| --- | --- | --- |
| `PRODUCT_STRONG` | 0.8 | Tuned against 52 hand-labelled pairs until precision hit 100%. Not a published threshold. |
| `PRODUCT_WEAK` | 0.34 | Same. Both would move if the labelled set grew. |
| `MIN_SHARED` | 2 | Chosen so one common word ("chicken") can never carry a strong match. |
| `MAX_ATTEMPTS` | 5 | Picked. Nothing measured a real carrier's transient failure rate. |
| `CLAIM_TTL_MS` | 5 min | Picked. Must exceed the longest plausible send; never measured against a real provider. |
| `STALE_AFTER_DAYS` | 180 | From the brief, which does not say where it got it. |
| `DECISION_LIMIT` / `WINDOW_MS` | 30/min | ~4× the fifteen-second human target, which is itself untimed. |
| `TOKEN_MIN_LENGTH` | 16 | A floor low enough nobody works around it, not an entropy argument. |
| `SESSION_TTL_MS` | 12 h | Picked to outlast one shift. |
| 300 characters | SMS body | Approximates two segments. Not measured against a carrier. |
| 100KB / 200KB | byte budgets | From the brief. |

The three thresholds the matcher depends on are the ones to distrust: they were fitted to 52
pairs written by the same author who wrote the matcher and the fixtures, which `VERIFY.md` Tier 1
item 2 already says is a self-consistency check rather than an evaluation.

## C. Places the app could show something confidently wrong, and the consequence

Ordered by how badly it goes for the person.

1. **disposal-guide names a real bin for a hazardous item.** Consequence: a lithium cell in a
   truck, a fire. *Guarded four ways:* the build refuses to emit a hazardous item with a curbside
   verdict, `clampVerdict()` re-checks at runtime so a hand-edited index cannot produce one,
   `jurisdiction.configured` is `false` so no bin is named at all today, and an unknown item never
   resolves to "trash".
2. **disposal-guide sends someone to a facility that has closed or changed its rules.** Consequence:
   a wasted trip with a car full of hazardous waste, and the likely outcome is that it goes in the
   bin. *Guarded:* every location is demo data flagged `NOT A REAL PLACE` and blocked from
   rendering as a destination; a browser test asserts that string never reaches a user screen.
   Unguarded once real data lands and goes stale — that is what `/verify` and the 180-day flag are
   for, and neither has been exercised against real rows.
3. **flood-and-water tells someone a waiting-period exception applies when it does not.** Consequence:
   they buy a policy believing they are covered tomorrow, and find out after the flood. *Guarded:*
   the shortest applicable exception wins only when the user answers its question affirmatively,
   the answer renders as a date rather than a duration, and R11 added a test asserting the
   post-wildfire exception states every condition that limits it.
4. **recall-watch texts someone about a recall that is not theirs.** Consequence: they throw away
   food they did not need to, and they trust the next message less. *Guarded:* precision over
   recall by design; ambiguity goes to a human; 100% precision on the labelled pairs.
5. **recall-watch stays silent about a recall that IS theirs.** The worse failure, and the harder
   one to see. *Guarded:* dead-lettering rather than false "delivered", an operator alert on
   permanent failure, a deferred record that can no longer be buried by a coordinator's "can't
   tell", a stranger who can no longer dismiss it at all (all R10), and an empty feed that now
   fails loudly instead of reporting a quiet week (R11). *Unguarded:* the adapters have never run
   against a live feed.
6. **flood-and-water overstates what its hash chain proves.** Consequence: someone leans on it in
   front of an adjuster or a judge and is embarrassed, or worse. *Guarded:* `METHODOLOGY` is
   exported with every packet and says what it does not prove; tests assert the overselling words
   appear only in negated form.

## D. Dependencies that would break these if they vanished tomorrow

| Dependency | Used by | What happens |
| --- | --- | --- |
| openFDA / FSIS / NHTSA feeds | recall-watch | The product stops working. There is no alternative source for this data and no cached fallback. This is the existential one, and no adapter has ever run against a live API. **[fixed]** A feed that silently starts returning nothing now fails the run and alerts an operator, rather than recording a clean zero. |
| `node:sqlite` | recall-watch | Still flagged experimental in Node 22, loaded through `createRequire` to work around Vite. An API change breaks the whole data layer. Mitigated by `Db` being a five-method local interface — a swap to `better-sqlite3` is a day. |
| `exifr` | flood-and-water | Photo timestamps degrade to "no camera timestamp", which is the honest fallback and already the tested path. Nothing breaks; evidentiary value drops. |
| `pdf-lib` | flood-and-water | The claim packet stops. The chain, the data, and the originals ZIP are unaffected — the ZIP writer is ~120 lines of our own code precisely so the archive does not depend on a library. |
| `zod` | disposal-guide, flood-and-water | Build-time only. Nothing ships to a user. |
| Vite / vitest / Playwright | all | Build and test only. |

Both browser apps make **zero runtime network requests** and work offline from a cold start, so
neither has a runtime third-party dependency at all. That was a design goal and it held.

## E. Spec quietly not built, or built differently than specified

The list Pass 6 exists for. Checked by reading each brief's ACCEPTANCE TESTS against the code.

**[fixed] recall-watch acceptance test 2 — the same product recalled through two feeds.** The
brief says the unique constraint on (subscriber, recall) is per *recall*, so "this test must
assert the dedup behaviour you chose and document it." Neither the test nor the documentation
existed, and the behaviour it warned about was live: FDA and FSIS both announce anything
containing meat, ingest correctly kept both notices, and the subscriber received **two identical
texts** — the outcome `notify.ts`'s own header calls worse than losing messages. Now: a partial
unique index on (subscriber, product) suppresses the second text when the notices share a UPC, a
`suppressed_notifications` row records which notice was held and which one went out instead, and
where there is no shared UPC both texts still go out because a wrong merge means silence.

**[fixed] recall-watch acceptance test 14 — public page under 60KB with JavaScript disabled.**
Never measured. It is 5.4KB and contains no `<script>` at all; both are now asserted, including a
guard so an empty page cannot pass the size check.

**Still not built, all documented in the projects' own `VERIFY.md` and `STATUS.md`:**

- **recall-watch: the digest.** `earnsSms` gates on high severity and code comments refer to a
  digest as though it exists. Medium and low severity recalls currently produce *nothing*.
- **recall-watch: messages in the subscriber's language.** The schema has a `language` column,
  `composeMessage` is English-only, and nothing reads the column. Acceptance test 10 is not met.
- **recall-watch: FSIS, NHTSA and CPSC adapters.** Fixtures only.
- **flood-and-water: the FEMA flood zone lookup.** Not implemented; egress is blocked and an
  approximated zone is worse than none.
- **flood-and-water and disposal-guide: the second language.** Not the same state in the two, and
  the difference matters. `disposal-guide` has the scaffolding and partial content — item names
  38/38, explanatory text 3/29. `flood-and-water` has **no localisation structure at all**: its
  strings are plain strings, not `{en, es}` objects, so "add Spanish" there is a refactor and not
  a translation job. Measured, not assumed — an earlier draft of this document repeated the
  disposal-guide figure for both, which is exactly the kind of unchecked number list B is about.
  Machine translation is not acceptable for hazard text in either.
- **disposal-guide: image recognition and the collection calendar.** Both explicitly cut by the
  brief, both named in `VERIFY.md` so nobody assumes they exist.

## F. Tests that pass without testing what their name says

**[fixed] `flood-and-water`: every photo test used a file with no EXIF.** Found in R10. The
distinction the evidence layer calls load-bearing — a camera timestamp is not an import timestamp
— was only ever tested in the case where there is no camera timestamp, and the read sits inside a
`try/catch` that treats any throw as "no EXIF". A break there would have shown as a confident "No
camera timestamp in this file" on every photo. There is now a hand-built EXIF+GPS JPEG fixture and
a browser test that drives the real path.

**[fixed] `flood-and-water`: "every insurance statement has a citation" did not reach the waiting
period exceptions.** Two tests enforce citations, on the coverage gaps and the safety points. The
four exceptions — the rules that turn "not covered for a month" into "covered tomorrow" — were
covered by neither.

**[fixed] `flood-and-water`: "every local resource, if any existed, would carry who verified it".**
`data.local.resources` is empty, so the loop asserted nothing. The name was at least honest about
it. Renamed, and it now asserts the unconfigured state directly so it stops being a no-op.

**[fixed] `recall-watch`: two tests with a bare `if (!row) return`.** Both currently find their
row — verified by making the early return throw — so neither is vacuous *today*. But a fixture
change that stopped producing an approvable candidate would have turned "a human approving a
candidate does queue it" into a green no-op still carrying that name. Now asserted rather than
skipped.

**[fixed] `disposal-guide`: "every hazardous item explains what to do before you go".** A loop
with `if (!u) continue` and no count. A data file that lost its hazardous items, or a renamed
hazard value, would read as every item explaining itself. Now counts what it checked.

**Weaker than they look, and left alone deliberately:** the three `it.skip`s in `disposal-guide`
are blocked on real verified locations and say so in their names. That is a documented gap rather
than a misleading test.

**The honest general caveat:** every one of these was found by looking for this specific failure
mode on purpose. R10 and R11 between them found six. The prior nine rounds, which were not
looking, found none — which says more about how invisible this class is than about the rate.

## G. The three most likely reasons these are abandoned in six months

1. **The verification work is unglamorous, unbounded, and nobody's job.** All three projects are
   built so that the code is the easy half. `disposal-guide` needs somebody to phone every
   facility and ask six questions, then re-phone them every six months forever.
   `recall-watch` needs a coordinator working a queue. The half a volunteer enjoys is finished;
   the half that never finishes has not started.
2. **The first wrong answer, and there is no one to absorb it.** Someone gets sent to a closed
   facility, or gets a text about a recall that was not theirs. On a volunteer project with no
   institution behind it, one bad outcome converts directly into "we should take this down",
   because nobody has the standing to say "this is what the error rate looks like and it is
   better than the alternative".
3. **Data rot outruns attention.** Every project here has a maintenance clock: hours and phone
   numbers, income limits and statute citations, feed schemas. `MAINTENANCE.md` files exist and
   say what to refresh and when. The failure will not be a crash — it will be an app that keeps
   answering confidently with last year's rules, which is worse than one that stops.

---

## If a real person relies on one of these tomorrow, how does it hurt them?

The closing question the hardening prompt asks, answered for each.

**disposal-guide** is the safest of the three today, precisely because it refuses to do its job:
`jurisdiction.configured` is `false`, so it will explain what a thing is and why it is dangerous
and then decline to name a bin. The realistic harm is not a wrong answer, it is a **useless** one
— somebody in a garage with a swollen battery, told only "this is hazardous, ask your county", who
puts it in the bin anyway. The moment that flag flips, the harm becomes a wrong destination, which
is why the flag is the last thing anyone should touch.

**flood-and-water** hurts someone by being believed too much. Its numbers are cited and its
methodology page is deliberately deflationary, but a person under stress will read a hash-chained
log as proof and a waiting-period date as a guarantee. The most likely real injury is somebody
buying a policy on the strength of an exception that does not apply to them and discovering it
after the water. The app now states every condition on the narrowest exception and renders a date
rather than a duration, and it still cannot stop someone reading past the conditions.

**recall-watch** hurts someone by silence. Every other failure in it is recoverable: a duplicate
text is an annoyance, a false alarm costs a jar of food. The one that matters is a real recall
that never arrives, and R10 found that a stranger on the network could cause exactly that with a
single unauthenticated POST, invisibly, on a project whose delivery layer is built around never
failing quietly.

Answering this question honestly is what produced R11's last fix. The most likely way this hurts
somebody in production was never a bug in the matcher — it is that **no adapter has ever run
against a live feed**, and an upstream schema change turns the parser's output into an empty
array. `ingest` recorded that as `fetched: 0, created: 0, error: null`: a successful run,
indistinguishable from a quiet week, forever, while every watch list matched nothing and every
dashboard read healthy. A source that has produced records and then returns none now marks the run
as failed and raises an operator alert; a brand-new source returning nothing does not, because
crying wolf on the first run is how an alert channel gets muted.

What remains is that the adapters still have not run against a live feed, and no amount of
alerting substitutes for that. It is Tier 1 in `recall-watch/VERIFY.md` and it needs network
access this environment does not have.
