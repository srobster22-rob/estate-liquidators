# BOT FACTORY

**A strategy search that has to prove its own results.** It generates trading
bots across twelve market families and seven asset classes, tests each one
through a seven-gate validation ladder, and keeps expanding the search space
until the target number of bots survives — or until it runs out of budget and
reports that nothing did.

The committed run certified **10 distinct strategies** from 960 candidates across
`futures_trend_daily`, `fx_major_daily` and `eq_largecap_daily`, with replication
alpha Sharpes to +0.64 that barely move under 3x costs.

Read the **search-burden headroom** before any Sharpe. It is the largest search a
bot's evidence could have come out of and still clear G6, and it spans six orders
of magnitude here (>=1.07e9 down to 1,129). A bot whose headroom is close to the
tests already run would vanish in a more serious hunt.

**Sample size, not search size, is what binds.** Across three runs at 3,000,
6,000 and 12,000 bars per instance, the count went 3 -> 6 -> 10 distinct
strategies while the candidates needed fell from 91,940 to 960. G6's luck bar
rises with the number of hypotheses tested, so a search big enough to find a
marginal edge is big enough to disqualify it; more evidence per test escapes that
trap from the other side (`FINDINGS.md` F16, F19).

**And that is where the honesty has to sit.** 12,000 daily bars is 47.6 *stationary*
years — more history than most instruments have, with identical parameters at the
last bar and the first. So the finding is a statement about search design, not
about markets: under stationarity, certification is limited by evidence per
hypothesis far more than by how many hypotheses you try. Every doubling makes the
experiment statistically stronger and externally weaker at once.

The interesting part is not the search. Searches are easy, and a big enough one
will hand you a beautiful equity curve on data with no edge in it at all. The
interesting part is the gauntlet, and the two negative-control markets whose job
is to catch the harness cheating.

---

## Read this before you read a single result

**"Proven" here means exactly one thing:** *this bot survived gates G1–G7 on
this market model, at these costs.* It does **not** mean the bot makes money.

Three specific reasons, stated plainly:

1. **The markets are synthetic.** Outbound market-data hosts are blocked in the
   environment this was built in, so the search runs on parameterised market
   *families* — a persistent trend state, an anchor-reversion pull, vol
   clustering, regimes, jumps, fat tails, calendar effects, carry — with
   parameters set from published single-asset anomaly research and checked by
   `run.py calibrate`. Structure that is *in* the generator is findable by
   construction. Whether the same structure is in your actual instrument, this
   repository cannot tell you.
2. **Synthetic markets are stationary; real edges decay.** Every family here has
   the same structure at bar 3000 as at bar 1. Real anomalies get arbitraged
   away, and the ones that survive publication usually shrink. Nothing in the
   gauntlet tests for decay, because the generator has none to test.
3. **No order has ever touched a book.** Fills, spreads, impact and funding are
   all models. Intrabar extremes come from a Brownian bridge between the open and
   the close, not from observed ticks, so stop and limit fills are distributional
   approximations. That model is load-bearing: an earlier version drew the high
   and low *unconditionally*, which broke optional stopping and let
   take-profit-only bots earn +0.35 alpha Sharpe on a pure random walk. See
   `FINDINGS.md` F6.

**What the synthetic side genuinely proves** is the thing real backtests cannot:
*replication*. A real backtest has one history, so "did this work by luck?" is
unanswerable. Here, a market family plus a seed gives an unlimited supply of
independent draws, so a bot can be re-tested on 40 histories it has never seen,
drawn from two disjoint pools. That is the strongest form of the test available,
and most bots die on it.

**The path to a real claim** runs through `verify --data`. Drop real OHLCV CSVs
in and the identical engine, costs and permutation null run on real bars:

```bash
python bots/run.py verify <bot_id> --data ~/my_csvs/ --template eq_largecap_daily
```

Replication gates (G2, G7) cannot run there — there is only one history — and the
command says so rather than quietly reporting a weaker test under the same name.

---

## Quick start

