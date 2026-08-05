# Kalshi Bot Factory — Coverage Matrix

Every market family against every strategy: 9 x 13 = 117 cells, best of 4 parameter draws each, 300 markets per cell.

**In-sample only, and every cell is the maximum of a small search.** Positive numbers here are where to look, not what is true — see `RESULTS.md` for the out-of-sample gate. Simulated markets, not Kalshi.

Mean cents per market offered:

| family | hold_favorite | buy_longshot | band_fade | late_favorite | snr_band | jump_follow | jump_fade | momentum | mean_revert | bracket_arb | pair_arb | maker_spread | random_contro |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `crypto_hourly` | -84 | +89 | -309 | +6 | -36 | -193 | -6349 | -1245 | -277 | n/a | +0 | +0 | -210 |
| `index_bracket_daily` | -203 | -88 | -184 | -39 | -69 | -3314 | -1252 | -2722 | -2099 | +0 | +0 | +0 | -817 |
| `econ_print` | -25 | -262 | +145 | +39 | +190 | -15 | -1188 | -271 | -751 | n/a | +0 | +0 | -950 |
| `weather_temp` | +297 | -186 | +220 | +72 | +1 | -999 | -647 | -909 | -741 | n/a | +0 | +0 | -142 |
| `sports_game` | -8 | -40 | -19 | -31 | -17 | -1358 | -941 | -324 | -480 | n/a | +0 | +0 | -196 |
| `politics_long` | -6 | -26 | +69 | +47 | -6 | -907 | -955 | -2315 | -1244 | n/a | +0 | -287 | -238 |
| `awards_thin` | -20 | -29 | -9 | -12 | -11 | -204 | -359 | -232 | -278 | n/a | +0 | -250 | -42 |
| `mentions_short` | -4 | -59 | +17 | +33 | +4 | -929 | -1093 | -282 | -377 | n/a | +0 | -211 | -230 |
| `efficient_control` | +71 | -154 | +47 | +4 | +35 | -602 | -957 | -255 | -515 | n/a | +0 | +0 | -3 |

### Read the control row first

`efficient_control` is a market with **no edge in it by construction** — gamma exactly 1.0, no quote lag, penny spread. Nothing can beat it. Its best cell scores **+71c per market** (`hold_favorite`), which ranks **#7 of 109** cells in this whole matrix.

That is the entire argument for the rest of this directory. The largest in-sample number produced by a 108-cell search came from a market that cannot be beaten. Every cell above is the maximum of four draws, and maxima of noise are large and positive. In-sample ranking is a way to decide what to test next; it is not evidence.

Second symptom of the same thing: 1 of the 5 strategies **designed to lose** (buy_longshot) show a positive best cell somewhere in this table.

## Best strategy per family

| family | best strategy in-sample | mean/market | ann. return | targets |
|---|---|---|---|---|
| `crypto_hourly` | buy_longshot(enter_frac=0.25,max_price=20,qty=100) | +89.3c | +98991%/yr | EDGE 1 sign control — expected to LOSE |
| `index_bracket_daily` | bracket_arb(min_edge=2,qty=25) | +0.0c | +0%/yr | EDGE 3 (bracket incoherence) — riskless |
| `econ_print` | snr_band(enter_frac=0.0,hi=98,lo=96,qty=100) | +190.1c | +3199%/yr | EDGE 1+5, narrowed to the best signal-to-noise window |
| `weather_temp` | hold_favorite(enter_frac=0.0,qty=250,thresh=65) | +297.5c | +799%/yr | EDGE 1 (longshot compression) |
| `sports_game` | pair_arb(min_edge=0,qty=100) | +0.0c | +0%/yr | nothing — structurally impossible, reported as zero |
| `politics_long` | band_fade(enter_frac=0.3,hi=25,lo=2,qty=100) | +69.3c | +15%/yr | EDGE 1, narrowed by search — overfitting canary |
| `awards_thin` | pair_arb(min_edge=1,qty=100) | +0.0c | +0%/yr | nothing — structurally impossible, reported as zero |
| `mentions_short` | late_favorite(enter_frac=0.8,qty=100,thresh=85) | +33.3c | +1091%/yr | EDGE 1, capital-efficient variant |
| `efficient_control` | hold_favorite(enter_frac=0.25,qty=100,thresh=95) | +70.5c | +19607%/yr | EDGE 1 (longshot compression) |

## Best family per strategy

| strategy | best family in-sample | mean/market |
|---|---|---|
| `hold_favorite` | weather_temp | +297.5c |
| `buy_longshot` | crypto_hourly | +89.3c |
| `band_fade` | weather_temp | +219.8c |
| `late_favorite` | weather_temp | +72.1c |
| `snr_band` | econ_print | +190.1c |
| `jump_follow` | econ_print | -15.0c |
| `jump_fade` | awards_thin | -359.0c |
| `momentum` | awards_thin | -231.5c |
| `mean_revert` | crypto_hourly | -277.1c |
| `bracket_arb` | index_bracket_daily | +0.0c |
| `pair_arb` | crypto_hourly | +0.0c |
| `maker_spread` | crypto_hourly | +0.0c |
| `random_control` | efficient_control | -3.0c |
