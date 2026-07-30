"""
The Kalshi adapter — the bridge from the simulator to the actual exchange.

    python -m kalshi.live --check                    can we reach the API at all?
    python -m kalshi.live --markets --limit 20       list open markets
    python -m kalshi.live --record BTCD-25JUL30       snapshot a market's book to disk
    python -m kalshi.live --replay recorded.jsonl     backtest recorded books, no simulator
    python -m kalshi.live --paper BTCD-25JUL30 --bot 'hold_favorite(thresh=95,qty=25)'

THIS FILE CANNOT BE TESTED IN THE ENVIRONMENT IT WAS WRITTEN IN. The container has no
route to `api.elections.kalshi.com` — the proxy answers 403 to CONNECT — so every code path
below that touches the network is UNVERIFIED against a live server. The request shapes,
the auth signature construction and the field names come from general knowledge of Kalshi's
v2 REST API and they are exactly the sort of thing that drifts. `--check` exists to be the
first thing anyone runs, and it prints what it actually got rather than asserting success.

WHY THIS MATTERS MORE THAN THE REST OF THE DIRECTORY

`factory.py` proves things about `markets.py`. The edges in `markets.py` were put there by
hand. So the factory's output is a statement about a simulator, and the only way to turn it
into a statement about Kalshi is `--record` (accumulate real books over weeks) then
`--replay` (run the identical strategy objects and the identical fee model over them). The
replay path deliberately reuses `backtest.run`, unmodified, so a bot cannot behave one way
in the simulator and another on real data.

ORDER SAFETY, in the order the checks fire:
  * Paper mode is the default. `--live` is required to place a real order.
  * `--live` additionally requires KALSHI_ALLOW_LIVE_ORDERS=yes in the environment, which
    is a second, separate action a human has to take.
  * `--max-notional` caps the total cents at risk and defaults to 500 ($5).
  * Every order is printed before it is sent, and in paper mode that is all that happens.
There is no argument combination that sends an order without both flags and the env var.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

from . import backtest, fees, markets, strategies

API_BASE = os.environ.get("KALSHI_API_BASE", "https://api.elections.kalshi.com/trade-api/v2")
UA = "estate-liquidators-kalshi-research/1.0"
DEFAULT_MAX_NOTIONAL_CENTS = 500


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

def _sign(method: str, path: str, key_id: str, private_key_pem: str) -> dict:
    """Kalshi request signing: RSA-PSS over `timestamp + METHOD + path`.

    UNVERIFIED against a live server. Needs `cryptography`, which is not a dependency of
    anything else here — read-only endpoints do not require signing, so the import is local
    and only the trading paths pay for it.
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        raise SystemExit(
            "signing needs the `cryptography` package: pip install cryptography\n"
            "(only required for authenticated endpoints; --check and --markets are public)")
    import base64

    ts = str(int(time.time() * 1000))
    msg = (ts + method.upper() + path).encode("utf-8")
    key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    sig = key.sign(
        msg,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode("ascii"),
        "KALSHI-ACCESS-TIMESTAMP": ts,
    }


def _credentials():
    key_id = os.environ.get("KALSHI_KEY_ID")
    pem = os.environ.get("KALSHI_PRIVATE_KEY")
    pem_path = os.environ.get("KALSHI_PRIVATE_KEY_PATH")
    if pem is None and pem_path:
        pem = pathlib.Path(pem_path).read_text(encoding="utf-8")
    return key_id, pem


def request(path: str, method: str = "GET", body: dict | None = None,
            authenticated: bool = False, timeout: float = 20.0):
    """One HTTP call. Returns parsed JSON, or raises with the server's own message.

    Never swallows an error into a default — a trading adapter that returns {} on failure
    will eventually be read as "no positions".
    """
    url = API_BASE.rstrip("/") + path
    headers = {"Accept": "application/json", "User-Agent": UA}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if authenticated:
        key_id, pem = _credentials()
        if not key_id or not pem:
            raise SystemExit("set KALSHI_KEY_ID and KALSHI_PRIVATE_KEY (or "
                             "KALSHI_PRIVATE_KEY_PATH) for authenticated endpoints")
        # Kalshi signs the path including the /trade-api/v2 prefix.
        prefix = "/" + API_BASE.split("://", 1)[-1].split("/", 1)[-1].strip("/")
        headers.update(_sign(method, prefix + path, key_id, pem))
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"HTTP {e.code} from {url}\n{detail}")
    except urllib.error.URLError as e:
        raise SystemExit(
            f"cannot reach {url}: {e.reason}\n"
            "If this is a 403 on CONNECT, the environment's network policy is blocking the "
            "host rather than Kalshi refusing you — this is what happens in the container "
            "this file was written in. Run it somewhere with egress to kalshi.com.")


