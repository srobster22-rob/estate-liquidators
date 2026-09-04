// Mutation audit. A passing suite proves nothing unless it FAILS when the game
// is broken - and this one has already been caught twice passing against
// something other than what it claimed to measure (a lost WebGL context still
// showing its last frame, and a world that was frozen by accident).
//
// Each mutation below breaks one thing on purpose and names the section that
// must notice. A mutation that the suite survives is a section that is not
// testing what its name says.
//
//   node mutate.js            # run them all
//   node mutate.js reach      # just the ones whose id contains "reach"
const fs = require("fs"), path = require("path"), { execFileSync } = require("child_process");
const SRC = path.resolve(__dirname, "index.html");
const src = fs.readFileSync(SRC, "utf8");

const MUTANTS = [
  { id:"reach-to-centre", must:"7g",
    why:"weapons measure to the centre again, so a 4m body eats 4m of reach",
    from:"const dx=e.x-x, dz=e.z-z, reach=r+e.rad;",
    to:  "const dx=e.x-x, dz=e.z-z, reach=r;" },
  { id:"burn-uncapped", must:"7h",
    why:"overlapping hazards stack without limit again",
    from:"const BURN_STACK = 3;", to:"const BURN_STACK = 9999;" },
  { id:"scrapper-reach", must:"7i",
    why:"THE SCRAPPER loses the reach stat and nothing else changes",
    from:"mods:{ mag:1.7, spd:1.10, hp:.85, reach:1.35 } },",
    to:  "mods:{ mag:1.7, spd:1.10, hp:.85 } }," },
  { id:"context-loss-ignored", must:"12c",
    why:"the lost context is never claimed back, which is the shipped default",
    from:"  e.preventDefault();\n  ctxLost = true;", to:"  ctxLost = true;" },
  { id:"drag-look-dead", must:"15c",
    why:"mouse-look is gated on pointer lock again, freezing an embed's camera",
    from:"  if(document.pointerLockElement!==cv && !dragging) return;",
    to:  "  if(document.pointerLockElement!==cv) return;" },
  { id:"shake-always-on", must:"16",
    why:"reduced motion is accepted and then ignored",
    from:"const shakeMul = ()=> save.motion ? 1 : 0;",
    to:  "const shakeMul = ()=> 1;" },
  // First written against the X line alone, which the suite survived - and the
  // test was right: the stick drag it uses is purely vertical, so X was never
  // the axis under measurement. An incomplete mutation is a false alarm, the
  // same failure mode in the other direction.
  // Re-pointed once already: the movement rewrite deleted the two lines this
  // used to target, and the harness reported SKIP. SKIP is counted as NOT
  // caught on purpose - a mutation whose anchor has drifted is a hole in the
  // audit that looks like a pass, and looking like a pass is the whole failure
  // mode this file exists to catch.
  // Re-pointed a second time, by bunnyhopping this time. Same lesson: an
  // anchor is a copy of a line of source, and every line of source is somebody
  // else's next edit.
  { id:"analog-ignored", must:"15",
    why:"the stick goes back to on/off, throwing away partial deflection",
    from:"  const wx = dx*P.spd*hm*analog, wz = dz*P.spd*hm*analog;",
    to:  "  const wx = dx*P.spd*hm, wz = dz*P.spd*hm;" },
  { id:"ladder-early", must:"17",
    why:"every rung pays out immediately, whatever the number says",
    from:"if(u.now(save, runStats) >= u.at)", to:"if(u.now(save, runStats) >= 0)" },
  { id:"ladder-repeats", must:"17",
    why:"a rung pays out again every single run",
    from:"    if(save.unlocked[u.id]) continue;\n", to:"" },
  { id:"shop-lock-ignored", must:"17",
    why:"the locked shop line is on sale from run one",
    from:"    if(u.lock && !save.unlocked[u.lock]) continue;      // not earned yet\n", to:"" },
  { id:"xpmul-ignored", must:"17",
    why:"THE ACCOUNTANT's whole identity silently does nothing",
    from:"  const got = v * (P.xpMul||1) * (P ? (biomeAt(P.x,P.z).mod.xp || 1) : 1);",
    to:  "  const got = v;" },
  { id:"camera-welded", must:"12d",
    why:"the boom goes back to being welded to the player",
    from:"  camAnchor[0] = lerp(camAnchor[0], px, kf);", to:"  camAnchor[0] = px;" },
  { id:"cache-never-opens", must:"18",
    why:"walking into a cache does nothing at all",
    from:"      if(near){\n        events.splice(i,1);", to:"      if(false){\n        events.splice(i,1);" },
  { id:"altar-charges-anywhere", must:"18",
    why:"the altar charges whether you are standing in it or not",
    from:"      e.chg = clamp(e.chg + (near ? dt : -dt*.32), 0, d.hold);",
    to:  "      e.chg = clamp(e.chg + dt, 0, d.hold);" },
  { id:"boon-not-durable", must:"18",
    why:"boons are written onto P and evaporate at the next passive pick",
    from:"  return Math.max(.58, 1*(m.cd||1)*(1-rank(\"cd\")*.035) * boonMul.cd",
    to:  "  return Math.max(.58, 1*(m.cd||1)*(1-rank(\"cd\")*.035)" },
  { id:"collector-charges", must:"18",
    why:"the collector walks at you like everything else, so there is no hunt",
    from:"    if(e.def.flee){", to:"    if(false){" },
  { id:"collector-never-rests", must:"18",
    why:"it never pauses, which is a treadmill rather than a chase",
    from:"      if(e.rest <= 0){ e.flash = Math.max(e.flash, .08); walk(e, lx, lz, dt); continue; }",
    to:  "" },
  { id:"hop-window-open", must:"19",
    why:"any jump chains, so the timing window is not a window",
    from:"      if(P.hopWin > 0){            // landed and jumped again inside the window",
    to:  "      if(true){                    // landed and jumped again inside the window" },
  { id:"hop-no-speed", must:"19",
    why:"the chain counts up and buys nothing",
    from:"const hopMul = ()=> 1 + HOP_TOP * (1 - Math.pow(HOP_FALL, P ? P.hop : 0));",
    to:  "const hopMul = ()=> 1;" },
  { id:"hop-caps-early", must:"19",
    why:"the chain stops paying after a few links, which is what a hard cap did",
    from:"const HOP_WIN = .16, HOP_BUF = .14, HOP_MAX = 24,",
    to:  "const HOP_WIN = .16, HOP_BUF = .14, HOP_MAX = 3," },
  { id:"hop-never-bleeds", must:"19",
    why:"a chain earned once is a chain kept forever",
    from:"    else if(P.hop > 0) P.hop = Math.max(0, P.hop - (HOP_BLEED + P.hop*.55)*dt);", to:"" },
  { id:"hop-autohop", must:"19",
    why:"a held spacebar hops for you, which is free top speed for twenty minutes",
    from:"  if(e.code===\"Space\" && !e.repeat && running && !paused) jumpPressed();",
    to:  "  if(e.code===\"Space\" && running && !paused) jumpPressed();" },
  { id:"jump-unbuffered", must:"19b",
    why:"the press has to land inside one 16ms frame or it is thrown away",
    from:"function jumpPressed(){ jumpBuf = HOP_BUF; }",
    to:  "function jumpPressed(){ jumpBuf = 1e-9; }" },
  { id:"wall-square-again", must:"20",
    why:"the boundary goes back to a square whose corners are past the wall",
    from:"  if(d2 <= lim*lim) return [x, z];\n  const s = lim / Math.sqrt(d2);\n  return [x*s, z*s];",
    to:  "  return [x, z];" },
  { id:"events-outside", must:"20",
    why:"side events spawn wherever the ring lands them, wall or no wall",
    from:"      [x, z] = confine(P.x + Math.sin(a)*r, P.z + Math.cos(a)*r, 6);",
    to:  "      x = P.x + Math.sin(a)*r; z = P.z + Math.cos(a)*r;" },
  { id:"no-evolution", must:"21",
    why:"monsters never evolve; the line is decoration",
    from:"  if(want > stage) evolveTo(want);", to:"" },
  { id:"evo-is-a-rename", must:"21",
    why:"the stage changes name and nothing else",
    from:"  const r = k => (to[k]||1)/(from[k]||1);", to:"  const r = k => 1;" },
  { id:"evo-overheals", must:"21",
    why:"evolving refills the bar instead of paying back what it added",
    from:"  P.hp = Math.min(P.maxhp, P.hp + Math.max(0, P.maxhp - before));",
    to:  "  P.hp = P.maxhp;" },
  { id:"mon-level-shared", must:"21",
    why:"every monster shares one XP pool, so raising one raises all of them",
    from:"function monBank(id){ return (save.mon && save.mon[id]) || 0; }",
    to:  "function monBank(id){ let t=0; for(const k in (save.mon||{})) t+=save.mon[k]; return t; }" },
  { id:"one-body-plan", must:"21b",
    why:"every species draws the same mesh again, which is what it looked like",
    from:"  (BODY[mCh.type] || BODY.plain)(D);",
    to:  "  BODY.plain(D);" },
  { id:"forms-dont-change", must:"21b",
    why:"a line's three stages are the same animal at three sizes",
    from:"  boxSeq = 0;",
    to:  "  boxSeq = 0; D.st = 0;" },
  { id:"one-arena", must:"23",
    why:"the map is generated once and never again, which is the backdrop it was",
    from:"  rollWorld(pinSeed === null ? undefined : pinSeed);\n  dealDens(); makeTerrain(); uploadTerrain(); bakeMap();",
    to:  "  " },
  { id:"spawn-anywhere", must:"23",
    why:"a run can open with you standing in the sludge",
    from:"  cells = [{ x:0, z:0, b:BIOME_BY.grass }];",
    to:  "  cells = [{ x:0, z:0, b:pool[0] }];" },
  { id:"regions-inert", must:"23b",
    why:"the ground you stand on stops meaning anything",
    // re-pointed by R223: airborne forms are exempt on the same line now
    from:"  const groundSpd = (sureFoot || up) ? 1 : (bmod.spd || 1);",
    to:  "  const groundSpd = 1;" },
  { id:"ashes-free", must:"23b",
    why:"standing in the ashes costs nothing",
    from:"  let d = raw * P.tough * (biomeAt(P.x,P.z).mod.tough || 1);",
    to:  "  let d = raw * P.tough;" },
  { id:"heirloom-unmarked", must:"7f",
    why:"the thing exempted from the ground check loses what it was exempted FOR",
    from:"  drawnMarks++;", to:"" },
  { id:"mon-level-inert", must:"21",
    why:"monster levels are a number on a card and nothing else",
    from:"const monHp  = id => 1 + (monLvl(id)-1)*.020;",
    to:  "const monHp  = id => 1;" },
  { id:"boss-body-dropped", must:"22",
    why:"spawnBoss stops carrying the body key, so all four render the fallback",
    from:"c:b.c, h:b.h, w:b.w, ai:b.ai, body:b.body, flier:!!b.flier };",
    to:  "c:b.c, h:b.h, w:b.w, ai:b.ai, flier:!!b.flier };" },
  { id:"boss-lod-pinned", must:"22",
    why:"a boss is drawn at full detail from any distance again",
    from:"const lod = e.boss ? (dp < 45 ? 2 : dp < 90 ? 1 : 0)",
    to:  "const lod = e.boss ? (2)" },
  { id:"fowl-marker-only", must:"22",
    why:"GLIMMERFOWL draws its ring and beam and then no bird",
    from:"    drawnMarks++;\n  }\n",
    to:  "    drawnMarks++;\n  }\n  if(W) return;\n" },
  { id:"rank-runs-past-three", must:"22b",
    why:"a rank can be pushed past three again, so the ceiling is not a ceiling",
    from:"for(let i=0;i<n && P.kit[k].l<WMAX-1;i++)",
    to:  "for(let i=0;i<n && P.kit[k].l<9;i++)" },
  { id:"rank-capped-low", must:"22b",
    why:"three ranks read lv[0..2], which is a two-rank nerf calling itself a UI change",
    from:"const RANKMAP = [0, 2, 4];", to:"const RANKMAP = [0, 1, 2];" },
  { id:"passive-scale-lost", must:"22b",
    why:"passives stop scaling for the missing ranks, costing a third of every one",
    from:"const PSCALE = 5 / WMAX;", to:"const PSCALE = 1;" },
  { id:"eye-unclamped", must:"12b",
    why:"the camera boom reaches past the wall again and the frame renders as fog",
    from:"  if(er > CAM_R){ const f = CAM_R/er; eye[0] *= f; eye[2] *= f; }",
    to:  "" },
  // The four below cover checks written in the last handful of rounds. Two of
  // those rounds ended with a check that passed against a broken build, so
  // every new section gets a mutation here the moment it is written, rather
  // than waiting for the next time something quietly stops measuring.
  { id:"hazard-hits-wider-than-drawn", must:"7c",
    why:"the damaged area is bigger than the marked one, so reading the tell " +
        "stops saving you and a telegraph becomes decoration",
    from:"Math.hypot(P.x-h.x, P.z-h.z) < h.r){",
    to:  "Math.hypot(P.x-h.x, P.z-h.z) < h.r*1.6){" },
  { id:"brood-unleashed", must:"30",
    why:"a hatchling can be walked off across the arena and never comes back, " +
        "which is the whole reason the leash is on the player and not the pet",
    from:"if(Math.hypot(p2.x-P.x, p2.z-P.z) > s.rng + 12){ p2.x = P.x; p2.z = P.z; }",
    to:  "if(false){ p2.x = P.x; p2.z = P.z; }" },
  { id:"brood-never-grows", must:"30",
    why:"the pack stays one animal at every rank, so five ranks buy nothing",
    from:"const s = wStat(w), n = Math.min(6, s.n + dupeN());",
    to:  "const s = wStat(w), n = 1;" },
  { id:"pets-walk-through-bosses", must:"30",
    why:"a pet crossing to a ring slot on the far side walks through the boss " +
        "and stands inside it, which draws a hatchling buried in the model",
    from:"      const keep = biting.rad + .35;", to:"      const keep = 0;" },
  { id:"pack-stacks", must:"30",
    why:"a pack's own animals stand inside each other again, so six hatchlings " +
        "render as fewer than six and the rank you bought is invisible",
    from:"const PET_SEP = 1.1;", to:"const PET_SEP = 0;" },
  { id:"tail-comes-off", must:"29",
    why:"a tapered chain stops clamping to its own neighbours, so tails and " +
        "limbs float free of the body that owns them",
    from:"cap(dr, hx); cap(df, hz); cap(dy, hy);",
    to:  "s = 1;" },
  { id:"thicket-reach-ignored", must:"23c",
    why:"THE THICKET stops shortening weapon reach, so the region does " +
        "nothing but change colour",
    from:"const reach = P.reach * (biomeAt(P.x, P.z).mod.reach || 1);",
    to:  "const reach = P.reach;" },
  { id:"final-form-unreachable", must:"22n",
    why:"EVO_AT loses its fifth entry, so the final form exists in the data " +
        "but no run can ever reach it by levelling",
    from:"const EVO_AT = [1, 7, 20, 34, 48];",
    to:  "const EVO_AT = [1, 7, 20, 34];" },
  { id:"warren-swarm-ignored", must:"23d",
    why:"THE WARRENS stops speeding up the director, so the region does " +
        "nothing but change colour",
    from:"nextSpawn = 1/(ph.rate * (bio.mod.swarm || 1)",
    to:  "nextSpawn = 1/(ph.rate * 1" },
  { id:"spring-regen-ignored", must:"23e",
    why:"THE HOTSPRINGS stops multiplying regeneration, so the tenth region " +
        "does nothing but change colour",
    from:"P.hp = Math.min(P.maxhp, P.hp + P.regen*dt * (bmod.regen || 1));",
    to:  "P.hp = Math.min(P.maxhp, P.hp + P.regen*dt);" },
  { id:"mosshide-inert", must:"18",
    why:"MOSSHIDE stops adding regeneration, so the eighth boon is a card " +
        "that says a thing and does nothing",
    from:'{ nm:"MOSSHIDE",    ds:"+1.1/s regeneration",\n    fn:()=>{ P.regen += 1.1; } },',
    to:  '{ nm:"MOSSHIDE",    ds:"+1.1/s regeneration",\n    fn:()=>{} },' },
  { id:"thermals-window-ignored", must:"18",
    why:"the landing keeps issuing the stock window, so THERMALS does nothing",
    from:"                     P.hopWin = HOP_WIN * (boonMul.hopWin || 1); P.hopGrace = HOP_GRACE;",
    to:  "                     P.hopWin = HOP_WIN; P.hopGrace = HOP_GRACE;" },
  { id:"pearl-uncounted", must:"22m",
    why:"a pearl taken never reaches the run's receipt, so the end screen " +
        "under-reports the one treasure the lakes grow",
    from:"      if(g.pearl) runPearls++;",
    to:  "" },
  { id:"den-ledger-immortal", must:"22m",
    why:"denStats goes back to never resetting, so every end screen after " +
        "the first over-reports what the run explored",
    from:"  denStats.woke = 0; denStats.cleared = 0;",
    to:  "" },
  { id:"pearl-splash-silent", must:"22m",
    why:"the pearl surfaces without a sound, which is the exact silent-ship " +
        "failure the sound ledger exists to catch",
    from:"  SFX.pearl();",
    to:  "" },
  { id:"pearls-never-surface", must:"23h",
    why:"the pearl tick finds its lake and then drops nothing, so lakes go " +
        "back to being water you walk around",
    from:"  const px2 = L.x + rnd(-2, 2), pz2 = L.z + rnd(-2, 2);\n  pushGem(px2, pz2, Math.round(rnd(24, 34)));",
    to:  "  const px2 = L.x + rnd(-2, 2), pz2 = L.z + rnd(-2, 2);" },
  { id:"upwelling-dry", must:"23g",
    why:"the upwelling's tick stops dropping anything, so the fourth event " +
        "is a green ring around ordinary ground",
    from:"        hazards.push(mkHaz(e.x + Math.cos(a2)*rr, e.z + Math.sin(a2)*rr,\n                           2.1, .75, .30, 14*dmgScale(T)));\n        const ga = R()*TAU, gr2 = Math.sqrt(R())*d.r*.9;\n        pushGem(e.x + Math.cos(ga)*gr2, e.z + Math.sin(ga)*gr2, 4);",
    to:  "" },
  { id:"angry-den-tame", must:"23f",
    why:"an angry den wakes its pack on the plain den numbers, so the red " +
        "ember advertises a fight that never shows up",
    from:"    if(m.angry){\n      e.elite = true; e.sz *= ELITE.sz; e.rad *= ELITE.sz;\n      e.xp *= ELITE.xp; e.spdMul *= ELITE.spd; e.dmg *= ELITE.dmg;\n      e.hp = e.maxhp = e.maxhp * ELITE.hp;\n    }\n    else e.hp = e.maxhp = e.maxhp * 1.25;",
    to:  "    e.hp = e.maxhp = e.maxhp * 1.25;" },
  { id:"massless-boss", must:"22v",
    why:"bosses take full weapon knockback again, so a shove-heavy kit " +
        "juggles the fight the run builds to at range forever",
    from:"  if(kx||kz){ const mass = e.boss ? .22 : e.elite ? .6 : 1;\n              e.kx += kx*mass; e.kz += kz*mass; }",
    to:  "  if(kx||kz){ e.kx += kx; e.kz += kz; }" },
  { id:"fauna-deaf", must:"23i",
    why:"the director stops hearing the ground's preferences - the warrens " +
        "and the glacier send the same mix again",
    from:"      let tot=0; for(const k of keysM) tot += ph.mix[k] * (fa[k] || 1);\n      let r = R()*tot, chosen = keysM[0];\n      for(const k of keysM){ r -= ph.mix[k] * (fa[k] || 1); if(r<=0){ chosen=k; break; } }",
    to:  "      let tot=0; for(const k of keysM) tot += ph.mix[k];\n      let r = R()*tot, chosen = keysM[0];\n      for(const k of keysM){ r -= ph.mix[k]; if(r<=0){ chosen=k; break; } }" },
  { id:"wipe-unarmed", must:"24",
    why:"WIPE SAVE goes back to firing on the first click - hours of unlocks " +
        "one stray tap from gone",
    from:"    if(dvW.dataset.armed){ wipeAll(); openMenu(); return; }",
    to:  "    { wipeAll(); openMenu(); return; }" },
  { id:"angry-article-kept", must:"23f",
    why:"the angry wake headline goes back to ANGRY THE TUSKS - the copy " +
        "defect in the run's loudest moment",
    from:"  alert2((m.angry ? \"ANGRY \" + K.nm.replace(/^THE /, \"\") : K.nm) + \" - \" + K.ds,",
    to:  "  alert2((m.angry ? \"ANGRY \" : \"\") + K.nm + \" - \" + K.ds," },
  { id:"shop-button-blind", must:"15",
    why:"the end screen's SHOP button opens the menu at the top again, the " +
        "shop somewhere below nine monster cards",
    from:"    const sh = document.getElementById(\"shop\");\n    if(sh) (sh.previousElementSibling || sh).scrollIntoView({ block:\"start\" });",
    to:  "" },
  { id:"pause-cheats-ungated", must:"24",
    why:"the pause screen's DEV strip shows for every player again - GODMODE " +
        "one accidental tap away on a phone",
    from:"  if(v) document.getElementById(\"dev\").classList.toggle(\"on\", !!save.dev);",
    to:  "  if(v) document.getElementById(\"dev\").classList.add(\"on\");" },
  { id:"gait-on-the-clock", must:"31",
    why:"gait time runs off the wall clock again, so a rooted spitter jogs on " +
        "the spot and a slowed animal strides at full tempo",
    from:"  e.gt += mv / nom;", to:"  e.gt += dt;" },
  { id:"stride-never-settles", must:"31",
    why:"stride amplitude is pinned at full, so stopping freezes the legs " +
        "mid-swing instead of settling them",
    from:"  e.amp += (clamp(v / nom, 0, 1) - e.amp) * Math.min(1, dt * 9);",
    to:  "  e.amp = 1;" },
  { id:"faces-you-always", must:"31",
    why:"the heading snaps back to the player every frame, so a backing " +
        "spitter walks backwards and a turn happens inside one frame",
    from:"  const turn = d * Math.min(1, dt * 7);\n  e.hd += turn;",
    to:  "  const turn = d;\n  e.hd = Math.atan2(px, pz);" },
  { id:"shove-is-a-walk", must:"31",
    why:"knockback is read as travel, so a bonked animal strides ten metres " +
        "of gait while it slides and turns to face the way it is flying",
    from:"    const lx = e.x, lz = e.z;\n\n    const dx = P.x-e.x",
    to:  "    let lx = e.x, lz = e.z;\n    lx -= e.kx*dt; lz -= e.kz*dt;\n\n    const dx = P.x-e.x" },
  { id:"no-flinch", must:"31",
    why:"a hit no longer squashes the animal, which is the binary width pop " +
        "with the pop removed - no hit tell in the body at all",
    from:"  e.sq = Math.min(e.sq, 1 - dip);", to:"" },
  { id:"no-bite", must:"31",
    why:"contact stops pitching the animal forward, so the horde's one " +
        "attack has no animation",
    from:"      e.lg = 1;                                     // the bite, see walk()",
    to:  "" },
  { id:"spitter-legs-near-only", must:"32",
    why:"DILOPHO's legs go back behind the close-range gate, so the one range " +
        "a spitter is ever seen from draws it with no legs again",
    from:"  for(const sg of [-1,1])\n    eleg(e, face, sg*W*.20, -W*.06, y0 + H*.38, H*.38, st*sg,\n" +
         "         Math.max(0, strideV(e, 7)*sg)*H*.06, W*.085, dk, lod);\n  if(lod < 2) return;",
    to:  "  if(lod < 2) return;\n  for(const sg of [-1,1])\n    eleg(e, face, sg*W*.20, -W*.06, y0 + H*.38, H*.38, st*sg,\n" +
         "         Math.max(0, strideV(e, 7)*sg)*H*.06, W*.085, dk, lod);" },
  { id:"feet-glued", must:"32",
    why:"the shin and foot no longer swing with the stride - only the thigh " +
        "does - so the feet stay together and the animal shuffles on the spot",
    from:"  const af = f + len*(k - .18) + sw*len*.44,", to:"  const af = f + len*(k - .18)," },
  { id:"foot-never-lifts", must:"32",
    why:"the swinging foot is dragged along the grass instead of lifted",
    // re-pointed by R222: the foot segment carries its lateral splay now
    from:"  seg(r + out, af, ay, r + out, af + len*.30, y - len + lift + th*.30, th*.62, col);  // foot",
    to:  "  seg(r + out, af, ay, r + out, af + len*.30, y - len + th*.30, th*.62, col);  // foot" },
  { id:"flinch-not-directional", must:"33",
    why:"the stagger no longer knows which side the blow came from - every " +
        "hit is the same crouch, so the body tells you nothing about where " +
        "the danger is",
    from:"                 + ANIM.hitR * hit * .34\n", to:"                 + 0 * hit * .34\n" },
  { id:"death-no-collapse", must:"33",
    why:"the legs never go - the dead animal stands at full height and only " +
        "shears, which reads as a glitch, not a fall",
    from:"  ANIM.sq += ((1 - settle * .56 + bounce) - ANIM.sq) * k;",
    to:  "  ANIM.sq += ((1 - settle * 0 + bounce) - ANIM.sq) * k;" },
  { id:"death-topple-toward-blow", must:"33",
    why:"the body falls INTO the blow instead of away from it - the fall " +
        "contradicts the hit it came from",
    from:"  ANIM.bank += (deathR * fall * .70 - ANIM.bank) * k;",
    to:  "  ANIM.bank += (-deathR * fall * .70 - ANIM.bank) * k;" },
  { id:"receipt-not-gated", must:"33",
    why:"the receipt is solid from the first frame of the beat again - the " +
        "fall happens behind a table nobody can see through",
    from:"  endFade(deathFx > 0 ? clamp((t - .66) / .48, 0, 1).toFixed(3) : \"\");",
    to:  "  endFade(deathFx > 0 ? \"1\" : \"\");" },
  { id:"beat-no-rearup", must:"34",
    why:"the slam's wind-up no longer stands the boss up - the tell is a lean " +
        "with no height in it, so the biggest hit in the game has the smallest " +
        "warning",
    from:"  slam:     { tsq: .16, tlf:-.18,", to:"  slam:     { tsq: 0, tlf:-.18," },
  { id:"beat-no-snap", must:"34",
    why:"the slam lands at full height - the wind-up releases into nothing, so " +
        "the hit has no weight and the hazard ring is once again the only thing " +
        "that moved",
    from:"  slam:     { tsq: .16, tlf:-.18, asq:-.28, alf: .26 },",
    to:  "  slam:     { tsq: .16, tlf:-.18, asq: 0, alf: .26 }," },
  { id:"arms-never-raise", must:"34",
    why:"THE MATRIARCH's forelimbs stay planted through the whole slam - the " +
        "body rears but the arms it is meant to come down on never leave the ground",
    from:"  const bt = e.bt || BT0, arm = bt.u * bt.u;", to:"  const bt = e.bt || BT0, arm = 0 * bt.u;" },
  { id:"beat-never-recovers", must:"34",
    why:"the ease-out never runs - the boss stays flattened in its landing pose " +
        "for the whole rest and walks at you that way",
    from:"    const k = clamp(1 - (ab.rest - A.t) / BEAT_REST, 0, 1);",
    to:  "    const k = clamp(1 - (ab.rest - A.t) / 1e9, 0, 1);" },
  { id:"beat-left-in-body", must:"34",
    why:"the draw no longer puts walk()'s squash back after the plan - the " +
        "beat compounds frame over frame and a paused boss shrinks into the ground",
    from:"    plan(e, face, W*sq, H, c, glow, lod, e.py);\n    e.sq = sq0;",
    to:  "    plan(e, face, W*sq, H, c, glow, lod, e.py);\n    e.sq = e.sq;" },
  // ---- R200: the horde falls down --------------------------------------
  { id:"no-corpse", must:"35",
    why:"a kill no longer puts the body on the corpse list - the horde is back " +
        "to vanishing on the frame it dies, a cut and not a death",
    // re-pointed by R221: the rush line now sits between kills++ and fell()
    from:"  fell(e);\n  if(e.denRef) denLost(e.denRef);", to:"  0;\n  if(e.denRef) denLost(e.denRef);" },
  { id:"corpse-drawn-twice", must:"35",
    why:"the live loop no longer skips the dead - a corpse is drawn standing by " +
        "the live pass AND falling by the corpse pass, two bodies for one kill",
    from:"    if(e.dead) continue;                 // on the corpse list now, drawn below",
    to:  "    if(false) continue;                  // on the corpse list now, drawn below" },
  { id:"corpse-never-goes", must:"35",
    why:"the fall never ends - the corpse list fills to the cap and stays full, " +
        "every body lying there forever",
    from:"    if(e.ft >= e.fd){ corpses.splice(i, 1); continue; }",
    to:  "    if(e.ft >= 1e9){ corpses.splice(i, 1); continue; }" },
  { id:"no-crumple", must:"35",
    why:"the squash is gone from the fall - the body leans, fades and sinks at " +
        "full height, a totem pole tipping into the ground",
    from:"  return { sq:   1 - .58*d + bounce,", to:"  return { sq:   1 - 0*d + bounce," },
  { id:"no-sink", must:"35",
    why:"the pivot never drops - the body lies on the grass in full view until " +
        "the list splices it, and then it vanishes in one frame",
    from:"    e.py = e.y + hop - dp.sink*H*1.15 - dp.drop*dp.sq*(e.fgap || 0);",
    to:  "    e.py = e.y + hop - dp.sink*H*0 - dp.drop*dp.sq*(e.fgap || 0);" },
  { id:"flier-dies-hovering", must:"35",
    why:"a flier keeps its hover through the fall - SKYSPLITTER crumples in the " +
        "air a metre and a half up and never touches the ground it is meant to hit",
    from:"    e.py = e.y + hop - dp.sink*H*1.15 - dp.drop*dp.sq*(e.fgap || 0);",
    to:  "    e.py = e.y + hop - dp.sink*H*1.15 - 0*dp.sq*(e.fgap || 0);" },
  { id:"boss-not-a-flier", must:"35",
    why:"the boss spawn drops the flier flag - SKYSPLITTER hops on a stride and " +
        "its corpse is not given the flier's drop out of the air",
    from:"                c:b.c, h:b.h, w:b.w, ai:b.ai, body:b.body, flier:!!b.flier };",
    to:  "                c:b.c, h:b.h, w:b.w, ai:b.ai, body:b.body, flier:false };" },
  { id:"last-boss-freezes", must:"35",
    why:"the world stops on the final kill and the corpse clock stops with it - " +
        "the last boss hangs at its kill frame over the end screen instead of falling",
    from:"  else if(over) stepCorpses(dt);", to:"  else if(false) stepCorpses(dt);" },
  { id:"corpse-pulls-back", must:"35",
    why:"the bite eases out of a corpse again - a boss killed mid-bite swings its " +
        "head metres back as it begins to fall",
    from:"    e.amp -= e.amp*Math.min(1, dt*6);",
    to:  "    e.amp -= e.amp*Math.min(1, dt*6); e.lg = Math.max(0, e.lg - dt*3.2);" },
  // ---- R201: every stage wears its own coat -----------------------------
  { id:"one-coat-per-line", must:"36",
    why:"the draw reads the hatchling's coat at every stage - five evolutions in " +
        "one paint again, the exact complaint the stage palettes answer",
    from:"  const mTy = monPal(mCh.type, stage);", to:"  const mTy = monPal(mCh.type, 0);" },
  { id:"table-ignored", must:"36",
    why:"monPal returns the line's palette whatever the stage - the table exists, " +
        "nothing is painted from it",
    from:"  const base = MTYPE[type] || MTYPE.plain, sp = (STAGEPAL[type] || [])[st|0];",
    to:  "  const base = MTYPE[type] || MTYPE.plain, sp = null;" },
  { id:"grey-legs-on-white", must:"36",
    why:"the pale-coat dark override is dropped - the SUPERNOVA, TEMPEST and the " +
        "bone fish stand on the same neutral grey, half of white",
    from:"  const mDk = mTy.dk ? wash(mTy.dk) : [mTc[0]*.52, mTc[1]*.52, mTc[2]*.52];",
    to:  "  const mDk = [mTc[0]*.52, mTc[1]*.52, mTc[2]*.52];" },
  { id:"stage-off-by-one", must:"36",
    why:"the coat lags the evolution by a stage - the FLAREDRAKE is still orange " +
        "and the final form wears the apex's paint",
    from:"  const mTy = monPal(mCh.type, stage);", to:"  const mTy = monPal(mCh.type, Math.max(0, stage-1));" },
  // ---- R202: the apex is a new shape ------------------------------------
  { id:"cinderstar-is-the-serpent", must:"37",
    why:"the CINDERSTAR branch is skipped and stage 3 falls through to the SUPERNOVA " +
        "plan - two of the intern's three top stages are one animal in two coats",
    from:"  } else if(st === 3){\n    // THE CINDERSTAR. THE VOLCANO STOOD UP.",
    to:  "  } else if(false){\n    // THE CINDERSTAR. THE VOLCANO STOOD UP." },
  // ---- R203: the tide's top two are other animals ------------------------
  { id:"maelstrom-is-the-leviathan", must:"37",
    why:"the ray-and-anglerfish branch is skipped and stages 3 and 4 fall through " +
        "to the plesiosaur plan - the top of the tide line is the LEVIATHAN in " +
        "two more coats",
    from:"  if(st >= 3){\n    const G = gr;\n    if(st === 3){\n      // THE MAELSTROM.",
    to:  "  if(false){\n    const G = gr;\n    if(st === 3){\n      // THE MAELSTROM." },
  // ---- R204: the volt line's top two are a wolf and a walking storm ------
  { id:"supercell-is-the-tyrant", must:"37",
    why:"the raiju-and-thunderhead branch is skipped and stages 3 and 4 fall " +
        "through to the tyrant plan - the top of the volt line is the " +
        "STORMTYRANT in two more coats",
    from:"  if(st >= 3){\n    const G = gr;\n    if(st === 3){\n      // THE SUPERCELL.",
    to:  "  if(false){\n    const G = gr;\n    if(st === 3){\n      // THE SUPERCELL." },
  // ---- R205: the stone line's top two are a tortoise and an island ------
  { id:"mountain-is-the-titanhide", must:"37",
    why:"the tortoise-and-island branch is skipped and stages 3 and 4 fall " +
        "through to the ceratopsian plan - the top of the stone line is " +
        "TITANHIDE with a bigger frill",
    from:"  if(st >= 3){\n    const G = gr;\n    if(st === 3){\n      // THE MOUNTAIN.",
    to:  "  if(false){\n    const G = gr;\n    if(st === 3){\n      // THE MOUNTAIN." },
  { id:"gorgon-is-the-basilisk", must:"37",
    why:"the head-and-ring branch is skipped and stages 3 and 4 fall through " +
        "to the serpent plan - the top of the rot line is BASILISK at two " +
        "more scales, which is the complaint this arc exists to close",
    from:"  if(st >= 3){\n    const G = 1 + st*.16;\n    const AMBER = [1,.72,.16];\n    if(st === 3){",
    to:  "  if(false){\n    const G = 1 + st*.16;\n    const AMBER = [1,.72,.16];\n    if(st === 3){" },
  // ---- R207: the gale line's top two are a funnel and a rain dragon ------
  { id:"hurricane-is-the-roc", must:"37",
    why:"the funnel-and-dragon branch is skipped and stages 3 and 4 fall through " +
        "to the wyvern plan - the top of the gale line is THE ROC at two more " +
        "scales with the same four wings",
    from:"  if(st >= 3){\n    const G = 1 + st*.16;\n    if(st === 3){\n      // THE HURRICANE.",
    to:  "  if(false){\n    const G = 1 + st*.16;\n    if(st === 3){\n      // THE HURRICANE." },
  // ---- R208: the pyre line's top two are an egg and a sun -----------------
  { id:"eternal-is-the-phoenix", must:"37",
    why:"the egg-and-sun branch is skipped and stages 3 and 4 fall through to " +
        "the bird plan - the top of the pyre line is THE PHOENIX at two more " +
        "scales with the same wings and legs",
    from:"  if(st >= 3){\n    const G = 1 + st*.18;\n    if(st === 3){\n      // THE ETERNAL.",
    to:  "  if(false){\n    const G = 1 + st*.18;\n    if(st === 3){\n      // THE ETERNAL." },
  { id:"flood-is-the-spine", must:"37",
    why:"the wave-and-serpent branch is skipped and stages 3 and 4 fall through " +
        "to the spinosaur plan - the top of the surge line is THE SPINE at two " +
        "more scales with a taller sail",
    from:"  if(st >= 3){\n    const G = 1 + st*.20;\n    const mix = ",
    to:  "  if(false){\n    const G = 1 + st*.20;\n    const mix = " },
  { id:"legion-is-the-hydra", must:"37",
    why:"the shield-wall-and-medusa branch is skipped and stages 3 and 4 fall " +
        "through to the hydra plan - the top of the echo line is THE HYDRA at two " +
        "more scales with a head more each",
    from:"  if(st >= 3){\n    const G = gr;\n    const mix = ",
    to:  "  if(false){\n    const G = gr;\n    const mix = " },
  { id:"bosses-do-not-grow", must:"48",
    why:"the mid-run bosses are back to flat health - a walk past for anyone who has grown",
    from:"const grow = final ? 1 : Math.min(BOSS_GROW_CAP, 1 + BOSS_GROW * Math.max(0, (P ? P.lvl : 1) - 1));",
    to:  "const grow = 1;" },
  { id:"bosses-arrive-far", must:"48",
    why:"the boss rises on the horizon again and dies on the way in",
    from:"const BOSS_AT = 15, BOSS_GROW = .05, BOSS_GROW_CAP = 3;",
    to:  "const BOSS_AT = 26, BOSS_GROW = .05, BOSS_GROW_CAP = 3;" },
  { id:"alert-through-the-caption", must:"52",
    why:"the boss alert is back at the caption's height on a phone",
    from:"let ay = Math.max(h*0.155, 78) + (w < 720 ? 70 : 0);",
    to:  "let ay = Math.max(h*0.155, 78);" },
  { id:"jaws-shut", must:"53",
    why:"the strike no longer opens any jaw",
    from:"           lean:k.lean * a, sq, a, bite:Math.max(0, a) * (k.bite || 0) };",
    to:  "           lean:k.lean * a, sq, a, bite:0 };" },
  { id:"cards-are-grey", must:"54",
    why:"the accent never reaches the card - four grey boxes again",
    from:"    el.style.setProperty(\"--ac\", d.ac);",
    to:  "    ;" },
  { id:"growths-are-one-colour", must:"54",
    why:"every growth card takes the family gold instead of its own colour",
    from:"        ac = (fam === \"u\" && Pa && Pa.col) ? Pa.col : (fam === \"w\" && WCOL[k]) ? WCOL[k] : FAM[fam].ac;",
    to:  "        ac = FAM[fam].ac;" },
  { id:"teeth-are-a-number", must:"55",
    why:"BIGGER TEETH changes the damage and nothing on the animal",
    from:"  return { teeth: 1 + GROW_TEETH * growRank(p, \"spinach\"),",
    to:  "  return { teeth: 1," },
  { id:"legs-never-lift", must:"55",
    why:"LONGER LEGS is a speed and the animal stands where it stood",
    from:"    if(gLift){ const a = legMap(y - hy),  b = legMap(y + hy);  y = (a + b) * .5; hy = (b - a) * .5; }",
    to:  "    ;" },
  { id:"stride-ignores-the-legs", must:"55",
    why:"longer legs take the same short steps, faster",
    from:"  ANIM.ph += (v * dt) * 2.35 / growOf(P).legs;",
    to:  "  ANIM.ph += (v * dt) * 2.35;" },
  { id:"neck-is-a-number", must:"55",
    why:"LONGER NECK grows the reach and not the neck",
    from:"           neck:      GROW_NECK  * growRank(p, \"heart\"),",
    to:  "           neck:      0," },
  { id:"claws-are-a-number", must:"55",
    why:"SHARPER CLAWS is a crit chance and the claws are the claws",
    from:"           claws: 1 + GROW_CLAWS * growRank(p, \"clover\"),",
    to:  "           claws: 1," },
  { id:"hide-is-a-number", must:"55",
    why:"THICKER HIDE is a damage multiplier and the torso is the torso",
    from:"           hide:      GROW_HIDE  * growRank(p, \"plating\"),",
    to:  "           hide:      0," },
  { id:"bite-lands-on-touch", must:"56",
    why:"no wind-up: the bite lands the frame the enemy reaches you, as it did",
    from:"const BITE_WIND = .18, BITE_REST = .47, SPIT_TELL = .30;",
    to:  "const BITE_WIND = .0001, BITE_REST = .47, SPIT_TELL = .30;" },
  { id:"snap-is-a-lean", must:"56",
    why:"the strike never pitches or reaches - the old shove with a new name",
    from:"  e.pt = -.24*e.pre + e.snap*.46;\n  e.rc = e.snap*.30;",
    to:  "  e.pt = 0;\n  e.rc = 0;" },
  { id:"rest-is-free", must:"56",
    why:"the wind-up is added on top of the old rest, and a pile of them bites a fifth less",
    from:"const BITE_WIND = .18, BITE_REST = .47, SPIT_TELL = .30;",
    to:  "const BITE_WIND = .18, BITE_REST = .68, SPIT_TELL = .30;" },
  { id:"spit-from-nowhere", must:"56",
    why:"the spitter lobs with no tell",
    from:"      e.spitTell = (e.atk < SPIT_TELL && d < e.def.ranged.r + 3) ? 1 - Math.max(0, e.atk) / SPIT_TELL : 0;",
    to:  "      e.spitTell = 0;" },
  { id:"dive-is-level", must:"57",
    why:"the dive is a straight line in again - no nose-down",
    from:"  e.pt = -.24*e.pre - .16*dwind + e.snap*.46*(1 - e.dvE*.5) + e.dvE*.40;",
    to:  "  e.pt = -.24*e.pre - .16*dwind + e.snap*.46*(1 - e.dvE*.5);" },
  { id:"dive-end-pops", must:"57",
    why:"the dive posture is binary again and the bird pops back up the frame it ends",
    from:"  e.dvE = (e.dvE || 0) + (dv - (e.dvE || 0)) * Math.min(1, dt * (dv > (e.dvE || 0) ? 18 : 9));",
    to:  "  e.dvE = dv;" },
  { id:"miss-is-silent", must:"57",
    why:"a dive that runs out without a hit just stops",
    from:"        if(e.dvT <= 0){ e.dvT = 0; e.lg = 1; }",
    to:  "        if(e.dvT <= 0){ e.dvT = 0; }" },
  { id:"beats-do-not-pitch", must:"58",
    why:"the boss beats are back to a shear: no rear, no drive",
    from:"           pt: (B.tpt || 0)*ue + (B.apt || 0)*act,",
    to:  "           pt: 0," },
  { id:"boss-chomps-through-the-tell", must:"58",
    why:"the bite's wind-up and snap run through a boss's ability tell",
    from:"      if(inBeat){",
    to:  "      if(false){" },
  { id:"bite-has-no-species", must:"59",
    why:"every kind winds up the same .18 s again",
    from:"        const j = rndSeed(e), b = e.def.bite || 1;",
    to:  "        const j = rndSeed(e), b = 1;" },
  { id:"slow-biters-start-late", must:"59",
    why:"the long wind-up is added on top of the rest and the nip is not: the brute bites less often, the skitter more",
    from:"        e.lead = BITE_WIND * (b - 1) * j;           // early by this (negative: waits this long)",
    to:  "        e.lead = 0;" },
  { id:"heavy-bite-same-motion", must:"59",
    why:"the brute's snap is the skitter's snap, bigger animal or not",
    from:"  const bA = .85 + .15*((e.def && e.def.bite) || 1);          // the heavy bite is the bigger motion",
    to:  "  const bA = 1;" },
  { id:"second-head-is-a-number", must:"60",
    why:"SECOND HEAD is echoes and trails and the animal has one head",
    from:"           heads: Math.min(HEAD_MAX, 1 + growRank(p, \"dupe\")),",
    to:  "           heads: 1," },
  { id:"heads-do-not-splay", must:"60",
    why:"the second head is drawn on top of the first",
    from:"const HEAD_AT = .66, HEAD_MAX = 2, HEAD_SPLAY_MIN = .20, HEAD_SPLAY_MAX = .42;",
    to:  "const HEAD_AT = .66, HEAD_MAX = 2, HEAD_SPLAY_MIN = 0, HEAD_SPLAY_MAX = 0;" },
  { id:"attack-is-a-lean", must:"53",
    why:"a weapon firing is back to the old quarter-lean shove: no wind-up, no swing, no reach",
    from:"    if(k !== \"skulls\") strike(k);",
    to:  "    if(k !== \"skulls\") ANIM.lunge = Math.min(1, ANIM.lunge + .55);" },
  { id:"turn-is-a-cut", must:"53",
    why:"the facing snaps to the new heading in one frame again",
    from:"    P.face = wrapAng(P.face + (Math.abs(d) < .012 ? d : d * (1 - Math.pow(1.7e-5, dt))));   // ~11/s: 95% of a turn in .27 s",
    to:  "    P.face = P.faceWant;" },
  { id:"stomp-is-a-swing", must:"53",
    why:"PULSE loses its stretch-and-stomp and gets the generic crouch",
    from:"  pulse:    { tw:0,   pitch:.04, reach:0,   lean:0,    sq:.18, stomp:true, bite:0 },",
    to:  "  pulse:    { tw:0,   pitch:.04, reach:0,   lean:0,    sq:.18, bite:0 }," },
  { id:"portrait-is-landscape", must:"52",
    why:"the portrait lens and boom go back to the landscape numbers",
    from:"const port = h > w ? clamp((h/w - 1) * .6, 0, .6) : 0;",
    to:  "const port = 0;" },
  { id:"kit-is-half-a-screen", must:"52",
    why:"the kit shrink-wraps to the half screen left of its anchor again",
    from:"    #kit{width:max-content}",
    to:  "    #kit{}" },
  { id:"mastery-never-comes", must:"51",
    why:"the back half of a run is silent growth again",
    from:"if(++silentLv % MASTERY_EVERY === 0){",
    to:  "if(false){" },
  { id:"mastery-includes-more", must:"51",
    why:"a MASTERY can hand MORE a fourth and fifth copy, re-opening the must-pick R230 closed",
    from:"if(!p || isRule(k) || k === \"dupe\") continue;",
    to:  "if(!p || isRule(k)) continue;" },
  { id:"afterburn-is-a-name", must:"50",
    why:"the rush fades at the bare rate with AFTERBURN taken",
    from:"P.rush - RUSH_DRAIN*dt*(hasRule(\"afterburn\") ? AFTERBURN_DRAIN : 1)",
    to:  "P.rush - RUSH_DRAIN*dt" },
  { id:"glass-is-free", must:"50",
    why:"GLASS gives the damage and keeps the health - a strictly better HARDER",
    from:"case \"glass\":   { P.maxhp = Math.max(1, Math.round(P.maxhp * GLASS_HP)); P.hp = Math.min(P.hp, P.maxhp);",
    to:  "case \"glass\":   { P.hp = Math.min(P.hp, P.maxhp);" },
  { id:"third-slot-never-opens", must:"50",
    why:"the third rule slot never opens, and the back half of a run has nothing to choose again",
    from:"const ruleSlots = () => (P && P.lvl >= RULE_THIRD) ? RSLOTS + 1 : RSLOTS;",
    to:  "const ruleSlots = () => RSLOTS;" },
  { id:"finale-forgets-the-last-boss", must:"49",
    why:"the finale never reads what you did to the last boss and falls back to the estimate",
    from:"if(!e.final && e.born !== undefined){ lastBossRate = e.maxhp / Math.max(1, T - e.born - BOSS_RISE); lastBossKit = kitDps(); }",
    to:  "if(false){ lastBossRate = e.maxhp / Math.max(1, T - e.born - BOSS_RISE); lastBossKit = kitDps(); }" },
  { id:"bosses-ignore-your-size", must:"49",
    why:"a mid boss is back to the table times level growth, a walk past for a strong run",
    from:"const ofYou = final ? finaleSize() : Math.min(b.hp * BOSS_SIZE_CAP, kitDps() * (BOSS_SECS[b.t] || 0));",
    to:  "const ofYou = final ? finaleSize() : 0;" },
  { id:"swing-at-the-nearest", must:"47",
    why:"the swing goes back to the nearest body, which in the finale is never the finale",
    from:"const tgt = threatTarget(P.x, P.z, s.rng+3);",
    to:  "const tgt = nearest(P.x, P.z, s.rng+3);" },
  { id:"shoot-the-nearest", must:"47",
    why:"the shot goes back to the nearest body",
    from:"const tgt = threatTarget(P.x, P.z, 40);",
    to:  "const tgt = nearest(P.x, P.z, 40);" },
  { id:"sudden-death-is-a-word", must:"8b",
    why:"the clock stops counting the moment the only timer that decides the run starts",
    from:"$(\"clock\").textContent = sudden ? \"SUDDEN DEATH  \" + fmt(Math.max(0, RUN_LEN + 240 - T))",
    to:  "$(\"clock\").textContent = sudden ? \"SUDDEN DEATH\"" },
  { id:"copy-pups-bite-full", must:"46",
    why:"MORE on BROOD is back to four full pups - ten times the bare weapon on the bench",
    from:"const copy = i >= s.n ? DUPE_DMG : 1;",
    to:  "const copy = 1;" },
  { id:"echoes-never-fire", must:"46",
    why:"MORE is back to five weapons - the other four never echo",
    from:"if(ECHO_WEAPONS.has(k) && dupeN() > 0){ w.echo = dupeN(); w.echoT = ECHO_GAP; }",
    to:  "if(false){ w.echo = dupeN(); w.echoT = ECHO_GAP; }" },
  { id:"trail-is-decoration", must:"46",
    why:"STINK's trailing clouds are drawn and never bite",
    from:"for(const p of auraEchoes(w)) hitNear(p.x, p.z, s.rad*AURA_ECHO_R, (e)=>{",
    to:  "for(const p of []) hitNear(p.x, p.z, s.rad*AURA_ECHO_R, (e)=>{" },
  { id:"momentum-is-a-name", must:"45",
    why:"the chain no longer pays in damage - the rule card is a label",
    from:"if(hasRule(\"momentum\")) d *= hopMul();",
    to:  "if(false) d *= hopMul();" },
  { id:"stomp-is-a-sound", must:"45",
    why:"a landing rings and shakes and hurts nothing",
    from:"  damageArea(P.x, P.z, STOMP_R, STOMP_DMG, 7);",
    to:  "  ;" },
  { id:"kills-do-not-heal", must:"45",
    why:"BLOODTHIRST heals nothing",
    from:"if(hasRule(\"bloodthirst\")) P.hp = Math.min(P.maxhp, P.hp + BLOOD_HEAL(e));",
    to:  "if(false) P.hp = Math.min(P.maxhp, P.hp + BLOOD_HEAL(e));" },
  { id:"hunter-hits-like-anyone", must:"45",
    why:"bosses and elites take the same as a grunt with HUNTER taken",
    from:"if((e.boss || e.elite) && hasRule(\"hunter\")) amount *= HUNTER_MUL;",
    to:  "if(false) amount *= HUNTER_MUL;" },
  { id:"rules-unlimited", must:"45",
    why:"the two-rule cap is gone, so a run takes all four and which two stops being a decision",
    from:"if(!p && rCount < RSLOTS && P.lvl >= RULE_FROM)",
    to:  "if(!p && P.lvl >= RULE_FROM)" },
  { id:"delta-says-nothing", must:"44",
    why:"a weapon rank-up card goes back to saying nothing about what the rank does",
    from:"if(dmg > 1.01) out.push(`+${Math.round((dmg-1)*100)}% DMG`);",
    to:  "if(false) out.push(`+${Math.round((dmg-1)*100)}% DMG`);" },
  { id:"partner-hidden", must:"44",
    why:"the passive half of an evolution pair stops saying what it unlocks",
    from:"if(leads.length) pt = \"UNLOCKS \" + leads.join(\" · \");",
    to:  "if(false) pt = \"UNLOCKS \" + leads.join(\" · \");" },
  { id:"headline-blank", must:"44",
    why:"the card's one big number is rendered empty - the old nine-pixel prose is all that is left",
    from:"`<div class=\"eff\">${d.eff}</div>",
    to:  "`<div class=\"eff\"></div>" },
  { id:"air-is-decoration", must:"43",
    why:"the airborne flag no longer lifts a form off the tar, so the kite and the " +
        "storm are dragged like walkers again",
    from:"  const groundSpd = (sureFoot || up) ? 1 : (bmod.spd || 1);",
    to:  "  const groundSpd = sureFoot ? 1 : (bmod.spd || 1);" },
  { id:"ice-grips-fliers", must:"43",
    why:"the glacier takes the grip off a flier that is not standing on it",
    from:"  const grip = bmod.slide && !sureFoot && !up ? .30 : 1;",
    to:  "  const grip = bmod.slide && !sureFoot ? .30 : 1;" },
  { id:"ground-is-silent", must:"43",
    why:"the tar and the ice go back to changing your speed without a word",
    from:"    if(known && running && !over){\n      if(bId === \"bog\")",
    to:  "    if(false){\n      if(bId === \"bog\")" },
  { id:"legs-do-not-go", must:"42",
    why:"a corpse's legs stay straight under it - the fall is back to a squash " +
        "with four stiff legs, a toy knocked over",
    from:"    splay = deathPose(e.ft / e.fd).drop;             // 0 -> 1 over the first 40%",
    to:  "    splay = 0;" },
  { id:"stubs-do-not-go", must:"42",
    why:"the terrapin's leg stubs stay under it - the shambler, the most common " +
        "body in the game, dies a toy again",
    from:"  const dsp = (e.dead && e.ft !== undefined) ? deathPose(e.ft / e.fd).drop : 0;\n  for(const sg of [-1,1]) for(const fs of [-1,1])",
    to:  "  const dsp = 0;\n  for(const sg of [-1,1]) for(const fs of [-1,1])" },
  { id:"taper-does-not-go", must:"42",
    why:"the pterling's legs stay tucked - a runner dies with its legs still " +
        "folded under a belly on the ground",
    from:"  const dsp = (e.dead && e.ft !== undefined) ? deathPose(e.ft / e.fd).drop : 0;\n  for(const sg of [-1,1])\n    etp(",
    to:  "  const dsp = 0;\n  for(const sg of [-1,1])\n    etp(" },
  { id:"rush-never-fills", must:"41",
    why:"a kill no longer feeds the meter, so there is no rush at all",
    from:"  if(P) P.rush = Math.min(1, (P.rush||0) + (e.boss ? 1 : e.elite ? RUSH_KILL*2 : RUSH_KILL));",
    to:  "" },
  { id:"rush-never-drains", must:"41",
    why:"the meter never bleeds, so the first three kills of a run are +22% forever",
    from:"  if(P.rush > 0) P.rush = Math.max(0, P.rush - RUSH_DRAIN*dt);   // rush bleeds, kills or no kills",
    to:  "" },
  { id:"rush-is-not-speed", must:"41",
    why:"the meter fills and bleeds and buys nothing on the ground",
    from:"* (surgeUp() ? SURGE_SPD : 1) * rushMul();",
    to:  "* (surgeUp() ? SURGE_SPD : 1);" },
  { id:"evolution-keeps-pace", must:"40",
    why:"evolving no longer rescales speed, so every line runs at one pace from " +
        "hatchling to final - which is exactly the report this section answers",
    from:"  monMul.spd *= r(\"spd\"); monMul.cd *= r(\"cd\"); monMul.mag *= r(\"mag\");",
    to:  "  monMul.spd *= 1; monMul.cd *= r(\"cd\"); monMul.mag *= r(\"mag\");" },
  { id:"hatchling-pace-skipped", must:"40",
    why:"the run starts with the multipliers at one again, so a pace on stage 0 " +
        "is silently skipped for the whole first stage",
    from:"  monMul = { spd:st0.spd||1, cd:st0.cd||1, mag:st0.mag||1 };\n  P.spd *= monMul.spd; P.cd *= monMul.cd; P.mag *= monMul.mag;",
    to:  "  monMul = { spd:1, cd:1, mag:1 };" },
  { id:"surge-is-not-speed", must:"40",
    why:"the courier's surge goes back to being damage only",
    from:"* wmul * (surgeUp() ? SURGE_SPD : 1) * rushMul();",
    to:  "* wmul * rushMul();" },
  { id:"portrait-axes-swapped", must:"39",
    why:"the card camera reads the box capture as (lateral, vertical, fore-aft) " +
        "again, so every portrait is framed on the animal's depth where it " +
        "wants its height and the tall ones lose their heads off the top",
    from:"              hx=bodyPos[i+3], hz=bodyPos[i+4], hy=bodyPos[i+5];",
    to:  "              hx=bodyPos[i+3], hy=bodyPos[i+4], hz=bodyPos[i+5];" },
  { id:"portrait-frames-flat", must:"39",
    why:"the card camera solves its boom as if it were level with the animal, " +
        "ignoring its own elevation, so a tall form is framed a tenth short",
    from:"      const tall = F.halfH * Math.cos(elev) + F.radF * Math.sin(elev);",
    to:  "      const tall = F.halfH;" },
  { id:"clutch-is-the-plesiosaur", must:"38",
    why:"the clutch-and-ribbon branch is skipped and stages 0 and 1 fall " +
        "through to the plesiosaur plan - the tide line is the LEVIATHAN at two " +
        "smaller scales with less neck, which is where it started",
    from:"  if(st <= 1){\n    const G = gr;\n    if(st === 0){\n      // SPAWNLING.",
    to:  "  if(false){\n    const G = gr;\n    if(st === 0){\n      // SPAWNLING." },
  { id:"grub-is-the-hydra", must:"38",
    why:"the grub-and-necks branch is skipped and stages 0 and 1 fall through " +
        "to the hydra plan - the echo line is one four-legged serpent three " +
        "times with a head less each, which is where it started",
    from:"  if(st <= 1){\n    const G = gr;\n    const HD = ",
    to:  "  if(false){\n    const G = gr;\n    const HD = " },
  { id:"kite-is-the-roc", must:"38",
    why:"the kite-and-fledgling branch is skipped and stages 0 and 1 fall " +
        "through to the wyvern plan - the gale line is THE ROC at two smaller " +
        "spans, which measured .61 of height over length at all three stages",
    from:"  if(st <= 1){\n    const G = gr;\n    if(st === 0){\n      // WYVERNET.",
    to:  "  if(false){\n    const G = gr;\n    if(st === 0){\n      // WYVERNET." },
  { id:"fry-is-the-spinosaur", must:"38",
    why:"the fry-and-koi branch is skipped and stages 0 and 1 fall through to " +
        "the spinosaur plan - the surge line is THE SPINE at two smaller scales " +
        "with less sail, which is where it started",
    from:"  if(st <= 1){\n    const G = gr;\n    const fin = ",
    to:  "  if(false){\n    const G = gr;\n    const fin = " },
  { id:"pebble-is-the-tank", must:"38",
    why:"the hatchling-and-juvenile branch is skipped and stages 0 and 1 fall " +
        "through to the ceratopsian plan - the stone line starts life as " +
        "TITANHIDE at two smaller scales, which is where it started",
    from:"  if(st <= 1){\n    const G = gr;",
    to:  "  if(false){\n    const G = gr;" },
  { id:"horde-count-reads-zero", must:"11b",
    why:"the horde's box counter is never set, so the per-enemy budget divides " +
        "nothing by the horde and every ceiling on it passes",
    from:"  hordeBoxes = drawnBoxes + nbox - hb0;",
    to:  "  hordeBoxes = 0;" },
];

