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
python3 sim/check_drift.py          # expect: 56/56 constants agree
python3 sim/validate_estate.py      # expect: clean estate 11/11, broken estate trips 8
dotnet run --project unity/tests/CoreTests   # expect: 31/31 assertions pass
```

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

**Verify this before committing to a pipeline.** It's my understanding of Unity's toolchain
rather than something I confirmed, and it moves between versions. It decides whether the PC is
retired or kept as the release builder.

Either way the PC stays useful: `BUILD-PROMPT.md` Phase 0 needs **two clients over Steam P2P
with spatial voice**, and Phase 1's exit criterion is explicitly *test at real latency, not
LAN*. A Mac plus a Windows PC is a better test pair than one machine, and it surfaces
cross-platform netcode bugs early instead of at release.

---

## Where to pick up

Read `README.md`, then `BUILD-PROMPT.md`. The project is at the point where the design is
settled (23 decisions logged, 1 open and it is an art question), the rules are tested, and the
next real step is Phase 0: **two people, a door, and spatial voice over Steam.**

`LOOP_LOG.md` has sixteen rounds of findings, including several corrections to the specs.
Where the log and a document disagree, the log is newer.
