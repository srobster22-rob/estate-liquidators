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

**Partially tested at R3.** Hand-picked labels still do not exist, but a label-free version of
the same question does: deliberately truncated windows are objectively less self-contained,
and the scorer must prefer the clean version. It now does so 76% / 95% of decided comparisons
on the two fixtures, and 100% for endings. At R1 the opening figure was 28% — i.e. the premise
of this decision was not merely untested, it was being violated.

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

**Amended at R5.** De-duplication used to additionally require the cue to start within 0.5s of
the previous one. That was wrong and it was corrupting output: carry-over is a property of the
format, not the timing, so every pause longer than the threshold duplicated a whole line
(573 words became 622 on the paired fixture). The temporal guard is replaced by a structural
one — a prefix is never dropped if it would consume the entire cue, because real rolling
captions always add new words.

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

**Falsified by:** an input where the candidate count becomes a real cost. 10⁶ would be.

**Measured at R4, and the estimate here was 4x low.** A synthetic 3-hour transcript (29,648
words, 3,207 utterances) produces **42,487** candidates, not the ~10⁴ guessed above. The
decision survives anyway: the whole pipeline short of encoding runs in 5.5s, of which ranking
is 5.3s. Growth is linear in utterance count — the windows per starting utterance are bounded
by `max_duration` — so a 10-hour input costs proportionally, not quadratically.

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

### D-8 · Clip length is not scored at all · **RESOLVED at R6, by deletion**

`duration_fit` and `ideal_duration` are gone. `--min-duration` / `--max-duration` are a hard
constraint enforced by `segment.candidates()`; inside that band the scorer has no opinion.

**Why the guess had to go rather than be improved:** measured, sweeping `ideal_duration`
across its plausible range changed **4 of 5 published clips** — 43% mean churn against under
10% for every other constant. The least justifiable number in the project was its dominant
control. Three possible justifications were tested and all failed: no evidence exists for any
target length; there is no short-clip bias to counterweight (`r(rank, duration)` = −0.00 and
−0.08 on two of three fixtures); and only 4% of candidates cluster at the band edge, so
"the edges have no slack" is too thin to carry a 40%-influence knob.

Removing it also took auto-caption boundary sensitivity from 79%/83% to **100%/100%**:
truncating a clip changes its duration, so the feature was the last channel through which
breaking a clip could improve its score.

**Reversed by:** real retention data showing a genuine length effect. Then it comes back as a
*measured* preference, and its influence gets re-checked against `parameter_sensitivity`.

---

### D-22 · A threshold belongs in a gap between populations, never inside one · FIRM

