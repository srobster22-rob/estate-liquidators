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

K17 · Verified `live.py` — not against the API, which is unreachable, but against Kalshi's own
published SDK. · **Four things were wrong and the first would have broken every authenticated
call.** Kalshi 403s this container and every fetch path, but **PyPI is not blocked**, so the
official `kalshi-python` 2.1.4 came down and its source settled the contract. Confirmed right:
the production base URL (`api.elections.kalshi.com/trade-api/v2` — a search snippet claiming
`external-api.kalshi.com` was simply wrong, and SDK source beat snippet), the market field
names, the `/portfolio/orders` path, and the order schema with prices bounded 1..99.

Wrong: **(1) the signature included the query string.** Kalshi signs `urlparse(url).path`;
this file signed `/markets?limit=1`, so every authenticated GET with a parameter would have
been rejected as a bad signature — and it would have looked like a credentials problem rather
than a bug here. **(2) The orderbook parser assumed one encoding** — Kalshi's generated SDK
exposes the sides as `"true"`/`"false"`, the YAML 1.1 trap where unquoted `yes:`/`no:` keys
parse as booleans, and levels appear as arrays, as `{price,count}` objects, and as
dollar-denominated strings. All four are accepted now, with a magnitude-independent dollar
test so a 1c level does not become 100c. **(3) No idempotency key** — orders now carry
`client_order_id`, without which a retry after a timeout can double-fill. **(4) A broken
`cryptography` crashed the process**: a build missing `_cffi_backend` raises pyo3's
`PanicException`, which is not an `ImportError` and sailed through the obvious guard. This
container ships exactly that build, and it took down the entire self-test suite with a Rust
stack trace before the guard was widened.

Added: `buy_max_cost` so the EXCHANGE enforces the notional ceiling too, set to the strict
notional so a fee-inclusive reading rejects rather than oversizes; and `--demo`, pointing at
`demo-api.elections.kalshi.com`, which is where order placement should be tested. The signing
path is now genuinely tested offline — generate a key, sign a request, verify the signature
against the message Kalshi's SDK builds, plus a **negative control** proving it does not verify
over the query-inclusive message. That negative control is the check that would have caught the
original bug. 106 checks pass.

K18 · Modelled the ladder structure the census turned up, expecting it to shrink the headline.
· **It did the opposite, and the reason is the real finding.** `econ_print` now generates 4
NESTED thresholds on one latent path — monotone by construction, so if the high rung pays every
lower rung paid too. That is what Kalshi actually lists: "CPI above 0.2%", "above 0.3%", each a
separate book, all settling from one printed number. The expectation was that correlated
resolution would widen the confidence interval by about sqrt(4.3), since 534 contracts would be
only ~124 pieces of evidence. **It barely moved.** Measured loss clustering over 2,500 events:
**96.3% of events lose nothing, 3.7% lose exactly one rung, 0.04% lose two, and three or four
never happened.** Losses cannot stack, because the strategy takes the near-certain side of
*every* rung — the printed number lands between two thresholds, so the bot is wrong only on the
one straddling it. **Nested ladders diversify a threshold strategy rather than correlating it.**
The "124 pieces of evidence" worry is real, but for a strategy with one directional view across
all rungs, which this is not.

Checked rather than assumed: a controlled test with the same family and only `n_rungs`
differing, equal contract counts on both sides, gave **+60.2c vs +63.7c per contract** and
identical trades-per-contract — so the ladder does not manufacture edge, and the first
comparison that looked like it did (54.8c vs 67.2c) was seed noise between two different
ranges. **Also caught a units bug the change exposed:** `markets_per_year` counts CONTRACTS
while the backtester measures per EVENT, so income is events/yr x PnL/event; multiplying
contracts/yr by PnL/ladder overstates by exactly n_rungs. Capacity now divides, prints both
numbers, and reports trade rate per contract instead of clamping to 100%. 113 checks pass.

K19 · Swept every remaining assumption and built `kalshi/sensitivity.py`. · **The p-value was
never the uncertainty that mattered, and the input I worried about most turns out to be the one
the result barely notices.** "$359/yr, p=0.0003" describes SAMPLING error — how much the number
moves if you redraw markets from the same simulator. It says nothing about whether the
simulator's inputs are right, and those were chosen by hand. Sweeping each one against the $250
bar:

    markets/yr        COUNTED    holds if >= 325 contracts/yr (census counted 534) — comfortable
    depth at 95-99c   MODELLED   holds if >= 0.60x my model, ~33 contracts at the touch — LINEAR
    planted edge      ASSUMED    holds if >= 72% of what markets.py plants — LEVERED
    spread            MODELLED   holds if no more than +1.8 ticks wider
    fee rate          VERIFIED   holds even at 3x fees — barely matters
    maker fill rate   GUESS      irrelevant, see below

