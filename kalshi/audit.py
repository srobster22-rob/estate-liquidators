"""
Audit a real recording — the instrument that settles this project.

    python -m kalshi.audit recording.jsonl
    python -m kalshi.audit recording.jsonl --band 95 99

WHAT THIS IS FOR

`SENSITIVITY.md` reduced the whole result to three falsifiable conditions about the real
exchange:

    depth   the book holds >= ~33 contracts at 95-99c
    spread  spreads are no more than ~1.8 ticks wider than modelled
    edge    the real mispricing is >= 72% of what markets.py plants

All three are measurable from recorded books plus settlement outcomes. None of them needs a
working bot, a backtest, or this simulator — which is the point. **The edge in particular is a
direct measurement:** for every contract quoted in the band, take `100 * outcome - ask`. That
is what buying at the ask and holding to settlement actually paid, in cents, with no model in
between. If that number is not positive on real data, nothing else in this directory matters.

So this file deliberately does NOT run a strategy. `--replay` does that. This measures the
inputs, because a backtest on real data can only tell you what one bot did, while these three
numbers tell you whether the whole family of bots was ever plausible.

WHY THE QUALITY GATE COMES FIRST

A recording is not automatically data. Polling drops, processes get killed, markets close
early, and a snapshot taken every 60s across a 10-hour contract that only ran for 20 minutes
is four data points wearing a trenchcoat. Every failure mode there produces a CONFIDENT wrong
number rather than an obvious error, which is the same trap as everything else this project
has walked into. So the audit refuses to report an edge on a recording that fails its quality
checks, and says which check failed.

HOW LONG YOU HAVE TO RECORD

Answered rather than guessed. Buying at price p and holding to settlement pays `100 - p` or
`-p`, so the per-contract variance is `10000 * q * (1 - q)` where q is the true probability —
about 17c of standard deviation at 97c. Detecting an edge of a cent or so therefore needs
thousands of settled observations IN THE BAND, and `required_samples` prints the number and
converts it to months at the census's 534 contracts a year. Expect the answer to be
uncomfortable; that is itself the finding.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics

ROOT = pathlib.Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

# Break-evens from SENSITIVITY.md, restated here so the audit is self-contained.
BREAKEVEN_DEPTH_CONTRACTS = 33      # at the touch, in the 95-99c band
BREAKEVEN_EDGE_FRACTION = 0.72      # of the modelled mispricing
MODEL_EDGE_CENTS = 0.85             # what markets.py plants at the grid boundary
MAX_EXTRA_SPREAD_TICKS = 1.8
MODEL_SPREAD_TICKS = 2.0            # econ_print quotes 1-3


class Quality:
    __slots__ = ("n_snapshots", "n_tickers", "n_settled", "median_snaps_per_market",
                 "median_gap_s", "worst_gap_s", "stale_fraction", "duplicate_fraction",
                 "failures")

    def ok(self) -> bool:
        return not self.failures


def load_snapshots(path: pathlib.Path) -> dict:
    by_ticker: dict[str, list[dict]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("ticker") is None:
                continue
            by_ticker.setdefault(rec["ticker"], []).append(rec)
    for recs in by_ticker.values():
        recs.sort(key=lambda r: r.get("ts", 0))
    return by_ticker


def settled_outcome(recs: list[dict]) -> int | None:
    """1 / 0 / None. `result` is the field Kalshi's SDK exposes on a settled market."""
    res = next((r.get("result") for r in reversed(recs) if r.get("result")), None)
    if res in ("yes", "no"):
        return 1 if res == "yes" else 0
    return None


