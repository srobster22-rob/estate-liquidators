// THE MUTATION FAMILY'S GATES, TEST-ONLY (L36 of this log).
//
// The other session moved mutGate, springGate and its new whipGate out of the
// page and into a test-only file of its own (tools/qa/mutations.js in its
// workspace), which never reaches this repository - only the page does. So the
// merge that brought WHIPTAIL in would have left section 97 calling two gates
// the page no longer carries, and WHIPTAIL with no gate here at all. This file
// is this repository's copy of the family's gates, at the peer's path:
//
//   mutGate, springGate - PORTED VERBATIM from the page as L30 last shipped
//                         them (the gates were written by the rounds that built
//                         the cards; the port changes where they live, not what
//                         they say - any edit below that is not a move is
//                         marked L36).
//   whipGate            - WRITTEN HERE for WHIPTAIL, in the same contract.
//
// THE FORM. The whole file is ONE expression, an object of gates. Section 97
// reads it from disk and evaluates it INSIDE the page with an indirect eval,
// so the page's own top-level bindings (PASSIVES, P, MUT_ON, ramMaybe, ...) are
// in scope exactly as they were when these lived in window.__g, and each gate
// runs against the live build a mutant hands the suite. Each returns
// { ok, bad[] } with its failures already worded, like every gate in 97.
// Strict, as the page is: a gate that assigns a page name the page no longer
// has must throw rather than quietly make a window global of it.
"use strict";
({
  // THE GATE. Subjects derived: the card is every PASSIVES entry with `mut`,
  // the trample is the same ramMaybe() step() calls, the horn is the real
  // drawMonBody. Each clause is a way the change could be wrong, and each
  // guard (switch, rush, moving, boss, kit, cooldown) has its own null.
  mutGate:()=>{
    const bad = [], subj = Object.keys(PASSIVES).filter(k => PASSIVES[k].mut);
    if(!subj.length) bad.push("NO MUTATION CARD IN PASSIVES");
    if(ramGive !== -1) bad.push(`THE BENCH KNOB IS LEFT ARMED: ramGive ${ramGive}, ships -1 (the card is out of the draft while it is set)`);
    const keep = { on:MUT_ON, rush:P.rush, idle:P.idle, lvl:P.lvl, ram:P.kit.ram, iframe:P.iframe };
    qaLive(bad, "THE MUTATION GATE");
    // 1. THE DRAFT, BOTH WAYS. With a free rule slot and past RULE_FROM, the
    // card must turn up in dealt hands with the switch on and never with it off.
    // The gate owns its precondition: a run that has already filled its rule
    // slots (the battery hands this gate a level-39 kit with three rules)
    // deals no rule at all, which is the game being right, not the card
    // missing. So the other rules are stood aside for this clause only.
    const stash = {}, nrWas = noRules; noRules = false;
    for(const k of Object.keys(P.kit)) if(isRule(k)){ stash[k] = P.kit[k]; delete P.kit[k]; }
    P.lvl = Math.max(P.lvl, RULE_FROM);
    // L36: counted PER CARD. With three cards in the family (ram, spring, tail)
    // a family total stays green while any one of them is out of the draft -
    // measured: RAMHORN barred outright still read "draft on 45" here.
    const dealt = (on)=>{ MUT_ON = on; const n = {}; for(const k of subj) n[k] = 0;
      for(let i=0;i<300;i++) for(const o of offers()) if(subj.includes(o.key)) n[o.key]++; return n; };
    const byOn = dealt(true), byOff = dealt(false), sum = n => subj.reduce((s, k)=>s + n[k], 0);
    const nOn = sum(byOn), nOff = sum(byOff);
    for(const k of subj) if(!(byOn[k] > 0)) bad.push(`THE MUTATION NEVER REACHES THE DRAFT: ${PASSIVES[k].name} (${k}) in 0 of 300 hands with the switch on`);
    if(nOff > 0)   bad.push(`THE OFF SWITCH LEAVES THE CARD IN THE DRAFT: ${nOff} of 300 hands with the switch off`);
    MUT_ON = true;
    for(const k of subj){
      const hand = (()=>{ for(let i=0;i<300;i++){ const o = offers().find(o=>o.key === k); if(o) return o; } return null; })();
      if(hand && (hand.lv !== "MUTATION" || cardFamily(hand) !== "mut"))
        bad.push(`THE CARD DOES NOT SAY MUTATION: ${k} lv ${hand.lv}, family ${cardFamily(hand)}`);
    }
    for(const k in stash) if(k !== "ram") P.kit[k] = stash[k];
    noRules = nrWas;
    // 2. THE TRAMPLE. One fat body 0.9 m ahead, winding up a bite.
    const mk = ()=>{ window.__g.clearEnemies(); const e = spawnEnemy("skitter", P.x + .9, P.z);
                     e.hp = e.maxhp = 1e9; e.rise = 0; e.dig = 0; e.stoop = 0; e.wu = .5; e.lg = 0; e.kx = 0; e.kz = 0;
                     rebuildGrid(); return e; };
    const trial = (c)=>{
      const e = mk(); if(c.boss) e.boss = true;
      MUT_ON = c.on; P.rush = c.rush; P.idle = c.idle;
      if(c.kit) P.kit.ram = { key:"ram", l:0, t:0, evo:false }; else delete P.kit.ram;
      const h0 = e.hp, n0 = ramN; ramMaybe();
      const out = { hit: e.hp < h0, n: ramN - n0, wu: e.wu, push: e.kx*(e.x-P.x) + e.kz*(e.z-P.z), e };
      if(c.again){ const h1 = e.hp; ramMaybe(); out.again = e.hp < h1; }
      if(e.boss && !c.boss) e.boss = false;
      return out;
    };
    const base = { on:true, rush:1, idle:0, kit:true };
    const A = trial(Object.assign({}, base, { again:true }));
    if(!A.hit || A.n !== 1) bad.push(`THE RUSH DOES NOT TRAMPLE: a body 0.9 m ahead took no bonk (hit ${A.hit}, n ${A.n})`);
    if(!(A.push > 0)) bad.push(`A BONKED BODY IS NOT THROWN ASIDE: shove along the line out ${A.push}`);
    if(A.wu !== 0) bad.push(`A BONKED BODY STILL BITES: its wind-up is ${A.wu}, not knocked out`);
    if(A.again) bad.push(`THE SAME BODY WAS TRAMPLED TWICE INSIDE RAM_CD (${RAM_CD} s)`);
    const nulls = [["THE OFF SWITCH DOES NOT STOP THE TRAMPLE", { on:false }],
                   ["IT TRAMPLES WITHOUT A RUSH", { rush:0 }],
                   ["IT TRAMPLES STANDING STILL", { idle:1 }],
                   ["IT TRAMPLES WITHOUT THE CARD", { kit:false }],
                   ["IT TRAMPLES A BOSS", { boss:true }]];
    for(const [msg, c] of nulls){ const r = trial(Object.assign({}, base, c)); if(r.hit || r.n) bad.push(msg); }
    // 3. THE HORN, on the real body: grown with the card, not without it, not
    // with the switch off, and never on THE SPLIT's second creature.
    const mesh = (ch, kit, twin)=>{
      const sp = { x:0, y:0, z:0, face:0, iframe:0, hopFx:0, air:false, portrait:true, rush:0,
                   mscale:1, kit, surge:0, surgeT:0, legSpan:null, headSpan:null };
      if(twin) sp.twinOf = {};
      const an = { ph:0, amp:0, lean:0, bank:0, sq:1, lunge:0, look:0, land:0,
                   hit:0, hitR:0, hitF:-1, br:0, dead:0, atkT:9, atkKind:"", atkDir:0, atkSide:1, atkAmp:1 };
      const cP = bodyPos, cC = bodyCap; let out;
      for(let i=0;i<2;i++){ bodyPos = []; bodyCap = null; drawMonBody(ch, sp, an, 0, 0, T); out = bodyPos; }
      bodyPos = cP; bodyCap = cC; vn = 0; nbox = 0;
      return out;
    };
    const same = (a, b)=> a.length === b.length && a.every((v,i)=>Math.abs(v - b[i]) < 1e-9);
    const rk = { ram:{ key:"ram", l:0, t:0, evo:false } };
    let grew = 0, forms = 0;
    for(const ch of CHARS){
      forms++; MUT_ON = true;
      const A0 = mesh(ch, {}), A1 = mesh(ch, rk), AT = mesh(ch, rk, true), AT0 = mesh(ch, {}, true);
      MUT_ON = false; const AO = mesh(ch, rk); MUT_ON = true;
      if(!same(A0, A1)) grew++; else bad.push(`THE MUTATION GROWS NOTHING on ${ch.id}`);
      if(!same(A0, AO)) bad.push(`THE OFF SWITCH LEAVES THE HORN ON ${ch.id}`);
      if(!same(AT0, AT)) bad.push(`THE SPLIT'S SECOND CREATURE GROWS THE HORN on ${ch.id} - the twin is not the mutation's`);
    }
    // restore
    window.__g.clearEnemies();
    MUT_ON = keep.on; P.rush = keep.rush; P.idle = keep.idle; P.lvl = keep.lvl; P.iframe = keep.iframe;
    if(keep.ram) P.kit.ram = keep.ram; else delete P.kit.ram;
    qaSettle();
    return { ok: bad.length === 0, bad, subj, draft:{ on:nOn, off:nOff, by:byOn }, horn:`${grew}/${forms}`, switch:MUT_ON };
  },
  // THE GATE. Subjects derived: the card is the `mut` entry whose key the
  // dodge reads (PASSIVES.spring), the dodge is the REAL enemy loop in step()
  // (a body staged with its wind-up on its last frame), the springs are the
  // real drawMonBody. One clause per way it could be wrong, each with a null.
  springGate:()=>{
    const bad = [], key = "spring", card = PASSIVES[key];
    if(!card || !card.mut) bad.push("SPRINGHEEL IS NOT A MUTATION CARD IN PASSIVES");
    if(springGive !== -1) bad.push(`THE BENCH KNOB IS LEFT ARMED: springGive ${springGive}, ships -1`);
    const keep = { on:MUT_ON, lvl:P.lvl, sp:P.kit.spring, iframe:P.iframe, x:P.x, y:P.y, z:P.z,
                   air:P.air, vy:P.vy, fly:P.fly, hp:P.hp, ns:noSpawn, bd:botDrive };
    qaLive(bad, "THE SPRINGHEEL GATE");
    // 1. THE DRAFT, BOTH WAYS, this card by name (mutGate counts the family).
    const stash = {}, nrWas = noRules; noRules = false;
    for(const k of Object.keys(P.kit)) if(isRule(k)){ stash[k] = P.kit[k]; delete P.kit[k]; }
    P.lvl = Math.max(P.lvl, RULE_FROM);
    const dealt = (on)=>{ MUT_ON = on; let n = 0; for(let i=0;i<300;i++) for(const o of offers()) if(o.key === key) n++; return n; };
    const nOn = dealt(true), nOff = dealt(false); MUT_ON = true;
    if(!(nOn > 0)) bad.push("SPRINGHEEL NEVER REACHES THE DRAFT: 0 of 300 hands with the switch on");
    if(nOff > 0)   bad.push(`THE OFF SWITCH LEAVES SPRINGHEEL IN THE DRAFT: ${nOff} of 300 hands with the switch off`);
    const hand = (()=>{ for(let i=0;i<300;i++){ const o = offers().find(o=>o.key === key); if(o) return o; } return null; })();
    if(hand && (hand.lv !== "MUTATION" || cardFamily(hand) !== "mut"))
      bad.push(`SPRINGHEEL DOES NOT SAY MUTATION: lv ${hand.lv}, family ${cardFamily(hand)}`);
    for(const k in stash) if(k !== key) P.kit[k] = stash[k];
    noRules = nrWas;
    // 2. THE DODGE, through the real step(). A skitter in reach whose bite
    // resolves THIS frame; the player on the ground or 1 m up and rising.
    noSpawn = true; botDrive = false;
    const trial = (c)=>{
      window.__g.clearEnemies();
      const gy = groundY(P.x, P.z);
      const e = spawnEnemy("skitter", P.x + .4, P.z);
      e.hp = e.maxhp = 1e9; e.rise = 0; e.dig = 0; e.dug = 0; e.stoop = 0; e.rout = 0; e.burrow = false;
      e.wd = 0; e.lg = 0; e.dvT = 0; e.kx = 0; e.kz = 0;
      if(c.dive){ e.dvT = .05; e.wu = 0; } else e.wu = 1e-4;
      rebuildGrid();
      MUT_ON = c.on; P.fly = false; P.iframe = 0; P.hp = P.maxhp;
      // L40: the kit is only the card - the battery's weapons knocked the
      // staged skitter clear on some pages (the tell gate's finding, same trial)
      P.kit = c.kit ? { spring:{ key, l:0, t:0, evo:false } } : {};
      if(c.air){ P.air = true; P.y = gy + 1; P.vy = 6; } else { P.air = false; P.y = gy; P.vy = 0; }
      const n0 = hurtLog.n.contact, s0 = springN;
      step(1/60);
      return { hurt: hurtLog.n.contact - n0, dodged: springN - s0 };
    };
    const base = { on:true, kit:true, air:true }, kitWas = P.kit;
    const A = trial(base);
    if(A.hurt !== 0 || A.dodged !== 1) bad.push(`THE HOP DOES NOT DODGE THE BITE: in the air with the card the bite landed (hurt ${A.hurt}, dodged ${A.dodged})`);
    const nulls = [["THE OFF SWITCH DOES NOT STOP THE DODGE", { on:false }],
                   ["IT DODGES WITHOUT THE CARD", { kit:false }],
                   ["IT DODGES ON THE GROUND", { air:false }],
                   ["IT DODGES A DIVE (a dive comes from above)", { dive:true }]];
    for(const [msg, c] of nulls){ const r = trial(Object.assign({}, base, c));
      if(r.dodged || r.hurt !== 1) bad.push(`${msg}: hurt ${r.hurt}, dodged ${r.dodged}`); }
    // the twin: the dodge is the player's alone, by the same predicate
    P.kit = kitWas;
    if(springDodge({ twinOf:{}, kit:{ spring:{} }, air:true })) bad.push("THE SPLIT'S SECOND CREATURE DODGES - the twin is not the mutation's");
    // 3. THE SPRINGS, on the real body, all characters.
    const mesh = (ch, kit, twin, air)=>{
      const sp = { x:0, y:0, z:0, face:0, iframe:0, hopFx:0, air:!!air, portrait:true, rush:0,
                   mscale:1, kit, surge:0, surgeT:0, legSpan:null, headSpan:null };
      if(twin) sp.twinOf = {};
      const an = { ph:0, amp:0, lean:0, bank:0, sq:1, lunge:0, look:0, land:0,
                   hit:0, hitR:0, hitF:-1, br:0, dead:0, atkT:9, atkKind:"", atkDir:0, atkSide:1, atkAmp:1 };
      const cP = bodyPos, cC = bodyCap; let out;
      for(let i=0;i<2;i++){ bodyPos = []; bodyCap = null; drawMonBody(ch, sp, an, 0, 0, T); out = bodyPos; }
      bodyPos = cP; bodyCap = cC; vn = 0; nbox = 0;
      return out;
    };
    const same = (a, b)=> a.length === b.length && a.every((v,i)=>Math.abs(v - b[i]) < 1e-9);
    const rk = { spring:{ key, l:0, t:0, evo:false } };
    // boxes (6-tuples) in `b` that are not in `a`, flattened in order
    const grownBy = (a, b)=>{ const k = (x,i)=>x.slice(i,i+6).map(v=>v.toFixed(6)).join(","), have = new Set();
      for(let i=0;i<a.length;i+=6) have.add(k(a,i));
      const out = []; for(let i=0;i<b.length;i+=6) if(!have.has(k(b,i))) out.push(...b.slice(i,i+6)); return out; };
    let grew = 0, forms = 0;
    for(const ch of CHARS){
      forms++; MUT_ON = true;
      const A0 = mesh(ch, {}), A1 = mesh(ch, rk), AA = mesh(ch, rk, false, true), AT = mesh(ch, rk, true), AT0 = mesh(ch, {}, true);
      MUT_ON = false; const AO = mesh(ch, rk); MUT_ON = true;
      if(!same(A0, A1)) grew++; else bad.push(`SPRINGHEEL GROWS NOTHING on ${ch.id}`);
      // the springs' OWN boxes (what the card adds), on the ground and in the
      // air - a body that changes pose in the air by itself (a flier) must
      // not pass this for the springs
      const AA0 = mesh(ch, {}, false, true);
      // L40: judged on the springs' own SHAPE, not their absolute boxes. Two
      // bodies (accnt, pyre) change pose in the air, which moves the haunch
      // the springs hang from - so the old comparison of boxes saw "different"
      // there whether or not the coils opened, and a closed spring passed on 2
      // of 9. The openness is the stack's height over its thinnest box: a
      // translated or uniformly resized spring keeps it, an opened one grows.
      const open = (bx)=>{ let lo = 1e9, hi = -1e9, th = 1e9;
        for(let i = 0; i < bx.length; i += 6){ lo = Math.min(lo, bx[i+2] - bx[i+5]); hi = Math.max(hi, bx[i+2] + bx[i+5]); th = Math.min(th, bx[i+5]); }
        return bx.length ? (hi - lo) / th : 0; };
      const oG = open(grownBy(A0, A1)), oA = open(grownBy(AA0, AA));
      if(!(oA > oG * 1.2)) bad.push(`THE SPRINGS DO NOT OPEN IN THE AIR on ${ch.id} (openness ${oG.toFixed(2)} ground, ${oA.toFixed(2)} air)`);
      if(!same(A0, AO)) bad.push(`THE OFF SWITCH LEAVES THE SPRINGS ON ${ch.id}`);
      if(!same(AT0, AT)) bad.push(`THE SPLIT'S SECOND CREATURE GROWS THE SPRINGS on ${ch.id} - the twin is not the mutation's`);
    }
    // restore
    window.__g.clearEnemies();
    MUT_ON = keep.on; P.lvl = keep.lvl; P.iframe = keep.iframe; P.x = keep.x; P.y = keep.y; P.z = keep.z;
    P.air = keep.air; P.vy = keep.vy; P.fly = keep.fly; P.hp = keep.hp; noSpawn = keep.ns; botDrive = keep.bd;
    if(keep.sp) P.kit.spring = keep.sp; else delete P.kit.spring;
    qaSettle();
    return { ok: bad.length === 0, bad, draft:{ on:nOn, off:nOff }, dodge:A, springs:`${grew}/${forms}`, switch:MUT_ON };
  },
  // WHIPTAIL (the other session's third mutation): THE TURN. Written here, in
  // the family's contract, because the gate the other session wrote for it
  // stayed in its own workspace.
  whipGate:(() => {
    // WHIPTAIL's gate. TEST-ONLY: this is a source string the suite evaluates in
    // the page by indirect eval, so it reads the page's own top-level names; it is
    // not in window.__g and uses none of window.__g's internals. Same contract as
    // mutGate and springGate: every failure is worded in capitals, every guard has
    // its own null, and everything it touches is put back on the way out.
    // Subjects derived: the card is PASSIVES.tail (the entry whipMaybe's kit test
    // reads), the lash is the same whipMaybe() step() calls - driven on staged
    // headings, then once through the real step() at the controls - the sweep's
    // drawing is the real drawLash, the club is the real drawMonBody, and the arc
    // is whipSwept on staged numbers.
    const bad = [], key = "tail", card = PASSIVES[key], ms0 = Date.now();
    if(!card || !card.mut) bad.push("WHIPTAIL IS NOT A MUTATION CARD IN PASSIVES");
    if(whipGive !== -1) bad.push(`THE BENCH KNOB IS LEFT ARMED: whipGive ${whipGive}, ships -1 (the card is out of the draft while it is set)`);
    if(WHIP_ON !== true) bad.push(`WHIPTAIL'S OWN SWITCH IS LEFT OFF: WHIP_ON ${WHIP_ON}, ships true`);
    if(!P || !running) return { ok:false, bad:[...bad, "THE WHIPTAIL GATE WAS HANDED NO RUN (P is null or the run is not up)"] };
    const PI = Math.PI, SL = WHIP_SLOP, TAILK = ()=>({ key, l:0, t:0, evo:false });
    // ---- what it touches, kept
    const arrs = { enemies, corpses, gems, hazards, pets, zones, spits, bolts, mortars, rings, swings, arcs, pops, cpops, nums, alerts };
    const kArr = {}; for(const k in arrs) kArr[k] = arrs[k].slice();
    const kKit = P.kit, kKitC = Object.assign({}, P.kit), kBan = P.banned;
    const kH = P.whipH ? P.whipH.map(h => h.slice()) : undefined, hadH = "whipH" in P;
    const kPrim = {}; for(const k in P) if(P[k] === null || typeof P[k] !== "object") kPrim[k] = P[k];
    const ks = { on:MUT_ON, whip:WHIP_ON, give:whipGive, nr:noRules, T, n:whipN, hit:whipHit, dmg:dmgWhip,
                 dealt:dmgDealt, dboss:dmgBoss, shake, flash, R, ns:noSpawn, bd:botDrive, cam:camYaw,
                 anchor:camAnchor ? camAnchor.slice() : null, keyW:keys.KeyW, hadW:"KeyW" in keys,
                 flow:{ ...hordeFlow }, hl:JSON.stringify(hurtLog) };
    let ev0 = null, armed = false, lived = false;
    const out = { draft:null, swept:null, reach:null, lash:null, nulls:null, boss:null, cd:null, club:null, controls:null };
    const clear = ()=>{ for(const k of ["enemies","corpses","gems","hazards","pets","zones","spits","bolts","mortars","rings","swings","arcs"]) arrs[k].length = 0; rebuildGrid(); };
    // one staged body at bearing b (atan2 dx,dz from you) and distance d - a
    // number, or a function of the body (its radius) - winding up a bite
    const put = (b, d, boss)=>{
      const e = spawnEnemy("skitter", P.x, P.z); if(!e) return null;
      const dd = typeof d === "function" ? d(e) : d;
      e.x = P.x + Math.sin(b) * dd; e.z = P.z + Math.cos(b) * dd; e.y = groundY(e.x, e.z);
      e.hp = e.maxhp = 1e9; e.rise = 0; e.dig = 0; e.dug = 0; e.stoop = 0; e.rout = 0; e.burrow = false; e.dvT = 0;
      e.elite = false; e.wu = .5; e.wd = .3; e.lg = 0; e.kx = 0; e.kz = 0; e.boss = !!boss; e.dead = false;
      return e;
    };
    try {
      // the gate's own dice: offers(), spawnEnemy() and dmgOut() draw from R, and
      // nothing in here may move the run's stream
      R = mulberry32(0x7a11);
      // 1. THE DRAFT, THREE SWITCHES, this card by name. Dealt only while
      // MUT_ON && WHIP_ON && whipGive < 0; out with any one of them off - and
      // WHIP_ON is this card's alone, so the rest of the family is still dealt
      // with it off. The gate owns its precondition (a free rule slot, past
      // RULE_FROM, nothing banished), as mutGate does.
      {
        const stash = {}; noRules = false; P.banned = {};
        for(const k of Object.keys(P.kit)) if(isRule(k)){ stash[k] = P.kit[k]; delete P.kit[k]; }
        P.lvl = Math.max(P.lvl, RULE_FROM);
        const isTail = o => o.key === key, isKin = o => o.key !== key && !!(PASSIVES[o.key] && PASSIVES[o.key].mut);
        const dealt = (on, whip, give, pred)=>{ MUT_ON = on; WHIP_ON = whip; whipGive = give; let n = 0;
          for(let i = 0; i < 300; i++) for(const o of offers()) if(pred(o)) n++; return n; };
        const D = { on:dealt(true, true, -1, isTail), mutOff:dealt(false, true, -1, isTail), whipOff:dealt(true, false, -1, isTail),
                    give0:dealt(true, true, 0, isTail), give1:dealt(true, true, 1, isTail), kinWhipOff:dealt(true, false, -1, isKin) };
        // is any other mutation dealable right now (its own bench knob not armed)?
        const kinOpen = Object.keys(PASSIVES).some(k => k !== key && PASSIVES[k].mut && !(PASSIVES[k].bar && PASSIVES[k].bar()));
        MUT_ON = true; WHIP_ON = true; whipGive = -1;
        if(!(D.on > 0)) bad.push("WHIPTAIL NEVER REACHES THE DRAFT: 0 of 300 hands with MUT_ON, WHIP_ON on and whipGive -1");
        if(D.mutOff) bad.push(`THE FAMILY SWITCH (MUT_ON) LEAVES WHIPTAIL IN THE DRAFT: ${D.mutOff} of 300 hands`);
        if(D.whipOff) bad.push(`THE CARD'S OWN SWITCH (WHIP_ON) LEAVES WHIPTAIL IN THE DRAFT: ${D.whipOff} of 300 hands`);
        if(D.give0) bad.push(`THE BENCH'S OFF ARM (whipGive 0) LEAVES WHIPTAIL IN THE DRAFT: ${D.give0} of 300 hands - the control would draft it by itself`);
        if(D.give1) bad.push(`THE BENCH'S ON ARM (whipGive 1) LEAVES WHIPTAIL IN THE DRAFT: ${D.give1} of 300 hands - that arm is handed the card, not dealt it`);
        if(kinOpen && !(D.kinWhipOff > 0)) bad.push("WHIP_ON TAKES THE WHOLE FAMILY OUT OF THE DRAFT: with it off no other mutation was dealt in 300 hands - it is this card's switch, MUT_ON is the family's");
        const hand = (()=>{ for(let i = 0; i < 300; i++){ const o = offers().find(isTail); if(o) return o; } return null; })();
        if(hand && (hand.lv !== "MUTATION" || cardFamily(hand) !== "mut"))
          bad.push(`WHIPTAIL DOES NOT SAY MUTATION: lv ${hand.lv}, family ${cardFamily(hand)}`);
        for(const k in stash) P.kit[k] = stash[k];
        noRules = ks.nr; P.banned = kBan; P.lvl = kPrim.lvl;
        out.draft = D;
      }
      // 2. PURE: the arc the tail sweeps, on staged numbers. The tail points at
      // facing + PI, so a turn f0 -> f1 sweeps from f0 + PI the short way round,
      // WHIP_SLOP past each end; and the reach grows with the form.
      {
        const C = [
          [0, 2.4, PI, true, "the tail's start"],
          [0, 2.4, PI + 1.2, true, "mid-sweep"],
          [0, 2.4, PI + 2.4, true, "the tail's end"],
          [0, 2.4, PI - SL * .5, true, "inside the slop before the start"],
          [0, 2.4, PI + 2.4 + SL * .5, true, "inside the slop past the end"],
          [0, 2.4, PI - SL * 2, false, "behind the start, past the slop"],
          [0, 2.4, PI + 2.4 + SL * 2, false, "past the end, past the slop"],
          [0, 2.4, 1.2, false, "the head's side of the turn"],
          [0, 2.4, PI - 1.2, false, "the other side of the tail"],
          [0, -2.4, PI - 1.2, true, "mid-sweep, turning the other way"],
          [0, -2.4, PI + 1.2, false, "the right turn's side, turning left"],
          [2.8, 5.2, wrapAng(2.8 + PI + 1.2), true, "mid-sweep across the +-PI seam"],
          [2.8, 5.2, wrapAng(2.8 + PI - 1.2), false, "the other side, across the seam"],
          [0, 4.0, PI - 1.14, true, "0 -> 4.0 is a 2.28 turn left, the short way round"],
          [0, 4.0, PI + 2.0, false, "the long way round is not swept"],
          [0, 0, PI + .5, false, "no turn sweeps only the slop"],
        ];
        let pass = 0;
        for(const [f0, f1, b, want, what] of C){ const got = whipSwept(f0, f1, b);
          if(got === want) pass++;
          else bad.push(`THE ARC MATH IS WRONG: whipSwept(${f0}, ${f1}, ${b.toFixed(3)}) is ${got}, wanted ${want} - ${what}`); }
        out.swept = `${pass}/${C.length}`;
        const nSt = Math.max(...CHARS.map(ch => Math.max(1, (ch.st || []).length)));
        const rr = []; for(let s = 0; s < nSt; s++) rr.push(+whipReach(s).toFixed(3));
        if(Math.abs(whipReach(0) - WHIP_R0) > 1e-9) bad.push(`A HATCHLING'S LASH IS NOT WHIP_R0: whipReach(0) ${whipReach(0)}, WHIP_R0 ${WHIP_R0}`);
        for(let s = 1; s < rr.length; s++) if(!(rr[s] > rr[s-1])) bad.push(`THE LASH DOES NOT REACH FURTHER ON A LATER FORM: ${rr.join(" / ")} m by stage`);
        out.reach = rr;
      }
      // 3. THE LASH, staged: the real whipMaybe on two headings. Six bodies round
      // you: three the tail sweeps through inside whipReach(stage) (mid, wide,
      // and one at the rim of the reach), three it must not touch (on the arc's
      // line but past the reach; behind the tail's start past the slop; on the
      // head's side of the turn).
      const HIT = ["mid", "wide", "edge"], MISS = ["far", "behind", "ahead"];
      const WHY = { far:"past the reach", behind:"behind the tail's start", ahead:"on the head's side" };
      const lash = (o)=>{
        const c = Object.assign({ on:true, whip:true, kit:true, f0:.4, turn:2.4, spd:1, gap:0, rest:false, idle:false, boss:false }, o || {});
        clear(); T = ks.T;
        MUT_ON = c.on; WHIP_ON = c.whip;
        if(c.kit) P.kit.tail = TAILK(); else delete P.kit.tail;
        const f0 = c.f0, f1 = f0 + c.turn, turn = wrapAng(f1 - f0), sd = Math.sign(turn) || 1, from = f0 + PI, r = whipReach(stage);
        const B = { mid:put(from + turn / 2, 1.6, c.boss), wide:put(from + turn * .85, 2.6), edge:put(from + turn * .3, ()=>r - .3),
                    far:put(from + turn / 2, e => r + e.rad + .6), behind:put(from - sd * (SL + .45), 1.6), ahead:put(f0 + turn / 2, 1.6) };
        rebuildGrid();
        P.whipH = []; P.whipCd = 0;
        const n0 = whipN, h0 = whipHit, d0 = dmgWhip;
        const go = (m)=>{ P.vx = Math.sin(f1) * P.spd * m; P.vz = Math.cos(f1) * P.spd * m; };
        const still0 = c.rest || c.idle;
        P.idle = still0 ? 1 : 0; go(still0 ? 0 : c.spd); P.faceWant = f0; whipMaybe(1/60);
        T += c.gap;
        P.idle = c.idle ? 1 : 0; go(c.idle ? 0 : c.spd); P.faceWant = f1;
        const ret = whipMaybe(1/60);
        const X = { lashes:whipN - n0, ret, hits:whipHit - h0, dmg:dmgWhip - d0, swing:swings.find(s => s.tail) || null, B, f0, f1, turn, r, row:{} };
        for(const k in B){ const e = B[k];
          X.row[k] = e ? { hit:e.hp < 1e9, push:e.kx * (e.x - P.x) + e.kz * (e.z - P.z), wu:e.wu, wd:e.wd, lg:e.lg } : null; }
        return X;
      };
      const untouched = q => !q || (!q.hit && q.push === 0 && q.wu === .5 && q.wd === .3);
      const judge = (X, what, hit)=>{
        const f = [], miss = Object.keys(X.row).filter(k => !hit.includes(k));
        if(X.lashes !== 1) f.push(`lashes ${X.lashes}, wanted 1`);
        for(const k of hit){ const q = X.row[k];
          if(!q){ f.push(`the body ${k} could not be staged`); continue; }
          if(!q.hit){ f.push(`the body ${k}, inside the arc and the reach, was not hit`); continue; }
          if(!(q.push > 0)) f.push(`${k} was not thrown clear (shove along the line out ${q.push.toFixed(3)})`);
          if(q.wu !== 0 || q.wd !== 0) f.push(`${k} still bites (wind-up ${q.wu}, wait ${q.wd}, not knocked out)`);
          if(!(q.lg >= WHIP_DAZE)) f.push(`${k} is not held off its next bite (lg ${q.lg}, WHIP_DAZE ${WHIP_DAZE})`); }
        for(const k of miss){ const q = X.row[k];
          if(!untouched(q)) f.push(`the body ${k} (${WHY[k] || "a boss"}) was touched: hit ${q.hit}, shove ${q.push.toFixed(3)}, wind-up ${q.wu}`); }
        if(X.ret !== hit.length || X.hits !== hit.length) f.push(`the tally is not the sweep: whipMaybe returned ${X.ret}, whipHit rose ${X.hits}, ${hit.length} bodies were in it`);
        if(hit.length && !(X.dmg > 0)) f.push(`dmgWhip did not rise (${X.dmg})`);
        if(f.length) bad.push(`${what}: ${f.join("; ")}`);
        return !f.length;
      };
      // the claim and its controls: each must lash, and hit exactly the three
      const A = lash();
      judge(A, "A HARD TURN WHILE MOVING DOES NOT LASH AS IT SHOULD", HIT);
      const ctrl = [["A HARD LEFT TURN DOES NOT LASH AS IT SHOULD", { turn:-2.4 }],
                    ["A HARD TURN ACROSS THE +-PI SEAM DOES NOT LASH AS IT SHOULD", { f0:2.9 }],
                    [`A TURN JUST PAST WHIP_TURN (${WHIP_TURN}) DOES NOT LASH`, { turn:WHIP_TURN + .04 }],
                    [`MOVING JUST PAST WHIP_MOVE (${WHIP_MOVE} of your speed) DOES NOT LASH`, { spd:WHIP_MOVE + .1 }],
                    [`A TURN JUST INSIDE WHIP_WIN (${WHIP_WIN} s) DOES NOT LASH`, { gap:WHIP_WIN - .03 }]];
      let ctrlOk = 0; for(const [msg, c] of ctrl) if(judge(lash(c), msg, HIT)) ctrlOk++;
      // the nulls: each guard alone, everything else as in the claim - no lash, nothing touched
      const nulls = [["THE CARD'S OWN SWITCH (WHIP_ON) DOES NOT STOP THE LASH", { whip:false }],
                     ["THE FAMILY SWITCH (MUT_ON) DOES NOT STOP THE LASH", { on:false }],
                     ["IT LASHES WITHOUT THE CARD", { kit:false }],
                     ["IT LASHES STANDING STILL", { idle:true }],
                     ["IT LASHES STANDING STILL WITH THE STICK HELD (not idle, not moving)", { spd:0 }],
                     ["A START FROM REST IS TAKEN FOR A TURN", { rest:true }],
                     [`IT LASHES MOVING SLOWER THAN WHIP_MOVE (${WHIP_MOVE} of your speed)`, { spd:WHIP_MOVE - .15 }],
                     [`IT LASHES A TURN SHORT OF WHIP_TURN (${WHIP_TURN} rad)`, { turn:WHIP_TURN - .04 }],
                     [`IT LASHES A TURN SLOWER THAN WHIP_WIN (${WHIP_WIN} s)`, { gap:WHIP_WIN + .03 }]];
      let nullOk = 0;
      for(const [msg, c] of nulls){ const X = lash(c);
        if(X.lashes === 0 && X.hits === 0 && Object.values(X.row).every(untouched)) nullOk++;
        else bad.push(`${msg}: lashes ${X.lashes}, bodies hit ${Object.keys(X.row).filter(k => X.row[k] && X.row[k].hit).join(",") || "none"}`); }
      // a boss is never bonked - and the same sweep still takes the rest (the null)
      const Bo = lash({ boss:true });
      if(!untouched(Bo.row.mid)) bad.push(`IT LASHES A BOSS: the boss in the middle of the sweep was hit ${Bo.row.mid.hit}, shoved ${Bo.row.mid.push.toFixed(3)}, wind-up ${Bo.row.mid.wu}`);
      judge(Bo, "BOSS CLAUSE NULL - THE SWEEP THAT SPARED THE BOSS DID NOT TAKE THE REST EITHER", ["wide", "edge"]);
      out.lash = { lashes:A.lashes, hits:A.hits, dmg:+A.dmg.toFixed(1), r:+A.r.toFixed(2), stage, ctrl:`${ctrlOk}/${ctrl.length}` };
      out.nulls = `${nullOk}/${nulls.length}`;
      out.boss = { spared:untouched(Bo.row.mid), rest:Bo.hits };
      // the sweep drawn is the sweep that hit: the swing it pushes, and drawLash's
      // plates on it, stay inside the arc and the reach that did the hitting and
      // cover both ends of it
      {
        const S = A.swing, sd = Math.sign(A.turn) || 1;
        if(!S) bad.push("THE LASH IS NOT DRAWN: no tail sweep on the swings list");
        else {
          if(Math.abs(wrapAng(S.ang - (A.f0 + PI + A.turn / 2))) > 1e-9 || Math.abs(S.arc - (Math.abs(A.turn) + 2 * SL)) > 1e-9
             || Math.abs(S.rng - A.r) > 1e-9 || S.dir !== sd)
            bad.push(`THE DRAWN SWEEP IS NOT THE ONE THAT HIT: ang ${S.ang.toFixed(3)} arc ${S.arc.toFixed(3)} rng ${S.rng} dir ${S.dir}, the lash turned ${A.turn.toFixed(3)} from ${A.f0} out to ${A.r}`);
          const vn0 = vn, nb0 = nbox, wc0 = wCap, bp0 = boxPx; let cap = [];
          try { vn = 0; nbox = 0; boxPx = 0; wCap = []; drawLash(Object.assign({}, S, { life:S.max * .02 })); cap = wCap; }
          finally { vn = vn0; nbox = nb0; wCap = wc0; boxPx = bp0; }
          let lo = 1e9, hi = -1e9, rmax = 0, stray = 0;
          for(let i = 0; i < cap.length; i += 6){
            const dx = cap[i] - S.x, dz = cap[i+2] - S.z, u = wrapAng(Math.atan2(dx, dz) - (A.f0 + PI)) * sd, rr = Math.hypot(dx, dz);
            lo = Math.min(lo, u); hi = Math.max(hi, u); rmax = Math.max(rmax, rr);
            if(u < -SL - 1e-6 || u > Math.abs(A.turn) + SL + 1e-6 || rr > S.rng + 1e-6) stray++; }
          if(!cap.length) bad.push("THE LASH DRAWS NOTHING: drawLash put no plate down on a full sweep");
          else {
            if(stray) bad.push(`THE DRAWN LASH LEAVES THE ARC THAT HIT: ${stray} of ${cap.length / 6} plates outside it`);
            if(!(lo < -SL + .05 && hi > Math.abs(A.turn) + SL - .05 && rmax > S.rng - 1e-3))
              bad.push(`THE DRAWN LASH DOES NOT COVER THE ARC THAT HIT: plates span ${lo.toFixed(3)}..${hi.toFixed(3)} rad of ${(-SL).toFixed(3)}..${(Math.abs(A.turn) + SL).toFixed(3)}, out to ${rmax.toFixed(2)} of ${S.rng.toFixed(2)} m`);
          }
          out.lash.plates = cap.length / 6;
        }
      }
      // 4. ONE TURN, ONE LASH; THE COOLDOWN HOLDS.
      // (a) the history restarts at the lash: with the cooldown cleared by hand,
      // holding the new heading does not lash again - and the null: a turn back
      // from there does.
      {
        const X = lash(); P.whipCd = 0; const n0 = whipN;
        whipMaybe(1/60); const twice = whipN - n0;
        P.faceWant = X.f0; whipMaybe(1/60); const back = whipN - n0 - twice;
        if(twice) bad.push(`ONE TURN LASHED TWICE: with the cooldown cleared, holding the new heading lashed ${twice} more - the history did not restart at the lash`);
        if(back !== 1) bad.push(`RESTART NULL: a turn straight back after it lashed ${back} times, wanted 1 - the clause above sees nothing`);
        // (b) the cooldown: the turn straight back, held with the clock stopped (so
        // the turn stays inside WHIP_WIN and only the cooldown can hold it) - no lash
        // for WHIP_CD less a margin, then exactly one, and the body is bonked only then
        const Y = lash(), e = Y.B.mid, nIn = Math.floor((WHIP_CD - .05) * 60);
        let early = 0, late = -1; const hp1 = e ? e.hp : 0;
        P.faceWant = Y.f0;
        for(let i = 0; i < nIn; i++){ const m = whipN; whipMaybe(1/60); early += whipN - m; }
        const hpIn = e ? e.hp : 0;
        for(let i = 0; i < 12 && late < 0; i++){ const m = whipN; whipMaybe(1/60); if(whipN > m) late = nIn + i + 1; }
        if(early) bad.push(`THE COOLDOWN DOES NOT HOLD: ${early} more lashes inside WHIP_CD (${WHIP_CD} s) off the turn straight back`);
        if(e && hpIn !== hp1) bad.push("THE COOLDOWN DOES NOT HOLD: the body was bonked again inside WHIP_CD");
        if(late < 0 && !early) bad.push(`COOLDOWN NULL: the same turn back never lashed after WHIP_CD either (${(nIn + 12) / 60} s) - the clause above sees nothing`);
        else if(e && !(e.hp < hpIn)) bad.push("COOLDOWN NULL: the lash after WHIP_CD did not bonk the body in the arc");
        out.cd = { held:+(nIn / 60).toFixed(3), early, lashedAt:late < 0 ? null : +(late / 60).toFixed(3), twice, back };
      }
      // 5. THE CLUB, on the real body, every form: grown with the card; not with
      // MUT_ON off, not with WHIP_ON off, never on THE SPLIT's second creature; and
      // on the body - every box of it touches the body or a box that does.
      T = ks.T; MUT_ON = true; WHIP_ON = true;
      {
        const mesh = (ch, st, kit, twin)=>{
          const sp = { x:0, y:0, z:0, face:0, iframe:0, hopFx:0, air:false, portrait:true, rush:0,
                       mscale:1, kit, surge:0, surgeT:0, legSpan:null, headSpan:null };
          if(twin) sp.twinOf = {};
          const an = { ph:0, amp:0, lean:0, bank:0, sq:1, lunge:0, look:0, land:0,
                       hit:0, hitR:0, hitF:-1, br:0, dead:0, atkT:9, atkKind:"", atkDir:0, atkSide:1, atkAmp:1 };
          const cP = bodyPos, cC = bodyCap; let o;
          for(let i = 0; i < 2; i++){ bodyPos = []; bodyCap = null; drawMonBody(ch, sp, an, st, 0, T); o = bodyPos; }
          bodyPos = cP; bodyCap = cC; vn = 0; nbox = 0;
          return o;
        };
        const same = (a, b)=> a.length === b.length && a.every((v, i)=>Math.abs(v - b[i]) < 1e-9);
        const grownBy = (a, b)=>{ const k = (x, i)=>x.slice(i, i + 6).map(v=>v.toFixed(6)).join(","), have = new Set();
          for(let i = 0; i < a.length; i += 6) have.add(k(a, i));
          const g = []; for(let i = 0; i < b.length; i += 6) if(!have.has(k(b, i))) g.push(...b.slice(i, i + 6)); return g; };
        // bodyPos is (lateral, fore-aft, vertical, hx, hz, hy): the same order for
        // position and half-extent, so axis k pairs with k + 3
        const touch = (a, i, b, j)=> Math.abs(a[i] - b[j]) <= a[i+3] + b[j+3] + 1e-3
                                  && Math.abs(a[i+1] - b[j+1]) <= a[i+4] + b[j+4] + 1e-3
                                  && Math.abs(a[i+2] - b[j+2]) <= a[i+5] + b[j+5] + 1e-3;
        const tk = { tail:TAILK() };
        let grew = 0, forms = 0; const floating = [];
        for(const ch of CHARS){
          const nS = Math.max(1, (ch.st || []).length);
          for(let st = 0; st < nS; st++){
            forms++; const id = `${ch.id}/${st}`;
            const A0 = mesh(ch, st, {}), A1 = mesh(ch, st, tk), AT = mesh(ch, st, tk, true), AT0 = mesh(ch, st, {}, true);
            MUT_ON = false; const AO = mesh(ch, st, tk); MUT_ON = true;
            WHIP_ON = false; const AW = mesh(ch, st, tk); WHIP_ON = true;
            if(same(A0, A1)){ bad.push(`THE CLUB DOES NOT GROW on ${id}`); continue; }
            grew++;
            if(!same(A0, AO)) bad.push(`THE FAMILY SWITCH (MUT_ON) LEAVES THE CLUB ON ${id}`);
            if(!same(A0, AW)) bad.push(`THE CARD'S OWN SWITCH (WHIP_ON) LEAVES THE CLUB ON ${id}`);
            if(!same(AT0, AT)) bad.push(`THE SPLIT'S SECOND CREATURE GROWS THE CLUB on ${id} - the twin is not the mutation's`);
            const G = grownBy(A0, A1), nG = G.length / 6, on = new Array(nG).fill(false);
            for(let i = 0; i < nG; i++) for(let j = 0; j < A0.length; j += 6) if(touch(G, i * 6, A0, j)){ on[i] = true; break; }
            for(let pass = 0; pass < nG; pass++) for(let i = 0; i < nG; i++) if(!on[i])
              for(let j = 0; j < nG; j++) if(on[j] && touch(G, i * 6, G, j * 6)){ on[i] = true; break; }
            const loose = on.filter(x => !x).length;
            if(!nG || loose) floating.push(`${id} (${loose} of ${nG} boxes)`);
          }
        }
        if(floating.length) bad.push(`THE CLUB FLOATS OFF THE BODY: ${floating.join(", ")}`);
        out.club = `${grew}/${forms}`;
      }
      // 6. AT THE CONTROLS, through the real step(): W held, the camera swung by
      // the turn between two frames - the heading the lash reads is the one the
      // controls set - with a body where the tail will pass. The kit is the card
      // alone (no weapon can touch the body), the field and the director are off;
      // counted on whipN/whipHit, which only the lash moves. The null: WHIP_ON off.
      {
        clear(); noSpawn = true; botDrive = false;
        ev0 = events.splice(0);
        lived = true; qaLive(bad, "THE WHIPTAIL GATE");
        qaArm(killR, killRN); armed = true;
        const drive = (whip)=>{
          clear(); T = ks.T; MUT_ON = true; WHIP_ON = whip;
          P.kit = { tail:TAILK() };
          P.x = kPrim.x; P.z = kPrim.z; P.air = false; P.fly = false; P.y = groundY(P.x, P.z); P.vy = 0; P.iframe = 0; P.hp = P.maxhp;
          P.whipH = []; P.whipCd = 0;
          const a0 = ks.cam, a1 = a0 + 2.4;
          camYaw = a0; keys.KeyW = true; P.vx = Math.sin(a0) * P.spd; P.vz = Math.cos(a0) * P.spd;
          const n0 = whipN, h0 = whipHit;
          step(1/60);
          const w0 = P.faceWant;
          put(w0 + PI + 1.2, 1.8); rebuildGrid();
          camYaw = a1; step(1/60);
          const w1 = P.faceWant, cd1 = P.whipCd; step(1/60); const cd2 = P.whipCd;
          keys.KeyW = false; camYaw = ks.cam;
          return { lashes:whipN - n0, hits:whipHit - h0, cd1, cd2, turn:+wrapAng(w1 - w0).toFixed(3), v:+(Math.hypot(P.vx, P.vz) / P.spd).toFixed(2) };
        };
        const ON = drive(true), OFF = drive(false);
        if(!(Math.abs(ON.turn) >= WHIP_TURN && Math.abs(OFF.turn) >= WHIP_TURN))
          bad.push(`CLAUSE 6 PREMISE: the controls did not turn the heading by WHIP_TURN between two frames (${ON.turn}, ${OFF.turn} rad)`);
        if(ON.lashes !== 1 || !(ON.hits >= 1)) bad.push(`A HARD TURN AT THE CONTROLS DOES NOT LASH: through step() it lashed ${ON.lashes} times and hit ${ON.hits} (turned ${ON.turn} rad at ${ON.v} of your speed) - whipMaybe is not wired into the frame`);
        if(OFF.lashes || OFF.hits) bad.push(`THE CARD'S OWN SWITCH DOES NOT STOP A LASH AT THE CONTROLS: ${OFF.lashes} lashes, ${OFF.hits} hits through step()`);
        if(ON.lashes === 1 && !(Math.abs(ON.cd1 - WHIP_CD) < 1e-9 && Math.abs(ON.cd2 - (WHIP_CD - 1/60)) < 1e-9))
          bad.push(`THE COOLDOWN DOES NOT RUN AT THE CONTROLS: through step() it read ${ON.cd1} on the lash frame and ${ON.cd2} one frame on, wanted ${WHIP_CD} then ${(WHIP_CD - 1/60).toFixed(4)}`);
        out.controls = { on:ON, off:OFF };
      }
    } catch(err){
      bad.push(`THE WHIPTAIL GATE THREW: ${err && err.message || err}`);
    } finally {
      // ---- put it all back
      for(const k in arrs){ arrs[k].length = 0; for(const x of kArr[k]) arrs[k].push(x); }
      if(ev0){ events.length = 0; events.push(...ev0); }
      P.kit = kKit; for(const k of Object.keys(P.kit)) if(!(k in kKitC)) delete P.kit[k]; Object.assign(P.kit, kKitC);
      P.banned = kBan;
      for(const k of Object.keys(P)) if(!(k in kPrim) && (P[k] === null || typeof P[k] !== "object")) delete P[k];
      Object.assign(P, kPrim);
      if(hadH) P.whipH = kH; else delete P.whipH;
      MUT_ON = ks.on; WHIP_ON = ks.whip; whipGive = ks.give; noRules = ks.nr; T = ks.T;
      whipN = ks.n; whipHit = ks.hit; dmgWhip = ks.dmg; dmgDealt = ks.dealt; dmgBoss = ks.dboss;
      shake = ks.shake; flash = ks.flash; R = ks.R; noSpawn = ks.ns; botDrive = ks.bd; camYaw = ks.cam; camAnchor = ks.anchor;
      if(ks.hadW) keys.KeyW = ks.keyW; else delete keys.KeyW;
      for(const k in hordeFlow) hordeFlow[k] = ks.flow[k];
      { const h = JSON.parse(ks.hl); for(const k in h) hurtLog[k] = h[k]; }
      if(armed) qaArm(null);
      rebuildGrid();
      if(lived) qaSettle();
    }
    return { ok:!bad.length, bad, ...out, switch:WHIP_ON, family:MUT_ON, ms:Date.now() - ms0 };
  }),
})
