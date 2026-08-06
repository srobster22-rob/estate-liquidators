import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import type { RecallSource } from './index.js';
import type { Recall } from '../types.js';

/**
 * Replays recorded feed responses from disk.
 *
 * IMPORTANT: the fixtures in this repository are SYNTHETIC. They are shaped from the documented
 * field names of the real feeds, not captured from them, because this build environment cannot
 * reach fda.gov, fsis.usda.gov, or api.fda.gov. See VERIFY.md — replacing these with real
 * captures is the first thing a maintainer with network access should do.
 */
export class FixtureSource implements RecallSource {
  constructor(
    readonly name: string,
    private readonly dir: string,
  ) {}

  async fetchSince(sinceISODate: string): Promise<Recall[]> {
    const out: Recall[] = [];
    for (const f of readdirSync(this.dir).filter((f) => f.startsWith(this.name) && f.endsWith('.json'))) {
      const parsed = JSON.parse(readFileSync(join(this.dir, f), 'utf8')) as Recall[];
      out.push(...parsed);
    }
    return out.filter((r) => r.announcedOn >= sinceISODate);
  }
}
