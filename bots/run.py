#!/usr/bin/env python3
"""Command line for the bot factory.

    python bots/run.py calibrate                     # are the markets sane?
    python bots/run.py loop --target 3               # search until 3 bots are proven
    python bots/run.py loop --target 3 --resume      # continue, ledger intact
    python bots/run.py verify <bot_id>               # re-run the gauntlet on one bot
    python bots/run.py verify <bot_id> --data csvs/  # ... on real bars
    python bots/run.py show <bot_id>                 # genome + evidence
    python bots/run.py report                        # rewrite REPORT.md from state
    python bots/run.py selftest                      # the falsification suite
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from bots.botlab import (calibrate, costlever, decaysweep, engine, gauntlet,
                         loop, metrics, portfolio, report, state)
from bots.botlab.genome import Genome, SearchSpace
from bots.botlab.markets import loader, universe

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, "state")
DEFAULT_STATE = os.path.join(STATE_DIR, "run_state.json")
DEFAULT_REPORT = os.path.join(HERE, "REPORT.md")
DEFAULT_LOG = os.path.join(STATE_DIR, "LOOP_LOG.md")


# --------------------------------------------------------------------------- #

def cmd_calibrate(a) -> int:
    if a.refresh_vol_fix:
        print("measured vol_fix constants — paste into bots/botlab/markets/universe.py:")
        for name, fx in calibrate.refresh_vol_fix():
            cur = universe.get(name).vol_fix
            flag = "" if abs(fx / cur - 1.0) < 0.02 else "   <-- changed"
            print(f"  {name:<26} vol_fix={fx:.4f},   (current {cur:.4f}){flag}")
        return 0
    rows = calibrate.calibrate_all(n_instances=a.instances, include_controls=True)
    print(calibrate.format_table(rows))
    print()
    for r in rows:
        print(f"{r['market']:<26} best net: {r['best_net_bot'][:90]}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)
        print(f"\nwrote {a.json}")
    return 0


def cmd_fpr(a) -> int:
    """The ladder's end-to-end false-positive rate. The number that justifies
    every threshold in GauntletConfig.

    One probe returning 0 bounds the rate loosely — the 95% upper bound on a rate
    with 0 successes in n trials is roughly 3/n, so 0 of 18 only says "below
    ~17%". Repeating over independent seeds is the only thing that tightens it,
    and it is cheap.
    """
    reached: dict[str, int] = {}
    tot_pass = tot_fin = 0
    for k in range(max(a.repeats, 1)):
        seed = a.seed + k * 100_003
        r = calibrate.control_search_fpr(n_candidates=a.candidates,
                                         n_finalists=a.finalists, seed=seed,
                                         verbose=a.repeats == 1)
        tot_pass += r["n_passed"]
        tot_fin += r["n_finalists"]
        for kk, vv in r["stopped_at"].items():
            reached[kk] = reached.get(kk, 0) + vv
        print(f"  seed {seed:>10}: {r['n_finalists']:>3} gauntleted, "
              f"{r['n_passed']} certified, best screen fit {r['best_screen_fitness']:+.2f}",
              flush=True)
    print()
    print(f"searched {a.candidates * max(a.repeats, 1):,} bots over {max(a.repeats, 1)} "
          f"independent probe(s) on a market with no exploitable structure")
    print(f"  finalists gauntleted  {tot_fin}")
    print(f"  certified as PROVEN   {tot_pass}   (correct answer: 0)")
    # Rule of three: with 0 successes in n trials the one-sided 95% upper bound
    # on the rate is ~3/n. Stating it keeps a zero from reading as a proof.
    if tot_pass == 0 and tot_fin:
        print(f"  => false-positive rate 0/{tot_fin}, 95% upper bound ~{3.0 / tot_fin:.1%}")
    print(f"  stopped at            {reached}")
    return 0 if tot_pass == 0 else 3


def cmd_markets(a) -> int:
    for m in universe.all_markets():
        print(m.summary())
        if a.verbose:
            print(f"    {m.notes}")
    return 0


def cmd_loop(a) -> int:
    os.makedirs(STATE_DIR, exist_ok=True)
    if not a.resume and os.path.exists(a.state):
        os.replace(a.state, a.state + ".prev")
        if os.path.exists(a.log):
            os.replace(a.log, a.log + ".prev")
    if a.catalogue:
        # Search a decay rung instead of the shipped catalogue. The panel sweep
        # can only ask whether known strategies survive a faster fade; this asks
        # whether a search can find different ones that do.
        with decaysweep.use_catalogue(a.catalogue):
            print(f"catalogue swapped to decay rung {a.catalogue}: "
                  f"{', '.join(m.name for m in universe.tradeable(4))}")
            return _loop_body(a)
    return _loop_body(a)


def _loop_body(a) -> int:
    cfg = gauntlet.GauntletConfig()
    if a.min_repl_sharpe is not None:
        cfg.min_repl_alpha_sr = a.min_repl_sharpe
    space = SearchSpace(level=a.level, population=a.population)
    st = loop.run_loop(
        target_proven=a.target, max_generations=a.max_generations, state_path=a.state,
        cfg=cfg, space=space, seed=a.seed, patience=a.patience, jobs=a.jobs,
        screen_instances=a.screen_instances, time_budget_s=a.time_budget,
        report_path=a.report, log_path=a.log,
    )
    print()
    funnel = loop.rejection_funnel(st)
    if funnel:
        print("rejection funnel:")
        for k, v in funnel:
            print(f"  {k:<18} {v}")
    if st.proven:
        print()
        bots = [Genome.from_dict(p["genome"]) for p in st.proven]
        print(portfolio.format_summary(portfolio.build(bots)))
    return 0 if st.proven else 2


def _find_bot(st: state.RunState, bot_id: str) -> Genome | None:
    for p in st.proven:
        if p["genome"]["bot_id"].startswith(bot_id):
            return Genome.from_dict(p["genome"])
    for e in st.hall:
        if e["genome"]["bot_id"].startswith(bot_id):
            return Genome.from_dict(e["genome"])
    return None


def cmd_show(a) -> int:
    st = state.RunState.load_or_new(a.state, SearchSpace())
    g = _find_bot(st, a.bot_id)
    if g is None:
        print(f"no bot matching '{a.bot_id}' in {a.state}")
        return 1
    print(f"{g.bot_id}  {g.market}")
    print(f"  {g.describe()}")
    print(f"  warmup {g.warmup()} bars, origin {g.origin}, generation {g.generation}")
    for p in st.proven:
        if p["genome"]["bot_id"] == g.bot_id:
            for s in p["verdict"]["stages"]:
                print(f"  [{'PASS' if s['passed'] else 'FAIL'}] {s['name']:<16} {s['detail']}")
    print()
    print(json.dumps(g.to_dict(), indent=2))
    return 0


def cmd_verify(a) -> int:
    st = state.RunState.load_or_new(a.state, SearchSpace())
    g = _find_bot(st, a.bot_id)
    if g is None:
        print(f"no bot matching '{a.bot_id}'")
        return 1
    cfg = gauntlet.GauntletConfig()
    rng = np.random.default_rng(a.seed)

    if a.data:
        series = loader.load_dir(a.data, template=a.template or g.market)
        print(f"loaded {len(series)} real series from {a.data}")
        print("NOTE: on real bars the gauntlet's replication gates (G2, G7) cannot run — "
              "there is only one history. What follows is the honest subset: "
              "out-of-sample window, cost stress, and the permutation null.\n")
        rows = []
        for s in series:
            n = len(s)
            tr, te = s.slice(0, int(n * gauntlet.TRAIN_FRAC)), s.slice(int(n * gauntlet.TRAIN_FRAC), n)
            p_tr = metrics.evaluate(engine.run(tr, g))
            p_te = metrics.evaluate(engine.run(te, g))
            p_2x = metrics.evaluate(engine.run(te, g, cost_mult=2.0))
            p_dl = metrics.evaluate(engine.run(te, g, exec_delay=2))
            nulls = []
            for _ in range(cfg.n_perm_draws):
                from bots.botlab.markets import generate as _gen
                nulls.append(metrics.evaluate(engine.run(_gen.bootstrap_like(te, rng, cfg.perm_block), g)).alpha_sharpe)
            null_arr = np.asarray(nulls)
            pv = float((np.sum(null_arr >= p_te.alpha_sharpe) + 1) / (null_arr.size + 1))
            rows.append((s.name, len(s), p_tr.alpha_sharpe, p_te.alpha_sharpe,
                         p_2x.alpha_sharpe, p_dl.alpha_sharpe, pv, p_te.max_dd, p_te.n_trades))
        print(f"{'series':<28}{'bars':>7}{'inSR':>7}{'oosSR':>7}{'2xSR':>7}{'dlySR':>7}"
              f"{'permP':>8}{'DD':>8}{'trades':>7}")
        for r in rows:
            print(f"{r[0][:28]:<28}{r[1]:>7}{r[2]:>7.2f}{r[3]:>7.2f}{r[4]:>7.2f}"
                  f"{r[5]:>7.2f}{r[6]:>8.3f}{r[7]:>8.1%}{r[8]:>7}")
        oos = np.array([r[3] for r in rows])
        print(f"\nreal-data OOS alphaSR: median {np.median(oos):+.2f}, "
              f"{np.mean(oos > 0):.0%} of {len(rows)} series positive")
        return 0

    v = gauntlet.run_gauntlet(g, cfg, n_trials=max(st.trials, 1),
                              var_trial_sharpe=st.var_trial_sharpe(), rng=rng)
    print(gauntlet.quick_report(v))
    return 0 if v.passed else 2


def cmd_revalidate(a) -> int:
    """Re-run the full gauntlet for every proven bot at the standard the run
    finished with, and rewrite the ledger from the result.

    Two things drift out of a ledger during a long run. The luck bar rises while
    the search continues, so early certifications were judged against a smaller
    search (F26). And the gauntlet itself changes between sessions, so stored
    verdicts can be the output of code that no longer exists — the margins added
    after F28 were missing from every bot certified before them.

    This makes the ledger self-consistent: every stored verdict is the current
    code's verdict at the closing burden. It is strictly conservative — the
    burden only ever goes up, so a bot can be removed but never added — and it
    refuses to run in the other direction.
    """
    st = state.RunState.load_or_new(a.state, SearchSpace())
    if not st.proven:
        print(f"no proven bots in {a.state}")
        return 1
    cfg = gauntlet.GauntletConfig()
    n_conf, var = max(st.gauntlet_runs, 1), st.var_trial_sharpe()
    print(f"re-running {len(st.proven)} verdicts at the closing standard "
          f"({n_conf} confirmation tests, trial variance {var:.4f})")
    kept = []
    for p_ in st.proven:
        g = Genome.from_dict(p_["genome"])
        old_burden = int(p_["verdict"].get("perf", {}).get("n_confirm_tests", 0))
        if old_burden > n_conf:
            print(f"  {g.bot_id} REFUSED: certified at burden {old_burden} > closing "
                  f"{n_conf}; re-running would lower the bar")
            kept.append(p_)
            continue
        v = gauntlet.run_gauntlet(g, cfg, n_trials=max(st.trials, 1),
                                  var_trial_sharpe=var,
                                  rng=np.random.default_rng(a.seed), cross_market=True,
                                  n_confirm_tests=n_conf)
        tight = min(((sg.margin, sg.name) for sg in v.stages
                     if sg.margin is not None and sg.name in report.SHARPE_GATES),
                    default=(None, ""))
        if v.passed:
            p_["verdict"] = v.to_dict()
            kept.append(p_)
            print(f"  {g.bot_id} PASS   tightest {tight[0]:+.3f} at {tight[1]}")
        else:
            print(f"  {g.bot_id} DROPPED at {v.failed_at}")
    dropped = len(st.proven) - len(kept)
    st.proven = kept
    st.save()
    print()
    print(f"{len(kept)} genomes kept, {dropped} dropped; "
          f"{st.n_distinct_proven()} distinct strategies")
    report.write_report(a.report, st, cfg)
    print(f"report rewritten to {a.report}")
    return 0


def cmd_report(a) -> int:
    # A ledger from `loop --catalogue <rung>` names markets that only exist while
    # that rung is registered, so regenerating its report needs the same swap.
    if a.catalogue:
        with decaysweep.use_catalogue(a.catalogue):
            return _report_body(a)
    return _report_body(a)


def _report_body(a) -> int:
    st = state.RunState.load_or_new(a.state, SearchSpace())
    cal = None
    if a.calibrate:
        cal = calibrate.calibrate_all(n_instances=5)
    write = report.write_report(a.report, st, gauntlet.GauntletConfig(), calibration=cal)
    print(f"wrote {a.report} ({len(write.splitlines())} lines)")
    return 0


def cmd_decay(a) -> int:
    """The decay-rate curve: one fixed panel, seven fade rates, same gates."""
    st = state.RunState.load_or_new(a.state, SearchSpace())
    rungs = a.rungs.split(",") if a.rungs else None
    sw = decaysweep.run_sweep(rungs, proven=st.proven, state_path=a.out,
                              resume=not a.fresh, per_signature=a.per_signature)
    print()
    print(decaysweep.format_curve(sw))
    print()
    print(decaysweep.survival_table(sw))
    print()
    print(decaysweep.format_achievable(sw))
    return 0


def cmd_costgrid(a) -> int:
    """Sweep planted edge and cost independently; test whether survival is a
    function of the ratio, as F21 claims."""
    out = costlever.run(state_path=a.out, n_instances=a.instances)
    print(costlever.format_grid(out["rows"], bar=gauntlet.GauntletConfig().min_repl_alpha_sr))
    print()
    print(costlever.format_fit(out["fit"]))
    return 0


def cmd_selftest(a) -> int:
    import subprocess
    tests = os.path.join(HERE, "tests", "test_botlab.py")
    return subprocess.call([sys.executable, tests])


# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bots/run.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default=DEFAULT_STATE)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("calibrate", help="measure each market family against textbook bots")
    p.add_argument("--instances", type=int, default=5)
    p.add_argument("--json", default=None)
    p.add_argument("--refresh-vol-fix", action="store_true",
                   help="recompute the locked vol_fix constants and print them")
    p.set_defaults(fn=cmd_calibrate)

    p = sub.add_parser("fpr", help="end-to-end false-positive rate on a structureless market")
    p.add_argument("--candidates", type=int, default=2000)
    p.add_argument("--finalists", type=int, default=30)
    p.add_argument("--seed", type=int, default=424242)
    p.add_argument("--repeats", type=int, default=1,
                   help="independent probes; one probe bounds the rate only loosely")
    p.set_defaults(fn=cmd_fpr)

    p = sub.add_parser("markets", help="list the catalogue")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(fn=cmd_markets)

    p = sub.add_parser("loop", help="search until N bots are proven")
    p.add_argument("--target", type=int, default=3)
    p.add_argument("--max-generations", type=int, default=40)
    p.add_argument("--population", type=int, default=160)
    p.add_argument("--level", type=int, default=1)
    p.add_argument("--patience", type=int, default=3)
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--screen-instances", type=int, default=gauntlet.SCREEN_INSTANCES)
    p.add_argument("--time-budget", type=float, default=None, help="seconds")
    p.add_argument("--seed", type=int, default=20260730)
    p.add_argument("--resume", action="store_true", help="continue an existing ledger")
    p.add_argument("--report", default=DEFAULT_REPORT)
    p.add_argument("--log", default=DEFAULT_LOG)
    p.add_argument("--min-repl-sharpe", type=float, default=None,
                   help="override the replication bar (raising it is fine; lowering it is cheating)")
    p.add_argument("--catalogue", default=None,
                   help="search a decay rung instead of the shipped catalogue; "
                        "see `decay --help` for the rung labels")
    p.set_defaults(fn=cmd_loop)

    p = sub.add_parser("show", help="print a bot and its evidence")
    p.add_argument("bot_id")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("verify", help="re-run the gauntlet, optionally on real CSVs")
    p.add_argument("bot_id")
    p.add_argument("--data", default=None, help="CSV file or directory of real OHLCV")
    p.add_argument("--template", default=None, help="catalogue family to inherit costs from")
    p.add_argument("--seed", type=int, default=99)
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("revalidate",
                       help="re-run every proven verdict at the run's closing standard")
    p.add_argument("--report", default=DEFAULT_REPORT)
    p.add_argument("--seed", type=int, default=31337)
    p.set_defaults(fn=cmd_revalidate)

    p = sub.add_parser("report", help="rewrite REPORT.md from saved state")
    p.add_argument("--report", default=DEFAULT_REPORT)
    p.add_argument("--calibrate", action="store_true")
    p.add_argument("--catalogue", default=None,
                   help="register a decay rung first; needed for a ledger produced "
                        "by `loop --catalogue`")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("decay", help="sweep the decay rate and report the survival curve")
    p.add_argument("--rungs", default=None, help="comma-separated subset of rung labels")
    p.add_argument("--out", default=decaysweep.SWEEP_STATE)
    p.add_argument("--fresh", action="store_true", help="ignore cached rungs")
    p.add_argument("--per-signature", type=int, default=3)
    p.set_defaults(fn=cmd_decay)

    p = sub.add_parser("costgrid", help="sweep edge and cost independently (F21's ratio claim)")
    p.add_argument("--out", default=costlever.GRID_STATE)
    p.add_argument("--instances", type=int, default=8)
    p.set_defaults(fn=cmd_costgrid)

    p = sub.add_parser("selftest", help="run the falsification suite")
    p.set_defaults(fn=cmd_selftest)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
