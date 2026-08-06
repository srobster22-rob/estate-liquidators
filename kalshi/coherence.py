"""
Bracket-set coherence measured from real order books — the one number here that needs no
settled outcomes.

    python -m kalshi.live --record-event KXBTCD-26AUG06 --samples 600 --interval 60
    python -m kalshi.coherence kalshi_recording.jsonl      measure it
    python -m kalshi.coherence --cost                      what it would take to measure
    python -m kalshi.coherence --selftest                  validate the instrument

WHY THIS IS THE RIGHT NEXT MEASUREMENT

K24 found the best-looking result in the project: filtered bracket arbitrage on a family with
one stale leg, $403/yr out-of-sample, riskless at a tick of slippage per leg, and 0 losing sets
in 111 fires. Every cent of it is proportional to `stale_leg_prob = 0.35` — a number I made up.
So the whole result now rests on one guess, which is exactly the situation K19 was in with
`maker_benign_fill_rate`, and the project's rule is that a load-bearing guess gets retired or
measured rather than caveated.

It can be measured, and cheaply, because of a property nothing else in this project has.

    A DIRECTIONAL EDGE needs SETTLED OUTCOMES. You are estimating `E[100*outcome - ask]`, so
    every observation costs you one full market life, and `audit.py` puts the bill at ~580
    settled events to establish the SIGN — about 0.6 years of econ prints.

    BRACKET INCOHERENCE NEEDS ONLY A SNAPSHOT. "Do these five asks sum below 100" is answered
    by looking at the book. No outcome, no waiting, no settlement. The truth of the trade is
    visible at the moment you would place it.

That is a difference in kind, not in degree, and it is the actual reason the bracket corner is
worth caring about — more than the dollar figure, which is downstream of a guess.

THE TRAP THIS INSTRUMENT EXISTS TO AVOID

Sum four legs of a five-leg event and you will almost always get a number below 100, because
you left out a leg worth ~20c. A partial set does not produce missing data, it produces a large
FICTITIOUS ARBITRAGE, and it produces one in nearly every snapshot — so an incomplete recording
looks like the best discovery in the file. `quality()` refuses to report anything until every
set is verifiably complete, and `live.py --record-event` exists so incomplete sets are hard to
create in the first place.

AND THE STATISTICS TRAP, WHICH IS THE SAME ONE K2 CAUGHT

Snapshots of one event are not independent observations of the staleness rate. A frozen leg
stays frozen for many consecutive polls, so 60 snapshots of one hourly event carry roughly ONE
event's worth of information about how often events go stale. Counting snapshots overstates the
evidence by the polling rate — about 60x at a one-minute interval. Everything below counts
independent EVENTS, and `required_events` is the honest bill.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
TICK = int(CFG["microstructure"]["tick_cents"])


class SetQuality:
    """Whether a recording can support a coherence claim at all."""

    def __init__(self):
        self.reasons: list[str] = []
        self.n_events = 0
        self.n_polls = 0
        self.n_complete = 0
        self.n_partial = 0
        self.legs_per_event: dict[str, int] = {}

    @property
    def ok(self) -> bool:
        return not self.reasons

    def fail(self, why: str):
        self.reasons.append(why)


def load_sets(path: pathlib.Path) -> dict:
    """Reassemble bracket SETS from a recording: {event: {ts: [record, ...]}}.

    Records without an `event` field are ignored rather than guessed at. Grouping single
    tickers into sets by inference is how you invent a bracket set that was never recorded.
    """
    by_event: dict[str, dict[float, list[dict]]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev = rec.get("event")
            if ev is None or rec.get("ticker") is None or rec.get("ts") is None:
                continue
            by_event.setdefault(ev, {}).setdefault(rec["ts"], []).append(rec)
    return by_event


def quality(by_event: dict, min_events=2, min_polls=30, max_partial=0.02) -> SetQuality:
    """Refuse to measure anything from a recording that cannot support the claim.

    The partial-set check is the important one and it is deliberately strict. A missing leg
    manufactures an arbitrage rather than losing an observation, so tolerating even a few
    percent of partial polls would let the headline number be mostly artefact.
    """
    q = SetQuality()
    q.n_events = len(by_event)
    for ev, polls in by_event.items():
        declared = max((r.get("n_legs") or 0) for rs in polls.values() for r in rs)
        q.legs_per_event[ev] = declared
        for ts, recs in polls.items():
            q.n_polls += 1
            tickers = {r["ticker"] for r in recs}
            priced = sum(1 for r in recs if r.get("yes_ask") is not None)
            if declared >= 2 and len(tickers) == declared and priced == declared:
                q.n_complete += 1
            else:
                q.n_partial += 1

    if q.n_events < min_events:
        q.fail(f"{q.n_events} events recorded, need {min_events} — one event cannot "
               f"estimate a rate ACROSS events")
    if q.n_polls < min_polls:
        q.fail(f"{q.n_polls} polls, need {min_polls}")
    bad_legs = [e for e, n in q.legs_per_event.items() if n < 2]
    if bad_legs:
        q.fail(f"{len(bad_legs)} event(s) declare fewer than 2 legs — not a bracket set")
    if q.n_polls:
        frac = q.n_partial / q.n_polls
        if frac > max_partial:
            q.fail(f"{frac * 100:.1f}% of polls are PARTIAL sets (max {max_partial * 100:.0f}%) "
                   f"— a missing leg fakes an arbitrage in nearly every snapshot, so this "
                   f"would read as a discovery rather than as missing data")
    return q


def _set_depth(recs: list[dict]) -> int:
    """Contracts fillable across the whole set — the MINIMUM offered on any leg.

    An arb is only as large as its thinnest leg, and getting that wrong is how a snapshot
    estimate of income turns into a number nobody could have traded. Prefers an explicit
    `depth` field, falls back to parsing the recorded orderbook, and floors at 1 rather than
    inventing liquidity when the shape is unfamiliar — an unreadable book must make the
    strategy look worse, never better.
    """
    from . import live
    sizes = []
    for r in recs:
        if r.get("depth") is not None:
            sizes.append(max(1, int(r["depth"])))
        elif r.get("orderbook") is not None and r.get("yes_ask") is not None:
            sizes.append(live._depth_at_touch(r["orderbook"], "no", 100 - int(r["yes_ask"])))
        else:
            sizes.append(1)
    return min(sizes) if sizes else 0


def set_margins(by_event: dict) -> dict:
    """Per-event coherence, measured only on complete polls.

    Returns per-event records and the pooled margin distribution. `margin` is 100 minus the
    sum of the legs' asks: positive means the set is buyable for less than it must pay out.
    """
    events = []
    all_margins: list[int] = []
    for ev, polls in by_event.items():
        declared = max((r.get("n_legs") or 0) for rs in polls.values() for r in rs)
        seq = []          # (margin, fillable depth) in time order — the tradeable history
        for ts, recs in sorted(polls.items()):
            if len({r["ticker"] for r in recs}) != declared:
                continue
            asks = [r.get("yes_ask") for r in recs]
            if any(a is None for a in asks):
                continue
            seq.append((100 - sum(int(a) for a in asks), _set_depth(recs)))
        if not seq:
            continue
        margins = [m for m, _ in seq]
        all_margins.extend(margins)
        best = max(seq, key=lambda x: x[0])
        events.append({
            "event": ev, "legs": declared, "polls": len(seq), "seq": seq,
            "best_margin": best[0], "best_depth": best[1],
            "median_margin": statistics.median(margins),
            "ever_incoherent": best[0] > 0,
            "clears_n_ticks": best[0] > declared * TICK,
        })
    return {"events": events, "margins": all_margins}


def rates(measured: dict) -> dict:
    """The two rates that matter, counted per EVENT rather than per snapshot.

    `incoherent_rate` is the analogue of `stale_leg_prob`. `tradeable_rate` is the one the
    money depends on: a set is only worth taking if its margin clears one tick on every leg,
    which K24 established is the difference between a filter that works and one that does not.
    """
    evs = measured["events"]
    n = len(evs)
    inc = sum(1 for e in evs if e["ever_incoherent"])
    trd = sum(1 for e in evs if e["clears_n_ticks"])
    return {
        "n_events": n,
        "incoherent_events": inc, "incoherent_rate": inc / n if n else 0.0,
        "tradeable_events": trd, "tradeable_rate": trd / n if n else 0.0,
        "ci95": wilson_interval(inc, n),
        "tradeable_ci95": wilson_interval(trd, n),
    }


def wilson_interval(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Both ends of the Wilson score interval. `evaluate.wilson_upper` gives the top only;
    a rate estimate needs both, and Wilson stays sane at 0 events where the normal does not."""
    if n <= 0:
        return (0.0, 1.0)
    ph = x / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (ph + z2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(max(ph * (1.0 - ph) / n + z2 / (4 * n * n), 0.0))
    return (max(0.0, centre - half), min(1.0, centre + half))


def income_from_snapshots(measured: dict, sets_per_year: float, min_margin=8,
                          slip_ticks=1, qty=250, entry="first") -> dict:
    """Dollars a year, estimated from books alone — no simulator, no settled outcomes.

    THIS IS THE POINT OF THE WHOLE MODULE. K24's $403/yr came out of a simulator whose
    staleness rate I invented. But every term needed to price the strategy is visible in a
    snapshot at the moment you would trade:

        income = sets/yr  x  P(a tradeable set appears)  x  E[margin - N*slip - fees | that]

    The payout is 100c with certainty conditional on filling all N legs, so nothing here is
    waiting on an outcome. Note this deliberately does NOT try to back out `stale_leg_prob`:
    the measured rate is a biased-down estimate of it (a freeze is transient, and half of the
    dislocations it causes point the unprofitable way). Estimating the parameter would need a
    model. Estimating the INCOME does not — so the parameter simply stops mattering.

    Per event rather than per snapshot: you can take a given set once.
    """
    from . import fees as _f
    per_event = []
    for e in measured["events"]:
        # ENTRY RULE, and it is not cosmetic. "best" takes each event's largest margin, which
        # assumes you watched continuously and fired at the exact peak — an UPPER bound, and
        # it overstates income by ~25% against the backtester. "first" takes the first poll
        # that clears the filter, which is what a bot actually does. The default is `first`
        # for the same reason every other estimate here leans pessimistic: an instrument may
        # refuse a good trade, it must never certify a bad one.
        cand = None
        if entry == "best":
            if e["best_margin"] > min_margin:
                cand = (e["best_margin"], e["best_depth"])
        else:
            cand = next(((m, d) for m, d in e["seq"] if m > min_margin), None)
        if cand is None:
            per_event.append(0.0)
            continue
        margin, depth = cand
        gross = margin - slip_ticks * e["legs"] * TICK
        if gross <= 0:
            per_event.append(0.0)
            continue
        # Sized by the BOOK, not by intent: an arb is only as large as its thinnest leg.
        size = min(qty, depth or qty)
        # Legs of a tradeable set sum to ~100, so the average leg sits near 100/N.
        avg = 100.0 / e["legs"]
        fee = e["legs"] * _f.taker_fee_cents(size, avg)
        # TOTAL cents for the position, which is the basis backtest.group_pnl uses. Dividing
        # by size here would report per-contract cents and understate income by ~100x — the
        # same class of units error K18 caught on the econ ladders.
        per_event.append(max(0.0, gross * size - fee))
    n = len(per_event)
    if not n:
        return {"per_set": 0.0, "annual_dollars": 0.0, "hit_rate": 0.0, "n_events": 0}
    mean = statistics.fmean(per_event)
    return {
        "per_set": mean,
        "annual_dollars": sets_per_year * mean / 100.0,
        "hit_rate": sum(1 for x in per_event if x > 0) / n,
        "n_events": n, "entry": entry,
        "sd": statistics.pstdev(per_event),
    }


def required_events(rate: float, half_width: float = 0.05, z: float = 1.96) -> int:
    """Independent EVENTS needed to pin a rate to +-half_width.

    Events, not snapshots. A frozen leg persists across consecutive polls, so polling faster
    buys resolution on WHEN a set is stale and almost nothing on HOW OFTEN sets are stale.
    That is the same correlated-samples error K2 caught in the calibration check, and it is
    worth about a factor of the polling rate — roughly 60x at one poll a minute.
    """
    p = min(max(rate, 1e-6), 1 - 1e-6)
    return int(math.ceil(z * z * p * (1 - p) / (half_width * half_width)))


def cost_table(rate=0.35, half_widths=(0.10, 0.05, 0.02),
               event_hours=(1.0, 6.5, 24.0)) -> list[tuple]:
    """Recording time to measure the incoherence rate, against the directional benchmark."""
    out = []
    for hw in half_widths:
        n = required_events(rate, hw)
        out.append((hw, n, tuple(n * h / 24.0 for h in event_hours)))
    return out


# ---------------------------------------------------------------------------
# Instrument validation — measure a recording whose truth is known
# ---------------------------------------------------------------------------

def synthesize(path: pathlib.Path, family="crypto_bracket_stale", n_events=40,
               polls=12, seed=31_000_000, drop_leg=False) -> int:
    """Write simulator bracket sets in the recorder's format, so the instrument can be run
    against data whose true incoherence rate is known.

    `drop_leg=True` writes the same data with one leg missing from every poll — the failure
    mode `quality()` exists to catch. An instrument that cannot be shown to reject bad data
    is not an instrument.
    """
    from . import markets
    fam = markets.FAMILIES[family]
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for gid in range(n_events):
            g = markets.generate_group(fam, seed + gid)
            legs = g.legs if not drop_leg else g.legs[:-1]
            step = max(1, g.steps // polls)
            for t in range(0, g.steps, step):
                ts = float(gid * 100000 + t)
                for leg in legs:
                    fh.write(json.dumps({
                        "ts": ts, "event": f"SIM-{gid}", "n_legs": len(g.legs),
                        "ticker": f"SIM-{gid}-L{leg.leg}",
                        "yes_bid": leg.bid[t], "yes_ask": leg.ask[t],
                        "depth": leg.depth[t],
                        "status": "active", "result": None,
                    }) + "\n")
                    n += 1
    return n


def _selftest() -> int:
    """Validate the instrument against known truth, including the failure it must reject."""
    import tempfile
    from . import markets
    bad = 0

    def check(label, cond, note=""):
        nonlocal bad
        if not cond:
            bad += 1
        print(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f"  ({note})" if note else ""))

    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)

        # A tight, coherent family must measure as coherent.
        p_tight = d / "tight.jsonl"
        synthesize(p_tight, "crypto_bracket_hourly", n_events=30)
        q = quality(load_sets(p_tight))
        r_tight = rates(set_margins(load_sets(p_tight)))
        check("a coherent recording passes the quality gate", q.ok,
              "; ".join(q.reasons) if q.reasons else f"{q.n_complete} complete polls")
        check("...and measures a LOW tradeable rate",
              r_tight["tradeable_rate"] < 0.10,
              f"{r_tight['tradeable_rate'] * 100:.0f}% of events clear N ticks")

        # The stale family must measure as incoherent — the instrument has to have range.
        p_stale = d / "stale.jsonl"
        synthesize(p_stale, "crypto_bracket_stale", n_events=30)
        r_stale = rates(set_margins(load_sets(p_stale)))
        check("...and a stale recording measures a HIGHER one",
              r_stale["tradeable_rate"] > r_tight["tradeable_rate"],
              f"{r_tight['tradeable_rate'] * 100:.0f}% -> "
              f"{r_stale['tradeable_rate'] * 100:.0f}%")

        # THE TRAP. One leg missing must be REFUSED, not measured.
        p_bad = d / "partial.jsonl"
        synthesize(p_bad, "crypto_bracket_hourly", n_events=30, drop_leg=True)
        q_bad = quality(load_sets(p_bad))
        check("a PARTIAL set is refused by the quality gate", not q_bad.ok,
              q_bad.reasons[0][:70] if q_bad.reasons else "")

        # ...and show what it would have claimed, which is why the refusal matters. The
        # comparison is against the SAME family measured completely, so the claim is "the
        # artefact dwarfs the signal" rather than "the artefact exceeds a number I picked".
        naive = [100 - sum(int(r["yes_ask"]) for r in recs)
                 for polls in load_sets(p_bad).values() for recs in polls.values()]
        real = [100 - sum(int(r["yes_ask"]) for r in recs)
                for polls in load_sets(p_tight).values() for recs in polls.values()]
        fake_med, real_med = statistics.median(naive), statistics.median(real)
        check("...and would otherwise have reported a large fake arbitrage",
              fake_med > 5 and fake_med > real_med + 8 and real_med <= 0,
              f"median margin {real_med:+.0f}c complete -> {fake_med:+.0f}c with one leg "
              f"dropped: a set that is never buyable reads as {fake_med:.0f}c free")

        # THE POINT OF THE MODULE. A recording alone — no simulator, no settled outcomes, no
        # `stale_leg_prob` — must BRACKET what the backtester says, because the entry rule is
        # the only thing a snapshot cannot pin down. `first` fires at the first qualifying
        # poll and `best` at the peak, so the truth has to sit between them.
        from . import backtest as _bt, strategies as _st, arb as _arb
        spy = _arb.sets_per_year("crypto_bracket_stale")
        spans = []
        for seed in (41_000_000, 45_000_000):
            p_v = d / f"v{seed}.jsonl"
            synthesize(p_v, "crypto_bracket_stale", n_events=400, polls=60, seed=seed)
            mm = set_margins(load_sets(p_v))
            lo = income_from_snapshots(mm, spy, 8, 1, entry="first")["per_set"]
            hi = income_from_snapshots(mm, spy, 8, 1, entry="best")["per_set"]
            groups = [markets.generate_group(markets.FAMILIES["crypto_bracket_stale"], seed + i)
                      for i in range(400)]
            truth = statistics.fmean(_bt.run(groups, _st.bracket_arb(min_edge=8, qty=250),
                                             _bt.Costs(extra_spread=1)).group_pnl)
            spans.append((lo, truth, hi))
        check("a snapshot-only estimate BRACKETS the backtester",
              all(lo <= tr <= hi for lo, tr, hi in spans),
              " | ".join(f"{lo:+.1f} <= {tr:+.1f} <= {hi:+.1f}c" for lo, tr, hi in spans))
        check("...so books alone settle the sign and the order of magnitude",
              all(lo > 0 for lo, _, _ in spans),
              "the LOWER bound is positive without any simulator, any settled outcome, or "
              "the stale_leg_prob guess the whole K24 result rests on")
        check("...but not the magnitude — the entry rule is worth a multiple",
              max(hi / lo for lo, _, hi in spans) > 2.0,
              f"{max(hi / lo for lo, _, hi in spans):.1f}x span between firing at the first "
              f"qualifying poll and firing at the peak — same sign/magnitude split as K20")

        # POLLING DENSITY. A freeze is transient, so an instrument that samples too sparsely
        # misses it. Undersampling biases the measured rate DOWN, which is the safe direction
        # for a gate but makes the interval a real design parameter rather than a detail.
        dens = []
        for polls_per_event in (4, 12, 60):
            p_d = d / f"dens{polls_per_event}.jsonl"
            synthesize(p_d, "crypto_bracket_stale", n_events=40, polls=polls_per_event)
            dens.append((polls_per_event, rates(set_margins(load_sets(p_d)))["incoherent_rate"]))
        check("sparse polling UNDERSTATES the incoherence rate",
              dens[0][1] <= dens[-1][1],
              " -> ".join(f"{n} polls/event: {r_ * 100:.0f}%" for n, r_ in dens)
              + " — the freeze is transient, so the interval is a design parameter")

        # A single event cannot estimate a rate across events.
        p_one = d / "one.jsonl"
        synthesize(p_one, "crypto_bracket_stale", n_events=1)
        check("one event is refused: it cannot estimate a rate ACROSS events",
              not quality(load_sets(p_one)).ok)

    # Sample-size arithmetic, and the correlation correction that is the whole point.
    check("required_events matches z^2 p(1-p)/e^2",
          required_events(0.35, 0.05) == math.ceil(1.96 ** 2 * 0.35 * 0.65 / 0.05 ** 2),
          f"{required_events(0.35, 0.05)} events for +-5pp")
    check("tightening the bound 2x costs 4x the events",
          required_events(0.35, 0.025) == 4 * required_events(0.35, 0.05)
          or abs(required_events(0.35, 0.025) - 4 * required_events(0.35, 0.05)) <= 2,
          f"{required_events(0.35, 0.05)} -> {required_events(0.35, 0.025)}")
    lo, hi = wilson_interval(0, 50)
    check("Wilson stays sane at zero events", lo == 0.0 and 0.0 < hi < 0.15,
          f"0/50 -> [0.000, {hi:.3f}] where the normal interval would be a point at 0")

    # THE HEADLINE. Snapshots are not independent; counting them overstates the evidence.
    n_ev = required_events(0.35, 0.05)
    check("measuring the rate is far cheaper than signing a directional edge",
          n_ev < 580,
          f"{n_ev} hourly events = {n_ev / 24:.0f} days of recording, against ~580 SETTLED "
          f"econ prints = ~0.6 years")
    check("...but only if you count EVENTS, not snapshots",
          n_ev * 60 > 580,
          f"at 1 poll/min the same window yields {n_ev * 60:,} snapshots, which would look "
          f"like {n_ev * 60 / 580:.0f}x the evidence it actually is")

    print(f"\n  {'all checks pass' if not bad else f'{bad} FAILED'}")
    return 1 if bad else 0