The two fragile inputs are the **edge magnitude** and the **spread**. The **fee rate** — the
thing flagged as "the single largest determinant" for most of this project's life — is the one
the answer is least sensitive to, because the winning strategy trades at 95-99c where the fee
is nearly zero. The worry was correct in general and wrong for this particular bot.

**A guess got retired rather than caveated.** `maker_benign_fill_rate = 0.35` was flagged from
round one as a pure invention that would become load-bearing the moment market-making worked.
Swept 0.15 -> 1.00 across all four thin families, `maker_spread` is negative **everywhere** —
and gets *worse* as fills get easier, which is adverse selection with the sign showing: the
fills you are certain to get are the ones you did not want. An assumption whose sign is
invariant across its entire range is not one the result depends on. It no longer needs a caveat
anywhere in the directory. 119 checks pass.

K20 · Built `kalshi/audit.py`, the instrument that would settle the three open conditions from
real books — then discovered it needs 18 years of data. · **The edge cannot be validated before
it is traded.** The audit measures depth, spread and edge directly from recorded books plus
settlement outcomes, with no simulator, no strategy and no backtest in between; the edge is
literally `100 * outcome - ask` for every settled contract quoted in the band, which is what
buying and holding actually paid. **The instrument was validated against a known answer** —
pointed at synthesised markets carrying a planted edge it recovers +1.55c, 95% CI
[+0.53, +2.58] — and it refuses data that cannot support a number: a 4-snapshot-per-market,
100%-stale recording fails two named checks instead of producing a confident figure.

Then the arithmetic. Buying at 97c pays +3c or -97c, so per-contract **sigma is ~17c**. Pinning
a ~1c edge to +-0.5c needs **~4,500 settled in-band contracts**; only ~44% of markets ever quote
in the band, giving ~233 usable a year against the census's 534. That is **~18 YEARS of
recording.** So "proven profit" was never reachable for this edge on this family — not because
the edge is absent but because a 1c edge against a 17c standard deviation is unmeasurable at
534 contracts a year. You would have to trade it to find out. That is a fact about the
arithmetic of rare-event contracts, not about this simulator.

**It reframes the whole directory.** The gate's eleven criteria are a good instrument aimed at a
question the available data cannot answer at this sample size. The honest use of this project is
as a *filter* — it ruled out round-trip strategies, thin families, market-making and the
pair-arb folklore cheaply and those exclusions stand — not as a way to certify one bot into
production. Also caught an understatement in my own first version of the wait estimate: it
divided by all 534 contracts a year rather than the ~233 that reach the band, calling it 8 years
when it is 18. 129 checks pass.

K21 · Asked for an edge with better signal-to-noise, and got two corrections instead of one
discovery. · **First, my own K20 headline was overstated.** "~18 years to validate" was the data
needed to pin the edge to +-0.5c — a precision target I picked arbitrarily and never justified.
Nobody faces that decision. Deciding whether to trade needs the **sign** (~580 events, **~1
year**); deciding how much to size needs the **magnitude** to +-20% (~14,600 events, ~29 years).
They differ by 25x. Both are true and quoting only the stricter one made the situation look far
worse than it is. `audit.py` now reports both.

**Second, the edge was in the wrong place, and the analysis says where.** Per-contract sigma is
`100*sqrt(q(1-q))` — 30c at 90c, 11c at 97c, 6c at 99c — so variance collapses much faster than
the grid-capped edge does. Measured by exact ask price on econ_print: 90-95c earns ~nothing
against 20-30c of sigma, 97c earns +1.68c against 11.4c, 98c earns +1.31c against 8.3c (best
SNR), and 99c drops back to 0.092 because the grid caps the winnings at 1c while sigma is still
6c. `hold_favorite(thresh=95)` had been taking the whole range and paying for the 90-95c trades.
New `snr_band` strategy takes only the window: per-event SNR **0.176 -> 0.226**, time-to-sign
**0.9 -> 0.6 years**, for 73% of the income. It clears the full gate at **$1,081/yr** OOS and is
the third distinct mechanism the loop has ever confirmed.

