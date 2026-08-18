# What exists, and what doesn't

The design documents describe the whole game. The prototype implements part of it. Nothing
below is a plan — it's a statement of what you can run today, updated whenever that changes.

**Run it:** open `proto3d/index.html`. Controls are on the start screen and behind `H`.
`?seed=12345` reproduces a specific house.

```bash
node proto3d/qa.mjs               # 198 checks, the real build in headless Chromium
python3 sim/check_counts.py --qa 198   # the numbers in these docs are the real ones
python3 sim/check_drift.py        # 177 constants agree across four implementations
python3 sim/check_claims.py       # 25 documented conclusions, re-derived from the sims
python3 sim/netcode.py            # what B1-B4 promise, on a clock with a delay in it
python3 sim/validate_estate.py    # 10 checks x 2 sample estates
node proto3d/dump-estate.mjs --seeds 24 --out /tmp/e && \
  python3 sim/validate_estate.py --estate /tmp/e/*.json   # 10 checks x 24, all four nights
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
| The apex | `ECONOMY` §3, D-21 | Late contracts only; 32–64% of the final quota; dolly-only. |
| Fragility and breakage | `DESIGN` §5 | Break chance by fragility × speed at release. |
| Corpse recovery | `DESIGN` §5 | A body is a two-man object that pays nothing and costs three slots. |
| Contract chain | `ECONOMY` §4 | Four nights, van 14→19, quotas measured for this build's shorter night. |
| Generated estates, gated | `LEVEL-SPEC` | Rejected until the contract passes, on every night of the chain; richer, deeper houses later in it. |
| Audio | `AUDIO-SPEC` §1, §A6.2 | Synthesised. The drag layer is never occluded to zero inside 8m. |
| Lights and the breaker | `DESIGN` §6.5 | Lighting a wing is silent and +25; the breaker at the van is −15 and takes them all. |
| The dolly | `DESIGN` §8 | Cart-class pieces cannot be picked up at all. Slow, L35 while rolling, and it tips if you sprint with it. |
| Salt line | `DESIGN` §8 | One charge, 20s, laid in a doorway. Buys a detour, not denial — see the note below. |
| The crowbar and the boarded wing | `DESIGN` §6.4, §8 | Every door into the deepest wing is boarded. The crowbar is somewhere shallow, takes both hands, and prying is L75 — the loudest thing in the game. The crew work around it; the Curator ignores it. |
| All three Disturbance levers | `DESIGN` §6.5 | Kill the lights, go quiet (window scaled to this build's night), unload cursed cargo into the yard. |
| What a curse costs to carry | `DESIGN` §4.2 | Tainted takes your torch away and adds Disturbance faster than the crew can decay it; malignant gains mass over 20s and speaks in a crewmate's voice, which the Curator hears. All of it ends the frame you put the piece down. |
| The torch as a verb | `DESIGN` §4.2, `TECH-SPEC` §A3 | Dark is a lighter mark and nearly blind. A cursed piece takes the choice away. |
| The voice ladder | `AUDIO-SPEC` §2 | Whisper 8, raised 45, shout 65, on the same hearing model as everything else: a whisper cannot cross the room you are in, a raised voice stops at the doorway, only a shout is heard next door — and the Curator is listening on the same channel. It is how you ask for the other end of an armoire. |
| Death as a role change | `DESIGN` §5.1 | 10s collection beat, then free movement, permanent sight of the Curator, curse-sight at 5m, and a Static budget. |
| Doors as entities | `DESIGN` §5.1 | Open until something shuts one; walking into a shut door costs 1.4s and a door's worth of noise. |
| All five Static verbs | `DESIGN` §5.1 | Knock 1, Flicker 1, Nudge 3, Slam 2, Hold 5 — against a cap of 6, so slam-then-hold does not fit in one budget. |

## Specified, not built

| System | Spec | Why not yet |
|---|---|---|
| **Multiplayer** | all of it | The prototype is one player and three haul bots. This is still the largest gap by far — but the *arithmetic* of it no longer is. `sim/netcode.py` puts `TECH-SPEC` B1–B4 on a clock with a delay in it: the hot potato survives (0.13s of wrong target at 120ms, against 2.5s to be caught), the pickup race only flips in a photo finish, the pry disagrees with the victim's own screen 3.6% of the time, and the two-man drift tolerance is entirely spent on latency before the physics gets any of it. What needs four people is the *feel*. |
| **Proximity voice** | `AUDIO-SPEC` §2 | Needs two clients. Phase 0's exit criterion. The *ladder* is built and on the same attenuation model — what is missing is a second mouth. |
| A body left behind costing you a hauler | `DESIGN` §5 | Works for crew. A single-player prototype has no way to be short a *player*, so your own body is an attention magnet and nothing else. |
| Radio | `DESIGN` §8 | The last tool. It is a communication device in a game with one player, so it needs the multiplayer layer to mean anything. |
| The van's interior light as a cursed-cargo gauge | `DESIGN` §4.2 | The floor rises per cursed piece, but the van does not visibly dim — the glanceable readout is still a UI number. |
| Unity / Steam | `BUILD-PROMPT` | The C# core exists and is pinned to the sims; there is no Unity project. |

## Known limits of the checks

- **Nobody has played this.** 198 headless checks say the rules behave. None of them says it
  is fun, and the Phase 2 gate in `DESIGN` §11 is the only thing that can.
- **The audio checks assert the mixing rule, not sound.** Headless Chromium has no audio
  clock, so the graph's gain values stay at zero however correct the mix is.
- **The C# suite has not run since R14** — no .NET SDK in the container this loop runs in.
  `check_drift.py` is currently the only thing holding the C# port to the canonical numbers.
- **The salt line cannot deny a route.** V3 requires every wing to survive losing any one
  portal, so a house that passes the level contract always has a way round. Salting a doorway
  costs the Curator a detour. That is the same V3/V4 tension R1 found and it is not a bug in
  either — but a tool sold as "it won't cross" behaves as "it goes the long way".
- **The sims agree with the documents, and two of them can't see much.**
  `check_claims.py` re-derives all 25 conclusions the design documents quote. Two of those
  claims are about the models' own blind spots and were written after injections walked
  through them untouched: halving the labour cost of a two-man piece moves the chain by 2%
  (trips bind a night, not people), and zeroing the curse fees entirely leaves the optimum
  where it was (a linear cost cannot move a multiplicative decision — which is exactly the
  argument for D-11's ruin tail). Beyond the first lit wing, `disturbance.py` saturates and
  has nothing to say at all.
- **The van never fills, so two of the design's levers are inert here.** Measured at dawn
  over 96 nights: the van still has 4–7.5 free slots and **88–95% of the house's value is
  still on its shelves**. Time binds this build, not capacity and not what is in the house —
  and it binds *harder* on the later nights, where the van is bigger. So the 14→19 upgrade
  curve and "richer estates later in the chain" are both decoration in the playable build,
  and no conclusion about capacity can be drawn from it; `sim/chain_sim.py`'s 720-second
  night is the only place that question can be asked. `qa.mjs` asserts this rather than
  leaving it to be rediscovered.
- **Statistical checks are coarse.** Pass-rate assertions run 12 nights and make shape claims
  ("harder than night one"), not rate claims; twelve runs cannot pin a rate to ten points.
