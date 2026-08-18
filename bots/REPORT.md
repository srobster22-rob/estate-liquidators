# Bot factory: run report

_Generated 2026-08-18 11:18:33 from `run_state.json`._

## Result

**1 distinct strategies passed all eight gates** (8 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes). Read that number together with the two sections below it: what survives this run's *closing* standard of proof rather than the standard in force when each bot was found, and what survives a faster decay rate. Both are more conservative.

7,950 candidates were screened across 22 generations and 4 search-space expansions; 404 reached the gauntlet; 11,668 backtests were run.

**All of them trade one market family: `commodity_meanrev_daily`.** Ten other tradeable families were searched every generation and yielded nothing that survived the ladder. That is the most informative result in this report, and it is the expected one: the catalogue deliberately contains families where the correct answer is *do not trade this* (the strongest planted edges sit behind a 28bp spread, or behind 0.30bp/bar funding). A search that returned winners everywhere would be evidence against itself.

**Every tradeable family's edge decays** — halflife half the series with a 35% floor by default, so the average edge across an instance is 70% of its opening value. A catalogue identical at the last bar and the first flatters everything tested on it.

The certified bots retain **64%-80%** of their first-half alpha in the second half. For scale, a textbook trend bot on a decaying trend market retains 11% — costs are fixed, so a 30% cut in gross edge takes ~90% of net alpha, and strategies running close to their cost floor die first. What survives decay is what had margin over costs to begin with.

None of the 2 families that decay *faster* than the default (`futures_trend_decay_daily`, `eq_largecap_break_daily`) certified anything.

**Search-burden headroom.** These were certified after 404 confirmation tests, and G6's luck bar rises with that count — so the count matters as much as the Sharpe. Headroom is the largest search each bot's evidence could have come out of and still clear G6: **6 of 8 genomes clear a bar ten times harder than the one they actually faced** (headroom 16,747 down to 1,394). Read it before the Sharpe — a bot whose headroom is close to the tests already run would vanish in a more serious hunt.

## Re-judged at the standard this run finished with

G6's luck bar rises with the size of the search — that is what it is for — so a bot certified in an early generation was measured against a smaller search than this run eventually became. Two inputs drift as a run continues: the confirmation-test count, and the variance of the trial-Sharpe distribution the bar is built from. Below, every proven bot is re-judged at the closing values (**404 confirmation tests, trial variance 0.126**). Nothing here can certify a bot that was not already certified; it can only take one away.

**All 8 genomes (1 distinct strategies) still clear the closing bar.** The headline is not an artefact of when in the run each bot happened to be found.

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
| G1-oos | 289 | 73% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 78 | 20% | worked only on the instances it was bred on (instance luck) |
| G2b-durability | 29 | 7% | edge faded across the series (a crowded or arbitraged anomaly) |

## Proven bots

### `89aa33cc3f9d` — commodity_meanrev_daily

```
rsi_rev(n=14)x0.80 + rsi_rev(n=24)x1.18 -> thr 0.29/0.08 both proportional lev<=2.0  [tp 5.3atr, hold<=20]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 8 via mutant from 7b7fd2db6f64
- **search-burden headroom: 1,394** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 404. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.023 alpha Sharpe at G2-replication** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.027 | alphaSR +0.28 (need +0.25), 7293 trades, 88% instances positive |
| PASS | G2-replication | +0.023 | median alphaSR +0.37 (need +0.35), 100% of 20 instances positive (need 70%), median DD -28.4% / worst -51.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.043 | late-half alphaSR +0.36, final-quarter +0.29 (both need +0.25) vs early half +0.45, retained 80% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.255 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.04] |
| PASS | G4-stress | +0.151 | 2x costs +0.30 (need +0.15), 3x +0.25 (need +0.00), +1 bar delay +0.32 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.37 vs null -0.01+-0.07 (p99 +0.17) -> z=5.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.047 | DSR 0.997 (need 0.95) vs luck bar SR 0.30 after 404 confirmation tests (would still pass up to 1,394); Bonferroni p 6.46e-05 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 0.603 vs SR 0.38, p 1.27e-03 |
| PASS | G7-stress-pool | +0.068 | median alphaSR +0.35 (need +0.28), 100% positive (need 65%), CAGR +2.6%, median DD -30.5% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.35 | +0.35 | +2.6% | 8.2% | -30.5% | 0.05 | 49 | 0.44% | 0.13 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.38, `eq_largecap_break_daily` +0.16, `eq_index_daily` +0.06, `rates_daily` +0.05, `eq_smallcap_daily` +0.04, `fx_em_daily` -0.03

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
      "weight": 0.8,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.1781,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.291,
  "exit_threshold": 0.08,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": 5.33,
  "trail_atr": null,
  "max_hold": 20,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "89aa33cc3f9d",
  "generation": 8,
  "origin": "mutant",
  "parents": [
    "7b7fd2db6f64"
  ]
}
```

