# cryptobot — a strategy factory that tries very hard to kill its own bots

Breeds trading bots across many market types and strategy families, tests each
survivor on data the search never saw, and keeps expanding until something passes
every gate — or until the budget runs out and the honest answer is *nothing here
beat the null*.

Standard library only. No numpy, no pandas, no network required.

```bash
python3 -m unittest cryptobot.test_cryptobot     # 46 tests, ~10s
python3 -m cryptobot.run null-test               # calibration: run this FIRST
python3 -m cryptobot.run evolve --markets synthetic
python3 -m cryptobot.run report
```

---

## Read this before you read a result

**A backtest cannot prove profit.** It can only fail to disprove it. Everything
below is built to make that failure as hard as possible, and the honest ceiling of
what a passing bot has earned is *a paper-trading period, then a small allocation
with a kill switch* — not a large one.

The specific danger with "keep making bots until one is profitable" is that it
**always succeeds**. Generate ten thousand strategies on noise, keep the best, and
its backtest Sharpe will be around 3.9 — not because it has an edge, but because
the maximum of ten thousand draws from a zero-mean distribution is a large number.
A loop with a weak validator does not find edges. It finds the strategies best at
fooling the validator, and it finds them *faster the harder it searches*.

So the loop here is built the other way around. The search may expand as much as it
likes; the bar rises with it, and the bar is never lowered.

---

## How it works

```
        TRAIN (50%)              VALIDATION (25%)           VAULT (25%)
   ┌──────────────────┐  ~500   ┌──────────────┐  ~500   ┌──────────────┐
   │ the search lives │ embargo │ the gauntlet │ embargo │  one-shot    │
   │ here, unlimited  │  bars   │ 11 gates     │  bars   │  confirmation│
   └──────────────────┘         └──────────────┘         └──────────────┘
```

Each generation: score the population in sample, promote the best few to the
gauntlet, breed the survivors, and expand the search if progress has stalled.
Anything that clears all eleven gates gets one shot at the vault.

### The expansion ladder

| Stage | What opens up |
|---|---|
| 0 | four markets, tier-0 strategies |
| 1 | the full market universe |
| 2 | tier-1 strategies (pairs, regime-filtered hybrids) |
| 3 | two-strategy ensembles |
| 4 | tier-2 strategies, larger population, higher mutation |
| 5 | wider risk envelope, heavy immigration |

Expansion adds *search breadth only*. It never touches a threshold. If the loop
could eventually lower the bar, running it until something passes would be
guaranteed to succeed and guaranteed to mean nothing.

### The eleven gates

| # | Gate | What it kills |
|---|---|---|
| 1 | `sanity` | bots with three trades and a fluke |
| 2 | `oos_profit` | bots that only worked in the training window |
| 3 | `wf_efficiency` | bots whose OOS is a fraction of their IS — overfit by definition |
| 4 | `beats_benchmark` | bots that made money because the coin went up |
| 5 | `drawdown` | bots nobody could hold through |
| 6 | `cost_stress` | bots living inside the fee assumption (2x and 3x costs) |
| 7 | `lag_robust` | bots that need fills nobody can get |
| 8 | `param_robust` | bots perched on a knife-edge in parameter space (±20% nudges) |
| 9 | `regime_consist` | bots that caught one move and gave it back |
| 10 | `deflated_sharpe` | bots that are just the maximum of N draws from noise |
| 11 | `mc_timing` | bots whose "edge" is exposure, not timing |

### Why the search optimises alpha, not Sharpe

The first working version had the search and the gauntlet pulling in opposite
directions: fitness rewarded raw Sharpe, so the population filled with bots riding
a trend with size — and gates 4 and 11 then killed them for failing to beat
buy-and-hold, or for losing to random signals with their own exposure profile. A
quarter of everything promoted died there.

So fitness scores each bot twice: raw Sharpe, and the Sharpe of its returns after
regressing out its market exposure. **The score is the worse of the two.** The gates
are a conjunction, so the search may as well optimise for that from the start.

