// Section 12 of the suite, repeated as a probe: the heavy frame's fps on this machine.
const fs = require("fs");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
(async()=>{
  const b = await chromium.launch(L), page = await b.newPage({ viewport:{ width:1280, height:760 } });
  await page.goto("file://" + process.env.FILE, { waitUntil:"load" }); await page.waitForTimeout(700);
  await page.evaluate(() => { const g = window.__g; g.wipeSave(); g.start("intern"); g.god(); g.skipTo(900);
    for(const w of ["bat","skulls","bolt","pulse","mortar","zap"]) g.give(w, 4);
    g.spawn("shambler", 200); g.spawn("skitter", 150); g.boss(2); });
  await page.waitForTimeout(1600);
  for(let k = 0; k < 3; k++){
    const perf = await page.evaluate(async () => { let frames = 0; const t0 = performance.now();
      await new Promise(r => { const tick = () => { frames++; performance.now() - t0 < 1500 ? requestAnimationFrame(tick) : r(); }; requestAnimationFrame(tick); });
      const s = window.__g.state(); return { fps:+(frames / ((performance.now() - t0) / 1000)).toFixed(1), enemies:s.enemies, boxes:s.boxes }; });
    console.log(`take ${k+1}: ~${perf.fps} fps with ${perf.enemies} enemies, ${perf.boxes} boxes`);
  }
  // and the bare cost of one render + readPixels, the unit chipReadFar spends
  const rp = await page.evaluate(() => { const E = (0, eval), gl = E("gl"), cv = E("cv"), px = new Uint8Array(cv.width*cv.height*4);
    E("render()"); gl.readPixels(0,0,cv.width,cv.height,gl.RGBA,gl.UNSIGNED_BYTE,px);
    const t0 = performance.now(); for(let i = 0; i < 10; i++){ E("render()"); gl.readPixels(0,0,cv.width,cv.height,gl.RGBA,gl.UNSIGNED_BYTE,px); }
    const tr = performance.now(); for(let i = 0; i < 10; i++) E("render()"); const t1 = performance.now();
    return { renderReadMs:Math.round((tr - t0)/10), renderOnlyMs:Math.round((t1 - tr)/10) }; });
  console.log("heavy frame: render+readPixels", rp.renderReadMs, "ms, render alone (no sync)", rp.renderOnlyMs, "ms");
  await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