**The general lesson is worth more than the strategy.** A mid-book bet with a *5c* edge has
worse SNR (0.101) than a 0.9c edge at the 99c ceiling (0.285). **Variance dominates edge.** The
biggest mispricing on the exchange was never the place to look, and the whole project spent
twenty rounds optimising a numerator while the denominator was the free variable. 136 checks
pass.

K22 · Analysed bracket arbitrage properly — the zero-variance corner K21's logic pointed at —
and **both things I had asserted about it were wrong.** Built `kalshi/arb.py`.

**"Sigma is zero, so the SNR is infinite."** True of the TRADE, false of the STRATEGY. The arb
fires in only 2.9% of sets, so the per-set-offered series is mostly zeros with occasional large
wins: sigma **36.4c**, SNR **0.1405** — *worse* than the directional `snr_band` at 0.2256. The
uncertainty did not vanish, it moved from "will this trade win" to "will there be a trade", and
it still takes **1.3 years** to sign. Riskless describes the trade, not the strategy.

**"Riskless."** Only with simultaneous fills on all 5 legs. One tick of slippage per leg takes
it from **0/118 losing fires to 105/118**, and from +$8/yr to -$3/yr. The mechanism generalises
past Kalshi: **an N-leg arb pays N x slippage to capture ONE margin.** Break-even per-leg
slippage is `margin/N`; the median margin here is **1c across 5 legs = 0.2 ticks, and the tick
is 1c.** The smallest possible adverse move is five times what the trade can afford. By leg
count, share of opportunities surviving one tick each: 2 legs 22%, 3 legs 10%, 5 legs 1%, 8
legs 0%. **Leg count is leverage on execution risk and it points the wrong way.**

The only version that survives slippage is resting orders on every leg, since a maker fill is
at your price by definition — which swaps slippage risk for fill risk, and K19 already showed
resting orders are negative at every fill rate from 0.15 to 1.00. Both doors shut, each by the
other's risk.

**Also corrected a live number in the README:** the arb was quoted at "$55/yr on ~750 bracket
sets". 750 is a count of CONTRACTS; the backtester measures per SET, and a set is 5 contracts.
It is 150 sets a year and about $8 — the same contracts-vs-sets units bug K18 caught on the econ
ladders, still lurking in prose after being fixed in code. 145 checks pass.

K23 · Tested my own closing sentence from K22 — "three structural walls, each blocking the
corner opposite" — and it was pattern-matching on three cases. Built `kalshi/frontier.py`.
Writing the arithmetic out gives an exact identity instead of a metaphor. With edge `e`, per-
opportunity sigma `s`, and `f` opportunities a year:

```
income  = f * e / 100                        dollars a year
years   = (1.96 * s / e)^2 / f               to establish the SIGN of the edge

income x years = 3.8416 * s^2 / (100 * e)    <- f cancels, exactly
```

Verified to the decimal on 19/19 sweep rows. So **information cost `I = s^2/e`** is the
frequency-invariant measure of an opportunity, and **frequency is not a wall at all** — doubling
`f` doubles income AND halves validation time. It is free and unambiguously good, which is
exactly why the K17 census mattered. `I` is the hard part, and it is a property of STRUCTURE.
Independent axes, not one tradeoff.

**Then the corrected model made a falsifiable prediction, and it failed.** Ranked by `I`,
`bracket_arb` is **84** — 15x better than the next structure (`snr_band`, 1,307) and 700x better
than the current winner (`hold_favorite`, 60,409). Its only stated problem was frequency. If
frequency is free, a bracket family at 23x the frequency should dominate everything here. Built
one: `crypto_bracket_hourly`, 5 brackets, 17,520 contracts a year, a realistically tight 0.6c
book. **It never fires once. $0.00.**

`arb.noise_sweep()` explains it. Incoherence share and edge per set, by quote noise: 0.4c ->
1.8% / +0.00c; 0.6c -> 9.6% / +0.00c; 1.0c -> 61.4% / +0.28c; 1.4c -> 93.1% / +12.47c; 2.0c ->
99.1% / +145.84c; 3.0c -> 99.9% / +543.43c. **Bracket incoherence IS quote noise, and the
response is violently non-linear** — 2.3x the noise moves the edge four orders of magnitude. A
high-frequency market is liquid *because* its quotes are tight, and tight quotes are coherent
quotes. Frequency is free WITHIN a family and anticorrelated with opportunity ACROSS families,
and none of that is visible in `I`.