Fitness also charges for *inconsistency* — the realised return series is split into
four blocks and the dispersion of their Sharpes is penalised. Selecting on raw
in-sample Sharpe is how the first version produced a population with in-sample
Sharpe 5.6 and out-of-sample Sharpe −1.4: the maximum of thousands of noisy
estimates is a measure of luck, and a genetic search compounds it every generation.
With the consistency term, in-sample best on null data fell from 4.26 to 1.79.

### Gate 11's null

Gate 11 is worth a note: the null it tests against isn't a coin flip, it's **random
signals matched to the candidate's own trading profile** — same fraction of bars
long, short and flat, same switching frequency, same fees paid. If the candidate
can't beat a bot that trades exactly as often as it does but has no idea when, then
what it found was exposure, not timing.

### What deflates the Sharpe, and why it isn't every trial

The intuitive move is to deflate by every bot the factory ever evaluated. It is also
wrong, and unusably strict. Under the null of no edge, a bot's **out-of-sample**
Sharpe is centred on zero *however it was chosen* — selecting it by maximising
in-sample fitness biases the in-sample estimate, not the out-of-sample one. That is
the entire reason for holding data back.

What must be paid for is the number of times the held-out data is **consulted**.
Test 200 candidates against the validation slice and the best of them is the maximum
of 200 draws. So gate 10 deflates by `oos_looks`, with the dispersion measured from
the out-of-sample Sharpes of every look — passes and failures alike, because keeping
only the winners' would understate the spread and quietly lower the hurdle.

Both counters live in `state/factory_state.json` and **persist across runs**.
Restarting the factory twenty times does not buy twenty fresh chances. Deleting that
file is lying to yourself about how hard you looked.

### The vault is a consumable

The final slice is touched only by a candidate that has already passed everything
else, and every use is logged permanently. Test against it twenty times and it has
quietly become a second validation set. `report` warns past ten burns; there is no
way to reset the counter that doesn't involve deliberately editing the state file.

---

## Calibration: the number that makes the rest meaningful

```bash
python3 -m cryptobot.run null-test
```

This points the whole factory at markets built with **no directional predictability
at all** — GARCH volatility clustering, fat tails, regime-switching vol, and zero
drift in every regime. Anything that passes is a false positive by construction, and
the count is the factory's false-positive rate.

Latest run: **0 false positives across 2 null runs.** The in-sample search still
reached fitness ~1.0 on that data, and every candidate it promoted died out of
sample — most at gate 2, having posted an out-of-sample Sharpe near 0.2. That gap
between what the search finds and what survives is the entire point.

Run this after any change to `validate.py`. A validator that passes bots on
structureless data invalidates every result the factory has ever produced.

The other half of the calibration runs in the test suite: on the synthetic markets
that *do* have added structure, a plain unfitted probe must clear costs
(`test_structured_markets_carry_a_reachable_edge`). Without that check, a rigged
universe where nothing is reachable would make a broken factory look appropriately
sceptical.

---

## A recorded run

400 generations, population 70, on the 30-market universe. **37,020 in-sample
trials, 140 out-of-sample looks, 2 vault burns — one confirmed bot.**

```
donchian @ largecap_alt_1h        train 4.24 | validation 5.46 | vault 5.31
                                  CAGR 2.25 | max DD 0.129 | 136 trades
                                  DSR 1.000, confirmed at look 5 / burn 2
```

It landed on a market with real structure and claimed nothing in the twelve that
have none.

### Where the 138 rejected candidates died

```
  79  deflated_sharpe      <- gate 10 does most of the killing, as designed
  17  oos_profit
  15  cost_stress
  11  sanity
   6  regime_consist
   6  drawdown
   1  each: wf_efficiency, mc_timing, lag_robust, beats_benchmark
```

### This run replaced a three-bot result, and that is the point

