# Bot factory: run report

_Generated 2026-08-06 05:14:58 from `run_state.json`._

## Result

**4 distinct strategies passed all eight gates** (30 genomes — several are the same rule at a different threshold or gene weight, which is why the headline counts structures rather than genomes).

12,400 candidates were screened across 19 generations and 2 search-space expansions; 353 reached the gauntlet; 29,049 backtests were run.

Markets represented: `commodity_meanrev_daily`, `eq_largecap_daily`.

**Every tradeable family's edge decays** — halflife half the series with a 35% floor by default, so the average edge across an instance is 70% of its opening value. A catalogue identical at the last bar and the first flatters everything tested on it.

The certified bots retain **60%-84%** of their first-half alpha in the second half. For scale, a textbook trend bot on a decaying trend market retains 11% — costs are fixed, so a 30% cut in gross edge takes ~90% of net alpha, and strategies running close to their cost floor die first. What survives decay is what had margin over costs to begin with.

None of the 2 families that decay *faster* than the default (`futures_trend_decay_daily`, `eq_largecap_break_daily`) certified anything.

**Search-burden headroom.** These were certified after 353 confirmation tests, and G6's luck bar rises with that count — so the count matters as much as the Sharpe. Headroom is the largest search each bot's evidence could have come out of and still clear G6: **27 of 30 genomes clear a bar ten times harder than the one they actually faced** (headroom 12,019,039 down to 229). Read it before the Sharpe — a bot whose headroom is close to the tests already run would vanish in a more serious hunt.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 296 | 92% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 21 | 7% | worked only on the instances it was bred on (instance luck) |
| G2b-durability | 2 | 1% | edge faded across the series (a crowded or arbitraged anomaly) |
| G4-stress | 1 | 0% | edge smaller than 2x costs or one bar of delay |
| G6-multiplicity | 3 | 1% | not surprising given how many candidates were tried |

## Proven bots

### `44504d663841` — commodity_meanrev_daily

```
rsi_rev(n=13)x1.24 + rsi_rev(n=8)x1.35 -> thr 0.30/0.03 both proportional lev<=2.0  [stop 5.1atr]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 6 via transplant from a9c6b78feffc
- **search-burden headroom: 147,460** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 82. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.47 (need +0.25), 10591 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.42 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.7% / worst -44.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.36 (need +0.25) vs early half +0.48, retained 74% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=-0.05] |
| PASS | G4-stress | 2x costs +0.34 (need +0.15), 3x +0.25 (need +0.00), +1 bar delay +0.37 (need +0.10) |
| PASS | G5-permutation | real +0.42 vs null +0.04+-0.06 (p99 +0.16) -> z=6.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.21 after 82 confirmation tests (would still pass up to 147,460); Bonferroni p 2.90e-08 (need <=0.05) \| stricter all-trials view (3040 screened): DSR 1.000 vs SR 0.30, p 1.08e-06 |
| PASS | G7-stress-pool | median alphaSR +0.40 (need +0.28), 100% positive (need 65%), CAGR +2.5%, median DD -21.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.40 | +0.40 | +2.5% | 6.7% | -21.1% | 0.07 | 70 | 0.60% | 0.14 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.29, `eq_largecap_break_daily` +0.20, `eq_index_daily` +0.00, `rates_daily` -0.02, `fx_major_daily` -0.05, `eq_smallcap_daily` -0.10

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
      "weight": 1.2373,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 8
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.3,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.138,
  "max_leverage": 2.0,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": 5.12,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "44504d663841",
  "generation": 6,
  "origin": "transplant",
  "parents": [
    "a9c6b78feffc"
  ]
}
```

</details>

### `8eb8425dceaf` — commodity_meanrev_daily

```
bollinger(k=1.99,n=84)x0.60 + rsi_rev(n=16)x1.35 -> thr 0.21/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 7 via mutant from e4c4f52e3585
- **search-burden headroom: 12,019,039** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 98. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.26 (need +0.25), 13001 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.51 (need +0.35), 100% of 20 instances positive (need 70%), median DD -25.2% / worst -39.3% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.41 (need +0.25) vs early half +0.64, retained 63% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.47 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.03+-0.06 (p99 +0.13) -> z=7.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 98 confirmation tests (would still pass up to 12,019,039); Bonferroni p 6.31e-13 (need <=0.05) \| stricter all-trials view (3760 screened): DSR 1.000 vs SR 0.31, p 2.42e-11 |
| PASS | G7-stress-pool | median alphaSR +0.46 (need +0.28), 100% positive (need 65%), CAGR +3.6%, median DD -27.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.46 | +0.44 | +3.6% | 8.8% | -27.1% | 0.07 | 89 | 0.52% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.09, `eq_index_daily` -0.01, `rates_daily` -0.01, `fx_em_daily` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9888,
        "n": 84
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.214,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.12,
  "max_leverage": 1.704,
  "rebalance_band": 0.2627,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "8eb8425dceaf",
  "generation": 7,
  "origin": "mutant",
  "parents": [
    "e4c4f52e3585"
  ]
}
```

</details>

### `48b28580e889` — commodity_meanrev_daily

```
rsi_rev(n=28)x1.35 + rsi_rev(n=9)x1.00 -> thr 0.30/0.05 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 8 via mutant from a8ca308ca0cb
- **search-burden headroom: 683,212** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 118. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.29 (need +0.25), 7073 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.48 (need +0.35), 100% of 20 instances positive (need 70%), median DD -17.8% / worst -29.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.55, retained 70% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.41 (need +0.15), 3x +0.36 (need +0.00), +1 bar delay +0.42 (need +0.10) |
| PASS | G5-permutation | real +0.45 vs null +0.02+-0.06 (p99 +0.18) -> z=6.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 118 confirmation tests (would still pass up to 683,212); Bonferroni p 1.32e-09 (need <=0.05) \| stricter all-trials view (4480 screened): DSR 1.000 vs SR 0.32, p 4.99e-08 |
| PASS | G7-stress-pool | median alphaSR +0.45 (need +0.28), 100% positive (need 65%), CAGR +2.1%, median DD -18.9% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.45 | +0.42 | +2.1% | 5.4% | -18.9% | 0.05 | 47 | 0.31% | 0.10 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.33, `eq_largecap_break_daily` +0.17, `eq_smallcap_daily` +0.09, `rates_daily` -0.01, `eq_index_daily` -0.02, `fx_major_daily` -0.08

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 28
      },
      "weight": 1.3532,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 9
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.3,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.15,
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
  "bot_id": "48b28580e889",
  "generation": 8,
  "origin": "mutant",
  "parents": [
    "a8ca308ca0cb"
  ]
}
```

</details>

### `deee71301b5f` — commodity_meanrev_daily

