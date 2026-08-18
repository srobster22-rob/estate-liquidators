# Improvement log — civic projects

Rounds over `society-prompts/` and the three built references. One line per round: what was
built, what it found. Same discipline as this repo's `LOOP_LOG.md` — pick the highest-value gap,
build it, verify by running it, reconcile anything it contradicts.

Standing rules for this loop:

- **Pick the gap the project's own `STATUS.md` or `VERIFY.md` already names.** They were written
  honestly; the top of those lists is the real backlog.
- **Verify by running.** A claim without an execution behind it does not count.
- **Distrust clean results.** A test that passes first time on a bug you were sure existed is
  usually testing the wrong thing.
- **Never loosen a failing assertion.** Find out whether the code or the test is wrong.
- **Prefer deleting duplication to adding features** — or, where duplication is deliberate, make
  drift loud.

---

## R1 — flood-and-water: offline, and the claim packet

Its own `STATUS.md` named "no service worker, so no offline" as the first thing to fix, on an app
whose emergency screen exists for when the power is out. Ported the worker from `disposal-guide`
(including its `ignoreVary` cache-lookup fix) plus the build-time precache injection, and built
the PDF claim packet that the evidence chain had been missing.

**Found:** nothing surprising — it worked as ported, which is itself the finding: the two
projects now share four files by copy, which is what R4 is about.
**Verified:** 17 browser tests, including the emergency screen loading with the network cut and
the export producing a real PDF with the methodology page in it.

## R2 — the hardening pass, applied to my own builds

Ran Pass 3 (failure paths) from `society-prompts/HARDENING-PROMPT.md` against the built projects.
Grepped every storage write for guards.

**Found a real bug.** `flood-and-water/src/store.ts` called `localStorage.setItem` unguarded. On
a full device — or in a private window, where the write throws — the entry the user had just
typed vanished with no message, on an app whose entire purpose is keeping a record somebody can
rely on months later. `disposal-guide`'s report button had the same shape.

Fixed by reporting rather than swallowing: a typed `StorageUnavailableError`, the entry kept in
memory so it can still be exported, and a banner saying it is not saved. Swallowing would have
been worse than throwing — the entry would have sat on screen looking saved until a reload.
**Verified:** a browser test that stubs `setItem` to throw and asserts the alert, the banner, the
surviving entry, and a working export.

## R3 — recall-watch: dead letters and operator alerts

Its `VERIFY.md` §2.2 said a permanently failing message sat in the table with `last_error` set
and nobody was told — so a bad number or a carrier block meant somebody silently stopped
receiving recall alerts while the dashboard looked fine. For a safety notification service that
is the worst available behaviour.

Added a five-attempt limit, a `dead_lettered_at` column, and an `OperatorSink`. A dead letter is
excluded from future claims and **is never marked delivered**, because it was not.
**Verified:** 29 tests, including that the alert fires exactly once per message, that dead
letters never re-enter the queue, and that a message succeeding before the limit never alerts.

## R4 — make the deliberate duplication loud

`sw.js`, `gen-sw.ts`, `check-budget.ts`, and `playwright.config.ts` are copied between the two
static projects. Extracting them into a shared package would be wrong: `society-prompts/launch/`
tells every agent to create a standalone repository, and a root-level dependency breaks that the
moment someone copies a project out.

So the duplication stays and `tools/check-shared-drift.mjs` makes divergence fail loudly, with a
tight per-file list of lines that *are* allowed to differ.

**Found:** one legitimate difference the first allowlist missed (preview server ports), and — on
a deliberate perturbation test — that the checker is not vacuous. It would have caught the
`ignoreVary` fix landing in one copy and not the other, which is exactly how it went the first
time.
**Verified:** 4 shared files, 0 drifted; perturb one and it fails with the file and line number.

## R5 — the budget check was measuring the wrong thing

R1's PDF export pushed `flood-and-water` from 37KB to 215KB gzipped and `check-budget.ts` failed
the build. Correct alarm, wrong number: it summed every `.js` file in `dist`, so a lazily-imported
library counted against a page that never loads it.

