# Continuing the bot factory

Reusable prompt for the next session. Mirrors the root `ITERATION-PROMPT.md`
convention: read the record, pick one thing, try to break it, write down what
broke.

---

## Before you change anything

```bash
python bots/run.py selftest      # 37 falsification tests
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
   into `universe.py` so they stay reviewable in a diff.

## The highest-value things left

Roughly in order of how much they would change what the lab can claim:

1. **Make decay the default, not an exhibit.** Two non-stationary families exist
   (F20) and nothing certifies on them, but the eleven families that produce every
   certified bot are still stationary across 47.6 simulated years. A catalogue
   with a stationary mainline and two cautionary twins beside it answers "does the
   ladder notice decay?" — it does — but not the question that matters: *which
   strategies survive decay?* Give every family a decay halflife, recalibrate so
   the achievable band is still 0.4-1.0, and re-run. Expect far fewer
   certifications; that is the point.
2. **Stationarity — was the only limit that mattered, now partly addressed.** Three doublings of
   `n_bars` took the run from 3 certified strategies to 10, and the daily families
   are now at **47.6 years per instance with identical parameters throughout**.
   More data will keep working and will keep meaning less: the next doubling is 95
   stationary years. Sample size has stopped being the binding constraint and the
   stationarity assumption has become it. Add a family whose `trend_frac` or
   `rev_kappa` halves partway through, and a gate requiring the edge to survive in
   the *second* half of the holdout instances. Until that exists, every headline
   number in this lab is conditional on an assumption real markets violate.
3. **The permutation null's block length vs the bot's holding horizon.** F12 is
   the sharpest open problem: a genuine edge on `eq_largecap_daily` (passes
   G1-G4, worst-instance drawdown fixed by de-risking) fails G5 because that
   market's 6-bar reversion halflife sits inside the null's 5-bar block, so the
   null keeps the structure the bot trades. Decide the rule **before** looking at
   which candidates it admits — tie the block to the holding horizon, or gate on
   block=1 AND block=5 — then re-run the whole search and re-measure `fpr`. If
   the new rule raises the false-positive rate above zero, it is wrong regardless
   of how attractive the bots it admits look.
4. **(done — see F20; superseded by item 1.)** Non-stationary markets. Every family has the same structure at bar 3000 as
   at bar 1. Real edges decay, and nothing in the gauntlet tests for decay
   because there is none to test. Add a family whose `trend_frac` or `rev_kappa`
   halves partway through, and add a gate that requires the edge to survive in
   the *second* half of the holdout instances. This is the single largest gap
   between "passed G1-G7" and "would have made money".
5. **Real data.** `verify --data` already runs the identical engine, costs and
   permutation null on real CSVs. Point it at real bars for the instrument type a
   proven bot claims to trade. Expect the permutation p-value to be
   unimpressive — a single 1,200-bar out-of-sample window cannot establish
   significance for a Sharpe-0.4 edge, which is exactly why the synthetic
   replication gates exist and exactly why they are not sufficient.
6. **Cross-sectional strategies.** The generator makes independent single
   instruments, so pairs, lead-lag, relative value and factor crowding are all
   out of reach. This is also what makes the portfolio's `rho=0` number a
   fiction. Generating correlated *baskets* would unlock a whole strategy class
   and make the portfolio numbers mean something.
7. **Repeat the FPR measurement at several seeds.** One probe returning 0/28
   bounds the false-positive rate loosely. Ten probes would bound it tightly, and
   it is the number every threshold rests on.
8. **Dependent intrabar extremes.** Max and min are currently sampled
   independently from the Brownian bridge; they are negatively dependent. The
   residual +0.07 gross alpha that take-profit-only bots still show on a random
   walk is the visible size of that approximation.

## What a good session looks like

Pick one item. Build the smallest thing that could falsify a claim the lab
currently makes. Run it. If it breaks something, fix the cause rather than the
symptom, and add the test that would have caught it. Append what you found to
`FINDINGS.md` in the same voice as the existing entries: what was wrong, how it
was caught, what the numbers were before and after.

If a session ends with "I found nothing wrong", that is a weaker result than
finding a bug, and probably means the falsification attempt was not sharp enough.
