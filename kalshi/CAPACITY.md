# Kalshi Bot Factory — Capacity

What the winning bots are worth **in dollars per year**, which is a different question from what `RESULTS.md` reports and a more useful one.

> `markets_per_year` in `config.json` is an **estimate** from general knowledge of what Kalshi lists. It was not scraped and not verified, and it scales every dollar figure on this page linearly. Fill sizes come from the simulator's depth model. No competition is modelled — a thin structural edge is exactly the kind somebody else's bot is already resting on.

| bot | markets/yr | fill | edge/market | **annual P&L** | capital to commit | return on it | utilisation |
|---|---|---|---|---|---|---|---|
| `econ_print` / band_fade(enter_frac=0.3,hi=8,lo=2,qty=100) | 250 | 57 | +65.8c | **$164** | $54 | 307%/yr | 9% |
| `econ_print` / band_fade(enter_frac=0.3,hi=8,lo=2,qty=250) | 250 | 60 | +64.0c | **$160** | $57 | 282%/yr | 9% |

## What this changes

The best bot in `RESULTS.md` reports a headline return in the thousands of percent. Its actual output is **$164 a year** on **$54** of committed capital, because `econ_print` lists roughly 250 markets a year and the book holds about 57 contracts at the price where the edge lives.

The percentage is not wrong — it is a return on capital measured only over the 9% of the year that capital is deployed. Both numbers describe the same bot. Only one of them tells you whether to build it.

The two ways this gets better are both about the denominator, not the edge: find the same inefficiency in a family that lists more markets, or find it at a price where the book is deeper. Neither is a tuning problem.

