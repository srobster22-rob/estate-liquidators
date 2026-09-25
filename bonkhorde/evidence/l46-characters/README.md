# L46: every character at n=24, both players

L45's per-character rows were four runs a cell, and the README's standing
note says the per-character ordering "does not survive re-sampling". This is
the first tier (no permanent upgrades) at 24 paired worlds a character
(seeds 20260821-44), 216 runs a player, on 71a42d3, the damage ledger on:
the bench bot, then the clumsy player (`BONKHORDE_CLUMSY=1`).

## The table

```
                 bench bot                         clumsy player                 both
character        early   clears  median   lvl      early   clears  median   lvl     clears   early
THE OX           0/24    20/24   20:45    84       1/24    15/24   20:44    77      35/48    1/48
THE COURIER      0/24    18/24   20:33    77       2/24    17/24   20:33    75      35/48    2/48
THE GHOUL        0/24    19/24   20:54    83       2/24    14/24   20:41    67      33/48    2/48
THE SPARK        2/24    14/24   20:33    66       3/24    12/24   20:15    64      26/48    5/48
THE TEMP         4/24    10/24   20:30    65       3/24    13/24   20:31    66      23/48    7/48
THE TWIN         4/24    12/24   20:36    65      11/24     8/24   10:32    53      20/48   15/48
THE SCRAPPER     2/24    10/24   19:05    66       6/24     9/24   15:26    61      19/48    8/48
THE INTERN       5/24     8/24   20:00    61       8/24    10/24   17:20    55      18/48   13/48
THE ACCOUNTANT   2/24    11/24   20:26    87       7/24     5/24   12:47    62      16/48    9/48
all             19/216  122/216                   43/216  103/216
```

(At n=24 one run is four points; a cell's 95% interval is about +/-20 points
near the middle, so 8/24 against 20/24 is a real difference and 10/24
against 12/24 is not.)

## What it says

- **The spread is real now, and it is the same for both players.** THE OX,
  THE COURIER and THE GHOUL clear 69-73% of their runs across the two
  players; THE ACCOUNTANT, THE INTERN, THE SCRAPPER and THE TWIN clear
  33-42%. The two players make entirely different runs on the same worlds,
  and they agree on the top three and the bottom four - the ordering the
  README says does not survive re-sampling survives a change of player.
- **THE SCRAPPER is not the weakest character.** It is in the bottom four
  and never alone there: THE INTERN is lowest for the bench bot (8/24), THE
  ACCOUNTANT for the plausible player (5/24).
- **THE TWIN falls apart in the first ten minutes for a plausible player:**
  11 of 24 runs dead before 10:00, a median of 10:32, where the bench bot
  loses 4. It is the largest gap between the two players of any character,
  and THE TWIN is the character a player unlocks by clearing a run.
- **THE INTERN - the character every new player starts with - dies before
  10:00 in 13 of 48 runs across the two players**, second only to THE TWIN.
- **The clear rates are not the ones the README's balance section once
  aimed at** ("a first run never clears", veteran at 50%): the first tier
  clears 56% for the bench bot and 48% for the plausible player, veteran
  (L45) 80% and 75%. That paragraph predates the finale sized by the kit
  (R237-R247: sixty seconds of your own kill rate at 15:00, scaled by the
  kit's growth since, never under 520,000), which made surviving to 20:00
  the power check and the fight at the end the same length for every kit.
  The tier gap now shows in who reaches 20:00, not in the fight; nothing
  was tuned toward the old aim.

## Files

- `bench-bot-n24.txt`, `clumsy-n24.txt`: `balance.js 24 first` as printed,
  the ledger columns on.
