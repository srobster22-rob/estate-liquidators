# Bot factory: run report

_Generated 2026-07-30 11:47:51 from `run_state.json`._

## Result

**2 distinct strategies passed all seven gates** (6 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes).

12,260 candidates were screened across 25 generations and 5 search-space expansions; 450 reached the gauntlet; 35,165 backtests were run.

**All of them trade one market family: `commodity_meanrev_daily`.** Ten other tradeable families were searched every generation and yielded nothing that survived the ladder. That is the most informative result in this report, and it is the expected one: the catalogue deliberately contains families where the correct answer is *do not trade this* (the strongest planted edges sit behind a 28bp spread, or behind 0.30bp/bar funding). A search that returned winners everywhere would be evidence against itself.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 193 | 43% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 192 | 43% | worked only on the instances it was bred on (instance luck) |
| G3-controls | 1 | 0% | showed profit on a random walk (artifact or harness bug) |
| G4-stress | 27 | 6% | edge smaller than 2x costs or one bar of delay |
| G5-permutation | 21 | 5% | no better than its own block-bootstrapped null |
| G6-multiplicity | 9 | 2% | not surprising given how many candidates were tried |
| G7-stress-pool | 1 | 0% | failed to replicate a second time on a third pool |

## Proven bots

### `a60935fe32e2` — commodity_meanrev_daily

```
rsi_rev(n=14)x1.00 -> thr 0.40/0.05 both voltarget@15%v lev<=2.0  [hold<=15]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 1.23)
- found in generation 4 via archetype

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.55 (need +0.25), 880 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.51 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.5% / worst -44.3% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.13 (allowed 0.30) [control_efficient_daily=-0.13, control_martingale_daily=+0.00] |
| PASS | G4-stress | 2x costs +0.40 (need +0.15), 3x +0.34 (need +0.00), +1 bar delay +0.38 (need +0.10) |
| PASS | G5-permutation | real +0.57 vs null +0.03+-0.13 (p99 +0.27) -> z=4.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.23 after 42 confirmation tests; Bonferroni p 3.96e-04 (need <=0.05) \| stricter all-trials view (1080 screened): DSR 0.994 vs SR 0.35, p 1.02e-02 |
| PASS | G7-stress-pool | median alphaSR +0.41 (need +0.28), 95% positive (need 65%), CAGR +3.7%, median DD -27.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.41 | +0.37 | +3.7% | 11.4% | -27.4% | 0.07 | 24 | 0.71% | 0.22 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.26, `eq_smallcap_daily` -0.14, `rates_daily` -0.16, `fx_major_daily` -0.20, `futures_trend_daily` -0.22, `eq_intraday_15m` -0.25

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
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.4,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 15,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "a60935fe32e2",
  "generation": 4,
  "origin": "archetype",
  "parents": []
}
```

</details>

### `7267d7623bad` — commodity_meanrev_daily

```
-breakout(n=20)x1.00 -> thr 0.50/0.10 both voltarget@15%v lev<=2.0  [hold<=20]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 1.23)
- found in generation 4 via transplant from 948431b929cf

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.65 (need +0.25), 1489 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -31.5% / worst -49.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.13 (allowed 0.30) [control_efficient_daily=-0.13, control_martingale_daily=+0.05] |
| PASS | G4-stress | 2x costs +0.40 (need +0.15), 3x +0.31 (need +0.00), +1 bar delay +0.44 (need +0.10) |
| PASS | G5-permutation | real +0.53 vs null +0.05+-0.12 (p99 +0.29) -> z=4.0, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 0.998 (need 0.95) vs luck bar SR 0.24 after 48 confirmation tests; Bonferroni p 1.56e-03 (need <=0.05) \| stricter all-trials view (1080 screened): DSR 0.911 vs SR 0.35, p 3.51e-02 |
| PASS | G7-stress-pool | median alphaSR +0.38 (need +0.28), 100% positive (need 65%), CAGR +5.0%, median DD -31.7% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.38 | +0.41 | +5.0% | 14.5% | -31.7% | 0.09 | 40 | 1.30% | 0.36 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `rates_daily` -0.07, `futures_trend_daily` -0.14, `eq_smallcap_daily` -0.20, `fx_major_daily` -0.27, `fx_em_daily` -0.37

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 20
      },
      "weight": 1.0,
      "mode": -1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.5,
  "exit_threshold": 0.1,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 20,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "7267d7623bad",
  "generation": 4,
  "origin": "transplant",
  "parents": [
    "948431b929cf"
  ]
}
```

