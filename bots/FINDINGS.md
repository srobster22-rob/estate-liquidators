# Bot factory: findings

What building and running this actually established, in the order it was
established. The pattern to notice: **every one of these was found by a control
or a falsification test, not by inspection.** Numbers here are reproducible from
the commands shown.

---

## F1 · Six of the twelve market families were mis-specified, and the parameter that lied was `vol_ann`

`run.py calibrate` compares each family against a fixed panel of textbook
strategies. First pass, the families missed their own volatility targets by up to
40% and the hourly families offered perfect-foresight Sharpe ceilings of **8.6**.

Two distinct causes:

- **Symmetric regime switching.** A single `regime_switch_prob` used for both
  directions gives a stationary distribution of 50/50, so the process spent half
  its life in the 2.2x-vol stress state. A market asking for 16% delivered 22%.
  Fixed with an asymmetric chain (stress is 8x likelier to end than to begin,
  ~11% occupancy) plus an analytic variance budget.
- **Structure priced per bar, then annualised.** `trend_frac=0.04` per *hourly*
  bar means a 4% predictable fraction of every bar, which annualises to a Sharpe
  of 3.7 — before adding reversion. Nobody trades hourly crypto at Sharpe 8.
  Hourly structure cut by ~65%; ceilings now 1.2–2.6.

The residual bias sits in the fat-tailed near-integrated GARCH families
(`alpha+beta ≈ 0.98` with Student-t df 4, where the fourth moment barely exists):
the unconditional variance is right but the *sampling distribution* of realised
vol is so skewed that a typical draw misses by up to 20%. That is absorbed by
locked `vol_fix` constants, refreshable with
`run.py calibrate --refresh-vol-fix`.

**Why it mattered:** every bot sizes positions off realised volatility, so a
market parameter that does not mean what it says silently rescales the entire
experiment.

---

## F2 · `alpha_sharpe` rewarded pure beta as skill, in both directions

Regressing out the market is the right way to stop a levered buy-and-hold bot
looking clever on a market with a 7% risk premium. But a bot that essentially *is*
buy-and-hold has a near-zero residual, so `alpha / residual_vol` exploded to ±∞
on rounding noise — sometimes scoring beta as brilliance, sometimes as disaster.

Fixed by flooring residual vol at 25% of the strategy's own vol. Now enforced by
`test_alpha_sharpe_does_not_reward_pure_beta`: a 1.5x-levered constant-long bot on
a drifting market must show raw Sharpe > 0.10 and |alpha Sharpe| < 0.15.

---

## F3 · Pooled drawdown across replication instances is meaningless

Chaining 20 independent 12-year instances end to end and compounding produces a
240-year equity curve whose drawdown is an artifact of the concatenation order. It
read **−99%** for strategies whose every individual run drew down 25%, and it was
the sole reason several genuinely robust bots were being rejected at G2.

Drawdown is a per-instance property. G2 now gates on the median per-instance
drawdown (≤35%) and the worst instance (≤56%).

---

## F4 · Two gates were arithmetically unpassable or wrongly specified

- **G5 asked for p ≤ 0.01 from 40 permutation draws.** The smallest attainable
  p-value is 1/(N+1) = 0.024. The gate could not be passed by any strategy that
  has ever existed. Draws raised to 120.
- **G6's luck bar was built from the wrong variance.** Deflated Sharpe needs the
  sampling variance of *the statistic being judged*. The code used the dispersion
  of single-backtest Sharpes (bar ≈ 0.8 annual Sharpe — above what any honest
  single-asset strategy reaches) while the evidence was a 40-instance replication
  median, whose sampling variance is ~40x smaller.

---

## F5 · The multiple-testing denominator is the confirmation count, not the trial count

With the total-trials denominator, 9 bots were killed at G6 *after* replicating on
20 fresh instances with 90–100% positive and beating their own permutation null at
p ≤ 0.01. That is double-counting, and the reason is structural:

