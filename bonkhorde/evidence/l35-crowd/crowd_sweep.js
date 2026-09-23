// L35 measurement: THE CROWD against its own switch. verbRun (levels on, keep on),
// pinned seed, minutes 6-16: mean/peak standing, hurt/min, level, kills, crowd
// tally, and the sim's own cost per step (ms of step() per 1/60 s frame).
const fs=require("fs");
function lp(){for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){try{return require(p)}catch(e){}}process.exit(2)}
const {chromium}=lp();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE=process.env.FILE, SEED=+(process.env.SEED||9);
const ARMS=(process.env.ARMS||"off,1,1.5").split(","), CH=(process.env.CH||"intern,scrap,spark,ox").split(",");
const RATE=process.env.RATE?+process.env.RATE:null, SHARE=process.env.SHARE!==undefined?+process.env.SHARE:null;
(async()=>{
 const b=await chromium.launch(L), pg=await b.newPage({viewport:{width:1280,height:720}});
 const errs=[]; pg.on("pageerror",e=>errs.push(e.message));
 await pg.goto("file://"+FILE); await pg.waitForFunction(()=>!!window.__g,null,{timeout:60000});
 await pg.evaluate(()=>{ const g=window.__g; g.wipeSave(); g.dev(true); g.pause(true); });
 console.log("arm  char    lvl  mean  peak  hurt/min  med/p90 m   kills  paid  free  sent  ms/step");
 for(const arm of ARMS) for(const ch of CH){
   const r=await pg.evaluate(({ch,SEED,arm,RATE,SHARE})=>{ const g=window.__g;
     if(arm==="off") g.crowd(false); else { g.crowd(true); g.crowdTable(+arm); }
     if(RATE!==null) g.crowdRate(RATE); if(SHARE!==null) g.crowdShare(SHARE);
     g.pin(SEED); g.pinRun(SEED);
     const R=g.verbInit(ch, 360, 960, 3, true); let peak=0, ms=0, fr=0, lvl10=null;
     while(true){ const t0=performance.now(), more=g.verbTick(R, 300); ms+=performance.now()-t0; fr+=300;
       const a=g.crowdStat().live; if(a>peak) peak=a; if(lvl10===null && g.state().t>=600) lvl10=g.state().lvl; if(!more) break; }
     const S=g.verbEnd(R), st=g.state(), c=g.crowdStat();
     const frames=Math.round((Math.min(st.t,960)-360)*60/3);
     g.crowd(true); g.crowdTable(); g.crowdRate(200); g.crowdShare(.10);
     return { lvl:st.lvl, lvl10, mean:+(S.bf/Math.max(1,frames)).toFixed(1), peak, hurt:S.hurtPerMin, med:S.med, p90:S.p90, kills:st.kills, paid:c.paid, free:c.free, sent:c.sent, ms:+(ms/fr).toFixed(2) }; }, {ch,SEED,arm,RATE,SHARE});
   console.log(`${arm.padEnd(4)} ${ch.padEnd(7)} ${String(r.lvl).padStart(3)}(${r.lvl10}) ${String(r.mean).padStart(5)} ${String(r.peak).padStart(5)} ${String(r.hurt).padStart(9)}  ${String(r.med).padStart(4)}/${String(r.p90).padEnd(5)} ${String(r.kills).padStart(7)} ${String(r.paid).padStart(5)} ${String(r.free).padStart(5)} ${String(r.sent).padStart(5)}  ${r.ms}`);
 }
 console.log("ERRS",errs.length,errs.slice(0,2).join(" | ")); await b.close();
})().catch(e=>{console.error("FAILED",e&&e.stack||e);process.exit(1);});
