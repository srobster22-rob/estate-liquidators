"""
MESO — R1. Do deload weeks pay for themselves, and if so, why?

The question this exists to answer:

    Every popular program inserts a deload every 4-6 weeks. DESIGN.md 5 wants to make
    deloads *triggered* rather than calendared. Before designing a trigger, establish
    that the thing being triggered is worth anything at all.

WHAT IS BEING COMPARED
  Five policies, all running the same ramping mesocycle (start at 12 hard sets/week,
  +2 sets each accumulation week, capped at 48 — deliberately well above the modelled
  MRV of ~31, so the ramp can actually overshoot), differing only in when they insert a
  deload week at 40% volume:

    NONE        never deload; ramp to the cap and hold
    FIXED-3     3 accumulation weeks, then 1 deload
    FIXED-5     5 accumulation weeks, then 1 deload
    FIXED-7     7 accumulation weeks, then 1 deload
    TRIGGERED   deload as soon as modelled preparedness is lower than it was 7 days ago

  After each deload the ramp restarts one set higher than the previous cycle started,
  so a policy that deloads often is not automatically a policy that trains less hard —
  it accumulates in shorter, more frequent waves.

  Run three times: the pure linear model, the linear model plus staleness (adaptation
  discounted when the fatigue trace runs high), and the saturating-stimulus model that
  R1b established is the only one of the three capable of representing volume at all.
  The first two are kept because their results are the argument for the third.

  KNOWN CONFOUND, unfixed on purpose (see DECISIONS.md D-06): the policies do not
  perform equal total volume — the deloading ones do 45-70% of the work of the
  never-deload one. So "deloading wins" here is partly "doing less than 618 sets in 20
  weeks wins". A volume-matched re-run is ranked third in LOOP_LOG's next round.

METRICS
  Mean and final preparedness over a 20-week block, plus total sets performed. Reporting
  volume alongside outcome matters: a policy that wins on preparedness while doing 20%
  less work is a different, better result than one that wins by grinding.

DELIBERATE OMISSIONS
  No injury hazard, no motivation, no life stress, no sleep. All four are real reasons
  people deload and all four are outside a performance model. If deloads only justify
  themselves through those channels, that is itself the finding, and it belongs in
  DESIGN.md as an honest statement rather than a fake curve.
"""

from __future__ import annotations

from dataclasses import dataclass

from ff_model import (
    FFParams,
    POPULATION_PRIOR,
    SaturationParams,
    StalenessParams,
    Trace,
    lifter_population,
    simulate,
    weekly_schedule,
)

TRAINING_DAYS = (0, 2, 4)
BLOCK_WEEKS = 20
RAMP_START = 12.0
RAMP_STEP = 2.0
VOLUME_CAP = 48.0   # deliberately above the modelled MRV, so the ramp can overshoot
DELOAD_FRACTION = 0.40
CYCLE_CARRYOVER = 1.0   # each new cycle starts this many sets above the last
MIN_WEEKS_BETWEEN_DELOADS = 2


@dataclass
class Result:
    policy: str
    mean_prep: float
    final_prep: float
    peak_prep: float
    total_sets: float
    deloads: int


def _run_weeks(
    weekly_sets: list[float],
    params: FFParams,
    stale: StalenessParams,
    sat: SaturationParams | None = None,
) -> Trace:
    series: list[float] = []
    for s in weekly_sets:
        series.extend(weekly_schedule(s, TRAINING_DAYS))
    return simulate(series, params, stale, saturation=sat)


def fixed_policy(accumulation_weeks: int) -> list[float]:
    """Weekly set counts for a fixed N-on-1-off cycle."""
    weeks: list[float] = []
    cycle_start = RAMP_START
    while len(weeks) < BLOCK_WEEKS:
        for i in range(accumulation_weeks):
            weeks.append(min(VOLUME_CAP, cycle_start + i * RAMP_STEP))
            if len(weeks) == BLOCK_WEEKS:
                return weeks
        weeks.append(round(weeks[-1] * DELOAD_FRACTION, 2))
        cycle_start = min(VOLUME_CAP, cycle_start + CYCLE_CARRYOVER)
    return weeks[:BLOCK_WEEKS]


def no_deload_policy() -> list[float]:
    return [min(VOLUME_CAP, RAMP_START + i * RAMP_STEP) for i in range(BLOCK_WEEKS)]


def triggered_policy(
    params: FFParams, stale: StalenessParams, sat: SaturationParams | None = None
) -> list[float]:
    """
    Grow the plan a week at a time, re-simulating after each week and inserting a
    deload the moment preparedness has gone backwards over the last 7 days.

    This is the honest version of a triggered policy: it only ever looks at data it
    would actually have at the time of the decision.
    """
    weeks: list[float] = []
    cycle_start = RAMP_START
    weeks_since_deload = 0
    step_in_cycle = 0

    while len(weeks) < BLOCK_WEEKS:
        planned = min(VOLUME_CAP, cycle_start + step_in_cycle * RAMP_STEP)
        weeks.append(planned)
        step_in_cycle += 1
        weeks_since_deload += 1

        trace = _run_weeks(weeks, params, stale, sat)
        today = trace.preparedness[-1]
        week_ago = trace.preparedness[-8] if len(trace.preparedness) > 8 else None

        if (
            week_ago is not None
            and today < week_ago
            and weeks_since_deload >= MIN_WEEKS_BETWEEN_DELOADS
            and len(weeks) < BLOCK_WEEKS
        ):
            weeks.append(round(planned * DELOAD_FRACTION, 2))
            cycle_start = min(VOLUME_CAP, cycle_start + CYCLE_CARRYOVER)
            step_in_cycle = 0
            weeks_since_deload = 0

    return weeks[:BLOCK_WEEKS]


