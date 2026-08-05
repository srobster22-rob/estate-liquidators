# Your locale — fill this in once

Edit the values inside the block below, then run `./build-pack.sh` from this directory. It
regenerates all 24 files in `ready/` with your values substituted in, and tells you which
placeholders are still empty in each one.

You do not have to fill everything. Anything you leave blank stays as `[BRACKETED]` in the
output, and the agent is instructed to state an assumption and keep going rather than stall.
**The first six are worth two minutes** — they appear in nearly every brief.

Values must not contain the `|` character. Everything else is fine, including commas and
apostrophes.

```
# ---- The six that matter most ----
CITY=
COUNTY=
STATE=
STATE_ABBR=
TIMEZONE=
LANGUAGES=

# ---- Project-specific. Fill the ones for projects you're actually starting. ----

# 06, 07, 08, 09, 11, 12, 22 — the organization you're building with or for.
# Write "no partner yet" if there isn't one; every brief handles that case.
ORG=

# 07 — the page where your city posts council agendas. Find it before you start this one.
AGENDA_URL=

# 09, 11, 12 — the neighborhood name.
NEIGHBORHOOD=

# 10 — the specific few blocks you'll survey. Not the whole city.
AREA=

# 11 — the pollution source you suspect: highway, rail yard, refinery, warehouses, wildfire smoke.
SOURCE=

# 15 — the water system serving your address, by name. It's on your bill.
UTILITY=

# 16 — who collects your trash and recycling. Also on a bill.
HAULER=

# 20 — your electric, gas, and water providers, comma-separated.
UTILITIES=

# 21 — your school district.
DISTRICT=

# 18 — what that directory covers: food pantries, cooling centers, legal aid, whatever you need.
DOMAIN=
```

---

## Where to find the harder ones

- **TIMEZONE** — use the IANA name, like `America/Chicago` or `America/Los_Angeles`. The briefs
  ask for correct DST handling and an IANA identifier is what makes that testable.
- **LANGUAGES** — don't guess. Pull the Census ACS table on language spoken at home for your
  county (data.census.gov, table S1601). The answer is reliably not what you'd assume, and the
  languages that surprise you are the ones with no existing local materials. Write it as a plain
  list: `English, Spanish, Haitian Creole`.
- **UTILITY / UTILITIES / HAULER** — look at an actual bill. The name on the bill is the name
  the agent needs to search for tariffs, inventories, and accepted-materials lists.
- **AGENDA_URL** — search your city's site for "agendas" or "meeting portal." Note which platform
  it is if you can tell (Legistar, Granicus, CivicPlus, PrimeGov, BoardDocs) — the brief asks the
  agent to figure this out, but telling it saves an hour.
