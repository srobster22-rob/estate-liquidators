// RUN SECTION 101 ALONE, exactly as test.js has it: the section's text is cut out of
// REPO/test.js and run against REPO/index.html (with MUT applied to a temp copy).
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor " + (src.split(m.from).length - 1)); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
const T = fs.readFileSync(path.join(REPO, "test.js"), "utf8");
const a = T.indexOf('  console.log("\\n=== 101.'), b = T.indexOf('  console.log("\\n" + "=".repeat(58));', a);
if(a < 0 || b < 0) throw new Error("section 101 not found"); const body = T.slice(a, b);
let passes = 0, fails = 0; const ok = (n, c, extra = "") => { c ? passes++ : fails++; console.log(`  ${c ? "PASS" : "FAIL"}  ${n}${extra ? "  " + extra : ""}`); };
(async()=>{
  const browser = await chromium.launch(L), page = await browser.newPage({ viewport:{ width:1280, height:760 } });
  await page.goto("file://" + TMP, { waitUntil:"load" }); await page.waitForTimeout(700);
  const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
  const t0 = Date.now();
  await new AsyncFunction("page", "ok", body)(page, ok);
  console.log(`${MUT || "clean"}: ${passes} passed, ${fails} failed in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  fs.unlinkSync(TMP); await browser.close(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(2); });
