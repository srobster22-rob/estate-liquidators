"""
The market taxonomy — nine families spanning what Kalshi actually lists, plus a control.

Each family is a variance schedule from `paths.py` (how information arrives) wrapped in a
quoting layer (how the book prices it). The quoting layer is where every exploitable edge
in this project is deliberately planted, so it is worth being explicit about what is in
here, because the loop's job is to find these and only these:

  EDGE 1 · LONGSHOT COMPRESSION  (`logit_gamma` < 1)
      quoted logit = gamma * true logit, so cheap contracts quote too high and expensive
      ones too low. The classic favourite-longshot bias, in its standard functional form.
      Sized per family by how retail-driven the book plausibly is: 0.995 for crypto
      hourlies (arbitraged by people with real models) down to 0.85 for thin entertainment
      markets. At gamma=0.85 a true 5c contract quotes ~8c — a 3c gross edge, which is
      large, and which is the whole reason the illiquid families are worth testing at all.

  EDGE 2 · UNDERREACTION  (`underreact_*`)
      the quoted mid lags a move instead of jumping to it, capped at a few cents. Modelled
      as a decaying gap: u_t = decay * u_{t-1} + alpha * (new move), clipped to
      `underreact_cap_cents`. The cap is what keeps this honest — an uncapped lag on a
      martingale would hand a momentum bot 20c per print and the loop would "discover" a
      20c edge that exists nowhere in the world.

  EDGE 3 · BRACKET INCOHERENCE  (`n_brackets` > 1)
      brackets in a mutually exclusive set are quoted with independent noise, so their
      asks sum to something other than 100. Buying every bracket when the asks sum below
      100 is a real, riskless, fully-collateralised arbitrage. It should be rare, small,
      and fee-sensitive — which is exactly what makes it a good test of whether the
      backtester's fee accounting is honest.

  EDGE 4 · SPREAD CAPTURE  (`spread_ticks`)
      wide books can in principle be made rather than taken. Whether that is a business
      depends entirely on `microstructure.maker_benign_fill_rate` in config.json, which
      is a guess. Flagged everywhere it matters.

  NOT AN EDGE · `efficient_control`
      gamma=1.0, no lag, minimal noise, penny spread. A perfectly efficient market. Any
      bot that shows profit here has found a bug in the harness, not an edge, and the
      loop treats a positive result on this family as a harness failure rather than a
      discovery. It is the single most useful family in the file.

Two structural facts about Kalshi's book are modelled faithfully and both matter:

  * ONE BOOK, NOT TWO. A YES bid at 40 *is* a NO ask at 60 — they are the same resting
    order. So no_ask = 100 - yes_bid and no_bid = 100 - yes_ask, always. This is why the
    much-repeated "buy YES and NO for less than 100" arbitrage cannot exist on a single
    Kalshi market: yes_ask + no_ask = 100 + (yes_ask - yes_bid) >= 100 identically. The
    `pair_arb` strategy is implemented anyway, and finds nothing, which is the point.

  * 1c TICK, PRICES 1..99. A 1c tick is coarse when the fee at mid-book is 1.75c. Half
    the strategies in this project are trying to earn less than one tick.
"""

from __future__ import annotations

import json
import pathlib
import random
import zlib

from . import paths