The deflated-Sharpe literature counts every trial because in real-data
backtesting there is one history and all trials are scored against it. That does
not hold here. Selection happens on the SEARCH pool; the evidence comes from the
HOLDOUT and STRESS pools, which are independent draws that no screened-out
candidate ever touched. The exposure on confirmation data is the number of
candidates *tested against it* — the gauntlet count — not the number screened.
Using the screen count demanded z ≥ 4.25 where the confirmation count demands
z ≥ 3.40.

Both figures are computed and both appear in every verdict; the gate uses the
confirmation count. **The choice is not justified by argument but by measurement**
— see F7.

---

## F6 · The intrabar range model broke optional stopping, and only the control market caught it

The most serious bug found, and the one that would have shipped.

Three bots reached G3 having passed G1 (alpha Sharpe +0.69, 100% of instances
positive) and G2 (+0.45 to +0.62 median, 90–100% positive, drawdowns under 20%).
They looked like the best results the lab had produced. All three had a
**take-profit and no stop-loss**. On `control_martingale_daily` — an iid Gaussian
random walk with zero drift and zero structure, where profit is impossible by
construction — they scored **+0.31 to +0.35 alpha Sharpe**.

The cause was in the generator, not the strategies. Intrabar high and low were
drawn as independent excursions above `max(open, close)` and below
`min(open, close)`, unconditional on the bar's own return. The engine reads
`high >= take_level` as "the limit order filled at the take level" — which is only
legitimate if the price actually traversed there. Unconditional extremes destroy
the martingale property of the path, so a take-profit with no stop harvests
favourable excursions that never happened, and pays for none of the unfavourable
ones. **Free money, in the harness rather than the market.**

Fixed by sampling the intrabar extremes as the running max/min of a **Brownian
bridge** from the open to the close, using the closed-form
`P(max ≥ m) = exp(-2m(m-Δ)/σ²)`. Sampling max and min independently remains an
approximation — they are negatively dependent — but every draw satisfies
`max ≥ max(0,Δ)` and `min ≤ min(0,Δ)`, so the OHLC stays consistent, and the
conditioning on Δ (the part that matters) is now correct.

Measured effect on the same take-profit-only bots, on the random walk:

| exits | gross alphaSR before | gross alphaSR after | net after |
|---|---|---|---|
| tp 1.1 ATR, no stop | +0.35 | **+0.07** | −0.13 |
| tp 1.3 ATR, no stop | +0.32 | **+0.05** | −0.14 |
| tp 2.0 ATR, no stop | — | **+0.00** | −0.17 |

Side effects, both checks that the fix is physically sane: the synthetic
`(high−low)/close` to `mean |log return|` ratio is now 1.8–1.9, matching real
equities; and best screen fitness on the random walk fell from +0.20 to +0.15
while the negative controls' own gross scores fell from 0.36/0.16 to 0.25/0.13 —
the artifact had been inflating those too.

**The lesson is about method, not about ranges.** No amount of reading the
generator would have found this; the bug was in the *interaction* between an
approximation in the data model and an assumption in the fill model. What found it
was a market where the correct answer was known to be zero.

---

## F7 · The ladder's false-positive rate, measured end to end

Every threshold in `GauntletConfig` can be argued about in the abstract. Only one
number settles it: point the entire search at a market with no exploitable
structure and count what it certifies.

`run.py fpr` registers a *tradeable* clone of the martingale control so G0 cannot
reject it on a technicality, screens N candidates with the real screen statistic,
and runs the full ladder on the finalists.

| harness | candidates | finalists | certified | died at |
|---|---|---|---|---|
| before the F6 fix | 2,000 | 22 | **0** | G1 ×20, G2 ×1, G3 ×1 |
| after the F6 fix | 3,000 | 28 | **0** | G1 ×26, G2 ×2 |

Zero both times — but note the second row reaches only G1/G2, and the best screen
fitness a random walk can produce fell to +0.15 against +0.65 on real families.
That separation is what licenses the F5 relaxation: G1 and G2 are doing the work,
so charging G6 for all 4,700 screened candidates was redundant strictness rather
than protection.

A miniature version runs in the test suite
(`test_end_to_end_false_positive_rate_is_zero`).

---

## F8 · The screen statistic decides everything, and the obvious one is the worst

