# Bot factory: run report

_Generated 2026-08-12 22:32:55 from `hibar.json`._

## Result

**1 distinct strategies passed all eight gates** (4 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes). Read that number together with the two sections below it: what survives this run's *closing* standard of proof rather than the standard in force when each bot was found, and what survives a faster decay rate. Both are more conservative.

10,380 candidates were screened across 20 generations and 4 search-space expansions; 390 reached the gauntlet; 6,788 backtests were run.

**All of them trade one market family: `commodity_meanrev_daily`.** Ten other tradeable families were searched every generation and yielded nothing that survived the ladder. That is the most informative result in this report, and it is the expected one: the catalogue deliberately contains families where the correct answer is *do not trade this* (the strongest planted edges sit behind a 28bp spread, or behind 0.30bp/bar funding). A search that returned winners everywhere would be evidence against itself.

**Every tradeable family's edge decays** — halflife half the series with a 35% floor by default, so the average edge across an instance is 70% of its opening value. A catalogue identical at the last bar and the first flatters everything tested on it.

The certified bots retain **65%-67%** of their first-half alpha in the second half. For scale, a textbook trend bot on a decaying trend market retains 11% — costs are fixed, so a 30% cut in gross edge takes ~90% of net alpha, and strategies running close to their cost floor die first. What survives decay is what had margin over costs to begin with.

None of the 2 families that decay *faster* than the default (`futures_trend_decay_daily`, `eq_largecap_break_daily`) certified anything.

**Search-burden headroom.** These were certified after 390 confirmation tests, and G6's luck bar rises with that count — so the count matters as much as the Sharpe. Headroom is the largest search each bot's evidence could have come out of and still clear G6: **4 of 4 genomes clear a bar ten times harder than the one they actually faced** (headroom 183,366 down to 68,519). Read it before the Sharpe — a bot whose headroom is close to the tests already run would vanish in a more serious hunt.

## Re-judged at the standard this run finished with

G6's luck bar rises with the size of the search — that is what it is for — so a bot certified in an early generation was measured against a smaller search than this run eventually became. Two inputs drift as a run continues: the confirmation-test count, and the variance of the trial-Sharpe distribution the bar is built from. Below, every proven bot is re-judged at the closing values (**390 confirmation tests, trial variance 0.130**). Nothing here can certify a bot that was not already certified; it can only take one away.

**All 4 genomes (1 distinct strategies) still clear the closing bar.** The headline is not an artefact of when in the run each bot happened to be found.

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

Read it as a sentence: **the strategies this lab has found survive a halflife of about 24 simulated years and are gone by 12.** Four to none across one rung that only takes the mean edge from 0.70 to 0.57 — because the whole population of viable strategies sits in a narrow band just above the replication bar, so a 20% edge cut does not thin the field, it empties it. Nothing survives an abrupt break in the first half of its life. Everything above is conditional on where in that range the real world sits, and this repository cannot tell you.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 360 | 93% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 18 | 5% | worked only on the instances it was bred on (instance luck) |
| G2b-durability | 8 | 2% | edge faded across the series (a crowded or arbitraged anomaly) |

## Proven bots

### `0a3b10605a98` — commodity_meanrev_daily

