const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome' });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    for (const [label, width, height] of [['desktop', 1280, 800], ['mobile', 390, 844]]) {
      await page.setViewportSize({ width, height });
      await page.goto('http://127.0.0.1:5173');
      await page.getByRole('status').filter({ hasText: 'Backend connected' }).waitFor();
      assert.equal(await page.locator('tbody tr').count(), 6);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.screenshot({ path: path.join(__dirname, '../work', `frontend-${label}.png`), fullPage: true });
    }
    await page.route('**/api/health', route => route.abort());
    await page.getByRole('button', { name: 'Refresh school' }).click();
    await page.getByRole('status').filter({ hasText: 'Backend unavailable' }).waitFor();
    await page.unroute('**/api/health');
    await page.getByRole('button', { name: 'Refresh school' }).click();
    await page.getByRole('status').filter({ hasText: 'Backend connected' }).waitFor();
    assert.deepEqual(errors, []);
    console.log('PASS: desktop/mobile six sections, no horizontal overflow, error/retry, no browser errors');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
