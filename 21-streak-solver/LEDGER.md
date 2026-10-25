# 21 STREAK Solver — ledger

Objective: maximise mean final score = banked points + 1000 if the game ends with all 3 lives
(the end bonus is a UI toggle; the bench runs with it on).

Every number below is a **paired** A/B on identical deals (`bench/par.js --a --b`), 240 games
unless stated, balanced mode. Rules of evidence are inherited from `../blackjack-solver/LOOP_PROMPT.md`:
t ≥ 2 on a confirmation run or reject; never two benchmarks at once; fuzz every candidate.

## Baseline — the fork as patched (2026-09-14)

```
mean 17940 ± 222   sd 3434   p10 13250   median 18500   p90 21750   max 23150
perfect-lives 0.775   bust-outs 0.013   busts/game 0.31 (0.19 forced)   stays/game 1.27
clears/game 14.77 (13.75 × 21, 0.51 × 5-card, 0.50 × 5-card-21, 0.02 × 777)
streak bonus/game 10752   mean best streak 11.5
```

Compared with the old game's 8,665 the extra ~9,300 is almost entirely streak bonus (1,485 →
10,752). Clears per game are the same 14.77 — the deck packs the same either way — so the
only lever left is **not resetting**: fewer stays, fewer busts, and ordering clears so the
streak is long when the deck is.

## Experiments

| # | hypothesis | result | verdict |
|---|---|---|---|
| A | Rollouts truncate at 22 cards, so a live streak's value beyond the horizon is invisible. Credit `min(rem/3.5, 8) × bonus(streak+1) × 0.5` in `stateValue`. | **−300 ± 176 (t=−1.71)**; stays 1.27 → 1.43, busts 0.31 → 0.35 | **rejected** — over-values the streak, so it takes stays/busts to *protect* it that cost more than they save |
| C | A bust-out forfeits the rest of the deck (~345 pts/card), so a life should be worth more than the old 500 in `stateValue`. lifeVal 500 → 1500. | −52 ± 125 (t=−0.42); bust-outs 0.013 → 0.008, busts 0.31 → 0.28 | **null** — rollouts already price the life through the streak reset; the proxy weight is flat, as it was in the old game |

(A and C were run with the all-lives end bonus ON, before the user confirmed this game has none. Everything below is bonus OFF.)
| F | The real game is 3 min for 52 cards, so cut latency: exact budgets 3000/2500/1500/1000 → 900/700/500/400 ms and SIMS 600 → 300 (node: median move 158 → 75 ms, worst 2.6 s → 1.0 s). | **−527 ± 191 (t=−2.76)**; bust-outs 0.004 → 0.021, busts 0.45 → 0.55, perfect-lives 0.654 → 0.571 | **rejected** — the search is NOT saturated here the way it was in the old game; the extra busts come from the thinner search. The 3-min clock is a TOTAL budget: ~0.3 s average per move plus two ~3 s endgame moves still fits with ~2 s of tapping per card, so full strength ships. Untested: which half (sims or budget) carries the cost. |

## Baseline, bonus OFF (240 games, the shipped build)

```
mean 17204 ± 180   perfect-lives 0.654   bust-outs 0.004   busts/game 0.45   stays/game 1.21
streak bonus/game 10786   mean best streak 11.5
```
| S | STAY confirmed to let the dealt card go into ANY slot, not just the cleared one. Action becomes (cleared slot, destination); busting destinations pruned as dominated; exact endgame enumerates the same pairs. | fuzz 0/325; traces show "stay slot 2, card to slot 4" in use; paired A/B vs the old stay (card into the cleared slot only): **−34 ± 119 (t=−0.28)**, 173/240 games identical | **shipped as a rule fix** — a strict superset of the old moves; the extra destinations almost never change the decision |
| G | The user watched the solver put a 10 on an 8 instead of on a loaded ace (A/9/5/8, 10 dealt). The old solver declined 21s to keep slots loaded for back-to-back chains; here the streak survives building, so declining has no chain value. Completions pre-empt the candidate list in every mode. | declined completions in 195 reachable states: 30 → 0. Paired A/B **+258 ± 157 (t=1.64)**; clears 14.73 → 15.00, busts 0.46 → 0.36, bust-outs 0.013 → 0.008, perfect-lives 0.633 → 0.704, sd 3024 → 2890, p10 13500 → 13700 | **SHIPPED and CONFIRMED** — fresh seeds (5000+, 240 games): **+230 ± 134 (t=1.72)**, bust-outs 0.008 → 0.000, clears 15.00 → 15.18. Pooled 480 paired games: ≈ +244 ± 103, t ≈ 2.4. |

## Baseline, shipped build (240 games, end bonus OFF, stay-anywhere, completions forced)

```
mean 17428 ± 187   sd 2890   p10 13700   perfect-lives 0.704   bust-outs 0.008
busts/game 0.36   stays/game 1.21   clears/game 15.00   streak bonus/game 11009   mean best streak 11.7
```

