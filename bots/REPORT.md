# Bot factory: run report

_Generated 2026-08-12 22:34:08 from `run_state.json`._

## Result

**4 distinct strategies passed all eight gates** (13 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes). Read that number together with the two sections below it: what survives this run's *closing* standard of proof rather than the standard in force when each bot was found, and what survives a faster decay rate. Both are more conservative.

9,570 candidates were screened across 19 generations and 4 search-space expansions; 371 reached the gauntlet; 14,589 backtests were run.

**All of them trade one market family: `commodity_meanrev_daily`.** Ten other tradeable families were searched every generation and yielded nothing that survived the ladder. That is the most informative result in this report, and it is the expected one: the catalogue deliberately contains families where the correct answer is *do not trade this* (the strongest planted edges sit behind a 28bp spread, or behind 0.30bp/bar funding). A search that returned winners everywhere would be evidence against itself.

**Every tradeable family's edge decays** — halflife half the series with a 35% floor by default, so the average edge across an instance is 70% of its opening value. A catalogue identical at the last bar and the first flatters everything tested on it.

The certified bots retain **60%-83%** of their first-half alpha in the second half. For scale, a textbook trend bot on a decaying trend market retains 11% — costs are fixed, so a 30% cut in gross edge takes ~90% of net alpha, and strategies running close to their cost floor die first. What survives decay is what had margin over costs to begin with.

None of the 2 families that decay *faster* than the default (`futures_trend_decay_daily`, `eq_largecap_break_daily`) certified anything.

**Search-burden headroom.** These were certified after 371 confirmation tests, and G6's luck bar rises with that count — so the count matters as much as the Sharpe. Headroom is the largest search each bot's evidence could have come out of and still clear G6: **13 of 13 genomes clear a bar ten times harder than the one they actually faced** (headroom 70,529 down to 7,353). Read it before the Sharpe — a bot whose headroom is close to the tests already run would vanish in a more serious hunt.

## Re-judged at the standard this run finished with

G6's luck bar rises with the size of the search — that is what it is for — so a bot certified in an early generation was measured against a smaller search than this run eventually became. Two inputs drift as a run continues: the confirmation-test count, and the variance of the trial-Sharpe distribution the bar is built from. Below, every proven bot is re-judged at the closing values (**371 confirmation tests, trial variance 0.128**). Nothing here can certify a bot that was not already certified; it can only take one away.

**All 13 genomes (4 distinct strategies) still clear the closing bar.** The headline is not an artefact of when in the run each bot happened to be found.

## How much of this depends on the decay rate

The catalogue's fade — halflife half the series, 35% floor — was chosen as the mildest setting that still certifies anything, not measured from data. So the headline above is not a number, it is a number *at one rate*. The sweep below re-runs a **fixed, pre-registered panel** — every untuned archetype of every family, plus every distinct strategy the search has certified — at each fade rate. Same genomes, same gates, same multiplicity denominator, seed-paired instances: the only thing that differs between two rows is how fast the edge goes away.

| rung | halflife | mean edge | edge at end | distinct strategies | genomes | markets |
|---|---|---|---|---|---|---|
| `stationary` | never | 1.00 | 1.00 | 8 | 14 | `commodity_meanrev_daily`, `eq_largecap_daily`, `futures_trend_daily`, `fx_major_daily` |
| `hl=1.00x` | 48 yr | 0.82 | 0.68 | 4 | 9 | `commodity_meanrev_daily` |
| `hl=0.50x` | 24 yr | 0.70 | 0.51 | 4 | 9 | `commodity_meanrev_daily` |
| `hl=0.25x` | 12 yr | 0.57 | 0.39 | 0 | 0 | — |
| `hl=0.125x` | 6 yr | 0.47 | 0.35 | 0 | 0 | — |
| `hl=0.125x/f10` | 6 yr | 0.26 | 0.10 | 0 | 0 | — |
| `break@45%` | abrupt | 0.53 | 0.15 | 0 | 0 | — |
| `break@85%` | abrupt | 0.87 | 0.15 | 0 | 0 | — |

**How much room did the survivors have?** Each certified bot's *margin* is how far its narrowest Sharpe-denominated gate cleared its threshold. The count above is a lagging indicator and this is a leading one — the whole distribution collapses a full rung before the count does.

