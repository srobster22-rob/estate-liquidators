import { createRequire } from 'node:module';

/**
 * `node:sqlite` is loaded through createRequire rather than a static import.
 *
 * Vite (and therefore vitest) does not have node:sqlite in its builtin list yet: it strips the
 * "node:" prefix, tries to resolve "sqlite" from disk, and the test run dies before a single
 * test collects. A resolve plugin does not help because the normalization happens first.
 * createRequire hands the load straight to Node, so the same code runs under tsx and vitest.
 *
 * The local interface keeps type safety at the call sites. Drop both when Vite learns the
 * module, or when node:sqlite stops being experimental and ships its own types everywhere.
 */
interface SqliteStatement {
  run(...params: unknown[]): { changes: number; lastInsertRowid: number | bigint };
  get(...params: unknown[]): unknown;
  all(...params: unknown[]): unknown[];
}
export interface Db {
  exec(sql: string): void;
  prepare(sql: string): SqliteStatement;
  close(): void;
}

const require = createRequire(import.meta.url);
const { DatabaseSync } = require('node:sqlite') as {
  DatabaseSync: new (path: string) => Db;
};

/**
 * Schema.
 *
 * The two rules that keep this system honest are UNIQUE constraints, not application logic:
 *
 *   recalls (source, source_ref)          — ingest is idempotent. Re-polling changes nothing.
 *   notifications (subscriber_id, recall_id) — one message per person per recall. Ever.
 *
 * Both properties have to survive concurrency and process restarts, which is exactly when a
 * "check then insert" in application code fails. Putting them in the database means the failure
 * mode is a caught constraint violation instead of a duplicate text at 6am.
 */
export function migrate(db: Db): void {
  db.exec(`
    PRAGMA journal_mode = WAL;
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS recalls (
      id INTEGER PRIMARY KEY,
      source TEXT NOT NULL,
      source_ref TEXT NOT NULL,
      title TEXT NOT NULL,
      brands TEXT NOT NULL,
      products TEXT NOT NULL,
      upcs TEXT NOT NULL,
      code_info TEXT NOT NULL DEFAULT '',
      hazard TEXT NOT NULL DEFAULT '',
      severity TEXT NOT NULL DEFAULT 'unknown',
      remedy TEXT NOT NULL DEFAULT '',
      announced_on TEXT NOT NULL,
      url TEXT NOT NULL DEFAULT '',
      raw TEXT NOT NULL DEFAULT '{}',
      first_seen_at TEXT NOT NULL,
      UNIQUE (source, source_ref)
    );

    CREATE TABLE IF NOT EXISTS subscribers (
      id INTEGER PRIMARY KEY,
      phone TEXT NOT NULL UNIQUE,
      language TEXT NOT NULL DEFAULT 'en',
      active INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS watch_items (
      id INTEGER PRIMARY KEY,
      subscriber_id INTEGER NOT NULL REFERENCES subscribers(id),
      kind TEXT NOT NULL,
      brand TEXT, product TEXT, upc TEXT, vin TEXT, category TEXT, lot TEXT,
      created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS matches (
      id INTEGER PRIMARY KEY,
      recall_id INTEGER NOT NULL REFERENCES recalls(id),
      watch_item_id INTEGER NOT NULL REFERENCES watch_items(id),
      confidence TEXT NOT NULL,
      reason TEXT NOT NULL,
      created_at TEXT NOT NULL,
      decision TEXT,
      decided_at TEXT,
      decided_by TEXT,
      -- "Can't tell" is a DEFERRAL, not a decision. It leaves the decision column NULL so the
      -- record stays in the queue; these two only push it to the back and count how often it has
      -- been passed over. Before this existed, the button said "skip" and the code dismissed the
      -- record permanently -- a coordinator who could not tell silently buried a real recall.
      deferred_at TEXT,
      defer_count INTEGER NOT NULL DEFAULT 0,
      UNIQUE (recall_id, watch_item_id)
    );

    CREATE TABLE IF NOT EXISTS notifications (
      id INTEGER PRIMARY KEY,
      subscriber_id INTEGER NOT NULL REFERENCES subscribers(id),
      recall_id INTEGER NOT NULL REFERENCES recalls(id),
      channel TEXT NOT NULL DEFAULT 'sms',
      body TEXT NOT NULL,
      idempotency_key TEXT NOT NULL UNIQUE,
      attempts INTEGER NOT NULL DEFAULT 0,
      claimed_at TEXT,
      sent_at TEXT,
      delivered INTEGER NOT NULL DEFAULT 0,
      dead_lettered_at TEXT,
      last_error TEXT,
      created_at TEXT NOT NULL,
      -- Identifies the physical product rather than the notice. Null when nothing identifies it
      -- confidently; see notify.ts. The partial index below is what makes it load-bearing.
      dedup_key TEXT,
      UNIQUE (subscriber_id, recall_id)
    );

    -- THE SECOND MESSAGE THAT MUST NOT ARRIVE.
    --
    -- UNIQUE (subscriber_id, recall_id) stops one notice texting twice. It cannot stop TWO
    -- notices about the same jar texting once each, which is what happens whenever FDA and FSIS
    -- both announce a product -- routine for anything with meat in it. Two rows, two ids, two
    -- identical texts, and a person who learns that this service repeats itself.
    --
    -- Partial, because dedup_key is null whenever nothing identifies the product confidently.
    -- Suppressing on a guess would mean silence about a real recall, and silence is the one
    -- failure this project will not trade for tidiness.
    CREATE UNIQUE INDEX IF NOT EXISTS idx_notifications_product
      ON notifications (subscriber_id, dedup_key) WHERE dedup_key IS NOT NULL;

    -- A notice that was NOT texted, and why.
    --
    -- Suppression without a record is just a drop with better manners. This table is what lets
    -- somebody answer "why didn't I hear about the FSIS notice" with the actual reason — you
    -- were told about the same UPC under the FDA one — instead of a shrug. It also makes the
    -- suppression count stable across re-runs, which a bare counter is not.
    CREATE TABLE IF NOT EXISTS suppressed_notifications (
      id INTEGER PRIMARY KEY,
      subscriber_id INTEGER NOT NULL REFERENCES subscribers(id),
      recall_id INTEGER NOT NULL REFERENCES recalls(id),
      dedup_key TEXT NOT NULL,
      /* The notice the person actually received instead. */
      superseded_by_recall_id INTEGER REFERENCES recalls(id),
      created_at TEXT NOT NULL,
      UNIQUE (subscriber_id, recall_id)
    );

    CREATE TABLE IF NOT EXISTS ingest_runs (
      id INTEGER PRIMARY KEY,
      source TEXT NOT NULL,
      started_at TEXT NOT NULL,
      finished_at TEXT,
      fetched INTEGER NOT NULL DEFAULT 0,
      created INTEGER NOT NULL DEFAULT 0,
      unchanged INTEGER NOT NULL DEFAULT 0,
      error TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_notifications_pending
      ON notifications (delivered, dead_lettered_at, claimed_at);
  `);
}

export function open(path = ':memory:'): Db {
  const db = new DatabaseSync(path);
  migrate(db);
  return db;
}
