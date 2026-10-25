# Third patch: a STAY clears a slot and the dealt card may then go into ANY slot (confirmed
# 2026-09-14), not only the cleared one. Action becomes {type:'pass', slot:<cleared>, to:<dest>}.
import io, sys

def patch(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            print('PATCH FAIL in %s (%d matches): %r' % (path, n, old[:100])); sys.exit(1)
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)

patch('index.html', [
# ---- resolvePass ----
("""// Pass: clear slot, place current card into it fresh. Costs one pass, breaks streak.
const RULE_PASS_BREAKS_STREAK = true;   // confirmed by play
const RULE_5CARD_BREAKS_STREAK = false; // confirmed: 5-card wins keep the combo going

function resolvePass(st, slotIdx, card){
  st.slots[slotIdx] = [card];
  st.passes--;
  if(RULE_PASS_BREAKS_STREAK) st.streak = 0;
  const {best} = handTotal(st.slots[slotIdx]);
  if(best === 21) { /* single card can't be 21 */ }
  return 'pass';
}""",
"""// STAY: clear a slot (costs one stay, resets the streak), then the dealt card goes ANYWHERE:
// into the cleared slot (fresh) or any other slot, where it may complete a 21 and start a new
// streak at x1. Confirmed by play 2026-09-14. Returns 'pass', or 'pass+<event>' when the
// placement itself clears or busts.
const RULE_PASS_BREAKS_STREAK = true;   // confirmed by play
const RULE_5CARD_BREAKS_STREAK = false; // confirmed: 5-card wins keep the combo going

function resolvePass(st, slotIdx, card, toIdx){
  if(toIdx===undefined) toIdx=slotIdx;
  st.slots[slotIdx] = [];
  st.passes--;
  if(RULE_PASS_BREAKS_STREAK) st.streak = 0;
  const evt = resolvePlace(st, toIdx, card);
  return evt==='safe' ? 'pass' : 'pass+'+evt;
}"""),
# ---- greedy rollout policy: card busts every slot, so the only safe home is the cleared slot ----
("    return {type:'pass', slot:pi};", "    return {type:'pass', slot:pi, to:pi};"),
("    if(ch.type==='pass') resolvePass(st, ch.slot, card);\n    else resolvePlace(st, ch.slot, card);\n  }\n  return stateValue(st);",
 "    if(ch.type==='pass') resolvePass(st, ch.slot, card, ch.to);\n    else resolvePlace(st, ch.slot, card);\n  }\n  return stateValue(st);"),
("    if(ch.type==='pass') resolvePass(st, ch.slot, card);\n    else resolvePlace(st, ch.slot, card);\n  }\n  return st.score",
 "    if(ch.type==='pass') resolvePass(st, ch.slot, card, ch.to);\n    else resolvePlace(st, ch.slot, card);\n  }\n  return st.score"),
# ---- exact decision node ----
("""      for(var k=0;k<4;k++){
        if(((sl[k]>>>2)&7)===0) continue;
        var s0=sl[k];
        sl[k]=fsMake(v,1,isA,is7);
        var val2=fsChance(sl, dk, total, lives, passes-1, 0, score);
        sl[k]=s0;
        if(val2>best) best=val2;
      }""",
"""      var pStreak = RULE_PASS_BREAKS_STREAK ? 0 : streak;
      for(var k=0;k<4;k++){
        if(((sl[k]>>>2)&7)===0) continue;
        var s0=sl[k];
        sl[k]=0;                                   // the stay empties slot k ...
        for(var j=0;j<4;j++){                      // ... and the card may go into ANY slot
          var cj=sl[j], jmin=cj>>>5, jlen=(cj>>>2)&7;
          if(jmin+v>21) continue;                  // busting after a stay is dominated by the fresh slot
          var jace=((cj>>>1)&1)|isA, jsev=(jlen===0)?is7:((cj&1)&is7);
          var jmin2=jmin+v, jlen2=jlen+1, jScore=score, jStreak=pStreak, jCode;
          var jb21=(jace && jmin2+10<=21) ? jmin2+10 : jmin2;
          if(jb21===21){ jStreak=pStreak+1; jScore=score+(jlen2>=5 ? PTS_5CARD21 : ((jlen2===3 && jsev) ? PTS_777 : PTS_21))+streakBonus(jStreak); jCode=0; }
          else if(jlen2>=5){ jStreak=pStreak+1; jScore=score+PTS_5CARD+streakBonus(jStreak); jCode=0; }
          else jCode=fsMake(jmin2,jlen2,jace,jsev);
          sl[j]=jCode;
          var val2=fsChance(sl, dk, total, lives, passes-1, jStreak, jScore);
          sl[j]=cj;
          if(val2>best) best=val2;
        }
        sl[k]=s0;
      }"""),
# ---- exactBest ----
("""  if(passes>0){
    for(let i=0;i<4;i++){
      if(slots[i].length===0) continue;
      const sv={ slots:slots.map(x=>[...x]), deck:{...deck}, lives, passes, score, streak };
      resolvePass(sv, i, card);
      const v=exactChance(sv);
      // a pass never costs a life, so it also outranks a tied bust
      if(v>bestV || (v===bestV && bestBust)){ bestV=v; bestBust=false; bestAct={type:'pass', slot:i, evt:'pass', ev:v}; }
    }
  }""",
"""  if(passes>0){
    for(let i=0;i<4;i++){
      if(slots[i].length===0) continue;
      for(let j=0;j<4;j++){
        if(j!==i && handTotal([...slots[j], card]).min>21) continue;   // busting after a stay is dominated
        const sv={ slots:slots.map(x=>[...x]), deck:{...deck}, lives, passes, score, streak };
        const pe=resolvePass(sv, i, card, j);
        const v=exactChance(sv);
        // a stay never costs a life, so it also outranks a tied bust
        if(v>bestV || (v===bestV && bestBust)){ bestV=v; bestBust=false; bestAct={type:'pass', slot:i, to:j, evt:pe, ev:v}; }
      }
    }
  }"""),
# ---- chooseBest candidates ----
("""    if(passes>0){
      for(let i=0;i<4;i++){
        if(slots[i].length===0) continue;
        candidates.push({type:'pass', slot:i});
      }
    }
  }""",
"""    if(passes>0){
      for(let i=0;i<4;i++){
        if(slots[i].length===0) continue;
        for(let j=0;j<4;j++){
          if(j!==i && handTotal([...slots[j], card]).min>21) continue;   // busting after a stay is dominated
          candidates.push({type:'pass', slot:i, to:j});
        }
      }
    }
  }"""),
("""    const seen=new Set();
    candidates = candidates.filter(c => {
      if(c.type!=='place') return true;
      const post = slots.map((sl,j)=> j===c.slot ? slotKey([...sl, card]) : slotKey(sl)).sort().join('|');
      if(seen.has(post)) return false;
      seen.add(post);
      return true;
    });""",
"""    const seen=new Set();
    candidates = candidates.filter(c => {
      let post;
      if(c.type==='place') post = slots.map((sl,j)=> j===c.slot ? slotKey([...sl, card]) : slotKey(sl)).sort().join('|');
      else post = 'P'+slots.map((sl,j)=> { const base = (j===c.slot) ? [] : sl; return slotKey(j===c.to ? [...base, card] : base); }).sort().join('|');
      if(seen.has(post)) return false;
      seen.add(post);
      return true;
    });"""),
("    const evt = c.type==='pass' ? resolvePass(st, c.slot, card) : resolvePlace(st, c.slot, card);",
 "    const evt = c.type==='pass' ? resolvePass(st, c.slot, card, c.to) : resolvePlace(st, c.slot, card);"),
("    const rerun = evalOn(pool.slice(0,2).map(r=>({type:r.type, slot:r.slot})), seqs.concat(extra));\n    rerun.sort((a,b)=>b.ev-a.ev || a.slot-b.slot);\n    return rerun[0];\n  }\n\n  // PLACEMENTS",
 "    const rerun = evalOn(pool.slice(0,2).map(r=>({type:r.type, slot:r.slot, to:r.to})), seqs.concat(extra));\n    rerun.sort((a,b)=>b.ev-a.ev || a.slot-b.slot);\n    return rerun[0];\n  }\n\n  // PLACEMENTS"),
("    const rerun = evalOn(pool.slice(0,2).map(r=>({type:r.type, slot:r.slot})), seqs.concat(extra));\n    rerun.sort((a,b)=>b.ev-a.ev || a.slot-b.slot);\n    // Still within noise",
 "    const rerun = evalOn(pool.slice(0,2).map(r=>({type:r.type, slot:r.slot, to:r.to})), seqs.concat(extra));\n    rerun.sort((a,b)=>b.ev-a.ev || a.slot-b.slot);\n    // Still within noise"),
# ---- dealCard: apply + text ----
("""    if(best.type==='pass'){
      evt=resolvePass(st, best.slot, rank);
    } else {
      evt=resolvePlace(st, best.slot, rank);
    }
    lives=st.lives; passes=st.passes; score=st.score; streak=st.streak;
    flashSlot=best.slot;
    let txt, sub='', logCls='', logTxt='';
    if(best.type==='pass'){
      txt='→ STAY / CLEAR SLOT '+(best.slot+1)+' (card starts it fresh)';
      sub=passes+' stay'+(passes===1?'':'s')+' left · streak reset';
      logCls='lose'; logTxt='STAY cleared slot '+(best.slot+1)+' — '+passes+' left, streak reset';
    } else {
      txt='→ SLOT '+(best.slot+1);
      if(evt==='win21')""",
"""    if(best.type==='pass'){
      evt=resolvePass(st, best.slot, rank, best.to);
    } else {
      evt=resolvePlace(st, best.slot, rank);
    }
    lives=st.lives; passes=st.passes; score=st.score; streak=st.streak;
    flashSlot=(best.type==='pass') ? best.to : best.slot;
    let txt, sub='', logCls='', logTxt='';
    if(best.type==='pass'){
      const to=(best.to===undefined)?best.slot:best.to;
      txt='→ STAY SLOT '+(best.slot+1)+', then card to SLOT '+(to+1)+(to===best.slot?' (fresh)':'');
      const pe = evt.startsWith('pass+') ? evt.slice(5) : 'safe';
      const win = pe==='win21' ? '21! ✓' : pe==='win777' ? 'TRIPLE 7s! 600 ✓' : pe==='win5x21' ? '5-CARD 21! ✓ +1000' : pe==='win5' ? '5-card stack ✓ +800' : pe==='bust' ? 'BUST — lost a life' : '';
      sub=passes+' stay'+(passes===1?'':'s')+' left · streak reset'+(win?' · '+win+(streak>0?' (streak x'+streak+')':''):'');
      logCls=(pe.startsWith('win')?'win':'lose'); logTxt='STAY cleared slot '+(best.slot+1)+', card to slot '+(to+1)+(win?' — '+win:'')+' — '+passes+' stay'+(passes===1?'':'s')+' left';
    } else {
      txt='→ SLOT '+(best.slot+1);
      if(evt==='win21')"""),
])

