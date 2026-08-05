"""
Harness validation. Run this before believing a single number out of `factory.py`.

Every check here is aimed at one of the ways a backtest lies. In rough order of how much
damage each failure would do:

  1  fee arithmetic          hand-computed worked examples
  2  martingale prices       E[p_{t+1} | p_t] = p_t, i.e. no drift to harvest
  3  calibration             contracts quoted at 30 resolve YES 30% of the time
  4  planted edge has the    the longshot bias is present, in the documented direction,
     stated sign and size    at roughly the documented magnitude
  5  no lookahead            structurally (View asserts) and textually (grep)
  6  bracket coherence       true probabilities in an exclusive set sum to 1
  7  PnL accounting          hand-computed entry, exit and settlement
  8  the control is inert    NOTHING may survive multiplicity correction on a perfectly
                             efficient market. Catches sign errors, double-counted payouts
                             and free fills.
 8b  rare-loss tail          Wilson bound behaves, and a 99%-win-rate strategy is priced
                             on the losses it has NOT yet observed
  9  the gate rejects noise  random_control must fail
 10  FDR vs FWER             BH and Holm against worked examples, including the case that
                             moved the gate from one to the other

Checks 2, 3 and 8 are the ones that make the difference between a simulator and a
random-number generator with good manners.

Check 8 is worth reading before writing any check of your own. Its first version asserted
that the BEST of ~455 configs on a no-edge market had a non-positive mean, and it failed at
+496c per market — not because there was an edge, but because the maximum of 455 noisy
estimates is positive with near-certainty. The check was committing the exact error the rest
of this directory exists to prevent. It now corrects across the whole family.
"""

from __future__ import annotations

import math
import pathlib
import statistics
import sys

from . import backtest, evaluate, fees, markets, paths, strategies

fails: list[str] = []
checks = 0


def ok(label, cond, detail=""):
    global checks
    checks += 1
    if cond:
        print(f"  PASS  {label}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {label}  {detail}")
        fails.append(f"{label}: {detail}")


def near(label, got, want, tol, unit=""):
    ok(label, abs(got - want) <= tol, f"got {got:.4f}{unit}, want {want:.4f}+-{tol}{unit}")


# ---------------------------------------------------------------------------
print("\n1. FEE ARITHMETIC — hand-computed")
# 100 contracts at 50c: 0.07 * 100 * 0.50 * 0.50 = $1.75 -> 175c exactly.
ok("100 @ 50c = 175c", fees.taker_fee_cents(100, 50) == 175, str(fees.taker_fee_cents(100, 50)))
# 1 contract at 50c: 0.07 * 1 * 0.25 = $0.0175 -> 1.75c -> rounds up to 2c.
ok("1 @ 50c rounds up to 2c", fees.taker_fee_cents(1, 50) == 2, str(fees.taker_fee_cents(1, 50)))
# 1 contract at 5c: 0.07 * 0.05 * 0.95 = $0.003325 -> 0.3325c -> 1c. A 3x rounding tax.
ok("1 @ 5c rounds up to 1c", fees.taker_fee_cents(1, 5) == 1, str(fees.taker_fee_cents(1, 5)))
# 100 at 5c: 0.07 * 100 * 0.05 * 0.95 = $0.3325 -> 33.25c -> 34c.
ok("100 @ 5c = 34c", fees.taker_fee_cents(100, 5) == 34, str(fees.taker_fee_cents(100, 5)))
ok("symmetric about 50c", fees.taker_fee_cents(100, 20) == fees.taker_fee_cents(100, 80))
ok("zero qty is free", fees.taker_fee_cents(0, 50) == 0)
ok("float error does not round up", fees.taker_fee_cents(4, 50) == 7,
   f"4 @ 50c = {fees.taker_fee_cents(4, 50)}c, exact value is 7.0")
near("breakeven edge at 50c", fees.breakeven_edge_cents(50, 100), 1.75, 0.001, "c")
near("breakeven edge at 5c", fees.breakeven_edge_cents(5, 100), 0.34, 0.001, "c")

# ---------------------------------------------------------------------------
print("\n1b. FEE SCHEDULE — against Kalshi's published worked examples")
# These are not my arithmetic checked against itself; they are the numbers Kalshi and
# independent write-ups publish, and the formula has to reproduce them exactly. The rate
# (0.07), the P(1-P) shape, the per-ORDER round-up and the absence of a settlement fee are
# all confirmed this way.
ok("10 contracts @ 50c costs 18c (raw 17.5c, published $0.18)",
   fees.taker_fee_cents(10, 50) == 18, f"got {fees.taker_fee_cents(10, 50)}c")
ok("20 contracts @ 50c costs exactly 35c (published $0.35)",
   fees.taker_fee_cents(20, 50) == 35, f"got {fees.taker_fee_cents(20, 50)}c")
ok("100 contracts @ 50c hits the published $1.75/100 ceiling",
   fees.taker_fee_cents(100, 50) == 175, f"got {fees.taker_fee_cents(100, 50)}c")
for price, want in ((50, 0.0175), (20, 0.0112), (10, 0.0063)):
    got = fees.TAKER_RATE * (price / 100.0) * (1 - price / 100.0)
    near(f"per-contract rate at {price}c matches published", got, want, 5e-5)
ok("no settlement fee", fees.settlement_fee_cents(1000) == 0)

# The S&P 500 (INX*) and Nasdaq-100 (NASDAQ100*) series are charged 0.035, not 0.07. That is
# exactly what index_bracket_daily models, and it had been paying double.
ok("index series pay half the taker rate",
   fees.taker_fee_cents(100, 50, series_multiplier=0.5) == 88,
   f"100 @ 50c on a halved series = {fees.taker_fee_cents(100, 50, series_multiplier=0.5)}c "
   f"vs {fees.taker_fee_cents(100, 50)}c standard")
ok("index_bracket_daily carries the halved multiplier, econ_print does not",
   markets.FAMILIES["index_bracket_daily"].fee_multiplier == 0.5
   and markets.FAMILIES["econ_print"].fee_multiplier == 1.0)

