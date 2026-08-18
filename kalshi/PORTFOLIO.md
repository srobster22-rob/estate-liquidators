# Kalshi Bot Factory — Portfolio

The dollar bar belongs on the portfolio; the statistical criteria belong on each bot. Every member below cleared criteria 1-10 of the gate on its own — out-of-sample significance after Holm correction, holdout, stress, half-edge world and rare-loss tail. Only the total is asked to clear the money bar.

All figures measured on the **holdout** seed range, not out-of-sample: OOS is where members are selected, so OOS means of selected bots run high. For the incumbent the gap was 85.6¢ vs a true 48.8¢ per market.

| member | markets/yr | ¢/market | annual $ | capital |
|---|---|---|---|---|
| `econ_print` / snr_band(enter_frac=0.25,hi=98,lo=96,qty=100) | 133.5 | +252.7¢ | $337 | $69 |
| **portfolio** | | | **$337** | **$69** |

- 95% CI on annual income: **$253 to $418**
- bootstrap p: 0.0002
- return on committed capital: 488%/yr
- best single member: $337/yr — the portfolio is 1.00x it
- diversification: interval is **1.00x tighter** than if the members moved together

**Verdict: the portfolio CLEARS the $250/yr bar.**

## The caveat that matters

Independence is true in this simulator by construction and is the weakest assumption on this page. On the real exchange these strategies are all short the same tail — every one of them buys a near-certain outcome and loses when the improbable happens — and a macro shock moves econ prints, index brackets and crypto together. The diversification figure is an upper bound and the correlated-crash case is not modelled anywhere in this directory.

