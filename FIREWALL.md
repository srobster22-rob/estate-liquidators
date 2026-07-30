# FIREWALL

**Why this file exists.** There are now two games. This one — *Estate Liquidators*, four-player
co-op horror extraction — and **UNDERMINE**, a single-player 2D mining game about reading rock, in
its own repository with no shared git ancestry. This file records what belongs to *this* project so
the other one cannot quietly reinvent it.

A fuller copy lives in the UNDERMINE repository, written from that side. This is the short version,
plus the parts that are this project's responsibility.

---

## 1. What this project owns

These are load-bearing here. If they show up in the other project, that project has become this one
with different art.

| Idea | Where | Status |
|---|---|---|
| **Greed is the difficulty slider** — the game never forces danger, it prices it | `DESIGN.md` §2, §4 | pillar 1 |
| **Aggro is an object, not a state** — threat attaches to loot and is transferable by handing it over, never deletable by dropping | `DESIGN.md` §2, §6.1 · D-03 FIRM | pillar 2, and the most identifiable idea in the project |
| **Information costs safety** — the appraiser reveals value and curse in three stationary seconds, louder than sprinting | `DESIGN.md` §2, §4.4 · D-10 | pillar 3 |
| **The tally is the punchline** — the itemized post-run ledger, read aloud | `DESIGN.md` §2, §3 | pillar 4 |
| **One Loudness value per event, read by three systems** — Curator hearing, Disturbance gain, player audibility | D-12 FIRM · `AUDIO-SPEC.md` §1 | the nervous system |
| **Disturbance** — fast-decaying noise level plus a ratcheting floor, tiers at 30/60/85 | `DESIGN.md` §6.5 | the pacing spine; took three sim rounds to get right |
| **Van capacity as the master balance constant** — 14 slots, and every other economy number reverse-engineered from it | D-19 FIRM · `ECONOMY.md` §1–2 | forced abandonment of value is the heartbeat |
| **The monster retrieves, it does not hunt** — a curator restoring a collection, and first contact takes the loot, not the life | D-02 FIRM · `DESIGN.md` §6, §6.3 | licenses the hot potato and the whole social layer |
| **The extraction run** — fixed-length night, hard end at sunrise, quota in dollars, contract chain | `DESIGN.md` §3, §9 | the run structure |

---

## 2. This project's obligations

Two things are this repository's job, not the other one's.

**Pin exact versions in `STACK.md`.** "Unity 6" is not a pin. Record the exact Unity version and the
exact FishNet, Dissonance and FMOD versions in use. **No dependency upgrade here may originate in
the other project**, and vice versa — a shared version bump is how two codebases start sharing
bugs.

**Keep the vendored voice bridge vendored.** `STACK.md` already calls for forking the
Dissonance↔FishNet bridge into this repository at Milestone 0 rather than depending on upstream
(D-16). That decision is unaffected by the other project existing, and it stays.

---

## 3. Sequencing — this project has priority

Recorded here because it constrains the other project, and in that project's `DECISIONS.md` as M-00.

Estate Liquidators is at *design settled, next information must come from a playtest*, and its next
step is the least pleasant work in the portfolio: two clients over Steam P2P with spatial voice.
UNDERMINE is at the most pleasant stage that exists — writing documents, which feels exactly like
progress.

**No further UNDERMINE work happens until this project clears its Phase 0 and Phase 1 exit
criteria**, except that project's own firewall hygiene. In a fair fight the new project wins on
pleasantness alone and this one quietly dies.

Progress here is measured in exit criteria met, never in documents written.

---

## 4. The review test

Before any design session on either project, and whenever a new mechanic is proposed for UNDERMINE,
apply one check:

> Can the proposed mechanic be described using one of this project's four pillars?

If yes, it does not go in the other game. The firewall's own falsification condition is stated in
UNDERMINE's copy: if that design can be described using these four pillars, the firewall has failed,
and **UNDERMINE changes — not the firewall.**
