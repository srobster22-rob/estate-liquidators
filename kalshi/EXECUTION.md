# Kalshi Bot Factory — Execution

Every bracket number in this project is quoted at some number of **ticks of slippage per leg**, and K22's conclusion rests on that axis. That models a *marketable* order — one that crosses and walks the book.

No sane implementation would send one. You would send a **limit order at the quoted ask**, immediate-or-cancel, and then you never pay worse than the price you computed the arb from. The risk moves somewhere else:

| order type | you always | you sometimes |
|---|---|---|
| marketable | fill | pay worse — **slippage** |
| IOC limit | pay your price | **miss** — partial fill |

For a one-leg strategy these are nearly interchangeable. For an N-leg arb they are not: a miss does not cost a tick, it leaves you holding *k* of *N* mutually exclusive brackets. K22 wrote that sentence and moved on without pricing it.

## Every mode on one basis

Four independent seeds, 3,000 sets each. `I = s²/e` is K23's frequency-invariant information cost — lower is better.

| execution | ¢/set | SE | σ | **I = s²/e** | losing sets | worst set |
|---|---|---|---|---|---|---|
| perfect fill (unachievable) | +21.00¢ | ±1.64 | 150¢ | **1,078** | 0/12,000 | +0¢ |
| marketable, +1 tick/leg | +10.91¢ | ±0.74 | 81¢ | **595** | 0/12,000 | +0¢ |
| marketable, +2 ticks/leg | +0.82¢ | ±0.49 | 37¢ | **1,632** | 150/12,000 | -564¢ |
| IOC limit, 95% per leg | +12.29¢ | ±1.81 | 359¢ | **10,466** | 26/12,000 | -16,125¢ |
| IOC limit, 80% per leg | +12.98¢ | ±3.73 | 505¢ | **19,662** | 70/12,000 | -16,125¢ |
| IOC limit, 60% per leg | +10.25¢ | ±3.32 | 562¢ | **30,851** | 124/12,000 | -17,324¢ |

## The result, and the one I nearly reported instead

The first version of this ran **one seed** and found income *rising* as fills got worse — +25.4¢/set at perfect fill against +28.3¢ at an 80% fill rate. That read as a discovery. It was noise: the strategy fires ~80 times in 3,000 sets, so the mean carries an SE of 1.5–3.3¢ and every row sat within about one of every other. Reporting the trend would have been exactly the error findings 5 and 8 exist to catch, one round after congratulating myself for catching it.

Measured across four seeds, **the expected value is flat in the fill rate** — every IOC row is within 2 SE of the best. The entire story is in the second moment.

- **σ rises 3.7×** across the IOC range while income holds at 49% of perfect fill.
- **Losing sets go from 0 to 124**, worst case -17,324¢ on a single set.
- **Information cost rises from 1,078 to 30,851** — an order of magnitude.

### Why the mean survives

A set only fires when it is underpriced by at least the filter, and a set that is collectively underpriced is on average made of individually underpriced legs. So a partial fill is a **positive-EV directional position**, not a loss. K22's phrase — *"you are holding a directional position you never chose"* — is right about the mechanism and wrong about the consequence. The money is fine. What you lose is *the reason you wanted the trade*.

## Which is what settles it

| | income | I = s²/e | riskless? |
|---|---|---|---|
| marketable, +1 tick | +10.91¢ | **595** | **yes** — 0/12,000 losing |
| IOC limit, 95% | +12.29¢ | 10,466 | no — 26/12,000 losing |

**Marketable execution has the lowest information cost of any mode measured, including perfect fill.** Slippage shrinks the mean and the spread by almost the same proportion, and `I` is linear in a proportional shrink — so you buy a better risk profile at a fair price. IOC keeps the money and throws the risk profile away.

So finding 17 modelled the right execution mode for the wrong reason, and the conclusion sharpens rather than reverses: **at a 95% per-leg fill rate this is no longer an arbitrage at all.** Its information cost is worse than `snr_band`, the plain directional strategy it was supposed to beat. A riskless trade you cannot execute risklessly is a directional trade with extra steps.

## K27 — how the misses are distributed, which is the part I got wrong

K26 closed by naming its own gap: *"real misses are correlated, and correlated misses are worse than independent ones at the same marginal rate."* The caveat was fair; the direction was a guess, and it is **backwards**.

Correlation across the legs of *one set* is not portfolio correlation. It means the set fills **entirely or not at all** — no partial brackets, so the riskless property survives. Same marginal fill rate in every row below; only the joint distribution moves.

| regime | ¢/set | SE | σ | **I = s²/e** | losing sets | worst set |
|---|---|---|---|---|---|---|
| perfect fill (unachievable) | +21.00¢ | ±1.64 | 150¢ | **1,078** | 0/12,000 | +0¢ |
| IOC 80%, independent misses | +12.98¢ | ±3.73 | 505¢ | **19,662** | 70/12,000 | -16,125¢ |
| IOC 80%, half correlated | +13.01¢ | ±4.56 | 351¢ | **9,460** | 44/12,000 | -15,478¢ |
| IOC 80%, fully correlated | +19.94¢ | ±1.00 | 149¢ | **1,119** | 0/12,000 | +0¢ |
| IOC 80%, ADVERSE | -1.01¢ | ±4.73 | 531¢ | **—** | 116/12,000 | -16,114¢ |

**At full correlation IOC is indistinguishable from perfect fill** — same σ, same zero losing sets, same information cost. And there is a second reason correlation helps that shows up in the realised fill rate:

| regime | legs filled, vs perfect fill |
|---|---|
| independent | 78.8% |
| adverse | 78.8% |
| fully correlated | 86.1% |

Full correlation lands *above* its nominal rate. That is not a leak — **an all-or-nothing miss is retryable.** Nothing was committed, so the batch re-fires against the next quote. A partial fill cannot be retried: the legs that did fill have already tripped the position guard.

### The hazard is a third mechanism, and it changes the sign

**Adverse selection.** The quote carrying the mispricing is the one whose maker pulls it first, so you systematically collect the fairly-priced legs and miss the cheap one. That does not add variance to an edge — it removes the edge. Ten seeds × 3,000 sets:

| per-leg fill | independent | adverse | delta | t |
|---|---|---|---|---|
| 95% | +14.27 ±1.97¢ | +13.31 ±2.64¢ | -0.96¢ | **-0.3** |
| 90% | +16.03 ±1.92¢ | +4.81 ±2.55¢ | -11.22¢ | **-3.5** |
| 80% | +13.02 ±2.53¢ | -4.80 ±2.54¢ | -17.82¢ | **-5.0** |

**Sharply non-linear, and that is the operationally useful part.** At a 95% per-leg fill rate adverse selection is undetectable (t = -0.3). By 80% it takes the strategy **negative**. The transition sits between 95% and 90%, which turns the whole question into one number an operator can measure from their own fill logs — the same move `COHERENCE.md` makes for the staleness rate.

## What this does not settle

- Adverse selection is modelled as **perfectly informed**: misses land on the most underpriced legs, always. Reality sits somewhere between that and random, and nothing here locates it.
- The gate's **stress** criterion still applies 2 ticks *and* 1.5× fees. Two ticks is a marketable-order assumption an IOC limit does not face, so the right stress for this strategy is a fill-rate stress — but inventing one now, after seeing which way it falls, is how a gate gets quietly loosened. It is left alone.
- `crypto_bracket_stale` remains a simulated family whose staleness rate was invented. `COHERENCE.md` is the branch that would settle it from real books.

