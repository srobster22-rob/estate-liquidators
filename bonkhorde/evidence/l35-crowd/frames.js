// Q4's protocol, crowd on vs off on one build: seed-9 bot run (god, so every mark is
// reached), frames at 0:30/3:00/7:00/12:00/17:00, paused INSIDE the same evaluate that
// stepped so the page's own loop cannot move the sim between burst and shot.
const fs=require("fs");
function lp(){for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){try{return require(p)}catch(e){}}process.exit(2)}
const {chromium}=lp();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE=process.env.FILE, OUT=process.env.OUT, ON=process.env.ON!=="0", SEED=+(process.env.SEED||9);
(async()=>{
 const b=await chromium.launch(L), pg=await b.newPage({viewport:{width:1280,height:720}});
 const errs=[]; pg.on("pageerror",e=>errs.push(e.message));
 await pg.goto("file://"+FILE); await pg.waitForFunction(()=>!!window.__g,null,{timeout:60000});
 await pg.evaluate(({SEED,ON})=>{ const g=window.__g; g.wipeSave(); g.dev(true); if(g.crowd) g.crowd(ON); g.pin(SEED); g.pinRun(SEED); g.start("intern"); g.god(); g.drainPicks(false); g.bot(true); g.pause(true); }, {SEED,ON});
 console.log(`crowd ${ON?"ON":"OFF"}   t  lvl  alive onScreen | frame horde (share) | sky props out mons marks zones player shots pops gems corpses`);
 for(const t of [30,180,420,720,1020]){
   await pg.evaluate((t)=>{ const g=window.__g; let guard=0; while(g.state().t < t && !g.state().over && guard++<400000){ g.step(60,1/60); } g.pause(true); }, t);
   await pg.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   const r=await pg.evaluate(()=>{ const g=window.__g, c=g.boxCensus(), s=g.state(), p=c.passes;
     return { t:s.t, lvl:s.lvl, alive:c.enemies, on:c.enemies - c.culled, drawn:c.drawn, horde:c.horde, p }; });
   await pg.evaluate(()=>{ const p=document.getElementById("paused"); if(p) p.style.visibility="hidden"; });
   await pg.screenshot({ path:`${OUT}/t${String(t).padStart(4,"0")}.png` });
   await pg.evaluate(()=>{ const p=document.getElementById("paused"); if(p) p.style.visibility=""; });
   const p=r.p;
   console.log(`${String(r.t).padStart(12)} ${String(r.lvl).padStart(4)} ${String(r.alive).padStart(6)} ${String(r.on).padStart(8)} | ${String(r.drawn).padStart(5)} ${String(r.horde).padStart(5)} (${(100*r.horde/r.drawn).toFixed(0)}%) | ${p.sky} ${p.props} ${p.outcrops} ${p.monuments} ${p.marks} ${p.zones} ${p.player} ${p.shots} ${p.pops} ${p.gems} ${p.corpses}`);
 }
 console.log("ERRS",errs.length,errs.slice(0,2).join(" | ")); await b.close();
})().catch(e=>{console.error("FAILED",e&&e.stack||e);process.exit(1);});
