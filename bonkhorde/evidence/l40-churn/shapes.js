// HOW MANY SHAPES DO THE BODIES HAVE? At t=AT on the pinned run: the distinct V8 maps
// (%HaveSameMap) among the enemies, gems, corpses, pets and the rest, grouped by their
// property-key signature. Also calibrates %GetOptimizationStatus's bits on this V8.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox", "--js-flags=--allow-natives-syntax"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde";
const AT = +(process.env.AT || 300), SEED = +(process.env.SEED || 9);
const src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const cal = await pg.evaluate(() => { const E = (0, eval), st = E("(f) => %GetOptimizationStatus(f)");
    const mk = () => E("(function(a){ return a + 1; })");
    const lazy = mk();
    const once = mk(); once(1);
    const base = mk(); E("(f)=>%PrepareFunctionForOptimization(f)")(base); base(1); base(2); E("(f)=>%CompileBaseline(f)")(base);
    const tf = mk(); E("(f)=>%PrepareFunctionForOptimization(f)")(tf); tf(1); tf(2); E("(f)=>%OptimizeFunctionOnNextCall(f)")(tf); tf(3);
    const mg = mk(); E("(f)=>%PrepareFunctionForOptimization(f)")(mg); mg(1); mg(2); E("(f)=>%OptimizeMaglevOnNextCall(f)")(mg); mg(3);
    const de = mk(); E("(f)=>%PrepareFunctionForOptimization(f)")(de); de(1); de(2); E("(f)=>%OptimizeFunctionOnNextCall(f)")(de); de(3); E("(f)=>%DeoptimizeFunction(f)")(de);
    return { lazy:st(lazy), once:st(once), baseline:st(base), turbofan:st(tf), maglev:st(mg), deoptimized:st(de) }; });
  console.log("status calibration: " + Object.entries(cal).map(([k, v]) => `${k}=${v}`).join("  "));
  const r = await pg.evaluate(({ AT, SEED }) => { const g = window.__g, E = (0, eval); g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED);
    g.start("intern"); g.god(); g.drainPicks(true); g.bot(true);
    let guard = 0; while(g.state().t < AT && guard++ < 200000) g.step(30, 1/60);
    const same = E("(a, b) => %HaveSameMap(a, b)");
    const census = (arr) => { const reps = [], sig = new Map();
      for(const o of arr){ if(!o || typeof o !== "object") continue;
        let found = false; for(const r of reps) if(same(r.o, o)){ r.n++; found = true; break; }
        if(!found) reps.push({ o, n:1, keys:Object.keys(o).length });
        const k = Object.keys(o).join(","); sig.set(k, (sig.get(k) || 0) + 1); }
      return { n:arr.length, maps:reps.length, sigs:sig.size, keyCounts:[...new Set(reps.map(r => r.keys))].sort((a, b) => a - b).join("/"),
               top:[...sig.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => `${v}x[${k.split(",").length} keys]`).join(" ") }; };
    const out = {};
    for(const name of ["enemies","gems","corpses","pets","hazards","events","zones","spits","bolts","mortars","rings","swings","arcs","nums","marks"]){
      let a; try { a = E(name); } catch(e){ out[name] = "unbound"; continue; } if(!Array.isArray(a)){ out[name] = "not an array"; continue; } out[name] = census(a); }
    // the enemies' per-key presence: which keys are on SOME bodies and not all
    const en = E("enemies"), all = new Map(); for(const e of en) for(const k of Object.keys(e)) all.set(k, (all.get(k) || 0) + 1);
    const partial = [...all.entries()].filter(([k, v]) => v !== en.length).sort((a, b) => a[1] - b[1]).map(([k, v]) => `${k}:${v}`);
    const defs = new Map(); for(const e of en){ const d = e.def && e.def.id || e.type || "?"; defs.set(d, (defs.get(d) || 0) + 1); }
    return { t:g.state().t.toFixed(1), out, partial, defs:[...defs.entries()].map(([k, v]) => `${k}:${v}`).join(" ") }; }, { AT, SEED });
  console.log(`t=${r.t}`); for(const [k, v] of Object.entries(r.out)) console.log(`  ${k.padEnd(9)} ${typeof v === "string" ? v : `${String(v.n).padStart(4)} objects, ${String(v.maps).padStart(3)} maps, ${String(v.sigs).padStart(3)} key signatures, key counts ${v.keyCounts}; ${v.top}`}`);
  console.log("enemy kinds: " + r.defs); console.log("enemy keys not on every body (key:count of " + r.out.enemies.n + "): " + r.partial.join(" "));
  fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
