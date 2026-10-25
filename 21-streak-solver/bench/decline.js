// How often does a build DECLINE an available completion (21 / 5-card) in reachable midgame
// states? Reachable states come from random self-play, as in fuzz.js.
const path = require('path');
const { loadEngine } = require('./engine');
const { mulberry32 } = require('./game');
const files = process.argv.slice(2);
const states = [];
{
  const E = loadEngine(path.resolve(__dirname, '..', files[0]));
  const RANKS = E.RANKS;
  for (let g = 0; g < 80; g++) {
    const rng = mulberry32(70000 + g);
    const cards = []; for (const r of RANKS) for (let i = 0; i < 4; i++) cards.push(r);
    for (let i = cards.length - 1; i > 0; i--) { const j = (rng() * (i + 1)) | 0; const t = cards[i]; cards[i] = cards[j]; cards[j] = t; }
    const st = { slots: [[], [], [], []], deck: E.freshDeck(), lives: 3, passes: 2, score: 0, streak: 0 };
    for (const c of cards) {
      if (st.lives <= 0) break;
      st.deck[c]--;
      let rem = 0; for (const r of RANKS) rem += st.deck[r];
      const comp = [];
      for (let i = 0; i < 4; i++) { const t = E.handTotal([...st.slots[i], c]); if (t.min <= 21 && (t.best === 21 || st.slots[i].length + 1 >= 5)) comp.push(i); }
      if (comp.length && rem > 10) states.push({ slots: st.slots.map(x => [...x]), deck: { ...st.deck }, lives: st.lives, passes: st.passes, score: st.score, streak: (rng() * 6) | 0, card: c, comp });
      const safe = []; for (let i = 0; i < 4; i++) if (E.handTotal([...st.slots[i], c]).min <= 21) safe.push(i);
      if (!safe.length) { if (st.passes > 0) { E.resolvePass(st, 0, c); continue; } E.resolvePlace(st, 0, c); continue; }
      E.resolvePlace(st, safe[(rng() * safe.length) | 0], c);
    }
  }
}
const sample = states.filter((_, i) => i % 3 === 0);
for (const f of files) {
  const E = loadEngine(path.resolve(__dirname, '..', f));
  E.setMode('balanced'); E.setTarget(0);
  let declined = 0, ex = [];
  Math.random = mulberry32(99);
  for (const s of sample) {
    E.setState({ slots: s.slots.map(x => [...x]), deck: { ...s.deck }, lives: s.lives, passes: s.passes, score: s.score, streak: s.streak });
    const a = E.chooseBest(s.card);
    if (!(a.type === 'place' && s.comp.includes(a.slot))) { declined++; if (ex.length < 4) ex.push({ card: s.card, slots: s.slots.map(x => x.join('')).join('|'), comp: s.comp, act: a.type + (a.slot + 1) }); }
  }
  console.log(f, 'states', sample.length, 'declined completions', declined, JSON.stringify(ex));
}
