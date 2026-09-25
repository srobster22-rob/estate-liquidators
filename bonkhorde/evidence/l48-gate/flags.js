// Which V8 flags does this Chrome accept, and what tier does a hot function reach under them?
const fs = require("fs");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
(async()=>{
  for(const jsf of ["--allow-natives-syntax", "--allow-natives-syntax --max-opt=2", "--allow-natives-syntax --max-opt=2 --no-maglev-inlining", "--allow-natives-syntax --no-turbo-inlining --no-maglev-inlining"]){
    const L = { args:["--no-sandbox", "--js-flags=" + jsf] };
    for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
    const b = await chromium.launch(L), pg = await b.newPage(); const out = [];
    pg.on("console", m => out.push(m.text()));
    const r = await pg.evaluate(async () => {
      const inner = (x) => [x, x + 1];                         // allocates, and is inlinable
      function outer(n){ let s = 0; for(let i = 0; i < n; i++){ const a = inner(i); s += a[0] + a[1]; } return s; }
      for(let k = 0; k < 400; k++) outer(10000);
      await new Promise(r => setTimeout(r, 300));
      for(let k = 0; k < 400; k++) outer(10000);
      const st = (0, eval)("(f) => %GetOptimizationStatus(f)");
      const tier = s => (s & 32) ? "TurboFan" : (s & 16) ? "Maglev" : (s & 16384) ? "Sparkplug" : (s & 64) ? "Ignition" : "other " + s;
      return { outer:tier(st(outer)), inner:tier(st(inner)) };
    }).catch(e => ({ error:e.message.slice(0, 120) }));
    console.log(`${jsf.padEnd(72)} ${JSON.stringify(r)}`);
    await b.close();
  }
})().catch(e => { console.error("FAILED", e && e.stack || e); process.exit(1); });
