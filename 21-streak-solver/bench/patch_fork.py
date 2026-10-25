# One-shot patch that turned the old 4-slot solver (blackjack-solver/index.html) into the
# STREAK-rules build. Kept for the record; every replacement must match exactly once.
import re, sys, io
p = 'index.html'
s = io.open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        print('PATCH FAIL (%d matches): %r' % (n, old[:80])); sys.exit(1)
    s = s.replace(old, new)

rep('<title>21 Solver — FINAL</title>', '<title>21 STREAK Solver</title>')
rep('<h1>21 Solver <span style="font-size:10px;color:#f59e0b">FINAL</span></h1>',
    '<h1>21 STREAK Solver <span style="font-size:10px;color:#f59e0b">streak survives builds</span></h1>')
rep('<div class="lbl">PASSES</div>', '<div class="lbl">STAYS</div>')

# ---- rules block ----
rep("const PTS_5CARD21 = 1000;",
    "const PTS_5CARD21 = 1000;  // confirmed: 5-card exact 21 paid 2000 at streak x10 = 1000 + 1000 bonus\n"
    "// ===== STREAK RULES (this game) =====\n"
    "// The streak counts consecutive clears and is broken ONLY by a STAY (clear) and, we\n"
    "// assume, by a bust. Building a stack with a non-clearing card does NOT break it, which\n"
    "// is why streaks of x10+ happen here and never did in the 4-slot 'any move' variant.\n"
    "const RULE_SAFE_BREAKS_STREAK = false;   // this game: a non-clearing placement keeps the streak\n"
    "let   RULE_BUST_BREAKS_STREAK = true;    // assumed ('potentially bust'); toggle in the UI\n"
    "// There is NO early exit / cash-out in this game: every dealt card must be played.")
rep("const PTS_PERFECT = 1000;  // confirmed: bonus for ending with all 3 lives",
    "let PTS_PERFECT = 1000;    // carried over from the old game; toggle in the UI if this one does not pay it")
rep("// With only 4 slots, a streak can be at most 4 consecutive 21s (one per slot), so the\n"
    "// highest combo is the 3rd (the 4th 21). Confirmed bonuses: 1st +250, 2nd +500, 3rd +1000.\n"
    "const STREAK_BONUS = [0, 250, 500, 1000];  // index = combo number; index 3 = 3rd combo (4th 21) = max",
    "// Streak payouts for a plain 21: x1 400, x2 650, x3 900, x4 1400, x5..x13+ 1400 (flat).\n"
    "// i.e. an additive bonus of +0 / +250 / +500 / +1000 (cap) on top of any clear's base.\n"
    "const STREAK_BONUS = [0, 250, 500, 1000];  // index = combo number; index 3+ = +1000 forever")

# ---- resolvePlace ----
rep("    st.slots[slotIdx] = [];\n    st.lives--;\n    st.streak = 0;\n    return 'bust';",
    "    st.slots[slotIdx] = [];\n    st.lives--;\n    if(RULE_BUST_BREAKS_STREAK) st.streak = 0;\n    return 'bust';")
rep("  st.streak = 0; // ANY move that isn't a 21 breaks the streak\n  return 'safe';",
    "  if(RULE_SAFE_BREAKS_STREAK) st.streak = 0; // this game: building keeps the streak alive\n  return 'safe';")

# ---- keys: streak beyond 4 is equivalent (bonus is flat), so clamp it in memo keys ----
rep("    (st.lives<<6)|(st.passes<<4)|st.streak\n  );", "    (st.lives<<6)|(st.passes<<4)|Math.min(st.streak,4)\n  );")
rep("(lives<<18)|(passes<<20)|(streak<<22);", "(lives<<18)|(passes<<20)|((streak>4?4:streak)<<22);")

# ---- exact decision node: no cash-out, streak rules ----
rep("  var best = fsFinal(score, lives);   // CASH OUT (end-anytime rule)",
    "  var best = -Infinity;   // no cash-out in this game: the card must be played")
rep("    if(nmin>21){ nCode=0; nLives=lives-1; nStreak=0; }",
    "    if(nmin>21){ nCode=0; nLives=lives-1; nStreak=RULE_BUST_BREAKS_STREAK?0:streak; }")
rep("      } else { nStreak=0; nCode=fsMake(nmin,nlen,nace,nsev); }",
    "      } else { nStreak=RULE_SAFE_BREAKS_STREAK?0:streak; nCode=fsMake(nmin,nlen,nace,nsev); }")

