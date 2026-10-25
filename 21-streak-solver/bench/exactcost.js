// Full cost of the exact endgame decision with every limit removed: node bench/exactcost.js <build> <states.json> <n> [passFullLimit] [memoBits]
const fs = require('fs'), path = require('path');
const { loadEngine } = require('./engine');
const [, , build, statesFile, nArg, pfl, bits] = process.argv;
let s = fs.readFileSync(path.resolve(__dirname, '..', build), 'utf8');
s = s.replace(/const EXACT_NODE_CAP_DEEP = \d+;/, 'const EXACT_NODE_CAP_DEEP = 4e9;')
     .replace(/function exactBudgetFor\(rem\)\{[^\n]*\}/, 'function exactBudgetFor(rem){ return 1e12; }')
     .replace(/var MEMO_BITS = \d+;/, `var MEMO_BITS = ${bits || 23};`);
if (pfl !== undefined) s = s.replace(/const PASS_FULL_LIMIT = \d+;/, `const PASS_FULL_LIMIT = ${pfl};`);
const tmp = path.join(__dirname, `_cost_${process.pid}.html`); fs.writeFileSync(tmp, s);
const E = loadEngine(tmp); fs.unlinkSync(tmp);
E.setMode('balanced'); E.setTarget(0);
const rows = JSON.parse(fs.readFileSync(path.resolve(__dirname, '..', statesFile), 'utf8')).slice(0, parseInt(nArg || '20', 10));
const res = [];
for (const r of rows) {
  E.setState({ slots: r.st.slots.map(x => [...x]), deck: { ...r.st.deck }, lives: r.st.lives, passes: r.st.passes, score: r.st.score, streak: r.st.streak });
  const t = Date.now(); E.chooseBest(r.card); res.push({ nodes: E.exactNodesUsed(), ms: Date.now() - t, passes: r.st.passes });
}
const q = (v, p) => { const a = [...v].sort((x, y) => x - y); return a[Math.min(a.length - 1, Math.floor(p * a.length))]; };
const N = res.map(r => r.nodes), M = res.map(r => r.ms);
console.log(`${build} PFL=${pfl ?? 'as built'}: nodes p50 ${q(N, .5)} p90 ${q(N, .9)} max ${Math.max(...N)} | ms p50 ${q(M, .5)} p90 ${q(M, .9)} max ${Math.max(...M)} | >800k: ${N.filter(x => x > 800000).length}/${N.length}`);
console.log('  by stays left:', [0, 1, 2].map(p => { const v = res.filter(r => r.passes === p).map(r => r.nodes); return v.length ? `${p}: n${v.length} p50 ${q(v, .5)} max ${Math.max(...v)}` : `${p}: -`; }).join(' | '));