def quality(by_ticker: dict, min_snaps=10, max_stale=0.5, min_settled=20) -> Quality:
    """Refuse to report a number on a recording that cannot support one."""
    q = Quality()
    q.failures = []
    all_recs = [r for recs in by_ticker.values() for r in recs]
    q.n_snapshots = len(all_recs)
    q.n_tickers = len(by_ticker)
    q.n_settled = sum(1 for recs in by_ticker.values() if settled_outcome(recs) is not None)

    per = [len(recs) for recs in by_ticker.values()] or [0]
    q.median_snaps_per_market = statistics.median(per)

    gaps, stale, dupes, total = [], 0, 0, 0
    for recs in by_ticker.values():
        for a, b in zip(recs, recs[1:]):
            dt = b.get("ts", 0) - a.get("ts", 0)
            total += 1
            if dt <= 0:
                dupes += 1
                continue
            gaps.append(dt)
            # A snapshot identical to its predecessor is a poll that learned nothing. Some of
            # that is real (quiet markets), but a recording that is mostly stale cannot
            # measure a spread or a depth that moves.
            if (a.get("yes_bid"), a.get("yes_ask")) == (b.get("yes_bid"), b.get("yes_ask")):
                stale += 1
    q.median_gap_s = statistics.median(gaps) if gaps else 0.0
    q.worst_gap_s = max(gaps) if gaps else 0.0
    q.stale_fraction = stale / total if total else 0.0
    q.duplicate_fraction = dupes / total if total else 0.0

    if q.median_snaps_per_market < min_snaps:
        q.failures.append(
            f"median {q.median_snaps_per_market:.0f} snapshots per market, need {min_snaps} — "
            f"too coarse to see a book move")
    if q.n_settled < min_settled:
        q.failures.append(
            f"only {q.n_settled} settled markets, need {min_settled} — an edge cannot be "
            f"measured against outcomes that have not happened yet")
    if q.stale_fraction > max_stale:
        q.failures.append(
            f"{q.stale_fraction * 100:.0f}% of consecutive snapshots are identical, over the "
            f"{max_stale * 100:.0f}% limit — polling faster than the book changes")
    if q.duplicate_fraction > 0.02:
        q.failures.append(
            f"{q.duplicate_fraction * 100:.0f}% of snapshots are out of order or duplicated — "
            f"check the recorder for double-appends")
    if q.worst_gap_s > 6 * max(q.median_gap_s, 1):
        q.failures.append(
            f"worst polling gap {q.worst_gap_s / 60:.0f} min against a median of "
            f"{q.median_gap_s / 60:.1f} min — the recorder stopped and restarted")
    return q


def measure_edge(by_ticker: dict, lo=95, hi=99) -> dict:
    """The direct measurement: what buying at the ask and holding to settlement PAID.

    No model, no strategy, no backtest. For each settled market, take the snapshots whose ask
    sits in the band and score `100 * outcome - ask`. One observation per MARKET, not per
    snapshot — snapshots of the same contract share an outcome, and counting each of them
    would inflate n by an order of magnitude and shrink the interval to nothing. That is
    exactly the mistake the calibration self-test made in K2.
    """
    obs, prices = [], []
    for recs in by_ticker.values():
        out = settled_outcome(recs)
        if out is None:
            continue
        in_band = [r for r in recs
                   if r.get("yes_ask") is not None and lo <= int(r["yes_ask"]) <= hi]
        if not in_band:
            continue
        # First qualifying quote, which is what a threshold bot would actually have hit.
        ask = int(in_band[0]["yes_ask"])
        obs.append(100 * out - ask)
        prices.append(ask)
    n = len(obs)
    if n < 2:
        return {"n": n, "mean": 0.0, "sd": 0.0, "lo95": 0.0, "hi95": 0.0, "mean_price": 0.0}
    mean = statistics.fmean(obs)
    sd = statistics.pstdev(obs)
    half = 1.96 * sd / math.sqrt(n)
    return {"n": n, "mean": mean, "sd": sd, "lo95": mean - half, "hi95": mean + half,
            "mean_price": statistics.fmean(prices)}


