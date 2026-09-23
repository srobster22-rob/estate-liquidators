// L37 measurement, v2: the WALL OF NUMBERS measured over the REAL loop. L35's
// protocol (seed-9 god bot, crowd on), and at each station 120 frames of the
// real loop - a step and a painted frame, sixty a second - with every frame
// measured off what that frame drew:
//   drawn    numbers on screen (base: every live number; L37: what numPlace placed)
//   illeg    share of drawn numbers more than 35% covered by other numbers
//   cover    share of the screen under a number (4 px grid union)
//   bodies   bodies on screen, and the share whose centre sits under a number
// Means over the 120 frames, so one frame's camera cannot decide the row.
const fs = require("fs");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const FILE = process.env.FILE, OUT = process.env.OUT, ON = process.env.ON !== "0", SEED = +(process.env.SEED || 9);
const TS = (process.env.TS || "180,420,720,1020").split(",").map(Number);
const CH = process.env.CH || "intern", TAG = process.env.TAG || (ON ? "on" : "off");
// ARM: "l37" (the build as shipped), "wall" (the L37 build with its three number knobs
// flipped back - the pre-L37 wall over the same sim), or "base" (a pre-L37 build)
const ARM = process.env.ARM || "l37";
// THE FRAME THAT IS SHOWN: one fixed frame of the measured window (the same index in
// every arm - the sim is identical), composed off the two canvases the moment it is
// drawn. A screenshot after the window caught whatever its last frame was, and at
// 17:00 the wall arm last frame was a lull: 2 numbers in the pool against a mean of 38.
const SHOT = +(process.env.SHOT || 60);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:720 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.goto("file://" + FILE); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  await pg.evaluate(({ SEED, ON, CH, ARM }) => { const g = window.__g; g.wipeSave(); g.dev(true); if(g.crowd) g.crowd(ON);
    g.pin(SEED); g.pinRun(SEED); g.start(CH); g.god(); g.drainPicks(false); g.bot(true); g.pause(true);
    if(ARM === "wall"){ g.numSort(false); g.numDepth(false); g.numJump(true); } }, { SEED, ON, CH, ARM });
  const rows = [];
  for(const t of TS){
    await pg.evaluate((t) => { const g = window.__g; let guard = 0;
      while(g.state().t < t - 3 && !g.state().over && guard++ < 400000) g.step(60, 1/60); g.pause(true); }, t);
    const r = await pg.evaluate((SHOT) => {
      const E = (0, eval), g = window.__g, N = E("nums"), P0 = Array.prototype.push;
      const g2 = E("g2"), project = E("project"), enemies = E("enemies"), ui = E("ui");
      const L37 = E("typeof numLast") !== "undefined" && E("NUM_SORT_ON");
      let push = 0, crit = 0;
      N.push = function(...a){ for(const o of a){ push++; if(o.crit) crit++; } return P0.apply(this, a); };
      const area = b => Math.max(0, b[2]-b[0]) * Math.max(0, b[3]-b[1]);
      const inter = (a, c) => Math.max(0, Math.min(a[2], c[2]) - Math.max(a[0], c[0])) * Math.max(0, Math.min(a[3], c[3]) - Math.max(a[1], c[1]));
      const acc = { frames:0, drawn:0, drawnMax:0, illeg:0, cover:0, onScr:0, under:0, alive:0, crits:0 };
      // a second of real loop first, so the chase camera is where play puts it
      // THE CAMERA A PLAYER POINTS: the bot steers in world space and leaves camYaw
      // alone, so its chase camera stares one way while the crowd it runs into
      // arrives in front of IT. A player steers with the camera; this eases the yaw
      // toward the heading, a player's pace (the same code runs in every arm).
      const look = ()=> E("if(Math.hypot(P.vx, P.vz) > .5) camYaw += wrapAng(Math.atan2(P.vx, P.vz) - camYaw) * .08");
      for(let i = 0; i < 90; i++){ g.step(1, 1/60); look(); E("render()"); }
      push = 0; crit = 0;
      let shotURL = null, shotDrawn = -1, shotIlleg = -1;
      for(let i = 0; i < 120; i++){
        g.step(1, 1/60); look(); E("render()");
        const shootNow = i === SHOT;
        const W = ui.width, H = ui.height, boxes = [];
        let cr = 0; const crs = [];
        if(L37) for(const L of E("numLast")){ boxes.push(L.box); crs.push(!!L.n.crit); }
        else for(const n of E("nums")){
          const s = project(n.x, n.y, n.z); if(!s) continue;
          const heft = n.crit ? 22 : Math.min(20, 13 + Math.log10(Math.max(1, +n.v)) * 3.4);
          g2.font = `${n.crit ? 800 : 700} ${heft.toFixed(0)}px ui-monospace,Menlo,monospace`;
          const txt = n.heal ? "+" + n.v : String(n.v), w = g2.measureText(txt).width + (n.crit ? 5 : 4);
          boxes.push([s[0] - w/2, s[1] - heft*.78 - 2, s[0] + w/2, s[1] + heft*.12 + 2]); crs.push(!!n.crit);
        }
        const vis = b => !(b[2] < 0 || b[0] > W || b[3] < 0 || b[1] > H), on = boxes.filter(vis);
        boxes.forEach((b, i) => { if(vis(b) && crs[i]) cr++; });   // crits among what is ON screen
        let il = 0;
        for(let i2 = 0; i2 < on.length; i2++){ let o = 0; for(let j = 0; j < on.length; j++) if(j !== i2) o += inter(on[i2], on[j]);
          if(o > .35 * area(on[i2])) il++; }
        const C = 4, gw = Math.ceil(W/C), gh = Math.ceil(H/C), grid = new Uint8Array(gw*gh);
        for(const b of on) for(let y = Math.max(0, b[1]/C|0); y <= Math.min(gh-1, b[3]/C|0); y++)
          for(let x = Math.max(0, b[0]/C|0); x <= Math.min(gw-1, b[2]/C|0); x++) grid[y*gw + x] = 1;
        let cells = 0; for(const v of grid) cells += v;
        let os = 0, un = 0;
        for(const e of enemies){ if(e.dead) continue; const s = project(e.x, e.y + e.def.h*e.sz*.5, e.z);
          if(!s || s[0] < 0 || s[0] > W || s[1] < 0 || s[1] > H) continue; os++;
          if(on.some(b => s[0] >= b[0] && s[0] <= b[2] && s[1] >= b[1] && s[1] <= b[3])) un++; }
        if(shootNow){ const gl = [...document.querySelectorAll("canvas")].find(c => c.id !== "ui"), c = document.createElement("canvas");
          c.width = W; c.height = H; const x = c.getContext("2d"); x.drawImage(gl, 0, 0, W, H); x.drawImage(ui, 0, 0, W, H);
          shotURL = c.toDataURL("image/png"); shotDrawn = on.length; shotIlleg = il; }
        acc.frames++; acc.drawn += on.length; acc.drawnMax = Math.max(acc.drawnMax, on.length); acc.illeg += il;
        acc.crits += cr; acc.cover += cells/(gw*gh); acc.onScr += os; acc.under += un; acc.alive += E("nums").length;
      }
      delete N.push; g.pause(true);
      return { t:g.state().t, lvl:g.state().lvl, crit:+E("P.crit").toFixed(2), push:push/2, critShare: push ? crit/push : 0,
               drawn:acc.drawn/acc.frames, drawnMax:acc.drawnMax, drawnCrit: acc.drawn ? acc.crits/acc.drawn : 0, illeg: acc.drawn ? acc.illeg/acc.drawn : 0,
               cover:acc.cover/acc.frames, onScr:acc.onScr/acc.frames, under: acc.onScr ? acc.under/acc.onScr : 0,
               alive:acc.alive/acc.frames, shotURL, shotDrawn, shotIlleg };
    }, SHOT);
    await pg.evaluate(() => { const p = document.getElementById("paused"); if(p) p.style.visibility = "hidden"; });
    if(OUT && r.shotURL) fs.writeFileSync(`${OUT}/${TAG}-t${String(t).padStart(4, "0")}.png`, Buffer.from(r.shotURL.split(",")[1], "base64"));
    console.log(`  frame ${SHOT} of the window: ${r.shotDrawn} numbers drawn, ${r.shotIlleg} of them illegible`); delete r.shotURL;
    const shot = await pg.evaluate(() => { const E = (0, eval); return { pool:E("nums.length"), placed:E("typeof numLast") !== "undefined" ? E("numLast.length") : -1, paused:E("paused"), t:+window.__g.state().t.toFixed(2) }; });
    console.log("  at the shot", JSON.stringify(shot));
    await pg.evaluate(() => { const p = document.getElementById("paused"); if(p) p.style.visibility = ""; });
    rows.push(r);
    console.log(`t ${String(r.t).padStart(6)} lvl ${String(r.lvl).padStart(3)} crit ${r.crit.toFixed(2)} | pushed/s ${r.push.toFixed(0).padStart(4)} crit ${(100*r.critShare).toFixed(0).padStart(3)}% | pool ${r.alive.toFixed(1).padStart(6)} | drawn ${r.drawn.toFixed(1).padStart(6)} max ${String(r.drawnMax).padStart(4)} (${(100*r.drawnCrit).toFixed(0)}% crit) illegible ${(100*r.illeg).toFixed(0).padStart(3)}% cover ${(100*r.cover).toFixed(2)}% | bodies ${r.onScr.toFixed(1).padStart(6)} under a number ${(100*r.under).toFixed(1)}%`);
  }
  if(OUT) fs.writeFileSync(`${OUT}/${TAG}.json`, JSON.stringify(rows, null, 1));
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
