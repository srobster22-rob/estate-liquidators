// The front end, photographed: PLAY on a fresh save, PLAY with a locked creature picked, POWER UP, COLLECTION, UNLOCKS - at desktop (1280x800) and phone (390x844).
// node film/menufilm.js  -> menu-<viewport>-<tab>.png in the working directory
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
  const shot=async(name,fn,arg)=>{ const st=await p.evaluate(fn,arg); await p.waitForTimeout(700); await p.screenshot({path:`menu-${nm}-${name}.png`}); console.log(nm, name, JSON.stringify(st)); };
  // a fresh save: PLAY, THE INTERN's line picked
  await shot("play-fresh",()=>{ const g=window.__g; g.wipeSave(); g.menuTab("play"); return g.menuState(); });
  // a veteran: coins, a clear, some ranks, a locked creature picked
  await shot("play-locked",()=>{ const g=window.__g; g.setSave({ coins:1480, runs:14, best:1040, wins:1, kills:2600, dist:5200, deaths:9, up:{ hp:3, dmg:2, spd:1, mag:2, reroll:1 } }); g.checkUnlocks(); g.menuPick("surge"); return g.menuState(); });
  await shot("play-vet",()=>{ const g=window.__g; g.menuPick("scrap"); return g.menuState(); });
  await shot("shop",()=>{ const g=window.__g; g.menuTab("shop"); return { tiles:document.querySelectorAll("#shop .up").length }; });
  await shot("collection",()=>{ const g=window.__g; g.menuTab("coll"); return { tiles:document.querySelectorAll(".ce").length }; });
  await shot("unlocks",()=>{ const g=window.__g; g.menuTab("locks"); return { left:document.querySelectorAll("#locks .lk").length }; });
  await p.close();
 }
 await b.close(); })();
