# Bot factory: run report

_Generated 2026-08-05 22:34:04 from `run_state.json`._

## Result

**10 distinct strategies passed all seven gates** (11 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes).

960 candidates were screened across 3 generations and 0 search-space expansions; 42 reached the gauntlet; 9,956 backtests were run.

Markets represented: `eq_largecap_daily`, `futures_trend_daily`, `fx_major_daily`.

**Search-burden headroom.** These were certified after 42 confirmation tests, and G6's luck bar rises with that count — so the count matters as much as the Sharpe. Headroom is the largest search each bot's evidence could have come out of and still clear G6: **11 of 11 genomes clear a bar ten times harder than the one they actually faced** (headroom >=1,073,741,824 down to 1,129). Read it before the Sharpe — a bot whose headroom is close to the tests already run would vanish in a more serious hunt.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 11 | 35% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 19 | 61% | worked only on the instances it was bred on (instance luck) |
| G7-stress-pool | 1 | 3% | failed to replicate a second time on a third pool |

## Proven bots

### `bc49c51e4be8` — futures_trend_daily

```
breakout(n=91)x0.88 unanimous carry()x0.75 -> thr 0.14/0.09 long fixed lev<=3.5  [stop 2.0atr]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 1 via random
- **search-burden headroom: 3,015,050** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 10. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.43 (need +0.25), 1569 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.55 (need +0.35), 100% of 20 instances positive (need 70%), median DD -22.0% / worst -32.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.00 (allowed 0.30) [control_efficient_daily=+0.00, control_martingale_daily=+0.00] |
| PASS | G4-stress | 2x costs +0.51 (need +0.15), 3x +0.49 (need +0.00), +1 bar delay +0.55 (need +0.10) |
| PASS | G5-permutation | real +0.55 vs null +0.05+-0.06 (p99 +0.17) -> z=7.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.15 after 10 confirmation tests (would still pass up to 3,015,050); Bonferroni p 1.55e-14 (need <=0.05) \| stricter all-trials view (320 screened): DSR 1.000 vs SR 0.28, p 4.97e-13 |
| PASS | G7-stress-pool | median alphaSR +0.48 (need +0.28), 100% positive (need 65%), CAGR +4.1%, median DD -23.5% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.48 | +0.65 | +4.1% | 6.5% | -23.5% | 0.14 | 10 | 0.09% | 0.34 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.32, `rates_daily` +0.11, `fx_em_daily` +0.05, `eq_index_daily` +0.00, `eq_largecap_daily` +0.00, `eq_smallcap_daily` +0.00

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 91
      },
      "weight": 0.881,
      "mode": 1
    },
    {
      "name": "carry",
      "params": {},
      "weight": 0.746,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "unanimous",
  "entry_threshold": 0.14,
  "exit_threshold": 0.092,
  "direction": "long",
  "sizing": "fixed",
  "base_size": 0.63,
  "target_vol": 0.2,
  "max_leverage": 3.528,
  "rebalance_band": 0.327,
  "atr_n": 30,
  "stop_atr": 1.98,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": null,
  "dd_resume": 38,
  "bot_id": "bc49c51e4be8",
  "generation": 1,
  "origin": "random",
  "parents": []
}
```

</details>

### `1e850e587087` — futures_trend_daily

```
ma_cross(fast=2,slow=59)x0.72 + momentum(lb=62)x1.33 -> thr 0.42/0.22 both voltarget@6%v lev<=3.0  [halt@44%dd]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 2 via crossover from 9bca5c829bc6, 1aa7bc5a7b3c
- **search-burden headroom: >=1,073,741,824** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 19. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.45 (need +0.25), 2081 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.64 (need +0.35), 100% of 20 instances positive (need 70%), median DD -20.0% / worst -29.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.08 (allowed 0.30) [control_efficient_daily=-0.08, control_martingale_daily=-0.07] |
| PASS | G4-stress | 2x costs +0.63 (need +0.15), 3x +0.62 (need +0.00), +1 bar delay +0.63 (need +0.10) |
| PASS | G5-permutation | real +0.60 vs null +0.04+-0.06 (p99 +0.17) -> z=9.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 19 confirmation tests (would still pass up to >=1,073,741,824); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.30, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.56 (need +0.28), 100% positive (need 65%), CAGR +3.7%, median DD -21.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.56 | +0.65 | +3.7% | 5.9% | -21.2% | 0.10 | 13 | 0.08% | 0.39 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.32, `eq_index_daily` +0.19, `fx_em_daily` +0.18, `rates_daily` +0.09, `eq_largecap_daily` -0.28, `eq_smallcap_daily` -0.41

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 2,
        "slow": 59
      },
      "weight": 0.72,
      "mode": 1
    },
    {
      "name": "momentum",
      "params": {
        "lb": 62
      },
      "weight": 1.326,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.421,
  "exit_threshold": 0.223,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 2.625,
  "target_vol": 0.06,
  "max_leverage": 2.996,
  "rebalance_band": 0.433,
  "atr_n": 37,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": 0.444,
  "dd_resume": 73,
  "bot_id": "1e850e587087",
  "generation": 2,
  "origin": "crossover",
  "parents": [
    "9bca5c829bc6",
    "1aa7bc5a7b3c"
  ]
}
```