First full run: 17 generations, 9,535 candidates screened, **zero** proven — while
best screen fitness climbed steadily 0.45 → 1.19. That combination is diagnostic:
the search was getting better at the screen and no better at reality. 76% of
finalists died at G1.

Two causes, both in *selection* rather than in the gates:

- **The hall of fame collapsed onto one lineage.** Eight of the top ten entries
  were the same rule at `lb=34` versus `lb=38`. Every subsequent generation bred
  from that one idea. Fixed with a structural signature (market + gene names +
  combiner + direction + sizing), capped at 2 parameterisations per signature and
  10 entries per market.
- **Pooled screen fitness selects for the luckiest instance.** With 640 candidates
  a generation and ~18 gauntlet slots, ranking is all that matters — and a
  textbook RSI-reversion bot that *does* pass all seven gates never made the
  finalist list, because its honest 0.5 could not outbid overfit 1.2s.

Rather than guess a better statistic, 370 candidates were scored under six of them
and each was checked against the outcome that matters — replication median alpha
Sharpe on the holdout pool:

| screen statistic | rho(OOS) | rho(repl) | top-10 median repl | top-10 clearing the 0.35 bar |
|---|---|---|---|---|
| pooled fitness (original) | 0.783 | 0.798 | +0.23 | 40% |
| **lower quartile − complexity** | 0.801 | 0.820 | **+0.37** | **50%** |
| median per-instance | 0.803 | 0.814 | −0.01 | 20% |
| median − ½·IQR | 0.796 | 0.810 | +0.22 | 40% |
| median × fraction positive | 0.268 | 0.247 | +0.10 | 30% |
| lower quartile, no complexity charge | 0.795 | 0.819 | +0.13 | 30% |

Base rate: **2.4%** of candidates clear the replication bar.

Two things stand out. Rank correlation barely separates the good statistics
(~0.80 for four of them) while precision-at-10 separates them by 3x — and
precision is what matters when only ~18 candidates get tested. And the complexity
charge alone moves top-10 replication from +0.13 to +0.37: penalising extra genes
at *selection* time, where priors belong, does more than any change to the gates.

That fixed the ranking but not the level. Re-running the loop, the screen still
discarded the one bot known to clear every gate: `rsi_rev(n=14)` on
`commodity_meanrev_daily` — replication median alpha Sharpe **+0.51**, 100% of 20
instances positive, permutation z = 4.3 — scored **−0.018** on the screen and was
never gauntleted.

The cause is sample size, not statistic choice. The screen runs on 1800-bar train
slices where a single instance's Sharpe is very noisy, so a *low quantile over few
instances is mostly measuring noise*. Sweeping instance count against quantile,
scored on the same holdout ground truth (base rate 1.8%):

| instances | q=0.25 | q=0.40 | q=0.50 | known-good bot's rank | in top 18? |
|---|---|---|---|---|---|
| 8 | 22% | 22% | 22% | 24th–48th | never |
| 12 | 33% | 28% | 28% | 9th–17th | yes |
| 16 | 39% | 39% | 33% | 5th–9th | yes |
| **24** | 33% | **44%** | 39% | **2nd** (at q=0.40) | yes |

(cells are precision among the top 18, complexity charge on)

Instance count dominates: 8 → 24 instances roughly doubles precision and moves
the known-good bot from unrankable to 2nd. And the best quantile *rises* with
instance count — 0.25 at n=8, 0.40 at n=24 — which is the same story from the
other side: the extreme quantile was compensating for noise, and once the estimate
is stable you no longer want to throw away that much information.

Adopted: **40th-percentile per-instance fitness over 24 instances**, minus 0.04
per gene/filter beyond the first, with half the gauntlet slots reserved for
candidates of at most two genes. The known-good bot's screen score went from
−0.018 to **+0.342**.

The general lesson is worth more than the parameter: in a strategy search, the
selection rule is a piece of statistical machinery that deserves the same
calibration as the gates. It is cheap to measure — pick candidates, score them,
check against held-out truth — and nobody does it.

---

## F9 · Junk candidates were setting the standard of proof

With the screen fixed, bots reached G6 and died there — including the untuned
archetype known to pass every gate. The cause was the variance estimate feeding
the deflated-Sharpe luck bar.

