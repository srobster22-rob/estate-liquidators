# Bot factory: run report

_Generated 2026-08-05 23:55:17 from `run_state.json`._

## Result

**11 distinct strategies passed all eight gates** (15 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes).

960 candidates were screened across 3 generations and 0 search-space expansions; 41 reached the gauntlet; 13,088 backtests were run.

Markets represented: `eq_largecap_daily`, `futures_trend_daily`, `fx_major_daily`.

**Non-stationary families: 0 of 2 produced a certified bot.** `futures_trend_decay_daily`, `eq_largecap_break_daily` are near-clones of the families that certify most readily, differing only in that their edge fades — one halves every 3,000 bars, the other loses 85% of itself on a date. They are searched every generation and their candidates reach the hall of fame on screen score. Nothing surviving there is the point of including them: a lab that certified strategies on a market whose edge has gone would be measuring its own optimism.

**Search-burden headroom.** These were certified after 41 confirmation tests, and G6's luck bar rises with that count — so the count matters as much as the Sharpe. Headroom is the largest search each bot's evidence could have come out of and still clear G6: **15 of 15 genomes clear a bar ten times harder than the one they actually faced** (headroom >=1,073,741,824 down to 9,514). Read it before the Sharpe — a bot whose headroom is close to the tests already run would vanish in a more serious hunt.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 13 | 50% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 12 | 46% | worked only on the instances it was bred on (instance luck) |
| G7-stress-pool | 1 | 4% | failed to replicate a second time on a third pool |

## Proven bots

### `0052362602ca` — futures_trend_daily

```
ma_cross(fast=2,slow=59)x0.72 unanimous momentum(lb=62)x1.33 -> thr 0.13/0.02 both proportional lev<=4.5
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 1 via random
- **search-burden headroom: >=1,073,741,824** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 10. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.45 (need +0.25), 3688 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.60 (need +0.35), 100% of 20 instances positive (need 70%), median DD -33.3% / worst -44.0% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.59 (need +0.25), retained 98% of the early half +0.60 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.05] |
| PASS | G4-stress | 2x costs +0.59 (need +0.15), 3x +0.56 (need +0.00), +1 bar delay +0.60 (need +0.10) |
| PASS | G5-permutation | real +0.58 vs null +0.02+-0.07 (p99 +0.17) -> z=8.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.11 after 10 confirmation tests (would still pass up to >=1,073,741,824); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (320 screened): DSR 1.000 vs SR 0.20, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.56 (need +0.28), 100% positive (need 65%), CAGR +5.7%, median DD -33.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.56 | +0.63 | +5.7% | 9.6% | -33.3% | 0.11 | 24 | 0.22% | 0.60 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.30, `eq_index_daily` +0.11, `futures_trend_decay_daily` +0.08, `rates_daily` +0.07, `fx_em_daily` -0.02, `eq_largecap_break_daily` -0.10

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
  "combine": "unanimous",
  "entry_threshold": 0.132,
  "exit_threshold": 0.024,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.223,
  "target_vol": 0.27,
  "max_leverage": 4.451,
  "rebalance_band": 0.515,
  "atr_n": 29,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": null,
  "dd_resume": 8,
  "bot_id": "0052362602ca",
  "generation": 1,
  "origin": "random",
  "parents": []
}
```

</details>

### `3f24f5df6035` — futures_trend_daily

```
breakout(n=55)x1.00 + momentum(lb=62)x1.33 -> thr 0.90/0.02 both proportional lev<=4.5
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 2 via crossover from 0052362602ca, 90daad4004f7
- **search-burden headroom: >=1,073,741,824** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 18. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.51 (need +0.25), 5232 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.59 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.3% / worst -39.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.64 (need +0.25), retained 108% of the early half +0.60 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.62 (need +0.15), 3x +0.61 (need +0.00), +1 bar delay +0.63 (need +0.10) |
| PASS | G5-permutation | real +0.61 vs null +0.05+-0.06 (p99 +0.18) -> z=8.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.14 after 18 confirmation tests (would still pass up to >=1,073,741,824); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.24, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.60 (need +0.28), 100% positive (need 65%), CAGR +5.4%, median DD -27.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.60 | +0.68 | +5.4% | 8.2% | -27.0% | 0.12 | 34 | 0.12% | 0.43 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.36, `eq_index_daily` +0.16, `rates_daily` +0.11, `futures_trend_decay_daily` +0.09, `fx_em_daily` +0.09, `eq_largecap_break_daily` -0.10

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 55
      },
      "weight": 1.0,
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
  "entry_threshold": 0.9,
  "exit_threshold": 0.024,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.27,
  "max_leverage": 4.451,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "3f24f5df6035",
  "generation": 2,
  "origin": "crossover",
  "parents": [
    "0052362602ca",
    "90daad4004f7"
  ]
}
```

</details>

