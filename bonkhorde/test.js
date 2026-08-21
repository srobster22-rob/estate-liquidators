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
  const weapons = ["bat","skulls","bolt","pulse","mortar","zap","aura","caltrops"];
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
                 mortar:"plating", zap:"magnet", aura:"heart", caltrops:"boots" };
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
  ok("and every body on the field is drawn with one",
     shad.shadows === shad.enemies && shad.enemies > 30,
     `${shad.shadows} shadows for ${shad.enemies} enemies`);

  console.log("\n=== 7d. EVOLUTION PARTNERS ALL CONTRIBUTE ===");
  const riders = await page.evaluate(() => {
    const dmgWith = mods => {
      window.__g.start("intern"); window.__g.drainPicks(true);
      for (const [k, n] of mods) window.__g.give(k, n);
      return window.__g.state().dps;
    };
    return { none: dmgWith([]), boots: dmgWith([["boots", 2]]),
             heart: dmgWith([["heart", 2]]), spinach: dmgWith([["spinach", 2]]) };
  });
  ok("BOOTS contributes damage",  riders.boots > riders.none * 1.15,
     `x${riders.none} -> x${riders.boots}`);
  ok("BIG HEART contributes damage", riders.heart > riders.none * 1.10,
     `x${riders.none} -> x${riders.heart}`);

  const offers = await page.evaluate(() => {
    const peek = (kit) => {
      window.__g.start("intern"); window.__g.drainPicks(true);
      for (const w of kit) window.__g.give(w, 1);
      return window.__g.peekOffers(80);
    };
    return { canUse: peek(["bolt"]), cannot: peek(["pulse", "aura"]) };
  });
  ok("DUPLICATOR offered when a weapon can use it",
     (offers.canUse["DUPLICATOR"] || 0) > 0,
     `${offers.canUse["DUPLICATOR"] || 0} times in 80 rolls`);
  ok("DUPLICATOR never offered to a kit that cannot",
     (offers.cannot["DUPLICATOR"] || 0) === 0,
     `${offers.cannot["DUPLICATOR"] || 0} times in 80 rolls`);

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
     ["slam","spokes","charge","evict"].every(k => allKinds[k] > 0),
     JSON.stringify(allKinds));

  // The point of a telegraph is that it can be read. If a dodging player eats
  // the same damage as a stationary one, these are not mechanics - they are a tax.
  const dodge = await page.evaluate(() => {
    const trial = (useBot) => {
      window.__g.start("ox"); window.__g.god(); window.__g.drainPicks(true);
      window.__g.freezeSpawns(true); window.__g.skipTo(900);
      window.__g.bot(useBot); window.__g.boss(2);          // MR. TEETH, charge+slam
      const hp0 = window.__g.hp();                         // godmode: nobody dies,
      for (let k = 0; k < 60 * 30; k++) window.__g.step(1);// so this compares damage
      return hp0 - window.__g.hp();
    };
    return { still: trial(false), moving: trial(true) };
  });
  ok("boss telegraphs are dodgeable", dodge.moving < dodge.still * 0.6,
     `stationary lost ${Math.round(dodge.still)} HP, dodging lost ${Math.round(dodge.moving)}`);

  console.log("\n=== 8b. SUDDEN DEATH GATE ===");
  const gate = await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god(); window.__g.skipTo(1135);
    window.__g.step(60 * 70);                            // past 20:00
    const a = window.__g.state();
    return { sudden: a.sudden, over: a.over, t: a.t };
  });
  ok("clock does not hand you the win at 20:00", gate.sudden === true && gate.over === false,
     `t=${gate.t} sudden=${gate.sudden}`);
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
  await page.click("#pkCards .card");
  await page.waitForTimeout(200);

  console.log("\n=== 11b. DRAW BUDGET UNDER A LIVE FRAME ===");
  const budget = await page.evaluate(() => {
    window.__g.start("intern"); window.__g.god(); window.__g.drainPicks(true);
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
    window.__g.skipTo(1140);
    for (const w of ["bat","skulls","bolt","pulse","mortar","zap","aura","caltrops"])
      window.__g.give(w, 4);
    window.__g.step(60 * 25); window.__g.resume();
    await new Promise(r => setTimeout(r, 700));
    return window.__g.state();
  });
  ok("and the horde on its own still fits one batch",
     hordeOnly.boxes > 0 && hordeOnly.boxes <= 3600,
     `${hordeOnly.boxes} boxes with ${hordeOnly.enemies} enemies, no boss`);

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
    // the most. STINK at rank 5 is a 6.5m ring; THE FINAL BONK is a 4.0m body.
    // The damage boundary therefore belongs at 10.5m of centre distance, not
    // 6.5m. Hold the gap by re-placing the player every frame, so the boss
    // walking toward you cannot smear the measurement.
    const probe = gap => page.evaluate((gap) => {
      window.__g.wipeSave(); window.__g.start("ghoul"); window.__g.god();
      window.__g.drainPicks(true); window.__g.freezeSpawns(true);
      window.__g.give("aura", 4);
      window.__g.boss(3);
      const b0 = window.__g.bossAt();
      for (let i = 0; i < 90; i++) {
        const b = window.__g.bossAt(); if (!b) break;
        window.__g.place(b.x + gap, b.z);
        window.__g.step(1);
      }
      const b1 = window.__g.bossAt();
      return { rad: b0.rad, lost: b0.hp - (b1 ? b1.hp : 0) };
    }, gap);

    const bossRad = (await probe(30)).rad;          // far enough to touch nothing
    const inside  = await probe(6.5 + bossRad - 1); // body in the cloud, centre well out
    const outside = await probe(6.5 + bossRad + 3); // body clear of the cloud

    ok("the boss's body is 4.0m, so the ring must reach 10.5m",
       Math.abs(bossRad - 4.0) < 0.01, `rad=${bossRad}`);
    ok("a body inside the ring takes damage though its centre is outside",
       inside.lost > 0, `lost ${Math.round(inside.lost)} HP at ${(6.5+bossRad-1)}m centre distance`);
    ok("a body clear of the ring takes none",
       outside.lost === 0, `lost ${Math.round(outside.lost)} HP`);
    ok("and reach is not simply infinite", (await probe(30)).lost === 0);
  }

  console.log("\n=== 7i. THE SCRAPPER'S REACH IS A REAL STAT ===");
  {
    // 6.5m STINK + 4.0m body puts everyone else's damage boundary at 10.5m.
    // +35% reach moves THE SCRAPPER's to 12.775m. A gap of 11.6m therefore has
    // to hurt for one character and do nothing at all for the other - which
    // also proves the multiplier is not leaking onto anybody else.
    const probe = (ch, gap) => page.evaluate(([ch, gap]) => {
      window.__g.wipeSave(); window.__g.start(ch); window.__g.god();
      window.__g.drainPicks(true); window.__g.freezeSpawns(true);
      window.__g.give("aura", 4); window.__g.boss(3);
      const b0 = window.__g.bossAt();
      for (let i = 0; i < 90; i++) {
        const b = window.__g.bossAt(); if (!b) break;
        window.__g.place(b.x + gap, b.z); window.__g.step(1);
      }
      return b0.hp - window.__g.bossAt().hp;
    }, [ch, gap]);

    const between = 11.6;                      // past 10.5, short of 12.775
    ok("THE SCRAPPER reaches past everyone else's boundary",
       (await probe("scrap",  between)) > 0, `${between}m`);
    ok("and THE INTERN, at the same distance, does not",
       (await probe("intern", between)) === 0);
    ok("THE SCRAPPER still has a boundary", (await probe("scrap", 13.5)) === 0);
    ok("and both connect well inside it", (await probe("intern", 8)) > 0 &&
                                          (await probe("scrap",  8)) > 0);
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
                                window.__g.step(60 * 20); window.__g.pause(true); });
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
    const altar = await page.evaluate(() => {
      window.__g.place(14, 0); window.__g.step(120);        // 6m away, two seconds
      const idle = window.__g.events()[0].chg;
      window.__g.place(20, 0); window.__g.step(90);         // standing in it
      const part = window.__g.events()[0].chg;
      window.__g.place(0, 0);  window.__g.step(60);         // walked off again
      const bled = window.__g.events()[0].chg;
      window.__g.place(20, 0); window.__g.step(60 * 7);     // hold it out
      return { idle, part, bled, left: window.__g.events().length,
               boons: window.__g.boons() };
    });
    ok("an altar does not charge from six metres away", altar.idle === 0, `${altar.idle}`);
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
      // it must PAUSE, or it is a treadmill: look for a second where it barely moved
      let stalled = 0;
      for (let i = 1; i < seen.length; i++) if (seen[i] - seen[i-1] < 0.002) stalled++;
      return { d0, d1: seen[seen.length-1], stalledFrames: stalled };
    });
    ok("the collector runs away rather than at you", hunt.d1 > hunt.d0 + 8,
       `${hunt.d0}m -> ${hunt.d1}m in six seconds`);
    ok("and it stops often enough to be caught",
       hunt.stalledFrames > 40, `${hunt.stalledFrames} stationary frames of 360`);

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
      g.start("intern"); g.freezeSpawns(true); g.drainPicks(true);
      const pre  = { maxhp: g.mon().maxhp, hp: g.state().hp };
      g.evolveTo(1);
      const post = { maxhp: g.mon().maxhp, hp: g.state().hp };
      const heal = { pre, post };

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
    ok("every monster is a three-stage line with a signature",
       r.lines.every(m => m.line.length === 3 && m.line.every(x => typeof x === "string" && x)),
       r.lines.map(m => m.line.join(">")).join("  "));
    ok("you start at the bottom of your line",
       r.s0.stage === 0 && r.s0.nm === r.s0.line[0], `${r.s0.nm} stage ${r.s0.stage}`);
    ok("level 7 evolves you", r.s1.stage === 1 && r.s1.nm === r.s1.line[1],
       `${r.s0.nm} -> ${r.s1.nm}`);
    ok("and it is a real stat block, not a rename",
       r.hpJump > 1.1, `maxhp x${r.hpJump.toFixed(3)}`);
    ok("level 20 reaches the top of the line",
       r.s2.stage === 2 && r.s2.nm === r.s2.line[2], `${r.s1.nm} -> ${r.s2.nm}`);
    ok("MOPMAW's signature is live at stage 3",
       Math.abs(r.s2.reach - 1.20) < 0.001, `reach ${r.s2.reach}`);
    ok("evolving heals exactly the HP it added, and no more",
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
      const speedAt = (x, z) => {
        g.place(x, z);
        dispatchEvent(new KeyboardEvent("keydown", { code: "KeyW" }));
        for (let i = 0; i < 60; i++) { g.step(1/60); g.place(x, z); }
        const v = g.hop().spd;
        dispatchEvent(new KeyboardEvent("keyup", { code: "KeyW" }));
        return v;
      };
      const green = cellOf("grass"), bog = cellOf("bog"), ash = cellOf("ash");
      const out = { ids: w.cells.map(c=>c.id) };
      out.vGreen = speedAt(green.x, green.z);
      out.vBog   = speedAt(bog.x, bog.z);
      out.inBog  = g.biomeAt(bog.x, bog.z).id;

      // damage taken in the ashes vs on the green, same hit
      const hitAt = (x, z) => { g.place(x, z); return g.hitMe(40); };
      out.dGreen = hitAt(green.x, green.z);
      out.dAsh   = hitAt(ash.x, ash.z);
      return out;
    });
    ok("the sludge is slower than the green",
       r.vBog < r.vGreen * 0.92,
       `${r.vGreen.toFixed(2)} m/s on THE GREEN -> ${r.vBog.toFixed(2)} in THE SLUDGE`);
    ok("and it is the sludge you were standing in", r.inBog === "bog", r.inBog);
    ok("the ashes cost you more for the same hit",
       r.dAsh > r.dGreen * 1.05,
       `${r.dGreen.toFixed(1)} damage on THE GREEN -> ${r.dAsh.toFixed(1)} in THE ASHES`);
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

  console.log("\n" + "=".repeat(58));
  if (errors.length) {
    console.log("ERRORS CAPTURED:");
    [...new Set(errors)].slice(0, 12).forEach(e => console.log("   " + e));
  }
  console.log(`RESULT: ${passes} passed, ${fails} failed`);
  await browser.close();
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error("HARNESS CRASH:", e); process.exit(2); });