def measure_depth(by_ticker: dict, lo=95, hi=99) -> dict:
    from .live import _depth_at_touch
    depths = []
    for recs in by_ticker.values():
        for r in recs:
            a = r.get("yes_ask")
            if a is None or not (lo <= int(a) <= hi):
                continue
            d = _depth_at_touch(r.get("orderbook"), "yes", int(a))
            depths.append(d)
    if not depths:
        return {"n": 0, "median": 0.0, "mean": 0.0, "p10": 0.0}
    depths.sort()
    return {"n": len(depths), "median": statistics.median(depths),
            "mean": statistics.fmean(depths), "p10": depths[len(depths) // 10]}


def measure_spread(by_ticker: dict, lo=95, hi=99) -> dict:
    sp = []
    for recs in by_ticker.values():
        for r in recs:
            b, a = r.get("yes_bid"), r.get("yes_ask")
            if b is None or a is None or not (lo <= int(a) <= hi):
                continue
            sp.append(int(a) - int(b))
    if not sp:
        return {"n": 0, "median": 0.0, "mean": 0.0}
    return {"n": len(sp), "median": statistics.median(sp), "mean": statistics.fmean(sp)}


def required_samples(price_cents: float, half_width_cents: float = 0.5) -> int:
    """Settled in-band contracts needed to pin the per-contract edge to +-`half_width`.

    Buying at p and holding pays 100-p or -p, so the per-contract variance is 10000*q*(1-q)
    — about 17c of standard deviation at 97c.
    """
    q = min(max(price_cents / 100.0, 1e-6), 1 - 1e-6)
    sd = 100.0 * math.sqrt(q * (1.0 - q))
    return int(math.ceil((1.96 * sd / max(half_width_cents, 1e-9)) ** 2))


def required_for_sign(mean_cents: float, sd_cents: float) -> float:
    """Observations for a 2-sigma read on the SIGN of the edge.

    THE PRECISION TARGET IS A CHOICE, AND THE FIRST VERSION OF THIS FILE CHOSE BADLY. It
    reported only the samples needed to pin the edge to +-0.5c and called the answer "18
    years", which made the situation look far worse than it is. Two different decisions need
    two different precisions:

        SIGN      is the edge positive at all? This decides whether to trade, and it is
                  reached in about a YEAR on econ_print.
        MAGNITUDE how big is it? This decides sizing and whether it pays for your time, and
                  at +-20% it needs well over a decade.

    Both are true and only the first is a gate. Quoting the stricter one alone was an
    overstatement of the problem.
    """
    if mean_cents <= 0 or sd_cents <= 0:
        return float("inf")
    return (1.96 * sd_cents / mean_cents) ** 2


def required_for_magnitude(mean_cents: float, sd_cents: float, rel=0.20) -> float:
    """Observations to know the edge to +-`rel` of itself."""
    if mean_cents <= 0 or sd_cents <= 0:
        return float("inf")
    return (1.96 * sd_cents / (rel * mean_cents)) ** 2


def audit(path: pathlib.Path, lo=95, hi=99) -> int:
    by_ticker = load_snapshots(path)
    if not by_ticker:
        print(f"no usable snapshots in {path}")
        return 1

    q = quality(by_ticker)
    print(f"RECORDING  {path}")
    print(f"  {q.n_snapshots:,} snapshots across {q.n_tickers:,} markets, "
          f"{q.n_settled:,} settled")
    print(f"  {q.median_snaps_per_market:.0f} snapshots per market (median), "
          f"polling every {q.median_gap_s / 60:.1f} min, worst gap {q.worst_gap_s / 60:.0f} min")
    print(f"  {q.stale_fraction * 100:.0f}% of consecutive snapshots unchanged, "
          f"{q.duplicate_fraction * 100:.0f}% out of order")
    print()
    if not q.ok():
        print("QUALITY GATE FAILED — not reporting an edge on this recording:")
        for f in q.failures:
            print(f"  - {f}")
        print("\nA bad recording produces a confident wrong number rather than an obvious "
              "error, which is why this refuses rather than warns.")
        return 1
    print("quality gate: PASS\n")

    d = measure_depth(by_ticker, lo, hi)
    s = measure_spread(by_ticker, lo, hi)
    e = measure_edge(by_ticker, lo, hi)

    print(f"MEASURED IN THE {lo}-{hi}c BAND — the three conditions from SENSITIVITY.md\n")
    dv = "PASS" if d["median"] >= BREAKEVEN_DEPTH_CONTRACTS else "FAIL"
    print(f"  depth   median {d['median']:.0f} contracts at the touch "
          f"(10th pct {d['p10']:.0f}, n={d['n']:,})")
    print(f"          needs >= {BREAKEVEN_DEPTH_CONTRACTS}  ->  {dv}")
    sv = "PASS" if s["median"] <= MODEL_SPREAD_TICKS + MAX_EXTRA_SPREAD_TICKS else "FAIL"
    print(f"  spread  median {s['median']:.1f} ticks (n={s['n']:,})")
    print(f"          needs <= {MODEL_SPREAD_TICKS + MAX_EXTRA_SPREAD_TICKS:.1f}  ->  {sv}")

    need = BREAKEVEN_EDGE_FRACTION * MODEL_EDGE_CENTS
    if e["n"] < 2:
        print(f"  edge    no settled in-band observations")
        ev = "FAIL"
    else:
        ev = "PASS" if e["lo95"] >= need else "FAIL"
        print(f"  edge    {e['mean']:+.2f}c per contract, 95% CI "
              f"[{e['lo95']:+.2f}, {e['hi95']:+.2f}]  (n={e['n']} settled markets, "
              f"mean price {e['mean_price']:.0f}c)")
        print(f"          needs lower bound >= {need:+.2f}c  ->  {ev}")
        # How long to record. Only contracts that actually pass through the band count, and
        # the recording itself measures that rate — dividing by ALL contracts a year
        # understates the wait by however often a market never reaches 95c.
        contracts_per_yr = CFG["capacity"]["markets_per_year"].get("econ_print", 534)
        in_band_rate = e["n"] / max(q.n_settled, 1)
        per_yr = contracts_per_yr * in_band_rate
        n_sign = required_for_sign(e["mean"], e["sd"])
        n_mag = required_for_magnitude(e["mean"], e["sd"])
        print(f"          {in_band_rate * 100:.0f}% of settled markets ever quote in the band, "
              f"so ~{per_yr:.0f} usable observations a year")
        print(f"          to know the SIGN (trade or not): ~{n_sign:,.0f} obs = "
              f"~{n_sign / max(per_yr, 1e-9):.1f} years")
        print(f"          to know the SIZE to +-20% (sizing): ~{n_mag:,.0f} obs = "
              f"~{n_mag / max(per_yr, 1e-9):.0f} years")
    print()
    verdicts = [dv, sv, ev]
    if all(v == "PASS" for v in verdicts):
        print("ALL THREE CONDITIONS HOLD on this recording. The simulator's inputs are not "
              "contradicted by real data — which is the strongest thing a recording can say, "
              "and still not the same as the bot making money.")
        return 0
    print(f"{sum(1 for v in verdicts if v == 'FAIL')} of 3 conditions FAIL. The headline in "
          f"RESULTS.md does not survive on this data.")
    return 2


def synthesize(family: str, n_groups: int, path: pathlib.Path, seed_base=13_000_000) -> int:
    """Write simulator markets out in the recorder's own JSONL format.

    This exists to VALIDATE THE INSTRUMENT. The audit is supposed to measure depth, spread and
    edge from real books; the only way to know it measures them correctly is to point it at
    data whose answers are already known. `markets.py` plants a specific mispricing at the
    grid boundary, so a synthesised recording has a knowable edge and the audit has to recover
    it. If it cannot recover a planted number, it will not measure a real one.
    """
    from . import markets as _m
    rows = 0
    with path.open("w", encoding="utf-8") as fh:
        for gid in range(n_groups):
            g = _m.generate_group(_m.FAMILIES[family], seed_base + gid)
            for leg_i, ep in enumerate(g.legs):
                tk = f"SIM-{family[:6].upper()}-{gid}-{leg_i}"
                step_s = ep.family.step_hours * 3600.0
                for t in range(ep.n):
                    last = t == ep.n - 1
                    fh.write(json.dumps({
                        "ts": gid * 1_000_000 + t * step_s,
                        "ticker": tk,
                        "yes_bid": ep.bid[t], "yes_ask": ep.ask[t],
                        "status": "settled" if last else "open",
                        "result": ("yes" if ep.outcome else "no") if last else "",
                        "close_time": "",
                        "orderbook": {"yes": [[ep.ask[t], ep.depth[t]]],
                                      "no": [[100 - ep.bid[t], ep.depth[t]]]},
                    }) + "\n")
                    rows += 1
    return rows


def main():
    ap = argparse.ArgumentParser(description="Measure the three conditions from a recording.")
    ap.add_argument("--synthesize", metavar="FAMILY",
                    help="write a simulator recording here instead of auditing, to validate "
                         "the instrument against a known answer")
    ap.add_argument("--groups", type=int, default=400)
    ap.add_argument("recording")
    ap.add_argument("--band", nargs=2, type=int, default=[95, 99], metavar=("LO", "HI"))
    args = ap.parse_args()
    if args.synthesize:
        n = synthesize(args.synthesize, args.groups, pathlib.Path(args.recording))
        print(f"wrote {n:,} synthetic snapshots to {args.recording}")
        raise SystemExit(0)
    raise SystemExit(audit(pathlib.Path(args.recording), args.band[0], args.band[1]))


if __name__ == "__main__":
    main()