| rung | certified | min margin | median | max | binding gate |
|---|---|---|---|---|---|
| `stationary` | 14 | +0.018 | +0.253 | +0.331 | G2-replication (6), G2b-durability (4), G1-oos (3), G7-stress-pool (1) |
| `hl=1.00x` | 9 | +0.097 | +0.127 | +0.156 | G1-oos (6), G2-replication (2), G2b-durability (1) |
| `hl=0.50x` | 9 | +0.000 | +0.026 | +0.054 | G2b-durability (5), G1-oos (4) |
| `hl=0.25x` | 0 | — | — | — | — |
| `hl=0.125x` | 0 | — | — | — | — |
| `hl=0.125x/f10` | 0 | — | — | — | — |
| `break@45%` | 0 | — | — | — | — |
| `break@85%` | 0 | — | — | — | — |

Read it as a sentence: **the strategies this lab has found survive a halflife of about 24 simulated years and are gone by 12.** Four to none across one rung that only takes the mean edge from 0.70 to 0.57 — because the whole population of viable strategies sits in a narrow band just above the replication bar, so a 20% edge cut does not thin the field, it empties it. Nothing survives an abrupt break in the first half of its life. Everything above is conditional on where in that range the real world sits, and this repository cannot tell you.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 291 | 81% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 58 | 16% | worked only on the instances it was bred on (instance luck) |
| G2b-durability | 8 | 2% | edge faded across the series (a crowded or arbitraged anomaly) |
| G4-stress | 1 | 0% | edge smaller than 2x costs or one bar of delay |

## Proven bots

### `aae521bbfb56` — commodity_meanrev_daily

```
rsi_rev(n=11)x1.00 + rsi_rev(n=19)x1.53 -> thr 0.40/0.05 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 13 via mutant from 289b0b31a93c
- **search-burden headroom: 9,110** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.026 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.072 | alphaSR +0.32 (need +0.25), 7985 trades, 88% instances positive |
| PASS | G2-replication | +0.073 | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -33.3% / worst -48.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.026 | late-half alphaSR +0.42, final-quarter +0.28 (both need +0.25) vs early half +0.51, retained 83% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.294 | worst \|alphaSR\| 0.01 (allowed 0.30) [control_efficient_daily=-0.01, control_martingale_daily=+0.01] |
| PASS | G4-stress | +0.195 | 2x costs +0.35 (need +0.15), 3x +0.29 (need +0.00), +1 bar delay +0.36 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.41 vs null +0.02+-0.07 (p99 +0.17) -> z=5.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 9,110); Bonferroni p 6.58e-07 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.946 vs SR 0.39, p 1.70e-05 |
| PASS | G7-stress-pool | +0.136 | median alphaSR +0.42 (need +0.28), 100% positive (need 65%), CAGR +3.3%, median DD -32.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.42 | +0.39 | +3.3% | 9.4% | -32.2% | 0.06 | 51 | 0.54% | 0.15 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.06, `rates_daily` +0.02, `eq_index_daily` +0.01, `eq_intraday_15m` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 11
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 19
      },
      "weight": 1.5291,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.4,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "aae521bbfb56",
  "generation": 13,
  "origin": "mutant",
  "parents": [
    "289b0b31a93c"
  ]
}
```

</details>

### `696e318c1767` — commodity_meanrev_daily

```
rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both proportional lev<=2.9
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 14 via mutant from 037fff769b79
- **search-burden headroom: 7,640** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.005 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.005 | alphaSR +0.26 (need +0.25), 17372 trades, 88% instances positive |
| PASS | G2-replication | +0.092 | median alphaSR +0.44 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.3% / worst -53.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.025 | late-half alphaSR +0.35, final-quarter +0.28 (both need +0.25) vs early half +0.48, retained 73% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.245 | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=+0.00] |
| PASS | G4-stress | +0.225 | 2x costs +0.38 (need +0.15), 3x +0.31 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.46 vs null +0.01+-0.06 (p99 +0.17) -> z=7.0, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 7,640); Bonferroni p 4.82e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.930 vs SR 0.39, p 1.24e-08 |
| PASS | G7-stress-pool | +0.123 | median alphaSR +0.40 (need +0.28), 100% positive (need 65%), CAGR +3.2%, median DD -27.7% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.40 | +0.40 | +3.2% | 9.0% | -27.7% | 0.05 | 117 | 0.63% | 0.20 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.31, `eq_largecap_break_daily` +0.16, `rates_daily` +0.04, `eq_index_daily` +0.02, `eq_smallcap_daily` -0.01, `fx_em_daily` -0.09

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.5278,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.147,
  "max_leverage": 2.9259,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "696e318c1767",
  "generation": 14,
  "origin": "mutant",
  "parents": [
    "037fff769b79"
  ]
}
```

