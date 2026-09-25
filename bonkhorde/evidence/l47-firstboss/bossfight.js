// THE FIRST BOSS, PER CHARACTER. Reproduces balance.js's first-tier runs exactly (the same
// setup calls in the same order, stepped the way runOut steps) to 10:00 or death, and
// records the 5:00 boss fight: the health it was sized to, the kit's estimated dps at its
// arrival (kitDps, what sizes it), the player's health going in, how long it took to kill,
// what the player took during it and the trough; and for a run that dies, when, whether a
// boss was up, and the ledger over its last thirty seconds.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde";
const N = +(process.env.N || 24), BASE = +(process.env.BASE || 20260821), UNTIL = +(process.env.UNTIL || 600);
const ARMS = (process.env.ARMS || "twin:clumsy,twin:bench,surge:clumsy,spark:clumsy,intern:clumsy,ox:clumsy").split(",").map(a => a.split(":"));
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + path.join(REPO, "index.html")); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const all = [];
  for(const [ch, player] of ARMS){
    const rows = [];
    for(let i = 0; i < N; i++){
      const seed = BASE + i;
      const r = await pg.evaluate(([ch, player, seed, UNTIL]) => { const g = window.__g, E = (0, eval);
        // balance.js runOne's calls, in its order (first tier: no setUpgrades, no crowd/curve overrides)
        g.wipeSave(); g.noDive(false); g.pin(seed); g.pinRun(seed); g.start(ch);
        g.botHop(true); g.clumsy(player === "clumsy"); g.bot(true);
        const P = () => E("P"), en = E("enemies");
        let boss = null, fight = null, trough = 1, hist = [], nstep = 0;
        while(true){
          const s0 = g.state(); if(s0.over || s0.t >= UNTIL) break;
          g.step(1, 1/60);
          const t = +E("T"), p = P();
          if(!boss){ const bb = en.find(e => e.boss && !e.dead); if(bb && t < 400){ boss = bb;
            fight = { at:+t.toFixed(1), nm:bb.def.nm, hp:Math.round(bb.maxhp), kitDps:Math.round(E("kitDps()")), pHp:Math.round(p.hp), pMax:Math.round(p.maxhp), lvl:p.lvl, h0:g.hurtBy().total, trough:1, killedAt:null, took:null }; } }
          if(fight && fight.killedAt === null){ const f = p.hp / p.maxhp; if(f < fight.trough) fight.trough = f;
            if(boss.dead){ fight.killedAt = +t.toFixed(1); fight.took = +(g.hurtBy().total - fight.h0).toFixed(0); } }
          if(++nstep % 60 === 0){ const hh = g.hurtBy(); hist.push([Math.round(t), hh.contact, hh.spit, hh.hazard]); }
        }
        const s = g.state(), h = g.hurtBy();
        if(fight && fight.killedAt === null) fight.took = +(h.total - fight.h0).toFixed(0);
        const died = s.over && !s.won, tEnd = +s.t;
        // the last thirty seconds' ledger, from the once-a-second history
        let last30 = null; if(died){ const a = hist.filter(x => x[0] <= tEnd - 30).pop() || [0, 0, 0, 0]; last30 = { contact:+(h.contact - a[1]).toFixed(0), spit:+(h.spit - a[2]).toFixed(0), hazard:+(h.hazard - a[3]).toFixed(0) }; }
        const bossUp = en.some(e => e.boss && !e.dead);
        g.clumsy(false);
        return { seed, died, t:+tEnd.toFixed(0), lvl:s.lvl, maxhp:s.maxhp, bossUpAtEnd:bossUp, fight, last30 }; }, [ch, player, seed, UNTIL]);
      rows.push(r); all.push({ ch, player, ...r });
      const f = r.fight;
      console.log(`${ch.padEnd(6)} ${player.padEnd(6)} ${String(seed).slice(-2)} ${r.died ? "DEAD " + String(r.t).padStart(3) + "s" : "alive    "} lvl ${String(r.lvl).padStart(2)} | ${f ? `boss@${f.at} ${f.nm} hp ${f.hp} (kitDps ${f.kitDps}, x${(f.hp / Math.max(1, f.kitDps)).toFixed(0)} s) you ${f.pHp}/${f.pMax} lvl ${f.lvl} -> ${f.killedAt !== null ? "killed in " + (f.killedAt - f.at).toFixed(1) + " s" : "NOT killed"}, took ${f.took}, trough ${(100 * f.trough).toFixed(0)}%` : "no boss by 6:40"}${r.died ? ` | died ${r.bossUpAtEnd ? "WITH A BOSS UP" : "no boss up"}, last 30 s: contact ${r.last30.contact} spit ${r.last30.spit} hazard ${r.last30.hazard}` : ""}`);
    }
    const dead = rows.filter(r => r.died), fights = rows.filter(r => r.fight), killed = fights.filter(r => r.fight.killedAt !== null);
    const med = a => { if(!a.length) return null; const s = a.slice().sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
    console.log(`== ${ch} ${player}: dead before ${UNTIL / 60}:00 ${dead.length}/${rows.length} (${dead.filter(r => r.bossUpAtEnd).length} with a boss up); first boss killed ${killed.length}/${fights.length}, median time to kill ${med(killed.map(r => r.fight.killedAt - r.fight.at))?.toFixed(1)} s, median hp ${med(fights.map(r => r.fight.hp))}, median kitDps ${med(fights.map(r => r.fight.kitDps))}, median taken in the fight ${med(fights.map(r => r.fight.took))} of median max hp ${med(fights.map(r => r.fight.pMax))}, median trough ${(100 * med(fights.map(r => r.fight.trough))).toFixed(0)}%\n`);
  }
  fs.writeFileSync(path.join(__dirname, "bossfight.json"), JSON.stringify(all));
  await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
