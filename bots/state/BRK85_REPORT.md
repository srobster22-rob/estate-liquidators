# Bot factory: run report

_Generated 2026-08-12 13:29:18 from `fast_brk85.json`._

## Result

**4 distinct strategies passed all eight gates** (4 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes). Read that number together with the two sections below it: what survives this run's *closing* standard of proof rather than the standard in force when each bot was found, and what survives a faster decay rate. Both are more conservative.

640 candidates were screened across 4 generations and 0 search-space expansions; 52 reached the gauntlet; 3,976 backtests were run.

Markets represented: `futures_trend_daily~break@85%`, `fx_major_daily~break@85%`.

**Every tradeable family's edge decays** — halflife half the series with a 35% floor by default, so the average edge across an instance is 70% of its opening value. A catalogue identical at the last bar and the first flatters everything tested on it.

The certified bots retain **76%-91%** of their first-half alpha in the second half. For scale, a textbook trend bot on a decaying trend market retains 11% — costs are fixed, so a 30% cut in gross edge takes ~90% of net alpha, and strategies running close to their cost floor die first. What survives decay is what had margin over costs to begin with.

**Search-burden headroom.** These were certified after 52 confirmation tests, and G6's luck bar rises with that count — so the count matters as much as the Sharpe. Headroom is the largest search each bot's evidence could have come out of and still clear G6: **4 of 4 genomes clear a bar ten times harder than the one they actually faced** (headroom 2,069,621 down to 1,163). Read it before the Sharpe — a bot whose headroom is close to the tests already run would vanish in a more serious hunt.

## Re-judged at the standard this run finished with

G6's luck bar rises with the size of the search — that is what it is for — so a bot certified in an early generation was measured against a smaller search than this run eventually became. Two inputs drift as a run continues: the confirmation-test count, and the variance of the trial-Sharpe distribution the bar is built from. Below, every proven bot is re-judged at the closing values (**52 confirmation tests, trial variance 0.143**). Nothing here can certify a bot that was not already certified; it can only take one away.

**All 4 genomes (4 distinct strategies) still clear the closing bar.** The headline is not an artefact of when in the run each bot happened to be found.

## How much of this depends on the decay rate

The catalogue's fade — halflife half the series, 35% floor — was chosen as the mildest setting that still certifies anything, not measured from data. So the headline above is not a number, it is a number *at one rate*. The sweep below re-runs a **fixed, pre-registered panel** — every untuned archetype of every family, plus every distinct strategy the search has certified — at each fade rate. Same genomes, same gates, same multiplicity denominator, seed-paired instances: the only thing that differs between two rows is how fast the edge goes away.

| rung | halflife | mean edge | edge at end | distinct strategies | genomes | markets |
|---|---|---|---|---|---|---|
| `stationary` | never | 1.00 | 1.00 | 8 | 16 | `commodity_meanrev_daily`, `eq_largecap_daily`, `futures_trend_daily`, `fx_major_daily` |
| `hl=1.00x` | 48 yr | 0.82 | 0.68 | 4 | 11 | `commodity_meanrev_daily`, `eq_largecap_daily` |
| `hl=0.50x` | 24 yr | 0.70 | 0.51 | 3 | 8 | `commodity_meanrev_daily` |
| `hl=0.25x` | 12 yr | 0.57 | 0.39 | 0 | 0 | — |
| `hl=0.125x` | 6 yr | 0.47 | 0.35 | 0 | 0 | — |
| `hl=0.125x/f10` | 6 yr | 0.26 | 0.10 | 0 | 0 | — |
| `break@45%` | abrupt | 0.53 | 0.15 | 0 | 0 | — |
| `break@85%` | abrupt | 0.87 | 0.15 | 1 | 1 | `commodity_meanrev_daily` |

