// Weapon DPS bench. Two axes that decide a run: BOSS (can you close it) and
// CROWD (can you survive to try).
//
// v1 of this measured boss DPS against a lone boss with the autopilot on, and
// reported exactly 0.0 for skulls, pulse and caltrops. That was not DPS, it was
// REACH: with one enemy and no gems on the floor the bot has no reason to be
// anywhere near it, so it fled and every player-centred weapon whiffed forever.
// The number that matters is damage landed on the boss during a REAL fight -
// horde present, gems pulling you back in, bot kiting through it. So: spawn the
// finale, let it run, and attribute boss damage separately.
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

let WEAPONS = null;                       // read from the game, see below
const SECONDS = 26;
// Two axes were not enough. BONK BAT reads last on both of them while carrying
// kb:20 at MEGABONK - by a distance the largest knockback in the game - and
// "space cleared" is worth minutes that neither DPS column can see. Same blind
// spot that made MAGNET look like the worst passive. So: a third column, one
// weapon and nothing else, played to death.
const SURV_N = +(process.argv[3] || 4);
// Paired seeds, same as balance.js. Without them this bench had the same
// problem the difficulty bench had: eight weapons each measured on a different
// arena with a different spawn mix, then compared to each other. Trial i of
// every weapon now runs seed BASE+i, so the eight rows share their worlds and
// the column is a comparison rather than eight separate experiments.
const SEED_BASE = process.env.BONKHORDE_SEED !== undefined
                ? +process.env.BONKHORDE_SEED : 20260821;
// BONKHORDE_TIERS=rank benches only the top of the normal table. The evolved
// half runs eight weapons to death with evolved kit, which is eight full
// twenty-four minute runs and most of the wall clock.
const TIERS = (process.env.BONKHORDE_TIERS || "both");
// One sample per cell swung crowd DPS by 40% between runs (skulls 1110 -> 1631).
// Averaging is not optional when the thing you are measuring has a horde in it.
const REPEATS = +(process.argv[2] || 3);

(async () => {
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage();
  p.on("pageerror", e => console.log("ERR", e.message));
  await p.goto("file://" + require("path").resolve(__dirname, "index.html"));
  await p.waitForTimeout(400);
  // hardcoding this list means a ninth weapon ships unbenched and the table
  // still prints a tidy eight rows, which reads as full coverage
  WEAPONS = await p.evaluate(() => window.__g.weapons());

  // one scenario, both numbers: the sudden-death fight as it actually happens
  const bench = (w, evo, seed) => p.evaluate(([w, evo, SECONDS, seed]) => {
    window.__g.wipeSave();
    if (seed !== null) { window.__g.pin(seed); window.__g.pinRun(seed); }
    window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
    window.__g.skipTo(1140);
    window.__g.give(w, 4);
    if (evo) window.__g.evolve(w);
    window.__g.bot(true);
    window.__g.boss(3);                                 // THE FINAL BONK
    window.__g.step(60 * 6);                            // let the horde build
    window.__g.dmg();                                   // reset meters
    window.__g.step(60 * SECONDS);
    const d = window.__g.dmg();
    return { boss: d.boss / SECONDS, crowd: (d.all - d.boss) / SECONDS };
  }, [w, evo, SECONDS, seed]);

  // one weapon, mid-tier shop, no godmode, autopilot, run until it dies
  const surv = (w, evo, seed) => p.evaluate(([w, evo, seed]) => {
    window.__g.wipeSave();
    if (seed !== null) { window.__g.pin(seed); window.__g.pinRun(seed); }
    window.__g.setUpgrades({hp:3,dmg:3,spd:3,mag:3,cd:3,crit:3,armor:3});
    window.__g.start("intern"); window.__g.drainPicks(true);
    window.__g.give(w, 4);
    if (evo) window.__g.evolve(w);
    window.__g.bot(true);
    return window.__g.runOut().t;
  }, [w, evo, seed]);

  const tiers = TIERS === "rank" ? [false] : TIERS === "evo" ? [true] : [false, true];
  for (const evo of tiers) {
    console.log(`\n${"=".repeat(58)}`);
    // "RANK 5" was the top of a five-rank table. It is rank 3 of 3 now and it
    // reads the same stat block - see RANKMAP - so the number did not move,
    // only the label anyone reading this would check it against.
    console.log(evo ? "EVOLVED" : "TOP RANK");
    console.log("=".repeat(58));
    console.log(`weapon        boss dps    crowd dps    survived   boss vs median` +
                `   (dps n=${REPEATS}, survival n=${SURV_N}` +
                (SEED_BASE ? `, seeds ${SEED_BASE}..${SEED_BASE + Math.max(REPEATS, SURV_N) - 1}` : ", unseeded") + ")");
    const rows = [];
    for (const w of WEAPONS) {
      let boss = 0, crowd = 0, alive = 0;
      for (let i = 0; i < REPEATS; i++) {
        const r = await bench(w, evo, SEED_BASE ? SEED_BASE + i : null);
        boss += r.boss / REPEATS; crowd += r.crowd / REPEATS;
      }
      for (let i = 0; i < SURV_N; i++)
        alive += (await surv(w, evo, SEED_BASE ? SEED_BASE + i : null)) / SURV_N;
      rows.push({ w, boss, crowd, alive });
    }
    const med = rows.map(r=>r.boss).sort((a,b)=>a-b)[rows.length>>1];
    for (const r of rows)
      console.log(`${r.w.padEnd(10)} ${Math.round(r.boss).toString().padStart(11)} ` +
                  `${Math.round(r.crowd).toString().padStart(12)} ` +
                  `${(Math.floor(r.alive/60) + ":" + String(Math.round(r.alive%60)).padStart(2,"0")).padStart(11)} ` +
                  `${(r.boss/med).toFixed(2).padStart(14)}x`);
    console.log(`${"".padEnd(10)} ${("median " + Math.round(med)).padStart(11)}`);
  }
  await b.close();
})();