### `c193adece047` — futures_trend_daily

```
ma_cross(fast=2,slow=59)x0.72 unanimous momentum(lb=62)x1.33 -> thr 0.13/0.02 both fixed lev<=3.2
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 2 via crossover from 0052362602ca, 9ce2c1e65a16
- **search-burden headroom: >=1,073,741,824** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 19. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.42 (need +0.25), 3178 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.55 (need +0.35), 100% of 20 instances positive (need 70%), median DD -28.0% / worst -39.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.61 (need +0.25), retained 108% of the early half +0.56 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.03] |
| PASS | G4-stress | 2x costs +0.55 (need +0.15), 3x +0.53 (need +0.00), +1 bar delay +0.56 (need +0.10) |
| PASS | G5-permutation | real +0.57 vs null +0.04+-0.07 (p99 +0.18) -> z=8.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.14 after 19 confirmation tests (would still pass up to >=1,073,741,824); Bonferroni p 2.11e-15 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.24, p 7.11e-14 |
| PASS | G7-stress-pool | median alphaSR +0.55 (need +0.28), 100% positive (need 65%), CAGR +4.4%, median DD -27.8% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.55 | +0.61 | +4.4% | 7.5% | -27.8% | 0.09 | 20 | 0.17% | 0.49 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.30, `futures_trend_decay_daily` +0.10, `eq_index_daily` +0.10, `rates_daily` +0.04, `fx_em_daily` -0.03, `eq_largecap_break_daily` -0.12

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
  "combine": "unanimous",
  "entry_threshold": 0.132,
  "exit_threshold": 0.024,
  "direction": "both",
  "sizing": "fixed",
  "base_size": 0.588,
  "target_vol": 0.29,
  "max_leverage": 3.249,
  "rebalance_band": 0.149,
  "atr_n": 39,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": null,
  "dd_resume": 5,
  "bot_id": "c193adece047",
  "generation": 2,
  "origin": "crossover",
  "parents": [
    "0052362602ca",
    "9ce2c1e65a16"
  ]
}
```

</details>

### `f65f080835b5` — futures_trend_daily

```
momentum(lb=62)x1.33 -> thr 0.13/0.02 both proportional lev<=4.5
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 2 via mutant from 0052362602ca
- **search-burden headroom: >=1,073,741,824** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 20. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.46 (need +0.25), 5023 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.58 (need +0.35), 100% of 20 instances positive (need 70%), median DD -33.1% / worst -44.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.59 (need +0.25), retained 105% of the early half +0.56 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.08 (allowed 0.30) [control_efficient_daily=-0.08, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.59 (need +0.15), 3x +0.58 (need +0.00), +1 bar delay +0.62 (need +0.10) |
| PASS | G5-permutation | real +0.60 vs null +0.03+-0.07 (p99 +0.19) -> z=8.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.14 after 20 confirmation tests (would still pass up to >=1,073,741,824); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.24, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.56 (need +0.28), 100% positive (need 65%), CAGR +5.9%, median DD -33.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.56 | +0.63 | +5.9% | 9.8% | -33.1% | 0.10 | 31 | 0.19% | 0.64 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.35, `eq_index_daily` +0.15, `futures_trend_decay_daily` +0.14, `rates_daily` +0.11, `fx_em_daily` +0.06, `eq_largecap_break_daily` -0.09

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
  "entry_threshold": 0.132,
  "exit_threshold": 0.024,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.223,
  "target_vol": 0.27,
  "max_leverage": 4.451,
  "rebalance_band": 0.515,
  "atr_n": 29,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": null,
  "dd_resume": 8,
  "bot_id": "f65f080835b5",
  "generation": 2,
  "origin": "mutant",
  "parents": [
    "0052362602ca"
  ]
}
```

</details>

### `9369fc5d6d0c` — fx_major_daily

```
momentum(lb=67)x1.44 + rsi_rev(n=10)x0.60 -> thr 0.11/0.02 both proportional lev<=2.6  [halt@27%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 2 via crossover from a838d255c1ad, 233e7316749b
- **search-burden headroom: 881,803** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 22. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.49 (need +0.25), 7454 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -12.8% / worst -17.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.37 (need +0.25), retained 93% of the early half +0.40 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.07 (allowed 0.30) [control_efficient_daily=-0.07, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.36 (need +0.15), 3x +0.35 (need +0.00), +1 bar delay +0.36 (need +0.10) |
| PASS | G5-permutation | real +0.37 vs null +0.01+-0.06 (p99 +0.16) -> z=6.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.15 after 22 confirmation tests (would still pass up to 881,803); Bonferroni p 1.18e-08 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.24, p 3.43e-07 |
| PASS | G7-stress-pool | median alphaSR +0.36 (need +0.28), 100% positive (need 65%), CAGR +1.0%, median DD -12.7% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.36 | +0.38 | +1.0% | 2.8% | -12.7% | 0.05 | 51 | 0.04% | 0.32 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.58, `eq_index_daily` +0.17, `rates_daily` +0.12, `fx_em_daily` +0.09, `futures_trend_decay_daily` +0.06, `eq_largecap_break_daily` -0.00

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "momentum",
      "params": {
        "lb": 67
      },
      "weight": 1.436,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 0.6,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.108,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.85,
  "target_vol": 0.172,
  "max_leverage": 2.623,
  "rebalance_band": 0.324,
  "atr_n": 21,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.267,
  "dd_resume": 40,
  "bot_id": "9369fc5d6d0c",
  "generation": 2,
  "origin": "crossover",
  "parents": [
    "a838d255c1ad",
    "233e7316749b"
  ]
}
```