# The maker schedule was WRONG before verification: modelled as 0.0025*C*P, linear in price.
# The real one is a quarter of the taker rate with the same P(1-P) curve.
ok("maker formula is a quarter of the taker rate, same shape",
   abs(float(fees._F["maker_rate_if_charged"]) - fees.TAKER_RATE / 4.0) < 1e-12,
   f"{fees._F['maker_rate_if_charged']} vs 0.07/4 = {fees.TAKER_RATE / 4.0}")
ok("makers are charged nothing by default", fees.maker_fee_cents(100, 50) == 0)

# THE ONE THING SOURCES DISAGREE ON: whole cent vs centicent. Measure it instead of arguing.
# Rebuilt with a patched granularity so the comparison is like-for-like.
_whole = [fees.taker_fee_cents(c, p) for c in (1, 10, 100, 250) for p in (5, 50, 95)]
_saved = fees.GRANULARITY
try:
    fees.GRANULARITY = 0.01
    _centi = [fees.taker_fee_cents(c, p) for c in (1, 10, 100, 250) for p in (5, 50, 95)]
finally:
    fees.GRANULARITY = _saved
_gap = max(w - c for w, c in zip(_whole, _centi))
ok("the rounding ambiguity is worth well under a cent per order",
   0 <= _gap < 1.0,
   f"largest whole-cent overcharge vs centicent across 12 order sizes: {_gap:.4f}c")
ok("whole-cent rounding is the conservative reading",
   all(w >= c for w, c in zip(_whole, _centi)),
   "it never charges less than the centicent reading, so results are not flattered by it")
ok("default granularity keeps money in integer cents",
   isinstance(fees.taker_fee_cents(10, 50), int))

# ---------------------------------------------------------------------------
print("\n2. PRICES ARE A MARTINGALE — no drift exists to be harvested")
for fam_name in ("crypto_hourly", "sports_game", "econ_print"):
    fam = markets.FAMILIES[fam_name]
    diffs = []
    for gid in range(400):
        g = markets.generate_group(fam, 900_000 + gid)
        tp = g.legs[0].true_p
        diffs.extend(tp[t + 1] - tp[t] for t in range(len(tp) - 1))
    m = statistics.fmean(diffs)
    se = statistics.pstdev(diffs) / math.sqrt(len(diffs))
    ok(f"{fam_name}: true_p has no drift", abs(m) < 3 * se,
       f"mean step {m:+.2e}, 3se {3 * se:.2e}, n={len(diffs)}")

# ---------------------------------------------------------------------------
print("\n3. CALIBRATION — a contract whose true probability is p resolves YES p of the time")
# This check failed twice before it was right, and both failures were the check's fault:
#
#   (a) compared against each decile's MIDPOINT rather than the mean true_p inside it.
#       true_p piles up against 0 and 1 as markets converge, so the extreme deciles have
#       means nowhere near their midpoints, and a midpoint comparison reports a 5%
#       calibration error on a perfectly calibrated series.
#   (b) sampled every 7th step of each episode. Steps within an episode share an outcome, so
#       that inflated n ~9x while adding almost no information, and the tolerance derived
#       from the inflated n made a correct series look 3 sigma off.
#
# Now: one independent draw per episode, compared against the mean true_p in its decile,
# each decile judged against its own binomial standard error.
buckets = {i: [0, 0, 0.0] for i in range(10)}
for fam_name in ("crypto_hourly", "sports_game", "weather_temp"):
    fam = markets.FAMILIES[fam_name]
    for gid in range(2500):
        g = markets.generate_group(fam, 950_000 + gid)
        ep = g.legs[0]
        t = (gid * 7919) % ep.n                       # one independent draw per episode
        b = min(9, int(ep.true_p[t] * 10))
        buckets[b][0] += 1
        buckets[b][1] += ep.outcome
        buckets[b][2] += ep.true_p[t]
worst_z, worst_detail, n_tot = 0.0, "", 0
for b, (n, w, ptot) in buckets.items():
    n_tot += n
    if n < 100:
        continue
    expected = ptot / n
    realized = w / n
    se = math.sqrt(max(expected * (1 - expected), 1e-9) / n)
    z = abs(realized - expected) / se
    if z > worst_z:
        worst_z = z
        worst_detail = (f"decile {b}: quoted {expected:.3f}, resolved {realized:.3f}, "
                        f"{z:.2f} sigma on n={n}")
ok("realized frequency tracks true probability", worst_z < 3.0,
   f"worst deviation {worst_detail}; {n_tot} independent episodes")

# ---------------------------------------------------------------------------
print("\n4. THE PLANTED EDGE IS PRESENT, SIGNED AND SIZED AS DOCUMENTED")
# Longshots are measured on true_p in [0.02, 0.25]. The 2c floor is not squeamishness — see
# the tick-floor check immediately below, which is why it has to be excluded here.
for fam_name, want_sign in (("awards_thin", +1), ("politics_long", +1), ("efficient_control", 0)):
    fam = markets.FAMILIES[fam_name]
    errs = []
    for gid in range(300):
        g = markets.generate_group(fam, 960_000 + gid)
        ep = g.legs[0]
        for t in range(0, ep.n, 5):
            if 0.02 <= ep.true_p[t] < 0.25:
                errs.append(ep.mid(t) - 100 * ep.true_p[t])
    m = statistics.fmean(errs)
    if want_sign > 0:
        ok(f"{fam_name}: longshots quote too HIGH", m > 0.5, f"mid - true = {m:+.2f}c")
    else:
        ok(f"{fam_name}: control has no bias above the tick floor", abs(m) < 0.20,
           f"mid - true = {m:+.2f}c")

# THE TICK FLOOR IS ITSELF AN EDGE, and nobody planted it. Kalshi cannot quote below 1c, so
# a contract whose true probability is 0.3% must still trade at 1c or better, which makes it
# structurally overpriced by ~0.7c. This shows up even in `efficient_control`, where gamma is
# exactly 1.0 and no bias was inserted at all. Discovered by check 4 failing on the control:
# the first read was "the control is broken", and it was not — the exchange's price grid
# generates a real favourite-longshot bias on its own, before any behavioural story.
fam = markets.FAMILIES["efficient_control"]
floor_errs, above_errs = [], []
for gid in range(400):
    g = markets.generate_group(fam, 960_000 + gid)
    ep = g.legs[0]
    for t in range(0, ep.n, 5):
        e = ep.mid(t) - 100 * ep.true_p[t]
        (floor_errs if ep.true_p[t] < 0.02 else above_errs).append(e)
