// Starting-weapon bench.
//
// Swapping THE INTERN's start from BONK BAT to MORTAR moved it from 2/8 veteran
// clears to 7/8 - a bigger swing than any character stat block in this game
// produces. Characters were being balanced on their mods while the mods were a
// rounding error next to the weapon they begin holding, and nothing measured
// that axis at all. This does: one character, held constant, every weapon in
// turn, so the numbers describe the STARTER and nothing else.
//
//   node starters.js [trials] [char]
const fs = require("fs");
function loadPlaywright(){
  for(const p of ["playwright", "/opt/node22/lib/node_modules/playwright"]){
    try { return require(p); } catch(e) {}
  }
  console.error("Playwright not found."); process.exit(2);
}
const { chromium } = loadPlaywright();
const LAUNCH = { args:["--use-gl=angle","--use-angle=swiftshader",
                       "--enable-unsafe-swiftshader","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"])
  if(fs.existsSync(p)) LAUNCH.executablePath = p;

const TRIALS = +(process.argv[2] || 8);
const CHAR   = process.argv[3] || "intern";
const fmt = t => `${Math.floor(t/60)}:${String(Math.round(t%60)).padStart(2,"0")}`;

(async () => {
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage();
  p.on("pageerror", e => console.log("ERR", e.message));
  await p.goto("file://" + require("path").resolve(__dirname, "index.html"));
  await p.waitForTimeout(400);
  const WEAPONS = await p.evaluate(() => window.__g.weapons());
  const ORIGINAL = await p.evaluate(c => window.__g.chars() && c, CHAR);

  const cell = (w) => p.evaluate(([c,w])=>{
    window.__g.wipeSave();
    window.__g.setUpgrades({hp:6,dmg:6,spd:5,mag:5,cd:5,crit:5,armor:5,start:3,rev:2});
    window.__g.patchStart(c, w);
    window.__g.start(c); window.__g.bot(true);
    const r = window.__g.runOut();
    return { t:r.t, won:!!r.won, lvl:window.__g.state().lvl, kills:window.__g.state().kills };
  }, [CHAR, w]);

  console.log(`\n${"=".repeat(64)}`);
  console.log(`STARTING WEAPON  -  ${CHAR.toUpperCase()} held constant, veteran shop, n=${TRIALS}`);
  console.log("=".repeat(64));
  console.log("start      clears   median   worst    lvl   kills");
  const rows = [];
  for (const w of WEAPONS) {
    const rs = []; for (let i=0;i<TRIALS;i++) rs.push(await cell(w));
    const ts = rs.map(r=>r.t).sort((a,b)=>a-b);
    const won = rs.filter(r=>r.won).length;
    const avg = k => rs.reduce((s,r)=>s+r[k],0)/rs.length;
    rows.push({ w, won, med: ts[ts.length>>1], worst: ts[0], lvl: avg("lvl"), kills: avg("kills") });
  }
  rows.sort((a,b)=>b.won-a.won || b.med-a.med);
  for (const r of rows)
    console.log(`${r.w.padEnd(10)} ${String(r.won+"/"+TRIALS).padStart(6)}  ` +
      `${fmt(r.med).padStart(6)}  ${fmt(r.worst).padStart(6)}  ` +
      `${r.lvl.toFixed(0).padStart(5)} ${r.kills.toFixed(0).padStart(7)}`);
  const spread = rows[0].won - rows[rows.length-1].won;
  console.log(`\n  spread ${spread}/${TRIALS} clears between the best and worst starter` +
              ` (${rows[0].w} vs ${rows[rows.length-1].w})`);
  await b.close();
})();
