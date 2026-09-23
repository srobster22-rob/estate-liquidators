// numGate over N seed bases on one build: the spread of the crowd clause. FILE=... N=40 node gatedist.js
const fs=require("fs");
function lp(){for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){try{return require(p)}catch(e){}}process.exit(2)}
const {chromium}=lp();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE=process.env.FILE, N=+(process.env.N||30);
(async()=>{
 const b=await chromium.launch(L), pg=await b.newPage({viewport:{width:1280,height:720}});
 const errs=[]; pg.on("pageerror",e=>errs.push(e.message));
 await pg.goto("file://"+FILE); await pg.waitForFunction(()=>!!window.__g,null,{timeout:60000});
 const r=await pg.evaluate((N)=>{ const g=window.__g; g.wipeSave(); g.dev(true); g.pin(9); g.pinRun(9); g.start("intern"); g.god(); g.drainPicks(true); g.freezeEvents(true);
   g.step(30,1/60); g.pause(true);
   const rows=[]; for(let i=0;i<N;i++){ const o=g.numGate(1000+i*7); const p=o.pulse;
     rows.push({ok:o.ok, bad:o.bad.map(x=>x.slice(0,60)), shown:p.shown, aU:p.under.n, bU:p.under.of?p.off.under.n:0, aI:p.ink, bI:p.off.ink, bS:p.off.shown}); }
   const d1=JSON.stringify(g.numGate(1000).pulse), d2=JSON.stringify(g.numGate(1000).pulse); rows.push({det:d1===d2, d1:d1.slice(0,160)}); return rows; }, N);
 for(const x of r) console.log(JSON.stringify(x));
 const q=(k)=>{const v=r.map(x=>x[k]).sort((a,b)=>a-b);return `${k} min ${v[0]} med ${v[v.length>>1]} max ${v[v.length-1]}`};
 console.log(["shown","aU","bU","aI","bI"].map(q).join(" | "));
 const det=r.pop(); console.log("DETERMINISTIC",det.det,det.d1); const rat=r.map(x=>x.aU/x.bU).sort((a,b)=>a-b), ri=r.map(x=>x.aI/x.bI).sort((a,b)=>a-b);
 console.log("under ratio min",rat[0].toFixed(3),"med",rat[rat.length>>1].toFixed(3),"max",rat[rat.length-1].toFixed(3),"| ink ratio min",ri[0].toFixed(3),"max",ri[ri.length-1].toFixed(3),"| fails",r.filter(x=>!x.ok).length);
 console.log("ERRS",errs.length,errs.slice(0,3).join(" | ")); await b.close();
})().catch(e=>{console.error("FAILED",e&&e.stack||e);process.exit(1);});