```
bollinger(k=1.99,n=84)x0.60 + rsi_rev(n=16)x1.35 -> thr 0.21/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 8 via mutant from 8eb8425dceaf
- **search-burden headroom: 8,287,751** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 119. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.26 (need +0.25), 13570 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.51 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.5% / worst -40.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.40 (need +0.25) vs early half +0.63, retained 63% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.47 (need +0.10) |
| PASS | G5-permutation | real +0.52 vs null +0.05+-0.06 (p99 +0.18) -> z=8.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.22 after 119 confirmation tests (would still pass up to 8,287,751); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (4480 screened): DSR 1.000 vs SR 0.32, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.46 (need +0.28), 100% positive (need 65%), CAGR +3.6%, median DD -27.6% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.46 | +0.44 | +3.6% | 8.8% | -27.6% | 0.06 | 93 | 0.53% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.09, `eq_index_daily` -0.01, `rates_daily` -0.02, `fx_em_daily` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9888,
        "n": 84
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.214,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.12,
  "max_leverage": 1.704,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "deee71301b5f",
  "generation": 8,
  "origin": "mutant",
  "parents": [
    "8eb8425dceaf"
  ]
}
```

</details>

### `7474113c038d` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.35 -> thr 0.21/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 9 via mutant from deee71301b5f
- **search-burden headroom: 5,813,962** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 138. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.26 (need +0.25), 13655 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.51 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.7% / worst -43.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.40 (need +0.25) vs early half +0.64, retained 62% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.43 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.04+-0.06 (p99 +0.17) -> z=8.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.23 after 138 confirmation tests (would still pass up to 5,813,962); Bonferroni p 3.06e-14 (need <=0.05) \| stricter all-trials view (5200 screened): DSR 1.000 vs SR 0.32, p 1.15e-12 |
| PASS | G7-stress-pool | median alphaSR +0.46 (need +0.28), 100% positive (need 65%), CAGR +3.7%, median DD -27.7% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.46 | +0.45 | +3.7% | 9.0% | -27.7% | 0.07 | 94 | 0.55% | 0.19 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.08, `eq_index_daily` -0.00, `rates_daily` -0.01, `fx_em_daily` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.214,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.12,
  "max_leverage": 1.704,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "7474113c038d",
  "generation": 9,
  "origin": "mutant",
  "parents": [
    "deee71301b5f"
  ]
}
```

</details>

### `a07e6aa7fed5` — commodity_meanrev_daily

```
rsi_rev(n=12)x0.91 + rsi_rev(n=16)x1.35 -> thr 0.30/0.03 both proportional lev<=1.5
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 9 via mutant from b6beb7fb85f0
- **search-burden headroom: 1,665,995** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 139. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.35 (need +0.25), 7812 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -18.8% / worst -31.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.60, retained 65% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.00] |
| PASS | G4-stress | 2x costs +0.40 (need +0.15), 3x +0.35 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | real +0.45 vs null +0.03+-0.06 (p99 +0.16) -> z=6.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.23 after 139 confirmation tests (would still pass up to 1,665,995); Bonferroni p 1.60e-09 (need <=0.05) \| stricter all-trials view (5200 screened): DSR 1.000 vs SR 0.32, p 5.99e-08 |
| PASS | G7-stress-pool | median alphaSR +0.46 (need +0.28), 100% positive (need 65%), CAGR +2.6%, median DD -22.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.46 | +0.43 | +2.6% | 6.5% | -22.1% | 0.07 | 52 | 0.35% | 0.13 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.35, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.09, `rates_daily` +0.00, `eq_index_daily` -0.02, `fx_em_daily` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 12
      },
      "weight": 0.913,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.3,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2314,
  "max_leverage": 1.5,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "a07e6aa7fed5",
  "generation": 9,
  "origin": "mutant",
  "parents": [
    "b6beb7fb85f0"
  ]
}
```

</details>

### `c862cbf498ea` — commodity_meanrev_daily

```
rsi_rev(n=13)x1.00 + rsi_rev(n=28)x1.35 -> thr 0.30/0.05 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 10 via mutant from 48b28580e889
- **search-burden headroom: 257,195** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 158. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.31 (need +0.25), 5266 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.46 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.0% / worst -29.6% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.54, retained 73% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=+0.01] |
| PASS | G4-stress | 2x costs +0.42 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | real +0.48 vs null +0.03+-0.06 (p99 +0.14) -> z=7.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.24 after 158 confirmation tests (would still pass up to 257,195); Bonferroni p 1.00e-11 (need <=0.05) \| stricter all-trials view (5920 screened): DSR 1.000 vs SR 0.33, p 3.75e-10 |
| PASS | G7-stress-pool | median alphaSR +0.42 (need +0.28), 100% positive (need 65%), CAGR +2.0%, median DD -18.1% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.42 | +0.42 | +2.0% | 5.1% | -18.1% | 0.05 | 34 | 0.20% | 0.09 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_intraday_15m` +0.22, `eq_smallcap_daily` +0.17, `eq_largecap_break_daily` +0.14, `eq_index_daily` -0.02, `rates_daily` -0.02

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
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 28
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.3,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.15,
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
  "bot_id": "c862cbf498ea",
  "generation": 10,
  "origin": "mutant",
  "parents": [
    "48b28580e889"
  ]
}
```

</details>

### `a63d754afd3f` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.35 -> thr 0.21/0.03 both proportional lev<=1.7  [tp 4.9atr]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 10 via mutant from 7474113c038d
- **search-burden headroom: 3,109,253** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 159. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.26 (need +0.25), 13676 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.51 (need +0.35), 100% of 20 instances positive (need 70%), median DD -25.2% / worst -43.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.64, retained 61% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.43 (need +0.15), 3x +0.37 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | real +0.50 vs null +0.02+-0.07 (p99 +0.15) -> z=7.3, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.24 after 159 confirmation tests (would still pass up to 3,109,253); Bonferroni p 2.67e-11 (need <=0.05) \| stricter all-trials view (5920 screened): DSR 1.000 vs SR 0.33, p 9.92e-10 |
| PASS | G7-stress-pool | median alphaSR +0.45 (need +0.28), 100% positive (need 65%), CAGR +3.6%, median DD -27.7% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.45 | +0.45 | +3.6% | 8.9% | -27.7% | 0.07 | 94 | 0.55% | 0.19 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.08, `eq_index_daily` +0.00, `rates_daily` -0.01, `fx_em_daily` -0.07

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.214,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.12,
  "max_leverage": 1.704,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": 4.88,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "a63d754afd3f",
  "generation": 10,
  "origin": "mutant",
  "parents": [
    "7474113c038d"
  ]
}
```

</details>

### `869724b2bed1` — commodity_meanrev_daily

```
rsi_rev(n=10)x1.00 + rsi_rev(n=28)x1.35 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 11 via mutant from 05659aa4ac6a
- **search-burden headroom: 250,743** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 178. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.33 (need +0.25), 7302 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.46 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.3% / worst -33.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.41 (need +0.25) vs early half +0.49, retained 84% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.41 (need +0.15), 3x +0.35 (need +0.00), +1 bar delay +0.42 (need +0.10) |
| PASS | G5-permutation | real +0.47 vs null +0.02+-0.07 (p99 +0.17) -> z=6.0, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.25 after 178 confirmation tests (would still pass up to 250,743); Bonferroni p 1.30e-07 (need <=0.05) \| stricter all-trials view (6640 screened): DSR 1.000 vs SR 0.34, p 4.86e-06 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +2.2%, median DD -18.5% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.42 | +2.2% | 5.4% | -18.5% | 0.06 | 48 | 0.28% | 0.10 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.35, `eq_largecap_break_daily` +0.17, `eq_smallcap_daily` +0.09, `eq_index_daily` +0.00, `rates_daily` -0.01, `eq_intraday_15m` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 28
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2314,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "869724b2bed1",
  "generation": 11,
  "origin": "mutant",
  "parents": [
    "05659aa4ac6a"
  ]
}
```

</details>

### `c860219fc8e1` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.35 -> thr 0.28/0.03 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 11 via crossover from 7474113c038d, 43f4ebad86e7
- **search-burden headroom: 2,068,378** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 179. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 11987 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.5% / worst -41.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.63, retained 62% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.47 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.04+-0.05 (p99 +0.15) -> z=9.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.25 after 179 confirmation tests (would still pass up to 2,068,378); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (6640 screened): DSR 1.000 vs SR 0.34, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +3.7%, median DD -29.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.45 | +3.7% | 8.9% | -29.0% | 0.06 | 82 | 0.52% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.10, `rates_daily` +0.00, `eq_index_daily` -0.01, `fx_em_daily` -0.03

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 2.0,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "c860219fc8e1",
  "generation": 11,
  "origin": "crossover",
  "parents": [
    "7474113c038d",
    "43f4ebad86e7"
  ]
}
```

