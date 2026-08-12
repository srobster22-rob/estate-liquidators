"""Correlated baskets: the one strategy class this lab could not reach.

Every family in `universe.py` generates *independent* instruments, which puts
pairs, lead-lag, relative value and factor crowding out of scope by construction
— and makes the portfolio's rho=0 number a fiction. It also matters for a
sharper reason. F29/F30 found that every strategy this lab certifies clears its
narrowest gate by under 0.07 alpha Sharpe, and that no widening tried so far
(more genes, more filters, more primitives, more search effort) changes that.
The open question was whether any *structurally different* source of return
would.

Cross-sectional strategies are the obvious candidate, and the reason is
arithmetic rather than hopeful. A dollar-neutral basket trade:

  * cancels the common factor, so its raw Sharpe *is* its alpha Sharpe — there is
    no beta to subtract and nothing for `alpha_sharpe` to residualise away; and
  * aggregates K independent idiosyncratic bets, so per-bet edge stays put while
    the portfolio's volatility falls by roughly sqrt(K).

So the *same planted per-instrument edge* should support a materially larger
Sharpe here than it does on a single instrument. If that shows up as margin, the
answer to "is there a space with room" is yes and it is structural. If it does
not, the negative result is worth more than the search that produced it.

HOW THIS AVOIDS BUILDING A SECOND BACKTESTER. It does not add a cross-sectional
engine. A basket is K ordinary `Series`, each carrying its peers in `meta`, and
the cross-sectional score is an ordinary *signal primitive* that reads them. Every
leg therefore runs through the existing, audited `engine.run` — the same fill
model, the same cost model, the same no-lookahead guarantees — and a basket
strategy is K single-leg backtests whose signal happens to be cross-sectional.
Dollar-neutrality falls out of the score being cross-sectionally demeaned rather
than being imposed by new machinery.

The bar model is `generate.bars_from_log_returns`, shared with `synth`, so the
Brownian-bridge intrabar extremes that F6 was about exist in exactly one place.

WHAT IS PLANTED. Short-horizon cross-sectional reversal, the most robustly
documented cross-sectional effect there is: a leg that has underperformed its
peers over the last `xs_lookback` bars earns back a fraction of that gap. The
size is set in units of idiosyncratic vol so it can be compared like for like
against the single-instrument families, and the control basket is the identical
factor structure with the effect switched off.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from . import generate
from .series import Series
from .spec import MarketSpec

PEERS_KEY = "peer_close"


@dataclass
class BasketSpec:
    """A basket family. `leg` supplies the price-process parameters (vol, GARCH,
    tails, costs) so a basket leg is the same kind of object as a catalogue
    instrument and is charged the same way to trade."""

    name: str
    leg: MarketSpec                 # the per-leg price process and cost model
    n_legs: int = 12
    n_bars: int = 12000
    factor_frac: float = 0.55       # share of each leg's variance from the common factor
    beta_disp: float = 0.25         # cross-leg dispersion of factor loadings
    xs_kappa: float = 0.045         # planted reversal, in units of idio sigma per bar
    xs_lookback: int = 5            # the horizon the reversal reverts
    seed_name: str = ""
    notes: str = ""

    @property
    def is_control(self) -> bool:
        return self.xs_kappa == 0.0


def _leg_specs(bspec: BasketSpec) -> list[MarketSpec]:
    """One MarketSpec per leg, named so `engine`/`metrics` can report per leg."""
    return [replace(bspec.leg, name=f"{bspec.name}.leg{i:02d}",
                    seed_name=f"{bspec.name}.leg{i:02d}", n_bars=bspec.n_bars)
            for i in range(bspec.n_legs)]


def synth_basket(bspec: BasketSpec, index: int) -> list[Series]:
    """Generate one basket instance: `n_legs` aligned Series that know each other.

    The construction, in order:

      1. a common factor path, drawn from the leg family's own price process via
         `generate.synth`, so the factor has realistic vol clustering, fat tails
         and regimes rather than being Gaussian noise;
      2. per-leg idiosyncratic innovations, scaled so each leg lands on the leg
         family's target volatility once factor and idio are combined;
      3. the planted cross-sectional reversal, applied to bar t from information
         available at bar t-1 only;
      4. bars, via the shared bar model.

    Step 3 is where lookahead would live if it lived anywhere, so it is written
    to make the offset obvious: `z` is built from returns up to and including
    t-1, and is added to the return of bar t.
    """
    legs = _leg_specs(bspec)
    n = int(bspec.n_bars)
    rng = np.random.default_rng(
        generate.instance_seed(bspec.seed_name or bspec.name, index))

    # 1. the common factor, from the leg family's own process
    factor_spec = replace(bspec.leg, name=f"{bspec.name}.factor",
                          seed_name=f"{bspec.name}.factor", n_bars=n)
    factor = generate.synth(factor_spec, index)
    f_lr = np.diff(np.log(factor.close), prepend=np.log(factor.close[0]))
    f_lr[0] = 0.0
    f_sd = float(f_lr.std()) or 1e-12

    # 2. loadings and idiosyncratic innovations
    betas = 1.0 + bspec.beta_disp * rng.standard_normal(bspec.n_legs)
    sigma_bar = float(bspec.leg.sigma_bar)
    # Total per-leg variance is factor + idio; split it to hit `factor_frac`.
    idio_sd = sigma_bar * np.sqrt(max(1.0 - bspec.factor_frac, 1e-6))
    f_scale = sigma_bar * np.sqrt(bspec.factor_frac) / f_sd
    eps = rng.standard_normal((n, bspec.n_legs))

    # 3. the reversal, planted bar by bar on lagged information only
    idio = np.empty((n, bspec.n_legs))
    lr = np.empty((n, bspec.n_legs))
    cum = np.zeros(bspec.n_legs)          # trailing idio sum over `xs_lookback`
    hist: list[np.ndarray] = []
    for t in range(n):
        if bspec.xs_kappa > 0.0 and len(hist) >= bspec.xs_lookback:
            gap = cum - cum.mean()
            sd = gap.std() or 1e-12
            pull = -bspec.xs_kappa * idio_sd * (gap / sd)
        else:
            pull = 0.0
        idio[t] = idio_sd * eps[t] + pull
        lr[t] = betas * (f_scale * f_lr[t]) + idio[t]
        hist.append(idio[t])
        cum += idio[t]
        if len(hist) > bspec.xs_lookback:
            cum -= hist.pop(0)

    # 4. bars, through the one shared bar model
    out: list[Series] = []
    sig = np.full(n, sigma_bar)
    for i, spec in enumerate(legs):
        o, h, lo, c, v = generate.bars_from_log_returns(spec, lr[:, i], sig, rng)
        out.append(Series(name=f"{bspec.name}.leg{i:02d}#{index}", open=o, high=h,
                          low=lo, close=c, volume=v, spec=spec, seed=index,
                          meta={"index": index, "generator": "basket-v1",
                                "basket": bspec.name, "leg": i}))
    attach_peers(out)
    return out


def attach_peers(legs: list[Series]) -> list[Series]:
    """Give every leg a view of the whole basket's closes.

    Stored as one (n_bars, n_legs) array plus this leg's column, so a
    cross-sectional signal is a couple of array ops rather than a join. It lives
    in `meta` because `Series` is the shape everything downstream agrees on and
    widening that dataclass for one strategy class would be the wrong trade.
    """
    mat = np.column_stack([s.close for s in legs])
    for i, s in enumerate(legs):
        s.meta[PEERS_KEY] = mat
        s.meta["peer_col"] = i
    return legs


def basket_control(bspec: BasketSpec) -> BasketSpec:
    """The same factor structure with the cross-sectional effect switched off.

    Without this, a cross-sectional bot that makes money proves nothing: a
    dollar-neutral basket trade has low volatility by construction, so a small
    artefact divides into a large Sharpe. This is the G3 lesson (F6) applied to
    a new strategy class before that class is allowed to claim anything.
    """
    return replace(bspec, name=f"{bspec.name}_control", xs_kappa=0.0,
                   seed_name=bspec.seed_name or bspec.name,
                   notes="control: identical factor structure, no cross-sectional effect")
