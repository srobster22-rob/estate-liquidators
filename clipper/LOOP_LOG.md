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
