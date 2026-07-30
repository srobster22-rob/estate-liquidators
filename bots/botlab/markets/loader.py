"""Real OHLCV in, same `Series` out.

This is the bridge that makes the rest of the lab worth anything. The synthetic
side proves the machinery can *find* a planted edge and that the gauntlet
rejects a bot when there is no edge to find. Only real data can tell you an
edge exists in the actual market — so the identical gauntlet accepts real bars
here, with no code path knowing the difference.

    python bots/run.py loop --data mydata/ --market-template eq_largecap_daily

Accepted: any CSV with a date-ish column and open/high/low/close (+ optional
volume), in any column order, header names case-insensitive. Rows must be in
ascending or descending date order; descending is flipped.
"""

from __future__ import annotations

import csv
import math
import os
from dataclasses import replace
from datetime import datetime

import numpy as np

from . import universe
from .series import Series
from .spec import MarketSpec

_DATE_KEYS = ("date", "datetime", "time", "timestamp", "dt")
_ALIASES = {
    "open": ("open", "o", "px_open", "adj open", "adj_open"),
    "high": ("high", "h", "px_high"),
    "low": ("low", "l", "px_low"),
    "close": ("close", "c", "px_last", "adj close", "adj_close", "adjclose", "close/last", "price"),
    "volume": ("volume", "vol", "v", "qty", "quantity"),
}
_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S",
                 "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y%m%d")


def _clean_number(text: str) -> float:
    t = text.strip().replace(",", "").replace("$", "").replace("%", "")
    if t in ("", "-", "null", "NULL", "None", "nan", "NaN", "N/A"):
        return float("nan")
    return float(t)


def _parse_date(text: str) -> datetime | None:
    t = text.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    try:                                     # epoch seconds or millis
        v = float(t)
        if v > 1e11:
            v /= 1000.0
        return datetime.utcfromtimestamp(v)
    except (ValueError, OverflowError, OSError):
        return None


def _resolve_columns(header: list[str]) -> dict[str, int]:
    low = [h.strip().strip('"').lower() for h in header]
    cols: dict[str, int] = {}
    for field, names in _ALIASES.items():
        for i, h in enumerate(low):
            if h in names:
                cols[field] = i
                break
    for i, h in enumerate(low):
        if h in _DATE_KEYS:
            cols["date"] = i
            break
    missing = [f for f in ("open", "high", "low", "close") if f not in cols]
    if missing:
        raise ValueError(f"CSV missing required column(s) {missing}; header was {header}")
    return cols


CONTINUOUS_COVER = 0.95     # fraction of calendar days present => a 24/7 market


def infer_bars_per_year(dates: list[datetime]) -> float:
    """Bars per year from the timestamps.

    Two independent questions, and conflating them is what made the first
    version return 6048 for continuous hourly data:

      1. How many bars per *session*?  -> median spacing, or bars per calendar
         date when the session is shorter than the day.
      2. How many sessions per year?   -> 365 if the data covers essentially
         every calendar day (crypto, FX), else 252 (an exchange calendar).
    """
    if len(dates) < 3:
        return 252.0
    gaps = [(dates[i + 1] - dates[i]).total_seconds() for i in range(len(dates) - 1)]
    gaps = [g for g in gaps if g > 0]
    if not gaps:
        return 252.0
    med = float(np.median(gaps))
    if med >= 20 * 86400:
        return 12.0
    if med >= 5 * 86400:
        return 52.0

    span_days = max((dates[-1] - dates[0]).total_seconds() / 86400.0, 1e-9)
    n_dates = len({d.date() for d in dates})
    cover = n_dates / max(span_days, 1.0)
    sessions_per_year = 365.0 if cover >= CONTINUOUS_COVER else 252.0

    if med >= 0.9 * 86400:                      # one bar per session or coarser
        return sessions_per_year
    if cover >= CONTINUOUS_COVER:               # continuous intraday: use the spacing
        return round(86400.0 / med) * 365.0
    return (len(dates) / max(n_dates, 1)) * 252.0   # exchange session: bars per date


