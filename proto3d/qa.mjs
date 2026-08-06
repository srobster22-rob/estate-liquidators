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

  const g = (fn, arg) => page.evaluate(fn, arg);   // run in page, return JSON
  const fresh = () => page.evaluate(() => { window.__g.clearKeys(); window.__g.reset(); });

  await checks(g, fresh);

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

  // --- the R12 bug: sustained noise must be per second, not per frame --------
  // Same ten seconds of sprinting at two timestep sizes must cost the same.
  const sprintAt = async dt => {
    await fresh();
    return g(([dt]) => {
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
  await fresh();
  const empty = await g(() => {
    window.__g.setDist(95);                   // COLLECT, the hungriest tier
    for (let i = 0; i < 60; i++) window.__g.step(30, 1 / 60);   // 30 seconds
    return { st: window.__g.state(), cur: window.__g.curator() };
  });
  ok("empty-handed player is never targeted",
    empty.st.marked === false && empty.cur.target === false, JSON.stringify(empty));

  // --- aggro follows the loot ----------------------------------------------
  await fresh();
  const carrying = await g(() => {
    const f = window.__g.rooms().find(r => r.id === "foyer");
    window.__g.tp(f.x, f.z);
    window.__g.setDist(95);
    window.__g.hold(0);
    for (let i = 0; i < 20; i++) window.__g.step(30, 1 / 60);
    return window.__g.state();
  });
  ok("carrying loot at COLLECT draws the Curator", carrying.marked === true,
    JSON.stringify(carrying));

  // --- dropping is loud -----------------------------------------------------
  await fresh();
  const drop = await g(() => {
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
    const v = window.__g.rooms().find(r => r.id === "drive");
    for (let i = 0; i < 14; i++) {
      if (window.__g.state().over) break;
      window.__g.hold(0); window.__g.tp(v.x, v.z); window.__g.step(2, 1 / 60);
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

  // --- the estate is authored, not assumed ---------------------------------
  const faults = await g(() => window.__g.faults());
  ok("every doorway fits its door", faults.length === 0, JSON.stringify(faults));

  // --- reset ----------------------------------------------------------------
  await fresh();
  const after = await g(() => window.__g.state());
  ok("reset restores a fresh night",
    after.slots === 14 && after.t === 0 && after.over === false, JSON.stringify(after));
}

main().catch(e => { console.error(e); process.exit(2); });
