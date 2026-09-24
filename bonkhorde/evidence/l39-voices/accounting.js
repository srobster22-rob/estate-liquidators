// WHERE THE BYTES ARE: after each runOut trial under a mutant, V8's own accounting -
// used and committed heap, embedder heap, ArrayBuffer backing stores (Runtime.getHeapUsage),
// performance.memory, and the renderer's RSS from outside.
const fs = require("fs"), path = require("path"), { execSync } = require("child_process");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox","--enable-precise-memory-info","--js-flags=--expose-gc"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor"); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, "_hang." + process.pid + ".html"); fs.writeFileSync(TMP, src);
const rss = () => { try { const o = execSync("ps -eo rss,args | grep 'type=renderer' | grep -v grep", { encoding:"utf8" }); let mx = 0; for(const l of o.trim().split("\n")){ const r = +l.trim().split(/\s+/)[0]; if(r > mx) mx = r; } return Math.round(mx/1024); } catch(e){ return -1; } };
const MB = x => x == null ? "?" : (x / 1048576).toFixed(0);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const cdp = await pg.context().newCDPSession(pg);
  const acct = async (label) => { const h = await cdp.send("Runtime.getHeapUsage"); const pm = await pg.evaluate(() => ({ used:performance.memory.usedJSHeapSize, total:performance.memory.totalJSHeapSize, limit:performance.memory.jsHeapSizeLimit }));
    console.log(`${label.padEnd(26)} rss ${String(rss()).padStart(5)} MB | v8 used ${MB(h.usedSize)} committed ${MB(h.totalSize)} (limit ${MB(pm.limit)}) | embedder ${MB(h.embedderHeapUsedSize)} | backing stores ${MB(h.backingStorageSize)} MB`); };
  await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.pin(999); g.pinRun(555); });
  await acct("fresh");
  for(const name of ["a", "b"]){
    const t0 = Date.now();
    const res = await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.start("intern"); g.bot(true); const st = g.runOut(); return `${st.t.toFixed(2)}/${st.lvl}/${st.kills}`; });
    await acct(`after trial ${name} (${res}, ${((Date.now()-t0)/1000).toFixed(0)} s)`);
    await pg.evaluate(() => { window.gc(); window.gc(); }); await acct("  after gc() x2");
    await cdp.send("HeapProfiler.collectGarbage"); await new Promise(r => setTimeout(r, 3000)); await acct("  after collectGarbage + 3 s");
  }
  fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
