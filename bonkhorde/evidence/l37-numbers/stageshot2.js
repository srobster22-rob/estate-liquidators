// The numGate staging as a picture, SEEDED like the gate's first pulse (mulberry32,
// seed 1000), both arms on the same seed: the same bodies, the same jitter. Reports
// what each arm drew, measured the way numGate measures it.
const fs=require("fs");
function lp(){for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){try{return require(p)}catch(e){}}process.exit(2)}
const {chromium}=lp();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE=process.env.FILE, OUT=process.env.OUT, SEED=+(process.env.SEED||1000);
(async()=>{
 const b=await chromium.launch(L), pg=await b.newPage({viewport:{width:1280,height:720}});
 await pg.goto("file://"+FILE); await pg.waitForFunction(()=>!!window.__g,null,{timeout:60000});
 await pg.evaluate(()=>{ const g=window.__g; g.wipeSave(); g.dev(true); g.pin(9); g.pinRun(9); g.start("intern"); g.god(); g.drainPicks(true); g.freezeEvents(true); g.step(30,1/60); g.pause(true); });
 const rows={};
 for(const arm of ["on","off"]){
   const r=await pg.evaluate(({arm,SEED})=>{ const E=(0,eval), g=window.__g;
     g.numSort(arm==="on"); g.numDepth(arm==="on"); g.numJump(arm!=="on");
     const mr=Math.random; let sd=SEED>>>0, pooled=0;
     Math.random=()=>{ sd=(sd+0x6D2B79F5)>>>0; let t=sd; t=Math.imul(t^t>>>15,t|1); t^=t+Math.imul(t^t>>>7,t|61); return ((t^t>>>14)>>>0)/4294967296; };
     try{
     E(`enemies.length=0; corpses.length=0; nums.length=0; P.x=0; P.z=0; P.y=groundY(0,0); P.vx=0; P.vz=0; camYaw=0; camLock=null; camAnchor=[P.x,P.y,P.z]; shake=0; flash=0;
        for(let i=0;i<NUM_STAGE[0]*NUM_STAGE[1];i++){ const e=spawnEnemy("shambler", P.x+(i%NUM_STAGE[1]-(NUM_STAGE[1]-1)/2)*1.6, P.z+18+(i/NUM_STAGE[1]|0)*2); if(e){ e.hp=e.maxhp=1e12; e.rise=0; e.burrow=false; } }
        rebuildGrid(); render(); render(); const c0=P.crit; P.crit=1; damageArea(P.x, P.z+26, 12, 10, 0); P.crit=c0;`);
     pooled=E("nums.length"); E("render()");
     } finally { Math.random=mr; }
     const cv=E("cv"), project=E("project"), enemies=E("enemies"), g2=E("g2");
     // both arms read what numPlace laid: with the knobs flipped it places everything, at full size
     const boxes=E("numLast").map(L=>L.box);
     const meets=(a,b)=>Math.min(a[2],b[2])-Math.max(a[0],b[0])>0&&Math.min(a[3],b[3])-Math.max(a[1],b[1])>0;
     let pairs=0; for(let i=0;i<boxes.length;i++) for(let j=i+1;j<boxes.length;j++) if(meets(boxes[i],boxes[j])) pairs++;
     const C=2,gw=Math.ceil(cv.width/C),gh=Math.ceil(cv.height/C),gr=new Uint8Array(gw*gh);
     for(const q of boxes) for(let y=Math.max(0,q[1]/C|0);y<=Math.min(gh-1,q[3]/C|0);y++) for(let x=Math.max(0,q[0]/C|0);x<=Math.min(gw-1,q[2]/C|0);x++) gr[y*gw+x]=1;
     let ink=0; for(const v of gr) ink+=v; ink*=C*C;
     let un=0,of=0; for(const e of enemies){ if(e.dead) continue; const s=project(e.x,e.y+e.def.h*e.sz*.5,e.z);
       if(!s||s[0]<0||s[0]>cv.width||s[1]<0||s[1]>cv.height) continue; of++; if(boxes.some(q=>s[0]>=q[0]&&s[0]<=q[2]&&s[1]>=q[1]&&s[1]<=q[3])) un++; }
     document.getElementById("paused").style.visibility="hidden";
     return { pooled, drawn:boxes.length, pairs, ink, under:un, of }; }, {arm,SEED});
   await pg.screenshot({path:`${OUT}/stage-${arm}.png`});
   await pg.evaluate(()=>{ document.getElementById("paused").style.visibility=""; });
   rows[arm]=r; console.log(arm, JSON.stringify(r));
 }
 fs.writeFileSync(`${OUT}/stage.json`, JSON.stringify(rows,null,1));
 await b.close();
})().catch(e=>{console.error("FAILED",e&&e.stack||e);process.exit(1);});
