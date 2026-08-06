# Kalshi Bot Factory — Bracket Arbitrage

The one structure in this project with **zero variance**: buy all N mutually exclusive brackets for under 100¢, exactly one pays 100¢, profit locked at trade time. K21 showed variance dominates edge, so a zero-variance trade is the best possible position on that axis and deserved a proper look.

It loses anyway, for a structural reason.

## What it is worth

| | |
|---|---|
| fires in | **2.9%** of bracket sets (118 of 4,000) |
| when it fires | +174¢ |
| losing fires | **0** — riskless means this is zero |
| per set offered | +5.12¢ |
| observations to sign the edge | 195 sets = **1.3 years** |
| **annual income** | **$8/yr** |

Only 150 bracket sets a year exist, so even a perfect capture is a rounding error. That alone would end it — but the reason it fails is more interesting and more general.

## The margin is 1¢ and it is shared across 5 legs

| percentile | margin (100 − Σ asks) |
|---|---|
| median | 1¢ |
| 75th | 2¢ |
| 90th | 3¢ |
| 99th | 6¢ |
| max | 10¢ |

## One tick of slippage destroys it

| slippage per leg | ¢/set | annual | fires that now LOSE |
|---|---|---|---|
| +0 tick | +5.12¢ | $+8 | **0/118** |
| +1 tick | -1.92¢ | $-3 | **105/118** |
| +2 tick | -8.96¢ | $-13 | **118/118** |

## Why: an N-leg arb pays N × slippage to capture ONE margin

| legs | cost of 1 tick each | opportunities still profitable |
|---|---|---|
| 2 | 2¢ | 22% |
| 3 | 3¢ | 10% |
| 5 | 5¢ | 1% |
| 8 | 8¢ | 0% |

Break-even per-leg slippage is `margin / N`. At a median margin of 1¢ over 5 legs that is **0.2 ticks** — and **the tick is 1¢**. The minimum possible adverse move is five times what the trade can afford. This is not a tuning problem; it is the price grid against the structure.

## Both doors are shut

The only version that survives slippage is **resting** orders on every leg, because a maker fill happens at your price by definition. That swaps slippage risk for fill risk — you get some legs and not others, leaving a directional position you never chose — and `maker_spread` already showed resting orders are negative here at **every** fill rate from 0.15 to 1.00.

So the zero-variance trade and the zero-slippage trade are each blocked by the other's risk. The general lesson outlives Kalshi: **leg count is leverage on execution risk, and it points the wrong way.**

## K23 — incoherence *is* quote noise

A bracket family at 23× the frequency should have dominated, on the information-cost ranking. It earns exactly nothing, and this is why.

| quote noise | sets incoherent | median margin | edge/set |
|---|---|---|---|
| 0.4¢ | 1.8% | 1.0¢ | +0.00¢ |
| 0.6¢ | 9.6% | 1.0¢ | +0.00¢ |
| 1.0¢ | 61.4% | 1¢ | +0.28¢ |
| 1.4¢ | 93.1% | 2.0¢ | +12.47¢ |
| 2.0¢ | 99.1% | 2¢ | +145.84¢ |
| 3.0¢ | 99.9% | 3¢ | +543.43¢ |

Violently non-linear: 2.3× the noise moves the edge four orders of magnitude. A liquid market is liquid *because* its quotes are tight.

## K24 — but quote noise was not the only channel

Bracket probabilities sum to 1 at every step, so their moves sum to zero, and any operator applied identically to every leg that is also **linear** returns a zero-sum vector — it cannot move the quoted total. Isolating each part of the quoting layer confirms the rule and turns up a channel nobody had noticed:

