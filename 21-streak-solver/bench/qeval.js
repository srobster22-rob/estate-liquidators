// POLICY EVALUATION of one decision. For a recorded state + dealt card, apply each candidate
// action, then play the REST of the game with the full solver (MC + exact endgame) over K
// shuffles of the remaining deck — the same K shuffles for every action, so the comparison is
// paired. Answers "was that move a mistake for THIS solver?" without the greedy-rollout bias
// the solver's own MC estimate carries.
//   node bench/qeval.js <build> <seed> [K] [workers]
// <seed>: a game seed from bench/busts.js output; the state is re-created by self-play up to the
// logged move, using the same seeds bench/busts.js and par.js use.
const path = require('path');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');
const ROOT = path.resolve(__dirname, '..');

function playOut(E, st0, k) {
  const st = { slots: st0.slots.map(x => [...x]), deck: { ...st0.deck }, lives: st0.lives, passes: st0.passes, score: st0.score, streak: st0.streak };
  const rng = mulberry32(424242 + k);
  const cards = []; for (const r of E.RANKS) for (let i = 0; i < st.deck[r]; i++) cards.push(r);
  for (let i = cards.length - 1; i > 0; i--) { const j = (rng() * (i + 1)) | 0; const t = cards[i]; cards[i] = cards[j]; cards[j] = t; }
  Math.random = mulberry32(9000 + k);
  for (const card of cards) {
    if (st.lives <= 0) break;
    st.deck[card]--; E.setState(st);
    let anySafe = false;
    for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) { anySafe = true; break; }
    if (!anySafe && st.passes === 0) { E.resolvePlace(st, E.chooseForcedBust(card), card); continue; }
    const a = E.chooseBest(card);
    a.type === 'pass' ? E.resolvePass(st, a.slot, card, a.to) : E.resolvePlace(st, a.slot, card);
  }
  return st.score;
}

if (!isMainThread) {
  const E = loadEngine(workerData.build); E.setMode('balanced'); E.setTarget(0);
  const out = [];
  for (const k of workerData.ks) out.push({ k, v: workerData.posts.map(p => playOut(E, p, k)) });
  parentPort.postMessage(out);
} else {
  const build = path.join(ROOT, process.argv[2] || 'index.html');
  const seed = parseInt(process.argv[3], 10), K = parseInt(process.argv[4] || '40', 10), nw = parseInt(process.argv[5] || '4', 10);
  const E = loadEngine(build); E.setMode('balanced'); E.setTarget(0);
  // replay the game to its first voluntary stay at streak >= 3 (the case bench/busts.js flagged)
  Math.random = mulberry32(seed ^ 0x9e3779b9);
  const order = shuffledDeck(mulberry32(seed), E.RANKS);
  const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
  let found = null;
  for (let n = 0; n < order.length && st.lives > 0; n++) {
    const card = order[n]; st.deck[card]--; E.setState(st);
    let safe = 0; for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) safe++;
    if (!safe && st.passes === 0) { E.resolvePlace(st, E.chooseForcedBust(card), card); continue; }
    const snap = { slots: st.slots.map(x => [...x]), deck: { ...st.deck }, lives: st.lives, passes: st.passes, score: st.score, streak: st.streak };
    const a = E.chooseBest(card);
    if (a.type === 'pass' && st.streak >= 3 && safe > 0 && 51 - n > 10) { found = { snap, card, chosen: a, rem: 51 - n }; break; }
    a.type === 'pass' ? E.resolvePass(st, a.slot, card, a.to) : E.resolvePlace(st, a.slot, card);
  }
  if (!found) { console.log('no voluntary high-streak MC stay in seed', seed); process.exit(0); }
  const { snap, card, chosen } = found;
  // candidates: the chosen stay, and every placement that does not bust
  // the rule under test ("no voluntary stay at x3+") would play the MC's best NON-stay move:
  E.setState({ slots: snap.slots.map(x => [...x]), deck: { ...snap.deck }, lives: snap.lives, passes: 0, score: snap.score, streak: snap.streak });
  const rulePick = E.chooseBest(card).slot;
  const acts = [{ type: 'pass', slot: chosen.slot, to: chosen.to }];
  for (let i = 0; i < 4; i++) if (E.handTotal([...snap.slots[i], card]).min <= 21) acts.push({ type: 'place', slot: i });
  const posts = acts.map(a => { const p = { slots: snap.slots.map(x => [...x]), deck: { ...snap.deck }, lives: snap.lives, passes: snap.passes, score: snap.score, streak: snap.streak };
    a.type === 'pass' ? E.resolvePass(p, a.slot, card, a.to) : E.resolvePlace(p, a.slot, card); return p; });
  console.log(`seed ${seed}: rem ${found.rem}, x${snap.streak}, stays ${snap.passes}, card ${card} | ${snap.slots.map(s => s.join(',') || '-').join(' | ')}`);
  const chunks = Array.from({ length: nw }, () => []); for (let k = 0; k < K; k++) chunks[k % nw].push(k);
  Promise.all(chunks.filter(c => c.length).map(ks => new Promise((res, rej) => {
    const w = new Worker(__filename, { workerData: { build, ks, posts } }); w.on('message', res); w.on('error', rej);
  }))).then(all => {
    const rows = [].concat(...all);
    const base = rows.map(r => r.v[0]);
    acts.forEach((a, i) => {
      const d = rows.map(r => r.v[i] - r.v[0]); const m = d.reduce((x, y) => x + y, 0) / d.length;
      const sd = Math.sqrt(d.reduce((x, y) => x + (y - m) ** 2, 0) / Math.max(1, d.length - 1));
      const mean = rows.reduce((x, r) => x + r.v[i], 0) / rows.length;
      const name = a.type === 'pass' ? `STAY ${a.slot + 1}->${a.to + 1} (chosen)` : `place ${a.slot + 1}${a.slot === rulePick ? ' (rule)' : ''}`;
      if (a.type === 'place' && a.slot === rulePick) console.log(`RULE ${seed} ${m.toFixed(1)} ${(sd / Math.sqrt(d.length)).toFixed(1)}`);
      console.log(`  ${name.padEnd(20)} mean final ${mean.toFixed(0)}  vs chosen ${i ? (m >= 0 ? '+' : '') + m.toFixed(0) + ' ± ' + (sd / Math.sqrt(d.length)).toFixed(0) : '—'}`);
    });
  });
}
