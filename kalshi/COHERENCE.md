# Kalshi Bot Factory — Bracket Coherence

The only quantity in this project that can be measured **without waiting for anything to settle**.

| | needs | to establish the sign |
|---|---|---|
| a directional edge | **settled outcomes** | ~580 events ≈ **0.6 years** |
| bracket incoherence | **a snapshot of the book** | see below |

`E[100·outcome − ask]` cannot be evaluated until the market settles. *"Do these five asks sum below 100"* is answered by looking. That is a difference in kind, and it is the real reason the bracket corner matters — more than K24's dollar figure, which is downstream of a guess.

## What it would cost to settle `stale_leg_prob`

K24's whole result is proportional to `stale_leg_prob = 0.35`, a number with no evidence behind it. Independent **events** needed to pin the rate, and the recording time that implies:

| precision | events | hourly brackets | daily index brackets |
|---|---|---|---|
| ±10 pp | 88 | 3.7 days | 88 days |
| ±5 pp | 350 | 14.6 days | 350 days |
| ±2 pp | 2,185 | 91.0 days | 2185 days |

**Counted in events, not snapshots.** A frozen leg stays frozen across consecutive polls, so polling faster buys resolution on *when* a set is stale and almost nothing on *how often* sets are. At one poll a minute the snapshot count overstates the evidence by about **60×** — the same correlated-samples error K2 caught in the calibration check.

## Better: the parameter never needs settling at all

Backing out `stale_leg_prob` from a recording would need a model — the measured incoherence rate is biased *down* by two things at once (a freeze is transient, so sparse polling misses it; and half the dislocations it causes point the unprofitable way). Measured against a known truth of 35%, the instrument reads 8% at 4 polls/event, 15% at 12, and 25% at 60.

But **income does not need the parameter.** Every term is visible in a snapshot at the moment you would trade:

```
income = sets/yr × P(tradeable set) × E[margin − N·slippage − fees | tradeable]
```
The payout is 100¢ with certainty once all N legs fill, so nothing waits on an outcome. The one thing a snapshot *cannot* pin down is the **entry rule** — whether you fire at the first qualifying poll or at the peak — so `income_from_snapshots` reports both, and the truth must lie between them. Checked against the backtester on four independent seeds:

| seed | `first` (lower) | backtester | `best` (upper) |
|---|---|---|---|
| 41M | +4.00¢ | **+8.99¢** | +9.90¢ |
| 43M | +4.75¢ | **+9.64¢** | +18.41¢ |
| 45M | +3.63¢ | **+8.23¢** | +9.63¢ |
| 47M | +2.14¢ | **+6.00¢** | +13.73¢ |

It brackets every time. So a recording alone — **no simulator, no settled outcomes, no `stale_leg_prob`** — establishes the sign and the order of magnitude, and leaves a 2–6× span on the magnitude itself. That is the same split finding 16 found for directional edges: *the sign is cheap and the size is not*, arrived at from the opposite direction.

## The trap this instrument exists to avoid

Sum four legs of a five-leg event and you get a number below 100, because you left out a leg worth ~20¢. **A partial set does not lose data, it manufactures an arbitrage** — and it does so in nearly every snapshot, so an incomplete recording reads as the best discovery in the file. Measured on a synthetic recording of a family whose real margin never reaches 1¢, dropping one leg turns a median margin of −5¢ into **+9¢** — a set that is never buyable reads as 9¢ free.

So `quality()` refuses to report anything until every set is verifiably complete, and `live.py --record-event` enumerates an event's legs from the API so partial sets are hard to create in the first place.

## No real recording yet

Nothing here has been run against Kalshi. `CENSUS.md` counted the market list from published research; this is the other half — the book itself — and it stays unmeasured until someone runs `--record-event` for a couple of weeks.

