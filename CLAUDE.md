# How to work on this project

## Reported issues come first, and they are not closed until they are verified

When the user writes an issue with the project, that issue becomes the only
work in flight.

1. **Fix it.**
2. **Verify it is actually fixed** — with the specific evidence that would
   convince a sceptic, not with "the code now says the right thing". A model
   complaint is verified with renders from several angles, not one screenshot
   at one moment of one animation. A behaviour complaint is verified by
   driving the behaviour. A layout complaint is verified at more than one
   viewport.
3. **Say plainly whether it is fixed**, and if a part of it is not, say which
   part and why.
4. **Only then** pick up anything else.

Do not open new self-directed work — audit items, backlog entries, "next
round" ideas — while a reported issue is unverified. Do not batch several
reports into one sweep and declare them all done. One at a time, closed with
evidence.

The verification tools that already exist:

- `node test.js` — the suite. 358 checks. Never leave it red.
- `node analyze.js` — per-form connectivity: is every creature ONE object?
- `bonkhorde/shot.js`, and the scratch harnesses for turntables, model sheets,
  biome sweeps and end screens. Rendering a model from six angles costs one
  command; guessing costs a round trip with the user.

## The loop

`LOOP_LOG.md` is the project's memory. One line per round:
`R<n> | <dimension> | <what changed> | <how verified> | next: <thing>`
Write it before the next round starts, not at the end of the turn.

## Ground rules

- Develop and push only on the branch named in the session brief.
- Publish the Artifact and hand over the link at the end of a round.
- Never put a model identifier in a commit message, PR, code comment or any
  other artifact that gets pushed.