Two fixes. `pdf-lib` is now imported inside the export click handler, because the emergency screen
has to render offline in under two seconds and nobody reaching it is about to generate a PDF. And
the checker now reads `dist/index.html` to find what the browser actually fetches first, budgets
*that*, and reports lazy chunks separately.

**Found:** the initial payload is **9.5KB JS / 12.3KB total** for flood-and-water and 16.0KB /
18.5KB for disposal-guide, against 202KB and 1.7KB of lazy chunks respectively. The original
number was off by a factor of seventeen — measuring the wrong thing loudly is its own kind of
wrong.
**Verified:** both projects pass; 17 browser tests still pass with the export dynamically
imported; R4's drift checker forced the fix into both copies, which is exactly what it is for.

## R6 — recall-watch: the review queue, and the public page

Queue item #1. `decide()` existed and was tested; the screen did not, which meant the matcher's
central policy — send anything ambiguous to a human rather than to a phone — resolved to
"nowhere". Every candidate sat forever and the coarse category watches people rely on quietly
did nothing.

Built both server-rendered screens with no client JavaScript: `/review` shows one candidate at a
time with the recall, what the subscriber said they had, and *why the matcher flagged it*, then
three buttons and a 303 redirect so a refresh cannot re-decide. `/` is the public page — current
high-severity recalls, no signup, nothing recorded.

**Found:** two bugs, both in my own tests rather than the code. One compared a raw reason string
against escaped HTML (the escaping is correct). The other assumed the fixture set yields two
candidates when it yields one, so the "bogus decision changes nothing" check ran against an empty
queue — restructured to check before the real decision instead.
**Verified:** 35 tests, including that a decision leaves the queue and does not return, that an
invalid decision value changes nothing, that an empty queue says so rather than looking broken,
and that the public page exposes no subscriber. Plus a live smoke test over `npm run serve`.

## R7 — flood-and-water: the originals archive

Queue item #1. The PDF is for reading; an adjuster or a lawyer wants the photo files themselves,
byte-identical, with something to re-hash them against. If the bytes were resized or re-encoded
on the way out, the SHA-256 in the record would prove nothing about the file in their hands.

Wrote a ~120-line STORE-only ZIP writer rather than adding a dependency — photos are already
compressed so deflate buys nothing, and STORE means the file in the archive *is* the file. The
manifest carries every hash, the chain-check result, any photos recorded but no longer on the
device (listed, not silently dropped), and a note that `cameraTimestamp: null` does not mean the
photo was taken on the day it was added.

**Verified against `unzip` and Python's `zipfile`** — implementations that know nothing about
this writer. Self-checking an archive writer with its own reader proves only self-consistency,
which is the limitation recall-watch's eval harness had to document about itself; here an
independent tool was available, so it got used. CRC-32 checked against the standard `123456789`
value, all 256 byte values round-tripped, a 300KB file across buffer boundaries, and a unicode
filename.

**Found:** two test bugs of my own. `unzip -l` exits non-zero on an empty archive with "zipfile
is empty" — a warning about content, not corruption, and Python reads the same bytes fine; the
test had read the exit code as a structural failure. And the warning goes to stderr, not stdout,
which the first fix missed. Also strengthened the end-to-end test, which originally asserted only
the `PK` signature: it now extracts the archive with Python and checks every manifest hash
against the actual bytes, which is the claim the record makes.
**Verified:** 40 unit tests, 18 browser tests, initial JS up only 0.5KB because the writer rides
the lazily-loaded export chunk.

## R8 — disposal-guide: the re-check loop

Queue item #1. The schema had refused to ship a location without `verifiedOn` and `verifiedBy`
since the first commit, and nothing kept them true. Hours change seasonally, facilities close,
and a rotting directory is worse than none — somebody drives to a locked gate on a Saturday.

Built `/verify`: one location at a time, oldest-first with never-verified ahead of everything,
the number as a tap-to-call link, the six questions already written, and four buttons. There is
no server, so it emits a YAML fragment to paste into `data/locations/local.yaml` and commit —
which keeps the directory in git where it can be reviewed.

