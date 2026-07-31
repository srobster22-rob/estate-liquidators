"""
Command line for the factory.

    python3 -m cryptobot.run evolve      --markets synthetic --generations 40
    python3 -m cryptobot.run null-test   --trials 3
    python3 -m cryptobot.run fetch       --venue binance --symbol BTCUSDT
    python3 -m cryptobot.run report
    python3 -m cryptobot.run diversity
    python3 -m cryptobot.run verify      --winner 0

`evolve` is the loop the brief asked for: it keeps producing bots and expanding the
search until one survives every gate, or until the generation budget runs out. It
prints the honest outcome either way — "nothing beat the null" is a result, and it
is the correct result far more often than anyone selling a bot factory admits.

`null-test` is the one to run first, and to re-run after touching validate.py. It
points the whole factory at markets built with no exploitable structure at all. The
number of "winners" it produces is the false-positive rate. It should be ~0.
"""

import argparse
import json
import pathlib
import sys

if __package__ in (None, ""):                       # allow `python3 cryptobot/run.py`
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    __package__ = "cryptobot"

from . import bot as botmod           # noqa: E402
from . import evolve                  # noqa: E402
from . import universe as uni         # noqa: E402
from . import validate as val         # noqa: E402
from . import data as dta             # noqa: E402

STATE_DIR = pathlib.Path(__file__).parent / "state"


def build_universe(spec, bars, refresh=False):
    if spec == "synthetic":
        markets = uni.synthetic_universe(bars=bars)
    elif spec == "null":
        markets = uni.null_universe(bars=bars)
    elif spec == "real":
        markets = uni.real_universe(bars=bars, refresh=refresh)
    elif spec.startswith("csv:"):
        markets = uni.csv_universe(spec[4:])
    else:
        raise SystemExit(f"unknown --markets value: {spec}")

    segments, skipped = {}, []
    for key, m in markets.items():
        try:
            segments[key] = uni.split(m)
        except ValueError as exc:
            skipped.append(str(exc))
    if not segments:
        raise SystemExit("no market had enough history to split:\n  "
                         + "\n  ".join(skipped))
    for line in skipped:
        print(f"  skipped: {line}")
    return segments


def cmd_evolve(args):
    segments = build_universe(args.markets, args.bars, args.refresh)
    print(f"\nuniverse: {len(segments)} markets")
    for key in sorted(segments):
        s = segments[key]
        print(f"  {key:<22} train {len(s.train):>6} | val {len(s.validation):>6} "
              f"| vault {len(s.vault):>6}  ({s.full.interval}, {s.full.kind})")

    state_file = pathlib.Path(args.state) if args.state else \
        STATE_DIR / "factory_state.json"
    if args.fresh and state_file.exists():
        state_file.unlink()
        print(f"\nstate reset: {state_file}")

    config = {"population": args.population, "gauntlet_every": args.gauntlet_every,
              "promote": args.promote, "patience": args.patience}
    factory = evolve.Factory(segments, config, seed=args.seed,
                             state_file=state_file)
    print(f"\ncarrying {factory.state['trials']} prior in-sample trials and "
          f"{factory.state['oos_looks']} prior out-of-sample looks\n"
          f"into the multiple-testing correction\n")

    winners = factory.run(args.generations, args.target_winners)

    print("\n" + "=" * 78)
    if not winners:
        print("NO BOT SURVIVED THE GAUNTLET.")
        print("That is a finding, not a failure. Either the universe has no edge "
              "this\nsearch can reach, or the budget was too small. Options, in "
              "descending order\nof honesty: get more/better data, add a strategy "
              "family the zoo is missing,\nor raise --generations. Do not lower "
              "the gates.")
        _print_near_misses(factory)
    else:
        print(f"{len(winners)} BOT(S) PASSED EVERY GATE AND THE VAULT CONFIRMATION")
        for candidate, report, confirmed in winners:
            print("\n" + "-" * 78)
            print(candidate.describe())
            print("\nvalidation slice:")
            print(report.render())
            print("\nvault slice (never touched before this test):")
            print(confirmed.render())
        _print_audit(winners, args.markets)
        print("\n" + "=" * 78)
        print(WINNER_CAVEAT)
    print(f"\nstate: {state_file}")
    return 0