The lesson is the one that generalises: **`I` measures how good a trade is IF IT EXISTS, and
says nothing about whether one does.** A low information cost is a reason to go looking, never
evidence that anything is there.

Also fixed a selftest that failed for the wrong reason — it asserted `len(FAMILIES) == 9`, so
adding a tenth family broke it. Replaced the magic number with the invariant it was standing in
for: derived families never leak into the sweep list, and every sweepable family has a capacity
denominator. 153 checks pass.

K24 · **Both of the last two rounds were reasoning about one mechanism while believing they
were reasoning about brackets, and there was a third mechanism in the code the whole time.**
K22 concluded the bracket arb cannot work; K23 concluded "tight books are coherent books". Both
rest on the margin DISTRIBUTION, and that came entirely from the only incoherence channel the
simulator had: independent per-leg `quote_noise`. Neither round varied the channel.

There is a rule for which parts of the quoting layer can produce an arb at all. Bracket
probabilities sum to 1 at every step, so their moves sum to zero, and any operator applied
identically to every leg that is also LINEAR returns a zero-sum vector — it cannot move the
quoted total. Isolating each part of `_price_series` with the rest switched off: no lag 0.0%
incoherent; uniform lag with cap 1000c (never binds) **0.0%**; cap 20c 15.5%; cap 3c **94.2%**;
cap 1c 57.8%; longshot compression gamma 1.0->0.9 **0.0%**; symmetric noise 2c 100%.

I set out to assert that uniform lag is incoherence-neutral full stop. The check FAILED, and
the failure is the finding: **`underreact_cap` clips the lag, and a clip is not linear.** It
binds on legs making big moves and not on legs making small ones, so the truncated lags stop
summing to zero. It is non-monotone in the cap — clip every leg and it is uniform again — which
identifies the mechanism as DIFFERENTIAL binding rather than clipping as such. That channel has
been in `markets.py` since round one and neither previous conclusion knew it was there.

**The channel that matters is asymmetric staleness, and it needs no wide book.** One leg's
quote frozen while the others track — a wing bracket nobody is actively quoting — dislocates
the set by however far the truth travels during the freeze: a function of VOLATILITY and UPDATE
LATENCY, with spread nowhere in it. Added `markets._apply_stale_leg` and `crypto_bracket_stale`,
paired with `crypto_bracket_hourly` by salt so the two share latent paths, strikes, spreads,
depths and the same 0.6c book and differ only in the freeze. Result: **0 fires -> 124 fires,
+18.71c/set.** The centre of the margin distribution moves 3x (1c -> 3c); **the tail moves 10x**
(3c -> 33c) — and the tail is the only part a filter can reach. Same filter, opposite verdicts:
`min_edge=5` selects ZERO on the noise channel, while `min_edge=8` on the staleness channel
takes 76 fires with **0 losing** at a tick of slippage per leg, +$432/yr.

So K22's mechanism was right and its conclusion was conditional. Corrected: **an N-leg arb
needs a margin above N ticks, and whether any exist depends on the TAIL of the margin
distribution — which depends on the incoherence channel, not on the spread.**

**And it still does not pass.** At `min_edge=8` with a tick of slippage everywhere it clears
9 of 11 criteria — OOS +11.5c/set (lo95 +8.02), holdout +11.9c, Holm p=0.0017, half-edge
+16.2c, $403/yr against a $250 bar, 0 losing sets in 54 OOS and 57 holdout fires — and fails
two. **stress** (-1.95c at 2 ticks + 1.5x fees) is a real failure: the slippage wall moved out,
it did not disappear. **tail_risk** counts legs, so a trade that cannot lose reads as an 80%
loss rate; that is documented in `evaluate.py` as deliberately pessimistic, and for a riskless
structure it is a categorical blind spot rather than conservatism — but a round that turns up
the best-looking result in the project is exactly when a gate gets quietly loosened, so it is
left alone and the failure is ASSERTED in selftest instead. The caveat is bigger than the
finding: all of it scales linearly with `stale_leg_prob = 0.35`, a number with no evidence
behind it. What transfers is where to look — fast underlyings with slow wing brackets, and a
minimum-margin filter of at least one tick per leg. 167 checks pass.

