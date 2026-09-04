// THUNDERHEAD's discharge, photographed: an elite in a crowd of eleven, the chain and the return stroke on the frame it fires.
// node film/thunderfilm.js  -> thunder-{chain,alone}.png in the working directory, and the damage each cast did to the elite
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html");
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:1280,height:800}}); p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
 for(const [nm,crowd] of [["chain",true],["alone",false]]){
  const r=await p.evaluate((crowd)=>{ const g=window.__g;
    g.drainPicks(true); g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.setShake(0); g.clearEnemies(); g.disarm(); g.skipTo(900);
    const s=g.state(); g.spawnAt("shambler", s.x+3, s.z); g.elite(0); const id=g.enemyList()[0].id, before=g.enemyList()[0];
    if(crowd) for(let i=0;i<11;i++){ const a=i/11*Math.PI*2+.3, d=5+(i%3); g.spawnAt("shambler", s.x+Math.cos(a)*d, s.z+Math.sin(a)*d); }
    g.give("zap",3); g.evolve("zap"); g.aim(0);
    g.setWT("zap",0); g.stepRaw(1/60); g.pause(true); document.getElementById("paused").style.display="none";
    const e=g.enemyList().find(x=>x.id===id); return { dmg:+(before.hp-(e?e.hp:0)).toFixed(1), killed:!e, arcs:g.arcsNow() }; }, crowd);
  await p.waitForTimeout(300); await p.screenshot({path:`thunder-${nm}.png`}); console.log(nm, JSON.stringify(r));
  await p.evaluate(()=>{ document.getElementById("paused").style.display=""; window.__g.resume(); });
 }
 await b.close(); })();