Read it as a sentence: **the strategies this lab has found survive a halflife of about 24 simulated years and are gone by 12.** Four to none across one rung that only takes the mean edge from 0.70 to 0.57 — because the whole population of viable strategies sits in a narrow band just above the replication bar, so a 20% edge cut does not thin the field, it empties it. Nothing survives an abrupt break in the first half of its life. Everything above is conditional on where in that range the real world sits, and this repository cannot tell you.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 25 | 52% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 14 | 29% | worked only on the instances it was bred on (instance luck) |
| G2b-durability | 9 | 19% | edge faded across the series (a crowded or arbitraged anomaly) |

## Proven bots

### `0c93744bd064` — futures_trend_daily~break@85%

```
momentum(lb=61)x1.27 | trend_regime(n=21) -> thr 0.59/0.12 both proportional lev<=5.0
```

- market: **futures_trend_daily~break@85%** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.17)
- found in generation 3 via mutant from 05fdb8c008cf
- **search-burden headroom: 74,201** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 34. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | — | alphaSR +0.30 (need +0.25), 4381 trades, 88% instances positive |
| PASS | G2-replication | — | median alphaSR +0.53 (need +0.35), 100% of 20 instances positive (need 70%), median DD -20.4% / worst -37.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | — | late-half alphaSR +0.48, final-quarter +0.26 (both need +0.25) vs early half +0.53, retained 91% (ratio not gated: this market decays by design) |
| PASS | G3-controls | — | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.02] |
| PASS | G4-stress | — | 2x costs +0.44 (need +0.15), 3x +0.41 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | — | real +0.46 vs null +0.03+-0.06 (p99 +0.18) -> z=7.0, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | — | DSR 1.000 (need 0.95) vs luck bar SR 0.23 after 34 confirmation tests (would still pass up to 74,201); Bonferroni p 4.86e-11 (need <=0.05) \| stricter all-trials view (480 screened): DSR 1.000 vs SR 0.33, p 6.85e-10 |
| PASS | G7-stress-pool | — | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +3.0%, median DD -19.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.55 | +3.0% | 5.6% | -19.2% | 0.08 | 29 | 0.17% | 0.28 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily~break@85%` +0.24, `rates_daily~break@85%` +0.07, `eq_index_daily~break@85%` +0.04, `fx_em_daily~break@85%` -0.01, `eq_largecap_daily~break@85%` -0.36, `eq_smallcap_daily~break@85%` -0.56

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily~break@85%",
  "genes": [
    {
      "name": "momentum",
      "params": {
        "lb": 61
      },
      "weight": 1.268,
      "mode": 1
    }
  ],
  "filters": [
    {
      "name": "trend_regime",
      "params": {
        "n": 21
      }
    }
  ],
  "combine": "weighted",
  "entry_threshold": 0.587,
  "exit_threshold": 0.116,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.723,
  "target_vol": 0.284,
  "max_leverage": 5.0,
  "rebalance_band": 0.234,
  "atr_n": 31,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": null,
  "dd_resume": 64,
  "bot_id": "0c93744bd064",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "05fdb8c008cf"
  ]
}
```

</details>

### `a5a110d0003f` — fx_major_daily~break@85%

```
ma_cross(fast=39,slow=67)x1.00 + momentum(lb=60)x1.00 -> thr 0.04/0.02 both proportional lev<=2.0
```