</details>

### `ee078efb9e3c` — fx_major_daily

```
momentum(lb=67)x1.44 -> thr 0.11/0.02 both proportional lev<=2.6  [halt@27%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 2 via mutant from a838d255c1ad
- **search-burden headroom: 847,024** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 23. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.43 (need +0.25), 7973 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.41 (need +0.35), 100% of 20 instances positive (need 70%), median DD -18.4% / worst -23.0% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.37 (need +0.25), retained 92% of the early half +0.40 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.36 (need +0.15), 3x +0.35 (need +0.00), +1 bar delay +0.38 (need +0.10) |
| PASS | G5-permutation | real +0.36 vs null +0.02+-0.06 (p99 +0.14) -> z=5.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.15 after 23 confirmation tests (would still pass up to 847,024); Bonferroni p 3.71e-07 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.24, p 1.03e-05 |
| PASS | G7-stress-pool | median alphaSR +0.38 (need +0.28), 100% positive (need 65%), CAGR +1.5%, median DD -18.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.38 | +0.37 | +1.5% | 4.2% | -18.0% | 0.05 | 54 | 0.06% | 0.47 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.62, `eq_index_daily` +0.15, `fx_em_daily` +0.10, `rates_daily` +0.08, `futures_trend_decay_daily` +0.07, `eq_largecap_break_daily` -0.06

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "momentum",
      "params": {
        "lb": 67
      },
      "weight": 1.436,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.108,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.85,
  "target_vol": 0.11,
  "max_leverage": 2.623,
  "rebalance_band": 0.324,
  "atr_n": 21,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.267,
  "dd_resume": 40,
  "bot_id": "ee078efb9e3c",
  "generation": 2,
  "origin": "mutant",
  "parents": [
    "a838d255c1ad"
  ]
}
```

</details>

### `6d352b175ab1` — fx_major_daily

```
ma_cross(fast=42,slow=134)x1.29 vote momentum(lb=67)x1.44 | trend_regime(n=118) -> thr 0.11/0.02 both proportional lev<=0.8  [halt@27%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 2 via crossover from 0ac3bd02597d, a838d255c1ad
- **search-burden headroom: 781,142** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 27. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.43 (need +0.25), 1991 trades, 75% instances positive |
| PASS | G2-replication | median alphaSR +0.38 (need +0.35), 100% of 20 instances positive (need 70%), median DD -22.8% / worst -35.1% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.40 (need +0.25), retained 88% of the early half +0.46 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.04] |
| PASS | G4-stress | 2x costs +0.36 (need +0.15), 3x +0.35 (need +0.00), +1 bar delay +0.36 (need +0.10) |
| PASS | G5-permutation | real +0.37 vs null +0.01+-0.07 (p99 +0.15) -> z=5.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.15 after 27 confirmation tests (would still pass up to 781,142); Bonferroni p 1.73e-06 (need <=0.05) \| stricter all-trials view (640 screened): DSR 1.000 vs SR 0.24, p 4.10e-05 |
| PASS | G7-stress-pool | median alphaSR +0.30 (need +0.28), 95% positive (need 65%), CAGR +1.9%, median DD -24.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.30 | +0.35 | +1.9% | 5.7% | -24.1% | 0.05 | 14 | 0.07% | 0.65 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.60, `eq_index_daily` +0.12, `fx_em_daily` +0.11, `rates_daily` +0.09, `futures_trend_decay_daily` +0.06, `eq_largecap_break_daily` -0.03

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 42,
        "slow": 134
      },
      "weight": 1.291,
      "mode": 1
    },
    {
      "name": "momentum",
      "params": {
        "lb": 67
      },
      "weight": 1.436,
      "mode": 1
    }
  ],
  "filters": [
    {
      "name": "trend_regime",
      "params": {
        "n": 118
      }
    }
  ],
  "combine": "vote",
  "entry_threshold": 0.108,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.85,
  "target_vol": 0.11,
  "max_leverage": 0.814,
  "rebalance_band": 0.324,
  "atr_n": 21,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.267,
  "dd_resume": 40,
  "bot_id": "6d352b175ab1",
  "generation": 2,
  "origin": "crossover",
  "parents": [
    "0ac3bd02597d",
    "a838d255c1ad"
  ]
}
```

