// What the WebGL frame holds on this machine: the renderer string, how many of
// the frame's pixels are not black after a render, and what one chipReadFar and a
// three-radius bezelDerive read (chip pixels, noise, gain, stations with px > 0).
const fs = require("fs");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:(process.env.ARGS || "--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist --no-sandbox").split(" ") };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const FILE = process.env.FILE, TAG = process.env.TAG || "";
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.goto("file://" + FILE); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const r = await pg.evaluate(() => {
    const g = window.__g, E = (0, eval);
    g.wipeSave(); g.dev(true); g.pin(11); g.pinRun(11); g.start("intern"); g.god(); g.drainPicks(true); g.freezeEvents(true); g.step(60, 1/60);
    const gl = E("gl"), cv = E("cv");
    const dbg = gl.getExtension("WEBGL_debug_renderer_info");
    const renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    E("render()"); E("render()");
    const w = cv.width, h = cv.height, px = new Uint8Array(w*h*4);
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
    let lit = 0, sum = 0; for(let q = 0; q < px.length; q += 4){ if(px[q] + px[q+1] + px[q+2] > 30) lit++; sum += px[q] + px[q+1] + px[q+2]; }
    const out = { renderer, canvas:`${w}x${h}`, dpr:devicePixelRatio, litShare:+(lit/(w*h)).toFixed(3), meanRGB:+(sum/(w*h*3)).toFixed(1), ctxLost:E("ctxLost"), glError:gl.getError() };
    out.derive = g.onBezelSeed(() => {
      const ids = [...E("silhouetteRegions()")], st = g.bezelStations(ids[0]);
      const one = g.chipReadFar(st[0][0], st[0][1] - 8, 8);
      const d = g.bezelDerive(ids[0], [8, 16, 24], 0, false);
      return { region:ids[0], station:st[0], one:{ off:one.off, on:one.on, now:one.now, noise:one.noise }, rows:d.rows.map(r => ({ r:r.r, n:r.n, gain:r.gain, off:r.off, on:r.on })), reach:d.reach };
    });
    return out;
  });
  console.log(TAG, JSON.stringify(r));
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
