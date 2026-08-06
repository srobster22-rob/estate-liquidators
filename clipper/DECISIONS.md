# Decisions — clipper

Every non-obvious call, why it was made, and **what would prove it wrong**. A decision with
no falsification condition is a belief.

Status: `FIRM` (reverse only on the stated condition) · `SOFT` (expected to move) ·
`OPEN` (not settled).

---

### D-1 · The scorer measures self-containment, not interest · FIRM

Ranking is built from six features that all detect *broken context* — a dangling pronoun, a
missing hook, a clip that stops mid-thought. None of them attempt to judge whether the
content is interesting.

**Why:** interest is not recoverable from a transcript, and a model that pretends otherwise
produces confident nonsense that is impossible to argue with. Self-containment is genuinely
visible in text, and it is also the failure that makes a clip unusable rather than merely
mediocre.

**Falsified by:** a set of hand-picked good clips scoring no better than random windows of
the same length. That would mean self-containment is not the binding constraint.

---

### D-2 · Rolling-caption de-duplication is a per-file mode, not a per-cue judgement · FIRM

Dialect detection runs once (inline `<c>` word timings are conclusive; otherwise ≥70% of
adjacent cue pairs must overlap by ≥2 words, over a minimum of 6 pairs). De-duplication only
runs inside that mode, and only between contiguous cues.

**Why:** the per-cue version had to distinguish carry-over from genuine repetition using
timing, and when its longest-overlap test failed it fell through to a shorter match and
deleted part of a real phrase. Half-working de-duplication is worse than none, because the
damage is invisible. See LOOP_LOG R1(c).

**Falsified by:** a real auto-caption file that overlaps on under 70% of pairs and carries no
inline timings, or a hand-authored file that overlaps on more than 70%. Either would mean the
threshold separates the wrong things.

---

### D-3 · Conservative defaults when evidence is thin · FIRM

Two instances. A file with fewer than 6 cue pairs is never assumed to be rolling. Word timings
that were interpolated disable caption highlighting entirely.

**Why:** the errors are not symmetric. Keeping a duplicated line is ugly and recoverable;
deleting speech is silent and permanent. Highlighting no word is neutral; highlighting the
*wrong* word actively misleads, because the eye tracks the highlight and notices when it lies.

**Falsified by:** users reporting duplicate text often enough to outweigh the deletion risk —
i.e. real auto-caption files that are shorter than 6 cue pairs turn out to be common.

---

### D-4 · `blur` is the default layout, not `fill` · SOFT

Centre-cropping to 9:16 (`fill`) is what most short-form content uses and generally looks
better on a centred talking head. It is not the default.

**Why:** the scorer reads text and has no idea where the subject is in frame. `fill` discards
69% of a 16:9 frame's width, so on any shot where the speaker is not centred it silently
beheads them — and nothing in the pipeline can detect that. `blur` never removes picture.
This trades fashion for not-producing-garbage, which is the right trade while the tool is
blind.

**Falsified by:** adding any face or saliency detection. The moment the crop can be aimed,
`fill` should become the default.

---

### D-5 · Candidate generation is uncapped · FIRM

`candidates()` emits every valid window; `max_per_start` exists but has no default.

**Why:** windows are generated shortest-first, so any cap truncates from the short end and
removes exactly the candidates nearest the target duration. Measured at R1: capping at 4
dropped the pool mean from 36.8s to 22.0s against a 32s target. The scorer cannot recover
what the generator never emitted. Cost is trivial — 680 candidates for a 3.5-minute talk,
scored in milliseconds.

**Falsified by:** an input where the candidate count becomes a real cost. A 3-hour podcast
would produce roughly 10⁴ candidates, which is still fine; 10⁶ would not be.

---

### D-6 · ffmpeg gets a path it can parse, rather than a cleverer escape · FIRM

The ASS subtitle file is written to a temp directory clipper controls, not next to the output.

**Why:** ffmpeg's filter argument parser cannot represent an apostrophe inside a single-quoted
value — backslash is literal there, so no escape sequence exists. This is not a bug that can
be escaped around; it is a hole in the grammar. Moving the file out of reach is the only fix
that actually holds. `is_filter_safe()` exists to catch the residual case where `TMPDIR`
itself contains an apostrophe, and raises rather than producing a silently uncaptioned clip.

**Falsified by:** ffmpeg gaining a way to pass a filter argument out-of-band (a file-based
option, or `-filter_complex_script` covering it).

---

### D-7 · Word timings are interpolated by character length, and say so · SOFT

SRT has no word timings, so words are spread across the cue weighted by length, and every such
`Word` carries `interpolated=True`.

**Why:** longer words genuinely take longer to say, so length beats uniform spacing. But it is
still a guess, and the flag is what lets `captions.py` refuse to highlight rather than lie.

**Falsified by:** measuring against a forced-alignment ground truth and finding uniform
spacing is no worse — in which case drop the weighting and keep the flag.

---

### D-8 · `ideal_duration = 32s` · OPEN

**This is a guess with nothing behind it.** It is the single least defensible number in the
project. It sits in the middle of the 15–60s band and that is the entire justification.

**Settled by:** retention data, or any published distribution of short-form clip length
against completion rate. Until then, treat every `duration_fit` contribution as arbitrary.

---

### D-9 · The download path ships unverified and labelled · FIRM

`sources.py` is written against yt-dlp's documented interface and has never been executed
against a live URL, because the environment it was built in has no route to YouTube. This is
stated in the module docstring, the README, and the log.

**Why:** the alternative is either not writing it, or writing it and implying it works. The
third option — write it, mark it — keeps the pipeline complete while making the risk
inspectable.

**Falsified by:** one real invocation. That is all it takes, and it should happen before
anything else is built on top of it.