</details>

### `03f9c3730fce` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.35 -> thr 0.28/0.03 both proportional lev<=2.0  [tp 6.1atr]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 12 via mutant from c860219fc8e1
- **search-burden headroom: 1,440,041** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 198. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.26 (need +0.25), 11992 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.51 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.5% / worst -41.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.63, retained 61% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.03+-0.06 (p99 +0.17) -> z=7.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.25 after 198 confirmation tests (would still pass up to 1,440,041); Bonferroni p 9.45e-13 (need <=0.05) \| stricter all-trials view (7360 screened): DSR 1.000 vs SR 0.35, p 3.51e-11 |
| PASS | G7-stress-pool | median alphaSR +0.46 (need +0.28), 100% positive (need 65%), CAGR +3.6%, median DD -29.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.46 | +0.44 | +3.6% | 8.9% | -29.0% | 0.06 | 82 | 0.51% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.09, `rates_daily` +0.00, `eq_index_daily` -0.01, `fx_em_daily` -0.04

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.1856,
  "max_leverage": 2.0,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": 6.1,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "03f9c3730fce",
  "generation": 12,
  "origin": "mutant",
  "parents": [
    "c860219fc8e1"
  ]
}
```

</details>

### `b83cba13320a` — commodity_meanrev_daily

```
rsi_rev(n=11)x1.00 + rsi_rev(n=28)x1.35 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 12 via mutant from 869724b2bed1
- **search-burden headroom: 263,476** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 199. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.30 (need +0.25), 6803 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.48 (need +0.35), 100% of 20 instances positive (need 70%), median DD -15.7% / worst -27.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.53, retained 73% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=-0.00] |
| PASS | G4-stress | 2x costs +0.41 (need +0.15), 3x +0.37 (need +0.00), +1 bar delay +0.42 (need +0.10) |
| PASS | G5-permutation | real +0.47 vs null +0.03+-0.07 (p99 +0.15) -> z=6.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.25 after 199 confirmation tests (would still pass up to 263,476); Bonferroni p 1.21e-09 (need <=0.05) \| stricter all-trials view (7360 screened): DSR 1.000 vs SR 0.35, p 4.48e-08 |
| PASS | G7-stress-pool | median alphaSR +0.46 (need +0.28), 100% positive (need 65%), CAGR +2.1%, median DD -17.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.46 | +0.42 | +2.1% | 5.3% | -17.3% | 0.05 | 44 | 0.25% | 0.10 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.34, `eq_largecap_break_daily` +0.15, `eq_smallcap_daily` +0.11, `eq_intraday_15m` +0.02, `rates_daily` -0.00, `eq_index_daily` -0.01

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
        "n": 28
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2314,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "b83cba13320a",
  "generation": 12,
  "origin": "mutant",
  "parents": [
    "869724b2bed1"
  ]
}
```

</details>

### `31945cb3bd26` — commodity_meanrev_daily

```
rsi_rev(n=16)x1.35 + rsi_rev(n=28)x1.35 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 13 via crossover from 3425c77257d8, d4899bf20b6e
- **search-burden headroom: 76,591** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 217. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 5462 trades, 75% instances positive |
| PASS | G2-replication | median alphaSR +0.45 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.7% / worst -27.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.38 (need +0.25) vs early half +0.55, retained 68% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.40 (need +0.15), 3x +0.37 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | real +0.48 vs null +0.03+-0.06 (p99 +0.17) -> z=7.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.26 after 217 confirmation tests (would still pass up to 76,591); Bonferroni p 5.31e-11 (need <=0.05) \| stricter all-trials view (8080 screened): DSR 0.999 vs SR 0.35, p 1.98e-09 |
| PASS | G7-stress-pool | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +2.0%, median DD -18.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.41 | +2.0% | 5.1% | -18.0% | 0.06 | 36 | 0.19% | 0.09 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_intraday_15m` +0.20, `eq_largecap_break_daily` +0.16, `eq_smallcap_daily` +0.16, `rates_daily` +0.02, `eq_index_daily` -0.03

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 28
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2314,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "31945cb3bd26",
  "generation": 13,
  "origin": "crossover",
  "parents": [
    "3425c77257d8",
    "d4899bf20b6e"
  ]
}
```

</details>