</details>

### `9dbfe2fa405b` — commodity_meanrev_daily

```
rsi_rev(n=11)x1.00 + rsi_rev(n=19)x1.53 -> thr 0.40/0.05 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 14 via mutant from aae521bbfb56
- **search-burden headroom: 9,110** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.026 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.072 | alphaSR +0.32 (need +0.25), 7985 trades, 88% instances positive |
| PASS | G2-replication | +0.073 | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -33.3% / worst -48.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.026 | late-half alphaSR +0.42, final-quarter +0.28 (both need +0.25) vs early half +0.51, retained 83% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.294 | worst \|alphaSR\| 0.01 (allowed 0.30) [control_efficient_daily=-0.01, control_martingale_daily=+0.01] |
| PASS | G4-stress | +0.195 | 2x costs +0.35 (need +0.15), 3x +0.29 (need +0.00), +1 bar delay +0.36 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.41 vs null +0.02+-0.07 (p99 +0.17) -> z=5.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 9,110); Bonferroni p 6.58e-07 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.946 vs SR 0.39, p 1.70e-05 |
| PASS | G7-stress-pool | +0.136 | median alphaSR +0.42 (need +0.28), 100% positive (need 65%), CAGR +3.3%, median DD -32.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.42 | +0.39 | +3.3% | 9.4% | -32.2% | 0.06 | 51 | 0.54% | 0.15 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.06, `rates_daily` +0.02, `eq_index_daily` +0.01, `eq_intraday_15m` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 11
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 19
      },
      "weight": 1.5291,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.4,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.1877,
  "max_leverage": 2.0,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "9dbfe2fa405b",
  "generation": 14,
  "origin": "mutant",
  "parents": [
    "aae521bbfb56"
  ]
}
```

</details>

### `2f6e9a69b3d1` — commodity_meanrev_daily

```
bollinger(k=2.81,n=49)x0.32 -> thr 0.08/0.02 both proportional lev<=2.9  [hold<=106]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 15 via mutant from 6b176fbaa56a
- **search-burden headroom: 46,962** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.031 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.037 | alphaSR +0.29 (need +0.25), 14057 trades, 100% instances positive |
| PASS | G2-replication | +0.139 | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.8% / worst -49.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.031 | late-half alphaSR +0.35, final-quarter +0.28 (both need +0.25) vs early half +0.58, retained 60% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.246 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.02] |
| PASS | G4-stress | +0.276 | 2x costs +0.43 (need +0.15), 3x +0.37 (need +0.00), +1 bar delay +0.45 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.04+-0.06 (p99 +0.19) -> z=7.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 46,962); Bonferroni p 1.08e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.997 vs SR 0.39, p 2.78e-09 |
| PASS | G7-stress-pool | +0.174 | median alphaSR +0.45 (need +0.28), 100% positive (need 65%), CAGR +4.0%, median DD -31.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.45 | +0.43 | +4.0% | 10.5% | -31.4% | 0.05 | 96 | 0.70% | 0.23 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.37, `eq_largecap_break_daily` +0.20, `eq_smallcap_daily` +0.06, `rates_daily` +0.01, `eq_index_daily` -0.02, `fx_em_daily` -0.03

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 2.8065,
        "n": 49
      },
      "weight": 0.3212,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.023,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.585,
  "target_vol": 0.147,
  "max_leverage": 2.869,
  "rebalance_band": 0.273,
  "atr_n": 31,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 106,
  "min_hold": 5,
  "dd_halt": null,
  "dd_resume": 42,
  "bot_id": "2f6e9a69b3d1",
  "generation": 15,
  "origin": "mutant",
  "parents": [
    "6b176fbaa56a"
  ]
}
```

</details>

### `0a3b10605a98` — commodity_meanrev_daily

