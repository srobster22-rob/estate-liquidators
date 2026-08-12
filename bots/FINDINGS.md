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

## F11 · Expansion silently became a no-op, and the third strategy was on the other side of it

The first run stopped at 2 distinct strategies after 25 generations, both
mean-reversion on `commodity_meanrev_daily`. Continuing it exposed a design flaw:
by level 6 every *structural* dial in `SearchSpace.expanded()` was already at its
ceiling — tier 3, five genes, three filters, all eleven markets — so each
subsequent "expansion" changed nothing but a finalist counter. The loop announced
`EXPAND -> L7` and resampled the identical space.

Past the ceiling, expansion now buys search *effort* instead: population
640 → 1,600, gauntlet slots 32 → 60, and the per-market finalist cap 3 → 6 so a
family with a promising near-miss can have several variants tested in one
generation. Effort is the weaker lever and is deliberately self-limiting — G6's
luck bar rises with every candidate screened — but it is honest, whereas an
expansion that does nothing while reporting that it did is not.

**The third strategy arrived at generation 45, level 15**, via crossover on
`futures_trend_daily`:

```
momentum(lb=126) + stoch(n=49)x0.43 | trend_regime(n=67)
  -> thr 0.15/0.05, voltarget @5% vol, lev<=1.7, stop 2.1 ATR
```

It is the strongest evidence in the run and the hardest-won. It survives **3×
costs at +0.49 alpha Sharpe** and one extra bar of delay at +0.48 — that is a
trend rule whose edge is much larger than its frictions. And it cleared a G6 luck
bar of **0.48**, against 0.23 for the bot proven at generation 4, because by then
the search had 40,740 trials and 1,255 confirmation tests behind it. Its
Bonferroni p was 2.67e-02 against a 0.05 threshold and its DSR 0.965 against
0.95: it only just made it, which is the correct price of a long search rather
than a flaw in it.

Two things this run demonstrated that the short one could not:

* **The multiple-testing machinery bites in the intended direction.** A bot found
  late has to be better than one found early. Nothing was relaxed to admit it.
* **The portfolio's two correlation scenarios finally diverge** (+0.71 at ρ=0
  versus +0.60 at ρ=0.3), because for the first time the legs span two market
  families. With all three on one family the numbers were identical, which the
  report said plainly rather than presenting one bet sized twice as
  diversification.

---

## F12 · A real edge blocked by the permutation null's block length

The most promising non-commodity candidate was an inverted breakout on
`eq_largecap_daily`: G1 alpha Sharpe +0.62, and 100% of 20 replication instances
positive. It failed G2 on drawdown alone — worst instance −63.1% against a −56%
cap — while its *median* alpha Sharpe of +0.38 cleared the +0.35 bar.

Alpha Sharpe is close to scale-invariant, so de-risking should have fixed it, and
it does:

| max leverage | median alphaSR | instances positive | median DD | worst DD |
|---|---|---|---|---|
| 0.90 | +0.38 | 100% | −33.8% | **−63.3%** |
| 0.60 | +0.37 | 95% | −27.4% | −55.5% |
| 0.45 | +0.36 | 95% | −23.6% | **−44.8%** |
| 0.30 | +0.35 | 95% | −17.3% | −31.8% |

The de-risked variant passes G1, G2, G3 and G4 — and then fails **G5** at
z = 2.4, p = 0.0165 against a required 0.01.

That failure is diagnosable and it is a limitation of the test, not of the bot.
`eq_largecap_daily` has a reversion halflife of **6 bars** and the permutation
null resamples in blocks of **5**, so the null retains most of the very structure
this bot trades: its null mean is +0.08 with an sd of 0.14, far above the +0.03
null seen on markets whose structure lives at longer horizons. The bot is being
asked to beat a null that contains its own edge.

**This was deliberately not fixed.** Shortening the block after seeing which
candidate it blocks is p-hacking the gate, which is precisely what the gate
exists to prevent. The correct procedure is to decide the rule first and then
re-run everything: pre-register a block length tied to the bot's holding horizon
(or gate on the conjunction of block=1 and block=5), re-run the full search, and
**re-measure the end-to-end false-positive rate** before believing anything the
new rule admits. That is a next-session task, recorded here so that whoever does
it knows the change was contemplated *before* it was made and why it was deferred.

---

## F13 · The search ate its own headroom, and that is the honest answer to "find a fourth"

Continuing past three strategies produced no fourth, and the reason is measurable
rather than a matter of not trying hard enough. Across 32 further generations —
**51,200 additional candidates, 1,626 additional gauntlets, ~100,000 additional
backtests** — nothing new was certified.

What happened instead is visible in the funnel. Deaths at **G6 rose from 36 to
120**: candidates that had already replicated on 20 unseen instances, stayed flat
on the random walk, survived 2x and 3x costs, and beaten their own permutation
null at p ≤ 0.01 — rejected solely because the search had grown.

The luck bar over the life of the run:

| moment | confirmation tests | luck bar (annual SR) |
|---|---|---|
| bot #1 proven (gen 4) | 42 | **0.23** |
| bot #3 proven (gen 45) | 1,255 | **0.48** |
| end of the hunt for #4 | 2,911 | **0.51** |

And the best remaining candidates, all of which reach G6:

| market | replication alphaSR | DSR | needed |
|---|---|---|---|
| `commodity_meanrev_daily` | +0.52 | 0.161 | 0.95 |
| `futures_trend_daily` | +0.38 | 0.637 | 0.95 |

These are **real edges**. The first has a higher replication alpha Sharpe than
the bot certified at generation 4. It cannot be certified now because the
evidence required has risen with the number of hypotheses tested, and 92,000
candidates is a lot of hypotheses.

