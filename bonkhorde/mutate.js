// Mutation audit. A passing suite proves nothing unless it FAILS when the game
// is broken - and this one has already been caught twice passing against
// something other than what it claimed to measure (a lost WebGL context still
// showing its last frame, and a world that was frozen by accident).
//
// Each mutation below breaks one thing on purpose and names the section that
// must notice. A mutation that the suite survives is a section that is not
// testing what its name says.
//
//   node mutate.js            # run them all
//   node mutate.js reach      # just the ones whose id contains "reach"
const fs = require("fs"), path = require("path"), { execFileSync } = require("child_process");
const SRC = path.resolve(__dirname, "index.html");
const src = fs.readFileSync(SRC, "utf8");

const MUTANTS = [
  { id:"reach-to-centre", must:"7g",
    why:"weapons measure to the centre again, so a 4m body eats 4m of reach",
    from:"const dx=e.x-x, dz=e.z-z, reach=r+e.rad;",
    to:  "const dx=e.x-x, dz=e.z-z, reach=r;" },
  { id:"burn-uncapped", must:"7h",
    why:"overlapping hazards stack without limit again",
    from:"const BURN_STACK = 3;", to:"const BURN_STACK = 9999;" },
  { id:"scrapper-reach", must:"7i",
    why:"THE SCRAPPER loses the reach stat and nothing else changes",
    from:"mods:{ mag:1.7, spd:1.10, hp:.85, reach:1.35 } },",
    to:  "mods:{ mag:1.7, spd:1.10, hp:.85 } }," },
  { id:"context-loss-ignored", must:"12c",
    why:"the lost context is never claimed back, which is the shipped default",
    from:"  e.preventDefault();\n  ctxLost = true;", to:"  ctxLost = true;" },
  { id:"drag-look-dead", must:"15c",
    why:"mouse-look is gated on pointer lock again, freezing an embed's camera",
    from:"  if(document.pointerLockElement!==cv && !dragging) return;",
    to:  "  if(document.pointerLockElement!==cv) return;" },
  { id:"shake-always-on", must:"16",
    why:"reduced motion is accepted and then ignored",
    from:"const shakeMul = ()=> save.motion ? 1 : 0;",
    to:  "const shakeMul = ()=> 1;" },
  // First written against the X line alone, which the suite survived - and the
  // test was right: the stick drag it uses is purely vertical, so X was never
  // the axis under measurement. An incomplete mutation is a false alarm, the
  // same failure mode in the other direction.
  { id:"analog-ignored", must:"15",
    why:"the stick goes back to on/off, throwing away partial deflection",
    from:"    P.x = clamp(P.x + dx*P.spd*analog*dt, -ARENA+1.5, ARENA-1.5);\n" +
         "    P.z = clamp(P.z + dz*P.spd*analog*dt, -ARENA+1.5, ARENA-1.5);",
    to:  "    P.x = clamp(P.x + dx*P.spd*dt, -ARENA+1.5, ARENA-1.5);\n" +
         "    P.z = clamp(P.z + dz*P.spd*dt, -ARENA+1.5, ARENA-1.5);" },
  { id:"ladder-early", must:"17",
    why:"every rung pays out immediately, whatever the number says",
    from:"if(u.now(save, runStats) >= u.at)", to:"if(u.now(save, runStats) >= 0)" },
  { id:"ladder-repeats", must:"17",
    why:"a rung pays out again every single run",
    from:"    if(save.unlocked[u.id]) continue;\n", to:"" },
  { id:"shop-lock-ignored", must:"17",
    why:"the locked shop line is on sale from run one",
    from:"    if(u.lock && !save.unlocked[u.lock]) continue;      // not earned yet\n", to:"" },
  { id:"xpmul-ignored", must:"17",
    why:"THE ACCOUNTANT's whole identity silently does nothing",
    from:"  P.xp += v * (P.xpMul||1);", to:"  P.xp += v;" },
  { id:"camera-welded", must:"12d",
    why:"the boom goes back to being welded to the player",
    from:"  camAnchor[0] = lerp(camAnchor[0], px, kf);", to:"  camAnchor[0] = px;" },
];

const want = process.argv[2];
const run = MUTANTS.filter(m => !want || m.id.includes(want));
const TMP = path.resolve(__dirname, "_mutant.html");
let survived = 0;

for (const m of run) {
  if (!src.includes(m.from)) {
    console.log(`SKIP  ${m.id.padEnd(22)} anchor no longer in index.html`);
    survived++; continue;
  }
  fs.writeFileSync(TMP, src.replace(m.from, m.to));
  // The child writes its verdict to stdout and exits 1 on failure, so the
  // failure path is the NORMAL path here and its output is the whole point.
  // A first version read `out` only from the success return and scanned it for
  // the word FAIL; every mutation therefore came back "SURVIVED", including
  // ones the suite was catching cleanly. Which is the joke: the tool built to
  // check that a green result means something was itself green and meaningless.
  let out = "", crash = null;
  try {
    out = execFileSync(process.execPath, [path.resolve(__dirname, "test.js")],
      { env: { ...process.env, BONKHORDE_TARGET: "_mutant.html" },
        encoding: "utf8", stdio: ["ignore", "pipe", "pipe"],
        maxBuffer: 32 << 20, timeout: 30 * 60e3 });
  } catch (e) {
    out = String(e.stdout || "") + String(e.stderr || "");
    if (e.killed || e.signal) crash = `killed (${e.signal || "timeout"})`;
  }
  // The suite's own RESULT line is the verdict. Its absence means the run died
  // before finishing, which is neither caught nor survived - it is no data.
  const verdict = out.match(/RESULT: (\d+) passed, (\d+) failed/);
  if (!verdict) {
    console.log(`ERROR     ${m.id.padEnd(22)} expected ${m.must.padEnd(4)} ` +
                `no RESULT line - ${crash || "the suite did not finish"}`);
    survived++; continue;
  }
  const nFail = +verdict[2];
  const lines = out.split("\n");
  let section = "(none)";
  for (const line of lines) {
    if (line.includes("FAIL")) break;
    const h = line.match(/^=== ([\w.]+)\./);
    if (h) section = h[1];
  }
  const caught = nFail > 0;
  const right  = caught && section === m.must;
  console.log(`${caught ? (right ? "CAUGHT  " : "caught  ") : "SURVIVED"}  ` +
              `${m.id.padEnd(22)} expected ${m.must.padEnd(4)} ` +
              `${caught ? `first failure in ${section}, ${nFail} assertion(s)`
                        : "the suite passed a broken game"}`);
  if (!caught) survived++;
}
fs.existsSync(TMP) && fs.unlinkSync(TMP);
console.log(`\n${run.length - survived}/${run.length} mutations caught`);
process.exit(survived ? 1 : 0);
