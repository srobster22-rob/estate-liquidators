/**
 * Local storage for the damage record. IndexedDB for photo bytes, localStorage for the chain.
 *
 * Photo blobs are stored byte-identical and keyed by their own SHA-256, so the same file added
 * twice costs one copy and a stored blob can always be re-hashed to prove it was not altered.
 *
 * Quota is handled explicitly. A flood photo set is large, and a silent QuotaExceededError that
 * loses somebody's claim evidence is the worst thing this module could do — so putBlob throws
 * loudly and the caller tells the user what to do about it.
 */
import type { ChainEntry } from './evidence.js';

const DB = 'fw-evidence';
const STORE = 'blobs';
const CHAIN_KEY = 'fw.chain';

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function putBlob(sha256: string, bytes: Uint8Array): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(bytes, sha256);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error ?? new Error('QuotaExceededError'));
  });
  db.close();
}

export async function getBlob(sha256: string): Promise<Uint8Array | undefined> {
  const db = await openDb();
  const out = await new Promise<Uint8Array | undefined>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly');
    const req = tx.objectStore(STORE).get(sha256);
    req.onsuccess = () => resolve(req.result as Uint8Array | undefined);
    req.onerror = () => reject(req.error);
  });
  db.close();
  return out;
}

export async function loadChain(): Promise<ChainEntry[]> {
  try {
    return JSON.parse(localStorage.getItem(CHAIN_KEY) ?? '[]') as ChainEntry[];
  } catch {
    return [];
  }
}

/** Thrown when the device refuses the write — quota exhausted, or private-mode storage. */
export class StorageUnavailableError extends Error {
  constructor(cause: unknown) {
    super('The record could not be saved on this device.');
    this.name = 'StorageUnavailableError';
    this.cause = cause;
  }
}

/**
 * Persists the chain, and REPORTS failure rather than swallowing it.
 *
 * The original version called setItem unguarded. On a full device, or in a private window where
 * localStorage throws on write, the entry the user had just typed vanished with no message — on
 * an app whose entire purpose is keeping a record somebody can rely on months later. Swallowing
 * the error would have been worse: the entry would sit on screen looking saved until a reload.
 *
 * So the caller is told, keeps the entry in memory, and is pushed to export immediately.
 */
export async function saveChain(chain: ChainEntry[]): Promise<void> {
  try {
    localStorage.setItem(CHAIN_KEY, JSON.stringify(chain));
  } catch (err) {
    throw new StorageUnavailableError(err);
  }
}

/** Shown on the log screen, because running out of space silently is the failure to avoid. */
export async function storageReport(): Promise<string> {
  if (!navigator.storage?.estimate) return 'Stored on this device. Export a backup regularly.';
  try {
    const { usage = 0, quota = 0 } = await navigator.storage.estimate();
    const mb = (n: number) => `${(n / 1024 / 1024).toFixed(1)} MB`;
    const pct = quota ? Math.round((usage / quota) * 100) : 0;
    const warn = pct > 80 ? ' — running low. Export a backup and remove older photos.' : '';
    return `Using ${mb(usage)} of about ${mb(quota)} available on this device (${pct}%)${warn}`;
  } catch {
    return 'Stored on this device. Export a backup regularly.';
  }
}