</details>

### `1234f60a7380` — futures_trend_daily

```
breakout(n=50)x0.72 unanimous ma_cross(fast=9,slow=58)x1.31 | trend_regime(n=69) -> thr 0.42/0.11 both proportional lev<=4.6  [stop 2.1atr, halt@20%dd]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 2 via crossover from ae3a095392bf, f193ed1a4882
- **search-burden headroom: 891,027,051** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 21. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.40 (need +0.25), 7397 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.58 (need +0.35), 100% of 20 instances positive (need 70%), median DD -13.3% / worst -20.1% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.01, control_martingale_daily=-0.05] |
| PASS | G4-stress | 2x costs +0.58 (need +0.15), 3x +0.56 (need +0.00), +1 bar delay +0.60 (need +0.10) |
| PASS | G5-permutation | real +0.61 vs null +0.06+-0.06 (p99 +0.18) -> z=8.6, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 21 confirmation tests (would still pass up to 891,027,051); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.30, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.57 (need +0.28), 100% positive (need 65%), CAGR +2.3%, median DD -13.9% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.57 | +0.64 | +2.3% | 3.7% | -13.9% | 0.10 | 47 | 0.07% | 0.22 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.32, `eq_index_daily` +0.11, `rates_daily` +0.07, `fx_em_daily` +0.06, `eq_largecap_daily` -0.43, `eq_smallcap_daily` -0.54

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 50
      },
      "weight": 0.717,
      "mode": 1
    },
    {
      "name": "ma_cross",
      "params": {
        "fast": 9,
        "slow": 58
      },
      "weight": 1.311,
      "mode": 1
    }
  ],
  "filters": [
    {
      "name": "trend_regime",
      "params": {
        "n": 69
      }
    }
  ],
  "combine": "unanimous",
  "entry_threshold": 0.42,
  "exit_threshold": 0.111,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.409,
  "target_vol": 0.292,
  "max_leverage": 4.604,
  "rebalance_band": 0.205,
  "atr_n": 27,
  "stop_atr": 2.06,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.2,
  "dd_resume": 5,
  "bot_id": "1234f60a7380",
  "generation": 2,
  "origin": "crossover",
  "parents": [
    "ae3a095392bf",
    "f193ed1a4882"
  ]
}
```

</details>

### `98f31db9ed40` — futures_trend_daily

```
ma_cross(fast=9,slow=58)x1.31 | trend_regime(n=69) -> thr 0.28/0.11 long proportional lev<=4.6  [stop 2.1atr]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 2 via mutant from ae3a095392bf
- **search-burden headroom: 82,555,639** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 22. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.38 (need +0.25), 1555 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.57 (need +0.35), 100% of 20 instances positive (need 70%), median DD -9.6% / worst -12.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.08 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.08] |
| PASS | G4-stress | 2x costs +0.57 (need +0.15), 3x +0.56 (need +0.00), +1 bar delay +0.59 (need +0.10) |
| PASS | G5-permutation | real +0.58 vs null +0.04+-0.07 (p99 +0.21) -> z=8.0, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.19 after 22 confirmation tests (would still pass up to 82,555,639); Bonferroni p 9.77e-15 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.30, p 2.84e-13 |
| PASS | G7-stress-pool | median alphaSR +0.51 (need +0.28), 100% positive (need 65%), CAGR +1.8%, median DD -8.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.51 | +0.66 | +1.8% | 2.8% | -8.4% | 0.11 | 10 | 0.02% | 0.13 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.33, `eq_index_daily` +0.14, `rates_daily` +0.12, `fx_em_daily` +0.11, `eq_largecap_daily` -0.28, `eq_smallcap_daily` -0.34

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 9,
        "slow": 58
      },
      "weight": 1.311,
      "mode": 1
    }
  ],
  "filters": [
    {
      "name": "trend_regime",
      "params": {
        "n": 69
      }
    }
  ],
  "combine": "weighted",
  "entry_threshold": 0.275,
  "exit_threshold": 0.111,
  "direction": "long",
  "sizing": "proportional",
  "base_size": 0.431,
  "target_vol": 0.292,
  "max_leverage": 4.604,
  "rebalance_band": 0.432,
  "atr_n": 19,
  "stop_atr": 2.06,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 55,
  "bot_id": "98f31db9ed40",
  "generation": 2,
  "origin": "mutant",
  "parents": [
    "ae3a095392bf"
  ]
}
```

