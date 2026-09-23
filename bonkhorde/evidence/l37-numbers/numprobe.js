// L37 measurement: the WALL OF NUMBERS. Same protocol as L35's frames.js (seed-9 god bot,
// intern, crowd on/off), and at each station it samples two seconds of sim, then one
// paused frame read off the REAL overlay canvas:
//   push/s, crit share of pushes, alive mean/max, alive crit share
//   boxes on screen, illegible share (a box more than 35% covered by other boxes),
//   union coverage of the screen, ink pixels the numbers add to the overlay,
//   and the share of on-screen bodies whose centre sits under a number.
const fs = require("fs");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const FILE = process.env.FILE, OUT = process.env.OUT, ON = process.env.ON !== "0", SEED = +(process.env.SEED || 9);
const TS = (process.env.TS || "180,420,720,1020").split(",").map(Number);
const CH = process.env.CH || "intern";
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:720 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.goto("file://" + FILE); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  await pg.evaluate(({ SEED, ON, CH }) => { const g = window.__g; g.wipeSave(); g.dev(true); if(g.crowd) g.crowd(ON);
    g.pin(SEED); g.pinRun(SEED); g.start(CH); g.god(); g.drainPicks(false); g.bot(true); g.pause(true); }, { SEED, ON, CH });
  const rows = [];
  for(const t of TS){
    await pg.evaluate((t) => { const g = window.__g; let guard = 0;
      while(g.state().t < t - 2 && !g.state().over && guard++ < 400000) g.step(60, 1/60); g.pause(true); }, t);
    const S = await pg.evaluate(() => {
      const E = (0, eval), g = window.__g, N = E("nums");
      const P0 = Array.prototype.push;
      let push = 0, crit = 0, alive = 0, aliveMax = 0, aliveCrit = 0, frames = 0, shown = 0, shownMax = 0;
      N.push = function(...a){ for(const o of a){ push++; if(o.crit) crit++; } return P0.apply(this, a); };
      // THE REAL LOOP: a step and a painted frame, sixty times a second - the L37 build
      // places each number the first frame it is drawn, so a snapshot after two seconds
      // of unpainted steps would ask one frame to place the whole backlog at once
      const L37 = E("typeof numLast") !== "undefined";
      for(let i = 0; i < 120; i++){ g.step(1, 1/60); E("shake = 0; render()"); const n = E("nums"); alive += n.length; aliveMax = Math.max(aliveMax, n.length);
        aliveCrit += n.filter(o => o.crit).length; frames++;
        const sh = L37 ? E("numLast.length") : n.length; shown += sh; shownMax = Math.max(shownMax, sh); }
      delete N.push; g.pause(true);
      return { push:push/2, critShare: push ? crit/push : 0, alive: alive/frames, aliveMax, aliveCritShare: alive ? aliveCrit/alive : 0,
               shown: shown/frames, shownMax,
               crit:+E("P.crit").toFixed(3), lvl:g.state().lvl, t:g.state().t };
    });
    const F = await pg.evaluate(() => {
      const E = (0, eval); E("shake = 0; flash = 0");
      const nums = E("nums"), g2 = E("g2"), project = E("project"), enemies = E("enemies"), ui = E("ui");
      E("render()");
      const W = ui.width, H = ui.height;
      const A = g2.getImageData(0, 0, W, H).data;
      const boxes = [];
      // the L37 build places its own numbers: read what the frame drew
      const placed = E("typeof numLast") !== "undefined" ? E("numLast") : null;
      if(placed) for(const L of placed){ const bx = L.box; if(bx[2] < 0 || bx[0] > W || bx[3] < 0 || bx[1] > H) continue; boxes.push({ b:bx.slice(), crit:!!L.n.crit }); }
      else for(const n of nums){
        const s = project(n.x, n.y, n.z); if(!s) continue;
        const heft = n.crit ? 22 : Math.min(20, 13 + Math.log10(Math.max(1, +n.v)) * 3.4);
        g2.font = `${n.crit ? 800 : 700} ${heft.toFixed(0)}px ui-monospace,Menlo,monospace`;
        const txt = n.heal ? "+" + n.v : String(n.v), w = g2.measureText(txt).width + (n.crit ? 5 : 4);
        const bx = [s[0] - w/2, s[1] - heft*.78 - 2, s[0] + w/2, s[1] + heft*.12 + 2];
        if(bx[2] < 0 || bx[0] > W || bx[3] < 0 || bx[1] > H) continue;
        boxes.push({ b:bx, crit:!!n.crit });
      }
      const area = b => Math.max(0, b[2]-b[0]) * Math.max(0, b[3]-b[1]);
      const inter = (a, c) => Math.max(0, Math.min(a[2], c[2]) - Math.max(a[0], c[0])) * Math.max(0, Math.min(a[3], c[3]) - Math.max(a[1], c[1]));
      let illeg = 0;
      for(let i = 0; i < boxes.length; i++){ let o = 0; for(let j = 0; j < boxes.length; j++) if(j !== i) o += inter(boxes[i].b, boxes[j].b);
        if(o > .35 * area(boxes[i].b)) illeg++; }
      // union on a 4 px grid
      const C = 4, gw = Math.ceil(W/C), gh = Math.ceil(H/C), grid = new Uint8Array(gw*gh);
      for(const { b } of boxes) for(let y = Math.max(0, b[1]/C|0); y <= Math.min(gh-1, b[3]/C|0); y++)
        for(let x = Math.max(0, b[0]/C|0); x <= Math.min(gw-1, b[2]/C|0); x++) grid[y*gw + x] = 1;
      let cells = 0; for(const v of grid) cells += v;
      // bodies under a number
      let onScr = 0, under = 0;
      for(const e of enemies){ if(e.dead) continue; const s = project(e.x, e.y + e.def.h*e.sz*.5, e.z);
        if(!s || s[0] < 0 || s[0] > W || s[1] < 0 || s[1] > H) continue; onScr++;
        if(boxes.some(({ b }) => s[0] >= b[0] && s[0] <= b[2] && s[1] >= b[1] && s[1] <= b[3])) under++; }
      // ink the numbers add, off the overlay itself
      const keep = nums.slice(); nums.length = 0; E("render()");
      const B = g2.getImageData(0, 0, W, H).data;
      Array.prototype.push.apply(nums, keep); E("render()");
      const hid = E("typeof numHidden") !== "undefined" ? E("numHidden") : null;
      let ink = 0; for(let i = 0; i < A.length; i += 4)
        if(Math.abs(A[i]-B[i]) + Math.abs(A[i+1]-B[i+1]) + Math.abs(A[i+2]-B[i+2]) + Math.abs(A[i+3]-B[i+3]) > 24) ink++;
      return { boxes:boxes.length, crits:boxes.filter(x => x.crit).length, illeg, pool:nums.length, cover:cells/(gw*gh), ink:ink/(W*H), onScr, under };
    });
    await pg.evaluate(() => { const p = document.getElementById("paused"); if(p) p.style.visibility = "hidden"; });
    if(OUT) await pg.screenshot({ path:`${OUT}/${ON ? "on" : "off"}-t${String(t).padStart(4, "0")}.png` });
    await pg.evaluate(() => { const p = document.getElementById("paused"); if(p) p.style.visibility = ""; });
    const r = { ...S, ...F }; rows.push(r);
    console.log(`t ${String(r.t).padStart(6)} lvl ${String(r.lvl).padStart(3)} crit ${r.crit.toFixed(2)} | push/s ${r.push.toFixed(0).padStart(5)} crit ${(100*r.critShare).toFixed(0).padStart(3)}% | alive ${r.alive.toFixed(1).padStart(6)} max ${String(r.aliveMax).padStart(4)} crit ${(100*r.aliveCritShare).toFixed(0).padStart(3)}% | drawn ${r.shown.toFixed(1).padStart(5)} max ${String(r.shownMax).padStart(3)} | on screen ${String(r.boxes).padStart(4)} illegible ${r.boxes ? (100*r.illeg/r.boxes).toFixed(0) : "-"}% cover ${(100*r.cover).toFixed(2)}% ink ${(100*r.ink).toFixed(2)}% | bodies ${r.onScr} under ${r.under} (${r.onScr ? (100*r.under/r.onScr).toFixed(0) : "-"}%)`);
  }
  if(OUT) fs.writeFileSync(`${OUT}/${ON ? "on" : "off"}.json`, JSON.stringify(rows, null, 1));
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