`closure` combines punctuation and silence as smooth, saturating evidence
(`gap / (gap + closing_gap)`, soft-OR'd with a sentence mark) instead of testing the gap
against a cutoff.

**Why:** the thresholded version put a kink in the function exactly at the parameter's value,
and on auto-captions `closing_gap` was 0.80 against a candidate-gap median of 0.80 — it
sliced the distribution through its own mode, 39/77, so nudging it reclassified a third of all
candidates and moved 48% of the published selection. That made it the most influential
constant in the project the moment `duration_fit` was removed. Smoothing took it to 0% on all
three fixtures with no loss of boundary sensitivity.

The contrast that makes this a rule rather than a fix: `MIN_CONFIDENCE` (D-12) is also a
threshold, and it is fine — because R2 placed it in a *measured gap between* two populations
(0.128 versus 0.556–0.689). Same instrument, opposite outcome, and the difference is entirely
whether anyone looked at the distribution first.

**Falsified by:** a signal that genuinely is bimodal at the cutoff, where a hard decision
carries information a smooth curve would blur away.

---

### D-9 · The download path ships unverified and labelled · FIRM

`sources.py` is written against yt-dlp's documented interface and has never been executed
against a live URL, because the environment it was built in has no route to YouTube. This is
stated in the module docstring, the README, and the log.

**Why:** the alternative is either not writing it, or writing it and implying it works. The
third option — write it, mark it — keeps the pipeline complete while making the risk
inspectable.

**Narrowed at R3.** yt-dlp *accepts* every flag the builder produces: invoked against a real
URL it parsed the whole command and failed only at the proxy. So argument construction is
verified and the remaining unknown is just the network round-trip and the shape of what comes
back — chiefly whether subtitle files land where `find_transcript` looks for them.

**Falsified by:** one real invocation from a machine with a route to YouTube.

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

---

### D-14 · Discourse markers carry no penalty · FIRM

A leading "so", "okay", "and", "well" costs nothing. They are still skipped over when looking
for a dangling referent, so "And that is why it works" is caught on "that".

**Why:** they used to cost 0.15 each, on the theory that they are weak openers. Measured at
R3, that penalty was the direct cause of the scorer preferring a *deliberately broken* clip
to a clean one 72% of the time — the fragment "the single most common reason…" was scored
higher than the sentence "Okay, so today I want to talk about…". The sign was backwards: in
spoken English a discourse marker is evidence that a sentence is *starting*, which is
precisely the property a clip opening needs.

**Falsified by:** viewers reporting that clips opening on "So…" read as mid-conversation. If
so the answer is a small penalty *plus* a larger mid-sentence penalty, never one without the
other.

---

### D-15 · A mid-sentence opening zeroes self-containment outright · FIRM

`MID_SENTENCE_PENALTY = 1.0`, applied when the first word is lower-case in a transcript that
capitalises at least 80% of its sentence starts.

**Why:** this feature asks whether the opening stands on its own. A clip that begins halfway
through a sentence does not stand at all, so the honest answer is zero rather than "somewhat".
At the first attempt, 0.6, it was *less* than the 0.7 charged for a dangling pronoun, so a
fragment still outscored a whole sentence. It zeroes one feature of six, so a genuinely strong
clip can still be selected.

**Falsified by:** a transcript with unreliable capitalisation slipping past the 80% floor —
heavy proper-noun or brand-name usage ("iPhone", "eBay") at sentence starts would produce
false positives.

---

### D-16 · `pacing` weight is 3.0, and the number is measured · FIRM

**Why:** at 1.0 the feature had variance but no effect. On a fixture containing real dead air,
a clip with a **10.5-second silence** in the middle ranked second and would have been
published; at 3.0 it leaves the top five. R1 had concluded pacing was dead from `talk.srt`
alone — that fixture contains *zero* candidates with a silence over 1.2s, so the feature could
not vary on it. Absence of variance in one fixture is not evidence about the feature.

**Falsified by:** content where deliberate pauses are the style — comedy, dramatic reads,
meditation — in which case a long silence is the point and this weight suppresses the best
moments.

---

### D-17 · The scorer is validated without labels, and the harness ships with the code · FIRM

`validate.py` measures discrimination, redundancy, ablation and boundary sensitivity.

**Why:** every scoring bug found in this project so far was found by measurement rather than
by reading the code — a dead feature in R1, an inverted penalty and an under-weighted feature
in R3. Ablation in particular catches the failure that variance cannot: a feature that moves
but never changes a decision. Shipping the harness alongside the scorer means the next person
to change a weight can check whether it did anything.

**Falsified by:** the harness passing cleanly while output quality is visibly bad, which would
mean the measurable properties are not the binding ones.

---

### D-18 · `hook` is gated on a clean sentence opening · FIRM

A clip that starts mid-sentence scores zero for `hook`, regardless of what its opening words
contain.

**Why:** the two features were individually reasonable and jointly incoherent. Truncating a
clip's opening pulls a hook phrase into the scored window, and the hook credit gained
(+0.5 × 3.0) exceeded the self-containment penalty for the broken opening it created
(−0.3 × 3.5) — so the scorer systematically preferred the damaged clip, 29 times out of 29 in
the residual failures. The fix is conceptual rather than numeric: a promise the viewer joined
halfway through was never made to them.

**Falsified by:** a transcript whose capitalisation is unreliable enough that
`opens_mid_sentence` misfires, which would silently zero the hook on good clips. The 80%
capitalisation floor is the guard, and it has not been tested against real auto-generated
punctuation.

---

### D-19 · Self-containment penalties compose multiplicatively · FIRM

`score *= (1 - penalty)` rather than `score -= penalty`.

**Why:** subtracting let two differently-broken openings both clamp to exactly 0.0, at which
point the feature has stopped ranking them and an irrelevant 0.011 difference in
`duration_fit` decides — which is precisely how the last five boundary-sensitivity failures
were lost. Multiplying never crosses zero, so "badly penalised" stays distinguishable from
"disqualified", and `MID_SENTENCE_PENALTY = 1.0` becomes genuinely absorbing rather than
merely large.

**Falsified by:** wanting a penalty that can be *fully* offset by another feature's strength.
Multiplication makes a 1.0 penalty unrecoverable within the feature, which is intended here
but would be wrong for a softer signal.

---

### D-20 · Silence is the auto-caption fallback for sentence starts, and only a fallback · FIRM

`opens_mid_sentence` uses capitalisation where the transcript has it, and the gap *before* the
opening where it does not. Never both.

**Why:** the mid-sentence defence built at R3/R4 depends entirely on capitals, which ASR does
not emit — so on YouTube auto-captions, the input this tool exists for, none of it was
running. Measured: 61%/78% boundary sensitivity against 100%/100% on punctuated text. Silence
is the only sentence-start signal ASR carries. It cannot be promoted to an override, because
on a punctuated transcript two sentences inside a single cue are contiguous and `gap_before`
is legitimately 0.0 at a perfectly clean boundary.

**Falsified by:** a real auto-caption file whose word gaps are distributed differently from
the synthetic fixture — which is likely, since the fixture inherits SRT cue timings. The
threshold (0.35s) is the first thing to re-measure against real ASR output.

---

### D-21 · Every positional-window feature is gated on the boundary it depends on · FIRM

`hook` scores zero when the clip opens mid-sentence; `payoff` scores zero when it ends
mid-sentence.

**Why:** both features scan a window anchored to a clip edge, so truncating that edge slides
new text into range and *raises* the score. R4 found this in `hook` — truncation made broken
clips outscore whole ones 29 times out of 29. R5 found the identical bug in `payoff`,
accounting for all 16 remaining ending failures. The generalisation is the point: a promise
you joined halfway through was never made to you, and a conclusion you were cut away from
never landed.

**The process failure is worth recording separately:** at R4 the hook bug was fixed without
asking whether the mirror feature had the mirror problem. It did, and it survived another
round. Any new edge-anchored feature must be gated at the time it is written.

**Falsified by:** a feature where the window genuinely should float free of the boundary —
for instance a topic-coherence measure over the whole clip, which has no edge to anchor to.

---

### D-23 · Word ends are inferred from the speaker's pace, not from the next word's start · FIRM

WebVTT gives word starts only. `estimate_word_ends` infers seconds-per-character from a low
quantile of the observed pace and gives each word that duration, capped by the next word's
start.

**Why:** the alternative — stretch each word until the next begins — is not a neutral reading.
It asserts that silence never occurs, which zeroes every inter-word gap in the format YouTube
actually ships. That single modelling choice disabled `pacing`, flattened `gap_before` and
`gap_after`, restricted segmentation to cue boundaries, and made `payoff` unreachable on the
entire auto-caption path. None of those symptoms pointed at the parser.

**Falsified by:** a transcript source that supplies real word end times — YouTube's `json3`
caption format does, and if clipper ever consumes it directly the estimate should be dropped
in favour of the measurement.

---

### D-24 · The sentence-pause threshold is derived per transcript, not fixed · FIRM

`segment.adaptive_gap` splits each transcript's own gap distribution by Otsu's method.
`DEFAULT_GAP = 0.65` remains only as a fallback when the distribution cannot be split.

**Why:** no single number fits every speaker. Measured, 0.65 caught **14 of 572** gaps on an
auto-caption transcript whose sentence pauses sit near 0.44, starving the segmenter of
boundaries. Deriving the threshold removes the constant rather than retuning it — the same
move as D-8, where an unjustifiable number was deleted instead of guessed better.

Two guards, both of which cost a bug to learn: the maximising bin is a *plateau* when the
populations separate cleanly, so its midpoint is taken rather than its first element; and gaps
under 1ms are numerical dust rather than silence, without which contiguous timings split into
nine times too many utterances.

**Falsified by:** a transcript whose gap distribution is genuinely unimodal — an unbroken
read with no sentence pauses — where Otsu will still return a split and there is nothing there
to find. The `MIN_GAP_THRESHOLD` floor is the current guard, and it is a threshold on a
threshold, which is not elegant.
