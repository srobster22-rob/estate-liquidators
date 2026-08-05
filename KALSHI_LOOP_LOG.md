# Kalshi Loop Log

One line per round. Newest at the bottom. Same format as `LOOP_LOG.md`.

Format: `K<n> · <what was built> · <what it found>`

This is a separate track from the game. It shares the repo's habits — stdlib only,
simulate before you believe, write down what would disprove you — and nothing else.

---

K1 · Built the foundation: `kalshi/fees.py` (Kalshi's fee formula with hand-computed worked
examples), `kalshi/paths.py` (latent price engine), `kalshi/markets.py` (nine market families
+ a no-edge control), `kalshi/strategies.py` (twelve strategies, five of them controls
designed to lose). · **Found that the fee schedule decides the project before any strategy
exists.** `0.07 × C × P × (1−P)` peaks at mid-book: a round trip at 50c burns 3.50c of a 100c
notional, 3.5%. Every round-trip strategy in the zoo needs to find 3.5c of edge before it has
found anything, and the largest bias I was willing to plant anywhere is 3.4c. So
hold-to-settlement is not one option among several, it is the only structure that can work —
it pays the fee once and never crosses the spread to exit. Also: the fee ceiling is charged
**per order**, so a 1-lot at 5c owes 0.33c and is charged 1c, a 3x tax unrelated to edge.
Order size left as a searched parameter rather than a constant because of it.

K2 · Built `kalshi/backtest.py` and `kalshi/selftest.py` — 38 checks aimed at the specific
ways a backtest lies. · **Three failed, and two of the three were bugs in the checks, which
was the more useful outcome.** (a) The calibration check sampled every 7th step of each
episode and then judged the error against a tolerance computed as if those samples were
independent — they share an outcome, so effective n was ~9x smaller than claimed and a
perfectly calibrated series looked 3-sigma off. (b) The control-bias check condemned
`efficient_control` for a +0.36c longshot bias when gamma is exactly 1.0 and nothing was
planted — see K3, it was real and it was not a bug. (c) The BH check asserted that 500 tests
at p=0.04 should all be rejected; BH correctly declares all 500 discoveries, and the
assertion was wrong about the statistics. That third failure is what moved the gate off FDR
— see K4.

K3 · Chased the control-market bias instead of tuning it away. · **Kalshi's 1c price floor is
itself a favourite-longshot bias, and nobody planted it.** Measured on the control:
**+1.13c below 2c, −0.12c above it.** Prices live on 1…99, so a contract whose true
probability is 0.3% must still trade at 1c or better and is structurally overpriced; the 99c
ceiling is the mirror image. This is a real feature of the exchange that falls out of
modelling the price grid honestly, and it is the mechanism both eventual winning bots trade.
The control is still a valid tripwire — above the floor its bias is zero to two decimal
places — but the check now excludes the boundary and asserts the floor effect separately.

K4 · Built `kalshi/evaluate.py` (the gate) and `kalshi/factory.py` (the loop). · **Changed
the multiplicity correction from Benjamini-Hochberg to Holm, because of what K2's failing
check exposed.** BH controls the false discovery *rate*: given 500 tests at p=0.04 it
declares all 500 discoveries, and it is right to — under a global null you would expect 25.
That reasoning is sound and useless here. The factory does not fund a portfolio of 500 bots;
it picks one and puts money behind it, so a single false discovery is not 1/500th of a
problem, it is the whole problem. Holm controls the probability of *any* false discovery,
which is the question actually being asked. BH is still computed and reported, because the
gap between the two numbers is a good read on how hard the search has been pushed.

