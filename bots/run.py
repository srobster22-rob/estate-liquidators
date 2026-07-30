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

from bots.botlab import (calibrate, engine, gauntlet, loop, metrics,
                         portfolio, report, state)
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
    every threshold in GauntletConfig."""
    r = calibrate.control_search_fpr(n_candidates=a.candidates, n_finalists=a.finalists,
                                     seed=a.seed)
    print()
    print(f"searched {r['n_candidates']} bots on a market with no exploitable structure")
    print(f"  best screen fitness   {r['best_screen_fitness']:+.2f}")
    print(f"  finalists gauntleted  {r['n_finalists']}")
    print(f"  certified as PROVEN   {r['n_passed']}   (correct answer: 0)")
    print(f"  stopped at            {r['stopped_at']}")
    return 0 if r["n_passed"] == 0 else 3


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


def cmd_report(a) -> int:
    st = state.RunState.load_or_new(a.state, SearchSpace())
    cal = None
    if a.calibrate:
        cal = calibrate.calibrate_all(n_instances=5)
    write = report.write_report(a.report, st, gauntlet.GauntletConfig(), calibration=cal)
    print(f"wrote {a.report} ({len(write.splitlines())} lines)")
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

    p = sub.add_parser("report", help="rewrite REPORT.md from saved state")
    p.add_argument("--report", default=DEFAULT_REPORT)
    p.add_argument("--calibrate", action="store_true")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("selftest", help="run the falsification suite")
    p.set_defaults(fn=cmd_selftest)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
