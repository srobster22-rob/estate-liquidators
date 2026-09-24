// SECTION 22h's det STEP, as the suite runs it: six trials, each wipeSave/start/bot/runOut
// inside one evaluate, under a mutant - with every chrome process's RSS sampled from
// outside every 5 s while the page is busy. Stops at 8 GB.
const fs = require("fs"), path = require("path"), { execSync } = require("child_process");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox","--enable-precise-memory-info"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor"); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
const rss = () => { try { const o = execSync("ps -eo rss,args | grep chrome-linux/chrome | grep -v grep", { encoding:"utf8" }); let mx = 0; for(const l of o.trim().split("\n")){ const r = +l.trim().split(/\s+/)[0]; if(r > mx) mx = r; } return Math.round(mx/1024); } catch(e){ return -1; } };
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message)); pg.on("crash", () => console.log("PAGE CRASHED"));
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.pin(999); g.pinRun(555); });
  const plan = [["a", null], ["b", null], ["c0", null], ["c", () => window.__g.pinRun(556)], ["d", () => { window.__g.pin(null); window.__g.pinRun(null); }], ["e", null]];
  console.log((MUT || "clean") + ": trial | result t/lvl/kills | wall s | rss MB start -> peak -> end | js heap MB");
  for(const [name, pre] of plan){
    if(pre) await pg.evaluate(pre);
    const r0 = rss(); let peak = r0; const t0 = Date.now();
    const timer = setInterval(() => { const r = rss(); if(r > peak) peak = r; if(r > 8000){ console.log(`STOP: rss ${r} MB in trial ${name} at ${((Date.now()-t0)/1000).toFixed(0)} s`); process.exit(3); } }, 5000);
    let res;
    try { res = await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.start("intern"); g.bot(true); const st = g.runOut();
      return { s:`${st.t.toFixed(2)}/${st.lvl}/${st.kills}`, heap:performance.memory ? Math.round(performance.memory.usedJSHeapSize/1048576) : -1 }; }); }
    catch(e){ clearInterval(timer); console.log(`trial ${name}: evaluate failed: ${String(e.message).slice(0, 120)} (rss peak ${peak} MB)`); break; }
    clearInterval(timer);
    console.log(`${name.padEnd(2)} | ${res.s.padEnd(20)} | ${((Date.now()-t0)/1000).toFixed(0).padStart(4)} | ${r0} -> ${peak} -> ${rss()} | ${res.heap}`);
  }
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