K5 · First full run of the loop. · **Found a reproducibility bug that would have invalidated
everything, and it was invisible.** `generate_group` seeded from `hash(family_name)`, and
Python randomises string hashing per process — so every run drew different markets from the
same seed. Two identical invocations disagreed about which strategy won: the best config on
the control market scored +84c in one process and +975c in the next. Each run was internally
consistent, so nothing in the pipeline would ever have flagged it. Now crc32, which is stable
across processes and machines forever. **Also caught myself committing the exact error this
directory exists to prevent:** selftest check 8 asserted that the best of ~455 configs on the
no-edge control had a non-positive mean, and it failed at +496c. That was not an edge — per
market PnL has a standard deviation near 10,000c, so the standard error over 400 markets is
~500c and the maximum of 455 such estimates is positive with near-certainty. The check now
Holm-corrects the whole family and requires that nothing survives.

K6 · Investigated the first strong candidate rather than banking it. · **The edge was the 99c
price ceiling plus the planted quote lag, and the simulator was flattering it.**
`hold_favorite(thresh=95)` on `econ_print` was earning ~1.8c/contract. Measured
`E[100·true_p − ask]` by price: **negative below 96c, +0.94c at 98c, +0.84c at 99c** — the
grid boundary, exactly as K3 predicted. But the first version of `markets.py` quoted 150–600
contracts of depth at 99c, which is not what a real book looks like at a price everyone
agrees is nearly certain. Added a depth taper (`4p(1−p)`, floored at 8% of base), so a 99c
market shows about a twelfth of the size a coin-flip market does. The most flattering
possible assumption was sitting at exactly the price where the discovered edge lived.

K7 · The gate passed three bots — so audited the winners and **found a hole in the gate that
the winners walked through.** All three won ~99.3% of the time and handed back most of the
position on the other 0.7%: **seven observed losses in 1,200 markets.** Every one of the
eight criteria treated seven observations of the only thing that can hurt you as sufficient
evidence. Added criterion 9: apply the **Wilson upper bound on the loss rate** to the losses
actually seen and require the strategy to still be profitable. The fewer losses observed, the
wider the bound and the harsher the test, so it needs no arbitrary minimum-loss threshold.
The three winners survive it (tail-adjusted +30.0c against a measured +85.6c); a synthetic
variant with the same expectancy but 2 losses instead of 7 does not, which is the check
earning its place. 53 harness checks now pass.

K8 · Ran the loop to completion and built the 9×12 coverage matrix (`--sweep`). · **The
best-looking bot in the entire sweep is on the market that cannot be beaten.** Of 100
populated cells, the highest in-sample score is `efficient_control / hold_favorite` at
**+422c per market** — gamma exactly 1.0, no lag, penny spread, profit impossible by
construction. `buy_longshot`, a control written to lose, tops the `crypto_hourly` column.
Three more results worth keeping: **every** round-trip strategy (`momentum`, `mean_revert`,
`jump_follow`, `jump_fade`) is negative on **all nine families**, including ones with a 3c
mispricing planted in them — they lose to the fee, twice per trade, not to the market.
`pair_arb` found **0 opportunities across 5,200 market-lives**, confirming that the
much-repeated "buy YES and NO under 100" arb cannot exist on a single unified book.
And `awards_thin`, which carries the largest planted mispricing of any family (~3.4c on a
10c contract), produced **nothing** — a 10–60 contract book and 60 days of locked collateral
beat a large edge. Depth and capital lockup decide tradeability, not the size of the
mispricing.

K9 · Reached the goal, then made the report argue against itself. · **The loop passes in
generation 0, and the honest reading of that is a warning.** Default run: 190 bots, 12
out-of-sample tests, **3 winners at Holm-adjusted p=0.006**, holdout +53.3c, stress +43.0c,
3 holdout touches. With `--keep-going` for all 12 generations: **718 bots, 142 tests, 28
winners — and only 3 distinct mechanisms, all on `econ_print`**, plus 29 holdout touches, at
which point the holdout is a second validation set rather than a clean third one. Both facts
are now printed by the loop and headlined in `RESULTS.md`, because "28 profitable bots" is a
count of parameter variants, not of findings. Wrote `kalshi/live.py` for the only path that
turns any of this into a statement about the real exchange — record real books, then replay
them through the *unmodified* backtester so a bot cannot behave one way in the simulator and
another on real data. The replay path is tested offline; every network path is unverified,
because this machine has no route to kalshi.com.

