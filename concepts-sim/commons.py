"""
The Commons (GAME-CONCEPTS.md #21) — the kill test, run.

THE BET
    An unrigged tragedy of the commons. The simulation isn't tuned to collapse — it
    collapses if you collapse it — and the game is the conversation about whether to.

THE STATED KILL CONDITION
    "The model has a stable dominant strategy, a solver finds it in an hour, and the
    conversation becomes theatre."

WHY THIS ONE IS DANGEROUS
    In the textbook commons, defection IS dominant. That is the entire point of the
    parable, and it is also exactly what would kill this as a *game*: if fishing hard is
    correct no matter what anyone else does, then talking is decoration and six players are
    just watching a lecture play out. So this test has a live chance of failing, and the
    honest version has to be able to return that.

WHAT DECIDES IT
    D1  Is any single effort level a dominant strategy — the best response regardless of
        what the other five do? If yes, the conversation cannot matter. Dead.

    D2  Does mutual restraint actually beat mutual greed? If all-greedy out-earns
        all-restrained, there is no tragedy to negotiate about, only a resource to strip.

    D3  What does unilateral restraint cost? If holding back while others don't is ruinous,
        then agreements are unenforceable in a way no amount of talking fixes, and the
        conversation is theatre by a slower route.

    A game needs all three: no dominant strategy, a cooperative surplus worth protecting,
    and a betrayal cost that stings without being fatal.

No dependencies, deterministic, runs in about two seconds.
"""

# --- The fishery -----------------------------------------------------------------------

# Baseline. These are NOT the numbers I guessed — the guessed set (r=0.45, q=0.55,
# cheap effort) failed D3 outright, and the sweep in D4 found only four viable points in
# seventy-two. This is one of them. Every viable point has LOW CATCHABILITY, which is the
# design finding: the fishery is only worth arguing about when boats are inefficient and
# expensive. A fleet that can strip the stock in three periods has nothing to negotiate.
K = 1000.0      # carrying capacity
R = 0.45        # intrinsic growth rate
Q = 0.15        # catchability — harvest per unit effort per unit stock
PRICE = 1.0
T = 24          # periods in a session
N = 6           # players
S0 = 700.0      # starting stock

# Cost per unit of effort, paid whether or not fish are there.
#
# UNITS BUG, v1: this was a bare 0.16 while revenue per unit effort is Q*stock — of order
# 385 at a healthy stock. The cost term was three orders of magnitude too small to matter,
# so sweeping it changed nothing and the sweep reported "0/48 viable, structural failure."
# That conclusion was an artifact of a parameter that could not move.
#
# Cost is now expressed as a FRACTION of revenue per unit effort at carrying capacity,
# which is the only scale on which it can compete with fishing.
COST_FRAC = 0.30
COST = COST_FRAC * Q * K

EFFORTS = [round(0.02 * i, 2) for i in range(1, 26)]   # 0.02 .. 0.50


def simulate(efforts, periods=T):
    """
    Run the fishery with fixed per-player efforts. Returns (payoffs, final_stock).

    Logistic growth, simultaneous harvest, harvest capped at the standing stock and shared
    proportionally if the fleet would take more than exists.
    """
    stock = S0
    payoffs = [0.0] * len(efforts)
    for _ in range(periods):
        wanted = [Q * e * stock for e in efforts]
        total = sum(wanted)
        if total > stock:                       # scarcity: everyone gets a share
            scale = stock / total if total > 0 else 0.0
            wanted = [w * scale for w in wanted]
            total = sum(wanted)
        for i, w in enumerate(wanted):
            payoffs[i] += PRICE * w - COST * efforts[i]
        stock -= total
        stock += R * stock * (1 - stock / K)    # what's left breeds
        stock = max(stock, 0.0)
    return payoffs, stock


# --- D1: is there a dominant strategy? --------------------------------------------------

OPPONENT_PROFILES = {
    "all restrained (0.06)":  [0.06] * (N - 1),
    "all moderate (0.14)":    [0.14] * (N - 1),
    "all greedy (0.30)":      [0.30] * (N - 1),
    "all rapacious (0.46)":   [0.46] * (N - 1),
    "mixed":                  [0.06, 0.10, 0.16, 0.30, 0.44],
}


def best_response(opponents):
    """My best constant effort, given what the other five are doing."""
    best_e, best_pay, best_stock = None, float("-inf"), 0.0
    for e in EFFORTS:
        pay, stock = simulate([e] + list(opponents))
        if pay[0] > best_pay:
            best_e, best_pay, best_stock = e, pay[0], stock
    return best_e, best_pay, best_stock


def d1_dominance():
    rows = []
    for label, opp in OPPONENT_PROFILES.items():
        e, pay, stock = best_response(opp)
        rows.append((label, e, pay, stock))
    return rows


# --- D2: is there a cooperative surplus? ------------------------------------------------

