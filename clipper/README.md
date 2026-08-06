# clipper

**Cut a long talking-head video into short vertical clips.** Point it at a video and a
transcript; it finds the moments that stand on their own, cuts them at sentence boundaries,
reframes to 9:16, and burns in captions.

```bash
python3 -m clipper.cli lesson.mp4 --dry-run          # what would it cut, and why
python3 -m clipper.cli lesson.mp4 -n 5 -o clips/     # actually cut them
python3 -m clipper.cli 'https://youtu.be/…' -n 5     # download first (see caveat below)
```

## Status

**Round 5. Works end to end, on local files.** 234 tests pass, including real ffmpeg encodes
against synthesised source media. The download path is written but **unverified** — the
sandbox this was built in has no route to YouTube, so `sources.py` is the one module nobody
has watched work.

## The pipeline

    transcript.load()  →  segment.segment()  →  score.rank()  →  render.render_clip()
       parse subs          find boundaries       pick moments        cut + reframe + caption
                                                                            ↑
                                                                     framing.aim()
                                                                   where's the subject?

Only the two ends touch the outside world. `sources` shells out to yt-dlp and `render` shells
out to ffmpeg; everything between them is pure Python over dataclasses, which is why the hard
parts are testable without a network.

| Module | What it does |
|---|---|
| `transcript.py` | WebVTT + SRT → flat word-timed stream. Handles YouTube's rolling auto-captions. |
| `segment.py` | Words → utterances → candidate windows. Every clip starts and ends on a boundary. |
| `score.py` | Ranks candidates by six named features. Every score carries its own breakdown. |
| `framing.py` | Finds *where* the subject is, so the crop can be aimed instead of assumed. |
| `captions.py` | Word-timed ASS subtitles, styled for vertical, with per-word highlighting. |
| `render.py` | ffmpeg filter graphs and encoding. Pure command construction, thin execution. |
| `sources.py` | yt-dlp / local-file ingest. **Unverified against a live URL.** |
| `validate.py` | Measures whether the scorer's features earn their weights. Finds bugs. |
| `cli.py` | Argument parsing, orchestration, JSON manifest. |

## What it is actually measuring

The scorer does **not** try to detect interesting content — it can't, from text, and pretending
otherwise would just produce confident nonsense. What it measures is **self-containment**: a
clip fails when the viewer needs context they don't have. That is visible in the transcript.

Six features, each 0–1, combined as a weighted sum:

| Feature | Fails when |
|---|---|
| `hook` | The opening promises nothing. |
| `self_contained` | It opens on "and that's why *it* works" — a pronoun with no antecedent. |
| `closure` | It stops mid-thought instead of landing. |
| `duration_fit` | Too far from the target length. |
| `pacing` | There's a long silence to sit through in the middle. |
| `payoff` | No conclusion marker near the end. |

Tune with `--weights weights.json`; `score.Weights` writes the file for you.

## Where it crops

Cropping 16:9 to 9:16 keeps about 32% of the frame's width, so taking that from the middle is
a coin flip. `framing.py` decodes a few 64×36 greyscale frames and scores each column by
**motion** (the only thing moving is usually the speaker) and **detail** (faces carry it,
walls don't) — no model, no dependencies, ~0.1s per clip.

It also reports how sure it is, which is the useful part. `--layout auto` (the default) crops
when the subject was located and letterboxes when it wasn't:

```
[1]    29.0 →    52.4  (23.4s)  12.54  [hook=1.00, …]
    subject at 83% across (confidence 0.74) -> fill
```

A speaker who walks across the frame scores near zero, falls back to `blur`, and keeps their
head. Confidence thresholds are measured, not guessed — see `DECISIONS.md` D-12.

## Arguing with the scorer

There is no labelled data, so "is the ranking good?" can't be answered directly. Four things
*can* be measured without labels, and each has caught something real:

```bash
python3 -m clipper.validate fixtures/talk.srt fixtures/pauses.srt fixtures/talk_auto.vtt
```

* **Discrimination** — does the feature vary at all? A feature pinned at its ceiling is a
  constant, and a constant cannot rank anything.
* **Redundancy** — Pearson r between features. |r| > 0.9 is one feature with two weights.
* **Ablation** — zero each weight and see whether the *published selection* changes. Stronger
  than variance: a feature can vary healthily and still never flip a decision.
* **Boundary sensitivity** — does the scorer prefer a clean clip to a deliberately broken
  one? Windows truncated mid-sentence are objectively worse and need no human labelling.

That last one found the worst bug in the project so far — the scorer *preferring* broken
clips, at R3 — and drove it from 28% to **100% on both fixtures** by R4.

## Two caption regimes, and they are not equal

`talk.srt` and `talk_auto.vtt` are a **paired** fixture — identical words and timings, one
written as clean subtitles and one as YouTube-style ASR output (lower-case, unpunctuated,
rolling carry-over). Any difference between them is caused by the caption regime alone.

| Boundary sensitivity | punctuated | auto-captions |
|---|---|---|
| clean opening preferred | **100%** | 79% |
| clean ending preferred | **100%** | 83% |

The gap is structural. Punctuation and capitals are what let the scorer tell a sentence start
from a mid-sentence cut; ASR provides neither, so it falls back to silence, which is weaker.
The CLI says so on every unpunctuated transcript rather than leaving you to find out.

Regenerate the paired fixture with `python3 fixtures/make_auto.py fixtures/talk.srt
fixtures/talk_auto.vtt`.

## Running it

Needs Python 3.11+, `ffmpeg` and `ffprobe` on PATH, and `yt-dlp` only for URLs.

```bash
cd clipper
python3 -m unittest discover -s tests -t .      # 234 tests, ~22s
python3 -m clipper.cli --help
```

The render tests skip themselves if ffmpeg is missing rather than failing.

## Known rough edges

Ranked by how much they'd hurt:

1. **The download path has never completed.** yt-dlp accepts every flag, but nothing here has
   a route to YouTube, so the round-trip is unverified — chiefly whether subtitle files land
   where `find_transcript` looks.
2. **The auto-caption fixture inherits SRT cue timings**, so gaps within a cue are exactly
   zero and the gap structure is subtitle-shaped rather than speech-shaped. The 79%/83%
   figures should be re-measured against a real auto-caption file before being trusted as
   absolutes; the *direction* is solid, the magnitude is not.
2. **No vertical aiming.** `framing.aim()` is horizontal only. Correct for 16:9 → 9:16,
   wrong for a square or already-tall source, where the interesting part of the frame may be
   above or below centre.
3. **The aim is static, one per clip.** A speaker who moves *within* the frame mid-clip is
   framed for the average of where they were. Panning is the obvious next round; today the
   fallback catches the severe cases rather than following them.
4. **`ideal_duration` is a guess**, not a measurement. 32s came from nowhere defensible.
5. **Aiming is horizontal only.** Vertical position is always the frame's centre, which is
   fine for 16:9 → 9:16 but wrong for a source that is already tall.

See `LOOP_LOG.md` for what each round found, and `DECISIONS.md` for the calls that are
deliberate — each with the condition that would prove it wrong.
