import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
for (const region of ['mena']) for (const locale of ['en','ar']) {
 test(`${region}/${locale} has no axe violations`, async ({page}) => {
   await page.goto(`/${region}/${locale}/`);
   await expect(page.locator('main h1')).toHaveCount(1);
   await expect(page.locator('html')).toHaveAttribute('lang',locale);
   await expect(page.locator('html')).toHaveAttribute('dir',locale==='ar'?'rtl':'ltr');
   const results=await new AxeBuilder({page}).analyze();
   expect(results.violations).toEqual([]);
 });
 test(`${region}/${locale} keyboard skip link`, async ({page}) => {
   await page.goto(`/${region}/${locale}/`);
   await page.keyboard.press('Tab');
   await expect(page.locator('a.skip')).toBeFocused();
   await page.keyboard.press('Enter');
   await expect(page.locator('#main')).toBeFocused();
 });
}
