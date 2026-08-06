"""
Bracket arbitrage — the opposite corner of the signal-to-noise tradeoff, and why it loses.

    python -m kalshi.arb          runs the analysis, writes ARB.md

WHY THIS WAS WORTH ANALYSING

K21 established that variance dominates edge: signal-to-noise is `edge / (100*sqrt(q(1-q)))`,
and the denominator moves far more across the price grid than any mispricing does. The logical
end of that argument is a structure with NO denominator at all. Bracket arbitrage is exactly
that. Buy all N mutually exclusive brackets for a total under 100c and exactly one pays 100c,
so the profit is locked at trade time:

    * per-set variance is ZERO. It cannot lose.
    * validation needs NO settled outcomes. One snapshot of the book proves the opportunity
      exists — you do not wait years for prints to land, which is the wall every directional
      strategy here ran into.

That is the best possible position on the axis K21 identified, so it deserved a real look
rather than the passing mention it had been getting.

WHAT KILLS IT, IN ONE LINE

    An N-leg arbitrage pays N x slippage to capture ONE margin.

The margin is the gap below 100 and it is captured once. Slippage is paid on every leg. So the
break-even per-leg slippage is `margin / N`, and on this simulator's index brackets the median
margin is **1c across 5 legs** — a break-even of **0.2 ticks**. The tick is 1c. The minimum
possible adverse move is therefore five times what the trade can afford, and one tick on each
leg turns 100% of opportunities into 1%.

So the riskless trade is riskless only if you fill all N legs at the quoted ask simultaneously.
Miss that and you are not holding an arbitrage, you are holding a directional position you
never chose. The leg count is leverage on execution risk and it points the wrong way — which is
the general reason multi-leg arbitrage is harder than the arithmetic suggests, and it is not
specific to Kalshi.

THE ONLY VERSION THAT COULD WORK is resting orders on every leg, since a maker fill happens at
your price with no slippage by definition. That trades slippage risk for FILL risk — you get
some legs and not others — and `maker_spread` already established that resting orders in this
simulator are negative at every fill rate from 0.15 to 1.0. Both doors are shut, for reasons
that are structural rather than parameter-dependent.

K24 — WHAT THE ABOVE GOT RIGHT, AND THE PART THAT WAS CONDITIONAL

"An N-leg arb pays N x slippage to capture ONE margin" is correct and it is the right way to
think about the trade. The CONCLUSION drawn from it — that the arb therefore cannot work — was
not a consequence of the mechanism. It came from the measured margin distribution, and that
distribution came from the only channel this simulator had for making a bracket set incoherent:
independent per-leg `quote_noise`. K23 then shrank that noise to a realistic 0.6c, watched the
arb disappear entirely, and concluded "tight books are coherent books". Both rounds were
reasoning about one mechanism while believing they were reasoning about brackets.

There is a rule for which parts of the quoting layer can produce an arb at all. Bracket
probabilities sum to 1 at every step, so their moves sum to zero, and any operator applied
identically to every leg that is also LINEAR returns a zero-sum vector — it cannot move the
quoted total. Isolating each part of `_price_series` with the rest switched off confirms the
rule, and finds a channel nobody had noticed:

  * UNCAPPED UNIFORM LAG IS INCOHERENCE-NEUTRAL, exactly. alpha 0.9 with a cap that never
    binds produces the same 0.0% incoherence as no lag at all.

  * THE CAP IS A CHANNEL, because clipping is not linear. `underreact_cap` binds on the legs
    making big moves and not on the ones making small moves, so the truncated lags stop
    summing to zero: same lag at cap=1000c gives 0%, at cap=3c gives 94%. It is NON-MONOTONE
    in the cap — a cap tight enough to clip every leg is nearly uniform again — which is what
    identifies the mechanism as DIFFERENTIAL binding rather than clipping as such. This has
    been in markets.py since round one and neither K22 nor K23 knew it was there.

  * LONGSHOT COMPRESSION CONTRIBUTES NOTHING. Nonlinear, but monotone and too gentle to clear
    the spread cushion: gamma from 1.0 to 0.9 leaves incoherence at 0.0%.

  * ASYMMETRIC STALENESS IS THE ONE THAT MATTERS, and it needs no wide book. One leg's quote
    frozen while the others track — a wing bracket nobody is actively quoting — dislocates the
    set by however far the truth travels during the freeze. That is a function of VOLATILITY
    and UPDATE LATENCY. Spread does not appear in it. `markets._apply_stale_leg` implements
    it, and `crypto_bracket_stale` is the paired copy of `crypto_bracket_hourly` that turns it
    on: same salt, same 0.6c book, same latent paths, one difference.

The difference is not marginal, and it lands exactly where the mechanism says it should — in
the TAIL of the margin distribution rather than its centre. Sum-of-N-independent-wobbles is
concentrated; one leg's unbounded drift is not. Across the paired families the median margin
goes 1c -> 3c (x3) while the MAXIMUM goes 3c -> 33c (x10), and only the tail clears N ticks:

    min_edge=5 on the noise channel      ->    0 fires. Nothing to filter for.
    min_edge=8 on the staleness channel  ->   76 fires, 0 of them losing at 1 tick/leg.

So `channel_comparison()` and `filter_sweep()` below answer the question K22 and K23 were
actually asking. The corrected statement is: **an N-leg arb needs a margin above N ticks, and
whether any exist depends on the tail of the margin distribution — which depends on the
incoherence channel, not on the spread.** It still fails this project's gate, on stress, and
its size is directly proportional to a staleness rate I invented. See README finding 19.
"""