# ---- greedy rollout policy: no 'stop' ----
rep("  if(allowStop && allBust && st.passes===0){\n"
    "    // End-anytime rule: eat an early forced bust (remaining cards outweigh the bonus),\n"
    "    // end on a late one. Thresholds from EV: ~145 pts/card of upside vs 1000 bonus + life.\n"
    "    if(st.lives===3 && remTot2<=12) return {type:'stop'};\n"
    "    if(st.lives<3 && remTot2<=5) return {type:'stop'};\n"
    "  }\n", "")

# ---- dealCard: forced bust is eaten, only the sacrificed slot is chosen ----
a = s.index("    // FORCED-BUST DECISION (end-anytime games): card busts every slot, no passes left")
b = s.index("    const best=chooseBest(rank);")
new_block = '''    // FORCED BUST: the card busts every slot and no stays are left. There is no early
    // exit in this game, so the only decision is WHICH slot to sacrifice. A low slot is the
    // flexible one; a dead 20 will only force another bust. Evaluate every bust properly:
    // exactly when the deck is short enough, otherwise by rollout.
    if(passes===0){
      let anySafe=false;
      for(let i=0;i<4;i++){ if(handTotal([...slots[i], rank]).min<=21){ anySafe=true; break; } }
      if(!anySafe){
        const bestBust = chooseForcedBust(rank);
        const stB = { slots, deck, lives, passes, score, streak };
        resolvePlace(stB, bestBust, rank);
        lives=stB.lives; score=stB.score; streak=stB.streak;
        flashSlot=bestBust; forcedBustFlag=true;
        lastMove={card:rank, text:'\\u2192 SLOT '+(bestBust+1)+' (forced bust \\u2014 every slot busts)',
                  sub:(lives>0 ? 'lost a life, '+lives+' left' : 'OUT OF LIVES \\u2014 game over')+(RULE_BUST_BREAKS_STREAK?' \\u00b7 streak reset':'')};
        logRows.unshift({cls:'lose', txt:'FORCED BUST slot '+(bestBust+1)+' \\u2014 '+lives+' lives left'});
        pending=null;
        render();
        return;
      }
    }
'''
s = s[:a] + new_block + s[b:]

# chooseForcedBust: shared by the app and the bench (lives in the engine block)
rep("function snapshot(){",
'''// Which slot to sacrifice when the dealt card busts every slot and no stays remain.
// (deck already decremented by dealCard)
function chooseForcedBust(rank){
  let bestBust=0, bestBV=-Infinity;
  let remSac=0; for(const r of RANKS) remSac+=deck[r];
  const useExact = remSac<=EXACT_LIMIT;
  let seqSac=null;
  if(!useExact){ try{ seqSac=genSequences(deck, 300); }catch(e){ seqSac=null; } }
  for(let i=0;i<4;i++){
    const sv={ slots: slots.map(x=>[...x]), deck:{...deck}, lives, passes, score, streak };
    resolvePlace(sv, i, rank);
    let v;
    if(sv.lives<=0) v = sv.score;
    else if(useExact){
      memoInit(); exactNodes=0; exactDeadline=Date.now()+exactBudgetFor(remSac);
      v = exactChance(sv);
      if(exactNodes>EXACT_NODE_CAP_DEEP){ v=0; const q2=genSequences(deck,300); for(const q of q2) v+=rolloutSeqReal(sv,q); v/=Math.max(1,q2.length); }
    }
    else if(seqSac && seqSac.length){ v=0; for(const q of seqSac) v+=rolloutSeqReal(sv, q); v/=seqSac.length; }
    else v = stateValue(sv);
    if(v>bestBV){ bestBV=v; bestBust=i; }
  }
  return bestBust;
}

function snapshot(){''')

# ---- text: pass -> stay ----
rep("      txt='→ PASS SLOT '+(best.slot+1)+' (clear it, card starts fresh)';\n"
    "      sub=passes+' pass'+(passes===1?'':'es')+' left';\n"
    "      logCls='lose'; logTxt='Passed slot '+(best.slot+1)+' — '+passes+' left';",
    "      txt='→ STAY / CLEAR SLOT '+(best.slot+1)+' (card starts it fresh)';\n"
    "      sub=passes+' stay'+(passes===1?'':'s')+' left · streak reset';\n"
    "      logCls='lose'; logTxt='STAY cleared slot '+(best.slot+1)+' — '+passes+' left, streak reset';")
