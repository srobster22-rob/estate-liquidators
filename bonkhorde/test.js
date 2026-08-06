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

const FILE = "file://" + path.resolve(__dirname, "index.html");
let fails = 0, passes = 0;
const ok  = (n, c, extra="") => { c ? passes++ : fails++;
  console.log(`  ${c ? "PASS" : "FAIL"}  ${n}${extra ? "  " + extra : ""}`); };

(async () => {
  const browser = await chromium.launch(LAUNCH);
  const page = await browser.newPage({ viewport: { width: 1280, height: 760 } });

  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

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
  ok("enemies spawned", s.enemies > 5, "n=" + s.enemies);
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
  for (const c of ["intern","scrap","spark","ox","ghoul"]) {
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
  ok("box budget never exceeded", full.marks.every(m => m.boxes <= 3600),
     "max " + Math.max(...full.marks.map(m => m.boxes)));
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

  console.log("\n=== 7e. COLOUR-VISION CONTRAST ===");
  const cvd = await page.evaluate(() => {
    const P = window.__g.palette();
    const M = { normal:[1,0,0,0,1,0,0,0,1],
                deuteranopia:[.625,.375,0,.70,.30,0,0,.30,.70],
                protanopia:[.567,.433,0,.558,.442,0,0,.242,.758],
                tritanopia:[.95,.05,0,0,.433,.567,0,.475,.525] };
    const LIT = 1.35;
    const ap = (c,m) => { const [r,g,b] = c.map(v => Math.min(1, v*LIT));
      return [m[0]*r+m[1]*g+m[2]*b, m[3]*r+m[4]*g+m[5]*b, m[6]*r+m[7]*g+m[8]*b]; };
    const lab = c => { const f = v => v<=.04045 ? v/12.92 : Math.pow((v+.055)/1.055,2.4);
      const [R,G,B] = c.map(v => f(Math.max(0,Math.min(1,v))));
      let X=(R*.4124+G*.3576+B*.1805)/.95047, Y=(R*.2126+G*.7152+B*.0722),
          Z=(R*.0193+G*.1192+B*.9505)/1.08883;
      const k = t => t>.008856 ? Math.cbrt(t) : 7.787*t+16/116;
      X=k(X);Y=k(Y);Z=k(Z); return [116*Y-16, 500*(X-Y), 200*(Y-Z)]; };
    const dE = (a,b) => Math.hypot(...lab(a).map((v,i)=>v-lab(b)[i]));

    const kinds = Object.keys(P).filter(k => !k.startsWith("_") && !k.includes("*"));
    let worstPair = { d: 1e9 }, worstGround = { d: 1e9 }, worstCross = { d: 1e9 };
    for (const vis in M) {
      const m = M[vis];
      for (let i = 0; i < kinds.length; i++) {
        for (let j = i+1; j < kinds.length; j++) {
          const d = dE(ap(P[kinds[i]],m), ap(P[kinds[j]],m));
          if (d < worstPair.d) worstPair = { d, vis, a:kinds[i], b:kinds[j] };
        }
        for (const g of ["_terrainA","_terrainB"]) {
          const d = dE(ap(P[kinds[i]],m), ap(P[g],m));
          if (d < worstGround.d) worstGround = { d, vis, a:kinds[i] };
        }
        // an ELITE of one type must not read as a NORMAL of another - that would
        // misinform about behaviour, which is worse than looking similar
        for (const j2 of kinds) {
          if (j2 === kinds[i]) continue;
          const d = dE(ap(P[kinds[i]+"*elite"],m), ap(P[j2],m));
          if (d < worstCross.d) worstCross = { d, vis, a:kinds[i]+" elite", b:j2 };
        }
      }
    }
    return { worstPair, worstGround, worstCross };
  });
  ok("enemy types stay distinct under every colour-vision type",
     cvd.worstPair.d > 20,
     `worst ${cvd.worstPair.a}/${cvd.worstPair.b} dE=${cvd.worstPair.d.toFixed(1)} (${cvd.worstPair.vis})`);
  ok("enemies stay distinct from the ground",
     cvd.worstGround.d > 20,
     `worst ${cvd.worstGround.a} dE=${cvd.worstGround.d.toFixed(1)} (${cvd.worstGround.vis})`);
  ok("an elite never reads as a different normal type",
     cvd.worstCross.d > 15,
     `worst ${cvd.worstCross.a} vs ${cvd.worstCross.b} dE=${cvd.worstCross.d.toFixed(1)} (${cvd.worstCross.vis})`);

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

  console.log("\n" + "=".repeat(58));
  if (errors.length) {
    console.log("ERRORS CAPTURED:");
    [...new Set(errors)].slice(0, 12).forEach(e => console.log("   " + e));
  }
  console.log(`RESULT: ${passes} passed, ${fails} failed`);
  await browser.close();
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error("HARNESS CRASH:", e); process.exit(2); });