K25 · K24 left the best result in the project resting on one invented number, which is the
situation K19 was in with `maker_benign_fill_rate` — and the rule there is retire it or measure
it, never caveat it. Built `kalshi/coherence.py` plus `live.py --record-event`. · **The bracket
corner is the one place in this project where the book tells you the answer without waiting for
anything to settle, and that is a bigger deal than K24's dollar figure.**

`E[100*outcome - ask]` cannot be evaluated until a market settles, so every directional
observation costs a full market life and K20 put the bill at ~580 settled events, about 0.6
years. "Do these five asks sum below 100" is answered by LOOKING. Measuring the incoherence
rate to +-5pp needs ~350 independent events = **15 days of recording** rather than seven months
of waiting.

Two traps had to be handled and both are the kind that produce a discovery rather than an
error. **Counting:** snapshots of one event are not independent — a frozen leg stays frozen
across consecutive polls, so polling faster buys resolution on WHEN a set is stale and almost
nothing on HOW OFTEN. At one poll a minute the snapshot count overstates the evidence ~60x,
the same correlated-samples error K2 caught in the calibration check, so everything counts
EVENTS. **Completeness:** four legs of a five-leg event sum below 100 essentially always,
because you left out a leg worth ~20c — so a partial recording does not lose data, it
MANUFACTURES an arbitrage, in nearly every snapshot. On a family whose real margin never
reaches 1c, dropping one leg turns a median margin of -5c into **+9c**. `quality()` refuses
partial sets outright and `--record-event` enumerates an event's legs from the API so they are
hard to create.

**Then the parameter stopped mattering, which is the better result.** Backing out
`stale_leg_prob` would need a model — the measured rate is biased down twice over, reading
8% / 15% / 25% at 4 / 12 / 60 polls per event against a known truth of 35%. But INCOME needs
no parameter, because every term is visible at the moment you would trade:
`sets/yr x P(tradeable) x E[margin - N*slip - fees]`, with the 100c payout certain once the
legs fill. The one thing a snapshot cannot pin down is the ENTRY RULE, so `first` and `best`
are both reported and the truth must lie between. Against the backtester on four independent
seeds it brackets every time: +4.00/+8.99/+9.90, +4.75/+9.64/+18.41, +3.63/+8.23/+9.63,
+2.14/+6.00/+13.73 — and the lower bound is positive every time.

So a recording alone, with no simulator and no settled outcomes and no `stale_leg_prob`,
settles the SIGN and the order of magnitude and leaves a 2-6x span on the size. That is K21's
sign-versus-magnitude split reached from the opposite direction, and the difference is that
here the cheap half costs a fortnight of polling instead of seven months of waiting. Nothing in
`COHERENCE.md` has been run against Kalshi; doing so is now the highest-value thing anyone
could do with this directory, and it is the first time that has been true of something
achievable in under a year. 176 checks pass.

K26 · Went after the assumption sitting under every bracket number in the project: they are
all quoted at some number of TICKS OF SLIPPAGE PER LEG, and K22's whole conclusion rests on
that axis. Built `kalshi/execution.py` and added `backtest.Costs(leg_fill_rate=...)`.

A tick of slippage models a MARKETABLE order — one that crosses and walks the book. No sane
implementation of this strategy would send one. You would send a LIMIT order at the quoted ask,
immediate-or-cancel, and then you never pay worse than the price you computed the arb from. The
risk does not vanish, it moves: marketable means you always fill and sometimes pay worse; IOC
means you never pay worse and sometimes MISS. For one leg those are interchangeable. For an
N-leg arb a miss leaves you holding k of N mutually exclusive brackets — K22 wrote exactly that
sentence and moved on without pricing it, and it has been load-bearing since.

**The mistake first.** The initial version ran ONE SEED and found income RISING as fills got
worse — +25.4c/set at perfect fill against +28.3c at an 80% fill rate. It read as a discovery.
It was noise: ~80 fires in 3,000 sets puts the mean's SE at 1.5-3.3c, so every row sat within
about one of every other. That is the error K5 and K8 exist to catch, committed one round after
congratulating myself for catching it. `measure()` now takes four seeds and reports an SE, and
`flat_in_fill_rate()` asserts the honest reading.

