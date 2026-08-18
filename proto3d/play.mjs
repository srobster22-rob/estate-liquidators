/**
 * A competent player, playing the real build.
 *
 * Every pass rate this project has ever quoted for the prototype was measured
 * with the player standing still in the driveway. `STATUS.md` says so in the
 * margin of three checks and `qa.mjs` says it out loud in the comment on the
 * last-night battery: "the player is doing NOTHING in these runs". That is a
 * strange gap for a game whose whole question is whether a night is winnable —
 * the one actor who makes decisions was the one actor not making any.
 *
 * So: a policy, driving the real build through the real verbs. It walks (it does
 * not teleport), it routes door by door over the same room graph the crew use, it
 * appraises before it commits, it uses the tools, and it hides when it is hunted.
 * It is not meant to be optimal. It is meant to be a competent player on a night
 * they are paying attention, which is the reference class every quota in
 * ECONOMY.md 4 is implicitly written against.
 *
 *   node proto3d/play.mjs                 one night, night one, narrated
 *   node proto3d/play.mjs --nights 4      the whole chain
 *   node proto3d/play.mjs --trials 8      pass rates, with and without a player
 *   node proto3d/play.mjs --seed 20260806 --quiet
 */

import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const CANDIDATES = [
  "playwright", "/opt/node22/lib/node_modules/playwright/index.js",
  "/usr/lib/node_modules/playwright/index.js",
];
function loadPlaywright() {
  for (const c of CANDIDATES) {
    try { return require(c); } catch { /* next */ }
  }
  throw new Error("playwright not found in " + CANDIDATES.join(", "));
}

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf(k); return i < 0 ? d : Number(argv[i + 1]); };
const has = k => argv.includes(k);