# ---- bench/game.js ----
patch('bench/game.js', [
("    const evt = act.type === 'pass' ? resolvePass(st, act.slot, card)\n                                    : resolvePlace(st, act.slot, card);\n    if (evt === 'bust') { stats.busts++; }\n    else if (evt === 'pass') stats.passes++;\n    else if (evt === 'win21') stats.win21++;",
 "    const rawEvt = act.type === 'pass' ? resolvePass(st, act.slot, card, act.to)\n                                       : resolvePlace(st, act.slot, card);\n    const stayed = rawEvt.startsWith('pass');\n    if (stayed) { stats.passes++; closeChain(); }       // the stay itself ends the streak\n    const evt = rawEvt.startsWith('pass+') ? rawEvt.slice(5) : rawEvt;\n    if (evt === 'bust') { stats.busts++; }\n    else if (evt === 'win21') stats.win21++;"),
("    else if (evt === 'pass' || evt === 'bust') closeChain();   // only a stay or a bust ends a streak here",
 "    else if (evt === 'bust') closeChain();   // only a stay or a bust ends a streak here"),
])

# ---- bench/fuzz.js ----
patch('bench/fuzz.js', [
("    if (st.slots[act.slot].length === 0) record('PASSED AN EMPTY SLOT', { act, card });",
 "    if (st.slots[act.slot].length === 0) record('PASSED AN EMPTY SLOT', { act, card });\n"
 "    const to = act.to === undefined ? act.slot : act.to;\n"
 "    if (!(to >= 0 && to < 4)) record('STAY DESTINATION OUT OF RANGE', { act, card });\n"
 "    else if (to !== act.slot && E.handTotal([...st.slots[to], card]).min > 21) record('STAY INTO A BUST', { act, card, slots: JSON.stringify(st.slots) });"),
])

# ---- bench/trace.js ----
patch('bench/trace.js', [
("  else { act = E.chooseBest(card); evt = act.type === 'pass' ? E.resolvePass(st, act.slot, card) : E.resolvePlace(st, act.slot, card); }\n"
 "  console.log(String(n + 1).padStart(2), card.padStart(2), act.type.padEnd(6), 'slot', act.slot + 1, evt.padEnd(7),",
 "  else { act = E.chooseBest(card); evt = act.type === 'pass' ? E.resolvePass(st, act.slot, card, act.to) : E.resolvePlace(st, act.slot, card); }\n"
 "  console.log(String(n + 1).padStart(2), card.padStart(2), act.type.padEnd(6), 'slot', act.slot + 1, (act.type === 'pass' ? 'to ' + (act.to + 1) : '    '), evt.padEnd(7),"),
])
print('anywhere patched OK')
