# Kalshi Bot Factory — Information Cost

For a strategy with edge `e` and standard deviation `s` per opportunity, appearing `f` times a year:

```
income  = f * e / 100                      dollars a year
years   = (1.96 * s / e)^2 / f             to establish the SIGN of the edge

income x years = 3.8416 * s^2 / (100 * e)  <- f cancels, exactly
```

So **information cost `I = s²/e`** is a frequency-invariant measure of how good an opportunity is, and every strategy satisfies `income × years = 0.0384 · I`.

| strategy | ¢/opportunity | σ | **I = s²/e** | opp/yr | $/yr | yrs to sign |
|---|---|---|---|---|---|---|
| `index_bracket_daily` / bracket_arb(min_edge=0,qty=25) | +2.2¢ | 14¢ | **84** | 150 | $+3 | 0.98 |
| `crypto_bracket_stale` / bracket_arb(min_edge=0,qty=100) | +14.0¢ | 85¢ | **513** | 3,504 | $+489 | 0.04 |
| `econ_print` / snr_band(enter_frac=0.0,hi=97,lo=9 | +84.6¢ | 399¢ | **1,883** | 134 | $+113 | 0.64 |
| `econ_print` / late_favorite(enter_frac=0.8,qty=2 | +57.7¢ | 442¢ | **3,378** | 134 | $+77 | 1.68 |
| `awards_thin` / late_favorite(enter_frac=0.9,qty=2 | +15.1¢ | 237¢ | **3,724** | 150 | $+23 | 6.33 |
| `mentions_short` / late_favorite(enter_frac=0.8,qty=2 | +25.6¢ | 479¢ | **8,962** | 500 | $+128 | 2.69 |
| `awards_thin` / band_fade(enter_frac=0.0,hi=15,lo= | +8.7¢ | 312¢ | **11,243** | 150 | $+13 | 33.26 |
| `crypto_bracket_stale` / late_favorite(enter_frac=0.9,qty=2 | +67.0¢ | 992¢ | **14,679** | 3,504 | $+2,349 | 0.24 |
| `mentions_short` / hold_favorite(enter_frac=0.5,qty=2 | +28.7¢ | 666¢ | **15,483** | 500 | $+143 | 4.15 |
| `sports_game` / late_favorite(enter_frac=0.9,qty=1 | +48.6¢ | 909¢ | **17,010** | 6,000 | $+2,915 | 0.22 |
| `politics_long` / band_fade(enter_frac=0.3,hi=15,lo= | +35.6¢ | 869¢ | **21,221** | 200 | $+71 | 11.46 |
| `mentions_short` / band_fade(enter_frac=0.3,hi=40,lo= | +29.8¢ | 818¢ | **22,500** | 500 | $+149 | 5.81 |
| `sports_game` / snr_band(enter_frac=0.0,hi=97,lo=9 | +4.7¢ | 354¢ | **26,884** | 6,000 | $+279 | 3.70 |
| `sports_game` / hold_favorite(enter_frac=0.0,qty=2 | +5.3¢ | 405¢ | **30,813** | 6,000 | $+320 | 3.70 |
| `awards_thin` / hold_favorite(enter_frac=0.5,qty=1 | +2.1¢ | 279¢ | **37,246** | 150 | $+3 | 455.68 |
| `politics_long` / hold_favorite(enter_frac=0.25,qty= | +24.7¢ | 1,363¢ | **75,349** | 200 | $+49 | 58.69 |
| `crypto_bracket_hourly` / late_favorite(enter_frac=0.9,qty=1 | +221.0¢ | 5,798¢ | **152,122** | 3,504 | $+7,743 | 0.75 |
| `index_bracket_daily` / late_favorite(enter_frac=0.9,qty=2 | +1.4¢ | 814¢ | **467,196** | 150 | $+2 | 8438.08 |

## What this corrects

After K22 I summarised the project as hitting *"three structural walls, each blocking the corner opposite"*. The arithmetic says that is partly wrong:

- **Frequency is free and unambiguously good.** Doubling `f` doubles income *and* halves validation time. It is not a wall and it has no cost — which is exactly why the census mattered.
- **Information cost is the hard part.** Lowering `I` is the only way to improve both at once, and it is a property of the *structure*: where in the price grid you trade, whether the payoff is bounded, how many legs you need.

They are **independent axes**, not one tradeoff. Conflating them produced the wrong summary.

## Where that points

Ranked by `I`, the best structure here is **`index_bracket_daily` / bracket_arb(min_edge=0,qty=25)`** at **I = 84** — an order of magnitude below the directional strategies, because a locked-in profit has almost no variance conditional on firing.

Its problem is *entirely* frequency: 150 opportunities a year, and it fires in about 3% of them. **It is not a bad trade, it is a good trade that hardly ever happens** — a different diagnosis from "riskless arbs don't work", and it points somewhere specific: a bracket-structured family with real frequency would dominate everything else in this directory.

## K24 — the prediction came true, via a mechanism K23 had not modelled

K23 predicted from this ranking that a bracket family at 23× the frequency should dominate, built one, and got **$0.00** — concluding that tight books are coherent books. That conclusion held only because independent per-leg `quote_noise` was the simulator's *only* incoherence channel. Add **asymmetric staleness** — one leg's quote frozen while the others track, which needs no wide book at all — and the same tight 0.6¢ family appears here at **I = 513**, **$489/yr**, signable in **0.5 months** rather than years.

So the *algebra* was right — low `I` plus high `f` is where to look — and the *search* was too narrow. `I` told us the shape of a good opportunity; it could not tell us which mechanism would produce one. See `ARB.md` and README finding 19, including the two gate criteria it still fails.

## Identity check

`income × years == 0.0384 · I` verified on every row:

- OK — index_bracket_daily/bracket_arb(min_edge=0,qty=2
- OK — crypto_bracket_stale/bracket_arb(min_edge=0,qty=1
- OK — econ_print/snr_band(enter_frac=0.0,hi=9
- OK — econ_print/late_favorite(enter_frac=0.8
- OK — awards_thin/late_favorite(enter_frac=0.9
- OK — mentions_short/late_favorite(enter_frac=0.8