The identical configuration previously returned **three** bots with near-zero
pairwise correlation — a much better-looking answer. It was substantially an
artifact. An adversarial audit found that gate 10's hurdle *fell* as the search
looked harder: the dispersion estimate switched from the in-sample pool to the
out-of-sample one the moment the 5th sample arrived, and a standard deviation from
five observations is noisy enough that the bar dropped 55% in a single step, from
2.80 to 1.25. A candidate posting 3.0 failed as the 5th look and its twin passed as
the 6th.

With the bar repaired — shrinkage instead of a switch, plus a persisted high-water
mark so it can never fall — gate 10's kill count went from 26 to 79 and two of the
three bots went with it. **Two thirds of that result was the broken hurdle.**

The same audit found the strict null was not null in the space where P&L is
measured: returns are generated in log space with zero drift, but P&L is earned in
simple returns, and E[exp(r)-1] = exp(sigma^2/2)-1 is a 21%/year premium to anything
permanently long at 65% vol. Every false-positive number quoted before that fix was
measured against a market that quietly paid for exposure. With the Ito correction
the residual drift across 24 null markets is t = +0.19 +/- 0.18, and the calibration
re-run still returns 0 false positives — now earned rather than inherited.

Eleven defects survived refutation out of thirty reported; all are fixed and listed
in the commit log. The two above are the ones that changed a published number.

### About that Sharpe

5.3 is not a plausible number for a real market and is not a claim about one.
`largecap_alt_1h` is a series this repo generated with a trend component this repo
inserted at a strength this repo chose. What the run establishes is that the
machinery works end to end and that its own reported numbers survive being attacked.

---

## Markets

`--markets synthetic` builds fourteen markets spanning the behaviours that matter —
slow majors, high-beta alts, funding-bearing perps, fast timeframes where costs
dominate, slow timeframes where sample size does — across 15m/1h/4h/1d.

**Five have deliberately added structure; nine have none.** `universe.STRUCTURED`
names them, which makes a synthetic run auditable in a way no real market ever is:
a factory that finds "edges" spread evenly across all fourteen is overfitting.

One of the five, `smallcap_alt_1h`, has a genuine reversion edge sitting behind
30bps of round-trip cost that eats it completely. The correct verdict there is *real
pattern, don't trade it* — it is in the universe precisely because that is the
verdict an optimistic fee model gets wrong.

The generator's edge knobs were calibrated, not guessed: probed with hand-written
unfitted bots and adjusted until they reached ~1.0–2.5 Sharpe. Note what does *not*
work — one-lag autocorrelation. On hourly bars, φ=0.05 is worth ~3bps of expected
move against ~9bps of round-trip cost and decays to nothing by the third bar. Real
trend edges are *persistent drift*, which is what `trend_strength` models.

### Real data

```bash
python3 -m cryptobot.run fetch --venue binance --symbol BTCUSDT --interval 1h
python3 -m cryptobot.run evolve --markets real
```

Public candle endpoints for Binance (spot and perp, with real funding history
prorated per bar), Coinbase and Kraken. Results are cached as CSV; a market is
loaded from cache if present. **If a venue is unreachable the fetch raises** rather
than substituting synthetic data — that substitution is how people end up trading a
backtest of a random number generator.

Own data: name files `venue_SYMBOL_interval.csv` with columns
`ts,open,high,low,close,volume[,funding]` and point `--markets csv:<dir>` at them.

> This sandbox blocks outbound access to exchange APIs, so every run recorded here
> is synthetic. A synthetic pass proves the harness works and **nothing else**.

---

## What the engine charges you

- **Fees** — taker, one side, per venue, in bps of traded notional
- **Spread** — half-spread crossed on every trade
- **Impact** — *quadratic* in turnover, so doubling size costs four times the
  slippage. Deliberately pessimistic; it's what stops the optimiser discovering
  that flipping the whole book every bar is free money.
