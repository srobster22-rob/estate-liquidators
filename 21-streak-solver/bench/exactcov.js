// How often does the exact endgame actually finish? exactBest() returns null when it hits the node
// cap or the wall-clock budget, and chooseBest() then silently falls back to Monte-Carlo -- the
// degraded mode that cost F 527 pts/game. Self-play N games and, for every move with <= EXACT_LIMIT
// cards left, record nodes, ms and whether the solve was cut off.
//   node bench/exactcov.js <build> [games] [seed0] [slow]
// `slow` multiplies the wall clock (e.g. 3 = pretend the device is 3x slower than this machine) by
// shrinking every exact budget, to see what a phone would get.
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');
const file = process.argv[2] || 'index.html';
const N = parseInt(process.argv[3] || '10', 10);
const seed0 = parseInt(process.argv[4] || '1000', 10);
const slow = parseFloat(process.argv[5] || '1');
const E = loadEngine(path.resolve(__dirname, '..', file));
if (slow !== 1) E.scaleBudgets(1 / slow);
const by = {};
for (let g = 0; g < N; g++) {
  const seed = seed0 + g;
  Math.random = mulberry32(seed ^ 0x9e3779b9);
  const order = shuffledDeck(mulberry32(seed), E.RANKS);
  const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
  E.setMode('balanced'); E.setTarget(0);
  for (let n = 0; n < order.length && st.lives > 0; n++) {
    const card = order[n]; st.deck[card]--; E.setState(st);
    let rem = 0; for (const r of E.RANKS) rem += st.deck[r];
    let anySafe = false;
    for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) { anySafe = true; break; }
    const t0 = Date.now();
    if (!anySafe && st.passes === 0) { E.resolvePlace(st, E.chooseForcedBust(card), card); continue; }
    const a = E.chooseBest(card);
    const ms = Date.now() - t0;
    if (rem <= E.EXACT_LIMIT && rem >= 7) {
      const nodes = E.exactNodesUsed();
      const cut = nodes > E.nodeCapDeep() ? 'nodecap' : (a.ev === undefined || a.type === undefined ? '?' : null);
      const k = String(rem);
      const b = (by[k] = by[k] || { n: 0, fellBack: 0, nodes: [], ms: [] });
      b.n++; b.nodes.push(nodes); b.ms.push(ms);
      // exactBest's actions carry `evt` but no `pBeat`; the MC path's carry `pBeat`
      if (a.pBeat !== undefined) b.fellBack++;
    }
    a.type === 'pass' ? E.resolvePass(st, a.slot, card, a.to) : E.resolvePlace(st, a.slot, card);
  }
}
const q = (v, p) => { const s = [...v].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; };
for (const k of Object.keys(by).sort((a, b) => b - a)) {
  const b = by[k];
  console.log(`rem ${k.padStart(2)}  moves ${b.n}  fell back to MC ${b.fellBack} (${(100 * b.fellBack / b.n).toFixed(0)}%)  nodes p50 ${q(b.nodes, .5)} p90 ${q(b.nodes, .9)} max ${Math.max(...b.nodes)}  ms p50 ${q(b.ms, .5)} max ${Math.max(...b.ms)}`);
}
