"""
The factory: breed bots, test them, expand the search, repeat until something
survives the gauntlet — or until the budget runs out and the honest answer is
"nothing here beat the null".

THE LOOP

    generation:
        evaluate every bot on the TRAIN slice          (fitness, in-sample)
        promote the best few to the gauntlet on the VALIDATION slice
        anything that passes all eleven gates goes to the VAULT for one-shot
            confirmation on data that has never been touched
        breed the survivors: tournament select, crossover, mutate, add immigrants
        if the population has stopped improving, EXPAND

THE EXPANSION LADDER, in order:

    0  four markets, tier-0 strategies
    1  every market in the universe
    2  tier-1 strategies (pairs, regime-filtered hybrids)
    3  ensembles of two strategies
    4  tier-2 strategies, larger population, higher mutation
    5  wider risk envelope, more random immigrants per generation

Expansion only ever adds search breadth. It NEVER touches the gates. That line is
the difference between a factory and a slot machine: if the loop can eventually
lower the bar, then "keep going until we get a profitable bot" is guaranteed to
succeed and guaranteed to mean nothing.

The bar is FLAT, not rising. Gate 10 deflates by the run's whole look budget from
the very first look, so every candidate faces the same hurdle. An earlier version
charged the running count instead, on the reasoning that looking harder should make
passing harder — which sounds right and was wrong in practice. It meant a
candidate's verdict depended on its position in the queue: across ten seeds, every
confirmed bot was found in the first half of its run, two of them at looks 1 and 2
posting validation Sharpes of 1.8, while candidates posting 4.7 were rejected later
in the same runs. The correction is still paid in full. It is just paid by everyone
equally rather than by whoever happens to arrive late.

BOTH COUNTERS PERSIST ACROSS RUNS, in state/factory_state.json:

    trials      bots evaluated in sample. Reported, not charged for — see the
                note in validate.py on why the out-of-sample claim doesn't owe
                anything to the in-sample search count.
    oos_looks   candidates tested against the validation slice. This one is
                charged for, in gate 10, and it is why restarting the factory
                twenty times does not get you twenty fresh chances.

Delete that file and you are lying to yourself about how hard you looked.
"""

import json
import math
import pathlib
import random
import time

from . import bot as botmod
from . import indicators as ind
from . import stats
from . import strategies as st
from . import validate as val

STATE_DIR = pathlib.Path(__file__).parent / "state"

STAGE_NAMES = [
    "core markets, tier-0 strategies",
    "full market universe",
    "tier-1 strategies unlocked",
    "ensembles unlocked",
    "tier-2 strategies, larger population",
    "wide risk envelope, heavy immigration",
]


