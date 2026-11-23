// DECISION-CLASS AUDIT. For each seed, replay the base build's self-play to its first voluntary
// MC stay at streak x3+ (safe placement open, >10 cards left), ask every candidate build what IT
// would play there, and grade the union of those moves (plus every placement) with K paired
// full-solver playouts of the rest of the game (the base build plays the rest). One JSON line per
// seed is appended to <out> as soon as it is done, so a killed run loses nothing.
//   node bench/qaudit.js <out.jsonl> <K> <workers> <base.html> <cand.html,...> <seed> [seed...]
//   node bench/qaudit.js --sum <out.jsonl>
const fs = require('fs');
const path = require('path');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');
const ROOT = path.resolve(__dirname, '..');
const clone = s => ({ slots: s.slots.map(x => [...x]), deck: { ...s.deck }, lives: s.lives, passes: s.passes, score: s.score, streak: s.streak });
const key = a => a.type === 'pass' ? `S${a.slot}>${a.to === undefined ? a.slot : a.to}` : `P${a.slot}`;

function playOut(E, st0, k) {
  const st = clone(st0);
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
  for (const k of workerData.ks) out.push(workerData.posts.map(p => playOut(E, p, k)));
  parentPort.postMessage(out);
} else if (process.argv[2] === '--sum') {
  const rows = fs.readFileSync(process.argv[3], 'utf8').split('\n').filter(Boolean).map(JSON.parse);
  const builds = Object.keys(rows[0].picks);
  for (const b of builds) {
    const d = rows.map(r => r.value[r.picks[b]] - r.value[r.picks[builds[0]]]);
    const n = d.length, m = d.reduce((x, y) => x + y, 0) / n;
    const se = Math.sqrt(rows.reduce((x, r) => x + r.se2[r.picks[b]], 0)) / n;   // playout noise only
    const changed = rows.filter(r => r.picks[b] !== r.picks[builds[0]]).length;
    console.log(`${b.padEnd(26)} vs ${builds[0]}: ${m >= 0 ? '+' : ''}${m.toFixed(0)} ± ${se.toFixed(0)} per audited decision; changes ${changed}/${n}`);
  }
} else {
  const [out, Karg, nwArg, baseArg, candArg, ...seeds] = process.argv.slice(2);
  const K = parseInt(Karg, 10), nw = parseInt(nwArg, 10);
  const base = path.join(ROOT, baseArg);
  const builds = [baseArg, ...candArg.split(',').filter(Boolean)];
  const Es = builds.map(b => { const E = loadEngine(path.join(ROOT, b)); E.setMode('balanced'); E.setTarget(0); return E; });
  const E = Es[0];
  (async () => {
    for (const seedStr of seeds) {
      const seed = parseInt(seedStr, 10);
      Math.random = mulberry32(seed ^ 0x9e3779b9);
      const order = shuffledDeck(mulberry32(seed), E.RANKS);
      const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
      let found = null;
      for (let n = 0; n < order.length && st.lives > 0 && 51 - n > 10; n++) {
        const card = order[n]; st.deck[card]--; E.setState(st);
        let safe = 0; for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) safe++;
        if (!safe && st.passes === 0) { E.resolvePlace(st, E.chooseForcedBust(card), card); continue; }
        const snap = clone(st);
        const a = E.chooseBest(card);
        if (a.type === 'pass' && st.streak >= 3 && safe > 0) { found = { snap, card, rem: 51 - n }; break; }
        a.type === 'pass' ? E.resolvePass(st, a.slot, card, a.to) : E.resolvePlace(st, a.slot, card);
      }
      if (!found) { console.log('seed', seed, ': no audited stay'); continue; }
      const { snap, card } = found;
      const picks = {};
      const acts = new Map();
      builds.forEach((b, i) => {
        Math.random = mulberry32(777 + seed); Es[i].setState(clone(snap));
        const a = Es[i].chooseBest(card); picks[b] = key(a); acts.set(key(a), a);
      });
      for (let i = 0; i < 4; i++) { const a = { type: 'place', slot: i }; if (!acts.has(key(a))) acts.set(key(a), a); }
      const list = [...acts.values()];
      const posts = list.map(a => { const p = clone(snap); a.type === 'pass' ? E.resolvePass(p, a.slot, card, a.to) : E.resolvePlace(p, a.slot, card); return p; });
      const chunks = Array.from({ length: nw }, () => []); for (let k = 0; k < K; k++) chunks[k % nw].push(k);
      const all = await Promise.all(chunks.filter(c => c.length).map(ks => new Promise((res, rej) => {
        const w = new Worker(__filename, { workerData: { build: base, ks, posts } }); w.on('message', res); w.on('error', rej);
      })));
      const rows = [].concat(...all);
      // value of each action = mean final; se2 = variance of its difference to the base pick / K
      const bi = list.findIndex(a => key(a) === picks[builds[0]]);
      const value = {}, se2 = {};
      list.forEach((a, i) => {
        const v = rows.map(r => r[i]); const d = rows.map(r => r[i] - r[bi]);
        value[key(a)] = v.reduce((x, y) => x + y, 0) / v.length;
        const m = d.reduce((x, y) => x + y, 0) / d.length;
        se2[key(a)] = d.reduce((x, y) => x + (y - m) ** 2, 0) / Math.max(1, d.length - 1) / d.length;
      });
      const rec = { seed, rem: found.rem, streak: snap.streak, stays: snap.passes, card, board: snap.slots.map(s => s.join(',') || '-').join(' | '), picks, value, se2 };
      fs.appendFileSync(path.join(ROOT, out), JSON.stringify(rec) + '\n');
      console.log(`seed ${seed} x${snap.streak} rem ${found.rem} card ${card} | ${rec.board} | ` + builds.map(b => `${path.basename(b)}=${picks[b]}:${(value[picks[b]] - value[picks[builds[0]]]).toFixed(0)}`).join(' '));
    }
  })();
}
