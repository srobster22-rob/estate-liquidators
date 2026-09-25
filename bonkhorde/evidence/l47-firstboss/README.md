# L47: the first boss, per character

L46 found THE TWIN dead before 10:00 in 11 of 24 first-tier runs for the
plausible player, against 4 for the bench bot, and THE INTERN - the starting
character - in 13 of 48 across the two. L43 had put most early deaths in the
ninety seconds after the first boss arrives at 5:00. The first guess was the
boss's size: a mid-run boss is sized to BOSS_SECS of `kitDps()`, a
single-target ceiling that counts THE SPLIT's copies on every shot, and THE
TWIN starts with THE SPLIT. Measured before anything was typed, and the guess
was wrong.

## The instrument

`bossfight.js` reproduces `balance.js`'s first-tier runs exactly - the same
setup calls in the same order, stepped the way `runOut` steps - on seeds
20260821-44, to 10:00 or death, and records THE MATRIARCH's fight: the health
it was sized to, `kitDps()` at its arrival, the player's health going in, the
time to kill it, what the player took during it and the trough; and for a
run that dies, when, and whether a boss was up. Five characters with the
plausible player (`__g.clumsy`), THE TWIN with the bench bot as well.
(Its death counts match L46's to the run: THE TWIN 11/24 and 4/24, THE
INTERN 8/24, THE OX 1/24, THE COURIER 2/24, THE SPARK 3/24.)

## What it read

```
                   dead <10:00   in the fight / after / before   time to kill (p25-p75)   the fight takes (of max hp)
TWIN, clumsy          11/24            5 / 6 / 0                   33 s (24-56)               71 of 91    74%
TWIN, bench bot        4/24            1 / 2 / 1                   21 s (11-23)               33 of 143   21%
COURIER, clumsy        2/24            1 / 1 / 0                   32 s (18-43)               78 of 147   48%
SPARK, clumsy          3/24            1 / 1 / 1                   26 s (16-39)               71 of 123   65%
INTERN, clumsy         8/24            8 / 0 / 0                   38 s (26-52)               70 of 133   64%
OX, clumsy             1/24            1 / 0 / 0                   37 s (31-63)               111 of 222  50%
```

THE MATRIARCH is at its 45,600 cap (12 x her table) in 22 of THE TWIN's
fights, 14 of THE COURIER's, 12 of THE INTERN's, 6-7 of THE SPARK's and THE
OX's.

## What it means

- **The sizing is doing its job.** Every character takes about as long to
  kill her - 26 to 38 s median for the plausible player - whatever its
  `kitDps()` read (1,500 to 6,600). THE TWIN's inflated estimate only pushes
  her to the cap, and at the cap THE TWIN kills her as fast as THE COURIER.
- **The fight costs the plausible player the same seventy-odd points of
  health whoever it plays** (70 to 78; THE OX, who stands in it longer,
  111), and what decides who dies is how much health there is to take it
  from: 91 for THE TWIN at 5:00 (74% of it gone, half its losses AFTER the
  fight, finished by the field at 5:30-9:00 from a quarter of its health),
  133 for THE INTERN, 222 for THE OX. The bench bot, which reads her
  telegraphs the frame they appear, takes 33.
- **THE INTERN's early deaths for the plausible player are all inside the
  first boss fight** - eight of eight, between 5:12 and 6:23. The first boss
  is the one thing in the first ten minutes a new player can lose to, and a
  third of plausible first runs do.
- Nothing was typed. THE TWIN is the glass cannon it says it is ("Half the
  health"), unlocked by clearing a run, which selects for a player nearer the
  bench bot than the clumsy one; whether a new player's first boss should
  take a third of their first runs is a design call for the owner, and it is
  recorded with these numbers in the README.

## Files

- `bossfight.js`, `bossfight.txt` (every run), `bossfight.json`,
  `summary.txt` (the table's numbers).