- market: **fx_major_daily~break@85%** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.56)
- found in generation 3 via mutant from 25a6bd7829c5
- **search-burden headroom: 1,163** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 36. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | — | alphaSR +0.33 (need +0.25), 10233 trades, 75% instances positive |
| PASS | G2-replication | — | median alphaSR +0.38 (need +0.35), 100% of 20 instances positive (need 70%), median DD -15.5% / worst -22.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | — | late-half alphaSR +0.34, final-quarter +0.26 (both need +0.25) vs early half +0.44, retained 78% (ratio not gated: this market decays by design) |
| PASS | G3-controls | — | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.02] |
| PASS | G4-stress | — | 2x costs +0.35 (need +0.15), 3x +0.34 (need +0.00), +1 bar delay +0.36 (need +0.10) |
| PASS | G5-permutation | — | real +0.33 vs null +0.01+-0.07 (p99 +0.13) -> z=4.6, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | — | DSR 1.000 (need 0.95) vs luck bar SR 0.23 after 36 confirmation tests (would still pass up to 1,163); Bonferroni p 6.33e-05 (need <=0.05) \| stricter all-trials view (480 screened): DSR 0.994 vs SR 0.33, p 8.44e-04 |
| PASS | G7-stress-pool | — | median alphaSR +0.31 (need +0.28), 100% positive (need 65%), CAGR +1.2%, median DD -18.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.31 | +0.33 | +1.2% | 3.8% | -18.3% | 0.04 | 69 | 0.04% | 0.43 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily~break@85%` +0.56, `rates_daily~break@85%` +0.12, `fx_em_daily~break@85%` +0.09, `eq_index_daily~break@85%` +0.08, `eq_largecap_daily~break@85%` -0.22, `eq_smallcap_daily~break@85%` -0.29

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily~break@85%",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 39,
        "slow": 67
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "momentum",
      "params": {
        "lb": 60
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.0442,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "a5a110d0003f",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "25a6bd7829c5"
  ]
}
```

</details>

### `c959aa71156b` — futures_trend_daily~break@85%

```
ma_cross(fast=15,slow=61)x1.00 -> thr 0.10/0.02 both proportional lev<=2.0  [stop 4.2atr]
```

- market: **futures_trend_daily~break@85%** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.17)
- found in generation 4 via mutant from 70e4fb6fd836
- **search-burden headroom: 2,069,621** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 42. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | — | alphaSR +0.27 (need +0.25), 7817 trades, 75% instances positive |
| PASS | G2-replication | — | median alphaSR +0.55 (need +0.35), 100% of 20 instances positive (need 70%), median DD -30.6% / worst -37.3% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | — | late-half alphaSR +0.44, final-quarter +0.27 (both need +0.25) vs early half +0.59, retained 76% (ratio not gated: this market decays by design) |
| PASS | G3-controls | — | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.01, control_martingale_daily=-0.03] |
| PASS | G4-stress | — | 2x costs +0.56 (need +0.15), 3x +0.55 (need +0.00), +1 bar delay +0.57 (need +0.10) |
| PASS | G5-permutation | — | real +0.55 vs null +0.03+-0.06 (p99 +0.18) -> z=8.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | — | DSR 1.000 (need 0.95) vs luck bar SR 0.23 after 42 confirmation tests (would still pass up to 2,069,621); Bonferroni p 4.66e-15 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.33, p 7.11e-14 |
| PASS | G7-stress-pool | — | median alphaSR +0.51 (need +0.28), 100% positive (need 65%), CAGR +4.5%, median DD -33.9% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.51 | +0.56 | +4.5% | 8.5% | -33.9% | 0.09 | 49 | 0.07% | 0.56 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily~break@85%` +0.30, `rates_daily~break@85%` +0.11, `fx_em_daily~break@85%` +0.10, `eq_index_daily~break@85%` +0.07, `eq_smallcap_daily~break@85%` -0.24, `eq_largecap_daily~break@85%` -0.25

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily~break@85%",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 15,
        "slow": 61
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.1,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.1545,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": 4.24,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "c959aa71156b",
  "generation": 4,
  "origin": "mutant",
  "parents": [
    "70e4fb6fd836"
  ]
}
```

</details>

### `46a2050ff2c1` — fx_major_daily~break@85%

```
ma_cross(fast=20,slow=61)x1.00 -> thr 0.10/0.02 both proportional lev<=2.0
```

