/* Existing hosted app: private real sign-in; zero model calls/password reads/exports. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const API = 'https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com';
const URL = 'https://main.d29v8cmldu93l3.amplifyapp.com';
let stage = 'start';
(async () => {
  const browser = await chromium.launch({ headless: false, channel: 'chrome', args: ['--start-maximized'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  page.setDefaultTimeout(60000);
  await page.addInitScript(api => {
    window.__features = { values: {} };
    const original = window.fetch;
    window.fetch = async (...args) => {
      const response = await original(...args);
      if (String(args[0]).startsWith(api)) window.__features.values[new URL(String(args[0])).pathname] = await response.clone().json().catch(() => null);
      return response;
    };
    window.__featureCall = async (path, method = 'GET', body, expected = 200) => {
      const session = JSON.parse(sessionStorage.getItem('airwise.session.v1'));
      const response = await fetch(api + path, { method, headers: { Authorization: 'Bearer ' + session.access,
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: AbortSignal.timeout(35000) });
      if (response.status !== expected) throw new Error('Unexpected status');
      return response.json();
    };
  }, API);
  async function login(role) {
    stage = 'private ' + role + ' sign-in';
    console.log('WAIT: privately sign in as ' + role);
    await page.getByRole('link', { name: role === 'synthetic-admin' ? 'Review' : 'Teacher inbox', exact: true }).waitFor({ timeout: 900000 });
  }
  async function logout() {
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.getByRole('button', { name: 'Sign in', exact: true }).waitFor();
  }
  try {
    await page.goto(URL); await login('synthetic-admin');
    stage = 'authenticated synthetic duration revision';
    await page.evaluate(async () => {
      const input = await window.__featureCall('/inputs');
      if (input.input.mode !== 'SYNTHETIC' || input.input.school_id !== 'synthetic-school-001') throw new Error('Unexpected school');
      for (const a of input.input.activities) if (a.duration_minutes == null) a.duration_minutes = 40;
      window.__features.input = await window.__featureCall('/inputs', 'POST', { expected_revision: input.revision, input: input.input });
    });
    await page.reload();
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    stage = 'generate and approve actual validated plan';
    await page.getByRole('button', { name: 'Generate draft', exact: true }).click();
    await page.getByRole('button', { name: 'Approve this version', exact: true }).click();
    await page.getByRole('button', { name: 'Approval recorded', exact: true }).waitFor();
    const version = await page.evaluate(async () => {
      const current = await window.__featureCall('/current-plan');
      const first = await window.__featureCall(`/draft-plans/${current.plan_version}/approve`, 'POST');
      if (first.plan_version !== current.plan_version) throw new Error('Duplicate approval moved pointer');
      return current.plan_version;
    });
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByRole('heading', { name: 'Administrator message previews', exact: true }).waitFor();
    assert((await page.getByLabel('Hindi preview').inputValue()).includes('केवल पूर्वावलोकन'));
    assert(await page.getByRole('button', { name: 'Copy English', exact: true }).isDisabled());
    await page.getByLabel('I reviewed the dates, assignments and both language versions.').check();
    assert(await page.getByRole('button', { name: 'Download Hindi', exact: true }).isEnabled());
    console.log('PASS: actual approved bilingual previews and review gate');
    await logout(); await login('synthetic-teacher-a');
    stage = 'teacher acknowledgement and completion';
    await page.getByRole('button', { name: 'Acknowledge this version', exact: true }).click();
    await page.getByRole('button', { name: 'Acknowledged', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Report 6-a:Mon-2', exact: true }).click();
    await page.getByLabel('Execution status').selectOption('COMPLETED');
    await page.getByLabel('Note (optional)').fill('SYNTHETIC duration-metrics verification only; not a real school activity.');
    await page.getByRole('button', { name: 'Save execution report' }).click();
    await page.getByRole('dialog').waitFor({ state: 'hidden' });
    await page.evaluate(async version => {
      const path = `/approved-plans/${version}/activities/6-a%3AMon-2/report`;
      const receipt = window.__features.values[path];
      if (!receipt?.request_id) throw new Error('No durable request ID');
      const duplicate = await window.__featureCall(path, 'PUT', { request_id: receipt.request_id, status: receipt.status, note: receipt.note });
      if (duplicate.timestamp !== receipt.timestamp) throw new Error('Duplicate execution created');
      await window.__featureCall(`/draft-plans/${version}/approve`, 'POST', undefined, 403);
      await window.__featureCall(`/approved-plans/${version}`, 'GET', undefined, 403);
      await window.__featureCall('/teachers/teacher-6-b/assignments', 'GET', undefined, 403);
    }, version);
    console.log('PASS: actual teacher ack/completion, duplicate receipt and three permission denials');
    await logout(); await login('synthetic-admin');
    stage = 'administrator persistence and metrics';
    const result = await page.evaluate(async version => {
      const review = await window.__featureCall(`/approved-plans/${version}/review`);
      const m = review.outdoor_metrics;
      if (!m.available || m.teacher_reported_completed_indoor_student_hours <= 0 || review.counts.reported !== 1 || m.unknown_indoor_execution_student_hours !== 0) throw new Error('Metric reconciliation failed');
      return { version, counts: review.counts, metrics: m };
    }, version);
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByRole('heading', { name: 'Outdoor student-hour accounting', exact: true }).waitFor();
    for (const [width, height] of [[1440, 960], [390, 844]]) {
      await page.setViewportSize({ width, height });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: `work/features-live-${width}.png`, fullPage: true });
    }
    fs.writeFileSync('work/features-live-results.json', JSON.stringify({ label: 'ACTUAL HOSTED WORKFLOW; SYNTHETIC DATA; ZERO MODEL CALLS', ...result }, null, 2));
    console.log('PASS: ' + JSON.stringify(result));
    await logout();
  } catch (e) { console.log('FAIL: ' + stage + ' (' + e.name + '); no credentials/body logged'); process.exitCode = 1; }
  finally { await browser.close(); }
})();
