/**
 * Asserts the brief's byte budget against the real build output, gzipped.
 *
 * The budget is not decoration. The intended user is on an old phone in a garage with bad
 * signal, and every kilobyte is the difference between an answer and a spinner. This fails the
 * build rather than reporting a number nobody reads.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dist = join(root, 'dist');

const BUDGET_JS_GZIP = 100 * 1024; // brief: "under 200KB JS"; held to 100KB here since exifr is lazy
const BUDGET_TOTAL_GZIP = 200 * 1024; // brief: "total page weight under 200KB"

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else out.push(p);
  }
  return out;
}

const files = walk(dist);
let js = 0;
let css = 0;
let html = 0;
let json = 0;
let other = 0;
const rows: { name: string; raw: number; gz: number }[] = [];

for (const f of files) {
  const buf = readFileSync(f);
  const gz = gzipSync(buf).length;
  const rel = f.slice(dist.length + 1);
  rows.push({ name: rel, raw: buf.length, gz });
  switch (extname(f)) {
    case '.js':
      js += gz;
      break;
    case '.css':
      css += gz;
      break;
    case '.html':
      html += gz;
      break;
    case '.json':
    case '.webmanifest':
      json += gz;
      break;
    default:
      other += gz;
  }
}

const kb = (n: number) => `${(n / 1024).toFixed(1)}KB`;
rows.sort((a, b) => b.gz - a.gz);

console.log('\nBuild size (gzipped):\n');
for (const r of rows) {
  console.log(`  ${kb(r.gz).padStart(8)}  ${kb(r.raw).padStart(8)} raw   ${r.name}`);
}

// The JSON index is bundled into the JS by Vite, so `js` already includes it. Reported
// separately when it is emitted as its own asset.
const total = js + css + html + json + other;
console.log(`\n  JS    ${kb(js)}  (budget ${kb(BUDGET_JS_GZIP)})`);
console.log(`  CSS   ${kb(css)}`);
console.log(`  HTML  ${kb(html)}`);
console.log(`  other ${kb(json + other)}`);
console.log(`  TOTAL ${kb(total)}  (budget ${kb(BUDGET_TOTAL_GZIP)})\n`);

let failed = false;
if (js > BUDGET_JS_GZIP) {
  console.error(`FAIL: JS is ${kb(js)}, over the ${kb(BUDGET_JS_GZIP)} budget.`);
  failed = true;
}
if (total > BUDGET_TOTAL_GZIP) {
  console.error(`FAIL: total is ${kb(total)}, over the ${kb(BUDGET_TOTAL_GZIP)} budget.`);
  failed = true;
}
if (failed) process.exit(1);
console.log('within budget\n');
