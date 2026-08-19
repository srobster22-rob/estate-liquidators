// Difficulty measurement. Runs the kiting autopilot to death, many times over,
// and reports where runs actually end. Answers the only question that matters
// for a survivors-like: is the 20-minute run winnable but not free?
const fs = require("fs");

// Resolve Playwright and Chromium wherever they happen to live. This runs in a
// container with a pre-installed browser; on a normal machine `npm i playwright
// && npx playwright install chromium` is enough and both fallbacks are unused.
function loadPlaywright(){
  for(const p of ["playwright", "/opt/node22/lib/node_modules/playwright"]){
    try { return require(p); } catch(e) {}
  }
  console.error("Playwright not found. Run: npm i playwright && npx playwright install chromium");
  process.exit(2);
}
const { chromium } = loadPlaywright();

const LAUNCH = {
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
         "--ignore-gpu-blocklist", "--no-sandbox"],
};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"])
  if(fs.existsSync(p)) LAUNCH.executablePath = p;


// node balance.js [trials] [first|vet|both]
// A bimodal outcome (die at minute 8, or clear) makes a median over 4 trials
// close to meaningless - raise trials when you are tuning against it.
// node balance.js [trials] [first|vet|both] [char,char]
const TRIALS = +(process.argv[2] || 4);
const TIER   = process.argv[3] || "both";
// Hardcoded here, this list silently excluded THE ACCOUNTANT and THE TWIN the
// moment they shipped - a bench that quietly stops covering new content is
// worse than no bench, because the gap looks like a clean sweep. Read from the
// game instead. (test.js was fixed for this and balance.js was not, which is
// how you end up with one instrument honest and the other out of date.)
let CHARS = process.argv[4] ? process.argv[4].split(",") : null;

(async () => {
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage();
  p.on("pageerror", e => console.log("ERR", e.message));
  await p.goto("file://" + require("path").resolve(__dirname, "index.html"));
  await p.waitForTimeout(400);
  if (!CHARS) CHARS = await p.evaluate(() => window.__g.chars());

  const fmt = s => `${String(Math.floor(s/60)).padStart(2,"0")}:${String(Math.floor(s%60)).padStart(2,"0")}`;

  const runOne = (ch, shopped) => p.evaluate(([ch, shopped]) => {
    window.__g.wipeSave();
    if (shopped) window.__g.setUpgrades(
      { hp:6, dmg:6, spd:5, mag:5, cd:5, crit:5, armor:5, start:3, rev:2 });
    window.__g.start(ch);
    window.__g.bot(true);
    const st = window.__g.runOut();
    return { t: st.t, lvl: st.lvl, kills: st.kills, over: st.over, won: st.won, why: st.why,
             kit: window.__g.kit().length,
             evos: window.__g.kit().filter(k => k.includes("EVO")).length };
  }, [ch, shopped]);

  const tiers = TIER === "first" ? [false] : TIER === "vet" ? [true] : [false, true];
  for (const shopped of tiers) {
    console.log(`\n${"=".repeat(66)}`);
    console.log(shopped ? "VETERAN  (all permanent upgrades bought)"
                        : "FIRST RUN  (no permanent upgrades)");
    console.log("=".repeat(66));
    console.log("char     n   median    worst     best   lvl  kills   evos  clears");
    for (const ch of CHARS) {
      const rs = [];
      for (let i = 0; i < TRIALS; i++) rs.push(await runOne(ch, shopped));
      const ts = rs.map(r => r.t).sort((a, b) => a - b);
      const med = ts[Math.floor(ts.length / 2)];
      const clears = rs.filter(r => r.won).length;   // NOT t>=1199 - sudden death runs past 20:00
      const avg = k => (rs.reduce((s, r) => s + r[k], 0) / rs.length);
      console.log(
        `${ch.padEnd(8)} ${String(TRIALS).padStart(2)}  ` +
        `${fmt(med).padStart(6)}   ${fmt(ts[0]).padStart(6)}   ${fmt(ts[ts.length-1]).padStart(6)}  ` +
        `${avg("lvl").toFixed(0).padStart(4)} ${avg("kills").toFixed(0).padStart(6)}  ` +
        `${avg("evos").toFixed(1).padStart(5)}  ${clears}/${TRIALS}`);
    }
  }

  if (TIER === "vet") { await b.close(); return; }

  // where does the run actually end?
  console.log(`\n${"=".repeat(66)}\nDEATH TIMING (intern, first run, ${TRIALS*2} trials)\n${"=".repeat(66)}`);
  const deaths = [];
  for (let i = 0; i < TRIALS * 2; i++) deaths.push((await runOne("intern", false)).t);
  const buckets = {};
  for (const d of deaths) { const m = Math.floor(d / 120) * 2; buckets[m] = (buckets[m] || 0) + 1; }
  for (const k of Object.keys(buckets).sort((a, b) => a - b))
    console.log(`  ${String(k).padStart(2)}-${String(+k+2).padStart(2)} min  ` +
                "#".repeat(buckets[k]) + ` (${buckets[k]})`);

  await b.close();
})();
