# Bot factory: run report

_Generated 2026-07-31 06:05:01 from `run_state.json`._

## Result

**3 distinct strategies passed all seven gates** (7 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes).

40,740 candidates were screened across 45 generations and 14 search-space expansions; 1285 reached the gauntlet; 100,045 backtests were run.

Markets represented: `commodity_meanrev_daily`, `futures_trend_daily`.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 567 | 44% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 509 | 40% | worked only on the instances it was bred on (instance luck) |
| G3-controls | 1 | 0% | showed profit on a random walk (artifact or harness bug) |
| G4-stress | 103 | 8% | edge smaller than 2x costs or one bar of delay |
| G5-permutation | 61 | 5% | no better than its own block-bootstrapped null |
| G6-multiplicity | 36 | 3% | not surprising given how many candidates were tried |
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

### `0dc98ea16ea7` — futures_trend_daily

```
momentum(lb=126)x1.00 + stoch(n=49)x0.43 | trend_regime(n=67) -> thr 0.15/0.05 both voltarget@5%v lev<=1.7  [stop 2.1atr]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 45 via crossover from a2b40991b175, 416835ed32f3

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 881 trades, 50% instances positive |
| PASS | G2-replication | median alphaSR +0.40 (need +0.35), 95% of 20 instances positive (need 70%), median DD -12.2% / worst -21.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.15 (allowed 0.30) [control_efficient_daily=+0.08, control_martingale_daily=-0.15] |
| PASS | G4-stress | 2x costs +0.52 (need +0.15), 3x +0.49 (need +0.00), +1 bar delay +0.48 (need +0.10) |
| PASS | G5-permutation | real +0.66 vs null +0.10+-0.14 (p99 +0.40) -> z=4.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 0.965 (need 0.95) vs luck bar SR 0.48 after 1255 confirmation tests; Bonferroni p 2.67e-02 (need <=0.05) \| stricter all-trials view (40740 screened): DSR 0.467 vs SR 0.61, p 8.67e-01 |
| PASS | G7-stress-pool | median alphaSR +0.42 (need +0.28), 80% positive (need 65%), CAGR +2.5%, median DD -13.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.42 | +0.51 | +2.5% | 5.1% | -13.0% | 0.07 | 25 | 0.12% | 0.34 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.44, `fx_em_daily` +0.32, `eq_index_daily` +0.32, `rates_daily` +0.22, `eq_largecap_daily` -0.17, `eq_smallcap_daily` -0.42

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "momentum",
      "params": {
        "lb": 126
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "stoch",
      "params": {
        "n": 49
      },
      "weight": 0.4317,
      "mode": 1
    }
  ],
  "filters": [
    {
      "name": "trend_regime",
      "params": {
        "n": 67
      }
    }
  ],
  "combine": "weighted",
  "entry_threshold": 0.15,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.0,
  "target_vol": 0.0532,
  "max_leverage": 1.6743,
  "rebalance_band": 0.2742,
  "atr_n": 20,
  "stop_atr": 2.1,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "0dc98ea16ea7",
  "generation": 45,
  "origin": "crossover",
  "parents": [
    "a2b40991b175",
    "416835ed32f3"
  ]
}
```

</details>

## Portfolio

```
3 distinct strategies across 2 market(s) / 2 asset class(es)   [from 7 proven genomes]
  best single bot        alphaSR +0.44
  portfolio (lab, rho=0) alphaSR +0.71   <- upper bound, independent synthetic markets
  portfolio (rho=0.3)    alphaSR +0.60   <- plan with this one
    24.4%  a60935fe32e2  commodity_meanrev_daily  alphaSR +0.38
    19.4%  7267d7623bad  commodity_meanrev_daily  alphaSR +0.44
    56.2%  0dc98ea16ea7  futures_trend_daily      alphaSR +0.40
```

The two portfolio numbers differ because this lab generates each market family independently, so cross-family correlation is structurally zero — an assumption real asset classes violate exactly when it matters. Plan with the rho=0.3 number.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `b7b101b57f8b` | eq_intraday_15m | +1.10 | +1.35 | 3833 | `bollinger(k=2.57,n=32)x0.58 + -carry()x1.48 + long_bias()x1.56 -> ` |
| `edb5284741dd` | eq_intraday_15m | +1.05 | +1.34 | 4008 | `bollinger(k=2.57,n=32)x0.58 + -carry()x1.48 + long_bias()x1.56 -> ` |
| `4a0b50a54b35` | eq_intraday_15m | +1.05 | +1.34 | 4008 | `bollinger(k=2.57,n=32)x0.58 + carry()x1.48 + long_bias()x1.56 -> t` |
| `1e0dc2fa6d88` | eq_intraday_15m | +1.03 | +1.41 | 3181 | `bollinger(k=2.57,n=32)x0.58 + carry()x1.48 + long_bias()x1.56 -> t` |
| `11c1e7154dd1` | eq_intraday_15m | +1.02 | +1.41 | 3212 | `bollinger(k=2.57,n=32)x0.58 + carry()x1.48 + long_bias()x1.56 -> t` |
| `95b485f14f30` | eq_intraday_15m | +1.02 | +1.41 | 3212 | `bollinger(k=2.57,n=32)x0.58 + carry()x1.48 + long_bias()x1.56 -> t` |
| `9dd6be7e89c2` | eq_intraday_15m | +1.02 | +1.41 | 3212 | `bollinger(k=2.57,n=32)x0.58 + -carry()x1.48 + long_bias()x1.56 -> ` |
| `84f49134ec86` | eq_intraday_15m | +1.02 | +1.42 | 3044 | `bollinger(k=2.57,n=32)x0.58 + -carry()x1.48 + long_bias()x1.56 -> ` |
| `3305d2061162` | crypto_major_hourly | +0.95 | +1.09 | 9041 | `bollinger(k=1.62,n=101)x0.58 + long_bias()x1.56 -> thr 0.43/0.10 l` |
| `7a3b5ad4ab18` | crypto_major_hourly | +0.95 | +1.09 | 9041 | `bollinger(k=1.62,n=101)x0.58 + long_bias()x1.56 -> thr 0.42/0.10 l` |
| `1521faed6a52` | crypto_major_hourly | +0.94 | +1.11 | 8975 | `bollinger(k=1.51,n=101)x0.58 + long_bias()x1.56 -> thr 0.40/0.10 b` |
| `d6946ccec51c` | crypto_major_hourly | +0.94 | +1.11 | 8975 | `bollinger(k=1.51,n=101)x0.58 + long_bias()x1.56 -> thr 0.40/0.10 b` |
| `fae4296029ad` | crypto_major_hourly | +0.93 | +1.12 | 6063 | `bollinger(k=2.48,n=54)x0.58 + -long_bias()x1.56 -> thr 0.27/0.10 s` |
| `86165d5b9fbb` | crypto_major_hourly | +0.93 | +1.12 | 6053 | `bollinger(k=2.49,n=54)x0.58 + -long_bias()x1.56 -> thr 0.27/0.10 s` |
| `3d07bb0dfc8b` | crypto_major_hourly | +0.92 | +1.12 | 9338 | `bollinger(k=2.17,n=54)x0.66 + -long_bias()x1.54 -> thr 0.33/0.10 b` |