// A stale anchor is a hole in the audit that reads as a pass, and the full run
// takes over an hour to tell you. This takes milliseconds and needs no browser,
// so CI can hold every mutation to the source on every push.
if (process.argv[2] === "--anchors") {
  const bad = MUTANTS.filter(m => !src.includes(m.from));
  console.log("=".repeat(70));
  console.log("ANCHOR CHECK  -  every mutation must still find its target");
  console.log("-".repeat(70));
  for (const m of bad) console.log(`  FAIL  ${m.id}: anchor no longer in index.html`);
  if (!bad.length) console.log(`  OK   ${MUTANTS.length} mutations, every anchor present`);
  process.exit(bad.length ? 1 : 0);
}

// RESUMABLE, because a full pass is 48 browser suites and this machine is never
// free for the four hours that takes. One run was lost to a container restart at
// row 37 and another wedged on a single mutant for six hours, and both threw
// away everything already measured. With --resume the results FILE is the
// state: rows already in it are skipped, and each new row is appended the
// moment it is known, so a pass can be run in slices between other work and
// survives anything that kills it.
//
//   node mutate.js --resume        # everything not yet recorded
//   node mutate.js --resume 4      # at most four more, then stop
const RESUME = process.argv.includes("--resume");
const LOG = path.resolve(__dirname, "mutate-results.txt");
const done = new Set();
let slice = Infinity;
if (RESUME) {
  if (fs.existsSync(LOG))
    for (const line of fs.readFileSync(LOG, "utf8").split("\n")) {
      const mm = line.match(/^\S+\s+(\S+)/);
      if (mm) done.add(mm[1]);
    }
  const n = process.argv.slice(3).find(a => /^\d+$/.test(a));
  if (n) slice = +n;
  console.log(`resuming: ${done.size} recorded, ${MUTANTS.length - done.size} to go` +
              (slice === Infinity ? "" : `, doing at most ${slice} now`));
}
const want = RESUME ? null : process.argv[2];
let run = MUTANTS.filter(m => (!want || m.id.includes(want)) && !done.has(m.id));
if (slice !== Infinity) run = run.slice(0, slice);
// ONE TEMP FILE PER RUN, named after the process. Two audits sharing a fixed
// filename do not fail loudly, they fail as nonsense: the second run's children
// load whatever the first run last wrote, so a mutation gets scored against
// somebody else's game, and when one run finishes and unlinks the file the
// other's next page load dies on ERR_FILE_NOT_FOUND. Both happened - a stale
// audit that a kill had not actually reaped was still writing this path while
// a fresh one ran, and the fresh one's rows came back as a wall of
// "no RESULT line" that looked like findings.
const TMP  = path.resolve(__dirname, `_mutant.${process.pid}.html`);
// SNAPSHOT THE SUITE TOO, not just the game. A full run takes hours, and this
// tool read `src` once at startup but shelled out to test.js FROM DISK for
// every mutant - so editing the suite mid-run silently changed the instrument
// underneath the experiment. It happened: a round added a setHp QA hook to
// index.html and a check that calls it to test.js, and every mutant after that
// point ran the new suite against a snapshot of the game that predated the
// hook. g.setHp was not a function, the harness died in section 21 whatever
// the mutation was, and eight consecutive rows came back "no RESULT line" -
// scored as holes, and every one of them an artefact of the edit rather than a
// finding. Copying the suite next to the mutant makes a run a snapshot of BOTH
// halves, so an audit measures the pair it started with.
const TMPT = path.resolve(__dirname, `_mutant.${process.pid}.test.js`);
fs.writeFileSync(TMPT, fs.readFileSync(path.resolve(__dirname, "test.js"), "utf8"));
let survived = 0;