### `c8879b484663` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.35 -> thr 0.28/0.03 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 13 via crossover from c860219fc8e1, 03f9c3730fce
- **search-burden headroom: 1,077,347** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 218. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 11987 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.5% / worst -41.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.63, retained 62% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.47 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.04+-0.07 (p99 +0.20) -> z=6.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.26 after 218 confirmation tests (would still pass up to 1,077,347); Bonferroni p 7.03e-09 (need <=0.05) \| stricter all-trials view (8080 screened): DSR 1.000 vs SR 0.35, p 2.61e-07 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +3.7%, median DD -29.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.45 | +3.7% | 8.9% | -29.0% | 0.06 | 82 | 0.52% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.10, `rates_daily` +0.00, `eq_index_daily` -0.01, `fx_em_daily` -0.03

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.1856,
  "max_leverage": 2.0,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "c8879b484663",
  "generation": 13,
  "origin": "crossover",
  "parents": [
    "c860219fc8e1",
    "03f9c3730fce"
  ]
}
```

</details>

### `0642136ed2e1` — commodity_meanrev_daily

```
rsi_rev(n=13)x0.50 -> thr 0.30/0.03 both proportional lev<=1.4
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 13 via mutant from cc8cacb4d3e9
- **search-burden headroom: 59,777** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 219. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.32 (need +0.25), 15211 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.46 (need +0.35), 100% of 20 instances positive (need 70%), median DD -23.1% / worst -38.0% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.39 (need +0.25) vs early half +0.54, retained 73% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.35 (need +0.15), 3x +0.28 (need +0.00), +1 bar delay +0.38 (need +0.10) |
| PASS | G5-permutation | real +0.41 vs null -0.00+-0.06 (p99 +0.14) -> z=6.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.26 after 219 confirmation tests (would still pass up to 59,777); Bonferroni p 1.05e-08 (need <=0.05) \| stricter all-trials view (8080 screened): DSR 0.999 vs SR 0.35, p 3.87e-07 |
| PASS | G7-stress-pool | median alphaSR +0.41 (need +0.28), 100% positive (need 65%), CAGR +2.7%, median DD -24.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.41 | +0.40 | +2.7% | 7.3% | -24.3% | 0.07 | 101 | 0.59% | 0.15 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.15, `rates_daily` +0.01, `eq_smallcap_daily` -0.00, `eq_index_daily` -0.02, `fx_major_daily` -0.12

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
      "weight": 0.4973,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.3,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2314,
  "max_leverage": 1.3935,
  "rebalance_band": 0.1959,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "0642136ed2e1",
  "generation": 13,
  "origin": "mutant",
  "parents": [
    "cc8cacb4d3e9"
  ]
}
```

</details>

### `5ea21d4fc2f9` — eq_largecap_daily

```
bollinger(k=2.91,n=24)x1.00 -> thr 0.21/0.03 both proportional lev<=1.7
```

- market: **eq_largecap_daily** (equity, vol 28%, spread 3.0bp, perfect-foresight ceiling SR 0.82)
- found in generation 13 via mutant from 1e2676bd17a3
- **search-burden headroom: 229** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 222. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.28 (need +0.25), 12688 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.38 (need +0.35), 100% of 20 instances positive (need 70%), median DD -32.5% / worst -51.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.26 (need +0.25) vs early half +0.43, retained 60% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=-0.04] |
| PASS | G4-stress | 2x costs +0.24 (need +0.15), 3x +0.18 (need +0.00), +1 bar delay +0.29 (need +0.10) |
| PASS | G5-permutation | real +0.34 vs null +0.04+-0.06 (p99 +0.16) -> z=4.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 0.953 (need 0.95) vs luck bar SR 0.26 after 222 confirmation tests (would still pass up to 229); Bonferroni p 2.20e-04 (need <=0.05) \| stricter all-trials view (8080 screened): DSR 0.114 vs SR 0.35, p 8.02e-03 |
| PASS | G7-stress-pool | median alphaSR +0.36 (need +0.28), 100% positive (need 65%), CAGR +2.5%, median DD -29.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.36 | +0.34 | +2.5% | 8.3% | -29.2% | 0.06 | 85 | 0.59% | 0.23 |

Travels to (alphaSR on other families, not a gate): `commodity_meanrev_daily` +0.45, `eq_largecap_break_daily` +0.18, `eq_index_daily` +0.01, `eq_smallcap_daily` +0.01, `rates_daily` -0.01, `fx_em_daily` -0.04

<details><summary>genome JSON</summary>

```json
{
  "market": "eq_largecap_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 2.9079,
        "n": 24
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2087,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "5ea21d4fc2f9",
  "generation": 13,
  "origin": "mutant",
  "parents": [
    "1e2676bd17a3"
  ]
}
```

</details>

### `8af95dc1b665` — commodity_meanrev_daily

```
rsi_rev(n=10)x1.00 + rsi_rev(n=28)x1.35 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 14 via mutant from 869724b2bed1
- **search-burden headroom: 124,272** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 238. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.33 (need +0.25), 7302 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.46 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.3% / worst -33.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.41 (need +0.25) vs early half +0.49, retained 84% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.41 (need +0.15), 3x +0.35 (need +0.00), +1 bar delay +0.42 (need +0.10) |
| PASS | G5-permutation | real +0.47 vs null +0.02+-0.06 (p99 +0.14) -> z=7.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.26 after 238 confirmation tests (would still pass up to 124,272); Bonferroni p 6.61e-13 (need <=0.05) \| stricter all-trials view (8800 screened): DSR 1.000 vs SR 0.36, p 2.44e-11 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +2.2%, median DD -18.5% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.42 | +2.2% | 5.4% | -18.5% | 0.06 | 48 | 0.28% | 0.10 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.35, `eq_largecap_break_daily` +0.17, `eq_smallcap_daily` +0.09, `eq_index_daily` +0.00, `rates_daily` -0.01, `eq_intraday_15m` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 28
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2934,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "8af95dc1b665",
  "generation": 14,
  "origin": "mutant",
  "parents": [
    "869724b2bed1"
  ]
}
```

</details>

### `480dc348d395` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.27 -> thr 0.28/0.03 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 14 via mutant from c860219fc8e1
- **search-burden headroom: 831,003** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 239. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 12035 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.8% / worst -41.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.38 (need +0.25) vs early half +0.62, retained 62% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.43 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.04+-0.06 (p99 +0.16) -> z=7.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.26 after 239 confirmation tests (would still pass up to 831,003); Bonferroni p 6.37e-13 (need <=0.05) \| stricter all-trials view (8800 screened): DSR 1.000 vs SR 0.36, p 2.34e-11 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +3.7%, median DD -29.6% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.45 | +3.7% | 9.0% | -29.6% | 0.06 | 83 | 0.52% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.10, `rates_daily` -0.00, `eq_index_daily` -0.01, `fx_em_daily` -0.02

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.2732,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 2.0,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "480dc348d395",
  "generation": 14,
  "origin": "mutant",
  "parents": [
    "c860219fc8e1"
  ]
}
```

</details>

### `2129e0f45017` — eq_largecap_daily

```
bollinger(k=3.00,n=25)x1.00 -> thr 0.21/0.03 both proportional lev<=1.7
```

- market: **eq_largecap_daily** (equity, vol 28%, spread 3.0bp, perfect-foresight ceiling SR 0.82)
- found in generation 14 via mutant from 5ea21d4fc2f9
- **search-burden headroom: 268** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 242. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 12433 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.37 (need +0.35), 100% of 20 instances positive (need 70%), median DD -31.4% / worst -51.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.28 (need +0.25) vs early half +0.41, retained 69% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.03] |
| PASS | G4-stress | 2x costs +0.25 (need +0.15), 3x +0.19 (need +0.00), +1 bar delay +0.29 (need +0.10) |
| PASS | G5-permutation | real +0.34 vs null +0.04+-0.06 (p99 +0.17) -> z=5.0, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 0.959 (need 0.95) vs luck bar SR 0.26 after 242 confirmation tests (would still pass up to 268); Bonferroni p 6.43e-05 (need <=0.05) \| stricter all-trials view (8800 screened): DSR 0.126 vs SR 0.36, p 2.34e-03 |
| PASS | G7-stress-pool | median alphaSR +0.36 (need +0.28), 100% positive (need 65%), CAGR +2.5%, median DD -28.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.36 | +0.35 | +2.5% | 8.1% | -28.0% | 0.07 | 83 | 0.55% | 0.22 |

