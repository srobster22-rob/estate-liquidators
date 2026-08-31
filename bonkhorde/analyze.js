// Model integrity report. For every one of the 21 player forms, capture the
// exact boxes its body plan emits and answer two questions the eye keeps
// asking and the suite could not:
//
//   1. is the animal ONE object? boxes that overlap nobody are floating parts,
//      and a set of parts that only touch their neighbours through a hairline
//      reads as a chain of separate objects rather than as a body.
//   2. where are the WEAK joints? two parts that overlap by less than a
//      couple of hundredths are a seam waiting to open, and the draw-index
//      nudge in mb() moves every box by up to .008 on each axis, which is
//      enough to pull a kissing pair apart on its own.
//
// Usage: node analyze.js [minOverlap]
const fs = require("fs"), path = require("path");
function loadPlaywright(){
  for(const p of ["playwright", "/opt/node22/lib/node_modules/playwright"]){
    try { return require(p); } catch(e) {}
  }
  process.exit(2);
}
const { chromium } = loadPlaywright();
const LAUNCH = { args:["--use-gl=angle","--use-angle=swiftshader",
  "--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"])
  if(fs.existsSync(p)) LAUNCH.executablePath = p;

const MIN = +(process.argv[2] || 0);

(async () => {
  const b = await chromium.launch(LAUNCH);
  const page = await b.newPage({ viewport:{ width:1000, height:700 } });
  page.on("pageerror", e => console.log("PAGEERROR", e.message));
  await page.goto("file://" + path.resolve(__dirname, "index.html"), { waitUntil:"load" });
  const out = await page.evaluate(async (MIN) => {
    const g = window.__g;
    const frame = () => new Promise(r => requestAnimationFrame(() => r()));
    // ONE analysis, two rosters. Player forms and horde bodies capture into the
    // same six-number layout - (r, f, y) local, then half-extents in (x, z, y)
    // order - so the union-find below does not care which it was handed.
    const analyse = (bx) => {
      const n = bx.length/6, P = i => bx.slice(i*6, i*6+6);
      const ov = (A,B,k) => Math.min(A[k]+A[k+3], B[k]+B[k+3])
                          - Math.max(A[k]-A[k+3], B[k]-B[k+3]);
      const par = Array.from({length:n}, (_,i)=>i);
      const find = a => { while(par[a]!==a){ par[a]=par[par[a]]; a=par[a]; } return a; };
      const uni  = (a,b)=>{ a=find(a); b=find(b); if(a!==b) par[b]=a; };
      const deg = new Array(n).fill(0);
      let weak = 0;
      for(let i=0;i<n;i++) for(let j=i+1;j<n;j++){
        const A=P(i), B=P(j);
        const o = Math.min(ov(A,B,0), ov(A,B,1), ov(A,B,2));
        if(o > MIN){ uni(i,j); deg[i]++; deg[j]++; if(o < .02) weak++; }
      }
      const roots = {};
      for(let i=0;i<n;i++){ const r = find(i); (roots[r] = roots[r] || []).push(i); }
      const groups = Object.values(roots).sort((a,b)=>b.length-a.length);
      const loose = groups.slice(1);
      return { n, comps: groups.length, biggest: groups[0] ? groups[0].length : 0, weak,
               orphans: deg.filter(d=>d===0).length,
               stray: loose.slice(0,3).map(gp => {
                 const A = P(gp[0]);
                 let best = null;
                 for(const m of groups[0]){
                   const B = P(m);
                   const g3 = [ov(A,B,0), ov(A,B,1), ov(A,B,2)];
                   const score = -Math.min(...g3);
                   if(!best || score < best.score) best = { score, m, g3, B };
                 }
                 return `${gp.length}@(${A[0].toFixed(2)},${A[1].toFixed(2)},${A[2].toFixed(2)})` +
                   `sz(${A[3].toFixed(3)},${A[4].toFixed(3)},${A[5].toFixed(3)})i${gp[0]}` +
                   (best ? ` | nearest i${best.m}@(${best.B[0].toFixed(2)},${best.B[1].toFixed(2)},${best.B[2].toFixed(2)})` +
                     `sz(${best.B[3].toFixed(3)},${best.B[4].toFixed(3)},${best.B[5].toFixed(3)})` +
                     ` ov[${best.g3.map(v=>v.toFixed(4)).join(",")}]` : "");
               }) };
    };
    const res = [], hordeRes = [];
    for(const ch of g.chars()) for(const st of [0,1,2,3,4]){
      g.wipeSave(); g.start(ch); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true); g.place(0,0);
      if(st) g.evolveTo(st);
      g.resume(); g.capturePos();
      await frame(); await frame();
      const bx = g.posOut();
      if(!bx){ res.push({ ch, st, nm:"?", n:0, comps:-1 }); continue; }
      res.push(Object.assign({ ch, st, nm: g.stageNm() }, analyse(bx)));
    }
    // ---- THE HORDE. Six trash bodies and four bosses, each spawned alone and
    // close enough to draw at full detail, because a body plan that only comes
    // apart at LOD 2 is still a body plan that comes apart.
    g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
    g.drainPicks(true); g.setShake(0); g.place(0,0); g.aim(0);
    // DISARMED, same fix the suite's own horde section already carries: THE
    // OX starts with PULSE, the balance arc widened it, and a live weapon on
    // the observer means the subject can be dead before it is captured - the
    // "-1 parts of 0 boxes" rows are exactly that, not broken bodies.
    g.disarm();
    g.step(20, 1/60);
    // SIX PHASES, and the worst one is the answer. Sway, tail lag and wing flap
    // all move parts relative to each other, so "is it one object" is a question
    // about the animation, not about whichever frame the report happened to
    // catch - two bodies passed a single-frame check and came apart elsewhere in
    // their own cycle. The clock is advanced with the field EMPTY and the body
    // respawned for each sample, because running the enemy for 240 frames walks
    // it out of full detail or lets the player's own weapon kill it.
    const worstOf = async (spawn) => {
      let out = null;
      for(let ph=0; ph<6; ph++){
        g.clearEnemies();
        g.step(40, 1/60);
        spawn();
        g.step(3, 1/60);
        g.resume(); g.captureEnemy();
        await frame(); await frame();
        const bx = g.enemyPos();
        if(!bx) return { n:0, comps:-1, stray:[], weak:0 };
        const a = analyse(bx);
        if(!out || a.comps > out.comps) out = a;
      }
      return out;
    };
    // WHAT IS DELIBERATELY NOT HERE, because an open question that keeps coming
    // back costs more than the answer written down:
    //   - THE ELITE CROWN. Four boxes that orbit the head, drawn with box() in
    //     world space AFTER the capture closes, so they never enter this
    //     analysis. That is correct rather than a gap: a crown is supposed to
    //     float clear of the animal, and a connectivity report that demanded it
    //     touch the skull would be asking for the wrong thing.
    //   - DEN PACK BODIES. A den spawns through spawnEnemy(K.den, ...) with the
    //     same five kinds listed below and one change, maxhp * 1.25. Same body
    //     plan, same boxes; running them again would re-measure these rows.
    const mobs = ["shambler","runner","brute","spitter","skitter","collector"];
    for(const k of mobs)
      hordeRes.push(Object.assign({ ch:k, st:"", nm:k.toUpperCase() },
        await worstOf(()=>{ g.place(0,0); g.spawnAt(k, 0, 7); })));
    for(let bi=0; bi<4; bi++){
      let nm = "boss" + bi;
      const r2 = await worstOf(()=>{
        g.boss(bi); g.step(1/60);
        const b = g.bossAt();
        if(b){ nm = b.nm; g.place(b.x - 9, b.z); g.step(120, 1/60); }
      });
      hordeRes.push(Object.assign({ ch:"boss"+bi, st:"", nm }, r2));
    }
    return { res, hordeRes };
  }, MIN);

  const report = (rows, title) => {
    let bad = 0;
    console.log(`\n  ${title}`);
    console.log("  FORM                    boxes  parts  loose  weak-joints");
    for(const r of rows){
      if(r.comps > 1 || r.comps === -1) bad++;
      const flag = r.comps > 1 ? "  <-- " + (r.stray||[]).join(" ") : "";
      console.log(`  ${(r.ch+" "+r.st).padEnd(12)}${(r.nm||"").padEnd(14)}` +
                  `${String(r.n).padStart(4)}${String(r.comps).padStart(7)}` +
                  `${String(r.comps-1).padStart(7)}${String(r.weak).padStart(8)}${flag}`);
    }
    console.log(`\n  ${bad} of ${rows.length} are not a single connected object`);
    return bad;
  };
  console.log(`\n  min overlap to count as joined: ${MIN}`);
  const badP = report(out.res, "PLAYER FORMS");
  const badH = report(out.hordeRes, "THE HORDE");
  console.log(`\n  TOTAL: ${badP + badH} of ${out.res.length + out.hordeRes.length} broken\n`);
  await b.close();
})();
