# Continuing the bot factory

Reusable prompt for the next session. Mirrors the root `ITERATION-PROMPT.md`
convention: read the record, pick one thing, try to break it, write down what
broke.

---

## Before you change anything

```bash
python bots/run.py selftest      # 50 falsification tests
python bots/run.py fpr           # false-positive rate on a structureless market: must be 0
python bots/run.py calibrate     # are the market families still realistic and findable?
```

If `fpr` returns anything other than 0 certified, stop and fix that first.
Nothing else in the lab means anything while the ladder can certify a random
walk.

Then read `bots/FINDINGS.md`. Every item in it was found by a control or a test,
not by reading code, and several were errors that made the whole search
impossible to pass (an unpassable permutation gate, a luck bar above what any
honest strategy reaches). Assume there are more of that kind still in here.

## The standing rules

1. **Never relax `GauntletConfig` to get a pass.** A bot that only survives a
   weakened gauntlet is worth less than no bot, because it will get funded. If a
   threshold is wrong, argue it from a measurement — `calibrate` for what is
   achievable, `fpr` for what the ladder lets through — and record the argument.
2. **Fix selection, not gates.** Three of the most productive fixes so far were
   in the *screen* and the *finalist rules*, which encode priors about what
   generalises. That is where priors belong. The gates are the standard of proof
   and should move only when they are provably mis-specified.
3. **Any new signal primitive must pass the lookahead scramble** —
   `test_no_lookahead_in_signals` modifies the future and requires the past not
   to move. Add the primitive, run the suite, and do not skip this because the
   function "obviously" only reads trailing windows.
4. **Any change to `markets/generate.py` needs the control markets re-checked.**
   The take-profit artifact (F6) lived in the interaction between the intrabar
   range model and the fill model, and only `control_martingale_daily` caught it.
   Re-run `fpr` after touching the generator.
5. **Refresh `vol_fix` after changing any price-process parameter**:
   `python bots/run.py calibrate --refresh-vol-fix`, then paste the constants
   into `universe.py` so they stay reviewable in a diff. But *measure before you
   refresh*: F23 found that the systematic effect of decay on realised volatility
   is 0.02-0.42% per family while the sampling noise in the constant itself is up
   to 1.9%, so re-measuring per variant injected an order of magnitude more noise
   than it removed. "Recalibrate everything you touch" is a heuristic, not a rule.
6. **Compare a market against itself with `seed_name`, never with a rename.**
   Instance seeds derive from the family name, so a renamed variant draws a fresh
   set of histories and any A/B between the two measures instance luck alongside
   the parameter that changed. Set `seed_name` to the base family and the
   comparison becomes paired; `test_paired_variants_share_their_random_stream`
   holds it.

## The highest-value things left

Roughly in order of how much they would change what the lab can claim:

1. **Find the cross-sectional control artefact.** This is now the top item, and
   it blocks the only identified route to a strategy with real room. A
   cross-sectional reversal bot earns **+0.26 gross alpha Sharpe on a basket with
   no cross-sectional effect planted** (F31) — seven standard errors from zero,
   and inside G3's +0.30 tolerance, so the current controls would wave it
   through. Four causes are ruled out: beta dispersion, `alpha_sharpe`'s beta
   correction, accidentally planted autocorrelation (measured at -0.001), and
   execution timing (invariant to `exec_delay`). It is also invariant to the
   lookback, which rules out anything proportional to turnover.

   Places not yet looked: the nonlinear per-leg transform between score and
   position (entry/exit thresholds, the rebalance band and the leverage clamp are
   applied per leg to a *demeaned* score, and a nonlinear function of a demeaned
   vector does not stay demeaned); the interaction between GARCH conditional vol
   and which legs the score selects; and the possibility that it is real
   small-sample bias in the cross-sectional demeaning at K=12, which would predict
   the artefact shrinking as K grows — cheap to test and not yet done.

   Until it is found, `xs_reversal`/`xs_momentum` stay tier 5, unreachable by any
   expansion. Do not raise the tier cap to "widen the search"; that is what the
   quarantine test exists to stop.
