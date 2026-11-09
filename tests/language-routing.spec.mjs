import { test, expect } from '@playwright/test';

const locales = [
  { locale: 'en-US', prefix: '/', language: 'en' },
  { locale: 'fr-FR', prefix: '/mena/fr/', language: 'fr' },
  { locale: 'ar-AE', prefix: '/mena/ar/', language: 'ar' },
];

test('the root serves the browser language when it is supported', async ({ browser }) => {
  for (const item of locales) {
    const context = await browser.newContext({ locale: item.locale });
    const page = await context.newPage();
    await page.goto('/');
    await page.waitForTimeout(300);
    expect(page.url(), item.locale).toContain(item.prefix);
    await expect(page.locator('html')).toHaveAttribute('lang', item.language);
    await context.close();
  }
});

test('an unsupported browser language falls back to the English chooser', async ({ browser }) => {
  const context = await browser.newContext({ locale: 'de-DE' });
  const page = await context.newPage();
  await page.goto('/');
  await page.waitForTimeout(300);
  expect(new URL(page.url()).pathname).toBe('/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await context.close();
});

test('the lang query parameter overrides browser language', async ({ browser }) => {
  const context = await browser.newContext({ locale: 'en-US' });
  const page = await context.newPage();
  await page.goto('/?lang=fr');
  await page.waitForTimeout(300);
  expect(new URL(page.url()).pathname).toBe('/mena/fr/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'fr');
  await context.close();
});

test('localized homepages expose the right language and language links', async ({ page }) => {
  for (const item of locales) {
    const path = item.prefix === '/' ? '/mena/en/index.html' : `${item.prefix}index.html`;
    await page.goto(path);
    await expect(page.locator('html')).toHaveAttribute('lang', item.language);
    const links = page.locator('nav.language a');
    const expected = ['ar', 'en', 'fr'].filter((code) => code !== item.language);
    await expect(links).toHaveCount(expected.length);
    const hrefs = await links.evaluateAll((nodes) => nodes.map((node) => node.getAttribute('hreflang')));
    expect(hrefs.sort()).toEqual(expected.sort());
  }
});
