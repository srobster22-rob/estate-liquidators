// One region-hour of rimDaySeeded's derivation, timed and counted: how many
// chipReadFar calls bezelDerive makes and how long each takes, on FILE, mirroring
// section 97's state before the bezel gates (pin 11, intern, god, one second),
// with NUM=1 running numGate first as the section does on the L37 build.
const fs = require("fs");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const FILE = process.env.FILE, NUM = process.env.NUM === "1", TAG = process.env.TAG || "";
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.goto("file://" + FILE); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const r = await pg.evaluate((NUM) => {
    const g = window.__g, E = (0, eval);
    g.wipeSave(); g.dev(true); g.pin(11); g.pinRun(11); g.start("intern"); g.god(); g.drainPicks(true); g.freezeEvents(true); g.step(60, 1/60);
    g.groundGate(); g.wardGate(); g.burrowGate();
    let numMs = 0; if(NUM && g.numGate){ const t = performance.now(); g.numGate(); numMs = performance.now() - t; }
    const scene = { enemies:E("enemies.length"), corpses:E("corpses.length"), cpops:E("cpops.length"), pops:E("pops.length"), rings:E("rings.length"), nums:E("nums.length"), gems:E("gems.length"), zones:E("zones.length") };
    const orig = g.chipReadFar; let calls = 0, callMs = 0;
    g.chipReadFar = function(){ const t = performance.now(); const o = orig.apply(this, arguments); callMs += performance.now() - t; calls++; return o; };
    const ids = [...E("silhouetteRegions()")], H = E("BEZEL_HOURS"), SW = E("BEZEL_SWEEP");
    const out = { numMs:Math.round(numMs), scene, ids, hours:H.length, sweep:SW.length, rows:[] };
    const t0 = performance.now();
    g.onBezelSeed(() => {
      for(const [id, t] of [[ids[0], H[0]], [ids[0], H[5]], [ids[1], H[0]]]){
        const c0 = calls, m0 = callMs, w0 = performance.now();
        const d = g.bezelDerive(id, SW, t, true);
        out.rows.push({ id, t, reach:d.reach, radii:d.rows.length, stations:d.stations.length, calls:calls - c0, ms:Math.round(performance.now() - w0), perCall:Math.round((callMs - m0) / Math.max(1, calls - c0)) });
      }
      return {};
    });
    out.totalMs = Math.round(performance.now() - t0);
    g.chipReadFar = orig;
    return out;
  }, NUM);
  console.log(TAG, JSON.stringify(r));
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
