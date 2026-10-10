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
  await page.addInitScript(() => { if (!sessionStorage.getItem('airwise.mode')) sessionStorage.setItem('airwise.mode', 'REPLAY'); });
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
    else if (p === '/current-plan') value = state === 'none' ? { ...f.room_current, plan_version: null, needs_review: false } : ['stale', 'pending-stale'].includes(state) ? f.revised_current : f.room_current;
    else if (p === '/approved-plans') value = state === 'none' ? [] : f.room_history;
    else if (p === '/evidence/forecast') {
      value = structuredClone(f.evidence);
      if (state === 'live') { value.snapshot.mode = 'LIVE'; value.freshness = 'FRESH'; }
      if (state === 'missing') value.snapshot.points.forEach(p => { if (p.pollutant === 'PM10') p.value = null; });
    }
    else if (p.startsWith('/draft-plans/')) value = state === 'invalid' ? f.blocked_plan : f.room_plan;
    else if (p.endsWith('/review')) value = state === 'neutral' ? { ...f.room_review, counts: { ...f.room_review.counts, unresolved: 0 }, unresolved_activity_ids: [] } : f.room_review;
    else if (p.startsWith('/approved-plans/')) {
      value = structuredClone(f.room_detail);
      if (state === 'unrestricted') value.plan.input_snapshot.restrictions = [];
      if (state === 'scoped') value.plan.input_snapshot.restrictions.forEach(r => { r.period_ids = ['Mon-3']; r.section_ids = ['6-a']; });
      if (state === 'directional') value.plan.placements.find(a => a.activity_id === '6-a:Mon-4').period_id = 'Tue-4';
    }
    else return r.fulfill({ status: 404, json: { detail: 'Offline route absent' } });
    return r.fulfill({ json: value });
  });
  async function switchState(value) {
    state = value;
    await page.evaluate(({ state, sub }) => {
      if (['pending', 'pending-stale', 'invalid'].includes(state)) sessionStorage.setItem(`airwise.draft.${sub}`, 'offline-draft');
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
    assert((await page.locator('.today-schedule-row').nth(3).innerText()).includes('Classroom lesson'));
    assert((await movement.first().innerText()).includes('Outdoor · restricted'));
    assert((await movement.last().innerText()).includes('Indoor'));
    assert((await movement.first().innerText()).includes('Moved to Period 4'));
    assert((await movement.last().innerText()).includes('Moved from Period 2'));
    assert.equal(await page.getByText('Reciprocal swap: Period 2 ↔ Period 4', { exact: true }).count(), 1);
    assert(!(await page.locator('.today-lesson').allTextContents()).some(text => text.includes('Room:') || text.includes('Preserved')));
    assert((await page.locator('.today-schedule').innerText()).includes('Fixed lesson'));
    assert.equal(await page.locator('.today-stale-plan').count(), 0);
    assert((await page.locator('.today-air-chip').innerText()).includes('PM10 260 µg/m³ · Severe-day scenario'));
    assert.equal(await page.getByText('Demo school · sample data · simulated high-pollution day', { exact: true }).count(), 1);
    assert.equal(await page.locator('.plan-numbers > div').count(), 3);
    assert((await page.locator('.today-retained').innerText()).includes('240 activities retained'));
    assert(await page.locator('.today-lesson.preserved').count() > 0);
    assert.equal(await page.locator('.today-exception').count(), 1);
    assert.equal(await page.locator('.today-change-details').getAttribute('open'), null);
    await page.reload();
    await page.getByRole('link', { name: 'View plan', exact: true }).waitFor();
    assert.equal(await page.locator('.today-stale-plan').count(), 0);
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      assert(await page.evaluate(() => getComputedStyle(document.body).fontSize === '16px'));
      if (width === 1440) assert.equal(Math.round((await page.locator('.sidebar').boundingBox()).width), 200);
      const row = await page.locator('.today-schedule-row').first().boundingBox();
      console.log(`Today ${width}: first timetable row at y=${Math.round(row.y)}`);
      if (width === 390) assert(await page.locator('.today-mobile-label').first().isVisible());
      await page.screenshot({ path: path.join(output, `today-approved-${width}.png`), fullPage: true });
      await page.screenshot({ path: path.join(output, `today-viewport-${width}.png`) });
      assert(row.y < (width === 1440 ? 650 : 844));
    }
    await page.locator('.today-schedule-row').nth(2).scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(output, 'today-mobile-lessons.png') });
    await page.evaluate(() => scrollTo(0, 0));
    await page.getByLabel('Today timetable class').selectOption('6-b');
    assert((await page.locator('.today-schedule-row').nth(2).innerText()).includes('Movement hall'));
    await switchState('stale');
    assert((await page.locator('.today-stale-plan').innerText()).includes('Plan inputs changed since approval. Review before relying on this plan.'));
    assert.equal(await page.locator('.today-stale-plan a').getAttribute('href'), '#plan');
    assert.equal(await page.locator('.today-headline h2').innerText(), 'Plan needs review');
    assert((await page.locator('.today-validation-note').innerText()).includes('this stored version, not the changed inputs'));
    assert((await page.locator('.today-schedule').innerText()).includes('Previously approved'));
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: path.join(output, `today-stale-${width}.png`) });
    }
    await switchState('unrestricted');
    assert.equal(await page.locator('.today-restricted').count(), 0);
    await switchState('scoped');
    assert.equal(await page.locator('.today-restricted').count(), 0);
    await page.getByLabel('Today timetable class').selectOption('6-b');
    assert.equal(await page.locator('.today-restricted').count(), 0);
    await switchState('directional');
    // Rendering-only test double: not a claim that this altered plan is solver-valid.
    const directional = page.locator('.today-lesson[data-activity="6-a:Mon-2"]').first();
    assert((await directional.innerText()).includes('Moved to Period 4'));
    assert(!(await directional.innerText()).includes('↔'));
    assert.equal(await page.locator('.today-swap-summary').count(), 0);
    await switchState('live');
    await page.getByRole('button', { name: 'Live', exact: true }).click();
    await page.getByText('Demo school · sample school data', { exact: true }).waitFor();
    await page.waitForFunction(() => document.querySelector('.today-air-chip')?.textContent.includes('regional forecast · LIVE'));
    assert((await page.locator('.today-air-chip').innerText()).includes('regional forecast · LIVE'));
    assert(!(await page.locator('.today-air-chip').innerText()).includes('REPLAY'));
    await switchState('missing');
    assert((await page.locator('.today-air-chip').innerText()).includes('PM10 unavailable'));
    await switchState('pending');
    await page.getByRole('link', { name: 'Review draft', exact: true }).waitFor();
    assert((await page.locator('.today-decision-summary').innerText()).includes('proposed indoor alternatives'));
    assert((await page.locator('.today-schedule').innerText()).includes('Proposed'));
    await switchState('pending-stale');
    await page.getByRole('link', { name: 'Review draft', exact: true }).waitFor();
    assert((await page.locator('.today-headline h2').innerText()).includes('proposed indoor alternatives'));
    assert((await page.locator('.today-schedule').innerText()).includes('Proposed · not approved'));
    assert(!(await page.locator('.today-schedule').innerText()).includes('Previously approved'));
    await switchState('invalid');
    assert((await page.locator('.today-decision-summary').innerText()).includes('no validated repair'));
    assert.equal(await page.locator('.today-schedule').count(), 0);
    await switchState('none');
    await page.getByRole('link', { name: 'Review evidence', exact: true }).waitFor();
    assert.equal(await page.locator('.today-schedule').count(), 0);
    await switchState('neutral');
    assert.equal(await page.locator('.today-exception').count(), 0);
    assert.equal(await page.locator('.today-stale-plan').count(), 0);
    await page.getByRole('link', { name: 'View plan', exact: true }).waitFor();
    const roomAction = page.getByRole('link', { name: 'What if a room is unavailable?', exact: true });
    assert.equal(await roomAction.getAttribute('href'), '#plan');
    await roomAction.click();
    await page.getByLabel('Room to exclude', { exact: true }).waitFor();
    assert.equal(mutations, 0); assert.equal(errors.length, 0);
    console.log('PASS: decision states, LIVE/REPLAY/missing PM10, explicit restriction scopes, reciprocal/directional labels, retained count, stale flag/action, desktop/mobile, read-only Today. Offline only.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e.stack); process.exitCode = 1; });
