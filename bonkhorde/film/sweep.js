// Robustness sweep: every creature, one seed each, a whole autopilot run, every page error captured.
// node film/sweep.js [seedBase]  -> one line per creature: time, level, outcome, kit size, evolutions reached, errors
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE="file://"+path.resolve(__dirname, "../index.html"); const BASE=+(process.argv[2]||100);
(async()=>{ const b=await chromium.launch(L);
 const chars=["intern","scrap","spark","ox","ghoul","accnt","twin","surge","pyre"];
 for(let i=0;i<chars.length;i++){
  const p=await b.newPage({viewport:{width:1280,height:800}}); const errs=[];
  p.on("pageerror",e=>errs.push(e.message)); p.on("console",m=>{ if(m.type()==="error" && !/AudioContext/.test(m.text())) errs.push("console: "+m.text()); });
  await p.goto(FILE,{waitUntil:"load"}); await p.waitForTimeout(400);
  const r=await p.evaluate(([id,seed])=>{ const g=window.__g; g.wipeSave(); g.unlockAll(); g.setSave({up:{hp:3,dmg:3,spd:3,mag:3,cd:3,crit:3,armor:3,reroll:2,banish:1}}); g.pin(seed); g.pinRun(seed); g.start(id); g.bot(true); g.botHop(true); g.setShake(0);
    g.runOut(); const s=g.state(); return { t:Math.round(s.t), lvl:s.lvl, won:s.won, why:s.why, kit:g.kit().length, caches:g.state().caches, evos:JSON.stringify(g.saveState().evos||{}), end:document.getElementById("endBody").textContent.replace(/\s+/g," ").slice(0,60) }; }, [chars[i], BASE+i]);
  console.log(chars[i], JSON.stringify(r), "errors:", errs.length, errs.slice(0,2).join(" | "));
  await p.close();
 }
 await b.close(); })();
