# Kalshi Bot Factory — Capacity

What the winning bots are worth **in dollars per year**, which is a different question from what `RESULTS.md` reports and a more useful one.

> `markets_per_year` scales every dollar figure on this page linearly. For `econ_print` it is now **counted** — 534/yr, from 2,668 settled contracts over 5 years; see `CENSUS.md`. For every other family it is still an unverified estimate. Fill sizes come from the simulator's depth model. No competition is modelled — a thin structural edge is exactly the kind somebody else's bot is already resting on.

| bot | markets/yr | fill | edge/market | **annual P&L** | capital to commit | return on it | utilisation |
|---|---|---|---|---|---|---|---|
| `econ_print` / hold_favorite(enter_frac=0.25,qty=250,thresh=95) | 534 | 55 | +53.3c | **$285** | $79 | 360%/yr | 13% |
| `econ_print` / hold_favorite(enter_frac=0.0,qty=100,thresh=95) | 534 | 54 | +44.7c | **$239** | $79 | 303%/yr | 13% |

## What this changes

The best bot in `RESULTS.md` reports a headline return in the thousands of percent. Its actual output is **$285 a year** on **$79** of committed capital, because `econ_print` lists roughly 534 markets a year and the book holds about 55 contracts at the price where the edge lives.

The percentage is not wrong — it is a return on capital measured only over the 13% of the year that capital is deployed. Both numbers describe the same bot. Only one of them tells you whether to build it.

The two ways this gets better are both about the denominator, not the edge: find the same inefficiency in a family that lists more markets, or find it at a price where the book is deeper. Neither is a tuning problem.

