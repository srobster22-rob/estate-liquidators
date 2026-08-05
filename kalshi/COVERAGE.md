# Kalshi Bot Factory — Coverage Matrix

Every market family against every strategy: 9 x 12 = 108 cells, best of 4 parameter draws each, 300 markets per cell.

**In-sample only, and every cell is the maximum of a small search.** Positive numbers here are where to look, not what is true — see `RESULTS.md` for the out-of-sample gate. Simulated markets, not Kalshi.

Mean cents per market offered:

| family | hold_favorite | buy_longshot | band_fade | late_favorite | jump_follow | jump_fade | momentum | mean_revert | bracket_arb | pair_arb | maker_spread | random_contro |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `crypto_hourly` | -84 | +89 | -309 | +6 | -737 | -2930 | -440 | -162 | n/a | +0 | +0 | -210 |
| `index_bracket_daily` | -237 | -82 | -81 | -124 | -1575 | -2276 | -1948 | -1606 | +2 | +0 | +0 | -817 |
| `econ_print` | +185 | -284 | -135 | +83 | -23 | -494 | -876 | -844 | n/a | +0 | +0 | -950 |
| `weather_temp` | +82 | -50 | +178 | +201 | -380 | -756 | -398 | -249 | n/a | +0 | -378 | -142 |
| `sports_game` | -59 | -41 | -18 | -31 | -1322 | -594 | -322 | -371 | n/a | +0 | +0 | -196 |
| `politics_long` | +39 | -90 | +61 | +114 | -2387 | -510 | -2315 | -1118 | n/a | +0 | -505 | -238 |
| `awards_thin` | -20 | -12 | -24 | -6 | -1228 | -796 | -583 | -341 | n/a | +0 | -227 | -42 |
| `mentions_short` | +26 | -23 | +1 | +22 | -320 | -762 | -234 | -185 | n/a | +0 | -376 | -230 |
| `efficient_control` | +422 | -70 | +175 | +173 | -900 | -1600 | -224 | -397 | n/a | +0 | +0 | -3 |

### Read the control row first

`efficient_control` is a market with **no edge in it by construction** — gamma exactly 1.0, no quote lag, penny spread. Nothing can beat it. Its best cell scores **+422c per market** (`hold_favorite`), which ranks **#1 of 100** cells in this whole matrix — the highest score in the table.

That is the entire argument for the rest of this directory. The largest in-sample number produced by a 108-cell search came from a market that cannot be beaten. Every cell above is the maximum of four draws, and maxima of noise are large and positive. In-sample ranking is a way to decide what to test next; it is not evidence.

Second symptom of the same thing: 1 of the 5 strategies **designed to lose** (buy_longshot) show a positive best cell somewhere in this table.

Top cell overall: `efficient_control / hold_favorite(enter_frac=0.25,qty=250,thresh=65)` at +422c. It is a control strategy on a control market, and it is the best-looking bot in the sweep.

## Best strategy per family

| family | best strategy in-sample | mean/market | ann. return | targets |
|---|---|---|---|---|
| `crypto_hourly` | buy_longshot(enter_frac=0.25,max_price=20,qty=100) | +89.3c | +98991%/yr | EDGE 1 sign control — expected to LOSE |
| `index_bracket_daily` | bracket_arb(min_edge=0,qty=100) | +1.7c | +5706%/yr | EDGE 3 (bracket incoherence) — riskless |
| `econ_print` | hold_favorite(enter_frac=0.0,qty=100,thresh=95) | +184.7c | +2610%/yr | EDGE 1 (longshot compression) |
| `weather_temp` | late_favorite(enter_frac=0.8,qty=100,thresh=75) | +200.8c | +4981%/yr | EDGE 1, capital-efficient variant |
| `sports_game` | pair_arb(min_edge=0,qty=100) | +0.0c | +0%/yr | nothing — structurally impossible, reported as zero |
| `politics_long` | late_favorite(enter_frac=0.8,qty=100,thresh=75) | +114.5c | +90%/yr | EDGE 1, capital-efficient variant |
| `awards_thin` | pair_arb(min_edge=1,qty=100) | +0.0c | +0%/yr | nothing — structurally impossible, reported as zero |
| `mentions_short` | hold_favorite(enter_frac=0.5,qty=25,thresh=85) | +25.9c | +290%/yr | EDGE 1 (longshot compression) |
| `efficient_control` | hold_favorite(enter_frac=0.25,qty=250,thresh=65) | +421.9c | +29773%/yr | EDGE 1 (longshot compression) |

## Best family per strategy

| strategy | best family in-sample | mean/market |
|---|---|---|
| `hold_favorite` | efficient_control | +421.9c |
| `buy_longshot` | crypto_hourly | +89.3c |
| `band_fade` | weather_temp | +178.2c |
| `late_favorite` | weather_temp | +200.8c |
| `jump_follow` | econ_print | -23.3c |
| `jump_fade` | econ_print | -494.2c |
| `momentum` | efficient_control | -224.0c |
| `mean_revert` | crypto_hourly | -161.5c |
| `bracket_arb` | index_bracket_daily | +1.7c |
| `pair_arb` | crypto_hourly | +0.0c |
| `maker_spread` | crypto_hourly | +0.0c |
| `random_control` | efficient_control | -3.0c |
