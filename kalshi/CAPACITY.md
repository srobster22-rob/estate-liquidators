# Kalshi Bot Factory — Capacity

What the winning bots are worth **in dollars per year**, which is a different question from what `RESULTS.md` reports and a more useful one.

> `markets_per_year` scales every dollar figure on this page linearly. For `econ_print` it is now **counted** — 534/yr, from 2,668 settled contracts over 5 years; see `CENSUS.md`. For every other family it is still an unverified estimate. Fill sizes come from the simulator's depth model. No competition is modelled — a thin structural edge is exactly the kind somebody else's bot is already resting on.

| bot | markets/yr | fill | edge/market | **annual P&L** | capital to commit | return on it | utilisation |
|---|---|---|---|---|---|---|---|
| `econ_print` / snr_band(enter_frac=0.25,hi=98,lo=96,qty=100) | 133.5 | 53 | +252.7c | **$337** | $69 | 488%/yr | 12% |

## What this changes

The best bot in `RESULTS.md` reports a headline return in the thousands of percent. Its actual output is **$337 a year** on **$69** of committed capital, because `econ_print` lists roughly 133.5 markets a year and the book holds about 53 contracts at the price where the edge lives.

The percentage is not wrong — it is a return on capital measured only over the 12% of the year that capital is deployed. Both numbers describe the same bot. Only one of them tells you whether to build it.

The two ways this gets better are both about the denominator, not the edge: find the same inefficiency in a family that lists more markets, or find it at a price where the book is deeper. Neither is a tuning problem.

