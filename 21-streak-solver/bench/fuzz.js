// Robustness / invariant fuzzer.
// Feeds the solver reachable states AND hand-built extremes, then checks that whatever it
// returns is legal. Also runs every mode and TARGET setting, which the score benchmarks
// never exercise.
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32 } = require('./game');

const FILE = process.argv[2] || 'index.html';
const E = loadEngine(path.resolve(__dirname, '..', FILE));
const RANKS = E.RANKS;
const fails = [];
const record = (kind, detail) => { if (fails.length < 12) fails.push({ kind, detail }); };

function check(st, card, opts) {
  E.setMode(opts.mode); E.setTarget(opts.target);
  E.setState({ slots: st.slots.map(x => [...x]), deck: { ...st.deck },
               lives: st.lives, passes: st.passes, score: st.score, streak: st.streak });
  const t0 = Date.now();
  let act;
  try { act = E.chooseBest(card); }
  catch (e) { record('THREW', { err: e.message, card, st: JSON.stringify(st.slots), ...opts }); return 0; }
  const ms = Date.now() - t0;

  if (!act || (act.type !== 'place' && act.type !== 'pass' && act.type !== 'stop')) { record('BAD ACTION TYPE', { act, card }); return ms; }
  if (act.type === 'stop') return ms;
  if (!(act.slot >= 0 && act.slot < 4)) { record('SLOT OUT OF RANGE', { act, card }); return ms; }
  if (act.type === 'pass') {
    if (st.passes <= 0) record('PASSED WITH NO PASSES LEFT', { act, card, passes: st.passes });
    if (st.slots[act.slot].length === 0) record('PASSED AN EMPTY SLOT', { act, card });
    const to = act.to === undefined ? act.slot : act.to;
    if (!(to >= 0 && to < 4)) record('STAY DESTINATION OUT OF RANGE', { act, card });
    else if (to !== act.slot && E.handTotal([...st.slots[to], card]).min > 21) record('STAY INTO A BUST', { act, card, slots: JSON.stringify(st.slots) });
  } else {
    // HARD RULE 2: never voluntarily bust when something safe exists
    const busts = E.handTotal([...st.slots[act.slot], card]).min > 21;
    let anySafe = false;
    for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], card]).min <= 21) { anySafe = true; break; }
    const canPass = st.passes > 0 && st.slots.some(s => s.length > 0);
    if (busts && (anySafe || canPass)) {
      // intentional in BALANCED/CHASE since HARD RULE 2 was relaxed; still illegal in SAFE
      if (opts.mode === 'safe') record('VOLUNTARY BUST IN SAFE MODE', { act, card, slots: JSON.stringify(st.slots) });
      else global.__volBusts = (global.__volBusts || 0) + 1;
    }
  }
  return ms;
}

// ---- reachable states, via random self-play ----
const states = [];
for (let g = 0; g < 60; g++) {
  const rng = mulberry32(90000 + g);
  const cards = [];
  for (const r of RANKS) for (let i = 0; i < 4; i++) cards.push(r);
  for (let i = cards.length - 1; i > 0; i--) { const j = (rng() * (i + 1)) | 0; const t = cards[i]; cards[i] = cards[j]; cards[j] = t; }
  const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
  for (const c of cards) {
    if (st.lives <= 0) break;
    st.deck[c]--;
    states.push({ slots: st.slots.map(x => [...x]), deck: { ...st.deck },
                  lives: st.lives, passes: st.passes, score: st.score, streak: st.streak, card: c });
    const safe = [];
    for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], c]).min <= 21) safe.push(i);
    if (!safe.length) { if (st.passes > 0) { E.resolvePass(st, 0, c); continue; } E.resolvePlace(st, 0, c); continue; }
    E.resolvePlace(st, safe[(rng() * safe.length) | 0], c);
  }
}

// ---- hand-built extremes ----
const T = (slots, deck, lives, passes, streak, card) => ({ slots, deck, lives, passes, score: 5000, streak, card });
const D = o => { const d = {}; for (const r of RANKS) d[r] = 0; Object.assign(d, o); return d; };
const extremes = [
  T([['K','9'],['K','9'],['K','9'],['K','9']], D({K:1}), 1, 0, 0, 'K'),          // every slot busts, no passes, last life
  T([['K','9'],['K','9'],['K','9'],['K','9']], D({K:1}), 3, 2, 3, 'K'),          // every slot busts, passes available
  T([[],[],[],[]], D({A:4}), 3, 2, 0, 'A'),                                       // empty board, aces only
  T([['A','A','A','A'],[],[],[]], D({'10':4}), 3, 2, 0, '10'),                     // 4 aces in one slot
  T([['10','J','Q'],[],[],[]], D({K:1}), 2, 1, 4, 'K'),                            // slot at 30 min? (illegal-ish) 
  T([['5','5','5','5'],['6','6','6'],['7','7'],['8']], D({'3':1}), 3, 0, 2, '3'),  // 4-card slot, no passes
  T([[],[],[],[]], D({}), 3, 2, 0, 'A'),                                           // empty deck
  T([['9','9','2'],[],[],[]], D({A:1,'2':1}), 1, 0, 0, 'A'),                        // last life, thin deck
];

let maxMs = 0, n = 0;
const MODES = [['balanced',0],['safe',0],['chase',0],['balanced',9000],['balanced',3000]];
for (const [mode, target] of MODES) {
  const sample = states.filter((_, i) => i % 37 === 0);
  for (const s of sample) { maxMs = Math.max(maxMs, check(s, s.card, { mode, target })); n++; }
  for (const s of extremes) {
    let ok = true;
    for (let i = 0; i < 4; i++) if (E.handTotal(s.slots[i]).min > 21) ok = false;  // skip malformed
    if (!ok) continue;
    maxMs = Math.max(maxMs, check(s, s.card, { mode, target })); n++;
  }
}
console.log(JSON.stringify({ file: FILE, checks: n, failures: fails.length, maxMs, voluntaryBusts: global.__volBusts || 0, examples: fails }, null, 2));
process.exit(fails.length ? 1 : 0);