That is the deflated-Sharpe correction working exactly as intended, and it is the
whole point of having it: *a search cannot buy certainty by searching harder.*
The mechanism that made bot #3 impressive — it cleared a bar twice as high as
bot #1 — is the same mechanism that now blocks bot #4.

**Three things would legitimately produce a fourth, and one thing would not.**

1. **More data per instance.** The luck bar does not depend on sample length, but
   the probabilistic Sharpe does, through its `sqrt(T-1)` term. Doubling
   `n_bars` from 3,000 to 6,000 raises DSR for a genuine edge and does nothing
   for a spurious one, because the null tightens too. This is the cleanest lever
   available: more evidence, not a weaker test. It requires regenerating the
   catalogue, refreshing `vol_fix`, and re-measuring the false-positive rate.
2. **Fixing F12's block-length problem properly** — pre-registered, whole search
   re-run, FPR re-measured. That admits the `eq_largecap_daily` edge, which is
   currently blocked by a null that retains the structure the bot trades.
3. **Richer market structure**, e.g. correlated baskets enabling cross-sectional
   strategies, which no primitive can currently express.

What would **not** be legitimate, and was not done: starting a fresh ledger. A
new run's luck bar resets to ~0.23, and every one of the G6 near-misses above
would certify immediately. Splitting one search into several to escape its own
multiple-testing correction is precisely the manipulation the correction exists
to prevent, and it would be undetectable in the final report. It is written down
here so that the temptation is on the record along with the reason it was
refused.

---

## F14 · Inert genes were forging diversity

While hunting the fourth, the hall of fame filled with eight bots that were
byte-for-byte different and behaviourally identical:

```
bollinger(k=2.57,n=32) + carry()  + long_bias()      on eq_intraday_15m
bollinger(k=2.57,n=32) + -carry() + long_bias()      on eq_intraday_15m
```

`eq_intraday_15m` has `carry_ann == 0`, so the `carry` primitive emits a constant
zero and its sign cannot affect anything. But the sign *is* part of the genome
hash, so `+carry` and `-carry` were different `bot_id`s and different structural
signatures. They occupied eight of sixty hall slots and a share of the per-market
cap, and the factory bred from all of them.

Worse, the same flaw could have inflated the headline: two "distinct" proven
strategies differing only by the sign of an inert gene would have counted as two.
It did not happen — none of the three proven bots use `carry` — but it was
reachable.

Fixed in `_repair`: a gene that is provably a no-op for its market is dropped
from the genome entirely, rather than being special-cased at comparison time. An
inert gene should not exist. Guarded by `test_inert_genes_are_dropped`, which
also checks the converse — `carry` on `fx_major_daily`, which really does pay
1.2%, must be kept.

---

## F15 · A primitive aimed at an effect below the noise floor

Three tier-4 primitives were added to widen the hypothesis space after the level
1-3 ladder was exhausted. Measured against the structure they target:

| primitive | best gross alphaSR | verdict |
|---|---|---|
| `efficiency_ratio(n=20)` | +0.43 on `futures_trend_daily` | works |
| `adaptive_horizon` | +0.39 on `eq_index_daily` | works |
| `seasonal_profile` | +0.01 at the *planted* period | cannot work here |

`seasonal_profile` estimates the mean return of each calendar phase from its last
`k` occurrences — the right tool for the sine calendar effect planted in
`commodity_meanrev_daily` and the session shape in `eq_intraday_15m`. It finds
nothing, and the arithmetic says it never could:

| market | effect size | phase-mean std error | SNR |
|---|---|---|---|
| `commodity_meanrev_daily` | 0.030 sigma | 0.084 sigma (142 cycles) | **0.36** |
| `eq_intraday_15m` | 0.015 sigma | 0.058 sigma (300 cycles) | **0.26** |

Using *every cycle in the series*, the standard error of the estimate is three to
four times the effect. The calendar effect is real, it is in the data, and it is
undetectable at this sample size by any estimator.

This has a consequence for `oracle_sharpe_ceiling()`. The ceiling is correctly
labelled perfect-foresight, and it adds a seasonal term of `amp/sqrt(2)` — but
for the calendar component the gap between that bound and anything achievable is
essentially total. The trend and reversion terms are reachable; the seasonal term
is a number no strategy can approach. Worth knowing before reading a ceiling as
"how much is on the table".

---

## F16 · Doubling the bars per instance: 6 strategies from 960 candidates instead of 3 from 92,000

F13 named more data as the cleanest way past the deadlock, on the theory that the
luck bar does not depend on sample length while the probabilistic Sharpe does,
through its `sqrt(T-1)` term. More evidence for a real edge; nothing for a
spurious one, because the null tightens too. Doubling `n_bars` on every family
(3,000 → 6,000 daily, 9,000 → 18,000 crypto hourly, 7,800 → 15,600 intraday)
tested that theory. It held, by a wider margin than expected.

| | 3,000 bars | 6,000 bars |
|---|---|---|
| distinct strategies | 3 | **6** |
| candidates screened | 91,940 | **960** |
| gauntlets | 2,911 | **41** |
| backtests | 202,348 | **6,968** |
| generations | 77 | **3** |
| markets represented | commodity, futures | **futures, FX** |

Roughly **96x fewer candidates for twice the strategies**, and on two market
families rather than one — `fx_major_daily` had never produced a certified bot in
any previous run.

The mechanism is visible in the second row. It is not that the gates got easier;
it is that a real edge needs far fewer *hypotheses* to establish when each test
carries twice the evidence, and fewer hypotheses means a lower multiple-testing
correction. The two effects compound.

