// HOW MUCH OF EACH CREATURE IS INSIDE ITSELF?
//
// Usage: node buried.js [name]   (a char id, a mob key, or boss0..boss3)
//
// Lives in the repo rather than a scratch directory because it is the tool
// that found CERATOP's eyes sealed inside its own skull and TERRAVORE's legs
// sealed inside its own flank, and a verification tool that only exists in
// one container is a verification tool the next session does not have.
// Parts have to interpenetrate or the animal comes apart, but a part that is
// almost entirely inside another part is not a part - it is z-fighting and a
// draw call. For every form: rasterise every box into one occupancy grid that
// COUNTS how many boxes cover each cell, then for each box report the fraction
// of its own cells that some OTHER box also covers.
const fs=require("fs"),path=require("path");
const {chromium}=require("/opt/node22/lib/node_modules/playwright");
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const ONLY = process.argv[2];
(async()=>{
  const b=await chromium.launch(L);
  const p=await b.newPage({viewport:{width:800,height:600}});
  p.on("pageerror",e=>console.log("PAGEERROR",e.message));
  await p.goto("file://"+path.resolve(__dirname, "index.html"),{waitUntil:"load"});
  const out=await p.evaluate(async (ONLY)=>{
    const g=window.__g, frame=()=>new Promise(r=>requestAnimationFrame(()=>r()));
    const res=[];
    // ONE measurement, two rosters. A box with no volume of its own is worse on
    // a trash mob than on the player: there can be four hundred of them on the
    // field, so an invisible box is a draw call paid four hundred times a frame
    // for something nobody can see from any angle.
    const jobs=[];
    for(const ch of g.chars()) for(const st of [0,1,2,3]) jobs.push({ch,st,horde:false});
    for(const k of ["shambler","runner","brute","spitter","skitter","collector"])
      jobs.push({ch:k,st:"",horde:true});
    for(let bi=0;bi<4;bi++) jobs.push({ch:"boss"+bi,st:"",horde:true,boss:bi});
    for(const job of jobs){
      const ch=job.ch, st=job.st;
      if(ONLY && ch!==ONLY) continue;
      {
        let bx, nm;
        if(!job.horde){
          g.wipeSave(); g.start(ch); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
          g.drainPicks(true); g.place(0,0); if(st) g.evolveTo(st);
          g.resume(); g.capturePos(); await frame(); await frame();
          bx=g.posOut(); nm=g.stageNm();
        } else {
          g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true);
          g.freezeEvents(true); g.drainPicks(true); g.setShake(0);
          g.place(0,0); g.aim(0); g.step(20,1/60); g.clearEnemies();
          if(job.boss!==undefined){ g.boss(job.boss); g.step(1/60);
            const bb=g.bossAt(); if(bb){ nm=bb.nm; g.place(bb.x-9,bb.z); g.step(150,1/60); } }
          else { g.spawnAt(ch,0,7); g.step(30,1/60); nm=ch.toUpperCase(); }
          g.resume(); g.captureEnemy(); await frame(); await frame();
          bx=g.enemyPos();
        }
        if(!bx){ res.push({ch,st,nm:nm||"?"}); continue; }
        const n=bx.length/6;
        let lo=[9,9,9], hi=[-9,-9,-9];
        for(let i=0;i<bx.length;i+=6) for(let k=0;k<3;k++){
          lo[k]=Math.min(lo[k], bx[i+k]-bx[i+3+k]); hi[k]=Math.max(hi[k], bx[i+k]+bx[i+3+k]); }
        const N=80, cell=[0,1,2].map(k=>Math.max(1e-4,(hi[k]-lo[k])/N));
        const cnt=new Uint8Array(N*N*N);
        const span=(i)=>{
          const a0=[0,1,2].map(k=>Math.max(0, Math.floor((bx[i+k]-bx[i+3+k]-lo[k])/cell[k])));
          const a1=[0,1,2].map(k=>Math.min(N-1, Math.floor((bx[i+k]+bx[i+3+k]-lo[k])/cell[k])));
          return [a0,a1];
        };
        for(let i=0;i<bx.length;i+=6){ const [a0,a1]=span(i);
          for(let x=a0[0];x<=a1[0];x++) for(let y=a0[1];y<=a1[1];y++)
            for(let z=a0[2];z<=a1[2];z++){ const q=(x*N+y)*N+z; if(cnt[q]<255) cnt[q]++; } }
        // What matters is not how much of a part is shared - parts are SUPPOSED
        // to interpenetrate, and a chamfer is three boxes deliberately inside
        // each other - it is whether the part contributes any volume that is
        // ITS OWN. A box with no exclusive cells is invisible: it cannot be
        // seen from any angle, it costs a draw, and it z-fights whatever
        // contains it. That is the "glitchy" in the report.
        let sum=0, deep=0, worst=[];
        for(let i=0;i<bx.length;i+=6){ const [a0,a1]=span(i);
          let tot=0, own=0;
          for(let x=a0[0];x<=a1[0];x++) for(let y=a0[1];y<=a1[1];y++)
            for(let z=a0[2];z<=a1[2];z++){ tot++; if(cnt[(x*N+y)*N+z]===1) own++; }
          const f = tot ? own/tot : 0;
          sum += f; if(f < .02) deep++;
          worst.push({ i:i/6, f:+f.toFixed(3),
                       sz:[bx[i+3],bx[i+4],bx[i+5]].map(v=>+v.toFixed(3)) });
        }
        worst.sort((a,b)=>a.f-b.f);
        res.push({ ch, st, nm, n, mean:+(sum/n).toFixed(3), deep,
                   top: worst.slice(0,3) });
      }
    }
    return res;
  }, ONLY);
  console.log("  FORM                    boxes   mean-own   invisible (no volume of its own)");
  for(const r of out) console.log(
    `  ${(r.ch+(r.st===""?"":" st"+r.st)).padEnd(12)}${(r.nm||"?").padEnd(14)}${String(r.n||0).padStart(5)}` +
    `${String(r.mean===undefined?"n/a":r.mean).padStart(13)}${String(r.deep||0).padStart(13)}` +
    (r.deep ? "   " + r.top.filter(t=>t.f<.02).slice(0,3).map(t=>`i${t.i}(${t.sz.join(",")})`).join(" ") : ""));
  await b.close();
})();
