# Kalshi Bot Factory — Portfolio

The dollar bar belongs on the portfolio; the statistical criteria belong on each bot. Every member below cleared criteria 1-10 of the gate on its own — out-of-sample significance after Holm correction, holdout, stress, half-edge world and rare-loss tail. Only the total is asked to clear the money bar.

All figures measured on the **holdout** seed range, not out-of-sample: OOS is where members are selected, so OOS means of selected bots run high. For the incumbent the gap was 85.6¢ vs a true 48.8¢ per market.

| member | markets/yr | ¢/market | annual $ | capital |
|---|---|---|---|---|
| `econ_print` / band_fade(enter_frac=0.3,hi=8,lo=2,qty=100) | 250 | +65.8¢ | $164 | $54 |
| **portfolio** | | | **$164** | **$54** |

- 95% CI on annual income: **$24 to $283**
- bootstrap p: 0.0030
- return on committed capital: 307%/yr
- best single member: $164/yr — the portfolio is 1.00x it
- diversification: interval is **1.00x tighter** than if the members moved together

**Verdict: the portfolio does NOT clear the $250/yr bar.**

## The caveat that matters

Independence is true in this simulator by construction and is the weakest assumption on this page. On the real exchange these strategies are all short the same tail — every one of them buys a near-certain outcome and loses when the improbable happens — and a macro shock moves econ prints, index brackets and crypto together. The diversification figure is an upper bound and the correlated-crash case is not modelled anywhere in this directory.

