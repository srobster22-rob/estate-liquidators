// SINK SCAN. Most high-streak resets come from boards where all four slots sit at 12+ when a
// ten-card arrives. Self-play and log every MC move (more than 10 cards left) whose chosen
// placement leaves NO sink (every slot non-empty at 12+, so a ten busts everything) while some
// other safe placement would have kept one. Prints the rate and the states, for bench/qeval.js.
//   node bench/sinks.js <build> [games] [seed0]
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');
const E = loadEngine(path.resolve(__dirname, '..', process.argv[2] || 'index.html'));
const N = parseInt(process.argv[3] || '20', 10), seed0 = parseInt(process.argv[4] || '1000', 10);
const noSink = slots => slots.every(s => s.length && E.handTotal(s).min >= 12);
let moves = 0, hits = 0, tenNext = 0;
for (let g = 0; g < N; g++) {
  const seed = seed0 + g;
  Math.random = mulberry32(seed ^ 0x9e3779b9);
  const order = shuffledDeck(mulberry32(seed), E.RANKS);
  const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
  E.setMode('balanced'); E.setTarget(0);
  for (let n = 0; n < order.length && st.lives > 0; n++) {
    const card = order[n]; st.deck[card]--; E.setState(st);
    let anySafe = false;
    for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) { anySafe = true; break; }
    if (!anySafe && st.passes === 0) { E.resolvePlace(st, E.chooseForcedBust(card), card); continue; }
    const before = st.slots.map(s => [...s]);
    const a = E.chooseBest(card);
    const rem = 51 - n;
    a.type === 'pass' ? E.resolvePass(st, a.slot, card, a.to) : E.resolvePlace(st, a.slot, card);
    if (rem <= 10 || a.type === 'pass') continue;
    moves++;
    if (!noSink(st.slots)) continue;
    // could another safe, non-clearing-or-clearing placement have kept a sink?
    const alt = [];
    for (let i = 0; i < 4; i++) {
      if (i === a.slot || E.handTotal([...before[i], card]).min > 21) continue;
      const t = before.map(s => [...s]); t[i].push(card);
      const h = E.handTotal(t[i]); if (h.best === 21 || t[i].length >= 5) t[i] = [];
      if (!noSink(t)) alt.push(i + 1);
    }
    if (!alt.length) continue;
    hits++;
    const next = order[n + 1]; if (next && ['10', 'J', 'Q', 'K'].includes(next)) tenNext++;
    console.log(JSON.stringify({ seed, rem, streak: st.streak, stays: st.passes, card, chose: a.slot + 1, alt, board: before.map(s => s.join(',') || '-').join(' | ') }));
  }
}
console.log(`# ${hits} sink-losing moves in ${moves} MC placements (${(hits / N).toFixed(2)}/game); next card was a ten ${tenNext}/${hits}`);