Three independent checks that this is more evidence and not a weaker test:

* **The false-positive rate stayed at zero, and got stricter.** 1,500 candidates
  on a structureless market certified nothing, and where the 3,000-bar harness
  let a few finalists reach G2 and G3, **all 20 now die at G1**. Doubling the data
  makes spurious edges easier to reject, exactly as the theory says.
* **The negative controls' apparent edge collapsed.** The best archetype on
  `control_efficient_daily` fell from +0.29 to +0.01 net alpha Sharpe — that
  number was always selection noise across 13 archetypes, and it shrinks with
  sample size like noise should.
* **`vol_fix` moved on six of thirteen families** and had to be re-measured. The
  constant absorbs the skewed sampling distribution of realised volatility in the
  near-integrated GARCH families, and that distribution depends on sample length.
  A change to `n_bars` is a change to the generator; the standing rule to refresh
  the constants earned its place.

The honest qualifier is in F17.

---

## F17 · Search-burden headroom: how much of a certification is the bot and how much is the search being small

Six strategies certified after 41 gauntlets is a very different claim from three
certified after 2,911, because G6's luck bar is a function of how many hypotheses
have been tested. So the obvious question is whether the six would survive the
burden the three had to.

Re-testing each against the previous run's 2,911 confirmation tests: **three
survive, three do not.** All three survivors trade `futures_trend_daily`; all
three casualties trade `fx_major_daily`. The FX bots are genuine edges — G2
replication +0.38 to +0.40 with 95-100% of instances positive, cost-robust to 3x —
but their *certification* leans on the search having been short.

Reporting only "6 distinct strategies" would have been misleading, so the
gauntlet now computes this directly. `burden_headroom` binary-searches the largest
number of confirmation tests at which a bot still clears both legs of G6. Both
criteria fall monotonically with the test count, and the replication returns and
permutation z-score are already in hand, so it costs nothing.

| bot | market | replication alphaSR | certified after | headroom |
|---|---|---|---|---|
| `cc979a601706` | futures_trend | +0.50 | 19 | **2,779,442** |
| `715224a93087` | futures_trend | +0.50 | 31 | **241,768** |
| `bc49c51e4be8` | futures_trend | +0.46 | 12 | **4,731** |
| `d8d97a6d4d8c` | fx_major | +0.40 | 38 | 2,028 |
| `471990f1c3e1` | fx_major | +0.39 | 26 | 1,017 |
| `824eaa23a9ab` | fx_major | +0.38 | 37 | 263 |

The spread is four orders of magnitude across bots whose replication Sharpes
differ by 0.12. That is the number to read before the Sharpe: a bot with headroom
of 263 is a bot that would vanish in a serious search, and one with headroom in
the millions is an edge that does not care how hard you looked.

It also retro-explains F13. The commodity near-miss that could not be certified at
2,911 tests was not weak — it was competing against a bar that its own search had
raised, and its headroom was simply below where the search had already got to.

---

## F18 · Doubling again found a generator defect that had been latent from the start

The second doubling (6,000 → 12,000 daily, 18,000 → 36,000 crypto hourly) broke
`test_every_family_hits_its_vol_target`: one `eq_smallcap_daily` instance realised
113.8% volatility against a 45% target. Inspecting it:

```
idx 6   vol 113.8%   max|log return| 3.915   sample kurtosis 1263
```

A single-bar log return of 3.915 is a **4,900% move in one day**. Not a fat tail —
a broken process.

My first explanation was wrong, and measuring killed it. I assumed the sample
variance could not concentrate because a Student-t with df ≤ 4 has infinite
kurtosis. The data disagreed: dispersion shrinks normally with more bars
(IQR/median 0.101 → 0.088 → 0.057 across the three sizes). Two real causes,
found only by looking at the instance:

**1. The GARCH variance feedback can transiently explode.** A GARCH(1,1) has
finite unconditional kurtosis only when `a²·E[eps⁴] + 2ab + b² < 1`, and `E[eps⁴]`
is infinite for `tail_df ≤ 4`. **Six of thirteen families sit below that line** —
`eq_smallcap` 3.6, `fx_em` 3.5, `crypto_alt` 3.2, `commodity_meanrev` 3.8,
`crypto_major` 4.0, `eq_intraday` 4.0. A large innovation inflates σ², which
scales the next shock, which inflates σ² further. Fixed by winsorising the
standardised shock **that enters the variance update** at 4σ; the return itself
still receives the full untruncated innovation, so prices keep their fat tails
while the recursion keeps finite moments. Plus a conditional-vol ceiling at 8×
the long-run level.

**2. There were no limit moves.** Even with a tamed variance process, a df-3.6
innovation draws 40σ often enough in 12,000 bars to produce an 1,100% day. Real
venues do not allow that: equities have limit-up/limit-down bands and market-wide
circuit breakers, futures have daily limits, crypto exchanges halt or
auto-deleverage. The single-bar move is now capped at 12σ — still far fatter than
Gaussian, which never reaches 12σ at all.

| family | worst bar before | worst bar after | kurtosis after |
|---|---|---|---|
| `eq_smallcap_daily` | 138σ (4,900%) | 12σ (**41%**) | 23.7 |
| `commodity_meanrev_daily` | 43σ | 12σ (**30%**) | 19.0 |
| `crypto_alt_hourly` | 36σ | 12σ (**15%**) | 35.7 |
| `eq_index_daily` | — | 12σ (**13%**) | 12.8 |

This had been in every result from the beginning. It took 4× the bars to give it
enough chances to fire in an evaluation instance, and the vol-target test to catch
it. The lesson is the one this file keeps repeating: the bug was in an
*interaction* — heavy-tailed innovations feeding a variance recursion — and no
amount of reading either piece in isolation would have found it.

