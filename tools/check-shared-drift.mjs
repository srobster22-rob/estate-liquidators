#!/usr/bin/env node
/**
 * Detects drift between files that are deliberately duplicated across the built projects.
 *
 * WHY THEY ARE DUPLICATED AND NOT EXTRACTED
 *
 * Each project in this repository is meant to be copied out and run as its own repository —
 * that is what `society-prompts/launch/` tells the agent to do, and a shared package at this
 * repo's root would break the moment someone did it. So the service worker, the byte-budget
 * checker, and the precache generator are copied on purpose.
 *
 * The cost of that choice is drift: a fix applied to one copy and not the other. That happened
 * already — the service worker's `ignoreVary` cache-lookup fix was found in disposal-guide, and
 * flood-and-water only got it because it was copied afterwards. Next time the copy might go the
 * other way, or not at all.
 *
 * So instead of extracting, this makes the drift loud. Lines that are *supposed* to differ are
 * declared per file; everything else must match byte for byte.
 *
 *   node tools/check-shared-drift.mjs
 */
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

/** `allowedToDiffer` lines are dropped before comparing. Keep the list tight. */
const SHARED = [
  {
    file: 'public/sw.js',
    projects: ['disposal-guide', 'flood-and-water'],
    allowedToDiffer: [/^const VERSION = /],
  },
  {
    file: 'scripts/gen-sw.ts',
    projects: ['disposal-guide', 'flood-and-water'],
    allowedToDiffer: [],
  },
  {
    file: 'scripts/check-budget.ts',
    projects: ['disposal-guide', 'flood-and-water'],
    allowedToDiffer: [/^const BUDGET_INITIAL_(JS|TOTAL)_GZIP = /],
  },
  {
    file: 'playwright.config.ts',
    projects: ['disposal-guide', 'flood-and-water'],
    allowedToDiffer: [/--port|baseURL|url: 'http/],
  },
];

function normalize(text, allowed) {
  return text
    .split('\n')
    .filter((line) => !allowed.some((re) => re.test(line)))
    .map((line) => line.trimEnd())
    .join('\n')
    .trim();
}

let failures = 0;
let checked = 0;

for (const spec of SHARED) {
  const present = spec.projects.filter((p) => existsSync(join(root, p, spec.file)));
  if (present.length < 2) {
    console.log(`  skip  ${spec.file} — only in ${present.join(', ') || 'no project'}`);
    continue;
  }
  checked++;

  const [base, ...rest] = present;
  const baseText = normalize(readFileSync(join(root, base, spec.file), 'utf8'), spec.allowedToDiffer);

  let ok = true;
  for (const other of rest) {
    const otherText = normalize(readFileSync(join(root, other, spec.file), 'utf8'), spec.allowedToDiffer);
    if (otherText === baseText) continue;
    ok = false;
    failures++;
    console.error(`\n  DRIFT  ${spec.file}: ${base} and ${other} disagree.`);
    const a = baseText.split('\n');
    const b = otherText.split('\n');
    for (let i = 0; i < Math.max(a.length, b.length); i++) {
      if (a[i] !== b[i]) {
        console.error(`         first difference at line ${i + 1}:`);
        console.error(`           ${base}: ${a[i] ?? '(end of file)'}`);
        console.error(`           ${other}: ${b[i] ?? '(end of file)'}`);
        break;
      }
    }
    console.error(
      '         A fix applied to one copy has to be applied to the other. If the difference is\n' +
        '         intentional, add the line pattern to allowedToDiffer in this script and say why.',
    );
  }
  if (ok) console.log(`  ok    ${spec.file} — identical across ${present.join(', ')}`);
}

console.log(`\n${checked} shared file(s) checked, ${failures} drifted.\n`);
process.exit(failures > 0 ? 1 : 0);
