// THE SHAPES OF THE TABLES the hot code reads through a body: ENEMIES defs, the boss defs,
// the BIOMES and their mod/fauna/mon sub-objects, the cells. Key signatures (keys in order)
// per table, and how many distinct ones.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde";
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + path.join(REPO, "index.html")); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const r = await pg.evaluate(() => { const g = window.__g, E = (0, eval); g.wipeSave(); g.dev(true); g.pin(9); g.pinRun(9); g.start("intern");
    const sig = (o) => Object.keys(o).join(",");
    const census = (name, list) => { const m = new Map(); for(const o of list){ if(!o || typeof o !== "object") continue; const s = sig(o); m.set(s, (m.get(s) || 0) + 1); }
      return { name, n:list.length, sigs:[...m.entries()].map(([s, c]) => `${c}x [${s}]`) }; };
    const out = [];
    const tryE = (x) => { try { return E(x); } catch(e){ return null; } };
    const EN = tryE("ENEMIES"); if(EN) out.push(census("ENEMIES defs", Object.values(EN)));
    const BO = tryE("BOSSES"); if(BO) out.push(census("BOSSES defs", Array.isArray(BO) ? BO : Object.values(BO)));
    const BI = tryE("BIOMES"); if(BI){ out.push(census("BIOMES", BI)); out.push(census("BIOMES[].mod", BI.map(x => x.mod))); out.push(census("BIOMES[].fauna", BI.map(x => x.fauna))); out.push(census("BIOMES[].mon", BI.map(x => x.mon))); }
    const CE = tryE("cells"); if(CE){ out.push(census("cells", CE)); out.push(census("cells[].b", CE.map(c => c.b))); }
    const MON = tryE("curMon()"); if(MON) out.push(census("curMon().st (stages)", MON.st || []));
    return out; });
  for(const c of r){ console.log(`${c.name}: ${c.n} objects, ${c.sigs.length} signature(s)`); for(const s of c.sigs) console.log("   " + s.slice(0, 230)); }
  await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
