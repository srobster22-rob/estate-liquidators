# BOT FACTORY

**A strategy search that has to prove its own results.** It generates trading
bots across thirteen market families and seven asset classes, tests each one
through an eight-gate validation ladder, and keeps expanding the search space
until the target number of bots survives — or until it runs out of budget and
reports that nothing did.

**Every tradeable family's edge decays** — halflife half the series with a 35%
floor, so the average edge across an instance is 70% of its opening value. Only
the predictable components fade; drift and carry do not, because a risk premium is
compensation for risk rather than a mispricing waiting to be arbitraged.

The committed run certified **1 distinct strategy** (8 genomes) from 7,950
candidates, on `commodity_meanrev_daily`. All 8 still clear the standard the run
*finished* with, which is not automatic — an earlier run lost a whole strategy to
it (F26), because G6's luck bar rises while the search is still going and a bot
certified early was measured against a smaller search.

**That headline was 4 strategies until a bug fix took three of them** (F32). The
bar model made the overnight gap a fixed *fraction of the same bar's return* —
correlation exactly 1, so seeing the gap told you the rest of the bar. Making the
gap an independent draw with the same variance share is unambiguously the better
model, and re-running the ledger through it dropped 8 of 13 genomes and 2 of 4
strategies; a fresh search then found 1. The catalogue is fine — `calibrate` still
puts the best archetype at +0.37 net alpha — and the false-positive rate is still
zero. What changed is fill prices, by less than most of those bots' entire margin.

**Read the margins before the Sharpes.** Every one of those 8 clears its narrowest
gate by between **+0.004 and +0.069 alpha Sharpe** (F29). So "passed all eight
gates" here means "passed all eight gates, several of them by a rounding error",
and pass/fail cannot say so. This is not academic: it is precisely why one bug fix
in the bar model could take three of four strategies (F32) — a population with no
margin is one modelling assumption away from empty, and that assumption arrived.

That margin turns out to be the most predictive number in the lab (F30). Raising
every Sharpe gate by 20% adds +0.050 to the two that bind, which exactly four of
the thirteen have room to spare. Re-running the whole search under the harder
gauntlet — fresh ledger, own luck bar — certified **those four and no others**:
thirteen for thirteen on a named, before-the-fact prediction.

**Which makes the real result narrower than the count.** Under bars 20% higher, the
four distinct strategies become **one** — a single structure, `rsi_rev + rsi_rev`
on `commodity_meanrev_daily`, at four parameter settings. Three of the four
strategies clear the bar as it stands and would not clear it set slightly higher.

Margins also predict the decay cliff a rung before the count does. Across the
curve the median margin runs **0.253 → 0.127 → 0.026 → (nothing)**, and the
distributions at 48 and 24 years do not overlap. A population whose median room is
0.026 is one perturbation from empty, whatever its count says.

**That "4" is a number at one fade rate, so the headline is the curve, not the
count** (`python bots/run.py decay`, `FINDINGS.md` F23). A fixed pre-registered
panel — every untuned archetype plus every distinct certified strategy — run
through the same gates at each rate, on seed-paired instances so nothing but the
fade differs:

| edge fades... | mean edge | distinct strategies | median margin |
|---|---|---|---|
| never | 1.00 | 5 | +0.153 |
| halflife 48 yr | 0.82 | 1 | +0.085 |
| **halflife 24 yr** *(shipped)* | **0.70** | **1** | **+0.024** |
| halflife 12 yr | 0.57 | **0** | — |
| halflife 6 yr | 0.47 | 0 | — |
| abrupt break, midway | 0.53 | 0 | — |

**The cliff is between 24 years and 12, and it is a cliff.** What is left goes to
none across a rung that only takes the mean edge from 0.70 to 0.57 — because the
catalogue's entire population of viable strategies is packed into a 0.2-Sharpe
band just above the +0.35 replication bar. A 20% edge cut does not thin that field,
it empties it — a claim the margins above confirm independently, since a 20% cut
on a 0.5-Sharpe strategy is worth ~0.10 and every margin in the lab is under 0.07.
And **market breadth collapses faster than the strategy count**:
four families produce something with no decay, two at 48 years, one at 24. Decay
takes the diversification well before it takes the last strategy.

**That zero at 12 years is about the rate, not about the panel** (F27). Pointing
the ordinary search loop at a 12-year-halflife catalogue — its own ledger, its own
luck bar, eight expansion levels — screened **16,375 candidates and certified
nothing**, against 12,400 candidates and four strategies at 24 years. 411 of 459
gauntleted bots died at G1 and the rest at G2; not one reached the permutation
null.

**Halving your costs does not buy back a halved edge.** Sweeping edge and cost
independently (`run.py costgrid`, F24) fits `net = a·edge − b·cost` at R² 0.87-0.98,
against 0.61-0.74 for a pure ratio model: `e=1.0, c=1.0` makes +0.47 and
`e=0.5, c=0.5` makes +0.27. Same ratio, 0.20 Sharpe apart. Edge level and cost
level are separate axes, so the curve above cannot be traded away by finding a
cheaper venue.

**Decay changed the answer, not just the count.** The same catalogue with
stationary edges certified 11 strategies from 960 candidates — thirteen times less
search for nearly three times the strategies. And the winners are different
strategies, not fewer of the same ones: 6 of the 11 stationary winners were trend
rules on `futures_trend_daily`, a family that under decay produces nothing at all.