## Expansions

| generation | new level | trigger | new space |
|---|---|---|---|
| 3 | 2 | 3 generations without a pass | L2: tier=2 genes<=3 filters<=1 pop=360 markets=10 |
| 11 | 3 | 3 generations without a pass | L3: tier=2 genes<=3 filters<=2 pop=540 markets=10 |
| 14 | 4 | 3 generations without a pass | L4: tier=3 genes<=4 filters<=2 pop=640 markets=11 |
| 20 | 5 | 3 generations without a pass | L5: tier=3 genes<=4 filters<=2 pop=640 markets=11 |
| 23 | 6 | 3 generations without a pass | L6: tier=3 genes<=5 filters<=3 pop=640 markets=11 |
| 27 | 7 | 2 generations without a pass | L7: tier=3 genes<=5 filters<=3 pop=960 finalists=36 per_mkt=4 markets=11 |
| 29 | 8 | 2 generations without a pass | L8: tier=3 genes<=5 filters<=3 pop=1440 finalists=40 per_mkt=5 markets=11 |
| 31 | 9 | 2 generations without a pass | L9: tier=3 genes<=5 filters<=3 pop=1600 finalists=44 per_mkt=6 markets=11 |
| 33 | 10 | 2 generations without a pass | L10: tier=3 genes<=5 filters<=3 pop=1600 finalists=48 per_mkt=6 markets=11 |
| 35 | 11 | 2 generations without a pass | L11: tier=3 genes<=5 filters<=3 pop=1600 finalists=52 per_mkt=6 markets=11 |
| 37 | 12 | 2 generations without a pass | L12: tier=3 genes<=5 filters<=3 pop=1600 finalists=56 per_mkt=6 markets=11 |
| 39 | 13 | 2 generations without a pass | L13: tier=3 genes<=5 filters<=3 pop=1600 finalists=60 per_mkt=6 markets=11 |
| 41 | 14 | 2 generations without a pass | L14: tier=3 genes<=5 filters<=3 pop=1600 finalists=60 per_mkt=6 markets=11 |
| 43 | 15 | 2 generations without a pass | L15: tier=3 genes<=5 filters<=3 pop=1600 finalists=60 per_mkt=6 markets=11 |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
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
| 26 | 6 | 640 | 11 | 20 | 0 | 0 | +0.89 | 47s |
| 27 | 6 | 640 | 11 | 23 | 0 | 0 | +0.90 | 45s |
| 28 | 7 | 960 | 11 | 25 | 0 | 0 | +0.93 | 67s |
| 29 | 7 | 960 | 11 | 30 | 0 | 0 | +0.93 | 91s |
| 30 | 8 | 1440 | 11 | 37 | 0 | 0 | +0.93 | 93s |
| 31 | 8 | 1440 | 11 | 38 | 0 | 0 | +1.00 | 102s |
| 32 | 9 | 1600 | 11 | 44 | 0 | 0 | +1.00 | 111s |
| 33 | 9 | 1600 | 11 | 44 | 0 | 0 | +1.02 | 119s |
| 34 | 10 | 1600 | 11 | 45 | 0 | 0 | +1.02 | 130s |
| 35 | 10 | 1600 | 11 | 44 | 0 | 0 | +1.02 | 116s |
| 36 | 11 | 1600 | 11 | 47 | 0 | 0 | +1.02 | 124s |
| 37 | 11 | 1600 | 11 | 48 | 0 | 0 | +1.02 | 123s |
| 38 | 12 | 1600 | 11 | 48 | 0 | 0 | +1.02 | 133s |
| 39 | 12 | 1600 | 11 | 43 | 0 | 0 | +1.02 | 126s |
| 40 | 13 | 1600 | 11 | 45 | 0 | 0 | +1.02 | 130s |
| 41 | 13 | 1600 | 11 | 50 | 0 | 0 | +1.02 | 127s |
| 42 | 14 | 1600 | 11 | 49 | 0 | 0 | +1.02 | 135s |
| 43 | 14 | 1600 | 11 | 52 | 0 | 0 | +1.02 | 129s |
| 44 | 15 | 1600 | 11 | 53 | 0 | 0 | +1.05 | 130s |
| 45 | 15 | 1600 | 11 | 50 | 0 | 1 | +1.10 | 121s |

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
