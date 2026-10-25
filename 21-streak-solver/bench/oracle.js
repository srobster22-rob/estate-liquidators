// DECISION-LEVEL ORACLE. Game-level A/Bs here have a paired stderr of ~130-190 per 240 games,
// because one diverging decision changes every later clear. This measures decisions instead:
// at a few cards above the exact limit the Monte-Carlo search is still deciding, but an
// unbounded exact solve can value every legal action, so each build's choice gets an exact
// regret (optimal EV - EV of the chosen action) with no game-level noise.
//
//   node bench/oracle.js gen   --rem=11 --n=200 --seed0=20000 --out=bench/st11.json [--build=index.html]
//   node bench/oracle.js label --in=bench/st11.json --out=bench/st11L.json [--workers=4]
//   node bench/oracle.js eval  --in=bench/st11L.json --builds=index.html,bench/cand_r.html
//
// gen   : self-play the build and record (state, dealt card) when `rem` cards remain undealt.
// label : exact value of every legal action (unbounded memo, no deadline). Stays are searched as
//         the shipped endgame does (freely in the last PASS_FULL_LIMIT=8 cards, else only when
//         every placement busts): allowing them at every depth made an 11-card solve take >30 min.
// eval  : each build's chooseBest() on every labelled state, Math.random seeded per state so the
//         builds are paired; prints mean regret, how often each is optimal, and the paired diff.
const fs = require('fs');
const path = require('path');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const { loadEngine } = require('./engine');
const { mulberry32, shuffledDeck } = require('./game');

const ROOT = path.resolve(__dirname, '..');
const ORACLE_HTML = path.join(__dirname, 'oracle_build.html');

function makeOracleBuild() {
  // Same rules and engine as the shipped build, with every search limit removed.
  let s = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const reps = [
    [/var MEMO_BITS = \d+;/, 'var MEMO_BITS = 25;'],
    [/const EXACT_NODE_CAP_DEEP = \d+;/, 'const EXACT_NODE_CAP_DEEP = 4e9;'],
    [/function exactBudgetFor\(rem\)\{[^\n]*\}/, 'function exactBudgetFor(rem){ return 1e12; }'],
  ];
  for (const [re, to] of reps) { if (!re.test(s)) throw new Error('oracle patch failed: ' + re); s = s.replace(re, to); }
  fs.writeFileSync(ORACLE_HTML, s);
}

function legalActions(E, st, card) {
  const acts = [];
  for (let i = 0; i < 4; i++) acts.push({ type: 'place', slot: i });
  if (st.passes > 0) for (let i = 0; i < 4; i++) {
    if (!st.slots[i].length) continue;
    for (let j = 0; j < 4; j++) {
      if (j !== i && E.handTotal([...st.slots[j], card]).min > 21) continue;
      acts.push({ type: 'pass', slot: i, to: j });
    }
  }
  return acts;
}
const clone = st => ({ slots: st.slots.map(x => [...x]), deck: { ...st.deck }, lives: st.lives, passes: st.passes, score: st.score, streak: st.streak });
const actKey = a => a.type === 'pass' ? `S${a.slot}>${a.to === undefined ? a.slot : a.to}` : `P${a.slot}`;

function args() {
  return Object.fromEntries(process.argv.slice(3).filter(a => a.startsWith('--'))
    .map(a => { const i = a.indexOf('='); return i < 0 ? [a.slice(2), true] : [a.slice(2, i), a.slice(i + 1)]; }));
}

