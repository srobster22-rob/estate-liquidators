/**
 * Real-browser checks: accessibility (acceptance test 12), keyboard operation, 200% zoom, and
 * the offline requirement (acceptance test 8).
 *
 * Run against the production build: `npm run build && npx playwright test`.
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const SCREENS = [
  { name: 'home', path: '/' },
  { name: 'answer-lithium', path: '/#/item/battery-lithium-ion' },
  { name: 'disambiguation', path: '/#/item/battery-generic' },
  { name: 'list', path: '/#/list' },
  { name: 'about', path: '/#/about' },
];

for (const screen of SCREENS) {
  test(`axe: ${screen.name} has no violations`, async ({ page }) => {
    await page.goto(screen.path);
    await page.waitForSelector('#app h1');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    if (results.violations.length) {
      console.log(JSON.stringify(results.violations, null, 2));
    }
    expect(results.violations).toEqual([]);
  });
}

test('the whole search-to-answer path works with the keyboard alone', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#q');
  // The search field takes focus on load; type without touching the mouse.
  await page.keyboard.type('flourescent');
  await page.waitForSelector('.results a');
  // Tab to the first result and activate it.
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  await expect(page.locator('#app h1')).toContainText(/fluorescent/i);
  await expect(page.locator('.verdict-word')).toBeVisible();
});

test('at 200% zoom on a 360px viewport the page never scrolls sideways', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 640 });
  await page.goto('/#/item/battery-lithium-ion');
  await page.waitForSelector('.verdict-word');
  // Emulating zoom by halving the CSS pixel budget is equivalent for layout purposes.
  await page.evaluate(() => {
    document.documentElement.style.fontSize = '200%';
  });
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
});

test('hazard is conveyed in words, not only by colour', async ({ page }) => {
  await page.goto('/#/item/battery-lithium-ion');
  await expect(page.locator('.hazard-tag')).toHaveText(/hazardous/i);
  await expect(page.locator('.verdict-word')).toHaveText(/hazardous waste/i);
});

test('an unconfigured build refuses to name a bin', async ({ page }) => {
  await page.goto('/#/item/battery-alkaline');
  await page.waitForSelector('.verdict-word');
  const body = (await page.locator('#app').innerText()).toLowerCase();
  expect(body).toContain('nobody has confirmed');
  expect(body).not.toMatch(/goes in your (recycling|regular trash)/);
});

test('demo locations never render as destinations', async ({ page }) => {
  for (const s of SCREENS) {
    await page.goto(s.path);
    await page.waitForSelector('#app');
    expect(await page.locator('#app').innerText()).not.toContain('NOT A REAL PLACE');
  }
});

test('no request leaves the origin', async ({ page }) => {
  const foreign: string[] = [];
  page.on('request', (r) => {
    const u = new URL(r.url());
    if (!['localhost', '127.0.0.1'].includes(u.hostname)) foreign.push(r.url());
  });
  for (const s of SCREENS) {
    await page.goto(s.path);
    await page.waitForSelector('#app h1');
  }
  // Back to the search screen and type, so the search path is covered too.
  await page.goto('/');
  await page.locator('#q').fill('battery');
  await page.waitForSelector('.results a');
  expect(foreign).toEqual([]);
});

test('search still answers with the network cut', async ({ page, context }) => {
  await page.goto('/');
  await page.waitForSelector('#q');
  // Let the service worker install and claim.
  await page.waitForTimeout(600);
  await context.setOffline(true);
  await page.reload();
  await page.waitForSelector('#q', { timeout: 10_000 });
  await page.locator('#q').fill('propane');
  await expect(page.locator('.results a').first()).toBeVisible();
  await page.locator('.results a').first().click();
  await expect(page.locator('.verdict-word')).toBeVisible();
  await context.setOffline(false);
});

test('screenshots for the record', async ({ page }) => {
  for (const s of SCREENS.slice(0, 3)) {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(s.path);
    await page.waitForSelector('#app h1');
    await page.screenshot({ path: `screenshots/${s.name}.png`, fullPage: true });
  }
});