- **Funding** — charged every bar a perp position is open, longs pay, shorts
  receive. That one line is why carry strategies here aren't free money.
- **Ruin** — absolute. Equity at zero ends the run.

Position sizing is volatility-targeted from *trailing* realised vol, so a quiet
market and a wild one carry the same risk budget and the optimiser can't discover
that leverage is alpha.

Timing convention, obeyed everywhere: `signal[i]` is decided at the close of bar `i`
from bars `0..i`, established at that close paying costs, and earns the return from
`close[i]` to `close[i+1]`. Gate 7 re-runs everything a bar later and discards
anything that only works at zero latency.

---

## The test that matters most

`test_every_strategy_every_kind` truncates each market at bar *k* and checks that
every strategy's first *k* signals are bit-identical to the first *k* signals
computed on the full history. A lookahead bug is invisible in a backtest and fatal
in live trading; that test is the only thing standing between the two.

The suite also verifies that fees are charged to the basis point, that funding is
debited to longs, that ruin is terminal, that a genome round-trips through JSON and
reproduces exactly, and — importantly — that the gauntlet **rejects** a strategy
mined on a random walk while still **passing** the early gates on a market with an
obvious edge. A validator nothing can ever pass is as useless as one everything can.

---

## Files

| File | What's in it |
|---|---|
| `data.py` | Market object, CSV cache, exchange fetchers, the synthetic generator |
| `indicators.py` | O(n) causal indicators, memoised per market |
| `strategies.py` | The zoo: trend, breakout, reversion, carry, cross-sectional, hybrid |
| `backtest.py` | Sizing, costs, funding, stops, metrics |
| `stats.py` | Deflated Sharpe, expected-max-Sharpe, stationary bootstrap, matched nulls |
| `universe.py` | Market universe, three-way split with embargo, regime blocks |
| `bot.py` | The genome, and the fitness function the search maximises |
| `validate.py` | The eleven gates |
| `evolve.py` | The loop: breed, promote, expand, persist |
| `run.py` | CLI |
| `test_cryptobot.py` | 46 tests |

---

## Why a run can come back empty, and what to do about it

Gate 10 needs the observed Sharpe to clear its hurdle by about 1.645 standard
errors, and the standard error of a Sharpe estimate is `sqrt((1 + S²/2) / years)`.
Over a three-month validation window that error is ~2.0 — larger than any edge worth
trading. **A short history makes the gate unpassable no matter how good the bot is**,
which is why every synthetic market here spans 5+ years and why a daily-bar market
needs ~12 years to be splittable at all (run.py skips it with a message if it
isn't).

When a candidate fails gate 10 the output prints what it *would* have needed:

```
[FAIL] deflated_sharpe  dsr=0.729 oos_looks=7 hurdle_sharpe=1.387
                        observed=2.045 needed=3.184 oos_years=0.86
```

Read that as: over ten months, with seven looks spent, a 2.0 Sharpe is not
distinguishable from luck — you need a 3.2, or more data. The two honest responses
are **more history** and **fewer looks** (each look raises the hurdle for everyone
after it, which is why promotion is capped at two per five generations and
deduplicated by market and strategy). Lowering `min_dsr` is a third option and it is
not an honest one.

## Honest limitations

- **No live execution.** No order router, no exchange keys, no position
  reconciliation, no kill switch. This finds candidates; it does not trade them.
- **Bar-level fills.** Stops fill at the stop price or the next open, whichever is
  worse. Real intrabar path risk is worse than that.
- **No cross-sectional portfolio.** Bots are single-market (pairs trades excepted).
  No correlation budgeting across a fleet.
- **Impact is a guess.** The quadratic coefficient is pessimistic-by-choice, not
  measured against a real order book.
- **Survivorship.** The real universe list is today's liquid pairs. Backtesting them
  over years silently excludes everything that died.
- **A pass is not a prediction.** Regimes change, edges get arbitraged, fee
  schedules change, and the sample is always finite.