if (!isMainThread) {
  // label worker
  const O = loadEngine(ORACLE_HTML);
  const out = [];
  for (const s of workerData.states) {
    const t0 = Date.now();
    const acts = legalActions(O, s.st, s.card).map(a => {
      const post = clone(s.st);
      if (a.type === 'pass') O.resolvePass(post, a.slot, s.card, a.to); else O.resolvePlace(post, a.slot, s.card);
      O.exactInit(1e12);
      const v = post.lives <= 0 ? post.score : O.exactChance(post);
      return { key: actKey(a), v };
    });
    out.push({ ...s, acts, ms: Date.now() - t0, nodes: O.exactNodesUsed() });
  }
  parentPort.postMessage(out);
} else {
  const mode = process.argv[2];
  const A = args();
  if (mode === 'gen') {
    const rem = parseInt(A.rem || '11', 10), n = parseInt(A.n || '200', 10), seed0 = parseInt(A.seed0 || '20000', 10);
    const E = loadEngine(path.join(ROOT, A.build || 'index.html'));
    E.setMode('balanced'); E.setTarget(0);
    const states = [];
    for (let seed = seed0; states.length < n; seed++) {
      Math.random = mulberry32(seed ^ 0x9e3779b9);
      const order = shuffledDeck(mulberry32(seed), E.RANKS);
      const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
      for (let k = 0; k < order.length && st.lives > 0; k++) {
        const card = order[k]; st.deck[card]--;
        const left = 52 - k - 1;
        let anySafe = false;
        for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) { anySafe = true; break; }
        if (left === rem) {
          // a real decision only: not a forced bust, and more than one distinct action
          if (anySafe || st.passes > 0) states.push({ seed, st: clone(st), card });
          break;
        }
        E.setState(st);
        if (!anySafe && st.passes === 0) { E.resolvePlace(st, E.chooseForcedBust(card), card); continue; }
        const a = E.chooseBest(card);
        if (a.type === 'pass') E.resolvePass(st, a.slot, card, a.to); else E.resolvePlace(st, a.slot, card);
      }
    }
    fs.writeFileSync(path.join(ROOT, A.out), JSON.stringify(states));
    console.log('wrote', states.length, 'states at rem', rem, '->', A.out);
  } else if (mode === 'label') {
    makeOracleBuild();
    const states = JSON.parse(fs.readFileSync(path.join(ROOT, A.in), 'utf8'));
    const nw = parseInt(A.workers || '4', 10);
    const chunks = Array.from({ length: nw }, () => []);
    states.forEach((s, i) => chunks[i % nw].push(s));
    const t0 = Date.now();
    Promise.all(chunks.filter(c => c.length).map(c => new Promise((res, rej) => {
      const w = new Worker(__filename, { workerData: { states: c } });
      w.on('message', res); w.on('error', rej);
    }))).then(all => {
      const rows = [].concat(...all).sort((a, b) => a.seed - b.seed);
      fs.writeFileSync(path.join(ROOT, A.out), JSON.stringify(rows));
      const ms = rows.map(r => r.ms).sort((a, b) => a - b);
      console.log('labelled', rows.length, 'states in', ((Date.now() - t0) / 1000).toFixed(0), 's; per state median', ms[ms.length >> 1], 'ms, max', ms[ms.length - 1]);
    });
  } else if (mode === 'eval') {
    const rows = JSON.parse(fs.readFileSync(path.join(ROOT, A.in), 'utf8'));
    const builds = A.builds.split(',');
    const res = {};
    for (const b of builds) {
      const E = loadEngine(path.join(ROOT, b));
      E.setMode('balanced'); E.setTarget(0);
      const reg = [];
      rows.forEach((r, idx) => {
        Math.random = mulberry32(777 + idx);
        E.setState(clone(r.st));
        const a = E.chooseBest(r.card);
        const best = Math.max(...r.acts.map(x => x.v));
        const got = r.acts.find(x => x.key === actKey(a));
        if (!got) throw new Error(`${b}: action ${actKey(a)} not in the oracle's legal set (seed ${r.seed})`);
        reg.push(best - got.v);
      });
      res[b] = reg;
      const mean = reg.reduce((x, y) => x + y, 0) / reg.length;
      console.log(b.padEnd(28), 'mean regret', mean.toFixed(1), '| optimal', (reg.filter(x => x < 1e-6).length / reg.length * 100).toFixed(1) + '%',
        '| regret>100:', reg.filter(x => x > 100).length, '| max', Math.max(...reg).toFixed(0));
    }
    if (builds.length === 2) {
      const [ra, rb] = builds.map(b => res[b]);
      const d = ra.map((x, i) => x - rb[i]);   // positive = B regrets less
      const n = d.length, dm = d.reduce((x, y) => x + y, 0) / n;
      const sd = Math.sqrt(d.reduce((x, y) => x + (y - dm) ** 2, 0) / Math.max(1, n - 1));
      console.log(`paired: B saves ${dm.toFixed(1)} ± ${(sd / Math.sqrt(n)).toFixed(1)} pts/decision (t=${(dm / (sd / Math.sqrt(n) || 1e-9)).toFixed(2)}); differ on ${d.filter(x => Math.abs(x) > 1e-6).length}/${n}`);
    }
  } else {
    console.log('usage: oracle.js gen|label|eval ...');
  }
}