```
rsi_rev(n=14)x1.50 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 15 via crossover from b47fea13e0c4, 696e318c1767
- **search-burden headroom: 51,170** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.055 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.064 | alphaSR +0.31 (need +0.25), 32454 trades, 100% instances positive |
| PASS | G2-replication | +0.141 | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -31.0% / worst -51.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.055 | late-half alphaSR +0.38, final-quarter +0.30 (both need +0.25) vs early half +0.56, retained 67% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.260 | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.232 | 2x costs +0.38 (need +0.15), 3x +0.30 (need +0.00), +1 bar delay +0.43 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.02+-0.06 (p99 +0.17) -> z=7.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 51,170); Bonferroni p 1.14e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.998 vs SR 0.39, p 2.95e-09 |
| PASS | G7-stress-pool | +0.171 | median alphaSR +0.45 (need +0.28), 100% positive (need 65%), CAGR +3.9%, median DD -30.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.45 | +0.44 | +3.9% | 9.8% | -30.2% | 0.08 | 213 | 0.90% | 0.21 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.37, `eq_largecap_break_daily` +0.19, `eq_index_daily` +0.01, `eq_smallcap_daily` +0.01, `rates_daily` +0.00, `fx_major_daily` -0.10

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 14
      },
      "weight": 1.5047,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.5278,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.02,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "0a3b10605a98",
  "generation": 15,
  "origin": "crossover",
  "parents": [
    "b47fea13e0c4",
    "696e318c1767"
  ]
}
```

</details>

### `edc7823d5f41` — commodity_meanrev_daily

```
rsi_rev(n=24)x1.53 -> thr 0.09/0.05 both proportional lev<=2.9
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 16 via mutant from 696e318c1767
- **search-burden headroom: 7,353** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.004 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.004 | alphaSR +0.25 (need +0.25), 16495 trades, 88% instances positive |
| PASS | G2-replication | +0.091 | median alphaSR +0.44 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.7% / worst -53.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.028 | late-half alphaSR +0.35, final-quarter +0.28 (both need +0.25) vs early half +0.49, retained 71% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.245 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=+0.00] |
| PASS | G4-stress | +0.227 | 2x costs +0.38 (need +0.15), 3x +0.31 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.46 vs null +0.01+-0.06 (p99 +0.17) -> z=6.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 7,353); Bonferroni p 7.08e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.926 vs SR 0.39, p 1.83e-08 |
| PASS | G7-stress-pool | +0.122 | median alphaSR +0.40 (need +0.28), 100% positive (need 65%), CAGR +3.3%, median DD -27.8% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.40 | +0.40 | +3.3% | 9.0% | -27.8% | 0.05 | 111 | 0.61% | 0.19 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.31, `eq_largecap_break_daily` +0.16, `rates_daily` +0.04, `eq_index_daily` +0.03, `eq_smallcap_daily` +0.00, `fx_em_daily` -0.09

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.5278,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.0949,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.147,
  "max_leverage": 2.9259,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "edc7823d5f41",
  "generation": 16,
  "origin": "mutant",
  "parents": [
    "696e318c1767"
  ]
}
```

</details>

### `8624582a1e57` — commodity_meanrev_daily

```
bollinger(k=3.00,n=49)x0.32 -> thr 0.08/0.02 both proportional lev<=2.9  [hold<=106]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 16 via mutant from 05c94449cf0b
- **search-burden headroom: 44,481** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.031 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.040 | alphaSR +0.29 (need +0.25), 14063 trades, 100% instances positive |
| PASS | G2-replication | +0.138 | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.2% / worst -47.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.031 | late-half alphaSR +0.37, final-quarter +0.28 (both need +0.25) vs early half +0.58, retained 64% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.246 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.274 | 2x costs +0.42 (need +0.15), 3x +0.36 (need +0.00), +1 bar delay +0.45 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.04+-0.06 (p99 +0.19) -> z=7.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 44,481); Bonferroni p 2.47e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.997 vs SR 0.39, p 6.38e-09 |
| PASS | G7-stress-pool | +0.176 | median alphaSR +0.46 (need +0.28), 100% positive (need 65%), CAGR +3.8%, median DD -29.6% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.46 | +0.43 | +3.8% | 9.9% | -29.6% | 0.05 | 96 | 0.64% | 0.22 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.37, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.07, `rates_daily` +0.01, `eq_index_daily` -0.02, `fx_em_daily` -0.03

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 3.0,
        "n": 49
      },
      "weight": 0.3212,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.023,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.585,
  "target_vol": 0.147,
  "max_leverage": 2.869,
  "rebalance_band": 0.273,
  "atr_n": 31,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 106,
  "min_hold": 5,
  "dd_halt": null,
  "dd_resume": 42,
  "bot_id": "8624582a1e57",
  "generation": 16,
  "origin": "mutant",
  "parents": [
    "05c94449cf0b"
  ]
}
```

