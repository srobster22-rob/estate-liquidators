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