</details>

### `39c252b40a36` — eq_largecap_daily

```
bollinger(k=2.14,n=20)x1.00 + rsi_rev(n=10)x0.60 -> thr 0.16/0.03 both proportional lev<=2.0
```

- market: **eq_largecap_daily** (equity, vol 28%, spread 3.0bp, perfect-foresight ceiling SR 1.17)
- found in generation 3 via crossover from 0f8dfb17b6a8, 62155dad7f82
- **search-burden headroom: 656,436** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 30. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.51 (need +0.25), 14318 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -31.3% / worst -39.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.51 (need +0.25), retained 102% of the early half +0.50 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.04] |
| PASS | G4-stress | 2x costs +0.38 (need +0.15), 3x +0.30 (need +0.00), +1 bar delay +0.39 (need +0.10) |
| PASS | G5-permutation | real +0.49 vs null +0.07+-0.06 (p99 +0.21) -> z=6.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 30 confirmation tests (would still pass up to 656,436); Bonferroni p 1.37e-09 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.28, p 4.38e-08 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +3.9%, median DD -29.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.47 | +3.9% | 8.9% | -29.1% | 0.10 | 96 | 0.75% | 0.26 |

Travels to (alphaSR on other families, not a gate): `commodity_meanrev_daily` +0.62, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.06, `rates_daily` -0.02, `fx_em_daily` -0.09, `eq_index_daily` -0.09

<details><summary>genome JSON</summary>

```json
{
  "market": "eq_largecap_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 2.1403,
        "n": 20
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 0.6,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.159,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.172,
  "max_leverage": 2.0,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "39c252b40a36",
  "generation": 3,
  "origin": "crossover",
  "parents": [
    "0f8dfb17b6a8",
    "62155dad7f82"
  ]
}
```

</details>

### `603e03198ba4` — futures_trend_daily

```
breakout(n=55)x1.00 + momentum(lb=62)x1.33 -> thr 0.90/0.02 both proportional lev<=2.6
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 3 via crossover from 3f24f5df6035, ee078efb9e3c
- **search-burden headroom: >=1,073,741,824** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 31. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.51 (need +0.25), 5264 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.59 (need +0.35), 100% of 20 instances positive (need 70%), median DD -27.3% / worst -39.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.64 (need +0.25), retained 107% of the early half +0.60 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.62 (need +0.15), 3x +0.61 (need +0.00), +1 bar delay +0.63 (need +0.10) |
| PASS | G5-permutation | real +0.61 vs null +0.05+-0.06 (p99 +0.19) -> z=8.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 31 confirmation tests (would still pass up to >=1,073,741,824); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.28, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.60 (need +0.28), 100% positive (need 65%), CAGR +5.4%, median DD -27.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.60 | +0.68 | +5.4% | 8.2% | -27.0% | 0.12 | 35 | 0.12% | 0.43 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.36, `eq_index_daily` +0.16, `rates_daily` +0.11, `futures_trend_decay_daily` +0.09, `fx_em_daily` +0.09, `eq_largecap_break_daily` -0.11

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "breakout",
      "params": {
        "n": 55
      },
      "weight": 1.0,
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
  "entry_threshold": 0.9,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.0,
  "target_vol": 0.11,
  "max_leverage": 2.623,
  "rebalance_band": 0.2,
  "atr_n": 20,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": null,
  "dd_resume": 20,
  "bot_id": "603e03198ba4",
  "generation": 3,
  "origin": "crossover",
  "parents": [
    "3f24f5df6035",
    "ee078efb9e3c"
  ]
}
```

</details>

### `a152e340a15b` — futures_trend_daily

```
ma_cross(fast=9,slow=50)x1.03 unanimous momentum(lb=62)x1.33 -> thr 0.13/0.02 both proportional lev<=4.5
```

- market: **futures_trend_daily** (futures, vol 14%, spread 1.5bp, perfect-foresight ceiling SR 1.34)
- found in generation 3 via crossover from dd9c28ab06bd, c8ce6ef6ee0a
- **search-burden headroom: >=1,073,741,824** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 33. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.50 (need +0.25), 3134 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.57 (need +0.35), 100% of 20 instances positive (need 70%), median DD -30.2% / worst -40.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.51 (need +0.25), retained 88% of the early half +0.58 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.04] |
| PASS | G4-stress | 2x costs +0.60 (need +0.15), 3x +0.59 (need +0.00), +1 bar delay +0.61 (need +0.10) |
| PASS | G5-permutation | real +0.61 vs null +0.02+-0.07 (p99 +0.17) -> z=8.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 33 confirmation tests (would still pass up to >=1,073,741,824); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.28, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.58 (need +0.28), 100% positive (need 65%), CAGR +5.5%, median DD -31.6% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.58 | +0.63 | +5.5% | 9.2% | -31.6% | 0.11 | 20 | 0.16% | 0.57 |

