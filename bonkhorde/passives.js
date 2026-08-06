// Passive bench. The evolution requirement funnels you into one specific
// passive for ~3 of your picks, so the question is not "does it say damage" but
// "is it a comparable pick". Two axes, both measured against a no-passive
// control with an identical weapon kit so the passive is the only variable:
//
//   OFFENCE  damage per second in the minute-19 fight. The obvious metric,
//            kills-by-8:00, is SUPPLY-CAPPED - with godmode and a working kit
//            the bot kills everything that spawns, so every passive scored
//            within 1% of the control including +39% damage from SPINACH.
//   DEFENCE  time to death with no godmode
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

const PASSIVES = ["spinach","clover","dupe","tempo","plating","magnet","heart","boots"];
const OFFENSIVE = new Set(["spinach","clover","dupe","tempo"]);
const N = +(process.argv[2] || 4);

(async () => {
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage();
  p.on("pageerror", e => console.log("ERR", e.message));
  await p.goto("file://" + require("path").resolve(__dirname, "index.html"));
  await p.waitForTimeout(400);

  const trial = (passive, mode) => p.evaluate(([passive, mode]) => {
    window.__g.wipeSave();
    window.__g.setUpgrades({hp:3,dmg:3,spd:3,mag:3,cd:3,crit:3,armor:3});
    window.__g.start("intern");
    if (mode === "offence") window.__g.god();
    window.__g.drainPicks(true);                 // no random picks: fixed kit only
    window.__g.give("bat", 4); window.__g.give("bolt", 4);
    if (passive) window.__g.give(passive, 2);    // rank 3 = the evolution gate
    window.__g.bot(true);
    if (mode === "offence") {
      window.__g.skipTo(1140); window.__g.boss(3);   // uncapped: 160k HP to chew
      window.__g.step(60 * 6); window.__g.dmg();     // settle, reset meter
      window.__g.step(60 * 24);
      return window.__g.dmg().all / 24;
    }
    return window.__g.runOut().t;
  }, [passive, mode]);

  const avg = async (passive, mode) => {
    let s = 0; for (let i = 0; i < N; i++) s += await trial(passive, mode);
    return s / N;
  };

  const base = { off: await avg(null, "offence"), def: await avg(null, "defence") };
  console.log(`control (no passive)   dps ${Math.round(base.off)}   ` +
              `survived ${(base.def/60).toFixed(1)}m     n=${N}`);
  console.log(`kit: BONK BAT + BOLT at rank 5. Note DUPLICATOR is kit-dependent -`);
  console.log(`see dupe measurements across kits; BOLT is one it can use.\n`);
  console.log("passive             dps   vs base   survived   vs base   type");
  const rows = [];
  for (const k of PASSIVES) {
    const off = await avg(k, "offence"), def = await avg(k, "defence");
    rows.push({ k, off, def });
    console.log(`${k.padEnd(10)} ${Math.round(off).toString().padStart(11)} ` +
                `${((off/base.off-1)*100).toFixed(0).padStart(8)}% ` +
                `${(def/60).toFixed(1).padStart(10)}m ` +
                `${((def/base.def-1)*100).toFixed(0).padStart(8)}% ` +
                `   ${OFFENSIVE.has(k) ? "offence" : "defence"}`);
  }
  const grp = t => {
    const g = rows.filter(r => OFFENSIVE.has(r.k) === t);
    return { off: g.reduce((s,r)=>s+r.off,0)/g.length, def: g.reduce((s,r)=>s+r.def,0)/g.length };
  };
  const O = grp(true), D = grp(false);
  console.log(`\n  offence partners  avg ${((O.off/base.off-1)*100).toFixed(0)}% dps, ` +
              `${((O.def/base.def-1)*100).toFixed(0)}% survival`);
  console.log(`  defence partners  avg ${((D.off/base.off-1)*100).toFixed(0)}% dps, ` +
              `${((D.def/base.def-1)*100).toFixed(0)}% survival`);
  await b.close();
})();