</details>

### `028ac1971f42` — fx_major_daily

```
breakout(n=50)x0.72 + breakout(n=91)x0.88 -> thr 0.42/0.10 long fixed lev<=3.5  [stop 2.0atr]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 2 via crossover from bc49c51e4be8, f193ed1a4882
- **search-burden headroom: 1,129** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 26. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.47 (need +0.25), 927 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.36 (need +0.35), 90% of 20 instances positive (need 70%), median DD -14.5% / worst -30.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.08 (allowed 0.30) [control_efficient_daily=-0.08, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.29 (need +0.15), 3x +0.28 (need +0.00), +1 bar delay +0.29 (need +0.10) |
| PASS | G5-permutation | real +0.32 vs null +0.03+-0.06 (p99 +0.16) -> z=4.6, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.19 after 26 confirmation tests (would still pass up to 1,129); Bonferroni p 6.41e-05 (need <=0.05) \| stricter all-trials view (640 screened): DSR 0.983 vs SR 0.30, p 1.58e-03 |
| PASS | G7-stress-pool | median alphaSR +0.30 (need +0.28), 100% positive (need 65%), CAGR +1.0%, median DD -14.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.30 | +0.32 | +1.0% | 3.2% | -14.3% | 0.05 | 6 | 0.02% | 0.25 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.51, `eq_index_daily` +0.14, `fx_em_daily` +0.07, `rates_daily` +0.06, `eq_largecap_daily` -0.27, `eq_smallcap_daily` -0.44

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 50
      },
      "weight": 0.717,
      "mode": 1
    },
    {
      "name": "breakout",
      "params": {
        "n": 91
      },
      "weight": 0.881,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.42,
  "exit_threshold": 0.097,
  "direction": "long",
  "sizing": "fixed",
  "base_size": 0.63,
  "target_vol": 0.056,
  "max_leverage": 3.528,
  "rebalance_band": 0.327,
  "atr_n": 30,
  "stop_atr": 1.98,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": null,
  "dd_resume": 38,
  "bot_id": "028ac1971f42",
  "generation": 2,
  "origin": "crossover",
  "parents": [
    "bc49c51e4be8",
    "f193ed1a4882"
  ]
}
```

</details>

### `06725db8db09` — futures_trend_daily

```
ma_cross(fast=2,slow=59)x0.72 + momentum(lb=122)x1.33 -> thr 0.42/0.22 both voltarget@6%v lev<=3.0  [halt@44%dd]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 3 via mutant from 1e850e587087
- **search-burden headroom: >=1,073,741,824** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 31. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.40 (need +0.25), 1555 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.64 (need +0.35), 100% of 20 instances positive (need 70%), median DD -21.4% / worst -28.0% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.64 (need +0.15), 3x +0.63 (need +0.00), +1 bar delay +0.65 (need +0.10) |
| PASS | G5-permutation | real +0.61 vs null +0.04+-0.08 (p99 +0.22) -> z=7.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 31 confirmation tests (would still pass up to >=1,073,741,824); Bonferroni p 4.42e-12 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.33, p 1.37e-10 |
| PASS | G7-stress-pool | median alphaSR +0.54 (need +0.28), 100% positive (need 65%), CAGR +3.6%, median DD -19.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.54 | +0.65 | +3.6% | 5.8% | -19.0% | 0.10 | 10 | 0.06% | 0.37 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.41, `eq_index_daily` +0.19, `fx_em_daily` +0.16, `rates_daily` +0.08, `eq_largecap_daily` -0.28, `eq_smallcap_daily` -0.35

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 2,
        "slow": 59
      },
      "weight": 0.72,
      "mode": 1
    },
    {
      "name": "momentum",
      "params": {
        "lb": 122
      },
      "weight": 1.326,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.421,
  "exit_threshold": 0.223,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 2.625,
  "target_vol": 0.06,
  "max_leverage": 2.996,
  "rebalance_band": 0.433,
  "atr_n": 37,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": 0.444,
  "dd_resume": 73,
  "bot_id": "06725db8db09",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "1e850e587087"
  ]
}
```

