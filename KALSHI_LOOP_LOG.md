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
- **In-sample selects, out-of-sample validates, holdout confirms once.** Breeding is never
  given OOS results. If a future round wants to mutate on out-of-sample scores, the honest
  move is to add a fourth dataset, not to relax the rule.
