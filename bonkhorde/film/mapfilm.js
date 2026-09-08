// THE MAP, DRIVEN. The owner's answer to "what is still wrong with the map"
// was "drive it and tell me" - so this takes one real bot-driven run and films
// the PLAY camera at several points through it, with the frame's own census
// beside each shot, so the report is evidence rather than a lead.
const fs = require("fs"), path = require("path");
function loadPlaywright(){
  for(const p of ["playwright", "/opt/node22/lib/node_modules/playwright"]){
    try { return require(p); } catch(e) {}
  }
  process.exit(2);
}
const { chromium } = loadPlaywright();
const LAUNCH = { args:["--use-gl=angle","--use-angle=swiftshader",
  "--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                "/opt/pw-browsers/chromium"])
  if(fs.existsSync(p)) LAUNCH.executablePath = p;

const OUT = path.resolve(__dirname, "..", "evidence", "l8-map");
const AT = [30, 180, 420, 720, 1020];        // 0:30, 3:00, 7:00, 12:00, 17:00

(async ()=>{
  fs.mkdirSync(OUT, { recursive:true });
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage({ viewport:{ width:1280, height:800 } });
  const errs = [];
  p.on("pageerror", e=>errs.push("pageerror: "+e.message));
  p.on("console", m=>{ if(m.type()==="error") errs.push(m.text()); });
  await p.goto("file://" + path.resolve(__dirname, "..", "index.html"));
  await p.waitForFunction(()=>window.__g && window.__g.state, null, { timeout:60000 });
  const frame = ()=>p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  // the point of a MAP film is the world, so every panel and the HUD come off.
  // !important, because hud() rewrites #hud's inline display every frame.
  await p.addStyleTag({ content: '#hud,#paused,#pick,#menu,#end{display:none !important}' });

  await p.evaluate(()=>{
    const g = window.__g;
    g.wipeSave(); g.pin(9); g.pinRun(9); g.start("intern"); g.god();
    g.bot(true); g.botHop(true); g.setShake(0);
  });

  const rows = [];
  let last = 0;
  for(const t of AT){
    // g.step() and NOT stepRaw(): step() returns immediately while a draft is
    // open, so a raw driver freezes the run at the first level-up and films
    // the same frame five times. g.step auto-picks, which is what a real run
    // does anyway.
    await p.evaluate(dt=>window.__g.step(dt*60, 1/60), t - last);
    last = t;
    await frame(); await frame();
    const tag = String(Math.floor(t/60)).padStart(2,"0") + "-" + String(t%60).padStart(2,"0");
    await p.screenshot({ path: path.join(OUT, `t${tag}.png`) });
    // what the frame is actually made of, and where the player is standing
    const info = await p.evaluate(()=>{
      const g = window.__g, c = g.boxCensus(), s = g.state();
      return { t:s.t, lvl:s.lvl, enemies:s.enemies, boxes:c.drawn,
               passes:c.passes, biome:g.biomeAt(s.x, s.z).nm,
               monsDrawn:c.monsDrawn, monuments:c.monuments,
               marksCulled:c.marksCulled, props:c.propsNear,
               gems:s.gems, paused:g.isPaused(),
               zones:c.zones, zonesCulled:c.zonesCulled, zoneBladed:c.zoneBladed };
    });
    rows.push({ tag, ...info });
    console.log(`t=${tag}  lvl ${String(info.lvl).padStart(2)}  ${info.biome.padEnd(16)}  ` +
      `boxes ${String(info.boxes).padStart(5)}  monuments ${info.monsDrawn}/${info.monuments}  ` +
      `enemies ${String(info.enemies).padStart(3)}  gems ${info.gems}` +
      `  zones ${info.zoneBladed}/${info.zones}` +
      (info.paused ? "  [PAUSED]" : ""));
  }

  // where a frame's geometry GOES, summed over the run - the honest answer to
  // "is the map most of what you are looking at, or is it the horde"
  const tot = {};
  for(const r of rows) for(const k in r.passes) tot[k] = (tot[k]||0) + r.passes[k];
  const sum = Object.values(tot).reduce((a,b)=>a+b,0);
  console.log("\nwhere the frames' boxes went, across the run:");
  Object.entries(tot).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>
    console.log(`  ${k.padEnd(12)} ${String(v).padStart(6)}  ${(v/sum*100).toFixed(1)}%`));
  fs.writeFileSync(path.join(OUT, "census.json"), JSON.stringify(rows, null, 2));
  console.log("\nshots ->", OUT);
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
