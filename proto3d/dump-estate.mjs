/**
 * Dump the prototype's estate in the schema sim/validate_estate.py expects.
 *
 *     node proto3d/dump-estate.mjs > /tmp/proto3d-estate.json
 *     python3 sim/validate_estate.py --estate /tmp/proto3d-estate.json
 *
 * The level contract was written in LEVEL-SPEC and verified against a worked
 * example in a document. Until R23 it had never been pointed at the wing anyone
 * actually plays, which is the only estate this project has.
 */
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const pw = ["playwright", "/opt/node22/lib/node_modules/playwright"]
  .reduce((acc, p) => acc || (() => { try { return require(p); } catch { return null; } })(), null);
if (!pw) { console.error("Playwright not found"); process.exit(2); }

const browser = await pw.chromium.launch({
  args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"],
});
const page = await browser.newPage();
await page.addInitScript(`(() => { let s = 0x2f6e2b1;
  Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; })();`);
await page.goto("file://" + path.join(HERE, "index.html"));
await page.waitForFunction("typeof window.__g === 'object'");
process.stdout.write(JSON.stringify(await page.evaluate(() => window.__g.estate()), null, 2));
await browser.close();
