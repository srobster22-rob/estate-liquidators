// Per-move solver latency over N self-play games (node is ~3-5x faster than a phone).
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');
const file = process.argv[2] || 'index.html';
const N = parseInt(process.argv[3] || '3', 10);
const E = loadEngine(path.resolve(__dirname, '..', file));
const ms = [], byRem = {};
for (let g = 0; g < N; g++) {
  const seed = 500 + g;
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
    if (!anySafe && st.passes === 0) E.resolvePlace(st, E.chooseForcedBust(card), card);
    else { const a = E.chooseBest(card); a.type === 'pass' ? E.resolvePass(st, a.slot, card) : E.resolvePlace(st, a.slot, card); }
    const dt = Date.now() - t0; ms.push(dt);
    const k = rem > 10 ? 'mid' : String(rem); (byRem[k] = byRem[k] || []).push(dt);
  }
}
ms.sort((a, b) => a - b);
const q = p => ms[Math.min(ms.length - 1, Math.floor(p * ms.length))];
console.log(file, 'moves', ms.length, 'median', q(0.5), 'p90', q(0.9), 'p99', q(0.99), 'max', ms[ms.length - 1], 'total/game', Math.round(ms.reduce((a, b) => a + b, 0) / N));
for (const k of Object.keys(byRem).sort((a, b) => (a === 'mid' ? 99 : +a) - (b === 'mid' ? 99 : +b))) {
  const v = byRem[k]; console.log('  rem', k.padStart(3), 'n', v.length, 'mean', Math.round(v.reduce((a, b) => a + b, 0) / v.length), 'max', Math.max(...v));
}
