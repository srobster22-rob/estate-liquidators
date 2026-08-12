# Recall Watch

Built from [`society-prompts/35-recall-watch.md`](../society-prompts/35-recall-watch.md).

```sh
npm install
npm run demo    # full pipeline, no network, no credentials
npm run eval    # matcher precision against the labelled pairs
npm test        # 50 tests
npm run serve   # the two screens, over the fixtures, no network
```

`npm run serve` gives you `/` (the public page — current high-severity recalls, no signup) and
`/review` (the queue a coordinator works: one candidate, three buttons, no navigation). The
review screen is what makes the precision-over-recall policy possible — the matcher sends
anything ambiguous to a human, and without a screen "to a human" means "nowhere".

**`/review` needs a token and will not open without one:**

```sh
RECALL_WATCH_REVIEW_TOKEN=$(node -e "console.log(require('crypto').randomBytes(24).toString('base64url'))") npm run serve
```

Deciding a candidate sends a text message to a real person, or dismisses a recall alert so that
nobody sees it again. Before R10 both were available to anyone who could reach the port, so an
unset token now means the screen refuses to open rather than opening to everyone. The public page
needs no token and is unaffected. `npm run serve` prints a usable token if you have not set one.

**Read [`VERIFY.md`](VERIFY.md) first.** The machinery is tested; the feed data is synthetic and
no adapter has ever run against a real API.

---

## The failure mode this is designed around

Not missing a recall. **Sending fourteen texts, after which nobody reads the fifteenth** — and the
fifteenth is the listeria one.

So the matcher has three outcomes and only three:

| | | |
|---|---|---|
| `exact` | a UPC or VIN in the notice matches a watched one | alerts |
| `strong` | brand and product both match, lot codes agree or the notice names none | alerts |
| `candidate` | brand alone, a fuzzy product, or a category watch | **never alerts** — a human decides |
| *(null)* | no match | the common case, and the correct one |

Ambiguity resolves downward, severity gates the channel (only the highest class earns a text), and
`MIN_SHARED = 2` means one shared word is never a product match. There is a comment in `match.ts`
telling the next maintainer not to promote candidates automatically: if the review queue is slow,
make review faster, don't lower the bar.

## Two guarantees, both in the database

Application code that checks-then-inserts loses under concurrency and after a restart, which is
exactly when a poller double-fires:

```sql
recalls        UNIQUE (source, source_ref)          -- ingest is idempotent
notifications  UNIQUE (subscriber_id, recall_id)    -- one message per person per recall
```

Delivery claims a row before sending it. A worker killed mid-send leaves a claim that expires
after five minutes; a replacement picks it up, and `delivered` stops it going twice. All of that
is tested, including the kill.

## The evaluation harness

`data/labelled-pairs.json` holds 52 hand-labelled `(recall, watch item)` pairs. `npm run eval`
reports precision and recall on the alertable classes and **exits non-zero below 95% precision**.

It found three real matcher bugs that the demo could not — see `STATUS.md`. It is also a
self-consistency check rather than an evaluation, because the same author wrote the matcher, the
fixtures, and the labels; `VERIFY.md` §1.2 explains what a real measurement would take.

The rule for changing the matcher: **add the pair first, then change the code.**

## Layout

```
src/normalize.ts     UPC/brand/product/lot normalization — its own module, its own tests,
                     because every false positive traces back to it
src/match.ts         the three-outcome matcher, with every match recording why
src/ingest.ts        idempotent ingest
src/notify.ts        enqueue, claim, deliver — exactly once, restart-safe
src/eval.ts          the precision harness
src/sources/         RecallSource interface, FixtureSource, and an UNVERIFIED openFDA adapter
                     that refuses to run without an explicit override
fixtures/            SYNTHETIC. See fixtures/README.md.
```

## What it is not

Not health advice. Messages relay what the official notice says and link it; hazard text is never
softened. No loyalty-card or purchase-history integration — that means holding a household's
complete shopping record, and a typed list of eleven things is worth nearly as much.
