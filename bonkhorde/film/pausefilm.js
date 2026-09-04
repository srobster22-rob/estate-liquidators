// The pause menu and the results screen, mid-run, at desktop (1280x800) and phone (390x844).
// node film/pausefilm.js [seed]  -> pause-<viewport>-{pause,end}.png in the working directory
// The run is the autopilot's on the pinned seed to 8:00; the results screen is that run killed on the spot.
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html");
const seed=+(process.argv[2]||41);
(async()=>{ const b=await chromium.launch(L);
 for(const [w,h,nm] of [[1280,800,"desk"],[390,844,"phone"]]){
  const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:1,hasTouch:nm==="phone",isMobile:nm==="phone"});
  p.on("pageerror",e=>console.log("ERR",e.message));
  await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
  const st=await p.evaluate((seed)=>{ const g=window.__g; g.wipeSave(); g.setSave({ up:{ reroll:2, banish:1 } }); g.pin(seed); g.pinRun(seed); g.start("intern"); g.bot(true); g.botHop(true); g.setShake(0); g.runOut(480); g.bot(false); g.pause(true);
    const s=g.state(); return { t:s.t, lvl:s.lvl, kit:g.kit().join(" "), rows:document.querySelectorAll("#psheet .st .row").length, boxes:document.querySelectorAll("#psheet .kit .ks").length }; }, seed);
  console.log(nm,"pause",JSON.stringify(st));
  await p.waitForTimeout(400); await p.screenshot({path:`pause-${nm}-pause.png`});
  const en=await p.evaluate(()=>{ const g=window.__g; g.pause(false); g.hitMe(1e12); g.step(2,1/60); return { over:g.state().over, boxes:document.querySelectorAll("#endBody .kit .ks").length }; });
  console.log(nm,"end",JSON.stringify(en));
  await p.waitForTimeout(5200); await p.screenshot({path:`pause-${nm}-end.png`});
  await p.close();
 }
 await b.close(); })();
