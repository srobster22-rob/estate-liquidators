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
// --seeds N --out DIR writes one file per generated estate, so the Python
// validator can be run over a batch. The JS gate in the prototype is a SUBSET of
// the ten checks; this is how the subset is held honest against the authority.
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf(k); return i < 0 ? d : argv[i + 1]; };
const n = Number(arg("--seeds", 0));
const out = arg("--out", "");
const seed = Number(arg("--seed", 0));

if (n > 0 && out) {
  const fs = await import("node:fs/promises");
  await fs.mkdir(out, { recursive: true });
  for (let i = 1; i <= n; i++) {
    const e = await page.evaluate(s => { window.__g.regen(s); return window.__g.estate(); },
                                  i * 104729);
    await fs.writeFile(path.join(out, `estate-${i}.json`), JSON.stringify(e, null, 2));
  }
  console.error(`wrote ${n} estates to ${out}`);
} else {
  if (seed) await page.evaluate(s => window.__g.regen(s), seed);
  process.stdout.write(JSON.stringify(await page.evaluate(() => window.__g.estate()), null, 2));
}
await browser.close();
