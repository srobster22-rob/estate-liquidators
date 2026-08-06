# Flood, water, and what your insurance doesn't cover

Built from [`society-prompts/27-flood-and-water.md`](../society-prompts/27-flood-and-water.md).

```sh
npm install
npm run dev
```

**Read [`VERIFY.md`](VERIFY.md) before anyone relies on this.** It ships with the local layer
switched off, and its sources have not been read in full.

---

## The three facts it exists to deliver

1. **Standard homeowners and renters insurance does not cover flood.** Flood is a separate policy.
2. **A new flood policy generally takes 30 days to take effect** — so the decision has to be made
   on a dry day, not during a forecast.
3. **Water backing up through a drain is usually covered by neither.** It needs its own
   endorsement on the homeowners policy, and it is the most common uncovered basement loss.

Each is cited on the page where it appears, with the date it was checked.

## Two ideas worth stealing

**The waiting period is rendered as a date, never a duration.** "There is a 30-day waiting
period" reads as trivia. "Coverage would start 2026-09-05" reads as a deadline. The four
exceptions (mortgage, renewal change, newly-mapped, post-wildfire) are structured data with day
counts, and when two apply the *shorter* wait wins — an error in the other direction costs
somebody coverage.

**"I don't know" is never treated as "I don't have it."** Most people genuinely do not know what
is on their declarations page. An unknown renders the exact phrase to search their own PDF for
(`"water backup", "sewer", "sump"`) rather than a verdict. Only an explicit no is a confirmed gap.

## The evidence layer

`src/evidence.ts` implements the append-only hash-chained log that projects 03, 13, 19, 22 and 30
in the kit all specify and none had built. It is reusable and deliberately narrow about what it
claims:

- Entries are append-only. An edit adds a correction; both stay visible with their original times.
- Each entry hashes its own contents plus the previous entry's hash. Altering, reordering, or
  deleting an entry breaks the chain and the check reports where.
- Photo bytes are hashed **before** anything touches them and stored unmodified.
- **Camera time and import time are different things and are never conflated.** Photos forwarded
  through messaging apps lose their EXIF; where it is missing the record says "No camera
  timestamp" instead of presenting the import date as a capture date. That is the detail most
  likely to be challenged and the one most tools get wrong.
- `METHODOLOGY` is exported and printed with the record. It says what the chain does *not* prove:
  nothing about the device clock, nothing about whether the events happened, nothing verifiable
  by someone who does not trust the device. It is not a notarization. A test asserts the source
  contains no overselling language.

## Measured

37.7KB total gzipped; 9.1KB initial JS (exifr loads lazily, only when a photo is attached).
33 unit tests, 14 browser tests, axe-core clean against wcag2a/2aa/21a/21aa/22aa on all five
screens.

## Layout

```
data/sources.yaml     citation registry; SOURCES.md is generated from it
data/coverage.yaml    the waiting period as structured data, the gaps, the what-to-look-for hints
data/safety.yaml      life-safety points, mold window, prepare checklist
data/local.yaml       your city — the configured flag lives here
scripts/build-index.ts   safety gate: no insurance or life-safety claim ships without a citation
src/coverage.ts       waiting-period date math and gap assessment
src/evidence.ts       the reusable hash-chained evidence log
src/store.ts          IndexedDB blobs, explicit quota handling
```

## What it is not

Not insurance advice, not a coverage determination, not run by any insurer or agency. It explains
what policy types generally cover and tells you which words to search your own paperwork for.
