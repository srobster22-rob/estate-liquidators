/**
 * Asserts the byte budget against the real build output, gzipped.
 *
 * The budget is not decoration. The intended user is on an old phone with bad signal, and every
 * kilobyte is the difference between an answer and a spinner. This fails the build rather than
 * reporting a number nobody reads.
 *
 * INITIAL vs LAZY. The budget applies to what the browser must fetch before the first screen is
 * usable: the entry script, the stylesheet, and the HTML, read out of dist/index.html. Chunks
 * that are only loaded on demand — a PDF library behind an export button, an EXIF parser behind
 * a photo picker — are reported separately and are not counted.
 *
 * The first version of this script summed every .js file in dist. That passed while everything
 * was small and then failed the moment a lazily-imported PDF library landed, reporting 212KB for
 * a page that actually ships 10KB. Measuring the wrong thing loudly is its own kind of wrong.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, dirname, extname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dist = join(root, 'dist');

const BUDGET_INITIAL_JS_GZIP = 100 * 1024;
const BUDGET_INITIAL_TOTAL_GZIP = 200 * 1024;

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else out.push(p);
  }
  return out;
}

/** What index.html actually references — everything else is loaded on demand, or not at all. */
function initialAssets(html: string): Set<string> {
  const names = new Set<string>();
  for (const m of html.matchAll(/(?:src|href)="([^"]+\.(?:js|css))"/g)) {
    names.add(basename(m[1]!));
  }
  return names;
}

const html = readFileSync(join(dist, 'index.html'), 'utf8');
const initial = initialAssets(html);

const rows: { name: string; raw: number; gz: number; eager: boolean }[] = [];
for (const f of walk(dist)) {
  const buf = readFileSync(f);
  rows.push({
    name: f.slice(dist.length + 1),
    raw: buf.length,
    gz: gzipSync(buf).length,
    // sw.js and the manifest are not part of the first paint; the worker is registered on load.
    eager: initial.has(basename(f)) || basename(f) === 'index.html',
  });
}

const kb = (n: number) => `${(n / 1024).toFixed(1)}KB`;
const sum = (pred: (r: (typeof rows)[number]) => boolean) =>
  rows.filter(pred).reduce((n, r) => n + r.gz, 0);

rows.sort((a, b) => Number(b.eager) - Number(a.eager) || b.gz - a.gz);

console.log('\nBuild size (gzipped):\n');
for (const r of rows) {
  console.log(`  ${r.eager ? 'initial' : '   lazy'}  ${kb(r.gz).padStart(8)}  ${kb(r.raw).padStart(9)} raw   ${r.name}`);
}

const initialJs = sum((r) => r.eager && extname(r.name) === '.js');
const initialTotal = sum((r) => r.eager);
const lazy = sum((r) => !r.eager);

console.log(`\n  INITIAL JS     ${kb(initialJs)}  (budget ${kb(BUDGET_INITIAL_JS_GZIP)})`);
console.log(`  INITIAL TOTAL  ${kb(initialTotal)}  (budget ${kb(BUDGET_INITIAL_TOTAL_GZIP)})`);
console.log(`  lazy chunks    ${kb(lazy)}  (fetched only when the feature is used)\n`);

let failed = false;
if (initialJs > BUDGET_INITIAL_JS_GZIP) {
  console.error(`FAIL: initial JS is ${kb(initialJs)}, over the ${kb(BUDGET_INITIAL_JS_GZIP)} budget.`);
  failed = true;
}
if (initialTotal > BUDGET_INITIAL_TOTAL_GZIP) {
  console.error(`FAIL: initial total is ${kb(initialTotal)}, over the ${kb(BUDGET_INITIAL_TOTAL_GZIP)} budget.`);
  failed = true;
}
if (failed) process.exit(1);
console.log('within budget\n');