**Measured properly (4 seeds x 3,000 sets), with I = s^2/e from K23:** perfect fill +21.00c,
sigma 150, I=1,078, 0 losing; marketable +1 tick +10.91c, sigma 81, **I=595**, 0 losing;
marketable +2 ticks +0.82c, I=1,632, 150 losing; IOC 95% +19.40c, sigma 305, I=4,808, 15
losing, worst -16,125c; IOC 80% +18.16c, I=11,824; IOC 60% +17.06c, sigma 534, I=16,708, 105
losing. **The expected value is FLAT in the fill rate** — every IOC row within 2 SE of the best
— and the entire story is in the second moment.

**Why the mean survives:** a set only fires when it is underpriced by at least the filter, and a
collectively underpriced set is on average made of INDIVIDUALLY underpriced legs. So a partial
fill is a positive-EV directional position, not a loss — at a 60% per-leg fill only 8% of
attempts complete all five legs and income still holds at 81% of perfect fill. K22's sentence is
right about the mechanism and wrong about the consequence. The money is fine; what you lose is
the reason you wanted the trade.

**And that settles it.** Marketable at +1 tick has the LOWEST information cost of any mode
measured, INCLUDING perfect fill — slippage shrinks mean and spread by nearly the same
proportion and I is linear in a proportional shrink, so you buy a better risk profile at a fair
price. IOC keeps the money and throws the risk profile away: sigma up 3.5x, losing sets 0 ->
105, worst case -$161 on one set. So K22 modelled the right execution mode for the wrong reason
and the conclusion SHARPENS: **at a 95% per-leg fill rate this is no longer an arbitrage at
all**, I=4,808, worse than snr_band's ~1,300-3,000 — the plain directional strategy it was
supposed to beat. A riskless trade you cannot execute risklessly is a directional trade with
extra steps.

Two things left open and stated rather than papered over. Fills here are INDEPENDENT per leg; a
fast move takes several books at once, and correlated misses are worse than independent ones at
the same marginal rate. And the gate's stress criterion still applies 2 ticks AND 1.5x fees —
two ticks is a marketable assumption an IOC limit does not face, so the right stress here is a
fill-rate stress, but inventing one after seeing which way it falls is how a gate gets quietly
loosened. Left alone. 184 checks pass.

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
- **"Riskless" is a property of a trade, never of a strategy.** A trade that cannot lose but
  only appears 3% of the time still has all its variance in whether it appears. Ask what the
  per-opportunity series looks like, not what the winning case looks like.
- **Count the legs before believing an arbitrage.** Profit is `margin - N*slippage`, so
  break-even slippage is `margin/N` and it shrinks as the structure gets prettier. On a 1c grid
  any arb whose margin is under N cents is untradeable by construction.
- **Name the precision target before quoting a sample size.** "How much data do I need" has
  no answer until you say what decision it serves. Sign and magnitude differ by 25x here, and
  conflating them cost a round.
- **Variance dominates edge.** Signal-to-noise is `edge / (100*sqrt(q(1-q)))`, and the sigma
  term moves far more across the price grid than any mispricing does. Look for the smallest
  denominator, not the biggest numerator.
- **Check whether the question is answerable before building the answer.** Eleven gate
  criteria, a census, a fee verification and a sensitivity sweep all preceded anyone asking how
  much data it would take to measure a 1c edge against a 17c standard deviation. The answer is
  18 years, and it was two lines of arithmetic available on day one.
- **A confidence interval measures sampling error, not model error.** Every headline here
  carries a p-value describing how the number moves under redrawn markets, and that is the
  smaller of the two uncertainties. `SENSITIVITY.md` is the other one, and it is where the
  result is actually fragile.
- **A guess whose sign is invariant across its whole range can be retired, not caveated.**
  Sweeping beats flagging: it either shows the assumption matters, in which case measure it
  properly, or that it never did.
- **When a modelling change moves the headline UP, distrust it until a controlled test says
  otherwise.** The ladder looked like it added 23% of edge; an A/B with only `n_rungs`
  differing showed the gap was seed noise. Change one thing, hold the rest fixed.
- **A vendor's own SDK is a better source than any write-up about it.** PyPI was reachable
  when every Kalshi host was not, and the SDK source corrected a base URL that a search
  snippet had wrong. When the API cannot be called, read the client the vendor ships.
- **`live.py` conforms to the SDK contract; it has still never made a request.** Whether the
  server emits `yes`/`no` or `true`/`false`, and whether `buy_max_cost` counts fees, can only
  be settled by a live call. Run `--demo --check` first, from a machine with egress.
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