- market: **fx_major_daily~break@85%** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.56)
- found in generation 4 via transplant from d33735f301dc
- **search-burden headroom: 1,801** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 47. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | — | alphaSR +0.32 (need +0.25), 7194 trades, 75% instances positive |
| PASS | G2-replication | — | median alphaSR +0.39 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.6% / worst -26.0% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | — | late-half alphaSR +0.33, final-quarter +0.25 (both need +0.25) vs early half +0.44, retained 76% (ratio not gated: this market decays by design) |
| PASS | G3-controls | — | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.01, control_martingale_daily=-0.03] |
| PASS | G4-stress | — | 2x costs +0.34 (need +0.15), 3x +0.33 (need +0.00), +1 bar delay +0.34 (need +0.10) |
| PASS | G5-permutation | — | real +0.32 vs null +0.01+-0.07 (p99 +0.14) -> z=4.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | — | DSR 1.000 (need 0.95) vs luck bar SR 0.24 after 47 confirmation tests (would still pass up to 1,801); Bonferroni p 2.69e-04 (need <=0.05) \| stricter all-trials view (640 screened): DSR 0.995 vs SR 0.33, p 3.66e-03 |
| PASS | G7-stress-pool | — | median alphaSR +0.30 (need +0.28), 100% positive (need 65%), CAGR +1.3%, median DD -20.9% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.30 | +0.33 | +1.3% | 4.3% | -20.9% | 0.04 | 47 | 0.03% | 0.50 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily~break@85%` +0.57, `rates_daily~break@85%` +0.11, `fx_em_daily~break@85%` +0.11, `eq_index_daily~break@85%` +0.07, `eq_largecap_daily~break@85%` -0.20, `eq_smallcap_daily~break@85%` -0.20

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily~break@85%",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 20,
        "slow": 61
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.1,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "46a2050ff2c1",
  "generation": 4,
  "origin": "transplant",
  "parents": [
    "d33735f301dc"
  ]
}
```

</details>

## Portfolio

```
4 distinct strategies across 2 market(s) / 2 asset class(es)
  best single bot        alphaSR +0.51
  portfolio (lab, rho=0) alphaSR +0.82   <- upper bound, independent synthetic markets
  portfolio (rho=0.3)    alphaSR +0.65   <- plan with this one
    22.5%  0c93744bd064  futures_trend_daily~break@85% alphaSR +0.50
    33.4%  a5a110d0003f  fx_major_daily~break@85% alphaSR +0.32
    15.0%  c959aa71156b  futures_trend_daily~break@85% alphaSR +0.51
    29.1%  46a2050ff2c1  fx_major_daily~break@85% alphaSR +0.31
```