def _print_audit(winners, market_spec):
    """On the synthetic universe we know which markets actually have structure, so
    a set of winners can be checked against the truth. This is the one audit real
    data can never give you: nine of the fourteen markets have nothing to find, and
    a winner sitting on one of those nine is a false positive no matter how good its
    gate report looked."""
    if market_spec != "synthetic":
        return
    print("\n" + "-" * 78)
    print("AUDIT — where the winners landed (synthetic universe only)\n")
    hits = misses = 0
    for candidate, _, _ in winners:
        real = candidate.market_key in uni.STRUCTURED
        reachable = candidate.market_key in uni.REACHABLE
        note = ("structured" if real else "NO STRUCTURE — false positive")
        if real and not reachable:
            note = "structured but cost-eaten — should not have been tradeable"
        print(f"  {candidate.market_key:<20} {candidate.strategy_name:<18} {note}")
        hits += real
        misses += not real
    print(f"\n  {hits} on markets with real structure, {misses} on markets with "
          f"none.")
    if misses:
        print("  A winner on a structureless market is a gauntlet leak. Re-run "
              "null-test\n  before trusting anything this factory has produced.")
    else:
        print("  No winner claimed an edge in a market that hasn't got one.")


def _print_near_misses(factory):
    if not factory.reports:
        print("\nNo candidate was even promoted to the gauntlet.")
        return
    counts = {}
    for r in factory.reports:
        counts[r.first_failure] = counts.get(r.first_failure, 0) + 1
    print("\nwhere the %d promoted candidates died:" % len(factory.reports))
    for name, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>3}  {name}")
    best = max(factory.reports, key=lambda r: sum(g.passed for g in r.gates))
    print("\nfurthest any candidate got:")
    print(best.render())


def cmd_null_test(args):
    """Point the factory at markets with no edge and count the winners.

    This is the calibration run. A validator that lets bots through here is
    manufacturing false positives, and every result it has produced elsewhere is
    worth exactly nothing until it is fixed."""
    total_winners = 0
    for trial in range(args.trials):
        print(f"\n{'='*78}\nNULL TRIAL {trial+1}/{args.trials} "
              f"(markets with zero exploitable structure)\n{'='*78}")
        markets = uni.null_universe(seed=1000 + trial, bars=args.bars)
        segments = {k: uni.split(m) for k, m in markets.items()}
        state_file = STATE_DIR / f"null_{trial}.json"
        if state_file.exists():
            state_file.unlink()
        factory = evolve.Factory(segments, {"population": args.population},
                                 seed=trial + 1, state_file=state_file)
        winners = factory.run(args.generations, target_winners=999)
        total_winners += len(winners)
        print(f"  trial {trial+1}: {len(winners)} false positive(s) from "
              f"{factory.state['trials']} trials")
        _print_near_misses(factory)

    print("\n" + "=" * 78)
    rate = total_winners / max(1, args.trials)
    print(f"FALSE POSITIVES: {total_winners} across {args.trials} null runs "
          f"({rate:.2f} per run)")
    if total_winners == 0:
        print("The gauntlet rejected everything on structureless data. That is the "
              "result\nyou want: a pass on real data means something.")
    else:
        print("The gauntlet let something through on data with NO edge. Treat every "
              "other\nresult from this factory as unproven until the leak is found.")
    return 0 if total_winners == 0 else 1


def _daily_returns(result, market):
    """Collapse a bot's per-bar returns onto a calendar-day grid, so bots trading
    different timeframes can be compared to each other at all."""
    by_day = {}
    for i, r in enumerate(result.net):
        day = market.ts[i] // 86400
        by_day[day] = by_day.get(day, 1.0) * (1.0 + r)
    return {d: v - 1.0 for d, v in by_day.items()}


def _correlation(a, b):
    days = sorted(set(a) & set(b))
    n = len(days)
    if n < 30:
        return None
    xs = [a[d] for d in days]
    ys = [b[d] for d in days]
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return None
    return cov / (vx * vy) ** 0.5


