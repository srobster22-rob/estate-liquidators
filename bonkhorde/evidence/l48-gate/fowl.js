// Section 22's GLIMMERFOWL count, alone, on REPO's build with an optional mutant, in a fresh page.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor"); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), page = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; page.on("pageerror", e => errs.push(e.message));
  await page.goto("file://" + TMP, { waitUntil:"load" }); await page.waitForTimeout(700);
  for(let k = 0; k < 3; k++){
    const fowl = await page.evaluate(async () => {
      const g = window.__g, E = (0, eval);
      const frame = () => new Promise(res => requestAnimationFrame(() => res()));
      const settle = async () => { await frame(); await frame(); return g.state().boxes; };
      g.wipeSave(); g.start("ox"); g.god(); g.freezeSpawns(true); g.freezeEvents(true);
      g.drainPicks(true); g.setShake(0); g.place(0, 0);
      g.pause(true);
      const bare = await settle();
      g.spawn("collector", 3, 8); g.step(1/60);
      const withFowl = await settle();
      const birds = E("enemies").filter(e => e.type === "collector").map(e => ({ d:+Math.hypot(e.x - E("P").x, e.z - E("P").z).toFixed(1), y:+e.y.toFixed(2), py:e.py, sz:e.sz, lf:e.lf, pH:e.pH, pt2:e.pt2, hd:e.hd, gt:e.gt, amp:e.amp, bt:!!e.bt }));
      g.pause(false);
      return { bare, withFowl, per:(withFowl - bare) / 3, birds };
    });
    console.log(`${MUT || "clean"} try ${k}: ${fowl.per.toFixed(1)} boxes a bird (bare ${fowl.bare}, with ${fowl.withFowl}); birds ${JSON.stringify(fowl.birds)}`);
  }
  console.log("errors:", errs.slice(0, 3).join(" | ") || "none");
  fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