```
rsi_rev(n=14)x1.50 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 15 via crossover from b47fea13e0c4, 696e318c1767
- **search-burden headroom: 183,366** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 269. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.005 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.014 | alphaSR +0.31 (need +0.30), 32454 trades, 100% instances positive |
| PASS | G2-replication | +0.071 | median alphaSR +0.49 (need +0.42), 100% of 20 instances positive (need 70%), median DD -31.0% / worst -51.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.005 | late-half alphaSR +0.38, final-quarter +0.30 (both need +0.30) vs early half +0.56, retained 67% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.260 | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.202 | 2x costs +0.38 (need +0.18), 3x +0.30 (need +0.00), +1 bar delay +0.43 (need +0.12) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.02+-0.07 (p99 +0.17) -> z=7.0, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.27 after 269 confirmation tests (would still pass up to 183,366); Bonferroni p 3.11e-10 (need <=0.05) \| stricter all-trials view (6330 screened): DSR 1.000 vs SR 0.35, p 7.33e-09 |
| PASS | G7-stress-pool | +0.115 | median alphaSR +0.45 (need +0.34), 100% positive (need 65%), CAGR +3.9%, median DD -30.2% |

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

### `e968878d9bc2` — commodity_meanrev_daily

```
rsi_rev(n=13)x1.53 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both proportional lev<=2.9
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 17 via mutant from 1f8c21af8a82
- **search-burden headroom: 138,544** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 311. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.011 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.021 | alphaSR +0.32 (need +0.30), 19719 trades, 88% instances positive |
| PASS | G2-replication | +0.065 | median alphaSR +0.49 (need +0.42), 100% of 20 instances positive (need 70%), median DD -28.2% / worst -54.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.011 | late-half alphaSR +0.38, final-quarter +0.31 (both need +0.30) vs early half +0.57, retained 66% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.255 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.215 | 2x costs +0.40 (need +0.18), 3x +0.32 (need +0.00), +1 bar delay +0.43 (need +0.12) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.02+-0.05 (p99 +0.16) -> z=8.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.28 after 311 confirmation tests (would still pass up to 138,544); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 1.000 vs SR 0.37, p 0.00e+00 |
| PASS | G7-stress-pool | +0.103 | median alphaSR +0.44 (need +0.34), 100% positive (need 65%), CAGR +3.8%, median DD -29.7% |

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
- **search-burden headroom: 99,766** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 331. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.014 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.018 | alphaSR +0.32 (need +0.30), 19700 trades, 88% instances positive |
| PASS | G2-replication | +0.065 | median alphaSR +0.48 (need +0.42), 100% of 20 instances positive (need 70%), median DD -28.4% / worst -53.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.014 | late-half alphaSR +0.37, final-quarter +0.31 (both need +0.30) vs early half +0.57, retained 65% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.251 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.213 | 2x costs +0.39 (need +0.18), 3x +0.32 (need +0.00), +1 bar delay +0.43 (need +0.12) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.01+-0.06 (p99 +0.16) -> z=7.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.29 after 331 confirmation tests (would still pass up to 99,766); Bonferroni p 4.41e-13 (need <=0.05) \| stricter all-trials view (8760 screened): DSR 1.000 vs SR 0.38, p 1.17e-11 |
| PASS | G7-stress-pool | +0.098 | median alphaSR +0.43 (need +0.34), 100% positive (need 65%), CAGR +3.8%, median DD -30.4% |

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
- **search-burden headroom: 68,519** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 350. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.014 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.018 | alphaSR +0.32 (need +0.30), 19700 trades, 88% instances positive |
| PASS | G2-replication | +0.065 | median alphaSR +0.48 (need +0.42), 100% of 20 instances positive (need 70%), median DD -28.4% / worst -53.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.014 | late-half alphaSR +0.37, final-quarter +0.31 (both need +0.30) vs early half +0.57, retained 65% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.251 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.213 | 2x costs +0.39 (need +0.18), 3x +0.32 (need +0.00), +1 bar delay +0.43 (need +0.12) |
| PASS | G5-permutation | +0.002 | real +0.48 vs null +0.02+-0.06 (p99 +0.13) -> z=7.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.29 after 350 confirmation tests (would still pass up to 68,519); Bonferroni p 3.26e-12 (need <=0.05) \| stricter all-trials view (9570 screened): DSR 0.999 vs SR 0.39, p 8.92e-11 |
| PASS | G7-stress-pool | +0.098 | median alphaSR +0.43 (need +0.34), 100% positive (need 65%), CAGR +3.8%, median DD -30.4% |

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

## Portfolio

```
1 distinct strategies across 1 market(s) / 1 asset class(es)   [from 4 proven genomes]
  best single bot        alphaSR +0.44
  portfolio             alphaSR +0.44
  NOTE: every leg trades the SAME market family, so the two correlation scenarios
        coincide and the blend buys no diversification at all — it is one bet,
        sized twice. Correlation between the legs is measured, not assumed.
    100.0%  0a3b10605a98  commodity_meanrev_daily  alphaSR +0.44
```