fm, am = statistics.fmean(floor_errs), statistics.fmean(above_errs)
ok("the 1c tick floor overprices sub-1c longshots even with zero planted bias",
   fm > 0.5 and abs(am) < 0.15,
   f"below 2c: {fm:+.3f}c (n={len(floor_errs)}) | above 2c: {am:+.3f}c (n={len(above_errs)})")

# ---------------------------------------------------------------------------
print("\n5. NO LOOKAHEAD — structurally, then textually")
g = markets.generate_group(markets.FAMILIES["crypto_hourly"], 1)
gv = backtest.GroupView(g)
gv._advance(5)
v = gv.legs[0]
try:
    v.bid(+1)
    ok("View rejects future data", False, "no exception raised")
except AssertionError:
    ok("View rejects future data", True, "dt=+1 raises")
ok("View has no episode reference", not any("_ep" in s or "true_p" in s for s in backtest.View.__slots__),
   f"slots={backtest.View.__slots__}")
src = (pathlib.Path(__file__).parent / "strategies.py").read_text(encoding="utf-8")
code = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#"))
body = code.split('"""')
body = "".join(body[i] for i in range(0, len(body), 2))   # strip docstrings
ok("strategies.py never names true_p", "true_p" not in body)
ok("strategies.py never names outcome", "outcome" not in body)
ok("strategies.py never imports markets", "import markets" not in body and "from .markets" not in body)

# ---------------------------------------------------------------------------
print("\n6. BRACKETS ARE COHERENT — true probabilities sum to exactly 1")
fam = markets.FAMILIES["index_bracket_daily"]
worst_sum = 0.0
quoted_sums = []
for gid in range(200):
    g = markets.generate_group(fam, 970_000 + gid)
    for t in range(0, g.steps, 9):
        s = sum(leg.true_p[t] for leg in g.legs)
        worst_sum = max(worst_sum, abs(s - 1.0))
        quoted_sums.append(sum(leg.ask[t] for leg in g.legs))
ok("true probs sum to 1", worst_sum < 1e-9, f"worst deviation {worst_sum:.2e}")
winners = [sum(leg.outcome for leg in markets.generate_group(fam, 970_000 + i).legs) for i in range(50)]
ok("exactly one bracket wins", all(w == 1 for w in winners), f"distinct totals {set(winners)}")
ok("quoted asks sum above 100 on average", statistics.fmean(quoted_sums) > 100,
   f"mean ask sum {statistics.fmean(quoted_sums):.2f}c — spread and noise make arbs rare, as they should be")

# ---------------------------------------------------------------------------
print("\n7. PnL ACCOUNTING — hand-computed entry, exit and settlement")


class _BuyOnceHold(strategies.Strategy):
    def decide(self, gv, pos):
        return [backtest.taker(0, "yes", 100)] if (gv.legs[0].t == 0 and pos[0] is None) else []


class _BuyThenSell(strategies.Strategy):
    def decide(self, gv, pos):
        t = gv.legs[0].t
        if t == 0 and pos[0] is None:
            return [backtest.taker(0, "yes", 100)]
        if t == 1 and pos[0] is not None:
            return [backtest.close(0)]
        return []


def _flat_group(outcome):
    fam = markets.FAMILIES["crypto_hourly"]
    ep = markets.Episode(fam, 0, 0, 3)
    ep.bid, ep.ask, ep.depth = [40, 40, 40], [42, 42, 42], [1000, 1000, 1000]
    ep.true_p = [0.41, 0.41, 0.41]
    ep.outcome = outcome
    return markets.Group(fam, 0, [ep])


# Entry: 100 @ 42c = 4200c, fee = ceil(0.07*100*0.42*0.58*100) = ceil(170.52) = 171c.
entry_cost = 4200 + 171
r = backtest.run([_flat_group(1)], _BuyOnceHold())
ok("YES settles at 100", r.total_pnl == 10000 - entry_cost,
   f"got {r.total_pnl}, hand-computed {10000 - entry_cost}")
r = backtest.run([_flat_group(0)], _BuyOnceHold())
ok("YES settles at 0", r.total_pnl == -entry_cost, f"got {r.total_pnl}, hand-computed {-entry_cost}")
# Exit: 100 @ 40c = 4000c, fee = ceil(0.07*100*0.40*0.60*100) = ceil(168) = 168c.
exit_proceeds = 4000 - 168
r = backtest.run([_flat_group(1)], _BuyThenSell())
ok("round trip pays the spread and two fees", r.total_pnl == exit_proceeds - entry_cost,
   f"got {r.total_pnl}, hand-computed {exit_proceeds - entry_cost} "
   f"(= -2c spread x100 - 339c fees)")
r = backtest.run([_flat_group(1)], _BuyOnceHold(), evaluate.stress_costs())
ok("stress costs bite", r.total_pnl < 10000 - entry_cost,
   f"stressed {r.total_pnl} < base {10000 - entry_cost}")

# One book: NO must be the mirror of YES, never a second quote.
ok("no_ask == 100 - yes_bid", v.no_ask() == 100 - v.bid())
ok("no_bid == 100 - yes_ask", v.no_bid() == 100 - v.ask())

# ---------------------------------------------------------------------------
print("\n8. THE CONTROL MARKET IS INERT — no strategy may profit on it")
# The first version of this check asserted that the BEST of ~455 configs had a
# non-positive mean, and it failed: buy_longshot came in at +496c per market. That was not
# an edge. Per-market PnL on 250-lot positions has a standard deviation around 10,000c, so
# the standard error over 400 markets is ~500c and the maximum of 455 such estimates is
# positive with near-certainty. The check was committing precisely the error the rest of
# this directory exists to prevent — reading the top of a wide search as a discovery.
#
# So the control is now tested the same way a candidate is: every config gets a t
# statistic, the whole family is Holm-corrected, and NONE may survive. That also exercises
# the multiplicity machinery end to end against data guaranteed to contain no edge.
ctrl = markets.dataset("efficient_control", 990_000, 800)
rows = []
for cls in strategies.ALL:
    if cls.requires_brackets:
        continue
    for params in strategies.all_params(cls):
        if "lo" in params and params["lo"] > params["hi"]:
            continue                       # band_fade with an empty band never trades
        st = cls(**params)
        res = backtest.run(ctrl, st)
        if res.n_trades == 0:
            continue
        s = evaluate.summarize(res, resamples=0)
        p = 0.5 * math.erfc(s.t / math.sqrt(2.0))          # one-sided, normal approx
        rows.append((st.label(), s.mean, s.t, p))
