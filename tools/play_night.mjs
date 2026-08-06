// Play whole nights in the real prototype under a named policy.
//
// R22 measured, in Python, that judging each item on the margin beats hauling
// blind. That claim has never been tested against the code anyone will actually
// play. This drives proto3d itself - real loop, real Disturbance, real Curator,
// real clock - under BLIND, VALUE_p and MARGIN_p, and prints what each policy
// banks.
//
//   node tools/play_night.mjs [runs]      ->  JSON on stdout, table on stderr
//
// NAVIGATION, AND WHAT IS FAKE ABOUT IT. The bot walks the room graph through
// doorway centres at the game's own speeds, advancing its position along that
// path each frame - it does not solve collision, it follows a route that avoids
// walls by construction. Everything else is the real thing: the clock runs, the
// keys are held so stamina and sprint noise behave normally, the Curator hunts,
// items are appraised through the same three-second scan. What this cannot
// catch is a bug in movement or collision. What it can catch is an economy that
// works in Python and not in the game.

import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const RUNS = Number(process.argv[2] || 12);
const POLICIES = ["BLIND", "VALUE_70", "MARGIN_30", "MARGIN_50"];

const browser = await chromium.launch(
  process.env.PW_CHROME ? { executablePath: process.env.PW_CHROME } : {});
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto("file://" + resolve(ROOT, "proto3d/index.html"));
await page.waitForFunction(() => !!window.__g);