def load_csv(path: str, template: str | MarketSpec = "eq_largecap_daily",
             name: str | None = None, bars_per_year: float | None = None) -> Series:
    """Load one CSV. `template` supplies the cost model and constraints — pick
    the catalogue family that most resembles the instrument, or pass a
    `MarketSpec` you built yourself."""
    spec_template = universe.get(template) if isinstance(template, str) else template

    with open(path, newline="", encoding="utf-8-sig") as fh:
        sample = fh.read(8192)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(fh, dialect)
        rows = [r for r in reader if r and any(c.strip() for c in r)]

    if len(rows) < 2:
        raise ValueError(f"{path}: fewer than 2 rows")
    cols = _resolve_columns(rows[0])

    dates: list[datetime] = []
    o, h, l, c, v = [], [], [], [], []
    for row in rows[1:]:
        if len(row) <= max(cols.values()):
            continue
        try:
            vals = [_clean_number(row[cols[f]]) for f in ("open", "high", "low", "close")]
        except ValueError:
            continue
        if any(math.isnan(x) or x <= 0 for x in vals):
            continue
        o.append(vals[0]); h.append(vals[1]); l.append(vals[2]); c.append(vals[3])
        if "volume" in cols:
            try:
                vv = _clean_number(row[cols["volume"]])
            except ValueError:
                vv = float("nan")
            v.append(0.0 if math.isnan(vv) else vv)
        else:
            v.append(0.0)
        if "date" in cols:
            d = _parse_date(row[cols["date"]])
            if d is not None:
                dates.append(d)

    if len(c) < 100:
        raise ValueError(f"{path}: only {len(c)} usable rows; need >= 100")

    if len(dates) == len(c) and len(dates) > 2 and dates[0] > dates[-1]:
        dates = dates[::-1]
        o, h, l, c, v = o[::-1], h[::-1], l[::-1], c[::-1], v[::-1]

    bpy = bars_per_year or (infer_bars_per_year(dates) if len(dates) == len(c) else spec_template.bars_per_year)

    close = np.asarray(c, dtype=float)
    high = np.maximum.reduce([np.asarray(h, float), close, np.asarray(o, float)])
    low = np.minimum.reduce([np.asarray(l, float), close, np.asarray(o, float)])
    volume = np.asarray(v, dtype=float)
    if not np.any(volume > 0):
        volume = np.full(close.size, spec_template.costs.adv_notional / float(close.mean()))

    lr = np.diff(np.log(close))
    vol_ann = float(lr.std(ddof=1) * math.sqrt(bpy)) if lr.size > 2 else spec_template.vol_ann
    label = name or os.path.splitext(os.path.basename(path))[0]

    spec = replace(
        spec_template,
        name=f"real:{label}",
        bars_per_year=bpy,
        n_bars=int(close.size),
        vol_ann=vol_ann,
        # Structure parameters describe the *generator*; on real data there is
        # no generator, so they are zeroed. The oracle ceiling therefore reads
        # 0.00 for real series — that is honest, not a bug: nobody knows the
        # true ceiling of a real market.
        trend_frac=0.0, rev_kappa=0.0, seasonal_amp=0.0, jump_prob=0.0,
        control=False,
        notes=f"real data from {path}; costs/constraints inherited from {spec_template.name}",
    )
    return Series(name=f"real:{label}", open=np.asarray(o, float), high=high, low=low,
                  close=close, volume=volume, spec=spec, seed=None,
                  meta={"path": path, "rows": int(close.size),
                        "start": dates[0].isoformat() if dates else None,
                        "end": dates[-1].isoformat() if dates else None,
                        "generator": "real-csv"})


def load_dir(path: str, template: str | MarketSpec = "eq_largecap_daily") -> list[Series]:
    """Load every CSV in a directory (non-recursive), skipping unreadable ones."""
    out: list[Series] = []
    if os.path.isfile(path):
        return [load_csv(path, template)]
    for fn in sorted(os.listdir(path)):
        if not fn.lower().endswith((".csv", ".txt", ".tsv")):
            continue
        try:
            out.append(load_csv(os.path.join(path, fn), template))
        except (ValueError, OSError) as exc:
            print(f"  ! skipped {fn}: {exc}")
    if not out:
        raise ValueError(f"no usable CSVs found in {path}")
    return out
