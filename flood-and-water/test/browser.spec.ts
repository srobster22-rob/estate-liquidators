import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

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
