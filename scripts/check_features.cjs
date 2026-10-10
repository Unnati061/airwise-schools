/* Labelled offline UI faults/layout checks, no AWS/model requests or real passwords. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fixture = JSON.parse(fs.readFileSync('work/d1-ui-fixtures.json', 'utf8'));
const base = 'http://127.0.0.1:5174';
(async () => {
  assert.equal((await fetch(base)).status, 200);
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  let stage = 'start';
  try {
    const page = await browser.newPage();
    let user = 'admin', approved = false, approvalCalls = 0, reportCalls = 0, report = null;
    const bodies = [];
    await page.route('https://cognito-idp.*.amazonaws.com/**', r => {
      user = r.request().postDataJSON().AuthParameters.USERNAME.includes('teacher') ? 'teacher' : 'admin';
      return r.fulfill({ json: { AuthenticationResult: { AccessToken: 'SYNTHETIC_TEST_ONLY', RefreshToken: 'SYNTHETIC_TEST_ONLY', ExpiresIn: 900 } } });
    });
    await page.route('**/api/**', async r => {
      const u = new URL(r.request().url()), p = u.pathname.slice(4);
      let value;
      if (p === '/auth/config') value = { region: 'ap-southeast-2', pool_id: 'SYNTHETIC', client_id: 'SYNTHETIC' };
      else if (p === '/me') value = fixture[user];
      else if (p === '/inputs') value = fixture.next_input;
      else if (p === '/current-plan') value = approved ? fixture.next_current : fixture.review_needed;
      else if (p === '/approved-plans') value = approved ? fixture.history : fixture.before_history;
      else if (p === '/evidence/forecast') value = fixture.evidence;
      else if (p === '/draft-plans') value = fixture.next_plan;
      else if (p.endsWith('/approve')) {
        approved = true; approvalCalls++;
        if (approvalCalls === 1) return r.fulfill({ status: 503, json: { detail: 'SYNTHETIC lost approval response' } });
        value = fixture.next_approval;
      } else if (p.startsWith('/draft-plans/')) value = fixture.next_plan;
      else if (p.endsWith('/review')) value = fixture.review;
      else if (p === '/audit-events') value = fixture.audits;
      else if (p.endsWith('/assignments')) value = fixture.assignments;
      else if (p.endsWith('/reports')) value = report ? [report] : [];
      else if (p.endsWith('/report')) {
        bodies.push(r.request().postDataJSON()); reportCalls++;
        report = { ...bodies.at(-1), actor: fixture.teacher.sub, teacher_id: fixture.teacher.teacher_id, timestamp: new Date().toISOString(), activity_id: '6-a:Mon-2', plan_version: fixture.next_plan.id };
        if (reportCalls === 1) return r.fulfill({ status: 503, json: { detail: 'SYNTHETIC lost report response' } });
        value = report;
      } else if (p.startsWith('/approved-plans/')) value = fixture.next_detail;
      else return r.fulfill({ status: 404, json: { detail: 'Offline route absent' } });
      await r.fulfill({ json: value });
    });
    async function login(username) {
      await page.getByLabel('Username', { exact: true }).fill(username);
      await page.getByLabel('Password', { exact: true }).fill('SYNTHETIC INPUT NOT A CREDENTIAL');
      await page.getByRole('button', { name: 'Sign in', exact: true }).click();
      await page.locator('nav').waitFor();
    }
    await page.goto(base); await login('synthetic-admin');
    stage = 'approval lost response recovery';
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
    await page.getByRole('button', { name: 'Approve this version', exact: true }).click();
    await page.getByRole('button', { name: 'Retry the same request', exact: true }).click();
    await page.getByRole('button', { name: 'Approval recorded', exact: true }).waitFor();
    assert.equal(approvalCalls, 2);
    stage = 'bilingual preview and metrics';
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByText('Review English / Hindi message previews · nothing is sent', { exact: true }).click();
    await page.getByRole('heading', { name: 'Administrator message previews' }).waitFor();
    assert((await page.getByLabel('Hindi preview').inputValue()).includes('केवल पूर्वावलोकन'));
    assert(await page.getByRole('button', { name: 'Copy Hindi', exact: true }).isDisabled());
    await page.getByLabel('I reviewed the dates, assignments and both language versions.').check();
    assert(await page.getByRole('button', { name: 'Download Hindi', exact: true }).isEnabled());
    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download Hindi', exact: true }).click();
    assert((await download).suggestedFilename().endsWith('-hi.txt'));
    await page.getByText('Outdoor student-hours · planned versus teacher-reported', { exact: true }).click();
    await page.getByRole('heading', { name: 'Outdoor student-hour accounting' }).waitFor();
    for (const [width, height] of [[1440, 960], [390, 844]]) {
      await page.setViewportSize({ width, height });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: `${process.env.AIRWISE_SCREENSHOT_DIR || 'work'}/features-${width}.png`, fullPage: true });
    }
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await login('synthetic-teacher-a');
    stage = 'report lost response recovery';
    await page.getByRole('button', { name: 'Report 6-a:Mon-2', exact: true }).click();
    await page.getByLabel('Execution status').selectOption('COULD_NOT_IMPLEMENT');
    await page.getByRole('button', { name: 'Save execution report' }).click();
    await page.getByRole('button', { name: 'Retry the same request', exact: true }).click();
    await page.getByRole('dialog').waitFor({ state: 'hidden' });
    assert.equal(reportCalls, 2); assert.deepEqual(bodies[0], bodies[1]);
    assert.match(bodies[0].request_id, /^[0-9a-f-]{36}$/);
    assert.equal(await page.getByRole('heading', { name: 'Administrator message previews' }).count(), 0);
    console.log('PASS: offline approval/report recovery, same request ID, bilingual review/download, metrics, desktop/mobile overflow. No AWS/model requests.');
  } catch (e) { console.log('FAIL: ' + stage + ' (' + e.name + ')'); process.exitCode = 1; }
  finally { await browser.close(); }
})();