</details>

### `4315dedca71d` — commodity_meanrev_daily

```
rsi_rev(n=11)x0.84 + rsi_rev(n=24)x1.18 -> thr 0.29/0.05 both proportional lev<=2.0  [hold<=31]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 9 via mutant from a8f9a956e0a5
- **search-burden headroom: 11,379** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 404. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.069 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.069 | alphaSR +0.32 (need +0.25), 10295 trades, 100% instances positive |
| PASS | G2-replication | +0.073 | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -29.6% / worst -53.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.072 | late-half alphaSR +0.37, final-quarter +0.32 (both need +0.25) vs early half +0.51, retained 72% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.239 | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.198 | 2x costs +0.35 (need +0.15), 3x +0.29 (need +0.00), +1 bar delay +0.37 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.42 vs null -0.00+-0.07 (p99 +0.15) -> z=6.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 404 confirmation tests (would still pass up to 11,379); Bonferroni p 9.76e-08 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 0.972 vs SR 0.38, p 1.92e-06 |
| PASS | G7-stress-pool | +0.124 | median alphaSR +0.40 (need +0.28), 100% positive (need 65%), CAGR +3.3%, median DD -28.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.40 | +0.40 | +3.3% | 9.2% | -28.0% | 0.06 | 68 | 0.61% | 0.16 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.38, `eq_largecap_break_daily` +0.15, `eq_smallcap_daily` +0.02, `rates_daily` +0.01, `eq_index_daily` +0.00, `fx_em_daily` -0.06

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
      "weight": 0.8361,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.1781,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.291,
  "exit_threshold": 0.05,
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
  "max_hold": 31,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "4315dedca71d",
  "generation": 9,
  "origin": "mutant",
  "parents": [
    "a8f9a956e0a5"
  ]
}
```

</details>

### `68f03aa1f441` — commodity_meanrev_daily

```
rsi_rev(n=11)x0.84 + rsi_rev(n=30)x1.18 -> thr 0.29/0.05 both proportional lev<=2.0  [hold<=31]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 10 via mutant from 4315dedca71d
- **search-burden headroom: 16,747** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 404. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.004 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.004 | alphaSR +0.25 (need +0.25), 9271 trades, 88% instances positive |
| PASS | G2-replication | +0.142 | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -25.2% / worst -50.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.087 | late-half alphaSR +0.38, final-quarter +0.34 (both need +0.25) vs early half +0.54, retained 70% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.260 | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.02] |
| PASS | G4-stress | +0.235 | 2x costs +0.39 (need +0.15), 3x +0.33 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.46 vs null +0.00+-0.07 (p99 +0.16) -> z=7.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 404 confirmation tests (would still pass up to 16,747); Bonferroni p 2.64e-10 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 0.986 vs SR 0.38, p 5.20e-09 |
| PASS | G7-stress-pool | +0.135 | median alphaSR +0.42 (need +0.28), 100% positive (need 65%), CAGR +3.1%, median DD -28.6% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.42 | +0.40 | +3.1% | 8.4% | -28.6% | 0.06 | 62 | 0.52% | 0.14 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.14, `rates_daily` +0.02, `eq_smallcap_daily` +0.01, `eq_index_daily` +0.01, `fx_em_daily` -0.06

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
      "weight": 0.8361,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 30
      },
      "weight": 1.1781,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.291,
  "exit_threshold": 0.05,
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
  "max_hold": 31,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "68f03aa1f441",
  "generation": 10,
  "origin": "mutant",
  "parents": [
    "4315dedca71d"
  ]
}
```

</details>

### `1a58db684982` — commodity_meanrev_daily

