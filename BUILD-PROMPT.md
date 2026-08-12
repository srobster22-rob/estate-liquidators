# The Build Prompt

Paste this to start a build session. It assumes nothing about the reader except access to
this repository.

Everything below the line is the prompt. Notes on how to use it are at the bottom.

---

## PROMPT

> You are building **Estate Liquidators**, a 4-player co-op horror extraction game, to ship
> on Steam. This repository contains a complete, simulation-verified design foundation and a
> playable single-player prototype. **Your job is the game, not the design.**
>
> ### Read first, in this order
>
> 1. `README.md` — the map.
> 2. `DECISIONS.md` — 28 settled calls, each with the condition that would disprove it.
>    **Do not relitigate these.** If you believe one is wrong, check whether its stated
>    falsification condition has actually been met; if it hasn't, implement it as written.
> 3. `DESIGN.md` — the game itself.
> 4. `TECH-SPEC.md` and `AUDIO-SPEC.md` — implementation detail for the two systems that
>    carry the product.
> 5. `LEVEL-SPEC.md`, `ECONOMY.md`, `STACK.md` — content contract, tuning, dependencies.
> 6. `LOOP_LOG.md` — twenty-eight rounds of findings, including several corrections to the specs.
>    Where the log contradicts a doc, **the log is newer**.
> 7. `proto/index.html` and `proto3d/index.html` — running single-player prototypes of the
>    core loop, top-down and first-person. Play them before writing anything.
>
> ### The stack is decided
>
> Unity 6 (URP) · FishNet for netcode · Steam P2P relay via Steamworks.NET or Facepunch ·
> Dissonance for positional voice · FMOD Studio for audio. Verified maintained and licensable
> as of 2026-07-29 (`STACK.md`).
>
> **Two hard constraints from that document.** The Dissonance↔FishNet bridge is
> community-maintained — **vendor it into this repo, do not depend on upstream.** And if voice
> is not working end-to-end within two days at Phase 0, **switch to Mirror**, which has an
> official integration. That contingency is pre-agreed; do not spend a week on it.
>
> ### Non-negotiables — these are simulation-verified, not opinions
>
> Each of these was wrong in an earlier draft and corrected by evidence. Reverting any of them
> reintroduces a specific, measured failure:
>
> - **Attention weighting is multiplicative, never additive** (`TECH-SPEC.md` §A3). Additive
>   constants let an empty-handed player be hunted 100% of the time over teammates carrying
>   loot, which breaks the game's second pillar.
> - **Aggro persists to the object, not the person** (`DESIGN.md` §6.1). Otherwise dropping is
>   a free two-second aggro reset.
> - **Hand-off re-targets instantly, bypassing hysteresis** (`TECH-SPEC.md` §A3). Measured at
>   0.0s with the override, 6.0s without.
> - **Carried items stay non-kinematic** (`TECH-SPEC.md` §B0). The safe implementation deletes
>   the comedy that is the product.
> - **Disturbance is a fast-decaying noise level plus a ratcheting floor**, not an accumulator
>   (`DESIGN.md` §6.5). And **decay scales with crew size** — the 50/min figure is calibrated
>   for four players (`LOOP_LOG.md` R12).
> - **Depth unlocks on work, never on a timer** (`DECISIONS.md` D-20). Clock gating silently
>   punishes larger crews.
> - **Full friendly-fire physics, zero friendly-fire damage** (`TECH-SPEC.md` §B6).
> - **Cursed cargo is a tail risk, not a fee** (`DESIGN.md` §4.2). A linear cost cannot balance
>   a multiplicative benefit; it produces a fake decision.
>
> ### Phases — each has an exit criterion. Do not start the next until it is met.
>
> **Phase 0 — Prove the risk.** Two clients in a grey box over Steam P2P, spatial proximity
> voice, and one door that occludes it.
> *Exit:* two people in different rooms sound different, over the internet, not LAN.
>
> **Phase 1 — The physics handoff.** Networked non-kinematic pickup/carry/drop with ownership
> transfer; then two-man carry via the anchor/follower model in `TECH-SPEC.md` §B4.
> *Exit:* two players carry a piano through a doorway at 120ms simulated latency without it
> jittering, duplicating, or achieving orbit. **Test at real latency, not LAN — LAN will lie.**
>
> **Phase 2 — The loop, instrumented.** One estate wing, ~20 items, appraiser, van, quota,
> sunrise timer, ledger. No monster.
> *Exit, and there are two:* (a) four real friends on voice find hauling junk to a van funny
> *without* a monster; (b) scan rate stays above ~30% at hour five (`DESIGN.md` §4.4). **If
> either fails, stop and rework — do not proceed to Phase 3.** This is the honest checkpoint;
> everything after it is expensive.
>
> **Phase 3 — The Curator.** State machine, multiplicative attention, plinth-intercept
> pathing, FIXATE, retrieval-then-death, and the frost/dimming-light aggro tell. **Build the
> aggro *display* before the aggro *logic*** — a readable indicator on a dumb monster is
> testable and fun; a brilliant monster nobody can read is a week of debugging bored testers.
>
> **Phase 4 — Systems.** Disturbance escalation and its three levers, curse grades and the
> tail-risk van cost, lights and breakers, corpse recovery and the ghost's Static budget.
>
> **Phase 5 — Content.** 5+ wing modules against the `LEVEL-SPEC.md` contract, with the
> ten-check validator wired into CI. Port `sim/validate_estate.py` to a Unity editor tool; a
> wing that fails any check does not enter the pool. **Automate V10 (does the piano physically
> fit through every route) before the first wing ships**, not after the first bug report.
>
> **Phase 6 — Ship.** See the Steam section below.
>
> ### Reuse the simulations
>
> `sim/` contains five Python models plus the estate validator and the drift/mutation
> tooling — ~2,400 lines that already answer most tuning questions, and they run in seconds
> with no dependencies. **Before changing any balance number, re-run the relevant one.** They
> are the reason the current values are trustworthy, and two of them exist specifically
> because earlier numbers were wrong.
>
> `python3 check.py` runs everything at once and prints SKIP, loudly, for anything the
> machine cannot run.
>
> Port `validate_estate.py` to C# for Phase 5. Leave the rest in Python as design tools.
>
> ### Steam — the part no design document covers
>
> Work these in parallel with Phase 4 onward; several have lead times measured in weeks.
>
> **Account and legal** *(the human owner must do these — they require identity, banking, and
> a signature; an agent cannot and should not)*: Steamworks Partner account, $100 app deposit
> per title (recoverable after $1,000 adjusted gross revenue), tax interview (W-9/W-8BEN),
> bank verification, and the 30-day mandatory wait between paying the fee and release date.
>
> **App setup:** claim the App ID, configure depots (Windows x64 first; Linux/Proton later),
> set launch options, and wire `SteamAPI_Init` early enough that P2P and lobbies work in
> development builds.
>
> **Store page:** capsule art at every required size, 5+ screenshots, a trailer, short and
> long descriptions, system requirements, tags. **The store page must be live and reviewed
> before release** — budget 2–5 business days for Valve's review, and expect at least one
> rejection round on capsule art or descriptions.
>
> **Content survey and ratings:** this game is horror with a monster; complete the content
> survey honestly. If targeting Germany or Brazil, factor in regional rating requirements.
>
> **Build pipeline:** `steamcmd` with depot scripts checked into this repo, plus branches for
> `default`, `beta`, and `internal`. Automate uploads; manual builds produce shipping
> mistakes.
>
> **Multiplayer specifics that catch people:** Steam P2P relay needs the app to be released or
> the tester on a Playtest/beta branch to connect; lobbies need the App ID configured; and
> **friends-join-via-overlay must be tested from a non-developer account.** Test with someone
> who has never had the project directory on their machine.
>
> **Strongly recommended before release:** ship a **Steam Playtest** (free, gated, no store
> commitment) once Phase 3 is stable. This genre lives or dies on whether groups of friends
> find it funny, and that cannot be measured any other way. A demo during a Next Fest is the
> other high-leverage option.
>
> ### How to work
>
> - Verify, don't assert. Every claim about the game working should be backed by something
>   you ran. This project has a history of confident numbers that turned out to be
>   instrumentation bugs — three were found in the first hour of building the prototype.
> - Log non-obvious decisions into `DECISIONS.md` with what would disprove them.
> - Append findings to `LOOP_LOG.md`, one line per unit of work.
> - Where a spec and reality disagree, fix the spec too. Stale docs are worse than none.
> - **Never commit to the repository at `C:\Users\srobs`** — it is shared across sessions.
>   This project directory is fine to version separately.
>
> ### The honest scope
>
> Phases 0–2 is 2–4 months and tells you whether the game is worth making. Phases 0–6 to a
> shippable Steam release is **9–18 months for a small team**, longer if netcode is new to
> you. Commit to Phase 2 and re-decide there.

---

## Notes on using this

**What this prompt is for.** Starting a build session with a coding agent, briefing a
collaborator, or re-orienting yourself after time away. It is deliberately self-contained —
it assumes the reader has not seen any of the prior conversation.

**What it can't do.** It won't produce a Steam game in one session. The scope section is
honest and the phases are ordered by risk, not by what's fun to build first. The single most
common failure mode for this genre is building content before proving that four friends
hauling furniture is funny — which is why Phase 2 has a hard stop in it.

**The parts only you can do.** Partner account, the $100 deposit, tax interview, bank
verification, and signing the distribution agreement all require your identity and payment
details. Don't delegate those to an agent, and be wary of any tool that offers to handle
them.

**Where to weaken it.** If you're building solo and slowly, cut Phase 5 to two wings and ship
a Playtest earlier. Content is the most compressible part; the Phase 2 gate is not.
