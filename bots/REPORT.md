# Bot factory: run report

_Generated 2026-08-05 21:44:42 from `run_state.json`._

## Result

**6 distinct strategies passed all seven gates** (7 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes).

960 candidates were screened across 3 generations and 0 search-space expansions; 41 reached the gauntlet; 6,968 backtests were run.

Markets represented: `futures_trend_daily`, `fx_major_daily`.

**Search-burden headroom.** These were certified after 41 confirmation tests, and G6's luck bar rises with that count — so the count matters as much as the Sharpe. Headroom is the largest search each bot's evidence could have come out of and still clear G6: **6 of 7 genomes clear a bar ten times harder than the one they actually faced** (headroom 2,779,442 down to 263). Read it before the Sharpe — a bot whose headroom is close to the tests already run would vanish in a more serious hunt.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 8 | 24% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 25 | 74% | worked only on the instances it was bred on (instance luck) |
| G7-stress-pool | 1 | 3% | failed to replicate a second time on a third pool |

## Proven bots

### `bc49c51e4be8` — futures_trend_daily

```
breakout(n=91)x0.88 unanimous carry()x0.75 -> thr 0.14/0.09 long fixed lev<=3.5  [stop 2.0atr]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 1 via random
- **search-burden headroom: 4,731** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 12. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.51 (need +0.25), 695 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.46 (need +0.35), 100% of 20 instances positive (need 70%), median DD -19.3% / worst -28.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.00 (allowed 0.30) [control_efficient_daily=+0.00, control_martingale_daily=+0.00] |
| PASS | G4-stress | 2x costs +0.61 (need +0.15), 3x +0.60 (need +0.00), +1 bar delay +0.58 (need +0.10) |
| PASS | G5-permutation | real +0.52 vs null +0.08+-0.10 (p99 +0.33) -> z=4.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.15 after 12 confirmation tests (would still pass up to 4,731); Bonferroni p 1.27e-04 (need <=0.05) \| stricter all-trials view (320 screened): DSR 1.000 vs SR 0.27, p 3.38e-03 |
| PASS | G7-stress-pool | median alphaSR +0.52 (need +0.28), 95% positive (need 65%), CAGR +3.6%, median DD -17.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.52 | +0.61 | +3.6% | 6.2% | -17.4% | 0.11 | 9 | 0.08% | 0.32 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.36, `fx_em_daily` +0.19, `rates_daily` +0.12, `eq_index_daily` +0.00, `eq_largecap_daily` +0.00, `eq_smallcap_daily` +0.00

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

### `cc979a601706` — futures_trend_daily

```
ma_cross(fast=50,slow=91)x1.16 + -rsi_rev(n=7)x0.61 -> thr 0.23/0.12 both proportional lev<=2.2  [stop 3.7atr]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 2 via mutant from 62304448e1df
- **search-burden headroom: 2,779,442** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 19. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.52 (need +0.25), 2994 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -28.4% / worst -44.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=+0.01] |
| PASS | G4-stress | 2x costs +0.59 (need +0.15), 3x +0.53 (need +0.00), +1 bar delay +0.65 (need +0.10) |
| PASS | G5-permutation | real +0.61 vs null +0.09+-0.09 (p99 +0.35) -> z=5.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.17 after 19 confirmation tests (would still pass up to 2,779,442); Bonferroni p 3.42e-07 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.28, p 1.15e-05 |
| PASS | G7-stress-pool | median alphaSR +0.55 (need +0.28), 95% positive (need 65%), CAGR +7.2%, median DD -29.7% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.55 | +0.64 | +7.2% | 12.0% | -29.7% | 0.14 | 40 | 0.76% | 0.71 |