for (const m of run) {
  if (!src.includes(m.from)) {
    console.log(`SKIP  ${m.id.padEnd(22)} anchor no longer in index.html`);
    survived++; continue;
  }
  fs.writeFileSync(TMP, src.replace(m.from, m.to));
  // The child writes its verdict to stdout and exits 1 on failure, so the
  // failure path is the NORMAL path here and its output is the whole point.
  // A first version read `out` only from the success return and scanned it for
  // the word FAIL; every mutation therefore came back "SURVIVED", including
  // ones the suite was catching cleanly. Which is the joke: the tool built to
  // check that a green result means something was itself green and meaningless.
  let out = "", crash = null;
  try {
    out = execFileSync(process.execPath, [TMPT],
      { env: { ...process.env, BONKHORDE_TARGET: path.basename(TMP) },
        encoding: "utf8", stdio: ["ignore", "pipe", "pipe"],
        maxBuffer: 32 << 20, timeout: 30 * 60e3 });
  } catch (e) {
    out = String(e.stdout || "") + String(e.stderr || "");
    if (e.killed || e.signal) crash = `killed (${e.signal || "timeout"})`;
  }
  // The suite's own RESULT line is the verdict. Its absence means the run died
  // before finishing, which is neither caught nor survived - it is no data.
  const verdict = out.match(/RESULT: (\d+) passed, (\d+) failed/);
  if (!verdict) {
    console.log(`ERROR     ${m.id.padEnd(22)} expected ${m.must.padEnd(4)} ` +
                `no RESULT line - ${crash || "the suite did not finish"}`);
    // AND WHY. A full run costs about five minutes, so an ERROR that says only
    // "did not finish" buys a second five minutes to find out what everybody
    // already had on stdout. The tail is almost always the answer: the section
    // header it died under, and the exception under that. Note the difference
    // this exposes - a `crash` value means the child was KILLED (timeout, a
    // signal), while its absence means the child exited on its own without
    // printing a verdict, which is a crash rather than a hang.
    const tail = out.trimEnd().split("\n").slice(-8);
    for (const line of tail) console.log(`          | ${line}`);
    survived++; continue;
  }
  const nFail = +verdict[2];
  // WHICH SECTIONS FAILED, not just the first one. Reading only the first was
  // ambiguous in a way that hid a real hole: a lower-case "caught" meant "the
  // first failure was somewhere else", which is damning when the expected
  // section runs EARLIER (it ran and passed a broken game) and means nothing
  // when it runs later (it may never have been reached before something else
  // went red). Both printed the same. collector-never-rests was the first kind
  // and section 18 had genuinely stopped working; jump-unbuffered looked
  // identical and was the second kind. Track every section that failed, and
  // say plainly whether the one that owns this mutation was among them.
  const lines = out.split("\n");
  let section = "(none)", first = null;
  const failedIn = new Set();
  for (const line of lines) {
    const h = line.match(/^=== ([\w.]+)\./);
    if (h) { section = h[1]; continue; }
    if (line.includes("FAIL")) { failedIn.add(section); if (!first) first = section; }
  }
  const caught = nFail > 0;
  const byOwner = failedIn.has(m.must);
  const tag = !caught ? "SURVIVED" : byOwner ? "CAUGHT  " : "elsewhere";
  const row = `${tag.padEnd(9)} ${m.id.padEnd(22)} expected ${m.must.padEnd(4)} ` +
              `${caught ? `${nFail} assertion(s), first in ${first}` +
                          (byOwner ? (first === m.must ? "" : ` and ${m.must} also caught it`)
                                   : ` - ${m.must} did NOT`)
                        : "the suite passed a broken game"}`;
  console.log(row);
  // Append the moment it is known, not at the end: a run that dies has still
  // banked everything it measured.
  if (RESUME) fs.appendFileSync(LOG, row + "\n");
  // A mutation caught only by a section that does not own it is a hole in the
  // owning section, even though the suite went red. Count it as one.
  if (!caught || !byOwner) survived++;
}
fs.existsSync(TMP) && fs.unlinkSync(TMP);
fs.existsSync(TMPT) && fs.unlinkSync(TMPT);
console.log(`\n${run.length - survived}/${run.length} mutations caught`);
process.exit(survived ? 1 : 0);
