# 21 STREAK solver — improvement loop

Paste this to continue improving the solver. It carries what the parent project
(`blackjack-solver`, the old "any non-21 breaks the streak" game) and this one learned, so a
fresh session does not repeat dead experiments.

---

Keep improving `index.html` for **mean final score in balanced mode** under this game's rules
(README "Rules modeled"). Loop in-turn: form a hypothesis, build `bench/cand_<x>.html`, measure
it, accept or reject, log it in `LEDGER.md`, repeat. Do not stop after one experiment.

## Rules of evidence

1. **Never accept a change without a paired A/B against the current build.**
   `node bench/par.js --a=index.html --b=bench/cand_x.html --games=240 --workers=W`
   `par.js` runs BOTH sides at once, so it starts `2 × W` worker threads: set `W` to half the
   cores (W=2 on the 4-core cloud box, W=10 on the owner's 24-thread PC).
2. **Never run two benchmarks at once**, and do not fuzz or time anything while one runs. The
   exact solver's deadline is wall-clock, so a loaded machine changes which searches truncate.
3. **Confirm anything you like on fresh seeds** (`--seed=5000`, then `--seed=9000`). In the
   parent, two changes with clean mechanism stories (+48, +96) collapsed on replication.
4. **t ≥ 2 pooled over the original and the confirmation run, or reject.** This game's paired
   standard error is large (~110 per 480 games for a change that touches most games: one
   diverging decision changes every later clear), so effects under ~100 points are invisible to
   game-level A/Bs. For narrow changes use `bench/oracle.js` (gen → diff → label → eval: exact
   regret on just the states where two builds disagree). Labelling costs ~5-120 s of CPU per
   state at 10-11 cards, far more when stays remain; it is resumable (`.part` file).
5. **`node bench/fuzz.js bench/cand_x.html` on every candidate** — 0 failures of 325.
6. **The harness must mirror the app.** `bench/game.js` reimplements `dealCard()`'s flow; if
   you touch a decision path outside `chooseBest` / `chooseForcedBust`, mirror it there.

## What this game is about

Streak bonus is ~11,000 of a ~17,400 mean. Past x3 every clear pays +1000 on top of its base,
and the streak survives building, so a STAY or a bust costs the ramp: +1000 / +1750 / +2250 of
future bonus for a streak at x1 / x2 / x3+ (if three more clears were coming), plus the stay or
the life. Clears per game (~15) are near the deck's packing ceiling.

## Already measured — do not re-run

| # | change | result |
|---|---|---|
| A | streak carry `min(rem/3.5,8) × bonus(s+1) × 0.5` in `stateValue` (≈2× too large) | −300 ± 176, rejected |
| C | lifeVal 500 → 1500 | −52 ± 125, null (flat, as in the parent) |
| F | SIMS 600 → 300 **and** exact budgets 3000/2500/1500/1000 → 900/700/500/400 ms | −527 ± 191, rejected — the search is not saturated here |
| S | STAY sends the card to any slot (rule fix) | −34 ± 119, shipped as the correct rule |
| G | completions always taken (the parent declined 21s to keep slots loaded) | +258 ± 157, replicated +230 ± 134, shipped |
| R | deck-end rollouts score real points (no lives/stays credit) | +16 ± 33, 218/240 identical, null |
| N | SIMS 600 → 1200 | −23 ± 111 (480), null: **the MC is saturated** |
| TC | ten-class + node cap 2.4M + memo 2^22, so the exact solve finishes more at 9-10 cards | +8.5 ± 5.4 (480), 468 identical: **MC at 9-10 cards is already near-exact** |
| T | 10/J/Q/K as one class in the exact engine | identical values, 1.43× fewer nodes: shipped as a speed-up |
| D | full-depth rollouts scored by real points | −236 ± 127 (480): busts 0.41 → 0.70. **The +500/life in `stateValue` is load-bearing** |
| K | horizon streak credit at its true size (1000/1750/2250) | −106 ± 95 (480): busts and stays up, like A. **Horizon streak credits are dead** |
| W | drop the parent's streak-coverage term from the rollout policy | −66 ± 113 (480), null |

Every change that raised busts/game lost (A, D, K); the one clear win (G) cut them. The exact
endgame falls back to MC 69/44/18% of the time at 10/9/8 cards even with T (node cap), and that
costs almost nothing (TC). Remaining untested levers: `lifeVal` / stays weight retuned with the
end bonus OFF (C was measured with it ON), and anything the owner reports from the table.

From the parent, still believed to hold: exact depth is exhausted at 10 cards (11-12 cost 3×
per card for nothing); rollout-policy tuning does not transfer into the search (+953
standalone → +18 inside it); 2-ply expectimax and two-stage sim allocation were dead ends.

## What has worked

Three of the parent's four wins and this project's G were **deletions of hand-written rules
that overrode the solver's computed values**, or rules carried over from the parent game whose
justification no longer holds here. When a comment says "what showed up at the table" or
reasons from the old streak rule, measure it.

## Ground truth

Rules are confirmed by the owner's play (README). If the owner reports a move that looks
wrong, reproduce it as a state, count how often the build makes that class of move
(`bench/decline.js` is the template), fix, and A/B. One such report (G) was worth more than
every self-directed experiment before it.
