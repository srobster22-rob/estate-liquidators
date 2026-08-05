# 11 — Neighborhood Air Quality Sensor Network

**What it is:** Eight cheap PM2.5 sensors on eight porches downwind of the highway, feeding a
dashboard that says what the air is doing on *this* block — with the calibration work that
makes the numbers defensible instead of alarming.

**Fill in before pasting:** `[NEIGHBORHOOD]`, `[CITY]`, `[COUNTY]`, `[STATE]`, `[TIMEZONE]`,
`[LANGUAGES]`, `[SOURCE]` (the thing you suspect — highway, rail yard, refinery, warehouse
district, wildfire smoke), `[ORG]` (community group, or "no partner yet").

**Read first:** PurpleAir sensors already exist and have a public map; if a few already sit in
[NEIGHBORHOOD], the honest first move may be to buy two more and use their network. Build this
when you need data you control, at locations you choose, with a calibration record you can
defend — which is the case whenever the data might end up in front of a regulator.

---

```text
You are building a community air quality monitoring network for [NEIGHBORHOOD] in [CITY],
[STATE], focused on [SOURCE]. Build it now; do not ask me clarifying questions. Where you need
a decision I did not make, choose the option that makes the data more defensible, state your
choice, and keep going.

Read the MEASUREMENT HONESTY DOCTRINE before writing code or ordering parts. It determines
whether this project produces evidence or produces noise.

=== THE PEOPLE ===

Ana lives four blocks from [SOURCE] in [NEIGHBORHOOD]. Two kids, one with asthma. On some days
the air smells and she keeps them inside, and on other days she doesn't and isn't sure whether
she should have. The nearest regulatory monitor is eleven miles away, in a different part of
the city, and its readings do not describe her block.

The second person is her neighbor Charles, who wants to know whether it is safe to run in the
morning and would look at a number on his phone before deciding.

The third is a public health official or a regulator who might eventually see this data — and
who will discard the entire dataset the moment they find an uncalibrated sensor, an unlogged
firmware change, or an AQI computed with the wrong breakpoints. Build for that reader from the
first commit, because it costs nothing then and is impossible to retrofit.

=== THE PROBLEM, WITH A NUMBER ===

Regulatory monitoring networks are sparse by design — they measure regional compliance, not
neighborhood exposure. Pollution near a highway or a rail yard varies sharply over hundreds of
meters, which is exactly the scale a regional network cannot resolve. Look up the actual number
of regulatory PM2.5 monitors in [COUNTY] and cite the source; it is usually a startlingly small
number and it is the whole argument for this project.

=== MEASUREMENT HONESTY DOCTRINE ===

Low-cost optical particle sensors are useful and they are not reference instruments. Four rules:

1. RAW AND CORRECTED, ALWAYS BOTH. Store the raw sensor output forever, unmodified. Corrections
   are computed on top and stored separately with the name and version of the correction
   applied. Never overwrite raw data. When a better correction is published, you reprocess;
   if you overwrote, you can't.
2. HUMIDITY IS THE BIG ERROR AND IT IS SYSTEMATIC. Optical sensors read high in humid
   conditions because water uptake makes particles look bigger. EPA researchers have published
   a US-wide correction for PurpleAir PA-II sensors (the Barkjohn et al. work) using the
   sensor's PM2.5 and relative humidity; look up the current published form of that equation,
   cite it, and implement it exactly as published. Do not derive your own. If your hardware is
   not a PurpleAir, say so and state which correction you applied and why it is appropriate —
   or state honestly that no validated correction exists for your sensor.
3. CO-LOCATE BEFORE YOU DEPLOY. Every sensor runs beside the others for at least a week before
   going in the field, and ideally beside a regulatory monitor if one is reachable. Record the
   inter-sensor agreement. A sensor that disagrees with its siblings by more than a defined
   tolerance does not get deployed. Publish those numbers.
4. NEVER CLAIM REGULATORY EQUIVALENCE. The dashboard says, in plain words, what this data is
   and is not: useful for patterns, trends, and relative comparisons between locations and
   times; not a regulatory measurement and not a legal determination of compliance. Say it on
   every page, not in a footer.

=== BUILD THIS ===

PART A — HARDWARE (one node)

- MCU: ESP32 (any common dev board with WiFi).
- PM sensor: a Plantower PMS5003 or a Sensirion SEN5x. Pick one, document why, and note that
  the correction you apply must match the sensor you chose.
- Temperature/humidity/pressure: BME280 or the equivalent integrated into an SEN5x. Humidity
  is not optional — it is required input to the correction.
- Enclosure: weatherproof, with a rain-shielded intake and passive airflow, and NOT in direct
  sun (solar heating changes the internal RH and corrupts the correction). Document the
  enclosure design, mounting height, and distance from walls, and photograph each installation.
- Power: USB. Assume mains, not solar, for v1.
- Cost target: under $120 per node. State the real bill of materials with part numbers.

Firmware requirements:
- Sample on a fixed interval (60s), average to 2-minute records, timestamp with NTP.
- Report raw PM1.0/PM2.5/PM10 in both the sensor's CF=1 and atmospheric variants if it
  provides both, plus temperature, humidity, pressure, uptime, WiFi RSSI, and a firmware
  version string in every payload. The version string is what makes a later anomaly
  explainable.
- Buffer to flash when the network is down and backfill on reconnect, with original
  timestamps preserved and a flag marking backfilled records.
- OTA update capability, and every firmware change logged in a deployment record with a date.
- Publish over MQTT or HTTPS POST to your collector. Do not depend on a vendor cloud.
- Consider ESPHome to avoid writing firmware from scratch; if you do, pin the version and
  commit the YAML.

PART B — COLLECTOR + STORAGE

- An HTTP/MQTT endpoint that accepts readings, validates them, and stores them.
- Schema keeps raw and derived strictly separate (see DATA MODEL).
- Reject impossible values (negative PM, RH > 100, timestamps in the future) into a quarantine
  table rather than discarding them — a sensor going bad is itself a finding.
- Flag but never delete: a sensor reading 4x its neighbors is flagged for review, not dropped.
  Suppressing outliers is how you miss the event you built the network for.

PART C — DASHBOARD

1. NOW (/) — For Ana and Charles. Top of the page, in large type: the current condition in
   words ("Good" / "Moderate" / "Unhealthy for sensitive groups" / …), the corrected PM2.5
   value with its units, and one sentence of what to do. Then a simple map of nodes with their
   current values, then a 24-hour chart.
   Compute AQI using the current EPA breakpoints — verify them from the primary source, since
   the PM2.5 breakpoints were revised following the 2024 NAAQS update, and an app using stale
   breakpoints reports the wrong category. Cite the version and effective date on the page.
   Never show only a number. "18 µg/m³" means nothing to Ana; the category and the sentence do.

2. PATTERNS — Time-of-day and day-of-week averages per node, and node-versus-node comparison.
   This is where [SOURCE] shows up: if the rail yard is the cause, the 4am peak on weekdays is
   the evidence. Include wind direction if you can get it from the nearest NWS station, and
   build a simple pollution rose. This view is the project's real output.

3. COMPARE — Your nodes against the nearest regulatory monitor, pulled from EPA's AirNow API
   (free, requires a key — verify current terms) or the state agency's feed. Plot both. Being
   able to show "we track the official monitor closely on regional smoke days and diverge
   sharply on weekday mornings" is the single most persuasive chart this project can produce.

4. NODE DETAIL — Per sensor: location, install date, photo, mounting description, firmware
   version history, co-location test results, current health (last seen, uptime, data
   completeness percentage over the last 30 days), and a link to download its complete raw
   history as CSV.

5. DATA — Public download of everything: raw and corrected, CSV and JSON, with a data
   dictionary, the correction equations used with citations, the calibration records, and an
   explicit open license. Reproducibility is the point. A researcher or an agency should be
   able to redo your analysis from scratch.

6. ALERTS — Optional email or SMS when a rolling 1-hour average crosses a threshold. Cap at
   one alert per 6 hours. Include the plain-language action.

=== DATA MODEL ===

nodes: id, label, lat, lng, install_date, removal_date, height_m, mounting_description,
  enclosure_type, sensor_model, mcu, photo_ref, owner_contact, active
readings_raw: node_id, ts, pm1_0_cf1, pm2_5_cf1, pm10_cf1, pm2_5_atm, temp_c, humidity_pct,
  pressure_hpa, firmware_version, rssi, backfilled bool
  PRIMARY KEY (node_id, ts) — idempotent ingest, no duplicates on backfill retry
readings_corrected: node_id, ts, pm2_5_corrected, correction_name, correction_version,
  computed_at
quarantine: node_id, ts, payload jsonb, reason, received_at
colocation_tests: id, node_ids[], started_at, ended_at, reference_source, results jsonb,
  passed bool, notes
firmware_deployments: id, node_id, version, deployed_at, notes
flags: id, node_id, ts_start, ts_end, kind, description, created_by

=== STACK ===

- Collector + API: Node/TypeScript or Python, whichever you'll maintain. PostgreSQL with
  TimescaleDB if convenient; plain Postgres with a good index is fine at this scale — eight
  nodes at 2-minute resolution is under 2M rows a year.
- Dashboard: server-rendered, light. Charts with a small library (uPlot or Observable Plot),
  not a heavy framework. NOW must render in under 1.5s on Slow 4G — measure it.
- Map: MapLibre with OSM tiles, lazy-loaded, not on the critical path.
- Firmware: ESPHome (pinned) or Arduino/PlatformIO. Commit the config or source.
- Everything self-hosted on one small VPS. No vendor cloud dependency for the data path — the
  point is that this dataset belongs to [NEIGHBORHOOD].
- Nightly database backup, off-box, tested by actually restoring it once.

=== HARD CONSTRAINTS ===

- Raw data is immutable and never deleted. Corrections are additive.
- Every displayed value states whether it is raw or corrected and which correction was used.
- Every threshold and breakpoint cites its source and effective date, stored as data.
- Data completeness per node shown honestly on the dashboard. A node offline for three days
  shows a gap in the chart, never an interpolated line.
- NOW page under 1.5s on Slow 4G, readable at 200% zoom, WCAG 2.2 AA, and never using color
  alone to convey the category.
- Reading level 6th grade for all public-facing copy. Technical detail lives on its own page.
- [LANGUAGES] on NOW and the alert messages.
- Node locations are approximate on the public map (nearest intersection, not the exact
  address), because a node is on somebody's porch and the map should not publish where they
  live. Store exact coordinates privately for analysis.
- Full data export always available, always free, openly licensed.

=== DO NOT BUILD ===

- No health advice beyond the standard AQI category guidance, quoted with a citation. Do not
  generate personalized recommendations, and never tell anyone whether their symptoms are
  related to air quality.
- No claims about [SOURCE] causing anything. Publish measurements and patterns. Causation
  requires source apportionment work you are not doing, and an unsupported accusation
  discredits the data that could have supported it later.
- No AQI forecasting or prediction in v1.
- No proprietary vendor cloud in the data path.
- No smoothing, interpolation, or gap-filling in stored data. Charts may visually indicate
  gaps; the database never invents a reading.
- No sensor calibration by adjusting numbers until they look right. Corrections come from
  published, cited equations or from a documented co-location regression whose method and data
  you publish.
- No login to view anything. All public.
- No LLM anywhere in the data path.

=== ACCEPTANCE TESTS ===

1. A node powered off for 6 hours backfills on reconnect with original timestamps, marked as
   backfilled, and creates zero duplicate rows.
2. Re-sending an identical payload is idempotent (primary key enforced).
3. A payload with RH = 130 lands in quarantine with a reason and is not in readings_raw.
4. The correction function reproduces published example values from its source paper — test
   against at least three worked examples and cite them.
5. AQI category boundaries match the current EPA breakpoints exactly; test each boundary value
   on both sides.
6. Reprocessing corrections for a date range does not modify readings_raw — assert by hash of
   the raw table before and after.
7. A node offline for 3 days renders a visible gap, never an interpolated segment.
8. The public map shows approximate locations only; exact coordinates never appear in any
   public response — test the API output directly.
9. CSV export of one node's full history round-trips: re-importing reproduces identical values.
10. Every chart and value on NOW labels raw vs corrected and names the correction version.
11. NOW renders under 1.5s on Slow 4G throttling — report the measured number.
12. axe-core clean; category conveyed by text as well as color.
13. Co-location results are displayed on each node's page, and a node without a passed
    co-location test is visibly marked as uncalibrated on the public map.

=== MILESTONES ===

M0 — One node on your own desk, reporting to a local collector.
  EXIT: 24 hours of continuous readings, raw stored, no gaps, firmware version in every row.

M1 — Correction implemented and verified against published examples; AQI with verified
  breakpoints.
  EXIT: tests 4 and 5 pass, and you can show the citation for both.

M2 — Co-location of all nodes for 7+ days.
  EXIT: published inter-sensor agreement numbers. Any node outside tolerance is repaired or
  retired before deployment. Do not skip this. It is the week that makes the dataset worth
  anything.

M3 — Deployment of all nodes + the NOW dashboard.
  EXIT: Ana looks at it and correctly tells you whether today is a stay-inside day.

M4 — Patterns + comparison to the regulatory monitor + open data export.
  EXIT: one chart that shows something the regional monitor cannot show, with the calibration
  record to back it up. Take it to [ORG] or a public meeting.

=== SAFETY + LEGAL ===

- Never claim regulatory equivalence, and never call a reading a violation of any standard.
  Air quality standards are defined over specific averaging periods with specific reference
  methods; your data does not meet those definitions and saying otherwise hands anyone who
  disagrees with you an easy dismissal of everything you've measured.
- Health guidance is quoted from EPA/CDC AQI category language with citation, never authored
  by you and never personalized.
- Host consent: every node sits on someone's property. Get written permission, be explicit
  that data will be public, agree on removal terms, and honor a removal request immediately.
  Publish approximate locations only.
- If this data is used in advocacy — and it should be — pair it with the calibration record
  and the methodology page every time. Data presented without them gets dismissed, and the
  dismissal sticks to the next group too.
- Be careful about naming a specific facility as a source. Measurements plus wind direction
  plus time-of-day patterns are legitimate findings; "Company X is poisoning us" is a legal
  claim. Present the evidence and let it speak, and involve [ORG] before making public
  accusations.
- Do not display any health statistic you have not sourced with a year.

=== HOW TO REPORT BACK ===

Tell me: the exact correction equation you implemented and its citation; the AQI breakpoint
version and effective date; the co-location agreement numbers per node; the real bill of
materials; the measured NOW load time; and everything you could not verify. If no validated
correction exists for the sensor you chose, lead with that.
```

