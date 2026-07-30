# Stack Verification

Checked 2026-07-29. Every previous document named these packages from general ecosystem
knowledge with an explicit "verify before committing" warning. This is that verification.

**Headline: the stack holds, with one real problem.** The Dissonance↔FishNet bridge is
community-maintained, not official — and it's the single point where this project's netcode
and voice choices meet.

---

## Results

| Package | Status | Finding |
|---|---|---|
| **FishNet** | ✅ **Verified good** | Actively developed. 4.7.2R released 2026-04-20. Explicitly supports Unity 6, with recent commits fixing Unity 6-specific multithreading issues in its object caches — that's the signature of someone actually using it on Unity 6, not just claiming compatibility. |
| **Dissonance Voice Chat** | ✅ **Verified good** | Actively maintained by Placeholder Software. Core asset updated 2026-04-27. Opus encoding, chat rooms, VAD/PTT — everything `AUDIO-SPEC.md` §2 assumes. |
| **Dissonance ↔ FishNet** | ⚠️ **Community-maintained** | See below. This is the risk. |
| **FMOD Studio** | ✅ **Verified good** | Free indie tier: budget under $500K USD and under $200K/yr gross revenue, no revenue share. Comfortably covers this project. Commercial licensing starts ~$5K if it ever grows past that. |
| **FMOD + Dissonance + FishNet together** | ✅ **Precedent found** | Third-party tutorials exist covering exactly this three-way combination for dynamic voice manipulation. `AUDIO-SPEC.md` §7.1 flagged "prove this combination works before it's in the critical path" as a week-eating unknown — someone has already proven it. |

**FMOD on Unity 6 specifically** was not directly confirmed in what I found. FMOD is a
first-tier Unity integration and this is very likely fine, but confirm against FMOD's own
compatibility docs before Milestone 0 rather than taking my inference for it.

---

## The problem: the voice bridge is unofficial

Dissonance ships **official** integrations for Mirror, Netcode for GameObjects, and Photon
Fusion. It does **not** ship one for FishNet. The FishNet bridge is a community project on
GitHub, and the copy that surfaces most prominently is a *backup* fork of the original
author's repository — which is exactly the fingerprint of a project whose maintainer has
moved on.

This matters more than a typical dependency risk, because it sits precisely at the junction
of the two systems this game cannot exist without: networked physics and proximity voice.

### The call: stay on FishNet, and vendor the bridge

**Reasoning:**

- FishNet's ownership and authority-transfer model is the better fit for the hardest problem
  in the project — the physics handoff in `TECH-SPEC.md` §B1–B4. That advantage is real and
  it applies constantly. The bridge risk is one-time and bounded.
- **The bridge is a thin transport shim.** Its whole job is moving opaque byte arrays between
  Dissonance and the network layer. It is not deep, clever, or large. If upstream dies, it
  can be maintained in-house for a cost measured in days, not months.
- **Vendoring neutralises most of the risk.** Fork it into this repository at Milestone 0
  rather than depending on upstream. An unmaintained dependency you control is just source
  code; an unmaintained dependency you fetch is a liability.

**The contingency, pre-agreed so it isn't relitigated under pressure:** if the bridge is not
working end-to-end within **two days** at Milestone 0, switch to **Mirror**, which has an
official Dissonance integration and comparable authority-transfer support. Losing FishNet's
prediction model is a real cost and it is smaller than losing two weeks to a transport shim.

**Do not switch to Netcode for GameObjects** for this project. It has the official
integration, but its physics story is the weakest of the three, and physics is the entire
game.

---

## What changed as a result

- `DECISIONS.md` **D-01** updated: stack verified, with the bridge risk and contingency
  recorded.
- New **D-16**: vendor the voice bridge.
- `TECH-SPEC.md` §10.1 and `AUDIO-SPEC.md` §7.1 "verify before committing" warnings replaced
  with these findings.
- `AUDIO-SPEC.md` §7.1's "prove this combination works in a throwaway scene" concern is
  **downgraded but not removed** — precedent existing is not the same as it working on your
  machine, on your Unity version, in a day.

---

## Sources

- [FishNet releases](https://github.com/FirstGearGames/FishNet/releases) · [FishNet docs](https://fish-networking.gitbook.io/docs) · [Asset Integrations](https://fish-networking.gitbook.io/docs/overview/asset-integrations)
- [Dissonance Voice Chat](https://assetstore.unity.com/packages/tools/audio/dissonance-voice-chat-70078) · [Choosing A Network](https://placeholder-software.co.uk/dissonance/docs/Basics/Choosing-A-Network.html) · [Dissonance GitHub](https://github.com/Placeholder-Software/Dissonance)
- [DissonanceVoiceForFishNet](https://github.com/LambdaTheDev/DissonanceVoiceForFishNet)
- [Dissonance + FMOD + FishNet walkthrough](https://kitemetric.com/blogs/dynamic-voice-manipulation-in-unity-using-dissonance-fmod-and-fishnet)
- [FMOD indie licensing](https://gamefromscratch.com/fmod-studio-now-free-for-indie-game-developers/)