All thirteen `vol_fix` constants moved after the fix (capping moves lowers
realised vol) and were re-measured, and the false-positive rate was re-confirmed
at zero.

---

## F19 · What four doublings bought, and what they cost

| bars per instance | 3,000 | 6,000 | **12,000** |
|---|---|---|---|
| distinct strategies | 3 | 6 | **10** |
| candidates screened | 91,940 | 960 | **960** |
| gauntlets | 2,911 | 41 | **42** |
| generations | 77 | 3 | **3** |
| markets represented | 1 | 2 | **3** |
| best replication alphaSR | +0.50 | +0.50 | **+0.64** |
| best headroom | 2.8e6 | 2.8e6 | **≥1.07e9** |

`eq_largecap_daily` certified for the first time — the family whose genuine edge
was blocked in F12 — and eight of the ten survive a bar 70× harder than the one
they faced. The top six all trade `futures_trend_daily` with replication alpha
Sharpes of +0.55 to +0.64 that barely move under 3× costs (+0.49 to +0.62).

**The cost is external validity, and it is not small.** 12,000 daily bars is
**47.6 years**. That is more history than most instruments have — most single
names have under 30 years, and the whole point of a synthetic lab is that these
are *stationary* 47.6 years, with the same trend and reversion parameters at bar
12,000 as at bar 1. Real markets do not offer that, and the anomalies that
survive publication usually shrink.

So the honest reading of this sequence is narrower than "more data finds more
strategies". It is: **under stationarity, certification is limited by evidence
per hypothesis far more than by the number of hypotheses tried.** That is a real
and useful statement about search design. It is not a statement about markets,
and the gap between the two widens with every doubling — the experiment gets
statistically stronger and externally weaker at the same time.

The next doubling would be 95 years of stationary daily data. At that point the
result would say almost nothing about anything tradeable, and the binding
constraint on this lab stops being sample size and becomes the stationarity
assumption itself. That is the item at the top of `ITERATION-PROMPT.md` for a
reason, and it is now the only one that matters.

---

## F20 · The non-stationary families, and a gate that has yet to earn its keep

Stationarity was the top open item after F19: every family had the same trend and
reversion parameters at bar 12,000 as at bar 1, which is the assumption real
markets most obviously violate. Two families now break it, built as **near-clones
of the two that certify most readily** so the only difference is durability:

* `futures_trend_decay_daily` — `futures_trend_daily` with a crowded edge: trend
  strength halves every 3,000 bars (~12 years) toward a 10% floor.
* `eq_largecap_break_daily` — `eq_largecap_daily` whose anomaly stops working on a
  date: 85% of the edge vanishes 45% of the way in.

Only the *predictable* components decay. Drift, volatility, GARCH and jumps are
untouched, so the instrument still looks like the same instrument — it just stops
being forecastable. Their ceilings fall accordingly (1.34 → 0.54, 1.17 → 0.62),
because quoting a decaying family's opening edge as its ceiling would overstate
what is available across the series by several times.

**The result: 11 strategies certified, none of them on a decaying family.**

| family | best archetype net alphaSR | certified in the run |
|---|---|---|
| `futures_trend_daily` | +0.52 | 6 |
| `futures_trend_decay_daily` | **+0.00** | **0** |
| `eq_largecap_daily` | +0.46 | 3 |
| `eq_largecap_break_daily` | **+0.18** | **0** |

This is not a vacuous zero. Both families are tier 1, so they are searched every
generation, and their candidates **reach the hall of fame on screen score** — 10
and 6 entries respectively. The search finds them attractive; the ladder rejects
every one. In a controlled run pointing the whole search at each family, 8 of 8
and 9 of 9 finalists were rejected, against 6 of 12 certified on the stationary
twin.

**The new gate did not do the work, and saying so matters.** G2b-durability
compares alpha in the second half of each holdout instance to the first, with
thresholds measured rather than assumed: across ten bots already certified on
stationary families, late-half alpha ran +0.38 to +0.66 and retention 0.85 to
1.40 (median 0.98), so floors of +0.25 and 50% sit clear of honest behaviour. On
the decaying twins the same style of bot retains 0.31 and 0.02.

It never fires. **G1 rejects everything first**, because G1's out-of-sample window
*is* the last 40% of the series — precisely where a decayed edge is weakest. The
two tests overlap almost completely for these decay shapes.

G2b is kept anyway, for two reasons that are worth stating rather than assuming:
it is free (it splits the return series G2 has already produced), and it is
independent evidence — G1 scores 8 search-pool instances adjacent to the training
window, G2b scores 20 holdout instances the search never touched. For a milder
decay, where the last 40% still clears G1's threshold but the trend is plainly
down, G2b is the binding test. Since nothing in the catalogue currently exercises
it, `test_durability_gate_can_fire` constructs a 5,000-bar-halflife probe and
requires the statistic to register the fade, so the gate is verified code rather
than decoration.

The honest summary is narrower than "the lab now handles non-stationarity". It
is: *the lab now contains non-stationarity and demonstrably refuses to certify
strategies on it* — and the gate built specifically for the job turned out to be
redundant with one that already existed. That is worth more than a gate that
looks necessary because nothing was measured.

---

## F21 · Decay as the default: two thirds of the strategies disappear, and the survivors are a different kind

Every tradeable family now decays — halflife half the series, 35% floor, so the
average edge across an instance is 70% of its opening value. Only the predictable
components fade; `drift_ann` and `carry_ann` do not, because a risk premium is
compensation for bearing risk rather than a mispricing waiting to be arbitraged.

