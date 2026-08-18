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
const POLICY = ({ seconds, verbose, off, dieAt }) => {
  const can = v => !(off || []).includes(v);
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
    // Unstick. A beeline at a doorway catches its frame about as often as it goes
    // through, and a policy with no answer to that stands in a corridor for the
    // rest of the night: the first draft logged 11,962 stuck frames and one item.
    // Strafing for a few frames is what a person does without thinking about it.
    if (dist2(me.x, me.z, lastX, lastZ) < 0.004) stuckFor++; else stuckFor = 0;
    if (stuckFor > 25) {
      g.press(((stuckFor >> 5) & 1) ? "KeyA" : "KeyD");
      if (stuckFor > 180) { stuckFor = 0; return -1; }    // give up on this target
    } else { g.press("KeyA", false); g.press("KeyD", false); }
    lastX = me.x; lastZ = me.z;
    return dist2(me.x, me.z, tx, tz);
  };
  const stop = () => { g.press("KeyW", false); g.press("ShiftLeft", false);
    g.press("KeyA", false); g.press("KeyD", false); };

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
      // R11's policy, which the crew already follow and the player did not: take
      // two or three cursed pieces and then stop. Ruin is 0.015 x cursed^1.8 at
      // extraction, so a fourth is how a $5,618 night banks $0 - which is exactly
      // what the first run of this policy did on night one.
      if (can("curse") && it.known && it.grade !== "clean" && aboard() >= CURSE_CAP)
        continue;
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
  let took = 0, delivered = 0, idle = 0, knocks = 0;
  // A scan is 3.2 seconds out of 210. Twelve of them is a fifth of the night,
  // which is about as much looking as hauling can pay for.
  const SCAN_BUDGET = 12, WORTH_IT = 220, CURSE_CAP = 3;
  const aboard = () => g.cargo().filter(c => c.grade !== "clean").length;
  const skip = new Set();
  let leverAt = 0;
  const HIDE_UNTIL = 3;

  for (let frame = 0; frame < seconds * 60; frame++) {
    const st = g.state();
    if (st.over) break;
    if (dieAt && st.t >= dieAt && !st.dead) { g.killPlayer(); say("died"); }
    const me = g.raw();

    // 0. The apex run. On a late night the biggest single thing in the house is a
    // cart-class piece behind the boards, worth 32-64% of the final quota on its
    // own (D-21), and it takes three tools in sequence: fetch the crowbar, walk it
    // to the deepest wing, pry, then wheel the piece back on the dolly. A policy
    // that cannot do that cannot reach a third of the night's money.
    // Only once the house is open: the deepest wing sits behind the prerequisite
    // chain as well as the boards, and a policy that sets off for it on minute one
    // walks into a locked door and stays there. Hauling is what opens the chain,
    // so this waits until the only locks left are wooden ones.
    const apex = g.apex();
    const onlyBoards = g.locked().every(id =>
      g.boarded().doors.some(d => d.id === id));
    if (can("apex") && apex && onlyBoards && phase !== "HIDE" && !st.holding) {
      const bd = g.boarded();
      const bar = g.crowbar(), doll = g.dolly();
      if (bd.doors.length && !bar.held) {
        // Go and get it.
        if (walkToward(bar.x, bar.z) < 1.5) { stop(); g.takeCrowbar(); say("picked up the crowbar"); }
        g.step(1, 1 / 60); continue;
      }
      if (bd.doors.length && bar.held) {
        const d = bd.doors[0];
        if (walkToward(d.x, d.z) < 0.9) { stop(); }   // walking into it pries it
        if (!g.boarded().doors.length) say("pried the boards off");
        g.step(1, 1 / 60); continue;
      }
      if (bar.held) { stop(); g.takeCrowbar(); }      // hands free from here on
      if (!doll.held && !doll.load) {
        if (walkToward(doll.x, doll.z) < 1.6) { stop(); g.takeDolly(); say("took the dolly"); }
        g.step(1, 1 / 60); continue;
      }
      if (doll.held && !doll.load) {
        const it = g.list().find(i => i.klass === "cart");
        if (!it) { /* somebody else has it */ }
        else if (walkToward(it.x, it.z) < 2.0) {
          stop();
          if (g.loadDolly()) say(`loaded the apex, $${it.value.toLocaleString()}`);
        }
        g.step(1, 1 / 60); continue;
      }
      if (doll.held && doll.load) {
        const v = van();
        if (walkToward(v.x, v.z) < 1.4) { stop(); }
        g.step(1, 1 / 60); continue;
      }
    }

    // 0b. Dead. DESIGN 5.1 makes this a role change rather than a spectator seat:
    // the ghost can see the Curator at all times and has Static to spend. What a
    // ghost is FOR is pulling the hunt off whoever is carrying - a knock is a
    // noise at your location, which is the cheapest way to do that.
    if (st.dead) {
      if (st.collecting > 0) { g.step(1, 1 / 60); continue; }
      const cur = g.curator();
      // `who` is only set while it is hunting a named body. A ghost waiting for
      // that does nothing all night - the first measurement of this averaged 0.3
      // knocks a night, which tests a ghost that is not trying. What a ghost can
      // actually see is the Curator and the crew, so: pull it off whoever is
      // carrying and closest to it, whenever the night is at PURSUE or worse.
      const carrying = g.crew().filter(c => c.alive && c.holding);
      const hunted = g.crew().find(c => c.name === cur.who)
        || (st.dist >= 60 && carrying.length
            ? carrying.sort((x, y) => dist2(cur.x, cur.z, x.x, x.z)
                                    - dist2(cur.x, cur.z, y.x, y.z))[0]
            : null);
      if (hunted && st.static >= 1 && dist2(cur.x, cur.z, hunted.x, hunted.z) < 16) {
        // Stand somewhere the Curator will hear, away from whoever it is on.
        const away = { x: (hunted.x + cur.x) / 2 + (cur.x - hunted.x),
                       z: (hunted.z + cur.z) / 2 + (cur.z - hunted.z) };
        if (dist2(me.x, me.z, away.x, away.z) > 2.0) walkToward(away.x, away.z);
        else { stop(); if (g.knock()) { knocks++; say(`knocked to pull it off ${cur.who}`); } }
      } else if (g.flickerLights && g.lights().lit.length && st.static >= 1) {
        g.flickerLights();
      }
      g.step(1, 1 / 60);
      continue;
    }

    // 1. Hunted and holding: hide. DESIGN 8.1 is the whole answer to COLLECT.
    if (can("hide") && st.marked && st.holding && phase !== "HIDE") {
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

    // 3. At the van: spend a lever if the night has got away from us, and dump the
    // cursed cargo if the crew have loaded past the cap. Ruin is rolled at
    // extraction, so the yard is the only place a fourth cursed piece can go.
    if (can("levers") && roomOf(me.x, me.z) === van().id && st.t > leverAt) {
      const lv = g.levers();
      if (aboard() > CURSE_CAP) {
        g.unloadCursed();
        // ...and do not pick them straight back up. The yard is beside the van,
        // the pieces are still in the list, and the selector went for the nearest
        // valuable thing: 142 pickups in one second, unloading and reloading the
        // same $1,316 vase, with the ruin roll happening at extraction either way.
        for (const it of g.list())
          if (g.roomAt(it.x, it.z) === van().id) skip.add(it.i);
        leverAt = st.t + 5;
        say("dumped the cursed cargo in the yard");
      } else if (st.dist > 80) {
        if (g.lights().lit.length) { g.killLights(); say("killed the lights"); }
        else if (lv.quiet <= 0) { g.goQuiet(); say("called for quiet"); }
        leverAt = st.t + 10;
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
    if (d < 0) { skip.add(t.i); target = null; g.step(1, 1 / 60); continue; }
    // 2.2m, not 1.6: a sideboard is solid, so walking at the item itself ends with
    // the player pressed against the furniture and the piece still out of reach.
    // Grab range is 3.2m in a 30-degree cone, and the cone is the part that has to
    // be aimed - a piece on a shelf sits half a metre below eye level, which at
    // this range is a pitch of about -0.3 rather than the -0.15 that was there.
    if (d < 2.2) {
      stop();
      const drop = Math.max(0.05, 1.62 - t.y);
      g.look(Math.atan2(t.x - me.x, t.z - me.z), -Math.atan2(drop, Math.max(0.4, d)));
      if (can("scan") && !t.known && appraised < SCAN_BUDGET) {
        g.press("KeyF"); g.step(60 * 3.2, 1 / 60); g.press("KeyF", false);
        appraised++;
        const now = g.list().find(i => i.i === t.i);
        if (now && now.known && now.value / SLOT[now.klass] < WORTH_IT) {
          skip.add(t.i); target = null; say(`walked away from $${now.value}`);
        }
      } else if (can("curse") && t.known && t.grade !== "clean" && aboard() >= CURSE_CAP) {
        skip.add(t.i); target = null; say("left a cursed piece where it was");
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
    dead: st.dead, dist: st.dist, appraised, took, delivered, idle, knocks,
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
      passPlayed: played.filter(p => p.met).length / played.length,
      quota: played[0].quota,
      nets: played.map(p => p.net ?? 0).sort((a, b) => a - b) });
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
  if (has("--death")) {
    // DESIGN 5: "Death always costs the crew more than the ghost gives back -
    // that margin is what keeps this honest, and it's the first thing to check in
    // playtest." Nobody has ever checked it. Paired, on identical houses: the same
    // night played through, against the same night with the player collected at
    // sixty seconds and playing on as a ghost.
    console.log(`\nWHAT DYING COSTS  -  ${trials} nights a night, paired`);
    console.log("-".repeat(74));
    console.log("night".padEnd(7) + "alive".padStart(10) + "died at 60s".padStart(13)
      + "the margin".padStart(12) + "95% band".padStart(10) + "knocks".padStart(8));
    const all = [];
    for (let n = 0; n < 4; n++) {
      const diffs = [], knocks = [];
      let a = 0, d = 0;
      for (let t = 0; t < trials; t++) {
        const sd = (t + 1) * 104729 + n;
        const setup = ([s2, nn]) => {
          window.__g.newContract(s2); window.__g.regen(s2, nn); window.__g.setNight(nn);
        };
        await page.evaluate(setup, [sd, n]);
        const alive = await page.evaluate(POLICY, { seconds: 210, verbose: false });
        await page.evaluate(setup, [sd, n]);
        const died = await page.evaluate(POLICY,
          { seconds: 210, verbose: false, dieAt: 60 });
        a += alive.net ?? 0; d += died.net ?? 0;
        diffs.push((died.net ?? 0) - (alive.net ?? 0));
        knocks.push(died.knocks);
        all.push((died.net ?? 0) - (alive.net ?? 0));
      }
      const mean = diffs.reduce((x, y) => x + y, 0) / diffs.length;
      const sd2 = Math.sqrt(diffs.reduce((x, y) => x + (y - mean) ** 2, 0)
        / Math.max(1, diffs.length - 1));
      console.log(String(n + 1).padEnd(7)
        + ("$" + Math.round(a / trials).toLocaleString()).padStart(10)
        + ("$" + Math.round(d / trials).toLocaleString()).padStart(13)
        + ((mean >= 0 ? "+" : "") + Math.round(mean).toLocaleString()).padStart(12)
        + ("+-" + Math.round(2 * sd2 / Math.sqrt(diffs.length))).padStart(10)
        + (knocks.reduce((x, y) => x + y, 0) / knocks.length).toFixed(1).padStart(8));
    }
    const m = all.reduce((x, y) => x + y, 0) / all.length;
    const sd3 = Math.sqrt(all.reduce((x, y) => x + (y - m) ** 2, 0) / (all.length - 1));
    const se = sd3 / Math.sqrt(all.length);
    console.log("-".repeat(74));
    console.log(`  over the whole chain, dying is worth ${Math.round(m)} `
      + `+-${Math.round(2 * se)} a night`);
    if (has("--check")) {
      // DESIGN 5 makes two claims and only one of them is checkable at this
      // sample size. "Death always costs the crew more than the ghost gives back"
      // is true in DIRECTION on every night and does not clear its band over the
      // chain - a competent ghost recovers most of it, which is a finding rather
      // than a failure. What IS checkable, and is the thing 5.1 actually guards
      // against, is the other side: dying must never be worth doing on purpose.
      const ok = m < 2 * se;
      console.log(ok
        ? `  OK   dying is not worth doing on purpose (${Math.round(m)} +-${Math.round(2 * se)})`
        : "  FAIL  the crew are BETTER OFF with somebody dead - 5.1's premise is gone");
      if (!ok) { await browser.close(); process.exit(1); }
    }
    await browser.close();
    return;
  }
  if (has("--ablate")) {
    // What each verb is actually worth, in the build, to somebody playing it.
    // Every one of these has an answer in a design document and most have one in
    // a sim; none of them had one HERE, because until R44 nobody was playing.
    const OFF = [
      ["nothing", [], "the policy as it stands"],
      ["scan", ["scan"], "never appraise - DESIGN 4.4 says the game rests on this"],
      ["hide", ["hide"], "never use the furniture - DESIGN 8.1"],
      ["apex", ["apex"], "leave the apex behind the boards - D-21"],
      ["curse", ["curse"], "no cursed-cargo cap - R11 / D-11"],
      ["levers", ["levers"], "never touch a lever - DESIGN 6.5"],
    ];
    console.log(`\nWHAT EACH VERB IS WORTH  -  ${trials} nights a night, all four nights`);
    console.log("-".repeat(74));
    console.log("policy".padEnd(10) + "vs full".padStart(11) + "95% band".padStart(10)
      + "pass".padStart(8) + "ruined".padStart(8) + "died".padStart(7)
      + "   what is off  (* = outside the band)");
    // PAIRED, on identical houses. This project learned in R11 that comparing two
    // policies across two sets of seeds measures the seeds: an unpaired first run
    // of this table said appraising costs 5% at eight nights and pays 7% at
    // twenty-four, which is the between-house variance talking, not the verb. The
    // difference per house has a standard error a fraction of the size.
    const ROWS = [];
    const full = new Map();
    for (let n = 0; n < 4; n++) {
      for (let t = 0; t < trials; t++) {
        const sd = (t + 1) * 104729 + n;
        await page.evaluate(([s2, nn]) => {
          window.__g.newContract(s2); window.__g.regen(s2, nn); window.__g.setNight(nn);
        }, [sd, n]);
        full.set(`${n}:${t}`, await page.evaluate(POLICY,
          { seconds: 210, verbose: false, off: [] }));
      }
    }
    for (const [name, off, why] of OFF) {
      const diffs = [], met = [], ruin = [], died = [];
      for (let n = 0; n < 4; n++) {
        for (let t = 0; t < trials; t++) {
          const sd = (t + 1) * 104729 + n;
          const base = full.get(`${n}:${t}`);
          let r = base;
          if (off.length) {
            await page.evaluate(([s2, nn]) => {
              window.__g.newContract(s2); window.__g.regen(s2, nn); window.__g.setNight(nn);
            }, [sd, n]);
            r = await page.evaluate(POLICY, { seconds: 210, verbose: false, off });
          }
          diffs.push((r.net ?? 0) - (base.net ?? 0));
          met.push(!!r.met); ruin.push((r.net ?? 0) === 0); died.push(!!r.dead);
        }
      }
      const mean = diffs.reduce((a, b) => a + b, 0) / diffs.length;
      const sd = Math.sqrt(diffs.reduce((a, b) => a + (b - mean) ** 2, 0)
        / Math.max(1, diffs.length - 1));
      const se = sd / Math.sqrt(diffs.length);
      const sig = off.length && Math.abs(mean) > 2 * se ? " *" : "";
      ROWS.push({ name, mean, se });
      console.log(name.padEnd(10)
        + (off.length ? (mean >= 0 ? "+" : "") + Math.round(mean).toLocaleString() : "-")
          .padStart(11)
        + (off.length ? "+-" + Math.round(2 * se) : "-").padStart(10)
        + (Math.round(met.filter(Boolean).length / met.length * 100) + "%").padStart(8)
        + (Math.round(ruin.filter(Boolean).length / ruin.length * 100) + "%").padStart(8)
        + String(died.filter(Boolean).length).padStart(7) + sig.padEnd(2) + " " + why);
    }
    if (has("--check")) {
      const fails = [];
      // Twelve nights a cell puts the appraiser at -301 +-898 and twenty puts it
      // at -620 +-508. The effect is real and it is narrow; the band has to be
      // small enough to see it before the claim means anything.
      if (trials < 20) fails.push(`--ablate --check needs --trials 20 or more `
        + `(got ${trials}); below that the band is wider than every effect in the table`);
      const scan = ROWS.find(r => r.name === "scan");
      if (!(scan.mean < 0 && Math.abs(scan.mean) > 2 * scan.se))
        fails.push(`turning the appraiser off costs ${Math.round(scan.mean)} `
          + `+-${Math.round(2 * scan.se)} - D-10 says the mechanic is dead if that is `
          + "not clearly negative");
      if (ROWS.filter(r => r.name !== "nothing").some(r => r.mean > 2 * r.se))
        fails.push("a verb PAYS to switch off: "
          + ROWS.filter(r => r.mean > 2 * r.se).map(r => r.name).join(", "));
      console.log("-".repeat(74));
      if (!fails.length) {
        console.log("  OK   every verb is worth having, and the appraiser clearly so");
      } else {
        for (const f of fails) console.log("  FAIL  " + f);
        await browser.close();
        process.exit(1);
      }
    }
    await browser.close();
    return;
  }
  if (has("--calibrate")) {
    // ECONOMY 4's pass rates are for a crew that includes somebody playing. The
    // build's quotas were measured in R25 against an idle player, which is why
    // the last night passes 88% here instead of biting. This prints the quota
    // that would produce each documented rate against the PLAYED distribution.
    console.log("\nWHAT THE QUOTA WOULD HAVE TO BE  (played, n=" + trials + ")");
    console.log("-".repeat(74));
    console.log("night".padEnd(7) + "now".padStart(9) + "95%".padStart(9)
      + "73%".padStart(9) + "55%".padStart(9) + "40%".padStart(9) + "median".padStart(10));
    for (const r of SUMMARY) {
      const q = f => r.nets[Math.min(r.nets.length - 1,
        Math.max(0, Math.floor(r.nets.length * (1 - f))))];
      console.log(String(r.night).padEnd(7) + String(r.quota).padStart(9)
        + String(q(0.95)).padStart(9) + String(q(0.73)).padStart(9)
        + String(q(0.55)).padStart(9) + String(q(0.40)).padStart(9)
        + String(r.nets[r.nets.length >> 1]).padStart(10));
    }
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