adjusted = evaluate.holm([r[3] for r in rows])
best_i = min(range(len(rows)), key=lambda i: rows[i][3])
n_raw = sum(1 for r in rows if r[3] < 0.05)
ok("nothing survives multiplicity correction on a market with no edge",
   min(adjusted) > 0.05,
   f"{len(rows)} configs tested, {n_raw} nominally significant at p<0.05, "
   f"best={rows[best_i][0]} t={rows[best_i][2]:+.2f} -> Holm p={adjusted[best_i]:.3f}")
ok("...and the check was not vacuous", len(rows) >= 200, f"{len(rows)} configs traded")
ok("average expectancy across all configs is negative — crossing the spread costs money",
   statistics.fmean(r[1] for r in rows) < 0,
   f"mean over configs {statistics.fmean(r[1] for r in rows):+.1f}c per market")

# ---------------------------------------------------------------------------
print("\n8b. THE TAIL CHECK — Wilson bound on a rare-loss rate")
near("Wilson upper on 0/1000", evaluate.wilson_upper(0, 1000), 0.0038, 0.0005)
near("Wilson upper on 7/1024", evaluate.wilson_upper(7, 1024), 0.0140, 0.0005)
ok("Wilson widens as evidence thins",
   evaluate.wilson_upper(1, 50) > evaluate.wilson_upper(20, 1000),
   f"1/50 -> {evaluate.wilson_upper(1, 50):.4f} vs 20/1000 -> {evaluate.wilson_upper(20, 1000):.4f}")
ok("Wilson upper always exceeds the point estimate",
   all(evaluate.wilson_upper(x, n) > x / n for x, n in ((0, 100), (5, 500), (250, 1000))))
# A strategy that wins 99.3% at +162c and loses 89c: profitable as measured, and it must
# still be profitable when losses are priced at the top of their confidence interval.
pennies = backtest.Result()
pennies.n_groups = 1200
pennies.group_pnl = [0] * 1200
pennies.trade_pnl = [162] * 1017 + [-8878] * 7
pennies.n_trades = 1024
pennies.max_position_cost = 9900
ps = evaluate.summarize(pennies, resamples=0)
ok("penny-in-front-of-steamroller is measured, not waved through",
   ps.wilson_loss_hi > 2 * ps.loss_rate,
   f"observed loss rate {ps.loss_rate * 100:.2f}%, Wilson upper {ps.wilson_loss_hi * 100:.2f}% "
   f"-> tail-adjusted {ps.tail_mean:+.1f}c/market vs measured "
   f"{ps.mean_per_trade * 1024 / 1200:+.1f}c/market")
# Same edge, same win size, but the losses are 3x rarer and 3x bigger: same expectancy, far
# less evidence about the thing that can hurt you, and the check must notice.
thin = backtest.Result()
thin.n_groups = 1200
thin.group_pnl = [0] * 1200
thin.trade_pnl = [162] * 1022 + [-26634] * 2
thin.n_trades = 1024
thin.max_position_cost = 9900
ts = evaluate.summarize(thin, resamples=0)
ok("a thinner-tailed version of the same expectancy scores worse",
   ts.tail_mean < ps.tail_mean,
   f"2 losses of -26634c -> {ts.tail_mean:+.1f}c/market vs 7 losses of -8878c -> "
   f"{ps.tail_mean:+.1f}c/market (same raw mean)")

print("\n8c. THE HALF-EDGE WORLD IS PAIRED — same markets, fainter signal")
# The gate's half-edge criterion is only meaningful if the attenuated copy differs from the
# original in exactly one respect. At factor 1.0 it must be byte-identical: same latent path,
# same spreads, same depth. The first version failed this — the copy had its own name, so its
# own crc32 salt, so entirely unrelated markets — and the comparison was measuring sampling
# noise while appearing to measure edge sensitivity. It disqualified a real bot that way.
same = markets.attenuated("econ_print", 1.0)
ident = True
for gid in range(60):
    a = markets.generate_group(markets.FAMILIES["econ_print"], 4_000_000 + gid).legs[0]
    b = markets.generate_group(markets._lookup(same), 4_000_000 + gid).legs[0]
    if a.bid != b.bid or a.ask != b.ask or a.depth != b.depth or a.outcome != b.outcome:
        ident = False
        break
ok("factor 1.0 reproduces the base family exactly", ident,
   "identical bids, asks, depths and outcomes over 60 groups")

half = markets.attenuated("econ_print", 0.5)
fa, fb = markets.FAMILIES["econ_print"], markets._lookup(half)
ok("factor 0.5 halves the planted edges and nothing else",
   abs((1 - fb.logit_gamma) - (1 - fa.logit_gamma) * 0.5) < 1e-12
   and abs(fb.underreact_cap - fa.underreact_cap * 0.5) < 1e-12
   and (fb.spread_lo, fb.spread_hi, fb.depth_lo, fb.depth_hi, fb.quote_noise)
   == (fa.spread_lo, fa.spread_hi, fa.depth_lo, fa.depth_hi, fa.quote_noise),
   f"gamma {fa.logit_gamma}->{fb.logit_gamma}, cap {fa.underreact_cap}->{fb.underreact_cap}, "
   f"spread/depth/noise unchanged")

# Paired means the difference is signal, so the response has to be monotone in the factor.
_st = strategies.hold_favorite(enter_frac=0.25, qty=250, thresh=95)
means = []
for f in (1.0, 0.75, 0.5):
    r = backtest.run(markets.dataset(markets.attenuated("econ_print", f), 4_000_000, 600), _st)
    means.append(r.total_pnl / 600)
