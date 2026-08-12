/**
 * Injects the built asset filenames into dist/sw.js.
 *
 * Without this, a hand-written service worker only caches hashed assets on the second visit,
 * because the first load fetches them before the worker controls the page. For an app whose
 * entire premise is working in a garage with no signal, "offline from the second visit" is a
 * bug, not a nuance.
 */
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dist = join(root, 'dist');
const assets = readdirSync(join(dist, 'assets')).map((f) => `./assets/${f}`);

const swPath = join(dist, 'sw.js');
const sw = readFileSync(swPath, 'utf8');
if (!sw.includes('/* __PRECACHE__ */')) {
  console.error('gen-sw: precache placeholder missing from sw.js');
  process.exit(1);
}
writeFileSync(swPath, sw.replace('/* __PRECACHE__ */', assets.map((a) => `'${a}'`).join(', ')));
console.log(`gen-sw: precached ${assets.length} asset(s)`);
