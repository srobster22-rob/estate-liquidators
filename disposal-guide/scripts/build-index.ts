/**
 * Validates the YAML data and emits src/generated/index.json plus SOURCES.md.
 *
 * This script is the project's safety gate. It refuses to emit data that could produce a
 * dangerous answer, so a mistake in a YAML file fails the build rather than reaching a person
 * standing in a garage holding a swollen laptop battery.
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'yaml';
import { z } from 'zod';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = join(root, 'data');
const outDir = join(root, 'src', 'generated');

const errors: string[] = [];
const warnings: string[] = [];

// ---------------------------------------------------------------------------- schemas

const i18n = z.object({ en: z.string().min(1) }).catchall(z.string());

const sourceSchema = z.object({
  org: z.string().min(1),
  title: z.string().min(1),
  url: z.string().url(),
  retrieved: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  method: z.enum(['fetched', 'search_index', 'phone', 'in_person']),
});

const hazardSchema = z.enum(['none', 'caution', 'hazardous', 'professional']);

const verdictSchema = z.enum([
  'recycling_cart',
  'trash_cart',
  'yard_waste',
  'special_dropoff',
  'retail_takeback',
  'hazardous_waste',
  'not_in_any_bin',
  'professional_only',
  'unknown',
]);

const universalSchema = z.object({
  hazard: hazardSchema,
  neverCurbside: z.boolean(),
  why: i18n,
  prep: z.array(i18n).default([]),
  nationalOptions: z.array(i18n).optional(),
  sourceRefs: z.array(z.string()).default([]),
});

const localRuleSchema = z.object({
  verdict: verdictSchema,
  destinations: z.array(z.string()).default([]),
  notes: i18n.optional(),
  quantityLimit: i18n.optional(),
  verifiedOn: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  verifiedBy: z.string().min(1),
});

const itemSchema = z.object({
  slug: z.string().regex(/^[a-z0-9-]+$/),
  category: z.string().min(1),
  names: z.record(z.string(), z.array(z.string().min(1))),
  disambiguates: z.array(z.string()).optional(),
  universal: universalSchema.optional(),
  local: z.record(z.string(), localRuleSchema).optional(),
});

const hoursSchema = z.record(
  z.string(),
  z.array(z.object({ open: z.string(), close: z.string() })),
);

const locationSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  address: z.string().min(1),
  phone: z.string().optional(),
  url: z.string().url().optional(),
  hours: hoursSchema.optional(),
  hoursNote: i18n.optional(),
  acceptsSlugs: z.array(z.string()).default([]),
  residencyRequired: z.boolean().optional(),
  proofRequired: i18n.optional(),
  feesNote: i18n.optional(),
  verifiedOn: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  verifiedBy: z.string().optional(),
  isDemo: z.boolean().optional(),
});

const jurisdictionSchema = z.object({
  id: z.string().min(1),
  city: z.string(),
  county: z.string(),
  state: z.string(),
  hauler: z.string(),
  timezone: z.string(),
  languages: z.array(z.string()).min(1),
  configured: z.boolean(),
});

// ---------------------------------------------------------------------------- load

function readYaml(path: string): unknown {
  return parse(readFileSync(path, 'utf8'));
}

const sourcesRaw = readYaml(join(dataDir, 'sources.yaml')) as Record<string, unknown>;
const sources: Record<string, z.infer<typeof sourceSchema>> = {};
for (const [key, val] of Object.entries(sourcesRaw ?? {})) {
  const parsed = sourceSchema.safeParse(val);
  if (!parsed.success) {
    errors.push(`sources.yaml: "${key}" is invalid — ${parsed.error.issues.map((i) => i.message).join('; ')}`);
    continue;
  }
  sources[key] = parsed.data;
}

const itemsDir = join(dataDir, 'items');
const rawItems: unknown[] = [];
for (const f of readdirSync(itemsDir).filter((f) => f.endsWith('.yaml')).sort()) {
  const parsed = readYaml(join(itemsDir, f));
  if (!Array.isArray(parsed)) {
    errors.push(`items/${f}: expected a list of items`);
    continue;
  }
  rawItems.push(...parsed);
}

const locationsDir = join(dataDir, 'locations');
const rawLocations: unknown[] = [];
for (const f of readdirSync(locationsDir).filter((f) => f.endsWith('.yaml')).sort()) {
  const parsed = readYaml(join(locationsDir, f));
  if (!Array.isArray(parsed)) {
    errors.push(`locations/${f}: expected a list of locations`);
    continue;
  }
  for (const row of parsed) {
    // A row in demo.yaml that forgot its flag would render as a real place. Fail instead.
    if (f === 'demo.yaml' && (row as Record<string, unknown>)?.isDemo !== true) {
      errors.push(`locations/demo.yaml: "${(row as Record<string, unknown>)?.id}" must set isDemo: true`);
    }
    rawLocations.push(row);
  }
}

const jurisdiction = jurisdictionSchema.parse(readYaml(join(dataDir, 'jurisdiction.yaml')));

// ---------------------------------------------------------------------------- validate

const items: z.infer<typeof itemSchema>[] = [];
for (const raw of rawItems) {
  const parsed = itemSchema.safeParse(raw);
  if (!parsed.success) {
    const slug = (raw as Record<string, unknown>)?.slug ?? '(no slug)';
    errors.push(`item ${slug}: ${parsed.error.issues.map((i) => `${i.path.join('.')} ${i.message}`).join('; ')}`);
    continue;
  }
  items.push(parsed.data);
}

const locations: z.infer<typeof locationSchema>[] = [];
for (const raw of rawLocations) {
  const parsed = locationSchema.safeParse(raw);
  if (!parsed.success) {
    errors.push(`location ${(raw as Record<string, unknown>)?.id}: ${parsed.error.issues.map((i) => `${i.path.join('.')} ${i.message}`).join('; ')}`);
    continue;
  }
  locations.push(parsed.data);
}

const slugs = new Set<string>();
for (const item of items) {
  if (slugs.has(item.slug)) errors.push(`duplicate item slug: ${item.slug}`);
  slugs.add(item.slug);
  if (!item.names.en?.length) errors.push(`item ${item.slug}: needs at least one English name`);
}

// Alias collisions make search ambiguous: the same typed word cannot mean two things.
const aliasOwner = new Map<string, string>();
for (const item of items) {
  for (const list of Object.values(item.names)) {
    for (const name of list) {
      const norm = name.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/[^\p{L}\p{N}\s]/gu, ' ').replace(/\s+/g, ' ').trim();
      const owner = aliasOwner.get(norm);
      if (owner && owner !== item.slug) {
        errors.push(`alias "${name}" is claimed by both ${owner} and ${item.slug}`);
      }
      aliasOwner.set(norm, item.slug);
    }
  }
}

const CURBSIDE = new Set(['recycling_cart', 'trash_cart', 'yard_waste']);

for (const item of items) {
  for (const ref of item.universal?.sourceRefs ?? []) {
    if (!sources[ref]) errors.push(`item ${item.slug}: unknown source key "${ref}"`);
  }

  for (const target of item.disambiguates ?? []) {
    if (!slugs.has(target)) errors.push(`item ${item.slug}: disambiguates unknown item "${target}"`);
  }

  const u = item.universal;
  if (u) {
    const dangerous = u.hazard === 'hazardous' || u.hazard === 'professional' || u.neverCurbside;
    if (dangerous && u.sourceRefs.length === 0) {
      // Hard error. A hazard claim without a citation is exactly the kind of confident,
      // unverifiable statement this project is built to avoid.
      errors.push(`item ${item.slug}: hazardous or never-curbside guidance requires at least one source`);
    } else if (u.sourceRefs.length === 0) {
      warnings.push(`item ${item.slug}: explanatory text has no source — record it in VERIFY.md`);
    }
  }

  // THE SAFETY RULE. A local rule may not put a hazardous or never-curbside item in a bin.
  for (const [jid, rule] of Object.entries(item.local ?? {})) {
    if (!CURBSIDE.has(rule.verdict)) continue;
    if (u?.neverCurbside) {
      errors.push(
        `item ${item.slug} (${jid}): local verdict "${rule.verdict}" contradicts neverCurbside. ` +
          `If your town genuinely allows this, change the universal guidance and cite the source.`,
      );
    } else if (u?.hazard === 'hazardous' || u?.hazard === 'professional') {
      errors.push(`item ${item.slug} (${jid}): a ${u.hazard} item cannot have a curbside verdict`);
    }
  }

  for (const [jid, rule] of Object.entries(item.local ?? {})) {
    for (const dest of rule.destinations) {
      const loc = locations.find((l) => l.id === dest);
      if (!loc) {
        errors.push(`item ${item.slug} (${jid}): unknown destination "${dest}"`);
      } else if (!loc.acceptsSlugs.includes(item.slug)) {
        errors.push(`item ${item.slug} (${jid}): destination "${dest}" does not list this item in acceptsSlugs`);
      }
    }
  }
}

for (const loc of locations) {
  for (const slug of loc.acceptsSlugs) {
    if (!slugs.has(slug)) errors.push(`location ${loc.id}: accepts unknown item "${slug}"`);
  }
  if (!loc.isDemo && (!loc.verifiedOn || !loc.verifiedBy)) {
    // Acceptance test 4: every shipped (non-demo) location must name who confirmed it and when.
    errors.push(`location ${loc.id}: a real location needs verifiedOn and verifiedBy (who did you speak to?)`);
  }
}

if (jurisdiction.configured && locations.every((l) => l.isDemo)) {
  errors.push(
    'jurisdiction.configured is true but every location is demo data. Add real, phoned-in ' +
      'locations before turning this on — see VERIFY.md.',
  );
}

// ---------------------------------------------------------------------------- emit

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

const resolvedItems = items.map((item) => ({
  ...item,
  universal: item.universal
    ? {
        hazard: item.universal.hazard,
        neverCurbside: item.universal.neverCurbside,
        why: item.universal.why,
        prep: item.universal.prep,
        nationalOptions: item.universal.nationalOptions ?? [],
        sources: item.universal.sourceRefs.map((r) => sources[r]),
      }
    : undefined,
}));

mkdirSync(outDir, { recursive: true });
const index = {
  jurisdiction,
  items: resolvedItems,
  locations,
  builtAt: new Date().toISOString().slice(0, 10),
};
writeFileSync(join(outDir, 'index.json'), JSON.stringify(index));

// SOURCES.md is generated so it can never drift from the data.
const used = new Set<string>();
for (const item of items) for (const r of item.universal?.sourceRefs ?? []) used.add(r);
const lines = [
  '# Sources',
  '',
  '_Generated by `npm run data`. Do not edit by hand — edit `data/sources.yaml`._',
  '',
  'Every claim the app makes about hazards, handling, or national options traces to one of these.',
  '',
  '## How each was checked',
  '',
  '- **fetched** — the page was retrieved and read in full.',
  '- **search_index** — content confirmed through a web search index, but the page itself could',
  "  not be retrieved. This environment's egress policy blocks direct fetches of these hosts, so",
  '  every source below is currently in this weaker category. Re-fetching them is the first item',
  '  in `VERIFY.md`.',
  '- **phone / in_person** — a person called or went.',
  '',
  '## Sources',
  '',
  '| Org | Title | Checked | How | URL |',
  '| --- | --- | --- | --- | --- |',
];
for (const key of [...used].sort()) {
  const s = sources[key];
  lines.push(`| ${s.org} | ${s.title} | ${s.retrieved} | ${s.method} | <${s.url}> |`);
}
const unused = Object.keys(sources).filter((k) => !used.has(k));
if (unused.length) {
  lines.push('', '## Registered but not currently cited', '', unused.map((u) => `- \`${u}\``).join('\n'));
}
lines.push('');
writeFileSync(join(root, 'SOURCES.md'), lines.join('\n'));

const withUniversal = items.filter((i) => i.universal).length;
const localRules = items.reduce((n, i) => n + Object.keys(i.local ?? {}).length, 0);
console.log(
  `\nok — ${items.length} items (${withUniversal} with sourced universal guidance, ` +
    `${localRules} local rules), ${locations.length} locations ` +
    `(${locations.filter((l) => l.isDemo).length} demo), ${used.size} sources cited.`,
);
console.log(`jurisdiction "${jurisdiction.id}" configured=${jurisdiction.configured}\n`);
