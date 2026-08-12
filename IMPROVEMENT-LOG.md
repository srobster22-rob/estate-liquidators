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

---

## The queue — what the next rounds should take

Ordered by value, from the projects' own VERIFY files:

1. **recall-watch: the review queue has no interface.** `decide()` exists and is tested; the
   fifteen-second screen a coordinator would actually use does not. Without it, every candidate
   match is stuck forever and the precision-over-recall design has no outlet.
2. **flood-and-water: the ZIP export of original photo bytes.** The PDF exists; a lawyer or
   adjuster wants the originals with a manifest, and the hashes are already stored.
3. **disposal-guide: the `/verify` re-verification screen.** The schema enforces
   `verifiedOn`/`verifiedBy`; the fifteen-second re-check loop that keeps them true is not built.
4. **All three: second language.** Spanish scaffolding exists in two and is 3/29 complete in
   `flood-and-water`. This one needs a paid human translator, not another round.
5. **recall-watch: FSIS and NHTSA adapters**, which exist only as fixtures.

Everything above #4 is code. #4 is money, and #5 needs network access this environment does not
have — worth naming so a future round does not burn an hour rediscovering it.