</details>

### `d313912aef14` — futures_trend_daily

```
momentum(lb=62)x1.33 -> thr 0.42/0.22 both voltarget@6%v lev<=3.0  [halt@44%dd]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 3 via mutant from 1e850e587087
- **search-burden headroom: 91,563,525** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 32. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.43 (need +0.25), 1987 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.61 (need +0.35), 100% of 20 instances positive (need 70%), median DD -21.9% / worst -31.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.11 (allowed 0.30) [control_efficient_daily=-0.11, control_martingale_daily=-0.04] |
| PASS | G4-stress | 2x costs +0.62 (need +0.15), 3x +0.61 (need +0.00), +1 bar delay +0.64 (need +0.10) |
| PASS | G5-permutation | real +0.59 vs null +0.04+-0.07 (p99 +0.18) -> z=8.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 32 confirmation tests (would still pass up to 91,563,525); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.33, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.55 (need +0.28), 100% positive (need 65%), CAGR +3.7%, median DD -23.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.55 | +0.65 | +3.7% | 5.9% | -23.0% | 0.09 | 12 | 0.08% | 0.39 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.31, `eq_index_daily` +0.23, `fx_em_daily` +0.16, `rates_daily` +0.08, `eq_largecap_daily` -0.21, `eq_smallcap_daily` -0.36

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "momentum",
      "params": {
        "lb": 62
      },
      "weight": 1.326,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.421,
  "exit_threshold": 0.223,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 2.625,
  "target_vol": 0.06,
  "max_leverage": 2.996,
  "rebalance_band": 0.433,
  "atr_n": 37,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": 0.444,
  "dd_resume": 73,
  "bot_id": "d313912aef14",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "1e850e587087"
  ]
}
```

</details>

### `0e16f6db96c5` — eq_largecap_daily

```
-ma_cross(fast=28,slow=10)x0.43 -> thr 0.28/0.20 long proportional lev<=1.8  [trail 7.2atr]
```

- market: **eq_largecap_daily** (equity, vol 28%, spread 3.0bp, perfect-foresight ceiling SR 1.17)
- found in generation 3 via mutant from 372cf6a51355
- **search-burden headroom: 78,394** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 33. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.41 (need +0.25), 8436 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -28.8% / worst -47.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.08 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.08] |
| PASS | G4-stress | 2x costs +0.30 (need +0.15), 3x +0.22 (need +0.00), +1 bar delay +0.35 (need +0.10) |
| PASS | G5-permutation | real +0.42 vs null +0.05+-0.06 (p99 +0.20) -> z=6.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 33 confirmation tests (would still pass up to 78,394); Bonferroni p 1.96e-09 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.33, p 5.70e-08 |
| PASS | G7-stress-pool | median alphaSR +0.37 (need +0.28), 100% positive (need 65%), CAGR +4.5%, median DD -30.8% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.37 | +0.48 | +4.5% | 10.2% | -30.8% | 0.09 | 57 | 0.69% | 0.22 |

Travels to (alphaSR on other families, not a gate): `commodity_meanrev_daily` +0.42, `rates_daily` -0.05, `eq_index_daily` -0.08, `fx_em_daily` -0.17, `eq_smallcap_daily` -0.18, `fx_major_daily` -0.19

<details><summary>genome JSON</summary>

```json
{
  "market": "eq_largecap_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 28,
        "slow": 10
      },
      "weight": 0.432,
      "mode": -1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.28,
  "exit_threshold": 0.2,
  "direction": "long",
  "sizing": "proportional",
  "base_size": 1.025,
  "target_vol": 0.082,
  "max_leverage": 1.811,
  "rebalance_band": 0.203,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": 7.2,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": null,
  "dd_resume": 19,
  "bot_id": "0e16f6db96c5",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "372cf6a51355"
  ]
}
```

</details>

### `caf0e938000d` — futures_trend_daily