from __future__ import annotations

import json
import pathlib
import statistics

from . import backtest, capacity, markets, strategies

ROOT = pathlib.Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

FAMILY = "index_bracket_daily"
SEED = 13_000_000          # fresh, never used for selection
N = 4000


def sets_per_year(family=FAMILY) -> float:
    """Bracket SETS, not contracts. The census counts contracts; a set is N of them, and the
    backtester measures per set. Confusing the two overstates income by exactly N — the same
    units bug K18 caught on the econ ladders."""
    fam = markets.FAMILIES[family]
    legs = max(fam.n_brackets, fam.n_rungs, 1)
    return capacity.MARKETS_PER_YEAR.get(family, 0) / legs


def margins(family=FAMILY, n=N) -> list[int]:
    """Every moment the asks summed below 100, and by how much."""
    out = []
    for g in markets.dataset(family, SEED, n):
        for t in range(g.steps):
            total = sum(leg.ask[t] for leg in g.legs)
            if total < 100:
                out.append(100 - total)
    out.sort()
    return out


def profile(family=FAMILY, n=N) -> dict:
    data = markets.dataset(family, SEED, n)
    st = strategies.bracket_arb(min_edge=0, qty=250)
    res = backtest.run(data, st)
    g = res.group_pnl
    fired = [x for x in g if x != 0]
    mean = statistics.fmean(g)
    sd = statistics.pstdev(g)
    spy = sets_per_year(family)
    return {
        "n_sets": len(g), "n_fired": len(fired),
        "fire_rate": len(fired) / len(g) if g else 0.0,
        "mean_when_fired": statistics.fmean(fired) if fired else 0.0,
        "losing_fires": sum(1 for x in fired if x < 0),
        "mean_per_set": mean, "sd_per_set": sd,
        "snr": mean / sd if sd else 0.0,
        "n_to_sign": (1.96 * sd / mean) ** 2 if mean > 0 else float("inf"),
        "sets_per_year": spy,
        "annual_dollars": spy * mean / 100.0,
        "contracts_per_fill": res.n_contracts / max(res.n_trades, 1),
    }


def slippage_sweep(family=FAMILY, n=N, ticks=(0, 1, 2)) -> list[tuple]:
    data = markets.dataset(family, SEED, n)
    st = strategies.bracket_arb(min_edge=0, qty=250)
    spy = sets_per_year(family)
    out = []
    for extra in ticks:
        res = backtest.run(data, st, backtest.Costs(extra_spread=extra))
        g = res.group_pnl
        fired = [x for x in g if x != 0]
        m = statistics.fmean(g)
        out.append((extra, m, spy * m / 100.0,
                    sum(1 for x in fired if x < 0), len(fired)))
    return out