Travels to (alphaSR on other families, not a gate): `fx_major_daily` +0.33, `eq_index_daily` +0.12, `futures_trend_decay_daily` +0.12, `rates_daily` +0.07, `fx_em_daily` +0.05, `eq_largecap_break_daily` -0.10

<details><summary>genome JSON</summary>

```json
{
  "market": "futures_trend_daily",
  "genes": [
    {
      "name": "ma_cross",
      "params": {
        "fast": 9,
        "slow": 50
      },
      "weight": 1.027,
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
  "combine": "unanimous",
  "entry_threshold": 0.132,
  "exit_threshold": 0.024,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 1.223,
  "target_vol": 0.27,
  "max_leverage": 4.451,
  "rebalance_band": 0.515,
  "atr_n": 29,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 3,
  "dd_halt": null,
  "dd_resume": 8,
  "bot_id": "a152e340a15b",
  "generation": 3,
  "origin": "crossover",
  "parents": [
    "dd9c28ab06bd",
    "c8ce6ef6ee0a"
  ]
}
```

</details>

### `a32e659543ac` — eq_largecap_daily

```
rsi_rev(n=10)x0.60 -> thr 0.18/0.03 both proportional lev<=1.2  [tp 5.6atr]
```

- market: **eq_largecap_daily** (equity, vol 28%, spread 3.0bp, perfect-foresight ceiling SR 1.17)
- found in generation 3 via mutant from 62155dad7f82
- **search-burden headroom: 47,832** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 34. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.42 (need +0.25), 14550 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -22.6% / worst -33.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.41 (need +0.25), retained 94% of the early half +0.43 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.04] |
| PASS | G4-stress | 2x costs +0.35 (need +0.15), 3x +0.27 (need +0.00), +1 bar delay +0.36 (need +0.10) |
| PASS | G5-permutation | real +0.43 vs null +0.05+-0.06 (p99 +0.17) -> z=6.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 34 confirmation tests (would still pass up to 47,832); Bonferroni p 1.49e-09 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.28, p 4.20e-08 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +2.5%, median DD -20.8% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.42 | +2.5% | 6.5% | -20.8% | 0.08 | 97 | 0.52% | 0.18 |

Travels to (alphaSR on other families, not a gate): `commodity_meanrev_daily` +0.56, `eq_largecap_break_daily` +0.15, `eq_smallcap_daily` -0.01, `rates_daily` -0.04, `eq_index_daily` -0.11, `futures_trend_decay_daily` -0.14

<details><summary>genome JSON</summary>

```json
{
  "market": "eq_largecap_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 0.6,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.176,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.172,
  "max_leverage": 1.221,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": 5.59,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "a32e659543ac",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "62155dad7f82"
  ]
}
```

</details>

### `00485c667557` — eq_largecap_daily

```
bollinger(k=1.69,n=20)x1.00 -> thr 0.50/0.11 long voltarget@17%v lev<=2.0  [halt@29%dd]
```

- market: **eq_largecap_daily** (equity, vol 28%, spread 3.0bp, perfect-foresight ceiling SR 1.17)
- found in generation 3 via mutant from 629426831974
- **search-burden headroom: 642,464** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 35. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.41 (need +0.25), 3562 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.37 (need +0.35), 100% of 20 instances positive (need 70%), median DD -35.0% / worst -52.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.32 (need +0.25), retained 93% of the early half +0.35 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.10 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.10] |
| PASS | G4-stress | 2x costs +0.27 (need +0.15), 3x +0.19 (need +0.00), +1 bar delay +0.33 (need +0.10) |
| PASS | G5-permutation | real +0.39 vs null +0.03+-0.06 (p99 +0.15) -> z=5.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 35 confirmation tests (would still pass up to 642,464); Bonferroni p 2.76e-07 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.28, p 7.57e-06 |
| PASS | G7-stress-pool | median alphaSR +0.30 (need +0.28), 100% positive (need 65%), CAGR +4.4%, median DD -34.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.30 | +0.43 | +4.4% | 11.4% | -34.4% | 0.07 | 24 | 0.78% | 0.27 |

Travels to (alphaSR on other families, not a gate): `commodity_meanrev_daily` +0.46, `eq_largecap_break_daily` +0.15, `rates_daily` -0.09, `eq_index_daily` -0.15, `eq_smallcap_daily` -0.17, `futures_trend_decay_daily` -0.17

<details><summary>genome JSON</summary>