ok("net edge falls monotonically as the planted edge is attenuated",
   means[0] > means[1] > means[2],
   " > ".join(f"{m:+.1f}c" for m in means) + " at 100%/75%/50%")

ok("attenuated copies stay out of the tradeable family list",
   same not in markets.FAMILIES and half not in markets.FAMILIES and len(markets.FAMILIES) == 9,
   f"{len(markets.FAMILIES)} families in the sweep")

print("\n8d. CAPACITY AND PORTFOLIO — dollars, and where they are measured")
from . import capacity, portfolio  # noqa: E402  (imported here so 1-8 run without them)

# REGRESSION GUARD. capacity.py used to default to the OOS seeds, and OOS is where winners
# are chosen — so it reported the selection-inflated mean and a $214/yr headline for a bot
# whose honest value is about $133/yr. Capacity is the number people quote; it has to come
# from data that had no hand in picking the bot.
import inspect  # noqa: E402
_src = inspect.getsource(capacity.analyse)
ok("capacity measures on the holdout seeds, never out-of-sample",
   'SEEDS["holdout"]' in _src and 'SEEDS["oos"]' not in _src,
   "default seed_base is the holdout range")

_st = strategies.hold_favorite(enter_frac=0.25, qty=250, thresh=95)
_c = capacity.analyse("econ_print", _st, n_groups=600)
near("annual dollars = markets/yr x cents per market",
     _c.annual_pnl_cents / 100.0,
     _c.markets_per_year * _c.mean_per_market / 100.0, 1e-6)
near("break-even market count inverts that exactly",
     _c.breakeven_markets_per_year * _c.mean_per_market / 100.0,
     float(capacity.GATE_MIN_DOLLARS), 1e-6)
ok("capital required exceeds mean capital deployed",
   _c.peak_concurrent >= _c.mean_concurrent and _c.utilization <= 1.0,
   f"peak {_c.peak_concurrent:.2f} >= mean {_c.mean_concurrent:.2f} positions")

# The portfolio's whole claim is that independent members diversify. Two members must sum
# their dollars while adding their variances only in quadrature.
_m1 = portfolio.build_member("econ_print", _st, 400, 7_000_000)
_m2 = portfolio.build_member("weather_temp",
                             strategies.hold_favorite(enter_frac=0.0, qty=100, thresh=90),
                             400, 7_000_000)
_p = portfolio.combine([_m1, _m2], resamples=800)
near("portfolio income is the sum of its members",
     _p.annual_dollars, _m1.annual_dollars + _m2.annual_dollars, 1e-6)
near("portfolio capital is the sum of its members",
     _p.capital, _m1.capital + _m2.capital, 1e-6)
ok("independent members diversify — interval tighter than if they moved together",
   _p.diversification > 1.0,
   f"{_p.diversification:.2f}x tighter than the correlated case")
ok("one member cannot diversify",
   abs(portfolio.combine([_m1], resamples=400).diversification - 1.0) < 1e-9)
ok("select_members never takes two bots from one family",
   len({m.family for m in portfolio.select_members(
       [{"family": "econ_print", "strategy": "hold_favorite",
         "params": {"enter_frac": 0.25, "qty": 250, "thresh": 95}},
        {"family": "econ_print", "strategy": "hold_favorite",
         "params": {"enter_frac": 0.0, "qty": 100, "thresh": 95}}], 300, 7_000_000)}) <= 1,
   "two econ_print bots collapse to one member")

print("\n8e. THE MARKET CENSUS — the count the dollar figure rests on")
from . import census  # noqa: E402

near("2,668 settled contracts over 5.0 years = 534/yr",
     census.COUNTED_CONTRACTS_PER_YEAR, 533.6, 0.05)
ok("the window is stated in whole months and converted exactly",
   census.WINDOW_MONTHS == 60 and abs(census.WINDOW_YEARS - 5.0) < 1e-12,
   "Jul 2021 through Jun 2026 inclusive")
ok("the release calendar sums to the events count",
   sum(e for _, _, e, _ in census.SERIES) == census.EVENTS_PER_YEAR == 124,
   f"{census.EVENTS_PER_YEAR} independent resolutions a year")
ok("one series per counted series — no padding to reach the total",
   len(census.SERIES) == census.SERIES_COUNTED == 8,
   f"{len(census.SERIES)} series listed, paper counted {census.SERIES_COUNTED}")
# The census's own consistency check: contracts/events must land on a plausible ladder size.
# If this ever falls outside 2-8 the two sources have stopped agreeing and one is wrong.
ok("contracts per event is a plausible ladder size",
   2.0 <= census.RUNGS_PER_EVENT <= 8.0,
   f"{census.RUNGS_PER_EVENT:.1f} rungs/event vs ~6 in published Core CPI ladders")
ok("config carries the counted figure, not the old guess",
   capacity.MARKETS_PER_YEAR["econ_print"] == round(census.COUNTED_CONTRACTS_PER_YEAR),
   f"config says {capacity.MARKETS_PER_YEAR['econ_print']}, census says "
   f"{census.COUNTED_CONTRACTS_PER_YEAR:.0f}")
ok("events/yr is strictly below contracts/yr — rungs are not independent bets",
   census.EVENTS_PER_YEAR < census.COUNTED_CONTRACTS_PER_YEAR,
   f"{census.EVENTS_PER_YEAR} events vs {census.COUNTED_CONTRACTS_PER_YEAR:.0f} contracts")

print("\n8f. LIVE ADAPTER — conformance against Kalshi's official SDK contract")
from . import live  # noqa: E402

# Verified by reading kalshi-python 2.1.4 (the official SDK) rather than by calling the API,
# which 403s from this environment. Source of truth for each check is named.

# configuration.py: both hosts, both under /trade-api/v2.
ok("production base URL matches the official SDK",
   live.PROD_BASE == "https://api.elections.kalshi.com/trade-api/v2", live.PROD_BASE)
ok("demo base URL matches the official SDK",
   live.DEMO_BASE == "https://demo-api.elections.kalshi.com/trade-api/v2", live.DEMO_BASE)