def evaluate(
    name: str,
    weeks: list[float],
    params: FFParams,
    stale: StalenessParams,
    sat: SaturationParams | None = None,
) -> Result:
    trace = _run_weeks(weeks, params, stale, sat)
    deloads = sum(1 for i, s in enumerate(weeks) if i > 0 and s < weeks[i - 1] * 0.6)
    return Result(
        policy=name,
        mean_prep=trace.mean(),
        final_prep=trace.final(),
        peak_prep=trace.peak()[1],
        total_sets=sum(weeks),
        deloads=deloads,
    )


def policies_for(
    params: FFParams, stale: StalenessParams, sat: SaturationParams | None = None
) -> list[tuple[str, list[float]]]:
    return [
        ("NONE", no_deload_policy()),
        ("FIXED-3", fixed_policy(3)),
        ("FIXED-5", fixed_policy(5)),
        ("FIXED-7", fixed_policy(7)),
        ("TRIGGERED", triggered_policy(params, stale, sat)),
    ]


def sweep(
    population: list[FFParams],
    stale: StalenessParams,
    sat: SaturationParams | None = None,
) -> dict[str, Result]:
    """Average each policy's result across the population."""
    accum: dict[str, list[Result]] = {}
    for params in population:
        for name, weeks in policies_for(params, stale, sat):
            accum.setdefault(name, []).append(evaluate(name, weeks, params, stale, sat))

    out: dict[str, Result] = {}
    for name, results in accum.items():
        n = len(results)
        out[name] = Result(
            policy=name,
            mean_prep=sum(r.mean_prep for r in results) / n,
            final_prep=sum(r.final_prep for r in results) / n,
            peak_prep=sum(r.peak_prep for r in results) / n,
            total_sets=sum(r.total_sets for r in results) / n,
            deloads=round(sum(r.deloads for r in results) / n),
        )
    return out


def report(title: str, results: dict[str, Result], baseline: str = "NONE") -> None:
    print(f"\n{title}")
    print("  policy       mean prep   final   peak    sets    deloads   vs NONE")
    print("  " + "-" * 66)
    base = results[baseline].mean_prep
    for name in ("NONE", "FIXED-3", "FIXED-5", "FIXED-7", "TRIGGERED"):
        r = results[name]
        delta = r.mean_prep - base
        print(
            f"  {r.policy:<11}  {r.mean_prep:8.2f}  {r.final_prep:7.2f} {r.peak_prep:7.2f}"
            f" {r.total_sets:7.0f}   {r.deloads:5d}   {delta:+7.2f}"
        )


def staleness_onset_sweep(population: list[FFParams]) -> None:
    """
    Find the chronic-fatigue threshold at which deloading starts to win.

    If there is no such threshold inside a plausible range, the staleness mechanism is
    not the explanation and DESIGN.md 5 needs a different one.
    """
    print("\nStaleness onset sweep — where does a deload start paying?")
    print("  onset   best policy   best mean   NONE mean   edge")
    print("  " + "-" * 56)
    for onset in (2.00, 1.50, 1.20, 1.00, 0.85, 0.70, 0.55, 0.40):
        stale = StalenessParams(enabled=True, onset=onset)
        results = sweep(population, stale)
        best = max(results.values(), key=lambda r: r.mean_prep)
        none = results["NONE"]
        print(
            f"  {onset:5.2f}   {best.policy:<11}  {best.mean_prep:9.2f}  {none.mean_prep:9.2f}"
            f"  {best.mean_prep - none.mean_prep:+6.2f}"
        )


def main() -> None:
    population = lifter_population(40)
    print(f"MESO R1 — deload policy sweep over {len(population)} synthetic lifters, "
          f"{BLOCK_WEEKS}-week block")

    sat = SaturationParams(enabled=True)

    report("LINEAR MODEL (no staleness, no saturation)", sweep(population, StalenessParams()))
    report("WITH STALENESS (onset 0.85, slope 1.60)",
           sweep(population, StalenessParams(enabled=True)))
    report("WITH SATURATING STIMULUS (ceiling 12 sets/session) — the R1b correction",
           sweep(population, StalenessParams(), sat))
    staleness_onset_sweep(population)

    print("\nPrior lifter, week-by-week sets for each policy (saturating model):")
    for name, weeks in policies_for(POPULATION_PRIOR, StalenessParams(), sat):
        print(f"  {name:<11} {[round(w, 1) for w in weeks]}")


if __name__ == "__main__":
    main()