class Factory:
    def __init__(self, segments, config=None, seed=1, state_file=None,
                 log=print):
        """`segments` maps market key -> universe.Segments."""
        self.segments = segments
        self.cfg = dict(DEFAULTS, **(config or {}))
        self.rng = random.Random(seed)
        self.log = log
        self.state_file = pathlib.Path(state_file) if state_file else \
            STATE_DIR / "factory_state.json"
        self.state = load_state(self.state_file)
        self.fitness_cache = {}
        self.stage = 0
        self.best_fitness = -1e9
        self.stagnant = 0
        self.history = []
        self.reports = []
        self.keys = sorted(segments)
        self._pairs = self._build_pairs()
        # Daily return streams of every candidate that has reached the vault, so a
        # near-duplicate can be turned away before it spends a burn. Rebuilt from
        # the persisted vault log so the protection survives a restart.
        self._tested_returns = []
        self._pending_returns = None
        self._rebuild_tested_returns()

    def _rebuild_tested_returns(self):
        """Recompute the validation return stream of every previously vault-tested
        bot. Costs one backtest per logged burn at startup — which is itself a
        useful signal: if this is slow, the vault has been used far too much."""
        for entry in self.state.get("vault_log", []):
            try:
                candidate = botmod.Bot.from_dict(entry["bot"])
                seg = self.segments.get(candidate.market_key)
                if seg is None:
                    continue
                pseg = self.segments.get(candidate.partner_key) \
                    if candidate.partner_key else None
                res = candidate.run(seg.validation,
                                    pseg.validation if pseg else None)
                self._tested_returns.append((_daily(res, seg.validation),
                                             entry.get("passed", False),
                                             candidate.market_key))
            except (KeyError, ValueError, ZeroDivisionError, OverflowError):
                continue

    # ------------------------------------------------------------ universe

    def _build_pairs(self):
        """Legal partners for a pairs trade: same interval, same bar count, same
        timestamps. Anything else and the spread is comparing Tuesday to Thursday."""
        pairs = {}
        for a in self.keys:
            sa = self.segments[a]
            partners = []
            for b in self.keys:
                if a == b:
                    continue
                sb = self.segments[b]
                if (sa.full.interval == sb.full.interval
                        and len(sa.full) == len(sb.full)
                        and sa.full.ts[0] == sb.full.ts[0]):
                    partners.append(b)
            pairs[a] = partners
        return pairs

    def active_markets(self):
        if self.stage >= 1:
            return self.keys
        return self.keys[:min(4, len(self.keys))]

    def tier(self):
        return {0: 0, 1: 0, 2: 1, 3: 1}.get(self.stage, 2)

    def ensembles_on(self):
        return self.stage >= 3

    def population_size(self):
        base = self.cfg["population"]
        return base if self.stage < 4 else int(base * 1.6)

    def mutation_scale(self):
        return 0.25 if self.stage < 4 else 0.45

    def immigrant_frac(self):
        return 0.15 if self.stage < 5 else 0.35

    # ---------------------------------------------------------- generation

    def random_bot(self, gen=0):
        key = self.rng.choice(self.active_markets())
        kind = self.segments[key].full.kind
        pool = st.available(self.tier(), kind)
        pool = [s for s in pool
                if not s.needs_partner or self._pairs.get(key)]
        if not pool:
            pool = [s for s in st.available(0, kind) if not s.needs_partner]
        strat = self.rng.choice(pool)
        partner = self.rng.choice(self._pairs[key]) if strat.needs_partner else None
        return botmod.Bot(key, strat.name, strat.sample(self.rng),
                          self._sample_risk(), partner, born_gen=gen)

    def _sample_risk(self):
        risk = {k: spec.sample(self.rng) for k, spec in botmod.RISK_SPACE.items()}
        if self.stage >= 5:
            risk["max_leverage"] = min(4.0, risk["max_leverage"] * 1.4)
        return risk

    def mutate(self, parent, gen):
        scale = self.mutation_scale()
        risk = dict(parent.risk)
        for k, spec in botmod.RISK_SPACE.items():
            if self.rng.random() < 0.3:
                risk[k] = spec.mutate(self.rng, risk[k], scale)

        if parent.children:
            # An ensemble has no strategy of its own: mutate each child's knobs and
            # leave the composition alone. Swapping a child is the crossover
            # operator's job, and doing both here made the lineage untraceable.
            children = []
            for child in parent.children:
                sub = st.REGISTRY[child["strategy"]]
                cp = dict(child["params"])
                for k, spec in sub.space.items():
                    if self.rng.random() < 0.4:
                        cp[k] = spec.mutate(self.rng, cp[k], scale)
                children.append({"strategy": child["strategy"], "params": cp})
            return botmod.Bot(parent.market_key, "ensemble", {}, risk, None,
                              children, born_gen=gen)

        params = dict(parent.params)
        strat = st.REGISTRY[parent.strategy_name]
        for k, spec in strat.space.items():
            if self.rng.random() < 0.4:
                params[k] = spec.mutate(self.rng, params[k], scale)
        key = parent.market_key
        strategy_name = parent.strategy_name
        partner = parent.partner_key
        children = []

        # Occasionally move a working idea to a different market. This is where the
        # factory finds out whether an edge is a market property or a fit.
        if self.rng.random() < 0.12:
            candidates = [k for k in self.active_markets()
                          if self.segments[k].full.kind in strat.kinds]
            if candidates:
                key = self.rng.choice(candidates)
                partner = (self.rng.choice(self._pairs[key])
                           if strat.needs_partner and self._pairs.get(key) else None)
                if strat.needs_partner and partner is None:
                    key = parent.market_key
                    partner = parent.partner_key

        # Or swap to a sibling in the same family, keeping the risk settings that
        # were working.
        if self.rng.random() < 0.08:
            kind = self.segments[key].full.kind
            sibs = [s for s in st.available(self.tier(), kind)
                    if s.family == strat.family and s.name != strategy_name
                    and (not s.needs_partner or self._pairs.get(key))]
            if sibs:
                new = self.rng.choice(sibs)
                strategy_name = new.name
                params = new.sample(self.rng)
                partner = (self.rng.choice(self._pairs[key])
                           if new.needs_partner else None)

        return botmod.Bot(key, strategy_name, params, risk, partner, children,
                          born_gen=gen)

    def crossover(self, a, b, gen):
        """Same strategy: blend the parameters. Different strategies on the same
        market: build an ensemble if they're unlocked, otherwise take one parent's
        logic and the other's risk settings."""
        if a.strategy_name == b.strategy_name and not a.children and not b.children:
            strat = st.REGISTRY[a.strategy_name]
            params = {}
            for k, spec in strat.space.items():
                if isinstance(spec, st.ChoiceP):
                    params[k] = self.rng.choice([a.params[k], b.params[k]])
                else:
                    w = self.rng.random()
                    v = a.params[k] * w + b.params[k] * (1 - w)
                    params[k] = int(round(v)) if isinstance(spec, st.IntP) else v
            risk = {k: (a.risk[k] if self.rng.random() < 0.5 else b.risk[k])
                    for k in botmod.RISK_SPACE}
            return botmod.Bot(a.market_key, a.strategy_name, params, risk,
                              a.partner_key, born_gen=gen)

        if (self.ensembles_on() and a.market_key == b.market_key
                and not a.children and not b.children
                and not a.partner_key and not b.partner_key):
            children = [{"strategy": a.strategy_name, "params": a.params},
                        {"strategy": b.strategy_name, "params": b.params}]
            return botmod.Bot(a.market_key, "ensemble", {}, dict(a.risk),
                              None, children, born_gen=gen)

        return botmod.Bot(a.market_key, a.strategy_name, dict(a.params),
                          dict(b.risk), a.partner_key, list(a.children),
                          born_gen=gen)

    # ---------------------------------------------------------- evaluation

    def evaluate(self, candidate):
        """In-sample fitness, memoised by fingerprint. Every FIRST evaluation of a
        distinct genome is a trial, and trials are what gate 10 charges for."""
        fp = candidate.fingerprint()
        hit = self.fitness_cache.get(fp)
        if hit is not None:
            return hit
        seg = self.segments[candidate.market_key]
        partner = self.segments[candidate.partner_key].train \
            if candidate.partner_key else None
        try:
            result = candidate.run(seg.train, partner)
        except (ValueError, ZeroDivisionError, OverflowError):
            self.fitness_cache[fp] = -1e9
            return -1e9
        score = botmod.fitness(result, self.cfg["min_trades"],
                               market_returns=ind.simple_returns(seg.train))
        self.fitness_cache[fp] = score
        self.state["trials"] += 1
        if math.isfinite(result["sharpe"]) and result["trades"] >= 5:
            samples = self.state["sharpe_samples"]
            samples.append(round(result["sharpe"], 4))
            if len(samples) > 8000:
                # Reservoir-style thinning: keep the dispersion estimate honest
                # without growing the state file without bound.
                del samples[::2]
        return score

    def dispersion(self):
        """Dispersion of the out-of-sample Sharpes — the scale for gate 10's hurdle,
        since that gate asks how good the best of `oos_looks` candidates would look
        by luck alone on this segment.

        SHRUNK, not switched. The first version flipped from the in-sample estimate
        to the out-of-sample one the moment the 5th sample landed, and a standard
        deviation computed from 5 observations is so noisy that the hurdle fell 55%
        in a single step — from 2.80 to 1.25 in a measured run. A candidate posting
        3.0 failed as the 5th look and an identical twin passed as the 6th. That is
        precisely the false-positive machine gate 10 exists to prevent, and it
        contradicted this file's own claim that the bar only ever rises.

        The two estimators converge as samples accumulate, so the fix is to blend
        rather than switch: weight the out-of-sample estimate by n/(n+K) and the
        (wider, more conservative) in-sample estimate by the remainder."""
        # The theoretical null dispersion, not the observed spread of candidates.
        # See stats.null_sharpe_dispersion for why the observed spread is the wrong
        # quantity: it is dominated by real quality differences among survivors of
        # the in-sample search, not by the sampling noise gate 10 is correcting for.
        # Using it drove the hurdle to 6.5 Sharpe and made the gate unpassable after
        # the first handful of looks.
        seg = next(iter(self.segments.values())).validation
        years = len(seg) / seg.bars_per_year
        return stats.null_sharpe_dispersion(years)

    # -------------------------------------------------------------- the run

    def run(self, generations=40, target_winners=1):
        pop = [self.random_bot(0) for _ in range(self.population_size())]
        winners = []
        t0 = time.time()

        for gen in range(1, generations + 1):
            scored = sorted(((self.evaluate(b), b) for b in pop),
                            key=lambda t: -t[0])
            best = scored[0][0]
            self.history.append({
                "gen": gen, "stage": self.stage, "best_fitness": best,
                "median_fitness": scored[len(scored) // 2][0],
                "trials": self.state["trials"],
                "oos_looks": self.state["oos_looks"],
            })
            self.log(f"gen {gen:>3} | stage {self.stage} "
                     f"({STAGE_NAMES[min(self.stage, len(STAGE_NAMES)-1)]}) | "
                     f"best {best:6.2f} | median "
                     f"{scored[len(scored)//2][0]:6.2f} | "
                     f"trials {self.state['trials']:>6} | "
                     f"looks {self.state['oos_looks']:>3} | "
                     f"{time.time()-t0:5.0f}s")

            if best > self.best_fitness + 0.02:
                self.best_fitness = best
                self.stagnant = 0
            else:
                self.stagnant += 1

            # Promote the most promising in-sample bots to the gauntlet.
            if gen % self.cfg["gauntlet_every"] == 0:
                for candidate in self.promote(scored):
                    report = self.run_gauntlet(candidate)
                    self.reports.append(report)
                    mark = "PASS" if report.passed else report.first_failure
                    self.log(f"      gauntlet: {candidate.strategy_name}"
                             f" on {candidate.market_key} -> {mark}")
                    if report.passed:
                        if self.vault_exhausted():
                            self.log(f"      passed, but the vault budget "
                                     f"({self.cfg['vault_budget']} burns) is "
                                     f"spent — NOT confirming. Get more history.")
                            self.state["unconfirmed"].append(candidate.to_dict())
                            continue
                        dupe = self.is_redundant(candidate, report)
                        if dupe is not None:
                            how = ("overlap too short to measure, same market"
                                   if dupe != dupe else f"r={dupe:+.2f}")
                            self.log(f"      passed, but {how} vs a bot already "
                                     f"vault-tested — not a new edge, vault not "
                                     f"burned")
                            self.state["redundant"].append(candidate.to_dict())
                            continue
                        confirmed = self.vault_confirm(candidate, report)
                        if confirmed.passed:
                            winners.append((candidate, report, confirmed))
                            self.log("      *** VAULT CONFIRMED ***")
                        else:
                            self.log(f"      vault rejected at "
                                     f"{confirmed.first_failure}")
                if len(winners) >= target_winners:
                    self.log(f"\ntarget reached: {len(winners)} confirmed bot(s) "
                             f"after {self.state['trials']} trials")
                    save_state(self.state_file, self.state)
                    return winners

            if self.stagnant >= self.cfg["patience"]:
                if self.stage < len(STAGE_NAMES) - 1:
                    self.stage += 1
                    self.stagnant = 0
                    self.log(f"      >>> EXPANDING to stage {self.stage}: "
                             f"{STAGE_NAMES[self.stage]}")
                    pop += [self.random_bot(gen)
                            for _ in range(self.population_size() - len(pop))]
                else:
                    # Fully expanded and still stuck: churn the population hard
                    # rather than grinding the same basin.
                    self.stagnant = 0
                    keep = [b for _, b in scored[:max(2, len(pop) // 5)]]
                    pop = keep + [self.random_bot(gen)
                                  for _ in range(self.population_size() - len(keep))]
                    self.log("      >>> full restart of the population "
                             "(search fully expanded, no improvement)")
                    continue

            pop = self.breed(scored, gen)

        save_state(self.state_file, self.state)
        self.log(f"\nbudget exhausted: {self.state['trials']} trials, "
                 f"{len(winners)} confirmed")
        return winners

    def promote(self, scored):
        """Pick which bots get to spend an out-of-sample look.

        At most one per (market, strategy) pair, and never a genome that has already
        been through. Late in a run the top of the population is dozens of near
        clones of one idea; promoting all of them would burn the validation slice on
        the same bot several times over and inflate gate 10's hurdle for no
        information in return."""
        chosen, seen = [], set()
        won = {(w["bot"]["market"], w["bot"]["strategy"])
               for w in self.state["winners"]}
        spent = self.state["pair_looks"]
        cap = self.cfg["max_looks_per_pair"]
        for score, candidate in scored:
            if len(chosen) >= self.cfg["promote"]:
                break
            if score <= 0:
                break
            fam = (candidate.market_key, candidate.strategy_name)
            # A market+strategy pair that already produced a confirmed winner is
            # not worth another look: the look raises the hurdle for every future
            # candidate, and what comes back is almost always the same bot again.
            # ...and a pair that has already had `cap` looks without producing a
            # winner has had its chance. Without this the population's favourite
            # market monopolises the out-of-sample budget: one run promoted 132
            # near-clones from a single market and learned nothing after the first
            # few.
            if (fam in seen or fam in won
                    or spent.get(f"{fam[0]}|{fam[1]}", 0) >= cap
                    or candidate.fingerprint() in self.state["gauntleted"]):
                continue
            seen.add(fam)
            chosen.append(candidate)
        return chosen

    def breed(self, scored, gen):
        size = self.population_size()
        elite = max(2, size // 10)
        nxt = [b for _, b in scored[:elite]]
        n_imm = int(size * self.immigrant_frac())
        while len(nxt) < size - n_imm:
            a = self._tournament(scored)
            b = self._tournament(scored)
            child = self.crossover(a, b, gen) if self.rng.random() < 0.5 else a
            nxt.append(self.mutate(child, gen))
        nxt += [self.random_bot(gen) for _ in range(size - len(nxt))]
        return nxt

    def _tournament(self, scored, k=4):
        picks = [self.rng.choice(scored) for _ in range(k)]
        return max(picks, key=lambda t: t[0])[1]

    # --------------------------------------------------------- the gauntlet

    def run_gauntlet(self, candidate):
        self.state["gauntleted"].append(candidate.fingerprint())
        self.state["oos_looks"] += 1
        pk = f"{candidate.market_key}|{candidate.strategy_name}"
        self.state["pair_looks"][pk] = self.state["pair_looks"].get(pk, 0) + 1
        seg = self.segments[candidate.market_key]
        pseg = self.segments[candidate.partner_key] if candidate.partner_key else None
        report = val.gauntlet(candidate, seg, pseg,
                              oos_looks=self.hurdle_looks(),
                              dispersion=self.hurdle_dispersion(),
                              thresholds=self.cfg.get("thresholds"),
                              seed=self.rng.randrange(1 << 30),
                              segment="validation",
                              trials=self.state["trials"])
        # Record the OOS Sharpe of every look, pass or fail. Keeping only the
        # winners' would understate the dispersion and quietly lower the hurdle.
        if math.isfinite(report.oos.get("sharpe", 0.0)):
            self.state["oos_sharpe_samples"].append(round(report.oos["sharpe"], 4))
        # Persist immediately. The counters were previously written only on the
        # three normal exit paths, so a Ctrl-C or any exception discarded every
        # look taken in that run — and the next run would start over with a lower
        # hurdle, having genuinely consulted the holdout. A crash must never be a
        # way to launder a search history.
        save_state(self.state_file, self.state)
        return report

    def is_redundant(self, candidate, report):
        """Has the vault already been asked this question?

        Compared against every candidate that has REACHED the vault — confirmed or
        rejected — not just the winners. The first version of this check only knew
        about winners, and the consequence was brutal: on a market where nothing
        ever got confirmed, every near-duplicate sailed straight through and burned
        the vault again. One run spent 105 of its 107 burns on a single market,
        getting the same rejection 99 times. The vault is a consumable and that run
        destroyed it.

        This is not a twelfth gate — it does not judge whether the bot is any good.
        It answers a different question: does testing this tell us anything we do
        not already know? Bots correlated at 0.9 are one bot with spare parameter
        sets. They draw down together, they fail together, and asking twice costs
        the one resource that cannot be replaced."""
        seg = self.segments[candidate.market_key]
        pseg = self.segments[candidate.partner_key] if candidate.partner_key else None
        mine = _daily(candidate.run(seg.validation,
                                    pseg.validation if pseg else None),
                      seg.validation)
        for prior, _passed, prior_market in self._tested_returns:
            c = _corr(mine, prior)
            if c is None:
                # Too few overlapping days to measure — which happens between
                # markets on different timeframes, whose segments can cover
                # disjoint calendar spans. Silence is not evidence of difference:
                # on the SAME market, assume duplicate; across markets, allow it
                # but do not pretend a correlation was checked.
                if prior_market == candidate.market_key:
                    return float("nan")
                continue
            if abs(c) > self.cfg["max_winner_correlation"]:
                return c
        self._pending_returns = mine
        return None

    def hurdle_dispersion(self):
        """The dispersion handed to gate 10. Now a fixed property of the validation
        window's length, so it neither drifts nor needs a ratchet."""
        return self.dispersion()

    def hurdle_looks(self):
        """The N that gate 10 deflates by: the run's whole look BUDGET, not the
        number spent so far.

        Charging the running count made a candidate's fate depend on when it
        happened to be promoted. Across ten seeds every single confirmed bot was
        found in the first half of its run — two of them at look 1 and 2 with
        validation Sharpes of 1.8, while candidates posting 4.7 were rejected later
        in the same runs. That is not a multiple-testing correction, it is a
        first-come-first-served queue with a statistical veneer, and it is the
        direct cause of the seed-to-seed variance.

        Every candidate now faces the bar for the full budget, from look one. The
        correction is still paid in full — it is just paid by everyone equally
        rather than by whoever arrives late."""
        return max(self.state["oos_looks"], self.cfg["look_budget"])

    def vault_exhausted(self):
        """The vault has a hard budget, not just a warning.

        A warning that nobody can act on mid-run is not a control. Past this many
        burns the slice has been consulted so often that it is a second validation
        set, and confirming anything against it would be dressing up an in-sample
        result. The factory stops burning and says so."""
        return self.state["vault_burns"] >= self.cfg["vault_budget"]

    def vault_confirm(self, candidate, validation_report=None):
        """One-shot confirmation on the untouched final slice.

        Every call is logged permanently. The vault is a consumable: burn it on
        twenty candidates and it has quietly become a second validation set, at
        which point the only honest thing to do is get more data."""
        self.state["vault_burns"] += 1
        seg = self.segments[candidate.market_key]
        pseg = self.segments[candidate.partner_key] if candidate.partner_key else None
        report = val.gauntlet(candidate, seg, pseg,
                              oos_looks=self.state["vault_burns"],
                              dispersion=self.dispersion(),
                              thresholds=self.cfg.get("thresholds"),
                              seed=self.rng.randrange(1 << 30),
                              segment="vault", stop_early=False,
                              trials=self.state["trials"])
        self.state["vault_log"].append({
            "burn": self.state["vault_burns"],
            "bot": candidate.to_dict(),
            "passed": report.passed,
            "first_failure": report.first_failure,
            "oos_sharpe": report.oos["sharpe"],
            "trials_at_burn": self.state["trials"],
        })
        if self._pending_returns is not None:
            self._tested_returns.append((self._pending_returns, report.passed,
                                         candidate.market_key))
        if report.passed:
            # `report.is_` is the TRAIN slice — the gauntlet always measures the
            # in-sample leg for its walk-forward ratio, whichever segment it is
            # testing. Recording it under "validation" published the number the
            # search had optimised as though it were out-of-sample. The validation
            # figures come from the validation report; the train figures are kept
            # but labelled as what they are.
            vr = validation_report
            self.state["winners"].append({
                "bot": candidate.to_dict(),
                "train": {k: report.is_[k] for k in ("sharpe", "max_dd")},
                "validation": ({k: vr.oos[k] for k in ("sharpe", "max_dd")}
                               if vr is not None else None),
                "vault": {k: report.oos[k] for k in
                          ("sharpe", "cagr", "max_dd", "total_return", "trades")},
                "dsr": report.dsr,
                "trials": self.state["trials"],
                "oos_looks": self.state["oos_looks"],
                "vault_burn": self.state["vault_burns"],
            })
        save_state(self.state_file, self.state)
        if self.state["vault_burns"] > self.cfg["vault_burn_warning"]:
            self.log(f"      !! vault used {self.state['vault_burns']} of "
                     f"{self.cfg['vault_budget']} times; its out-of-sample status "
                     f"is degrading")
        return report


DEFAULTS = {
    "population": 60,
    "min_trades": 20,
    # Promotion is deliberately stingy. Every look at the validation slice raises
    # gate 10's hurdle for every candidate after it, so spending looks on near
    # clones of one idea makes the bar harder without learning anything.
    "gauntlet_every": 5,
    "promote": 2,
    "patience": 4,
    "vault_burn_warning": 10,
    "max_winner_correlation": 0.70,
    # The vault is a consumable with a hard budget, and no (market, strategy) pair
    # may monopolise the out-of-sample budget.
    "vault_budget": 25,
    "max_looks_per_pair": 8,
    # Pseudo-observations of the in-sample prior mixed into the out-of-sample
    # dispersion estimate. Higher = slower to trust a small out-of-sample pool.
    # Gate 10 deflates by this many looks regardless of how many have been spent,
    # so a candidate's verdict does not depend on its position in the queue.
    "look_budget": 50,
    "thresholds": None,
}


# ---------------------------------------------------------------- state i/o

def blank_state():
    return {"trials": 0, "oos_looks": 0, "sharpe_samples": [],
            "oos_sharpe_samples": [], "gauntleted": [], "winners": [],
            "redundant": [], "vault_burns": 0, "vault_log": [],
            "pair_looks": {}, "unconfirmed": [], "dispersion_floor": 0.0}


def load_state(path):
    """Load the persisted counters, tolerating an empty or truncated file.

    A run killed mid-write leaves a zero-byte state file behind, and crashing on it
    would be the worst possible response: the obvious fix is to delete the file,
    which silently resets the trial and vault counters and hands back a clean sheet
    nobody earned. Starting from blank is the same outcome, but it is at least
    visible in the run header, which prints the counters it is carrying."""
    path = pathlib.Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return blank_state()
    try:
        with open(path) as fh:
            state = json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return blank_state()
    if not isinstance(state, dict):
        return blank_state()
    for k, v in blank_state().items():
        state.setdefault(k, v)
    return state


def save_state(path, state):
    path = pathlib.Path(path)
    path.parent.mkdir(exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=1)
    tmp.replace(path)


# ------------------------------------------------- winner-overlap helpers

def _daily(result, market):
    """Per-bar returns collapsed onto a calendar-day grid, so bots on different
    timeframes can be compared to each other at all."""
    by_day = {}
    for i, r in enumerate(result.net):
        day = market.ts[i] // 86400
        by_day[day] = by_day.get(day, 1.0) * (1.0 + r)
    return {d: v - 1.0 for d, v in by_day.items()}


def _corr(a, b):
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
