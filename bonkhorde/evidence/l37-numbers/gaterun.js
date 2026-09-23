// numGate on one build. FILE=path/to/index.html [T=seconds of bot play first] node gaterun.js
const fs=require("fs");
function lp(){for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){try{return require(p)}catch(e){}}process.exit(2)}
const {chromium}=lp();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE=process.env.FILE, T=+(process.env.T||0);
(async()=>{
 const b=await chromium.launch(L), pg=await b.newPage({viewport:{width:1280,height:720}});
 const errs=[]; pg.on("pageerror",e=>errs.push(e.message));
 await pg.goto("file://"+FILE); await pg.waitForFunction(()=>!!window.__g,null,{timeout:60000});
 const r=await pg.evaluate((T)=>{ const g=window.__g; g.wipeSave(); g.dev(true); g.pin(9); g.pinRun(9); g.start("intern"); g.god(); g.drainPicks(true); g.freezeEvents(true);
   if(T){ g.bot(true); g.drainPicks(false); let guard=0; while(g.state().t<T && guard++<100000) g.step(60,1/60); g.bot(false); g.drainPicks(true); }
   g.step(30,1/60); g.pause(true);
   const t0=performance.now(); const o=g.numGate(); o.ms=Math.round(performance.now()-t0); return o; }, T);
 console.log(JSON.stringify(r,null,1)); console.log("ERRS",errs.length,errs.slice(0,3).join(" | ")); await b.close();
})().catch(e=>{console.error("FAILED",e&&e.stack||e);process.exit(1);});
