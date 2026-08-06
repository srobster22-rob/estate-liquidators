# What do I do with this?

A local disposal and recycling lookup. Type "old laptop battery" and get one screen: not the
recycling bin, here's why, here's what to do before you go, and here's who takes it.

Built from [`society-prompts/16-disposal-guide.md`](../society-prompts/16-disposal-guide.md).

```sh
npm install
npm run dev      # runs on a clean clone, no credentials, no setup
```

**Before you deploy this for a real town, read [`VERIFY.md`](VERIFY.md).** It ships with local
answers switched off on purpose.

---

## The one idea

Two kinds of fact go into every answer, and the whole design is about keeping them apart.

**Universal.** A lithium battery starts fires when it's crushed. A loose needle can stick a
sanitation worker. These are true in every town, they come from federal agencies, and every one
is cited on the answer page with the date it was checked. Safe to ship.

**Local.** Which of *your* bins it goes in, which facility, what hours. Municipal, changing, and
only true after somebody phones and confirms it.

An item with universal guidance and no local rule renders an honest partial answer — the hazard,
the mechanism, the prep, and "nobody has confirmed the rule for your area, here's who to ask."
It never guesses a bin. That is why the app is useful before the phone calls and safe during them.

`jurisdiction.configured: false` is the interlock. While it's false every local verdict is
suppressed. Flip it after the calls in `VERIFY.md`, not before.

## Safety rules enforced by the build

`npm run data` refuses to emit data that could produce a dangerous answer:

- A hazard claim with no citation fails the build.
- A local rule sending a hazardous or never-curbside item to a bin fails the build. (`clampVerdict`
  enforces the same rule at runtime, so a hand-edited index can't get around it either.)
- A demo location missing its `isDemo` flag fails the build.
- A real location without `verifiedOn` and `verifiedBy` fails the build.
- Two items claiming the same search alias fails the build — this caught `aceite usado`, which
  means both used motor oil and used cooking oil.
- `configured: true` while every location is demo data fails the build.

When the app doesn't know, the answer is household hazardous waste and a phone number. Never
"trash." That is never the wrong answer, only the inconvenient one.

## Layout

```
data/
  sources.yaml          citation registry; SOURCES.md is generated from it
  jurisdiction.yaml     your town — the configured flag lives here
  items/*.yaml          38 items, universal guidance + optional local rules
  locations/demo.yaml   fictional, flagged, blocked from rendering. Delete when you add real ones.
scripts/
  build-index.ts        validation + safety gate; emits src/generated/index.json and SOURCES.md
  gen-sw.ts             injects the built asset list into the service worker precache
  check-budget.ts       asserts the byte budget against the real gzipped build
src/
  types.ts              the two-layer model, documented
  resolve.ts            verdict resolution + the runtime safety clamp
  search.ts             dependency-free fuzzy matcher (~1KB)
  main.ts               rendering and routing
test/
  acceptance.test.ts    the brief's 14 numbered criteria, in order
  browser.spec.ts       axe-core, keyboard, 200% zoom, offline, screenshots
```

## Measured

19.5KB total gzipped, database included. 42 unit tests passing, 13 browser tests passing, axe
clean on all five screens. See [`STATUS.md`](STATUS.md) for what is and isn't done, and the bugs
found on the way.

## Setting it up for your town

1. Fill in `data/jurisdiction.yaml`. Leave `configured: false`.
2. Work through `VERIFY.md` §2.1 — call every location, write down what you're told.
3. Create `data/locations/local.yaml` with real rows. Delete `demo.yaml`.
4. Add `local:` rules to items as you confirm them.
5. Set `configured: true`. Run `npm run check`.
6. Count how many websites were wrong. That's your argument for why this needed to exist.

## What this is not

Not official. Not run by any city, county, or hauler. Rules change — the app says so on every
page and tells people to call before they drive anywhere.
