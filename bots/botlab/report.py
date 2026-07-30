"""Writes the run up — including, and especially, when it found nothing.

Two outputs:
  * `bots/REPORT.md`          the standing record of the latest run
  * `bots/state/LOOP_LOG.md`  one line per generation, newest at the bottom,
                              matching the convention in the repo root
"""

from __future__ import annotations

import json
import os
import time

from . import gauntlet, portfolio
from .genome import Genome, SearchSpace
from .markets import universe
from .state import RunState

FUNNEL_ORDER = ["G0-market", "G1-oos", "G2-replication", "G3-controls", "G4-stress",
                "G5-permutation", "G6-multiplicity", "G7-stress-pool", "unknown"]


def append_loop_log(path: str, rec: dict, verdicts: list, space: SearchSpace,
                    st: RunState) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# Bot Loop Log\n\nOne line per generation. Newest at the bottom.\n\n"
                     "Format: `G<n> L<expansion level> · <what was searched> · <what passed>`\n\n---\n\n")
        if verdicts:
            found = "; ".join(f"**{v.bot_id}** on {v.market} "
                              f"(replSR {v.perf.get('repl_alpha_sr', 0):+.2f})" for v in verdicts)
        else:
            found = "nothing passed"
        fh.write(f"G{rec['generation']} L{rec['level']} · {rec['candidates']} candidates over "
                 f"{len(rec['markets'])} markets, {rec['gauntlets']} gauntlets, "
                 f"best screen fit {rec['best_screen_fitness']:+.2f} "
                 f"({rec['trials_total']} trials on the ledger) · {found}\n\n")


def _cell(x) -> str:
    """Escape pipes: gate evidence contains things like `worst |alphaSR| 0.13`,
    and an unescaped pipe silently splits the cell and mangles the whole table."""
    return str(x).replace("|", "\\|")


