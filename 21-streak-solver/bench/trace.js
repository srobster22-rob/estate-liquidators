// Trace one self-play game move by move (sanity check of the rules as played).
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');
const E = loadEngine(path.resolve(__dirname, '..', process.argv[2] || 'index.html'));
const seed = parseInt(process.argv[3] || '1', 10);
Math.random = mulberry32(seed ^ 0x9e3779b9);
const order = shuffledDeck(mulberry32(seed), E.RANKS);
const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
E.setMode('balanced'); E.setTarget(0);
for (let n = 0; n < order.length && st.lives > 0; n++) {
  const card = order[n]; st.deck[card]--; E.setState(st);
  let anySafe = false;
  for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) { anySafe = true; break; }
  let act, evt;
  if (!anySafe && st.passes === 0) { act = { type: 'FORCED', slot: E.chooseForcedBust(card) }; evt = E.resolvePlace(st, act.slot, card); }
  else { act = E.chooseBest(card); evt = act.type === 'pass' ? E.resolvePass(st, act.slot, card, act.to) : E.resolvePlace(st, act.slot, card); }
  console.log(String(n + 1).padStart(2), card.padStart(2), act.type.padEnd(6), 'slot', act.slot + 1, (act.type === 'pass' ? 'to ' + (act.to + 1) : '    '), evt.padEnd(7),
    'score', String(st.score).padStart(5), 'streak', st.streak, 'lives', st.lives, 'stays', st.passes,
    '|', st.slots.map(s => s.join(',') || '-').join(' | '));
}
console.log('FINAL', st.score + (st.lives >= 3 ? E.perfect() : 0));
