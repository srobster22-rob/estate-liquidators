"""The backtester. Everything the lab claims rests on this file being honest.

Execution model, stated in full because the details are where backtests lie:

  * A decision made from bar t's close executes at bar t+`exec_delay`'s **open**
    (default 1 bar). Nothing is ever filled at a price that was used to
    generate the signal.
  * Positions are leverage (fraction of current equity). Between rebalances the
    position drifts with the market rather than being magically re-levered every
    bar; a trade only happens when the target moves outside `rebalance_band`.
  * Overnight/weekend gaps are carried by the *old* position. If a gap jumps
    through a stop, the fill is the open, not the stop price.
  * Intrabar, stops are checked against the bar's low/high. When both a stop and
    a take-profit are reachable in the same bar, the **stop** is assumed to hit
    first. Fills are the worse of (level, open).
  * Costs: half the quoted spread + commission + square-root impact against the
    bar's own dollar volume, charged on every trade; plus per-bar financing on
    leverage above 1x, borrow on shorts, and perpetual funding where the market
    has it.
  * Equity compounds. A wipeout is recorded as a wipeout, not clipped to zero
    and forgotten.

Known approximation: intrabar sequencing is synthetic (see markets/generate.py).
A strategy whose result depends on tight intrabar stops is therefore flagged as
`stop_sensitive` by the gauntlet rather than trusted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import signals
from .genome import Genome
from .markets.series import Series

RUIN_EQUITY = 0.02          # below 2% of starting capital, the bot is dead
DEFAULT_CAPITAL = 5_000_000.0


@dataclass
class BacktestResult:
    equity: np.ndarray
    ret: np.ndarray
    pos: np.ndarray
    market_ret: np.ndarray
    bars_per_year: float
    start: int
    n_trades: int = 0
    cost_paid: float = 0.0            # cumulative cost in equity fraction
    financing_paid: float = 0.0
    exposure: float = 0.0             # mean |leverage|
    time_in_market: float = 0.0
    halted_frac: float = 0.0
    stop_exits: int = 0
    ruined: bool = False
    market: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def active_ret(self) -> np.ndarray:
        return self.ret[self.start:]

    @property
    def active_market_ret(self) -> np.ndarray:
        return self.market_ret[self.start:]


def score_series(series: Series, g: Genome) -> tuple[np.ndarray, np.ndarray]:
    """(combined score in [-1,1], gate multiplier) — both strictly trailing."""
    n = series.close.size
    raws = []
    weights = []
    for gene in g.genes:
        d = signals.SIGNALS[gene.name]
        v = np.asarray(d.fn(series, gene.params), dtype=float) * float(gene.mode)
        raws.append(np.clip(np.nan_to_num(v, nan=0.0, posinf=1.5, neginf=-1.5), -1.5, 1.5))
        weights.append(max(float(gene.weight), 0.0))

    if not raws:
        return np.zeros(n), np.zeros(n)

    R = np.vstack(raws)
    W = np.asarray(weights)
    if g.combine == "weighted" or R.shape[0] == 1:
        wsum = W.sum() or 1.0
        score = (R * W[:, None]).sum(axis=0) / wsum
    elif g.combine == "vote":
        active = np.abs(R) > 0.10
        votes = np.sign(R) * active
        denom = np.maximum(active.sum(axis=0), 1)
        score = votes.sum(axis=0) / denom
    else:                                                   # unanimous
        sgn = np.sign(R)
        agree = np.all(sgn == sgn[0:1, :], axis=0) & (np.abs(R) > 0.10).all(axis=0)
        score = np.where(agree, np.abs(R).mean(axis=0) * sgn[0], 0.0)

    score = np.clip(score, -1.0, 1.0)

    gate = np.ones(n)
    for f in g.filters:
        d = signals.FILTERS[f.name]
        v = np.asarray(d.fn(series, f.params), dtype=float)
        if d.kind == "gate":
            gate *= np.nan_to_num(v, nan=0.0)
        else:                                               # directional mask
            allow = np.nan_to_num(v, nan=0.0)
            score = np.where((allow != 0) & (np.sign(score) != allow), 0.0, score)

    if g.direction == "long":
        score = np.maximum(score, 0.0)
    elif g.direction == "short":
        score = np.minimum(score, 0.0)

    return score, np.clip(gate, 0.0, 1.0)


def _magnitude(series: Series, g: Genome, score: np.ndarray) -> np.ndarray:
    lr = signals.log_returns(series)
    vol_n = max(int(g.atr_n), 20)
    vol_ann = signals.rstd(lr, vol_n) * math.sqrt(series.bars_per_year)
    vol_ann = np.nan_to_num(vol_ann, nan=0.0)
    vol_ann = np.maximum(vol_ann, 0.01)

    if g.sizing == "fixed":
        mag = np.full(score.size, float(g.base_size))
    elif g.sizing == "proportional":
        mag = float(g.base_size) * np.abs(score)
    else:                                                   # voltarget
        mag = float(g.target_vol) / vol_ann
    return np.clip(mag, 0.0, float(g.max_leverage))


def run(series: Series, g: Genome, cost_mult: float = 1.0, exec_delay: int = 1,
        capital: float = DEFAULT_CAPITAL) -> BacktestResult:
    """Backtest one genome on one series."""
    n = series.close.size
    warm = g.warmup()
    start = min(max(warm, int(g.atr_n) + 2, 2 + exec_delay), n)
    spec = series.spec
    bpy = float(spec.bars_per_year)

    equity_arr = np.ones(n)
    pos_arr = np.zeros(n)
    if start >= n - 5:
        return BacktestResult(equity_arr, np.zeros(n), pos_arr, series.returns(), bpy,
                              start=n, market=spec.name, meta={"error": "series too short for warmup"})

    score, gate = score_series(series, g)
    mag = _magnitude(series, g, score)
    atr_arr = np.nan_to_num(signals.atr(series, int(g.atr_n)), nan=0.0)

    o = series.open.tolist()
    h = series.high.tolist()
    lo_ = series.low.tolist()
    c = series.close.tolist()
    dvol = (series.volume * series.close).tolist()
    sc = score.tolist()
    gt = gate.tolist()
    mg = mag.tolist()
    at = atr_arr.tolist()

    cm = spec.costs
    spread_half = 0.5 * cm.spread_bps * cost_mult / 1e4
    comm = cm.commission_bps * cost_mult / 1e4
    impact_coef = cm.impact_coef_bps * cost_mult / 1e4
    fin_bar = cm.financing_ann * cost_mult / bpy
    borrow_bar = cm.borrow_ann * cost_mult / bpy
    fund_bar = cm.funding_bps_per_bar * cost_mult / 1e4
    min_ticket = cm.min_ticket_bps * cost_mult / 1e4

    entry_thr = float(g.entry_threshold)
    exit_thr = float(g.exit_threshold)
    band = float(g.rebalance_band)
    max_lev = float(g.max_leverage)
    stop_atr = g.stop_atr
    take_atr = g.take_atr
    trail_atr = g.trail_atr
    max_hold = g.max_hold
    min_hold = int(g.min_hold)
    dd_halt = g.dd_halt
    dd_resume = int(g.dd_resume)

    equity = 1.0
    pos = 0.0
    entry_px = 0.0
    entry_atr = 0.0
    extreme = 0.0
    held = 0
    blocked_sign = 0
    halt_until = -1
    peak = 1.0
    n_trades = 0
    cost_paid = 0.0
    fin_paid = 0.0
    stop_exits = 0
    exposure_sum = 0.0
    in_mkt = 0
    halted_bars = 0
    ruined = False

    equity_arr[:start] = 1.0

    for i in range(start, n):
        prev_c = c[i - 1]
        op = o[i]

        # ---- 1. gap: carried by the position we already had -----------------
        if pos != 0.0:
            gap_r = op / prev_c - 1.0
            grow = 1.0 + pos * gap_r
            if grow <= RUIN_EQUITY:
                equity = 0.0
                ruined = True
                equity_arr[i:] = 0.0
                break
            equity *= grow
            pos = pos * (1.0 + gap_r) / grow

        # ---- 2. what do we want to hold through this bar? -------------------
        j = i - exec_delay
        s_j = sc[j] * gt[j]
        m_j = mg[j]

        if blocked_sign != 0 and (abs(s_j) < exit_thr or
                                  (s_j > 0) != (blocked_sign > 0)):
            blocked_sign = 0

        if dd_halt is not None:
            if i < halt_until:
                halted_bars += 1
                target = 0.0
                s_eff = 0.0
            else:
                if halt_until > 0 and i == halt_until:
                    peak = equity                     # fresh start after a halt
                    halt_until = -1
                s_eff = s_j
                target = None
        else:
            s_eff = s_j
            target = None

        if target is None:
            if pos == 0.0:
                # s_eff != 0.0 is load-bearing, not defensive. Mutation can drive
                # entry_threshold to exactly 0.0, and then a signal of exactly 0.0
                # satisfies abs(s) >= thr while copysign(m, 0.0) is *positive* — so
                # a bot with no opinion would open a long at full size. Exposure
                # must come from a signal, never from the absence of one.
                if (blocked_sign == 0 and m_j > 0.0 and s_eff != 0.0
                        and abs(s_eff) >= entry_thr):
                    target = math.copysign(min(m_j, max_lev), s_eff)
                else:
                    target = 0.0
            else:
                same_side = (s_eff > 0) == (pos > 0)
                if abs(s_eff) < exit_thr or (not same_side and abs(s_eff) >= entry_thr):
                    if held >= min_hold:
                        target = (math.copysign(min(m_j, max_lev), s_eff)
                                  if (not same_side and abs(s_eff) >= entry_thr) else 0.0)
                    else:
                        target = pos
                elif not same_side:
                    target = 0.0 if held >= min_hold else pos
                else:
                    target = math.copysign(min(m_j, max_lev), s_eff)
                if max_hold is not None and held >= max_hold:
                    target = 0.0
                    blocked_sign = 1 if pos > 0 else -1

        # ---- 3. trade at the open ------------------------------------------
        delta = target - pos
        ref = op
        if abs(delta) > band * max(abs(target), abs(pos), 0.05) and abs(delta) > 1e-4:
            notional = abs(delta) * equity * capital
            bar_dv = dvol[i] if dvol[i] > 0 else 1e12
            part = notional / bar_dv
            cost_frac = (spread_half + comm + impact_coef * math.sqrt(max(part, 0.0))) * abs(delta)
            cost_frac += min_ticket
            equity *= (1.0 - cost_frac)
            cost_paid += cost_frac
            n_trades += 1
            was = pos
            pos = target
            if (was == 0.0 and pos != 0.0) or (was * pos < 0.0):
                entry_px = op
                entry_atr = at[i - 1] if at[i - 1] > 0 else at[i]
                extreme = op
                held = 0

        # ---- 4. intrabar: stops, targets, trailing --------------------------
        exit_px = None
        if pos != 0.0 and entry_atr > 0.0 and (stop_atr or take_atr or trail_atr):
            if pos > 0.0:
                extreme = max(extreme, h[i])
                lvl_stop = -math.inf
                if stop_atr:
                    lvl_stop = entry_px - stop_atr * entry_atr
                if trail_atr:
                    lvl_stop = max(lvl_stop, extreme - trail_atr * entry_atr)
                if lvl_stop > -math.inf and lo_[i] <= lvl_stop:
                    exit_px = min(lvl_stop, op)
                    stop_exits += 1
                elif take_atr and h[i] >= entry_px + take_atr * entry_atr:
                    exit_px = max(entry_px + take_atr * entry_atr, op)
            else:
                extreme = min(extreme, lo_[i]) if extreme > 0 else lo_[i]
                lvl_stop = math.inf
                if stop_atr:
                    lvl_stop = entry_px + stop_atr * entry_atr
                if trail_atr:
                    lvl_stop = min(lvl_stop, extreme + trail_atr * entry_atr)
                if lvl_stop < math.inf and h[i] >= lvl_stop:
                    exit_px = max(lvl_stop, op)
                    stop_exits += 1
                elif take_atr and lo_[i] <= entry_px - take_atr * entry_atr:
                    exit_px = min(entry_px - take_atr * entry_atr, op)

        # ---- 5. mark the bar out -------------------------------------------
        if exit_px is not None:
            r = exit_px / ref - 1.0
            grow = 1.0 + pos * r
            if grow <= RUIN_EQUITY:
                equity = 0.0
                ruined = True
                equity_arr[i:] = 0.0
                break
            equity *= grow
            notional = abs(pos) * equity * capital
            bar_dv = dvol[i] if dvol[i] > 0 else 1e12
            cost_frac = (spread_half + comm +
                         impact_coef * math.sqrt(max(notional / bar_dv, 0.0))) * abs(pos)
            equity *= (1.0 - cost_frac)
            cost_paid += cost_frac
            n_trades += 1
            blocked_sign = 1 if pos > 0 else -1
            pos = 0.0
            held = 0
        else:
            r = c[i] / ref - 1.0
            if pos != 0.0:
                grow = 1.0 + pos * r
                if grow <= RUIN_EQUITY:
                    equity = 0.0
                    ruined = True
                    equity_arr[i:] = 0.0
                    break
                equity *= grow
                pos = pos * (1.0 + r) / grow

        # ---- 6. carry costs -------------------------------------------------
        if pos != 0.0:
            ap = abs(pos)
            carry = max(ap - 1.0, 0.0) * fin_bar
            if pos < 0.0:
                carry += ap * borrow_bar
            if fund_bar != 0.0:
                carry += pos * fund_bar                 # longs pay, shorts receive
            if carry != 0.0:
                equity *= (1.0 - carry)
                fin_paid += carry
            held += 1
            in_mkt += 1
            exposure_sum += ap
        else:
            held = 0

        if equity > peak:
            peak = equity
        if dd_halt is not None and halt_until < 0 and peak > 0 and equity / peak - 1.0 < -dd_halt:
            halt_until = i + dd_resume
            if pos != 0.0:                              # flatten immediately, at cost
                cost_frac = (spread_half + comm) * abs(pos)
                equity *= (1.0 - cost_frac)
                cost_paid += cost_frac
                n_trades += 1
                pos = 0.0
                held = 0

        equity_arr[i] = equity
        pos_arr[i] = pos

    if ruined:
        pos_arr[i:] = 0.0

    ret = np.zeros(n)
    with np.errstate(divide="ignore", invalid="ignore"):
        prev = equity_arr[:-1]
        ret[1:] = np.where(prev > 0, equity_arr[1:] / np.where(prev > 0, prev, 1.0) - 1.0, 0.0)
    ret[:start + 1] = 0.0
    active = max(n - start, 1)

    return BacktestResult(
        equity=equity_arr, ret=ret, pos=pos_arr, market_ret=series.returns(),
        bars_per_year=bpy, start=start, n_trades=n_trades,
        cost_paid=cost_paid, financing_paid=fin_paid,
        exposure=exposure_sum / active, time_in_market=in_mkt / active,
        halted_frac=halted_bars / active, stop_exits=stop_exits, ruined=ruined,
        market=spec.name, meta={"series": series.name, "cost_mult": cost_mult,
                                "exec_delay": exec_delay},
    )
