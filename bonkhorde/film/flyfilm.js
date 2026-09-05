// Flight, driven: a form with wings hops, holds JUMP, hovers until the meter is dry, lands and refills.
// node film/flyfilm.js  -> fly-<t>.png at 0.5 s, 1.5 s, 3.0 s of hover, 1.5 s after landing; a trace every 10 frames
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html"), OUT=process.env.OUT||".";
(async()=>{ const b=await chromium.launch(L); const p=await b.newPage({viewport:{width:1280,height:800}}); p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
 const setup=await p.evaluate(()=>{ const g=window.__g; g.drainPicks(true); g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.setShake(0); g.drainPicks(true);
   let n=0; while(!g.wings().can && n<6){ document.getElementById("dvEvo").click(); n++; g.step(30,1/60); } g.clearEnemies(); g.place(0,0); g.aim(0);
   const pp=g.state(); for(let i=0;i<8;i++){ const a=(i/8)*Math.PI*2; g.spawnAt("shambler", pp.x+Math.sin(a)*4, pp.z+Math.cos(a)*4); }
   return { evolved:n, form:g.stageNm(), wings:g.wings() }; });
 console.log("setup", JSON.stringify(setup));
 const rows=[]; const snap=async tag=>{ await p.evaluate(()=>{ window.__g.pause(true); document.getElementById("paused").style.display="none"; }); await p.waitForTimeout(250); await p.screenshot({path:`${OUT}/fly-${tag}.png`}); await p.evaluate(()=>{ document.getElementById("paused").style.display=""; window.__g.resume(); }); };
 const trace=(tag)=>p.evaluate((tag)=>{ const g=window.__g, w=g.wings(), s=g.state(), h=g.hop(); return { tag, t:+s.t.toFixed(2), alt:w.alt, wing:w.wing, fly:w.fly, air:w.air, aloft:w.aloft, hop:h.n, hp:Math.round(s.hp), enemies:s.enemies }; }, tag);
 // hop, then hold
 await p.evaluate(()=>{ const g=window.__g; g.jump(); for(let i=0;i<5;i++) g.stepRaw(1/60); g.holdJump(true); });
 rows.push(await trace("hold+0"));
 for(let k=1;k<=42;k++){ await p.evaluate(()=>{ const g=window.__g; for(let i=0;i<10;i++) g.stepRaw(1/60); }); rows.push(await trace(`hold+${(k*10/60).toFixed(2)}s`)); if(k===3) await snap("0.5s"); if(k===9) await snap("1.5s"); if(k===18) await snap("3.0s"); if(k===25) await snap("glide4.2s"); if(k===36) await snap("relift6.0s"); }
 await p.evaluate(()=>{ window.__g.holdJump(false); });
 for(let k=1;k<=24;k++){ await p.evaluate(()=>{ const g=window.__g; for(let i=0;i<10;i++) g.stepRaw(1/60); }); rows.push(await trace(`release+${(k*10/60).toFixed(2)}s`)); if(k===9) await snap("landed1.5s"); }
 for(const r of rows) console.log(JSON.stringify(r));
 await b.close(); })();
