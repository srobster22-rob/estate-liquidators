// ===========================================================================
// clip/render.mjs - capture pass.
//
// Opens proto3d in headless Chromium at 1080x1920, injects the director and the
// shot script, and pumps exactly one simulated frame per screenshot. The sim's
// clock is virtual, so a slow renderer produces the same film as a fast one.
//
//   node clip/render.mjs [--frames 720] [--seed 20260806] [--out build]
// ===========================================================================
import {execSync} from "node:child_process";
import {mkdirSync, rmSync, writeFileSync} from "node:fs";
import {dirname, join, resolve} from "node:path";
import {fileURLToPath, pathToFileURL} from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

const argv = process.argv.slice(2);
const arg = (name, dflt) => {
  const i = argv.indexOf("--" + name);
  return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : dflt;
};

const W = 1080, H = 1920;
const FPS = 30;
const FRAMES = Number(arg("frames", 720));
const SEED = Number(arg("seed", 20260806));
const OUT = resolve(ROOT, arg("out", "clip/build"));
const FRAMEDIR = join(OUT, "frames");

// playwright is installed globally in this environment and locally elsewhere;
// try the normal resolution first and fall back to the global root.
async function loadChromium(){
  const pick = m => m.chromium || (m.default && m.default.chromium);   // ESM or CJS interop
  try {
    const c = pick(await import("playwright"));
    if (c) return c;
  } catch { /* fall through to the global install */ }
  const root = execSync("npm root -g", {encoding: "utf8"}).trim();
  const c = pick(await import(pathToFileURL(join(root, "playwright", "index.js")).href));
  if (!c) throw new Error("playwright is installed but exposes no chromium export");
  return c;
}

const pad = n => String(n).padStart(5, "0");

async function main(){
  const chromium = await loadChromium();

  rmSync(FRAMEDIR, {recursive: true, force: true});
  mkdirSync(FRAMEDIR, {recursive: true});

  const browser = await chromium.launch({
    args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader",
           "--force-device-scale-factor=1", "--hide-scrollbars",
           "--disable-lcd-text", "--force-color-profile=srgb"]
  });
  const page = await browser.newPage({viewport: {width: W, height: H},
                                      deviceScaleFactor: 1});
  const errors = [];
  page.on("pageerror", e => errors.push(String(e)));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });

  await page.addInitScript({path: join(HERE, "director.js")});
  const url = pathToFileURL(join(ROOT, "proto3d", "index.html")).href + `?seed=${SEED}`;
  await page.goto(url, {waitUntil: "load"});

  const ok = await page.evaluate(() => !!(window.__d && window.__g && window.__clip));
  if (!ok) throw new Error("proto3d did not expose __d/__g, or the director failed to inject");

  await page.addScriptTag({path: join(HERE, "shots.js")});
  await page.evaluate(() => window.__clip.boot());

  const t0 = Date.now();
  for (let n = 0; n < FRAMES; n++){
    await page.evaluate(f => window.__clip.step(f), n);
    await page.screenshot({path: join(FRAMEDIR, `${pad(n)}.png`), type: "png",
                           animations: "disabled", caret: "hide"});
    if (n % 60 === 0 || n === FRAMES - 1){
      const s = (Date.now() - t0) / 1000;
      process.stdout.write(`  frame ${pad(n)}/${FRAMES}  ${s.toFixed(1)}s  ` +
        `(${(n / Math.max(s, .001)).toFixed(1)} fps)\n`);
    }
  }

  const trace = await page.evaluate(() => ({
    seed: window.__clip.seed,
    fps: window.__clip.fps,
    spans: window.__clip.captionSpans,
    frames: window.__clip.trace
  }));
  trace.frameCount = FRAMES;
  trace.width = W; trace.height = H;
  writeFileSync(join(OUT, "trace.json"), JSON.stringify(trace));

  await browser.close();

  if (errors.length){
    console.error("page errors:\n  " + errors.slice(0, 8).join("\n  "));
    process.exitCode = 1;
    return;
  }
  console.log(`  captured ${FRAMES} frames -> ${FRAMEDIR}`);
  console.log(`  trace     ${join(OUT, "trace.json")}`);
}

main().catch(e => { console.error(e); process.exit(1); });

export {FPS, W, H};
