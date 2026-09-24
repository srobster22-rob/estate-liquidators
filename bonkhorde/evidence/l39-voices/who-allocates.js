// (memprobe10 in the round) WHO MAKES THE BACKING STORES: typed-array / ArrayBuffer constructors and the canvas and
// audio buffer makers wrapped in the page, bytes counted per allocating stack (every 32nd
// call's stack, weighted), over one runOut trial under a mutant.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor"); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, "_hang." + process.pid + ".html"); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.pin(999); g.pinRun(555);
    const T = window.__alloc = { n:0, bytes:0, sites:new Map() };
    const note = (kind, bytes) => { T.n++; T.bytes += bytes; if(T.n % 32) return;
      const st = (new Error().stack || "").split("\n").slice(2, 5).map(l => l.trim().replace(/^at /, "").replace(/\(?file:.*?:(\d+):\d+\)?/, ":$1")).join(" < ");
      const k = kind + " @ " + st; const e = T.sites.get(k) || { n:0, bytes:0 }; e.n += 32; e.bytes += bytes * 32; T.sites.set(k, e); };
    for(const name of ["Float32Array","Float64Array","Uint8Array","Uint8ClampedArray","Uint16Array","Uint32Array","Int8Array","Int16Array","Int32Array"]){
      const O = window[name]; const W = function(...a){ const o = new O(...a); note(name, o.byteLength); return o; };
      W.prototype = O.prototype; Object.defineProperty(W, "name", { value:name }); W.BYTES_PER_ELEMENT = O.BYTES_PER_ELEMENT; W.from = O.from.bind(O); W.of = O.of.bind(O); window[name] = W; }
    { const O = window.ArrayBuffer; const W = function(...a){ const o = new O(...a); note("ArrayBuffer", o.byteLength); return o; }; W.prototype = O.prototype; W.isView = O.isView; window.ArrayBuffer = W; }
    const C2 = CanvasRenderingContext2D.prototype;
    for(const m of ["getImageData","createImageData"]){ const o = C2[m]; C2[m] = function(...a){ const r = o.apply(this, a); note("2d." + m, r.data ? r.data.byteLength : 0); return r; }; }
    if(window.AudioContext){ const o = AudioContext.prototype.createBuffer; AudioContext.prototype.createBuffer = function(...a){ const r = o.apply(this, a); note("audio.createBuffer", r.length * r.numberOfChannels * 4); return r; }; }
    if(window.WebGL2RenderingContext){ const o = WebGL2RenderingContext.prototype.readPixels; WebGL2RenderingContext.prototype.readPixels = function(...a){ note("gl.readPixels", a[6] && a[6].byteLength || 0); return o.apply(this, a); }; }
  });
  const t0 = Date.now();
  const res = await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.start("intern"); g.bot(true); const st = g.runOut(); return `${st.t.toFixed(2)}/${st.lvl}/${st.kills}`; });
  const out = await pg.evaluate(() => { const T = window.__alloc; return { n:T.n, mb:+(T.bytes/1048576).toFixed(1), top:[...T.sites.entries()].sort((a, b) => b[1].bytes - a[1].bytes).slice(0, 12).map(([k, v]) => `${(v.bytes/1048576).toFixed(1).padStart(8)} MB  ${String(v.n).padStart(8)} calls  ${k}`) }; });
  console.log(`${MUT || "clean"}: trial ${res} in ${((Date.now()-t0)/1000).toFixed(0)} s - ${out.n} allocations seen, ${out.mb} MB`); for(const l of out.top) console.log("   " + l);
  fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