```
ma_cross(fast=2,slow=59)x0.72 vote momentum(lb=62)x1.22 -> thr 0.42/0.22 both voltarget@6%v lev<=3.0  [halt@44%dd]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 3 via mutant from 1e850e587087
- **search-burden headroom: 20,298,397** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 34. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.44 (need +0.25), 2760 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.56 (need +0.35), 100% of 20 instances positive (need 70%), median DD -23.1% / worst -43.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.05] |
| PASS | G4-stress | 2x costs +0.56 (need +0.15), 3x +0.54 (need +0.00), +1 bar delay +0.59 (need +0.10) |
| PASS | G5-permutation | real +0.60 vs null +0.03+-0.07 (p99 +0.15) -> z=8.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 34 confirmation tests (would still pass up to 20,298,397); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.33, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.57 (need +0.28), 100% positive (need 65%), CAGR +3.8%, median DD -23.9% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.57 | +0.62 | +3.8% | 6.3% | -23.9% | 0.09 | 18 | 0.14% | 0.44 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.28, `eq_index_daily` +0.16, `fx_em_daily` +0.13, `rates_daily` +0.01, `eq_largecap_daily` -0.27, `eq_smallcap_daily` -0.51

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 2,
        "slow": 59
      },
      "weight": 0.72,
      "mode": 1
    },
    {
      "name": "momentum",
      "params": {
        "lb": 62
      },
      "weight": 1.2226,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "vote",
  "entry_threshold": 0.421,
  "exit_threshold": 0.223,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 2.625,
  "target_vol": 0.06,
  "max_leverage": 2.996,
  "rebalance_band": 0.433,
  "atr_n": 37,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": 0.444,
  "dd_resume": 73,
  "bot_id": "caf0e938000d",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "1e850e587087"
  ]
}
```

</details>

### `4e4596f20706` — fx_major_daily

```
breakout(n=98)x1.00 -> thr 0.42/0.10 both proportional lev<=2.4  [halt@20%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 3 via mutant from f193ed1a4882
- **search-burden headroom: 2,750** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 37. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.44 (need +0.25), 11102 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.38 (need +0.35), 100% of 20 instances positive (need 70%), median DD -9.2% / worst -14.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.35 (need +0.15), 3x +0.34 (need +0.00), +1 bar delay +0.38 (need +0.10) |
| PASS | G5-permutation | real +0.36 vs null +0.01+-0.07 (p99 +0.17) -> z=4.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 37 confirmation tests (would still pass up to 2,750); Bonferroni p 2.59e-05 (need <=0.05) \| stricter all-trials view (960 screened): DSR 0.995 vs SR 0.33, p 6.72e-04 |
| PASS | G7-stress-pool | median alphaSR +0.32 (need +0.28), 100% positive (need 65%), CAGR +0.7%, median DD -9.9% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.32 | +0.36 | +0.7% | 2.1% | -9.9% | 0.04 | 76 | 0.04% | 0.23 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.63, `eq_index_daily` +0.10, `rates_daily` +0.08, `fx_em_daily` +0.04, `eq_largecap_daily` -0.39, `eq_smallcap_daily` -0.56

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 98
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.42,
  "exit_threshold": 0.097,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.409,
  "target_vol": 0.056,
  "max_leverage": 2.447,
  "rebalance_band": 0.164,
  "atr_n": 27,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.2,
  "dd_resume": 5,
  "bot_id": "4e4596f20706",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "f193ed1a4882"
  ]
}
```

</details>

### `61c34bdbdfa4` — fx_major_daily