The two portfolio numbers differ because this lab generates each market family independently, so cross-family correlation is structurally zero — an assumption real asset classes violate exactly when it matters. Plan with the rho=0.3 number.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `7abdcfeca1af` | eq_largecap_daily~break@85% | +0.52 | +0.52 | 29314 | `bollinger(k=1.62,n=26)x1.00 -> thr 0.50/0.02 long proportional lev` |
| `b9bcccc697c6` | eq_largecap_daily~break@85% | +0.49 | +0.58 | 54802 | `bollinger(k=2.14,n=35)x1.00 + rsi_rev(n=14)x0.80 -> thr 0.50/0.10 ` |
| `c959aa71156b` | futures_trend_daily~break@85% | +0.49 | +0.54 | 32539 | `ma_cross(fast=15,slow=61)x1.00 -> thr 0.10/0.02 both proportional ` |
| `17c7f354a621` | eq_largecap_daily~break@85% | +0.49 | +0.60 | 107403 | `bollinger(k=2.00,n=20)x1.00 + rsi_rev(n=14)x1.00 -> thr 0.10/0.02 ` |
| `a7528ca419b7` | futures_trend_daily~break@85% | +0.48 | +0.58 | 32131 | `breakout(n=55)x1.00 unanimous ma_cross(fast=20,slow=100)x1.00 -> t` |
| `459c5829158c` | eq_largecap_daily~break@85% | +0.48 | +0.52 | 78355 | `bollinger(k=2.53,n=20)x1.00 -> thr 0.50/0.02 both proportional lev` |
| `aa7739b7387a` | futures_trend_daily~break@85% | +0.48 | +0.56 | 37051 | `breakout(n=55)x1.00 unanimous ma_cross(fast=20,slow=65)x1.00 -> th` |
| `70bce0175815` | eq_largecap_daily~break@85% | +0.47 | +0.52 | 38867 | `rsi_rev(n=14)x1.36 -> thr 0.40/0.05 both proportional lev<=2.0  [h` |
| `44cb22a8d18e` | eq_largecap_daily~break@85% | +0.47 | +0.52 | 38867 | `rsi_rev(n=14)x1.00 -> thr 0.40/0.05 both proportional lev<=2.0  [h` |
| `13332a09c5ae` | futures_trend_daily~break@85% | +0.47 | +0.57 | 51708 | `breakout(n=55)x1.00 + ma_cross(fast=20,slow=100)x1.00 -> thr 0.10/` |
| `8f07b2658c53` | eq_largecap_daily~break@85% | +0.47 | +0.52 | 67535 | `bollinger(k=2.53,n=20)x1.00 -> thr 0.50/0.02 both proportional lev` |
| `6a85efa1b597` | eq_largecap_daily~break@85% | +0.46 | +0.48 | 33665 | `bollinger(k=2.38,n=16)x1.00 -> thr 0.50/0.02 long proportional lev` |
| `37575c0f9819` | futures_trend_daily~break@85% | +0.45 | +0.52 | 21256 | `breakout(n=55)x1.00 + ma_cross(fast=20,slow=100)x1.00 -> thr 0.90/` |
| `13bf5a4a56a2` | futures_trend_daily~break@85% | +0.45 | +0.50 | 26078 | `momentum(lb=61)x1.27 \| trend_regime(n=21) -> thr 0.40/0.05 both pr` |
| `0c93744bd064` | futures_trend_daily~break@85% | +0.45 | +0.50 | 19860 | `momentum(lb=61)x1.27 \| trend_regime(n=21) -> thr 0.59/0.12 both pr` |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 160 | 5 | 16 | 14 | 0 | +0.47 | 122s |
| 2 | 1 | 160 | 5 | 12 | 0 | 0 | +0.48 | 81s |
| 3 | 1 | 160 | 5 | 12 | 0 | 2 | +0.49 | 79s |
| 4 | 1 | 160 | 5 | 12 | 0 | 2 | +0.52 | 85s |

## Standard of proof used

```json
{
  "min_oos_alpha_sr": 0.25,
  "min_repl_alpha_sr": 0.35,
  "min_repl_pos_frac": 0.7,
  "min_late_alpha_sr": 0.25,
  "min_edge_retention": 0.5,
  "min_stress_alpha_sr": 0.28,
  "min_stress_pos_frac": 0.65,
  "max_drawdown": 0.35,
  "min_trades": 30,
  "max_control_alpha_sr": 0.3,
  "cost_stress_2x_min": 0.15,
  "cost_stress_3x_min": 0.0,
  "delay_stress_min": 0.1,
  "perm_p_max": 0.01,
  "min_dsr": 0.95,
  "family_wise_p_max": 0.05,
  "n_oos_instances": 8,
  "n_repl_instances": 20,
  "n_control_instances": 10,
  "n_stress_instances": 20,
  "n_perm_instances": 5,
  "n_perm_draws": 120,
  "perm_block": 5
}
```

## What to do next

1. Re-run the identical gauntlet on **real bars** for the same instrument type: `python bots/run.py verify <bot_id> --data path/to/csvs`. Until that passes, a proven bot is a proven bot *about a market model*.
2. Check the `travels to` row. A rule that only works on the one family it was bred on is a fit to that generator's parameters.
3. Paper-trade before funding. Nothing in this repository has touched a live order book, a real spread, or a real fill.