</details>

### `9a6f1aa7f76e` — commodity_meanrev_daily

```
rsi_rev(n=14)x1.82 -> thr 0.34/0.05 both voltarget@15%v lev<=2.0  [hold<=15]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 1.23)
- found in generation 5 via mutant from a60935fe32e2

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.45 (need +0.25), 1040 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.48 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.3% / worst -44.0% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.10 (allowed 0.30) [control_efficient_daily=-0.10, control_martingale_daily=-0.03] |
| PASS | G4-stress | 2x costs +0.46 (need +0.15), 3x +0.39 (need +0.00), +1 bar delay +0.45 (need +0.10) |
| PASS | G5-permutation | real +0.65 vs null +0.01+-0.12 (p99 +0.27) -> z=5.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.26 after 61 confirmation tests; Bonferroni p 1.16e-05 (need <=0.05) \| stricter all-trials view (1440 screened): DSR 0.954 vs SR 0.38, p 2.73e-04 |
| PASS | G7-stress-pool | median alphaSR +0.42 (need +0.28), 95% positive (need 65%), CAGR +4.1%, median DD -27.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.42 | +0.39 | +4.1% | 12.2% | -27.1% | 0.07 | 28 | 0.85% | 0.25 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.28, `eq_smallcap_daily` -0.12, `rates_daily` -0.17, `futures_trend_daily` -0.19, `fx_major_daily` -0.31, `eq_intraday_15m` -0.32

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
      "weight": 1.8188,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.3448,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 15,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "9a6f1aa7f76e",
  "generation": 5,
  "origin": "mutant",
  "parents": [
    "a60935fe32e2"
  ]
}
```

</details>

### `381b0a6f12da` — commodity_meanrev_daily

```
-breakout(n=20)x1.00 -> thr 0.50/0.10 both voltarget@15%v lev<=2.0  [hold<=20]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 1.23)
- found in generation 5 via mutant from 7267d7623bad

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.65 (need +0.25), 1751 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.42 (need +0.35), 95% of 20 instances positive (need 70%), median DD -31.3% / worst -48.3% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.12 (allowed 0.30) [control_efficient_daily=-0.12, control_martingale_daily=+0.06] |
| PASS | G4-stress | 2x costs +0.40 (need +0.15), 3x +0.31 (need +0.00), +1 bar delay +0.45 (need +0.10) |
| PASS | G5-permutation | real +0.53 vs null +0.06+-0.13 (p99 +0.33) -> z=3.6, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 0.994 (need 0.95) vs luck bar SR 0.26 after 62 confirmation tests; Bonferroni p 9.05e-03 (need <=0.05) \| stricter all-trials view (1440 screened): DSR 0.790 vs SR 0.38, p 2.10e-01 |
| PASS | G7-stress-pool | median alphaSR +0.40 (need +0.28), 100% positive (need 65%), CAGR +5.1%, median DD -30.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.40 | +0.41 | +5.1% | 14.5% | -30.3% | 0.10 | 47 | 1.33% | 0.36 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `rates_daily` -0.07, `futures_trend_daily` -0.14, `eq_smallcap_daily` -0.20, `fx_major_daily` -0.28, `eq_index_daily` -0.38

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 20
      },
      "weight": 1.0,
      "mode": -1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.5,
  "exit_threshold": 0.1,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.1244,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 20,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "381b0a6f12da",
  "generation": 5,
  "origin": "mutant",
  "parents": [
    "7267d7623bad"
  ]
}
```

</details>

### `cea46db4a4a3` — commodity_meanrev_daily

