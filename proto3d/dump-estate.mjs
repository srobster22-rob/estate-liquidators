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

// Nights matter to the generator - a late contract must reach tier 4, and the
// house is grown bigger to hold it - so a batch that only ever dumped night one
// was showing the Python authority a quarter of what the generator makes. With
// no --night the batch cycles all four.
const nightArg = arg("--night", "");
const nights = nightArg === "" ? [0, 1, 2, 3] : [Number(nightArg)];

if (n > 0 && out) {
  const fs = await import("node:fs/promises");
  await fs.mkdir(out, { recursive: true });
  for (let i = 1; i <= n; i++) {
    const nt = nights[(i - 1) % nights.length];
    const e = await page.evaluate(a => { window.__g.regen(a[0], a[1]); return window.__g.estate(); },
                                  [i * 104729, nt]);
    await fs.writeFile(path.join(out, `estate-${i}-n${nt}.json`), JSON.stringify(e, null, 2));
  }
  console.error(`wrote ${n} estates to ${out} (nights ${nights.join(",")})`);
} else {
  if (seed) await page.evaluate(a => window.__g.regen(a[0], a[1]), [seed, nights[0]]);
  process.stdout.write(JSON.stringify(await page.evaluate(() => window.__g.estate()), null, 2));
}
await browser.close();
