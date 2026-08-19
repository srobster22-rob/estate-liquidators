// Smoke suite for the two Estate Liquidators prototypes.
//
// BONKHORDE has 148 checks; these two had none, and they are the only playable
// evidence this half of the repository has. Nothing here is a balance claim -
// the simulations own that. This asks the three questions a prototype can fail
// silently: does it boot, does its loop actually advance state, and can you
// still steer it where pointer lock is refused (which is every embed, and is
// how BONKHORDE's camera was found frozen).
const path = require("path");
function loadPlaywright(){
  for(const p of ["playwright", "/opt/node22/lib/node_modules/playwright"]){
    try { return require(p); } catch(e) {}
  }
  console.error("Playwright not found."); process.exit(2);
}
const { chromium } = loadPlaywright();
const fs = require("fs");
const LAUNCH = { args:["--use-gl=angle","--use-angle=swiftshader",
                       "--enable-unsafe-swiftshader","--no-sandbox"] };
for(const p of ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"])
  if(fs.existsSync(p)) LAUNCH.executablePath = p;

let passes = 0, fails = 0;
const ok = (n, c, extra="") => { c ? passes++ : fails++;
  console.log(`  ${c?"PASS":"FAIL"}  ${n}${extra?"  "+extra:""}`); };
const url = d => "file://" + path.resolve(__dirname, d, "index.html");

(async () => {
  const b = await chromium.launch(LAUNCH);

  console.log("\n=== proto — top-down loop ===");
  {
    const p = await b.newPage({ viewport:{width:1000,height:700} });
    const errs = []; p.on("pageerror", e => errs.push(e.message));
    await p.goto(url("proto"), { waitUntil:"load" });
    await p.waitForTimeout(400);
    ok("boots without throwing", errs.length === 0, errs.slice(0,2).join(" | "));
    ok("exposes its QA hook", await p.evaluate(() => !!window.__game));
    const a = await p.evaluate(() => window.__game.state());
    const c = await p.evaluate(() => window.__game.step(60 * 30));
    ok("the clock advances under stepping", c.t > a.t + 20, `${a.t} -> ${c.t}`);
    ok("the Curator has a state", typeof c.curator === "string", c.curator);
    ok("items exist to steal", (await p.evaluate(() => window.__game.items())) > 0);
    const moved = await p.evaluate(() => {
      const b0 = window.__game.pos();
      window.__game.press("KeyD", true); window.__game.step(90);
      window.__game.press("KeyD", false);
      const b1 = window.__game.pos();
      return Math.abs(b1.px - b0.px) + Math.abs(b1.py - b0.py);
    });
    ok("input moves the player", moved > 0, `${moved} units`);
    ok("no errors across the whole run", errs.length === 0, errs.slice(0,2).join(" | "));
    await p.close();
  }

  console.log("\n=== proto3d — first-person prototype ===");
  {
    const p = await b.newPage({ viewport:{width:1000,height:700} });
    const errs = []; p.on("pageerror", e => errs.push(e.message));
    await p.goto(url("proto3d"), { waitUntil:"load" });
    await p.waitForTimeout(400);
    ok("boots without throwing", errs.length === 0, errs.slice(0,2).join(" | "));
    ok("exposes its QA hook", await p.evaluate(() => !!window.__g));
    ok("draws to a live WebGL context", await p.evaluate(() =>
      !!document.querySelector("canvas").getContext("webgl")));
    const a = await p.evaluate(() => window.__g.state());
    const c = await p.evaluate(() => window.__g.step(60 * 30));
    ok("the clock advances under stepping", c.t > a.t + 20, `${a.t} -> ${c.t}`);
    ok("the Curator has a tier", typeof c.tier === "string", `${c.tier} at ${c.dist}`);
    const moved = await p.evaluate(() => {
      const b0 = window.__g.pos();
      window.__g.press("KeyW", true); window.__g.step(120);
      window.__g.press("KeyW", false);
      const b1 = window.__g.pos();
      return Math.hypot(b1.x - b0.x, b1.z - b0.z);
    });
    ok("input moves the player", moved > 0.5, `${moved.toFixed(1)}m`);

    // the bug this suite exists for
    const look = await p.evaluate(() => {
      const cv = document.querySelector("canvas");
      const move = dx => dispatchEvent(new MouseEvent("mousemove",
        { movementX: dx, movementY: 0, bubbles: true }));
      const locked = document.pointerLockElement === cv;
      const a = window.__g.yaw();
      move(80);                                            // loose mouse
      const idle = window.__g.yaw();
      cv.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
      move(80);                                            // dragging
      const dragged = window.__g.yaw();
      dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
      move(80);
      return { locked, a, idle, dragged, after: window.__g.yaw() };
    });
    ok("the camera turns with no pointer lock held",
       look.locked === false && Math.abs(look.dragged - look.idle) > 0.05,
       `locked=${look.locked} ${look.idle.toFixed(3)} -> ${look.dragged.toFixed(3)}`);
    ok("a loose mouse does not steer", Math.abs(look.idle - look.a) < 1e-9);
    ok("mouseup ends the drag", Math.abs(look.after - look.dragged) < 1e-9);
    ok("no errors across the whole run", errs.length === 0, errs.slice(0,2).join(" | "));
    await p.close();
  }

  console.log("\n" + "=".repeat(52));
  console.log(`RESULT: ${passes} passed, ${fails} failed`);
  await b.close();
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error("HARNESS CRASH:", e); process.exit(2); });
