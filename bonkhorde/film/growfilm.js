// the same animal at rank 0 and at full growth, from a fixed camera: node growfilm.js <prefix> <char> <stage> [key|all]  (CAM=close|front|side|high)
const fs=require("fs");const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const [pre="grow", ch="intern", st="1", key="all"]=process.argv.slice(2);
const RANKS=(process.env.RANKS||"0,3").split(",").map(Number);
(async()=>{ const b=await chromium.launch(L); const VW=+(process.env.VW||900), VH=+(process.env.VH||600); const p=await b.newPage({viewport:{width:VW,height:VH}, deviceScaleFactor:1});
 p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto("file://"+require("path").resolve(__dirname, "../index.html"),{waitUntil:"load"}); await p.waitForTimeout(400);
 await p.evaluate(async({ch,st,cam,dist})=>{ const g=window.__g; g.wipeSave(); g.pin(3); g.pinRun(3); g.start(ch); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0,0); g.aim(0); g.still(true);
   if(+st) g.evolveTo(+st); g.step(480,1/60);            // past the evolution flash and the LEARNED caption
   const s=g.state(), D=dist;
   if(cam==="play") return;                       // the game's own camera, as a player sees it
   if(cam==="snout"){
     // find the snout on the captured mesh and park the camera in front of it
     g.resume(); g.capturePos(); await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))); await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
     const b=g.posOut()||[]; let best=null; for(let i=0;i<b.length/6;i++){ const bx=b.slice(i*6,i*6+6); if(!best||bx[1]>best[1]) best=bx; }
     const sc=2.05*(1+(+st)*.06); const hx=s.x+best[0]*sc, hy=s.y+best[2]*sc, hz=s.z+best[1]*sc;   // aim 0: forward is +z
     g.camLock(hx+1.7*D, hy+.35*D, hz+2.3*D, hx, hy-.1*D, hz-.15*D); return;
   }
   if(cam==="front") g.camLock(s.x+0.6*D, s.y+2.2*D, s.z+5.2*D, s.x, s.y+1.0*D, s.z);
   else if(cam==="side") g.camLock(s.x-5.6*D, s.y+2.0*D, s.z+0.8*D, s.x, s.y+1.0*D, s.z+0.4*D);
   else if(cam==="head") g.camLock(s.x+1.1*D, s.y+1.25*D, s.z+3.0*D, s.x, s.y+1.05*D, s.z+1.1*D);
   else if(cam==="high") g.camLock(s.x-3.0*D, s.y+7.0*D, s.z-5.0*D, s.x, s.y+0.6*D, s.z+1.0*D);
   else g.camLock(s.x-3.2*D, s.y+2.6*D, s.z+3.6*D, s.x+0.4*D, s.y+1.25*D, s.z+0.6*D);
 },{ch,st,cam:process.env.CAM||"close",dist:+(process.env.DIST||1)});
 let prev=0;
 for(const rk of RANKS){
   await p.evaluate(({key,rk,prev})=>{ const g=window.__g; const keys= key==="all" ? ["spinach","boots","heart","clover","plating"] : key.split(",");
     // give(k,0) would CREATE the entry at rank 1: only give when there is a rank to add
     for(const k of keys) if(rk-prev>0) g.give(k, rk-prev); for(let i=0;i<8;i++) g.stepRaw(1/60); },{key,rk,prev});
   prev=rk; await p.waitForTimeout(200);
   if(process.env.BITE){
     // the teeth live inside a closed mouth: film the strike, when the jaw is open
     const n=await p.evaluate(()=>{ const g=window.__g; if(!g.kit().some(k=>k.startsWith("bolt:"))){ g.disarm(); g.give("bolt",0); }
       if(g.enemiesPos().length<3) for(let i=0;i<4;i++) g.spawnAt("brute", -2.2+i*1.5, 6.5);
       const c0=g.fxCounts(); let n=0; while(n<600){ g.stepRaw(1/60); n++; if(g.fxCounts().bolts>c0.bolts) break; }
       for(let i=0;i<9;i++) g.stepRaw(1/60); return { n, pose:g.pose() }; });
     console.log("bite", JSON.stringify(n)); await p.waitForTimeout(60);
   }
   const info=await p.evaluate(()=>({kit:window.__g.kit(), grow:window.__g.grow()}));
   await p.screenshot({path:`${pre}-r${rk}.png`,clip: process.env.VW ? undefined : {x:150,y:60,width:600,height:480}}); console.log(rk, JSON.stringify(info));
 }
 await b.close(); })();