```
breakout(n=50)x0.72 + ma_cross(fast=4,slow=100)x0.71 | trend_regime(n=209) -> thr 0.20/0.10 both fixed lev<=4.8  [stop 1.1atr, halt@20%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 3 via crossover from f193ed1a4882, 3953f7fa0da4
- **search-burden headroom: 3,414** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 39. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.41 (need +0.25), 2127 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.43 (need +0.35), 100% of 20 instances positive (need 70%), median DD -11.0% / worst -18.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.07 (allowed 0.30) [control_efficient_daily=-0.07, control_martingale_daily=-0.05] |
| PASS | G4-stress | 2x costs +0.37 (need +0.15), 3x +0.36 (need +0.00), +1 bar delay +0.35 (need +0.10) |
| PASS | G5-permutation | real +0.38 vs null +0.03+-0.06 (p99 +0.16) -> z=5.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 39 confirmation tests (would still pass up to 3,414); Bonferroni p 2.28e-07 (need <=0.05) \| stricter all-trials view (960 screened): DSR 0.997 vs SR 0.33, p 5.61e-06 |
| PASS | G7-stress-pool | median alphaSR +0.29 (need +0.28), 95% positive (need 65%), CAGR +0.8%, median DD -12.7% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.29 | +0.30 | +0.8% | 2.6% | -12.7% | 0.04 | 15 | 0.04% | 0.26 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.61, `fx_em_daily` +0.11, `rates_daily` +0.10, `eq_index_daily` +0.01, `eq_largecap_daily` -0.29, `eq_smallcap_daily` -0.50

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 50
      },
      "weight": 0.717,
      "mode": 1
    },
    {
      "name": "ma_cross",
      "params": {
        "fast": 4,
        "slow": 100
      },
      "weight": 0.71,
      "mode": 1
    }
  ],
  "filters": [
    {
      "name": "trend_regime",
      "params": {
        "n": 209
      }
    }
  ],
  "combine": "weighted",
  "entry_threshold": 0.205,
  "exit_threshold": 0.097,
  "direction": "both",
  "sizing": "fixed",
  "base_size": 0.409,
  "target_vol": 0.243,
  "max_leverage": 4.755,
  "rebalance_band": 0.205,
  "atr_n": 27,
  "stop_atr": 1.09,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.2,
  "dd_resume": 5,
  "bot_id": "61c34bdbdfa4",
  "generation": 3,
  "origin": "crossover",
  "parents": [
    "f193ed1a4882",
    "3953f7fa0da4"
  ]
}
```

</details>

## Portfolio

```
10 distinct strategies across 3 market(s) / 3 asset class(es)   [from 11 proven genomes]
  best single bot        alphaSR +0.59
  portfolio (lab, rho=0) alphaSR +1.14   <- upper bound, independent synthetic markets
  portfolio (rho=0.3)    alphaSR +0.82   <- plan with this one
     7.7%  bc49c51e4be8  futures_trend_daily      alphaSR +0.52
     6.0%  1e850e587087  futures_trend_daily      alphaSR +0.59
     9.6%  1234f60a7380  futures_trend_daily      alphaSR +0.59
    16.7%  98f31db9ed40  futures_trend_daily      alphaSR +0.52
    14.0%  028ac1971f42  fx_major_daily           alphaSR +0.30
     6.0%  d313912aef14  futures_trend_daily      alphaSR +0.58
     4.3%  0e16f6db96c5  eq_largecap_daily        alphaSR +0.41
     5.6%  caf0e938000d  futures_trend_daily      alphaSR +0.56
    16.6%  4e4596f20706  fx_major_daily           alphaSR +0.35
    13.5%  61c34bdbdfa4  fx_major_daily           alphaSR +0.29
```