The rate was chosen by measurement and is a modelling choice, stated as one.
Against the archetype panel, this halflife costs about a third of the achievable
alpha Sharpe (catalogue mean +0.36 → +0.24); a quarter-series halflife costs about
half (+0.19), which puts nearly every family under the certification bar and leaves
the lab measuring nothing. So this is the mildest setting that still tests
something, not an estimate of how fast real anomalies die. The published
post-publication literature is far more abrupt, and that case is
`eq_largecap_break_daily`.

**The result:**

| | stationary catalogue | decaying catalogue |
|---|---|---|
| distinct strategies | 11 | **4** |
| candidates screened | 960 | **12,400** |
| gauntlets | 41 | **353** |
| generations | 3 | **19** |
| markets producing a bot | 3 | **2** |

Thirteen times the search for a third of the strategies. Nothing certified on
either family that decays *faster* than the default.

**The composition changed completely, and that is the real finding.** On the
stationary catalogue, 6 of the 11 winners were trend rules on
`futures_trend_daily`. With decay, that family produces **nothing at all**, and
three of the four survivors are commodity mean-reversion.

The mechanism is cost leverage. Net alpha is `gross × decay − costs`, and costs do
not decay. Measured on `futures_trend_daily`, a textbook trend bot's gross edge
retains the ~71% the edge profile implies, but its **net alpha retains 11%** — the
fixed cost base amplifies a 30% haircut into a 90% collapse. The four survivors
retain 60–84%, because they were running far enough above their cost floor that
the haircut did not reach it.

So decay does not shave a bit off every strategy. **It selects, hard, for margin
over costs** — which is also why crowded anomalies in the real world tend to die
abruptly rather than fade gracefully. A strategy operating near its cost floor has
no gradual decline available to it.

---

## F22 · The durability gate had to be recalibrated when the catalogue changed, and that is not the same as relaxing it

G2b was built (F20) against a stationary catalogue, where retention of first-half
alpha into the second half is ~1.0 by construction. Measured on a stationary
probe it is **1.04**; on a decaying family it is **0.11**. As a
stationary-versus-decaying test it is sharp.

But with decay universal, every bot on every tradeable family fails a 50%
retention bar — the gate would reject everything and discriminate nothing among
the candidates that matter. Worse, the ratio is dominated by an effect that has
nothing to do with strategy quality: as F21 shows, it measures the cost base as
much as the fade.

So the ratio is now applied only where it means something — markets that are
supposed to be stationary, which is the controls — and the economically
meaningful question is asked everywhere: **is there still a usable edge at the
end?** That is the absolute late-half floor of +0.25 alpha Sharpe, and it is the
stricter test in the way that counts, because a bot can clear G2 on a full-series
average while having nothing left in its second half.

**This is recalibration, not relaxation, and the distinction is worth being
explicit about** because this file has refused the other thing twice (F12, F13).
The test for which one you are doing: a threshold moved because the *underlying
distribution changed* and re-derived by the same measurement as the original is
recalibration; a threshold moved because it *blocked a specific candidate you
liked* is p-hacking. Here the catalogue changed under the gate, the new
thresholds were measured the same way the old ones were, and the false-positive
rate was re-confirmed at zero before any result was believed.

The gate still never fires in a full run — G1 rejects decayed edges first, since
its out-of-sample window *is* the last 40% of the series. Its value remains what
F20 said: independent evidence on 20 holdout instances the search never touched,
for the milder decay where the last 40% still clears G1. All four certified bots
have late-half alpha between +0.26 and +0.41, which is the gate confirming rather
than rejecting — the useful thing it currently does is put that number in the
record for every proven bot.

---

## F23 · The decay-rate curve: 4 strategies at a 24-year halflife, 0 at 12

Every headline this lab has produced was conditional on one number nobody had
measured — how fast a planted edge fades. F21 chose a halflife of half the series
because it was the mildest setting that still certified anything, which is an
honest reason to pick a parameter and a bad reason to trust a result derived from
it. So: report the curve.

The sweep (`python bots/run.py decay`) evaluates a **fixed, pre-registered panel**
at every rate — all 120 untuned archetypes plus every distinct strategy the search
has certified, deduplicated by signature. Same genomes, same gates, same
multiplicity denominator (131, the panel size), and **seed-paired instances**: the
`~hl=0.125x` variant of a family draws the identical innovation, jump and regime
stream as its `~stationary` twin, so the only difference between two rows is how
fast the edge goes away.

| rung | halflife | mean edge | edge at end | distinct | genomes | markets |
|---|---|---|---|---|---|---|
| `stationary` | never | 1.00 | 1.00 | **8** | 16 | 4 |
| `hl=1.00x` | 48 yr | 0.82 | 0.68 | **4** | 11 | 2 |
| `hl=0.50x` *(shipped)* | 24 yr | 0.70 | 0.51 | **3** | 8 | 1 |
| `hl=0.25x` | 12 yr | 0.57 | 0.39 | **0** | 0 | 0 |
| `hl=0.125x` | 6 yr | 0.47 | 0.35 | **0** | 0 | 0 |
| `hl=0.125x/f10` | 6 yr, 10% floor | 0.26 | 0.10 | **0** | 0 | 0 |
| `break@45%` | abrupt, midway | 0.53 | 0.15 | **0** | 0 | 0 |
| `break@85%` | abrupt, late | 0.87 | 0.15 | **1** | 1 | 1 |