2. **The constructive question F30 asked is still open.** Every widening tried so
   far produces more bots at the same margin, and under a gauntlet 20% harder the
   four distinct strategies become **one**. Cross-sectional was the only candidate
   for a structurally different source of return, and it is currently blocked by
   item 1. If it stays blocked, the honest position is that this lab has one
   result and no route to a second.
3. **The permutation null's block length vs the bot's holding horizon.** F12 is
   now the sharpest open problem: a genuine edge on `eq_largecap_daily` fails G5
   because that market's 6-bar reversion halflife sits inside the null's 5-bar
   block, so the null keeps the structure the bot trades. Decide the rule **before**
   looking at which candidates it admits — tie the block to the holding horizon, or
   gate on block=1 AND block=5 — then re-run the whole search and re-measure `fpr`.
   If the new rule raises the false-positive rate above zero, it is wrong regardless
   of how attractive the bots it admits look.
4. **Real data, and a decay rate that is not a modelling choice.** `verify --data`
   already runs the identical engine, costs and permutation null on real CSVs.
   Point it at real bars for the instrument type a proven bot claims to trade.
   Expect an unimpressive permutation p-value — a single 1,200-bar out-of-sample
   window cannot establish significance for a Sharpe-0.4 edge, which is why the
   synthetic replication gates exist and why they are not sufficient. It is also
   the only route to putting the real world somewhere on F23's curve, which is the
   single largest thing this lab cannot currently do.
5. **Resolving a death confined to the last 10% of a series.** F25 tightened G2b
   to a final-quarter window and that removed three of four late-break
   certifications, but not the fourth: the quarter still contains 10 percentage
   points of pre-break data against 15 post-break. A shorter window is too noisy
   to gate on directly. The interesting version is a *changepoint* statistic
   rather than a shorter window — test whether the late alpha series has a break
   in it, not whether its average is high.
6. **Search the other rungs.** F27 ran the loop against `hl=0.25x` and found
   nothing in 16,375 candidates. `hl=1.00x` and `break@85%` have never been
   searched, only paneled. `break@85%` is the interesting one: the panel certifies
   one strategy there, and a search might find that a *late* break is the easiest
   non-stationarity to survive — which would be a real design principle, since it
   is also the one a live trader has the least warning of.
7. **What would a search find that the panel cannot represent?** F27 answers this
   for one rung. The general version — is the strategy space searched here wide
   enough that "nothing certified" means "nothing is there" — is answered only by
   widening it. Cross-sectional strategies (below) are the biggest missing class.
8. **Dependent intrabar extremes.** Max and min are currently sampled
   independently from the Brownian bridge; they are negatively dependent. The
   residual +0.07 gross alpha that take-profit-only bots still show on a random
   walk is the visible size of that approximation.
9. **The archetype panel is better but still not neutral.** F23 found and closed
   two blank columns in it — no archetype used `proportional` sizing, and none
   carried a filter, though every certified strategy uses the first. Assume there
   are more holes of that kind. The test for one: take any axis of `SearchSpace`
   and ask which of its values the panel never exercises.

**Done, for reference:** the decay curve (F23), the cost-leverage experiment
(F24 — it *falsified* F21's ratio claim), the late-break blind spot in G2b (F25),
the closing-standard recheck (F26), the searched 12-year catalogue and the
ten-probe FPR bound (F27), the searched late-break catalogue and per-gate margins
(F28, F29), and the non-stationary families (F20).

Useful commands added along the way:

```bash
python bots/run.py decay                            # the survival curve over fade rates
python bots/run.py costgrid                         # sweep edge and cost independently
python bots/run.py fpr --repeats 10                 # a tight bound, not a single probe
python bots/run.py loop --catalogue hl=0.25x        # search a decay rung
python bots/run.py revalidate                       # re-judge the ledger at the closing bar
```

## What a good session looks like

Pick one item. Build the smallest thing that could falsify a claim the lab
currently makes. Run it. If it breaks something, fix the cause rather than the
symptom, and add the test that would have caught it. Append what you found to
`FINDINGS.md` in the same voice as the existing entries: what was wrong, how it
was caught, what the numbers were before and after.

If a session ends with "I found nothing wrong", that is a weaker result than
finding a bug, and probably means the falsification attempt was not sharp enough.