</details>

### `14967114bcfe` — commodity_meanrev_daily

```
rsi_rev(n=11)x1.35 + rsi_rev(n=40)x1.53 -> thr 0.08/0.05 both proportional lev<=2.9
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 16 via mutant from 9e7da7221f1c
- **search-burden headroom: 61,314** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.005 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.115 | alphaSR +0.37 (need +0.25), 20008 trades, 100% instances positive |
| PASS | G2-replication | +0.144 | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.4% / worst -44.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.005 | late-half alphaSR +0.37, final-quarter +0.26 (both need +0.25) vs early half +0.59, retained 63% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.260 | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.02] |
| PASS | G4-stress | +0.231 | 2x costs +0.38 (need +0.15), 3x +0.30 (need +0.00), +1 bar delay +0.44 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.47 vs null +0.01+-0.06 (p99 +0.16) -> z=7.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 61,314); Bonferroni p 3.82e-11 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.999 vs SR 0.39, p 9.86e-10 |
| PASS | G7-stress-pool | +0.209 | median alphaSR +0.49 (need +0.28), 100% positive (need 65%), CAGR +3.5%, median DD -29.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.49 | +0.44 | +3.5% | 8.7% | -29.4% | 0.07 | 133 | 0.81% | 0.19 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.33, `eq_largecap_break_daily` +0.16, `rates_daily` -0.02, `eq_smallcap_daily` -0.03, `eq_index_daily` -0.06, `fx_em_daily` -0.14

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 11
      },
      "weight": 1.3533,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 40
      },
      "weight": 1.5278,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.9259,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "14967114bcfe",
  "generation": 16,
  "origin": "mutant",
  "parents": [
    "9e7da7221f1c"
  ]
}
```

</details>

### `80a991776d9d` — commodity_meanrev_daily

```
rsi_rev(n=24)x1.66 -> thr 0.09/0.05 both proportional lev<=2.9
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 17 via mutant from edc7823d5f41
- **search-burden headroom: 7,353** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.004 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.004 | alphaSR +0.25 (need +0.25), 16495 trades, 88% instances positive |
| PASS | G2-replication | +0.091 | median alphaSR +0.44 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.7% / worst -53.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.028 | late-half alphaSR +0.35, final-quarter +0.28 (both need +0.25) vs early half +0.49, retained 71% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.245 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=+0.00] |
| PASS | G4-stress | +0.227 | 2x costs +0.38 (need +0.15), 3x +0.31 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.46 vs null +0.01+-0.06 (p99 +0.17) -> z=6.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 7,353); Bonferroni p 7.08e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.926 vs SR 0.39, p 1.83e-08 |
| PASS | G7-stress-pool | +0.122 | median alphaSR +0.40 (need +0.28), 100% positive (need 65%), CAGR +3.3%, median DD -27.8% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.40 | +0.40 | +3.3% | 9.0% | -27.8% | 0.05 | 111 | 0.61% | 0.19 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.31, `eq_largecap_break_daily` +0.16, `rates_daily` +0.04, `eq_index_daily` +0.03, `eq_smallcap_daily` +0.00, `fx_em_daily` -0.09

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.6599,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.0949,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.147,
  "max_leverage": 2.9259,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "80a991776d9d",
  "generation": 17,
  "origin": "mutant",
  "parents": [
    "edc7823d5f41"
  ]
}
```

</details>

### `e968878d9bc2` — commodity_meanrev_daily