K10 · Asked what the winning bot is worth in dollars rather than percent — built
`kalshi/capacity.py`. · **The +4552%/yr bot is a $214-a-year business.** The percentage is
arithmetically correct and describes capital that is deployed 9% of the year; the rest of the
time it earns nothing. Actual figures: `econ_print` lists roughly **250 markets a year**, the
book holds about **55 contracts** at the price where the edge lives, so the bot commits **$52**
of capital and returns **$214/yr** — 409% on committed capital, and unscalable. Neither of the
two ways to improve that is a tuning problem: find the same inefficiency in a family that
lists more markets, or at a price where the book is deeper. Also replaced an inference with a
measurement — capacity was splitting capital-cent-hours into cost x duration using the largest
position ever opened as the scale, which got both halves wrong in opposite directions; the
engine now reports mean position cost and mean holding time directly.

K11 · Added gate criterion 10, the half-edge world: re-run every winner against markets whose
planted inefficiency is halved and whose spreads, depth and fees are untouched. · **The result
is a levered bet on magnitudes I chose by hand, and the leverage is about 3x.** Paired
sensitivity for `hold_favorite(95)`: **100% -> +84.3c, 75% -> +61.2c, 50% -> +23.2c,
25% -> -11.0c**. Costs are fixed, so net edge is gross minus a constant — halving the assumed
inefficiency removes roughly three quarters of the profit, and every winner turns negative
between 25% and 50%. The real claim is therefore narrow: *if* Kalshi's mispricing is at least
~40% of what `markets.py` guesses, these bots work. **The first version of this criterion was
wrong and it disqualified a real bot.** The attenuated copy had its own name, therefore its own
crc32 salt, therefore entirely unrelated markets — so the comparison measured sampling noise
while appearing to measure edge sensitivity. The giveaway was the sensitivity curve coming out
non-monotone: a 25%-strength world scored *better* than a 50% one, which is impossible if the
only thing changing is the edge. Attenuated families now inherit their base family's salt, and
four new self-tests pin the pairing down — factor 1.0 must reproduce the base family byte for
byte. 57 checks pass.

K12 · Asked for more than $214/yr. Made annual dollars a first-class metric and gate
criterion, then measured every family directly. · **The $214 was my own bug, and the honest
figure is $133.** `capacity.py` measured on the OUT-OF-SAMPLE seeds — and OOS is where winners
are *chosen*, so the OOS mean of a winner is the maximum of a selected set. Holdout says 53.3c
per market; a fourth, never-touched seed range says 48.8c; OOS said 85.6c. The headline was 60%
too high and `selftest.py` now fails if capacity ever reads the OOS seeds again. Then the
search itself: 14 generations, 814 bots, 164 out-of-sample tests against a $250 bar produced
**nothing**. Direct measurement explains why — Kalshi's fee plus one spread crossing costs
1.5-3c a contract, only `econ_print`'s 3c quote lag clears it, and `econ_print` is the rarest
thing on the exchange at ~250 markets/yr. `crypto_hourly`, with 70x the listings, is **negative
at every threshold tested** over 8,000 markets. The ceiling is the product of those two facts.

