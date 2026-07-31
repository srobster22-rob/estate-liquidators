# Kalshi Bot Factory

A loop that builds trading bots for Kalshi event contracts — every market family against
every strategy family — backtests them against a market simulator, and then tries as hard
as it can to disqualify them. It keeps breeding and widening the search until something
clears a ten-criterion gate, or until the generation budget runs out.

**Status: the loop works and it produces bots that clear the gate. The gate is a statement
about a simulator, not about Kalshi.** That distinction is the most important thing on this
page and §[What this does not prove](#what-this-does-not-prove) is not boilerplate.

Runs on Python 3.11+ with **no dependencies** — same rule as `sim/`. `cryptography` is
needed only if you place authenticated orders.

---

## Run it

```bash
python -m kalshi.selftest          # 57 harness checks. Run this FIRST and always.
python -m kalshi.factory           # the loop; writes RESULTS.md + results.json
python -m kalshi.factory --sweep   # 9x12 coverage matrix; writes COVERAGE.md
python -m kalshi.capacity          # dollars per year, not percent; writes CAPACITY.md
python -m kalshi.fees              # what the fee formula does to every price
python -m kalshi.markets           # the market families and their planted edges
python -m kalshi.strategies        # the strategy zoo and the size of the search space

python -m kalshi.factory --keep-going          # don't stop at the first winner
python -m kalshi.factory --generations 20      # longer search
python -m kalshi.factory --quick               # seconds, for checking wiring

python -m kalshi.live --check                  # can this machine reach Kalshi?
python -m kalshi.live --record TICKER --samples 500 --interval 60
python -m kalshi.live --replay rec.jsonl --bot 'hold_favorite(thresh=95,qty=25)'
```

`selftest.py` failing means nothing else here is trustworthy. It is not a formality — four
of its checks caught real bugs while this was being built, and two of those bugs were in the
checks themselves.

---

## What's here

| File | What it is |
|---|---|
| `config.json` | Every constant the backtester or gate depends on. Canonical, like `tuning.json`. |
| `fees.py` | Kalshi's fee formula, with worked examples. The most important file. |
| `paths.py` | The latent price engine. Prices are a martingale *by construction*. |
| `markets.py` | Nine market families, the quoting layer, and every planted edge. |
| `strategies.py` | Twelve strategies, five of them controls designed to lose. |
| `backtest.py` | Execution: spread, depth, fees, maker fills, no lookahead. |
| `evaluate.py` | The gate. Bootstrap, Holm correction, stress, tail risk, half-edge. |
| `factory.py` | The loop: build → screen → validate → correct → confirm → expand. |
| `live.py` | Kalshi REST adapter: check, record, replay, paper, live. |
| `capacity.py` | Turns a percentage return into dollars per year. Read it before believing one. |
| `selftest.py` | 57 checks that have to pass before any of the above means anything. |
| `RESULTS.md` | Output of the last full run. Generated. |
| `COVERAGE.md` | Every family × strategy, in-sample. Generated. |
| `CAPACITY.md` | What the winners are worth in dollars a year. Generated. |

---

## The market families

Nine, spanning what Kalshi lists — plus one that exists only to catch bugs.

| family | horizon | turns/yr | planted bias | why it's here |
|---|---|---|---|---|
| `crypto_hourly` | 1 h | 8760 | tiny | most efficient thing on the exchange; recycles capital constantly |
| `index_bracket_daily` | 6.5 h | 1348 | tiny + incoherent brackets | the only family where riskless arbitrage is structurally possible |
| `econ_print` | 10 h | 876 | small, big quote lag | 90% of the uncertainty lands in one step |
| `weather_temp` | 2 d | 182 | moderate | uncertainty resolves late as forecasts sharpen |
| `sports_game` | 3 h | 2920 | strong | scores are jumps; retail pricing most plausible |
| `politics_long` | 90 d | 4 | strong | biggest gross edges, worst capital efficiency |
| `awards_thin` | 60 d | 6 | worst on the exchange | tests whether a big edge in a 30-lot book is a business |
| `mentions_short` | 6 d | 63 | strong | thin-family mispricing at 60 turns a year instead of 4 |
| `efficient_control` | 1 h | 8760 | **none, by construction** | a tripwire. Profit here is impossible; measuring it means the harness broke |

Every family is the same construction — a Gaussian random walk, with the event being
`{walk ends above a strike}` — differing only in **when information arrives** (smoothly, in
one shock, accelerating, in jumps, or slowly) and in microstructure. That makes the price a
martingale for free, with no parameter to tune wrong, and it makes the series perfectly
calibrated: contracts quoted at 30 resolve YES 30% of the time. Both are asserted
numerically in `selftest.py`, because a simulator that fails either one will hand a bot
factory infinite money.

---

## What the loop found

From the run in `RESULTS.md` (seed 20260730). Simulated markets throughout.

**1. Fees decide almost everything, and they decide it before any strategy is written.**
The fee is `0.07 × contracts × P × (1−P)`, which peaks at mid-book: a round trip at 50¢
costs 3.50¢ of a 100¢ notional, and at 5¢ it costs 0.68¢. Every round-trip strategy in the
zoo — `momentum`, `mean_revert`, `jump_follow`, `jump_fade` — is negative on **every one of
the nine families**, including the ones with a 3¢ mispricing planted in them. They are not
losing to the market; they are losing to the fee, twice per trade. Hold-to-settlement pays
the fee once and never crosses the spread to exit, and every bot that passed the gate is a
hold-to-settlement bot. That is the single most transferable result here, because it depends
on the published fee schedule rather than on anything this simulator invented.

**2. Order size is free alpha, because the fee ceiling is charged per order.** One contract
at 5¢ owes 0.33¢ and is charged 1¢ — a 3× tax with no relationship to edge. A hundred
contracts pay 0.34¢ each. Order size was left as a searched parameter rather than a
constant, and the loop reliably prefers the larger sizes.

**3. "Buy YES and NO for under 100" cannot exist on Kalshi, and `pair_arb` proves it.**
Kalshi runs one book per market: a YES bid at 40 *is* a NO ask at 60. So
`yes_ask + no_ask = 100 + spread ≥ 100` identically. `pair_arb` was implemented anyway and
found **0 opportunities across 5,200 market-lives**, in all nine families. Bracket
arbitrage across a mutually exclusive *set* is a different matter and it is real: buying all
five closing-range brackets when their asks sum below 100 is riskless, fully collateralised,
and worth **+2.22¢ per market offered** out-of-sample. But it fires in only **40 of 1,200
bracket sets (3.3%)**, which is why it never even reached the out-of-sample stage in the
factory run — at 300 in-sample markets it does not trade often enough to clear the minimum
trade count. Real, riskless, and rate-limited by how rarely the exchange is incoherent.

**4. The biggest gross edge on the exchange is the worst business on it.** `awards_thin`
carries the largest planted mispricing of any family (~3.4¢ on a 10¢ contract) and produced
**nothing**. Two reasons, both structural: a 10–60 contract book means you cannot take size,
and 60 days of locked collateral means the same edge turns over 6 times a year instead of
876. `politics_long` fails the same way. Depth limits and capital lockup, not the size of the
mispricing, decide which family is tradeable.

**5. Kalshi's price grid is itself an edge, and nobody planted it.** Prices live on 1…99.
A contract whose true probability is 99.8% can only be quoted at 99, so it is structurally
underpriced by 0.8¢; a contract worth 0.2% must still trade at 1¢ or better. This shows up
in `efficient_control`, where the bias is *exactly zero* by construction — measured at
**+1.13¢ below 2¢ and −0.12¢ above it**. It was found by a self-test failing and being
misread as a broken control. Both bots that passed the gate trade in that boundary region.
Real feature of the exchange; also the most fragile result here, since it lives entirely in
prices where a real book has almost no size.

**6. The goal was reached in generation 0 — and that is a warning, not a win.**
Three bots cleared all ten criteria: `hold_favorite(thresh=95)` and `band_fade(lo=5,hi=8)`
on `econ_print`, at **+85.6¢** and **+33.1¢** per market offered out-of-sample, Holm-adjusted
p = 0.006 over 12 tests, holding up on the holdout (+53.3¢) and under stress (+43.0¢). But
three bots is **two mechanisms**. Run with `--keep-going` for the full 12 generations, the
loop built **718 bots, ran 142 out-of-sample tests, and passed 28 of them — and those 28 are
still only 3 mechanisms, all on `econ_print`.** It also touched the holdout 29 times, at
which point the holdout is a second validation set rather than an untouched one, and the
report says so. A bot factory's headline count measures how many parameter variants it tried,
not how many things it found; the default run stops at the goal precisely to keep the third
dataset clean.

**7. The whole result is a levered bet on a number I chose by hand.** The gate now re-runs
every winner against a *paired* world — identical markets, identical spreads, depth and fees,
with only the planted inefficiency scaled down. All three winners collapse the same way:

| planted edge | `hold_favorite(95)` | `band_fade(5,8)` |
|---|---|---|
| 100% | +84.3¢ | +33.1¢ |
| 75% | +61.2¢ | +20.9¢ |
| 50% | +23.2¢ | +9.7¢ |
| 25% | −11.0¢ | −0.4¢ |

Costs are **fixed** — spread and fee do not shrink when the edge does — so net edge is gross
minus a constant, which makes it a *levered* function of the assumption. Halving the assumed
inefficiency does not halve the profit; it removes about three quarters of it, and every bot
goes negative somewhere between 25% and 50%. So the real claim these bots make is narrow:
*if* Kalshi's actual mispricing is at least ~40% of what `markets.py` guesses, they work.
That table, not the p-value, is the honest measure of how much any of this depends on
magnitudes nobody has measured.

**8. It is a $214-a-year business.** `RESULTS.md` reports the winner at +4552%/yr, which is
arithmetically correct and nearly useless. `python -m kalshi.capacity` asks the two questions
that decide whether a strategy is worth building — how many such markets exist, and how much
size the book holds where the edge lives — and the answer is **$214/year on $52 of committed
capital**, because `econ_print` lists ~250 markets a year and the book holds ~55 contracts at
the price the edge lives at. The percentage is a return measured over the 9% of the year the
capital is deployed; the rest of the time it earns nothing. Both numbers describe the same
bot and only one of them tells you whether to build it. The two ways it improves are the same
inefficiency in a family that lists more markets, or at a price where the book is deeper —
neither is a tuning problem.

**9. The best-looking bot in the entire coverage sweep is on the market that cannot be
beaten.** In the 9 × 12 matrix, the highest in-sample cell of all 100 is
`efficient_control / hold_favorite` at **+422¢ per market** — on a market with γ = 1.0, no
quote lag and a penny spread, where profit is impossible by construction. `buy_longshot`,
a control written to lose, tops the `crypto_hourly` column. This is what the maximum of a
wide search looks like when there is nothing there, and it is the reason every number in
`COVERAGE.md` is labelled as a direction rather than a result.

---

## The gate

Ten criteria. All of them, or it is not a pass.

| # | criterion | what it stops |
|---|---|---|
| 1 | ≥200 out-of-sample trades | an edge measured over 40 trades is not measured |
| 2 | positive mean per market **offered** (declines count as zeros) | flattering a selective bot |
| 3 | bootstrap 95% lower bound > 0, resampling **groups** | claiming 5× the evidence when a bracket arb takes 5 legs |
| 4 | **Holm**-adjusted p < 0.05 over *every* OOS test in the run | the whole search being hidden behind one lucky result |
| 5 | holdout confirms the sign | fitting the out-of-sample set |
| 6 | survives 1.5× fees, +1 tick spread, halved maker fills | an edge that was really an assumption |
| 7 | annualised return on locked capital ≥ 5% | a real edge that cannot pay for the collateral it ties up |
| 8 | ≥100 holdout trades | a confirmation too small to confirm |
| 9 | profitable at the **Wilson upper bound on the loss rate** | 99.3% win rates whose entire risk rests on 7 observed losses |
| 10 | profitable in a **half-edge world** (paired: same markets, planted edge halved) | a result that is really a bet on the magnitudes in `markets.py` |

Three of these were added *because the gate was passed* — every time this thing clears its
own bar, the first question is what the bar failed to ask. Criterion 4 was originally
Benjamini-Hochberg, which controls the false discovery *rate* — correct for a portfolio of
findings, wrong here, because the factory funds one bot and a single false discovery is the
entire failure. Criterion 9 did not exist until the first three winners turned out to win
99.3% of the time and hand back most of the position on the other 0.7%: seven observed
losses in 1200 markets, and nothing else in the gate noticed. Criterion 10 came last: the
other nine all test whether the bot is real *given* the simulator, and none of them tests
whether the simulator's magnitudes are.

**Selection is in-sample only, including breeding.** `_breed` is not given access to
out-of-sample results. The moment a survivor is bred from its OOS score, OOS has been fitted
and the number in the report is decoration.

---

## What this does not prove

Read this before quoting any number above.

**The edges were planted by hand.** `markets.py` inserts longshot compression, a capped
quote lag, bracket incoherence and wide spreads, at magnitudes chosen for plausibility. The
factory then rediscovers them. That is a real test of the *harness* — it shows the machinery
finds a known edge, correctly signs it, and prices it after fees, spreads and depth — and it
is **not evidence that those inefficiencies exist on Kalshi**, at those magnitudes or at
all. A bot passing the gate has proven it can harvest a specified inefficiency, not that the
inefficiency is out there.

**Two things are unverified because this machine has no network access:**

1. **The fee schedule.** `fees.taker_rate = 0.07` and the maker schedule come from general
   knowledge, not a live read of Kalshi's published rates. Fees are the largest single
   determinant of every result on this page. Re-read the fee schedule and correct
   `config.json` before trusting anything.
2. **The whole of `live.py`.** Endpoint paths, field names and the RSA-PSS signature
   construction are unverified against a live server. `--check` prints what it actually got
   back and warns on missing fields. The offline `--replay` path *is* tested.

**Also not modelled:** market impact beyond depth-at-touch, a shared bankroll across
simultaneous markets (so no compounding and no path to ruin — sizing is a separate problem
this project does not solve), queue position, outages, rejected orders, exchange position
limits, and adverse selection beyond what the maker fill rule encodes.
`maker_benign_fill_rate = 0.35` is a **guess**, and every market-making number here is
downstream of it.

### Turning this into a real result

The path exists and it is not short:

1. `python -m kalshi.live --check` — confirm the API shape on a machine with egress.
2. Correct the fee schedule in `config.json` against Kalshi's published rates.
3. `--record` on a cron job for weeks, across several families. Books, not just prices.
4. `--replay` the recording through the *same* strategy objects and the *same* fee model.
   The replay path reuses `backtest.run` unmodified so a bot cannot behave one way in the
   simulator and another on real data.
5. Only then ask whether the gate passes. Expect it not to.

**On real money:** paper mode is the default; `--live` also requires
`KALSHI_ALLOW_LIVE_ORDERS=yes` in the environment and caps notional at $5 unless raised.
Nothing in this directory has been validated against real market data, and event contracts
are a leveraged, all-or-nothing instrument. A simulated edge that survives nine criteria on
data you generated yourself is a reason to go collect real data — not a reason to fund a bot.