```
rsi_rev(n=13)x1.53 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both proportional lev<=2.9
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 17 via mutant from 1f8c21af8a82
- **search-burden headroom: 70,529** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.061 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.071 | alphaSR +0.32 (need +0.25), 19719 trades, 88% instances positive |
| PASS | G2-replication | +0.135 | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -28.2% / worst -54.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.061 | late-half alphaSR +0.38, final-quarter +0.31 (both need +0.25) vs early half +0.57, retained 66% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.255 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.245 | 2x costs +0.40 (need +0.15), 3x +0.32 (need +0.00), +1 bar delay +0.43 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.02+-0.06 (p99 +0.18) -> z=7.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 70,529); Bonferroni p 1.28e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.999 vs SR 0.39, p 3.30e-09 |
| PASS | G7-stress-pool | +0.159 | median alphaSR +0.44 (need +0.28), 100% positive (need 65%), CAGR +3.8%, median DD -29.7% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.44 | +0.43 | +3.8% | 9.8% | -29.7% | 0.08 | 132 | 0.86% | 0.21 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.37, `eq_largecap_break_daily` +0.17, `eq_smallcap_daily` +0.01, `eq_index_daily` +0.01, `rates_daily` +0.00, `fx_em_daily` -0.10

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 13
      },
      "weight": 1.5278,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.5278,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.147,
  "max_leverage": 2.9259,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "e968878d9bc2",
  "generation": 17,
  "origin": "mutant",
  "parents": [
    "1f8c21af8a82"
  ]
}
```

</details>

### `0e4671daeb34` — commodity_meanrev_daily

```
rsi_rev(n=13)x1.53 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both proportional lev<=2.9  [hold<=63]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 18 via mutant from e968878d9bc2
- **search-burden headroom: 68,519** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.064 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.068 | alphaSR +0.32 (need +0.25), 19700 trades, 88% instances positive |
| PASS | G2-replication | +0.135 | median alphaSR +0.48 (need +0.35), 100% of 20 instances positive (need 70%), median DD -28.4% / worst -53.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.064 | late-half alphaSR +0.37, final-quarter +0.31 (both need +0.25) vs early half +0.57, retained 65% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.251 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.243 | 2x costs +0.39 (need +0.15), 3x +0.32 (need +0.00), +1 bar delay +0.43 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.02+-0.06 (p99 +0.18) -> z=7.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 68,519); Bonferroni p 1.27e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.999 vs SR 0.39, p 3.27e-09 |
| PASS | G7-stress-pool | +0.154 | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +3.8%, median DD -30.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.43 | +3.8% | 9.8% | -30.4% | 0.08 | 131 | 0.86% | 0.21 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.38, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.01, `rates_daily` +0.00, `eq_index_daily` -0.00, `fx_major_daily` -0.09

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 13
      },
      "weight": 1.5278,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.5278,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.147,
  "max_leverage": 2.9259,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 63,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "0e4671daeb34",
  "generation": 18,
  "origin": "mutant",
  "parents": [
    "e968878d9bc2"
  ]
}
```

</details>

### `f8cf35845ef9` — commodity_meanrev_daily

```
rsi_rev(n=13)x1.53 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both proportional lev<=2.9  [hold<=63]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 19 via mutant from 0e4671daeb34
- **search-burden headroom: 68,519** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.064 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.068 | alphaSR +0.32 (need +0.25), 19700 trades, 88% instances positive |
| PASS | G2-replication | +0.135 | median alphaSR +0.48 (need +0.35), 100% of 20 instances positive (need 70%), median DD -28.4% / worst -53.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.064 | late-half alphaSR +0.37, final-quarter +0.31 (both need +0.25) vs early half +0.57, retained 65% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.251 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.243 | 2x costs +0.39 (need +0.15), 3x +0.32 (need +0.00), +1 bar delay +0.43 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.02+-0.06 (p99 +0.18) -> z=7.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 68,519); Bonferroni p 1.27e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.999 vs SR 0.39, p 3.27e-09 |
| PASS | G7-stress-pool | +0.154 | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +3.8%, median DD -30.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.43 | +3.8% | 9.8% | -30.4% | 0.08 | 131 | 0.86% | 0.21 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.38, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.01, `rates_daily` +0.00, `eq_index_daily` -0.00, `fx_major_daily` -0.09

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 13
      },
      "weight": 1.5278,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.5278,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.1637,
  "max_leverage": 2.9259,
  "rebalance_band": 0.2118,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 63,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "f8cf35845ef9",
  "generation": 19,
  "origin": "mutant",
  "parents": [
    "0e4671daeb34"
  ]
}
```

