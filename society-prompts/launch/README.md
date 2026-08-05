# The Launch Pack

24 files in `ready/`. Each one is a complete paste unit: open a new chat, paste the whole file,
and the build starts. Nothing else to set up, no repo access needed on the other end.

---

## Two minutes of setup

```sh
cd society-prompts/launch
$EDITOR LOCALE.md      # fill in at least CITY, COUNTY, STATE, STATE_ABBR, TIMEZONE, LANGUAGES
./build-pack.sh        # regenerates all 24 with your values, reports what's still blank
```

The pack in `ready/` is already generated with placeholders intact, so it works right now if you
skip this. But every `[BRACKETED]` value you leave blank is an hour the agent spends guessing at
something you know, and the whole premise of these projects is local specificity. The six core
values cover most of it.

Re-run `build-pack.sh` any time — after editing `LOCALE.md`, or after editing a brief in the
parent directory. The briefs are the source of truth; `ready/` is generated.

---

## Using one

1. Open a new chat with a coding agent, in an empty directory or a fresh repo.
2. Paste the entire contents of one `ready/*.txt` file. Not a summary of it — the whole file.
3. Let it work. It's instructed not to ask you questions before starting, to build in milestone
   order, and to stop and tell you if it hits one of the stop conditions.
4. When it stops, read the "everything I could not verify" section first. That list is the real
   output of the session.

One project per chat. They share nothing and combining them just produces a confused session.

---

## What each file contains

- **Setup** — repo name, first commit, how to work
- **The working agreement** — build in milestone order, verify every source before building on
  it, never invent an endpoint or a statistic, runs with no credentials, tests are part of the
  work, distrust clean results
- **The brief, verbatim** — everything from the original, with your locale substituted in
- **What it cannot do** — the milestones that need a phone call or a human review, and the
  instruction to write them into `VERIFY.md` rather than quietly reporting them as met
- **Deliverables and reporting** — including `VERIFY.md`, `MAINTENANCE.md`, `SOURCES.md`
- **Stop conditions** — including "somebody local already does this well, here's who"

---

## Suggested order

**Start with `16-disposal-guide.txt`.** Lowest stakes, real users the first week, and it drills
the two habits everything else depends on: verify local facts by phone, design for data going
stale. If the first session goes badly, you've learned that on a project whose worst failure is
a wasted Saturday.

Then pick by what you can actually deploy. Two useful filters:

- **Do you know someone affected?** Proximity beats a better idea every time.
- **Can you make the phone calls?** Half these projects live or die on ten calls to county
  offices, and no agent can make them.

Leave `19` (debt), `20` (utilities), `21` (special education), `02` (benefits), `04` (medical
bills), and `24` (after a death) until you have someone lined up to review the output. Each has
a milestone gated on a domain expert reading it, and each is a domain where a confidently wrong
sentence costs somebody real money or real time.

`18-directory-that-doesnt-rot.txt` is infrastructure, not a product. Run it when a directory
you already maintain has started to rot.

---

## What a session will and won't produce

**Will:** working code that runs from a clean clone with no credentials, tests against the
brief's acceptance criteria, honest measurements, and a written list of every unverified claim.

**Won't:** a tool you can hand to a stranger. Every brief's real milestones — M2 onward, mostly —
exit on things an agent cannot do: calling the county to confirm hours, walking into the
courthouse to see which door, getting a legal aid attorney to read the letter template, watching
a real person use it and counting where they stop.

So expect each session to end at roughly "M1 complete, M2 code written, human verification
pending." That is the correct outcome, not a shortfall. The `VERIFY.md` it produces is the
handoff from the part a machine can do to the part only you can — and the projects that get
finished are the ones where somebody works through that file with a phone.

Before anyone relies on any of this, run `../LAUNCH-CHECKLIST.md`.

---

## Running several at once

Fine, and the pack is built for it. Two cautions from experience with parallel work:

- **Don't start more than you can read.** Four finished projects you've reviewed beat twelve you
  haven't. The failure mode is a directory of plausible-looking apps with unverified numbers in
  them, which is precisely the outcome this whole kit is written to prevent.
- **Keep the domains separate.** Don't run the benefits screener and the medical bill auditor in
  the same week unless you have two different reviewers, because the review is the bottleneck
  and it does not parallelize.
