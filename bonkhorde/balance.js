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
// BONKHORDE_NOEVENTS=1 measures the same build with side events switched
// off, which is the only way to read what they are actually worth.
const NOEV   = !!process.env.BONKHORDE_NOEVENTS;
// BONKHORDE_NOHOP=1 turns the autopilot's bunnyhopping off. The bot chains
// perfectly - it jumps on the frame it lands, every time - so it measures the
// CEILING of the mechanic and not the median player. Running the same build
// both ways is the only way to read what the hop is actually worth, and it is
// how the six-link version was caught doubling the first-run median.
const NOHOP  = !!process.env.BONKHORDE_NOHOP;
// BONKHORDE_NOEVO=1 holds the monster at the bottom of its line, so the
// evolution stat block can be read apart from everything that shipped with it.
const NOEVO  = !!process.env.BONKHORDE_NOEVO;
// BONKHORDE_CURVE="hpQuad,dmgDiv" overrides the difficulty curve for the whole
// bench, so a sweep is three env vars rather than three edits. Printed in the
// header of every table, because a balance number with no curve attached to it
// is a number you cannot reproduce.
// BONKHORDE_SEED pins the arena for every trial. Region layout and den placement
// are variance the bench does not want and cannot currently subtract: a
// candidate measured on 42 different arenas against a control measured on 42
// other arenas is comparing two things that differ in more than the candidate.
const SEED   = process.env.BONKHORDE_SEED ? +process.env.BONKHORDE_SEED : null;
const CURVE  = process.env.BONKHORDE_CURVE
             ? process.env.BONKHORDE_CURVE.split(",").map(Number) : null;
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

  const runOne = (ch, shopped) => p.evaluate(([ch, shopped, noEv, noHop, noEvo, curve, seed]) => {
    window.__g.wipeSave();
    if (curve) window.__g.curve(curve[0], curve[1], curve[2], curve[3]);
    if (seed !== null) window.__g.pin(seed);
    if (shopped) window.__g.setUpgrades(
      { hp:6, dmg:6, spd:5, mag:5, cd:5, crit:5, armor:5, start:3, rev:2 });
    window.__g.start(ch);
    if (noEv) window.__g.freezeEvents(true);   // startRun resets the timer
    window.__g.botHop(!noHop);
    if (noEvo) window.__g.freezeEvo(true);
    window.__g.bot(true);
    const st = window.__g.runOut();
    return { t: st.t, lvl: st.lvl, kills: st.kills, over: st.over, won: st.won, why: st.why,
             kit: window.__g.kit().length,
             evos: window.__g.kit().filter(k => k.includes("EVO")).length };
  }, [ch, shopped, NOEV, NOHOP, NOEVO, CURVE, SEED]);

  const tiers = TIER === "first" ? [false] : TIER === "vet" ? [true] : [false, true];
  for (const shopped of tiers) {
    console.log(`\n${"=".repeat(66)}`);
    console.log(shopped ? "VETERAN  (all permanent upgrades bought)"
                        : "FIRST RUN  (no permanent upgrades)");
    if (CURVE) console.log(`curve: hpQuad=${CURVE[0]} dmgDiv=${CURVE[1]} hpLin=${CURVE[2]} xpNeed=${CURVE[3]}`);
    if (SEED !== null) console.log(`arena pinned to seed ${SEED}`);
    console.log("=".repeat(66));
    // The median is the WRONG headline for this game and it has now cost a whole
    // round of work. Run lengths here are bimodal - a run either falls apart in
    // the first five minutes or coasts to the twenty-minute wall - so at n=3 or
    // n=6 the median is whichever side got one more sample, and it swings from
    // 05:08 to 24:00 on builds that are otherwise identical. `early` (share of
    // runs dead before 10:00) and `clears` are counts over every trial, they
    // move smoothly, and they are what the difficulty claim is actually about.
    console.log("char     n   early  median    worst     best   lvl  kills   evos  clears");
    let totEarly = 0, totClear = 0, totN = 0;
    for (const ch of CHARS) {
      const rs = [];
      for (let i = 0; i < TRIALS; i++) rs.push(await runOne(ch, shopped));
      const ts = rs.map(r => r.t).sort((a, b) => a - b);
      const med = ts[Math.floor(ts.length / 2)];
      const clears = rs.filter(r => r.won).length;   // NOT t>=1199 - sudden death runs past 20:00
      const early  = rs.filter(r => r.t < 600).length;
      const avg = k => (rs.reduce((s, r) => s + r[k], 0) / rs.length);
      totEarly += early; totClear += clears; totN += TRIALS;
      console.log(
        `${ch.padEnd(8)} ${String(TRIALS).padStart(2)}  ` +
        `${`${early}/${TRIALS}`.padStart(5)}  ` +
        `${fmt(med).padStart(6)}   ${fmt(ts[0]).padStart(6)}   ${fmt(ts[ts.length-1]).padStart(6)}  ` +
        `${avg("lvl").toFixed(0).padStart(4)} ${avg("kills").toFixed(0).padStart(6)}  ` +
        `${avg("evos").toFixed(1).padStart(5)}  ${clears}/${TRIALS}`);
    }
    console.log(`${"TOTAL".padEnd(8)} ${String(totN).padStart(2)}  ` +
                `${`${totEarly}/${totN}`.padStart(5)}` +
                `${"".padStart(40)}${totClear}/${totN}`);
  }

  // The histogram is twelve more full-length runs. When a sweep only needs the
  // table it is half the wall clock for nothing.
  if (TIER === "vet" || process.env.BONKHORDE_NOHIST) { await b.close(); return; }

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