There is only one number because there is only one market family, so the correlation assumption never bites. Correlation *between* these legs is measured directly (they share instances), and the blend's small improvement over the best single bot is what two imperfectly correlated expressions of the same effect buy you — not diversification.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `9e34e6c7b452` | commodity_meanrev_daily | +0.55 | +0.57 | 78206 | `rsi_rev(n=23)x1.65 -> thr 0.09/0.05 both proportional lev<=2.6` |
| `0c2f8e25c81c` | commodity_meanrev_daily | +0.55 | +0.57 | 78206 | `rsi_rev(n=23)x2.93 -> thr 0.09/0.05 both proportional lev<=2.9` |
| `eb05ba6ccb66` | commodity_meanrev_daily | +0.54 | +0.63 | 78549 | `rsi_rev(n=14)x1.50 + rsi_rev(n=24)x1.66 + rsi_rev(n=40)x1.53 -> th` |
| `56b77c744754` | commodity_meanrev_daily | +0.54 | +0.63 | 78549 | `rsi_rev(n=14)x1.50 + rsi_rev(n=24)x1.66 + rsi_rev(n=40)x1.53 -> th` |
| `0e4671daeb34` | commodity_meanrev_daily | +0.53 | +0.60 | 90150 | `rsi_rev(n=13)x1.53 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both prop` |
| `f8cf35845ef9` | commodity_meanrev_daily | +0.53 | +0.60 | 90150 | `rsi_rev(n=13)x1.53 + rsi_rev(n=24)x1.53 -> thr 0.08/0.05 both prop` |
| `a956465c671a` | commodity_meanrev_daily | +0.53 | +0.59 | 48613 | `bollinger(k=3.00,n=49)x0.32 + rsi_rev(n=23)x1.53 -> thr 0.08/0.05 ` |
| `f4de3d14ec1f` | commodity_meanrev_daily | +0.53 | +0.59 | 48613 | `bollinger(k=3.00,n=49)x0.32 + rsi_rev(n=23)x1.53 -> thr 0.08/0.05 ` |
| `2cc84e6923bf` | commodity_meanrev_daily | +0.53 | +0.61 | 52338 | `rsi_rev(n=24)x1.53 unanimous rsi_rev(n=27)x1.53 -> thr 0.00/0.00 b` |
| `7f18594a39b7` | commodity_meanrev_daily | +0.53 | +0.58 | 68877 | `bollinger(k=3.00,n=44)x0.32 -> thr 0.08/0.02 both proportional lev` |
| `361dc67f6581` | eq_intraday_15m | +0.52 | +0.60 | 114236 | `bollinger(k=2.78,n=120)x0.49 -> thr 0.08/0.02 both proportional le` |
| `fd84578d6f62` | eq_intraday_15m | +0.50 | +0.57 | 113828 | `bollinger(k=3.00,n=120)x0.49 -> thr 0.08/0.02 both proportional le` |
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
| 1 | 1 | 160 | 7 | 17 | 16 | 0 | +0.34 | 65s |
| 2 | 1 | 160 | 7 | 12 | 0 | 0 | +0.38 | 55s |
| 3 | 1 | 160 | 7 | 12 | 0 | 0 | +0.43 | 55s |
| 4 | 2 | 240 | 12 | 19 | 6 | 0 | +0.43 | 92s |
| 5 | 2 | 240 | 12 | 16 | 0 | 0 | +0.36 | 90s |
| 6 | 2 | 240 | 12 | 16 | 0 | 0 | +0.39 | 91s |
| 7 | 3 | 360 | 12 | 20 | 0 | 0 | +0.39 | 132s |
| 8 | 3 | 360 | 12 | 19 | 0 | 0 | +0.43 | 126s |
| 9 | 3 | 360 | 12 | 20 | 0 | 0 | +0.49 | 126s |
| 10 | 4 | 540 | 13 | 21 | 0 | 0 | +0.49 | 211s |
| 11 | 4 | 540 | 13 | 24 | 0 | 0 | +0.51 | 208s |
| 12 | 4 | 540 | 13 | 23 | 0 | 0 | +0.50 | 206s |
| 13 | 5 | 810 | 13 | 24 | 0 | 0 | +0.51 | 307s |
| 14 | 5 | 810 | 13 | 23 | 0 | 0 | +0.54 | 315s |
| 15 | 5 | 810 | 13 | 22 | 0 | 1 | +0.55 | 316s |
| 16 | 5 | 810 | 13 | 21 | 0 | 0 | +0.54 | 333s |
| 17 | 5 | 810 | 13 | 20 | 0 | 1 | +0.54 | 344s |
| 18 | 5 | 810 | 13 | 19 | 0 | 1 | +0.55 | 351s |
| 19 | 5 | 810 | 13 | 23 | 0 | 1 | +0.55 | 349s |
| 20 | 5 | 810 | 13 | 19 | 0 | 0 | +0.55 | 350s |

## Standard of proof used

```json
{
  "min_oos_alpha_sr": 0.3,
  "min_repl_alpha_sr": 0.42,
  "min_repl_pos_frac": 0.7,
  "min_late_alpha_sr": 0.3,
  "min_edge_retention": 0.5,
  "min_stress_alpha_sr": 0.336,
  "min_stress_pos_frac": 0.65,
  "max_drawdown": 0.35,
  "min_trades": 30,
  "max_control_alpha_sr": 0.3,
  "cost_stress_2x_min": 0.18,
  "cost_stress_3x_min": 0.0,
  "delay_stress_min": 0.12,
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