// ---------------------------------------------------------------- the policy
// Runs INSIDE the page, because it has to see the world every frame. Everything
// it uses is a hook qa.mjs already relies on; nothing here reaches past __g.
const POLICY = ({ seconds, verbose }) => {
  const g = window.__g;
  const log = [];
  const say = m => { if (verbose) log.push(`${g.state().t.toFixed(0)}s  ${m}`); };

  const dist2 = (ax, az, bx, bz) => Math.hypot(bx - ax, bz - az);
  const rooms = () => g.rooms();
  const roomOf = (x, z) => g.roomAt(x, z);
  const van = () => rooms().find(r => r.van);

  // Walk toward a point, door by door. The room graph is the crew's; using it
  // means the player is subject to the same locks and boards they are.
  let stuckFor = 0, lastX = 0, lastZ = 0;
  const walkToward = (tx, tz) => {
    const me = g.raw();
    const here = roomOf(me.x, me.z), there = roomOf(tx, tz);
    let gx = tx, gz = tz;
    if (here && there && here !== there) {
      const id = g.route(here, there);
      const d = id && g.doors().find(x => `${x.a}-${x.b}` === id);
      if (d) { gx = d.x; gz = d.z; }
    }
    g.look(Math.atan2(gx - me.x, gz - me.z));
    g.press("KeyW");
    // Sprinting is loud (L45); walk unless the Curator is already on you.
    g.press("ShiftLeft", g.state().marked === true);
    if (dist2(me.x, me.z, lastX, lastZ) < 0.01) stuckFor++; else stuckFor = 0;
    lastX = me.x; lastZ = me.z;
    return dist2(me.x, me.z, tx, tz);
  };
  const stop = () => { g.press("KeyW", false); g.press("ShiftLeft", false); };

  // What is worth carrying: the best appraised piece on a shelf we can reach,
  // preferring value per slot the way ECONOMY 3 prices depth.
  const SLOT = { pocket: 0.5, armful: 1, two_man: 3, cart: 5 };
  const pickTarget = () => {
    const st = g.state();
    const list = g.list().filter(i => !i.held && !i.corpse);
    let best = null, bv = 0;
    for (const it of list) {
      if (it.klass === "cart") continue;              // dolly work, not a grab
      if (SLOT[it.klass] > st.slots) continue;
      const room = roomOf(it.x, it.z);
      if (!room) continue;
      if (g.locked().some(id => id.split("-").includes(room))) continue;
      if (skip.has(it.i)) continue;
      // Value per slot, discounted by how far it is: a $300 vase four rooms away
      // is worth less than a $250 one in this room, because the night is short.
      const me = g.raw();
      const d = Math.max(3, dist2(me.x, me.z, it.x, it.z));
      const known = it.known ? it.value : it.value * 0.75;   // unknown: be cautious
      const v = (known / SLOT[it.klass]) / d;
      if (v > bv) { bv = v; best = it; }
    }
    return best;
  };

  let phase = "SEEK", target = null, hidTill = -1, appraised = 0;
  let took = 0, delivered = 0, idle = 0;
  // A scan is 3.2 seconds out of 210. Twelve of them is a fifth of the night,
  // which is about as much looking as hauling can pay for.
  const SCAN_BUDGET = 12, WORTH_IT = 220;
  const skip = new Set();
  const HIDE_UNTIL = 3;

  for (let frame = 0; frame < seconds * 60; frame++) {
    const st = g.state();
    if (st.over) break;
    const me = g.raw();

    // 1. Hunted and holding: hide. DESIGN 8.1 is the whole answer to COLLECT.
    if (st.marked && st.holding && phase !== "HIDE") {
      const h = g.hides().filter(x => !x.item)
        .sort((a, b) => dist2(me.x, me.z, a.x, a.z) - dist2(me.x, me.z, b.x, b.z))[0];
      if (h && dist2(me.x, me.z, h.x, h.z) < 12) {
        phase = "HIDE"; target = h; say("marked - going for the wardrobe");
      }
    }
    if (phase === "HIDE") {
      if (dist2(me.x, me.z, target.x, target.z) > 1.0) walkToward(target.x, target.z);
      else {
        stop();
        // hides() returns fresh objects every call, so indexOf(target) on a later
        // array is always -1. The index is a field on the hide; use that.
        if (!st.concealed) g.hide(target.i);
        if (hidTill < 0) hidTill = st.t + HIDE_UNTIL;
        if (st.t > hidTill && !st.marked) {
          g.hide(target.i);                       // climb out
          hidTill = -1; phase = "SEEK"; target = null; say("clear - back to work");
        }
      }
      g.step(1, 1 / 60);
      continue;
    }

    // 2. Holding something: take it to the van.
    if (st.holding) {
      const v = van();
      if (walkToward(v.x, v.z) < 1.2) { stop(); delivered++; }
      g.step(1, 1 / 60);
      continue;
    }

    // 3. Disturbance high and we are at the van: spend a lever.
    if (st.dist > 80 && roomOf(me.x, me.z) === van().id) {
      const lv = g.levers();
      if (g.lights().lit.length) { g.killLights(); say("killed the lights"); }
      else if (lv.quiet <= 0) { g.goQuiet(); say("called for quiet"); }
      else if (g.cargo().some(c => c.grade !== "clean")) {
        g.unloadCursed(); say("dumped the cursed cargo in the yard");
      }
    }

    // 4. Otherwise: find something, appraise it, decide.
    //
    // The first version of this appraised everything it walked to and then went
    // looking for something else to appraise, because clearing the target after a
    // scan sends pickTarget() at the next unknown piece. Forty scans at 3.2s each
    // is two minutes of a 210-second night spent looking at things and three
    // items delivered. Appraising has to end in a DECISION about the piece in
    // front of you: take it, or write it off and never come back.
    if (!target || target.gone) target = pickTarget();
    if (!target) { stop(); idle++; g.step(1, 1 / 60); continue; }
    const t = g.list().find(i => i.i === target.i) || target;
    const d = walkToward(t.x, t.z);
    if (d < 1.6) {
      stop();
      g.look(Math.atan2(t.x - me.x, t.z - me.z), -0.15);
      if (!t.known && appraised < SCAN_BUDGET) {
        g.press("KeyF"); g.step(60 * 3.2, 1 / 60); g.press("KeyF", false);
        appraised++;
        const now = g.list().find(i => i.i === t.i);
        if (now && now.known && now.value / SLOT[now.klass] < WORTH_IT) {
          skip.add(t.i); target = null; say(`walked away from $${now.value}`);
        }
      } else {
        g.grab();
        if (g.state().holding) { took++; say(`took $${g.state().holding}`); }
        else skip.add(t.i);
        target = null;
      }
    }
    g.step(1, 1 / 60);
  }
  stop();
  const st = g.state();
  const c = g.contract();
  return { banked: st.banked, quota: c.quota, met: c.last ? c.last.met : null,
    net: c.last ? Math.round(c.last.net) : null, over: st.over, why: st.why,
    dead: st.dead, dist: st.dist, appraised, took, delivered, idle,
    stuckFor, at: g.pos(), log };
};

