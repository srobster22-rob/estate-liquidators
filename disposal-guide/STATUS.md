# Status

Built in one session against `society-prompts/16-disposal-guide.md`.

## Where it stands against the brief's milestones

| Milestone | State |
| --- | --- |
| **M0** — 30 items, 10 locations, all phone-verified | **Not met.** 38 items built; **0 locations phone-verified**, because an agent cannot make phone calls. Exit criterion is a human task — see `VERIFY.md` §2.1. |
| **M1** — search that actually finds things | **Code complete, exit criterion not met.** Search handles synonyms, colloquialisms, brand names, misspellings, and both languages; the zero-result log is built. The exit criterion is watching ten people search, which has not happened. |
| **M2** — 120 items, full locations, re-verification workflow | **Partial.** 38 of ~120 items. The re-verification loop is now built: `/verify` walks locations oldest-first with the number as a tap-to-call link, the questions pre-written, and four outcome buttons, then emits a YAML fragment to paste into the data file. Still 0 real locations. |
| **M3** — second language, printables, collection schedule | **Partial.** Spanish scaffolding throughout; item names 38/38, explanatory text 3/29, none reviewed by a speaker. Print stylesheet done, not tested on paper. No collection calendar. |
| **M4** — real use | Not started. |

## What runs

`npm run dev` on a clean clone, no credentials, no setup. Static site, 38 items, offline after
first load.

## Measured

- **19.5KB total gzipped** (16.8KB JS, 1.7KB CSS, 0.8KB HTML), against budgets of 200KB and
  100KB. Includes the entire item database.
- **60 tests, 57 passing, 3 skipped.** The three skips are genuinely human: the 180-day
  staleness flag (needs real locations), real-device load time, and printing on paper.
- **17 browser tests passing** in real Chromium: axe-core clean against wcag2a/2aa/21a/21aa/22aa
  on all five screens, keyboard-only search-to-answer, no horizontal overflow at 200% zoom on a
  360px viewport, no cross-origin requests, and search working with the network cut.
- Search: ~0.02ms per query over the full index.

## Assumptions I made

The brief's placeholders were not filled in, so:

- **Jurisdiction is `example`, `configured: false`.** Rather than invent a town, the app ships
  with local answers disabled and says so. This turned out to be the right architecture anyway.
- **Languages assumed English + Spanish.** The brief says to pull Census ACS data for the county;
  without a county, Spanish was the defensible default. Re-derive it.
- **Locations are four fictional demo rows**, flagged `isDemo` and blocked from rendering as
  destinations. Inventing plausible-looking real places would have been the worst possible move.

## Deviations from the brief

- **Vanilla TypeScript instead of Astro or Next.js.** The brief allows either; this is a search
  box over a few hundred records and no framework fits the byte budget better. 16.8KB of JS
  including the database.
- **Own fuzzy matcher instead of Fuse.js.** The brief permits "Fuse.js or a small trie you
  write." Fuse is ~12KB gzipped; this is ~1KB and tuned for the specific misspelling case the
  brief names.

## Bugs found and fixed during the build

- **Alias collision: `aceite usado`.** Spanish for "used oil" — means both motor oil and cooking
  oil, which have opposite answers. The build-time collision check caught it; both items now
  carry qualified aliases so the bare phrase surfaces both. There's a regression test.
- **Alias collision: `monitor`** claimed by both `electronics` and `tv-crt`. CRT and flat panels
  have different answers and fees, so the disambiguating item won the word.
- **Offline was broken.** The service worker's cache fallback used `caches.match()` without
  `ignoreVary`, so a reload's navigation request missed the precached `index.html`,
  `respondWith(undefined)` threw, and the browser showed its offline error page — on an app whose
  entire premise is working in a garage with no signal. Fixed, plus a last-resort inline response.
- **Assets were only cached on the second visit.** The hand-written worker had no precache list,
  so first-load assets were fetched before the worker controlled the page. `scripts/gen-sw.ts`
  now injects the built filenames at build time.
- **A test was wrong, not the code.** `pilas` was asserted to resolve to alkaline; it's the
  generic Spanish word for batteries and correctly disambiguates. Fixed the test, kept the
  reasoning in a comment.

## What I'd cut with half the time

The `#/list` and `#/about` screens, and the Spanish scaffolding. Search, the two-layer verdict
model, and the build-time safety validation are the project; everything else is trim.

## What worries me

**That someone flips `configured: true` before doing the calls.** Every safety property in this
build routes through that flag. The build blocks the obvious mistake (turning it on while all
locations are demo), but a half-verified deployment — five real locations, sixty guessed
verdicts — would pass every check here and be exactly the confidently-wrong artifact the brief
is written against.

Second: the sources are `search_index`, not `fetched`. The hazard guidance is almost certainly
right, and "almost certainly" is not the standard this project set for itself. `VERIFY.md` §1.1.
