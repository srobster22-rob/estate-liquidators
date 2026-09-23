// Section 100's paint measurement over a FULL TURN of the camera at the suite's
// station: the tier's paint at eight headings, each against its own null frame.
const fs=require("fs");
function lp(){for(const p of ["playwright","/opt/node22/lib/node_modules/playwright"]){try{return require(p)}catch(e){}}process.exit(2)}
const {chromium}=lp();
const L={args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--no-sandbox"]};
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"]) if(fs.existsSync(p)) L.executablePath=p;
const FILE=process.env.FILE, TAG=process.env.TAG||"", TS=(process.env.TS||"420").split(",").map(Number), SEED=+(process.env.SEED||9);
(async()=>{
 const b=await chromium.launch(L), page=await b.newPage({viewport:{width:1280,height:760}});
 const errs=[]; page.on("pageerror",e=>errs.push(e.message));
 await page.goto("file://"+FILE); await page.waitForFunction(()=>!!window.__g,null,{timeout:60000});
 for(const T of TS){
 const r = await page.evaluate(async ({T,SEED}) => {
  const g = window.__g;
  g.wipeSave(); g.dev(true); g.pin(SEED); g.pinRun(SEED);
  g.start("intern"); g.god(); g.drainPicks(true); g.bot(true);
  let guard = 0; while(g.state().t < T && guard++ < 200000) g.step(30, 1/60);
  g.pause(true); g.setShake(0);
  const cv = [...document.querySelectorAll("canvas")].find(c => c.id !== "ui");
  const W = cv.width, H = cv.height;
  const sc = document.createElement("canvas"); sc.width = W; sc.height = H;
  const sx = sc.getContext("2d", { willReadFrequently:true });
  let ms = performance.now();
  const arm = (on)=>{ g.outcropsOn(on); g.tick(ms += 16); sx.clearRect(0,0,W,H); sx.drawImage(cv,0,0);
    const c = g.boxCensus(); return { px:sx.getImageData(0,0,W,H).data, pass:c.passes.outcrops||0 }; };
  const diff = (A,B)=>{ let n=0; for(let q=0;q<A.length;q+=4){ if(Math.abs(A[q]-B[q])<6 && Math.abs(A[q+1]-B[q+1])<6 && Math.abs(A[q+2]-B[q+2])<6) continue; n++; } return n; };
  const S = g.state();
  const brg = g.monuments().filter(m => Math.hypot(m.x - S.x, m.z - S.z) < 200).map(m => Math.atan2(m.x - S.x, m.z - S.z) * 180 / Math.PI);
  const clear = a => brg.length ? Math.min(...brg.map(bb => Math.abs((((a - bb) % 360) + 540) % 360 - 180))) : 180;
  const rows = [];
  for(let a = 0; a < 360; a += 45){
    g.outcropsOn(true); g.setCam(a * Math.PI / 180);
    for(let i=0;i<50;i++) g.tick(ms += 16);
    const off = arm(false), off2 = arm(false), on = arm(true);
    rows.push({ a, clear:Math.round(clear(a)), paint:+(100*diff(off2.px,on.px)/(W*H)).toFixed(2), floor:+(100*diff(off.px,off2.px)/(W*H)).toFixed(2), pass:on.pass });
  }
  g.outcropsOn(true); g.setCam(0); g.pause(false);
  return { t:S.t, x:+S.x.toFixed(1), z:+S.z.toFixed(1), rows };
 }, {T,SEED});
 const mean = r.rows.reduce((s,x)=>s+x.paint,0)/r.rows.length, fl = Math.max(...r.rows.map(x=>x.floor));
 console.log(TAG, `t ${r.t} at (${r.x},${r.z}) mean paint ${mean.toFixed(2)}% max floor ${fl}% |`, r.rows.map(x=>`${x.a}:${x.paint}${x.clear<30?"m":""}`).join(" "));
 }
 console.log("ERRS",errs.length,errs.slice(0,2).join(" | ")); await b.close();
})().catch(e=>{console.error("FAILED",e&&e.stack||e);process.exit(1);});
