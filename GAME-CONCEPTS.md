# Forty Game Concepts

`GAMES-PROJECT-PROMPT.md`, run once, then corrected and verified across five passes. **40 live
concepts** in nine families, a ranked top eight, and a graveyard of thirty-one.

All 47 cards have been checked against the market. **Seven were games that already exist; one
was recovered from the graveyard once its rejection was audited.** The
[verification ledger](#verification-ledger) records what the search found for **every card**,
and the six cards it contradicted have been rewritten — so the cards and the ledger no longer
disagree, and there's no "trust the newer one" clause to remember.

**Pass two — the action amendment.** The first pass produced 40 concepts with no twitch, no aim
and no combat depth anywhere in them, and the self-audit at the bottom called that a bias of
the generator rather than a position worth defending. **Family 9 — Fast** is the correction:
six action concepts, and a note on why action resists this format. Two entered the top eight on
merit and displaced two entries, written up in that section rather than quietly swapped.

**Pass three — verification, and it cost seven concepts.** Every card was searched. Seven are
occupied by shipped games (#3, #7, #9, #33, #36, #43, #45), four were wounded, twenty-eight
survived. **Two of the seven were in the top eight**, and three were on cards I had already
labelled probably-occupied and ranked highly anyway — which is the whole lesson: a suspicion
written on a card does nothing, only the search does anything. Ninety minutes, and it
outperformed every prototype in the document put together.

It also **breached the action quota** and I've left it breached rather than padded — the two
replacement concepts I generated were searched first and both died before a card was written.
See the ledger.

**Pass four — auditing the rejections.** The sweep checked what the document *kept*; it never
checked the 25 things it threw away. Doing that reversed no verdicts but found six wrong
reasons, one of which — an unchecked assumption that LLM referees can't be consistent — had
killed two concepts and was setting the kill condition on a live card. *Arsenic* falsifies it,
and #34 Understudy went from runner-up to **#3** as a result. Write-up in
[Auditing the rejections](#auditing-the-rejections).

**Pass five — one concept came back.** Graveyard entry 17 was reopened as **#47 Reservation**,
searched first, and the search *supplied the design* rather than merely clearing it: the
original rejection was an accurate description of the naive build, and the fix is
architectural. One recovery against seven kills is the honest ratio — **the audit is worth
running, and it is not a way to get your ideas back.**

**What this is for.** Finding the one thing to prototype on Saturday. Not a list to feel good
about. Every card carries a written-down result that would make you drop it and a test small
enough that you'd actually run it.

**What is verified and what isn't.** Nothing here is verified. Every "nearest shipped game"
is memory, and that memory has a cutoff — some of these shipped last year and I don't know it.
**Search before you rank — this document learned that the expensive way.** All 45 cards have
been checked and the results are in the ledger below. The short version: seven concepts were
games that already exist, three of those were on cards I had *already flagged* as probably
occupied and ranked highly anyway, and two of them sat in the top eight. The whole sweep took
about ninety minutes.

**What that means for reading the rest of this.** SURVIVED means "a real search found nothing
occupying the bet" — not "nothing exists." Jam builds and unlisted prototypes are invisible to
it, and several survivors are one design decision away from being occupied (see the caveats in
the ledger). Every kill condition on every surviving card is still unrun. The portfolio is now
honestly scoped and completely untested.

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

Quota check, current: 9 families, **40 live concepts**, 7 killed by search, 1 recovered from
the graveyard · Family 5 is now at 6, the per-family cap · 0 co-op horror (the one entry died)
and 1 solo horror · 17 solo-shippable · 27 with no combat · **4 with combat as the point —
the action quota is breached, see below** · 7 unmarketable · 8 needing a population.

---

## Verification ledger

All 45 cards checked against the market on **2026-08-06**. This table is the document's
current source of truth; where a card's `Nearest` field disagrees with this ledger, the
ledger is newer.

**Of 47 cards written: 7 dead, 4 wounded, 36 survived.** 40 remain live.

**#47 Reservation** was written *after* its search rather than before, which is the order this
document spent four passes learning. The search didn't just clear it — it supplied the
architecture the concept had been missing, and the original rejection turned out to be an
accurate description of the version without that architecture. Recovering it cost four
searches and about twenty minutes.

| Verdict | Count | Cards | Meaning |
|---|---|---|---|
| **DEAD** | 7 | #3, #7, #9, #33, #36, #43, #45 | A shipped game occupies the concept *and* the bet. Tombstoned in place; graveyard entries 26–32. |
| **WOUNDED** | 4 | #2, #37, #40, #41 | The bet was partly taken, or a claim on the card was factually wrong. All four cards rewritten. #2 and #40 need real work before either is buildable. |
| **SURVIVED** | 35 | everything else | A real search found nothing occupying the bet. Not the same as "nothing exists" — see the caveats. |

**One verdict a search structurally cannot deliver:** #40 Shelf. *Shelf by Shelf: Bookstore
Simulator* exists and is unquestionably in the same room, but whether it models **adjacency**
— the actual bet — isn't in the store copy or any review. It needs two hours of play, not more
searching. Counted above as wounded, listed separately because the instrument is different.

### What the search actually found, per card

The cards' `Nearest` fields are a design argument — *why* a comparable matters. **This table is
the verification record.** Keeping them apart is deliberate: copying findings onto forty cards
would recreate exactly the drift this repo's `IMPROVE-PROMPT.md` exists to fight. Where a
card's `Nearest` is factually *contradicted* by this table, the card was rewritten (#2, #34,
#37, #40, #41, #46); everywhere else the card's argument stands and this is the evidence.

`EMPTY` = a real search found nothing at all. That is a finding, not a failure of recall.

| # | Concept | What the search surfaced |
|---|---|---|
| 1 | Party Line | *911 Operator* (has a map — the map does the work), *Emergency Call 112*, *SIM Dispatcher*. Nothing built on conflicting testimony. **Name risk:** the 2025 narrative game *Dispatch* owns the word |
| 2 | Sworn | **[*Arsenic*](https://playarsenic.com/)** — GM agent validating every claim for consistency. *CrimeChat*, *Contradiction: Spot The Liar*. Card rewritten |
| 4 | Nightshift | *Killer Frequency*, *Night Call*, *Dead Air Radio*. All content-driven; silence-as-mechanic unoccupied |
| 5 | Cartographer's Error | Nothing. Closest remains *Death Stranding*'s async structures |
| 6 | Removals | *Moving Out* / *Moving Out 2* only. The simulation-depth gap is real |
| 8 | Scaffold | *Construction Crew* (co-op, no structural sim), *Construction Simulator*, *Besiege*, *Poly Bridge*. Structural integrity exists in *Valheim* and *Dwarf Fortress*, never as the game |
| 10 | Weight | *Carry The Glass* (co-op fragile carry — not accelerometer), Wii-era motion, *Jackbox* phone-as-controller |
| 11 | Thirty Years of Tuesdays | *100 Years — Life Simulator*, *BitLife*, *King of Dragon Pass*. No weekday elision anywhere |
| 12 | The Inheritance | *Next, please* (async, builds on predecessors' paths). Save-inheritance between strangers not found |
| 13 | Slow Mail | **[*Leaving Cambridge*](https://parenthesispress.itch.io/leaving-cambridge)** — letters written across a real calendar year. The bet exists, in tabletop. *Kind Words* |
| 14 | Erosion | **[*Terra Firma*](https://store.steampowered.com/app/2143140/Terra_Firma/)** — tectonics and erosion over geological time. *From Dust*, *Terra Nil*, *Mountain*. The offline-while-away half is unclaimed |
| 15 | Ten Year Lease | *[Nova Alea](https://molleindustria.org/nova-alea/)* (gentrification — but you play the investor, not the tenant) |
| 16 | Provenance | *FakeMuse* (academic serious game). *Strange Horticulture*, *Contraband Police*. Generation unoccupied — **and the kill test has since been run** |
| 17 | Differential | *Veterinary Clinic Simulator*, *Vetdle*, *VetVR*, *Vety*. **None price the tests**, which is the entire bet |
| 18 | Luthier | `EMPTY` — no instrument-building game with DSP as the win condition. The field is a Stanford CCRMA course and the NESS project |
| 19 | The Restorer | *Modelist: Restorer*, *Extremely OK Painting Restoration Studio*, *PowerWash Simulator*. Irreversibility unoccupied |
| 20 | Ledger | *The Investigation Game* (forensic accounting training, real cases). *Obra Dinn*, *Golden Idol*. Generated fraud unoccupied |
| 21 | The Commons | *Eco*, and a thick layer of teaching sims — *Fishbanks* (MIT), MobLab's Fishery. Unrigged-as-a-game unoccupied |
| 22 | Escrow | `EMPTY` — player-written enforced contracts exist only in academic market-simulation papers and one game patent |
| 23 | Split the Difference | Only the academic ultimatum-game literature (partner vs stranger matching), which corroborates the bet |
| 24 | Wake | `EMPTY` — no social deduction game where you win by *keeping* a secret |
| 25 | Bailiff | Nothing. *Papers, Please* and *Beholder* remain the ancestors |
| 26 | Steady | *SILENT BREATH*, *Hold Your Breath*, *Breathless* — **all breath-as-stealth**. Breath as a precision axis unoccupied. Plus VR archery breath-hold research |
| 27 | Both Hands | *Two Friends One Keyboard* (itch), LEGO-game split keyboards. Exists as a concession, never as a design |
| 28 | Hold Music | **[*IVR Adventure Game*](https://rabbitboots.itch.io/ivr-adventure-game)** — audio-only, navigated by touch-tone. It's a cave, not a bureaucracy. Form prototyped |
| 29 | Pack | *The Wild Wolf* — AI packs where you **assign roles**, i.e. the opposite of the bet. *WolfQuest* |
| 30 | Foley | `EMPTY` — no foley game at all |
| 31 | Dead Languages | *Chants of Sennaar*, *Heaven's Vault*, *Tunic*. All hand-authored; generation unoccupied |
| 32 | Marginalia | Concept not found. **Name taken three times** — a card game, a Connor Sherlock game, and a Steam app. Plus a collaborative e-reading patent. Rename |
| 34 | Understudy | *Improbotics*, *ImprovMate*, academic co-creative-improv work, *Façade*. Card rewritten and promoted |
| 35 | Signal | *Broadcast* (itch), *Stories Untold* ep. 3, *Number Spies*. The setting is occupied; **real scheduled scarcity is not** |
| 37 | Loam | **FS25 soil mods** do full N/P/K, pH, rotation. Card rewritten — my claim was wrong |
| 38 | Blend | *Potion Craft*, *Potion Shop Simulator*, *VA-11 HALL-A*, *Coffee Talk*. Was flagged suspect; **the flavour-space-with-palates bet is not confirmed occupied**, but the neighbourhood is busy |
| 39 | Ten Thousand Doors | *P.T.*, *Anatomy*, *Visage*. No door-only game found |
| 40 | Shelf | **[*Shelf by Shelf: Bookstore Simulator*](https://store.steampowered.com/app/3943720/Shelf_by_Shelf_Bookstore_Simulator/)**. Unresolvable by search — see above |
| 41 | Tell | **[*Echo*](https://store.steampowered.com/app/551770/ECHO/)** — enemies learn your moves and use them against you. Better comparable than the card had; adapts between cycles, not within a fight. Card rewritten |
| 42 | Throng | `EMPTY` — crowd-as-fluid exists as [SPH crowd-simulation research](https://www.sciencedirect.com/science/article/abs/pii/S0097849321001205), never as an action game |
| 44 | Ghosts | `EMPTY` — ghost replays are universally cosmetic (*Trackmania*, *Mario Kart*). Nobody has made them lethal |
| 46 | Direct | Gaze-directed steering as a **standard VR locomotion technique**; *Cameraman* (itch, but you still walk); US patent 10974149. Card rewritten |
| 47 | Reservation | *Suck Up!*, *Whispers from the Star*, *1001 Nights*, *Wanderfolk* — **all let the model own the outcome**. *Recettear* is the ancestor without language |

**Seven `EMPTY` results**, and they are the most valuable rows here: #18, #22, #24, #30, #42,
#44, plus #5. "Nobody has done this" now means a search came back empty rather than that I
couldn't recall one.

**Three caveats on the survivors, all of which cut the same way.**

1. **A search proves absence of *indexed* work, not absence of work.** Half the kills came
   from itch.io pages and one-line store blurbs; the next tier down is jam builds nobody
   writes about. Treat SURVIVED as "not obviously taken."
2. **Four survivors have a name collision, not a concept collision** — #32 Marginalia (a card
   game, a Connor Sherlock game, and a Steam app already use it) and #1 Party Line (the 2025
   narrative game *Dispatch* owns the dispatcher space by association). Rename before you get
   attached.
3. **Several survivors are surrounded.** #26 Steady survives only because *Silent Breath*,
   *Hold Your Breath* and *Breathless* all use breath for **stealth**, not as a precision
   axis. #35 Signal survives because number-station games (*Broadcast*, *Stories Untold*
   ep. 3) don't use real scheduled scarcity. #28 Hold Music survives an existing
   [IVR Adventure Game](https://rabbitboots.itch.io/ivr-adventure-game) because that one is a cave, not a bureaucracy. Those are one design
   decision away from being occupied, and a competitor could make that decision tomorrow.

### The action quota is breached, and I'd rather say so than pad it

Family 9 lost #43 and #45, leaving **four** action concepts against the prompt's floor of six.
The rule I wrote last pass said a breach means generating replacements rather than quietly
dropping the quota. So I generated two — **Tempo** (a duel with no attack button: you block,
parry and step until the opponent's stamina breaks) and **Standing Room** (your own attacks
destroy the floor, so offence is the timer) — and **searched them before writing the cards.
Both died.** Tempo: [*Sword Instructor Gerald*](https://bossblitz.itch.io/sword-instructor-gerald) already runs blocking-drains-stamina to
exhaustion, and *Perfect Parry* is parry-only. Standing Room: [*Decay Protocol*](https://gabrielkaszewski.itch.io/decay-grid) has the grid
disintegrate as you cross it, *Unstaball* breaks tiles under you, *The Finals* does it at
scale.

**Two search-first attempts, two deaths, no code written** — which is the process working, and
also the answer to why the quota exists. Action is the densest space in games; the same filter
that kills one card in eight elsewhere kills action ideas at roughly one in two here. **The
honest conclusion is that this prompt may not be able to satisfy its own action quota**, and
that's better information than three padded cards would have been. Left breached deliberately.

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
- **Nearest — checked 2026-08-06, and the bet has been taken.** [*Arsenic*](https://playarsenic.com/) is an AI murder
  mystery in which "a Game Master agent validates every response for consistency" and surfaces
  contradictions across suspects automatically. That is my bet — automated consistency grading
  — already built and shipped. [*CrimeChat*](https://apps.apple.com/ly/app/crimechat/id6446483261) does it on-device. *Contradiction: Spot The Liar*
  is the FMV ancestor. Also: *Obra Dinn*, *Deception: Murder in Hong Kong*.
- **What's left, and it's narrower but not nothing.** Every one of those puts an **AI** in the
  suspect's chair. The claim-log engine is the *hard* part and it now has working precedent —
  which is good news for feasibility and bad news for novelty. The remaining bet is the one
  thing none of them do: **a human friend lying, graded by that engine, in front of their
  friends.** Rewrite the card around that before building, and read *Arsenic*'s design first.
- **Kills it:** the median player freezes in the suspect seat. If only extroverts can carry
  the role, it's dead air three rotations out of four and the group stops picking it.
- **Test:** paper. Print the claim log as a form, one friend lies, three interrogate, you
  referee with a pen. One evening.
- **Scope:** 3–4 people, 9–12 months. The claim ontology is the hard part and it's a design
  problem, not an engineering one.

### ~~3 · The Quiet Part~~ — **dead, verified 2026-08-06**
**The monster hears words, not volume. Some words are forbidden this run. Talk around them.**

> **Killed by [*Cursed Companions*](https://store.steampowered.com/app/3265230/Cursed_Companions/)** (Crimson Forge), a co-op horror game
> whose central system assigns every player a forbidden word each run — and hurts you when a
> *teammate* says yours. It also punishes swearing with a dedicated monster. That is the
> concept, the bet, and one refinement I hadn't thought of. Graveyard entry 27. The card below
> is kept as a record.

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

### ~~7 · Tow~~ — **dead, verified 2026-08-06**
**Orbital salvage. One tool: a winch cable. Nothing has thrusters except you.**

> **Killed by [*Orbital Salvager*](https://store.steampowered.com/app/4384760)** (Steam, 5 March 2026): a 2D space sim about
> mastering orbital mechanics to recover salvage, built on *tethering and towing* under scarce
> fuel. It is the concept **and the prototype I proposed** — my one-weekend test was "2D, a
> point mass, a rope constraint." Someone shipped that five months ago. *Space Salvage* is a
> second entry. Graveyard entry 28. Was ranked #5 in the top eight.

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

### ~~9 · Deep Clean~~ — **dead, verified 2026-08-06**
**Crime-scene remediation, two-person crew, and a UV pass at the end that scores what you
missed.**

> **Killed by [*Crime Scene Cleaner*](https://store.steampowered.com/app/1040200/)**, with *Viscera Cleanup Detail*, *Body of
> Evidence* and *Breach and Clean* behind it. The card already said "this is the one I'd cut
> first" and named VCD as possibly-sufficient occupation; the search found a game with the
> literal premise. Graveyard entry 29. **Predicted correctly, ranked accordingly, and still
> only settled by a search** — the one card where the document's own judgement got there first.

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
- **Test — RUN, 2026-08-06. `concepts-sim/provenance.py`. The kill condition is not met.**
  A seven-attribute model of period construction (woods, joinery, finish, hardware, saw
  marks, wear), forgers who err toward *neighbouring* periods, and — the part that makes it
  a real test — genuine objects carrying **honest anomalies**: repairs, replaced hardware,
  transitional pieces. 8,000 objects.

  | Measure | Result |
  |---|---|
  | Undetectable forgeries | **7.8%** — a real accuracy ceiling; you cannot always be right |
  | Forgeries in the learnable 1–3 cue band | 74% |
  | Distribution overlap, genuine vs forged | **29% of mass is ambiguous** |
  | Best achievable accuracy, full knowledge | **85.5%** at "flag on ≥2 inconsistencies" |

  **The finding worth having is emergent and I didn't design it in.** The optimal threshold
  *moves as you learn*: a novice should flag on any single inconsistency, an expert should
  demand two — because expertise means being able to see the honest repairs a novice reads as
  fakes. Skill expresses as *raising your bar*, not sharpening your eye. That's a real
  mechanic, it fell out of the model, and it's the strongest argument yet that this card is
  the right one to build.

  **What it does not show, and two things to distrust.** It shows a learnable signal exists to
  be communicated — not that dossier prose communicates it, not that anyone finds it fun. The
  fifty dossiers and the friend are still owed. And: M1's middle band is substantially a
  reflection of the forger-skill distribution I chose, so it is weakly informative; M3 is the
  load-bearing measure because it puts two independently-generated distributions against each
  other. M2's "no step function" passed at 43% against a 45% bar **I picked myself** — that's
  a marginal pass on an unjustified threshold, and I'd want a second opinion on it before
  leaning on it.

  *v1 of this test passed cleanly and was wrong: forgeries could not have zero errors by
  construction, and genuines were drawn from the same rules the detector checked, so two of
  three measurements could only ever return a pass. Both artifacts are documented in the
  file.*
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
- **Test — RUN, 2026-08-06. `concepts-sim/commons.py`. Passes, but only in a narrow band, and
  the band is the finding.** Logistic fishery, six players, 24 periods, best-response solver.
  Four checks: no dominant strategy · mutual restraint beats mutual greed · unilateral
  restraint stings without being fatal · and a 72-point sweep asking whether *any* parameter
  region satisfies all three.

  **My guessed numbers failed.** At the parameters I'd have picked by instinct — efficient
  boats, cheap effort — fishing hard is the right answer against almost anything, keeping your
  word earns 15% of defecting, and the conversation is exactly the theatre the kill condition
  describes.

  **Only 4 of 72 parameter points work, and every one has low catchability.** The fishery is
  a game only when boats are *inefficient and expensive*. A fleet that can strip the stock in
  three periods has nothing to negotiate about — which is a design constraint with fiction
  already attached, and it is not a thing a playtest would have told you cheaply.

  At a viable setting: four distinct best responses across opponent profiles (no dominant
  strategy), restraint pays 1.24×, betrayal leaves you on 41% of the defector's take, and
  **the social optimum is moderate effort, not maximal restraint** — the right answer is "fish
  carefully," not "don't fish," which is a far better argument to have at a table.

  *Three of this file's own measurements were wrong before they were right: effort cost was
  specified three orders of magnitude too small to affect anything (making a sweep over it
  meaningless, and producing a confident "0/72, structural failure"), a sentinel counted
  "greed loses money" as a cooperative surplus, and the headline compared two negative
  payoffs and reported the best outcome on the board as a catastrophe. All three are
  documented in the file.*
- **Original test spec, retained:** solve the model before building anything around it. A
  dominant strategy found on day one saves a year. This is the only concept here whose kill
  test is a maths problem rather than a playtest.
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

### 47 · Reservation `NO COMBAT`
**You haggle in free text with a merchant who isn't allowed to know their own walk-away
price.**

*Reopened from graveyard entry 17 and rewritten. Searched before the card was written, per
the rule the rejection audit produced — and the search changed the design rather than just
clearing it.*

The merchant's reservation price is a number held by a solver. The language model never sees
it and never decides anything; it only renders the position it's handed. You probe, you offer,
you cite the competitor down the road, you threaten to walk. Ninety seconds: work out which of
this merchant's levers is real today, and spend it.

- **The bet: separate the *position* from the *voice*.** The model owns none of the outcome —
  it is the merchant's mouth, not their mind. That converts "can I trick the AI" into "can I
  find the lever," which is the entire difference between a jailbreak contest and a game.
- **Why this is back.** The original rejection said an LLM merchant is "either
  prompt-exploitable or arbitrary." A developer's write-up of exactly this — [*Game AI NPCs:
  Architecture, Not Better Prompts*](https://medium.com/@ashutosh_veriprajna/i-watched-a-playtester-talk-an-ai-merchant-out-of-a-quest-key-with-one-sentence-3b58e39bd1ef) — opens with a playtester talking an AI merchant out of a
  quest key **in one sentence**, and concludes: *"you cannot patch a jailbreak with a better
  prompt… the root cause is that the model was allowed to decide a game outcome at all."*
  So the rejection was right about every naive build and wrong about the concept. *Arsenic*
  independently shows the fix — a validating agent above the model — working in a shipped
  product. **The reopened bet is the architecture, which is precisely what the original card
  didn't have.**
- **Nearest:** *Suck Up!*, [*Whispers from the Star*](https://wfts.anuttacon.com/) (Steam, well reviewed), *1001 Nights*
  and *Wanderfolk* are all free-text persuasion of AI characters — and in all of them the
  model owns the outcome, which is the thing this card refuses to do. *Recettear* is the
  mechanical ancestor with no language in it: a hidden accept/reject curve you learn by
  probing. Research to read first: [NEGOTIATIONARENA](https://dl.acm.org/doi/10.5555/3692070.3692228) and [*Bounded Autonomy: Controlling LLM
  Characters in Live Multiplayer Games*](https://arxiv.org/html/2604.04703v1), which is this architecture written up properly.
- **Kills it — two ways, and they point in opposite directions.** (a) Players find a lever that
  *is* model-mediated after all, and one sentence moves the solver. It will be posted online
  within a day, because players are optimisers and this is the most efficient path if it
  exists at all. (b) The levers turn out to be enumerable: four of them, found in one session,
  after which the merchant is a vending machine with dialogue. **The band between exploitable
  and menu is the whole design**, and nothing about it is answerable from a design document.
- **Test:** no game. A chat window, one merchant, a reservation price in a spreadsheet, three
  legible levers, twenty people. Measure two things: **how many attempt a jailbreak, and
  whether that drops after the first failure** — if it doesn't, the architecture isn't reading
  as a rule and (a) is already true. Then check whether probers actually beat non-probers on
  price; if they don't, there's no skill in it. One day.
- **Scope:** 2 people, 7 months. **Per-session inference cost is a unit economic, not a line
  item** — same flag as Understudy (#34), and the two share enough architecture that building
  either one part-answers the other.

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

### ~~33 · Redaction~~ — **dead, verified 2026-08-06**
**You're a censor. Your only verb is blacking out text, and your deletions play out.**

> **Killed by [*De-File*](https://ibrahimexe.itch.io/de-file)** more than by the two comparables the card already named.
> *Blackbar* has you *guess* what's under the bars; De-File has you *place* them — "a rookie
> redactor… place redaction bars to guide its path, making sure it reaches the end without
> the truth getting exposed." That is "deletion as the input," which was the entire bet. Add
> *[REDACTED]* and *Orwell*. Graveyard entry 30.

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
- **Kills it — substantially de-risked, 2026-08-06, and this card was promoted as a result.**
  The stated kill was "the referee disagrees with itself on identical input." [*Arsenic*](https://playarsenic.com/) is
  a shipped counter-example: a Game Master agent validates every character response for
  consistency, and the reported behaviour is "consistent within their rules but creative in
  their delivery." That doesn't prove *this* referee will hold — grading in-character-ness is
  a harder judgement than flagging a factual contradiction — but it removes the assumption
  that it can't be done, which was the whole objection.
  **The remaining kill is now the *Façade* problem, alone:** players can't tell what the game
  wants from them, freeze, and blame themselves. Watch for the tester who stops talking.
- **Test:** no engine. A chat window, a scene, a character sheet, a grader prompt. Run the same
  line past it ten times and measure agreement. **One hour, pass/fail** — and read *Arsenic*'s
  [write-up of its own architecture](https://playarsenic.com/blog/how-ai-murder-mystery-games-work) first, which is free and will save most of the hour.
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

### ~~36 · Timetable~~ — **dead, verified 2026-08-06**
**A small rail network where the timetable is the program you write, and the trains execute
it.**

> **Killed by [*Rail Route*](https://railroute.eu/)'s Timetable Mode and [*Railroad Scheduler*](https://store.steampowered.com/app/2820250/Railroad_Scheduler/)**, the latter being
> "orchestrating all schedules and testing them as you go" with a rewind for failed runs —
> write-the-schedule-then-watch-it-execute, which was the bet. The card's own kill condition
> was "it's *Shenzhen I/O* with a worse theme"; the real answer is that the train version
> already exists twice. Graveyard entry 31.

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
- **Nearest — checked 2026-08-06; wounded.** "*Farming Simulator* does machinery, not agronomy"
  was wrong. The **FS25 mod scene** has [full N/P/K, pH and organic-matter tracking per field](https://github.com/Realistic-Farming/FS25_SoilFertilizer)
  with crop-specific depletion, weather effects and seasonal cycles, plus a crop-rotation mod
  where cover-crop choice changes next year's yield. The simulation exists and people play it
  voluntarily. What's still unoccupied is making it **the game** rather than a realism mod on
  a machinery sim — and the modders have already proven the audience is small but real.
  Still standing: *Stardew Valley* (soil as texture), *Terra Nil* (abstracted).
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
- **Nearest — checked 2026-08-06; wounded, and the check isn't finished.**
  [***Shelf by Shelf: Bookstore Simulator***](https://store.steampowered.com/app/3943720/Shelf_by_Shelf_Bookstore_Simulator/) (Steam, 2026) is a bookshop game whose whole
  loop is arranging books — "aesthetic yet strategically effective book arrangements" — and
  learning customer preferences. Whether *adjacency* drives sales, which is the actual bet, is
  not answerable from store copy or reviews. **This is the one card a search cannot settle:
  it needs the £-and-two-hours version of the test.** Buy it, play it, and see whether a
  theory about placement forms. If it does, this card is dead. Still standing: *Strange
  Horticulture*, *Unpacking*, *TCG Card Shop Simulator*.
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

**This family has since lost half its entries to verification** — #43 Recoil and #45 Sever are
both shipped games, and the two replacements generated to restore the quota died on the search
before they were written up. Four of six left, against a floor of six. Left breached
deliberately; the reasoning is in the ledger, and it is the strongest evidence in the document
that action is a genuinely harder space to find room in than the other eight families.

### 41 · Tell
**A duel where the enemy builds a model of your habits inside a single fight, and starts
punishing them at thirty seconds.**

Not run-to-run learning and not a scripted phase change — an online model of the last half
minute of your inputs, updating live.

- **The bet:** within-fight adaptation is *legible*. The player can feel themselves being
  read, name the habit that got punished, and change it — rather than experiencing it as
  rubber-banding.
- **Nearest — checked 2026-08-06; survives, with a better comparable than the card had.**
  ***Echo*** is the real nearest: enemies learn directly from your actions and use your own
  smart moves against you — it "punishes players for being good," which is this card's feeling
  exactly. It adapts between cycles rather than *within* one fight, and that gap is what's
  left of the bet. Also found: *Ghost Recon Wildlands*' adaptive AI, higher-tier fighting-game
  bots that parry your repeated attack types mid-match (the bet in miniature, undesigned), and
  a stack of NVIDIA AI-boss demos. Still standing: *Sekiro* (static), Nemesis (between
  encounters), Drivatars (offline-trained).
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

### ~~45 · Sever~~ — **dead, verified 2026-08-06**
**Melee with limb-level damage and no health bar. You win by disabling.**

> **Killed three times over.** *Bushido Blade 2* (1998) — no health bars, crippled limbs,
> one fatal blow — did this before I was looking. [*Gladio Mori*](https://bonusstagepublishing.itch.io/gladio-mori) goes further than the card
> did: no health bars, an *organ*-level model with muscles, arteries and vitals, muscle damage
> costing strength in that limb and artery cuts causing bleeding. *GUTS* is a third. The card
> called this "the most expensive concept in the document"; it was also the most occupied.
> Graveyard entry 32.

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
| 1 | **Provenance** (#16) | ~~One day~~ — **RUN. Kill condition not met** | Already spent. `concepts-sim/provenance.py`: 86% ceiling, 29% ambiguous, 7.8% of forgeries undetectable, and the optimal threshold *rises* with expertise. Still owes the fifty dossiers and a human |
| 2 | **Direct** (#46) | **One afternoon**, 2D, decisive in ten minutes | An afternoon. And a fail is genuinely informative: it tells you *why* indirect control keeps getting buried |
| 3 | **Understudy** (#34) | **One hour**, a chat window, ten repeated inputs | An hour — and *Arsenic* has already published how it built the same referee, so a fail is informative rather than just discouraging |
| 4 | **Party Line** (#1) | One evening, four friends, zero code | Nothing. Literally an evening |
| 5 | **Wake** (#24) | One evening, printed, zero engineering | An evening. And it ships as a paper game even if the digital version never happens |
| 6 | **The Commons** (#21) | ~~One day~~ — **RUN. Passes in a narrow band** | Already spent. `concepts-sim/commons.py`: my guessed parameters *failed*; only 4 of 72 work, all with low catchability. The fishery is a game only when boats are inefficient and expensive |
| 7 | **Foley** (#30) | One day, one clip, six sounds | A day — and the latency measurement across three machines is reusable for anything audio-timed |
| 8 | **Removals** (#6) | **Zero.** Estate Liquidators Phase 1 already runs it | Nothing. Free information from work you're doing anyway |

**How this table has moved, in order.** Worth keeping visible, because the movement is the
only evidence that the ranking is doing anything.

- **The action pass** put Direct (#46) and Recoil (#43) in on merit — an afternoon and a
  weekend, both decisive, both solo-shippable — and pushed out **Ledger** (#20) and **Pack**
  (#29). Ledger's removal was overdue on principle: it shares its kill condition with
  Provenance, so it was never an independent option and counting it as one overstated the
  portfolio. It's still worth building; it just isn't a separate *question*. Pack was
  straightforwardly outbid, and noted at the time as "the first thing back in if any of the
  above dies on contact."
- **The first verification pass** killed **Recoil** (#43) outright — *Kickback: Shoot to Move!*
  shipped in July 2025 with the same bet — and Pack came back in at #8, exactly as written.
  Direct survived its check and holds #2.
- **The full sweep** (all 45 cards) then killed **Tow** (#5) — *Orbital Salvager* shipped in
  March 2026 — and demoted **Sworn** (#6), whose bet turns out to be running in *Arsenic*.
  **Wake** (#24) and **Foley** (#30) took the slots: both clean after a real search, one
  evening and one day respectively.
- **The rejection audit** then promoted **Understudy** (#34) from runner-up to #3 — its kill
  condition rested on a prediction about LLM referees that *Arsenic* has since falsified — and
  pushed **Pack** (#29) back out. Pack has now entered and left this table twice.

**Pack's yo-yo is worth reading as a signal.** The top two haven't moved through three passes;
positions 6–8 have churned every time. That says the bottom of this ranking is carrying very
little information — several concepts sit within noise of each other on cost-to-disprove, and
the ordering between them is close to arbitrary. **Treat the top three as a recommendation and
the rest as a set.**

**Which is why #47 Reservation is not in the table.** Its test is one day, it's freshly
searched, and on the stated criterion it lands somewhere around 6th — indistinguishable from
Foley, The Commons, and the Pack/Removals cluster. Slotting it in would churn the same three
positions a fourth time and communicate a precision the criterion doesn't have. **It belongs
in the noise band with them, and saying so is more useful than picking an order.** If you want
a tiebreak between that group, the honest one isn't cost-to-disprove — it's which subject you
actually want to spend six months inside.

**What the sweep did to the table's credibility.** Two of the original eight were occupied
games. That is a 25% error rate in the section of the document that was supposed to be its
most considered, and it was 25% for exactly one reason: the ranking was built before the
search. **Resolve named suspicions with the cheapest instrument that can resolve them, before
ranking — not with the test the ranking happens to prefer.** Every card in this table has now
been searched, so the current eight is the first version of it that means anything.

**Sworn (#2) is the interesting demotion.** It didn't die — *Arsenic* proves the hard part
(automated consistency grading) is buildable, which raises the concept's feasibility while
gutting its novelty. Cheap test, and now a *known-achievable* mechanic, but the remaining
claim is much smaller than the card originally made. It sits just outside the eight and would
re-enter immediately if the human-liar framing survives an evening on paper.

**~~Runner-up, and the one worth arguing about: Understudy (#34).~~ Promoted to #3.** It was
held out on the grounds that a *pass* barely derisks it — referee consistency being necessary
and nowhere near sufficient. The rejection audit undercut that: *Arsenic* is a shipped
existence proof for the referee, so the objection has become "this part is known to work"
rather than "this part might be impossible." The remaining risk collapsed to one thing (the
*Façade* problem) instead of two, and its test is still the cheapest in the document at one
hour. Cheap test, and now a *meaningfully* narrowed question.

The per-session inference cost is still unpriced, and still decides whether this is sold once
or subscribed to. That's a business question, not a design one, and it doesn't belong in a
cost-to-disprove ranking — but do price it before designing anything.

**Runner-up now: Pack (#29)**, out for the second time. Three days, clean after search, and
outbid on both occasions by something cheaper. Its read-back finding is shared with Tell
(#41), so it stays useful even unbuilt.

**The action equivalent of that argument is Tell (#41).** Three days for the read-back, and a
pass proves only that adaptation is *legible* — not that being read is fun to play against.
Legibility is the necessary half and the cheap half. Highest ceiling in what's left of Family
9, weakest signal per day spent. Play *Echo* first; it's the nearest thing and it's cheap.

**If you only do one thing this Saturday:** Provenance's fifty text dossiers. It's a day, it
needs no engine, the artefact survives failure, and it also answers Ledger. **If you want to
do one thing this afternoon:** Direct's running dot. Ten minutes of play answers it, and the
answer is unambiguous in a way none of the systems concepts can be.

**And one thing that is neither:** buy *Shelf by Shelf* and play it for two hours. It's the
only open question in the document that no amount of searching will close, it costs less than
a prototype, and it decides whether #40 exists.

---

## The graveyard

Thirty-two entries, **thirty-one still dead** — entry 17 was reopened as card #47 after its
reason was audited, and the numbering is left intact so references resolve. This is the
section that should make you trust the other forty.

Entries 1–19 were cut by judgement during the first pass. Entries 20–25 came from the action
pass — action is the most crowded space in games, so a pass that produced six keepers and cut
nothing would be a pass that wasn't looking. **Entries 26–32 were killed by evidence rather
than opinion**, all of them published as keepers first, two of them ranked in the top eight.

That the last group exists at all is the document's most useful output. A graveyard filled
only by taste is a record of what one generator found unappealing; a graveyard filled by
search is a record of the market.

1. ~~**Chorus** — co-op where sung pitch is the network protocol. The accessibility floor is a
   wall, not a slope: a large minority genuinely cannot pitch-match, and there's no parallel
   path that isn't a different game.~~
   **Reason falsified 2026-08-06. Still dead, but not for that.** Pitch-as-control is a working
   shipped genre: [*One Hand Clapping*](https://store.steampowered.com/app/893720/One_Hand_Clapping/) (a vocal platformer on Steam), [*Pitch Pong*](https://flappysound.com/pitch-pong/) (1v1
   online, sung), *Pitch Bird*, *Vocaluxe* (six players). The accessibility objection I killed
   it with is contradicted by a market that supports several of these. It stays dead because
   it's **occupied**, which is a completely different finding — and the objection I used would
   have wrongly killed all four of those games too.
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
10. ~~**Deduction where the murderer is an LLM** — Understudy's referee-consistency problem
    (#34) without the theatrical framing that makes inconsistency forgivable.~~
    **Prediction falsified 2026-08-06, and this is the most consequential error in the
    document.** [*Arsenic*](https://playarsenic.com/) ships exactly this: AI suspects, a Game Master agent validating
    every response for consistency, contradictions surfaced across interrogations. Reported as
    working — "consistent within their rules but creative in their delivery." I killed this
    concept on a *guess* about LLM referees, and that guess also grounds graveyard entry 17
    **and the kill condition of live card #34**. It stays dead because Arsenic occupies it —
    but the reasoning that killed it was wrong, and it was doing work in three places. See
    the audit below.
11. **Plants that grow between sessions in real time** — the good half of this is #13 and #14.
    On its own it's a push notification.
12. **Racing where the track is drawn by the previous player** — *Trackmania* and the entire
    user-track genre.
13. **Audio-only maze** — tried repeatedly (*A Blind Legend*, *The Nightjar*). ~~The ceiling is
    well documented and it is low.~~ **Corrected:** both games are real and *A Blind Legend* is
    well regarded — reviewers say its binaural work "sets the bar very high." What's small is
    the **market** ("a few creative teams, free mobile games and five-dollar PC games"), not
    the design ceiling. I conflated the two. Dead on commercial grounds, not creative ones,
    which is a materially different reason to walk away.
14. **Multiplayer where you can't see your own character** — occupied by *Invisigun Heroes*,
    where everyone turns invisible and you give yourself away by touching the world. ~~Every
    playtest of this shape ends with players reading their position off a teammate.~~ **I made
    that up.** The reported dynamic is players repeatedly self-revealing to locate themselves,
    then having to move because they just announced where they were. Right verdict,
    invented evidence — flagged because invented evidence is worse than no evidence.
15. **A game where you play the building, not the people** — fails the picture-the-hands test
    on contact.
16. **Cozy crafting with a dark secret** — banned, arrived anyway on the second pass. That it
    keeps arriving is precisely why the ban is in the prompt.
17. ~~**Negotiating against LLM merchants**~~ — **reopened, searched, and rewritten as card
    #47 "Reservation."** The original reason ("prompt-exploitable or arbitrary") turns out to
    be *correct about every naive implementation* — a developer has published a playtest where
    an AI merchant was talked out of a quest key in one sentence — and *wrong about the
    concept*, because the fix is architectural: don't let the model own the outcome. Cut on a
    guess that happened to describe the bad version. **The only entry to leave this graveyard.**
18. **Physics game where you play the furniture** — funny for one screenshot.
19. **City builder where citizens write their own laws** — ~~the rigorous version is
    *Democracy*; the fun version is a chat log; **nobody has found the middle**, and I don't
    have a mechanism for it either.~~ **Flatly wrong, corrected 2026-08-06.** Two games found
    the middle: [*Lawmaker*](https://lawmakergame.com/) — found a party, *write the laws*, campaign to thousands of
    individually-modelled AI voters, with bills that must clear multiple legislatures — and
    *Polity*, where players are citizens, lawmakers and journalists in player-driven
    legislation. **I cut a concept for being unsolvable while two games were solving it.**
    Dead now because it's occupied, which is the opposite reason.

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

*Killed by verification rather than by judgement — the full sweep of 2026-08-06:*

26. **Recoil** (was #43) — *Kickback: Shoot to Move!* (Dot Blood / Targem, Steam, July 2025)
    ships the concept and the bet; *Recoil Rush* is a second commercial entry; itch.io has a
    `shoot-to-move` tag with a page of them. The only unoccupied version is 3D, which is a
    different concept with a different kill condition and should be written fresh rather than
    revived. **The first entry here killed by evidence instead of by opinion, and it took four
    minutes** — which is the argument for searching before ranking rather than after.
27. **The Quiet Part** (was #3) — *Cursed Companions* assigns each player a forbidden word per
    run and punishes the whole crew when anyone says it. Also has a monster for swearing. The
    concept, the bet, and a refinement I'd missed.
28. **Tow** (was #7) — *Orbital Salvager* (Steam, March 2026): 2D, tether-and-tow, orbital
    mechanics, scarce fuel. It is also the exact prototype the card proposed as its own kill
    test.
29. **Deep Clean** (was #9) — *Crime Scene Cleaner*, on top of *Viscera Cleanup Detail*, *Body
    of Evidence* and *Breach and Clean*. The card had already nominated itself for cutting.
30. **Redaction** (was #33) — *De-File* has you *place* the redaction bars to steer a reader
    away from the truth. That's "deletion as the input" exactly. *Blackbar*, *[REDACTED]* and
    *Orwell* fill in around it.
31. **Timetable** (was #36) — *Rail Route*'s Timetable Mode and *Railroad Scheduler* both ship
    write-the-schedule-then-watch-it-run, with a rewind for the crashes.
32. **Sever** (was #45) — *Bushido Blade 2* did no-health-bars limb crippling in 1998;
    *Gladio Mori* now models muscles, arteries and vitals; *GUTS* is a third. The most
    expensive concept in the document was also the most thoroughly occupied.

*Generated during the sweep to fill the breached action quota, and killed before being written
up as cards:*

- **Tempo** — a duel with no attack button; you block, parry and step until the opponent's
  stamina breaks. *Sword Instructor Gerald* already has blocking drain stamina to exhaustion;
  *Perfect Parry* is parry-only.
- **Standing Room** — your own attacks destroy the floor, so offence is the timer. *Decay
  Protocol*, *Unstaball*, and *The Finals* at scale.

Both were searched *before* a card was written, which is the order the whole document should
have used. Total cost: two searches.

---

## Auditing the rejections

The verification sweep checked the 46 things this document kept. It did not check the 25 it
**threw away** — and a rejection resting on a wrong memory discards a concept just as
permanently as a wrong keep wastes a month. Same defect class, mirror image, and the harder
one to notice: nothing downstream of a bad rejection ever complains.

Checked 2026-08-06. **No verdict reversed. Six reasons were wrong, and one of the wrong
reasons was doing work elsewhere in the document.**

| Entry | Verdict | The reason I gave | What's actually true |
|---|---|---|---|
| **1** Chorus | stands | "Accessibility floor is a wall — a large minority can't pitch-match" | *One Hand Clapping*, *Pitch Pong*, *Pitch Bird*, *Vocaluxe*. A working shipped genre. **Occupied, not inaccessible** — and my objection would have killed all four |
| **10** LLM murderer | stands | "The referee-consistency problem" | *Arsenic* ships it and it works. **Occupied. The prediction was wrong** |
| **13** Audio-only maze | stands | "The ceiling is documented and low" | *A Blind Legend* is well regarded; the **market** is small, not the ceiling. Two different reasons to walk away |
| **14** Can't see yourself | stands | "Every playtest ends with players reading position off a teammate" | *Invisigun Heroes*. The real dynamic is self-revealing to locate yourself. **I invented the evidence** |
| **17** LLM merchants | **reopened → #47** | "Prompt-exploitable or arbitrary" | True of every naive build, false of the concept. The fix is architectural. Now card #47 |
| **19** Citizens write laws | stands | "**Nobody has found the middle**" | *Lawmaker* and *Polity* both found it. **Cut as unsolvable while two games were solving it** |

Entries 5, 6, 9, 11, 12, 20, 21, 22, 23 checked out as stated — *Outer Wilds* and its cohort,
a large asymmetric-VR subgenre (*Panoptic*, *Mass Exodus*, *Keep Talking*), *Barotrauma*,
the whole offline-growth mobile category, *Trackmania*, *BPM* and *Metal: Hellsinger*,
*Receiver 2*, *I am the Final Boss*, *Shadow Fight*. The rest were cut on form rather than on
any claim about the world, so there was nothing to check.

### The finding that matters

**One unexamined prediction — "an LLM referee will be inconsistent or exploitable" — killed
two concepts and set the kill condition on a third.** It was never marked as a guess, it never
got a search, and *Arsenic* is shipped evidence against it. A belief that appears in three
places and is checked in none is exactly what `DECISIONS.md` exists to prevent, and this
document had no equivalent mechanism until now.

**So: a rejection needs the same falsification discipline as a keep.** The prompt now says so.
The practical rule is narrower and cheaper than auditing everything — **when the same reason
kills more than one concept, that reason is load-bearing and has to be checked once, properly.**
Reasons used once can stay cheap.

**And "I made that up" deserves its own line.** Entry 14 cited a playtest pattern that does not
exist. It reached the right verdict, which is worse than reaching the wrong one — a fabricated
justification that happens to land correctly is invisible, and the habit that produced it isn't.

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

**~~Almost every market claim is still memory.~~ Done — all 45 checked, and the rate is the
finding.** Seven died, four were wounded, thirty-five survived. **That is a 15% kill rate on
concepts I had written confidently enough to publish**, and 25% on the top eight specifically,
which is the part of the document that had received the most thought. The correlation runs the
wrong way from comfort: the more attention a concept got, the more likely it was to be a game
someone had already shipped — because attention and market obviousness are the same signal.

Three of the seven kills were on cards I had explicitly labelled as probably-occupied (#9,
#33, #43). **I had the information and ranked against it anyway.** Suspicion recorded on a
card does nothing; only the search does anything.

**So: assume taken until a search says otherwise.** The document was written on the opposite
prior and it cost seven concepts. The prompt now carries the corrected version, and that
correction is worth more than any card here.

**What the sweep cost: about ninety minutes.** Against seven concepts removed, two of them
from the top eight, and one — Tow — whose recommended weekend prototype was a game that had
been on Steam for five months. There is no other instrument in this document with that ratio.

**What a search still cannot do.** It can't settle #40 (does *Shelf by Shelf* model
adjacency?) — that needs two hours of play. It can't see jam builds and unlisted prototypes,
so SURVIVED means "not obviously taken," not "clear." And it can't tell you whether a
surviving concept is *good*; every kill condition on every card is still unrun. ~~**The
portfolio is now honestly scoped and entirely untested**~~ — **one test has now been run
(#16), and it is the first thing in this document backed by something that was executed
rather than argued.** Thirty-nine to go.

---

## Round log

One line per round: what was built, what it found. Where this log contradicts anything above,
**the log is newer** — same convention as `LOOP_LOG.md`.

**R1 · The forty.** Ran `GAMES-PROJECT-PROMPT.md` once. 40 concepts, 8 families, ranked top
eight, 19 rejections. Self-audit caught that nothing in it was fast.

**R2 · Family 9.** Added six action concepts. *Found:* the absence wasn't taste, it was the
scoring function — ranking by cost-to-disprove structurally suppresses bets about *feel*,
because feel has no paper version. Two entered the top eight.

**R3 · First verification.** Checked #43 and #46. *Found:* #43 was a shipped game
(*Kickback*), ranked #5, on a card that already said "probably occupied." Produced the
search-before-you-rank rule.

**R4 · Full sweep.** Checked all 46. *Found:* **seven were games that already exist**, two of
them in the top eight — a 15% kill rate overall and 25% inside the most-considered section.
Breached the action quota and left it breached; two replacement concepts were searched first
and both died before a card was written.

**R5 · Auditing the rejections.** Checked the 25 judgement-based cuts. *Found:* no verdict
reversed, **six reasons wrong**, and one unexamined belief about LLM referees that had killed
two concepts *and* was setting the kill condition on a live card. Promoted #34 from runner-up
to #3. One entry cited a playtest pattern I had invented.

**R6 · Reopening #17.** Rewrote it as #47 Reservation, searched first. *Found:* the search
**supplied the design** rather than just clearing it — the original rejection was accurate
about the naive build and wrong about the concept, and the fix is architectural. Declined to
add it to the top eight: it lands in the noise band with positions 6–8, and saying so beats
implying a precision the criterion doesn't have.

**R7 · Running a kill test.** Built and ran `concepts-sim/provenance.py` for #16. *Found:*
the kill condition is not met — 86% ceiling, 29% ambiguous, 7.8% of forgeries undetectable,
and the optimal threshold **rises with expertise**, which is an emergent mechanic I didn't
design in. *Also found:* v1 of my own test was tautological — forgeries couldn't have zero
errors, and genuines were drawn from the rules the detector checked — so two of three
measurements could only ever pass. Caught by the repo's "distrust clean results" rule, which
has now earned its place twice.

**R8 · Closing the verification drift.** Completed the ledger with a **per-card row for all
40 live cards** — what the search actually surfaced, not just a verdict — and deleted the
"where a card disagrees, the ledger is newer" clause, which was a fudge standing in for work.
Deliberately did *not* copy findings onto forty cards: that rebuilds the drift machine.
Cards carry the design argument, the ledger carries the evidence, six contradicted cards were
rewritten. *Found:* seven cards are `EMPTY` — a search returned nothing at all — which is a
much stronger claim than the "nobody's done this" they carried before.

**R9 · Running The Commons.** Built and ran `concepts-sim/commons.py`. *Found:* **the numbers
I'd have picked by instinct fail the concept's own kill condition.** Only 4 of 72 parameter
points work, all with low catchability — the fishery is a game only when boats are inefficient
and expensive. Also found that the social optimum is *moderate* effort, not maximal restraint,
which is a better argument to have at a table than the one the card imagined.

### The pattern across R7 and R9, which is now the thing to watch

**Four times in two rounds, my own instrumentation produced a confident wrong answer.**
Provenance v1 had two tautological measurements. Commons had a cost parameter three orders of
magnitude too small to matter (producing a decisive "0/72, structural failure"), a sentinel
that scored "greed loses money" as a cooperative surplus, and a headline that compared two
negative payoffs and reported the best outcome on the board as a catastrophe.

Every one was caught by the same reflex — `IMPROVE-PROMPT.md`'s **"distrust clean results"** —
and every one would have shipped a confident, wrong, *quotable* number. The failure rate of my
own tests is currently higher than the failure rate of the concepts they test. **Two sims in,
the instrumentation is the least reliable thing in this repo**, which is exactly what the
Estate Liquidators log said after its first three rounds. Assume the next sim is wrong until it
has survived an attempt to break it.

**R10 · Guarding the numbers.** Built `concepts-sim/check_numbers.py`, the equivalent of
`sim/check_drift.py`: it asserts **13 published figures** — every number cards #16 and #21
quote — plus the two *claims* underneath them, that the optimal threshold rises with expertise
and that all viable Commons points are low-catchability. **Deliberately taken out of ranked
order**, ahead of a third kill test, because the round above concluded the instrumentation is
the least reliable thing here and adding a fourth unguarded sim would compound that.

*Verified it can fail:* perturbing catchability 0.15 → 0.22 drops it to 11/13 and exits 1.
A guard that cannot fail is the same tautology this round kept catching, so it was checked
rather than assumed.

### Next, ranked

1. **A third kill test — #44 Ghosts.** Needs no new game (replay 50 recorded runs as hazards,
   measure path variance at day 1 vs day 7), it's `EMPTY` on search, and convergence is
   measurable rather than a matter of taste. Best evidence-per-hour left.
2. **Dedupe the prompt.** Five separate clauses now say some version of "search first." One
   should say it and the rest should point at it — `IMPROVE-PROMPT.md`'s "prefer deleting
   duplication to adding features," applied to the prompt itself.
3. **#47 Reservation's test needs a human**, and is the highest-value thing in the document
   that no amount of simulation reaches. Worth saying plainly rather than looping past it.

Left rough deliberately: #40 still needs two hours of playing *Shelf by Shelf*, which no
amount of looping substitutes for.