Travels to (alphaSR on other families, not a gate): `commodity_meanrev_daily` +0.46, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.02, `rates_daily` +0.00, `eq_index_daily` +0.00, `fx_em_daily` -0.04

<details><summary>genome JSON</summary>

```json
{
  "market": "eq_largecap_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 3.0,
        "n": 25
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2087,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "2129e0f45017",
  "generation": 14,
  "origin": "mutant",
  "parents": [
    "5ea21d4fc2f9"
  ]
}
```

</details>

### `53de0df77ddb` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.27 -> thr 0.28/0.03 both proportional lev<=2.0  [hold<=80]
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 15 via mutant from 480dc348d395
- **search-burden headroom: 560,981** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 257. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 11939 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -25.4% / worst -41.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.38 (need +0.25) vs early half +0.61, retained 62% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.43 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | real +0.50 vs null +0.02+-0.06 (p99 +0.17) -> z=7.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.27 after 257 confirmation tests (would still pass up to 560,981); Bonferroni p 5.59e-12 (need <=0.05) \| stricter all-trials view (9520 screened): DSR 1.000 vs SR 0.36, p 2.07e-10 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +3.7%, median DD -29.9% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.44 | +3.7% | 9.0% | -29.9% | 0.06 | 82 | 0.52% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.10, `rates_daily` -0.00, `eq_index_daily` -0.02, `fx_em_daily` -0.02

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.2732,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 2.0,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": 80,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "53de0df77ddb",
  "generation": 15,
  "origin": "mutant",
  "parents": [
    "480dc348d395"
  ]
}
```

</details>

### `c7e87eea3e42` — commodity_meanrev_daily

```
rsi_rev(n=37)x1.35 + rsi_rev(n=8)x1.00 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 15 via mutant from 8af95dc1b665
- **search-burden headroom: 443,571** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 258. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.34 (need +0.25), 8167 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.49 (need +0.35), 100% of 20 instances positive (need 70%), median DD -17.5% / worst -30.3% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.43 (need +0.25) vs early half +0.59, retained 72% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.04 (allowed 0.30) [control_efficient_daily=-0.04, control_martingale_daily=-0.03] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.37 (need +0.00), +1 bar delay +0.44 (need +0.10) |
| PASS | G5-permutation | real +0.49 vs null +0.01+-0.06 (p99 +0.16) -> z=7.6, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.27 after 258 confirmation tests (would still pass up to 443,571); Bonferroni p 5.41e-12 (need <=0.05) \| stricter all-trials view (9520 screened): DSR 1.000 vs SR 0.36, p 2.00e-10 |
| PASS | G7-stress-pool | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +1.9%, median DD -17.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.39 | +1.9% | 5.2% | -17.4% | 0.05 | 54 | 0.33% | 0.10 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.30, `eq_largecap_break_daily` +0.16, `eq_smallcap_daily` +0.02, `rates_daily` -0.01, `eq_index_daily` -0.07, `fx_em_daily` -0.09

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 37
      },
      "weight": 1.3532,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 8
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2934,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "c7e87eea3e42",
  "generation": 15,
  "origin": "mutant",
  "parents": [
    "8af95dc1b665"
  ]
}
```

</details>

### `b8dca1603e1e` — commodity_meanrev_daily

```
rsi_rev(n=12)x1.00 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 15 via mutant from 8af95dc1b665
- **search-burden headroom: 19,288** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 260. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.39 (need +0.25), 10817 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.43 (need +0.35), 100% of 20 instances positive (need 70%), median DD -22.3% / worst -40.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.35 (need +0.25) vs early half +0.48, retained 74% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.35 (need +0.15), 3x +0.28 (need +0.00), +1 bar delay +0.39 (need +0.10) |
| PASS | G5-permutation | real +0.42 vs null +0.01+-0.07 (p99 +0.16) -> z=6.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.27 after 260 confirmation tests (would still pass up to 19,288); Bonferroni p 1.43e-07 (need <=0.05) \| stricter all-trials view (9520 screened): DSR 0.984 vs SR 0.36, p 5.22e-06 |
| PASS | G7-stress-pool | median alphaSR +0.40 (need +0.28), 100% positive (need 65%), CAGR +2.7%, median DD -26.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.40 | +0.39 | +2.7% | 7.5% | -26.4% | 0.06 | 71 | 0.58% | 0.16 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.32, `eq_largecap_break_daily` +0.14, `rates_daily` -0.00, `eq_smallcap_daily` -0.02, `eq_index_daily` -0.02, `fx_major_daily` -0.09

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 12
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2934,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "b8dca1603e1e",
  "generation": 15,
  "origin": "mutant",
  "parents": [
    "8af95dc1b665"
  ]
}
```

</details>

### `e8840ff23941` — eq_largecap_daily

```
bollinger(k=3.00,n=25)x1.00 -> thr 0.20/0.03 both proportional lev<=1.7
```

- market: **eq_largecap_daily** (equity, vol 28%, spread 3.0bp, perfect-foresight ceiling SR 0.82)
- found in generation 15 via mutant from 2129e0f45017
- **search-burden headroom: 263** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 262. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.28 (need +0.25), 12489 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.38 (need +0.35), 100% of 20 instances positive (need 70%), median DD -30.2% / worst -51.5% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.28 (need +0.25) vs early half +0.40, retained 70% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.06 (allowed 0.30) [control_efficient_daily=-0.06, control_martingale_daily=-0.03] |
| PASS | G4-stress | 2x costs +0.26 (need +0.15), 3x +0.19 (need +0.00), +1 bar delay +0.30 (need +0.10) |
| PASS | G5-permutation | real +0.34 vs null +0.04+-0.06 (p99 +0.18) -> z=4.8, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 0.951 (need 0.95) vs luck bar SR 0.27 after 262 confirmation tests (would still pass up to 263); Bonferroni p 2.07e-04 (need <=0.05) \| stricter all-trials view (9520 screened): DSR 0.106 vs SR 0.36, p 7.51e-03 |
| PASS | G7-stress-pool | median alphaSR +0.36 (need +0.28), 100% positive (need 65%), CAGR +2.5%, median DD -28.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.36 | +0.35 | +2.5% | 8.1% | -28.2% | 0.07 | 84 | 0.56% | 0.22 |

Travels to (alphaSR on other families, not a gate): `commodity_meanrev_daily` +0.45, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.01, `rates_daily` +0.01, `eq_index_daily` +0.00, `fx_em_daily` -0.04

<details><summary>genome JSON</summary>

```json
{
  "market": "eq_largecap_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 3.0,
        "n": 25
      },
      "weight": 1.0,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2029,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "e8840ff23941",
  "generation": 15,
  "origin": "mutant",
  "parents": [
    "2129e0f45017"
  ]
}
```

</details>

### `8af53c0789f6` — commodity_meanrev_daily

```
rsi_rev(n=16)x1.35 + rsi_rev(n=28)x1.35 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 16 via mutant from abf6c0225ffd
- **search-burden headroom: 43,371** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 276. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 5462 trades, 75% instances positive |
| PASS | G2-replication | median alphaSR +0.45 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.7% / worst -27.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.38 (need +0.25) vs early half +0.55, retained 68% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.40 (need +0.15), 3x +0.37 (need +0.00), +1 bar delay +0.41 (need +0.10) |
| PASS | G5-permutation | real +0.48 vs null +0.02+-0.06 (p99 +0.18) -> z=7.4, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.27 after 276 confirmation tests (would still pass up to 43,371); Bonferroni p 1.37e-11 (need <=0.05) \| stricter all-trials view (10240 screened): DSR 0.996 vs SR 0.37, p 5.09e-10 |
| PASS | G7-stress-pool | median alphaSR +0.43 (need +0.28), 100% positive (need 65%), CAGR +2.0%, median DD -18.0% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.43 | +0.41 | +2.0% | 5.1% | -18.0% | 0.06 | 36 | 0.19% | 0.09 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_intraday_15m` +0.20, `eq_largecap_break_daily` +0.16, `eq_smallcap_daily` +0.16, `rates_daily` +0.02, `eq_index_daily` -0.03

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.3532,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 28
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.173,
  "max_leverage": 1.704,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "8af53c0789f6",
  "generation": 16,
  "origin": "mutant",
  "parents": [
    "abf6c0225ffd"
  ]
}
```

