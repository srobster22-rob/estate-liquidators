// DOES A WARM PAGE HIDE THE ALLOCATION? The section-101 measurement (seed 9 god bot, settle
// to t=300, V8's sampling heap profiler around 600 steps) taken two ways on REPO's build
// with an optional mutant: COLD, in a fresh page (what section101.js did), and WARM, in a
// page that first plays a whole run to t=WARMT so every hot function has reached its top
// tier before the same settle and the same 600 steps. JSF adds V8 flags (e.g.
// --no-turbo-escape) to tell escape analysis apart from anything else.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT, WARMT = +(process.env.WARMT || 900);
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"].concat(process.env.JSF ? ["--js-flags=" + process.env.JSF] : []) };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor " + (src.split(m.from).length - 1)); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
const measure = async (b, warm) => {
  const pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  if(warm) await pg.evaluate((WARMT) => { const g = window.__g; g.wipeSave(); g.dev(true); g.pin(9); g.pinRun(9);
    g.start("intern"); g.god(); g.drainPicks(true); g.bot(true); let guard = 0; while(g.state().t < WARMT && guard++ < 400000) g.step(30, 1/60); }, WARMT);
  await pg.evaluate(() => { const g = window.__g; g.wipeSave(); g.dev(true); g.pin(9); g.pinRun(9);
    g.start("intern"); g.god(); g.drainPicks(true); g.bot(true); let guard = 0; while(g.state().t < 300 && guard++ < 200000) g.step(30, 1/60); });
  const cdp = await pg.context().newCDPSession(pg);
  await cdp.send("HeapProfiler.enable");
  await cdp.send("HeapProfiler.startSampling", { samplingInterval:16384, includeObjectsCollectedByMajorGC:true, includeObjectsCollectedByMinorGC:true });
  await pg.evaluate(() => window.__g.step(600, 1/60));
  const { profile } = await cdp.send("HeapProfiler.stopSampling");
  const self = new Map(), under = new Map(); let total = 0;
  const walk = (node, parent) => { const f = node.callFrame.functionName || "(anon)"; if(node.selfSize){ total += node.selfSize; self.set(f, (self.get(f) || 0) + node.selfSize); const k = parent + " < " + f; under.set(k, (under.get(k) || 0) + node.selfSize); } for(const c of node.children || []) walk(c, f); };
  walk(profile.head, "");
  const same = await pg.evaluate(() => { const E = (0, eval); return E("nearestCells(0, 0) === nearestCells(5, 5)"); });
  await pg.close();
  const KB = x => (x / 1024).toFixed(0), at = n => self.get(n) || 0;
  return `nearestCells ${KB(at("nearestCells"))} KB, groundY ${KB(at("groundY"))} KB, biomeAt ${KB(at("biomeAt"))} KB, confineIn ${KB(at("confineIn"))} KB, confine ${KB(at("confine"))} KB, botVector<next ${KB(under.get("botVector < next") || 0)} KB, step total ${KB(total / 600)} KB/step; same array twice: ${same}`;
};
(async()=>{
  const b = await chromium.launch(L);
  const tag = `${MUT || "clean"}${process.env.JSF ? " [" + process.env.JSF + "]" : ""}`;
  console.log(`${tag.padEnd(48)} COLD: ${await measure(b, false)}`);
  console.log(`${tag.padEnd(48)} WARM: ${await measure(b, true)}`);
  fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