def cmd_diversity(args):
    """Pairwise correlation of the confirmed winners' out-of-sample returns.

    Worth its own command because "the factory found six bots" is a very different
    statement depending on the answer. Six bots correlated at 0.95 are one bot with
    five spare parameter sets: they will draw down together, and running all six
    buys diversification that isn't there. Anything above ~0.7 should be treated as
    a single position for risk purposes."""
    state_file = pathlib.Path(args.state) if args.state else \
        STATE_DIR / "factory_state.json"
    state = evolve.load_state(state_file)
    winners = state.get("winners", [])
    if len(winners) < 2:
        print(f"{len(winners)} confirmed bot(s) — need at least 2 to compare")
        return 1
    segments = build_universe(args.markets, args.bars)

    series, labels = [], []
    for w in winners:
        candidate = botmod.Bot.from_dict(w["bot"])
        seg = segments.get(candidate.market_key)
        if seg is None:
            continue
        pseg = segments.get(candidate.partner_key) if candidate.partner_key else None
        res = candidate.run(seg.vault, pseg.vault if pseg else None)
        series.append(_daily_returns(res, seg.vault))
        labels.append(f"{candidate.strategy_name[:12]}@{candidate.market_key[:16]}")

    width = max(len(x) for x in labels) + 2
    print("\npairwise correlation of daily vault returns\n")
    print(" " * width + "".join(f"{i:>7}" for i in range(len(labels))))
    high, unmeasured = [], []
    for i, lab in enumerate(labels):
        row = f"{i} {lab:<{width-2}}"
        for j in range(len(labels)):
            c = 1.0 if i == j else _correlation(series[i], series[j])
            row += "      ?" if c is None else f"{c:>7.2f}"
            if i < j:
                if c is None:
                    unmeasured.append((labels[i], labels[j]))
                elif abs(c) > 0.7:
                    high.append((labels[i], labels[j], c))
        print(row)

    print()
    if high:
        print("These pairs are effectively the same position:")
        for a, b, c in high:
            print(f"  {a} <-> {b}   r={c:.2f}")
        print("Running them side by side buys no diversification. Size them as one.")
    if unmeasured:
        # A '?' is not a zero. Bots on different timeframes can have vault segments
        # covering disjoint calendar spans, and reporting that as "distinct" would
        # be claiming a measurement that was never made.
        print(f"{len(unmeasured)} pair(s) marked '?' share too few days to "
              f"correlate at all:")
        for a, b in unmeasured:
            print(f"  {a} <-> {b}   NOT MEASURED — do not read as uncorrelated")
    if not high and not unmeasured:
        print("No pair above 0.7 — these are genuinely distinct return streams.")
    return 0


def cmd_fetch(args):
    m = dta.fetch_market(args.venue, args.symbol, interval=args.interval,
                         bars=args.bars, kind=args.kind, refresh=True)
    print(m.describe())
    print(f"cached: {dta.cache_path(args.venue, args.symbol, args.interval, args.kind)}")
    return 0


def cmd_report(args):
    state_file = pathlib.Path(args.state) if args.state else \
        STATE_DIR / "factory_state.json"
    if not state_file.exists():
        print(f"no state at {state_file} — nothing has been run yet")
        return 1
    state = evolve.load_state(state_file)
    print(f"trials evaluated : {state['trials']}   (in-sample search intensity)")
    print(f"out-of-sample looks: {state['oos_looks']}   (this is what gate 10 "
          f"charges for)")
    print(f"gauntlet runs    : {len(state['gauntleted'])}")
    print(f"vault burns      : {state['vault_burns']}")
    print(f"confirmed bots   : {len(state['winners'])}")
    print(f"rejected as redundant: {len(state.get('redundant', []))}   "
          f"(passed every gate, but too correlated with a bot already confirmed)")
    fails = [v for v in state.get("vault_log", []) if not v.get("passed")]
    if fails:
        print(f"vault rejections : {len(fails)}   (passed validation, failed the "
              f"final slice)")
        for v in fails:
            print(f"    {v['bot']['strategy']} on {v['bot']['market']}"
                  f" -> {v['first_failure']}")
    unconf = len(state.get("unconfirmed", []))
    if unconf:
        print(f"passed but NOT confirmed: {unconf}   (vault budget was already "
              f"spent — these are unverified)")
    if state["vault_burns"] > 10:
        print("\n!! the vault has been used more than ten times. It is no longer "
              "clean\n   out-of-sample data. Get more history before trusting the "
              "next pass.")
    for w in state["winners"]:
        print("\n" + "-" * 78)
        print(json.dumps(w, indent=2, default=str))
    return 0


