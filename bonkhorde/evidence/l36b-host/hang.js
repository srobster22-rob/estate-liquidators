// WHICH GATE HANGS, AND WHERE. A mutant (MUT, by id from mutate.js) applied to a temp
// copy of FILE; section 97's sequence walked gate by gate, each in its own evaluate
// raced against a timeout; on a timeout the page's JS is paused through CDP and the
// stack printed, which names the loop that never ends. The three bezel gates
// (silhouette, rimDay, farRead) are skipped: twenty minutes, and they never step.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
const PER = +(process.env.PER || 240), SKIP = (process.env.SKIP || "silhouette,rimDay,farRead").split(",");
const src0 = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
let src = src0;
if(MUT){
  const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8");
  const i = t.indexOf(`id:"${MUT}"`); if(i < 0){ console.error("no mutant", MUT); process.exit(2); }
  const blk = t.slice(t.lastIndexOf("{", i), t.indexOf("}", t.indexOf("to:", i)) + 1);
  const m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2){ console.error("anchor count", src.split(m.from).length - 1); process.exit(2); }
  src = src.replace(m.from, m.to);
}
const TMP = path.join(REPO, `_hang.${process.pid}.html`);
fs.writeFileSync(TMP, src);
const QA = fs.readFileSync(path.join(REPO, "tools", "qa", "mutations.js"), "utf8");
const timeout = (ms, tag) => new Promise((_, rej) => setTimeout(() => rej(new Error("TIMEOUT " + tag)), ms));
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  const cdp = await pg.context().newCDPSession(pg);
  const scripts = {};
  cdp.on("Debugger.scriptParsed", s => { scripts[s.scriptId] = { url:s.url, startLine:s.startLine }; });
  await cdp.send("Debugger.enable");
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const t0 = Date.now(), stamp = () => ((Date.now() - t0) / 1000).toFixed(0).padStart(5) + "s";
  const run = async (tag, fn, arg, ms) => {
    const t = Date.now();
    try {
      const r = await Promise.race([pg.evaluate(fn, arg), timeout(ms || PER * 1000, tag)]);
      const ok = r && typeof r === "object" && "ok" in r ? (r.ok ? "ok" : "NOT OK: " + (r.bad || []).slice(0, 2).join(" | ").slice(0, 200)) : "";
      console.log(`${stamp()} ${tag.padEnd(12)} ${((Date.now() - t) / 1000).toFixed(1).padStart(6)}s ${ok}`);
      return r;
    } catch(e) {
      console.log(`${stamp()} ${tag.padEnd(12)} ${String(e.message).slice(0, 120)}`);
      if(/TIMEOUT/.test(e.message)){
        // pause the page's JS and read the stack
        const paused = new Promise(res => cdp.once("Debugger.paused", res));
        try {
          await cdp.send("Debugger.pause");
          const ev = await Promise.race([paused, timeout(20000, "pause")]);
          console.log("HUNG IN " + tag + " - the stack, innermost first:");
          for(const f of ev.callFrames.slice(0, 16)){
            const s = scripts[f.location.scriptId] || {};
            console.log(`   ${(f.functionName || "(anonymous)").padEnd(28)} line ${f.location.lineNumber + 1} (script start ${s.startLine}, ${path.basename(s.url || "?")})`);
          }
          await cdp.send("Debugger.resume").catch(()=>{});
        } catch(e2){ console.log("could not pause: " + e2.message); }
      }
      throw e;
    }
  };
  try {
    await run("sight", () => { const g = window.__g; g.wipeSave(); g.dev(true); g.pin(9); g.pinRun(9);
      g.start("intern"); g.god(); g.drainPicks(true); g.freezeEvents(true); g.step(60, 1/60);
      return g.sightGate ? g.sightGate() : { ok:false, bad:["no sightGate"] }; });
    await run("graft", (QA) => { const g = window.__g, qa = (0, eval)(QA); for(const k of Object.keys(qa)) if(!(k in g)) g[k] = qa[k];
      g.wipeSave(); const r = g.unlockNameGate ? g.unlockNameGate() : { ok:false };
      g.dev(true); g.pin(11); g.pinRun(11); g.start("intern"); g.god(); g.drainPicks(true); g.freezeEvents(true); g.step(60, 1/60); return r; }, QA);
    const seq = [["ground","groundGate"],["ward","wardGate"],["burrow","burrowGate"],["num","numGate"],
                 ["silhouette","silhouetteGate"],["rimDay","rimDayGate"],["farRead","farReadGate"],
                 ["split", null, () => { window.__g.give("dupe", 1); return window.__g.splitGate(); }],
                 ["hud", null, async () => { const g = window.__g; g.hudShowAll(); await new Promise(res => requestAnimationFrame(() => requestAnimationFrame(res))); return g.hudOverlaps(); }],
                 ["rout","routGate"],["digin","diginGate"],["stoop","stoopGate"],["mut","mutGate"],["charge","chargeGate"],
                 ["spring","springGate"],["whip","whipGate"],["tell","tellGate"],["mat","matGate"],["thn","thnGate"],
                 ["sks","sksGate"],["trv","trvGate"],["hdl","hdlGate"],["crowd","crowdGate"],["freeze","freezeGate"],
                 ["arm","armGate"],["reset","burrowResetGate"],["census","censusGate"],["relief","reliefGate"],
                 ["noise","noiseGate"],["hudG","hudGate"],["pair","pairGate"],["leak","leakGate"],["shadow","shadowGate"]];
    for(const [tag, name, fn] of seq){
      if(SKIP.includes(tag)){ console.log(`${stamp()} ${tag.padEnd(12)} skipped`); continue; }
      if(fn) await run(tag, fn, undefined, tag === "census" ? 900000 : undefined);
      else await run(tag, (n) => { const g = window.__g; return g[n] ? g[n]() : { ok:false, bad:["missing " + n] }; }, name, tag === "census" ? 900000 : undefined);
    }
    console.log("ALL GATES RETURNED. errs", errs.length, errs.slice(0, 3).join(" | "));
  } catch(e){ console.log("STOPPED: " + e.message, "errs", errs.length, errs.slice(0, 3).join(" | ")); }
  finally { fs.unlinkSync(TMP); await b.close().catch(()=>{}); process.exit(0); }
})();