</details>

### `a48393e6deb4` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.27 -> thr 0.29/0.03 both proportional lev<=2.0
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 16 via mutant from 480dc348d395
- **search-burden headroom: 506,445** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 277. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 11827 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.8% / worst -41.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.38 (need +0.25) vs early half +0.62, retained 61% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.39 (need +0.00), +1 bar delay +0.47 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.03+-0.06 (p99 +0.19) -> z=7.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.27 after 277 confirmation tests (would still pass up to 506,445); Bonferroni p 6.09e-12 (need <=0.05) \| stricter all-trials view (10240 screened): DSR 1.000 vs SR 0.37, p 2.25e-10 |
| PASS | G7-stress-pool | median alphaSR +0.48 (need +0.28), 100% positive (need 65%), CAGR +3.6%, median DD -29.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.48 | +0.44 | +3.6% | 9.0% | -29.4% | 0.06 | 81 | 0.52% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.19, `eq_smallcap_daily` +0.11, `rates_daily` +0.00, `eq_index_daily` -0.01, `fx_em_daily` -0.02

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.2732,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2903,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 2.0,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "a48393e6deb4",
  "generation": 16,
  "origin": "mutant",
  "parents": [
    "480dc348d395"
  ]
}
```

</details>

### `867146acee0d` — commodity_meanrev_daily

```
rsi_rev(n=10)x1.00 + rsi_rev(n=28)x1.35 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 17 via mutant from 869724b2bed1
- **search-burden headroom: 69,669** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 295. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.33 (need +0.25), 7302 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.46 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.3% / worst -33.4% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.41 (need +0.25) vs early half +0.49, retained 84% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.03 (allowed 0.30) [control_efficient_daily=-0.03, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.41 (need +0.15), 3x +0.35 (need +0.00), +1 bar delay +0.42 (need +0.10) |
| PASS | G5-permutation | real +0.47 vs null +0.02+-0.07 (p99 +0.15) -> z=6.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.28 after 295 confirmation tests (would still pass up to 69,669); Bonferroni p 3.94e-09 (need <=0.05) \| stricter all-trials view (10960 screened): DSR 0.998 vs SR 0.37, p 1.46e-07 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +2.2%, median DD -18.5% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.42 | +2.2% | 5.4% | -18.5% | 0.06 | 48 | 0.28% | 0.10 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.35, `eq_largecap_break_daily` +0.17, `eq_smallcap_daily` +0.09, `eq_index_daily` +0.00, `rates_daily` -0.01, `eq_intraday_15m` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "rsi_rev",
      "params": {
        "n": 10
      },
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 28
      },
      "weight": 1.3532,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2314,
  "max_leverage": 1.6686,
  "rebalance_band": 0.394,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "867146acee0d",
  "generation": 17,
  "origin": "mutant",
  "parents": [
    "869724b2bed1"
  ]
}
```

</details>

### `42dac13e16ac` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.27 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 17 via crossover from 480dc348d395, 3425c77257d8
- **search-burden headroom: 419,851** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 296. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 12035 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -24.8% / worst -41.7% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.38 (need +0.25) vs early half +0.62, retained 62% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.43 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.04+-0.06 (p99 +0.15) -> z=8.1, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.28 after 296 confirmation tests (would still pass up to 419,851); Bonferroni p 9.86e-14 (need <=0.05) \| stricter all-trials view (10960 screened): DSR 1.000 vs SR 0.37, p 3.65e-12 |
| PASS | G7-stress-pool | median alphaSR +0.47 (need +0.28), 100% positive (need 65%), CAGR +3.7%, median DD -29.6% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.47 | +0.45 | +3.7% | 9.0% | -29.6% | 0.06 | 83 | 0.52% | 0.18 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.10, `rates_daily` -0.00, `eq_index_daily` -0.01, `fx_em_daily` -0.02

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.2732,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 1.704,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "42dac13e16ac",
  "generation": 17,
  "origin": "crossover",
  "parents": [
    "480dc348d395",
    "3425c77257d8"
  ]
}
```

</details>

### `745cc2b1f2a0` — commodity_meanrev_daily

```
rsi_rev(n=13)x1.00 + rsi_rev(n=30)x1.08 -> thr 0.21/0.05 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 18 via mutant from 87a6fb75501d
- **search-burden headroom: 264,442** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 315. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.28 (need +0.25), 13414 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -16.0% / worst -32.8% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.37 (need +0.25) vs early half +0.58, retained 63% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.01] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.44 (need +0.10) |
| PASS | G5-permutation | real +0.50 vs null +0.03+-0.07 (p99 +0.18) -> z=7.2, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.28 after 315 confirmation tests (would still pass up to 264,442); Bonferroni p 1.36e-10 (need <=0.05) \| stricter all-trials view (11680 screened): DSR 1.000 vs SR 0.38, p 5.04e-09 |
| PASS | G7-stress-pool | median alphaSR +0.49 (need +0.28), 100% positive (need 65%), CAGR +2.3%, median DD -18.4% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.49 | +0.44 | +2.3% | 5.5% | -18.4% | 0.07 | 88 | 0.32% | 0.11 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.37, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.10, `rates_daily` +0.01, `eq_index_daily` +0.01, `fx_major_daily` -0.09

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
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 30
      },
      "weight": 1.0798,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.207,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2314,
  "max_leverage": 1.704,
  "rebalance_band": 0.1959,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "745cc2b1f2a0",
  "generation": 18,
  "origin": "mutant",
  "parents": [
    "87a6fb75501d"
  ]
}
```

</details>

### `1db3a9db76fd` — commodity_meanrev_daily

