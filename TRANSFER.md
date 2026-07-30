# Moving to the Mac

The project moved from a Windows PC to an M2 Mac because the PC's drive was 100% full
(~10 GB free of 1.9 TB), which is not enough to create a Unity project, let alone build one.

The whole repository is **930 KB across 30 files** — plain text, Python, C# and HTML. Nothing
platform-specific, no binaries, no build artifacts worth carrying.

---

## Moving it

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

Then push to a private remote and clone on the Mac. **Note:** this initialises a repo *inside
the project folder only*. The parent `C:\Users\srobs` is a separate shared repo that must
never be committed to.

Land it somewhere with real headroom — `~/dev/estate-liquidators` is fine.

---

## First things to check on the Mac

Run these before anything else; the answers change the plan.

```bash
python3 sim/check_drift.py          # expect: 106 checks over 59/59 constants
dotnet run --project unity/tests/CoreTests   # expect: 31/31 assertions pass
```

The drift figure was `55/55` until `LOOP_LOG.md` R16, which found the checker was silently
skipping unmatched patterns and left 23 of the 59 canonical constants unguarded. It is now
fail-closed: a renamed constant, an unregistered one, or a deleted check each fail the run.

If `dotnet` is missing, install the .NET 9 SDK — the C# core suite is the thing that stops
anyone quietly reverting the three rules that were each wrong once.

Then the engine:

- **Unity 6** for Apple Silicon, via Unity Hub. Personal licence is free under $200k revenue
  and needs a one-time interactive sign-in — that's an account credential, so do it yourself
  and don't delegate it to any agent.
- Add the **Windows Build Support** module while you're there.

---

## The one Mac-specific catch

**Unity's IL2CPP backend compiles through the host platform's native toolchain, and the
Windows target needs MSVC.** That means a Mac probably cannot produce a Windows IL2CPP
build — you can cross-compile a Windows *Mono* build for development, but the shipping Steam
build likely has to come off a Windows machine.

**Confirmed — the suspicion was right. The PC is the release builder.** Unity's own manual
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

`LOOP_LOG.md` has fifteen rounds of findings, including several corrections to the specs.
Where the log and a document disagree, the log is newer.