K13 · Fixed a search-allocation bug, chased the family it had been hiding, and watched the
confirmation step earn its keep. · **`sports_game` had received ZERO out-of-sample slots in 164
tests** — a global top-N ranking by t-statistic let `econ_print` take 92 of them, and three
families were never tested at all. Slots are now stratified by family first, global rank
second. Testing `sports_game` directly gave **+379.7c/market, t=+2.40, $22,785/yr** — 100x the
incumbent. On an independent confirmation set: **+7.5c, t=+0.05, p=0.46**, with a tail-adjusted
figure of **-$16,174/yr**. It was the maximum of 18 configs on a family whose per-market
standard deviation swamps 4,000 markets. Every clean select-then-confirm split behaved the same
way, with one exception that matters: `hold_favorite(thresh=95)` scored t=+2.57 on selection and
**t=+4.12 on confirmation**, p=0.0003. Ranking by dollars picks variance; ranking by evidence
picks the thing that replicates — which is why annual dollars is a prefilter and a gate, never
the ranking. Also built `portfolio.py` and moved the money bar onto the book rather than the
bot, since a real-but-small component still adds income. Only one family ever gets confirmed,
so the portfolio is currently a portfolio of one: **$164/yr, 95% CI $24-$283**.

K14 · Restated the result as something falsifiable instead of as a dollar figure. · **The bot
clears $250/yr if and only if `econ_print`-style markets number >= 469 a year.** Annual income
is strictly linear in markets-per-year, which is the one input in this project that is a pure
estimate (mine is 250), so that break-even count is where the entire dollar figure rests and
`capacity.py` now prints it. Someone with API access can settle it in an afternoon — and should
also check whether strike *ladders* inflate the count, because eight strikes on one CPI print
are eight markets but one bet. **The requested target was not reached and could not be reached
honestly**: the only lever that clears it is the unverified input, and moving that to hit a
number is precisely the failure this directory exists to prevent. 66 checks pass.

