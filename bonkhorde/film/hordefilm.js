// the horde's bite, frame by frame: a brute walks in from 7 m and bites a standing player; fixed side camera; frames every 50 ms once it is within 3 m
// node hordefilm.js <prefix> <enemy> [file]
const fs=require("fs");const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"],executablePath:"/opt/pw-browsers/chromium-1194/chrome-linux/chrome"};
const [pre="bite", en="brute", file=require("path").resolve(__dirname, "../index.html")]=process.argv.slice(2);
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:900,height:600}});
 p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto("file://"+file,{waitUntil:"load"}); await p.waitForTimeout(400);
 await p.evaluate(({en})=>{ const g=window.__g; g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0,0); g.aim(0); if(g.still) g.still(true);
   g.step(120,1/60); const s=g.state();
   // side camera on the line the brute walks in on (+z), looking at the gap in front of the player
   g.camLock(s.x-6.5, s.y+2.4, s.z+2.6, s.x, s.y+0.9, s.z+1.8);
   g.spawnAt(en, 0, 7.0); },{en});
 // step until it is within 3.2 m, then film 20 frames 50 ms apart
 const t0=await p.evaluate(()=>{ const g=window.__g; let n=0; while(n<900){ g.stepRaw(1/60); n++; const e=g.enemiesPos()[0]; if(!e) return -1; if(Math.hypot(e.x-g.state().x, e.z-g.state().z) < 3.2) return n; } return -2; });
 console.log("close after", t0); await p.evaluate(()=>{ dispatchEvent(new KeyboardEvent("keydown",{code:"Escape"})); const pz=document.getElementById("paused"); if(pz) pz.style.display="none"; });
 const rows=[];
 for(let i=0;i<20;i++){ const r=await p.evaluate((follow)=>{ const g=window.__g; for(let k=0;k<3;k++) g.stepRaw(1/60); if(follow){ const ep=g.enemiesPos()[0]; const s=g.state(); if(ep) g.camLock(ep.x-3.2, s.y+1.4, ep.z+0.6, ep.x, s.y+0.6, ep.z); } const e=g.gait()[0]||{}; const s=g.state(); const ep=g.enemiesPos()[0]||{x:0,z:0}; return { d:+Math.hypot(ep.x-s.x,ep.z-s.z).toFixed(2), lg:e.lg, pre:e.pre, hp:s.hp }; }, !!process.env.FOLLOW);
   rows.push(r); await p.waitForTimeout(80); await p.screenshot({path:`${pre}-${String(i).padStart(2,"0")}.png`,clip:{x:150,y:60,width:600,height:480}}); }
 console.log(JSON.stringify(rows)); await b.close(); })();
