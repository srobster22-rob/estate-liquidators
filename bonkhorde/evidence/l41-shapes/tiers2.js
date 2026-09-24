// WHICH TIER THE HOT FUNCTIONS RUN IN, AS PLAYED. The page's own frame loop is cut (its
// requestAnimationFrame made a no-op after load, since __g.step() un-pauses the game), the
// settled pinned run is stepped at sixty steps a second of wall time, and every 250 ms
// %GetOptimizationStatus is read for the hot functions - so the answer is the share of
// wall time each spends in TurboFan, Maglev, the baseline or the interpreter. The deopt
// trace over the same window (DEBUG=pw:browser) says why they leave the top tier, and the
// sampling heap profiler says what the step allocates in this regime.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox","--js-flags=--allow-natives-syntax --trace-deopt"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde";
const AT = +(process.env.AT || 300), SECS = +(process.env.SECS || 20), SEED = +(process.env.SEED || 9), WARM = +(process.env.WARM || 5);
const FNS = (process.env.FNS || "step,updateEnemies,walk,groundY,botVector,near,wardPass,updateGems,hitNear,nearestCells,confineIn,sepAcc,RELIEF,BASE_Y,waterDepth").split(",");
// V8 14 (Chrome 141): the enum without kAlwaysOptimize
const BITS = { 1:"fn", 2:"NeverOpt", 4:"MaybeDeopted", 8:"Optimized", 16:"Maglev", 32:"TurboFan", 64:"Interpreted", 128:"MarkedForOpt", 256:"MarkedForConcOpt", 512:"OptimizingConc", 1024:"Executing", 2048:"TopTF", 4096:"Lite", 8192:"MarkedForDeopt", 16384:"Baseline", 32768:"TopInterp", 65536:"TopBaseline", 131072:"Lazy", 262144:"TopMaglev" };
const tier = (s) => (s & 32) ? "TF" : (s & 16) ? "Maglev" : (s & 16384) ? "Baseline" : (s & 64) ? "Interp" : (s & 131072) ? "Lazy" : (s & 8192) ? "MarkedDeopt" : (s === 1 ? "none" : "other:" + s);
const src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const cdp = await pg.context().newCDPSession(pg);
  await pg.evaluate(({ AT, SEED }) => { window.requestAnimationFrame = () => 0;    // the page's loop ends with its current frame
    const g = window.__g; g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED);
    g.start("intern"); g.god(); g.drainPicks(true); g.bot(true);
    let guard = 0; while(g.state().t < AT && guard++ < 200000) g.step(30, 1/60); }, { AT, SEED });
  const pace = (secs, fns) => pg.evaluate(({ secs, fns }) => new Promise(res => { const g = window.__g, E = (0, eval), st = E("(f) => %GetOptimizationStatus(f)");
    const samples = {}; for(const n of fns) samples[n] = []; let n = 0, last = 0; const t0 = performance.now(), T0 = g.state().t;
    const tick = () => { g.step(1, 1/60); n++; const now = performance.now();
      if(now - last >= 250){ last = now; for(const k of fns){ let f; try { f = E(k); } catch(e){ continue; } if(typeof f === "function") samples[k].push(st(f)); } }
      if(now - t0 < secs * 1000) setTimeout(tick, 16); else res({ n, ms:now - t0, simT:g.state().t - T0, samples }); }; tick(); }), { secs, fns });
  console.log(`${new Date().toISOString()} warm-up`);
  await pace(WARM, FNS);
  await cdp.send("HeapProfiler.enable");
  await cdp.send("HeapProfiler.startSampling", { samplingInterval:16384, includeObjectsCollectedByMajorGC:true, includeObjectsCollectedByMinorGC:true });
  console.log(`${new Date().toISOString()} window start`);
  const r = await pace(SECS, FNS);
  console.log(`${new Date().toISOString()} window end`);
  const { profile } = await cdp.send("HeapProfiler.stopSampling");
  const byFn = new Map(); let total = 0;
  const walk = (node) => { const f = node.callFrame.functionName || "(anon)"; if(node.selfSize){ total += node.selfSize; byFn.set(f, (byFn.get(f) || 0) + node.selfSize); } for(const c of node.children || []) walk(c); };
  walk(profile.head);
  const KB = x => (x / 1024).toFixed(1);
  console.log(`${REPO.replace(/.*scratchpad\//, "")}: ${r.n} paced steps in ${(r.ms/1000).toFixed(1)} s (${(r.n/(r.ms/1000)).toFixed(0)}/s; sim advanced ${r.simT.toFixed(1)} s = ${(r.simT*60).toFixed(0)} steps, so the page's own loop ${Math.abs(r.simT*60 - r.n) < 6 ? "did not step" : "ALSO STEPPED"}): ${(total/1048576).toFixed(1)} MB sampled = ${KB(total/r.n)} KB a step`);
  console.log("tier residency over the window (share of 250 ms samples):");
  for(const k of FNS){ const s = r.samples[k] || []; if(!s.length){ console.log(`  ${k.padEnd(14)} (unbound)`); continue; } const c = {}; for(const v of s) c[tier(v)] = (c[tier(v)] || 0) + 1;
    const alloc = byFn.get(k) || 0;
    console.log(`  ${k.padEnd(14)} ${Object.entries(c).sort((a, b) => b[1] - a[1]).map(([t, n]) => `${t} ${(100*n/s.length).toFixed(0)}%`).join(", ").padEnd(46)} allocates ${KB(alloc/r.n).padStart(6)} KB a step   raw ${[...new Set(s)].slice(0, 6).join(" ")}`); }
  console.log("  by function (top 8):"); for(const [k, v] of [...byFn.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8)) console.log(`    ${KB(v/r.n).padStart(7)} KB/step  ${k}`);
  fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
