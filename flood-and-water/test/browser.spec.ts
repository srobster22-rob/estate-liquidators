import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const SCREENS = [
  { name: 'coverage', path: '/' },
  { name: 'now', path: '/#/now' },
  { name: 'prepare', path: '/#/prepare' },
  { name: 'log', path: '/#/log' },
  { name: 'about', path: '/#/about' },
];

for (const s of SCREENS) {
  test(`axe: ${s.name}`, async ({ page }) => {
    await page.goto(s.path);
    await page.waitForSelector('#app h1');
    const r = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
    if (r.violations.length) console.log(JSON.stringify(r.violations, null, 2));
    expect(r.violations).toEqual([]);
  });
}

test('the waiting period renders as a real future date, not a duration', async ({ page }) => {
  await page.goto('/');
  const shown = await page.locator('.bigdate').innerText();
  expect(shown).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  const days = (new Date(shown).getTime() - Date.now()) / 86_400_000;
  expect(days).toBeGreaterThan(28);
  expect(days).toBeLessThan(31);
});

test('checking the mortgage exception collapses the wait to today', async ({ page }) => {
  await page.goto('/');
  await page.locator('details summary').click();
  await page.locator('input[name="exc"][value="mortgage"]').check();
  const shown = await page.locator('.bigdate').innerText();
  expect(shown).toBe(new Date().toISOString().slice(0, 10));
});

test('unknown coverage is never rendered as a confirmed gap', async ({ page }) => {
  await page.goto('/');
  const text = await page.locator('#app').innerText();
  expect(text).toContain('Worth checking');
  expect(text).not.toContain('Not covered —');
});

test('the emergency screen leads with never driving into floodwater', async ({ page }) => {
  await page.goto('/#/now');
  const h1 = await page.locator('.emergency h1').innerText();
  expect(h1.toLowerCase()).toContain('never walk or drive');
  const box = await page.locator('.emergency').boundingBox();
  expect(box!.y).toBeLessThan(300); // above the fold, not below the chrome
});

test('the damage log records an entry and reports the chain intact', async ({ page }) => {
  await page.goto('/#/log');
  await page.locator('#note').fill('Water reached the third step');
  await page.locator('#add').click();
  await expect(page.locator('.chain-ok')).toContainText('intact');
  await expect(page.locator('.entry')).toHaveCount(1);
  await page.reload();
  await expect(page.locator('.entry')).toHaveCount(1); // survives a reload
});

test('the methodology text is printed with the log', async ({ page }) => {
  await page.goto('/#/log');
  const text = await page.locator('#app').innerText();
  expect(text).toContain('does not show');
  expect(text).toContain('not a notarization');
});

test('no request leaves the origin', async ({ page }) => {
  const foreign: string[] = [];
  page.on('request', (r) => {
    const u = new URL(r.url());
    if (!['localhost', '127.0.0.1'].includes(u.hostname)) foreign.push(r.url());
  });
  for (const s of SCREENS) { await page.goto(s.path); await page.waitForSelector('#app h1'); }
  expect(foreign).toEqual([]);
});

test('200% zoom on 360px does not scroll sideways', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 640 });
  for (const s of SCREENS) {
    await page.goto(s.path);
    await page.waitForSelector('#app h1');
    await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, s.name).toBeLessThanOrEqual(1);
  }
});

test('screenshots', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const s of ['/', '/#/now']) {
    await page.goto(s);
    await page.waitForSelector('#app h1');
    await page.screenshot({ path: `screenshots/${s === '/' ? 'coverage' : 'now'}.png`, fullPage: true });
  }
});

test('the emergency screen works with the network cut', async ({ page, context }) => {
  await page.goto('/');
  await page.waitForSelector('#app h1');
  await page.waitForTimeout(700); // let the worker install and claim
  await context.setOffline(true);
  await page.goto('/#/now');
  await expect(page.locator('.emergency h1')).toContainText(/never walk or drive/i);
  await page.goto('/#/log');
  await expect(page.locator('#note')).toBeVisible();
  await context.setOffline(false);
});