| channel | incoherent sets | |
|---|---|---|
| no lag at all | 0.0% | baseline |
| uniform lag, cap 1000¢ (never binds) | **0.0%** | linear ⇒ neutral |
| uniform lag, cap 3¢ | **94.2%** | clipping is *not* linear |
| uniform lag, cap 1¢ | 57.8% | non-monotone: clip every leg and it is uniform again |
| longshot compression, γ 1.0 → 0.9 | 0.0% | too gentle to clear the spread |
| symmetric quote noise, 2¢ | 100% | the channel K22 and K23 measured |

`underreact_cap` binds on the legs making big moves and not on the ones making small moves, so the truncated lags stop summing to zero. That channel has been in `markets.py` since round one and neither previous conclusion knew it existed.

**Asymmetric staleness** is the other channel, and it needs no wide book. One leg frozen while the others track dislocates the set by however far the truth travels during the freeze — a function of volatility and update latency, with spread nowhere in it. `crypto_bracket_stale` is `crypto_bracket_hourly` with the *same salt*, so the paired groups differ in nothing else.

| family | fires | ¢/set | median margin | **max margin** |
|---|---|---|---|---|
| `crypto_bracket_hourly` | 0 | +0.00¢ | 1¢ | **3¢** |
| `crypto_bracket_stale` | 124 | +18.71¢ | 3¢ | **33¢** |
| `index_bracket_daily` | 53 | +4.38¢ | 2¢ | **8¢** |

Sum-of-N-independent-wobbles is concentrated; one leg's unbounded drift is not. The centre moves 3×; **the tail moves 10×** — and only the tail clears N ticks, so the tail is the only part a filter can reach.

## The filter that was useless becomes decisive

A minimum-margin filter is the obvious defence against per-leg slippage. On the noise channel it selects *nothing* (`min_edge=5` on `index_bracket_daily` → 0 fires). On the staleness channel, same filter, same arithmetic:

| min margin | slippage/leg | fires | **losing** | ¢/set | $/yr |
|---|---|---|---|---|---|
| 0¢ | +0 tick | 183 | **0** | +18.45¢ | $+647 |
| 0¢ | +1 tick | 182 | **133** | -11.56¢ | $-405 |
| 3¢ | +0 tick | 128 | **0** | +25.84¢ | $+905 |
| 3¢ | +1 tick | 127 | **44** | +6.28¢ | $+220 |
| 5¢ | +0 tick | 109 | **0** | +26.37¢ | $+924 |
| 5¢ | +1 tick | 108 | **5** | +9.64¢ | $+338 |
| 8¢ | +0 tick | 76 | **0** | +22.50¢ | $+788 |
| 8¢ | +1 tick | 76 | **0** | +12.32¢ | $+432 |
| 8¢ | +2 tick | 76 | **31** | +2.16¢ | $+76 |
| 12¢ | +0 tick | 52 | **0** | +18.02¢ | $+631 |
| 12¢ | +1 tick | 52 | **0** | +11.88¢ | $+416 |
| 12¢ | +2 tick | 52 | **0** | +5.76¢ | $+202 |

So the corrected statement is: **an N-leg arb needs a margin above N ticks, and whether any exist depends on the tail of the margin distribution — which depends on the incoherence channel, not on the spread.** K22's mechanism was right; the conclusion drawn from it was conditional on a distribution nobody had varied.

### It still fails the gate

At `min_edge=8` with 1 tick of slippage on every leg this clears **9 of 11** criteria — OOS, holdout, bootstrap, Holm, half-edge, and the $250 dollar bar — and fails two:

- **stress** (−1.95¢ at 2 ticks + 1.5× fees). A real failure: the slippage wall moved further out, it did not disappear.
- **tail risk**, which counts *legs*. A bracket arb books four guaranteed-losing legs per winning one, so a trade that cannot lose reads as an 80% loss rate. Documented in `evaluate.py` as deliberately pessimistic — but for a *riskless* structure that is a categorical blind spot, not conservatism, and it is left alone rather than loosened to admit this candidate.

And the size of all of it is directly proportional to `stale_leg_prob = 0.35`, which is a number with no evidence behind it whatsoever.