**Market breadth collapses faster than the strategy count.** Stationary, the panel
certifies on four families — `commodity_meanrev_daily`, `eq_largecap_daily`,
`futures_trend_daily`, `fx_major_daily`. At a 48-year halflife it is two. At the
shipped 24 years it is one. Long before decay takes the last strategy it has
already taken the diversification.

**The cliff is between a 24-year halflife and a 12-year one, and it is a cliff,
not a slope.** Three strategies to none, across a rung that only takes the mean
edge from 0.70 to 0.57.

Why it is a cliff is visible in the achievable-alpha table the same command
prints. The best archetype on `commodity_meanrev_daily` makes 0.52 net alpha
Sharpe stationary, 0.35 at the shipped rate, 0.28 one rung faster. The replication
bar is +0.35. The catalogue's whole population of strategies is packed into a
0.2-Sharpe band just above the bar, so a 20% edge cut does not thin the field —
it empties it.

**The panel had a hole in it, and finding it was the more useful half of this.**
The first version of this sweep produced an `arch` column — distinct strategies
from the *untuned* panel — of 1 at `stationary` and 0 everywhere else, which meant
the whole curve rested on bots fitted to the `hl=0.50x` catalogue. The cause was
not subtle once looked for: **every one of the ten archetypes sized by `voltarget`
or `fixed`, and every strategy the search has ever certified sizes
`proportional`.** A whole position-sizing convention was missing from the priors.
Filters were the other blank column — not one archetype carried a regime or
volatility filter, though the search space has five and "trade the rule only when
conditions suit it" is as textbook as the rules themselves.

Adding those (same signals, same parameters, only the missing conventions) took
the panel from 142 to 233 rules and the `arch` column at `stationary` from 1 to 5.
It is coverage, not tuning: the additions were chosen by reading what the panel
contained against what the search space allows, before measuring what any of them
would do. Two of them certify at `stationary` on families — `futures_trend_daily`,
`fx_major_daily` — that produce nothing at any decay rate, which is the kind of
thing a silent panel was hiding.

**Two smaller things fell out of building it.**

*Seed pairing is not optional.* Instance seeds derive from the family name, so a
renamed variant silently draws a fresh set of 47-year histories. With 11 families
and ~50 instances each, that resampling noise is comparable in size to the decay
effect, and the first version of this sweep would have been reporting both.
`MarketSpec.seed_name` pins the stream, and
`test_paired_variants_share_their_random_stream` holds it: a renamed-but-identical
variant must be byte-identical to its base.

*Decay barely moves realised volatility, and the constant that corrects it is
noisier than the effect.* Fading the trend removes variance the `_noise_scale`
budget subtracts unconditionally, so a decayed family should land slightly under
its vol target. Measured paired across all 77 family-rung combinations, the
systematic effect is **0.02%-0.42%** per family; the per-family offset in the
locked `vol_fix` constants is up to **1.9%**. So the rungs inherit their base
family's constant. Re-measuring per rung would have injected an order of magnitude
more noise than it removed — which is the opposite of what "recalibrate everything
you touch" would have suggested, and is why it was measured.

---

## F24 · F21's cost-leverage claim is a plane, not a ratio, and the difference matters

F21 concluded that cost leverage is what selects the survivors of decay. That
implies something checkable: if costs are a fixed subtraction and edge a
proportional one, survival should depend on the **ratio** of gross edge to cost.
`python bots/run.py costgrid` sweeps the two independently — an edge multiplier
`e` applied through the same decay machinery the gauntlet uses, against a cost
multiplier `c` — and fits both models.

| market | a(edge) | b(cost) | intercept | R² plane | R² ratio-only | breakeven e/c |
|---|---|---|---|---|---|---|
| `commodity_meanrev_daily` | 0.396 | −0.057 | 0.116 | **0.94** | 0.69 | 0.14 |
| `eq_largecap_daily` | 0.357 | −0.078 | 0.136 | **0.98** | 0.72 | 0.22 |
| `futures_trend_daily` | 0.417 | −0.052 | −0.038 | **0.87** | 0.61 | 0.12 |
| `eq_smallcap_daily` | 0.043 | −0.023 | 0.032 | 0.31 | 0.74 | 0.55 |

**The ratio model loses a quarter of the explained variance.** The falsification
is visible in the raw grid without any fitting: on `commodity_meanrev_daily`,
`e=1.0, c=1.0` gives +0.47 net alpha and `e=0.5, c=0.5` gives +0.27. Same ratio,
0.20 Sharpe apart.

The reason is arithmetic once written down. Under `net = a·e − b·c`, scaling both
by λ scales net by λ — it does not preserve it. A ratio determines the *sign* of
net alpha, and only when the intercept is zero; it never determines the
*magnitude*. And the gauntlet's bar is +0.35, not 0. So **halving your costs does
not buy back a halved edge**, and the decay curve in F23 is a statement about edge
levels that cannot be undone by trading somewhere cheaper.

F21's underlying observation survives — a fixed cost base does amplify a
proportional edge cut, and `a` is 5-8x `|b|`, which is exactly that amplification
— but its generalisation to a ratio does not. Note also that F21's headline "a 30%
edge cut takes 90% of net alpha" was measured on a *within-series fade*, where the
bot's own calibration also drifts out of step with the market; the uniform level
change measured here costs 36-49% instead. Both numbers are real and they measure
different things.

`eq_smallcap_daily` is in the table as the control: its best archetype makes
nothing at any edge level once costs are at 1x or above, the plane fit collapses
to R²=0.31 because the surface is censored at zero, and the ratio model "wins"
only because both models are fitting a flat plate. The trap market is a trap at
every edge level.

---

## F25 · The durability gate could not see an edge that died in the last 15% of its life

This one was found by a control built to answer a different question, which is
the third time in this file that has happened.

