// the dive, one frame per shot: a runner spawned in range of a standing player; side camera; the loop paused so only stepRaw advances
const fs=require("fs");const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"],executablePath:"/opt/pw-browsers/chromium-1194/chrome-linux/chrome"};
const [pre="dive", file=require("path").resolve(__dirname, "../index.html"), every="2"]=process.argv.slice(2);
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:900,height:600}}); p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto("file://"+file,{waitUntil:"load"}); await p.waitForTimeout(400);
 const info=await p.evaluate(()=>{ const g=window.__g; g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0,0); g.aim(0); if(g.still) g.still(true);
   g.step(120,1/60); const s=g.state(); g.camLock(s.x-7.5, s.y+2.6, s.z+3.6, s.x, s.y+1.2, s.z+3.2);
   g.spawnAt("runner", 0, 7.5); let n=0; while(n<600){ g.stepRaw(1/60); n++; const e=g.gait()[0]; if(e.dvW>.25) break; }
   dispatchEvent(new KeyboardEvent("keydown",{code:"Escape"})); const pz=document.getElementById("paused"); if(pz) pz.style.display="none";
   return { n, paused:!!document.getElementById("paused").classList.contains("on") }; });
 console.log(JSON.stringify(info)); const rows=[];
 for(let i=0;i<30;i++){ const r=await p.evaluate((every)=>{ const g=window.__g; for(let k=0;k<every;k++) g.stepRaw(1/60); const e=g.gait()[0]||{}; return { dvW:e.dvW, dvT:e.dvT, dvE:e.dvE, pt:e.pt, lg:e.lg }; }, +every); rows.push(r); await p.waitForTimeout(70); await p.screenshot({path:`${pre}-${String(i).padStart(2,"0")}.png`,clip:{x:150,y:60,width:600,height:480}}); }
 console.log(JSON.stringify(rows.map(r=>[r.dvW,r.dvT,+(r.dvE||0).toFixed(2),+(r.pt||0).toFixed(2),r.lg]))); await b.close(); })();
