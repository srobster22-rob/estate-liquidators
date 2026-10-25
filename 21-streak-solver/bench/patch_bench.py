# Second patch: strip the dead cash-out banner from index.html and adapt the bench harness
# (engine.js / game.js) to the STREAK rules: no forfeit, no end-anytime, forced busts eaten.
import io, sys, re

def patch(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            print('PATCH FAIL in %s (%d matches): %r' % (path, n, old[:90])); sys.exit(1)
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)

# ---- index.html: dead code ----
s = io.open('index.html', encoding='utf-8').read()
a = s.index("function applyForcedBust(){")
b = s.index("function toggleEdit(){")
s = s[:a] + s[b:]
a = s.index("  const co=document.getElementById('cashoutBanner');")
b = s.index("  // show bust risk in the hint line when meaningful")
s = s[:a] + "  document.getElementById('cashoutBanner').style.display='none';\n" + s[b:]
s = s.replace("  if(pending || pendingForcedBust){ return; }", "  if(pending){ return; }")
io.open('index.html', 'w', encoding='utf-8', newline='\n').write(s)

# ---- bench/engine.js ----
patch('bench/engine.js', [
  ("      RANKS, VAL, PTS_PERFECT, EXACT_LIMIT,",
   "      RANKS, VAL, EXACT_LIMIT,\n      perfect: () => PTS_PERFECT,\n      chooseForcedBust,\n"
   "      setBustRule: (v) => { RULE_BUST_BREAKS_STREAK = !!v; },\n      setPerfect: (v) => { PTS_PERFECT = v ? 1000 : 0; },"),
])

# ---- bench/game.js ----
patch('bench/game.js', [
  ("// Self-play driver: deals a shuffled 52-card deck to the solver one card at a time\n"
   "// and returns the real final score. Mirrors dealCard()'s flow in index.html,\n"
   "// including the forced-bust end/eat decision.",
   "// Self-play driver: deals a shuffled 52-card deck to the solver one card at a time\n"
   "// and returns the real final score. Mirrors dealCard()'s flow in index.html: there is\n"
   "// no early exit in this game, so a card that busts every slot is always eaten and the\n"
   "// only decision is which slot to sacrifice (chooseForcedBust, the app's own function)."),
])
s = io.open('bench/game.js', encoding='utf-8').read()
a = s.index("// Replicates the forced-bust branch of dealCard()")
b = s.index("function playGame(E, seed, opts = {}) {")
s = s[:a] + s[b:]
patch_pairs = [
  ("  const { RANKS, handTotal, resolvePlace, resolvePass, PTS_PERFECT } = E;",
   "  const { RANKS, handTotal, resolvePlace, resolvePass } = E;"),
  ("  E.setMode(opts.mode || 'balanced');\n  E.setTarget(opts.target || 0);",
   "  E.setMode(opts.mode || 'balanced');\n  E.setTarget(opts.target || 0);\n"
   "  if (opts.bustBreaks !== undefined) E.setBustRule(opts.bustBreaks);\n"
   "  if (opts.perfect !== undefined) E.setPerfect(opts.perfect);"),
  ("  const stats = { busts: 0, passes: 0, win21: 0, win5: 0, win777: 0, win5x21: 0,\n"
   "                  cashedOut: false, stoppedEarly: false, forfeited: false, cardsDealt: 0, maxStreak: 0,\n"
   "                  chainBonus: 0, clears: 0, chainHist: [0, 0, 0, 0, 0] };\n"
   "  // chainHist[k] = number of chains of length k (index 4 = length 4)",
   "  const stats = { busts: 0, forcedBusts: 0, passes: 0, win21: 0, win5: 0, win777: 0, win5x21: 0,\n"
   "                  cashedOut: false, stoppedEarly: false, forfeited: false, cardsDealt: 0, maxStreak: 0,\n"
   "                  chainBonus: 0, clears: 0, chainHist: [0, 0, 0, 0, 0] };\n"
   "  // chainHist[k] = number of streaks of length k (index 4 = length 4 or more)"),
  ("    // DEAD GAME: no remaining card can complete any slot, so playing on cannot gain a point\n"
   "    // and can only bust away the 1000-point all-lives bonus. Forfeit instead.\n"
   "    const availDeck = { ...st.deck }; availDeck[card]++;   // the card in hand is playable too\n"
   "    if (E.noMorePointsPossible(st.slots, availDeck, st.passes)) {\n"
   "      stats.cashedOut = true; stats.forfeited = true; break;\n"
   "    }\n\n"
   "    if (!anySafe && st.passes === 0) {\n"
   "      const fb = forcedBust(E, st, card);\n"
   "      if (fb.end) { stats.cashedOut = true; break; }\n"
   "      resolvePlace(st, fb.bustSlot, card);\n"
   "      stats.busts++;\n"
   "      closeChain();\n"
   "      continue;\n"
   "    }",
   "    if (!anySafe && st.passes === 0) {\n"
   "      const bustSlot = E.chooseForcedBust(card);\n"
   "      resolvePlace(st, bustSlot, card);\n"
   "      stats.busts++; stats.forcedBusts++;\n"
   "      closeChain();\n"
   "      continue;\n"
   "    }"),
  ("    if (evt === 'bust') stats.busts++;", "    if (evt === 'bust') { stats.busts++; }"),
  ("    if (isClear) { stats.clears++; curChain++; stats.chainBonus += E.streakBonus(st.streak); }\n"
   "    else closeChain();",
   "    if (isClear) { stats.clears++; curChain++; stats.chainBonus += E.streakBonus(st.streak); }\n"
   "    else if (evt === 'pass' || evt === 'bust') closeChain();   // only a stay or a bust ends a streak here"),
  ("  const final = st.score + (st.lives >= 3 ? PTS_PERFECT : 0);",
   "  const final = st.score + (st.lives >= 3 ? E.perfect() : 0);"),
  ("module.exports = { playGame, mulberry32, shuffledDeck, forcedBust };",
   "module.exports = { playGame, mulberry32, shuffledDeck };"),
]
io.open('bench/game.js', 'w', encoding='utf-8', newline='\n').write(s)
patch('bench/game.js', patch_pairs)

# ---- bench/par.js: extra stat ----
patch('bench/par.js', [
  ("      busts: +avg('busts').toFixed(2), n21:", "      busts: +avg('busts').toFixed(2), forcedBusts: +avg('forcedBusts').toFixed(2), n21:"),
])
print('bench patched OK')
