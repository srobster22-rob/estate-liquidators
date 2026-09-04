// The level-up screen, photographed: a fresh hand with the shop's reroll and banish bought, banish armed, the hand after a reroll,
// an eight-minute hand with an evolution on it, and a MASTERY hand - each at desktop (1280x800) and phone (390x844).
// node film/draftfilm.js  -> draft-<viewport>-<state>.png in the working directory
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html");
(async()=>{ const b=await chromium.launch(L);
 for(const [w,h,nm] of [[1280,800,"desk"],[390,844,"phone"]]){
  const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:1,hasTouch:nm==="phone",isMobile:nm==="phone"});
  p.on("pageerror",e=>console.log("ERR",e.message));
  await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
  const shot=async(name,fn,arg)=>{ const st=await p.evaluate(fn,arg); await p.waitForTimeout(350); await p.screenshot({path:`draft-${nm}-${name}.png`}); console.log(nm, name, JSON.stringify(st)); };
  // a fresh hand at level 2, with two rerolls and a banish bought
  await shot("lv2",()=>{ const g=window.__g; g.wipeSave(); g.setSave({ up:{ reroll:2, banish:1 } }); g.pin(7); g.pinRun(7); g.start("intern"); g.bot(true); g.botHop(true); g.setShake(0);
    g.runOut(20); g.bot(false); g.drainPicks(false); g.xp(60); g.stepRaw(1/60); const s=g.state(); return { t:s.t, lvl:s.lvl, picking:s.picking, hand:g.hand().map(o=>o.nm), draft:g.draft() }; });
  // banish armed: the rows say which can go
  await shot("banish-armed",()=>{ const g=window.__g; const a=g.draft(); if(!a.banMode){ document.getElementById("pkBanish").click(); } return g.draft(); });
  // the second row struck from the run, its place filled
  await shot("banished",()=>{ const g=window.__g; const before=g.hand().map(o=>o.nm); g.banishRow(1); return { before, after:g.hand().map(o=>o.nm), draft:g.draft() }; });
  // and the hand rerolled
  await shot("rerolled",()=>{ const g=window.__g; const before=g.hand().map(o=>o.nm); g.rerollHand(); return { before, after:g.hand().map(o=>o.nm), draft:g.draft() }; });
  // eight minutes in on seed 41, dealt on its own run, with THICKER HIDE finished so MORTAR's evolution is on the table
  await shot("8m",()=>{ const g=window.__g; g.drainPicks(true); g.wipeSave(); g.setSave({ up:{ reroll:1, banish:1 } }); g.pin(41); g.pinRun(41); g.start("intern"); g.bot(true); g.botHop(true); g.setShake(0);
    g.runOut(480); g.bot(false); g.give("plating",3); g.drainPicks(false); g.xp(400); g.stepRaw(1/60); const s=g.state(); return { t:s.t, lvl:s.lvl, picking:s.picking, hand:g.hand().map(o=>o.lv+" "+o.nm), kit:g.kit().join(" ") }; });
  // a MASTERY hand: everything finished, every fifth silent level
  await shot("mastery",()=>{ const g=window.__g; g.drainPicks(true); g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.setShake(0);
    for(const k of ["bat","skulls","bolt","pulse","mortar","zap","aura","caltrops","gore","brood"]){ g.give(k,3); g.evolve(k); }
    for(const k of ["spinach","boots","tempo","magnet","plating","heart","clover","dupe"]) g.give(k,3);
    for(const k of ["momentum","stomp","hunter"]) g.give(k,1);
    g.drainPicks(false); g.xp(9000); g.step(1,1/60); const s=g.state(); return { lvl:s.lvl, picking:s.picking, hand:g.hand().map(o=>o.lv+" "+o.nm), mastery:g.draft().mastery, tools:document.getElementById("pkTools").children.length }; });
  await p.close();
 }
 await b.close(); })();