```
-breakout(n=15)x1.00 -> thr 0.50/0.10 both voltarget@15%v lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 1.23)
- found in generation 8 via mutant from 86c491ea9c30

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.62 (need +0.25), 1805 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.51 (need +0.35), 100% of 20 instances positive (need 70%), median DD -32.2% / worst -49.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.19 (allowed 0.30) [control_efficient_daily=-0.19, control_martingale_daily=-0.00] |
| PASS | G4-stress | 2x costs +0.46 (need +0.15), 3x +0.36 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | real +0.61 vs null +0.09+-0.12 (p99 +0.30) -> z=4.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 0.997 (need 0.95) vs luck bar SR 0.31 after 106 confirmation tests; Bonferroni p 4.43e-04 (need <=0.05) \| stricter all-trials view (2520 screened): DSR 0.850 vs SR 0.42, p 1.05e-02 |
| PASS | G7-stress-pool | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +6.1%, median DD -34.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.45 | +6.1% | 15.9% | -34.1% | 0.11 | 47 | 1.62% | 0.42 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.52, `rates_daily` -0.11, `eq_smallcap_daily` -0.22, `futures_trend_daily` -0.36, `fx_major_daily` -0.38, `eq_index_daily` -0.43

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 15
      },
      "weight": 1.0,
      "mode": -1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.5,
  "exit_threshold": 0.1,
  "direction": "both",
  "sizing": "voltarget",
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
  "bot_id": "cea46db4a4a3",
  "generation": 8,
  "origin": "mutant",
  "parents": [
    "86c491ea9c30"
  ]
}
```

</details>

### `56b292fa87f1` — commodity_meanrev_daily

```
-breakout(n=15)x1.26 -> thr 0.50/0.10 both voltarget@15%v lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 1.23)
- found in generation 17 via mutant from cf65200c718e

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.62 (need +0.25), 1828 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -32.2% / worst -48.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.19 (allowed 0.30) [control_efficient_daily=-0.19, control_martingale_daily=-0.00] |
| PASS | G4-stress | 2x costs +0.46 (need +0.15), 3x +0.36 (need +0.00), +1 bar delay +0.47 (need +0.10) |
| PASS | G5-permutation | real +0.61 vs null +0.09+-0.12 (p99 +0.35) -> z=4.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 0.950 (need 0.95) vs luck bar SR 0.38 after 273 confirmation tests; Bonferroni p 1.92e-03 (need <=0.05) \| stricter all-trials view (7140 screened): DSR 0.426 vs SR 0.50, p 5.03e-02 |
| PASS | G7-stress-pool | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +6.1%, median DD -34.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.45 | +6.1% | 15.9% | -34.4% | 0.11 | 48 | 1.63% | 0.42 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.52, `rates_daily` -0.11, `eq_smallcap_daily` -0.22, `futures_trend_daily` -0.35, `fx_major_daily` -0.38, `eq_index_daily` -0.44

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 15
      },
      "weight": 1.2644,
      "mode": -1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.5,
  "exit_threshold": 0.1,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.0,
  "rebalance_band": 0.1922,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "56b292fa87f1",
  "generation": 17,
  "origin": "mutant",
  "parents": [
    "cf65200c718e"
  ]
}
```

</details>

## Portfolio

```
2 distinct strategies across 1 market(s) / 1 asset class(es)   [from 6 proven genomes]
  best single bot        alphaSR +0.44
  portfolio             alphaSR +0.58
  NOTE: every leg trades the SAME market family, so the two correlation scenarios
        coincide and the blend buys no diversification at all — it is one bet,
        sized twice. Correlation between the legs is measured, not assumed.
    55.7%  a60935fe32e2  commodity_meanrev_daily  alphaSR +0.38
    44.3%  7267d7623bad  commodity_meanrev_daily  alphaSR +0.44
```