K15 · Counted the real market list instead of guessing at it. · **534 economics contracts a
year, not 250 — and that flips the answer.** The whole result had been reduced to a counting
question: the bot clears $250/yr iff `econ_print`-style markets number >= 469 a year. Kalshi's
API returns 403 to everything here — the container proxy blocks the host AND Kalshi's own bot
protection blocks the fetch tooling, including on kalshi.com — so the count came from published
sources instead. Headline figure from an academic dataset: **2,668 settled contracts across 8
economic series, July 2021-June 2026**. Sixty months is exactly 5.0 years, so **534 a year**,
2.1x the guess, and a *lower* bound (8 series only; the window includes Kalshi's small years).
Confirmed series tickers seen in search results: KXCPI, KXPAYROLLS, KXFED, KXJOBLESSCLAIMS,
KXU3MAX — and **jobless claims is WEEKLY**, 52 events a year on its own, which is most of what
the old estimate was missing. At the replicated edge that is **$292/yr (95% CI $151-$421,
p=0.0003, tail-adjusted $147)**, clearing both the $250 bar and the $214 that started this.
**The bot did not get better; the count got right** — the edge per market is unchanged and so
is every gate verdict about it.

The census also produced a second number that matters more for risk than for income. A Kalshi
CPI market is a **ladder**: nested rungs ("above 0.2%", "above 0.3%", ...) that all settle from
one printed number. So 534 contracts is only ~**124 independent events** a year. The two
numbers do different jobs — income scales with contracts, because each rung has its own book
and its own depth; risk and evidence scale with events. 534/124 = 4.3 rungs per event, which is
consistent with the ~6-threshold ladders in published Core CPI examples, and that agreement
between two independently sourced numbers is the only internal check the census has. A $292/yr
business resting on 124 independent resolutions a year is a much narrower thing than the
contract count makes it look. 73 checks pass.

K16 · Verified the fee schedule — the last load-bearing guess, and the one that decides every
result in the directory. · **The 0.07 rate is right; two things around it were wrong.**
Confirmed against Kalshi's published schedule and independent worked examples, now reproduced
in `selftest.py` §1b: 10 contracts @ 50c = **$0.18** (raw $0.175), 20 @ 50c = **$0.35**,
per-contract **0.0175 / 0.0112 / 0.0063** at 50c / 20c / 10c, and no settlement fee. The rate,
the P(1-P) shape, and the round-up being charged **per ORDER** rather than per contract all
hold exactly as modelled — which also means the "order size is free alpha" finding survives.

What was wrong: (a) the **maker formula** was a guess, `0.0025 * C * P`, linear in price. The
real schedule is `0.0175 * C * P * (1-P)` — a quarter of the taker rate with the *same* curve,
charged only on designated series. (b) **S&P 500 (INX\*) and Nasdaq-100 (NASDAQ100\*) series
are charged 0.035, half the standard rate** — and that is precisely what `index_bracket_daily`
models. It had been paying double the real fee for the entire project. Correcting it more than
triples the only riskless trade here: **bracket arb goes +2.22c -> +7.37c per market**, $17 ->
$55/yr. Still small, because index brackets are ~750 markets a year, but it is riskless money
that the wrong fee was hiding.

One ambiguity survives and is now measured instead of argued: sources disagree on whether the
round-up is to the whole cent or to a **centicent**. Whole cent matches every published example
that has a number attached to it, so it is what runs, and it is the *conservative* reading — it
never charges less, so no result here is flattered by the choice. `rounding_granularity_cents`
switches the other reading on and §1b prices the gap at under a cent per order. The headline is
unchanged at **$292/yr** because econ_print's multiplier is 1.0. 87 checks pass.

---

## Standing notes

- **The edges are planted.** `markets.py` inserts longshot compression, a capped quote lag,
  bracket incoherence and wide spreads. The factory rediscovers them. That tests the harness;
  it says nothing about whether those inefficiencies exist on Kalshi. Any round that starts
  to read the factory's output as a market claim has lost the thread.
- **Two things are unverified and one of them is load-bearing.** The 0.07 fee rate is from
  general knowledge, not a live read of Kalshi's schedule, and fees decide every result here.
  All of `live.py`'s network paths are unverified against a real server.
- **`maker_benign_fill_rate = 0.35` is a guess.** Every market-making number is downstream of
  it. `maker_spread` currently produces nothing anywhere, so the guess is not yet
  load-bearing — but it will be the moment it does.
- **Check the control row before reading any table.** Three separate times, the most
  profitable-looking thing in a search was a control. That is what maxima of noise look like,
  and it is the reason the gate corrects across every test the loop has ever run.
- **The fee schedule is verified; `live.py` is not.** Endpoint paths, field names and the
  signature construction have never touched a live server. That is now the largest unchecked
  assumption in the directory.
- **A sourced count is not a measurement.** The census comes from published figures because
  the API is unreachable from here; it is far better than the guess it replaced and it is still
  not `GET /markets`. Re-run it against the live API from a machine with egress before anyone
  plans around $292.
- **Measure capacity on data that had no hand in picking the bot.** OOS selects winners, so
  OOS means of winners are maxima of a selected set. Holdout or a fresh seed range only. This
  cost 60% of a headline once already.
- **Rank by evidence, size by dollars.** Ranking candidates by annual dollars chases variance:
  it picked configs that scored $22,785/yr and confirmed at t=+0.05. The t-statistic picked the
  one config that replicated. Dollars are a prefilter and a gate, never the ranking.
- **Stratify the search by family.** A global top-N starves families that need a different
  threshold to look good, and it hid `sports_game` for 164 consecutive tests.
- **Report dollars, not percentages.** Every return figure in this project is a return on
  capital measured over the fraction of the year that capital is deployed, and that fraction
  is often under 10%. `capacity.py` exists because the percentage flatters by roughly an
  order of magnitude and the dollar figure is the one that decides anything.
- **Every time the gate is passed, ask what it failed to ask.** Criteria 9 and 10 both exist
  because a bot cleared the bar and the bar turned out to be missing something — rare-loss
  tail risk, then sensitivity to the simulator's own magnitudes. That is the intended rhythm.
- **In-sample selects, out-of-sample validates, holdout confirms once.** Breeding is never
  given OOS results. If a future round wants to mutate on out-of-sample scores, the honest
  move is to add a fourth dataset, not to relax the rule.