</details>

### `a956465c671a` — commodity_meanrev_daily

```
bollinger(k=3.00,n=49)x0.32 + rsi_rev(n=23)x1.53 -> thr 0.08/0.05 both proportional lev<=2.9  [hold<=41]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 19 via mutant from 4263f8e4524b
- **search-burden headroom: 20,407** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 371. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.000 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.000 | alphaSR +0.25 (need +0.25), 10386 trades, 100% instances positive |
| PASS | G2-replication | +0.137 | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -29.0% / worst -50.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.021 | late-half alphaSR +0.39, final-quarter +0.27 (both need +0.25) vs early half +0.49, retained 79% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.264 | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.253 | 2x costs +0.40 (need +0.15), 3x +0.35 (need +0.00), +1 bar delay +0.43 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.47 vs null +0.02+-0.06 (p99 +0.18) -> z=6.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 371 confirmation tests (would still pass up to 20,407); Bonferroni p 8.11e-10 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.986 vs SR 0.39, p 2.09e-08 |
| PASS | G7-stress-pool | +0.147 | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +3.6%, median DD -33.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.41 | +3.6% | 9.9% | -33.3% | 0.06 | 71 | 0.61% | 0.21 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.16, `eq_index_daily` +0.04, `eq_smallcap_daily` +0.04, `rates_daily` +0.04, `fx_em_daily` -0.02

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 3.0,
        "n": 49
      },
      "weight": 0.3212,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 23
      },
      "weight": 1.5278,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.08,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.147,
  "max_leverage": 2.869,
  "rebalance_band": 0.4108,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 41,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "a956465c671a",
  "generation": 19,
  "origin": "mutant",
  "parents": [
    "4263f8e4524b"
  ]
}
```

</details>

## Portfolio

```
4 distinct strategies across 1 market(s) / 1 asset class(es)   [from 13 proven genomes]
  best single bot        alphaSR +0.43
  portfolio             alphaSR +0.68
  NOTE: every leg trades the SAME market family, so the two correlation scenarios
        coincide and the blend buys no diversification at all — it is one bet,
        sized twice. Correlation between the legs is measured, not assumed.
    25.8%  aae521bbfb56  commodity_meanrev_daily  alphaSR +0.39
    26.8%  696e318c1767  commodity_meanrev_daily  alphaSR +0.40
    23.0%  2f6e9a69b3d1  commodity_meanrev_daily  alphaSR +0.43
    24.4%  a956465c671a  commodity_meanrev_daily  alphaSR +0.41
```

There is only one number because there is only one market family, so the correlation assumption never bites. Correlation *between* these legs is measured directly (they share instances), and the blend's small improvement over the best single bot is what two imperfectly correlated expressions of the same effect buy you — not diversification.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `b0ea14be4154` | commodity_meanrev_daily | +0.55 | +0.57 | 78206 | `rsi_rev(n=23)x1.66 -> thr 0.09/0.05 both proportional lev<=2.9` |
| `789b17775bb2` | commodity_meanrev_daily | +0.55 | +0.57 | 78206 | `rsi_rev(n=23)x1.66 -> thr 0.09/0.05 both proportional lev<=2.6` |
| `eb05ba6ccb66` | commodity_meanrev_daily | +0.54 | +0.63 | 78549 | `rsi_rev(n=14)x1.50 + rsi_rev(n=24)x1.66 + rsi_rev(n=40)x1.53 -> th` |
| `947a3162fd43` | commodity_meanrev_daily | +0.54 | +0.65 | 138044 | `rsi_rev(n=14)x1.50 + rsi_rev(n=24)x1.53 + rsi_rev(n=40)x1.53 -> th` |
| `0e4671daeb34` | commodity_meanrev_daily | +0.53 | +0.60 | 90150 | `rsi_rev(n=13)x1.53 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both prop` |
| `f8cf35845ef9` | commodity_meanrev_daily | +0.53 | +0.60 | 90150 | `rsi_rev(n=13)x1.53 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both prop` |
| `a956465c671a` | commodity_meanrev_daily | +0.53 | +0.59 | 48613 | `bollinger(k=3.00,n=49)x0.32 + rsi_rev(n=23)x1.53 -> thr 0.08/0.05 ` |
| `2cc84e6923bf` | commodity_meanrev_daily | +0.53 | +0.61 | 52338 | `rsi_rev(n=24)x1.53 unanimous rsi_rev(n=27)x1.53 -> thr 0.00/0.00 b` |
| `f746193a66b1` | commodity_meanrev_daily | +0.53 | +0.58 | 68894 | `bollinger(k=3.00,n=44)x0.32 -> thr 0.08/0.02 both proportional lev` |
| `e8954e8a6169` | commodity_meanrev_daily | +0.53 | +0.57 | 68778 | `bollinger(k=3.00,n=44)x0.32 -> thr 0.08/0.02 both proportional lev` |
| `fd84578d6f62` | eq_intraday_15m | +0.50 | +0.57 | 113828 | `bollinger(k=3.00,n=120)x0.49 -> thr 0.08/0.02 both proportional le` |
| `a471df162e92` | eq_intraday_15m | +0.50 | +0.57 | 113860 | `bollinger(k=3.00,n=120)x0.49 -> thr 0.08/0.02 both proportional le` |
| `57f64d0c763a` | eq_largecap_daily | +0.48 | +0.50 | 132341 | `bollinger(k=3.00,n=27)x0.40 -> thr 0.25/0.08 both proportional lev` |
| `dbf0eb74a8f2` | eq_largecap_daily | +0.48 | +0.49 | 121806 | `bollinger(k=3.00,n=27)x0.40 -> thr 0.25/0.08 both proportional lev` |
| `609e048c7d1f` | eq_largecap_daily | +0.44 | +0.55 | 58860 | `bollinger(k=2.66,n=40)x0.84 + rsi_rev(n=11)x2.47 -> thr 0.40/0.05 ` |

