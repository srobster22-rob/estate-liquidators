// RUN ONE SECTION OF test.js ALONE: the text from its "=== <SEC>." header to the next
// section header is cut out of REPO/test.js and run against REPO/index.html (MUT applied to a
// temp copy), with the harness names the sections use (page, ok, chromium, LAUNCH, FILE, errors).
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const LAUNCH = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) LAUNCH.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT, SEC = process.env.SEC || "101";
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor " + (src.split(m.from).length - 1)); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
const FILE = "file://" + TMP;
const T = fs.readFileSync(path.join(REPO, "test.js"), "utf8");
const a = T.indexOf(`  console.log("\\n=== ${SEC}. `); if(a < 0) throw new Error("no section " + SEC);
let b = T.indexOf('  console.log("\\n=== ', a + 10); const e2 = T.indexOf('  console.log("\\n" + "=".repeat(58));', a); if(b < 0 || (e2 > 0 && e2 < b)) b = e2;
const body = T.slice(a, b);
let passes = 0, fails = 0; const errors = [];
const ok = (n, c, extra = "") => { c ? passes++ : fails++; console.log(`  ${c ? "PASS" : "FAIL"}  ${n}${extra ? "  " + extra : ""}`); };
(async()=>{
  const browser = await chromium.launch(LAUNCH), page = await browser.newPage({ viewport:{ width:1280, height:760 } });
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  await page.goto(FILE, { waitUntil:"load" }); await page.waitForTimeout(700);
  const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
  const t0 = Date.now();
  await new AsyncFunction("page", "ok", "chromium", "LAUNCH", "FILE", "errors", body)(page, ok, chromium, LAUNCH, FILE, errors);
  console.log(`${MUT || "clean"} section ${SEC}: ${passes} passed, ${fails} failed in ${((Date.now() - t0) / 1000).toFixed(0)} s${errors.length ? "; errors " + errors.slice(0, 2).join(" | ") : ""}`);
  fs.unlinkSync(TMP); await browser.close(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(2); });