There is only one number because there is only one market family, so the correlation assumption never bites. Correlation *between* these legs is measured directly (they share instances), and the blend's small improvement over the best single bot is what two imperfectly correlated expressions of the same effect buy you — not diversification.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `0cb21479740b` | eq_intraday_15m | +0.89 | +1.22 | 2305 | `bollinger(k=2.57,n=32)x0.58 + carry()x1.48 + long_bias()x1.56 -> t` |
| `f99800f63aa8` | eq_intraday_15m | +0.78 | +1.31 | 4882 | `bollinger(k=2.57,n=32)x0.58 + -carry()x1.48 + long_bias()x1.56 -> ` |
| `5ae5c68623b9` | eq_intraday_15m | +0.78 | +1.22 | 1285 | `bollinger(k=2.24,n=30)x0.58 + -carry()x1.37 + long_bias()x1.56 -> ` |
| `6e9785e1678e` | eq_intraday_15m | +0.78 | +1.22 | 1285 | `bollinger(k=2.24,n=30)x0.58 + -carry()x1.37 + long_bias()x1.56 -> ` |
| `f684d2787d17` | eq_intraday_15m | +0.75 | +1.62 | 1206 | `bollinger(k=2.98,n=30)x0.58 + carry()x1.37 + long_bias()x1.56 -> t` |
| `520cd8e2bc1d` | eq_intraday_15m | +0.75 | +1.28 | 2214 | `bollinger(k=2.57,n=32)x0.58 + carry()x1.48 + long_bias()x1.56 -> t` |
| `2e65961fe577` | eq_intraday_15m | +0.75 | +1.28 | 2214 | `bollinger(k=2.57,n=32)x0.58 + -carry()x1.48 + long_bias()x1.56 -> ` |
| `c0eab38042ac` | eq_intraday_15m | +0.75 | +1.28 | 2214 | `bollinger(k=2.57,n=32)x0.58 + -carry()x1.48 + long_bias()x1.56 -> ` |
| `8f616e09e0d9` | eq_intraday_15m | +0.74 | +1.44 | 1252 | `bollinger(k=2.98,n=30)x0.59 + carry()x1.37 + long_bias()x1.56 -> t` |
| `9dac326fb5b7` | eq_intraday_15m | +0.66 | +1.32 | 3102 | `bollinger(k=2.46,n=28)x0.58 + -carry()x1.48 + long_bias()x1.56 + -` |
| `7d649b6325ef` | commodity_meanrev_daily | +0.62 | +0.79 | 6082 | `-momentum(lb=5)x0.76 unanimous rsi_rev(n=27)x1.09 -> thr 0.54/0.10` |
| `4de60c04d6aa` | eq_largecap_daily | +0.62 | +0.71 | 30384 | `-breakout(n=26)x1.04 -> thr 0.40/0.10 both proportional lev<=0.9  ` |
| `27b51838b5e7` | eq_largecap_daily | +0.62 | +0.71 | 30384 | `-breakout(n=26)x1.65 -> thr 0.40/0.10 both proportional lev<=0.9  ` |
| `89dfbf4f3a2f` | commodity_meanrev_daily | +0.61 | +0.79 | 5892 | `-momentum(lb=5)x0.76 unanimous rsi_rev(n=27)x1.09 -> thr 0.54/0.10` |
| `ef57417aa7fa` | commodity_meanrev_daily | +0.61 | +0.77 | 10325 | `-breakout(n=22)x1.50 unanimous -momentum(lb=5)x0.76 unanimous rsi_` |

## Expansions