The mechanism is cost leverage. Net alpha is `gross x decay - costs`, and costs do
not decay, so a trend bot whose *gross* edge retains the ~71% the profile implies
sees its **net alpha retain 11%**. The four survivors retain 60-84%, because they
had margin over costs to begin with. Decay does not shave a little off everything;
it selects hard for that margin — which is why crowded anomalies die abruptly in
practice rather than fading (`FINDINGS.md` F21).

Read the **search-burden headroom** before any Sharpe: the largest search a bot's
evidence could have come out of and still clear G6. It spans 229 to 12 million
here, and a bot whose headroom is near the tests already run would vanish in a
more serious hunt.

The interesting part is not the search. Searches are easy, and a big enough one
will hand you a beautiful equity curve on data with no edge in it at all. The
interesting part is the gauntlet, and the two negative-control markets whose job
is to catch the harness cheating.

---

## Read this before you read a single result

**"Proven" here means exactly one thing:** *this bot survived gates G1–G7 plus the durability gate on
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
2. **The decay rate is a modelling choice, not a measurement.** Every family
   fades, but the halflife was picked as the mildest setting that still certifies
   anything. Nothing here tells you which rate is right, and the curve above shows
   the answer flipping from four strategies to none across a single rung. Read
   every number in this README as conditional on that choice.
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

python bots/run.py selftest              # 53 falsification tests
python bots/run.py fpr                   # false-positive rate on a random walk: must be 0
python bots/run.py markets -v            # the catalogue
python bots/run.py calibrate             # is each market's edge realistic AND findable?
python bots/run.py loop --target 3 --jobs 4
python bots/run.py show <bot_id>
python bots/run.py verify <bot_id>       # re-run the full gauntlet

python bots/run.py decay                 # the survival curve over fade rates (F23)
python bots/run.py costgrid              # sweep edge and cost independently (F24)
python bots/run.py loop --catalogue hl=0.25x --state bots/state/fast.json
python bots/run.py loop --bar-scale 1.2         # a harder gauntlet (>=1.0 only)
python bots/run.py revalidate                   # re-judge the ledger at the closing bar
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

## The eight gates

Each of the eight gates answers one specific way a backtest lies. A candidate stops at the
first failure, which is also what makes the run cheap: most bots never reach the
expensive gates.

| Gate | Question | Catches |
|---|---|---|
| **G1** out-of-sample | Does it work on bars the search never scored? | in-sample fitting |
| **G2** replication | Does it work on 20 fresh instances of its market? | instance-specific luck |
| **G2b** durability | Is the edge still there in the second half *and the final quarter* of each instance? | crowded / arbitraged anomalies |
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

**Cross-sectional strategies exist here, and are rejected by their own gates**
(`FINDINGS.md` F31-F33). A dollar-neutral 12-leg basket makes +1.94 gross alpha
Sharpe on a planted cross-sectional effect — the sqrt(K) arithmetic works. Finding
that number was the easy part; the six hypotheses it took to explain the *control*
basket were not, and they are what turned up the gap defect above.

With the gap fixed, the class went in front of the five gates a basket harness can
honestly run and failed two — and both failures were informative (F33, F34).

The control failure was the strategy's fault, not the harness's: a dollar-neutral
book with dispersed betas is **not market-neutral**, because its relative return
still carries `(beta_i - betabar) x the factor's own move`. It is partly a
time-series bet that the factor reverts, in a cross-sectional costume. Swapping the
factor's reversion off takes the control from +0.132 to +0.022 with everything else
identical. Ranking on the **beta residual** instead cleans the control (+0.016)
*and raises* the planted-edge result — what was removed was never edge.

The cost failure needed the strategy to trade less. Six turnover configurations,
fixed before running and all six reported; four cleared, and the best passes all
five gates:

| gate | margin | | gate | margin |
|---|---|---|---|---|
| XS1 out-of-sample | +1.067 | | XS4 **cost stress** | **+0.060** |
| XS2 replication | +0.847 | | XS5 stress pool | +0.907 |
| XS3 control | +0.065 | | | |

**And that is the result, which is not the one it looks like.** The statistical
gates clear by 0.85–1.07 — an order of magnitude more room than anything else here.
The *binding* margin is **+0.060, on costs**, which is the same 0.00–0.07 band every
single-instrument strategy sits in. **Aggregation buys statistical significance,
not margin**: sqrt(K) legs make the edge unmistakable, but costs scale with K
linearly, so the binding constraint moves from "is this real" to "does it survive
frictions" and lands in exactly the same place.

Tested directly by sweeping the cost model (F35): a **10x cost cut takes the
binding margin from +0.048 to +1.179**, and the binding gate never changes. For
this class the margin is a cost story and nothing else measured touches it — so
the lab's ceiling is the cost floor, and it is the same floor for every strategy
class tried.

The `xs_*` primitives stay tier 5, unreachable by any expansion: five gates is not
eight, nothing here is deflated for the six configurations tried, and clearing the
gates a harness can run is not a certification.

**The false-positive rate is measured, not argued.** `run.py fpr --repeats 10`
points ten independent searches at a structureless market: 20,000 candidates, 137
reached the gauntlet, **0 certified**, 95% upper bound ~2.2%. Every one died at
G1 — on a random walk, a rule fitted to the first 60% of a series has nothing left
in the last 40%, so the expensive machinery downstream never has to fire.

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
    gauntlet.py             the eight gates and their thresholds
    factory.py              candidate generation and market coverage
    loop.py                 the generation loop and the expansion policy
    portfolio.py            combining survivors, with the correlation caveat
    calibrate.py            are the markets realistic and findable?
    report.py               REPORT.md and LOOP_LOG.md
  tests/test_botlab.py      53 falsification tests
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
