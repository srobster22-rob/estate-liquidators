# The Build Prompt

Paste this to start a build session. It assumes nothing about the reader except access to
this repository.

Everything below the line is the prompt. Notes on how to use it are at the bottom.

---

## PROMPT

> You are building **Estate Liquidators**, a 4-player co-op horror extraction game, to ship
> on Steam. This repository contains a complete, simulation-verified design foundation, two
> playable single-player browser prototypes, and a C# core of the verified rules pinned by 31
> passing assertions, with `tuning.json` as the canonical source of the tuning constants and a
> fail-closed drift check over it. **Your job is the game, not the design.**
>
> ### Read first, in this order
>
> 1. `README.md` — the map.
> 2. `DECISIONS.md` — 23 settled calls, each with the condition that would disprove it.
>    **Do not relitigate these.** If you believe one is wrong, check whether its stated
>    falsification condition has actually been met; if it hasn't, implement it as written.
> 3. `DESIGN.md` — the game itself.
> 4. `TECH-SPEC.md` and `AUDIO-SPEC.md` — implementation detail for the two systems that
>    carry the product.
> 5. `LEVEL-SPEC.md`, `ECONOMY.md`, `ART-DIRECTION.md`, `STACK.md` — content contract, tuning,
>    the look, dependencies. `tuning.json` at the repo root is the canonical copy of the 59
>    constants the sims, the prototype, and the C# core all share; `sim/check_drift.py` runs
>    106 fail-closed checks asserting all three agree with it. Change a shared number there
>    and re-run the checker. If a spec and `tuning.json` disagree, nothing guards that — it is
>    a bug, and you fix both.
> 6. `LOOP_LOG.md` — sixteen rounds of findings, including several corrections to the specs.
>    Where the log contradicts a doc, **the log is newer**.
> 7. `proto/index.html` and `proto3d/index.html` — two running single-player prototypes of the
>    core loop. `proto/` is the top-down one, and is the JS implementation that
>    `sim/check_drift.py` checks against `tuning.json`; `proto3d/` is first-person, matching the
>    direction correction in `LOOP_LOG.md` R15, and is not covered by the drift checker. Play
>    both before writing anything. Then read the C# core in `unity/Assets/Scripts/Core/` and run
>    `dotnet run --project unity/tests/CoreTests` — 41 assertions, all passing, and every
>    one of them proven able to FAIL by `sim/check_core.py` (R19).
> 8. `TRANSFER.md` — which machine does what. Unity cannot cross-compile a Windows IL2CPP
>    player from macOS, so iterate on the Mac and produce the shipping Steam build on the PC.
>    Read before planning Phase 2 or Phase 6.
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
> *without* a monster; (b) scan rate stays above **~30%** at hour five (`DESIGN.md` §4.4). That
> number is the designer's, not a simulation's: R20 lowered it to 15% on a measured optimum,
> R23 found the optimum was an artifact of clock-gated depth and reversed it. **No scan-rate
> threshold here is simulation-backed** — the Milestone 2 telemetry is what settles it. **If
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
> wing that fails any check does not enter the pool. **Port `sim/check_estates.py` with it** —
> it mutates a known-good wing one fault at a time and asserts every check can actually fail.
> R18 added it and immediately found V7 could not fail at all, so the C# port needs the same
> guard or it will inherit a check that only prints PASS. **Automate V10 (does the piano physically
> fit through every route) before the first wing ships**, not after the first bug report.
>
> **Phase 6 — Ship.** See the Steam section below.
>
> ### Reuse the simulations
>
> `sim/` contains eight Python models totalling ~1,740 lines that already answer most tuning
> questions, and they run in seconds with no dependencies. `tuning.json` at the repo root is the
> canonical value for every constant, and `sim/check_drift.py` asserts that the Python, both JS
> prototypes and the C# core all agree with it — 133 checks over 59/59 constants across all four
> implementations, fail-closed since R16 (unmatched patterns fail rather than skip) and
> per-implementation since R17 (a constant an implementation carries must be checked *there*). **Before changing any balance number, change it in
> `tuning.json`, re-run the relevant model, then re-run `python3 sim/check_drift.py`.** The models
> are the reason the current values are trustworthy, and two of them exist specifically because
> earlier numbers were wrong.
>
> The verified rules are **already ported to C#** in `unity/Assets/Scripts/Core/` — Loudness,
> multiplicative Attention plus the hysteresis selector, Disturbance, and the van/curse economy —
> written free of `UnityEngine` so they compile and test outside the editor. `unity/tests/CoreTests`
> pins them against the Python simulations' numbers: **41 assertions, all passing**, via
> `dotnet run --project unity/tests/CoreTests`. `sim/check_core.py` then breaks the core one
> rule at a time and requires something to notice — it found eight rules that nothing was
> guarding, including the multiplicative-attention non-negotiable below (R19).
>
> **Three of the eight non-negotiables cannot be guarded by anything in this repo yet**, because
> they are Unity behaviour: aggro persisting to the object, carried items staying non-kinematic,
> and zero friendly-fire damage. They are the likeliest to be lost during Phases 1 and 3. Write
> a test for each as you build it, and add it to `sim/check_core.py`'s NON_NEGOTIABLES map. Build Phases 3–4 on that core rather than
> re-deriving it. After changing any constant, re-run `python3 sim/check_drift.py`, which holds
> `tuning.json` (canonical), the C# core, and both JS prototypes in agreement — 133 checks over 59
> canonical constants across four implementations, fail-closed. Still to port: `sim/validate_estate.py` to a C# editor tool for
> Phase 5. Leave the remaining models in Python as design tools.
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
> - **This project is now its own git repo with its own remote — commit here freely.** The old
>   warning about never committing to `C:\Users\srobs` described the Windows PC, where this
>   folder sat inside a shared parent repo. Day-to-day work now happens on the Mac
>   (`TRANSFER.md`); the PC is kept for the shipping Windows IL2CPP build, which cannot be
>   cross-compiled from macOS, and as a second client for real-latency netcode tests.
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