The two portfolio numbers differ because this lab generates each market family independently, so cross-family correlation is structurally zero — an assumption real asset classes violate exactly when it matters. Plan with the rho=0.3 number.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `06725db8db09` | futures_trend_daily | +0.52 | +0.58 | 6488 | `ma_cross(fast=2,slow=59)x0.72 + momentum(lb=122)x1.33 -> thr 0.42/` |
| `d313912aef14` | futures_trend_daily | +0.52 | +0.54 | 8463 | `momentum(lb=62)x1.33 -> thr 0.42/0.22 both voltarget@6%v lev<=3.0 ` |
| `1e850e587087` | futures_trend_daily | +0.48 | +0.55 | 8812 | `ma_cross(fast=2,slow=59)x0.72 + momentum(lb=62)x1.33 -> thr 0.42/0` |
| `0e16f6db96c5` | eq_largecap_daily | +0.45 | +0.51 | 38422 | `-ma_cross(fast=28,slow=10)x0.43 -> thr 0.28/0.20 long proportional` |
| `caf0e938000d` | futures_trend_daily | +0.44 | +0.53 | 11771 | `ma_cross(fast=2,slow=59)x0.72 vote momentum(lb=62)x1.22 -> thr 0.4` |
| `c4a6afc450c6` | futures_trend_daily | +0.44 | +0.58 | 10243 | `ma_cross(fast=2,slow=59)x0.72 + momentum(lb=62)x1.33 \| trend_regim` |
| `200770c16b01` | futures_trend_daily | +0.44 | +0.56 | 10138 | `ma_cross(fast=2,slow=72)x0.72 -> thr 0.42/0.22 both voltarget@6%v ` |
| `afbf9ba2fab0` | futures_trend_daily | +0.44 | +0.52 | 3539 | `breakout(n=55)x1.00 + momentum(lb=62)x1.33 -> thr 0.90/0.20 both v` |
| `80c6c1638a3a` | eq_largecap_daily | +0.43 | +0.50 | 25764 | `-ma_cross(fast=25,slow=21)x0.43 + rsi_rev(n=12)x0.65 -> thr 0.28/0` |
| `915e2619708a` | eq_largecap_daily | +0.43 | +0.50 | 78572 | `rsi_rev(n=7)x1.00 -> thr 0.40/0.05 both proportional lev<=1.7  [ho` |
| `43bd2149a115` | futures_trend_daily | +0.41 | +0.52 | 55828 | `breakout(n=46)x1.46 + zrev(lb=13)x0.43 -> thr 0.12/0.04 both propo` |
| `d97abc36a4ab` | eq_largecap_daily | +0.41 | +0.44 | 17797 | `-ma_cross(fast=22,slow=21)x0.43 -> thr 0.30/0.20 long proportional` |
| `ecebf5f0a18c` | futures_trend_daily | +0.40 | +0.45 | 23884 | `ma_cross(fast=11,slow=23)x0.59 -> thr 0.51/0.42 both proportional ` |
| `611281f012ce` | futures_trend_daily | +0.39 | +0.53 | 54376 | `breakout(n=50)x0.72 \| trend_regime(n=69) -> thr 0.42/0.11 both pro` |
| `aee702e43a06` | eq_largecap_daily | +0.39 | +0.48 | 33950 | `bollinger(k=1.36,n=73)x0.60 + rsi_rev(n=5)x0.71 -> thr 0.40/0.19 b` |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 320 | 5 | 18 | 8 | 1 | +0.36 | 50s |
| 2 | 1 | 320 | 5 | 12 | 0 | 4 | +0.48 | 44s |
| 3 | 1 | 320 | 5 | 12 | 0 | 6 | +0.53 | 43s |

## Market calibration

`ceiling` is the perfect-foresight Sharpe bound implied by the planted structure; `gross`/`net` are the best textbook archetype without and with costs. A family whose net number is negative is a market where the honest answer is *don't trade this*.

The two `control_*` rows show a positive net number (~+0.3) and that is expected, not a contradiction: it is the **maximum over 13 archetypes of a median over 6 instances**, which is a selection statistic, and on 12 years of daily data its null spread is about that size. The point of the controls is not that no single statistic on them is ever positive — it is that nothing survives *replication* on them, which is what the gauntlet tests and what `run.py fpr` measures end to end (0 certified from 3,000 candidates).

| family | vol | ceiling SR | gross alphaSR | net alphaSR | cost bite | archetypes net + |
|---|---|---|---|---|---|---|
| eq_index_daily | 16.3% | 1.45 | +0.27 | +0.13 | +0.13 | 4/10 |
| eq_largecap_daily | 29.1% | 1.17 | +0.62 | +0.51 | +0.11 | 4/10 |
| eq_smallcap_daily | 46.0% | 1.85 | +0.65 | +0.00 | +0.00 | 1/10 |
| fx_major_daily | 8.3% | 1.79 | +0.49 | +0.31 | +0.18 | 6/12 |
| fx_em_daily | 13.8% | 1.45 | +0.31 | +0.12 | +0.19 | 4/12 |
| crypto_major_hourly | 58.4% | 2.57 | +0.98 | -0.75 | +0.74 | 0/10 |
| crypto_alt_hourly | 110.5% | 2.66 | +1.39 | -0.95 | +0.95 | 0/10 |
| futures_trend_daily | 13.9% | 1.34 | +0.51 | +0.43 | +0.08 | 7/12 |
| commodity_meanrev_daily | 35.7% | 1.23 | +0.67 | +0.53 | +0.14 | 4/12 |
| rates_daily | 5.5% | 1.24 | +0.40 | +0.26 | +0.14 | 8/12 |
| eq_intraday_15m | 21.9% | 2.60 | +1.11 | -0.00 | -0.00 | 0/10 |
| control_efficient_daily | 20.5% | 0.00 | +0.12 | +0.08 | +0.04 | 4/10 |
| control_martingale_daily | 20.0% | 0.00 | +0.09 | +0.07 | +0.02 | 6/10 |

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
