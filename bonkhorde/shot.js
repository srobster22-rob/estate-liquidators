// Screenshot helper: node shot.js <out.png> [selector]
const fs = require("fs"), path = require("path");
function loadPlaywright(){
  for(const p of ["playwright", "/opt/node22/lib/node_modules/playwright"]){
    try { return require(p); } catch(e) {}
  }
  process.exit(2);
}
const { chromium } = loadPlaywright();
const LAUNCH = { args:["--use-gl=angle","--use-angle=swiftshader",
  "--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"])
  if(fs.existsSync(p)) LAUNCH.executablePath = p;
(async ()=>{
  const out = process.argv[2] || "shot.png", sel = process.argv[3] || "#chars";
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage({ viewport:{width:1400,height:900}, deviceScaleFactor:+(process.env.DSF||1) });
  p.on("pageerror", e=>console.log("PAGEERROR", e.message));
  p.on("console", m=>{ if(m.type()==="error") console.log("CONSOLE", m.text()); });
  await p.goto("file://" + path.resolve(__dirname, "index.html"));
  await p.waitForTimeout(500);
  await p.evaluate(()=>{ if(window.__g && __g.unlockAll) __g.unlockAll(); });
  await p.waitForTimeout(3000);
  console.log("portraits:", await p.evaluate(()=>document.querySelectorAll(".ch canvas.pv").length));
  const el = sel === "page" ? null : await p.$(sel);
  if(el) await el.screenshot({ path: out }); else await p.screenshot({ path: out });
  await b.close();
})();