The decay curve confounds two things that fall together in every gradual rung: how
much edge there was *in total*, and how much was left *at the end*. To separate
them, `break@85%` cuts 85% of the edge at the 85% mark — average edge 0.87, edge
at the close 0.15. If certification tracked the average it should behave like
`hl=1.00x`; if it tracked the terminal value it should behave like `break@45%`,
which certifies nothing.

**It behaved like `hl=1.00x`: four distinct strategies certified, with median
late-half alpha +0.45.** Identical terminal edge to `break@45%`, opposite verdict.

The cause is that every window in the ladder averages over a span long enough to
hide the end. G1's out-of-sample window is the last 40% of the series; G2b's
durability window is the last 50%. A death confined to the final 15% leaves 70% of
the durability window full of live edge, and the median reads healthy. So the
gauntlet was certifying strategies whose edge had been 85% gone for the last
twelve simulated years of a forty-eight-year test, and reporting +0.45 late-half
alpha while doing it.

**The fix is a second leg on G2b: the same "is there still a usable edge"
question, at the same +0.25 threshold, over the final *quarter*.** No new free
parameter — the principle and the number are the ones already argued for in F22,
applied to a window that can resolve the end. This is a gate being *tightened*
because it was provably mis-specified, which is the only circumstance the standing
rules permit a gate to move at all, and the proof was in hand before the change.

What it cost, measured before and after on the identical panel:

| rung | before | after |
|---|---|---|
| `stationary` | 5 distinct | 5 |
| `hl=1.00x` | 4 | 4 |
| `hl=0.50x` *(shipped)* | 4 (11 genomes) | 4 (10 genomes) |
| `hl=0.25x` | 1 | **0** |
| `break@85%` | 4 | **1** |

It removed three of the four late-break certifications and the marginal 12-year
survivor, and left the shipped catalogue's four strategies standing. False-positive
rate re-measured at 0 of 18 afterwards; 42/42 tests pass.

**It does not close the hole completely, and the residual is a windowing limit
rather than an oversight.** The final quarter still contains 10 percentage points
of pre-break series against 15 post-break, so its effective edge is ~0.49 —
comparable to the shipped rung's 0.51, which certifies four. One strategy survives
`break@85%` for that reason, and arguably should: it still earns +0.48 alpha in
that window. Resolving a death confined to the last 15% needs a window that short,
and a window that short is too noisy to gate on. The honest statement of what the
ladder can now do: **it detects an edge death that occupies at least a quarter of
the series, and detects one confined to the last 15% only for marginal
strategies.**

---

## F26 · A run's own closing standard of proof rejects one of the four strategies it certified

Re-running the current gauntlet over the committed ledger, to check what the F25
gate change had cost, produced a bigger drop than the change could explain. The
first attribution was wrong and worth recording as such: **the losses were not
from the new gate, and not from permutation-seed noise either** — five re-runs at
five different seeds returned byte-identical headroom values, which ruled that out
immediately.

The cause is that **G6's luck bar rises while the run is still going**, and two of
its inputs drift:

* the confirmation-test count (`n_confirm_tests`), already visible per bot as
  `burden_headroom`; and
* `var_trial_sharpe`, the variance of the trial-Sharpe distribution the bar is
  built from, which was visible nowhere.

So a bot certified in generation 5 was judged against a smaller search than the
run eventually became. Two re-runs of the identical ledger separate the effects:

| re-run | what varies | genomes | distinct |
|---|---|---|---|
| as certified | — | 30 | 4 |
| **A:** each bot at *its own* recorded burden and variance | only the F25 gate | **28** | **4** |
| **B:** every bot at the run's *closing* burden (353) and variance (0.123) | the closing standard | **27** | **3** |

**A says the tightened durability gate cost 2 genomes and no strategies**, both
marginal — final-quarter alpha +0.23 and +0.24 against a +0.25 bar.

**B says the run's own closing standard costs a whole strategy.** All three
`eq_largecap_daily` genomes fall, and their recorded headroom had already said
they would: 229, 242 and 262 against a run that finished at 353 gauntlets. The
headroom statistic (F17) was doing exactly its job; nothing was reading it.

So `gauntlet.recheck_at_final_standard()` now runs at report time and prints both
counts. It is cheap — the permutation z-score is on the ledger already, so only 20
replication backtests per bot are re-run — and it is structurally incapable of
certifying anything new: a bigger search can only take bots away, which
`test_final_standard_recheck_can_only_take_bots_away` holds by checking the count
is monotone as the burden goes 1 → 100 → 10⁴ → 10⁷.

**The general lesson is about the shape of the claim, not the number.** "N
strategies were certified during this run" and "N strategies clear the bar this
run finished with" are different statements, and the first is the one every search
naturally produces. Any lab that expands its search until it succeeds — which is
precisely what the loop in this repository is instructed to do — will accumulate
early certifications that its own final bar no longer supports. The report now
leads with the conservative number.

---

## F27 · A search 30% bigger than the one that found four strategies finds none at half the halflife

F23's curve is built from a fixed panel, so on its own it can only say that
*known* strategies do not survive a faster fade. It is blind by construction to a
search discovering something else — a shorter-horizon, lower-turnover rule that
never wins at the shipped rate and so never entered the panel. That was the
largest open question the curve left behind, and it is the one that decides
whether the zero at 12 years is a fact about the rate or about the panel.

`run.py loop --catalogue hl=0.25x` swaps the entire tradeable catalogue for one
decay rung — base families *and* the two off-ladder twins are unregistered, so no
candidate can wander onto a family fading at some other rate — and runs the
ordinary loop against it, with its own ledger, its own priors pass and its own
multiplicity burden.

