import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { open } from './db.js';
import { FixtureSource } from './sources/fixture.js';
import { ingest } from './ingest.js';
import { runMatching } from './matchrun.js';
import { enqueue, deliverBatch } from './notify.js';
import { pickProvider } from './sms.js';
import { evaluate, formatReport } from './eval.js';
import { createServer } from './server.js';
import { TOKEN_ENV, suggestToken } from './auth.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const FIXTURES = join(root, 'fixtures');
const cmd = process.argv[2] ?? 'demo';

if (cmd === 'serve') {
  // A running instance over the fixtures, so the review queue can be worked with no network.
  const db = open(':memory:');
  const now = new Date().toISOString();
  db.prepare('INSERT INTO subscribers (phone, language, created_at) VALUES (?,?,?)')
    .run('+15550100', 'en', now);
  db.prepare(
    'INSERT INTO watch_items (subscriber_id, kind, brand, product, upc, vin, category, lot, created_at) VALUES (?,?,?,?,?,?,?,?,?)',
  ).run(1, 'category', null, null, null, null, 'infant acetaminophen', null, now);
  for (const name of ['fda', 'fsis', 'nhtsa']) {
    await ingest(db, new FixtureSource(name, FIXTURES), '2026-01-01', now);
  }
  runMatching(db, now);
  const port = Number(process.env.PORT ?? 4180);
  createServer(db, { env: process.env }).listen(port, () => {
    console.log(`\n  public page   http://127.0.0.1:${port}/`);
    console.log(`  review queue  http://127.0.0.1:${port}/review`);
    if (!process.env[TOKEN_ENV]) {
      console.log(
        `\n  ${TOKEN_ENV} is not set, so the review queue will not open. It decides whether\n` +
          '  real people get texted, so it refuses to serve rather than serving open. Restart with:\n' +
          `\n    ${TOKEN_ENV}=${suggestToken()} npm run serve\n`,
      );
    } else {
      console.log('');
    }
  });
} else if (cmd === 'eval') {
  const report = evaluate(FIXTURES, join(root, 'data', 'labelled-pairs.json'));
  console.log(formatReport(report));
  if (report.precision < 0.95) {
    console.error(`FAIL: alertable precision ${(report.precision * 100).toFixed(1)}% is below 95%.`);
    process.exit(1);
  }
  console.log('precision bar met\n');
} else {
  // A full end-to-end run with no network and no credentials.
  const db = open(':memory:');
  const now = '2026-03-25T09:00:00.000Z';

  db.prepare('INSERT INTO subscribers (phone, language, created_at) VALUES (?, ?, ?)')
    .run('+15550100', 'en', now);
  const w = db.prepare(
    'INSERT INTO watch_items (subscriber_id, kind, brand, product, upc, vin, category, lot, created_at) VALUES (?,?,?,?,?,?,?,?,?)',
  );
  w.run(1, 'product', 'Green Valley Farms', 'frozen cut green beans', null, null, null, '4272', now);
  w.run(1, 'upc', null, null, '811223004417', null, null, null, now);
  w.run(1, 'product', 'Copper Creek', 'ground beef', null, null, null, null, now);
  w.run(1, 'category', null, null, null, null, 'infant acetaminophen', null, now);
  w.run(1, 'vin', null, null, null, '1MER5A2XKL0091223', null, null, now);

  console.log('\n1. Ingest (fixtures, no network)');
  for (const name of ['fda', 'fsis', 'nhtsa']) {
    const r = await ingest(db, new FixtureSource(name, FIXTURES), '2026-01-01', now);
    console.log(`   ${r.source}: fetched ${r.fetched}, created ${r.created}, unchanged ${r.unchanged}`);
  }

  console.log('\n2. Ingest again — should change nothing');
  for (const name of ['fda', 'fsis', 'nhtsa']) {
    const r = await ingest(db, new FixtureSource(name, FIXTURES), '2026-01-01', now);
    console.log(`   ${r.source}: fetched ${r.fetched}, created ${r.created}, unchanged ${r.unchanged}`);
  }

  console.log('\n3. Match');
  console.log(`   ${JSON.stringify(runMatching(db, now))}`);
  for (const m of db.prepare(
    'SELECT m.confidence, r.title, m.reason FROM matches m JOIN recalls r ON r.id = m.recall_id ORDER BY m.confidence',
  ).all() as Record<string, unknown>[]) {
    const reason = JSON.parse(String(m.reason));
    console.log(`   [${String(m.confidence).padEnd(9)}] ${m.title}\n               ${reason.detail}`);
  }

  console.log('\n4. Queue (high severity only; candidates need a human)');
  console.log(`   queued ${enqueue(db, now)}`);

  console.log('\n5. Deliver');
  const provider = pickProvider(process.env);
  console.log(`   ${JSON.stringify(await deliverBatch(db, provider, 20, Date.parse(now)))}`);

  console.log('\n6. Deliver again — nothing left to send');
  console.log(`   ${JSON.stringify(await deliverBatch(db, provider, 20, Date.parse(now)))}\n`);
}