Two decisions worth naming. **A no-answer never updates the date** — a location nobody can reach
is a finding, not a confirmation, and the fragment says "NOT verified" instead. And **a closure
is emitted commented out**, because removing a row is a decision a person should make with their
eyes open.

**Found a real regression, in a different project.** Adding a fourth nav link pushed
`disposal-guide` into horizontal scrolling at 200% zoom on a 360px screen. The nav-wrap fix for
exactly this had landed in `flood-and-water` during R5 and never made it here — CSS is not
covered by R4's drift checker, because the two stylesheets diverged by design. The per-project
reflow test caught it, which is the right control; the drift checker now documents that
explicitly so nobody assumes CSS is covered.

Also two of my own test bugs: adding `/verify` to the shared screen list broke the "demo
locations never render as destinations" test, whose intent is about answer pages (the maintainer
screen must show demo rows, flagged) — and an assertion matched a source string against rendered
text that wraps.

**Verified:** 57 unit tests including that the emitted fragment parses as real YAML with the
`yaml` package, and 17 browser tests including the no-answer path and the refusal to record
without a name.

## R9 — flood-and-water: damaged items, calls, and receipts

Queue item #1 and the last substantial code the brief specified. Only the generic note-and-photo
entry existed; the brief also models room-by-room damaged property, a contact log, and receipts.

All three became typed entries on the *same* hash chain rather than separate stores — a receipt
is evidence in exactly the way a photo is, and splitting them would mean two things to keep
honest instead of one. A discriminator lets the PDF, the log screen, and the manifest group them
without the chain caring.

**The decision that mattered: receipts total, damaged property never does.** The brief bans claim
estimates and damage valuation, so `receiptsTotalCents()` sums receipts only, the damage form asks
what an item *cost when bought* rather than what it is worth, and every place the total appears
says it is money spent with paper kept, not money owed. Additional living expenses go unclaimed
constantly for want of exactly that total, and an appraisal is not this app's business. There is a
test asserting a $900 sofa never appears in the figure, and a note in `VERIFY.md` so a future
round does not add a "total loss" line and quietly turn a record into an appraisal.

Money is parsed to integer cents and refuses input it cannot read confidently rather than
guessing — `12.345` and `about ninety quid` are both rejected with a message, not rounded.

**Verified:** 46 unit tests including a float-drift case that would sum to 1470.0000000000002,
and 20 browser tests including that the three kinds share one verifiable chain and that an
unreadable amount is refused rather than recorded.

---

## R10 — the hardening prompt's Pass 2 and Pass 4, finally run

Every earlier round improved something the projects already did. This one ran the checklist the
kit ships to other people and had never run against its own work. `society-prompts/HARDENING-PROMPT.md`
has seven passes; R2 ran Pass 3 and nothing else. Pass 2 is privacy leaks, Pass 4 is abuse, and
both start with the same instruction: enumerate every route, call each one unauthenticated, and
read the raw response bytes rather than the rendered page.

**The finding that mattered, and it was worse than expected.** `recall-watch` grew an HTTP server
in R6. Against a running instance, with no credential of any kind:

```
POST /review/1  decision=alert        -> 303
POST /review/N  decision=not_a_match  -> 303, for N = 1..8
GET  /review                          -> "Nothing to review"
```

The obvious harm is toll fraud — a stranger queues text messages to real phone numbers, which is
the exact scenario Pass 4.2 names. The harm that actually matters is the second line. A passer-by
marked a superpotent-infant-acetaminophen recall "not a match", and the coordinator's screen then
said *Nothing to review*, which the empty-state text truthfully calls the normal state. The alert
was gone and nothing anywhere said so.

That is the failure this entire project is written to prevent. `notify.ts` dead-letters rather
than marking undelivered messages delivered, because "for a safety notification service, failing
quietly is the worst available behaviour." The one write endpoint failed quietly to anyone who
could reach the port. Reading the code did not surface it in six rounds; running one `curl` did.

**Fixed, and verified against a live server both before and after:**