```bash
pip install -r bots/requirements.txt     # numpy, nothing else

python bots/run.py selftest              # 34 falsification tests
python bots/run.py fpr                   # false-positive rate on a random walk: must be 0
python bots/run.py markets -v            # the catalogue
python bots/run.py calibrate             # is each market's edge realistic AND findable?
python bots/run.py loop --target 3 --jobs 4
python bots/run.py show <bot_id>
python bots/run.py verify <bot_id>       # re-run the full gauntlet
```

`--target N` counts **distinct strategies**, not genomes: a run that certifies the
same rule at two entry thresholds has found one thing, not two.

`loop` is resumable: `--resume` continues an existing run with its trial ledger
intact. That matters — the G6 luck bar rises with the number of candidates ever
tried, so losing the ledger would silently *lower* the standard of proof. The
ledger (`state/run_state.json`) is deliberately **not** committed: it is 30k lines
of candidate hashes useful only to the machine that produced it. The committed
record of a run is `REPORT.md` and `state/LOOP_LOG.md`.

---

## The seven gates

Each gate answers one specific way a backtest lies. A candidate stops at the
first failure, which is also what makes the run cheap: most bots never reach the
expensive gates.

| Gate | Question | Catches |
|---|---|---|
| **G1** out-of-sample | Does it work on bars the search never scored? | in-sample fitting |
| **G2** replication | Does it work on 20 fresh instances of its market? | instance-specific luck |
| **G3** controls | Does it stay flat on a pure random walk? | artifacts, harness bugs |
| **G4** stress | Survive 2× costs, 3× costs, +1 bar of delay? | frictionless fantasy |
| **G5** permutation | Beat its own block-bootstrapped null at p ≤ 0.01? | return distribution posing as skill |
| **G6** multiplicity | Beat the luck bar implied by the whole search? | p-hacking |
| **G7** confirmation | Replicate again, on a third disjoint pool? | everything above, twice |

Three design decisions inside those gates do most of the work:

**Alpha, not Sharpe.** Every gate is stated in `alpha_sharpe` — the Sharpe of
the residual after regressing the bot's returns on the underlying's. On a market
with a 7% risk premium, levered buy-and-hold has a perfectly respectable Sharpe
and zero skill. `fitness` takes the *worse* of raw and alpha Sharpe, so beta
cannot buy a pass.

**Negative controls are markets, not assertions.** `control_martingale_daily` is
an iid Gaussian random walk with no drift. Any strategy showing profit there
after costs proves the harness is broken, not that the strategy is good. This is
not a formality — it is what caught the most serious bug in the project, a fill
model that paid out on intrabar excursions the price never traversed. Three bots
had already passed G1 and G2 with alpha Sharpe +0.45 to +0.69 before G3 stopped
them. Beyond the per-candidate check, `run.py fpr` points the *entire search* at
that market and requires it to certify nothing: 0 of 28 finalists out of 3,000
candidates, with 26 dead at G1.

**The luck bar rises as the search grows.** G6 deflates the Sharpe by the
expected best-of-N under the null. Searching harder makes passing *harder*, which
is why the loop expands by adding new *kinds* of bot rather than simply buying
more lottery tickets. Two subtleties, both of which had to be measured rather
than assumed (`FINDINGS.md` F5, F9): the denominator is the number of candidates
ever tested against the *confirmation* pools, not the number screened — those
pools are independent draws no screened-out candidate touched; and the variance
input is estimated robustly, because a genome generator's tail of structurally
broken bots would otherwise set the bar, making the standard of proof rise with
the amount of junk produced.

The thresholds live in one place — `GauntletConfig` in `botlab/gauntlet.py` — and
are set from the calibration table: the best textbook archetype on the
best-behaved family reaches ~0.5–0.8 net alpha Sharpe, so the replication bar of
0.35 asks for "as good as a well-implemented classic", not for a miracle.

---

## The catalogue

Twelve tradeable families across equity, FX, crypto, futures, commodity, rates
and intraday, plus two controls. Each family states the claim it is making about
the real world in its `notes` field, and `calibrate` measures whether the claim
is (a) realistic and (b) findable after costs.

Some families are deliberately unwinnable. `eq_smallcap_daily` has the strongest
planted edges in the catalogue behind a 28bp spread; `crypto_alt_hourly` has a
violent reversal edge behind 25bp spreads and 0.30bp/bar funding. The correct
answer on those markets is *don't trade this*, and a search that reports
otherwise is wrong.

