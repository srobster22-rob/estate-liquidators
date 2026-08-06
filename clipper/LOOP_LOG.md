# Loop Log — clipper

One entry per round. Newest at the bottom.

Format: `R<n> · <what was built> · <what it found>`

---

R1 · Built the whole vertical slice: WebVTT/SRT parsing with YouTube rolling-caption
de-duplication, utterance segmentation, a six-feature scorer, ASS caption generation with
per-word highlighting, three ffmpeg reframing layouts, a yt-dlp ingest adapter and a CLI.
149 tests, including real encodes against ffmpeg-synthesised source media.
· **Found four things, two of them real bugs:**

**(a) The candidate generator was silently biasing every clip short.** `candidates()` capped
output at 4 windows per starting utterance, and since windows are generated shortest-first,
the cap discarded exactly the candidates nearest the target length. Measured: capped pool
mean 22.0s and max 33.7s, against an uncapped mean of 36.8s and max 59.8s — with
`ideal_duration` set to 32s, the scorer was choosing from a pool that mostly *couldn't*
satisfy it. The clips looked like scorer decisions and were generator artifacts. Cap removed;
it is now opt-in with a comment explaining why it is dangerous.

**(b) The `density` feature was dead weight.** Measured across 680 candidates: sd = 0.000,
100% at ceiling. One speaker's average words-per-second barely moves across a talk, so a
band check on the mean rate is a constant — it added 1.0 to every score and could not change
a single ranking. Replaced with `pacing`, which measures the *longest internal silence*,
because what a viewer notices is not the average rate but the one gap they have to sit
through. **Still unproven:** `pacing` also has sd = 0.000 on the only fixture available,
which has no gap over 0.8s. It is tested synthetically and needs real content with dead air.

**(c) Rolling-caption de-duplication cannot be decided per cue.** The first design dropped a
repeated prefix when its timing overlapped what had already been emitted. It half-worked and
that was worse than not working: when the longest overlap failed the time test, the loop fell
through to a shorter match and deleted part of a phrase. The honest discriminator is the
*dialect*, not the cue — YouTube auto-captions carry text forward on essentially every cue,
hand-authored captions never do. Detection now happens once per file (inline `<c>` timings
are conclusive; otherwise ≥70% of adjacent pairs must overlap, over a minimum of 6 pairs),
and de-duplication only runs inside that mode, only on contiguous cues. A four-cue file where
"the starter" legitimately ends one cue and opens the next now survives intact — under the
first threshold (30%, no minimum sample) it was being eaten.

**(d) ffmpeg cannot escape an apostrophe inside a filter argument.** A path containing `'`
passed to the `subtitles` filter comes back mangled — `it's [odd]` was opened as `its [odd]`
— because inside single quotes ffmpeg treats backslash as literal, so there is no escape
sequence available. No amount of escaping fixes this. Restructured instead: the ASS file is
now written to a temp directory clipper controls rather than beside the output, so an awkward
path never reaches the filter parser. The *output* path is unaffected — it is its own argv
element and never goes near libavfilter.

Also caught by a test rather than in production: `glob_escape` corrupted its own output by
replacing `[` with `[[]` and then escaping the `]` it had just introduced. Delegated to
`glob.escape`.

**Left rough on purpose:** the download path (no network here — flagged UNVERIFIED in the
module docstring rather than pretended); `ideal_duration = 32s`, which is a guess with no
measurement behind it; and any notion of visual quality, which text cannot supply.

---

R2 · Built `framing.py`: locate the speaker by motion + detail energy on 64×36 greyscale
frames decoded through ffmpeg, in pure Python, ~0.1s per clip. Added an aimed crop
expression, a measured confidence threshold, and a `--layout auto` that crops when the
subject was found and letterboxes when it was not. 32 new tests, 181 total.
· **Found three things, and one of them invalidated a whole afternoon of measurement:**

**(a) My motion fixtures contained no motion.** Every "moving subject" fixture used
`drawbox=x='900+40*sin(2*t)'`. In `drawbox`, **`t` is thickness, not time** — and the same
command passed `t=fill`. So the expression evaluated to a constant, and every fixture was a
static box at a nonsense offset. The sinusoid appeared to work only because `sin(thickness)`
is constant per frame. Three rounds of "motion centroid is biased right" analysis were
measuring nothing. `overlay` is the filter that exposes real time; rebuilt on that, all the
numbers changed and the algorithm turned out to be correct — static subjects land within
0.008 of truth, gentle sway within 0.002. **Standing note: before trusting a synthetic
fixture, assert that it contains the thing it is supposed to contain.** A fixture that
silently degrades to a constant produces confident, wrong conclusions.

**(b) Normalising each signal to unit mass throws away whether it means anything.** Motion
and detail were each scaled to sum 1 so their shapes were comparable — which meant a motion
field consisting entirely of x264 compression noise still carried its full 0.65 weight. On a
static shot, that noise (concentrated at the left edge) was outvoting a perfectly clean
detail peak sitting exactly on the subject's two edges. Fixed by scaling each normalised
signal by its own `concentration()` — the share of mass in the heaviest quartile of columns,
rebased so uniform maps to zero. Noise is near-uniform and now contributes ~nothing; measured
reliability on a static shot went to motion 0.00 / detail 1.00, and the aim error dropped
from +0.064 to +0.008.

**(c) The confidence threshold was on the wrong side of the gap.** `MIN_CONFIDENCE` was
0.12, picked by eye. Measured across fixtures, the two populations are cleanly separated:
subjects that stay inside a crop window score 0.556–0.689, and a subject walking across the
frame scores 0.128 — *just above the threshold*, aiming at a meaningless 0.322. Moved to
0.35, in the middle of the gap. This is the one tuning constant in the project with a
measurement behind it; `ideal_duration` still is not.

**Retired D-4.** `blur` was the default only because nothing could aim a crop. That condition
was written down as its falsification, and R2 hit it. Default is now `auto`. Demonstrated:
with a subject at 82% across, the old centre crop produced a frame containing *none* of them.

**Left rough on purpose:** the aim is static per clip, so a speaker who moves mid-clip is
framed for their average position; and aiming is horizontal only, which is right for
16:9 → 9:16 and wrong for a tall source.
