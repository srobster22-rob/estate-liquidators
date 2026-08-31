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
  // Re-pointed once already: the movement rewrite deleted the two lines this
  // used to target, and the harness reported SKIP. SKIP is counted as NOT
  // caught on purpose - a mutation whose anchor has drifted is a hole in the
  // audit that looks like a pass, and looking like a pass is the whole failure
  // mode this file exists to catch.
  // Re-pointed a second time, by bunnyhopping this time. Same lesson: an
  // anchor is a copy of a line of source, and every line of source is somebody
  // else's next edit.
  { id:"analog-ignored", must:"15",
    why:"the stick goes back to on/off, throwing away partial deflection",
    from:"  const wx = dx*P.spd*hm*analog, wz = dz*P.spd*hm*analog;",
    to:  "  const wx = dx*P.spd*hm, wz = dz*P.spd*hm;" },
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
    from:"  const got = v * (P.xpMul||1) * (P ? (biomeAt(P.x,P.z).mod.xp || 1) : 1);",
    to:  "  const got = v;" },
  { id:"camera-welded", must:"12d",
    why:"the boom goes back to being welded to the player",
    from:"  camAnchor[0] = lerp(camAnchor[0], px, kf);", to:"  camAnchor[0] = px;" },
  { id:"cache-never-opens", must:"18",
    why:"walking into a cache does nothing at all",
    from:"      if(near){\n        events.splice(i,1);", to:"      if(false){\n        events.splice(i,1);" },
  { id:"altar-charges-anywhere", must:"18",
    why:"the altar charges whether you are standing in it or not",
    from:"      e.chg = clamp(e.chg + (near ? dt : -dt*.32), 0, d.hold);",
    to:  "      e.chg = clamp(e.chg + dt, 0, d.hold);" },
  { id:"boon-not-durable", must:"18",
    why:"boons are written onto P and evaporate at the next passive pick",
    from:"  return Math.max(.58, 1*(m.cd||1)*(1-rank(\"cd\")*.035) * boonMul.cd",
    to:  "  return Math.max(.58, 1*(m.cd||1)*(1-rank(\"cd\")*.035)" },
  { id:"collector-charges", must:"18",
    why:"the collector walks at you like everything else, so there is no hunt",
    from:"    if(e.def.flee){", to:"    if(false){" },
  { id:"collector-never-rests", must:"18",
    why:"it never pauses, which is a treadmill rather than a chase",
    from:"      if(e.rest <= 0){ e.flash = Math.max(e.flash, .08); continue; }", to:"" },
  { id:"hop-window-open", must:"19",
    why:"any jump chains, so the timing window is not a window",
    from:"      if(P.hopWin > 0){            // landed and jumped again inside the window",
    to:  "      if(true){                    // landed and jumped again inside the window" },
  { id:"hop-no-speed", must:"19",
    why:"the chain counts up and buys nothing",
    from:"const hopMul = ()=> 1 + HOP_TOP * (1 - Math.pow(HOP_FALL, P ? P.hop : 0));",
    to:  "const hopMul = ()=> 1;" },
  { id:"hop-caps-early", must:"19",
    why:"the chain stops paying after a few links, which is what a hard cap did",
    from:"const HOP_WIN = .16, HOP_BUF = .14, HOP_MAX = 24,",
    to:  "const HOP_WIN = .16, HOP_BUF = .14, HOP_MAX = 3," },
  { id:"hop-never-bleeds", must:"19",
    why:"a chain earned once is a chain kept forever",
    from:"    else if(P.hop > 0) P.hop = Math.max(0, P.hop - (HOP_BLEED + P.hop*.55)*dt);", to:"" },
  { id:"hop-autohop", must:"19",
    why:"a held spacebar hops for you, which is free top speed for twenty minutes",
    from:"  if(e.code===\"Space\" && !e.repeat && running && !paused) jumpPressed();",
    to:  "  if(e.code===\"Space\" && running && !paused) jumpPressed();" },
  { id:"jump-unbuffered", must:"19b",
    why:"the press has to land inside one 16ms frame or it is thrown away",
    from:"function jumpPressed(){ jumpBuf = HOP_BUF; }",
    to:  "function jumpPressed(){ jumpBuf = 1e-9; }" },
  { id:"wall-square-again", must:"20",
    why:"the boundary goes back to a square whose corners are past the wall",
    from:"  if(d2 <= lim*lim) return [x, z];\n  const s = lim / Math.sqrt(d2);\n  return [x*s, z*s];",
    to:  "  return [x, z];" },
  { id:"events-outside", must:"20",
    why:"side events spawn wherever the ring lands them, wall or no wall",
    from:"      [x, z] = confine(P.x + Math.sin(a)*r, P.z + Math.cos(a)*r, 6);",
    to:  "      x = P.x + Math.sin(a)*r; z = P.z + Math.cos(a)*r;" },
  { id:"no-evolution", must:"21",
    why:"monsters never evolve; the line is decoration",
    from:"  if(want > stage) evolveTo(want);", to:"" },
  { id:"evo-is-a-rename", must:"21",
    why:"the stage changes name and nothing else",
    from:"  const r = k => (to[k]||1)/(from[k]||1);", to:"  const r = k => 1;" },
  { id:"evo-overheals", must:"21",
    why:"evolving refills the bar instead of paying back what it added",
    from:"  P.hp = Math.min(P.maxhp, P.hp + Math.max(0, P.maxhp - before));",
    to:  "  P.hp = P.maxhp;" },
  { id:"mon-level-shared", must:"21",
    why:"every monster shares one XP pool, so raising one raises all of them",
    from:"function monBank(id){ return (save.mon && save.mon[id]) || 0; }",
    to:  "function monBank(id){ let t=0; for(const k in (save.mon||{})) t+=save.mon[k]; return t; }" },
  { id:"one-body-plan", must:"21b",
    why:"every species draws the same mesh again, which is what it looked like",
    from:"  (BODY[mCh.type] || BODY.plain)(D);",
    to:  "  BODY.plain(D);" },
  { id:"forms-dont-change", must:"21b",
    why:"a line's three stages are the same animal at three sizes",
    from:"  boxSeq = 0;",
    to:  "  boxSeq = 0; D.st = 0;" },
  { id:"one-arena", must:"23",
    why:"the map is generated once and never again, which is the backdrop it was",
    from:"  rollWorld(pinSeed === null ? undefined : pinSeed);\n  dealDens(); makeTerrain(); uploadTerrain(); bakeMap();",
    to:  "  " },
  { id:"spawn-anywhere", must:"23",
    why:"a run can open with you standing in the sludge",
    from:"  cells = [{ x:0, z:0, b:BIOME_BY.grass }];",
    to:  "  cells = [{ x:0, z:0, b:pool[0] }];" },
  { id:"regions-inert", must:"23b",
    why:"the ground you stand on stops meaning anything",
    from:"  const groundSpd = sureFoot ? 1 : (bmod.spd || 1);",
    to:  "  const groundSpd = 1;" },
  { id:"ashes-free", must:"23b",
    why:"standing in the ashes costs nothing",
    from:"  let d = raw * P.tough * (biomeAt(P.x,P.z).mod.tough || 1);",
    to:  "  let d = raw * P.tough;" },
  { id:"heirloom-unmarked", must:"7f",
    why:"the thing exempted from the ground check loses what it was exempted FOR",
    from:"  drawnMarks++;", to:"" },
  { id:"mon-level-inert", must:"21",
    why:"monster levels are a number on a card and nothing else",
    from:"const monHp  = id => 1 + (monLvl(id)-1)*.020;",
    to:  "const monHp  = id => 1;" },
  { id:"boss-body-dropped", must:"22",
    why:"spawnBoss stops carrying the body key, so all four render the fallback",
    from:"c:b.c, h:b.h, w:b.w, ai:b.ai, body:b.body };",
    to:  "c:b.c, h:b.h, w:b.w, ai:b.ai };" },
  { id:"boss-lod-pinned", must:"22",
    why:"a boss is drawn at full detail from any distance again",
    from:"const lod = e.boss ? (dp < 45 ? 2 : dp < 90 ? 1 : 0)",
    to:  "const lod = e.boss ? (2)" },
  { id:"fowl-marker-only", must:"22",
    why:"GLIMMERFOWL draws its ring and beam and then no bird",
    from:"  drawnMarks++;\n  const stride",
    to:  "  drawnMarks++;\n  if(W) return;\n  const stride" },
  { id:"rank-runs-past-three", must:"22b",
    why:"a rank can be pushed past three again, so the ceiling is not a ceiling",
    from:"for(let i=0;i<n && P.kit[k].l<WMAX-1;i++)",
    to:  "for(let i=0;i<n && P.kit[k].l<9;i++)" },
  { id:"rank-capped-low", must:"22b",
    why:"three ranks read lv[0..2], which is a two-rank nerf calling itself a UI change",
    from:"const RANKMAP = [0, 2, 4];", to:"const RANKMAP = [0, 1, 2];" },
  { id:"passive-scale-lost", must:"22b",
    why:"passives stop scaling for the missing ranks, costing a third of every one",
    from:"const PSCALE = 5 / WMAX;", to:"const PSCALE = 1;" },
  { id:"eye-unclamped", must:"12b",
    why:"the camera boom reaches past the wall again and the frame renders as fog",
    from:"  if(er > CAM_R){ const f = CAM_R/er; eye[0] *= f; eye[2] *= f; }",
    to:  "" },
  // The four below cover checks written in the last handful of rounds. Two of
  // those rounds ended with a check that passed against a broken build, so
  // every new section gets a mutation here the moment it is written, rather
  // than waiting for the next time something quietly stops measuring.
  { id:"hazard-hits-wider-than-drawn", must:"7c",
    why:"the damaged area is bigger than the marked one, so reading the tell " +
        "stops saving you and a telegraph becomes decoration",
    from:"Math.hypot(P.x-h.x, P.z-h.z) < h.r){",
    to:  "Math.hypot(P.x-h.x, P.z-h.z) < h.r*1.6){" },
  { id:"brood-unleashed", must:"30",
    why:"a hatchling can be walked off across the arena and never comes back, " +
        "which is the whole reason the leash is on the player and not the pet",
    from:"if(Math.hypot(p2.x-P.x, p2.z-P.z) > s.rng + 12){ p2.x = P.x; p2.z = P.z; }",
    to:  "if(false){ p2.x = P.x; p2.z = P.z; }" },
  { id:"brood-never-grows", must:"30",
    why:"the pack stays one animal at every rank, so five ranks buy nothing",
    from:"const s = wStat(w), n = Math.min(6, s.n + dupeN());",
    to:  "const s = wStat(w), n = 1;" },
  { id:"pets-walk-through-bosses", must:"30",
    why:"a pet crossing to a ring slot on the far side walks through the boss " +
        "and stands inside it, which draws a hatchling buried in the model",
    from:"      const keep = biting.rad + .35;", to:"      const keep = 0;" },
  { id:"pack-stacks", must:"30",
    why:"a pack's own animals stand inside each other again, so six hatchlings " +
        "render as fewer than six and the rank you bought is invisible",
    from:"const PET_SEP = 1.1;", to:"const PET_SEP = 0;" },
  { id:"tail-comes-off", must:"29",
    why:"a tapered chain stops clamping to its own neighbours, so tails and " +
        "limbs float free of the body that owns them",
    from:"cap(dr, hx); cap(df, hz); cap(dy, hy);",
    to:  "s = 1;" },
  { id:"thicket-reach-ignored", must:"23c",
    why:"THE THICKET stops shortening weapon reach, so the region does " +
        "nothing but change colour",
    from:"const reach = P.reach * (biomeAt(P.x, P.z).mod.reach || 1);",
    to:  "const reach = P.reach;" },
  { id:"final-form-unreachable", must:"22n",
    why:"EVO_AT loses its fifth entry, so the final form exists in the data " +
        "but no run can ever reach it by levelling",
    from:"const EVO_AT = [1, 7, 20, 34, 48];",
    to:  "const EVO_AT = [1, 7, 20, 34];" },
  { id:"warren-swarm-ignored", must:"23d",
    why:"THE WARRENS stops speeding up the director, so the region does " +
        "nothing but change colour",
    from:"nextSpawn = 1/(ph.rate * (biomeAt(P.x, P.z).mod.swarm || 1)",
    to:  "nextSpawn = 1/(ph.rate * 1" },
  { id:"spring-regen-ignored", must:"23e",
    why:"THE HOTSPRINGS stops multiplying regeneration, so the tenth region " +
        "does nothing but change colour",
    from:"P.hp = Math.min(P.maxhp, P.hp + P.regen*dt * (bmod.regen || 1));",
    to:  "P.hp = Math.min(P.maxhp, P.hp + P.regen*dt);" },
];

