# Maintenance

What rots, how fast, and which month to deal with it. A disposal guide that is quietly wrong is
worse than none, because people stop calling to check.

## The refresh calendar

| What | How often | Where it comes from | Month |
| --- | --- | --- | --- |
| **Location hours** | Every 6 months, and always before summer and the holidays | Phone call | Apr, Oct |
| **Location acceptance lists** | Annually | Phone call | Oct |
| **Phone numbers** | Whenever a call fails | The failed call | continuous |
| **HHW collection event dates** | Each season | County solid waste calendar | Feb, May, Aug, Nov |
| **Federal guidance sources** | Annually, and whenever a link 404s | `SOURCES.md` URLs | Jan |
| **Hauler accepted-materials list** | Annually — this changes with their processing contract | Hauler | Jan |
| **Item list additions** | Continuous | Zero-result log (see below) | continuous |

## The loop that keeps it useful

1. Read the zero-result log. Every search that found nothing is a synonym somebody needed.
   In the browser console: `JSON.parse(localStorage['dg.zeroresults'])`
2. Add the alias, or add the item.
3. `npm run data` — the build refuses aliases that collide with another item, which is how you
   find out that the word means two things.

## Staleness is enforced, not remembered

- Every source carries `retrieved` and `method`; both render on the answer page.
- Every real location must carry `verifiedOn` and `verifiedBy` or the build fails.
- A location with no hours record renders "call first" and can never show as open.
- `jurisdiction.configured: false` suppresses every local verdict, so an abandoned deployment
  degrades to "here's why it's dangerous, call your county" rather than to stale bin advice.

## Commands

```sh
npm run dev      # validate data, serve locally
npm run build    # validate, typecheck, build, inject the service worker precache list
npm test         # 45 acceptance/unit tests
npm run check    # everything above plus the byte budget and the browser/axe suite
npx playwright test   # axe, keyboard, 200% zoom, offline, screenshots
```

## If you stop maintaining this

Set `configured: false` and push. The app keeps giving correct universal hazard guidance —
which does not go stale — and stops giving local answers that have. That is the safe failure
mode and it is worth using deliberately rather than letting the site rot.
