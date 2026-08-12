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
})();`;

const pageErrors = [];

async function main() {
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
  const fresh = () => page.evaluate(() => { window.__g.clearKeys(); window.__g.reset(); });
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

  ok("no page errors", pageErrors.length === 0, pageErrors.join(" | "));
  await browser.close();

  console.log(`PROTO3D QA  -  ${passed + failures.length} checks`);
  console.log("-".repeat(74));
  if (!failures.length) { console.log("  OK   the prototype behaves as specified"); process.exit(0); }
  for (const f of failures) console.log(`  FAIL  ${f}`);
  console.log(`\n${failures.length} failing check(s).`);
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
  const sweep = await g(() => {
    const bad = [], tries = [];
    for (let i = 1; i <= 120; i++) {
      const r = window.__g.regen(i * 104729);
      tries.push(window.__g.seed().tries);
      if (r.faults.length) bad.push({ seed: r.seed, faults: r.faults.slice(0, 2) });
    }
    tries.sort((a, b) => a - b);
    return { bad, median: tries[60], worst: tries[tries.length - 1] };
  });
  ok("every seed produces an estate that passes the gate",
    sweep.bad.length === 0, JSON.stringify(sweep.bad.slice(0, 3)));
  ok("and it does not take many attempts to find one",
    sweep.median <= 12 && sweep.worst < 60,
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
        window.__g.newContract(); window.__g.regen((trial + 1) * 104729 + n);
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
        window.__g.newContract(); window.__g.regen((t + 1) * 104729);
        for (let i = 0; i < 210 * 60 && !window.__g.state().over; i++) window.__g.step(1, 1 / 60);
        const l = window.__g.contract().last;
        cursed += l.cursed; net += l.net;
      }
      return { cap, cursed: +(cursed / n).toFixed(2), net: Math.round(net / n) };
    };
    const strict = run(1), normal = run(3), none = run(0);
    window.__g.curseCap(3);
    window.__g.newContract(); window.__g.regen(20260806);
    return { strict, normal, none };
  });
  ok("the crew honour the cursed-cargo cap",
    curse.strict.cursed <= 1.05, JSON.stringify(curse));
  ok("and refusing cursed cargo outright costs real money",
    curse.none.net < curse.normal.net * 0.85, JSON.stringify(curse));

  // ECONOMY 4's description of the last night: "above the mean. The apex is not
  // optional." Bots alone should mostly miss it; the apex should turn it around.
  const lastNight = await g(() => {
    window.__g.freezeCrew(false);
    let bots = 0, withApex = 0, runs = 12;
    const apexValue = [];
    for (let t = 0; t < runs; t++) {
      window.__g.newContract(); window.__g.regen((t + 1) * 104729 + 3, 3);
      window.__g.setNight(3);
      const a = window.__g.apex(); if (a) apexValue.push(a.value);
      for (let i = 0; i < 210 * 60 && !window.__g.state().over; i++) window.__g.step(1, 1 / 60);
      const l = window.__g.contract().last;
      if (l.met) bots++;
      if (l.net + (a ? a.value : 0) >= l.quota) withApex++;
    }
    window.__g.newContract(); window.__g.regen(20260806);
    return { bots: bots / runs, withApex: withApex / runs,
             apex: Math.round(apexValue.reduce((s, v) => s + v, 0) / apexValue.length) };
  });
  ok("the last night is not passable on crew throughput alone",
    lastNight.bots <= 0.6, JSON.stringify(lastNight));
  ok("but the apex turns it around",
    lastNight.withApex >= lastNight.bots + 0.15, JSON.stringify(lastNight));

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

  await g(() => { window.__g.newContract(); window.__g.regen(20260806); });

  // --- the apex (ECONOMY 3, D-21) -------------------------------------------
  // The thing the last night is built around: one per estate, only in late
  // contracts, five of the van's slots, and it takes two people to move.
  const apex = await g(() => {
    const out = { early: [], late: [], haul: null };
    for (const n of [0, 1]) {
      window.__g.newContract(); window.__g.regen(4242 + n, n); window.__g.setNight(n);
      out.early.push(window.__g.apex());
    }
    for (const n of [2, 3]) {
      window.__g.newContract(); window.__g.regen(4242 + n, n); window.__g.setNight(n);
      out.late.push(window.__g.apex());
    }
    // Haul it: crewmate alongside, lift, walk it to the van.
    window.__g.newContract(); window.__g.regen(4242, 3); window.__g.setNight(3);
    window.__g.gates(true); window.__g.freezeCrew(true);
    const a = window.__g.apex(), it = window.__g.list()[a.i];
    window.__g.setCrew(0, it.x + 1.0, it.z);
    window.__g.tp(it.x - 1.3, it.z);
    window.__g.look(Math.PI / 2, -Math.atan2(1.62 - it.y, 1.3));
    window.__g.grab();
    const alone = window.__g.carry();
    const v = window.__g.rooms().find(r => r.van);
    const before = window.__g.vanSlots();
    window.__g.tp(v.x, v.z); window.__g.step(4, 1 / 60);
    out.haul = { carry: alone, slots: before - window.__g.vanSlots(),
                 banked: window.__g.state().banked, value: a.value };
    window.__g.gates(false); window.__g.freezeCrew(false);
    window.__g.newContract(); window.__g.regen(20260806);
    return out;
  });
  ok("early contract nights have no apex",
    apex.early.every(a => a === null), JSON.stringify(apex.early));
  ok("late ones always do", apex.late.every(a => a && a.tier === 4),
    JSON.stringify(apex.late));
  ok("it takes two people and five slots",
    apex.haul.carry !== null && apex.haul.carry.follower !== null && apex.haul.slots === 5,
    JSON.stringify(apex.haul));
  ok("and it is worth a third to two thirds of the night it decides",
    apex.late.every(a => a.value >= 2900 * 0.30 && a.value <= 3300 * 0.68),
    JSON.stringify(apex.late.map(a => a.value)));

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
  ok("second contact is fatal", second.over === true && second.why === "COLLECTED",
    JSON.stringify(second));

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
