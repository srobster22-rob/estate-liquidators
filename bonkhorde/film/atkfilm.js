// The attack, frame by frame: a form stands among grubs with one weapon, the camera fixed behind-left, twelve frames 50 ms apart from the swing.
// node atkfilm.js <prefix> <char> <stage> <weapon>
const fs=require("fs");const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const [pre="atk", ch="intern", st="1", w="bat"]=process.argv.slice(2);
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:900,height:600}});
 p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto("file://"+require("path").resolve(__dirname, "../index.html"),{waitUntil:"load"}); await p.waitForTimeout(400);
 await p.evaluate(({ch,st,w,cam,tgt})=>{ const g=window.__g; g.wipeSave(); g.pin(3); g.pinRun(3); g.start(ch); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.aim(0);
   if(+st) g.evolveTo(+st); g.give(w,0); g.step(30,1/60);
   // a ring of tanks in front so the swing has something to hit and nothing dies
   for(let i=0;i<5;i++){ if(tgt==="side") g.spawnAt("brute", 6.0, -3+i*1.5); else g.spawnAt("brute", -3+i*1.5, 5.5); }
   g.step(20,1/60);
   // camera: fixed, behind-left, looking at the animal
   const s=g.state(); if(cam==="front") g.camLock(s.x+3.5, s.y+6.0, s.z+7.5, s.x, s.y+0.8, s.z+0.5); else if(cam==="close") g.camLock(s.x-3.2, s.y+2.6, s.z+3.6, s.x+0.4, s.y+1.25, s.z+0.6); else if(cam==="high") g.camLock(s.x-3.0, s.y+7.0, s.z-5.0, s.x, s.y+0.6, s.z+1.0); else g.camLock(s.x-5.5, s.y+3.2, s.z-6.5, s.x, s.y+1.0, s.z+1.5);
 },{ch,st,w,cam:process.env.CAM||"back",tgt:process.env.TGT||"front"});
 // wait for the next fire: poll the swing count, then film
 const fired=await p.evaluate(()=>{ const g=window.__g; const c0=g.fxCounts(); let n=0; while(n<600){ g.stepRaw(1/60); n++; const c=g.fxCounts(); if(c.swings>c0.swings||c.bolts>c0.bolts||c.rings>c0.rings||c.lanes>c0.lanes||c.shells>c0.shells||c.arcs>c0.arcs) return n; } return -1; });
 console.log("fired after frames", fired);
 // step back a few frames is not possible; instead film from here, 3 frames apart (50 ms)
 for(let i=0;i<12;i++){ await p.evaluate(()=>{ window.__g.stepRaw(1/60); window.__g.stepRaw(1/60); window.__g.stepRaw(1/60); }); await p.waitForTimeout(90); await p.screenshot({path:`${pre}-${String(i).padStart(2,"0")}.png`,clip:{x:150,y:60,width:600,height:480}}); }
 const a=await p.evaluate(()=>window.__g.anim ? window.__g.anim() : null); console.log("anim", JSON.stringify(a));
 await b.close(); })();
