# L45: the plausible player's table

Every balance number in the README was the bench bot's - the ceiling player,
which kites perfectly and hops on the frame it lands. L43 found the first ten
minutes are free for that player and a fight for the clumsy one; L44 gave
`balance.js` the clumsy player as a switch. This is the table with both, on
one build (4c2809d), the same 36 paired worlds a side (9 characters x seeds
20260821-4), first tier and veteran, the damage ledger on.

## First tier (no permanent upgrades)

```
                  early (<10:00)   clears   median    level at end   hits   contact   spit   hazard
bench bot              4/36        17/36    ~20:30        69         872     5134    2121    2878
clumsy player          9/36        20/36    ~20:30        62        1042     6151    2920    5048
```

```
per character          bench bot                    clumsy player
                  early  clears  median          early  clears  median
intern             2/4    0/4    20:32            2/4    1/4    10:29
scrap              0/4    0/4    17:24            2/4    0/4    10:33
spark              0/4    2/4    20:52            0/4    3/4    20:51
ox                 0/4    4/4    20:52            0/4    4/4    20:44
ghoul              0/4    2/4    20:23            1/4    3/4    21:07
accnt              1/4    0/4    13:21            1/4    1/4    11:59
twin               1/4    3/4    20:47            2/4    2/4    21:49
surge              0/4    3/4    21:04            1/4    2/4    20:31
pyre               0/4    3/4    20:49            0/4    4/4    20:40
```

## Veteran (every permanent upgrade bought)

```
                  early (<10:00)   clears   level at end
bench bot              0/36        29/36        85
clumsy player          1/36        27/36        78
```

Per character, veteran clears: bench bot intern 3, scrap 2, spark 2, ox 4,
ghoul 4, accnt 3, twin 3, surge 4, pyre 4; clumsy 3, 2, 2, 4, 4, 2, 3, 4, 3.

## What it says

- **Early deaths are the plausible player's number, and it is one in four.**
  9/36 at first tier against the ceiling's 4/36; L43's 7/27 on the same
  build. At veteran neither player dies early (0 and 1 of 36).
- **Clears do not separate the players.** 17 against 20 at first tier, 29
  against 27 at veteran - inside the +/-10-point band the README already
  warns about at this n. The clumsy player reads telegraphs late and pays for
  it in hazard damage (5,048 against 2,878 over the tier) and levels (62
  against 69 at the end), but it clears the run about as often.
- **THE SCRAPPER is still the weakest** - 0/8 first-tier clears across both
  players, 2/4 and 2/4 at veteran - and THE ACCOUNTANT keeps it company at
  first tier (0/4 and 1/4). THE TEMP, half health and death as a resource,
  clears 3/4 and 4/4: L43's no-hop deaths were its design.
- **A number that moved.** L35's README table had the bench bot at 25/36
  first-tier clears (and 29/36 before the crowd) on these same paired seeds;
  this build reads 17/36. Veteran did not move (30/36 then, 29/36 now).
  Measured, not guessed: the L35 build itself (4fcc82c), run again on those
  seeds, prints its README table to the run (1/36, 25/36); the L36 merge
  (9af902a) prints 2/36 and 26/36; the L37 build (d569ec8) prints 4/36 and
  17/36 - row for row the table this build prints, which is also the proof
  that L39, L40 and L41 moved nothing. So the number changed at L37, and L37's
  own README says how: a damage number's jitter took three draws from the
  seeded run stream, and taking it off the stream re-rolled every pinned run
  once. "The same seeds" across L37 are two different sets of worlds. On a
  SECOND seed base (20260901), where both builds roll fresh worlds, this build
  reads 1/36 and 24/36 and the L35 build 3/36 and 22/36; with WHIPTAIL
  shipped off (another re-rolled draft) this build reads 1/36 and 26/36.
  Pooled over every table, the bench bot's first tier is 67/108 clears on
  this build against 47/72 on L35's (62% and 65%) and 6/108 against 4/72
  early (5.6% and 5.6%). The drop was the dice: the +/-10-point band the
  README warns about, read from its low end. Nothing in the build got harder,
  and nothing needed typing. (`old-builds.txt`, `followups.txt`.)

## Files

- `first-tier.txt`, `veteran.txt`: the two tables as `balance.js` printed
  them, both players.
- `old-builds.txt`: the bench bot's first tier on the L35 build (4fcc82c),
  the L36 merge (9af902a) and the L37 build (d569ec8), same seeds.
- `followups.txt`: this build with WHIPTAIL off, and this build and the L35
  build at a second seed base.