```
bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.68 -> thr 0.28/0.03 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 18 via mutant from 480dc348d395
- **search-burden headroom: 374,174** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 317. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.27 (need +0.25), 11990 trades, 100% instances positive |
| PASS | G2-replication | median alphaSR +0.50 (need +0.35), 100% of 20 instances positive (need 70%), median DD -23.6% / worst -39.2% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.40 (need +0.25) vs early half +0.62, retained 64% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.02 (allowed 0.30) [control_efficient_daily=-0.02, control_martingale_daily=-0.02] |
| PASS | G4-stress | 2x costs +0.44 (need +0.15), 3x +0.38 (need +0.00), +1 bar delay +0.46 (need +0.10) |
| PASS | G5-permutation | real +0.51 vs null +0.03+-0.06 (p99 +0.16) -> z=8.5, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.28 after 317 confirmation tests (would still pass up to 374,174); Bonferroni p 0.00e+00 (need <=0.05) \| stricter all-trials view (11680 screened): DSR 1.000 vs SR 0.38, p 0.00e+00 |
| PASS | G7-stress-pool | median alphaSR +0.46 (need +0.28), 100% positive (need 65%), CAGR +3.5%, median DD -28.2% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.46 | +0.45 | +3.5% | 8.5% | -28.2% | 0.07 | 82 | 0.50% | 0.17 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.36, `eq_largecap_break_daily` +0.20, `eq_smallcap_daily` +0.10, `rates_daily` +0.00, `eq_index_daily` -0.01, `fx_em_daily` -0.05

<details><summary>genome JSON</summary>

```json
{
  "market": "commodity_meanrev_daily",
  "genes": [
    {
      "name": "bollinger",
      "params": {
        "k": 1.9265,
        "n": 78
      },
      "weight": 0.596,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 16
      },
      "weight": 1.6755,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.2814,
  "exit_threshold": 0.034,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.157,
  "max_leverage": 1.7265,
  "rebalance_band": 0.2469,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "1db3a9db76fd",
  "generation": 18,
  "origin": "mutant",
  "parents": [
    "480dc348d395"
  ]
}
```

</details>

### `4fda11304f30` — commodity_meanrev_daily

```
rsi_rev(n=13)x1.00 + rsi_rev(n=24)x1.08 -> thr 0.21/0.05 both proportional lev<=1.7
```

- market: **commodity_meanrev_daily** (commodity, vol 35%, spread 5.0bp, perfect-foresight ceiling SR 0.87)
- found in generation 19 via mutant from 745cc2b1f2a0
- **search-burden headroom: 104,950** — the largest number of confirmation tests this bot's evidence could have come out of and still clear G6. Certified here after 334. A headroom close to that number means the certification leans on the search having been small; a headroom far above it means the edge would survive a much larger hunt.

|  | gate | evidence |
|---|---|---|
| PASS | G1-oos | alphaSR +0.29 (need +0.25), 13900 trades, 88% instances positive |
| PASS | G2-replication | median alphaSR +0.48 (need +0.35), 100% of 20 instances positive (need 70%), median DD -17.8% / worst -36.9% (allowed -35%/-56%), 0 wipeouts |
| PASS | G2b-durability | late-half alphaSR +0.38 (need +0.25) vs early half +0.61, retained 62% (ratio not gated: this market decays by design) |
| PASS | G3-controls | worst \|alphaSR\| 0.05 (allowed 0.30) [control_efficient_daily=-0.05, control_martingale_daily=+0.00] |
| PASS | G4-stress | 2x costs +0.42 (need +0.15), 3x +0.36 (need +0.00), +1 bar delay +0.43 (need +0.10) |
| PASS | G5-permutation | real +0.47 vs null +0.03+-0.06 (p99 +0.17) -> z=7.7, p=0.0083 of 120 draws (need <=0.01) |
| PASS | G6-multiplicity | DSR 1.000 (need 0.95) vs luck bar SR 0.29 after 334 confirmation tests (would still pass up to 104,950); Bonferroni p 1.56e-12 (need <=0.05) \| stricter all-trials view (12400 screened): DSR 0.999 vs SR 0.38, p 5.78e-11 |
| PASS | G7-stress-pool | median alphaSR +0.45 (need +0.28), 100% positive (need 65%), CAGR +2.5%, median DD -19.3% |

Confirmation-pool performance (third disjoint instance pool, 20 instances):

| alphaSR | SR | CAGR | vol | medDD | Calmar | trades/yr | cost/yr | avg lev |
|---|---|---|---|---|---|---|---|---|
| +0.45 | +0.44 | +2.5% | 5.9% | -19.3% | 0.07 | 93 | 0.36% | 0.12 |

Travels to (alphaSR on other families, not a gate): `eq_largecap_daily` +0.37, `eq_largecap_break_daily` +0.18, `eq_smallcap_daily` +0.09, `rates_daily` +0.02, `eq_index_daily` +0.01, `fx_em_daily` -0.10

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
      "weight": 1.0,
      "mode": 1
    },
    {
      "name": "rsi_rev",
      "params": {
        "n": 24
      },
      "weight": 1.0798,
      "mode": 1
    }
  ],
  "filters": [],
  "combine": "weighted",
  "entry_threshold": 0.207,
  "exit_threshold": 0.05,
  "direction": "both",
  "sizing": "proportional",
  "base_size": 0.611,
  "target_vol": 0.2314,
  "max_leverage": 1.704,
  "rebalance_band": 0.1959,
  "atr_n": 32,
  "stop_atr": null,
  "take_atr": null,
  "trail_atr": null,
  "max_hold": null,
  "min_hold": 4,
  "dd_halt": null,
  "dd_resume": 13,
  "bot_id": "4fda11304f30",
  "generation": 19,
  "origin": "mutant",
  "parents": [
    "745cc2b1f2a0"
  ]
}
```

</details>

## Portfolio

```
4 distinct strategies across 2 market(s) / 2 asset class(es)   [from 30 proven genomes]
  best single bot        alphaSR +0.45
  portfolio (lab, rho=0) alphaSR +0.68   <- upper bound, independent synthetic markets
  portfolio (rho=0.3)    alphaSR +0.59   <- plan with this one
    28.7%  44504d663841  commodity_meanrev_daily  alphaSR +0.39
    21.8%  8eb8425dceaf  commodity_meanrev_daily  alphaSR +0.45
    26.4%  0642136ed2e1  commodity_meanrev_daily  alphaSR +0.40
    23.2%  5ea21d4fc2f9  eq_largecap_daily        alphaSR +0.36
```

The two portfolio numbers differ because this lab generates each market family independently, so cross-family correlation is structurally zero — an assumption real asset classes violate exactly when it matters. Plan with the rho=0.3 number.

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `745cc2b1f2a0` | commodity_meanrev_daily | +0.55 | +0.61 | 61031 | `rsi_rev(n=13)x1.00 + rsi_rev(n=30)x1.08 -> thr 0.21/0.05 both prop` |
| `4fda11304f30` | commodity_meanrev_daily | +0.55 | +0.61 | 64220 | `rsi_rev(n=13)x1.00 + rsi_rev(n=24)x1.08 -> thr 0.21/0.05 both prop` |
| `cc8cacb4d3e9` | commodity_meanrev_daily | +0.54 | +0.60 | 41956 | `rsi_rev(n=23)x0.50 -> thr 0.30/0.03 both proportional lev<=1.4` |
| `3bdf55742c6c` | commodity_meanrev_daily | +0.54 | +0.60 | 41956 | `rsi_rev(n=23)x0.44 -> thr 0.30/0.03 both proportional lev<=1.4` |
| `480dc348d395` | commodity_meanrev_daily | +0.52 | +0.60 | 56603 | `bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.27 -> thr 0.28/0.03 ` |
| `42dac13e16ac` | commodity_meanrev_daily | +0.52 | +0.60 | 56603 | `bollinger(k=1.93,n=78)x0.60 + rsi_rev(n=16)x1.27 -> thr 0.28/0.03 ` |
| `1e9f0b018cc4` | eq_intraday_15m | +0.52 | +0.75 | 39172 | `rsi_rev(n=23)x0.33 + rsi_rev(n=28)x1.35 + rsi_rev(n=30)x1.08 -> th` |
| `3ee219106b0f` | commodity_meanrev_daily | +0.52 | +0.63 | 39312 | `rsi_rev(n=13)x1.00 + rsi_rev(n=23)x0.44 + rsi_rev(n=30)x1.08 -> th` |
| `abf6c0225ffd` | commodity_meanrev_daily | +0.51 | +0.62 | 28061 | `bollinger(k=2.53,n=73)x0.60 + rsi_rev(n=16)x1.35 + rsi_rev(n=28)x1` |
| `21c5799fa669` | commodity_meanrev_daily | +0.51 | +0.62 | 28061 | `bollinger(k=2.53,n=73)x0.60 + rsi_rev(n=16)x1.35 + rsi_rev(n=28)x1` |
| `68fae7387518` | eq_intraday_15m | +0.51 | +0.69 | 46990 | `rsi_rev(n=13)x0.72 + rsi_rev(n=28)x1.35 + rsi_rev(n=30)x1.08 -> th` |
| `395aafbd8b21` | eq_intraday_15m | +0.51 | +0.63 | 53747 | `rsi_rev(n=26)x1.58 -> thr 0.29/0.03 both proportional lev<=1.5  [t` |
| `87a6fb75501d` | commodity_meanrev_daily | +0.51 | +0.63 | 39012 | `rsi_rev(n=13)x1.00 + rsi_rev(n=23)x0.50 + rsi_rev(n=30)x1.08 -> th` |
| `00a713fdc0f5` | eq_intraday_15m | +0.51 | +0.70 | 74439 | `bollinger(k=1.70,n=78)x0.60 + -macd(fast=6,sig=19,slow=118)x0.82 +` |
| `d33f78a8c1d3` | eq_intraday_15m | +0.50 | +0.65 | 53869 | `rsi_rev(n=26)x1.58 -> thr 0.29/0.03 both proportional lev<=1.5` |

## Expansions

| generation | new level | trigger | new space |
|---|---|---|---|
| 2 | 2 | 2 generations without a pass | L2: tier=2 genes<=3 filters<=1 pop=480 finalists=16 per_mkt=3 markets=12 |
| 4 | 3 | 2 generations without a pass | L3: tier=2 genes<=3 filters<=2 pop=720 finalists=20 per_mkt=3 markets=12 |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 320 | 7 | 12 | 4 | 0 | +0.23 | 50s |
| 2 | 1 | 320 | 7 | 12 | 0 | 0 | +0.40 | 44s |
| 3 | 2 | 480 | 12 | 16 | 2 | 0 | +0.40 | 71s |
| 4 | 2 | 480 | 12 | 16 | 0 | 0 | +0.42 | 69s |
| 5 | 3 | 720 | 12 | 20 | 0 | 0 | +0.42 | 93s |
| 6 | 3 | 720 | 12 | 20 | 0 | 1 | +0.52 | 96s |
| 7 | 3 | 720 | 12 | 20 | 0 | 1 | +0.53 | 97s |
| 8 | 3 | 720 | 12 | 20 | 0 | 2 | +0.53 | 102s |
| 9 | 3 | 720 | 12 | 20 | 0 | 2 | +0.54 | 98s |
| 10 | 3 | 720 | 12 | 20 | 0 | 2 | +0.54 | 105s |
| 11 | 3 | 720 | 12 | 20 | 0 | 2 | +0.54 | 111s |
| 12 | 3 | 720 | 12 | 20 | 0 | 2 | +0.54 | 113s |
| 13 | 3 | 720 | 12 | 20 | 0 | 4 | +0.52 | 108s |
| 14 | 3 | 720 | 12 | 20 | 0 | 3 | +0.54 | 108s |
| 15 | 3 | 720 | 12 | 18 | 0 | 4 | +0.52 | 116s |
| 16 | 3 | 720 | 12 | 20 | 0 | 2 | +0.53 | 112s |
| 17 | 3 | 720 | 12 | 20 | 0 | 2 | +0.53 | 112s |
| 18 | 3 | 720 | 12 | 19 | 0 | 2 | +0.55 | 122s |
| 19 | 3 | 720 | 12 | 20 | 0 | 1 | +0.55 | 118s |

## Market calibration

`ceiling` is the perfect-foresight Sharpe bound implied by the planted structure; `gross`/`net` are the best textbook archetype without and with costs. A family whose net number is negative is a market where the honest answer is *don't trade this*.

The two `control_*` rows show a positive net number (~+0.3) and that is expected, not a contradiction: it is the **maximum over 13 archetypes of a median over 6 instances**, which is a selection statistic, and on 12 years of daily data its null spread is about that size. The point of the controls is not that no single statistic on them is ever positive — it is that nothing survives *replication* on them, which is what the gauntlet tests and what `run.py fpr` measures end to end (0 certified from 3,000 candidates).

| family | vol | ceiling SR | gross alphaSR | net alphaSR | cost bite | archetypes net + |
|---|---|---|---|---|---|---|
| eq_index_daily | 16.3% | 1.02 | +0.15 | +0.06 | +0.09 | 3/10 |
| eq_largecap_daily | 29.1% | 0.82 | +0.47 | +0.36 | +0.10 | 4/10 |
| eq_smallcap_daily | 46.0% | 1.30 | +0.56 | +0.00 | +0.00 | 1/10 |
| fx_major_daily | 8.3% | 1.26 | +0.37 | +0.19 | +0.18 | 3/12 |
| fx_em_daily | 13.8% | 1.02 | +0.22 | +0.01 | +0.19 | 3/12 |
| crypto_major_hourly | 58.4% | 1.80 | +0.91 | -0.75 | +0.74 | 0/10 |
| crypto_alt_hourly | 110.5% | 1.86 | +1.12 | -0.95 | +0.95 | 0/10 |
| futures_trend_daily | 13.9% | 0.94 | +0.31 | +0.21 | +0.09 | 6/12 |
| commodity_meanrev_daily | 35.7% | 0.87 | +0.48 | +0.36 | +0.12 | 4/12 |
| rates_daily | 5.5% | 0.87 | +0.31 | +0.16 | +0.15 | 6/12 |
| eq_intraday_15m | 21.9% | 1.82 | +0.74 | -0.00 | -0.00 | 0/10 |
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
