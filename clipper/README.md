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

**Round 1. Works end to end, on local files.** 149 tests pass, including real ffmpeg encodes
against synthesised source media. The download path is written but **unverified** — the
sandbox this was built in has no route to YouTube, so `sources.py` is the one module nobody
has watched work.

## The pipeline

    transcript.load()  →  segment.segment()  →  score.rank()  →  render.render_clip()
       parse subs          find boundaries       pick moments        cut + reframe + caption

Only the two ends touch the outside world. `sources` shells out to yt-dlp and `render` shells
out to ffmpeg; everything between them is pure Python over dataclasses, which is why the hard
parts are testable without a network.

| Module | What it does |
|---|---|
| `transcript.py` | WebVTT + SRT → flat word-timed stream. Handles YouTube's rolling auto-captions. |
| `segment.py` | Words → utterances → candidate windows. Every clip starts and ends on a boundary. |
| `score.py` | Ranks candidates by six named features. Every score carries its own breakdown. |
| `captions.py` | Word-timed ASS subtitles, styled for vertical, with per-word highlighting. |
| `render.py` | ffmpeg filter graphs and encoding. Pure command construction, thin execution. |
| `sources.py` | yt-dlp / local-file ingest. **Unverified against a live URL.** |
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

## Running it

Needs Python 3.11+, `ffmpeg` and `ffprobe` on PATH, and `yt-dlp` only for URLs.

```bash
cd clipper
python3 -m unittest discover -s tests -t .      # 149 tests, ~8s
python3 -m clipper.cli --help
```

The render tests skip themselves if ffmpeg is missing rather than failing.

## Known rough edges

Ranked by how much they'd hurt:

1. **The download path has never run.** `sources.build_download_command` matches yt-dlp's
   documented flags; one real invocation would confirm or kill it.
2. **Three of six features barely discriminate** on the one fixture available. `pacing` has
   zero variance there — it needs content with real dead air to prove itself.
3. **No visual quality signal at all.** The scorer reads text and cannot tell that the speaker
   walked out of frame, so `fill` (centre crop) can behead someone silently. `blur` is the
   default for exactly this reason.
4. **`ideal_duration` is a guess**, not a measurement. 32s came from nowhere defensible.

See `LOOP_LOG.md` for what each round found, and `DECISIONS.md` for the calls that are
deliberate — each with the condition that would prove it wrong.
