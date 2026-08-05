# Kalshi Bot Factory — Sensitivity

The confidence interval on the headline describes **sampling** error. It says nothing about whether the simulator's inputs are right, and those were chosen by hand. This sweeps each one and reports where the answer crosses the **$250/yr** bar.

Bot: `econ_print` / `hold_favorite(enter_frac=0.25,qty=250,thresh=95)`, measured on fresh seeds never used for selection. One input moves at a time, everything else held fixed, paired seeds throughout.

## Depth at 95–99¢ — MODELLED

Income is exactly linear in depth: the bot is depth-limited at every size it wants. `markets._depth_taper` floors the book at 8% of base, which is a modelling choice, not a measurement — and it sits at precisely the price where the whole edge lives.

| depth × my model | ¢/event | annual $ | vs bar |
|---|---|---|---|
| 2 | +607.5¢ | $811 | clears |
| 1.5 | +480.4¢ | $641 | clears |
| 1 | +307.3¢ | $410 | clears |
| 0.75 | +240.3¢ | $321 | clears |
| 0.5 | +151.8¢ | $203 | **below** |
| 0.25 | +75.0¢ | $100 | **below** |
| 0.1 | +27.2¢ | $36 | **below** |

**Crosses the bar at 0.60.**

## Planted edge magnitude — ASSUMED

The levered one. Costs are fixed, so net = gross − constant, and halving the assumed inefficiency removes far more than half the profit.

| edge × markets.py | ¢/event | annual $ | vs bar |
|---|---|---|---|
| 1.5 | +581.0¢ | $776 | clears |
| 1.25 | +437.8¢ | $584 | clears |
| 1 | +307.3¢ | $410 | clears |
| 0.75 | +204.2¢ | $273 | clears |
| 0.5 | +77.4¢ | $103 | **below** |
| 0.25 | +29.2¢ | $39 | **below** |

**Crosses the bar at 0.72.**

## Spread — MODELLED

Steps rather than glides, because the spread is quantised to whole cents and the bot's entry threshold sits on a tick boundary.

| extra ticks | ¢/event | annual $ | vs bar |
|---|---|---|---|
| 0 | +307.3¢ | $410 | clears |
| 1 | +271.2¢ | $362 | clears |
| 2 | +162.8¢ | $217 | **below** |
| 3 | +99.1¢ | $132 | **below** |

**Crosses the bar at 1.77.**

## Markets per year — COUNTED

Linear by construction. This is the input the census settled at 534 contracts ≈ 134 ladder events; it is here for completeness.

| contracts/yr | ¢/event | annual $ | vs bar |
|---|---|---|---|
| 1068 | +307.3¢ | $820 | clears |
| 800 | +307.3¢ | $615 | clears |
| 534 | +307.3¢ | $410 | clears |
| 400 | +307.3¢ | $307 | clears |
| 250 | +307.3¢ | $192 | **below** |
| 150 | +307.3¢ | $115 | **below** |

**Crosses the bar at 325.41.**

## Fee rate — VERIFIED

The published schedule is confirmed (see `selftest.py` §1b), so this column is not an open question — it is here to show what a schedule change would do.

| fee × published | ¢/event | annual $ | vs bar |
|---|---|---|---|
| 0.5 | +327.6¢ | $437 | clears |
| 1 | +307.3¢ | $410 | clears |
| 1.5 | +287.0¢ | $383 | clears |
| 2 | +266.6¢ | $356 | clears |
| 3 | +226.0¢ | $302 | clears |

## Maker fill rate — a GUESS that turned out not to matter

`maker_benign_fill_rate` was flagged from the start as a pure guess that would become load-bearing the moment market-making worked. Swept across its whole plausible range, it never works — and it gets **worse** as fills get easier, which is adverse selection with the sign showing: the fills you are certain to get are the ones you did not want.

| fill rate | `politics_long` | `awards_thin` | `weather_temp` | `mentions_short` |
|---|---|---|---|---|
| 0.15 | -792¢ | -348¢ | -1,086¢ | -475¢ |
| 0.35 | -833¢ | -339¢ | -1,086¢ | -494¢ |
| 0.60 | -885¢ | -360¢ | -1,071¢ | -520¢ |
| 0.85 | -958¢ | -353¢ | -1,063¢ | -539¢ |
| 1.00 | -970¢ | -367¢ | -1,055¢ | -541¢ |

Best of 12 configs per cell — a maximum, so an upper bound. **An assumption whose sign is invariant across its entire range is not one the result depends on.** This one is retired rather than caveated.

## What has to be true

Stated so each can be checked separately, against a real book:

- the book holds at least **0.60×** the depth this simulator assumes at 95–99¢ — roughly **33 contracts** at the touch
- the real mispricing is at least **72%** of what `markets.py` plants
- Kalshi lists at least **325 econ contracts a year** (census counted 534)

Each is a one-input statement. Real model error arrives in combination, and two inputs each 30% out in the same direction are not covered by any single column above.

