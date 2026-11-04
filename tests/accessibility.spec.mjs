import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readdirSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const distDir = fileURLToPath(new URL('../dist/', import.meta.url));

function htmlFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) return htmlFiles(full);
    return entry.name.endsWith('.html') ? [full] : [];
  });
}

const pages = htmlFiles(distDir)
  .sort()
  .map((file) => '/' + relative(distDir, file).split(sep).join('/'));

for (const path of pages) {
  test(`${path} has no axe violations`, async ({ page }) => {
    await page.goto(path);
    await expect(page.locator('main h1')).toHaveCount(1);
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });

  test(`${path} keyboard skip link moves focus to main`, async ({ page }) => {
    await page.goto(path);
    await page.keyboard.press('Tab');
    await expect(page.locator('a.skip')).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('#main')).toBeFocused();
  });

  test(`${path} reflows at 640 and 320 CSS pixels`, async ({ page }) => {
    for (const width of [640, 320]) {
      await page.setViewportSize({ width, height: 800 });
      await page.goto(path);
      const overflow = await page.evaluate(() => {
        const root = document.documentElement;
        return root.scrollWidth - root.clientWidth;
      });
      expect(overflow, `${path} overflows horizontally at ${width}px`).toBeLessThanOrEqual(1);
    }
  });
}

test('document titles are unique and descriptive', async ({ page }) => {
  const seen = new Map();
  for (const path of pages) {
    await page.goto(path);
    const title = (await page.title()).trim();
    expect(title.length, `${path} has a very short title`).toBeGreaterThan(10);
    expect(seen.has(title), `${path} repeats the title used by ${seen.get(title)}`).toBeFalsy();
    seen.set(title, path);
  }
  expect(seen.size).toBe(pages.length);
});

test('language switch reaches the equivalent page', async ({ page, request }) => {
  for (const path of pages) {
    await page.goto(path);
    const switchHref = await page.locator('.language a').getAttribute('href');
    expect(switchHref, `${path} needs a language switch`).toBeTruthy();
    const alternates = await page.locator('link[rel="alternate"][hreflang]').evaluateAll((nodes) =>
      nodes.map((node) => ({ hreflang: node.getAttribute('hreflang'), href: node.getAttribute('href') })),
    );
    const expected = path.includes('/ar/') ? 'en' : 'ar';
    const alternate = alternates.find((item) => item.hreflang === expected);
    expect(alternate, `${path} needs hreflang=${expected}`).toBeTruthy();
    const switchUrl = new URL(switchHref, page.url()).href;
    expect(switchUrl, `${path} language link does not match the alternate`).toBe(
      new URL(alternate.href, page.url()).href,
    );
    const response = await request.get(switchUrl);
    expect(response.ok(), `${switchUrl} is not reachable`).toBeTruthy();
    await page.goto(switchUrl);
    await expect(page.locator('html')).toHaveAttribute('lang', expected);
    if (path.includes('/records/')) {
      const recordFile = path.split('/').pop();
      expect(page.url(), `${path} loses the record on language switch`).toContain(`/records/${recordFile}`);
    }
  }
});
