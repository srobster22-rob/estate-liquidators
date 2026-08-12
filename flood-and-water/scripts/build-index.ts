/**
 * Validates the YAML data and emits src/generated/index.json plus SOURCES.md.
 *
 * The safety gate: no life-safety claim and no insurance claim ships without a citation. Both
 * kinds of statement have the same failure mode — a confident sentence somebody acts on — and
 * neither is something to author from scratch.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'yaml';
import { z } from 'zod';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = join(root, 'data');
const outDir = join(root, 'src', 'generated');

const errors: string[] = [];
const warnings: string[] = [];

const sourceSchema = z.object({
  org: z.string().min(1),
  title: z.string().min(1),
  url: z.string().url(),
  retrieved: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  method: z.enum(['fetched', 'search_index', 'phone', 'in_person']),
});

const refs = z.array(z.string()).default([]);

const coverageSchema = z.object({
  waitingPeriod: z.object({
    days: z.number().int().min(0),
    exceptions: z.array(
      z.object({
        id: z.string().min(1),
        days: z.number().int().min(0),
        question: z.string().min(1),
        detail: z.string().min(1),
        // Required, not inherited. Each exception is the rule that turns "you are not covered
        // for a month" into "you are covered tomorrow", which is the single most consequential
        // sentence this app says. Until R11 they relied on the parent block's two general
        // citations, so nothing named which page backed which rule.
        sourceRefs: refs,
      }),
    ),
    sourceRefs: refs,
  }),
  gaps: z.array(
    z.object({
      id: z.string().min(1),
      name: z.string().min(1),
      what: z.string().min(1),
      coveredByHomeowners: z.boolean(),
      why: z.string().min(1),
      rentersNote: z.string().optional(),
      sourceRefs: refs,
    }),
  ),
  declarationsHints: z.array(z.object({ gapId: z.string(), lookFor: z.string().min(1) })),
});

const safetySchema = z.object({
  emergency: z.object({
    headline: z.string().min(1),
    points: z.array(z.object({ text: z.string().min(1), sourceRefs: refs })),
  }),
  mold: z.object({ window_hours: z.number(), text: z.string().min(1), sourceRefs: refs }),
  prepare: z.array(
    z.object({
      id: z.string().min(1),
      title: z.string().min(1),
      detail: z.string().min(1),
      cost: z.string().min(1),
      sourceRefs: refs,
    }),
  ),
});

const localSchema = z.object({
  id: z.string().min(1),
  city: z.string(),
  county: z.string(),
  state: z.string(),
  languages: z.array(z.string()).min(1),
  configured: z.boolean(),
  resources: z.array(
    z.object({
      id: z.string().min(1),
      name: z.string().min(1),
      kind: z.string().min(1),
      phone: z.string().optional(),
      url: z.string().url().optional(),
      note: z.string().optional(),
      verifiedOn: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      verifiedBy: z.string().min(1),
    }),
  ),
});

const readYaml = (f: string): unknown => parse(readFileSync(join(dataDir, f), 'utf8'));

const sourcesRaw = (readYaml('sources.yaml') ?? {}) as Record<string, unknown>;
const sources: Record<string, z.infer<typeof sourceSchema>> = {};
for (const [key, val] of Object.entries(sourcesRaw)) {
  const p = sourceSchema.safeParse(val);
  if (!p.success) errors.push(`sources.yaml "${key}": ${p.error.issues.map((i) => i.message).join('; ')}`);
  else sources[key] = p.data;
}

const coverage = coverageSchema.parse(readYaml('coverage.yaml'));
const safety = safetySchema.parse(readYaml('safety.yaml'));
const local = localSchema.parse(readYaml('local.yaml'));

const used = new Set<string>();
function resolve(keys: string[], where: string, required: boolean): z.infer<typeof sourceSchema>[] {
  if (required && keys.length === 0) {
    errors.push(`${where}: this is a safety or insurance claim and needs at least one source`);
  } else if (!required && keys.length === 0) {
    warnings.push(`${where}: no source — record it in VERIFY.md`);
  }
  return keys.map((k) => {
    if (!sources[k]) {
      errors.push(`${where}: unknown source key "${k}"`);
      return undefined;
    }
    used.add(k);
    return sources[k];
  }).filter(Boolean) as z.infer<typeof sourceSchema>[];
}

// Every life-safety point and every insurance claim requires a citation. The prepare checklist
// is practical advice rather than a claim about law or physics, so it warns instead.
const resolved = {
  coverage: {
    waitingPeriod: {
      days: coverage.waitingPeriod.days,
      exceptions: coverage.waitingPeriod.exceptions.map((e) => ({
        ...e,
        sources: resolve(e.sourceRefs, `waiting period exception ${e.id}`, true),
      })),
      sources: resolve(coverage.waitingPeriod.sourceRefs, 'coverage.waitingPeriod', true),
    },
    gaps: coverage.gaps.map((g) => ({
      ...g,
      sources: resolve(g.sourceRefs, `gap ${g.id}`, true),
    })),
    declarationsHints: coverage.declarationsHints,
  },
  safety: {
    emergency: {
      headline: safety.emergency.headline,
      points: safety.emergency.points.map((p, i) => ({
        text: p.text,
        sources: resolve(p.sourceRefs, `safety.emergency.points[${i}]`, true),
      })),
    },
    mold: { ...safety.mold, sources: resolve(safety.mold.sourceRefs, 'safety.mold', true) },
    prepare: safety.prepare.map((s) => ({
      ...s,
      sources: resolve(s.sourceRefs, `prepare ${s.id}`, false),
    })),
  },
  local,
  builtAt: new Date().toISOString().slice(0, 10),
};

for (const h of coverage.declarationsHints) {
  if (!coverage.gaps.some((g) => g.id === h.gapId)) {
    errors.push(`declarationsHints references unknown gap "${h.gapId}"`);
  }
}
for (const g of coverage.gaps) {
  if (!coverage.declarationsHints.some((h) => h.gapId === g.id)) {
    // Without this the user is told they have a gap and not how to check their own paperwork.
    errors.push(`gap "${g.id}" has no declarationsHints entry — every gap needs a what-to-look-for`);
  }
}
if (local.configured && local.resources.length === 0) {
  errors.push('local.configured is true but no resources are listed. Do the calls first — see VERIFY.md.');
}

if (warnings.length) {
  console.warn('\nWarnings:');
  for (const w of warnings) console.warn(`  ! ${w}`);
}
if (errors.length) {
  console.error('\nData validation failed:\n');
  for (const e of errors) console.error(`  x ${e}`);
  console.error(`\n${errors.length} error(s). Nothing was written.\n`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'index.json'), JSON.stringify(resolved));

const lines = [
  '# Sources',
  '',
  '_Generated by `npm run data`. Edit `data/sources.yaml`, not this file._',
  '',
  'Every life-safety statement and every insurance statement in this app traces to one of these.',
  '',
  '`search_index` means the content was confirmed through a web search index but the page itself',
  "could not be retrieved — this environment's egress policy blocks these hosts. That is weaker",
  'than reading the page. Re-fetching all of them is item 1.1 in `VERIFY.md`.',
  '',
  '| Org | Title | Checked | How | URL |',
  '| --- | --- | --- | --- | --- |',
  ...[...used].sort().map((k) => {
    const s = sources[k];
    return `| ${s.org} | ${s.title} | ${s.retrieved} | ${s.method} | <${s.url}> |`;
  }),
  '',
];
writeFileSync(join(root, 'SOURCES.md'), lines.join('\n'));

console.log(
  `\nok — ${resolved.coverage.gaps.length} coverage gaps, ` +
    `${resolved.safety.emergency.points.length} safety points, ` +
    `${resolved.safety.prepare.length} prepare steps, ${used.size} sources cited.`,
);
console.log(`waiting period: ${coverage.waitingPeriod.days} days, ${coverage.waitingPeriod.exceptions.length} exceptions`);
console.log(`local "${local.id}" configured=${local.configured}\n`);