```
rsi_rev(n=13)x0.84 + rsi_rev(n=24)x1.18 -> thr 0.29/0.05 both proportional lev<=2.0  [hold<=31]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 11 via mutant from 4315dedca71d
- **search-burden headroom: 9,947** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 404. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.039 alpha Sharpe at G2b-durability** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.064 | alphaSR +0.31 (need +0.25), 9401 trades, 100% instances positive |
| PASS | G2-replication | +0.089 | median alphaSR +0.44 (need +0.35), 100% of 20 instances positive (need 70%), median DD -29.6% / worst -49.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.039 | late-half alphaSR +0.38, final-quarter +0.29 (both need +0.25) vs early half +0.55, retained 69% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.239 | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.201 | 2x costs +0.35 (need +0.15), 3x +0.30 (need +0.00), +1 bar delay +0.37 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.40 vs null +0.00+-0.07 (p99 +0.18) -> z=5.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 404 confirmation tests (would still pass up to 9,947); Bonferroni p 6.93e-07 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 0.965 vs SR 0.38, p 1.36e-05 |
| PASS | G7-stress-pool | +0.125 | median alphaSR +0.41 (need +0.28), 100% positive (need 65%), CAGR +3.2%, median DD -29.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.41 | +0.40 | +3.2% | 8.9% | -29.0% | 0.05 | 62 | 0.52% | 0.15 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.39, `eq_largecap_break_daily` +0.16, `eq_smallcap_daily` +0.06, `rates_daily` +0.04, `eq_index_daily` +0.02, `fx_em_daily` -0.03

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
      "weight": 0.8361,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.1781,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.291,
  "exit_threshold": 0.05,
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
  "max_hold": 31,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "1a58db684982",
  "generation": 11,
  "origin": "mutant",
  "parents": [
    "4315dedca71d"
  ]
}
```

</details>

### `c0e2a138c0d5` — commodity_meanrev_daily

```
rsi_rev(n=11)x0.84 + rsi_rev(n=24)x1.18 -> thr 0.29/0.05 both proportional lev<=2.0  [hold<=31]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 12 via mutant from 4315dedca71d
- **search-burden headroom: 11,379** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 404. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.069 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.069 | alphaSR +0.32 (need +0.25), 10295 trades, 100% instances positive |
| PASS | G2-replication | +0.073 | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -29.6% / worst -53.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.072 | late-half alphaSR +0.37, final-quarter +0.32 (both need +0.25) vs early half +0.51, retained 72% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.239 | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.01] |
| PASS | G4-stress | +0.198 | 2x costs +0.35 (need +0.15), 3x +0.29 (need +0.00), +1 bar delay +0.37 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.42 vs null -0.00+-0.07 (p99 +0.15) -> z=6.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 404 confirmation tests (would still pass up to 11,379); Bonferroni p 9.76e-08 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 0.972 vs SR 0.38, p 1.92e-06 |
| PASS | G7-stress-pool | +0.124 | median alphaSR +0.40 (need +0.28), 100% positive (need 65%), CAGR +3.3%, median DD -28.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.40 | +0.40 | +3.3% | 9.2% | -28.0% | 0.06 | 68 | 0.61% | 0.16 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.38, `eq_largecap_break_daily` +0.15, `eq_smallcap_daily` +0.02, `rates_daily` +0.01, `eq_index_daily` +0.00, `fx_em_daily` -0.06

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
      "weight": 0.8361,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.1781,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.291,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.1526,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 31,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "c0e2a138c0d5",
  "generation": 12,
  "origin": "mutant",
  "parents": [
    "4315dedca71d"
  ]
}
```

</details>

### `c0611cfe3b5b` — commodity_meanrev_daily

