# Maintenance

| What | How often | Why |
| --- | --- | --- |
| Feed adapters | On any ingest error, and quarterly | Feeds change field names and pagination without notice |
| The labelled pairs | Whenever the matcher changes | It is the regression suite; add a pair for every bug found |
| Precision measurement | Every matcher change | `npm run eval` fails the build below 95% |
| Review queue decisions | Weekly | Every `not_a_match` is a matcher bug report; read them |
| Unsubscribe rate | Monthly | A rising rate means over-alerting, which is the failure mode |

## The loop that keeps it accurate

1. Read the review queue. Each candidate a human rejects is a signal about the thresholds.
2. Add the pair to `data/labelled-pairs.json` with the label the human gave it.
3. Change the matcher.
4. `npm run eval` — precision must stay at or above 95%, and the new pair must pass.

Never tune a threshold without adding the pair first. The evaluation set is the only thing
standing between this and a matcher that quietly drifts toward sending more texts.

## Commands

```sh
npm run demo    # full pipeline on fixtures: ingest, re-ingest, match, queue, deliver
npm run eval    # matcher precision and recall against the labelled pairs
npm test        # 26 tests: idempotency, exactly-once, restart safety, STOP, normalizer
npm run check   # typecheck + tests + eval
```