- `/review` is behind a shared reviewer token (`src/auth.ts`). Unset means the screen refuses to
  open — 503 with instructions — rather than serving open, the same rule as `jurisdiction.configured`
  in the disposal guide: an unconfigured deployment is useless rather than dangerous. The public
  page is unaffected.
- The token is never in a URL (Pass 2.3: URLs reach access logs, `Referer` headers, and shared
  browser history). It is posted once to a sign-in form; the cookie holds an expiring HMAC rather
  than the secret, and is `HttpOnly; SameSite=Strict`.
- Cross-origin POSTs with a valid cookie are rejected on `Origin` as well.
- Per-client rate limiting: a hundred rapid decisions produced 29 accepted and 71 `429`s with a
  `Retry-After`. A human at the fifteen-second target never approaches it.
- A decided record is final. `decide()` used to issue a bare UPDATE, so any repeat POST silently
  replaced a coordinator's judgement with whatever arrived last. Correcting a mistake now takes a
  deliberate `overwrite`.

**A second bug, found while reading the queue rather than attacking it.** The third button says
"Can't tell — skip", and the code wrote `decision='unclear'`, which drops the record out of
`nextForReview` permanently. So the honest answer — *I don't know, let someone else look* — was
the one answer that buried a recall with nobody informed. It now defers: the record stays in the
queue, sorts behind anything nobody has seen, and tells the next person it has been passed over.

**Pass 2 on the two browser projects.** No third-party requests in any of the three (the single
external URL is the openFDA adapter, already gated behind an env var), no personal data in any
log line, and the phone number that `nextForReview` selected but never rendered is no longer
selected — Pass 2.2 is right that over-fetching is the leak whether or not the view happens to
print it, and that row was typed `[k: string]: unknown`.

**Pass 2.6 — what the export contains that the screen didn't — found the subtlest one.**
`flood-and-water` reads exactly one EXIF tag and shows a date. The originals archive then ships
the camera file untouched, and a phone photo routinely carries the coordinates it was taken at and
the device serial number. Stripping it would be the wrong fix and was rejected: the unmodified
bytes *are* the evidence, and editing them invalidates every SHA-256 in the record. What was
missing is that nobody was told. The app now checks which of those tags are present, records only
that they are present — no coordinates, no serials, ever — and asks before the archive leaves the
device: *1 of your 1 photo also contains the place it was taken.* The manifest and the methodology
page say it too, so the disclosure outlives the dialog box.

**The coverage gap underneath it.** Every photo test in the project used a file with no EXIF and
asserted the null path. The distinction the evidence layer calls load-bearing — a camera timestamp
is not an import timestamp — had never once been tested in the case where a camera timestamp
exists, and the read sits in a `try/catch` that treats any throw as "no EXIF". A break there would
have read as a confident "No camera timestamp in this file" on every photo. `test/fixtures/exif-jpeg.ts`
now builds a real JPEG with a real EXIF and GPS block, and a browser test drives it end to end.
The path turned out to work; it was untested, not broken, and it is worth saying which.

**Verified:** every new assertion was mutation-tested. Removing the auth gate, restoring the phone
to the query, restoring the dismiss-on-unclear behaviour, and dropping the `javascript:` scheme
check each turn their own test red and nothing else. Final state: recall-watch 50 tests with
matcher precision and recall both still 100%; flood-and-water 51 unit and 21 browser tests, 12.5KB
initial JS; disposal-guide 57 unit and 17 browser tests, 18.0KB; 0 shared-file drift; axe-core
clean across every screen in both browser projects.

**Still not run:** Pass 1 (data rot) needs the network. Passes 5, 6 and 7 are partly covered by
work already done — axe, zoom, contrast, the byte budget, MAINTENANCE.md — but Pass 6's honest
inventory has not been produced as the enumerated lists it asks for, and lists E and F are exactly
where this round's two worst findings came from.

---

## R11 — Pass 6, the honest inventory

The pass the hardening prompt calls "the most valuable and the most likely to be skipped", skipped
for ten rounds. Its lists E and F ask an agent to enumerate its own quiet substitutions and its own
green-but-empty tests. Output: [`PASS6-INVENTORY.md`](PASS6-INVENTORY.md), all seven lists,
unsoftened. Four real bugs came out of it.