Travels to (alphaSR on other families, not a gate): `eq_index_daily` +0.35, `fx_major_daily` +0.35, `rates_daily` +0.14, `fx_em_daily` +0.09, `eq_largecap_daily` -0.30, `eq_smallcap_daily` -0.56

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 50,
        "slow": 91
      },
      "weight": 1.164,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 7
      },
      "weight": 0.61,
      "mode": -1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.229,
  "exit_threshold": 0.125,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 2.654,
  "target_vol": 0.154,
  "max_leverage": 2.224,
  "rebalance_band": 0.377,
  "atr_n": 25,
  "stop_atr": 3.73,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 5,
  "dd_halt": null,
  "dd_resume": 6,
  "bot_id": "cc979a601706",
  "generation": 2,
  "origin": "mutant",
  "parents": [
    "62304448e1df"
  ]
}
```

</details>

### `471990f1c3e1` — fx_major_daily

```
breakout(n=50)x0.72 + rsi_rev(n=28)x0.65 -> thr 0.42/0.07 both voltarget@6%v lev<=1.8
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 2 via crossover from f193ed1a4882, 03e46a56e685
- **search-burden headroom: 1,017** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 26. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.42 (need +0.25), 710 trades, 75% instances positive |
| PASS | G2-replication | median alphaSR +0.39 (need +0.35), 95% of 20 instances positive (need 70%), median DD -15.2% / worst -27.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.00, control_martingale_daily=-0.03] |
| PASS | G4-stress | 2x costs +0.32 (need +0.15), 3x +0.30 (need +0.00), +1 bar delay +0.37 (need +0.10) |
| PASS | G5-permutation | real +0.37 vs null +0.00+-0.09 (p99 +0.24) -> z=3.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 26 confirmation tests (would still pass up to 1,017); Bonferroni p 1.28e-03 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.28, p 3.14e-02 |
| PASS | G7-stress-pool | median alphaSR +0.36 (need +0.28), 70% positive (need 65%), CAGR +1.4%, median DD -14.9% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.36 | +0.36 | +1.4% | 4.2% | -14.9% | 0.05 | 9 | 0.08% | 0.38 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.46, `fx_em_daily` +0.29, `eq_index_daily` +0.26, `rates_daily` +0.11, `eq_largecap_daily` -0.39, `eq_smallcap_daily` -0.40

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
      "name": "rsi_rev",
      "params": {
        "n": 28
      },
      "weight": 0.645,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.42,
  "exit_threshold": 0.071,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.498,
  "target_vol": 0.056,
  "max_leverage": 1.782,
  "rebalance_band": 0.535,
  "atr_n": 31,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 5,
  "dd_halt": null,
  "dd_resume": 24,
  "bot_id": "471990f1c3e1",
  "generation": 2,
  "origin": "crossover",
  "parents": [
    "f193ed1a4882",
    "03e46a56e685"
  ]
}
```

</details>

### `715224a93087` — futures_trend_daily

```
ma_cross(fast=20,slow=100)x1.00 + ma_cross(fast=50,slow=91)x1.16 -> thr 0.10/0.10 both proportional lev<=2.2  [stop 3.7atr]
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 3 via crossover from e4910ff6d4ce, cc979a601706
- **search-burden headroom: 241,768** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 31. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.51 (need +0.25), 1982 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 95% of 20 instances positive (need 70%), median DD -19.7% / worst -25.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=+0.02, control_martingale_daily=+0.02] |
| PASS | G4-stress | 2x costs +0.70 (need +0.15), 3x +0.70 (need +0.00), +1 bar delay +0.70 (need +0.10) |
| PASS | G5-permutation | real +0.65 vs null +0.09+-0.11 (p99 +0.33) -> z=5.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.21 after 31 confirmation tests (would still pass up to 241,768); Bonferroni p 6.41e-06 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.33, p 1.99e-04 |
| PASS | G7-stress-pool | median alphaSR +0.59 (need +0.28), 95% positive (need 65%), CAGR +4.5%, median DD -20.5% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.59 | +0.67 | +4.5% | 7.0% | -20.5% | 0.12 | 25 | 0.03% | 0.47 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.42, `fx_em_daily` +0.31, `eq_index_daily` +0.29, `rates_daily` +0.24, `eq_smallcap_daily` -0.12, `eq_largecap_daily` -0.15

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 20,
        "slow": 100
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "ma_cross",
      "params": {
        "fast": 50,
        "slow": 91
      },
      "weight": 1.164,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.1,
  "exit_threshold": 0.099,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.15,
  "max_leverage": 2.224,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": 3.73,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "715224a93087",
  "generation": 3,
  "origin": "crossover",
  "parents": [
    "e4910ff6d4ce",
    "cc979a601706"
  ]
}
```

</details>

### `c75b1814f73b` — fx_major_daily

```
breakout(n=50)x0.72 + rsi_rev(n=10)x0.65 -> thr 0.34/0.07 both voltarget@6%v lev<=1.8
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 3 via crossover from be11c27dddea, 471990f1c3e1
- **search-burden headroom: 2,405** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 36. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.47 (need +0.25), 887 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.40 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.4% / worst -27.1% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.12 (allowed 0.30) [control_efficient_daily=-0.00, control_martingale_daily=-0.12] |
| PASS | G4-stress | 2x costs +0.36 (need +0.15), 3x +0.34 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | real +0.40 vs null +0.00+-0.09 (p99 +0.18) -> z=4.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 36 confirmation tests (would still pass up to 2,405); Bonferroni p 2.50e-04 (need <=0.05) \| stricter all-trials view (960 screened): DSR 0.986 vs SR 0.33, p 6.65e-03 |
| PASS | G7-stress-pool | median alphaSR +0.31 (need +0.28), 95% positive (need 65%), CAGR +1.7%, median DD -17.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.31 | +0.38 | +1.7% | 4.7% | -17.2% | 0.07 | 12 | 0.11% | 0.48 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.49, `fx_em_daily` +0.28, `eq_index_daily` +0.22, `rates_daily` +0.19, `eq_largecap_daily` -0.20, `eq_smallcap_daily` -0.30

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
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 0.645,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.341,
  "exit_threshold": 0.071,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.498,
  "target_vol": 0.056,
  "max_leverage": 1.782,
  "rebalance_band": 0.5193,
  "atr_n": 31,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 5,
  "dd_halt": null,
  "dd_resume": 24,
  "bot_id": "c75b1814f73b",
  "generation": 3,
  "origin": "crossover",
  "parents": [
    "be11c27dddea",
    "471990f1c3e1"
  ]
}
```

</details>

### `824eaa23a9ab` — fx_major_daily

```
breakout(n=78)x0.72 -> thr 0.42/0.10 both proportional lev<=2.4  [halt@20%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 3 via mutant from 4df126c5bcd9
- **search-burden headroom: 263** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 37. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.50 (need +0.25), 4934 trades, 75% instances positive |
| PASS | G2-replication | median alphaSR +0.38 (need +0.35), 100% of 20 instances positive (need 70%), median DD -7.7% / worst -13.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.10 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.10] |
| PASS | G4-stress | 2x costs +0.33 (need +0.15), 3x +0.31 (need +0.00), +1 bar delay +0.38 (need +0.10) |
| PASS | G5-permutation | real +0.34 vs null -0.00+-0.09 (p99 +0.18) -> z=3.6, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 37 confirmation tests (would still pass up to 263); Bonferroni p 7.02e-03 (need <=0.05) \| stricter all-trials view (960 screened): DSR 0.973 vs SR 0.33, p 1.82e-01 |
| PASS | G7-stress-pool | median alphaSR +0.29 (need +0.28), 85% positive (need 65%), CAGR +0.7%, median DD -8.8% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.29 | +0.36 | +0.7% | 2.1% | -8.8% | 0.05 | 69 | 0.04% | 0.22 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.56, `eq_index_daily` +0.26, `rates_daily` +0.14, `fx_em_daily` +0.14, `eq_largecap_daily` -0.44, `eq_smallcap_daily` -0.63

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 78
      },
      "weight": 0.717,
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
  "target_vol": 0.0475,
  "max_leverage": 2.447,
  "rebalance_band": 0.205,
  "atr_n": 27,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.2,
  "dd_resume": 5,
  "bot_id": "824eaa23a9ab",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "4df126c5bcd9"
  ]
}
```

</details>

### `d8d97a6d4d8c` — fx_major_daily

```
momentum(lb=56)x1.28 + rsi_rev(n=10)x0.65 -> thr 0.60/0.18 both voltarget@8%v lev<=2.0  [stop 4.2atr]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 3 via crossover from bc9c9bc67adb, be11c27dddea
- **search-burden headroom: 2,028** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 38. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.42 (need +0.25), 346 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.40 (need +0.35), 95% of 20 instances positive (need 70%), median DD -17.1% / worst -44.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G3-controls | worst \|alphaSR\| 0.11 (allowed 0.30) [control_efficient_daily=-0.11, control_martingale_daily=-0.10] |
| PASS | G4-stress | 2x costs +0.30 (need +0.15), 3x +0.24 (need +0.00), +1 bar delay +0.32 (need +0.10) |
| PASS | G5-permutation | real +0.35 vs null -0.02+-0.09 (p99 +0.18) -> z=4.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 38 confirmation tests (would still pass up to 2,028); Bonferroni p 6.02e-04 (need <=0.05) \| stricter all-trials view (960 screened): DSR 0.982 vs SR 0.33, p 1.52e-02 |
| PASS | G7-stress-pool | median alphaSR +0.35 (need +0.28), 90% positive (need 65%), CAGR +2.1%, median DD -18.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.35 | +0.40 | +2.1% | 5.5% | -18.4% | 0.07 | 5 | 0.31% | 0.45 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.54, `fx_em_daily` +0.41, `eq_index_daily` +0.34, `rates_daily` +0.18, `eq_largecap_daily` -0.01, `commodity_meanrev_daily` -0.01

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "momentum",
      "params": {
        "lb": 56
      },
      "weight": 1.284,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 0.645,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.599,
  "exit_threshold": 0.177,
  "direction": "both",
  "sizing": "voltarget",
  "base_size": 1.805,
  "target_vol": 0.082,
  "max_leverage": 2.015,
  "rebalance_band": 0.367,
  "atr_n": 38,
  "stop_atr": 4.16,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": null,
  "dd_resume": 19,
  "bot_id": "d8d97a6d4d8c",
  "generation": 3,
  "origin": "crossover",
  "parents": [
    "bc9c9bc67adb",
    "be11c27dddea"
  ]
}
```

</details>

## Portfolio

```
6 distinct strategies across 2 market(s) / 2 asset class(es)   [from 7 proven genomes]
  best single bot        alphaSR +0.57
  portfolio (lab, rho=0) alphaSR +0.97   <- upper bound, independent synthetic markets
  portfolio (rho=0.3)    alphaSR +0.74   <- plan with this one
    16.7%  bc49c51e4be8  futures_trend_daily      alphaSR +0.53
     6.2%  cc979a601706  futures_trend_daily      alphaSR +0.55
    17.6%  471990f1c3e1  fx_major_daily           alphaSR +0.32
    10.8%  715224a93087  futures_trend_daily      alphaSR +0.57
    35.2%  824eaa23a9ab  fx_major_daily           alphaSR +0.31
    13.4%  d8d97a6d4d8c  fx_major_daily           alphaSR +0.36