```json
{
  "market": "eq_largecap_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.6902,
        "n": 20
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.5,
  "exit_threshold": 0.113,
  "direction": "long",
  "sizing": "voltarget",
  "base_size": 1.786,
  "target_vol": 0.172,
  "max_leverage": 2.0,
  "rebalance_band": 0.135,
  "atr_n": 38,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 1,
  "dd_halt": 0.293,
  "dd_resume": 76,
  "bot_id": "00485c667557",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "629426831974"
  ]
}
```

</details>

### `d51433a515c8` — fx_major_daily

```
bollinger(k=2.74,n=16)x1.10 + momentum(lb=67)x1.44 -> thr 0.11/0.02 both proportional lev<=2.6  [stop 2.2atr, halt@27%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 3 via mutant from ee078efb9e3c
- **search-burden headroom: 9,514** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 36. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.31 (need +0.25), 8658 trades, 75% instances positive |
| PASS | G2-replication | median alphaSR +0.37 (need +0.35), 100% of 20 instances positive (need 70%), median DD -8.1% / worst -14.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.37 (need +0.25), retained 113% of the early half +0.32 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.04] |
| PASS | G4-stress | 2x costs +0.31 (need +0.15), 3x +0.29 (need +0.00), +1 bar delay +0.36 (need +0.10) |
| PASS | G5-permutation | real +0.31 vs null -0.01+-0.07 (p99 +0.12) -> z=4.9, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.18 after 36 confirmation tests (would still pass up to 9,514); Bonferroni p 1.67e-05 (need <=0.05) \| stricter all-trials view (960 screened): DSR 0.999 vs SR 0.28, p 4.45e-04 |
| PASS | G7-stress-pool | median alphaSR +0.35 (need +0.28), 95% positive (need 65%), CAGR +0.6%, median DD -9.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.35 | +0.33 | +0.6% | 2.0% | -9.3% | 0.05 | 61 | 0.05% | 0.19 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.50, `eq_index_daily` +0.16, `rates_daily` +0.12, `fx_em_daily` +0.10, `eq_largecap_daily` +0.03, `eq_largecap_break_daily` +0.02

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 2.7354,
        "n": 16
      },
      "weight": 1.105,
      "mode": 1
    },
    {
      "name": "momentum",
      "params": {
        "lb": 67
      },
      "weight": 1.436,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.108,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.85,
  "target_vol": 0.11,
  "max_leverage": 2.623,
  "rebalance_band": 0.324,
  "atr_n": 21,
  "stop_atr": 2.2,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.267,
  "dd_resume": 40,
  "bot_id": "d51433a515c8",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "ee078efb9e3c"
  ]
}
```

</details>

### `b3c01f89fcbf` — fx_major_daily

```
momentum(lb=71)x1.44 + rsi_rev(n=10)x0.60 -> thr 0.11/0.02 both proportional lev<=2.6  [halt@27%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 3 via mutant from 9369fc5d6d0c
- **search-burden headroom: 199,473** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 37. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.44 (need +0.25), 7398 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.45 (need +0.35), 95% of 20 instances positive (need 70%), median DD -12.4% / worst -20.3% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.43 (need +0.25), retained 99% of the early half +0.43 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.07 (allowed 0.30) [control_efficient_daily=-0.07, control_martingale_daily=-0.03] |
| PASS | G4-stress | 2x costs +0.37 (need +0.15), 3x +0.36 (need +0.00), +1 bar delay +0.38 (need +0.10) |
| PASS | G5-permutation | real +0.37 vs null +0.01+-0.07 (p99 +0.16) -> z=5.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.19 after 37 confirmation tests (would still pass up to 199,473); Bonferroni p 1.12e-06 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.28, p 2.91e-05 |
| PASS | G7-stress-pool | median alphaSR +0.34 (need +0.28), 95% positive (need 65%), CAGR +1.0%, median DD -13.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.34 | +0.38 | +1.0% | 2.9% | -13.0% | 0.05 | 50 | 0.04% | 0.32 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.61, `eq_index_daily` +0.17, `rates_daily` +0.15, `fx_em_daily` +0.11, `futures_trend_decay_daily` +0.02, `eq_largecap_break_daily` -0.02

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "momentum",
      "params": {
        "lb": 71
      },
      "weight": 1.436,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 0.6,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.108,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.85,
  "target_vol": 0.172,
  "max_leverage": 2.623,
  "rebalance_band": 0.324,
  "atr_n": 21,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.267,
  "dd_resume": 40,
  "bot_id": "b3c01f89fcbf",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "9369fc5d6d0c"
  ]
}
```

</details>

### `8a2eeb4f2b10` — fx_major_daily

```
momentum(lb=47)x1.44 -> thr 0.11/0.02 both proportional lev<=2.6  [halt@27%dd]
```