Seed pools are disjoint and used in a fixed order — `SEARCH` for the search,
`HOLDOUT` first touched at G2, `STRESS` first touched at G7 — so no gate is ever
evaluated on data an earlier decision used.

---

## Layout

```
bots/
  run.py                    CLI
  requirements.txt
  REPORT.md                 latest run: proven bots, evidence, funnel, portfolio
  FINDINGS.md               what building this established, and what broke
  ITERATION-PROMPT.md       how to continue without lowering the bar
  state/
    run_state.json          trial ledger, hall of fame, proven bots (resumable)
    LOOP_LOG.md             one line per generation
  botlab/
    markets/
      spec.py               MarketSpec + CostModel; the perfect-foresight ceiling
      generate.py           synthetic generator + the block-bootstrap null
      universe.py           the catalogue and the seed pools
      loader.py             real OHLCV CSV -> the same Series type
      series.py             the one data shape everything agrees on
    signals.py              21 primitives + 5 filters, all strictly trailing
    genome.py               what a bot is; mutation, crossover, SearchSpace
    engine.py               the backtester (execution model documented in full)
    metrics.py              performance, incl. alpha_sharpe and fitness
    stats.py                PSR, deflated Sharpe, block bootstrap
    gauntlet.py             the seven gates and their thresholds
    factory.py              candidate generation and market coverage
    loop.py                 the generation loop and the expansion policy
    portfolio.py            combining survivors, with the correlation caveat
    calibrate.py            are the markets realistic and findable?
    report.py               REPORT.md and LOOP_LOG.md
  tests/test_botlab.py      34 falsification tests
```

---

## Things that were wrong, and how they were caught

Kept here because they are the reason to trust the rest, and because each one
would have silently corrupted results:

- **Realised volatility overshot its target by 40%.** Symmetric regime switching
  parked the process in the stress state half the time. Fixed with an asymmetric
  chain plus an analytic variance budget; the residual bias in the fat-tailed
  GARCH families is absorbed by the locked `vol_fix` constants.
- **`alpha_sharpe` exploded on near-beta bots.** A bot that is essentially
  buy-and-hold has a near-zero residual, so its alpha Sharpe went to ±∞ on
  rounding noise — and levered buy-and-hold scored as skill. Fixed by flooring
  residual vol at a quarter of the strategy's own vol.
- **Pooled drawdown was meaningless.** Chaining 20 instances end to end compounds
  240 years into one curve, so `max_dd` read −99% for strategies whose every
  individual run drew down 25%. Drawdown is now measured per instance.
- **G5 demanded p ≤ 0.01 from 40 permutation draws.** The smallest attainable
  p-value was 1/41 = 0.024, so the gate was unpassable by construction. Draws
  raised to 120.
- **The G6 luck bar was built from the wrong variance.** It used the dispersion
  of single-backtest Sharpes (bar ≈ 0.8) while the evidence being judged was a
  40-instance replication median. Corrected to the sampling variance of that
  median.
- **`cost_bite` in the calibration table compared two different bots**, reporting
  beta exposure as a cost effect. Now measured per bot, gross vs net.
- **Hourly families had edge ceilings of 8.6 Sharpe.** Generator fantasy. Pulled
  down to ~2.5, where a *perfect* forecaster gets 2.5 and real bots get ~1.
- **`describe()` disagreed with itself after a round-trip**, because the identity
  hash sorted genes and the description did not.

The suite that catches this class of bug is `tests/test_botlab.py`. The
load-bearing ones scramble the future and assert the past does not move
(every signal, every filter, and the engine's own position series), require a
constant-long bot to reproduce the price exactly, require the same trend
primitive to find the planted trend *and* find nothing in the random walk, and
require that nothing anywhere beats perfect foresight.

---

## If it finds nothing

That is a result and `REPORT.md` writes it up as one, with the rejection funnel
showing which gate did the killing — mass death at G2 means the search is finding
instance luck; mass death at G4 means the edge is real but smaller than the
spread.

Do not relax `GauntletConfig` to manufacture a pass. A bot that only passes a
weakened gauntlet is worth *less* than no bot, because it will get funded.
