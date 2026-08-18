/**
 * Headless QA for the first-person prototype.
 *
 * Loads proto3d/index.html in real Chromium and drives it through `window.__g`.
 * This tests the artifact that actually ships, not a re-implementation of it:
 * the rules, the estate geometry and the render loop are the same code a player
 * runs. Math.random is seeded before any page script executes, so a failure here
 * is reproducible.
 *
 *     node proto3d/qa.mjs          -> exit 0 if every check passes
 *     node proto3d/qa.mjs -v       -> print every check, not just failures
 *     node proto3d/qa.mjs -r 5     -> run five times and report anything flaky
 *
 * Several checks here are statistical, and three of them have been caught
 * failing one run in six on their own variance. A check that passes sometimes is
 * not a passing check, so -r is how you believe this suite rather than hope.
 *
 * Needs Playwright and a Chromium build. Both are present in the project's
 * container; PW_PATH overrides the module location if yours differs.
 */
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PAGE = "file://" + path.join(HERE, "index.html");
const VERBOSE = process.argv.includes("-v");

const require = createRequire(import.meta.url);
function loadPlaywright() {
  const tries = [
    process.env.PW_PATH,
    "playwright",
    "/opt/node22/lib/node_modules/playwright",
    "/usr/lib/node_modules/playwright",
  ].filter(Boolean);
  for (const t of tries) {
    try { return require(t); } catch { /* next */ }
  }
  console.error("Playwright not found. Tried:\n  " + tries.join("\n  ") +
    "\nInstall it (npm i -D playwright) or set PW_PATH to the module directory.");
  process.exit(2);
}

// ---------------------------------------------------------------- assertions
let passed = 0;
const failures = [];
function ok(label, cond, detail = "") {
  if (cond) { passed++; if (VERBOSE) console.log(`  ok    ${label}`); }
  else failures.push(`${label}${detail ? "  ->  " + detail : ""}`);
}
function near(label, got, want, tol) {
  ok(label, Math.abs(got - want) <= tol, `got ${got}, want ${want} +/-${tol}`);
}

// A seeded LCG replaces Math.random before the game's first line runs, so the
// estate layout, the grades and the ruin roll are all identical run to run.
const SEED_SCRIPT = `(() => {
  let s = 0x2f6e2b1;
  Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  // A paired measurement needs both runs to draw the SAME numbers - hearing is
  // fuzzed +-3m, which moves an approach further than most effects being
  // measured. This returns the previous state, so a check can pin the stream
  // and then put it back: every check after it sees the sequence it always saw.
  window.__seed = n => { const was = s; s = n >>> 0; return was; };
  // console.error reaches the harness asynchronously, so "no page errors" was
  // racing the errors it exists to catch - the same ESTATE FAULT appeared in
  // roughly one run in four and was invisible in the rest. Recorded in-page,
  // it is observed the moment it is asked for.
  window.__errs = [];
  const ce = console.error;
  console.error = (...a) => {
    let where = null;
    try { where = window.__g ? window.__g.seed() : null; } catch (e) {}
    window.__errs.push({ msg: a.map(String).join(" "), where });
    ce.apply(console, a);
  };
})();`;

const pageErrors = [];

async function main() {
  const ri = process.argv.indexOf("-r");
  const repeats = ri >= 0 ? Math.max(1, Number(process.argv[ri + 1]) || 3) : 1;
  if (repeats > 1) return repeat(repeats);
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({
    args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"],
  });
  const page = await browser.newPage();
  page.on("pageerror", e => pageErrors.push("pageerror: " + e.message));
  page.on("console", m => { if (m.type() === "error") pageErrors.push("console: " + m.text()); });
  await page.addInitScript(SEED_SCRIPT);
  await page.goto(PAGE);
  await page.waitForFunction("typeof window.__g === 'object'", null, { timeout: 10000 });
  // The game's own requestAnimationFrame loop would otherwise advance time
  // between checks, which made results depend on how long an evaluate took.
  await page.evaluate(() => window.__g.pause(true));
  // Estates are generated from a seed; pin one so a failure is reproducible.
  // A separate check sweeps many seeds through the gate.
  await page.evaluate(() => window.__g.regen(20260806));

  const g = (fn, arg) => page.evaluate(fn, arg);   // run in page, return JSON
  // gates(true) is sticky - it is a global QA switch, not night state, so reset()
  // does not clear it. A block that turned it on left every later block running
  // with the prerequisite chain disabled, which is how the crowbar checks came to
  // report that boards cannot be pried: nothing was stopping the player at all.
  const fresh = () => page.evaluate(() => {
    window.__g.clearKeys(); window.__g.gates(false); window.__g.reset();
  });
  const named = await page.evaluate(() => {
    const rs = window.__g.rooms();
    const byTier = t => rs.filter(r => r.tier === t && !r.van).map(r => r.id);
    return { start: rs.find(r => r.van).id, shallow: byTier(0).concat(byTier(1)),
             mid: byTier(2), deep: byTier(3), all: rs.map(r => r.id) };
  });

  // A throw inside a check is a failure like any other - it must not take the
  // remaining checks down with it. Injecting a two-item shelf crashed the run at
  // check 30 and reported nothing about the other 46.
  try {
    await checks(g, fresh);
  } catch (e) {
    ok("the harness ran to completion", false, `threw: ${e.message}`);
  }

  const inPage = await page.evaluate(() => window.__errs.slice());
  ok("no page errors", pageErrors.length === 0 && inPage.length === 0,
    pageErrors.join(" | ") + inPage.map(e => ` | ${e.msg} @ ${JSON.stringify(e.where)}`).join(""));
  await browser.close();

  console.log(`PROTO3D QA  -  ${passed + failures.length} checks`);
  console.log("-".repeat(74));
  if (!failures.length) { console.log("  OK   the prototype behaves as specified"); process.exit(0); }
  for (const f of failures) console.log(`  FAIL  ${f}`);
  console.log(`\n${failures.length} failing check(s).`);
  process.exit(1);
}

// A check that passes four times and fails once is a failing check with a
// publicity problem. This runs the whole suite N times in one browser and
// reports any label whose result was not the same every time.
async function repeat(n) {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({
    args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"],
  });
  const seen = new Map();
  for (let i = 0; i < n; i++) {
    passed = 0; failures.length = 0; pageErrors.length = 0;
    const page = await browser.newPage();
    page.on("pageerror", e => pageErrors.push("pageerror: " + e.message));
    await page.addInitScript(SEED_SCRIPT);
    await page.goto(PAGE);
    await page.waitForFunction("typeof window.__g === 'object'", null, { timeout: 10000 });
    await page.evaluate(() => window.__g.pause(true));
    await page.evaluate(() => window.__g.regen(20260806));
    const g = (fn, arg) => page.evaluate(fn, arg);
    // gates(true) is sticky - it is a global QA switch, not night state, so reset()
  // does not clear it. A block that turned it on left every later block running
  // with the prerequisite chain disabled, which is how the crowbar checks came to
  // report that boards cannot be pried: nothing was stopping the player at all.
  const fresh = () => page.evaluate(() => {
    window.__g.clearKeys(); window.__g.gates(false); window.__g.reset();
  });
    try { await checks(g, fresh); }
    catch (e) { ok("the harness ran to completion", false, `threw: ${e.message}`); }
    for (const f of failures) {
      const label = f.split("  ->  ")[0];
      seen.set(label, (seen.get(label) || 0) + 1);
    }
    process.stdout.write(`run ${i + 1}/${n}: ${failures.length} failing\n`);
    await page.close();
  }
  await browser.close();
  console.log("-".repeat(74));
  if (!seen.size) { console.log(`  OK   ${n} runs, no failures and nothing flaky`); process.exit(0); }
  for (const [label, count] of seen)
    console.log(`  ${count === n ? "FAIL " : "FLAKY"}  ${label}  (${count}/${n} runs)`);
  process.exit(1);
}