def _table(rows: list[list[str]], head: list[str]) -> str:
    out = ["| " + " | ".join(_cell(h) for h in head) + " |",
           "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        out.append("| " + " | ".join(_cell(x) for x in r) + " |")
    return "\n".join(out)


def write_report(path: str, st: RunState, cfg: gauntlet.GauntletConfig,
                 calibration: list[dict] | None = None) -> str:
    proven = [(Genome.from_dict(p["genome"]), p["verdict"], p) for p in st.proven]
    port = portfolio.build([g for g, _, _ in proven]) if proven else {"n_bots": 0}

    L: list[str] = []
    L.append("# Bot factory: run report")
    L.append("")
    L.append(f"_Generated {time.strftime('%Y-%m-%d %H:%M:%S')} from `{os.path.basename(st.path)}`._")
    L.append("")
    L.append("## Result")
    L.append("")
    if proven:
        sigs = st.proven_signatures()
        markets = sorted({p["genome"]["market"] for p in st.proven})
        L.append(f"**{len(sigs)} distinct strategies passed all seven gates** "
                 f"({len(proven)} genomes — several are the same rule at a different "
                 f"threshold or gene weight, which is why the headline counts "
                 f"structures rather than genomes).")
        L.append("")
        L.append(f"{st.trials:,} candidates were screened across {st.generation} "
                 f"generations and {len(st.expansions)} search-space expansions; "
                 f"{st.gauntlet_runs} reached the gauntlet; {st.backtests:,} backtests "
                 f"were run.")
        L.append("")
        if len(markets) == 1:
            L.append(f"**All of them trade one market family: `{markets[0]}`.** Ten other "
                     "tradeable families were searched every generation and yielded "
                     "nothing that survived the ladder. That is the most informative "
                     "result in this report, and it is the expected one: the catalogue "
                     "deliberately contains families where the correct answer is *do not "
                     "trade this* (the strongest planted edges sit behind a 28bp spread, "
                     "or behind 0.30bp/bar funding). A search that returned winners "
                     "everywhere would be evidence against itself.")
        else:
            L.append(f"Markets represented: {', '.join('`' + m + '`' for m in markets)}.")
    else:
        L.append(f"**No bot passed.** {st.trials} candidates were screened across "
                 f"{st.generation} generations and {st.gauntlet_runs} reached the gauntlet. "
                 "That is a result, not a failure to produce one: it says the edges planted "
                 "in this catalogue, at these costs, are not reachable by the strategy space "
                 "searched so far. The funnel below shows which gate did the killing, which "
                 "is the useful information — see 'What to do next'.")
    L.append("")

    # ---- funnel ------------------------------------------------------------
    L.append("## Rejection funnel")
    L.append("")
    L.append("Where candidates died. A healthy funnel kills most bots early; a funnel that "
             "kills everything at G5/G6 means the search is finding in-sample fits, and a "
             "funnel with kills at G3 means something is wrong with the harness.")
    L.append("")
    total_fail = sum(st.fail_counts.values())
    rows = []
    for k in FUNNEL_ORDER:
        v = st.fail_counts.get(k, 0)
        if v:
            rows.append([k, v, f"{v / max(total_fail, 1):.0%}", _gate_meaning(k)])
    if rows:
        L.append(_table(rows, ["gate", "rejected", "share", "what that gate proves"]))
    else:
        L.append("_No gauntlet rejections recorded._")
    L.append("")

    # ---- proven bots -------------------------------------------------------
    if proven:
        L.append("## Proven bots")
        L.append("")
        for g, v, meta in proven:
            perf = v.get("perf", {})
            L.append(f"### `{g.bot_id}` — {g.market}")
            L.append("")
            L.append(f"```\n{g.describe()}\n```")
            L.append("")
            spec = universe.get(g.market)
            L.append(f"- market: **{g.market}** ({spec.asset_class}, "
                     f"vol {spec.vol_ann:.0%}, spread {spec.costs.spread_bps:.1f}bp, "
                     f"perfect-foresight ceiling SR {spec.oracle_sharpe_ceiling():.2f})")
            L.append(f"- found in generation {meta.get('found_generation', '?')} "
                     f"via {g.origin}" + (f" from {', '.join(g.parents)}" if g.parents else ""))
            L.append("")
            grows = []
            for s in v.get("stages", []):
                grows.append(["PASS" if s["passed"] else "FAIL", s["name"], s["detail"]])
            L.append(_table(grows, ["", "gate", "evidence"]))
            L.append("")
            L.append("Confirmation-pool performance (third disjoint instance pool, 20 instances):")
            L.append("")
            L.append(_table([[
                f"{perf.get('stress_alpha_sr', 0):+.2f}",
                f"{perf.get('stress_sr', 0):+.2f}",
                f"{perf.get('stress_cagr', 0):+.1%}",
                f"{perf.get('stress_vol', 0):.1%}",
                f"{perf.get('stress_max_dd', 0):.1%}",
                f"{perf.get('stress_calmar', 0):.2f}",
                f"{perf.get('stress_turnover', 0):.0f}",
                f"{perf.get('stress_cost_drag', 0):.2%}",
                f"{perf.get('stress_exposure', 0):.2f}",
            ]], ["alphaSR", "SR", "CAGR", "vol", "medDD", "Calmar", "trades/yr", "cost/yr", "avg lev"]))
            L.append("")
            xm = v.get("cross_market") or {}
            if xm:
                best = sorted(xm.items(), key=lambda kv: -kv[1])[:6]
                L.append("Travels to (alphaSR on other families, not a gate): "
                         + ", ".join(f"`{k}` {x:+.2f}" for k, x in best))
                L.append("")
            L.append("<details><summary>genome JSON</summary>\n\n```json\n"
                     + json.dumps(g.to_dict(), indent=2) + "\n```\n\n</details>")
            L.append("")

        L.append("## Portfolio")
        L.append("")
        L.append("```")
        L.append(portfolio.format_summary(port))
        L.append("```")
        L.append("")
        if len(port.get("markets", [])) > 1:
            L.append("The two portfolio numbers differ because this lab generates each market "
                     "family independently, so cross-family correlation is structurally zero — "
                     "an assumption real asset classes violate exactly when it matters. Plan "
                     f"with the rho={port.get('adverse_cross_corr', 0.3):.1f} number.")
        else:
            L.append("There is only one number because there is only one market family, so "
                     "the correlation assumption never bites. Correlation *between* these legs "
                     "is measured directly (they share instances), and the blend's small "
                     "improvement over the best single bot is what two imperfectly correlated "
                     "expressions of the same effect buy you — not diversification.")
        L.append("")

    # ---- hall of fame ------------------------------------------------------
    if st.hall:
        L.append("## Hall of fame (screen scores — evidence of nothing, kept for breeding)")
        L.append("")
        rows = []
        for e in st.hall[:15]:
            g = Genome.from_dict(e["genome"])
            rows.append([f"`{g.bot_id}`", g.market, f"{e['fitness']:+.2f}",
                         f"{e['alpha_sharpe']:+.2f}", e["n_trades"], f"`{g.describe()[:66]}`"])
        L.append(_table(rows, ["bot", "market", "screen fit", "screen alphaSR", "trades", "rule"]))
        L.append("")

    # ---- expansion history -------------------------------------------------
    if st.expansions:
        L.append("## Expansions")
        L.append("")
        L.append(_table([[e["generation"], e["level"], e.get("reason", ""),
                          e.get("to", "")] for e in st.expansions],
                        ["generation", "new level", "trigger", "new space"]))
        L.append("")

    # ---- generation log ----------------------------------------------------
    if st.log:
        L.append("## Generations")
        L.append("")
        rows = [[r["generation"], r["level"], r["candidates"], len(r["markets"]),
                 r["gauntlets"], r.get("priors_tested", 0), r["proven_new"],
                 f"{r['best_screen_fitness']:+.2f}", f"{r['screen_seconds']:.0f}s"]
                for r in st.log[-40:]]
        L.append(_table(rows, ["gen", "level", "candidates", "markets", "gauntlets",
                               "of which priors", "proven", "best screen fit",
                               "screen time"]))
        L.append("")

    # ---- calibration -------------------------------------------------------
    if calibration:
        L.append("## Market calibration")
        L.append("")
        L.append("`ceiling` is the perfect-foresight Sharpe bound implied by the planted "
                 "structure; `gross`/`net` are the best textbook archetype without and with "
                 "costs. A family whose net number is negative is a market where the honest "
                 "answer is *don't trade this*.")
        L.append("")
        L.append("The two `control_*` rows show a positive net number (~+0.3) and that is "
                 "expected, not a contradiction: it is the **maximum over 13 archetypes of a "
                 "median over 6 instances**, which is a selection statistic, and on 12 years "
                 "of daily data its null spread is about that size. The point of the controls "
                 "is not that no single statistic on them is ever positive — it is that "
                 "nothing survives *replication* on them, which is what the gauntlet tests "
                 "and what `run.py fpr` measures end to end (0 certified from 3,000 "
                 "candidates).")
        L.append("")
        rows = [[r["market"], f"{r['vol_measured']:.1%}", f"{r['ceiling_sr']:.2f}",
                 f"{r['best_gross_sr']:+.2f}", f"{r['best_net_alpha_sr']:+.2f}",
                 f"{r['cost_bite']:+.2f}",
                 f"{r['n_archetypes_net_positive']}/{r['n_archetypes']}"]
                for r in calibration]
        L.append(_table(rows, ["family", "vol", "ceiling SR", "gross alphaSR",
                               "net alphaSR", "cost bite", "archetypes net +"]))
        L.append("")

    # ---- standard of proof -------------------------------------------------
    L.append("## Standard of proof used")
    L.append("")
    L.append("```json")
    L.append(json.dumps(cfg.to_dict(), indent=2))
    L.append("```")
    L.append("")
    L.append("## What to do next")
    L.append("")
    if proven:
        L.append("1. Re-run the identical gauntlet on **real bars** for the same instrument "
                 "type: `python bots/run.py verify <bot_id> --data path/to/csvs`. Until that "
                 "passes, a proven bot is a proven bot *about a market model*.")
        L.append("2. Check the `travels to` row. A rule that only works on the one family it "
                 "was bred on is a fit to that generator's parameters.")
        L.append("3. Paper-trade before funding. Nothing in this repository has touched a "
                 "live order book, a real spread, or a real fill.")
    else:
        L.append("1. Read the funnel. Mass death at **G2** means the search is finding "
                 "instance-specific luck — raise `screen_instances` so screening is harder to "
                 "fool. Mass death at **G4** means the edge is real but smaller than the "
                 "spread; look at cheaper families or lower-turnover genomes.")
        L.append("2. Let it expand further: `--max-generations` higher, or `--target 1`. "
                 "Expansion unlocks primitives and families it has not tried yet.")
        L.append("3. Do **not** relax `GauntletConfig` to manufacture a pass. A bot that "
                 "only passes a weakened gauntlet is worth less than no bot, because it will "
                 "be funded.")
    L.append("")

    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    text = "\n".join(L)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def _gate_meaning(gate: str) -> str:
    return {
        "G0-market": "candidate was aimed at a control family",
        "G1-oos": "worked only on the bars the search scored (in-sample fit)",
        "G2-replication": "worked only on the instances it was bred on (instance luck)",
        "G3-controls": "showed profit on a random walk (artifact or harness bug)",
        "G4-stress": "edge smaller than 2x costs or one bar of delay",
        "G5-permutation": "no better than its own block-bootstrapped null",
        "G6-multiplicity": "not surprising given how many candidates were tried",
        "G7-stress-pool": "failed to replicate a second time on a third pool",
        "unknown": "unclassified",
    }.get(gate, "")
