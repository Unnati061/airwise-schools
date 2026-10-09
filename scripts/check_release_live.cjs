/* Public notice/real protected wording verification; never exports sessions/passwords. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const crypto = require('node:crypto');
const URL = 'https://main.d29v8cmldu93l3.amplifyapp.com';
let stage = 'public signed-out notice';
(async () => {
  const browser = await chromium.launch({ headless: false, channel: 'chrome' });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  page.setDefaultTimeout(60000);
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'Sign in', exact: true }).waitFor();
    const expected = crypto.createHash('sha256').update(fs.readFileSync('frontend/public/THIRD_PARTY_NOTICES.txt')).digest('hex');
    const notice = await page.evaluate(async () => {
      const response = await fetch('/THIRD_PARTY_NOTICES.txt', { cache: 'no-store', signal: AbortSignal.timeout(15000) });
      const content = await response.arrayBuffer();
      const digest = await crypto.subtle.digest('SHA-256', content);
      return { status: response.status, bytes: content.byteLength,
        sha256: Array.from(new Uint8Array(digest)).map(n => n.toString(16).padStart(2, '0')).join('') };
    });
    assert.equal(notice.status, 200); assert.equal(notice.sha256, expected);
    console.log('PASS: signed-out public notices, matching SHA256 ' + expected);
    stage = 'private administrator sign-in';
    console.log('WAIT: privately sign in as synthetic-admin; passwords must not be shared.');
    await page.getByRole('link', { name: 'Review', exact: true }).waitFor({ timeout: 900000 });
    stage = 'protected revised wording';
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByLabel('English preview').waitFor();
    const english = await page.getByLabel('English preview').inputValue();
    const hindi = await page.getByLabel('Hindi preview').inputValue();
    assert(english.includes('receiving the plan is separate from carrying it out'));
    assert(english.includes('does not establish a school closure or a health benefit'));
    assert(hindi.includes('योजना मिलने की पुष्टि और उसका कार्यान्वयन अलग हैं'));
    assert(hindi.includes('निष्कर्ष नहीं निकाला जा सकता'));
    assert(english.includes('PREVIEW ONLY - NOT SENT') && hindi.includes('भेजा नहीं गया'));
    const result = { public_notice: notice, revised_authenticated_previews: 'PASSED', model_calls: 0, mutations: 0 };
    fs.writeFileSync('work/release-browser-results.json', JSON.stringify(result, null, 2));
    await page.screenshot({ path: 'work/release-live-review.png', fullPage: false });
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.reload();
    await page.getByRole('button', { name: 'Sign in', exact: true }).waitFor();
    console.log('PASS: revised English/Hindi previews through deployed authenticated API; logout/reload signed out.');
    await browser.close();
  } catch (error) {
    console.error('STOPPED: ' + stage + '; ' + error.name);
    await browser.close(); process.exitCode = 1;
  }
})();
