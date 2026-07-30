"""The one data shape everything downstream agrees on."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np


@dataclass
class Series:
    """An OHLCV bar series plus the market it came from.

    Synthetic instances and real CSVs both land here, so the engine, the
    signals and the gauntlet cannot tell them apart. That is the whole point:
    the same validation ladder runs on both.
    """

    name: str
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    spec: "object"                      # markets.spec.MarketSpec
    seed: int | None = None
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = self.close.size
        for name in ("open", "high", "low", "volume"):
            if getattr(self, name).size != n:
                raise ValueError(f"{self.name}: {name} length != close length")
        if n and not np.all(np.isfinite(self.close)):
            raise ValueError(f"{self.name}: non-finite closes")
        if n and float(self.close.min()) <= 0.0:
            raise ValueError(f"{self.name}: non-positive prices")

    def __len__(self) -> int:
        return int(self.close.size)

    @property
    def bars_per_year(self) -> float:
        return float(self.spec.bars_per_year)

    def slice(self, lo: int, hi: int, tag: str = "") -> "Series":
        lo = max(0, int(lo))
        hi = min(len(self), int(hi))
        return replace(
            self,
            name=f"{self.name}{tag}",
            open=self.open[lo:hi].copy(),
            high=self.high[lo:hi].copy(),
            low=self.low[lo:hi].copy(),
            close=self.close[lo:hi].copy(),
            volume=self.volume[lo:hi].copy(),
            meta={**self.meta, "slice": (lo, hi)},
        )

    def returns(self) -> np.ndarray:
        """Close-to-close simple returns, r[0] = 0."""
        r = np.zeros_like(self.close)
        r[1:] = self.close[1:] / self.close[:-1] - 1.0
        return r

    def log_returns(self) -> np.ndarray:
        lr = np.zeros_like(self.close)
        lr[1:] = np.log(self.close[1:] / self.close[:-1])
        return lr

    def realised_vol_ann(self) -> float:
        lr = self.log_returns()[1:]
        if lr.size < 3:
            return 0.0
        return float(lr.std(ddof=1) * np.sqrt(self.bars_per_year))

    def buy_and_hold_ann(self) -> float:
        if len(self) < 2:
            return 0.0
        years = len(self) / self.bars_per_year
        return float((self.close[-1] / self.close[0]) ** (1.0 / years) - 1.0)
