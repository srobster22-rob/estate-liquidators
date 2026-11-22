// Where do busts come from? Self-play N games and log every bust: cards left, streak lost,
// forced (card busts every slot, no stays) or chosen, and the board just before.
//   node bench/busts.js <build> [games] [seed0]
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');
const E = loadEngine(path.resolve(__dirname, '..', process.argv[2] || 'index.html'));
const N = parseInt(process.argv[3] || '20', 10), seed0 = parseInt(process.argv[4] || '1000', 10);
const ev = [];
for (let g = 0; g < N; g++) {
  const seed = seed0 + g;
  Math.random = mulberry32(seed ^ 0x9e3779b9);
  const order = shuffledDeck(mulberry32(seed), E.RANKS);
  const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
  E.setMode('balanced'); E.setTarget(0);
  for (let n = 0; n < order.length && st.lives > 0; n++) {
    const card = order[n]; st.deck[card]--; E.setState(st);
    const before = { board: st.slots.map(s => s.join(',') || '-').join(' | '), streak: st.streak, passes: st.passes, rem: 51 - n };
    let anySafe = false;
    for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) { anySafe = true; break; }
    let evt, kind;
    if (!anySafe && st.passes === 0) { evt = E.resolvePlace(st, E.chooseForcedBust(card), card); kind = 'forced'; }
    else {
      const a = E.chooseBest(card);
      evt = a.type === 'pass' ? E.resolvePass(st, a.slot, card, a.to) : E.resolvePlace(st, a.slot, card);
      kind = a.type === 'pass' ? 'stay' : 'chosen';
    }
    if (evt.endsWith('bust') || kind === 'stay') ev.push({ seed, kind: evt.endsWith('bust') ? (kind === 'forced' ? 'forced bust' : 'chosen bust') : 'stay', card, ...before });
  }
}
for (const e of ev) console.log(JSON.stringify(e));
const by = {}; for (const e of ev) { const k = e.kind; (by[k] = by[k] || []).push(e); }
for (const k of Object.keys(by)) {
  const v = by[k];
  console.log(`# ${k}: ${(v.length / N).toFixed(2)}/game | streak lost: mean ${(v.reduce((a, e) => a + e.streak, 0) / v.length).toFixed(1)}, at x3+ ${v.filter(e => e.streak >= 3).length}/${v.length} | cards left: mean ${(v.reduce((a, e) => a + e.rem, 0) / v.length).toFixed(1)}`);
}