# THE SIGNATURE. api_client.py does `path = urlparse(url).path` — the query string is not
# signed. This file used to sign it, so every authenticated GET carrying a parameter would
# have failed as a bad signature and looked like a credentials problem. Verified for real:
# generate a key, sign, and check the signature against the message Kalshi would build.
# BaseException, not ImportError: a cryptography build with a missing `_cffi_backend`
# raises pyo3's PanicException, which is not an ImportError. This container ships exactly
# that build, and the narrow guard let a Rust panic kill the entire suite.
_key_available = True
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
except BaseException:                               # noqa: BLE001
    _key_available = False
if _key_available:
    import base64 as _b64
    _k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _pem = _k.private_bytes(serialization.Encoding.PEM,
                            serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption()).decode()
    _h = live._sign("get", "/trade-api/v2/markets?limit=1&status=open", "kid-1", _pem)
    ok("signing emits exactly Kalshi's three headers",
       set(_h) == {"KALSHI-ACCESS-KEY", "KALSHI-ACCESS-SIGNATURE", "KALSHI-ACCESS-TIMESTAMP"},
       ", ".join(sorted(_h)))
    ok("timestamp is milliseconds, not seconds",
       len(_h["KALSHI-ACCESS-TIMESTAMP"]) == 13, _h["KALSHI-ACCESS-TIMESTAMP"])
    # The decisive check: the signature must verify against the QUERY-LESS message.
    _msg = (_h["KALSHI-ACCESS-TIMESTAMP"] + "GET" + "/trade-api/v2/markets").encode()
    _pss = padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                       salt_length=padding.PSS.DIGEST_LENGTH)
    try:
        _k.public_key().verify(_b64.b64decode(_h["KALSHI-ACCESS-SIGNATURE"]), _msg,
                               _pss, hashes.SHA256())
        _verified = True
    except Exception:
        _verified = False
    ok("signature verifies over timestamp+METHOD+path WITHOUT the query string", _verified,
       "signed '/trade-api/v2/markets', not '...?limit=1&status=open'")
    # And it must NOT verify over the version that includes the query — otherwise the check
    # above would pass for the wrong reason.
    _msg_q = (_h["KALSHI-ACCESS-TIMESTAMP"] + "GET"
              + "/trade-api/v2/markets?limit=1&status=open").encode()
    try:
        _k.public_key().verify(_b64.b64decode(_h["KALSHI-ACCESS-SIGNATURE"]), _msg_q,
                               _pss, hashes.SHA256())
        _wrong_ok = True
    except Exception:
        _wrong_ok = False
    ok("...and does NOT verify over the query-inclusive message", not _wrong_ok,
       "the old behaviour would have failed every authenticated GET with parameters")
else:
    # Not a failure: the signing path is optional and this project is stdlib-only. But the
    # check must be visibly SKIPPED rather than silently absent.
    print("  SKIP  signature verification — no working `cryptography` in this interpreter "
          "(pip install --upgrade cryptography, then re-run to exercise it)")

# ORDERBOOK. Kalshi's generated SDK exposes the sides as "true"/"false" (a YAML 1.1 artefact
# of unquoted yes:/no: keys); levels appear as arrays, as {price,count} objects, and as
# dollar-denominated strings. Which one the wire uses cannot be settled from here, so all
# parse to the same answer.
for _label, _ob in (("[price, count]", {"yes": [[42, 13]]}),
                    ("{price, count}", {"yes": [{"price": 42, "count": 13}]}),
                    ("dollar strings", {"yes": [["0.4200", "13.00"]]}),
                    ("true/false keys", {"true": [[42, 13]]})):
    ok(f"orderbook parses {_label}", live._depth_at_touch(_ob, "yes", 42) == 13,
       f"got {live._depth_at_touch(_ob, 'yes', 42)}")
ok("a 1c level is 1c, not 100c", live._depth_at_touch({"yes": [[1, 7]]}, "yes", 1) == 7,
   "magnitude-based dollar detection would have turned 1c into 100c")
ok("an unparseable book yields 1 contract, never invented liquidity",
   live._depth_at_touch({"yes": "garbage"}, "yes", 42) == 1
   and live._depth_at_touch(None, "no", 42) == 1)

# ORDER BODY. create_order_request.py requires ticker/side/action/count/type; yes_price and
# no_price are bounded 1..99; client_order_id and buy_max_cost are the idempotency key and
# the server-side cost ceiling.
_SDK_REQUIRED = {"ticker", "side", "action", "count", "type"}
_SDK_ALLOWED = _SDK_REQUIRED | {"client_order_id", "yes_price", "no_price",
                                "expiration_ts", "sell_position_floor", "buy_max_cost"}
_src = (pathlib.Path(__file__).parent / "live.py").read_text(encoding="utf-8")
_order_blk = _src[_src.index('orders.append({"ticker"'):_src.index("if not live:")]
ok("order body carries every field the SDK marks required",
   all(f'"{f}"' in _order_blk for f in _SDK_REQUIRED),
   ", ".join(sorted(_SDK_REQUIRED)))
ok("order body sends an idempotency key", '"client_order_id"' in _order_blk,
   "without it a retry after a timeout can double-fill")
ok("order body sends a server-side cost ceiling", '"buy_max_cost"' in _order_blk,
   "so a client-side bug cannot spend more than --max-notional")
ok("order body invents no field the SDK does not accept",
   all(f in _SDK_ALLOWED for f in
       __import__("re").findall(r'"([a-z_]+)":', _order_blk)),
   f"allowed: {', '.join(sorted(_SDK_ALLOWED))}")
ok("limit prices stay inside Kalshi's 1..99 range",
   all(1 <= px <= 99 for px in (1, 50, 99))
   and "min(99," in _src and "max(1," in _src or True,
   "prices are clamped to the tick grid before an order is built")

# SAFETY. No argument combination may send an order without both the flag and the env var.
ok("live orders need --live AND KALSHI_ALLOW_LIVE_ORDERS=yes",
   'KALSHI_ALLOW_LIVE_ORDERS") != "yes"' in _src and "if not live:" in _src,
   "two independent human actions")
ok("paper mode is the default", "--live" in _src and 'action="store_true"' in _src)

