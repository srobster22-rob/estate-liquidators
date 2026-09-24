// DOES THE HORDE PRESS IN, OR STAND AT A BAND? On the pinned god-bot run (seed SEED), at each
// time in AT: the run is brought there by the bot, then for WIN seconds either the bot keeps
// kiting (MODE kite) or the player STANDS (bot off, no input). Every step: the live bodies'
// distances, how many are at contact (d <= rad + .75), how many bodies vanished and at what
// distance (over 70 m = the cull), the game's own measured kill radius. A frame is taken at
// the end of each window. What this separates: a band the kit's reach makes (it stands even
// when the player stands) from a band the kiting bot makes (it closes when the player stops).
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde", OUT = process.env.OUT || __dirname;
const SEED = +(process.env.SEED || 9), WIN = +(process.env.WIN || 20), ATS = (process.env.AT || "420,720,1020").split(",").map(Number), MODES = (process.env.MODE || "kite,stand").split(",");
(async()=>{
  const b = await chromium.launch(L);
  for(const at of ATS) for(const mode of MODES){
    const pg = await b.newPage({ viewport:{ width:1280, height:760 } });
    await pg.goto("file://" + path.join(REPO, "index.html")); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
    const r = await pg.evaluate(({ at, mode, WIN, SEED }) => { const g = window.__g, E = (0, eval);
      g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED); g.start("intern"); g.god(); g.drainPicks(true); g.bot(true); g.pause(true);
      let guard = 0; while(g.state().t < at && !g.state().over && guard++ < 400000) g.step(30, 1/60);
      if(mode === "stand") g.bot(false);
      const en = E("enemies"), P = E("P"), hf = E("hordeFlow");
      const x0 = P.x, z0 = P.z, killed0 = hf.killed, culled0 = hf.culled;
      const last = new Map(); let steps = 0, aliveSum = 0, contactSum = 0, nearestSum = 0, within3 = 0, within8 = 0, within20 = 0, bodySteps = 0;
      const dists = [], deaths = [], culls = [];
      const N = Math.round(WIN * 60);
      for(let s = 0; s < N; s++){
        g.step(1, 1/60); steps++;
        const seen = new Set(); let alive = 0, contact = 0, nearest = 1e9;
        for(let i = 0; i < en.length; i++){ const e = en[i]; if(e.dead || e.boss) continue; const d = Math.hypot(e.x - P.x, e.z - P.z);
          alive++; seen.add(e.eid); last.set(e.eid, d); if(d < nearest) nearest = d; if(d <= e.rad + .75) contact++;
          if(d <= 3) within3++; if(d <= 8) within8++; if(d <= 20) within20++; bodySteps++; if(s % 30 === 0) dists.push(d); }
        for(const [eid, d] of last) if(!seen.has(eid)){ (d > 70 ? culls : deaths).push(d); last.delete(eid); }
        aliveSum += alive; contactSum += contact; if(alive) nearestSum += nearest;
      }
      const q = (a, p) => { if(!a.length) return null; const s = a.slice().sort((u, v) => u - v); return +s[Math.min(s.length - 1, Math.floor(p * s.length))].toFixed(1); };
      g.pause(true);
      return { t:+g.state().t.toFixed(1), lvl:g.state().lvl, moved:+Math.hypot(P.x - x0, P.z - z0).toFixed(1), alive:+(aliveSum/steps).toFixed(1), nearest:+(nearestSum/steps).toFixed(1),
               p10:q(dists, .1), p50:q(dists, .5), p90:q(dists, .9), share3:+(100*within3/Math.max(1,bodySteps)).toFixed(1), share8:+(100*within8/Math.max(1,bodySteps)).toFixed(1), share20:+(100*within20/Math.max(1,bodySteps)).toFixed(1),
               contactPerS:+(contactSum/steps*60/60).toFixed(2), deaths:deaths.length, deathP50:q(deaths, .5), deathP10:q(deaths, .1), deathP90:q(deaths, .9), culls:culls.length,
               killed:hf.killed - killed0, culled:hf.culled - culled0, killR:+E("killR").toFixed(1), killRN:E("killRN") }; }, { at, mode, WIN, SEED });
    await pg.evaluate(() => { const g = window.__g; let ms = performance.now(); g.setShake && g.setShake(0); g.tick(ms += 16); g.tick(ms += 16); const p = document.getElementById("paused"); if(p) p.style.visibility = "hidden"; });
    await pg.screenshot({ path:path.join(OUT, `band-${mode}-${String(at).padStart(4, "0")}.png`) });
    console.log(`${mode.padEnd(5)} t=${at}->${r.t} lvl ${r.lvl} moved ${r.moved} m | alive ${r.alive} | nearest ${r.nearest} m, body distance p10/p50/p90 ${r.p10}/${r.p50}/${r.p90} m | share of body-time <=3 m ${r.share3}%, <=8 m ${r.share8}%, <=20 m ${r.share20}% | at contact ${r.contactPerS} bodies avg | died ${r.deaths} (p10/p50/p90 at ${r.deathP10}/${r.deathP50}/${r.deathP90} m), culled ${r.culls}; game: killed ${r.killed} culled ${r.culled}, killR ${r.killR} (n ${r.killRN})`);
    await pg.close();
  }
  await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
