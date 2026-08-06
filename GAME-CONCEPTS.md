# Forty-Five Game Concepts

`GAMES-PROJECT-PROMPT.md`, run once, plus two passes over it. 45 live concepts in nine
families, a ranked top eight, and a graveyard of twenty-six.

**Pass two — the action amendment.** The first pass produced 40 concepts with no twitch, no aim
and no combat depth anywhere in them, and the self-audit at the bottom called that a bias of
the generator rather than a position worth defending. **Family 9 — Fast** is the correction:
six action concepts, and a note on why action resists this format. Two entered the top eight on
merit and displaced two entries, written up in that section rather than quietly swapped.

**Pass three — verification, and it cost one of them.** #43 Recoil was checked against the
store and is dead: *Kickback: Shoot to Move!* shipped in July 2025 with the same bet. #46
Direct was checked and survives, with the bet narrowed. That's 5 of 6 in Family 9 still
standing, the top eight reshuffled again, and **one concrete lesson about the order these
passes should run in** — the search is five minutes and the prototype is two days, so the
search goes first, above the ranking. It didn't, and the ranking was wrong for a day as a
result.

**What this is for.** Finding the one thing to prototype on Saturday. Not a list to feel good
about. Every card carries a written-down result that would make you drop it and a test small
enough that you'd actually run it.

**What is verified and what isn't.** Nothing here is verified. Every "nearest shipped game"
is memory, and that memory has a cutoff — some of these shipped last year and I don't know it.
**Before building anything — before *ranking* anything — search the store for the comparables.**
Five minutes each, and it is the highest-value hour in this document. Two of the five I flagged
as probably-occupied have now been checked:

- **`#43` Recoil is dead.** *Kickback: Shoot to Move!* (Steam, July 2025) ships the concept
  and the bet. Moved to the graveyard; the number is left vacant so cross-references resolve.
- **`#46` Direct survives**, with the bet narrowed and one piece of adverse evidence found.
  Details on the card.

**Still unchecked, and still suspect: `#9` (vs *Viscera Cleanup Detail*), `#33` (vs *Blackbar*
and *Orwell*), `#38` (vs *Potion Craft*).** Everything else in here remains unverified memory.
One card in six survived contact with a search engine at full strength; assume that rate
applies to the rest.

**Calibration.** Estate Liquidators — *aggro follows the most valuable object leaving the
house, so you can get rid of the monster by handing the vase to your friend* — is roughly the
bar these were written against. Concepts that couldn't state their bet that sharply were cut;
nineteen of them are in the graveyard with the reason.

---

## How to read a card

| Field | What it's doing |
|---|---|
| **The bet** | The one mechanical claim the whole thing rests on. Exactly one. If it's wrong, there is no game. |
| **Nearest** | The closest shipped thing, named. An empty Nearest is a warning, not an opportunity. |
| **Kills it** | Not a risk — a *result*. Something you could watch happen and know it was over. |
| **Test** | The smallest thing that would trip the kill condition. Most are a day; several are an evening with no code. |
| **Scope** | Team and months to shippable, not to demo. |

Tags: `SOLO` shippable by one person · `NO COMBAT` no combat, no health bar anywhere ·
`UNMARKETABLE` mechanically true, commercially unwise, included deliberately ·
`POPULATION` needs a live player base to function — the heaviest structural dependency here.

Quota check: 9 families — 5 each, Family 9 down to 5 after #43 was killed by verification ·
1 co-op horror and 1 solo horror against a cap of 3 · 20 solo-shippable · 28 with no combat ·
5 with combat as the point · 7 marked unmarketable · 8 needing a population.

Family 9 now sits at the action quota's floor rather than above it. One more loss there and
the prompt's "at least six are fast" is breached, which would mean generating a replacement
rather than quietly dropping the quota.

---

## Family 1 — Testimony

**Verb: listen. Feeling: doubt.** You never see the world. You only ever get accounts of it,
and the accounts disagree.

### 1 · Party Line `NO COMBAT`
**Emergency dispatch, 1984. Four players, four consoles, and none of you hear the same calls.**

Calls arrive on your line only. One shared radio channel to the units, and a finite number of
units. Ninety seconds: take a call, work out whether it's the same incident someone else is
already on, commit a unit or hold.

- **The bet:** conflicting testimony from panicked callers is a better puzzle than a map. The
  game never renders the world — there is no top-down view to fall back on, ever.