- market: **fx_major_daily** (fx, vol 8%, spread 0.8bp, perfect-foresight ceiling SR 1.79)
- found in generation 3 via mutant from 9369fc5d6d0c
- **search-burden headroom: 26,962** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 38. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.48 (need +0.25), 9112 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.39 (need +0.35), 100% of 20 instances positive (need 70%), median DD -15.9% / worst -25.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.38 (need +0.25), retained 100% of the early half +0.38 (need 50%) |
| PASS | G3-controls | worst \|alphaSR\| 0.07 (allowed 0.30) [control_efficient_daily=+0.00, control_martingale_daily=-0.07] |
| PASS | G4-stress | 2x costs +0.35 (need +0.15), 3x +0.33 (need +0.00), +1 bar delay +0.37 (need +0.10) |
| PASS | G5-permutation | real +0.36 vs null +0.00+-0.06 (p99 +0.14) -> z=5.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.19 after 38 confirmation tests (would still pass up to 26,962); Bonferroni p 5.70e-07 (need <=0.05) \| stricter all-trials view (960 screened): DSR 1.000 vs SR 0.28, p 1.44e-05 |
| PASS | G7-stress-pool | median alphaSR +0.33 (need +0.28), 100% positive (need 65%), CAGR +1.2%, median DD -19.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.33 | +0.32 | +1.2% | 4.1% | -19.3% | 0.04 | 63 | 0.08% | 0.47 |

Travels to (alphaSR on other families, not a gate): `futures_trend_daily` +0.58, `futures_trend_decay_daily` +0.15, `rates_daily` +0.09, `eq_index_daily` +0.07, `fx_em_daily` +0.04, `eq_largecap_break_daily` -0.11

<details><summary>genome JSON</summary>

```json
{
  "market": "fx_major_daily",
  "genes": [
    {
      "name": "momentum",
      "params": {
        "lb": 47
      },
      "weight": 1.436,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.108,
  "exit_threshold": 0.02,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.85,
  "target_vol": 0.172,
  "max_leverage": 2.623,
  "rebalance_band": 0.324,
  "atr_n": 21,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 2,
  "dd_halt": 0.267,
  "dd_resume": 40,
  "bot_id": "8a2eeb4f2b10",
  "generation": 3,
  "origin": "mutant",
  "parents": [
    "9369fc5d6d0c"
  ]
}
```

</details>

## Portfolio

```
11 distinct strategies across 3 market(s) / 3 asset class(es)   [from 15 proven genomes]
  best single bot        alphaSR +0.62
  portfolio (lab, rho=0) alphaSR +0.93   <- upper bound, independent synthetic markets
  portfolio (rho=0.3)    alphaSR +0.69   <- plan with this one
     5.0%  0052362602ca  futures_trend_daily      alphaSR +0.57
     5.8%  3f24f5df6035  futures_trend_daily      alphaSR +0.62
     6.4%  c193adece047  futures_trend_daily      alphaSR +0.55
     4.9%  f65f080835b5  futures_trend_daily      alphaSR +0.57
    16.6%  9369fc5d6d0c  fx_major_daily           alphaSR +0.37
    11.4%  ee078efb9e3c  fx_major_daily           alphaSR +0.36
     8.3%  6d352b175ab1  fx_major_daily           alphaSR +0.33
     5.3%  39c252b40a36  eq_largecap_daily        alphaSR +0.48
     7.3%  a32e659543ac  eq_largecap_daily        alphaSR +0.43
     5.1%  00485c667557  eq_largecap_daily        alphaSR +0.34
    23.7%  d51433a515c8  fx_major_daily           alphaSR +0.32
```

