// WHAT ONE STEP ALLOCATES, at a settled mid-run state: V8's sampling heap profiler
// (collected objects included) around N sim steps at t=AT on a pinned run, on REPO's
// index.html with an optional mutant (MUT, by id from REPO's mutate.js). Prints bytes
// per step, the allocating functions, and the self-size of the functions L40 touched.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
const AT = +(process.env.AT || 300), N = +(process.env.N || 600), SEED = +(process.env.SEED || 9);
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor " + (src.split(m.from).length - 1)); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const cdp = await pg.context().newCDPSession(pg);
  const t0 = Date.now();
  const pre = await pg.evaluate(({ AT, SEED }) => { const g = window.__g; g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED);
    g.start("intern"); g.god(); g.drainPicks(true); g.bot(true);
    let guard = 0; while(g.state().t < AT && guard++ < 200000) g.step(30, 1/60);
    const s = g.state(); return { t:+s.t.toFixed(2), lvl:s.lvl, kills:s.kills, enemies:(0,eval)("enemies.length"), gems:(0,eval)("gems.length"), hazards:(0,eval)("hazards.length"), events:(0,eval)("events.length") }; }, { AT, SEED });
  const t1 = Date.now();
  await cdp.send("HeapProfiler.enable");
  await cdp.send("HeapProfiler.startSampling", { samplingInterval:16384, includeObjectsCollectedByMajorGC:true, includeObjectsCollectedByMinorGC:true });
  const post = await pg.evaluate((N) => { const g = window.__g; g.step(N, 1/60); const s = g.state(); return { t:+s.t.toFixed(2), kills:s.kills, enemies:(0,eval)("enemies.length"), gems:(0,eval)("gems.length") }; }, N);
  const { profile } = await cdp.send("HeapProfiler.stopSampling");
  const t2 = Date.now();
  const byFn = new Map(), byPath = new Map(); let total = 0;
  const walk = (node, stack) => { const f = node.callFrame, name = `${f.functionName || "(anon)"}`; const s = [...stack, name];
    if(node.selfSize){ total += node.selfSize; byFn.set(name, (byFn.get(name) || 0) + node.selfSize);
      const p = s.slice(-3).join(" < "); byPath.set(p, (byPath.get(p) || 0) + node.selfSize); }
    for(const c of node.children || []) walk(c, s); };
  walk(profile.head, []);
  const KB = x => (x / 1024).toFixed(1), MB = x => (x / 1048576).toFixed(1);
  const of = (n) => byFn.get(n) || 0;
  console.log(`${MUT || "clean"} @${REPO.replace(/.*scratchpad\//, "")}: settled at t=${pre.t} (lvl ${pre.lvl}, ${pre.kills} kills, ${pre.enemies} bodies, ${pre.gems} gems, ${pre.hazards} hazards, ${pre.events} events) in ${((t1-t0)/1000).toFixed(0)} s; ${N} steps to t=${post.t} in ${((t2-t1)/1000).toFixed(1)} s: ${MB(total)} MB sampled = ${KB(total / N)} KB/step`);
  console.log(`  touched: nearestCells ${KB(of("nearestCells"))} KB, confine ${KB(of("confine"))} KB, confineIn ${KB(of("confineIn"))} KB, botVector ${KB(of("botVector"))} KB, updateEnemies ${KB(of("updateEnemies"))} KB, updateGems ${KB(of("updateGems"))} KB, groundY ${KB(of("groundY"))} KB, walk ${KB(of("walk"))} KB, hypot ${KB(of("hypot"))} KB, next ${KB(of("next"))} KB`);
  console.log("  by function:"); for(const [k, v] of [...byFn.entries()].sort((a, b) => b[1] - a[1]).slice(0, 14)) console.log(`    ${KB(v).padStart(9)} KB  ${(100*v/total).toFixed(1).padStart(5)}%  ${k}`);
  console.log("  by path:"); for(const [k, v] of [...byPath.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)) console.log(`    ${KB(v).padStart(9)} KB  ${k}`);
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
