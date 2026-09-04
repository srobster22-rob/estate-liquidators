// A CACHE opened with an evolution ready, photographed at desktop (1280x800) and phone (390x844): the panel under its CACHE banner.
// node film/cachefilm.js  -> cache-<viewport>.png in the working directory
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html");
(async()=>{ const b=await chromium.launch(L);
 for(const [w,h,nm] of [[1280,800,"desk"],[390,844,"phone"]]){
  const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:1,hasTouch:nm==="phone",isMobile:nm==="phone"});
  p.on("pageerror",e=>console.log("ERR",e.message));
  await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
  const r=await p.evaluate(()=>{ const g=window.__g;
    g.drainPicks(true); g.wipeSave(); g.pin(7); g.pinRun(7); g.start("intern"); g.god(); g.freezeEvents(true); g.setShake(0);
    g.step(240, 1/60);                                    // four seconds: a horde around
    g.give("bat", 3); g.give("spinach", 3);               // MEGABONK is ready
    g.drainPicks(false); const s0=g.state(); g.spawnEvent("cache", s0.x, s0.z); for(let i=0;i<3;i++) g.stepRaw(1/60);   // raw: g.step() would auto-pick the hand
    const s=g.state(), d=g.draft(); return { picking:s.picking, title:d.title, cache:d.cache, hand:g.hand().map(o=>o.nm).join("|") }; });
  await p.waitForTimeout(400); await p.screenshot({path:`cache-${nm}.png`}); console.log(nm, JSON.stringify(r));
  await p.close();
 }
 await b.close(); })();
