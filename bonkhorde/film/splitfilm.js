// THE SPLIT, filmed: the player and its twin, from three angles, at three
// points down both lines. A model change is verified with renders from several
// angles, not one screenshot at one moment of one animation.
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

const OUT = path.resolve(__dirname, "..", "evidence", "l7-split");

(async ()=>{
  fs.mkdirSync(OUT, { recursive:true });
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage({ viewport:{ width:1280, height:800 } });
  const errs = [];
  p.on("pageerror", e=>errs.push("pageerror: "+e.message));
  p.on("console", m=>{ if(m.type()==="error") errs.push(m.text()); });
  await p.goto("file://" + path.resolve(__dirname, "..", "index.html"));
  await p.waitForFunction(()=>window.__g && window.__g.state, null, { timeout:60000 });
  // hud() rewrites #hud's inline display every frame and the pause sheet is a
  // full-screen panel, so the overlays are taken out with !important rather
  // than by poking the DOM - a stylesheet rule marked important beats an
  // inline style, which is the only way to win against a per-frame writer.
  await p.addStyleTag({ content: '#hud,#paused,#pick,#menu,#end{display:none !important}' });

  const frame = ()=>p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));

  // the three angles the play camera and the model sheet actually use
  const ANGLES = [
    ["behind",  [0, 7.5, -13,  0, 2.2, 1.5]],
    ["three-q", [11, 7.0, -8,  0, 2.2, 0]],
    ["side",    [15, 4.5, 0.5, 0, 2.2, 0]],
  ];

  const shots = [];
  for(const [lvl, tag] of [[1,"hatchlings"], [20,"grown"], [48,"final"]]){
    await p.evaluate((lvl)=>{
      const g = window.__g;
      g.wipeSave(); g.pin(5); g.pinRun(5); g.start("intern"); g.god(); g.disarm();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0);
      g.clearEnemies(); g.clearGems(); g.place(0,0); g.aim(0); g.still(true);
      g.splitAs("scrap");                       // a named line, so the sheet is stable
      while(g.state().lvl < lvl) g.levelUp();
      g.drainPicks(true);
      // settle the twin into its slot and let both gaits run a little
      for(let i=0;i<240;i++) g.stepRaw(1/60);
      // NOT paused: the pause sheet is the whole screen, and a live frame with
      // the spawner frozen and the field swept is a still anyway. The three
      // angles then land on three moments of the gait, which is better
      // evidence than one moment three times.
    }, lvl);
    for(const [nm, cam] of ANGLES){
      await p.evaluate(c=>window.__g.camLock(...c), cam);
      await frame(); await frame();
      const f = path.join(OUT, `${tag}-${nm}.png`);
      await p.screenshot({ path:f });
      shots.push(f);
    }
    const info = await p.evaluate(()=>({ me: window.__g.stageNm(), twin: window.__g.twin() }));
    console.log(`${tag.padEnd(11)} lvl ${String(lvl).padStart(2)}  ${info.me}  +  ${info.twin.nm}  (gap ${info.twin.d}m)`);
    await p.evaluate(()=>window.__g.camLock());
  }
  console.log("\nshots:", shots.length, "->", OUT);
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