_CFG = json.loads((pathlib.Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
_MICRO = _CFG["microstructure"]

TICK = int(_MICRO["tick_cents"])
MIN_P = int(_MICRO["min_price_cents"])
MAX_P = int(_MICRO["max_price_cents"])

HOURS_PER_YEAR = 24 * 365


class Family:
    """One Kalshi market family: its information dynamics and its microstructure."""

    __slots__ = ("name", "label", "steps", "step_hours", "schedule_kind", "schedule_kw",
                 "p0_mu", "p0_sd", "logit_gamma", "underreact_alpha", "underreact_decay",
                 "underreact_cap", "quote_noise", "spread_lo", "spread_hi", "depth_lo",
                 "depth_hi", "n_brackets", "notes", "salt_name")

    def __init__(self, name, label, steps, step_hours, schedule_kind, p0_mu, p0_sd,
                 logit_gamma, underreact_alpha, underreact_decay, underreact_cap,
                 quote_noise, spread_lo, spread_hi, depth_lo, depth_hi,
                 n_brackets=1, schedule_kw=None, notes="", salt_name=None):
        self.name, self.label = name, label
        # Which name seeds the RNG. Normally the family's own, but an attenuated copy
        # borrows its base family's salt so that the same group id draws the SAME latent
        # path, spreads and depths — see `attenuated`.
        self.salt_name = salt_name or name
        self.steps, self.step_hours = steps, step_hours
        self.schedule_kind, self.schedule_kw = schedule_kind, schedule_kw or {}
        self.p0_mu, self.p0_sd = p0_mu, p0_sd
        self.logit_gamma = logit_gamma
        self.underreact_alpha = underreact_alpha
        self.underreact_decay = underreact_decay
        self.underreact_cap = underreact_cap
        self.quote_noise = quote_noise
        self.spread_lo, self.spread_hi = spread_lo, spread_hi
        self.depth_lo, self.depth_hi = depth_lo, depth_hi
        self.n_brackets = n_brackets
        self.notes = notes

    @property
    def life_hours(self) -> float:
        return self.steps * self.step_hours

    @property
    def turns_per_year(self) -> float:
        """How many times a year the same capital could be recycled through this family.
        The reason a 2% edge on a 90-day political market is worse than a 0.3% edge on an
        hourly crypto market, and the reason the gate scores annualised return."""
        return HOURS_PER_YEAR / max(self.life_hours, 1e-9)


FAMILIES: dict[str, Family] = {}


def _add(f: Family):
    FAMILIES[f.name] = f
    return f


# --- liquid, fast, heavily modelled by others -------------------------------------
_add(Family(
    "crypto_hourly", "BTC/ETH above strike at top of hour",
    steps=60, step_hours=1 / 60, schedule_kind="uniform",
    p0_mu=0.0, p0_sd=1.2,
    logit_gamma=0.995, underreact_alpha=0.25, underreact_decay=0.45, underreact_cap=1.0,
    quote_noise=0.6, spread_lo=1, spread_hi=2, depth_lo=300, depth_hi=1200,
    notes="Most efficient thing Kalshi lists. Deep, penny-wide, and full of people with "
          "the same spot feed you have. Included because it recycles capital 8760x/yr, "
          "so a tiny real edge here beats a large one anywhere else."))

_add(Family(
    "index_bracket_daily", "S&P/Nasdaq closing range brackets",
    steps=78, step_hours=6.5 / 78, schedule_kind="uniform",
    p0_mu=0.0, p0_sd=1.0,
    logit_gamma=0.995, underreact_alpha=0.25, underreact_decay=0.45, underreact_cap=1.0,
    quote_noise=1.4, spread_lo=1, spread_hi=3, depth_lo=100, depth_hi=500,
    n_brackets=5,
    notes="Five mutually exclusive closing ranges. The only family where a riskless "
          "arbitrage is structurally possible, because five books quote one distribution."))

# --- event-driven ------------------------------------------------------------------
_add(Family(
    "econ_print", "CPI / payrolls / Fed decision above threshold",
    steps=40, step_hours=0.25, schedule_kind="print_shock",
    p0_mu=0.0, p0_sd=1.1,
    logit_gamma=0.99, underreact_alpha=0.55, underreact_decay=0.60, underreact_cap=3.0,
    quote_noise=1.0, spread_lo=1, spread_hi=3, depth_lo=150, depth_hi=600,
    schedule_kw={"shock_share": 0.90},
    notes="Dead flat, then one step carries 90% of the uncertainty. The bot is not told "
          "when the print lands; it has to infer it from the move, like everyone else."))

_add(Family(
    "weather_temp", "High temperature in city above threshold",
    steps=48, step_hours=1.0, schedule_kind="convergence",
    p0_mu=0.0, p0_sd=1.3,
    logit_gamma=0.97, underreact_alpha=0.35, underreact_decay=0.55, underreact_cap=2.0,
    quote_noise=1.5, spread_lo=2, spread_hi=4, depth_lo=60, depth_hi=250,
    schedule_kw={"gamma": 1.6},
    notes="Forecast skill improves as the date nears, so uncertainty resolves late. "
          "Thin enough that the spread is a real cost and retail bias is real."))

_add(Family(
    "sports_game", "Single-game moneyline, in-play",
    steps=60, step_hours=3.0 / 60, schedule_kind="jumpy",
    p0_mu=0.0, p0_sd=0.9,
    logit_gamma=0.93, underreact_alpha=0.30, underreact_decay=0.50, underreact_cap=2.0,
    quote_noise=1.2, spread_lo=2, spread_hi=3, depth_lo=150, depth_hi=800,
    schedule_kw={"n_jumps": 6, "base_share": 0.45},
    notes="Scores are jumps. Strong favourite-longshot bias — this is the family where "
          "sportsbook-style retail pricing is most plausible."))

# --- slow, thin, retail-priced -----------------------------------------------------
_add(Family(
    "politics_long", "Election / nomination, months out",
    steps=90, step_hours=24.0, schedule_kind="slow",
    p0_mu=-0.6, p0_sd=1.4,
    logit_gamma=0.90, underreact_alpha=0.50, underreact_decay=0.70, underreact_cap=3.0,
    quote_noise=2.0, spread_lo=3, spread_hi=6, depth_lo=30, depth_hi=150,
    notes="The biggest gross edges and the worst capital efficiency: 90 days of locked "
          "collateral turns a 3c edge into a single-digit annualised return."))

_add(Family(
    "awards_thin", "Awards / entertainment / novelty",
    steps=60, step_hours=24.0, schedule_kind="slow",
    p0_mu=-1.8, p0_sd=1.2,
    logit_gamma=0.85, underreact_alpha=0.55, underreact_decay=0.70, underreact_cap=3.0,
    quote_noise=2.5, spread_lo=4, spread_hi=8, depth_lo=10, depth_hi=60,
    notes="Worst pricing on the exchange and the least size to trade against it. The "
          "test of whether a large edge in a 30-contract book is a business at all."))

_add(Family(
    "mentions_short", "Will X say Y this week / short novelty",
    steps=35, step_hours=4.0, schedule_kind="uniform",
    p0_mu=-1.2, p0_sd=1.3,
    logit_gamma=0.90, underreact_alpha=0.45, underreact_decay=0.60, underreact_cap=2.5,
    quote_noise=2.0, spread_lo=3, spread_hi=6, depth_lo=25, depth_hi=120,
    notes="Short-dated novelty markets: mispriced like the thin families but they turn "
          "over ~60x a year instead of 4. Added in generation 3 for exactly that reason."))

# --- the control -------------------------------------------------------------------
_add(Family(
    "efficient_control", "CONTROL — perfectly efficient market, no edge exists",
    steps=60, step_hours=1 / 60, schedule_kind="uniform",
    p0_mu=0.0, p0_sd=1.2,
    logit_gamma=1.0, underreact_alpha=0.0, underreact_decay=0.0, underreact_cap=0.0,
    quote_noise=0.4, spread_lo=1, spread_hi=1, depth_lo=500, depth_hi=1500,
    notes="NOT a market. A tripwire. Prices are the true probability plus symmetric "
          "noise, penny-wide. Profit here is impossible; measuring profit here means the "
          "harness is broken. Checked every generation."))

TRADEABLE = [n for n in FAMILIES if n != "efficient_control"]


# ---------------------------------------------------------------------------
# Episodes
# ---------------------------------------------------------------------------

class Episode:
    """One market's whole life: quotes at every step, and how it resolved.

    Parallel lists rather than a list of records — this gets touched a few million times
    per generation and the difference is minutes.
    """

    __slots__ = ("family", "n", "bid", "ask", "depth", "true_p", "outcome",
                 "group_id", "leg", "life_hours")

    def __init__(self, family, group_id, leg, n):
        self.family = family
        self.group_id = group_id
        self.leg = leg
        self.n = n
        self.bid: list[int] = []
        self.ask: list[int] = []
        self.depth: list[int] = []
        self.true_p: list[float] = []
        self.outcome = 0
        self.life_hours = family.life_hours

    def mid(self, t: int) -> float:
        return (self.bid[t] + self.ask[t]) / 2.0


class Group:
    """The unit of backtesting: one market, or one mutually exclusive bracket set.

    Groups are the unit because bracket arbitrage is a statement about several markets at
    once, and a per-market loop could never see it.
    """

    __slots__ = ("family", "legs", "gid")

    def __init__(self, family, gid, legs):
        self.family, self.gid, self.legs = family, gid, legs

    @property
    def steps(self) -> int:
        return self.legs[0].n


def _biased_prob(p: float, gamma: float) -> float:
    if gamma == 1.0:
        return p
    return paths.expit(gamma * paths.logit(p))


def _quote(mid_float: float, spread: int, rng) -> tuple[int, int]:
    """Turn a fair mid into a two-sided book. Kalshi's single book means the NO side is
    implied, never quoted separately."""
    mid = min(max(mid_float, MIN_P + spread / 2.0), MAX_P - spread / 2.0)
    bid = int(round(mid - spread / 2.0))
    bid = min(max(bid, MIN_P), MAX_P - spread)
    ask = bid + spread
    if ask > MAX_P:
        ask = MAX_P
        bid = max(MIN_P, ask - spread)
    return bid, ask


def _depth_taper(price_cents: int) -> float:
    """Liquidity concentrates near even money and thins at the extremes.

    Added after the factory found its first strong candidate: buying 99c contracts and
    holding to settlement, which works because the price grid stops at 99 so a contract
    worth 99.8c can only be quoted at 99. That edge is real — it is the mirror of the 1c
    floor, it was never planted, and it exists on the actual exchange.

    But the first version of this file quoted 150-600 contracts of depth at 99c, which is
    not what a real book looks like: nobody rests size at 99 on a contract everyone agrees
    is nearly certain. Without a taper the simulator hands out unlimited size at exactly the
    price where the structural edge lives, which is the most flattering possible assumption
    for the strategy that had just been discovered.

    4p(1-p) is 1.0 at 50c and floors at 8% of base depth, so a 99c market shows roughly a
    twelfth of the size a coin-flip market does. The shape is a modelling choice, not a
    measurement; the floor is what stops the extremes becoming untradeable outright.
    """
    p = price_cents / 100.0
    return max(0.08, 4.0 * p * (1.0 - p))


def _price_series(fam: Family, true_p: list[float], rng) -> tuple[list[int], list[int], list[int]]:
    """Apply the planted edges to a true probability path and quote a book around it."""
    bids, asks, depths = [], [], []
    u = 0.0            # unreflected move, in cents (EDGE 2)
    prev_target = None
    for t, p in enumerate(true_p):
        target = 100.0 * _biased_prob(p, fam.logit_gamma)          # EDGE 1
        if prev_target is None:
            prev_target = target
        move = target - prev_target
        u = fam.underreact_decay * u + fam.underreact_alpha * move
        if fam.underreact_cap > 0:
            u = max(-fam.underreact_cap, min(fam.underreact_cap, u))
        else:
            u = 0.0
        prev_target = target
        mid = target - u + rng.gauss(0.0, fam.quote_noise)          # EDGE 3 source
        spread = rng.randint(fam.spread_lo, fam.spread_hi)
        b, a = _quote(mid, spread, rng)
        bids.append(b)
        asks.append(a)
        base = rng.randint(fam.depth_lo, fam.depth_hi)              # EDGE 4 context
        depths.append(max(1, int(base * _depth_taper((b + a) // 2))))
    return bids, asks, depths


def _family_salt(name: str) -> int:
    """A STABLE per-family seed offset.

    This used to be `hash(name)`, and that was a genuine bug rather than a style problem:
    Python randomises string hashing per process, so every run of the factory drew
    different markets from the same seed. Two identical invocations disagreed about which
    strategy won — in one process the best config on the control market scored +84c, in the
    next +975c — and nothing in the pipeline would ever have flagged it, because each run
    was internally consistent. crc32 is stable across processes and machines forever.
    """
    import zlib
    return zlib.crc32(name.encode("utf-8")) & 0x7FFFFFFF


def generate_group(fam: Family, gid: int) -> Group:
    """One episode (or bracket set) for family `fam`, reproducible from `gid` alone.

    Determinism by group id is what lets in-sample / OOS / holdout be disjoint by seed
    range instead of by a shuffle someone has to remember to do correctly.
    """
    rng = random.Random(_family_salt(fam.salt_name) ^ (gid * 2654435761 & 0x7FFFFFFF))
    sched = paths.variance_schedule(fam.schedule_kind, fam.steps, rng, **fam.schedule_kw)

    if fam.n_brackets > 1:
        # Bracket set: one latent path, N intervals over it. True probs sum to 1 exactly,
        # each leg is quoted independently, so the quoted set is incoherent.
        path = paths.LatentPath(fam.steps, sched, 0.0, rng)
        n = fam.n_brackets
        edges = [paths.norm_ppf((i + 1) / n) * 0.9 for i in range(n - 1)]
        winner = path.bracket_outcome(edges, rng)
        legs = []
        for i in range(n):
            ep = Episode(fam, gid, i, fam.steps)
            tp = [path.bracket_probs(t, edges)[i] for t in range(fam.steps)]
            ep.true_p = tp
            ep.bid, ep.ask, ep.depth = _price_series(fam, tp, rng)
            ep.outcome = 1 if i == winner else 0
            legs.append(ep)
        return Group(fam, gid, legs)

    p0 = paths.expit(rng.gauss(fam.p0_mu, fam.p0_sd))
    p0 = min(max(p0, 0.02), 0.98)
    k = paths.strike_for_initial_prob(p0)
    path = paths.LatentPath(fam.steps, sched, k, rng)
    ep = Episode(fam, gid, 0, fam.steps)
    ep.true_p = path.true_p
    ep.bid, ep.ask, ep.depth = _price_series(fam, path.true_p, rng)
    ep.outcome = path.outcome
    return Group(fam, gid, [ep])


# Attenuated copies of families, kept OUT of FAMILIES so they never enter the factory's
# sweep as tradeable families in their own right.
_ATTENUATED: dict[str, Family] = {}


def attenuated(family_name: str, factor: float) -> str:
    """A copy of `family_name` with every planted edge scaled by `factor`. Returns its name.

    The gate's stress test makes execution worse — higher fees, wider spread, fewer maker
    fills — and that tests whether a bot was fitting the cost assumptions. It does not test
    the assumption that actually matters most: that the inefficiency is as large as
    `markets.py` says it is. Those magnitudes are my estimates. Halving them is the closest
    thing available to asking "what if the world is only half as exploitable as I guessed",
    which is the most likely way any of this fails outside the simulator.

    Attenuates the two planted edges and leaves microstructure alone, so the bot faces the
    same spreads, the same depth and the same fees against a fainter signal. gamma moves
    toward 1.0 (no compression) and the underreaction cap scales directly.

    PAIRED, and it has to be. The copy inherits its base family's `salt_name`, so group 7 of
    the attenuated family runs the same latent path, the same spread draws and the same depth
    draws as group 7 of the original — the ONLY difference is the size of the planted edge.
    The first version of this did not do that: the copy had its own name, therefore its own
    crc32 salt, therefore entirely unrelated markets. The comparison still ran, and it still
    disqualified a bot, but the difference it measured was mostly sampling noise. The giveaway
    was the sensitivity curve coming out non-monotone — a 25%-strength world scored better
    than a 50%-strength one, which cannot happen if the only thing changing is the edge.
    """
    key = f"{family_name}@{factor:g}"
    got = _ATTENUATED.get(key)
    if got is not None:
        return key
    base = FAMILIES[family_name]
    f = Family(
        key, f"{base.label} (edges x{factor:g})", base.steps, base.step_hours,
        base.schedule_kind, base.p0_mu, base.p0_sd,
        logit_gamma=1.0 - (1.0 - base.logit_gamma) * factor,
        underreact_alpha=base.underreact_alpha,
        underreact_decay=base.underreact_decay,
        underreact_cap=base.underreact_cap * factor,
        quote_noise=base.quote_noise, spread_lo=base.spread_lo, spread_hi=base.spread_hi,
        depth_lo=base.depth_lo, depth_hi=base.depth_hi, n_brackets=base.n_brackets,
        schedule_kw=base.schedule_kw, salt_name=base.name,
        notes=f"attenuated copy of {family_name} for the gate's half-edge criterion")
    _ATTENUATED[key] = f
    return key


def _lookup(name: str) -> Family:
    f = FAMILIES.get(name)
    return f if f is not None else _ATTENUATED[name]


_CACHE: dict[tuple[str, int, int], list[Group]] = {}


def dataset(family_name: str, seed_base: int, count: int) -> list[Group]:
    """Cached, so all candidates in a generation are scored on identical markets.

    Paired comparison, not just a speed trick: two bots differing by one parameter are
    measured on the same draws, which removes most of the sampling noise from the
    comparison between them.
    """
    key = (family_name, seed_base, count)
    got = _CACHE.get(key)
    if got is None:
        fam = _lookup(family_name)
        got = [generate_group(fam, seed_base + i) for i in range(count)]
        _CACHE[key] = got
    return got


def clear_cache():
    _CACHE.clear()


if __name__ == "__main__":
    print(f"{len(FAMILIES)} families ({len(TRADEABLE)} tradeable + 1 control)\n")
    hdr = f"{'family':<22} {'steps':>5} {'life':>9} {'turns/yr':>9} {'gamma':>6} {'lag cap':>8} {'spread':>7} {'depth':>11}"
    print(hdr)
    print("-" * len(hdr))
    for f in FAMILIES.values():
        life = f"{f.life_hours:.1f}h" if f.life_hours < 48 else f"{f.life_hours / 24:.0f}d"
        print(f"{f.name:<22} {f.steps:>5} {life:>9} {f.turns_per_year:>9.0f} "
              f"{f.logit_gamma:>6.3f} {f.underreact_cap:>7.1f}c {f.spread_lo}-{f.spread_hi:<5} "
              f"{f.depth_lo}-{f.depth_hi:<7}")

    print("\nPlanted longshot edge (gamma), gross cents, before any cost:")
    print(f"  {'family':<22} " + " ".join(f"{f'p={p}c':>8}" for p in (3, 10, 25, 50)))
    for f in FAMILIES.values():
        cells = []
        for tp in (0.03, 0.10, 0.25, 0.50):
            q = _biased_prob(tp, f.logit_gamma)
            cells.append(f"{(q - tp) * 100:>+7.2f}c")
        print(f"  {f.name:<22} " + " ".join(cells))
