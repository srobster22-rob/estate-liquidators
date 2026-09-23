// Section 96's early leg, exactly as the suite runs it: the mean horde share of
// the drawn boxes over seven settled frames 4:30-6:00, per seed.
const fs=require("fs");
function lp(){for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){try{return require(p)}catch(e){}}process.exit(2)}
const {chromium}=lp();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE=process.env.FILE, SEEDS=(process.env.SEEDS||"9,3").split(",").map(Number), TAG=process.env.TAG||"";
(async()=>{
 const b=await chromium.launch(L), pg=await b.newPage({viewport:{width:1280,height:760}});
 const errs=[]; pg.on("pageerror",e=>errs.push(e.message));
 await pg.goto("file://"+FILE); await pg.waitForFunction(()=>!!window.__g,null,{timeout:60000});
 for(const seed of SEEDS){
  const r=await pg.evaluate((seed)=>{ const g=window.__g;
    const settled=()=>{ g.pause(true); let ms=performance.now(); for(let i=0;i<50;i++) g.tick(ms+=16); const c=g.boxCensus(); g.pause(false); return c; };
    g.wipeSave(); g.dev(true); g.pin(seed); g.pinRun(seed); g.start("intern"); g.god(); g.bot(true); g.drainPicks(true);
    g.step(270*60,1/60);
    const shares=[]; let c=null, alive=[]; const P={};
    for(let k=0;k<7;k++){ if(k) g.step(15*60,1/60); c=settled(); shares.push(+(c.horde/c.drawn).toFixed(3)); for(const k in c.passes) P[k]=(P[k]||0)+c.passes[k]/c.drawn/7; alive.push(g.hordeFlow().alive); }
    const cs=g.crowdStat();
    const top=Object.entries(P).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([k,v])=>k+" "+v.toFixed(3)).join(", "); return { top, seed, mean:+(shares.reduce((a,b)=>a+b,0)/shares.length).toFixed(3), shares, alive, drawn:c.enemies-c.culled, boxes:c.drawn, sent:cs.sent, table:cs.table, lvl:g.state().lvl };
  }, seed);
  console.log(TAG, JSON.stringify(r));
 }
 console.log("ERRS",errs.length,errs.slice(0,2).join(" | ")); await b.close();
})().catch(e=>{console.error("FAILED",e&&e.stack||e);process.exit(1);});
