// WHO ALLOCATED WHAT IS STILL ALIVE: V8's sampling heap profiler over one runOut trial
// under a mutant (live objects only, with the allocating call frames), aggregated by
// function, top sites by retained bytes. MUT unset = the clean build.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox","--enable-precise-memory-info"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const blk = t.slice(t.lastIndexOf("{", i), t.indexOf("}", t.indexOf("to:", i)) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor"); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const cdp = await pg.context().newCDPSession(pg);
  await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.pin(999); g.pinRun(555); });
  await cdp.send("HeapProfiler.enable");
  await cdp.send("HeapProfiler.startSampling", { samplingInterval:32768, includeObjectsCollectedByMajorGC:true, includeObjectsCollectedByMinorGC:true });
  const t0 = Date.now();
  const res = await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.start("intern"); g.bot(true); const st = g.runOut();
    return { s:`${st.t.toFixed(2)}/${st.lvl}/${st.kills}`, heap:performance.memory ? Math.round(performance.memory.usedJSHeapSize/1048576) : -1 }; });
  const { profile } = await cdp.send("HeapProfiler.stopSampling");
  // aggregate self sizes by allocating function, and by the two frames above it
  const byFn = new Map(), byPath = new Map(); let total = 0;
  const walk = (node, stack) => { const f = node.callFrame, name = `${f.functionName || "(anon)"}:${f.lineNumber + 1}`; const s = [...stack, name];
    if(node.selfSize){ total += node.selfSize; byFn.set(name, (byFn.get(name) || 0) + node.selfSize);
      const p = s.slice(-3).join(" < "); byPath.set(p, (byPath.get(p) || 0) + node.selfSize); }
    for(const c of node.children || []) walk(c, s); };
  walk(profile.head, []);
  const MB = x => (x / 1048576).toFixed(1);
  console.log(`${MUT || "clean"}: trial ${res.s} in ${((Date.now()-t0)/1000).toFixed(0)} s, js heap ${res.heap} MB, sampled allocated (churn) ${MB(total)} MB`);
  console.log("  by allocating function:"); for(const [k, v] of [...byFn.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12)) console.log(`    ${MB(v).padStart(7)} MB  ${k}`);
  console.log("  by call path (innermost last):"); for(const [k, v] of [...byPath.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8)) console.log(`    ${MB(v).padStart(7)} MB  ${k}`);
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
