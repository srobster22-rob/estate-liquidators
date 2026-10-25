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

## Round 2 — cloud session, 2026-10-25 (rebuilt copy, 4-core box, `--workers=2`)

**Reproduction check.** The rebuilt `index.html` on seeds 1000-1239 scores **17,427.7**, the
PC's figure above to the decimal, with every secondary metric identical (perfect-lives 0.704,
bust-outs 0.008, busts 0.36, stays 1.21, clears 15.00, streak bonus 11,009, best streak 11.69).
The exact solver's wall-clock deadline does not bind on either machine at this load, so runs
here are comparable to runs on the PC.

| # | hypothesis | result | verdict |
|---|---|---|---|
| R | A rollout that plays out the whole remaining deck still scores `stateValue` (+500 per life, +60 per stay), but this game pays nothing for either at the end. Score deck-end rollouts as the game does. | +15.8 ± 32.7 (t=0.48); **218/240 games identical**; busts 0.36 → 0.47, stays 1.21 → 1.10, perfect-lives 0.704 → 0.621 | **null at game level** — it changes only a few late decisions (it now spends a worthless last life instead of a stay). Too small for a game A/B; sent to the decision-level oracle. |
| N | F cut sims AND exact budgets and lost 527; which half? Double the sims, SIMS 600 → 1200 (480 games). | −23 ± 111 (t=−0.21); 316/480 games differ; every secondary metric flat | **null — the Monte-Carlo search is saturated here too**, as in the parent. So F's −527 was the exact-budget cut: falling back to MC on the 9- and 10-card moves alone costs ~500/game, which says MC decisions just above the exact limit are far from optimal. Measured next with the oracle. |

**Finding: the "exact endgame" mostly does not run.** `bench/exactcov.js` (40 self-play games,
seeds 1000-1039) records whether `exactBest` finished or `chooseBest` fell back to MC:

| cards left | 10 | 9 | 8 | 7 |
|---|---|---|---|---|
| fell back to MC | **87%** | **64%** | 26% | 3% |

Every cut-off is the 800k node cap (`EXACT_NODE_CAP_DEEP`), not the clock — which is why runs on
the PC and here agree to the decimal. The 10- and 9-card moves spend ~1.5-2 s and then decide by
MC anyway. The parent tuned the cap for its game; here the state space is larger (stays are
searched freely in the last 8 cards, and with the streak in the key). Cutting STAYs out of the
search (`PASS_FULL_LIMIT` 8 → 0) does not fix it on its own: still 70-89% fallback at 10 cards.
So F's −527 is explained: its smaller budgets turned the 7- and 8-card solves, which do finish,
into MC as well.

**Making it finish.** In this game 10, J, Q and K are interchangeable (only aces and 7s have
rules), but the engine kept 13 rank counts, so drawing a J and drawing a Q reached two memo
entries for one position. **T** folds them into one ten-class (10 value classes). Exact values
are unchanged (`bench/exactsame.js`, 48 eight-card endgames: max difference 3.6e-12) and the
search needs 1.43× fewer nodes. Exact completion, 40 games, seeds 1000-1039 (`bench/covsum.js`):

| build | fell back at 10 | at 9 | at 8 | 10-card move, ms p50 / max (this box) |
|---|---|---|---|---|
| shipped | 87% | 64% | 26% | 1809 / 2730 |
| T (ten class) | 69% | 44% | 18% | 1577 / 2720 |
| T4 (T + stays searched only in the last 4 cards) | 69% | 38% | 15% | 1393 / 2372 |
| TC (T + node cap 800k → 2.4M, memo 2^21 → 2^22 = ~100 MB) | 56% | 28% | 15% | 3006 / 3183 (now the 3 s clock binds) |

| # | hypothesis | result | verdict |
|---|---|---|---|
| TC | If the exact solve finished more often at 9-10 cards, decisions there would improve (F lost 527 by finishing less often). | **+8.5 ± 5.4 (t=1.57), 468/480 games identical**; every secondary metric flat | **rejected** — when the exact solve now finishes where MC used to decide, it almost always picks the same move: MC at 9-10 cards is already near-exact. Not worth +1.2 s and +50 MB per game. It also means F's −527 was mostly its SIMS 600 → 300 (300 < 600 ≈ 1200), not the exact budgets. |
| T | Fold 10/J/Q/K into one class in the exact engine. | identical exact values (max diff 3.6e-12); 1.43× fewer nodes; 10-card move p50 1809 → 1577 ms; completion at 10/9/8: 87/64/26% → 69/44/18% fallback. Paired A/B **+4.2 ± 3.0 (t=1.39)**, 238/240 identical, wins 2-0; fuzz 0/325 | **SHIPPED as v4** — a pure speed-up: it cannot change a value, only finish more exact solves, and sooner. |
| D | Rollouts truncate at 22 cards and score a proxy that ignores the streak. Play every rollout to the deck end and score real points (R + DEPTH 52). | **−236 ± 127 (t=−1.86)**; busts 0.41 → **0.70**, bust-outs 0.008 → 0.019, perfect-lives 0.675 → 0.458, stays 1.22 → 1.06 | **rejected** — with real scores everywhere the +500/life proxy is gone, and the greedy rollouts almost never bust out (they stay whenever they can), so a lost life looks free and the root starts spending them. The life weight in `stateValue` is load-bearing, not just a horizon patch. Same direction as R's busts 0.36 → 0.47, at full strength. |
| K | A over-credited a live streak at the horizon. Credit it at its true size: a streak at x s beats a reset one only through the next 3 clears, +1000 / +1750 / +2250 for s = 1 / 2 / 3+, scaled by the clears the unplayed remainder can make. | **−106 ± 95 (t=−1.12)**; busts 0.41 → 0.45, stays 1.22 → 1.27 | **rejected** — A's pattern at half the size. "Streak alive at the horizon" is credited the same whether the board is clean or one card from a forced bust, so it rewards lines that kept the streak by sitting on high slots. Two sizings of a horizon streak credit have now lost; drop the idea. |
| W | The rollout policy paid extra for coverage while a streak was alive — a parent rule (there the streak died unless the NEXT card cleared). Here building keeps the streak, so drop that term. | −66 ± 113 (t=−0.59); 300/480 games differ, wins 150-150 | **null** — the parent's lesson again: rollout-policy edits do not move the search. |

## Shipped build after round 2: v4 = v3 + T (seeds 1000-1239, 240 games)

```
mean 17432 ± 187   bust-outs 0.008   busts/game 0.37   clears/game 15.00
```

Round 2 tested seven ideas on 3,120 paired games; only the speed-up survived. See LOOP_PROMPT.md
for what is now known not to work.