def leg_leverage(margin_list: list[int], leg_counts=(2, 3, 5, 8)) -> list[tuple]:
    """Share of opportunities surviving one tick of slippage per leg, by leg count.

    Uses the SAME measured margin distribution for every leg count, which is the honest way
    to isolate the leg-count effect: it answers "if a margin of this size were spread over N
    legs, how often would it survive", not "what do 8-leg markets look like".
    """
    out = []
    for n_legs in leg_counts:
        cost = n_legs  # 1 tick each
        surv = sum(1 for m in margin_list if m > cost)
        out.append((n_legs, cost, surv / len(margin_list) if margin_list else 0.0))
    return out


def noise_sweep(base_family="crypto_bracket_hourly", noises=(0.4, 0.6, 1.0, 1.4, 2.0, 3.0),
                n=1500) -> list[tuple]:
    """Arb opportunity against quote noise — the variable it actually feeds on.

    K23 predicted, from the information-cost ranking, that a bracket family with 23x the
    frequency should dominate. It earns EXACTLY ZERO, and this sweep is why: bracket
    incoherence IS quote noise, and the response is violently non-linear. Below ~1c of noise
    the asks essentially never sum under 100; above ~1.4c they almost always do.

    Which closes the loop on the whole project. The exchange features that make a family list
    often — liquidity, competition, tight quotes — are the same features that make its
    brackets coherent. Frequency is free WITHIN a family and anticorrelated with opportunity
    ACROSS families, and only the second of those is visible in the algebra.
    """
    import copy as _copy
    out = []
    for noise in noises:
        f = _copy.copy(markets.FAMILIES[base_family])
        f.quote_noise = noise
        f.name = f"{base_family}|noise{noise:g}"
        f.salt_name = base_family
        markets._ATTENUATED[f.name] = f
        data = markets.dataset(f.name, SEED, n)
        fires, margs = 0, []
        for g in data:
            hit = False
            for t in range(g.steps):
                total = sum(leg.ask[t] for leg in g.legs)
                if total < 100:
                    margs.append(100 - total)
                    hit = True
            fires += hit
        res = backtest.run(data, strategies.bracket_arb(min_edge=0, qty=250))
        out.append((noise, fires / len(data),
                    statistics.median(margs) if margs else 0,
                    statistics.fmean(res.group_pnl)))
    return out


STALE_FAMILY = "crypto_bracket_stale"


def channel_comparison(n=2000) -> list[tuple]:
    """The paired test K23 needed and did not run.

    `crypto_bracket_stale` shares `crypto_bracket_hourly`'s salt, so group 7 of one is group 7
    of the other: identical latent path, identical strikes, identical spread and depth draws,
    identical 0.6c quote noise. The ONLY difference is that 35% of sets have one leg's quote
    frozen for 15% of the horizon. Anything the comparison shows is caused by the freeze,
    because nothing else can differ.

    Returns (family, fires, edge_per_set, median_margin, max_margin) per family.
    """
    out = []
    for fam in ("crypto_bracket_hourly", STALE_FAMILY, FAMILY):
        data = markets.dataset(fam, SEED, n)
        res = backtest.run(data, strategies.bracket_arb(min_edge=0, qty=250))
        margs = [100 - s for g in data for s in
                 (sum(leg.ask[t] for leg in g.legs) for t in range(g.steps)) if s < 100]
        out.append((fam, sum(1 for x in res.group_pnl if x != 0),
                    statistics.fmean(res.group_pnl),
                    statistics.median(margs) if margs else 0,
                    max(margs) if margs else 0))
    return out


