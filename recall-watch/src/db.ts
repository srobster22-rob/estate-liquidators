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
      last_error TEXT,
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
      ON notifications (delivered, claimed_at);
  `);
}

export function open(path = ':memory:'): Db {
  const db = new DatabaseSync(path);
  migrate(db);
  return db;
}
