// kill-check: apply each mutant whose must matches the section to a copy of
// index.html and run just that section against it. node mutsec.js 35
const fs=require("fs"), path=require("path"), { spawnSync } = require("child_process");
const DIR = path.resolve(__dirname, "..");
const N = process.argv[2] || "35";
const src = fs.readFileSync(path.join(DIR, "index.html"), "utf8");
const mut = fs.readFileSync(path.join(DIR, "mutate.js"), "utf8");
// pull MUTANTS out of mutate.js without running it
const m0 = mut.indexOf("const MUTANTS = ["), m1 = mut.indexOf("\n];", m0) + 3;
const MUTANTS = new Function(mut.slice(m0, m1) + "; return MUTANTS;")();
const mine = MUTANTS.filter(m => m.must === N);
console.log(`${mine.length} mutants for section ${N}`);
let caught = 0;
for(const m of mine){
  if(!src.includes(m.from)){ console.log(`  SKIP  ${m.id}: anchor missing`); continue; }
  const out = path.join(DIR, `mut-${m.id}.html`);
  fs.writeFileSync(out, src.replace(m.from, m.to));
  const t0 = Date.now();
  const r = spawnSync("node", [path.join(__dirname, "sec.js"), N], { env: { ...process.env, BONKHORDE_TARGET: `mut-${m.id}.html` }, encoding: "utf8", timeout: 400000 });
  fs.unlinkSync(out);
  const line = (r.stdout.match(/section \w+: (\d+) passed, (\d+) failed/) || [,"?","?"]);
  const fails = r.stdout.split("\n").filter(l => l.startsWith("  FAIL")).map(l => l.slice(8, 80));
  const ok = +line[2] > 0;
  if(ok) caught++;
  console.log(`  ${ok ? "KILLED" : "SURVIVED"}  ${m.id}  (${line[1]} passed, ${line[2]} failed, ${((Date.now()-t0)/1000).toFixed(0)} s)${r.status === null ? " TIMEOUT" : ""}`);
  for(const f of fails.slice(0,3)) console.log(`      - ${f}`);
  if(r.stderr && /CRASH/.test(r.stderr)) console.log("      CRASH:", r.stderr.split("\n")[0].slice(0,200));
}
console.log(`\n${caught}/${mine.length} killed`);