**The worst one came from the closing question, not from the lists.** "If a real person relies on
this tomorrow, how does it hurt them?" For recall-watch the honest answer was never the matcher —
it is that no adapter has ever run against a live feed, and an upstream schema change turns the
parser's output into an empty array. `ingest` recorded that as `fetched: 0, created: 0,
error: null`. A successful run. Indistinguishable from a quiet week, forever, while every watch
list matched nothing and every dashboard read healthy. Pass 1 states the rule this broke: *a zero
displayed as data is the worst outcome — worse than an error.* A source that has produced records
and then returns none now fails the run and alerts an operator; a brand-new source returning
nothing does not, because crying wolf on a first run is how an alert channel gets muted.

**Brief acceptance test 2 was never written, and the thing it warned about was live.** The brief
says the unique constraint on (subscriber, recall) is per *recall*, so "this test must assert the
dedup behaviour you chose and document it." FDA and FSIS both announce anything containing meat;
ingest correctly kept both notices; the subscriber received **two identical texts** — the outcome
`notify.ts`'s own header calls worse than losing messages. Now a partial unique index on
(subscriber, product) suppresses the second when the notices share a UPC, a
`suppressed_notifications` row records which notice was held and which went out instead, and
where there is no shared UPC both still go out, because a wrong merge means silence and silence is
the failure this project will not trade away. My own test caught the first version of this fix
re-reporting the same suppression on every run.

**Four tests that could pass without testing what they claim.** Two `if (!row) return` guards in
recall-watch — not vacuous today, verified by making the early return throw, but one fixture change
away from turning "a human approving a candidate does queue it" into a green no-op under that
name. A disposal-guide loop with `continue` and no count, which a renamed hazard value would have
turned into "every item explains itself". A flood-and-water test whose own name admitted it
("every local resource, *if any existed*"). All now assert their preconditions.

**Every insurance statement is supposed to carry a citation; the waiting-period exceptions did
not.** Two tests enforce that rule, on the coverage gaps and the safety points. The four
exceptions — the rules that turn "not covered for a month" into "covered tomorrow", the most
consequential sentence the app says — were covered by neither, inheriting two general FEMA
citations from their parent block. They now cite individually and the build refuses to emit an
uncited one. The post-wildfire exception was re-verified against FEMA's dedicated page: its
conditions were right, and the "privately owned property" condition was missing and has been
added.

**And one wrong number in the inventory itself.** The first draft said flood-and-water's Spanish
coverage was 3/29 — that is disposal-guide's figure. Measured from the built index,
flood-and-water has no localisation structure at all: plain strings, not `{en, es}` objects, so
"add Spanish" there is a refactor rather than a translation job. Corrected in the document, with
the mistake left visible in it, because a list about unchecked numbers that contains an unchecked
number is worth exactly nothing.

**Verified:** the dedup index, the empty-feed alert and the per-exception citation requirement
were each mutation-tested — restoring the old behaviour turns its own test red and nothing else.
recall-watch 61 tests with matcher precision and recall still 100%; flood-and-water 53 unit and 21
browser; disposal-guide 57 unit and 17 browser; 0 shared-file drift.

---

## R12 — Pass 4 on the browser apps, and Pass 5 measured for the first time

R10 ran the abuse pass against the server and stopped there. R12 ran it against the two browser
apps, and ran Pass 5 — "the people it was built for" — which had never been run at all.

**The YAML that gets pasted into a safety data file could contain things nobody typed.**
`disposal-guide`'s `/verify` screen emits YAML a maintainer pastes into
`data/locations/local.yaml`, the file that decides where somebody drives with a car full of
hazardous waste. A note containing a newline escaped its `#` comment and emitted live keys:

```
#   note: ok
  hazard: none        <- emitted as real YAML
```