## Expansions

| generation | new level | trigger | new space |
|---|---|---|---|
| 3 | 2 | 3 generations without a pass | L2: tier=2 genes<=3 filters<=1 pop=240 finalists=16 per_mkt=3 markets=12 |
| 6 | 3 | 3 generations without a pass | L3: tier=2 genes<=3 filters<=2 pop=360 finalists=20 per_mkt=3 markets=12 |
| 9 | 4 | 3 generations without a pass | L4: tier=3 genes<=4 filters<=2 pop=540 finalists=24 per_mkt=3 markets=13 |
| 12 | 5 | 3 generations without a pass | L5: tier=3 genes<=4 filters<=2 pop=810 finalists=28 per_mkt=3 markets=13 |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 160 | 7 | 17 | 16 | 0 | +0.34 | 67s |
| 2 | 1 | 160 | 7 | 12 | 0 | 0 | +0.38 | 50s |
| 3 | 1 | 160 | 7 | 12 | 0 | 0 | +0.43 | 46s |
| 4 | 2 | 240 | 12 | 19 | 6 | 0 | +0.43 | 77s |
| 5 | 2 | 240 | 12 | 16 | 0 | 0 | +0.36 | 72s |
| 6 | 2 | 240 | 12 | 16 | 0 | 0 | +0.39 | 73s |
| 7 | 3 | 360 | 12 | 20 | 0 | 0 | +0.39 | 104s |
| 8 | 3 | 360 | 12 | 19 | 0 | 0 | +0.43 | 104s |
| 9 | 3 | 360 | 12 | 20 | 0 | 0 | +0.49 | 110s |
| 10 | 4 | 540 | 13 | 21 | 0 | 0 | +0.49 | 172s |
| 11 | 4 | 540 | 13 | 24 | 0 | 0 | +0.51 | 174s |
| 12 | 4 | 540 | 13 | 23 | 0 | 0 | +0.50 | 172s |
| 13 | 5 | 810 | 13 | 24 | 0 | 1 | +0.51 | 278s |
| 14 | 5 | 810 | 13 | 23 | 0 | 2 | +0.54 | 253s |
| 15 | 5 | 810 | 13 | 22 | 0 | 2 | +0.55 | 275s |
| 16 | 5 | 810 | 13 | 21 | 0 | 3 | +0.54 | 274s |
| 17 | 5 | 810 | 13 | 20 | 0 | 2 | +0.54 | 303s |
| 18 | 5 | 810 | 13 | 19 | 0 | 1 | +0.55 | 291s |
| 19 | 5 | 810 | 13 | 23 | 0 | 2 | +0.55 | 311s |

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
