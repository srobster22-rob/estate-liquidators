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
    const res = [];
    for(const ch of g.chars()) for(const st of [0,1,2,3]){
      g.wipeSave(); g.start(ch); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true); g.place(0,0);
      if(st) g.evolveTo(st);
      g.resume(); g.capturePos();
      await frame(); await frame();
      const bx = g.posOut();
      if(!bx){ res.push({ ch, st, nm:"?", n:0, comps:-1 }); continue; }
      const n = bx.length/6, P = i => bx.slice(i*6, i*6+6);
      const ov = (A,B,k) => Math.min(A[k]+A[k+3], B[k]+B[k+3])
                          - Math.max(A[k]-A[k+3], B[k]-B[k+3]);
      // union-find over "these two boxes actually share volume"
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
      res.push({ ch, st, nm: g.stageNm(), n, comps: groups.length,
                 biggest: groups[0].length, weak,
                 orphans: deg.filter(d=>d===0).length,
                 stray: loose.slice(0,3).map(gp => {
                   const A = P(gp[0]);
                   // nearest box in the main group, and which axis fails
                   let best = null;
                   for(const m of groups[0]){
                     const B = P(m);
                     const g3 = [ov(A,B,0), ov(A,B,1), ov(A,B,2)];
                     const worstAx = g3.indexOf(Math.min(...g3));
                     const score = -Math.min(...g3);
                     if(!best || score < best.score)
                       best = { score, m, g3, B, worstAx };
                   }
                   return `${gp.length}@(${A[0].toFixed(2)},${A[1].toFixed(2)},${A[2].toFixed(2)})` +
                     `sz(${A[3].toFixed(3)},${A[4].toFixed(3)},${A[5].toFixed(3)})i${gp[0]}` +
                     ` | nearest i${best.m}@(${best.B[0].toFixed(2)},${best.B[1].toFixed(2)},${best.B[2].toFixed(2)})` +
                     `sz(${best.B[3].toFixed(3)},${best.B[4].toFixed(3)},${best.B[5].toFixed(3)})` +
                     ` ov[${best.g3.map(v=>v.toFixed(4)).join(",")}]`;
                 }) });
    }
    return res;
  }, MIN);

  let bad = 0;
  console.log(`\n  min overlap to count as joined: ${MIN}\n`);
  console.log("  FORM                    boxes  parts  loose  weak-joints");
  for(const r of out){
    if(r.comps > 1) bad++;
    const flag = r.comps > 1 ? "  <-- " + r.stray.join(" ") : "";
    console.log(`  ${(r.ch+" st"+r.st).padEnd(12)}${(r.nm||"").padEnd(14)}` +
                `${String(r.n).padStart(4)}${String(r.comps).padStart(7)}` +
                `${String(r.comps-1).padStart(7)}${String(r.weak).padStart(8)}${flag}`);
  }
  console.log(`\n  ${bad} of ${out.length} forms are not a single connected object\n`);
  await b.close();
})();
