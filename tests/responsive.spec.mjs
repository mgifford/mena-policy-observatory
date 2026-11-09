import { test, expect } from '@playwright/test';

const homePaths = [
  '/mena/en/index.html',
  '/mena/fr/index.html',
  '/mena/ar/index.html',
];

const representativePaths = [
  '/mena/en/index.html',
  '/mena/en/countries/index.html',
  '/mena/en/coverage/index.html',
  '/mena/en/comparison/index.html',
  '/mena/en/sources/index.html',
  '/mena/en/visualizations/index.html',
  '/mena/en/records/ae-national-digital-accessibility.html',
];

const viewports = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'tablet-landscape', width: 1024, height: 768 },
  { name: 'desktop', width: 1280, height: 900 },
];

test('all localized homepages reflow at mobile, tablet and desktop sizes', async ({ page }) => {
  test.setTimeout(60_000);
  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    for (const path of homePaths) {
      await page.goto(path);
      const overflow = await page.evaluate(() => {
        const root = document.documentElement;
        return root.scrollWidth - root.clientWidth;
      });
      expect(overflow, `${path} overflows at ${viewport.name} (${viewport.width}px)`).toBeLessThanOrEqual(1);
      await expect(page.locator('main h1')).toHaveCount(1);
      await expect(page.locator('.home-paths a')).toHaveCount(4);
      await expect(page.locator('.stat-grid .stat')).toHaveCount(7);
      await expect(page.locator('nav.site-nav')).toBeVisible();
      await expect(page.locator('nav.language')).toBeVisible();
    }
  }
});

test('representative research pages reflow at mobile, tablet and desktop sizes', async ({ page }) => {
  test.setTimeout(60_000);
  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    for (const path of representativePaths) {
      await page.goto(path);
      const overflow = await page.evaluate(() => {
        const root = document.documentElement;
        return root.scrollWidth - root.clientWidth;
      });
      expect(overflow, `${path} overflows at ${viewport.name} (${viewport.width}px)`).toBeLessThanOrEqual(1);
      await expect(page.locator('main h1')).toHaveCount(1);
      await expect(page.locator('main')).toBeVisible();
    }
  }
});