def d2_surplus():
    out = {}
    for label, e in [("everyone restrained", 0.06), ("everyone moderate", 0.14),
                     ("everyone greedy", 0.30), ("everyone rapacious", 0.46)]:
        pay, stock = simulate([e] * N)
        out[label] = (e, pay[0], sum(pay), stock)
    # The best the group could do if it could bind itself to one shared effort level.
    best = max(((e, simulate([e] * N)) for e in EFFORTS), key=lambda x: sum(x[1][0]))
    out["_social_optimum"] = (best[0], best[1][0][0], sum(best[1][0]), best[1][1])
    return out


# --- D3: what does unilateral restraint cost? -------------------------------------------

def d3_betrayal():
    """I hold to an agreed low effort; the others quietly don't."""
    agreed = 0.06
    rows = []
    for label, defect in [("nobody defects", 0.06), ("others go moderate", 0.14),
                          ("others go greedy", 0.30), ("others go rapacious", 0.46)]:
        pay, stock = simulate([agreed] + [defect] * (N - 1))
        my_alt, _ = simulate([defect] * N)
        rows.append((label, pay[0], my_alt[0], stock))
    return rows


def bar(v, vmax, width=28):
    return "#" * max(0, int(round((v / vmax) * width))) if vmax > 0 else ""


# --- D4: is there ANY parameter region where all three hold? ----------------------------
#
# A single FAIL at one point in parameter space is not a dead concept — the card's own test
# said "find the curve." This asks whether a curve exists at all. If no combination of
# growth rate, catchability and effort cost produces a fishery worth arguing over, the
# concept is dead on structure rather than on tuning, and that is a much stronger result.

def evaluate(r, q, cost_frac, periods=T, n=N):
    """
    Run D1/D2/D3 at one point in parameter space. Returns (p1, p2, p3, detail).

    `cost_frac` is cost per unit effort as a fraction of revenue per unit effort at
    carrying capacity — see the units note at the top.
    """
    global R, Q, COST, T, N
    saved = (R, Q, COST, T, N)
    R, Q, COST, T, N = r, q, cost_frac * q * K, periods, n
    try:
        profiles = {
            "restrained": [0.06] * (n - 1),
            "moderate":   [0.14] * (n - 1),
            "greedy":     [0.30] * (n - 1),
            "rapacious":  [0.46] * (n - 1),
        }
        brs = {best_response(o)[0] for o in profiles.values()}
        p1 = len(brs) > 1

        low = simulate([0.06] * n)[0][0]
        high = simulate([0.30] * n)[0][0]
        # A cooperative surplus only means something if greed is a REAL temptation. When
        # effort costs enough that fishing hard loses money outright, "restraint wins"
        # is true and worthless — there is no dilemma, just a bad option nobody takes.
        # v1 returned a 99.0 sentinel here and counted those points as viable, which
        # inflated the viable region with cases that had no tragedy in them at all.
        greed_is_tempting = high > 0.15 * low
        surplus = low / high if high > 0 else float("inf")
        p2 = greed_is_tempting and surplus > 1.15

        worst = 1.0
        for d in (0.14, 0.30, 0.46):
            kept = simulate([0.06] + [d] * (n - 1))[0][0]
            alt = simulate([d] * n)[0][0]
            if alt > 0:
                worst = min(worst, kept / alt)
        p3 = 0.25 < worst < 0.95
        return p1, p2, p3, (len(brs), surplus, worst)
    finally:
        R, Q, COST, T, N = saved


def d4_sweep():
    hits = []
    grid = []
    for r in (0.25, 0.45, 0.65, 0.85):
        for q in (0.15, 0.30, 0.55):
            for cf in (0.0, 0.10, 0.20, 0.30, 0.40, 0.55):
                p1, p2, p3, detail = evaluate(r, q, cf)
                grid.append((r, q, cf, p1, p2, p3, detail))
                if p1 and p2 and p3:
                    hits.append((r, q, cf, detail))
    return grid, hits


