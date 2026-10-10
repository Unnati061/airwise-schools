/* Existing hosted app; private sign-in, sample workflow, zero paid model calls. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const API = 'https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com';
const HOSTED_URL = 'https://main.d29v8cmldu93l3.amplifyapp.com';
assert.equal(new URL(API + '/me').pathname, '/me');
let stage = 'startup';
(async () => {
  const browser = await chromium.launch({ headless: false, channel: 'chrome', args: ['--start-maximized'] });
  const page = await browser.newPage({ viewport: null });
  const display = await page.context().newCDPSession(page);
  page.setDefaultTimeout(60000);
  const requests = [];
  page.on('response', response => {
    if (response.url().startsWith(API)) requests.push({ method: response.request().method(), path: new URL(response.url()).pathname, status: response.status() });
  });
  await page.addInitScript(api => {
    window.__product = { values: {} };
    const original = window.fetch;
    window.fetch = async (...args) => {
      const response = await original(...args);
      if (String(args[0]).startsWith(api)) window.__product.values[new URL(String(args[0])).pathname] = await response.clone().json().catch(() => null);
      return response;
    };
    window.__productCall = async (path, method = 'GET', body, expected = 200) => {
      const session = JSON.parse(sessionStorage.getItem('airwise.session.v1'));
      const response = await fetch(api + path, { method, headers: { Authorization: 'Bearer ' + session.access,
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: AbortSignal.timeout(35000) });
      if (response.status !== expected) throw new Error('Unexpected status');
      return response.json();
    };
  }, API);
  async function login(role) {
    await display.send('Emulation.clearDeviceMetricsOverride');
    await page.bringToFront();
    stage = 'private ' + role + ' sign-in';
    console.log('WAIT: privately sign in as ' + role);
    await page.getByRole('link', { name: role === 'synthetic-admin' ? 'Review' : 'Teacher inbox', exact: true }).waitFor({ timeout: 900000 });
  }
  async function logout() {
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.reload();
    await page.getByRole('button', { name: 'Sign in', exact: true }).waitFor();
  }
  async function layouts(name) {
    for (const [width, height] of [[1440, 900], [390, 844]]) {
      await page.setViewportSize({ width, height });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      const rect = await page.getByRole('button', { name: 'Sign out', exact: true }).boundingBox();
      assert(rect && rect.x >= 0 && rect.x + rect.width <= width);
      await page.screenshot({ path: `work/product-live-${name}-${width}.png`, fullPage: true });
    }
    await display.send('Emulation.clearDeviceMetricsOverride');
  }
  try {
    await page.goto(HOSTED_URL);
    let draft;
    if (process.env.AIRWISE_RESUME_APPROVED_VERSION) {
      draft = { version: process.env.AIRWISE_RESUME_APPROVED_VERSION, status: 'OPTIMAL',
        counts: { changed_periods: 2, substitutions: 2, room_moves: 2, deferrals: 0 }, activities: 240 };
      console.log('RESUME: previously verified approval; no new confirmation, draft or approval');
    } else {
    await login('synthetic-admin');
    stage = 'open plan comparison';
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    stage = 'open sample review';
    await page.getByText('Review a sample repair scenario', { exact: true }).click();
    stage = 'select shared-resource sample';
    await page.getByLabel('Sample scenario').selectOption('room-resilience');
    await page.getByLabel('I reviewed and confirm these sample restrictions and permitted placements.').check();
    stage = 'confirm sample inputs';
    await page.getByRole('button', { name: 'Confirm sample inputs' }).click();
    await page.getByText('Sample inputs confirmed.', { exact: false }).waitFor();
    await page.getByText('Review a sample repair scenario', { exact: true }).click();
    stage = 'generate independently validated repair';
    await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
    await page.getByText('Draft generated;', { exact: false }).waitFor();
    await page.getByRole('button', { name: 'Approve this version', exact: true }).waitFor();
    draft = await page.evaluate(() => {
      const p = window.__product.values['/draft-plans'];
      if (!p?.successful || p.solver_status !== 'OPTIMAL' || !p.validation?.valid || p.placements.length !== 240 ||
          p.counts.changed_periods !== 2 || p.counts.substitutions !== 2 || p.counts.room_moves !== 2 || p.counts.deferrals !== 0) throw new Error('Repair differs from validated sample');
      return { version: p.id, status: p.solver_status, counts: p.counts, activities: p.placements.length,
        occupied_room: p.placements.find(a => a.activity_id === '6-a:Mon-2').room_id };
    });
    await page.getByLabel('Changed activities only').uncheck();
    assert((await page.locator('tr[data-activity="7-a:Mon-4"]').innerText()).includes('Preserved · fixed'));
    await page.getByRole('button', { name: 'Approve this version', exact: true }).click();
    await page.getByRole('button', { name: 'Approval recorded', exact: true }).waitFor();
    stage = 'exclude occupied room without replacing approval';
    const baseVersion = draft.version;
    await page.getByLabel('Room to exclude', { exact: true }).selectOption(draft.occupied_room);
    await page.getByLabel('I confirm this sample room is unavailable for the affected day.').check();
    await page.getByRole('button', { name: 'Generate room-change draft', exact: true }).click();
    await page.getByText('Room change confirmed and revised draft generated.', { exact: false }).waitFor();
    draft = await page.evaluate(async ({ baseVersion, excluded }) => {
      const p = window.__product.values['/draft-plans'];
      const current = await window.__productCall('/current-plan');
      const frozen = await window.__productCall(`/approved-plans/${baseVersion}`);
      if (!p.successful || !p.validation.valid || p.solver_status !== 'OPTIMAL' || p.placements.length !== 240 ||
          current.plan_version !== baseVersion || !current.needs_review ||
          p.placements.some(a => a.room_id === excluded && a.period_id?.startsWith('Mon-'))) throw new Error('Room exclusion or approval preservation failed');
      const delta = p.placements.filter(a => { const old = frozen.plan.placements.find(b => b.activity_id === a.activity_id); return a.room_id !== old.room_id || a.period_id !== old.period_id || a.alternative_id !== old.alternative_id; });
      if (delta.length !== 1 || delta[0].activity_id !== '6-a:Mon-2') throw new Error('Unexpected room-change repair');
      return { version: p.id, status: p.solver_status, counts: p.counts, activities: p.placements.length,
        base_version: baseVersion, excluded_room: excluded, revised_room: delta[0].room_id, changed_from_previous: delta.length };
    }, { baseVersion, excluded: draft.occupied_room });
    await page.getByLabel('Changed activities only').check();
    await layouts('room-revision');
    await page.getByRole('button', { name: 'Approve this version', exact: true }).click();
    await page.getByRole('button', { name: 'Approval recorded', exact: true }).waitFor();
    await page.getByLabel('Changed activities only').check();
    await layouts('comparison');
    await page.evaluate(async version => {
      const approved = await window.__productCall(`/draft-plans/${version}/approve`, 'POST');
      const current = await window.__productCall('/current-plan');
      if (approved.plan_version !== version || current.plan_version !== version || current.needs_review) throw new Error('Approval pointer mismatch');
    }, draft.version);
    console.log('PASS: actual sample confirmation, OPTIMAL repair, independent validation, 240 activities, fixed lesson, approval and duplicate receipt');
    await logout();
    }
    await login('synthetic-teacher-a');
    stage = 'teacher acknowledgement and exception';
    if (!process.env.AIRWISE_RESUME_REPORTED) {
    await page.getByRole('button', { name: 'Acknowledge this version', exact: true }).click();
    await page.getByRole('button', { name: 'Acknowledged', exact: true }).waitFor();
    await page.evaluate(async version => {
      const reports = await window.__productCall(`/teachers/teacher-6-a/reports?version=${encodeURIComponent(version)}`);
      if (reports.length) throw new Error('Acknowledgement became execution');
    }, draft.version);
    await page.getByRole('button', { name: 'Report 6-a:Mon-2', exact: true }).click();
    await page.getByLabel('Execution status').selectOption('COULD_NOT_IMPLEMENT');
    await page.getByLabel('Note (optional)').fill('Demo report: room unavailable at implementation (sample event, not an observed school condition).');
    await page.getByRole('button', { name: 'Save execution report' }).click();
    await page.getByRole('dialog').waitFor({ state: 'hidden' });
    }
    await page.evaluate(async version => {
      const path = `/approved-plans/${version}/activities/6-a%3AMon-2/report`;
      const receipt = window.__product.values[path] || (await window.__productCall(`/teachers/teacher-6-a/reports?version=${encodeURIComponent(version)}`)).find(r => r.activity_id === '6-a:Mon-2');
      if (!receipt?.request_id) throw new Error('No report receipt');
      const duplicate = await window.__productCall(path, 'PUT', { request_id: receipt.request_id, status: receipt.status, note: receipt.note });
      if (duplicate.timestamp !== receipt.timestamp) throw new Error('Duplicate report');
      await window.__productCall(`/draft-plans/${version}/approve`, 'POST', undefined, 403);
      await window.__productCall('/teachers/teacher-6-b/assignments', 'GET', undefined, 403);
      await window.__productCall('/inputs', 'GET', undefined, 403);
    }, draft.version);
    await layouts('teacher');
    await page.evaluate(() => { location.hash = 'inbox'; });
    await page.waitForFunction(() => location.hash === '#inbox');
    await page.waitForTimeout(100);
    await page.evaluate(() => { location.hash = 'plan'; });
    await page.getByText('Administrator access required.', { exact: false }).waitFor();
    await page.getByRole('link', { name: 'Open your teacher inbox' }).click();
    console.log('PASS: actual separate acknowledgement/exception, report receipt reuse, teacher approval/cross-teacher/input denials and navigation guard');
    await logout(); await login('synthetic-admin');
    stage = 'administrator persisted report and overview';
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByRole('heading', { name: 'Execution exceptions', exact: true }).waitFor();
    await page.getByText('Demo report: room unavailable at implementation (sample event, not an observed school condition).', { exact: true }).first().waitFor();
    const result = await page.evaluate(async version => {
      const r = await window.__productCall(`/approved-plans/${version}/review`);
      const history = await window.__productCall('/approved-plans');
      if (r.counts.reported !== 1 || r.counts.completed !== 0 || r.counts.unresolved !== 1 ||
          !history.find(p => p.plan_version === version && p.current)) throw new Error('Persisted review mismatch');
      return { counts: r.counts, metrics: r.outdoor_metrics, approval_versions: history.length };
    }, draft.version);
    await layouts('review');
    await page.getByRole('link', { name: 'Today', exact: true }).click();
    await page.getByRole('heading', { name: 'Implementation', exact: true }).waitFor();
    await page.getByText('Demo report: room unavailable at implementation (sample event, not an observed school condition).', { exact: true }).waitFor();
    await layouts('today');
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    await page.getByRole('button', { name: 'Approval recorded', exact: true }).waitFor();
    await page.getByLabel('Changed activities only').check();
    await layouts('comparison');
    fs.writeFileSync('work/product-live-results.json', JSON.stringify({ label: 'ACTUAL HOSTED WORKFLOW, SAMPLE SCHOOL DATA, ZERO MODEL CALLS',
      version: draft.version, status: draft.status, activities: draft.activities,
      repair_counts: draft.counts, execution_counts: result.counts,
      room_scenario: { base_version: draft.base_version, excluded_room: draft.excluded_room,
        revised_room: draft.revised_room, changed_from_previous: draft.changed_from_previous },
      metrics: result.metrics, approval_versions: result.approval_versions }, null, 2));
    console.log('PASS: persisted admin Review/Today, version history, planned/reported distinction and desktop/mobile layouts');
    await logout();
  } catch (e) {
    console.log('FAIL: ' + stage + ' (' + e.name + '); credentials and bodies withheld');
    fs.writeFileSync('work/product-live-failure.json', JSON.stringify({ stage, error_class: e.name, requests }, null, 2));
    if (await page.locator('nav').count() && !await page.locator('input[type="password"]').count()) await page.screenshot({ path: 'work/product-live-failure.png', fullPage: true });
    process.exitCode = 1;
  }
  finally { await browser.close(); }
})();
