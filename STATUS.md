# What exists, and what doesn't

The design documents describe the whole game. The prototype implements part of it. Nothing
below is a plan — it's a statement of what you can run today, updated whenever that changes.

**Run it:** open `proto3d/index.html`. `?seed=12345` reproduces a specific house.

```bash
node proto3d/qa.mjs               # 154 checks, the real build in headless Chromium
python3 sim/check_counts.py --qa 154   # the numbers in these docs are the real ones
python3 sim/check_drift.py        # 144 constants agree across four implementations
python3 sim/validate_estate.py    # 10 checks x 2 sample estates
node proto3d/dump-estate.mjs --seeds 12 --out /tmp/e && \
  python3 sim/validate_estate.py --estate /tmp/e/*.json
dotnet run --project unity/tests/CoreTests   # 31 assertions — needs a .NET SDK
```

---

## Implemented and checked

| System | Spec | Notes |
|---|---|---|
| Loudness → Disturbance | `AUDIO-SPEC` §1 | One number, three consumers. Impulse and sustained separated. |
| Disturbance tiers + ratcheting floor | `DESIGN` §6.5 | Decay scales with crew size (R12). |
| Attention, multiplicative | `TECH-SPEC` §A3 | Over **items**, not players — see D-25. Steal threshold and commitment both active. |
| Aggro binds to the object | `DESIGN` §6.1, D-06 | Dropping moves the mark off you without calling off the hunt. |
| Plinth-intercept pathing | `TECH-SPEC` §A4 | Plus a real route over the room graph (R24). |
| Retrieval, then death | `DESIGN` §6.3 | First contact takes the piece; second is fatal. |
| Curator senses | `TECH-SPEC` §A5 | Hearing `L × 0.33`, 0.85 per wall, ±3m fuzz; sight 18m/100° blocked by walls. |
| Crew hunt at COLLECT | `DESIGN` §6.5 | Where concealment becomes the primary verb. |
| Concealment and stashing | `DESIGN` §8.1 | Hide, stash for 20s, and the four seconds it takes to open the door on you. |
| Appraiser, per candidate | `DESIGN` §4.4, D-24 | Shelves of four; the UI shows how much of one you have paid to look at. |
| Curse grades, fees, ruin tail | `DESIGN` §4.2, D-11 | Ruin rises as `0.015 × cursed^1.8`. |
| Weight classes and slots | `ECONOMY` §1 | Van priced in slots: armful 1, two-man 3, cart 5. |
| Two-man carry | `TECH-SPEC` §B4 | Anchor/follower, single-machine. |
| The apex | `ECONOMY` §3, D-21 | Late contracts only; 32–64% of the final quota. |
| Fragility and breakage | `DESIGN` §5 | Break chance by fragility × speed at release. |
| Corpse recovery | `DESIGN` §5 | A body is a two-man object that pays nothing and costs three slots. |
| Contract chain | `ECONOMY` §4 | Four nights, van 14→19, quotas measured for this build's shorter night. |
| Generated estates, gated | `LEVEL-SPEC` | Rejected until the contract passes; richer houses later in the chain. |
| Audio | `AUDIO-SPEC` §1, §A6.2 | Synthesised. The drag layer is never occluded to zero inside 8m. |
| Lights and the breaker | `DESIGN` §6.5 | Lighting a wing is silent and +25; the breaker at the van is −15 and takes them all. |
| Salt line | `DESIGN` §8 | One charge, 20s, laid in a doorway. Buys a detour, not denial — see the note below. |
| All three Disturbance levers | `DESIGN` §6.5 | Kill the lights, go quiet (window scaled to this build's night), unload cursed cargo into the yard. |
| Death as a role change | `DESIGN` §5.1 | 10s collection beat, then free movement, permanent sight of the Curator, curse-sight at 5m, and a Static budget. Knock and Nudge only. |

## Specified, not built

| System | Spec | Why not yet |
|---|---|---|
| **Multiplayer** | all of it | The prototype is one player and three haul bots. The hot potato, proximity voice, the physics handoff at 120ms and the whole social layer are unproven. This is the largest gap by far. |
| **Proximity voice** | `AUDIO-SPEC` §2 | Needs two clients. Phase 0's exit criterion. |
| The dolly | `DESIGN` §8 | Cart-class pieces are carried by two at a crawl instead. Flagged where it happens. |
| Flicker / Slam / Hold | `DESIGN` §5.1 | The other three Static verbs need a lights system and door entities; neither exists. |
| A body left behind costing you a hauler | `DESIGN` §5 | Works for crew. A single-player prototype has no way to be short a *player*, so your own body is an attention magnet and nothing else. |
| Radio, crowbar, dolly | `DESIGN` §8 | No other tools. The appraiser, the flashlight, the salt line and the breaker are built. |
| Curses beyond value and ruin | `DESIGN` §4.2 | Grades affect price, attention and the ruin roll; no per-curse behaviour. |
| Unity / Steam | `BUILD-PROMPT` | The C# core exists and is pinned to the sims; there is no Unity project. |

## Known limits of the checks

- **Nobody has played this.** 154 headless checks say the rules behave. None of them says it
  is fun, and the Phase 2 gate in `DESIGN` §11 is the only thing that can.
- **The audio checks assert the mixing rule, not sound.** Headless Chromium has no audio
  clock, so the graph's gain values stay at zero however correct the mix is.
- **The C# suite has not run since R14** — no .NET SDK in the container this loop runs in.
  `check_drift.py` is currently the only thing holding the C# port to the canonical numbers.
- **The salt line cannot deny a route.** V3 requires every wing to survive losing any one
  portal, so a house that passes the level contract always has a way round. Salting a doorway
  costs the Curator a detour. That is the same V3/V4 tension R1 found and it is not a bug in
  either — but a tool sold as "it won't cross" behaves as "it goes the long way".
- **Statistical checks are coarse.** Pass-rate assertions run 12 nights and make shape claims
  ("harder than night one"), not rate claims; twelve runs cannot pin a rate to ten points.