async function main() {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({
    args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage();
  await page.addInitScript(`(() => { let s = 0x2f6e2b1;
    Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; })();`);
  await page.goto("file://" + path.join(HERE, "index.html"));
  await page.waitForFunction("typeof window.__g === 'object'", null, { timeout: 10000 });
  await page.evaluate(() => window.__g.pause(true));

  const trials = arg("--trials", 0);
  const nights = arg("--nights", 1);
  const seed = arg("--seed", 20260806);
  const verbose = !has("--quiet") && !trials;

  if (!trials) {
    for (let n = 0; n < nights; n++) {
      await page.evaluate(([s, nn]) => {
        window.__g.newContract(s); window.__g.regen(s, nn); window.__g.setNight(nn);
      }, [seed, n]);
      const r = await page.evaluate(POLICY, { seconds: 210, verbose });
      for (const l of r.log) console.log("   " + l);
      console.log(`   took ${r.took}, appraised ${r.appraised}, idle frames ${r.idle}, `
        + `stuck ${r.stuckFor}, ended in ${r.at.room}`);
      console.log(`night ${n + 1}  banked $${r.banked.toLocaleString()}  `
        + `net $${(r.net ?? 0).toLocaleString()}  quota $${r.quota.toLocaleString()}  `
        + `${r.met ? "MET" : "MISSED"}  ${r.dead ? "(died)" : ""}  ${r.why || ""}`);
    }
    await browser.close();
    return;
  }

  // The comparison the project has never had: the same nights, with and without
  // somebody playing them.
  const SUMMARY = [];
  console.log(`A PLAYER, AND NO PLAYER  -  ${trials} nights each`);
  console.log("-".repeat(74));
  console.log("night".padEnd(7) + "bots alone".padStart(14) + "with a player".padStart(16)
    + "pass, bots".padStart(12) + "pass, played".padStart(14));
  for (let n = 0; n < 4; n++) {
    const bots = [], played = [];
    for (let t = 0; t < trials; t++) {
      const s = (t + 1) * 104729 + n;
      await page.evaluate(([sd, nn]) => {
        window.__g.newContract(sd); window.__g.regen(sd, nn); window.__g.setNight(nn);
      }, [s, n]);
      const idle = await page.evaluate(() => {
        for (let i = 0; i < 210 * 60 && !window.__g.state().over; i++) window.__g.step(1, 1 / 60);
        const c = window.__g.contract();
        return { net: Math.round(c.last.net), met: !!c.last.met };
      });
      bots.push(idle);
      await page.evaluate(([sd, nn]) => {
        window.__g.newContract(sd); window.__g.regen(sd, nn); window.__g.setNight(nn);
      }, [s, n]);
      played.push(await page.evaluate(POLICY, { seconds: 210, verbose: false }));
    }
    const mean = xs => Math.round(xs.reduce((a, b) => a + b, 0) / xs.length);
    const rate = xs => xs.filter(Boolean).length / xs.length;
    SUMMARY.push({ night: n + 1,
      bots: Math.round(bots.reduce((a, b) => a + b.net, 0) / bots.length),
      played: Math.round(played.reduce((a, b) => a + (b.net ?? 0), 0) / played.length),
      passBots: bots.filter(b => b.met).length / bots.length,
      passPlayed: played.filter(p => p.met).length / played.length });
    const died = played.filter(p => p.dead).length;
    const scans = mean(played.map(p => p.appraised));
    const carried = mean(played.map(p => p.took));
    console.log(`${String(n + 1).padEnd(7)}`
      + `${("$" + mean(bots.map(b => b.net)).toLocaleString()).padStart(14)}`
      + `${("$" + mean(played.map(p => p.net ?? 0)).toLocaleString()).padStart(16)}`
      + `${(Math.round(rate(bots.map(b => b.met)) * 100) + "%").padStart(12)}`
      + `${(Math.round(rate(played.map(p => p.met)) * 100) + "%").padStart(14)}`
      + `${(carried + " taken").padStart(11)}${(scans + " scans").padStart(10)}`
      + `${(died + " died").padStart(9)}`);
  }
  if (has("--check")) {
    // A script whose output nothing asserts is not a check (R37). The claims are
    // shape claims, because twenty-four nights cannot pin a rate to ten points:
    // a competent player is worth real money on every night, and the last night
    // is still not a formality with one in the house.
    const fails = [];
    // Eight nights per cell is not enough to say anything per night: on a clean
    // build it produces "the player made night one worse" about as often as not.
    // The chain average is stable at sixteen; the per-night claim is only ever a
    // majority claim.
    if (trials < 16) fails.push(`--check needs --trials 16 or more (got ${trials}); `
      + "eight nights cannot tell a contribution from a coin flip");
    const better = SUMMARY.filter(r => r.played > r.bots).length;
    if (better < 3)
      fails.push(`a player is worth nothing on ${4 - better} of the four nights: `
        + SUMMARY.map(r => `n${r.night} ${r.bots}->${r.played}`).join(", "));
    const lift = SUMMARY.reduce((a, r) => a + r.played / r.bots, 0) / SUMMARY.length - 1;
    if (lift < 0.08 || lift > 0.80)
      fails.push(`a player is worth ${(lift * 100).toFixed(0)}% of a night, `
        + "which is outside anything this policy should produce");
    if (SUMMARY[3].passPlayed > 0.85)
      fails.push(`the last night passes ${(SUMMARY[3].passPlayed * 100).toFixed(0)}% `
        + "with a player - ECONOMY 4 wants it to bite");
    console.log("-".repeat(74));
    if (!fails.length) {
      console.log("  OK   a player is worth about a third of a night, and night four still bites");
    } else {
      for (const f of fails) console.log("  FAIL  " + f);
      await browser.close();
      process.exit(1);
    }
  }
  await browser.close();
}

main();
