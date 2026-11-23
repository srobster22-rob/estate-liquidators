// Seeds whose self-play makes a voluntary MC stay at streak x3+ (safe placement open, >10 cards
// left) — the cases bench/qeval.js audits. node bench/findstays.js <build> <seed0> <n>
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');
const E = loadEngine(path.resolve(__dirname, '..', process.argv[2]));
const s0 = parseInt(process.argv[3], 10), N = parseInt(process.argv[4], 10);
for (let seed = s0; seed < s0 + N; seed++) {
  Math.random = mulberry32(seed ^ 0x9e3779b9);
  const order = shuffledDeck(mulberry32(seed), E.RANKS);
  const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
  E.setMode('balanced'); E.setTarget(0);
  for (let n = 0; n < order.length && st.lives > 0 && 51 - n > 10; n++) {
    const card = order[n]; st.deck[card]--; E.setState(st);
    let safe = 0; for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) safe++;
    if (!safe && st.passes === 0) { E.resolvePlace(st, E.chooseForcedBust(card), card); continue; }
    const a = E.chooseBest(card);
    if (a.type === 'pass' && st.streak >= 3 && safe > 0) { console.log(seed); break; }
    a.type === 'pass' ? E.resolvePass(st, a.slot, card, a.to) : E.resolvePlace(st, a.slot, card);
  }
}