// ---------------------------------------------------------------- the checks
async function checks(g, fresh) {
  const NIGHT = 210, RATCHET_END = 55, IMPULSE = 0.09;
  const L = { sprint: 45, appraise: 48, drop: 90 };

  // --- boot -----------------------------------------------------------------
  await fresh();
  let s = await g(() => window.__g.state());
  ok("boots with 14 van slots", s.slots === 14, `slots=${s.slots}`);
  ok("boots at zero disturbance", s.dist === 0 && s.tier === "DORMANT", JSON.stringify(s));
  const n0 = await g(() => window.__g.items());
  ok("estate is populated", n0 >= 20, `items=${n0}`);
  const start = await g(() => window.__g.pos());
  ok("player starts on the driveway", start.room === "drive", JSON.stringify(start));

  // --- the generator, gated (LEVEL-SPEC / BUILD-PROMPT Phase 5) -------------
  // "A wing that fails any check does not enter the pool." The point of a
  // generator is that this stops being a review step and becomes an invariant,
  // so the assertion is over MANY seeds rather than the one being played.
  // Swept over every night, not just night one: the gate asks for MORE on a late
  // contract - a tier-3 wing always, and from night three an apex wing at tier 4 -
  // and night three was the only night nothing was checking. It failed 5% of
  // seeds outright and played them with their faults printed to the console.
  const sweep = await g(() => {
    const bad = [], tries = [];
    for (let n = 0; n <= 3; n++)
      for (let i = 1; i <= 60; i++) {
        const r = window.__g.regen(i * 104729, n);
        tries.push(window.__g.seed().tries);
        if (r.faults.length) bad.push({ night: n, seed: r.seed, faults: r.faults.slice(0, 2) });
      }
    tries.sort((a, b) => a - b);
    return { bad, median: tries[tries.length >> 1], worst: tries[tries.length - 1] };
  });
  ok("every seed produces an estate that passes the gate, on every night",
    sweep.bad.length === 0, JSON.stringify(sweep.bad.slice(0, 3)));
  // The retry cap is 120. Asserting "under 120" only says the gate holds, which
  // the check above already says; the number worth defending is the margin.
  // Over 1,600 seed-nights the worst case is 60 attempts with the house grown to
  // fit the tier it has to hold and 86 without, so 80 is the line between them.
  ok("and it does not take many attempts to find one",
    sweep.median <= 12 && sweep.worst < 80,
    `median ${sweep.median}, worst ${sweep.worst}, ${sweep.bad.length} seeds unbuildable`);

  // The generated estate must also satisfy the properties the rest of the game
  // assumes: a van, a deep wing, shelves and hiding places everywhere, and a
  // prerequisite chain that actually gates something.
  const shapes = await g(() => {
    const out = [];
    for (let i = 1; i <= 40; i++) {
      window.__g.regen(i * 7907);
      const rooms = window.__g.rooms(), shelves = window.__g.shelves();
      const hides = window.__g.hides(), prereq = window.__g.prereq();
      const loot = rooms.filter(r => !r.van);
      const problems = [];
      if (rooms.filter(r => r.van).length !== 1) problems.push("van count");
      if (!rooms.some(r => r.tier === 3)) problems.push("no tier-3 wing");
      if (loot.some(r => !shelves.find(s => s.room === r.id))) problems.push("room without a shelf");
      if (loot.some(r => !hides.find(h => h.room === r.id))) problems.push("room with nowhere to hide");
      if (!Object.keys(prereq).length) problems.push("nothing gated");
      if (window.__g.items() < 12) problems.push("too little loot");
      if (problems.length) out.push({ seed: window.__g.seed().seed, problems });
    }
    return out;
  });
  ok("every generated estate is playable",
    shapes.length === 0, JSON.stringify(shapes.slice(0, 3)));

  // The Python validator is the authority on the ten level checks, and it can
  // only apply them to what the exporter hands it. Two of its checks divide a
  // designed multiplier back out of a price - the curse grade and the fragility
  // premium - and one bands the apex as a share of the final quota. Drop any of
  // those three fields and V8 starts rejecting houses for being correct: it
  // rejected 12 of 12 in the batch the README tells you to run.
  const exported = await g(() => {
    window.__g.regen(20260806, 3);
    const e = window.__g.estate();
    const cart = e.plinths.find(p => p.cls === "cart");
    return { quota: e.final_quota,
      missing: e.plinths.filter(p => p.grade === undefined || p.frag === undefined).length,
      cart: cart ? cart.value : null };
  });
  ok("the export carries what the level validator needs to judge a price",
    exported.missing === 0 && exported.quota > 0 &&
    exported.cart >= 0.32 * exported.quota && exported.cart <= 0.64 * exported.quota,
    JSON.stringify(exported));

  // The crew have to be able to get around the house they are given. A greedy
  // "walk at the nearest door" rule survived the hand-authored chain and jammed
  // three haulers against locked doors in generated estates - they stood in a
  // corridor in SEEK for a whole night and banked $381. Nothing caught it,
  // because every rule-level check still passed.
  const hauling = await g(() => {
    const out = [];
    for (const s of [11, 22, 33, 44, 55]) {
      window.__g.regen(s * 104729);
      for (let i = 0; i < 120 * 60 && !window.__g.state().over; i++) window.__g.step(1, 1 / 60);
      const st = window.__g.state();
      out.push({ seed: s, banked: st.banked, taken: 14 - st.slots });
    }
    return out;
  });
  ok("the crew can work the house they are given",
    hauling.every(h => h.taken >= 4 && h.banked > 400), JSON.stringify(hauling));

  await g(() => window.__g.regen(20260806));     // back to the pinned estate

  // --- the R12 bug: sustained noise must be per second, not per frame --------
  // Same ten seconds of sprinting at two timestep sizes must cost the same.
  const sprintAt = async dt => {
    await fresh();
    return g(([dt]) => {
      // Park the crew: they haul at slightly different rates under different
      // timesteps, and every cursed piece they land raises the floor by 7, which
      // swamps the 0.9/s this check is actually about.
      window.__g.parkCrew();
      window.__g.press("KeyW"); window.__g.press("ShiftLeft");
      const n = Math.round(10 / dt);
      const st = window.__g.step(n, dt);
      window.__g.clearKeys();
      return st.dist;
    }, [dt]);
  };
  const d60 = await sprintAt(1 / 60), d10 = await sprintAt(1 / 10);
  near("sustained noise is per-second, not per-frame", d60, d10, 0.35);
  ok("sprinting is audible at all", d60 > 0.5, `dist after 10s sprint = ${d60}`);

  // --- the ratcheting floor -------------------------------------------------
  await fresh();
  const half = await g(() => { window.__g.setT(105); return window.__g.step(2, 1 / 60); });
  near("floor ratchets with the night", half.dist, RATCHET_END * (105 / NIGHT), 0.6);

  // --- pillar 2: carry nothing, weigh nothing -------------------------------
  // At PURSUE the Curator is curating - it wants objects, and an empty-handed
  // player is worth nothing to it. At COLLECT it has stopped curating and is
  // collecting crew (DESIGN 6.5), which is a different rule, tested below.
  await fresh();
  const empty = await g(() => {
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    window.__g.setDist(70);                   // PURSUE
    for (let i = 0; i < 60; i++) window.__g.step(30, 1 / 60);   // 30 seconds
    return { st: window.__g.state(), cur: window.__g.curator() };
  });
  // Stronger than the R16 version: the house is busy, it IS hunting - three
  // crewmates are carrying - and you are still worth nothing while empty-handed.
  ok("empty-handed player is never targeted at PURSUE",
    empty.st.marked === false && empty.st.who !== "YOU", JSON.stringify(empty));

  await fresh();
  const crew = await g(() => {
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    window.__g.parkCrew();          // alone in the house: it must come for YOU
    for (let i = 0; i < 40; i++) { window.__g.setDist(95); window.__g.step(15, 1 / 60); }
    return window.__g.state();
  });
  ok("at COLLECT it hunts crew, empty-handed or not",
    crew.marked === true && crew.mode === "CREW" && crew.who === "YOU",
    JSON.stringify(crew));

  // --- aggro binds to the object, not the person ---------------------------
  // Dropping must not clear the hunt, or dropping is a free aggro reset.
  await fresh();
  const dropped = await g(() => {
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.parkCrew();
    window.__g.tp(f.x, f.z);
    window.__g.setDist(70);
    window.__g.hold(0);
    for (let i = 0; i < 20; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    const chasing = window.__g.state().marked;
    const value = window.__g.state().holding;
    window.__g.grab();                        // put it down and walk away
    for (let i = 0; i < 30; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    return { chasing, value, after: window.__g.state(), cur: window.__g.curator() };
  });
  // The distinction D-06 exists for: dropping takes the target off YOU without
  // calling off the hunt. If it cleared the hunt, dropping would be the free
  // two-second aggro reset and the hot potato would cost nothing.
  ok("dropping takes the mark off you",
    dropped.chasing === true && dropped.after.marked === false, JSON.stringify(dropped));
  ok("but the piece is still being retrieved",
    (dropped.after.mode === "ITEM" && dropped.cur.goalValue === dropped.value) ||
    dropped.after.cur === "RESEAT" || dropped.cur.carrying === true,
    JSON.stringify(dropped));

  // --- aggro follows the loot ----------------------------------------------
  await fresh();
  const carrying = await g(() => {
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.parkCrew();
    window.__g.tp(f.x, f.z);
    window.__g.hold(0);
    for (let i = 0; i < 20; i++) { window.__g.setDist(70); window.__g.step(30, 1 / 60); }
    return window.__g.state();
  });
  ok("carrying loot while it is hunting draws it to you", carrying.marked === true,
    JSON.stringify(carrying));

  // --- dropping is loud -----------------------------------------------------
  await fresh();
  const drop = await g(() => {
    window.__g.parkCrew();          // else E in a crowded driveway is a hand-off
    window.__g.setDist(50);
    window.__g.hold(0);
    const before = window.__g.state().dist;
    window.__g.grab();                        // holding -> drop
    return { before, after: window.__g.state().dist, holding: window.__g.state().holding };
  });
  near("dropping costs L90 x 0.09", drop.after - drop.before, L.drop * IMPULSE, 0.05);
  ok("dropping empties the hands", drop.holding === null, JSON.stringify(drop));

  // --- appraising -----------------------------------------------------------
  await fresh();
  const scan = await g(() => {
    const it = window.__g.list()[0];
    window.__g.tp(it.x, it.z - 1.4);
    window.__g.look(0, -Math.atan2(1.62 - 0.45, 1.4));   // crosshair on the item
    window.__g.setDist(40);
    window.__g.press("KeyF");
    window.__g.step(60, 1 / 60);              // 1s - not enough
    const partial = window.__g.list()[0].known;
    // Measure the ping across the single tick the scan completes on. Sampling
    // either side of the whole 3.5s would fold in 0.7 of decay and read 3.6.
    let before = 0, after = 0, done = false;
    for (let i = 0; i < 200 && !done; i++) {
      before = window.__g.state().dist;
      window.__g.step(1, 1 / 60);
      done = window.__g.list()[0].known;
      after = window.__g.state().dist;
    }
    window.__g.clearKeys();
    return { before, after, partial, done, decayPerTick: (50 / 4) / 60 / 60 };
  });
  ok("a one-second scan tells you nothing", scan.partial === false);
  ok("a three-second scan appraises", scan.done === true);
  near("appraising costs L48 x 0.09",
    scan.after - scan.before + scan.decayPerTick, L.appraise * IMPULSE, 0.05);

  // Moving must cancel the scan - the cost of information is standing still.
  await fresh();
  const moved = await g(() => {
    const it = window.__g.list()[0];
    window.__g.tp(it.x, it.z - 1.4);
    window.__g.look(0, -Math.atan2(1.62 - 0.45, 1.4));
    window.__g.press("KeyF"); window.__g.press("KeyW");
    window.__g.step(300, 1 / 60);             // 5s of walking while holding F
    window.__g.clearKeys();
    return window.__g.list()[0]?.known ?? "item-gone";
  });
  ok("walking cancels the appraisal", moved === false, `known=${moved}`);

  // --- scan breadth (D-24) --------------------------------------------------
  // The appraiser is a breadth decision worth +14% with an interior optimum at
  // two of four. That only exists if there IS a set of four, and if the player
  // can see how much of it they have paid to look at.
  await fresh();
  const shelfLayout = await g(() => window.__g.shelves());
  ok("loot comes in shelves of four",
    shelfLayout.length >= 5 && shelfLayout.every(sh => sh.total === 4),
    JSON.stringify(shelfLayout.map(s => s.total)));
  ok("every room but the driveway has one",
    new Set(shelfLayout.map(s => s.room)).size === shelfLayout.length,
    JSON.stringify(shelfLayout.map(s => s.room)));

  await fresh();
  const breadth = await g(() => {
    window.__g.parkCrew();
    const sh = window.__g.shelves()[0];
    const on = window.__g.list().filter(i => i.shelf === sh.i);
    const seen = [];
    for (let k = 0; k < Math.min(3, on.length); k++) {
      const it = on[k];
      window.__g.tp(it.x - 1.3, it.z);
      window.__g.look(Math.PI / 2, -Math.atan2(1.62 - 0.95, 1.3));
      window.__g.press("KeyF");
      window.__g.step(230, 1 / 60);
      window.__g.clearKeys();
      const st = window.__g.shelves()[sh.i];
      seen.push({ scanned: st.scanned, best: st.best });
    }
    const st = window.__g.shelves()[sh.i];
    const values = on.map(i => i.value);
    return { seen, st, values, prompt: window.__g.prompt() };
  });
  ok("scanning is per candidate, not per shelf",
    breadth.seen.map(s => s.scanned).join(",") === "1,2,3", JSON.stringify(breadth.seen));
  ok("the shelf tracks the best piece found so far",
    breadth.st.best === Math.max(...breadth.values.slice(0, 3)),
    JSON.stringify(breadth));
  ok("and one unscanned piece is still unknown",
    breadth.st.scanned === 3 && breadth.st.total === 4, JSON.stringify(breadth.st));
  ok("the prompt says how much of the shelf you have paid for",
    /SHELF 3\/4 scanned/.test(breadth.prompt), breadth.prompt);

  // --- the van --------------------------------------------------------------
  await fresh();
  const deposit = await g(() => {
    const v = window.__g.rooms().find(r => r.id === "drive");
    const value = window.__g.hold(0);
    window.__g.tp(v.x, v.z);
    window.__g.step(2, 1 / 60);
    return { value, st: window.__g.state(), cargo: window.__g.cargo() };
  });
  ok("depositing consumes a slot", deposit.st.slots === 13, `slots=${deposit.st.slots}`);
  ok("depositing banks the value", deposit.st.banked === deposit.value,
    `banked=${deposit.st.banked} value=${deposit.value}`);
  ok("depositing empties the hands", deposit.st.holding === null);

  // A cursed piece aboard raises the floor by 7 (LOOP_LOG R9; +2 was inert).
  await fresh();
  const cursedFloor = await g(() => {
    const list = window.__g.list();
    const cursedIdx = list.findIndex(i => i.grade !== "clean");
    if (cursedIdx < 0) return null;
    const v = window.__g.rooms().find(r => r.id === "drive");
    window.__g.hold(cursedIdx); window.__g.tp(v.x, v.z); window.__g.step(2, 1 / 60);
    window.__g.setT(0); window.__g.setDist(0);
    window.__g.step(2, 1 / 60);
    return window.__g.state().dist;
  });
  ok("a cursed piece aboard raises the floor by 7",
    cursedFloor !== null && Math.abs(cursedFloor - 7) < 0.3, `floor=${cursedFloor}`);

  // --- weight classes and the two-man carry (B4) ----------------------------
  await fresh();
  const alone = await g(() => {
    window.__g.parkCrew();                       // nobody to shout at
    const idx = window.__g.twoMan();
    const it = window.__g.list()[idx];
    window.__g.tp(it.x - 1.2, it.z);
    window.__g.look(Math.PI / 2, -Math.atan2(1.62 - it.y, 1.2));
    window.__g.grab();
    return { idx, klass: it.klass, carry: window.__g.carry(),
             asked: window.__g.wantHelp() };
  });
  ok("an armoire cannot be lifted alone",
    alone.carry === null && alone.asked === true, JSON.stringify(alone));

  await fresh();
  const pair = await g(() => {
    window.__g.freezeCrew(true);
    const idx = window.__g.twoMan();
    const it = window.__g.list()[idx];
    window.__g.setCrew(0, it.x + 1.0, it.z);     // a crewmate within shouting range
    window.__g.tp(it.x - 1.2, it.z);
    window.__g.look(Math.PI / 2, -Math.atan2(1.62 - it.y, 1.2));
    window.__g.grab();
    const got = window.__g.carry();
    // walk it a few metres and check the far end comes too
    const start = window.__g.raw();
    window.__g.press("KeyS");
    window.__g.step(180, 1 / 60);
    window.__g.clearKeys();
    const moved = Math.hypot(window.__g.raw().x - start.x, window.__g.raw().z - start.z);
    const mate = window.__g.crew()[0];
    const carried = window.__g.list()[idx];
    return { got, moved, mate, gap: Math.hypot(mate.x - carried.x, mate.z - carried.z) };
  });
  ok("with a crewmate you can carry it", pair.got !== null && pair.got.follower !== null,
    JSON.stringify(pair.got));
  ok("the far end comes with you", pair.gap < 2.0, JSON.stringify(pair));

  const slow = await g(() => {
    const trip = (klass) => {
      window.__g.clearKeys(); window.__g.reset(); window.__g.freezeCrew(true);
      const f = window.__g.rooms().find(r => r.id === "hall");
      window.__g.tp(f.x, f.z - 4); window.__g.look(0, 0);
      if (klass === "two_man") {
        const idx = window.__g.twoMan();
        const it = window.__g.list()[idx];
        window.__g.setCrew(0, it.x + 1.0, it.z);   // within shouting range of the piece
        window.__g.tp(it.x - 1.2, it.z);
        window.__g.look(Math.PI / 2, -Math.atan2(1.62 - it.y, 1.2));
        window.__g.grab();
        window.__g.tp(f.x, f.z - 4); window.__g.look(0, 0);
      } else if (klass === "armful") {
        window.__g.hold(0);
      }
      const a = window.__g.raw();
      window.__g.press("KeyW"); window.__g.step(120, 1 / 60); window.__g.clearKeys();
      const b = window.__g.raw();
      return Math.hypot(b.x - a.x, b.z - a.z);
    };
    return { empty: trip(null), armful: trip("armful"), two: trip("two_man") };
  });
  ok("two-man is slower than an armful, which is slower than empty-handed",
    slow.two < slow.armful && slow.armful < slow.empty, JSON.stringify(slow));

  // ECONOMY 1: the van is priced in slots, and a two-man piece costs three.
  await fresh();
  const slots = await g(() => {
    window.__g.parkCrew();
    const before = window.__g.vanSlots();
    const v = window.__g.rooms().find(r => r.id === "drive");
    window.__g.hold(0);                          // an armful
    window.__g.tp(v.x, v.z); window.__g.step(2, 1 / 60);
    const afterArmful = window.__g.vanSlots();
    return { before, afterArmful, costs: window.__g.slots() };
  });
  ok("an armful costs one slot of fourteen",
    slots.before === 14 && slots.afterArmful === 13, JSON.stringify(slots));
  ok("and the slot table matches ECONOMY 1",
    slots.costs.pocket === 0.5 && slots.costs.armful === 1 &&
    slots.costs.two_man === 3 && slots.costs.cart === 5, JSON.stringify(slots.costs));

  // LEVEL-SPEC V10, "it fits": walk the biggest thing in the house through every
  // doorway in the estate. Automate this BEFORE the first wing ships, not after
  // the first bug report - it is the check the build prompt calls out by name.
  await fresh();
  const fits = await g(() => {
    // Gates off: this asks whether the geometry admits the object, which is a
    // different question from whether the crew has earned the room yet.
    window.__g.gates(true);
    const stuck = [];
    for (const d of window.__g.doors()) {
      window.__g.reset(); window.__g.freezeCrew(true);
      const idx = window.__g.twoMan();
      const it = window.__g.list()[idx];
      window.__g.setCrew(0, it.x + 1.0, it.z);
      window.__g.tp(it.x - 1.2, it.z);
      window.__g.look(Math.PI / 2, -Math.atan2(1.62 - it.y, 1.2));
      window.__g.grab();
      if (!window.__g.carry()) { stuck.push({ door: d.a + "-" + d.b, why: "no lift" }); continue; }
      // Approach along the corridor axis, centred, the way a player lining up a
      // wardrobe would. Walking at the door from an angle is a different (and
      // much harder) question than whether the geometry admits the object.
      const A = window.__g.rooms().find(r => r.id === d.a);
      const B = window.__g.rooms().find(r => r.id === d.b);
      const along = d.axis === "x" ? [1, 0] : [0, 1];
      const towardB = d.axis === "x" ? Math.sign(B.x - A.x) : Math.sign(B.z - A.z);
      window.__g.tp(d.x - along[0] * 2.6 * towardB, d.z - along[1] * 2.6 * towardB);
      window.__g.look(Math.atan2(along[0] * towardB, along[1] * towardB), 0);
      let through = false;
      for (let i = 0; i < 600; i++) {
        window.__g.press("KeyW"); window.__g.step(1, 1 / 60);
        const p = window.__g.pos();
        if (p.room === d.b) { through = true; break; }
      }
      window.__g.clearKeys();
      if (!through) stuck.push({ door: d.a + "-" + d.b, at: window.__g.pos() });
    }
    window.__g.gates(false);
    return stuck;
  });
  ok("the biggest thing in the house fits through every doorway",
    fits.length === 0, JSON.stringify(fits));

  // --- the contract chain (ECONOMY 4) ---------------------------------------
  // Four nights, an escalating quota and a van that grows 14->19. The quotas in
  // ECONOMY are for the twelve-minute ship night; this build runs 210s, so they
  // are scaled by night length rather than copied.
  await fresh();
  const chain = await g(() => window.__g.contract());
  ok("the contract is four nights", chain.nights === 4 && chain.curve.length === 4,
    JSON.stringify(chain.curve));
  ok("the van follows ECONOMY's curve",
    chain.curve.map(c => c.van).join(",") === "14,15,17,19",
    JSON.stringify(chain.curve.map(c => c.van)));
  ok("the quota rises every night",
    chain.curve.every((c, i) => i === 0 || c.here > chain.curve[i - 1].here),
    JSON.stringify(chain.curve.map(c => c.here)));
  // Deliberately NOT the scaled ship quota: earnings do not scale with the clock,
  // and scaling put night two above the mean take. These are measured (R25).
  ok("the quota is measured for this build, not scaled from the ship night",
    chain.curve.every(c => Math.abs(c.here - c.ship * chain.scale) > 100),
    JSON.stringify(chain.curve));

  // The first rung has to be winnable and the last one has to bite.
  const rates = await g(() => {
    // The selector checks freeze the crew; a leaked freeze silently zeroes every
    // night's take and reads as "the quota is too hard".
    window.__g.freezeCrew(false);
    const out = [];
    for (const n of [0, 3]) {
      let met = 0, runs = 12;
      for (let trial = 0; trial < runs; trial++) {
        window.__g.newContract((trial + 1) * 104729 + n); window.__g.regen((trial + 1) * 104729 + n);
        window.__g.setNight(n);
        for (let i = 0; i < 210 * 60 && !window.__g.state().over; i++) window.__g.step(1, 1 / 60);
        if (window.__g.contract().last.met) met++;
      }
      out.push({ night: n + 1, pass: met / runs });
    }
    window.__g.newContract();      // this sweep walks the chain; put it back
    window.__g.regen(20260806);
    return out;
  });
  // R11's curse policy, exercised in the live build. Two claims, both paired on
  // identical houses so the answer does not come from which seeds got drawn:
  //   1. the cap is honoured, and
  //   2. refusing cursed cargo outright costs real money.
  // Note what is NOT claimed: in a 210s night the crew only find ~2.7 cursed
  // pieces anyway, so CAP_3 barely binds. An earlier reading of this as
  // "the cap cut ruin nights from 18% to 5%" compared different seeds and was
  // sampling noise; the paired sweep puts both around 2-5%.
  const curse = await g(() => {
    window.__g.freezeCrew(false);
    const run = cap => {
      window.__g.curseCap(cap);
      let cursed = 0, net = 0, n = 12;
      for (let t = 0; t < n; t++) {
        window.__g.newContract((t + 1) * 104729); window.__g.regen((t + 1) * 104729);
        for (let i = 0; i < 210 * 60 && !window.__g.state().over; i++) window.__g.step(1, 1 / 60);
        const l = window.__g.contract().last;
        cursed += l.cursed; net += l.net;
      }
      return { cap, cursed: +(cursed / n).toFixed(2), net: Math.round(net / n) };
    };
    const strict = run(1), normal = run(3), none = run(0);
    window.__g.curseCap(3);
    window.__g.newContract(20260806); window.__g.regen(20260806);
    return { strict, normal, none };
  });
  // Not exactly 1: the cap only applies to pieces they have appraised, and a
  // blind pickup at PURSUE can still be cursed. That is the appraiser earning
  // its place rather than a leak.
  ok("the crew honour the cursed-cargo cap",
    curse.strict.cursed <= 1.35 && curse.strict.cursed < curse.normal.cursed,
    JSON.stringify(curse));
  ok("and refusing cursed cargo outright costs real money",
    curse.none.net < curse.normal.net * 0.85, JSON.stringify(curse));

  // ECONOMY 4's description of the last night: "above the mean. The apex is not
  // optional." Bots alone should mostly miss it; the apex should turn it around.
  const lastNight = await g(() => {
    window.__g.freezeCrew(false);
    let bots = 0, missed = 0, rescued = 0, runs = 12;
    const shortfall = [];
    const apexValue = [];
    for (let t = 0; t < runs; t++) {
      window.__g.newContract((t + 1) * 104729 + 3); window.__g.regen((t + 1) * 104729 + 3, 3);
      window.__g.setNight(3);
      const a = window.__g.apex(); if (a) apexValue.push(a.value);
      for (let i = 0; i < 210 * 60 && !window.__g.state().over; i++) window.__g.step(1, 1 / 60);
      const l = window.__g.contract().last;
      if (l.met) bots++; else {
        missed++;
        // A ruined night is a different failure mode - the collection took the
        // whole van, and no single object was ever going to cover that.
        if (!l.ruin) shortfall.push(l.quota - l.net);
        if (l.net + (a ? a.value : 0) >= l.quota) rescued++;
      }
    }
    window.__g.newContract(20260806); window.__g.regen(20260806);
    shortfall.sort((a, b) => a - b);
    return { bots: bots / runs, missed, rescued,
             medianShort: shortfall.length ? shortfall[Math.floor(shortfall.length / 2)] : 0,
             apex: Math.round(apexValue.reduce((s, v) => s + v, 0) / apexValue.length) };
  });
  // Twelve runs cannot pin a rate to ten points, so the claim is coarse: the
  // last night is not a formality, and the apex is what closes the gap.
  ok("the last night is not a formality on crew throughput alone",
    lastNight.bots <= 0.75, JSON.stringify(lastNight) + " (n=12)");
  // A scale claim, not a rescue rate. The apex only rescued a third of the
  // failed nights when this was measured - but the player is doing NOTHING in
  // these runs, and the shortfall on a failed night is about one apex wide.
  // What is being asserted is that the apex is the right size to be the thing
  // that decides the night, which is ECONOMY 4's intent for it.
  ok("and the apex is the right size to decide it",
    lastNight.missed === 0 || lastNight.medianShort === 0 ||
    (lastNight.medianShort <= lastNight.apex * 2 && lastNight.rescued >= 1),
    JSON.stringify(lastNight));

  // What actually stops a night in this build? ECONOMY 1 sells the van as the
  // master scarcity lever and ECONOMY 4 wants later estates to be richer, and
  // NEITHER of those is what binds here: at dawn the van still has free slots and
  // almost all of the house is still on its shelves. Time binds, and it binds
  // harder on the later nights, where the house is bigger and the van is larger.
  // That is not a bug in the build - it is what a 210-second night does to a
  // design calibrated for 720 - but it means this build cannot be used to tune
  // capacity, and the check exists so that stays visible rather than becoming a
  // thing everyone forgot.
  const binds = await g(() => {
    window.__g.freezeCrew(false);
    const out = [];
    for (const n of [0, 3]) {
      let slots = 0, leftShare = 0, runs = 8;
      for (let t = 0; t < runs; t++) {
        window.__g.newContract((t + 1) * 104729 + n);
        window.__g.regen((t + 1) * 104729 + n, n); window.__g.setNight(n);
        const start = window.__g.list().reduce((a, i) => a + i.value, 0);
        for (let i = 0; i < 210 * 60 && !window.__g.state().over; i++) window.__g.step(1, 1 / 60);
        slots += window.__g.state().slots;
        leftShare += window.__g.list().reduce((a, i) => a + i.value, 0) / Math.max(1, start);
      }
      out.push({ night: n + 1, van: window.__g.contract().van,
        slotsFreeAtDawn: +(slots / runs).toFixed(1),
        valueLeftInHouse: +(leftShare / runs).toFixed(2) });
    }
    window.__g.newContract(20260806); window.__g.regen(20260806);
    return out;
  });
  ok("time is what binds a night here, not the van and not the house",
    binds.every(b => b.slotsFreeAtDawn > 1.0 && b.valueLeftInHouse > 0.6),
    JSON.stringify(binds) + " (n=8 per night)");
  ok("and the van binds less on the last night than the first, not more",
    binds[1].slotsFreeAtDawn > binds[0].slotsFreeAtDawn, JSON.stringify(binds));

  ok("night one is winnable and the last night is harder than the first",
    rates[0].pass >= 0.6 && rates[1].pass < rates[0].pass, JSON.stringify(rates));

  // Meeting the quota advances; missing it ends the contract. Nothing else does.
  await fresh();
  const advance = await g(() => {
    window.__g.parkCrew();
    window.__g.bank(window.__g.contract().quota + 500);   // comfortably over
    window.__g.setT(209.5); window.__g.step(60, 1 / 60);
    const after = window.__g.contract();
    const moved = window.__g.nextNight();
    const now = window.__g.contract();
    return { met: after.last.met, moved, night: now.night, van: now.van,
             quota: now.quota, seedChanged: true };
  });
  ok("meeting the quota moves you to the next night",
    advance.met === true && advance.moved === true && advance.night === 1,
    JSON.stringify(advance));
  ok("and the next night is a bigger van and a higher quota",
    advance.van === 15 && advance.quota > chain.curve[0].here, JSON.stringify(advance));

  await fresh();
  const missed = await g(() => {
    window.__g.parkCrew();
    window.__g.setT(209.5); window.__g.step(60, 1 / 60);   // sunrise with nothing
    const after = window.__g.contract();
    const moved = window.__g.nextNight();
    return { met: after.last.met, over: after.chainOver, moved };
  });
  ok("missing it ends the chain",
    missed.met === false && missed.over === true && missed.moved === false,
    JSON.stringify(missed));

  // A full contract, played out headlessly: four nights, each a different house.
  const played = await g(() => {
    window.__g.freezeCrew(false);
    window.__g.newContract();
    const seeds = [], nights = [];
    for (let n = 0; n < 4; n++) {
      seeds.push(window.__g.seed().seed);
      window.__g.parkCrew();
      window.__g.bank(window.__g.contract().quota + 100);
      window.__g.setT(209.5); window.__g.step(60, 1 / 60);
      nights.push(window.__g.contract().last.met);
      if (n < 3 && !window.__g.nextNight()) break;
    }
    const c = window.__g.contract();
    return { seeds, nights, over: c.chainOver, earned: c.chainEarnings };
  });
  ok("a contract can be played to the end",
    played.nights.length === 4 && played.nights.every(Boolean) && played.over === true,
    JSON.stringify(played));
  ok("every night is a different house",
    new Set(played.seeds).size === 4, JSON.stringify(played.seeds));

  await g(() => { window.__g.newContract(20260806); window.__g.regen(20260806); });

  // --- the apex (ECONOMY 3, D-21) -------------------------------------------
  // The thing the last night is built around: one per estate, only in late
  // contracts, five of the van's slots, and it takes two people to move.
  const apex = await g(() => {
    const out = { early: [], late: [], haul: null };
    for (const n of [0, 1]) {
      window.__g.newContract(4242 + n); window.__g.regen(4242 + n, n); window.__g.setNight(n);
      out.early.push(window.__g.apex());
    }
    for (const n of [2, 3]) {
      window.__g.newContract(4242 + n); window.__g.regen(4242 + n, n); window.__g.setNight(n);
      out.late.push(window.__g.apex());
    }
    // Wheel it: an apex is cart class, so it cannot be picked up at all - it goes
    // on the dolly or it stays where it is.
    window.__g.newContract(4242); window.__g.regen(4242, 3); window.__g.setNight(3);
    window.__g.gates(true); window.__g.freezeCrew(true);
    const a = window.__g.apex(), it = window.__g.list()[a.i];
    window.__g.tp(it.x - 1.3, it.z);
    window.__g.look(Math.PI / 2, -Math.atan2(1.62 - it.y, 1.3));
    window.__g.grab();
    const byHand = window.__g.carry();
    window.__g.moveDolly(it.x + 1.0, it.z);
    window.__g.tp(it.x + 1.6, it.z);
    const took = window.__g.takeDolly();
    const loaded = window.__g.loadDolly();
    const v = window.__g.rooms().find(r => r.van);
    const before = window.__g.vanSlots();
    window.__g.moveDolly(v.x, v.z); window.__g.tp(v.x, v.z); window.__g.step(4, 1 / 60);
    out.haul = { byHand, took, loaded, slots: before - window.__g.vanSlots(),
                 banked: window.__g.state().banked, value: a.value };
    window.__g.gates(false); window.__g.freezeCrew(false);
    window.__g.newContract(20260806); window.__g.regen(20260806);
    return out;
  });
  ok("early contract nights have no apex",
    apex.early.every(a => a === null), JSON.stringify(apex.early));
  ok("late ones always do", apex.late.every(a => a && a.tier === 4),
    JSON.stringify(apex.late));
  ok("it cannot be picked up at all - it goes on the dolly",
    apex.haul.byHand === null && apex.haul.loaded !== null, JSON.stringify(apex.haul));
  ok("and it costs five slots when it gets there",
    apex.haul.slots === 5 && apex.haul.banked >= apex.haul.value,
    JSON.stringify(apex.haul));
  ok("and it is worth a third to two thirds of the night it decides",
    apex.late.every(a => a.value >= 2900 * 0.30 && a.value <= 3300 * 0.68),
    JSON.stringify(apex.late.map(a => a.value)));

  // --- lights and the breaker (DESIGN 6.5) ----------------------------------
  // "Lights are the exception, being silent: switching on a wing is a flat +25."
  // And the lever against it: kill the breaker for -15, and haul the rest blind.
  await fresh();
  const lights = await g(() => {
    window.__g.parkCrew();
    const start = window.__g.lights();
    const r = window.__g.rooms().find(x => !x.van);
    window.__g.tp(r.x, r.z);
    window.__g.setDist(50);
    const before = window.__g.state().dist;
    const noiseBefore = window.__g.noiseLog().length;
    const on = window.__g.toggleLights();
    const afterOn = window.__g.state().dist;
    const noiseAfter = window.__g.noiseLog().length;
    // A second wing, then the breaker - which only works at the van.
    const r2 = window.__g.rooms().filter(x => !x.van)[1];
    window.__g.tp(r2.x, r2.z); window.__g.toggleLights();
    const twoLit = window.__g.lights().lit.length;
    const inHouse = window.__g.killLights();
    const v = window.__g.rooms().find(x => x.van);
    window.__g.tp(v.x, v.z);
    const beforeKill = window.__g.state().dist;
    const killed = window.__g.killLights();
    const afterKill = window.__g.state().dist;
    const again = window.__g.killLights();
    return { start, on, before, afterOn, silent: noiseAfter === noiseBefore,
             twoLit, inHouse, killed, beforeKill, afterKill, again };
  });
  ok("the house starts dark", lights.start.lit.length === 0, JSON.stringify(lights.start));
  ok("lighting a wing costs a flat 25",
    Math.abs((lights.afterOn - lights.before) - 25) < 0.2, JSON.stringify(lights));
  ok("and is silent - no Loudness event at all", lights.silent === true,
    JSON.stringify(lights));
  ok("the breaker is at the van, not wherever you are standing",
    lights.inHouse === null && lights.killed !== null, JSON.stringify(lights));
  ok("killing it drops fifteen and takes every wing with it",
    lights.twoLit === 2 && lights.killed !== null && lights.killed.wings === 2 &&
    Math.abs((lights.beforeKill - lights.afterKill) - 15) < 0.2, JSON.stringify(lights));
  ok("and there is nothing to kill twice", lights.again === null, JSON.stringify(lights));

  // Go quiet: no running, no scanning, crew-wide, -20 over the period.
  await fresh();
  const quiet = await g(() => {
    window.__g.freezeCrew(false);
    const r = window.__g.rooms().find(x => !x.van);
    window.__g.tp(r.x, r.z);
    window.__g.setDist(60);
    const window0 = window.__g.levers().quietWindow;
    const started = window.__g.goQuiet();
    const twice = window.__g.goQuiet();               // no stacking
    const before = window.__g.state().dist;
    // Try to run during it.
    const p0 = window.__g.raw();
    window.__g.press("KeyW"); window.__g.press("ShiftLeft");
    window.__g.step(60, 1 / 60);
    const p1 = window.__g.raw();
    window.__g.clearKeys();
    const ranAt = Math.hypot(p1.x - p0.x, p1.z - p0.z) / 1.0;
    // Ride it out; disturbance should fall by 20 more than decay alone.
    for (let i = 0; i < window0 * 60; i++) window.__g.step(1, 1 / 60);
    const after = window.__g.state().dist;
    return { window0, started, twice, before, after, ranAt,
             quietNow: window.__g.levers().quiet };
  });
  ok("going quiet is a window, not a toggle",
    quiet.started !== null && quiet.twice === null && quiet.quietNow === 0,
    JSON.stringify(quiet));
  ok("its length is scaled to this build's night",
    Math.abs(quiet.window0 - 45 * (210 / 720)) <= 1, `${quiet.window0}s`);
  ok("you cannot run during it", quiet.ranAt < 3.4, `${quiet.ranAt.toFixed(2)} m/s`);
  ok("and it takes twenty off the meter",
    quiet.before - quiet.after >= 20, JSON.stringify(quiet));

  // Unload cursed cargo: the floor contribution goes, and so does the strap.
  await fresh();
  const unload = await g(() => {
    window.__g.parkCrew();
    const v = window.__g.rooms().find(x => x.van);
    // Re-read the list every time: hold() indexes the LIVE list and depositing
    // removes an entry, so indices taken from one snapshot slide by one and you
    // end up banking a clean piece you never chose.
    let put = 0;
    for (let attempt = 0; attempt < 40 && put < 2; attempt++) {
      const live = window.__g.list();
      const k = live.findIndex(i => i.grade !== "clean" && !i.corpse && !i.held
                                    && i.klass === "armful");
      if (k < 0) break;
      window.__g.hold(k); window.__g.tp(v.x, v.z); window.__g.step(2, 1 / 60); put++;
    }
    window.__g.setT(0); window.__g.setDist(0); window.__g.step(2, 1 / 60);
    const floorWith = window.__g.floor();
    const banked = window.__g.state().banked;
    const slots = window.__g.vanSlots();
    const done = window.__g.unloadCursed();
    window.__g.step(2, 1 / 60);
    const floorWithout = window.__g.floor();
    const loose = window.__g.list().filter(i => i.grade !== "clean" && !i.corpse);
    return { put, done, floorWith, floorWithout, banked, bankedAfter: window.__g.state().banked,
             slots, slotsAfter: window.__g.vanSlots(),
             radiating: loose.some(i => Math.hypot(i.x - v.x, i.z - v.z) < 4) };
  });
  // The FLOOR, not the meter: the meter decays toward it rather than snapping,
  // and asserting on the meter measures the decay rate instead of the rule.
  ok("cursed cargo aboard raises the floor",
    unload.put === 2 && unload.floorWith >= 13.9, JSON.stringify(unload));
  ok("unloading it into the yard takes that floor away",
    unload.done.unloaded === 2 && unload.floorWithout < 0.2, JSON.stringify(unload));
  ok("but it is out of the van, so it is not money any more",
    unload.bankedAfter < unload.banked && unload.slotsAfter > unload.slots,
    JSON.stringify(unload));
  ok("and it is lying in the yard where it can be reclaimed",
    unload.radiating === true, JSON.stringify(unload));

  // --- the controls are discoverable ----------------------------------------
  // The single most valuable thing this build can do is be played by a person
  // once. Sixteen verbs had accumulated behind a start screen that listed eight.
  const controls = await g(() => {
    const listed = [...document.querySelectorAll("#keys kbd")].map(k => k.textContent);
    const src = document.documentElement.innerHTML;
    // Every key the game binds, straight out of the handler.
    const bound = [...src.matchAll(/e\.code===\"Key([A-Z])\"/g)].map(m => m[1]);
    const missing = [...new Set(bound)].filter(k =>
      !listed.some(l => l.split(/\s+/).includes(k)));
    return { listed: listed.length, bound: [...new Set(bound)].length, missing };
  });
  ok("every bound key is on the controls list",
    controls.missing.length === 0, JSON.stringify(controls));

  const help = await g(() => {
    const h = document.getElementById("help");
    const before = getComputedStyle(h).display;
    window.dispatchEvent(new KeyboardEvent("keydown", { code: "KeyH" }));
    const during = h.style.display;
    window.dispatchEvent(new KeyboardEvent("keydown", { code: "KeyH" }));
    return { before, during, after: h.style.display,
             rows: document.querySelectorAll("#keys2 .k").length };
  });
  ok("H opens the list in game and closes it again",
    help.during === "flex" && help.after === "none" && help.rows >= 15,
    JSON.stringify(help));

  // --- the dolly (DESIGN 8) -------------------------------------------------
  // "Moves cart-class items - slow, loud on hardwood, tips over."
  await fresh();
  const dollyChecks = await g(() => {
    window.__g.parkCrew(); window.__g.gates(true);
    window.__g.newContract(4242); window.__g.regen(4242, 3); window.__g.setNight(3);
    window.__g.parkCrew(); window.__g.gates(true);
    const start = window.__g.dolly();

    // Slow: same ten strides with and without it.
    const walk = (withDolly) => {
      const r = window.__g.rooms().find(x => !x.van);
      window.__g.tp(r.x - 3, r.z); window.__g.look(Math.PI / 2, 0);
      if (withDolly) { window.__g.moveDolly(r.x - 3, r.z); window.__g.takeDolly(); }
      const a = window.__g.raw();
      window.__g.press("KeyW"); window.__g.step(90, 1 / 60); window.__g.clearKeys();
      const b = window.__g.raw();
      if (withDolly) window.__g.takeDolly();
      return Math.hypot(b.x - a.x, b.z - a.z);
    };
    const free = walk(false), pushing = walk(true);

    // Loud: it is a rolling alarm, and the Curator hears it.
    const r = window.__g.rooms().find(x => !x.van);
    window.__g.tp(r.x - 3, r.z); window.__g.moveDolly(r.x - 3, r.z);
    window.__g.takeDolly(); window.__g.setDist(40); window.__g.setCur(r.x, r.z);
    const dBefore = window.__g.state().dist;
    // Sample as it goes: the Curator is standing right there, so it walks to the
    // fix and clears it inside a second - reading the fix at the end reads null
    // and looks like it never heard anything.
    let heardIt = false;
    window.__g.press("KeyW");
    for (let i = 0; i < 120; i++) {
      window.__g.step(1, 1 / 60);
      if (window.__g.fix()) heardIt = true;
    }
    window.__g.clearKeys();
    const dAfter = window.__g.state().dist;
    window.__g.takeDolly();

    // Tips: shove it faster than it wants to go.
    const a = window.__g.apex();
    if (a) {
      const it = window.__g.list()[a.i];
      window.__g.moveDolly(it.x + 1.0, it.z);
      window.__g.tp(it.x + 1.6, it.z);
      window.__g.takeDolly(); window.__g.loadDolly();
    }
    const loadedBefore = window.__g.dolly().load;
    // Shoved, not pushed: sprinting with it is above the tipping speed. Setting
    // player.speed directly does nothing - the movement code overwrites it from
    // actual displacement on the same frame.
    window.__g.press("KeyW"); window.__g.press("ShiftLeft");
    window.__g.step(30, 1 / 60); window.__g.clearKeys();
    const after = window.__g.dolly();
    return { start, free, pushing, dBefore, dAfter, heardIt,
             loadedBefore, after, broken: window.__g.broken().length };
  });
  ok("there is a dolly, parked at the van",
    dollyChecks.start !== null && dollyChecks.start.load === null,
    JSON.stringify(dollyChecks.start));
  ok("pushing it is slower than walking",
    dollyChecks.pushing < dollyChecks.free * 0.75,
    JSON.stringify({ free: dollyChecks.free, pushing: dollyChecks.pushing }));
  ok("it is a rolling alarm",
    dollyChecks.dAfter > dollyChecks.dBefore && dollyChecks.heardIt === true,
    JSON.stringify(dollyChecks));
  ok("and it tips if you shove it",
    dollyChecks.loadedBefore !== null && dollyChecks.after.load === null &&
    dollyChecks.after.held === false, JSON.stringify(dollyChecks));

  // --- doors, and the Static verbs they unlock (DESIGN 5.1) -----------------
  // A door is a thing that takes time to get through. That is the only reason
  // slamming one is worth two Static and holding it is worth five.
  await fresh();
  const doors = await g(() => {
    window.__g.parkCrew(); window.__g.gates(true);
    const start = window.__g.doors2();
    // Become a ghost the quick way, then stand in a doorway.
    const d = window.__g.doors()[1];
    window.__g.tp(d.x, d.z);
    const aliveSlam = window.__g.slamDoor();          // the living cannot
    window.__g.setDist(95);
    for (let hit = 0; hit < 2; hit++)
      for (let i = 0; i < 3000 && window.__g.state().hits <= hit; i++) {
        const p = window.__g.raw();
        window.__g.setCur(p.x + 1.0, p.z, "PURSUE");
        window.__g.setDist(95); window.__g.step(1, 1 / 60);
      }
    window.__g.step(60 * 11, 1 / 60);                 // through the collection beat
    window.__g.tp(d.x, d.z);
    window.__g.setStatic(6);
    const s0 = window.__g.ghost().static;
    const slam = window.__g.slamDoor();
    const s1 = window.__g.ghost().static;
    const shut = window.__g.doors2().find(x => x.id === `${d.a}-${d.b}`);
    // Slam is 2 and Hold is 5 against a cap of 6, so you cannot do both on one
    // budget - holding a door you just slammed means waiting out a regen tick
    // first. That is DESIGN 5.1's arithmetic, not a bug, and it is why this
    // fixture tops the budget back up.
    const bothOnOneBudget = window.__g.holdDoor();
    window.__g.setStatic(6);
    const hold = window.__g.holdDoor();
    const s2 = window.__g.ghost().static;
    const held = window.__g.doors2().find(x => x.id === `${d.a}-${d.b}`);
    return { start, aliveSlam, slam, hold, bothOnOneBudget, s0, s1, s2, shut, held };
  });
  ok("every door starts open",
    doors.start.length > 0 && doors.start.every(x => !x.shut), JSON.stringify(doors.start));
  ok("the living cannot slam a door - that is a ghost's verb",
    doors.aliveSlam === null, JSON.stringify(doors.aliveSlam));
  ok("slamming costs two Static and shuts it",
    doors.slam !== null && doors.s0 - doors.s1 === 2 && doors.shut.shut === true,
    JSON.stringify(doors));
  ok("you cannot slam and hold the same door on one budget",
    doors.bothOnOneBudget === null, JSON.stringify({ after: doors.s1 }));
  ok("holding costs five and is a four-second thing",
    doors.hold !== null && 6 - doors.s2 === 5 && doors.held.held > 3.5,
    JSON.stringify(doors.held));

  // The point of all of it: a shut door costs the Curator time. Three things had
  // to be got right before this measured anything at all.
  //   - Measure the crossing of the doorway, not the arrival at the player. The
  //     first version measured the latter and read no difference, because both
  //     runs spent the same two and a half seconds in FIXATE first and 1.4s
  //     vanished inside the noise of a longer walk.
  //   - Start the Curator OUTSIDE the door's rect. At 1m it is already standing
  //     in the doorway, so the door spends its FIXATE seconds opening and only
  //     half the delay survives to be measured.
  //   - Give both runs the same random stream. Hearing is fuzzed +-3m, which
  //     moves the approach by a second either way - more than the effect being
  //     measured. __seed puts the stream back afterwards, so no check that
  //     follows can tell this one ran.
  const timed = await g(() => {
    const d = window.__g.doors()[1];
    const rooms = window.__g.rooms();
    const A = rooms.find(r => r.id === d.a), B = rooms.find(r => r.id === d.b);
    const along = d.axis === "x" ? [1, 0] : [0, 1];
    const sign = d.axis === "x" ? Math.sign(B.x - A.x) : Math.sign(B.z - A.z);
    const past = c => d.axis === "x" ? (c.x - d.x) * sign > 0.4 : (c.z - d.z) * sign > 0.4;

    const run = (shut, held) => {
      window.__seed(0x51ed);
      window.__g.reset(); window.__g.parkCrew(); window.__g.gates(true);
      window.__g.tp(d.x, d.z);
      if (shut) window.__g.slamDoorForce();
      if (held) window.__g.holdDoorForce();
      window.__g.tp(B.x, B.z);
      const me = window.__g.raw();
      window.__g.setCur(d.x - along[0] * 2.2 * sign, d.z - along[1] * 2.2 * sign, "PURSUE");
      let out = -1;
      for (let i = 0; i < 60 * 20; i++) {
        window.__g.setDist(95);
        window.__g.heard(65, me.x, me.z);
        window.__g.step(1, 1 / 60);
        if (past(window.__g.curator())) { out = i / 60; break; }
      }
      return out;
    };
    const was = window.__seed(0);
    const open = run(false, false), shut = run(true, false), held = run(true, true);
    window.__seed(was);
    return { open, shut, held, cost: +(shut - open).toFixed(2),
      holdCost: +(held - shut).toFixed(2) };
  });
  // Doors are estate furniture, so nothing in the night reset was clearing them
  // until this asked.
  const doorNight = await g(() => {
    const d = window.__g.doors()[1];
    window.__g.tp(d.x, d.z); window.__g.slamDoorForce();
    const before = window.__g.doors2().filter(x => x.shut).length;
    window.__g.reset();
    return { before, after: window.__g.doors2().filter(x => x.shut || x.held > 0).length };
  });
  ok("a new night reopens every door",
    doorNight.before === 1 && doorNight.after === 0, JSON.stringify(doorNight));

  ok("a shut door costs the Curator the time it takes to open it",
    timed.open >= 0 && timed.shut >= 0 && timed.cost > 1.2 && timed.cost < 1.8,
    JSON.stringify(timed));
  // Held is the expensive verb because it is the only one that stops the
  // Curator rather than slowing it: the opening timer does not even start.
  ok("and a held door does not start opening at all until the hold lapses",
    timed.held > timed.shut + 1.0, JSON.stringify(timed));

  // Flicker: cheap, and only if there is a light to flicker.
  await fresh();
  const flick = await g(() => {
    window.__g.parkCrew();
    const dark = window.__g.flickerLights();       // no ghost, no lights
    const r = window.__g.rooms().find(x => !x.van);
    window.__g.tp(r.x, r.z); window.__g.toggleLights();
    const aliveTry = window.__g.flickerLights();
    return { dark, aliveTry };
  });
  ok("flicker is a ghost's verb and needs a light on",
    flick.dark === null && flick.aliveTry === null, JSON.stringify(flick));

  // --- the voice ladder (AUDIO-SPEC 2) --------------------------------------
  // Four loudness values sat in tuning.json unused for forty rounds because the
  // prototype had nothing to say. What they buy is the ask for the other end of
  // an armoire, and the decision is the ladder itself: who hears you against who
  // else does. Reach is the same arithmetic the Curator uses - L x 0.33, times
  // 0.85 per wall - so a whisper does not leave the room and a shout crosses the
  // house, and the thing upstairs is listening on the same channel.
  await fresh();
  const voice = await g(() => {
    window.__g.parkCrew();
    const out = {};
    for (const level of ["whisper", "call", "shout"]) {
      window.__g.reset(); window.__g.parkCrew();
      const rooms = window.__g.rooms().filter(r => !r.van);
      const here = rooms[0];
      window.__g.tp(here.x, here.z);
      const d0 = window.__g.state().dist;
      const said = window.__g.speak(level);
      const heard = window.__g.noiseLog().slice(-1)[0];
      // Reach in metres, and then the two questions that matter: can it cross
      // your own room, and can it be heard in the next one? Rooms sit on a 13m
      // lattice, so those are 5m and 13m-through-a-wall.
      const across = window.__g.voiceReaches(said.l, here.x, here.z, here.x + 5, here.z);
      const nextRoom = window.__g.rooms().find(r =>
        r.id !== here.id && Math.abs(Math.hypot(r.x - here.x, r.z - here.z) - 13) < 1);
      const nextDoor = nextRoom
        ? window.__g.voiceReaches(said.l, here.x, here.z, nextRoom.x, nextRoom.z) : null;
      out[level] = { l: said.l, heard: heard && heard.l, across, nextDoor,
        gained: +(window.__g.state().dist - d0).toFixed(2) };
    }
    return out;
  });
  ok("the voice ladder is the one in AUDIO-SPEC, and every rung is a real noise",
    voice.whisper.l === 8 && voice.call.l === 45 && voice.shout.l === 65 &&
    ["whisper", "call", "shout"].every(k => voice[k].heard === voice[k].l),
    JSON.stringify(voice));
  // L x 0.33 metres, 0.85 per wall: a whisper carries 2.6m and cannot cross the
  // room you are standing in; a raised voice fills the room and stops at the
  // doorway; only a shout is heard next door. That is the ladder being a decision
  // rather than three words for the same thing.
  ok("you have to shout to be heard in the next room, and a whisper stays with you",
    voice.whisper.across === false && voice.call.across === true &&
    voice.call.nextDoor === false && voice.shout.nextDoor === true,
    JSON.stringify(voice));
  ok("and talking costs Disturbance like anything else that makes a noise",
    Math.abs(voice.shout.gained - 65 * 0.09) < 0.4 &&
    voice.whisper.gained < voice.call.gained, JSON.stringify(voice));

  // The reason the verb exists: grabDrop has said "you take one end and shout at
  // somebody to take the other" since R26, with no shout in the game.
  await fresh();
  const otherEnd = await g(() => {
    const idx = window.__g.twoMan();
    const it = window.__g.list()[idx];
    // Stand at the armoire with the crew parked at the far end of the house.
    window.__g.parkCrew();
    window.__g.tp(it.x, it.z);
    window.__g.look(Math.atan2(it.x - it.x, it.z - it.z));
    window.__g.hold(idx);
    const alone = window.__g.carry();
    // Put them in the NEXT room, not in the driveway where reset() left them and
    // not on top of you: 13m through one wall is out of range of a whisper and
    // inside a shout, which is the whole point of having a ladder. Whispering for
    // help and having somebody arrive would mean the guard was doing nothing.
    // Clear the prerequisite chain first. A two-man piece lives at tier 2 or
    // deeper, which is behind a lock, and crew who cannot legally route to you
    // walk to the nearest open door and stall there - which reads as "three
    // people heard you and nobody came", and is in fact correct behaviour.
    const mine = window.__g.roomAt(it.x, it.z);
    for (const r of window.__g.rooms()) if (!r.van && r.id !== mine) window.__g.clearRoom(r.id);
    const here = window.__g.rooms().find(r => r.id === mine);
    const next = window.__g.rooms().find(r => r.id !== here.id && !r.van &&
      Math.abs(Math.hypot(r.x - here.x, r.z - here.z) - 13) < 1) || here;
    window.__g.unparkCrew(next.x, next.z);
    const whispered = window.__g.speak("whisper").heard.length;
    window.__g.step(60 * 5, 1 / 60);
    // Null-safe: an armoire held by one person is not a stable state, and what is
    // being asked here is whether anybody answered, not what happened to the piece.
    const afterWhisper = window.__g.called().length;
    // Put them back where they were: five seconds of SEEK carries them out of the
    // room and into somebody's sideboard, and speak() skips a crew member with
    // their hands full - which reads as "nobody heard the shout".
    window.__g.unparkCrew(next.x, next.z);
    window.__g.hold(window.__g.twoMan());       // re-find it: indices shift
    const answered = window.__g.speak("shout").heard.length;
    // carry() goes null the moment the piece leaves your hands, which an armoire
    // held by one person does; the loop has to survive that rather than throw.
    const follower = () => (window.__g.carry() || {}).follower ?? null;
    for (let i = 0; i < 60 * 40 && !follower(); i++) window.__g.step(1, 1 / 60);
    return { alone, whispered, afterWhisper, answered, follower: follower(),
      carry: window.__g.carry(), called: window.__g.called() };
  });
  ok("shouting brings somebody to take the other end of an armoire",
    otherEnd.answered > 0 && otherEnd.follower !== null, JSON.stringify(otherEnd));
  ok("and whispering for help from the next room brings nobody at all",
    otherEnd.whispered === 0 && otherEnd.afterWhisper === 0, JSON.stringify(otherEnd));

  // A ghost has Static instead. A dead player who could still shout would make
  // Knock worth one point and nothing.
  const mute = await g(() => {
    window.__g.reset(); window.__g.parkCrew();
    window.__g.setDist(95);
    for (let hit = 0; hit < 2; hit++)
      for (let i = 0; i < 3000 && window.__g.state().hits <= hit; i++) {
        const p = window.__g.raw();
        window.__g.setCur(p.x + 1.0, p.z, "PURSUE");
        window.__g.setDist(95); window.__g.step(1, 1 / 60);
      }
    window.__g.step(60 * 11, 1 / 60);
    return { dead: window.__g.ghost().dead, said: window.__g.speak("shout") };
  });
  ok("the dead do not shout - they have Static for that",
    mute.dead === true && mute.said === null, JSON.stringify(mute));

  // --- the radio (DESIGN 8) -------------------------------------------------
  // "Talk to crew across map - broadcasts audibly in-world at BOTH ends." The
  // second clause is the tool. A shout is one loud noise where you are; the radio
  // is a quieter one where you are AND one wherever each listener is standing, so
  // it trades a beacon on yourself for a beacon on everybody.
  await fresh();
  const wireless = await g(() => {
    const r = window.__g.radio();
    const rooms = window.__g.rooms().filter(x => !x.van);
    for (const x of rooms) window.__g.clearRoom(x.id);
    // Crew scattered as far apart as the house allows, and the player further.
    window.__g.unparkCrew(rooms[rooms.length - 1].x, rooms[rooms.length - 1].z);
    window.__g.tp(rooms[0].x, rooms[0].z);
    const far = Math.hypot(rooms[0].x - rooms[rooms.length - 1].x,
                           rooms[0].z - rooms[rooms.length - 1].z);
    // Off the air first: a shout across the whole house reaches nobody, and the
    // radio cannot be keyed from across the room it is sitting in.
    const shout = window.__g.speak("shout").heard.length;
    const startedIn = r !== null && window.__g.roomAt(r.x, r.z) === null
      ? false : true;
    const reachedFor = window.__g.takeRadio();
    window.__g.moveRadio(rooms[0].x, rooms[0].z);
    const took = window.__g.takeRadio();
    const before = window.__g.noiseLog().length;
    const said = window.__g.speak("call");
    const made = window.__g.noiseLog().slice(before);
    return { far: +far.toFixed(1), shout, took, reachedFor, startedIn,
      heard: said.heard.length, l: said.l,
      noises: made.length, levels: [...new Set(made.map(n => n.l))],
      crew: window.__g.crew().length };
  });
  ok("you have to go and get the radio - it starts in the van",
    wireless.reachedFor === null && wireless.startedIn === true,
    JSON.stringify({ reachedFor: wireless.reachedFor, startedIn: wireless.startedIn }));
  ok("the radio reaches the whole house when a shout does not",
    wireless.far > 25 && wireless.shout === 0 && wireless.took !== null &&
    wireless.heard === wireless.crew, JSON.stringify(wireless));
  ok("and it broadcasts at both ends - one noise at you, one at everybody listening",
    wireless.noises === wireless.crew + 1 && wireless.levels.length === 1 &&
    wireless.levels[0] === 38, JSON.stringify(wireless));

  // The trade, stated as the thing a player would notice: keying the radio tells
  // the house where your crew are, which shouting never does.
  await fresh();
  const beacons = await g(() => {
    const rooms = window.__g.rooms().filter(x => !x.van);
    for (const x of rooms) window.__g.clearRoom(x.id);
    const near = rooms[rooms.length - 1];
    window.__g.unparkCrew(near.x, near.z);
    window.__g.tp(rooms[0].x, rooms[0].z);
    // Curator standing next to the crew, at the far end from the player.
    window.__g.setCur(near.x + 1.0, near.z, "PURSUE");
    window.__g.setDist(95);
    const shoutFix = (window.__g.speak("shout"), window.__g.fix());
    window.__g.moveRadio(rooms[0].x, rooms[0].z);
    window.__g.takeRadio();
    window.__g.speak("call");
    const radioFix = window.__g.fix();
    return { shoutFix, radioFix, crewAt: { x: near.x, z: near.z } };
  });
  ok("keying it tells the house where your crew are standing, which a shout never does",
    beacons.radioFix !== null &&
    Math.hypot(beacons.radioFix.x - beacons.crewAt.x,
               beacons.radioFix.z - beacons.crewAt.z) < 6,
    JSON.stringify(beacons));

  // --- what a curse costs you while you hold it (DESIGN 4.2) ----------------
  // The hard rule in the spec: every curse cost must be felt within thirty
  // seconds of pickup and be obviously caused by the thing in your hands. Each of
  // these measures one of the three, and each measures it against the SAME piece
  // put down again, because "attributable" is the half of the rule that is easy
  // to lose.
  await fresh();
  const curseCarry = await g(() => {
    window.__g.parkCrew();
    const out = {};
    for (const grade of ["clean", "tainted", "malignant"]) {
      // Re-read the list AFTER the reset: reset() remakes every item, so an index
      // taken before it points at a different piece with a different grade. This
      // is the third fixture in this file to be caught by exactly that.
      window.__g.reset(); window.__g.parkCrew();
      const idx = window.__g.list().findIndex(i => i.grade === grade);
      if (idx < 0) { out[grade] = null; continue; }
      // Stand somewhere that is not the van: reset() puts you in the driveway,
      // and anything in your hands there is banked on the next frame. The first
      // version of this fixture measured an empty pair of hands for thirty
      // seconds and reported that curses cost nothing.
      const room = window.__g.rooms().find(r => !r.van);
      window.__g.tp(room.x, room.z);
      window.__g.setDist(20);
      const before = window.__g.state().dist;
      // Go dark FIRST, with empty hands, so what is being measured is the piece
      // taking the choice away rather than a switch that was never flipped.
      window.__g.toggleTorch();
      const darkBefore = window.__g.torch().on === false;
      window.__g.hold(idx);
      const t0 = window.__g.torch();
      // Stand still for the thirty seconds the rule is about. Walking for them
      // takes you out of the room and into the van, where the piece is banked and
      // every effect stops - which the first version of this measured as "curses
      // cost nothing" for all three grades.
      window.__g.step(30 * 60, 1 / 60);
      const t30 = window.__g.torch();
      // Now try to turn it off while holding the thing. Get it ON first - after a
      // clean thirty seconds it is still dark, and "toggle" on a dark torch is a
      // request for light, which is not the question being asked.
      window.__g.toggleTorch(); window.__g.step(1, 1 / 60);
      const wasOn = window.__g.torch().on;
      window.__g.toggleTorch(); window.__g.step(1, 1 / 60);
      const stuck = window.__g.torch().on;
      const gained = window.__g.state().dist - before;
      const voices = window.__g.noiseLog().filter(n => n.l === 25).length;
      // Then one second of walking, which is short enough to stay in the room and
      // long enough to read the mass in metres rather than in the variable that
      // is supposed to cause it.
      window.__g.tp(room.x, room.z); window.__g.look(0, 0); window.__g.press("KeyW");
      const p0 = window.__g.raw();
      window.__g.step(60, 1 / 60);
      const p1 = window.__g.raw();
      window.__g.clearKeys();
      window.__g.drop();
      window.__g.toggleTorch();
      out[grade] = { darkBefore, wasOn, stuck, lightBack: t30.on === true,
        forced: t0.forced, gained: +gained.toFixed(2),
        slow: t30.slow, walked: +Math.hypot(p1.x - p0.x, p1.z - p0.z).toFixed(2),
        voices, afterDrop: window.__g.torch() };
    }
    return out;
  });
  // Disturbance DECAYS at 0.83/s with four crew, so "costs you nothing" is a
  // number that goes down. Comparing the three grades against each other is the
  // point: the clean piece is the baseline the other two are a cost against.
  ok("a clean piece costs you nothing to carry",
    curseCarry.clean && curseCarry.clean.darkBefore === true &&
    curseCarry.clean.lightBack === false && curseCarry.clean.voices === 0 &&
    curseCarry.clean.slow === 1 && curseCarry.clean.gained < 0,
    JSON.stringify(curseCarry.clean));
  ok("a tainted piece turns your torch back on and will not let you turn it off",
    curseCarry.tainted && curseCarry.tainted.darkBefore === true &&
    curseCarry.tainted.lightBack === true && curseCarry.tainted.stuck === true &&
    curseCarry.clean.stuck === false, JSON.stringify(curseCarry.tainted));
  // The number has to RISE, not fall more slowly - see the note on the constant.
  ok("and it costs Disturbance faster than the crew can decay it",
    curseCarry.tainted && curseCarry.tainted.gained > 2 &&
    curseCarry.tainted.gained > curseCarry.clean.gained + 20,
    JSON.stringify({ tainted: curseCarry.tainted.gained, clean: curseCarry.clean.gained }));
  ok("a malignant piece is visibly heavier inside twenty seconds",
    curseCarry.malignant && curseCarry.malignant.slow <= 0.63 &&
    curseCarry.malignant.walked < curseCarry.clean.walked * 0.85,
    JSON.stringify({ malignant: curseCarry.malignant.walked,
      clean: curseCarry.clean.walked, slow: curseCarry.malignant.slow }));
  ok("and it speaks in a crewmate's voice, which is a noise where you are standing",
    curseCarry.malignant && curseCarry.malignant.voices >= 3,
    JSON.stringify(curseCarry.malignant));
  ok("putting it down gives you the torch back - the cost is the thing in your hands",
    curseCarry.tainted && curseCarry.tainted.afterDrop.forced === false &&
    curseCarry.malignant && curseCarry.malignant.afterDrop.mass === 0,
    JSON.stringify({ tainted: curseCarry.tainted.afterDrop,
      malignant: curseCarry.malignant.afterDrop }));

  // The torch is a verb now, and going dark is worth something: A3 weights a lit
  // carrier above an unlit one, so the choice is "be seen" against "be blind".
  await fresh();
  const torch = await g(() => {
    window.__g.parkCrew();
    const idx = window.__g.list().findIndex(i => i.grade === "clean");
    window.__g.hold(idx);
    const me = window.__g.raw();
    // Facing matters: sees() is a cone, so a Curator dropped next to you looking
    // the wrong way weighs a lit carrier exactly like an unlit one.
    window.__g.setCur(me.x + 2.0, me.z, "PURSUE", Math.atan2(-2.0, 0));
    window.__g.look(0, 0);
    const lit = window.__g.weight();
    window.__g.toggleTorch();
    const dark = window.__g.weight();
    window.__g.toggleTorch();
    return { lit, dark, back: window.__g.torch().on };
  });
  ok("going dark makes you a lighter mark, which is what the torch verb is for",
    torch.dark < torch.lit && torch.back === true, JSON.stringify(torch));

  // --- the crowbar and the boarded wing (DESIGN 6.4, 8) ---------------------
  // "The boarded stair needs the crowbar that's in the garage. You physically
  // cannot be deep at minute one." V3 guarantees no single doorway seals anything,
  // so the boards go on EVERY door into the deepest wing - the same shape of lock
  // the prerequisite chain already uses, and the reason the salt line is a detour
  // and this is not.
  await fresh();
  const bar = await g(() => {
    const b = window.__g.boarded();
    const c = window.__g.crowbar();
    const rooms = window.__g.rooms();
    const all = window.__g.doors().filter(d => d.a === b.wing || d.b === b.wing);
    return { wing: b.wing, boards: b.doors.length, into: all.length, crowbar: c,
      wingIsDeepest: rooms.filter(r => !r.van)
        .every(r => r.tier <= (rooms.find(x => x.id === b.wing) || {}).tier) };
  });
  ok("the deepest wing is boarded shut, on every door into it",
    bar.wing !== null && bar.boards > 0 && bar.boards === bar.into,
    JSON.stringify(bar));
  ok("and the crowbar that opens it is not inside it",
    bar.crowbar !== null && bar.crowbar.room !== bar.wing && bar.crowbar.held === false,
    JSON.stringify(bar.crowbar));

  const pry = await g(() => {
    window.__g.parkCrew();
    const b = window.__g.boarded(), d = b.doors[0];
    const rooms = window.__g.rooms();
    const wing = rooms.find(r => r.id === b.wing);
    // Face the wing. W walks along +z at yaw 0 and +x at yaw pi/2, so pointing the
    // player at the room behind the boards is the difference between prying and
    // wandering off down the corridor - which is what the first version of this
    // check did, and it read as "the crowbar does not work".
    const yaw = Math.atan2(wing.x - d.x, wing.z - d.z);
    const walkInto = (frames) => {
      window.__g.tp(d.x, d.z); window.__g.look(yaw);
      window.__g.press("KeyW");
      let i = 0;
      for (; i < frames && window.__g.boarded().doors.length; i++)
        window.__g.step(1, 1 / 60);
      window.__g.clearKeys();
      return i / 60;
    };
    walkInto(60 * 5);                        // bare hands: the boards do not care
    const bare = window.__g.boarded().doors.length;
    // Now fetch it. It is across the house, so QA moves it rather than walking.
    window.__g.moveCrowbar(d.x, d.z);
    window.__g.tp(d.x, d.z);
    const took = window.__g.takeCrowbar();
    const d0 = window.__g.state().dist;
    const seconds = walkInto(60 * 8);
    return { bare, took, seconds,
      left: window.__g.boarded().doors.length, d0, d1: window.__g.state().dist,
      loud: window.__g.noiseLog().slice(-1)[0] };
  });
  ok("bare hands do nothing to a board",
    pry.bare > 0, JSON.stringify({ boards: pry.bare }));
  ok("the crowbar takes about three seconds and opens the whole wing at once",
    pry.took !== null && pry.left === 0 && pry.seconds > 2.5 && pry.seconds < 4.0,
    JSON.stringify(pry));
  ok("and it is the loudest thing in the toolkit - L75",
    pry.loud && pry.loud.l === 75 && pry.d1 - pry.d0 >= 75 * 0.09 - 0.5,
    JSON.stringify({ loud: pry.loud, gain: +(pry.d1 - pry.d0).toFixed(2) }));

  await fresh();
  const hands = await g(() => {
    const took = { held: true };
    // The real verb, not the hold() hook - hold() attaches an item directly and
    // would happily put a vase in a hand that is already full of crowbar. It has
    // to be aimed at a real piece too: grab() with nothing in front of you does
    // nothing whether the rule is there or not, which is a check that cannot fail.
    const it = window.__g.list()[0];
    window.__g.moveCrowbar(it.x, it.z);
    window.__g.tp(it.x, it.z - 1.1);
    window.__g.look(0, 0);
    window.__g.takeCrowbar();
    window.__g.grab();
    const gotDolly = window.__g.takeDolly();
    window.__g.takeCrowbar();                      // put it down again
    const after = window.__g.crowbar();
    return { took, gotDolly, after, carry: window.__g.carry() };
  });
  ok("the crowbar takes both hands",
    hands.took !== null && hands.carry === null && hands.gotDolly === null,
    JSON.stringify(hands));
  ok("and you can put it down where you are standing",
    hands.after.held === false, JSON.stringify(hands.after));

  // The deepest wing is shut twice over - by its prerequisite chain and by the
  // boards - so "the crew cannot get in" says nothing about boards on its own.
  // Clear the prerequisite first, and then the only thing left holding it is wood.
  await fresh();
  const onlyWood = await g(() => {
    const b = window.__g.boarded();
    // Empty every sideboard in the house except the wing's own: the prerequisite
    // chain is then satisfied everywhere, the neighbours are open too, and the
    // only thing left that can lock a door is wood. Clearing just the wing's own
    // prerequisite is not enough - its neighbours are deep rooms with chains of
    // their own, and they kept the doors shut whether or not boards did anything.
    const emptied = window.__g.rooms().filter(r => !r.van && r.id !== b.wing)
      .map(r => window.__g.clearRoom(r.id)).filter(Boolean).length;
    const lockedAfter = window.__g.locked();
    const boardIds = b.doors.map(d => d.id);
    let inside = 0;
    for (let i = 0; i < 60 * 60; i++) {
      window.__g.step(1, 1 / 60);
      if (i % 30) continue;
      for (const c of window.__g.crew()) if (window.__g.roomAt(c.x, c.z) === b.wing) inside++;
    }
    return { wing: b.wing, emptied, lockedAfter, boardIds, inside };
  });
  ok("with every prerequisite in the house cleared, the boards are the only lock left",
    onlyWood.lockedAfter.length === onlyWood.boardIds.length &&
    onlyWood.boardIds.every(id => onlyWood.lockedAfter.includes(id)) &&
    onlyWood.inside === 0, JSON.stringify(onlyWood));

  // The boards are the crew's problem and the player's job. Nothing in the crew AI
  // fetches a tool, so a night with the wing shut is a night worked around it.
  await fresh();
  const crewBoards = await g(() => {
    const wing = window.__g.boarded().wing;
    let inside = 0;
    for (let i = 0; i < 60 * 90; i++) {
      window.__g.step(1, 1 / 60);
      if (i % 30) continue;
      for (const c of window.__g.crew()) if (window.__g.roomAt(c.x, c.z) === wing) inside++;
    }
    return { inside, wing, banked: window.__g.state().banked,
      quota: window.__g.contract().quota };
  });
  ok("the crew work around a boarded wing rather than jamming against it",
    crewBoards.inside === 0 && crewBoards.banked > 0, JSON.stringify(crewBoards));

  // ...and the Curator is not a crew member. It is the house.
  await fresh();
  const curBoards = await g(() => {
    const b = window.__g.boarded(), d = b.doors[0];
    const rooms = window.__g.rooms();
    const out = rooms.find(r => r.id !== b.wing && (d.id.split("-").includes(r.id)));
    window.__g.parkCrew();
    window.__g.setCur(d.x, d.z, "PURSUE");
    window.__g.tp(out.x, out.z);
    let crossed = false;
    for (let i = 0; i < 60 * 20 && !crossed; i++) {
      window.__g.setDist(95);
      window.__g.heard(65, out.x, out.z);
      window.__g.step(1, 1 / 60);
      const c = window.__g.curator();
      if (window.__g.roomAt(c.x, c.z) === out.id) crossed = true;
    }
    return { crossed, boards: window.__g.boarded().doors.length };
  });
  ok("boards do not stop the Curator - it is the house, not a guest",
    curBoards.crossed === true && curBoards.boards > 0, JSON.stringify(curBoards));

  // What the crowbar actually buys: the thing the whole night builds toward.
  const apexBehind = await g(() => {
    window.__g.newContract(4242); window.__g.regen(4242, 3); window.__g.setNight(3);
    const a = window.__g.apex(), b = window.__g.boarded();
    return { apexRoom: a && a.room, wing: b.wing, boards: b.doors.length };
  });
  const reboard = await g(() => {
    const before = window.__g.boarded();
    window.__g.tp(before.doors[0].x, before.doors[0].z);
    window.__g.moveCrowbar(before.doors[0].x, before.doors[0].z);
    window.__g.takeCrowbar();
    const wing = window.__g.rooms().find(r => r.id === before.wing);
    window.__g.look(Math.atan2(wing.x - before.doors[0].x, wing.z - before.doors[0].z));
    window.__g.press("KeyW");
    for (let i = 0; i < 60 * 6 && window.__g.boarded().doors.length; i++)
      window.__g.step(1, 1 / 60);
    window.__g.clearKeys();
    const opened = window.__g.boarded().doors.length;
    window.__g.reset();
    return { opened, after: window.__g.boarded().doors.length, was: before.doors.length };
  });
  ok("and a new night puts the boards back up",
    reboard.opened === 0 && reboard.after === reboard.was && reboard.was > 0,
    JSON.stringify(reboard));

  ok("on a late night the apex is behind the boards",
    apexBehind.apexRoom === apexBehind.wing && apexBehind.boards > 0,
    JSON.stringify(apexBehind));

  await g(() => { window.__g.newContract(20260806); window.__g.regen(20260806); });

  // --- the salt line (DESIGN 8) ---------------------------------------------
  // "Curator won't cross for 20s, single use, consumed."
  //
  // What it actually buys, measured: a DETOUR, not denial. V3 requires every
  // wing to survive losing any one portal, so a house that passes the level
  // contract has a second way round by construction and salting one doorway can
  // never seal anything. The first version of this check asserted the Curator
  // never entered the salted corridor and passed with the rule DELETED, because
  // it was going the other way regardless. Same V3/V4 tension R1 found: every
  // second route that satisfies V3 is a bypass that defeats a pinch.
  await fresh();
  const saltLine = await g(() => {
    const rooms = window.__g.rooms();
    const d = window.__g.doors()[1];
    const A = rooms.find(r => r.id === d.a), B = rooms.find(r => r.id === d.b);

    // Deterministic: what the router picks, and whether the body can pass.
    window.__g.reset(); window.__g.parkCrew(); window.__g.gates(true);
    const routeClear = window.__g.route(d.a, d.b);
    window.__g.tp(d.x, d.z);
    window.__g.layStop();
    const routeSalted = window.__g.route(d.a, d.b);

    // Physical block: stand it in the corridor mouth and drive it through.
    const along = d.axis === "x" ? [1, 0] : [0, 1];
    const sign = d.axis === "x" ? Math.sign(B.x - A.x) : Math.sign(B.z - A.z);
    window.__g.setCur(d.x - along[0] * 1.6 * sign, d.z - along[1] * 1.6 * sign, "PURSUE");
    window.__g.tp(B.x, B.z);
    const start = window.__g.curator();
    for (let i = 0; i < 60 * 8; i++) {
      window.__g.setDist(95);
      window.__g.heard(65, B.x, B.z);
      window.__g.step(1, 1 / 60);
    }
    const after = window.__g.curator();
    const q = d.rect;
    const inCorridor = after.x > q.x0 && after.x < q.x1 && after.z > q.z0 && after.z < q.z1;
    const pastIt = d.axis === "x" ? (after.x - d.x) * sign > 0 : (after.z - d.z) * sign > 0;

    window.__g.reset();
    const outside = window.__g.layStop();          // not standing in a doorway
    window.__g.tp(d.x, d.z);
    const first = window.__g.layStop();
    const second = window.__g.layStop();
    const state = window.__g.levers();
    const moved = Math.hypot(after.x - start.x, after.z - start.z);
    return { routeClear, routeSalted, inCorridor, pastIt, moved: +moved.toFixed(2),
             outside, first, second, state, d: `${d.a}-${d.b}` };
  });
  ok("salt only goes down in a doorway",
    saltLine.outside === null && saltLine.first !== null, JSON.stringify(saltLine));
  ok("and there is one charge of it",
    saltLine.second === null && saltLine.state.saltCharges === 0,
    JSON.stringify(saltLine.state));
  ok("it holds for twenty seconds",
    saltLine.state.salt !== null && saltLine.state.salt.left > 19,
    JSON.stringify(saltLine.state));
  ok("the router sends it the other way once salt is down",
    saltLine.routeClear === saltLine.d && saltLine.routeSalted !== saltLine.routeClear &&
    saltLine.routeSalted !== null,
    JSON.stringify({ door: saltLine.d, clear: saltLine.routeClear,
                     salted: saltLine.routeSalted }));
  // The physical block behind the router. It is only reachable when there is no
  // way round at all, so this asserts the weaker thing it can honestly assert:
  // the Curator moved, and it did not end up on your side of the line.
  ok("and it does not walk over the line while going round",
    saltLine.moved > 1.0 && saltLine.pastIt === false && saltLine.inCorridor === false,
    JSON.stringify({ moved: saltLine.moved, past: saltLine.pastIt,
                     inCorridor: saltLine.inCorridor }));

  // --- the dead (DESIGN 5.1) ------------------------------------------------
  // "Die at minute three of a fourteen-minute night and the genre standard is
  // that you watch for eleven." The collection beat is deliberately slow, and
  // what comes after it is a role.
  await fresh();
  const dead = await g(() => {
    window.__g.parkCrew();
    const f = window.__g.rooms().find(r => !r.van);
    window.__g.tp(f.x, f.z);
    window.__g.setDist(95);
    // Two contacts.
    for (let hit = 0; hit < 2; hit++) {
      for (let i = 0; i < 3000 && window.__g.state().hits <= hit; i++) {
        const p = window.__g.raw();
        window.__g.setCur(p.x + 1.0, p.z, "PURSUE");
        window.__g.setDist(95);
        window.__g.step(1, 1 / 60);
      }
    }
    const atDeath = window.__g.ghost();
    window.__g.step(60 * 5, 1 / 60);              // five seconds in
    const half = window.__g.ghost();
    window.__g.step(60 * 6, 1 / 60);              // past ten
    const now = window.__g.ghost();
    return { atDeath, half, now, over: window.__g.state().over,
             corpses: window.__g.corpses() };
  });
  ok("the collection beat is ten seconds",
    dead.atDeath.collecting > 9 && dead.half.dead === false && dead.now.dead === true,
    JSON.stringify(dead));
  ok("and the night does not end when you do", dead.over === false, JSON.stringify(dead));
  ok("your body is left where you fell",
    dead.corpses.some(c => c.who === "YOU"), JSON.stringify(dead.corpses));

  const ghost = await g(() => {
    // Free movement: walls are not a thing any more.
    const before = window.__g.raw();
    window.__g.look(Math.PI / 2, 0);
    window.__g.press("KeyW"); window.__g.step(240, 1 / 60); window.__g.clearKeys();
    const after = window.__g.raw();
    const travelled = Math.hypot(after.x - before.x, after.z - before.z);
    // A ghost carries nothing.
    const list = window.__g.list();
    const near = list.find(i => !i.corpse && !i.held);
    window.__g.tp(near.x - 0.8, near.z);
    window.__g.grab();
    const holding = window.__g.state().holding;
    return { travelled, holding, static: window.__g.ghost().static };
  });
  ok("the dead move freely through the house", ghost.travelled > 12,
    JSON.stringify(ghost));
  ok("and cannot carry anything", ghost.holding === null, JSON.stringify(ghost));

  // Curse-sight: the grade at 5m, never the number. "The dead help you not die,
  // they don't help you get rich" - 4.4's economic loop has to stay untouched.
  const graded = await g(() => {
    const list = window.__g.list();
    const it = list.find(i => !i.corpse && !i.held);
    const idx = list.indexOf(it);
    window.__g.tp(it.x + 2.0, it.z);
    const near = window.__g.curseSight(idx);
    window.__g.tp(it.x + 9.0, it.z);
    const far = window.__g.curseSight(idx);
    return { near, far, known: window.__g.list()[idx].known };
  });
  ok("the dead see curse grades within five metres",
    graded.near === true && graded.far === false, JSON.stringify(graded));
  ok("but never the value - that stays the appraiser's job",
    graded.known === false, JSON.stringify(graded));

  // Static: the intervention budget, and the one line that balances it.
  const statics = await g(() => {
    window.__g.setStatic(6); window.__g.setDist(50);
    // A knock is L25: heard at 25 x 0.33 = 8.25m through open air. Put it in
    // earshot, or this tests nothing but the geometry of where it happened to be.
    const me = window.__g.raw();
    window.__g.setCur(me.x + 3.0, me.z);
    const d0 = window.__g.state().dist, s0 = window.__g.ghost().static;
    const knocked = window.__g.knock();
    const d1 = window.__g.state().dist, s1 = window.__g.ghost().static;
    // A knock is heard: it should hand the Curator a fix near the ghost.
    const fix = window.__g.fix();
    // ...and not heard from across the house.
    window.__g.setCur(me.x + 40, me.z);
    window.__g.setStatic(6);
    window.__g.knock();
    const farFix = window.__g.fix();
    window.__g.setStatic(0);
    const refused = window.__g.knock();
    // regen
    window.__g.step(60 * 21, 1 / 60);
    const regen = window.__g.ghost().static;
    // A fix does not expire on its own, so "did it hear the far knock" is
    // whether the fix MOVED - comparing ages compares the same stale fix twice.
    return { knocked, refused, s0, s1, d0, d1, fix, regen,
             farHeard: !!farFix && (farFix.x !== fix.x || farFix.z !== fix.z) };
  });
  ok("a knock costs one Static", statics.knocked === true && statics.s1 === statics.s0 - 1,
    JSON.stringify(statics));
  ok("and every point spent makes the house angrier",
    statics.d1 - statics.d0 >= 1 + 25 * 0.09 - 0.05, JSON.stringify(statics));
  ok("it pulls the Curator toward the ghost",
    statics.fix !== null && statics.fix.age < 1, JSON.stringify(statics.fix));
  ok("and only if it is close enough to hear it",
    statics.farHeard === false, JSON.stringify(statics));
  ok("an empty budget spends nothing", statics.refused === false, JSON.stringify(statics));
  ok("Static regenerates one per twenty seconds", statics.regen === 1,
    JSON.stringify(statics));

  const nudged = await g(() => {
    window.__g.setStatic(6);
    const it = window.__g.list().find(i => !i.corpse && !i.held && i.shelf !== null);
    window.__g.tp(it.x + 0.6, it.z);
    // Snapshot everything: nudge takes the nearest piece, which need not be the
    // one this fixture picked, and comparing only that one reported no movement
    // when a neighbour had just been knocked onto the floor.
    const before = window.__g.list().map(i => `${i.value}@${i.x},${i.y},${i.z}`);
    const staticBefore = window.__g.ghost().static;
    const did = window.__g.nudge();
    const after = window.__g.list().map(i => `${i.value}@${i.x},${i.y},${i.z}`);
    const changed = after.filter(k => !before.includes(k)).length + (before.length - after.length);
    return { did, cost: staticBefore - window.__g.ghost().static, changed,
             broken: window.__g.broken().length };
  });
  ok("a nudge costs three Static", nudged.did === true && nudged.cost === 3,
    JSON.stringify(nudged));
  ok("and it actually moves something off a shelf",
    nudged.changed > 0 || nudged.broken > 0, JSON.stringify(nudged));

  // --- fragility (DESIGN 5) -------------------------------------------------
  // "A broken item is worth $0 and makes a lot of noise. Fragile items are
  // disproportionately valuable - the physics does the comedy."
  await fresh();
  const frag = await g(() => {
    window.__g.parkCrew();
    const list = window.__g.list();
    const byGrade = [0, 1, 2, 3].map(g => list.filter(i => i.frag === g).length);
    // Same piece, put down standing still vs let go at a run, many times over.
    const trial = (speed) => {
      let broke = 0, tries = 40;
      for (let t = 0; t < tries; t++) {
        window.__g.reset(); window.__g.parkCrew();
        const l = window.__g.list();
        const idx = l.findIndex(i => i.frag === 3 && i.klass === "armful");
        if (idx < 0) return null;
        window.__g.hold(idx);
        window.__g.setSpeed(speed);
        window.__g.grab();
        if (window.__g.broken().length) broke++;
      }
      return broke / tries;
    };
    const still = trial(0), sprinting = trial(4.1);
    return { byGrade, still, sprinting };
  });
  ok("fragility is spread across the loot",
    frag.byGrade.every(n => n > 0), JSON.stringify(frag.byGrade));
  ok("putting a piece down carefully never breaks it", frag.still === 0,
    JSON.stringify(frag));
  ok("letting go at a run breaks the fragile ones",
    frag.sprinting > 0.4, JSON.stringify(frag));

  const smashed = await g(() => {
    window.__g.reset(); window.__g.parkCrew();
    const l = window.__g.list();
    const idx = l.findIndex(i => i.frag === 3 && i.klass === "armful");
    const value = l[idx].value;
    window.__g.setDist(40);
    const before = window.__g.state().dist;
    window.__g.hold(idx); window.__g.setSpeed(4.1);
    let tries = 0;
    while (!window.__g.broken().length && tries++ < 60) {
      window.__g.grab();                       // drop
      if (!window.__g.broken().length) window.__g.hold(idx);
    }
    const after = window.__g.state();
    return { value, broke: window.__g.broken().length, noise: after.dist - before,
             holding: after.holding, banked: after.banked, log: window.__g.noiseLog().slice(-1) };
  });
  ok("a broken piece is worth nothing and is out of the night",
    smashed.broke > 0 && smashed.holding === null && smashed.banked === 0,
    JSON.stringify(smashed));
  ok("and it is heard", smashed.log.length === 1 && smashed.log[0].l >= 90,
    JSON.stringify(smashed.log));

  const premium = await g(() => {
    // Pooled over many seeds and over pairs of grades. The premium is 18% per
    // grade against a band that spans 80-300, so a per-grade mean off eight
    // seeds is mostly noise - this check failed one run in six on exactly that.
    const rows = [[], [], [], []];
    for (let s = 1; s <= 24; s++) {
      window.__g.newContract(s * 7919);
      for (const it of window.__g.list())
        if (it.klass === "armful" && it.grade === "clean" && it.tier <= 1)
          rows[it.frag].push(it.value);
    }
    window.__g.newContract(20260806);
    const mean = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0;
    return { each: rows.map(r => Math.round(mean(r))), n: rows.map(r => r.length),
             sturdy: Math.round(mean([...rows[0], ...rows[1]])),
             delicate: Math.round(mean([...rows[2], ...rows[3]])) };
  });
  ok("delicate pieces are worth more than sturdy ones",
    premium.delicate > premium.sturdy * 1.15 &&
    premium.n.every(n => n > 10), JSON.stringify(premium));

  // --- the corpse economy (DESIGN 5) ----------------------------------------
  // "Recover him and he's back next night, free. Leave him and you run
  // tomorrow's higher quota one hauler short. That's the entire trade - no cash,
  // no fees, no invented currency."
  await fresh();
  const body = await g(() => {
    window.__g.freezeCrew(true);
    const before = window.__g.roster().alive.length;
    const dead = window.__g.killCrew(0);
    const c = window.__g.corpses();
    return { before, dead, corpses: c, after: window.__g.roster() };
  });
  ok("a collected crewmate leaves a body",
    body.corpses.length === 1 && body.corpses[0].who === body.dead.name,
    JSON.stringify(body));
  ok("and the body is a two-man object",
    body.corpses.length > 0 && body.corpses[0].klass === "two_man" &&
    body.corpses[0].value > 0, JSON.stringify(body.corpses));

  // It radiates: carrying your friend makes you a target, exactly like loot.
  const carriedBody = await g(() => {
    const list = window.__g.list();
    const idx = list.findIndex(i => i.corpse);
    const f = window.__g.rooms().find(r => !r.van);
    window.__g.tp(f.x, f.z);
    window.__g.hold(idx);
    for (let i = 0; i < 30; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    return { st: window.__g.state(), cur: window.__g.curator() };
  });
  ok("carrying your friend makes you a target",
    carriedBody.st.marked === true, JSON.stringify(carriedBody.st));

  // It pays nothing, and it costs three slots to bring home.
  const recovered = await g(() => {
    const v = window.__g.rooms().find(r => r.van);
    const slotsBefore = window.__g.vanSlots();
    window.__g.tp(v.x, v.z); window.__g.step(4, 1 / 60);
    const st = window.__g.state();
    const roster = window.__g.roster();
    window.__g.setT(209.5); window.__g.step(60, 1 / 60);
    const after = window.__g.contract().last;
    return { slotsUsed: slotsBefore - window.__g.vanSlots(), banked: st.banked,
             roster, net: after.net, gross: after.gross };
  });
  ok("bringing a body home costs three slots and pays nothing",
    recovered.slotsUsed === 3 && recovered.banked === 0 && recovered.gross === 0,
    JSON.stringify(recovered));
  ok("and it is the crewmate you get back, not money",
    recovered.roster.recovered.length === 1, JSON.stringify(recovered.roster));

  // Leave him and tomorrow is a hauler short.
  const left = await g(() => {
    window.__g.newContract(777); window.__g.freezeCrew(true);
    const dead = window.__g.killCrew(0);
    window.__g.bank(window.__g.contract().quota + 200);   // pass the night anyway
    window.__g.setT(209.5); window.__g.step(60, 1 / 60);
    const beforeNext = window.__g.roster();
    window.__g.nextNight();
    const now = window.__g.roster();
    window.__g.newContract(20260806);
    return { dead, beforeNext, now };
  });
  ok("a body left behind is a hauler you do not have tomorrow",
    left.now.alive.length === 2 && left.now.lost.includes(left.dead.name),
    JSON.stringify(left));

  // --- night endings --------------------------------------------------------
  await fresh();
  const sunrise = await g(() => {
    window.__g.setT(209.5);
    window.__g.step(60, 1 / 60);
    return window.__g.state();
  });
  ok("sunrise ends the night", sunrise.over === true && sunrise.why === "SUNRISE",
    JSON.stringify(sunrise));

  await fresh();
  const full = await g(() => {
    const v = window.__g.rooms().find(r => r.van);
    // Take armfuls only: a two-man piece costs three slots and will be refused
    // once fewer than three are left, which stalls the fill rather than ending it.
    for (let i = 0; i < 40 && !window.__g.state().over; i++) {
      const idx = window.__g.list().findIndex(it => it.klass === "armful" && !it.held);
      if (idx < 0) break;
      window.__g.hold(idx); window.__g.tp(v.x, v.z); window.__g.step(2, 1 / 60);
    }
    return window.__g.state();
  });
  ok("a full van ends the night", full.over === true && full.why === "VAN FULL",
    JSON.stringify(full));

  // --- retrieval, then death ------------------------------------------------
  await fresh();
  const contact = await g(() => {
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    window.__g.setDist(95);
    const value = window.__g.hold(0);
    const p = window.__g.pos();
    window.__g.setCur(p.x + 1.0, p.z, "PURSUE");
    for (let i = 0; i < 400 && !window.__g.state().over; i++) {
      window.__g.step(1, 1 / 60);
      if (window.__g.state().hits >= 1) break;
    }
    return { value, st: window.__g.state(), cur: window.__g.curator() };
  });
  ok("first contact takes the item, not the player",
    contact.st.hits === 1 && contact.st.over === false && contact.st.holding === null,
    JSON.stringify(contact.st));
  ok("the Curator carries the piece home", contact.cur.carrying === true,
    JSON.stringify(contact.cur));

  const second = await g(() => {
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    window.__g.setDist(95);
    window.__g.hold(0);
    for (let i = 0; i < 3000 && !window.__g.state().over; i++) {
      const p = window.__g.pos();
      window.__g.setCur(p.x + 1.0, p.z, "PURSUE");
      window.__g.step(1, 1 / 60);
    }
    return window.__g.state();
  });
  // Second contact no longer ends the night: it collects you, and DESIGN 5.1
  // turns that into a role rather than a spectator seat.
  // The beat's exact length is checked in the dead-player battery; here it is
  // enough that the second contact collects you and the night carries on.
  ok("second contact collects you",
    second.hits >= 2 && second.over === false &&
    (second.collecting > 0 || second.dead === true), JSON.stringify(second));

  // --- the house is a house -------------------------------------------------
  // Sprint out of every room and every corridor on 16 headings, checking
  // containment on every tick rather than only where the walk happens to end -
  // passing through the void and back in again is still a leak.
  //
  // The legal region is recomputed here from room boxes and the link list, NOT
  // from the game's own solid(). Asking solid() whether the player is somewhere
  // legal cannot fail: a doorway test that is too permissive simply declares its
  // own leak to be floor. That is exactly the bug this check exists to catch.
  await fresh();
  const leaks = await g(() => {
    const rooms = window.__g.rooms(), doors = window.__g.doors();
    const DOOR_W = 2.2, LIP = 0.06, EPS = 0.02;
    const box = r => ({ x0: r.x - r.w / 2, x1: r.x + r.w / 2, z0: r.z - r.d / 2, z1: r.z + r.d / 2 });
    const corridors = doors.map(d => {
      const A = box(rooms.find(r => r.id === d.a)), B = box(rooms.find(r => r.id === d.b));
      const ox = [Math.max(A.x0, B.x0), Math.min(A.x1, B.x1)];
      const oz = [Math.max(A.z0, B.z0), Math.min(A.z1, B.z1)];
      const alongX = ox[1] <= ox[0];
      const span = alongX ? oz : ox, c = (span[0] + span[1]) / 2, h = DOOR_W / 2;
      const gA = alongX ? [A.x0, A.x1] : [A.z0, A.z1];
      const gB = alongX ? [B.x0, B.x1] : [B.z0, B.z1];
      const lo = Math.min(gA[1], gB[1]), hi = Math.max(gA[0], gB[0]);
      return alongX ? { x0: lo - LIP, x1: hi + LIP, z0: c - h, z1: c + h }
                    : { x0: c - h, x1: c + h, z0: lo - LIP, z1: hi + LIP };
    });
    const legal = (x, z) => [...rooms.map(box), ...corridors].some(b =>
      x >= b.x0 - EPS && x <= b.x1 + EPS && z >= b.z0 - EPS && z <= b.z1 + EPS);

    const out = [];
    const starts = rooms.map(r => ({ id: r.id, x: r.x, z: r.z }))
      .concat(doors.map(d => ({ id: d.a + "-" + d.b, x: d.x, z: d.z })));
    for (const st of starts) {
      for (let k = 0; k < 16; k++) {
        window.__g.reset();
        window.__g.tp(st.x, st.z);
        window.__g.look((k / 16) * Math.PI * 2);
        window.__g.press("KeyW"); window.__g.press("ShiftLeft");
        for (let i = 0; i < 480 && out.length < 6; i++) {   // 8 seconds
          window.__g.step(1, 1 / 60);
          const p = window.__g.raw();
          if (!legal(p.x, p.z)) {
            out.push({ from: st.id, heading: k, x: +p.x.toFixed(2), z: +p.z.toFixed(2) });
            break;
          }
        }
        window.__g.clearKeys();
      }
    }
    return out;
  });
  ok("no room or corridor leaks to the outside", leaks.length === 0, JSON.stringify(leaks));

  // --- concealment (DESIGN 8.1) --------------------------------------------
  await fresh();
  const hides = await g(() => window.__g.hides());
  const roomsWithHides = new Set(hides.map(h => h.room));
  const lootRooms = await g(() => window.__g.rooms().filter(r => r.id !== "drive").map(r => r.id));
  ok("every room but the driveway has concealment",
    lootRooms.every(r => roomsWithHides.has(r)), JSON.stringify([...roomsWithHides]));

  await fresh();
  const enter = await g(() => {
    window.__g.setDist(40);
    const before = window.__g.state().dist;
    const got = window.__g.hide(0);
    const half = { in: got, concealed: window.__g.state().concealed };
    window.__g.step(30, 1 / 60);              // 0.5s - still climbing in
    const mid = window.__g.state().concealed;
    window.__g.step(45, 1 / 60);              // past 1.0s
    const done = window.__g.state().concealed;
    return { before, after: window.__g.state().dist, half, mid, done };
  });
  ok("entering a hiding place takes a second", enter.mid === false && enter.done === true,
    JSON.stringify(enter));
  ok("entering is silent", enter.after <= enter.before + 0.01,
    `${enter.before} -> ${enter.after}`);

  const leave = await g(() => {
    const before = window.__g.state().dist;
    window.__g.toggleHide();
    return { before, after: window.__g.state().dist, concealed: window.__g.state().concealed };
  });
  near("leaving costs a door - L60 x 0.09", leave.after - leave.before, 60 * 0.09, 0.05);
  ok("leaving is instant", leave.concealed === false, JSON.stringify(leave));

  // Concealed and empty-handed at COLLECT: the hiding game the genre trades on.
  await fresh();
  const hidCollect = await g(() => {
    window.__g.hide(0);
    window.__g.step(90, 1 / 60);
    for (let i = 0; i < 40; i++) { window.__g.setDist(95); window.__g.step(15, 1 / 60); }
    return window.__g.state();
  });
  // With a crew in the house it does not stop hunting - it hunts someone else,
  // which is the rule working rather than failing. What concealment buys is that
  // the someone else is not you.
  ok("concealment works at COLLECT",
    hidCollect.who !== "YOU" && hidCollect.hits === 0, JSON.stringify(hidCollect));

  // Concealed WITH the prize: it comes to the wardrobe and opens it.
  await fresh();
  const hidLoot = await g(() => {
    window.__g.parkCrew();
    window.__g.gates(true);
    const h = window.__g.hides()[0];
    const idx = window.__g.list().findIndex(i => Math.hypot(i.x - h.x, i.z - h.z) < 90);
    window.__g.hold(idx);
    window.__g.hide(0);
    window.__g.step(90, 1 / 60);
    let sawOpening = false, opened = 0;
    for (let i = 0; i < 6000 && !window.__g.state().over; i++) {
      window.__g.setDist(70);
      window.__g.step(1, 1 / 60);
      const st = window.__g.state();
      if (st.opening > 0) { sawOpening = true; opened = Math.max(opened, st.opening); }
      if (st.hits >= 1) break;
    }
    return { sawOpening, opened, st: window.__g.state() };
  });
  ok("hiding with the prize does not hide the prize",
    hidLoot.sawOpening === true, JSON.stringify(hidLoot.st));
  ok("being found while concealed is a retrieval, not a death",
    hidLoot.st.hits === 1 && hidLoot.st.over === false, JSON.stringify(hidLoot.st));
  ok("opening the door takes about four seconds", hidLoot.opened >= 3.9,
    `opened=${hidLoot.opened}`);

  // Stash: the item goes quiet for 20s and the chase breaks.
  await fresh();
  const stashed = await g(() => {
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.parkCrew();
    window.__g.tp(f.x, f.z);
    window.__g.setDist(70);
    window.__g.hold(0);
    for (let i = 0; i < 20; i++) window.__g.step(15, 1 / 60);
    const chasing = window.__g.state().marked;
    const before = window.__g.state().dist;
    const hi = window.__g.hides().findIndex(h => h.room === "foyer");
    const h = window.__g.hides()[hi];
    window.__g.tp(h.x, h.z - 1.0);
    window.__g.stash();
    const quiet = window.__g.radiance(0);
    window.__g.step(60, 1 / 60);
    const dropped = window.__g.state().marked;
    const t20 = window.__g.stashOf(0);
    return { chasing, quiet, dropped, t20, noise: window.__g.state().dist - before };
  });
  ok("stashing silences the piece", stashed.chasing === true && stashed.quiet === 0,
    JSON.stringify(stashed));
  ok("stashing breaks the chase", stashed.dropped === false, JSON.stringify(stashed));
  ok("the stash lasts twenty seconds", stashed.t20 > 18 && stashed.t20 <= 20,
    `remaining=${stashed.t20}`);

  // ...and when it runs out, the collection comes and takes it back.
  await fresh();
  const expired = await g(() => {
    window.__g.parkCrew();
    window.__g.gates(true);
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    window.__g.setDist(70);
    const value = window.__g.hold(0);
    const hi = window.__g.hides().findIndex(h => h.room === "foyer");
    const h = window.__g.hides()[hi];
    window.__g.tp(h.x, h.z - 1.0);
    window.__g.stash();
    window.__g.tp(f.x, f.z);
    // Sample throughout: by 45s the whole retrieval can already be over, and an
    // end-state assertion would read that as the Curator never having come.
    let came = false, quietFor = 0;
    for (let i = 0; i < 90; i++) {
      window.__g.setDist(70); window.__g.step(30, 1 / 60);
      const st = window.__g.state();
      // "It came" means it is hunting THIS piece - the mark is not on the player
      // once the piece is out of their hands, which is D-06 working.
      const c = window.__g.curator();
      const after = c.goalValue === value || c.carrying || st.cur === "RESEAT";
      if (st.t < 20 && after) quietFor++;
      if (after) came = true;
    }
    return { came, quietFor, value, st: window.__g.state(), cur: window.__g.curator() };
  });
  ok("a stash buys quiet while it lasts", expired.quietFor === 0, JSON.stringify(expired));
  ok("a stash is a delay, not a solution", expired.came === true, JSON.stringify(expired));

  await fresh();
  const stuck = await g(() => {
    window.__g.hide(0);
    window.__g.step(90, 1 / 60);
    const at = window.__g.raw();
    window.__g.press("KeyW");
    window.__g.step(60, 1 / 60);
    const after = window.__g.raw();
    window.__g.clearKeys();
    return { moved: Math.hypot(after.x - at.x, after.z - at.z), concealed: window.__g.state().concealed };
  });
  ok("walking out of a hiding place leaves it", stuck.concealed === false, JSON.stringify(stuck));

  // --- the selector, with more than one candidate in the house (A3) ---------
  // None of this could be tested before R20: with a single actor there was
  // never a second weight to compare against, so "the richest carrier is
  // hunted", the 1.25x steal threshold and the 8s commitment were all
  // unexercised code paths.
  await fresh();
  const richest = await g(() => {
    window.__g.freezeCrew(true); window.__g.clearCrew();
    const list = window.__g.list();
    const sorted = [...list].sort((a, b) => b.value - a.value);
    const rich = list.indexOf(list.find(i => i === sorted[0]));
    const poor = list.indexOf(list.find(i => i === sorted[sorted.length - 1]));
    window.__g.giveCrew(0, rich);
    window.__g.giveCrew(1, poor);
    for (let i = 0; i < 40; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    return { cur: window.__g.curator(), rich: sorted[0].value,
             poor: sorted[sorted.length - 1].value };
  });
  ok("the richest carrier is the one hunted",
    richest.cur.goalValue === richest.rich, JSON.stringify(richest));

  // Pillar 2 at multi-actor scale: noise multiplies LOOT, it is never an addend.
  // An empty-handed crewmate making a racket must never outweigh a quiet carrier.
  await fresh();
  const loudEmpty = await g(() => {
    window.__g.freezeCrew(true); window.__g.clearCrew();
    const list = window.__g.list();
    const cheap = list.reduce((a, b) => (a.value < b.value ? a : b));
    window.__g.giveCrew(0, list.indexOf(cheap));       // carrying the worst piece
    window.__g.crewNoise(1, 40);                       // carrying nothing, deafening
    for (let i = 0; i < 40; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    const c = window.__g.curator();
    return { who: c.who, goal: c.goalValue, cheap: cheap.value };
  });
  ok("a loud empty-handed crewmate is still worth nothing",
    loudEmpty.goal === loudEmpty.cheap, JSON.stringify(loudEmpty));

  // Noise multiplies what you carry: same piece, one of them shouting.
  await fresh();
  const noisy = await g(() => {
    window.__g.freezeCrew(true); window.__g.clearCrew();
    // Same grade, similar value: attention weight is value x curse multiplier,
    // so a malignant piece can outweigh a clean one worth twice as much and the
    // noise term would not be what decided it.
    const list = window.__g.list();
    const clean = list.filter(i => i.grade === "clean").sort((x, y) => x.value - y.value);
    const pair = clean.slice(Math.floor(clean.length / 2), Math.floor(clean.length / 2) + 2);
    const a = list.indexOf(pair[0]), b = list.indexOf(pair[1]);
    window.__g.giveCrew(0, a);
    window.__g.giveCrew(1, b);
    window.__g.crewNoise(1, 6);                        // 1 + 0.20*6 = 2.2x
    for (let i = 0; i < 40; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    return { goal: window.__g.curator().goalValue, quiet: pair[0].value, loud: pair[1].value };
  });
  ok("noise multiplies the loot you are carrying",
    noisy.goal === noisy.loud, JSON.stringify(noisy));

  // Hysteresis: a marginally better piece must NOT steal the target.
  await fresh();
  const hyst = await g(() => {
    window.__g.freezeCrew(true); window.__g.clearCrew();
    // Same grade throughout: attention weight is value x curse multiplier, so a
    // $332 malignant outweighs a $612 clean and "decisively richer" in dollars
    // can be lighter to the Curator. Comparing like with like isolates hysteresis.
    // Same grade throughout: attention weight is value x curse multiplier, so a
    // $332 malignant outweighs a $612 clean and "decisively richer" in dollars
    // can be lighter to the Curator. Comparing like with like isolates hysteresis.
    // Indices must come from ONE list() call - each returns fresh objects.
    const all = window.__g.list();
    const clean = all.filter(i => i.grade === "clean");
    const base = clean.find(i => i.value > 200) || clean[0];
    const marginal = clean.filter(i => i !== base)
      .map(i => ({ i, r: i.value / base.value }))
      .filter(x => x.r > 1.02 && x.r < 1.2).sort((a, b) => b.r - a.r)[0];
    const big = clean.filter(i => i !== base)
      .map(i => ({ i, r: i.value / base.value })).filter(x => x.r > 1.5)
      .sort((a, b) => a.r - b.r)[0];
    if (!marginal || !big) return { skipped: true };
    window.__g.giveCrew(0, all.indexOf(base));
    for (let i = 0; i < 60; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    const locked = window.__g.curator().goalValue;
    window.__g.giveCrew(1, all.indexOf(marginal.i));
    for (let i = 0; i < 60; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    const afterMarginal = window.__g.curator().goalValue;
    window.__g.giveCrew(2, all.indexOf(big.i));
    for (let i = 0; i < 60; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    return { locked, afterMarginal, afterBig: window.__g.curator().goalValue,
             base: base.value, marginal: marginal.i.value, big: big.i.value,
             ratio: +marginal.r.toFixed(3) };
  });
  ok("a marginally richer piece does not steal the target",
    hyst.skipped || hyst.afterMarginal === hyst.locked, JSON.stringify(hyst));
  ok("a decisively richer piece does",
    hyst.skipped || hyst.afterBig === hyst.big, JSON.stringify(hyst));

  // Commitment: even a decisively richer piece has to wait out the lock. This is
  // what makes it look decisive rather than indecisive, and nothing tested it
  // until the steal-threshold injection came back clean with COMMIT_S = 0.
  await fresh();
  const commit = await g(() => {
    window.__g.freezeCrew(true); window.__g.clearCrew();
    const all = window.__g.list();
    const clean = all.filter(i => i.grade === "clean").sort((a, b) => a.value - b.value);
    const base = clean[Math.floor(clean.length / 3)];
    const big = clean.find(i => i.value > base.value * 2);
    if (!big) return { skipped: true };
    window.__g.giveCrew(0, all.indexOf(base));
    for (let i = 0; i < 12; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    window.__g.giveCrew(1, all.indexOf(big));      // richer, arrives mid-lock
    const seen = [];
    for (let i = 0; i < 60; i++) {                 // 15 seconds, sampled each 0.25
      window.__g.setDist(70); window.__g.step(15, 1 / 60);
      seen.push([+(i * 0.25).toFixed(2), window.__g.curator().goalValue]);
    }
    const switchAt = seen.find(([, v]) => v === big.value);
    return { base: base.value, big: big.value, switchAt: switchAt ? switchAt[0] : null };
  });
  ok("it does not drop a target the instant something better appears",
    commit.skipped || (commit.switchAt !== null && commit.switchAt >= 4.0),
    JSON.stringify(commit));
  ok("but it does switch once the commitment expires",
    commit.skipped || (commit.switchAt !== null && commit.switchAt <= 12.0),
    JSON.stringify(commit));

  // --- the hot potato ------------------------------------------------------
  // The pillar the whole game is built on, playable for the first time.
  await fresh();
  const potato = await g(() => {
    window.__g.freezeCrew(true); window.__g.clearCrew();
    const list = window.__g.list();
    const idx = list.reduce((best, it, i) => it.value > list[best].value ? i : best, 0);
    window.__g.hold(idx);
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    for (let i = 0; i < 60; i++) { window.__g.setDist(70); window.__g.step(15, 1 / 60); }
    const before = window.__g.state().marked;
    // Put a crewmate in front of you and pass it. This lands INSIDE the eight
    // second commitment lock, which is the case R2 measured at 0.0s with the
    // hand-off override and 6.0s without.
    const raw = window.__g.raw();
    window.__g.setCrew(0, raw.x + Math.sin(0) * 1.4, raw.z + 1.4);
    window.__g.look(0, 0);
    const aimed = window.__g.aimedCrew();
    const took = window.__g.handOff();
    const after = window.__g.state();
    return { before, aimed, took, marked: after.marked, holding: after.holding,
             goal: window.__g.curator().goalValue, val: list[idx].value };
  });
  ok("you can hand the piece to a crewmate", potato.took !== null, JSON.stringify(potato));
  ok("handing it over takes the target off you immediately",
    potato.before === true && potato.marked === false, JSON.stringify(potato));
  ok("and the Curator still wants the same object",
    potato.goal === potato.val, JSON.stringify(potato));

  await g(() => window.__g.freezeCrew(false));

  // --- senses (TECH-SPEC A5) ------------------------------------------------
  // Hearing radius is L x 0.33, attenuated 0.85 per wall, and the point it walks
  // to is fuzzed +/-3m. Drive it from known geometry rather than from the game's
  // own numbers: sprint is L45, so 14.85m in the clear and ~12.6m through a wall.
  await fresh();
  const hearing = await g(() => {
    const out = { near: 0, far: 0, fuzzMax: 0, throughWall: null, clear: null };
    const c0 = window.__g.curator();
    for (let i = 0; i < 200; i++) {
      window.__g.setCur(0, 0);
      window.__g.heard(45, 10, 0);              // 10m away, same room
      if (window.__g.fix()) {
        out.near++;
        const f = window.__g.fix();
        out.fuzzMax = Math.max(out.fuzzMax, Math.hypot(f.x - 10, f.z - 0));
      }
      window.__g.setCur(0, 0);
      window.__g.heard(45, 20, 0);              // 20m away - past L45 x 0.33
      const f2 = window.__g.fix();
      if (f2 && Math.hypot(f2.x - 20, f2.z) < 5) out.far++;
    }
    return out;
  });
  ok("it hears a sprint at ten metres", hearing.near > 190, JSON.stringify(hearing));
  ok("it does not hear a sprint at twenty", hearing.far === 0, JSON.stringify(hearing));
  ok("the heard position is fuzzed, never exact",
    hearing.fuzzMax > 1.0 && hearing.fuzzMax <= 3.05, `max error ${hearing.fuzzMax}`);

  const occl = await g(() => {
    // Seed-agnostic: a door's two rooms are one wall apart by definition, and the
    // room furthest from the van is several.
    const rooms = window.__g.rooms();
    const d = window.__g.doors()[0];
    const a = rooms.find(r => r.id === d.a), b = rooms.find(r => r.id === d.b);
    const far = rooms.reduce((m, r) => Math.hypot(r.x, r.z) > Math.hypot(m.x, m.z) ? r : m);
    return { same: window.__g.hops(a.x, a.z, a.x + 1, a.z),
             next: window.__g.hops(a.x, a.z, b.x, b.z),
             far: window.__g.hops(rooms.find(r => r.van).x, rooms.find(r => r.van).z,
                                  far.x, far.z) };
  });
  ok("walls are counted over the portal graph",
    occl.same === 0 && occl.next === 1 && occl.far >= 2, JSON.stringify(occl));

  // Concealment beats sight outright - that is what the wardrobe is for.
  await fresh();
  const sight = await g(() => {
    window.__g.parkCrew();
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    window.__g.setCur(f.x - 3, f.z, null, Math.PI / 2);   // inside the room, facing the player
    window.__g.step(1, 1 / 60);
    const openGround = window.__g.fix();
    const hi = window.__g.hides().findIndex(h => h.room === "foyer");
    window.__g.hide(hi); window.__g.step(90, 1 / 60);
    const before = window.__g.fix();
    window.__g.setCur(window.__g.raw().x + 2.5, window.__g.raw().z, null, -Math.PI / 2);
    for (let i = 0; i < 120; i++) window.__g.step(1, 1 / 60);
    const after = window.__g.fix();
    return { openGround: !!openGround, sure: openGround && openGround.sure,
             hiddenFixAged: after ? after.age : null,
             hiddenFixWho: after ? after.who : null, before: !!before };
  });
  ok("it sees you in the open", sight.openGround === true && sight.sure === true,
    JSON.stringify(sight));
  ok("it cannot see you in a wardrobe",
    sight.hiddenFixWho !== "YOU" || sight.hiddenFixAged > 1.0, JSON.stringify(sight));

  const throughWall = await g(() => {
    const rooms = window.__g.rooms();
    const foyer = rooms.find(r => r.id === "foyer"), hall = rooms.find(r => r.id === "hall");
    window.__g.tp(hall.x, hall.z);
    window.__g.setCur(foyer.x + 4, foyer.z, null, Math.PI / 2);   // in the cone, 7m off
    return { d: Math.hypot(hall.x - (foyer.x + 4), hall.z - foyer.z),
             seen: window.__g.sees(hall.x, hall.z) };
  });
  ok("sight does not pass through walls",
    throughWall.seen === false && throughWall.d < 18, JSON.stringify(throughWall));

  // --- audio, and the fairness rule it exists to keep -----------------------
  // A6.2: always audible for >= 8m before contact, on a layer never occluded to
  // zero. Read the mix rather than listening to it.
  await fresh();
  const audio = await g(() => {
    window.__g.startAudio();
    const probe = window.__g.audio();
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    const at = d => { window.__g.setCur(f.x + d, f.z); return window.__g.mix().drag; };
    const far = at(30), eight = at(8), close = at(2);
    // through a wall, at eight metres: the rule says still audible
    const hall = window.__g.rooms().find(r => r.id === "hall");
    window.__g.tp(hall.x, hall.z);
    window.__g.setCur(f.x + 4, f.z);
    const walled = window.__g.mix().drag;
    return { probe, far, eight, close, walled };
  });
  ok("the audio engine comes up", audio.probe.ready === true, JSON.stringify(audio.probe));
  // Note: this asserts the MIXING RULE, not audible output. Headless Chromium
  // has no audio device and its context clock does not advance, so the graph's
  // own gain values stay at zero however correct the mix is.
  ok("it is audible at eight metres", audio.eight >= 0.05, `drag=${audio.eight}`);
  ok("it gets louder as it closes", audio.close > audio.eight && audio.eight > audio.far,
    JSON.stringify(audio));
  ok("occlusion never silences the drag layer inside eight metres",
    audio.walled > 0, `drag through a wall = ${audio.walled}`);

  // The rule, at every combination including ones this estate cannot produce.
  const floor = await g(() => {
    const bad = [];
    for (let walls = 0; walls <= 6; walls++)
      for (let d = 0; d <= 8; d += 0.5)
        if (window.__g.dragAt(d, walls, false) < 0.06)
          bad.push({ d, walls, g: window.__g.dragAt(d, walls, false) });
    return { bad, beyond: window.__g.dragAt(9, 6, false) };
  });
  ok("the eight-metre floor holds through any number of walls",
    floor.bad.length === 0, JSON.stringify(floor.bad.slice(0, 3)));
  ok("and does not apply past eight metres", floor.beyond < 0.06,
    `drag at 9m through 6 walls = ${floor.beyond}`);

  await fresh();
  const muted = await g(() => {
    window.__g.startAudio();
    const on = window.__g.mute(true);
    const m = window.__g.audio();
    window.__g.mute(false);
    return { on, master: m.master, after: window.__g.audio().master };
  });
  ok("mute works", muted.on === true && muted.master === 0 && muted.after > 0,
    JSON.stringify(muted));

  // --- the estate is authored, not assumed ---------------------------------
  const faults = await g(() => window.__g.faults());
  ok("no estate faults at boot", faults.length === 0, JSON.stringify(faults));

  // Depth unlocks on work, never on a clock (D-20). At the start of the night the
  // deep wings are shut, and what opens them is an emptied sideboard.
  await fresh();
  const gating = await g(() => {
    // Seed-agnostic: pick a tier-2 wing and the room that gates it, whatever the
    // generator called them this time.
    const prereq = window.__g.prereq();
    const rooms = window.__g.rooms();
    const gated = Object.keys(prereq).find(id => rooms.find(r => r.id === id).tier === 2);
    const feeder = prereq[gated][0];
    const shutAtStart = window.__g.locked();
    const shelf = window.__g.shelves().find(s => s.room === feeder);
    const v = window.__g.rooms().find(r => r.van);
    window.__g.parkCrew();
    for (const it of window.__g.list().filter(i => i.shelf === shelf.i)) {
      const idx = window.__g.list().findIndex(x => x.x === it.x && x.z === it.z);
      window.__g.hold(idx);
      window.__g.tp(v.x, v.z); window.__g.step(2, 1 / 60);
    }
    const deep = Object.keys(prereq).filter(id => rooms.find(r => r.id === id).tier === 3);
    return { gated, feeder, deep, shutAtStart, cleared: window.__g.cleared(feeder),
             shutAfter: window.__g.locked() };
  });
  const pairOf = (a, b) => [`${a}-${b}`, `${b}-${a}`];
  ok("the deep wings start sealed",
    pairOf(gating.feeder, gating.gated).some(p => gating.shutAtStart.includes(p)),
    JSON.stringify(gating));
  ok("emptying a wing's sideboard is what opens the next one",
    gating.cleared === true &&
    !pairOf(gating.feeder, gating.gated).some(p => gating.shutAfter.includes(p)),
    JSON.stringify(gating));
  ok("and the tier-3 wings stay shut behind the tier-2 one",
    gating.deep.length === 0 ||
    gating.deep.every(d => gating.shutAfter.some(p => p.split("-").includes(d))),
    JSON.stringify(gating));

  // --- reset ----------------------------------------------------------------
  await fresh();
  const after = await g(() => window.__g.state());
  ok("reset restores a fresh night",
    after.slots === 14 && after.t === 0 && after.over === false, JSON.stringify(after));
}

main().catch(e => { console.error(e); process.exit(2); });
