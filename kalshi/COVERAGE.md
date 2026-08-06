# Kalshi Bot Factory — Coverage Matrix

Every market family against every strategy: 11 x 13 = 143 cells, best of 4 parameter draws each, 300 markets per cell.

**In-sample only, and every cell is the maximum of a small search.** Positive numbers here are where to look, not what is true — see `RESULTS.md` for the out-of-sample gate. Simulated markets, not Kalshi.

Mean cents per market offered:

| family | hold_favorite | buy_longshot | band_fade | late_favorite | snr_band | jump_follow | jump_fade | momentum | mean_revert | bracket_arb | pair_arb | maker_spread | random_contro |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `crypto_hourly` | -84 | +89 | -309 | +6 | -36 | -193 | -6349 | -1245 | -277 | n/a | +0 | +0 | -210 |
| `index_bracket_daily` | -203 | -88 | -184 | -39 | -69 | -3314 | -1252 | -2722 | -2099 | +0 | +0 | +0 | -817 |
| `crypto_bracket_hourly` | -35 | -153 | +107 | +75 | -6 | -1009 | -2119 | -1482 | -1137 | +0 | +0 | +0 | -1898 |
| `crypto_bracket_stale` | -31 | -254 | +28 | +804 | -14 | -766 | -2120 | -3466 | -812 | +24 | +0 | +0 | -678 |
| `econ_print` | +187 | -322 | +62 | +14 | +190 | -127 | -1188 | -2158 | -599 | n/a | +0 | +0 | -950 |
| `weather_temp` | +353 | -46 | +206 | +53 | +1 | -1411 | -1083 | -796 | -640 | n/a | +0 | -445 | -142 |
| `sports_game` | +161 | -157 | -14 | -51 | -23 | -233 | -440 | -427 | -255 | n/a | +0 | +0 | -196 |
| `politics_long` | -9 | -81 | +91 | +114 | -8 | -2011 | -1356 | -744 | -985 | n/a | +0 | -301 | -238 |
| `awards_thin` | -22 | -12 | -14 | -6 | -12 | -679 | -458 | -435 | -418 | n/a | +0 | -238 | -42 |
| `mentions_short` | +1 | -21 | -80 | +33 | +13 | -627 | -348 | -198 | -383 | n/a | +0 | -479 | -230 |
| `efficient_control` | +161 | -24 | +326 | +56 | +68 | -605 | -753 | -255 | -446 | n/a | +0 | +0 | -3 |

### Read the control row first

`efficient_control` is a market with **no edge in it by construction** — gamma exactly 1.0, no quote lag, penny spread. Nothing can beat it. Its best cell scores **+326c per market** (`band_fade`), which ranks **#3 of 135** cells in this whole matrix.

That is the entire argument for the rest of this directory. The largest in-sample number produced by a 108-cell search came from a market that cannot be beaten. Every cell above is the maximum of four draws, and maxima of noise are large and positive. In-sample ranking is a way to decide what to test next; it is not evidence.

Second symptom of the same thing: 1 of the 5 strategies **designed to lose** (buy_longshot) show a positive best cell somewhere in this table.

## Best strategy per family

| family | best strategy in-sample | mean/market | ann. return | targets |
|---|---|---|---|---|
| `crypto_hourly` | buy_longshot(enter_frac=0.25,max_price=20,qty=100) | +89.3c | +98991%/yr | EDGE 1 sign control — expected to LOSE |
| `index_bracket_daily` | bracket_arb(min_edge=2,qty=25) | +0.0c | +0%/yr | EDGE 3 (bracket incoherence) — riskless |
| `crypto_bracket_hourly` | band_fade(enter_frac=0.0,hi=8,lo=2,qty=100) | +107.2c | +6703%/yr | EDGE 1, narrowed by search — overfitting canary |
| `crypto_bracket_stale` | late_favorite(enter_frac=0.8,qty=250,thresh=75) | +803.8c | +71583%/yr | EDGE 1, capital-efficient variant |
| `econ_print` | snr_band(enter_frac=0.25,hi=98,lo=96,qty=100) | +190.5c | +3215%/yr | EDGE 1+5, narrowed to the best signal-to-noise window |
| `weather_temp` | hold_favorite(enter_frac=0.25,qty=250,thresh=65) | +352.5c | +1225%/yr | EDGE 1 (longshot compression) |
| `sports_game` | hold_favorite(enter_frac=0.0,qty=250,thresh=85) | +161.1c | +5568%/yr | EDGE 1 (longshot compression) |
| `politics_long` | late_favorite(enter_frac=0.8,qty=100,thresh=75) | +114.5c | +90%/yr | EDGE 1, capital-efficient variant |
| `awards_thin` | pair_arb(min_edge=1,qty=100) | +0.0c | +0%/yr | nothing — structurally impossible, reported as zero |
| `mentions_short` | late_favorite(enter_frac=0.8,qty=100,thresh=85) | +33.3c | +1091%/yr | EDGE 1, capital-efficient variant |
| `efficient_control` | band_fade(enter_frac=0.3,hi=40,lo=30,qty=250) | +325.7c | +45031%/yr | EDGE 1, narrowed by search — overfitting canary |

## Best family per strategy

| strategy | best family in-sample | mean/market |
|---|---|---|
| `hold_favorite` | weather_temp | +352.5c |
| `buy_longshot` | crypto_hourly | +89.3c |
| `band_fade` | efficient_control | +325.7c |
| `late_favorite` | crypto_bracket_stale | +803.8c |
| `snr_band` | econ_print | +190.5c |
| `jump_follow` | econ_print | -127.3c |
| `jump_fade` | mentions_short | -347.8c |
| `momentum` | mentions_short | -198.1c |
| `mean_revert` | sports_game | -255.2c |
| `bracket_arb` | crypto_bracket_stale | +23.6c |
| `pair_arb` | crypto_hourly | +0.0c |
| `maker_spread` | crypto_hourly | +0.0c |
| `random_control` | efficient_control | -3.0c |