# ---------------------------------------------------------------------------
# Read-only endpoints
# ---------------------------------------------------------------------------

def check():
    print(f"API base: {API_BASE}")
    key_id, pem = _credentials()
    print(f"credentials: key_id={'set' if key_id else 'MISSING'}, "
          f"private_key={'set' if pem else 'MISSING'}")
    print(f"live orders allowed: {os.environ.get('KALSHI_ALLOW_LIVE_ORDERS') == 'yes'}")
    print("\nGET /markets?limit=1 ...")
    out = request("/markets?limit=1")
    ms = out.get("markets", [])
    print(f"  ok — {len(ms)} market returned")
    if ms:
        m = ms[0]
        print(f"  ticker={m.get('ticker')} status={m.get('status')} "
              f"yes_bid={m.get('yes_bid')} yes_ask={m.get('yes_ask')}")
        missing = [k for k in ("ticker", "yes_bid", "yes_ask", "status", "close_time")
                   if k not in m]
        if missing:
            print(f"  WARNING: expected fields absent from the response: {missing}. "
                  f"The field names in this file are unverified; fix them here.")
    return out


def list_markets(limit=20, series=None, status="open"):
    q = f"/markets?limit={limit}&status={status}"
    if series:
        q += f"&series_ticker={series}"
    out = request(q)
    rows = out.get("markets", [])
    print(f"{'ticker':<28} {'bid':>4} {'ask':>4} {'vol':>8}  title")
    for m in rows:
        print(f"{str(m.get('ticker')):<28} {str(m.get('yes_bid')):>4} "
              f"{str(m.get('yes_ask')):>4} {str(m.get('volume')):>8}  "
              f"{str(m.get('title'))[:60]}")
    return rows


def record(tickers: list[str], out_path: pathlib.Path, interval_s: float, samples: int):
    """Poll order books and append JSONL snapshots.

    This is the only way anything in this directory becomes a statement about the real
    exchange. One run of it is a few minutes of data and proves nothing; the useful version
    is a cron job appending for weeks, which is why the format is append-only JSONL and why
    each line carries its own timestamp rather than relying on line order.
    """
    with out_path.open("a", encoding="utf-8") as fh:
        for i in range(samples):
            ts = time.time()
            for tk in tickers:
                try:
                    ob = request(f"/markets/{tk}/orderbook")
                    m = request(f"/markets/{tk}").get("market", {})
                except SystemExit as e:
                    print(f"  {tk}: {e}", file=sys.stderr)
                    continue
                fh.write(json.dumps({
                    "ts": ts, "ticker": tk,
                    "yes_bid": m.get("yes_bid"), "yes_ask": m.get("yes_ask"),
                    "status": m.get("status"), "result": m.get("result"),
                    "close_time": m.get("close_time"), "orderbook": ob.get("orderbook"),
                }) + "\n")
            fh.flush()
            print(f"  sample {i + 1}/{samples} written", flush=True)
            if i + 1 < samples:
                time.sleep(interval_s)
    print(f"appended to {out_path}")


# ---------------------------------------------------------------------------
# Replay — recorded real books through the unmodified backtester
# ---------------------------------------------------------------------------

def _depth_at_touch(ob, side, price):
    """Contracts resting at `price` on `side` of a Kalshi orderbook payload.

    Kalshi returns {"yes": [[price, size], ...], "no": [[price, size], ...]}. Falls back to
    a nominal 1 contract when the shape is not what is expected, rather than inventing
    liquidity — an unparseable book should make a strategy look worse, never better.
    """
    try:
        levels = (ob or {}).get(side) or []
        for lvl in levels:
            if int(lvl[0]) == int(price):
                return max(1, int(lvl[1]))
    except (TypeError, ValueError, IndexError, KeyError):
        pass
    return 1


