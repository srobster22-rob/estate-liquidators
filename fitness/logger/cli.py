"""
MESO — the logging CLI.

Deliberately small. Four verbs, no configuration file, no state beyond the JSONL log
itself. Anything that cannot be done with these can be done by editing the log in a text
editor, which is a feature rather than an admission.

    python3 -m logger.cli baseline LOG --exercise squat --value 140
    python3 -m logger.cli set      LOG --week 3 --day 0 --muscle quads --reps 8 --load 100 --rir 2
    python3 -m logger.cli test     LOG --week 3 --day 0 --exercise squat --reps 3 --load 130 --rir 1
    python3 -m logger.cli status   LOG --muscle quads

`status` is the one that matters: it prints what the log has earned the right to say,
which is the whole point of six rounds of simulation.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log import PerformanceTest, Session, WorkSet, load  # noqa: E402
from readiness import report  # noqa: E402


def _warn(problems: list[str]) -> None:
    """
    Problems are printed and the record is still written.

    The log is a record of what happened, not of what should have happened. Refusing to
    store a set taken at 15 reps would just mean the set is missing from the history, and
    a gap is worse than a flagged entry — `assess` can see a flagged entry and discount
    it, and can see nothing at all about a set that was never written.
    """
    for p in problems:
        print(f"  ! {p}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="meso", description="MESO training log")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("baseline", help="record a reference e1RM for a lift")
    p.add_argument("log")
    p.add_argument("--exercise", required=True)
    p.add_argument("--value", type=float, required=True)

    p = sub.add_parser("set", help="log one hard set")
    p.add_argument("log")
    p.add_argument("--week", type=int, required=True)
    p.add_argument("--day", type=int, required=True)
    p.add_argument("--muscle", required=True)
    p.add_argument("--reps", type=int, required=True)
    p.add_argument("--load", type=float, required=True)
    p.add_argument("--rir", type=float, default=2.0)
    p.add_argument("--exercise", default="")

    p = sub.add_parser("test", help="log the weekly performance test")
    p.add_argument("log")
    p.add_argument("--week", type=int, required=True)
    p.add_argument("--day", type=int, default=0)
    p.add_argument("--exercise", required=True)
    p.add_argument("--reps", type=int, required=True)
    p.add_argument("--load", type=float, required=True)
    p.add_argument("--rir", type=float, default=0.0)

    p = sub.add_parser("status", help="what this log has earned the right to say")
    p.add_argument("log")
    p.add_argument("--muscle", required=True)

    args = parser.parse_args(argv)
    log = load(args.log)

    if args.cmd == "baseline":
        log.set_baseline(args.log, args.exercise, args.value)
        print(f"baseline for {args.exercise}: {args.value}")

    elif args.cmd == "set":
        ws = WorkSet(
            muscle_group=args.muscle, reps=args.reps, load=args.load,
            rir=args.rir, exercise=args.exercise,
        )
        _warn(ws.validate())
        existing = next(
            (s for s in log.sessions if s.week == args.week and s.day == args.day), None
        )
        if existing is not None:
            # Sessions are appended whole, so adding a set to an existing day means
            # re-appending that day with the extra set. The reader keeps the last one.
            existing.sets.append(ws)
            log.sessions.remove(existing)
            log.append_session(args.log, existing)
        else:
            log.append_session(args.log, Session(week=args.week, day=args.day, sets=[ws]))
        print(f"logged {args.reps}x{args.load} @RIR{args.rir} ({args.muscle}) "
              f"week {args.week} day {args.day}")

    elif args.cmd == "test":
        t = PerformanceTest(
            week=args.week, day=args.day, exercise=args.exercise,
            reps=args.reps, load=args.load, rir=args.rir,
        )
        _warn(t.validate())
        log.append_test(args.log, t)
        print(f"logged test: {args.exercise} {args.reps}x{args.load} @RIR{args.rir} "
              f"-> e1RM {t.estimated_1rm():.1f}")

    elif args.cmd == "status":
        print(report(log, args.muscle))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
