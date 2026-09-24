// THE SOUNDS OF ONE TRIAL: AudioContext state in headless, and how many times each SFX
// fired over one runOut trial (the page's own sfxCount), on FILE with an optional mutant.
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
  const r = await pg.evaluate(() => { const g = window.__g, E = (0, eval); g.wipeSave(); g.pin(999); g.pinRun(555); g.wipeSave(); g.start("intern"); g.bot(true);
    const st0 = E("AC && AC.state"), sr = E("AC && AC.sampleRate"), snd = E("save.sound");
    for(const k in E("sfxCount")) E("sfxCount")[k] = 0;
    const st = g.runOut(); const c = Object.assign({}, E("sfxCount"));
    return { state0:st0, state1:E("AC && AC.state"), sr, snd, res:`${st.t.toFixed(2)}/${st.lvl}/${st.kills}`, counts:Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 8) }; });
  console.log(`${MUT || "clean"}: AC state ${r.state0} -> ${r.state1}, ${r.sr} Hz, save.sound ${r.snd}; trial ${r.res}; sfx: ` + r.counts.map(([k, v]) => `${k} ${v}`).join(", "));
  fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
