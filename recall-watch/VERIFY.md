# What a human has to verify

The machinery is real and tested. The data is not. Ordered by how badly a wrong value hurts.

---

## Tier 1 — the project is not real until these are done

### 1.1 Every feed is unverified. All of them.

This environment blocks `api.fda.gov`, `www.fda.gov`, `www.fsis.usda.gov`, and every other
non-package host, so **not one line of feed code has run against a real API.**

- `src/sources/openfda.ts` was written from openFDA's published field documentation and has
  never executed. It refuses to run without `RECALL_WATCH_ALLOW_UNVERIFIED=1` for exactly that
  reason. Verify field names, pagination, rate limits, date formats, and the classification
  values, then delete the guard.
- There is **no FSIS adapter and no NHTSA adapter at all** — only fixtures shaped like their
  output. Write them.
- Everything in `fixtures/` is **synthetic**, hand-authored to match documented field shapes.
  Replace it with real captures. Until then, the precision number below describes invented data.

### 1.2 The precision number is a self-consistency check, not an evaluation

`npm run eval` reports **100% precision and 100% recall on 52 hand-labelled pairs**, with the
one remaining disagreement being non-alerting either way (`p08`, kept deliberately — see below).

That number is worth much less than it looks, and the reason is written into `src/eval.ts`: the
same author wrote the matcher, the fixtures, and the labels. It proves the rules are internally
consistent and it catches regressions. It says nothing about real recall notices.

A real measurement needs (a) real feed records and (b) labels from somebody who did not write the
matching rules. Do both before trusting a single automated alert.

**`p08` is a deliberate open disagreement.** A watch for "Green Valley Farms frozen corn" against
a green beans recall from the same brand: the label says no match, the matcher says candidate. It
was left rather than relabelled, because moving the label to fit the model is how an evaluation
set stops being useful. Decide it with a real reviewer.

### 1.3 UPCs are the whole matcher, and openFDA may not give you any

The `exact` path — the only one that alerts with no ambiguity — needs UPCs in the notice.
openFDA has no structured UPC field; where UPCs appear at all, they are inside free-text
`product_description` or `code_info`. The adapter deliberately returns `upcs: []` rather than
guessing.

Find out what fraction of real notices contain a recoverable UPC. If the answer is low, the
`strong` brand+product path carries almost all the weight and its thresholds deserve much more
scrutiny than 52 synthetic pairs gave them.

---

## Tier 2 — before anyone subscribes

### 2.1 A real SMS provider
`pickProvider()` throws if Twilio credentials are present, because no real provider is wired up.
Implement one behind the same interface and keep `ConsoleSmsProvider` working — the pipeline must
stay runnable with no credentials.

### 2.2 Operator alerting on permanent failures
A message that fails repeatedly currently sits in the table with `last_error` set and nobody is
told. `notify.ts` says so in a comment. For a safety notification service that is not acceptable:
add a threshold on `attempts` that raises an alert to a human.

### 2.3 Digest, severity classification, and the public page
Not built. Only high-severity recalls are handled; medium and low currently produce nothing at
all rather than a weekly digest. Verify FDA and FSIS classification schemes and encode them as
data rather than the string comparison in the openFDA adapter.

### 2.4 The review queue has no interface
`decide()` exists and is tested. The fifteen-second screen the brief describes does not.

---

## Tier 3 — decisions worth revisiting with real data

- **Ingest never updates an existing recall.** Notices get revised, and silently rewriting one
  people were already told about seemed worse than ignoring the revision. With real data you may
  find revisions are common and material; if so, handle them explicitly with a human in the loop.
- **The `CLAIM_TTL_MS` of five minutes** was picked, not measured. Too short and a slow provider
  gets its work stolen mid-send; too long and a crashed worker's messages sit undelivered.
- **`MIN_SHARED = 2`** means a one-word product name can never produce a `strong` match. That is
  correct for "Solace" and probably wrong for a single-word brand-and-product like "Nutella".
- **Timezone handling for digests is not implemented** — there are no digests yet.

---

## What is actually verified

Everything in `npm test` (26 tests), and it is the part that usually goes wrong silently:

- Ingest is idempotent under repetition — ten runs, one row per recall.
- Re-matching creates no duplicates and does not disturb a human's decision.
- Two matches on one recall produce exactly one notification.
- A worker killed after claiming loses nothing and duplicates nothing; the claim expires and a
  replacement worker sends exactly once.
- A transient provider failure retries and still sends exactly once.
- STOP cancels queued messages and prevents re-queueing.
- Only high-severity recalls reach SMS; candidates never send without a human decision.
- The subscriber schema holds a phone number, a language, and nothing else.
