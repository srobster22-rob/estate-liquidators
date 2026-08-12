# What a human has to verify

This is the handoff from what a machine could do to what only a person can. The code is done
enough to be useful; **none of it is trustworthy for a real town until the calls below are made.**

The app is built so that skipping this list is safe but useless — `jurisdiction.configured` is
`false`, so it will tell people what a thing is and why it's dangerous, and will refuse to name
a bin. Flipping that flag is what makes it start giving bin answers, so flip it last.

Ordered by how badly a wrong value hurts.

---

## Tier 1 — wrong here hurts somebody

### 1.1 Re-fetch every source and read the actual page

**Why it matters:** every hazard claim in the app rests on these, and none of them was read in
full. The build environment blocks direct fetches of `epa.gov`, `fda.gov`, `nrc.gov`, and
`dea.gov`, so all 16 sources are recorded with `method: search_index` — meaning the content was
confirmed through a search index, not by opening the page. That is weaker than it looks: search
summaries can be stale, can conflate a current page with an archived snapshot, and cannot tell
you a page's last-updated date.

**Do this:** open each URL in `SOURCES.md`. Confirm the guidance still says what the app says it
says. Then change `method:` to `fetched` in `data/sources.yaml` and update `retrieved:`.

**Watch for:** several EPA and FDA URLs in the search results were `19january2021snapshot.epa.gov`
and `archive.epa.gov` — archived snapshots of old pages. The registry deliberately uses live URLs,
but confirm each one actually resolves to a current page and not a redirect to an archive.

### 1.2 Confirm the smoke detector guidance for your state

**Why it matters:** this is the one item where the sources genuinely conflict. NRC material
indicates residential quantities of ionization smoke detectors may go in household garbage;
plenty of county programs require hazardous waste or manufacturer return; some states differ
again. The app currently says "rules differ, ask your county," which is honest but unhelpful.

**Do this:** call your county solid waste office and your state environmental agency. Get one
answer. Record it as a local rule with `verifiedBy` naming who told you.

### 1.3 Confirm propane cylinder handling, especially 1 lb camping canisters

**Why it matters:** the 20 lb grill tank has an easy answer (exchange programs). The 1 lb camping
canister is the one people actually have a bag of, and handling varies — some facilities take
them, some run special events, some refuse them outright. The current answer is generic.

**Do this:** ask your HHW facility specifically about 1 lb cylinders, by that name.

### 1.4 Every phone number in the app

**Why it matters:** a wrong number sends a frightened person to a dead end. There are currently
**zero real phone numbers in this build** — every one is a `555-01xx` demo placeholder.

**Do this:** call each number you add, before you add it. Confirm it reaches the right desk.

---

## Tier 2 — the project isn't real without these

### 2.1 M0: call every location and record what you're told

The brief's M0 exit criterion. **Not met, and cannot be met by an agent.**

For each place — county HHW facility, transfer station, hardware and electronics retailers with
take-back bins, pharmacy drop boxes, auto parts stores taking oil and batteries — ask:

1. What do you accept from households? (Read them the category list.)
2. What are your hours, including seasonal changes?
3. Do you charge? For what, how much?
4. Do I need proof of residency? What counts?
5. Any quantity limits?
6. Anything people commonly bring that you *don't* take?

Then write them into `data/locations/local.yaml` with `verifiedOn` and `verifiedBy` (a person or
a desk, not "the website"). The `/verify` screen walks you through this and emits the YAML. **Delete `data/locations/demo.yaml`** — do not edit demo rows into
real ones, so a half-finished row can never survive.

**Record how many websites were wrong.** That number is the project's whole justification and
you will want it when you ask anyone for support.

### 2.2 Time the re-check loop with somebody who is not you
`/verify` is built and the target is fifteen seconds per confirmation. Nobody has timed it. Watch
one person do ten and cut whatever makes them hesitate.

### 2.3 Ask your hauler for their contamination rate and top problem items

Cheap call, high value. It gives you the front-page number and usually your first ten additions
to the item list.

### 2.4 Fill in `data/jurisdiction.yaml`

City, county, state, hauler, timezone, languages. Set `configured: true` **only after** 2.1 is
done. The build refuses to let you set it while every location is still demo data.

### 2.5 Get the Spanish reviewed by a human

Current coverage, measured by the test suite: **names 38/38, explanatory text 3/29.** The item
names are translated; almost none of the "why" and "before you go" text is. What exists was not
written by a native speaker and has not been reviewed.

Machine translation is not acceptable for the hazard text — "tape the terminals" and "do not
puncture" have to be unambiguous. Pay someone.

---

## Tier 3 — measurements a machine couldn't take

### 3.1 Real-device load time

The byte budget is verified: **19.5KB total gzipped, 16.8KB of it JS** (`npm run check`),
against budgets of 200KB and 100KB. That is the part a machine can check.

Not checked: the brief's "answer visible within 2 seconds on Slow 4G with 4x CPU throttle" on an
actual old phone. Do it with a real cheap Android, not a simulator on a fast laptop.

### 3.2 Print it

`#/list` has a print stylesheet and is asserted to exist, but nobody has put it on paper. Print
it. Check it fits, check the fridge sheet is legible across a kitchen.

### 3.3 The M1 exit criterion: watch ten people search

Hand ten people a list of eight items and watch them type. Every zero-result is a synonym to add.
The app logs zero-result queries to `localStorage` (query text only, day-level date, nothing
else) — read them with `JSON.parse(localStorage['dg.zeroresults'])`.

Repeat until the miss rate is near zero. This is the loop that makes the app usable, and it is
the whole of M1.

---

## Unsourced claims currently in the app

The build prints these as warnings on every run. They are explanatory text on non-hazardous
items — real, widely-repeated, and not currently backed by a citation in `SOURCES.md`:

| Item | Claim needing a source |
| --- | --- |
| `plastic-bags-film` | Bags tangle in sorting machinery; facilities stop the line to cut them out |
| `shredded-paper` | Shredding shortens fibres and defeats some sorting equipment |
| `glass-containers` | Container glass, window glass, Pyrex and ceramics melt at different temperatures |
| `textiles` | Worn-out clothing has value as fibre; textile recovery is separate from donation |
| `cooking-oil` | Oil down a drain congeals and blocks sewers |

Either source them (your hauler or MRF can usually confirm the first three in one call, and they
make great "why" text when attributed to the local facility) or delete the `why`.

---

## Things deliberately not built

Named here so nobody assumes they exist:

- **No image recognition.** The brief cuts it from v1 and the reasoning holds: it would eat the
  schedule and a model that misreads a swollen lithium pouch as a AA is worse than a text box.
- **No collection-day calendar.** Needs your hauler's schedule; add it when you have the data.
- **The `/verify` screen does not write to the data files.** It cannot — there is no server. It
  emits a YAML fragment you paste and commit, which keeps the directory in git where it can be
  reviewed.
- **No server.** The report button writes to `localStorage` and tells the user to send it on.
  `UPLOAD_ENDPOINT` in `src/telemetry.ts` is `null`, which is why the app makes zero network
  requests. If you set it, point it at your own host.
- **No real locations.** See 2.1.
