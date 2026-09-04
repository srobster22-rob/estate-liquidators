// run ONE section of bonkhorde/test.js on its own: node sec.js 35
// The section is sliced out of test.js by its banner and evaluated with the
// same page/ok/errors the suite gives it, so what passes here is the text
// that will run in the suite - not a copy of it.
const fs=require("fs"), path=require("path");
const {chromium}=(()=>{ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try { return require(p); } catch(e){} } console.error("playwright not found"); process.exit(2); })();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const DIR = path.resolve(__dirname, "..");
const N = process.argv[2] || "35";
const src = fs.readFileSync(path.join(DIR, "test.js"), "utf8");
const lines = src.split("\n");
const a = lines.findIndex(l => l.includes(`=== ${N}. `));
if(a < 0){ console.log("no section", N); process.exit(2); }
let b = lines.findIndex((l, i) => i > a && (/^  console\.log\("\\n=== \d+\. /.test(l) || l.includes('"=".repeat(58)')));
const body = lines.slice(a, b).join("\n");
let fails = 0, passes = 0;
const ok = (n, c, extra="") => { c ? passes++ : fails++; console.log(`  ${c ? "PASS" : "FAIL"}  ${n}${extra ? "  " + extra : ""}`); };
(async () => {
  const browser = await chromium.launch(L);
  const page = await browser.newPage({ viewport: { width: 1280, height: 760 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error" && !/AudioContext/.test(m.text())) errors.push("CONSOLE: " + m.text()); });
  await page.goto("file://" + path.join(DIR, process.env.BONKHORDE_TARGET || "index.html"), { waitUntil: "load" });
  await page.waitForTimeout(700);
  const t0 = Date.now();
  const FILE = "file://" + path.join(DIR, process.env.BONKHORDE_TARGET || "index.html");
  const fn = new Function("page", "ok", "errors", "fs", "require", "browser", "L", "path", "__dirname", "FILE", `return (async () => { ${body} })();`);
  await fn(page, ok, errors, fs, require, browser, L, path, DIR, FILE);
  console.log(`\nsection ${N}: ${passes} passed, ${fails} failed in ${((Date.now()-t0)/1000).toFixed(0)} s`);
  if(errors.length) console.log("ERRORS:", [...new Set(errors)].slice(0, 6).join(" | "));
  await browser.close();
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error("CRASH:", e); process.exit(2); });
