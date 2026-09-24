// THE FIRST TEN MINUTES, WITH A WORSE PLAYER. Every character, SEEDS seeds, three players:
// the bench bot (kites perfectly, hops on the frame it lands), the CLUMSY bot (re-decides
// every BOT_LAG s, makes the hop BOT_HOP_ODDS of the time, sees a telegraph BOT_REACT s
// late) and the clumsy bot with the hop off. First tier (no permanent upgrades), no god,
// minute by minute to 10:00 or death: hp at each minute, the hp trough, the damage ledger by
// source per minute, level and kills. What this answers: can a mediocre player lose the
// first ten minutes, and if not, where is the damage NOT arriving?
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde";
const SEEDS = (process.env.SEEDS || "20260821,20260822,20260823").split(",").map(Number), MIN = +(process.env.MIN || 10);
const MODES = (process.env.MODES || "bench,clumsy,clumsy-nohop").split(",");
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + path.join(REPO, "index.html")); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const chars = process.env.CHARS ? process.env.CHARS.split(",") : await pg.evaluate(() => window.__g.chars());
  const rows = [];
  for(const mode of MODES) for(const ch of chars) for(const seed of SEEDS){
    const r = await pg.evaluate(([ch, seed, mode, MIN]) => { const g = window.__g;
      g.wipeSave(); g.pin(seed); g.pinRun(seed); g.start(ch);
      g.botHop(mode !== "clumsy-nohop"); g.clumsy(mode !== "bench"); g.bot(true);
      let h0 = g.hurtBy(), trough = 1, troughAt = 0; const mins = [];
      for(let m = 1; m <= MIN; m++){
        let guard = 0; while(g.state().t < m * 60 && !g.state().over && guard++ < 20000){ g.step(30, 1/60); const s = g.state(); const f = s.hp / s.maxhp; if(f < trough){ trough = f; troughAt = s.t; } }
        const s = g.state(), h = g.hurtBy();
        mins.push({ m, t:+s.t.toFixed(0), hp:+(100 * s.hp / s.maxhp).toFixed(0), lvl:s.lvl, kills:s.kills, contact:+(h.contact - h0.contact).toFixed(0), spit:+(h.spit - h0.spit).toFixed(0), hazard:+(h.hazard - h0.hazard).toFixed(0), over:s.over });
        h0 = h; if(s.over) break;
      }
      const s = g.state(); g.clumsy(false); g.botHop(true);
      return { ch, seed, mode, dead:s.over && !s.won, at:+s.t.toFixed(0), lvl:s.lvl, kills:s.kills, maxhp:s.maxhp, trough:+(100 * trough).toFixed(0), troughAt:+troughAt.toFixed(0), mins }; }, [ch, seed, mode, MIN]);
    rows.push(r);
    const dmg = r.mins.map(x => x.contact + x.spit + x.hazard);
    console.log(`${mode.padEnd(13)} ${ch.padEnd(7)} ${String(seed).slice(-2)}  ${r.dead ? "DEAD " + String(r.at).padStart(3) + "s" : "alive    "}  lvl ${String(r.lvl).padStart(2)} kills ${String(r.kills).padStart(4)}  trough ${String(r.trough).padStart(3)}% at ${String(r.troughAt).padStart(3)}s  hp/min ${r.mins.map(x => String(x.hp).padStart(3)).join(" ")}  dmg/min ${dmg.map(x => String(x).padStart(3)).join(" ")}  (contact ${r.mins.reduce((a, x) => a + x.contact, 0)}, spit ${r.mins.reduce((a, x) => a + x.spit, 0)}, hazard ${r.mins.reduce((a, x) => a + x.hazard, 0)})`);
  }
  console.log("\nSUMMARY per player: deaths before 10:00 / runs, mean hp trough, mean damage per minute by source (0-5 and 5-10)");
  for(const mode of MODES){ const R = rows.filter(r => r.mode === mode); const dead = R.filter(r => r.dead).length;
    const avg = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0;
    const per = (k, lo, hi) => avg(R.map(r => avg(r.mins.filter(x => x.m > lo && x.m <= hi).map(x => x[k]))));
    console.log(`  ${mode.padEnd(13)} dead ${dead}/${R.length}  trough ${avg(R.map(r => r.trough)).toFixed(0)}% (worst ${Math.min(...R.map(r => r.trough))}%)  0-5: contact ${per("contact", 0, 5).toFixed(0)} spit ${per("spit", 0, 5).toFixed(0)} hazard ${per("hazard", 0, 5).toFixed(0)} /min   5-10: contact ${per("contact", 5, 10).toFixed(0)} spit ${per("spit", 5, 10).toFixed(0)} hazard ${per("hazard", 5, 10).toFixed(0)} /min   lvl at end ${avg(R.map(r => r.lvl)).toFixed(1)}`); }
  fs.writeFileSync(path.join(__dirname, "early.json"), JSON.stringify(rows));
  await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