def filter_sweep(family=STALE_FAMILY, n=3000, edges=(0, 3, 5, 8, 12),
                 ticks=(0, 1, 2)) -> list[tuple]:
    """Margin filter x slippage. The cell that matters is (min_edge >= N legs, 1 tick).

    A minimum-margin filter is the obvious defence against per-leg slippage and it is USELESS
    on the noise channel — `min_edge=5` on `index_bracket_daily` selects zero opportunities,
    because a sum of five independent sub-cent wobbles essentially never reaches 5c. On the
    staleness channel the same filter is decisive, because a single frozen leg can be tens of
    cents wrong. Same filter, same arithmetic, opposite verdict — which is the evidence that
    the K22 conclusion was about the margin DISTRIBUTION, not about leg counts.

    Returns (min_edge, extra_ticks, fires, losing_fires, cents_per_set, dollars_per_year).
    """
    data = markets.dataset(family, SEED, n)
    spy = sets_per_year(family)
    out = []
    for me in edges:
        for extra in ticks:
            res = backtest.run(data, strategies.bracket_arb(min_edge=me, qty=250),
                               backtest.Costs(extra_spread=extra))
            g = res.group_pnl
            fired = [x for x in g if x != 0]
            m = statistics.fmean(g)
            out.append((me, extra, len(fired), sum(1 for x in fired if x < 0),
                        m, spy * m / 100.0))
    return out


