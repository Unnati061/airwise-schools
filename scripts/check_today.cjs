/* Read-only frontend test doubles. No AWS, solver changes or paid calls. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const f = JSON.parse(fs.readFileSync('work/d1-ui-fixtures.json'));
const output = process.env.AIRWISE_SCREENSHOT_DIR;
assert(output, 'Set AIRWISE_SCREENSHOT_DIR outside the repository');
fs.mkdirSync(output, { recursive: true });
(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  let state = 'approved', mutations = 0;
  page.on('pageerror', () => errors.push('Page error'));
  await page.route('https://cognito-idp.*.amazonaws.com/**', r => r.fulfill({ json: { AuthenticationResult: { AccessToken: 'SYNTHETIC_TEST_ONLY', RefreshToken: 'SYNTHETIC_TEST_ONLY', ExpiresIn: 900 } } }));
  await page.route('**/api/**', r => {
    const p = new URL(r.request().url()).pathname.slice(4);
    if (r.request().method() !== 'GET') mutations++;
    let value;
    if (p === '/auth/config') value = { region: 'ap-southeast-2', pool_id: 'SYNTHETIC', client_id: 'SYNTHETIC' };
    else if (p === '/me') value = f.admin;
    else if (p === '/inputs') value = f.room_input;
    else if (p === '/current-plan') value = state === 'none' ? { ...f.room_current, plan_version: null, needs_review: false } : f.room_current;
    else if (p === '/approved-plans') value = state === 'none' ? [] : f.room_history;
    else if (p === '/evidence/forecast') value = f.evidence;
    else if (p.startsWith('/draft-plans/')) value = state === 'invalid' ? f.blocked_plan : f.room_plan;
    else if (p.endsWith('/review')) value = state === 'neutral' ? { ...f.room_review, counts: { ...f.room_review.counts, unresolved: 0 }, unresolved_activity_ids: [] } : f.room_review;
    else if (p.startsWith('/approved-plans/')) value = f.room_detail;
    else return r.fulfill({ status: 404, json: { detail: 'Offline route absent' } });
    return r.fulfill({ json: value });
  });
  async function switchState(value) {
    state = value;
    await page.evaluate(({ state, sub }) => {
      if (['pending', 'invalid'].includes(state)) sessionStorage.setItem(`airwise.draft.${sub}`, 'offline-draft');
      else sessionStorage.removeItem(`airwise.draft.${sub}`);
    }, { state, sub: f.admin.sub });
    await page.reload();
    await page.locator('.today-decision-summary').waitFor();
  }
  try {
    await page.goto('http://127.0.0.1:5174');
    await page.getByLabel('Username', { exact: true }).fill('synthetic-admin');
    await page.getByLabel('Password', { exact: true }).fill('SYNTHETIC INPUT NOT A CREDENTIAL');
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('link', { name: 'View plan', exact: true }).waitFor();
    assert((await page.locator('.today-decision-summary').innerText()).includes('2 outdoor lessons: approved indoor alternatives'));
    assert.equal(await page.locator('.today-schedule-row').count(), 8);
    const movement = page.locator('.today-lesson[data-activity="6-a:Mon-2"]');
    assert.equal(await movement.count(), 2);
    assert((await movement.first().innerText()).includes('Sports field'));
    assert((await movement.last().innerText()).includes('Reserve studio'));
    assert((await page.locator('.today-schedule-row').nth(3).innerText()).includes('classroom lesson'));
    assert(await page.locator('.today-lesson.preserved').count() > 0);
    assert.equal(await page.locator('.today-exception').count(), 1);
    assert.equal(await page.locator('.today-change-details').getAttribute('open'), null);
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      assert(await page.evaluate(() => getComputedStyle(document.body).fontSize === '16px'));
      const row = await page.locator('.today-schedule-row').first().boundingBox();
      console.log(`Today ${width}: first timetable row at y=${Math.round(row.y)}`);
      if (width === 390) assert(await page.locator('.today-mobile-label').first().isVisible());
      await page.screenshot({ path: path.join(output, `today-approved-${width}.png`), fullPage: true });
      await page.screenshot({ path: path.join(output, `today-viewport-${width}.png`) });
      assert(row.y < (width === 1440 ? 650 : 844));
    }
    await page.getByLabel('Today timetable class').selectOption('6-b');
    assert((await page.locator('.today-schedule-row').nth(2).innerText()).includes('Movement hall'));
    await switchState('pending');
    await page.getByRole('link', { name: 'Review draft', exact: true }).waitFor();
    assert((await page.locator('.today-decision-summary').innerText()).includes('proposed indoor alternatives'));
    assert((await page.locator('.today-schedule').innerText()).includes('Proposed'));
    await switchState('invalid');
    assert((await page.locator('.today-decision-summary').innerText()).includes('no validated repair'));
    assert.equal(await page.locator('.today-schedule').count(), 0);
    await switchState('none');
    await page.getByRole('link', { name: 'Review evidence', exact: true }).waitFor();
    assert.equal(await page.locator('.today-schedule').count(), 0);
    await switchState('neutral');
    assert.equal(await page.locator('.today-exception').count(), 0);
    const roomAction = page.getByRole('link', { name: 'What if a room is unavailable?', exact: true });
    assert.equal(await roomAction.getAttribute('href'), '#plan');
    await roomAction.click();
    await page.getByLabel('Room to exclude', { exact: true }).waitFor();
    assert.equal(mutations, 0); assert.equal(errors.length, 0);
    console.log('PASS: approved/pending/invalid/no-plan states, real placement/room swaps, preserved activities, class selection, conditional exceptions, desktop/mobile layout, read-only Today. Offline only.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e.stack); process.exitCode = 1; });
