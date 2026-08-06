# Status

Second reference implementation from the kit, built in the same session as `../disposal-guide`.
Chosen to exercise a different shape: a rules-and-dates engine plus the evidence-log pattern,
rather than search-and-lookup.

## Against the brief's milestones

| Milestone | State |
| --- | --- |
| **M0** — the three facts verified | **Partially met.** All three verified against FEMA, NFIP, and III, with the four waiting-period exceptions and their day counts. But via search index, not by reading the pages, and not confirmed by phone. See VERIFY.md §1.1–1.3. |
| **M1** — "Am I covered?" + prepare checklist | **Code complete, gate not met.** The exit criterion is an insurance agent or state consumer specialist reading every coverage statement. That has not happened. |
| **M2** — emergency screen + damage log | **Mostly built.** Emergency screen and evidence chain done and tested. Photo EXIF path built but exercised only against synthetic records, not ten real phone photos. |
| **M3** — zone lookup, local page, second language | **Not built.** FEMA egress is blocked here; an approximated flood zone is worse than none. No Spanish. |
| **M4** — one household, one season | Not started. |

## What runs

`npm run dev` on a clean clone, no credentials. Five screens: coverage assessment with the
waiting-period date, emergency, prepare checklist, damage log, about.

## Measured

- **37.7KB total gzipped**, 9.1KB initial JS. exifr (25.9KB gz) is a lazy chunk loaded only when
  a photo is attached.
- **33 unit tests, 14 browser tests, all passing.** axe-core clean on all five screens against
  wcag2a/2aa/21a/21aa/22aa; no horizontal overflow at 200% zoom on 360px; no cross-origin
  requests; the damage log survives a reload.

## Bugs found by the tests

- **Horizontal overflow at 200% zoom, twice.** First the header nav — four links with
  `flex-wrap` on the parent but not the nav itself — then the emergency `h1` at a fixed 1.9rem,
  which rendered wider than a 360px screen. Both are WCAG 1.4.10 reflow failures and neither is
  visible at normal zoom. Every oversized display string is now capped with `min(rem, vw)`.
  (My first guess at the cause was the big date, which was wrong; the element-level diagnostic
  found the real culprits.)
- **A test was wrong again.** I asserted the source contains no occurrence of "blockchain",
  which failed on the sentence "it is not a blockchain" — exactly the honesty the test was meant
  to protect. Rewritten to check for overselling *claims*, plus a second test asserting that
  blockchain and notarization appear only in negated form.

## Deviations

- **No service worker yet**, so no offline. The brief requires the emergency screen to work
  offline and it is right to. Porting `../disposal-guide/public/sw.js` (including its
  `ignoreVary` fix) is the first thing to do next.
- **No PDF/ZIP export.** The chain, the photo records, and the methodology text all exist; the
  packet that turns them into something you hand an adjuster does not.
- **English only.**

## What worries me

That someone reads the waiting-period date as authoritative. It is computed from a rule I
confirmed through a search index rather than by reading FEMA's page, and it is the single number
in this app someone would act on financially. The four exceptions make it worse, not better —
they are exactly the kind of detail that gets amended quietly. VERIFY.md §1.2 is not optional.

Second: the life-safety points are close paraphrases, not verbatim quotations. For text that
tells someone whether to drive through water, that gap should be closed before launch.