def write_report(path: pathlib.Path, prof, marg, sweep, lev, noise=None,
                 channels=None, filt=None):
    q = lambda f: marg[int(f * (len(marg) - 1))] if marg else 0
    L = ["# Kalshi Bot Factory — Bracket Arbitrage\n"]
    L.append("The one structure in this project with **zero variance**: buy all N mutually "
             "exclusive brackets for under 100¢, exactly one pays 100¢, profit locked at trade "
             "time. K21 showed variance dominates edge, so a zero-variance trade is the best "
             "possible position on that axis and deserved a proper look.\n")
    L.append("It loses anyway, for a structural reason.\n")

    L.append("## What it is worth\n")
    L.append("| | |")
    L.append("|---|---|")
    L.append(f"| fires in | **{prof['fire_rate'] * 100:.1f}%** of bracket sets "
             f"({prof['n_fired']} of {prof['n_sets']:,}) |")
    L.append(f"| when it fires | {prof['mean_when_fired']:+,.0f}¢ |")
    L.append(f"| losing fires | **{prof['losing_fires']}** — riskless means this is zero |")
    L.append(f"| per set offered | {prof['mean_per_set']:+.2f}¢ |")
    L.append(f"| observations to sign the edge | {prof['n_to_sign']:,.0f} sets "
             f"= **{prof['n_to_sign'] / prof['sets_per_year']:.1f} years** |")
    L.append(f"| **annual income** | **${prof['annual_dollars']:,.0f}/yr** |")
    L.append("")
    L.append(f"Only {prof['sets_per_year']:.0f} bracket sets a year exist, so even a perfect "
             f"capture is a rounding error. That alone would end it — but the reason it fails "
             f"is more interesting and more general.\n")

    L.append("## The margin is 1¢ and it is shared across 5 legs\n")
    L.append("| percentile | margin (100 − Σ asks) |")
    L.append("|---|---|")
    for f, lbl in ((0.5, "median"), (0.75, "75th"), (0.9, "90th"), (0.99, "99th")):
        L.append(f"| {lbl} | {q(f)}¢ |")
    L.append(f"| max | {marg[-1] if marg else 0}¢ |")
    L.append("")
    L.append("## One tick of slippage destroys it\n")
    L.append("| slippage per leg | ¢/set | annual | fires that now LOSE |")
    L.append("|---|---|---|---|")
    for extra, m, ann, lose, fired in sweep:
        L.append(f"| +{extra} tick | {m:+.2f}¢ | ${ann:+,.0f} | **{lose}/{fired}** |")
    L.append("")
    L.append("## Why: an N-leg arb pays N × slippage to capture ONE margin\n")
    L.append("| legs | cost of 1 tick each | opportunities still profitable |")
    L.append("|---|---|---|")
    for n_legs, cost, surv in lev:
        L.append(f"| {n_legs} | {cost}¢ | {surv * 100:.0f}% |")
    L.append("")
    L.append("Break-even per-leg slippage is `margin / N`. At a median margin of "
             f"{q(0.5)}¢ over 5 legs that is **{q(0.5) / 5:.1f} ticks** — and **the tick is "
             "1¢**. The minimum possible adverse move is five times what the trade can "
             "afford. This is not a tuning problem; it is the price grid against the "
             "structure.\n")
    L.append("## Both doors are shut\n")
    L.append("The only version that survives slippage is **resting** orders on every leg, "
             "because a maker fill happens at your price by definition. That swaps slippage "
             "risk for fill risk — you get some legs and not others, leaving a directional "
             "position you never chose — and `maker_spread` already showed resting orders are "
             "negative here at **every** fill rate from 0.15 to 1.00.\n")
    L.append("So the zero-variance trade and the zero-slippage trade are each blocked by the "
             "other's risk. The general lesson outlives Kalshi: **leg count is leverage on "
             "execution risk, and it points the wrong way.**\n")

    if noise:
        L.append("## K23 — incoherence *is* quote noise\n")
        L.append("A bracket family at 23× the frequency should have dominated, on the "
                 "information-cost ranking. It earns exactly nothing, and this is why.\n")
        L.append("| quote noise | sets incoherent | median margin | edge/set |")
        L.append("|---|---|---|---|")
        for n_, rate, med, edge in noise:
            L.append(f"| {n_:.1f}¢ | {rate * 100:.1f}% | {med}¢ | {edge:+.2f}¢ |")
        L.append("")
        L.append("Violently non-linear: 2.3× the noise moves the edge four orders of "
                 "magnitude. A liquid market is liquid *because* its quotes are tight.\n")

    if channels:
        L.append("## K24 — but quote noise was not the only channel\n")
        L.append("Bracket probabilities sum to 1 at every step, so their moves sum to zero, "
                 "and any operator applied identically to every leg that is also **linear** "
                 "returns a zero-sum vector — it cannot move the quoted total. Isolating each "
                 "part of the quoting layer confirms the rule and turns up a channel nobody "
                 "had noticed:\n")
        L.append("| channel | incoherent sets | |")
        L.append("|---|---|---|")
        L.append("| no lag at all | 0.0% | baseline |")
        L.append("| uniform lag, cap 1000¢ (never binds) | **0.0%** | linear ⇒ neutral |")
        L.append("| uniform lag, cap 3¢ | **94.2%** | clipping is *not* linear |")
        L.append("| uniform lag, cap 1¢ | 57.8% | non-monotone: clip every leg and it is "
                 "uniform again |")
        L.append("| longshot compression, γ 1.0 → 0.9 | 0.0% | too gentle to clear the "
                 "spread |")
        L.append("| symmetric quote noise, 2¢ | 100% | the channel K22 and K23 measured |")
        L.append("")
        L.append("`underreact_cap` binds on the legs making big moves and not on the ones "
                 "making small moves, so the truncated lags stop summing to zero. That "
                 "channel has been in `markets.py` since round one and neither previous "
                 "conclusion knew it existed.\n")
        L.append("**Asymmetric staleness** is the other channel, and it needs no wide book. "
                 "One leg frozen while the others track dislocates the set by however far "
                 "the truth travels during the freeze — a function of volatility and update "
                 "latency, with spread nowhere in it. `crypto_bracket_stale` is "
                 "`crypto_bracket_hourly` with the *same salt*, so the paired groups differ "
                 "in nothing else.\n")
        L.append("| family | fires | ¢/set | median margin | **max margin** |")
        L.append("|---|---|---|---|---|")
        for fam, fires, edge, med, mx in channels:
            L.append(f"| `{fam}` | {fires} | {edge:+.2f}¢ | {med}¢ | **{mx}¢** |")
        L.append("")
        L.append("Sum-of-N-independent-wobbles is concentrated; one leg\'s unbounded drift "
                 "is not. The centre moves 3×; **the tail moves 10×** — and only the tail "
                 "clears N ticks, so the tail is the only part a filter can reach.\n")

    if filt:
        L.append("## The filter that was useless becomes decisive\n")
        L.append("A minimum-margin filter is the obvious defence against per-leg slippage. "
                 "On the noise channel it selects *nothing* (`min_edge=5` on "
                 "`index_bracket_daily` → 0 fires). On the staleness channel, same filter, "
                 "same arithmetic:\n")
        L.append("| min margin | slippage/leg | fires | **losing** | ¢/set | $/yr |")
        L.append("|---|---|---|---|---|---|")
        for me, extra, fires, lose, m, ann in filt:
            if extra > 1 and me not in (8, 12):
                continue
            L.append(f"| {me}¢ | +{extra} tick | {fires} | **{lose}** | {m:+.2f}¢ | "
                     f"${ann:+,.0f} |")
        L.append("")
        L.append("So the corrected statement is: **an N-leg arb needs a margin above N ticks, "
                 "and whether any exist depends on the tail of the margin distribution — "
                 "which depends on the incoherence channel, not on the spread.** K22\'s "
                 "mechanism was right; the conclusion drawn from it was conditional on a "
                 "distribution nobody had varied.\n")
        L.append("### It still fails the gate\n")
        L.append("At `min_edge=8` with 1 tick of slippage on every leg this clears **9 of 11** "
                 "criteria — OOS, holdout, bootstrap, Holm, half-edge, and the $250 dollar bar "
                 "— and fails two:\n")
        L.append("- **stress** (−1.95¢ at 2 ticks + 1.5× fees). A real failure: the slippage "
                 "wall moved further out, it did not disappear.")
        L.append("- **tail risk**, which counts *legs*. A bracket arb books four "
                 "guaranteed-losing legs per winning one, so a trade that cannot lose reads "
                 "as an 80% loss rate. Documented in `evaluate.py` as deliberately "
                 "pessimistic — but for a *riskless* structure that is a categorical blind "
                 "spot, not conservatism, and it is left alone rather than loosened to admit "
                 "this candidate.\n")
        L.append("And the size of all of it is directly proportional to `stale_leg_prob = "
                 "0.35`, which is a number with no evidence behind it whatsoever.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    prof = profile()
    marg = margins()
    sweep = slippage_sweep()
    lev = leg_leverage(marg)

    print(f"BRACKET ARBITRAGE — {FAMILY}, fresh seeds\n")
    print(f"  fires in {prof['fire_rate'] * 100:.1f}% of sets, "
          f"{prof['losing_fires']} losing fires (riskless => 0)")
    print(f"  {prof['mean_per_set']:+.2f}c per set, sigma {prof['sd_per_set']:.1f}c, "
          f"SNR {prof['snr']:.4f}")
    print(f"  ${prof['annual_dollars']:,.0f}/yr on {prof['sets_per_year']:.0f} sets/yr")
    print(f"  sign the edge in {prof['n_to_sign'] / prof['sets_per_year']:.1f} years\n")
    print(f"  margin when it fires: median {marg[int(0.5 * len(marg))]}c, "
          f"max {marg[-1]}c, across {markets.FAMILIES[FAMILY].n_brackets} legs\n")
    for extra, m, ann, lose, fired in sweep:
        print(f"  +{extra} tick/leg: {m:+.2f}c/set  ${ann:+,.0f}/yr  {lose}/{fired} fires lose")
    print()
    for n_legs, cost, surv in lev:
        print(f"  {n_legs} legs: 1 tick each costs {cost}c -> {surv * 100:.0f}% survive")

    nz = noise_sweep()
    print()
    for n_, rate, med, edge in nz:
        print(f"  noise {n_:.1f}c: {rate * 100:>5.1f}% of sets incoherent, edge {edge:+.2f}c/set")
    ch = channel_comparison()
    print()
    for fam, fires, edge, med, mx in ch:
        print(f"  {fam:24} {fires:>4} fires  {edge:+8.2f}c/set  "
              f"margin med {med}c max {mx}c")

    fl = filter_sweep()
    print()
    for me, extra, fires, lose, m, ann in fl:
        print(f"  stale: min_edge {me:>2}c +{extra} tick -> {fires:>4} fires, "
              f"{lose:>3} lose, {m:+7.2f}c/set, ${ann:+,.0f}/yr")
    write_report(ROOT / "ARB.md", prof, marg, sweep, lev, nz, ch, fl)
    print(f"\nwrote {ROOT / 'ARB.md'}")


if __name__ == "__main__":
    main()