| generation | new level | trigger | new space |
|---|---|---|---|
| 3 | 2 | 3 generations without a pass | L2: tier=2 genes<=3 filters<=1 pop=360 markets=10 |
| 11 | 3 | 3 generations without a pass | L3: tier=2 genes<=3 filters<=2 pop=540 markets=10 |
| 14 | 4 | 3 generations without a pass | L4: tier=3 genes<=4 filters<=2 pop=640 markets=11 |
| 20 | 5 | 3 generations without a pass | L5: tier=3 genes<=4 filters<=2 pop=640 markets=11 |
| 23 | 6 | 3 generations without a pass | L6: tier=3 genes<=5 filters<=3 pop=640 markets=11 |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 240 | 5 | 17 | 10 | 0 | +0.34 | 9s |
| 2 | 1 | 240 | 5 | 12 | 0 | 0 | +0.38 | 8s |
| 3 | 1 | 240 | 5 | 12 | 0 | 0 | +0.47 | 9s |
| 4 | 2 | 360 | 10 | 15 | 2 | 2 | +0.55 | 14s |
| 5 | 2 | 360 | 10 | 15 | 0 | 2 | +0.55 | 13s |
| 6 | 2 | 360 | 10 | 14 | 0 | 0 | +0.55 | 17s |
| 7 | 2 | 360 | 10 | 16 | 0 | 0 | +0.55 | 17s |
| 8 | 2 | 360 | 10 | 16 | 0 | 1 | +0.52 | 17s |
| 9 | 2 | 360 | 10 | 16 | 0 | 0 | +0.52 | 14s |
| 10 | 2 | 360 | 10 | 16 | 0 | 0 | +0.56 | 14s |
| 11 | 2 | 360 | 10 | 16 | 0 | 0 | +0.57 | 13s |
| 12 | 3 | 540 | 10 | 19 | 0 | 0 | +0.56 | 19s |
| 13 | 3 | 540 | 10 | 20 | 0 | 0 | +0.56 | 19s |
| 14 | 3 | 540 | 10 | 19 | 0 | 0 | +0.56 | 19s |
| 15 | 4 | 640 | 11 | 21 | 0 | 0 | +0.61 | 26s |
| 16 | 4 | 640 | 11 | 20 | 0 | 0 | +0.62 | 25s |
| 17 | 4 | 640 | 11 | 18 | 0 | 1 | +0.75 | 27s |
| 18 | 4 | 640 | 11 | 20 | 0 | 0 | +0.75 | 27s |
| 19 | 4 | 640 | 11 | 22 | 0 | 0 | +0.75 | 27s |
| 20 | 4 | 640 | 11 | 21 | 0 | 0 | +0.75 | 27s |
| 21 | 5 | 640 | 11 | 22 | 0 | 0 | +0.75 | 26s |
| 22 | 5 | 640 | 11 | 22 | 0 | 0 | +0.75 | 27s |
| 23 | 5 | 640 | 11 | 20 | 0 | 0 | +0.78 | 27s |
| 24 | 6 | 640 | 11 | 19 | 0 | 0 | +0.78 | 29s |
| 25 | 6 | 640 | 11 | 22 | 0 | 0 | +0.89 | 28s |

## Market calibration

`ceiling` is the perfect-foresight Sharpe bound implied by the planted structure; `gross`/`net` are the best textbook archetype without and with costs. A family whose net number is negative is a market where the honest answer is *don't trade this*.

The two `control_*` rows show a positive net number (~+0.3) and that is expected, not a contradiction: it is the **maximum over 13 archetypes of a median over 6 instances**, which is a selection statistic, and on 12 years of daily data its null spread is about that size. The point of the controls is not that no single statistic on them is ever positive — it is that nothing survives *replication* on them, which is what the gauntlet tests and what `run.py fpr` measures end to end (0 certified from 3,000 candidates).

| family | vol | ceiling SR | gross alphaSR | net alphaSR | cost bite | archetypes net + |
|---|---|---|---|---|---|---|
| eq_index_daily | 15.9% | 1.45 | +0.62 | +0.51 | +0.10 | 7/10 |
| eq_largecap_daily | 27.6% | 1.17 | +0.66 | +0.55 | +0.11 | 6/10 |
| eq_smallcap_daily | 46.8% | 1.85 | +0.57 | +0.01 | -0.00 | 1/10 |
| fx_major_daily | 8.2% | 1.79 | +0.65 | +0.47 | +0.18 | 6/12 |
| fx_em_daily | 14.8% | 1.45 | +0.34 | +0.11 | +0.23 | 5/12 |
| crypto_major_hourly | 57.0% | 2.57 | +1.14 | -0.38 | +0.53 | 0/10 |
| crypto_alt_hourly | 113.2% | 2.66 | +0.95 | -1.05 | +1.04 | 0/10 |
| futures_trend_daily | 14.3% | 1.34 | +0.51 | +0.42 | +0.09 | 6/12 |
| commodity_meanrev_daily | 35.8% | 1.23 | +0.89 | +0.80 | +0.09 | 3/12 |
| rates_daily | 5.4% | 1.24 | +0.19 | +0.00 | +0.00 | 2/12 |
| eq_intraday_15m | 21.8% | 2.60 | +1.59 | +0.17 | +1.42 | 1/10 |
| control_efficient_daily | 22.0% | 0.00 | +0.36 | +0.29 | +0.07 | 6/10 |
| control_martingale_daily | 20.0% | 0.00 | +0.30 | +0.27 | +0.03 | 4/10 |

## Standard of proof used

```json
{
  "min_oos_alpha_sr": 0.25,
  "min_repl_alpha_sr": 0.35,
  "min_repl_pos_frac": 0.7,
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
