# Status

Third reference implementation from the kit. Chosen to exercise the shape nothing else here
demonstrates — a server with feed ingest, a matcher, and a durable notification pipeline — and
because that shape's failure modes (double-sends, lost messages on deploy, silent duplicate rows)
are subtle, invisible in a demo, and fully verifiable offline.

## Against the brief's milestones

| Milestone | State |
| --- | --- |
| **M0** — one source ingested idempotently into fixtures | **Half met.** Idempotency proven under repetition. The fixtures are synthetic, not captured, because egress to every feed host is blocked. |
| **M1** — the matcher and its normalizer, with a measured precision number | **Met on synthetic data.** 100% precision, 100% recall on 52 hand-labelled pairs. See VERIFY.md §1.2 for why that number is weaker than it sounds. |
| **M2** — notification with console provider, plus the review queue | **Met.** Delivery is exactly-once, restart-safe, retried, and dead-lettered with an operator alert. The review queue is built and served: one candidate at a time, three buttons, redirect-after-post. |
| **M3** — real SMS, all four sources, public page, second language | **Partly.** The public page is built and served. Real SMS, the CPSC/FSIS/NHTSA adapters, and a second language are not. |
| **M4** — twenty subscribers and a pantry, one quarter | Not started. |

## What runs

`npm run demo` — the full pipeline end to end with no network and no credentials: ingest, ingest
again (changing nothing), match with explanations, queue high-severity only, deliver, deliver
again with nothing left.

## Measured

- **35 tests passing.** Idempotent ingest, exactly-once delivery, restart safety, retry after
  transient failure, STOP cancellation, severity gating, and the normalizer.
- **`npm run eval`: 100% precision, 100% recall** on 52 labelled pairs, with a hard 95% floor
  that fails the command. One deliberate open disagreement (`p08`).

## Bugs the evaluation harness found

The matcher's first version scored **100% precision but 65.5% recall** — ten real alerts silently
downgraded to candidates, which in production means ten people not warned. Three causes:

1. **Jaccard was the wrong metric.** A notice says "Frozen Cut Green Beans 12 oz"; a subscriber
   types "frozen cut green beans". Symmetric overlap punished the notice for being specific about
   packaging and scored 0.67, then 0.5 for "salsa verde" against "Salsa Verde 16 fluid ounces".
   Replaced with containment over content tokens (numbers and units stripped), plus a minimum of
   two shared words so one common word can never be a strong match.
2. **Apostrophes became spaces.** "Ben's Best" normalized to `ben s best`, so a subscriber typing
   `bens best` matched nothing at all. Apostrophes are now deleted rather than replaced.
3. **Brand prefix matching was too strict in one direction and would have been too loose in the
   other.** "Harborline Beverages Co." had to match a recall brand of "Harborline", while "Green"
   must never match "Green Valley Farms". Resolved with a distinctiveness rule: a whole-token
   prefix matches when the shorter side is multi-word or is a single token of six or more
   characters.

None of these were visible in the demo. All three came from labelling pairs by hand and counting.

Also fixed: `node:sqlite` is not in Vite's builtin list, so vitest stripped the `node:` prefix,
tried to resolve `sqlite` from disk, and killed the whole test run before a single test
collected. A resolve plugin does not help — normalization happens first. Loaded through
`createRequire` instead, with a local interface to keep types.

## Deviations from the brief

- **SQLite via `node:sqlite`, not PostgreSQL.** The brief specifies Postgres; there is no server
  here. Every property that matters — the two unique constraints, `BEGIN IMMEDIATE` for atomic
  claiming — translates directly. Say so when you port it.
- **CPSC adapter not written**, and FSIS/NHTSA exist only as fixtures.
- **No digest and no second language.** The public page and review UI now exist.

## What worries me

That the precision number gets quoted without its caveat. It is 100% against data I invented,
labelled by the person who wrote the rules. It proves the rules are self-consistent and it will
catch regressions. It is not evidence that this would work on real recall notices, and VERIFY.md
§1.2 says so at length because that is exactly the kind of number that escapes its footnote.

Second: if real openFDA notices rarely carry a recoverable UPC, the `exact` path — the only one
that alerts with no ambiguity — is mostly decorative, and the whole system rests on brand+product
thresholds tuned against 52 synthetic pairs. That is worth finding out before anyone subscribes.