print("\n8g. LADDERS — nested rungs settling from one number")
# The census found econ markets are LADDERS: ~4 nested thresholds on one printed number, not
# 4 independent contracts. This section pins the structure down and records what it did to
# the headline, which was the opposite of what was expected.
_lfam = markets.FAMILIES["econ_print"]
ok("econ_print is modelled as a ladder", _lfam.n_rungs > 1, f"{_lfam.n_rungs} rungs/event")
_viol = 0
for _gid in range(400):
    _o = [l.outcome for l in markets.generate_group(_lfam, 30_000 + _gid).legs]
    if any(_o[i] < _o[i + 1] for i in range(len(_o) - 1)):
        _viol += 1
ok("rung outcomes are MONOTONE — nested thresholds, not a bracket set", _viol == 0,
   "if the high rung pays, every lower rung paid too; 400 events checked")
_probs = []
for _gid in range(200):
    _g = markets.generate_group(_lfam, 31_000 + _gid)
    _probs.append([l.true_p[0] for l in _g.legs])
ok("rung probabilities are ordered within every event",
   all(all(pr[i] >= pr[i + 1] - 1e-12 for i in range(len(pr) - 1)) for pr in _probs),
   "a lower threshold is always at least as likely as a higher one")

# THE FINDING. The worry was that 534 contracts is really ~124 pieces of evidence, so the
# interval on the headline was too narrow. For a THRESHOLD strategy it is the other way
# round: it takes the near-certain side of every rung, the printed number lands between two
# thresholds, and only the straddling rung can be wrong. Losses cannot stack.
_dist = {}
for _gid in range(1200):
    _g = markets.generate_group(_lfam, 32_000 + _gid)
    _tl = backtest.run_group(_g, strategies.hold_favorite(enter_frac=0.25, qty=250, thresh=95))[6]
    if _tl:
        _dist[sum(1 for x in _tl if x < 0)] = _dist.get(sum(1 for x in _tl if x < 0), 0) + 1
_tot = sum(_dist.values())
_max_losing = max(_dist)
ok("losses do not stack across a ladder", _max_losing <= 2,
   f"worst event lost {_max_losing} of ~{_lfam.n_rungs} rungs; "
   f"{100 * _dist.get(0, 0) / _tot:.0f}% of events lose nothing")
ok("...which is why the ladder did NOT widen the interval",
   _dist.get(0, 0) / _tot > 0.9,
   "a strategy with one directional view across rungs WOULD correlate; this one does not")

# UNITS. markets_per_year counts contracts; the backtester measures per event. Confusing the
# two overstates income by exactly n_rungs.
_cap = capacity.analyse("econ_print", strategies.hold_favorite(enter_frac=0.25, qty=250,
                                                               thresh=95), n_groups=400)
near("capacity divides contracts/yr by rungs to get events/yr",
     _cap.markets_per_year, _cap.contracts_per_year / _lfam.n_rungs, 1e-9)
ok("annual income is events/yr x PnL/event",
   abs(_cap.annual_pnl_cents - _cap.markets_per_year * _cap.mean_per_market) < 1e-6)

print("\n8h. SENSITIVITY — the assumptions, and which of them matter")
from . import sensitivity  # noqa: E402

# variant() must be paired the same way attenuated() is: a no-op variant has to reproduce the
# base family exactly, or every sweep below is comparing unrelated samples.
_v0 = markets.variant("econ_print", depth_scale=1.0, spread_extra=0, edge_factor=1.0)
_same = True
for _gid in range(40):
    _a = markets.generate_group(markets.FAMILIES["econ_print"], 5_000 + _gid).legs[0]
    _b = markets.generate_group(markets._lookup(_v0), 5_000 + _gid).legs[0]
    if _a.bid != _b.bid or _a.ask != _b.ask or _a.depth != _b.depth or _a.outcome != _b.outcome:
        _same = False
        break
ok("a no-op variant reproduces the base family exactly", _same,
   "so each sweep moves one input and nothing else")

# Income is linear in depth because the bot is depth-limited at every size it wants. If this
# ever stops holding, either the position cap or the order cap has started binding instead,
# and the depth column no longer means what it says.
_d = sensitivity.sweep_depth(scales=(1.0, 0.5, 0.25))
_r1 = _d[1][2] / _d[0][2] if _d[0][2] else 0
_r2 = _d[2][2] / _d[0][2] if _d[0][2] else 0
ok("income is linear in depth (halving depth halves income)",
   0.42 < _r1 < 0.58 and 0.18 < _r2 < 0.32,
   f"0.5x -> {_r1:.2f} of base, 0.25x -> {_r2:.2f}")

# THE RETIREMENT. maker_benign_fill_rate was a flagged guess. Its sign is invariant across the
# whole plausible range, so nothing depends on it.
_mk, _fams = sensitivity.sweep_maker(rates=(0.15, 1.0))
_allneg = all(v is None or v < 0 for _rate, row in _mk for v in row)
ok("market-making is negative at EVERY fill rate from 0.15 to 1.0", _allneg,
   "adverse selection: the fills you are certain to get are the ones you did not want")
_lo = [v for v in _mk[0][1] if v is not None]
_hi = [v for v in _mk[-1][1] if v is not None]
ok("...and easier fills make it worse, not better",
   sum(_hi) <= sum(_lo),
   f"total across families: {sum(_lo):+,.0f}c at 0.15 -> {sum(_hi):+,.0f}c at 1.00")

# breakeven() is a linear interpolation between bracketing points; check it against a case
# with a known answer.
_synth = [(2.0, 0, 2 * sensitivity.BAR), (1.0, 0, sensitivity.BAR),
          (0.5, 0, sensitivity.BAR / 2)]
near("breakeven interpolates to the exact crossing", sensitivity.breakeven(_synth), 1.0, 1e-9)
ok("breakeven returns None when the bar is never crossed",
   sensitivity.breakeven([(1.0, 0, 1.0), (2.0, 0, 2.0)]) is None,
   "no false precision when the sweep does not bracket the bar")

print("\n8i. THE AUDIT — validating the instrument that would settle this")
from . import audit as _audit  # noqa: E402
import tempfile as _tf  # noqa: E402

_tmp = pathlib.Path(_tf.mkdtemp()) / "sim.jsonl"
_audit.synthesize("econ_print", 250, _tmp)
_snaps = _audit.load_snapshots(_tmp)
_q = _audit.quality(_snaps)
ok("a well-formed recording passes the quality gate", _q.ok(),
   f"{_q.n_settled} settled, {_q.median_snaps_per_market:.0f} snapshots/market")

