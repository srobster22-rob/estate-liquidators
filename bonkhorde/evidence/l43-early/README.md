# L43: the first ten minutes, with a worse player

The README's top not-done item said the early game cannot be lost and that no
constant fixes it - six sweeps moved early deaths by one run in forty-two -
and concluded that whatever fixes it is a mechanic that makes running cost
something. Every one of those sweeps was run with the bench bot, which kites
perfectly and hops on the frame it lands. Measured again, on the L41 build,
with two worse players.

## The instrument

`early.js`: every character, three paired seeds (20260821-3), first tier (no
permanent upgrades), no god, three players - the BENCH bot; the CLUMSY bot
(`__g.clumsy(true)`: it re-decides its heading every 0.35 s and holds it
between, makes the landing window 65% of the time and otherwise stands half a
second, and does not see a telegraph until 0.55 s before it lands); and the
clumsy bot with the hop OFF. Minute by minute to 10:00 or death: hp at each
minute, the hp trough and when, the damage ledger by source per minute, level
and kills (`early.txt` has every run, `early.json` the numbers).

## What it read

```
                      dead before 10:00   mean hp trough (worst)   damage a minute, 0-5 / 5-10 (contact, spit, hazard)
bench bot                  2 / 27           58%  (-6%)                6, 7, 1  /  30, 10,  4
clumsy bot                 7 / 27           30%  (-17%)               7, 8, 1  /  32, 11, 17
clumsy, no hop             8 / 27           27%  (-21%)               6, 10, 2 /  12, 13, 30
```

Where the deaths are: 5:16, 5:20, 5:27, 5:32, 5:52, 5:52, 6:07, 6:07, 6:15,
6:18, 6:58 - eleven of the seventeen in the ninety seconds after the first
boss arrives at 5:00 on top of the phase that adds spitters and brutes;
minute six deals 100 to 260 damage in most runs to a player with 100 to 200
hp. Three are the bench bot's own late deaths (9:40 intern; 4:51 twin) and
9:24 spark without the hop. The other three are `THE TEMP` (`pyre`) without
the hop, which dies in every run it is given: 1:58, 3:51, 5:52 - the one
per-character result in the table.

The players who are not the ceiling take three to seven times the bench
bot's hazard damage from 5:00 on (17 and 30 a minute against 4) - the late
telegraph read is where the clumsiness costs - and lose seven levels by
10:00 (31-33 against 38).

## What it means

- The early game can be lost, by a plausible player rather than the ceiling
  one. One run in four for the clumsy bot, one in three without the hop; the
  bench bot's one in fourteen is the number the six sweeps were reading.
- Movement dominates the first ten minutes for the CEILING player. For the
  plausible one the 5:00 boss window is a real fight, and it is the boss and
  the field together, not a stat.
- Nothing was typed. The README's item is rewritten to say what was measured;
  the mechanic it asked for is not owed until a bench with the clumsy player
  says the first ten minutes are free, and this one says they are not.

## For later

- The clumsy bot should be the bench's second column for early deaths (the
  ceiling bot for clears, the clumsy bot for the first ten minutes); balance.js
  takes a `BONKHORDE_CLUMSY=1` the way it takes `BONKHORDE_NOHOP`.
- `THE TEMP` without the hop: three deaths in three runs before 6:00, the only
  character for which the hop is the difference between a run and none. Whether
  that is the character's design (it flies) or a hole is a per-character
  question.

## Files

- `early.js`, `early.txt`, `early.json`.
