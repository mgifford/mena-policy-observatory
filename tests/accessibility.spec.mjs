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

test('language switch reaches every equivalent page', async ({ page, request }) => {
  test.setTimeout(120_000);
  const languages = ['en', 'fr', 'ar'];
  for (const path of pages) {
    const parts = path.split('/');
    const current = parts[1] === 'mena' ? parts[2] : 'en';
    expect(languages, `${path} has an unknown locale`).toContain(current);
    const expected = languages.filter((language) => language !== current);
    await page.goto(path);
    const pageUrl = page.url();
    const switchLinks = await page.locator('.language a').evaluateAll((nodes) =>
      nodes.map((node) => ({ lang: node.getAttribute('hreflang'), href: node.getAttribute('href') })),
    );
    expect(switchLinks.map((link) => link.lang).sort(), `${path} needs both other languages`).toEqual(expected.slice().sort());
    const alternates = await page.locator('link[rel="alternate"][hreflang]').evaluateAll((nodes) =>
      nodes.map((node) => ({ hreflang: node.getAttribute('hreflang'), href: node.getAttribute('href') })),
    );
    for (const language of expected) {
      const alternate = alternates.find((item) => item.hreflang === language);
      expect(alternate, `${path} needs hreflang=${language}`).toBeTruthy();
      const link = switchLinks.find((item) => item.lang === language);
      const switchUrl = new URL(link.href, pageUrl).href;
      expect(switchUrl, `${path} ${language} link does not match the alternate`).toBe(
        new URL(alternate.href, pageUrl).href,
      );
      const response = await request.get(switchUrl);
      expect(response.ok(), `${switchUrl} is not reachable`).toBeTruthy();
      await page.goto(switchUrl);
      await expect(page.locator('html')).toHaveAttribute('lang', language);
      if (path.includes('/records/')) {
        const recordFile = path.split('/').pop();
        expect(page.url(), `${path} loses the record on language switch`).toContain(`/records/${recordFile}`);
      }
    }
  }
});
