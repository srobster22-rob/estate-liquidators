// Every weapon in action, photographed: one weapon at rank 3 (and evolved, with EVO=1), a ring of shamblers,
// three moments of its cycle from a close camera. node film/weaponsheet.js [key,key,...]  -> ws-<key>-<n>.png
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html"), OUT=process.env.OUT||".", EVO=process.env.EVO==="1";
const KEYS=(process.argv[2]||"bat,skulls,bolt,pulse,mortar,zap,stink,gore,trail,pack").split(",");
const FRAMES=(process.env.FRAMES||"2,10,26").split(",").map(Number);
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:720,height:450}}); p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
 for(const key of KEYS){
  let last=0;
  for(const f of FRAMES){
    const r=await p.evaluate(([key,f,evo])=>{ const g=window.__g;
      g.drainPicks(true); g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.setShake(0); g.drainPicks(true); g.clearEnemies(); g.disarm();
      g.place(0,0); const pp=g.state();
      for(let i=0;i<10;i++){ const a=(i/10)*Math.PI*2, d=5.5+(i%2)*2.5; g.spawnAt("shambler", pp.x+Math.sin(a)*d, pp.z+Math.cos(a)*d); }
      g.give(key,3); if(evo){ try{ g.evolve(key); }catch(e){} }
      g.aim(0); g.setCam(Math.PI, .75, .62);
      g.setWT(key,0); for(let i=0;i<f;i++) g.stepRaw(1/60);
      g.pause(true); document.getElementById("paused").style.display="none"; document.getElementById("hud").style.opacity="0";
      return { kit:g.kit().join(","), enemies:g.state().enemies, wt:g.fxCounts ? Object.entries(g.fxCounts()).filter(([k,v])=>v).map(([k,v])=>k+":"+v).join(" ") : "" }; }, [key,f,EVO]);
    await p.waitForTimeout(250); await p.screenshot({path:`${OUT}/ws-${key}${EVO?"-evo":""}-${String(f).padStart(2,"0")}.png`});
    await p.evaluate(()=>{ document.getElementById("paused").style.display=""; document.getElementById("hud").style.opacity=""; window.__g.resume(); });
    last=r; }
  console.log(key, JSON.stringify(last)); }
 await b.close(); })();
