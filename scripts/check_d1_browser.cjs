/* Offline UI fault/layout checks. All authentication/API responses here are test doubles. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, '../work/d1-ui-fixtures.json'), 'utf8'));
const BASE = 'http://127.0.0.1:5173';
let stage = 'startup';

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', () => errors.push('browser error; contents withheld'));
    let user = 'admin', confirmed = false, approved = false, acknowledged = false;
    let analysisCalls = 0, refreshCalls = 0, approvalCalls = 0, denyApproval = false;
    let report = null;
    await page.route('https://cognito-idp.*.amazonaws.com/**', async route => {
      const headers = { 'access-control-allow-origin': BASE, 'access-control-allow-headers': 'content-type,x-amz-target', 'access-control-allow-methods': 'POST' };
      if (route.request().method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
      const request = route.request().postDataJSON();
      if (request.AuthFlow === 'REFRESH_TOKEN_AUTH') refreshCalls++;
      else user = request.AuthParameters.USERNAME === 'synthetic-teacher-a' ? 'teacher' : 'admin';
      await route.fulfill({ headers, json: { AuthenticationResult: { AccessToken: 'SYNTHETIC_BROWSER_TEST_ONLY', RefreshToken: 'SYNTHETIC_BROWSER_REFRESH_ONLY', ExpiresIn: 900 } } });
    });
    await page.route('**/api/**', async route => {
      const url = new URL(route.request().url()), endpoint = url.pathname.slice(4), method = route.request().method();
      let result;
      if (endpoint === '/auth/config') result = { region: 'ap-southeast-2', pool_id: 'SYNTHETIC', client_id: 'SYNTHETIC' };
      else if (endpoint === '/me') result = fixture[user];
      else if (endpoint === '/inputs') result = confirmed ? fixture.next_input : fixture.first;
      else if (endpoint.startsWith('/inputs/')) result = endpoint.endsWith(fixture.first.revision) ? fixture.first : fixture.next_input;
      else if (endpoint === '/current-plan') result = approved ? fixture.next_current : confirmed ? fixture.review_needed : fixture.current;
      else if (endpoint === '/approved-plans') result = approved ? fixture.history : fixture.before_history;
      else if (endpoint === '/evidence/forecast' && url.searchParams.get('mode') === 'LIVE') return route.fulfill({ status: 503, json: { detail: 'SYNTHETIC OFFLINE TEST: live endpoint unavailable, no replay substituted' } });
      else if (endpoint.includes('/evidence/')) result = fixture.evidence;
      else if (endpoint === '/policy-excerpts') result = fixture.policies;
      else if (endpoint === '/notice-analyses') {
        analysisCalls++;
        const notice = route.request().postDataJSON().notice;
        fixture.analysis.notice_sha256 = crypto.createHash('sha256').update(notice).digest('hex');
        result = fixture.analysis;
      } else if (endpoint.endsWith('/confirm')) { confirmed = true; result = fixture.next_input; }
      else if (endpoint.startsWith('/notice-analyses/')) result = fixture.analysis;
      else if (endpoint === '/draft-plans') result = fixture.next_plan;
      else if (endpoint.endsWith('/approve')) {
        approvalCalls++;
        if (denyApproval) return route.fulfill({ status: 409, json: { detail: 'Stale draft input/restriction versions' } });
        approved = true; result = fixture.next_approval;
      } else if (endpoint.startsWith('/draft-plans/')) result = endpoint.endsWith(fixture.next_plan.id) ? fixture.next_plan : fixture.old_detail.plan;
      else if (endpoint.endsWith('/acknowledgements')) { acknowledged = true; result = { actor: fixture.teacher.sub, teacher_id: fixture.teacher.teacher_id, timestamp: new Date().toISOString(), plan_version: fixture.next_plan.id }; }
      else if (endpoint.endsWith('/report') && method === 'PUT') { result = report = { ...route.request().postDataJSON(), actor: fixture.teacher.sub, teacher_id: fixture.teacher.teacher_id, activity_id: '6-a:Mon-2', plan_version: fixture.next_plan.id, timestamp: new Date().toISOString() }; }
      else if (endpoint.endsWith('/assignments')) result = { ...fixture.assignments, acknowledged };
      else if (endpoint.endsWith('/reports')) result = report ? [report] : [];
      else if (endpoint.endsWith('/review')) result = report ? { ...fixture.review, reports: [report], unresolved_activity_ids: ['6-a:Mon-2'], counts: { reported: 1, completed: 0, could_not_implement: 1, needs_clarification: 0, unresolved: 1 } } : fixture.review;
      else if (endpoint === '/audit-events') result = fixture.audits;
      else if (endpoint.startsWith('/approved-plans/')) result = endpoint.endsWith(fixture.next_plan.id) ? fixture.next_detail : fixture.old_detail;
      else return route.fulfill({ status: 404, json: { detail: 'Offline fixture route not found' } });
      await route.fulfill({ json: result });
    });
    async function login(username) {
      await page.getByLabel('Username', { exact: true }).fill(username);
      await page.getByLabel('Password', { exact: true }).fill('SYNTHETIC TEST INPUT, NOT A CREDENTIAL');
      await page.getByRole('button', { name: 'Sign in', exact: true }).click();
      await page.locator('nav').waitFor();
    }
    async function screenshot(view) {
      for (const [label, width, height] of [['desktop', 1440, 960], ['scaled-desktop', 1280, 720], ['compact', 1024, 768], ['tablet', 768, 1024], ['mobile', 390, 844]]) {
        await page.setViewportSize({ width, height });
        await page.evaluate(() => window.scrollTo(0, 0));
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${view}/${label}: document overflow`);
        const logout = page.getByRole('button', { name: 'Sign out', exact: true });
        if (await logout.isVisible()) {
          const bounds = await logout.boundingBox();
          assert(bounds && bounds.x >= 0 && bounds.x + bounds.width <= width && bounds.y >= 0 && bounds.y + bounds.height <= height, `${view}/${label}: sign out clipped`);
        }
        await page.screenshot({ path: path.join(__dirname, `../work/d1-offline-${view}-${label}.png`), fullPage: true });
      }
      await page.setViewportSize({ width: 1440, height: 960 });
    }
    await page.goto(BASE);
    await screenshot('login');
    await login('synthetic-admin');
    stage = 'today';
    await page.getByRole('button', { name: 'Synthetic replay', exact: true }).click();
    await page.getByRole('heading', { name: 'Hourly forecast' }).waitFor();
    await screenshot('today');
    await page.getByRole('link', { name: 'Evidence & restrictions', exact: true }).click();
    stage = 'evidence interpretation';
    await page.getByRole('button', { name: 'Use synthetic notice' }).click();
    assert.equal(analysisCalls, 0);
    await page.getByRole('button', { name: 'Interpret notice', exact: true }).click();
    await page.getByRole('checkbox', { name: 'Outdoor spaces unavailable', exact: true }).waitFor();
    await page.getByRole('checkbox', { name: 'Outdoor spaces unavailable', exact: true }).check();
    await page.getByLabel('Reviewed calendar date').fill('2026-10-12');
    await page.getByRole('checkbox', { name: 'Period 2', exact: true }).check();
    await page.getByLabel('Notice source and authenticity reviewed').check();
    await page.getByLabel('Dates, period scope and ambiguities reviewed').check();
    await screenshot('evidence');
    stage = 'confirmation';
    await page.getByRole('button', { name: 'Confirm reviewed restrictions' }).click();
    await page.getByText('Restrictions confirmed. The existing approved plan is retained', { exact: false }).waitFor();
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    stage = 'draft';
    await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
    await page.getByText('Draft generated; approval is still required.').waitFor();
    await page.getByRole('checkbox', { name: 'Changed activities only' }).check();
    await screenshot('plan');
    denyApproval = true;
    stage = 'stale approval';
    await page.getByRole('button', { name: 'Approve this version' }).click();
    await page.getByText('Stale draft input/restriction versions', { exact: true }).waitFor();
    assert.equal(approvalCalls, 1);
    denyApproval = false;
    await page.getByRole('button', { name: 'Approve this version' }).click();
    await page.getByText('Approval recorded for this version.').waitFor();
    await page.reload();
    await page.getByRole('heading', { name: 'Plan comparison' }).waitFor();
    assert.equal(analysisCalls, 1);
    await page.evaluate(() => { const key = 'airwise.session.v1', value = JSON.parse(sessionStorage.getItem(key)); value.expires = Date.now() - 1; sessionStorage.setItem(key, JSON.stringify(value)); });
    await page.reload();
    await page.locator('nav').waitFor();
    assert.equal(refreshCalls, 1);
    await page.getByRole('button', { name: 'Sign out' }).click();
    assert(await page.evaluate(() => sessionStorage.getItem('airwise.session.v1') === null));
    await login('synthetic-teacher-a');
    stage = 'teacher acknowledgement and report';
    await page.getByRole('button', { name: 'Acknowledge this version' }).click();
    await page.getByRole('button', { name: 'Acknowledged', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Report 6-a:Mon-2', exact: true }).click();
    await page.getByLabel('Execution status').selectOption('COULD_NOT_IMPLEMENT');
    await page.getByLabel('Note (optional)').fill('SYNTHETIC OFFLINE TEST: classroom locked');
    await page.getByRole('button', { name: 'Save execution report' }).click();
    await page.locator('tr[data-activity="6-a:Mon-2"]').getByText('Could not implement', { exact: true }).waitFor();
    await screenshot('inbox');
    await page.goto(`${BASE}/#review`);
    await page.getByText('Administrator access required.', { exact: false }).waitFor();
    await page.getByRole('button', { name: 'Sign out' }).click();
    await login('synthetic-admin');
    stage = 'review';
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByRole('heading', { name: 'Execution exceptions' }).waitFor();
    await page.getByText('SYNTHETIC OFFLINE TEST: classroom locked').first().waitFor();
    await screenshot('review');
    assert.deepEqual(errors, []);
    console.log('PASS OFFLINE ONLY: five views, desktop/mobile, ambiguity/unsupported review, controlled 409, one explicit analysis call, refresh/logout, acknowledgement/exception, role navigation');
  } finally { await browser.close(); }
})().catch(error => { console.error(`FAIL offline browser checks: ${stage}, ${error.name}; request/credential contents withheld`); process.exitCode = 1; });
