const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
(async()=>{ const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + path.join(process.env.REPO || "/home/user/estate-liquidators/bonkhorde", "index.html")); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const r = await pg.evaluate(() => { const g = window.__g, E = (0, eval); g.wipeSave(); g.dev(true); g.pin(9); g.pinRun(9); g.start("intern"); g.god(); g.drainPicks(true); g.bot(true); g.pause(true);
    const out = []; for(const at of [300, 420, 720, 1020]){ let guard = 0; while(g.state().t < at && guard++ < 400000) g.step(30, 1/60);
      const en = E("enemies"); out.push({ t:g.state().t.toFixed(0), alive:en.filter(e => !e.dead).length, crowdLive:en.filter(e => !e.dead && e.crowd).length, unpaidLive:en.filter(e => !e.dead && e.crowd && !e.xp).length, stat:Object.assign({}, E("crowdStat")), bank:+E("crowdBank").toFixed(1), free:E("crowdFree") }); }
    return out; });
  for(const o of r) console.log(`t=${o.t}: alive ${o.alive}, crowd-flagged ${o.crowdLive} (unpaid ${o.unpaidLive}); crowdStat ${JSON.stringify(o.stat)} bank ${o.bank} crowdFree ${o.free}`);
  await b.close(); })().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
