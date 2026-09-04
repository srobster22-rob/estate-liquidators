// the spitter's lob, frame by frame: side camera on the spitter holding at range; one frame per shot through the tell and the snap
const fs=require("fs");const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"],executablePath:"/opt/pw-browsers/chromium-1194/chrome-linux/chrome"};
const [pre="spit", file=require("path").resolve(__dirname, "../index.html")]=process.argv.slice(2);
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:900,height:600}}); p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto("file://"+file,{waitUntil:"load"}); await p.waitForTimeout(400);
 const info=await p.evaluate(()=>{ const g=window.__g; g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0,0); g.aim(0); if(g.still) g.still(true);
   g.step(120,1/60); g.spawnAt("spitter", 0, 12.5);
   // run to 22 frames before the second spit (the first is immediate); it settles in its band meanwhile
   let snaps=0, n=0; while(n<600){ g.stepRaw(1/60); n++; const e=g.gait()[0]; if(e.lg>.9 && snaps===0){ snaps=1; break; } }
   for(let i=0;i<157-24;i++) g.stepRaw(1/60);
   const e=g.gait()[0]; const s=g.state();
   g.camLock(e.x-4.2, e.y+1.9, e.z-1.2, e.x, e.y+.9, e.z+.3);
   dispatchEvent(new KeyboardEvent("keydown",{code:"Escape"})); const pz=document.getElementById("paused"); if(pz) pz.style.display="none";   // pause: the render runs, the sim does not
   return { paused: !!document.getElementById("paused").classList.contains("on"), n, ex:+e.x.toFixed(2), ez:+e.z.toFixed(2), d:+Math.hypot(e.x-s.x,e.z-s.z).toFixed(2) }; });
 console.log(JSON.stringify(info)); const rows=[];
 for(let i=0;i<16;i++){ const r=await p.evaluate(()=>{ const g=window.__g; g.stepRaw(1/60); g.stepRaw(1/60); const e=g.gait()[0]; return { pre:e.pre, lg:e.lg, pt:e.pt }; }); rows.push(r); await p.waitForTimeout(70); await p.screenshot({path:`${pre}-${String(i).padStart(2,"0")}.png`,clip:{x:150,y:60,width:600,height:480}}); }
 console.log(JSON.stringify(rows)); await b.close(); })();
