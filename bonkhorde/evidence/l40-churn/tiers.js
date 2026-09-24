// ARE THE HOT FUNCTIONS OPTIMIZED? Chrome launched with --allow-natives-syntax and
// --trace-deopt; the pinned run settled at t=AT, N steps taken, then V8's own
// %GetOptimizationStatus read for each hot function (twice, N steps apart). With
// DEBUG=pw:browser the browser's stdout (the deopt trace) reaches this process's stderr.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const JSF = process.env.JSF || "--allow-natives-syntax --trace-deopt";
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox", "--js-flags=" + JSF] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde";
const AT = +(process.env.AT || 300), N = +(process.env.N || 600), SEED = +(process.env.SEED || 9);
const FNS = (process.env.FNS || "updateEnemies,walk,groundY,botVector,updateGems,updateBrood,stepCorpses,near,hitNear,step,nearestCells,confine,confineIn,RELIEF,RELIEF_RAW,BASE_Y,waterDepth,wardPass,updateProjectiles,sampleStyle,vnoise,shoreCap,biomeAt,hdlInLane,inWater").split(",");
const BITS = ["IsFunction","NeverOptimize","AlwaysOptimize","MaybeDeopted","Optimized","Maglevved","TurboFanned","Interpreted","MarkedForOptimization","MarkedForConcurrentOptimization","OptimizingConcurrently","IsExecuting","TopmostFrameIsTurboFanned","LiteMode","MarkedForDeoptimization","Baseline","TopmostFrameIsInterpreted","TopmostFrameIsBaseline","IsLazy","TopmostFrameIsMaglev","OptimizeOnNextCallOptimizesToMaglev","OptimizeMaglevOptimizesToTurbofan","MarkedForMaglevOptimization","MarkedForConcurrentMaglevOptimization"];
const src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  console.log("UA " + await pg.evaluate(() => navigator.userAgent));
  const natives = await pg.evaluate(() => { try { return (0, eval)("%GetOptimizationStatus(function(){})") >= 0; } catch(e){ return "no: " + e.message; } });
  console.log("natives syntax: " + natives);
  const status = (fns) => pg.evaluate(({ fns, BITS }) => { const out = {};
    for(const n of fns){ let f; try { f = (0, eval)(n); } catch(e){ out[n] = "unbound"; continue; }
      if(typeof f !== "function"){ out[n] = "not a function"; continue; }
      const s = (0, eval)("(f) => %GetOptimizationStatus(f)")(f);
      out[n] = s + " " + BITS.filter((_, i) => s & (1 << i)).join("|"); }
    return out; }, { fns, BITS });
  const settle = await pg.evaluate(({ AT, SEED }) => { const g = window.__g; g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED);
    g.start("intern"); g.god(); g.drainPicks(true); g.bot(true);
    let guard = 0; while(g.state().t < AT && guard++ < 200000) g.step(30, 1/60); return g.state().t.toFixed(1); }, { AT, SEED });
  console.log(`${new Date().toISOString()} settled at t=${settle}`);
  const s1 = await status(FNS);
  await pg.evaluate((N) => window.__g.step(N, 1/60), N);
  const s2 = await status(FNS); console.log(`${new Date().toISOString()} stepped ${N}`);
  console.log("function".padEnd(18) + "after settling".padEnd(60) + `after ${N} more steps`);
  for(const n of FNS) console.log(n.padEnd(18) + String(s1[n]).padEnd(60) + s2[n]);
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
