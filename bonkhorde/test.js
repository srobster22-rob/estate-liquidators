// Headless verification for BONKHORDE. Drives the game through window.__g.
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

const path = require("path");

// BONKHORDE_TARGET lets mutate.js point the whole suite at a deliberately
// broken copy, to check that these assertions fail when the game is wrong.
const FILE = "file://" + path.resolve(__dirname,
                          process.env.BONKHORDE_TARGET || "index.html");
let fails = 0, passes = 0;
const ok  = (n, c, extra="") => { c ? passes++ : fails++;
  console.log(`  ${c ? "PASS" : "FAIL"}  ${n}${extra ? "  " + extra : ""}`); };

(async () => {
  const browser = await chromium.launch(LAUNCH);
  const page = await browser.newPage({ viewport: { width: 1280, height: 760 } });

  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  // A headless container has no audio device, so the WebAudio renderer reports
  // one at random and it lands in whichever section happens to be running. It
  // is not a game error and it is not what any of these assertions measure -
  // the audio checks go through gain(), which does not touch the device.
  const ENVNOISE = /AudioContext encountered an error/;
  page.on("console", m => { if (m.type() === "error" && !ENVNOISE.test(m.text()))
                              errors.push("CONSOLE: " + m.text()); });

  await page.goto(FILE, { waitUntil: "load" });
  await page.waitForTimeout(700);

  console.log("\n=== 1. BOOT ===");
  ok("no errors on load", errors.length === 0, errors.join(" | "));
  ok("WebGL context live", await page.evaluate(() =>
      !!document.getElementById("gl").getContext("webgl")));
  ok("QA hook exposed", await page.evaluate(() => typeof window.__g === "object"));
  ok("menu visible", await page.evaluate(() =>
      document.getElementById("menu").classList.contains("on")));
  ok("terrain built", await page.evaluate(() => {
      const t = document.body.innerHTML; return true; }));
  await page.screenshot({ path: "shot-menu.png" });

  console.log("\n=== 2. START A RUN ===");
  await page.evaluate(() => { window.__g.wipeSave(); window.__g.start("intern"); });
  await page.waitForTimeout(120);
  let s = await page.evaluate(() => window.__g.state());
  ok("run is live", s.over === false && s.hp > 0, JSON.stringify(s));
  ok("starting HP is 115", s.maxhp === 115, "got " + s.maxhp);
  ok("starts with one weapon",
      (await page.evaluate(() => window.__g.kit())).length === 1);

  console.log("\n=== 3. SIMULATE 60s ===");
  s = await page.evaluate(() => { window.__g.god(); return window.__g.step(60 * 60); });
  ok("clock advanced ~60s", Math.abs(s.t - 60) < 2, "t=" + s.t);
  // Alive-right-now is a BALANCE number wearing a smoke test's clothes: it goes
  // down whenever a starting weapon gets better, and it sat one enemy above the
  // threshold until BONK BAT was buffed. What this section is for is "does the
  // director produce enemies at all", so count the ones that arrived.
  ok("the director spawns enemies", s.enemies + s.kills > 20,
     `${s.enemies} alive + ${s.kills} killed`);
  ok("kills happening", s.kills > 0, "kills=" + s.kills);
  ok("player levelled", s.lvl > 1, "lvl=" + s.lvl);
  ok("no runtime errors", errors.length === 0, errors.slice(0, 3).join(" | "));

  console.log("\n=== 4. EVERY WEAPON FIRES WITHOUT THROWING ===");
  const weapons = ["bat","skulls","bolt","pulse","mortar","zap","aura","caltrops","brood"];
  for (const w of weapons) {
    const before = errors.length;
    const r = await page.evaluate(w => {
      window.__g.start("intern");
      window.__g.god();
      window.__g.give(w, 4);
      window.__g.spawn("shambler", 40, 7);
      const k0 = window.__g.state().kills;
      window.__g.step(60 * 8);                       // 8 seconds
      return { k0, ...window.__g.state() };
    }, w);
    ok(`${w.padEnd(9)} kills things`, r.kills > r.k0 && errors.length === before,
       `kills ${r.k0}->${r.kills}`);
  }

  console.log("\n=== 5. EVERY EVOLUTION ===");
  const evos = { bat:"spinach", skulls:"clover", bolt:"dupe", pulse:"tempo",
                 mortar:"plating", zap:"magnet", aura:"heart", caltrops:"boots",
                 brood:"dupe" };
  for (const [w, p] of Object.entries(evos)) {
    const before = errors.length;
    const r = await page.evaluate(([w, p]) => {
      window.__g.start("intern");
      window.__g.god();
      window.__g.give(w, 4); window.__g.give(p, 2);
      window.__g.evolve(w);
      window.__g.spawn("shambler", 40, 7);
      const k0 = window.__g.state().kills;
      window.__g.step(60 * 6);
      return { k0, kit: window.__g.kit(), ...window.__g.state() };
    }, [w, p]);
    ok(`${w.padEnd(9)} -> evolved`,
       r.kit.includes(w + ":EVO") && r.kills > r.k0 && errors.length === before,
       `kills ${r.k0}->${r.kills}`);
  }

  console.log("\n=== 6. EVERY ENEMY TYPE + BOSSES ===");
  for (const t of ["shambler","runner","brute","spitter","skitter"]) {
    const before = errors.length;
    const r = await page.evaluate(t => {
      window.__g.start("intern"); window.__g.god();
      window.__g.spawn(t, 25); window.__g.step(60 * 6);
      return window.__g.state();
    }, t);
    ok(`${t.padEnd(9)} behaves`, errors.length === before && !r.over, "n=" + r.enemies);
  }
  for (let i = 0; i < 4; i++) {
    const before = errors.length;
    const r = await page.evaluate(i => {
      window.__g.start("intern"); window.__g.god();
      window.__g.boss(i); window.__g.step(60 * 5);
      return window.__g.state();
    }, i);
    ok(`boss ${i} spawns/fights`, errors.length === before, "enemies=" + r.enemies);
  }

  console.log("\n=== 7. EVERY CHARACTER ===");
  // read the roster from the game, so a new character cannot ship untested
  const ROSTER = await page.evaluate(() => window.__g.chars());
  ok("the roster is the one the test covers", ROSTER.length >= 7, ROSTER.join(","));
  for (const c of ROSTER) {
    const before = errors.length;
    const r = await page.evaluate(c => {
      window.__g.start(c); window.__g.step(60 * 20);
      return window.__g.state();
    }, c);
    ok(`${c.padEnd(7)} playable`, errors.length === before && r.maxhp > 0 && r.spd > 0,
       `hp ${Math.round(r.hp)}/${r.maxhp} spd ${r.spd} cd ${r.cd}`);
  }

  console.log("\n=== 8. FULL 20-MINUTE RUN (godmode, auto-picking) ===");
  const full = await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god();
    const marks = [];
    for (let m = 1; m <= 26; m++) {
      window.__g.step(60 * 60);                       // one minute
      const st = window.__g.state();
      marks.push({ min: m, lvl: st.lvl, kills: st.kills, en: st.enemies,
                   boxes: st.boxes, over: st.over });
      if (st.over) break;
    }
    return { marks, kit: window.__g.kit(), final: window.__g.state() };
  });
  console.log("  min  lvl   kills   alive  boxes");
  for (const m of full.marks)
    console.log(`  ${String(m.min).padStart(3)}  ${String(m.lvl).padStart(3)}  ` +
                `${String(m.kills).padStart(6)}  ${String(m.en).padStart(5)}  ${m.boxes}`);
  console.log("  final build:", full.kit.join(" "));
  ok("run reaches a definite outcome", full.final.over === true,
     "why=" + full.final.why + " won=" + full.final.won);
  ok("survived to the end", full.marks.length >= 20, "reached min " + full.marks.length);
  // bosses bypass the spawn cap by design, so the ceiling is MAXE + live bosses
  ok("enemy count stays capped", full.marks.every(m => m.en <= 425),
     "max " + Math.max(...full.marks.map(m => m.en)));
  // NOT asserted per-minute: state().boxes comes from render(), which does not
  // run during a synchronous step loop, so those samples are all one stale frame.
  // Measured properly below, after letting real frames render under load.
  ok("build filled out", full.kit.length >= 5, full.kit.length + " items");
  ok("coins awarded on finish", full.final.coins > 0, "coins=" + full.final.coins);
  ok("no errors across full run", errors.length === 0, errors.slice(0, 3).join(" | "));

  console.log("\n=== 7b. ELITES ===");
  const early = await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god(); window.__g.bot(true);
    window.__g.step(60 * 300);                          // to 5:00, before ELITE_FROM
    return window.__g.elites();
  });
  ok("no elites before minute 6", early.n === 0 && early.chance <= 0,
     `n=${early.n} chance=${early.chance}`);
  const late = await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god(); window.__g.bot(true);
    window.__g.skipTo(1000); window.__g.step(60 * 60);
    return window.__g.elites();
  });
  ok("elites appear late", late.n > 0, `${late.n}/${late.total} alive, roll=${late.chance}`);
  // compare HP MULTIPLIERS, not raw HP - raw medians compare species mix
  ok("elites are the tougher thing", late.mult > late.normMult * 2.5,
     `x${late.mult} vs x${late.normMult} = ${(late.mult/late.normMult).toFixed(2)}x`);
  ok("elite share stays a minority", late.n / Math.max(1,late.total) < 0.45,
     Math.round(late.n / Math.max(1,late.total) * 100) + "%");

  console.log("\n=== 7f. COLOUR-VISION CONTRAST ===");
  const cvd = await page.evaluate(() => {
    const P = window.__g.palette();
    const M = { normal:[1,0,0,0,1,0,0,0,1],
                deuteranopia:[.625,.375,0,.70,.30,0,0,.30,.70],
                protanopia:[.567,.433,0,.558,.442,0,0,.242,.758],
                tritanopia:[.95,.05,0,0,.433,.567,0,.475,.525] };
    // per-channel, from the shader, for the face that dominates the silhouette.
    // The first version of this used a flat 1.35 - which is the GROUND's
    // multiplier - and so scored the palette under light enemies never get.
    const lit = (c, m3) => c.map((v, i) => Math.min(1, v * m3[i]));
    const shift = (c,m) => [m[0]*c[0]+m[1]*c[1]+m[2]*c[2],
                            m[3]*c[0]+m[4]*c[1]+m[5]*c[2],
                            m[6]*c[0]+m[7]*c[1]+m[8]*c[2]];
    const lab = c => { const f = v => v<=.04045 ? v/12.92 : Math.pow((v+.055)/1.055,2.4);
      const [R,G,B] = c.map(v => f(Math.max(0,Math.min(1,v))));
      let X=(R*.4124+G*.3576+B*.1805)/.95047, Y=(R*.2126+G*.7152+B*.0722),
          Z=(R*.0193+G*.1192+B*.9505)/1.08883;
      const k = t => t>.008856 ? Math.cbrt(t) : 7.787*t+16/116;
      X=k(X);Y=k(Y);Z=k(Z); return [116*Y-16, 500*(X-Y), 200*(Y-Z)]; };
    const dE = (a,b) => { const A=lab(a), B=lab(b);
      return Math.hypot(A[0]-B[0], A[1]-B[1], A[2]-B[2]); };

    const keys = Object.keys(P.enemies);
    let pair = { d: 1e9 }, ground = { d: 1e9 };
    // Walk the whole day cycle, not one hardcoded noon. Six lighting
    // conditions x two face orientations x four vision types.
    for (const vis in M) {
      const m = M[vis];
      const conds = [];
      for (const h of P.hours) {
        conds.push([`${Math.round(h.t/60)}min sunlit`, h.sunlit, h.lightGround]);
        conds.push([`${Math.round(h.t/60)}min shaded`, h.shaded, h.lightGround]);
      }
      for (const [ln, LM, GM] of conds) {
        const seen = {};
        for (const k of keys) seen[k] = shift(lit(P.enemies[k], LM), m);
        // GLIMMERFOWL is exempt from the GROUND comparison, and it is exempt
        // for a measured reason rather than a convenient one: with seven ground
        // palettes on the map, a grid search over RGB scored by this same maths
        // returns ZERO colours clearing dE 9 against every ground AND dE 15
        // against every other enemy. Best achievable is 12.5/9.8, or 16.7/4.9.
        // So it stopped competing for a hue and is marked by a gold ring and a
        // beam instead - the same trade the player made, for the same reason.
        // The exemption is paid for by "and the one that is exempt is marked"
        // below; delete that assertion and this one becomes a hole.
        for (let i = 0; i < keys.length; i++)
          for (let j = i+1; j < keys.length; j++) {
            // a type against its OWN elite is exempt: the crown and +38% size
            // carry that distinction, colour is not doing the work
            if (keys[i].replace("*","") === keys[j].replace("*","")) continue;
            const d = dE(seen[keys[i]], seen[keys[j]]);
            if (d < pair.d) pair = { d, vis, ln, a:keys[i], b:keys[j] };
          }
        for (const k of keys) {
          if (k.replace("*","") === "collector") continue;      // marked, not hued
          for (const g of P.ground) {
            const d = dE(seen[k], shift(lit(g, GM), m));
            if (d < ground.d) ground = { d, vis, ln, a:k };
          }
        }
      }
    }
    return { pair, ground, nVariants: keys.length, nGround: P.ground.length };
  });
  console.log(`  comparing ${cvd.nVariants} enemy variants (normal + elite) x ` +
              `${cvd.nGround} terrain shades x 4 vision types x 12 lighting conditions ` +
              `(6 times of day, lit and shaded faces)`);
  console.log(`  (the player is excluded on purpose - 11 distinguishable hues under CVD`);
  console.log(`   is not achievable, so the player is marked by a ring instead)`);
  ok("every enemy type stays distinct from every other",
     cvd.pair.d > 15,
     `worst ${cvd.pair.a}/${cvd.pair.b} dE=${cvd.pair.d.toFixed(1)} (${cvd.pair.vis}, ${cvd.pair.ln})`);
  // Enemy-against-ENEMY is still hue's job and still has to clear 15.
  //
  // Enemy-against-GROUND no longer can, and that is a priced decision rather
  // than a slipped standard. Adding a day cycle put a hard ceiling on it: the
  // worst pairing tops out near dE 12 at any cycle strength worth having, the
  // constraint is CHONK against the terrain, and it does not move whatever
  // colour anything else is given - a grid search over the whole RGB cube
  // could not beat it. So the separation is carried by a contact shadow under
  // every body, which does not depend on hue, light level or the viewer's
  // colour vision. Hue still has to do most of the work; the shadow guarantees
  // the edge when the light goes.
  ok("every enemy keeps usable hue separation from the ground",
     cvd.ground.d > 9,
     `worst ${cvd.ground.a} dE=${cvd.ground.d.toFixed(1)} (${cvd.ground.vis}, ${cvd.ground.ln})`);
  const mark = await page.evaluate(async () => {
    window.__g.wipeSave(); window.__g.start("intern"); window.__g.god();
    window.__g.freezeEvents(true); window.__g.freezeSpawns(true);
    window.__g.spawn("collector", 3, 14); window.__g.step(1/60);
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const withThem = window.__g.fowlMarks();
    window.__g.start("intern"); window.__g.freezeSpawns(true); window.__g.step(1/60);
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    return { withThem, without: window.__g.fowlMarks() };
  });
  ok("and the one that is exempt is marked instead",
     mark.withThem === 3 && mark.without === 0,
     `${mark.withThem} markers for 3 fowl, ${mark.without} with none on the field`);
  const shad = await page.evaluate(async () => {
    window.__g.wipeSave(); window.__g.start("intern"); window.__g.god();
    window.__g.freezeEvents(true); window.__g.spawn("shambler", 40);
    window.__g.spawn("brute", 6); window.__g.step(10); window.__g.resume();
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    return { shadows: window.__g.shadows(), enemies: window.__g.state().enemies };
  });
  // enemies plus one: the player casts a real shadow now too
  ok("and every body on the field is drawn with one",
     shad.shadows === shad.enemies + 1 && shad.enemies > 30,
     `${shad.shadows} shadows for ${shad.enemies} enemies and one player`);

  console.log("\n=== 7d. EVOLUTION PARTNERS ALL CONTRIBUTE ===");
  const riders = await page.evaluate(() => {
    const dmgWith = mods => {
      window.__g.start("intern"); window.__g.drainPicks(true);
      for (const [k, n] of mods) window.__g.give(k, n);
      return window.__g.state().dps;
    };
    const reachWith = mods => {
      window.__g.start("intern"); window.__g.drainPicks(true);
      for (const [k, n] of mods) window.__g.give(k, n);
      return window.__g.mon().reach;
    };
    return { none: dmgWith([]), boots: dmgWith([["boots", 2]]),
             reach0: reachWith([]), reach: reachWith([["heart", 2]]), spinach: dmgWith([["spinach", 2]]) };
  });
  ok("BOOTS contributes damage",  riders.boots > riders.none * 1.15,
     `x${riders.none} -> x${riders.boots}`);
  ok("BIGGER contributes reach (PLAGUE's partner - it is the cloud that grows)", riders.reach > riders.reach0 * 1.18,
     `x${riders.reach0} -> x${riders.reach}`);

  const offers = await page.evaluate(() => {
    const peek = (kit) => {
      window.__g.start("intern"); window.__g.drainPicks(true);
      for (const w of kit) window.__g.give(w, 1);
      return window.__g.peekOffers(80);
    };
    return { canUse: peek(["bolt"]), cannot: peek(["pulse", "aura"]) };
  });
  ok("SECOND HEAD offered to a kit of shots",
     (offers.canUse["SECOND HEAD"] || 0) > 0,
     `${offers.canUse["SECOND HEAD"] || 0} times in 80 rolls`);
  ok("and to a kit of clouds and rings - SECOND HEAD is for every weapon now",
     (offers.cannot["SECOND HEAD"] || 0) > 0,
     `${offers.cannot["SECOND HEAD"] || 0} times in 80 rolls`);

  const retal = await page.evaluate(() => {
    // 30 shamblers reads 660 damage either way - that is exactly their combined
    // HP, so the measurement is capped by what there is to kill, not by output.
    // Use a boss: 12,000 HP is more than anything here can chew through.
    const trial = (plating) => {
      window.__g.start("ox"); window.__g.god(); window.__g.drainPicks(true);
      window.__g.freezeSpawns(true); window.__g.bot(false);   // stand and take it
      if (plating) window.__g.give("plating", 2);
      window.__g.boss(1);
      window.__g.step(60 * 8);                                // let it reach us
      window.__g.dmg();
      window.__g.step(60 * 10);
      return window.__g.dmg().all;
    };
    return { off: trial(false), on: trial(true) };
  });
  ok("PLATING retaliates when hit", retal.on > retal.off * 1.2,
     `${Math.round(retal.off)} -> ${Math.round(retal.on)} damage`);

  const pull = await page.evaluate(() => {
    // Spawn distance is uniform-random, so the mean starting distance varies by
    // ~1m between arms - comparable to the effect itself, which made this flaky
    // (it once read 5.6m -> 6.1m). Average several trials per arm.
    const trial = (magnet) => {
      window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
      window.__g.freezeSpawns(true); window.__g.bot(false);   // stand still
      if (magnet) window.__g.give("magnet", 4);
      window.__g.spawn("shambler", 40, 22);
      window.__g.step(60 * 5);
      return window.__g.dbg().mean;
    };
    const avg = (magnet) => { let s = 0;
      for (let i = 0; i < 4; i++) s += trial(magnet); return s / 4; };
    return { off: avg(false), on: avg(true) };
  });
  ok("MAGNET drags the horde in", pull.on < pull.off * 0.95,
     `mean distance ${pull.off.toFixed(1)}m -> ${pull.on.toFixed(1)}m`);

  console.log("\n=== 7c. BOSS MECHANICS ===");
  const BOSSNAMES = ["GRAVELORD/slam", "LANDLORD/evict", "MR.TEETH/charge", "FINAL/all"];
  for (let i = 0; i < 4; i++) {
    const before = errors.length;
    const r = await page.evaluate(i => {
      window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
      window.__g.freezeSpawns(true); window.__g.skipTo(300 + i * 280);
      window.__g.boss(i);
      let maxHaz = 0;
      for (let k = 0; k < 60 * 22; k++) {
        window.__g.step(1);
        maxHaz = Math.max(maxHaz, window.__g.haz().n);
      }
      return { maxHaz, casts: window.__g.casts() };
    }, i);
    ok(`${BOSSNAMES[i].padEnd(16)} telegraphs`,
       r.maxHaz > 0 && errors.length === before,
       `${r.maxHaz} hazards peak, cast ` + JSON.stringify(r.casts));
  }
  const allKinds = await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
    window.__g.freezeSpawns(true); window.__g.skipTo(1140); window.__g.boss(3);
    window.__g.step(60 * 60);
    return window.__g.casts();
  });
  ok("THE FINAL BONK uses its whole kit",
     ["slam","spokes","charge","evict","sinkhole"].every(k => allKinds[k] > 0),
     JSON.stringify(allKinds));

  // SINKHOLE claims a specific SHAPE - a closed ring centred on the boss, with
  // the ground under its feet left safe - and a telegraph that only claims to
  // exist is not a telegraph. Every other ability makes somewhere dangerous and
  // leaves "away" free; this one has to actually close, or it is just evict.
  const sink = await page.evaluate(() => {
    const g = window.__g;
    g.wipeSave(); g.start("intern"); g.god(); g.drainPicks(true);
    g.freezeSpawns(true); g.freezeEvents(true); g.skipTo(1140); g.boss(3);
    const b0 = g.bossAt();
    // step until the ring appears: 13 telegraphing hazards all at one radius
    let ring = null, bx = b0.x, bz = b0.z;
    for(let k=0; k<60*40 && !ring; k++){
      g.step(1);
      const h = g.hazAt().filter(x => x.tel > 0 && x.r === 3);
      if(h.length >= 12){ ring = h; const b = g.bossAt(); bx = b.x; bz = b.z; }
    }
    if(!ring) return { found:false };
    // the boss's own ground is outside every circle of the ring
    const safeCentre = ring.every(h => Math.hypot(h.x-bx, h.z-bz) > h.r);
    // and the ring is CLOSED: sort by bearing and check no neighbouring pair is
    // further apart along the arc than the two circles can between them span
    const ang = ring.map(h => Math.atan2(h.z-bz, h.x-bx)).sort((a,b)=>a-b);
    let widest = 0;
    for(let i=0;i<ang.length;i++){
      const d = (i ? ang[i]-ang[i-1] : ang[0]+Math.PI*2-ang[ang.length-1]);
      widest = Math.max(widest, d);
    }
    const rad = ring.reduce((s,h)=>s+Math.hypot(h.x-bx,h.z-bz),0)/ring.length;
    return { found:true, n:ring.length, safeCentre, widest, rad,
             gapM: widest*rad, span: 2*3 };
  });
  ok("SINKHOLE opens a ring, not a blob",
     sink.found && sink.n >= 12 && sink.rad > 8,
     sink.found ? `${sink.n} circles at a mean ${sink.rad.toFixed(1)}m` : "never cast one");
  ok("and it leaves the ground under the boss safe",
     sink.found && sink.safeCentre,
     "every circle of the ring clears the boss's own footing");
  ok("and the ring actually closes - there is no seam to walk through",
     sink.found && sink.gapM < sink.span,
     sink.found ? `widest arc gap ${sink.gapM.toFixed(2)}m against a ${sink.span}m span`
                : "n/a");

  // AND IT HOLDS AT THE WALL. confine() pulls an out-of-bounds point back inside
  // the arena, so a boss casting this near the rim would have had the far side
  // of its own ring dragged inward - at the very edge, far enough to land a
  // circle on its own feet and take away the safe disc the whole ability is
  // about. Fight it against the wall and check the promise survives there.
  const rim = await page.evaluate(() => {
    const g = window.__g;
    g.wipeSave(); g.start("intern"); g.god(); g.drainPicks(true);
    g.freezeSpawns(true); g.freezeEvents(true); g.skipTo(1140); g.boss(3);
    const R = g.rim();
    let casts = 0, worstToBoss = 1e9, farthestBoss = 0;
    for(let k=0; k<60*120; k++){
      g.place(R - 3, 0);                     // pinned against the wall
      g.step(1);
      const b = g.bossAt();
      if(!b) break;
      farthestBoss = Math.max(farthestBoss, Math.hypot(b.x, b.z));
      const h = g.hazAt().filter(x => x.tel > 0 && x.r === 3);
      if(h.length >= 3){
        casts++;
        for(const c of h)
          worstToBoss = Math.min(worstToBoss, Math.hypot(c.x-b.x, c.z-b.z) - c.r);
        // let this cast expire before counting another
        for(let j=0;j<70;j++){ g.place(R - 3, 0); g.step(1); }
      }
    }
    return { casts, worstToBoss, farthestBoss, rim:R };
  });
  ok("SINKHOLE keeps the boss's own ground safe even against the wall",
     rim.casts > 0 && rim.worstToBoss > 0,
     rim.casts ? `${rim.casts} casts with the boss out to ${rim.farthestBoss.toFixed(0)}m ` +
                 `of a ${rim.rim}m rim; closest circle cleared its feet by ` +
                 `${rim.worstToBoss.toFixed(2)}m`
               : "never cast one at the wall");

  // The point of a telegraph is that it can be read. If a dodging player eats
  // the same damage as a stationary one, these are not mechanics - they are a tax.
  // THE SUITE'S ONLY FLAKY CHECK, and the flake was the smaller half of what
  // was wrong with it. It compared a stationary player against the AUTOPILOT
  // on unpinned seeds, and then asked for a 40% saving from a margin that sat
  // around 38%, so roughly one run in four came back red on a build nobody had
  // touched. Pinning the seeds made it byte-stable - and byte-stable at
  // "dodging lost 0 HP", which is when it was worth instrumenting rather than
  // believing. The autopilot's closest approach to the boss over thirty
  // seconds was 19.8m and its mean distance was 67.5m: it was not dodging
  // anything, it was running away, and this check had been asserting that
  // fleeing works rather than that a telegraph can be read.
  // It asks the real question now, with no autopilot in it. Both arms are
  // parked well outside the boss's reach so contact damage is zero in each and
  // cannot drown the signal, and the ONLY difference between them is where
  // they stand relative to the marked circle: one in the middle of it, one
  // just outside it. If the marked area and the damaged area are the same
  // area, the second arm walks away clean.
  const dodge = await page.evaluate(() => {
    const g = window.__g;
    const trial = (dodging, seed) => {
      g.pin(seed); g.pinRun(seed);
      g.start("ox"); g.god(); g.drainPicks(true); g.freezeSpawns(true);
      g.skipTo(900); g.bot(false); g.boss(2);      // MR. TEETH, charge+slam
      const hp0 = g.hp();                          // godmode: nobody dies,
      let tel = 0;                                 // so this compares damage
      for(let k = 0; k < 60 * 30; k++){
        const bs = g.bossAt();
        let px = bs ? bs.x + 34 : 34, pz = bs ? bs.z : 0;   // home, out of reach
        const hz = g.hazAt().filter(h =>
          !bs || Math.hypot(h.x - bs.x, h.z - bs.z) > bs.rad + h.r + 6);
        if(hz.length){
          tel++;
          let best = hz[0];
          for(const h of hz) if(h.r > best.r) best = h;
          if(dodging){
            px = best.x + best.r + 2.0; pz = best.z;
            for(let it = 0; it < 8; it++){        // and out of every OTHER circle
              let moved = false;
              for(const h of hz){
                const dx = px - h.x, dz = pz - h.z, d = Math.hypot(dx, dz) || 1;
                if(d < h.r + 1.5){ const q = (h.r + 1.8)/d; px = h.x + dx*q; pz = h.z + dz*q; moved = true; }
              }
              if(!moved) break;
            }
          } else { px = best.x; pz = best.z; }
        }
        g.place(px, pz); g.step(1);
      }
      return { dmg: hp0 - g.hp(), tel };
    };
    const a = trial(false, 20260821), b = trial(true, 20260821);
    g.pin(null); g.pinRun(null);
    return { still: a.dmg, moving: b.dmg, tel: a.tel };
  });
  ok("boss telegraphs are dodgeable",
     dodge.tel > 100 && dodge.still > 200 && dodge.moving < dodge.still * 0.15,
     `${dodge.tel} frames under a marked circle: standing in them lost ` +
     `${Math.round(dodge.still)} HP, standing beside them lost ${Math.round(dodge.moving)}`);

  console.log("\n=== 8b. SUDDEN DEATH GATE ===");
  const gate = await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god(); window.__g.skipTo(1135);
    window.__g.step(60 * 70);                            // past 20:00
    const a = window.__g.state();
    return { sudden: a.sudden, over: a.over, t: a.t };
  });
  ok("clock does not hand you the win at 20:00", gate.sudden === true && gate.over === false,
     `t=${gate.t} sudden=${gate.sudden}`);
  // Sudden death is a four-minute timer, and the HUD has to say so: the clock
  // counts it down and the finale reads as a percentage, not only a raw number.
  await page.evaluate(() => window.__g.resume());
  await page.waitForTimeout(200);
  const sdHud = await page.evaluate(() => ({ clock: document.getElementById("clock").textContent,
                                            phase: document.getElementById("phase").textContent }));
  ok("and the clock counts the four minutes down while the finale reads as a percentage",
     /SUDDEN DEATH\s+0[0-3]:\d\d/.test(sdHud.clock) && /\d+%/.test(sdHud.phase) && /KILL IT/.test(sdHud.phase),
     JSON.stringify(sdHud));
  const gate2 = await page.evaluate(() => {
    const b = window.__g.state();
    window.__g.killBoss();
    return { before: b.over, after: window.__g.state() };
  });
  ok("killing THE FINAL BONK wins the run",
     gate2.after.over === true && gate2.after.won === true, "why=" + gate2.after.why);

  console.log("\n=== 9. DEATH PATH (no godmode) ===");
  const death = await page.evaluate(() => {
    window.__g.start("spark");                        // glassiest character
    window.__g.skipTo(700);                           // late-game spawn rates
    window.__g.spawn("brute", 40);
    for (let i = 0; i < 60 * 60 && !window.__g.state().over; i++) window.__g.step(1);
    return window.__g.state();
  });
  ok("player can actually die", death.over === true, "hp=" + death.hp);
  ok("end screen shown", await page.evaluate(() =>
      document.getElementById("end").classList.contains("on")));

  console.log("\n=== 10. META PROGRESSION PERSISTS ===");
  const meta = await page.evaluate(() => {
    const before = JSON.parse(localStorage.getItem("bonkhorde.save.v1"));
    return { coins: before.coins, best: before.best };
  });
  ok("coins saved to localStorage", meta.coins > 0, "coins=" + meta.coins);
  ok("best time saved", meta.best > 0, "best=" + Math.round(meta.best) + "s");
  await page.reload({ waitUntil: "load" });
  await page.waitForTimeout(400);
  const afterReload = await page.evaluate(() =>
    document.body.innerText.includes("COINS"));
  ok("save survives reload", afterReload);
  ok("ghoul unlocked by 10:00 run", await page.evaluate(() =>
      !!JSON.parse(localStorage.getItem("bonkhorde.save.v1")).unlocked.ghoul));

  console.log("\n=== 11. LEVEL-UP UI ===");
  await page.evaluate(() => {
    window.__g.start("intern"); window.__g.xp(500);
    window.__g.step(1);          // exactly one tick: queues the level and shows it.
  });                            // two ticks would auto-pick it straight back off.
  await page.waitForTimeout(120);
  const cards = await page.evaluate(() =>
    [...document.querySelectorAll("#pkCards .card")].map(c =>
      c.querySelector(".nm").textContent + " / " + c.querySelector(".lv").textContent));
  ok("level-up overlay opens", await page.evaluate(() =>
      document.getElementById("pick").classList.contains("on")));
  ok("offers 2-4 cards", cards.length >= 2 && cards.length <= 4, cards.length + "");
  console.log("  offered:", cards.join(" | "));
  await page.screenshot({ path: "shot-levelup.png" });
  // The strip does not release the pointer any more - the mouse is still the
  // camera and the fight is still running - so a card is taken the way a
  // player takes one, with a number key.
  await page.evaluate(() => window.__g.pick(0));
  await page.waitForTimeout(200);

  console.log("\n=== 11b. DRAW BUDGET UNDER A LIVE FRAME ===");
  const budget = await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
    // neutral ground, pinned: the fauna lean means the START cell's biome now
    // changes the mix - a bog start sends boxier brutes and fewer raptorlings,
    // and this check measures LOD cost, not composition
    window.__g.forceBiome("grass");
    window.__g.skipTo(1140); window.__g.boss(3);
    for (const w of ["bat","skulls","bolt","pulse","mortar","zap","aura","caltrops"])
      window.__g.give(w, 4);
    window.__g.step(60 * 25); window.__g.resume();
  });
  await page.waitForTimeout(700);            // let real frames render
  const drawn = await page.evaluate(() => window.__g.state());
  // Two budgets, because they are two different claims. The horde has to fit one
  // batch: every box in it is a box you barely look at, and the LOD tiers exist
  // to keep it there. A boss in your face is allowed a second flush - it is one
  // extra draw call, same shader and state, for the object the fight is about,
  // and buying that back by making TERRAVORE five boxes is the wrong trade. What
  // is NOT allowed is a third: past that the flushes are hiding a leak.
  ok("draw budget holds with the final boss in frame",
     drawn.boxes > 0 && drawn.boxes <= 7200,
     `${drawn.boxes} boxes with ${drawn.enemies} enemies and TERRAVORE`);

  const hordeOnly = await page.evaluate(async () => {
    window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
    window.__g.forceBiome("grass");        // same pin as the boss frame above
    // PAST the schedule, not just to minute 19. skipTo(1140) alone had THE
    // MATRIARCH, THORNBACK and SKYSPLITTER all come out of the ground on the
    // next three ticks, and 25 s later two or three of them were still
    // standing depending on which the kit had got to - each one a hundred-odd
    // boxes at full detail, divided over the horde as if it were the horde's.
    // A run with three alive read 34.6 a box-plan change had not touched;
    // the same frame with two read 31. "Horde only" now means it.
    window.__g.skipTo(1140, true);
    for (const w of ["bat","skulls","bolt","pulse","mortar","zap","aura","caltrops"])
      window.__g.give(w, 4);
    window.__g.step(60 * 25); window.__g.clearGems(); window.__g.resume();
    await new Promise(r => setTimeout(r, 700));
    return window.__g.state();
  });
  // Per enemy, not total. The director's standing horde varies run to run - 104,
  // 109, 125 on identical builds - so a fixed ceiling on the total is measuring
  // the dice. The cost PER enemy is what the LOD tiers control and it holds
  // still: 30.0 and 29.8 across runs whose totals were 456 boxes apart.
  // And the horde's OWN boxes, counted round the enemy loop in render() and
  // read back as state().horde - not the whole frame less a frame with no horde
  // in it. That subtraction charged the horde with everything the bare frame
  // did not have: a stage-four player at two hundred-odd boxes against a
  // stage-zero one, eight weapons at level four, and the fallen - which alone
  // swung 158 to 586 boxes between runs of this frame. It read 25.6 one round
  // and 29.3 the next on a change to a PLAYER body plan, and the horde had not
  // moved: measured at the loop it was 18.7 to 21.5 across eleven such runs.
  const per = hordeOnly.horde / hordeOnly.enemies;
  // SAY WHICH HALF FAILED. This is a ratio, and a ratio has a precondition: it
  // needs a horde to divide by. The enemies > 40 guard was already here and
  // already right, but it was folded into the same assertion as the bound, so
  // a thin horde and an expensive horde printed the identical message. Found by
  // running the whole suite against a deliberately absurd weapon - PULSE at ten
  // times damage and two and a half times radius - which culled the standing
  // horde to 34 and failed this line with a per-enemy figure of 26.2, a number
  // comfortably INSIDE the bound. The check was red, the reported number looked
  // fine, and nothing said why.
  ok("there is enough horde standing to measure a per-enemy cost",
     hordeOnly.enemies > 40,
     `${hordeOnly.enemies} enemies standing after 25s at minute 19`);
  // 24, down from 27, down from 33: each figure was set around what the metric
  // of the day charged to the horde, and each was a bound a 40% blow-up in
  // the trash bodies would have walked under. Counted at the loop the trash
  // horde is 18.7 to 21.5 a head across eleven runs of 78 to 113 - the spread
  // is the mix, a CERATOP-heavy roll costing more than a skitter-heavy one -
  // so 24 sits a box and a half over the worst roll seen and a fifth more
  // boxes on the trash bodies fails it on any roll.
  ok("the horde's cost per enemy stays bounded",
     per <= 24,
     `${per.toFixed(1)} boxes each across ${hordeOnly.enemies} enemies ` +
     `(${hordeOnly.horde} of ${hordeOnly.boxes} in the frame are the horde's, ` +
     `${hordeOnly.corpses} the fallen's)`);
  // and a ceiling on a counter that reads zero is no ceiling: the cheapest
  // trash body at the far LOD is still several boxes, so a per-enemy figure
  // under eight means the loop is not being counted, not that it got cheap
  ok("and the count is the horde's own - a standing enemy is never under eight boxes",
     per >= 8, `${per.toFixed(1)} a head`);
  ok("and the frame still fits two flushes without a boss",
     hordeOnly.boxes > 0 && hordeOnly.boxes <= 7200, `${hordeOnly.boxes} boxes`);

  console.log("\n=== 12. RENDER + PERFORMANCE UNDER LOAD ===");
  await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god(); window.__g.skipTo(900);
    for (const w of ["bat","skulls","bolt","pulse","mortar","zap"]) window.__g.give(w, 4);
    window.__g.spawn("shambler", 200); window.__g.spawn("skitter", 150);
    window.__g.boss(2);
  });
  await page.waitForTimeout(1600);
  const perf = await page.evaluate(async () => {
    let frames = 0;
    const t0 = performance.now();
    await new Promise(r => {
      const tick = () => { frames++;
        performance.now() - t0 < 1500 ? requestAnimationFrame(tick) : r(); };
      requestAnimationFrame(tick);
    });
    return { fps: frames / ((performance.now() - t0) / 1000), ...window.__g.state() };
  });
  ok("renders a heavy frame", perf.enemies > 100, "enemies=" + perf.enemies);
  console.log(`  ~${perf.fps.toFixed(1)} fps with ${perf.enemies} enemies, ` +
              `${perf.boxes} boxes (software GL - real GPU is far higher)`);
  await page.screenshot({ path: "shot-combat.png" });

  console.log("\n=== 12b. CAMERA AT THE ARENA EDGE ===");
  // The chase boom is 17 units long; at the arena edge that used to put the eye
  // inside the boundary spires and the whole frame rendered as fog.
  //
  // Two things were wrong with the version this replaces. The coordinates were
  // (0,71) and (71,71), written when RIM was 84 - after the map went up ten
  // times those are a third of the way out, so "corner" was testing the middle
  // of the map. And the measure was "how much of the bottom half differs from
  // the sky", which is a colour comparison against seven ground palettes rolled
  // fresh every run: it read 100/100/50 on one run and passed on the next, not
  // because the camera moved but because the dice did.
  //
  // What the check is actually for is that the eye does not end up buried, with
  // the frame rendering as one flat fill. So measure STRUCTURE, which no ground
  // palette can take away: the bottom half has to carry many distinct colours
  // AND read differently from the top half. Both collapse to ~0 in fog.
  {
    const rim = await page.evaluate(() => window.__g.rim());
    const out = Math.round(rim - 8), diag = Math.round((rim - 8) / Math.SQRT2);
    for (const [label, x, z] of [["centre", 0, 0], ["edge", 0, out], ["corner", diag, diag]]) {
      await page.evaluate(([x, z]) => {
        window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
        window.__g.freezeSpawns(true); window.__g.bot(false);
        window.__g.place(x, z); window.__g.step(20); window.__g.resume();
      }, [x, z]);
      await page.waitForTimeout(260);
      const shot = await page.screenshot();
      const m = await page.evaluate(async b64 => {
        const img = new Image();
        await new Promise(r => { img.onload = r; img.src = "data:image/png;base64," + b64; });
        const c = document.createElement("canvas"); c.width = img.width; c.height = img.height;
        const g = c.getContext("2d"); g.drawImage(img, 0, 0);
        const d = g.getImageData(0, 0, c.width, c.height).data;
        const w = c.width, h = c.height, at = (x, y) => (y * w + x) * 4;
        const band = (y0, y1) => {
          const seen = new Set(); let r = 0, gg = 0, b = 0, n = 0;
          for (let y = y0; y < y1; y += 3) for (let x = 0; x < w; x += 6) {
            const i = at(x, y);
            r += d[i]; gg += d[i+1]; b += d[i+2]; n++;
            seen.add(((d[i] >> 4) << 8) | ((d[i+1] >> 4) << 4) | (d[i+2] >> 4));
          }
          return { tones: seen.size, r: r/n, g: gg/n, b: b/n };
        };
        const top = band(2, Math.floor(h * 0.20)), bot = band(Math.floor(h * 0.60), h);
        return { tones: bot.tones,
                 split: Math.abs(bot.r-top.r) + Math.abs(bot.g-top.g) + Math.abs(bot.b-top.b) };
      }, shot.toString("base64"));
      ok(`the camera is not buried at the ${label}`, m.tones >= 12 && m.split > 24,
         `${m.tones} distinct tones below the horizon, ${m.split.toFixed(0)} apart from the sky`);
    }
    // And the eye itself, which is the thing that actually breaks: a boom that
    // reaches past the wall is a fog frame no pixel test can un-bury.
    const eyes = await page.evaluate(async () => {
      const g = window.__g, rim = g.rim(), out = rim - 8, worst = [];
      for (let i = 0; i < 16; i++) {
        const a = i * Math.PI / 8;
        g.start("intern"); g.god(); g.drainPicks(true); g.freezeSpawns(true); g.bot(false);
        g.place(Math.cos(a) * out, Math.sin(a) * out); g.step(20); g.resume();
        await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
        const e = g.eye();
        worst.push(Math.hypot(e[0], e[2]));
      }
      return { rim, max: Math.max(...worst) };
    });
    ok("and the eye never reaches the wall from any bearing",
       eyes.max < eyes.rim - 1, `worst eye radius ${eyes.max.toFixed(1)} against RIM ${eyes.rim}`);
  }

  console.log("\n=== 13. NON-BLANK RENDER CHECK ===");
  const shot = await page.screenshot({ path: "shot-check.png" });
  const varied = await page.evaluate(async b64 => {
    const img = new Image();
    await new Promise(r => { img.onload = r; img.src = "data:image/png;base64," + b64; });
    const c = document.createElement("canvas");
    c.width = img.width; c.height = img.height;
    const x = c.getContext("2d"); x.drawImage(img, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height).data;
    const seen = new Set();
    for (let i = 0; i < d.length; i += 4 * 37)
      seen.add((d[i] >> 3) + "," + (d[i+1] >> 3) + "," + (d[i+2] >> 3));
    return seen.size;
  }, shot.toString("base64"));
  ok("frame is a real rendered scene", varied > 60, varied + " distinct colours sampled");

  console.log("\n=== 14. INPUT SMOKE TEST ===");
  await page.evaluate(() => window.__g.start("intern"));
  await page.waitForTimeout(100);
  const p0 = await page.evaluate(() => ({ x: window.__g.state(), k: window.__g.kit() }));
  await page.keyboard.down("KeyW");
  await page.waitForTimeout(500);
  await page.keyboard.up("KeyW");
  await page.keyboard.press("Space");
  await page.waitForTimeout(200);
  ok("keyboard input does not throw", errors.length === 0, errors.slice(0,2).join(" | "));

  console.log("\n=== 15. TOUCH CONTROLS (phone-sized, touch-enabled context) ===");
  {
    const ctx = await browser.newContext({
      viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true,
      // deviceScaleFactor 1, not 3: at 3 the canvas is 1170x2532, SwiftShader
      // crawls, and the dt clamp turns the run into slow motion - so the test
      // ends up measuring the software rasteriser instead of the controls.
      deviceScaleFactor: 1,
    });
    const mp = await ctx.newPage();
    const merr = [];
    mp.on("pageerror", e => merr.push(e.message));
    await mp.goto(FILE, { waitUntil: "load" });
    await mp.waitForTimeout(600);

    // One event per call. The previous version returned a page-side closure from
    // evaluate() to fire touchend later - functions do not serialise across that
    // boundary, so touchend was NEVER dispatched and both tap-to-jump and stick
    // release went untested while the docs claimed touch was covered.
    const fire = (type, x, y, id) => mp.evaluate(([type, x, y, id]) => {
      const cv = document.getElementById("gl");
      const t = new Touch({ identifier: id, target: cv, clientX: x, clientY: y });
      cv.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true,
        touches: type === "touchend" ? [] : [t], changedTouches: [t] }));
    }, [type, x, y, id]);
    const drag = async (x0, y0, x1, y1, id) => {
      await fire("touchstart", x0, y0, id);
      for (let i = 1; i <= 8; i++)
        await fire("touchmove", x0 + (x1-x0)*i/8, y0 + (y1-y0)*i/8, id);
    };

    ok("detects a touch device", await mp.evaluate(() => window.__g.hasTouch()));
    ok("mobile boot is clean", merr.length === 0, merr.slice(0, 2).join(" | "));

    await mp.evaluate(() => { window.__g.wipeSave(); window.__g.start("intern"); });
    await mp.waitForTimeout(150);
    ok("touch start does not leave the game paused",
       await mp.evaluate(() => !window.__g.isPaused()));

    // left half = movement stick. Hold it, then step a fixed number of ticks;
    // waiting on wall-clock made this flaky because the context is render-bound.
    const before = await mp.evaluate(() => window.__g.state());
    await drag(90, 600, 90, 480, 1);                    // full deflection forward
    const moved = await mp.evaluate(([bx, bz]) => {
      window.__g.step(120);
      const a = window.__g.state();
      return Math.hypot(a.x - bx, a.z - bz);
    }, [before.x, before.z]);
    ok("left-thumb stick moves the player", moved > 8,
       `moved ${moved.toFixed(1)}m in 2 simulated seconds`);

    // the stick is analog: a small push must travel measurably less far
    await fire("touchend", 90, 480, 1);
    const small = await mp.evaluate(() => window.__g.state());
    await drag(90, 600, 90, 578, 3);                    // ~22px, just over dead zone
    const movedSmall = await mp.evaluate(([bx, bz]) => {
      window.__g.step(120);
      const a = window.__g.state();
      return Math.hypot(a.x - bx, a.z - bz);
    }, [small.x, small.z]);
    ok("the stick is analog, not on/off", movedSmall < moved * 0.75,
       `${movedSmall.toFixed(1)}m at part deflection vs ${moved.toFixed(1)}m at full`);

    // releasing must actually stop you
    await fire("touchend", 90, 578, 3);
    const rel = await mp.evaluate(() => window.__g.state());
    const drift = await mp.evaluate(([bx, bz]) => {
      window.__g.step(120);
      const a = window.__g.state();
      return Math.hypot(a.x - bx, a.z - bz);
    }, [rel.x, rel.z]);
    ok("releasing the stick stops the player", drift < 0.5, `drifted ${drift.toFixed(2)}m`);

    // right half = camera
    const yaw0 = await mp.evaluate(() => window.__g.camYaw());
    await drag(300, 400, 180, 400, 2);
    await fire("touchend", 180, 400, 2);
    const yaw1 = await mp.evaluate(() => window.__g.camYaw());
    ok("right-thumb drag turns the camera", Math.abs(yaw1 - yaw0) > 0.15,
       `yaw ${yaw0.toFixed(2)} -> ${yaw1.toFixed(2)}`);

    // a quick tap on the right jumps
    const jumped = await mp.evaluate(async () => {
      const cv = document.getElementById("gl");
      const mk = () => new Touch({ identifier: 9, target: cv, clientX: 300, clientY: 500 });
      cv.dispatchEvent(new TouchEvent("touchstart", { bubbles:true, cancelable:true,
        touches:[mk()], changedTouches:[mk()] }));
      cv.dispatchEvent(new TouchEvent("touchend", { bubbles:true, cancelable:true,
        touches:[], changedTouches:[mk()] }));
      // Jump input is BUFFERED now, so a tap arms it and the next step spends
      // it. Reading isAirborne() straight off the touchend read false and would
      // have gone on reading false however broken the jump was.
      const armed = window.__g.hop().buf > 0;
      window.__g.step(1/60);
      return { armed, air: window.__g.isAirborne() };
    });
    ok("a tap on the right arms a jump", jumped.armed === true, `buf armed=${jumped.armed}`);
    ok("a tap on the right jumps", jumped.air === true, `airborne=${jumped.air}`);

    // a phone has no Escape key, so the pause button has to exist and work
    const paused = await mp.evaluate(() => {
      const pb = document.getElementById("pausebtn");
      if (!pb || getComputedStyle(pb).display === "none") return "missing";
      pb.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      return window.__g.isPaused();
    });
    ok("the pause button exists and works on touch", paused === true, `result=${paused}`);

    // while the pause screen is up: the copy speaks touch, and the cheats hide
    // (fresh save, so DEV MODE is off - the strip must not exist visually)
    const pcopy = await mp.evaluate(() => ({
      sub: document.querySelector("#paused .sub").textContent,
      dev: getComputedStyle(document.getElementById("dev")).display }));
    ok("the pause headline speaks touch, not mouse", pcopy.sub === "tap to resume",
       JSON.stringify(pcopy.sub));
    ok("no cheat strip on a fresh player's pause screen", pcopy.dev === "none",
       `display=${pcopy.dev}`);

    // a thumb still held when the run ends must not steer the next one
    await drag(90, 600, 90, 470, 7);
    const carried = await mp.evaluate(() => {
      window.__g.start("intern");            // retry with the thumb still down
      const b = window.__g.state();
      window.__g.step(90);
      const a = window.__g.state();
      return Math.hypot(a.x - b.x, a.z - b.z);
    });
    ok("a held thumb does not steer the next run", carried < 0.5,
       `drifted ${carried.toFixed(2)}m after restart`);
    await fire("touchend", 90, 470, 7);

    // SHOP on the end screen must land on the SHOP - on a phone the upgrades
    // sit below nine monster cards, so "open the menu at the top" is not it
    const landed = await mp.evaluate(() => {
      const g = window.__g;
      g.hitMe(1e12); g.step(2, 1/60);        // die, so the end screen is real
      document.getElementById("shopBtn").click();
      const r = document.getElementById("shop").getBoundingClientRect();
      return { over: g.state().over, top: Math.round(r.top), vh: innerHeight };
    });
    ok("the end screen's SHOP button lands on the shop",
       landed.over === true && landed.top >= 0 && landed.top < landed.vh * .8,
       `over=${landed.over}, shop top at ${landed.top}px of ${landed.vh}`);

    await mp.screenshot({ path: "shot-mobile.png" });
    ok("no errors from touch handling", merr.length === 0, merr.slice(0, 2).join(" | "));
    await ctx.close();
  }

  console.log("\n=== 15b. INPUT PATHS DO NOT EXCLUDE EACH OTHER ===");
  {
    // A touchscreen laptop has both a mouse and a digitiser, and this harness
    // CANNOT emulate that: Playwright's hasTouch context reports
    // (any-pointer:fine)=false and pointer:coarse - byte-identical to a phone.
    // So testing the capability guess is impossible here, which is the argument
    // for not having one. What IS testable is the mechanism that replaced it:
    // the auto-pause must key off a lock actually held, never off a guess.
    const ctx = await browser.newContext({
      viewport: { width: 1280, height: 800 }, hasTouch: true, isMobile: false });
    const lp = await ctx.newPage();
    const lerr = [];
    lp.on("pageerror", e => lerr.push(e.message));
    await lp.goto(FILE, { waitUntil: "load" });
    await lp.waitForTimeout(500);
    const r = await lp.evaluate(() => {
      window.__g.wipeSave(); window.__g.start("intern");
      return { paused: window.__g.isPaused(), hadLock: window.__g.hadLock() };
    });
    await lp.waitForTimeout(500);
    const still = await lp.evaluate(() => window.__g.isPaused());
    ok("a device that never gets pointer lock is not auto-paused",
       r.paused === false && still === false, `paused=${r.paused} then ${still}`);
    ok("and it knows it never held the lock", r.hadLock === false);
    ok("no errors in the both-inputs case", lerr.length === 0, lerr.slice(0,2).join(" | "));
    await ctx.close();
  }

  console.log("\n=== 7g. WEAPONS REACH THE BODY, NOT THE CENTRE ===");
  {
    // Every enemy hits the player at `e.rad + .75` - it counts its own body.
    // Weapons did not: they measured centre-to-centre, so a target shrugged off
    // exactly its own radius worth of reach, and the biggest boss shrugged off
    // the most.
    // WITHOUT NAMING A RADIUS. This block used to probe at 6.5 + bossRad, the
    // 6.5 copied out of STINK's table, and when STINK was retuned to 9.4 the
    // "outside" probe survived by ten centimetres - it was one tweak away from
    // going red for the same reason section 7i actually did. The claim does not
    // need the weapon's number at all: if reach counts the target's BODY, then
    // measuring the boundary against two bosses of DIFFERENT sizes has to give
    // two boundaries differing by exactly the difference in their radii. That
    // is true whatever the weapon's radius is, and it is false the moment
    // anything goes back to measuring centre-to-centre.
    const probe = (bi, gap) => page.evaluate(([bi, gap]) => {
      window.__g.wipeSave(); window.__g.start("ghoul"); window.__g.god();
      window.__g.drainPicks(true); window.__g.freezeSpawns(true);
      window.__g.give("aura", 4);
      window.__g.boss(bi);
      // Let it finish arriving. A boss is buried and untouchable for its first
      // 1.5s now, and these probes run for exactly 90 frames - which is 1.5s,
      // so all of them were measuring damage against something immune.
      window.__g.step(120);
      const b0 = window.__g.bossAt();
      for (let i = 0; i < 90; i++) {
        const b = window.__g.bossAt(); if (!b) break;
        window.__g.place(b.x + gap, b.z);
        window.__g.step(1);
      }
      const b1 = window.__g.bossAt();
      return { rad: b0.rad, lost: b0.hp - (b1 ? b1.hp : 0) };
    }, [bi, gap]);
    const edge = async (bi) => {
      let lo = 1, hi = 40;
      for (let i = 0; i < 9; i++) {
        const mid = (lo + hi) / 2;
        if ((await probe(bi, mid)).lost > 0) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    };
    const bigRad = (await probe(3, 40)).rad, smallRad = (await probe(0, 40)).rad;
    const bigEdge = await edge(3), smallEdge = await edge(0);

    ok("the two bosses really are different sizes",
       bigRad - smallRad > 0.5, `${bigRad}m vs ${smallRad}m`);
    ok("a bigger body is reached from further out, by exactly its extra radius",
       Math.abs((bigEdge - smallEdge) - (bigRad - smallRad)) < 0.5,
       `boundaries ${bigEdge.toFixed(1)}m and ${smallEdge.toFixed(1)}m differ by ` +
       `${(bigEdge - smallEdge).toFixed(1)}m, radii differ by ${(bigRad - smallRad).toFixed(1)}m`);
    ok("a body inside the ring takes damage though its centre is outside",
       (await probe(3, bigEdge - 1)).lost > 0 && bigEdge - 1 > bigRad,
       `centre ${(bigEdge - 1).toFixed(1)}m out, body only ${bigRad}m thick`);
    ok("a body clear of the ring takes none",
       (await probe(3, bigEdge + 2)).lost === 0, `nothing at ${(bigEdge + 2).toFixed(1)}m`);
    ok("and reach is not simply infinite", (await probe(3, 40)).lost === 0);
  }

  console.log("\n=== 7i. THE SCRAPPER'S REACH IS A REAL STAT ===");
  {
    // MEASURE THE BOUNDARY, do not hardcode where it should be. This block used
    // to read "6.5m STINK + 4.0m body puts everyone else's boundary at 10.5m"
    // and probe at fixed gaps of 11.6 and 13.5 either side of it - numbers
    // copied out of the weapon table. Retuning STINK's radius moved every one
    // of those boundaries and turned two correct assertions red, which is a
    // test failing for the one reason a test must not: the thing it measures
    // moved and it was still looking at the old address.
    // It finds each character's boundary by bisection now and checks the STAT,
    // which is what the section is actually about: reach multiplies the
    // weapon's radius, so the extra distance THE SCRAPPER gets has to be 35% of
    // the radius - recovered from its own boundary minus the boss's body -
    // whatever that radius happens to be this month.
    const probe = (ch, gap) => page.evaluate(([ch, gap]) => {
      window.__g.wipeSave(); window.__g.start(ch); window.__g.god();
      window.__g.drainPicks(true); window.__g.freezeSpawns(true);
      window.__g.give("aura", 4); window.__g.boss(3);
      window.__g.step(120);                 // let it finish arriving; see above
      const b0 = window.__g.bossAt();
      for (let i = 0; i < 90; i++) {
        const b = window.__g.bossAt(); if (!b) break;
        window.__g.place(b.x + gap, b.z); window.__g.step(1);
      }
      return { dmg: b0.hp - window.__g.bossAt().hp, rad: b0.rad };
    }, [ch, gap]);
    // largest gap that still connects, to a tenth of a metre
    const boundary = async (ch) => {
      let lo = 1, hi = 40;
      for (let i = 0; i < 9; i++) {
        const mid = (lo + hi) / 2;
        if ((await probe(ch, mid)).dmg > 0) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    };
    const bIntern = await boundary("intern"), bScrap = await boundary("scrap");
    const bossRad = (await probe("intern", 4)).rad;
    const radius  = bIntern - bossRad;           // the weapon's own reach
    const want    = radius * 1.35 + bossRad;     // what +35% has to buy
    ok("THE SCRAPPER reaches further than everyone else",
       bScrap > bIntern + 0.5,
       `intern ${bIntern.toFixed(1)}m, scrapper ${bScrap.toFixed(1)}m`);
    ok("and the extra distance is exactly the +35% reach stat",
       Math.abs(bScrap - want) < 0.6,
       `radius ${radius.toFixed(1)}m + boss ${bossRad.toFixed(1)}m -> expected ` +
       `${want.toFixed(1)}m, measured ${bScrap.toFixed(1)}m`);
    ok("and reach is a boundary, not an absence of one",
       bScrap < 39 && (await probe("scrap", bScrap + 3)).dmg === 0,
       `nothing lands ${(bScrap + 3).toFixed(1)}m out`);
    ok("and both connect well inside it", (await probe("intern", 8)).dmg > 0 &&
                                          (await probe("scrap",  8)).dmg > 0);
  }

  console.log("\n=== 7h. OVERLAPPING HAZARDS STACK, BUT NOT WITHOUT LIMIT ===");
  {
    // SCORCHED EARTH is a trail laid over itself; stacking IS the weapon, and
    // capping a body to one zone dropped it from best boss weapon to worst.
    // What has to be bounded is the stack a LARGE body can sit inside, so this
    // measures damage against zone count and asserts it plateaus at the cap
    // rather than scaling forever.
    const burn = n => page.evaluate((n) => {
      window.__g.wipeSave(); window.__g.start("intern"); window.__g.god();
      window.__g.drainPicks(true); window.__g.freezeSpawns(true);
      window.__g.boss(3);
      // Let it finish arriving. A boss is buried and untouchable for its first
      // 1.5s now, and these probes run for exactly 90 frames - which is 1.5s,
      // so all of them were measuring damage against something immune.
      window.__g.step(120);
      const b0 = window.__g.bossAt();
      window.__g.zones(b0.x, b0.z, n, 400);
      window.__g.step(30);                       // half a second: two windows
      const b1 = window.__g.bossAt();
      return b0.hp - b1.hp;
    }, n);

    // Counts are FIXED, not derived from the cap. Deriving them let a mutation
    // that set the cap to 9999 survive: both probes then killed the boss
    // outright, both readings clamped to its HP pool, and "no more than the
    // cap" passed on two saturated numbers that measured nothing.
    const cap = await page.evaluate(() => window.__g.burnStack());
    const one    = await burn(1);
    const atCap  = await burn(3);
    const over   = await burn(12);

    ok("the cap is the three this test is written against", cap === 3, `cap=${cap}`);
    ok("one zone burns", one > 0, `${Math.round(one)} HP`);
    ok("three zones do three times one",
       Math.abs(atCap - one * 3) <= one * 0.05,
       `${Math.round(one)} -> ${Math.round(atCap)} HP`);
    ok("twelve zones do no more than three",
       Math.abs(over - atCap) <= atCap * 0.05,
       `${Math.round(atCap)} vs ${Math.round(over)} HP`);
    ok("and the boss survived all three probes, so nothing is clamped",
       await page.evaluate(() => window.__g.bossAt() !== null));
  }

  console.log("\n=== 12c. THE GPU CAN BE TAKEN AWAY AND GIVEN BACK ===");
  {
    // A mobile browser reclaims the GPU when you switch apps. Lost-context GL
    // calls fail SILENTLY rather than throwing, so with no handler the canvas
    // is black forever while the simulation carries on behind it - which reads
    // as a crash. This drives the real thing through WEBGL_lose_context.
    const ctx = await browser.newContext({ viewport: { width: 900, height: 600 } });
    const cp = await ctx.newPage();
    const cerr = [];
    cp.on("pageerror", e => cerr.push(e.message));
    await cp.goto(FILE, { waitUntil: "load" });
    await cp.waitForTimeout(500);
    await cp.evaluate(() => { window.__g.wipeSave(); window.__g.start("intern");
                              window.__g.god(); window.__g.step(60 * 40); });
    await cp.waitForTimeout(400);

    const before = await cp.evaluate(() => window.__g.state().boxes);
    const shotA  = await cp.screenshot({ type: "png" });

    await cp.evaluate(() => window.__g.loseCtx());
    await cp.waitForTimeout(300);
    const lost = await cp.evaluate(() => ({ lost: window.__g.ctxLost(),
                                            paused: window.__g.isPaused() }));
    // A lost context keeps its last drawing buffer on screen and drawnBoxes
    // keeps its last value, so "it renders" and "it isn't blank" both pass on a
    // corpse. Park the counter and move the camera: only a LIVE frame can
    // reset one and change the other.
    await cp.evaluate(() => window.__g.clearBoxes());
    const stale = await cp.evaluate(() => window.__g.state().boxes);

    await cp.evaluate(() => window.__g.restoreCtx());
    await cp.waitForTimeout(800);
    const back = await cp.evaluate(() => window.__g.ctxLost());
    await cp.evaluate(() => { window.__g.resume(); window.__g.place(-40, -40); });
    await cp.waitForTimeout(800);
    const after = await cp.evaluate(() => window.__g.state().boxes);
    const shotB = await cp.screenshot({ type: "png" });
    const hues  = new Set();
    for (let i = 0; i < shotB.length - 4; i += 997) hues.add(shotB.readUInt32BE(i));

    ok("losing the context is noticed, not ignored", lost.lost === true);
    ok("and it pauses instead of playing on behind a black screen", lost.paused === true);
    ok("nothing renders while the context is gone", stale === -1);
    ok("restore clears the lost flag", back === false);
    ok("a live frame draws after restore", after > 0 && before > 0,
       `${before} boxes before, parked at ${stale}, ${after} after`);
    ok("the restored frame is not a blank screen", hues.size > 20, `${hues.size} samples`);
    ok("and it is a NEW frame, not the buffer left behind",
       Buffer.compare(shotA, shotB) !== 0);
    ok("nothing threw across loss and restore", cerr.length === 0, cerr.slice(0,2).join(" | "));
    await ctx.close();
  }

  console.log("\n=== 16. COMFORT: SHAKE AND SOUND CAN BE TURNED OFF ===");
  {
    // Getting hit several times a second for twenty minutes means the camera
    // shake and the white flash are the steady state, not a flourish. The OS
    // preference picks the default; both stay switchable; and a page you opened
    // from a link must have a mute that is one key away.
    const shot2 = async (page) => {
      const a = await page.screenshot({ type: "png" });
      await page.waitForTimeout(120);
      const b = await page.screenshot({ type: "png" });
      return Buffer.compare(a, b) !== 0;              // did the frame jitter?
    };
    const boot = async (reducedMotion) => {
      const ctx = await browser.newContext({ viewport:{width:800,height:520}, reducedMotion });
      const pg = await ctx.newPage();
      await pg.goto(FILE, { waitUntil: "load" });
      await pg.waitForTimeout(450);
      return { ctx, pg };
    };

    const R = await boot("reduce");
    await R.pg.evaluate(() => window.__g.wipeSave());
    await R.pg.reload({ waitUntil: "load" });
    await R.pg.waitForTimeout(700);
    const rDefault = await R.pg.evaluate(() => window.__g.opts());
    ok("prefers-reduced-motion picks the default", rDefault.motion === 0,
       JSON.stringify(rDefault));

    // Hold the world genuinely still, crank the shake, and see whether the frame
    // moves. The first version of this skipped the pause and passed anyway,
    // because the harness happened to leave the game paused - a test that was
    // right for a reason it did not state, and therefore a coin flip.
    await R.pg.evaluate(() => { window.__g.start("intern"); window.__g.god();
                                window.__g.step(60 * 20);
                                // if a level-up draft opened on the very last
                                // frame, picking=true makes pause(true) refuse
                                // (the strip is already a pause) - and this
                                // check is about SHAKE, not drafts. The fauna
                                // lean re-rolled the XP timing dice here.
                                window.__g.drainPicks();
                                window.__g.pause(true); });
    await R.pg.waitForTimeout(150);
    ok("the world is actually frozen for this comparison",
       await R.pg.evaluate(() => window.__g.isPaused()) === true);
    await R.pg.evaluate(() => { window.__g.setOpt("motion", 0); window.__g.setShake(1.4); });
    await R.pg.waitForTimeout(200);
    const stillOff = await shot2(R.pg);
    await R.pg.evaluate(() => { window.__g.setOpt("motion", 1); window.__g.setShake(1.4); });
    await R.pg.waitForTimeout(200);
    const stillOn = await shot2(R.pg);
    ok("shake off holds the camera perfectly still", stillOff === false);
    ok("shake on moves it", stillOn === true);

    const gains = await R.pg.evaluate(() => {
      window.__g.setOpt("sound", 1); const on = window.__g.gain();
      window.__g.setOpt("sound", 0); const off = window.__g.gain();
      return { on, off };
    });
    ok("muting takes the master gain to zero", gains.off === 0 && gains.on > 0,
       `on=${gains.on} off=${gains.off}`);

    await R.pg.evaluate(() => { window.__g.setOpt("sound", 0);
                                window.__g.setOpt("motion", 1); });
    await R.pg.reload({ waitUntil: "load" });
    await R.pg.waitForTimeout(700);
    const kept = true;
    const after = await R.pg.evaluate(() => window.__g.opts());
    ok("both choices survive a reload", kept && after.sound === 0 && after.motion === 1,
       JSON.stringify(after));
    await R.ctx.close();

    const N = await boot("no-preference");
    await N.pg.evaluate(() => window.__g.wipeSave());
    await N.pg.reload({ waitUntil: "load" });
    await N.pg.waitForTimeout(700);
    const nDefault = await N.pg.evaluate(() => window.__g.opts());
    ok("no preference leaves shake on", nDefault.motion === 1, JSON.stringify(nDefault));
    await N.ctx.close();
  }

  console.log("\n=== 12d. THE CAMERA CHASES, IT IS NOT WELDED ===");
  {
    // A boom recomputed from the player's exact position every frame pins you
    // to the dead centre of the screen forever, which means no acceleration you
    // ever make is visible. That was most of what "clunky" meant here. The
    // anchor has to trail the player and then catch up.
    const ctx = await browser.newContext({ viewport: { width: 900, height: 600 } });
    const cp = await ctx.newPage();
    await cp.goto(FILE, { waitUntil: "load" });
    await cp.waitForTimeout(450);
    await cp.evaluate(() => { window.__g.wipeSave(); window.__g.start("intern");
                              window.__g.god(); window.__g.place(0, 0); });
    // Every read here is frame-counted and null-tolerant, because camAnchor is
    // null until render() has run once and this suite shares a machine. The
    // first two versions of this check were both wrong for the same reason in
    // different costumes - 50ms with nothing drawn reads 0.00 and passes a
    // welded camera; 1400ms with a bench hogging the CPU reads 28.42 and fails
    // a working one; and a 500ms settle under real load reads null and takes
    // the whole harness down.
    const untilAnchor = (test, cap = 900) => cp.evaluate(([src, cap]) => new Promise(res => {
      const pass = new Function("a", src);
      let n = 0;
      const tick = () => {
        const a = window.__g.camAnchor();
        if ((a && pass(a)) || ++n > cap) return res(a);
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }), [test, cap]);

    const settled = await untilAnchor("return Math.abs(a[0]) < 0.05");
    const lagged  = await cp.evaluate(() => new Promise(res => {
      window.__g.place(30, 0);
      let n = 0;
      const tick = () => (++n < 4) ? requestAnimationFrame(tick)
                                   : res(window.__g.camAnchor());
      requestAnimationFrame(tick);
    }));
    const caught  = await untilAnchor("return Math.abs(a[0] - 30) < 0.5");

    // A null anchor means no frame ever rendered, which is a FAILURE and not a
    // crash - it is exactly the state that used to make this section pass.
    ok("the anchor starts on the player", !!settled && Math.abs(settled[0]) < 1.5,
       `x=${settled ? settled[0].toFixed(2) : "no frame rendered"}`);
    ok("it does not teleport with them",
       !!lagged && lagged[0] > 0.5 && lagged[0] < 26,
       `x=${lagged ? lagged[0].toFixed(2) : "no frame"} of 30 after three frames`);
    ok("but it does get there", !!caught && Math.abs(caught[0] - 30) < 1.5,
       `x=${caught ? caught[0].toFixed(2) : "no frame"}`);
    await ctx.close();
  }

  console.log("\n=== 18. SIDE EVENTS ===");
  {
    const at = (kind, dx, dz) => page.evaluate(([kind,dx,dz]) => {
      window.__g.wipeSave(); window.__g.start("intern"); window.__g.god();
      window.__g.drainPicks(true); window.__g.freezeSpawns(true);
      window.__g.freezeEvents(true); window.__g.place(0,0);
      window.__g.spawnEvent(kind, dx, dz);
      return window.__g.events().length;
    }, [kind,dx,dz]);

    ok("a cache can be placed", (await at("cache", 20, 0)) === 1);

    // walking into it opens it; standing near it does not
    const cache = await page.evaluate(() => {
      // step(4) is ONE four-second step, which flings every gem 176 metres past
      // you in a single frame - so whether this passed came down to how many of
      // the nine happened to land inside the 1.1m pickup ring on the frame they
      // spawned. It read "+1 levels" for months and "+0" the day an unrelated
      // change consumed fewer Math.random() calls at page load and shifted the
      // whole stream. Step it properly and measure XP, not a level boundary.
      const before = window.__g.state(), xp0 = window.__g.xpBanked();
      window.__g.place(14, 0);
      for (let i = 0; i < 90; i++) window.__g.step(1/60);   // 6m away
      const far = window.__g.events().length;
      window.__g.place(20, 0);
      for (let i = 0; i < 150; i++) window.__g.step(1/60);  // on top of it
      return { far, after: window.__g.events().length,
               levels: window.__g.state().lvl - before.lvl,
               xp: window.__g.xpBanked() - xp0,
               picking: window.__g.state().picking };
    });
    ok("a cache six metres away stays shut", cache.far === 1);
    ok("walking into it opens it", cache.after === 0);
    ok("and it pays out a level-up",
       cache.picking === true || cache.levels > 0 || cache.xp > 0,
       `picking=${cache.picking} +${cache.levels} levels +${cache.xp} XP`);

    await at("altar", 20, 0);
    // READ THE CHARGE, DO NOT ASSUME THERE IS ONE. This block used to index
    // events()[0] directly, which is fine while the altar behaves and fatal
    // when it does not: an altar that charges from anywhere completes during
    // the first sample and events() is empty, so the next line read .chg off
    // undefined and the whole HARNESS died. A dead harness prints no RESULT
    // line, and no RESULT line is not a failing test - the mutation audit
    // scores it as no data, which is the same column as a hole. A check that
    // cannot report its own failure is worth less than one that can, so this
    // reports -1 for "the altar was already gone" and lets the assertions below
    // fail on it in the ordinary way.
    const altar = await page.evaluate(() => {
      const chg = () => { const e = window.__g.events()[0]; return e ? e.chg : -1; };
      window.__g.place(14, 0); window.__g.step(120);        // 6m away, two seconds
      const idle = chg();
      window.__g.place(20, 0); window.__g.step(90);         // standing in it
      const part = chg();
      window.__g.place(0, 0);  window.__g.step(60);         // walked off again
      const bled = chg();
      window.__g.place(20, 0); window.__g.step(60 * 7);     // hold it out
      return { idle, part, bled, left: window.__g.events().length,
               boons: window.__g.boons() };
    });
    ok("an altar does not charge from six metres away", altar.idle === 0,
       altar.idle === -1 ? "the altar had already completed itself" : `${altar.idle}`);
    ok("standing in it charges it", altar.part > 1, `${altar.part}s`);
    ok("stepping out bleeds progress rather than resetting it",
       altar.bled < altar.part && altar.bled > 0, `${altar.part} -> ${altar.bled}`);
    ok("holding it out grants a boon",
       altar.left === 0 && altar.boons.length === 1, altar.boons.join());

    // the failure a naive implementation ships: every stat here is recomputed
    // from scratch on the next passive pick, so a boon written onto P alone
    // survives until your next level-up and then quietly evaporates
    // The failure a naive implementation ships: every one of these stats is
    // recomputed from scratch on the next passive pick, so a boon written onto
    // P alone survives until your next level-up and then quietly evaporates.
    //
    // A first version of this used give("tempo", 0) as the passive pick. That
    // is a no-op - cooldown stayed at exactly 1 - so the assertion passed
    // without ever triggering the recompute it existed to survive. Assert the
    // PRODUCT instead: boon-then-passive must equal passive alone times the
    // boon's own multiplier, which can only hold if both are in one calculation.
    const durable = await page.evaluate(() => {
      const boot = () => { window.__g.wipeSave(); window.__g.start("intern");
                           window.__g.god(); window.__g.freezeEvents(true);
                           window.__g.freezeSpawns(true); window.__g.place(0,0); };
      const out = {};
      boot(); out.baseCd = window.__g.state().cd;
      boot(); window.__g.give("tempo", 2); out.tempoCd = window.__g.state().cd;
      boot(); window.__g.grantBoon("QUICK HANDS");
      out.boonCd = window.__g.state().cd;
      window.__g.give("tempo", 2); out.bothCd = window.__g.state().cd;
      boot(); window.__g.give("boots", 2); out.bootsSpd = window.__g.state().spd;
      boot(); window.__g.grantBoon("LIGHT FEET");
      window.__g.give("boots", 2); out.bothSpd = window.__g.state().spd;
      return out;
    });
    ok("the passive pick really does recompute the stat",
       durable.tempoCd < durable.baseCd * 0.95,
       `${durable.baseCd} -> ${durable.tempoCd} with METRONOME 3`);
    ok("QUICK HANDS cuts cooldowns", durable.boonCd < durable.baseCd,
       `${durable.baseCd} -> ${durable.boonCd}`);
    ok("and it survives that recompute, multiplying through it",
       Math.abs(durable.bothCd - durable.tempoCd * 0.93) < 0.004,
       `${durable.tempoCd} x0.93 = ${(durable.tempoCd*0.93).toFixed(3)}, got ${durable.bothCd}`);
    ok("LIGHT FEET multiplies through it too",
       Math.abs(durable.bothSpd - durable.bootsSpd * 1.07) < 0.02,
       `${durable.bootsSpd} x1.07 = ${(durable.bootsSpd*1.07).toFixed(2)}, got ${durable.bothSpd}`);

    // The eighth and ninth boons, each measured at its own outlet. MOSSHIDE
    // is a direct write to the one stat with no recompute rail, so the
    // assertion is the stat; THERMALS re-issues from the constant at every
    // landing, so the assertion is a real landing's window - jump, wait for
    // the ground, read what the landing handed back.
    const nb = await page.evaluate(() => {
      const boot = () => { window.__g.wipeSave(); window.__g.start("intern");
                           window.__g.god(); window.__g.freezeEvents(true);
                           window.__g.freezeSpawns(true); window.__g.place(0,0); };
      const out = {};
      boot(); out.baseRegen = window.__g.mon().regen;
      window.__g.grantBoon("MOSSHIDE"); out.mossRegen = window.__g.mon().regen;
      const land = () => { window.__g.jump();
        for(let i=0;i<200 && !window.__g.isAirborne();i++) window.__g.stepRaw(1/60);
        for(let i=0;i<400 && window.__g.isAirborne();i++) window.__g.stepRaw(1/60);
        return window.__g.hop().win; };
      boot(); out.baseWin = land();
      boot(); window.__g.grantBoon("THERMALS"); out.thermWin = land();
      return out;
    });
    ok("MOSSHIDE adds 1.1 of regeneration",
       Math.abs(nb.mossRegen - nb.baseRegen - 1.1) < .01,
       `${nb.baseRegen}/s -> ${nb.mossRegen}/s`);
    ok("THERMALS holds the landing window open half again longer",
       nb.thermWin > nb.baseWin * 1.35 && nb.thermWin < nb.baseWin * 1.65,
       `a ${nb.baseWin}s window -> ${nb.thermWin}s with THERMALS`);

    // THE COLLECTOR: the only thing in the game that walks away from you
    const hunt = await page.evaluate(() => {
      window.__g.wipeSave(); window.__g.start("intern"); window.__g.god();
      window.__g.drainPicks(true); window.__g.freezeSpawns(true);
      window.__g.freezeEvents(true); window.__g.place(0,0);
      window.__g.spawnEvent("hunt", 8, 0);
      const d0 = window.__g.huntInfo().d;
      const seen = [];
      for (let i = 0; i < 60 * 6; i++) {                 // six seconds of flight
        window.__g.place(0, 0);                          // hold the player still
        window.__g.step(1);
        const h = window.__g.huntInfo(); if (!h) break;
        seen.push(h.d);
      }
      // It must PAUSE, or it is a treadmill. Counting stationary frames was the
      // first attempt and it does not work: a quarry that never rests still
      // produces them in bulk, because any frame where it turns or runs mostly
      // sideways barely changes its DISTANCE from you. Measured against a build
      // with the rest deleted, the count came back 74 and then 103 against a
      // real 167 and then 120 - two overlapping noisy ranges either side of a
      // threshold of 40, so the check passed a treadmill every time.
      // The pause is a CONTIGUOUS thing, which is what separates it from
      // jitter: the longest unbroken run of stationary frames is 78 on the real
      // build - the 1.3s rest, exactly - and 1 without it.
      let stalled = 0, run = 0, longest = 0;
      for (let i = 1; i < seen.length; i++) {
        if (seen[i] - seen[i-1] < 0.002) { stalled++; run++; if (run > longest) longest = run; }
        else run = 0;
      }
      return { d0, d1: seen[seen.length-1], stalledFrames: stalled, longestPause: longest };
    });
    ok("the collector runs away rather than at you", hunt.d1 > hunt.d0 + 8,
       `${hunt.d0}m -> ${hunt.d1}m in six seconds`);
    ok("and it stops often enough to be caught",
       hunt.longestPause > 40,
       `longest unbroken pause ${hunt.longestPause} frames ` +
       `(${hunt.stalledFrames} stationary frames of 360 in total, which is the ` +
       `number that could not tell a rest from jitter)`);

    const paid = await page.evaluate(() => {
      window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
      window.__g.freezeSpawns(true); window.__g.freezeEvents(true);
      window.__g.place(0,0);
      for (const w of ["bat","bolt","zap","mortar"]) window.__g.give(w, 4);
      // state().coins is the SAVED wallet and only moves when a run ends, so
      // asserting on it measured nothing and read +0 against a kill that had
      // definitely happened. coinsRun is the number the reward touches.
      const before = window.__g.runCoins();
      window.__g.spawnEvent("hunt", 5, 0);
      for (let i = 0; i < 60 * 20; i++) {
        window.__g.place(0,0); window.__g.step(1);
        if (!window.__g.huntInfo()) break;
      }
      return { got: window.__g.evStats().hunts, coins: window.__g.runCoins() - before,
               left: window.__g.events().length };
    });
    ok("an armed player kills it", paid.got === 1 && paid.left === 0, JSON.stringify(paid));
    ok("and it pays in coins, which cannot destabilise the run it happened in",
       paid.coins > 100, `+${paid.coins}`);

    const expired = await page.evaluate(() => {
      window.__g.start("intern"); window.__g.god(); window.__g.freezeEvents(true);
      window.__g.place(0,0); window.__g.spawnEvent("cache", 40, 40);
      window.__g.step(60 * 45);
      return window.__g.events().length;
    });
    ok("an event you ignore expires", expired === 0);
  }

  console.log("\n=== 16b. THE MIX TRACKS THE PRESSURE ===");
  {
    // The pulse is the only thing in the game that states the shape of a run
    // out loud, so it has to actually move: quiet and slow on an empty first
    // minute, fast with the arena full at nineteen minutes.
    const bpm = await page.evaluate(() => {
      window.__g.wipeSave(); window.__g.start("intern"); window.__g.god();
      window.__g.freezeSpawns(true); window.__g.drainPicks(true);
      const early = window.__g.bpm();
      window.__g.skipTo(1150); window.__g.spawn("shambler", 240);
      const late = window.__g.bpm();
      return { early, late };
    });
    ok("an empty first minute is slow", bpm.early < 82, bpm.early.toFixed(1));
    ok("a full arena at nineteen minutes is not",
       bpm.late > 150, bpm.late.toFixed(1));
    ok("and it is a curve, not a switch", bpm.late - bpm.early > 60,
       `${bpm.early.toFixed(0)} -> ${bpm.late.toFixed(0)} bpm`);
  }

  console.log("\n=== 17. THE UNLOCK LADDER ===");
  {
    // A locked box with no progress bar is just a locked box, and a ladder that
    // pays out early or never is worse than no ladder. Each rung is checked on
    // both sides of its own threshold.
    const ctx = await browser.newContext({ viewport: { width: 1000, height: 900 } });
    const up = await ctx.newPage();
    await up.goto(FILE, { waitUntil: "load" });
    await up.waitForTimeout(450);

    const probe = (patch) => up.evaluate((patch) => {
      window.__g.wipeSave();
      window.__g.setSave(patch);
      return { got: window.__g.checkUnlocks().map(u => u.id),
               unlocked: window.__g.saveState().unlocked };
    }, patch);

    const shy   = await probe({ best: 599, wins: 0, bestLvl: 29, kills: 5999 });
    ok("nothing pays out one unit short",
       shy.got.length === 0, JSON.stringify(shy.got));

    const ghoul = await probe({ best: 600 });
    ok("10:00 unlocks THE GHOUL", ghoul.got.join() === "ghoul", JSON.stringify(ghoul.got));
    const twin  = await probe({ wins: 1 });
    ok("a clear unlocks THE TWIN", twin.got.join() === "twin", JSON.stringify(twin.got));
    const acc   = await probe({ bestLvl: 30 });
    ok("level 30 unlocks THE ACCOUNTANT", acc.got.join() === "accnt", JSON.stringify(acc.got));
    const tal   = await probe({ kills: 6000 });
    ok("6,000 kills unlocks TALLY", tal.got.join() === "tally", JSON.stringify(tal.got));

    const twice = await up.evaluate(() => {
      window.__g.wipeSave(); window.__g.setSave({ best: 900 });
      const a = window.__g.checkUnlocks().map(u => u.id);
      const b = window.__g.checkUnlocks().map(u => u.id);
      return { a, b };
    });
    ok("a rung pays out once, not every run",
       twice.a.join() === "ghoul" && twice.b.length === 0, JSON.stringify(twice));

    // the shop line is genuinely absent, not merely greyed.
    // Reload through Playwright, not location.reload() inside an evaluate:
    // navigating destroys the context the evaluate is still returning through,
    // which crashes the whole harness the moment the timing shifts.
    await up.evaluate(() => window.__g.wipeSave());
    await up.reload({ waitUntil: "load" });
    await up.waitForTimeout(650);
    const hidden = true;
    const shopBefore = await up.evaluate(() =>
      [...document.querySelectorAll("#shop .n")].map(e => e.textContent));
    await up.evaluate(() => { window.__g.setSave({ kills: 6000 });
                              window.__g.checkUnlocks(); window.__g.menu(); });
    await up.waitForTimeout(250);
    const shopAfter = await up.evaluate(() =>
      [...document.querySelectorAll("#shop .n")].map(e => e.textContent));
    ok("TALLY is absent from the shop until it is earned",
       hidden && !shopBefore.includes("TALLY") && shopAfter.includes("TALLY"),
       `${shopBefore.length} lines -> ${shopAfter.length}`);

    // and the two new characters do what their cards claim
    const twinKit = await up.evaluate(() => {
      window.__g.start("twin"); return window.__g.kit();
    });
    ok("THE TWIN starts holding DUPLICATOR",
       twinKit.some(k => k.startsWith("dupe")), twinKit.join(" "));
    // Levels are DISCRETE. This asserted on them and passed at +34%, then failed
    // at +18% for a bonus that was still entirely there - the smaller multiplier
    // simply stopped crossing a level boundary at that gem count. Measure the
    // continuous quantity the mod actually changes.
    const xp = await up.evaluate(() => {
      const one = (c) => { window.__g.start(c); window.__g.god(); window.__g.freezeSpawns(true);
                           window.__g.drainPicks(true); window.__g.xp(100);
                           return window.__g.xpBanked(); };
      return { intern: one("intern"), accnt: one("accnt") };
    });
    ok("THE ACCOUNTANT banks more from the same gems",
       xp.accnt > xp.intern * 1.1,
       `${xp.intern} vs ${xp.accnt} XP from the same 100`);
    await ctx.close();
  }

  console.log("\n=== 15c. THE CAMERA TURNS WITHOUT POINTER LOCK ===");
  {
    // A sandboxed iframe can refuse pointer lock outright. When that happens the
    // mouse-look handler used to return early on every event, which froze the
    // camera and left the game unplayable in any embed. Drag has to cover it.
    const ctx = await browser.newContext({ viewport: { width: 1100, height: 700 } });
    const dp = await ctx.newPage();
    await dp.goto(FILE, { waitUntil: "load" });
    await dp.waitForTimeout(500);
    const r = await dp.evaluate(() => {
      window.__g.wipeSave(); window.__g.start("intern");
      const cv = document.getElementById("gl");
      const move = dx => dispatchEvent(new MouseEvent("mousemove",
        { movementX: dx, movementY: 0, bubbles: true }));
      const locked = document.pointerLockElement === cv;
      const a = window.__g.camYaw();
      move(60);                                   // no button down, no lock
      const idle = window.__g.camYaw();
      cv.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
      const held = window.__g.dragging();
      move(60);                                   // dragging
      const b = window.__g.camYaw();
      dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
      move(60);                                   // released again
      const c = window.__g.camYaw();
      return { locked, a, idle, b, c, held, after: window.__g.dragging() };
    });
    ok("drag turns the camera with no lock held",
       r.locked === false && Math.abs(r.b - r.idle) > 0.1,
       `locked=${r.locked} idle=${r.idle.toFixed(3)} dragged=${r.b.toFixed(3)}`);
    ok("mousedown on the canvas starts a drag", r.held === true);
    ok("a loose mouse does not steer", Math.abs(r.idle - r.a) < 1e-9,
       `${r.a.toFixed(4)} -> ${r.idle.toFixed(4)}`);
    ok("mouseup ends the drag", r.after === false && Math.abs(r.c - r.b) < 1e-9,
       `dragging=${r.after} yaw ${r.b.toFixed(4)} -> ${r.c.toFixed(4)}`);
    await ctx.close();
  }

  console.log("\n=== 19. BUNNYHOPPING ===");
  {
    // The mechanic is "jump on the frame you land and keep the momentum", so
    // every assertion here is about the WINDOW, not about the jump. A test that
    // only checked "space makes you airborne" would have passed against a build
    // with no chain in it at all.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const key = (t, code, repeat = false) =>
        dispatchEvent(new KeyboardEvent(t, { code, repeat }));
      const steps = n => { for (let i = 0; i < n; i++) g.step(1 / 60); };
      const jump  = () => { key("keydown", "Space"); key("keyup", "Space"); };
      const land  = () => { let n = 0; while (g.hop().air && n++ < 400) g.step(1 / 60); };

      // Twelve seconds of running north crosses the whole arena, and the wall
      // slide zeroes the velocity aimed into it - which read as "the chain cost
      // you all your speed" the first time this ran. Re-centre between phases
      // and assert we never reached the wall at all.
      const home = () => g.place(0, 0);
      let hitWall = false;
      const watch = () => { if (g.hop().r > g.rim() - 3) hitWall = true; };

      key("keydown", "KeyW");
      home(); steps(60); watch();                 // settle at base top speed
      const base = g.hop().spd, baseN = g.hop().n;

      jump(); steps(1);                           // a cold jump: no chain
      const cold = g.hop().n;

      const chain = [], mults = [];
      for (let k = 0; k < 14; k++) { land(); jump(); g.step(1 / 60);
                                     chain.push(g.hop().n); mults.push(g.hop().mul);
                                     if (g.hop().r > 40) home(); }
      steps(30); watch();                         // let the speed catch up in air
      const top = g.hop();

      // miss the window: land, stand still for a while, jump cold
      land(); steps(30);                          // 0.5s grounded
      const bleeding = g.hop().n;
      steps(210);                                 // 3.5s grounded
      const dead = g.hop().n;
      home(); steps(60); watch();
      const backToBase = g.hop().spd;

      // holding the key must not auto-hop
      land();
      key("keydown", "Space", true);
      const heldBuf = g.hop().buf;

      // and a press slightly BEFORE touchdown still counts
      jump(); g.step(1 / 60);                     // airborne again
      let n2 = 0; while (g.hop().air && g.hop().spd >= 0 && n2++ < 400) {
        g.step(1 / 60);
        if (!g.hop().air) break;
      }
      key("keyup", "KeyW");
      return { base, baseN, cold, chain, mults, top, bleeding, dead, backToBase,
               heldBuf, hitWall, max: g.hop().mul };
    });
    ok("standing still, there is no chain", r.baseN === 0, `n=${r.baseN}`);
    ok("a cold jump starts the chain at zero", r.cold === 0, `n=${r.cold}`);
    ok("jumping on the landing frame links the chain",
       r.chain[0] === 1 && r.chain[1] === 2 && r.chain[2] === 3,
       `chain ${r.chain.join(",")}`);
    ok("the chain keeps counting past where it used to stop",
       r.chain[13] === 14, `chain reached ${r.chain[13]}`);
    // The old cap made hopping a thing you FINISHED. Every link has to still
    // buy something, and the gains have to shrink rather than stop.
    ok("every link still pays, and later ones pay less",
       r.mults.every((m, i) => i === 0 || m > r.mults[i-1]) &&
       (r.mults[13] - r.mults[12]) < (r.mults[1] - r.mults[0]) * 0.4,
       `+${((r.mults[0]-1)*100).toFixed(0)}% / +${((r.mults[4]-1)*100).toFixed(0)}% / ` +
       `+${((r.mults[11]-1)*100).toFixed(0)}% at links 1/5/12`);
    ok("and it converges instead of running away",
       r.mults[13] < 1.62, `x${r.mults[13].toFixed(3)} at link 14`);
    ok("a full chain is measurably faster than walking",
       r.top.spd > r.base * 1.4,
       `${r.base.toFixed(2)} -> ${r.top.spd.toFixed(2)} m/s  (x${(r.top.spd/r.base).toFixed(2)})`);
    ok("landing and standing bleeds the chain rather than snapping it",
    // The bound, not the behaviour: this was written against a flat 2.4/s bleed
    // and the bleed is proportional now. What the assertion is FOR is that half
    // a second off-tempo costs you real chain and not all of it.
       r.bleeding > 9 && r.bleeding < 13.5,
       `14 -> ${r.bleeding.toFixed(2)} after half a second`);
    ok("and it is gone a few seconds after you stop", r.dead === 0, `n=${r.dead}`);
    ok("speed comes back down with it",
       Math.abs(r.backToBase - r.base) < 0.15,
       `${r.top.spd.toFixed(2)} -> ${r.backToBase.toFixed(2)} vs base ${r.base.toFixed(2)}`);
    ok("a HELD spacebar does not auto-hop", r.heldBuf === 0, `buf=${r.heldBuf}`);
    ok("and none of that was measured against a wall", r.hitWall === false);
  }

  console.log("\n=== 19c. KEEPING TEMPO PAYS ===");
  {
    // The chain has to be worth keeping for something other than speed, or it
    // is a movement tech rather than a mechanic. Every link pulls loot in;
    // every fifth pays XP and coins with a number on it.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const key = c => { dispatchEvent(new KeyboardEvent("keydown", { code: c }));
                         dispatchEvent(new KeyboardEvent("keyup",   { code: c })); };
      const land = () => { let n = 0; while (g.hop().air && n++ < 400) g.step(1/60); };
      dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
      g.place(0, 0);
      for (let i = 0; i < 60; i++) g.step(1/60);

      // a gem five metres away, well outside the 4.2m pickup radius
      g.place(0, 0);
      const before = { xp: g.xpBanked(), coins: g.runCoins() };
      const out = [];
      for (let k = 0; k < 11; k++) {
        land(); key("Space"); g.step(1/60);
        out.push({ n: g.hop().n, xp: g.xpBanked(), coins: g.runCoins() });
        if (g.hop().r > 40) g.place(0, 0);
      }
      dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
      return { before, out };
    });
    // Key off the chain length the game REPORTS, not the loop index. The first
    // press in this section is a cold jump - there is no landing window to hit
    // yet - so link n happens on iteration n+1, and indexing by position read
    // "links that paid: 6,11" against a game that was paying at 5 and 10.
    const gained = r.out.map((o, i) => o.xp - (i ? r.out[i-1].xp : r.before.xp));
    const paid   = r.out.map((o, i) => gained[i] > 0 ? o.n : 0).filter(Boolean);
    const atLink = n => gained[r.out.findIndex(o => o.n === n)];
    ok("every fifth link pays out", paid.join() === "5,10",
       `links that paid: ${paid.join() || "none"}`);
    ok("and the links between them do not",
       gained.filter(v => v > 0).length === 2, `${gained.filter(v=>v>0).length} payouts in 11 links`);
    ok("the payout scales with the level it happens at",
       atLink(5) >= 3, `+${atLink(5)} XP at link 5`);
    ok("coins too",
       r.out[9].coins > r.out[3].coins, `${r.out[3].coins} -> ${r.out[9].coins}`);
  }

  console.log("\n=== 19b. THE JUMP INPUT IS BUFFERED ===");
  {
    // Landing frames are 16ms wide. Without a pre-land buffer the window is not
    // a skill, it is a coin flip on frame timing - so a press issued while still
    // airborne has to survive until touchdown and spend itself there.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true);
      const key = c => { dispatchEvent(new KeyboardEvent("keydown", { code: c }));
                         dispatchEvent(new KeyboardEvent("keyup",   { code: c })); };
      dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
      for (let i = 0; i < 60; i++) g.step(1 / 60);

      key("Space"); g.step(1 / 60);                  // airborne, chain 0
      // Fire the press on the way DOWN and then never touch the key again. The
      // buffer is 0.14s and a jump is airborne for 0.73s, so pressing at the top
      // of the arc proves nothing except that buffers expire - the press has to
      // land inside the window it exists to widen.
      let armedInAir = false, n = 0;
      while (g.hop().air && n++ < 400) {
        g.step(1 / 60);
        if (g.hop().air && g.hop().vy < -9 && !armedInAir) {
          key("Space"); armedInAir = g.hop().buf > 0;
        }
      }
      g.step(1 / 60);                                 // the frame after touchdown
      const linkedFromBuffer = g.hop().n;

      // and a press that is too early expires instead of hanging around
      key("Space");
      for (let i = 0; i < 12; i++) g.step(1 / 60);    // 0.2s > HOP_BUF
      const expired = g.hop().buf;
      dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
      return { armedInAir, linkedFromBuffer, expired };
    });
    ok("a press made in mid-air is stored", r.armedInAir === true);
    ok("and it links the chain on touchdown without a second press",
       r.linkedFromBuffer === 1, `n=${r.linkedFromBuffer}`);
    ok("a buffer nobody spends expires", r.expired === 0, `buf=${r.expired}`);
  }

  console.log("\n=== 20. THE WALL IS THE EDGE OF THE MAP ===");
  {
    // The boundary used to be a square clamp with a decorative ring of spires
    // inside it, thirty metres short of the corners. You walked through the wall
    // and the map kept going. These check the two shapes are now one shape.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.start("intern"); g.god(); g.freezeSpawns(true); g.drainPicks(true);
      const RIM = g.rim();
      g.place(500, 500);
      const st1 = g.state();
      const corner = Math.hypot(st1.x, st1.z);

      // walk into the wall for four seconds and see if it holds
      g.place(0, 0);
      dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
      let worst = 0;
      for (let i = 0; i < 60 * 20; i++) { g.step(1 / 60);
        const s = g.state(); worst = Math.max(worst, Math.hypot(s.x, s.z)); }
      dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));

      // 300 event spawns, all of which used to be able to land in a corner
      g.freezeEvents(false);
      // g.spawnEvent() returns the KIND, not the event - reading .x off it gave
      // NaN, and "NaN > RIM" is false, so the first version of this check passed
      // by measuring nothing at all. Read the live list instead.
      let evOut = 0, evMax = 0, evSeen = 0;
      for (let i = 0; i < 300; i++) {
        g.place((Math.random()*2-1)*RIM*0.7, (Math.random()*2-1)*RIM*0.7);
        if (!g.spawnEvent(["cache","altar","hunt"][i % 3])) continue;
        for (const e of g.events()) {
          const d = Math.hypot(e.x, e.z);
          if (!isFinite(d)) continue;
          evSeen++; evMax = Math.max(evMax, d);
          if (d > RIM) evOut++;
        }
      }

      return { RIM, corner, worst, evOut, evMax, evSeen,
               wall: g.wall(), propsOut: g.propsOut() };
    });
    ok("there is a continuous wall, not a picket fence",
       r.wall.n >= Math.floor(2*Math.PI*r.RIM/3.0), `${r.wall.n} segments at rim ${r.RIM}`);
    ok("every segment sits at exactly the play radius",
       Math.abs(r.wall.rmin - r.RIM) < 0.01 && Math.abs(r.wall.rmax - r.RIM) < 0.01,
       `RIM ${r.RIM}, segments ${r.wall.rmin}..${r.wall.rmax}`);
    {
      // Position alone says nothing about ORIENTATION, and the first build of
      // this wall had all 150 slabs rotated 90 degrees - a ring of radial
      // spokes with daylight between every one, which the check above passed.
      // Walk the ring and ask, at every half-degree, whether there is material.
      let worst = 0, worstA = 0;
      for (let i = 0; i < 720; i++) {
        const th = i / 720 * Math.PI * 2;
        const qx = Math.cos(th) * r.RIM, qz = Math.sin(th) * r.RIM;
        let best = 1e9;
        for (const g of r.wall.seg) {
          const t = Math.max(-g.L, Math.min(g.L, (qx - g.x) * g.ux + (qz - g.z) * g.uz));
          const dx = qx - (g.x + g.ux * t), dz = qz - (g.z + g.uz * t);
          best = Math.min(best, Math.hypot(dx, dz));
        }
        if (best > worst) { worst = best; worstA = th; }
      }
      ok("and the ring actually closes - no gap anywhere on it",
         worst < 0.1,
         `widest gap ${worst.toFixed(3)}m at ${(worstA * 180 / Math.PI).toFixed(0)} degrees`);
    }
    ok("teleporting outside puts you back inside",
       r.corner <= r.RIM - 1.4, `${r.corner.toFixed(2)} vs rim ${r.RIM}`);
    ok("walking into it for twenty seconds does not get through",
       r.worst <= r.RIM - 1.4, `furthest ${r.worst.toFixed(2)} of ${r.RIM}`);
    ok("no side event spawns outside the wall",
       r.evSeen > 200 && r.evOut === 0,
       `${r.evSeen} sampled, ${r.evOut} outside, furthest ${r.evMax.toFixed(1)} of ${r.RIM}`);
    {
      // camEye is written by render(), and render() runs on requestAnimationFrame
      // - NOT inside __g.step(). The first version of this stepped the sim 90
      // times per angle and then read the eye, which never re-rendered once: it
      // reported 11.7 of 84, i.e. the boom from whatever frame happened to have
      // drawn last, with the player still near the middle. Same trap as the
      // camera-lag check, third file. Real frames, and wait for the anchor to
      // actually arrive before reading anything.
      const eye = await page.evaluate(RIM => new Promise(res => {
        const angles = [0, 0.25, 0.5, 0.75].map(f => f * Math.PI * 2);
        let i = 0, n = 0, worst = 0, placed = false;
        window.__g.setShake(0);
        const tick = () => {
          const tx = Math.cos(angles[i]) * RIM, tz = Math.sin(angles[i]) * RIM;
          if (!placed) { window.__g.place(tx, tz); placed = true; n = 0; }
          window.__g.place(tx, tz);                 // hold it against the wall
          const a = window.__g.camAnchor(), e = window.__g.eye();
          const there = a && Math.hypot(a[0] - window.__g.state().x,
                                        a[2] - window.__g.state().z) < 1.0;
          if (there || ++n > 400) {
            worst = Math.max(worst, Math.hypot(e[0], e[2]));
            if (++i >= angles.length) return res({ worst, converged: there });
            placed = false;
          }
          requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      }), r.RIM);
      ok("and the camera stays inside it too",
         eye.converged && eye.worst > r.RIM * 0.5 && eye.worst <= r.RIM,
         `eye reached ${eye.worst.toFixed(1)} of ${r.RIM}${
           eye.converged ? "" : " (anchor never arrived)"}`);
    }
    ok("no scenery is stranded out there either", r.propsOut === 0, `${r.propsOut} props`);
  }

  console.log("\n=== 21. MONSTERS EVOLVE MID-RUN ===");
  {
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const lines = g.chars().map(id => { g.start(id); return g.mon(); });

      g.start("intern"); g.god(); g.freezeSpawns(true); g.drainPicks(true);
      const s0 = g.mon();
      // level 7 is stage 2 of 3
      while (g.state().lvl < 7) g.xp(200);
      const s1 = g.mon();
      const hpJump = s1.maxhp / s0.maxhp;
      // and the top of the line at 20, where the signature turns on
      while (g.state().lvl < 20) g.xp(2000);
      const s2 = g.mon();

      // Healing: an evolution must hand back exactly the HP it added. More and
      // level 7 is a panic button; nothing and a +16% maxhp bonus reads on the
      // HP bar as a LOSS, which is exactly how it looked the first time.
      // ON A DAMAGED PLAYER, which is the whole point and was missing. This
      // ran on a fresh run, where hp already equals maxhp - and at full health
      // "hand back exactly what the evolution added" and "refill the bar" do
      // the identical thing, so the assertion below could not tell them apart.
      // The mutation audit proved it: replacing the payback with P.hp = P.maxhp
      // sailed through this section and was only caught, by accident, eleven
      // sections later. Take four tenths of the bar off first and the two come
      // apart immediately.
      g.start("intern"); g.freezeSpawns(true); g.drainPicks(true);
      g.setHp(g.mon().maxhp * 0.4);
      const pre  = { maxhp: g.mon().maxhp, hp: g.state().hp };
      g.evolveTo(1);
      const post = { maxhp: g.mon().maxhp, hp: g.state().hp };
      const heal = { pre, post, wasDamaged: pre.hp < pre.maxhp * 0.6 };

      // an evolution is worth a pick of its own, on top of the level that caused it
      g.start("intern"); g.freezeSpawns(true); g.drainPicks(true);
      const q0 = g.state().pending;
      g.evolveTo(1);
      const q1 = g.state().pending;

      // monster levels are per monster and permanent
      g.wipeSave();
      g.start("intern"); const fresh = g.mon();
      g.setMon("intern", 40000);
      g.start("intern"); const raised = g.mon();
      g.start("scrap");  const other  = g.mon();
      return { lines, s0, s1, s2, hpJump, heal, q0, q1, fresh, raised, other,
               freshLvl: fresh.lvl, raisedLvl: raised.lvl, otherLvl: other.lvl };
    });
    // Five stages since the FINAL FORM arrived - three growth forms, the
    // apex, and the final above it.
    ok("every monster is a five-stage line, capped by its final form",
       r.lines.every(m => m.line.length === 5 && m.line.every(x => typeof x === "string" && x)),
       r.lines.map(m => m.line.join(">")).join("  "));
    ok("you start at the bottom of your line",
       r.s0.stage === 0 && r.s0.nm === r.s0.line[0], `${r.s0.nm} stage ${r.s0.stage}`);
    ok("level 7 evolves you", r.s1.stage === 1 && r.s1.nm === r.s1.line[1],
       `${r.s0.nm} -> ${r.s1.nm}`);
    ok("and it is a real stat block, not a rename",
       r.hpJump > 1.1, `maxhp x${r.hpJump.toFixed(3)}`);
    ok("level 20 reaches the signature stage",
       r.s2.stage === 2 && r.s2.nm === r.s2.line[2], `${r.s1.nm} -> ${r.s2.nm}`);
    ok("MOPMAW's signature is live at stage 3",
       Math.abs(r.s2.reach - 1.20) < 0.001, `reach ${r.s2.reach}`);
    ok("evolving heals exactly the HP it added, and no more",
       r.heal.wasDamaged &&
       Math.abs((r.heal.post.hp - r.heal.pre.hp) -
                (r.heal.post.maxhp - r.heal.pre.maxhp)) < 1.5 &&
       r.heal.post.hp <= r.heal.post.maxhp + 0.01,
       `hp +${(r.heal.post.hp - r.heal.pre.hp).toFixed(1)}, maxhp +${
         (r.heal.post.maxhp - r.heal.pre.maxhp).toFixed(1)}`);
    ok("an evolution is worth a level-up pick of its own",
       r.q1 === r.q0 + 1, `${r.q0} -> ${r.q1} queued`);
    ok("banking XP raises that monster's level",
       r.raisedLvl > r.freshLvl, `${r.freshLvl} -> ${r.raisedLvl}`);
    ok("and it raises its starting HP with it",
       r.raised.maxhp > r.fresh.maxhp * 1.05,
       `${r.fresh.maxhp} -> ${r.raised.maxhp}`);
    ok("a level on one monster is not a level on another",
       r.otherLvl === 1, `scrap is LV ${r.otherLvl}`);
  }

  console.log("\n=== 21b. TWENTY-ONE FORMS, NOT ONE MESH IN SEVEN COLOURS ===");
  {
    // The whole roster used to be a single quadruped tinted seven ways, and it
    // read exactly like that. Nothing in a body plan animates a size, so the
    // signature - box count plus every box's half-extents, sorted - is stable
    // frame to frame, and two forms sharing a mesh come back byte-identical.
    const sigs = await page.evaluate(async ids => {
      const frame = () => new Promise(r => requestAnimationFrame(() => r()));
      const out = {};
      for (const id of ids) {
        for (const [lv, tag] of [[1, "s1"], [7, "s2"], [20, "s3"]]) {
          window.__g.wipeSave(); window.__g.start(id); window.__g.god();
          window.__g.freezeSpawns(true); window.__g.freezeEvents(true);
          window.__g.drainPicks(true);
          // xp() in small bites: one big grant skips whole stages at once, and
          // the first version of this handed over 4000 XP and screenshotted the
          // SAME form for s2 and s3 while reporting them as two.
          for (let g = 0; g < 5000 && window.__g.state().lvl < lv; g++) window.__g.xp(4);
          window.__g.step(1 / 60);
          await frame();
          window.__g.captureBody();
          await frame(); await frame();
          out[id + "-" + tag] = { sig: window.__g.bodySig(),
                                  stage: window.__g.mon().stage,
                                  nm: window.__g.mon().nm };
        }
      }
      return out;
    }, ["intern", "scrap", "spark", "ox", "ghoul", "accnt", "twin"]);

    const keys = Object.keys(sigs);
    const all  = keys.map(k => sigs[k].sig);
    ok("every form actually rendered a body",
       all.every(v => typeof v === "string" && v.length > 0),
       keys.filter(k => !sigs[k].sig).join(",") || "all 21 captured");
    ok("twenty-one forms, twenty-one distinct meshes",
       new Set(all).size === 21, `${new Set(all).size} distinct of ${all.length}`);
    ok("each line's three forms are three different animals",
       ["intern","scrap","spark","ox","ghoul","accnt","twin"].every(id =>
         new Set(["s1","s2","s3"].map(t => sigs[id + "-" + t].sig)).size === 3),
       ["intern","scrap","spark","ox","ghoul","accnt","twin"]
         .map(id => `${id} ${["s1","s2","s3"].map(t =>
           sigs[id + "-" + t].sig.split("|")[0]).join("/")}`).join("  "));
    ok("and the stage the test asked for is the stage it got",
       ["s1","s2","s3"].every((t, i) =>
         Object.keys(sigs).filter(k => k.endsWith(t)).every(k => sigs[k].stage === i)),
       keys.map(k => `${sigs[k].nm}:${sigs[k].stage}`).join(" "));
  }

  console.log("\n=== 22. THE HORDE IS NOT FIVE COLOURED BOXES ===");
  {
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true); g.setShake(0);
      const b = g.bodies();

      // LOD: the same forty bodies, once inside the full-detail radius and once
      // well outside it. If distance does not buy anything back, four hundred
      // enemies at fourteen boxes each is the whole frame budget.
      g.place(0, 0);
      const count = async () => { await frame(); await frame(); return g.state().boxes; };
      g.spawn("brute", 40, 9);      await frame();
      const near = await count();
      g.place(0, 60);               // same enemies, now ~60m away
      const far  = await count();
      return { b, near, far };
    });
    const sp = r.b.species;
    ok("every species has a body plan of its own",
       Object.keys(sp).every(k => sp[k].want && sp[k].has),
       Object.keys(sp).map(k => `${k}:${sp[k].want || "none"}${sp[k].has ? "" : " MISSING"}`).join(" "));
    // Count DECLARED plans only. Counting the undefineds too meant a species
    // with no plan at all still contributed a distinct value, and this passed
    // while GLIMMERFOWL was falling back to the generic box.
    const want = Object.values(sp).map(v => v.want).filter(Boolean);
    ok("and no two species share one",
       new Set(want).size === Object.keys(sp).length,
       `${new Set(want).size} distinct plans for ${Object.keys(sp).length} species`);
    ok("distance buys the box budget back",
       r.far < r.near * 0.75, `${r.near} boxes near -> ${r.far} far`);

    // GLIMMERFOWL draws its ring and beam BEFORE its body, so a throw halfway
    // down the plan still leaves fowlMarks reading 3. Count the boxes instead:
    // fifteen of them are the marker, so a bird that only marks itself and then
    // dies shows up here as a bird made of nothing.
    const fowl = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const settle = async () => { await frame(); await frame(); return g.state().boxes; };
      g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true); g.setShake(0); g.place(0, 0);
      const bare = await settle();
      g.spawn("collector", 3, 8); g.step(1/60);
      return { bare, withFowl: await settle() };
    });
    const per = (fowl.withFowl - fowl.bare) / 3;
    ok("and GLIMMERFOWL is a bird, not fifteen marker boxes",
       per > 26, `${per.toFixed(1)} boxes each, 15 of which are the marker`);

    // The four bosses shared `generic` - one five-box plan and a scale factor -
    // for the whole life of the project, which meant the four moments the run is
    // built around were the same silhouette four times in four colours. Sign the
    // mesh the way the player's forms are signed: eb() is the door every plan
    // goes through, so the capture is box count plus sorted half-extents.
    const bosses = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const out = [];
      for(let i = 0; i < 4; i++){
        g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.place(0, 0);
        g.boss(i); g.step(1/60);
        g.captureEnemy();
        await frame(); await frame();
        out.push({ nm: g.bossAt() ? g.bossAt().nm : "none", sig: g.enemySig() });
      }
      return out;
    });
    ok("every boss rendered a body",
       bosses.every(b => b.sig), bosses.map(b => `${b.nm}:${b.sig ? "ok" : "NULL"}`).join(" "));
    ok("four bosses, four different animals",
       new Set(bosses.map(b => b.sig)).size === 4,
       `${new Set(bosses.map(b => b.sig)).size} distinct of 4`);
    const boxesOf = b => b.sig ? +b.sig.split("|")[0] : 0;
    ok("and none of them is the five-box fallback",
       bosses.every(b => boxesOf(b) >= 30),
       bosses.map(b => `${b.nm} ${boxesOf(b)}`).join("  "));

    // A boss was pinned at full detail forever, which was free at five boxes and
    // is not at ninety-eight. State the LOD claim directly rather than leaning on
    // the frame budget - the budget passes either way now, so it cannot notice.
    const lod = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const at = async dist => {
        g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.place(0, 0);
        g.boss(3); g.step(1/60);
        const b = g.bossAt();
        g.place(b.x - dist, b.z); g.step(1/60);
        g.captureEnemy(); await frame(); await frame();
        const sig = g.enemySig();
        return sig ? +sig.split("|")[0] : 0;
      };
      return { near: await at(10), far: await at(110) };
    });
    ok("and distance thins a boss out too",
       lod.far > 0 && lod.far < lod.near * 0.55,
       `TERRAVORE ${lod.near} boxes at 10m -> ${lod.far} at 110m`);
  }

  console.log("\n=== 22b. THREE RANKS, AND THE CEILING DID NOT MOVE ===");
  {
    // The rank COUNT dropped from five to three. The rank VALUE did not: RANKMAP
    // reads lv[0], lv[2], lv[4] and passives scale by 5/3, so rank 3 of 3 is
    // worth exactly what rank 5 of 5 was. Both halves of that need asserting -
    // a version that quietly caps at lv[2] is a two-rank nerf wearing a UI
    // change, and a version that lets a rank run past 3 is the same bug pointing
    // the other way.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const boot = () => { g.wipeSave(); g.start("intern"); g.god(); g.drainPicks(true);
                           g.freezeSpawns(true); g.freezeEvents(true); };
      boot(); g.give("boots", 3);
      const at3 = g.state().spd;
      boot(); g.give("boots", 9);          // ask for far more than the game allows
      const at9 = g.state().spd, kit9 = g.kitRaw().boots.l;
      boot();
      const bare = g.state().spd;
      return { bare, at3, at9, kit9, wmax: g.wmax ? g.wmax() : null };
    });
    ok("three ranks is the ceiling, however hard you push",
       r.at9 === r.at3 && r.kit9 === 2,
       `rank index ${r.kit9} at nine picks, spd ${r.at3} vs ${r.at9}`);
    ok("and three ranks is worth what five used to be",
       Math.abs(r.at3 / r.bare - 1.45) < 0.02,
       `${r.bare} -> ${r.at3} m/s, x${(r.at3 / r.bare).toFixed(3)} (five ranks of +9% was x1.45)`);
  }

  console.log("\n=== 22c. A LEVEL-UP WITH NOTHING ON IT IS NOT A SCREEN ===");
  {
    // Everything maxes at rank 3 now, so a full kit is about fifty picks - and a
    // long run reaches level 70-80. The back thirty were full-screen drafts with
    // exactly one card on them, ROAST CHICKEN, each one unlocking the pointer,
    // freezing the chain and stopping the camera to be dismissed. That is the
    // "too many levels to upgrade" complaint in its purest form and no amount of
    // rank remapping touches it.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.freezeSpawns(true); g.freezeEvents(true);
      // max everything the draft could ever offer
      for (const k of ["bat","skulls","bolt","pulse","mortar","zap","aura","caltrops",
                       "spinach","boots","tempo","magnet","plating","heart","dupe","clover",
                       "momentum","stomp","bloodthirst","hunter"])
        g.give(k, 3);
      // and evolve every weapon, or the eight EVOLUTION cards are still real
      // choices sitting in the pool - which they should be.
      for (const k of ["bat","skulls","bolt","pulse","mortar","zap","aura","caltrops"])
        g.evolve(k);
      g.hitMe(40);                        // room to notice a heal
      const before = g.state();
      g.xp(9000);                         // several levels, nothing left to learn
      g.step(1, 1/60);                    // the drain runs in the loop, not in gainXP
      const after = g.state();
      // the one screen a silent level may open is a MASTERY (every fifth)
      const lv = [...document.querySelectorAll("#pkCards .card .lv span")].map(e => e.textContent);
      const masteryOpen = after.picking && lv.length > 0 && lv.every(x => x === "MASTERY");
      return { picking: after.picking, pending: after.pending, masteryOpen,
               gained: after.lvl - before.lvl, healed: after.hp > before.hp,
               kit: g.kit().length };
    });
    ok("a full kit still levels", r.gained > 3, `+${r.gained} levels, ${r.kit} things carried`);
    ok("and none of those levels opened a screen, other than a MASTERY",
       (r.picking === false && r.pending === 0) || r.masteryOpen,
       `picking=${r.picking}, ${r.pending} queued, mastery=${r.masteryOpen}`);
    ok("the refreshment is taken for you instead", r.healed, "healed on the way past");

    // and the opposite: a level-up that DOES have a choice still stops the game.
    const real = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.xp(60); g.step(1, 1/60);
      return g.state();
    });
    ok("a level-up with a real choice still opens one", real.picking === true,
       `picking=${real.picking}`);
  }

  console.log("\n=== 22s. NO PART OF A CREATURE FIGHTS ANOTHER PART ===");
  {
    // Reported as "the models glitch into each other". A rounded box in this
    // renderer is three concentric boxes, each full-size on one axis and shrunk
    // on the other two - and the shrink factor was the SAME .78 on every axis,
    // so box A and box C were both .78 wide, A and B both .78 deep, B and C
    // both .78 tall. Three pairs of exactly coplanar faces at the same centre,
    // in every rounded part of every creature in the game.
    //
    // Two surfaces at the same depth make the depth buffer pick, and the pick
    // changes with the camera. This counts them: a pair is fighting if a face
    // plane coincides within a millimetre AND the boxes actually overlap on the
    // other two axes, because coplanar faces that do not overlap never show.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      // The capture is filled by render(), not by step() - the body is drawn in
      // the frame, not in the simulation. Stepping and then reading gives null.
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const EPS = 0.001;
      const out = [];
      for (const ch of g.chars()) for (const st of [0, 1, 2, 3, 4]) {
        g.wipeSave(); g.start(ch); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.place(0, 0);
        if (st) g.evolveTo(st);
        g.resume(); g.capturePos();
        await frame(); await frame();
        const b = g.posOut();
        if (!b) { out.push({ ch, st, nm: g.stageNm(), bad: -1, n: 0 }); continue; }
        const n = b.length / 6, box = i => b.slice(i*6, i*6+6);   // r f y hx hy hz
        let bad = 0, cores = 0, twins = 0;
        for (let i = 0; i < n; i++) for (let j = i+1; j < n; j++) {
          const A = box(i), B = box(j);
          // CONCENTRIC and coplanar is the always-visible case: two boxes on
          // the same centre with a face on the same plane have BOTH faces
          // exposed, because neither can hide the other. That is what blob()
          // was doing on three axis pairs in every rounded part of every model,
          // and it is the class that has to be zero.
          const same = Math.abs(A[0]-B[0]) < EPS && Math.abs(A[1]-B[1]) < EPS
                    && Math.abs(A[2]-B[2]) < EPS;
          for (let k = 0; k < 3; k++) {
            const o1 = (k+1)%3, o2 = (k+2)%3;
            // must overlap on the other two axes, or the shared plane is invisible
            const ov = (ax) => Math.min(A[ax]+A[ax+3], B[ax]+B[ax+3])
                             - Math.max(A[ax]-A[ax+3], B[ax]-B[ax+3]);
            if (ov(o1) <= EPS || ov(o2) <= EPS) continue;
            const hi = Math.abs((A[k]+A[k+3]) - (B[k]+B[k+3]));
            const lo = Math.abs((A[k]-A[k+3]) - (B[k]-B[k+3]));
            if (hi < EPS || lo < EPS) {
              bad++;
              if (same) cores++;
              // TWINS: two boxes of the SAME extents sharing a face plane.
              // That is what a row of identical parts looks like from the
              // depth buffer, and it is the class the absolute budget below
              // was really a proxy for - a proxy that stopped working once
              // chain() quadrupled how many boxes a creature is made of.
              if (Math.abs(A[3]-B[3]) < 1e-6 && Math.abs(A[4]-B[4]) < 1e-6
                                             && Math.abs(A[5]-B[5]) < 1e-6) twins++;
              break;
            }
          }
        }
        out.push({ ch, st, nm: g.stageNm(), bad, cores, twins, n });
      }
      return out;
    });
    const worst = r.slice().sort((a, b) => b.bad - a.bad).slice(0, 3);
    const total = r.reduce((s, x) => s + Math.max(0, x.bad), 0);
    const cores = r.reduce((s, x) => s + Math.max(0, x.cores || 0), 0);
    ok("every form was captured", r.every(x => x.bad >= 0), `${r.length} forms`);
    ok("no two concentric parts share a face plane - the always-visible case",
       cores === 0, `${cores} concentric fighting pairs across 21 forms`);
    // NO ROWS OF IDENTICAL PARTS. This is what the absolute budget below was
    // always a proxy for, measured directly: two boxes with the SAME extents
    // sharing a face plane is a repeated part landing on its own neighbour,
    // which is the pattern that shimmers. Measured directly it is zero, and it
    // has to stay zero.
    const twins = r.reduce((s, x) => s + Math.max(0, x.twins || 0), 0);
    // Six survive, all of them MIRRORED pairs - a left horn and a right horn of
    // the same size, overlapping near the midline, whose draw-index nudges
    // happened to land in the same slot on the one axis their positions agree
    // on. The nudge quantises to twelve, thirteen and eleven slots, so a
    // collision on one axis is a one-in-twelve event and with four hundred
    // boxes a creature it will happen. Eight is the ceiling, not the target.
    // A RATE against the roster size, like the incidental budget below it:
    // the ceiling was 8 across 21 forms (all of them MIRRORED left/right
    // pairs whose nudges landed in the same slot on the one axis their
    // positions agree on). The apex stages took the roster to 36 forms, and
    // every apex adds mirrored pairs by design - rods, streamers, eye-spots.
    // Same allowance per form, not the old absolute.
    ok("no rows of IDENTICAL parts share a face plane",
       twins <= Math.ceil(r.length * .4),
       `${twins} same-size fighting pairs across ${r.length} forms (ceiling ${Math.ceil(r.length*.4)})`);
    // A RATE, not a total, and the change is worth stating plainly. The budget
    // here used to be 300 against meshes of about a hundred boxes. chain()
    // rebuilt every creature as a run of interpenetrating segments to close
    // the gaps between parts, which took the twenty-one forms from ~1,900
    // boxes to ~8,000 - and once every part overlaps its neighbour on purpose,
    // the number of pairs that happen to share a face plane within a
    // millimetre scales with the square of how solid the animal is. Holding
    // the old absolute number would have been holding a budget on SOLIDITY.
    // What still has to hold: nothing concentric, nothing identical, and the
    // incidental cross-part coincidences stay near one per box rather than
    // becoming the mesh.
    const boxes = r.reduce((s, x) => s + x.n, 0);
    ok("and incidental coplanar pairs stay near one per box",
       total <= boxes * 1.15,
       `${total} pairs / ${boxes} boxes = ${(total/boxes).toFixed(2)} per box; worst: ` +
       worst.map(x => `${x.nm} ${x.bad}/${x.n}`).join(", "));
  }

  console.log("\n=== 22m. THE WORLD HAS WATER, AND THE WATER KNOWS WHO IS AQUATIC ===");
  {
    // Requested: "create water areas that enable dinosaurs that are aquatic."
    // Lakes are part of the world roll: carved basins with a flat rendered
    // surface. The TIDE plesiosaur and SURGE spinosaur swim 30% faster through
    // them; everything else wades at three-quarter speed; a flyer overflies.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.step(10, 1/60);
      const out = {};
      out.lakes = g.lakes();
      // depth is a pure function: centre of the first lake is wet, spawn is dry
      const L = out.lakes[0];
      out.wetAtLake = L ? g.inWater(L.x, L.z) : false;
      out.dryAtSpawn = !g.inWater(0, 0);
      // no den or monument stands in a lake
      out.marksDry = (g.dens() || []).every(m => !g.inWater(m.x, m.z));
      return out;
    });
    ok("the world rolls three to five lakes",
       r.lakes.length >= 3 && r.lakes.length <= 5, `${r.lakes.length} lakes`);
    ok("a lake centre is wet and the spawn is dry",
       r.wetAtLake && r.dryAtSpawn,
       `wet@lake=${r.wetAtLake} dry@spawn=${r.dryAtSpawn}`);
    ok("no den stands in a lake", r.marksDry, "checked every den");

    const m = await page.evaluate(async () => {
      const g = window.__g;
      // distance covered over one second, from a stand, holding one key
      const runFor = (id, x, z) => {
        g.wipeSave(); g.start(id); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.step(10, 1/60);
        g.place(x, z); g.aim(0);
        dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
        const x0 = g.state().x, z0 = g.state().z;
        g.step(60, 1/60);
        dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
        const s2 = g.state();
        return Math.hypot(s2.x - x0, s2.z - z0);
      };
      // PINNED. Each start rerolls the world, so the four runs were swimming
      // four different lakes in four different biomes - the ratio comparison
      // assumed one lake, and an ice lake for one animal only flaked it. One
      // pinned arena, one lake, every run.
      g.pin(31337);
      const runFor2 = (id, wet) => {
        g.wipeSave(); g.start(id); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.step(10, 1/60);
        const L = g.lakes()[0];
        // enter at the south rim heading north, so the whole second of travel
        // stays inside the lake instead of exiting the far bank halfway
        // inWater needs real depth, and depth dies off toward the rim: the
        // wet zone ends around .78 of the radius, so the run enters at .6 -
        // deep enough to count from the first frame, far enough south that a
        // second of travel stays wet in the smallest lake the roll allows
        if(wet) g.place(L.x, L.z - L.r*.6); else g.place(0, -10);
        g.aim(0);
        dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
        const x0 = g.state().x, z0 = g.state().z;
        g.step(60, 1/60);
        dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
        const s2 = g.state();
        return Math.hypot(s2.x - x0, s2.z - z0);
      };
      const out2 = {
        aquaWet:  runFor2("scrap", true),
        aquaDry:  runFor2("scrap", false),
        landWet:  runFor2("ox",    true),
        landDry:  runFor2("ox",    false),
      };
      g.pin(null);
      return out2;
    });
    // Each animal against ITS OWN dry speed, and swimmer against wader. A
    // straight wet-vs-dry check flaked whenever the roll parked the lake in a
    // bog: the bog's own -14% ate the swim bonus while the dry control ran on
    // neutral grass. The ratio of ratios cancels whatever biome the lake is
    // in, because both animals swim the same lake.
    const aqua = m.aquaWet / m.aquaDry, land = m.landWet / m.landDry;
    ok("a plesiosaur swims faster than it walks, allowing for the lake's biome",
       m.aquaWet > m.aquaDry * .95,
       `${m.aquaWet.toFixed(1)}m through water vs ${m.aquaDry.toFixed(1)}m over land`);
    const en = await page.evaluate(async () => {
      const g = window.__g;
      // BOTH streams pinned - see R77's note on section 28. Each shambler's
      // own speed multiplier comes off the RUN stream, which reseeds itself
      // from Math.random() on any start() that does not pin it, so this
      // average of six was carrying the same latent flake the bog check had
      // even though its wider margin (.88 against a true .74) never tripped it.
      g.pin(31337); g.pinRun(31337);
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.step(10, 1/60);
      const L = g.lakes()[0];
      // one shambler in open ground, one in the lake, both walking at a
      // player parked far away so they run in a straight line
      // SIX walkers averaged, because every enemy carries a seeded speed
      // variance of its own - one-vs-one this check compared two dice rolls
      // and lost to them
      const walk = (x, z) => { g.clearEnemies(); g.place(x, z + 30);
        for(let k2=0;k2<6;k2++) g.spawnAt("shambler", x + (k2%3-1)*1.2, z + (k2/3|0)*1.2);
        g.step(1, 1/60);
        const p0 = g.enemiesPos(); g.step(90, 1/60);
        const p1 = g.enemiesPos();
        let d2 = 0;
        for(let k2=0;k2<p0.length;k2++)
          d2 += Math.hypot(p1[k2].x - p0[k2].x, p1[k2].z - p0[k2].z);
        return d2 / p0.length; };
      const dry = walk(0, -30), wet = walk(L.x, L.z);
      g.pin(null); g.pinRun(null);
      return { dry, wet };
    });
    ok("and the horde wades too - a lake is terrain, not a player tax",
       en.wet < en.dry * .88,
       `a shambler covered ${en.wet.toFixed(1)}m through the lake vs ${en.dry.toFixed(1)}m on land`);
    ok("and water helps a swimmer far more than a wader",
       aqua > land * 1.5,
       `wet/dry ${aqua.toFixed(2)} for the plesiosaur vs ${land.toFixed(2)} for the ceratopsian`);

    // SURE FOOT is the den reward for the seven lines that pay every terrain
    // cost water and mud added: it does not shrink the tax, it buys it off.
    const sf = await page.evaluate(async () => {
      const g = window.__g;
      g.pin(31337);
      const run = (id, x, z, boon) => {
        g.wipeSave(); g.start(id); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.step(10, 1/60);
        if(boon) g.giveBoon("SURE FOOT");
        if(x !== null) g.place(x, z);
        g.aim(0);
        dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
        const x0 = g.state().x, z0 = g.state().z;
        g.step(60, 1/60);
        dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
        const s2 = g.state();
        return Math.hypot(s2.x - x0, s2.z - z0);
      };
      const L = (() => { g.wipeSave(); g.start("ox"); return g.lakes()[0]; })();
      const dry       = run("ox", 0, -10, false);
      const wetPlain  = run("ox", L.x, L.z - L.r*.6, false);
      const wetSure   = run("ox", L.x, L.z - L.r*.6, true);
      g.pin(null);
      return { dry, wetPlain, wetSure };
    });
    ok("SURE FOOT buys off the water tax rather than shrinking it",
       sf.wetSure > sf.wetPlain * 1.2 && sf.wetSure >= sf.dry * .97,
       `dry ${sf.dry.toFixed(1)}m, wet ${sf.wetPlain.toFixed(1)}m, wet+SURE FOOT ${sf.wetSure.toFixed(1)}m`);
  }

  console.log("\n=== 22n. THE APEX IS A FOURTH ANIMAL, AND ITS POWER IS REAL ===");
  {
    // Requested as "a fourth evolution that takes the monster to the next
    // level just like pokemon does their mega evolutions". Every line gains a
    // stage at level 34. Two families of claim, both checked here: the stage
    // EXISTS and arrives through the level system, and each apex POWER does
    // the thing its card says.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const boot = (id) => { g.wipeSave(); g.start(id); g.god();
        g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
        g.place(0, 0); g.aim(0); g.step(30, 1/60); };
      const out = { names: {}, apexAt: {} };
      // 1. all nine lines have a fourth AND a fifth distinct stage - and the
      // fifth is a different MESH, not the apex renamed: same signature
      // check 21b runs on the growth stages (box count + sorted extents)
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      for (const id of g.chars()) {
        boot(id);
        g.evolveTo(2); const was = g.mon().nm;
        g.evolveTo(3); const now = g.mon().nm;
        const apexStage = g.mon().stage;
        g.step(240, 1/60); g.resume(); g.captureBody();
        await frame(); await frame();
        const apexSig = g.bodySig();
        g.evolveTo(4); const fin = g.mon().nm;
        g.step(240, 1/60); g.resume(); g.captureBody();
        await frame(); await frame();
        const finSig = g.bodySig();
        out.names[id] = { was, now, fin, apexStage,
                          distinct: was !== now && now !== fin && was !== fin,
                          meshDiffers: !!apexSig && !!finSig && apexSig !== finSig,
                          stage: g.mon().stage };
      }
      // 2. and both arrive BY LEVELLING, not only by the dev hook - 40 levels
      // lands between the apex gate (34) and the final gate (48), 15 more
      // clears the final
      boot("spark");
      for (let i = 0; i < 40; i++) g.levelUp ? g.levelUp() : g.xp(2000);
      g.step(30, 1/60);
      out.byLevel = { lvl: g.state().lvl, stage: g.mon().stage };
      for (let i = 0; i < 15; i++) g.levelUp ? g.levelUp() : g.xp(4000);
      g.step(30, 1/60);
      out.byLevel2 = { lvl: g.state().lvl, stage: g.mon().stage };
      return out;
    });
    ok("all nine lines grow a fourth, differently named form",
       Object.values(r.names).every(x => x.distinct && x.apexStage === 3),
       Object.entries(r.names).map(([k, v]) => `${k}:${v.now}`).join(" "));
    ok("and a fifth above it - the final form, its own name again",
       Object.values(r.names).every(x => x.distinct && x.stage === 4),
       Object.entries(r.names).map(([k, v]) => `${k}:${v.fin}`).join(" "));
    ok("and the final form is a different mesh, not the apex renamed",
       Object.values(r.names).every(x => x.meshDiffers),
       Object.entries(r.names).filter(([, v]) => !v.meshDiffers)
         .map(([k]) => k).join(",") || "all 9 differ");
    ok("and the apex arrives through the level system at 34",
       r.byLevel.lvl >= 34 && r.byLevel.lvl < 48 && r.byLevel.stage === 3,
       `level ${r.byLevel.lvl} -> stage ${r.byLevel.stage}`);
    ok("and the final form arrives through the level system at 48",
       r.byLevel2.lvl >= 48 && r.byLevel2.stage === 4,
       `level ${r.byLevel2.lvl} -> stage ${r.byLevel2.stage}`);

    const p = await page.evaluate(async () => {
      const g = window.__g;
      const boot = (id) => { g.wipeSave(); g.start(id); g.god();
        g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
        g.place(0, 0); g.aim(0); g.step(30, 1/60); };
      const out = {};

      // STORMCALL: a hop landing at the apex fires the line's zap for free.
      boot("spark"); g.evolveTo(3); g.clearEnemies();
      g.spawnAt("brute", 0, 6); g.step(5, 1/60);
      g.setWT("zap", 99);                    // silence the carried zap's own clock
      const arcs0 = g.fxCounts().arcs;
      g.jump(); g.step(90, 1/60);            // up, land
      out.stormcall = { arcs: g.fxCounts().arcs - arcs0 };

      // RIPTIDE: an enemy inside the pickup radius is dragged in.
      const closed = (st) => { boot("scrap"); g.evolveTo(st); g.clearEnemies();
        g.spawnAt("shambler", 0, 6); g.step(45, 1/60);
        const e = g.nearestEnemy(); return e ? +Math.hypot(e.x, e.z).toFixed(2) : 99; };
      out.riptide = { st2: closed(2), st3: closed(3) };

      // PETRIFY: the sporecloud holds enemies at the slow.
      boot("ghoul"); g.evolveTo(3); g.give("aura", 1); g.clearEnemies();
      g.spawnAt("brute", 0, 2); g.step(30, 1/60);
      out.petrify = { slowed: g.nearestEnemy ? g.nearestEnemy().slowT > 0 : false };

      // WARCHOIR: one bolt more per volley than the same build one stage down.
      const volley = (st) => { boot("twin"); g.evolveTo(st); g.give("bolt", 1);
        g.clearEnemies(); g.spawnAt("brute", 0, 10);
        g.clearBolts(); g.step(40, 1/60); return g.boltsPeak(); };
      out.warchoir = { st2: volley(2), st3: volley(3) };

      // BREAKWATER: the apex surge outlives the stage-2 surge.
      const surged = (st) => { boot("surge"); g.evolveTo(st);
        g.setSurge(1.2); g.step(1, 1/60); return g.rule().surgeT; };
      out.breakwater = { st2: surged(2), st3: surged(3) };

      // SUNDIAL: the third rebirth costs the same as the first.
      boot("pyre"); g.evolveTo(3);
      const cds = [];
      for (let k = 0; k < 3; k++) { g.hitMe(1e12); cds.push(g.rule().rebirthCd);
        g.setRebirthCd(0); g.step(1, 1/60); }
      out.sundial = { cds };

      // UPHEAVAL: taking a hit answers with a pulse ring.
      boot("ox"); g.evolveTo(3); g.give("pulse", 1);
      const rings0 = g.fxCounts().rings;
      g.hitMe(10); g.step(2, 1/60);
      out.upheaval = { rings: g.fxCounts().rings - rings0 };

      // EYEWALL: the mortar fires twice as often at the apex.
      const shells = (st) => { boot("accnt"); g.evolveTo(st); g.give("mortar", 1);
        g.clearEnemies(); g.spawnAt("brute", 0, 12);
        g.clearMortars(); g.step(60 * 6, 1/60); return g.mortarsFired(); };
      out.eyewall = { st2: shells(2), st3: shells(3) };

      // STARFIRE: flying writes burning ground.
      boot("intern"); g.evolveTo(3); g.give("caltrops", 1);
      const z0 = g.fxCounts().zones;
      g.jump(); g.holdJump(true); g.step(80, 1/60); g.holdJump(false);
      out.starfire = { zones: g.fxCounts().zones - z0 };
      return out;
    });
    ok("STORMCALL: a hop landing calls down a zap",
       p.stormcall.arcs >= 1, `${p.stormcall.arcs} arc(s) from one landing`);
    ok("RIPTIDE: the pickup radius drags enemies in",
       p.riptide.st3 < p.riptide.st2 - .5,
       `same enemy after .75s: ${p.riptide.st2} away at stage 2, ${p.riptide.st3} at the apex`);
    ok("PETRIFY: the sporecloud slows what stands in it",
       p.petrify.slowed, `slowT set by the cloud`);
    ok("WARCHOIR: the apex volley carries one bolt more",
       p.warchoir.st3 === p.warchoir.st2 + 1,
       `${p.warchoir.st2} bolts at stage 2 -> ${p.warchoir.st3} at the apex`);
    ok("BREAKWATER: the apex surge lasts longer",
       p.breakwater.st3 > p.breakwater.st2 * 1.4,
       `${p.breakwater.st2}s -> ${p.breakwater.st3}s`);
    ok("SUNDIAL: the rebirth cooldown stops growing",
       Math.abs(p.sundial.cds[2] - p.sundial.cds[0]) < .01,
       `cooldowns ${p.sundial.cds.join(", ")}`);
    ok("UPHEAVAL: taking a hit answers with a tremor",
       p.upheaval.rings >= 1, `${p.upheaval.rings} ring(s) from one hit`);
    ok("EYEWALL: the mortar falls twice as often",
       p.eyewall.st3 >= p.eyewall.st2 * 1.7,
       `${p.eyewall.st2} shells in 6s -> ${p.eyewall.st3}`);
    ok("STARFIRE: flight writes burning ground",
       p.starfire.zones >= 2, `${p.starfire.zones} zones from one flight`);
  }

  console.log("\n=== 22o. PYRAETHON FLIES ===");
  {
    // Reported: "cinderwelp 2nd evolution should unlock flying". The EMBER
    // line's top form holds JUMP to beat its wings: it climbs to a hover,
    // nothing that has to touch you can reach it up there, and it costs a
    // meter that only refills on the ground. What it costs is the hop chain,
    // because you cannot chain a hop you never land from.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const boot = (st) => { g.wipeSave(); g.start("intern"); g.god();
        g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
        g.place(0, 0); g.aim(0); if (st) g.evolveTo(st); g.step(40, 1/60); };
      const down = () => dispatchEvent(new KeyboardEvent("keydown", { code: "Space" }));
      const up   = () => dispatchEvent(new KeyboardEvent("keyup",   { code: "Space" }));
      const out = {};
      boot(0); down(); g.step(90, 1/60); out.whelp = g.wings(); up();
      boot(1); down(); g.step(90, 1/60); out.drake = g.wings(); up();
      boot(2); down(); g.step(20, 1/60);  out.launch = g.wings();
      g.step(110, 1/60);                  out.hover  = g.wings();
      g.step(200, 1/60);                  out.spent  = g.wings();
      up(); g.step(300, 1/60);            out.back   = g.wings();
      // and the ground cannot touch it. Same hazard, on the floor and in the air.
      // Short exposure on purpose: the meter is under three seconds and when
      // it runs out the animal falls into the fire, which is the mechanic
      // working rather than the immunity failing.
      const burn = (fly) => {
        boot(2);
        if (fly) { down(); g.step(45, 1/60); }
        const hp0 = g.state().hp;
        g.hazardAt(0, 0, 3);
        g.step(60, 1/60);
        if (fly) up();
        return hp0 - g.state().hp;
      };
      out.hurtGround = burn(false);
      out.hurtAir    = burn(true);
      // and the moment it happens has to say so
      boot(1); g.evolveTo(2);
      out.banner = g.evoTxt().sub;
      return out;
    });
    ok("CINDERWHELP cannot fly", !r.whelp.can && !r.whelp.fly,
       `can=${r.whelp.can} fly=${r.whelp.fly}`);
    ok("nor can FLAREDRAKE", !r.drake.can && !r.drake.fly,
       `can=${r.drake.can} fly=${r.drake.fly}`);
    ok("PYRAETHON leaves the ground when you hold jump",
       r.launch.can && r.launch.fly && r.launch.alt > 1.2,
       `alt ${r.launch.alt} with ${r.launch.wing} of meter left`);
    ok("and holds a hover rather than climbing forever",
       Math.abs(r.hover.alt - 3.1) < .35, `alt ${r.hover.alt}`);
    ok("the meter runs out and puts it back on the floor",
       !r.spent.fly && r.spent.alt < .5, `fly=${r.spent.fly} alt=${r.spent.alt}`);
    ok("and refills on the ground", r.back.wing > .95, `wing ${r.back.wing}`);
    ok("and the evolution that grants it says so",
       /FLY/.test(r.banner), `banner read "${r.banner}"`);
    ok("up there the burning ground cannot reach it",
       r.hurtGround > 0 && r.hurtAir === 0,
       `${r.hurtGround.toFixed(1)} damage on the floor, ${r.hurtAir.toFixed(1)} in the air`);
  }

  console.log("\n=== 22p. THE ANIMAL KEEPS ITS OWN HEADING ===");
  {
    // Reported: "I don't like how the monster looks back at you while
    // receiving no inputs, change it to where it looks last place where it is
    // left". Pausing called faceCamera(), which spun the animal round to face
    // the lens - so the thing you were driving snapped to a pose it was never
    // in, and the pause read as the creature noticing you rather than as the
    // game stopping. Standing still must not turn it either.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.place(0, 0); g.aim(0);
      dispatchEvent(new KeyboardEvent("keydown", { code: "KeyA" }));
      g.step(60, 1/60);
      dispatchEvent(new KeyboardEvent("keyup", { code: "KeyA" }));
      const moving = g.state().face;
      g.step(40, 1/60);
      const idle = g.state().face;
      g.pause(true);
      const paused = g.state().face;
      g.pause(false);
      // NOT g.aim() with no argument - that setter takes whatever it is given,
      // so reading the camera that way sets the camera to undefined.
      return { moving, idle, paused };
    });
    const near = (a, b) => Math.abs(a - b) < 1e-3;
    ok("walking left points the animal left, not at the camera",
       Math.abs(Math.abs(r.moving) - Math.PI / 2) < .25,
       `face ${r.moving} with the camera at 0`);
    ok("standing still does not turn it",
       near(r.moving, r.idle), `${r.moving} walking -> ${r.idle} idle`);
    ok("and neither does pausing",
       near(r.idle, r.paused), `${r.idle} idle -> ${r.paused} paused`);

    // THE HEAD, TOO. The body kept its heading but ANIM.look clamped the head
    // toward the nearest enemy at any bearing, so a horde BEHIND the animal -
    // which is where the horde is whenever you have been running from it, and
    // where the camera is - pinned the head at the far edge of its arc and
    // held it there. That is the "looks back at you" in the report.
    const h = await page.evaluate(async () => {
      const g = window.__g;
      const run = (n) => g.step(n, 1/60);
      const set = (x, z) => {
        g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.place(0, 0); g.aim(0);
        run(20); g.clearEnemies(); g.spawnAt("shambler", x, z); run(50);
        return Math.abs(g.anim().look);
      };
      // face is 0, which is +z: dead ahead is +z, dead astern is -z
      return { ahead: set(3.5, 9), behind: set(3.5, -9) };
    });
    ok("the head tracks something in front of it",
       h.ahead > .12, `look ${h.ahead} with a target dead ahead`);
    ok("and does not crane round at something behind it",
       h.behind < .05, `look ${h.behind} with the same target astern`);
  }

  console.log("\n=== 22r. THE ANIMATION IS DRIVEN BY WHAT YOU DID ===");
  {
    // The creature had one animation: sin(T*13) while moving, hard zero while
    // not. One frequency, one amplitude, no ramp - so a careful walk and a
    // hop-chain sprint animated identically, stopping snapped the legs to a
    // dead pose mid-stride, and nothing the player did was visible on the
    // animal. Every term below is a thing the player can do.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const boot = () => { g.wipeSave(); g.start("intern"); g.god();
                           g.freezeSpawns(true); g.freezeEvents(true);
                           g.drainPicks(true); g.place(0, 0); g.step(30, 1/60); };
      const hold = (code, n) => { dispatchEvent(new KeyboardEvent("keydown", { code }));
                                  g.step(n, 1/60);
                                  dispatchEvent(new KeyboardEvent("keyup", { code })); };
      // 1. standing still settles to no gait at all
      boot(); g.step(90, 1/60);
      const still = g.anim();
      // 2. walking builds one, and the PHASE advances with distance
      boot(); hold("KeyW", 40);
      const walk = g.anim();
      const d0 = g.state();
      g.step(1, 1/60);
      // 3. the phase must track distance, not the clock: same seconds, no
      //    movement, must not advance
      boot(); const p0 = g.anim().ph; g.step(60, 1/60); const p1 = g.anim().ph;
      // 4. a landing crouches it
      boot(); hold("KeyW", 20);
      g.jump(); g.step(4, 1/60);
      const air = g.anim();
      // NOT "step until vy === 0" - vertical speed passes through zero at the
      // APEX, so that exits halfway up and measures a creature still climbing.
      // Step until the landing actually registers.
      let landed = null;
      for (let i = 0; i < 120; i++) { g.step(1, 1/60);
        if (g.anim().land > 0) { landed = g.anim(); break; } }
      landed = landed || g.anim();
      // 5. taking a hit recoils it
      boot(); g.hitMe(30); g.step(1, 1/60);
      const hit = g.anim();
      // 6. something nearby turns the head
      // placed, not rolled: "one within nine metres" lands at a random angle,
      // and about one time in twenty it lands dead ahead - where the correct
      // answer for "which way did the head turn" is nought
      boot(); g.spawnAt("brute", 7, 1); g.step(40, 1/60);
      const looking = g.anim();
      return { still, walk, standPh: p1 - p0, air, landed, hit, looking };
    });
    ok("standing still has no gait", r.still.amp < 0.03, `amp=${r.still.amp}`);
    ok("walking builds one", r.walk.amp > 0.5, `amp=${r.walk.amp}`);
    ok("the stride is measured in distance, not seconds",
       Math.abs(r.standPh) < 0.001, `phase moved ${r.standPh} across a second of standing still`);
    ok("moving leans the animal", Math.abs(r.walk.lean) > 0.02, `lean=${r.walk.lean}`);
    ok("landing crouches it", r.landed.sq < 0.99 && r.landed.land > 0,
       `sq=${r.landed.sq}, land=${r.landed.land}`);
    ok("a hit recoils it", r.hit.lunge < 0, `lunge=${r.hit.lunge}`);
    ok("and it looks at what is next to it",
       Math.abs(r.looking.look) > 0.05, `look=${r.looking.look}`);
  }

  console.log("\n=== 22q. A BOSS ARRIVES ===");
  {
    // Bosses used to appear: one frame not there, the next frame there,
    // twenty-six metres away, with a line of text. Something five times your
    // size should not be able to do that quietly. And the rise has to be safe
    // in both directions - a boss that can be shot while buried is a free kill,
    // one that can hit you while buried is an ambush you cannot see.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.place(0, 0); g.setShake(0);
      g.boss(3); g.step(1, 1/60);
      const b0 = g.bossAt();
      await frame(); await frame();
      const drawnRising = g.state().boxes;
      const hp0 = g.bossAt().hp;
      g.hitBoss ? g.hitBoss(9999) : null;
      g.step(6, 1/60);
      const hpWhileBuried = g.bossAt().hp;
      g.step(150, 1/60);                       // well past the rise
      const b1 = g.bossAt();
      return { started: b0 ? b0.rise : null, hp0, hpWhileBuried,
               after: b1 ? b1.rise : null, drawnRising };
    });
    ok("a boss starts buried", r.started > 0, `rise=${r.started}`);
    ok("and cannot be damaged while it is",
       r.hpWhileBuried === r.hp0, `${r.hp0} -> ${r.hpWhileBuried}`);
    ok("and it finishes arriving", r.after === 0, `rise=${r.after}`);
  }

  console.log("\n=== 22v. THE BOSS ARRIVES THROUGH THE SHOVE ===");
  {
    // Enemies take weapon knockback; bosses take .22 of it (elites .6). The
    // R166 combat film showed why: under a maxed kit the Matriarch was pushed
    // from 26m out to 33m while dying - the fight the run builds to could
    // never reach the player. EARTHQUAKE is the shove-heaviest single card
    // (kb 22 every .85s vs the Matriarch's 2.9m/s walk), so if she can arrive
    // through THAT, mass is doing its job; without mass she is juggled at
    // range forever and this stays red.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.disarm();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      g.setShake(0); g.clearEnemies(); g.place(0, 0);
      g.give("pulse", 6);                  // l=5: the EARTHQUAKE row
      g.boss(0);
      const s0 = g.state(), b0 = g.bossAt();
      const d0 = Math.hypot(b0.x - s0.x, b0.z - s0.z);
      let dMin = 1e9;
      for(let i = 0; i < 15 * 60; i++){
        g.step(1, 1/60);
        const b = g.bossAt(); if(!b) break;
        const s = g.state();
        dMin = Math.min(dMin, Math.hypot(b.x - s.x, b.z - s.z));
      }
      return { d0: +d0.toFixed(1), dMin: +dMin.toFixed(1),
               alive: !!g.bossAt() };
    });
    ok("the Matriarch reaches arm's length through EARTHQUAKE",
       r.alive && r.dMin < 4.5,
       `closed from ${r.d0}m to ${r.dMin}m in 15s (alive=${r.alive})`);
  }

  console.log("\n=== 22p. THERE IS SOMETHING AFTER THE FIRST CLEAR ===");
  {
    // Clearing a run was the end of the game: TERRAVORE dies and the only thing
    // left is the same twenty minutes again. THE DEEP is a layer ladder - every
    // clear opens one more, each one the same world dug further down.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave();
      const fresh = g.deep();
      // a fresh save can only play the surface
      g.pickDeep(4);
      const clamped = g.deep().sel;
      // opening layers lets you pick them, and picking one scales the curve
      g.setDeep(3); g.pickDeep(2);
      g.start("intern");
      const on2 = g.deep();
      g.pickDeep(0); g.start("intern");
      const on0 = g.deep();
      // and the ceiling holds
      g.setDeep(99);
      return { fresh, clamped, on2, on0, cap: g.deep().unlocked, max: g.deep().max };
    });
    ok("a fresh save has only the surface",
       r.fresh.unlocked === 0 && r.fresh.at === 0, JSON.stringify(r.fresh));
    ok("and cannot pick a layer it has not opened", r.clamped === 0, `picked ${r.clamped}`);
    ok("a layer makes the run harder and pays more",
       r.on2.at === 2 && r.on2.hp > 1.5 && r.on2.dmg > 1.2 && r.on2.pay > 1.4,
       `layer ${r.on2.at}: hp x${r.on2.hp}, dmg x${r.on2.dmg}, coins x${r.on2.pay}`);
    ok("and the surface is still the surface",
       r.on0.at === 0 && r.on0.hp === 1 && r.on0.dmg === 1 && r.on0.pay === 1,
       JSON.stringify({ hp: r.on0.hp, dmg: r.on0.dmg }));
    ok("the ladder has a top", r.cap === r.max, `${r.cap} of ${r.max}`);

    // clearing a layer opens the next one
    const won = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.setDeep(1); g.pickDeep(1);
      g.start("intern"); g.god(); g.drainPicks(true);
      g.skipTo(1140); g.boss(3);
      g.step(1, 1/60);
      g.killBoss();                            // the win condition, directly
      return g.deep();
    });
    ok("clearing a layer opens the next", won.unlocked >= 1, JSON.stringify(won));
  }

  console.log("\n=== 22o. EVOLVING IS A MOMENT, NOT A STAT CHANGE ===");
  {
    // The centrepiece of a game about raising a creature was a caption: the body
    // swapped to the next form between one frame and the next, six percent
    // larger, while a banner explained what had happened.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.place(0, 0); g.setShake(0);
      await frame(); await frame();
      const before = g.state().boxes, fx0 = g.evoFx();
      g.evolveTo(1);
      const fx1 = g.evoFx();
      await frame(); await frame();
      const during = g.state().boxes;
      g.step(120, 1/60);                      // two seconds later
      const fx2 = g.evoFx();
      await frame(); await frame();
      const after = g.state().boxes;
      return { before, during, after, fx0, fx1, fx2 };
    });
    ok("evolving starts a transformation", r.fx0 === 0 && r.fx1 > 0,
       `${r.fx0} -> ${r.fx1}`);
    ok("and it puts light on the screen while it runs",
       r.during > r.before + 15, `${r.before} boxes -> ${r.during} mid-transformation`);
    // NOT "back to the box count it started at" - the point of evolving is that
    // you are a different, larger animal afterwards. What has to go away is the
    // burst, so compare against the peak rather than against the start.
    ok("then it ends and takes its light with it",
       r.fx2 === 0 && r.after < r.during - 30,
       `fx ${r.fx2}, ${r.during} boxes mid-burst -> ${r.after} after (${r.before} before)`);
  }

  console.log("\n=== 22n. THE GAME USES THE NAME IT GAVE YOU ===");
  {
    // Evolving announces "LEARNED CINDERTRAIL" and then every surface in the
    // game went on saying CALTROPS. The move name has to win wherever one was
    // learned - and only there, because a MYCONID that picks up hazards in the
    // draft has not learned CINDERTRAIL and should not be told it has.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const learn = (ch) => {
        g.wipeSave(); g.start(ch); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true);
        const before = g.wNames();
        g.evolveTo(1);
        const mv = g.moveOf(ch);           // returns the move OBJECT
        return { move: mv && mv.nm, before, after: g.wNames() };
      };
      const a = learn("intern");
      // the generic name survives for a line that did not learn it
      g.wipeSave(); g.start("ghoul"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true); g.give("caltrops", 1);
      const borrowed = g.wNames();
      return { a, borrowed };
    });
    ok("the move you were taught is what the game calls it",
       r.a.after.includes(r.a.move) && !r.a.before.includes(r.a.move),
       `learned ${r.a.move}; kit went [${r.a.before}] -> [${r.a.after}]`);
    ok("and a line that never learned it still sees the generic name",
       r.borrowed.includes("CALTROPS"), `[${r.borrowed}]`);
  }

  console.log("\n=== 22m. THE NEW THINGS MAKE A NOISE ===");
  {
    // The dive, the dens and the affinity all shipped silent, and the dive is a
    // hit you are meant to dodge - the camera is behind you, so a bird winding
    // up at your flank is off-screen as often as not. A telegraph you can only
    // see is half a telegraph.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const boot = () => { g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
                           g.freezeEvents(true); g.drainPicks(true); g.place(0, 0);
                           g.setOpt("sound", 1); g.sfxReset(); };
      // THREE BIRDS, AND THE PLAYER PUTS THE BAT DOWN. One bird spawned nine
      // units out and given three and a third seconds to start its wind-up is
      // a race against the player's own auto-attack, not a check: it passed
      // alone three times for three and four chirps and came back 0 inside a
      // full suite run. Longer made it WORSE - two chirps, then one - because
      // the extra seconds are seconds the bat spends killing the bird before
      // it can wind up. What this section claims is that a wind-up makes a
      // noise, so: disarm the player, and give it three birds close enough to
      // reach him.
      boot(); g.disarm();
      for (const [bx, bz] of [[4, 4], [-4, 4], [4, -4]]) g.spawn("runner", bx, bz);
      for (let i = 0; i < 600; i++) { g.step(1, 1/60); g.place(0, 0); }
      const dive = g.sfx().dive || 0;

      // a den waking and a den taken. An ORDINARY den, deliberately: dens
      // have two voices now, and about one in five sounds the angry horn
      // instead - picking dens()[0] blind made this an 18% coin flip.
      g.wipeSave(); g.start("intern"); g.god(); g.freezeEvents(true); g.drainPicks(true);
      for (const w of ["bat", "zap", "aura"]) g.give(w, 3);
      g.skipTo(90);
      const d = g.dens().find(m => !m.angry) || g.dens()[0];
      g.sfxReset();
      g.place(d.x + 6, d.z); g.step(1, 1/60);
      const woke = g.sfx().denWake || 0;
      g.step(60 * 45, 1/60);
      const done = g.sfx().denDone || 0;

      // crossing onto home ground and off it
      let aff = { affIn: 0, affOut: 0 }, tries = 0, home = null, weak = null;
      while (tries++ < 300 && !(home && weak)) {
        g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true);
        const a = g.aff(), cs = g.world().cells;
        home = cs.find(c => c.id === a.home); weak = cs.find(c => c.id === a.weak);
      }
      if (home && weak) {
        g.sfxReset();
        g.place(home.x, home.z); g.step(1, 1/60); g.hud && g.hud();
        await new Promise(res => requestAnimationFrame(() => res()));
        g.place(weak.x, weak.z); g.step(1, 1/60);
        await new Promise(res => requestAnimationFrame(() => res()));
        aff = g.sfx();
      }
      return { dive, woke, done, affIn: aff.affIn || 0, affOut: aff.affOut || 0,
               src: g.sfxSrc() };
    });
    ok("a bird winding up on you is audible", r.dive > 0, `${r.dive} chirps`);
    ok("a den waking says so", r.woke > 0, `${r.woke}`);
    ok("and a den taken says so differently", r.done > 0, `${r.done}`);
    ok("crossing onto your own ground is audible", r.affIn > 0 && r.affOut > 0,
       `in ${r.affIn}, out ${r.affOut}`);
    // and no sound is a copy of another wearing a new name
    const src = r.src, names = Object.keys(src);
    const dupes = [];
    for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++)
      if (src[names[i]] === src[names[j]]) dupes.push(`${names[i]}=${names[j]}`);
    ok("every sound in the game is its own sound",
       dupes.length === 0 && names.length >= 21,
       `${names.length} sounds, duplicates: ${dupes.join(",") || "none"}`);

    // The danger-pays arc's own voices, held to the bar this section set the
    // first time features shipped silent: the pearl, the angry den and the
    // upwelling each say so, and the fingerprint sweep above already proves
    // none of them is an old sound wearing a new name.
    const r2 = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.disarm();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const L = g.lakes()[0];
      let pearl = 0;
      if (L) { g.clearGems(); g.place(L.x + L.r + 14, L.z); g.sfxReset();
               g.step(30 * 60, 1/60); pearl = g.sfx().pearl || 0; }
      let angry = 0, d = null;
      for (let seed = 500; seed < 560 && !d; seed++) {
        g.wipeSave(); g.start("intern"); g.god(); g.freezeEvents(true);
        g.drainPicks(true); g.reroll(seed);
        d = g.dens().find(m => m.angry);
      }
      if (d) { g.skipTo(90); g.sfxReset(); g.place(d.x + 6, d.z); g.step(2, 1/60);
               angry = g.sfx().denWakeAngry || 0; }
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.sfxReset();
      g.spawnEvent("storm", 20, 0);
      const upwell = g.sfx().upwell || 0;
      return { pearl, angry, upwell };
    });
    ok("a pearl breaking the surface is audible", r2.pearl > 0, `${r2.pearl} plips`);
    ok("an angry den sounds angrier than a den", r2.angry > 0, `${r2.angry}`);
    ok("and the upwelling rumbles when it opens", r2.upwell > 0, `${r2.upwell}`);

    // The end screen's den count is PER-RUN. denStats was a module const that
    // nothing reset, so "Explored: N dens cleared" summed every run since the
    // page loaded - a rule-character sweep caught a second run claiming 39
    // dens cleared of the 26 that exist.
    const dr = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeEvents(true); g.drainPicks(true);
      g.skipTo(90);
      const d = g.dens()[0];
      g.place(d.x + 6, d.z); g.step(2, 1/60);
      const woke1 = g.denStats().woke;
      g.start("intern");
      return { woke1, woke2: g.denStats().woke };
    });
    ok("a new run starts its den ledger at zero",
       dr.woke1 > 0 && dr.woke2 === 0,
       `run one woke ${dr.woke1}; run two opened at ${dr.woke2}`);

    // The receipt counts a pearl the player actually took - surfaced beside
    // a lake, walked onto, counted at pickup and per-run like everything
    // else on the end screen.
    const pr = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.disarm();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const L = g.lakes()[0];
      if (!L) return { err: "no lakes rolled" };
      g.clearGems();
      g.place(L.x + L.r + 14, L.z);
      g.step(20 * 60, 1/60);                        // a pearl surfaces
      g.place(L.x, L.z); g.step(4 * 60, 1/60);      // wade in and take it
      const taken = g.pearlsTaken();
      g.start("intern");
      return { taken, fresh: g.pearlsTaken() };
    });
    ok("a pearl taken lands on the run's receipt",
       !pr.err && pr.taken >= 1 && pr.fresh === 0,
       pr.err || `${pr.taken} taken; a new run opens at ${pr.fresh}`);
  }

  console.log("\n=== 22l. THE HUD FITS ON A PHONE ===");
  {
    // Three things went onto the HUD this session - the minimap, the affinity
    // line, den labels - and none of them was ever looked at below 1280px. The
    // minimap shipped as a fixed 148px disc: 12% of a desktop screen and 38% of
    // a phone, sitting exactly where the right thumb drags the camera. And the
    // centred phase line ran straight through the level readout, so a 360px
    // screen printed "CINDERPUP - LV 7" and "MATRIARCH IN 04:49" on top of each
    // other. Both were visible in the first screenshot anyone took.
    const IDS = ["lvl", "phase", "clock", "biome", "stats", "hop", "kit", "hpwrap"];
    const sizes = [["phone", 390, 844], ["small", 360, 640],
                   ["tall", 412, 915], ["desktop", 1280, 760]];
    const rows = [];
    for (const [nm, w, h] of sizes) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h },
        hasTouch: nm !== "desktop", isMobile: nm !== "desktop", deviceScaleFactor: 1 });
      const pp = await ctx.newPage();
      await pp.goto(FILE, { waitUntil: "load" });
      await pp.waitForTimeout(500);
      await pp.evaluate(() => { window.__g.wipeSave(); window.__g.start("intern");
                                window.__g.god(); window.__g.resume();
                                window.__g.step(600, 1/60); });
      await pp.waitForTimeout(400);
      rows.push(await pp.evaluate(ids => {
        const R = {}, PAD = 4;
        for (const id of ids) {
          const e = document.getElementById(id); if (!e) continue;
          const b = e.getBoundingClientRect();
          if (b.width && getComputedStyle(e).display !== "none")
            R[id] = { l: b.left, t: b.top, r: b.right, b: b.bottom };
        }
        // Four pixels of tolerance: a text element's line box overhangs its
        // glyphs, and two things stacked centre-screen touch by a pixel while
        // looking perfectly fine.
        const hit = [], k = Object.keys(R);
        for (let i = 0; i < k.length; i++) for (let j = i + 1; j < k.length; j++) {
          const a = R[k[i]], b = R[k[j]];
          const ox = Math.min(a.r, b.r) - Math.max(a.l, b.l);
          const oy = Math.min(a.b, b.b) - Math.max(a.t, b.t);
          if (ox > PAD && oy > PAD) hit.push(`${k[i]}/${k[j]}`);
        }
        const m = window.__g.mapBox();
        const strip = Object.values(R).filter(r => r.t > innerHeight * 0.75);
        return { hit, mapD: m.d, mapBottom: m.oy + m.d,
                 frac: m.d / Math.min(innerWidth, innerHeight),
                 stripTop: strip.length ? Math.min(...strip.map(r => r.t)) : innerHeight,
                 stripLeft: strip.length ? Math.min(...strip.map(r => r.l)) : innerWidth,
                 mapLeft: m.ox, w: innerWidth };
      }, IDS));
      await ctx.close();
    }
    const named = sizes.map((s, i) => [s[0], rows[i]]);
    ok("nothing on the HUD overlaps anything else, at any size",
       named.every(([, r]) => r.hit.length === 0),
       named.map(([n, r]) => `${n}:${r.hit.join(",") || "ok"}`).join("  "));
    ok("the minimap is a proportion of the screen, not 148 pixels",
       named.every(([, r]) => r.frac <= 0.25 && r.mapD >= 80),
       named.map(([n, r]) => `${n} ${r.mapD.toFixed(0)}px (${(r.frac*100).toFixed(0)}%)`).join("  "));
    ok("and it never sits on the bottom HUD strip",
       named.every(([, r]) => r.mapBottom <= r.stripTop + 4 || r.mapLeft > r.stripLeft),
       named.map(([n, r]) => `${n} map ends ${r.mapBottom.toFixed(0)}, strip at ${r.stripTop.toFixed(0)}`).join("  "));
  }

  console.log("\n=== 22k. THE HORDE CAN REACH YOU NOW ===");
  {
    // FLITTER dives. Everything here is a way this could be a no-op or a
    // cheat: a dive that never fires, one that fires from across the arena,
    // one with no wind-up to read, or one that cannot be dodged by turning -
    // which is the only verb this game claims to be about.
    const r = await page.evaluate(() => {
      const g = window.__g;
      // DISARMED, because the subject here is the bird. This booted with the
      // default kit, and a BONK BAT retune gave the starting weapon the reach
      // and damage to kill a bird at seven metres before it could wind up -
      // three assertions about diving went red because the player got faster,
      // which is the same failure as a check that hardcodes a weapon's radius:
      // it measures something other than what its name says.
      const boot = () => { g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
                           g.freezeEvents(true); g.drainPicks(true); g.place(0, 0);
                           g.disarm(); };
      // 1. it fires, and only from close
      // spawn(t, n, radius) scatters WITHIN the radius, so "spawn at 40" puts
      // some of them on top of you. Ask the distances, not the spawn call.
      boot(); g.spawn("runner", 14, 40);
      g.step(30, 1/60);
      const far = g.dives().filter(d => d.d > 14 && (d.wind > 0 || d.diving)).length;
      boot(); g.spawn("runner", 6, 7);
      let sawWind = 0, sawDive = 0, maxAt = 0;
      for (let i = 0; i < 240; i++) {
        g.step(1, 1/60); g.place(0, 0);
        for (const d of g.dives()) {
          if (d.wind > 0) sawWind++;
          if (d.diving) { sawDive++; maxAt = Math.max(maxAt, d.d); }
        }
      }
      // 2. does it actually land damage the horde could not land before?
      const hurtStill = (() => { boot(); g.spawn("runner", 10, 7);
        for (let i = 0; i < 60 * 8; i++) { g.step(1, 1/60); g.place(0, 0); }
        return g.hurtBy().contact; })();
      // 3. and can it be dodged by turning? same fight, but moving.
      const hurtMoving = (() => { boot(); g.spawn("runner", 10, 7);
        let a = 0;
        for (let i = 0; i < 60 * 8; i++) {
          a += 0.05; g.step(1, 1/60);
          g.place(Math.cos(a) * 7, Math.sin(a) * 7);
        }
        return g.hurtBy().contact; })();
      return { far, sawWind, sawDive, maxAt, hurtStill, hurtMoving };
    });
    ok("nothing winds up from across the arena", r.far === 0,
       `${r.far} birds beyond 14m winding up`);
    ok("a bird close to you winds up", r.sawWind > 0, `${r.sawWind} wind-up frames`);
    ok("and then commits to a dive", r.sawDive > 0, `${r.sawDive} diving frames`);
    ok("the dive is a short crossing, not a charge across the map",
       r.maxAt > 0 && r.maxAt < 14, `furthest frame of a dive: ${r.maxAt}m`);
    ok("standing in front of one costs you", r.hurtStill > 0,
       `${r.hurtStill} contact damage standing still`);
  }

  console.log("\n=== 22j. THE DAMAGE LEDGER SAYS WHO HIT YOU ===");
  {
    // "The autopilot is not being hit" was inferred from the absence of deaths
    // for a whole session before anything counted. Three sources, and each one
    // has to be filed under itself or the ledger is worse than no ledger.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const boot = () => { g.wipeSave(); g.start("intern"); g.freezeSpawns(true);
                           g.freezeEvents(true); g.drainPicks(true); g.place(0, 0); };
      boot();
      const zero = g.hurtBy();
      // contact: a body on top of you
      g.spawn("brute", 4, 1); g.step(120, 1/60);
      const contact = g.hurtBy();
      // spit: a projectile
      boot(); g.spawn("spitter", 6, 8); g.step(60 * 8, 1/60);
      const spit = g.hurtBy();
      // hazard: a boss ability's ground
      boot(); g.boss(0); g.step(60 * 12, 1/60);
      const haz = g.hurtBy();
      return { zero, contact, spit, haz };
    });
    ok("a fresh run has taken nothing", r.zero.total === 0, JSON.stringify(r.zero.hits));
    ok("a body on you is filed as contact",
       r.contact.contact > 0 && r.contact.spit === 0,
       `contact ${r.contact.contact}, spit ${r.contact.spit}, hazard ${r.contact.hazard}`);
    ok("a projectile is filed as a spit",
       r.spit.spit > 0 && r.spit.spit > r.spit.contact,
       `contact ${r.spit.contact}, spit ${r.spit.spit}, hazard ${r.spit.hazard}`);
    ok("and a boss's ground is filed as a hazard",
       r.haz.hazard > 0,
       `contact ${r.haz.contact}, spit ${r.haz.spit}, hazard ${r.haz.hazard}`);
  }

  console.log("\n=== 22i. A TYPE IS SOMEWHERE YOU BELONG ===");
  {
    // Seven types and seven regions, and until now the type was a colour: two
    // lines with the same stat mods played identically wherever you stood. Each
    // type has one region it is at home in and one it is not, and both have to
    // be felt through the fight rather than read off a card.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const cells = () => g.world().cells;
      const at = (id) => { const c = cells().find(x => x.id === id); return c; };
      const out = { lines: {} };
      for (const ch of g.chars()) {
        g.wipeSave(); g.start(ch); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true);
        const a = g.aff();
        // roll until this creature's home AND weak regions are both on the map
        let tries = 0;
        while (tries++ < 300 && !(at(a.home) && at(a.weak))) { g.start(ch); g.drainPicks(true); }
        const home = at(a.home), weak = at(a.weak);
        if (!home || !weak) { out.lines[ch] = "no map"; continue; }
        // Divide the region's own tough mod back out. THE CINDERFLATS is +12% on
        // own account, so a raw 40-vs-46 comparison between two regions is
        // measuring the regions, not the affinity - which is how this first
        // read GHOUL at 47/61 and called it a failure.
        const hitAt = (c) => { g.place(c.x, c.z);
                               return g.hitMe(40) / (g.biomeMod(c.x, c.z).tough || 1); };
        out.lines[ch] = { type: a.type,
                          dWeak: hitAt(weak), dHome: hitAt(home),
                          affHome: (g.place(home.x, home.z), g.aff().now),
                          affWeak: (g.place(weak.x, weak.z), g.aff().now) };
      }
      return { lines: out.lines, count: g.chars().length };
    });
    const rows = Object.entries(r.lines).filter(([, v]) => typeof v === "object");
    // Nine now, not seven: THE COURIER and THE TEMP joined the roster. The
    // count is read off the game rather than written here, so the next line
    // added does not have to come back and edit this number.
    ok("every line has a home and a weakness on the map",
       rows.length === r.count && rows.length >= 9,
       `${rows.length} of ${r.count} lines measured`);
    ok("home ground reads as home for every one of them",
       rows.every(([, v]) => v.affHome === 1 && v.affWeak === -1),
       rows.map(([k, v]) => `${k}:${v.affHome}/${v.affWeak}`).join(" "));
    ok("the wrong ground costs you, and home ground does not",
       rows.every(([, v]) => Math.abs(v.dWeak / v.dHome - 1.15) < 0.02),
       rows.map(([k, v]) => `${k} ${v.dHome.toFixed(1)}->${v.dWeak.toFixed(1)}`).join("  "));

    // and the other half: home ground has to actually hit harder. Same boss,
    // same weapons, same number of frames, two different pieces of ground.
    const out = await page.evaluate(() => {
      const g = window.__g;
      const dmgOn = (id) => {
        g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true);
        let c = null, tries = 0;
        while (tries++ < 300 && !c) { c = g.world().cells.find(x => x.id === id);
                                      if (!c) { g.start("intern"); g.drainPicks(true); } }
        if (!c) return null;
        for (const w of ["bat", "zap", "aura"]) g.give(w, 3);
        g.place(c.x, c.z); g.boss(0);
        const b = g.bossAt();
        g.place(b.x, b.z);                     // stand on it, in the region
        const hp0 = g.bossAt().hp;
        g.step(60 * 3, 1/60);
        const b1 = g.bossAt();
        return { here: g.aff().now, dealt: hp0 - (b1 ? b1.hp : 0) };
      };
      const home = dmgOn(g.chars() && "ash"), neutral = dmgOn("bone");
      return { home, neutral };
    });
    ok("home ground hits harder",
       out.home && out.neutral && out.home.here === 1 && out.neutral.here === 0 &&
       out.home.dealt > out.neutral.dealt * 1.12,
       out.home && out.neutral
         ? `${out.neutral.dealt.toFixed(0)} damage on neutral ground -> ${out.home.dealt.toFixed(0)} at home`
         : "region not on the map");
  }

  console.log("\n=== 22h. THE ARENA CAN BE REPLAYED ===");
  {
    // worldSeed was recorded from the first day and could never be replayed,
    // because generation called Math.random() directly - a label on a run nobody
    // could re-enter. The point is not seed-sharing: every balance trial rolled
    // a fresh arena, so region layout and den placement were variance baked into
    // a bench whose noise band has already cost this project two rounds.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const snap = () => ({ ter: g.terHash(),
                            biomes: g.biomes().map(b => `${b.id}@${b.x},${b.z}`).join("|"),
                            dens: g.dens().map(d => `${d.k}${d.x},${d.z}:${d.n}:${d.boon}`).join("|") });
      g.wipeSave();
      g.pin(1234567); g.start("intern"); const a = snap();
      g.start("ox");                       const b = snap();
      g.pin(7654321); g.start("intern");   const c = snap();
      g.pin(1234567); g.start("intern");   const d = snap();
      g.pin(null);   g.start("intern");    const e1 = snap();
      g.start("intern");                   const e2 = snap();
      return { a, b, c, d, e1, e2, seed: g.world().seed };
    });
    ok("the same seed builds the same ground",
       r.a.ter === r.b.ter && r.a.ter === r.d.ter,
       `${r.a.ter} / ${r.b.ter} / ${r.d.ter}`);
    ok("and the same regions in the same places",
       r.a.biomes === r.d.biomes && r.a.biomes.length > 20,
       `${r.a.biomes.split("|").length} regions, identical: ${r.a.biomes === r.d.biomes}`);
    ok("and the same dens holding the same boons",
       r.a.dens === r.d.dens && r.a.dens.length > 40,
       `${r.a.dens.split("|").length} dens, identical: ${r.a.dens === r.d.dens}`);
    ok("a different seed builds a different arena",
       r.c.ter !== r.a.ter && r.c.dens !== r.a.dens, `${r.a.ter} vs ${r.c.ter}`);
    ok("and unpinned still rolls a fresh one every run",
       r.e1.ter !== r.e2.ter, `${r.e1.ter} vs ${r.e2.ter}`);

    // The arena was only a slice of it. Pinned to one arena, the same build
    // measured 10/42 and 14/42 - the spawn mix, the crits, the drops, the draft
    // sampling and the autopilot's own choices were all still Math.random().
    // With the run stream seeded too, a trial is a pure function of its inputs,
    // which is what lets a candidate and its control share forty-two worlds.
    // Snapshot the module-level state a run can inherit. It matches a freshly
    // loaded page now - noEvents, a stale hand of cards and a negative hitstop
    // were all leaking through startRun and are reset there - and the warm-up
    // trial STILL differs, so whatever is left is not one of these twenty-five
    // knobs. Printed only when it matters, so the pass is quiet.
    const snapBefore = await page.evaluate(() => window.__g.snapshot());
    const det = await page.evaluate(() => {
      const g = window.__g;
      const trial = () => { g.wipeSave(); g.start("intern"); g.bot(true);
                            const st = g.runOut();
                            return `${st.t.toFixed(2)}/${st.lvl}/${st.kills}`; };
      g.pin(999); g.pinRun(555);
      // NO WARM-UP ANY MORE. This used to throw away up to four trials until
      // two of them agreed, because the first pinned run of a pair reliably
      // differed from the rest and nobody could find why. The why was the
      // spatial grid: near() and hitNear() read a grid rebuilt in step()'s
      // world section, after the block the autopilot steers from, so a run's
      // first frame read the PREVIOUS RUN's grid - empty on the very first
      // trial, full of a dead run's bodies on every one after. The bot opened
      // on a different heading, the spawn director biases arrivals off that
      // heading, and ten seconds later it was a different game. startRun()
      // rebuilds the grid now, so the honest question can be asked directly:
      // the first pinned trial and the two after it must all agree.
      const a = trial(), b = trial(), c0 = trial();
      g.pinRun(556);            const c = trial();
      g.pin(null); g.pinRun(null);
      const d = trial(), e = trial();
      return { a, b, c0, c, d, e };
    });
    ok("a fully pinned trial is reproducible to the kill",
       det.a === det.b && det.b === det.c0,
       `${det.a} / ${det.b} / ${det.c0}` +
       (det.a === det.b && det.b === det.c0 ? "" :
        `   (state leak, entering state ${JSON.stringify(snapBefore)})`));
    ok("a different run seed on the same arena is a different run",
       det.c !== det.a, `${det.a} vs ${det.c}`);
    ok("and unpinned play is still random",
       det.d !== det.e, `${det.d} vs ${det.e}`);
  }

  console.log("\n=== 22g. YOU CAN SEE WHERE YOU ARE ===");
  {
    // Twenty-five dens across 222,000 square metres with no map is a lottery,
    // not an explorable arena: the dormant ember only draws inside 120m and the
    // woken column only exists once you are already in the fight. The regions
    // never move once a world is rolled, so the background is baked once per run
    // rather than sampling seven Voronoi cells per pixel per frame.
    const m = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true); g.place(0, 0);
      await frame(); await frame();
      const baked = g.map();
      // the map has to be REBUILT for a new world, not carried over
      const h0 = g.terHash();
      g.start("ox");
      // resume, or a lost pointer lock leaves the game paused and the corner
      // this check samples is a flat overlay - which is exactly what it read
      // once the section above started ending its own runs by dying.
      g.resume(); g.place(0, 0);
      await frame(); await frame();
      return { baked, h0, h1: g.terHash(), rebaked: g.map(),
               live: g.state().over === false };
    });
    ok("the run bakes a map of its own arena",
       m.baked && m.baked.px > 100 && m.baked.painted.opaque > 12000,
       m.baked ? `${m.baked.px}px, ${m.baked.painted.opaque} painted pixels` : "no map");
    ok("and it is a map, not one flat colour",
       m.baked && m.baked.painted.tones >= 6,
       m.baked ? `${m.baked.painted.tones} distinct tones` : "no map");
    ok("a new arena rebakes it",
       m.h0 !== m.h1 && m.rebaked && m.rebaked.painted.opaque > 12000,
       `terrain ${m.h0} -> ${m.h1}, ${m.rebaked ? m.rebaked.painted.opaque : 0} painted`);

    // and it actually reaches the screen. Retried: a single capture can land on a
    // frame the compositor has not painted yet, which reads as a flat corner and
    // says nothing about whether the map is drawn. Take the best of five, and
    // require that drawMap actually ran between them - a flat corner with the
    // counter stuck is a paused game, which is a different failure.
    const hits0 = await page.evaluate(() => window.__g.mapHits());
    let seen = 0, shot = null, over = "none";
    for (let i = 0; i < 5 && seen < 10; i++) {
      // Clear anything that could be sitting on top of the corner, and record
      // what it was. A flat corner told me nothing three times running; the
      // overlay name is the difference between "no map" and "a modal".
      over = await page.evaluate(() => {
        window.__g.drainPicks(true); window.__g.resume();
        const up = ["pick", "end", "paused", "menu"]
          .filter(id => { const el = document.getElementById(id);
                          return el && getComputedStyle(el).display !== "none"
                                    && getComputedStyle(el).opacity !== "0"; });
        for (const id of up) { const el = document.getElementById(id);
                               el.classList.remove("on"); el.style.display = "none"; }
        return up.join(",") || "none";
      });
      await page.waitForTimeout(180);
      shot = await page.screenshot();
      seen = Math.max(seen, await page.evaluate(async b64 => {
      const img = new Image();
      await new Promise(r => { img.onload = r; img.src = "data:image/png;base64," + b64; });
      const c = document.createElement("canvas"); c.width = img.width; c.height = img.height;
      const x2 = c.getContext("2d"); x2.drawImage(img, 0, 0);
      // bottom-right corner, where the map lives
      const w = c.width, h = c.height;
      const d = x2.getImageData(w - 190, h - 190, 180, 180).data;
      const tones = new Set();
      for (let i = 0; i < d.length; i += 4)
        tones.add(((d[i] >> 4) << 8) | ((d[i+1] >> 4) << 4) | (d[i+2] >> 4));
      return tones.size;
    }, shot.toString("base64")));
    }
    const hits1 = await page.evaluate(() => window.__g.mapHits());
    ok("the map is being drawn every frame", hits1 > hits0,
       `${hits1 - hits0} draws across the captures`);
    ok("and it is drawn on the screen, not just in memory",
       seen >= 10, `${seen} distinct tones in the corner it occupies` +
                   (over === "none" ? "" : `, overlays up: ${over}`));
  }

  console.log("\n=== 22f. THE LANDMARKS HAVE SOMETHING IN THEM ===");
  {
    // Landmarks were scenery that side events happened to prefer as spawn
    // points. A place you can see from far off and might decide to take is an
    // explorable area; a rock you have no reason to walk to is not. Each den is
    // dormant until you are close, wakes into the pack the terrain implies,
    // goes quiet again if you leave, and pays a boon when cleared. Every one of
    // those five states is a place this could silently do nothing.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeEvents(true); g.drainPicks(true);
      for (const w of ["bat", "zap", "aura"]) g.give(w, 3);
      const all = g.dens();
      if (!all.length) return { err: "no dens rolled", stats: g.denStats() };
      const d = all[0], find = () => g.dens().find(m => m.k === d.k && m.x === d.x);
      // standing ON it, before the grace is up
      g.place(d.x, d.z); g.step(1, 1/60);
      const grace = find(), graceT = g.state().t;
      g.skipTo(90);
      // TOWARD THE CENTRE, at every distance. The arena confines a position, so
      // stepping +60 or +200 on x from a den that rolled near the rim clamps
      // straight back inside the wake radius and the check reads "still awake"
      // for a reason that is not the game. The retire case was fixed this way
      // and the 60m case was left on +x; it came back woke=true in a suite run
      // where den[0] happened to roll out east. Walking d -> d - d/|d| * r is
      // exactly r metres from the den and never further out than the den is.
      const L = Math.hypot(d.x, d.z) || 1;
      const away = r => g.place(d.x - d.x / L * r, d.z - d.z / L * r);
      away(60); g.step(1, 1/60);                 const far = find();
      g.place(d.x + 6,  d.z); g.step(1, 1/60);   const near = find();
      away(150); g.step(1, 1/60);
      const left = find();
      g.place(d.x + 6,  d.z); g.step(1, 1/60);   const again = find();
      g.step(60 * 45, 1/60);                      const done = find();
      // The pack a den wakes is the pack it ADVERTISES - the HUD label reads
      // "N CERATOP" off these same two fields - so that is the number held to.
      // An ANGRY den sends the elite fraction, floored at three: the first den
      // of an unpinned arena has rolled "3 brute" and failed a ">3" here that
      // only ever meant "more than a straggler".
      const want = d.angry ? Math.max(3, Math.ceil(d.n * .55)) : d.n;
      return { total: all.length, stats: g.denStats(), species: d.sp, angry: d.angry, want,
               grace, graceT, far, near, left, again, done, boons: g.boons() };
    });
    ok("the arena rolls dens into its landmarks",
       !r.err && r.total > 4 && r.total < r.stats.marks,
       r.err || `${r.total} dens across ${r.stats.marks} landmarks`);
    ok("nothing wakes in the opening seconds",
       r.grace && !r.grace.woke,
       r.grace ? `woke=${r.grace.woke} standing on it at T=${r.graceT}s` : "no den");
    ok("a den is asleep until you go to it",
       r.far && !r.far.woke, r.far ? `woke=${r.far.woke} at 60m` : "no den");
    ok("and it wakes with the pack it advertises, of what lives there",
       r.near && r.near.woke && r.near.alive >= 3 && r.near.alive === r.want,
       r.near ? `${r.near.alive} ${r.angry ? "elite " : ""}${r.species} awake at 6m, ${r.want} promised` : "no den");
    ok("walking away puts it back to sleep - the fight is not a leash",
       r.left && !r.left.woke && r.left.alive === 0,
       r.left ? `woke=${r.left.woke} alive=${r.left.alive} at 200m` : "no den");
    ok("and it can be taken later instead - the full pack again, not the survivors",
       r.again && r.again.woke && r.again.alive === r.want,
       r.again ? `${r.again.alive} awake on the second visit` : "no den");
    // A reward you only learn after the fight is a surprise. A den advertises a
    // SPECIFIC boon from sixty metres, so going to one is a plan.
    const adv = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      // NOT freezeSpawns: that sets noSpawn, and a den will not wake into a world
      // where spawning is off. Third time this trap has been walked into today.
      g.wipeSave(); g.start("intern"); g.god(); g.freezeEvents(true);
      g.drainPicks(true); g.skipTo(90);
      for (const w of ["bat", "zap", "aura"]) g.give(w, 3);   // enough to take one
      const dens = g.dens();
      const target = dens[0];
      g.place(target.x + 20, target.z);        // close enough to read, not to wake
      await frame(); await frame();
      const shot = { named: dens.every(d => d.boon && d.n > 0),
                     spread: new Set(dens.map(d => d.boon)).size,
                     total: dens.length, want: target.boon };
      g.place(target.x + 6, target.z); g.step(1, 1/60);
      g.step(60 * 45, 1/60);
      return Object.assign(shot, { got: g.boons() });
    });
    ok("every den names a boon and a pack size before you commit",
       adv.named, `${adv.total} dens, all named: ${adv.named}`);
    ok("and a run's dens are not six of the same offer",
       adv.spread >= 4, `${adv.spread} distinct boons across ${adv.total} dens`);
    ok("clearing one pays the boon it advertised",
       adv.got.includes(adv.want), `advertised ${adv.want}, got ${adv.got.join(", ") || "none"}`);

    ok("clearing one pays a boon",
       r.done && r.done.cleared && r.boons.length > 0,
       r.done ? `cleared=${r.done.cleared}, boons: ${r.boons.join(", ") || "none"}` : "no den");

    // One of each boon, ever. The altar's old fallback - re-roll from the whole
    // list once the pool is dry - was survivable at one altar a run and is an
    // unbounded multiplier at twenty-five dens: HEAVY HANDS is x1.15 compounding.
    const cap = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true);
      const dmg0 = g.state().dps;
      for (let i = 0; i < 40; i++) g.boon();      // far more than the list holds
      const b = g.boons();
      return { n: b.length, uniq: new Set(b).size, dmg0, dmg1: g.state().dps };
    });
    // <= 10, from <= 8: the table grew to nine with MOSSHIDE and THERMALS.
    // The cap the check actually guards is n === uniq - no boon twice - and
    // the ceiling only exists to notice the table growing without this test
    // hearing about it, which is exactly what just happened.
    ok("a boon can be taken once, however many dens you clear",
       cap.n === cap.uniq && cap.n <= 10,
       `${cap.n} boons, ${cap.uniq} distinct, after forty awards`);
    ok("so run power cannot compound off them",
       cap.dmg1 / cap.dmg0 < 1.6,
       `damage x${(cap.dmg1 / cap.dmg0).toFixed(2)} with every boon in the game`);
  }

  console.log("\n=== 22e. BREADTH COSTS SLOTS ===");
  {
    // Six weapon slots was sized for five ranks. At three, a full kit is 36 picks
    // plus six evolutions against the ~80 a long run hands you - so every run
    // took six of the eight weapons, maxed all of them, and came out as the same
    // build as every other run. Four chosen weapons and five passives, and your
    // line's own move is free on top, because that move is the whole reason a
    // CINDERPUP run should not look like a ZAPLET run.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      const lim = g.slots();
      for (let i = 0; i < 400; i++) { g.xp(400); g.step(1, 1/60); }   // draft, forever
      const full = g.slots();
      g.monLvl && g.evolveTo(2);                                       // learn the line's move
      g.step(1, 1/60);
      return { lim, full, after: g.slots() };
    });
    ok("a run cannot carry more than four chosen weapons",
       r.full.carried <= r.lim.w,
       `${r.full.carried} carried against a limit of ${r.lim.w}`);
    ok("nor more than five passives",
       r.full.passives <= r.lim.p,
       `${r.full.passives} carried against a limit of ${r.lim.p}`);
    ok("and it fills them - the cap is a choice, not a shortage",
       r.full.carried === r.lim.w && r.full.passives === r.lim.p,
       `${r.full.carried}w ${r.full.passives}p`);
    ok("the line's own move rides free on top",
       r.after.granted >= 1 && r.after.carried <= r.lim.w,
       `${r.after.carried} chosen + ${r.after.granted} granted`);
  }

  console.log("\n=== 22d. A RUN BEGINS AT ZERO ===");
  {
    // HEAD START handed you its levels at t=0, so a run with the shop maxed
    // OPENED on a stack of draft screens - "PICK ONE, 3 MORE QUEUED" - before a
    // single enemy had walked on. The run has to start with the game, not with
    // a menu; the levels are banked and released over the first minute instead.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave();
      g.setUpgrades({ hp:6, dmg:6, spd:5, mag:5, cd:5, crit:5, armor:5, start:3, rev:2 });
      g.start("intern"); g.freezeSpawns(true); g.freezeEvents(true);
      const t0 = g.state();
      g.step(1, 1/60);
      const t1 = g.state();
      g.step(60 * 40, 1/60);              // forty seconds of play
      const t2 = g.state();
      return { lvl0: t0.lvl, picking0: t1.picking, pending0: t1.pending, lvl2: t2.lvl };
    });
    ok("a maxed shop does not open the run on a draft screen",
       r.picking0 === false && r.pending0 === 0,
       `picking=${r.picking0}, ${r.pending0} queued at t=0`);
    ok("and the run starts at level 1", r.lvl0 === 1, `level ${r.lvl0}`);
    ok("the head start still arrives, during play",
       r.lvl2 > r.lvl0, `level ${r.lvl0} -> ${r.lvl2} after forty seconds`);
  }

  console.log("\n=== 23. THE ARENA IS ROLLED, NOT REMEMBERED ===");
  {
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);

      const snap = () => { const w = g.world();
                           return { key: w.cells.map(c=>c.id+"@"+c.x+","+c.z).join("|"),
                                    marks: w.marks.map(m=>m.k+"@"+m.x+","+m.z).join("|"),
                                    ter: g.terHash(), w }; };
      const a = snap(), b = (g.reroll(), snap()), c = (g.reroll(), snap());

      // coverage: does the whole disc resolve, and to more than one thing
      const RIM = g.rim(), seen = {};
      let unresolved = 0;
      for (let i = 0; i < 900; i++) {
        const th = Math.random()*Math.PI*2, rr = Math.sqrt(Math.random())*RIM*0.98;
        const bm = g.biomeAt(Math.cos(th)*rr, Math.sin(th)*rr);
        if (!bm || !bm.id) unresolved++; else seen[bm.id] = (seen[bm.id]||0)+1;
      }

      // spawn must always be neutral, across many rolls
      let badSpawn = 0;
      for (let i = 0; i < 60; i++) { g.reroll(); if (g.biomeAt(0,0).id !== "grass") badSpawn++; }

      // landmarks: inside the wall, clear of spawn, not stacked on each other
      let outside = 0, tooClose = 0, overlapping = 0, total = 0;
      for (let i = 0; i < 40; i++) {
        const w = g.reroll();
        for (let j = 0; j < w.marks.length; j++) {
          const m = w.marks[j]; total++;
          if (Math.hypot(m.x, m.z) > RIM) outside++;
          if (Math.hypot(m.x, m.z) < 18) tooClose++;
          for (let k = j+1; k < w.marks.length; k++)
            if (Math.hypot(m.x-w.marks[k].x, m.z-w.marks[k].z) < 10) overlapping++;
        }
      }
      return { a, b, c, seen, unresolved, badSpawn, outside, tooClose, overlapping, total };
    });
    ok("no two runs get the same layout",
       r.a.key !== r.b.key && r.b.key !== r.c.key && r.a.key !== r.c.key,
       `${new Set([r.a.key, r.b.key, r.c.key]).size} distinct layouts of 3`);
    ok("and the ground mesh is actually rebuilt for it",
       new Set([r.a.ter, r.b.ter, r.c.ter]).size === 3,
       `terrain hashes ${r.a.ter}, ${r.b.ter}, ${r.c.ter}`);
    ok("the landmarks move too",
       new Set([r.a.marks, r.b.marks, r.c.marks]).size === 3);
    ok("every point in the arena belongs to a region",
       r.unresolved === 0, `${r.unresolved} unresolved of 900`);
    ok("and more than one region is on the map",
       Object.keys(r.seen).length >= 4,
       Object.entries(r.seen).map(([k,v])=>`${k}:${v}`).join(" "));
    ok("you never open a run standing in one of the bad ones",
       r.badSpawn === 0, `${r.badSpawn} of 60 rolls put you somewhere else`);
    ok("landmarks stay inside the wall", r.outside === 0, `${r.outside} of ${r.total} outside`);
    ok("and off the spawn point", r.tooClose === 0, `${r.tooClose} of ${r.total} within 18m`);
    ok("and off each other", r.overlapping === 0, `${r.overlapping} overlapping pairs`);
  }

  console.log("\n=== 23b. STANDING SOMEWHERE HAS TO MEAN SOMETHING ===");
  {
    // A region you can only identify by its colour is a texture swap. Each one
    // is measured through the thing it claims to change.
    const r = await page.evaluate(() => {
      const g = window.__g;
      // roll until the map contains the regions we need to stand in
      let w = null;
      for (let i = 0; i < 400; i++) {
        g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true);
        w = g.world();
        const ids = w.cells.map(c => c.id);
        if (ids.includes("bog") && ids.includes("ash") && ids.includes("sand")) break;
      }
      const cellOf = id => w.cells.find(c => c.id === id);
      // g.bot(false) FIRST. A section that left the autopilot running hands this
      // one a driver that presses jump, and a hop chain multiplies move speed by
      // up to 1.6 - which is more than the sludge's 0.86 takes away. It read
      // 8.03 on the green and 7.97 in the bog: not a broken biome, a chain that
      // was two links deep for the first reading and six for the second. The
      // measurement now refuses to report a speed taken mid-chain.
      let chain = 0;
      const speedAt = (x, z) => {
        g.bot(false); g.place(x, z);
        dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
        for (let i = 0; i < 60; i++) { g.step(1/60); g.place(x, z); }
        const h = g.hop();
        chain = Math.max(chain, h.n);
        dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
        return h.spd;
      };
      const green = cellOf("grass"), bog = cellOf("bog"), ash = cellOf("ash");
      const out = { ids: w.cells.map(c=>c.id) };
      out.vGreen = speedAt(green.x, green.z);
      out.vBog   = speedAt(bog.x, bog.z);
      out.inBog  = g.biomeAt(bog.x, bog.z).id;
      out.chain  = chain;

      // damage taken in the ashes vs on the green, same hit
      const hitAt = (x, z) => { g.place(x, z); return g.hitMe(40); };
      out.dGreen = hitAt(green.x, green.z);
      out.dAsh   = hitAt(ash.x, ash.z);
      return out;
    });
    ok("the tarpits are slower than the fernlands",
       r.vBog < r.vGreen * 0.92,
       `${r.vGreen.toFixed(2)} m/s on THE FERNLANDS -> ${r.vBog.toFixed(2)} in THE TARPITS`);
    ok("and it is the tarpits you were standing in", r.inBog === "bog", r.inBog);
    ok("and neither reading was taken mid-hop-chain", r.chain === 0,
       `deepest chain during the measurement: ${r.chain}`);
    ok("the cinderflats cost you more for the same hit",
       r.dAsh > r.dGreen * 1.05,
       `${r.dGreen.toFixed(1)} damage on THE FERNLANDS -> ${r.dAsh.toFixed(1)} in THE CINDERFLATS`);
  }

  console.log("\n=== 23c. THE THICKET SHORTENS YOUR REACH ===");
  {
    // The eighth region and the first that touches a WEAPON stat rather than a
    // player one. Every other region's effect was already measured by 23b's
    // pattern - speed, damage taken - so this asks the same kind of question of
    // reach: where does a ring STOP landing, in the open versus in the thicket.
    // forceBiome exists for exactly this - the alternative is 23b's own
    // reject-and-reroll loop, which this section does not need since the biome
    // can be set directly rather than waited for.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const boundary = (biome) => {
        let farthest = 0;
        for (let d = 0; d <= 20; d += 0.5) {
          g.pin(20260821); g.pinRun(20260821);
          g.wipeSave(); g.start("intern"); g.god(); g.drainPicks(true); g.freezeSpawns(true);
          g.give("aura", 4);
          if (!g.forceBiome(biome)) throw new Error("forceBiome failed for " + biome);
          g.boss(3); g.step(120);
          const b0 = g.bossAt(), hp0 = b0.hp;
          g.place(b0.x + d, b0.z);
          for (let i = 0; i < 30; i++) g.step(1);
          if (g.bossAt().hp < hp0) farthest = d;
        }
        return farthest;
      };
      return { grass: boundary("grass"), thicket: boundary("bramble"),
               inThicket: g.biomeIdAt(0, 0) };
    });
    // -18% on the WEAPON's own radius, diluted at the boundary by the boss's
    // own body - hitNear counts rad + bossRad, and only rad is cut - so the
    // measured shrink at the edge is smaller than the raw modifier and the
    // window below is set from that, not from -18% directly.
    ok("a ring reaches less far in THE THICKET",
       r.thicket < r.grass * 0.95 && r.thicket > r.grass * 0.75,
       `${r.grass}m in THE FERNLANDS -> ${r.thicket}m in THE THICKET`);
  }

  console.log("\n=== 23d. THE WARRENS SPAWN MORE OF THEM ===");
  {
    // The ninth region and the first that touches the DIRECTOR: +35% spawn
    // rate while the player stands in it. Measured the only way a spawn rate
    // can be - count the arrivals. Same pinned seed, same 40 phase-0 seconds,
    // a disarmed god so nothing dies and nothing interferes; the only variable
    // is the ground under the player's feet.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const arrivals = (biome) => {
        g.pin(777); g.pinRun(777);
        g.wipeSave(); g.start("intern"); g.god(); g.disarm();
        g.drainPicks(true); g.freezeEvents(true); g.place(0, 0);
        if (!g.forceBiome(biome)) throw new Error("forceBiome failed for " + biome);
        g.clearEnemies();
        g.step(40 * 60, 1/60);
        return g.state().enemies;
      };
      return { grass: arrivals("grass"), warren: arrivals("warren") };
    });
    // 40s at 1.2/s is 48 on grass and 64-65 in the warrens; the window is set
    // off the ratio so a director retune that moves the base rate does not
    // break a test about the REGION.
    ok("the horde arrives faster in THE WARRENS",
       r.warren > r.grass * 1.20 && r.warren < r.grass * 1.50,
       `${r.grass} arrivals in 40s on THE FERNLANDS -> ${r.warren} in THE WARRENS`);
  }

  console.log("\n=== 23e. THE HOTSPRINGS MEND YOU FASTER ===");
  {
    // The tenth region and the first that touches REGENERATION. Every heal in
    // the game trickles through one line in step(), so the region is measured
    // at that stat's only outlet: same character, same 20 seconds, an empty
    // swept field with events frozen so nothing else can move the bar - the
    // only variable is the ground under the animal. No god(), deliberately:
    // god sets hp to 1e9 and the measurement needs a bar with room to climb.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const healed = (biome) => {
        g.pin(777); g.pinRun(777);
        g.wipeSave(); g.start("intern"); g.disarm();
        g.drainPicks(true); g.freezeEvents(true); g.freezeSpawns(true);
        g.place(0, 0);
        if (!g.forceBiome(biome)) throw new Error("forceBiome failed for " + biome);
        const from = g.setHp(40);
        g.step(20 * 60, 1/60);
        return +(g.hp() - from).toFixed(1);
      };
      return { grass: healed("grass"), spring: healed("spring") };
    });
    // base regen is deterministic (no crits, no drops in an empty field), so
    // the ratio should land on 2.5 nearly exactly; the window is width for
    // frame-count rounding, not for noise.
    ok("standing in THE HOTSPRINGS heals two and a half times as fast",
       r.spring > r.grass * 2.2 && r.spring < r.grass * 2.8,
       `+${r.grass} HP in 20s on THE FERNLANDS -> +${r.spring} in THE HOTSPRINGS`);
  }

  console.log("\n=== 23f. AN ANGRY DEN WAKES ELITE ===");
  {
    // About one den in five wakes as an ELITE pack: fewer bodies, the full
    // elite treatment apiece, double the coin payout. Rolled off the mark's
    // own seed so it is a property of the world, findable by rerolling.
    // NOT freezeSpawns - a den will not wake into a world where spawning is
    // off; that trap is already documented at the section-21 den harness.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeEvents(true);
      g.drainPicks(true);
      let d = null;
      for(let seed = 500; seed < 560 && !d; seed++){
        g.reroll(seed);
        // a THE-named kind (everything but crater), so the headline check
        // below cannot pass vacuously on "ANGRY CRATER"
        d = g.dens().find(m => m.angry && m.k !== "crater");
      }
      if(!d) return { err: "no angry non-crater den in 60 seeds" };
      g.skipTo(90);                                 // past the wake grace
      g.place(d.x + 6, d.z); g.step(2, 1/60);
      const woke = g.dens().find(m => m.x === d.x && m.z === d.z);
      const el = g.elites();
      return { woke: !!(woke && woke.woke), alive: woke ? woke.alive : 0,
               elites: el.n, mult: el.mult,
               alert: g.alerts().slice(-1)[0] || "" };
    });
    // elites() reports the HP multiplier against species base; an angry pack
    // carries ELITE.hp (3.2) on top of hpScale(90s) ~1.26, so ~4 - while a
    // plain den pack sits at 1.25 x 1.26 and an ambient spawn at 90s cannot
    // be elite at all (ELITE_FROM is 360). Elite crowns before minute six can
    // only have come from the den.
    ok("an angry den rolls, wakes, and the pack comes up elite",
       !r.err && r.woke && r.alive >= 3 && r.elites >= r.alive && r.mult > 2.8,
       r.err || `${r.alive} awake, ${r.elites} wearing crowns at x${r.mult} toughness`);
    // "ANGRY THE TUSKS" is not English; the article yields to the adjective
    ok("and the wake headline reads as English",
       !r.err && /^ANGRY [A-Z]/.test(r.alert) && !r.alert.startsWith("ANGRY THE "),
       r.err || JSON.stringify(r.alert));
  }

  console.log("\n=== 23g. THE UPWELLING RAINS GEMS AND ROCK ===");
  {
    // The fourth event kind. Its whole design is one clock driving both
    // halves, so the check asserts both at once: gems accumulate AND
    // hazards exist while it lives, and it subsides on schedule. The player
    // stands well outside the disc so pickup cannot eat the evidence.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.disarm();
      // freezeEvents stops the DIRECTOR, not a manual spawn - without it the
      // timer rolled a fresh event mid-check and, one run in five, that
      // fresh event was itself a storm, so "it subsides" read the new one
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      g.place(0, 0);
      g.clearGems();
      const gems0 = g.state().gems;
      g.spawnEvent("storm", 20, 0);
      g.step(10 * 60, 1/60);
      const mid = { gems: g.state().gems, haz: g.haz().n };
      g.step(25 * 60, 1/60);
      const still = g.events().some(e => e.kind === "storm");
      return { gems0, mid, still };
    });
    ok("the upwelling drops gems and telegraphed rock while it lives",
       r.mid.gems > r.gems0 + 6 && r.mid.haz > 0,
       `+${r.mid.gems - r.gems0} gems on the ground and ${r.mid.haz} hazards after 10s`);
    ok("and it subsides instead of raining forever",
       !r.still, "gone after its 26 seconds");
  }

  console.log("\n=== 23h. THE LAKES GROW PEARLS ===");
  {
    // With the director frozen, the kit disarmed and the field swept, NOTHING
    // in the game can put a gem on the ground except a pearl - so the check
    // needs no gem-position hook: any gem that exists after thirty quiet
    // seconds beside a lake is the feature, and any gem that exists after
    // thirty quiet seconds in the middle of nowhere is a bug.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.disarm();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const L = g.lakes()[0];
      if(!L) return { err: "no lakes rolled" };
      g.clearGems();
      g.place(L.x + L.r + 14, L.z);              // beside it, not in it
      g.step(30 * 60, 1/60);
      const near = g.state().gems;
      // somewhere no lake can reach: walk candidate spots until one clears
      // 70m from every lake on the map
      let fx = 0, fz = 0, found = false;
      for(let a = 0; a < 24 && !found; a++){
        const x = Math.cos(a * 2.4) * (40 + a * 8), z = Math.sin(a * 2.4) * (40 + a * 8);
        if(g.lakes().every(l => Math.hypot(l.x - x, l.z - z) > 70)){
          fx = x; fz = z; found = true; }
      }
      if(!found) return { err: "no lake-free ground found" };
      g.clearGems();
      g.place(fx, fz);
      g.step(30 * 60, 1/60);
      return { near, far: g.state().gems };
    });
    ok("a lake beside you grows a pearl",
       !r.err && r.near >= 1 && r.near <= 3,
       r.err || `${r.near} pearl(s) surfaced in 30s beside the lake`);
    ok("and open ground grows nothing",
       !r.err && r.far === 0,
       r.err || `${r.far} gems appeared 70m from every lake`);
  }

  console.log("\n=== 23i. THE GROUND CHOOSES ITS ANIMALS ===");
  {
    // Biomes used to change the rate and the stats but never WHO arrives -
    // the WARRENS and the GLACIER sent the same mix. fauna weights lean on
    // the phase table per biome. Counted from the director's own output:
    // ~500 standing bodies per ground at a phase where all five kinds exist.
    // Skitters arrive five at a time in every biome alike, so shares compare
    // across biomes even though the pack mechanism inflates them everywhere.
    const r = await page.evaluate(() => {
      const g = window.__g;
      // PINNED, and three rounds. This is a statistical check on a spawn
      // table - across six seeds the ice/ferns runner odds ratio runs 1.33 to
      // 2.34 - and at two rounds of 250 it sat close enough to its 1.2 bar
      // that a shift in the shared RNG stream upstream (R256's per-animal
      // wind-up jitter draws one number per boss) turned it red every run
      // with the same 16% vs 16%. A pinned stream makes the sample the same
      // sample in the suite and alone; eight rounds (R261: the brute is 2-4% of
      // a field - forty animals in two thousand - and its ice/ferns odds ratio
      // runs .39 to .77 across six seeds against a true halving, so a short
      // sample against a .75 bar turned on a dozen brutes) keep both shares
      // out of the noise, and the bar sits at .8.
      g.wipeSave(); g.pin(7); g.start("intern"); g.god(); g.disarm();
      g.freezeEvents(true); g.drainPicks(true); g.setShake(0);
      g.skipTo(400);                       // phase t=360: all five kinds live
      // INTERLEAVED. The mix drifts with the clock - brutes climb through the
      // phases - and measuring the three grounds one after the other put the
      // ice a minute later than the ferns, which is where "heavy things stay
      // off the ice" went to 4% against 4% however long it sampled. One
      // round of each ground in turn, eight times, and all three see the same
      // minute.
      const tallies = { grass:{}, warren:{}, ice:{} };
      for(let round = 0; round < 8; round++){
        for(const biome of ["grass", "warren", "ice"]){
          g.forceBiome(biome); g.clearEnemies();
          for(let i = 0; i < 4000 && g.state().enemies < 250; i++) g.step(1, 1/60);
          const c = g.comp(), tally = tallies[biome];
          for(const k in c) tally[k] = (tally[k] || 0) + c[k];
        }
      }
      const share = biome => { const tally = tallies[biome], tot = Object.values(tally).reduce((a, b) => a + b, 0) || 1;
        const s = {}; for(const k in tally) s[k] = tally[k] / tot; return s; };
      const ferns = share("grass"), warren = share("warren"), ice = share("ice");
      return { ferns, warren, ice };
    });
    // ODDS, not shares: skitter bodies are ~two-thirds of every field because
    // packs arrive six at a time, so a share near its ceiling can never clear
    // a x1.25 bar however hard the biome leans. Odds ratios stay linear.
    const pct = v => `${Math.round((v || 0) * 100)}%`;
    const odds = v => (v || 0) / Math.max(1e-9, 1 - (v || 0));
    ok("the warrens pour raptorlings",
       odds(r.warren.skitter) > odds(r.ferns.skitter) * 1.35,
       `skitter ${pct(r.warren.skitter)} (odds ${odds(r.warren.skitter).toFixed(2)}) in the warrens vs ` +
       `${pct(r.ferns.skitter)} (odds ${odds(r.ferns.skitter).toFixed(2)}) on ferns`);
    ok("the glacier belongs to the divers",
       odds(r.ice.runner) > odds(r.ferns.runner) * 1.2,
       `runner ${pct(r.ice.runner)} on ice vs ${pct(r.ferns.runner)} on ferns`);
    ok("and heavy things stay off the ice",
       odds(r.ice.brute) < odds(r.ferns.brute) * 0.8,
       `brute ${pct(r.ice.brute)} on ice vs ${pct(r.ferns.brute)} on ferns`);
  }

  console.log("\n=== 24. THE DEV PANEL IS WIRED TO SOMETHING ===");
  {
    // It shipped with UNLOCK EVERYTHING and WIPE SAVE calling functions that
    // did not exist - the patch defining them aborted on a later assertion and
    // wrote nothing, and only the half that DREW them got re-run. 225 checks
    // passed, because not one of them pressed a button.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeAll();
      const menu = g.devWiring();
      g.start("intern"); g.god(); g.drainPicks(true); g.pause(true);
      await new Promise(res => requestAnimationFrame(() => res()));
      const paused = g.devWiring();
      g.pause(false);

      // and the thing they are wired to has to do the thing
      g.wipeAll();
      const before = { chars: g.chars().filter(c => !g.saveState().unlocked[c]).length,
                       coins: g.saveState().coins, mon: g.monLvl("ox") };
      g.unlockAll();
      const after  = { locked: Object.keys(g.saveState().unlocked).length,
                       coins: g.saveState().coins, mon: g.monLvl("ox"),
                       up: Object.values(g.saveState().up).reduce((a,b)=>a+b,0) };
      const devOn = g.dev(true), wasOn = g.isDev();
      g.wipeAll();
      const afterWipe = { coins: g.saveState().coins, dev: g.isDev() };
      return { menu, paused, before, after, devOn, wasOn, afterWipe };
    });
    const all = { ...r.menu, ...r.paused };
    ok("every DEV control exists in the DOM",
       ["dvMode","dvAll","dvWipe"].every(k => r.menu[k].exists) &&
       ["dvLvl","dvEvo","dvSkip","dvGod"].every(k => r.paused[k].exists),
       Object.entries(all).filter(([,v]) => !v.exists).map(([k]) => k).join(",") || "all 7");
    ok("and every one of them is wired to a handler",
       Object.values(all).every(v => !v.exists || v.wired),
       Object.entries(all).filter(([,v]) => v.exists && !v.wired).map(([k]) => k).join(",") || "all wired");
    ok("UNLOCK EVERYTHING unlocks everything",
       r.after.locked >= 4 && r.after.coins >= 99999 && r.after.mon > 1 && r.after.up > 30,
       `${r.after.locked} unlocks, ${r.after.coins} coins, monster LV ${r.after.mon}, ${r.after.up} shop ranks`);
    ok("DEV MODE is a real switch", r.devOn === true && r.wasOn === true);
    ok("and WIPE SAVE actually wipes",
       r.afterWipe.coins === 0 && r.afterWipe.dev === false, JSON.stringify(r.afterWipe));

    // The pause DEV strip stays in the DOM (wiring is checked above) but must
    // only SHOW for someone who turned DEV MODE on - it carries GODMODE.
    const gate = await page.evaluate(() => {
      const g = window.__g;
      g.wipeAll(); g.start("intern"); g.god(); g.drainPicks(true);
      g.pause(true);
      const off = getComputedStyle(document.getElementById("dev")).display;
      g.pause(false); g.dev(true); g.pause(true);
      const on = getComputedStyle(document.getElementById("dev")).display;
      g.pause(false); g.wipeAll();
      return { off, on };
    });
    ok("the pause cheat strip hides until DEV MODE is on",
       gate.off === "none" && gate.on === "flex", JSON.stringify(gate));

    // WIPE SAVE is irreversible, so one click must not do it: the first click
    // arms the button, the second wipes. dev(true) fills the save so a wipe
    // is visible as coins going 99999 -> 0.
    const arm = await page.evaluate(() => {
      const g = window.__g;
      g.dev(true);
      const el = document.getElementById("dvWipe");
      el.click();
      const after1 = g.saveState().coins;
      el.click();
      const after2 = g.saveState().coins;
      g.wipeAll();
      return { after1, after2 };
    });
    ok("WIPE SAVE arms on the first click and wipes on the second",
       arm.after1 >= 99999 && arm.after2 === 0, JSON.stringify(arm));
  }

  console.log("\n=== 24a. THE SIM PAYS ITS WAY AT PEAK DENSITY ===");
  {
    // Measured under a full bot run: 174 live enemies three minutes into
    // sudden death cost ~2ms of sim on this runner (renderMs is SwiftShader
    // noise and transfers to nothing). The bound is 5x that measurement - not
    // a benchmark, a tripwire for an accidental O(n^2): a missing grid
    // rebuild, a per-enemy scan of enemies, a hazard loop gone quadratic.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeAll(); g.start("intern"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.place(0, 0);
      for (let i = 0; i < 200; i++)
        g.spawnAt("shambler", Math.cos(i) * 20 + (i % 7), Math.sin(i) * 20 + (i % 5));
      g.step(60, 1/60);                       // let the field settle
      return g.perf(60);
    });
    ok("200 enemies simulate inside the frame", r.simMs < 10 && r.enemies > 150,
       `${r.simMs}ms sim for ${r.enemies} enemies (ceiling ${r.simFpsCeiling}fps)`);
  }

  console.log("\n=== 24b. A LEVEL-UP DOES NOT COST YOU THE CHAIN ===");
  {
    // The chain punishes you for taking your hands off the keys, and a draft
    // screen takes your hands off the keys. That is the game punishing you for
    // playing it.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const key = c => { dispatchEvent(new KeyboardEvent("keydown", { code: c }));
                         dispatchEvent(new KeyboardEvent("keyup",   { code: c })); };
      const land = () => { let n = 0; while (g.hop().air && n++ < 400) g.step(1/60); };
      dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
      g.place(0, 0);
      for (let i = 0; i < 60; i++) g.step(1/60);
      key("Space"); g.step(1/60);
      for (let k = 0; k < 6; k++) { land(); key("Space"); g.step(1/60); g.place(0,0); }
      const built = g.hop().n;

      // pause is the same interruption with the same fix
      g.pause(true);
      const held = g.hop().n;
      g.pause(false);
      const afterPause = g.hop().n, winAfter = g.hop().win;

      // and the real one: land, take a draft, come back and carry on
      land();
      g.pause(true); g.pause(false);      // stand-in for the pick screen's freeze/thaw
      g.step(1/60);
      key("Space"); g.step(1/60);
      const resumed = g.hop().n;
      dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
      return { built, held, afterPause, winAfter, resumed };
    });
    ok("a chain survives the screen that interrupted it",
       r.afterPause === r.built && r.built >= 6, `${r.built} -> ${r.afterPause}`);
    ok("and you come back with a landing window open",
       r.winAfter > 0.1, `win=${r.winAfter}`);
    ok("so the next jump continues the chain instead of restarting it",
       r.resumed === r.built + 1, `${r.built} -> ${r.resumed}`);
  }

  console.log("\n=== 21c. EVOLVING IS WHERE ABILITIES COME FROM ===");
  {
    // The headline claim of the creature rework, and nothing in the suite
    // pressed it. The dev panel shipped calling functions that did not exist
    // for exactly this reason: 225 assertions, none of which touched the thing.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const out = {};
      for (const id of g.chars()) {
        g.wipeSave(); g.start(id); g.god();
        g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
        const mv = g.moveOf(id);
        const before = g.kitRaw();
        g.evolveTo(1);
        const at1 = g.kitRaw()[mv.key];
        g.evolveTo(2);
        const at2 = g.kitRaw()[mv.key];
        out[id] = { key: mv.key, nm: mv.nm, had: !!before[mv.key],
                    hadL: before[mv.key] ? before[mv.key].l : null,
                    at1, at2 };
      }
      // and if the draft already gave you that weapon, evolving RANKS it
      // rather than handing you a second copy
      g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.drainPicks(true);
      const mvk = g.moveOf("ox").key;
      g.give(mvk, 1);
      const pre = g.kitRaw()[mvk].l;
      g.evolveTo(1);
      const post = g.kitRaw()[mvk];
      const slots = Object.keys(g.kitRaw()).length;
      return { out, dupe: { pre, post, slots } };
    });
    const ids = Object.keys(r.out);
    ok("every line grants its move on the first evolution",
       ids.every(id => r.out[id].at1 && r.out[id].at1.mv === r.out[id].nm),
       ids.map(id => `${id}:${r.out[id].at1 ? r.out[id].at1.mv : "NONE"}`).join(" "));
    ok("and the second evolution sharpens it",
       ids.every(id => r.out[id].at2.l > r.out[id].at1.l),
       ids.map(id => `${id} ${r.out[id].at1.l}->${r.out[id].at2.l}`).join("  "));
    ok("no two lines learn the same move",
       new Set(ids.map(id => r.out[id].nm)).size === ids.length,
       `${new Set(ids.map(id => r.out[id].nm)).size} moves for ${ids.length} lines`);
    ok("a move you already own is ranked up, not duplicated",
       r.dupe.post.l > r.dupe.pre && r.dupe.post.mv,
       `rank ${r.dupe.pre} -> ${r.dupe.post.l}, ${r.dupe.slots} kit slots`);
  }

  console.log("\n=== 25. THE MENU SHOWS YOU THE ANIMAL ===");
  {
    // Seven hand-built body plans and the menu used to describe them in prose
    // next to a flat glyph. The cards render the real mesh through the real
    // engine now, so this section checks the three things that can silently
    // break: that the canvases exist, that something was actually painted into
    // them, and that seven different monsters produce seven different images -
    // one shared GL canvas blitted into seven cards is exactly the setup where
    // a stale readback would show you the same animal seven times.
    await page.reload({ waitUntil: "load" });
    await page.waitForTimeout(600);
    const r = await page.evaluate(async () => {
      const cards = [...document.querySelectorAll(".ch")];
      const open  = cards.filter(c => !c.classList.contains("lock"));
      // give the portrait pass a few frames to paint
      await new Promise(res => { let n = 0;
        const tick = () => (++n > 20 ? res() : requestAnimationFrame(tick));
        requestAnimationFrame(tick); });
      const shots = [];
      for (const c of cards.filter(c => c.querySelector("canvas.pv"))) {
        const cv = c.querySelector("canvas.pv");
        const d = cv.getContext("2d").getImageData(0, 0, cv.width, cv.height).data;
        let h = 2166136261, lit = 0;
        for (let i = 0; i < d.length; i += 4) {
          h = Math.imul(h ^ d[i], 16777619) ^ d[i+1] ^ d[i+2];
          if (d[i] + d[i+1] + d[i+2] > 120) lit++;
        }
        shots.push({ nm: c.querySelector(".nm").textContent.trim(),
                     hash: h >>> 0, lit, px: d.length / 4 });
      }
      return { cards: cards.length, open: open.length,
               pv: document.querySelectorAll(".ch canvas.pv").length,
               prose: open.filter(c => c.querySelector(".ds")).length,
               // the locked card's unlock condition moved out of a .ds prose
               // block and into the same labelled grid the open cards use
               lockProse: cards.filter(c => c.classList.contains("lock")
                            && /UNLOCK/.test(c.textContent)
                            && c.textContent.replace(/\s+/g," ").length > 20).length,
               locked: cards.length - open.length,
               shots };
    });
    ok("every unlocked card carries a live portrait",
       r.pv === r.open && r.pv > 0, `${r.pv} portraits / ${r.open} unlocked`);
    ok("and no unlocked card carries a description any more",
       r.prose === 0, `${r.prose} prose blocks on ${r.open} open cards`);
    ok("a locked card still says what unlocks it",
       r.locked === 0 || r.lockProse === r.locked,
       `${r.lockProse} of ${r.locked} locked cards explain themselves`);
    // "painted" means a real spread of lit pixels: a clear-only frame is all
    // background, and a blit of the wrong region is usually all background too.
    const painted = r.shots.filter(s => s.lit > s.px * 0.02 && s.lit < s.px * 0.92);
    ok("something is actually drawn into each one",
       painted.length === r.shots.length,
       r.shots.map(s => `${s.nm} ${(s.lit / s.px * 100).toFixed(0)}%`).join("  "));
    ok("and no two monsters produce the same picture",
       new Set(r.shots.map(s => s.hash)).size === r.shots.length,
       `${new Set(r.shots.map(s => s.hash)).size} distinct of ${r.shots.length}`);
    const after = await page.evaluate(() => {
      window.__g.start("plain");
      return { live: window.__g.portraits(), menu: window.__g.menuUp() };
    });
    ok("starting a run stops the portraits rendering",
       after.live === 0 && after.menu === false,
       `${after.live} live, menuUp ${after.menu}`);
  }

  console.log("\n=== 26. THE COURIER CHARGES BY MOVING ===");
  {
    // Seven characters are stat blocks; this one is a rule, and a rule that
    // only exists in the HUD is not a rule. Everything here presses on the
    // mechanic itself: does distance fill it, does standing still drain it,
    // does it fire, and is the payoff real at the damage funnel.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.unlockAll(); g.start("surge"); g.god();
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const isSurge = g.rule().isSurge;
      // baseline first, on an empty meter, so "cold" can never accidentally be
      // measured during a surge the walk below set off
      const cold = g.dmgOut(100);
      g.bot(true);
      g.step(120);                                  // walk for two seconds
      const moved = g.rule();
      g.bot(false);
      // stand still long enough for the drain to beat any residual sliding
      const before = moved.surge;
      g.step(300);
      const idled = g.rule();
      // fill it and walk until it trips
      g.fillSurge(); g.bot(true); g.step(45); g.bot(false);
      const fired = g.rule();
      const hot = g.dmgOut(100);
      return { isSurge, moved, before, idled, fired, hot, cold,
               plainCold: (g.wipeSave(), g.start("intern"), g.god(), g.dmgOut(100)) };
    });
    ok("the line knows it has a rule", r.isSurge === true, `isSurge ${r.isSurge}`);
    ok("covering ground fills the meter",
       r.moved.surge > .10 && r.moved.dist > 8,
       `${(r.moved.surge*100).toFixed(0)}% after ${r.moved.dist.toFixed(0)}m`);
    ok("and standing still bleeds it back out",
       r.idled.surge < r.before - .05,
       `${(r.before*100).toFixed(0)}% -> ${(r.idled.surge*100).toFixed(0)}% after five seconds still`);
    ok("a full meter spends itself all at once",
       r.fired.surgeT > 3 && r.fired.surge < .2,
       `surge ${r.fired.surgeT.toFixed(2)}s, meter back to ${(r.fired.surge*100).toFixed(0)}%`);
    ok("and while it is up the damage funnel pays out",
       r.hot / r.cold > 1.7 && r.hot / r.cold < 2.0,
       `${r.cold.toFixed(1)} -> ${r.hot.toFixed(1)} = x${(r.hot/r.cold).toFixed(2)}`);
    ok("nobody else gets it", Math.abs(r.plainCold - 100) < 40 && r.cold > 0,
       `THE INTERN ${r.plainCold.toFixed(1)} for a base of 100`);
  }

  console.log("\n=== 26b. THE TEMP SPENDS DEATHS ===");
  {
    // The only character in the game that can lose a fight and keep the run.
    // What has to hold: the first lethal hit does not end it, the second one
    // inside the cooldown does, and the cooldown grows so it cannot carry a
    // whole run on its own.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.unlockAll(); g.start("pyre");
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const isPyre = g.rule().isPyre;
      const maxhp = g.state().maxhp;
      g.hitMe(1e6);                                  // certain death
      const after = { st: g.state(), rule: g.rule() };
      const cd1 = after.rule.rebirthCd;
      // unlockAll hands out SECOND WIND too, so the ORDER is the thing worth
      // checking: the character's own rule first, the shop's revive second,
      // and only then the run ends.
      g.hitMe(1e6);
      const wind = g.state();
      g.hitMe(1e6);
      const dead = g.state();
      // a fresh one, run past the cooldown, and spend it a second time
      g.wipeSave(); g.unlockAll(); g.start("pyre");
      g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      g.hitMe(1e6);
      const one = g.rule();
      g.step(60 * Math.ceil(one.rebirthCd) + 120);
      const cooled = g.rule();
      g.hitMe(1e6);
      const two = g.rule();
      return { isPyre, maxhp, after, cd1, wind, dead, one, cooled, two };
    });
    ok("the line knows it has a rule", r.isPyre === true, `isPyre ${r.isPyre}`);
    ok("a lethal hit does not end the run the first time",
       r.after.st.over === false && r.after.st.hp > 0,
       `over ${r.after.st.over}, ${r.after.st.hp} HP left`);
    ok("it comes back at 45%",
       Math.abs(r.after.st.hp / r.maxhp - 0.45) < 0.03,
       `${r.after.st.hp} of ${r.maxhp} = ${(r.after.st.hp/r.maxhp*100).toFixed(0)}%`);
    ok("and the rebirth goes on a cooldown", r.cd1 > 30, `${r.cd1}s`);
    ok("the character's rule fires before the shop's revive",
       r.wind.over === false && r.dead.over === true,
       `rebirth, then SECOND WIND (over ${r.wind.over}), then dead (over ${r.dead.over})`);
    ok("the cooldown runs down", r.cooled.rebirthCd === 0,
       `${r.cooled.rebirthCd}s left after waiting it out`);
    ok("and the second rebirth costs more than the first",
       r.two.rebirths === 2 && r.two.rebirthCd > r.one.rebirthCd,
       `${r.one.rebirthCd}s then ${r.two.rebirthCd}s`);
  }

  console.log("\n=== 27. LEVELLING UP DOES NOT STOP THE GAME ===");
  {
    // The draft used to be a full-screen modal: pointer released, camera
    // parked, simulation halted. A long run levels forty times, so the back
    // half of every run was a slideshow - and the thing the game is about,
    // positioning, was switched off for all of it.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.unlockAll(); g.start("intern"); g.god();
      g.freezeEvents(true);
      g.xp(500);                                  // a fistful of levels
      g.step(1);                                  // one tick queues and shows
      const open = document.getElementById("pick").classList.contains("on");
      const t0 = g.state().t, n0 = g.state().enemies;
      // the world keeps turning while the cards are on screen
      for (let i = 0; i < 120; i++) g.stepRaw(1/60);
      const t1 = g.state().t;
      const stillOpen = document.getElementById("pick").classList.contains("on");
      // and an ignored draft eventually resolves itself rather than sitting
      // there for the rest of the run
      for (let i = 0; i < 60 * 14; i++) g.stepRaw(1/60);
      const resolved = !document.getElementById("pick").classList.contains("on")
                    || g.state().pending < 500;
      return { open, t0, t1, n0, stillOpen, resolved,
               modal: getComputedStyle(document.getElementById("pick")).backdropFilter };
    });
    ok("the draft opens on a level", r.open === true, `open ${r.open}`);
    ok("and the clock keeps running underneath it",
       r.t1 - r.t0 > 1.5, `${r.t0}s -> ${r.t1}s with cards on screen`);
    ok("it is not a modal any more",
       r.modal === "none" || r.modal === "" , `backdrop-filter: ${r.modal}`);
    ok("an ignored draft resolves itself", r.resolved === true, `${r.resolved}`);
  }

  console.log("\n=== 27b. A LEVEL WITH NOTHING TO CHOOSE IS STILL WORTH SOMETHING ===");
  {
    // Past about level fifty everything is maxed and the draft has one card on
    // it that says ROAST CHICKEN. That level used to be forty hit points and a
    // modal to accept them. It is permanent growth now.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.unlockAll(); g.start("intern");
      g.freezeSpawns(true); g.freezeEvents(true);
      for (const w of ["bat","skulls","bolt","pulse"]) g.give(w, 4);
      for (const p of ["spinach","boots","tempo","magnet","plating"]) g.give(p, 4);
      for (const k of Object.keys(g.kitRaw())) g.evolve(k);
      const before = { hp: g.state().maxhp, dmg: g.state().dps };
      g.xp(40000);                                 // a great many empty levels
      for (let i = 0; i < 240; i++) g.stepRaw(1/60);
      const after = { hp: g.state().maxhp, dmg: g.state().dps, lvl: g.state().lvl };
      // and it has to SURVIVE the next recalc, which is what killed the boons
      g.give("spinach", 1);
      const kept = { hp: g.state().maxhp, dmg: g.state().dps };
      return { before, after, kept };
    });
    ok("empty levels raise max HP", r.after.hp > r.before.hp * 1.05,
       `${r.before.hp} -> ${r.after.hp} by LV ${r.after.lvl}`);
    ok("and they raise damage", r.after.dmg > r.before.dmg * 1.05,
       `${r.before.dmg} -> ${r.after.dmg}`);
    ok("and the growth survives the next recalc",
       r.kept.dmg >= r.after.dmg * 0.999,
       `${r.after.dmg} -> ${r.kept.dmg} after another passive`);
  }

  console.log("\n=== 28. THE GROUND HOLDS THE HORDE TOO ===");
  {
    // Every biome had a rule for the player and none for anything chasing
    // them - THE TARPITS' "-14% move speed" was a player-only tax on terrain
    // the game itself describes as gripping "your" feet, no different from
    // the mud gripping anything else standing in it. Same fix as the lake:
    // the ground is terrain, not a player-exclusive cost.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      // BOTH streams pinned. The world stream alone left the six shamblers'
      // individual speed multipliers - drawn from the RUN stream, reseeded
      // fresh from Math.random() every start() that does not pin it - free
      // to vary from one execution of this file to the next, and averaging
      // six of a +/-12% draw does not kill enough of that noise to clear a
      // tight margin reliably. Pinned, the six draws are the same every time.
      g.pin(31337); g.pinRun(31337);
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.step(10, 1/60);
      // find a bog cell near the middle of the map by scanning a spiral -
      // the same technique the water test uses via g.lakes(), but biomes
      // aren't listed anywhere so this walks the ground itself
      let bogAt = null;
      const STEPS = 24;
      for(let ring=10; ring<200 && !bogAt; ring+=6)
        for(let a=0; a<STEPS && !bogAt; a++){
          const ang = a/STEPS*Math.PI*2;
          const x = Math.cos(ang)*ring, z = Math.sin(ang)*ring;
          if(g.biomeAt(x,z).id === "bog") bogAt = {x,z};
        }
      const walk = (x, z) => { g.clearEnemies(); g.place(x, z + 30);
        for(let k2=0;k2<6;k2++) g.spawnAt("shambler", x + (k2%3-1)*1.2, z + (k2/3|0)*1.2);
        g.step(1, 1/60);
        const p0 = g.enemiesPos(); g.step(90, 1/60);
        const p1 = g.enemiesPos();
        let d2 = 0;
        for(let k2=0;k2<p0.length;k2++)
          d2 += Math.hypot(p1[k2].x - p0[k2].x, p1[k2].z - p0[k2].z);
        return d2 / p0.length; };
      const dry = walk(0, 0);
      const wet = bogAt ? walk(bogAt.x, bogAt.z) : null;
      g.pin(null); g.pinRun(null);
      return { dry, wet, found: !!bogAt, bogAt };
    });
    ok("a bog cell exists to test against", r.found, "world rolled with no THE TARPITS in range");
    if(r.found)
      ok("and the horde bogs down too - the ground is terrain, not a player tax",
         r.wet < r.dry * .92,
         `a shambler covered ${r.wet.toFixed(1)}m through THE TARPITS vs ${r.dry.toFixed(1)}m on THE FERNLANDS`);

    // and SURE FOOT buys the player back out of the same mud
    const sf = r.found ? await page.evaluate(async (bogAt) => {
      const g = window.__g;
      g.pin(31337);
      const run = (boon) => {
        g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.step(10, 1/60);
        if(boon) g.giveBoon("SURE FOOT");
        g.place(bogAt.x, bogAt.z); g.aim(0);
        dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
        const x0 = g.state().x, z0 = g.state().z;
        g.step(60, 1/60);
        dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
        const s2 = g.state();
        return Math.hypot(s2.x - x0, s2.z - z0);
      };
      const plain = run(false), sure = run(true);
      g.pin(null);
      return { plain, sure };
    }, r.bogAt) : null;
    // THE TARPITS' own penalty is .86, so the theoretical ceiling on this
    // ratio is 1/.86 = 1.163; a second of acceleration ramp eats some of
    // that before top speed is reached, so 1.08 is comfortably above noise
    // and comfortably below "no effect" without demanding the ideal number.
    if(sf)
      ok("and SURE FOOT buys the player back out of the same mud",
         sf.sure > sf.plain * 1.08,
         `${sf.plain.toFixed(1)}m plain vs ${sf.sure.toFixed(1)}m with SURE FOOT`);

    // AQUA lines still walk on dry mud like everyone else - the first cut of
    // SURE FOOT gated all three terrain effects behind one "not aquatic" flag
    // and silently zeroed the boon for a swimmer standing on the bank rather
    // than in the lake. Same bog cell, the "scrap" line (a swimmer) instead.
    const sfAqua = r.found ? await page.evaluate(async (bogAt) => {
      const g = window.__g;
      g.pin(31337);
      const run = (boon) => {
        g.wipeSave(); g.start("scrap"); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.step(10, 1/60);
        if(boon) g.giveBoon("SURE FOOT");
        g.place(bogAt.x, bogAt.z); g.aim(0);
        dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
        const x0 = g.state().x, z0 = g.state().z;
        g.step(60, 1/60);
        dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
        const s2 = g.state();
        return Math.hypot(s2.x - x0, s2.z - z0);
      };
      const plain = run(false), sure = run(true);
      g.pin(null);
      return { plain, sure };
    }, r.bogAt) : null;
    // "scrap" runs 10% faster than "ox" to start with, so the same one-second
    // window spends proportionally more of it still accelerating toward a
    // higher top speed - the ratio this masks is real, not a smaller effect,
    // so the bar is 1.05 rather than 1.08: still well clear of "no effect".
    if(sfAqua)
      ok("and it still helps a swimmer standing on dry mud",
         sfAqua.sure > sfAqua.plain * 1.05,
         `${sfAqua.plain.toFixed(1)}m plain vs ${sfAqua.sure.toFixed(1)}m with SURE FOOT, on "scrap"`);
  }

  console.log("\n=== 29. THE HORDE IS ONE OBJECT EACH, TOO ===");
  {
    // analyze.js has asked "is this animal ONE object?" of the 36 player forms
    // since the first model round and never once of the horde - and the first
    // time it was pointed at the enemy roster it found five of ten bodies in
    // pieces, including two red squares that had been hanging in the air beside
    // every PTERLING on screen since the pterosaur rebuild. A report nobody is
    // obliged to run is not a guard, so the same question is asked here.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      // capture layout is (r, f, y, hx, hz, hy) - same six numbers the player
      // capture uses, so this is the same union-find analyze.js runs
      const comps = (bx) => {
        const n = bx.length / 6, P = i => bx.slice(i*6, i*6+6);
        const ov = (A,B,k) => Math.min(A[k]+A[k+3], B[k]+B[k+3])
                            - Math.max(A[k]-A[k+3], B[k]-B[k+3]);
        const par = Array.from({length:n}, (_,i)=>i);
        const find = a => { while(par[a]!==a){ par[a]=par[par[a]]; a=par[a]; } return a; };
        for(let i=0;i<n;i++) for(let j=i+1;j<n;j++){
          const A=P(i), B=P(j);
          if(Math.min(ov(A,B,0), ov(A,B,1), ov(A,B,2)) > 0){
            const a=find(i), b=find(j); if(a!==b) par[b]=a;
          }
        }
        return new Set(Array.from({length:n}, (_,i)=>find(i))).size;
      };
      // DISARMED. The note below already knew the player's own weapon could
      // kill the subject before it was captured, and mitigated it by stepping
      // only three frames after the spawn - which held until PULSE, the weapon
      // THE OX starts with, was widened to a 10.4m radius and began firing
      // inside that window. A 14 HP runner then reported "0 boxes" and this
      // section failed for a reason that had nothing to do with body plans.
      // The subject here is the horde, so the player carries nothing.
      g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true);
      g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.disarm();
      g.place(0,0); g.aim(0); g.step(20, 1/60);
      const out = [];
      // SIX PHASES, not one. Brood sway, tail lag and wing flap all move parts
      // relative to each other, so whether a body holds together is a question
      // about the whole animation, not about whichever frame the check happened
      // to land on - and a deliberately broken wing proved it, failing THE
      // MATRIARCH on one sampling run and passing her on the next. The slowest
      // sway in the roster cycles about every 240 frames, so six samples 40
      // frames apart walk right around it, and the worst one is the answer.
      // The clock is advanced with the field EMPTY and the body respawned
      // fresh for each sample: run the enemy for 240 frames instead and it
      // walks out of full detail, or the player's own weapon kills it, and
      // the check starts reporting zero boxes it never looked at.
      const worst = async (spawn) => {
        let parts = 0, n = 0;
        for(let ph=0; ph<6; ph++){
          g.clearEnemies();
          g.step(40, 1/60);
          spawn();
          g.step(3, 1/60);
          // and the STRIDE is walked round too, now that the legs bend with
          // it: a knee that only comes off the hip at full swing is a break
          // the standing frame never shows. .53 apart over six samples steps
          // through more than a full cycle of every leg frequency in use.
          g.setGait(ph*.53, 1);
          g.resume(); g.captureEnemy();
          await frame(); await frame();
          const bx = g.enemyPos();
          if(!bx) return { n:0, parts:-1 };
          n = bx.length/6;
          parts = Math.max(parts, comps(bx));
        }
        return { n, parts };
      };
      // close enough to draw at full detail: a body plan that only comes apart
      // at LOD 2 is still a body plan that comes apart
      for(const k of ["shambler","runner","brute","spitter","skitter","collector"])
        out.push(Object.assign({ nm:k }, await worst(()=>{
          g.place(0,0); g.spawnAt(k, 0, 7); })));
      for(let bi=0; bi<4; bi++){
        let nm = "boss"+bi;
        const r2 = await worst(()=>{
          g.boss(bi); g.step(1/60);
          const b = g.bossAt();
          if(b){ nm = b.nm; g.place(b.x - 9, b.z); g.step(120, 1/60); }
        });
        out.push(Object.assign({ nm }, r2));
      }
      return out;
    });
    const broke = r.filter(x => x.parts !== 1);
    ok("every trash body and every boss is a single connected object",
       r.length === 10 && broke.length === 0,
       broke.length ? broke.map(x => `${x.nm}: ${x.parts} parts of ${x.n} boxes`).join(", ")
                    : `${r.length} bodies, all in one piece`);
    ok("and each one actually drew something to check",
       r.every(x => x.n > 10), r.map(x => `${x.nm} ${x.n}`).join(" "));
  }

  console.log("\n=== 30. THE BROOD IS A BODY, NOT A BULLET ===");
  {
    // Nine weapons and not one of them put another body on the field. A summon
    // is a different KIND of thing to test: it is not "did the shot land", it
    // is "is there something out there, does it fight, and can it be walked off
    // the edge of the world while its owner is somewhere else".
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const boot = (rank, evo) => {
        g.wipeSave(); g.start("intern"); g.god();
        g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
        g.give("brood", rank);
        if(evo){ g.give("dupe", 2); g.evolve("brood"); }
        g.place(0,0); g.aim(0); g.step(30, 1/60);
      };
      const out = {};
      // 1. it exists, and how many of it there are follows the rank
      boot(0, false); out.n0 = g.pets().length;
      boot(4, false); out.n4 = g.pets().length;
      boot(4, true);  out.nEvo = g.pets().length;
      // 2. it fights on its own - the player never moves and never fires at it
      boot(4, false);
      g.clearEnemies();
      for(let i=0;i<12;i++) g.spawnAt("shambler", -6 + (i%4)*3, 9 + (i/4|0)*2);
      const k0 = g.state().kills;
      g.step(60*8, 1/60);
      out.killed = g.state().kills - k0;
      // 3. it cannot be baited off the map: park a lone target far away and
      //    check the brood stays inside its leash of the PLAYER
      boot(4, false);
      g.clearEnemies(); g.place(0,0);
      g.spawnAt("shambler", 0, 120);
      let far = 0;
      for(let i=0;i<60*10;i++){ g.step(1/60);
        for(const p of g.pets()) far = Math.max(far, p.d); }
      out.far = +far.toFixed(1);
      // 4. and it never costs the owner health
      boot(4, false);
      g.clearEnemies();
      for(let i=0;i<8;i++) g.spawnAt("shambler", -4 + i, 4);
      g.ungod && g.ungod();
      const hp0 = g.state().hp;
      g.freezeSpawns(true);
      g.clearEnemies();                       // only the brood is left near you
      g.step(60*6, 1/60);
      out.hpDrop = +(hp0 - g.state().hp).toFixed(1);
      // 5. and six of them are six animals. A render caught the pack standing
      //    inside itself - two of six visibly interpenetrating - and no check
      //    here noticed, because every one of them counted pets rather than
      //    looking at where they were. Measured over a real fight: the closest
      //    pair of the pack, every frame.
      boot(4, true);
      g.clearEnemies();
      for(let i=0;i<14;i++) g.spawnAt("shambler", -8 + (i%5)*4, 10 + (i/5|0)*3);
      let worst = 1e9, overlap = 0, frames = 0;
      for(let i=0;i<60*10;i++){
        g.step(1/60);
        const ps = g.pets();
        if(!ps || ps.length < 2) continue;
        let mn = 1e9;
        for(let a=0;a<ps.length;a++) for(let b2=a+1;b2<ps.length;b2++)
          mn = Math.min(mn, Math.hypot(ps[a].x-ps[b2].x, ps[a].z-ps[b2].z));
        frames++; worst = Math.min(worst, mn);
        if(mn < 0.9) overlap++;
      }
      out.closest = +worst.toFixed(2);
      out.overlapPct = Math.round(100*overlap/Math.max(1,frames));
      // 6. and none of them stands INSIDE what it is biting. Nothing stops a
      //    pet walking through an enemy body, and a ring slot on the far side
      //    of a boss means crossing straight through the middle of one. Caught
      //    with the owner at melee range, which is where it happens.
      boot(4, true);
      g.clearEnemies(); g.boss(0); g.step(1/60);
      const b0 = g.bossAt();
      out.bossRad = b0 ? b0.rad : 0;
      let inside = 1e9;
      for(let i=0;i<60*8;i++){
        const bb = g.bossAt(); if(!bb) break;
        g.place(bb.x - 7, bb.z);              // three metres outside its hitbox
        g.step(1/60);
        for(const q of (g.pets()||[]))
          inside = Math.min(inside, Math.hypot(q.x-bb.x, q.z-bb.z));
      }
      out.nearestToBoss = inside === 1e9 ? -1 : +inside.toFixed(2);
      return out;
    });
    ok("a brood actually puts something on the field",
       r.n0 === 1, `${r.n0} hatchling at rank 1`);
    ok("and the pack grows with the rank",
       r.n4 > r.n0 && r.nEvo > r.n4,
       `rank1 ${r.n0} -> rank5 ${r.n4} -> evolved ${r.nEvo}`);
    ok("it hunts on its own, with the owner standing still",
       r.killed > 0, `${r.killed} killed while the player never moved`);
    // the leash is the whole reason this is playable: a follower that chases
    // one distant straggler is a follower you do not have when the crowd lands
    ok("and it cannot be baited off the map",
       r.far < 40, `furthest a hatchling strayed from its owner: ${r.far}m`);
    ok("and standing next to your own brood is free",
       r.hpDrop <= 0, `owner lost ${r.hpDrop} HP alone with it`);
    // A pack that renders as one animal is not a pack. Before the pets took a
    // side of the target each, the closest pair of a four-strong brood averaged
    // 0.011m apart and spent 100% of frames inside a body radius.
    ok("and a pack of six is six animals, not one",
       r.overlapPct <= 2 && r.closest > 0.6,
       `closest any two came: ${r.closest}m, and ${r.overlapPct}% of frames ` +
       `had a pair inside a body radius`);
    // A hatchling drawn inside the boss is a hatchling you cannot see fighting.
    ok("and none of them stands inside what it is biting",
       r.nearestToBoss > r.bossRad,
       `closest a pet came to a ${r.bossRad}m boss centre: ${r.nearestToBoss}m`);
  }

  console.log("\n=== 31. THE HORDE WALKS, IT DOES NOT JOG ON THE SPOT ===");
  {
    // Every enemy animated off the wall clock: the same stride at the same
    // tempo whether it was sprinting, slowed, sliding off a bat or standing in
    // a spitter's firing band going nowhere, and every one of them snapped to
    // face the player each frame, so a shoved brute slid backwards staring at
    // you. The gait rides distance covered now, the way the player's does, and
    // the heading is the animal's own. These read the locomotion state walk()
    // keeps, through the same hook the draw reads it from.
    const r = await page.evaluate(() => {
      const g = window.__g;
      const boot = () => {
        g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.disarm();
        g.place(0,0); g.aim(0); g.step(20, 1/60); g.clearEnemies();
      };
      const out = {};
      // 1. A spitter holding its band stands. Spawned exactly on the band it
      //    wants (13m), it never moves, so its gait time must not advance and
      //    its stride amplitude must settle to nothing - and a shambler walking
      //    in from thirty metres covers ground, so its gait runs.
      boot();
      g.spawnAt("spitter", 0, 13); g.spawnAt("shambler", 0, 30);
      g.step(30, 1/60);
      const a0 = g.gait();
      g.step(60, 1/60);
      const a1 = g.gait();
      out.stand = { dgt: +(a1[0].gt - a0[0].gt).toFixed(4), amp: a1[0].amp,
                    moved: +Math.hypot(a1[0].x - a0[0].x, a1[0].z - a0[0].z).toFixed(3) };
      out.walkr = { dgt: +(a1[1].gt - a0[1].gt).toFixed(4), amp: a1[1].amp,
                    moved: +Math.hypot(a1[1].x - a0[1].x, a1[1].z - a0[1].z).toFixed(3) };
      // 2. Gait time is in seconds of the SPECIES' own running, so a skitter
      //    at 5.0 and a shambler at 2.5 both bank about one second of gait per
      //    second at full stride - the plans' tuned frequencies keep their look.
      boot();
      g.spawnAt("skitter", 0, 40); g.spawnAt("shambler", 0, 30);
      g.step(30, 1/60);
      const b0 = g.gait(); g.step(60, 1/60); const b1 = g.gait();
      out.norm = { skitter: +(b1[0].gt - b0[0].gt).toFixed(3),
                   shambler: +(b1[1].gt - b0[1].gt).toFixed(3) };
      // 3. and a slowed animal strides slowly: the same shambler under the 45%
      //    slow banks 45% of the gait, not the same stride at the same tempo.
      g.slowAll(10);
      g.step(30, 1/60);
      const c0 = g.gait(); g.step(60, 1/60); const c1 = g.gait();
      out.slow = { ratio: +((c1[1].gt - c0[1].gt) / out.norm.shambler).toFixed(3),
                   amp: c1[1].amp };
      // 4. The heading is where the animal is GOING. A spitter spawned inside
      //    its band backs out of it, and while it backs away it faces AWAY from
      //    you; a shambler walking in faces you. Both are a finite turn, so a
      //    freshly spawned body is read after it has had time to come round.
      boot();
      g.spawnAt("spitter", 0, 6); g.spawnAt("shambler", 0, 30);
      g.step(45, 1/60);
      const d1 = g.gait();
      const away = Math.atan2(0 - d1[0].x, 0 - d1[0].z);      // toward the player
      const wrap = a => { while(a > Math.PI) a -= 2*Math.PI; while(a < -Math.PI) a += 2*Math.PI; return a; };
      out.head = { spitterOff: +Math.abs(wrap(d1[0].hd - away)).toFixed(3),
                   shamblerOff: +Math.abs(wrap(d1[1].hd - Math.atan2(0 - d1[1].x, 0 - d1[1].z))).toFixed(3) };
      // 5. and it comes round at a rate, not in a frame. A chaser that has
      //    settled facing you is asked to turn a right angle - the player
      //    jumps a quarter-circle round it - and the heading swings over
      //    several frames rather than arriving in one.
      boot();
      g.spawnAt("shambler", 0, 30); g.step(45, 1/60);
      const e0 = g.gait()[0].hd;
      g.place(30, 30); g.step(1, 1/60);
      const e1 = g.gait()[0].hd;
      g.step(20, 1/60);
      const e2 = g.gait()[0].hd;
      out.turn = { oneFrame: +Math.abs(wrap(e1 - e0)).toFixed(3),
                   later: +Math.abs(wrap(e2 - e0)).toFixed(3) };
      // 5b. A shove is not a walk. Knocked ten metres sideways, the animal
      //     slides - it does not stride ten metres' worth of gait in half a
      //     second, and it keeps facing the way it is walking, not the way it
      //     is flying.
      boot();
      g.spawnAt("shambler", 0, 30); g.step(45, 1/60);
      const s0 = g.gait()[0];
      g.hurtAt(0, 1, 40, 0); g.step(30, 1/60);
      const s1 = g.gait()[0];
      out.shove = { slid: +Math.abs(s1.x - s0.x).toFixed(2), dgt: +(s1.gt - s0.gt).toFixed(3),
                    turned: +Math.abs(wrap(s1.hd - s0.hd)).toFixed(3) };
      // 6. The flinch. A hit that takes a third of the animal squashes it and
      //    the squash recovers in a few frames; a chip barely dips it.
      boot();
      g.spawnAt("brute", 0, 30); g.spawnAt("brute", 4, 30); g.step(30, 1/60);
      g.hurtAt(0, 60); g.hurtAt(1, 1);
      const f0 = g.gait();
      g.step(45, 1/60);
      const f1 = g.gait();
      out.flinch = { big: f0[0].sq, chip: f0[1].sq, after: f1[0].sq };
      // 7. The bite. Contact with the player pitches the animal forward -
      //    lg goes to 1 on the touch and decays over the next third of a second.
      boot();
      g.spawnAt("shambler", 0, 1.2);
      let peak = 0, low = 1;
      for(let i=0;i<60;i++){ g.step(1, 1/60); const v = g.gait()[0].lg; peak = Math.max(peak, v); }
      g.hitMe(0); // reset iframe so the next touch lands; then let it decay
      for(let i=0;i<40;i++){ g.step(1, 1/60); low = Math.min(low, g.gait()[0].lg); }
      out.bite = { peak: +peak.toFixed(3), low: +low.toFixed(3) };
      // 8. and none of it produces a number that is not a number: a full
      //    minute of a real mixed wave leaves every field finite.
      boot(); g.freezeSpawns(false); g.skipTo(300); g.step(60*20, 1/60);
      const all = g.gait();
      out.finite = { n: all.length,
                     bad: all.filter(e => [e.gt,e.amp,e.hd,e.bk,e.lg,e.sq].some(v => v === null || !isFinite(v))).length };
      return out;
    });
    ok("a spitter holding its band stands, its gait frozen and its stride settled",
       r.stand.moved < .05 && r.stand.dgt < .01 && r.stand.amp < .05,
       `moved ${r.stand.moved}m in a second, gait +${r.stand.dgt}, amp ${r.stand.amp}`);
    ok("and a shambler walking in runs its gait at full stride",
       r.walkr.moved > 1.5 && r.walkr.dgt > .7 && r.walkr.amp > .8,
       `moved ${r.walkr.moved}m, gait +${r.walkr.dgt}, amp ${r.walkr.amp}`);
    ok("gait time is in seconds of the species' own running",
       Math.abs(r.norm.skitter - 1) < .16 && Math.abs(r.norm.shambler - 1) < .16,
       `per second at full stride: skitter +${r.norm.skitter}, shambler +${r.norm.shambler}`);
    ok("and a slowed animal strides slowly",
       r.slow.ratio > .35 && r.slow.ratio < .55 && r.slow.amp < .6,
       `slowed gait runs at ${r.slow.ratio} of the free rate, amp ${r.slow.amp}`);
    ok("the heading is where the animal is going, not where you are",
       r.head.spitterOff > 2.6 && r.head.shamblerOff < .3,
       `a backing spitter faces ${r.head.spitterOff} rad off you, a chaser ${r.head.shamblerOff}`);
    ok("and it comes round at a rate, not in a frame",
       r.turn.oneFrame < .5 && r.turn.later > r.turn.oneFrame + .3,
       `a right-angle turn: ${r.turn.oneFrame} rad in one frame, ${r.turn.later} after twenty`);
    ok("a shove is a slide, not a stride",
       r.shove.slid > 3 && r.shove.dgt < .6 && r.shove.turned < .6,
       `knocked ${r.shove.slid}m sideways in half a second: gait +${r.shove.dgt}, turned ${r.shove.turned} rad`);
    ok("a hit squashes the animal in proportion, and it recovers",
       r.flinch.big < .75 && r.flinch.chip > r.flinch.big + .1 && r.flinch.after > .97,
       `a big hit squashed to ${r.flinch.big}, a chip to ${r.flinch.chip}, back to ${r.flinch.after}`);
    ok("and contact is a bite that goes out and comes back",
       r.bite.peak > .9 && r.bite.low < .1,
       `bite peaked at ${r.bite.peak} and fell to ${r.bite.low}`);
    ok("and a minute of a real wave leaves every gait field finite",
       r.finite.n > 20 && r.finite.bad === 0,
       `${r.finite.n} bodies, ${r.finite.bad} with a bad field`);
  }

  console.log("\n=== 32. THE HORDE HAS KNEES ===");
  {
    // Every walking body on the roster had legs that were one box each, slid
    // fore and aft as a unit, and on two of the five species did not exist at
    // all in the middle detail tier - which is the tier a spitter holding its
    // thirteen-metre band and a collector running from you are actually seen
    // at. The legs are jointed now (thigh, shin, foot), the swinging foot
    // lifts, and every walker has them at LOD 1. These read the captured box
    // list the way section 29 does - face-local (r, f, y, hx, hz, hy).
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const boot = () => {
        g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.disarm();
        g.place(0,0); g.aim(0); g.step(20, 1/60); g.clearEnemies();
      };
      // Capture the body on the field at a stride phase. The sim is PAUSED for
      // the capture - the draw loop keeps drawing a frozen field, the way the
      // film harnesses rely on - so the phase set here is the phase drawn, and
      // the same animal is re-shot phase after phase: each spawn rolls its own
      // stride offset, so respawning per phase would sample random phases.
      const recap = async (gt, amp) => {
        g.setGait(gt, amp); g.pause(true); g.captureEnemy();
        await frame(); await frame();
        const bx = g.enemyPos(); if(!bx) return null;
        const out = [];
        for(let i=0;i<bx.length;i+=6)
          out.push({ r:bx[i], f:bx[i+1], y:bx[i+2], hx:bx[i+3], hz:bx[i+4], hy:bx[i+5] });
        return out;
      };
      const shoot = async (k, dist, gt, amp) => {
        g.clearEnemies(); g.step(2, 1/60);
        g.place(0,0); g.spawnAt(k, 0, dist); g.step(2, 1/60);
        return recap(gt, amp);
      };
      const W = { shambler:.55, brute:1.5, spitter:.62, skitter:.34, collector:.82 };
      // a LEG box: narrow in plan (a body slab is not), off the centre line
      // (a tail is not), and in the lower half of the animal (an arm is not)
      const legs = (bx, k) => {
        const top = Math.max(...bx.map(b => b.y + b.hy)), bot = Math.min(...bx.map(b => b.y - b.hy));
        const mid = (top + bot) / 2, w = W[k];
        return bx.filter(b => b.hx < w*.2 && b.hz < w*.24 && Math.abs(b.r) > w*.08 && b.y < mid);
      };
      // FEET: the lowest leg box on each side
      const feet = (lg) => {
        const side = s => lg.filter(b => Math.sign(b.r) === s).sort((a,b) => (a.y-a.hy) - (b.y-b.hy))[0];
        return [side(-1), side(1)];
      };
      boot();
      const out = { tier:{}, joint:{} };
      // 1. legs in BOTH tiers, standing (amp 0 - nothing lifted), touching the
      //    ground: at least two leg boxes a side stacked at LOD 1, three at
      //    LOD 2 for the bipeds; the quadrupeds four and four
      for(const k of ["shambler","brute","spitter","skitter","collector"]){
        const near = await shoot(k, 7, 0, 0), gy = (g.gait()[0] || {}).y;
        const far = await shoot(k, 18.5, 0, 0), gyf = (g.gait()[0] || {}).y;
        if(!near || !far){ out.tier[k] = null; continue; }
        const ln = legs(near, k), lf = legs(far, k);
        const perSide = (lg) => [-1, 1].map(s => lg.filter(b => Math.sign(b.r) === s).length);
        const low = (bx) => Math.min(...bx.map(b => b.y - b.hy));
        out.tier[k] = { near: perSide(ln), far: perSide(lf), nearN: near.length, farN: far.length,
                        // and the middle tier stands on the same ground the near tier
                        // does - each measured against its own patch of terrain
                        drop: +((low(far) - gyf) - (low(near) - gy)).toFixed(3),
                        ground: +(low(near) - gy).toFixed(3) };
      }
      // 2. the stride: the same animal walked round more than a full cycle at
      //    full amplitude, twelve phases .075 apart. The two feet come apart
      //    fore-and-aft and go back together, the swinging one comes up off
      //    the planted one, and the planted one is the lowest thing on the
      //    animal at every phase - the body stands on it.
      for(const k of ["spitter","skitter","collector"]){
        let spread = [], lift = [], planted = [];
        for(let ph=0; ph<12; ph++){
          const bx = ph ? await recap(ph*.075, 1) : await shoot(k, 7, 0, 1);
          if(!bx){ spread = null; break; }
          const [a, b] = feet(legs(bx, k));
          if(!a || !b){ spread = null; break; }
          const ba = a.y - a.hy, bb = b.y - b.hy;
          spread.push(Math.abs(a.f - b.f));
          lift.push(Math.abs(ba - bb));
          planted.push(Math.min(ba, bb) - Math.min(...bx.map(x => x.y - x.hy)));
        }
        out.joint[k] = spread ? { apart: +Math.max(...spread).toFixed(3), together: +Math.min(...spread).toFixed(3),
                                  lift: +Math.max(...lift).toFixed(3), planted: +Math.max(...planted).toFixed(3) }
                              : null;
      }
      g.resume();
      return out;
    });
    const T = r.tier, J = r.joint;
    const stacked = (k, n) => T[k] && T[k].near[0] >= n && T[k].near[1] >= n;
    ok("every walker has a jointed leg on each side at full detail",
       stacked("spitter", 3) && stacked("skitter", 3) && stacked("collector", 3) &&
       stacked("brute", 4) && stacked("shambler", 2),
       Object.keys(T).map(k => `${k} ${T[k] ? T[k].near.join("/") : "-"}`).join(", "));
    const farOk = (k, n) => T[k] && T[k].far[0] >= n && T[k].far[1] >= n;
    ok("and legs in the MIDDLE tier too - the one a spitter and a collector are seen at",
       farOk("spitter", 2) && farOk("skitter", 2) && farOk("collector", 2) &&
       farOk("brute", 4) && farOk("shambler", 2),
       Object.keys(T).map(k => `${k} ${T[k] ? T[k].far.join("/") : "-"}`).join(", "));
    ok("both tiers stand on the ground, not on a body with the legs left off",
       Object.values(T).every(t => t && Math.abs(t.drop) < .18 && Math.abs(t.ground) < .12),
       Object.keys(T).map(k => `${k} tier drop ${T[k] ? T[k].drop : "-"} / ground ${T[k] ? T[k].ground : "-"}`).join(", "));
    const strides = (k, apart) => J[k] && J[k].apart > apart && J[k].together < J[k].apart*.45;
    ok("the feet come apart along the stride and go back together",
       strides("spitter", .25) && strides("skitter", .12) && strides("collector", .30),
       Object.keys(J).map(k => J[k] ? `${k} apart ${J[k].apart} together ${J[k].together}` : `${k} -`).join(", "));
    const lifts = (k, lift) => J[k] && J[k].lift > lift && J[k].planted < .01;
    ok("and the swinging foot comes up off the planted one, which the body stands on",
       lifts("spitter", .03) && lifts("skitter", .02) && lifts("collector", .04),
       Object.keys(J).map(k => J[k] ? `${k} lift ${J[k].lift} planted ${J[k].planted}` : `${k} -`).join(", "));
  }

  console.log("\n=== 33. THE ANIMAL FLINCHES, AND IT DIES ON SCREEN ===");
  {
    // Getting hit was a white strobe and a screen shake; the body itself did
    // not react. Standing still, it was a statue. Dying was a table appearing
    // over a body that was still standing there. Now a blow from the right
    // leans the body left, snaps the head toward it and drops it into a
    // crouch that eases back out; a standing animal breathes; and death is a
    // beat on the clock - the legs go, then the body goes over away from the
    // blow, and the receipt comes up over the fall, not before it.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const endEl = () => document.getElementById("end");
      const boot = () => {
        g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.disarm();
        g.place(0,0); g.aim(0); g.step(20, 1/60); g.clearEnemies();
      };
      const out = {};
      boot();
      g.step(90, 1/60);
      // 1. the breath: two seconds standing, watching the squash and the clock
      const still = g.anim();
      let mn = 9, mx = -9;
      for(let i=0;i<120;i++){ g.step(1, 1/60); const a = g.anim(); mn = Math.min(mn, a.sq); mx = Math.max(mx, a.sq); }
      out.still = { amp: still.amp, br0: still.br, br1: g.anim().br, span: +(mx - mn).toFixed(4) };
      // 2. a blow from the +x side, facing +z. aim() right before it: an idle
      //    animal turns to face the camera between frames.
      g.aim(0); g.place(0,0); g.step(2, 1/60);
      g.hurtFrom(5, 4, 0);
      out.hit = g.anim();
      let low = 9;
      for(let i=0;i<6;i++){ g.step(1, 1/60); low = Math.min(low, g.anim().sq); }
      out.crouch = low; out.hold = g.anim();
      g.step(34, 1/60); out.after = g.anim();
      // 3. from behind: shoved forward. No source at all: knocked back.
      g.step(60, 1/60); g.aim(0);
      g.hurtFrom(5, 0, -3); g.step(1, 1/60); out.behind = g.anim();
      g.step(60, 1/60); g.aim(0);
      g.hitMe(5); g.step(1, 1/60); out.noSrc = g.anim();
      // 4. the death, stepped by hand so the shape is the shape at any frame
      //    rate: over at once, the receipt held clear, then the drop, then
      //    the topple away from the blow, then the receipt.
      g.step(60, 1/60); g.aim(0);
      g.hurtFrom(1e12, 4, 0);
      const op = () => getComputedStyle(endEl()).opacity;
      out.dead0 = { over: g.state().over, dfx: g.deathFx(), died: endEl().classList.contains("died"),
                    on: endEl().classList.contains("on"), op: op(), an: g.anim() };
      g.deathStep(24, 1/60);
      out.dead1 = { dfx: g.deathFx(), op: op(), an: g.anim() };
      g.deathStep(200, 1/60);
      out.dead2 = { dfx: g.deathFx(), op: op(), an: g.anim() };
      // 5. a new run stands the animal back up
      g.start("ox"); g.step(2, 1/60);
      out.again = { dfx: g.deathFx(), an: g.anim(), style: endEl().style.opacity,
                    died: endEl().classList.contains("died"), on: endEl().classList.contains("on") };
      // 6. and the real loop drives the beat, past over, without step()
      boot(); g.step(30, 1/60); g.aim(0); g.pause(false);
      g.hurtFrom(1e12, 4, 0);
      const d0 = g.deathFx(), a0 = g.anim().dead;
      for(let i=0;i<4;i++) await frame();
      out.clock = { d0, d1: g.deathFx(), a0, a1: g.anim().dead, over: g.state().over };
      g.start("ox"); g.step(2, 1/60);
      return out;
    });
    ok("a standing animal breathes: no stride, but the body rises and falls and the clock runs",
       r.still.amp < .03 && r.still.span > .01 && r.still.br1 > r.still.br0 + 3,
       `amp ${r.still.amp}, sq span ${r.still.span} over 2 s, br ${r.still.br0} -> ${r.still.br1}`);
    ok("a blow from the right leans the body left and snaps the head toward it",
       r.hit.bank < -.1 && r.hit.look > .2 && r.hit.hitR < -.9,
       `bank ${r.hit.bank}, look ${r.hit.look}, hitR ${r.hit.hitR} hitF ${r.hit.hitF}`);
    ok("and it stays staggered that way while the crouch plays, not just on the hit frame",
       r.hold.bank < -.18 && r.hold.hit > .3,
       `six frames on: bank ${r.hold.bank}, pulse ${r.hold.hit}`);
    ok("it drops into a crouch and is back up two thirds of a second later",
       r.crouch < .92 && r.after.sq > .97 && Math.abs(r.after.bank) < .08 && r.after.hit === 0,
       `sq low ${r.crouch}, at +40 frames sq ${r.after.sq} bank ${r.after.bank} hit ${r.after.hit}`);
    ok("a blow from behind shoves it forward; a blow from nowhere knocks it back",
       r.behind.lunge > .3 && r.noSrc.lunge < -.3,
       `behind lunge ${r.behind.lunge}, no-source lunge ${r.noSrc.lunge}`);
    ok("the fatal blow ends the run at once, and holds the receipt clear",
       r.dead0.over === true && r.dead0.dfx > 1 && r.dead0.died && r.dead0.on && r.dead0.op === "0" && r.dead0.an.dead === 0,
       `over ${r.dead0.over}, beat ${r.dead0.dfx}, died ${r.dead0.died}, receipt opacity ${r.dead0.op}`);
    ok("the legs go first: under half its height inside the first half second",
       r.dead1.an.dead > .2 && r.dead1.an.sq < .7 && r.dead1.op === "0" && Math.abs(r.dead1.an.bank) < .2,
       `dead ${r.dead1.an.dead} sq ${r.dead1.an.sq} bank ${r.dead1.an.bank}, receipt still ${r.dead1.op}`);
    ok("then the body goes over, away from the blow, and the receipt comes up as the beat ends",
       r.dead2.dfx === 0 && r.dead2.an.dead >= .99 && r.dead2.an.bank < -.6 && r.dead2.an.sq < .5 && r.dead2.an.amp < .01 && r.dead2.op === "1",
       `beat ${r.dead2.dfx}, dead ${r.dead2.an.dead}, bank ${r.dead2.an.bank} sq ${r.dead2.an.sq} amp ${r.dead2.an.amp}, receipt ${r.dead2.op}`);
    ok("a new run stands it back up with nothing of the fall left on it",
       r.again.dfx === 0 && r.again.an.dead === 0 && Math.abs(r.again.an.sq - 1) < .05 && Math.abs(r.again.an.bank) < .05 && r.again.style === "" && !r.again.on,
       `beat ${r.again.dfx}, dead ${r.again.an.dead}, sq ${r.again.an.sq}, bank ${r.again.an.bank}, style "${r.again.style}", end on ${r.again.on}`);
    ok("and the real frame loop plays the beat after the run is over",
       r.clock.over === true && r.clock.d1 < r.clock.d0 && r.clock.a1 > r.clock.a0,
       `beat ${r.clock.d0} -> ${r.clock.d1}, dead ${r.clock.a0} -> ${r.clock.a1} over four frames`);
  }

  console.log("\n=== 34. THE BOSS WINDS UP, AND THEN IT HITS ===");
  {
    // A boss ability was a hazard ring on the ground and a 22% size pop. The
    // body did nothing: the tell was a shape standing there for a second and
    // the act was the same shape standing there for a shorter one. Now every
    // ability is a beat in the body - a wind-up that gathers through the
    // tell, a snap into the act, an ease back out over the first half second
    // of the rest - and the plans hang their own limbs on it: THE MATRIARCH
    // rears up and drops onto its forelimbs, THORNBACK bristles and heaves,
    // SKYSPLITTER gathers its wings and throws them, TERRAVORE gapes and
    // flares its tooth ring. bossCue() puts the live boss at an exact moment
    // of an ability so the pose there can be read without waiting for it.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const boot = (bi) => {
        g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.disarm(); g.place(0,0); g.aim(0);
        g.step(20, 1/60); g.clearEnemies();
        g.boss(bi); g.step(1, 1/60);
        const b = g.bossAt(); g.place(b.x - 9, b.z); g.aim(0);
        g.bossCue("slam", "move", 2.0); g.step(60, 1/60);   // up out of the ground, standing, rest long over
        return g.bossAt();
      };
      const out = { kinds:{} };
      // 1. every ability, read at the start, middle and top of its tell, in
      //    its act, and at three points of the rest. TERRAVORE carries all five.
      boot(3);
      for(const k of ["slam","sinkhole","charge","spokes","evict"]){
        const t0   = g.bossCue(k, "tell");
        const half = g.bossCue(k, "tell", t0.t*.5);
        const top  = g.bossCue(k, "tell", .0001);
        const act  = g.bossCue(k, "act");
        const r0   = g.bossCue(k, "move");                 // first instant of the rest
        const r3   = g.bossCue(k, "move", r0.t - .3);
        const r9   = g.bossCue(k, "move", r0.t - .9);      // past the ease-out
        out.kinds[k] = { t0, half, top, act, r0, r3, r9 };
      }
      // 2. the real AI on THE MATRIARCH: rest runs out, tell, slam, rest -
      //    sampled every frame with nothing cued
      boot(0);
      g.bossCue("slam", "move", .2);
      const trace = [];
      // .2 s of rest left, 1.15 tell, .30 act, then 2.27 s of the 2.5 s rest
      for(let i=0;i<235;i++){ g.step(1, 1/60); const b = g.beat(); trace.push({ ph:b.phase, u:b.u, act:b.act, sq:b.sq }); }
      const tell = trace.filter(s=>s.ph==="tell"), act = trace.filter(s=>s.ph==="act");
      let climbs = true;
      for(let i=1;i<tell.length;i++) if(tell[i].u < tell[i-1].u - 1e-6) climbs = false;
      const snaps = [];
      for(let i=1;i<trace.length;i++) if(Math.abs(trace[i].sq - trace[i-1].sq) > .3) snaps.push(trace[i-1].ph + ">" + trace[i].ph);
      const firstMove = trace.findIndex((s,i)=> i > 0 && s.ph==="move" && trace[i-1].ph==="act");
      out.cycle = { tellN: tell.length, actN: act.length, u0: tell[0] && tell[0].u, uTop: tell.length ? tell[tell.length-1].u : null,
                    climbs, snaps, actSqMax: act.length ? Math.max(...act.map(s=>s.sq)) : null,
                    moveAct: firstMove > 0 ? trace[firstMove].act : null,
                    end: trace[trace.length-1] };
      // 3. the limbs, off the captured boxes: neutral, top of the tell, act.
      //    Every plan is drawn paused, so the walk cannot touch e.sq between
      //    frames - which is also how the draw is caught leaving the beat in it.
      const cap = async (kind, phase, t) => {
        g.bossCue(kind, phase, t); g.captureEnemy();
        await frame(); await frame(); await frame();
        return g.enemyPos();
      };
      const diff = (A, B) => {
        const n = Math.min(A.length, B.length)/6, d = { n, dr:[], df:[], dy:[] };
        for(let i=0;i<n;i++){ d.dr.push(B[i*6]-A[i*6]); d.df.push(B[i*6+1]-A[i*6+1]); d.dy.push(B[i*6+2]-A[i*6+2]); }
        const sum = arr => ({ max:+Math.max(...arr).toFixed(3), min:+Math.min(...arr).toFixed(3),
                              up:arr.filter(v=>v>.25).length, dn:arr.filter(v=>v<-.25).length,
                              up1:arr.filter(v=>v>1).length, moved:arr.filter(v=>Math.abs(v)>.1).length });
        return { n, r:sum(d.dr), f:sum(d.df), y:sum(d.dy) };
      };
      out.limbs = {};
      for(const [bi, kind] of [[0,"slam"],[1,"slam"],[2,"charge"],[3,"slam"]]){
        const b = boot(bi);
        g.pause(true);
        const neutral = await cap("slam", "move", .5);
        const top = await cap(kind, "tell", .0001);
        const act = await cap(kind, "act");
        const wsq = g.gait().find(e=>e.boss).sq;
        g.pause(false);
        out.limbs[b.body] = neutral && top && act
          ? { n:neutral.length/6, tell:diff(neutral, top), act:diff(neutral, act), wsq }
          : { n:0, missing:[!neutral, !top, !act] };
      }
      g.start("ox"); g.step(2, 1/60);
      return out;
    });
    const K = r.kinds;
    const at = (o, f) => `${f} sq ${o[f].sq} lf ${o[f].lf}`;
    ok("nothing is cued at the start of a tell; every ability is fully wound at the top of it",
       Object.values(K).every(o => o.t0.u === 0 && o.t0.sq === 1 && o.t0.lf === 0 && o.top.u > .99 && o.top.act === 0),
       Object.entries(K).map(([k,o]) => `${k} u ${o.t0.u}->${o.top.u}`).join(", "));
    ok("the slam and the sinkhole rear up - taller and leaning back - and the charge and the evict crouch",
       K.slam.top.sq > 1.1 && K.slam.top.lf < -.1 && K.sinkhole.top.sq > 1.15 && K.sinkhole.top.lf < -.15 &&
       K.charge.top.sq < .9 && K.charge.top.lf < -.1 && K.evict.top.sq < .95 && K.spokes.top.sq > 1.05,
       Object.entries(K).map(([k,o]) => `${k} ${at(o,"top")}`).join("; "));
    ok("the wind-up gathers: halfway through the tell it is a quarter of the way into the pose, not half",
       Object.values(K).every(o => { const a = Math.abs(o.half.sq - 1), b = Math.abs(o.top.sq - 1); return a > b*.15 && a < b*.35; }),
       Object.entries(K).map(([k,o]) => `${k} half ${(Math.abs(o.half.sq-1)/Math.abs(o.top.sq-1)).toFixed(2)}`).join(", "));
    ok("the act snaps the other way: the slam and sinkhole flatten and lunge, the charge throws itself forward",
       K.slam.act.act === 1 && K.slam.act.sq < .8 && K.slam.act.lf > .15 && K.sinkhole.act.sq < .7 &&
       K.charge.act.lf > .2 && K.evict.act.sq > 1.05 && Object.values(K).every(o => o.act.u === 0),
       Object.entries(K).map(([k,o]) => `${k} ${at(o,"act")}`).join("; "));
    ok("the rest starts where the act left it and is back to neutral inside the first second",
       Object.values(K).every(o => o.r0.act > .99 && o.r0.sq === o.act.sq && o.r3.act > .2 && o.r3.act < .7 &&
                                    o.r9.act === 0 && o.r9.sq === 1 && o.r9.lf === 0),
       Object.entries(K).map(([k,o]) => `${k} act ${o.r0.act} > ${o.r3.act} > ${o.r9.act}`).join(", "));
    const C = r.cycle;
    ok("THE MATRIARCH's own AI drives it: the wind-up climbs through the whole tell, from nothing to full",
       C.tellN > 60 && C.u0 < .05 && C.uTop > .95 && C.climbs,
       `${C.tellN} tell frames, u ${C.u0} -> ${C.uTop}, monotonic ${C.climbs}`);
    ok("one snap in the whole cycle, at the moment the tell becomes the act; the act stays flat; the rest eases home",
       C.snaps.length === 1 && C.snaps[0] === "tell>act" && C.actN > 10 && C.actSqMax < .8 &&
       C.moveAct > .95 && C.end.ph === "move" && Math.abs(C.end.sq - 1) < .01 && C.end.act < .02,
       `snaps [${C.snaps.join(" ")}], ${C.actN} act frames sq<=${C.actSqMax}, first rest frame act ${C.moveAct}, end ${C.end.ph} sq ${C.end.sq}`);
    const L = r.limbs;
    const j = (o) => JSON.stringify(o);
    ok("THE MATRIARCH's forelimbs come up off the ground for the slam - a fifth of its height or more",
       L.matriarch && L.matriarch.n > 40 && L.matriarch.tell.y.up1 >= 8 && L.matriarch.tell.y.max > 1.8,
       L.matriarch ? `${L.matriarch.n} boxes, tell dy ${j(L.matriarch.tell.y)}` : "no capture");
    ok("and they are down on it again the instant the slam lands, the jaw dropped and nothing else moved",
       L.matriarch && L.matriarch.act.y.max < .05 && L.matriarch.act.y.min < -.2 && L.matriarch.act.y.up === 0 &&
       L.matriarch.act.f.moved === 0 && L.matriarch.act.r.moved === 0,
       L.matriarch ? `act dy ${j(L.matriarch.act.y)} df moved ${L.matriarch.act.f.moved} dr moved ${L.matriarch.act.r.moved}` : "no capture");
    ok("THORNBACK's thorns rise in the tell and lie back along the shell in the heave",
       L.thornback && L.thornback.tell.y.max > .8 && L.thornback.act.f.dn >= 16 && L.thornback.act.y.max < .2,
       L.thornback ? `tell dy max ${L.thornback.tell.y.max}; act df ${j(L.thornback.act.f)} dy max ${L.thornback.act.y.max}` : "no capture");
    ok("SKYSPLITTER pulls its wings back for the charge and throws them forward with its head as it goes",
       L.skysplitter && L.skysplitter.tell.f.min < -1.2 && L.skysplitter.tell.f.dn >= 12 &&
       L.skysplitter.act.f.up >= 16 && L.skysplitter.act.y.min < -.5,
       L.skysplitter ? `tell df ${j(L.skysplitter.tell.f)}; act df ${j(L.skysplitter.act.f)} dy min ${L.skysplitter.act.y.min}` : "no capture");
    ok("TERRAVORE's tooth ring flares open and its mandibles step forward when the slam lands",
       L.terravore && (L.terravore.act.r.moved + L.terravore.act.y.moved) >= 12 && L.terravore.act.f.max > .15,
       L.terravore ? `act dr ${j(L.terravore.act.r)} dy moved ${L.terravore.act.y.moved} df max ${L.terravore.act.f.max}` : "no capture");
    ok("the draw leaves nothing of the beat in the body: e.sq is walk()'s again after every drawn frame",
       Object.values(L).every(o => o.wsq !== undefined && Math.abs(o.wsq - 1) < .01),
       Object.entries(L).map(([k,o]) => `${k} sq ${o.wsq}`).join(", "));
  }

  console.log("\n=== 35. THE HORDE FALLS DOWN ===");
  {
    // A kill was a splice. The body was on the field one frame and a burst of
    // particles the next, and eleven body plans' worth of animal vanished the
    // way a sprite is unset. Now it FALLS: killEnemy() hands the body to a
    // corpse list with the direction it was hit from, and the draw runs the
    // same plan down the same squash-and-shear pose path with deathPose(u) -
    // the legs go and the body shears the way it was hit, it lies there, it
    // goes into the ground. A flier drops out of the air first. World-space
    // FX a plan hangs on a live body - the collector's beacon, the pterling's
    // warning and streak, the terravore's seam - go with the kill. Everything
    // here runs PAUSED and steps the fall by hand, same as 34.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const boot = () => {
        g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.disarm(); g.place(0,0); g.aim(0);
        g.step(20, 1/60); g.clearEnemies(); g.clearGems();
      };
      // the standing body's DRAWN top - the world-space capture the corpse
      // pass uses, so the two sides of "not a cut" are measured the same way.
      // It used to read eb()'s untransformed mesh capture, which does not carry
      // the pose: once the bite pitched the body about its hips (R256), a boss
      // caught in a wind-up drew its crest a metre from where the mesh said.
      // The box COUNT stays the mesh capture's: the world capture also holds
      // the body's own FX (a beacon column, a dive streak), which the
      // crumpled-count check below deliberately expects to be gone.
      const standing = async () => {
        const gs = g.gait()[0];
        g.captureEnemy(); g.captureEnemyWorld(); await frame(); await frame();
        const bx = g.enemyPos() || [], b = g.enemyBox(); if(!b) return { n:bx.length/6, top:null, bot:null, hop:gs.hop, gs };
        return { n:bx.length/6, top:+(b.maxY - gs.y).toFixed(3), bot:+(b.minY - gs.y).toFixed(3), hop:gs.hop, gs };
      };
      // step the first corpse to normalised time u and read its drawn box
      const at = async (u) => {
        const c0 = g.corpses()[0]; if(!c0) return null;
        const n = Math.round(Math.max(0, u*c0.dur - c0.t)*60);
        if(n > 0) g.corpseStep(n, 1/60);
        const c = g.corpses()[0]; if(!c) return null;
        g.captureCorpse(); await frame(); await frame();
        const b = g.corpseBox(); if(!b) return null;
        return { u:c.u, n:b.n, top:+(b.maxY - b.gy).toFixed(3), bot:+(b.minY - b.gy).toFixed(3),
                 cx:+((b.minX + b.maxX)/2 - c.x).toFixed(3), cz:+((b.minZ + b.maxZ)/2 - c.z).toFixed(3),
                 tx:+(b.tx - c.x).toFixed(3), tz:+(b.tz - c.z).toFixed(3),
                 marks:g.fowlMarks(), amp:c.amp, lg:c.lg, bk:c.bk };
      };
      const out = {};
      // 1. THE LIST. The kill puts the body on it at once, with the shove it
      //    died under as its direction; the next world step takes it off the
      //    field; the fall runs its length and the body is gone.
      boot();
      g.spawnAt("shambler", 0, 6); g.step(40, 1/60); g.pause(true);
      g.hurtAt(0, 1e9, 7, 0);
      const c0 = g.corpses()[0], onField = g.state().enemies;
      // the frame's box count at the kill, while the dead body is still in the
      // enemy list, against the frame one step later when it is only a corpse:
      // the live pass has to skip it, or the kill frame draws it twice
      g.clearFx(); g.clearGems(); await frame(); await frame();
      const bxKill = g.state().boxes;
      g.step(1, 1/60); g.pause(true);
      const c1 = g.corpses()[0];
      g.clearFx(); g.clearGems(); await frame(); await frame();
      const bxNext = g.state().boxes;
      out.list = { c0, onField, enemies:g.state().enemies, c1, bxKill, bxNext,
                   late:g.corpseStep(31, 1/60), gone:g.corpseStep(2, 1/60) };
      // with no shove on it, it drops away from the player
      g.spawnAt("shambler", 0, -6); g.step(2, 1/60); g.pause(true);
      g.hurtAt(0, 1e9, 0, 0);
      out.away = g.corpses()[0];
      // 2. THE CAP, and the two ways the list is emptied
      boot();
      for(let i=0;i<60;i++){ const a = i*(Math.PI*2/60); g.spawnAt("shambler", Math.sin(a)*5, Math.cos(a)*5); }
      g.step(1, 1/60); g.pause(true);
      const n0 = g.state().enemies;
      for(let i=0;i<n0;i++) g.hurtAt(i, 1e9, 1, 0);
      out.cap = { n0, corpses:g.corpses().length, cleared:g.clearEnemies() + g.corpses().length };
      g.spawnAt("shambler", 0, 5); g.step(1, 1/60); g.pause(true); g.hurtAt(0, 1e9, 1, 0);
      const had = g.corpses().length;
      g.start("ox"); out.cap.restart = { had, now:g.corpses().length };
      // 3. THE POSE TABLE, straight from the function
      out.pose = {};
      for(const u of [0, .15, .3, .36, .4, .49, .55, .7, .85, 1]) out.pose[u] = g.deathPose(u);
      let mono = true;
      for(let u = 0; u < .36; u += .01) if(g.deathPose(u + .01).sq > g.deathPose(u).sq + 1e-9) mono = false;
      out.pose.sqFalls = mono;
      // 4. THE DRAWN BODY. Six kinds and two bosses, killed with a shove
      //    across +x, read standing, at the kill frame, crumpled, lying and
      //    almost gone. The elite is a brute promoted the way a den does it.
      out.fall = {};
      const kinds = ["shambler","brute","spitter","skitter","runner","collector","elite","boss0","boss2"];
      for(const kind of kinds){
        boot();
        if(kind.startsWith("boss")){
          g.boss(+kind.slice(4)); g.step(1, 1/60);
          const b = g.bossAt(); g.place(b.x, b.z - 9); g.step(180, 1/60);
          // the charge boss dies MID-BITE: step to a frame inside the snap's
          // recovery (the bite winds up first now, so the moment is found,
          // not assumed)
          // ...and outside an ability beat, whose wind-up swells the live body
          if(kind === "boss2") for(let i=0;i<600;i++){ const q = g.gait()[0]; if(q && q.lg > .3 && q.lg < .95 && q.btu === 0) break; g.step(1, 1/60); }
        } else {
          g.spawnAt(kind === "elite" ? "brute" : kind, 0, 6);
          if(kind === "elite") g.elite(0);
          g.step(40, 1/60);
        }
        g.pause(true);
        const gs = g.gait()[0];
        if(!gs){ out.fall[kind] = { err:"no subject" }; continue; }
        // the observer well clear of the shot but inside full detail (11 m):
        // a runner has dived onto the player by now
        if(!kind.startsWith("boss")) g.place(gs.x - 6, gs.z + 6);
        const st = await standing();
        g.hurtAt(0, 1e9, kind.startsWith("boss") ? 30 : 7, 0); g.clearFx(); g.clearGems();
        const c = g.corpses()[0];
        if(!c){ out.fall[kind] = { err:"no corpse", enemies:g.state().enemies }; continue; }
        const f = { type:c.type, boss:c.boss, elite:c.elite, dur:c.dur, fx:c.fx, fz:c.fz, nAlive:st.n, topAlive:st.top, botAlive:st.bot, hopAlive:st.hop,
                    u0:await at(0), u4:await at(.4), u5:await at(.55), u97:await at(.97) };
        f.expired = g.corpseStep(4, 1/60);
        out.fall[kind] = f;
      }
      // 5. THE OTHER WAY. A shove along -z: the lean follows the blow, not the lens.
      boot();
      g.spawnAt("brute", 0, 6); g.step(40, 1/60); g.pause(true);
      { const gs = g.gait()[0]; g.place(gs.x - 6, gs.z + 6); }
      g.hurtAt(0, 1e9, 0, -7); g.clearFx(); g.clearGems();
      out.back = { c:g.corpses()[0], u0:await at(0), u4:await at(.4) };
      // 6. THE LAST BOSS. Its death ends the run, the run's end stops the
      //    world, and the body still has to reach the floor under the banner:
      //    frame() steps the fallen on the wall clock once the run is over.
      boot();
      g.boss(3); g.step(1, 1/60);
      { const b = g.bossAt(); g.place(b.x, b.z - 9); g.step(180, 1/60); }
      g.pause(true);
      g.hurtAt(0, 1e9, 30, 0);
      const st0 = g.state(), t0 = g.corpses()[0] ? g.corpses()[0].t : null;
      for(let i=0;i<14;i++) await frame();     // through the .2 s boss hitstop and out the other side
      out.last = { over:st0.over, won:st0.won, enemies:st0.enemies, t0, t1:g.corpses()[0] ? g.corpses()[0].t : null,
                   nm:g.corpses()[0] && g.corpses()[0].type };
      g.start("ox"); g.step(2, 1/60);
      return out;
    });
    const L = r.list;
    ok("a kill puts the body on the corpse list at once, facing where it faced, headed the way it was shoved",
       L.c0 && L.c0.type === "shambler" && L.c0.t === 0 && L.c0.dur === .55 && L.c0.fx === 1 && L.c0.fz === 0 &&
       Math.abs(L.c0.hd - Math.PI) < .05 && L.onField === 1,
       L.c0 ? `t ${L.c0.t} dur ${L.c0.dur} dir ${L.c0.fx},${L.c0.fz} hd ${L.c0.hd}, ${L.onField} on the field` : "no corpse");
    ok("the next world step takes it off the field and the fall has begun; a body with no shove on it drops away from the player",
       L.enemies === 0 && L.c1 && L.c1.t > .016 && L.c1.t < .018 && r.away && r.away.fz < -.99,
       `enemies ${L.enemies}, t ${L.c1 && L.c1.t}, unshoved dir ${r.away && r.away.fx},${r.away && r.away.fz}`);
    ok("the kill frame draws the body once: the dead body still in the enemy list is left to the corpse pass, so the frame holds the same boxes as the one after it",
       L.bxKill > 0 && L.bxKill === L.bxNext, `boxes at the kill ${L.bxKill}, one step on ${L.bxNext}`);
    ok("the fall runs .55 s for trash and the body is gone at the end of it, not before",
       L.late === 1 && L.gone === 0, `at .533 s ${L.late}, at .567 s ${L.gone}`);
    ok("the list holds 48: the oldest go first, and clearEnemies() and a new run both empty it",
       r.cap.n0 === 60 && r.cap.corpses === 48 && r.cap.cleared === 0 && r.cap.restart.had === 1 && r.cap.restart.now === 0,
       `${r.cap.n0} killed -> ${r.cap.corpses}, cleared ${r.cap.cleared}, restart ${r.cap.restart.had} -> ${r.cap.restart.now}`);
    const Pz = r.pose, p = u => Pz[u];
    ok("deathPose: neutral at the kill frame - squash 1, no lean, no drop, no sink, no fade",
       p(0).sq === 1 && p(0).lean === 0 && p(0).drop === 0 && p(0).sink === 0 && p(0).fade === 0,
       JSON.stringify(p(0)));
    ok("the legs go over the first 40%: the squash falls without a rise to below half, the lean reaches .6, the drop is whole",
       Pz.sqFalls && p(.15).sq > .75 && p(.3).sq < .6 && p(.4).sq < .5 && p(.4).drop === 1 && p(.4).lean > .55 && p(.4).sink === 0,
       `sq ${p(.15).sq.toFixed(3)} ${p(.3).sq.toFixed(3)} ${p(.4).sq.toFixed(3)} monotonic ${Pz.sqFalls}; lean ${p(.4).lean.toFixed(3)} drop ${p(.4).drop}`);
    ok("one small rebound past the bottom, then it lies flat: sq .49 at the top of the bounce, .42 by .7 and no sink yet",
       p(.49).sq > p(.4).sq + .02 && p(.49).sq < .5 && Math.abs(p(.7).sq - .42) < .001 && p(.7).sink === 0 && p(.7).lean > .6,
       `sq at .4 ${p(.4).sq.toFixed(3)} .49 ${p(.49).sq.toFixed(3)} .7 ${p(.7).sq.toFixed(3)}; sink at .7 ${p(.7).sink}`);
    ok("the sink is the last 30% and complete at the end; the fade climbs across the first two thirds",
       p(.85).sink > .4 && p(.85).sink < .6 && p(1).sink === 1 && p(.3).fade > .4 && p(.3).fade < .5 && p(.7).fade === 1,
       `sink .85 ${p(.85).sink.toFixed(3)} 1 ${p(1).sink}; fade .3 ${p(.3).fade.toFixed(3)} .7 ${p(.7).fade}`);
    const F = r.fall, K = Object.keys(F), fine = K.filter(k => !F[k].err && F[k].u0 && F[k].u4 && F[k].u5 && F[k].u97);
    // a kind the game failed to fell is a red row below, not a harness crash
    const has = (...ks) => ks.every(k => fine.includes(k));
    const row = (k, f) => `${k} ${f.u0.top}>${f.u4.top}>${f.u97.top}`;
    ok("every kind was killed and captured standing, at the kill frame, crumpled, lying and near the end",
       fine.length === K.length, K.filter(k => !fine.includes(k)).map(k => `${k}: ${JSON.stringify(F[k]).slice(0, 80)}`).join("; ") || `${K.length} kinds`);
    // the collector's kill frame is read at 40% instead: its corpse capture
    // is world-space and holds the beacon column - nine metres of it - that
    // eb()'s live capture never sees, and the beacon is out by 35%
    const cut = fine.filter(k => k !== "collector");
    ok("the kill frame is not a cut: the corpse draws to the same top as the standing body did",
       cut.every(k => Math.abs(F[k].u0.top - F[k].topAlive) < .06) && has("collector") && (F.collector.u0.top > F.collector.topAlive*3 || Math.abs(F.collector.u0.top - F.collector.topAlive) < .06),
       cut.map(k => `${k} ${F[k].topAlive}->${F[k].u0.top}`).join(", ") + (has("collector") ? `; collector ${F.collector.topAlive}->${F.collector.u0.top} with its beacon` : "; collector missing"));
    ok("crumpled at 40%, every body draws to under 60% of its standing height and is still on the ground",
       fine.every(k => F[k].u4.top < F[k].u0.top*.60 && F[k].u4.bot > -.15 && F[k].u4.bot < .25),
       fine.map(k => `${k} ${(F[k].u4.top/F[k].u0.top).toFixed(2)} bot ${F[k].u4.bot}`).join(", "));
    // the lean is read off the highest box's centre, kill frame to crumple: a
    // body's own shape - a tail a metre behind its origin - is not a lean, and
    // the AABB centre of an asymmetric body drifts as its boxes widen under
    // the squash; a box centre does neither. What is left along the other
    // axis is the dying pose easing out (the bite, the lean into the run) and
    // has to stay well under the fall - and the bite does not ease out of a
    // corpse at all: SKYSPLITTER is killed mid-bite here, its crest is the
    // highest box at both marks (draw index 10, the same box), and a bite
    // pulled back on an eleven-metre shear arm swung it three metres along z
    // against three and a half along the shove.
    const dtx = k => +(F[k].u4.tx - F[k].u0.tx).toFixed(3), dtz = k => +(F[k].u4.tz - F[k].u0.tz).toFixed(3);
    ok("it fell the way it was hit: shoved across +x, every body's top moves to +x as it crumples, and at least twice what it moves along z",
       fine.every(k => F[k].fx === 1 && dtx(k) > .05 && Math.abs(dtz(k)) < dtx(k)*.5),
       fine.map(k => `${k} ${dtx(k)},${dtz(k)}`).join(", "));
    const bk = r.back.u4 && { x:+(r.back.u4.tx - r.back.u0.tx).toFixed(3), z:+(r.back.u4.tz - r.back.u0.tz).toFixed(3) };
    ok("...and shoved along -z, the brute's top moves to -z as it crumples, and at least twice what it moves along x",
       r.back.c && r.back.c.fz === -1 && bk && bk.z < -.05 && Math.abs(bk.x) < -bk.z*.5,
       bk ? `dir ${r.back.c.fx},${r.back.c.fz} top moved ${bk.x},${bk.z}` : "no capture");
    ok("near the end every body is under the ground, whole, and it is gone at the end",
       fine.every(k => F[k].u97.top < 0 && F[k].expired === 0),
       fine.map(k => `${k} top ${F[k].u97.top}`).join(", "));
    ok("the stride dies with it: the gait amplitude is under a fifth of a stride by the time it lies",
       fine.every(k => F[k].u5.amp < .2), fine.map(k => `${k} amp ${F[k].u5.amp}`).join(", "));
    // the charge boss reaches the ox and bites inside the three seconds it is
    // given, so it is the body that dies mid-bite here
    ok("...but the bite does not: SKYSPLITTER died mid-bite and lies with the bite still on it, the same as at the kill frame - it went down head first",
       has("boss2") && F.boss2.u0.lg > .2 && F.boss2.u5.lg === F.boss2.u0.lg && fine.every(k => F[k].u5.lg === F[k].u0.lg && F[k].u5.bk === F[k].u0.bk),
       (has("boss2") ? `boss2 lg ${F.boss2.u0.lg} -> ${F.boss2.u5.lg}; ` : "boss2 missing; ") + fine.map(k => `${k} lg ${F[k].u0.lg} bk ${F[k].u0.bk}`).join(", "));
    ok("the fliers fall out of the air: SKYSPLITTER hung well over a metre up alive, and it and the runner lie ON the ground - not hovering, not under it",
       F.boss2 && F.boss2.botAlive > 1 && ["runner","boss2"].every(k => F[k] && F[k].u4 && Math.abs(F[k].u4.bot) < .12 && Math.abs(F[k].u5.bot) < .12),
       ["runner","boss2"].map(k => F[k] && F[k].u4 ? `${k} alive bot ${F[k].botAlive} -> lying ${F[k].u4.bot} / ${F[k].u5.bot}` : `${k} missing`).join(", "));
    ok("the world-space FX go with the kill: crumpled, the runner and the collector draw exactly their standing box count, and the collector's beacon is out",
       has("runner","collector") && ["runner","collector"].every(k => F[k].u4.n === F[k].nAlive) && F.collector.u4.marks === 0 && F.collector.u0.n > F.collector.nAlive,
       ["runner","collector"].map(k => F[k] && F[k].u4 ? `${k} ${F[k].u0.n}->${F[k].u4.n} (alive ${F[k].nAlive})` : `${k} missing`).join(", ") + `, beacon ${F.collector.u4 && F.collector.u4.marks}`);
    // the size is read with the hop taken back off: each body is caught at one
    // frame of a hop whose phase is the random one it spawned with, and a brute
    // at the crest against an elite in the trough is 1.52 against 1.77 - a
    // 1.38x animal measuring 1.16x, and a check that went red one run in many
    const grounded = k => +(F[k].topAlive - F[k].hopAlive).toFixed(3);
    ok("an elite takes .85 s to go down and a boss 1.6, and the elite is drawn at its size",
       has("elite","brute","boss0","boss2") && F.elite.elite && F.elite.dur === .85 && F.boss0.boss && F.boss0.dur === 1.6 && F.boss2.dur === 1.6 &&
       grounded("elite") > grounded("brute")*1.30 && grounded("elite") < grounded("brute")*1.46,
       `elite ${F.elite && F.elite.dur} (${has("elite","brute") ? `${grounded("elite")} vs brute ${grounded("brute")} with the hops ${F.elite.hopAlive}/${F.brute.hopAlive} off, x${(grounded("elite")/grounded("brute")).toFixed(3)}` : "missing"}), bosses ${F.boss0 && F.boss0.dur} ${F.boss2 && F.boss2.dur}`);
    const La = r.last || {};
    ok("the last boss ends the run and still falls: the world is stopped and the corpse clock ran on the frame",
       La.over === true && La.won === true && La.t0 === 0 && La.t1 > La.t0 && La.nm === "boss",
       `over ${La.over} won ${La.won}, corpse t ${La.t0} -> ${La.t1} across fourteen frames with the world stopped`);
  }

  console.log("\n=== 36. EVERY STAGE WEARS ITS OWN COAT ===");
  {
    // The roster sheet at R200 was nine rows of one colour each: MTYPE held a
    // single palette per LINE, the only stage rule was "the apex is 18%
    // darker", and five evolutions read as one animal with more parts glued
    // on. The standard the player named is the pocket-monster one - the
    // orange lizard turns red, the red fish turns into a blue serpent - so
    // STAGEPAL gives every stage from the first evolution up its own body,
    // belly and accent, and every line one hard turn. This reads the table
    // AND the colour the last frame was actually painted in, per form, so a
    // plan that quietly kept reading the line's palette would fail here.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const lab = c => { const f = v => v<=.04045 ? v/12.92 : Math.pow((v+.055)/1.055,2.4);
        const [R,G,B] = c.map(v => f(Math.max(0,Math.min(1,v))));
        let X=(R*.4124+G*.3576+B*.1805)/.95047, Y=(R*.2126+G*.7152+B*.0722),
            Z=(R*.0193+G*.1192+B*.9505)/1.08883;
        const k = t => t>.008856 ? Math.cbrt(t) : 7.787*t+16/116;
        X=k(X);Y=k(Y);Z=k(Z); return [116*Y-16, 500*(X-Y), 200*(Y-Z)]; };
      const dE = (a,b) => { const A=lab(a), B=lab(b);
        return Math.hypot(A[0]-B[0], A[1]-B[1], A[2]-B[2]); };
      const hue = c => { const L = lab(c); return { h:(Math.atan2(L[2],L[1])*180/Math.PI+360)%360, C:Math.hypot(L[1],L[2]) }; };
      const dh = (a,b) => { const d = Math.abs(a-b)%360; return d > 180 ? 360-d : d; };
      const lum = c => .2126*c[0] + .7152*c[1] + .0722*c[2];
      const IDS = ["intern","scrap","spark","ox","ghoul","accnt","twin","surge","pyre"];
      const out = {};
      for(const id of IDS){
        g.wipeSave(); g.start(id); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.disarm(); g.place(0,0); g.aim(0);
        const ty = g.curType(), row = { ty, st:[] };
        for(let s=0; s<=4; s++){
          if(s) g.evolveTo(s);
          g.step(300, 1/60);                    // the evolution wash is long gone
          await frame(); await frame();
          const tab = g.stagePal(ty, s), drawn = g.monTint();
          row.st.push({ nm:g.stageNm(), c:tab.c, acc:tab.acc, bel:tab.bel,
                        drawn:drawn && drawn[0], dk:drawn && drawn[1],
                        match: drawn ? +dE(tab.c, drawn[0]).toFixed(2) : 99 });
        }
        // the roster numbers: nearest pair of stages, nearest neighbours, the
        // hardest turn (hue, where both coats have a hue; else lightness)
        let minPair = 1e9, minCons = 1e9, turn = 0, minAcc = 1e9, darkOk = true;
        for(let i=0;i<5;i++){
          for(let j=i+1;j<5;j++){ const d = dE(row.st[i].c, row.st[j].c); minPair = Math.min(minPair, d); if(j === i+1) minCons = Math.min(minCons, d); }
          minAcc = Math.min(minAcc, dE(row.st[i].c, row.st[i].acc));
          // and on a PALE coat the dark has to be a colour, not a grey: half of
          // white is the same grey on the star dragon and the bone fish
          if(!row.st[i].dk || !(lum(row.st[i].dk) < lum(row.st[i].drawn) * .75)
             || (lum(row.st[i].drawn) > .7 && hue(row.st[i].dk).C < 10)) darkOk = false;
          if(i){ const a = hue(row.st[i-1].c), b = hue(row.st[i].c), d = dE(row.st[i-1].c, row.st[i].c);
                 turn = Math.max(turn, (a.C > 12 && b.C > 12) ? dh(a.h, b.h) : 0, d >= 45 ? 60 : 0); }
        }
        row.minPair = +minPair.toFixed(1); row.minCons = +minCons.toFixed(1);
        row.turn = Math.round(turn); row.minAcc = +minAcc.toFixed(1); row.darkOk = darkOk;
        row.maxMatch = Math.max(...row.st.map(s => s.match));
        row.hatch = g.typePal(ty).c;
        out[id] = row;
      }
      return out;
    });
    const rows = Object.keys(r), R = k => r[k];
    const names = rows.map(k => R(k).st.map(s => s.nm));
    ok("nine lines, five named stages each, forty-five forms on the sheet",
       rows.length === 9 && names.every(n => n.length === 5 && new Set(n).size === 5),
       names.map(n => n.join(">")).join(" | ").slice(0, 200));
    ok("every stage of every line is drawn in a coat of its own: no two stages of one line are within dE 12 of each other",
       rows.every(k => R(k).minPair >= 12), rows.map(k => `${k} ${R(k).minPair}`).join(", "));
    ok("...and each evolution is a visible change of colour, not a shade: consecutive stages sit dE 18 or more apart",
       rows.every(k => R(k).minCons >= 18), rows.map(k => `${k} ${R(k).minCons}`).join(", "));
    ok("every line makes one hard turn - a hue swing of 60 degrees or better, or a coat that goes from dark to light (dE 45+) - somewhere up the line",
       rows.every(k => R(k).turn >= 60), rows.map(k => `${k} ${R(k).turn}`).join(", "));
    ok("the animal is painted in the table's colour, at every one of the forty-five forms - a plan is not quietly reading the line's palette",
       rows.every(k => R(k).maxMatch < .5), rows.map(k => `${k} ${R(k).maxMatch}`).join(", "));
    ok("the accent is never the body: dE 30 or better apart at every stage, so the markings still read on every coat",
       rows.every(k => R(k).minAcc >= 30), rows.map(k => `${k} ${R(k).minAcc}`).join(", "));
    ok("the dark is at most three quarters of the coat's luminance on every form, and on a pale coat it is a colour (chroma 10+) - a white dragon does not stand on grey legs",
       rows.every(k => R(k).darkOk), rows.filter(k => !R(k).darkOk).join(", ") || "all 45");
    // the card and the game agree about what hatches
    const hatchSame = rows.every(k => R(k).st[0].c.every((v, i) => v === R(k).hatch[i]));
    ok("the hatchling on the card is the hatchling in the game: stage 0 IS the line's palette",
       hatchSame, rows.map(k => `${k} ${R(k).st[0].c.join("/")}`).join(", ").slice(0, 160));
  }

  console.log("\n=== 37. THE APEX IS A NEW SHAPE ===");
  {
    // Section 36 turned the coats. This is the other half of the same
    // complaint - "no creativity between forms" - because a red dragon and a
    // black dragon and a white dragon in the same pose are still one dragon.
    // The measure is the drawn body's box: height over length, width over
    // length, and where the mass sits. Scaling a plan up and adding parts
    // leaves those numbers where they were (the sheet at R201 had every line
    // within .03 across stages 2, 3 and 4); a new animal moves them. The
    // list of lines held to it grows by one a round, and the rest are
    // printed so the log carries the state of the complaint.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const out = {};
      for (const id of g.chars()) {
        const row = [];
        for (const st of [2, 3, 4]) {
          g.wipeSave(); g.start(id); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
          g.drainPicks(true); g.setShake(0); g.place(0, 0); g.aim(0);
          g.evolveTo(st); g.step(300, 1/60);         // the evolution wash is long gone
          g.resume(); g.capturePos();
          await frame(); await frame();
          const b = g.posOut();
          if (!b) { row.push({ st, nm: g.stageNm(), n: 0 }); continue; }
          const n = b.length / 6;
          let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9], cy = 0;
          for (let i = 0; i < n; i++) {                 // r f y hx hz hy
            const c = [b[i*6], b[i*6+1], b[i*6+2]], h = [b[i*6+3], b[i*6+4], b[i*6+5]];
            for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], c[k]-h[k]); mx[k] = Math.max(mx[k], c[k]+h[k]); }
            cy += c[2];
          }
          const W = mx[0]-mn[0], L = mx[1]-mn[1], H = mx[2]-mn[2];
          row.push({ st, nm: g.stageNm(), n, HL: +(H/L).toFixed(2), WL: +(W/L).toFixed(2),
                     massY: +((cy/n - mn[2]) / H).toFixed(2), lo: +mn[2].toFixed(2) });
        }
        out[id] = row;
      }
      return out;
    });
    // one more line each round, R202 to R210 - and now it is all nine
    const DONE = ["intern", "scrap", "spark", "ox", "ghoul", "accnt", "pyre", "surge", "twin"];
    const dist = (a, b) => +(Math.abs(a.HL - b.HL) + Math.abs(a.WL - b.WL)).toFixed(2);
    const pairs = row => [[0,1],[1,2],[0,2]].map(([i,j]) => ({ a: row[i], b: row[j], d: dist(row[i], row[j]) }));
    const line = id => r[id].map(s => `${s.nm} ${s.HL}/${s.WL}`).join(" > ")
                     + `  d ${pairs(r[id]).map(p => p.d).join("/")}`;
    ok("the body is captured at all twenty-seven forms from the third stage up, and every one is more than a handful of boxes",
       Object.values(r).every(row => row.length === 3 && row.every(s => s.n >= 40)),
       Object.keys(r).map(id => `${id} ${r[id].map(s => s.n).join("/")}`).join(", "));
    ok(`the redesigned lines (${DONE.join(", ")}) change shape at every evolution from the third stage up: |dH/L| + |dW/L| of .12 or better between each pair of stages 2, 3 and 4`,
       DONE.every(id => r[id] && pairs(r[id]).every(p => p.d >= .12)),
       DONE.map(id => `${id}: ${line(id)}`).join(" | "));
    ok("...and it is a rear, a sprawl or a coil, not a tweak: the redesigned lines move the mass by .05 of the height or better somewhere across those stages",
       DONE.every(id => r[id] && Math.max(...r[id].map(s => s.massY)) - Math.min(...r[id].map(s => s.massY)) >= .05),
       DONE.map(id => `${id} massY ${r[id].map(s => s.massY).join(">")}`).join(", "));
    // the echo line is the one the numbers alone do not hold: a hydra with a
    // head more at each of two more scales happens to clear .12 and .05 both.
    // What the redesign did is not a matter of degree - THE LEGION is a wall on
    // legs, lower for its length than the rearing HYDRA, and THE MYRIAD is a
    // medusa, hanging in the air where every other stage of the line stands on
    // the ground - so ask for the wall and the hover by name
    const tw = r.twin;
    ok("the echo line rears, then walls, then floats: THE LEGION is lower for its length than THE HYDRA by .08 of H/L, and THE MYRIAD's lowest box hangs .08 or more above the ground the other four stand on",
       tw && tw[1].HL <= tw[0].HL - .08 && tw[2].lo >= .08 && tw[0].lo < .04 && tw[1].lo < .04,
       tw && `H/L ${tw[0].HL} > ${tw[1].HL} > ${tw[2].HL}, lowest box ${tw.map(s => s.lo).join(" > ")}`);
    const left = Object.keys(r).filter(id => !DONE.includes(id) && pairs(r[id]).some(p => p.d < .12));
    if (left.length) console.log("   still one plan at three scales: " + left.map(id => `${id} d ${pairs(r[id]).map(p => p.d).join("/")}`).join(", "));
  }

  console.log("\n=== 38. THE HATCHLING IS NOT A SMALL ADULT ===");
  {
    // Section 37 holds the TOP of a line to a new shape. This is the bottom of
    // the same complaint, and it is the half the player actually starts every
    // run in: a hatchling that is its adult at a smaller scale is no more of
    // an evolution than an apex that is its adult at a larger one. Measured
    // the same way, on stages 0, 1 and 2. The stone line was the worst of the
    // nine - .02 of shape change from SHALEBACK to ANKYLOS, one ceratopsian at
    // three zooms - and the list grows by a line a round the way 37's did.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const out = {};
      for (const id of g.chars()) {
        const row = [];
        for (const st of [0, 1, 2]) {
          g.wipeSave(); g.start(id); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
          g.drainPicks(true); g.setShake(0); g.place(0, 0); g.aim(0);
          if (st) g.evolveTo(st);
          g.step(300, 1/60);
          g.resume(); g.capturePos();
          await frame(); await frame();
          const b = g.posOut();
          if (!b) { row.push({ st, nm: g.stageNm(), n: 0 }); continue; }
          const n = b.length / 6;
          let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9];
          for (let i = 0; i < n; i++) {                 // r f y hx hz hy
            const c = [b[i*6], b[i*6+1], b[i*6+2]], h = [b[i*6+3], b[i*6+4], b[i*6+5]];
            for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], c[k]-h[k]); mx[k] = Math.max(mx[k], c[k]+h[k]); }
          }
          const W = mx[0]-mn[0], L = mx[1]-mn[1], H = mx[2]-mn[2];
          row.push({ st, nm: g.stageNm(), n, HL: +(H/L).toFixed(2), WL: +(W/L).toFixed(2), lo: +mn[2].toFixed(2) });
        }
        out[id] = row;
      }
      return out;
    });
    const EARLY = ["ox", "surge", "accnt", "twin", "scrap"];   // and that is all nine
    const dist = (a, b) => +(Math.abs(a.HL - b.HL) + Math.abs(a.WL - b.WL)).toFixed(2);
    const pairs = row => [[0,1],[1,2],[0,2]].map(([i,j]) => dist(row[i], row[j]));
    const line = id => r[id].map(s => `${s.nm} ${s.HL}/${s.WL}`).join(" > ") + `  d ${pairs(r[id]).join("/")}`;
    ok(`the redesigned lines (${EARLY.join(", ")}) are three different animals before they are grown, not one at three scales: |dH/L| + |dW/L| of .12 or better between each pair of stages 0, 1 and 2`,
       EARLY.every(id => r[id] && r[id].length === 3 && pairs(r[id]).every(d => d >= .12)),
       EARLY.map(id => `${id}: ${line(id)}`).join(" | "));
    // and by name, because "different numbers" is not the same claim as "a
    // pebble, then a tail with legs on it, then a tank"
    const s0 = r.ox && r.ox[0], s1 = r.ox && r.ox[1], s2 = r.ox && r.ox[2];
    ok("the stone line hatches as a pebble and grows its weapon first: SHALEBACK is nearly as wide as it is long, ANKYLOS is four times longer than it is wide, and TITANHIDE is neither",
       s0 && s0.WL >= .65 && s1 && s1.WL <= .30 && s2 && s2.WL > .45 && s2.WL < .70,
       s0 && `W/L ${s0.WL} > ${s1.WL} > ${s2.WL}, H/L ${s0.HL} > ${s1.HL} > ${s2.HL}`);
    const g0 = r.surge && r.surge[0], g1 = r.surge && r.surge[1], g2 = r.surge && r.surge[2];
    ok("the surge line is a fry, then a fish that walks on its fins, then a predator: RIVERKING is the only stage of the line standing taller than .7 of its own length, and both juveniles are half again as wide for their length as THE SPINE",
       g1 && g1.HL >= .70 && g0 && g0.HL < .70 && g2 && g2.HL < .70 && g0.WL >= .45 && g1.WL >= .45 && g2.WL <= .30,
       g0 && `H/L ${g0.HL} > ${g1.HL} > ${g2.HL}, W/L ${g0.WL} > ${g1.WL} > ${g2.WL}`);
    const a0 = r.accnt && r.accnt[0], a1 = r.accnt && r.accnt[1], a2 = r.accnt && r.accnt[2];
    ok("the gale line hatches straight into the air and then cannot use it: WYVERNET hangs a quarter of a unit clear of the ground the rest of the line stands on, and SKYREND is the one stage of the line standing taller than it is long",
       a0 && a0.lo >= .25 && a1 && a1.lo < .06 && a2 && a2.lo < .06 && a1.HL > 1 && a0.HL < 1 && a2.HL < 1,
       a0 && `lowest box ${a0.lo} > ${a1.lo} > ${a2.lo}, H/L ${a0.HL} > ${a1.HL} > ${a2.HL}`);
    const w0 = r.twin && r.twin[0], w1 = r.twin && r.twin[1], w2 = r.twin && r.twin[2];
    ok("the echo line hatches as a grub and grows its necks before its body: HYDRALING is the flattest thing in the line and TRIHYDRA stands nearly as tall as it is long, and both are wider for their length than THE HYDRA",
       w0 && w0.HL <= .48 && w1 && w1.HL >= .90 && w2 && w0.WL > w2.WL && w1.WL > w2.WL,
       w0 && `H/L ${w0.HL} > ${w1.HL} > ${w2.HL}, W/L ${w0.WL} > ${w1.WL} > ${w2.WL}`);
    const c0 = r.scrap && r.scrap[0], c1 = r.scrap && r.scrap[1], c2 = r.scrap && r.scrap[2];
    ok("the tide line is not out of the egg yet, and what comes out is a ribbon: SPAWNLING is a clutch as wide as it is long, TIDESERPENT is the flattest thing in the game at under .25 of its own length, and the LEVIATHAN is neither",
       c0 && c0.WL >= .65 && c1 && c1.HL <= .25 && c1.WL <= .30 && c2 && c2.WL > .45 && c2.HL > .40,
       c0 && `H/L ${c0.HL} > ${c1.HL} > ${c2.HL}, W/L ${c0.WL} > ${c1.WL} > ${c2.WL}`);
    const left = Object.keys(r).filter(id => !EARLY.includes(id) && pairs(r[id]).some(d => d < .12));
    if (left.length) console.log("   still one plan at three scales below the third stage: "
      + left.map(id => `${id} d ${pairs(r[id]).join("/")}`).join(", "));
  }

  console.log("\n=== 39. THE PORTRAIT FITS IN ITS CARD ===");
  {
    // The card portraits solve their own camera off the first frame's box
    // capture, and nothing has ever checked the answer - the section above
    // asks whether a portrait was painted, not whether the animal is INSIDE
    // it. The capture is (lateral, fore-aft, vertical) and the framing read it
    // as (lateral, vertical, fore-aft), so every camera in the roster was
    // solved against an animal's depth where it wanted its height. That is
    // survivable while a body is about as deep as it is tall and it clips the
    // head off the moment it is not, which is what a clutch of eggs with one
    // head out of the top of it is. Measure the painted pixels: the animal has
    // to clear the frame edge, and it still has to fill the card.
    await page.reload({ waitUntil: "load" });
    await page.waitForTimeout(600);
    const r = await page.evaluate(async () => {
      window.__g.unlockAll(); window.__g.menu();
      await new Promise(res => { let n = 0;
        const tick = () => (++n > 40 ? res() : requestAnimationFrame(tick));
        requestAnimationFrame(tick); });
      const out = [];
      for (const c of [...document.querySelectorAll(".ch")]) {
        const cv = c.querySelector("canvas.pv"); if (!cv) continue;
        const W = cv.width, H = cv.height;
        const d = cv.getContext("2d").getImageData(0, 0, W, H).data;
        let x0 = W, x1 = -1, y0 = H, y1 = -1, lit = 0, top = 0, side = 0;
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
          const i = (y*W + x)*4;
          // the clear colour is (11, 12, 14) and the ground splash under the
          // animal is only a little above it; 150 across the three channels is
          // the animal's own darkest lit face and nothing else
          if (d[i] + d[i+1] + d[i+2] > 150) {
            lit++;
            if (x < x0) x0 = x; if (x > x1) x1 = x;
            if (y < y0) y0 = y; if (y > y1) y1 = y;
            // HOW MUCH of the edge is lit, not whether any of it is: this line
            // throws sparks, and a lit pixel on the top row is a spark leaving
            // the frame far more often than it is a head being cut off. The
            // ambient effects are drawn outside the body capture on purpose, so
            // the camera does not and should not frame for them.
            if (y < 2) top++;
            if (x < 2 || x > W - 3) side++;
          }
        }
        out.push({ nm: (c.querySelector(".nm") || {}).textContent?.trim() || "?",
                   W, H, x0, x1, y0, y1, top, side, fill: +(lit/(W*H)).toFixed(3) });
      }
      return out;
    });
    // the BOTTOM edge is where the animal stands - a card is framed so the
    // feet are at the floor of it, and a clutch of eggs lying on the ground
    // touches that floor by construction. Top and sides are the ones that mean
    // something was cut off.
    // and the bar is a BAND of edge, not a pixel of it: a head cut off by the
    // top of a card lights a tenth of that row, a spark lights three pixels.
    const edge = r.filter(p => p.x1 < 0 || p.top > p.W * .04 || p.side > p.H * .04);
    ok("no card portrait is clipped by its own frame: every one of them clears the top and both sides",
       r.length >= 9 && edge.length === 0,
       edge.length ? edge.map(p => `${p.nm} ${p.top} lit on the top row, ${p.side} down the sides, of ${p.W}x${p.H}`).join(", ")
                   : `${r.length} portraits, worst edge ${Math.max(...r.map(p => Math.max(p.top, p.side)))} lit pixels`);
    ok("...and none of them is a speck in the middle of it either",
       r.length >= 9 && r.every(p => p.fill >= .06),
       r.map(p => `${p.nm} ${p.fill}`).join(", "));
    // AND THE NUMBERS IT SOLVED AGAINST ARE THE RIGHT ONES. Pixels alone let a
    // framing that measures the wrong axis pass on margin: widen the lip and a
    // camera solved against an animal's DEPTH still fits its height by luck.
    // So ask the solver what it measured and check it against the same box
    // capture the shape sections use.
    const fit = await page.evaluate(async () => {
      const g = window.__g;
      const fits = g.portraitFits(), out = [];
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      for (const f of fits) {
        g.wipeSave(); g.start(f.id); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.place(0, 0); g.aim(0);
        if (f.st) g.evolveTo(f.st);
        g.resume(); g.capturePos();
        await frame(); await frame();
        const b = g.posOut(); if (!b) continue;
        let mn = [1e9,1e9,1e9], mx = [-1e9,-1e9,-1e9];
        for (let i = 0; i < b.length; i += 6) {
          const c = [b[i], b[i+1], b[i+2]], h = [b[i+3], b[i+4], b[i+5]];
          for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], c[k]-h[k]); mx[k] = Math.max(mx[k], c[k]+h[k]); }
        }
        const S0 = 2.05;                     // the model scale the fit carries
        out.push({ id: f.id, halfH: f.halfH, wantH: +((mx[2]-mn[2])/2*S0).toFixed(3),
                   radF: f.radF, wantF: +((mx[1]-mn[1])/2*S0).toFixed(3) });
      }
      return out;
    });
    const off = fit.filter(p => Math.abs(p.halfH - p.wantH) > p.wantH * .25
                             || Math.abs(p.radF - p.wantF) > p.wantF * .25);
    ok("and the camera solved against the animal's height and depth, not against them the other way round",
       fit.length >= 9 && off.length === 0,
       off.length ? off.map(p => `${p.id} framed halfH ${p.halfH} for a body ${p.wantH} tall, radF ${p.radF} for ${p.wantF} deep`).join(", ")
                  : `${fit.length} cameras, worst error ${Math.max(...fit.map(p =>
                      Math.max(Math.abs(p.halfH-p.wantH)/p.wantH, Math.abs(p.radF-p.wantF)/p.wantF))).toFixed(3)}`);
  }

  console.log("\n=== 40. EVERY LINE MOVES AT ITS OWN PACE ===");
  {
    // Reported: "they seem to all be the same speed, there has to be factors
    // that encourage fun gameplay with movement speed". Measured before the
    // round: six of nine lines at 6.6 u/s at all five stages, the ox at 5.7
    // flat, the tide line at 7.25 flat, only the courier changing at an
    // evolution. This drives the animal itself - a held W on flat grass, no
    // hop chain, no boon, no water - and reads the ground it covers, so what
    // is held here is the speed the player feels and not a stat.
    const r = await page.evaluate(async () => {
      const g = window.__g, out = {};
      const key = (t, code) => dispatchEvent(new KeyboardEvent(t, { code }));
      const run = (id, st, prep) => {
        g.wipeSave(); g.start(id); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.place(0, 0); g.aim(0);
        if (st) g.evolveTo(st);
        if (prep) prep();
        g.step(30, 1/60); g.place(0, 0);
        key("keydown", "KeyW"); g.step(30, 1/60);
        const a = g.state(); g.step(90, 1/60); const b = g.state();
        key("keyup", "KeyW");
        return +(Math.hypot(b.x - a.x, b.z - a.z) / 1.5).toFixed(2);
      };
      for (const id of g.chars()) out[id] = [0,1,2,3,4].map(st => run(id, st));
      // the courier's surge, up against down, on the same body
      const up = run("surge", 2, () => { g.fillSurge(); g.step(2, 1/60); });
      const down = run("surge", 2);
      return { pace: out, up, down };
    });
    const all = Object.values(r.pace).flat();
    const line = id => `${id} ${r.pace[id].join("/")}`;
    ok("the roster spans a real range: the fastest form covers at least half again the ground of the slowest",
       Math.max(...all) / Math.min(...all) >= 1.55,
       `${Math.min(...all)} to ${Math.max(...all)} u/s, x${(Math.max(...all)/Math.min(...all)).toFixed(2)}`);
    const steps = id => r.pace[id].slice(1).map((v, i) => v / r.pace[id][i]);
    ok("every line changes pace at two or more of its four evolutions, by five percent or better",
       Object.keys(r.pace).every(id => steps(id).filter(k => Math.abs(k - 1) >= .05).length >= 2),
       Object.keys(r.pace).map(line).join(" | "));
    // A QUARTER is the bar, not a fifth: the fledgling becoming THE ROC is a
    // +22% step and that is the point of it - the moment the line becomes a
    // real flier should be felt in the hands. A step over a quarter would be
    // the thing that feels like a bug.
    ok("...and no single evolution is a jump: no step moves pace by more than a quarter",
       Object.keys(r.pace).every(id => steps(id).every(k => Math.abs(k - 1) <= .25)),
       Object.keys(r.pace).map(id => `${id} ${steps(id).map(k => ((k-1)*100).toFixed(0)+"%").join("/")}`).join(" | "));
    // the hatchling's own pace is applied from the first frame: three numbers
    // the design table says, read off the ground
    const near = (v, w) => Math.abs(v - w) <= w * .03;
    ok("the hatchling's own pace applies from the first frame of a run: THE INTERN 6.60, THE OX's pebble 5.45, THE TWIN's grub 5.54",
       near(r.pace.intern[0], 6.60) && near(r.pace.ox[0], 5.45) && near(r.pace.twin[0], 5.54),
       `intern ${r.pace.intern[0]}, ox ${r.pace.ox[0]}, twin ${r.pace.twin[0]}`);
    ok("the courier's surge is a burst of pace: x1.30 on the ground while it is up",
       r.up / r.down >= 1.24 && r.up / r.down <= 1.36,
       `${r.down} u/s down, ${r.up} up, x${(r.up/r.down).toFixed(3)}`);
  }

  console.log("\n=== 41. KILLS FEED PACE ===");
  {
    // The second half of the movement report. Section 40 gave every line a
    // pace of its own; this makes pace something a fight hands you. Each kill
    // fills a meter that bleeds away in a couple of seconds, and the meter is
    // speed - so cutting through a pack keeps you fast and circling it does
    // not. Held here on the ground covered, not on the number.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const key = (t, code) => dispatchEvent(new KeyboardEvent(t, { code }));
      const boot = () => { g.wipeSave(); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true);
                           g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.place(0, 0); g.aim(0); };
      const pace = () => { g.place(0, 0); key("keydown", "KeyW"); g.step(20, 1/60);
                           const a = g.state(); g.step(60, 1/60); const b = g.state();
                           key("keyup", "KeyW"); return +(Math.hypot(b.x-a.x, b.z-a.z)).toFixed(2); };
      boot(); g.step(30, 1/60);
      const cold = g.rule().rush, coldPace = pace();
      // three kills, read at once
      boot(); g.spawn("runner", 3, 8); g.step(1, 1/60);
      const slain = g.slay(3); const afterKills = g.rule();
      // a fourth: does the meter keep climbing, and does it cap
      g.spawn("runner", 12, 8); g.step(1, 1/60); g.slay(12); const capped = g.rule();
      const hotPace = pace();
      // and it bleeds: no kills for three seconds
      g.step(180, 1/60); const later = g.rule();
      // an elite is worth two kills (a brute is a SPECIES; an elite is the
      // promotion an angry den hands out, and the hook promotes on demand)
      boot(); g.spawn("runner", 1, 8); g.step(1, 1/60); g.elite(0); g.slay(1); const elite = g.rule();
      return { cold, coldPace, slain, afterKills, capped, hotPace, later, elite };
    });
    ok("a run starts with no rush and a kill gives you some", r.cold === 0 && r.slain >= 3 && r.afterKills.rush > .30,
       `cold ${r.cold}, after three kills ${r.afterKills.rush} (x${r.afterKills.rushMul})`);
    ok("...and it caps: a dozen more kills take the meter to full and no further", r.capped.rush <= 1 && r.capped.rush >= .95,
       `after fifteen ${r.capped.rush} (x${r.capped.rushMul})`);
    ok("a full rush is pace on the ground: a fifth again the distance in the same second",
       r.hotPace / r.coldPace >= 1.10 && r.hotPace / r.coldPace <= 1.24,
       `${r.coldPace} cold, ${r.hotPace} hot, x${(r.hotPace/r.coldPace).toFixed(3)} (the meter bled during the read)`);
    ok("and it bleeds away: three seconds without a kill and it is gone", r.later.rush === 0 && r.later.rushMul === 1,
       `${r.later.rush} after 3 s`);
    ok("an elite is worth two kills", r.elite.rush >= .27 && r.elite.rush <= .29, `elite ${r.elite.rush}`);
  }

  console.log("\n=== 42. THE LEGS GO WITH IT ===");
  {
    // R200 made the horde fall: squash, shear the way it was hit, lie, sink.
    // What it did not do is anything to the legs - the whole-body squash
    // folded them exactly as far as it folded the head, so a dead brute lay
    // there with four straight legs still under it, a toy knocked over. The
    // shared leg helper now reads the same fall clock the squash does: the
    // knee buckles forward, the foot slides out ahead and drops flat, and the
    // legs splay to their own side.
    // MEASURED ON THE LEG BOXES' CENTRES, not on the footprint. The first
    // version of this read the whole corpse's width and passed with the splay
    // switched off, because the squash widens every box about its centre and
    // a brute's legs never reach past its own frill anyway. A squash moves an
    // extent and never a centre; only the splay moves a leg's centre sideways.
    const r = await page.evaluate(async () => {
      const g = window.__g, frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const out = {};
      for (const kind of ["brute", "shambler", "runner"]) {
        g.wipeSave(); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.place(0, 0); g.aim(0); g.clearEnemies();
        g.spawnAt(kind, 0, 6); g.step(2, 1/60);            // it faces the player: lateral is x
        g.slay(1); g.pause();
        const cap = async u => { while ((g.corpses()[0] || { u: 9 }).u < u) g.corpseStep(1, 1/60);
          g.captureCorpse(); g.resume(); await frame(); await frame(); g.pause();
          const c = g.corpseBox(), boxes = [];
          for (let i = 0; i < c.n; i++) { const o = g.corpseBox(i); boxes.push({ x: o.ax, y: o.ay }); }
          return { u: g.corpses()[0].u, c, boxes }; };
        const a = await cap(0);
        // the legs: whatever sat in the lowest third of the standing body
        const lim = a.c.minY + (a.c.maxY - a.c.minY) * .33;
        const legs = a.boxes.map((b, i) => b.y < lim ? i : -1).filter(i => i >= 0);
        const spread = s => { const xs = legs.map(i => s.boxes[i].x); return +(Math.max(...xs) - Math.min(...xs)).toFixed(3); };
        const s0 = spread(a);
        const b = await cap(.62);
        out[kind] = { legs: legs.length, s0, s62: spread(b), ratio: +(spread(b) / s0).toFixed(3), n0: a.c.n, n62: b.c.n };
      }
      return out;
    });
    ok("a dead brute's legs go out from under it: the centres of its leg boxes spread a quarter wider across the facing between the kill frame and the end of the crumple, and a shambler's too",
       r.brute.legs >= 4 && r.brute.ratio >= 1.25 && r.shambler.legs >= 4 && r.shambler.ratio >= 1.25,
       `brute ${r.brute.legs} leg boxes ${r.brute.s0} -> ${r.brute.s62} (x${r.brute.ratio}), shambler ${r.shambler.legs} boxes ${r.shambler.s0} -> ${r.shambler.s62} (x${r.shambler.ratio})`);
    ok("...and a runner's, by a fifth at least", r.runner.legs >= 4 && r.runner.ratio >= 1.20,
       `runner ${r.runner.legs} leg boxes ${r.runner.s0} -> ${r.runner.s62} (x${r.runner.ratio})`);
    ok("the splay adds no boxes and loses none: the corpse is the same count of parts at the end of the crumple as on the kill frame",
       Object.values(r).every(k => k.n0 === k.n62 && k.n0 > 10),
       Object.entries(r).map(([k, v]) => `${k} ${v.n0}/${v.n62}`).join(", "));
  }

  console.log("\n=== 43. THE GROUND KNOWS WHO IS AIRBORNE ===");
  {
    // The third movement factor. The tarpits slow the ground 14% and the
    // glacier takes the grip off it, and before this round they did it to a
    // hovering kite and a storm funnel as readily as to a walker. Stages
    // flagged air:true - and a dragon with its wings out - are not on the
    // ground: the tar cannot drag them, the ice cannot slip under them, and
    // the fledgling SKYREND is the one stage of the gale line still caught.
    // Every start rolls a new arena, so the cell is looked up after each boot.
    const r = await page.evaluate(async () => {
      const g = window.__g, key = (t, c) => dispatchEvent(new KeyboardEvent(t, { code: c }));
      const boot = (id, st) => { g.wipeSave(); g.start(id); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.aim(0); if (st) g.evolveTo(st); g.step(30, 1/60); };
      const at = kind => g.world().cells.find(c => c.id === kind);
      // TWO LEGS OF 45 FRAMES FROM THE CELL'S CENTRE, not one of 90: a second
      // and a half of walking is ten units, which walks straight out of a small
      // cell into whatever is next to it (one run in three read THE INTERN at
      // 4.4 on "bog" after crossing water). Each leg starts at the centre, and a
      // cell either leg leaves is thrown away for the next cell of its kind.
      const pace = (id, st, kind) => { boot(id, st);
        for (const c of g.world().cells.filter(c => c.id === kind).slice(0, 4)) {
          let d = 0, stayed = true;
          for (let leg = 0; leg < 2; leg++) {
            g.place(c.x, c.z); g.step(20, 1/60); g.place(c.x, c.z);
            key("keydown", "KeyW"); g.step(30, 1/60); const a = g.state(); g.step(22, 1/60); const m = g.state(); g.step(23, 1/60); const b = g.state(); key("keyup", "KeyW");
            d += Math.hypot(b.x - a.x, b.z - a.z);
            // and no water on the way: THE TARPITS can hold a pool, and tar times
            // water is x.64, which read as a walker dragged twice (one run in four)
            for (const q of [a, m, b]) if (g.biomeAt(q.x, q.z).id !== kind || g.inWater(q.x, q.z)) stayed = false;
          }
          if (stayed) return { ups: +(d / 1.5).toFixed(2), on: kind };
        }
        return null; };
      // how far it carries on after the key comes up: grip
      const coast = (id, st, kind) => { boot(id, st); const c = at(kind); if (!c) return null;
        g.place(c.x, c.z); g.step(20, 1/60); g.place(c.x, c.z);
        key("keydown", "KeyW"); g.step(30, 1/60); key("keyup", "KeyW"); const a = g.state(); g.step(40, 1/60); const b = g.state();
        return +Math.hypot(b.x - a.x, b.z - a.z).toFixed(2); };
      // the announcement, on the first step in
      const said = (id, st, kind) => { boot(id, st); const c = at(kind); if (!c) return null;
        const g0 = at("grass"); g.place(g0.x, g0.z); g.step(5, 1/60); g.place(c.x, c.z); g.step(5, 1/60);
        return g.alerts().filter(a => /TARPITS|GLACIER/.test(a)); };
      const forms = { intern: ["intern", 0], skyrend: ["accnt", 1], kite: ["accnt", 0], roc: ["accnt", 2], hurricane: ["accnt", 3],
                      myriad: ["twin", 4], supernova: ["intern", 4], continent: ["ox", 4] };
      const out = {};
      for (const [k, [id, st]] of Object.entries(forms)) out[k] = { grass: pace(id, st, "grass"), bog: pace(id, st, "bog") };
      return { out, coastIntern: [coast("intern", 0, "grass"), coast("intern", 0, "ice")], coastKite: [coast("accnt", 0, "grass"), coast("accnt", 0, "ice")],
               saidWalker: said("intern", 0, "bog"), saidKite: said("accnt", 0, "bog"), saidIce: said("intern", 0, "ice") };
    });
    const ratio = k => r.out[k].bog && r.out[k].grass ? +(r.out[k].bog.ups / r.out[k].grass.ups).toFixed(3) : null;
    const line = k => `${k} ${r.out[k].grass && r.out[k].grass.ups}->${r.out[k].bog && r.out[k].bog.ups} (x${ratio(k)}, on ${r.out[k].bog && r.out[k].bog.on})`;
    ok("the tar still drags a walker, and the fledgling with it: THE INTERN and SKYREND lose about a seventh of their pace in THE TARPITS",
       ratio("intern") !== null && ratio("intern") >= .80 && ratio("intern") <= .92 && ratio("skyrend") >= .80 && ratio("skyrend") <= .92,
       [line("intern"), line("skyrend")].join(", "));
    const AIR = ["kite", "roc", "hurricane", "myriad", "supernova", "continent"];
    ok("...and it cannot reach what is not on it: the kite, the ROC, the HURRICANE, the MYRIAD, the SUPERNOVA and the CONTINENT cross the tar at their grass pace",
       AIR.every(k => ratio(k) !== null && ratio(k) >= .96 && ratio(k) <= 1.04),
       AIR.map(line).join(", "));
    ok("the glacier takes a walker's grip and not a flier's: THE INTERN coasts three times as far on ice after the key comes up, the kite does not",
       r.coastIntern[1] >= r.coastIntern[0] * 3 && r.coastKite[1] <= r.coastKite[0] * 1.5,
       `intern ${r.coastIntern[0]} -> ${r.coastIntern[1]} on ice, kite ${r.coastKite[0]} -> ${r.coastKite[1]}`);
    ok("and the ground is announced, the way the water was: the first step into the tar says what it does, in one line for a walker and another for a flier, and the ice too",
       r.saidWalker && r.saidWalker.some(a => /DRAGS/.test(a)) && r.saidKite && r.saidKite.some(a => /ABOVE/.test(a)) && r.saidIce && r.saidIce.some(a => /GLACIER/.test(a)),
       `walker: ${JSON.stringify(r.saidWalker)}, kite: ${JSON.stringify(r.saidKite)}, ice: ${JSON.stringify(r.saidIce)}`);
  }

  console.log("\n=== 44. THE DRAFT READS IN ONE GLANCE ===");
  {
    // The upgrade remodel. The report was that the upgrades were boring and
    // unreadable: eight passives written as stat soup at nine pixels, and a
    // rank-up card that carried the same blurb as the card you took at rank
    // one. Now every upgrade is one adjective and one headline number, every
    // card carries its rank as pips, a weapon rank-up says what the next rank
    // changes (read off its own table, not written), and the evolution rule -
    // which partner a weapon needs - is printed on both halves of the pair.
    const EVO = { bat:"MEGABONK", skulls:"CAROUSEL", bolt:"BOLTSTORM", pulse:"EARTHQUAKE",
                  mortar:"SKYFALL", zap:"THUNDERHEAD", aura:"PLAGUE", gore:"STAMPEDE",
                  caltrops:"SCORCHED EARTH", brood:"THE PACK" };
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const deal = () => { g.drainPicks(false); g.xp(600); g.step(1, 1/60);
        if (!g.state().picking) return [];                // no level, no hand
        const cards = [...document.querySelectorAll("#pkCards .card")].map(c => ({
          nm: c.querySelector(".nm").textContent, lv: c.querySelector(".lv span").textContent,
          eff: c.querySelector(".eff").textContent, ds: c.querySelector(".ds").textContent,
          pt: (c.querySelector(".pt") || {}).textContent || "",
          pips: c.querySelectorAll(".pips s").length, filled: c.querySelectorAll(".pips s.f").length,
          next: c.querySelectorAll(".pips s.n").length, type: c.dataset.otype, key: c.dataset.okey }));
        g.drainPicks(true); return cards; };
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true);
      const fresh = []; for (let i = 0; i < 6; i++) fresh.push(...deal());
      // a full kit, so the pool is nothing but rank-ups and every one of them
      // is dealt inside forty hands - ten hands with new cards in the pool
      // left MORE undealt one run in five
      for (const k of ["bolt", "zap", "skulls", "dupe", "spinach", "tempo", "clover", "magnet"]) g.give(k, 1);
      const mid = []; for (let i = 0; i < 40; i++) mid.push(...deal());
      g.give("bat", 3); g.give("spinach", 3);
      const evo = deal();
      return { fresh, mid, evo, ups: g.upgrades(), kit: g.kit(),
               delta: { bat: g.wDelta("bat", 0), zap: g.wDelta("zap", 0), bolt: g.wDelta("bolt", 1),
                        skulls: g.wDelta("skulls", 0), max: g.wDelta("bat", 2) } };
    });
    const all = [...r.fresh, ...r.mid, ...r.evo];
    ok("every upgrade is a part of the animal and one headline: eight of them, two words each, a signed number or a count on the face",
       r.ups.length === 8 && r.ups.every(u => /^[A-Z]+ [A-Z]+$/.test(u.nm)) &&
       r.ups.every(u => [].concat(u.eff).every(e => /^[+-]\d/.test(e))),
       r.ups.map(u => `${u.nm}=${[].concat(u.eff)[0]}`).join(" "));
    ok("every card dealt has a headline and three pips, with the rank you would gain lit",
       all.length >= 30 && all.every(c => c.eff.length > 0) &&
       all.filter(c => c.type !== "heal" && c.lv !== "RULE").every(c => c.pips === 3 && (c.type === "evo" ? c.filled === 3 : c.next === 1)),
       `${all.length} cards, blank headlines ${all.filter(c => !c.eff).length}, pipless ${all.filter(c => c.type !== "heal" && c.lv !== "RULE" && c.pips !== 3).length}`);
    const rank = r.mid.filter(c => c.type === "up" && EVO[c.key]);
    ok("a weapon rank-up says what the next rank changes, in numbers, and does not repeat the weapon's blurb",
       rank.length >= 3 && rank.every(c => /^\+\d+% DMG/.test(c.eff) && c.ds === "" && c.filled >= 1),
       rank.slice(0, 4).map(c => `${c.nm}: ${c.eff}`).join(" | "));
    const wcards = all.filter(c => EVO[c.key] && c.type !== "evo");
    ok("every weapon card names the evolution it is walking toward and the partner it needs",
       wcards.length >= 10 && wcards.every(c => c.pt.startsWith(EVO[c.key] + " · WITH ")),
       wcards.filter(c => !c.pt.startsWith(EVO[c.key] + " · WITH ")).map(c => `${c.nm}: ${c.pt}`).join(" | ") || "all named");
    const more = r.mid.filter(c => c.key === "dupe");
    ok("and the partner's card names what it unlocks: MORE, in a kit with BOLT, says BOLTSTORM",
       more.length >= 1 && more.every(c => /UNLOCKS .*BOLTSTORM/.test(c.pt)),
       more.map(c => c.pt).join(" | ") || "MORE never dealt");
    const mega = r.evo.find(c => c.type === "evo");
    ok("the evolution card reads EVOLVED with the bar full",
       mega && mega.nm === "MEGABONK" && mega.eff === "EVOLVED" && mega.filled === 3,
       mega ? `${mega.nm} ${mega.eff} ${mega.filled}/3` : "no evolution dealt");
    ok("the delta is read off the table: BONK BAT's next rank is more damage, bigger and faster; ZAP gains jumps; BOLT gains pierce; a maxed weapon says so",
       /\+\d+% DMG/.test(r.delta.bat) && /BIGGER/.test(r.delta.bat) && /FASTER/.test(r.delta.bat) &&
       /JUMP/.test(r.delta.zap) && /PIERCE/.test(r.delta.bolt) && /SKULL/.test(r.delta.skulls) && r.delta.max === "MAXED",
       JSON.stringify(r.delta));
  }

  console.log("\n=== 45. THE RULES ===");
  {
    // The fun half of the upgrade report. Four cards that change how a run
    // plays: RHYTHM (key momentum) makes the hop chain pay in damage, STOMP makes every
    // landing a blast, BLOODTHIRST makes kills heal, HUNTER makes bosses and
    // elites take half again. Each is measured through the real pipeline
    // with the rule off and then on, on the same field.
    const r = await page.evaluate(async () => {
      const g = window.__g, key = (t, c) => dispatchEvent(new KeyboardEvent(t, { code: c }));
      const boot = () => { g.wipeSave(); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.step(5, 1/60); };
      const out = {};
      // RHYTHM
      boot(); g.setHop(8); out.momOff = g.dmgOut(100); g.give("momentum", 1); out.momOn = g.dmgOut(100);
      g.setHop(0); out.momIdle = g.dmgOut(100);
      // HUNTER: a grunt and an elite, same hit
      const lost = (i, n) => { const h0 = g.hordeHp(); g.hurtAt(i, n); return +(h0 - g.hordeHp()).toFixed(2); };
      boot(); g.spawn("brute", 2, 3); g.elite(1);
      out.huntOff = [lost(0, 50), lost(1, 50)];
      g.give("hunter", 1); out.huntOn = [lost(0, 50), lost(1, 50)];
      // BLOODTHIRST
      boot(); g.spawn("shambler", 10, 3); g.setHp(40); g.slay(10); out.bloodOff = g.state().hp;
      boot(); g.spawn("shambler", 10, 3); g.setHp(40); g.give("bloodthirst", 1); g.slay(10); out.bloodOn = g.state().hp;
      // STOMP: jump once over a ring of grubs, land, and count what it cost them
      const hop = () => { const hp0 = g.hordeHp(); key("keydown", "Space"); g.step(2, 1/60); key("keyup", "Space");
        let landed = false; for (let i = 0; i < 90 && !landed; i++) { g.step(1, 1/60); landed = !g.state().air; }
        return { landed, lost: +(hp0 - g.hordeHp()).toFixed(1) }; };
      boot(); g.spawn("shambler", 8, 2); g.step(3, 1/60); out.stompOff = hop();
      boot(); g.spawn("shambler", 8, 2); g.step(3, 1/60); g.give("stomp", 1); out.stompOn = hop();
      // and what the shove is FOR: twenty seconds hopping in place inside a ring
      // of forty, weapons off, with the card and without. Benched with the
      // autopilot STOMP was a tenth of a percent of a run, because the autopilot
      // kites at weapon range and nothing was ever inside seven metres of a
      // landing; a player with the horde on their heels is the case that counts.
      const brawl = (rule) => { g.wipeSave(); g.pin(7); g.pinRun(7); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.step(5, 1/60);
        if (rule) g.give(rule, 1); g.spawn("shambler", 30, 6); g.spawn("runner", 10, 8); g.step(10, 1/60);
        const hp0 = g.state().hp;
        for (let i = 0; i < 20 * 60; i++) { if (!g.state().air) { key("keydown", "Space"); g.step(1, 1/60); key("keyup", "Space"); } else g.step(1, 1/60); }
        const s = g.stompDmg(); return { lost: Math.round(hp0 - g.state().hp), hits: s.hit, left: g.hordeHp() }; };
      out.brawlOff = brawl(null); out.brawlOn = brawl("stomp");
      // the draft: rules arrive at level 4 as their own kind of card, and two is the cap
      // each hand is tagged with the level it was dealt AT - a 600 xp step is
      // one level early on and several later, so the level is read, not counted
      const deal = (xp = 600) => { g.drainPicks(false); g.xp(xp); g.step(1, 1/60); const st = g.state(), lvl = st.lvl;
        // past level sixty a 600 xp step does not always level: an unopened
        // draft leaves the previous hand in the DOM, hidden, and it must not count
        if (!st.picking) return [];
        const c = [...document.querySelectorAll("#pkCards .card")].map(e => ({ nm: e.querySelector(".nm").textContent,
          lv: e.querySelector(".lv span").textContent, rule: e.classList.contains("rule"), key: e.dataset.okey, lvl }));
        g.drainPicks(true); return c; };
      boot(); for (const k of ["bolt", "zap", "skulls", "dupe", "spinach", "tempo", "clover", "magnet"]) g.give(k, 1);
      const hands = []; for (let i = 0; i < 12; i++) hands.push(...deal(40));     // one level at a time
      for (let i = 0; i < 40; i++) hands.push(...deal());
      const early = hands.filter(c => c.lvl < 4), later = hands.filter(c => c.lvl >= 4);
      g.give("momentum", 1); g.give("hunter", 1); g.give("stomp", 1);       // three: the level is past 30 by now
      const capped = []; for (let i = 0; i < 30; i++) capped.push(...deal(2500));
      out.earlyHands = early.length; out.early = early.filter(c => c.rule).length; out.later = later.filter(c => c.rule);
      out.capped = capped.filter(c => c.rule).length; out.lvl = g.state().lvl;
      g.setHop(5);                                        // a live chain, with RHYTHM held
      await new Promise(res => setTimeout(res, 250));      // the kit bar redraws on the frame loop
      out.slot = !!document.querySelector("#kit .slot.r"); out.rules = g.rules();
      out.hopLabel = document.querySelector("#hop em").textContent;
      out.pCount = g.kit().length;
      return out;
    });
    ok("RHYTHM: an eight-link chain multiplies a hit by the chain's own bonus, and does nothing on the ground",
       Math.abs(r.momOn / r.momOff - (1 + .60 * (1 - Math.pow(.80, 8)))) < .01 && Math.abs(r.momIdle - r.momOff) < .01,
       `x${(r.momOn / r.momOff).toFixed(3)} at eight links, x${(r.momIdle / r.momOff).toFixed(3)} idle`);
    ok("HUNTER: the elite takes half again, the grunt beside it takes what it took before",
       Math.abs(r.huntOn[1] / r.huntOff[1] - 1.5) < .02 && Math.abs(r.huntOn[0] - r.huntOff[0]) < .01,
       `grunt ${r.huntOff[0]} -> ${r.huntOn[0]}, elite ${r.huntOff[1]} -> ${r.huntOn[1]}`);
    ok("BLOODTHIRST: ten kills are ten health, and none without it",
       r.bloodOff === 40 && r.bloodOn === 50, `${r.bloodOff} without, ${r.bloodOn} with`);
    ok("STOMP: one landing in a ring of grubs costs them health, and a bare landing costs nothing",
       r.stompOff.landed && r.stompOn.landed && r.stompOff.lost === 0 && r.stompOn.lost > 30,
       `without ${JSON.stringify(r.stompOff)}, with ${JSON.stringify(r.stompOn)}`);
    ok("and the shove is what it is for: twenty seconds hopping inside a ring of forty costs real health bare, and next to nothing with the card",
       r.brawlOff.lost > 60 && r.brawlOn.lost < r.brawlOff.lost * .25 && r.brawlOn.hits >= 3,
       `bare: lost ${r.brawlOff.lost}, ${r.brawlOff.left} HP of horde left; STOMP: lost ${r.brawlOn.lost}, ${r.brawlOn.hits} landings connected, ${r.brawlOn.left} HP left`);
    ok("the draft deals rules as their own kind of card from level 4, all six of them, none before",
       r.earlyHands >= 4 && r.early === 0 && r.later.length >= 6 && new Set(r.later.map(c => c.key)).size === 6 &&
       r.later.every(c => c.lv === "RULE" && c.rule),
       `${r.early} of ${r.earlyHands} cards before level 4, ${r.later.length} after (${[...new Set(r.later.map(c => c.nm))].join(" ")}), level ${r.lvl}`);
    ok("the slots cap the rules: with three taken past level 30 the draft offers no fourth, and a rule sits in the kit bar in its own colour",
       r.capped === 0 && r.slot && r.rules.length === 6 && r.lvl >= 30, `${r.capped} offered past the cap, slot ${r.slot}, level ${r.lvl}`);
    ok("and the chain readout says the chain is paying twice while RHYTHM is held",
       /x\d/.test(r.hopLabel) && /PACE & DMG/.test(r.hopLabel), JSON.stringify(r.hopLabel));
  }

  console.log("\n=== 46. MORE IS FOR EVERY WEAPON ===");
  {
    // MORE used to touch five weapons and say so in nine-pixel type. The four
    // weapons with no shot count now ECHO - the same fire again a beat later
    // at copy damage, once per copy - and STINK leaves copies of its cloud
    // behind you. Each is counted with the card at rank 3 and without, same
    // seed, same ring of grubs, walking so that GORE fires and the trail exists.
    const r = await page.evaluate(async () => {
      const g = window.__g, key = (t, c) => dispatchEvent(new KeyboardEvent(t, { code: c }));
      const count = (w, more, secs, ring, kind = "shambler") => {
        g.wipeSave(); g.pin(5); g.pinRun(5); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.give(w, 1);
        if (more) g.give("dupe", 3); g.spawn(kind, 24, ring); g.step(5, 1/60);
        const c0 = g.fxCounts(), h0 = g.hordeHp();
        key("keydown", "KeyW"); g.step(secs * 60, 1/60); key("keyup", "KeyW");
        const c1 = g.fxCounts();
        return { swings: c1.swings - c0.swings, rings: c1.rings - c0.rings, zones: c1.zones - c0.zones,
                 lanes: c1.lanes - c0.lanes, echoes: c1.echoes - c0.echoes, lost: Math.round(h0 - g.hordeHp()) };
      };
      const pair = (w, secs, ring, kind) => [count(w, false, secs, ring, kind), count(w, true, secs, ring, kind)];
      // the trail needs animals that outlive the base cloud: a ring of grubs at
      // five metres is dead inside a second, before there is a trail to walk
      // them through. Ceratops at four metres are left behind at 1.9 u/s and
      // spend the next seconds in the copies.
      // BROOD's copy pups bite at copy damage like every other copy: one pup
      // and four on THORNBACK for eight seconds, standing still, no shoving
      // the target out of reach (a boss barely moves). Full-damage copies
      // would read x4; at 55% the pack reads about x2.65.
      // Summed over three seeds, because a pack fight is chaotic: on one seed
      // two pups did less than one (they jostle for the same flank). The sum
      // reads x1.8 with copies at 55% and x2.4 with them at full.
      const pack = (more, seed) => { g.wipeSave(); g.pin(seed); g.pinRun(seed); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.give("brood", 1);
        if (more) g.give("dupe", 3); g.boss(1); g.step(90, 1/60); g.dmg(); g.step(8 * 60, 1/60); return Math.round(g.dmg().boss); };
      let packOff = 0, packOn = 0;
      for (const seed of [5, 6, 7]) { packOff += pack(false, seed); packOn += pack(true, seed); }
      return { bat: pair("bat", 4, 4), pulse: pair("pulse", 4, 6), caltrops: pair("caltrops", 4, 6),
               gore: pair("gore", 4, 6), aura: pair("aura", 6, 4, "brute"), pack: [packOff, packOn],
               more: g.upgrades().find(u => u.key === "dupe") };
    });
    const x = (a, f) => (a[1][f] / Math.max(1, a[0][f])).toFixed(1);
    ok("BONK BAT swings a flurry: at least three times the swings with MORE 3, the extras counted as echoes",
       r.bat[1].swings >= r.bat[0].swings * 3 && r.bat[1].echoes > 0 && r.bat[0].echoes === 0,
       `${r.bat[0].swings} -> ${r.bat[1].swings} swings (x${x(r.bat, "swings")}), ${r.bat[1].echoes} echoes`);
    ok("PULSE rings again and again", r.pulse[1].rings >= r.pulse[0].rings * 3,
       `${r.pulse[0].rings} -> ${r.pulse[1].rings} rings (x${x(r.pulse, "rings")})`);
    ok("CALTROPS drops a denser trail", r.caltrops[1].zones >= r.caltrops[0].zones * 3,
       `${r.caltrops[0].zones} -> ${r.caltrops[1].zones} zones (x${x(r.caltrops, "zones")})`);
    ok("GORE cuts more lanes while you move", r.gore[1].lanes >= r.gore[0].lanes * 3 && r.gore[0].lanes > 0,
       `${r.gore[0].lanes} -> ${r.gore[1].lanes} lanes (x${x(r.gore, "lanes")})`);
    ok("STINK's trailing clouds bite: walking away from a ring of ceratops costs them more with MORE than without",
       r.aura[1].lost > r.aura[0].lost * 1.25 && r.aura[0].lost > 0,
       `${r.aura[0].lost} -> ${r.aura[1].lost} horde HP (x${(r.aura[1].lost / Math.max(1, r.aura[0].lost)).toFixed(2)})`);
    ok("BROOD's copy pups bite at copy damage: four pups on a boss, over three seeds, do more than one pup and well short of four full ones",
       r.pack[0] > 0 && r.pack[1] > r.pack[0] * 1.3 && r.pack[1] < r.pack[0] * 2.1,
       `${r.pack[0]} -> ${r.pack[1]} boss damage over three seeds (x${(r.pack[1] / Math.max(1, r.pack[0])).toFixed(2)})`);
    ok("and the card says so, without a weapon list", r.more && !/BOLT/.test(String(r.more.eff)) && r.more.nm === "SECOND HEAD",
       JSON.stringify(r.more));
  }

  console.log("\n=== 47. THE BOSS IS THE TARGET ===");
  {
    // BONK BAT and BOLT aimed at the nearest body. With a grub two metres south
    // and TERRAVORE seven metres north, the swing and the shot went south. ZAP
    // already weighed a boss in reach above everything; the swing and the shot
    // read the same threatTarget() now. A north-facing aim is angle 0.
    const r = await page.evaluate(async () => {
      const g = window.__g, wrap = a => Math.atan2(Math.sin(a), Math.cos(a));
      const aim = (w) => { g.wipeSave(); g.pin(8); g.pinRun(8); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.aim(0); g.give(w, 1);
        g.boss(3); g.step(150, 1/60);                                        // let it rise
        g.bossTo(0, 7); g.clearShots();                                       // forget the swings before the move
        g.spawnAt("brute", 0, -2); g.step(2, 1/60);                           // the decoy arrives last, so it is alive
        const b = g.bossAt(); const st = g.state();
        const bossAng = b ? wrap(Math.atan2(b.x - st.x, b.z - st.z)) : null;
        const grubAng = Math.PI;
        // wait out the first cooldown and read where the next fire went
        for (let i = 0; i < 120; i++) { g.step(1, 1/60); const a = w === "bat" ? g.lastSwing() : g.lastBolt(); if (a !== null) return { w, aimed: wrap(a), bossAng, grubAng, bossDist: b ? Math.round(Math.hypot(b.x - st.x, b.z - st.z)) : null }; }
        return { w, aimed: null, bossAng, grubAng };
      };
      return { bat: aim("bat"), bolt: aim("bolt") };
    });
    const toward = (a, target) => a !== null && target !== null && Math.abs(Math.atan2(Math.sin(a - target), Math.cos(a - target))) < .5;
    ok("BONK BAT swings at the boss in reach, not at the grub at its feet",
       toward(r.bat.aimed, r.bat.bossAng) && !toward(r.bat.aimed, r.bat.grubAng), JSON.stringify(r.bat));
    ok("BOLT is loosed at the boss in reach, not at the grub at its feet",
       toward(r.bolt.aimed, r.bolt.bossAng) && !toward(r.bolt.aimed, r.bolt.grubAng), JSON.stringify(r.bolt));
  }

  console.log("\n=== 48. BOSSES ARE FIGHTS ===");
  {
    // The three mid-run bosses died in five to twenty-five seconds against the
    // benched veteran, twenty-six metres out. They rise fifteen metres away now
    // and carry health that grows with your level, capped at three times; the
    // finale, recalibrated against the ceiling on its own, does not grow.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const at = (lvl, i) => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies();
        for (let k = 0; k < 40000 && g.state().lvl < lvl; k++) g.xp(20);            // climb to the level, exactly
        g.drainPicks(true); g.boss(i); g.step(1, 1/60); const b = g.bossAt(), st = g.state();
        return { lvl: st.lvl, hp: b.hp, dist: +Math.hypot(b.x - st.x, b.z - st.z).toFixed(1), nm: b.nm }; };
      return { m1: at(1, 0), m10: at(10, 0), m25: at(25, 0), m60: at(60, 0), t1: at(1, 1), t60: at(3, 1), f1: at(1, 3), f60: at(60, 3) };
    });
    ok("THE MATRIARCH is the table's 3,800 for a hatchling at level 1", r.m1.hp === 3800 && r.m1.lvl === 1, `${r.m1.hp} at level ${r.m1.lvl}`);
    ok("and grows with the level you reached: about x1.45 at ten, x2.2 at twenty-five, and no more than x3 ever",
       r.m10.lvl >= 10 && Math.abs(r.m10.hp / 3800 - (1 + .05 * (r.m10.lvl - 1))) < .02 &&
       Math.abs(r.m25.hp / 3800 - (1 + .05 * (r.m25.lvl - 1))) < .02 && r.m60.hp === 3800 * 3,
       `lv${r.m10.lvl} ${r.m10.hp}, lv${r.m25.lvl} ${r.m25.hp}, lv${r.m60.lvl} ${r.m60.hp}`);
    ok("the finale does not grow with LEVEL - an empty kit meets its 520,000 floor at level 1 and at level 60 alike (it grows with the kit, section 49)",
       r.f1.hp === 520000 && r.f60.hp === 520000,
       `${r.f1.hp} at level ${r.f1.lvl}, ${r.f60.hp} at level ${r.f60.lvl}`);
    ok("every boss rises inside weapon range, fifteen metres out, not on the horizon",
       [r.m1, r.t1, r.f1].every(b => b.dist >= 12 && b.dist <= 16.5), [r.m1, r.t1, r.f1].map(b => `${b.nm} ${b.dist}m`).join(", "));
  }

  console.log("\n=== 49. A BOSS IS SECONDS OF YOU ===");
  {
    // The mid-run bosses are sized in seconds of what your kit would do to one
    // body - twenty for THE MATRIARCH, thirty for THORNBACK, forty for
    // SKYSPLITTER - never below the table times your level growth and never
    // above twelve times the table. The finale is sixty seconds of the last boss's rate, floored at 520,000.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const boot = () => { g.wipeSave(); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.step(3, 1/60); };
      const hpOf = (i, kit) => { boot(); for (const [k, n] of kit) g.give(k, n); const kd = g.kitDps(); g.boss(i);
        const b = g.bossAt(); const hp = b ? Math.round(b.hp) : null; g.clearEnemies(); return { hp, kd }; };
      const small = [["bat", 0]], big = [["bolt", 3], ["zap", 3], ["mortar", 3], ["spinach", 3], ["dupe", 3], ["clover", 3]];
      const huge = [...big, ["skulls", 3], ["tempo", 3], ["boots", 3], ["brood", 3], ["aura", 3], ["caltrops", 3]];
      // the finale reads what you did to the LAST boss: kill SKYSPLITTER a
      // second after it is up and the rate is its whole health a second
      const finalAfterKill = () => { boot(); for (const [k, n] of huge) g.give(k, n); g.boss(2); g.step(150, 1/60);
        const b2 = g.bossAt(); g.hitBoss(1e9); g.step(2, 1/60); const rate = g.bossRate(); g.boss(3);
        const b = g.bossAt(); const hp = b ? Math.round(b.hp) : null; g.clearEnemies();
        // and grown since, at a rate the cap does not hide: ten thousand a
        // second recorded, once with the kit as it is and once as if it had
        // been half the size at the kill
        g.setBossRate(10000); g.setBossKit(g.kitDps()); g.boss(3); const b3 = g.bossAt(); const hpSame = b3 ? Math.round(b3.hp) : null; g.clearEnemies();
        g.setBossKit(g.kitDps() / 2); g.boss(3); const b4 = g.bossAt(); const hpGrown = b4 ? Math.round(b4.hp) : null; g.clearEnemies();
        return { hp, hpSame, hpGrown, rate, sky: b2 ? Math.round(b2.hp) : null }; };
      return { fresh: [hpOf(0, []), hpOf(1, []), hpOf(2, [])], small: hpOf(0, small),
               big: [hpOf(0, big), hpOf(1, big), hpOf(2, big)], final: [hpOf(3, []), hpOf(3, huge)], finalKill: finalAfterKill() };
    });
    ok("an empty kit meets the table: 3,800 / 15,000 / 55,000",
       r.fresh.every(x => x.kd === 0) && r.fresh[0].hp === 3800 && r.fresh[1].hp === 15000 && r.fresh[2].hp === 55000,
       r.fresh.map(x => x.hp).join(" / "));
    ok("a bare BONK BAT is under forty a second and its MATRIARCH is still the table", r.small.kd > 20 && r.small.kd < 60 && r.small.hp === 3800,
       `${r.small.kd}/s -> ${r.small.hp}`);
    // the hook rounds the rate to a whole number, so the product is matched to a tenth of a percent
    const want = (i, kd, table) => Math.max(table, Math.min(table * 12, kd * [20, 30, 40][i]));
    const near = (hp, w) => Math.abs(hp - w) <= w * .001 + 1;
    ok("a big kit meets a boss sized in seconds of it, capped at twelve tables",
       r.big.every(x => x.kd > 500) && near(r.big[0].hp, want(0, r.big[0].kd, 3800)) &&
       near(r.big[1].hp, want(1, r.big[1].kd, 15000)) && near(r.big[2].hp, want(2, r.big[2].kd, 55000)),
       r.big.map((x, i) => `${x.kd}/s -> ${x.hp}`).join(" / "));
    ok("and it is bigger than the table by a lot", r.big[1].hp >= 15000 * 4 && r.big[2].hp >= 55000 * 2,
       `THORNBACK x${(r.big[1].hp / 15000).toFixed(1)}, SKYSPLITTER x${(r.big[2].hp / 55000).toFixed(1)}`);
    ok("the finale with no boss killed: never under 520,000, and a third of the estimate at most (the estimate is a ceiling)",
       r.final[0].hp === 520000 && near(r.final[1].hp, Math.max(520000, r.final[1].kd * 60 / 3)),
       `${r.final[0].hp} / ${r.final[1].kd}/s -> ${r.final[1].hp}`);
    ok("and after a boss kill it is sixty seconds of what you did to that boss: SKYSPLITTER killed in a second sizes it at its rate x60, capped",
       r.finalKill.rate > 0 && Math.abs(r.finalKill.rate / r.finalKill.sky - 1) < .15 && near(r.finalKill.hp, Math.min(1200000 * 12, r.finalKill.rate * 60)),
       `SKYSPLITTER ${r.finalKill.sky} in a second -> rate ${r.finalKill.rate}/s -> TERRAVORE ${r.finalKill.hp}`);
    ok("and scaled by how much the kit grew since the kill: ten thousand a second is 600,000 as it was and 1,200,000 for a kit twice the size",
       r.finalKill.hpSame === 600000 && near(r.finalKill.hpGrown, 1200000),
       `${r.finalKill.hpSame} same kit, ${r.finalKill.hpGrown} at twice the kit`);
  }

  console.log("\n=== 50. THE THIRD RULE ===");
  {
    // A run film found the kit complete by 8:00 and identical at 20:00. A
    // third rule slot opens at level 30, and two more rules exist to fill it:
    // AFTERBURN (rush fades at a third of the rate) and GLASS (+40% damage,
    // -40% max HP). Each is measured off then on; the slot is counted below
    // and above level 30 with two rules already held.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const boot = () => { g.wipeSave(); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.step(3, 1/60); };
      const fade = (rule) => { boot(); if (rule) g.give(rule, 1); g.spawn("shambler", 4, 3); g.slay(4); const r0 = g.rule().rush;
        g.step(60, 1/60); return { r0: +r0.toFixed(3), r1: +g.rule().rush.toFixed(3) }; };
      const out = { fadeOff: fade(null), fadeOn: fade("afterburn") };
      g.wipeSave(); g.start("intern"); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0);
      const s0 = g.state(); const d0 = s0.dps; g.give("glass", 1); const s1 = g.state();
      out.glass = { hp0: s0.maxhp, hp1: s1.maxhp, d0, d1: s1.dps };
      // the third slot: two rules held, deal below 30 and above
      const dealRules = (n, xp) => { let seen = 0; for (let i = 0; i < n; i++) { g.drainPicks(false); g.xp(xp); g.step(1, 1/60);
        if (g.state().picking) seen += document.querySelectorAll("#pkCards .card.rule").length; g.drainPicks(true); } return seen; };
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0);
      for (const k of ["bolt", "zap", "skulls", "dupe", "spinach", "tempo", "clover", "magnet", "momentum", "hunter"]) g.give(k, 1);
      out.below = dealRules(12, 40); out.lvlBelow = g.state().lvl;             // small steps: stays well under 30
      while (g.state().lvl < 30) { g.drainPicks(false); g.xp(600); g.step(1, 1/60); g.drainPicks(true); }
      out.above = dealRules(30, 600); out.lvlAbove = g.state().lvl; out.rules = g.rules().map(x => x.nm);
      return out;
    });
    ok("AFTERBURN: a second after four kills the rush has faded to about half bare, and barely at all with the card",
       r.fadeOff.r0 > .5 && r.fadeOff.r1 < r.fadeOff.r0 * .6 && r.fadeOn.r1 > r.fadeOn.r0 * .7,
       `bare ${r.fadeOff.r0} -> ${r.fadeOff.r1}, AFTERBURN ${r.fadeOn.r0} -> ${r.fadeOn.r1}`);
    ok("GLASS: +40% damage and -40% max HP the moment it is taken",
       Math.abs(r.glass.d1 / r.glass.d0 - 1.4) < .01 && Math.abs(r.glass.hp1 / r.glass.hp0 - .6) < .02,
       `dmg x${(r.glass.d1 / r.glass.d0).toFixed(2)}, hp ${r.glass.hp0} -> ${r.glass.hp1}`);
    ok("the third slot opens at level 30: with two rules held nothing green is dealt below it and rules are dealt above",
       r.lvlBelow < 30 && r.below === 0 && r.lvlAbove >= 30 && r.above > 0 && r.rules.length === 6,
       `level ${r.lvlBelow}: ${r.below} rule cards; level ${r.lvlAbove}: ${r.above}; ${r.rules.join(" ")}`);
  }

  console.log("\n=== 51. MASTERY ===");
  {
    // Past a full kit every fifth silent level deals three of the upgrades
    // you finished; the one you take goes a rank further, to five at most.
    // MORE never appears in one (its copies are one a rank by design).
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0);
      for (const k of ["bat","skulls","bolt","pulse","spinach","boots","tempo","magnet","plating","heart","dupe","clover","momentum","hunter","stomp"]) g.give(k, 3);
      for (const k of ["bat","skulls","bolt","pulse"]) g.evolve(k);
      g.drainPicks(false);
      const hands = [], gaps = []; let silentAt = g.mastery().silent, guard = 0;
      const ranksBefore = g.kit().join(" ");
      while (hands.length < 6 && guard++ < 400) {
        g.xp(60); g.step(1, 1/60);
        if (g.state().picking) {
          const cards = [...document.querySelectorAll("#pkCards .card")].map(c => ({ key: c.dataset.okey, lv: c.querySelector(".lv span").textContent,
            pips: c.querySelectorAll(".pips s").length, lit: c.querySelectorAll(".pips s.n").length, filled: c.querySelectorAll(".pips s.f").length }));
          // the line's own move arrives with an evolution and is a real draft, not a mastery: take it and carry on
          if (cards.every(c => c.lv === "MASTERY")) { hands.push(cards); gaps.push(g.mastery().silent - silentAt); silentAt = g.mastery().silent; }
          g.pick(0);                                         // take the first
        }
      }
      return { hands, gaps, kit: g.kit(), ranksBefore, dps: g.state().dps, hp: g.state().maxhp };
    });
    const all = r.hands.flat();
    ok("six MASTERY hands arrive, each five silent levels after the last, three cards each",
       r.hands.length === 6 && r.gaps.every(x => x === 5) && r.hands.every(h => h.length === 3),
       `${r.hands.length} hands, gaps ${r.gaps.join(",")}, sizes ${r.hands.map(h => h.length).join(",")}`);
    ok("every card is a MASTERY of a finished upgrade, never MORE and never a rule",
       all.every(c => c.lv === "MASTERY") && !all.some(c => c.key === "dupe") &&
       all.every(c => ["spinach","boots","tempo","magnet","plating","heart","clover"].includes(c.key)),
       [...new Set(all.map(c => c.key))].join(" "));
    ok("the card shows the pip you would gain past three: four pips with the fourth lit, or five",
       all.every(c => (c.pips === 4 || c.pips === 5) && c.lit === 1 && c.filled === c.pips - 1),
       `${all.map(c => `${c.pips}/${c.filled}+${c.lit}`).slice(0, 6).join(" ")}`);
    const ranks = Object.fromEntries(r.kit.map(x => x.split(":")));
    ok("six taken: the kit now holds ranks four and five, none past five",
       Object.values(ranks).some(v => v === "4" || v === "5") && !Object.values(ranks).some(v => +v > 5),
       `${r.kit.filter(x => /:[45]$/.test(x)).join(" ")}`);
  }

  console.log("\n=== 52. THE PHONE KIT AND CAMERA ===");
  {
    // The phone film (R248) found a kit of nine in three rows of four under the
    // chain bars, and the animal filling half the screen. The kit was absolutely
    // positioned at 50% with no width and could never exceed half the screen;
    // the phone media block began the sheet and lost to every base rule after
    // it; and a fixed vertical lens left 28 degrees across in portrait.
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
    const pg = await ctx.newPage();
    await pg.goto(page.url(), { waitUntil: "load" }); await pg.waitForTimeout(500);
    const r = await pg.evaluate(async () => {
      const g = window.__g; g.wipeSave(); g.start("intern"); g.god(); g.freezeEvents(true); g.freezeSpawns(true); g.setShake(0); g.drainPicks(true);
      for (const k of ["bolt","zap","skulls","dupe","spinach","tempo","clover","momentum","hunter"]) g.give(k, 1);
      g.step(5, 1/60); g.resume();
      // the kit bar is drawn on the frame loop; wait for it rather than for a clock
      const k = document.getElementById("kit");
      for (let i = 0; i < 40 && k.children.length < 10; i++) await new Promise(res => setTimeout(res, 50));
      const slots = [...k.children].map(s => s.getBoundingClientRect());
      const rows = new Set(slots.map(s => Math.round(s.top))).size, kitTop = Math.min(...slots.map(s => s.top));
      const hop = document.getElementById("hop").getBoundingClientRect();
      // and the boss alert against the region caption in the top-left corner
      g.boss(0); g.step(2, 1/60);
      let box = null; for (let i = 0; i < 40 && !box; i++) { await new Promise(res => setTimeout(res, 50)); box = g.alertBox(); }
      box = box || [0, 0, ""]; const biome = document.getElementById("biome").getBoundingClientRect();
      return { n: slots.length, rows, slotW: slots[0].width, hopBottom: hop.bottom, kitTop, cam: g.camInfo(), kitW: k.getBoundingClientRect().width,
               warn: [box[0], box[1]], biome: [Math.round(biome.top), Math.round(biome.bottom)], warnText: box[2] };
    });
    await ctx.close();
    const land = await page.evaluate(async () => { const g = window.__g; g.wipeSave(); g.start("intern"); g.god(); g.freezeEvents(true); g.freezeSpawns(true);
      g.drainPicks(true); g.step(5, 1/60); g.resume(); await new Promise(res => setTimeout(res, 200)); return g.camInfo(); });
    ok("ten things in the kit sit in at most two rows of thirty-pixel slots on a 390px phone, not three rows of four",
       r.n === 10 && r.rows <= 2 && Math.abs(r.slotW - 30) < 1 && r.kitW > 200,
       `${r.n} slots of ${r.slotW}px in ${r.rows} rows, kit ${Math.round(r.kitW)}px wide`);
    ok("and the chain bar sits above the kit, not through it", r.hopBottom <= r.kitTop + 1,
       `bar bottom ${Math.round(r.hopBottom)}, kit top ${Math.round(r.kitTop)}`);
    ok("the boss alert prints below the region caption on a phone, not through it",
       /MATRIARCH/.test(r.warnText) && r.warn[0] >= r.biome[1],
       `alert ${r.warn.join("-")} "${r.warnText}", caption ${r.biome.join("-")}`);
    ok("the portrait camera opens its lens and backs the boom off: wider than landscape and further away",
       r.cam.fov > land.fov + .12 && r.cam.dist > land.dist * 1.12,
       `portrait fov ${r.cam.fov} dist ${r.cam.dist}; landscape fov ${land.fov} dist ${land.dist}`);
  }

  console.log("\n=== 53. ATTACKS HAVE BODIES ===");
  {
    // Reported: "models still are clunky, especially attack animations". A
    // weapon firing shoved the body forward a quarter of a lean and nothing
    // else. Every fire now runs a strike envelope - wind-up away, strike
    // through, recovery - resolved into a twist, a pitch, a reach, a lean and
    // a squash that every body plan gets through one transform; a bat swing
    // is mostly twist, a bolt mostly a thrust of the head. And the facing
    // eases into a new heading instead of cutting to it.
    const r = await page.evaluate(async () => {
      const g = window.__g, key = (t, c) => dispatchEvent(new KeyboardEvent(t, { code: c }));
      const boot = (w) => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.aim(0); g.give(w, 0);
        for (let i = 0; i < 5; i++) g.spawnAt("brute", -3 + i * 1.5, 5.5); g.step(20, 1/60); };
      const film = (w) => { boot(w); const c0 = g.fxCounts(); let n = 0;
        while (n < 600) { g.stepRaw(1/60); n++; const c = g.fxCounts(); if (c.swings > c0.swings || c.bolts > c0.bolts || c.rings > c0.rings || c.shells > c0.shells) break; }
        const frames = []; for (let i = 0; i < 30; i++) { frames.push({ t: +g.anim().atkT.toFixed(3), ...g.pose() }); g.stepRaw(1/60); } return frames; };
      // rest: after the last swing has fully recovered and before the next
      const rest = (() => { boot("bat"); let n = 0; while (n++ < 200 && !(g.anim().atkT > .45 && g.anim().atkT < .95)) g.stepRaw(1/60); return g.pose(); })();
      // the turn: a quarter turn, sampled
      boot("bat"); g.aim(0); key("keydown", "KeyA"); const turn = []; for (let i = 0; i < 24; i++) { g.stepRaw(1/60); turn.push(+g.state().face.toFixed(3)); } key("keyup", "KeyA");
      return { bat: film("bat"), bolt: film("bolt"), pulse: film("pulse"), rest, turn };
    });
    const peak = (fr, f) => fr.reduce((m, x) => Math.abs(x[f]) > Math.abs(m[f]) ? x : m, fr[0]);
    const early = r.bat.filter(f => f.t < .08), late = r.bat.filter(f => f.t > .42);
    ok("at rest nothing is on: no twist, no pitch, no reach, squash one", !r.rest.on && r.rest.tw === 0 && r.rest.reach === 0 && r.rest.sq === 1, JSON.stringify(r.rest));
    ok("a bat swing winds up one way and strikes through the other, more than a third of a radian, and is home within four tenths of a second",
       early.length > 0 && late.length > 0 && Math.sign(early[0].tw) === -Math.sign(peak(r.bat, "tw").tw) && Math.abs(peak(r.bat, "tw").tw) > .35 && late.every(f => !f.on),
       `wind-up ${early[0] ? early[0].tw : "none"} at ${early[0] ? early[0].t : "-"}s, peak ${peak(r.bat, "tw").tw} at ${peak(r.bat, "tw").t}s, home by ${late[0] ? late[0].t : "-"}s`);
    ok("a bolt is a thrust: the front reaches forward and pitches, with little twist",
       peak(r.bolt, "reach").reach > .15 && peak(r.bolt, "pitch").pitch > .08 && Math.abs(peak(r.bolt, "tw").tw) < .15,
       `reach ${peak(r.bolt, "reach").reach}, pitch ${peak(r.bolt, "pitch").pitch}, twist ${peak(r.bolt, "tw").tw}`);
    const sqs = r.pulse.map(f => f.sq);
    ok("a pulse is a stomp: the body stretches up in the wind-up and squashes down on the strike",
       Math.max(...sqs) > 1.04 && Math.min(...sqs) < .88 && sqs.indexOf(Math.max(...sqs)) < sqs.indexOf(Math.min(...sqs)),
       `stretch ${Math.max(...sqs)}, squash ${Math.min(...sqs)}`);
    ok("the jaw opens on a swing and stays shut on a stomp", peak(r.bat, "bite").bite > .6 && Math.max(...r.pulse.map(f => f.bite)) === 0,
       `swing bite ${peak(r.bat, "bite").bite}, stomp bite ${Math.max(...r.pulse.map(f => f.bite))}`);
    const mid = r.turn[5], end = r.turn[r.turn.length - 1];
    ok("the turn eases: a tenth of a second into a quarter turn the animal is between the two headings, and it is there by four tenths",
       mid < -.15 && mid > -1.45 && Math.abs(end + Math.PI / 2) < .02,
       `face ${r.turn[0]} -> ${mid} at 0.1s -> ${end} at 0.4s`);
  }

  console.log("\n=== 54. THE CARDS ARE NOT FOUR GREY BOXES ===");
  {
    // Reported: "just four grey boxes on your screen". Every card wears a
    // family word and an accent now - weapons a colour each, the eight
    // growths their own, rules green, evolutions ember, masteries pale gold -
    // and the border, the icon disc, the pips and the headline all take it.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.start("intern"); g.god(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.setShake(0);
      const deal = () => { g.drainPicks(false); g.xp(600); g.step(1, 1/60); if (!g.state().picking) return [];
        const c = [...document.querySelectorAll("#pkCards .card")].map(e => ({ fam: (e.querySelector(".fam") || {}).textContent || "",
          ac: e.style.getPropertyValue("--ac"), border: getComputedStyle(e).borderLeftColor, eff: getComputedStyle(e.querySelector(".eff")).color,
          key: e.dataset.okey, cls: e.className }));
        g.drainPicks(true); return c; };
      const hands = []; for (let i = 0; i < 10; i++) hands.push(...deal());
      return { hands, ups: g.upgrades() };
    });
    const cols = new Set(r.ups.map(u => u.col));
    ok("the eight growths carry eight different colours", r.ups.every(u => /^#[0-9a-f]{6}$/i.test(u.col || "")) && cols.size === 8,
       [...cols].join(" "));
    ok("every card dealt wears a family word and an accent, and the border and the headline take the accent",
       r.hands.length >= 20 && r.hands.every(c => c.fam.length > 0 && /^#/.test(c.ac) && c.border !== "rgb(42, 49, 60)" && c.eff !== "rgb(255, 255, 255)"),
       `${r.hands.length} cards; families ${[...new Set(r.hands.map(c => c.fam))].join(" ")}; blank accents ${r.hands.filter(c => !/^#/.test(c.ac)).length}`);
    const accents = new Set(r.hands.map(c => c.ac));
    ok("and across ten hands the strip shows at least six different accents - it is not one colour with different words",
       accents.size >= 6, `${accents.size} accents`);
  }

  console.log("\n=== 55. THE CREATURE SHOWS WHAT YOU GREW ===");
  {
    // The eight growths were renamed for parts of the animal (R254) - BIGGER
    // TEETH, LONGER LEGS, LONGER NECK, SHARPER CLAWS, THICKER HIDE - and a
    // card that promises a bigger tooth owes you a bigger tooth. Five of them
    // are geometry now: measured on the captured mesh, rank 0 against rank 3,
    // the same six numbers per box the connectivity checks read.
    const r = await page.evaluate(async () => {
      const g = window.__g, key = (t, c) => dispatchEvent(new KeyboardEvent(t, { code: c }));
      const frame = () => new Promise(res => requestAnimationFrame(() => requestAnimationFrame(res)));
      const boot = (ch, st) => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start(ch); g.god(); g.disarm(); g.freezeSpawns(true);
        g.freezeEvents(true); g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0);
        if (st) g.evolveTo(st); g.step(30, 1/60); };
      // a frame BEFORE the capture is armed: the lift the legs earn is read
      // the frame after they earn it, and a rank that has just been given has
      // not been drawn yet
      const cap = async () => { g.resume(); g.step(2, 1/60); await frame(); g.capturePos(); await frame(); await frame();
        const b = g.posOut(); if (!b) return []; const bx = []; for (let i = 0; i < b.length / 6; i++) bx.push(b.slice(i*6, i*6+6)); return bx; };
      // layout (r, f, y, hx, hz, hy)
      const minY = bx => Math.min(...bx.map(x => x[2] - x[5]));
      const maxF = bx => Math.max(...bx.map(x => x[1] + x[4]));
      const meanY = bx => { let s = 0, w = 0; for (const x of bx) { const v = x[3]*x[4]*x[5]; s += x[2]*v; w += v; } return s / w; };
      const bigHx = bx => bx.slice().sort((a, b) => b[3]*b[4]*b[5] - a[3]*a[4]*a[5])[0][3];
      // boxes whose extents grew by the same factor k in [lo, hi] - all three
      // for a tooth; lateral and fore-aft for a claw, because a claw sits at
      // the bottom edge of the leg region and the LONGER LEGS map stretches
      // its height a little on its own
      const grown = (a, b, lo, hi, flat) => { let n = 0; for (let i = 0; i < Math.min(a.length, b.length); i++) {
        const k = b[i][3] / a[i][3]; if (k > lo && k < hi && Math.abs(b[i][4] / a[i][4] - k) < .02 && (flat || Math.abs(b[i][5] / a[i][5] - k) < .02)) n++; } return n; };
      const comps = (bx) => { const n = bx.length, ov = (A, B, k) => Math.min(A[k]+A[k+3], B[k]+B[k+3]) - Math.max(A[k]-A[k+3], B[k]-B[k+3]);
        const par = Array.from({ length: n }, (_, i) => i); const find = a => { while (par[a] !== a) { par[a] = par[par[a]]; a = par[a]; } return a; };
        for (let i = 0; i < n; i++) for (let j = i+1; j < n; j++) if (Math.min(ov(bx[i], bx[j], 0), ov(bx[i], bx[j], 1), ov(bx[i], bx[j], 2)) > 0) { const a = find(i), b = find(j); if (a !== b) par[b] = a; }
        return new Set(Array.from({ length: n }, (_, i) => find(i))).size; };
      // phase advanced per metre walked: the stride, independent of speed
      const stride = () => { g.aim(0); const a0 = g.anim().ph, s0 = g.state(); key("keydown", "KeyW"); for (let i = 0; i < 90; i++) g.stepRaw(1/60); key("keyup", "KeyW");
        const a1 = g.anim().ph, s1 = g.state(); for (let i = 0; i < 60; i++) g.stepRaw(1/60); return (a1 - a0) / Math.max(.01, Math.hypot(s1.x - s0.x, s1.z - s0.z)); };
      const out = {};
      boot("intern", 0);
      const base = await cap(); out.n0 = base.length; out.grow0 = g.grow();
      out.stride0 = stride();
      g.give("spinach", 3); const t = await cap(); out.teeth = { grown: grown(base, t, 1.58, 1.74), mul: g.grow().teeth };
      g.give("boots", 3); const l = await cap();
      out.legs = { rise: meanY(l) - meanY(t), feet: minY(l) - minY(base), lift: g.grow().lift, mul: g.grow().legs, stride: stride() };
      g.give("heart", 3); const nk = await cap(); out.neck = { reach: maxF(nk) / maxF(l), add: g.grow().neck };
      g.give("clover", 3); const c = await cap(); out.claws = { grown: grown(nk, c, 1.68, 1.82, true), mul: g.grow().claws };
      g.give("plating", 3); const h = await cap(); out.hide = { wider: bigHx(h) / bigHx(c), add: g.grow().hide };
      // a jaw built by a shared helper - the WYVERNET's hookJaw
      boot("accnt", 1); const j0 = await cap(); g.give("spinach", 3); const j1 = await cap(); out.jaw = { grown: grown(j0, j1, 1.58, 1.74), n: j0.length };
      // and the grown animal is still one object, on three body plans
      out.whole = [];
      for (const [ch, st] of [["intern", 0], ["ox", 1], ["accnt", 1]]) {
        boot(ch, st); const a = await cap(); for (const k of ["spinach", "boots", "heart", "clover", "plating"]) g.give(k, 3);
        const b = await cap(); out.whole.push({ nm: g.stageNm(), n0: a.length, n1: b.length, c0: comps(a), c1: comps(b) });
      }
      return out;
    });
    ok("BIGGER TEETH: rank 3 grows the four fangs by the card's factor, all three extents together",
       r.teeth.grown >= 4 && Math.abs(r.teeth.mul - 1.66) < .01, `${r.teeth.grown} boxes x${r.teeth.mul}`);
    ok("and a jaw drawn by a shared helper grows every tooth in it",
       r.jaw.grown >= 8, `${r.jaw.grown} teeth of ${r.jaw.n} boxes on the WYVERNET`);
    ok("LONGER LEGS: rank 3 lifts the body and the feet stay where the ground is",
       r.legs.rise > .05 && Math.abs(r.legs.feet) < .02 && r.legs.lift > .05,
       `body +${r.legs.rise.toFixed(3)}, feet ${r.legs.feet >= 0 ? "+" : ""}${r.legs.feet.toFixed(3)}, lift ${r.legs.lift}`);
    ok("and it takes longer strides - phase per metre falls by the leg factor",
       r.stride0 > 2.2 && Math.abs(r.legs.stride * r.legs.mul - r.stride0) < .08,
       `${r.stride0.toFixed(3)} -> ${r.legs.stride.toFixed(3)} rad/m at x${r.legs.mul}`);
    ok("LONGER NECK: rank 3 puts the snout at least 8% further forward",
       r.neck.reach > 1.08 && r.neck.add > .2, `x${r.neck.reach.toFixed(3)} (+${r.neck.add})`);
    ok("SHARPER CLAWS: rank 3 grows all twelve claws by the card's factor",
       r.claws.grown >= 12, `${r.claws.grown} claws x${r.claws.mul}`);
    ok("THICKER HIDE: rank 3 makes the torso at least 8% wider",
       r.hide.wider > 1.08, `x${r.hide.wider.toFixed(3)} (+${r.hide.add})`);
    ok("and at full growth each animal is still ONE object - no growth tears a part off",
       r.whole.length === 3 && r.whole.every(w => w.n1 > 0 && w.c1 <= w.c0),
       r.whole.map(w => `${w.nm} ${w.c0}->${w.c1} parts (${w.n0}/${w.n1} boxes)`).join("; "));
  }

  console.log("\n=== 56. THE HORDE'S BITE HAS A WIND-UP ===");
  {
    // The player's attacks got anticipation and follow-through in R252; the
    // horde's bite was still a lean applied the frame the damage landed. A
    // melee enemy in reach now winds up for BITE_WIND - rears back, crouches -
    // and bites only if you are still there; the rest after a landed bite is
    // shorter by the same amount so the cycle costs what it cost. Spitters
    // telegraph the lob off the timer they already run. Read off the gait
    // fields walk() resolves (pre, pt, rc, lg) and off your own HP.
    const r = await page.evaluate(async () => {
      const g = window.__g, key = (t, c) => dispatchEvent(new KeyboardEvent(t, { code: c }));
      const boot = () => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); g.step(30, 1/60); };
      const out = {};
      // 1. stand in reach: the wind-up rises before the bite, the snap follows it, the cycle is unchanged
      boot(); const hp0 = g.state().hp; g.spawnAt("shambler", 0, 1.2);
      const rows = []; let last = hp0; const hits = [];
      for (let i = 0; i < 240; i++) { g.stepRaw(1/60); const e = g.gait()[0], h = g.state().hp; rows.push({ i, pre: e.pre, pt: e.pt, rc: e.rc, lg: e.lg, wu: e.wu }); if (h < last - .01) hits.push(i); last = h; }
      const h0 = hits[0];
      out.stand = { hits: hits.slice(0, 5), gaps: hits.slice(1).map((h, i) => h - hits[i]),
        preBefore: h0 !== undefined ? rows[h0 - 1].pre : null, ptBefore: h0 !== undefined ? rows[h0 - 1].pt : null,
        windFrames: h0 !== undefined ? rows.slice(0, h0).filter(r => r.wu > 0).length : 0,
        ptPeak: h0 !== undefined ? Math.max(...rows.slice(h0, h0 + 8).map(r => r.pt)) : null,
        rcPeak: h0 !== undefined ? Math.max(...rows.slice(h0, h0 + 8).map(r => r.rc)) : null,
        ptLater: h0 !== undefined ? rows[Math.min(239, h0 + 24)].pt : null };
      // 2. walk out of the wind-up: the snap comes and the bite whiffs - and you hear it
      boot(); g.setOpt("sound", 1); g.sfxReset(); const hp1 = g.state().hp; g.spawnAt("shambler", 0, 1.2); let started = -1, snapped = -1, dAt = null;
      for (let i = 0; i < 80; i++) { g.stepRaw(1/60); const e = g.gait()[0]; if (started < 0 && e.wu > 0) { started = i; key("keydown", "KeyS"); }
        if (started >= 0 && snapped < 0 && e.lg > .9) { snapped = i; const s = g.state(); dAt = Math.hypot(e.x - s.x, e.z - s.z); } }
      key("keyup", "KeyS"); out.whiff = { started, snapped, dAt: dAt === null ? null : +dAt.toFixed(2), dmg: +(hp1 - g.state().hp).toFixed(2), clicks: g.sfx().whiff || 0 };
      // ...and a bite that lands makes no click; a pile that whiffs together makes one
      boot(); g.setOpt("sound", 1); g.sfxReset(); g.spawnAt("shambler", 0, 1.2); for (let i = 0; i < 60; i++) g.stepRaw(1/60); out.landClicks = g.sfx().whiff || 0;
      boot(); g.setOpt("sound", 1); g.sfxReset(); for (let k = 0; k < 6; k++) g.spawnAt("shambler", -.5 + k * .2, 1.2); let st2 = -1;
      for (let i = 0; i < 80; i++) { g.stepRaw(1/60); if (st2 < 0 && g.gait().some(e => e.wu > 0)) { st2 = i; key("keydown", "KeyS"); } }
      key("keyup", "KeyS"); out.pileClicks = g.sfx().whiff || 0;
      // 3. the spitter: the tell rises through the last SPIT_TELL of the timer, and the lob is a snap
      boot(); g.spawnAt("spitter", 0, 12.5); const sr = [];
      for (let i = 0; i < 400; i++) { g.stepRaw(1/60); const e = g.gait()[0]; sr.push({ pre: e.pre, lg: e.lg, pt: e.pt }); }
      const snaps = sr.map((r, i) => r.lg > .9 && (i === 0 || sr[i-1].lg <= .9) ? i : -1).filter(i => i >= 0);
      const s2 = snaps[1];
      out.spit = { snaps, pre18: s2 ? sr[s2 - 18].pre : null, pre1: s2 ? sr[s2 - 1].pre : null, ptBefore: s2 ? sr[s2 - 1].pt : null,
        ptPeak: s2 ? Math.max(...sr.slice(s2, s2 + 8).map(r => r.pt)) : null, quiet: s2 ? sr[s2 - 60].pre : null };
      return out;
    });
    const S = r.stand;
    ok("in reach, a shambler winds up before it bites: the rear-back is most of the way in the frame before the hit",
       S.hits.length >= 3 && S.windFrames >= 8 && S.preBefore > .6 && S.ptBefore < -.12,
       `${S.windFrames} frames of wind-up, pre ${S.preBefore}, pitch ${S.ptBefore} before hit at frame ${S.hits[0]}`);
    ok("and the bite is a snap forward with reach, recovered a quarter second later",
       S.ptPeak > .30 && S.rcPeak > .20 && Math.abs(S.ptLater) < .12,
       `pitch peak ${S.ptPeak}, reach ${S.rcPeak}, pitch +.4s ${S.ptLater}`);
    ok("the bite cycle costs what it cost - one landed bite every .68 s, give or take a frame",
       S.gaps.length >= 3 && S.gaps.every(gp => gp >= 39 && gp <= 44), `gaps ${S.gaps.join(" ")} frames`);
    ok("walk out of the wind-up and the snap comes anyway - at air: no damage",
       r.whiff.started >= 0 && r.whiff.snapped > r.whiff.started && r.whiff.dmg === 0 && r.whiff.dAt > 1.3,
       `wind-up at ${r.whiff.started}, snap at ${r.whiff.snapped} with the shambler ${r.whiff.dAt} m away, damage ${r.whiff.dmg}`);
    ok("and you hear it: a whiff clicks, a landed bite does not, and six whiffing at once are one click",
       r.whiff.clicks >= 1 && r.landClicks === 0 && r.pileClicks >= 1 && r.pileClicks <= 2,
       `walk-out ${r.whiff.clicks}, landed ${r.landClicks}, pile of six ${r.pileClicks}`);
    // the first landed bite of a fresh save says it, once, ever
    const tip = await page.evaluate(() => {
      const g = window.__g; const boot = () => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); g.step(30, 1/60); };
      const bite = () => { g.clearEnemies(); g.spawnAt("shambler", 0, 1.2); for (let i = 0; i < 30; i++) g.stepRaw(1/60); };
      const seen = () => g.alerts().some(a => /STEP OUT/.test(a));
      boot(); bite(); const first = seen(); for (let i = 0; i < 200; i++) g.stepRaw(1/60); bite(); const second = seen();
      g.start("intern"); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true); g.drainPicks(true); g.clearEnemies(); g.place(0, 0); g.step(30, 1/60); bite(); const nextRun = seen();
      return { first, second, nextRun };
    });
    ok("the first bite of a fresh save says the rear was the warning - once, not on the second, not in the next run",
       tip.first && !tip.second && !tip.nextRun, JSON.stringify(tip));
    // and on a phone the toast fits the screen: a 31-character plate at the
    // lane's size is wider than 390 px unless the type gives
    const phone = await (async () => {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
      const mp = await ctx.newPage(); await mp.goto(FILE, { waitUntil: "load" }); await mp.waitForTimeout(300);   // FILE, not index.html: a mutant runs against a copy
      const r = await mp.evaluate(async () => { const g = window.__g; g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); g.step(30, 1/60); g.spawnAt("shambler", 0, 1.2); for (let i = 0; i < 20; i++) g.stepRaw(1/60);
        let box = null; for (let i = 0; i < 40 && !(box && box.length > 3); i++) { await new Promise(res => requestAnimationFrame(res)); box = g.alertBox(); }
        return { box, w: innerWidth, alerts: g.alerts() }; });
      await ctx.close(); return r;
    })();
    ok("and on a 390 px phone the toast's plate fits inside the screen",
       phone.box && phone.box.length > 3 && /STEP OUT/.test(phone.box[2]) && phone.box[3] <= phone.w * .95,
       phone.box ? `plate ${phone.box[3]} px of ${phone.w}, "${phone.box[2]}"` : `no toast (${JSON.stringify(phone.alerts)})`);
    const hint = await page.evaluate(() => (document.getElementById("pauseHint") || {}).textContent || "");
    ok("and the pause screen says so: a bite has a wind-up, and stepping out of it is the answer",
       /wind-up/i.test(hint) && /rears back/i.test(hint) && /step out/i.test(hint), hint.replace(/\s+/g, " ").slice(0, 160));
    ok("a spitter telegraphs the lob: quiet a second before, rearing through the last .3 s, and the spit is a snap",
       r.spit.snaps.length >= 2 && r.spit.quiet < .05 && r.spit.pre18 < .15 && r.spit.pre1 > .7 && r.spit.ptBefore < -.15 && r.spit.ptPeak > .3,
       `spits at ${r.spit.snaps.join(" ")}; pre -1s ${r.spit.quiet}, -.3s ${r.spit.pre18}, -1f ${r.spit.pre1}; pitch ${r.spit.ptBefore} -> ${r.spit.ptPeak}`);
  }

  console.log("\n=== 57. THE DIVE HAS A BOTTOM ===");
  {
    // The pterling's dive had a telegraph (rear, wings back, white-hot) and a
    // streak, and then a straight line in that ended the frame its timer did:
    // level flight, at speed, and the bird popped a sixth of its height back
    // up. The dive now pitches nose-down through the same channel the bite
    // uses, snaps at the bottom - on the hit or at air - and pulls out over a
    // quarter second.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const boot = () => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); g.step(30, 1/60); };
      // 1. the numbers, one frame at a time, from spawn through the first dive and out of it
      boot(); const hp0 = g.state().hp; g.spawnAt("runner", 0, 7.5); const rows = [];
      for (let i = 0; i < 300; i++) { g.stepRaw(1/60); const e = g.gait()[0]; if (!e) break;
        rows.push({ i, dvW: e.dvW, dvT: e.dvT, dvE: e.dvE, pt: e.pt, lg: e.lg, dmg: +(hp0 - g.state().hp).toFixed(1) }); }
      const windRows = rows.filter(q => q.dvW > .2 && q.dvT === 0);
      const commit = rows.findIndex(q => q.dvT > 0);
      const end = rows.findIndex((q, i) => i > commit && commit >= 0 && q.dvT === 0);
      const inDive = commit >= 0 ? rows.slice(commit, end > 0 ? end : commit + 27) : [];
      const after = end > 0 ? rows.slice(end, end + 30) : [];
      const out = { commit, end, windPt: windRows.length ? Math.min(...windRows.map(q => q.pt)) : null,
        ptIn: inDive.length > 9 ? inDive[9].pt : null, ptPeak: inDive.length ? Math.max(...inDive.map(q => q.pt)) : null,
        snapAtBottom: after.length ? Math.max(...after.slice(0, 3).map(q => q.lg)) : null,
        dmgAtEnd: after.length ? after[0].dmg : null,
        easeOut: after.map(q => q.dvE), framesToLow: after.findIndex(q => q.dvE < .3),
        monotone: after.every((q, i) => i === 0 || q.dvE <= after[i-1].dvE + 1e-6) };
      // 2. the drawn bird does not pop at the bottom: world-space top, frame by frame, across the dive's end
      boot(); g.spawnAt("runner", 0, 7.5); let n = 0; while (n++ < 300) { g.stepRaw(1/60); const e = g.gait()[0]; if (e && e.dvT > 0 && e.dvT < .08) break; }
      const tops = [];
      for (let i = 0; i < 16; i++) { g.pause(true); g.captureEnemyWorld(); await frame(); await frame(); const b = g.enemyBox(); const e = g.gait()[0];
        tops.push({ top: b ? +(b.maxY - b.gy).toFixed(3) : null, dvT: e.dvT, dvE: e.dvE }); g.stepRaw(1/60); }
      out.tops = tops; out.maxJump = Math.max(...tops.slice(1).map((q, i) => Math.abs(q.top - tops[i].top)));
      // 3. a dive that MISSES - you step aside once it has committed - still
      //    snaps at air when its timer runs out, for no damage
      boot(); const hp2 = g.state().hp; g.spawnAt("runner", 0, 7.5); const key = (tp, c) => dispatchEvent(new KeyboardEvent(tp, { code: c }));
      let cm = -1, endLg = null, endDmg = null; n = 0;
      while (n++ < 400) { g.stepRaw(1/60); const e = g.gait()[0]; if (!e) break;
        if (cm < 0 && e.dvT > 0) { cm = n; key("keydown", "KeyA"); }
        // the hook rounds dvT to 3 places, so "0" can be a frame early: read
        // the snap across this frame and the next
        if (cm > 0 && e.dvT === 0 && endLg === null) { g.stepRaw(1/60); const e2 = g.gait()[0]; endLg = Math.max(e.lg, e2 ? e2.lg : 0); endDmg = +(hp2 - g.state().hp).toFixed(1); break; } }
      key("keyup", "KeyA"); out.miss = { committed: cm, endLg, endDmg };
      return out;
    });
    ok("the wind-up rears the bird: pitch goes negative while it hangs and flares",
       r.commit > 0 && r.windPt !== null && r.windPt < -.08, `commit at frame ${r.commit}, wind-up pitch ${r.windPt}`);
    ok("committed, it goes in nose-down within 150 ms and holds it",
       r.ptIn !== null && r.ptIn > .30 && r.ptPeak > .30, `pitch at +9 frames ${r.ptIn}, peak ${r.ptPeak}`);
    ok("the bottom is a snap - on the hit, or at air when the timer runs out",
       r.end > 0 && r.snapAtBottom > .85, `dive ended at frame ${r.end}, lg ${r.snapAtBottom}, damage by then ${r.dmgAtEnd}`);
    ok("and it pulls out over a quarter second instead of cutting to level flight",
       r.framesToLow >= 4 && r.framesToLow <= 20 && r.monotone, `dvE after the end: ${r.easeOut.slice(0, 10).join(" ")} (below .3 after ${r.framesToLow} frames)`);
    ok("the drawn bird does not pop at the dive's end: no frame moves its top more than 12 cm",
       r.tops.every(q => q.top !== null) && r.maxJump < .12, `tops ${r.tops.map(q => q.top).join(" ")} (max step ${r.maxJump && r.maxJump.toFixed(3)})`);
    ok("a dive you step out of still snaps at air when it runs out - and for nothing",
       r.miss.committed > 0 && r.miss.endLg !== null && r.miss.endLg > .85 && r.miss.endDmg === 0,
       `committed at ${r.miss.committed}, lg at the end ${r.miss.endLg}, damage ${r.miss.endDmg}`);
  }

  console.log("\n=== 58. THE BOSS BEATS PITCH ===");
  {
    // bossBeat carried a squash and a lean per phase - a shear, the same
    // construction the horde's bite had. Each beat now also carries a pitch
    // about the hips (the tell rears the head, the act drives it down) and a
    // reach on the act, through the channel eb() already applies for the
    // bite. And a boss inside a beat does not chomp: the R256 wind-up was
    // running through the slam's tell, so contact damage there lands as it
    // always did and the beat owns the pose.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const boot = () => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); g.step(30, 1/60); };
      const out = { beats: {} };
      boot(); g.god(); g.boss(0); g.step(1, 1/60);
      for (const kind of ["slam", "sinkhole", "charge", "spokes", "evict"]) {
        const A = { tell: 0, act: 0 };
        g.bossCue(kind, "tell", 0.001); const tell = g.beat();           // the end of the tell: u ~ 1
        g.bossCue(kind, "act"); const act = g.beat();                    // act = 1
        out.beats[kind] = { tellPt: tell.pt, actPt: act.pt, actRc: act.rc, tellRc: tell.rc };
      }
      // the drawn MATRIARCH: reared at the end of the slam's tell, down on the act
      // cued and drawn without a step in between: a step would run the beat
      // on into its next phase (a tell cued at .001 s is an act one frame on)
      const boxAt = async () => { g.pause(true); g.captureEnemyWorld(); await frame(); await frame(); const b = g.enemyBox(); return b ? { top: +(b.maxY - b.gy).toFixed(3), bot: +(b.minY - b.gy).toFixed(3) } : null; };
      g.bossCue("slam", "tell", 0.12); out.tellBox = await boxAt();
      g.bossCue("slam", "act", 0.30); out.actBox = await boxAt();
      g.bossCue("slam", "move", 2.0); g.step(90, 1/60); out.restBox = await boxAt();
      // in contact through a tell: no wind-up, no snap, and the damage still lands
      boot(); g.boss(0); g.step(1, 1/60); const b0 = g.bossAt(); g.place(b0.x, b0.z - (b0.rad + .4)); g.step(2, 1/60);
      g.bossCue("slam", "tell", 1.15); const hp0 = g.state().hp; let wuMax = 0, lgMax = 0, hits = 0, last = hp0;
      for (let i = 0; i < 60; i++) { g.stepRaw(1/60); const e = g.gait()[0]; wuMax = Math.max(wuMax, e.wu); lgMax = Math.max(lgMax, e.lg); const h = g.state().hp; if (h < last - .01) hits++; last = h; }
      out.tellContact = { wuMax, lgMax, hits, dmg: +(hp0 - last).toFixed(1), phase: g.beat().phase };
      // ...and outside a beat the bite is back
      g.bossCue("slam", "move", 3.0); let wuSeen = 0; for (let i = 0; i < 90; i++) { g.stepRaw(1/60); wuSeen = Math.max(wuSeen, g.gait()[0].wu); }
      out.restWu = wuSeen;
      return out;
    });
    const B = r.beats, K = Object.keys(B);
    ok("every beat rears through its tell: pitch negative at the end of the tell for all five kinds",
       K.length === 5 && K.every(k => B[k].tellPt < -.04), K.map(k => `${k} ${B[k].tellPt}`).join(", "));
    ok("and comes down on the act - a small pitch, a return from the rear rather than a dive under the ground - with the reach where the act goes forward",
       K.every(k => B[k].actPt >= .04 && B[k].actPt <= .12) && ["slam", "sinkhole", "charge", "evict"].every(k => B[k].actRc > .05) && B.spokes.actRc === 0 && K.every(k => B[k].tellRc === 0),
       K.map(k => `${k} pt ${B[k].actPt} rc ${B[k].actRc}`).join(", "));
    const TB = r.tellBox, AB = r.actBox, RB = r.restBox;
    ok("the drawn MATRIARCH reads it: taller and reared at the end of the slam's tell than at rest, and down on the stomp",
       TB && AB && RB && TB.top > RB.top + .3 && AB.top < RB.top - .8,
       `top: tell ${TB && TB.top}, act ${AB && AB.top}, rest ${RB && RB.top}`);
    ok("and the stomp keeps its feet on the ground - nothing of it is driven more than 25 cm under",
       AB && AB.bot > -.25 && TB && TB.bot > -.25, `lowest point: tell ${TB && TB.bot}, act ${AB && AB.bot}, rest ${RB && RB.bot}`);
    ok("a boss in a tell does not chomp - no wind-up, no snap - and the contact damage still lands",
       r.tellContact.wuMax === 0 && r.tellContact.lgMax === 0 && r.tellContact.hits >= 1 && r.tellContact.dmg > 0,
       `wu ${r.tellContact.wuMax}, lg ${r.tellContact.lgMax}, ${r.tellContact.hits} hits for ${r.tellContact.dmg} in a second of tell (${r.tellContact.phase})`);
    ok("and outside a beat the bite winds up again", r.restWu > 0, `wu seen ${r.restWu}`);
  }

  console.log("\n=== 59. THE BITE HAS A SPECIES ===");
  {
    // One wind-up for every animal made a CERATOP nip like a RAPTORLING. The
    // wind-up is per kind now - long on the brute, a nip on the skitter - and
    // the slow ones start early while the quick ones wait, so every kind
    // lands the same beat after the rest ends and a pile bites at the pace it
    // always did whatever it is made of.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const boot = () => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); g.step(30, 1/60); };
      const run = (kind, extra) => {
        boot(); const hp0 = g.state().hp; g.spawnAt(kind, 0, 1.2); for (const k of (extra || [])) g.spawnAt(k, .6, 1.2);
        const hits = [], wind = []; let last = hp0, ifr0 = -1, ptPeak = 0;
        for (let i = 0; i < 260; i++) { g.stepRaw(1/60); const s = g.state(), e = g.gait().find(q => q.type === kind);
          if (e && e.wu > 0) wind.push(i);
          if (hits.length === 1 && ifr0 < 0 && s.iframe <= 0) ifr0 = i;
          if (s.hp < last - .01) hits.push(i); last = s.hp;
          if (e && hits.length && i < hits[0] + 12) ptPeak = Math.max(ptPeak, e.pt); }
        return { w1: wind.filter(i => i < (hits[0] === undefined ? 999 : hits[0])).length, hits: hits.slice(0, 5),
                 gaps: hits.slice(1).map((h, i) => h - hits[i]), delay: ifr0 >= 0 && hits[1] !== undefined ? hits[1] - ifr0 : null, ptPeak: +ptPeak.toFixed(3) };
      };
      return { shambler: run("shambler"), brute: run("brute"), skitter: run("skitter"), pile: run("shambler", ["brute", "skitter"]) };
    });
    const K = ["shambler", "brute", "skitter"];
    ok("the CERATOP winds up longest and the RAPTORLING nips: frames of wind-up before the first bite",
       r.brute.w1 >= 15 && r.skitter.w1 <= 9 && r.shambler.w1 >= 9 && r.shambler.w1 <= 14 && r.brute.w1 > r.shambler.w1 && r.shambler.w1 > r.skitter.w1,
       K.map(k => `${k} ${r[k].w1}`).join(", "));
    ok("and every kind lands the same beat after the rest ends - the slow start early, the quick wait",
       K.every(k => r[k].delay !== null) && Math.abs(r.brute.delay - r.shambler.delay) <= 3 && Math.abs(r.skitter.delay - r.shambler.delay) <= 3,
       K.map(k => `${k} +${r[k].delay} frames`).join(", "));
    ok("so each kind's own cycle is the .68 s it was",
       K.every(k => r[k].gaps.length >= 3 && r[k].gaps.every(gp => gp >= 39 && gp <= 44)), K.map(k => `${k} ${r[k].gaps.join(" ")}`).join("; "));
    ok("and a pile of all three bites at the same pace",
       r.pile.gaps.length >= 3 && r.pile.gaps.every(gp => gp >= 39 && gp <= 44), `pile ${r.pile.gaps.join(" ")}`);
    ok("the heavy bite is the bigger motion: the CERATOP's snap pitches further than the RAPTORLING's",
       r.brute.ptPeak > r.skitter.ptPeak + .05 && r.brute.ptPeak > r.shambler.ptPeak, K.map(k => `${k} ${r[k].ptPeak}`).join(", "));
  }

  console.log("\n=== 60. SECOND HEAD IS A SECOND HEAD ===");
  {
    // The card says +1 OF EVERYTHING and the animal showed nothing. Everything
    // forward of two thirds of the body's length is drawn twice now, each
    // copy turned about the shoulders - two necks splaying from one chest to
    // two heads. A rigid turn, so every joint a head had it keeps; the mesh
    // capture records the unturned box once, so the one-object question is
    // still answered by the base mesh and the heads are counted by the draw.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => requestAnimationFrame(res)));
      const boot = (ch, st) => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start(ch); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); if (st) g.evolveTo(st); g.step(30, 1/60); };
      const cap = async () => { g.resume(); g.step(2, 1/60); await frame(); g.capturePos(); await frame(); await frame();
        const b = g.posOut(); if (!b) return []; const bx = []; for (let i = 0; i < b.length / 6; i++) bx.push(b.slice(i*6, i*6+6)); return bx; };
      const comps = (bx) => { const n = bx.length, ov = (A, B, k) => Math.min(A[k]+A[k+3], B[k]+B[k+3]) - Math.max(A[k]-A[k+3], B[k]-B[k+3]);
        const par = Array.from({ length: n }, (_, i) => i); const find = a => { while (par[a] !== a) { par[a] = par[par[a]]; a = par[a]; } return a; };
        for (let i = 0; i < n; i++) for (let j = i+1; j < n; j++) if (Math.min(ov(bx[i], bx[j], 0), ov(bx[i], bx[j], 1), ov(bx[i], bx[j], 2)) > 0) { const a = find(i), b = find(j); if (a !== b) par[b] = a; }
        return new Set(Array.from({ length: n }, (_, i) => find(i))).size; };
      const out = { plans: [] };
      for (const [ch, st] of [["intern", 1], ["ox", 1], ["accnt", 1], ["pyre", 1], ["scrap", 0]]) {
        boot(ch, st); const a = await cap(); const g0 = g.grow();
        g.give("dupe", 1); const b = await cap(); const g1 = g.grow();
        g.give("dupe", 2); await cap(); const g3 = g.grow();
        out.plans.push({ nm: g.stageNm(), n0: a.length, n1: b.length, c0: comps(a), c1: comps(b), hb0: g0.headBoxes, hb1: g1.headBoxes, hb3: g3.headBoxes, heads1: g1.heads, heads3: g3.heads, splay: g1.splay });
      }
      return out;
    });
    const Pl = r.plans;
    ok("at rank 1 the head region is drawn twice: the draw counts an even number of head boxes, at least a sixth of the body, where rank 0 counted none",
       Pl.every(p => p.hb0 === 0 && p.hb1 > 0 && p.hb1 % 2 === 0 && p.hb1 / 2 >= p.n0 * .16 && p.heads1 === 2),
       Pl.map(p => `${p.nm} ${p.hb1 / 2}x2 of ${p.n0}`).join(", "));
    ok("and never more than two, whatever the rank: rank 3 draws what rank 1 drew",
       Pl.every(p => p.heads3 === 2 && p.hb3 === p.hb1), Pl.map(p => `${p.nm} ${p.hb1}->${p.hb3}`).join(", "));
    ok("the copies are turned apart by at least .2 rad about the shoulders", Pl.every(p => p.splay >= .2 && p.splay <= .42), Pl.map(p => `${p.nm} ${p.splay}`).join(", "));
    ok("the base mesh the checks read is unchanged and still one object on five plans - a turned copy is a rigid image of a connected part",
       Pl.every(p => p.n1 === p.n0 && p.c1 === p.c0 && p.c1 === 1), Pl.map(p => `${p.nm} ${p.n0}/${p.n1} boxes, ${p.c0}->${p.c1} parts`).join("; "));
  }

  console.log("\n=== 61. EVERY MUTANT STILL ANCHORS ===");
  {
    // A mutant whose `from` no longer appears in the game is a mutant that
    // never applies, and a mutant that never applies is a hole in the
    // suite nobody sees: eleven of them had rotted that way by R261, three
    // of them written that same week. Read straight off the files, no
    // browser: every mutant's anchor must occur in index.html exactly once,
    // and its replacement must actually change something.
    const src = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
    const mu = fs.readFileSync(path.join(__dirname, "mutate.js"), "utf8");
    const m0 = mu.indexOf("const MUTANTS = ["), m1 = mu.indexOf("\n];", m0) + 3;
    const MUTANTS = new Function(mu.slice(m0, m1) + "; return MUTANTS;")();
    const count = (s, f) => s.split(f).length - 1;
    const stale = MUTANTS.filter(m => count(src, m.from) !== 1).map(m => `${m.id} x${count(src, m.from)}`);
    const noop = MUTANTS.filter(m => m.from === m.to).map(m => m.id);
    const ids = MUTANTS.map(m => m.id), dupIds = ids.filter((id, i) => ids.indexOf(id) !== i);
    ok("every mutant's anchor occurs in the game exactly once", MUTANTS.length > 150 && stale.length === 0,
       stale.length ? `stale: ${stale.join(", ")}` : `${MUTANTS.length} mutants anchored`);
    ok("and every mutant changes something, under a name of its own", noop.length === 0 && dupIds.length === 0,
       `${noop.length} no-ops${noop.length ? ` (${noop.join(", ")})` : ""}, ${dupIds.length} duplicate ids${dupIds.length ? ` (${dupIds.join(", ")})` : ""}`);
  }

  console.log("\n=== 62. THE BANNER CLEARS THE BOSS ===");
  {
    // The evolution banner sat at 40% of the screen, which is where the boss
    // is when there is one - the run film caught FLAREDRAKE and PYRAETHON
    // announcing themselves across THE MATRIARCH and THORNBACK. With a boss
    // alive it steps up into the band between the clock and the boss bar.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      const frame = () => new Promise(res => requestAnimationFrame(() => requestAnimationFrame(res)));
      const boot = () => { g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
        g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); g.step(30, 1/60); };
      // the banner's clock runs on RENDER frames, not sim steps, and it fades
      // in over its first third of a second: render until it has
      const where = async () => { await frame(); for (let k = 0; k < 60 && g.evoTxt().t > 2.95; k++) await frame(); const ev = document.getElementById("evo"), b = ev.getBoundingClientRect();
        return { top: +(b.top / innerHeight).toFixed(3), mid: +((b.top + b.height / 2) / innerHeight).toFixed(3), up: ev.classList.contains("up"), op: +getComputedStyle(ev).opacity, txt: ev.firstElementChild.textContent }; };
      const out = {};
      boot(); g.evolveTo(1); out.alone = await where();
      boot(); g.boss(1); g.step(2, 1/60); const bs = g.bossAt(); g.place(bs.x, bs.z - 12); g.step(60, 1/60); g.evolveTo(1); out.boss = await where();
      g.clearEnemies(); out.after = await where();
      return out;
    });
    ok("with no boss on the field the banner sits where it always did, in the upper-middle of the screen, visible",
       !r.alone.up && r.alone.op > .5 && r.alone.mid > .34 && r.alone.mid < .46 && r.alone.txt.length > 0, `mid ${r.alone.mid}, opacity ${r.alone.op}, "${r.alone.txt}"`);
    ok("with a boss alive it steps up out of the fight's third: its centre is above 30% of the screen, still visible",
       r.boss.up && r.boss.op > .5 && r.boss.mid < .30, `mid ${r.boss.mid}, opacity ${r.boss.op}`);
    ok("and it comes back down the moment the boss is gone", !r.after.up && r.after.mid > .34, `mid ${r.after.mid}`);
  }

  console.log("\n=== 63. THE GILDWING GLOATS ===");
  {
    // The collector runs for three seconds and pauses for one and a bit, and
    // the pause is the window you kill it in - signalled by a flash and
    // nothing in the body. It rears up and stretches tall through the pause
    // now, through the same pitch channel the bite uses, and drops it the
    // moment it bolts again.
    const r = await page.evaluate(() => {
      const g = window.__g;
      g.wipeSave(); g.pin(3); g.pinRun(3); g.start("intern"); g.god(); g.disarm(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true); g.setShake(0); g.clearEnemies(); g.place(0, 0); g.aim(0); g.step(30, 1/60);
      g.spawnAt("collector", 0, 9); const rows = [];
      for (let i = 0; i < 420; i++) { g.stepRaw(1/60); const e = g.gait()[0]; if (!e) break; rows.push({ i, rest: e.rest, pt: e.pt, stq: e.stq, taunt: e.taunt, amp: e.amp }); }
      // "running" leaves out the third of a second after a bolt, while the gloat's pose is still letting go
      const running = rows.filter(q => q.rest !== null && q.rest > .3 && q.rest < 2.5), gloat = rows.filter(q => q.rest !== null && q.rest < -.25 && q.rest > -1.2);
      const bolt = rows.find((q, i) => i > 0 && rows[i-1].rest !== null && rows[i-1].rest < -1.2 && q.rest > 2.5);
      const after = bolt ? rows.slice(bolt.i, bolt.i + 12) : [];
      return { n: rows.length, runPt: running.length ? Math.max(...running.map(q => Math.abs(q.pt))) : null, runN: running.length,
        gloatPt: gloat.length ? Math.max(...gloat.map(q => q.pt)) : null, gloatStq: gloat.length ? Math.min(...gloat.map(q => q.stq)) : null, gloatN: gloat.length,
        dropped: after.length ? after[after.length - 1].taunt : null, boltAt: bolt ? bolt.i : null };
    });
    ok("while it runs the body is level: no pitch to speak of over three seconds of flight",
       r.runN > 120 && r.runPt !== null && r.runPt < .06, `${r.runN} frames running, |pitch| peak ${r.runPt}`);
    ok("and through the gloat it is reared back and stretched tall - the window has a shape",
       r.gloatN > 40 && r.gloatPt !== null && r.gloatPt < -.28 && r.gloatStq > 1.07, `${r.gloatN} frames gloating, pitch ${r.gloatPt}, stretch ${r.gloatStq}`);
    ok("and it drops the pose within a fifth of a second of bolting again",
       r.boltAt !== null && r.dropped !== null && r.dropped < .2, `bolt at frame ${r.boltAt}, taunt 12 frames later ${r.dropped}`);
  }

  console.log("\n=== 64. A SHORT HAND IS STILL A CHOICE ===");
  {
    // Seed 41's bot run reaches 8:00 with one legal card (QUICKER HEART, a
    // rank short, everything else maxed or waiting on a partner) and dealt a
    // hand of one under PRESS 1-4 (R272's run film). The snack joins a hand
    // of one now and the caption counts the cards; an EMPTY pool is still
    // not a draft at all - the level is taken silently, as the mastery count
    // requires.
    const r = await page.evaluate(async () => {
      const g = window.__g;
      g.wipeSave(); g.pin(41); g.pinRun(41); g.start("intern"); g.bot(true); g.botHop(true); g.setShake(0); g.runOut(480);
      g.bot(false); g.freezeSpawns(true); g.freezeEvents(true); g.god(); g.clearEnemies();
      const read = () => ({ picking: g.state().picking, lvl: g.state().lvl, pending: g.state().pending, max: g.state().maxhp,
        cards: [...document.querySelectorAll("#pkCards .card")].map(e => ({ nm: (e.querySelector(".nm") || {}).textContent, fam: (e.querySelector(".fam") || {}).textContent })),
        sub: document.getElementById("pkSub").textContent });
      g.drainPicks(false); const lv0 = g.state().lvl; g.xp(400); g.step(1, 1/60); const a = read();
      // take the growth; the rules are held out so the next level's pool is genuinely
      // empty, and the queued level waits out the gap between drafts before it is dealt
      g.noRules(true); g.pick(0); g.step(90, 1/60); const b = read();
      g.drainPicks(true); g.noRules(false);
      return { lv0, a, b, kit: g.kit().join(" ") };
    });
    ok("one legal growth left: the hand is that growth and the snack, and the caption says PRESS 1-2",
       r.a.picking && r.a.cards.length === 2 && r.a.cards[0].nm === "QUICKER HEART" && r.a.cards[1].fam === "SNACK" && /PRESS 1-2/.test(r.a.sub),
       `${r.a.cards.map(c => c.nm).join(" | ")} - "${r.a.sub}" (level ${r.a.lvl}, kit ${r.kit})`);
    ok("and with nothing left the queued level is not a draft at all: no screen, taken as growth (max HP rises)",
       !r.b.picking && r.b.pending === 0 && r.b.max > r.a.max, `picking ${r.b.picking}, pending ${r.a.pending} -> ${r.b.pending}, max HP ${r.a.max} -> ${r.b.max}`);
  }

  console.log("\n" + "=".repeat(58));
  if (errors.length) {
    console.log("ERRORS CAPTURED:");
    [...new Set(errors)].slice(0, 12).forEach(e => console.log("   " + e));
  }
  console.log(`RESULT: ${passes} passed, ${fails} failed`);
  await browser.close();
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error("HARNESS CRASH:", e); process.exit(2); });