```
rsi_rev(n=13)x0.84 + rsi_rev(n=24)x1.18 -> thr 0.37/0.05 both proportional lev<=2.0  [hold<=31]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 13 via mutant from 1a58db684982
- **search-burden headroom: 2,983** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 404. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.007 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.007 | alphaSR +0.26 (need +0.25), 6740 trades, 75% instances positive |
| PASS | G2-replication | +0.071 | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.1% / worst -51.1% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.023 | late-half alphaSR +0.36, final-quarter +0.27 (both need +0.25) vs early half +0.47, retained 75% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.257 | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.00] |
| PASS | G4-stress | +0.194 | 2x costs +0.34 (need +0.15), 3x +0.30 (need +0.00), +1 bar delay +0.33 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.41 vs null +0.00+-0.07 (p99 +0.15) -> z=6.0, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 404 confirmation tests (would still pass up to 2,983); Bonferroni p 4.89e-07 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 0.811 vs SR 0.38, p 9.62e-06 |
| PASS | G7-stress-pool | +0.110 | median alphaSR +0.39 (need +0.28), 100% positive (need 65%), CAGR +2.8%, median DD -27.6% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.39 | +0.38 | +2.8% | 8.4% | -27.6% | 0.05 | 44 | 0.40% | 0.12 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.41, `eq_largecap_break_daily` +0.12, `eq_intraday_15m` +0.06, `eq_smallcap_daily` +0.05, `rates_daily` +0.02, `eq_index_daily` +0.00

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
      "weight": 0.8361,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.1781,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.3684,
  "exit_threshold": 0.05,
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
  "max_hold": 31,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "c0611cfe3b5b",
  "generation": 13,
  "origin": "mutant",
  "parents": [
    "1a58db684982"
  ]
}
```

</details>

### `4a3eff82bfa2` — commodity_meanrev_daily

```
rsi_rev(n=15)x0.84 + rsi_rev(n=24)x1.18 -> thr 0.29/0.05 both proportional lev<=2.0  [hold<=31]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 14 via mutant from 4315dedca71d
- **search-burden headroom: 6,114** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 404. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.043 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.043 | alphaSR +0.29 (need +0.25), 8534 trades, 88% instances positive |
| PASS | G2-replication | +0.058 | median alphaSR +0.41 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.0% / worst -50.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.066 | late-half alphaSR +0.33, final-quarter +0.32 (both need +0.25) vs early half +0.52, retained 64% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.254 | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.04] |
| PASS | G4-stress | +0.199 | 2x costs +0.35 (need +0.15), 3x +0.30 (need +0.00), +1 bar delay +0.37 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.39 vs null +0.00+-0.07 (p99 +0.17) -> z=5.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 404 confirmation tests (would still pass up to 6,114); Bonferroni p 1.03e-06 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 0.926 vs SR 0.38, p 2.02e-05 |
| PASS | G7-stress-pool | +0.131 | median alphaSR +0.41 (need +0.28), 100% positive (need 65%), CAGR +3.1%, median DD -28.6% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.41 | +0.40 | +3.1% | 8.7% | -28.6% | 0.05 | 57 | 0.45% | 0.14 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.40, `eq_largecap_break_daily` +0.17, `eq_smallcap_daily` +0.06, `rates_daily` +0.05, `eq_index_daily` +0.02, `fx_major_daily` -0.03

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 15
      },
      "weight": 0.8361,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.1781,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.291,
  "exit_threshold": 0.05,
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
  "max_hold": 31,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "4a3eff82bfa2",
  "generation": 14,
  "origin": "mutant",
  "parents": [
    "4315dedca71d"
  ]
}
```

</details>

### `23854b5224d5` — commodity_meanrev_daily