rep("else if(evt==='win5'){ sub='5-card stack ✓ +800'; logCls='win'; logTxt='5-card win in slot '+(best.slot+1); }",
    "else if(evt==='win5'){ sub='5-card stack ✓ +800'+(streak>1?' (streak x'+streak+')':''); logCls='win'; logTxt='5-card win in slot '+(best.slot+1)+(streak>1?' — streak '+streak:''); }")
rep("else if(evt==='bust'){ sub='forced bust — lost a life'; logCls='lose'; logTxt='BUST slot '+(best.slot+1)+' — '+lives+' lives left'; forcedBustFlag=true; }",
    "else if(evt==='bust'){ sub='deliberate bust — lost a life'+(RULE_BUST_BREAKS_STREAK?', streak reset':''); logCls='lose'; logTxt='BUST slot '+(best.slot+1)+' — '+lives+' lives left'; forcedBustFlag=true; }")
rep("if(logTxt) logRows.unshift({cls:logCls, txt:logTxt});",
    "if(logTxt) logRows.unshift({cls:logCls, txt:logTxt+((evt==='win21'||evt==='win777'||evt==='win5'||evt==='win5x21')&&streakBonus(streak)>0 ? ' (+'+streakBonus(streak)+' streak)' : '')});")

# ---- dead-game box: no forfeit here ----
rep("'. Your score is final at '+(score+(lives>=3?PTS_PERFECT:0))+\n"
    "          ' — playing on cannot gain a point and risks the all-lives bonus.';",
    "'. Nothing left can score: just place the rest where they cannot bust.';")
rep("FORFEIT — NO MORE POINTS POSSIBLE", "NO MORE POINTS POSSIBLE")

# ---- streak display shows what the next clear pays ----
rep("document.getElementById('streak').textContent=streak;",
    "document.getElementById('streak').textContent=streak>0 ? 'x'+streak+' (next +'+streakBonus(streak+1)+')' : '0 (next +0)';")

# ---- settings UI ----
rep('    <div class="hint" style="margin-top:6px">PLAY MODE</div>',
    '''    <div class="hint" style="margin-top:6px">RULE TOGGLES (unconfirmed rules — flip if the game proves otherwise)</div>
    <label style="display:block;font-size:11px;color:#cbd5e1;margin:3px 0"><input type="checkbox" id="rBust" checked onchange="setBustRule(this.checked)"> a BUST resets the streak</label>
    <label style="display:block;font-size:11px;color:#cbd5e1;margin:3px 0"><input type="checkbox" id="rPerf" checked onchange="setPerfect(this.checked)"> +1000 end bonus for finishing with all 3 lives</label>
    <div class="hint" style="margin-top:6px">PLAY MODE</div>''')
rep("function loadMode(){",
    '''function setBustRule(v){ RULE_BUST_BREAKS_STREAK=!!v; try{ localStorage.setItem('s21bust', v?'1':'0'); }catch(e){} }
function setPerfect(v){ PTS_PERFECT = v ? 1000 : 0; try{ localStorage.setItem('s21perf', v?'1':'0'); }catch(e){} render(); }
function loadRules(){
  try{
    const b=localStorage.getItem('s21bust'); if(b!==null){ RULE_BUST_BREAKS_STREAK=(b==='1'); document.getElementById('rBust').checked=RULE_BUST_BREAKS_STREAK; }
    const p=localStorage.getItem('s21perf'); if(p!==null){ PTS_PERFECT=(p==='1')?1000:0; document.getElementById('rPerf').checked=PTS_PERFECT>0; }
  }catch(e){}
}
function loadMode(){''')
rep("try{ renderHistory(); loadMode(); }catch(e){}", "try{ renderHistory(); loadMode(); loadRules(); }catch(e){}")

# ---- footer ----
rep("Rules modeled: slot clears on exact 21 or on 5 cards ≤ 21; busting clears the slot and costs a life (3 lives, +1000 bonus for keeping all 3); 2 passes let you clear a stuck slot instead of busting; the 21-streak breaks on ANY move that isn't a 21. It always takes an available 21 and burns a pass before ever busting.",
    "Rules modeled: slot clears on exact 21 (400), 5 cards ≤ 21 (800), 5-card 21 (1000) or 7-7-7 (600); the streak adds +250 / +500 / +1000 (x2 / x3 / x4 and beyond) to every clear and survives non-clearing placements — only a STAY (clear, 2 per game) or a bust resets it. Busting clears the slot and costs one of 3 lives. No early exit: every card must be played.")

io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched OK')
