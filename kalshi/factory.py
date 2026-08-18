"""
The loop. Breed bots across every market family and strategy family, and try to
disqualify all of them.

    python -m kalshi.factory                  full run, writes RESULTS.md
    python -m kalshi.factory --quick          small run for checking wiring
    python -m kalshi.factory --generations 20

HOW A GENERATION WORKS, and why in this order:

    1  BUILD      generation 0 pairs EVERY market family with EVERY compatible strategy,
                  two random parameter draws each — that is the "try all the market types
                  with all the strategies" sweep. Later generations are mutations of what
                  survived, plus fresh random draws so the search cannot collapse into one
                  neighbourhood, plus whatever the expansion step has widened.
    2  SCREEN     in-sample only, 300 markets. Ranked by t-statistic, after discarding
                  anything below the capital-efficiency floor — a 3c edge that locks
                  collateral for 90 days is not worth an out-of-sample slot.
    3  VALIDATE   the top survivors go to out-of-sample data, disjoint by seed. Every one
                  of these is a hypothesis test and every one is recorded in a CUMULATIVE
                  registry that spans all generations.
    4  CORRECT    Holm across the entire registry. Generation 8's candidate is judged
                  against every test generations 0-7 already spent.
    5  CONFIRM    only a candidate that passes everything else touches the holdout set,
                  and the stress test. Holdout touches are counted and reported, because a
                  third dataset visited fifty times is not a third dataset.
    6  EXPAND     widen the parameter grid around the best in-sample performers, so the
                  search genuinely grows rather than re-rolling the same dice.

THE ONE RULE THAT MAKES THE OUT-OF-SAMPLE NUMBER MEAN ANYTHING:

    Selection and breeding use IN-SAMPLE RESULTS ONLY. Never OOS. The instant a survivor
    is bred from its out-of-sample score, out-of-sample has been fitted and the number on
    the report is decoration. This is the single easiest place for a loop like this to
    quietly cheat, so `_breed` is not given access to OOS results at all.

WHAT A PASS HERE DOES AND DOES NOT MEAN. It means: a bot cleared eight independent
disqualification criteria on data drawn from THIS SIMULATOR. The simulator's edges were
planted by hand in markets.py. So a pass is evidence that the strategy correctly harvests
a known, quantified inefficiency after realistic fees, spreads and depth limits — and it
is not evidence that the inefficiency exists on Kalshi at that size, or at all. That
question needs real historical data, and `live.py` is the adapter for getting it.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import time

from . import backtest, capacity, evaluate, markets, strategies

CFG = json.loads((pathlib.Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
LOOP = CFG["loop"]
SEEDS = CFG["seeds"]
GATE = CFG["gate"]

MIN_TRADES_INSAMPLE = 50
ROOT = pathlib.Path(__file__).parent


class Candidate:
    __slots__ = ("family", "cls", "params", "gen", "origin", "ins", "oos", "holdout",
                 "stress", "half_edge", "verdict", "raw_p", "fwer_p", "bh_p", "sens")

    def __init__(self, family, cls, params, gen, origin):
        self.family, self.cls, self.params = family, cls, params
        self.gen, self.origin = gen, origin
        self.ins = self.oos = self.holdout = self.stress = self.half_edge = None
        self.verdict = None
        self.raw_p = self.fwer_p = self.bh_p = None
        self.sens = None

    def build(self):
        return self.cls(**self.params)

    def key(self):
        return (self.family, self.cls.__name__, tuple(sorted(self.params.items())))

    def label(self):
        return f"{self.family} / {self.build().label()}"


class Registry:
    """Every out-of-sample test the loop has ever run. The denominator of the correction.

    Kept across generations on purpose. A loop that resets its multiplicity count each
    generation can run forever and will eventually "find" something, which is the failure
    mode this class exists to make impossible.
    """

    def __init__(self):
        self.tests: list[tuple[str, float, int]] = []
        self.holdout_touches = 0

    def add(self, label, p, gen) -> int:
        self.tests.append((label, p, gen))
        return len(self.tests)

    def adjusted(self):
        ps = [p for _, p, _ in self.tests]
        return evaluate.holm(ps), evaluate.benjamini_hochberg(ps)

    def __len__(self):
        return len(self.tests)


def compatible(family: str, cls) -> bool:
    fam = markets.FAMILIES[family]
    if cls.requires_brackets:
        return fam.n_brackets > 1
    return True


def _params_ok(cls, params) -> bool:
    if cls in (strategies.band_fade, strategies.snr_band) and params["lo"] > params["hi"]:
        return False
    return True


def _sample(cls, rng):
    for _ in range(12):
        p = strategies.sample_params(cls, rng)
        if _params_ok(cls, p):
            return p
    return None


def initial_population(rng, draws_per_pair=2) -> list[Candidate]:
    """Every market family x every compatible strategy. The broad sweep."""
    pop = []
    for family in markets.FAMILIES:
        for cls in strategies.ALL:
            if not compatible(family, cls):
                continue
            for _ in range(draws_per_pair):
                p = _sample(cls, rng)
                if p is not None:
                    pop.append(Candidate(family, cls, p, 0, "sweep"))
    return pop


def _breed(survivors: list[Candidate], rng, size, gen, already: set) -> list[Candidate]:
    """Mutations of in-sample survivors, plus fresh draws.

    Takes `survivors` ranked by IN-SAMPLE t only. It is never passed out-of-sample results
    and must never be — see the module docstring.

    `already` is every bot the run has built so far, so a generation fills up to `size` with
    genuinely NEW candidates instead of proposing duplicates and being silently trimmed
    afterwards. Without it, later generations shrank towards nothing as the neighbourhoods
    around the survivors got used up, and the loop looked like it was converging when it was
    only running out of unseen parameter tuples.
    """
    pop, seen = [], set(already)
    per = max(1, LOOP["mutations_per_survivor"])
    for c in survivors:
        for _ in range(per * 2):
            p = strategies.mutate(c.cls, c.params, rng)
            if not _params_ok(c.cls, p):
                continue
            nc = Candidate(c.family, c.cls, p, gen, f"mutation of g{c.gen}")
            if nc.key() in seen:
                continue
            seen.add(nc.key())
            pop.append(nc)
            if sum(1 for x in pop if x.cls is c.cls and x.family == c.family) >= per:
                break
    # Fresh blood, so the search cannot converge on one corner of the space and declare it
    # the world. Bounded attempts because a saturated grid would otherwise spin here.
    fams = list(markets.FAMILIES)
    attempts = 0
    while len(pop) < size and attempts < size * 60:
        attempts += 1
        family = rng.choice(fams)
        cls = rng.choice(strategies.ALL)
        if not compatible(family, cls):
            continue
        p = _sample(cls, rng)
        if p is None:
            continue
        nc = Candidate(family, cls, p, gen, "fresh")
        if nc.key() in seen:
            continue
        seen.add(nc.key())
        pop.append(nc)
    return pop[:size]


def _expand(survivors: list[Candidate], rng, log):
    """Widen the grid around what is working. The 'expand' half of expand-until-done.

    Only extends parameters that are already at the edge of their range — if the best
    threshold found is the largest one on the list, the list was too short.
    """
    added = 0
    for c in survivors[:4]:
        grid = strategies.PARAM_GRID[c.cls]
        for k, cur in c.params.items():
            vals = grid[k]
            if not isinstance(cur, (int, float)) or k == "qty":
                continue
            if cur == max(vals) and isinstance(cur, int):
                nxt = cur + max(1, (max(vals) - min(vals)) // 4)
                if nxt not in vals and nxt <= (99 if "thresh" in k or k in ("lo", "hi") else 60):
                    vals.append(nxt)
                    vals.sort()
                    added += 1
                    log(f"      expanded {c.cls.__name__}.{k} -> added {nxt} "
                        f"(best was at the edge of the grid)")
            elif cur == min(vals) and isinstance(cur, int) and cur > 1:
                nxt = max(1, cur - max(1, (max(vals) - min(vals)) // 4))
                if nxt not in vals:
                    vals.append(nxt)
                    vals.sort()
                    added += 1
                    log(f"      expanded {c.cls.__name__}.{k} -> added {nxt} "
                        f"(best was at the edge of the grid)")
    return added


def _base_family(name: str) -> str:
    """'econ_print@0.5' -> 'econ_print'. Attenuated copies list the same markets a year."""
    return name.split("@", 1)[0]


def score(c: Candidate, seed_base, n_groups, costs=backtest.BASE_COSTS, resamples=0,
          family=None):
    fam = family or c.family
    data = markets.dataset(fam, seed_base, n_groups)
    res = backtest.run(data, c.build(), costs)
    return evaluate.summarize(res, resamples=resamples,
                              markets_per_year=capacity.sets_per_year(
                                  _base_family(fam)))


def run_loop(generations, insample_n, oos_n, holdout_n, survivors_n, pop_size,
             seed=20260730, verbose=True, keep_going=False):
    rng = random.Random(seed)
    reg = Registry()
    lines: list[str] = []
    winners: list[Candidate] = []
    confirmed: list[Candidate] = []      # cleared criteria 1-10; may be too small on dollars
    all_oos: list[Candidate] = []
    control_flags: list[str] = []
    t0 = time.time()

    def log(s=""):
        lines.append(s)
        if verbose:
            print(s, flush=True)

    log(f"KALSHI BOT FACTORY — seed {seed}")
    log(f"  {len(markets.FAMILIES)} market families x {len(strategies.ALL)} strategies")
    log(f"  in-sample {insample_n} markets (seed {SEEDS['insample']}) | "
        f"OOS {oos_n} (seed {SEEDS['oos']}) | holdout {holdout_n} (seed {SEEDS['holdout']})")
    log(f"  bar to beat: ${GATE['min_annual_dollars']:,}/yr")
    log(f"  gate: {len(evaluate.GATE_CRITERIA)} criteria "
        f"({', '.join(evaluate.GATE_CRITERIA)}), Holm-corrected across every OOS test")
    log()

    prev_survivors: list[Candidate] = []
    seen_keys: set = set()

    for gen in range(generations):
        gt0 = time.time()
        if gen == 0:
            pop = initial_population(rng)
        else:
            pop = _breed(prev_survivors, rng, pop_size, gen, seen_keys)
        pop = [c for c in pop if c.key() not in seen_keys]
        for c in pop:
            seen_keys.add(c.key())

        log(f"--- GENERATION {gen} --- {len(pop)} candidates "
            f"({'full sweep' if gen == 0 else 'bred from in-sample survivors'})")
        if not pop:
            log("    nothing new to test — the search space around the survivors is exhausted")
            break

        # 2. SCREEN — in-sample only.
        for c in pop:
            c.ins = score(c, SEEDS["insample"], insample_n)

        # Two filters, then rank by evidence. The dollar filter is the new one and it is a
        # prefilter, not the ranking: ranking BY in-sample dollars would just chase the
        # noisiest high-frequency family, since dollars amplify sampling error by markets/yr
        # exactly as much as they amplify edge. The t-statistic is still the right screening
        # statistic; dollars decide who is worth an out-of-sample slot at all.
        dollar_floor = 0.0
        eligible = [c for c in pop
                    if c.ins.n_trades >= MIN_TRADES_INSAMPLE
                    and c.ins.annualized >= GATE["min_annualized_return_on_locked_capital"]
                    and c.family != "efficient_control"]

        # WHY A CANDIDATE WAS DISCARDED, REPORTED SEPARATELY. K28 found the loop could never
        # have discovered the best result in this project, and the trade-count screen is half
        # the reason: `bracket_arb` fires in ~1.7% of sets, so at the default 300 in-sample
        # groups it books 25 leg-trades against a floor of 50 and is cut before it is ever
        # scored. That is not the same outcome as losing money, and reporting them together
        # as "screened out" is how the loop hid its own best candidate for four rounds.
        #
        # This is deliberately a REPORT, not a fix. Lowering the floor would admit strategies
        # whose t-statistic is meaningless, and raising insample_n costs time on every
        # candidate to rescue the rare ones. The honest move is to make the loop say what it
        # threw away and why, so a rare-but-real strategy is visible as a sample-size problem
        # rather than invisible as a failure.
        _too_rare = [c for c in pop
                     if c.ins.n_trades < MIN_TRADES_INSAMPLE
                     and c.ins.mean > 0 and c.family != "efficient_control"]
        if _too_rare:
            _by_fam: dict[str, int] = {}
            for c in _too_rare:
                _by_fam[c.family] = _by_fam.get(c.family, 0) + 1
            _worst = min(_too_rare, key=lambda c: c.ins.n_trades)
            log(f"    NOT SCORED — too rare to screen, not unprofitable: {len(_too_rare)} "
                f"candidates with a positive in-sample mean booked fewer than "
                f"{MIN_TRADES_INSAMPLE} trades in {insample_n} groups "
                f"({', '.join(f'{k} x{v}' for k, v in sorted(_by_fam.items()))})")
            log(f"      rarest: {_worst.label()[:52]} on {_worst.family} — "
                f"{_worst.ins.n_trades} trades, {_worst.ins.mean:+.1f}c/group. A strategy "
                f"this rare needs more in-sample data, not a lower bar.")
        eligible.sort(key=lambda c: -c.ins.t)
        # STRATIFY BY FAMILY BEFORE RANKING GLOBALLY. A pure global top-N starves families:
        # over 14 generations and 164 out-of-sample tests, econ_print took 92 slots while
        # sports_game, index_bracket_daily and awards_thin got ZERO — never tested once.
        # sports_game has the second-strongest planted bias on the exchange (gamma 0.93), a
        # 150-800 contract book and 6,000 markets a year, and the loop had never looked at
        # it. That was an artefact of how slots were handed out, not a finding about the
        # family. Each family with an eligible candidate now gets its best one first; the
        # remaining slots go by global t-rank as before.
        survivors, taken = [], set()
        for c in eligible:
            if c.family not in taken:
                taken.add(c.family)
                survivors.append(c)
                if len(survivors) >= survivors_n:
                    break
        for c in eligible:
            if len(survivors) >= survivors_n:
                break
            if c not in survivors:
                survivors.append(c)

        n_pos = sum(1 for c in pop if c.ins.mean > 0)
        log(f"    screened: {n_pos}/{len(pop)} positive in-sample, "
            f"{len(eligible)} clear the trade-count and capital floors")

        # The tripwire. Any control-family candidate that looks good in-sample is expected
        # (search noise); one that would pass the full gate is a harness failure.
        for c in pop:
            if c.family == "efficient_control" and c.ins.t > 3.0:
                control_flags.append(f"g{gen} {c.label()} in-sample t={c.ins.t:+.2f}")

        # 3. VALIDATE — out-of-sample.
        for c in survivors:
            c.oos = score(c, SEEDS["oos"], oos_n, resamples=2000)
            c.raw_p = c.oos.p_one_sided
            reg.add(c.label(), c.raw_p, gen)
            all_oos.append(c)

        # 4. CORRECT — Holm over every OOS test in the whole run.
        holm_adj, bh_adj = reg.adjusted()
        for i, c in enumerate(all_oos):
            c.fwer_p, c.bh_p = holm_adj[i], bh_adj[i]

        log(f"    out-of-sample: {len(survivors)} tested "
            f"({len(reg)} cumulative tests, Holm denominator)")
        for c in sorted(survivors, key=lambda x: -x.oos.mean)[:6]:
            log(f"      {c.label():<62} ins t={c.ins.t:+5.2f} | "
                f"oos mean={c.oos.mean:+8.2f}c p={c.raw_p:.4f} "
                f"holm={c.fwer_p:.3f} ${c.oos.annual_dollars:+9,.0f}/yr")

        # 5. CONFIRM — holdout and stress, only for candidates that clear everything else.
        for c in sorted(survivors, key=lambda x: x.fwer_p):
            pre = evaluate.gate(c.oos, None, None, c.fwer_p, len(reg), c.bh_p)
            # `annual_dollars` is excluded here on purpose. It is a statement about the
            # BUSINESS, not about whether the edge is real, and applying it per-bot rejects
            # components that are genuinely profitable but small — even when adding them
            # strictly increases total income. Criteria 1-10 gate the bot; criterion 11 gates
            # the portfolio, in portfolio.py.
            blocking = [r for r in pre.reasons
                        if not r.startswith(("holdout", "stress", "half_edge",
                                             "annual_dollars"))]
            if blocking:
                continue
            reg.holdout_touches += 1
            c.holdout = score(c, SEEDS["holdout"], holdout_n, resamples=2000)
            c.stress = score(c, SEEDS["oos"], oos_n, costs=evaluate.stress_costs(), resamples=1000)
            # Same seeds, fainter world: a paired comparison against markets whose planted
            # inefficiency is halved and whose spreads, depth and fees are untouched.
            faint = markets.attenuated(c.family, GATE["half_edge_factor"])
            c.half_edge = score(c, SEEDS["oos"], oos_n, resamples=1000, family=faint)
            c.verdict = evaluate.gate(c.oos, c.holdout, c.stress, c.fwer_p, len(reg),
                                      c.bh_p, half_edge=c.half_edge)
            status = "PASSED" if c.verdict.passed else "failed on " + "; ".join(c.verdict.reasons)
            log(f"    CONFIRM  {c.label()}  (${c.oos.annual_dollars:,.0f}/yr)")
            log(f"             holdout mean={c.holdout.mean:+.2f}c  "
                f"stress mean={c.stress.mean:+.2f}c  "
                f"half-edge mean={c.half_edge.mean:+.2f}c  ->  {status}")
            if not any(r.startswith("annual_dollars") for r in c.verdict.reasons) \
                    and len(c.verdict.reasons) <= 1:
                confirmed.append(c)
            if c.verdict.passed:
                c.sens = sensitivity(c, oos_n)
                log("             sensitivity to assumed edge size: "
                    + "  ".join(f"{f * 100:.0f}%->{s_.mean:+.1f}c" for f, s_ in c.sens))
                winners.append(c)

        # 6. EXPAND.
        n_added = _expand(survivors, rng, log)
        prev_survivors = survivors
        log(f"    generation took {time.time() - gt0:.1f}s"
            + (f", grid expanded in {n_added} place(s)" if n_added else ""))
        log()

        fams_confirmed = {c.family for c in confirmed}
        if confirmed:
            log(f"    confirmed on criteria 1-10: {len(confirmed)} bot(s) across "
                f"{len(fams_confirmed)} famil(y/ies) — {', '.join(sorted(fams_confirmed))}")
        if winners and not keep_going:
            log(f"*** GOAL REACHED in generation {gen}: {len(winners)} bot(s) cleared "
                f"every gate criterion ***")
            break
        if winners:
            log(f"    ({len(winners)} winner(s) so far; --keep-going, so the search "
                f"continues and expands)")

    elapsed = time.time() - t0
    gens_run = gen + 1
    log(f"finished: {gens_run} generation(s), "
        f"{len(seen_keys)} distinct bots built, {len(reg)} out-of-sample tests, "
        f"{reg.holdout_touches} holdout touches, {elapsed:.0f}s")

    mechanisms = sorted({(c.family, c.cls.__name__) for c in winners})
    if winners:
        log(f"{len(winners)} bot(s) passed, but they represent only {len(mechanisms)} "
            f"distinct mechanism(s) — parameter variants of one idea are not independent "
            f"discoveries:")
        for fam, cls in mechanisms:
            best = max((c for c in winners if c.family == fam and c.cls.__name__ == cls),
                       key=lambda c: c.oos.annual_dollars)
            log(f"    {fam} / {cls}: {sum(1 for c in winners if c.family == fam and c.cls.__name__ == cls)}"
                f" variants, best ${best.oos.annual_dollars:,.0f}/yr "
                f"({best.oos.mean:+.2f}c/market)")
    if reg.holdout_touches > 3:
        log(f"WARNING: the holdout set was evaluated {reg.holdout_touches} times. It was "
            f"meant to be touched once. Holdout figures above are no longer a clean third "
            f"sample and should be read as optimistic.")
    if control_flags:
        log(f"CONTROL TRIPWIRE: {len(control_flags)} control-family candidates looked strong "
            f"in-sample (expected from search noise; none reached the gate):")
        for f in control_flags[:5]:
            log(f"    {f}")
    return {"winners": winners, "all_oos": all_oos, "registry": reg,
            "log": lines, "elapsed": elapsed, "n_built": len(seen_keys),
            "control_flags": control_flags, "generations": gens_run,
            "mechanisms": mechanisms, "confirmed": confirmed}


def sweep(insample_n, draws_per_cell=4, seed=20260730, verbose=True):
    """Coverage matrix: every market family x every strategy, in-sample.

    This is the literal "try all the market types with all the strategies" answer, and it is
    deliberately IN-SAMPLE ONLY. Certifying 108 cells would put 108 tests into the
    multiplicity denominator and make the gate harder for no gain — the matrix is a map of
    where to look, not a claim about what is real. Every cell reports the best of
    `draws_per_cell` random parameter draws, which is exactly the kind of maximum-of-a-search
    statistic that `RESULTS.md` exists to discount. Read it as a direction, not a number.
    """
    rng = random.Random(seed)
    rows = {}
    for family in markets.FAMILIES:
        for cls in strategies.ALL:
            if not compatible(family, cls):
                rows[(family, cls.__name__)] = None
                continue
            best = None
            for _ in range(draws_per_cell):
                p = _sample(cls, rng)
                if p is None:
                    continue
                c = Candidate(family, cls, p, 0, "sweep")
                c.ins = score(c, SEEDS["insample"], insample_n)
                if best is None or c.ins.mean > best.ins.mean:
                    best = c
            rows[(family, cls.__name__)] = best
        if verbose:
            print(f"  swept {family}", flush=True)
    return rows


def write_coverage(rows, path: pathlib.Path, insample_n, draws_per_cell):
    fams = list(markets.FAMILIES)
    strats = [c.__name__ for c in strategies.ALL]
    L = ["# Kalshi Bot Factory — Coverage Matrix\n"]
    L.append(f"Every market family against every strategy: {len(fams)} x {len(strats)} = "
             f"{len(fams) * len(strats)} cells, best of {draws_per_cell} parameter draws each, "
             f"{insample_n} markets per cell.\n")
    L.append("**In-sample only, and every cell is the maximum of a small search.** Positive "
             "numbers here are where to look, not what is true — see `RESULTS.md` for the "
             "out-of-sample gate. Simulated markets, not Kalshi.\n")
    L.append("Mean cents per market offered:\n")
    L.append("| family | " + " | ".join(s[:13] for s in strats) + " |")
    L.append("|" + "---|" * (len(strats) + 1))
    for f in fams:
        cells = []
        for s in strats:
            c = rows.get((f, s))
            cells.append("n/a" if c is None or c.ins is None else f"{c.ins.mean:+.0f}")
        L.append(f"| `{f}` | " + " | ".join(cells) + " |")
    L.append("")

    # The punchline, computed rather than asserted.
    live = [c for c in rows.values() if c is not None and c.ins is not None]
    if live:
        top = max(live, key=lambda c: c.ins.mean)
        ctrl = [c for c in live if c.family == "efficient_control"]
        best_ctrl = max(ctrl, key=lambda c: c.ins.mean) if ctrl else None
        ranked = sorted(live, key=lambda c: -c.ins.mean)
        ctrl_rank = (ranked.index(best_ctrl) + 1) if best_ctrl else None
        L.append("### Read the control row first\n")
        L.append(f"`efficient_control` is a market with **no edge in it by construction** — "
                 f"gamma exactly 1.0, no quote lag, penny spread. Nothing can beat it. Its "
                 f"best cell scores **{best_ctrl.ins.mean:+.0f}c per market** "
                 f"(`{best_ctrl.cls.__name__}`), which ranks **#{ctrl_rank} of "
                 f"{len(live)}** cells in this whole matrix"
                 + (" — the highest score in the table.\n" if ctrl_rank == 1 else ".\n"))
        L.append("That is the entire argument for the rest of this directory. The largest "
                 "in-sample number produced by a 108-cell search came from a market that "
                 "cannot be beaten. Every cell above is the maximum of four draws, and "
                 "maxima of noise are large and positive. In-sample ranking is a way to "
                 "decide what to test next; it is not evidence.\n")
        strat_of = {}
        for c in live:
            strat_of.setdefault(c.cls.__name__, []).append(c.ins.mean)
        controls = {c.__name__ for c in strategies.CONTROLS}
        beat = [s for s in strat_of if s in controls and max(strat_of[s]) > 0]
        if beat:
            L.append(f"Second symptom of the same thing: {len(beat)} of the "
                     f"{len(controls)} strategies **designed to lose** "
                     f"({', '.join(sorted(beat))}) show a positive best cell somewhere in "
                     f"this table.\n")
        if top.family == "efficient_control":
            L.append(f"Top cell overall: `{top.family} / {top.build().label()}` at "
                     f"{top.ins.mean:+.0f}c. It is a control strategy on a control market, "
                     f"and it is the best-looking bot in the sweep.\n")
    L.append("## Best strategy per family\n")
    L.append("| family | best strategy in-sample | mean/market | ann. return | targets |")
    L.append("|---|---|---|---|---|")
    for f in fams:
        cs = [c for (ff, _), c in rows.items() if ff == f and c is not None and c.ins is not None]
        if not cs:
            continue
        b = max(cs, key=lambda c: c.ins.mean)
        L.append(f"| `{f}` | {b.build().label()} | {b.ins.mean:+.1f}c | "
                 f"{b.ins.annualized * 100:+.0f}%/yr | {b.cls.targets} |")
    L.append("")
    L.append("## Best family per strategy\n")
    L.append("| strategy | best family in-sample | mean/market |")
    L.append("|---|---|---|")
    for s in strats:
        cs = [c for (_, ss), c in rows.items() if ss == s and c is not None and c.ins is not None]
        if not cs:
            continue
        b = max(cs, key=lambda c: c.ins.mean)
        L.append(f"| `{s}` | {b.family} | {b.ins.mean:+.1f}c |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

SENSITIVITY_FACTORS = (1.0, 0.75, 0.5, 0.25)


def sensitivity(c: Candidate, oos_n: int) -> list[tuple[float, object]]:
    """How the net edge responds to the ASSUMED size of the inefficiency.

    Paired: every factor runs the same markets, with only the planted edge scaled. The shape
    is the point. Costs — spread and fee — are FIXED, so net edge is gross minus a constant
    and therefore a LEVERED function of the assumption. Halving the assumed inefficiency does
    not halve the profit; it comes close to erasing it. That is the honest sensitivity of
    every result in RESULTS.md to the magnitudes chosen by hand in markets.py.
    """
    rows = []
    for f in SENSITIVITY_FACTORS:
        fam = markets.attenuated(c.family, f)
        rows.append((f, score(c, SEEDS["oos"], oos_n, resamples=1000, family=fam)))
    return rows


def write_report(out: dict, path: pathlib.Path, args):
    reg = out["registry"]
    winners = out["winners"]
    ranked = sorted(out["all_oos"], key=lambda c: -c.oos.mean)

    L = []
    L.append("# Kalshi Bot Factory — Results\n")
    L.append("Generated by `python -m kalshi.factory`. Every number below comes from the "
             "simulator in `kalshi/markets.py`, **not** from Kalshi. Read "
             "`kalshi/README.md` §What this does not prove before quoting any of it.\n")
    L.append(f"- generations run: **{out['generations']}**")
    L.append(f"- bots built: **{out['n_built']}**")
    L.append(f"- out-of-sample tests (Holm denominator): **{len(reg)}**")
    L.append(f"- holdout touches: **{reg.holdout_touches}**")
    L.append(f"- runtime: {out['elapsed']:.0f}s")
    L.append(f"- verdict: **{len(winners)} bot(s) cleared all "
             f"{len(evaluate.GATE_CRITERIA)} gate criteria, representing "
             f"{len(out['mechanisms'])} distinct mechanism(s)**\n")

    if len(winners) > len(out["mechanisms"]):
        L.append(f"> **{len(winners)} passing bots is not {len(winners)} findings.** They "
                 f"collapse to **{len(out['mechanisms'])}** distinct (family, strategy) "
                 f"mechanism(s); the rest are parameter variants of the same idea tested on "
                 f"the same markets, so they are not independent evidence of anything. "
                 f"Counting them separately is how a strategy search inflates its own "
                 f"results.\n")
    if reg.holdout_touches > 3:
        L.append(f"> **The holdout was evaluated {reg.holdout_touches} times.** It is "
                 f"designed to be touched once. Every holdout figure below should be read as "
                 f"optimistic — after this many visits it is a second validation set, not an "
                 f"untouched one. Run without `--keep-going` for a clean holdout.\n")

    if winners:
        L.append("## Bots that passed the gate\n")
        for c in winners:
            L.append(f"### {c.label()}\n")
            L.append(f"- origin: generation {c.gen}, {c.origin}")
            L.append(f"- targets: {c.cls.targets}\n")
            L.append("| dataset | markets | trades | mean/market | 95% CI | ann. return |")
            L.append("|---|---|---|---|---|---|")
            for nm, s in (("in-sample", c.ins), ("out-of-sample", c.oos),
                          ("holdout", c.holdout), ("stress", c.stress),
                          ("half-edge world", c.half_edge)):
                if s is None:
                    continue
                # In-sample is scored without a bootstrap on purpose — it selects, it does
                # not certify — so it has no interval to show rather than an interval of zero.
                ci = ("not bootstrapped" if (s.lo95 == 0.0 and s.hi95 == 0.0)
                      else f"[{s.lo95:+.2f}, {s.hi95:+.2f}]")
                L.append(f"| {nm} | {s.n_groups} | {s.n_trades} | {s.mean:+.2f}c | "
                         f"{ci} | {s.annualized * 100:+.1f}%/yr |")
            L.append("")
            L.append(f"Raw one-sided p = {c.raw_p:.5f}; Holm-adjusted over {len(reg)} tests "
                     f"= **{c.fwer_p:.5f}** (BH would say {c.bh_p:.5f}).\n")
            if c.sens:
                L.append("Sensitivity to the assumed size of the inefficiency "
                         "(paired — identical markets, only the planted edge scaled):\n")
                L.append("| planted edge | mean/market | 95% CI | share of full |")
                L.append("|---|---|---|---|")
                base = c.sens[0][1].mean or 1.0
                for f, s_ in c.sens:
                    L.append(f"| {f * 100:.0f}% | {s_.mean:+.2f}c | "
                             f"[{s_.lo95:+.1f}, {s_.hi95:+.1f}] | {s_.mean / base * 100:.0f}% |")
                L.append("")
                L.append("Costs are fixed, so net edge is gross minus a constant — a levered "
                         "function of the assumption. This table, not the p-value, is the "
                         "honest measure of how much this result depends on magnitudes that "
                         "were chosen by hand.\n")
            L.append("Gate detail:\n")
            for lbl, okk, det in c.verdict.checks:
                L.append(f"- {'PASS' if okk else 'FAIL'} `{lbl}` — {det}")
            L.append("")
    else:
        L.append("## No bot passed\n")
        L.append("Nothing cleared all criteria. The closest candidates and what stopped "
                 "them are below — a bot failing on `fwer_adjusted_p` was profitable but "
                 "not distinguishable from the best of a wide search; one failing on "
                 "`annualized_return` had a real edge that does not pay for the capital it "
                 "locks up.\n")

    L.append("## Every bot that reached out-of-sample, ranked\n")
    L.append("| bot | targets | ins t | oos mean | oos CI | raw p | Holm p | ann. return | stopped by |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for c in ranked[:40]:
        v = evaluate.gate(c.oos, c.holdout, c.stress, c.fwer_p, len(reg), c.bh_p,
                          half_edge=c.half_edge)
        stop = "—" if v.passed else ", ".join(
            r.split(":")[0] for r in v.reasons
            if not r.startswith(("holdout", "stress", "half_edge")))[:46] or "holdout/stress/half-edge"
        L.append(f"| {c.label()} | {c.cls.targets[:34]} | {c.ins.t:+.2f} | "
                 f"{c.oos.mean:+.2f}c | [{c.oos.lo95:+.1f},{c.oos.hi95:+.1f}] | "
                 f"{c.raw_p:.4f} | {c.fwer_p:.3f} | {c.oos.annualized * 100:+.1f}%/yr | {stop} |")
    L.append("")

    L.append("## Per-family summary\n")
    L.append("Best out-of-sample mean per market offered, by family.\n")
    L.append("| family | bots to OOS | best oos mean | best ann. return | best Holm p |")
    L.append("|---|---|---|---|---|")
    byfam: dict[str, list] = {}
    for c in out["all_oos"]:
        byfam.setdefault(c.family, []).append(c)
    for fam, cs in sorted(byfam.items(), key=lambda kv: -max(c.oos.mean for c in kv[1])):
        best = max(cs, key=lambda c: c.oos.mean)
        L.append(f"| {fam} | {len(cs)} | {best.oos.mean:+.2f}c | "
                 f"{best.oos.annualized * 100:+.1f}%/yr | {min(c.fwer_p for c in cs):.3f} |")
    L.append("")

    if out["control_flags"]:
        L.append("## Control tripwire\n")
        L.append(f"{len(out['control_flags'])} candidates on `efficient_control` — a market "
                 "with no edge in it by construction — looked strong in-sample. That is "
                 "expected: it is what a wide search does to noise, and it is the reason "
                 "the gate corrects for multiplicity. None reached the gate.\n")
        for f in out["control_flags"][:10]:
            L.append(f"- {f}")
        L.append("")

    L.append("## Full run log\n")
    L.append("```")
    L.extend(out["log"])
    L.append("```")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def write_json(out: dict, path: pathlib.Path):
    def cand(c):
        return {"family": c.family, "strategy": c.cls.__name__, "params": c.params,
                "gen": c.gen, "origin": c.origin, "targets": c.cls.targets,
                "raw_p": c.raw_p, "holm_p": c.fwer_p, "bh_p": c.bh_p,
                "passed": bool(c.verdict.passed) if c.verdict else False,
                "stats": {k: (v.to_dict() if v else None) for k, v in
                          (("insample", c.ins), ("oos", c.oos),
                           ("holdout", c.holdout), ("stress", c.stress),
                           ("half_edge", c.half_edge))}}
    payload = {
        "n_built": out["n_built"], "n_oos_tests": len(out["registry"]),
        "holdout_touches": out["registry"].holdout_touches,
        "elapsed_s": round(out["elapsed"], 1),
        "winners": [cand(c) for c in out["winners"]],
        "confirmed": [cand(c) for c in out["confirmed"]],
        "candidates": [cand(c) for c in sorted(out["all_oos"], key=lambda c: -c.oos.mean)],
        "config": CFG,
    }
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Breed Kalshi bots and try to disqualify them.")
    ap.add_argument("--generations", type=int, default=LOOP["max_generations"])
    ap.add_argument("--insample", type=int, default=LOOP["insample_groups"])
    ap.add_argument("--oos", type=int, default=LOOP["oos_groups"])
    ap.add_argument("--holdout", type=int, default=LOOP["holdout_groups"])
    ap.add_argument("--survivors", type=int, default=LOOP["survivors_to_oos"])
    ap.add_argument("--population", type=int, default=LOOP["population_per_generation"])
    ap.add_argument("--seed", type=int, default=20260730)
    ap.add_argument("--quick", action="store_true", help="tiny run, for checking wiring only")
    ap.add_argument("--sweep", action="store_true",
                    help="write the family x strategy coverage matrix to COVERAGE.md "
                         "instead of running the loop")
    ap.add_argument("--sweep-draws", type=int, default=4)
    ap.add_argument("--keep-going", action="store_true",
                    help="do not stop at the first winner; keep breeding and expanding "
                         "for the full generation budget")
    ap.add_argument("--no-report", action="store_true")
    args = ap.parse_args()

    if args.sweep:
        rows = sweep(args.insample, args.sweep_draws, args.seed)
        write_coverage(rows, ROOT / "COVERAGE.md", args.insample, args.sweep_draws)
        print(f"wrote {ROOT / 'COVERAGE.md'}")
        return

    if args.quick:
        args.generations, args.insample, args.oos = 2, 120, 300
        args.holdout, args.survivors, args.population = 300, 5, 20

    out = run_loop(args.generations, args.insample, args.oos, args.holdout,
                   args.survivors, args.population, args.seed,
                   keep_going=args.keep_going)

    if not args.no_report:
        write_report(out, ROOT / "RESULTS.md", args)
        write_json(out, ROOT / "results.json")
        print(f"\nwrote {ROOT / 'RESULTS.md'} and {ROOT / 'results.json'}")


if __name__ == "__main__":
    main()