// A stale anchor is a hole in the audit that reads as a pass, and the full run
// takes over an hour to tell you. This takes milliseconds and needs no browser,
// so CI can hold every mutation to the source on every push.
if (process.argv[2] === "--anchors") {
  const bad = MUTANTS.filter(m => !src.includes(m.from));
  console.log("=".repeat(70));
  console.log("ANCHOR CHECK  -  every mutation must still find its target");
  console.log("-".repeat(70));
  for (const m of bad) console.log(`  FAIL  ${m.id}: anchor no longer in index.html`);
  if (!bad.length) console.log(`  OK   ${MUTANTS.length} mutations, every anchor present`);
  process.exit(bad.length ? 1 : 0);
}

// RESUMABLE, because a full pass is 48 browser suites and this machine is never
// free for the four hours that takes. One run was lost to a container restart at
// row 37 and another wedged on a single mutant for six hours, and both threw
// away everything already measured. With --resume the results FILE is the
// state: rows already in it are skipped, and each new row is appended the
// moment it is known, so a pass can be run in slices between other work and
// survives anything that kills it.
//
//   node mutate.js --resume        # everything not yet recorded
//   node mutate.js --resume 4      # at most four more, then stop
const RESUME = process.argv.includes("--resume");
const LOG = path.resolve(__dirname, "mutate-results.txt");
const done = new Set();
let slice = Infinity;
if (RESUME) {
  if (fs.existsSync(LOG))
    for (const line of fs.readFileSync(LOG, "utf8").split("\n")) {
      const mm = line.match(/^\S+\s+(\S+)/);
      if (mm) done.add(mm[1]);
    }
  const n = process.argv.slice(3).find(a => /^\d+$/.test(a));
  if (n) slice = +n;
  console.log(`resuming: ${done.size} recorded, ${MUTANTS.length - done.size} to go` +
              (slice === Infinity ? "" : `, doing at most ${slice} now`));
}
const want = RESUME ? null : process.argv[2];
let run = MUTANTS.filter(m => (!want || m.id.includes(want)) && !done.has(m.id));
if (slice !== Infinity) run = run.slice(0, slice);
// ONE TEMP FILE PER RUN, named after the process. Two audits sharing a fixed
// filename do not fail loudly, they fail as nonsense: the second run's children
// load whatever the first run last wrote, so a mutation gets scored against
// somebody else's game, and when one run finishes and unlinks the file the
// other's next page load dies on ERR_FILE_NOT_FOUND. Both happened - a stale
// audit that a kill had not actually reaped was still writing this path while
// a fresh one ran, and the fresh one's rows came back as a wall of
// "no RESULT line" that looked like findings.
const TMP  = path.resolve(__dirname, `_mutant.${process.pid}.html`);
// SNAPSHOT THE SUITE TOO, not just the game. A full run takes hours, and this
// tool read `src` once at startup but shelled out to test.js FROM DISK for
// every mutant - so editing the suite mid-run silently changed the instrument
// underneath the experiment. It happened: a round added a setHp QA hook to
// index.html and a check that calls it to test.js, and every mutant after that
// point ran the new suite against a snapshot of the game that predated the
// hook. g.setHp was not a function, the harness died in section 21 whatever
// the mutation was, and eight consecutive rows came back "no RESULT line" -
// scored as holes, and every one of them an artefact of the edit rather than a
// finding. Copying the suite next to the mutant makes a run a snapshot of BOTH
// halves, so an audit measures the pair it started with.
const TMPT = path.resolve(__dirname, `_mutant.${process.pid}.test.js`);
fs.writeFileSync(TMPT, fs.readFileSync(path.resolve(__dirname, "test.js"), "utf8"));
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
    out = execFileSync(process.execPath, [TMPT],
      { env: { ...process.env, BONKHORDE_TARGET: path.basename(TMP) },
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
    // AND WHY. A full run costs about five minutes, so an ERROR that says only
    // "did not finish" buys a second five minutes to find out what everybody
    // already had on stdout. The tail is almost always the answer: the section
    // header it died under, and the exception under that. Note the difference
    // this exposes - a `crash` value means the child was KILLED (timeout, a
    // signal), while its absence means the child exited on its own without
    // printing a verdict, which is a crash rather than a hang.
    const tail = out.trimEnd().split("\n").slice(-8);
    for (const line of tail) console.log(`          | ${line}`);
    survived++; continue;
  }
  const nFail = +verdict[2];
  // WHICH SECTIONS FAILED, not just the first one. Reading only the first was
  // ambiguous in a way that hid a real hole: a lower-case "caught" meant "the
  // first failure was somewhere else", which is damning when the expected
  // section runs EARLIER (it ran and passed a broken game) and means nothing
  // when it runs later (it may never have been reached before something else
  // went red). Both printed the same. collector-never-rests was the first kind
  // and section 18 had genuinely stopped working; jump-unbuffered looked
  // identical and was the second kind. Track every section that failed, and
  // say plainly whether the one that owns this mutation was among them.
  const lines = out.split("\n");
  let section = "(none)", first = null;
  const failedIn = new Set();
  for (const line of lines) {
    const h = line.match(/^=== ([\w.]+)\./);
    if (h) { section = h[1]; continue; }
    if (line.includes("FAIL")) { failedIn.add(section); if (!first) first = section; }
  }
  const caught = nFail > 0;
  const byOwner = failedIn.has(m.must);
  const tag = !caught ? "SURVIVED" : byOwner ? "CAUGHT  " : "elsewhere";
  const row = `${tag.padEnd(9)} ${m.id.padEnd(22)} expected ${m.must.padEnd(4)} ` +
              `${caught ? `${nFail} assertion(s), first in ${first}` +
                          (byOwner ? (first === m.must ? "" : ` and ${m.must} also caught it`)
                                   : ` - ${m.must} did NOT`)
                        : "the suite passed a broken game"}`;
  console.log(row);
  // Append the moment it is known, not at the end: a run that dies has still
  // banked everything it measured.
  if (RESUME) fs.appendFileSync(LOG, row + "\n");
  // A mutation caught only by a section that does not own it is a hole in the
  // owning section, even though the suite went red. Count it as one.
  if (!caught || !byOwner) survived++;
}
fs.existsSync(TMP) && fs.unlinkSync(TMP);
fs.existsSync(TMPT) && fs.unlinkSync(TMPT);
console.log(`\n${run.length - survived}/${run.length} mutations caught`);
process.exit(survived ? 1 : 0);