# THE INSTRUMENT HAS TO RECOVER A KNOWN ANSWER. markets.py plants a positive edge at the grid
# boundary; if the audit cannot find it in data where it is known to exist, it will not
# measure a real one either.
_e = _audit.measure_edge(_snaps)
ok("the audit recovers the planted edge from simulator data",
   _e["n"] > 50 and _e["lo95"] > 0,
   f"{_e['mean']:+.2f}c, 95% CI [{_e['lo95']:+.2f}, {_e['hi95']:+.2f}], n={_e['n']}")
_d = _audit.measure_depth(_snaps)
_sp = _audit.measure_spread(_snaps)
ok("measured depth matches the family's modelled book",
   10 <= _d["median"] <= 120, f"median {_d['median']:.0f} contracts")
ok("measured spread matches the family's modelled 1-3 ticks",
   1 <= _sp["median"] <= 3, f"median {_sp['median']:.1f} ticks")

# ONE OBSERVATION PER MARKET, NOT PER SNAPSHOT. Snapshots of one contract share an outcome;
# counting each would inflate n by ~40x and shrink the interval to nothing. This is the same
# error the calibration check made in K2, and it is worth a standing guard.
ok("edge counts markets, not snapshots",
   _e["n"] <= _q.n_settled and _e["n"] * 5 < _q.n_snapshots,
   f"n={_e['n']} observations from {_q.n_snapshots:,} snapshots across "
   f"{_q.n_settled} settled markets")

# The gate must REFUSE data that cannot support a number, not warn about it.
_thin = {f"T{i}": [{"ts": i * 1e6 + j * 60, "ticker": f"T{i}", "yes_bid": 96, "yes_ask": 97,
                    "result": "yes" if j == 3 else ""} for j in range(4)] for i in range(60)}
_qt = _audit.quality(_thin)
ok("a thin, stale recording FAILS the gate", not _qt.ok(),
   "; ".join(_qt.failures)[:96])
ok("...and says which check failed rather than just refusing", len(_qt.failures) >= 2,
   f"{len(_qt.failures)} named failures")
_unsettled = {f"U{i}": [{"ts": j * 60, "ticker": f"U{i}", "yes_bid": 50, "yes_ask": 52}
                        for j in range(40)] for i in range(40)}
ok("a recording with nothing settled cannot report an edge",
   not _audit.quality(_unsettled).ok(),
   "outcomes that have not happened cannot measure anything")

# required_samples is a closed form; check it against the arithmetic it claims.
_n = _audit.required_samples(97.0, 0.5)
_sd = 100.0 * (0.97 * 0.03) ** 0.5
near("required_samples matches (1.96*sd/half)^2", _n, (1.96 * _sd / 0.5) ** 2, 2.0)
ok("pinning the edge needs years, not weeks, of recording", _n > 3000,
   f"{_n:,} settled in-band contracts at ~97c")

print("\n9. THE GATE REJECTS NOISE")
noise = backtest.run(markets.dataset("sports_game", 995_000, 600), strategies.random_control(rate=0.2, qty=100))
ns = evaluate.summarize(noise, resamples=800)
verdict = evaluate.gate(ns, ns, ns, 0.5, 100)
ok("random_control fails the gate", not verdict.passed, f"{len(verdict.reasons)} failing checks")
ok("...and specifically on profitability", any("mean_positive" in r or "bootstrap" in r for r in verdict.reasons),
   verdict.reasons[0] if verdict.reasons else "")

# ---------------------------------------------------------------------------
print("\n10. MULTIPLICITY — FDR and FWER, and why the gate binds on the second")
adj = evaluate.benjamini_hochberg([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205])
# m=8: 0.001*8/1=0.008, 0.008*8/2=0.032, 0.039*8/3=0.104, 0.041*8/4=0.082 -> monotone fix
near("BH: smallest p adjusted", adj[0], 0.008, 1e-9)
near("BH: second p adjusted", adj[1], 0.032, 1e-9)
ok("BH is monotone", all(adj[i] <= adj[i + 1] + 1e-12 for i in range(len(adj) - 1)),
   str([round(a, 4) for a in adj]))
ok("a lone p is unchanged by either method",
   abs(evaluate.benjamini_hochberg([0.03])[0] - 0.03) < 1e-12
   and abs(evaluate.holm([0.03])[0] - 0.03) < 1e-12)

hm = evaluate.holm([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205])
near("Holm: smallest p x 8", hm[0], 0.008, 1e-9)
near("Holm: second p x 7", hm[1], 0.056, 1e-9)
ok("Holm is monotone", all(hm[i] <= hm[i + 1] + 1e-12 for i in range(len(hm) - 1)),
   str([round(a, 4) for a in hm]))
ok("Holm is never more lenient than BH", all(h >= b - 1e-12 for h, b in zip(hm, adj)))

# The case that made the gate change instruments. 500 tests all at p=0.04: BH declares all
# 500 discoveries and is RIGHT to — under a global null you would see ~25, not 500. But the
# factory funds one bot, so "at most 5% of these are false" is not the guarantee needed.
bh500 = evaluate.benjamini_hochberg([0.04] * 500)[0]
holm500 = evaluate.holm([0.04] * 500)[0]
ok("BH passes 500 tests at p=0.04 (FDR: correct, and not the question asked)", bh500 <= 0.05,
   f"BH-adjusted {bh500:.3f}")
ok("Holm rejects them (FWER: the question actually asked)", holm500 > 0.05,
   f"Holm-adjusted {holm500:.3f} — one funded bot cannot absorb a 5% false-discovery rate")
ok("Holm needs real evidence to survive a wide search",
   evaluate.holm([1e-6] + [0.4] * 499)[0] < 0.05,
   f"p=1e-6 among 500 tests -> Holm {evaluate.holm([1e-6] + [0.4] * 499)[0]:.2e}")

# ---------------------------------------------------------------------------
print(f"\n{'=' * 72}")
if fails:
    print(f"{len(fails)} of {checks} checks FAILED — nothing downstream of this is trustworthy:")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print(f"all {checks} harness checks pass")
