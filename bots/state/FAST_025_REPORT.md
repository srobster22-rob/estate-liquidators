# Bot factory: run report

_Generated 2026-08-12 12:59:50 from `fast_025.json`._

## Result

**No bot passed.** 16375 candidates were screened across 22 generations and 459 reached the gauntlet. That is a result, not a failure to produce one: it says the edges planted in this catalogue, at these costs, are not reachable by the strategy space searched so far. The funnel below shows which gate did the killing, which is the useful information — see 'What to do next'.

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

Read it as a sentence: **the strategies this lab has found survive a fade of about a halflife every 24 simulated years, thin out sharply by 12, and are gone by 6.** Nothing survives an abrupt break in the first half of its life. Everything above is conditional on where in that range the real world sits, and this repository cannot tell you.

## Rejection funnel

Where candidates died. A healthy funnel kills most bots early; a funnel that kills everything at G5/G6 means the search is finding in-sample fits, and a funnel with kills at G3 means something is wrong with the harness.

| gate | rejected | share | what that gate proves |
|---|---|---|---|
| G1-oos | 411 | 90% | worked only on the bars the search scored (in-sample fit) |
| G2-replication | 48 | 10% | worked only on the instances it was bred on (instance luck) |

## Hall of fame (screen scores — evidence of nothing, kept for breeding)

| bot | market | screen fit | screen alphaSR | trades | rule |
|---|---|---|---|---|---|
| `6a2296c707ce` | commodity_meanrev_daily~hl=0.25x | +0.52 | +0.52 | 69755 | `rsi_rev(n=24)x0.90 -> thr 0.14/0.05 both proportional lev<=0.8  [h` |
| `ab485bda7b03` | commodity_meanrev_daily~hl=0.25x | +0.52 | +0.53 | 64942 | `rsi_rev(n=24)x0.90 -> thr 0.14/0.05 both proportional lev<=0.8  [h` |
| `5bcf3fb66be3` | commodity_meanrev_daily~hl=0.25x | +0.48 | +0.53 | 65807 | `rsi_rev(n=14)x0.70 + rsi_rev(n=34)x0.99 -> thr 0.14/0.05 both prop` |
| `1a94d6162a79` | commodity_meanrev_daily~hl=0.25x | +0.48 | +0.53 | 65001 | `rsi_rev(n=14)x0.70 + rsi_rev(n=34)x0.99 -> thr 0.14/0.05 both prop` |
| `56ef798d37da` | commodity_meanrev_daily~hl=0.25x | +0.47 | +0.52 | 104708 | `rsi_rev(n=24)x0.90 \| trend_strength(nf=9,ns=59,thr=0.00) -> thr 0.` |
| `674d04438d6d` | commodity_meanrev_daily~hl=0.25x | +0.47 | +0.52 | 104679 | `rsi_rev(n=24)x0.90 \| trend_strength(nf=9,ns=59,thr=0.00) -> thr 0.` |
| `505f6aca1112` | commodity_meanrev_daily~hl=0.25x | +0.46 | +0.55 | 39277 | `rsi_rev(n=23)x1.00 unanimous rsi_rev(n=29)x1.00 -> thr 0.08/0.05 b` |
| `6262dcbebb8c` | commodity_meanrev_daily~hl=0.25x | +0.46 | +0.54 | 35313 | `rsi_rev(n=23)x1.00 unanimous rsi_rev(n=29)x1.00 -> thr 0.14/0.05 b` |
| `dee2016e646f` | commodity_meanrev_daily~hl=0.25x | +0.46 | +0.56 | 91094 | `rsi_rev(n=14)x1.04 + rsi_rev(n=22)x1.01 + rsi_rev(n=40)x0.99 -> th` |
| `71585b6680f1` | commodity_meanrev_daily~hl=0.25x | +0.46 | +0.56 | 91094 | `rsi_rev(n=14)x1.04 + rsi_rev(n=22)x1.01 + rsi_rev(n=40)x0.99 -> th` |
| `39f0f7b5bac0` | eq_largecap_daily~hl=0.25x | +0.43 | +0.46 | 77019 | `rsi_rev(n=14)x0.45 -> thr 0.26/0.05 both proportional lev<=2.0  [s` |
| `2cc2950b0307` | eq_largecap_daily~hl=0.25x | +0.43 | +0.48 | 83858 | `rsi_rev(n=14)x0.45 -> thr 0.22/0.05 both proportional lev<=2.0  [s` |
| `69f2f98179e5` | eq_largecap_daily~hl=0.25x | +0.41 | +0.50 | 79316 | `rsi_rev(n=14)x1.39 + rsi_rev(n=37)x0.42 -> thr 0.14/0.05 both prop` |
| `f0f5f0bc79bd` | eq_largecap_daily~hl=0.25x | +0.41 | +0.51 | 80481 | `rsi_rev(n=14)x1.39 + rsi_rev(n=37)x0.42 -> thr 0.14/0.05 both prop` |
| `49bc3d20e505` | eq_largecap_daily~hl=0.25x | +0.40 | +0.48 | 89372 | `bollinger(k=2.45,n=50)x1.21 + rsi_rev(n=14)x1.00 -> thr 0.22/0.05 ` |

