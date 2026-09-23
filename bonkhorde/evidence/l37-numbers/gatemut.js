// Usage: S=<dir holding gaterun.js under m37/> WT=<repo root> node gatemut.js [id]
// L37: each L37 mutant against numGate alone (not the full suite - that runs after
// the L36 chain). A temp copy per mutant; the gate must come back not-ok, by name.
const fs=require("fs"), path=require("path"), cp=require("child_process");
const WT=process.env.WT, S=process.env.S;
const src=fs.readFileSync(path.join(WT,"bonkhorde","index.html"),"utf8");
const M=(0,eval)("["+fs.readFileSync(path.join(WT,"bonkhorde","mutate.js"),"utf8").split("// ---- L37: THE WALL OF NUMBERS (numGate). Every one fails the gate by name.")[1].split('  { id:"headlong-shipped-off"')[0]+"]");
const only=process.argv[2];
for(const m of M){
  if(only && !m.id.includes(only)) continue;
  if(src.split(m.from).length!==2){ console.log("ANCHOR", m.id); continue; }
  const tmp=path.join(WT,"bonkhorde","_gm_"+m.id+".html");
  fs.writeFileSync(tmp, src.replace(m.from,m.to));
  let out=""; try{ out=cp.execFileSync("nice",["-n","19","node",path.join(S,"m37","gaterun.js")],{env:{...process.env,FILE:tmp},encoding:"utf8",timeout:600000}); }catch(e){ out=(e.stdout||"")+(e.stderr||""); }
  fs.unlinkSync(tmp);
  let r=null; try{ r=JSON.parse(out.slice(out.indexOf("{"), out.lastIndexOf("}")+1)); }catch(e){}
  console.log((r && r.ok===false ? "CAUGHT  " : "SURVIVED")+" "+m.id.padEnd(34)+" "+(r ? (r.bad||[]).map(x=>x.slice(0,150)).join("\n      ") : "no result: "+out.slice(0,200)));
}
