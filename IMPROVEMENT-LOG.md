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

## The queue — what the next rounds should take

Ordered by value, from the projects' own VERIFY files:

1. **All three: second language.** Spanish scaffolding exists in two and is 3/29 complete in
   `flood-and-water`. This one needs a paid human translator, not another round.
3. **recall-watch: FSIS and NHTSA adapters**, which exist only as fixtures.
4. **recall-watch: time the review queue with a real coordinator.** The fifteen-second target is
   unmeasured.
5. **flood-and-water: receipts, room-by-room items, and the contact log**, all modelled in the
   brief but only the generic note/photo entry is built.

Only #1 and #5 are code I can finish here. #2 is money, #3 needs network access this environment
does not have, and #4 needs a person — worth naming so a future round does not burn an hour
rediscovering it.
