# Moving to the Mac

The project moved from a Windows PC to an M2 Mac because the PC's drive was 100% full
(~10 GB free of 1.9 TB), which is not enough to create a Unity project, let alone build one.

The whole repository is **~330 KB across 33 files** — plain text, Python, C# and HTML. Nothing
platform-specific, no binaries, no build artifacts worth carrying.

---

## How it moved (done)

Kept as the record of how it got here — nothing in this section needs running again. The
commands below ran on the old Windows PC at `C:\Users\srobs`. The project now lives at
`~/dev/estate-liquidators` on the Mac as its own git repo with its own remote; the initial
commit is *"Estate Liquidators: design foundation, simulations, tested C# core"*.

Any of these is fine. `.gitignore` already excludes the regenerable parts (`bin/`, `obj/`,
`__pycache__/`, and Unity's `Library/`).

**Simplest — zip and AirDrop:**

```bash
cd /c/Users/srobs
tar --exclude='bin' --exclude='obj' --exclude='__pycache__' \
    -czf estate-liquidators.tar.gz estate-liquidators
```

**Or version it properly, which is worth doing now:**

```bash
cd /c/Users/srobs/estate-liquidators
git init && git add -A && git commit -m "Estate Liquidators: design foundation, sims, tested C# core"
```

Then push to a private remote and clone on the Mac. That `git init` deliberately initialised a
repo *inside the project folder only*, because on the Windows PC the parent `C:\Users\srobs`
was a separate shared repo that must never be committed to. **That hazard is gone.** On the
Mac the project is its own repo at `~/dev/estate-liquidators` with its own remote, and there
is no shared parent above it — committing here is not just safe, it's expected. The same stale
warning appeared in `BUILD-PROMPT.md`, `IMPROVE-PROMPT.md` and `ITERATION-PROMPT.md`; R17
retires it there too.

---

## First things to check on the Mac

Run these before anything else; the answers change the plan.

```bash
python3 sim/check_drift.py          # expect: 132 checks, 59/59 constants, 4 implementations
dotnet run --project unity/tests/CoreTests   # expect: 41/41 assertions pass
python3 sim/check_estates.py         # expect: 10/10 estate checks can fail
python3 sim/check_core.py            # expect: every core reversion caught (needs dotnet)
```

The drift figure was `55/55` until `LOOP_LOG.md` R16, which found the checker was silently
skipping unmatched patterns and left 23 of the 59 canonical constants unguarded, and 132 since
R17, which found it had never opened `proto3d/index.html` at all — a fourth implementation that
had drifted behind the gap. It is now fail-closed both ways: a renamed constant, an unregistered
one or a deleted check each fail the run, and coverage is asserted *per implementation*, so a
constant one copy carries but nobody checks there is a failure rather than a silence.

If `dotnet` is missing, install the .NET 9 SDK. The C# core suite is what stops anyone quietly
reverting a rule that was already wrong once — and `sim/check_core.py` is what stops the suite
itself from going soft: it reverts each rule on purpose and fails if nothing notices. Without
dotnet, `check_core.py` exits **2** rather than 0, so a skip can never read as a pass.

Then the engine:

- **Unity 6** for Apple Silicon, via Unity Hub. Personal licence is free under $200k revenue
  and needs a one-time interactive sign-in — that's an account credential, so do it yourself
  and don't delegate it to any agent.
- Add the **Windows Build Support** module while you're there.

---

## The one Mac-specific catch

**Unity's IL2CPP backend compiles through the host platform's native toolchain, and the
Windows target needs MSVC.** The original note here guessed that a Mac therefore *probably*
could not produce a Windows IL2CPP build. **Confirmed — the guess was right. The PC is the
release builder.** Unity's own manual
states cross-compilation is not supported for IL2CPP: to build an IL2CPP player for a target
platform you must build from an Editor running on that platform. Concretely, a macOS Unity
install offers **Windows Build Support (Mono)** only — there is no Windows-IL2CPP module to
tick in Unity Hub, because the Windows IL2CPP toolchain needs MSVC, which exists only on
Windows. macOS gets IL2CPP for the *Mac* target, not for Windows.

So the pipeline is: **develop and iterate on the Mac (Mono is fine for that), and produce the
shipping Steam x64 build on the PC.** Practical consequences worth knowing before Phase 6
rather than during it:

- IL2CPP and Mono differ in ways that bite late — stripping, `[Preserve]`, reflection, and
  generic virtual methods. A build that works in the Editor and under Mono can still fail
  under IL2CPP. Do a Windows IL2CPP build on the PC **early**, at Phase 2, not at Phase 6.
- `steamcmd` depot upload therefore runs on the PC too. Check the depot scripts into this repo
  so the machine doing the upload isn't also the only place the recipe exists.
- The PC's drive was the reason this project moved. A Unity project plus an IL2CPP build needs
  real headroom — clear that space before Phase 6 depends on it.

*Verified 2026-07-30 against Unity's manual and Unity Discussions. This was checked by web
search; the primary docs host was unreachable from the machine that ran the check, so treat
the module list as high-confidence-but-secondhand and confirm it in Unity Hub's install
dialog, which takes ten seconds and settles it outright.*

Either way the PC stays useful: `BUILD-PROMPT.md` Phase 0 needs **two clients over Steam P2P
with spatial voice**, and Phase 1's exit criterion is explicitly *test at real latency, not
LAN*. A Mac plus a Windows PC is a better test pair than one machine, and it surfaces
cross-platform netcode bugs early instead of at release.

---

## Where to pick up

Read `README.md`, then `BUILD-PROMPT.md`. The project is at the point where the design is
settled (21 decisions logged, 1 open and it's an art question), the rules are tested, and the
next real step is Phase 0: **two people, a door, and spatial voice over Steam.**

`LOOP_LOG.md` carries every round of findings, newest at the bottom, including several
corrections to the specs. Where the log and a document disagree, the log is newer. (The round
count used to be quoted here and went stale three times; it isn't any more.)
