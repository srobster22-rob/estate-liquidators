// THE BAND, BY KIND: the same windows as band.js, the live bodies' distances and death
// distances split by enemy type and by crowd/ambient, and the damage ledger's contact hits
// over the window (g.hurtBy()). What this answers: WHO stands at twenty metres.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde";
const SEED = +(process.env.SEED || 9), WIN = +(process.env.WIN || 20), ATS = (process.env.AT || "720,1020").split(",").map(Number), MODES = (process.env.MODE || "kite,stand").split(",");
(async()=>{
  const b = await chromium.launch(L);
  for(const at of ATS) for(const mode of MODES){
    const pg = await b.newPage({ viewport:{ width:1280, height:760 } });
    await pg.goto("file://" + path.join(REPO, "index.html")); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
    const r = await pg.evaluate(({ at, mode, WIN, SEED }) => { const g = window.__g, E = (0, eval);
      g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED); g.start("intern"); g.god(); g.drainPicks(true); g.bot(true); g.pause(true);
      let guard = 0; while(g.state().t < at && !g.state().over && guard++ < 400000) g.step(30, 1/60);
      if(mode === "stand") g.bot(false);
      const en = E("enemies"), P = E("P"), hb0 = g.hurtBy ? JSON.parse(JSON.stringify(g.hurtBy())) : null;
      const K = {}; const kind = e => (e.crowd ? "crowd:" : "") + e.type;
      const rec = k => K[k] || (K[k] = { bodySteps:0, d:[], within8:0, within20:0, contact:0, deaths:[] });
      const last = new Map(); const N = Math.round(WIN * 60);
      for(let s = 0; s < N; s++){ g.step(1, 1/60); const seen = new Set();
        for(let i = 0; i < en.length; i++){ const e = en[i]; if(e.dead || e.boss) continue; const d = Math.hypot(e.x - P.x, e.z - P.z), k = kind(e), r = rec(k);
          r.bodySteps++; if(s % 30 === 0) r.d.push(d); if(d <= 8) r.within8++; if(d <= 20) r.within20++; if(d <= e.rad + .75) r.contact++;
          seen.add(e.eid); last.set(e.eid, [k, d]); }
        for(const [eid, [k, d]] of last) if(!seen.has(eid)){ if(d <= 70) rec(k).deaths.push(d); last.delete(eid); } }
      const q = (a, p) => { if(!a.length) return null; const s = a.slice().sort((u, v) => u - v); return +s[Math.min(s.length - 1, Math.floor(p * s.length))].toFixed(1); };
      const hb1 = g.hurtBy ? g.hurtBy() : null, hb = hb0 && hb1 ? Object.fromEntries(Object.keys(hb1).filter(k => typeof hb1[k] === "number").map(k => [k, hb1[k] - hb0[k]])) : null;
      const rows = Object.entries(K).sort((a, b) => b[1].bodySteps - a[1].bodySteps).map(([k, r]) => ({ k, alive:+(r.bodySteps / N).toFixed(1), p10:q(r.d, .1), p50:q(r.d, .5), p90:q(r.d, .9), in8:+(100*r.within8/r.bodySteps).toFixed(0), in20:+(100*r.within20/r.bodySteps).toFixed(0), contact:+(r.contact/N).toFixed(2), died:r.deaths.length, dp50:q(r.deaths, .5), dp90:q(r.deaths, .9) }));
      return { t:+g.state().t.toFixed(1), rows, hb }; }, { at, mode, WIN, SEED });
    console.log(`\n${mode} t=${at}..${r.t}  ledger over the window: ${r.hb ? JSON.stringify(r.hb) : "n/a"}`);
    console.log(`  ${"kind".padEnd(16)} ${"alive".padStart(6)}  ${"dist p10/p50/p90".padEnd(20)} ${"<=8m".padStart(5)} ${"<=20m".padStart(6)}  ${"at contact".padStart(10)}  died  death p50/p90`);
    for(const w of r.rows) console.log(`  ${w.k.padEnd(16)} ${String(w.alive).padStart(6)}  ${`${w.p10}/${w.p50}/${w.p90}`.padEnd(20)} ${String(w.in8 + "%").padStart(5)} ${String(w.in20 + "%").padStart(6)}  ${String(w.contact).padStart(10)}  ${String(w.died).padStart(4)}  ${w.dp50}/${w.dp90}`);
    await pg.close();
  }
  await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