The two portfolio numbers differ because this lab generates each market family independently, so cross-family correlation is structurally zero — an assumption real asset classes violate exactly when it matters. Plan with the rho=0.3 number.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `39c252b40a36` | eq_largecap_daily | +0.50 | +0.56 | 65738 | `bollinger(k=2.14,n=20)x1.00 + rsi_rev(n=10)x0.60 -> thr 0.16/0.03 ` |
| `0426ad79d716` | eq_largecap_daily | +0.47 | +0.56 | 39463 | `bollinger(k=2.14,n=20)x1.00 + rsi_rev(n=13)x1.50 -> thr 0.50/0.03 ` |
| `3f24f5df6035` | futures_trend_daily | +0.47 | +0.57 | 23023 | `breakout(n=55)x1.00 + momentum(lb=62)x1.33 -> thr 0.90/0.02 both p` |
| `603e03198ba4` | futures_trend_daily | +0.47 | +0.57 | 23156 | `breakout(n=55)x1.00 + momentum(lb=62)x1.33 -> thr 0.90/0.02 both p` |
| `461de2beffb2` | futures_trend_daily | +0.46 | +0.54 | 17223 | `momentum(lb=87)x1.33 -> thr 0.13/0.02 both proportional lev<=4.5` |
| `a152e340a15b` | futures_trend_daily | +0.46 | +0.57 | 13205 | `ma_cross(fast=9,slow=50)x1.03 unanimous momentum(lb=62)x1.33 -> th` |
| `c193adece047` | futures_trend_daily | +0.46 | +0.55 | 13500 | `ma_cross(fast=2,slow=59)x0.72 unanimous momentum(lb=62)x1.33 -> th` |
| `6ff4177ed563` | futures_trend_daily | +0.46 | +0.54 | 20820 | `momentum(lb=62)x1.33 -> thr 0.13/0.02 both proportional lev<=4.5  ` |
| `a32e659543ac` | eq_largecap_daily | +0.45 | +0.47 | 66074 | `rsi_rev(n=10)x0.60 -> thr 0.18/0.03 both proportional lev<=1.2  [t` |
| `bdb03bc5f680` | futures_trend_daily | +0.45 | +0.54 | 11310 | `ma_cross(fast=2,slow=59)x0.72 unanimous momentum(lb=120)x1.33 -> t` |
| `629d6fad1f31` | eq_largecap_daily | +0.44 | +0.57 | 59745 | `rsi_rev(n=14)x0.91 -> thr 0.24/0.11 both proportional lev<=2.0  [h` |
| `af8621272661` | futures_trend_daily | +0.43 | +0.56 | 11123 | `ma_cross(fast=8,slow=129)x0.74 unanimous momentum(lb=62)x1.33 -> t` |
| `3aa03f1ff4d0` | futures_trend_daily | +0.43 | +0.50 | 15443 | `ma_cross(fast=20,slow=93)x1.00 \| trend_regime(n=145) -> thr 0.04/0` |
| `684a01263237` | futures_trend_daily | +0.43 | +0.56 | 55132 | `breakout(n=94)x1.00 + ma_cross(fast=2,slow=59)x0.72 -> thr 0.13/0.` |
| `00485c667557` | eq_largecap_daily | +0.41 | +0.46 | 16090 | `bollinger(k=1.69,n=20)x1.00 -> thr 0.50/0.11 long voltarget@17%v l` |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 320 | 7 | 17 | 9 | 1 | +0.41 | 49s |
| 2 | 1 | 320 | 7 | 12 | 0 | 6 | +0.47 | 44s |
| 3 | 1 | 320 | 7 | 12 | 0 | 8 | +0.50 | 44s |

## Market calibration

`ceiling` is the perfect-foresight Sharpe bound implied by the planted structure; `gross`/`net` are the best textbook archetype without and with costs. A family whose net number is negative is a market where the honest answer is *don't trade this*.

The two `control_*` rows show a positive net number (~+0.3) and that is expected, not a contradiction: it is the **maximum over 13 archetypes of a median over 6 instances**, which is a selection statistic, and on 12 years of daily data its null spread is about that size. The point of the controls is not that no single statistic on them is ever positive — it is that nothing survives *replication* on them, which is what the gauntlet tests and what `run.py fpr` measures end to end (0 certified from 3,000 candidates).

| family | vol | ceiling SR | gross alphaSR | net alphaSR | cost bite | archetypes net + |
|---|---|---|---|---|---|---|
| eq_index_daily | 16.3% | 1.45 | +0.27 | +0.13 | +0.13 | 4/10 |
| eq_largecap_daily | 29.1% | 1.17 | +0.62 | +0.51 | +0.11 | 4/10 |
| eq_smallcap_daily | 46.0% | 1.85 | +0.65 | +0.00 | -0.00 | 1/10 |
| fx_major_daily | 8.3% | 1.79 | +0.49 | +0.31 | +0.18 | 6/12 |
| fx_em_daily | 13.8% | 1.45 | +0.31 | +0.12 | +0.19 | 4/12 |
| crypto_major_hourly | 58.4% | 2.57 | +0.98 | -0.75 | +0.74 | 0/10 |
| crypto_alt_hourly | 110.5% | 2.66 | +1.39 | -0.95 | +0.95 | 0/10 |
| futures_trend_daily | 13.9% | 1.34 | +0.51 | +0.43 | +0.08 | 7/12 |
| commodity_meanrev_daily | 35.7% | 1.23 | +0.67 | +0.53 | +0.14 | 4/12 |
| rates_daily | 5.5% | 1.24 | +0.40 | +0.26 | +0.14 | 8/12 |
| eq_intraday_15m | 21.9% | 2.60 | +1.11 | -0.00 | -0.00 | 0/10 |
| futures_trend_decay_daily | 13.6% | 0.54 | +0.08 | +0.00 | -0.00 | 2/12 |
| eq_largecap_break_daily | 29.2% | 0.62 | +0.29 | +0.22 | +0.06 | 5/10 |
| control_efficient_daily | 20.5% | 0.00 | +0.12 | +0.08 | +0.04 | 4/10 |
| control_martingale_daily | 20.0% | 0.00 | +0.09 | +0.07 | +0.02 | 6/10 |

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