test('the damage record exports a PDF containing the methodology', async ({ page }) => {
  await page.goto('/#/log');
  await page.locator('#note').fill('Water reached the third step');
  await page.locator('#add').click();
  await expect(page.locator('.entry')).toHaveCount(1);

  const download = page.waitForEvent('download');
  await page.locator('#export').click();
  const file = await download;
  const stream = await file.createReadStream();
  const chunks: Buffer[] = [];
  for await (const c of stream) chunks.push(c as Buffer);
  const pdf = Buffer.concat(chunks);
  expect(pdf.subarray(0, 5).toString()).toBe('%PDF-');
  expect(pdf.length).toBeGreaterThan(1000);
});

test('a refused write is reported, not swallowed, and the entry survives', async ({ page }) => {
  // The failure this guards: a full device or a private window makes localStorage.setItem throw,
  // and the entry the user just typed disappears with no message.
  await page.goto('/#/log');
  await page.addInitScript(() => {
    const real = Storage.prototype.setItem;
    Storage.prototype.setItem = function (k: string, v: string) {
      if (k === 'fw.chain') throw new DOMException('quota', 'QuotaExceededError');
      return real.call(this, k, v);
    };
  });
  await page.reload();
  await page.waitForSelector('#note');

  const alerts: string[] = [];
  page.on('dialog', (d) => { alerts.push(d.message()); void d.accept(); });

  await page.locator('#note').fill('Water reached the third step');
  await page.locator('#add').click();
  await expect.poll(() => alerts.length).toBe(1);
  expect(alerts[0]).toMatch(/would not save/i);

  // Still on screen, and clearly flagged as not saved.
  await expect(page.locator('.entry')).toHaveCount(1);
  await expect(page.locator('.callout-danger')).toContainText(/not saved on this device/i);

  // And still exportable, which is the whole point of keeping it in memory.
  const download = page.waitForEvent('download');
  await page.locator('#export').click();
  expect((await download).suggestedFilename()).toMatch(/\.pdf$/);
});

test('the originals ZIP round-trips photo bytes and lists them in a manifest', async ({ page }) => {
  await page.goto('/#/log');
  await page.locator('#note').fill('Water line on the north wall');
  // A tiny PNG with no EXIF: the manifest must report cameraTimestamp null rather than passing
  // the import date off as a capture time.
  await page.locator('#photo').setInputFiles({
    name: 'wall.png',
    mimeType: 'image/png',
    buffer: Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      'base64',
    ),
  });
  await page.locator('#add').click();
  await expect(page.locator('.entry')).toHaveCount(1);

  const download = page.waitForEvent('download');
  await page.locator('#export-zip').click();
  const file = await download;
  expect(file.suggestedFilename()).toMatch(/^water-damage-originals-\d{4}-\d{2}-\d{2}\.zip$/);

  const stream = await file.createReadStream();
  const chunks: Buffer[] = [];
  for await (const c of stream) chunks.push(c as Buffer);
  const zipBytes = Buffer.concat(chunks);
  expect(zipBytes.subarray(0, 2).toString()).toBe('PK');

  // The signature proves nothing. What matters is that every hash in the manifest matches the
  // bytes actually in the archive — that is the claim the record makes to an adjuster. Checked
  // with Python, which knows nothing about the writer.
  const dir = mkdtempSync(join(tmpdir(), 'zip-e2e-'));
  const zipPath = join(dir, 'originals.zip');
  writeFileSync(zipPath, zipBytes);

  const script = [
    'import json, zipfile, hashlib',
    `z = zipfile.ZipFile(${JSON.stringify(zipPath)})`,
    'assert z.testzip() is None',
    'm = json.loads(z.read("manifest.json"))',
    'ok = all(hashlib.sha256(z.read(p["file"])).hexdigest() == p["sha256"] for p in m["photos"])',
    'print(json.dumps({"names": z.namelist(), "hashesMatch": ok, "manifest": m}))',
  ].join('\n');
  const parsed = JSON.parse(execFileSync('python3', ['-c', script], { encoding: 'utf8' }));

  expect(parsed.names).toContain('manifest.json');
  expect(parsed.names).toContain('METHODOLOGY.txt');
  expect(parsed.hashesMatch).toBe(true);
  expect(parsed.manifest.photoCount).toBe(1);
  expect(parsed.manifest.chainIntact).toBe(true);
  expect(parsed.manifest.missingFromDevice).toEqual([]);
  // A PNG with no EXIF must report null, not the import date dressed up as a capture time.
  expect(parsed.manifest.photos[0].cameraTimestamp).toBeNull();
  expect(parsed.manifest.photos[0].addedToRecord).toMatch(/^\d{4}-\d{2}-\d{2}$/);
});
