"""
MESO — the training log.

The question this exists to answer:

    D-23 closed the simulation phase: the project's central quantity swings by a factor of
    two depending on a population assumption no simulation can settle. What settles it is
    twenty lifters with six months of honest data. This is the thing that collects it.

WHAT THE MODEL ACTUALLY NEEDS
  Six rounds narrowed this to almost nothing. Per week:

    - hard sets per muscle group, with an RIR for each          (drives the impulse)
    - one performance test: reps and load on a known lift       (the observation)

  That is the whole requirement. Everything else a training app might record — tempo,
  rest, bar speed, session RPE, sleep — is outside the model and would be collected on
  spec. It may be worth collecting anyway; it is not worth *blocking* on.

STORAGE
  Append-only JSONL. No dependencies, human-readable, diffable, trivially recoverable if
  the tool that wrote it disappears, and it survives being edited by hand in a text editor
  at 6am in a gym car park — which is a real failure mode for anything with a schema.

  Append-only matters for a reason specific to this project: R2 established that refits
  must see a growing prefix of ONE history. A store that permits silent edits to past
  weeks would let a lifter rewrite the data a fit was already computed from, and nothing
  downstream would notice.

WHAT IS DELIBERATELY NOT HERE
  No exercise database, no muscle-group taxonomy beyond a free string, no sets/reps
  prescription. The logger's job is to produce fittable data, and every one of those would
  be a design decision the project has not earned yet.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, field


# ---------------------------------------------------------------------------
# Estimated 1RM
# ---------------------------------------------------------------------------
#
# The measurement chain the whole project rests on: a top set becomes a number the fitter
# can use. Three published formulas are implemented rather than one, because they disagree
# — and the size of that disagreement is a direct input to D-09's noise assumption. See
# `logger/formula_check.py`, which measures it rather than assuming it.
#
# All three take REPS AT FAILURE. A set taken to RIR r with n reps is treated as a set of
# (n + r) reps at failure, which is the standard convention and is itself an assumption:
# it presumes a lifter's RIR estimate is unbiased, and the literature says novices
# systematically overestimate how many reps they have left. INFERRED, D-24.


def epley(load: float, reps_at_failure: float) -> float:
    return load * (1.0 + reps_at_failure / 30.0)


def brzycki(load: float, reps_at_failure: float) -> float:
    # Undefined at 37 reps and negative beyond; clamped rather than allowed to produce
    # a confidently absurd number.
    return load * 36.0 / max(1.0, 37.0 - min(reps_at_failure, 36.0))


def lombardi(load: float, reps_at_failure: float) -> float:
    return load * math.pow(max(reps_at_failure, 1.0), 0.10)


FORMULAS = {"epley": epley, "brzycki": brzycki, "lombardi": lombardi}
DEFAULT_FORMULA = "epley"


def e1rm(load: float, reps: int, rir: float = 0.0, formula: str = DEFAULT_FORMULA) -> float:
    """
    Estimated one-rep max from a set taken to a stated RIR.

    Epley by default: it is the most widely used, it is smooth, and it does not blow up
    at high reps the way Brzycki does. That choice is worth ~2-4% against the
    alternatives in the 5-10 rep range and much more above it — measured, not guessed,
    in `formula_check.py`.
    """
    if load <= 0 or reps <= 0:
        raise ValueError("a set needs a positive load and at least one rep")
    if rir < 0:
        raise ValueError("RIR cannot be negative")
    return FORMULAS[formula](load, reps + rir)


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


@dataclass
class WorkSet:
    """One hard set. Warm-ups are not logged — they are not stimulus and not fatigue."""

    muscle_group: str
    reps: int
    load: float
    rir: float = 2.0
    exercise: str = ""

    def validate(self) -> list[str]:
        problems = []
        if not self.muscle_group.strip():
            problems.append("muscle_group is empty")
        if self.reps <= 0:
            problems.append(f"reps must be positive, got {self.reps}")
        if self.load <= 0:
            problems.append(f"load must be positive, got {self.load}")
        if not 0 <= self.rir <= 10:
            problems.append(f"rir outside 0-10, got {self.rir}")
        return problems


@dataclass
class Session:
    """One training day. `week` and `day` are the only time the model cares about."""

    week: int
    day: int                       # 0-6 within the week
    sets: list[WorkSet] = field(default_factory=list)
    note: str = ""

    def sets_for(self, muscle_group: str) -> list[WorkSet]:
        return [s for s in self.sets if s.muscle_group == muscle_group]

    def validate(self) -> list[str]:
        problems = []
        if self.week < 0:
            problems.append(f"week must be >= 0, got {self.week}")
        if not 0 <= self.day <= 6:
            problems.append(f"day must be 0-6, got {self.day}")
        for i, s in enumerate(self.sets):
            problems.extend(f"set {i}: {p}" for p in s.validate())
        return problems


# Test protocol caps. Derived in logger/formula_check.py, not chosen. D-26.
TEST_MAX_REPS = 8
TEST_MAX_RIR = 1.0


@dataclass
class PerformanceTest:
    """
    The weekly observation. One top set on a consistent lift, converted to an e1RM.

    `baseline` is the lifter's reference e1RM for this lift, so observations can be
    expressed as a percentage of it — which is what makes `p0 = 100` a definition rather
    than a fifth free parameter (DESIGN.md 4.1).
    """

    week: int
    day: int
    exercise: str
    reps: int
    load: float
    rir: float = 0.0

    def estimated_1rm(self, formula: str = DEFAULT_FORMULA) -> float:
        return e1rm(self.load, self.reps, self.rir, formula)

    def as_percentage(self, baseline: float, formula: str = DEFAULT_FORMULA) -> float:
        if baseline <= 0:
            raise ValueError("baseline must be positive")
        return self.estimated_1rm(formula) / baseline * 100.0

    def validate(self) -> list[str]:
        problems = []
        if self.week < 0:
            problems.append(f"week must be >= 0, got {self.week}")
        if not 0 <= self.day <= 6:
            problems.append(f"day must be 0-6, got {self.day}")
        if self.reps <= 0 or self.load <= 0:
            problems.append("a test needs positive reps and load")
        if not self.exercise.strip():
            problems.append("exercise is empty")
        # The test protocol, derived in logger/formula_check.py rather than chosen.
        # Naive logging (up to 12 reps at RIR 2 — i.e. testing the way you train) implies
        # a measurement sigma of 5.6 points against D-09's assumed 2.5, which pushes every
        # week-threshold in the project far out. Capping reps and testing near failure
        # brings it to 2.4. A test is a measurement, not a stimulus: its only job is to be
        # precise, so it is taken differently from the training. D-26.
        if self.reps > TEST_MAX_REPS:
            problems.append(
                f"{self.reps} reps is above the {TEST_MAX_REPS}-rep test cap — e1RM "
                "formulas diverge fast above this (2.8% spread at 8 reps, 11.3% at 12, "
                "46.1% at 20) and the observation becomes noise"
            )
        if self.rir > TEST_MAX_RIR:
            problems.append(
                f"RIR {self.rir} is above the {TEST_MAX_RIR} test cap — RIR enters the "
                "formula through (reps + RIR), so a misestimate here lands straight in "
                "the observation. Train at RIR 1-3; test at RIR 0-1."
            )
        return problems


# ---------------------------------------------------------------------------
# The log
# ---------------------------------------------------------------------------


@dataclass
class TrainingLog:
    sessions: list[Session] = field(default_factory=list)
    tests: list[PerformanceTest] = field(default_factory=list)
    baseline_e1rm: dict[str, float] = field(default_factory=dict)

    # -- queries ---------------------------------------------------------

    def weeks_logged(self) -> int:
        weeks = {s.week for s in self.sessions} | {t.week for t in self.tests}
        return max(weeks) + 1 if weeks else 0

    def muscle_groups(self) -> list[str]:
        return sorted({s.muscle_group for sess in self.sessions for s in sess.sets})

    def weekly_sets(self, muscle_group: str) -> list[float]:
        """Hard sets per week for one muscle group, zero-filled for missed weeks."""
        n = self.weeks_logged()
        out = [0.0] * n
        for sess in self.sessions:
            if 0 <= sess.week < n:
                out[sess.week] += len(sess.sets_for(muscle_group))
        return out

    def daily_sets(self, muscle_group: str) -> list[float]:
        """
        Sets per day, RIR-weighted, in the layout `fit.Log` expects.

        Weighted by `RIR_STIMULUS` so a set to RIR 4 does not count the same as one to
        RIR 1 — the divergence between the stimulus and fatigue tables is the arithmetic
        reason DESIGN.md 6 prescribes RIR 1-3, and ignoring it here would throw that away
        at the point where it finally meets real data.
        """
        from ff_model import RIR_STIMULUS

        n = self.weeks_logged() * 7
        out = [0.0] * n
        for sess in self.sessions:
            idx = sess.week * 7 + sess.day
            if 0 <= idx < n:
                for s in sess.sets_for(muscle_group):
                    key = int(round(min(5.0, max(0.0, s.rir))))
                    out[idx] += RIR_STIMULUS[key]
        return out

    def validate(self) -> list[str]:
        problems: list[str] = []
        for s in self.sessions:
            problems.extend(f"session w{s.week}d{s.day}: {p}" for p in s.validate())
        for t in self.tests:
            problems.extend(f"test w{t.week}: {p}" for p in t.validate())

        seen: set[tuple[int, int]] = set()
        for s in self.sessions:
            if (s.week, s.day) in seen:
                problems.append(f"duplicate session at week {s.week} day {s.day}")
            seen.add((s.week, s.day))

        for t in self.tests:
            if t.exercise not in self.baseline_e1rm:
                problems.append(f"no baseline recorded for test exercise '{t.exercise}'")
        return problems

    # -- persistence -----------------------------------------------------

    def append_session(self, path: str, session: Session) -> None:
        _append(path, {"type": "session", **asdict(session)})
        self.sessions.append(session)

    def append_test(self, path: str, test: PerformanceTest) -> None:
        _append(path, {"type": "test", **asdict(test)})
        self.tests.append(test)

    def set_baseline(self, path: str, exercise: str, value: float) -> None:
        _append(path, {"type": "baseline", "exercise": exercise, "value": value})
        self.baseline_e1rm[exercise] = value


def _append(path: str, record: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def load(path: str) -> TrainingLog:
    """
    Read a JSONL log. Later baselines override earlier ones; everything else appends.

    Unknown record types are IGNORED rather than rejected, so a future version writing new
    record kinds does not make old files unreadable by old code. Malformed lines are a
    different matter and do raise — a line that cannot be parsed is data loss, and
    silently skipping it would hide it.
    """
    log = TrainingLog()
    if not os.path.exists(path):
        return log

    # Sessions are stored as whole records keyed on (week, day), and a later record for
    # the same day SUPERSEDES the earlier one rather than adding to it. That is what makes
    # append-only storage compatible with editing a day — add a fourth set to Tuesday and
    # the writer re-appends Tuesday with four sets.
    #
    # Getting this wrong is not a crash, it is silent double-counting: the first version of
    # this reader summed every record it saw, so logging three sets one at a time produced
    # a week with five. Caught by its own test, and pinned by one.
    sessions: dict[tuple[int, int], Session] = {}

    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno} is not valid JSON: {exc}") from exc

            kind = rec.pop("type", None)
            if kind == "session":
                sets = [WorkSet(**s) for s in rec.pop("sets", [])]
                sess = Session(sets=sets, **rec)
                sessions[(sess.week, sess.day)] = sess
            elif kind == "test":
                log.tests.append(PerformanceTest(**rec))
            elif kind == "baseline":
                log.baseline_e1rm[rec["exercise"]] = rec["value"]

    log.sessions = [sessions[k] for k in sorted(sessions)]
    return log