- **Nearest:** *911 Operator* (has a map, and the map does the work) · *Unheard* (recorded,
  single-player) · *Keep Talking and Nobody Explodes* (asymmetry, but a manual is not
  testimony — a manual doesn't lie).
- **Kills it:** players start reading transcripts aloud verbatim to each other. If verbatim
  relay is optimal, the asymmetry is decoration and you've built a group reading exercise.
- **Test:** four people, a voice call, four docs of pre-written conflicting transcripts, one
  shared sheet. **No code at all.** Watch whether they paraphrase or read. One evening.
- **Scope:** 2 people, 6–9 months. Voice acting is the cost centre, not the engineering.

### 2 · Sworn
**One player saw the crime. Three are trying to reconstruct it. The one who saw it is lying.**

The suspect watches a 90-second silent film — they *know* what happened. Three detectives
interrogate. The suspect wins if a false but consistent story survives.

- **The bet:** consistency can be graded automatically. Every claim goes into a structured log
  — time, place, person, object — and the engine flags contradictions with no human referee.
  That's what turns lying to your friends into a game with rules instead of a vibe.
- **Nearest:** *Return of the Obra Dinn* (deduction against a real solution, single-player) ·
  *Deception: Murder in Hong Kong* (tabletop, closest) · *Among Us* (lying with no structure
  under it).
- **Kills it:** the median player freezes in the suspect seat. If only extroverts can carry
  the role, it's dead air three rotations out of four and the group stops picking it.
- **Test:** paper. Print the claim log as a form, one friend lies, three interrogate, you
  referee with a pen. One evening.
- **Scope:** 3–4 people, 9–12 months. The claim ontology is the hard part and it's a design
  problem, not an engineering one.

### 3 · The Quiet Part `HORROR`
**The monster hears words, not volume. Some words are forbidden this run. Talk around them.**

On-device speech recognition, a forbidden-word list that rerolls per run, and four people who
have to coordinate a heist without saying the nouns.

- **The bet:** local speech-to-text is now fast and accurate enough to be a mechanic rather
  than a gimmick. **Unverified, and it's an engineering claim — check it on day one.**
- **Nearest:** *Phasmophobia* (voice recognition, but for summoning — the inverse) · *In
  Verbis Virtus*.
- **Kills it:** the crew converges on pointing and grunting inside one session. If silence is
  dominant, the optimal way to play the game is not to play it.
- **Test:** no game. Four people, a voice call, a word list, a Python script watching a mic
  with a local model, and a buzzer. One day.
- **Scope:** small team, 9 months. **Counts as 1 of the 3 permitted horror slots.**
- **The problem nobody mentions:** the accessibility floor is brutal — accents, non-native
  speakers, mute players. It needs a non-voice parallel path designed in from day one, not
  bolted on, or the game excludes people structurally.

### 4 · Nightshift `SOLO` `NO COMBAT` `UNMARKETABLE`
**Call-in radio, 3am, one real hour a session.**

The board shows callers waiting. You choose who to take, when to cut in, when to go to music,
and how long to let dead air run.

- **The bet:** **silence is the mechanic.** The game scores the shape of the hour, not the
  content of it. Waiting is a move.
- **Nearest:** *Oxenfree* (interrupt-based dialogue — closest mechanically) · *Killer
  Frequency* (same setting, but puzzle-driven and comedic).
- **Kills it:** playtesters read "wait" as "nothing is happening" and mash next-caller. If the
  interface can't make waiting feel like an action, there's no game underneath.
- **Test:** audio only. Five recorded callers, a timeline, one button. A weekend. The only
  question: does anyone ever *choose* to wait?
- **Scope:** solo, 5–6 months. Writing and VO dominate.

### 5 · Cartographer's Error `NO COMBAT` `POPULATION`
**You survey a wilderness and submit a map. The next player gets your map, not the terrain.**

Asynchronous, and not co-op — *inherited*. Your errors become someone else's world, and theirs
become the next person's.

- **The bet:** a chain where one player's mistakes are another player's ground truth produces
  a kind of care that neither competition nor cooperation does.
- **Nearest:** *Death Stranding*'s async structures (helpful, never misleading) · *Elden Ring*
  messages (lies, but as a joke rather than a system).
- **Kills it:** two failures that look opposite and are the same. Everyone maps honestly, and
  it's a slow single-player game. Or trolling saturates in a week and every map is garbage.
  Either way there's no gradient between them, and the gradient is the game.
- **Test:** not a build. Fifty people, a shared folder, one hand-drawn map of a real park, and
  a rule. Look at what round three produces.
- **Scope:** 2–3 people, 8 months, plus a live population — the riskiest dependency here.

---

## Family 2 — Two Hands, One Object

**Verb: carry. Feeling: strained hilarity.** Physics taken seriously, which is what makes it
funny. Nothing snaps.

### 6 · Removals
**Two players, one house, one wardrobe, and a staircase with a turn in it.**

Full-physics two-man carry. No snapping, no teleporting, real floor plans. The clock is the
client standing in the driveway watching.

- **The bet:** the anchor/follower two-man carry is a whole game on its own and doesn't need a
  monster on top of it. *(Estate Liquidators has this as a feature — `TECH-SPEC.md` §B4. This
  is the same mechanic promoted to the entire product. Stating the overlap rather than
  pretending it isn't there.)*
- **Nearest:** *Moving Out* (arcade, forgiving, top-down — the gap is simulation depth) ·
  *Hardspace: Shipbreaker* (physical labour taken seriously) · *Gang Beasts* (the ragdoll
  comedy).
- **Kills it:** two-man carry at real latency turns out to be either trivial or infuriating
  with no band in between. Estate Liquidators' Phase 1 exists to find that band; if it doesn't
  exist, this concept dies with it.
- **Test:** **already funded.** `TECH-SPEC.md` §B4 / Phase 1 is running this experiment for
  another reason. Marginal cost of evaluating this concept: zero.
- **Scope:** 2–3 people, 8–12 months. Content is levels and levels are floor plans.

### 7 · Tow `SOLO`
**Orbital salvage. One tool: a winch cable. Nothing has thrusters except you.**

- **The bet:** a cable is a better verb than a gun. Everything interesting comes from the fact
  that pulling something also moves *you*.
- **Nearest:** *Hardspace: Shipbreaker* — closest by a distance, but its tether is one tool
  among many and the physics forgives you · *Kerbal Space Program*.
- **Kills it:** the cable is unreadable. If a player can't predict what a pull will do before
  committing to it, it reads as random and the skill ceiling never appears.
- **Test:** **2D.** A point mass, a rope constraint, a mouse, one weekend. If the 2D version
  isn't satisfying, 3D will not rescue it — 3D never rescues anything.
- **Scope:** solo, 6–8 months in 2D. Small team for 3D.

### 8 · Scaffold
**Co-op construction with no grid, and a wind test at the end of the shift.**

- **The bet:** real structural simulation turns building into a conversation — you physically
  can't hold two things at once, so you have to agree, and the sim settles who was right.
- **Nearest:** *Besiege* (structural sim, single-player, comedic) · *Poly Bridge* (sim as
  judge, no co-op) · *Satisfactory* (co-op, but everything snaps).
- **Kills it:** the verdict feels arbitrary. If a collapse can't be traced by eye to a
  decision somebody made out loud, it's a slot machine with hammers.
- **Test:** single-player 2D truss builder with a load test, two days. Show the failure in
  slow motion and ask the tester to explain it. If they can't, the sim isn't legible and no
  amount of co-op fixes that.
- **Scope:** 3 people, 10 months.

### 9 · Deep Clean
**Crime-scene remediation, two-person crew, and a UV pass at the end that scores what you
missed.**

- **The bet:** thoroughness is measurable, and being graded on what you couldn't see is a
  feeling no other game gives you. The residue simulation is the game; the UV reveal is the
  payoff.
- **Nearest:** *Viscera Cleanup Detail*. **This exists and it is close.** The offered
  difference is that VCD scores loosely and comedically while this scores precisely and
  doesn't joke. That may simply not be enough of a difference.
- **Kills it:** play it beside VCD for an hour. If the precision doesn't change *how* you
  clean, there is no second game here.
- **Test:** one room, one fluid, one UV lamp, three days — then play them back to back.
- **Scope:** 2 people, 6–8 months.
- **Honest:** this is the card I'd cut first. It's in the document because the prompt asks for
  the nearest shipped game to be named honestly, and naming it is what demotes this concept.

### 10 · Weight `SOLO` `NO COMBAT` `UNMARKETABLE`
**A full glass of water, a house, and your phone as the spirit level.**

Local multiplayer, everyone holding their own device, standing up, in the same room.

- **The bet:** the accelerometer as the entire control scheme. The comedy happens between the
  players' bodies, not on the screen.
- **Nearest:** the Wii Sports era (the ancestor) · *Bishi Bashi* · *Jackbox* (phone as
  controller, socially normalised).
- **Kills it:** it's a party trick with a ninety-second lifespan. If nobody asks for a second
  round, that's the whole answer.
- **Test:** a web page. `DeviceOrientation`, a tilt meter, a timer. One afternoon, and it runs
  on anyone's phone with a link.
- **Scope:** solo, 3–4 months. Marked unmarketable because motion control is out of fashion —
  which is also precisely why the space is empty.

---

## Family 3 — The Long Wait

**Verb: return. Feeling: consequence.** Real time, elision, persistence. Nothing here has a
health bar.

### 11 · Thirty Years of Tuesdays `SOLO` `NO COMBAT`
**You only ever play Tuesdays. There are 1,560 of them.**

- **The bet:** forced elision makes consequence legible. You never watch the drift happen —
  you see what it did, once a week, for thirty years.
- **Nearest:** *King of Dragon Pass* / *Six Ages* (seasonal elision — closest structurally) ·
  *The Sims* (continuous, which is the difference) · *Chinese Parents*.
- **Kills it:** players decide the story is in the gaps and resent the cuts. The device is
  either a window or a wall and there's no third outcome.
- **Test:** text only. Forty generated Tuesdays, no art, ninety minutes of play. Then ask the
  tester to narrate what happened *in between*. If they can, it works.
- **Scope:** solo, 6–9 months, mostly writing systems.

### 12 · The Inheritance `NO COMBAT` `UNMARKETABLE` `POPULATION`
**When you die, your save goes to a stranger — the house, the debts, the unfinished projects,
and one letter you wrote without knowing who'd read it.**

- **The bet:** inheritance between strangers produces care that a personal save can't. You
  tidy up for someone you'll never meet.
- **Nearest:** *Death Stranding* (async gifts) · *Rogue Legacy* (legacy, but within one
  player's run) · *NieR: Automata* ending E (the gesture, made once, not as a loop).
- **Kills it:** every letter is a prank. If players optimise the handover into a joke, the
  sincerity the entire design rests on never shows up.
- **Test:** no game. Thirty volunteers, a spreadsheet, a text field. Read the letters. That is
  the entire experiment and it costs an afternoon.
- **Scope:** 2–3 people, 9 months — plus moderation, permanently. Moderation is a staffing
  line here, not a footnote.

### 13 · Slow Mail `SOLO` `NO COMBAT` `POPULATION`
**You write a letter and it arrives tomorrow. Actually tomorrow.**

- **The bet:** real-world delay as a mechanic rather than a monetisation timer. Correspondence
  chess, where the correspondence is the game.
- **Nearest:** *Kind Words* (async letters between strangers — closest, but no delay) ·
  *Animal Crossing* (real clock, instant communication) · correspondence chess itself.
- **Kills it:** retention. If a player has forgotten by Thursday there is no game, and no
  notification strategy has ever fixed a thing people don't miss.
- **Test:** an email list, thirty people, two weeks. Measure reply rate at day 3, 7, 14. Costs
  nothing and produces the only number that matters.
- **Scope:** solo, 4 months.

### 14 · Erosion `SOLO` `NO COMBAT`
**Shape a landscape. The simulation runs at geological pace while you're gone. Come back in a
week and see what the water did.**

- **The bet:** a simulation that outlives the session. You're a slow force among slower ones.
- **Nearest:** *From Dust* (real-time erosion at session scale) · *Terra Nil* · *Mountain*
  (the game that waits — the tonal ancestor).
- **Kills it:** a week of simulation looks like a day of simulation. If you can't *see* a
  week, the wait is a lie and the player will feel lied to.
- **Test:** run the erosion model offline at 10,000× and screenshot 1 day, 1 week, 1 month.
  Put them side by side. Half a day, and it's pass/fail before you've designed anything.
- **Scope:** solo to 2 people, 6 months.

### 15 · Ten Year Lease `NO COMBAT`
**You run a shop on a real street for ten years. Sessions are quarterly. The neighbourhood
changes around you and you can't stop it.**

- **The bet:** the antagonist is a simulated neighbourhood with its own trajectory — rents,
  demographics, a chain opening across the road. You can't win it, only decide what to be
  when it turns.
- **Nearest:** *Papers, Please* (systemic pressure on one person — the ancestor) · *Recettear*
  (shopkeeping with no macro sim) · *Cities: Skylines* (you play the macro; here you're under
  it).
- **Kills it:** the neighbourhood is unreadable and its changes land as weather. If a player
  can't say "the rent went up because the tram opened," it's noise with a calendar.
- **Test:** build only the neighbourhood sim, no shop. Run forty years, print the timeline,
  hand it to someone and see if they can narrate it. Two days.
- **Scope:** solo to 2 people, 8 months.

---

## Family 4 — Judgment Calls

**Verb: appraise. Feeling: craft-pride, and the dread of being wrong.** No combat in this
family either.

### 16 · Provenance `SOLO` `NO COMBAT`
**You authenticate antiques. The forgeries are generated, not authored.**

- **The bet:** a generative model of *how objects get made* — period, workshop, materials,
  wear pattern — so that a forgery has real internal inconsistencies. The tells become
  learnable but never memorisable, because there is no finite list of them.
- **Nearest:** *Strange Horticulture* (identification, hand-authored) · *Papers, Please*
  (rule-checking, authored) · *Contraband Police*. **The generative half is the whole gap.**
- **Kills it:** generated flaws come out either trivially visible or invisible, with nothing in
  between. That's the standard failure of procedural puzzles and it shows itself inside the
  first fifty generated items.
- **Test:** skip 3D entirely. Generate 50 objects as **text dossiers** with a seeded flaw and
  give them to a friend. Measure accuracy at item 5 against item 50. If it doesn't climb,
  there's nothing to learn and therefore no game. One day.
- **Scope:** solo, 6–8 months. The strongest solo candidate in the document.

### 17 · Differential `NO COMBAT`
**Rural vet. No money. A dog that might have three things wrong with it.**

- **The bet:** the *cost* of a test is the game. Every diagnostic narrows the space and empties
  someone's wallet, and you're allowed to be right in a way that ruins them.
- **Nearest:** *Papers, Please* (the moral cost of correctness) · *Beholder* (closest in feel)
  · a thin field of medical games, none of which price the tests.
- **Kills it:** players find the dominant test order in one evening and it never varies again.
  A collapsed decision tree makes "judgment" a wiki lookup.
- **Test:** the disease model on paper. Thirty generated cases, the test list, the prices.
  Watch whether the tester is still second-guessing at case 20.
- **Scope:** solo to 2 people, 6 months.

### 18 · Luthier `NO COMBAT` `UNMARKETABLE`
**Build instruments. A physical-modelling synth plays them. The sound is the score.**

- **The bet:** audio DSP as the win condition. Change the bracing, hear the change, and the
  game never shows you a number.
- **Nearest:** nothing close, **and I'm suspicious of that.** Adjacent: *Kerbal* (parts →
  simulated outcome) · *VCV Rack* and modular synth software (a toy, not a game) · *Airships*.
  Unverified, and the empty space is exactly the flag the prompt warns about — spend the first
  hour looking for the grave.
- **Kills it:** untrained ears can't hear the difference between a good instrument and a
  slightly better one. If the discrimination threshold sits above the design space, the
  feedback loop never closes and no amount of UI will close it.
- **Test:** synthesise ten instruments varying one parameter and ask non-musicians to rank
  them. Random rankings, stop. Two days including the DSP.
- **Scope:** 2 people, 8 months, **one of whom must actually know DSP.** That constraint is
  the real scope estimate; the months are the easy part.

### 19 · The Restorer `NO COMBAT`
**Painting conservation. Every intervention is irreversible, and you can always do more.**

- **The bet:** **regret as the core feeling.** No undo, ever. The finished piece is a record of
  your restraint or the lack of it, and you submit it knowing exactly what you did.
- **Nearest:** *PowerWash Simulator* (surface revelation with zero stakes — the exact
  inversion, and instructive) · *Papers, Please*. Restoration is an enormous video genre with
  no good game in it, which is a real signal rather than an absence.
- **Kills it:** irreversibility routes players into save-scumming. If the tension moves from
  the brush to the file system, the design has been beaten by the operating system and you
  can't patch that.
- **Test:** one painting, one solvent, no undo, a hard commit. Five people. Watch how many
  reach for alt-F4.
- **Scope:** solo to 2 people, 5–7 months.

### 20 · Ledger `SOLO` `NO COMBAT`
**Forensic accounting. Find the fraud in a generated company's books.**

- **The bet:** procedurally generated fraud **with a cover-up** — the generator commits the
  crime and then hides it using a real repertoire of techniques, so the trail is genuine
  rather than decorated.
- **Nearest:** *Return of the Obra Dinn* (deduction against a real solution — the bar) · *The
  Case of the Golden Idol* · *Duskers*. All hand-authored. The generation is the bet.
- **Kills it:** the fraud is either mechanical — find the row that doesn't add up — or
  unfindable. **This is the same failure mode as Provenance (#16).** If you're building one of
  them, build Provenance first and let its result decide this one.
- **Test:** generate one company, commit one fraud, export a CSV, hand it to an accountant
  friend with no instructions. Watch where they look first.
- **Scope:** solo, 5 months. Spreadsheet-shaped games are cheap and this one is genuinely
  cheap.

---

## Family 5 — The Table

**Verb: negotiate. Feeling: complicity, and spite.** Player-to-player economics. No combat.

### 21 · The Commons `NO COMBAT` `POPULATION`
**Six players, one fishery, one honest differential equation underneath.**

- **The bet:** an unrigged tragedy of the commons. The simulation isn't tuned to collapse — it
  collapses if you collapse it — and the game is the conversation about whether to.
- **Nearest:** *Eco* (a real ecology MMO — closest, but the scale hides the arithmetic) ·
  *Diplomacy* · the *Fishbanks* teaching simulation, which is what this is.
- **Kills it:** the model has a stable dominant strategy, a solver finds it in an hour, and
  the conversation becomes theatre.
- **Test:** **solve the model before building anything around it.** The ODE in Python plus a
  strategy sweep. One day. A dominant strategy found on day one saves a year. This is the only
  concept here whose kill test is a maths problem rather than a playtest.
- **Scope:** 2 people, 6 months, plus the population problem.

### 22 · Escrow `NO COMBAT` `UNMARKETABLE`
**A trading game whose only mechanic is contracts you write in a tiny formal language, and an
engine that enforces them literally.**

- **The bet:** player-authored rules, mechanically enforced, are funnier and sharper than any
  negotiation UI. The comedy is the loophole; the engine is the straight man. (No blockchain.
  The interesting part was never the ledger.)
- **Nearest:** *EVE Online* contracts (a UI, not a language) · *Zachtronics* titles
  (programming as play) · *Baba Is You* (rules as manipulable objects).
- **Kills it:** writing a contract is work and nobody does it twice. If the median player
  settles into three templates forever, the language is overhead with extra steps.
- **Test:** a chat bot and a five-verb language. Twenty people, one week. Count how many wrote
  a contract nobody had written before.
- **Scope:** 2 people, 7 months. It's a programming game wearing a market's clothes; the
  audience is small and devoted.

### 23 · Split the Difference `NO COMBAT` `POPULATION`
**Two players, one deal, and neither knows the other's constraint. Reputation persists between
strangers.**

- **The bet:** reputation across a population turns a one-shot bargaining game into a long
  one. The real decision isn't the price — it's whether you want to be known as someone who
  walks away.
- **Nearest:** the ultimatum game, dressed · *Sea of Thieves* alliances · *Rust* (reputation
  with no memory system to hang it on).
- **Kills it:** alts. Every persistent-reputation system that isn't bound to a real identity
  has died this way inside a fortnight, and the concept needs an answer to it before it needs
  a build.
- **Test:** run the bare ultimatum game with a reputation column on forty people for a week,
  in a spreadsheet. You'll see the alt problem arrive or you won't.
- **Scope:** 2 people, 5 months, plus population.

### 24 · Wake `NO COMBAT` `UNMARKETABLE`
**A funeral. Four to six players are the family. Everyone has a secret, and one of them is who
the deceased actually loved.**

- **The bet:** a social deduction game where the win condition is **not** exposure. You can win
  by keeping something buried — which inverts the genre's entire incentive to accuse.
- **Nearest:** *Fiasco* (tabletop, GM-less — closest tonally) · *Blood on the Clocktower* ·
  *Among Us* (exposure-driven, the thing being inverted).
- **Kills it:** playing a grieving relative is more embarrassing than fun for the median
  group. It sits one notch past what most tables will do sober, and that notch is the entire
  risk.
- **Test:** it's a tabletop game. Print it, play it, one evening, zero engineering.
- **Scope:** 2 people, 6 months digital — but **ship the printed version first** and only
  build it if the paper one travels beyond your own table.

### 25 · Bailiff `NO COMBAT`
**Repossession, on a clock, with the debtor standing in the room.**

- **The bet:** the presence of the person is the mechanic. Everything you take gets physically
  carried past them, and the game never once lets you do it off-screen.
- **Nearest:** *Papers, Please* (the ancestor of this whole family) · *This War of Mine* ·
  *Beholder*.
- **Kills it:** it's one note. Complicity games have a ninety-minute ceiling before the player
  either dissociates or quits, and content doesn't extend it.
- **Test:** build hour one and *only* hour one. Then watch someone play it a second time. The
  second playthrough tells you whether there's a game or a short film here — and if it's a
  short film, ship it as a ninety-minute game deliberately rather than padding it to eight.
- **Scope:** 2–3 people, 8 months.

---

## Family 6 — One Strange Input

**Verb: whatever the body will do. Feeling: embarrassment.**

### 26 · Steady `SOLO`
**The input is your breathing, through the microphone. A game about holding still.**

- **The bet:** breath is a precise enough control axis to build a skill curve on.
  **Unverified, and answerable in an afternoon.**
- **Nearest:** *Nevermind* (biofeedback, but needs hardware) · *Sniper Elite*'s hold-breath (a
  button pretending to be this) · VR meditation apps.
- **Kills it:** detection is unreliable across rooms, mics and people. If calibration takes
  more than ten seconds, nobody ever reaches the game.
- **Test:** a web page with a mic and a wobbling dot. One afternoon, then try it on five
  people in five different rooms — the variance across rooms is the actual finding.
- **Scope:** solo, 3 months.

### 27 · Both Hands `SOLO` `UNMARKETABLE`
**Two players, one keyboard, physically sharing it. Left half and right half.**

- **The bet:** forced physical proximity is a mechanic. You're in each other's space and the
  game is built knowing it.
- **Nearest:** *Overcooked* (shoulder to shoulder, separate pads) · single-keyboard
  *Bomberman* (the accidental ancestor).
- **Kills it:** nobody has this setup anymore. "Two people at one desk for fun" may have an
  install base too small to matter, and that's a distribution problem no design solves.
- **Test:** **don't build anything.** Ask ten people when they last sat two-to-a-keyboard for
  fun. If the answer is "at work, never for fun," you're done.
- **Scope:** solo, 3 months. The mechanic is real; the market may not be. That's exactly what
  the unmarketable tag is for.

### 28 · Hold Music `SOLO`
**The phone tree is the dungeon. You're on hold, and the menu options are the map.**

- **The bet:** an IVR is structurally a dungeon crawl, and playing it *straight* — real hold
  times, real transfers, really being sent back to the main menu — is funnier than
  exaggerating it.
- **Nearest:** *The Stanley Parable* (institutional comedy) · *Papers, Please* · text games in
  the Kafka register. Audio-first games are rare, which is either an opening or a grave.
- **Kills it:** the joke is the premise and the premise is sixty seconds long. **Test at minute
  twenty, not minute one.**
- **Test:** record fifteen minutes of it, play it to someone with a single button, and note the
  moment they stop smiling. That timestamp is the design brief.
- **Scope:** solo, 3–4 months, audio-heavy.

### 29 · Pack
**You're one wolf in an AI pack. You can't give orders. You can only move, and the pack reads
your movement.**

- **The bet:** **positioning as a command language.** The pack runs an inference model over
  your trajectory, and a flank that gets *read* as a flank is a completely different feeling
  from pressing a flank button.
- **Nearest:** *ICO* and *Brothers* (companion legibility) · and, more usefully than any game,
  sheepdog trials — that's where the design research is.
- **Kills it:** players can't tell whether the pack understood them. With no read-back,
  correct play and lucky play are indistinguishable and no skill ever forms. *(Same lesson as
  Estate Liquidators' "build the aggro display before the aggro logic" — build the pack's
  read-back first, on a stupid pack.)*
- **Test:** top-down 2D. Three AI dots, one player dot, and a debug overlay showing what the
  pack thinks you meant. Three days.
- **Scope:** 2–3 people, 9 months.

### 30 · Foley `SOLO` `NO COMBAT`
**Score a film with objects, in real time, in one take.**

- **The bet:** timing against picture is satisfying the way rhythm games are, but the failures
  are *funny* rather than punishing, because a mistimed door still plays.
- **Nearest:** *Rhythm Heaven* (timing, abstract) · *Wattam* and the music-toy space. Nothing
  does foley properly, which for once is probably just an unoccupied niche rather than a
  grave — but check.
- **Kills it:** audio latency. Without tight, predictable latency it's unplayable, and it
  varies by 40ms+ across machines and browsers.
- **Test:** one 30-second clip, six sounds, a keyboard, one day — **and measure the latency
  spread across three machines while you're in there.** That measurement is the real result.
- **Scope:** solo, 4 months.

---

## Family 7 — Reading

**Verb: read, and — in one case — speak. Feeling: recognition.**

### 31 · Dead Languages `NO COMBAT`
**Decipherment, but the language is generated. Real morphology, real syntax, a new one every
run.**

- **The bet:** a generated language can be *fairly* decipherable. This is a hard claim — an
  author controls where the aha happens; a generator has to produce it by construction.
- **Nearest:** *Chants of Sennaar* (hand-authored, excellent — that's the bar) · *Heaven's
  Vault* · *Tunic* (a real cipher, authored).
- **Kills it:** generated languages come out transparent or opaque, and the band where
  deciphering feels earned is narrow.
- **Test:** build only the generator and a corpus. No game. Then solve five of them yourself
  with a pen — you're the test subject, and you'll know by the third. Two days.
- **Scope:** 2 people, 8 months.

### 32 · Marginalia `NO COMBAT` `POPULATION`
**You read a book thousands of strangers have annotated. The annotations are the puzzle and
the multiplayer.**

- **The bet:** a shared text as a persistent world. Good annotations surface, bad ones sink,
  and the book changes shape as the population reads it.
- **Nearest:** *Kind Words* (async, moderated, kind) · *Elden Ring* messages (the mechanic
  without the substance) · *S.* by Doug Dorst (the artefact this wants to be).
- **Kills it:** moderation cost exceeds every other cost combined. Every open text-input
  system converges on the same content within a month, and having a plan for that is a
  prerequisite rather than a later phase.
- **Test:** one public-domain short story, an annotation layer, 200 readers, one week. You'll
  learn about moderation before you learn anything else — which is the correct order.
- **Scope:** 2 people, 6 months, plus permanent moderation.

### 33 · Redaction `SOLO` `NO COMBAT`
**You're a censor. Your only verb is blacking out text, and your deletions play out.**

- **The bet:** **deletion as the input.** No writing, no dialogue trees — the player's entire
  expression is what they remove.
- **Nearest:** *Blackbar* (2013, mobile — redaction as puzzle, closest) · *Orwell*
  (surveillance and selective reporting) · *Papers, Please*.
- **Kills it:** *Blackbar* and *Orwell* between them may already occupy this completely.
- **Test:** **play both comparables first.** That's a £15 test and it precedes every other
  step. Then twenty passages in a text editor with a highlighter.
- **Scope:** solo, 4–5 months.

### 34 · Understudy
**Live repertory theatre. You improvise a role; the other actors are AI; the scene goes off
script and you have to stay in character.**

- **The bet:** a language model can referee "in character" as a **rule** rather than a vibe —
  grading not what you said but whether the person you're playing would have said it.
- **Nearest:** *Façade* (2005 — the structural ancestor, and instructive: it was brilliant and
  nobody could tell what it wanted from them) · AI Dungeon and its descendants (unconstrained,
  and therefore with no failure state).
- **Kills it:** the referee disagrees with itself on identical input. A rule that changes its
  mind isn't a rule, and players detect this within twenty minutes.
- **Test:** no engine. A chat window, a scene, a character sheet, a grader prompt. Run the same
  line past it ten times and measure agreement. **One hour, pass/fail.**
- **Scope:** 2 people, 8 months. **Per-session inference cost is a unit economic, not a line
  item** — price it before designing anything, because it decides whether this is sold once or
  subscribed to. Unverified.

### 35 · Signal `SOLO` `NO COMBAT` `POPULATION`
**Number stations. It broadcasts at 03:00. If you miss it, you missed it.**

- **The bet:** genuine scheduled scarcity buys an attention the game couldn't otherwise
  purchase.
- **Nearest:** ARGs as a form · *The Black Watchmen* · the discovery layer of *Frog Fractions
  2*.
- **Kills it:** scheduled scarcity inside a *paid* product reads as disrespect. There's a
  reason only free ARGs do this, and it isn't that nobody thought of charging.
- **Test:** run it as an actual ARG, free, for two weeks, with no game attached. Count who's
  still there on night twelve.
- **Scope:** solo, 4 months, plus a live operator — a person, indefinitely.

---

## Family 8 — Small and Finishable

**The solo shelf.** Every one of these is one person, under six months, and shippable.

### 36 · Timetable `SOLO` `NO COMBAT`
**A small rail network where the timetable is the program you write, and the trains execute
it.**

- **The bet:** scheduling is a better puzzle than track-laying, which every train game already
  does well.
- **Nearest:** *Shenzhen I/O* (programming as play — the real ancestor) · *Factorio* train
  scheduling (exists, buried under a factory) · *Mini Metro* (elegance, no program).
- **Kills it:** it's *Shenzhen I/O* with a worse theme. The train framing has to add something
  the abstract version doesn't — most likely that failure is visible as a collision rather
  than a red X, which is a real difference but a thin one.
- **Test:** five stations, a text schedule, a tick loop. A weekend. The question is whether
  *reading the failure* is satisfying.
- **Scope:** solo, 4–5 months.

### 37 · Loam `SOLO` `NO COMBAT`
**Farming where the soil is the protagonist and the crop is a lagging indicator.**

- **The bet:** real agronomy — nitrogen, compaction, rotation — with a two-season feedback
  delay. You're farming a system you can't see and won't be graded on until later.
- **Nearest:** *Stardew Valley* (soil is a texture) · *Farming Simulator* (machinery, not
  agronomy) · *Terra Nil* (restoration, abstracted).
- **Kills it:** the delay is too long to teach. If a player can't connect season four's
  failure to season two's decision, it's a punishment generator with a nice palette.
- **Test:** the soil model alone, on a spreadsheet, with a chart. Play ten seasons yourself and
  ask whether *you* learned anything.
- **Scope:** solo, 5–6 months.

### 38 · Blend `SOLO` `NO COMBAT`
**Coffee, whisky, tea. A simulated flavour space and a town of customers with distinct
palates.**

- **The bet:** a flavour space with real dimensionality is a legible optimisation problem and
  a social one at once — you're not making the best blend, you're making the one this town's
  mouths want.
- **Nearest:** *Potion Craft* — closest, and it has an actual ingredient space · *VA-11 HALL-A*
  and *Coffee Talk* (drinks as narrative, no simulation).
- **Kills it:** *Potion Craft* already has this. If its ingredient space is deep enough, the
  flavour framing is a reskin.
- **Test:** play *Potion Craft* for two hours with a notebook, then build the flavour space as
  a scatter plot and ask whether yours is richer. If you can't say why it's richer in one
  sentence, it isn't.
- **Scope:** solo, 5 months.

### 39 · Ten Thousand Doors `SOLO` `HORROR`
**A game entirely about opening doors — the sound, the resistance, what's behind. A horror
game with no monster in it at all.**

- **The bet:** **anticipation without payoff, sustained.** The monster never arrives. If door
  physics and sound design carry two hours alone, you've proven the thing every horror game
  assumes it needs a monster for.
- **Nearest:** *P.T.* (one corridor, no monster for most of it — the proof of concept) ·
  *Anatomy* · *Visage*.
- **Kills it:** two hours with no payoff is a cruelty rather than a mechanic. **Test at minute
  40** — after the player has worked out that nothing is coming.
- **Test:** twelve doors, no monster, excellent audio. A week. Note the minute the player
  relaxes; that number is the whole design.
- **Scope:** solo, 4–6 months. Single-player, so it's the second of three permitted horror
  slots and the co-op cap still has room.

### 40 · Shelf `SOLO` `NO COMBAT`
**A second-hand bookshop where the only mechanic is where things go.**

- **The bet:** arrangement as gameplay. Adjacency changes what sells — someone comes in for one
  thing and leaves with three because of what was sitting next to it.
- **Nearest:** *Strange Horticulture* (organisation as play — closest) · *Unpacking*
  (placement as narrative, no system underneath) · *TCG Card Shop Simulator* (commerce, no
  adjacency model).
- **Kills it:** the adjacency model is invisible. If players can't form a theory about why a
  sale happened they'll arrange by aesthetics and ignore the system — which is fine, but then
  you've made *Unpacking* and should build that instead, deliberately.
- **Test:** forty books, a grid, an adjacency matrix, one simulated week. Two days, entirely in
  a spreadsheet. Ask a tester to predict which shelf sells best.
- **Scope:** solo, 4 months.

---

## Family 9 — Fast

**Verb: aim, dodge, time. Feeling: pressure.** Added on a second pass, because the first pass
produced forty concepts with no twitch anywhere in them and the self-audit called it a bias
rather than a position.

**One honest note before the cards, because it changes how you read them.** Action concepts
resist this document's format. In every other family the bet is a claim about a *system* —
"generated forgeries can be fair," "reputation survives alts" — and a system can be
interrogated on paper, in a spreadsheet, in an evening with friends. An action game's bet is
usually a claim about **feel**, and feel is not falsifiable on paper. There is no dossier
version of "does the recoil read."

So every card in this family has a **playable** kill test — a 2D grey box, a debug overlay, a
dummy — and the costs run from an afternoon to three days rather than from nothing to an
evening. That's a real difference and it's priced into the ranking. It is also, I suspect, the
actual mechanism behind the bias: a generator asked for cheap-to-disprove ideas will quietly
drift toward systems and away from feel, because systems are cheaper to argue about.

Two of these were among the cheapest tests in the document, which is why the top eight changed
— and then one of the two turned out to be a shipped game, which is why it changed again. Both
movements are recorded rather than tidied away.

### 41 · Tell
**A duel where the enemy builds a model of your habits inside a single fight, and starts
punishing them at thirty seconds.**

Not run-to-run learning and not a scripted phase change — an online model of the last half
minute of your inputs, updating live.

- **The bet:** within-fight adaptation is *legible*. The player can feel themselves being
  read, name the habit that got punished, and change it — rather than experiencing it as
  rubber-banding.
- **Nearest:** *Sekiro* (the bar for readable duels, and entirely static) · the *Shadow of
  Mordor* Nemesis system (adaptation, but between encounters, where you have time to notice) ·
  Forza Drivatars (offline-trained, racing).
- **Kills it:** players can't name what it punished. If a tester who just lost says "it got
  harder" instead of "it started blocking my third light attack," the system is invisible, and
  an invisible system is indistinguishable from difficulty scaling — which is cheaper.
- **Test:** **build the read-back before the model.** One dummy enemy, one debug panel showing
  the habit it currently thinks you have, and a stupid punish. Three days. Then hide the panel
  and see whether testers still name the habit. *(Same lesson as Pack (#29) and as Estate
  Liquidators' "build the aggro display before the aggro logic" — this is now the third
  independent concept to land on it, which is worth noticing.)*
- **Scope:** 2–3 people, 9 months.

### 42 · Throng
**One against five hundred, and the crowd is a fluid.**

Not five hundred enemies with individual AI — a continuum with pressure, flow, and
compression. You fight by displacing a substance.

- **The bet:** a crowd simulated as flow makes positioning matter more than your weapon does.
  The skill is reading currents and creating a gap, not clearing spawns.
- **Nearest:** *Dynasty Warriors* (crowds as scenery that falls over) · *Total War* (real mass,
  but strategic and from above) · *Hades* (density as a difficulty dial, no flow model).
- **Kills it:** at 500 agents the readable information collapses into noise and the player just
  mashes. Legibility, not performance, is what kills this — though performance will try.
- **Test:** **strip the combat out entirely.** 2D top-down, 500 boids, one player dot, no
  weapon. Can a tester deliberately steer the crowd — split it, herd it, open a lane? Three
  days. If they can't do it with no enemies attacking them, they never will with.
- **Scope:** 3 people, 10–12 months. The crowd solver is the whole engineering risk and it's a
  real one.

### ~~43 · Recoil~~ — **dead, verified 2026-08-06**
**No walk button. Firing is how you move.**

Checked on request, killed in about four minutes, moved to the graveyard (entry 26). The
number is left vacant rather than reused so the cross-references above still resolve.

**What killed it:** *Kickback: Shoot to Move!* (Dot Blood / Targem Games, Steam, 14 July 2025)
is this concept, including the bet. Its store copy — *"no WASD, no mouse movement… your choice
of weapons will shape how you move and survive"* — is a paraphrase of the sentence I wrote for
"the bet," which is about as complete an occupation as a card in this document can suffer.
*Recoil Rush* (Steam) is a second commercial entry, and itch.io carries an entire **`shoot-to-
move` tag** with a page of them.

**The useful part.** I marked this "most likely to be occupied" and put it fifth in the top
eight anyway, on the argument that a weekend prototype would settle it. That was the wrong
instrument: the store check costs five minutes and the prototype costs two days, and I had
already written down the suspicion. **A named suspicion should be resolved by the cheapest
instrument that can resolve it, before the ranking, not by the test the ranking prefers.**
That's a defect in how this document was assembled, not in the idea — see the note at the top
about verification order.

**One salvage.** *Kickback* is a top-down roguelike; *Downwell* is a single-axis platformer. No
one found has committed to recoil-only movement in **3D**, where the nausea risk I listed is
real and unexplored. That's a different concept with a different kill condition, and it is not
this card — if you want it, write it fresh rather than reviving this one.

### 44 · Ghosts `POPULATION`
**A bullet-hell where the hazards are other players' recorded runs.**

- **The bet:** asynchronous PvP where the danger *is* the population. Nobody is online with
  you and everybody is against you.
- **Nearest:** *Trackmania* ghosts and *Super Meat Boy* replays (both purely cosmetic — the
  step is making them lethal) · *Dark Souls* invasions (live, and the tonal ancestor) ·
  *Crypt of the NecroDancer* leaderboards.
- **Kills it:** the ghost pool converges. If everyone's run collapses onto one optimal path
  within a week, the level is static again — and you've built a hand-authored level the
  expensive way, via infrastructure.
- **Test:** **no new game needed.** Take any existing score-attack level, record fifty runs
  from ten people, replay them as hazards, and measure path variance on day 1 against day 7.
  Two days of work and it answers the only question that matters.
- **Scope:** 2 people, 6 months, plus a population.

### 45 · Sever
**Melee with limb-level damage and no health bar. You win by disabling.**

- **The bet:** an injury model instead of an HP pool makes every exchange legible and
  permanent. A cut arm stays cut, both fighters can see it, and the fight's state is written on
  the bodies rather than in a bar.
- **Nearest:** *Exanima* (physics melee with real injury — closest, and deliberately slow) ·
  *Kingdom Come: Deliverance* (directional, still HP-driven) · *Mordhau*. Injury-as-state
  exists in simulations; it does not exist at action speed, which is either the gap or the
  reason.
- **Kills it:** at speed, players can't read which limb they hit or what it cost. If the state
  isn't legible inside half a second, you've built an HP bar with bookkeeping — worse than an
  HP bar, because it's also confusing.
- **Test:** no combat AI, no enemies. Two players, one training dummy, one weapon, and a
  visible injury readout. **Can they call the hit before the readout updates?** If not, stop.
  Three days.
- **Scope:** 3 people, 12 months. The most expensive concept in the document, and the least
  compressible — this one does not have a cheap 2D version.

### 46 · Direct `SOLO`
**You control the camera. The character runs toward whatever you frame.**

- **The bet:** **framing is the verb.** The skill is composition under pressure, and the
  character's competence is downstream of your attention rather than your dexterity.
- **Nearest — checked 2026-08-06, and it survives.** No shipped game was found in which
  framing is the sole verb and the character's competence is downstream of it. What *was*
  found, and all three matter:
  - **Gaze-directed steering** is a standard VR locomotion technique, studied since the
    earliest VR research. So the mechanic is not novel — it's a solved *interface* problem
    that nobody has promoted to a skill.
  - ***Cameraman*** (Polyfrog Studio, itch.io): you film enemies so an autonomous protagonist
    can fight them. The closest thing found, and the difference is real — the player still
    walks with WASD, so framing is a second verb rather than the only one.
  - **A US patent** covering automatic character movement toward points of interest driven by
    the player's camera view. Someone thought this was worth owning. Probably unenforced, as
    mechanic patents usually are, but it's evidence the idea has been reached before.
- **Kills it:** indirect control reads as unresponsive — and **there is now adverse evidence
  for exactly this**, which is the real result of the check. Comparative VR studies find
  gaze-directed steering *slower and less comfortable* than a gamepad. That is not fatal: those
  studies measure task efficiency, and the bet here is that framing is a **skill** rather than
  a convenience, which efficiency tests are the wrong instrument for. But it raises the bar.
  The afternoon prototype now has a sharper question than "is it responsive" — it's **does
  being slower than a gamepad stop mattering once it's the whole game?** If the character does
  the wrong thing twice in the first minute, players quit and never articulate why.
- **Test:** 2D. A dot that runs toward the centre of your view, and a reason to go somewhere.
  **One afternoon, and you'll know inside ten minutes.** The cheapest decisive test in the
  document and the reason this card enters the top eight.
- **Scope:** solo, 5 months.

---

## The top eight

**Ordering criterion: how cheaply can I find out I'm wrong, weighted by how much survives a
pass.** Not excitement. Excitement ranking is why people build the expensive idea first and
learn nothing for a quarter.

| # | Concept | Cost to run the kill test | What it costs to be wrong |
|---|---|---|---|
| 1 | **Provenance** (#16) | One day, text only, no engine | Nothing — the test *is* the generator you'd need anyway, so a fail leaves you a tool and a finding |
| 2 | **Direct** (#46) | **One afternoon**, 2D, decisive in ten minutes | An afternoon. And a fail is genuinely informative: it tells you *why* indirect control keeps getting buried |
| 3 | **Party Line** (#1) | One evening, four friends, zero code | Nothing. Literally an evening |
| 4 | **The Commons** (#21) | One day of Python and a solver sweep | Nothing, and a fail saves a year of building a conversation that turns out to be theatre |
| 5 | **Tow** (#7) | A weekend, 2D | A weekend. And the rope-constraint code survives into anything physical |
| 6 | **Sworn** (#2) | One evening, on paper | An evening — but the *build* is 9–12 months, so a false positive here is the most expensive mistake in the table. Run it twice, with two different groups |
| 7 | **Removals** (#6) | **Zero.** Estate Liquidators Phase 1 already runs it | Nothing. Free information from work you're doing anyway |
| 8 | **Pack** (#29) | Three days, 2D, debug overlay | Three days, and the read-back finding transfers to Tell (#41) and to any companion-AI design you ever do |

**How this table has moved, in order.** Worth keeping visible, because the movement is the
only evidence that the ranking is doing anything.

- **The action pass** put Direct (#46) and Recoil (#43) in on merit — an afternoon and a
  weekend, both decisive, both solo-shippable — and pushed out **Ledger** (#20) and **Pack**
  (#29). Ledger's removal was overdue on principle: it shares its kill condition with
  Provenance, so it was never an independent option and counting it as one overstated the
  portfolio. It's still worth building; it just isn't a separate *question*. Pack was
  straightforwardly outbid, and noted at the time as "the first thing back in if any of the
  above dies on contact."
- **The verification pass** then killed **Recoil** (#43) outright — *Kickback: Shoot to Move!*
  shipped in July 2025 with the same bet — and Pack came back in at #8, exactly as written.
  Direct survived its check and holds #2.

**One place this table was wrong about itself.** Recoil sat at #5 on the argument that a
weekend prototype would settle it, while its own card said "most likely to be occupied." The
suspicion was already written down and the instrument that could resolve it cost five minutes,
not two days. **Resolve named suspicions with the cheapest instrument that can resolve them,
before ranking — not with the test the ranking happens to prefer.** The store check belongs
above the whole table, which is where the header now puts it.

**Runner-up, and the one worth arguing about: Understudy (#34).** Its test is the cheapest in
the whole document — one hour, a chat window, ten repeated inputs, measure agreement. By raw
cost-to-disprove it should be top three. It isn't, because a *pass* barely derisks it:
referee consistency is necessary and nowhere near sufficient, the *Façade* problem (players
can't tell what the game wants) sits entirely downstream of it, and the per-session inference
cost is unpriced. Cheap test, weak signal.

That distinction — cost to disprove versus **information gained per pound** — is the real
criterion, and Understudy is where the two come apart. If you think a cheap test that proves
little still beats a moderate test that proves a lot, promote it and the ranking changes.

**The action equivalent of that argument is Tell (#41).** Three days for the read-back, and a
pass proves only that adaptation is *legible* — not that being read is fun to play against.
Legibility is the necessary half and the cheap half. Highest ceiling in Family 9, weakest
signal per day spent.

**If you only do one thing this Saturday:** Provenance's fifty text dossiers. It's a day, it
needs no engine, the artefact survives failure, and it also answers Ledger. **If you want to
do one thing this afternoon:** Direct's running dot. Ten minutes of play answers it, and the
answer is unambiguous in a way none of the systems concepts can be.

---

## The graveyard

Twenty-six that were generated and cut, with the reason. This is the section that should make
you trust the other forty-five. Entries 20–25 came from the action pass, and that family needed
its own rejections more than most — action is the most crowded space in games, so a pass that
produced six keepers and cut nothing would be a pass that wasn't looking. Entry 26 is the first
one killed by a search rather than by an argument, and it was a keeper until it wasn't.

1. **Chorus** — co-op where sung pitch is the network protocol. The accessibility floor is a
   wall, not a slope: a large minority genuinely cannot pitch-match, and there's no parallel
   path that isn't a different game.
2. **Bequest** — a museum curated across 200 years by predecessors you don't control.
   Collapsed into The Inheritance (#12), which has the same bet with a live person on the far
   end.
3. **Deckbuilder where the deck is your inventory weight** — banned by the brief, and the ban
   is correct.
4. **"Papers, Please but for organ transplants"** — a comparable, not an idea. The moral weight
   is doing the job the mechanic should be doing.
5. **Time-loop detective** — *Outer Wilds*, *Twelve Minutes*, *Deathloop*, *The Forgotten
   City*. Fully occupied, by good games.
6. **Asymmetric VR, one in the headset and four on the couch** — Both Hands' install-base
   problem (#27) with a £400 floor under it.
7. **Call-centre ticket resolution** — no bet. It's a job with a UI.
8. **Procedural dungeon where the dungeon is a body** — setting as hook. Banned, and it still
   arrived on the second pass.
9. **Co-op submarine** — *Barotrauma*, and it's excellent.
10. **Deduction where the murderer is an LLM** — Understudy's referee-consistency problem
    (#34) without the theatrical framing that makes inconsistency forgivable.
11. **Plants that grow between sessions in real time** — the good half of this is #13 and #14.
    On its own it's a push notification.
12. **Racing where the track is drawn by the previous player** — *Trackmania* and the entire
    user-track genre.
13. **Audio-only maze** — tried repeatedly (*A Blind Legend*, *The Nightjar*). The ceiling is
    well documented and it is low.
14. **A game where you play the building, not the people** — fails the picture-the-hands test
    on contact.
15. **Multiplayer where you can't see your own character** — cute for an hour. Every playtest
    of this shape ends with players reading their position off a teammate, which is a chore
    with a novelty wrapper.
16. **Cozy crafting with a dark secret** — banned, arrived anyway on the second pass. That it
    keeps arriving is precisely why the ban is in the prompt.
17. **Negotiating against LLM merchants** — the merchant is either prompt-exploitable or
    arbitrary, and those are the same failure. Same problem as #34, in a context where nobody
    forgives it.
18. **Physics game where you play the furniture** — funny for one screenshot.
19. **City builder where citizens write their own laws** — the rigorous version is
    *Democracy*; the fun version is a chat log; nobody has found the middle, and I don't have
    a mechanism for it either. Cut for honesty rather than for quality.

*From the action pass:*

20. **Rhythm FPS** — *BPM: Bullets Per Minute* and *Metal: Hellsinger*. Occupied twice, by two
    good games, which is about as closed as a space gets.
21. **A shooter where reloading is the whole skill** — *Receiver 2*, and it commits harder than
    my version did.
22. **Soulslike where you play the boss** — the bet is a framing, not a mechanic. It also
    arrives on every list like this one, which is usually the tell.
23. **Fighting game where you only see your opponent's shadow** — reading the opponent is
    already the entire genre. Removing information doesn't change the read, it deletes it.
24. **A racing game with no brake** — the bet ("removing an input deepens the line") is real,
    and *Trials* and *Descenders* have both explored the neighbourhood. It's a mode, not a
    game.
25. **Extraction shooter with a twist** — banned by the brief, and it arrived twice. The
    attractor is strong enough that the ban is doing visible work.

*Killed by verification rather than by judgement:*

26. **Recoil** (was #43) — *Kickback: Shoot to Move!* (Dot Blood / Targem, Steam, July 2025)
    ships the concept and the bet; *Recoil Rush* is a second commercial entry; itch.io has a
    `shoot-to-move` tag with a page of them. The only unoccupied version is 3D, which is a
    different concept with a different kill condition and should be written fresh rather than
    revived. **This is the first entry here killed by evidence instead of by opinion, and it
    took four minutes** — which is the argument for doing the search before the ranking rather
    than after it.

---

## What this set is missing

The prompt asks for coverage. Here's where the coverage is thin, which is a finding about the
generator as much as about the ideas.

**~~Nothing here is fast.~~ Addressed, and the fix is more interesting than the gap was.**
The first forty had no aim, no twitch and no combat depth in them at all — 28 cards explicitly
`NO COMBAT` and most of the other twelve incidentally so. Family 9 adds six action concepts
and the prompt now carries an explicit quota (`GAMES-PROJECT-PROMPT.md`, coverage section).

But the *diagnosis* was wrong, and that's the part worth keeping. I called it a taste bias.
It's structural: this document ranks by cost-to-disprove, action bets are claims about
**feel**, and feel has no paper version. Every cheap test in Families 1–8 is a spreadsheet, a
solver, or an evening with friends — none of those instruments can measure whether a recoil
reads. So a generator optimising for cheap falsifiability drifts away from action
automatically, and no amount of taste correction fixes that. **The quota is a patch on a
scoring function, not a change of mind**, and it's worth knowing which of those you're
applying. The same distortion presumably suppresses anything else whose quality lives in
execution rather than in structure — animation, comedy timing, horror pacing. Six of those are
now in; the bias that removed them is still running.

**Eight concepts need a live population** (#5, #12, #13, #21, #23, #32, #35, #44). That's the
most-repeated structural risk in the set, and it only became visible when the tags were
counted rather than while they were being written. A population dependency is worse than a
technical risk: you can't test it small, and it converts a project into an operation with
staffing.

**Four concepts rest on "generation can be fair"** (#16, #20, #31, and #34's referee). That's
one bet wearing four hats. Test it once — cheaply, on Provenance — and let the single result
decide the other three. Treating them as four independent options overstates the portfolio's
diversity by three.

**No mobile, no console-first, no local-couch beyond two entries.** Platform diversity wasn't
in the prompt's axis list and it shows. Worth adding.

**Almost every market claim is still memory.** Two have now been checked — #43, which died,
and #46, which survived. Forty-three have not. The three I'm most suspicious of are flagged on
their cards (#9, #33, #38) and should go next.

**And the hit rate is the finding.** One of the two cards checked was fully occupied by a game
that shipped thirteen months ago, and it was a card I had already labelled "most likely to be
occupied" — I just ranked it above the check instead of below it. Two data points is not a
rate, but it is enough to say the prior should be *pessimistic*: assume a concept is taken
until a search says otherwise, rather than the reverse. The whole document is currently written
the other way round, and that's its largest remaining defect.

**The cheapest fix is an ordering change, not more work.** The search is five minutes per card
and it strictly dominates every other instrument here — it can kill a concept outright, which
no prototype can do faster. It should run across all 45 before anything is ranked, let alone
built. Four hours, once. `GAMES-PROJECT-PROMPT.md` now says so explicitly; this document was
built before it did.
