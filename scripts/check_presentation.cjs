/* Labelled offline layout/repair checks: no AWS, passwords or model calls. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fixture = JSON.parse(fs.readFileSync('work/d1-ui-fixtures.json', 'utf8'));
const base = 'http://127.0.0.1:5174';
(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  let stage = 'startup';
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', () => errors.push('browser error'));
    let user = 'admin', confirmed = false, confirmationCalls = 0;
    await page.route('https://cognito-idp.*.amazonaws.com/**', r => {
      user = r.request().postDataJSON().AuthParameters.USERNAME.includes('teacher') ? 'teacher' : 'admin';
      return r.fulfill({ json: { AuthenticationResult: { AccessToken: 'SYNTHETIC_TEST_ONLY', RefreshToken: 'SYNTHETIC_TEST_ONLY', ExpiresIn: 900 } } });
    });
    await page.route('**/api/**', async r => {
      const p = new URL(r.request().url()).pathname.slice(4);
      let value;
      if (p === '/auth/config') value = { region: 'ap-southeast-2', pool_id: 'SYNTHETIC', client_id: 'SYNTHETIC' };
      else if (p === '/me') value = fixture[user];
      else if (p === '/inputs') {
        if (r.request().method() === 'POST') {
          assert.equal(r.request().postDataJSON().expected_revision, fixture.next_input.revision);
          assert.equal(r.request().postDataJSON().input.activities.length, 240);
          confirmationCalls++; confirmed = true;
        }
        value = confirmed ? fixture.shared_input : fixture.next_input;
      } else if (p === '/repair-fixture') value = fixture.shared_fixture;
      else if (p === '/current-plan') value = fixture.next_current;
      else if (p === '/approved-plans') value = fixture.history;
      else if (p === '/evidence/forecast') value = fixture.evidence;
      else if (p === '/draft-plans' || p.startsWith('/draft-plans/')) value = fixture.shared_plan;
      else if (p.endsWith('/review')) value = fixture.review;
      else if (p === '/audit-events') value = fixture.audits;
      else if (p.endsWith('/assignments')) value = fixture.assignments;
      else if (p.endsWith('/reports')) value = [];
      else if (p.startsWith('/approved-plans/')) value = fixture.next_detail;
      else return r.fulfill({ status: 404, json: { detail: 'Offline route absent' } });
      await r.fulfill({ json: value });
    });
    async function login(name) {
      await page.getByLabel('Username', { exact: true }).fill(name);
      await page.getByLabel('Password', { exact: true }).fill('SYNTHETIC INPUT NOT A CREDENTIAL');
      await page.getByRole('button', { name: 'Sign in', exact: true }).click();
      await page.locator('nav').waitFor();
    }
    async function layouts(name) {
      for (const [width, height] of [[1440, 960], [390, 844]]) {
        await page.setViewportSize({ width, height });
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
        const logout = page.getByRole('button', { name: 'Sign out', exact: true });
        const rect = await logout.boundingBox();
        assert(rect && rect.x >= 0 && rect.x + rect.width <= width);
        await page.screenshot({ path: `work/presentation-${name}-${width}.png`, fullPage: true });
      }
      await page.setViewportSize({ width: 1440, height: 960 });
    }
    await page.goto(base); await login('synthetic-admin');
    stage = 'Today operations overview';
    await page.getByRole('heading', { name: 'What has actually been implemented' }).waitFor();
    assert.equal(await page.getByText('Demo school · sample school data', { exact: true }).count(), 1);
    await layouts('today');
    stage = 'sample confirmation and before/after';
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    await page.getByText('Review a sample repair scenario', { exact: true }).click();
    await page.getByLabel('Sample scenario').selectOption('shared-resources');
    assert(await page.getByRole('button', { name: 'Confirm sample inputs' }).isDisabled());
    await page.getByLabel('I reviewed and confirm these sample restrictions and permitted placements.').check();
    await page.getByRole('button', { name: 'Confirm sample inputs' }).click();
    await page.getByText('Sample inputs confirmed.', { exact: false }).waitFor();
    assert.equal(confirmationCalls, 1);
    await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
    await page.getByText('Draft generated;', { exact: false }).waitFor();
    await page.locator('tr[data-activity="6-a:Mon-2"].changed-row').waitFor();
    assert.equal(await page.locator('.changed-row').count(), 3);
    assert((await page.locator('tr[data-activity="6-a:Mon-2"] .after-cell').innerText()).includes('Mon-4'));
    assert((await page.locator('tr[data-activity="7-a:Mon-4"]').innerText()).includes('Preserved · fixed'));
    await page.getByLabel('Changed activities only').check();
    await layouts('comparison');
    const after = await page.locator('.changed-row .after-cell').first().boundingBox();
    assert(after && after.x + after.width <= 1440);
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await login('synthetic-teacher-a');
    await page.getByRole('heading', { name: 'Assignments', exact: true }).waitFor();
    assert.equal(await page.getByRole('link', { name: 'Plan comparison', exact: true }).count(), 0);
    await layouts('teacher');
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.reload();
    await page.getByRole('button', { name: 'Sign in', exact: true }).waitFor();
    assert.equal(errors.length, 0);
    console.log('PASS: operations overview, one demo label, explicit sample confirmation, actual repaired/preserved rows, desktop/mobile sign-out, teacher navigation and logout. Offline only.');
  } catch (e) { console.log('FAIL: ' + stage + ' (' + e.name + ')'); process.exitCode = 1; }
  finally { await browser.close(); }
})();
