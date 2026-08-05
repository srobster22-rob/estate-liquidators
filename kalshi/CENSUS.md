# Kalshi Bot Factory — Market Census

The one estimate the whole dollar figure rested on, replaced with a count.

> **534 economics contracts per year**, from 2,668 settled contracts across 8 series over 5.0 years.
>
> Source: "Information Efficiency Across Macroeconomic Prediction Markets: Evidence from Kalshi" — 2,668 settled contracts, 8 series, July 2021-June 2026

Counted from published sources rather than from `GET /markets`: Kalshi's API returns 403 to every request from this environment, and so does kalshi.com itself. That makes this a *sourced count* rather than a *measurement*, and the distinction is worth keeping — the honest next step is still to run the census against the live API from a machine with egress.

## The release calendar

| series | ticker | events/yr | evidence |
|---|---|---|---|
| Initial jobless claims | `KXJOBLESSCLAIMS` | 52 | ticker confirmed; weekly DOL release |
| CPI headline | `KXCPI` | 12 | ticker confirmed; monthly BLS release |
| Core CPI | — | 12 | ladder example published; monthly |
| Nonfarm payrolls | `KXPAYROLLS` | 12 | ticker confirmed; monthly BLS release |
| Unemployment rate | `KXU3MAX` | 12 | ticker confirmed; monthly BLS release |
| Fed / FOMC rate decision | `KXFED` | 8 | ticker confirmed; 8 scheduled meetings a year |
| PCE inflation | — | 12 | series named in coverage; monthly BEA release |
| GDP | — | 4 | series named in coverage; quarterly BEA release |
| **total** | | **124** | independent resolutions per year |

534 contracts ÷ 124 events = **4.3 rungs per event**, consistent with the ~6-threshold ladders visible in published Core CPI examples. Two independently sourced numbers landing on a plausible third is weak evidence, but it is evidence.

## Contracts are not independent bets

A Kalshi CPI market is a **ladder**: nested rungs ("above 0.2%", "above 0.3%", …) that all settle from one printed number. Six rungs is one bet resolved six ways. So the census yields two numbers doing two different jobs:

- **income** scales with contracts (~534/yr) — each rung has its own book and its own depth
- **risk and evidence** scale with events (~124/yr) — this is the honest denominator for a confidence interval

## What it does to the answer

| | markets/yr | annual income |
|---|---|---|
| previous estimate | 250 | $133 |
| **counted** | **534** | **$284** |

At the replicated edge of +53.3¢ per market, the count **clears** the $250/yr bar.

The income went up because the count went up, not because the bot got better. The edge per market is unchanged and so is everything the gate said about it.

