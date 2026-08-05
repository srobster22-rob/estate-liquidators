"""
The Kalshi adapter — the bridge from the simulator to the actual exchange.

    python -m kalshi.live --check                    can we reach the API at all?
    python -m kalshi.live --markets --limit 20       list open markets
    python -m kalshi.live --record BTCD-25JUL30       snapshot a market's book to disk
    python -m kalshi.live --replay recorded.jsonl     backtest recorded books, no simulator
    python -m kalshi.live --paper BTCD-25JUL30 --bot 'hold_favorite(thresh=95,qty=25)'

NO REQUEST HERE HAS EVER REACHED KALSHI. The container has no route to the API and Kalshi's
bot protection blocks every other fetch path, so nothing below has been exercised against a
live server. What HAS been done is verify the contract against Kalshi's own published Python
SDK (`kalshi-python` 2.1.4, read from PyPI, which the proxy does allow) — endpoint paths,
host names, field names, the order schema and the signing algorithm all come from that source
rather than from memory. `selftest.py` section 8f pins each one, and the signature is verified
for real: a key is generated, a request is signed, and the signature is checked against the
message Kalshi's SDK would construct.

FOUR THINGS WERE WRONG BEFORE THAT CHECK:

  1. THE SIGNATURE INCLUDED THE QUERY STRING. Kalshi signs `timestamp + METHOD + path` with
     the path taken as `urlparse(url).path` — no query. This file signed `/markets?limit=1`,
     so every authenticated GET carrying a parameter would have been rejected as a bad
     signature, and it would have looked like a credentials problem rather than a bug here.
  2. THE ORDERBOOK PARSER ASSUMED ONE ENCODING. Kalshi's generated SDK exposes the two sides
     under `"true"`/`"false"` (unquoted `yes:`/`no:` keys in the spec, parsed as YAML 1.1
     booleans), and levels appear variously as `[price, count]`, as `{"price", "count"}`, and
     as dollar-denominated strings. All four are accepted now; an unparseable book still
     yields one contract rather than invented liquidity.
  3. NO IDEMPOTENCY KEY. Orders now carry a `client_order_id`. Without one, a retry after a
     timeout can double-fill — the worst failure mode a trading adapter has.
  4. A BROKEN `cryptography` CRASHED THE PROCESS. A build with a missing `_cffi_backend`
     raises pyo3's `PanicException`, which is not an `ImportError` and sailed straight
     through the obvious guard. This container ships exactly that build.

STILL UNVERIFIED, and only a live call can settle it: whether the server actually emits
`yes`/`no` or `true`/`false`, whether `buy_max_cost` counts fees toward the ceiling, and
whether any response field has been renamed since 2.1.4. `--check` prints what it actually
got back and warns on missing fields; run it first, on `--demo`.

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
import uuid
import time
import urllib.error
import urllib.request

from . import backtest, fees, markets, strategies

# Confirmed against Kalshi's official Python SDK (kalshi-python 2.1.4, configuration.py):
# production and demo hosts, both under /trade-api/v2.
PROD_BASE = "https://api.elections.kalshi.com/trade-api/v2"
DEMO_BASE = "https://demo-api.elections.kalshi.com/trade-api/v2"
API_BASE = os.environ.get("KALSHI_API_BASE", PROD_BASE)
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
    except BaseException as e:                      # noqa: BLE001 — see below
        # Deliberately BaseException, not ImportError. A cryptography install with a missing
        # `_cffi_backend` raises pyo3's PanicException, which does NOT inherit from
        # ImportError and so sails straight through the obvious `except ImportError`. This
        # environment has exactly that build, and it took down the whole self-test suite with
        # a Rust stack trace before this was widened.
        raise SystemExit(
            f"signing needs a working `cryptography`: pip install --upgrade cryptography\n"
            f"(import failed with {type(e).__name__}: {e})\n"
            "Only authenticated endpoints need it; --check, --markets and --replay do not.")
    import base64

    ts = str(int(time.time() * 1000))
    # The query string is NOT signed. Kalshi's own SDK does `path = urlparse(url).path`,
    # i.e. it signs `/trade-api/v2/markets`, never `/trade-api/v2/markets?limit=1`. This file
    # used to sign the full path INCLUDING the query, which meant every authenticated GET
    # that carried a parameter would have been rejected for a bad signature — and it would
    # have looked like a credentials problem, not a bug here.
    path = path.split("?", 1)[0]
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

def _orderbook_levels(ob, side: str) -> list:
    """The resting levels on one side, whatever the server chose to call them.

    Kalshi's own generated SDK exposes the two sides under the keys `"true"` and `"false"`
    rather than `"yes"` and `"no"` — the classic YAML 1.1 trap, where unquoted `yes:`/`no:`
    keys in the spec were parsed as booleans and stringified. Which pair actually comes over
    the wire cannot be settled from here (Kalshi 403s every request from this environment),
    so both are accepted. Guessing wrong in one direction silently reports an empty book;
    accepting both costs nothing.
    """
    if not isinstance(ob, dict):
        return []
    for key in (side, {"yes": "true", "no": "false"}[side]):
        v = ob.get(key)
        if isinstance(v, list):
            return v
    return []


def _level_price_count(lvl) -> tuple[int, int] | None:
    """One level -> (price in whole cents, contracts), across all documented encodings.

    Seen in the wild and in Kalshi's own models: `[42, 13]`, `{"price": 42, "count": 13}`,
    and dollar-denominated strings like `["0.4200", "13.00"]`. The string case is detected by
    the decimal point rather than by magnitude, because a bare `1` is one CENT and `"0.01"`
    is the same price written the other way — a magnitude test would turn 1c into 100c.
    """
    if isinstance(lvl, dict):
        p, c = lvl.get("price"), lvl.get("count")
    elif isinstance(lvl, (list, tuple)) and len(lvl) >= 2:
        p, c = lvl[0], lvl[1]
    else:
        return None
    if p is None or c is None:
        return None
    try:
        price = (round(float(p) * 100) if isinstance(p, str) and "." in p
                 else int(round(float(p))))
        return price, int(round(float(c)))
    except (TypeError, ValueError):
        return None


def _depth_at_touch(ob, side, price):
    """Contracts resting at `price` on `side` of a Kalshi orderbook payload.

    Falls back to a nominal 1 contract when the shape is not what is expected, rather than
    inventing liquidity — an unparseable book should make a strategy look worse, never
    better. That fallback is the reason this function is written to be permissive about
    encodings but never optimistic about size.
    """
    for lvl in _orderbook_levels(ob, side):
        got = _level_price_count(lvl)
        if got and got[0] == int(price):
            return max(1, got[1])
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
        # client_order_id is the exchange's idempotency key. Without it a retry after a
        # timeout can double-fill, which is the single worst failure mode a trading adapter
        # has. buy_max_cost is a SERVER-side ceiling on what the order may cost in cents —
        # --max-notional is enforced here in the client, and this makes the exchange enforce
        # it too, so a bug on this side cannot spend more than intended.
        orders.append({"ticker": ticker, "action": "buy", "side": it.side,
                       "count": qty, "type": "limit",
                       "client_order_id": str(uuid.uuid4()),
                       "buy_max_cost": int(notional),
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
    ap.add_argument("--demo", action="store_true",
                    help="use the demo exchange (demo-api.elections.kalshi.com) — separate "
                         "credentials, fake money, the right place to test order placement")
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

    if args.demo:
        global API_BASE
        API_BASE = os.environ.get("KALSHI_DEMO_API_BASE", DEMO_BASE)
        print(f"demo exchange: {API_BASE}\n")

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