How real: **latent, not live.** The only input path is `<input type="text">`, and browsers strip
newlines from anything pasted into one — verified in a real browser rather than assumed. Fixed
anyway, because the function is exported and independently used, and because the field is
captioned "anything that changed" with a placeholder inviting a sentence, which is one considerate
round away from being a textarea. Values with control characters now go out double-quoted, every
comment line gets its own `#`, and the tests parse the result with the same YAML library the build
uses — a string assertion would only prove the emitter agrees with itself.

**A skipped test was hiding a feature that was never wired to the screen people see.** The 180-day
staleness test had been skipped since M0 as "needs real verified locations to exercise". That was
wrong: it needs a location with an old *date*, and one can be written in a test. The skip cost
something real — `isStale` shipped in R8 and was wired into the maintainer's re-check screen and
nowhere else, so the answer screen rendered `Confirmed 2023-04-01 by Dana` at any age with no flag
at all. Brief acceptance test 5 was unbuilt on the only path that matters. There is now a
`freshnessLine` that states elapsed time rather than a date the reader has to do arithmetic on
("Last confirmed over 3 years ago — that is out of date. Call before you go.") with the phone
number in the flag, and a deliberately source-level test asserting the answer screen uses it,
because the bug was not wrong logic — it was correct logic wired to one screen out of two.

**Pass 5: the ~6th grade reading level was a promise nobody had measured.** `scripts/reading-level.mjs`
now scores every user-facing string in the built index. Two things had to be fixed in the tool
before its output meant anything: it was scoring Spanish with Flesch–Kincaid, which is calibrated
for English and reports ordinary Spanish as difficult, and it was scoring citation titles, which
are the publisher's words and must not be rewritten.

Then the gate itself was wrong. The first version failed the build on the grade score, and the
worst offender was *"Tape over the terminals with non-conductive tape, or bag each battery
separately"* — a clear twelve-word safety instruction penalised entirely for syllables, where any
rewrite to satisfy the number would be worse. So the grade is now advisory, printed for a human to
argue with, and **the build fails on sentence length**, which is the half of the measure a writer
should actually act on. That gate immediately found a 45-word sentence about disposing of
medicine and a 37-word one about the post-wildfire exception — the latter lengthened by R11's own
fix, which added a real condition and made the sentence worse to read. Nine strings in
`disposal-guide` and four in `flood-and-water` were split into shorter sentences with no loss of
precision; the R11 test asserting every post-wildfire condition still appears still passes.
English median grade: disposal-guide 7.9 → 7.2, flood-and-water 8.5 → 7.8.

Wired into both projects' `npm run check`, duplicated per project rather than shared from
`tools/` — the launch pack tells agents to build standalone repositories and a script reaching up
to `../tools` breaks the moment one is cloned alone — and added to the drift checker, which now
covers five files.

**Verified:** the YAML escaping, the comment prefixing and the staleness wiring were each
mutation-tested; restoring the old behaviour turns its own test red and nothing else.
disposal-guide 64 unit and 17 browser tests; flood-and-water 53 unit and 21 browser;
recall-watch 61, matcher still 100%/100%; 0 drift across 5 shared files.

---

## The queue — what the next rounds should take

Ordered by value, from the projects' own VERIFY files and what R10 left open:

1. **Everything below needs money, network, or a person.** Pass 6 is done and its findings are
   fixed; what it surfaced that remains open is listed in `PASS6-INVENTORY.md` and every item
   traces back to one of those three. That is the honest state of the loop, and the inventory is
   the artifact to hand the next maintainer rather than a to-do list I can work through here.
2. **All three: second language.** Spanish scaffolding exists in two and is 3/29 complete in
   `flood-and-water`. Needs a paid human translator, not another round.
3. **recall-watch: FSIS and NHTSA adapters**, which exist only as fixtures. Needs network.
4. **recall-watch: time the review queue with a real coordinator**, and time disposal-guide's
   re-check loop. Both fifteen-second targets are unmeasured. Needs a person.
5. **Pass 1 — re-fetch every source.** Every citation in all three projects is recorded
   `method: search_index`, not `fetched`. Needs network.

Only #1 can be finished here. #2 is money, #3 and #5 need network access this environment does
not have, and #4 needs a person — worth naming so a future round does not burn an hour
rediscovering it.
