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
likes; the bar is set by how many times the held-out data will be consulted, and the
search cannot lower it.

A caution earned the hard way: "the bar rises as you look harder" is the right
instinct and the wrong implementation. Raising it *during* a run makes a candidate's
verdict depend on when it happened to be promoted, which is luck, not evidence. The
bar is now computed once from the run's whole look budget and applied equally to
everyone. See "before and after a miscalibrated gate" below for what the wrong
version cost.

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
of 200 draws. So gate 10 deflates by the run's **look budget** — the same N for every
candidate, whether it arrives first or last.

The sigma in that correction is the one thing most easily got wrong. It must be the
dispersion of Sharpe estimates **under the null of no edge**, which is the sampling
error of a Sharpe over the window — `sqrt(1/T)`, about 0.56 over 3.1 years. It is
*not* the observed spread of the candidates that reached the gate: those are
survivors of an in-sample search, and their spread is dominated by real differences
in quality rather than by noise. Using it inflated this project's hurdle from 1.26
to 6.46 and demanded a 7.4 Sharpe before anything counted as real.

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

## A recorded run — before and after a miscalibrated gate

Same five seeds, same 65-market universe, same everything except gate 10:

```
seed        5    11    21    33    47
before      0     0     2     1     1     mean 0.80 +/- 0.84   (sd == mean)
after       4     6     4     6     5     mean 5.00 +/- 1.00   (sd == 20% of mean)
```

Six times the bots, and the run-to-run variance collapses from "the standard
deviation equals the mean" to a tight band. Distinct markets found goes from 3 to 8.
Every seed now finds something; before, two of five found nothing at all.

**The seed variance was never a property of the universe. It was the bug.** Several
earlier sections of this project's history explained that variance in terms of
markets, strategy families and history length. All of those explanations were wrong.

### The two bugs, and how they were found

The hunt started from a falsifiable claim — "the factory is hurdle-limited, so the
never-found markets should be exactly those below gate 10's bar" — and the test
refuted it. The bar computed out at **7.4 Sharpe**, which nothing in the universe
can reach, yet three markets were being found anyway. Something was inconsistent.

Checking *when* each winner was confirmed explained it:

```
seed 21   donchian@alt_perp_4h        look  1 of 41    validation Sharpe 1.89
seed 33   ts_momentum@alt_perp_4h     look  2 of 44    validation Sharpe 1.81
seed 104  ema_cross@largecap_alt_1h   look 15 of 44    validation Sharpe 4.66
seed 21   ensemble@largecap_alt_1h    look 23 of 41    validation Sharpe 5.30
```

Every confirmed bot arrived in the first half of its run, and the weakest arrived
first.

**Bug 1 — the wrong sigma.** The expected-max correction was fed the observed spread
of promoted candidates (~2.9). Those are survivors of an in-sample search: a mixed
population of genuinely good and genuinely awful bots, whose spread is dominated by
real quality differences. The correction asks a different question — *if these N
strategies all had zero edge, how good would the luckiest one look?* — and that is
the sampling error of a Sharpe estimate, which depends only on window length:
`sqrt(1/T)`, or **0.56** on a 3.1-year slice. The wrong sigma pushed the hurdle from
1.26 to 6.46.

**Bug 2 — the bar depended on arrival order.** Deflating by the *running* look count
meant the correction grew during a run, so a 1.8-Sharpe bot passed at look 1 while a
4.7-Sharpe bot was rejected at look 30 of the same run. That is not a
multiple-testing correction, it is a queue with statistical decoration.

Together they made the gate **lax early and impossible late** — worse than either
extreme, and undetectable from any single run's output.

### The fix lowers the bar fivefold, so the calibration was mandatory

`null-test` on structureless data, at the corrected hurdle and the same 110k-bar
length: **0 false positives across 3 runs, ~1,700 trials.** Lowering a hurdle is
exactly how a validator starts leaking, and this one does not.

### What the corrected factory finds

```
trend_fast_1h      4/5 seeds   REPRODUCED
largecap_alt_1h    4/5 seeds   REPRODUCED
largecap_alt_4h    2/5 seeds   REPRODUCED
trend_mid_4h       2/5 seeds   REPRODUCED
trend2_e, trend2_c, trend2_f, trend_slow_1h    1/5 each
```

Four of eight markets reproduce across independent trajectories, and 7 of 16 exact
genomes now repeat — up from 1 of 7. **Every market found is genuinely structured;
across all five seeds no decoy was ever selected.**

Vault burns rose to 6-10 per seed against a budget of 25, which is now the binding
constraint rather than the hurdle.

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
