# Maintenance

| What | How often | Where from | Month |
| --- | --- | --- | --- |
| Waiting period and its exceptions | Annually, and on any NFIP program change | FEMA / floodsmart | Jan |
| Coverage exclusions and the backup endorsement | Annually | State insurance dept, III | Jan |
| Life-safety wording | Annually | NWS | Mar (flood safety week) |
| Mold guidance | Every 2 years | EPA | — |
| Sandbag sites and local programs | Twice a year, before the wet season | Phone call | Apr, Oct |
| State insurance dept phone numbers | On any failed call | The failed call | continuous |

## Staleness is enforced

- Every source carries `retrieved` and `method`; both render on the page.
- Every local resource needs `verifiedOn` and `verifiedBy` or the build fails.
- `local.configured: false` suppresses the whole local layer, so an abandoned deployment degrades
  to correct national guidance rather than to stale local claims.

## Commands

```sh
npm run dev     # validate data, serve
npm run build   # validate, typecheck, build
npm test        # 33 unit and data tests
npm run check   # build + tests + byte budget
npx playwright test   # 14 browser tests: axe, zoom, the date, the log, screenshots
```