def cmd_verify(args):
    """Re-run a saved winner from scratch on a freshly built universe. If a bot's
    numbers don't reproduce from its JSON genome alone, it isn't a bot, it's an
    anecdote.

    This deliberately does NOT re-run the eleven gates. Running the gauntlet against
    the vault is a consultation of the holdout, and doing it here would have been an
    unlogged one — outside the burn counter, and (because it passed its own
    hardcoded dispersion) against an easier gate 10 than the original. Reproducing
    the recorded numbers needs only the backtest, so that is all it does."""
    state_file = pathlib.Path(args.state) if args.state else \
        STATE_DIR / "factory_state.json"
    state = evolve.load_state(state_file)
    if not state["winners"]:
        print("no confirmed winners to verify")
        return 1
    entry = state["winners"][args.winner]
    candidate = botmod.Bot.from_dict(entry["bot"])
    segments = build_universe(args.markets, args.bars)
    seg = segments.get(candidate.market_key)
    if seg is None:
        print(f"market {candidate.market_key} is not in this universe")
        return 1
    pseg = segments.get(candidate.partner_key) if candidate.partner_key else None
    res = candidate.run(seg.vault, pseg.vault if pseg else None)
    print(candidate.describe())
    print(f"\n  vault sharpe   {res['sharpe']:.4f}")
    print(f"  vault CAGR     {res['cagr']:.4f}")
    print(f"  vault max DD   {res['max_dd']:.4f}")
    print(f"  vault trades   {res['trades']}")
    recorded = entry["vault"]["sharpe"]
    now = res["sharpe"]
    match = abs(recorded - now) < 1e-6
    print(f"\nrecorded vault sharpe {recorded:.4f} | recomputed {now:.4f} | "
          f"{'reproduces exactly' if match else 'MISMATCH'}")
    return 0 if match else 1


WINNER_CAVEAT = """WHAT THIS DOES AND DOES NOT ESTABLISH

  Established: profitable after costs on data withheld from the search; survives
  doubled fees, one bar of execution lag, and +/-20% parameter nudges; positive in
  most regime blocks; beats buy-and-hold on the same window; and clears a Sharpe
  hurdle deflated for every strategy this factory has ever tried.

  Not established: that it will make money. Every number above is retrospective.
  The correct next step is paper trading on live data for at least as long as the
  strategy's average holding period times a few hundred, then a small allocation
  with a hard kill switch, not a large one.

  If this ran on synthetic markets, it establishes only that the harness works."""


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cryptobot", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evolve", help="breed bots until one survives the gauntlet")
    ev.add_argument("--markets", default="synthetic",
                    help="synthetic | real | null | csv:<dir>")
    ev.add_argument("--bars", type=int, default=45000,
                help="reference history for a 1h market; other "
                     "timeframes scale to a similar span")
    ev.add_argument("--generations", type=int, default=40)
    ev.add_argument("--population", type=int, default=60)
    ev.add_argument("--target-winners", type=int, default=1)
    ev.add_argument("--gauntlet-every", type=int, default=5)
    ev.add_argument("--promote", type=int, default=2)
    ev.add_argument("--patience", type=int, default=4)
    ev.add_argument("--seed", type=int, default=1)
    ev.add_argument("--state", default=None)
    ev.add_argument("--fresh", action="store_true",
                    help="reset the trial counter (resets the multiple-testing "
                         "correction — only honest for a genuinely new project)")
    ev.add_argument("--refresh", action="store_true", help="re-fetch real data")
    ev.set_defaults(func=cmd_evolve)

    nt = sub.add_parser("null-test", help="measure the factory's false-positive rate")
    nt.add_argument("--trials", type=int, default=2)
    nt.add_argument("--generations", type=int, default=12)
    nt.add_argument("--population", type=int, default=40)
    nt.add_argument("--bars", type=int, default=45000)
    nt.set_defaults(func=cmd_null_test)

    ft = sub.add_parser("fetch", help="download and cache real candles")
    ft.add_argument("--venue", default="binance", choices=sorted(dta.FETCHERS))
    ft.add_argument("--symbol", default="BTCUSDT")
    ft.add_argument("--interval", default="1h", choices=sorted(dta.SECONDS))
    ft.add_argument("--kind", default="spot", choices=("spot", "perp"))
    ft.add_argument("--bars", type=int, default=8000)
    ft.set_defaults(func=cmd_fetch)

    rp = sub.add_parser("report", help="summarise the factory state")
    rp.add_argument("--state", default=None)
    rp.set_defaults(func=cmd_report)

    dv = sub.add_parser("diversity",
                        help="are the confirmed winners actually different bots?")
    dv.add_argument("--markets", default="synthetic")
    dv.add_argument("--bars", type=int, default=45000)
    dv.add_argument("--state", default=None)
    dv.set_defaults(func=cmd_diversity)

    vf = sub.add_parser("verify", help="reproduce a saved winner from its genome")
    vf.add_argument("--winner", type=int, default=0)
    vf.add_argument("--markets", default="synthetic")
    vf.add_argument("--bars", type=int, default=45000)
    vf.add_argument("--state", default=None)
    vf.set_defaults(func=cmd_verify)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
