// WHAT ONE STEP ALLOCATES AS PLAYED: the same settled pinned run, but the steps PACED at
// sixty a second of wall time (setTimeout, the page's own loop paused) so the JIT gets the
// wall time it gets in play - a big function that has just deoptimized is back in the top
// tier within a fraction of a second, not still in the baseline tier hundreds of steps
// later as it is when the steps are run flat out. V8's sampling heap profiler around SECS
// seconds of that, by allocating function.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde";
const AT = +(process.env.AT || 300), SECS = +(process.env.SECS || 20), SEED = +(process.env.SEED || 9), WARM = +(process.env.WARM || 5);
const src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const cdp = await pg.context().newCDPSession(pg);
  await pg.evaluate(({ AT, SEED }) => { const g = window.__g; g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED);
    g.start("intern"); g.god(); g.drainPicks(true); g.bot(true); g.pause(true);
    let guard = 0; while(g.state().t < AT && guard++ < 200000) g.step(30, 1/60); }, { AT, SEED });
  const pace = (secs) => pg.evaluate((secs) => new Promise(res => { const g = window.__g; let n = 0; const t0 = performance.now();
    const tick = () => { g.step(1, 1/60); n++; if(performance.now() - t0 < secs * 1000) setTimeout(tick, 16); else res({ n, ms:performance.now() - t0 }); }; tick(); }), secs);
  const w = await pace(WARM);                                    // the JIT settles into the paced regime first
  await cdp.send("HeapProfiler.enable");
  await cdp.send("HeapProfiler.startSampling", { samplingInterval:16384, includeObjectsCollectedByMajorGC:true, includeObjectsCollectedByMinorGC:true });
  const r = await pace(SECS);
  const { profile } = await cdp.send("HeapProfiler.stopSampling");
  const st = await pg.evaluate(() => { const s = window.__g.state(); return { t:+s.t.toFixed(1), bodies:(0,eval)("enemies.length") }; });
  const byFn = new Map(); let total = 0;
  const walk = (node) => { const f = node.callFrame.functionName || "(anon)"; if(node.selfSize){ total += node.selfSize; byFn.set(f, (byFn.get(f) || 0) + node.selfSize); } for(const c of node.children || []) walk(c); };
  walk(profile.head);
  const KB = x => (x / 1024).toFixed(1), of = n => byFn.get(n) || 0;
  console.log(`${REPO.replace(/.*scratchpad\//, "")}: ${w.n} warm-up steps in ${(w.ms/1000).toFixed(1)} s, then ${r.n} paced steps in ${(r.ms/1000).toFixed(1)} s (${(r.n / (r.ms/1000)).toFixed(0)} a second) to t=${st.t}, ${st.bodies} bodies: ${(total/1048576).toFixed(1)} MB sampled = ${KB(total / r.n)} KB a step`);
  console.log(`  walk ${KB(of("walk"))} KB, updateEnemies ${KB(of("updateEnemies"))} KB, groundY ${KB(of("groundY"))} KB, botVector ${KB(of("botVector"))} KB, hypot ${KB(of("hypot"))} KB, min ${KB(of("min"))} KB, next ${KB(of("next"))} KB  (per step: walk ${KB(of("walk")/r.n)}, updateEnemies ${KB(of("updateEnemies")/r.n)}, groundY ${KB(of("groundY")/r.n)})`);
  console.log("  by function:"); for(const [k, v] of [...byFn.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)) console.log(`    ${KB(v).padStart(9)} KB  ${(100*v/total).toFixed(1).padStart(5)}%  ${k}`);
  fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
