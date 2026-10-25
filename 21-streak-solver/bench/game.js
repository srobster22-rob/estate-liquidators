// Self-play driver: deals a shuffled 52-card deck to the solver one card at a time
// and returns the real final score. Mirrors dealCard()'s flow in index.html: there is
// no early exit in this game, so a card that busts every slot is always eaten and the
// only decision is which slot to sacrifice (chooseForcedBust, the app's own function).

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffledDeck(rng, RANKS) {
  const cards = [];
  for (const r of RANKS) for (let i = 0; i < 4; i++) cards.push(r);
  for (let i = cards.length - 1; i > 0; i--) {
    const j = (rng() * (i + 1)) | 0;
    const t = cards[i]; cards[i] = cards[j]; cards[j] = t;
  }
  return cards;
}

function playGame(E, seed, opts = {}) {
  const { RANKS, handTotal, resolvePlace, resolvePass } = E;
  const rng = mulberry32(seed);
  const order = shuffledDeck(rng, RANKS);

  const st = { slots: [[], [], [], []], deck: E.freshDeck(),
               lives: 3, passes: 2, score: 0, streak: 0 };
  E.setMode(opts.mode || 'balanced');
  E.setTarget(opts.target || 0);
  if (opts.bustBreaks !== undefined) E.setBustRule(opts.bustBreaks);
  if (opts.perfect !== undefined) E.setPerfect(opts.perfect);

  const stats = { busts: 0, forcedBusts: 0, passes: 0, win21: 0, win5: 0, win777: 0, win5x21: 0,
                  cashedOut: false, stoppedEarly: false, forfeited: false, cardsDealt: 0, maxStreak: 0,
                  chainBonus: 0, clears: 0, chainHist: [0, 0, 0, 0, 0] };
  // chainHist[k] = number of streaks of length k (index 4 = length 4 or more)
  let curChain = 0;
  const closeChain = () => { if (curChain > 0) stats.chainHist[Math.min(4, curChain)]++; curChain = 0; };

  for (let n = 0; n < order.length; n++) {
    if (st.lives <= 0) break;
    const card = order[n];
    st.deck[card]--;
    stats.cardsDealt++;
    E.setState(st);

    let anySafe = false;
    for (let i = 0; i < 4; i++) {
      if (handTotal([...st.slots[i], card]).min <= 21) { anySafe = true; break; }
    }

    if (!anySafe && st.passes === 0) {
      const bustSlot = E.chooseForcedBust(card);
      resolvePlace(st, bustSlot, card);
      stats.busts++; stats.forcedBusts++;
      closeChain();
      continue;
    }

    const act = E.chooseBest(card);
    if (act.type === 'stop') { stats.cashedOut = true; stats.stoppedEarly = true; break; }
    const rawEvt = act.type === 'pass' ? resolvePass(st, act.slot, card, act.to)
                                       : resolvePlace(st, act.slot, card);
    const stayed = rawEvt.startsWith('pass');
    if (stayed) { stats.passes++; closeChain(); }       // the stay itself ends the streak
    const evt = rawEvt.startsWith('pass+') ? rawEvt.slice(5) : rawEvt;
    if (evt === 'bust') { stats.busts++; }
    else if (evt === 'win21') stats.win21++;
    else if (evt === 'win5') stats.win5++;
    else if (evt === 'win777') stats.win777++;
    else if (evt === 'win5x21') stats.win5x21++;

    const isClear = evt === 'win21' || evt === 'win5' || evt === 'win777' || evt === 'win5x21';
    if (isClear) { stats.clears++; curChain++; stats.chainBonus += E.streakBonus(st.streak); }
    else if (evt === 'bust') closeChain();   // only a stay or a bust ends a streak here
    if (st.streak > stats.maxStreak) stats.maxStreak = st.streak;
  }

  closeChain();
  const final = st.score + (st.lives >= 3 ? E.perfect() : 0);
  return { final, score: st.score, lives: st.lives, ...stats };
}

module.exports = { playGame, mulberry32, shuffledDeck };