```
rsi_rev(n=13)x0.84 + rsi_rev(n=24)x1.18 -> thr 0.25/0.05 both proportional lev<=2.0  [tp 3.8atr, hold<=31]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 15 via mutant from 1a58db684982
- **search-burden headroom: 11,627** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 404. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.
- **tightest gate margin: +0.040 alpha Sharpe at G1-oos** — how much room the binding statistic had. A certification that clears its narrowest gate by a hundredth is a different piece of evidence from one that clears it by two tenths, and the verdict alone does not say which this is.

|  | gate | margin | evidence |
|---|---|---|---|
| PASS | G1-oos | +0.040 | alphaSR +0.29 (need +0.25), 10927 trades, 100% instances positive |
| PASS | G2-replication | +0.089 | median alphaSR +0.44 (need +0.35), 100% of 20 instances positive (need 70%), median DD -28.2% / worst -51.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | +0.099 | late-half alphaSR +0.36, final-quarter +0.35 (both need +0.25) vs early half +0.51, retained 71% (ratio not gated: this market decays by design) |
| PASS | G3-controls | +0.245 | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.02] |
| PASS | G4-stress | +0.201 | 2x costs +0.35 (need +0.15), 3x +0.29 (need +0.00), +1 bar delay +0.36 (need +0.10) |
| PASS | G5-permutation | +0.002 | real +0.40 vs null -0.01+-0.07 (p99 +0.15) -> z=6.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | +0.050 | DSR 1.000 (need 0.95) vs luck bar SR 0.30 after 404 confirmation tests (would still pass up to 11,627); Bonferroni p 1.70e-07 (need <=0.05) \| stricter all-trials view (7950 screened): DSR 0.973 vs SR 0.38, p 3.34e-06 |
| PASS | G7-stress-pool | +0.139 | median alphaSR +0.42 (need +0.28), 100% positive (need 65%), CAGR +3.3%, median DD -29.8% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.42 | +0.40 | +3.3% | 9.0% | -29.8% | 0.06 | 73 | 0.57% | 0.16 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.38, `eq_largecap_break_daily` +0.17, `rates_daily` +0.03, `eq_index_daily` +0.03, `eq_smallcap_daily` +0.01, `fx_em_daily` -0.08

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
      "weight": 0.8361,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.1781,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2453,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": 3.81,
  "trail_atr": null,
  "max_hold": 31,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "23854b5224d5",
  "generation": 15,
  "origin": "mutant",
  "parents": [
    "1a58db684982"
  ]
}
```

</details>

## Portfolio

```
1 distinct strategies across 1 market(s) / 1 asset class(es)   [from 8 proven genomes]
  best single bot        alphaSR +0.36
  portfolio             alphaSR +0.36
  NOTE: every leg trades the SAME market family, so the two correlation scenarios
        coincide and the blend buys no diversification at all — it is one bet,
        sized twice. Correlation between the legs is measured, not assumed.
    100.0%  89aa33cc3f9d  commodity_meanrev_daily  alphaSR +0.36
```

There is only one number because there is only one market family, so the correlation assumption never bites. Correlation *between* these legs is measured directly (they share instances), and the blend's small improvement over the best single bot is what two imperfectly correlated expressions of the same effect buy you — not diversification.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `d8aa6b0645b7` | eq_intraday_15m | +0.54 | +0.71 | 101972 | `-ma_cross(fast=45,slow=33)x0.95 + -macd(fast=9,sig=12,slow=118)x0.` |
| `e08a11ad3e7d` | commodity_meanrev_daily | +0.53 | +0.58 | 68305 | `rsi_rev(n=11)x0.84 + rsi_rev(n=24)x1.18 -> thr 0.20/0.05 both prop` |
| `5504e6342add` | commodity_meanrev_daily | +0.53 | +0.58 | 68305 | `rsi_rev(n=11)x0.84 + rsi_rev(n=24)x1.18 -> thr 0.20/0.05 both prop` |
| `64ae5db3d2b9` | eq_intraday_15m | +0.51 | +0.62 | 79525 | `-ma_cross(fast=51,slow=48)x0.93 -> thr 0.06/0.04 both proportional` |
| `6617c35870c2` | eq_intraday_15m | +0.51 | +0.62 | 79525 | `-ma_cross(fast=58,slow=48)x0.93 -> thr 0.06/0.04 both proportional` |
| `f609acff6a56` | eq_intraday_15m | +0.51 | +0.63 | 54701 | `-ma_cross(fast=51,slow=51)x1.00 \| trend_strength(nf=8,ns=85,thr=0.` |
| `8dce3d0d3416` | eq_intraday_15m | +0.51 | +0.63 | 54701 | `-ma_cross(fast=51,slow=51)x1.00 \| trend_strength(nf=8,ns=85,thr=0.` |
| `726ebb9930f8` | eq_intraday_15m | +0.51 | +0.70 | 99201 | `-ma_cross(fast=45,slow=33)x0.95 + -macd(fast=9,sig=17,slow=120)x0.` |
| `bf23db8814c0` | commodity_meanrev_daily | +0.49 | +0.52 | 36382 | `rsi_rev(n=16)x1.00 -> thr 0.39/0.05 both proportional lev<=1.2  [h` |
| `cd271e6de6e7` | commodity_meanrev_daily | +0.49 | +0.53 | 37346 | `rsi_rev(n=16)x1.00 -> thr 0.39/0.05 both proportional lev<=2.0  [h` |
| `ef1cafc8e77d` | commodity_meanrev_daily | +0.49 | +0.58 | 35898 | `rsi_rev(n=21)x1.18 unanimous rsi_rev(n=25)x0.84 -> thr 0.22/0.05 b` |
| `fda2b9b065f3` | commodity_meanrev_daily | +0.49 | +0.58 | 35898 | `rsi_rev(n=21)x1.67 unanimous rsi_rev(n=25)x0.84 -> thr 0.22/0.05 b` |
| `597c62812608` | commodity_meanrev_daily | +0.49 | +0.58 | 29008 | `rsi_rev(n=14)x0.80 + rsi_rev(n=28)x0.84 + rsi_rev(n=31)x1.23 -> th` |
| `7ec9807c66d4` | commodity_meanrev_daily | +0.49 | +0.58 | 29008 | `rsi_rev(n=14)x0.80 + rsi_rev(n=28)x0.84 + rsi_rev(n=31)x1.23 -> th` |
| `6d6b2e093d0c` | eq_intraday_15m | +0.48 | +0.65 | 82036 | `-ma_cross(fast=51,slow=43)x3.00 + -ma_cross(fast=51,slow=51)x1.00 ` |