if __name__ == "__main__":
    print("=" * 76)
    print("THE COMMONS (#21) — kill test")
    print(f"  {N} players · {T} periods · K={K:.0f} r={R} q={Q} cost={COST}")
    print("=" * 76)

    print("\nD1  Is any effort level a DOMINANT strategy?")
    print("    Kill condition: the same best response against every opponent profile.")
    print("    That would mean nothing anyone says can change what you should do.\n")
    print("      opponents doing...          my best effort   my payoff   final stock")
    rows = d1_dominance()
    for label, e, pay, stock in rows:
        print(f"      {label:26s}      {e:.2f}        {pay:7.1f}      {stock:6.1f}")
    responses = {e for _, e, _, _ in rows}
    dominant = len(responses) == 1
    print(f"\n      distinct best responses: {len(responses)}  ({sorted(responses)})")
    print(f"      dominant strategy: {'YES — this is fatal' if dominant else 'NO'}")

    print("\n" + "-" * 76)
    print("\nD2  Does mutual restraint actually beat mutual greed?")
    print("    Kill condition: greed wins even when everyone does it. Then there is no")
    print("    tragedy to negotiate about — just a pile of fish and a countdown.\n")
    d2 = d2_surplus()
    opt = d2.pop("_social_optimum")
    vmax = max(v[1] for v in d2.values())
    print("      everyone plays...      effort   payoff each   final stock")
    for label, (e, mine, _tot, stock) in d2.items():
        print(f"      {label:22s}  {e:.2f}     {mine:7.1f}      {stock:6.1f}  {bar(mine, vmax)}")
    print(f"\n      best shared effort:     {opt[0]:.2f}     {opt[1]:7.1f}      {opt[3]:6.1f}")
    greed_pay = d2["everyone greedy"][1]
    if greed_pay > 0:
        surplus = d2["everyone restrained"][1] / greed_pay
        print(f"      restraint vs greed:     {surplus:.2f}x")
    else:
        surplus = float("inf")
        print("      restraint vs greed:     greed loses money outright — no dilemma here")

    print("\n" + "-" * 76)
    print("\nD3  What does keeping your word cost when others don't?")
    print("    Kill condition: ruinous. An agreement nobody can afford to keep is not a")
    print("    negotiation, it is a formality before the same outcome.\n")
    print("      situation                 I keep my word   I defect too   final stock")
    d3 = d3_betrayal()
    for label, kept, alt, stock in d3:
        ratio = kept / alt if alt else 0
        print(f"      {label:24s}    {kept:7.1f}       {alt:7.1f}       {stock:6.1f}   "
              f"({ratio:.0%} of defecting)")
    # Only compare against defections that actually PAY. Where mass defection loses money
    # outright, the ratio compares two losses and inverts the meaning: at the rapacious
    # profile, keeping your word loses 19 while joining in loses 265, and reporting that as
    # "7% of defecting" reads as a catastrophe when it is the best outcome on the board.
    # evaluate() already skipped these; the headline did not, and disagreed with the sweep.
    payable = [(k, a) for _, k, a, _ in d3 if a > 0]
    worst = min(k / a for k, a in payable) if payable else 1.0

    print("\n" + "-" * 76)
    print("\nD4  Is there ANY parameter region where all three hold?")
    print("    A failure at one point is a tuning result. A failure everywhere is a")
    print("    structural one. 72 points across growth rate, catchability and effort cost.\n")
    grid, hits = d4_sweep()
    print(f"      viable points: {len(hits)}/{len(grid)}")
    if hits:
        print("\n      r     q     cost*   best-responses  restraint:greed  sucker payoff")
        for r, q, cost, (nbr, surp, w) in hits[:12]:
            print(f"      {r:.2f}  {q:.2f}  {cost:.2f}         {nbr}            "
                  f"{surp:5.2f}x          {w:.0%}")
        if len(hits) > 12:
            print(f"      ... and {len(hits) - 12} more")
        costs = sorted({h[2] for h in hits})
        print(f"\n      cost fractions that work: {costs}  (baseline {COST_FRAC})")
    else:
        print("      none. The concept fails on structure, not on tuning.")

    print("\n" + "=" * 76)
    print("VERDICT")
    print("=" * 76)
    p1 = not dominant
    p2 = d2["everyone greedy"][1] > 0.15 * d2["everyone restrained"][1] and surplus > 1.15
    p3 = 0.25 < worst < 0.95
    for name, ok, why in [
        ("D1 no dominant strategy", p1, f"{len(responses)} distinct best responses"),
        ("D2 cooperative surplus exists", p2,
         f"restraint pays {surplus:.2f}x greed" if surplus != float("inf")
         else "greed loses money — no dilemma"),
        ("D3 betrayal stings, isn't fatal", p3,
         f"worst case, keeping your word earns {worst:.0%} of defecting"),
    ]:
        print(f"  [{'PASS' if ok else 'FAIL'}]  {name:32s}  {why}")
    print(f"  [{'PASS' if hits else 'FAIL'}]  {'D4 a viable region exists':32s}  "
          f"{len(hits)}/{len(grid)} parameter points work")
    print()
    if p1 and p2 and p3:
        print("  The stated kill condition is NOT met at the baseline numbers.")
    elif hits:
        print("  The kill condition IS met at the baseline numbers — but a viable region")
        print("  exists. This is a TUNING result, not a dead concept. The baseline made")
        print("  effort too cheap: at cost=0.16 the correct answer is max effort against")
        print("  almost anything, so agreements have nothing to hold them up.")
    else:
        print("  The kill condition IS met and no viable region exists. Structural. Stop.")
    print()
    print("  What this does NOT show: whether six people will actually talk, whether the")
    print("  numbers are legible at the table, or whether the argument is fun. It shows")
    print("  only that the incentives leave something to argue about — which had to be")
    print("  true first, and is the half a playtest cannot repair.")