| | 24-year halflife (shipped) | 12-year halflife |
|---|---|---|
| candidates screened | 12,400 | **16,375** |
| gauntlets | 353 | **459** |
| generations | 19 | **22** |
| expansion levels reached | 3 | **8** |
| distinct strategies | 4 | **0** |

**More search, more expansion, nothing.** The funnel is the informative part: 411
of 459 died at G1 and the remaining 48 at G2. Not one candidate in 16,375 reached
the permutation null. Best screen fitness plateaued at +0.51 from generation 10
onward across four further expansions — the search was not still climbing when it
ran out of budget, it had stopped.

So the zero at 12 years is a property of the decay rate, not of the panel, and
F23's curve can be read as a statement about what is *available* rather than about
what these particular bots happen to do. The honest caveat that remains is
narrower than before: a search is not a proof of absence, and this one was bounded
at 5,627 seconds.

**Alongside it, the number every threshold rests on is now bounded properly.** The
false-positive rate had one probe behind it — 0 of 18, which by the rule of three
only says "below about 17%". `run.py fpr --repeats 10` runs ten independent probes:

> 20,000 candidates over 10 seeds on a structureless market, 137 reached the
> gauntlet, **0 certified**, 95% upper bound **~2.2%**. Every one of the 137 died
> at G1.

That the entire rejection happens at the *first* gate is worth noting on its own.
The expensive machinery downstream — replication, controls, cost stress, the
permutation null, the deflated Sharpe — never has to fire on a random walk,
because a strategy fitted to the first 60% of a structureless series has nothing
left in the last 40%. The later gates exist for the harder case: a bot with a real
but small edge that a big enough search would still have found by luck.

---

## F28 · An edge that worked for forty years and then stopped is 19x easier to certify than one that faded gently

F27 searched the fast-fade rung and found nothing. The obvious companion — search
the *late-break* rung, where 85% of the edge vanishes at the 85% mark — produced
the opposite result, and it is the most uncomfortable finding in this file.

| catalogue | mean edge | edge at end | candidates | gauntlets | distinct |
|---|---|---|---|---|---|
| `break@85%` | 0.87 | 0.15 | **640** | 52 | **4** |
| `hl=0.50x` *(shipped, 24 yr)* | 0.70 | 0.51 | 12,400 | 353 | 4 |
| `hl=0.25x` (12 yr) | 0.57 | 0.39 | 16,375 | 459 | **0** |

**Nineteen times less search for the same number of strategies** — and the
strategies are on different markets. The late-break winners are trend rules on
`futures_trend_daily` and `fx_major_daily`, two families that produce *nothing* at
any gradual decay rate in this catalogue. Decay locks trend-following out; a late
break lets it straight back in.

The mechanism is not mysterious, and it is not a bug: `break@85%` simply has more
total edge (mean 0.87 against 0.70), because it is at full strength for
five-sixths of its life. Certification tracks the average over the test window,
and by that measure the late-break catalogue is the *easiest* thing in the lab.

**The uncomfortable part is what that means about the verdict.** A market that
worked fully for forty years and then died certifies easily; one that faded gently
over forty-eight years does not — even though the second is in better shape
*today* (edge 0.51 against 0.15). The ladder is measuring "did this work, on
average, across its history", and that is not the same question as "is this
working now". The two answers diverge most exactly when an edge dies abruptly and
recently, which is the realistic failure mode and the one a live trader has the
least warning of.

**G2b's final-quarter leg (F25) is the only gate that pushes back, and it is
operating at its limit.** It rejected 9 of the 52 gauntleted candidates — 19% of
the whole funnel, the largest share it has ever taken. But the four that got
through cleared it by **+0.00, +0.01, +0.01 and +0.02**, against a +0.25 bar. Four
certifications, decided by hundredths, on the one gate designed to catch this.

Raising that bar to block them is precisely the p-hacking F22 defines — a
threshold moved because it let through candidates one dislikes. Shortening the
window costs the statistical power that makes the gate meaningful. So the change
made instead is to **report the margin rather than move the bar**: every gate now
records how much room its binding statistic had, and the report prints the
tightest one for each proven bot. This is the same reasoning that produced
`burden_headroom` for G6 (F17), generalised — a certification that clears its
narrowest gate by a hundredth is different evidence from one that clears it by two
tenths, and pass/fail cannot tell you which you are holding.

The principled fix for the gate itself is a *changepoint* statistic rather than a
shorter window: ask whether the late alpha series contains a break, not whether
its average is high enough. That is written down in `ITERATION-PROMPT.md` and has
not been built.

---

## What is still wrong, or unproven

Stated because the point of this document is not to look finished.

1. **The decay *rate* is still a free parameter, but it is now reported as a
   curve rather than assumed.** F23 sweeps it: 4 distinct strategies survive a
   24-year halflife, 0 survive 12, 0 survive an abrupt break in the first half.
   That is the honest form of every headline in this repository. What is still
   missing is any evidence about *where in that range the real world sits* —
   nothing here estimates a decay rate from data, and the curve is steep enough
   between 24 and 12 years that the answer flips completely across it.
   The curve is also carried almost entirely by strategies discovered at the
   shipped rate; the untuned archetype panel certifies at most one at any rung, so
   it is a curve for these strategies, not for the strategy space (F23).
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
6. **The FPR upper bound is 2.2%, not zero.** Ten independent probes returning 0
   of 137 is a much tighter bound than the single probe it replaces (F27), but "no
   false positive was observed in 137 tries" is not "the false-positive rate is
   zero", and the ladder's thresholds rest on the difference.