Deflated Sharpe needs the dispersion of trial Sharpes attributable to **chance**:
how good the best of N plausible candidates looks for free. The code passed the
raw population variance of screen Sharpes. Measured over 2,340 trials:

| statistic | value |
|---|---|
| population variance | **1.256** |
| 1st percentile screen alpha Sharpe | −5.5 |
| 5th percentile | −2.29 |
| interquartile range | 0.56 |
| robust variance (IQR/1.349)² | **0.175** |
| → luck bar, population estimate | **0.776** annual Sharpe |
| → luck bar, robust estimate | **0.289** annual Sharpe |

A random genome generator emits a long left tail of structurally broken bots —
over-levered, wrong-signed, ruined. They contributed almost all of the second
moment and pushed the luck bar to 0.776, above what any honest single-asset
strategy reaches, so G6 rejected everything including bots that had replicated on
20 fresh instances.

The perverse incentive is the tell: **with a population estimator, the more junk
the generator emits, the harder it becomes to prove anything.** Broken hypotheses
are not lucky draws. Switched to the Gaussian-consistent robust estimate,
IQR/1.349 squared, floored at 0.02 and capped at 1.0. Guarded by
`test_luck_bar_is_robust_to_junk_candidates`, which adds 40 bots at −3 to −8
Sharpe to a clean population and requires the estimate to move less than 45%.

With this fixed, the first bot passed within four generations.

---

## F10 · "Three proven bots" was two strategies counted twice

The first successful run reported 4 proven bots and declared its target of 3 met.
Reading them:

```
a60935fe32e2  rsi_rev(n=14) x1.00  thr 0.40/0.05  [hold<=15]
9a6f1aa7f76e  rsi_rev(n=14) x1.82  thr 0.34/0.05  [hold<=15]
7267d7623bad  -breakout(n=20)      thr 0.50/0.10  [hold<=20]
381b0a6f12da  -breakout(n=20)      thr 0.50/0.10  [hold<=20]
```

Two strategies, each certified twice. The `x1.00` versus `x1.82` pair is the
starkest: with a single gene, the weighted combiner divides by the sum of weights,
so the gene weight **normalises out entirely** — those are the identical signal
with a slightly different entry threshold, and they got different `bot_id`s
because the hash covers fields that make no difference to behaviour.

Two consequences, both bad. The loop declares victory on cosmetic variation. And
the portfolio builder treats them as separate legs, so risk parity across four
"diversified" positions understates concentration by a factor of two — exactly
where understating it matters.

Fixed by counting distinct structural signatures: the loop's target is
`n_distinct_proven()`, and `portfolio.dedupe()` keeps one genome per signature.
Both counts appear in the report, because the difference between them is
informative — it says how much of the search's output is genuinely different.

---

## What is still wrong, or unproven

Stated because the point of this document is not to look finished.

1. **Synthetic markets are stationary.** Every family has the same structure at
   bar 3000 as at bar 1. Real edges decay; that is the single largest gap between
   a pass here and a claim about a real instrument.
2. **The Bonferroni leg of G6 extrapolates.** It reads a Gaussian tail well past
   what 120 permutation draws can resolve. It is a sanity bound, not a measured
   p-value; the weight is carried by the conjunction of G2, G5 and G7.
3. **Intrabar max and min are sampled independently.** They are negatively
   dependent in a real bridge. The residual +0.07 gross alpha that take-profit-only
   bots still show on the random walk is the visible size of this approximation —
   below the G3 tolerance of 0.30, but not zero.
4. **Cross-family correlation is structurally zero here**, because instances are
   generated independently. Every portfolio number is therefore reported twice,
   once under that assumption and once at ρ=0.3. The second is the one to plan
   with, and even it is a guess.
5. **Costs are a model.** Square-root impact against the bar's own dollar volume,
   with a fixed notional. No queue position, no partial fills, no adverse
   selection, no borrow recall.
6. **The FPR measurement has one seed.** Zero out of 28 bounds the rate loosely,
   not tightly. A proper estimate wants repeated probes at several seeds.
