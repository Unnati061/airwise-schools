/* Real hosted UI verification: no traces, password reads or token exports. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, '../work/aws-hosting.json')));
const API = 'https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com';
const results = [], timings = [];
let stage = 'startup';
(async () => {
  const browser = await chromium.launch({ headless: false, channel: 'chrome', args: ['--start-maximized'] });
  const page = await browser.newPage({ viewport: null });
  page.setDefaultTimeout(90000);
  await page.addInitScript(api => {
    const original = window.fetch;
    window.__host = { responses: {}, refreshes: 0 };
    window.fetch = async (...args) => {
      const response = await original(...args);
      const url = String(args[0]);
      if (url.startsWith(api)) {
        const value = await response.clone().json().catch(() => null);
        window.__host.responses[new URL(url).pathname] = value;
      }
      if (url.startsWith('https://cognito-idp.')) {
        const value = await response.clone().json().catch(() => null);
        if (value?.AuthenticationResult) {
          window.__host.idToken = value.AuthenticationResult.IdToken;
          if (!value.AuthenticationResult.RefreshToken) window.__host.refreshes++;
        }
      }
      return response;
    };
    window.__hostCall = async (p, method = 'GET', body, expected = 200, override) => {
      const session = JSON.parse(sessionStorage.getItem('airwise.session.v1') || 'null');
      const response = await fetch(api + p, { method,
        headers: { Authorization: 'Bearer ' + (override ?? session?.access ?? ''), ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: AbortSignal.timeout(35000) });
      if (response.status !== expected) {
        window.__host.failure = { path: p, expected, actual: response.status };
        throw new Error('Unexpected HTTP status');
      }
      return response.json();
    };
  }, API);
  page.on('response', response => {
    if (response.url().startsWith(API)) {
      const request = response.request();
      response.finished().then(() => {
        const timing = request.timing();
        timings.push({ path: new URL(response.url()).pathname, method: request.method(), status: response.status(),
          duration_ms: Math.round(timing.responseEnd) });
      }).catch(() => {});
    }
  });
  const pass = (name, values = {}) => { results.push({ check: name, ...values }); console.log('PASS ' + JSON.stringify(results.at(-1))); };
  const login = async role => {
    stage = 'private ' + role + ' sign-in';
    console.log('WAIT: privately sign in as ' + role);
    await page.getByRole('link', { name: role === 'administrator' ? 'Evidence & restrictions' : 'Teacher inbox', exact: true }).waitFor({ timeout: 900000 });
    pass('private ' + role + ' sign-in');
  };
  const action = async (name, predicate, click) => {
    stage = name;
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().startsWith(API) && predicate(r)), click(),
    ]);
    if (response.status() !== 200) throw new Error('Mutation rejected: HTTP ' + response.status());
    await response.finished();
    await page.waitForFunction(p => window.__host.responses[p] !== undefined, new URL(response.url()).pathname);
  };
  const logout = async () => {
    await page.getByRole('button', { name: 'Sign out' }).click();
    const cleared = await page.evaluate(() => sessionStorage.getItem('airwise.session.v1') === null && localStorage.getItem('airwise.session.v1') === null);
    if (!cleared) throw new Error('Session not cleared');
    await page.reload();
    await page.getByRole('button', { name: 'Sign in', exact: true }).waitFor();
    pass('logout and signed-out reload');
  };
  try {
    await page.goto(manifest.origin);
    await page.getByRole('button', { name: 'Sign in', exact: true }).waitFor();
    pass('fresh signed-out hosted browser');
    await login('administrator');
    stage = 'JWT negative checks';
    pass('actual JWT validation', await page.evaluate(async () => {
      const s = JSON.parse(sessionStorage.getItem('airwise.session.v1'));
      const payload = JSON.parse(atob(s.access.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
      if (payload.token_use !== 'access' || payload.client_id !== '5gq58g4sp2o7ic7grg8k7cld2' || payload.iss !== 'https://cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_LhIz6g1r9') throw new Error('Unexpected token claims');
      await window.__hostCall('/me', 'GET', undefined, 403, window.__host.idToken);
      await window.__hostCall('/me', 'GET', undefined, 401, 'invalid-token');
      const pieces = s.access.split('.'); pieces[2] = (pieces[2][0] === 'A' ? 'B' : 'A') + pieces[2].slice(1);
      await window.__hostCall('/me', 'GET', undefined, 401, pieces.join('.'));
      window.__host.idToken = null;
      return { id_token: 403, malformed: 401, tampered_signature: 401, token_use: payload.token_use, expected_issuer_client: true };
    }));
    stage = 'session refresh';
    await page.evaluate(() => {
      const s = JSON.parse(sessionStorage.getItem('airwise.session.v1')); s.expires = 0;
      sessionStorage.setItem('airwise.session.v1', JSON.stringify(s));
    });
    await page.reload();
    await page.getByRole('link', { name: 'Evidence & restrictions', exact: true }).waitFor();
    if (!(await page.evaluate(() => window.__host.refreshes > 0))) throw new Error('Refresh not observed');
    pass('real refresh-token exchange and reload');
    stage = 'live forecast';
    pass('live forecast', await page.evaluate(async () => {
      const v = await window.__hostCall('/evidence/forecast?mode=LIVE');
      if (v.snapshot.mode !== 'LIVE' || v.freshness !== 'FRESH') throw new Error('Live evidence unavailable');
      return { source: v.snapshot.source, retrieved_at: v.snapshot.retrieved_at, model_issue_time: v.snapshot.model_issue_time, freshness: v.freshness, observations_available: v.observations_available };
    }));
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    stage = 'administrator data read';
    try {
      await page.getByRole('button', { name: 'Generate draft', exact: true }).waitFor({ timeout: 15000 });
    } catch (e) {
      // One user-visible read retry only; never repeat a paid call or mutation.
      await page.getByRole('button', { name: 'Retry loading', exact: true }).first().click();
      pass('one read-only administrator data retry');
      await page.getByRole('button', { name: 'Generate draft', exact: true }).waitFor();
    }
    await action('pre-revision draft', r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/draft-plans',
      () => page.getByRole('button', { name: 'Generate draft', exact: true }).click());
    const stale = await page.evaluate(() => window.__host.responses['/draft-plans'].id);
    await page.getByRole('link', { name: 'Evidence & restrictions', exact: true }).click();
    await page.getByRole('button', { name: 'Synthetic replay', exact: true }).click();
    await page.getByRole('button', { name: 'Use synthetic notice' }).click();
    await page.getByLabel('Pasted notice', { exact: false }).fill('SYNTHETIC UNVERIFIED HOSTED CHECK: On 2026-10-12 restrict outdoor PE for section 6A, Monday period 2, using its approved indoor classroom movement alternative. Administrator review is required. This is not a legal closure or GRAP activation order.');
    await action('one bounded Bedrock analysis', r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/notice-analyses',
      () => page.getByRole('button', { name: 'Interpret notice', exact: true }).click());
    pass('bounded Bedrock analysis', await page.evaluate(() => {
      const a = window.__host.responses['/notice-analyses'];
      if (a.status !== 'SUCCESS' || a.mode !== 'REPLAY') throw new Error('Model result invalid');
      return { status: a.status, model: a.model, region: a.region, usage: a.usage, analysis_id: a.id, mode: a.mode };
    }));
    await page.getByRole('checkbox', { name: 'Outdoor spaces unavailable', exact: true }).check();
    await page.getByLabel('Reviewed calendar date').fill('2026-10-12');
    await page.getByRole('checkbox', { name: 'Period 2', exact: true }).check();
    await page.getByLabel('Notice source and authenticity reviewed').check();
    await page.getByLabel('Dates, period scope and ambiguities reviewed').check();
    await action('administrator restriction review', r => r.request().method() === 'POST' && new URL(r.url()).pathname.endsWith('/confirm'),
      () => page.getByRole('button', { name: 'Confirm reviewed restrictions' }).click());
    await page.evaluate(async stale => { await window.__hostCall('/draft-plans/' + stale + '/approve', 'POST', undefined, 409); }, stale);
    pass('stale approval rejected', { status: 409 });
    await page.getByRole('link', { name: 'Plan comparison', exact: true }).click();
    await action('new validated draft', r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/draft-plans',
      () => page.getByRole('button', { name: 'Generate draft', exact: true }).click());
    pass('native solver and validation', await page.evaluate(() => {
      const p = window.__host.responses['/draft-plans'];
      if (!p.successful || !p.validation.valid || p.placements.length !== 240) throw new Error('Invalid plan');
      return { draft_id: p.id, status: p.solver_status, recommendation: p.recommendation, counts: p.counts, activities: p.placements.length };
    }));
    await action('administrator approval', r => r.request().method() === 'POST' && new URL(r.url()).pathname.endsWith('/approve'),
      () => page.getByRole('button', { name: 'Approve this version' }).click());
    await page.getByText('Approval recorded for this version.').waitFor();
    const version = await page.evaluate(() => window.__host.responses['/draft-plans'].id);
    pass('hosted approval', { plan_version: version });
    await logout();
    await login('teacher');
    stage = 'teacher denials';
    await page.evaluate(async v => {
      await window.__hostCall('/draft-plans/' + v + '/approve', 'POST', undefined, 403);
      await window.__hostCall('/teachers/teacher-6-b/assignments', 'GET', undefined, 403);
      await window.__hostCall('/inputs', 'GET', undefined, 403);
    }, version);
    pass('teacher approval, other assignments and administrator input denied', { status: 403 });
    await action('teacher acknowledgement', r => r.request().method() === 'POST' && new URL(r.url()).pathname.endsWith('/acknowledgements'),
      () => page.getByRole('button', { name: 'Acknowledge this version' }).click());
    const reportsBefore = await page.evaluate(v => window.__hostCall('/teachers/teacher-6-a/reports?version=' + v), version);
    if (reportsBefore.length !== 0) throw new Error('Acknowledgement is not execution');
    await page.getByRole('button', { name: 'Report 6-a:Mon-2', exact: true }).click();
    await page.getByLabel('Execution status').selectOption('COULD_NOT_IMPLEMENT');
    await page.getByLabel('Note (optional)').fill('SYNTHETIC HOSTED CHECK: classroom unavailable');
    await action('teacher execution report', r => r.request().method() === 'PUT' && new URL(r.url()).pathname.endsWith('/report'),
      () => page.getByRole('button', { name: 'Save execution report' }).click());
    await page.locator('tr[data-activity="6-a:Mon-2"]').getByText('Could not implement', { exact: true }).waitFor();
    pass('hosted acknowledgement separate from execution');
    await logout(); await login('administrator');
    await page.getByRole('link', { name: 'Review', exact: true }).click();
    await page.getByText('SYNTHETIC HOSTED CHECK: classroom unavailable', { exact: true }).first().waitFor();
    pass('administrator Review', await page.evaluate(async v => {
      const r = await window.__hostCall('/approved-plans/' + v + '/review');
      const history = await window.__hostCall('/approved-plans');
      if (r.counts.reported !== 1 || r.counts.unresolved !== 1 || !history.some(p => p.current && p.plan_version === v)) throw new Error('Review mismatch');
      return { counts: r.counts, approved_versions: history.length };
    }, version));
    await logout();
  } catch (e) {
    results.push({ failure_stage: stage, error_type: e.name });
    console.error('FAIL: ' + stage + '; ' + e.name + '; private contents withheld'); process.exitCode = 1;
  } finally {
    const failure = await page.evaluate(() => window.__host.failure || null).catch(() => null);
    fs.writeFileSync(path.join(__dirname, '../work/hosted-verification.json'), JSON.stringify({ results, timings, failure }, null, 2));
    await browser.close();
  }
})().catch(e => { console.error('FAIL startup: ' + e.name); process.exitCode = 1; });
