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

### D-4 · `blur` is the default layout, not `fill` · **RETIRED at R2**

Superseded by D-10. The stated falsification condition — "adding any face or saliency
detection; the moment the crop can be aimed, `fill` should become the default" — was met by
`framing.py`. Kept here because a retired decision with its trigger recorded is the evidence
that the falsification conditions are doing work rather than decorating the file.

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

---

### D-10 · The layout is chosen per clip from aim confidence, not set globally · FIRM

`--layout auto` is the default. It crops (`fill`) when `framing.aim()` located the subject,
and letterboxes (`blur`) when it did not.

**Why:** the old argument was "cropping looks better but might behead someone, so never
crop". That was correct only while the tool was blind. Once confidence exists, the question
stops being a global preference and becomes a per-clip fact — and the failure it was
protecting against is exactly the case confidence reports. Demonstrated at R2: with a subject
82% across the frame, a centred crop produced a frame containing none of them; the aimed crop
kept them whole.

**Falsified by:** confident aims that are nonetheless wrong on real footage — a busy
background that out-scores the speaker, or a two-shot where the energy centroid lands between
two people and crops both in half.

---

### D-11 · Each signal is weighted by its own concentration, not just normalised · FIRM

Motion and detail are normalised to unit mass so their shapes are comparable, then multiplied
by `concentration()` — the share of mass in the heaviest quartile of columns, rebased so
uniform maps to zero.

**Why:** unit-mass normalisation alone discards the one thing that decides whether a signal
means anything, which is how much of it there is. Measured: on a static shot the motion field
is pure x264 compression noise, and under plain normalisation it carried its full 0.65 weight
and outvoted a clean detail peak sitting exactly on the subject. With reliability weighting,
motion scores 0.00 there and the aim error fell from +0.064 to +0.008 of frame width.

**Falsified by:** footage where the true subject occupies more than a quarter of the frame's
columns and is therefore scored as "unconcentrated" — a very wide shot, or a close-up filling
the frame. The quartile is a parameter, not a law.

---

### D-12 · `MIN_CONFIDENCE = 0.35`, and it is measured · FIRM

**Why:** the two populations separate cleanly on synthesised fixtures — subjects that stay
inside a crop window score 0.556–0.689, a subject walking across the frame scores 0.128. The
previous value of 0.12 was picked by eye and sat *below* the walking case, so the worst input
was being treated as aimable and pointed somewhere meaningless. 0.35 sits in the middle of
the gap.

Noted explicitly because it is the only tuned constant in the project with a measurement
behind it. D-8 (`ideal_duration`) still has none, and the contrast is the point.

**Falsified by:** changing the analysis grid, the sample rate, or the motion/detail weights —
all three move the confidence scale, and the threshold has to be re-measured rather than
carried over.

---

### D-13 · One aim per clip, held for its whole duration · SOFT

No panning, no tracking, and horizontal only.

**Why:** a static aim fixes the severe failure (a subject who is simply not in the middle) at
trivial cost, and a wrong *moving* crop is more disorienting than a slightly wrong static one.
Subjects who move too much to frame statically are detected by confidence and letterboxed
instead, so the bad case degrades to the old safe behaviour rather than to garbage.

**Falsified by:** real footage where confident aims are common but the subject drifts enough
within a clip that the average framing is visibly wrong. That is the signal to build the
smoothed pan.
