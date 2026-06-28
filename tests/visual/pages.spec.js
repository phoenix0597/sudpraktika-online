const { test, expect } = require('@playwright/test');

const PAGES = [
  { name: 'home', path: '/' },
  { name: 'zpp-section', path: '/zpp/' },
  { name: 'situation-goods-defect', path: '/zpp/praktika/nekachestvennyy-tovar/' },
  { name: 'situation-service-refusal', path: '/zpp/praktika/vozvrat-deneg-za-uslugu/' },
  { name: 'case-important-points', path: '/zpp/dela/9xUCtLJ9m3HR/' },
  { name: 'case-legal-analysis', path: '/zpp/dela/xyw1pNsfewV8/' },
  { name: 'case-long-title', path: '/zpp/dela/3mMKR7CNUYQ8/' },
];

const VIEWPORTS = [
  { name: 'desktop', size: { width: 1366, height: 900 } },
  { name: 'mobile', size: { width: 390, height: 844 } },
];

async function stabilizePage(page) {
  await page.evaluate(async () => {
    if (document.fonts?.ready) {
      await document.fonts.ready;
    }
  });
}

for (const viewport of VIEWPORTS) {
  test.describe(`visual ${viewport.name}`, () => {
    test.use({ viewport: viewport.size });

    for (const pageCase of PAGES) {
      test(`${pageCase.name}`, async ({ page }) => {
        await page.goto(pageCase.path);
        await stabilizePage(page);
        await expect(page).toHaveScreenshot(`${pageCase.name}-${viewport.name}.png`, {
          animations: 'disabled',
          caret: 'hide',
          fullPage: false,
        });
      });
    }
  });
}
