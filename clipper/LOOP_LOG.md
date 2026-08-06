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

---

R3 · Built `clipper/validate.py`, a label-free validation harness for the scorer:
discrimination, redundancy, ablation, and boundary sensitivity. Added a second fixture
containing real dead air. 29 new tests, 210 total.
· **Found the worst bug in the project so far, and it had been shipping since R1:**

**(a) The scorer preferred a deliberately broken clip to a clean one 72% of the time.**
Boundary sensitivity truncates a candidate's first utterance halfway through — objectively
worse, no judgement needed to label it — and asks whether the scorer notices. It did not
merely fail to notice; it *actively preferred the fragment*. Cause: `self_containment` docked
0.15 per leading discourse marker, so "Okay, so today I want to talk about…" lost 0.30 while
"the single most common reason…" — which opens mid-sentence — lost nothing. **The sign was
backwards.** A leading "so" or "okay" is evidence that this *is* a sentence start, which is
exactly what a clip opening needs. Removed the penalty (markers are still skipped when
hunting for a dangling referent) and added the signal that was actually missing: a lower-case
opening word in a transcript that otherwise capitalises sentences. 28% → 64%.

**(b) The new penalty was calibrated below the one it had to beat.** At 0.6 the mid-sentence
penalty was *smaller* than the 0.7 charged for a dangling pronoun, so "not your starter"
still beat "And it is not your starter" — a fragment outscoring a whole sentence. Raised to
the full 1.0: this feature asks whether an opening stands on its own, and a clip starting
mid-sentence does not stand at all. 64% → **76% on `talk.srt`, 95% on `pauses.srt`**.
Endings were never affected — clean beats truncated 100% of the time, both fixtures.

**(c) `pacing` was not weak, it was under-weighted — and R1's fixture had nothing for it to
find.** R1 left this open: sd = 0.000, apparently dead. Measured properly this round,
`talk.srt` contains **zero** candidates with a silence over 1.2s, so the feature could not
possibly vary on it. On `pauses.srt` it has sd = 0.471. Then ablation showed it still changed
nothing — because at weight 1.0 it was too weak to act: **a clip containing a 10.5-second
silence ranked second and would have been published.** At 3.0 it drops out of the top five.
A feature with high variance and zero effect on the decision is the failure mode that
variance alone cannot detect, which is the whole argument for ablation.

**(d) My own metric counted ties as losses.** Four features read "0% clean preferred" when
they were simply neutral to the break. Ties are now excluded from the denominator and
reported separately. A validation harness that overstates the problem is as misleading as
one that hides it.

**Also verified**, cheaply and worth doing: yt-dlp *accepts* every flag
`build_download_command` produces — it reached the network stage and failed only on the
proxy. D-9's unknown narrows from "the whole command" to "the network round-trip".

**Left rough on purpose:** boundary sensitivity is 76%, not 100%. The residual cases are
truncations that drag a hook phrase into the scored opening window. Nothing can currently
generate such a window, so it is latent — but it is exactly the kind of latent fault that
becomes live the moment someone loosens the segmenter.

---

R4 · Closed the boundary-sensitivity gap R3 left open, verified the caption-highlight path
by eye for the first time, and measured the pipeline against a 3-hour transcript.
7 new tests, 217 total. · **Found three things:**

**(a) A promise you joined halfway through was never made to you.** R3's residual 24% was one
pattern repeated 29 times: truncating a clip's opening drags a hook phrase into the scored
window, and `hook` (+0.5 × weight 3.0) outweighed the `self_contained` penalty for the broken
opening it created (−0.3 × 3.5). Both features were behaving as specified; the specification
was incoherent. `hook` is now gated on a clean sentence opening — if the clip starts
mid-sentence the viewer never received the promise, so the hook is worth zero. **76% → 100%
on `talk.srt`.**

**(b) Subtracting penalties destroys ordering at the floor.** The last 5 losses on
`pauses.srt` were decided by an *irrelevant 0.011 difference in `duration_fit`* — because
both clips scored exactly 0.0 on `self_contained` and the tiebreak fell through to noise.
"That distinction matters." loses 0.7 for the pronoun and 0.35 for being a fragment: −0.05
before the clamp. The broken version loses more, and also clamps to 0. Once two clips read as
an identical zero, the feature has stopped ranking them. Switched to **multiplicative**
composition — 1.0 × 0.3 × 0.65 = 0.195 versus a disqualified 0.0 — which never crosses zero
and keeps heavily-penalised openings distinguishable from disqualified ones. **95% → 100%.**
Boundary sensitivity is now 100% across both fixtures and both break types.

**(c) D-5's own arithmetic was 4× low.** It predicted "roughly 10⁴ candidates" for a 3-hour
podcast. Measured: 29,648 words, 3,207 utterances, **42,487 candidates**. The decision
survives — everything short of encoding runs in 5.5s, ranking being 5.3s of it, and growth is
linear because windows per start are bounded by `max_duration` — but the number in the log
was wrong and is now the measured one. Added a structural test so an accidental quadratic
never passes silently.

**Also verified:** the word-highlight caption path, rendered and inspected frame by frame for
the first time. The gold marker advances correctly word by word. R1 had only ever looked at
the *non*-highlighted path, because every fixture available then had interpolated timings —
which the code deliberately refuses to highlight.

**Left rough on purpose:** aiming is still horizontal only, and still one static aim per clip.