---

## Why it's shaped this way

**Co-location for a week before deployment is the milestone people skip, and it is the one that
decides whether the data survives contact with a skeptic.** Eight sensors reading the same air
in the same place for seven days tells you which one is broken, what your real inter-sensor
variance is, and what tolerance to hold future nodes to. Without it, every difference between
locations is ambiguous — it could be the air or it could be the sensor, and you can never say
which.

**Raw immutable, corrections additive** matters because correction science moves. The EPA's
US-wide PurpleAir correction was published after thousands of sensors were already deployed;
groups that stored only corrected values couldn't reprocess. Keep the raw and you can always
apply the next equation.

**Humidity correction is not optional.** Optical sensors read high in humid air because water
makes particles look bigger. Uncorrected data reliably over-reports on exactly the muggy summer
mornings people are most worried about, which produces alarming charts that a regulator will
correctly dismiss — and that dismissal costs the community its credibility.

**"Publish measurements, not accusations."** The pattern chart — a weekday 4am peak that the
regional monitor eleven miles away cannot see — is far more persuasive than any claim you could
write on top of it, and it doesn't hand anyone a reason to attack the messenger.

**Before you build:** check PurpleAir's map for existing sensors in [NEIGHBORHOOD], and find
out whether [STATE]'s environmental agency has a community air monitoring program. Several
states now lend equipment and provide co-location access at their regulatory sites — which is
the calibration gold standard, for free.
