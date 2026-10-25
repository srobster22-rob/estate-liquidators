// Two builds must give the SAME exact values (a pure speed change):
//   node bench/exactsame.js <a> <b> <states.json> [n] [drop]
// `drop` removes that many cards from each recorded deck first (a smaller, still-legal endgame),
// because full 10-card solves take minutes each.
const fs = require('fs'), path = require('path');
const { loadEngine } = require('./engine');
const unbound = f => { let s = fs.readFileSync(path.resolve(__dirname, '..', f), 'utf8')
  .replace(/const EXACT_NODE_CAP_DEEP = \d+;/, 'const EXACT_NODE_CAP_DEEP = 4e9;')
  .replace(/function exactBudgetFor\(rem\)\{[^\n]*\}/, 'function exactBudgetFor(rem){ return 1e12; }')
  .replace(/const PASS_FULL_LIMIT = \d+;/, 'const PASS_FULL_LIMIT = 0;');
  const t = path.join(__dirname, `_same_${process.pid}_${path.basename(f)}`); fs.writeFileSync(t, s); const E = loadEngine(t); fs.unlinkSync(t); return E; };
const [, , fa, fb, sf, nArg, dropArg] = process.argv;
const DROP = parseInt(dropArg || '0', 10);
const A = unbound(fa), B = unbound(fb);
const rows = JSON.parse(fs.readFileSync(path.resolve(__dirname, '..', sf), 'utf8')).filter(r => r.st.passes === 0).slice(0, parseInt(nArg || '10', 10));
let worst = 0, n = 0, na = 0, nb = 0, ta = 0, tb = 0;
for (const r of rows) for (let i = 0; i < 4; i++) {
  const mk = () => { const st = { slots: r.st.slots.map(x => [...x]), deck: { ...r.st.deck }, lives: r.st.lives, passes: r.st.passes, score: r.st.score, streak: r.st.streak };
    for (let d = 0, k = (r.seed * 7) % 13; d < DROP; k = (k + 5) % 13) { const rk = A.RANKS[k]; if (st.deck[rk] > 0) { st.deck[rk]--; d++; } }
    A.resolvePlace(st, i, r.card); return st; };
  const sa = mk(), sb = mk();
  if (sa.lives <= 0) continue;
  A.exactInit(1e12); let t = Date.now(); const va = A.exactChance(sa); ta += Date.now() - t; na += A.exactNodesUsed();
  B.exactInit(1e12); t = Date.now(); const vb = B.exactChance(sb); tb += Date.now() - t; nb += B.exactNodesUsed();
  worst = Math.max(worst, Math.abs(va - vb)); n++;
}
console.log(`${n} exact values compared: max |a-b| = ${worst.toExponential(2)} | nodes ${na} vs ${nb} (${(na / Math.max(1, nb)).toFixed(2)}x) | ms ${ta} vs ${tb}`);
process.exit(worst < 1e-6 ? 0 : 1);
