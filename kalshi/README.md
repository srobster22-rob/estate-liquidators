# Kalshi Bot Factory

A loop that builds trading bots for Kalshi event contracts — every market family against
every strategy family — backtests them against a market simulator, and then tries as hard
as it can to disqualify them. It keeps breeding and widening the search until something
clears an eleven-criterion gate, or until the generation budget runs out.

**Status: the loop works and it produces bots that clear the gate. The gate is a statement
about a simulator, not about Kalshi.** That distinction is the most important thing on this
page and §[What this does not prove](#what-this-does-not-prove) is not boilerplate.

Runs on Python 3.11+ with **no dependencies** — same rule as `sim/`. `cryptography` is
needed only if you place authenticated orders.

---

## Run it

```bash
python -m kalshi.selftest          # 184 harness checks. Run this FIRST and always.
python -m kalshi.factory           # the loop; writes RESULTS.md + results.json
python -m kalshi.factory --sweep   # family x strategy coverage matrix; writes COVERAGE.md
python -m kalshi.capacity          # dollars per year, not percent; writes CAPACITY.md
python -m kalshi.portfolio         # combine bots across families; writes PORTFOLIO.md
python -m kalshi.census            # the counted market list; writes CENSUS.md
python -m kalshi.sensitivity       # what every assumption is worth; writes SENSITIVITY.md
python -m kalshi.arb               # why the riskless trade loses; writes ARB.md
python -m kalshi.coherence --cost  # the one measurement needing no settlement
python -m kalshi.coherence --selftest        # validate that instrument
python -m kalshi.frontier          # information cost I = s^2/e; writes FRONTIER.md
python -m kalshi.execution         # slippage vs partial fill; writes EXECUTION.md
python -m kalshi.fees              # what the fee formula does to every price
python -m kalshi.markets           # the market families and their planted edges
python -m kalshi.strategies        # the strategy zoo and the size of the search space

python -m kalshi.factory --keep-going          # don't stop at the first winner
python -m kalshi.factory --generations 20      # longer search
python -m kalshi.factory --quick               # seconds, for checking wiring

python -m kalshi.live --check                  # can this machine reach Kalshi?
python -m kalshi.live --demo --check           # same, against the demo exchange
python -m kalshi.live --record TICKER --samples 500 --interval 60
python -m kalshi.live --replay rec.jsonl --bot 'hold_favorite(thresh=95,qty=25)'
python -m kalshi.audit rec.jsonl               # measure the three conditions from real books
python -m kalshi.live --record-event KXBTCD-26AUG06 --samples 600
python -m kalshi.coherence rec.jsonl           # bracket coherence, no settlement needed
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
| `markets.py` | Eleven market families (ten plus a no-edge control), the quoting layer, and every planted edge. |
| `strategies.py` | Thirteen strategies, five of them controls designed to lose. |
| `backtest.py` | Execution: spread, depth, fees, maker fills, no lookahead. |
| `evaluate.py` | The gate. Bootstrap, Holm correction, stress, tail risk, half-edge. |
| `factory.py` | The loop: build → screen → validate → correct → confirm → expand. |
| `live.py` | Kalshi REST adapter: check, record, replay, paper, live. |
| `capacity.py` | Turns a percentage return into dollars per year. Read it before believing one. |
| `portfolio.py` | Combines confirmed bots across families. The dollar bar lives here. |
| `census.py` | The counted market list. The one input the dollar figure rests on. |
| `sensitivity.py` | Every assumption swept, and where each crosses the bar. |
| `arb.py` | The zero-variance trade, the leg-count arithmetic that kills it, and which incoherence channels can revive it. |
| `frontier.py` | Information cost `I = s²/e`: what makes an opportunity good, independent of how often it appears. |
| `audit.py` | Measures the three conditions from a real recording. Refuses bad data. |
| `coherence.py` | Bracket coherence from books alone — the one measurement needing no settled outcomes. Refuses partial sets. |
| `execution.py` | Marketable vs IOC limit: what a missed leg costs, and why it is not what finding 17 assumed. |
| `selftest.py` | 184 checks that have to pass before any of the above means anything. |
| `RESULTS.md` | Output of the last full run. Generated. |
| `COVERAGE.md` | Every family × strategy, in-sample. Generated. |
| `CAPACITY.md` | What the winners are worth in dollars a year. Generated. |
| `PORTFOLIO.md` | The combined book and whether it clears the money bar. Generated. |
| `CENSUS.md` | How many markets Kalshi actually lists, and the sources. Generated. |
| `SENSITIVITY.md` | What has to be true for the headline to hold. Generated. |
| `ARB.md` | Bracket arbitrage: margins, slippage, leg leverage, incoherence channels. Generated. |
| `FRONTIER.md` | Every strategy ranked by information cost, and the identity behind it. Generated. |
| `COHERENCE.md` | What it would cost to measure the bracket edge for real. Generated. |
| `EXECUTION.md` | Every execution mode on one basis, ranked by information cost. Generated. |

---

## The market families

Ten, spanning what Kalshi lists — plus one that exists only to catch bugs.

| family | horizon | turns/yr | planted bias | why it's here |
|---|---|---|---|---|
| `crypto_hourly` | 1 h | 8760 | tiny | most efficient thing on the exchange; recycles capital constantly |
| `index_bracket_daily` | 6.5 h | 1348 | tiny + incoherent brackets | brackets at low frequency; the family the arb was built on |
| `crypto_bracket_hourly` | 1 h | 8760 | tiny + a **tight** book | K23's failed prediction: brackets at 23× the frequency. Never fires on quote noise alone |
| `crypto_bracket_stale` | 1 h | 8760 | same book, **one leg frozen** | K24's paired control for it. Same salt, same 0.6¢ quotes, one difference — and the arb comes back |
| `econ_print` | 10 h | 876 | small, big quote lag | 90% of the uncertainty lands in one step; listed as a **ladder** of 4 nested thresholds |
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

`RESULTS.md`, `CAPACITY.md` and `PORTFOLIO.md` are that one seeded run and predate the two
bracket families added in K23/K24; `COVERAGE.md` covers all eleven. Findings 17–21 were
measured directly by `arb.py`, `frontier.py`, `coherence.py` and `execution.py` on fresh seeds
rather than by the factory loop — the bracket arb has never reached the factory's out-of-sample stage, because at 300
in-sample sets it does not fire often enough to clear the minimum trade count.

**1. Fees decide almost everything, and they decide it before any strategy is written.**
The fee is `0.07 × contracts × P × (1−P)`, which peaks at mid-book: a round trip at 50¢
costs 3.50¢ of a 100¢ notional, and at 5¢ it costs 0.68¢. Every round-trip strategy in the
zoo — `momentum`, `mean_revert`, `jump_follow`, `jump_fade` — is negative on **every one of
the tradeable families**, including the ones with a 3¢ mispricing planted in them. They are not
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
found **0 opportunities across 5,200 market-lives**, in every family. Bracket
arbitrage across a mutually exclusive *set* is a different matter and it is real: buying all
five closing-range brackets when their asks sum below 100 is riskless, fully collateralised,
and worth **+7.37¢ per market offered** out-of-sample. But it fires in only **40 of 1,200
bracket sets (3.3%)**, which is why it never even reached the out-of-sample stage in the
factory run — at 300 in-sample markets it does not trade often enough to clear the minimum
trade count. Real, riskless, and rate-limited by how rarely the exchange is incoherent.

That +7.37¢ was **+2.22¢ until the fee schedule was verified.** S&P 500 and Nasdaq-100 series
pay half the standard rate, `index_bracket_daily` models exactly those, and it had been
charged double for the entire project — understating the only riskless trade here by 3.3×.

**The "$55/yr" this used to claim was also wrong**, and by the same units bug K18 caught on the
econ ladders: 750 is a count of *contracts*, but the backtester measures per *set*, and a set
is 5 contracts. It is **150 sets a year, ~$8**. See finding 17 — the arb loses for a much more
interesting reason than its size.

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

**8. It is a $133-a-year business, and the $214 I first reported was my own bug.** `RESULTS.md` reports the winner at +4552%/yr, which is
arithmetically correct and nearly useless. `python -m kalshi.capacity` asks the two questions
that decide whether a strategy is worth building — how many such markets exist, and how much
size the book holds where the edge lives.

The first answer was **$214/year**, and it was wrong. `capacity.py` measured on the
out-of-sample set, which is where winners are *chosen*: a bot only becomes a winner if its OOS
numbers clear the gate, so the OOS mean of a winner is the maximum of a selected set. Measured
on the holdout it is 53.3¢ per market; on a fourth, never-touched seed range, 48.8¢. The
honest figure is **$133/year on $52 of committed capital**, and the headline was 60% too high.
It is fixed, and `selftest.py` now fails if capacity ever reads the OOS seeds again.

`econ_print` lists ~250 markets a year and the book holds ~55 contracts where the edge lives.
The percentage is a return measured over the 9% of the year the capital is deployed; the rest
of the time it earns nothing.

**9. Nothing beats it, and the reason is structural.** Asked to find something better than
$214/yr, the loop ran 14 generations, 814 bots and 164 out-of-sample tests and found nothing —
then a direct measurement of every family explained why. Kalshi's fee plus one spread crossing
costs roughly 1.5–3¢ a contract. Only `econ_print`'s planted edge (a 3¢ quote lag) clears that
bar, and `econ_print` is the *rarest* thing on the exchange at ~250 markets a year. The
families that list constantly have edges too small to pay for their own spread — measured, not
assumed: `crypto_hourly` is **negative at every threshold tested** on 8,000 markets. The
ceiling is the product of those two facts and no parameter search moves it.

The near-miss is the interesting part. `sports_game` — strong bias, deep book, 6,000 markets a
year — had received **zero out-of-sample slots in 164 tests**, because a global top-N ranking
let `econ_print` take 92 of them. Fixing that (slots are now stratified by family) and testing
it directly gave **+379.7¢/market, t=+2.40, $22,785/yr**. On an independent confirmation set it
was **+7.5¢, t=+0.05**. It was the maximum of 18 configs on a high-variance family, and the
confirmation step is the only reason it is in this paragraph instead of at the top of the page.

**10. The one number that decided it has now been counted: 534, not 250.** Annual income is
strictly linear in markets-per-year, which was the single input here that was a pure estimate,
so the whole result reduced to a counting question: the bot clears $250/yr **iff
`econ_print`-style markets number ≥ 469 a year**.

Kalshi's API returns 403 to everything in this environment, and so does `kalshi.com`, so the
count comes from published sources instead — headline figure from an academic dataset of
**2,668 settled contracts across 8 economic series, July 2021 – June 2026**. Sixty months is
exactly 5.0 years, so **534 contracts a year**, 2.1× the guess it replaces, and a *lower*
bound: eight series only, and the window includes Kalshi's small years.

At the replicated edge that gives **$292/yr** (95% CI $151–$421, p=0.0003, tail-adjusted
$147) — clearing both the $250 bar and the $214 that started this. **The bot did not get
better; the count got right.** The edge per market is unchanged and so is everything the gate
said about it.

The census also produced a second number: a Kalshi CPI market is a **ladder** — nested rungs
that all settle from one printed number — so 534 contracts is only ~**124 independent events**
a year (534 ÷ 124 = 4.3 rungs/event, consistent with the ~6-threshold ladders in published
Core CPI examples). See finding 12: the obvious conclusion from that turned out to be wrong.

**12. Modelling the ladder was supposed to shrink the result. It did the opposite, and the
reason is worth more than the number.** `econ_print` now generates 4 *nested* thresholds on
one latent path — monotone by construction, so if the high rung pays, every lower rung paid
too. The expectation was that correlated resolution would widen the confidence interval by
roughly √4.3, because 534 contracts would be only ~124 pieces of evidence. It didn't:

| losing rungs in a 4-rung event | share of events |
|---|---|
| 0 | 96.3% |
| 1 | 3.7% |
| 2 | 0.04% |
| 3–4 | never observed |

**Losses cannot stack, because the strategy takes the near-certain side of *every* rung.** The
printed number lands between two thresholds, so the bot is right on every rung except the one
straddling it. Nested ladders *diversify* a threshold strategy rather than correlating it. The
"124 pieces of evidence" worry is real — but for a strategy holding one directional view across
all rungs, which this is not.

Verified by a controlled test rather than assumed: same family, only `n_rungs` differing, equal
contract counts on both sides gave **+60.2¢ vs +63.7¢ per contract** and identical
trades-per-contract. The ladder doesn't manufacture edge.

It did fix a units bug worth catching, though: `markets_per_year` counts **contracts** while
the backtester measures per **event**, so income is events/yr × PnL/event. Multiplying
contracts/yr by PnL/ladder overstates by exactly `n_rungs`.

**11. The best-looking bot in the entire coverage sweep is on the market that cannot be
beaten.** In the 9 × 12 matrix, the highest in-sample cell of all 100 is
`efficient_control / hold_favorite` at **+422¢ per market** — on a market with γ = 1.0, no
quote lag and a penny spread, where profit is impossible by construction. `buy_longshot`,
a control written to lose, tops the `crypto_hourly` column. This is what the maximum of a
wide search looks like when there is nothing there, and it is the reason every number in
`COVERAGE.md` is labelled as a direction rather than a result.

---

**13. The p-value is not the uncertainty that matters.** "$359/yr, p=0.0003" describes
*sampling* error — how much the number wobbles if you redraw markets from the same simulator.
It says nothing about whether the simulator's inputs are right, and those were chosen by hand.
`python -m kalshi.sensitivity` sweeps each one and reports where it crosses the $250 bar:

| input | status | headline holds if | fragility |
|---|---|---|---|
| markets/yr | **counted** (534) | ≥ 325 contracts/yr | comfortable margin |
| depth at 95–99¢ | modelled | ≥ **0.60×** my model (~33 contracts at the touch) | linear, and the model is a guess |
| planted edge | assumed | ≥ **72%** of what `markets.py` plants | **levered** — costs are fixed |
| spread | modelled | no more than **+1.8 ticks** wider | steps, quantised to cents |
| fee rate | **verified** | holds even at **3× fees** | robust; not an open question |
| maker fill rate | guess | *irrelevant* — see below | **retired** |

The two fragile ones are the edge magnitude and the spread. The fee — the input I worried
about most for weeks — turns out to be the one the result barely notices.

**14. One guess got retired instead of caveated.** `maker_benign_fill_rate = 0.35` was flagged
from the start as a pure invention that would become load-bearing the moment market-making
worked. Swept from 0.15 to 1.00 across all four thin families, `maker_spread` is negative
*everywhere* — and gets **worse** as fills get easier, which is adverse selection with the sign
showing: the fills you are certain to get are the ones you did not want. **An assumption whose
sign is invariant across its entire range is not one the result depends on.** It no longer
needs a caveat anywhere.

**15. The edge cannot be validated before it is traded — it would take ~18 years.**
`audit.py` measures the three conditions directly from recorded books plus settlement
outcomes, with no simulator, no strategy and no backtest in between. The edge measurement is
just `100 × outcome − ask` for every settled contract quoted in the band: what buying and
holding actually paid.

The instrument works — pointed at simulator data with a known planted edge it recovers
**+1.55¢, 95% CI [+0.53, +2.58]** — and it refuses recordings that cannot support a number
(a 4-snapshot-per-market, 100%-stale recording fails two named checks rather than producing a
confident figure). But running it exposes the practical wall:

- buying at 97¢ pays +3¢ or −97¢, so per-contract **σ ≈ 17¢**
- pinning an edge of ~1¢ to ±0.5¢ needs **~4,500 settled in-band contracts**
- only ~44% of markets ever quote in the band, so that is **~233 usable contracts a year**
- **≈ 18 years of recording**

So "proven profit" was never reachable for this edge on this family — not because the edge is
absent, but because a ~1¢ edge against a 17¢ standard deviation is unmeasurable on 534
contracts a year. **You would have to trade it to find out whether it works.** That is a fact
about the arithmetic of rare-event contracts, not about this simulator, and it is the single
most decision-relevant number the project produced.

It also reframes everything above it. The gate's eleven criteria are a good instrument aimed
at a question the available data cannot answer at this sample size. The honest use of this
directory is as a *filter* — it rules families and strategy shapes out cheaply, and every such
exclusion in findings 1–9 is solid — not as a way to certify one bot into production.

**16. A better edge is a smaller denominator, not a bigger numerator — and my 18-year
headline was overstated.** Two corrections came out of asking for better signal-to-noise.

*The precision target was wrong.* K20 reported "~18 years to validate", which was the data
needed to pin the edge to **±0.5¢**. That is not the decision anyone faces. Deciding whether
to trade needs the **sign**; deciding how much to size needs the **magnitude**. They differ by
25×:

| question | decides | data | time |
|---|---|---|---|
| is the edge positive? | trade or don't | ~580 events | **~1 year** |
| how big is it, ±20%? | sizing, is it worth the effort | ~14,600 events | ~29 years |

Both are true; quoting only the second overstated the problem. The sign is reachable.

*And the edge was in the wrong place.* Per-contract σ is `100·√(q(1−q))` — **30¢ at 90¢, 11¢ at
97¢, 6¢ at 99¢** — so variance collapses far faster than the grid-capped edge does. Measured
by exact ask price on `econ_print`:

| ask | edge | σ | SNR | obs. to detect |
|---|---|---|---|---|
| 90–95 | ≈0 | 20–30¢ | ~0 | never |
| 97 | +1.68¢ | 11.4¢ | 0.147 | 178 |
| **98** | +1.31¢ | 8.3¢ | **0.158** | **154** |
| 99 | +0.59¢ | 6.4¢ | 0.092 | 450 |

`hold_favorite(thresh=95)` was taking the whole range, paying for 90–95¢ trades that earn
nothing and carry triple the variance. 99¢ is worse than 98¢ for the opposite reason: the grid
caps the winnings at 1¢ while σ is still 6¢. New `snr_band` strategy trades only the window —
per-event SNR **0.176 → 0.226**, time-to-sign **0.9 → 0.6 years**, at 73% of the income.

That is a real improvement and a modest one. Worth stating plainly: a mid-book bet with a
**5¢** edge has *worse* SNR (0.101) than a 0.9¢ edge at the ceiling (0.285). **Variance
dominates edge**, which is why the biggest mispricing on the exchange was never the place to
look.

**17. The zero-variance trade loses to arithmetic, and "riskless" describes the trade rather
than the strategy.** K21 showed variance dominates edge, so the logical end of that argument is
a structure with no variance at all. Bracket arbitrage is exactly that: buy all 5 mutually
exclusive brackets for under 100¢, exactly one pays 100¢, profit locked at trade time. It also
needs **no settled outcomes to verify** — one snapshot of the book proves the opportunity
exists, sidestepping the wall every directional strategy hit. `python -m kalshi.arb`.

Two things turned out to be false, and I had asserted both.

*"σ ≈ 0, so infinite SNR."* True of the **trade**, false of the **strategy**. It fires in only
2.9% of sets, so the per-set-offered series is mostly zeros with occasional large wins — σ is
**36.4¢** and SNR **0.1405**, *worse* than the directional `snr_band` at 0.2256. The uncertainty
did not vanish; it moved from *will this trade win* to *will there be a trade*. It still takes
**1.3 years** to sign.

*"Riskless."* Only if all 5 legs fill at the quoted ask simultaneously:

| slippage per leg | ¢/set | annual | fires that now LOSE |
|---|---|---|---|
| +0 tick | +5.12¢ | $+8 | **0/118** |
| +1 tick | −1.92¢ | $−3 | **105/118** |
| +2 tick | −8.96¢ | $−13 | 118/118 |

The mechanism generalises well beyond Kalshi: **an N-leg arb pays N × slippage to capture ONE
margin.** The margin is the gap below 100 and it is captured once; slippage is paid on every
leg. Break-even per-leg slippage is `margin / N`, and the median margin here is **1¢ across 5
legs — 0.2 ticks. The tick is 1¢.** The smallest possible adverse move is five times what the
trade can afford.

| legs | cost of 1 tick each | opportunities surviving |
|---|---|---|
| 2 | 2¢ | 22% |
| 3 | 3¢ | 10% |
| 5 | 5¢ | **1%** |
| 8 | 8¢ | 0% |

The only version that survives slippage is **resting** orders on every leg — a maker fill is at
your price by definition. That swaps slippage risk for fill risk, and finding 14 already showed
resting orders are negative here at every fill rate from 0.15 to 1.00. Both doors are shut, and
each is shut by the other's risk.

*(Finding 21 found a third door this missed — an **IOC limit** is neither marketable nor
resting: you pay your price or you get nothing. It turns out not to be shut for money at all.
It is shut for the only property that made this trade interesting.)*

**18. Frequency is free; information cost is the whole problem. My own K22 summary was
wrong, and the correction made a prediction that then failed too.** `python -m kalshi.frontier`.

I closed K22 by calling this "three structural walls, each blocking the corner opposite." That
was pattern-matching on three cases. Written out, the arithmetic is sharper. For edge `e` and
standard deviation `s` per opportunity, at `f` opportunities a year:

```
income  = f · e / 100                        dollars a year
years   = (1.96 · s / e)² / f                to establish the SIGN of the edge

income × years = 3.8416 · s² / (100 · e)     ← f cancels, exactly
```

Verified to the decimal on 19/19 sweep rows. So **information cost `I = s²/e`** is the
frequency-invariant measure of an opportunity, and every strategy satisfies
`income × years = 0.0384 · I`. Frequency is not a wall — doubling `f` doubles income *and*
halves validation time, so it is unambiguously good and free. `I` is the hard part, and it is a
property of *structure*: where in the price grid you trade, whether the payoff is bounded, how
many legs you need. **Independent axes, not one tradeoff.**

Then the ranking made a falsifiable prediction, which is the point of having one:

| strategy | I = s²/e | opp/yr | $/yr | yrs to sign |
|---|---|---|---|---|
| `index_bracket_daily` / `bracket_arb` | **84** | 150 | $+3 | 0.98 |
| `econ_print` / `snr_band` | 1,307 | 134 | $+166 | 0.30 |
| `politics_long` / `late_favorite` | 4,595 | 200 | $+40 | 4.39 |
| `econ_print` / `hold_favorite` | 60,409 | 134 | $+386 | 6.01 |

The arb's `I` is **15× better than the next structure and 700× better than the current
winner.** Its only problem is frequency. If frequency is genuinely free, a bracket family at
23× the frequency should dominate everything here. So I built one — `crypto_bracket_hourly`,
5 brackets, 17,520 contracts a year, a realistically tight 0.6¢ book.

**It earns exactly $0.00. It never fires once.** The reason is the finding:

| quote noise | sets incoherent | edge/set |
|---|---|---|
| 0.4¢ | 1.8% | +0.00¢ |
| 0.6¢ | 9.6% | +0.00¢ |
| 1.0¢ | 61.4% | +0.28¢ |
| 1.4¢ | 93.1% | +12.47¢ |
| 2.0¢ | 99.1% | +145.84¢ |
| 3.0¢ | 99.9% | +543.43¢ |

**Bracket incoherence *is* quote noise, and the response is violently non-linear** — a 2.3×
increase in noise moves the edge by 4 orders of magnitude. A liquid, high-frequency market is
liquid *because* its quotes are tight, and tight quotes are coherent quotes. So while frequency
is free *within* a family, frequency and opportunity are **anticorrelated across** families,
and that is not visible anywhere in `I`.

Which is the actual lesson: `I` measures how good a trade is *if it exists*. It says nothing
about whether one does. A low information cost is a reason to go looking, never evidence that
you will find anything.

**19. Both of the last two rounds were reasoning about one mechanism while believing they were
reasoning about brackets — and there was a third mechanism in the code the whole time.**

K22 concluded the bracket arb cannot work; K23 concluded "tight books are coherent books". Both
conclusions rest on the *margin distribution*, and that came entirely from the only channel the
simulator had for making a bracket set incoherent: independent per-leg `quote_noise`. Neither
round varied the channel. So I went looking for the others.

Bracket probabilities sum to 1 at every step, so their moves sum to zero. Any operator applied
identically to every leg that is also **linear** returns a zero-sum vector and cannot move the
quoted total. That predicts which parts of the quoting layer can produce an arb, and isolating
each one with the rest switched off confirms it — except in one place:

| channel | incoherent sets | |
|---|---|---|
| no lag at all | 0.0% | baseline |
| uniform lag, cap 1000¢ (never binds) | **0.0%** | linear ⇒ neutral, exactly as predicted |
| uniform lag, cap 20¢ | 15.5% | |
| uniform lag, cap 3¢ | **94.2%** | |
| uniform lag, cap 1¢ | 57.8% | |
| longshot compression, γ 1.0 → 0.9 | 0.0% | nonlinear but too gentle to clear the spread |
| symmetric quote noise, 2¢ | 100% | the channel K22 and K23 measured |

I set out to assert that uniform lag is incoherence-neutral, full stop. The check failed, and
the failure is the finding: **`underreact_cap` clips the lag, and a clip is not linear.** It
binds on legs making big moves and not on legs making small ones, so the truncated lags stop
summing to zero. Note it is *non-monotone* — a cap tight enough to clip every leg is nearly
uniform again — which confirms the mechanism is **differential** binding rather than clipping
as such. That channel has been in `markets.py` since the first round and neither previous
conclusion knew it existed.

**The channel that matters in practice is asymmetric staleness**, and it needs no wide book.
One leg's quote frozen while the others track — a wing bracket nobody is actively quoting —
dislocates the set by however far the truth travels during the freeze. That is a function of
*volatility and update latency*; spread does not appear in it. `crypto_bracket_stale` is
`crypto_bracket_hourly` with the **same salt**, so the paired sets share latent path, strikes,
spreads, depths and the same 0.6¢ book, and differ only in the freeze:

| family | fires | ¢/set | median margin | **max margin** |
|---|---|---|---|---|
| `crypto_bracket_hourly` (noise only, 0.6¢) | **0** | +0.00¢ | 1¢ | 3¢ |
| `crypto_bracket_stale` (one leg frozen) | 124 | +18.71¢ | 3¢ | **33¢** |
| `index_bracket_daily` (noise, 1.4¢) | 53 | +4.38¢ | 2¢ | 8¢ |

The centre moves 3×; **the tail moves 10×** — and the tail is the only part a filter can reach.
Which is why the same margin filter gives opposite verdicts on the two channels:

| | min margin | slippage/leg | fires | **losing** | $/yr |
|---|---|---|---|---|---|
| noise channel | 5¢ | +1 tick | **0** | — | $0 |
| staleness channel | 0¢ | +1 tick | 182 | 133 | −$405 |
| staleness channel | 8¢ | +1 tick | 76 | **0** | **+$432** |
| staleness channel | 12¢ | +2 ticks | 52 | **0** | +$202 |

So K22's mechanism was right and its conclusion was conditional. The corrected statement:
**an N-leg arb needs a margin above N ticks, and whether any exist depends on the tail of the
margin distribution — which depends on the incoherence channel, not on the spread.**

**And it still does not pass.** At `min_edge=8` with a tick of slippage on every leg it clears
**9 of 11** criteria — OOS +11.5¢/set (95% CI lo +8.0), holdout +11.9¢, Holm-corrected
p=0.0017, half-edge positive, $403/yr against a $250 bar, and **0 losing sets in 54 OOS fires
and 57 holdout fires**. It
fails on **stress** (−1.95¢ at 2 ticks + 1.5× fees — the slippage wall moved out, it did not
disappear) and on **tail risk**, which counts legs: a bracket arb books four guaranteed-losing
legs per winning one, so a trade that *cannot lose* reads as an 80% loss rate. That is
documented in `evaluate.py` as deliberately pessimistic, and for a riskless structure it is a
categorical blind spot rather than conservatism — but a round that turns up the best-looking
result in the project is exactly when a gate gets quietly loosened, so it is left alone and the
failure is asserted in `selftest.py` instead.

The honest caveat is larger than the finding: the whole thing scales linearly with
`stale_leg_prob = 0.35`, a number with no evidence behind it whatsoever. What transfers is not
the $432 — it is **where to look**: not at wide books, but at fast-moving underlyings with
slow-updating wing brackets, and with a minimum-margin filter of at least one tick per leg.

**20. That guess never needs settling, because the bracket corner is the one place where the
book tells you the answer without waiting.** `python -m kalshi.coherence`.

Finding 19 left the best result in the project resting on one invented number — the situation
finding 14 was in with `maker_benign_fill_rate`, where the rule is *retire it or measure it,
don't caveat it*. Here it can be measured, for a reason nothing else in this directory has:

| | needs | to establish the sign |
|---|---|---|
| a directional edge | **settled outcomes** | ~580 events ≈ **0.6 years** |
| bracket incoherence | **a snapshot of the book** | ~350 events ≈ **15 days of recording** |

`E[100·outcome − ask]` cannot be evaluated until the market settles, so every observation costs
a full market life. *"Do these five asks sum below 100"* is answered by **looking**. That is a
difference in kind, and it is the real reason this corner matters — more than the dollar
figure, which is downstream of the guess.

Two things had to be got right, and both are traps rather than details.

**Counting.** Snapshots of one event are not independent draws. A frozen leg stays frozen
across consecutive polls, so 60 polls of an hourly event carry roughly *one* event's worth of
information about how often events go stale. Polling faster buys resolution on **when** a set
is stale and almost nothing on **how often** — at one poll a minute the snapshot count
overstates the evidence by ~60×. Same correlated-samples error as finding 2's calibration bug.

**Completeness.** Sum four legs of a five-leg event and you get a number below 100, because you
left out a leg worth ~20¢. **A partial recording does not lose data — it manufactures an
arbitrage**, in nearly every snapshot, so it reads as the best discovery in the file. On a
family whose real margin never reaches 1¢, dropping one leg turns a median margin of −5¢ into
**+9¢**. So `quality()` refuses to report anything until every set is verifiably complete, and
`live.py --record-event` enumerates an event's legs from the API rather than trusting a
hand-typed list.

**And then the parameter stops mattering.** Backing out `stale_leg_prob` would need a model —
the measured rate is biased *down* by two things at once, reading 8% / 15% / 25% at 4 / 12 / 60
polls per event against a known truth of 35%. But **income needs no parameter**, because every
term is visible at the moment you would trade:

```
income = sets/yr × P(tradeable set) × E[margin − N·slippage − fees | tradeable]
```

The payout is 100¢ with certainty once all N legs fill. The one thing a snapshot cannot pin
down is the **entry rule** — first qualifying poll, or the peak — so both are reported, and
the truth must sit between them. Against the backtester on four independent seeds:

| seed | `first` (lower) | backtester | `best` (upper) |
|---|---|---|---|
| 41M | +4.00¢ | **+8.99¢** | +9.90¢ |
| 43M | +4.75¢ | **+9.64¢** | +18.41¢ |
| 45M | +3.63¢ | **+8.23¢** | +9.63¢ |
| 47M | +2.14¢ | **+6.00¢** | +13.73¢ |

It brackets every time, and the lower bound is positive every time. So a recording alone — **no
simulator, no settled outcomes, no `stale_leg_prob`** — settles the sign and the order of
magnitude, and leaves a 2–6× span on the size. Which is finding 16 again, reached from the
opposite direction: *the sign is cheap and the magnitude is not.* The difference is that here
the cheap half costs two weeks of polling instead of seven months of waiting.

Nothing in `COHERENCE.md` has been run against Kalshi. `CENSUS.md` counted the market list from
published research; this is the other half — the book itself — and it stays unmeasured until
someone runs `--record-event` for a fortnight. That is now the single highest-value thing
anyone could do with this directory, and it is the first time that has been true of something
achievable in under a year.

**21. Every bracket number in this project assumes an order no sane implementation would
send — and correcting it kills the strategy's whole reason for existing, while leaving the
money intact.** `python -m kalshi.execution`.

Findings 17–19 are all quoted at some number of *ticks of slippage per leg*. That models a
**marketable** order, one that crosses and walks the book. A real bot would send a **limit
order at the quoted ask**, immediate-or-cancel — and then it never pays worse than the price
it computed the arb from. The risk doesn't vanish, it moves:

| order type | you always | you sometimes |
|---|---|---|
| marketable | fill | pay worse — **slippage** |
| IOC limit | pay your price | **miss** — partial fill |

For a one-leg strategy these are interchangeable. For an N-leg arb they are not: a miss leaves
you holding *k* of *N* mutually exclusive brackets. Finding 17 wrote that sentence and moved on
without pricing it. Four seeds × 3,000 sets, with `I = s²/e` from finding 18:

| execution | ¢/set | SE | σ | **I = s²/e** | losing sets | worst set |
|---|---|---|---|---|---|---|
| perfect fill (unachievable) | +21.00¢ | ±1.64 | 150¢ | 1,078 | 0/12,000 | +0¢ |
| **marketable, +1 tick/leg** | +10.91¢ | ±0.74 | 81¢ | **595** | **0/12,000** | **+0¢** |
| marketable, +2 ticks/leg | +0.82¢ | ±0.49 | 37¢ | 1,632 | 150/12,000 | −564¢ |
| IOC limit, 95% per leg | +19.40¢ | ±1.39 | 305¢ | 4,808 | 15/12,000 | −16,125¢ |
| IOC limit, 80% per leg | +18.16¢ | ±3.29 | 463¢ | 11,824 | 54/12,000 | −16,125¢ |
| IOC limit, 60% per leg | +17.06¢ | ±2.25 | 534¢ | 16,708 | 105/12,000 | −16,125¢ |

**The mistake I nearly published.** The first version ran *one seed* and found income **rising**
as fills got worse — +25.4¢/set at perfect fill against +28.3¢ at an 80% fill rate. It read as a
discovery. It was noise: ~80 fires in 3,000 sets puts the mean's SE at 1.5–3.3¢, so every row
sat within about one of every other. That is precisely the error findings 5 and 8 exist to
catch, committed one round after I congratulated myself for catching it. Measured across four
seeds, **the expected value is flat in the fill rate** and the whole story is in σ.

**Why the mean survives.** A set only fires when it is underpriced by at least the filter, and a
collectively underpriced set is on average made of *individually* underpriced legs. So a partial
fill is a **positive-EV directional position**, not a loss — at a 60% per-leg fill only 8% of
attempts complete all five legs, yet income holds at 81% of perfect fill. Finding 17's phrase is
right about the mechanism and wrong about the consequence: the money is fine, what you lose is
*the reason you wanted the trade*.

**And that is what settles it.** Marketable execution at +1 tick has the **lowest information
cost of any mode measured, including perfect fill** — slippage shrinks the mean and the spread
by almost the same proportion, and `I` is linear in a proportional shrink, so you buy a better
risk profile at a fair price. IOC keeps the money and throws the risk profile away: σ rises 3.5×,
losing sets go 0 → 105, worst case −$161 on a single set.

So finding 17 modelled the right execution mode for the wrong reason, and the conclusion
sharpens rather than reverses. **At a 95% per-leg fill rate this is no longer an arbitrage at
all** — `I = 4,808`, worse than `snr_band`'s ~1,300–3,000, the plain directional strategy it was
supposed to beat. A riskless trade you cannot execute risklessly is a directional trade with
extra steps.

Two things this does *not* settle. Fills here are **independent per leg**, and a fast move takes
several books at once — correlated misses are worse than independent ones at the same marginal
rate, and nothing here measures that. And the gate's stress criterion still applies 2 ticks *and*
1.5× fees; two ticks is a marketable assumption an IOC limit does not face, so the right stress
here is a fill-rate stress — but inventing one *after* seeing which way it falls is how a gate
gets quietly loosened, so it is left alone.

## The gate

Eleven criteria. Criteria 1-10 gate each **bot**; criterion 11 gates the **portfolio**.

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
| 11 | the **portfolio** clears `min_annual_dollars` | a bot that aces every statistical test and is still a $133/yr business |

Criterion 11 sits on the portfolio rather than on each bot deliberately. Criteria 1-10 ask
*is this edge real*, which is a question about a bot. Criterion 11 asks *is this enough
money*, which is a question about a book. Applying the money bar per-bot rejects a component
that is real but small even when adding it strictly increases total income — a $60/yr bot that
genuinely works is a good thing to own next to a $133/yr one. Members still clear every
statistical and robustness criterion individually; no free passes for being in a basket.

Four of these were added *because the gate was passed* — every time this thing clears its
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

**The fee schedule is now VERIFIED** — it was the largest single determinant of every result
here, so it was checked against Kalshi's published schedule and independent worked examples,
and `selftest.py` §1b reproduces them (10 contracts @ 50¢ = $0.18; 20 @ 50¢ = $0.35;
per-contract 0.0175 / 0.0112 / 0.0063 at 50¢ / 20¢ / 10¢; no settlement fee). The 0.07 rate,
the P(1−P) shape and the per-**order** round-up are all confirmed. Two things were wrong and
are corrected:

- the **maker formula** was a guess (`0.0025 × C × P`, linear in price); the real one is
  `0.0175 × C × P × (1−P)` — a quarter of the taker rate, same curve, charged only on
  designated series;
- **S&P 500 (INX\*) and Nasdaq-100 (NASDAQ100\*) pay 0.035, half the standard rate**, and
  that is exactly what `index_bracket_daily` models. It had been paying double, which
  understated the only riskless trade in the project by **3.3×** (+2.22¢ → +7.37¢ per market).

One detail stays ambiguous: sources disagree on whether the round-up is to the whole cent or
to a *centicent*. Whole cent matches every published example with a number attached, so it is
what runs, and it is the **conservative** reading — it never charges less, so nothing here is
flattered by it. `rounding_granularity_cents` switches the other reading on and §1b prices the
difference at under a cent per order.

**`live.py` is now verified against Kalshi's own SDK, not against the API.** No request here
has ever reached Kalshi — the container has no route and Kalshi's bot protection blocks every
other fetch path. But the official `kalshi-python` 2.1.4 package *is* reachable (PyPI is not
blocked), so endpoint paths, host names, field names, the order schema and the signing
algorithm were checked against its source. `selftest.py` §8f pins each one, and the signature
is verified for real — a key is generated, a request signed, and the signature checked against
the message Kalshi's SDK would build, plus a negative control proving it does *not* verify over
the query-inclusive message.

Four things were wrong, and the first would have broken every authenticated call:

1. **The signature included the query string.** Kalshi signs `urlparse(url).path`. This signed
   `/markets?limit=1`, so any authenticated GET with a parameter would have been rejected as a
   bad signature — and it would have looked like a credentials problem, not a bug here.
2. **The orderbook parser assumed one encoding.** Kalshi's generated SDK exposes the sides as
   `"true"`/`"false"` (unquoted `yes:`/`no:` keys read as YAML 1.1 booleans), and levels appear
   as arrays, as objects, and as dollar strings. All four parse now.
3. **No idempotency key.** Orders now carry `client_order_id`; without one a retry after a
   timeout can double-fill.
4. **A broken `cryptography` crashed the process** with a Rust `PanicException`, which is not
   an `ImportError` and sailed through the obvious guard. This container ships exactly that
   build, and it took the whole self-test suite down with it.

Still settleable only by a live call: whether the server emits `yes`/`no` or `true`/`false`,
whether `buy_max_cost` counts fees toward its ceiling, and whether any field has been renamed
since 2.1.4. Run `--demo --check` first.

**Also not modelled:** market impact beyond depth-at-touch, a shared bankroll across
simultaneous markets (so no compounding and no path to ruin — sizing is a separate problem
this project does not solve), queue position, outages, rejected orders, exchange position
limits, and adverse selection beyond what the maker fill rule encodes.
`maker_benign_fill_rate = 0.35` is a **guess**, and every market-making number here is
downstream of it. So is `stale_leg_prob = 0.35`, which finding 19's whole result scales
linearly with — the difference is that finding 20 shows that one need never be settled at all,
because income can be estimated from books directly.

### Turning this into a real result

The path exists and it is not short:

1. `python -m kalshi.live --check` — confirm the API shape on a machine with egress.
2. Correct the fee schedule in `config.json` against Kalshi's published rates. *(done — see
   above; it stays step 2 because it is the first thing anyone else should re-check.)*
3. `--record` on a cron job for weeks, across several families. Books, not just prices.
4. `--replay` the recording through the *same* strategy objects and the *same* fee model.
   The replay path reuses `backtest.run` unmodified so a bot cannot behave one way in the
   simulator and another on real data.
5. Only then ask whether the gate passes. Expect it not to.

**Start at the bracket branch instead, because it is a fortnight rather than a year.** Steps
3–5 need settled outcomes and finding 16 prices that at ~0.6 years just to establish a sign.
The bracket path does not:

1. `python -m kalshi.live --record-event <EVENT> --samples 600 --interval 60` — every leg of
   one event, from the API rather than a hand-typed list. A partial set fabricates an arb.
2. Repeat across ~350 independent events. At an hour an event that is about **15 days**.
3. `python -m kalshi.coherence rec.jsonl` — it refuses the recording outright if any set is
   incomplete, then reports the tradeable rate with a Wilson interval and brackets the income
   between the two entry rules.
4. If the lower bound is not positive, the branch is dead and it cost two weeks. If it is,
   *that* is the first real number this directory has ever produced.

**On real money:** paper mode is the default; `--live` also requires
`KALSHI_ALLOW_LIVE_ORDERS=yes` in the environment and caps notional at $5 unless raised.
Nothing in this directory has been validated against real market data, and event contracts
are a leveraged, all-or-nothing instrument. A simulated edge that survives nine criteria on
data you generated yourself is a reason to go collect real data — not a reason to fund a bot.
