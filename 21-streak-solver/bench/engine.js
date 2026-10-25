// Loads the solver engine straight out of an index.html build, so the benchmark
// always measures the REAL shipped code rather than a drifting copy.
const fs = require('fs');

const START = 'const RANKS =';
const END = 'function snapshot(){';

function loadEngine(htmlPath) {
  const html = fs.readFileSync(htmlPath, 'utf8');
  const a = html.indexOf(START);
  const b = html.indexOf(END);
  if (a < 0 || b < 0 || b <= a) throw new Error('engine markers not found in ' + htmlPath);
  const src = html.slice(a, b);

  const accessors = `
    return {
      RANKS, VAL, EXACT_LIMIT,
      perfect: () => PTS_PERFECT,
      chooseForcedBust,
      setBustRule: (v) => { RULE_BUST_BREAKS_STREAK = !!v; },
      setPerfect: (v) => { PTS_PERFECT = v ? 1000 : 0; },
      handTotal, freshDeck, resolvePlace, resolvePass, stateValue,
      genSequences, rolloutSeqReal, exactChance, chooseBest, streakBonus, greedyChoice,
      exactInit: (ms) => { if (typeof memoInit === 'function') memoInit(); else exactMemo = new Map(); exactNodes = 0; exactDeadline = Date.now() + ms; },
      exactBudgetFor,
      // emulate a slower device: every exact wall-clock budget times f (f < 1 = slower device)
      scaleBudgets: (f) => { const orig = exactBudgetFor; exactBudgetFor = (rem) => orig(rem) * f; },
      exactNodesUsed: () => exactNodes,
      nodeCapDeep: () => EXACT_NODE_CAP_DEEP,
      fbMargin: () => (typeof FB_MARGIN !== 'undefined' ? FB_MARGIN : 250),
      noMorePointsPossible: (sl, dk, ps) => (typeof noMorePointsPossible === 'function' ? noMorePointsPossible(sl, dk, ps) : false),
      collisions: () => (typeof COLL==='undefined'?-1:COLL),
      collEx: () => (typeof COLLEX==='undefined'?null:COLLEX),
      setWinTarget: (t) => { WIN_TARGET = t; },
      setState(s){ slots=s.slots; deck=s.deck; lives=s.lives; passes=s.passes; score=s.score; streak=s.streak; },
      getState(){ return {slots, deck, lives, passes, score, streak}; },
      setMode(m){ MODE = m; },
      setTarget(t){ TARGET = t; }
    };
  `;
  // eslint-disable-next-line no-new-func
  return new Function(src + accessors)();
}

module.exports = { loadEngine };
