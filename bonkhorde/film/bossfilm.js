// a boss ability, frame by frame: the boss is cued into the TELL, the loop paused, and shots are taken every N frames through the tell and the act. node bossfilm.js <prefix> <bossIndex> <kind> [file] [every]
const fs=require("fs");const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"],executablePath:"/opt/pw-browsers/chromium-1194/chrome-linux/chrome"};
const [pre="boss", bi="0", kind="slam", file=require("path").resolve(__dirname, "../index.html"), every="6"]=process.argv.slice(2);
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:900,height:600}}); p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto("file://"+file,{waitUntil:"load"}); await p.waitForTimeout(400);
 const info=await p.evaluate(({bi,kind,follow})=>{ const g=window.__g; g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0,0); g.aim(0); if(g.still) g.still(true);
   g.step(60,1/60); g.boss(+bi); g.step(1,1/60); const b0=g.bossAt(); g.place(b0.x, b0.z-9); g.step(240,1/60);   // arrived and out of the ground
   const b1=g.bossAt(); const H=b1.rad*2.2;
   g.camLock(b1.x-H*2.6, b1.y!==undefined? b1.y+H*.9 : H*.9, b1.z+H*.4, b1.x, H*.55, b1.z);
   window.__follow = !!follow; g.bossCue(kind, "tell"); g.stepRaw(1/60);
   dispatchEvent(new KeyboardEvent("keydown",{code:"Escape"})); const pz=document.getElementById("paused"); if(pz) pz.style.display="none";
   return { nm:b1.nm, rad:b1.rad, ab:g.bossAt().ab }; },{bi,kind,follow:!!process.env.FOLLOW});
 console.log(JSON.stringify(info)); const rows=[];
 for(let i=0;i<20;i++){ const r=await p.evaluate((every)=>{ const g=window.__g; for(let k=0;k<every;k++) g.stepRaw(1/60); if(window.__follow){ const b=g.bossAt(); if(b){ const H=b.rad*2.2; g.camLock(b.x-H*2.6, H*.9, b.z+H*.4, b.x, H*.55, b.z); } } const e=g.gait().find(q=>q.type && q.type.startsWith && true)||g.gait()[0]; const b=g.bossAt(); return { ph:b&&b.ab?b.ab.phase:null, t:b&&b.ab?b.ab.t:null, pt:e?e.pt:null, btu:e?e.btu:null, sq:e?e.sq:null }; }, +every); rows.push(r); await p.waitForTimeout(70); await p.screenshot({path:`${pre}-${String(i).padStart(2,"0")}.png`,clip:{x:150,y:60,width:600,height:480}}); }
 console.log(JSON.stringify(rows.map(r=>[r.ph,r.t,r.pt,r.btu,r.sq]))); await b.close(); })();
