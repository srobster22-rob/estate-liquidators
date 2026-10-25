# 21 STREAK Solver

Single-file HTML solver for the 4-slot "21" game **with the persistent-streak rules**. Tap the
card you were dealt and it tells you which slot to put it in (or which slot to STAY / clear).

- **`index.html`** — the app. Open it directly in a browser; no server or build needed.
- **`bench/`** — the measurement rig (see below).
- **`LEDGER.md`** — every change tested against this build, with measurements.

> **This copy was rebuilt in a cloud session (2026-10-25) from the 2026-09-14/15 session
> transcript**, because the original lives only on the owner's PC (`C:\Users\srobs\21-streak-solver`).
> The transcript held lines 60-1183 of the parent `blackjack-solver/index.html` verbatim, every
> bench file, and every patch the session applied; replaying them reproduces v1, v2 and v3 at
> exactly the PC's byte sizes **plus 251 bytes** — the one part not in the transcript was the
> parent's CSS block (lines 10-52), which was rewritten from the class names the markup uses.
> So the solver logic is byte-faithful and only the styling differs. Checked: `trace.js` on v2,
> seeds 2-5, reproduces the transcript's output line for line; fuzz 325/325. The parent as
> rebuilt is kept at `bench/parent/blackjack-solver-index.html`. `bench/gap2.js` was not recovered.

Forked from `../blackjack-solver/index.html` (the "any non-21 move breaks the streak" game).
The search machinery is identical; only the rules changed. `bench/patch_fork.py` and
`bench/patch_bench.py` are the exact diffs that produced this build.

## Rules modeled (from play, 2026-09-14)

| event | base | notes |
|---|---|---|
| exact 21 | 400 | |
| 7-7-7 | 600 | instead of 400 |
| 5 cards ≤ 21 | 800 | |
| 5 cards = 21 | 1000 | paid 2000 at streak x10, so base 1000 + the 1000 bonus |
| streak bonus | +0 / +250 / +500 / +1000 | on the 1st / 2nd / 3rd / 4th-and-every-later clear of a streak, so a plain 21 pays 400 / 650 / 900 / 1400 / 1400 … |

- **The streak is broken ONLY by a STAY (clear) or a bust.** Placing a card that does not
  clear a slot keeps the streak alive. That is the whole difference from the old game, and
  it is why streaks of x13+ happen here and could never exceed x4 there.
- 2 STAYs per game: clear a slot (streak resets), then the dealt card goes into **any** slot —
  the cleared one fresh, or another slot where it may even complete a 21 and start a new streak.
  The solver searches every (cleared slot, destination) pair; it shows "STAY SLOT i, then card to SLOT j".
- 3 lives; a bust clears the slot, costs a life and resets the streak (confirmed). 0 lives = game over.
- One 52-card deck, no reshuffle, **no early exit**: every dealt card must be played. When a
  card busts every slot and no stays remain, the solver picks the slot whose loss costs least.

- **No end bonus for finishing with lives** (confirmed). Lives only matter because 0 lives ends the game.
- **3 minutes on the clock** for the 52 cards: ~3.5 s per card including your taps, so solver
  latency matters; the app prints "solved in N ms" under every recommendation.
  Measured on an idle desktop (node, `bench/timing.js`): median move 46 ms, midgame mean 55 ms
  (max 157), the two exact-solve moves at 10 and 9 cards left 0.5-1.0 s, ~4 s of solver time per
  game. A phone is roughly 3-5x slower, so budget ~15-20 s of solver time in the 180 s.

Two rule toggles remain in the UI (bust resets streak: on; all-lives end bonus: off), both
confirmed by play — flip them only if the game changes. The solver, including the exact
endgame, honours both.

## What the rule change does to strategy

Under the old rule ~54% of clears earned no streak bonus, and the streak bonus was ~1,150 of
an ~8,400 mean. Here the streak is worth **10,750 of a 17,940 mean**: once you are past x3
every clear pays 1,400 (or 1,800 / 2,000 for 5-card wins), so the game is about never
resetting. A STAY mid-game costs far more than the slot it rescues. The solver's rollouts and
the exact endgame both price this directly; the ledger records what else was tried.

## Benchmarking

```bash
node bench/par.js --html=index.html --games=240 --workers=12
```

A/B two builds on identical deals (paired; reports `deltaMean ± stderr` and a t-statistic):

```bash
node bench/par.js --a=index.html --b=bench/cand.html --games=240 --workers=10
```

Other tools:

| command | what it does |
|---|---|
| `node bench/fuzz.js index.html` | legality fuzz over 325 reachable + extreme states in every mode; 0 failures required |
| `node bench/trace.js index.html 1` | prints one self-play game move by move (rules sanity check) |

`par.js` runs both sides of an A/B at once, so `--workers=W` starts `2W` threads: use half the
cores (`--workers=2` on a 4-core box, where 480 paired games take ~35 minutes).

| more tools | what it does |
|---|---|
| `node bench/exactcov.js index.html 10 1000` | how often the exact endgame finishes vs falls back to MC, by cards left |
| `node bench/exactsame.js a.html b.html bench/st10.json 12 2` | proves two builds give identical exact values (for pure speed-ups) |
| `node bench/oracle.js gen\|diff\|label\|eval ...` | decision-level grading against an unbounded exact solve (see the file header) |
| `node bench/timing.js index.html 3` | per-move latency by cards left |

A full game takes ~45 s of solver time on a loaded machine (the exact endgame gets 3 s per move
on the last 10 cards), so 240 games on 12 workers is ~15 minutes. **Never run two benchmarks at once** — the
exact solver's deadline is wall-clock, so an oversubscribed machine silently changes results.

## Baseline (240 games, balanced mode, end bonus OFF as in the real game)

```
mean 17428 ± 187   sd 2890   p10 13700   perfect-lives 0.704   bust-outs 0.008
busts/game 0.36   stays/game 1.21   clears/game 15.00   streak bonus/game 11009   mean best streak 11.7
```

Rows are the B side of `bench/r_ab_force.json`. **Completions are always taken** in this
build: the old solver declined 21s to keep slots loaded for back-to-back chains, which has no
value when the streak survives building (`LEDGER.md` G: +258, declines 30 → 0). (With the end bonus on it was 17940 ± 222,
`bench/r_base.json`.) A faster build (sub-second endgame) was tried and cost 527 points
(`LEDGER.md` F), so the shipped build keeps full search strength.