## Expansions

| generation | new level | trigger | new space |
|---|---|---|---|
| 3 | 2 | 3 generations without a pass | L2: tier=2 genes<=3 filters<=1 pop=240 finalists=16 per_mkt=3 markets=10 |
| 6 | 3 | 3 generations without a pass | L3: tier=2 genes<=3 filters<=2 pop=360 finalists=20 per_mkt=3 markets=10 |
| 9 | 4 | 3 generations without a pass | L4: tier=3 genes<=4 filters<=2 pop=540 finalists=24 per_mkt=3 markets=11 |
| 12 | 5 | 3 generations without a pass | L5: tier=3 genes<=4 filters<=2 pop=810 finalists=28 per_mkt=3 markets=11 |
| 15 | 6 | 3 generations without a pass | L6: tier=4 genes<=5 filters<=3 pop=1215 finalists=32 per_mkt=4 markets=11 |
| 18 | 7 | 3 generations without a pass | L7: tier=4 genes<=5 filters<=3 pop=1600 finalists=36 per_mkt=5 markets=11 |
| 21 | 8 | 3 generations without a pass | L8: tier=4 genes<=5 filters<=3 pop=1600 finalists=40 per_mkt=6 markets=11 |

## Generations

| gen | level | candidates | markets | gauntlets | of which priors | proven | best screen fit | screen time |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 160 | 5 | 6 | 2 | 0 | +0.13 | 54s |
| 2 | 1 | 160 | 5 | 7 | 0 | 0 | +0.18 | 45s |
| 3 | 1 | 160 | 5 | 9 | 0 | 0 | +0.39 | 44s |
| 4 | 2 | 240 | 10 | 11 | 2 | 0 | +0.35 | 71s |
| 5 | 2 | 240 | 10 | 11 | 0 | 0 | +0.39 | 65s |
| 6 | 2 | 240 | 10 | 9 | 0 | 0 | +0.46 | 69s |
| 7 | 3 | 360 | 10 | 13 | 0 | 0 | +0.45 | 94s |
| 8 | 3 | 360 | 10 | 15 | 0 | 0 | +0.46 | 96s |
| 9 | 3 | 360 | 10 | 14 | 0 | 0 | +0.47 | 100s |
| 10 | 4 | 540 | 11 | 17 | 0 | 0 | +0.51 | 183s |
| 11 | 4 | 540 | 11 | 16 | 0 | 0 | +0.51 | 172s |
| 12 | 4 | 540 | 11 | 19 | 0 | 0 | +0.51 | 179s |
| 13 | 5 | 810 | 11 | 21 | 0 | 0 | +0.51 | 261s |
| 14 | 5 | 810 | 11 | 25 | 0 | 0 | +0.52 | 267s |
| 15 | 5 | 810 | 11 | 23 | 0 | 0 | +0.48 | 272s |
| 16 | 6 | 1215 | 11 | 32 | 0 | 0 | +0.52 | 386s |
| 17 | 6 | 1215 | 11 | 32 | 0 | 0 | +0.52 | 401s |
| 18 | 6 | 1215 | 11 | 31 | 0 | 0 | +0.52 | 410s |
| 19 | 7 | 1600 | 11 | 36 | 0 | 0 | +0.51 | 552s |
| 20 | 7 | 1600 | 11 | 36 | 0 | 0 | +0.52 | 567s |
| 21 | 7 | 1600 | 11 | 36 | 0 | 0 | +0.52 | 580s |
| 22 | 8 | 1600 | 11 | 40 | 0 | 0 | +0.52 | 605s |

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

1. Read the funnel. Mass death at **G2** means the search is finding instance-specific luck — raise `screen_instances` so screening is harder to fool. Mass death at **G4** means the edge is real but smaller than the spread; look at cheaper families or lower-turnover genomes.
2. Let it expand further: `--max-generations` higher, or `--target 1`. Expansion unlocks primitives and families it has not tried yet.
3. Do **not** relax `GauntletConfig` to manufacture a pass. A bot that only passes a weakened gauntlet is worth less than no bot, because it will be funded.