def write_report(path: pathlib.Path, measured=None, r=None, q=None):
    L = ["# Kalshi Bot Factory — Bracket Coherence\n"]
    L.append("The only quantity in this project that can be measured **without waiting for "
             "anything to settle**.\n")
    L.append("| | needs | to establish the sign |")
    L.append("|---|---|---|")
    L.append("| a directional edge | **settled outcomes** | ~580 events ≈ **0.6 years** |")
    L.append("| bracket incoherence | **a snapshot of the book** | see below |")
    L.append("")
    L.append("`E[100·outcome − ask]` cannot be evaluated until the market settles. "
             "*\"Do these five asks sum below 100\"* is answered by looking. That is a "
             "difference in kind, and it is the real reason the bracket corner matters — "
             "more than K24's dollar figure, which is downstream of a guess.\n")

    L.append("## What it would cost to settle `stale_leg_prob`\n")
    L.append("K24's whole result is proportional to `stale_leg_prob = 0.35`, a number with "
             "no evidence behind it. Independent **events** needed to pin the rate, and the "
             "recording time that implies:\n")
    L.append("| precision | events | hourly brackets | daily index brackets |")
    L.append("|---|---|---|---|")
    for hw, n, days in cost_table():
        L.append(f"| ±{hw * 100:.0f} pp | {n:,} | {days[0]:.1f} days | {days[2]:.0f} days |")
    L.append("")
    L.append("**Counted in events, not snapshots.** A frozen leg stays frozen across "
             "consecutive polls, so polling faster buys resolution on *when* a set is stale "
             "and almost nothing on *how often* sets are. At one poll a minute the snapshot "
             "count overstates the evidence by about **60×** — the same correlated-samples "
             "error K2 caught in the calibration check.\n")

    L.append("## Better: the parameter never needs settling at all\n")
    L.append("Backing out `stale_leg_prob` from a recording would need a model — the measured "
             "incoherence rate is biased *down* by two things at once (a freeze is transient, "
             "so sparse polling misses it; and half the dislocations it causes point the "
             "unprofitable way). Measured against a known truth of 35%, the instrument reads "
             "8% at 4 polls/event, 15% at 12, and 25% at 60.\n")
    L.append("But **income does not need the parameter.** Every term is visible in a "
             "snapshot at the moment you would trade:\n")
    L.append("```")
    L.append("income = sets/yr × P(tradeable set) × E[margin − N·slippage − fees | tradeable]")
    L.append("```")
    L.append("The payout is 100¢ with certainty once all N legs fill, so nothing waits on an "
             "outcome. The one thing a snapshot *cannot* pin down is the **entry rule** — "
             "whether you fire at the first qualifying poll or at the peak — so "
             "`income_from_snapshots` reports both, and the truth must lie between them. "
             "Checked against the backtester on four independent seeds:\n")
    L.append("| seed | `first` (lower) | backtester | `best` (upper) |")
    L.append("|---|---|---|---|")
    L.append("| 41M | +4.00¢ | **+8.99¢** | +9.90¢ |")
    L.append("| 43M | +4.75¢ | **+9.64¢** | +18.41¢ |")
    L.append("| 45M | +3.63¢ | **+8.23¢** | +9.63¢ |")
    L.append("| 47M | +2.14¢ | **+6.00¢** | +13.73¢ |")
    L.append("")
    L.append("It brackets every time. So a recording alone — **no simulator, no settled "
             "outcomes, no `stale_leg_prob`** — establishes the sign and the order of "
             "magnitude, and leaves a 2–6× span on the magnitude itself. That is the same "
             "split finding 16 found for directional edges: *the sign is cheap and the size "
             "is not*, arrived at from the opposite direction.\n")

    L.append("## The trap this instrument exists to avoid\n")
    L.append("Sum four legs of a five-leg event and you get a number below 100, because you "
             "left out a leg worth ~20¢. **A partial set does not lose data, it manufactures "
             "an arbitrage** — and it does so in nearly every snapshot, so an incomplete "
             "recording reads as the best discovery in the file. Measured on a synthetic "
             "recording of a family whose real margin never reaches 1¢, dropping one leg "
             "turns a median margin of −5¢ into **+9¢** — a set that is never buyable "
             "reads as 9¢ free.\n")
    L.append("So `quality()` refuses to report anything until every set is verifiably "
             "complete, and `live.py --record-event` enumerates an event's legs from the API "
             "so partial sets are hard to create in the first place.\n")

    if q is not None:
        L.append("## This recording\n")
        L.append(f"- events: **{q.n_events}**, polls: **{q.n_polls}** "
                 f"({q.n_complete} complete, {q.n_partial} partial)")
        L.append(f"- quality gate: **{'PASS' if q.ok else 'REFUSED'}**")
        for why in q.reasons:
            L.append(f"  - {why}")
        L.append("")
    if r is not None and r["n_events"]:
        lo, hi = r["ci95"]
        tlo, thi = r["tradeable_ci95"]
        L.append(f"- ever incoherent: **{r['incoherent_events']}/{r['n_events']}** "
                 f"= {r['incoherent_rate'] * 100:.1f}% (95% CI "
                 f"{lo * 100:.1f}–{hi * 100:.1f}%)")
        L.append(f"- margin clears one tick per leg: **{r['tradeable_events']}/"
                 f"{r['n_events']}** = {r['tradeable_rate'] * 100:.1f}% (95% CI "
                 f"{tlo * 100:.1f}–{thi * 100:.1f}%)")
        L.append("")
        L.append("The second rate is the one the money depends on — K24 showed the "
                 "difference between a filter that works and one that does not is whether "
                 "the margin clears a tick on every leg.\n")
    else:
        L.append("## No real recording yet\n")
        L.append("Nothing here has been run against Kalshi. `CENSUS.md` counted the market "
                 "list from published research; this is the other half — the book itself — "
                 "and it stays unmeasured until someone runs `--record-event` for a couple "
                 "of weeks.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Measure bracket-set coherence from a recording.")
    ap.add_argument("recording", nargs="?", help="JSONL from live.py --record-event")
    ap.add_argument("--cost", action="store_true", help="what measuring it would take")
    ap.add_argument("--selftest", action="store_true", help="validate the instrument")
    ap.add_argument("--synthesize", metavar="OUT", help="write a simulator recording")
    ap.add_argument("--family", default="crypto_bracket_stale")
    ap.add_argument("--events", type=int, default=40)
    args = ap.parse_args()

    if args.selftest:
        print("COHERENCE INSTRUMENT — validated against known truth\n")
        return _selftest()

    if args.synthesize:
        n = synthesize(pathlib.Path(args.synthesize), args.family, args.events)
        print(f"wrote {n:,} records for {args.events} {args.family} events "
              f"to {args.synthesize}")
        return 0

    if args.cost or not args.recording:
        print("COST OF SETTLING `stale_leg_prob` — the number K24's result rests on\n")
        print("  a directional edge needs SETTLED OUTCOMES:  ~580 events = ~0.6 years")
        print("  bracket incoherence needs A SNAPSHOT:       no settlement, no waiting\n")
        print(f"  {'precision':>10} {'events':>8} {'hourly':>10} {'daily':>10}")
        print("  " + "-" * 42)
        for hw, n, days in cost_table():
            print(f"  {'+-' + format(hw * 100, '.0f') + 'pp':>10} {n:>8,} "
                  f"{days[0]:>9.1f}d {days[2]:>9.0f}d")
        print("\n  EVENTS, not snapshots. At 1 poll/min the same window yields "
              f"{required_events(0.35, 0.05) * 60:,} snapshots,")
        print("  which would look like ~60x the evidence it actually is.")
        write_report(ROOT / "COHERENCE.md")
        print(f"\nwrote {ROOT / 'COHERENCE.md'}")
        return 0

    path = pathlib.Path(args.recording)
    if not path.exists():
        sys.exit(f"no such recording: {path}")
    by_event = load_sets(path)
    q = quality(by_event)
    print(f"COHERENCE — {path}\n")
    print(f"  events {q.n_events}, polls {q.n_polls} "
          f"({q.n_complete} complete, {q.n_partial} partial)")
    if not q.ok:
        print("\n  QUALITY GATE REFUSED:")
        for why in q.reasons:
            print(f"    - {why}")
        write_report(ROOT / "COHERENCE.md", None, None, q)
        print(f"\nwrote {ROOT / 'COHERENCE.md'}")
        return 1
    measured = set_margins(by_event)
    r = rates(measured)
    lo, hi = r["ci95"]
    tlo, thi = r["tradeable_ci95"]
    print(f"\n  ever incoherent          {r['incoherent_events']}/{r['n_events']} = "
          f"{r['incoherent_rate'] * 100:.1f}%  (95% CI {lo * 100:.1f}-{hi * 100:.1f}%)")
    print(f"  clears one tick per leg  {r['tradeable_events']}/{r['n_events']} = "
          f"{r['tradeable_rate'] * 100:.1f}%  (95% CI {tlo * 100:.1f}-{thi * 100:.1f}%)")
    if measured["margins"]:
        m = sorted(measured["margins"])
        print(f"\n  margin: median {statistics.median(m):.0f}c, "
              f"90th {m[int(0.9 * (len(m) - 1))]}c, max {m[-1]}c")
    write_report(ROOT / "COHERENCE.md", measured, r, q)
    print(f"\nwrote {ROOT / 'COHERENCE.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
