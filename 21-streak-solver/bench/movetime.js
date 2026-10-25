// Time chooseBest on recorded oracle states (one core): node bench/movetime.js <build> <states.json> [n]
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32 } = require('./game');
const E = loadEngine(path.resolve(__dirname, '..', process.argv[2]));
const rows = require(path.resolve(__dirname, '..', process.argv[3])).slice(0, parseInt(process.argv[4] || '10', 10));
E.setMode('balanced'); E.setTarget(0);
const ms = [];
rows.forEach((r, i) => {
  Math.random = mulberry32(777 + i);
  E.setState({ slots: r.st.slots.map(x => [...x]), deck: { ...r.st.deck }, lives: r.st.lives, passes: r.st.passes, score: r.st.score, streak: r.st.streak });
  const t = Date.now(); E.chooseBest(r.card); ms.push(Date.now() - t);
});
ms.sort((a, b) => a - b);
console.log(process.argv[2], 'n', ms.length, 'median', ms[ms.length >> 1], 'max', ms[ms.length - 1], 'mean', Math.round(ms.reduce((a, b) => a + b, 0) / ms.length));
