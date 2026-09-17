// Q4 #3 RE-TAKEN on the shipped build: one bot-driven run, pinned seed 9, the frame
// read at 0:30, 3:00, 7:00, 12:00 and 17:00 - monuments drawn/culled, outcrops,
// and the frame's geometry by distance from the eye (near <40, middle 40-145, far).
const fs=require("fs");
function lp(){for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){try{return require(p)}catch(e){}}process.exit(2)}
const {chromium}=lp();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const SEED=+(process.env.SEED||9), FILE=process.env.FILE||"/home/user/estate-liquidators/bonkhorde/index.html";
(async()=>{
 const b=await chromium.launch(L), pg=await b.newPage({viewport:{width:1280,height:720}});
 const errs=[]; pg.on("pageerror",e=>errs.push(e.message));
 await pg.goto("file://"+FILE); await pg.waitForFunction(()=>!!window.__g,null,{timeout:60000});
 await pg.evaluate((SEED)=>{ const g=window.__g; g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED); g.start("intern"); g.drainPicks(false); g.bot(true); }, SEED);
 const rows=[];
 for(const t of [30,180,420,720,1020]){
   await pg.evaluate((t)=>{ const g=window.__g; let guard=0; while(g.state().t < t && !g.state().over && guard++<200000){ g.step(60,1/60); } }, t);
   await pg.evaluate(()=>window.__g.pause(true));
   await pg.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   const r=await pg.evaluate(()=>{ const g=window.__g, c=g.boxCensus(), s=g.state();
     // the frame by distance from the eye, off the boxes it actually built (capFrame renders once more)
     const eye=g.eye(), B=g.capFrame(); let near=0, mid=0, far=0, sky=0;
     for(const q of B){ const d=Math.hypot(q[0]-eye[0], q[1]-eye[1], q[2]-eye[2]);
       if(d>=170) sky++; else if(d<40) near++; else if(d<145) mid++; else far++; }
     const M=g.monuments(), P={x:s.x,z:s.z};
     return { t:s.t, over:s.over, alive:s.enemies, drawn:c.drawn, horde:c.horde, monsDrawn:c.monsDrawn, monsCulled:c.monsCulled, monuments:c.monuments,
              outDrawn:c.outDrawn, outBoxes:c.outBoxes, passes:c.passes, near, mid, far, sky, total:B.length,
              monsIn40to145: M.filter(m=>{ const d=Math.hypot(m.x-P.x, m.z-P.z); return d>=40 && d<145; }).length,
              nearestMon:+Math.min(...M.map(m=>Math.hypot(m.x-P.x, m.z-P.z))).toFixed(0), lit:M.filter(m=>m.lit).length }; });
   rows.push(r); await pg.evaluate(()=>window.__g.pause(false));
   if(r.over) break;
 }
 console.log("t     alive drawn horde | mons drawn/culled/total  in40-145  nearest lit | out drawn/boxes | near  mid  far  sky  (of total)");
 for(const r of rows) console.log(`${String(r.t).padStart(5)} ${String(r.alive).padStart(5)} ${String(r.drawn).padStart(5)} ${String(r.horde).padStart(5)} | ${String(r.monsDrawn).padStart(4)}/${String(r.monsCulled).padEnd(2)}/${r.monuments}   ${String(r.monsIn40to145).padStart(4)}     ${String(r.nearestMon).padStart(4)}  ${r.lit}  | ${String(r.outDrawn).padStart(3)}/${String(r.outBoxes).padStart(4)} | ${String(r.near).padStart(5)} ${String(r.mid).padStart(5)} ${String(r.far).padStart(4)} ${String(r.sky).padStart(4)}  (${r.total})  mid ${(100*r.mid/r.total).toFixed(1)}%`);
 for(const r of rows) console.log("passes", r.t, JSON.stringify(r.passes));
 console.log("ERRS", errs.length, errs.slice(0,2).join(" | ")); await b.close();
})().catch(e=>{console.error("FAILED",e&&e.stack||e);process.exit(1);});
