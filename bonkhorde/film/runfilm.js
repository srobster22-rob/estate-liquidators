// A whole run from the player's seat: the autopilot on a pinned seed, photographed at the moments that matter.
// node film/runfilm.js [seed]  -> film-<seed>-<stop>.png in the working directory
// The pauses between marks freeze the hop, so this run is not frame-for-frame the bench's run
// of the same seed - it is a photograph of a plausible one. The draft frame comes from a SEPARATE short run on the same seed: dealing a hand inside the
// filmed run changed its picks (it once handed the bot GLASS into a finale death, R257).
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html");
const seed=+(process.argv[2]||33);
(async()=>{ const b=await chromium.launch(L);
 const shot=async(p,name,setup,arg)=>{ const st=await p.evaluate(setup,arg); await p.waitForTimeout(350); await p.screenshot({path:`film-${seed}-${name}.png`}); console.log(name, JSON.stringify(st)); return st; };
 // the run itself, untouched
 const p=await b.newPage({viewport:{width:1280,height:800}}); p.on("pageerror",e=>console.log("ERR",e.message));
 await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
 await p.evaluate((seed)=>{ const g=window.__g; g.wipeSave(); g.pin(seed); g.pinRun(seed); g.start("intern"); g.bot(true); g.botHop(true); g.setShake(0); },seed);
 const stops=[["t01",60],["t05-boss",312],["t08",480],["t10-boss",612],["t15-boss",915],["t19",1150],["t20-finale",1215]];
 for(const [name,t] of stops){
   const st=await p.evaluate((t)=>{ const g=window.__g; g.runOut(t); const s=g.state(); const bs=g.bossAt(); g.pause(true); document.getElementById("paused").style.display="none";
     return { t:s.t, lvl:s.lvl, hp:Math.round(s.hp), enemies:s.enemies, kit:g.kit().join(" "), boss: bs?{nm:bs.nm,hp:Math.round(bs.hp),d:Math.round(Math.hypot(bs.x-s.x,bs.z-s.z))}:null, over:s.over, won:s.won }; },t);
   await p.waitForTimeout(350); await p.screenshot({path:`film-${seed}-${name}.png`}); console.log(name, JSON.stringify(st));
   if(st.over) break;
   await p.evaluate(()=>{ window.__g.resume(); });
 }
 await p.close();
 // the draft, on its own run of the same seed, dealt at 8:00 and left on screen
 const q=await b.newPage({viewport:{width:1280,height:800}});
 await q.goto(FILE,{waitUntil:"load"}); await q.waitForTimeout(400);
 await shot(q,"t08-draft",(seed)=>{ const g=window.__g; g.wipeSave(); g.pin(seed); g.pinRun(seed); g.start("intern"); g.bot(true); g.botHop(true); g.setShake(0); g.runOut(480); g.drainPicks(false); g.xp(400); g.stepRaw(1/60); const s=g.state(); return { t:s.t, lvl:s.lvl, picking:s.picking, kit:g.kit().join(" ") }; }, seed);
 await b.close(); })();
