# What a human has to verify

The code is done enough to be useful. None of it is trustworthy until the checks below are made.
Ordered by how badly a wrong value hurts.

`local.configured` ships `false`, so the app makes no claims about your city. Flip it last.

---

## Tier 1 — wrong here hurts somebody

### 1.1 Re-fetch every source and read the actual page
**All 9 sources are recorded `method: search_index`** — confirmed through a web search index, not
read. This environment's egress policy blocks `fema.gov`, `floodsmart.gov`, `weather.gov`,
`epa.gov`, and `iii.org` outright. Search summaries can be stale and can conflate a current page
with an archived snapshot.

Open every URL in `SOURCES.md`. Confirm the wording. Then set `method: fetched` and update
`retrieved` in `data/sources.yaml`.

### 1.2 Confirm the waiting period and its four exceptions with a human
The 30-day period and the four exceptions (mortgage, renewal change, newly-mapped, post-wildfire)
are the load-bearing facts of this entire app, and they are encoded as data that computes a date
someone will act on. Call your state insurance department's consumer line and an agent. Confirm
each exception's exact conditions and day counts.

If a private flood policy is involved rather than NFIP, the waiting period may differ. The app
currently assumes NFIP. **Verify and say so in the UI, or add it as a question.**

### 1.3 Confirm the sewer backup distinction for your state
The app says water backup is usually excluded from homeowners and generally not covered by flood
insurance either unless it results directly from a flood. State regulation and policy forms vary.
Confirm with the state insurance department before this sentence reaches anyone.

### 1.4 Quote the life-safety text from the primary page
The six emergency points are close paraphrases of NWS guidance confirmed by search index. They
must be verbatim quotations from the page, or clearly attributed paraphrase. Open
weather.gov/safety/flood-turn-around-dont-drown and weather.gov/safety/flood-during and fix the
wording to match.

---

## Tier 2 — the project isn't real without these

### 2.1 The local layer — nothing has been checked
`data/local.yaml` has zero resources. Call and record, each with `verifiedOn` and `verifiedBy`:
- County/city sandbag distribution: where, when they open, whether you bring your own bags
- The storm drain and flooded-street complaint line
- **Any municipal sewer backup reimbursement or backwater valve subsidy program.** Several cities
  run these and almost nobody publicises them. This is the highest-value local item.
- The floodplain manager, and how to get an elevation certificate
- Your state insurance department consumer line

### 2.2 Flood zone lookup is not built
The brief calls for a FEMA National Flood Hazard Layer lookup. It is not implemented, because
network egress to FEMA is blocked here and an approximated flood zone is worse than none.
Either wire it to FEMA's published service and cache the result with the date checked, or link
FEMA's own lookup — and either way keep the caveat that maps are years old and model neither
heavy-rain street flooding nor sewer surcharge.

### 2.3 The unsourced prepare steps
Five checklist items have no citation and the build warns about them on every run: `inventory`,
`lift-the-irreplaceable`, `sump-backup`, `know-your-shutoffs`, `gutters-grading`. They are
practical advice rather than claims about law or physics, which is why they warn rather than
fail. Source them or delete them.

### 2.4 Spanish
Not started. `languages: [en]`. Every other project in this kit assumes at minimum a second
language from the first commit; this one does not have it yet, and machine translation is not
acceptable for the emergency screen.

---

## Tier 3 — measurements and gaps

### 3.1 Not built, and stated so nobody assumes otherwise
- **Flood zone lookup** (2.2).
- **A second language.**

Built since this file was first written: the service worker and offline emergency screen, the PDF
claim packet, the originals ZIP with a manifest an adjuster can re-hash against, and typed entries
for damaged items, calls, and receipts — all on the same hash chain.

**One thing to watch when extending this.** Receipts total; damaged property never does. The brief
bans claim estimates and damage valuation, so `receiptsTotalCents()` sums receipts only and every
place the total appears says it is money spent, not money owed. A future round adding a "total
loss" figure would quietly turn a record into an appraisal.

### 3.2 Real device
Measured here: **37.7KB total gzipped**, 9.1KB initial JS (exifr's 25.9KB loads only when a photo
is attached). Not measured: load time on an actual cheap Android.

### 3.3 EXIF against real files
The EXIF path uses `exifr` and is exercised only by unit tests over synthetic records. Import ten
real phone photos — some straight from the camera, some forwarded through a messaging app, some
HEIC — and confirm each timestamp is correct or correctly marked missing.

### 3.4 Print
No print testing has been done on paper.