const results = await page.evaluate(({ runs, policies }) => {
  const DT = 1 / 60;
  const g = window.__g;

  // Deterministic runs. The prototype uses Math.random everywhere; seeding it
  // is the only way one policy's night is comparable to another's.
  const seedRandom = (seed) => {
    let s = (seed * 2654435761) >>> 0;
    Math.random = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  };

  const roomOf = (x, z) => ROOMS.find((r) => inRoom(r, x, z));
  const doorBetween = (a, b) =>
    DOORS.find((d) => (d.a === a && d.b === b) || (d.a === b && d.b === a));

  const routeRooms = (from, to) => {
    const prev = { [from]: null };
    const q = [from];
    while (q.length) {
      const cur = q.shift();
      if (cur === to) break;
      for (const [a, b] of LINKS) {
        for (const [x, y] of [[a, b], [b, a]]) {
          if (x === cur && !(y in prev)) { prev[y] = cur; q.push(y); }
        }
      }
    }
    if (!(to in prev)) return null;
    const out = [];
    for (let r = to; r; r = prev[r]) out.unshift(r);
    return out;
  };

  // Waypoints: doorway centres along the route, then the destination point.
  const waypoints = (tx, tz) => {
    const here = roomOf(player.x, player.z);
    const there = roomOf(tx, tz);
    if (!here || !there) return [[tx, tz]];
    const rooms = routeRooms(here.id, there.id) || [here.id];
    const pts = [];
    for (let i = 0; i < rooms.length - 1; i++) {
      const d = doorBetween(rooms[i], rooms[i + 1]);
      if (d) pts.push([d.x, d.z]);
    }
    pts.push([tx, tz]);
    return pts;
  };

  // Walk to a point, stepping the real loop every frame. Returns false if the
  // night ended on the way.
  const walkTo = (tx, tz, budgetS = 40) => {
    let spent = 0;
    for (const [wx, wz] of waypoints(tx, tz)) {
      let guard = 0;
      while (Math.hypot(wx - player.x, wz - player.z) > 0.35) {
        if (g.state().over || spent > budgetS) return false;
        const speed = player.holding ? CARRY : WALK;
        const dx = wx - player.x, dz = wz - player.z;
        const len = Math.hypot(dx, dz) || 1;
        const stepLen = Math.min(speed * DT, len);
        player.x += (dx / len) * stepLen;
        player.z += (dz / len) * stepLen;
        player.yaw = Math.atan2(dx, dz);
        g.press("KeyW", true);          // so stamina and noise behave normally
        g.step(1, DT);
        g.press("KeyW", false);
        spent += DT;
        if (++guard > 60 * 40) return false;
      }
    }
    return !g.state().over;
  };

  // Aim at it properly. Items sit at knee height and the camera is at 1.62m,
  // so standing on top of one and looking level misses the aim cone entirely -
  // which is how the first version of this bot had BLIND banking 1.6 items a
  // night while visiting 26 shelves.
  const aimAt = (it) => {
    const back = 1.6;
    const dx = player.x - it.x, dz = player.z - it.z;
    const len = Math.hypot(dx, dz) || 1;
    player.x = it.x + (dx / len) * back;
    player.z = it.z + (dz / len) * back;
    player.yaw = Math.atan2(it.x - player.x, it.z - player.z);
    player.pitch = Math.atan2(it.y - EYE, back);
  };

  const appraise = (it) => {
    aimAt(it);
    g.press("KeyF", true);
    for (let i = 0; i < Math.ceil((APPRAISE_S + 0.2) * 60); i++) {
      g.step(1, DT);
      if (g.state().over) break;
    }
    g.press("KeyF", false);
    return it.known;
  };

  const ruinAt = (n) => (n <= 0 ? 0 : Math.min(0.95, RUIN_K * Math.pow(n, RUIN_EXP)));

  // Should we spend a slot on this? BLIND never asks. VALUE_p asks about the
  // sticker price. MARGIN_p asks what the piece ADDS, which is the R22 rule.
  const wants = (policy, it) => {
    if (policy === "BLIND") return true;
    const [lo, hi] = BAND[it.tier];
    const pct = Number(policy.split("_")[1]) / 100;
    const bar = lo + (hi - lo) * pct;
    if (policy.startsWith("VALUE_")) return it.value >= bar;
    const n = van.cargo.filter((c) => c.grade !== "clean").length;
    const next = n + (it.grade === "clean" ? 0 : 1);
    const gross = van.cargo.reduce((s, c) => s + c.value, 0);
    const margin = it.value * (1 - FEE[it.grade]) * (1 - ruinAt(next))
                 - gross * (ruinAt(next) - ruinAt(n));
    return margin >= bar;
  };

  const out = {};
  for (const policy of policies) {
    const nights = [];
    for (let run = 0; run < runs; run++) {
      seedRandom(run + 1);
      g.reset();
      let visited = 0;
      while (!g.state().over && van.slots > 0) {
        // Nearest item we have not already dealt with.
        const live = items.filter((i) => !i.gone && !i.held && !i.refused);
        if (!live.length) break;
        live.sort((a, b) => Math.hypot(a.x - player.x, a.z - player.z)
                          - Math.hypot(b.x - player.x, b.z - player.z));
        const it = live[0];
        if (!walkTo(it.x, it.z)) break;
        visited++;
        aimAt(it);
        if (policy !== "BLIND") {
          appraise(it);
          if (!wants(policy, it)) { g.leave(); continue; }
        }
        g.grab();
        if (!player.holding) { it.refused = true; continue; }
        const van_ = ROOMS.find((r) => r.van);
        if (!walkTo(van_.x, van_.z, 60)) break;
        g.step(3, DT);          // the van deposits on the next tick inside it
      }
      const s = g.state();
      const cursed = van.cargo.filter((c) => c.grade !== "clean").length;
      const gross = van.cargo.reduce((a, c) => a + c.value, 0);
      const fees = van.cargo.reduce((a, c) => a + c.value * FEE[c.grade], 0);
      const ruined = Math.random() < ruinAt(cursed);
      nights.push({
        net: ruined ? 0 : Math.round(gross - fees),
        items: van.cargo.length, cursed, ruined,
        appraised: g.stats().appraised, refused: g.stats().refused,
        dist: s.dist, visited, t: s.t,
      });
    }
    const mean = (f) => nights.reduce((a, n) => a + f(n), 0) / nights.length;
    out[policy] = {
      net: Math.round(mean((n) => n.net)), items: +mean((n) => n.items).toFixed(1),
      cursed: +mean((n) => n.cursed).toFixed(1),
      ruined: +mean((n) => (n.ruined ? 1 : 0)).toFixed(2),
      appraised: +mean((n) => n.appraised).toFixed(1),
      refused: +mean((n) => n.refused).toFixed(1),
      visited: +mean((n) => n.visited).toFixed(1),
    };
  }
  return out;
}, { runs: RUNS, policies: POLICIES });

await browser.close();

const pad = (s, n) => String(s).padStart(n);
console.error(`\nPLAYED NIGHTS  -  ${RUNS} seeded runs per policy, in the real prototype`);
console.error("-".repeat(78));
console.error("policy        net $   items  cursed  ruined  appraised  refused  shelves");
for (const [p, r] of Object.entries(results)) {
  console.error(`${p.padEnd(12)}${pad(r.net.toLocaleString(), 7)}${pad(r.items, 8)}`
    + `${pad(r.cursed, 8)}${pad(r.ruined, 8)}${pad(r.appraised, 11)}`
    + `${pad(r.refused, 9)}${pad(r.visited, 9)}`);
}
if (errors.length) console.error("\npage errors: " + errors.slice(0, 3).join(" | "));
console.log(JSON.stringify(results));
process.exit(errors.length ? 1 : 0);
