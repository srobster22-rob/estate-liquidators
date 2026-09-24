// EVERY PROPERTY A BODY EVER HAS, AND WHO ASKS BEFORE IT IS SET. Every object pushed
// onto `enemies` is wrapped in a Proxy for one pinned trial (bot, runOut); per key:
// how many bodies had it set, from where (first set, by site), what types it held,
// how often it was READ while still unset and from where, and any `in`, delete or
// own-keys walk over a body. What this answers: which keys can be given a default
// in the spawn literal without any read noticing.
const fs = require("fs"), path = require("path");
function lp(){ for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){ try{ return require(p); }catch(e){} } process.exit(2); }
const { chromium } = lp();
const L = { args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath = p;
const REPO = process.env.REPO || "/home/user/estate-liquidators/bonkhorde", MUT = process.env.MUT;
const SEED = +(process.env.SEED || 999), RUN = +(process.env.RUN || 555);
let src = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
if(MUT){ const t = fs.readFileSync(path.join(REPO, "mutate.js"), "utf8"), i = t.indexOf(`id:"${MUT}"`);
  const end = t.indexOf("\n  { id:", i), blk = t.slice(t.lastIndexOf("{", i), t.lastIndexOf("}", end < 0 ? t.length : end) + 1), m = (0, eval)("(" + blk + ")");
  if(src.split(m.from).length !== 2) throw new Error("anchor"); src = src.replace(m.from, m.to); }
const TMP = path.join(REPO, `_hang.${process.pid}.html`); fs.writeFileSync(TMP, src);
(async()=>{
  const b = await chromium.launch(L), pg = await b.newPage({ viewport:{ width:1280, height:760 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.goto("file://" + TMP); await pg.waitForFunction(() => !!window.__g, null, { timeout:60000 });
  const t0 = Date.now();
  const r = await pg.evaluate(({ SEED, RUN }) => {
    const g = window.__g, E = (0, eval);
    const en0 = E("enemies");
    const keys = new Map();               // key -> { set:n, types:Set, setSites:Map, rbs:n, rbsSites:Map, has:n, hasSites:Map, del:n, delSites:Map }
    const own = new Map();                // ownKeys walks by site
    let wrapped = 0; const proxies = new WeakSet();
    const site = () => { const s = new Error().stack.split("\n"); for(let i = 2; i < s.length; i++){ const m = /at (?:([^ ]+) )?\(?[^)]*?:(\d+):\d+\)?$/.exec(s[i]); if(m && !/^(Proxy|Object\.)/.test(m[1] || "")) return (m[1] || "?") + ":" + m[2]; } return "?"; };
    const rec = (k) => { let r = keys.get(k); if(!r){ r = { set:0, types:new Set(), setSites:new Map(), rbs:0, rbsSites:new Map(), has:0, hasSites:new Map(), del:0, delSites:new Map(), tyChange:new Set() }; keys.set(k, r); } return r; };
    const bump = (m, s) => m.set(s, (m.get(s) || 0) + 1);
    const ty = (v) => v === null ? "null" : Array.isArray(v) ? "array" : typeof v;
    const wrap = (o) => { if(!o || typeof o !== "object" || proxies.has(o)) return o; wrapped++;
      for(const k of Object.keys(o)){ const r = rec(k); r.set++; r.types.add(ty(o[k])); bump(r.setSites, "literal"); }
      const p = new Proxy(o, {
        set(t, k, v){ if(typeof k === "string"){ const r = rec(k); const had = k in t;
            if(!had){ r.set++; bump(r.setSites, site()); } else { const was = ty(t[k]), now = ty(v); if(was !== now && !(was === "number" && now === "number")) r.tyChange.add(was + "->" + now); }
            r.types.add(ty(v)); } t[k] = v; return true; },
        get(t, k, rcv){ if(typeof k === "string" && !(k in t)){ const r = rec(k); r.rbs++; if(r.rbs <= 40) bump(r.rbsSites, site()); } return t[k]; },
        has(t, k){ if(typeof k === "string"){ const r = rec(k); r.has++; if(r.has <= 40) bump(r.hasSites, site()); } return k in t; },
        deleteProperty(t, k){ if(typeof k === "string"){ const r = rec(k); r.del++; bump(r.delSites, site()); } delete t[k]; return true; },
        ownKeys(t){ bump(own, site()); return Reflect.ownKeys(t); },
      }); proxies.add(p); return p; };
    g.wipeSave(); g.pin(SEED); g.pinRun(RUN); g.wipeSave(); g.start("intern"); g.bot(true);
    const en = E("enemies"), push0 = en.push, same = en === en0, already = en.length;   // start() may make a new array
    for(let i = 0; i < en.length; i++) en[i] = wrap(en[i]);
    en.push = function(...a){ return push0.apply(this, a.map(wrap)); };
    const st = g.runOut();
    const stillSame = E("enemies") === en;
    const co = E("corpses");
    const cover = { enemies:en.length, enemiesWrapped:en.filter(e => proxies.has(e)).length, corpses:co.length, corpsesWrapped:co.filter(e => proxies.has(e)).length };
    const top = (m, n) => [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(([k, v]) => `${k} x${v}`).join("; ");
    const rows = [...keys.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1).map(([k, r]) => ({ k, set:r.set, types:[...r.types].join("/"), setSites:top(r.setSites, 3), rbs:r.rbs, rbsSites:top(r.rbsSites, 3), has:r.has, hasSites:top(r.hasSites, 2), del:r.del, delSites:top(r.delSites, 2), tyChange:[...r.tyChange].join(",") }));
    return { res:`${st.t.toFixed(2)}/${st.lvl}/${st.kills}`, wrapped, cover, rows, own:top(own, 8), same, already, stillSame };
  }, { SEED, RUN });
  console.log(`${MUT || "clean"}: trial ${r.res} in ${((Date.now() - t0) / 1000).toFixed(0)} s; enemies array same across start: ${r.same}, across the run: ${r.stillSame}, ${r.already} bodies there at the hook; ${r.wrapped} bodies wrapped; at the end ${r.cover.enemiesWrapped}/${r.cover.enemies} enemies and ${r.cover.corpsesWrapped}/${r.cover.corpses} corpses are wrapped`);
  console.log(`own-keys walks over a body: ${r.own || "none"}`);
  console.log(`\n${"key".padEnd(10)} ${"set on".padStart(6)}  ${"types".padEnd(22)} ${"first set from".padEnd(58)} ${"read unset".padStart(10)}  read-unset from`);
  for(const w of r.rows) console.log(`${w.k.padEnd(10)} ${String(w.set).padStart(6)}  ${w.types.padEnd(22)} ${w.setSites.slice(0, 58).padEnd(58)} ${String(w.rbs).padStart(10)}  ${w.rbsSites}${w.has ? `  | in: ${w.has} (${w.hasSites})` : ""}${w.del ? `  | DELETE: ${w.del} (${w.delSites})` : ""}${w.tyChange ? `  | type change: ${w.tyChange}` : ""}`);
  console.log("ERRS", errs.length, errs.slice(0, 2).join(" | ")); fs.unlinkSync(TMP); await b.close();
})().catch(e => { console.error("FAILED", e && e.stack || e); try { fs.unlinkSync(TMP); } catch(_){} process.exit(1); });