```

The two portfolio numbers differ because this lab generates each market family independently, so cross-family correlation is structurally zero — an assumption real asset classes violate exactly when it matters. Plan with the rho=0.3 number.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `7a1bcf537529` | futures_trend_daily | +0.52 | +0.55 | 4422 | `ma_cross(fast=17,slow=100)x1.00 -> thr 0.10/0.02 both voltarget@13` |
| `5cca83b98c31` | futures_trend_daily | +0.50 | +0.58 | 4827 | `ma_cross(fast=19,slow=100)x1.00 -> thr 0.15/0.05 both voltarget@15` |
| `715224a93087` | futures_trend_daily | +0.49 | +0.56 | 8254 | `ma_cross(fast=20,slow=100)x1.00 + ma_cross(fast=50,slow=91)x1.16 -` |
| `c69ecca05934` | futures_trend_daily | +0.49 | +0.63 | 6806 | `ma_cross(fast=20,slow=100)x1.00 + momentum(lb=40)x1.00 -> thr 0.15` |
| `9bedf150770e` | futures_trend_daily | +0.49 | +0.58 | 6505 | `breakout(n=51)x0.57 + ma_cross(fast=20,slow=100)x1.00 -> thr 0.15/` |
| `cc979a601706` | futures_trend_daily | +0.49 | +0.55 | 13421 | `ma_cross(fast=50,slow=91)x1.16 + -rsi_rev(n=7)x0.61 -> thr 0.23/0.` |
| `8fd42321b458` | futures_trend_daily | +0.48 | +0.59 | 7817 | `ma_cross(fast=22,slow=100)x1.00 \| trend_regime(n=76) -> thr 0.09/0` |
| `44431e6f2367` | futures_trend_daily | +0.48 | +0.54 | 7731 | `ma_cross(fast=18,slow=130)x1.00 \| trend_regime(n=76) -> thr 0.09/0` |
| `31f206a25e01` | futures_trend_daily | +0.47 | +0.62 | 3967 | `breakout(n=36)x0.72 + ma_cross(fast=20,slow=100)x1.00 -> thr 0.15/` |
| `441e60568718` | futures_trend_daily | +0.46 | +0.58 | 6806 | `ma_cross(fast=20,slow=100)x1.00 + momentum(lb=45)x1.00 -> thr 0.15` |
| `152b3ef81f20` | eq_largecap_daily | +0.36 | +0.42 | 24292 | `bollinger(k=2.00,n=8)x1.00 -> thr 0.50/0.10 both voltarget@15%v le` |
| `50e6366e351c` | eq_largecap_daily | +0.35 | +0.40 | 23905 | `bollinger(k=2.14,n=8)x1.00 -> thr 0.50/0.10 both voltarget@15%v le` |
| `2af4fb89fdd9` | eq_largecap_daily | +0.34 | +0.50 | 11496 | `bollinger(k=2.40,n=20)x1.00 -> thr 0.50/0.10 both fixed lev<=2.0  ` |
| `1f5ac3ac98ef` | eq_largecap_daily | +0.32 | +0.45 | 17129 | `bollinger(k=2.00,n=20)x1.00 + zrev(lb=15)x1.38 -> thr 0.50/0.10 lo` |
| `f97f75a0a8bd` | eq_largecap_daily | +0.30 | +0.41 | 19437 | `zrev(lb=15)x1.38 -> thr 0.50/0.10 both voltarget@15%v lev<=2.0  [h` |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 320 | 5 | 17 | 11 | 1 | +0.46 | 26s |
| 2 | 1 | 320 | 5 | 12 | 0 | 2 | +0.49 | 24s |
| 3 | 1 | 320 | 5 | 12 | 0 | 4 | +0.52 | 25s |

## Market calibration

`ceiling` is the perfect-foresight Sharpe bound implied by the planted structure; `gross`/`net` are the best textbook archetype without and with costs. A family whose net number is negative is a market where the honest answer is *don't trade this*.

The two `control_*` rows show a positive net number (~+0.3) and that is expected, not a contradiction: it is the **maximum over 13 archetypes of a median over 6 instances**, which is a selection statistic, and on 12 years of daily data its null spread is about that size. The point of the controls is not that no single statistic on them is ever positive — it is that nothing survives *replication* on them, which is what the gauntlet tests and what `run.py fpr` measures end to end (0 certified from 3,000 candidates).

| family | vol | ceiling SR | gross alphaSR | net alphaSR | cost bite | archetypes net + |
|---|---|---|---|---|---|---|
| eq_index_daily | 16.4% | 1.45 | +0.42 | +0.33 | +0.09 | 6/10 |
| eq_largecap_daily | 28.6% | 1.17 | +0.51 | +0.41 | +0.10 | 5/10 |
| eq_smallcap_daily | 45.1% | 1.85 | +0.66 | +0.00 | +0.00 | 1/10 |
| fx_major_daily | 8.2% | 1.79 | +0.46 | +0.28 | +0.18 | 6/12 |
| fx_em_daily | 14.7% | 1.45 | +0.31 | +0.10 | +0.21 | 4/12 |
| crypto_major_hourly | 56.7% | 2.57 | +1.20 | -0.76 | +0.75 | 0/10 |
| crypto_alt_hourly | 129.3% | 2.66 | +0.88 | -0.88 | +0.88 | 0/10 |
| futures_trend_daily | 13.8% | 1.34 | +0.69 | +0.59 | +0.10 | 6/12 |
| commodity_meanrev_daily | 35.9% | 1.23 | +0.68 | +0.56 | +0.12 | 5/12 |
| rates_daily | 5.5% | 1.24 | +0.21 | +0.09 | +0.12 | 5/12 |
| eq_intraday_15m | 22.2% | 2.60 | +0.92 | -0.00 | -0.00 | 0/10 |
| control_efficient_daily | 20.9% | 0.00 | +0.07 | +0.01 | +0.06 | 1/10 |
| control_martingale_daily | 20.0% | 0.00 | +0.22 | +0.20 | +0.02 | 5/10 |

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