def load_replay(path: pathlib.Path) -> list[markets.Group]:
    """Turn recorded snapshots into Groups the existing backtester can run.

    Reuses `markets.Episode` and `backtest.run` deliberately and without modification, so a
    strategy cannot behave differently on real data than it did in the simulator. The
    `true_p` list is filled with the mid purely because Episode carries the field; nothing
    on the execution path reads it, and `View` has no access to it.
    """
    by_ticker: dict[str, list[dict]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("yes_bid") is None or rec.get("yes_ask") is None:
                continue
            by_ticker.setdefault(rec["ticker"], []).append(rec)

    groups, skipped = [], []
    for i, (tk, recs) in enumerate(sorted(by_ticker.items())):
        recs.sort(key=lambda r: r["ts"])
        result = next((r.get("result") for r in reversed(recs) if r.get("result")), None)
        if result not in ("yes", "no"):
            skipped.append(tk)
            continue
        span_h = max((recs[-1]["ts"] - recs[0]["ts"]) / 3600.0, 1e-6)
        fam = markets.Family(
            f"replay:{tk}", f"recorded {tk}", steps=len(recs),
            step_hours=span_h / max(len(recs) - 1, 1), schedule_kind="uniform",
            p0_mu=0.0, p0_sd=1.0, logit_gamma=1.0, underreact_alpha=0.0,
            underreact_decay=0.0, underreact_cap=0.0, quote_noise=0.0,
            spread_lo=1, spread_hi=1, depth_lo=1, depth_hi=1,
            notes="recorded from the live exchange")
        ep = markets.Episode(fam, i, 0, len(recs))
        for r in recs:
            b, a = int(r["yes_bid"]), int(r["yes_ask"])
            ep.bid.append(b)
            ep.ask.append(a)
            ep.depth.append(_depth_at_touch(r.get("orderbook"), "yes", a))
            ep.true_p.append((b + a) / 200.0)
        ep.outcome = 1 if result == "yes" else 0
        groups.append(markets.Group(fam, i, [ep]))
    if skipped:
        print(f"skipped {len(skipped)} unsettled market(s): {', '.join(skipped[:6])}"
              + (" ..." if len(skipped) > 6 else ""))
    return groups


def parse_bot(spec: str):
    """'hold_favorite(thresh=95,qty=25)' -> a Strategy instance."""
    name, _, rest = spec.partition("(")
    name = name.strip()
    cls = next((c for c in strategies.ALL if c.__name__ == name), None)
    if cls is None:
        raise SystemExit(f"unknown strategy {name!r}. Available: "
                         + ", ".join(c.__name__ for c in strategies.ALL))
    params = {}
    for part in rest.rstrip(")").split(","):
        if not part.strip():
            continue
        k, _, v = part.partition("=")
        try:
            params[k.strip()] = int(v)
        except ValueError:
            params[k.strip()] = float(v)
    return cls(**params)


def replay(path: pathlib.Path, bot_spec: str):
    from . import evaluate
    groups = load_replay(path)
    if not groups:
        raise SystemExit("no settled markets in that recording — nothing to replay. "
                         "A market has to close and settle before it can be scored.")
    strat = parse_bot(bot_spec)
    res = backtest.run(groups, strat)
    s = evaluate.summarize(res, resamples=2000)
    print(f"replayed {len(groups)} recorded market(s) through {strat.label()}")
    print(f"  {evaluate.fmt_stats(s)}")
    print(f"  fees paid {s.fees_paid}c of {abs(s.gross):d}c gross "
          f"({s.fee_share * 100:.1f}%)")
    print(f"\n  {len(groups)} markets is almost certainly too few to conclude anything. "
          f"The gate in evaluate.py wants {evaluate.GATE['min_trades_oos']} trades before "
          f"it will look at a mean, and that is the bare minimum.")
    return s


# ---------------------------------------------------------------------------
# Paper / live trading
# ---------------------------------------------------------------------------

def trade_once(ticker: str, bot_spec: str, live: bool, max_notional: int):
    """One decision cycle against the current book. Paper unless every guard is satisfied."""
    strat = parse_bot(bot_spec)
    m = request(f"/markets/{ticker}").get("market", {})
    bid, ask = m.get("yes_bid"), m.get("yes_ask")
    if bid is None or ask is None:
        raise SystemExit(f"{ticker}: no two-sided quote to act on (bid={bid}, ask={ask})")
    ob = request(f"/markets/{ticker}/orderbook").get("orderbook")

    fam = markets.FAMILIES["crypto_hourly"]
    ep = markets.Episode(fam, 0, 0, 1)
    ep.bid, ep.ask = [int(bid)], [int(ask)]
    ep.depth = [_depth_at_touch(ob, "yes", ask)]
    ep.true_p = [(int(bid) + int(ask)) / 200.0]
    gv = backtest.GroupView(markets.Group(fam, 0, [ep]))
    intents = strat.decide(gv, [None])

    print(f"{ticker}: bid={bid} ask={ask} depth_at_ask={ep.depth[0]} status={m.get('status')}")
    if not intents:
        print(f"  {strat.label()} declines to trade this book")
        return []

    orders = []
    for it in intents:
        px = int(ask) if it.side == "yes" else 100 - int(bid)
        qty = min(it.qty, ep.depth[0], max(1, max_notional // max(px, 1)))
        notional = qty * px
        if notional > max_notional:
            print(f"  SKIP {it.side} x{qty} @ {px}c = {notional}c > --max-notional "
                  f"{max_notional}c")
            continue
        orders.append({"ticker": ticker, "action": "buy", "side": it.side,
                       "count": qty, "type": "limit",
                       ("yes_price" if it.side == "yes" else "no_price"): px})
        print(f"  ORDER buy {it.side} x{qty} @ {px}c  (notional {notional}c, "
              f"est. fee {fees.taker_fee_cents(qty, px)}c)")

    if not live:
        print("  PAPER MODE — nothing sent. Pass --live (and set "
              "KALSHI_ALLOW_LIVE_ORDERS=yes) to place these.")
        return orders
    if os.environ.get("KALSHI_ALLOW_LIVE_ORDERS") != "yes":
        raise SystemExit("--live requires KALSHI_ALLOW_LIVE_ORDERS=yes in the environment. "
                         "This is deliberately a second, separate action.")
    for o in orders:
        resp = request("/portfolio/orders", method="POST", body=o, authenticated=True)
        print(f"  sent -> {json.dumps(resp)[:200]}")
    return orders


def main():
    ap = argparse.ArgumentParser(description="Kalshi adapter: check, list, record, replay, trade.")
    ap.add_argument("--check", action="store_true", help="probe the API and print what came back")
    ap.add_argument("--markets", action="store_true", help="list open markets")
    ap.add_argument("--series", help="filter --markets by series ticker")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--record", nargs="+", metavar="TICKER", help="poll these books to JSONL")
    ap.add_argument("--out", default="kalshi_recording.jsonl")
    ap.add_argument("--interval", type=float, default=60.0)
    ap.add_argument("--samples", type=int, default=10)
    ap.add_argument("--replay", metavar="JSONL", help="backtest a recording")
    ap.add_argument("--paper", metavar="TICKER", help="one paper decision cycle")
    ap.add_argument("--bot", default="hold_favorite(thresh=95,enter_frac=0.0,qty=25)")
    ap.add_argument("--live", action="store_true",
                    help="actually place orders (also needs KALSHI_ALLOW_LIVE_ORDERS=yes)")
    ap.add_argument("--max-notional", type=int, default=DEFAULT_MAX_NOTIONAL_CENTS,
                    help="cents at risk per cycle (default 500 = $5)")
    args = ap.parse_args()

    if args.check:
        check()
    elif args.markets:
        list_markets(args.limit, args.series)
    elif args.record:
        record(args.record, pathlib.Path(args.out), args.interval, args.samples)
    elif args.replay:
        replay(pathlib.Path(args.replay), args.bot)
    elif args.paper:
        trade_once(args.paper, args.bot, args.live, args.max_notional)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