## Expansions

| generation | new level | trigger | new space |
|---|---|---|---|
| 3 | 2 | 3 generations without a pass | L2: tier=2 genes<=3 filters<=1 pop=240 finalists=16 per_mkt=3 markets=12 |
| 6 | 3 | 3 generations without a pass | L3: tier=2 genes<=3 filters<=2 pop=360 finalists=20 per_mkt=3 markets=12 |
| 18 | 4 | 3 generations without a pass | L4: tier=3 genes<=4 filters<=2 pop=540 finalists=24 per_mkt=3 markets=13 |
| 21 | 5 | 3 generations without a pass | L5: tier=3 genes<=4 filters<=2 pop=810 finalists=28 per_mkt=3 markets=13 |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 160 | 7 | 17 | 15 | 0 | +0.31 | 31s |
| 2 | 1 | 160 | 7 | 12 | 0 | 0 | +0.36 | 26s |
| 3 | 1 | 160 | 7 | 12 | 0 | 0 | +0.39 | 27s |
| 4 | 2 | 240 | 12 | 19 | 6 | 0 | +0.37 | 42s |
| 5 | 2 | 240 | 12 | 16 | 0 | 0 | +0.37 | 43s |
| 6 | 2 | 240 | 12 | 16 | 0 | 0 | +0.40 | 39s |
| 7 | 3 | 360 | 12 | 20 | 0 | 0 | +0.40 | 53s |
| 8 | 3 | 360 | 12 | 18 | 0 | 1 | +0.44 | 56s |
| 9 | 3 | 360 | 12 | 20 | 0 | 1 | +0.49 | 57s |
| 10 | 3 | 360 | 12 | 20 | 0 | 1 | +0.48 | 54s |
| 11 | 3 | 360 | 12 | 18 | 0 | 1 | +0.49 | 54s |
| 12 | 3 | 360 | 12 | 20 | 0 | 1 | +0.49 | 58s |
| 13 | 3 | 360 | 12 | 19 | 0 | 1 | +0.49 | 54s |
| 14 | 3 | 360 | 12 | 20 | 0 | 1 | +0.48 | 60s |
| 15 | 3 | 360 | 12 | 20 | 0 | 1 | +0.47 | 65s |
| 16 | 3 | 360 | 12 | 19 | 0 | 0 | +0.51 | 61s |
| 17 | 3 | 360 | 12 | 20 | 0 | 0 | +0.51 | 61s |
| 18 | 3 | 360 | 12 | 19 | 0 | 0 | +0.53 | 62s |
| 19 | 4 | 540 | 13 | 19 | 0 | 0 | +0.51 | 117s |
| 20 | 4 | 540 | 13 | 19 | 0 | 0 | +0.53 | 115s |
| 21 | 4 | 540 | 13 | 20 | 0 | 0 | +0.52 | 114s |
| 22 | 5 | 810 | 13 | 21 | 0 | 0 | +0.54 | 168s |

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
