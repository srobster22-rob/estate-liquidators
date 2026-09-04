// The bolt fan, photographed mid-flight: the finale boss nine metres ahead, a crowd off to the side, one volley in the air.
// node film/fanfilm.js  -> fan-crowd.png (the fan goes to the crowd) and fan-alone.png (the boss alone takes it all)
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html");
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:1280,height:800}}); p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
 for(const [nm,crowd] of [["crowd",true],["alone",false]]){
  const r=await p.evaluate((crowd)=>{ const g=window.__g;
    g.drainPicks(true); g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.setShake(0); g.clearEnemies(); g.disarm();
    g.skipTo(1140); g.boss(3); for(let i=0;i<240;i++) g.stepRaw(1/60);
    const bs=g.bossAt(), s0=g.state(), ang=Math.atan2(bs.z-s0.z, bs.x-s0.x);
    g.place(bs.x-Math.cos(ang)*9, bs.z-Math.sin(ang)*9); const pp=g.state();
    if(crowd) for(let i=0;i<10;i++){ const a=ang+Math.PI/2+((i+.5)/10-.5)*Math.PI/2, d=12+(i%2)*2; g.spawnAt("shambler", pp.x+Math.cos(a)*d, pp.z+Math.sin(a)*d); }
    g.give("bolt",3); g.evolve("bolt"); g.aim(Math.atan2(Math.cos(ang), Math.sin(ang)) + (crowd ? Math.PI/4 : 0)); g.dmg();
    g.setWT("bolt",0); g.stepRaw(1/60); g.setWT("bolt",99); for(let i=0;i<10;i++) g.stepRaw(1/60);
    g.pause(true); document.getElementById("paused").style.display="none";
    const d=g.dmg(); return { bossSoFar:Math.round(d.boss), allSoFar:Math.round(d.all), bolts:g.fxCounts().bolts }; }, crowd);
  await p.waitForTimeout(300); await p.screenshot({path:`fan-${nm}.png`}); console.log(nm, JSON.stringify(r));
  await p.evaluate(()=>{ document.getElementById("paused").style.display=""; window.__g.resume(); });
 }
 await b.close(); })();
